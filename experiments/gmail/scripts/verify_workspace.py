#!/usr/bin/env python3
"""
verify_workspace.py — Gmail benchmark workspace verifier.

Read-only diff between the live mailbox and the seeded ground_truth snapshot
written by ``seed_workspace.py``. Runs after ``reset_workspace.py`` and
before each prompt session as a fairness gate proving every stack starts
from identical state.

Drift severity:
    hard  — the live mailbox differs from ground_truth in a way that biases
            prompt grading (wrong thread labels, missing seeded entity, etc.)
    soft  — known-volatile fields (messagesTotal/threadsTotal counts drift
            naturally as Gmail recalculates; auto_forwarding state on
            mailboxes that never configured forwarding)

Usage:
    uv run python experiments/gmail/scripts/verify_workspace.py --stack gmail
    uv run python experiments/gmail/scripts/verify_workspace.py --stack gmail --report /tmp/drift.json
    uv run python experiments/gmail/scripts/verify_workspace.py --stack gmail --soft

Exit codes (contract for run_benchmark.py):
    0 → clean (no hard drift)
    1 → hard drift detected (unless --soft, which always returns 0)
    2 → structural failure (auth, state file missing, etc.)

The report JSON includes ``hard_count`` and ``soft_count`` so the orchestrator
can summarise drift across runs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Make sibling scripts/ modules importable when invoked directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from googleapiclient.errors import HttpError

import constants
import utils
from utils import (
    GROUND_TRUTH, build_service, build_substitution_map, load_state,
    load_users, log, resolve_state_file, section, subsection,
)


# ---------------------------------------------------------------------------
# Drift dataclass
# ---------------------------------------------------------------------------

@dataclass
class Drift:
    path: str
    severity: str  # "hard" or "soft"
    expected: object
    actual: object
    note: str = ""


DRIFTS: list[Drift] = []


def hard(path: str, expected, actual, note: str = "") -> None:
    DRIFTS.append(Drift(path=path, severity="hard", expected=expected, actual=actual, note=note))
    print(f"  [HARD] {path}: expected={expected!r}, actual={actual!r}"
          + (f" ({note})" if note else ""))


def soft(path: str, expected, actual, note: str = "") -> None:
    DRIFTS.append(Drift(path=path, severity="soft", expected=expected, actual=actual, note=note))
    print(f"  [soft] {path}: expected={expected!r}, actual={actual!r}"
          + (f" ({note})" if note else ""))


# ---------------------------------------------------------------------------
# Expected views derived from ground_truth
# ---------------------------------------------------------------------------

@dataclass
class Expected:
    owner_email: str = ""
    messages_total: int | None = None
    threads_total: int | None = None
    user_labels_by_name: dict[str, dict] = field(default_factory=dict)  # name → ground_truth entry
    threads_by_logical: dict[str, dict] = field(default_factory=dict)
    label_id_to_name: dict[str, str] = field(default_factory=dict)
    drafts_by_subject: dict[str, dict] = field(default_factory=dict)
    filters_by_signature: dict[tuple, dict] = field(default_factory=dict)
    send_as_addresses: set[str] = field(default_factory=set)
    primary_send_as: str = ""
    vacation: dict = field(default_factory=dict)
    auto_forwarding: dict = field(default_factory=dict)
    ignore_label_name_res: list[re.Pattern] = field(default_factory=list)


def derive_expected() -> Expected:
    exp = Expected()
    ws = GROUND_TRUTH.get("workspace", {}) or {}
    exp.owner_email = ws.get("owner_email", "")
    exp.messages_total = ws.get("messages_total")
    exp.threads_total = ws.get("threads_total")

    for lbl in GROUND_TRUTH.get("labels", []) or []:
        if lbl.get("id"):
            exp.label_id_to_name[lbl["id"]] = lbl["name"]
        if lbl.get("type") == "user":
            exp.user_labels_by_name[lbl["name"]] = lbl

    for t in GROUND_TRUTH.get("threads", []) or []:
        exp.threads_by_logical[t["logical_id"]] = t

    for d in GROUND_TRUTH.get("drafts", []) or []:
        if d.get("subject"):
            exp.drafts_by_subject[d["subject"]] = d

    for f in GROUND_TRUTH.get("filters", []) or []:
        sig = (
            (f.get("criteria", {}).get("from") or "").lower(),
            (f.get("criteria", {}).get("subject") or "").lower(),
            tuple(sorted(f.get("action", {}).get("addLabelIds", []) or [])),
        )
        exp.filters_by_signature[sig] = f

    for a in GROUND_TRUTH.get("send_as_aliases", []) or []:
        addr = (a.get("send_as_email") or "").lower()
        exp.send_as_addresses.add(addr)
        if a.get("is_primary"):
            exp.primary_send_as = addr

    exp.vacation = GROUND_TRUTH.get("vacation_responder", {}) or {}
    exp.auto_forwarding = GROUND_TRUTH.get("auto_forwarding", {}) or {}

    ignore = GROUND_TRUTH.get("ignore", {}) or {}
    exp.ignore_label_name_res = [re.compile(p) for p in ignore.get("label_name_patterns", []) or []]
    return exp


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_profile(exp: Expected) -> None:
    subsection("profile")
    svc = utils.service()
    try:
        profile = svc.users().getProfile(userId="me").execute()
    except HttpError as e:
        hard("profile", "getProfile success", str(e), note="API error")
        return
    actual_email = profile.get("emailAddress", "")
    if actual_email.lower() != exp.owner_email.lower():
        hard("profile.email_address", exp.owner_email, actual_email)
    else:
        log(f"emailAddress={actual_email}")
    actual_msgs = profile.get("messagesTotal")
    actual_threads = profile.get("threadsTotal")
    if exp.messages_total is not None and actual_msgs != exp.messages_total:
        soft("profile.messages_total", exp.messages_total, actual_msgs,
             note="natural drift; Gmail recomputes")
    if exp.threads_total is not None and actual_threads != exp.threads_total:
        soft("profile.threads_total", exp.threads_total, actual_threads,
             note="natural drift; Gmail recomputes")


def check_labels(exp: Expected) -> None:
    subsection("labels")
    svc = utils.service()
    try:
        data = svc.users().labels().list(userId="me").execute()
    except HttpError as e:
        hard("labels", "list ok", str(e), note="API error")
        return
    current = {lbl["name"]: lbl for lbl in data.get("labels", []) or []}

    # Every expected user label must be present.
    for name, exp_lbl in exp.user_labels_by_name.items():
        if name not in current:
            hard(f"labels.user.{name}", "present", "missing")
            continue
        cur = current[name]
        if cur.get("type") != "user":
            hard(f"labels.user.{name}.type", "user", cur.get("type"))

    # Extras (current user-defined labels not in expected set) are hard drift
    # unless they match an ignore pattern.
    for name, lbl in current.items():
        if lbl.get("type") != "user":
            continue
        if name in exp.user_labels_by_name:
            continue
        if any(rx.search(name) for rx in exp.ignore_label_name_res):
            log(f"extra label {name!r} matches ignore pattern — soft")
            soft(f"labels.user.{name}", "absent", "present", note="matches ignore pattern")
            continue
        hard(f"labels.user.{name}", "absent", "present", note="extra user label")

    log(f"checked {len(exp.user_labels_by_name)} expected, {len(current)} live labels")


def check_threads(exp: Expected) -> None:
    subsection("threads")
    svc = utils.service()
    thread_id_map = utils.STATE.get("thread_id_map", {}) or {}

    # Single labels.list call up front — used to map current live label ids
    # to names (labels may have been re-created with new ids by reset).
    try:
        live_labels = svc.users().labels().list(userId="me").execute().get("labels", []) or []
    except HttpError:
        live_labels = []
    live_id_to_name = {lbl["id"]: lbl["name"] for lbl in live_labels}

    def _to_names(ids: set[str], id_to_name: dict[str, str]) -> set[str]:
        out: set[str] = set()
        for i in ids:
            if i in constants.SYSTEM_LABELS:
                out.add(i)
            else:
                out.add(id_to_name.get(i, i))
        return out

    for logical_id, exp_thread in exp.threads_by_logical.items():
        real_id = thread_id_map.get(logical_id)
        if not real_id:
            hard(f"threads.{logical_id}.id", "in state", "missing")
            continue
        try:
            t = svc.users().threads().get(
                userId="me", id=real_id, format="minimal",
            ).execute()
        except HttpError as e:
            status = getattr(e, "resp", None) and e.resp.status
            if status == 404:
                hard(f"threads.{logical_id}", "present", "missing", note="404")
            else:
                hard(f"threads.{logical_id}", "get ok", str(e), note="API error")
            continue

        actual_label_ids: set[str] = set()
        for m in t.get("messages", []) or []:
            actual_label_ids.update(m.get("labelIds", []) or [])
        expected_label_ids = set(exp_thread.get("label_ids", []) or [])

        expected_names = _to_names(expected_label_ids, exp.label_id_to_name)
        actual_names = _to_names(actual_label_ids, live_id_to_name)

        # CATEGORY_* labels are classifier-managed and can flip between runs.
        # Filter them symmetrically — neither presence nor absence counts as
        # hard drift unless ground_truth pinned a specific category.
        def _filter_categories(names: set[str], pinned: set[str]) -> set[str]:
            return {
                n for n in names
                if not (n.startswith("CATEGORY_") and n != "CATEGORY_PERSONAL"
                        and n not in pinned)
            }

        pinned_categories = {n for n in expected_names if n.startswith("CATEGORY_")}
        expected_filtered = _filter_categories(expected_names, pinned_categories)
        actual_filtered = _filter_categories(actual_names, pinned_categories)

        missing = expected_filtered - actual_filtered
        extra = actual_filtered - expected_filtered
        if missing or extra:
            hard(
                f"threads.{logical_id}.labels",
                sorted(expected_filtered),
                sorted(actual_filtered),
                note=f"missing={sorted(missing) or '∅'} extra={sorted(extra) or '∅'}",
            )
        else:
            log(f"{logical_id} labels OK")


def check_drafts(exp: Expected) -> None:
    subsection("drafts")
    svc = utils.service()
    try:
        live = svc.users().drafts().list(userId="me", maxResults=500).execute().get("drafts", []) or []
    except HttpError as e:
        hard("drafts", "list ok", str(e), note="API error")
        return
    live_subjects: dict[str, dict] = {}
    for d in live:
        try:
            full = svc.users().drafts().get(
                userId="me", id=d["id"], format="metadata",
            ).execute()
        except HttpError:
            continue
        headers = {h["name"].lower(): h["value"]
                   for h in (full.get("message", {}).get("payload", {}).get("headers", []) or [])}
        subject = headers.get("subject", "")
        live_subjects[subject] = d

    for subject, exp_draft in exp.drafts_by_subject.items():
        if subject not in live_subjects:
            hard(f"drafts[{subject!r}]", "present", "missing")
        else:
            log(f"draft {subject!r} OK")

    for subject in live_subjects:
        if subject not in exp.drafts_by_subject:
            hard(f"drafts[{subject!r}]", "absent", "present", note="extra draft")


def check_filters(exp: Expected) -> None:
    subsection("filters")
    svc = utils.service()
    try:
        live = svc.users().settings().filters().list(userId="me").execute().get("filter", []) or []
    except HttpError as e:
        hard("filters", "list ok", str(e), note="API error")
        return

    def _sig(f: dict) -> tuple:
        return (
            (f.get("criteria", {}).get("from") or "").lower(),
            (f.get("criteria", {}).get("subject") or "").lower(),
            tuple(sorted(f.get("action", {}).get("addLabelIds", []) or [])),
        )

    live_sigs = {_sig(f): f for f in live}

    for sig in exp.filters_by_signature:
        if sig not in live_sigs:
            hard("filters[signature]", sig, "missing")
        else:
            log(f"filter ({sig[0]!r}) OK")

    for sig in live_sigs:
        if sig not in exp.filters_by_signature:
            hard("filters[signature]", "absent", sig, note="extra filter")


def check_send_as(exp: Expected) -> None:
    subsection("send-as aliases")
    svc = utils.service()
    try:
        aliases = svc.users().settings().sendAs().list(userId="me").execute().get("sendAs", []) or []
    except HttpError as e:
        hard("send_as", "list ok", str(e), note="API error")
        return
    live_addrs = {(a.get("sendAsEmail") or "").lower(): a for a in aliases}

    primary_present = any(a.get("isPrimary") for a in aliases)
    if not primary_present:
        hard("send_as.primary", "present", "missing")

    extras = set(live_addrs) - exp.send_as_addresses
    for addr in extras:
        hard(f"send_as.{addr}", "absent", "present", note="extra alias")


def check_vacation(exp: Expected) -> None:
    subsection("vacation responder")
    svc = utils.service()
    try:
        vac = svc.users().settings().getVacation(userId="me").execute()
    except HttpError as e:
        hard("vacation", "get ok", str(e), note="API error")
        return
    actual_enabled = bool(vac.get("enableAutoReply"))
    expected_enabled = bool(exp.vacation.get("enable_auto_reply", False))
    if actual_enabled != expected_enabled:
        hard("vacation.enable_auto_reply", expected_enabled, actual_enabled)
    else:
        log(f"enableAutoReply={actual_enabled}")


def check_auto_forwarding(exp: Expected) -> None:
    subsection("auto-forwarding")
    svc = utils.service()
    try:
        af = svc.users().settings().getAutoForwarding(userId="me").execute()
    except HttpError as e:
        # 400 is common on mailboxes that never configured forwarding; treat as soft.
        status = getattr(e, "resp", None) and e.resp.status
        if status in (400, 404):
            soft("auto_forwarding", "configured", "not configured",
                 note="Gmail returns 4xx on getAutoForwarding for never-configured mailboxes")
        else:
            hard("auto_forwarding", "get ok", str(e), note="API error")
        return
    expected_enabled = bool(exp.auto_forwarding.get("enabled", False))
    actual_enabled = bool(af.get("enabled"))
    if actual_enabled != expected_enabled:
        hard("auto_forwarding.enabled", expected_enabled, actual_enabled)
    else:
        log(f"enabled={actual_enabled}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Gmail benchmark mailbox matches the seeded snapshot")
    parser.add_argument("--token",
                        help="Refresh token override (otherwise read from <STACK>_TOKEN env).")
    parser.add_argument("--state-file",
                        help="Explicit state-file path (overrides --stack default).")
    parser.add_argument("--stack", required=True,
                        help="Stack name from gmail.toml (e.g. 'gmail' or 'hintas').")
    parser.add_argument("--report", type=Path,
                        help="Write a JSON drift report to this path.")
    parser.add_argument("--soft", action="store_true",
                        help="Exit 0 even on hard drift (still records counts in the report).")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing, exit 0 instead of 2.")
    args = parser.parse_args()

    build_service(args.stack, refresh_token=args.token)

    print(f"\n{'=' * 60}")
    print("  Gmail Benchmark — Workspace Verifier")
    print(f"  Stack: {args.stack}")
    print(f"{'=' * 60}")

    state_path = resolve_state_file(args.state_file, args.stack)
    if not load_state(state_path, allow_missing=args.allow_missing_state):
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({
                "hard_count": 0,
                "soft_count": 0,
                "drifts": [],
                "note": "state file missing; --allow-missing-state",
            }, indent=2))
        return 0

    users = load_users()
    build_substitution_map(users, owner_email=utils.STATE.get("owner_email"))

    exp = derive_expected()

    section("Drift checks")
    check_profile(exp)
    check_labels(exp)
    check_threads(exp)
    check_drafts(exp)
    check_filters(exp)
    check_send_as(exp)
    check_vacation(exp)
    check_auto_forwarding(exp)

    hard_count = sum(1 for d in DRIFTS if d.severity == "hard")
    soft_count = sum(1 for d in DRIFTS if d.severity == "soft")

    print(f"\n{'=' * 60}")
    print(f"  Hard drift: {hard_count}")
    print(f"  Soft drift: {soft_count}")
    print(f"{'=' * 60}\n")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "stack": args.stack,
            "state_file": state_path,
            "hard_count": hard_count,
            "soft_count": soft_count,
            "drifts": [asdict(d) for d in DRIFTS],
        }, indent=2, default=str))
        print(f"  Report written → {args.report}")

    if args.soft:
        return 0
    return 1 if hard_count else 0


if __name__ == "__main__":
    sys.exit(main())
