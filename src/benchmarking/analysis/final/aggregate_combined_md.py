#!/usr/bin/env python3
"""
aggregate_combined_md.py — deterministically build a combined comparison
markdown across one baseline run and N variant runs (no LLM grader).

Each run directory must already hold an analysis.json produced by the per-run
analyzer. The script trusts those verdicts and rolls them up into a single
side-by-side report.

Usage:
    uv run benchmark combine \\
        --platform notion \\
        --baseline platforms/notion/runs/20260429_205418__notion \\
        --variants platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off \\
                   platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off \\
                   platforms/notion/runs/20260430_100101__hintas__topk10_batch-off_max5_rag-off

    # default output: platforms/<platform>/final/<timestamp>/combined_comparison.md
    # override with --output-dir <path>
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean

from benchmarking.config import (
    Platform, available_platforms, preload_platform,
)
from benchmarking.paths import REPO_ROOT

VERDICT_KEYS  = ("PASS", "PARTIAL", "FAIL", "ERROR")
VERDICT_GLYPH = {"PASS": "✓", "PARTIAL": "◐", "FAIL": "✗", "ERROR": "⚠"}

HINTAS_PARAM_LABELS = [
    ("search_top_k",         "search_top_k"),
    ("search_batch_enabled", "search_batch_enabled"),
    ("search_max_results",   "search_max_results"),
    ("rag_enabled",          "rag_enabled"),
]

TIE_PCT = 1.0
TIE_PP  = 0.5


def add_arguments(p: argparse.ArgumentParser, platform: Platform) -> None:
    p.add_argument("--platform", default="notion",
                   choices=available_platforms() or None,
                   help="Platform manifest under platforms/ (default: notion)")
    p.add_argument("--baseline", type=Path, required=True,
                   help="Run directory for the baseline stack.")
    p.add_argument("--variants", nargs="+", type=Path, action="extend",
                   required=True,
                   help="One or more variant run directories. May be repeated, "
                        "e.g. `--variants A B` or `--variants A --variants B`.")
    p.add_argument("--output-dir", type=Path,
                   help="Where to write combined_comparison.md. "
                        "Default: platforms/<platform>/final/<timestamp>/")


def resolve_dir(p: Path) -> Path:
    path = p if p.is_absolute() else (REPO_ROOT / p)
    path = path.resolve()
    if not path.is_dir():
        sys.exit(f"ERROR: run directory does not exist: {path}")
    return path


def load_run(run_dir: Path) -> dict:
    """Read analysis.json + results.json for a single run."""
    a_path = run_dir / "analysis.json"
    r_path = run_dir / "results.json"
    if not a_path.exists():
        sys.exit(f"ERROR: missing {a_path}; run per-run analysis first")
    if not r_path.exists():
        sys.exit(f"ERROR: missing {r_path}")
    analysis = json.loads(a_path.read_text())
    results  = json.loads(r_path.read_text())
    stacks = analysis.get("stacks") or []
    if len(stacks) != 1:
        sys.exit(f"ERROR: {a_path} must declare exactly one stack; got {stacks!r}")
    return {
        "dir":       run_dir,
        "stack_name": stacks[0],
        "analysis":   analysis,
        "results":    results,
        "hintas_params": results.get("hintas_params"),
    }


def normalize_side(side: dict) -> dict:
    tc = side.get("tool_calls", {}) or {}
    complete = int(tc.get("complete", 0))
    failed   = int(tc.get("failed", 0))
    partial  = int(tc.get("partial", 0))
    total    = complete + failed + partial
    return {
        "verdict":       side.get("verdict", "ERROR"),
        "tools_passed":  complete,
        "tools_failed":  failed,
        "tools_partial": partial,
        "tools_total":   total,
        "initial_context": side.get("initial_context", 0),
        "peak_context":    side.get("peak_context", 0),
        "total_tokens":    side.get("total_tokens", 0),
        "wall_clock_s":    side.get("wall_clock_s", 0),
    }


def collect_per_prompt(runs: list[dict]) -> tuple[dict, list[str]]:
    """Merge per_prompt rows across runs. Each prompt id maps to:
        {
          "title": ..., "difficulty": ..., "category": ...,
          "sides": { run_label: normalized_side, ... }
        }
    """
    per_prompt: dict[str, dict] = {}
    for run in runs:
        label = run["label"]
        stack = run["stack_name"]
        for pid, prompt in run["analysis"].get("per_prompt", {}).items():
            side = prompt.get(stack)
            if side is None:
                continue
            row = per_prompt.setdefault(pid, {
                "title":      prompt.get("title", ""),
                "difficulty": prompt.get("difficulty", ""),
                "category":   prompt.get("category", ""),
                "sides":      {},
            })
            row["sides"][label] = normalize_side(side)
    ordered_ids = sorted(per_prompt.keys(), key=lambda x: int(x))
    return per_prompt, ordered_ids


def stack_totals(per_prompt: dict, label: str) -> dict:
    rows = [p["sides"][label] for p in per_prompt.values() if label in p["sides"]]
    n = len(rows)
    verdicts = Counter(r["verdict"] for r in rows)
    tools_passed  = sum(r["tools_passed"]  for r in rows)
    tools_failed  = sum(r["tools_failed"]  for r in rows)
    tools_partial = sum(r["tools_partial"] for r in rows)
    tools_total   = sum(r["tools_total"]   for r in rows)
    return {
        "n":              n,
        "verdicts":       {k: verdicts.get(k, 0) for k in VERDICT_KEYS},
        "pass_rate":      (verdicts.get("PASS", 0) / n) if n else 0.0,
        "tools_passed":   tools_passed,
        "tools_failed":   tools_failed,
        "tools_partial":  tools_partial,
        "tools_total":    tools_total,
        "tool_pass_rate": (tools_passed / tools_total) if tools_total else 0.0,
    }


def comparable_metrics(per_prompt: dict, label: str, comparable_ids: list[str]) -> dict:
    """Compute comparable-only averages for a stack across the given prompt IDs."""
    rows = [per_prompt[pid]["sides"][label]
            for pid in comparable_ids
            if label in per_prompt[pid]["sides"]]
    n = len(rows)
    total_tokens = sum(r["total_tokens"] for r in rows) if rows else 0
    total_tools  = sum(r["tools_total"]  for r in rows) if rows else 0
    return {
        "comparable_n":             n,
        "comparable_total_tokens":  total_tokens,
        "comparable_avg_initial_context": mean(r["initial_context"] for r in rows) if rows else None,
        "comparable_avg_peak_context":    mean(r["peak_context"]    for r in rows) if rows else None,
        "comparable_avg_wall_clock_s":    mean(r["wall_clock_s"]    for r in rows) if rows else None,
        "comparable_avg_tokens_per_prompt":    (total_tokens / n) if n else None,
        "comparable_avg_tokens_per_tool_call": (total_tokens / total_tools) if total_tools else None,
    }


def pair_comparable_ids(per_prompt: dict, ordered_ids: list[str],
                        a_label: str, b_label: str) -> list[str]:
    """IDs where both stacks scored PASS."""
    out = []
    for pid in ordered_ids:
        sides = per_prompt[pid]["sides"]
        a, b = sides.get(a_label), sides.get(b_label)
        if a and b and a["verdict"] == "PASS" and b["verdict"] == "PASS":
            out.append(pid)
    return out


# ---------------------------------------------------------------------------
# formatters

def fmt_int(x):
    return "—" if x is None else f"{int(round(x)):,}"

def fmt_pct(x):
    return "—" if x is None else f"{x*100:.0f}%"

def fmt_float(x, n=2):
    return "—" if x is None else f"{x:.{n}f}"

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

def fmt_param_value(v) -> str:
    if isinstance(v, bool):
        return "on" if v else "off"
    if v is None:
        return "—"
    return str(v)


# ---------------------------------------------------------------------------
# pairwise verdict (baseline vs each variant)

def lower_wins(b_val, v_val, b_label, v_label):
    if b_val is None or v_val is None:
        return "Tie", 0.0
    if b_val == 0 and v_val == 0:
        return "Tie", 0.0
    slow, fast = max(b_val, v_val), min(b_val, v_val)
    margin = ((slow - fast) / slow * 100.0) if slow else 0.0
    if margin < TIE_PCT:
        return "Tie", margin
    return (v_label if v_val < b_val else b_label), margin


def higher_wins_pp(b_val, v_val, b_label, v_label):
    if b_val is None or v_val is None:
        return "Tie", 0.0
    margin_pp = abs(b_val - v_val) * 100.0
    if margin_pp < TIE_PP:
        return "Tie", margin_pp
    return (b_label if b_val > v_val else v_label), margin_pp


def higher_wins_pct(b_val, v_val, b_label, v_label):
    if b_val is None or v_val is None:
        return "Tie", 0.0
    if b_val == 0 and v_val == 0:
        return "Tie", 0.0
    high, low = max(b_val, v_val), min(b_val, v_val)
    margin = ((high - low) / high * 100.0) if high else 0.0
    if margin < TIE_PCT:
        return "Tie", margin
    return (b_label if b_val > v_val else v_label), margin


def pairwise_verdict(b_totals, v_totals, b_label, v_label) -> dict:
    speed_w,  speed_m  = lower_wins(b_totals.get("comparable_avg_wall_clock_s"),
                                    v_totals.get("comparable_avg_wall_clock_s"),
                                    b_label, v_label)
    tokens_w, tokens_m = lower_wins(b_totals.get("comparable_total_tokens"),
                                    v_totals.get("comparable_total_tokens"),
                                    b_label, v_label)
    peak_w,   peak_m   = lower_wins(b_totals.get("comparable_avg_peak_context"),
                                    v_totals.get("comparable_avg_peak_context"),
                                    b_label, v_label)
    acc_w,    acc_m    = higher_wins_pp(b_totals.get("pass_rate"),
                                        v_totals.get("pass_rate"),
                                        b_label, v_label)
    tool_w,   _        = higher_wins_pct(b_totals.get("tool_pass_rate"),
                                         v_totals.get("tool_pass_rate"),
                                         b_label, v_label)

    wins = Counter(w for w in (speed_w, tokens_w, peak_w, acc_w, tool_w) if w != "Tie")
    if not wins:
        winner = "Tie"
    elif len(wins) == 1:
        winner = next(iter(wins))
    else:
        top, second = wins.most_common(2)
        winner = top[0] if top[1] > second[1] else "Tie"

    return {
        "winner": winner,
        "accuracy_winner":  acc_w,    "accuracy_margin_pp":      acc_m,
        "speed_winner":     speed_w,  "speed_margin_pct":        speed_m,
        "tokens_winner":    tokens_w, "tokens_margin_pct":       tokens_m,
        "peak_context_winner": peak_w, "peak_context_margin_pct": peak_m,
        "tool_reliability_winner": tool_w,
    }


# ---------------------------------------------------------------------------
# rendering

def md_link(run_dir: Path, output_dir: Path) -> str | None:
    md = run_dir / "analysis.md"
    if not md.exists():
        return None
    try:
        rel = md.resolve().relative_to(output_dir.resolve())
        target = str(rel)
    except ValueError:
        target = str(md.resolve())
    return f"[`{md.name}`]({target})"


def render_header(L, platform, runs, ts, n_prompts):
    L.append(f"# Combined Benchmark Comparison — {platform.display_name} — {ts}")
    L.append("")
    L.append(f"**Scope:** {n_prompts} prompts × {len(runs)} stacks "
             f"(baseline + {len(runs) - 1} variant{'s' if len(runs) != 2 else ''}).")
    L.append("")
    for run in runs:
        kind = "Baseline" if run is runs[0] else "Variant "
        L.append(f"- {kind}: `{run['dir']}` ({run['label']})")
    L.append("")


def render_run_links(L, runs, output_dir):
    L.append("## Per-run reports")
    L.append("")
    for run in runs:
        link = md_link(run["dir"], output_dir)
        L.append(f"- {run['label']}: {link or '_(missing analysis.md)_'}  ↳ `{run['dir']}`")
    L.append("")


def render_stack_config(L, runs):
    """One sub-block per variant; columns are baseline MCP and the variant MCP."""
    if not any(r["hintas_params"] for r in runs):
        return
    baseline = runs[0]
    variants = [r for r in runs[1:] if r["hintas_params"]]
    if not variants:
        return
    multi = len(variants) > 1

    L.append("## MCP configuration")
    L.append("")
    L.append("> Each variant block shows the parameters the variant run was launched "
             "with, alongside the baseline MCP (which carries no Hintas params).")
    L.append("")

    differing_keys = [k for k, _ in HINTAS_PARAM_LABELS
                      if len({v["hintas_params"].get(k) for v in variants}) > 1]

    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        L.append(f"| Parameter | {baseline['label']} | {v['label']} |")
        L.append("|:----------|:--------------:|:--------------:|")
        for key, label_str in HINTAS_PARAM_LABELS:
            b_val = fmt_param_value(baseline["hintas_params"].get(key)) \
                if baseline["hintas_params"] else "—"
            v_val = fmt_param_value(v["hintas_params"].get(key))
            mark = "  ⚠" if multi and key in differing_keys else ""
            L.append(f"| `{label_str}` | **{b_val}** | **{v_val}**{mark} |")
        L.append("")

    if multi:
        if differing_keys:
            L.append(f"_Parameters differing across variants: `{'`, `'.join(differing_keys)}`._")
        else:
            L.append("_All variants share identical parameters._")
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


def render_per_prompt_verdicts(L, per_prompt, ordered_ids, runs):
    """One sub-table per variant; columns are baseline MCP and the variant MCP."""
    L.append("## Per-prompt verdicts")
    L.append("")
    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1
    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        L.append(f"| ID | Title | Diff | {baseline['label']} | {v['label']} |")
        L.append("|---:|:------|:----:|:------:|:------:|")
        for pid in ordered_ids:
            row = per_prompt[pid]
            title = row["title"].replace("|", "\\|")
            cells = [pid, title, row["difficulty"]]
            for r in (baseline, v):
                side = row["sides"].get(r["label"])
                cells.append(f"{VERDICT_GLYPH[side['verdict']]} {side['verdict']}"
                             if side else "—")
            L.append("| " + " | ".join(cells) + " |")
        L.append("")


def render_per_prompt_metrics(L, per_prompt, ordered_ids, runs, metric_key, metric_label, fmt):
    """One sub-table per variant; columns are baseline, variant, Δ. Δ shown only when both PASS."""
    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1
    L.append(f"## Per-prompt {metric_label}")
    L.append("")
    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        L.append(f"| ID | Title | {baseline['label']} | {v['label']} | Δ {v['label']} vs {baseline['label']} |")
        L.append("|---:|:------|---:|---:|---:|")
        for pid in ordered_ids:
            row = per_prompt[pid]
            title = row["title"].replace("|", "\\|")
            b_side = row["sides"].get(baseline["label"])
            v_side = row["sides"].get(v["label"])
            cells = [pid, title]
            cells.append(fmt(b_side[metric_key]) if b_side else "—")
            cells.append(fmt(v_side[metric_key]) if v_side else "—")
            if (b_side and v_side
                    and b_side["verdict"] == "PASS"
                    and v_side["verdict"] == "PASS"):
                delta = v_side[metric_key] - b_side[metric_key]
                if metric_key == "total_tokens":
                    cells.append(fmt_delta_int(delta))
                else:
                    cells.append(fmt_delta_float(delta, 1) + "s")
            else:
                cells.append("*excl*")
            L.append("| " + " | ".join(cells) + " |")
        L.append("")


def render_verdict_tally(L, runs, totals_by_label):
    """Rows = verdict metrics, columns = baseline MCP + variant MCP (one sub-table per variant)."""
    L.append("## Verdict tallies")
    L.append("")
    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1
    b_t = totals_by_label[baseline["label"]]
    b_v = b_t["verdicts"]
    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        v_t = totals_by_label[v["label"]]
        v_v = v_t["verdicts"]
        L.append(f"| Metric | {baseline['label']} | {v['label']} |")
        L.append("|:-------|---:|---:|")
        for k in VERDICT_KEYS:
            L.append(f"| {k} | {b_v.get(k, 0)} | {v_v.get(k, 0)} |")
        L.append(f"| Pass rate | {fmt_pct(b_t['pass_rate'])} | {fmt_pct(v_t['pass_rate'])} |")
        L.append("")


def render_tool_tally(L, runs, totals_by_label):
    """Rows = tool-call metrics, columns = baseline MCP + variant MCP (one sub-table per variant)."""
    L.append("## Tool-call tallies (every prompt, regardless of verdict)")
    L.append("")
    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1
    b_t = totals_by_label[baseline["label"]]
    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        v_t = totals_by_label[v["label"]]
        L.append(f"| Metric | {baseline['label']} | {v['label']} |")
        L.append("|:-------|---:|---:|")
        L.append(f"| Tools complete | {b_t['tools_passed']} | {v_t['tools_passed']} |")
        L.append(f"| Tools failed | {b_t['tools_failed']} | {v_t['tools_failed']} |")
        L.append(f"| Tools partial | {b_t['tools_partial']} | {v_t['tools_partial']} |")
        L.append(f"| Total | {b_t['tools_total']} | {v_t['tools_total']} |")
        L.append(f"| Tool pass rate | {fmt_pct(b_t['tool_pass_rate'])} | {fmt_pct(v_t['tool_pass_rate'])} |")
        L.append("")


COMPARABLE_ROWS = (
    ("Total tokens",            "comparable_total_tokens",            "int"),
    ("Avg tokens / prompt",     "comparable_avg_tokens_per_prompt",   "int"),
    ("Avg tokens / tool call",  "comparable_avg_tokens_per_tool_call","int"),
    ("Avg peak context",        "comparable_avg_peak_context",        "int"),
    ("Avg initial context",     "comparable_avg_initial_context",     "float2"),
    ("Avg wall-clock (s)",      "comparable_avg_wall_clock_s",        "float1"),
)


def _fmt_comparable(v, kind):
    if v is None:
        return "—"
    if kind == "int":
        return fmt_int(v)
    if kind == "float1":
        return fmt_float(v, 1)
    return fmt_float(v, 2)


def render_global_comparable(L, runs, per_prompt, comparable_ids, excluded_ids):
    L.append("## Global comparable metrics (every stack PASS)")
    L.append("")
    cmp_str = ", ".join(comparable_ids) if comparable_ids else "(none)"
    L.append(f"- Comparable prompt IDs: `{cmp_str}` (count: {len(comparable_ids)})")
    L.append(f"- Excluded count: {len(excluded_ids)}")
    L.append("")
    if not comparable_ids:
        L.append("_No prompts where every stack passed — see the per-pair "
                 "comparable metrics below for fairer apples-to-apples numbers._")
        L.append("")
        return

    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1

    b_metrics = comparable_metrics(per_prompt, baseline["label"], comparable_ids)
    for v in variants:
        if multi:
            L.append(f"### {v['label']}")
            L.append("")
        v_metrics = comparable_metrics(per_prompt, v["label"], comparable_ids)
        L.append(f"| Metric | {baseline['label']} | {v['label']} |")
        L.append("|:-------|---:|---:|")
        for label, key, kind in COMPARABLE_ROWS:
            b_cell = _fmt_comparable(b_metrics.get(key), kind)
            v_cell = _fmt_comparable(v_metrics.get(key), kind)
            L.append(f"| {label} | {b_cell} | {v_cell} |")
        L.append("")


def render_pair_comparable(L, runs, per_prompt, ordered_ids):
    """One comparable-only metrics block per (baseline, variant) pair."""
    baseline = runs[0]
    L.append("## Per-pair comparable metrics (baseline ∩ variant PASS)")
    L.append("")
    L.append("> For each variant, this restricts to prompts where **both** the "
             "baseline and that variant passed — the fair apples-to-apples "
             "subset for token, speed, and context comparisons.")
    L.append("")

    for v in runs[1:]:
        ids = pair_comparable_ids(per_prompt, ordered_ids,
                                  baseline["label"], v["label"])
        L.append(f"### {baseline['label']} vs {v['label']}")
        L.append("")
        L.append(f"- Comparable prompt IDs: "
                 f"`{', '.join(ids) if ids else '(none)'}` (count: {len(ids)})")
        L.append("")
        if not ids:
            L.append("_No comparable prompts; metrics suppressed._")
            L.append("")
            continue

        b_metrics = comparable_metrics(per_prompt, baseline["label"], ids)
        v_metrics = comparable_metrics(per_prompt, v["label"],        ids)

        L.append(f"| Metric | {baseline['label']} | {v['label']} | "
                 f"Δ ({v['label']} − {baseline['label']}) |")
        L.append("|:-------|---:|---:|---:|")
        for label, key, kind in COMPARABLE_ROWS:
            b_val = b_metrics.get(key)
            v_val = v_metrics.get(key)
            b_cell = _fmt_comparable(b_val, kind)
            v_cell = _fmt_comparable(v_val, kind)
            if b_val is None or v_val is None:
                d_cell = "—"
            elif kind == "int":
                d_cell = fmt_delta_int(v_val - b_val)
            elif kind == "float1":
                d_cell = fmt_delta_float(v_val - b_val, 1)
            else:
                d_cell = fmt_delta_float(v_val - b_val, 2)
            L.append(f"| {label} | {b_cell} | {v_cell} | {d_cell} |")
        L.append("")


def render_pairwise_verdicts(L, runs, totals_by_label, per_prompt, ordered_ids):
    """One sub-table per variant; rows = metrics, columns = baseline + variant.
    The winning stack's cell shows the margin; the other shows a dash."""
    baseline = runs[0]
    b_totals = totals_by_label[baseline["label"]]
    L.append("## Pairwise verdicts (each variant vs baseline)")
    L.append("")
    L.append(f"Baseline: **{baseline['label']}**. Speed / token / context margins "
             "use the per-pair comparable subset (both stacks PASS).")
    L.append("")

    variants = runs[1:]
    multi = len(variants) > 1

    def cells(winner_label, b_label, v_label, attr_str):
        if winner_label == "Tie":
            return "Tie", "Tie"
        if winner_label == b_label:
            return attr_str, "—"
        if winner_label == v_label:
            return "—", attr_str
        return "—", "—"

    for r in variants:
        v_totals = totals_by_label[r["label"]]
        ids = pair_comparable_ids(per_prompt, ordered_ids,
                                  baseline["label"], r["label"])
        b_metrics = comparable_metrics(per_prompt, baseline["label"], ids)
        v_metrics = comparable_metrics(per_prompt, r["label"],        ids)
        b_for_pair = {**b_totals, **b_metrics}
        v_for_pair = {**v_totals, **v_metrics}
        verd = pairwise_verdict(b_for_pair, v_for_pair,
                                baseline["label"], r["label"])

        if multi:
            L.append(f"### {r['label']}")
            L.append("")
        L.append(f"| Metric | {baseline['label']} | {r['label']} |")
        L.append("|:-------|:---:|:---:|")

        b_c, v_c = cells(verd["accuracy_winner"], baseline["label"], r["label"],
                         f"+{fmt_float(verd['accuracy_margin_pp'], 1)} pp")
        L.append(f"| Accuracy | {b_c} | {v_c} |")

        b_c, v_c = cells(verd["speed_winner"], baseline["label"], r["label"],
                         f"+{fmt_float(verd['speed_margin_pct'], 1)}%")
        L.append(f"| Speed | {b_c} | {v_c} |")

        b_c, v_c = cells(verd["tokens_winner"], baseline["label"], r["label"],
                         f"+{fmt_float(verd['tokens_margin_pct'], 1)}%")
        L.append(f"| Tokens | {b_c} | {v_c} |")

        b_c, v_c = cells(verd["peak_context_winner"], baseline["label"], r["label"],
                         f"+{fmt_float(verd['peak_context_margin_pct'], 1)}%")
        L.append(f"| Peak context | {b_c} | {v_c} |")

        b_c, v_c = cells(verd["tool_reliability_winner"], baseline["label"], r["label"], "✓")
        L.append(f"| Tool reliability | {b_c} | {v_c} |")

        b_c, v_c = cells(verd["winner"], baseline["label"], r["label"], "**✓**")
        L.append(f"| **Overall winner** | {b_c} | {v_c} |")
        L.append("")


