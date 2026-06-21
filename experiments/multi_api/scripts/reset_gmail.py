#!/usr/bin/env python3
"""
reset_gmail.py — multi-API benchmark Gmail-surface reset.

Restores the agent's mailbox to the snapshot captured by ``seed_gmail.py``
BEFORE every prompt run. Surgical reset — undoes prompt-induced mutations
without re-wiping and re-seeding. Loads ``workspace_state_gmail.json`` for the
per-surface thread/message id maps and the ground-truth snapshot.

Standalone: reads OAuth credentials straight from the environment
(``GMAIL_TOKEN`` refresh token plus ``GMAIL_CLIENT_ID`` /
``GMAIL_CLIENT_SECRET``) and inlines a minimal Gmail Discovery service builder.

Usage:
    uv run python experiments/multi_api/scripts/reset_gmail.py
    uv run python experiments/multi_api/scripts/reset_gmail.py --dry-run
    uv run python experiments/multi_api/scripts/reset_gmail.py --prompt-id 12

What resets:
  ✓ Extra user-defined labels created by prompts → deleted (e.g. 'Needs-Triage')
  ✓ Per-seeded-message label state (star/read/important/user labels) → restored
  ✓ Extra drafts created by prompts → deleted (none seeded)
  ✓ Non-seed SENT messages → trashed (prompt-sent mail; seeded reply preserved)
  ✓ Extra filters created by prompts → deleted (none seeded)
  ✓ Vacation responder → disabled (defensive)

What does NOT reset (manual / one-time work):
  ! Seeded message internalDates (set at import time; later runs can't change them)

Exit codes:
    0 → reset succeeded (or state missing with --allow-missing-state)
    1 → API failure during reset
    2 → structural failure (missing state file without --allow-missing-state)
"""
from __future__ import annotations

import argparse
import os
import sys

# Make sibling scripts/ modules (common.py) importable when invoked directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common
from common import (
    log, warn, err, section, subsection, set_dry_run, load_users,
    build_substitution_map, subst, subst_obj, team_distribution,
    agent_logical_id, email_of, name_of, save_state, load_state,
    resolve_state_file, add_stack_arg, stack_env, STACK_ENV_PREFIX,
)
from benchmarking.clock import BENCHMARK_NOW, BENCHMARK_NOW_EPOCH

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_URI = "https://oauth2.googleapis.com/token"

# No user labels are seeded — anything user-type is prompt drift.
SEEDED_LABELS: list[str] = []

# System membership we never strip during per-message label restore; only
# STARRED/UNREAD/IMPORTANT and user labels are reconciled against the snapshot.
PROTECTED_SYSTEM_LABELS = {
    "INBOX", "SENT", "DRAFT", "TRASH", "SPAM", "CHAT",
    "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS",
}

# Module-level dry-run mirror (kept in lockstep with common.DRY_RUN).
DRY_RUN: bool = False

SERVICE = None


# ---------------------------------------------------------------------------
# Standalone auth + service builder (mirrors seed_gmail.build_service())
# ---------------------------------------------------------------------------

def build_service(
    stack: str = "baseline",
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
):
    """Build a Gmail Discovery resource from env-supplied OAuth credentials.

    Credentials resolve from the stack-prefixed env vars
    (``BASELINE_``/``HINTAS_`` + ``GMAIL_TOKEN`` / ``GMAIL_CLIENT_ID`` /
    ``GMAIL_CLIENT_SECRET``). Any explicit value passed in overrides the
    lookup. Exits with a friendly message when any credential is missing.
    """
    global SERVICE

    refresh_token = refresh_token or stack_env(stack, "GMAIL_TOKEN")
    client_id = client_id or stack_env(stack, "GMAIL_CLIENT_ID")
    client_secret = client_secret or stack_env(stack, "GMAIL_CLIENT_SECRET")

    p = STACK_ENV_PREFIX[stack]
    missing = [
        name
        for name, value in (
            (f"{p}GMAIL_TOKEN (refresh token)", refresh_token),
            (f"{p}GMAIL_CLIENT_ID", client_id),
            (f"{p}GMAIL_CLIENT_SECRET", client_secret),
        )
        if not value
    ]
    if missing:
        err(f"missing Gmail credentials: {', '.join(missing)}")
        print(
            f"  Set {p}GMAIL_TOKEN, {p}GMAIL_CLIENT_ID and {p}GMAIL_CLIENT_SECRET "
            "in the environment (or pass --token / --client-id / --client-secret)."
        )
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
    )
    SERVICE = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return SERVICE


