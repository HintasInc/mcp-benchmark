#!/usr/bin/env python3
from __future__ import annotations
"""
runner.py  —  Capability Benchmark Runner (Platform-agnostic, Single Stack)
================================================================
Runs the benchmark loop against ONE stack declared by a platform manifest
(platforms/<name>/<name>.toml). The stack is selected via --stack. Tokens are
read from platforms/<name>/.env / <repo>/.env, never from the command line.

For each eligible prompt:
  1. Reset the workspace
  2. Verify post-reset state
  3. Launch one Claude session against the chosen stack's CLAUDE_CONFIG_DIR
  4. Capture token usage, wall-clock time, tool calls, failures, success.
     Logs saved at <output_dir>/<run_subdir>/p<id>/.

Usage:
    uv run python -m benchmarking.runner --platform slack --stack hintas --difficulty L1 L2
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

from benchmarking.config import (
    Platform, Stack, RUN_TS_FORMAT, available_platforms,
    build_run_subdir, hintas_params_dict, preload_platform,
)
from benchmarking.prompts import load_prompts as _load_prompts_with_substitutions

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

# Thread-safe print lock
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print."""
    with _print_lock:
        print(*args, **kwargs)

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def parse_args() -> tuple[argparse.Namespace, Platform]:
    # First pass resolves --platform so the second pass can advertise
    # platform-specific defaults (prompts file, scripts) and per-stack token flags.
    platform = preload_platform()

    p = argparse.ArgumentParser(description="MCP Capability Benchmark Runner (Single Stack)")
    p.add_argument("--platform",          default="slack",
                   choices=available_platforms() or None,
                   help="Platform manifest under platforms/ (default: slack)")
    p.add_argument("--stack",             required=True,
                   choices=platform.stack_names,
                   help="Which stack from the platform manifest to benchmark")
    p.add_argument("--prompts-file",      default=str(platform.prompts_file))
    p.add_argument("--reset-script",      default=str(platform.reset_script))
    p.add_argument("--verify-script",     default=str(platform.verify_script))
    p.add_argument("--output-dir",        default=str(platform.output_dir),
                   help="Where run directories are written (default: platforms/<platform>/runs)")
    p.add_argument("--difficulty",        nargs="+",  help="e.g. L1 L2")
    p.add_argument("--prompt-ids",        nargs="+",  help="specific prompt IDs to run (e.g. 1 2 3 22)")
    p.add_argument("--category",          nargs="+",  help="e.g. retrieval write search")
    p.add_argument("--feasibility",       nargs="+",  default=["core"],
                   help="core | extension | both  (default: core only)")
    p.add_argument("--dry-run",           action="store_true",
                   help="Skip actual claude invocations; emit placeholder metrics")
    p.add_argument("--skip-reset",        action="store_true",
                   help="Skip the per-prompt workspace reset between sessions")
    p.add_argument("--verify",            action="store_true",
                   help="Run post-reset state verification (off by default)")
    p.add_argument("--verify-every-n",    type=int, default=1, metavar="N",
                   help="Run pre-prompt verify every Nth prompt instead of every prompt "
                        "(default 1 = every prompt). The first prompt is always verified. "
                        "Ignored unless --verify is set.")
    p.add_argument("--strict-verify",     action="store_true",
                   help="Skip any prompt where the workspace has hard drift after reset")
    p.add_argument("--timeout",           type=int, default=300,
                   help="Max seconds per claude invocation (default 300)")
    p.add_argument("--run-subdir",        default="",
                   help="Pre-computed run subdirectory under --output-dir. "
                        "If unset, uses build_run_subdir(args, platform, stack, now()).")

    # Variant-only label flags. Recorded in the run-dir name + results.json
    # when --stack matches platform.variant_stack so repeat runs against
    # different Hintas server configurations don't collide.
    hintas = p.add_argument_group("Hintas labels")
    hintas.add_argument("--search-top-k",         type=int, default=10)
    hintas.add_argument("--search-batch-enabled", action="store_true")
    hintas.add_argument("--search-max-results",   type=int, default=10)
    hintas.add_argument("--rag-enabled",          action="store_true")
    return p.parse_args(), platform


def token_for(stack: Stack) -> str:
    return os.environ.get(stack.token_env, "")


def require_token(stack: Stack) -> None:
    if token_for(stack):
        return
    print(f"ERROR: ${stack.token_env} is not set; load it via .env or the shell environment",
          file=sys.stderr)
    sys.exit(2)

