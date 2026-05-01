#!/usr/bin/env python3
"""
render_md.py — deterministically render <run_dir>/analysis.md from analysis.json.

Each run dir is single-stack now, so this script renders a per-stack report
without any cross-stack comparison. The cross-stack comparison happens at
the final-analysis stage (see benchmarking.analysis.final.render_final_md).

Usage:
    uv run python -m benchmarking.analysis.per_run.render_md <run_dir>
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean

VERDICT_GLYPH = {"PASS": "✓", "PARTIAL": "◐", "FAIL": "✗", "ERROR": "⚠"}
DIFFICULTIES  = ["L1", "L2", "L3", "L4", "L5"]
CATEGORIES    = ["retrieval", "search", "write", "workflow", "orchestration", "edge_case"]

HINTAS_PARAM_LABELS = [
    ("search_top_k",         "search_top_k"),
    ("search_batch_enabled", "search_batch_enabled"),
    ("search_max_results",   "search_max_results"),
    ("rag_enabled",          "rag_enabled"),
]


def fmt_int(x):    return f"{int(round(x)):,}" if x is not None else ""
def fmt_pct(x):    return f"{x*100:.0f}%" if x is not None else ""
def fmt_float(x, n=2): return f"{x:.{n}f}" if x is not None else ""


def fmt_param_value(v) -> str:
    if isinstance(v, bool):
        return "on" if v else "off"
    if v is None:
        return "—"
    return str(v)


def display_name_for(stack: str) -> str:
    return f"{stack.capitalize()} MCP"


def load_hintas_params(run_dir: Path) -> dict | None:
    """Pull `hintas_params` from analysis_data.json or results.json (in that order)."""
    for fname in ("analysis_data.json", "results.json"):
        path = run_dir / fname
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        params = data.get("hintas_params")
        if params:
            return params
    return None


def normalize(data: dict) -> tuple[str, str, list[dict]]:
    """Return (ts, stack, prompts) regardless of which schema the analyzer wrote."""
    if "prompts" in data and "stack" in data:
        ts = data.get("run_id") or data.get("graded_at") or ""
        return ts, data["stack"], data["prompts"]

    if "per_prompt" in data and "stacks" in data:
        stacks = data["stacks"]
        if len(stacks) != 1:
            raise SystemExit(
                f"Expected analysis.json `stacks` to contain exactly one entry; got {stacks!r}"
            )
        stack = stacks[0]
        ts = data.get("timestamp", "")
        prompts: list[dict] = []
        for pid, p in data["per_prompt"].items():
            r = p[stack]
            tc = r["tool_calls"]
            tc_complete = tc.get("complete", 0)
            tc_failed   = tc.get("failed", 0)
            tc_partial  = tc.get("partial", 0)
            prompts.append({
                "prompt_id":  int(pid),
                "title":      p["title"],
                "difficulty": p["difficulty"],
                "category":   p["category"],
                "verdict":    r["verdict"],
                "reasoning":  r["reasoning"],
                "metrics": {
                    "total_tokens":         r["total_tokens"],
                    "wall_clock_s":         r["wall_clock_s"],
                    "tool_calls_completed": tc_complete,
                    "tool_calls_failed":    tc_failed,
                    "tool_calls_total":     tc_complete + tc_failed + tc_partial,
                    "initial_context":      r["initial_context"],
                    "peak_context":         r["peak_context"],
                },
            })
        return ts, stack, prompts

    raise SystemExit(
        f"Unrecognized analysis.json schema; top-level keys: {sorted(data.keys())}"
    )


def recompute_aggregates(prompts: list[dict]) -> dict:
    n = len(prompts)
    if n == 0:
        return {}
    verdicts = Counter(p["verdict"] for p in prompts)
    metrics = [p["metrics"] for p in prompts]
    return {
        "n": n,
        "pass":    verdicts.get("PASS", 0),
        "partial": verdicts.get("PARTIAL", 0),
        "fail":    verdicts.get("FAIL", 0),
        "error":   verdicts.get("ERROR", 0),
        "success_rate":        verdicts.get("PASS", 0) / n,
        "avg_initial_context": mean(m["initial_context"] for m in metrics),
        "avg_peak_context":    mean(m["peak_context"]    for m in metrics),
        "avg_wall_clock_s":    mean(m["wall_clock_s"]    for m in metrics),
        "total_tokens":        sum(m["total_tokens"]     for m in metrics),
        "avg_total_tokens":    mean(m["total_tokens"]    for m in metrics),
        "avg_tool_calls":      mean(m["tool_calls_total"] for m in metrics),
        "total_tool_failures": sum(m["tool_calls_failed"] for m in metrics),
    }


def breakdown(prompts: list[dict], key: str, buckets: list[str]) -> list[dict]:
    out = []
    for b in buckets:
        rows = [p for p in prompts if p[key] == b]
        if not rows:
            continue
        n = len(rows)
        verdicts = Counter(p["verdict"] for p in rows)
        out.append({
            "bucket": b, "n": n,
            "success_rate": verdicts.get("PASS", 0) / n,
            "partial":      verdicts.get("PARTIAL", 0),
            "fail":         verdicts.get("FAIL", 0),
            "error":        verdicts.get("ERROR", 0),
        })
    return out


def pick_notable(prompts: list[dict], limit: int = 8) -> list[dict]:
    """Pick the most instructive PARTIAL/FAIL/ERROR rows, spread across categories."""
    bad = {"FAIL", "ERROR", "PARTIAL"}
    candidates = sorted(
        (p for p in prompts if p["verdict"] in bad),
        key=lambda p: int(p["prompt_id"]),
    )

    chosen: list[dict] = []
    seen_categories: Counter = Counter()
    for p in candidates:
        if len(chosen) >= limit:
            break
        if seen_categories[p["category"]] < 2:
            chosen.append(p)
            seen_categories[p["category"]] += 1
    for p in candidates:
        if len(chosen) >= limit:
            break
        if p in chosen:
            continue
        chosen.append(p)
    return chosen


def render(run_dir: Path) -> str:
    data = json.loads((run_dir / "analysis.json").read_text())
    ts, stack, prompts = normalize(data)
    if not ts:
        ts = run_dir.name
    label = display_name_for(stack)

    prompts_by_id = {int(p["prompt_id"]): p for p in prompts}
    sorted_ids = sorted(prompts_by_id.keys())
    agg = recompute_aggregates(prompts)

    L: list[str] = []

    L.append(f"# Benchmark Analysis — {label} — Run {ts}")
    L.append("")
    L.append(f"**Scope:** {len(prompts)} prompts × {label}, "
             "graded against precomputed session summaries (`analysis_data.json`).")
    L.append("")

    hintas_params = load_hintas_params(run_dir)
    if hintas_params:
        L.append("## MCP configuration")
        L.append("")
        L.append("> The variant Hintas server runs with the parameters below. When "
                 "comparing two Hintas runs, this is the block to scan first — these "
                 "are the only knobs that change between them.")
        L.append("")
        L.append("| Parameter | Value |")
        L.append("|:----------|:-----:|")
        for key, label_str in HINTAS_PARAM_LABELS:
            L.append(f"| `{label_str}` | **{fmt_param_value(hintas_params.get(key))}** |")
        L.append("")

    L.append("## Verdict legend")
    L.append("")
    L.append("- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.")
    L.append("- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.")
    L.append("- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** "
             "(\"user doesn't exist\", \"page not shared\", \"integration lacks access\", server refused).")
    L.append("- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).")
    L.append("")

    # ── Per-prompt results table ──────────────────────────────────────
    L.append("## Per-prompt results")
    L.append("")
    L.append("| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |")
    L.append("|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|")
    for pid in sorted_ids:
        p = prompts_by_id[pid]
        m = p["metrics"]
        v = f"{VERDICT_GLYPH[p['verdict']]} {p['verdict']}"
        title = p["title"].replace("|", "\\|")
        L.append(f"| {pid} | {title} | {p['difficulty']} | {v} | "
                 f"{fmt_float(m['wall_clock_s'], 1)}s | "
                 f"{fmt_int(m['total_tokens'])} | "
                 f"{m['tool_calls_total']} | {m['tool_calls_failed']} |")
    L.append("")

    # ── Initial vs peak context ─────────────────────────────────────
    L.append("## Initial vs peak context")
    L.append("")
    L.append("| ID | Title | Initial | Peak |")
    L.append("|---:|:------|--------:|-----:|")
    for pid in sorted_ids:
        p = prompts_by_id[pid]
        m = p["metrics"]
        title = p["title"].replace("|", "\\|")
        L.append(f"| {pid} | {title} | "
                 f"{fmt_int(m['initial_context'])} | {fmt_int(m['peak_context'])} |")
    L.append("")

    # ── Aggregates ──────────────────────────────────────────────────
    L.append("## Aggregates")
    L.append("")
    if agg:
        L.append("| Metric | Value |")
        L.append("|:-------|------:|")
        L.append(f"| Prompts run | {agg['n']} |")
        L.append(f"| Success rate | {fmt_pct(agg['success_rate'])} |")
        L.append(f"| Passes | {agg['pass']} |")
        L.append(f"| Partial | {agg['partial']} |")
        L.append(f"| Fails | {agg['fail']} |")
        L.append(f"| Errors | {agg['error']} |")
        L.append(f"| Avg initial context | {fmt_float(agg['avg_initial_context'], 0)} |")
        L.append(f"| Avg peak context | {fmt_int(agg['avg_peak_context'])} |")
        L.append(f"| Avg wall-clock | {fmt_float(agg['avg_wall_clock_s'], 1)}s |")
        L.append(f"| Total tokens | {fmt_int(agg['total_tokens'])} |")
        L.append(f"| Avg tokens/prompt | {fmt_int(agg['avg_total_tokens'])} |")
        L.append(f"| Avg tool calls | {fmt_float(agg['avg_tool_calls'], 2)} |")
        L.append(f"| Total tool failures | {agg['total_tool_failures']} |")
    else:
        L.append("_No prompts graded._")
    L.append("")

    # ── Breakdown by difficulty ─────────────────────────────────────
    L.append("## Breakdown by difficulty")
    L.append("")
    L.append("| Difficulty | n | Success rate | P/F/E |")
    L.append("|:-----------|--:|-------------:|:-----:|")
    for row in breakdown(prompts, "difficulty", DIFFICULTIES):
        L.append(f"| {row['bucket']} | {row['n']} | "
                 f"{fmt_pct(row['success_rate'])} | "
                 f"{row['partial']}/{row['fail']}/{row['error']} |")
    L.append("")

    # ── Breakdown by category ───────────────────────────────────────
    L.append("## Breakdown by category")
    L.append("")
    L.append("| Category | n | Success rate | P/F/E |")
    L.append("|:---------|--:|-------------:|:-----:|")
    for row in breakdown(prompts, "category", CATEGORIES):
        L.append(f"| {row['bucket']} | {row['n']} | "
                 f"{fmt_pct(row['success_rate'])} | "
                 f"{row['partial']}/{row['fail']}/{row['error']} |")
    L.append("")

    # ── Notable failures ────────────────────────────────────────────
    L.append("## Notable failures")
    L.append("")
    notable = pick_notable(prompts, limit=8)
    if notable:
        for p in notable:
            L.append(f"- **#{p['prompt_id']} {p['title']}** "
                     f"({p['difficulty']}, {p['category']}) — "
                     f"`{p['verdict']}`: {p['reasoning']}")
    else:
        L.append("_No PARTIAL / FAIL / ERROR rows._")
    L.append("")

    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Render analysis.md from analysis.json")
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    if not (args.run_dir / "analysis.json").exists():
        raise SystemExit(f"analysis.json not found in {args.run_dir}")
    md = render(args.run_dir)
    out = args.run_dir / "analysis.md"
    out.write_text(md)
    print(f"wrote {out} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
