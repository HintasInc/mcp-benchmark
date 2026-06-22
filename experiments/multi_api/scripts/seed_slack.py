#!/usr/bin/env python3
"""
seed_slack.py  —  Multi-API Benchmark, Slack surface

Seeds the Slack surface of the multi-API benchmark workspace: resolves the
persona cast, creates (or reuses) the five seed channels, restores their
memberships, and posts the canonical seed messages (incident thread +
general/announcement chatter). The resulting ``workspace_state_slack.json`` is
the answer key both ``reset_slack.py`` and the graders read back.

Standalone: this script does NOT import the slack experiment's utils. The Slack
HTTP wrappers (``api`` / ``api_get`` / ``api_get_paginated``) are inlined below
and gate mutating calls on the module-level ``DRY_RUN`` (GET/read calls always
run, exactly like the reference). Generic plumbing — console output, persona
cast, state I/O — comes from the shared ``common`` module.

Token:
    export SLACK_TOKEN=xoxp-...          # the agent's user token (Miranda)
    python seed_slack.py                 # full seed
    python seed_slack.py --verify        # dry-run: report what's missing

Optional multi-author support: if ``slack_tokens.local.json`` exists in this
dir mapping ``{logical_id: "xoxp-..."}``, a seed message is posted using that
persona's own token (Slack ignores the ``username`` param on user tokens, so a
token-swap is the only faithful way to author as someone else). Regardless of
who actually posted, the INTENDED ``author_logical`` is recorded in
``msg_ts_map`` and ``ground_truth`` so graders can reason about authorship.

NOTE: Slack does NOT allow backdating user-token messages. Every message gets
today's real timestamp. Ordering is preserved by posting oldest-first, and
"last N days" windows are satisfied because seed time ≈ benchmark_now.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

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

# One source of truth for dry-run, shared with common (whose helpers gate on its
# own DRY_RUN). The inline api wrappers below check THIS module-level flag.
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
# Fixture
# ---------------------------------------------------------------------------

# Logical channel key → channel name. All public, created if absent, reused by name.
CHANNEL_SEED_NAMES: dict[str, str] = {
    "C_GENERAL":   "general",
    "C_ANNOUNCE":  "announcements",
    "C_SUPPORT":   "support",
    "C_INCIDENTS": "incidents",
    "C_LEADS":     "leads",
}

# Seed messages — (label, channel_logical, author_logical, text, thread_parent_label).
# Posted oldest-first; thread replies hang off the resolved parent label's ts.
MESSAGES: list[tuple[str, str, str, str, str | None]] = [
    ("M_INC1", "C_INCIDENTS", "U02JARED",
     "DB connection pool exhausted — we're seeing elevated 500s on the API since 14:00. Investigating.", None),
    ("M_INC2", "C_INCIDENTS", "U03PINKMAN",
     "Pool is maxed at 20. Connections aren't being released after the 13:50 migration.", "M_INC1"),
    ("M_INC3", "C_INCIDENTS", "U04LAGOON",
     "Rolled back the migration. Pool is draining now — 12/20 in use and falling.", "M_INC1"),
    ("M_INC4", "C_INCIDENTS", "U02JARED",
     "Confirmed recovered as of 14:40. 500s are back to baseline. I'll write up the postmortem.", "M_INC1"),
    ("M_GEN_PRICING", "C_GENERAL", "U04LAGOON",
     "Pricing page is ready for review.", None),
    ("M_GEN1", "C_GENERAL", "U01MIRANDA",
     "Reminder: all-hands moved to Friday 3pm.", None),
    ("M_GEN2", "C_GENERAL", "U06DEVON",
     "Staging deploy is green again — unblock your merges.", None),
    ("M_ANN1", "C_ANNOUNCE", "U02JARED",
     "We shipped the v3.9 hotfix this morning — thanks all.", None),
    ("M_ANN2", "C_ANNOUNCE", "U03PINKMAN",
     "Reminder: code freeze starts Thursday EOD.", None),
    ("M_ANN3", "C_ANNOUNCE", "U04LAGOON",
     "Design-review slots for next week are open.", None),
]

# State maps populated in place across the seed steps.
USER_ID_MAP: dict[str, str] = {}
CHANNEL_ID_MAP: dict[str, str] = {}
DM_ID_MAP: dict[str, str] = {}
# label → {ts, channel_logical, author_logical, thread_parent}
MSG_TS_MAP: dict[str, dict] = {}

AGENT = agent_logical_id()  # U01MIRANDA (Miranda is the acting agent)
# The real Slack user id the token authenticates as (set in main() from
# auth.test). The token owner is already a member of channels they create and
# cannot be invited to one (cant_invite_self), so they're excluded from invites
# regardless of which persona's account the token belongs to.
AGENT_REAL_ID = ""

# Optional per-persona author tokens (logical_id → xoxp-...).
AUTHOR_TOKENS: dict[str, str] = {}


def _channel_memberships() -> dict[str, list[str]]:
    """Logical channel key → seed member logical ids (the agent is excluded; it
    is already a member as the channel creator)."""
    everyone = team_distribution()  # all 8 humans (excludes agent + candidate)
    return {
        "C_GENERAL":   everyone,
        "C_ANNOUNCE":  everyone,
        "C_SUPPORT":   everyone,
        "C_INCIDENTS": everyone,
        "C_LEADS":     leads(),  # 3
    }


def uid(logical: str) -> str:
    """Resolve a logical user id to its real Slack id (falls back to logical)."""
    return USER_ID_MAP.get(logical, logical)


def cid(logical: str) -> str:
    """Resolve a logical channel key to its real Slack id (falls back to logical)."""
    return CHANNEL_ID_MAP.get(logical, logical)


def load_author_tokens() -> None:
    """Load optional ``slack_tokens.local.json`` ({logical_id: xoxp-...})."""
    path = os.path.join(SCRIPT_DIR, "slack_tokens.local.json")
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        warn(f"Could not read slack_tokens.local.json: {e}")
        return
    AUTHOR_TOKENS.clear()
    AUTHOR_TOKENS.update({k: v for k, v in data.items() if isinstance(v, str) and v})
    if AUTHOR_TOKENS:
        log(f"[config] Loaded {len(AUTHOR_TOKENS)} author token(s) for multi-author seeding")


# ---------------------------------------------------------------------------
# Step 0 — Verify token & identify the agent's user ID
# ---------------------------------------------------------------------------

def verify_auth() -> tuple[str, str, str]:
    """Returns (user_id, team_id, team_name)."""
    section("0. Verifying auth")
    data = api_get("auth.test")
    user_id = data["user_id"]
    team_id = data.get("team_id", "")
    team = data.get("team", "?")
    print(f"  Authenticated as: {data.get('user')} ({user_id}) in workspace: {team} ({team_id})")
    return user_id, team_id, team


# ---------------------------------------------------------------------------
# Step 1 — Resolve persona user IDs by email
# ---------------------------------------------------------------------------

def resolve_users(users: dict) -> None:
    """Look up each persona by email and populate USER_ID_MAP in place."""
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


def create_channels() -> None:
    section("2. Creating channels")
    existing = get_existing_channels()

    for logical_id, name in CHANNEL_SEED_NAMES.items():
        if name in existing:
            real_id = existing[name]
            CHANNEL_ID_MAP[logical_id] = real_id
            log(f"#{name} already exists → {real_id}")
            continue
        if DRY_RUN:
            warn(f"#{name} MISSING (would create)")
            continue
        try:
            data = api("conversations.create", name=name, is_private=False)
            real_id = data["channel"]["id"]
            CHANNEL_ID_MAP[logical_id] = real_id
            log(f"Created public #{name} → {real_id}")
        except RuntimeError as e:
            # Lost a create race or it was archived under a different listing.
            if "name_taken" in str(e) and name in get_existing_channels():
                real_id = get_existing_channels()[name]
                CHANNEL_ID_MAP[logical_id] = real_id
                log(f"#{name} exists (name_taken) → {real_id}")
            else:
                warn(f"Create #{name} failed: {e}")


def invite_members() -> None:
    section("2b. Inviting channel members")
    memberships = _channel_memberships()
    for logical_ch_id, members_logical in memberships.items():
        real_ch_id = CHANNEL_ID_MAP.get(logical_ch_id)
        if not real_ch_id:
            warn(f"No real channel ID for {logical_ch_id}, skipping members")
            continue
        # Skip the logical agent, the real token owner (can't invite self),
        # and any unresolved id.
        real_members = [uid(m) for m in members_logical
                        if m != AGENT and USER_ID_MAP.get(m) and USER_ID_MAP[m] != m
                        and uid(m) != AGENT_REAL_ID]
        if not real_members:
            continue
        if DRY_RUN:
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
# Step 3 — Wipe + post seed messages
# ---------------------------------------------------------------------------

def _seed_author_real_ids() -> set[str]:
    """Real ids whose messages the wipe should remove: the agent plus any
    persona we have an author token for (those can post real-authored seeds)."""
    ids = {USER_ID_MAP.get(AGENT, "")}
    for lid in AUTHOR_TOKENS:
        ids.add(USER_ID_MAP.get(lid, ""))
    return {i for i in ids if i}


def wipe_seed_messages() -> None:
    """
    Delete prior agent (and seed author-token) messages in the seed channels so
    reruns don't duplicate. Slack retains user-token chat.postMessage history
    forever, so re-running without wiping accumulates duplicates.
    """
    section("3a. Wiping prior seed messages in seed channels")
    if DRY_RUN:
        log("Would wipe agent / seed-author messages in all seed channels")
        return

    seed_authors = _seed_author_real_ids()
    for real_ch in list(CHANNEL_ID_MAP.values()):
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
                author = msg.get("user")
                if author not in seed_authors and msg.get("bot_id") is None:
                    continue
                ts = msg.get("ts")
                if not ts:
                    continue
                try:
                    api("chat.delete", channel=real_ch, ts=ts)
                    deleted += 1
                    time.sleep(0.15)
                except RuntimeError as e:
                    if "message_not_found" not in str(e) and "cant_delete_message" not in str(e):
                        warn(f"delete {real_ch}/{ts} failed: {e}")
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        if deleted:
            log(f"Deleted {deleted} message(s) in {real_ch}")


def _post_message(real_ch: str, text: str, author_logical: str, thread_ts: str | None) -> dict:
    """
    Post one message. If an author token exists for ``author_logical``, post as
    that persona by swapping HEADERS for this single call (Slack ignores the
    username param on user tokens, so a token-swap is the only faithful path).
    Otherwise post as the agent.
    """
    kwargs: dict = {"channel": real_ch, "text": text}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts

    author_token = AUTHOR_TOKENS.get(author_logical)
    if author_token and author_logical != AGENT:
        saved = HEADERS["Authorization"]
        HEADERS["Authorization"] = f"Bearer {author_token}"
        try:
            return api("chat.postMessage", **kwargs)
        finally:
            HEADERS["Authorization"] = saved
    return api("chat.postMessage", **kwargs)


def seed_messages() -> None:
    """
    Post seeded messages oldest-first via chat.postMessage.

    NOTE: Slack does NOT allow backdating user-token messages — every message
    gets today's real timestamp. Ordering is preserved by posting in list order
    (oldest first); "last N days" windows hold because seed time ≈ benchmark_now.
    """
    section("3. Seeding messages")

    for label, ch_logical, author_logical, text, thread_parent in MESSAGES:
        real_ch = cid(ch_logical)
        parent = MSG_TS_MAP.get(thread_parent) if thread_parent else None
        thread_ts = parent["ts"] if parent else None

        if DRY_RUN:
            log(f"{label}: Would post in {ch_logical} as {author_logical}: {text[:50]}...")
            MSG_TS_MAP[label] = {
                "ts": f"PLACEHOLDER_{label}",
                "channel_logical": ch_logical,
                "author_logical": author_logical,
                "thread_parent": thread_parent,
            }
            continue

        try:
            data = _post_message(real_ch, text, author_logical, thread_ts)
            ts = data["ts"]
            MSG_TS_MAP[label] = {
                "ts": ts,
                "channel_logical": ch_logical,
                "author_logical": author_logical,
                "thread_parent": thread_parent,
            }
            log(f"{label}: posted ts={ts} as {author_logical}  [{text[:50]}]")
            time.sleep(0.3)
        except RuntimeError as e:
            warn(f"{label}: failed — {e}")
            MSG_TS_MAP[label] = {
                "ts": "ERROR",
                "channel_logical": ch_logical,
                "author_logical": author_logical,
                "thread_parent": thread_parent,
            }


# ---------------------------------------------------------------------------
# Step 4 — Capture ground-truth snapshot
# ---------------------------------------------------------------------------

def capture_ground_truth(agent_real_id: str) -> dict:
    """
    Snapshot the workspace after seeding — the benchmark's answer key. Lighter
    than the single-API capture: workspace, users, the seed channels, DMs, and
    the seed messages with intended authorship.
    """
    section("4. Capturing ground truth")
    truth: dict = {
        "workspace": {},
        "users": [], "channels": [], "dms": [], "seed_messages": [],
        "ignore": {"user_ids": [], "channel_name_patterns": ["^all-"]},
        "seed_channel_ids": [cid(lid) for lid in CHANNEL_SEED_NAMES if cid(lid)],
    }

    # Workspace metadata
    try:
        info = api_get("team.info").get("team", {}) or {}
        truth["workspace"] = {
            "id": info.get("id", ""),
            "name": info.get("name", ""),
            "domain": info.get("domain", ""),
        }
        log(f"Captured workspace metadata for {info.get('name')}")
    except RuntimeError as e:
        warn(f"team.info failed: {e}")

    # Users — every account
    try:
        for u in api_get_paginated("users.list", {}, "members"):
            profile = u.get("profile", {}) or {}
            truth["users"].append({
                "id": u.get("id"),
                "name": u.get("name"),
                "real_name": u.get("real_name", "") or profile.get("real_name", ""),
                "email": profile.get("email", ""),
                "is_bot": u.get("is_bot", False),
                "deleted": u.get("deleted", False),
            })
        log(f"Captured {len(truth['users'])} users")
    except RuntimeError as e:
        warn(f"users.list failed during ground-truth capture: {e}")

    # Channels — the seed channels only, with current membership
    seed_real_ids = {cid(lid) for lid in CHANNEL_SEED_NAMES if cid(lid)}
    try:
        chans = api_get_paginated(
            "conversations.list",
            {"types": "public_channel,private_channel", "exclude_archived": False},
            "channels",
        )
        for ch in chans:
            if ch.get("id") not in seed_real_ids:
                continue
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
                "topic": (ch.get("topic", {}) or {}).get("value", ""),
                "creator": ch.get("creator", ""),
                "members": members,
            })
        log(f"Captured {len(truth['channels'])} seed channels")
    except RuntimeError as e:
        warn(f"conversations.list (channels) failed: {e}")

    # DMs visible to the agent
    try:
        for ch in api_get_paginated("conversations.list", {"types": "im"}, "channels"):
            truth["dms"].append({
                "id": ch.get("id"),
                "user": ch.get("user", ""),
                "is_user_deleted": ch.get("is_user_deleted", False),
            })
        log(f"Captured {len(truth['dms'])} DMs")
    except RuntimeError as e:
        warn(f"conversations.list (im) failed: {e}")

    # Seed messages — intended authorship, recorded regardless of actual poster
    for label, entry in MSG_TS_MAP.items():
        ch_logical = entry.get("channel_logical")
        parent = entry.get("thread_parent")
        parent_ts = MSG_TS_MAP.get(parent, {}).get("ts") if parent else None
        truth["seed_messages"].append({
            "label": label,
            "channel_id": cid(ch_logical) if ch_logical else "",
            "author_logical": entry.get("author_logical"),
            "ts": entry.get("ts"),
            "thread_ts": parent_ts,
        })
    log(f"Captured {len(truth['seed_messages'])} seed messages")

    return truth


# ---------------------------------------------------------------------------
# Step 5 — Save state
# ---------------------------------------------------------------------------

def save_workspace_state(team_id: str, team_name: str, agent_real_id: str,
                         state_path: str) -> None:
    section("5. Saving workspace state")
    truth = capture_ground_truth(agent_real_id)
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
    save_state(state_path, payload)
    print("  reset_slack.py will auto-load this file when run against the same workspace.")
    print("  Graders read state['ground_truth'] as the answer key for prompt verdicts.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description="Seed the multi-API benchmark Slack surface")
    parser.add_argument("--verify", "--dry-run", dest="verify", action="store_true",
                        help="Dry-run: report missing items without mutating the workspace")
    parser.add_argument("--token", help="Slack user token (overrides BASELINE_/HINTAS_SLACK_TOKEN)")
    parser.add_argument("--state-file",
                        help="Explicit path for the workspace state file (overrides the default).")
    add_stack_arg(parser)
    args = parser.parse_args()

    global AGENT_REAL_ID
    DRY_RUN = args.verify
    set_dry_run(args.verify)
    set_token(args.token or stack_env(args.stack, "SLACK_TOKEN"))
    require_token(f"{'BASELINE_' if args.stack == 'baseline' else 'HINTAS_'}SLACK_TOKEN")

    print(f"\n{'=' * 60}")
    print("  Multi-API Benchmark — Slack Seeder")
    print(f"  Mode: {'DRY RUN (verify only)' if DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'=' * 60}")

    state_path = resolve_state_file(args.state_file, "slack", args.stack)

    users = load_users()
    build_substitution_map(email_of(AGENT))
    load_author_tokens()
    agent_real_id, team_id, team_name = verify_auth()
    AGENT_REAL_ID = agent_real_id
    resolve_users(users)
    create_channels()
    invite_members()
    wipe_seed_messages()
    seed_messages()

    if not DRY_RUN:
        save_workspace_state(team_id, team_name, agent_real_id, state_path)

    print(f"\n{'=' * 60}")
    print(f"  {'VERIFY COMPLETE' if DRY_RUN else 'SEED COMPLETE'}")
    print("  Next step: run reset_slack.py before each prompt run.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
