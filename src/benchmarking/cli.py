#!/usr/bin/env python3
"""
cli.py — single-entrypoint orchestrator for MCP benchmarks.

Subcommands:
  run         Run a benchmark pipeline (reset → seed → benchmark; optional
              --analyze chains per-run grading).
  precompute  Build analysis_data.json from raw session logs in a run dir.
  analyze     Per-run grading: produces analysis.{json,md} inside the run dir.
              Auto-runs precompute when analysis_data.json is missing.
  final       LLM-graded cross-stack final analysis (baseline vs variant).
  aggregate   Deterministic 2-stack rollup (baseline vs variant) → final_analysis.json.
              Skip the LLM grader when you trust the per-run verdicts.
  combine     Deterministic N-stack combined comparison (1 baseline + N variants)
              → combined_comparison.md.
  scaffold    Generate the skeleton for a new benchmark platform.

Tokens are read from `experiments/<platform>/.env` and `<repo>/.env` (loaded automatically).
They are NOT accepted on the command line.

Run subcommand pipeline:
  1. Reset the selected stack's workspace.
  2. Full-seed the selected stack's workspace.
  3. Run benchmarks for each selected prompt against the selected stack.
     Logs land under <output>/<run_subdir>/p<id>/.
  4. (Optional, --analyze) Per-stack grading against the new run dir,
     producing analysis_data.json + analysis.json + analysis.md.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from benchmarking import runner
from benchmarking.analysis import precompute as precompute_mod
from benchmarking.analysis.final import (
    aggregate_combined_md,
    aggregate_final_json,
    run_final_analysis,
)
from benchmarking.analysis.per_run import run_per_run_analysis
from benchmarking import scaffold as scaffold_mod
from benchmarking.config import (
    Platform, Stack, RUN_TS_FORMAT, available_platforms,
    build_run_subdir, preload_platform,
)
from benchmarking.paths import REPO_ROOT


# ─────────────────────────────────────────────────────────────
# `run` subcommand — the original benchmark pipeline
# ─────────────────────────────────────────────────────────────

def add_run_arguments(p: argparse.ArgumentParser, platform: Platform) -> None:
    p.add_argument("--platform",     default="slack",
                   choices=available_platforms() or None,
                   help="Platform manifest under experiments/ (default: slack)")
    p.add_argument("--stack",        required=True,
                   choices=platform.stack_names,
                   help="Which stack from the platform manifest to benchmark")
    p.add_argument("--prompts-file", default=str(platform.prompts_file))
    p.add_argument("--output-dir",   default=str(platform.output_dir),
                   help="Where run directories are written (default: experiments/<platform>/runs)")
    p.add_argument("--prompt-ids",   nargs="+")
    p.add_argument("--difficulty",   nargs="+")
    p.add_argument("--category",     nargs="+")
    p.add_argument("--feasibility",  nargs="+", default=["core"])
    p.add_argument("--timeout",      type=int, default=300)
    p.add_argument("--dry-run",      action="store_true")
    p.add_argument("--skip-setup",   action="store_true",
                   help="Skip reset+seed phases (workspace is already in baseline state)")
    p.add_argument("--reset-script",  default=str(platform.reset_script) if platform.reset_script else None,
                   help="Per-prompt reset script (default: platform manifest)")
    p.add_argument("--verify-script", default=str(platform.verify_script) if platform.verify_script else None,
                   help="Post-reset verification script (default: platform manifest)")
    p.add_argument("--skip-reset",    action="store_true",
                   help="Skip the per-prompt workspace reset between sessions")
    p.add_argument("--verify",        action="store_true",
                   help="Run post-reset state verification (off by default)")
    p.add_argument("--verify-every-n", type=int, default=1, metavar="N",
                   help="Run pre-prompt verify every Nth prompt instead of every prompt "
                        "(default 1 = every prompt). The first prompt is always verified. "
                        "Ignored unless --verify is set.")
    p.add_argument("--strict-verify", action="store_true",
                   help="Skip any prompt where the workspace has hard drift after reset")

    # Hintas-only label flags. Used solely to compose the run-dir name so
    # repeat runs against different Hintas server configurations don't collide.
    hintas = p.add_argument_group(
        "Hintas labels",
        "Recorded in the run-dir name when --stack hintas. Configured on the "
        "Hintas server itself; the script does not forward these to the MCP."
    )
    hintas.add_argument("--search-top-k", type=int, default=10,
                        help="SEARCH_TOP_K used by the Hintas server (default 10)")
    hintas.add_argument("--search-batch-enabled", action="store_true",
                        help="SEARCH_BATCH_ENABLED on the Hintas server")
    hintas.add_argument("--search-max-results", type=int, default=10,
                        help="SEARCH_MAX_RESULTS used by the Hintas server (default 10)")
    hintas.add_argument("--rag-enabled", action="store_true",
                        help="Whether the Hintas RAG pipeline / documentation is set up")

    p.add_argument("--analyze", action="store_true",
                   help="After phase 3, chain per-run analysis against the new run dir "
                        "to produce analysis.json + analysis.md.")
    p.add_argument("--analysis-timeout", type=int, default=1800,
                   help="Per-run analysis agent timeout in seconds (default 1800, "
                        "applies only when --analyze is set)")
    p.add_argument("--verbose-analysis", action="store_true",
                   help="When chaining --analyze, render analysis.md with per-prompt "
                        "detail tables (default: summarized).")


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def token_for(stack: Stack) -> str:
    return os.environ.get(stack.token_env, "")


def require_token(platform: Platform, stack: Stack) -> None:
    if token_for(stack):
        return
    env_files = [platform.root / ".env", REPO_ROOT / ".env"]
    hint = " or ".join(str(p) for p in env_files)
    print(f"ERROR: ${stack.token_env} is not set; add it to {hint}", file=sys.stderr)
    sys.exit(2)


def run_with_token(script: Path, token: str, token_env: str | None, label: str,
                   extra_args: list[str] | None = None) -> int:
    """Run a bench script, injecting the stack token under `token_env`.

    When `token_env` is None the script self-resolves its credentials (multi-API
    surfaces read stack-prefixed vars from the platform .env); nothing is injected.
    Returns the script's exit code."""
    cmd = [sys.executable, str(script), *(extra_args or [])]
    env = {**os.environ}
    if token_env:
        env[token_env] = token
    print(f"  [{label}] → {' '.join(cmd)}")
    proc = subprocess.run(cmd, env=env)
    if proc.returncode != 0:
        print(f"  [{label}] exited with code {proc.returncode}", file=sys.stderr)
    return proc.returncode


