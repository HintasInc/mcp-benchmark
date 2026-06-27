#!/usr/bin/env python3
"""
reset_notion.py  —  Hintas Multi-API Benchmark (Notion surface)

Resets the Notion surface back to the snapshot ``seed_notion.py`` recorded in
``workspace_state_notion.json`` BEFORE every prompt run. Undoes mutations a
prompt may have made. Standalone: reads ``NOTION_TOKEN`` from the environment
(override ``--token``) rather than a platform manifest.

What this resets:
  ✅ Page titles + archived flag on seeded pages (restores drifted titles,
                                     un-archives any seeded page a prompt trashed)
  ✅ Extra child pages under P_ROOT and PG_INCIDENTS (archives prompt-created
                                     incident / onboarding / 'Atlas Migration' pages)
  ✅ Database row property values   (re-writes seeded Status/Assignee/Due/Email/
                                     Team/Person back to the snapshot — restores
                                     e.g. Devon's People Status flipped to Inactive
                                     and Pricing page Status flipped to In review)
  ✅ Extra rows in seeded databases (archives anything not in row_id_map — removes
                                     prompt-created tasks / onboarding rows / a
                                     People row a prompt may have added for Priya)
  ✅ Prompt-appended blocks on append-target pages (archives top-level blocks not
                                     in that page's seeded page_block_ids set)

What this can NOT reset (limits of the Notion API):
  ⚠️  Comments — Notion's API has no delete endpoint for comments. Extra comments
      authored by the integration during a prompt run will accumulate.
  ⚠️  Edited block content — once a seeded block's rich_text is mutated there's no
      API path to recreate it at the same id. Rich-text edits to seeded blocks are
      NOT reverted; re-run seed_notion.py to fully rebuild after destructive prompts.

Exit codes:
    0 — reset succeeded (or nothing to do)
    1 — reset failed (auth, API error)
    2 — state file missing (and --allow-missing-state not set)

Usage:
    export NOTION_TOKEN=secret_...
    python reset_notion.py                 # full reset
    python reset_notion.py --dry-run       # show what would change
    python reset_notion.py --prompt-id 7   # log scope; no behavioral effect today
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

STATE: dict = {}
GROUND_TRUTH: dict = {}
USER_ID_MAP: dict = {}
PAGE_ID_MAP: dict = {}
DB_ID_MAP: dict = {}
ROW_ID_MAP: dict = {}
BLOCK_ID_MAP: dict = {}

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

def delete(path: str) -> dict:
    return _request("DELETE", path)

def paginate(path: str, body: dict | None = None, *, method: str = "POST",
             page_size: int = 100) -> list[dict]:
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
# Rich-text + property builders (mirrors seed_notion.py)
# ---------------------------------------------------------------------------

def rt_text(content: str) -> dict:
    return {"type": "text", "text": {"content": content, "link": None}}

def people_value(logical_ids: list[str]) -> dict:
    refs: list[dict] = []
    for logical in logical_ids:
        real = USER_ID_MAP.get(logical)
        if not real:
            continue
        refs.append({"object": "user", "id": real})
    return {"people": refs}

# ---------------------------------------------------------------------------
# State loading
# ---------------------------------------------------------------------------

def hydrate_state(state_path: str, allow_missing: bool) -> bool:
    """Load the seed state via common.load_state. Returns False on allowed miss."""
    global STATE, GROUND_TRUTH, USER_ID_MAP, PAGE_ID_MAP, DB_ID_MAP, ROW_ID_MAP, BLOCK_ID_MAP
    data = load_state(state_path, allow_missing=allow_missing)
    if data is None:
        return False
    STATE = data
    GROUND_TRUTH = data.get("ground_truth", {})
    USER_ID_MAP  = data.get("user_id_map", {})
    PAGE_ID_MAP  = data.get("page_id_map", {})
    DB_ID_MAP    = data.get("db_id_map", {})
    ROW_ID_MAP   = data.get("row_id_map", {})
    BLOCK_ID_MAP = data.get("block_id_map", {})
    return True

# ---------------------------------------------------------------------------
# Snapshot-driven property rebuilds
#
# Reset re-writes the seeded value of each mutable property from the ground-truth
# snapshot. We reconstruct each property's API write-shape from its normalized
# snapshot value, so a prompt that flipped a Status / Assignee / Due / Email /
# Team / Person is undone without re-deriving the fixture by hand.
# ---------------------------------------------------------------------------

# Property names re-written per database (everything except the title, which is
# restored separately and rarely drifts on a row).
_RESET_PROP_NAMES = {
    "DB_PEOPLE":     ["Email", "Status", "Team"],
    "DB_PROJECTS":   ["Assignee", "Status", "Due", "Owner"],
    "DB_ONBOARDING": ["Status", "Person"],
}

def _prop_write_shape(name: str, snap: dict) -> dict | None:
    """Reconstruct a Notion property write-payload from a normalized snapshot value."""
    ptype = snap.get("type", "")
    if ptype == "status":
        return {"status": {"name": snap.get("name")}} if snap.get("name") else {"status": None}
    if ptype == "select":
        return {"select": {"name": snap.get("name")}} if snap.get("name") else {"select": None}
    if ptype == "multi_select":
        return {"multi_select": [{"name": n} for n in snap.get("names", [])]}
    if ptype == "people":
        return {"people": [{"object": "user", "id": uid} for uid in snap.get("user_ids", [])]}
    if ptype == "date":
        start = snap.get("start")
        if not start:
            return {"date": None}
        inner = {"start": start}
        if snap.get("end"):
            inner["end"] = snap["end"]
        return {"date": inner}
    if ptype == "email":
        return {"email": snap.get("value")}
    if ptype == "url":
        return {"url": snap.get("value")}
    if ptype == "number":
        return {"number": snap.get("value")}
    if ptype == "rich_text":
        return {"rich_text": [rt_text(snap.get("text", ""))]}
    return None

def _rows_for_db(db_label: str) -> list[dict]:
    return [r for r in GROUND_TRUTH.get("rows", []) if r.get("db_label") == db_label]

# ---------------------------------------------------------------------------
# Reset steps
# ---------------------------------------------------------------------------

def reset_pages() -> None:
    """Restore the title of every seeded page; un-archive any seeded page a prompt
    trashed. Then archive extra child pages a prompt created under P_ROOT or
    PG_INCIDENTS that aren't seeded pages/databases."""
    section("1. Restoring seeded pages")
    seeded_pages = {p["label"]: p for p in GROUND_TRUTH.get("pages", [])}

    for label, snap in seeded_pages.items():
        page_id = snap.get("id") or PAGE_ID_MAP.get(label)
        if not page_id:
            warn(f"{label} missing from state; skipping")
            continue
        try:
            page = get(f"/pages/{page_id}")
        except NotionError as e:
            warn(f"{label} retrieve failed: {e}")
            continue

        body: dict = {}
        is_archived = bool(page.get("archived") or page.get("in_trash"))
        if is_archived:  # every seeded page should be live
            body["archived"] = False

        title = snap.get("title", "")
        cur_title_arr = (page.get("properties") or {}).get("title", {}).get("title", [])
        cur_title = "".join(t.get("plain_text", "") for t in cur_title_arr)
        if title and cur_title != title:
            body.setdefault("properties", {})["title"] = {"title": [rt_text(title)]}

        if not body:
            log(f"{label}: clean")
            continue
        if DRY_RUN:
            log(f"{label}: would PATCH {list(body.keys())}")
            continue
        # Un-archive in its own PATCH before any property update.
        if body.get("archived") is False and len(body) > 1:
            patch(f"/pages/{page_id}", {"archived": False})
            del body["archived"]
            time.sleep(0.1)
        patch(f"/pages/{page_id}", body)
        log(f"{label}: restored {list(body.keys())}")
        time.sleep(0.15)

    # Archive prompt-created child pages under P_ROOT and PG_INCIDENTS.
    seeded_page_ids = {p["id"] for p in GROUND_TRUTH.get("pages", []) if p.get("id")}
    seeded_db_ids = {d["id"] for d in GROUND_TRUTH.get("databases", []) if d.get("id")}
    keep_ids = seeded_page_ids | seeded_db_ids
    for parent_label in ["P_ROOT", "PG_INCIDENTS"]:
        parent_id = PAGE_ID_MAP.get(parent_label)
        if not parent_id:
            continue
        try:
            children = paginate(f"/blocks/{parent_id}/children", method="GET")
        except NotionError as e:
            warn(f"{parent_label} children query failed: {e}")
            continue
        extras = [b for b in children
                  if b.get("type") == "child_page" and b["id"] not in keep_ids]
        if not extras:
            log(f"{parent_label}: no extra child pages")
            continue
        if DRY_RUN:
            warn(f"{parent_label}: would archive {len(extras)} extra child page(s)")
            continue
        for b in extras:
            try:
                patch(f"/pages/{b['id']}", {"archived": True})
                log(f"{parent_label}: archived extra child page {b['id']}")
                time.sleep(0.15)
            except NotionError as e:
                warn(f"archive child page {b['id']} failed: {e}")

