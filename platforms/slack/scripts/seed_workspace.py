#!/usr/bin/env python3
"""
seed_workspace.py  —  Hintas Slack Benchmark v4 (Scenario A)

Creates (or verifies) every entity defined in workspace_state.md §2-§7:
  users, channels, DMs, MPIM, threads, reactions, reminders,
  one scheduled message, files, custom emoji.

Scenario A (single-token): the previous Miranda Okonkwo (U01MIRANDA) persona
is merged into the agent (U05CLAUDE, display name "Miranda"). All seeded
messages, reactions, reminders, scheduled messages, and file uploads are
authored by the agent because only one token is available.

Usage:
    export SLACK_TOKEN=xoxp-...          # agent's user token
    python seed_workspace.py             # full seed
    python seed_workspace.py --verify    # dry-run: report what's missing

IMPORTANT:
  - The token must belong to U05CLAUDE (the agent, display name Miranda).
  - Run this ONCE against a fresh Hintas workspace.
  - For per-prompt resets, use reset_workspace.py instead.
  - State is written to ``workspace_state_<stack>.json`` (resolved via
    ``--stack`` for standalone runs, or ``--state-file`` from the orchestrator).
  - Beyond ID maps, the state file embeds a ``ground_truth`` block: a full
    snapshot of every entity at seed time. Prompts express success criteria
    as references into that block.
  - benchmark_now is anchored to 2026-04-19T10:00:00-07:00.
"""
from __future__ import annotations

import argparse
import os
import time
import json
from datetime import datetime, timezone