def phase_reset(args: argparse.Namespace, platform: Platform, stack: Stack) -> None:
    section(f"Phase 1 — Resetting {stack.display_name} workspace")
    if args.dry_run:
        print(f"  [DRY RUN] would reset {stack.name} workspace")
        return
    for surface in platform.setup_surfaces:
        rc = run_with_token(
            surface.reset_script, token_for(stack),
            surface.token_env, f"{stack.name} reset [{surface.name}]",
            ["--allow-missing-state", "--stack", stack.name],
        )
        if rc != 0:
            print(f"ERROR: reset phase failed for {surface.name} — aborting", file=sys.stderr)
            sys.exit(3)


def phase_seed(args: argparse.Namespace, platform: Platform, stack: Stack) -> None:
    section(f"Phase 2 — Full-seeding {stack.display_name} workspace")
    if args.dry_run:
        print(f"  [DRY RUN] would full-seed {stack.name} workspace")
        return
    for surface in platform.setup_surfaces:
        rc = run_with_token(
            surface.seed_script, token_for(stack),
            surface.token_env, f"{stack.name} seed [{surface.name}]",
            ["--stack", stack.name],
        )
        if rc != 0:
            print(f"ERROR: seed phase failed for {surface.name} — aborting", file=sys.stderr)
            sys.exit(4)


def phase_benchmark(args: argparse.Namespace, platform: Platform,
                    stack: Stack, run_subdir: str) -> Path:
    section(f"Phase 3 — Running benchmarks ({run_subdir})")
    args.run_subdir = run_subdir
    runner.run(args, platform, stack)
    return Path(args.output_dir) / run_subdir