def service():
    if SERVICE is None:
        err("gmail service not initialised — call build_service() first")
        sys.exit(1)
    return SERVICE


# ---------------------------------------------------------------------------
# 1. Labels — delete every user-type label not in the seeded set.
# ---------------------------------------------------------------------------

def reset_labels() -> None:
    section("1. Deleting extra user labels")
    svc = service()
    current = svc.users().labels().list(userId="me").execute().get("labels", []) or []
    for lbl in current:
        if lbl.get("type") != "user":
            continue
        if lbl.get("name") in SEEDED_LABELS:
            continue
        if DRY_RUN:
            warn(f"would delete extra label {lbl.get('name')!r}")
            continue
        try:
            svc.users().labels().delete(userId="me", id=lbl["id"]).execute()
            log(f"deleted extra label {lbl.get('name')!r}")
        except HttpError as e:
            warn(f"labels.delete {lbl.get('name')!r} failed: {e}")


# ---------------------------------------------------------------------------
# 2. Per-seeded-message label restore — reconcile each message's reconciled
#    labels (STARRED/UNREAD/IMPORTANT + user labels) to the seed snapshot.
# ---------------------------------------------------------------------------

def _seed_message_labels(state: dict) -> dict[str, set[str]]:
    """Return {message_real_id: {seed label_ids...}} from ground_truth."""
    out: dict[str, set[str]] = {}
    truth = state.get("ground_truth", {}) or {}
    for m in truth.get("messages", []) or []:
        mid = m.get("id")
        if mid:
            out[mid] = set(m.get("label_ids", []) or [])
    return out


def reset_message_labels(state: dict) -> None:
    section("2. Restoring per-message label state")
    svc = service()
    seed_labels = _seed_message_labels(state)
    message_id_map = state.get("message_id_map", {}) or {}

    # Only these labels are reconciled. System membership (INBOX/SENT/...) and
    # CATEGORY_* are left to their snapshot/classifier state.
    reconcilable_system = {"STARRED", "UNREAD", "IMPORTANT"}

    for logical_id, real_id in message_id_map.items():
        seed_set = seed_labels.get(real_id)
        if seed_set is None:
            warn(f"{logical_id}: no ground-truth labels — skipping")
            continue
        try:
            m = svc.users().messages().get(
                userId="me", id=real_id, format="minimal",
            ).execute()
        except HttpError as e:
            warn(f"messages.get {logical_id} failed: {e}")
            continue
        current = set(m.get("labelIds", []) or [])

        # Add back any seed label that's now missing (e.g. a prompt marked a
        # triage message read → re-add UNREAD).
        add = sorted(seed_set - current)
        # Remove labels present now but not in the seed set, scoped to the
        # reconcilable system labels (STARRED/UNREAD/IMPORTANT) plus user labels
        # (anything that isn't a protected system label). e.g. prompt 4 stars
        # TH_EXPORT → remove STARRED.
        removable = set()
        for lid in current - seed_set:
            if lid in reconcilable_system:
                removable.add(lid)
            elif lid not in PROTECTED_SYSTEM_LABELS:
                removable.add(lid)
        remove = sorted(removable)

        if not add and not remove:
            log(f"{logical_id} clean")
            continue
        if DRY_RUN:
            warn(f"{logical_id}: would add={add} remove={remove}")
            continue
        try:
            svc.users().messages().modify(
                userId="me", id=real_id,
                body={"addLabelIds": add, "removeLabelIds": remove},
            ).execute()
            log(f"{logical_id}: add={add} remove={remove}")
        except HttpError as e:
            warn(f"messages.modify {logical_id} failed: {e}")


# ---------------------------------------------------------------------------
# 3. Drafts — delete ALL drafts (none seeded → removes prompt-created drafts).
# ---------------------------------------------------------------------------

def reset_drafts() -> None:
    section("3. Deleting all drafts")
    svc = service()
    current = svc.users().drafts().list(userId="me", maxResults=500).execute().get("drafts", []) or []
    for d in current:
        did = d.get("id")
        if not did:
            continue
        if DRY_RUN:
            warn(f"would delete draft {did}")
            continue
        try:
            svc.users().drafts().delete(userId="me", id=did).execute()
            log(f"deleted draft {did}")
        except HttpError as e:
            warn(f"drafts.delete {did} failed: {e}")