def reset_db_rows() -> None:
    """Re-write seeded row property values; archive prompt-created extra rows."""
    for db_label in ["DB_PEOPLE", "DB_PROJECTS", "DB_ONBOARDING"]:
        _reset_one_db(db_label)

def _reset_one_db(db_label: str) -> None:
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
    by_id = {r["id"]: r for r in live}

    prop_names = _RESET_PROP_NAMES.get(db_label, [])
    seeded_ids: set[str] = set()
    for snap in _rows_for_db(db_label):
        row_id = snap.get("id")
        if not row_id:
            continue
        seeded_ids.add(row_id)
        live_row = by_id.get(row_id)
        if live_row is None:
            warn(f"{snap.get('label')} ({row_id}) not found in {db_label} live results; "
                 "may have been hard-deleted. Re-run seed_notion.py.")
            continue

        props: dict = {}
        snap_props = snap.get("properties", {})
        for name in prop_names:
            psnap = snap_props.get(name)
            if not psnap:
                continue
            shape = _prop_write_shape(name, psnap)
            if shape is not None:
                props[name] = shape
        # Title restore (rarely drifts but cheap to re-assert).
        title = snap.get("title", "")
        title_name = next((n for n, p in snap_props.items() if p.get("type") == "title"), None)
        if title and title_name:
            props[title_name] = {"title": [rt_text(title)]}

        needs_unarchive = bool(live_row.get("archived") or live_row.get("in_trash"))
        if DRY_RUN:
            log(f"{snap.get('label')}: would restore {sorted(props)} (archived={needs_unarchive})")
            continue
        try:
            if needs_unarchive:
                patch(f"/pages/{row_id}", {"archived": False})
                time.sleep(0.1)
            if props:
                patch(f"/pages/{row_id}", {"properties": props})
            log(f"{snap.get('label')}: restored")
        except NotionError as e:
            warn(f"{snap.get('label')} restore failed: {e}")
        time.sleep(0.15)

    # Archive any extra rows a prompt created.
    extras = [rid for rid in by_id
              if rid not in seeded_ids
              and not (by_id[rid].get("archived") or by_id[rid].get("in_trash"))]
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