# ─────────────────────────────────────────────────────────────
# Prompt loading & filtering
# ─────────────────────────────────────────────────────────────

def load_prompts(path: str) -> list[dict]:
    return _load_prompts_with_substitutions(path)

def filter_prompts(prompts: list[dict], args) -> list[dict]:
    feasibility_set = set(args.feasibility) if args.feasibility else {"core"}
    if "both" in feasibility_set:
        feasibility_set = {"core", "extension"}

    result = []
    for p in prompts:
        feas = p.get("feasible_on_free_plan", "infeasible")
        if feas not in feasibility_set:
            continue
        if args.difficulty and p.get("difficulty") not in args.difficulty:
            continue
        if args.category and p.get("category") not in args.category:
            continue
        if args.prompt_ids and str(p["id"]) not in args.prompt_ids:
            continue
        result.append(p)
    return result

# ─────────────────────────────────────────────────────────────
# Workspace reset
# ─────────────────────────────────────────────────────────────

def reset_workspace(reset_script: str, prompt_id, token: str, token_env: str,
                    dry_run: bool = False, stack_name: str | None = None) -> bool:
    """Run reset_workspace.py. Returns True on success."""
    if dry_run:
        safe_print(f"    [DRY] Would reset workspace for prompt {prompt_id}")
        return True
    cmd = [sys.executable, reset_script, "--prompt-id", str(prompt_id)]
    if stack_name:
        cmd.extend(["--stack", stack_name])
    env = {**os.environ, token_env: token}
    safe_print(f"    ↻ Resetting workspace (prompt {prompt_id})…")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        if result.returncode != 0:
            safe_print(f"    [WARN] Reset exited with code {result.returncode}")
            safe_print(result.stderr[-500:] if result.stderr else "")
            return False
        return True
    except subprocess.TimeoutExpired:
        safe_print("    [WARN] Reset timed out after 120s")
        return False
    except Exception as e:
        safe_print(f"    [WARN] Reset failed: {e}")
        return False