from benchmarking.clock import BENCHMARK_NOW, BENCHMARK_NOW_EPOCH
from constants import (
    CHANNEL_MEMBERS, CHANNEL_SEED_ARCHIVED, CHANNEL_SEED_NAMES,
    CHANNEL_SEED_PRIVATE, CHANNEL_SEED_TOPICS, SEED_REACTIONS,
    STANDUP_CHANNEL, STANDUP_POST_AT_EPOCH, STANDUP_TEXT,
)
from utils import (
    CHANNEL_ID_MAP, DM_ID_MAP, MSG_TS_MAP, USER_ID_MAP,
    api, api_get, api_get_paginated, cid, load_token_for_stack, log,
    require_token, save_state as _save_state, section, set_dry_run, set_token,
    uid, warn,
)
import utils

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Channel purposes are seed-only metadata (reset / verify don't care).
CHANNEL_SEED_PURPOSES: dict[str, str] = {
    "C001GENERAL":   "Company-wide",
    "C002RANDOM":    "Off-topic",
    "C003ENGBACK":   "Backend eng",
    "C004ENGFRONT":  "Frontend eng",
    "C005DESIGNRV":  "Design reviews",
    "C006QA":        "Bug triage",
    "C007MKT":       "Marketing / social",
    "C009INCIDENTS": "Incidents",
    "C010ANNOUNCE":  "Official announcements",
}

# DMs to open during seed (Scenario A: D03_MI_CL collapses since Miranda IS the agent).
DM_PAIRS: dict[str, list[str]] = {
    "D04_JA_CL": ["U02JARED", "U05CLAUDE"],
}

# Seed messages — every entry: (label, channel_key, author, days_ago, minor_seconds, text, thread_parent).
# Author is always U05CLAUDE in Scenario A; the column stays for grading-label fidelity.
MESSAGES: list[tuple[str, str, str, float, int, str, str | None]] = [
    # announcements
    ("M10c", "C001GENERAL",   "U05CLAUDE",  60,  0,   "Welcome to Hintas's Slack workspace.", None),
    ("M1b",  "C010ANNOUNCE",  "U05CLAUDE",  40,  0,   "Welcome Rhea to the team!", None),
    ("M1c",  "C010ANNOUNCE",  "U05CLAUDE",  25,  0,   "Reminder: studio all-hands Monday 11am.", None),
    ("M10d", "C001GENERAL",   "U05CLAUDE",  14,  0,   "FYI — alpha demo will be shared with press mid-May.", None),
    ("M1",   "C010ANNOUNCE",  "U05CLAUDE",  10,  0,   "Alpha build shipping 2026-05-10. Lock your features by 2026-04-25.", None),
    ("M1d",  "C010ANNOUNCE",  "U05CLAUDE",   4,  0,   "Press preview scheduled for 2026-05-03.", None),
    ("M1e",  "C010ANNOUNCE",  "U05CLAUDE",   1,  0,   "Reminder: code freeze discussion tomorrow in #eng-backend.", None),
    # eng-backend
    ("P1",   "C003ENGBACK",   "U05CLAUDE",  45,  0,   "Code freeze rules: no merges after Friday 5pm PT.", None),
    ("M2",   "C003ENGBACK",   "U05CLAUDE",   8,  0,   "Investigating crash in level-4 tile loader. Repro on macOS 14 only.", None),
    ("M3",   "C003ENGBACK",   "U05CLAUDE",   8,  300, "I can repro. It's the async streamer dropping a chunk when GPU memory is tight.", "M2"),
    ("M4",   "C003ENGBACK",   "U05CLAUDE",   8,  600, "Filed as BUG-247. Tagging the engineering team.", "M2"),
    ("M2b",  "C003ENGBACK",   "U05CLAUDE",   5,  0,   "Shipped fix for tile loader on branch `fix/tile-loader-async`. PR #12345.", None),
    ("M2c",  "C003ENGBACK",   "U05CLAUDE",   3,  0,   "Reminder: no merges after 5pm Friday.", None),
    # design-reviews
    ("M5",   "C005DESIGNRV",  "U05CLAUDE",   7,  0,   "Tomb-level 3 concept pass — five angles attached. Looking for crits on the lighting.", None),
    ("M5b",  "C005DESIGNRV",  "U05CLAUDE",   7,  1200,"The lighting in angle B is gorgeous. Angle E feels flat — try warming the rim.", None),
    ("M5c",  "C005DESIGNRV",  "U05CLAUDE",   6,  0,   "Agree — B and C are the keepers.", None),
    # qa-bugs
    ("M6b",  "C006QA",        "U05CLAUDE",  13,  0,   "BUG-246: main-menu flicker on launch (low).", None),
    ("M6c",  "C006QA",        "U05CLAUDE",  11,  0,   "BUG-245: audio desync after cutscene (medium).", None),
    ("M6",   "C006QA",        "U05CLAUDE",   6,  0,   "BUG-247: save-file corruption on macOS. Reproduces 4/10 runs. Blocker.", None),
    ("M6d",  "C006QA",        "U05CLAUDE",   4,  0,   "BUG-248: tomb-3 door collider blocks player on revisit (high).", None),
    ("M6e",  "C006QA",        "U05CLAUDE",   2,  0,   "Triaging the open BUG-### list at 2pm.", None),
    # launch-2026
    ("M7",   "C008LAUNCH",    "U05CLAUDE",   5,  0,   "Launch checklist v3 — owners: Lagoon/mkt, Miranda/brand, Jared/eng.", None),
    ("M7b",  "C008LAUNCH",    "U05CLAUDE",   2,  0,   "Marketing side is 60% ready — blockers in thread below.", None),
    ("M7c",  "C008LAUNCH",    "U05CLAUDE",   2,  1800,"Brand kit finalized. Legal approved the name.", None),
    ("M7d",  "C008LAUNCH",    "U05CLAUDE",   2,  3600,"Eng side has 2 open blockers: BUG-247 and the streaming cert.", None),
    # general
    ("M8",   "C001GENERAL",   "U05CLAUDE",   4,  0,   "Team Lisbon offsite: 2026-06-10 → 2026-06-14. RSVP in thread.", None),
    ("M9",   "C001GENERAL",   "U05CLAUDE",   4,  600, "Count me in.", "M8"),
    ("M10",  "C001GENERAL",   "U05CLAUDE",   4,  1200,"Can't make it — wedding that week.", "M8"),
    ("M10b", "C001GENERAL",   "U05CLAUDE",   4,  2400,"Yes! Booking flights now.", "M8"),
    # random
    ("M11b", "C002RANDOM",    "U05CLAUDE",  20,  0,   "Rec of the week: 'Annihilation' on rewatch hits different.", None),
    ("M11",  "C002RANDOM",    "U05CLAUDE",   3,  0,   "New :raider_skull: emoji is live. Use responsibly.", None),
    ("M17",  "C002RANDOM",    "U05CLAUDE",   2,  0,   "Finally shipped it :ship_it_raider:", None),
    # marketing
    ("M15b", "C007MKT",       "U05CLAUDE",  10,  0,   "Press list for review — spreadsheet in thread.", None),
    ("M15",  "C007MKT",       "U05CLAUDE",   4,  0,   "Trailer draft goes live Thursday. I need final copy by EOD Tuesday.", None),
    # DM accessible to the agent (prompt 53 targets D04_JA_CL for 'pacing' / 'boss fight')
    ("M13b", "D04_JA_CL",     "U05CLAUDE",   6,  0,   "Jared — can we chat about tomb-3 pacing when you have a sec? Also the boss fight feels rough.", None),
    ("M13c", "D04_JA_CL",     "U05CLAUDE",   6,  900, "Any time — ping me.", None),
]


# ---------------------------------------------------------------------------
# Step 0 — Verify token & identify Claude's user ID
# ---------------------------------------------------------------------------

def verify_auth() -> tuple[str, str, str]:
    """Returns (user_id, team_id, team_name)."""
    section("0. Verifying auth")
    data = api_get("auth.test")
    user_id = data["user_id"]
    team_id = data.get("team_id", "")
    team = data.get("team", "?")
    print(f"  Authenticated as: {data.get('user')} ({user_id}) in workspace: {team} ({team_id})")
    if team.lower() not in ("hintas", "tombra"):
        warn("Workspace name does not look like 'Hintas' — double-check you're hitting the right workspace.")
    return user_id, team_id, team


# ---------------------------------------------------------------------------
# Step 1 — Resolve / record user IDs from users.json
# ---------------------------------------------------------------------------

def _load_users() -> dict:
    local = os.path.join(SCRIPT_DIR, "users.local.json")
    sample = os.path.join(SCRIPT_DIR, "users.json")
    path = local if os.path.exists(local) else sample
    if not os.path.exists(path):
        raise SystemExit("users.json not found in platforms/slack/scripts/ — cannot resolve user emails")
    with open(path) as f:
        data = json.load(f)
    print(f"  [config] Loaded user records from {os.path.basename(path)}")
    return data


def resolve_users(users: dict) -> None:
    """
    Look up each user by email and populate USER_ID_MAP in place.
    """
    section("1. Resolving users")
    for logical_id, entry in users.items():
        email = entry["email"]
        try:
            data = api_get("users.lookupByEmail", {"email": email})
            real_id = data["user"]["id"]
            USER_ID_MAP[logical_id] = real_id
            log(f"{logical_id} → {real_id}  ({email})")
        except RuntimeError as e:
            warn(f"Could not resolve {email}: {e}")
            USER_ID_MAP[logical_id] = logical_id


# ---------------------------------------------------------------------------
# Step 2 — Create / verify channels
# ---------------------------------------------------------------------------

def get_existing_channels() -> dict[str, str]:
    """Returns {name: channel_id} for all channels (including archived)."""
    existing: dict[str, str] = {}
    for ch in api_get_paginated(
        "conversations.list",
        {"types": "public_channel,private_channel", "exclude_archived": False},
        "channels",
    ):
        existing[ch["name"]] = ch["id"]
    return existing


def create_channels():
    section("2. Creating channels")
    existing = get_existing_channels()

    for logical_id, name in CHANNEL_SEED_NAMES.items():
        if logical_id in CHANNEL_SEED_ARCHIVED:
            continue  # handled separately so we can also archive after creating

        is_private = CHANNEL_SEED_PRIVATE.get(logical_id, False)
        topic = CHANNEL_SEED_TOPICS.get(logical_id, "")
        purpose = CHANNEL_SEED_PURPOSES.get(logical_id, "")

        if name in existing:
            real_id = existing[name]
            CHANNEL_ID_MAP[logical_id] = real_id
            prefix = "🔒 " if is_private else ""
            log(f"{prefix}#{name} already exists → {real_id}")
        else:
            if utils.DRY_RUN:
                warn(f"#{name} MISSING (would create)")
                continue
            data = api("conversations.create", name=name, is_private=is_private)
            real_id = data["channel"]["id"]
            CHANNEL_ID_MAP[logical_id] = real_id
            log(f"Created {'private 🔒 ' if is_private else 'public '}#{name} → {real_id}")

        for method, kw in (("conversations.setTopic", {"topic": topic}),
                           ("conversations.setPurpose", {"purpose": purpose})):
            if not kw[next(iter(kw))]:
                continue
            try:
                api(method, channel=real_id, **kw)
            except RuntimeError:
                pass

    for logical_id in CHANNEL_SEED_ARCHIVED:
        name = CHANNEL_SEED_NAMES[logical_id]
        if name in existing:
            real_id = existing[name]
            CHANNEL_ID_MAP[logical_id] = real_id
            log(f"#{name} exists → {real_id}")
            continue
        if utils.DRY_RUN:
            warn(f"#{name} MISSING (would create + archive)")
            continue
        data = api("conversations.create", name=name, is_private=False)
        real_id = data["channel"]["id"]
        CHANNEL_ID_MAP[logical_id] = real_id
        api("conversations.archive", channel=real_id)
        log(f"Created and archived #{name} → {real_id}")


def invite_members():
    section("2b. Inviting channel members")
    for logical_ch_id, members_logical in CHANNEL_MEMBERS.items():
        real_ch_id = CHANNEL_ID_MAP.get(logical_ch_id)
        if not real_ch_id:
            warn(f"No real channel ID for {logical_ch_id}, skipping members")
            continue
        # Skip the agent itself (already a member after creation) and bots
        # (which can only join via OAuth).
        real_members = [uid(m) for m in members_logical if m not in ("U05CLAUDE", "U10BOT_CI")]
        if not real_members:
            continue
        if utils.DRY_RUN:
            log(f"Would invite {real_members} → {logical_ch_id}")
            continue
        try:
            api("conversations.invite", channel=real_ch_id, users=",".join(real_members))
            log(f"Invited {len(real_members)} members to {logical_ch_id}")
        except RuntimeError as e:
            if "already_in_channel" in str(e):
                log(f"Members already in {logical_ch_id}")
            else:
                warn(f"Invite to {logical_ch_id} failed: {e}")


# ---------------------------------------------------------------------------
# Step 3 — Open DMs
# ---------------------------------------------------------------------------

def open_dms():
    section("3. Opening DMs")
    for logical_id, (user_a, user_b) in DM_PAIRS.items():
        if utils.DRY_RUN:
            log(f"Would open DM {logical_id}")
            continue
        data = api("conversations.open", users=f"{uid(user_a)},{uid(user_b)}")
        real_id = data["channel"]["id"]
        DM_ID_MAP[logical_id] = real_id
        log(f"DM {logical_id} → {real_id}")


# ---------------------------------------------------------------------------
# Step 4 — Wipe + post seed messages
# ---------------------------------------------------------------------------

def wipe_agent_messages():
    """
    Delete every message in the seeded channels + DMs so we can re-post
    cleanly. Slack retains user-token chat.postMessage history forever, so
    re-running the seeder without wiping accumulates duplicates.
    """
    section("4a. Wiping existing agent messages in seeded channels")
    if utils.DRY_RUN:
        log("Would wipe agent messages in all seeded channels + DMs")
        return

    me = USER_ID_MAP.get("U05CLAUDE", "")
    for real_ch in list(CHANNEL_ID_MAP.values()) + list(DM_ID_MAP.values()):
        cursor = None
        deleted = 0
        while True:
            params = {"channel": real_ch, "limit": 200}
            if cursor:
                params["cursor"] = cursor
            try:
                data = api_get("conversations.history", params)
            except RuntimeError as e:
                warn(f"history failed for {real_ch}: {e}")
                break
            for msg in data.get("messages", []):
                if msg.get("user") != me and msg.get("bot_id") is None:
                    continue
                ts = msg.get("ts")
                if not ts:
                    continue
                try:
                    api("chat.delete", channel=real_ch, ts=ts)
                    deleted += 1
                    time.sleep(0.15)
                except RuntimeError as e:
                    if "message_not_found" not in str(e):
                        warn(f"delete {real_ch}/{ts} failed: {e}")
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        if deleted:
            log(f"Deleted {deleted} message(s) in {real_ch}")


def _resolve_message_channel(key: str) -> str:
    return CHANNEL_ID_MAP.get(key) or DM_ID_MAP.get(key) or key


def seed_messages():
    """
    Post seeded messages via chat.postMessage.

    NOTE: Slack does NOT allow backdating user-token messages. All messages
    will have today's real timestamp, NOT the offset timestamp. Graders must
    use benchmark_now relative logic. The numeric offset ordering IS preserved
    by posting in ascending-offset order (oldest first).
    """
    section("4. Seeding messages")

    for label, ch_key, author_logical, _days_ago, _minor_s, text, thread_parent in MESSAGES:
        real_ch = _resolve_message_channel(ch_key)
        thread_ts = MSG_TS_MAP.get(thread_parent) if thread_parent else None

        if utils.DRY_RUN:
            log(f"{label}: Would post in {ch_key} as {author_logical}: {text[:50]}...")
            MSG_TS_MAP[label] = f"PLACEHOLDER_{label}"
            continue

        kwargs: dict = {"channel": real_ch, "text": text, "username": author_logical}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        try:
            data = api("chat.postMessage", **kwargs)
            ts = data["ts"]
            MSG_TS_MAP[label] = ts
            log(f"{label}: posted ts={ts}  [{text[:50]}]")
            time.sleep(0.3)
        except RuntimeError as e:
            warn(f"{label}: failed — {e}")
            MSG_TS_MAP[label] = "ERROR"


# ---------------------------------------------------------------------------
# Step 5 — Reactions
# ---------------------------------------------------------------------------

def seed_reactions():
    section("5. Adding reactions")
    for msg_label, emoji, ch_logical in SEED_REACTIONS:
        ts = MSG_TS_MAP.get(msg_label)
        if not ts or ts.startswith("PLACEHOLDER") or ts == "ERROR":
            warn(f"Skipping reaction {emoji} on {msg_label} — no ts")
            continue
        real_ch = cid(ch_logical)
        if not real_ch:
            warn(f"No channel for {msg_label}")
            continue
        if utils.DRY_RUN:
            log(f"Would react :{emoji}: on {msg_label} as the agent")
            continue
        try:
            api("reactions.add", channel=real_ch, timestamp=ts, name=emoji)
            log(f":{emoji}: on {msg_label}")
            time.sleep(0.2)
        except RuntimeError as e:
            if "already_reacted" in str(e):
                log(f":{emoji}: already on {msg_label}")
            else:
                warn(f"Reaction failed: {e}")


# ---------------------------------------------------------------------------
# Step 6 — Scheduled message
# ---------------------------------------------------------------------------

def wipe_scheduled_messages():
    """Cancel every existing scheduled message before re-seeding."""
    section("6a. Wiping existing scheduled messages")
    if utils.DRY_RUN:
        log("Would cancel all existing scheduled messages")
        return
    try:
        data = api("chat.scheduledMessages.list")
    except RuntimeError as e:
        warn(f"scheduledMessages.list failed: {e}")
        return
    for sm in data.get("scheduled_messages", []):
        sm_id = sm.get("id")
        channel = sm.get("channel_id")
        if not sm_id or not channel:
            continue
        try:
            api("chat.deleteScheduledMessage", channel=channel, scheduled_message_id=sm_id)
            log(f"Cancelled scheduled msg {sm_id} in {channel}")
            time.sleep(0.15)
        except RuntimeError as e:
            warn(f"delete scheduled {sm_id} failed: {e}")


def seed_scheduled_messages():
    section("6. Scheduling messages")
    if utils.DRY_RUN:
        log(f"Would schedule '{STANDUP_TEXT}' in #marketing at {STANDUP_POST_AT_EPOCH}")
        return
    try:
        data = api("chat.scheduleMessage",
                   channel=cid(STANDUP_CHANNEL),
                   post_at=STANDUP_POST_AT_EPOCH,
                   text=STANDUP_TEXT)
        log(f"Scheduled standup message: {data.get('scheduled_message_id')}")
    except RuntimeError as e:
        if "time_in_past" in str(e):
            warn("Scheduled message post_at is in the past relative to NOW — "
                 "expected if running after 2026-04-19. Re-anchor benchmark_now to fix.")
        else:
            warn(f"Schedule failed: {e}")


# ---------------------------------------------------------------------------
# Step 7 — Reminder
# ---------------------------------------------------------------------------

def wipe_reminders():
    section("7a. Wiping existing reminders")
    if utils.DRY_RUN:
        log("Would delete all existing reminders")
        return
    try:
        data = api("reminders.list")
    except RuntimeError as e:
        warn(f"reminders.list failed: {e}")
        return
    for rem in data.get("reminders", []):
        rem_id = rem.get("id")
        if not rem_id:
            continue
        try:
            api("reminders.delete", reminder=rem_id)
            log(f"Deleted reminder {rem_id} ({rem.get('text','')[:40]})")
            time.sleep(0.15)
        except RuntimeError as e:
            warn(f"reminders.delete {rem_id} failed: {e}")


def seed_reminders():
    section("7. Creating agent's reminder")
    remind_at = int(BENCHMARK_NOW_EPOCH + 8 * 3600)
    if utils.DRY_RUN:
        log(f"Would create reminder 'Review tomb-3 crits' for the agent at {remind_at}")
        return
    try:
        api("reminders.add", text="Review tomb-3 crits", time=remind_at)
        log("Created agent's reminder: 'Review tomb-3 crits'")
    except RuntimeError as e:
        warn(f"reminders.add failed: {e}")


# ---------------------------------------------------------------------------
# Step 8 — Custom emoji note
# ---------------------------------------------------------------------------

def note_custom_emoji():
    section("8. Custom emoji")
    print(
        "  Custom emoji (:raider_skull:, :gold_gold:, :ship_it_raider:) must be\n"
        "  added via the Slack workspace admin UI at:\n"
        "    https://hintas.slack.com/customize/emoji\n"
        "  The Slack API does NOT expose an emoji.add endpoint to user tokens.\n"
        "  :ship_it_raider: should be configured as an alias of :ship_it:"
    )


# ---------------------------------------------------------------------------
# Step 9a — Capture ground-truth snapshot
# ---------------------------------------------------------------------------

def capture_ground_truth(claude_real_id: str) -> dict:
    """
    Snapshot every entity in the workspace after seeding completes.

    This is the benchmark's answer key. Prompts express success criteria as
    references into this snapshot (``seed.users.where(deleted=false AND
    is_bot=false)``, ``seed.channels.public.active``, etc.).
    """
    section("9a. Capturing workspace ground truth")
    truth: dict = {
        "workspace": {},
        "users": [], "channels": [], "dms": [], "mpims": [],
        "scheduled_messages": [], "reminders": [], "custom_emoji": [], "dnd": {},
        "ignore": {"user_ids": [], "channel_name_patterns": ["^all-"]},
    }

    # Workspace-level metadata (workspace_state §1)
    try:
        info = api_get("team.info").get("team", {}) or {}
        truth["workspace"] = {
            "id": info.get("id", ""),
            "name": info.get("name", ""),
            "domain": info.get("domain", ""),
            "email_domain": info.get("email_domain", ""),
            "enterprise_id": info.get("enterprise_id", ""),
            "enterprise_name": info.get("enterprise_name", ""),
        }
        log(f"Captured workspace metadata for {info.get('name')}")
    except RuntimeError as e:
        warn(f"team.info failed: {e}")

    # Users — every account, including deleted/bots/Slackbot
    try:
        for u in api_get_paginated("users.list", {}, "members"):
            profile = u.get("profile", {}) or {}
            truth["users"].append({
                "id": u.get("id"),
                "name": u.get("name"),
                "real_name": u.get("real_name", "") or profile.get("real_name", ""),
                "display_name": profile.get("display_name", ""),
                "email": profile.get("email", ""),
                "title": profile.get("title", ""),
                "is_admin": u.get("is_admin", False),
                "is_owner": u.get("is_owner", False),
                "is_primary_owner": u.get("is_primary_owner", False),
                "is_bot": u.get("is_bot", False),
                "is_app_user": u.get("is_app_user", False),
                "is_restricted": u.get("is_restricted", False),
                "is_ultra_restricted": u.get("is_ultra_restricted", False),
                "deleted": u.get("deleted", False),
                "tz": u.get("tz", ""),
            })
        log(f"Captured {len(truth['users'])} users")
    except RuntimeError as e:
        warn(f"users.list failed during ground-truth capture: {e}")

    seed_real_ids = {real for real in USER_ID_MAP.values() if real}
    for u in truth["users"]:
        uid_real = u.get("id", "")
        if uid_real == "USLACKBOT":
            truth["ignore"]["user_ids"].append(uid_real)
        elif u.get("is_primary_owner") and uid_real != claude_real_id:
            truth["ignore"]["user_ids"].append(uid_real)
        elif (uid_real and uid_real not in seed_real_ids
              and not u.get("is_bot") and not u.get("deleted")
              and uid_real != claude_real_id):
            truth["ignore"]["user_ids"].append(uid_real)

    # Channels (public + private, archived included)
    try:
        chans = api_get_paginated(
            "conversations.list",
            {"types": "public_channel,private_channel", "exclude_archived": False},
            "channels",
        )
        for ch in chans:
            members: list[str] = []
            try:
                members = api_get_paginated(
                    "conversations.members", {"channel": ch["id"]}, "members",
                )
            except RuntimeError as e:
                warn(f"conversations.members failed for #{ch.get('name')}: {e}")
            truth["channels"].append({
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False),
                "is_archived": ch.get("is_archived", False),
                "is_general": ch.get("is_general", False),
                "topic": (ch.get("topic", {}) or {}).get("value", ""),
                "purpose": (ch.get("purpose", {}) or {}).get("value", ""),
                "creator": ch.get("creator", ""),
                "created": ch.get("created"),
                "members": members,
                "num_members": ch.get("num_members", len(members)),
            })
        log(f"Captured {len(truth['channels'])} channels (incl. archived)")
    except RuntimeError as e:
        warn(f"conversations.list (channels) failed: {e}")

    # DMs and MPIMs
    try:
        for ch in api_get_paginated("conversations.list", {"types": "im,mpim"}, "channels"):
            entry: dict = {"id": ch.get("id")}
            if ch.get("is_im"):
                entry["user"] = ch.get("user", "")
                entry["is_user_deleted"] = ch.get("is_user_deleted", False)
                truth["dms"].append(entry)
            elif ch.get("is_mpim"):
                try:
                    entry["members"] = api_get_paginated(
                        "conversations.members", {"channel": ch["id"]}, "members",
                    )
                except RuntimeError:
                    entry["members"] = []
                truth["mpims"].append(entry)
        log(f"Captured {len(truth['dms'])} DMs and {len(truth['mpims'])} MPIMs")
    except RuntimeError as e:
        warn(f"conversations.list (im/mpim) failed: {e}")

    # Scheduled messages
    try:
        for m in api_get_paginated(
            "chat.scheduledMessages.list", {}, "scheduled_messages"
        ):
            truth["scheduled_messages"].append({
                "id": m.get("id"),
                "channel_id": m.get("channel_id"),
                "user_id": m.get("user_id"),
                "post_at": m.get("post_at"),
                "date_created": m.get("date_created"),
                "text": m.get("text", ""),
            })
        log(f"Captured {len(truth['scheduled_messages'])} scheduled messages")
    except RuntimeError as e:
        warn(f"chat.scheduledMessages.list failed: {e}")

    # Reminders (only the agent's own reminders are visible to its token)
    try:
        data = api_get("reminders.list")
        for r in data.get("reminders", []):
            truth["reminders"].append({
                "id": r.get("id"),
                "creator": r.get("creator"),
                "user": r.get("user"),
                "text": r.get("text", ""),
                "time": r.get("time"),
                "recurring": r.get("recurring", False),
                "complete_ts": r.get("complete_ts", 0),
            })
        log(f"Captured {len(truth['reminders'])} reminders (agent-visible only)")
    except RuntimeError as e:
        warn(f"reminders.list failed: {e}")

    # Custom emoji
    try:
        data = api_get("emoji.list")
        emoji_map = data.get("emoji", {}) or {}
        for name, url in emoji_map.items():
            truth["custom_emoji"].append({
                "name": name,
                "url_or_alias": url,
                "is_alias": isinstance(url, str) and url.startswith("alias:"),
            })
        log(f"Captured {len(truth['custom_emoji'])} custom emoji")
    except RuntimeError as e:
        warn(f"emoji.list failed: {e}")

    # DND state for the seed roster
    if seed_real_ids:
        try:
            data = api_get("dnd.teamInfo", {"users": ",".join(sorted(seed_real_ids))})
            truth["dnd"] = data.get("users", {})
            log(f"Captured DND state for {len(truth['dnd'])} users")
        except RuntimeError as e:
            warn(f"dnd.teamInfo failed: {e}")

    return truth


