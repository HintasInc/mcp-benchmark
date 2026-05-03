#!/usr/bin/env python3
"""
reset_workspace.py  —  Hintas Slack Benchmark v4 (Scenario A)

Resets the workspace back to the exact v4 snapshot defined in workspace_state.md
BEFORE every prompt run. This script undoes any mutations a prompt may have made.

Scenario A (single-token): all seeded content is agent-authored (U05CLAUDE,
display name "Miranda"). Reset targets only the agent's own state — messages,
reactions, scheduled messages, DND snooze, reminders.

Usage:
    export SLACK_TOKEN=xoxp-...
    python reset_workspace.py                          # full reset
    python reset_workspace.py --prompt-id 22          # reset after a specific prompt
    python reset_workspace.py --dry-run                # show what would change
    python reset_workspace.py --state-file path.json  # force a specific state file

Loads the workspace state file produced by seed_workspace.py. The path is
resolved via ``--stack`` (writing ``workspace_state_<stack>.json``) or
``--state-file`` (which the orchestrator passes from the manifest's
``state_file_template``).

What this resets:
  ✅ Channel names (renames back if a prompt renamed them)
  ✅ Channel topics (restores seed topics)
  ✅ Channel archive state (#old-playtest-2025 → archived; others → unarchived)
  ✅ Channel memberships (restores kicked members, removes extras)
  ✅ Agent's prompt-created messages (deletes anything outside the seed set)
  ✅ Agent's reactions (removes extras; re-adds seed reactions)
  ✅ Scheduled messages (cancels agent-created, re-seeds the Monday standup)
  ✅ Agent's DND snooze (ends any active snooze)
  ✅ Non-seed channels (archives anything outside the seed set; Slack
       won't permit deletion on non-Enterprise plans, so archive is the
       fairness equivalent.)

What this CANNOT reset automatically (manual steps noted):
  ⚠️  Seeded message ts values — they were posted at real wall-clock time
  ⚠️  Custom emoji — cannot be deleted/added via user token API
  ⚠️  File uploads — files.delete is not in standard user token scope
  ⚠️  Pins — restored only when pins:write is granted to the seed token
"""
from __future__ import annotations

import argparse
import re
import time

from constants import (
    CHANNEL_MEMBERS, CHANNEL_SEED_NAMES, CHANNEL_SEED_TOPICS,
    IGNORE_NAME_PATTERNS, SEED_REACTIONS, STANDUP_CHANNEL,
    STANDUP_POST_AT_EPOCH, STANDUP_TEXT,
)
from utils import (
    CHANNEL_ID_MAP, DM_ID_MAP, MSG_TS_MAP,
    api, api_get, cid, load_state, load_token_for_stack, log, require_token,
    resolve_state_file, section, set_dry_run, set_token, uid, warn,
)
import utils

# ---------------------------------------------------------------------------
# 1. Channel names & topics
# ---------------------------------------------------------------------------

def reset_channel_names_and_topics():
    section("1. Resetting channel names & topics")
    for logical_id, seed_name in CHANNEL_SEED_NAMES.items():
        real_id = cid(logical_id)
        if not real_id:
            warn(f"No ID for {logical_id}")
            continue
        try:
            info = api_get("conversations.info", {"channel": real_id})
            ch = info["channel"]
            current_name = ch.get("name", "")
            current_topic = ch.get("topic", {}).get("value", "")
            archived = ch.get("is_archived", False)

            # Rename if drifted (e.g. prompt 26 renames eng-frontend)
            if current_name != seed_name:
                if utils.DRY_RUN:
                    warn(f"#{current_name} should be '{seed_name}' (would rename)")
                else:
                    # Unarchive first if needed (can't rename archived channels)
                    if archived:
                        api("conversations.unarchive", channel=real_id)
                    api("conversations.rename", channel=real_id, name=seed_name)
                    log(f"Renamed #{current_name} → #{seed_name}")

            seed_topic = CHANNEL_SEED_TOPICS.get(logical_id, "")
            if current_topic != seed_topic:
                if utils.DRY_RUN:
                    warn(f"#{seed_name} topic drifted (would restore)")
                else:
                    api("conversations.setTopic", channel=real_id, topic=seed_topic)
                    log(f"Restored topic for #{seed_name}")
            else:
                log(f"#{seed_name} name+topic OK")

        except RuntimeError as e:
            warn(f"Could not check {logical_id}: {e}")