# ---------------------------------------------------------------------------
# main

PARAM_SHORT = {
    "search_max_results":   "max",
    "search_top_k":         "topk",
    "search_batch_enabled": "batch",
    "rag_enabled":          "rag",
}


def assign_labels(runs: list[dict], platform: Platform) -> None:
    """Mutate each run dict to include a unique display label.

    When multiple runs share the same stack, the suffix lists only the
    parameters that *differ* across those runs — keeping labels short.
    """
    stack_count: dict[str, int] = Counter(r["stack_name"] for r in runs)

    differing_keys: dict[str, list[str]] = {}
    for stack_name, count in stack_count.items():
        if count <= 1:
            continue
        siblings = [r for r in runs if r["stack_name"] == stack_name]
        keys = sorted({k for r in siblings if r["hintas_params"]
                         for k in r["hintas_params"]})
        differing = [k for k in keys
                     if len({(r["hintas_params"] or {}).get(k) for r in siblings}) > 1]
        differing_keys[stack_name] = differing

    seen: dict[str, int] = {}
    for r in runs:
        stack = platform.stack(r["stack_name"])
        base = stack.display_name
        if stack_count[r["stack_name"]] == 1:
            r["label"] = base
            continue
        params = r["hintas_params"] or {}
        keys = differing_keys.get(r["stack_name"], [])
        suffix = _format_param_subset(params, keys) if params else ""
        if not suffix:
            seen[r["stack_name"]] = seen.get(r["stack_name"], 0) + 1
            suffix = f"#{seen[r['stack_name']]}"
        r["label"] = f"{base} ({suffix})"


