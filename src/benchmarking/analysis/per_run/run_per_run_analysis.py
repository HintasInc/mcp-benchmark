#!/usr/bin/env python3
"""
run_per_run_analysis.py — regenerate per-run analysis.json incrementally.

Each run dir is single-stack, so this module grades exactly one stack per dir.
Grading is **incremental**: the analyzer agent writes one JSON file per prompt
into ``<run_dir>/per_prompt_analysis/p<id>.json`` as it goes, so a rate-limit
or timeout halfway through a 50-prompt run does not lose the work already done.
On the next invocation any prompt whose per-prompt file already exists is
skipped, the agent only grades the remainder, and the orchestrator aggregates
all per-prompt files into ``analysis.json`` plus a rendered ``analysis.md``.

Use ``--prompt-ids 1,2,5`` to focus the agent on a subset of prompts (useful
for validating the analyzer cheaply before a full run). Aggregation is
unaffected — ``analysis.json`` always reflects every per-prompt file on disk.

Usage:
    uv run benchmark analyze --platform notion --all
    uv run benchmark analyze --platform slack \\
        --runs experiments/slack/runs/20260427_1719__slack experiments/slack/runs/20260428_1030__hintas
    uv run benchmark analyze --platform notion \\
        --runs experiments/notion/runs/<dir>/ --prompt-ids 1,2,4
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

from benchmarking.analysis import precompute as precompute_mod
from benchmarking.analysis.categories import resolve_categories
from benchmarking.analysis.per_run import render_md
from benchmarking.config import (
    Platform, Stack, available_platforms, preload_platform,
)
from benchmarking.paths import ANALYSIS_DIR, REPO_ROOT


PER_PROMPT_DIRNAME      = "per_prompt_analysis"
PENDING_DATA_FILENAME   = "analysis_data_pending.json"
DIFFICULTIES = ["L1", "L2", "L3", "L4", "L5"]


# Appended verbatim to every rendered prompt. Tells the agent to write one
# verdict file per prompt and never touch analysis.json itself — the
# orchestrator aggregates afterwards. The ``{{IDS_HINT}}`` line lists the
# pending IDs so the agent can validate it covered every one.
PER_PROMPT_OVERRIDE = """

---

## OVERRIDE — Incremental per-prompt mode (highest priority)

Earlier sections told you to read ``analysis_data.json`` and write a single
``analysis.json`` plus ``analysis.md``. **Override:**

- Read **only** ``{{RUN_DIR}}/{{PENDING_FILENAME}}``. It contains exactly the
  prompts that still need grading. Do NOT open ``analysis_data.json``.
- For **every** prompt in ``per_prompt`` (IDs: {{IDS_HINT}}):
  1. Grade the prompt using the verdict rules above.
  2. **Immediately** call the **Write** tool to create
     ``{{RUN_DIR}}/{{PER_PROMPT_DIR}}/p<id>.json`` with the JSON object below
     for that single prompt. Write per-prompt **before** moving to the next —
     do NOT batch writes at the end. This is what lets a rate-limit halfway
     through a run preserve the prompts already graded.
  3. Move on to the next prompt.
- Do NOT write ``analysis.json``, ``analysis.md``, or any aggregate file. The
  orchestrator aggregates the per-prompt files into ``analysis.json`` and
  renders markdown.

### Per-prompt file shape — write exactly this for each prompt

```json
{
  "id": "<id>",
  "title": "<title from analysis_data_pending.json>",
  "difficulty": "<difficulty>",
  "category": "<category>",
  "{{STACK}}": {
    "verdict": "{{VERDICT_ENUM}}",
    "reasoning": "1-2 sentence grounded explanation",
    "noteworthy_paths": ["...", "..."],
    "tool_calls":      {"complete": N, "failed": N, "partial": N},
    "tools_invoked":   [...],
    "initial_context": N,
    "peak_context":    N,
    "total_tokens":    N,
    "wall_clock_s":    N
  }
}
```

Copy ``tool_calls``, ``tools_invoked``, ``initial_context``, ``peak_context``,
``total_tokens`` and ``wall_clock_s`` **verbatim** from the prompt's entry in
``{{PENDING_FILENAME}}`` — they are precomputed and must not be re-derived.
Your only judgment is ``verdict``, ``reasoning`` and ``noteworthy_paths``.

