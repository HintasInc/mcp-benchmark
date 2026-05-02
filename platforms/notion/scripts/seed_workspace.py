#!/usr/bin/env python3
"""
seed_workspace.py  —  Hintas Notion Benchmark v1

Seeds (or verifies) every entity defined in platforms/notion/state/workspace_state.md:
  page hierarchy P02..P07, P09, P10
  databases DB_BUGS, DB_TASKS, DB_PROJECTS, DB_MEETING_NOTES
    (DB_PRESS_CONTACTS is created pre-seed by the operator and NOT shared
     to the integration; see prerequisites.md.)
  database rows with property values (incl. people, relations, dates, mentions)
  block trees with rich-text mentions, callouts, code, toggles, to_do, bullets
  page-level + block-level comments
  archived state for P10_PLAYTEST_A3

Usage:
    export NOTION_TOKEN=secret_<integration token>   # or HINTAS_TOKEN, etc. per stack
    python seed_workspace.py --stack notion            # full seed (idempotent — reruns safely)
    python seed_workspace.py --stack hintas --verify   # dry-run: report what's missing, don't mutate
    python seed_workspace.py --stack notion --token TOK  # override env var

State-file path, prereq-file path, and auth-token env var are all resolved
from notion.toml (``state_file_template``, ``prereq_file_template``, and the
stack's ``token_env``).

Pre-seed prerequisites (one-time, see prerequisites.md):
  * Workspace, users, and integration are provisioned in the Notion UI.
  * U09EMBER is invited and then revoked; the operator records her user_id.
  * P08_LEADS_ONLY ("🔒 Leads-only") and its child P11_LEADS_NOTES are created
    as workspace-parented pages and NOT shared to the integration.
  * DB_PRESS_CONTACTS is created as an empty database NOT shared to the
    integration.
  * The IDs above are written to the per-stack
    platforms/notion/scripts/prerequisites_<stack>.local.json file before this
    script runs. The seeder verifies they resolve as expected (404 to the
    integration; absent from listUsers).

Notion API limits this script does not try to work around:
  * Author attribution — the integration is the author of every seeded row,
    block, and comment. The benchmark grading reflects this (single-token
    Scenario A, same as Slack).
  * Backdating created_time / last_edited_time — Notion stamps real wall-clock.
    Date-window prompts grade the seeded `Date`/`Filed`/`Embargo Date`/`Due`
    properties (which we DO write deterministically).
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from benchmarking.clock import BENCH_TZ, BENCHMARK_NOW
from benchmarking.config import load_platform, load_platform_env


def _resolve_stack_paths(stack: str) -> tuple[str, str, str]:
    """Resolve (state_file, prereq_file, token) for ``stack`` from notion.toml."""
    load_platform_env("notion")
    platform = load_platform("notion")
    stack_cfg = platform.stack(stack)
    state_p = platform.state_file_for(stack_cfg)
    prereq_p = platform.prereq_file_for(stack_cfg)
    if state_p is None or prereq_p is None:
        raise SystemExit("notion.toml must declare state_file_template and prereq_file_template")
    return str(state_p), str(prereq_p), os.environ.get(stack_cfg.token_env, "")

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

DRY_RUN = False
SCRIPT_DIR = os.path.dirname(__file__)
STATE_PATH: str = ""  # set in main() from notion.toml's state_file_template

# Populated as seeding progresses.
USER_ID_MAP: dict[str, str] = {}        # logical → real Notion user UUID
PAGE_ID_MAP: dict[str, str] = {}        # P01_HINTAS_ROOT, P02_TEAM_DIR, ...
DB_ID_MAP: dict[str, str] = {}          # DB_BUGS, DB_TASKS, ...
ROW_ID_MAP: dict[str, str] = {}         # BUG247, TASK_FIX_TILE_LOADER, ...
BLOCK_ID_MAP: dict[str, str] = {}       # B01..B46
COMMENT_ID_MAP: dict[str, str] = {}     # CMT01..CMT05

BOT_ID: str = ""
WORKSPACE_NAME: str = ""

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

def log(msg: str) -> None:
    print(f"  {'[DRY]' if DRY_RUN else '[OK ]'} {msg}")

def warn(msg: str) -> None:
    print(f"  [WARN] {msg}")

def err(msg: str) -> None:
    print(f"  [ERR ] {msg}", file=sys.stderr)

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
        body.setdefault("_request", {"method": method, "url": url})
        raise NotionError(resp.status_code, body)
    return resp.json() if resp.text else {}

def get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params or {})

def post(path: str, body: dict | None = None) -> dict:
    return _request("POST", path, json=body or {})

def patch(path: str, body: dict | None = None) -> dict:
    return _request("PATCH", path, json=body or {})

def paginate(path: str, body: dict | None = None, *, method: str = "POST",
             page_size: int = 100) -> list[dict]:
    """Walk a Notion paginated endpoint to completion. Returns concatenated results."""
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
# Rich-text builders
# ---------------------------------------------------------------------------

def rt_text(content: str, *, bold: bool = False, italic: bool = False) -> dict:
    return {
        "type": "text",
        "text": {"content": content, "link": None},
        "annotations": {
            "bold": bold, "italic": italic,
            "strikethrough": False, "underline": False, "code": False,
            "color": "default",
        },
    }

def rt_mention_user(user_id: str) -> dict:
    return {"type": "mention", "mention": {"type": "user", "user": {"id": user_id}}}

def rt_mention_page(page_id: str) -> dict:
    return {"type": "mention", "mention": {"type": "page", "page": {"id": page_id}}}

def rt_mention_date(start: str, end: str | None = None) -> dict:
    date_obj = {"start": start, "end": end}
    return {"type": "mention", "mention": {"type": "date", "date": date_obj}}

def rt(*segments: dict) -> list[dict]:
    return list(segments)

# ---------------------------------------------------------------------------
# Pre-seed prerequisites (operator-managed)
#
# Notion's API can't create the following from an integration token, so the
# operator must create them in the UI once and record the IDs in the per-stack
# prerequisites_<stack>.local.json file (path comes from notion.toml's
# prereq_file_template):
#   * P08_LEADS_ONLY     — workspace-parented page, NOT shared to integration
#   * P11_LEADS_NOTES    — child page of P08_LEADS_ONLY
#   * DB_PRESS_CONTACTS  — empty database NOT shared to integration
#   * U09EMBER           — invited then revoked; user_id captured before revoke
# The seeder verifies each: the three pages/db must 404 to the integration,
# and Ember must be absent from /users.
# ---------------------------------------------------------------------------

PREREQ_PATH: str = ""  # set in main() from notion.toml's prereq_file_template

PREREQ_KEYS_PAGES = ("P08_LEADS_ONLY", "P11_LEADS_NOTES")
PREREQ_KEYS_DBS = ("DB_PRESS_CONTACTS",)
PREREQ_KEYS_USERS = ("U09EMBER",)
PREREQ_KEYS_ALL = PREREQ_KEYS_PAGES + PREREQ_KEYS_DBS + PREREQ_KEYS_USERS

PREREQUISITES: dict[str, str] = {}

def _resolve_prereq_path() -> str:
    if not os.path.exists(PREREQ_PATH):
        raise SystemExit(f"prerequisites file not found: {PREREQ_PATH}")
    return PREREQ_PATH

def load_prerequisites() -> None:
    section("Pre-seed prerequisites")
    path = _resolve_prereq_path()
    with open(path) as f:
        data = json.load(f)
    print(f"  [config] Loaded prerequisites from {path}")
    missing = [k for k in PREREQ_KEYS_ALL if not data.get(k)]
    if missing:
        err(f"prerequisites file is missing IDs for: {missing}")
        err(f"Fill in {path} per prerequisites.md, then rerun.")
        sys.exit(1)
    PREREQUISITES.update({k: data[k] for k in PREREQ_KEYS_ALL})
    for k in PREREQ_KEYS_PAGES:
        PAGE_ID_MAP[k] = data[k]
    for k in PREREQ_KEYS_DBS:
        DB_ID_MAP[k] = data[k]
    for k in PREREQ_KEYS_USERS:
        USER_ID_MAP[k] = data[k]
    for k in PREREQ_KEYS_ALL:
        log(f"{k} → {data[k]}")

def verify_prerequisites_unshared() -> None:
    """The pages/database in PREREQUISITES must NOT be visible to the integration."""
    section("Pre-seed prerequisites — access boundary")
    failures: list[str] = []
    for label in PREREQ_KEYS_PAGES:
        pid = PREREQUISITES[label]
        try:
            get(f"/pages/{pid}")
            failures.append(f"{label} ({pid}) IS visible to the integration — must be unshared")
        except NotionError as e:
            if e.status == 404:
                log(f"{label} returns 404 to the integration (correct)")
            else:
                failures.append(f"{label} unexpected error: {e}")
    for label in PREREQ_KEYS_DBS:
        did = PREREQUISITES[label]
        try:
            get(f"/databases/{did}")
            failures.append(f"{label} ({did}) IS visible to the integration — must be unshared")
        except NotionError as e:
            if e.status == 404:
                log(f"{label} returns 404 to the integration (correct)")
            else:
                failures.append(f"{label} unexpected error: {e}")
    if failures:
        for msg in failures:
            err(msg)
        err("Open Notion → page/database → Connections → remove 'Hintas Agent', then rerun.")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Step 0 — Auth + bot identity
# ---------------------------------------------------------------------------

def verify_auth() -> tuple[str, str]:
    """Returns (bot_id, workspace_name). Aborts on failure."""
    section("0. Verifying auth")
    me = get("/users/me")
    if me.get("type") != "bot":
        err(f"NOTION_TOKEN is for a {me.get('type')!r} user, not an integration bot. Aborting.")
        sys.exit(1)
    bot_id = me["id"]
    workspace_name = me.get("bot", {}).get("workspace_name", "")
    print(f"  Authenticated as bot: {me.get('name')} ({bot_id})")
    print(f"  Workspace: {workspace_name!r}")
    if workspace_name and "hintas" not in workspace_name.lower():
        warn(f"Workspace name does not look like 'Hintas' — double-check you're hitting the right workspace.")
    return bot_id, workspace_name

# ---------------------------------------------------------------------------
# Step 1 — Resolve users by email
# ---------------------------------------------------------------------------

_LOCAL_EMAIL_PATH = os.path.join(SCRIPT_DIR, "users.local.json")
_SAMPLE_EMAIL_PATH = os.path.join(SCRIPT_DIR, "users.json")

def _load_email_map() -> dict[str, str]:
    if os.path.exists(_LOCAL_EMAIL_PATH):
        path = _LOCAL_EMAIL_PATH
    elif os.path.exists(_SAMPLE_EMAIL_PATH):
        path = _SAMPLE_EMAIL_PATH
    else:
        raise SystemExit("users.json not found in platforms/notion/scripts/ — cannot resolve user emails")
    with open(path) as f:
        raw = json.load(f)
    if raw and all(isinstance(v, str) for v in raw.values()):
        emails = raw
    else:
        emails = {logical_id: entry.get("email", "") for logical_id, entry in raw.items()}
    print(f"  [config] Loaded user emails from {os.path.basename(path)}")
    return emails

def resolve_users(bot_id: str) -> None:
    """Populate USER_ID_MAP via /users (paginated). Logical IDs map by email.

    Aborts if any expected active user is missing, if Pinkman's display name is
    not 'Pinkman', or if U09EMBER is still present (i.e. revoke step skipped).
    """
    section("1. Resolving users")
    emails = _load_email_map()
    by_email = {v.lower(): k for k, v in emails.items()}

    all_users = paginate("/users", method="GET")
    live_user_ids: set[str] = set()
    pinkman_name: str | None = None
    found_emails: set[str] = set()
    for u in all_users:
        live_user_ids.add(u["id"])
        if u.get("type") == "person":
            email = (u.get("person") or {}).get("email", "").lower()
            logical = by_email.get(email)
            if logical:
                USER_ID_MAP[logical] = u["id"]
                found_emails.add(email)
                if logical == "U03PINKMAN":
                    pinkman_name = u.get("name", "")
                log(f"{logical} → {u['id']}  ({email})")

    USER_ID_MAP["U10AGENT"] = bot_id
    log(f"U10AGENT → {bot_id}  (this integration's bot user)")

    expected_active = {"U01MIRANDA", "U02JARED", "U03PINKMAN", "U04LAGOON",
                       "U05CLAUDE", "U06DEVON", "U07RHEA", "U08TOMAS"}
    missing_active = [m for m in expected_active if m not in USER_ID_MAP]
    if missing_active:
        err(f"These active users are missing from /users: {missing_active}")
        err("Invite them via Notion settings → Members and rerun.")
        sys.exit(1)

    if pinkman_name != "Pinkman":
        err(f"U03PINKMAN display name is {pinkman_name!r}; expected 'Pinkman'.")
        err("Notion settings → Members → edit Saul Rivera → display name 'Pinkman'.")
        sys.exit(1)

    ember_id = USER_ID_MAP.get("U09EMBER")
    if ember_id and ember_id in live_user_ids:
        err(f"U09EMBER ({ember_id}) is still present in /users; expected revoked.")
        err("Notion settings → Members → remove ember@hintas.co, then rerun.")
        sys.exit(1)
    log("U09EMBER absent from /users (correct: revoked).")

def uid(logical: str) -> str | None:
    return USER_ID_MAP.get(logical)

def people_value(logical_ids: list[str]) -> dict:
    """Build a `people` property value, skipping unknown logical ids with a warning."""
    refs: list[dict] = []
    for logical in logical_ids:
        real = uid(logical)
        if not real:
            warn(f"Skipping {logical} in people prop — not in USER_ID_MAP")
            continue
        refs.append({"object": "user", "id": real})
    return {"people": refs}

# ---------------------------------------------------------------------------
# Step 2 — Find the root page (must be pre-shared by the operator)
# ---------------------------------------------------------------------------

ROOT_PAGE_TITLE = "Hintas"

def find_root_page() -> str:
    section("2. Locating the Hintas root page")
    results = post("/search", {
        "query": ROOT_PAGE_TITLE,
        "filter": {"value": "page", "property": "object"},
    }).get("results", [])
    candidates = []
    for r in results:
        title = _read_title(r)
        if title.strip().lower() == ROOT_PAGE_TITLE.lower():
            candidates.append(r)
    if not candidates:
        err(f"No page titled {ROOT_PAGE_TITLE!r} is shared to this integration.")
        err("Manual step: open the Hintas workspace, share the top-level Hintas page to the integration, then rerun.")
        sys.exit(1)
    # Prefer a workspace-parented top-level page; otherwise take the first.
    workspace_parented = [r for r in candidates if r.get("parent", {}).get("type") == "workspace"]
    chosen = (workspace_parented or candidates)[0]
    page_id = chosen["id"]
    PAGE_ID_MAP["P01_HINTAS_ROOT"] = page_id
    log(f"P01_HINTAS_ROOT → {page_id}")
    return page_id

def _read_title(obj: dict) -> str:
    """Extract the title plain_text from a page or database object."""
    if obj.get("object") == "database":
        return "".join(t.get("plain_text", "") for t in obj.get("title", []))
    props = obj.get("properties") or {}
    for v in props.values():
        if v.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in v.get("title", []))
    return ""

# ---------------------------------------------------------------------------
# Step 3 — Page hierarchy
# ---------------------------------------------------------------------------

PAGES_SPEC = [
    # (label, parent_label, title, icon_emoji)
    ("P02_TEAM_DIR",            "P01_HINTAS_ROOT",      "Team Directory",       "👥"),
    ("P03_PROJECTS",            "P01_HINTAS_ROOT",      "Projects",             "📁"),
    ("P04_TOMB3",               "P03_PROJECTS",         "Tomb-3 Level Design",  "🗿"),
    ("P05_LAUNCH26",            "P03_PROJECTS",         "Launch 2026",          "🚀"),
    ("P06_MEETING_NOTES_HOME",  "P01_HINTAS_ROOT",      "Meeting Notes",        "📝"),
    ("P07_PLAYTEST_ARCHIVE",    "P01_HINTAS_ROOT",      "Playtest Archive",     "📦"),
    ("P09_PLAYTEST_A2",         "P07_PLAYTEST_ARCHIVE", "Playtest — alpha round 2", None),
    ("P10_PLAYTEST_A3",         "P07_PLAYTEST_ARCHIVE", "Playtest — alpha round 3", None),
]

def _find_child_page_by_title(parent_id: str, title: str) -> str | None:
    """Return id of an existing child page (or row) with the exact title, else None."""
    blocks = paginate(f"/blocks/{parent_id}/children", method="GET")
    for b in blocks:
        if b.get("type") == "child_page" and b.get("child_page", {}).get("title") == title:
            return b["id"]
    return None

def create_pages() -> None:
    section("3. Creating page hierarchy")
    for label, parent_label, title, icon in PAGES_SPEC:
        parent_id = PAGE_ID_MAP.get(parent_label)
        if not parent_id:
            warn(f"Parent {parent_label} not yet known — skipping {label}")
            continue
        existing = _find_child_page_by_title(parent_id, title)
        if existing:
            PAGE_ID_MAP[label] = existing
            log(f"{label} ('{title}') already exists → {existing}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create under {parent_label})")
            continue
        body = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": {"title": {"title": [rt_text(title)]}},
        }
        if icon:
            body["icon"] = {"type": "emoji", "emoji": icon}
        page = post("/pages", body)
        PAGE_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{title}') → {page['id']}")
        time.sleep(0.15)

# ---------------------------------------------------------------------------
# Step 4 — Database schemas
# ---------------------------------------------------------------------------

def db_schema_bugs() -> dict:
    return {
        "Title":        {"title": {}},
        "Bug ID":       {"rich_text": {}},
        "Severity":     {"select": {"options": [
            {"name": "Low",     "color": "gray"},
            {"name": "Medium",  "color": "yellow"},
            {"name": "High",    "color": "orange"},
            {"name": "Blocker", "color": "red"},
        ]}},
        "Status":       {"status": {}},  # options patched in configure_status_options()
        "Reporter":     {"people": {}},
        "Assignee":     {"people": {}},
        "Platform":     {"multi_select": {"options": [
            {"name": "macOS",   "color": "blue"},
            {"name": "Windows", "color": "purple"},
            {"name": "Linux",   "color": "green"},
            {"name": "Switch",  "color": "red"},
        ]}},
        "Filed":        {"date": {}},
        "URL":          {"url": {}},
        # Related Task is added as a relation later, after DB_TASKS exists.
    }

def db_schema_tasks() -> dict:
    return {
        "Task":     {"title": {}},
        "Owner":    {"people": {}},
        "Due":      {"date": {}},
        "Status":   {"status": {}},  # options patched in configure_status_options()
        "Priority": {"select": {"options": [
            {"name": "P0", "color": "red"},
            {"name": "P1", "color": "orange"},
            {"name": "P2", "color": "yellow"},
            {"name": "P3", "color": "default"},
        ]}},
        "Estimate": {"number": {"format": "number"}},
        "Tags":     {"multi_select": {"options": [
            {"name": "eng",             "color": "blue"},
            {"name": "design",          "color": "purple"},
            {"name": "qa",              "color": "green"},
            {"name": "marketing",       "color": "pink"},
            {"name": "launch-blocker",  "color": "red"},
        ]}},
        # Project relation added after DB_PROJECTS exists.
    }

def db_schema_projects() -> dict:
    return {
        "Name":   {"title": {}},
        "Lead":   {"people": {}},
        "Status": {"status": {}},  # UI step
    }

def db_schema_meeting_notes() -> dict:
    return {
        "Title":      {"title": {}},
        "Date":       {"date": {}},
        "Attendees":  {"people": {}},
        "Type":       {"select": {"options": [
            {"name": "standup",        "color": "blue"},
            {"name": "design-review",  "color": "purple"},
            {"name": "retro",          "color": "green"},
            {"name": "all-hands",      "color": "orange"},
        ]}},
        "Follow-ups": {"rich_text": {}},
        # Action Items relation → DB_TASKS, added after both exist.
    }

DATABASES_SPEC = [
    # (label, parent_label, title, description, schema_fn)
    ("DB_BUGS",           "P03_PROJECTS",         "Bugs",
     "Active and resolved bugs across all platforms.", db_schema_bugs),
    ("DB_TASKS",          "P03_PROJECTS",         "Tasks",
     "Engineering and design work.", db_schema_tasks),
    ("DB_PROJECTS",       "P03_PROJECTS",         "Projects (catalog)",
     "Project catalog used as a relation target by Tasks.", db_schema_projects),
    ("DB_MEETING_NOTES",  "P06_MEETING_NOTES_HOME", "Meeting Notes",
     "Recurring syncs, design reviews, retros.", db_schema_meeting_notes),
    # DB_PRESS_CONTACTS is created by the operator pre-seed (not shared to the
    # integration); see prerequisites.md and load_prerequisites().
]

def _find_child_database_by_title(parent_id: str, title: str) -> str | None:
    blocks = paginate(f"/blocks/{parent_id}/children", method="GET")
    for b in blocks:
        if b.get("type") == "child_database" and b.get("child_database", {}).get("title") == title:
            return b["id"]
    return None

def create_databases() -> None:
    section("4. Creating databases")
    for label, parent_label, title, description, schema_fn in DATABASES_SPEC:
        parent_id = PAGE_ID_MAP.get(parent_label)
        if not parent_id:
            warn(f"Parent {parent_label} unknown — skipping {label}")
            continue
        existing = _find_child_database_by_title(parent_id, title)
        if existing:
            DB_ID_MAP[label] = existing
            log(f"{label} ('{title}') already exists → {existing}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create under {parent_label})")
            continue
        body = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "title": [rt_text(title)],
            "description": [rt_text(description)],
            "properties": schema_fn(),
        }
        db = post("/databases", body)
        DB_ID_MAP[label] = db["id"]
        log(f"Created {label} ('{title}') → {db['id']}")
        time.sleep(0.2)

STATUS_OPTIONS_SPEC = {
    "DB_BUGS":     ["Open", "In Progress", "Fixed", "Won't Fix"],
    "DB_TASKS":    ["Backlog", "Up Next", "In Progress", "Done"],
    "DB_PROJECTS": ["Active", "On hold", "Done"],
}

def configure_status_options() -> None:
    """
    Notion forces a default set of status options ('Not started' / 'In progress'
    / 'Done') at database creation. PATCH each database to align its Status
    options with the benchmark spec so subsequent row writes don't fail with
    'Status option X does not exist'.
    """
    section("4c. Configuring Status property options")
    if DRY_RUN:
        for label, names in STATUS_OPTIONS_SPEC.items():
            log(f"Would set {label}.Status options → {names}")
        return
    for label, target_names in STATUS_OPTIONS_SPEC.items():
        db_id = DB_ID_MAP.get(label)
        if not db_id:
            warn(f"{label} missing — skipping status configuration")
            continue
        try:
            db = get(f"/databases/{db_id}")
        except NotionError as e:
            warn(f"{label} retrieve failed: {e}")
            continue
        existing = (db.get("properties") or {}).get("Status", {}).get("status", {}).get("options", [])
        existing_names = [o.get("name") for o in existing]
        if set(existing_names) >= set(target_names):
            log(f"{label}.Status options already include spec ({existing_names})")
            continue
        body = {"properties": {"Status": {"status": {
            "options": [{"name": n} for n in target_names]
        }}}}
        try:
            patch(f"/databases/{db_id}", body)
            log(f"{label}.Status options → {target_names}")
        except NotionError as e:
            err(f"{label}.Status options PATCH failed: {e}")
            sys.exit(1)
        time.sleep(0.2)


def add_relation_properties() -> None:
    """Patch in cross-database relations after every database exists."""
    section("4b. Wiring relation properties")
    if DRY_RUN:
        log("Would add relation properties: Bugs.Related Task → Tasks; Tasks.Project → Projects; MeetingNotes.Action Items → Tasks")
        return
    targets = [
        ("DB_BUGS",          "Related Task", "DB_TASKS",     "single_property"),
        ("DB_TASKS",         "Project",      "DB_PROJECTS",  "single_property"),
        ("DB_MEETING_NOTES", "Action Items", "DB_TASKS",     "single_property"),
    ]
    for src_label, prop_name, dst_label, rel_kind in targets:
        src_id = DB_ID_MAP.get(src_label)
        dst_id = DB_ID_MAP.get(dst_label)
        if not (src_id and dst_id):
            warn(f"Cannot wire {src_label}.{prop_name} — missing source or target db")
            continue
        # Read current schema; skip if already present.
        db = get(f"/databases/{src_id}")
        if prop_name in (db.get("properties") or {}):
            log(f"{src_label}.{prop_name} already wired")
            continue
        body = {"properties": {prop_name: {
            "relation": {"database_id": dst_id, "type": rel_kind, rel_kind: {}}
        }}}
        try:
            patch(f"/databases/{src_id}", body)
            log(f"Wired {src_label}.{prop_name} → {dst_label}")
        except NotionError as e:
            warn(f"Failed to wire {src_label}.{prop_name}: {e}")

# ---------------------------------------------------------------------------
# Step 5 — Seed database rows
# ---------------------------------------------------------------------------

# Days offset relative to BENCHMARK_NOW. Negative = past, positive = future.
def date_at(days_offset: float) -> str:
    """Date-only ISO string (YYYY-MM-DD)."""
    return (BENCHMARK_NOW + timedelta(days=days_offset)).date().isoformat()

def datetime_at(days_offset: float, hour: int, minute: int) -> str:
    """Full ISO with PT offset, used for Meeting Notes Date property."""
    base = (BENCHMARK_NOW + timedelta(days=days_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base.isoformat()

def date_value(start: str, end: str | None = None) -> dict:
    inner = {"start": start}
    if end:
        inner["end"] = end
    return {"date": inner}

def select_value(name: str) -> dict:
    return {"select": {"name": name}}

def status_value(name: str) -> dict:
    return {"status": {"name": name}}

def multi_select_value(names: list[str]) -> dict:
    return {"multi_select": [{"name": n} for n in names]}

def rich_text_value(segments: list[dict]) -> dict:
    return {"rich_text": segments}

def title_value(text: str) -> dict:
    return {"title": [rt_text(text)]}

def number_value(n: float | int | None) -> dict:
    return {"number": n}

def url_value(url: str | None) -> dict:
    return {"url": url}

def relation_value(row_labels: list[str]) -> dict:
    refs = []
    for lbl in row_labels:
        rid = ROW_ID_MAP.get(lbl)
        if rid:
            refs.append({"id": rid})
        else:
            warn(f"Relation target {lbl} not yet seeded; skipping")
    return {"relation": refs}

# --- DB_PROJECTS rows -------------------------------------------------------
PROJECTS_ROWS = [
    # (label, name, lead_logical, status_name)
    ("PROJ_TOMB3",   "Tomb-3",         "U01MIRANDA", "Active"),
    ("PROJ_LAUNCH",  "Launch 2026",    "U04LAGOON",  "Active"),
    ("PROJ_OFFSITE", "Lisbon offsite", "U05CLAUDE",  "On hold"),
]

def seed_projects() -> None:
    section("5a. Seeding DB_PROJECTS rows")
    db_id = DB_ID_MAP.get("DB_PROJECTS")
    if not db_id:
        warn("DB_PROJECTS missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Name")
    for label, name, lead, status_name in PROJECTS_ROWS:
        if name in existing:
            ROW_ID_MAP[label] = existing[name]
            log(f"{label} ('{name}') already exists → {existing[name]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{name}') MISSING (would create)")
            continue
        props = {
            "Name": title_value(name),
            "Lead": people_value([lead]),
            "Status": status_value(status_name),
        }
        page = post("/pages", {
            "parent": {"database_id": db_id},
            "properties": props,
        })
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{name}') → {page['id']}")
        time.sleep(0.15)

# --- DB_TASKS rows ----------------------------------------------------------
TASKS_ROWS = [
    # (label, task, owner, due_offset, status, priority, estimate, tags, project_label)
    ("TASK_FIX_TILE_LOADER",   "Fix async tile loader chunk drop",   "U06DEVON",   +2,  "In progress", "P0", 2, ["eng","launch-blocker"],  "PROJ_TOMB3"),
    ("TASK_TOMB3_LIGHTING",    "Polish tomb-3 lighting passes B & C","U01MIRANDA", +4,  "In progress", "P1", 3, ["design"],                "PROJ_TOMB3"),
    ("TASK_PRESS_LIST",        "Finalize press contact list",        "U04LAGOON",  +3,  "Up Next",     "P1", 1, ["marketing","launch-blocker"], "PROJ_LAUNCH"),
    ("TASK_TRAILER_COPY",      "Write final trailer copy",           "U04LAGOON",  +2,  "In progress", "P0", 1, ["marketing","launch-blocker"], "PROJ_LAUNCH"),
    ("TASK_BRAND_KIT",         "Brand-kit handoff to PR firm",       "U01MIRANDA", -2,  "In progress", "P1", 1, ["marketing","design"],    "PROJ_LAUNCH"),
    ("TASK_BUG247_VERIFY",     "Verify BUG-247 fix on macOS 14.4",   "U08TOMAS",   +3,  "Up Next",     "P0", 1, ["qa","launch-blocker"],   "PROJ_TOMB3"),
    ("TASK_CONCEPT_REVIEW",    "Concept review session — tomb-3",    "U05CLAUDE",  -4,  "Done",        "P2", 1, ["design"],                "PROJ_TOMB3"),
    ("TASK_CHANGELOG",         "Draft alpha-build changelog",        "U02JARED",   +7,  "Backlog",     "P2", 1, ["eng"],                   "PROJ_LAUNCH"),
    ("TASK_LISBON_LOGISTICS",  "Book Lisbon offsite flights",        "U04LAGOON", +26,  "Backlog",     "P3", 2, [],                        "PROJ_OFFSITE"),
    ("TASK_MIGRATE_INVENTORY", "Migrate inventory schema to v3",     "U06DEVON",  +12,  "Backlog",     "P2", 5, ["eng"],                   "PROJ_TOMB3"),
    ("TASK_RHEA_INPUT_REBIND", "Input rebind UI polish",             "U07RHEA",   +11,  "Backlog",     "P2", 2, ["eng"],                   "PROJ_TOMB3"),
    ("TASK_QA_REGRESSION",     "Run regression suite on alpha",      "U03PINKMAN", +5,  "Up Next",     "P1", 2, ["qa","launch-blocker"],   "PROJ_LAUNCH"),
]

def seed_tasks() -> None:
    section("5b. Seeding DB_TASKS rows")
    db_id = DB_ID_MAP.get("DB_TASKS")
    if not db_id:
        warn("DB_TASKS missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Task")
    for (label, task, owner, due_off, status, prio, est, tags, project) in TASKS_ROWS:
        if task in existing:
            ROW_ID_MAP[label] = existing[task]
            log(f"{label} ('{task}') already exists → {existing[task]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{task}') MISSING (would create)")
            continue
        props = {
            "Task":     title_value(task),
            "Owner":    people_value([owner]),
            "Due":      date_value(date_at(due_off)),
            "Status":   status_value(status),
            "Priority": select_value(prio),
            "Estimate": number_value(est),
            "Tags":     multi_select_value(tags),
            "Project":  relation_value([project]),
        }
        page = post("/pages", {
            "parent": {"database_id": db_id},
            "properties": props,
        })
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{task}') → {page['id']}")
        time.sleep(0.15)

# --- DB_BUGS rows -----------------------------------------------------------
BUGS_ROWS = [
    # (label, title, bug_id, severity, status, reporter, assignee, platforms, filed_offset, related_task, url)
    ("BUG245", "Audio desync after cutscene",                          "BUG-245", "Medium",  "In progress", "U08TOMAS",   "U06DEVON", ["macOS","Windows"],          -11, None,                      None),
    ("BUG246", "Main-menu flicker on launch",                          "BUG-246", "Low",     "Open",        "U03PINKMAN", None,       ["macOS"],                    -13, None,                      None),
    ("BUG247", "Save-file corruption on macOS",                        "BUG-247", "Blocker", "In progress", "U03PINKMAN", "U06DEVON", ["macOS"],                     -6, "TASK_FIX_TILE_LOADER",    "https://ci.hintas.co/builds/842"),
    ("BUG248", "Tomb-3 door collider blocks player on revisit",        "BUG-248", "High",    "Open",        "U03PINKMAN", "U07RHEA",  ["macOS","Windows"],           -4, None,                      None),
    ("BUG230", "Settings dialog scrollbar overlap",                    "BUG-230", "Low",     "Fixed",       "U08TOMAS",   "U07RHEA",  ["Windows"],                  -45, None,                      None),
    ("BUG231", "Save thumbnail blurry at 1080p",                       "BUG-231", "Low",     "Won't Fix",   "U03PINKMAN", None,       ["Windows","Linux"],          -50, None,                      None),
    ("BUG244", "Localization: French quote marks",                     "BUG-244", "Medium",  "Fixed",       "U04LAGOON",  "U07RHEA",  ["macOS","Windows","Linux","Switch"], -18, None,              None),
]

def seed_bugs() -> None:
    section("5c. Seeding DB_BUGS rows")
    db_id = DB_ID_MAP.get("DB_BUGS")
    if not db_id:
        warn("DB_BUGS missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Title")
    for (label, title, bug_id, sev, status, reporter, assignee, platforms, filed_off, rel_task, url) in BUGS_ROWS:
        if title in existing:
            ROW_ID_MAP[label] = existing[title]
            log(f"{label} ('{title}') already exists → {existing[title]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create)")
            continue
        props: dict = {
            "Title":    title_value(title),
            "Bug ID":   rich_text_value([rt_text(bug_id)]),
            "Severity": select_value(sev),
            "Status":   status_value(status),
            "Reporter": people_value([reporter]),
            "Assignee": people_value([assignee] if assignee else []),
            "Platform": multi_select_value(platforms),
            "Filed":    date_value(date_at(filed_off)),
            "URL":      url_value(url),
        }
        if rel_task:
            props["Related Task"] = relation_value([rel_task])
        page = post("/pages", {
            "parent": {"database_id": db_id},
            "properties": props,
        })
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{title}') → {page['id']}")
        time.sleep(0.15)

# --- DB_MEETING_NOTES rows --------------------------------------------------

def _follow_ups_segments(template: str, *, replacements: dict[str, list[dict]]) -> list[dict]:
    """
    Build a rich_text rich-text array from a template like
        "@Miranda owns this. See @[Tomb-3 Level Design]."
    where each token (@Miranda, @[Tomb-3 Level Design], @2026-05-10) is replaced
    by the rich_text segments in `replacements`. Any token NOT in replacements
    is left as plain text (still anchored to first-name search).
    """
    segments: list[dict] = []
    i = 0
    while i < len(template):
        # Find the next token.
        next_idx = len(template)
        next_token = None
        for tok in replacements:
            j = template.find(tok, i)
            if j != -1 and j < next_idx:
                next_idx = j
                next_token = tok
        if next_token is None:
            segments.append(rt_text(template[i:]))
            break
        if next_idx > i:
            segments.append(rt_text(template[i:next_idx]))
        segments.extend(replacements[next_token])
        i = next_idx + len(next_token)
    return segments

MEETING_NOTES_ROWS = [
    # (label, title, date_offset, hour, minute, attendees, type, follow_ups_template, action_items)
    ("MTG_TOMB3_REVIEW",  "Tomb-3 design review",     -7,  14, 0,
        ["U01MIRANDA","U05CLAUDE","U07RHEA"], "design-review",
        "@Miranda to push the warm-rim lighting on angle B; followup tracked in @[Tomb-3 Level Design].",
        ["TASK_TOMB3_LIGHTING"]),
    ("MTG_BUG247_TRIAGE", "BUG-247 triage",           -6,  11, 0,
        ["U02JARED","U03PINKMAN","U06DEVON"], "standup",
        "@Jared owns escalation. @Devon investigates async streamer. See @[Tomb-3 Level Design] notes.",
        ["TASK_FIX_TILE_LOADER","TASK_BUG247_VERIFY"]),
    ("MTG_LAUNCH_STANDUP","Launch standup",           -2,   9, 0,
        ["U01MIRANDA","U02JARED","U04LAGOON","U05CLAUDE"], "standup",
        "Marketing is 60% ready. @Lagoon: trailer copy by Tuesday EOD. @Miranda: brand kit signed off.",
        ["TASK_TRAILER_COPY","TASK_PRESS_LIST"]),
    ("MTG_ALL_HANDS",     "April all-hands",         -13,  11, 0,
        ["U01MIRANDA","U02JARED","U03PINKMAN","U04LAGOON","U05CLAUDE","U06DEVON","U07RHEA","U08TOMAS"], "all-hands",
        "Recap of milestones; @Miranda demoed tomb-3 stills.",
        []),
    ("MTG_QA_RETRO",      "QA retro — alpha round 2",-20,  15, 0,
        ["U03PINKMAN","U08TOMAS","U02JARED"], "retro",
        "Three repeat regressions; @Pinkman to set up nightly smoke run.",
        []),
    ("MTG_ENG_PLANNING",  "Eng planning — week of 4/13", -6, 10, 0,
        ["U02JARED","U06DEVON","U07RHEA"], "standup",
        "Sprint goals locked. @Rhea on input UI; @Devon on inventory v3 spike.",
        ["TASK_RHEA_INPUT_REBIND","TASK_MIGRATE_INVENTORY"]),
    ("MTG_PRESS_PREP",    "Press preview prep",      -4,  13, 0,
        ["U04LAGOON","U05CLAUDE"], "standup",
        "Coverage embargo set to 2026-05-03. @Lagoon: press list. @Claude: legal review.",
        ["TASK_PRESS_LIST"]),
    ("MTG_LEADS_SYNC",    "Leads sync",             -10,  16, 0,
        ["U01MIRANDA","U02JARED","U03PINKMAN","U04LAGOON"], "retro",
        "Cadence locked: weekly Wednesdays. @Jared owns the agenda.",
        []),
]

def _follow_up_replacements_for() -> dict[str, list[dict]]:
    """Mention tokens that may appear in any Follow-ups template."""
    repl: dict[str, list[dict]] = {}
    for first, label in [("@Miranda","U01MIRANDA"),("@Jared","U02JARED"),
                         ("@Pinkman","U03PINKMAN"),("@Lagoon","U04LAGOON"),
                         ("@Claude","U05CLAUDE"),("@Devon","U06DEVON"),
                         ("@Rhea","U07RHEA"),("@Tomás","U08TOMAS")]:
        u = uid(label)
        if u:
            repl[first] = [rt_mention_user(u)]
    tomb3 = PAGE_ID_MAP.get("P04_TOMB3")
    if tomb3:
        repl["@[Tomb-3 Level Design]"] = [rt_mention_page(tomb3)]
    return repl

def seed_meeting_notes() -> None:
    section("5d. Seeding DB_MEETING_NOTES rows")
    db_id = DB_ID_MAP.get("DB_MEETING_NOTES")
    if not db_id:
        warn("DB_MEETING_NOTES missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Title")
    repls = _follow_up_replacements_for()
    for (label, title, day_off, hh, mm, attendees, mtg_type, follow_template, action_items) in MEETING_NOTES_ROWS:
        if title in existing:
            ROW_ID_MAP[label] = existing[title]
            log(f"{label} ('{title}') already exists → {existing[title]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create)")
            continue
        props: dict = {
            "Title":      title_value(title),
            "Date":       date_value(datetime_at(day_off, hh, mm)),
            "Attendees":  people_value(attendees),
            "Type":       select_value(mtg_type),
            "Follow-ups": rich_text_value(_follow_ups_segments(follow_template, replacements=repls)),
        }
        if action_items:
            props["Action Items"] = relation_value(action_items)
        page = post("/pages", {
            "parent": {"database_id": db_id},
            "properties": props,
        })
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{title}') → {page['id']}")
        time.sleep(0.15)

# --- Helpers shared across row seeders --------------------------------------

def _index_rows_by_title(db_id: str, title_prop: str) -> dict[str, str]:
    """Return {plain_text_title: page_id} for every row in `db_id`."""
    rows = paginate(f"/databases/{db_id}/query")
    out: dict[str, str] = {}
    for r in rows:
        prop = (r.get("properties") or {}).get(title_prop) or {}
        title_arr = prop.get("title") or []
        text = "".join(t.get("plain_text", "") for t in title_arr)
        if text:
            out[text] = r["id"]
    return out

# ---------------------------------------------------------------------------
# Step 6 — Block trees on narrative pages
# ---------------------------------------------------------------------------

def _para(rich) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich}}

def _h1(text: str) -> dict:
    return {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [rt_text(text)]}}

def _h2(text: str) -> dict:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [rt_text(text)]}}

def _bullet(rich) -> dict:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich}}

def _todo(text: str, checked: bool) -> dict:
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": [rt_text(text)], "checked": checked}}

def _callout(rich, *, emoji: str, color: str) -> dict:
    return {"object": "block", "type": "callout", "callout": {
        "rich_text": rich, "icon": {"type": "emoji", "emoji": emoji}, "color": color,
    }}

def _toggle(text: str, *, children: list[dict]) -> dict:
    return {"object": "block", "type": "toggle", "toggle": {
        "rich_text": [rt_text(text)], "color": "default", "children": children,
    }}

def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

def _code(text: str, language: str) -> dict:
    return {"object": "block", "type": "code", "code": {
        "rich_text": [rt_text(text)], "language": language,
    }}

def _image(url: str) -> dict:
    return {"object": "block", "type": "image", "image": {
        "type": "external", "external": {"url": url},
    }}

def _existing_block_children(parent_id: str) -> list[dict]:
    return paginate(f"/blocks/{parent_id}/children", method="GET")

def seed_blocks_for_page(page_label: str, blocks: list[tuple[str, dict]]) -> None:
    """
    Append `blocks` to a page if its block list is empty (idempotent: skip if any
    seed-managed block already exists, signalled by a non-empty children list).
    Records each new block id under its label in BLOCK_ID_MAP.
    """
    page_id = PAGE_ID_MAP.get(page_label)
    if not page_id:
        warn(f"Page {page_label} unknown — skipping its blocks")
        return
    children = _existing_block_children(page_id)
    if children:
        # Fast path: assume the page is already seeded. Index existing blocks
        # by their (type, plain_text) so labels still map for downstream steps.
        log(f"{page_label} already has {len(children)} children — indexing")
        _index_existing_blocks(blocks, children)
        return
    if DRY_RUN:
        warn(f"{page_label} has 0 children (would append {len(blocks)})")
        return
    payload_children = [b for _, b in blocks]
    resp = patch(f"/blocks/{page_id}/children", {"children": payload_children})
    new_blocks = resp.get("results") or []
    for (label, _), new in zip(blocks, new_blocks):
        BLOCK_ID_MAP[label] = new["id"]
    log(f"Appended {len(new_blocks)} blocks to {page_label}")
    # For toggle children, reach into the response: Notion returns the toggle but
    # not its children. We must list children of the toggle to capture image ids.
    for (label, spec), new in zip(blocks, new_blocks):
        if spec.get("type") == "toggle" and spec["toggle"].get("children"):
            sub_children = _existing_block_children(new["id"])
            for (clabel, _), cnew in zip([(f"{label}_C{i+1}", c) for i, c in enumerate(spec["toggle"]["children"])], sub_children):
                BLOCK_ID_MAP[clabel] = cnew["id"]
    time.sleep(0.2)

def _index_existing_blocks(specs: list[tuple[str, dict]], live: list[dict]) -> None:
    """
    Best-effort label → live block id mapping when re-running against a page
    that's already been seeded. Matches by (type, plain_text). Toggle children
    are indexed separately by drilling into the toggle.
    """
    def block_text(b: dict) -> str:
        t = b.get("type")
        body = b.get(t, {}) if t else {}
        rt_arr = body.get("rich_text") or []
        return "".join(seg.get("plain_text", "") for seg in rt_arr)

    used: set[str] = set()
    for label, spec in specs:
        spec_type = spec.get("type")
        spec_body = spec.get(spec_type, {})
        spec_rt = spec_body.get("rich_text") or []
        spec_text = "".join(seg.get("text", {}).get("content", "") for seg in spec_rt)
        for b in live:
            if b["id"] in used:
                continue
            if b.get("type") != spec_type:
                continue
            if spec_type in ("paragraph","heading_1","heading_2","bulleted_list_item","to_do","callout","toggle","code") and block_text(b) != spec_text:
                continue
            BLOCK_ID_MAP[label] = b["id"]
            used.add(b["id"])
            if spec_type == "toggle" and spec_body.get("children"):
                sub = _existing_block_children(b["id"])
                for i, child_spec in enumerate(spec_body["children"]):
                    sub_label = f"{label}_C{i+1}"
                    if i < len(sub):
                        BLOCK_ID_MAP[sub_label] = sub[i]["id"]
            break

def seed_all_blocks() -> None:
    section("6. Seeding block trees")
    miranda = uid("U01MIRANDA")
    claude  = uid("U05CLAUDE")
    jared   = uid("U02JARED")
    lagoon  = uid("U04LAGOON")
    pinkman = uid("U03PINKMAN")
    devon   = uid("U06DEVON")
    rhea    = uid("U07RHEA")
    tomas   = uid("U08TOMAS")
    bug247  = ROW_ID_MAP.get("BUG247")

    # --- P04_TOMB3 -------------------------------------------------------
    tomb3_blocks = [
        ("B01", _h1("Tomb-3 Level Design")),
        ("B02", _para([
            rt_text("Owner: "),
            rt_mention_user(miranda) if miranda else rt_text("@Miranda"),
            rt_text(". Last updated: 2026-04-15."),
        ])),
        ("B03", _h2("Pillars")),
        ("B04", _bullet([rt_text("Verticality — players see the goal before they reach it.")])),
        ("B05", _bullet([rt_text("Diegetic light cues — warm = safe, cool = unknown.")])),
        ("B06", _bullet([rt_text("No combat in tomb interior.")])),
        ("B07", _h2("Open issues")),
        ("B08", _todo("Lighting pass on angle B — warm rim", True)),
        ("B09", _todo("Lighting pass on angle E — warmer",  False)),
        ("B10", _todo("Door collider revisit (BUG-248)",     False)),
        ("B11", _callout([
            rt_text("Save-file corruption is a launch blocker — see "),
            rt_mention_page(bug247) if bug247 else rt_text("@[BUG-247 row]"),
            rt_text("."),
        ], emoji="🚧", color="yellow_background")),
        ("B12", _toggle("Reference angles (click to expand)", children=[
            _image("https://assets.hintas.co/tomb3/angle_a.png"),
            _image("https://assets.hintas.co/tomb3/angle_b.png"),
            _image("https://assets.hintas.co/tomb3/angle_c.png"),
        ])),
        ("B13", _divider()),
        ("B14", _code(
            "# pseudo-code for streaming budget\nbudget = 256 * MB\nif gpu_pressure > 0.8 * budget:\n    drop_chunk()",
            "python")),
        ("B15", _para([
            rt_text("Last reviewed by "),
            rt_mention_user(claude) if claude else rt_text("@Claude"),
            rt_text("."),
        ])),
    ]
    seed_blocks_for_page("P04_TOMB3", tomb3_blocks)

    # --- P05_LAUNCH26 ----------------------------------------------------
    launch_blocks = [
        ("B20", _h1("Launch 2026")),
        ("B21", _para([
            rt_text("Ship target: "),
            rt_mention_date("2026-05-10"),
            rt_text(". Press preview: 2026-05-03."),
        ])),
        ("B22", _h2("Marketing checklist")),
        ("B23", _todo("Trailer copy", False)),
        ("B24", _todo("Press list finalized", False)),
        ("B25", _todo("Brand kit handoff", True)),
        ("B26", _h2("Engineering checklist")),
        ("B27", _todo("BUG-247 fix verified on macOS 14.4", False)),
        ("B28", _todo("Streaming-cert renewed", False)),
        ("B29", _divider()),
        ("B30", _para([
            rt_text("Owner: "),
            rt_mention_user(lagoon) if lagoon else rt_text("@Lagoon"),
            rt_text(". Eng-lead: "),
            rt_mention_user(jared) if jared else rt_text("@Jared"),
            rt_text("."),
        ])),
    ]
    seed_blocks_for_page("P05_LAUNCH26", launch_blocks)

    # --- P02_TEAM_DIR ----------------------------------------------------
    def team_bullet(handle_label: str, real_id: str | None, role: str) -> dict:
        if real_id:
            return _bullet([rt_mention_user(real_id), rt_text(f" — {role}")])
        return _bullet([rt_text(f"{handle_label} — {role}")])
    team_blocks = [
        ("B35", _h1("Team Directory")),
        ("B36", _para([rt_text("Active team members (April 2026):")])),
        ("B37", team_bullet("@Miranda", miranda, "Lead Designer")),
        ("B38", team_bullet("@Jared",   jared,   "Engineering Manager")),
        ("B39", team_bullet("@Pinkman", pinkman, "QA Lead")),
        ("B40", team_bullet("@Lagoon",  lagoon,  "Marketing & Community")),
        ("B41", team_bullet("@Devon",   devon,   "Backend Engineer")),
        ("B42", team_bullet("@Rhea",    rhea,    "Frontend Engineer")),
        ("B43", team_bullet("@Tomás",   tomas,   "QA Tester")),
        ("B44", team_bullet("@Claude",  claude,  "Founder")),
        ("B45", _divider()),
        ("B46", _divider()),
    ]
    seed_blocks_for_page("P02_TEAM_DIR", team_blocks)

    # --- P09_PLAYTEST_A2 -------------------------------------------------
    playtest_a2_blocks = [
        ("PT2_H", _h1("Playtest — alpha round 2")),
        ("PT2_P", _para([rt_text("Six external testers, three days. Feedback summary in toggle below.")])),
        ("PT2_T", _toggle("Raw participant notes", children=[
            _para([rt_text("Tester 1: tomb-3 lighting felt confusing in angle E. Otherwise loved the verticality.")]),
        ])),
    ]
    seed_blocks_for_page("P09_PLAYTEST_A2", playtest_a2_blocks)

    # --- P10_PLAYTEST_A3 -------------------------------------------------
    # A minimal block tree before we archive the page.
    playtest_a3_blocks = [
        ("PT3_H", _h1("Playtest — alpha round 3")),
        ("PT3_P", _para([rt_text("Cancelled before recruitment.")])),
    ]
    seed_blocks_for_page("P10_PLAYTEST_A3", playtest_a3_blocks)

# ---------------------------------------------------------------------------
# Step 7 — Comments
# ---------------------------------------------------------------------------

COMMENTS_SPEC = [
    # (label, parent_kind, parent_label, segments_builder)
    ("CMT01", "page",  "BUG247",
     lambda: [
         rt_text("@Devon can you confirm this repros on Sonoma 14.3 too?"),
     ] if not uid("U06DEVON") else [
         rt_mention_user(uid("U06DEVON")),
         rt_text(" can you confirm this repros on Sonoma 14.3 too?"),
     ]),
    ("CMT02", "page",  "BUG247",
     lambda: [rt_text("Confirmed on 14.3 and 14.4. Streamer drops chunk under 6 GB GPU pressure.")]),
    ("CMT03", "block", "B11",
     lambda: [rt_text("Marking this as launch-critical — let's keep it visible.")]),
    ("CMT04", "block", "B14",
     lambda: [rt_text("Real impl uses an LRU; pseudo-code is for clarity only.")]),
    ("CMT05", "page",  "MTG_BUG247_TRIAGE",
     lambda: [rt_text("Smoke run was clean on Windows. macOS still flaky.")]),
]

def _existing_comment_texts_for(parent_id: str, *, kind: str) -> set[str]:
    """Plain-text bodies of existing comments under a page or block.

    Notion's /comments endpoint is GET-only and uses `block_id` as the
    discussion anchor for both page-level and block-level comments.
    """
    params = {"block_id": parent_id}
    cursor: str | None = None
    out_texts: set[str] = set()
    while True:
        q = dict(params)
        if cursor:
            q["start_cursor"] = cursor
        try:
            resp = get("/comments", q)
        except NotionError as e:
            if e.status == 404:
                return out_texts
            raise
        for c in resp.get("results", []):
            txt = "".join(seg.get("plain_text", "") for seg in c.get("rich_text", []))
            if txt:
                out_texts.add(txt)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
        if not cursor:
            break
    return out_texts

def seed_comments() -> None:
    section("7. Seeding comments")
    for label, kind, parent_label, builder in COMMENTS_SPEC:
        parent_map = ROW_ID_MAP if kind == "page" else BLOCK_ID_MAP
        parent_id = parent_map.get(parent_label)
        if not parent_id:
            warn(f"{label}: parent {parent_label} unknown — skipping")
            continue
        segments = builder()
        plain = "".join(seg.get("plain_text") or seg.get("text", {}).get("content", "") for seg in segments)
        existing = _existing_comment_texts_for(parent_id, kind=kind)
        if plain in existing:
            log(f"{label} already exists on {parent_label}")
            continue
        if DRY_RUN:
            warn(f"{label} on {parent_label} MISSING (would create)")
            continue
        if kind == "page":
            body = {"parent": {"page_id": parent_id}, "rich_text": segments}
        else:
            body = {"parent": {"block_id": parent_id}, "rich_text": segments}
        try:
            resp = post("/comments", body)
            COMMENT_ID_MAP[label] = resp.get("id", "")
            log(f"Created {label} on {parent_label}")
            time.sleep(0.15)
        except NotionError as e:
            warn(f"{label} on {parent_label} failed: {e}")

# ---------------------------------------------------------------------------
# Step 8 — Archive P10_PLAYTEST_A3
# ---------------------------------------------------------------------------

def archive_playtest_a3() -> None:
    section("8. Archiving P10_PLAYTEST_A3")
    page_id = PAGE_ID_MAP.get("P10_PLAYTEST_A3")
    if not page_id:
        warn("P10_PLAYTEST_A3 missing — skipping archive")
        return
    if DRY_RUN:
        log("Would PATCH archived=true on P10_PLAYTEST_A3")
        return
    try:
        page = get(f"/pages/{page_id}")
        if page.get("archived"):
            log("P10_PLAYTEST_A3 already archived")
            return
        patch(f"/pages/{page_id}", {"archived": True})
        log("Archived P10_PLAYTEST_A3 (in_trash)")
    except NotionError as e:
        warn(f"Could not archive P10_PLAYTEST_A3: {e}")

# ---------------------------------------------------------------------------
# Step 8b — Capture ground-truth snapshot
# ---------------------------------------------------------------------------

# Properties whose values we record per row. Restricted to the property types
# that survive a round-trip through the API; long rich_text / files columns
# would balloon the snapshot without aiding fairness.
_GROUND_TRUTH_ROW_PROP_TYPES = {
    "title", "rich_text", "select", "multi_select", "status", "people",
    "date", "number", "url", "checkbox", "email", "phone_number", "relation",
}


def _plain_text(rt: list[dict]) -> str:
    return "".join(seg.get("plain_text", "") for seg in (rt or []))


def _normalize_property_schema(prop: dict) -> dict:
    """Flatten a single Notion DB property to {type, options?} for snapshotting."""
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


def _normalize_property_value(prop: dict) -> dict | None:
    """Reduce a row property value to the comparable subset used by the verifier."""
    ptype = prop.get("type", "")
    if ptype not in _GROUND_TRUTH_ROW_PROP_TYPES:
        return None
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


def _row_label_index() -> dict[str, str]:
    """Reverse of ROW_ID_MAP — real id → logical label, for snapshot tagging."""
    return {real: label for label, real in ROW_ID_MAP.items() if real}


def _block_label_index() -> dict[str, str]:
    return {real: label for label, real in BLOCK_ID_MAP.items() if real}


def _page_label_index() -> dict[str, str]:
    return {real: label for label, real in PAGE_ID_MAP.items() if real}


def _db_label_index() -> dict[str, str]:
    return {real: label for label, real in DB_ID_MAP.items() if real}


def capture_ground_truth(bot_id: str, workspace_name: str) -> dict:
    """
    Snapshot every shared entity post-seed so the verifier can derive its
    expected state dynamically (no hardcoded EXPECTED_* tables in verify).

    Mirrors the Slack benchmark's ground-truth block: anything inside this
    block is the answer key; entities outside the seed scope live under the
    ``ignore`` lists so workspace drift in non-seeded areas doesn't trigger
    hard drift.
    """
    section("8b. Capturing workspace ground truth")
    truth: dict = {
        "workspace": {"bot_id": bot_id, "name": workspace_name},
        "users":     [],
        "pages":     [],
        "databases": [],
        "rows":      [],
        "blocks":    [],
        "comments":  [],
        "ignore":    {"user_ids": [], "page_ids": [], "database_ids": []},
    }

    pages_label = _page_label_index()
    dbs_label   = _db_label_index()
    rows_label  = _row_label_index()
    blocks_label = _block_label_index()
    seed_user_ids = {real for real in USER_ID_MAP.values() if real}

    # --- users -----------------------------------------------------------
    try:
        for u in paginate("/users", method="GET"):
            person = u.get("person") or {}
            bot = u.get("bot") or {}
            truth["users"].append({
                "id":    u.get("id"),
                "name":  u.get("name", ""),
                "type":  u.get("type", ""),
                "is_bot": u.get("type") == "bot",
                "email": person.get("email", ""),
                "owner_type": (bot.get("owner") or {}).get("type", ""),
                "workspace_name": bot.get("workspace_name", ""),
            })
        log(f"Captured {len(truth['users'])} users")
    except NotionError as e:
        warn(f"/users failed during ground-truth capture: {e}")

    # Workspace owner (if surfaced by the bot record); used by verify to skip
    # workspace-owner drift checks. Heuristic: any active person not in the
    # seeded user roster is workspace drift.
    for u in truth["users"]:
        uid_real = u.get("id")
        if not uid_real or uid_real == bot_id:
            continue
        if u.get("is_bot") or u.get("type") == "bot":
            continue
        if uid_real not in seed_user_ids:
            truth["ignore"]["user_ids"].append(uid_real)

    # --- pages -----------------------------------------------------------
    for label, real_id in PAGE_ID_MAP.items():
        if not real_id:
            continue
        try:
            page = get(f"/pages/{real_id}")
        except NotionError as e:
            if e.status == 404:
                # Pre-seed unshared pages (P08, P11) MUST 404 — record them as
                # ignore-list entries so the verifier expects this state.
                if label in PREREQ_KEYS_PAGES:
                    truth["ignore"]["page_ids"].append(real_id)
                    log(f"{label} 404 — recorded under ignore.page_ids")
                else:
                    warn(f"{label} 404 during ground-truth capture")
                continue
            warn(f"{label} retrieve failed: {e}")
            continue
        title_prop = (page.get("properties") or {}).get("title") or {}
        title_text = _plain_text(title_prop.get("title") or [])
        parent = page.get("parent") or {}
        truth["pages"].append({
            "id":           page.get("id"),
            "label":        label,
            "title":        title_text,
            "icon":         (page.get("icon") or {}).get("emoji", ""),
            "parent_type":  parent.get("type", ""),
            "parent_id":    parent.get(parent.get("type", ""), "") if parent else "",
            "parent_label": pages_label.get(parent.get("page_id") or ""),
            "archived":     bool(page.get("archived") or page.get("in_trash")),
        })
    log(f"Captured {len(truth['pages'])} pages")

    # --- databases (schema + parent) ------------------------------------
    for label, real_id in DB_ID_MAP.items():
        if not real_id:
            continue
        try:
            db = get(f"/databases/{real_id}")
        except NotionError as e:
            if e.status == 404:
                if label in PREREQ_KEYS_DBS:
                    truth["ignore"]["database_ids"].append(real_id)
                    log(f"{label} 404 — recorded under ignore.database_ids")
                else:
                    warn(f"{label} 404 during ground-truth capture")
                continue
            warn(f"{label} retrieve failed: {e}")
            continue
        properties = {
            name: _normalize_property_schema(prop)
            for name, prop in (db.get("properties") or {}).items()
        }
        parent = db.get("parent") or {}
        truth["databases"].append({
            "id":           db.get("id"),
            "label":        label,
            "title":        _plain_text(db.get("title") or []),
            "parent_type":  parent.get("type", ""),
            "parent_id":    parent.get(parent.get("type", ""), "") if parent else "",
            "parent_label": pages_label.get(parent.get("page_id") or ""),
            "archived":     bool(db.get("archived") or db.get("in_trash")),
            "properties":   properties,
        })
    log(f"Captured {len(truth['databases'])} databases")

    # --- rows (per shared db) -------------------------------------------
    db_real_ids = [d["id"] for d in truth["databases"]]
    for db_real in db_real_ids:
        db_label = dbs_label.get(db_real)
        try:
            rows = paginate(f"/databases/{db_real}/query")
        except NotionError as e:
            warn(f"{db_label or db_real} query failed during ground-truth capture: {e}")
            continue
        # Skip pre-seed dbs that should not be visible (defensive — we
        # already filtered them out above when get() 404'd, but the loop is
        # bounded to the visible set anyway).
        for row in rows:
            props_in = row.get("properties") or {}
            title_text = ""
            for prop in props_in.values():
                if prop.get("type") == "title":
                    title_text = _plain_text(prop.get("title") or [])
                    break
            row_props: dict = {}
            for name, prop in props_in.items():
                normalized = _normalize_property_value(prop)
                if normalized is not None:
                    row_props[name] = normalized
            truth["rows"].append({
                "id":         row.get("id"),
                "label":      rows_label.get(row.get("id", "")),
                "db_id":      db_real,
                "db_label":   db_label,
                "title":      title_text,
                "archived":   bool(row.get("archived") or row.get("in_trash")),
                "properties": row_props,
            })
    log(f"Captured {len(truth['rows'])} rows across {len(db_real_ids)} databases")

    # --- blocks ----------------------------------------------------------
    # Only the labelled blocks (BLOCK_ID_MAP) are "answer key" — extras live
    # on the page and the verifier treats them as soft drift.
    for label, block_id in BLOCK_ID_MAP.items():
        if not block_id:
            continue
        try:
            blk = get(f"/blocks/{block_id}")
        except NotionError as e:
            if e.status == 404:
                warn(f"Block {label} 404 — not capturing into ground truth")
                continue
            warn(f"Block {label} retrieve failed: {e}")
            continue
        btype = blk.get("type", "")
        body = blk.get(btype) or {}
        plain = _plain_text(body.get("rich_text") or []) if isinstance(body, dict) else ""
        parent = blk.get("parent") or {}
        parent_id = parent.get(parent.get("type", ""), "") if parent else ""
        truth["blocks"].append({
            "id":           block_id,
            "label":        label,
            "type":         btype,
            "parent_type":  parent.get("type", ""),
            "parent_id":    parent_id,
            "parent_page_label":  pages_label.get(parent_id),
            "parent_block_label": blocks_label.get(parent_id),
            "plain_text":   plain,
            "archived":     bool(blk.get("archived") or blk.get("in_trash")),
        })
    log(f"Captured {len(truth['blocks'])} blocks")

    # P02_TEAM_DIR child count — preserved as a benchmark invariant from
    # workspace_state §6.5 (pagination boundary at 11 children).
    team_dir_real = PAGE_ID_MAP.get("P02_TEAM_DIR")
    if team_dir_real:
        try:
            children = paginate(f"/blocks/{team_dir_real}/children", method="GET")
            truth["page_child_counts"] = {"P02_TEAM_DIR": len(children)}
            log(f"P02_TEAM_DIR child count: {len(children)}")
        except NotionError as e:
            warn(f"P02_TEAM_DIR children query failed: {e}")

    # --- comments --------------------------------------------------------
    for label, comment_id in COMMENT_ID_MAP.items():
        # Notion's API has no GET /comments/{id}; the snapshot just records
        # the id mapping. The verifier will look these up via the parent
        # row/block id paired in COMMENTS_SPEC.
        truth["comments"].append({"id": comment_id, "label": label})
    log(f"Captured {len(truth['comments'])} comment ids")

    return truth


# ---------------------------------------------------------------------------
# Step 9 — Save state file
# ---------------------------------------------------------------------------

def save_state(bot_id: str, workspace_name: str) -> None:
    section("9. Saving workspace state")
    truth = capture_ground_truth(bot_id, workspace_name) if not DRY_RUN else {}
    state = {
        "workspace_name": workspace_name,
        "bot_id": bot_id,
        "benchmark_now": BENCHMARK_NOW.isoformat(),
        "user_id_map":   USER_ID_MAP,
        "page_id_map":   PAGE_ID_MAP,
        "db_id_map":     DB_ID_MAP,
        "row_id_map":    ROW_ID_MAP,
        "block_id_map":  BLOCK_ID_MAP,
        "comment_id_map": COMMENT_ID_MAP,
        "seeded_at":     datetime.now(timezone.utc).isoformat(),
        "ground_truth":  truth,
    }
    if DRY_RUN:
        log(f"Would write state → {STATE_PATH}")
        return
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"  Saved → {STATE_PATH}")
    print("  verify_workspace.py reads state['ground_truth'] as the answer key.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN, TOKEN, HEADERS, STATE_PATH, PREREQ_PATH

    parser = argparse.ArgumentParser(description="Seed Hintas Notion benchmark workspace")
    parser.add_argument("--verify", "--dry-run", dest="verify", action="store_true",
                        help="Dry-run: report missing items without creating")
    parser.add_argument("--token", help="Notion integration token (overrides NOTION_TOKEN)")
    parser.add_argument("--stack", required=True,
                        help="Stack name (e.g. notion, hintas). Resolves state/prereq "
                             "paths and the auth token from notion.toml.")
    args = parser.parse_args()

    DRY_RUN = args.verify

    STATE_PATH, PREREQ_PATH, stack_token = _resolve_stack_paths(args.stack)

    if args.token:
        TOKEN = args.token
    elif stack_token:
        TOKEN = stack_token
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

    if not TOKEN:
        err("Set NOTION_TOKEN env var or pass --token secret_...")
        return 1

    print(f"\n{'='*60}")
    print(f"  Hintas Notion Benchmark — Workspace Seeder")
    print(f"  Mode: {'DRY RUN (verify only)' if DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'='*60}")

    try:
        bot_id, workspace_name = verify_auth()
        load_prerequisites()
        verify_prerequisites_unshared()
        resolve_users(bot_id)
        find_root_page()
        create_pages()
        create_databases()
        add_relation_properties()
        configure_status_options()
        seed_projects()
        seed_tasks()
        seed_bugs()
        seed_meeting_notes()
        seed_all_blocks()
        seed_comments()
        archive_playtest_a3()
        save_state(bot_id, workspace_name)
    except NotionError as e:
        req = e.body.get("_request", {})
        if req:
            err(f"Notion API error on {req.get('method')} {req.get('url')}: {e}")
        err(f"  body: {json.dumps(e.body, indent=2)}")
        return 1
    except KeyboardInterrupt:
        err("Interrupted by user.")
        return 1

    print(f"\n{'='*60}")
    print(f"  {'VERIFY COMPLETE' if DRY_RUN else 'SEED COMPLETE'}")
    if not DRY_RUN:
        print(f"  Next: run verify_workspace.py to confirm zero drift.")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