# ---------------------------------------------------------------------------
# Step 9 — Save state for reset script and graders
# ---------------------------------------------------------------------------

def save_workspace_state(team_id: str, team_name: str, claude_real_id: str,
                         state_path: str | None = None,
                         stack: str | None = None) -> None:
    section("9. Saving workspace state")
    truth = capture_ground_truth(claude_real_id)
    payload = {
        "team_id": team_id,
        "team_name": team_name,
        "user_id_map": dict(USER_ID_MAP),
        "channel_id_map": dict(CHANNEL_ID_MAP),
        "dm_id_map": dict(DM_ID_MAP),
        "msg_ts_map": dict(MSG_TS_MAP),
        "benchmark_now_epoch": BENCHMARK_NOW_EPOCH,
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "ground_truth": truth,
    }
    if not state_path:
        if not stack:
            raise RuntimeError("Must pass --stack or --state-file to determine where to write workspace state.")
        state_path = os.path.join(SCRIPT_DIR, f"workspace_state_{stack}.json")
    _save_state(state_path, payload)
    print(f"  Saved → {state_path}")
    print("  reset_workspace.py will auto-load this file when run against the same workspace.")
    print("  Graders read state['ground_truth'] as the answer key for prompt verdicts.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed Hintas benchmark workspace")
    parser.add_argument("--verify", "--dry-run", dest="verify", action="store_true",
                        help="Dry-run: report missing items without creating")
    parser.add_argument("--token", help="Slack user token (overrides SLACK_TOKEN env var)")
    parser.add_argument("--state-file",
                        help="Explicit path for the workspace state file (overrides --stack).")
    parser.add_argument("--stack",
                        help="Stack name (e.g. slack, hintas). Writes workspace_state_<stack>.json "
                             "and resolves the auth token from the manifest's token_env.")
    args = parser.parse_args()

    set_dry_run(args.verify)
    if args.token:
        set_token(args.token)
    elif args.stack:
        set_token(load_token_for_stack(args.stack))
    require_token()

    print(f"\n{'=' * 60}")
    print("  Hintas Benchmark — Workspace Seeder")
    print(f"  Mode: {'DRY RUN (verify only)' if utils.DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'=' * 60}")

    users = _load_users()
    claude_real_id, team_id, team_name = verify_auth()
    resolve_users(users)
    create_channels()
    invite_members()
    open_dms()
    wipe_agent_messages()
    seed_messages()
    seed_reactions()
    wipe_scheduled_messages()
    seed_scheduled_messages()
    wipe_reminders()
    seed_reminders()
    note_custom_emoji()

    if not utils.DRY_RUN:
        save_workspace_state(team_id, team_name, claude_real_id, args.state_file, args.stack)

    print(f"\n{'=' * 60}")
    print(f"  {'VERIFY COMPLETE' if utils.DRY_RUN else 'SEED COMPLETE'}")
    print("  Next step: run reset_workspace.py before each prompt run.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
