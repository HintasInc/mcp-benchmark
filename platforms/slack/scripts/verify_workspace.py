#!/usr/bin/env python3
"""
verify_workspace.py  —  Hintas Slack Benchmark state verifier

Queries the live Slack workspace and asserts it matches the seeded state.
The state path is resolved via ``--stack`` (loading
``workspace_state_<stack>.json``) for standalone runs, or via
``--state-file`` from the orchestrator (driven by the manifest's
``state_file_template``). Intended to run after ``reset_workspace.py`` and
before a benchmark prompt session, as a fairness gate proving each MCP stack
starts from the same state.

Usage:
    export SLACK_TOKEN=xoxp-...
    python verify_workspace.py                        # check; exit 1 on hard drift
    python verify_workspace.py --report drift.json    # write structured report
    python verify_workspace.py --soft                 # exit 0 even on hard drift
    python verify_workspace.py --state-file path.json # override auto state resolution

Exit codes:
    0 — clean (no hard drift)
    1 — hard drift detected
    2 — structural / API failure (state file missing, auth, etc.)

Drift categories:
    hard — would bias the Slack-MCP vs Hintas-MCP comparison
    soft — informational; known limitation or agent-only state

Source of truth:
    When the loaded state file carries a ``ground_truth`` block (produced by
    seed_workspace.py post-seed snapshot), the verifier derives expected
    channel names, topics, archive/private state, and membership from that
    block, and applies the per-workspace ignore set. State files without
    ``ground_truth`` fall back to the constants in ``constants.py`` and no
    ignore-set filtering — re-seed to upgrade.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from constants import (
    CHANNEL_MEMBERS, CHANNEL_SEED_ARCHIVED, CHANNEL_SEED_NAMES,
    CHANNEL_SEED_PRIVATE, CHANNEL_SEED_TOPICS, SEED_REACTIONS,
    STANDUP_CHANNEL, STANDUP_POST_AT_EPOCH, STANDUP_TEXT,
)
from utils import (
    CHANNEL_ID_MAP, DM_ID_MAP, GROUND_TRUTH, IGNORE_USER_IDS, MSG_TS_MAP, STATE,
    api_get, api_get_paginated, load_state, load_token_for_stack, resolve_state_file, set_token, subsection as section, uid,
)
import utils

# ---------------------------------------------------------------------------
# Drift collection
# ---------------------------------------------------------------------------

@dataclass
class Drift:
    dimension: str
    severity: str
    message: str
    context: dict = field(default_factory=dict)


DRIFTS: list[Drift] = []


def add_drift(dimension: str, message: str, severity: str = "hard", **context):
    DRIFTS.append(Drift(dimension=dimension, severity=severity, message=message, context=context))


# ---------------------------------------------------------------------------
# Expected state — populated from ground_truth when available, otherwise
# falls back to the constants module. Kept local to verify so we don't
# mutate the shared constants dicts.
# ---------------------------------------------------------------------------

EXPECTED_NAMES: dict[str, str] = dict(CHANNEL_SEED_NAMES)
EXPECTED_TOPICS: dict[str, str] = dict(CHANNEL_SEED_TOPICS)
EXPECTED_PRIVATE: dict[str, bool] = dict(CHANNEL_SEED_PRIVATE)
EXPECTED_ARCHIVED: set[str] = set(CHANNEL_SEED_ARCHIVED)
EXPECTED_MEMBERS_REAL: dict[str, set[str]] = {}


def derive_expected_from_truth() -> None:
    """
    Replace the fallback EXPECTED_* tables with values derived from the
    ground-truth snapshot. ``EXPECTED_MEMBERS_REAL`` keys by logical channel
    ID and stores **real** Slack user IDs so check_memberships can compare
    against real IDs without an ``uid()`` round-trip for unresolved bot
    accounts (e.g. U10BOT_CI).
    """
    if not GROUND_TRUTH:
        return

    by_real = {ch["id"]: ch for ch in GROUND_TRUTH.get("channels", []) if ch.get("id")}

    new_names: dict = {}
    new_topics: dict = {}
    new_private: dict = {}
    new_archived: set = set()
    new_members: dict[str, set[str]] = {}

    for logical, real in CHANNEL_ID_MAP.items():
        ch = by_real.get(real)
        if not ch:
            continue
        new_names[logical] = ch.get("name", "")
        new_topics[logical] = ch.get("topic", "") or ""
        if ch.get("is_private"):
            new_private[logical] = True
        if ch.get("is_archived"):
            new_archived.add(logical)
        new_members[logical] = set(ch.get("members", []) or [])

    if new_names:
        EXPECTED_NAMES.clear()
        EXPECTED_NAMES.update(new_names)
    if new_topics:
        EXPECTED_TOPICS.clear()
        EXPECTED_TOPICS.update(new_topics)
    EXPECTED_PRIVATE.clear()
    EXPECTED_PRIVATE.update(new_private)
    EXPECTED_ARCHIVED.clear()
    EXPECTED_ARCHIVED.update(new_archived)
    EXPECTED_MEMBERS_REAL.clear()
    EXPECTED_MEMBERS_REAL.update(new_members)


# ---------------------------------------------------------------------------
# 1. Channel topology
# ---------------------------------------------------------------------------

def check_channel_topology():
    section("1. Channel topology")

    expected_names = set(EXPECTED_NAMES.values())
    expected_ids   = set(CHANNEL_ID_MAP.values())

    for logical_id, expected_name in EXPECTED_NAMES.items():
        real_id = CHANNEL_ID_MAP.get(logical_id)
        if not real_id:
            add_drift("topology", f"{logical_id}: no real channel ID recorded in state", logical_id=logical_id)
            continue
        try:
            info = api_get("conversations.info", {"channel": real_id})["channel"]
        except RuntimeError as e:
            add_drift("topology", f"{logical_id} ({expected_name}): conversations.info failed: {e}",
                      logical_id=logical_id)
            continue

        actual_name     = info.get("name", "")
        actual_topic    = info.get("topic", {}).get("value", "")
        actual_archived = info.get("is_archived", False)
        actual_private  = info.get("is_private", False)

        if actual_name != expected_name:
            add_drift("topology", f"#{actual_name} should be named #{expected_name}",
                      logical_id=logical_id, actual=actual_name, expected=expected_name)
        if actual_topic != EXPECTED_TOPICS.get(logical_id, ""):
            add_drift("topology", f"#{actual_name} topic drift",
                      logical_id=logical_id, actual=actual_topic,
                      expected=EXPECTED_TOPICS.get(logical_id, ""))

        expected_archived = logical_id in EXPECTED_ARCHIVED
        if actual_archived != expected_archived:
            add_drift("topology", f"#{actual_name} archive={actual_archived} expected={expected_archived}",
                      logical_id=logical_id)

        expected_private = EXPECTED_PRIVATE.get(logical_id, False)
        if actual_private != expected_private:
            add_drift("topology", f"#{actual_name} private={actual_private} expected={expected_private}",
                      logical_id=logical_id)

    try:
        channels = api_get_paginated(
            "conversations.list",
            {"types": "public_channel,private_channel", "exclude_archived": True},
            "channels",
        )
    except RuntimeError as e:
        add_drift("topology", f"conversations.list failed: {e}")
        return

    for ch in channels:
        if ch["id"] in expected_ids:
            continue
        if ch["name"] in expected_names:
            continue
        if any(rx.search(ch["name"]) for rx in utils.IGNORE_CHANNEL_NAME_RES):
            continue
        add_drift("topology", f"stray non-archived channel #{ch['name']} ({ch['id']}) outside seed set",
                  channel_id=ch["id"], channel_name=ch["name"])


# ---------------------------------------------------------------------------
# 2. Channel memberships
# ---------------------------------------------------------------------------

def check_memberships(bot_ids: set[str]):
    section("2. Channel memberships")
    use_truth = bool(EXPECTED_MEMBERS_REAL)
    iter_keys = EXPECTED_MEMBERS_REAL.keys() if use_truth else CHANNEL_MEMBERS.keys()

    for logical_ch_id in iter_keys:
        real_ch = CHANNEL_ID_MAP.get(logical_ch_id)
        name = EXPECTED_NAMES.get(logical_ch_id, logical_ch_id)
        if not real_ch:
            continue

        try:
            members = set()
            cursor = None
            while True:
                params = {"channel": real_ch, "limit": 200}
                if cursor:
                    params["cursor"] = cursor
                data = api_get("conversations.members", params)
                members.update(data.get("members", []))
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        except RuntimeError as e:
            add_drift("membership", f"#{name}: conversations.members failed: {e}", channel=logical_ch_id)
            continue

        if use_truth:
            expected = EXPECTED_MEMBERS_REAL.get(logical_ch_id, set())
        else:
            expected = {uid(m) for m in CHANNEL_MEMBERS.get(logical_ch_id, [])}

        missing = expected - members
        for m in missing:
            add_drift("membership", f"#{name}: expected member {m} missing",
                      channel=logical_ch_id, user=m)

        extras = members - expected - bot_ids - IGNORE_USER_IDS
        for m in extras:
            add_drift("membership", f"#{name}: unexpected member {m}",
                      severity="soft", channel=logical_ch_id, user=m)


# ---------------------------------------------------------------------------
# 3. Seeded messages + no strays
# ---------------------------------------------------------------------------

def fetch_channel_messages(real_ch: str) -> tuple[list[dict], dict[str, list[dict]]]:
    """
    Return (top_level_messages, replies_by_thread_ts).
    Paginates history and fetches replies for any message with reply_count > 0.
    """
    top: list[dict] = []
    cursor = None
    while True:
        params = {"channel": real_ch, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = api_get("conversations.history", params)
        top.extend(data.get("messages", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    replies: dict[str, list[dict]] = {}
    for m in top:
        if m.get("reply_count", 0) > 0 and m.get("thread_ts") == m.get("ts"):
            cursor = None
            bucket: list[dict] = []
            while True:
                params = {"channel": real_ch, "ts": m["ts"], "limit": 200}
                if cursor:
                    params["cursor"] = cursor
                rd = api_get("conversations.replies", params)
                bucket.extend(rd.get("messages", []))
                cursor = rd.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            replies[m["ts"]] = [r for r in bucket if r.get("ts") != m["ts"]]
            time.sleep(0.1)
    return top, replies


def check_messages():
    section("3. Seeded messages")

    seeded_ts = set(MSG_TS_MAP.values())
    claude_real = uid("U05CLAUDE")

    all_channels = list(CHANNEL_ID_MAP.values()) + list(DM_ID_MAP.values())
    observed_ts: set[str] = set()

    for real_ch in all_channels:
        try:
            top, replies = fetch_channel_messages(real_ch)
        except RuntimeError as e:
            add_drift("messages", f"history fetch failed for {real_ch}: {e}", channel=real_ch)
            continue

        for m in top:
            ts = m.get("ts")
            if ts:
                observed_ts.add(ts)
            if m.get("user") != claude_real:
                continue
            if m.get("subtype") in ("bot_message", "channel_join", "channel_leave"):
                continue
            if ts and ts not in seeded_ts:
                add_drift("messages", f"stray agent message in {real_ch} ts={ts}: {m.get('text','')[:60]}",
                          channel=real_ch, ts=ts)

        for parent_ts, thread_msgs in replies.items():
            for m in thread_msgs:
                ts = m.get("ts")
                if ts:
                    observed_ts.add(ts)
                if m.get("user") != claude_real:
                    continue
                if m.get("subtype") in ("bot_message", "channel_join", "channel_leave"):
                    continue
                if ts and ts not in seeded_ts:
                    add_drift("messages",
                              f"stray agent thread reply in {real_ch} parent={parent_ts} ts={ts}: {m.get('text','')[:60]}",
                              channel=real_ch, parent_ts=parent_ts, ts=ts)

    missing = seeded_ts - observed_ts
    for label, ts in MSG_TS_MAP.items():
        if ts in missing:
            add_drift("messages", f"seeded message {label} (ts={ts}) missing from workspace",
                      label=label, ts=ts)


# ---------------------------------------------------------------------------
# 4. Reactions on seeded messages
# ---------------------------------------------------------------------------

def check_reactions():
    section("4. Reactions")

    claude_real = uid("U05CLAUDE")
    expected_by_msg: dict[str, set[str]] = {}
    for label, emoji, _ch_logical in SEED_REACTIONS:
        expected_by_msg.setdefault(label, set()).add(emoji)

    checked_ts: set[str] = set()

    for label, emoji, ch_logical in SEED_REACTIONS:
        ts = MSG_TS_MAP.get(label)
        real_ch = CHANNEL_ID_MAP.get(ch_logical)
        if not ts or not real_ch:
            add_drift("reactions", f"cannot resolve message {label} or channel {ch_logical}",
                      label=label, channel=ch_logical)
            continue
        if ts in checked_ts:
            continue
        checked_ts.add(ts)

        try:
            rd = api_get("reactions.get", {"channel": real_ch, "timestamp": ts, "full": "true"})
        except RuntimeError as e:
            add_drift("reactions", f"{label}: reactions.get failed: {e}", label=label)
            continue

        reactions = rd.get("message", {}).get("reactions", []) or []
        expected = expected_by_msg.get(label, set())
        present_claude: set[str] = set()
        for rxn in reactions:
            if claude_real in rxn.get("users", []):
                present_claude.add(rxn["name"])

        missing = expected - present_claude
        for em in missing:
            add_drift("reactions", f"{label}: expected agent reaction :{em}: missing",
                      label=label, emoji=em)

        extras = present_claude - expected
        for em in extras:
            add_drift("reactions", f"{label}: unexpected agent reaction :{em}:",
                      label=label, emoji=em)


# ---------------------------------------------------------------------------
# 5. Pins (seed creates none; any pin is drift)
# ---------------------------------------------------------------------------

def check_pins():
    section("5. Pins")
    for logical_id, real_ch in CHANNEL_ID_MAP.items():
        if logical_id in EXPECTED_ARCHIVED:
            continue
        try:
            data = api_get("pins.list", {"channel": real_ch})
        except RuntimeError as e:
            add_drift("pins", f"{logical_id}: pins.list failed: {e}", channel=logical_id)
            continue
        items = data.get("items", []) or []
        for item in items:
            if item.get("type") != "message":
                continue
            msg_ts = item.get("message", {}).get("ts", "")
            add_drift("pins",
                      f"#{EXPECTED_NAMES.get(logical_id, logical_id)}: unexpected pin ts={msg_ts}",
                      channel=logical_id, ts=msg_ts)


# ---------------------------------------------------------------------------
# 6. DND snooze
# ---------------------------------------------------------------------------

def check_dnd():
    section("6. DND snooze")
    try:
        data = api_get("dnd.info")
    except RuntimeError as e:
        add_drift("dnd", f"dnd.info failed: {e}", severity="soft")
        return
    if data.get("snooze_enabled"):
        add_drift("dnd",
                  f"agent DND snooze is active (ends at {data.get('snooze_endtime')})",
                  snooze_endtime=data.get("snooze_endtime"))


# ---------------------------------------------------------------------------
# 7. Scheduled messages
# ---------------------------------------------------------------------------

def check_scheduled_messages():
    section("7. Scheduled messages")
    try:
        data = api_get("chat.scheduledMessages.list", {"limit": 100})
    except RuntimeError as e:
        add_drift("scheduled", f"chat.scheduledMessages.list failed: {e}")
        return

    claude_real = uid("U05CLAUDE")
    standup_ch = CHANNEL_ID_MAP.get(STANDUP_CHANNEL)
    standup_expected = STANDUP_POST_AT_EPOCH > time.time()

    standup_found = False
    for m in data.get("scheduled_messages", []):
        if m.get("user_id") != claude_real:
            continue
        ch = m.get("channel_id")
        text = m.get("text", "")
        if ch == standup_ch and STANDUP_TEXT in text:
            standup_found = True
            continue
        add_drift("scheduled",
                  f"stray agent scheduled message in {ch}: {text[:60]}",
                  channel=ch, text=text[:200])

    if standup_expected and not standup_found:
        add_drift("scheduled", "expected weekly standup scheduled message missing in #marketing")
    elif not standup_expected and not standup_found:
        add_drift("scheduled",
                  "weekly standup scheduled message missing — benchmark_now anchor is in the past "
                  "so chat.scheduleMessage rejects with time_in_past",
                  severity="soft")


# ---------------------------------------------------------------------------
# Bot / app users
# ---------------------------------------------------------------------------

def fetch_bot_user_ids() -> set[str]:
    """Return the set of user IDs that are bots, apps, or Slackbot."""
    if GROUND_TRUTH.get("users"):
        return {
            u["id"] for u in GROUND_TRUTH["users"]
            if u.get("id") and (u.get("is_bot") or u.get("is_app_user") or u["id"] == "USLACKBOT")
        }
    try:
        members = api_get_paginated("users.list", {}, "members")
    except RuntimeError:
        return set()
    bots = set()
    for u in members:
        if u.get("is_bot") or u.get("id") == "USLACKBOT":
            bots.add(u["id"])
    return bots


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report():
    hard = [d for d in DRIFTS if d.severity == "hard"]
    soft = [d for d in DRIFTS if d.severity == "soft"]

    print()
    print(f"  Drift summary: {len(hard)} hard, {len(soft)} soft")

    if hard:
        print("\n  Hard drift:")
        for d in hard:
            print(f"    [{d.dimension}] {d.message}")
    if soft:
        print("\n  Soft drift:")
        for d in soft:
            print(f"    [{d.dimension}] {d.message}")
    if not hard and not soft:
        print("  ✓ Workspace matches seeded state.")


def write_report(path: str, team_id: str):
    out = {
        "verified_at":   datetime.now(timezone.utc).isoformat(),
        "team_id":       team_id,
        "hard_count":    sum(1 for d in DRIFTS if d.severity == "hard"),
        "soft_count":    sum(1 for d in DRIFTS if d.severity == "soft"),
        "drifts":        [asdict(d) for d in DRIFTS],
    }
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Report written → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Verify Hintas benchmark workspace against seeded state")
    parser.add_argument("--token", help="Slack user token (overrides SLACK_TOKEN env var)")
    parser.add_argument("--state-file", help="Explicit path for the workspace state file (overrides --stack).")
    parser.add_argument("--stack",
                        help="Stack name (e.g. slack, hintas). Loads workspace_state_<stack>.json "
                             "and resolves the auth token from the manifest's token_env.")
    parser.add_argument("--report", help="Write a structured drift report to this path")
    parser.add_argument("--soft", action="store_true", help="Always exit 0, even on hard drift")
    args = parser.parse_args()

    if args.token:
        set_token(args.token)
    elif args.stack:
        set_token(load_token_for_stack(args.stack))
    if not utils.TOKEN:
        print("ERROR: Set SLACK_TOKEN env var or pass --token xoxp-...")
        sys.exit(2)

    print("\n  Hintas Benchmark — Workspace Verifier")

    state_path = resolve_state_file(args.state_file, args.stack)
    load_state(state_path)

    if GROUND_TRUTH:
        derive_expected_from_truth()
        print(
            f"  Ground-truth: {len(GROUND_TRUTH.get('users', []))} users, "
            f"{len(GROUND_TRUTH.get('channels', []))} channels, "
            f"{len(IGNORE_USER_IDS)} user(s) and "
            f"{len(utils.IGNORE_CHANNEL_NAME_RES)} channel pattern(s) on the ignore list"
        )
    else:
        print("  ⚠️  state file has no ground_truth block — falling back to constants module")
        print("     re-run seed_workspace.py to capture the augmented snapshot")

    bot_ids = fetch_bot_user_ids()

    check_channel_topology()
    check_memberships(bot_ids)
    check_messages()
    check_reactions()
    check_pins()
    check_dnd()
    check_scheduled_messages()

    print_report()

    if args.report:
        write_report(args.report, STATE.get("team_id", ""))

    hard = [d for d in DRIFTS if d.severity == "hard"]
    if hard and not args.soft:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
