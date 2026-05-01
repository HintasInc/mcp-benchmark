#!/usr/bin/env python3
"""
precompute.py — deterministic pre-analysis for a benchmark run.

Reads every session.log + token_trace.json under a single-stack run directory,
classifies tool calls (complete / failed / partial), extracts token + timing
totals, builds a cleaned bounded transcript of what the agent did and what
each MCP tool returned, and emits a JSON summary that downstream graders can
consume without re-reading the raw logs.

Each run dir holds exactly one stack's data and contains prompt subdirs
directly (`<run_dir>/p<id>/session.log`). The active stack is read from
`<run_dir>/results.json` unless explicitly overridden via --stack.

The transcript lets the LLM grader judge from observed behaviour — the actual
working path of the agent — rather than from metadata heuristics.

Usage:
    uv run benchmark precompute \
        --run-dir    platforms/slack/runs/20260423_2107__slack \
        --prompts    platforms/slack/prompts/benchmark_prompts.json \
        --out        platforms/slack/runs/20260423_2107__slack/analysis_data.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from benchmarking.prompts import load_prompts as _load_prompts_with_substitutions


MCP_PREFIX_RE = re.compile(r"^mcp__[^_]+(?:-[^_]+)*__")
BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{500,}")

SLACK_API_METHODS = {
    "conversations_list",        "conversations_info",
    "conversations_history",     "conversations_members",
    "conversations_replies",     "conversations_join",
    "conversations_leave",       "conversations_open",
    "conversations_create",      "conversations_archive",
    "conversations_rename",      "conversations_setPurpose",
    "conversations_setTopic",    "conversations_invite",
    "conversations_kick",        "conversations_mark",
    "chat_postMessage",          "chat_update",
    "chat_delete",               "chat_postEphemeral",
    "chat_scheduleMessage",      "chat_deleteScheduledMessage",
    "chat_getPermalink",         "chat_meMessage",
    "users_list",                "users_info",
    "users_lookupByEmail",       "users_profile_get",
    "users_profile_set",         "users_conversations",
    "reactions_add",             "reactions_remove",
    "reactions_get",             "reactions_list",
    "files_upload",              "files_list",
    "files_info",                "files_delete",
    "pins_add",                  "pins_remove",   "pins_list",
    "bookmarks_add",             "bookmarks_edit","bookmarks_list","bookmarks_remove",
    "team_info",                 "team_profile_get",
    "usergroups_list",           "usergroups_users_list",
    "search_messages",           "search_files",
    "dnd_info",                  "dnd_setSnooze","dnd_endSnooze",
    "remind_add",                "remind_list",  "remind_delete",
    "views_open",                "views_update", "views_publish",
}


# ─────────────────────────────────────────────────────────────
# Truncation helpers
# ─────────────────────────────────────────────────────────────

def _redact_base64(s: str) -> str:
    return BASE64_RE.sub(lambda m: f"[base64 blob, {len(m.group(0))} chars elided]", s)


def smart_truncate(s: str, head: int, tail: int) -> tuple[str, bool, int]:
    """Return (possibly-truncated, was_truncated, original_length).

    For long strings, returns head + marker + tail. Base64-like blobs are
    redacted before measurement.
    """
    if not isinstance(s, str):
        s = str(s)
    s = _redact_base64(s)
    n = len(s)
    if n <= head + tail + 32:
        return s, False, n
    elided = n - head - tail
    return f"{s[:head]}\n...[truncated {elided} chars]...\n{s[-tail:]}", True, n


def truncate_json_payload(obj, max_chars: int = 1000):
    """Recursively shrink strings/lists inside a structured payload.

    Strings longer than max_chars are head+tail truncated. Long lists keep
    head+tail items with a marker entry. If the serialized form still exceeds
    max_chars, fall back to stringify+truncate (losing structure but bounded).
    """
    truncated = [False]

    def _walk(o, budget):
        if isinstance(o, str):
            new, was_t, _ = smart_truncate(o, head=int(budget * 0.7), tail=int(budget * 0.2))
            if was_t:
                truncated[0] = True
            return new
        if isinstance(o, list):
            if len(o) > 8:
                truncated[0] = True
                head = [_walk(x, budget) for x in o[:5]]
                tail = [_walk(x, budget) for x in o[-2:]]
                return head + [f"...[{len(o) - 7} items elided]..."] + tail
            return [_walk(x, budget) for x in o]
        if isinstance(o, dict):
            return {k: _walk(v, budget) for k, v in o.items()}
        return o

    shrunk = _walk(obj, max_chars)
    serialized = json.dumps(shrunk, ensure_ascii=False)
    if len(serialized) > max_chars * 1.5:
        flat, was_t, _ = smart_truncate(serialized, head=int(max_chars * 0.7), tail=int(max_chars * 0.2))
        return flat, True
    return shrunk, truncated[0]


# ─────────────────────────────────────────────────────────────
# Tool name normalisation
# ─────────────────────────────────────────────────────────────

def normalize_tool_name(raw: str) -> str:
    """Strip MCP prefixes and normalize to Slack's dotted form where applicable."""
    name = MCP_PREFIX_RE.sub("", raw)
    if name in SLACK_API_METHODS:
        return name.replace("_", ".", 1)
    return name