After every per-prompt Write succeeds, print a ≤10-line summary to stdout
(verdict counts, total tokens, one headline finding) and stop.
"""


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
                   help="Explicit list of run directories. Mutually exclusive with --all.")
    p.add_argument("--all", action="store_true",
                   help="Re-grade every run directory under <output-dir>.")
    p.add_argument("--output-dir", type=Path, default=platform.output_dir,
                   help="Where run dirs live (default: experiments/<platform>/runs/). "
                        "Pass `runs` if your existing runs are in the top-level runs/.")
    p.add_argument("--prompts-file", default=str(platform.prompts_file),
                   help="Override the prompts file used by precompute.")
    p.add_argument("--timeout", type=int, default=1800,
                   help="Max seconds per run for the analysis agent (default 1800).")
    p.add_argument("--skip-precompute", action="store_true",
                   help="Don't auto-precompute analysis_data.json for run dirs missing it.")
    p.add_argument("--skip-claude", action="store_true",
                   help="Render each prompt and stop; print the rendered prompts to stdout.")
    p.add_argument("--continue-on-error", action="store_true",
                   help="If one run fails to grade, log and continue with the rest.")
    p.add_argument("--prompt-ids", default=None,
                   help="Comma-separated prompt IDs to grade (e.g. '1,2,5'). "
                        "Limits which prompts the agent grades this invocation; "
                        "analysis.json still aggregates every per-prompt file on disk.")
    p.add_argument("--regrade", action="store_true",
                   help="Delete existing per-prompt files for the targeted IDs "
                        "before running, forcing the agent to re-grade them.")
    p.add_argument("--verbose", action="store_true",
                   help="Include per-prompt detail tables in analysis.md "
                        "(default: summarized — aggregates and breakdowns only).")


def resolve_runs(args: argparse.Namespace) -> list[Path]:
    if args.all and args.runs:
        sys.exit("ERROR: pass either --all or --runs, not both")
    if args.all:
        out = args.output_dir if args.output_dir.is_absolute() else (REPO_ROOT / args.output_dir)
        if not out.is_dir():
            sys.exit(f"ERROR: no runs directory at {out}")
        runs = sorted(d for d in out.iterdir() if d.is_dir())
        if not runs:
            sys.exit(f"ERROR: no run subdirectories under {out}")
        return [r.resolve() for r in runs]
    if not args.runs:
        sys.exit("ERROR: pass --all or --runs <dir> [<dir> ...]")
    resolved = []
    for r in args.runs:
        path = r if r.is_absolute() else (REPO_ROOT / r)
        path = path.resolve()
        if not path.is_dir():
            sys.exit(f"ERROR: run directory does not exist: {path}")
        resolved.append(path)
    return resolved


def stack_for_run(platform: Platform, run_dir: Path) -> Stack:
    """Resolve which platform stack a run dir holds via its results.json."""
    results_path = run_dir / "results.json"
    if not results_path.exists():
        raise RuntimeError(f"results.json missing in {run_dir}; cannot resolve stack")
    raw = json.loads(results_path.read_text())
    stacks = raw.get("stacks") or []
    if len(stacks) != 1:
        raise RuntimeError(
            f"results.json in {run_dir} must declare exactly one stack; got {stacks!r}"
        )
    return platform.stack(stacks[0])


def ensure_analysis_data(run_dir: Path, stack: Stack, prompts_file: str) -> None:
    out = run_dir / "analysis_data.json"
    if out.exists():
        return
    print(f"  precomputing: {run_dir.name} → analysis_data.json")
    data = precompute_mod.precompute(run_dir, Path(prompts_file).resolve(), stack.name)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def all_ids(run_dir: Path) -> list[str]:
    src = run_dir / "analysis_data.json"
    if not src.exists():
        raise RuntimeError(f"missing analysis_data.json in {run_dir}")
    data = json.loads(src.read_text())
    pp = data.get("per_prompt") or {}
    return sorted(pp.keys(), key=lambda s: (len(s), s))


def completed_ids(run_dir: Path) -> set[str]:
    pp_dir = run_dir / PER_PROMPT_DIRNAME
    if not pp_dir.is_dir():
        return set()
    out = set()
    for f in pp_dir.glob("p*.json"):
        stem = f.stem
        if stem.startswith("p") and stem[1:].isdigit():
            out.add(stem[1:])
    return out


def write_pending_data(run_dir: Path, pending: list[str]) -> Path:
    """Write a filtered analysis_data file containing only the un-graded prompts."""
    src = run_dir / "analysis_data.json"
    data = json.loads(src.read_text())
    pp = data.get("per_prompt") or {}
    missing = [i for i in pending if i not in pp]
    if missing:
        available = sorted(pp.keys(), key=lambda s: (len(s), s))
        raise RuntimeError(
            f"prompt id(s) {missing!r} not found in {src}; available IDs: {available}"
        )
    data["per_prompt"] = {i: pp[i] for i in pending}
    out = run_dir / PENDING_DATA_FILENAME
    out.write_text(json.dumps(data, indent=2))
    return out


def render_prompt(template: str, platform: Platform, stack: Stack,
                  run_dir: Path, run_ts: str, prompts_file: str,
                  pending: list[str]) -> str:
    notes_path = ANALYSIS_DIR / "notes" / f"notes_{platform.name}.md"
    platform_notes = notes_path.read_text() if notes_path.exists() else ""
    body = (template
            .replace("{{RUN_DIR}}",                str(run_dir.resolve()))
            .replace("{{TIMESTAMP}}",              run_ts)
            .replace("{{PROMPTS_FILE}}",           str(Path(prompts_file).resolve()))
            .replace("{{PLATFORM_DISPLAY_NAME}}",  platform.display_name)
            .replace("{{STACK}}",                  stack.name)
            .replace("{{STACK_DISPLAY_NAME}}",     stack.display_name)
            .replace("{{PLATFORM_NOTES}}",         platform_notes))
    verdict_enum = "PASS|FAIL|ERROR" if platform.analysis.binary else "PASS|PARTIAL|FAIL|ERROR"
    override = (PER_PROMPT_OVERRIDE
                .replace("{{RUN_DIR}}",          str(run_dir.resolve()))
                .replace("{{PER_PROMPT_DIR}}",   PER_PROMPT_DIRNAME)
                .replace("{{PENDING_FILENAME}}", PENDING_DATA_FILENAME)
                .replace("{{STACK}}",            stack.name)
                .replace("{{VERDICT_ENUM}}",     verdict_enum)
                .replace("{{IDS_HINT}}",         ", ".join(pending)))
    return body + override


def spawn_claude(prompt: str, platform: Platform, timeout: int) -> int:
    env = {
        **os.environ,
        "CLAUDE_CONFIG_DIR": os.path.expanduser(platform.analysis.config_dir),
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS":
            os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "64000"),
    }
    cmd = [
        "claude",
        "--print",
        "--verbose",
        "--output-format", "stream-json",
        "--permission-mode", "bypassPermissions",
        "--model", platform.analysis.model,
        prompt,
    ]
    try:
        proc = subprocess.run(cmd, env=env, timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(f"ERROR: analyzer timed out after {timeout}s", file=sys.stderr)
        return 124
    except FileNotFoundError:
        sys.exit("ERROR: `claude` CLI not found on PATH")


MECHANICAL_FIELDS = (
    "tool_calls", "tools_invoked",
    "initial_context", "peak_context", "total_tokens", "wall_clock_s",
)


def aggregate_analysis_json(run_dir: Path, stack: Stack) -> Path:
    """Combine every per_prompt_analysis/p<id>.json into a single analysis.json.

    Pulls title/difficulty/category and the mechanical metrics (tool_calls,
    tools_invoked, initial_context, peak_context, total_tokens, wall_clock_s)
    from analysis_data.json. The LLM grader is instructed to copy these
    verbatim from the precompute, but its outputs aren't trustworthy enough
    to use directly — we always overwrite from analysis_data.json so the
    deterministic precompute wins.
    """
    src = run_dir / "analysis_data.json"
    src_data = json.loads(src.read_text()) if src.exists() else {"per_prompt": {}}
    src_pp = src_data.get("per_prompt") or {}

    pp_dir = run_dir / PER_PROMPT_DIRNAME
    per_prompt: dict[str, dict] = {}
    for f in sorted(pp_dir.glob("p*.json"),
                    key=lambda p: (len(p.stem), p.stem)):
        try:
            row = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            print(f"  ⚠ skipping malformed {f.name}: {e}", file=sys.stderr)
            continue
        pid = row.get("id") or f.stem.lstrip("p")
        meta = src_pp.get(pid, {})
        side = dict(row.get(stack.name, {}))
        precomputed = meta.get(stack.name, {}) or {}
        for field in MECHANICAL_FIELDS:
            if field in precomputed:
                side[field] = precomputed[field]
        per_prompt[pid] = {
            "title":      row.get("title")      or meta.get("title", ""),
            "difficulty": row.get("difficulty") or meta.get("difficulty", ""),
            "category":   row.get("category")   or meta.get("category", ""),
            stack.name:   side,
        }

    out = {
        "timestamp":     run_dir.name,
        "stacks":        [stack.name],
        "display_names": {stack.name: stack.display_name},
        "per_prompt":    per_prompt,
        "aggregates":    {stack.name: _aggregates(per_prompt, stack.name)},
        "breakdowns":    _breakdowns(per_prompt, stack.name),
    }
    path = run_dir / "analysis.json"
    path.write_text(json.dumps(out, indent=2))
    return path


def _aggregates(per_prompt: dict, stack: str) -> dict:
    rows = [r[stack] for r in per_prompt.values() if stack in r]
    n = len(rows)
    if n == 0:
        return {"n": 0, "pass": 0, "partial": 0, "fail": 0, "error": 0,
                "success_rate": 0.0}
    verdicts = Counter(r.get("verdict", "ERROR") for r in rows)
    tc_total = [r.get("tool_calls", {}).get("complete", 0)
                + r.get("tool_calls", {}).get("failed", 0)
                + r.get("tool_calls", {}).get("partial", 0)
                for r in rows]
    return {
        "n":                   n,
        "pass":                verdicts.get("PASS", 0),
        "partial":             verdicts.get("PARTIAL", 0),
        "fail":                verdicts.get("FAIL", 0),
        "error":               verdicts.get("ERROR", 0),
        "success_rate":        verdicts.get("PASS", 0) / n,
        "avg_initial_context": mean(r.get("initial_context", 0) for r in rows),
        "avg_peak_context":    mean(r.get("peak_context", 0)    for r in rows),
        "avg_wall_clock_s":    mean(r.get("wall_clock_s", 0)    for r in rows),
        "total_tokens":        sum(r.get("total_tokens", 0)     for r in rows),
        "avg_tool_calls":      mean(tc_total) if tc_total else 0,
        "total_tool_failures": sum(r.get("tool_calls", {}).get("failed", 0)
                                   for r in rows),
    }


def _breakdowns(per_prompt: dict, stack: str) -> dict:
    def by(key: str, buckets: list[str]) -> dict:
        out = {}
        for b in buckets:
            rows = [r[stack] for r in per_prompt.values()
                    if r.get(key) == b and stack in r]
            n = len(rows)
            if not n:
                continue
            verdicts = Counter(r.get("verdict", "ERROR") for r in rows)
            out[b] = {
                "n":            n,
                "success_rate": verdicts.get("PASS", 0) / n,
                "partial":      verdicts.get("PARTIAL", 0),
                "fail":         verdicts.get("FAIL", 0),
                "error":        verdicts.get("ERROR", 0),
            }
        return out
    categories = resolve_categories(r.get("category") for r in per_prompt.values())
    return {
        "by_difficulty": by("difficulty", DIFFICULTIES),
        "by_category":   by("category",   categories),
    }


def render_md_for(run_dir: Path, platform: Platform, verbose: bool = False) -> None:
    """Always (re)render analysis.md so it tracks the latest analysis.json."""
    md_path = run_dir / "analysis.md"
    if md_path.exists():
        md_path.unlink()
    mode = "verbose" if verbose else "summarized"
    print(f"  rendering analysis.md from analysis.json ({mode})")
    md = render_md.render(run_dir, verbose=verbose,
                          binary=platform.analysis.binary,
                          is_multi_api=(platform.name == "multi_api"))
    md_path.write_text(md)


def grade_one(run_dir: Path, platform: Platform, stack: Stack, template: str,
              prompts_file: str, timeout: int, skip_claude: bool,
              prompt_ids: list[str] | None, regrade: bool,
              verbose: bool = False) -> bool:
    run_ts = run_dir.name
    section(f"Grading {platform.name}/{run_ts} ({stack.name})")
    print(f"  run_dir: {run_dir}")

    pp_dir = run_dir / PER_PROMPT_DIRNAME
    pp_dir.mkdir(exist_ok=True)

    available = all_ids(run_dir)
    targeted  = prompt_ids if prompt_ids else available
    unknown   = [i for i in targeted if i not in available]
    if unknown:
        raise RuntimeError(
            f"prompt id(s) {unknown!r} not in analysis_data.json; "
            f"available IDs: {available}"
        )

    if regrade and not skip_claude:
        for pid in targeted:
            f = pp_dir / f"p{pid}.json"
            if f.exists():
                print(f"  --regrade: removing {f.name}")
                f.unlink()

    done = completed_ids(run_dir)
    pending = [i for i in targeted if i not in done]
    print(f"  prompts: {len(targeted)} targeted, {len(done & set(targeted))} already done, "
          f"{len(pending)} pending")

    if not pending:
        print("  nothing to grade — all targeted prompts already have per-prompt files")
        if skip_claude:
            return True
        json_path = aggregate_analysis_json(run_dir, stack)
        render_md_for(run_dir, platform, verbose=verbose)
        print(f"  ✓ {json_path}")
        return True

    if not skip_claude:
        write_pending_data(run_dir, pending)

    prompt = render_prompt(template, platform, stack, run_dir, run_ts,
                           prompts_file, pending=pending)
    print(f"  prompt size: {len(prompt):,} chars")

    if skip_claude:
        print(f"  pending IDs: {pending}")
        print("--- BEGIN RENDERED PROMPT ---")
        print(prompt)
        print("--- END RENDERED PROMPT ---")
        return True

    print(f"  Spawning analyzer (timeout={timeout}s, model={platform.analysis.model})")
    rc = spawn_claude(prompt, platform, timeout)

    after = completed_ids(run_dir)
    newly_done = after - done
    print(f"  agent rc={rc}; per-prompt files written this run: {len(newly_done)} "
          f"({sorted(newly_done, key=lambda s: (len(s), s))})")

    json_path = aggregate_analysis_json(run_dir, stack)
    render_md_for(run_dir, platform, verbose=verbose)

    still_pending = [i for i in targeted if i not in after]
    if still_pending:
        print(f"  ⚠ still pending after this run: {still_pending}")
        print("  re-run the same command to grade the rest "
              "(already-done prompts will be skipped)")
        print(f"  ✓ {json_path} (partial — {len(after)} of {len(available)} graded)")
        return False

    print(f"  ✓ {json_path}")
    return True


def run(args: argparse.Namespace, platform: Platform) -> int:
    template = platform.analysis.prompt_template.read_text()

    prompt_ids = None
    if args.prompt_ids:
        prompt_ids = [s.strip() for s in args.prompt_ids.split(",") if s.strip()]
        if not prompt_ids:
            sys.exit("ERROR: --prompt-ids was empty after parsing")

    section(f"Resolving run directories ({platform.name})")
    runs = resolve_runs(args)
    run_stacks: list[tuple[Path, Stack]] = []
    for r in runs:
        try:
            stack = stack_for_run(platform, r)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            if args.continue_on_error:
                continue
            sys.exit(6)
        run_stacks.append((r, stack))
        print(f"  • {r}  [{stack.name}]")

    if not args.skip_precompute and not args.skip_claude:
        section("Ensuring analysis_data.json for each run")
        for r, stack in run_stacks:
            try:
                ensure_analysis_data(r, stack, args.prompts_file)
            except RuntimeError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                if not args.continue_on_error:
                    sys.exit(7)

    failed: list[Path] = []
    for r, stack in run_stacks:
        try:
            ok = grade_one(r, platform, stack, template, args.prompts_file,
                           args.timeout, args.skip_claude,
                           prompt_ids=prompt_ids, regrade=args.regrade,
                           verbose=args.verbose)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            ok = False
        if not ok:
            failed.append(r)
            if not args.continue_on_error:
                sys.exit(8)

    section("Done")
    print(f"  graded: {len(run_stacks) - len(failed)}/{len(run_stacks)}")
    if failed:
        print("  runs with pending or errored prompts:")
        for r in failed:
            print(f"    • {r}")
        return 9
    return 0


def main() -> None:
    platform = preload_platform()
    p = argparse.ArgumentParser(description="Per-run analysis.json regenerator")
    add_arguments(p, platform)
    args = p.parse_args()
    sys.exit(run(args, platform))


if __name__ == "__main__":
    main()