def _format_param_subset(params: dict, keys: list[str]) -> str:
    bits = []
    for k in keys:
        short = PARAM_SHORT.get(k, k)
        bits.append(f"{short}={fmt_param_value(params.get(k))}")
    return ", ".join(bits)


def run(args: argparse.Namespace, platform: Platform) -> int:
    baseline_dir = resolve_dir(args.baseline)
    variant_dirs = [resolve_dir(p) for p in args.variants]

    runs = [load_run(baseline_dir)] + [load_run(d) for d in variant_dirs]

    # Sanity: baseline run must be the platform's baseline stack.
    if runs[0]["stack_name"] != platform.baseline_stack.name:
        sys.exit(f"ERROR: --baseline {baseline_dir} declares stack "
                 f"{runs[0]['stack_name']!r}, expected "
                 f"{platform.baseline_stack.name!r}")

    assign_labels(runs, platform)

    # Disambiguate exact-duplicate labels by appending the run timestamp.
    label_counts = Counter(r["label"] for r in runs)
    for r in runs:
        if label_counts[r["label"]] > 1:
            r["label"] = f"{r['label']} [{r['dir'].name}]"

    per_prompt, ordered_ids = collect_per_prompt(runs)

    # A prompt is "comparable" only when EVERY stack scored PASS.
    comparable_ids: list[str] = []
    excluded_ids:   list[str] = []
    for pid in ordered_ids:
        sides = per_prompt[pid]["sides"]
        if (len(sides) == len(runs)
                and all(s["verdict"] == "PASS" for s in sides.values())):
            comparable_ids.append(pid)
        else:
            excluded_ids.append(pid)

    totals_by_label = {
        r["label"]: stack_totals(per_prompt, r["label"]) for r in runs
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    if args.output_dir:
        out_dir = (args.output_dir if args.output_dir.is_absolute()
                   else (REPO_ROOT / args.output_dir))
    else:
        out_dir = platform.root / "final" / ts
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    L: list[str] = []
    render_header(L, platform, runs, ts, len(ordered_ids))
    render_run_links(L, runs, out_dir)
    render_stack_config(L, runs)
    render_legend(L)
    render_per_prompt_verdicts(L, per_prompt, ordered_ids, runs)
    render_per_prompt_metrics(L, per_prompt, ordered_ids, runs,
                              "total_tokens", "total tokens", fmt_int)
    render_per_prompt_metrics(L, per_prompt, ordered_ids, runs,
                              "wall_clock_s", "wall-clock", lambda x: f"{fmt_float(x, 1)}s")
    render_verdict_tally(L, runs, totals_by_label)
    render_tool_tally(L, runs, totals_by_label)
    render_global_comparable(L, runs, per_prompt, comparable_ids, excluded_ids)
    render_pair_comparable(L, runs, per_prompt, ordered_ids)
    render_pairwise_verdicts(L, runs, totals_by_label, per_prompt, ordered_ids)

    out_path = out_dir / "combined_comparison.md"
    out_path.write_text("\n".join(L))
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    for r in runs:
        kind = "baseline" if r is runs[0] else "variant "
        print(f"  {kind}: {r['label']}  ({r['dir']})")
    return 0


def main() -> None:
    platform = preload_platform()
    p = argparse.ArgumentParser(
        description="Render a combined N-stack comparison markdown from per-run analysis.json files."
    )
    add_arguments(p, platform)
    args = p.parse_args()
    sys.exit(run(args, platform))


if __name__ == "__main__":
    main()
