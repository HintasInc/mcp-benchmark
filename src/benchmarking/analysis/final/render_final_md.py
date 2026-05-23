#!/usr/bin/env python3
"""
render_final_md.py — deterministically render final_analysis.md from final_analysis.json.

The grader (or aggregate_final_json.py) produced final_analysis.json comparing
exactly one baseline stack vs one variant stack. This script does the
mechanical markdown layout so the grader doesn't burn its budget on rendering.

Usage:
    uv run python -m benchmarking.analysis.final.render_final_md <output_dir>

    # expects <output_dir>/final_analysis.json
    # writes  <output_dir>/final_analysis.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

VERDICT_GLYPH = {"PASS": "✓", "PARTIAL": "◐", "FAIL": "✗", "ERROR": "⚠"}

HINTAS_PARAM_LABELS = [
    ("search_top_k",         "search_top_k"),
    ("search_batch_enabled", "search_batch_enabled"),
    ("search_max_results",   "search_max_results"),
    ("rag_enabled",          "rag_enabled"),
]


def fmt_param_value(v) -> str:
    if isinstance(v, bool):
        return "on" if v else "off"
    if v is None:
        return "—"
    return str(v)


def load_hintas_params(run_dir: Path) -> dict | None:
    """Pull `hintas_params` from analysis_data.json or results.json (in that order)."""
    if not run_dir or not run_dir.is_dir():
        return None
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


def fmt_int(x):
    if x is None:
        return "—"
    return f"{int(round(x)):,}"


def fmt_pct(x):
    if x is None:
        return "—"
    return f"{x*100:.0f}%"


def fmt_float(x, n=2):
    if x is None:
        return "—"
    return f"{x:.{n}f}"


def fmt_delta_int(x):
    if x is None:
        return "—"
    sign = "+" if x > 0 else ""
    return f"{sign}{int(round(x)):,}"


def fmt_delta_float(x, n=2):
    if x is None:
        return "—"
    sign = "+" if x > 0 else ""
    return f"{sign}{x:.{n}f}"


COMPARABLE_ROWS = (
    ("Total tokens",            "comparable_total_tokens",            "int"),
    ("Avg tokens / prompt",     "comparable_avg_tokens_per_prompt",   "int"),
    ("Avg tokens / tool call",  "comparable_avg_tokens_per_tool_call","int"),
    ("Avg peak context",        "comparable_avg_peak_context",        "int"),
    ("Avg initial context",     "comparable_avg_initial_context",     "float2"),
    ("Avg wall-clock (s)",      "comparable_avg_wall_clock_s",        "float1"),
)


def _fmt_pair(b_val, v_val, kind):
    if b_val is None or v_val is None:
        return "—", "—", "—"
    delta = b_val - v_val
    if kind == "int":
        return fmt_int(b_val), fmt_int(v_val), fmt_delta_int(delta)
    if kind == "float1":
        return fmt_float(b_val, 1), fmt_float(v_val, 1), fmt_delta_float(delta, 1)
    return fmt_float(b_val, 2), fmt_float(v_val, 2), fmt_delta_float(delta, 2)


def _analysis_md_link(run_dir: Path | None, output_dir: Path) -> str | None:
    """Return a markdown link to a run's analysis.md, relative to output_dir when possible."""
    if run_dir is None:
        return None
    md_path = run_dir / "analysis.md"
    if not md_path.exists():
        return None
    try:
        target = os.path.relpath(md_path.resolve(), output_dir.resolve())
    except ValueError:
        target = str(md_path.resolve())
    return f"[`{md_path.name}`]({target})"


def _rel_dir(run_dir: Path | None, output_dir: Path) -> str:
    """Render a run dir relative to output_dir so committed reports carry no absolute paths."""
    if run_dir is None:
        return ""
    try:
        return os.path.relpath(run_dir.resolve(), output_dir.resolve())
    except ValueError:
        return str(run_dir)


def render_run_links(L, b_dir, v_dir, b_label, v_label, output_dir):
    b_link = _analysis_md_link(b_dir, output_dir)
    v_link = _analysis_md_link(v_dir, output_dir)
    if not (b_link or v_link):
        return
    L.append("## Per-run reports")
    L.append("")
    L.append(f"- {b_label}: {b_link or '_(missing analysis.md)_'}  ↳ `{_rel_dir(b_dir, output_dir)}`")
    L.append(f"- {v_label}: {v_link or '_(missing analysis.md)_'}  ↳ `{_rel_dir(v_dir, output_dir)}`")
    L.append("")


