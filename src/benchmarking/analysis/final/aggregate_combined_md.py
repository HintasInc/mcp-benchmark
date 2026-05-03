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
        --baseline experiments/notion/runs/20260429_205418__notion \\
        --variants experiments/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off \\
                   experiments/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off \\
                   experiments/notion/runs/20260430_100101__hintas__topk10_batch-off_max5_rag-off

    # default output: experiments/<platform>/results.md
    # override with --output-dir <path>
"""
from __future__ import annotations

import argparse
import json
import os
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

TIE_PCT = 1.0
TIE_PP  = 0.5


def add_arguments(p: argparse.ArgumentParser, platform: Platform) -> None:
    p.add_argument("--platform", default="notion",
                   choices=available_platforms() or None,
                   help="Platform manifest under experiments/ (default: notion)")
    p.add_argument("--baseline", type=Path, required=True,
                   help="Run directory for the baseline stack.")
    p.add_argument("--variants", nargs="+", type=Path, action="extend",
                   required=True,
                   help="One or more variant run directories. May be repeated, "
                        "e.g. `--variants A B` or `--variants A --variants B`.")
    p.add_argument("--output-dir", type=Path,
                   help="Where to write results.md. "
                        "Default: experiments/<platform>/")
    p.add_argument("--force", action="store_true",
                   help="Overwrite results.md without prompting.")
    p.add_argument("--verbose", action="store_true",
                   help="Include per-prompt detail tables (verdicts, tokens, "
                        "wall-clock). Default: summarized — tallies and "
                        "comparable metrics only.")


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
        "total_tokens":  side.get("total_tokens", 0),
        "wall_clock_s":  side.get("wall_clock_s", 0),
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
        "comparable_avg_wall_clock_s":         mean(r["wall_clock_s"] for r in rows) if rows else None,
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
    acc_w,    acc_m    = higher_wins_pp(b_totals.get("pass_rate"),
                                        v_totals.get("pass_rate"),
                                        b_label, v_label)
    tool_w,   _        = higher_wins_pct(b_totals.get("tool_pass_rate"),
                                         v_totals.get("tool_pass_rate"),
                                         b_label, v_label)

    wins = Counter(w for w in (speed_w, tokens_w, acc_w, tool_w) if w != "Tie")
    if not wins:
        winner = "Tie"
    elif len(wins) == 1:
        winner = next(iter(wins))
    else:
        top, second = wins.most_common(2)
        winner = top[0] if top[1] > second[1] else "Tie"

    return {
        "winner": winner,
        "accuracy_winner":  acc_w,    "accuracy_margin_pp":  acc_m,
        "speed_winner":     speed_w,  "speed_margin_pct":    speed_m,
        "tokens_winner":    tokens_w, "tokens_margin_pct":   tokens_m,
        "tool_reliability_winner": tool_w,
    }


# ---------------------------------------------------------------------------
# rendering

def run_dir_link(run_dir: Path, output_dir: Path) -> str:
    """Render the run-dir name as a link to its analysis.md (relative path).

    Falls back to a plain code span when analysis.md is missing.
    """
    md = run_dir / "analysis.md"
    name = run_dir.name
    if not md.exists():
        return f"`{name}` _(missing analysis.md)_"
    try:
        target = os.path.relpath(md.resolve(), start=output_dir.resolve())
    except ValueError:
        target = str(md.resolve())
    return f"[`{name}`]({target})"


def render_header(L, platform, runs, ts, n_prompts):
    L.append(f"# Combined Benchmark Comparison — {platform.display_name} — {ts}")
    L.append("")
    L.append(f"**Scope:** {n_prompts} prompts × {len(runs)} stacks "
             f"(baseline + {len(runs) - 1} variant{'s' if len(runs) != 2 else ''}).")
    L.append("")


def render_runs_list(L, runs, output_dir):
    L.append("## Measured against")
    L.append("")
    for run in runs:
        kind = "baseline" if run is runs[0] else "variant"
        L.append(f"- **{run['label']}** ({kind}) — {run_dir_link(run['dir'], output_dir)}")
    L.append("")


def render_legend(L):
    L.append("## Verdict legend")
    L.append("")
    L.append("- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.")
    L.append("- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.")
    L.append("- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ")
    L.append("- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or "
             "`result_subtype: error` with no usable output).")
    L.append("")


def render_per_prompt_verdicts(L, per_prompt, ordered_ids, runs):
    """Single combined table with one verdict column per stack."""
    L.append("## Per-prompt verdicts")
    L.append("")
    headers = ["ID", "Title", "Diff"] + [r["label"] for r in runs]
    aligns  = ["---:", ":------", ":----:"] + [":------:"] * len(runs)
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")
    for pid in ordered_ids:
        row = per_prompt[pid]
        title = row["title"].replace("|", "\\|")
        cells = [pid, title, row["difficulty"]]
        for r in runs:
            side = row["sides"].get(r["label"])
            cells.append(f"{VERDICT_GLYPH[side['verdict']]} {side['verdict']}"
                         if side else "—")
        L.append("| " + " | ".join(cells) + " |")
    L.append("")


def render_per_prompt_metrics(L, per_prompt, ordered_ids, runs, metric_key, metric_label, fmt):
    """Single combined table: ID/Title, baseline value, every variant value,
    then a Δ-vs-baseline column per variant. Δ is shown only when both stacks PASS."""
    baseline = runs[0]
    variants = runs[1:]
    L.append(f"## Per-prompt {metric_label}")
    L.append("")
    headers = ["ID", "Title", baseline["label"]] + [v["label"] for v in variants]
    headers += [f"Δ {v['label']} vs {baseline['label']}" for v in variants]
    aligns  = ["---:", ":------"] + ["---:"] * (len(headers) - 2)
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")
    for pid in ordered_ids:
        row = per_prompt[pid]
        title = row["title"].replace("|", "\\|")
        b_side = row["sides"].get(baseline["label"])
        cells = [pid, title]
        cells.append(fmt(b_side[metric_key]) if b_side else "—")
        for v in variants:
            v_side = row["sides"].get(v["label"])
            cells.append(fmt(v_side[metric_key]) if v_side else "—")
        for v in variants:
            v_side = row["sides"].get(v["label"])
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
    """Single combined table: rows = verdict metrics, columns = each stack."""
    L.append("## Verdict tallies")
    L.append("")
    headers = ["Metric"] + [r["label"] for r in runs]
    aligns  = [":-------"] + ["---:"] * len(runs)
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")
    for k in VERDICT_KEYS:
        cells = [k]
        for r in runs:
            cells.append(str(totals_by_label[r["label"]]["verdicts"].get(k, 0)))
        L.append("| " + " | ".join(cells) + " |")
    cells = ["Success rate"]
    for r in runs:
        cells.append(fmt_pct(totals_by_label[r["label"]]["pass_rate"]))
    L.append("| " + " | ".join(cells) + " |")
    L.append("")


def render_tool_tally(L, runs, totals_by_label):
    """Single combined table: rows = tool-call metrics, columns = each stack."""
    L.append("## Tool-call tallies")
    L.append("")
    headers = ["Metric"] + [r["label"] for r in runs]
    aligns  = [":-------"] + ["---:"] * len(runs)
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")
    rows = (
        ("Tools complete", "tools_passed"),
        ("Tools failed",   "tools_failed"),
        ("Tools partial",  "tools_partial"),
        ("Total",          "tools_total"),
    )
    for label, key in rows:
        cells = [label]
        for r in runs:
            cells.append(str(totals_by_label[r["label"]][key]))
        L.append("| " + " | ".join(cells) + " |")
    cells = ["Tool pass rate"]
    for r in runs:
        cells.append(fmt_pct(totals_by_label[r["label"]]["tool_pass_rate"]))
    L.append("| " + " | ".join(cells) + " |")
    L.append("")


COMPARABLE_ROWS = (
    ("Total tokens",            "comparable_total_tokens",            "int"),
    ("Avg tokens / prompt",     "comparable_avg_tokens_per_prompt",   "int"),
    ("Avg tokens / tool call",  "comparable_avg_tokens_per_tool_call","int"),
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
    """Single combined table: rows = comparable metrics, columns = each stack."""
    L.append("## Global comparable metrics")
    L.append("> Only the prompts where every stack passed are included.")
    cmp_str = ", ".join(comparable_ids) if comparable_ids else "(none)"
    L.append(f"- Included count: {len(comparable_ids)} (prompt IDs: `{cmp_str}`)")
    L.append(f"- Excluded count: {len(excluded_ids)}")
    L.append("")
    if not comparable_ids:
        L.append("_No prompts where every stack passed — see the per-pair "
                 "comparable metrics below for fairer apples-to-apples numbers._")
        L.append("")
        return

    metrics_by_label = {
        r["label"]: comparable_metrics(per_prompt, r["label"], comparable_ids)
        for r in runs
    }
    headers = ["Metric"] + [r["short_label"] for r in runs]
    aligns  = [":-------"] + ["---:"] * len(runs)
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")
    for label, key, kind in COMPARABLE_ROWS:
        cells = [label]
        for r in runs:
            cells.append(_fmt_comparable(metrics_by_label[r["label"]].get(key), kind))
        L.append("| " + " | ".join(cells) + " |")
    L.append("")


def render_pair_comparable(L, runs, per_prompt, ordered_ids, totals_by_label):
    """Single combined table. For each variant a 3-column block (baseline value
    on that pair / variant value / Δ) so all pairs sit side-by-side. The
    baseline value differs across blocks because each pair uses its own
    intersection.

    Verdict rows (success rate, tool reliability, overall winner) are appended
    to the same table so the reader sees the full pairwise picture in one place.

    When there is exactly one variant, the per-pair subset is identical to the
    global "every stack PASS" subset, so we render this section under the
    `## Global comparable metrics` heading and skip the dedicated global block."""
    baseline = runs[0]
    variants = runs[1:]
    multi = len(variants) > 1
    if multi:
        L.append("## Per-pair comparable metrics (baseline ∩ variant PASS)")
    else:
        L.append("## Global comparable metrics")
    L.append("")
    L.append("> For each variant, this restricts to prompts where **both** the "
             "baseline and that variant passed — the fair apples-to-apples "
             "subset for token and speed comparisons.")
    if multi:
        L.append("> Each variant column group uses its own pair-specific "
                 "intersection, so baseline values differ across groups.")
    L.append("")

    b_short = baseline["short_provider"]
    b_totals = totals_by_label[baseline["label"]]

    pair_data = []
    for v in variants:
        ids = pair_comparable_ids(per_prompt, ordered_ids,
                                  baseline["label"], v["label"])
        b_metrics = comparable_metrics(per_prompt, baseline["label"], ids)
        v_metrics = comparable_metrics(per_prompt, v["label"], ids)
        v_totals = totals_by_label[v["label"]]
        verdict = pairwise_verdict(
            {**b_totals, **b_metrics},
            {**v_totals, **v_metrics},
            baseline["label"], v["label"],
        )
        pair_data.append({
            "v":         v,
            "ids":       ids,
            "b_metrics": b_metrics,
            "v_metrics": v_metrics,
            "v_totals":  v_totals,
            "verdict":   verdict,
        })

    for d in pair_data:
        ids_str = ", ".join(d["ids"]) if d["ids"] else "(none)"
        if multi:
            L.append(f"- {baseline['short_label']} ∩ {d['v']['short_label']}: "
                     f"n={len(d['ids'])}, IDs `{ids_str}`")
        else:
            L.append(f"- Comparable prompt IDs: `{ids_str}` (count: {len(d['ids'])})")
            L.append(f"- Excluded count: {len(ordered_ids) - len(d['ids'])}")
    L.append("")

    if not any(d["ids"] for d in pair_data):
        L.append("_No comparable prompts; metrics suppressed._")
        L.append("")
        return

    headers = ["Metric"]
    aligns  = [":-------"]
    for d in pair_data:
        v_short = d["v"]["short_provider"]
        suffix = f" ({d['v']['short_provider']} pair)" if multi else ""
        headers.append(f"{baseline['short_label']}{suffix}")
        headers.append(d["v"]["short_label"])
        headers.append(f"Δ {v_short} - {b_short}")
        aligns.extend(["---:", "---:", "---:"])
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(aligns) + "|")

    for label, key, kind in COMPARABLE_ROWS:
        cells = [label]
        for d in pair_data:
            if not d["ids"]:
                cells.extend(["—", "—", "—"])
                continue
            b_val = d["b_metrics"].get(key)
            v_val = d["v_metrics"].get(key)
            cells.append(_fmt_comparable(b_val, kind))
            cells.append(_fmt_comparable(v_val, kind))
            if b_val is None or v_val is None:
                cells.append("—")
            elif kind == "int":
                cells.append(fmt_delta_int(v_val - b_val))
            elif kind == "float1":
                cells.append(fmt_delta_float(v_val - b_val, 1))
            else:
                cells.append(fmt_delta_float(v_val - b_val, 2))
        L.append("| " + " | ".join(cells) + " |")

    cells = ["Success rate"]
    for d in pair_data:
        b_rate = b_totals["pass_rate"]
        v_rate = d["v_totals"]["pass_rate"]
        cells.append(fmt_pct(b_rate))
        cells.append(fmt_pct(v_rate))
        cells.append(f"{fmt_delta_float((v_rate - b_rate) * 100.0, 1)} pp")
    L.append("| " + " | ".join(cells) + " |")

    cells = ["Tool pass rate"]
    for d in pair_data:
        b_rate = b_totals["tool_pass_rate"]
        v_rate = d["v_totals"]["tool_pass_rate"]
        cells.append(fmt_pct(b_rate))
        cells.append(fmt_pct(v_rate))
        cells.append(f"{fmt_delta_float((v_rate - b_rate) * 100.0, 1)} pp")
    L.append("| " + " | ".join(cells) + " |")
    L.append("")


def render_pairwise_verdicts(L, runs, totals_by_label, per_prompt, ordered_ids):
    """Per-variant 2-column table (Metric | Result). Each result cell reads as
    `{winner display name} wins by {margin}`. The header row is intentionally
    blank since the variant identity is already encoded in each cell."""
    baseline = runs[0]
    variants = runs[1:]
    multi    = len(variants) > 1
    b_totals = totals_by_label[baseline["label"]]

    L.append("## Pairwise verdicts")
    L.append("")

    metric_rows = (
        ("Success rate", "accuracy_winner",
            lambda d: f"+{fmt_float(d['accuracy_margin_pp'], 1)} percentage points"),
        ("Speed",        "speed_winner",
            lambda d: f"+{fmt_float(d['speed_margin_pct'], 1)}%"),
        ("Tokens",       "tokens_winner",
            lambda d: f"+{fmt_float(d['tokens_margin_pct'], 1)}%"),
        ("Tool reliability", "tool_reliability_winner", lambda d: ""),
    )

    def result_text(winner: str, margin: str) -> str:
        if winner == "Tie":
            return "Tie"
        return f"{winner} wins by {margin}" if margin else f"{winner} wins"

    for v in variants:
        ids = pair_comparable_ids(per_prompt, ordered_ids,
                                  baseline["label"], v["label"])
        b_metrics = comparable_metrics(per_prompt, baseline["label"], ids)
        v_metrics = comparable_metrics(per_prompt, v["label"],        ids)
        b_for_pair = {**b_totals, **b_metrics}
        v_for_pair = {**totals_by_label[v["label"]], **v_metrics}
        d = pairwise_verdict(b_for_pair, v_for_pair,
                             baseline["label"], v["label"])

        if multi:
            L.append(f"### {v['label']} vs {baseline['label']}")
            L.append("")

        L.append("<table>")
        for metric_label, winner_key, margin_fn in metric_rows:
            L.append(f"<tr><td>{metric_label}</td>"
                     f"<td>{result_text(d[winner_key], margin_fn(d))}</td></tr>")
        overall = "<b>Tie</b>" if d["winner"] == "Tie" else f"<b>{d['winner']}</b>"
        L.append(f"<tr><td><b>Overall winner</b></td><td>{overall}</td></tr>")
        L.append("</table>")
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


def assign_short_labels(runs: list[dict], platform: Platform) -> None:
    """Mutate each run dict to include a short provider tag and short label.

    Used by the comparable-metrics tables so headers stay scannable:
      `<Platform> MCP - Official` for the baseline,
      `<Platform> MCP - Hintas` (with optional disambiguator) for each variant.
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
    baseline_stack_name = platform.baseline_stack.name
    for r in runs:
        provider = "Official" if r["stack_name"] == baseline_stack_name else "Hintas"
        if stack_count[r["stack_name"]] > 1:
            params = r["hintas_params"] or {}
            keys = differing_keys.get(r["stack_name"], [])
            suffix = _format_param_subset(params, keys) if params else ""
            if not suffix:
                seen[r["stack_name"]] = seen.get(r["stack_name"], 0) + 1
                suffix = f"#{seen[r['stack_name']]}"
            provider = f"{provider} ({suffix})"
        r["short_provider"] = provider
        r["short_label"]    = f"{platform.display_name} MCP - {provider}"


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
    assign_short_labels(runs, platform)

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
        out_dir = platform.root
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "results.md"
    if out_path.exists() and not getattr(args, "force", False):
        if not sys.stdin.isatty():
            sys.exit(f"ERROR: {out_path} already exists; pass --force to overwrite.")
        try:
            reply = input(f"{out_path} already exists. Overwrite? [y/N]: ").strip().lower()
        except EOFError:
            reply = ""
        if reply not in ("y", "yes"):
            print("aborted; existing results.md left unchanged.")
            return 1

    verbose = bool(getattr(args, "verbose", False))

    L: list[str] = []
    render_header(L, platform, runs, ts, len(ordered_ids))
    render_runs_list(L, runs, out_dir)
    render_legend(L)
    if verbose:
        render_per_prompt_verdicts(L, per_prompt, ordered_ids, runs)
        render_per_prompt_metrics(L, per_prompt, ordered_ids, runs,
                                  "total_tokens", "total tokens", fmt_int)
        render_per_prompt_metrics(L, per_prompt, ordered_ids, runs,
                                  "wall_clock_s", "wall-clock", lambda x: f"{fmt_float(x, 1)}s")
    render_verdict_tally(L, runs, totals_by_label)
    render_tool_tally(L, runs, totals_by_label)
    if len(runs) > 2:
        render_global_comparable(L, runs, per_prompt, comparable_ids, excluded_ids)
    render_pair_comparable(L, runs, per_prompt, ordered_ids, totals_by_label)

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