def verify_workspace(verify_script: str, stack: Stack, token: str, token_env: str,
                     report_path: Path, dry_run: bool = False) -> dict:
    """
    Run verify_workspace.py against a workspace.

    Returns {"ok": bool, "hard": int, "soft": int, "report_path": str, "error": str|None}.
    "ok" is True iff verify exited 0 (no hard drift). On structural failure (exit 2),
    "ok" is False and "error" carries the reason.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    display = stack.display_name

    if dry_run:
        safe_print(f"    [DRY] Would verify {display} workspace")
        return {"ok": True, "hard": 0, "soft": 0, "report_path": str(report_path), "error": None}

    cmd = [sys.executable, verify_script, "--soft", "--report", str(report_path),
           "--stack", stack.name]
    env = {**os.environ, token_env: token}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "hard": 0, "soft": 0, "report_path": str(report_path),
                "error": "verify timed out after 180s"}
    except Exception as e:
        return {"ok": False, "hard": 0, "soft": 0, "report_path": str(report_path),
                "error": f"verify failed: {e}"}

    if result.returncode == 2:
        return {"ok": False, "hard": 0, "soft": 0, "report_path": str(report_path),
                "error": f"verify exited 2 (structural): {result.stderr[-300:] or result.stdout[-300:]}"}

    hard = soft = 0
    if report_path.exists():
        try:
            with open(report_path) as f:
                data = json.load(f)
            hard = data.get("hard_count", 0)
            soft = data.get("soft_count", 0)
        except Exception as e:
            return {"ok": False, "hard": 0, "soft": 0, "report_path": str(report_path),
                    "error": f"could not parse report: {e}"}

    return {"ok": hard == 0, "hard": hard, "soft": soft,
            "report_path": str(report_path), "error": None}

# ─────────────────────────────────────────────────────────────
# Token trace parsing
# ─────────────────────────────────────────────────────────────

def parse_token_trace(content: str) -> list[dict]:
    """
    Parse stream-json JSONL output and build a chronological token trace.

    Returns a list of token snapshots:
      [
        {"event": "session_start", "input_tokens": N, "output_tokens": N, "cumulative_input": N, "cumulative_output": N},
        {"event": "tool_call",     "tool_name": "...", "input_tokens": N, "output_tokens": N, "cumulative_input": N, "cumulative_output": N},
        ...
        {"event": "result",        "input_tokens": N, "output_tokens": N, "cumulative_input": N, "cumulative_output": N},
      ]
    """
    trace = []
    cumulative_input = 0
    cumulative_output = 0
    first_assistant_seen = False
    pending_tool_names = []

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = obj.get("type", "")

        # ── First assistant turn: this is the session start / initial context load
        if event_type == "assistant":
            msg = obj.get("message", {})
            usage = msg.get("usage", {})
            turn_input = usage.get("input_tokens", 0)
            turn_output = usage.get("output_tokens", 0)
            cumulative_input += turn_input
            cumulative_output += turn_output

            if not first_assistant_seen:
                first_assistant_seen = True
                trace.append({
                    "event": "session_start",
                    "description": "Initial context load — tokens used before any tool calls",
                    "turn_input_tokens": turn_input,
                    "turn_output_tokens": turn_output,
                    "cumulative_input": cumulative_input,
                    "cumulative_output": cumulative_output,
                })
            else:
                # Subsequent assistant turns after tool results → "after tool call"
                tool_desc = ", ".join(pending_tool_names) if pending_tool_names else "unknown"
                trace.append({
                    "event": "after_tool_call",
                    "description": f"After tool call(s): {tool_desc}",
                    "tools_used": list(pending_tool_names),
                    "turn_input_tokens": turn_input,
                    "turn_output_tokens": turn_output,
                    "cumulative_input": cumulative_input,
                    "cumulative_output": cumulative_output,
                })
                pending_tool_names = []

            # Collect tool names from content blocks in this assistant turn
            for block in msg.get("content", []):
                if block.get("type") == "tool_use":
                    pending_tool_names.append(block.get("name", "unknown_tool"))
            continue

        # ── Tool result
        if event_type == "tool_result":
            continue

        # ── Final result
        if event_type == "result":
            usage = obj.get("usage", {})
            if usage.get("input_tokens") is not None:
                final_input = usage.get("input_tokens", cumulative_input)
                final_output = usage.get("output_tokens", cumulative_output)
            else:
                final_input = cumulative_input
                final_output = cumulative_output

            trace.append({
                "event": "result",
                "description": "Final session result — authoritative token totals",
                "cumulative_input": final_input,
                "cumulative_output": final_output,
                "total_tokens": final_input + final_output,
            })
            continue

    return trace

# ─────────────────────────────────────────────────────────────
# Claude invocation (per-session, using alias)
# ─────────────────────────────────────────────────────────────

def build_claude_command(prompt_text: str, stack: Stack) -> list[str]:
    """Build the claude CLI invocation. Config dir routing is handled via env.

    The session is locked to the stack's MCP server: built-in tools are disabled
    (`--tools ""`) and the allowlist admits only `mcp__<server>__*`, so the agent
    cannot shell out, read/write files, or fetch the web to work around a missing
    MCP capability — it must succeed or fail using the MCP under test.
    """
    mcp_allowlist = f"mcp__{stack.mcp_server}__*"
    return [
        "claude",
        "--print",
        "--verbose",
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
        "--model", "sonnet",
        "--effort", "high",
        "--tools", "",
        "--allowedTools", mcp_allowlist,
        "--",
        prompt_text,
    ]

def run_session(prompt: dict, stack: Stack, platform: Platform,
                session_dir: Path, timeout: int, dry_run: bool,
                token: str) -> dict:
    """
    Run a single Claude session for one stack.
    Saves logs and token trace to session_dir.
    Returns a metrics dict.
    """
    display = stack.display_name
    prompt_text = prompt["prompt"]
    pid = prompt["id"]
    start = time.monotonic()

    safe_print(f"    [{display}] ► Starting session…")

    if dry_run:
        time.sleep(0.1)
        # Save placeholder trace
        trace = [{"event": "session_start", "description": "dry run", "turn_input_tokens": 0,
                  "turn_output_tokens": 0, "cumulative_input": 0, "cumulative_output": 0}]
        session_dir.mkdir(parents=True, exist_ok=True)
        with open(session_dir / "token_trace.json", "w") as f:
            json.dump(trace, f, indent=2)
        with open(session_dir / "session.log", "w") as f:
            f.write("[DRY RUN — no output]\n")
        return {
            "stack":           stack.name,
            "prompt_id":       pid,
            "success":         None,
            "wall_clock_s":    0.1,
            "input_tokens":    0,
            "output_tokens":   0,
            "tool_calls":      0,
            "tool_failures":   0,
            "clarifying_qs":   0,
            "raw_output":      "[DRY RUN — no output]",
            "error":           None,
            "token_trace":     trace,
        }

    cmd = build_claude_command(prompt_text, stack)

    config_dir_path = os.path.expanduser(stack.config_dir)
    env = {**os.environ,
           platform.downstream_token_env: token,
           "CLAUDE_CONFIG_DIR": config_dir_path}

    session_dir.mkdir(parents=True, exist_ok=True)

    raw_output = ""
    error_msg  = None
    returncode = None

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        raw_output = proc.stdout + "\n" + proc.stderr
        returncode = proc.returncode
        if proc.returncode != 0:
            error_msg = f"exit code {proc.returncode}"
    except subprocess.TimeoutExpired:
        raw_output = ""
        error_msg  = f"timed out after {timeout}s"
    except FileNotFoundError:
        error_msg  = "claude CLI not found — install it with 'npm i -g @anthropic-ai/claude-code' or ensure it's in your PATH"
        raw_output = ""

    wall_clock = time.monotonic() - start

    # Write raw session log
    with open(session_dir / "session.log", "w", encoding="utf-8") as f:
        f.write(f"# Prompt {pid} — {stack.name}\n")
        f.write(f"# Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"# Config Dir: {stack.config_dir}\n")
        f.write(f"# Wall-clock: {wall_clock:.2f}s\n\n")
        f.write(raw_output)

    # Parse token trace
    token_trace = parse_token_trace(raw_output)

    # Save token trace as JSON
    with open(session_dir / "token_trace.json", "w", encoding="utf-8") as f:
        json.dump(token_trace, f, indent=2)

    # Parse standard metrics
    metrics = parse_log(raw_output)

    # Extract plain-text result from stream-json for grading heuristic.
    grading_text = raw_output
    for line in raw_output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            if obj.get("type") == "result" and "result" in obj:
                grading_text = obj["result"]
                break
        except json.JSONDecodeError:
            continue

    initial_tokens = 0
    if token_trace and token_trace[0].get("event") == "session_start":
        initial_tokens = token_trace[0].get("turn_input_tokens", 0)

    metrics.update({
        "stack":         stack.name,
        "prompt_id":     pid,
        "success":       None,
        "wall_clock_s":  round(wall_clock, 2),
        "initialization_tokens": initial_tokens,
        "raw_output":    grading_text,
        "full_log":      raw_output,
        "error":         error_msg,
        "token_trace":   token_trace,
    })

    # Print session token summary
    _print_session_token_info(display, pid, token_trace, metrics)

    return metrics

def _print_session_token_info(display: str, pid, token_trace: list[dict], metrics: dict):
    """Print individual session token usage info (thread-safe)."""
    safe_print(f"\n    ┌─ {display} — Prompt {pid} — Token Trace ─────────────────")

    if not token_trace:
        safe_print("    │  (no token trace data captured)")
        safe_print(f"    └{'─' * 55}")
        return

    for i, snap in enumerate(token_trace):
        event = snap.get("event", "?")
        if event == "session_start":
            safe_print("    │  📋 SESSION START (initial context load)")
            safe_print(f"    │     Input tokens:  {snap.get('turn_input_tokens', 0):,}")
            safe_print(f"    │     Output tokens: {snap.get('turn_output_tokens', 0):,}")
            safe_print("    │     ─ This is the context size before any tool calls")
        elif event == "after_tool_call":
            tools = snap.get("tools_used", [])
            safe_print(f"    │  🔧 AFTER TOOL CALL: {', '.join(tools)}")
            safe_print(f"    │     Turn input:    {snap.get('turn_input_tokens', 0):,}")
            safe_print(f"    │     Turn output:   {snap.get('turn_output_tokens', 0):,}")
            safe_print(f"    │     Cumulative in:  {snap.get('cumulative_input', 0):,}")
            safe_print(f"    │     Cumulative out: {snap.get('cumulative_output', 0):,}")
        elif event == "result":
            safe_print("    │  ✅ SESSION RESULT")
            safe_print(f"    │     Total input:  {snap.get('cumulative_input', 0):,}")
            safe_print(f"    │     Total output: {snap.get('cumulative_output', 0):,}")
            safe_print(f"    │     Total tokens: {snap.get('total_tokens', 0):,}")

    safe_print(f"    └{'─' * 55}")

# ─────────────────────────────────────────────────────────────
# Log parsing (reused from v4)
# ─────────────────────────────────────────────────────────────

def parse_log(content: str) -> dict:
    """
    Parse stream-json JSONL output from `claude --output-format stream-json`.

    Each line is a JSON object. Relevant event types:
      - type=assistant  → message.content[] may have tool_use items;
                          message.usage has per-turn token counts
      - type=tool_result → is_error=true signals a tool failure
      - type=result      → usage has final cumulative token totals
    """
    input_tokens  = 0
    output_tokens = 0
    tool_calls    = 0
    tool_failures = 0
    clarifying_qs = 0
    result_subtype  = ""     # "success" | "error" from the final result event
    result_is_error = False  # is_error field from the final result event

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = obj.get("type", "")

        # ── Final result: use cumulative usage if present ─────────────────
        if event_type == "result":
            usage = obj.get("usage", {})
            if usage.get("input_tokens") is not None:
                # Replace running totals with the authoritative final count
                input_tokens  = usage.get("input_tokens",  input_tokens)
                output_tokens = usage.get("output_tokens", output_tokens)
            # Primary grading signals
            result_subtype   = obj.get("subtype", "")        # "success" | "error"
            result_is_error  = obj.get("is_error", False)
            continue

        # ── Assistant turn ────────────────────────────────────────────────
        if event_type == "assistant":
            msg = obj.get("message", {})
            usage = msg.get("usage", {})
            input_tokens  += usage.get("input_tokens",  0)
            output_tokens += usage.get("output_tokens", 0)
            for block in msg.get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls += 1
            continue

        # ── Tool result (failure check) ───────────────────────────────────
        if event_type == "tool_result":
            if obj.get("is_error", False):
                tool_failures += 1
            continue

        # ── Heuristic: clarifying questions in plain text lines ───────────
        if event_type == "text" or event_type == "content_block_delta":
            text = obj.get("text", obj.get("delta", {}).get("text", ""))
            qs = len(re.findall(r'(?m)^.*\?\s*$', text))
            clarifying_qs += qs

    return {
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "tool_calls":    tool_calls,
        "tool_failures": tool_failures,
        "clarifying_qs": clarifying_qs,
        "result_subtype":  result_subtype,
        "result_is_error": result_is_error,
    }

# ─────────────────────────────────────────────────────────────
# Grading  (heuristic — no live Slack verification)
# ─────────────────────────────────────────────────────────────

def grade_output(prompt: dict, raw_output: str,
                 metrics: dict | None = None) -> tuple[bool, list[str]]:
    """
    Grade success from the stream-json result event:
      - result_is_error=True / result_subtype='error' → FAIL
      - result_subtype='success' + no tool failures + no hard-error keywords → PASS
      - result_subtype='success' + tool failures > 0  → FAIL
      - anything else → None (ungraded; downstream analysis decides)
    """
    output_lower = raw_output.lower() if raw_output else ""
    error_indicators = ["error", "failed", "exception", "timed out"]

    if not metrics:
        return (None, ["no metrics available"])

    r_subtype  = metrics.get("result_subtype", "")
    r_is_error = metrics.get("result_is_error", False)
    t_failures = metrics.get("tool_failures", 0)

    if r_is_error or r_subtype == "error":
        return (False, ["✗ result event reported is_error=true / subtype=error"])

    if r_subtype == "success" and t_failures == 0:
        if any(e in output_lower for e in error_indicators):
            return (False, ["✗ result subtype=success but error text detected in output"])
        return (True, ["✓ result subtype=success, 0 tool failures, no error text"])

    if r_subtype == "success" and t_failures > 0:
        return (False, [f"✗ result subtype=success but {t_failures} tool failure(s)"])

    return (None, ["no structured result event in stream"])

# ─────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────

COLORS = {
    "reset": "\033[0m",
    "bold":  "\033[1m",
    "green": "\033[92m",
    "red":   "\033[91m",
    "yellow":"\033[93m",
    "cyan":  "\033[96m",
    "blue":  "\033[94m",
    "dim":   "\033[2m",
}

def c(color: str, text: str) -> str:
    return f"{COLORS.get(color,'')}{text}{COLORS['reset']}"

def fmt_bool(val) -> str:
    if val is True:  return c("green", "✓ PASS")
    if val is False: return c("red",   "✗ FAIL")
    return c("yellow", "? N/A")

def print_header(title: str):
    w = 80
    print()
    print(c("bold", "═" * w))
    print(c("bold", f"  {title}"))
    print(c("bold", "═" * w))

def print_section(title: str):
    print()
    print(c("cyan", f"  ── {title} " + "─" * max(0, 74 - len(title))))

def print_per_prompt_table(prompts: list[dict], results: dict, stack: Stack):
    """Per-prompt single-stack results table."""
    print_header("PER-PROMPT RESULTS")

    hdr = (
        f"  {'ID':<5} {'Title':<35} {'Diff':<4} "
        f"{'Pass':<6} {'Time':<8} {'Tokens':<10} {'Tools':<6} {'Fails':<6}"
    )
    print(c("bold", hdr))
    print(c("dim", "  " + "─" * 78))

    for p in prompts:
        pid    = str(p["id"])
        title  = p["title"][:34]
        diff   = p.get("difficulty", "?")
        r      = results.get(f"p{pid}_{stack.name}")

        ok    = fmt_bool(r["success"]) if r else c("dim", "—")
        t     = f"{r['wall_clock_s']:.1f}s" if r else "—"
        tok   = str(r["input_tokens"] + r["output_tokens"]) if r else "—"
        tools = str(r["tool_calls"]) if r else "—"
        fails = str(r["tool_failures"]) if r else "—"

        err_flag = c("yellow", " [!]") if (r and r.get("error")) else ""

        print(
            f"  {pid:<5} {title:<35} {diff:<4} "
            f"{ok:<6} {t:<8} {tok:<10} {tools:<6} {fails:<6}{err_flag}"
        )

def print_aggregate(prompts: list[dict], results: dict, stack: Stack):
    """Single-stack aggregate summary."""
    print_header(f"AGGREGATE SUMMARY: {stack.display_name}")

    rows = [results[f"p{p['id']}_{stack.name}"]
            for p in prompts if f"p{p['id']}_{stack.name}" in results]
    if not rows:
        print("  No results collected.")
        return

    n      = len(rows)
    passes = sum(1 for r in rows if r["success"] is True)
    fails  = sum(1 for r in rows if r["success"] is False)
    skips  = n - passes - fails
    errors = sum(1 for r in rows if r.get("error"))

    metric_rows = [r for r in rows if r["success"] is not None]
    m_n = len(metric_rows)

    ctx_tokens = []
    for r in metric_rows:
        for snap in r.get("token_trace", []):
            if snap.get("event") == "session_start":
                ctx_tokens.append(snap.get("turn_input_tokens", 0))
                break

    avg_time     = sum(r["wall_clock_s"] for r in metric_rows) / m_n if m_n else 0
    total_input  = sum(r["input_tokens"]  for r in metric_rows)
    total_output = sum(r["output_tokens"] for r in metric_rows)
    avg_tools    = sum(r["tool_calls"]    for r in metric_rows) / m_n if m_n else 0
    total_fails  = sum(r["tool_failures"] for r in metric_rows)
    avg_clarify  = sum(r["clarifying_qs"] for r in metric_rows) / m_n if m_n else 0
    avg_context  = sum(ctx_tokens) / len(ctx_tokens) if ctx_tokens else 0

    W = 26
    print(c("bold", f"  {'Metric':<{W}} │ Value"))
    print(c("dim", "  " + "─" * 50))
    print(f"  {'Prompts run':<{W}} │ {n}")
    print(f"  {'Pass rate':<{W}} │ {passes/n:.1%}" if n else f"  {'Pass rate':<{W}} │ —")
    print(f"  {'Passes':<{W}} │ {passes}")
    print(f"  {'Fails':<{W}} │ {fails}")
    print(f"  {'Skipped':<{W}} │ {skips}")
    print(f"  {'Invocation errors':<{W}} │ {errors}")
    print(c("dim", "  " + "─" * 50))
    print(f"  {'Avg context tokens':<{W}} │ {avg_context:,.0f}")
    print(f"  {'Avg wall-clock (s)':<{W}} │ {avg_time:.2f}s")
    print(f"  {'Total input tokens':<{W}} │ {total_input:,}")
    print(f"  {'Total output tokens':<{W}} │ {total_output:,}")
    print(f"  {'Avg tool calls':<{W}} │ {avg_tools:.2f}")
    print(f"  {'Total tool failures':<{W}} │ {total_fails}")
    print(f"  {'Avg clarif. Qs':<{W}} │ {avg_clarify:.2f}")

def print_by_difficulty(prompts: list[dict], results: dict, stack: Stack):
    """Single-stack breakdown by difficulty level."""
    print_section("BREAKDOWN BY DIFFICULTY")
    levels = ["L1", "L2", "L3", "L4", "L5"]
    hdr = f"  {'Diff':<6} {'N':<4} {'Pass%':<10} {'Tok avg':<12} {'Time avg':<10}"
    print(c("bold", hdr))
    print(c("dim", "  " + "─" * 50))

    for level in levels:
        ps = [p for p in prompts if p.get("difficulty") == level]
        if not ps:
            continue

        rows = [results[f"p{p['id']}_{stack.name}"]
                for p in ps if f"p{p['id']}_{stack.name}" in results]
        if not rows:
            continue

        passes     = sum(1 for r in rows if r["success"] is True)
        valid_rows = [r for r in rows if r["success"] is not None]
        m_n        = len(valid_rows)
        avg_tok    = sum(r["input_tokens"] + r["output_tokens"] for r in valid_rows) / m_n if m_n else 0
        avg_time   = sum(r["wall_clock_s"] for r in valid_rows) / m_n if m_n else 0

        print(f"  {level:<6} {len(ps):<4} "
              f"{passes/len(rows):.0%}      "
              f"{avg_tok:<12,.0f} "
              f"{avg_time:<10.1f}")

def print_by_category(prompts: list[dict], results: dict, stack: Stack):
    """Single-stack breakdown by prompt category."""
    print_section("BREAKDOWN BY CATEGORY")
    cats = sorted(set(p.get("category", "?") for p in prompts))
    hdr  = f"  {'Category':<16} {'N':<4} {'Pass%':<10}"
    print(c("bold", hdr))
    print(c("dim", "  " + "─" * 36))

    for cat in cats:
        ps   = [p for p in prompts if p.get("category") == cat]
        rows = [results[f"p{p['id']}_{stack.name}"]
                for p in ps if f"p{p['id']}_{stack.name}" in results]
        if not rows:
            continue
        passes = sum(1 for r in rows if r["success"] is True)
        print(f"  {cat:<16} {len(ps):<4} {passes/len(rows):.0%}")

def save_json_results(prompts: list[dict], results: dict, results_path: Path,
                      platform: Platform, stack: Stack, args):
    """Save full results as JSON for downstream analysis."""
    out = {
        "run_at":       datetime.now(timezone.utc).isoformat(),
        "platform":     platform.name,
        "stacks":       [stack.name],
        "config_dirs":  {stack.name: stack.config_dir},
        "prompts":      [{"id": p["id"], "title": p["title"],
                          "difficulty": p["difficulty"],
                          "category": p.get("category")} for p in prompts],
        "results":      {k: {kk: vv for kk, vv in v.items()
                             if kk not in ("raw_output", "full_log")}
                         for k, v in results.items()},
    }
    if stack.name == platform.variant_stack.name:
        out["hintas_params"] = hintas_params_dict(args)

    with open(results_path, "w") as f:
        json.dump(out, f, indent=2)
    print(c("dim", f"\n  Results saved → {results_path}"))

# ─────────────────────────────────────────────────────────────
# Main loop (one stack, sequential prompts)
# ─────────────────────────────────────────────────────────────

def run(args, platform, stack: Stack):
    require_token(stack)
    token = token_for(stack)

    # Set up output directory: <output-dir>/<run_subdir>/p<id>/
    user_run_subdir = getattr(args, "run_subdir", "")
    run_subdir = user_run_subdir or \
                 build_run_subdir(args, platform, stack, datetime.now().strftime(RUN_TS_FORMAT))
    run_dir = Path(args.output_dir) / run_subdir
    if run_dir.exists():
        if user_run_subdir:
            print(f"ERROR: run directory already exists: {run_dir}", file=sys.stderr)
            print( "       pass a different --run-subdir", file=sys.stderr)
            sys.exit(5)
        # Auto-generated subdir collided (same-second re-invocation). Disambiguate.
        base_subdir = run_subdir
        for n in range(1, 1000):
            run_subdir = f"{base_subdir}_{n}"
            run_dir    = Path(args.output_dir) / run_subdir
            if not run_dir.exists():
                break
        else:
            print(f"ERROR: could not allocate unique run directory under: {run_dir.parent}",
                  file=sys.stderr)
            sys.exit(5)
    run_dir.mkdir(parents=True)

    # Load + filter prompts
    all_prompts = load_prompts(args.prompts_file)
    prompts     = filter_prompts(all_prompts, args)

    if not prompts:
        print("No prompts match the given filters.")
        sys.exit(0)

    print_header(f"{platform.display_name} Benchmark — {len(prompts)} prompt(s) × {stack.display_name}")
    print(f"  Platform:      {platform.name}")
    print(f"  Stack:         {stack.name} ({stack.display_name})")
    print(f"  Config dir:    {stack.config_dir}")
    print(f"  Output dir:    {run_dir}")
    if args.dry_run:
        print(c("yellow", "  ⚠ DRY RUN — no real claude invocations"))
    if args.skip_reset:
        print(c("yellow", "  ⚠ Skips reset: True (Workspace will not be reset)"))
    if not args.verify:
        print(c("yellow", "  ⚠ Verify off (post-reset state will not be checked); pass --verify to enable"))
    else:
        if args.verify_every_n > 1:
            print(c("yellow", f"  ⚠ Verify every {args.verify_every_n} prompts (sampled)"))
        if args.strict_verify:
            print(c("yellow", "  ⚠ Strict verify: prompts with hard drift will be skipped"))

    results: dict = {}
    total     = len(prompts)
    token_env = platform.downstream_token_env

    for idx, p in enumerate(prompts, 1):
        pid   = p["id"]
        title = p["title"]

        print()
        print(c("bold", f"  [{idx}/{total}] Prompt {pid}: {title}  [{p.get('difficulty','?')} / {p.get('category','?')}]"))

        if not args.skip_reset:
            reset_workspace(args.reset_script, pid, token, token_env,
                            args.dry_run, stack.name)

        prompt_dir = run_dir / f"p{pid}"

        skip_session = False
        verify_due = (
            args.verify
            and (args.verify_every_n <= 1 or (idx - 1) % args.verify_every_n == 0)
        )
        if verify_due:
            verify_report = prompt_dir / "verify_report.json"
            v = verify_workspace(args.verify_script, stack, token, token_env,
                                 verify_report, args.dry_run)
            if v["error"]:
                safe_print(c("yellow", f"    ! [{stack.display_name}] verify: {v['error']}"))
            elif v["hard"] or v["soft"]:
                color = "red" if v["hard"] else "yellow"
                safe_print(c(color, f"    ! [{stack.display_name}] drift: {v['hard']} hard, {v['soft']} soft "
                                    f"→ {v['report_path']}"))
            else:
                safe_print(c("green", f"    ✓ [{stack.display_name}] workspace verified clean"))

            if args.strict_verify and not v["ok"]:
                safe_print(c("yellow", f"    ⚠ Skipping prompt {pid} due to --strict-verify"))
                skip_session = True

        if skip_session:
            results[f"p{pid}_{stack.name}"] = {
                "stack":          stack.name,
                "prompt_id":      pid,
                "success":        None,
                "wall_clock_s":   0.0,
                "input_tokens":   0,
                "output_tokens":  0,
                "tool_calls":     0,
                "tool_failures":  0,
                "clarifying_qs":  0,
                "raw_output":     "",
                "error":          "skipped: pre-prompt verify reported hard drift",
                "token_trace":    [],
            }
            continue

        metrics = run_session(p, stack, platform, prompt_dir,
                              args.timeout, args.dry_run, token)

        if metrics.get("error"):
            safe_print(c("yellow", f"    ! [{stack.display_name}] {metrics['error']}"))

        success, _ = grade_output(p, metrics.get("raw_output", ""), metrics=metrics)
        metrics["success"] = success
        results[f"p{pid}_{stack.name}"] = metrics

        print()
        print(c("blue", f"    ── Prompt {pid} Summary ──"))
        print(f"    {c('blue', stack.display_name)}  {fmt_bool(success)}  "
              f"time={metrics['wall_clock_s']:.1f}s  "
              f"tokens={metrics['input_tokens']+metrics['output_tokens']:,}  "
              f"tools={metrics['tool_calls']}  "
              f"failures={metrics['tool_failures']}")

    # ── Final report ──────────────────────────────────────────────────────
    print_per_prompt_table(prompts, results, stack)
    print_aggregate(prompts, results, stack)
    print_by_difficulty(prompts, results, stack)
    print_by_category(prompts, results, stack)
    results_path = run_dir / "results.json"
    save_json_results(prompts, results, results_path, platform, stack, args)

    print()
    print(c("bold", "  Done. Session logs saved in:"))
    print(f"    {run_dir}/")
    print(c("dim", "  Each prompt folder contains: session.log + token_trace.json"))
    print(c("dim", f"  Detailed results JSON: {results_path}"))
    print()


def main():
    args, platform = parse_args()
    run(args, platform, platform.stack(args.stack))


if __name__ == "__main__":
    main()
