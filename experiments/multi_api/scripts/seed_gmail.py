#!/usr/bin/env python3
"""
seed_gmail.py — multi-API benchmark Gmail-surface seeder.

Builds the acting agent's mailbox (persona Miranda) into the
multi-API seed snapshot: a handful of inbound threads, one short two-sided
partnership negotiation thread, and a triage set — all anchored relative to
``benchmarking.clock.BENCHMARK_NOW``.

Standalone: unlike the single-surface ``experiments/gmail`` scripts this does
NOT resolve a stack from a platform manifest. It reads its OAuth credentials
straight from the environment (``GMAIL_TOKEN`` refresh token plus
``GMAIL_CLIENT_ID`` / ``GMAIL_CLIENT_SECRET``) and inlines a minimal Gmail
Discovery service builder. The mailbox the refresh token authenticates against
IS the acting agent; all seeded inbound mail lands there via ``messages.insert``
(userId='me').

Usage:
    uv run python experiments/multi_api/scripts/seed_gmail.py --verify
    uv run python experiments/multi_api/scripts/seed_gmail.py

State is written to ``workspace_state_gmail.json`` next to this script. The
payload embeds a ``ground_truth`` block — a snapshot of every seeded entity —
that prompts and graders reference as the answer key.

benchmark_now is anchored to 2026-04-19T10:00:00-07:00 via benchmarking.clock.
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Any

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

# Every seed message carries a Message-ID in this domain so the wipe phase can
# scope itself to seed-origin threads and leave any operator mail untouched.
SEED_MSGID_DOMAIN = "seed.multiapi.local"

# Module-level dry-run mirror (kept in lockstep with common.DRY_RUN).
DRY_RUN: bool = False

# Logical → real id maps, populated during seeding.
THREAD_ID_MAP: dict[str, str] = {}
MESSAGE_ID_MAP: dict[str, str] = {}
LABEL_ID_MAP: dict[str, str] = {}  # no user labels seeded — stays empty.


# ---------------------------------------------------------------------------
# Fixture — each entry is one Gmail thread; messages insert oldest-first and
# chain In-Reply-To/References within the thread.
# ---------------------------------------------------------------------------

# No user labels are pre-seeded. The 'Needs-Triage' label is created by a
# prompt and removed on reset.
SEEDED_LABELS: list[str] = []

SEEDED_THREADS: list[dict] = [
    {
        "logical_id": "TH_EXPORT",
        "messages": [
            {
                "logical_id": "TH_EXPORT_m1",
                "from": "Dana Whitfield <dana@northwind-systems.example>",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Urgent: export failing in production",
                "offset_hours": -6,
                "labelIds": ["INBOX", "UNREAD"],
                "body": (
                    "Hi team — our nightly CSV export has been failing in "
                    "production since the 02:00 run. We get a 500 with "
                    "'pipeline timeout'. This is blocking our finance close. "
                    "Can someone look ASAP?\n\n— Dana, Northwind Systems"
                ),
            },
        ],
    },
    {
        "logical_id": "TH_SSO",
        "messages": [
            {
                "logical_id": "TH_SSO_m1",
                "from": "{{EMAIL_U07RHEA}}",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Please add SSO docs",
                "offset_hours": -30,
                # READ (no UNREAD) so it stays out of the triage count.
                "labelIds": ["INBOX"],
                "body": (
                    "Can we get SSO setup docs added to the help center? "
                    "Two customers asked this week. Thanks!\n\n— {{NAME_U07RHEA}}"
                ),
            },
        ],
    },
    {
        "logical_id": "TH_PARTNERSHIP",
        "messages": [
            {
                "logical_id": "TH_PARTNERSHIP_m1",
                "from": "Mara Lindqvist <mara@brightpath.example>",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Partnership terms",
                "offset_hours": -72,
                "labelIds": ["INBOX"],
                "body": (
                    "Sharing our proposed partnership terms: 18-month term, "
                    "20% revenue share, co-marketing in Q3. Let me know your "
                    "thoughts.\n\n— Mara, BrightPath"
                ),
            },
            {
                "logical_id": "TH_PARTNERSHIP_m2",
                "from": "{{EMAIL_U01MIRANDA}}",
                "to": "mara@brightpath.example",
                "subject": "Re: Partnership terms",
                "offset_hours": -50,
                "labelIds": ["SENT"],
                "body": (
                    "Thanks Mara. 20% works if we cap co-marketing spend at "
                    "$15k. We'd want a 12-month initial term with auto-renew."
                ),
            },
            {
                "logical_id": "TH_PARTNERSHIP_m3",
                "from": "Mara Lindqvist <mara@brightpath.example>",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Re: Partnership terms",
                "offset_hours": -26,
                "labelIds": ["INBOX"],
                "body": (
                    "Agreed on the $15k cap and the 12-month term. Decisions: "
                    "legal drafts the contract by next Friday. Action items — "
                    "you send the logo pack, I'll send the partner contact "
                    "sheet."
                ),
            },
        ],
    },
    {
        "logical_id": "TH_PRIYA",
        "messages": [
            {
                "logical_id": "TH_PRIYA_m1",
                "from": "{{EMAIL_NEWHIRE}}",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Excited to join Hintas!",
                "offset_hours": -40,
                # READ — the new-hire inbound contact.
                "labelIds": ["INBOX"],
                "body": (
                    "Hi! I'm really looking forward to starting. Is there "
                    "anything I should set up before day one?\n\n— {{NAME_NEWHIRE}}"
                ),
            },
        ],
    },
    {
        "logical_id": "TH_TRIAGE1",
        "messages": [
            {
                "logical_id": "TH_TRIAGE1_m1",
                "from": "{{EMAIL_U05CLAUDE}}",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Brand kit needs your sign-off",
                "offset_hours": -20,
                "labelIds": ["INBOX", "UNREAD"],
                "body": (
                    "The updated brand kit is ready for your sign-off before "
                    "we send it to print. — {{NAME_U05CLAUDE}}"
                ),
            },
        ],
    },
    {
        "logical_id": "TH_TRIAGE2",
        "messages": [
            {
                "logical_id": "TH_TRIAGE2_m1",
                "from": "{{EMAIL_U06DEVON}}",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Build broke on main",
                "offset_hours": -10,
                "labelIds": ["INBOX", "UNREAD"],
                "body": (
                    "Main is red after the last merge — looks like the "
                    "analytics module. Can you take a look? — {{NAME_U06DEVON}}"
                ),
            },
        ],
    },
    {
        "logical_id": "TH_TRIAGE3",
        "messages": [
            {
                "logical_id": "TH_TRIAGE3_m1",
                "from": "{{EMAIL_U08TOMAS}}",
                "to": "{{EMAIL_U01MIRANDA}}",
                "subject": "Review request: pricing tiers",
                "offset_hours": -5,
                "labelIds": ["INBOX", "UNREAD"],
                "body": (
                    "Could you review the proposed pricing tiers doc today? "
                    "— {{NAME_U08TOMAS}}"
                ),
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Standalone auth + service builder (mirrors the reference build_service())
# ---------------------------------------------------------------------------

SERVICE = None


def build_service(
    stack: str = "baseline",
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
):
    """Build a Gmail Discovery resource from env-supplied OAuth credentials.

    Credentials resolve from the stack-prefixed env vars
    (``BASELINE_``/``HINTAS_`` + ``GMAIL_TOKEN`` / ``GMAIL_CLIENT_ID`` /
    ``GMAIL_CLIENT_SECRET``). Any explicit value passed in (``--token`` /
    ``--client-id`` / ``--client-secret``) overrides the lookup. Exits with a
    friendly message when any of the three credentials is missing.
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
    message_id = make_msgid(domain=SEED_MSGID_DOMAIN)
    em["Message-ID"] = message_id
    if in_reply_to:
        em["In-Reply-To"] = in_reply_to
    if references:
        em["References"] = " ".join(references)
    em.set_content(subst(msg["body"]))

    raw = base64.urlsafe_b64encode(em.as_bytes()).decode("ascii")
    return raw, message_id


