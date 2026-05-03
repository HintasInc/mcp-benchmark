#!/usr/bin/env python3
"""
reset_workspace.py  —  Hintas Notion Benchmark v1

Resets the workspace back to the snapshot defined in workspace_state.md
BEFORE every prompt run. Undoes any mutations a prompt may have made.

Usage:
    export NOTION_TOKEN=secret_...   # or set HINTAS_TOKEN, etc. per stack
    python reset_workspace.py --stack notion              # full reset
    python reset_workspace.py --stack hintas --prompt-id 22  # log scope; no behavioral effect today
    python reset_workspace.py --stack notion --dry-run    # show what would change

State-file and auth-token resolution come from notion.toml's
``state_file_template`` and the matching stack's ``token_env``.

What this resets:
  ✅ Database row property values  (re-writes seeded values for known rows)
  ✅ Archived state of seeded rows  (un-archives any seed row the prompt trashed)
  ✅ Extra rows in seeded databases (archives anything not in row_id_map)
  ✅ P10_PLAYTEST_A3 archive flag   (re-archives if a prompt restored it)
  ✅ Page children added by prompts (archives any block on a seeded page that
                                     isn't in block_id_map; only top-level)
  ✅ Property updates on seeded pages (restores P02..P09 page titles and icons)
  ✅ Database schema drift on primitive properties (re-types/re-creates columns
                                     an agent retyped/renamed/deleted; archives
                                     unexpected columns the agent added)

What this can NOT reset (limits of the Notion API):
  ⚠️  Deleted/edited block content — once a block's rich_text is mutated or the
      block is trashed, there's no API path to recreate it at the same id.
      Re-run seed_workspace.py to fully rebuild after destructive prompts.
  ⚠️  Comments — Notion's API has no delete endpoint for comments. Extra
      comments authored by the integration during a prompt run will accumulate.
  ⚠️  Relation property drift — if a relation column is retyped, this script
      warns but does not rebuild it (rebuild requires the target DB id).
      Re-run seed_workspace.py.
  ⚠️  Select / status option drift — option lists and colors aren't rebuilt.
      Re-run seed_workspace.py if options were renamed or removed.

Exit codes:
    0 — reset succeeded (or nothing to do)
    1 — reset failed (auth, missing state, API error)
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

DRY_RUN = False

STATE: dict = {}
USER_ID_MAP: dict = {}
PAGE_ID_MAP: dict = {}
DB_ID_MAP: dict = {}
ROW_ID_MAP: dict = {}
BLOCK_ID_MAP: dict = {}

# ---------------------------------------------------------------------------
# Logging
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
        raise NotionError(resp.status_code, body)
    return resp.json() if resp.text else {}

def get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params or {})

def post(path: str, body: dict | None = None) -> dict:
    return _request("POST", path, json=body or {})

def patch(path: str, body: dict | None = None) -> dict:
    return _request("PATCH", path, json=body or {})

def delete(path: str) -> dict:
    return _request("DELETE", path)

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
# State loading
# ---------------------------------------------------------------------------

def load_state(path: str, allow_missing: bool = False) -> bool:
    global STATE, USER_ID_MAP, PAGE_ID_MAP, DB_ID_MAP, ROW_ID_MAP, BLOCK_ID_MAP
    if not os.path.exists(path):
        if allow_missing:
            print(f"  No state file at {path} — workspace has not been seeded; reset is a no-op.")
            return False
        err(f"{path} not found. Run seed_workspace.py first.")
        sys.exit(1)
    with open(path) as f:
        STATE = json.load(f)
    USER_ID_MAP   = STATE.get("user_id_map", {})
    PAGE_ID_MAP   = STATE.get("page_id_map", {})
    DB_ID_MAP     = STATE.get("db_id_map", {})
    ROW_ID_MAP    = STATE.get("row_id_map", {})
    BLOCK_ID_MAP  = STATE.get("block_id_map", {})
    print(f"  Loaded state ← {path}")
    return True

def uid(label: str) -> str | None:
    return USER_ID_MAP.get(label)

# ---------------------------------------------------------------------------
# Rich-text + property builders (mirrors seed_workspace.py)
# ---------------------------------------------------------------------------

def rt_text(content: str) -> dict:
    return {"type": "text", "text": {"content": content, "link": None}}

def rt_mention_user(user_id: str) -> dict:
    return {"type": "mention", "mention": {"type": "user", "user": {"id": user_id}}}

def rt_mention_page(page_id: str) -> dict:
    return {"type": "mention", "mention": {"type": "page", "page": {"id": page_id}}}

def date_at(days_offset: float) -> str:
    return (BENCHMARK_NOW + timedelta(days=days_offset)).date().isoformat()

def datetime_at(days_offset: float, hour: int, minute: int) -> str:
    base = (BENCHMARK_NOW + timedelta(days=days_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base.isoformat()

# ---------------------------------------------------------------------------
# Expected row state (single source of truth shared with verify_workspace.py)
# ---------------------------------------------------------------------------

PROJECTS_EXPECTED = [
    ("PROJ_TOMB3",   "Tomb-3",         "U01MIRANDA", "Active"),
    ("PROJ_LAUNCH",  "Launch 2026",    "U04LAGOON",  "Active"),
    ("PROJ_OFFSITE", "Lisbon offsite", "U05CLAUDE",  "On hold"),
]

TASKS_EXPECTED = [
    ("TASK_FIX_TILE_LOADER",   "Fix async tile loader chunk drop",   "U06DEVON",   +2,  "In progress", "P0", 2, ["eng","launch-blocker"],         "PROJ_TOMB3"),
    ("TASK_TOMB3_LIGHTING",    "Polish tomb-3 lighting passes B & C","U01MIRANDA", +4,  "In progress", "P1", 3, ["design"],                       "PROJ_TOMB3"),
    ("TASK_PRESS_LIST",        "Finalize press contact list",        "U04LAGOON",  +3,  "Up Next",     "P1", 1, ["marketing","launch-blocker"],   "PROJ_LAUNCH"),
    ("TASK_TRAILER_COPY",      "Write final trailer copy",           "U04LAGOON",  +2,  "In progress", "P0", 1, ["marketing","launch-blocker"],   "PROJ_LAUNCH"),
    ("TASK_BRAND_KIT",         "Brand-kit handoff to PR firm",       "U01MIRANDA", -2,  "In progress", "P1", 1, ["marketing","design"],           "PROJ_LAUNCH"),
    ("TASK_BUG247_VERIFY",     "Verify BUG-247 fix on macOS 14.4",   "U08TOMAS",   +3,  "Up Next",     "P0", 1, ["qa","launch-blocker"],          "PROJ_TOMB3"),
    ("TASK_CONCEPT_REVIEW",    "Concept review session — tomb-3",    "U05CLAUDE",  -4,  "Done",        "P2", 1, ["design"],                       "PROJ_TOMB3"),
    ("TASK_CHANGELOG",         "Draft alpha-build changelog",        "U02JARED",   +7,  "Backlog",     "P2", 1, ["eng"],                          "PROJ_LAUNCH"),
    ("TASK_LISBON_LOGISTICS",  "Book Lisbon offsite flights",        "U04LAGOON", +26,  "Backlog",     "P3", 2, [],                               "PROJ_OFFSITE"),
    ("TASK_MIGRATE_INVENTORY", "Migrate inventory schema to v3",     "U06DEVON",  +12,  "Backlog",     "P2", 5, ["eng"],                          "PROJ_TOMB3"),
    ("TASK_RHEA_INPUT_REBIND", "Input rebind UI polish",             "U07RHEA",   +11,  "Backlog",     "P2", 2, ["eng"],                          "PROJ_TOMB3"),
    ("TASK_QA_REGRESSION",     "Run regression suite on alpha",      "U03PINKMAN", +5,  "Up Next",     "P1", 2, ["qa","launch-blocker"],          "PROJ_LAUNCH"),
]

BUGS_EXPECTED = [
    ("BUG245", "Audio desync after cutscene",                          "BUG-245", "Medium",  "In progress", "U08TOMAS",   "U06DEVON", ["macOS","Windows"],                  -11, None,                  None),
    ("BUG246", "Main-menu flicker on launch",                          "BUG-246", "Low",     "Open",        "U03PINKMAN", None,       ["macOS"],                            -13, None,                  None),
    ("BUG247", "Save-file corruption on macOS",                        "BUG-247", "Blocker", "In progress", "U03PINKMAN", "U06DEVON", ["macOS"],                             -6, "TASK_FIX_TILE_LOADER","https://ci.hintas.co/builds/842"),
    ("BUG248", "Tomb-3 door collider blocks player on revisit",        "BUG-248", "High",    "Open",        "U03PINKMAN", "U07RHEA",  ["macOS","Windows"],                   -4, None,                  None),
    ("BUG230", "Settings dialog scrollbar overlap",                    "BUG-230", "Low",     "Fixed",       "U08TOMAS",   "U07RHEA",  ["Windows"],                          -45, None,                  None),
    ("BUG231", "Save thumbnail blurry at 1080p",                       "BUG-231", "Low",     "Won't Fix",   "U03PINKMAN", None,       ["Windows","Linux"],                  -50, None,                  None),
    ("BUG244", "Localization: French quote marks",                     "BUG-244", "Medium",  "Fixed",       "U04LAGOON",  "U07RHEA",  ["macOS","Windows","Linux","Switch"], -18, None,                  None),
]

MEETING_NOTES_EXPECTED = [
    ("MTG_TOMB3_REVIEW",  "Tomb-3 design review",          -7, 14, 0, ["U01MIRANDA","U05CLAUDE","U07RHEA"],                    "design-review",
        "@Miranda to push the warm-rim lighting on angle B; followup tracked in @[Tomb-3 Level Design].",  ["TASK_TOMB3_LIGHTING"]),
    ("MTG_BUG247_TRIAGE", "BUG-247 triage",                -6, 11, 0, ["U02JARED","U03PINKMAN","U06DEVON"],                    "standup",
        "@Jared owns escalation. @Devon investigates async streamer. See @[Tomb-3 Level Design] notes.",   ["TASK_FIX_TILE_LOADER","TASK_BUG247_VERIFY"]),
    ("MTG_LAUNCH_STANDUP","Launch standup",                -2,  9, 0, ["U01MIRANDA","U02JARED","U04LAGOON","U05CLAUDE"],       "standup",
        "Marketing is 60% ready. @Lagoon: trailer copy by Tuesday EOD. @Miranda: brand kit signed off.",   ["TASK_TRAILER_COPY","TASK_PRESS_LIST"]),
    ("MTG_ALL_HANDS",     "April all-hands",              -13, 11, 0, ["U01MIRANDA","U02JARED","U03PINKMAN","U04LAGOON","U05CLAUDE","U06DEVON","U07RHEA","U08TOMAS"], "all-hands",
        "Recap of milestones; @Miranda demoed tomb-3 stills.",                                              []),
    ("MTG_QA_RETRO",      "QA retro — alpha round 2",     -20, 15, 0, ["U03PINKMAN","U08TOMAS","U02JARED"],                    "retro",
        "Three repeat regressions; @Pinkman to set up nightly smoke run.",                                  []),
    ("MTG_ENG_PLANNING",  "Eng planning — week of 4/13",   -6, 10, 0, ["U02JARED","U06DEVON","U07RHEA"],                       "standup",
        "Sprint goals locked. @Rhea on input UI; @Devon on inventory v3 spike.",                            ["TASK_RHEA_INPUT_REBIND","TASK_MIGRATE_INVENTORY"]),
    ("MTG_PRESS_PREP",    "Press preview prep",            -4, 13, 0, ["U04LAGOON","U05CLAUDE"],                               "standup",
        "Coverage embargo set to 2026-05-03. @Lagoon: press list. @Claude: legal review.",                  ["TASK_PRESS_LIST"]),
    ("MTG_LEADS_SYNC",    "Leads sync",                   -10, 16, 0, ["U01MIRANDA","U02JARED","U03PINKMAN","U04LAGOON"],      "retro",
        "Cadence locked: weekly Wednesdays. @Jared owns the agenda.",                                       []),
]

PAGE_TITLES = {
    "P02_TEAM_DIR":           ("Team Directory",          "👥"),
    "P03_PROJECTS":           ("Projects",                "📁"),
    "P04_TOMB3":              ("Tomb-3 Level Design",     "🗿"),
    "P05_LAUNCH26":           ("Launch 2026",             "🚀"),
    "P06_MEETING_NOTES_HOME": ("Meeting Notes",           "📝"),
    "P07_PLAYTEST_ARCHIVE":   ("Playtest Archive",        "📦"),
    "P09_PLAYTEST_A2":        ("Playtest — alpha round 2", None),
    "P10_PLAYTEST_A3":        ("Playtest — alpha round 3", None),
}

# Primitive property spec for each DB. Mirrors db_schema_*() in seed_workspace.py
# but omits select/multi_select option lists (we only rebuild on type drift; the
# original options stay intact when the type is unchanged). Relation columns are
# not in this spec — see RELATION_PROPS.
SCHEMA_SPEC: dict[str, dict[str, dict]] = {
    "DB_TASKS": {
        "Task":     {"title": {}},
        "Owner":    {"people": {}},
        "Due":      {"date": {}},
        "Status":   {"status": {}},
        "Priority": {"select": {}},
        "Estimate": {"number": {"format": "number"}},
        "Tags":     {"multi_select": {}},
    },
    "DB_BUGS": {
        "Title":    {"title": {}},
        "Bug ID":   {"rich_text": {}},
        "Severity": {"select": {}},
        "Status":   {"status": {}},
        "Reporter": {"people": {}},
        "Assignee": {"people": {}},
        "Platform": {"multi_select": {}},
        "Filed":    {"date": {}},
        "URL":      {"url": {}},
    },
    "DB_PROJECTS": {
        "Name":   {"title": {}},
        "Lead":   {"people": {}},
        "Status": {"status": {}},
    },
    "DB_MEETING_NOTES": {
        "Title":      {"title": {}},
        "Date":       {"date": {}},
        "Attendees":  {"people": {}},
        "Type":       {"select": {}},
        "Follow-ups": {"rich_text": {}},
    },
}

RELATION_PROPS: dict[str, set[str]] = {
    "DB_TASKS":         {"Project"},
    "DB_BUGS":          {"Related Task"},
    "DB_MEETING_NOTES": {"Action Items"},
}

# ---------------------------------------------------------------------------
# People / mention helpers
# ---------------------------------------------------------------------------

def people_value(logical_ids: list[str]) -> dict:
    refs: list[dict] = []
    for logical in logical_ids:
        real = uid(logical)
        if not real:
            continue
        refs.append({"object": "user", "id": real})
    return {"people": refs}

def follow_ups_segments(template: str) -> list[dict]:
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

    segments: list[dict] = []
    i = 0
    while i < len(template):
        next_idx = len(template)
        next_token = None
        for tok in repl:
            j = template.find(tok, i)
            if j != -1 and j < next_idx:
                next_idx = j
                next_token = tok
        if next_token is None:
            segments.append(rt_text(template[i:]))
            break
        if next_idx > i:
            segments.append(rt_text(template[i:next_idx]))
        segments.extend(repl[next_token])
        i = next_idx + len(next_token)
    return segments

def relation_value(row_labels: list[str]) -> dict:
    return {"relation": [{"id": ROW_ID_MAP[lbl]} for lbl in row_labels if lbl in ROW_ID_MAP]}

# ---------------------------------------------------------------------------
# Reset steps
# ---------------------------------------------------------------------------

def reset_pages() -> None:
    """Restore archived flag, title, and icon on every seeded page."""
    section("1. Restoring seeded pages")
    for label, (title, icon) in PAGE_TITLES.items():
        page_id = PAGE_ID_MAP.get(label)
        if not page_id:
            warn(f"{label} missing from state; skipping")
            continue
        try:
            page = get(f"/pages/{page_id}")
        except NotionError as e:
            warn(f"{label} retrieve failed: {e}")
            continue

        # Re-archive P10_PLAYTEST_A3; un-archive everyone else.
        should_archive = (label == "P10_PLAYTEST_A3")
        is_archived = bool(page.get("archived") or page.get("in_trash"))
        body: dict = {}
        if is_archived != should_archive:
            body["archived"] = should_archive

        # Title drift
        cur_title_arr = (page.get("properties") or {}).get("title", {}).get("title", [])
        cur_title = "".join(t.get("plain_text", "") for t in cur_title_arr)
        if cur_title != title:
            body.setdefault("properties", {})["title"] = {"title": [rt_text(title)]}

        # Icon drift (only if originally seeded with one)
        if icon:
            cur_icon = (page.get("icon") or {}).get("emoji")
            if cur_icon != icon:
                body["icon"] = {"type": "emoji", "emoji": icon}

        if not body:
            log(f"{label}: clean")
            continue
        if DRY_RUN:
            log(f"{label}: would PATCH {list(body.keys())}")
            continue
        # If the page was archived, you must unarchive in a separate PATCH
        # before issuing further property updates.
        if "archived" in body and body["archived"] is False and len(body) > 1:
            patch(f"/pages/{page_id}", {"archived": False})
            del body["archived"]
            time.sleep(0.1)
        patch(f"/pages/{page_id}", body)
        log(f"{label}: restored {list(body.keys())}")
        time.sleep(0.15)

def reset_db_schemas() -> None:
    """Re-assert primitive property types and remove agent-added columns.

    Catches drift like an agent retyping ``Estimate`` from number to text or
    renaming ``Filed`` → ``Reported``. Without this step, downstream row resets
    fail with HTTP 400 ``... is expected to be <other_type>``.
    """
    section("2. Asserting database schemas")
    for db_label, spec in SCHEMA_SPEC.items():
        db_id = DB_ID_MAP.get(db_label)
        if not db_id:
            warn(f"{db_label} missing from state; skipping schema reset")
            continue
        try:
            db = get(f"/databases/{db_id}")
        except NotionError as e:
            warn(f"{db_label} retrieve failed: {e}")
            continue
        live = db.get("properties", {})
        patch_body: dict = {}

        expected_title = next((n for n, d in spec.items() if next(iter(d)) == "title"), None)
        live_title = next((n for n, d in live.items() if d.get("type") == "title"), None)
        if expected_title and live_title and live_title != expected_title:
            patch_body[live_title] = {"name": expected_title}

        for name, defn in spec.items():
            if name == expected_title:
                continue
            want_type = next(iter(defn))
            cur_type = live.get(name, {}).get("type")
            if cur_type != want_type:
                patch_body[name] = defn

        keep = set(spec) | RELATION_PROPS.get(db_label, set())
        for live_name, live_def in live.items():
            if live_def.get("type") == "title":
                continue
            if live_name in keep or live_name in patch_body:
                continue
            patch_body[live_name] = None

        for rel_name in RELATION_PROPS.get(db_label, set()):
            cur_type = live.get(rel_name, {}).get("type")
            if cur_type and cur_type != "relation":
                warn(f"{db_label}.{rel_name} drifted to {cur_type}; re-run seed_workspace.py")

        if not patch_body:
            log(f"{db_label}: schema clean")
            continue
        if DRY_RUN:
            log(f"{db_label}: would PATCH schema {sorted(patch_body)}")
            continue
        try:
            patch(f"/databases/{db_id}", {"properties": patch_body})
            log(f"{db_label}: schema asserted ({sorted(patch_body)})")
        except NotionError as e:
            warn(f"{db_label} schema reset failed: {e}")
        time.sleep(0.2)

def reset_projects() -> None:
    _reset_db_rows(
        db_label="DB_PROJECTS",
        title_prop="Name",
        expected=[(label, name, lambda lead=lead, status=status: {
            "Name":   {"title": [rt_text(name)]},
            "Lead":   people_value([lead]),
            "Status": {"status": {"name": status}},
        }) for (label, name, lead, status) in PROJECTS_EXPECTED],
    )

def reset_tasks() -> None:
    expected = []
    for (label, task, owner, due_off, status, prio, est, tags, project) in TASKS_EXPECTED:
        def build(task=task, owner=owner, due_off=due_off, status=status, prio=prio, est=est, tags=tags, project=project):
            return {
                "Task":     {"title": [rt_text(task)]},
                "Owner":    people_value([owner]),
                "Due":      {"date": {"start": date_at(due_off)}},
                "Status":   {"status": {"name": status}},
                "Priority": {"select": {"name": prio}},
                "Estimate": {"number": est},
                "Tags":     {"multi_select": [{"name": n} for n in tags]},
                "Project":  relation_value([project]),
            }
        expected.append((label, task, build))
    _reset_db_rows(db_label="DB_TASKS", title_prop="Task", expected=expected)

def reset_bugs() -> None:
    expected = []
    for (label, title, bug_id, sev, status, reporter, assignee, platforms, filed_off, rel_task, url) in BUGS_EXPECTED:
        def build(title=title, bug_id=bug_id, sev=sev, status=status, reporter=reporter, assignee=assignee,
                  platforms=platforms, filed_off=filed_off, rel_task=rel_task, url=url):
            props = {
                "Title":    {"title": [rt_text(title)]},
                "Bug ID":   {"rich_text": [rt_text(bug_id)]},
                "Severity": {"select": {"name": sev}},
                "Status":   {"status": {"name": status}},
                "Reporter": people_value([reporter]),
                "Assignee": people_value([assignee] if assignee else []),
                "Platform": {"multi_select": [{"name": n} for n in platforms]},
                "Filed":    {"date": {"start": date_at(filed_off)}},
                "URL":      {"url": url},
            }
            if rel_task:
                props["Related Task"] = relation_value([rel_task])
            else:
                props["Related Task"] = {"relation": []}
            return props
        expected.append((label, title, build))
    _reset_db_rows(db_label="DB_BUGS", title_prop="Title", expected=expected)

def reset_meeting_notes() -> None:
    expected = []
    for (label, title, day_off, hh, mm, attendees, mtg_type, follow_template, action_items) in MEETING_NOTES_EXPECTED:
        def build(title=title, day_off=day_off, hh=hh, mm=mm, attendees=attendees, mtg_type=mtg_type,
                  follow_template=follow_template, action_items=action_items):
            props = {
                "Title":      {"title": [rt_text(title)]},
                "Date":       {"date": {"start": datetime_at(day_off, hh, mm)}},
                "Attendees":  people_value(attendees),
                "Type":       {"select": {"name": mtg_type}},
                "Follow-ups": {"rich_text": follow_ups_segments(follow_template)},
                "Action Items": relation_value(action_items),
            }
            return props
        expected.append((label, title, build))
    _reset_db_rows(db_label="DB_MEETING_NOTES", title_prop="Title", expected=expected)

def _reset_db_rows(*, db_label: str, title_prop: str, expected: list) -> None:
    section(f"2. Resetting {db_label} rows")
    db_id = DB_ID_MAP.get(db_label)
    if not db_id:
        warn(f"{db_label} missing from state; skipping")
        return
    try:
        live = paginate(f"/databases/{db_id}/query")
    except NotionError as e:
        warn(f"{db_label} query failed: {e}")
        return

    by_id: dict[str, dict] = {r["id"]: r for r in live}

    seeded_ids: set[str] = set()
    for (label, _title, build_fn) in expected:
        seeded_id = ROW_ID_MAP.get(label)
        if not seeded_id:
            warn(f"{label} not in state; skipping")
            continue
        seeded_ids.add(seeded_id)
        live_row = by_id.get(seeded_id)
        if live_row is None:
            warn(f"{label} ({seeded_id}) not found in {db_label} live results; may have been hard-deleted. Re-run seed.")
            continue
        body: dict = {}
        if live_row.get("archived"):
            body["archived"] = False
        body["properties"] = build_fn()
        if DRY_RUN:
            log(f"{label}: would restore properties (archived={live_row.get('archived')})")
            continue
        try:
            if body.get("archived") is False:
                patch(f"/pages/{seeded_id}", {"archived": False})
                time.sleep(0.1)
                patch(f"/pages/{seeded_id}", {"properties": body["properties"]})
            else:
                patch(f"/pages/{seeded_id}", {"properties": body["properties"]})
            log(f"{label}: restored")
        except NotionError as e:
            warn(f"{label} restore failed: {e}")
        time.sleep(0.15)

    # Archive any rows the agent created that aren't in our seed.
    extras = [rid for rid in by_id if rid not in seeded_ids and not by_id[rid].get("archived")]
    if not extras:
        log(f"{db_label}: no extra rows to archive")
        return
    if DRY_RUN:
        warn(f"{db_label}: would archive {len(extras)} extra row(s)")
        return
    for rid in extras:
        try:
            patch(f"/pages/{rid}", {"archived": True})
            log(f"{db_label}: archived extra row {rid}")
            time.sleep(0.15)
        except NotionError as e:
            warn(f"archive extra {rid} failed: {e}")

def archive_extra_blocks_on_seeded_pages() -> None:
    """For each seeded page, archive top-level blocks not in BLOCK_ID_MAP."""
    section("3. Archiving prompt-added blocks on seeded pages")
    seeded_block_ids = set(BLOCK_ID_MAP.values())
    for page_label in ["P02_TEAM_DIR", "P04_TOMB3", "P05_LAUNCH26", "P09_PLAYTEST_A2"]:
        page_id = PAGE_ID_MAP.get(page_label)
        if not page_id:
            continue
        try:
            children = paginate(f"/blocks/{page_id}/children", method="GET")
        except NotionError as e:
            warn(f"{page_label} children query failed: {e}")
            continue
        extras = [b["id"] for b in children if b["id"] not in seeded_block_ids]
        if not extras:
            log(f"{page_label}: no extra blocks")
            continue
        if DRY_RUN:
            warn(f"{page_label}: would archive {len(extras)} extra block(s)")
            continue
        for bid in extras:
            try:
                delete(f"/blocks/{bid}")
                log(f"{page_label}: deleted extra block {bid}")
                time.sleep(0.15)
            except NotionError as e:
                warn(f"delete block {bid} failed: {e}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN, TOKEN, HEADERS

    parser = argparse.ArgumentParser(description="Reset Hintas Notion benchmark workspace")
    parser.add_argument("--prompt-id", default=None,
                        help="Optional: log which prompt this reset is for (no behavioral effect today)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without mutating state")
    parser.add_argument("--stack", required=True,
                        help="Stack name (e.g. notion, hintas). Resolves the state file and "
                             "auth token from notion.toml.")
    parser.add_argument("--token", help="Notion integration token (overrides NOTION_TOKEN)")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. first run before seed), "
                             "exit 0 instead of erroring")
    args = parser.parse_args()

    DRY_RUN = args.dry_run

    state_file, stack_token = _resolve_stack_paths(args.stack)

    if args.token:
        TOKEN = args.token
    elif stack_token:
        TOKEN = stack_token
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

    if not TOKEN:
        err("Set NOTION_TOKEN env var or pass --token secret_...")
        return 1

    print(f"\n{'='*60}")
    print(f"  Hintas Notion Benchmark — Workspace Reset")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Scope: prompt {args.prompt_id}")
    print(f"{'='*60}")

    try:
        if not load_state(state_file, allow_missing=args.allow_missing_state):
            return 0
        reset_pages()
        reset_db_schemas()
        reset_projects()
        reset_tasks()
        reset_bugs()
        reset_meeting_notes()
        archive_extra_blocks_on_seeded_pages()
    except NotionError as e:
        err(f"Notion API error: {e}\n  body: {json.dumps(e.body, indent=2)}")
        return 1

    print(f"\n{'='*60}")
    print(f"  {'DRY RUN COMPLETE' if DRY_RUN else 'RESET COMPLETE'}")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