def iter_json_lines(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


# ─────────────────────────────────────────────────────────────
# Transcript builder
# ─────────────────────────────────────────────────────────────

# Per-block char budgets
THINKING_HEAD, THINKING_TAIL = 400, 100
TEXT_HEAD, TEXT_TAIL = 700, 200
RESULT_HEAD, RESULT_TAIL = 1400, 500
TOOL_ARG_BUDGET = 1000


def _extract_tool_result_text(content) -> str:
    """Extract a single text blob from a tool_result's content field.

    Tool results may be a string, a list of {type, text} parts, or a list
    containing mixed types. This concatenates text fields with a separator
    and tags non-text items.
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)
    parts: list[str] = []
    for part in content:
        if isinstance(part, dict):
            ptype = part.get("type", "")
            if ptype == "text" or "text" in part:
                parts.append(str(part.get("text", "")))
            elif ptype == "image":
                src = part.get("source", {})
                parts.append(f"[image: {src.get('media_type', '?')}]")
            else:
                parts.append(f"[{ptype or 'unknown'} part]")
        else:
            parts.append(str(part))
    return "\n---\n".join(parts)


def build_transcript(session_log: Path, prompt_text: str) -> tuple[list[dict], dict]:
    """Walk JSONL → cleaned, bounded transcript.

    Returns (entries, meta).
    """
    if not session_log.exists():
        return [], {
            "total_turns": 0, "total_chars": 0,
            "tools_truncated": 0, "results_truncated": 0,
            "has_result": False, "unknown_events": [],
        }

    # Group assistant events by message.id; preserve event order within group.
    # We emit one transcript entry per *distinct* content block across the group.
    assistant_blocks: dict[str, list[tuple[str, dict]]] = {}
    assistant_order: list[str] = []
    events_order: list[tuple[str, object]] = []
    has_result = False
    unknown_events: set[str] = set()
    final_text = ""

    for obj in iter_json_lines(session_log):
        t = obj.get("type", "")

        if t == "assistant":
            msg = obj.get("message", {}) or {}
            mid = msg.get("id", f"_anon_{len(assistant_order)}")
            content = msg.get("content")
            if mid not in assistant_blocks:
                assistant_blocks[mid] = []
                assistant_order.append(mid)
                events_order.append(("assistant", mid))
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    assistant_blocks[mid].append((btype, block))
            continue

        if t == "user":
            msg = obj.get("message", {}) or {}
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        events_order.append(("tool_result", block))
            continue

        if t == "tool_result":
            events_order.append(("tool_result", obj))
            continue

        if t == "result":
            has_result = True
            final_text = obj.get("result", "") or ""
            events_order.append(("result", final_text))
            continue

        if t in ("system", "rate_limit_event"):
            continue

        unknown_events.add(t)
        events_order.append(("unknown", obj))

    # Build transcript entries
    entries: list[dict] = []
    tools_truncated = 0
    results_truncated = 0

    # User prompt always first
    entries.append({"role": "user", "type": "prompt", "text": prompt_text})

    for kind, payload in events_order:
        if kind == "assistant":
            mid = payload
            seen_text: set[str] = set()
            seen_thinking: set[str] = set()
            seen_tool: set[str] = set()
            for btype, block in assistant_blocks.get(mid, []):
                if btype == "thinking":
                    text = block.get("thinking", "")
                    sig = text[:80]
                    if sig in seen_thinking:
                        continue
                    seen_thinking.add(sig)
                    truncated, _, _ = smart_truncate(text, THINKING_HEAD, THINKING_TAIL)
                    entries.append({
                        "role": "assistant", "type": "thinking", "text": truncated,
                    })
                elif btype == "text":
                    text = block.get("text", "")
                    sig = text[:80]
                    if sig in seen_text:
                        continue
                    seen_text.add(sig)
                    truncated, _, _ = smart_truncate(text, TEXT_HEAD, TEXT_TAIL)
                    entries.append({
                        "role": "assistant", "type": "text", "text": truncated,
                    })
                elif btype == "tool_use":
                    tid = block.get("id", "")
                    if tid and tid in seen_tool:
                        continue
                    if tid:
                        seen_tool.add(tid)
                    raw_name = block.get("name", "unknown")
                    args = block.get("input", {}) or {}
                    args_shrunk, args_t = truncate_json_payload(args, max_chars=TOOL_ARG_BUDGET)
                    if args_t:
                        tools_truncated += 1
                    entries.append({
                        "role": "assistant", "type": "tool_use",
                        "tool_use_id": tid,
                        "tool_name": normalize_tool_name(raw_name),
                        "tool_name_raw": raw_name,
                        "arguments": args_shrunk,
                        "arguments_truncated": args_t,
                    })
                else:
                    entries.append({
                        "role": "assistant", "type": btype or "unknown",
                        "raw_block_keys": sorted(list(block.keys()))[:10],
                    })

        elif kind == "tool_result":
            block = payload
            tid = block.get("tool_use_id", "")
            is_error = bool(block.get("is_error", False))
            text = _extract_tool_result_text(block.get("content", ""))
            excerpt, was_t, total = smart_truncate(text, RESULT_HEAD, RESULT_TAIL)
            if was_t:
                results_truncated += 1
            entries.append({
                "role": "tool", "type": "tool_result",
                "tool_use_id": tid,
                "is_error": is_error,
                "result_excerpt": excerpt,
                "result_truncated": was_t,
                "result_total_chars": total,
            })

        elif kind == "result":
            truncated, _, _ = smart_truncate(payload, RESULT_HEAD, RESULT_TAIL)
            entries.append({
                "role": "result", "type": "final", "text": truncated,
            })

        elif kind == "unknown":
            obj = payload
            entries.append({
                "role": "unknown", "type": obj.get("type", "unknown"),
            })

    total_chars = sum(
        len(e.get("text", "")) + len(e.get("result_excerpt", ""))
        for e in entries
    )

    meta = {
        "total_turns": sum(1 for e in entries if e.get("role") == "assistant"),
        "total_chars": total_chars,
        "tools_truncated": tools_truncated,
        "results_truncated": results_truncated,
        "has_result": has_result,
        "unknown_events": sorted(unknown_events),
    }
    return entries, meta


# ─────────────────────────────────────────────────────────────
# Per-session metric extraction (unchanged math)
# ─────────────────────────────────────────────────────────────

def parse_session_log(path: Path) -> dict:
    """
    Walk the JSONL events and build a per-session summary.

    Returns a dict with:
      - tool_calls: {"complete": N, "failed": N, "partial": N, "total": N}
      - tools_invoked: [canonical tool name, ...] unique, order of first call
      - failed_details: [{"name": ..., "error": ...}, ...]
      - result_text: the final assistant text from the `result` event (or "")
      - result_subtype: "success" | "error" | ""
      - result_is_error: bool | None
      - has_result: bool (false ⇒ session crashed / truncated)
    """
    tool_invocations: dict[str, dict] = {}
    tools_invoked_canonical: list[str] = []
    tools_seen: set[str] = set()
    failed_details: list[dict] = []

    result_text = ""
    result_subtype = ""
    result_is_error: bool | None = None
    has_result = False

    def walk_content(content):
        if not isinstance(content, list):
            return
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tid = block.get("id", "")
                name = block.get("name", "unknown")
                canon = normalize_tool_name(name)
                # Same tool_use id may appear in multiple streamed events; only record once.
                if tid in tool_invocations:
                    continue
                tool_invocations[tid] = {"name": canon, "raw_name": name, "status": "partial", "error": None}
                if canon not in tools_seen:
                    tools_seen.add(canon)
                    tools_invoked_canonical.append(canon)

    def handle_tool_result(block):
        tid = block.get("tool_use_id", "")
        is_error = bool(block.get("is_error", False))
        rec = tool_invocations.get(tid)
        if not rec:
            return
        if is_error:
            rec["status"] = "failed"
            content = block.get("content", "")
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        parts.append(str(part.get("text", part)))
                    else:
                        parts.append(str(part))
                rec["error"] = " ".join(parts)[:500]
            else:
                rec["error"] = str(content)[:500]
            failed_details.append({"name": rec["name"], "error": rec["error"]})
        else:
            rec["status"] = "complete"

    for obj in iter_json_lines(path):
        t = obj.get("type")

        if t == "assistant":
            msg = obj.get("message", {}) or {}
            walk_content(msg.get("content"))
            continue

        if t == "user":
            msg = obj.get("message", {}) or {}
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        handle_tool_result(block)
            continue

        if t == "tool_result":
            handle_tool_result(obj)
            continue

        if t == "result":
            has_result = True
            result_subtype = obj.get("subtype", "") or ""
            result_is_error = obj.get("is_error")
            result_text = obj.get("result", "") or ""
            continue

    complete = sum(1 for r in tool_invocations.values() if r["status"] == "complete")
    failed = sum(1 for r in tool_invocations.values() if r["status"] == "failed")
    partial = sum(1 for r in tool_invocations.values() if r["status"] == "partial")

    return {
        "tool_calls": {
            "complete": complete,
            "failed": failed,
            "partial": partial,
            "total": complete + failed + partial,
        },
        "tools_invoked": tools_invoked_canonical,
        "failed_details": failed_details[:10],
        "result_text": result_text,
        "result_subtype": result_subtype,
        "result_is_error": result_is_error,
        "has_result": has_result,
    }


def parse_token_trace(path: Path) -> dict:
    """Extract initial_context, peak_context, total_tokens from token_trace.json."""
    try:
        with open(path, encoding="utf-8") as f:
            trace = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"initial_context": 0, "peak_context": 0, "total_tokens": 0}

    initial = 0
    peak = 0
    total = 0
    for snap in trace:
        event = snap.get("event")
        if event == "session_start":
            initial = snap.get("turn_input_tokens", 0) or 0
        cum_in = snap.get("cumulative_input", 0) or 0
        if cum_in > peak:
            peak = cum_in
        if event == "result":
            total = snap.get("total_tokens", 0) or 0

    return {"initial_context": initial, "peak_context": peak, "total_tokens": total}


# ─────────────────────────────────────────────────────────────
# Top-level orchestration
# ─────────────────────────────────────────────────────────────

def _read_results_json(run_dir: Path) -> dict:
    results_path = run_dir / "results.json"
    if not results_path.exists():
        return {}
    with open(results_path, encoding="utf-8") as f:
        return json.load(f)


def resolve_stack(run_dir: Path) -> str:
    """Read the run dir's stack name from results.json.

    Each single-stack run dir records its stack in `results.json["stacks"]`
    as a one-element list.
    """
    raw = _read_results_json(run_dir)
    stacks = raw.get("stacks") or []
    if len(stacks) != 1:
        raise ValueError(
            f"results.json in {run_dir} must declare exactly one stack; got {stacks!r}. "
            "Pass --stack explicitly to override."
        )
    return stacks[0]


def precompute(run_dir: Path, prompts_file: Path, stack: str) -> dict:
    prompts_by_id = {str(p["id"]): p for p in _load_prompts_with_substitutions(prompts_file)}

    raw = _read_results_json(run_dir)
    results       = raw.get("results", {})
    run_at        = raw.get("run_at")
    platform_name = raw.get("platform")
    hintas_params = raw.get("hintas_params")

    prompt_dirs = sorted(
        (p for p in run_dir.iterdir()
         if p.is_dir() and p.name.startswith("p") and p.name[1:].isdigit()),
        key=lambda p: int(p.name[1:]),
    )

    per_prompt: dict[str, dict] = {}
    for pdir in prompt_dirs:
        pid = pdir.name[1:]
        prompt = prompts_by_id.get(pid)
        if not prompt:
            continue

        prompt_text = prompt.get("prompt", "")
        session_log = pdir / "session.log"
        token_trace = pdir / "token_trace.json"

        if session_log.exists():
            parsed = parse_session_log(session_log)
        else:
            parsed = {
                "tool_calls": {"complete": 0, "failed": 0, "partial": 0, "total": 0},
                "tools_invoked": [],
                "failed_details": [],
                "result_text": "",
                "result_subtype": "",
                "result_is_error": None,
                "has_result": False,
            }

        tokens = parse_token_trace(token_trace)
        transcript, transcript_meta = build_transcript(session_log, prompt_text)

        raw_row = results.get(f"p{pid}_{stack}", {})

        per_prompt[pid] = {
            "title":         prompt.get("title", ""),
            "difficulty":    prompt.get("difficulty", "?"),
            "category":      prompt.get("category", "?"),
            "success_criteria": prompt.get("success_criteria", []),
            "prompt":        prompt_text,
            stack: {
                "has_result":        parsed["has_result"],
                "result_subtype":    parsed["result_subtype"],
                "result_is_error":   parsed["result_is_error"],
                "result_text":       parsed["result_text"],
                "tool_calls":        parsed["tool_calls"],
                "tools_invoked":     parsed["tools_invoked"],
                "failed_details":    parsed["failed_details"],
                "initial_context":   tokens["initial_context"],
                "peak_context":      tokens["peak_context"],
                "total_tokens":      tokens["total_tokens"],
                "wall_clock_s":      raw_row.get("wall_clock_s", 0),
                "orchestrator_error": raw_row.get("error"),
                "transcript":        transcript,
                "transcript_meta":   transcript_meta,
            },
        }

    return {
        "run_dir":      str(run_dir.resolve()),
        "run_at":       run_at,
        "platform":     platform_name,
        "stacks":       [stack],
        "hintas_params": hintas_params,
        "prompts_file": str(prompts_file.resolve()),
        "per_prompt":   per_prompt,
    }


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("--run-dir", required=True, type=Path,
                   help="Path to the benchmark run directory "
                        "(e.g. platforms/slack/runs/20260423_2107__slack)")
    p.add_argument("--prompts", required=True, type=Path,
                   help="Path to benchmark_prompts.json")
    p.add_argument("--stack",
                   help="Stack name (default: read from <run-dir>/results.json)")
    p.add_argument("--out", type=Path,
                   help="Output path (default: <run-dir>/analysis_data.json)")


def run(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        print(f"ERROR: run directory does not exist: {run_dir}", file=sys.stderr)
        return 2

    stack = args.stack or resolve_stack(run_dir)
    out = args.out or (run_dir / "analysis_data.json")

    data = precompute(run_dir, args.prompts.resolve(), stack)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    n = len(data["per_prompt"])
    print(f"wrote {out} ({n} prompts, stack={stack})")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    add_arguments(ap)
    sys.exit(run(ap.parse_args()))


if __name__ == "__main__":
    main()
