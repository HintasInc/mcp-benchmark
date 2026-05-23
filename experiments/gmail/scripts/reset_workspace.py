#!/usr/bin/env python3
"""
reset_workspace.py — Gmail benchmark workspace reset.

Restores the mailbox to the snapshot captured by ``seed_workspace.py``
BEFORE every prompt run. Surgical reset — undoes prompt-induced mutations
without re-wiping and re-seeding (which would take minutes per prompt). Loads
``workspace_state_ids_<stack>.json`` for the per-stack thread/label/filter id
maps and the ground-truth snapshot.

Scenario A (single-token): all seeded content is agent-authored under
``userId='me'``. Reset only touches the mailbox the script is authenticated
against; cross-mailbox state is not in scope.

Usage:
    uv run python experiments/gmail/scripts/reset_workspace.py --stack gmail
    uv run python experiments/gmail/scripts/reset_workspace.py --stack gmail --dry-run
    uv run python experiments/gmail/scripts/reset_workspace.py --stack gmail --prompt-id 12

What resets:
  ✓ Thread label state (archive/star/read/label add/remove → restored)
  ✓ Trashed seeded threads → untrashed (if a prompt trashed them)
  ✓ Extra user-defined labels created by prompts → deleted
  ✓ Missing seeded labels → recreated (label-id changes, grader resolves by name)
  ✓ Extra drafts created by prompts → deleted
  ✓ Missing seeded drafts → recreated
  ✓ Extra filters created by prompts → deleted
  ✓ Missing seeded filters → recreated
  ✓ Non-primary send-as aliases → deleted (only the primary is preserved)
  ✓ Vacation responder → disabled
  ✓ Auto-forwarding → disabled (if the API exposes it on this mailbox)
  ✓ Non-seed SENT messages → trashed

What does NOT reset (manual / one-time work):
  ! Forwarding-address verification record (operator-managed; reset cannot re-verify)
  ! Seeded message internalDates (set at import time; later runs can't change them)

Exit codes (contract for run_benchmark.py):
    0 → reset succeeded
    1 → API failure during reset
    2 → structural failure (missing state file without --allow-missing-state)
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

# Make sibling scripts/ modules importable when invoked directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmarking.clock import BENCHMARK_NOW
from googleapiclient.errors import HttpError

import constants
import utils
from utils import (
    DRAFT_ID_MAP, FILTER_ID_MAP, GROUND_TRUTH, LABEL_ID_MAP, MESSAGE_ID_MAP,
    THREAD_ID_MAP, build_service, build_substitution_map, load_state,
    load_users, log, resolve_state_file, section, set_dry_run, subst,
    subst_obj, warn,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_thread_labels() -> dict[str, list[str]]:
    """Return {thread_logical_id: [label_name_or_id...]} from ground_truth.

    Ground-truth ``threads`` entries hold the labels as Gmail ids (system
    labels stay as their well-known names). For reset we want the current
    label_id of each user label (since labels may have been re-created),
    resolved via the active ``LABEL_ID_MAP``.
    """
    out: dict[str, list[str]] = {}
    # ground_truth labels come keyed by id; build id → name lookup.
    id_to_name = {lbl["id"]: lbl["name"] for lbl in GROUND_TRUTH.get("labels", []) or [] if lbl.get("id")}
    for t in GROUND_TRUTH.get("threads", []) or []:
        ids: list[str] = []
        for lid in t.get("label_ids", []) or []:
            if lid in constants.SYSTEM_LABELS:
                ids.append(lid)
                continue
            name = id_to_name.get(lid)
            if name and name in LABEL_ID_MAP:
                ids.append(LABEL_ID_MAP[name])
            else:
                # Unknown — drop it from the seed set rather than failing the
                # whole thread reset. Verify will flag any residual drift.
                continue
        out[t["logical_id"]] = ids
    return out


# ---------------------------------------------------------------------------
# 1. Labels — restore seeded set first so thread label restoration can
#    reference the latest ids.
# ---------------------------------------------------------------------------

def reset_labels() -> None:
    section("1. Resetting labels to seeded set")
    svc = utils.service()
    current = svc.users().labels().list(userId="me").execute().get("labels", []) or []
    current_by_name = {lbl["name"]: lbl for lbl in current}

    seed_label_ids = set(LABEL_ID_MAP.values())
    seed_label_names = set(LABEL_ID_MAP.keys())

    # Delete extras (user-type labels not in the seed set).
    for lbl in current:
        if lbl.get("type") != "user":
            continue
        if lbl["id"] in seed_label_ids:
            continue
        if lbl["name"] in seed_label_names:
            # Same name, different id (label was re-created by a prompt) — keep
            # the existing id and update the map so downstream reset steps see it.
            LABEL_ID_MAP[lbl["name"]] = lbl["id"]
            log(f"label {lbl['name']!r} re-bound to current id {lbl['id']}")
            continue
        if utils.DRY_RUN:
            warn(f"would delete extra label {lbl['name']!r}")
            continue
        try:
            svc.users().labels().delete(userId="me", id=lbl["id"]).execute()
            log(f"deleted extra label {lbl['name']!r}")
        except HttpError as e:
            warn(f"labels.delete {lbl['name']!r} failed: {e}")

    # Recreate any seeded label that's missing.
    for name in constants.SEEDED_LABELS:
        if name in current_by_name:
            LABEL_ID_MAP[name] = current_by_name[name]["id"]
            continue
        if utils.DRY_RUN:
            warn(f"would recreate missing label {name!r}")
            LABEL_ID_MAP[name] = f"PLACEHOLDER_{name}"
            continue
        try:
            resp = svc.users().labels().create(
                userId="me",
                body={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            ).execute()
            LABEL_ID_MAP[name] = resp["id"]
            log(f"recreated label {name!r} → {resp['id']}")
        except HttpError as e:
            warn(f"labels.create {name!r} failed: {e}")


# ---------------------------------------------------------------------------
# 2. Threads — restore label state and untrash anything that was trashed.
# ---------------------------------------------------------------------------

def reset_threads() -> None:
    section("2. Restoring thread label state")
    svc = utils.service()
    seed_labels = _seed_thread_labels()

    for logical_id, real_id in THREAD_ID_MAP.items():
        seed_ids = seed_labels.get(logical_id)
        if seed_ids is None:
            warn(f"{logical_id}: no ground-truth labels — skipping")
            continue
        try:
            t = svc.users().threads().get(
                userId="me", id=real_id, format="minimal",
            ).execute()
        except HttpError as e:
            warn(f"threads.get {logical_id} failed: {e}")
            continue

        # threads.get returns messages with per-message labelIds; the thread's
        # effective labels are the union (Gmail semantics).
        current_ids: set[str] = set()
        for m in t.get("messages", []) or []:
            current_ids.update(m.get("labelIds", []) or [])
        seed_set = set(seed_ids)

        # CATEGORY_* labels (except CATEGORY_PERSONAL) are classifier-managed;
        # Gmail rejects threads.modify calls that try to add them via the API.
        # Drop them from `add` so reset doesn't 400 on every run, and leave
        # them alone on the `remove` side too — verify will surface real drift.
        classifier_managed = {
            "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES",
            "CATEGORY_FORUMS",
        }
        add = sorted((seed_set - current_ids) - classifier_managed)
        keep_unmanaged = utils.IGNORE_LABEL_IDS | (
            classifier_managed | {"IMPORTANT", "CATEGORY_PERSONAL", "CHAT"}
        )
        remove = sorted((current_ids - seed_set) - keep_unmanaged)

        if not add and not remove:
            log(f"{logical_id} clean")
            continue
        if utils.DRY_RUN:
            warn(f"{logical_id}: would add={add} remove={remove}")
            continue
        try:
            svc.users().threads().modify(
                userId="me", id=real_id,
                body={"addLabelIds": add, "removeLabelIds": remove},
            ).execute()
            log(f"{logical_id}: add={add} remove={remove}")
            time.sleep(0.1)
        except HttpError as e:
            warn(f"threads.modify {logical_id} failed: {e}")


def untrash_seeded() -> None:
    """If a prompt trashed a thread that wasn't seeded as trashed, untrash it."""
    section("3. Untrashing seeded items not seeded as trashed")
    svc = utils.service()
    seed_labels = _seed_thread_labels()
    for logical_id, real_id in THREAD_ID_MAP.items():
        seed_ids = seed_labels.get(logical_id) or []
        if "TRASH" in seed_ids:
            continue
        try:
            t = svc.users().threads().get(
                userId="me", id=real_id, format="minimal",
            ).execute()
        except HttpError as e:
            warn(f"threads.get {logical_id} failed: {e}")
            continue
        in_trash = any(
            "TRASH" in (m.get("labelIds", []) or []) for m in t.get("messages", []) or []
        )
        if not in_trash:
            continue
        if utils.DRY_RUN:
            warn(f"{logical_id}: would untrash")
            continue
        try:
            svc.users().threads().untrash(userId="me", id=real_id).execute()
            log(f"{logical_id}: untrashed")
        except HttpError as e:
            warn(f"threads.untrash {logical_id} failed: {e}")


