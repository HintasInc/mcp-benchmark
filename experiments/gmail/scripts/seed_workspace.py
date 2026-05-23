#!/usr/bin/env python3
"""
seed_workspace.py — Gmail benchmark workspace seeder.

Builds the {{EMAIL_U05CLAUDE}} mailbox into the v1 seed snapshot described in
experiments/gmail/IMPLEMENTATION.md §"Mailbox overview". Runs against a single
stack at a time; the orchestrator invokes this twice (once per stack) before
the benchmark proper.

Scenario A (single-token): every seeded SENT message, draft, label, filter,
and send-as alias is authored by the agent under userId='me'. Inbound
messages carry external sender addresses in their From headers via
``messages.import``.

Usage:
    uv run python experiments/gmail/scripts/seed_workspace.py --stack gmail --verify
    uv run python experiments/gmail/scripts/seed_workspace.py --stack gmail

Prerequisites:
    - experiments/gmail/.env populated with <STACK>_CLIENT_ID,
      <STACK>_CLIENT_SECRET, and the refresh token env from gmail.toml.
    - experiments/gmail/scripts/prerequisites_<stack>.local.json hand-written
      by the operator (see utils.load_prerequisites).

State is written to ``workspace_state_ids_<stack>.json`` (path templated by
gmail.toml). The state file embeds a ``ground_truth`` block — a snapshot of
every entity at seed time — that prompts and the verifier reference as the
benchmark's answer key.

benchmark_now is anchored to 2026-04-19T10:00:00-07:00 via
``benchmarking.clock``.
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Any

# Make sibling scripts/ modules importable when invoked directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmarking.clock import BENCHMARK_NOW, BENCHMARK_NOW_EPOCH
from googleapiclient.errors import HttpError

import constants
import utils
from utils import (
    DRAFT_ID_MAP, FILTER_ID_MAP, LABEL_ID_MAP, MESSAGE_ID_MAP, THREAD_ID_MAP,
    build_service, build_substitution_map, load_prerequisites, load_users,
    log, save_state, section, set_dry_run, subst, subst_obj, warn,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# RFC822 construction
# ---------------------------------------------------------------------------

def _date_for_offset(offset_hours: float) -> datetime:
    return BENCHMARK_NOW + timedelta(hours=offset_hours)


def _build_raw(msg: dict, *, in_reply_to: str | None = None,
               references: list[str] | None = None) -> tuple[str, str]:
    """Build an RFC822 raw blob from a seed-message dict.

    Returns ``(raw_b64url, message_id_header)`` so the seeder can chain the
    Message-ID into the next message's References.
    """
    em = EmailMessage()
    em["From"] = subst(msg["from"])
    em["To"] = subst(msg["to"])
    if msg.get("cc"):
        em["Cc"] = subst(msg["cc"])
    em["Subject"] = subst(msg["subject"])
    em["Date"] = format_datetime(_date_for_offset(msg["offset_hours"]))
    message_id = make_msgid(domain="seed.hintas.local")
    em["Message-ID"] = message_id
    if in_reply_to:
        em["In-Reply-To"] = in_reply_to
    if references:
        em["References"] = " ".join(references)
    em.set_content(subst(msg["body"]))

    for att in msg.get("attachments") or []:
        maintype, _, subtype = att["mime"].partition("/")
        em.add_attachment(
            att["content"].encode("utf-8"),
            maintype=maintype,
            subtype=subtype or "plain",
            filename=att["filename"],
        )

    raw = base64.urlsafe_b64encode(em.as_bytes()).decode("ascii")
    return raw, message_id


# ---------------------------------------------------------------------------
# Auth + prerequisite checks
# ---------------------------------------------------------------------------

def verify_auth_and_prereqs(stack: str) -> dict[str, Any]:
    """Confirm the mailbox identity matches the prerequisites file.

    Returns the ``users.getProfile`` payload (emailAddress, messagesTotal,
    threadsTotal, historyId) for downstream use.
    """
    section("0. Verifying auth + prerequisites")
    svc = utils.service()
    profile = svc.users().getProfile(userId="me").execute()
    email = profile.get("emailAddress", "")
    print(f"  Authenticated as: {email}")
    print(
        f"  Mailbox totals: {profile.get('messagesTotal', '?')} messages, "
        f"{profile.get('threadsTotal', '?')} threads, "
        f"historyId={profile.get('historyId', '?')}"
    )

    prereqs = load_prerequisites(stack)
    if prereqs["email_address"].lower() != email.lower():
        print(
            f"ERROR: prerequisites_{stack}.local.json email_address "
            f"({prereqs['email_address']!r}) does not match the authenticated "
            f"mailbox ({email!r}). Update the prerequisites file or check that "
            f"the {stack.upper()}_TOKEN refresh token belongs to the right mailbox."
        )
        sys.exit(2)
    log(f"prereqs match {email}")
    return profile


def verify_aliases() -> list[dict]:
    """Confirm the primary send-as alias is present. Returns the alias list."""
    svc = utils.service()
    data = svc.users().settings().sendAs().list(userId="me").execute()
    aliases = data.get("sendAs", []) or []
    primary = next((a for a in aliases if a.get("isPrimary")), None)
    if not primary:
        print("ERROR: no primary send-as alias on this mailbox — Gmail account is misconfigured")
        sys.exit(2)
    log(f"Primary send-as alias present: {primary.get('sendAsEmail')}")
    return aliases


# ---------------------------------------------------------------------------
# Wipe phase
# ---------------------------------------------------------------------------

MAX_WIPE_PASSES = 50


def wipe_threads() -> None:
    """Permanently delete every thread in the mailbox.

    Re-lists after each pass — Gmail's index sometimes lags behind deletes, so
    chasing ``nextPageToken`` can return stale ids. Bounded at
    ``MAX_WIPE_PASSES`` so a misbehaving API doesn't spin forever, and breaks
    when a pass makes no progress.
    """
    section("1a. Wiping all existing threads")
    if utils.DRY_RUN:
        log("Would delete every thread (all labels)")
        return
    svc = utils.service()
    deleted = 0
    for _ in range(MAX_WIPE_PASSES):
        resp = svc.users().threads().list(
            userId="me", maxResults=500, includeSpamTrash=True,
        ).execute()
        threads = resp.get("threads", []) or []
        if not threads:
            break
        pass_deleted = 0
        for t in threads:
            tid = t.get("id")
            if not tid:
                continue
            try:
                svc.users().threads().delete(userId="me", id=tid).execute()
                pass_deleted += 1
            except HttpError as e:
                # 404 means already gone — fine. Anything else, log and continue.
                if getattr(e, "resp", None) and e.resp.status == 404:
                    continue
                warn(f"threads.delete {tid} failed: {e}")
        deleted += pass_deleted
        if pass_deleted == 0:
            warn(f"wipe pass made no progress with {len(threads)} thread(s) remaining — aborting")
            break
    else:
        warn(f"wipe_threads hit MAX_WIPE_PASSES={MAX_WIPE_PASSES}")
    if deleted:
        log(f"Deleted {deleted} thread(s)")
    else:
        log("Mailbox already empty")


def wipe_drafts() -> None:
    section("1b. Wiping all drafts")
    if utils.DRY_RUN:
        log("Would delete every draft")
        return
    svc = utils.service()
    deleted = 0
    for _ in range(MAX_WIPE_PASSES):
        resp = svc.users().drafts().list(userId="me", maxResults=500).execute()
        drafts = resp.get("drafts", []) or []
        if not drafts:
            break
        pass_deleted = 0
        for d in drafts:
            did = d.get("id")
            if not did:
                continue
            try:
                svc.users().drafts().delete(userId="me", id=did).execute()
                pass_deleted += 1
            except HttpError as e:
                if getattr(e, "resp", None) and e.resp.status == 404:
                    continue
                warn(f"drafts.delete {did} failed: {e}")
        deleted += pass_deleted
        if pass_deleted == 0:
            warn(f"wipe pass made no progress with {len(drafts)} draft(s) remaining — aborting")
            break
    else:
        warn(f"wipe_drafts hit MAX_WIPE_PASSES={MAX_WIPE_PASSES}")
    if deleted:
        log(f"Deleted {deleted} draft(s)")
    else:
        log("No drafts present")


def wipe_filters() -> None:
    section("1c. Wiping all filters")
    if utils.DRY_RUN:
        log("Would delete every filter")
        return
    svc = utils.service()
    data = svc.users().settings().filters().list(userId="me").execute()
    for f in data.get("filter", []) or []:
        fid = f.get("id")
        if not fid:
            continue
        try:
            svc.users().settings().filters().delete(userId="me", id=fid).execute()
            log(f"Deleted filter {fid}")
        except HttpError as e:
            warn(f"filters.delete {fid} failed: {e}")


def wipe_user_labels() -> None:
    section("1d. Wiping user-defined labels")
    if utils.DRY_RUN:
        log("Would delete every user-type label")
        return
    svc = utils.service()
    data = svc.users().labels().list(userId="me").execute()
    for lbl in data.get("labels", []) or []:
        if lbl.get("type") != "user":
            continue
        lid = lbl.get("id")
        if not lid:
            continue
        try:
            svc.users().labels().delete(userId="me", id=lid).execute()
            log(f"Deleted label {lbl.get('name')!r}")
        except HttpError as e:
            warn(f"labels.delete {lbl.get('name')!r} failed: {e}")


def wipe_non_primary_aliases() -> None:
    section("1e. Wiping non-primary send-as aliases")
    if utils.DRY_RUN:
        log("Would delete every non-primary send-as alias")
        return
    svc = utils.service()
    data = svc.users().settings().sendAs().list(userId="me").execute()
    for a in data.get("sendAs", []) or []:
        if a.get("isPrimary"):
            continue
        addr = a.get("sendAsEmail", "")
        try:
            svc.users().settings().sendAs().delete(
                userId="me", sendAsEmail=addr,
            ).execute()
            log(f"Deleted send-as alias {addr}")
        except HttpError as e:
            warn(f"sendAs.delete {addr} failed: {e}")


def wipe_vacation() -> None:
    section("1f. Disabling vacation responder")
    if utils.DRY_RUN:
        log("Would set enableAutoReply=false")
        return
    svc = utils.service()
    try:
        svc.users().settings().updateVacation(
            userId="me", body={"enableAutoReply": False},
        ).execute()
        log("Vacation responder disabled")
    except HttpError as e:
        warn(f"updateVacation failed: {e}")


# ---------------------------------------------------------------------------
# Create labels
# ---------------------------------------------------------------------------

def create_labels() -> None:
    section("2. Creating user labels")
    svc = utils.service()
    LABEL_ID_MAP.clear()
    # Capture every existing label by name first so re-runs don't double-create.
    existing = {
        lbl["name"]: lbl["id"]
        for lbl in svc.users().labels().list(userId="me").execute().get("labels", []) or []
    }
    for name in constants.SEEDED_LABELS:
        if name in existing:
            LABEL_ID_MAP[name] = existing[name]
            log(f"{name} already exists → {existing[name]}")
            continue
        if utils.DRY_RUN:
            log(f"Would create label {name!r}")
            LABEL_ID_MAP[name] = f"PLACEHOLDER_{name}"
            continue
        resp = svc.users().labels().create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        LABEL_ID_MAP[name] = resp["id"]
        log(f"{name} → {resp['id']}")


def _resolve_label_ids(label_names: list[str]) -> list[str]:
    """Map seed-label names to Gmail label ids (system labels pass through)."""
    out: list[str] = []
    for name in label_names:
        if name in constants.SYSTEM_LABELS:
            out.append(name)
        elif name in LABEL_ID_MAP:
            out.append(LABEL_ID_MAP[name])
        else:
            warn(f"unknown label {name!r}; passing through")
            out.append(name)
    return out


# ---------------------------------------------------------------------------
# Import seeded threads + outbound
# ---------------------------------------------------------------------------

def import_threads() -> None:
    section("3. Importing seeded threads")
    svc = utils.service()
    for thread in constants.SEEDED_THREADS:
        label_ids = _resolve_label_ids(thread["labels"])
        thread_id: str | None = None
        prev_message_id: str | None = None
        references: list[str] = []

        for i, msg in enumerate(thread["messages"]):
            raw, message_id = _build_raw(
                msg,
                in_reply_to=prev_message_id,
                references=list(references) if references else None,
            )
            body: dict[str, Any] = {"raw": raw, "labelIds": label_ids}
            if thread_id:
                body["threadId"] = thread_id

            if utils.DRY_RUN:
                log(
                    f"{thread['logical_id']} msg {i + 1}/{len(thread['messages'])}: "
                    f"would import (subject={subst(msg['subject'])!r}, "
                    f"labels={label_ids})"
                )
                THREAD_ID_MAP.setdefault(
                    thread["logical_id"], f"PLACEHOLDER_{thread['logical_id']}"
                )
                MESSAGE_ID_MAP[msg["logical_id"]] = f"PLACEHOLDER_{msg['logical_id']}"
                prev_message_id = message_id
                references.append(message_id)
                continue

            # messages.insert bypasses Gmail's classification + spam filter and
            # honors labelIds verbatim (including SPAM/TRASH/SENT/CATEGORY_*) —
            # essential for predictable benchmark seed state. Per
            # developers.google.com/workspace/gmail/api/reference/rest, insert is
            # the IMAP-APPEND-equivalent path; import_ runs delivery scanning.
            try:
                resp = svc.users().messages().insert(
                    userId="me",
                    internalDateSource="dateHeader",
                    body=body,
                ).execute()
            except HttpError as e:
                warn(
                    f"{thread['logical_id']} msg {i + 1}: insert failed: {e}"
                )
                continue

            if thread_id is None:
                thread_id = resp["threadId"]
                THREAD_ID_MAP[thread["logical_id"]] = thread_id
            MESSAGE_ID_MAP[msg["logical_id"]] = resp["id"]
            prev_message_id = message_id
            references.append(message_id)
            log(
                f"{thread['logical_id']} msg {i + 1}: id={resp['id']} "
                f"thread={resp['threadId']}"
            )


def import_outbound() -> None:
    section("4. Importing seeded outbound (SENT) messages")
    svc = utils.service()
    for msg in constants.SEEDED_OUTBOUND:
        label_ids = _resolve_label_ids(msg.get("labels", ["SENT"]))
        raw, _ = _build_raw(msg)
        body = {"raw": raw, "labelIds": label_ids}
        if utils.DRY_RUN:
            log(f"{msg['logical_id']}: would import SENT message")
            MESSAGE_ID_MAP[msg["logical_id"]] = f"PLACEHOLDER_{msg['logical_id']}"
            continue
        try:
            # See note in import_threads — messages.insert is the
            # classification-bypassing primitive we need for SENT seeding.
            resp = svc.users().messages().insert(
                userId="me",
                internalDateSource="dateHeader",
                body=body,
            ).execute()
            MESSAGE_ID_MAP[msg["logical_id"]] = resp["id"]
            log(f"{msg['logical_id']}: id={resp['id']}")
        except HttpError as e:
            warn(f"{msg['logical_id']} insert failed: {e}")


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------

def create_drafts() -> None:
    section("5. Creating drafts")
    svc = utils.service()
    DRAFT_ID_MAP.clear()
    for d in constants.SEEDED_DRAFTS:
        # Drafts don't carry the offset_hours field; format as benchmark_now.
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
        if utils.DRY_RUN:
            log(f"{d['logical_id']}: would create draft (subject={subst(d['subject'])!r})")
            DRAFT_ID_MAP[d["logical_id"]] = f"PLACEHOLDER_{d['logical_id']}"
            continue
        try:
            resp = svc.users().drafts().create(
                userId="me", body={"message": {"raw": raw}},
            ).execute()
            DRAFT_ID_MAP[d["logical_id"]] = resp["id"]
            log(f"{d['logical_id']} → {resp['id']}")
        except HttpError as e:
            warn(f"{d['logical_id']} create failed: {e}")


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def create_filters() -> None:
    section("6. Creating filters")
    svc = utils.service()
    FILTER_ID_MAP.clear()
    for f in constants.SEEDED_FILTERS:
        criteria = subst_obj(f["criteria"])
        action = subst_obj(f["action"])
        # Resolve label names in addLabelIds / removeLabelIds.
        if "addLabelIds" in action:
            action["addLabelIds"] = _resolve_label_ids(action["addLabelIds"])
        if "removeLabelIds" in action:
            action["removeLabelIds"] = _resolve_label_ids(action["removeLabelIds"])
        if utils.DRY_RUN:
            log(f"{f['logical_id']}: would create filter (criteria={criteria}, action={action})")
            FILTER_ID_MAP[f["logical_id"]] = f"PLACEHOLDER_{f['logical_id']}"
            continue
        try:
            resp = svc.users().settings().filters().create(
                userId="me", body={"criteria": criteria, "action": action},
            ).execute()
            FILTER_ID_MAP[f["logical_id"]] = resp["id"]
            log(f"{f['logical_id']} → {resp['id']}")
        except HttpError as e:
            warn(f"{f['logical_id']} create failed: {e}")


# ---------------------------------------------------------------------------
# Ground truth capture
# ---------------------------------------------------------------------------

def capture_ground_truth(profile: dict[str, Any], aliases: list[dict]) -> dict:
    section("7. Capturing ground truth")
    svc = utils.service()
    truth: dict[str, Any] = {
        "workspace": {
            "owner_email": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal"),
            "threads_total": profile.get("threadsTotal"),
            "history_id": profile.get("historyId"),
            "timezone": "America/Los_Angeles",
            "locale": "en-US",
        },
        "users": [],
        "labels": [],
        "threads": [],
        "messages": [],
        "drafts": [],
        "filters": [],
        "send_as_aliases": [],
        "vacation_responder": {},
        "auto_forwarding": {},
        "ignore": {
            "label_name_patterns": list(constants.IGNORE_LABEL_NAME_PATTERNS),
            "label_ids": [],
        },
    }

    # Users (resolved via subst from the loaded cast).
    for logical_id, entry in utils.USERS.items():
        truth["users"].append({
            "id": entry.get("id", logical_id),
            "email": subst(f"{{{{EMAIL_{logical_id}}}}}"),
            "name": entry.get("name", ""),
            "handle": entry.get("handle", ""),
            "display_name": entry.get("display_name", ""),
            "is_benchmark_author": bool(entry.get("benchmark-author")),
        })

    # Labels — capture every label so verifier can flag drift.
    labels_data = svc.users().labels().list(userId="me").execute()
    for lbl in labels_data.get("labels", []) or []:
        truth["labels"].append({
            "id": lbl.get("id"),
            "name": lbl.get("name"),
            "type": lbl.get("type"),
            "label_list_visibility": lbl.get("labelListVisibility"),
            "message_list_visibility": lbl.get("messageListVisibility"),
        })
    log(f"Captured {len(truth['labels'])} labels")

    # Threads — capture every seeded thread by id (resolved at seed time).
    for logical_id, real_id in THREAD_ID_MAP.items():
        try:
            t = svc.users().threads().get(
                userId="me", id=real_id, format="metadata",
            ).execute()
        except HttpError as e:
            warn(f"threads.get {logical_id} failed: {e}")
            continue
        msgs = t.get("messages", []) or []
        thread_label_ids: set[str] = set()
        thread_messages: list[dict] = []
        for m in msgs:
            label_ids = m.get("labelIds", []) or []
            thread_label_ids.update(label_ids)
            headers = {h["name"].lower(): h["value"] for h in (m.get("payload", {}).get("headers", []) or [])}
            thread_messages.append({
                "id": m.get("id"),
                "thread_id": m.get("threadId"),
                "label_ids": label_ids,
                "internal_date_ms": int(m.get("internalDate", "0")),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "cc": headers.get("cc", ""),
                "subject": headers.get("subject", ""),
                "message_id_header": headers.get("message-id", ""),
            })
        truth["threads"].append({
            "logical_id": logical_id,
            "id": real_id,
            "label_ids": sorted(thread_label_ids),
            "message_count": len(msgs),
            "subject": thread_messages[0]["subject"] if thread_messages else "",
        })
        truth["messages"].extend(thread_messages)
    log(f"Captured {len(truth['threads'])} threads / {len(truth['messages'])} messages")

    # Drafts.
    for logical_id, real_id in DRAFT_ID_MAP.items():
        try:
            d = svc.users().drafts().get(
                userId="me", id=real_id, format="metadata",
            ).execute()
        except HttpError as e:
            warn(f"drafts.get {logical_id} failed: {e}")
            continue
        m = d.get("message", {}) or {}
        headers = {h["name"].lower(): h["value"] for h in (m.get("payload", {}).get("headers", []) or [])}
        truth["drafts"].append({
            "logical_id": logical_id,
            "id": real_id,
            "message_id": m.get("id"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "cc": headers.get("cc", ""),
            "subject": headers.get("subject", ""),
        })
    log(f"Captured {len(truth['drafts'])} drafts")

    # Filters.
    fdata = svc.users().settings().filters().list(userId="me").execute()
    for f in fdata.get("filter", []) or []:
        truth["filters"].append({
            "id": f.get("id"),
            "criteria": f.get("criteria", {}),
            "action": f.get("action", {}),
        })
    log(f"Captured {len(truth['filters'])} filters")

    # Send-as aliases.
    for a in aliases:
        truth["send_as_aliases"].append({
            "send_as_email": a.get("sendAsEmail"),
            "display_name": a.get("displayName", ""),
            "signature": a.get("signature", ""),
            "is_primary": bool(a.get("isPrimary")),
            "is_default": bool(a.get("isDefault")),
            "verification_status": a.get("verificationStatus", ""),
        })
    log(f"Captured {len(truth['send_as_aliases'])} send-as aliases")

    # Vacation responder + auto-forwarding (post-wipe, expected baseline = off).
    try:
        vac = svc.users().settings().getVacation(userId="me").execute()
        truth["vacation_responder"] = {
            "enable_auto_reply": bool(vac.get("enableAutoReply")),
            "response_subject": vac.get("responseSubject", ""),
            "response_body_plain_text": vac.get("responseBodyPlainText", ""),
            "response_body_html": vac.get("responseBodyHtml", ""),
            "restrict_to_contacts": bool(vac.get("restrictToContacts")),
            "restrict_to_domain": bool(vac.get("restrictToDomain")),
            "start_time": vac.get("startTime"),
            "end_time": vac.get("endTime"),
        }
    except HttpError as e:
        warn(f"getVacation failed: {e}")

    try:
        af = svc.users().settings().getAutoForwarding(userId="me").execute()
        truth["auto_forwarding"] = {
            "enabled": bool(af.get("enabled")),
            "email_address": af.get("emailAddress", ""),
            "disposition": af.get("disposition", ""),
        }
    except HttpError as e:
        # Some accounts return 400 when no forwarding has ever been configured.
        warn(f"getAutoForwarding skipped: {e}")

    return truth


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the Gmail benchmark mailbox")
    parser.add_argument(
        "--verify", "--dry-run", dest="verify", action="store_true",
        help="Dry-run: walk the seed plan, log every step, mutate nothing.",
    )
    parser.add_argument(
        "--token",
        help="Refresh token override (otherwise read from <STACK>_TOKEN env).",
    )
    parser.add_argument(
        "--state-file",
        help="Explicit state-file path (overrides --stack default).",
    )
    parser.add_argument(
        "--stack", required=True,
        help="Stack name from gmail.toml (e.g. 'gmail' or 'hintas').",
    )
    args = parser.parse_args()

    set_dry_run(args.verify)
    build_service(args.stack, refresh_token=args.token)

    print(f"\n{'=' * 60}")
    print("  Gmail Benchmark — Workspace Seeder")
    print(f"  Stack: {args.stack}")
    print(f"  Mode:  {'DRY RUN (verify)' if utils.DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'=' * 60}")

    users = load_users()
    profile = verify_auth_and_prereqs(args.stack)
    build_substitution_map(users, owner_email=profile.get("emailAddress"))
    aliases = verify_aliases()

    wipe_threads()
    wipe_drafts()
    wipe_filters()
    wipe_user_labels()
    wipe_non_primary_aliases()
    wipe_vacation()

    create_labels()
    import_threads()
    import_outbound()
    create_drafts()
    create_filters()

    aliases_post = verify_aliases()  # re-read after wipe + recreation

    if utils.DRY_RUN:
        print(f"\n{'=' * 60}")
        print("  VERIFY COMPLETE — no mutations performed")
        print(f"{'=' * 60}\n")
        return 0

    truth = capture_ground_truth(profile, aliases_post)
    state_path = args.state_file or os.path.join(
        SCRIPT_DIR, f"workspace_state_ids_{args.stack}.json",
    )
    payload = {
        "stack": args.stack,
        "owner_email": profile.get("emailAddress", ""),
        "history_id": profile.get("historyId"),
        "thread_id_map": dict(THREAD_ID_MAP),
        "message_id_map": dict(MESSAGE_ID_MAP),
        "label_id_map": dict(LABEL_ID_MAP),
        "draft_id_map": dict(DRAFT_ID_MAP),
        "filter_id_map": dict(FILTER_ID_MAP),
        "benchmark_now_iso": BENCHMARK_NOW.isoformat(),
        "benchmark_now_epoch": BENCHMARK_NOW_EPOCH,
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "ground_truth": truth,
    }
    save_state(state_path, payload)
    print(f"\n  Saved → {state_path}")
    print(f"\n{'=' * 60}")
    print("  SEED COMPLETE")
    print("  Next step: reset_workspace.py before each prompt run.")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