# ---------------------------------------------------------------------------
# Auth / owner identity
# ---------------------------------------------------------------------------

def verify_owner() -> dict[str, Any]:
    """Resolve the mailbox identity via users.getProfile.

    Returns the ``users.getProfile`` payload. The mailbox owner is the acting
    agent; warn (do NOT hard-fail) if it doesn't match the agent persona's
    email, since this script is standalone and the operator may point it at any
    authenticated mailbox.
    """
    section("0. Resolving mailbox owner")
    svc = service()
    profile = svc.users().getProfile(userId="me").execute()
    owner_email = profile.get("emailAddress", "")
    print(f"  Authenticated as: {owner_email}")
    print(
        f"  Mailbox totals: {profile.get('messagesTotal', '?')} messages, "
        f"{profile.get('threadsTotal', '?')} threads, "
        f"historyId={profile.get('historyId', '?')}"
    )
    expected = email_of(agent_logical_id())
    if expected and owner_email.lower() != expected.lower():
        warn(
            f"owner mailbox {owner_email!r} != agent persona {expected!r} — "
            f"proceeding anyway (standalone seeder)"
        )
    else:
        log(f"owner matches agent persona {owner_email}")
    return profile


# ---------------------------------------------------------------------------
# Wipe phase — scope deletes to seed-origin threads so reruns don't duplicate
# ---------------------------------------------------------------------------