# ---------------------------------------------------------------------------
# 4. SENT cleanup — trash any SENT message not in the seed message map.
# ---------------------------------------------------------------------------

def trash_non_seed_sent(state: dict) -> None:
    section("4. Trashing non-seed SENT messages")
    svc = service()
    seed_ids = set((state.get("message_id_map", {}) or {}).values())
    page_token = None
    trashed = 0
    while True:
        params = {"userId": "me", "labelIds": ["SENT"], "maxResults": 500}
        if page_token:
            params["pageToken"] = page_token
        try:
            resp = svc.users().messages().list(**params).execute()
        except HttpError as e:
            warn(f"messages.list SENT failed: {e}")
            return
        for m in resp.get("messages", []) or []:
            # Preserve the seeded TH_PARTNERSHIP reply (its id is in seed_ids).
            if m.get("id") in seed_ids:
                continue
            if DRY_RUN:
                warn(f"would trash SENT message {m['id']}")
                continue
            try:
                svc.users().messages().trash(userId="me", id=m["id"]).execute()
                trashed += 1
            except HttpError as e:
                warn(f"messages.trash {m['id']} failed: {e}")
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    if trashed:
        log(f"trashed {trashed} non-seed SENT message(s)")
    else:
        log("no non-seed SENT messages found")


# ---------------------------------------------------------------------------
# 5. Filters — delete any filter not seeded (none seeded → delete all).
# ---------------------------------------------------------------------------

def reset_filters() -> None:
    section("5. Deleting non-seed filters")
    svc = service()
    current = svc.users().settings().filters().list(userId="me").execute().get("filter", []) or []
    for f in current:
        fid = f.get("id")
        if not fid:
            continue
        if DRY_RUN:
            warn(f"would delete filter {fid}")
            continue
        try:
            svc.users().settings().filters().delete(userId="me", id=fid).execute()
            log(f"deleted filter {fid}")
        except HttpError as e:
            warn(f"filters.delete {fid} failed: {e}")


# ---------------------------------------------------------------------------
# 6. Vacation responder — disabled defensively.
# ---------------------------------------------------------------------------

def reset_vacation() -> None:
    section("6. Disabling vacation responder")
    svc = service()
    if DRY_RUN:
        log("would set enableAutoReply=false")
        return
    try:
        svc.users().settings().updateVacation(
            userId="me", body={"enableAutoReply": False},
        ).execute()
        log("vacation responder disabled")
    except HttpError as e:
        warn(f"updateVacation failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN

    parser = argparse.ArgumentParser(
        description="Reset the multi-API benchmark Gmail surface to the seed snapshot"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without making API calls.")
    parser.add_argument("--prompt-id",
                        help="(informational) Which prompt just ran — logged for traceability.")
    parser.add_argument("--token", help="Refresh token override (else BASELINE_/HINTAS_GMAIL_TOKEN).")
    parser.add_argument("--client-id", help="OAuth client id override (else BASELINE_/HINTAS_GMAIL_CLIENT_ID).")
    parser.add_argument("--client-secret", help="OAuth client secret override (else BASELINE_/HINTAS_GMAIL_CLIENT_SECRET).")
    parser.add_argument("--state-file", help="Explicit state-file path (overrides the default).")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. before seed), exit 0 instead of erroring.")
    add_stack_arg(parser)
    args = parser.parse_args()

    DRY_RUN = args.dry_run
    set_dry_run(args.dry_run)
    build_service(
        stack=args.stack,
        refresh_token=args.token,
        client_id=args.client_id,
        client_secret=args.client_secret,
    )

    print(f"\n{'=' * 60}")
    print("  Multi-API Benchmark — Gmail Surface Reset")
    print(f"  Mode:  {'DRY RUN' if DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Resetting after prompt: {args.prompt_id}")
    print(f"{'=' * 60}")

    state_path = resolve_state_file(args.state_file, "gmail", args.stack)
    state = load_state(state_path, allow_missing=args.allow_missing_state)
    if state is None:
        return 0

    load_users()
    build_substitution_map(owner_email=state.get("owner_email", ""))

    try:
        reset_labels()
        reset_message_labels(state)
        reset_drafts()
        trash_non_seed_sent(state)
        reset_filters()
        reset_vacation()
    except HttpError as e:
        print(f"\nERROR: reset aborted on Gmail API failure: {e}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  RESET {'(DRY RUN)' if DRY_RUN else 'COMPLETE'}")
    print("  Manual / per-prompt step — run before each prompt run.")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