def phase_analyze(args: argparse.Namespace, platform: Platform, run_dir: Path) -> None:
    """Chain the per-run analyzer in-process against the new run dir."""
    section(f"Phase 4 — Per-run analysis ({run_dir.name})")
    analyze_args = argparse.Namespace(
        platform=platform.name,
        runs=[run_dir],
        all=False,
        output_dir=platform.output_dir,
        prompts_file=args.prompts_file,
        timeout=args.analysis_timeout,
        skip_precompute=False,
        skip_claude=False,
        continue_on_error=False,
        prompt_ids=None,
        regrade=False,
        verbose=args.verbose_analysis,
    )
    rc = run_per_run_analysis.run(analyze_args, platform)
    if rc != 0:
        print(f"ERROR: per-run analysis exited with code {rc}", file=sys.stderr)
        sys.exit(rc)


def cmd_run(args: argparse.Namespace, platform: Platform) -> int:
    stack = platform.stack(args.stack)
    require_token(platform, stack)

    run_ts     = datetime.now().strftime(RUN_TS_FORMAT)
    run_subdir = build_run_subdir(args, platform, stack, run_ts)

    if not args.skip_setup:
        phase_reset(args, platform, stack)
        phase_seed(args, platform, stack)
    else:
        section("Setup (reset + seed) skipped via --skip-setup")

    run_dir = phase_benchmark(args, platform, stack, run_subdir)

    if args.analyze:
        phase_analyze(args, platform, run_dir)

    section("Done")
    print(f"  Run directory: {run_dir}")
    if args.analyze:
        print(f"  Analysis:      {run_dir}/analysis.json + analysis.md")
    print("  (Cross-stack final analysis is a separate step — "
          "see `uv run benchmark final --help`.)")
    return 0


# ─────────────────────────────────────────────────────────────
# Top-level dispatch
# ─────────────────────────────────────────────────────────────

def build_parser(platform: Platform) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="MCP benchmark orchestrator (run, analyze, compare).",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    run_p = sub.add_parser("run", help="Run a benchmark pipeline against one stack")
    add_run_arguments(run_p, platform)

    pre_p = sub.add_parser("precompute", help="Build analysis_data.json from raw session logs")
    precompute_mod.add_arguments(pre_p)

    ana_p = sub.add_parser("analyze", help="Per-run grading (LLM)")
    run_per_run_analysis.add_arguments(ana_p, platform)

    fin_p = sub.add_parser("final", help="LLM-graded cross-stack final analysis")
    run_final_analysis.add_arguments(fin_p, platform)

    agg_p = sub.add_parser("aggregate", help="Deterministic 2-stack rollup (no LLM)")
    aggregate_final_json.add_arguments(agg_p, platform)

    cmb_p = sub.add_parser("combine", help="Deterministic N-stack combined comparison (no LLM)")
    aggregate_combined_md.add_arguments(cmb_p, platform)

    sca_p = sub.add_parser("scaffold", help="Scaffold a new platform")
    scaffold_mod.add_arguments(sca_p)

    return parser


def main() -> None:
    # Resolve --platform (if any) before building the parser so subcommand
    # defaults (output_dir, prompts_file, etc.) can be drawn from the manifest.
    platform = preload_platform()
    parser = build_parser(platform)
    args = parser.parse_args()

    if args.command in ("run", "analyze", "final", "aggregate", "combine"):
        # User may have passed --platform on the subcommand; reload if it differs.
        if getattr(args, "platform", platform.name) != platform.name:
            from benchmarking.config import load_platform, load_platform_env
            load_platform_env(args.platform)
            platform = load_platform(args.platform)
        if args.command == "run":
            sys.exit(cmd_run(args, platform))
        if args.command == "analyze":
            sys.exit(run_per_run_analysis.run(args, platform))
        if args.command == "final":
            sys.exit(run_final_analysis.run(args, platform))
        if args.command == "aggregate":
            sys.exit(aggregate_final_json.run(args, platform))
        if args.command == "combine":
            sys.exit(aggregate_combined_md.run(args, platform))

    if args.command == "precompute":
        sys.exit(precompute_mod.run(args))
    if args.command == "scaffold":
        sys.exit(scaffold_mod.run(args))

    parser.error(f"unknown command: {args.command!r}")


if __name__ == "__main__":
    main()