# ---------------------------------------------------------------------------
# 4. Drafts
# ---------------------------------------------------------------------------

def reset_drafts() -> None:
    section("4. Resetting drafts")
    svc = utils.service()
    seed_subjects: dict[str, dict] = {
        subst(d["subject"]): d for d in constants.SEEDED_DRAFTS
    }
    seed_ids = set(DRAFT_ID_MAP.values())

    current = svc.users().drafts().list(userId="me", maxResults=500).execute().get("drafts", []) or []
    current_by_id = {d["id"]: d for d in current}

    # Delete extras.
    extras_seen = set()
    for d in current:
        if d["id"] in seed_ids:
            continue
        # Could be a recreated seed draft (same subject, new id). Probe via get.
        try:
            full = svc.users().drafts().get(
                userId="me", id=d["id"], format="metadata",
            ).execute()
        except HttpError as e:
            warn(f"drafts.get {d['id']} failed: {e}")
            continue
        headers = {h["name"].lower(): h["value"]
                   for h in (full.get("message", {}).get("payload", {}).get("headers", []) or [])}
        subject = headers.get("subject", "")
        seed_def = seed_subjects.get(subject)
        if seed_def and seed_def["logical_id"] not in extras_seen:
            DRAFT_ID_MAP[seed_def["logical_id"]] = d["id"]
            extras_seen.add(seed_def["logical_id"])
            log(f"draft {seed_def['logical_id']} rebound to current id {d['id']}")
            continue
        if utils.DRY_RUN:
            warn(f"would delete extra draft {d['id']!r} (subject={subject!r})")
            continue
        try:
            svc.users().drafts().delete(userId="me", id=d["id"]).execute()
            log(f"deleted extra draft {d['id']}")
        except HttpError as e:
            warn(f"drafts.delete {d['id']} failed: {e}")

    # Recreate any seed draft that's missing.
    for d in constants.SEEDED_DRAFTS:
        existing_id = DRAFT_ID_MAP.get(d["logical_id"])
        if existing_id and existing_id in current_by_id:
            continue
        if existing_id and existing_id in {x["id"] for x in current}:
            continue
        if utils.DRY_RUN:
            warn(f"would recreate draft {d['logical_id']}")
            continue
        em = EmailMessage()
        em["From"] = subst(d["from"])
        em["To"] = subst(d["to"])
        if d.get("cc"):
            em["Cc"] = subst(d["cc"])
        em["Subject"] = subst(d["subject"])
        em["Date"] = format_datetime(BENCHMARK_NOW)
        em["Message-ID"] = make_msgid(domain="seed.hintas.local")
        em.set_content(subst(d["body"]))
        raw = base64.urlsafe_b64encode(em.as_bytes()).decode("ascii")
        try:
            resp = svc.users().drafts().create(
                userId="me", body={"message": {"raw": raw}},
            ).execute()
            DRAFT_ID_MAP[d["logical_id"]] = resp["id"]
            log(f"recreated draft {d['logical_id']} → {resp['id']}")
        except HttpError as e:
            warn(f"drafts.create {d['logical_id']} failed: {e}")


