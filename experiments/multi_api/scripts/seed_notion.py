#!/usr/bin/env python3
"""
seed_notion.py  —  Hintas Multi-API Benchmark (Notion surface)

Seeds (or verifies) the Notion surface of the multi-API benchmark. Unlike the
single-API experiments/notion seeder this script is STANDALONE: it reads its
own integration token from ``NOTION_TOKEN`` (override ``--token``) rather than
resolving a stack from a platform manifest, and it writes its answer key to
``workspace_state_notion.json`` next to the script (resolved via common.py).

Everything is parented under a single root page the operator shares with the
integration once: a page titled "Hintas Multi-API" (or whatever
``NOTION_PARENT_PAGE_ID`` / ``--parent-page-id`` points at). The script can only
build under a page that is already shared with it, so if none resolves it exits
with a manual instruction.

What it seeds (all under P_ROOT):
  databases  DB_PEOPLE, DB_PROJECTS, DB_ONBOARDING  (created as child databases)
  rows       People rows (one per active human), project tasks, one draft
             onboarding row for the candidate
  pages      release notes, all-hands, weekly notes, Q2 roadmap, incidents,
             and one notes page per lead
  blocks     a small block tree per page (captured into block_id_map so reset
             can tell prompt-appended blocks from seeded ones)

Notion API limits this script does not work around:
  * Author attribution — the integration authors every seeded row, block and
    page. The grading reflects this (single-token scenario).
  * Backdating created_time / last_edited_time — Notion stamps real wall-clock.
    Date-window prompts grade the seeded `Due` property (written deterministically).

Usage:
    export NOTION_TOKEN=secret_<integration token>
    python seed_notion.py                 # full seed (idempotent — reruns safely)
    python seed_notion.py --verify        # dry-run: report what's missing
    python seed_notion.py --token TOK     # override env var
    python seed_notion.py --parent-page-id <id>   # override root page resolution
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from common import (log, warn, err, section, subsection, set_dry_run, load_users,
    leads, team_distribution, agent_logical_id, email_of, name_of,
    save_state, load_state, resolve_state_file, add_stack_arg, stack_env)
from benchmarking.clock import BENCH_TZ, BENCHMARK_NOW

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
ROOT_PAGE_TITLE = "Hintas"

# Populated as seeding progresses.
USER_ID_MAP: dict[str, str] = {}        # logical → real Notion user UUID
PAGE_ID_MAP: dict[str, str] = {}        # P_ROOT, PG_RELEASE_NOTES, ...
DB_ID_MAP: dict[str, str] = {}          # DB_PEOPLE, DB_PROJECTS, DB_ONBOARDING
ROW_ID_MAP: dict[str, str] = {}         # PEOPLE_*, PROJ_*, TASK_*, ONB_*
BLOCK_ID_MAP: dict[str, str] = {}       # <PAGELABEL>_B<n>

BOT_ID: str = ""
WORKSPACE_NAME: str = ""

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

def rt_mention_date(start: str, end: str | None = None) -> dict:
    date_obj = {"start": start, "end": end}
    return {"type": "mention", "mention": {"type": "date", "date": date_obj}}

def rt(*segments: dict) -> list[dict]:
    return list(segments)

# ---------------------------------------------------------------------------
# Property builders
# ---------------------------------------------------------------------------

def title_value(text: str) -> dict:
    return {"title": [rt_text(text)]}

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

def number_value(n: float | int | None) -> dict:
    return {"number": n}

def url_value(url: str | None) -> dict:
    return {"url": url}

def email_value(addr: str | None) -> dict:
    return {"email": addr}

def people_value(logical_ids: list[str]) -> dict:
    """Build a `people` property value, skipping unresolved logical ids with a warning."""
    refs: list[dict] = []
    for logical in logical_ids:
        real = USER_ID_MAP.get(logical)
        if not real:
            warn(f"Skipping {logical} in people prop — not in USER_ID_MAP (no Notion member)")
            continue
        refs.append({"object": "user", "id": real})
    return {"people": refs}

# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def _para(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [rt_text(text)]}}

def _h1(text: str) -> dict:
    return {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [rt_text(text)]}}

def _h2(text: str) -> dict:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [rt_text(text)]}}

def _bullet(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [rt_text(text)]}}

def _todo(text: str, checked: bool) -> dict:
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": [rt_text(text)], "checked": checked}}

def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

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
    return bot_id, workspace_name

# ---------------------------------------------------------------------------
# Step 1 — Resolve users by email
# ---------------------------------------------------------------------------

def resolve_users(bot_id: str) -> None:
    """Populate USER_ID_MAP via /users (paginated). Logical ids map by email.

    Softened relative to the single-API seeder: a missing expected member is a
    warning, not a hard exit (this surface is standalone and may run against a
    workspace that hasn't fully provisioned every persona yet).
    """
    section("1. Resolving users")
    users = load_users()
    by_email = {entry.get("email", "").lower(): lid
                for lid, entry in users.items() if entry.get("email")}

    all_users = paginate("/users", method="GET")
    found_logical: set[str] = set()
    for u in all_users:
        if u.get("type") != "person":
            continue
        email = (u.get("person") or {}).get("email", "").lower()
        logical = by_email.get(email)
        if logical:
            USER_ID_MAP[logical] = u["id"]
            found_logical.add(logical)
            log(f"{logical} → {u['id']}  ({email})")

    USER_ID_MAP["U10AGENT"] = bot_id
    log(f"U10AGENT → {bot_id}  (this integration's bot user)")

    # The acting agent maps to the bot too — a people-prop on the agent resolves
    # to whatever Notion member shares the agent's email, falling back to the bot.
    agent = agent_logical_id()
    if agent not in USER_ID_MAP:
        USER_ID_MAP[agent] = bot_id
        log(f"{agent} → {bot_id}  (agent falls back to bot user)")

    expected = set(team_distribution())
    missing = [m for m in expected if m not in USER_ID_MAP]
    for m in missing:
        warn(f"Expected member {m} ({email_of(m)}) not found in /users — "
             "people props referencing it will be created with no assignee.")

# ---------------------------------------------------------------------------
# Step 2 — Resolve the root page (must be pre-shared with the integration)
# ---------------------------------------------------------------------------

def _read_title(obj: dict) -> str:
    """Extract the title plain_text from a page or database object."""
    if obj.get("object") == "database":
        return "".join(t.get("plain_text", "") for t in obj.get("title", []))
    props = obj.get("properties") or {}
    for v in props.values():
        if v.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in v.get("title", []))
    return ""

def find_root_page(explicit_id: str | None) -> str:
    """Resolve the root page: the resolved id (flag/env) if given, else /search by title."""
    section("2. Locating the root page")
    candidate_id = explicit_id or ""
    if candidate_id:
        page = get(f"/pages/{candidate_id}")
        page_id = page["id"]
        title = _read_title(page)
        if title.strip().lower() != ROOT_PAGE_TITLE.lower():
            warn(f"Parent page title is {title!r}, expected {ROOT_PAGE_TITLE!r} — "
                 "double-check NOTION_PARENT_PAGE_ID / --parent-page-id points at the right page.")
        PAGE_ID_MAP["P_ROOT"] = page_id
        log(f"P_ROOT → {page_id}  (from explicit id / env)")
        return page_id

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
        err(f"Manual step: share a page titled {ROOT_PAGE_TITLE!r} with the integration, "
            "or set NOTION_PARENT_PAGE_ID / pass --parent-page-id, then rerun.")
        sys.exit(1)
    workspace_parented = [r for r in candidates if r.get("parent", {}).get("type") == "workspace"]
    chosen = (workspace_parented or candidates)[0]
    page_id = chosen["id"]
    PAGE_ID_MAP["P_ROOT"] = page_id
    log(f"P_ROOT → {page_id}")
    return page_id

# ---------------------------------------------------------------------------
# Step 3 — Databases
# ---------------------------------------------------------------------------

def db_schema_people() -> dict:
    return {
        "Name":   {"title": {}},
        "Email":  {"email": {}},
        "Status": {"status": {}},  # options patched in configure_status_options()
        "Team":   {"select": {"options": [
            {"name": "leads",   "color": "blue"},
            {"name": "members", "color": "green"},
        ]}},
    }

def db_schema_projects() -> dict:
    return {
        "Task":     {"title": {}},
        "Assignee": {"people": {}},
        "Status":   {"status": {}},  # options patched in configure_status_options()
        "Due":      {"date": {}},
        "Owner":    {"people": {}},
    }

def db_schema_onboarding() -> dict:
    return {
        "Name":   {"title": {}},
        "Status": {"status": {}},  # options patched in configure_status_options()
        "Person": {"email": {}},
    }

DATABASES_SPEC = [
    # (label, title, schema_fn)
    ("DB_PEOPLE",     "People",     db_schema_people),
    ("DB_PROJECTS",   "Projects",   db_schema_projects),
    ("DB_ONBOARDING", "Onboarding", db_schema_onboarding),
]

# Notion forces a default status option set at db creation; align each db's
# Status options with the spec so row writes don't fail with 'option ... does
# not exist'.
STATUS_OPTIONS_SPEC = {
    "DB_PEOPLE":     ["Active", "Inactive"],
    "DB_PROJECTS":   ["Not started", "In progress", "In review", "Done"],
    "DB_ONBOARDING": ["Draft", "In progress", "Done"],
}

def _find_child_database_by_title(parent_id: str, title: str) -> str | None:
    blocks = paginate(f"/blocks/{parent_id}/children", method="GET")
    for b in blocks:
        if b.get("type") == "child_database" and b.get("child_database", {}).get("title") == title:
            return b["id"]
    return None

def create_databases() -> None:
    section("3. Creating databases")
    root_id = PAGE_ID_MAP.get("P_ROOT")
    if not root_id:
        warn("P_ROOT unknown — skipping databases")
        return
    for label, title, schema_fn in DATABASES_SPEC:
        existing = _find_child_database_by_title(root_id, title)
        if existing:
            DB_ID_MAP[label] = existing
            log(f"{label} ('{title}') already exists → {existing}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create under P_ROOT)")
            continue
        body = {
            "parent": {"type": "page_id", "page_id": root_id},
            "title": [rt_text(title)],
            "properties": schema_fn(),
        }
        db = post("/databases", body)
        DB_ID_MAP[label] = db["id"]
        log(f"Created {label} ('{title}') → {db['id']}")
        time.sleep(0.2)

def configure_status_options() -> None:
    section("3b. Configuring Status property options")
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

# ---------------------------------------------------------------------------
# Step 4 — Seed database rows
# ---------------------------------------------------------------------------

def date_at(days_offset: float) -> str:
    """Date-only ISO string (YYYY-MM-DD), offset from BENCHMARK_NOW."""
    return (BENCHMARK_NOW + timedelta(days=days_offset)).date().isoformat()

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

def seed_people() -> None:
    section("4a. Seeding DB_PEOPLE rows")
    db_id = DB_ID_MAP.get("DB_PEOPLE")
    if not db_id:
        warn("DB_PEOPLE missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Name")
    for logical in team_distribution():
        label = f"PEOPLE_{logical}"
        name = name_of(logical)
        if name in existing:
            ROW_ID_MAP[label] = existing[name]
            log(f"{label} ('{name}') already exists → {existing[name]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{name}') MISSING (would create)")
            continue
        team = common.USERS.get(logical, {}).get("team", "members")
        props = {
            "Name":   title_value(name),
            "Email":  email_value(email_of(logical)),
            "Status": status_value("Active"),
            "Team":   select_value(team),
        }
        page = post("/pages", {"parent": {"database_id": db_id}, "properties": props})
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{name}') → {page['id']}")
        time.sleep(0.15)

# (label, task, assignee_logical, status, due_offset_days)
PROJECTS_ROWS = [
    ("PROJ_PRICING",   "Pricing page",                "U04LAGOON",  "In progress",  +3),
    ("TASK_JARED1",    "Refactor auth module",        "U02JARED",   "In progress",  +5),
    ("TASK_JARED2",    "Write onboarding guide",      "U02JARED",   "Not started", +12),
    ("TASK_LAGOON1",   "Migrate analytics events",    "U04LAGOON",  "In review",    +9),
    ("TASK_PINK_DONE", "Q1 retro notes",              "U03PINKMAN", "Done",         -3),
    ("TASK_DEVON1",    "Fix export pipeline timeout", "U06DEVON",   "In progress",  +2),
]

def seed_projects() -> None:
    section("4b. Seeding DB_PROJECTS rows")
    db_id = DB_ID_MAP.get("DB_PROJECTS")
    if not db_id:
        warn("DB_PROJECTS missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Task")
    for label, task, assignee, status, due_off in PROJECTS_ROWS:
        if task in existing:
            ROW_ID_MAP[label] = existing[task]
            log(f"{label} ('{task}') already exists → {existing[task]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{task}') MISSING (would create)")
            continue
        props = {
            "Task":     title_value(task),
            "Assignee": people_value([assignee]),
            "Status":   status_value(status),
            "Due":      date_value(date_at(due_off)),
            "Owner":    people_value([]),
        }
        page = post("/pages", {"parent": {"database_id": db_id}, "properties": props})
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{task}') → {page['id']}")
        time.sleep(0.15)

# (label, name, status, person_email)
ONBOARDING_ROWS = [
    ("ONB_PRIYA", "Priya Nakamura", "Draft", "priya@hintas.co"),
]

def seed_onboarding() -> None:
    section("4c. Seeding DB_ONBOARDING rows")
    db_id = DB_ID_MAP.get("DB_ONBOARDING")
    if not db_id:
        warn("DB_ONBOARDING missing — skipping rows")
        return
    existing = _index_rows_by_title(db_id, "Name")
    for label, name, status, person in ONBOARDING_ROWS:
        if name in existing:
            ROW_ID_MAP[label] = existing[name]
            log(f"{label} ('{name}') already exists → {existing[name]}")
            continue
        if DRY_RUN:
            warn(f"{label} ('{name}') MISSING (would create)")
            continue
        props = {
            "Name":   title_value(name),
            "Status": status_value(status),
            "Person": email_value(person),
        }
        page = post("/pages", {"parent": {"database_id": db_id}, "properties": props})
        ROW_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{name}') → {page['id']}")
        time.sleep(0.15)

# ---------------------------------------------------------------------------
# Step 5 — Pages + block trees
# ---------------------------------------------------------------------------

# (label, title, [block specs...]). The block list order is preserved so reset
# can map seeded top-level block ids by position.
PAGES_SPEC = [
    ("PG_RELEASE_NOTES", "Release Notes", [
        _h1("Release Notes"),
        _bullet("2026-03-12 — v3.8: search performance improvements."),
        _bullet("2026-03-28 — v3.9: SSO bug fixes and CSV export hardening."),
    ]),
    ("PG_ALLHANDS", "All-Hands", [
        _h1("All-Hands"),
        _h2("Agenda"),
        _bullet("Q2 roadmap walkthrough"),
        _h2("Attendees"),
    ]),
    ("PG_WEEKLY", "Weekly Notes", [
        _h1("Weekly Notes"),
        _para("Running log of weekly team digests."),
    ]),
    ("PG_Q2_ROADMAP", "Q2 Roadmap", [
        _h1("Q2 Roadmap"),
        _h2("Themes"),
        _bullet("Reliability: cut p95 API latency by 30%."),
        _bullet("Growth: ship self-serve onboarding."),
        _h2("Milestones"),
        _bullet("April — SSO GA."),
        _bullet("May — pricing page revamp."),
        _bullet("June — analytics v2."),
    ]),
    ("PG_INCIDENTS", "Incidents", [
        _h1("Incidents"),
        _para("Incident reports are filed as child pages here."),
    ]),
    ("PG_LEAD_JARED", "Jared Blackwood", [
        _h1("Jared Blackwood"),
        _h2("Notes"),
    ]),
    ("PG_LEAD_PINKMAN", "Saul Rivera", [
        _h1("Saul Rivera"),
        _h2("Notes"),
    ]),
    ("PG_LEAD_LAGOON", "Lagoon Takahashi", [
        _h1("Lagoon Takahashi"),
        _h2("Notes"),
    ]),
]

def _find_child_page_by_title(parent_id: str, title: str) -> str | None:
    blocks = paginate(f"/blocks/{parent_id}/children", method="GET")
    for b in blocks:
        if b.get("type") == "child_page" and b.get("child_page", {}).get("title") == title:
            return b["id"]
    return None

def _existing_block_children(parent_id: str) -> list[dict]:
    return paginate(f"/blocks/{parent_id}/children", method="GET")

def _spec_text(spec: dict) -> str:
    btype = spec.get("type", "")
    body = spec.get(btype, {})
    return "".join(seg.get("text", {}).get("content", "") for seg in body.get("rich_text", []))

def _live_text(blk: dict) -> str:
    btype = blk.get("type", "")
    body = blk.get(btype, {})
    rt_arr = body.get("rich_text", []) if isinstance(body, dict) else []
    return "".join(seg.get("plain_text", "") for seg in rt_arr)

def _index_block_ids(page_label: str, blocks: list[dict], live: list[dict]) -> None:
    """Map <PAGELABEL>_B<n> → live block id, anchored by (type, plain_text).

    Anchoring (rather than pure position) keeps the seeded ids correct even when
    a prompt prepended/reordered blocks before a re-run. A seeded spec with no
    live match is warned rather than mapped to a wrong id, so reset never deletes
    the wrong block.
    """
    used: set[str] = set()
    for i, spec in enumerate(blocks):
        label = f"{page_label}_B{i+1}"
        spec_type = spec.get("type")
        spec_text = _spec_text(spec)
        match = None
        for b in live:
            if b["id"] in used:
                continue
            if b.get("type") != spec_type:
                continue
            if spec_type == "divider" or _live_text(b) == spec_text:
                match = b
                break
        if match is None:
            warn(f"{label}: no live block matched (type={spec_type!r}) — not indexed")
            continue
        BLOCK_ID_MAP[label] = match["id"]
        used.add(match["id"])

def create_pages() -> None:
    section("5. Creating pages + block trees")
    root_id = PAGE_ID_MAP.get("P_ROOT")
    if not root_id:
        warn("P_ROOT unknown — skipping pages")
        return
    for label, title, blocks in PAGES_SPEC:
        existing = _find_child_page_by_title(root_id, title)
        if existing:
            PAGE_ID_MAP[label] = existing
            log(f"{label} ('{title}') already exists → {existing}")
            live = _existing_block_children(existing)
            _index_block_ids(label, blocks, live)
            continue
        if DRY_RUN:
            warn(f"{label} ('{title}') MISSING (would create under P_ROOT)")
            continue
        body = {
            "parent": {"type": "page_id", "page_id": root_id},
            "properties": {"title": {"title": [rt_text(title)]}},
            "children": blocks,
        }
        page = post("/pages", body)
        PAGE_ID_MAP[label] = page["id"]
        log(f"Created {label} ('{title}') → {page['id']}")
        live = _existing_block_children(page["id"])
        _index_block_ids(label, blocks, live)
        captured = sum(1 for i in range(len(blocks)) if f"{label}_B{i+1}" in BLOCK_ID_MAP)
        log(f"  captured {captured}/{len(blocks)} block ids for {label}")
        time.sleep(0.2)

# ---------------------------------------------------------------------------
# Step 6 — Capture ground-truth snapshot
# ---------------------------------------------------------------------------

_GROUND_TRUTH_ROW_PROP_TYPES = {
    "title", "rich_text", "select", "multi_select", "status", "people",
    "date", "number", "url", "checkbox", "email", "phone_number",
}

def _plain_text(rt_arr: list[dict]) -> str:
    return "".join(seg.get("plain_text", "") for seg in (rt_arr or []))

def _normalize_property_schema(prop: dict) -> dict:
    ptype = prop.get("type", "")
    out: dict = {"type": ptype}
    body = prop.get(ptype) or {}
    if ptype in ("select", "multi_select", "status"):
        out["options"] = sorted(o.get("name", "") for o in body.get("options", []))
    return out

def _normalize_property_value(prop: dict) -> dict | None:
    ptype = prop.get("type", "")
    if ptype not in _GROUND_TRUTH_ROW_PROP_TYPES:
        return None
    body = prop.get(ptype)
    if ptype in ("title", "rich_text"):
        return {"type": ptype, "text": _plain_text(body)}
    if ptype in ("select", "status"):
        return {"type": ptype, "name": (body or {}).get("name")}
    if ptype == "multi_select":
        return {"type": ptype, "names": sorted(o.get("name", "") for o in (body or []))}
    if ptype == "people":
        return {"type": ptype, "user_ids": sorted(p.get("id", "") for p in (body or []))}
    if ptype == "date":
        return {"type": ptype, "start": (body or {}).get("start"), "end": (body or {}).get("end")}
    if ptype in ("number", "url", "email", "phone_number"):
        return {"type": ptype, "value": body}
    if ptype == "checkbox":
        return {"type": ptype, "value": bool(body)}
    return None

def _row_label_index() -> dict[str, str]:
    return {real: label for label, real in ROW_ID_MAP.items() if real}

def _db_label_index() -> dict[str, str]:
    return {real: label for label, real in DB_ID_MAP.items() if real}

def capture_ground_truth(bot_id: str, workspace_name: str) -> dict:
    """Snapshot every seeded entity post-seed so the verifier/reset derive their
    expected state dynamically. Anything inside ``ground_truth`` is the answer
    key; non-seeded drift lives under ``ignore``."""
    section("6. Capturing workspace ground truth")
    truth: dict = {
        "workspace": {"bot_id": bot_id, "name": workspace_name},
        "users":     [],
        "databases": [],
        "rows":      [],
        "pages":     [],
        "page_block_ids": {},
        "ignore":    {"user_ids": [], "page_ids": [], "database_ids": []},
    }
    rows_label = _row_label_index()
    dbs_label = _db_label_index()

    # --- users -----------------------------------------------------------
    try:
        for u in paginate("/users", method="GET"):
            person = u.get("person") or {}
            truth["users"].append({
                "id":    u.get("id"),
                "name":  u.get("name", ""),
                "type":  u.get("type", ""),
                "email": person.get("email", ""),
            })
        log(f"Captured {len(truth['users'])} users")
    except NotionError as e:
        warn(f"/users failed during ground-truth capture: {e}")

    # --- databases (schema) ----------------------------------------------
    for label, real_id in DB_ID_MAP.items():
        try:
            db = get(f"/databases/{real_id}")
        except NotionError as e:
            warn(f"{label} retrieve failed: {e}")
            continue
        properties = {
            name: _normalize_property_schema(prop)
            for name, prop in (db.get("properties") or {}).items()
        }
        truth["databases"].append({
            "label":      label,
            "id":         db.get("id"),
            "title":      _plain_text(db.get("title") or []),
            "properties": properties,
        })
    log(f"Captured {len(truth['databases'])} databases")

    # --- rows ------------------------------------------------------------
    for label in DB_ID_MAP:
        db_real = DB_ID_MAP[label]
        try:
            rows = paginate(f"/databases/{db_real}/query")
        except NotionError as e:
            warn(f"{label} query failed during ground-truth capture: {e}")
            continue
        for row in rows:
            # Only seeded rows are "answer key". Pre-existing/stray rows are left
            # out so reset can archive them as extras (anything not in row_id_map).
            row_label = rows_label.get(row.get("id", ""))
            if not row_label:
                continue
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
                "label":      row_label,
                "db_label":   dbs_label.get(db_real),
                "id":         row.get("id"),
                "title":      title_text,
                "archived":   bool(row.get("archived") or row.get("in_trash")),
                "properties": row_props,
            })
    log(f"Captured {len(truth['rows'])} rows")

    # --- pages -----------------------------------------------------------
    for label, real_id in PAGE_ID_MAP.items():
        try:
            page = get(f"/pages/{real_id}")
        except NotionError as e:
            warn(f"{label} retrieve failed: {e}")
            continue
        title_prop = (page.get("properties") or {}).get("title") or {}
        title_text = _plain_text(title_prop.get("title") or [])
        truth["pages"].append({
            "label":    label,
            "id":       page.get("id"),
            "title":    title_text,
            "archived": bool(page.get("archived") or page.get("in_trash")),
        })
    log(f"Captured {len(truth['pages'])} pages")

    # --- seeded top-level block ids per page (for reset's append cleanup) -
    for label, real_id in BLOCK_ID_MAP.items():
        page_label = label.rsplit("_B", 1)[0]
        truth["page_block_ids"].setdefault(page_label, []).append(real_id)
    log(f"Captured block ids for {len(truth['page_block_ids'])} pages")

    return truth

# ---------------------------------------------------------------------------
# Step 7 — Save state file
# ---------------------------------------------------------------------------

def persist_state(state_path: str, bot_id: str, workspace_name: str) -> None:
    section("7. Saving workspace state")
    if DRY_RUN:
        log(f"Would write state → {state_path}")
        return
    truth = capture_ground_truth(bot_id, workspace_name)
    payload = {
        "workspace_name": workspace_name,
        "bot_id":         bot_id,
        "benchmark_now":  BENCHMARK_NOW.isoformat(),
        "user_id_map":    USER_ID_MAP,
        "db_id_map":      DB_ID_MAP,
        "page_id_map":    PAGE_ID_MAP,
        "row_id_map":     ROW_ID_MAP,
        "block_id_map":   BLOCK_ID_MAP,
        "seeded_at":      datetime.now(timezone.utc).isoformat(),
        "ground_truth":   truth,
    }
    save_state(state_path, payload)
    print("  reset_notion.py reads state['ground_truth'] as the answer key.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN, TOKEN, HEADERS, BOT_ID, WORKSPACE_NAME

    parser = argparse.ArgumentParser(description="Seed Hintas multi-API Notion surface")
    parser.add_argument("--verify", "--dry-run", dest="verify", action="store_true",
                        help="Dry-run: report missing items without creating")
    parser.add_argument("--token", help="Notion integration token (overrides BASELINE_/HINTAS_NOTION_TOKEN)")
    parser.add_argument("--parent-page-id", default=None,
                        help="Root page id to parent everything under (overrides "
                             "BASELINE_/HINTAS_NOTION_PARENT_PAGE_ID and title search)")
    parser.add_argument("--state-file", default=None,
                        help="Override the state file path (default: workspace_state_notion_<stack>.json)")
    add_stack_arg(parser)
    args = parser.parse_args()

    DRY_RUN = args.verify
    set_dry_run(DRY_RUN)

    TOKEN = args.token or stack_env(args.stack, "NOTION_TOKEN")
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

    if not TOKEN:
        err(f"Set {('BASELINE_' if args.stack == 'baseline' else 'HINTAS_')}NOTION_TOKEN env var or pass --token secret_...")
        return 1

    parent_page_id = args.parent_page_id or stack_env(args.stack, "NOTION_PARENT_PAGE_ID")
    state_path = resolve_state_file(args.state_file, "notion", args.stack)

    print(f"\n{'='*60}")
    print(f"  Hintas Multi-API Benchmark — Notion Seeder")
    print(f"  Mode: {'DRY RUN (verify only)' if DRY_RUN else 'LIVE SEED'}")
    print(f"  benchmark_now: {BENCHMARK_NOW.isoformat()}")
    print(f"{'='*60}")

    try:
        BOT_ID, WORKSPACE_NAME = verify_auth()
        resolve_users(BOT_ID)
        find_root_page(parent_page_id)
        create_databases()
        configure_status_options()
        seed_people()
        seed_projects()
        seed_onboarding()
        create_pages()
        persist_state(state_path, BOT_ID, WORKSPACE_NAME)
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
        print(f"  State written for reset_notion.py to consume.")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
