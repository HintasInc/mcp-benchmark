"""
Slack benchmark workspace utilities — HTTP client, console helpers, state.

Imported by reset / seed / verify so each script stays focused on its own
domain logic. The state dicts (``USER_ID_MAP`` etc.) are populated by
``load_state()`` via in-place mutation, so callers can ``from .utils import
USER_ID_MAP`` and the reference stays current after the load.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests

BASE_URL = "https://slack.com/api"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Token / headers
# ---------------------------------------------------------------------------

TOKEN: str = ""
HEADERS: dict = {"Authorization": "", "Content-Type": "application/json; charset=utf-8"}


def set_token(token: str) -> None:
    """Update the token used by ``api`` / ``api_get`` for subsequent calls."""
    global TOKEN
    TOKEN = token
    HEADERS["Authorization"] = f"Bearer {token}"


# Initialise from the env so module import alone is enough for the common case.
set_token(os.environ.get("SLACK_TOKEN", ""))


def load_token_for_stack(stack: str) -> str:
    """
    Resolve the auth token for ``stack`` from the platform manifest.

    Loads ``experiments/slack/.env`` and the repo ``.env`` (without overriding
    already-set env vars), reads the stack's ``token_env`` from ``slack.toml``,
    and returns the value from ``os.environ``. Returns an empty string when the
    var is unset.
    """
    from benchmarking.config import load_platform, load_platform_env

    load_platform_env("slack")
    platform = load_platform("slack")
    stack_cfg = platform.stack(stack)
    return os.environ.get(stack_cfg.token_env, "")


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

DRY_RUN: bool = False


def set_dry_run(value: bool) -> None:
    global DRY_RUN
    DRY_RUN = value


def log(msg: str) -> None:
    prefix = "[DRY]" if DRY_RUN else "[OK ]"
    print(f"  {prefix} {msg}")


def warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def section(title: str) -> None:
    """60-wide framed section header (used by reset and seed)."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def subsection(title: str) -> None:
    """Inline section marker (used by verify)."""
    print(f"\n  ── {title}")


# ---------------------------------------------------------------------------
# Slack HTTP client
# ---------------------------------------------------------------------------

def api(method: str, **kwargs) -> dict:
    """POST to slack.com/api/<method>. Raises ``RuntimeError`` on ``ok=false``."""
    resp = requests.post(f"{BASE_URL}/{method}", headers=HEADERS, json=kwargs)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"{method} failed: {data.get('error')} — {data}")
    return data


def api_get(method: str, params: dict | None = None) -> dict:
    """GET slack.com/api/<method>. Raises ``RuntimeError`` on ``ok=false``."""
    resp = requests.get(f"{BASE_URL}/{method}", headers=HEADERS, params=params or {})
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"GET {method} failed: {data.get('error')} — {data}")
    return data


def api_get_paginated(method: str, params: dict, items_key: str, limit: int = 200) -> list:
    """Accumulate all items across cursor pages."""
    out: list = []
    cursor = None
    while True:
        p = dict(params)
        p["limit"] = limit
        if cursor:
            p["cursor"] = cursor
        data = api_get(method, p)
        out.extend(data.get(items_key, []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return out


# ---------------------------------------------------------------------------
# Workspace state
# ---------------------------------------------------------------------------

# Populated in-place by ``load_state``. Importers can ``from .utils import
# USER_ID_MAP`` and read the dict after load — the reference stays valid.
STATE: dict = {}
USER_ID_MAP: dict[str, str] = {}
CHANNEL_ID_MAP: dict[str, str] = {}
DM_ID_MAP: dict[str, str] = {}
MSG_TS_MAP: dict[str, str] = {}
GROUND_TRUTH: dict = {}
IGNORE_USER_IDS: set[str] = set()
IGNORE_CHANNEL_NAME_RES: list[re.Pattern] = []


def resolve_state_file(explicit_path: str | None, stack: str | None = None) -> str:
    """
    Pick the per-stack state file. Precedence:
      1. ``explicit_path`` (e.g. from ``--state-file``)
      2. ``workspace_state_<stack>.json`` (from ``--stack``)
    Exits if neither is provided.
    """
    if explicit_path:
        return explicit_path
    if stack:
        return os.path.join(SCRIPT_DIR, f"workspace_state_{stack}.json")
    print("ERROR: --stack or --state-file is required to resolve the workspace state file.")
    sys.exit(2)


def load_state(state_path: str, allow_missing: bool = False) -> bool:
    """
    Load a workspace state file into the module-level dicts (in place).

    Returns False if ``allow_missing=True`` and the file is absent.
    Returns True after a successful load. Exits the process on hard errors
    so individual scripts don't need to repeat the boilerplate.
    """
    if not os.path.exists(state_path):
        if allow_missing:
            print(f"  No state file at {state_path} — workspace has not been seeded; reset is a no-op.")
            return False
        print(
            f"ERROR: {state_path} not found. "
            f"Run seed_workspace.py against this workspace first."
        )
        sys.exit(2)

    with open(state_path) as f:
        loaded = json.load(f)

    STATE.clear()
    STATE.update(loaded)

    for target, key in (
        (USER_ID_MAP,    "user_id_map"),
        (CHANNEL_ID_MAP, "channel_id_map"),
        (DM_ID_MAP,      "dm_id_map"),
        (MSG_TS_MAP,     "msg_ts_map"),
    ):
        target.clear()
        target.update(STATE.get(key, {}) or {})

    GROUND_TRUTH.clear()
    GROUND_TRUTH.update(STATE.get("ground_truth", {}) or {})

    ignore = GROUND_TRUTH.get("ignore", {}) or {}
    IGNORE_USER_IDS.clear()
    IGNORE_USER_IDS.update(ignore.get("user_ids", []))
    IGNORE_CHANNEL_NAME_RES.clear()
    IGNORE_CHANNEL_NAME_RES.extend(re.compile(p) for p in ignore.get("channel_name_patterns", []))

    print(f"  Loaded state ← {state_path}")
    return True


def save_state(state_path: str, payload: dict) -> None:
    """Persist a state payload to disk and refresh the in-memory mirror."""
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(payload, f, indent=2)
    STATE.clear()
    STATE.update(payload)


def uid(logical: str) -> str:
    """Resolve a logical user ID (``U05CLAUDE``) to the real Slack ID."""
    return USER_ID_MAP.get(logical, logical)


def cid(logical: str) -> str:
    """Resolve a logical channel ID (``C001GENERAL``) to the real Slack ID."""
    return CHANNEL_ID_MAP.get(logical, logical)


# ---------------------------------------------------------------------------
# Token guard
# ---------------------------------------------------------------------------

def require_token() -> None:
    """Exit with a friendly message when SLACK_TOKEN is missing."""
    if not TOKEN:
        print("ERROR: Set SLACK_TOKEN env var or pass --token xoxp-...")
        sys.exit(1)