# ---------------------------------------------------------------------------
# 5. Filters
# ---------------------------------------------------------------------------

def _resolve_label_ids(names: list[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        if n in constants.SYSTEM_LABELS:
            out.append(n)
        elif n in LABEL_ID_MAP:
            out.append(LABEL_ID_MAP[n])
        else:
            out.append(n)
    return out


def reset_filters() -> None:
    section("5. Resetting filters")
    svc = utils.service()
    current = svc.users().settings().filters().list(userId="me").execute().get("filter", []) or []
    seed_ids = set(FILTER_ID_MAP.values())

    # The filter id often changes when a filter is recreated. Match by criteria
    # signature as a fallback so we don't unnecessarily churn the seeded ones.
    def _sig(f: dict) -> tuple:
        return (
            (f.get("criteria", {}).get("from") or "").lower(),
            (f.get("criteria", {}).get("subject") or "").lower(),
            tuple(sorted(f.get("action", {}).get("addLabelIds", []) or [])),
        )

    seed_sigs = {}
    for sf in constants.SEEDED_FILTERS:
        criteria = subst_obj(sf["criteria"])
        action = subst_obj(sf["action"])
        addLabels = _resolve_label_ids(action.get("addLabelIds", []) or [])
        sig = (
            (criteria.get("from") or "").lower(),
            (criteria.get("subject") or "").lower(),
            tuple(sorted(addLabels)),
        )
        seed_sigs[sig] = sf["logical_id"]

    matched: set[str] = set()
    for f in current:
        fid = f.get("id")
        sig = _sig(f)
        if sig in seed_sigs:
            FILTER_ID_MAP[seed_sigs[sig]] = fid
            matched.add(seed_sigs[sig])
            continue
        if fid in seed_ids:
            # Same id but signature changed — treat as drift, delete + recreate.
            pass
        if utils.DRY_RUN:
            warn(f"would delete extra filter {fid}")
            continue
        try:
            svc.users().settings().filters().delete(userId="me", id=fid).execute()
            log(f"deleted extra filter {fid}")
        except HttpError as e:
            warn(f"filters.delete {fid} failed: {e}")

    # Recreate any seeded filter not currently matched.
    for sf in constants.SEEDED_FILTERS:
        if sf["logical_id"] in matched:
            continue
        criteria = subst_obj(sf["criteria"])
        action = subst_obj(sf["action"])
        if "addLabelIds" in action:
            action["addLabelIds"] = _resolve_label_ids(action["addLabelIds"])
        if "removeLabelIds" in action:
            action["removeLabelIds"] = _resolve_label_ids(action["removeLabelIds"])
        if utils.DRY_RUN:
            warn(f"would recreate filter {sf['logical_id']}")
            continue
        try:
            resp = svc.users().settings().filters().create(
                userId="me", body={"criteria": criteria, "action": action},
            ).execute()
            FILTER_ID_MAP[sf["logical_id"]] = resp["id"]
            log(f"recreated filter {sf['logical_id']} → {resp['id']}")
        except HttpError as e:
            warn(f"filters.create {sf['logical_id']} failed: {e}")


# ---------------------------------------------------------------------------
# 6. Send-as aliases
# ---------------------------------------------------------------------------

def reset_send_as_aliases() -> None:
    section("6. Sweeping non-primary send-as aliases")
    svc = utils.service()
    try:
        aliases = svc.users().settings().sendAs().list(userId="me").execute().get("sendAs", []) or []
    except HttpError as e:
        warn(f"sendAs.list failed: {e}")
        return
    for a in aliases:
        if a.get("isPrimary"):
            continue
        addr = a.get("sendAsEmail", "")
        if utils.DRY_RUN:
            warn(f"would delete extra send-as alias {addr}")
            continue
        try:
            svc.users().settings().sendAs().delete(
                userId="me", sendAsEmail=addr,
            ).execute()
            log(f"deleted extra send-as alias {addr}")
        except HttpError as e:
            warn(f"sendAs.delete {addr} failed: {e}")


# ---------------------------------------------------------------------------
# 7. Vacation + auto-forwarding
# ---------------------------------------------------------------------------

def reset_vacation_and_forwarding() -> None:
    section("7. Disabling vacation responder + auto-forwarding")
    svc = utils.service()
    if utils.DRY_RUN:
        log("would set enableAutoReply=false")
        log("would set auto-forwarding enabled=false")
        return
    try:
        svc.users().settings().updateVacation(
            userId="me", body={"enableAutoReply": False},
        ).execute()
        log("vacation responder disabled")
    except HttpError as e:
        warn(f"updateVacation failed: {e}")
    try:
        svc.users().settings().updateAutoForwarding(
            userId="me", body={"enabled": False},
        ).execute()
        log("auto-forwarding disabled")
    except HttpError as e:
        # 400 is common when no forwarding address was ever configured.
        if getattr(e, "resp", None) and e.resp.status == 400:
            log("auto-forwarding not configured — skipping")
        else:
            warn(f"updateAutoForwarding failed: {e}")


# ---------------------------------------------------------------------------
# 8. Trash non-seed SENT messages
# ---------------------------------------------------------------------------

def trash_non_seed_sent() -> None:
    section("8. Trashing non-seed SENT messages")
    svc = utils.service()
    seed_ids = set(MESSAGE_ID_MAP.values())
    seed_thread_ids = set(THREAD_ID_MAP.values())
    page_token = None
    trashed = 0
    while True:
        params = {
            "userId": "me",
            "labelIds": ["SENT"],
            "maxResults": 500,
        }
        if page_token:
            params["pageToken"] = page_token
        try:
            resp = svc.users().messages().list(**params).execute()
        except HttpError as e:
            warn(f"messages.list SENT failed: {e}")
            return
        for m in resp.get("messages", []) or []:
            if m.get("id") in seed_ids:
                continue
            # Some seeded SENT messages live inside a thread we own — leave any
            # message in a seeded thread alone (it's part of the seeded state).
            if m.get("threadId") in seed_thread_ids:
                continue
            if utils.DRY_RUN:
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
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Reset the Gmail benchmark mailbox to the seed snapshot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without making API calls")
    parser.add_argument("--token",
                        help="Refresh token override (otherwise read from <STACK>_TOKEN env).")
    parser.add_argument("--prompt-id",
                        help="(informational) Which prompt just ran — logged for traceability")
    parser.add_argument("--state-file",
                        help="Explicit state-file path (overrides --stack default).")
    parser.add_argument("--stack", required=True,
                        help="Stack name from gmail.toml (e.g. 'gmail' or 'hintas').")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. before seed), exit 0 instead of erroring")
    args = parser.parse_args()

    set_dry_run(args.dry_run)
    build_service(args.stack, refresh_token=args.token)

    print(f"\n{'=' * 60}")
    print("  Gmail Benchmark — Workspace Reset")
    print(f"  Stack: {args.stack}")
    print(f"  Mode:  {'DRY RUN' if utils.DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Resetting after prompt: {args.prompt_id}")
    print(f"{'=' * 60}")

    state_path = resolve_state_file(args.state_file, args.stack)
    if not load_state(state_path, allow_missing=args.allow_missing_state):
        return 0

    users = load_users()
    owner_email = utils.STATE.get("owner_email", "")
    build_substitution_map(users, owner_email=owner_email)

    try:
        reset_labels()
        reset_threads()
        untrash_seeded()
        reset_drafts()
        reset_filters()
        reset_send_as_aliases()
        reset_vacation_and_forwarding()
        trash_non_seed_sent()
    except HttpError as e:
        print(f"\nERROR: reset aborted on Gmail API failure: {e}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  RESET {'(DRY RUN)' if utils.DRY_RUN else 'COMPLETE'}")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