def render_stack_config(L, b_dir, v_dir, b_stack, v_stack, b_label, v_label):
    """Side-by-side MCP-config block. Skipped when neither side has hintas_params."""
    b_params = load_hintas_params(b_dir)
    v_params = load_hintas_params(v_dir)
    if not (b_params or v_params):
        return
    L.append("## MCP configuration")
    L.append("")
    L.append("> The variant Hintas server runs with the parameters below. When "
             "comparing two Hintas runs (A vs B), this is the block to scan first — "
             "these are the only knobs that change between them.")
    L.append("")
    both_parameterized = bool(b_params and v_params)
    L.append(f"| Parameter | {b_label} (`{b_stack}`) | {v_label} (`{v_stack}`) |")
    L.append("|:----------|:----------------:|:----------------:|")
    for key, label_str in HINTAS_PARAM_LABELS:
        b_val = fmt_param_value(b_params.get(key)) if b_params else "—"
        v_val = fmt_param_value(v_params.get(key)) if v_params else "—"
        marker = ""
        if both_parameterized and b_params.get(key) != v_params.get(key):
            marker = "  ⚠"
        L.append(f"| `{label_str}` | **{b_val}** | **{v_val}**{marker} |")
    L.append("")
    if both_parameterized:
        diffs = [k for k, _ in HINTAS_PARAM_LABELS
                 if b_params.get(k) != v_params.get(k)]
        if diffs:
            L.append(f"_Differing parameters: `{'`, `'.join(diffs)}`._")
        else:
            L.append("_All parameters match across stacks._")
    else:
        L.append("_Only the variant stack carries Hintas parameters; baseline is the unmodified MCP._")
    L.append("")


def render_legend(L):
    L.append("## Verdict legend")
    L.append("")
    L.append("- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.")
    L.append("- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.")
    L.append("- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** "
             "(\"user doesn't exist\", \"page not shared\", \"integration lacks access\", server refused).")
    L.append("- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or "
             "`result_subtype: error` with no usable output).")
    L.append("")


def render_per_prompt(L, data, b_key, v_key, b_label, v_label):
    L.append("## Per-prompt results")
    L.append("")
    L.append(f"| ID | Title | Diff | {b_label} | {v_label} | "
             f"{b_label[:1]} Tok | {v_label[:1]} Tok | "
             f"{b_label[:1]} Time | {v_label[:1]} Time | ΔTok | ΔTime |")
    L.append("|---:|:------|:----:|:------:|:------:|---:|---:|---:|---:|---:|---:|")
    sorted_ids = sorted(data["per_prompt"].keys(), key=lambda x: int(x))
    for pid in sorted_ids:
        p = data["per_prompt"][pid]
        b = p[b_key]
        v = p[v_key]
        bv = f"{VERDICT_GLYPH[b['verdict']]} {b['verdict']}"
        vv = f"{VERDICT_GLYPH[v['verdict']]} {v['verdict']}"
        if b["comparable"] and v["comparable"]:
            d_tok  = fmt_delta_int(v["total_tokens"]  - b["total_tokens"])
            d_time = fmt_delta_float(v["wall_clock_s"] - b["wall_clock_s"], 1)
        else:
            d_tok = d_time = "*excl*"
        title = p["title"].replace("|", "\\|")
        L.append(f"| {pid} | {title} | {p['difficulty']} | {bv} | {vv} | "
                 f"{fmt_int(b['total_tokens'])} | {fmt_int(v['total_tokens'])} | "
                 f"{fmt_float(b['wall_clock_s'], 1)}s | {fmt_float(v['wall_clock_s'], 1)}s | "
                 f"{d_tok} | {d_time} |")
    L.append("")


def render_verdict_tally(L, b_totals, v_totals, b_label, v_label):
    L.append("## Verdict tallies")
    L.append("")
    L.append("| Stack | PASS | PARTIAL | FAIL | ERROR | Success rate |")
    L.append("|:------|---:|---:|---:|---:|---:|")
    for label, side in ((b_label, b_totals), (v_label, v_totals)):
        verd = side.get("verdicts", {})
        L.append(
            f"| {label} | "
            f"{verd.get('PASS', 0)} | {verd.get('PARTIAL', 0)} | "
            f"{verd.get('FAIL', 0)} | {verd.get('ERROR', 0)} | "
            f"{fmt_pct(side.get('pass_rate'))} |"
        )
    L.append("")


def render_tool_tally(L, b_totals, v_totals, b_label, v_label):
    L.append("## Tool-call tallies (every prompt, regardless of verdict)")
    L.append("")
    L.append("| Stack | Tools complete | Tools failed | Tools partial | Total | Tool success rate |")
    L.append("|:------|---:|---:|---:|---:|---:|")
    for label, side in ((b_label, b_totals), (v_label, v_totals)):
        L.append(
            f"| {label} | "
            f"{side.get('tools_passed', 0)} | "
            f"{side.get('tools_failed', 0)} | "
            f"{side.get('tools_partial', 0)} | "
            f"{side.get('tools_total', 0)} | "
            f"{fmt_pct(side.get('tool_pass_rate'))} |"
        )
    L.append("")