def reset_appended_blocks() -> None:
    """For each append-target page, archive top-level blocks not in its seeded set."""
    section("3. Archiving prompt-appended blocks")
    page_block_ids = GROUND_TRUTH.get("page_block_ids", {})
    targets = ["PG_RELEASE_NOTES", "PG_WEEKLY", "PG_ALLHANDS",
               "PG_LEAD_JARED", "PG_LEAD_PINKMAN", "PG_LEAD_LAGOON"]
    for page_label in targets:
        page_id = PAGE_ID_MAP.get(page_label)
        if not page_id:
            continue
        seeded = set(page_block_ids.get(page_label, []))
        if not seeded:
            # No seeded ids recorded for this page (older/partial state). Skip
            # rather than treat every block as an extra — deleting seeded blocks
            # is irreversible.
            warn(f"{page_label}: no seeded block ids in state — skipping (would risk deleting seeded content)")
            continue
        try:
            children = paginate(f"/blocks/{page_id}/children", method="GET")
        except NotionError as e:
            warn(f"{page_label} children query failed: {e}")
            continue
        # Only hard-delete leaf blocks the prompt appended; nested child pages /
        # databases are handled (archived, recoverable) by reset_pages.
        extras = [b["id"] for b in children
                  if b["id"] not in seeded
                  and b.get("type") not in ("child_page", "child_database")]
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

    parser = argparse.ArgumentParser(description="Reset Hintas multi-API Notion surface")
    parser.add_argument("--prompt-id", default=None,
                        help="Optional: log which prompt this reset is for (no behavioral effect today)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without mutating state")
    parser.add_argument("--token", help="Notion integration token (overrides BASELINE_/HINTAS_NOTION_TOKEN)")
    parser.add_argument("--parent-page-id", default=None,
                        help="Optional root page id (accepted for symmetry with the seeder; "
                             "reset resolves ids from the state file)")
    parser.add_argument("--state-file", default=None,
                        help="Override the state file path (default: workspace_state_notion_<stack>.json)")
    parser.add_argument("--allow-missing-state", action="store_true",
                        help="If the state file is missing (e.g. first run before seed), "
                             "exit 0 instead of erroring")
    add_stack_arg(parser)
    args = parser.parse_args()

    DRY_RUN = args.dry_run
    set_dry_run(DRY_RUN)

    TOKEN = args.token or stack_env(args.stack, "NOTION_TOKEN")
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

    if not TOKEN:
        err(f"Set {('BASELINE_' if args.stack == 'baseline' else 'HINTAS_')}NOTION_TOKEN env var or pass --token secret_...")
        return 1

    state_path = resolve_state_file(args.state_file, "notion", args.stack)

    print(f"\n{'='*60}")
    print(f"  Hintas Multi-API Benchmark — Notion Reset")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE RESET'}")
    if args.prompt_id:
        print(f"  Scope: prompt {args.prompt_id}")
    print(f"{'='*60}")

    try:
        if not hydrate_state(state_path, allow_missing=args.allow_missing_state):
            return 0
        reset_pages()
        reset_db_rows()
        reset_appended_blocks()
    except NotionError as e:
        err(f"Notion API error: {e}\n  body: {json.dumps(e.body, indent=2)}")
        return 1
    except KeyboardInterrupt:
        err("Interrupted by user.")
        return 1

    print(f"\n{'='*60}")
    print(f"  {'DRY RUN COMPLETE' if DRY_RUN else 'RESET COMPLETE'}")
    print(f"  Note: comments cannot be deleted via the Notion API, and rich-text")
    print(f"  edits to seeded blocks are NOT reverted. Re-run seed_notion.py to")
    print(f"  fully rebuild after destructive prompts.")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