MAX_WIPE_PASSES = 50


def _is_seed_thread(svc, thread_id: str) -> bool:
    """True when every message in the thread carries a seed-domain Message-ID.

    Seed messages all stamp ``@SEED_MSGID_DOMAIN`` in their Message-ID header,
    so we can recognise our own seeded mail and leave operator mail alone.
    """
    try:
        t = svc.users().threads().get(
            userId="me", id=thread_id, format="metadata",
            metadataHeaders=["Message-ID"],
        ).execute()
    except HttpError as e:
        warn(f"threads.get {thread_id} failed during wipe scan: {e}")
        return False
    msgs = t.get("messages", []) or []
    if not msgs:
        return False
    for m in msgs:
        headers = {
            h["name"].lower(): h["value"]
            for h in (m.get("payload", {}).get("headers", []) or [])
        }
        if f"@{SEED_MSGID_DOMAIN}" not in headers.get("message-id", ""):
            return False
    return True


def wipe_seed_threads() -> None:
    """Permanently delete prior seed-origin threads so reruns don't duplicate.

    Scoped to threads whose messages all carry the seed Message-ID domain —
    operator mail in the mailbox is left untouched. Re-lists after each pass
    since Gmail's index lags behind deletes; bounded at ``MAX_WIPE_PASSES`` and
    breaks when a pass makes no progress.
    """
    section("1a. Wiping prior seed threads")
    if DRY_RUN:
        log("Would delete every prior seed-origin thread")
        return
    svc = service()
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
            if not tid or not _is_seed_thread(svc, tid):
                continue
            try:
                svc.users().threads().delete(userId="me", id=tid).execute()
                pass_deleted += 1
            except HttpError as e:
                if getattr(e, "resp", None) and e.resp.status == 404:
                    continue
                warn(f"threads.delete {tid} failed: {e}")
        deleted += pass_deleted
        if pass_deleted == 0:
            break
    else:
        warn(f"wipe_seed_threads hit MAX_WIPE_PASSES={MAX_WIPE_PASSES}")
    if deleted:
        log(f"Deleted {deleted} seed thread(s)")
    else:
        log("No prior seed threads present")


def wipe_drafts() -> None:
    """Delete every draft so reruns and prompt-created drafts don't linger."""
    section("1b. Wiping all drafts")
    if DRY_RUN:
        log("Would delete every draft")
        return
    svc = service()
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
            break
    else:
        warn(f"wipe_drafts hit MAX_WIPE_PASSES={MAX_WIPE_PASSES}")
    if deleted:
        log(f"Deleted {deleted} draft(s)")
    else:
        log("No drafts present")


# ---------------------------------------------------------------------------
# Import seeded threads
# ---------------------------------------------------------------------------