# ---------------------------------------------------------------------------
# 2. Archive state
# ---------------------------------------------------------------------------

def reset_archive_state():
    section("2. Resetting archive state")
    # #old-playtest-2025 must be archived; all others must be active.
    for logical_id in CHANNEL_SEED_NAMES:
        real_id = cid(logical_id)
        if not real_id:
            continue
        should_be_archived = (logical_id == "C011OLDPLAYTEST")
        try:
            info = api_get("conversations.info", {"channel": real_id})
            is_archived = info["channel"].get("is_archived", False)
            name = CHANNEL_SEED_NAMES[logical_id]
            if is_archived and not should_be_archived:
                if utils.DRY_RUN:
                    warn(f"#{name} is archived but should be active (would unarchive)")
                else:
                    api("conversations.unarchive", channel=real_id)
                    log(f"Unarchived #{name}")
            elif not is_archived and should_be_archived:
                if utils.DRY_RUN:
                    warn(f"#{name} is active but should be archived (would archive)")
                else:
                    api("conversations.archive", channel=real_id)
                    log(f"Archived #{name}")
            else:
                log(f"#{name} archive state OK ({'archived' if is_archived else 'active'})")
        except RuntimeError as e:
            warn(f"Archive check failed for {logical_id}: {e}")


# ---------------------------------------------------------------------------
# 3. Channel memberships
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


def reset_memberships():
    section("3. Resetting channel memberships")
    claude_real = uid("U05CLAUDE")
    for logical_ch_id, logical_members in CHANNEL_MEMBERS.items():
        real_ch = cid(logical_ch_id)
        if not real_ch:
            warn(f"No real ID for {logical_ch_id}")
            continue

        if logical_ch_id == "C011OLDPLAYTEST":
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
            to_add_filtered = [m for m in to_add if m != claude_real]
            if to_add_filtered:
                if utils.DRY_RUN:
                    warn(f"#{name}: would add {to_add_filtered}")
                else:
                    try:
                        api("conversations.invite", channel=real_ch, users=",".join(to_add_filtered))
                        log(f"#{name}: added {len(to_add_filtered)} members")
                    except RuntimeError as e:
                        warn(f"#{name} invite failed: {e}")

        to_remove = current_members - seed_real_ids
        for m in to_remove:
            if m == claude_real:
                continue
            if utils.DRY_RUN:
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
# 4. Delete agent's prompt-created messages
# ---------------------------------------------------------------------------