def render_comparable(L, b_totals, v_totals, comparable_ids, excluded_ids, b_label, v_label):
    L.append("## Comparable-only metrics (both stacks PASS)")
    L.append("")
    cmp_str = ", ".join(comparable_ids) if comparable_ids else "(none)"
    exc_str = ", ".join(excluded_ids) if excluded_ids else "(none)"
    L.append(f"- Comparable prompt IDs: `{cmp_str}` (count: {len(comparable_ids)})")
    L.append(f"- Excluded prompt IDs:   `{exc_str}` (count: {len(excluded_ids)})")
    L.append("")
    if not comparable_ids:
        L.append("_No prompts where both stacks passed; comparable metrics suppressed._")
        L.append("")
        return
    L.append(f"| Metric | {b_label} | {v_label} | Δ ({b_label[:1]} − {v_label[:1]}) |")
    L.append("|:-------|---:|---:|---:|")
    for label, key, kind in COMPARABLE_ROWS:
        b_val, v_val = b_totals.get(key), v_totals.get(key)
        b, v, d = _fmt_pair(b_val, v_val, kind)
        L.append(f"| {label} | {b} | {v} | {d} |")
    L.append("")


def render_verdict(L, verdict):
    L.append("## Final verdict")
    L.append("")
    L.append("| Category | Winner | Margin |")
    L.append("|:---------|:------:|---:|")
    L.append(f"| Accuracy (success rate) | {verdict.get('accuracy_winner', '—')} | "
             f"{fmt_float(verdict.get('accuracy_margin_pp'), 1)} pp |")
    L.append(f"| Speed (avg wall-clock) | {verdict.get('speed_winner', '—')} | "
             f"{fmt_float(verdict.get('speed_margin_pct'), 1)}% |")
    L.append(f"| Token efficiency (comparable total) | {verdict.get('tokens_winner', '—')} | "
             f"{fmt_float(verdict.get('tokens_margin_pct'), 1)}% |")
    L.append(f"| Peak context (comparable avg) | {verdict.get('peak_context_winner', '—')} | "
             f"{fmt_float(verdict.get('peak_context_margin_pct'), 1)}% |")
    L.append(f"| Tool reliability (tool success rate) | {verdict.get('tool_reliability_winner', '—')} | — |")
    L.append("")
    if verdict.get("summary"):
        L.append(verdict["summary"])
        L.append("")


def render(data: dict, output_dir: Path) -> str:
    ts = data["timestamp"]
    platform   = data.get("platform", "")
    b_key      = data["baseline_stack"]
    v_key      = data["variant_stack"]
    b_label    = data.get("baseline_display") or b_key.capitalize() + " MCP"
    v_label    = data.get("variant_display")  or v_key.capitalize() + " MCP"
    n_prompts  = data.get("n_prompts", len(data.get("per_prompt", {})))

    b_dir_raw  = data.get("baseline_run_dir", "")
    v_dir_raw  = data.get("variant_run_dir",  "")
    b_dir = Path(b_dir_raw) if b_dir_raw else None
    v_dir = Path(v_dir_raw) if v_dir_raw else None

    L: list[str] = []
    L.append(f"# Final Benchmark Analysis — {platform} — {ts}")
    L.append("")
    L.append(f"**Scope:** {n_prompts} prompts × 2 stacks ({b_label}, {v_label}).")
    L.append("")
    L.append(f"- Baseline: `{b_dir_raw}` ({b_label})")
    L.append(f"- Variant:  `{v_dir_raw}` ({v_label})")
    L.append("")

    render_run_links(L, b_dir, v_dir, b_label, v_label, output_dir)
    render_stack_config(L, b_dir, v_dir, b_key, v_key, b_label, v_label)
    render_legend(L)

    render_per_prompt(L, data, b_key, v_key, b_label, v_label)

    totals = data.get("totals", {})
    b_totals = totals.get(b_key, {})
    v_totals = totals.get(v_key, {})
    comparable_ids = totals.get("comparable_prompt_ids", [])
    excluded_ids   = totals.get("excluded_prompt_ids", [])

    render_verdict_tally(L, b_totals, v_totals, b_label, v_label)
    render_tool_tally(L, b_totals, v_totals, b_label, v_label)
    render_comparable(L, b_totals, v_totals, comparable_ids, excluded_ids, b_label, v_label)
    render_verdict(L, data.get("verdict", {}))

    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(
        description="Render final_analysis.md from final_analysis.json"
    )
    ap.add_argument("output_dir", type=Path,
                    help="Directory containing final_analysis.json; "
                         "final_analysis.md will be written here.")
    args = ap.parse_args()

    json_path = args.output_dir / "final_analysis.json"
    if not json_path.exists():
        raise SystemExit(f"final_analysis.json not found in {args.output_dir}")

    data = json.loads(json_path.read_text())
    md = render(data, args.output_dir)
    out = args.output_dir / "final_analysis.md"
    out.write_text(md)
    print(f"wrote {out} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
