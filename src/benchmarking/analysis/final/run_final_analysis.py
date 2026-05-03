#!/usr/bin/env python3
"""
run_final_analysis.py — drive the cross-stack final analysis for one platform.

Each run dir is single-stack now, so this script consumes exactly TWO run
dirs (one for the platform's baseline stack, one for the variant stack) and
asks the LLM grader to compare them.

Workflow:
  1. Resolve which run directories to grade (--all under experiments/<platform>/runs/
     when there are exactly two dirs, or an explicit --runs <a> <b>).
  2. Read each run dir's results.json to identify which stack lives there.
     Verify the pair is exactly {baseline, variant}.
  3. For each run dir, ensure analysis_data.json exists; if missing, run
     precompute in-process.
  4. Render final_analysis_prompt.md (package data) with baseline + variant
     run-dir paths and inline analysis_data.json blobs.
  5. Spawn `claude --print` against the rendered prompt under the platform's
     analyzer config dir to produce final_analysis.{json,md}.
  6. If final_analysis.md is missing but final_analysis.json exists, fall
     back to render_final_md (in-process).

Usage:
    uv run benchmark final --platform slack --all
    uv run benchmark final --platform notion \\
        --runs experiments/notion/runs/20260428_2354__notion experiments/notion/runs/20260428_2400__hintas
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from benchmarking.analysis import precompute as precompute_mod
from benchmarking.analysis.final import render_final_md
from benchmarking.config import (
    Platform, Stack, available_platforms, preload_platform,
)
from benchmarking.paths import ANALYSIS_DIR, REPO_ROOT


PROMPT_TEMPLATE = ANALYSIS_DIR / "final" / "final_analysis_prompt.md"


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def add_arguments(p: argparse.ArgumentParser, platform: Platform) -> None:
    p.add_argument("--platform", default="slack",
                   choices=available_platforms() or None,
                   help="Platform manifest under experiments/ (default: slack)")
    p.add_argument("--runs", nargs="+", type=Path,
                   help="Two run directories (baseline + variant). "
                        "Mutually exclusive with --all.")
    p.add_argument("--all", action="store_true",
                   help="Grade every run directory under experiments/<platform>/runs/. "
                        "Requires exactly two dirs to be present.")
    p.add_argument("--output-dir", type=Path,
                   help="Where to write final_analysis.{json,md}. "
                        "Default: experiments/<platform>/final/<timestamp>/")
    p.add_argument("--prompts-file", default=str(platform.prompts_file),
                   help="Override the prompts file used by precompute.")
    p.add_argument("--timeout", type=int, default=3600,
                   help="Max seconds for the analysis agent (default 3600)")
    p.add_argument("--skip-precompute", action="store_true",
                   help="Don't auto-precompute analysis_data.json for run dirs missing it")
    p.add_argument("--skip-claude", action="store_true",
                   help="Render the prompt and exit; print the rendered prompt to stdout")


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
        sys.exit(f"ERROR: results.json missing in {run_dir}; cannot resolve stack")
    raw = json.loads(results_path.read_text())
    stacks = raw.get("stacks") or []
    if len(stacks) != 1:
        sys.exit(
            f"ERROR: results.json in {run_dir} must declare exactly one stack; "
            f"got {stacks!r}"
        )
    return platform.stack(stacks[0])


def assign_roles(platform: Platform,
                 runs: list[Path]) -> tuple[tuple[Path, Stack], tuple[Path, Stack]]:
    """Map the two run dirs onto (baseline, variant) by reading results.json."""
    by_stack: dict[str, tuple[Path, Stack]] = {}
    for r in runs:
        stack = stack_for_run(platform, r)
        if stack.name in by_stack:
            sys.exit(f"ERROR: two run dirs claim stack {stack.name!r}; "
                     "expected one baseline and one variant")
        by_stack[stack.name] = (r, stack)

    baseline_name = platform.baseline_stack.name
    variant_name  = platform.variant_stack.name
    if baseline_name not in by_stack or variant_name not in by_stack:
        sys.exit(
            f"ERROR: expected one run dir for stack {baseline_name!r} and one for "
            f"{variant_name!r}; got {sorted(by_stack)}"
        )
    return by_stack[baseline_name], by_stack[variant_name]


def ensure_analysis_data(run_dir: Path, stack: Stack, prompts_file: str) -> None:
    """Run precompute in-process if analysis_data.json is missing."""
    out = run_dir / "analysis_data.json"
    if out.exists():
        return
    print(f"  precomputing: {run_dir}  →  analysis_data.json")
    data = precompute_mod.precompute(run_dir, Path(prompts_file).resolve(), stack.name)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def render_prompt(platform: Platform,
                  baseline: tuple[Path, Stack], variant: tuple[Path, Stack],
                  output_dir: Path, timestamp: str) -> str:
    template = PROMPT_TEMPLATE.read_text()
    notes_path = ANALYSIS_DIR / "notes" / f"notes_{platform.name}.md"
    platform_notes = notes_path.read_text() if notes_path.exists() else ""
    b_dir, b_stack = baseline
    v_dir, v_stack = variant
    return (template
            .replace("{{TIMESTAMP}}",                timestamp)
            .replace("{{OUTPUT_DIR}}",               str(output_dir.resolve()))
            .replace("{{PLATFORM_DISPLAY_NAME}}",    platform.display_name)
            .replace("{{BASELINE_STACK}}",           b_stack.name)
            .replace("{{BASELINE_DISPLAY_NAME}}",    b_stack.display_name)
            .replace("{{BASELINE_RUN_DIR}}",         str(b_dir.resolve()))
            .replace("{{VARIANT_STACK}}",            v_stack.name)
            .replace("{{VARIANT_DISPLAY_NAME}}",     v_stack.display_name)
            .replace("{{VARIANT_RUN_DIR}}",          str(v_dir.resolve()))
            .replace("{{PLATFORM_NOTES}}",           platform_notes))


def spawn_claude(prompt: str, platform: Platform, timeout: int) -> int:
    env = {
        **os.environ,
        "CLAUDE_CONFIG_DIR": os.path.expanduser(platform.analysis.config_dir),
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS":
            os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "64000"),
    }
    print(f"  CLAUDE_CONFIG_DIR for analyzer: {env['CLAUDE_CONFIG_DIR']}")
    print(f"  CLAUDE_CODE_MAX_OUTPUT_TOKENS:   {env['CLAUDE_CODE_MAX_OUTPUT_TOKENS']}")
    cmd = [
        "claude",
        "--print",
        "--verbose",
        "--output-format", "stream-json",
        "--permission-mode", "bypassPermissions",
        "--model", platform.analysis.model,
        prompt,
    ]
    print(f"  Spawning analyzer (timeout={timeout}s, model={platform.analysis.model})")
    try:
        proc = subprocess.run(cmd, env=env, timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(f"ERROR: analyzer timed out after {timeout}s", file=sys.stderr)
        return 124
    except FileNotFoundError:
        sys.exit("ERROR: `claude` CLI not found on PATH")


def fallback_render_md(output_dir: Path) -> None:
    json_path = output_dir / "final_analysis.json"
    md_path   = output_dir / "final_analysis.md"
    if json_path.exists() and not md_path.exists():
        print(f"  final_analysis.md missing; rendering from {json_path.name}")
        data = json.loads(json_path.read_text())
        md = render_final_md.render(data, output_dir)
        md_path.write_text(md)


def run(args: argparse.Namespace, platform: Platform) -> int:
    section(f"Resolving run directories ({platform.name})")
    runs = resolve_runs(args, platform)
    baseline, variant = assign_roles(platform, runs)
    print(f"  baseline ({baseline[1].name}): {baseline[0]}")
    print(f"  variant  ({variant[1].name}): {variant[0]}")

    if not args.skip_precompute:
        section("Ensuring analysis_data.json for each run")
        for run_dir, stack in (baseline, variant):
            ensure_analysis_data(run_dir, stack, args.prompts_file)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = (args.output_dir
                  if args.output_dir
                  else platform.root / "final" / timestamp).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    section("Rendering final-analysis prompt")
    prompt = render_prompt(platform, baseline, variant, output_dir, timestamp)
    print(f"  output_dir: {output_dir}")
    print(f"  prompt size: {len(prompt):,} chars")

    if args.skip_claude:
        section("Rendered prompt (skipping claude invocation)")
        print(prompt)
        return 0

    section(f"Phase — Final analysis agent ({output_dir})")
    rc = spawn_claude(prompt, platform, args.timeout)

    fallback_render_md(output_dir)

    json_path = output_dir / "final_analysis.json"
    md_path   = output_dir / "final_analysis.md"
    if not json_path.exists() or not md_path.exists():
        print(f"ERROR: agent did not produce both {json_path.name} and {md_path.name}",
              file=sys.stderr)
        return 8

    print()
    print(f"  ✓ final_analysis.json → {json_path}")
    print(f"  ✓ final_analysis.md   → {md_path}")
    if rc != 0:
        print(f"  ⚠ analyzer exited non-zero ({rc}) — outputs still present")
    return 0


def main() -> None:
    platform = preload_platform()
    p = argparse.ArgumentParser(description="Cross-stack final analysis driver")
    add_arguments(p, platform)
    args = p.parse_args()
    sys.exit(run(args, platform))


if __name__ == "__main__":
    main()
