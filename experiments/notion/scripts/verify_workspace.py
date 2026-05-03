#!/usr/bin/env python3
"""
verify_workspace.py  —  Hintas Notion Benchmark state verifier

Queries the live Notion workspace and asserts it matches the seeded state
recorded in the per-stack workspace_state_ids_<stack>.json. Intended to run
after reset_workspace.py and before a benchmark prompt session, as a fairness
gate proving each MCP stack starts from the same state.

Usage:
    export NOTION_TOKEN=secret_...   # or set HINTAS_TOKEN, etc. per stack
    python verify_workspace.py --stack notion                  # check; exit 1 on hard drift
    python verify_workspace.py --stack notion --report drift.json   # also write a JSON report
    python verify_workspace.py --stack notion --soft           # exit 0 even on hard drift

State-file and auth-token resolution come from notion.toml's
``state_file_template`` and the matching stack's ``token_env``.

Exit codes (contract expected by run_benchmark.py):
    0 — clean (no hard drift)
    1 — hard drift detected
    2 — structural / API failure (state file missing, auth, etc.)

Drift categories:
    hard — would bias the Hintas-MCP vs Notion-MCP comparison
    soft — informational; known limitation or agent-only state

Source of truth:
    When the loaded state file carries a ``ground_truth`` block (produced by
    seed_workspace.py post-seed snapshot), the verifier derives expected
    users, pages, databases (titles + property schemas), rows (titles +
    property values), and labelled blocks (plain_text) from that block, and
    applies the per-workspace ignore set. State files without ``ground_truth``
    fall back to the constants below — re-seed to upgrade.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from benchmarking.clock import BENCH_TZ, BENCHMARK_NOW
from benchmarking.config import load_platform, load_platform_env


def _resolve_stack_paths(stack: str) -> tuple[str, str]:
    """Resolve (state_file, token) for ``stack`` from notion.toml."""
    load_platform_env("notion")
    platform = load_platform("notion")
    stack_cfg = platform.stack(stack)
    state_p = platform.state_file_for(stack_cfg)
    if state_p is None:
        raise SystemExit("notion.toml must declare state_file_template")
    return str(state_p), os.environ.get(stack_cfg.token_env, "")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("NOTION_TOKEN", "")
BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# ---------------------------------------------------------------------------
# Fallback expected-state tables (used only when state['ground_truth'] is
# absent — i.e. legacy state files seeded before the snapshot was added).
# Live runs replace every dict below from the snapshot via
# derive_expected_from_truth().
# ---------------------------------------------------------------------------

EXPECTED_PAGES: dict[str, tuple[str, bool]] = {
    "P01_HINTAS_ROOT":        ("Hintas",                  False),
    "P02_TEAM_DIR":           ("Team Directory",          False),
    "P03_PROJECTS":           ("Projects",                False),
    "P04_TOMB3":              ("Tomb-3 Level Design",     False),
    "P05_LAUNCH26":           ("Launch 2026",             False),
    "P06_MEETING_NOTES_HOME": ("Meeting Notes",           False),
    "P07_PLAYTEST_ARCHIVE":   ("Playtest Archive",        False),
    "P09_PLAYTEST_A2":        ("Playtest — alpha round 2", False),
    "P10_PLAYTEST_A3":        ("Playtest — alpha round 3", True),
}

EXPECTED_DBS: dict[str, tuple[str, str]] = {
    "DB_BUGS":           ("Bugs",                "P03_PROJECTS"),
    "DB_TASKS":          ("Tasks",               "P03_PROJECTS"),
    "DB_PROJECTS":       ("Projects (catalog)",  "P03_PROJECTS"),
    "DB_MEETING_NOTES":  ("Meeting Notes",       "P06_MEETING_NOTES_HOME"),
}

EXPECTED_UNSHARED_PAGES: tuple[str, ...] = ("P08_LEADS_ONLY", "P11_LEADS_NOTES")
EXPECTED_UNSHARED_DBS: tuple[str, ...] = ("DB_PRESS_CONTACTS",)

EXPECTED_DB_SCHEMA: dict[str, dict[str, str]] = {
    "DB_BUGS": {
        "Title": "title", "Bug ID": "rich_text", "Severity": "select",
        "Status": "status", "Reporter": "people", "Assignee": "people",
        "Platform": "multi_select", "Filed": "date", "Related Task": "relation",
        "URL": "url",
    },
    "DB_TASKS": {
        "Task": "title", "Owner": "people", "Due": "date", "Status": "status",
        "Priority": "select", "Estimate": "number", "Tags": "multi_select",
        "Project": "relation",
    },
    "DB_PROJECTS": {
        "Name": "title", "Lead": "people", "Status": "status",
    },
    "DB_MEETING_NOTES": {
        "Title": "title", "Date": "date", "Attendees": "people", "Type": "select",
        "Follow-ups": "rich_text", "Action Items": "relation",
    },
}

EXPECTED_DB_OPTIONS: dict[str, dict[str, list[str]]] = {}

EXPECTED_ROW_LABELS: dict[str, list[str]] = {
    "DB_PROJECTS": ["PROJ_TOMB3", "PROJ_LAUNCH", "PROJ_OFFSITE"],
    "DB_TASKS": [
        "TASK_FIX_TILE_LOADER", "TASK_TOMB3_LIGHTING", "TASK_PRESS_LIST",
        "TASK_TRAILER_COPY", "TASK_BRAND_KIT", "TASK_BUG247_VERIFY",
        "TASK_CONCEPT_REVIEW", "TASK_CHANGELOG", "TASK_LISBON_LOGISTICS",
        "TASK_MIGRATE_INVENTORY", "TASK_RHEA_INPUT_REBIND", "TASK_QA_REGRESSION",
    ],
    "DB_BUGS": [
        "BUG230", "BUG231", "BUG244", "BUG245", "BUG246", "BUG247", "BUG248",
    ],
    "DB_MEETING_NOTES": [
        "MTG_TOMB3_REVIEW", "MTG_BUG247_TRIAGE", "MTG_LAUNCH_STANDUP",
        "MTG_ALL_HANDS", "MTG_QA_RETRO", "MTG_ENG_PLANNING",
        "MTG_PRESS_PREP", "MTG_LEADS_SYNC",
    ],
}

# Per-row expected property values (derived from ground_truth at run time;
# empty under the constants fallback because the snapshot is the only place
# row values are recorded).
EXPECTED_ROW_PROPS: dict[str, dict] = {}

# Per-block expected plain_text + type (derived from ground_truth).
EXPECTED_BLOCKS: dict[str, dict] = {}

# Expected page child counts (currently just P02_TEAM_DIR's pagination
# boundary at 11 children; populated from ground_truth).
EXPECTED_PAGE_CHILD_COUNTS: dict[str, int] = {"P02_TEAM_DIR": 11}

EXPECTED_ACTIVE_USERS: list[str] = ["U01MIRANDA", "U02JARED", "U03PINKMAN", "U04LAGOON",
                                    "U05CLAUDE", "U06DEVON", "U07RHEA", "U08TOMAS"]

# Per-workspace ignore set (populated from ground_truth.ignore).
IGNORE_USER_IDS: set[str] = set()
IGNORE_PAGE_IDS: set[str] = set()
IGNORE_DATABASE_IDS: set[str] = set()

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class NotionError(RuntimeError):
    def __init__(self, code: int, body: dict):
        self.status = code
        self.body = body
        super().__init__(f"HTTP {code} — {body.get('code')} — {body.get('message')}")

def _request(method: str, path: str, **kwargs) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, headers=HEADERS, **kwargs)
    if resp.status_code >= 400:
        try:
            body = resp.json()
        except Exception:
            body = {"message": resp.text}
        raise NotionError(resp.status_code, body)
    return resp.json() if resp.text else {}

def get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params or {})

def post(path: str, body: dict | None = None) -> dict:
    return _request("POST", path, json=body or {})

def paginate(path: str, body: dict | None = None, *, method: str = "POST", page_size: int = 100) -> list[dict]:
    out: list[dict] = []
    cursor: str | None = None
    while True:
        payload = dict(body or {})
        payload["page_size"] = page_size
        if cursor:
            payload["start_cursor"] = cursor
        if method == "POST":
            data = post(path, payload)
        else:
            data = get(path, payload)
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return out

# ---------------------------------------------------------------------------
# Drift collector
# ---------------------------------------------------------------------------

@dataclass
class Drift:
    hard: list[str] = field(default_factory=list)
    soft: list[str] = field(default_factory=list)

    def hard_add(self, msg: str) -> None:
        self.hard.append(msg)
        print(f"  [HARD] {msg}")

    def soft_add(self, msg: str) -> None:
        self.soft.append(msg)
        print(f"  [soft] {msg}")

    def info(self, msg: str) -> None:
        print(f"  [info] {msg}")

# ---------------------------------------------------------------------------
# Ground-truth derivation — replaces fallback EXPECTED_* tables with values
# pulled from the snapshot embedded in the state file.
# ---------------------------------------------------------------------------

def _plain_text(rt: list[dict]) -> str:
    return "".join(seg.get("plain_text", "") for seg in (rt or []))


def _normalize_live_property_schema(prop: dict) -> dict:
    """Same shape as seed_workspace._normalize_property_schema."""
    ptype = prop.get("type", "")
    out: dict = {"type": ptype}
    body = prop.get(ptype) or {}
    if ptype in ("select", "multi_select", "status"):
        out["options"] = sorted(o.get("name", "") for o in body.get("options", []))
    elif ptype == "relation":
        out["database_id"] = body.get("database_id", "")
    elif ptype == "number":
        out["format"] = body.get("format", "")
    return out


def _normalize_live_property_value(prop: dict) -> dict | None:
    """Mirrors seed_workspace._normalize_property_value (kept in sync)."""
    ptype = prop.get("type", "")
    body = prop.get(ptype)
    if ptype == "title":
        return {"type": ptype, "text": _plain_text(body)}
    if ptype == "rich_text":
        return {"type": ptype, "text": _plain_text(body)}
    if ptype == "select":
        return {"type": ptype, "name": (body or {}).get("name")}
    if ptype == "status":
        return {"type": ptype, "name": (body or {}).get("name")}
    if ptype == "multi_select":
        return {"type": ptype, "names": sorted(o.get("name", "") for o in (body or []))}
    if ptype == "people":
        return {"type": ptype, "user_ids": sorted(p.get("id", "") for p in (body or []))}
    if ptype == "relation":
        return {"type": ptype, "row_ids": sorted(r.get("id", "") for r in (body or []))}
    if ptype == "date":
        return {
            "type": ptype,
            "start": (body or {}).get("start"),
            "end": (body or {}).get("end"),
        }
    if ptype == "number":
        return {"type": ptype, "value": body}
    if ptype == "url":
        return {"type": ptype, "value": body}
    if ptype == "checkbox":
        return {"type": ptype, "value": bool(body)}
    if ptype in ("email", "phone_number"):
        return {"type": ptype, "value": body}
    return None


def derive_expected_from_truth(state: dict) -> bool:
    """
    Replace EXPECTED_* with values from ``state['ground_truth']``. Returns
    True when the snapshot was found and applied; False when the state file
    has no ground_truth and the verifier should use its constants.
    """
    truth = state.get("ground_truth") or {}
    if not truth:
        return False

    # --- pages ----------------------------------------------------------
    new_pages: dict[str, tuple[str, bool]] = {}
    for p in truth.get("pages", []):
        label = p.get("label")
        if not label:
            continue
        new_pages[label] = (p.get("title", ""), bool(p.get("archived")))
    if new_pages:
        EXPECTED_PAGES.clear()
        EXPECTED_PAGES.update(new_pages)

    # --- databases (title + parent label) -------------------------------
    new_dbs: dict[str, tuple[str, str]] = {}
    for d in truth.get("databases", []):
        label = d.get("label")
        if not label:
            continue
        new_dbs[label] = (d.get("title", ""), d.get("parent_label") or "")
    if new_dbs:
        EXPECTED_DBS.clear()
        EXPECTED_DBS.update(new_dbs)

    # --- db schema (property name → type, plus options where applicable) -
    new_schema: dict[str, dict[str, str]] = {}
    new_options: dict[str, dict[str, list[str]]] = {}
    for d in truth.get("databases", []):
        label = d.get("label")
        if not label:
            continue
        per_db: dict[str, str] = {}
        per_options: dict[str, list[str]] = {}
        for prop_name, prop_spec in (d.get("properties") or {}).items():
            ptype = prop_spec.get("type", "")
            per_db[prop_name] = ptype
            if ptype in ("select", "multi_select", "status"):
                per_options[prop_name] = list(prop_spec.get("options") or [])
        new_schema[label] = per_db
        if per_options:
            new_options[label] = per_options
    if new_schema:
        EXPECTED_DB_SCHEMA.clear()
        EXPECTED_DB_SCHEMA.update(new_schema)
    EXPECTED_DB_OPTIONS.clear()
    EXPECTED_DB_OPTIONS.update(new_options)

    # --- row labels (per db) and per-row property values ----------------
    new_row_labels: dict[str, list[str]] = {}
    new_row_props: dict[str, dict] = {}
    for r in truth.get("rows", []):
        label = r.get("label")
        db_label = r.get("db_label")
        if not label or not db_label:
            continue
        new_row_labels.setdefault(db_label, []).append(label)
        new_row_props[label] = {
            "db_label":   db_label,
            "row_id":     r.get("id"),
            "title":      r.get("title", ""),
            "archived":   bool(r.get("archived")),
            "properties": r.get("properties") or {},
        }
    if new_row_labels:
        EXPECTED_ROW_LABELS.clear()
        EXPECTED_ROW_LABELS.update(new_row_labels)
    EXPECTED_ROW_PROPS.clear()
    EXPECTED_ROW_PROPS.update(new_row_props)

    # --- blocks (label → expected type + plain_text) --------------------
    new_blocks: dict[str, dict] = {}
    for b in truth.get("blocks", []):
        label = b.get("label")
        if not label:
            continue
        new_blocks[label] = {
            "id":         b.get("id"),
            "type":       b.get("type", ""),
            "plain_text": b.get("plain_text", ""),
            "archived":   bool(b.get("archived")),
        }
    EXPECTED_BLOCKS.clear()
    EXPECTED_BLOCKS.update(new_blocks)

    # --- page child counts ---------------------------------------------
    counts = truth.get("page_child_counts") or {}
    if counts:
        EXPECTED_PAGE_CHILD_COUNTS.clear()
        EXPECTED_PAGE_CHILD_COUNTS.update({k: int(v) for k, v in counts.items()})

    # --- active users from snapshot -------------------------------------
    user_id_map = state.get("user_id_map") or {}
    bot_id = state.get("bot_id", "")
    snapshot_user_ids = {u["id"] for u in truth.get("users", []) if u.get("id")}
    new_active = []
    for label, real_id in user_id_map.items():
        if not real_id or real_id == bot_id or label == "U10AGENT":
            continue
        if label.startswith("U09"):  # revoked seed user (U09EMBER)
            continue
        if real_id in snapshot_user_ids:
            new_active.append(label)
    if new_active:
        EXPECTED_ACTIVE_USERS.clear()
        EXPECTED_ACTIVE_USERS.extend(sorted(new_active))

    # --- ignore set -----------------------------------------------------
    ignore = truth.get("ignore") or {}
    IGNORE_USER_IDS.clear()
    IGNORE_USER_IDS.update(ignore.get("user_ids") or [])
    IGNORE_PAGE_IDS.clear()
    IGNORE_PAGE_IDS.update(ignore.get("page_ids") or [])
    IGNORE_DATABASE_IDS.clear()
    IGNORE_DATABASE_IDS.update(ignore.get("database_ids") or [])

    return True

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_users(state: dict, drift: Drift) -> None:
    print("\n  -- users --")
    user_id_map = state.get("user_id_map", {})
    try:
        users = paginate("/users", method="GET")
    except NotionError as e:
        drift.hard_add(f"/users failed: {e}")
        return
    live_ids = {u["id"] for u in users}
    for label in EXPECTED_ACTIVE_USERS:
        expected_id = user_id_map.get(label)
        if not expected_id:
            drift.hard_add(f"{label} missing from state file (user_id_map)")
            continue
        if expected_id not in live_ids:
            drift.hard_add(f"{label} ({expected_id}) not in /users — was workspace access removed?")
    # U09EMBER must NOT be in /users (revoked)
    ember_id = user_id_map.get("U09EMBER")
    if ember_id and ember_id in live_ids:
        drift.hard_add("U09EMBER appears in /users — should be revoked")
    # Bot user
    bot_id = state.get("bot_id")
    if bot_id and bot_id not in live_ids:
        drift.hard_add(f"Bot user {bot_id} not in /users — token may be wrong")

def check_pages(state: dict, drift: Drift) -> None:
    print("\n  -- pages --")
    pmap = state.get("page_id_map", {})
    for label, (title, archived_expected) in EXPECTED_PAGES.items():
        pid = pmap.get(label)
        if not pid:
            drift.hard_add(f"{label} missing from state file (page_id_map)")
            continue
        if pid in IGNORE_PAGE_IDS:
            continue
        try:
            page = get(f"/pages/{pid}")
        except NotionError as e:
            if e.status == 404:
                drift.hard_add(f"{label} ({pid}) returns 404 — page deleted or unshared")
            else:
                drift.hard_add(f"{label} retrieve failed: {e}")
            continue
        cur_title = "".join(t.get("plain_text", "") for t in
                            (page.get("properties") or {}).get("title", {}).get("title", []))
        if cur_title != title:
            drift.hard_add(f"{label} title is {cur_title!r}, expected {title!r}")
        is_archived = bool(page.get("archived") or page.get("in_trash"))
        if is_archived != archived_expected:
            drift.hard_add(f"{label} archived={is_archived}, expected {archived_expected}")

def check_databases(state: dict, drift: Drift) -> None:
    print("\n  -- databases --")
    dmap = state.get("db_id_map", {})
    for label, (title, parent_label) in EXPECTED_DBS.items():
        did = dmap.get(label)
        if not did:
            drift.hard_add(f"{label} missing from state file (db_id_map)")
            continue
        if did in IGNORE_DATABASE_IDS:
            continue
        try:
            db = get(f"/databases/{did}")
        except NotionError as e:
            drift.hard_add(f"{label} retrieve failed: {e}")
            continue
        cur_title = "".join(t.get("plain_text", "") for t in db.get("title", []))
        if cur_title != title:
            drift.hard_add(f"{label} title is {cur_title!r}, expected {title!r}")
        live_props = db.get("properties") or {}
        for prop_name, prop_type in EXPECTED_DB_SCHEMA.get(label, {}).items():
            prop = live_props.get(prop_name)
            if not prop:
                drift.hard_add(f"{label}.{prop_name} property missing")
                continue
            if prop.get("type") != prop_type:
                drift.hard_add(f"{label}.{prop_name} type is {prop.get('type')!r}, expected {prop_type!r}")
        # Schema option drift (select / multi_select / status) — only for
        # ground-truth-derived runs that populated EXPECTED_DB_OPTIONS.
        for prop_name, expected_options in EXPECTED_DB_OPTIONS.get(label, {}).items():
            prop = live_props.get(prop_name)
            if not prop:
                continue
            ptype = prop.get("type")
            body = prop.get(ptype) or {}
            live_options = sorted(o.get("name", "") for o in (body.get("options") or []))
            missing = [o for o in expected_options if o not in live_options]
            extras  = [o for o in live_options if o not in expected_options]
            for o in missing:
                drift.hard_add(f"{label}.{prop_name} missing option {o!r}")
            for o in extras:
                # Extra options don't break grading on their own — soft.
                drift.soft_add(f"{label}.{prop_name} has extra option {o!r}")

def check_unshared_prerequisites(state: dict, drift: Drift) -> None:
    """Pre-seed entities (P08, P11, DB_PRESS_CONTACTS) must 404 to the integration."""
    print("\n  -- unshared prerequisites --")
    pmap = state.get("page_id_map", {})
    dmap = state.get("db_id_map", {})
    for label in EXPECTED_UNSHARED_PAGES:
        pid = pmap.get(label)
        if not pid:
            drift.hard_add(f"{label} missing from state — fill in prerequisites.local.json and reseed")
            continue
        try:
            get(f"/pages/{pid}")
            drift.hard_add(f"{label} ({pid}) IS visible to the integration; must be unshared")
        except NotionError as e:
            if e.status == 404:
                drift.info(f"{label} 404 — correct (not shared)")
            else:
                drift.hard_add(f"{label} unexpected error: {e}")
    for label in EXPECTED_UNSHARED_DBS:
        did = dmap.get(label)
        if not did:
            drift.hard_add(f"{label} missing from state — fill in prerequisites.local.json and reseed")
            continue
        try:
            get(f"/databases/{did}")
            drift.hard_add(f"{label} ({did}) IS visible to the integration; must be unshared")
        except NotionError as e:
            if e.status == 404:
                drift.info(f"{label} 404 — correct (not shared)")
            else:
                drift.hard_add(f"{label} unexpected error: {e}")

def check_rows(state: dict, drift: Drift) -> None:
    print("\n  -- database rows --")
    dmap = state.get("db_id_map", {})
    rmap = state.get("row_id_map", {})
    for db_label, expected_labels in EXPECTED_ROW_LABELS.items():
        did = dmap.get(db_label)
        if not did:
            continue  # already reported by check_databases
        try:
            rows = paginate(f"/databases/{did}/query")
        except NotionError as e:
            drift.hard_add(f"{db_label} query failed: {e}")
            continue
        live_ids = {r["id"] for r in rows}
        rows_by_id = {r["id"]: r for r in rows}
        seeded_ids = []
        for lbl in expected_labels:
            rid = rmap.get(lbl)
            if not rid:
                drift.hard_add(f"{lbl} missing from state file (row_id_map)")
                continue
            if rid not in live_ids:
                drift.hard_add(f"{lbl} ({rid}) absent from {db_label} — deleted or archived")
                continue
            seeded_ids.append(rid)
            row = rows_by_id.get(rid)
            if row and row.get("archived"):
                drift.hard_add(f"{lbl} is archived; expected active")

            # Property-value comparison (only when ground_truth populated
            # EXPECTED_ROW_PROPS for this label; under the constants
            # fallback, the dict is empty and this loop is a no-op).
            expected = EXPECTED_ROW_PROPS.get(lbl)
            if not expected or not row:
                continue
            check_row_properties(lbl, row, expected, drift)
        # Extra rows are soft drift (agent-added during a prompt run)
        extras = [r["id"] for r in rows if r["id"] not in set(seeded_ids) and not r.get("archived")]
        if extras:
            drift.soft_add(f"{db_label} has {len(extras)} extra unarchived row(s) — reset_workspace will archive")


def check_row_properties(label: str, live_row: dict, expected: dict, drift: Drift) -> None:
    """
    Compare a row's property values against the snapshot.

    Property-value drift is HARD when it could bias prompt grading (status,
    select, people, relation, multi_select, dates, number, url, checkbox).
    rich_text and title text drift is SOFT — Notion can't reset rich_text in
    place, so an edit by a previous prompt run can leave a stale value the
    reset script can't fully recover.
    """
    expected_props = expected.get("properties") or {}
    live_props = live_row.get("properties") or {}
    for name, exp_val in expected_props.items():
        live_prop = live_props.get(name)
        if live_prop is None:
            drift.hard_add(f"{label}.{name} property is missing on live row")
            continue
        live_norm = _normalize_live_property_value(live_prop)
        if live_norm is None:
            continue
        ptype = exp_val.get("type")
        if live_norm.get("type") != ptype:
            drift.hard_add(
                f"{label}.{name} type is {live_norm.get('type')!r}, expected {ptype!r}"
            )
            continue
        # Pull comparable subset for this property type.
        if ptype in ("title", "rich_text"):
            if live_norm.get("text") != exp_val.get("text"):
                # Notion rich_text edits aren't fully reversible by reset.
                drift.soft_add(
                    f"{label}.{name} text drift "
                    f"(live={live_norm.get('text')!r} expected={exp_val.get('text')!r})"
                )
        elif ptype in ("select", "status"):
            if live_norm.get("name") != exp_val.get("name"):
                drift.hard_add(
                    f"{label}.{name} {ptype}={live_norm.get('name')!r} "
                    f"expected {exp_val.get('name')!r}"
                )
        elif ptype == "multi_select":
            if live_norm.get("names") != exp_val.get("names"):
                drift.hard_add(
                    f"{label}.{name} multi_select={live_norm.get('names')} "
                    f"expected {exp_val.get('names')}"
                )
        elif ptype == "people":
            if live_norm.get("user_ids") != exp_val.get("user_ids"):
                drift.hard_add(
                    f"{label}.{name} people drift "
                    f"(live={live_norm.get('user_ids')} expected={exp_val.get('user_ids')})"
                )
        elif ptype == "relation":
            if live_norm.get("row_ids") != exp_val.get("row_ids"):
                drift.hard_add(
                    f"{label}.{name} relation drift "
                    f"(live={live_norm.get('row_ids')} expected={exp_val.get('row_ids')})"
                )
        elif ptype == "date":
            if (live_norm.get("start"), live_norm.get("end")) != (
                exp_val.get("start"), exp_val.get("end")
            ):
                drift.hard_add(
                    f"{label}.{name} date drift "
                    f"(live={live_norm.get('start')}/{live_norm.get('end')} "
                    f"expected={exp_val.get('start')}/{exp_val.get('end')})"
                )
        elif ptype in ("number", "url", "email", "phone_number", "checkbox"):
            if live_norm.get("value") != exp_val.get("value"):
                drift.hard_add(
                    f"{label}.{name} {ptype}={live_norm.get('value')!r} "
                    f"expected {exp_val.get('value')!r}"
                )


def check_blocks(state: dict, drift: Drift) -> None:
    print("\n  -- blocks --")
    pmap = state.get("page_id_map", {})
    bmap = state.get("block_id_map", {})

    # Page-child-count invariants from ground_truth (e.g. P02_TEAM_DIR
    # holds exactly 11 children to exercise the pagination boundary).
    for page_label, expected_n in EXPECTED_PAGE_CHILD_COUNTS.items():
        page_id = pmap.get(page_label)
        if not page_id:
            continue
        try:
            children = paginate(f"/blocks/{page_id}/children", method="GET")
            if len(children) != expected_n:
                drift.hard_add(
                    f"{page_label} has {len(children)} children, expected {expected_n}"
                )
        except NotionError as e:
            drift.hard_add(f"{page_label} children query failed: {e}")

    # Each labelled block must still resolve and (when ground_truth is
    # available) match the snapshot's type + plain_text.
    for label, bid in bmap.items():
        try:
            blk = get(f"/blocks/{bid}")
        except NotionError as e:
            if e.status == 404:
                drift.hard_add(f"Block {label} ({bid}) 404 — deleted")
            else:
                drift.soft_add(f"Block {label} retrieve failed: {e}")
            continue
        if blk.get("archived") or blk.get("in_trash"):
            drift.hard_add(f"Block {label} ({bid}) is archived")
            continue
        expected = EXPECTED_BLOCKS.get(label)
        if not expected:
            continue
        live_type = blk.get("type", "")
        if expected.get("type") and live_type != expected["type"]:
            drift.hard_add(
                f"Block {label} type={live_type!r} expected {expected['type']!r}"
            )
            continue
        body = blk.get(live_type) or {}
        live_text = _plain_text(body.get("rich_text") or []) if isinstance(body, dict) else ""
        if expected.get("plain_text") and live_text != expected["plain_text"]:
            # Block content edits don't bias entity-shape grading; report soft.
            drift.soft_add(
                f"Block {label} text drift "
                f"(live={live_text[:60]!r} expected={expected['plain_text'][:60]!r})"
            )

def check_bot(state: dict, drift: Drift) -> None:
    print("\n  -- bot --")
    try:
        me = get("/users/me")
    except NotionError as e:
        drift.hard_add(f"/users/me failed: {e}")
        return
    if me.get("type") != "bot":
        drift.hard_add(f"NOTION_TOKEN identifies as {me.get('type')!r}, not bot")
    expected_bot_id = state.get("bot_id")
    if expected_bot_id and me.get("id") != expected_bot_id:
        drift.hard_add(f"Bot id drifted: live={me.get('id')} vs state={expected_bot_id}")
    workspace_name = me.get("bot", {}).get("workspace_name", "")
    if workspace_name and "hintas" not in workspace_name.lower():
        drift.soft_add(f"workspace_name={workspace_name!r} does not contain 'hintas'")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global TOKEN, HEADERS

    parser = argparse.ArgumentParser(description="Verify Hintas Notion benchmark workspace state")
    parser.add_argument("--soft", action="store_true",
                        help="Exit 0 even when hard drift is detected")
    parser.add_argument("--report", default=None, help="Write a JSON drift report to this path")
    parser.add_argument("--stack", required=True,
                        help="Stack name (e.g. notion, hintas). Resolves the state file and "
                             "auth token from notion.toml.")
    parser.add_argument("--token", help="Notion integration token (overrides NOTION_TOKEN)")
    args = parser.parse_args()

    state_file, stack_token = _resolve_stack_paths(args.stack)

    if args.token:
        TOKEN = args.token
    elif stack_token:
        TOKEN = stack_token
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

    if not TOKEN:
        print("ERROR: Set NOTION_TOKEN env var or pass --token", file=sys.stderr)
        return 2

    if not os.path.exists(state_file):
        print(f"ERROR: state file not found: {state_file}", file=sys.stderr)
        return 2
    with open(state_file) as f:
        state = json.load(f)

    print(f"\n{'='*60}")
    print(f"  Hintas Notion Benchmark — Verifier")
    print(f"  State file: {state_file}")
    print(f"{'='*60}")

    used_truth = derive_expected_from_truth(state)
    if used_truth:
        truth = state.get("ground_truth") or {}
        print(
            f"  Ground-truth: {len(truth.get('users', []))} users, "
            f"{len(truth.get('pages', []))} pages, "
            f"{len(truth.get('databases', []))} dbs, "
            f"{len(truth.get('rows', []))} rows, "
            f"{len(truth.get('blocks', []))} labelled blocks; "
            f"{len(IGNORE_USER_IDS)} ignored users, "
            f"{len(IGNORE_PAGE_IDS)} ignored pages, "
            f"{len(IGNORE_DATABASE_IDS)} ignored dbs"
        )
    else:
        print("  ⚠️  state file has no ground_truth block — falling back to constants")
        print("     re-run seed_workspace.py to capture the augmented snapshot")

    drift = Drift()
    try:
        check_bot(state, drift)
        check_users(state, drift)
        check_pages(state, drift)
        check_databases(state, drift)
        check_unshared_prerequisites(state, drift)
        check_rows(state, drift)
        check_blocks(state, drift)
    except NotionError as e:
        print(f"\nERROR: structural failure during verify: {e}", file=sys.stderr)
        if args.report:
            os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
            with open(args.report, "w") as f:
                json.dump({"hard_count": len(drift.hard), "soft_count": len(drift.soft),
                           "hard": drift.hard, "soft": drift.soft,
                           "fatal": str(e)}, f, indent=2)
        return 2

    print(f"\n{'='*60}")
    print(f"  Hard drift: {len(drift.hard)}    Soft drift: {len(drift.soft)}")
    print(f"{'='*60}\n")

    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        report = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "hard_count": len(drift.hard),
            "soft_count": len(drift.soft),
            "hard": drift.hard,
            "soft": drift.soft,
            "used_ground_truth": used_truth,
        }
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Report → {args.report}")

    if drift.hard and not args.soft:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