def import_threads() -> None:
    section("2. Importing seeded threads")
    svc = service()
    for thread in SEEDED_THREADS:
        thread_id: str | None = None
        prev_message_id: str | None = None
        references: list[str] = []

        for i, msg in enumerate(thread["messages"]):
            raw, message_id = _build_raw(
                msg,
                in_reply_to=prev_message_id,
                references=list(references) if references else None,
            )
            label_ids = list(msg.get("labelIds", []))
            body: dict[str, Any] = {"raw": raw, "labelIds": label_ids}
            if thread_id:
                body["threadId"] = thread_id

            if DRY_RUN:
                log(
                    f"{thread['logical_id']} msg {i + 1}/{len(thread['messages'])}: "
                    f"would insert (subject={subst(msg['subject'])!r}, "
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
            # honors labelIds verbatim (INBOX/UNREAD/SENT) — essential for
            # predictable benchmark seed state. internalDateSource="dateHeader"
            # anchors the timestamp to our Date header (offset from benchmark_now).
            try:
                resp = svc.users().messages().insert(
                    userId="me",
                    internalDateSource="dateHeader",
                    body=body,
                ).execute()
            except HttpError as e:
                warn(f"{thread['logical_id']} msg {i + 1}: insert failed: {e}")
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


# ---------------------------------------------------------------------------
# Ground truth capture
# ---------------------------------------------------------------------------

def capture_ground_truth(profile: dict[str, Any]) -> dict:
    section("3. Capturing ground truth")
    svc = service()
    truth: dict[str, Any] = {
        "workspace": {
            "owner_email": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal"),
            "threads_total": profile.get("threadsTotal"),
            "history_id": profile.get("historyId"),
        },
        "labels": [],
        "threads": [],
        "messages": [],
        "ignore": {
            "label_name_patterns": ["^CATEGORY_"],
            "label_ids": [],
        },
    }

    # Labels — capture every label so the verifier can flag drift.
    labels_data = svc.users().labels().list(userId="me").execute()
    for lbl in labels_data.get("labels", []) or []:
        truth["labels"].append({
            "id": lbl.get("id"),
            "name": lbl.get("name"),
            "type": lbl.get("type"),
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
            headers = {
                h["name"].lower(): h["value"]
                for h in (m.get("payload", {}).get("headers", []) or [])
            }
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
        # Tag each captured message with its logical id so reset can restore
        # the per-message label snapshot.
        logical_by_real = {
            v: k for k, v in MESSAGE_ID_MAP.items()
        }
        for tm in thread_messages:
            tm["logical_id"] = logical_by_real.get(tm["id"], "")
        truth["messages"].extend(thread_messages)
    log(f"Captured {len(truth['threads'])} threads / {len(truth['messages'])} messages")

    return truth


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN

    parser = argparse.ArgumentParser(
        description="Seed the multi-API benchmark Gmail surface"
    )
    parser.add_argument(
        "--verify", "--dry-run", dest="verify", action="store_true",
        help="Dry-run: walk the seed plan, log every step, mutate nothing.",
    )
    parser.add_argument("--token", help="Refresh token override (else BASELINE_/HINTAS_GMAIL_TOKEN).")
    parser.add_argument("--client-id", help="OAuth client id override (else BASELINE_/HINTAS_GMAIL_CLIENT_ID).")
    parser.add_argument("--client-secret", help="OAuth client secret override (else BASELINE_/HINTAS_GMAIL_CLIENT_SECRET).")
    parser.add_argument("--state-file", help="Explicit state-file path (overrides the default).")
    add_stack_arg(parser)
    args = parser.parse_args()

    DRY_RUN = args.verify
    set_dry_run(args.verify)
    build_service(
        stack=args.stack,
        refresh_token=args.token,
        client_id=args.client_id,
        client_secret=args.client_secret,
    )

    print(f"\n{'=' * 60}")
    print("  Multi-API Benchmark — Gmail Surface Seeder")
    print(f"  Mode:  {'DRY RUN (verify)' if DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'=' * 60}")

    load_users()
    profile = verify_owner()
    owner_email = profile.get("emailAddress", "")
    build_substitution_map(owner_email=owner_email)

    wipe_seed_threads()
    wipe_drafts()
    import_threads()

    if DRY_RUN:
        print(f"\n{'=' * 60}")
        print("  VERIFY COMPLETE — no mutations performed")
        print(f"{'=' * 60}\n")
        return 0

    truth = capture_ground_truth(profile)
    state_path = resolve_state_file(args.state_file, "gmail", args.stack)
    payload = {
        "owner_email": owner_email,
        "thread_id_map": dict(THREAD_ID_MAP),
        "message_id_map": dict(MESSAGE_ID_MAP),
        "label_id_map": dict(LABEL_ID_MAP),
        "benchmark_now_iso": BENCHMARK_NOW.isoformat(),
        "benchmark_now_epoch": BENCHMARK_NOW_EPOCH,
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "ground_truth": truth,
    }
    save_state(state_path, payload)

    print(f"\n{'=' * 60}")
    print("  SEED COMPLETE")
    print("  This is a manual / seed-only step. Run reset_gmail.py before each")
    print("  prompt run to restore the mailbox to this snapshot.")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
