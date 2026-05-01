#!/usr/bin/env python3
"""
aggregate_final_json.py — deterministically build final_analysis.json from
two single-stack analysis.json files (no LLM grader).

Use this when you trust the per-run verdicts already on disk and just want to
roll them up into the cross-stack final-analysis JSON. Pair with
analysis/final/render_final_md.py to produce final_analysis.md.

The two run dirs must hold the platform's baseline and variant stacks,
respectively (read from each dir's results.json).

Usage:
    uv run benchmark aggregate --platform notion --all
    uv run benchmark aggregate --platform slack \\
        --runs platforms/slack/runs/20260428_2354__slack platforms/slack/runs/20260429_1015__hintas \\
        --output-dir platforms/slack/final/manual
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
    Platform, Stack, available_platforms, preload_platform,
)
from benchmarking.paths import REPO_ROOT

VERDICT_KEYS = ("PASS", "PARTIAL", "FAIL", "ERROR")
TIE_PCT = 1.0
TIE_PP = 0.5


def add_arguments(p: argparse.ArgumentParser, platform: Platform) -> None:
    p.add_argument("--platform", default="slack",
                   choices=available_platforms() or None,
                   help="Platform manifest under platforms/ (default: slack)")
    p.add_argument("--runs", nargs="+", type=Path,
                   help="Two run directories (baseline + variant). "
                        "Mutually exclusive with --all.")
    p.add_argument("--all", action="store_true",
                   help="Aggregate every run dir under platforms/<platform>/runs/. "
                        "Requires exactly two dirs to be present.")
    p.add_argument("--output-dir", type=Path,
                   help="Where to write final_analysis.json. "
                        "Default: platforms/<platform>/final/<timestamp>/")


def resolve_runs(args: argparse.Namespace, platform: Platform) -> list[Path]:
    if args.all and args.runs:
        sys.exit("ERROR: pass either --all or --runs, not both")
    if args.all:
        if not platform.output_dir.is_dir():
            sys.exit(f"ERROR: no runs directory at {platform.output_dir}")
        runs = sorted(d for d in platform.output_dir.iterdir() if d.is_dir())
        if len(runs) != 2:
            sys.exit(
                f"ERROR: --all expects exactly two run directories under "
                f"{platform.output_dir}; found {len(runs)}. "
                "Pass --runs <baseline> <variant> explicitly."
            )
        return [r.resolve() for r in runs]
    if not args.runs:
        sys.exit("ERROR: pass --all or --runs <baseline_dir> <variant_dir>")
    if len(args.runs) != 2:
        sys.exit(f"ERROR: --runs expects exactly two directories; got {len(args.runs)}")
    resolved = []
    for r in args.runs:
        path = r if r.is_absolute() else (REPO_ROOT / r)
        path = path.resolve()
        if not path.is_dir():
            sys.exit(f"ERROR: run directory does not exist: {path}")
        resolved.append(path)
    return resolved


def stack_for_run(platform: Platform, run_dir: Path) -> Stack:
    results_path = run_dir / "results.json"
    if not results_path.exists():
        sys.exit(f"ERROR: results.json missing in {run_dir}")
    raw = json.loads(results_path.read_text())
    stacks = raw.get("stacks") or []
    if len(stacks) != 1:
        sys.exit(f"ERROR: results.json in {run_dir} must declare exactly one stack; "
                 f"got {stacks!r}")
    return platform.stack(stacks[0])


def assign_roles(platform: Platform,
                 runs: list[Path]) -> tuple[tuple[Path, Stack], tuple[Path, Stack]]:
    by_stack: dict[str, tuple[Path, Stack]] = {}
    for r in runs:
        stack = stack_for_run(platform, r)
        if stack.name in by_stack:
            sys.exit(f"ERROR: two run dirs claim stack {stack.name!r}")
        by_stack[stack.name] = (r, stack)

    baseline_name = platform.baseline_stack.name
    variant_name  = platform.variant_stack.name
    if baseline_name not in by_stack or variant_name not in by_stack:
        sys.exit(
            f"ERROR: expected one run dir for {baseline_name!r} and one for "
            f"{variant_name!r}; got {sorted(by_stack)}"
        )
    return by_stack[baseline_name], by_stack[variant_name]


def load_analysis(run_dir: Path, stack: Stack) -> dict:
    """Return per-prompt rows keyed by id with the stack-side payload."""
    analysis_path = run_dir / "analysis.json"
    if not analysis_path.exists():
        sys.exit(f"ERROR: missing {analysis_path}; run per-run analysis first")
    data = json.loads(analysis_path.read_text())
    stacks = data.get("stacks") or []
    if stack.name not in stacks:
        sys.exit(f"ERROR: {analysis_path} does not declare stack {stack.name!r}; "
                 f"got {stacks!r}")
    out: dict[str, dict] = {}
    for pid, prompt in data.get("per_prompt", {}).items():
        side = prompt.get(stack.name)
        if side is None:
            continue
        out[pid] = {
            "title":      prompt.get("title", ""),
            "difficulty": prompt.get("difficulty", ""),
            "category":   prompt.get("category", ""),
            "side":       side,
        }
    return out


def per_prompt_side(side: dict) -> dict:
    tc = side.get("tool_calls", {}) or {}
    complete = int(tc.get("complete", 0))
    failed   = int(tc.get("failed", 0))
    partial  = int(tc.get("partial", 0))
    total    = complete + failed + partial
    total_tokens = side.get("total_tokens", 0)
    return {
        "verdict":          side.get("verdict", "ERROR"),
        "reasoning":        side.get("reasoning", ""),
        "noteworthy_paths": side.get("noteworthy_paths", []),
        "tools_passed":     complete,
        "tools_failed":     failed,
        "tools_partial":    partial,
        "tools_total":      total,
        "tokens_per_tool_call": (total_tokens / total) if total else 0.0,
        "initial_context":  side.get("initial_context", 0),
        "peak_context":     side.get("peak_context", 0),
        "total_tokens":     total_tokens,
        "wall_clock_s":     side.get("wall_clock_s", 0),
        "comparable":       False,
    }


def stack_totals(per_prompt: dict, stack_key: str, comparable_ids: list[str]) -> dict:
    rows = [p[stack_key] for p in per_prompt.values()]
    n = len(rows)
    verdicts = Counter(r["verdict"] for r in rows)
    tools_passed  = sum(r["tools_passed"]  for r in rows)
    tools_failed  = sum(r["tools_failed"]  for r in rows)
    tools_partial = sum(r["tools_partial"] for r in rows)
    tools_total   = sum(r["tools_total"]   for r in rows)

    cmp_rows = [per_prompt[pid][stack_key] for pid in comparable_ids]
    cmp_n = len(cmp_rows)
    cmp_total_tokens = sum(r["total_tokens"] for r in cmp_rows) if cmp_rows else 0
    cmp_total_tools  = sum(r["tools_total"]  for r in cmp_rows) if cmp_rows else 0

    return {
        "verdicts": {k: verdicts.get(k, 0) for k in VERDICT_KEYS},
        "pass_rate":      (verdicts.get("PASS", 0) / n) if n else 0.0,
        "tools_passed":   tools_passed,
        "tools_failed":   tools_failed,
        "tools_partial":  tools_partial,
        "tools_total":    tools_total,
        "tool_pass_rate": (tools_passed / tools_total) if tools_total else 0.0,
        "comparable_n":            cmp_n,
        "comparable_total_tokens": cmp_total_tokens,
        "comparable_avg_initial_context": mean(r["initial_context"] for r in cmp_rows) if cmp_rows else None,
        "comparable_avg_peak_context":    mean(r["peak_context"]    for r in cmp_rows) if cmp_rows else None,
        "comparable_avg_wall_clock_s":    mean(r["wall_clock_s"]    for r in cmp_rows) if cmp_rows else None,
        "comparable_avg_tokens_per_prompt":    (cmp_total_tokens / cmp_n) if cmp_n else None,
        "comparable_avg_tokens_per_tool_call": (cmp_total_tokens / cmp_total_tools) if cmp_total_tools else None,
    }


def lower_wins(b_val, v_val,
               baseline_label: str, variant_label: str) -> tuple[str, float]:
    """For metrics where lower is better. Returns (winner, margin_pct)."""
    if b_val is None or v_val is None:
        return "Tie", 0.0
    if b_val == 0 and v_val == 0:
        return "Tie", 0.0
    slow, fast = max(b_val, v_val), min(b_val, v_val)
    margin = ((slow - fast) / slow * 100.0) if slow else 0.0
    if margin < TIE_PCT:
        return "Tie", margin
    return (variant_label if v_val < b_val else baseline_label), margin


def higher_wins_pp(b_val, v_val,
                   baseline_label: str, variant_label: str) -> tuple[str, float]:
    """For pass_rate-style metrics. Returns (winner, margin_pp)."""
    if b_val is None or v_val is None:
        return "Tie", 0.0
    margin_pp = abs(b_val - v_val) * 100.0
    if margin_pp < TIE_PP:
        return "Tie", margin_pp
    return (baseline_label if b_val > v_val else variant_label), margin_pp


def higher_wins_pct(b_val, v_val,
                    baseline_label: str, variant_label: str) -> tuple[str, float]:
    if b_val is None or v_val is None:
        return "Tie", 0.0
    if b_val == 0 and v_val == 0:
        return "Tie", 0.0
    high, low = max(b_val, v_val), min(b_val, v_val)
    margin = ((high - low) / high * 100.0) if high else 0.0
    if margin < TIE_PCT:
        return "Tie", margin
    return (baseline_label if b_val > v_val else variant_label), margin


def build_verdict(b_totals: dict, v_totals: dict,
                  baseline_label: str, variant_label: str) -> dict:
    speed_w,  speed_m  = lower_wins(b_totals.get("comparable_avg_wall_clock_s"),
                                    v_totals.get("comparable_avg_wall_clock_s"),
                                    baseline_label, variant_label)
    tokens_w, tokens_m = lower_wins(b_totals.get("comparable_total_tokens"),
                                    v_totals.get("comparable_total_tokens"),
                                    baseline_label, variant_label)
    peak_w,   peak_m   = lower_wins(b_totals.get("comparable_avg_peak_context"),
                                    v_totals.get("comparable_avg_peak_context"),
                                    baseline_label, variant_label)
    acc_w,    acc_m    = higher_wins_pp(b_totals.get("pass_rate"),
                                        v_totals.get("pass_rate"),
                                        baseline_label, variant_label)
    tool_w,   _        = higher_wins_pct(b_totals.get("tool_pass_rate"),
                                         v_totals.get("tool_pass_rate"),
                                         baseline_label, variant_label)

    wins = Counter(w for w in (speed_w, tokens_w, peak_w, acc_w, tool_w) if w != "Tie")
    if not wins:
        winner = "Tie"
    elif len(wins) == 1:
        winner = next(iter(wins))
    else:
        top, second = wins.most_common(2)
        winner = top[0] if top[1] > second[1] else "Tie"

    summary = (f"{winner} wins on accuracy={acc_w} ({acc_m:.1f}pp), "
               f"speed={speed_w} ({speed_m:.1f}%), "
               f"tokens={tokens_w} ({tokens_m:.1f}%).")

    return {
        "winner":                  winner,
        "speed_winner":            speed_w,  "speed_margin_pct":        speed_m,
        "tokens_winner":           tokens_w, "tokens_margin_pct":       tokens_m,
        "peak_context_winner":     peak_w,   "peak_context_margin_pct": peak_m,
        "accuracy_winner":         acc_w,    "accuracy_margin_pp":      acc_m,
        "tool_reliability_winner": tool_w,
        "summary":                 summary,
    }


def build(platform: Platform,
          baseline: tuple[Path, Stack], variant: tuple[Path, Stack],
          timestamp: str) -> dict:
    b_dir, b_stack = baseline
    v_dir, v_stack = variant

    b_rows = load_analysis(b_dir, b_stack)
    v_rows = load_analysis(v_dir, v_stack)

    all_ids = sorted(set(b_rows) | set(v_rows), key=lambda x: int(x))
    per_prompt: dict[str, dict] = {}
    comparable_ids: list[str] = []
    excluded_ids:   list[str] = []

    for pid in all_ids:
        b_meta = b_rows.get(pid)
        v_meta = v_rows.get(pid)
        title      = (b_meta or v_meta)["title"]
        difficulty = (b_meta or v_meta)["difficulty"]
        category   = (b_meta or v_meta)["category"]

        b_side = per_prompt_side(b_meta["side"]) if b_meta else _missing_side()
        v_side = per_prompt_side(v_meta["side"]) if v_meta else _missing_side()
        comparable = (b_side["verdict"] == "PASS" and v_side["verdict"] == "PASS")
        b_side["comparable"] = comparable
        v_side["comparable"] = comparable
        per_prompt[pid] = {
            "title":      title,
            "difficulty": difficulty,
            "category":   category,
            b_stack.name: b_side,
            v_stack.name: v_side,
        }
        (comparable_ids if comparable else excluded_ids).append(pid)

    b_totals = stack_totals(per_prompt, b_stack.name, comparable_ids)
    v_totals = stack_totals(per_prompt, v_stack.name, comparable_ids)
    verdict = build_verdict(b_totals, v_totals,
                            b_stack.display_name, v_stack.display_name)

    return {
        "timestamp":         timestamp,
        "platform":          platform.display_name,
        "baseline_stack":    b_stack.name,
        "variant_stack":     v_stack.name,
        "baseline_display":  b_stack.display_name,
        "variant_display":   v_stack.display_name,
        "baseline_run_dir":  str(b_dir),
        "variant_run_dir":   str(v_dir),
        "n_prompts":         len(per_prompt),
        "per_prompt":        per_prompt,
        "totals": {
            b_stack.name: b_totals,
            v_stack.name: v_totals,
            "comparable_prompt_ids": comparable_ids,
            "excluded_prompt_ids":   excluded_ids,
        },
        "verdict": verdict,
    }


def _missing_side() -> dict:
    return {
        "verdict": "ERROR", "reasoning": "row missing in this stack's analysis.json",
        "noteworthy_paths": [],
        "tools_passed": 0, "tools_failed": 0, "tools_partial": 0, "tools_total": 0,
        "tokens_per_tool_call": 0.0,
        "initial_context": 0, "peak_context": 0,
        "total_tokens": 0,    "wall_clock_s": 0,
        "comparable": False,
    }


def run(args: argparse.Namespace, platform: Platform) -> int:
    runs = resolve_runs(args, platform)
    baseline, variant = assign_roles(platform, runs)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if args.output_dir:
        out_dir = args.output_dir if args.output_dir.is_absolute() else (REPO_ROOT / args.output_dir)
    else:
        out_dir = platform.root / "final" / timestamp
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    final = build(platform, baseline, variant, timestamp)
    out_path = out_dir / "final_analysis.json"
    out_path.write_text(json.dumps(final, indent=2))
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"  baseline: {final['baseline_display']}  ({final['baseline_run_dir']})")
    print(f"  variant:  {final['variant_display']}   ({final['variant_run_dir']})")
    v = final["verdict"]
    print(f"  winner: {v['winner']}  — accuracy={v['accuracy_winner']} ({v['accuracy_margin_pp']:.1f}pp), "
          f"speed={v['speed_winner']} ({v['speed_margin_pct']:.1f}%), "
          f"tokens={v['tokens_winner']} ({v['tokens_margin_pct']:.1f}%)")
    print(f"  next: uv run benchmark render-final {out_dir}")
    return 0


def main() -> None:
    platform = preload_platform()
    p = argparse.ArgumentParser(description="Aggregate analysis.json into final_analysis.json")
    add_arguments(p, platform)
    args = p.parse_args()
    sys.exit(run(args, platform))


if __name__ == "__main__":
    main()
