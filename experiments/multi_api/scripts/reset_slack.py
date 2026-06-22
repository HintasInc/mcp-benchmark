#!/usr/bin/env python3
"""
reset_slack.py  —  Multi-API Benchmark, Slack surface

Resets the Slack surface back to the exact seed snapshot BEFORE every prompt
run, undoing any mutations a prompt may have made. Loads the state file written
by ``seed_slack.py`` and reasons against its ``ground_truth`` answer key.

Standalone: this script does NOT import the slack experiment's utils. The Slack
HTTP wrappers (``api`` / ``api_get`` / ``api_get_paginated``) are inlined below
and gate mutating calls on the module-level ``DRY_RUN`` (GET/read calls always
run, exactly like the reference). Generic plumbing comes from ``common``.

Token:
    export SLACK_TOKEN=xoxp-...                # the agent's user token
    python reset_slack.py                      # full reset
    python reset_slack.py --dry-run            # show what would change
    python reset_slack.py --prompt-id 18       # (informational) which prompt ran
    python reset_slack.py --allow-missing-state  # exit 0 if not seeded yet

What this resets:
  - Channel memberships (re-invites kicked seed members, removes extras)
  - The agent's prompt-created messages (anything outside the seed ts set)
  - The agent's reactions (seed set is empty → strips ALL of them)
  - Non-seed channels (archives anything outside the seed set / ignore patterns)
  - Scheduled messages (cancels any agent-created — defensive; none seeded)

Never kicks the agent. Mirrors the dry-run logging style ([DRY]/[WARN]) and the
``time.sleep`` throttling of experiments/slack/scripts/reset_workspace.py.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from common import (log, warn, err, section, subsection, set_dry_run, load_users,
    build_substitution_map, subst, leads, team_distribution, agent_logical_id,
    email_of, name_of, save_state, load_state, resolve_state_file, require_env,
    add_stack_arg, stack_env)
from benchmarking.clock import BENCHMARK_NOW, BENCHMARK_NOW_EPOCH

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://slack.com/api"

# ---------------------------------------------------------------------------
# Token / headers (mirror experiments/slack/scripts/utils.py)
# ---------------------------------------------------------------------------

TOKEN: str = ""
HEADERS: dict = {"Authorization": "", "Content-Type": "application/json; charset=utf-8"}

# One source of truth for dry-run, shared with common. The inline api wrappers
# below check THIS module-level flag for mutating calls.
DRY_RUN: bool = False


def set_token(token: str) -> None:
    """Update the token used by ``api`` / ``api_get`` for subsequent calls."""
    global TOKEN
    TOKEN = token
    HEADERS["Authorization"] = f"Bearer {token}"


# Initialise from the env so module import alone is enough for the common case.
set_token(os.environ.get("SLACK_TOKEN", ""))


# ---------------------------------------------------------------------------
# Slack HTTP client (inlined from experiments/slack/scripts/utils.py)
# ---------------------------------------------------------------------------

def api(method: str, **kwargs) -> dict:
    """POST to slack.com/api/<method>. Raises ``RuntimeError`` on ``ok=false``."""
    resp = requests.post(f"{BASE_URL}/{method}", headers=HEADERS, json=kwargs)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method} failed: {data.get('error')} — {data}")
    return data


def api_get(method: str, params: dict | None = None) -> dict:
    """GET slack.com/api/<method>. Raises ``RuntimeError`` on ``ok=false``."""
    resp = requests.get(f"{BASE_URL}/{method}", headers=HEADERS, params=params or {})
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"GET {method} failed: {data.get('error')} — {data}")
    return data


def api_get_paginated(method: str, params: dict, items_key: str, limit: int = 200) -> list:
    """Accumulate all items across cursor pages."""
    out: list = []
    cursor = None
    while True:
        p = dict(params)
        p["limit"] = limit
        if cursor:
            p["cursor"] = cursor
        data = api_get(method, p)
        out.extend(data.get(items_key, []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return out


def require_token(env_var: str = "SLACK_TOKEN") -> None:
    """Exit with a friendly message when the resolved token is empty."""
    if not TOKEN:
        err(f"Set {env_var} env var or pass --token xoxp-... (agent token, Miranda)")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Fixture (the seed snapshot this reset restores to)
# ---------------------------------------------------------------------------

CHANNEL_SEED_NAMES: dict[str, str] = {
    "C_GENERAL":   "general",
    "C_ANNOUNCE":  "announcements",
    "C_SUPPORT":   "support",
    "C_INCIDENTS": "incidents",
    "C_LEADS":     "leads",
}

AGENT = agent_logical_id()  # U01MIRANDA (Miranda is the acting agent)

# State loaded from workspace_state_slack.json.
USER_ID_MAP: dict[str, str] = {}
CHANNEL_ID_MAP: dict[str, str] = {}
DM_ID_MAP: dict[str, str] = {}
MSG_TS_MAP: dict[str, dict] = {}
GROUND_TRUTH: dict = {}
IGNORE_CHANNEL_NAME_RES: list[re.Pattern] = []


def uid(logical: str) -> str:
    return USER_ID_MAP.get(logical, logical)


def cid(logical: str) -> str:
    return CHANNEL_ID_MAP.get(logical, logical)


def _channel_memberships() -> dict[str, list[str]]:
    """Logical channel key → seed member logical ids (agent excluded — it is a
    member as creator, never kicked)."""
    everyone = team_distribution()  # all 8 humans
    return {
        "C_GENERAL":   everyone,
        "C_ANNOUNCE":  everyone,
        "C_SUPPORT":   everyone,
        "C_INCIDENTS": everyone,
        "C_LEADS":     leads(),  # 3
    }


def hydrate_state(state: dict) -> None:
    """Populate the module-level maps from the loaded state dict (in place)."""
    USER_ID_MAP.clear()
    USER_ID_MAP.update(state.get("user_id_map", {}) or {})
    CHANNEL_ID_MAP.clear()
    CHANNEL_ID_MAP.update(state.get("channel_id_map", {}) or {})
    DM_ID_MAP.clear()
    DM_ID_MAP.update(state.get("dm_id_map", {}) or {})
    MSG_TS_MAP.clear()
    MSG_TS_MAP.update(state.get("msg_ts_map", {}) or {})
    GROUND_TRUTH.clear()
    GROUND_TRUTH.update(state.get("ground_truth", {}) or {})

    ignore = GROUND_TRUTH.get("ignore", {}) or {}
    IGNORE_CHANNEL_NAME_RES.clear()
    IGNORE_CHANNEL_NAME_RES.extend(re.compile(p) for p in ignore.get("channel_name_patterns", []))


def _seed_ts_set() -> set[str]:
    """The set of real ts values seeded (used to spare seed messages from deletion)."""
    out: set[str] = set()
    for entry in MSG_TS_MAP.values():
        ts = entry.get("ts") if isinstance(entry, dict) else entry
        if ts and not str(ts).startswith("PLACEHOLDER") and ts != "ERROR":
            out.add(ts)
    return out


# ---------------------------------------------------------------------------
# 1. Channel memberships
# ---------------------------------------------------------------------------

def get_channel_members(real_ch_id: str) -> set[str]:
    members: set[str] = set()
    cursor = None
    while True:
        params = {"channel": real_ch_id, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = api_get("conversations.members", params)
        members.update(data.get("members", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return members


def reset_memberships() -> None:
    """
    Restore each seed channel's membership to its seed roster: re-invite removed
    seed members (e.g. prompt 18 kicks Devon from 'leads') and kick extras (e.g.
    prompt 6/21 invite priya/ember to 'general'). Never kicks the agent.
    """
    section("1. Resetting channel memberships")
    agent_real = uid(AGENT)
    for logical_ch_id, logical_members in _channel_memberships().items():
        real_ch = cid(logical_ch_id)
        if not real_ch:
            warn(f"No real ID for {logical_ch_id}")
            continue

        seed_real_ids = {uid(m) for m in logical_members}

        try:
            current_members = get_channel_members(real_ch)
        except RuntimeError as e:
            warn(f"Could not get members for {logical_ch_id}: {e}")
            continue

        name = CHANNEL_SEED_NAMES.get(logical_ch_id, logical_ch_id)

        to_add = seed_real_ids - current_members
        if to_add:
            to_add_filtered = [m for m in to_add if m != agent_real]
            if to_add_filtered:
                if DRY_RUN:
                    warn(f"#{name}: would add {to_add_filtered}")
                else:
                    try:
                        api("conversations.invite", channel=real_ch, users=",".join(to_add_filtered))
                        log(f"#{name}: added {len(to_add_filtered)} members")
                    except RuntimeError as e:
                        warn(f"#{name} invite failed: {e}")

        to_remove = current_members - seed_real_ids
        for m in to_remove:
            if m == agent_real:
                continue
            if DRY_RUN:
                warn(f"#{name}: would kick extra member {m}")
            else:
                try:
                    api("conversations.kick", channel=real_ch, user=m)
                    log(f"#{name}: kicked extra member {m}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    if "cant_kick_self" in str(e) or "not_in_channel" in str(e):
                        pass
                    else:
                        warn(f"#{name} kick {m} failed: {e}")

        if not to_add and not to_remove:
            log(f"#{name} membership OK")


# ---------------------------------------------------------------------------
# 2. Delete the agent's prompt-created messages
# ---------------------------------------------------------------------------

def delete_agent_messages() -> None:
    """
    Delete messages posted by the agent that are NOT in the seed ts set (i.e.
    created during a prompt). Scans the seed channels + the agent's DMs.
    """
    section("2. Removing agent's prompt-created messages")
    agent_real = uid(AGENT)
    seed_ts_set = _seed_ts_set()

    channels = list(CHANNEL_ID_MAP.values())

    # The agent's DMs (conversations.list types=im).
    try:
        for ch in api_get_paginated("conversations.list", {"types": "im"}, "channels"):
            channels.append(ch["id"])
    except RuntimeError as e:
        warn(f"conversations.list (im) failed: {e}")

    for real_ch in channels:
        try:
            data = api_get("conversations.history", {"channel": real_ch, "limit": 50})
        except RuntimeError:
            continue
        for msg in data.get("messages", []):
            if msg.get("user") != agent_real:
                continue
            ts = msg.get("ts")
            if ts in seed_ts_set:
                continue
            if msg.get("subtype") in ("bot_message", "channel_join", "channel_leave"):
                continue
            if DRY_RUN:
                warn(f"Would delete agent's message ts={ts} in {real_ch}: {msg.get('text','')[:50]}")
            else:
                try:
                    api("chat.delete", channel=real_ch, ts=ts)
                    log(f"Deleted agent msg ts={ts} in {real_ch}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    warn(f"Delete failed {ts}: {e}")


# ---------------------------------------------------------------------------
# 3. Reset reactions — seed set is empty, strip ALL of the agent's reactions
# ---------------------------------------------------------------------------

def reset_reactions() -> None:
    """
    The seed reaction set is empty, so remove every reaction the agent added
    (e.g. prompt 17 adds ✅). Mirrors the "strip extra" half of the reference's
    reset_reactions.
    """
    section("3. Resetting reactions")
    agent_real = uid(AGENT)

    try:
        data = api_get("reactions.list", {"user": agent_real, "full": True, "limit": 100})
    except RuntimeError as e:
        warn(f"reactions.list failed: {e}")
        return
    for item in data.get("items", []):
        if item.get("type") != "message":
            continue
        msg = item.get("message", {})
        msg_ts = msg.get("ts")
        for rxn in msg.get("reactions", []):
            if agent_real not in rxn.get("users", []):
                continue
            emoji = rxn["name"]
            if DRY_RUN:
                warn(f"Would remove agent reaction :{emoji}: ts={msg_ts}")
            else:
                try:
                    api("reactions.remove",
                        channel=item.get("channel", ""), timestamp=msg_ts, name=emoji)
                    log(f"Removed :{emoji}: ts={msg_ts}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    if "no_reaction" not in str(e):
                        warn(f"Remove reaction failed: {e}")


# ---------------------------------------------------------------------------
# 4. Archive sweep — any non-seed channel
# ---------------------------------------------------------------------------

def sweep_non_seed_channels() -> None:
    """
    Archive every active channel that is not in the seed set and not matching an
    ignore pattern (removes prompt-created channels like 'atlas-migration',
    'leads-private'). Trust the seed channel ids recorded at seed time.
    """
    section("4. Archive sweep — non-seed channels")

    seed_real_ids = {cid(lid) for lid in CHANNEL_SEED_NAMES if cid(lid)}
    seed_real_ids.update(GROUND_TRUTH.get("seed_channel_ids", []) or [])

    to_archive: list[tuple[str, str]] = []
    cursor = None
    while True:
        params = {
            "types": "public_channel,private_channel",
            "exclude_archived": True,
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor
        try:
            data = api_get("conversations.list", params)
        except RuntimeError as e:
            warn(f"conversations.list failed during sweep: {e}")
            return
        for ch in data.get("channels", []):
            ch_id = ch["id"]
            ch_name = ch.get("name", "")
            if ch_id in seed_real_ids:
                continue
            if any(rx.search(ch_name) for rx in IGNORE_CHANNEL_NAME_RES):
                log(f"#{ch_name} matches ignore pattern — skipping")
                continue
            to_archive.append((ch_id, ch_name))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    if not to_archive:
        log("No non-seed channels found — workspace clean ✓")
        return

    for ch_id, ch_name in to_archive:
        if DRY_RUN:
            warn(f"#{ch_name} ({ch_id}) is non-seed — would archive")
            continue
        try:
            api("conversations.archive", channel=ch_id)
            log(f"Archived non-seed #{ch_name}")
            time.sleep(0.3)
        except RuntimeError as e:
            msg = str(e)
            if "already_archived" in msg:
                log(f"#{ch_name} already archived — OK")
            elif "not_in_channel" in msg:
                try:
                    api("conversations.join", channel=ch_id)
                    api("conversations.archive", channel=ch_id)
                    log(f"Joined and archived non-seed #{ch_name}")
                    time.sleep(0.3)
                except RuntimeError as e2:
                    warn(f"#{ch_name}: archive failed after join: {e2}")
            elif "cant_archive_general" in msg or "method_not_supported_for_channel_type" in msg:
                warn(f"#{ch_name}: Slack refused archive ({msg}) — drift will be flagged by verify")
            else:
                warn(f"#{ch_name}: archive failed: {e}")


# ---------------------------------------------------------------------------
# 5. Cancel agent-created scheduled messages (defensive; none seeded)
# ---------------------------------------------------------------------------

def reset_scheduled_messages() -> None:
    section("5. Resetting scheduled messages")
    agent_real = uid(AGENT)

    try:
        data = api_get("chat.scheduledMessages.list", {"limit": 100})
    except RuntimeError as e:
        warn(f"Could not list scheduled messages: {e}")
        return

    for msg in data.get("scheduled_messages", []):
        if msg.get("user_id") != agent_real:
            continue
        msg_id = msg.get("id")
        ch_id = msg.get("channel_id")
        text = msg.get("text", "")[:50]
        if DRY_RUN:
            warn(f"Would cancel agent scheduled message: {text} (id={msg_id})")
        else:
            try:
                api("chat.deleteScheduledMessage", channel=ch_id, scheduled_message_id=msg_id)
                log(f"Cancelled agent scheduled msg: {text}")
                time.sleep(0.2)
            except RuntimeError as e:
                warn(f"Cancel scheduled msg failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description="Reset the multi-API benchmark Slack surface to its seed snapshot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without making API calls")
    parser.add_argument("--prompt-id",
                        help="(informational) Which prompt you just ran — logged for traceability")
    parser.add_argument("--state-file",
                        help="Explicit path for the workspace state file (overrides the default).")
    parser.add_argument("--token", help="Slack user token (overrides BASELINE_/HINTAS_SLACK_TOKEN)")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. before seed), exit 0 instead of erroring")
    add_stack_arg(parser)
    args = parser.parse_args()

    DRY_RUN = args.dry_run
    set_dry_run(args.dry_run)
    set_token(args.token or stack_env(args.stack, "SLACK_TOKEN"))
    require_token(f"{'BASELINE_' if args.stack == 'baseline' else 'HINTAS_'}SLACK_TOKEN")

    print(f"\n{'=' * 60}")
    print("  Multi-API Benchmark — Slack Reset")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Resetting after prompt: {args.prompt_id}")
    print(f"{'=' * 60}")

    # The persona cast drives the seed membership rosters this reset restores to.
    load_users()

    state_path = resolve_state_file(args.state_file, "slack", args.stack)
    state = load_state(state_path, allow_missing=args.allow_missing_state)
    if state is None:
        return
    hydrate_state(state)

    reset_memberships()
    delete_agent_messages()
    reset_reactions()
    sweep_non_seed_channels()
    reset_scheduled_messages()

    print(f"\n{'=' * 60}")
    print(f"  RESET {'(DRY RUN)' if DRY_RUN else 'COMPLETE'}")
    print("  ⚠️  Manual/seed-only items:")
    print("     - Seeded message ts values (posted at real wall-clock time)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