def delete_claude_messages():
    """
    Delete any messages posted by the agent that are NOT in MSG_TS_MAP (i.e.
    created during a prompt). Scans all channels the agent has access to.
    """
    section("4. Removing agent's prompt-created messages")
    claude_real = uid("U05CLAUDE")
    seed_ts_set = set(MSG_TS_MAP.values())

    all_channels = list(CHANNEL_ID_MAP.values()) + list(DM_ID_MAP.values())

    for real_ch in all_channels:
        try:
            data = api_get("conversations.history", {"channel": real_ch, "limit": 50})
        except RuntimeError:
            continue
        for msg in data.get("messages", []):
            if msg.get("user") != claude_real:
                continue
            ts = msg.get("ts")
            if ts in seed_ts_set:
                continue
            if msg.get("subtype") in ("bot_message", "channel_join", "channel_leave"):
                continue
            if utils.DRY_RUN:
                warn(f"Would delete agent's message ts={ts} in {real_ch}: {msg.get('text','')[:50]}")
            else:
                try:
                    api("chat.delete", channel=real_ch, ts=ts)
                    log(f"Deleted agent msg ts={ts} in {real_ch}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    warn(f"Delete failed {ts}: {e}")


# ---------------------------------------------------------------------------
# 5. Reset reactions
# ---------------------------------------------------------------------------

def reset_reactions():
    """
    For each seeded reaction (always by the agent in Scenario A), restore the
    seed state and strip any extra agent reactions added during a prompt run.
    """
    section("5. Resetting reactions")
    claude_real = uid("U05CLAUDE")

    for msg_label, emoji, ch_logical in SEED_REACTIONS:
        ts = MSG_TS_MAP.get(msg_label)
        real_ch = cid(ch_logical)

        if not ts or ts.startswith("PLACEHOLDER") or ts == "ERROR":
            warn(f"No ts for {msg_label}, skipping reaction reset")
            continue

        try:
            react_data = api_get("reactions.get", {"channel": real_ch, "timestamp": ts, "full": True})
            current_reactions = {
                r["name"]: list(r.get("users", []))
                for r in react_data.get("message", {}).get("reactions", [])
            }
        except RuntimeError:
            current_reactions = {}

        users_on_emoji = current_reactions.get(emoji, [])

        if claude_real not in users_on_emoji:
            if utils.DRY_RUN:
                warn(f"Would add :{emoji}: to {msg_label} as the agent")
            else:
                try:
                    api("reactions.add", channel=real_ch, timestamp=ts, name=emoji)
                    log(f"Added :{emoji}: to {msg_label}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    if "already_reacted" not in str(e):
                        warn(f"Failed to add :{emoji}: to {msg_label}: {e}")
        else:
            log(f":{emoji}: on {msg_label} OK")

    # Strip any agent reactions that aren't in the seed set.
    seed_claude_reactions = {
        (MSG_TS_MAP.get(lbl), em)
        for lbl, em, _ in SEED_REACTIONS
        if MSG_TS_MAP.get(lbl)
    }

    try:
        data = api_get("reactions.list", {"user": claude_real, "full": True, "limit": 100})
    except RuntimeError:
        return
    for item in data.get("items", []):
        if item.get("type") != "message":
            continue
        msg = item.get("message", {})
        msg_ts = msg.get("ts")
        for rxn in msg.get("reactions", []):
            if claude_real not in rxn.get("users", []):
                continue
            emoji = rxn["name"]
            if (msg_ts, emoji) in seed_claude_reactions:
                continue
            if utils.DRY_RUN:
                warn(f"Would remove extra agent reaction :{emoji}: ts={msg_ts}")
            else:
                try:
                    api("reactions.remove",
                        channel=item.get("channel", ""), timestamp=msg_ts, name=emoji)
                    log(f"Removed extra :{emoji}: ts={msg_ts}")
                    time.sleep(0.2)
                except RuntimeError as e:
                    warn(f"Remove reaction failed: {e}")


# ---------------------------------------------------------------------------
# 6. Cancel agent-created scheduled messages; restore the standup
# ---------------------------------------------------------------------------

def reset_scheduled_messages():
    section("6. Resetting scheduled messages")
    claude_real = uid("U05CLAUDE")

    try:
        data = api_get("chat.scheduledMessages.list", {"limit": 100})
    except RuntimeError as e:
        warn(f"Could not list scheduled messages: {e}")
        return

    for msg in data.get("scheduled_messages", []):
        if msg.get("user_id") != claude_real:
            continue
        msg_id = msg.get("id")
        ch_id = msg.get("channel_id")
        text = msg.get("text", "")[:50]
        if utils.DRY_RUN:
            warn(f"Would cancel agent scheduled message: {text} (id={msg_id})")
        else:
            try:
                api("chat.deleteScheduledMessage", channel=ch_id, scheduled_message_id=msg_id)
                log(f"Cancelled agent scheduled msg: {text}")
                time.sleep(0.2)
            except RuntimeError as e:
                warn(f"Cancel scheduled msg failed: {e}")

    try:
        data = api_get("chat.scheduledMessages.list", {"channel": cid(STANDUP_CHANNEL), "limit": 10})
        existing = [
            m for m in data.get("scheduled_messages", [])
            if m.get("user_id") == claude_real and STANDUP_TEXT in m.get("text", "")
        ]
        if existing:
            log("Agent's standup scheduled message still present ✓")
            return
        if utils.DRY_RUN:
            warn(f"Would re-schedule standup at post_at={STANDUP_POST_AT_EPOCH}")
        else:
            api("chat.scheduleMessage",
                channel=cid(STANDUP_CHANNEL),
                post_at=STANDUP_POST_AT_EPOCH,
                text=STANDUP_TEXT)
            log("Re-scheduled agent's Monday standup in #marketing")
    except RuntimeError as e:
        warn(f"Could not verify scheduled messages: {e}")


# ---------------------------------------------------------------------------
# 7. Reset agent's DND snooze
# ---------------------------------------------------------------------------

def reset_dnd():
    section("7. Resetting DND snooze")
    if utils.DRY_RUN:
        log("Would end agent's DND snooze (dnd.endSnooze)")
        return
    try:
        api("dnd.endSnooze")
        log("Agent's DND snooze ended")
    except RuntimeError as e:
        if "snooze_not_active" in str(e):
            log("Agent's DND snooze was not active — OK")
        else:
            warn(f"dnd.endSnooze failed: {e}")


# ---------------------------------------------------------------------------
# 8. Archive sweep — any non-seed channel
# ---------------------------------------------------------------------------

def sweep_non_seed_channels():
    """
    Archive every active channel that is not in the canonical seed set.
    Trust the seed set as ground truth and archive anything outside it,
    so reset stays durable against arbitrary channel-creating prompts.
    """
    section("8. Archive sweep — non-seed channels")

    seed_real_ids = {cid(lid) for lid in CHANNEL_SEED_NAMES if cid(lid)}
    ignore_res = [re.compile(p) for p in IGNORE_NAME_PATTERNS]

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
            if any(rx.search(ch_name) for rx in ignore_res):
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
        if utils.DRY_RUN:
            warn(f"#{ch_name} ({ch_id}) is non-seed — would archive")
            continue
        try:
            api("conversations.archive", channel=ch_id)
            log(f"Archived non-seed #{ch_name}")
            time.sleep(0.3)
        except RuntimeError as e:
            err = str(e)
            if "already_archived" in err:
                log(f"#{ch_name} already archived — OK")
            elif "not_in_channel" in err:
                try:
                    api("conversations.join", channel=ch_id)
                    api("conversations.archive", channel=ch_id)
                    log(f"Joined and archived non-seed #{ch_name}")
                    time.sleep(0.3)
                except RuntimeError as e2:
                    warn(f"#{ch_name}: archive failed after join: {e2}")
            elif "cant_archive_general" in err or "method_not_supported_for_channel_type" in err:
                warn(f"#{ch_name}: Slack refused archive ({err}) — drift will be flagged by verify")
            else:
                warn(f"#{ch_name}: archive failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Reset Hintas benchmark workspace to v4 snapshot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without making API calls")
    parser.add_argument("--token", help="Slack user token (overrides SLACK_TOKEN env var)")
    parser.add_argument("--prompt-id",
                        help="(informational) Which prompt you just ran — logged for traceability")
    parser.add_argument("--state-file",
                        help="Explicit path for the workspace state file (overrides --stack).")
    parser.add_argument("--stack",
                        help="Stack name (e.g. slack, hintas). Loads workspace_state_<stack>.json "
                             "and resolves the auth token from the manifest's token_env.")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. first run before seed), exit 0 instead of erroring")
    args = parser.parse_args()

    set_dry_run(args.dry_run)
    if args.token:
        set_token(args.token)
    elif args.stack:
        set_token(load_token_for_stack(args.stack))
    require_token()

    print(f"\n{'=' * 60}")
    print("  Hintas Benchmark — Workspace Reset")
    print(f"  Mode: {'DRY RUN' if utils.DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Resetting after prompt: {args.prompt_id}")
    print(f"{'=' * 60}")

    state_path = resolve_state_file(args.state_file, args.stack)
    if not load_state(state_path, allow_missing=args.allow_missing_state):
        return

    reset_channel_names_and_topics()
    reset_archive_state()
    reset_memberships()
    delete_claude_messages()
    reset_reactions()
    reset_scheduled_messages()
    reset_dnd()
    sweep_non_seed_channels()

    print(f"\n{'=' * 60}")
    print(f"  RESET {'(DRY RUN)' if utils.DRY_RUN else 'COMPLETE'}")
    print("  ⚠️  Manual/seed-only items:")
    print("     - Custom emoji (add via Slack admin UI, not API)")
    print("     - File uploads (files.delete requires extra scope)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
