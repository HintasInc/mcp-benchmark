"""
Gmail benchmark workspace utilities — Discovery client, console helpers,
state, and substitution.

Imported by reset / seed / verify so each script stays focused on its own
domain logic. The state dicts (``THREAD_ID_MAP`` etc.) are populated by
``load_state()`` via in-place mutation, so callers can ``from utils import
THREAD_ID_MAP`` and the reference stays current after the load.

Authentication: each Gmail stack has its own Google Cloud OAuth client.
``build_service(stack)`` resolves the client id, client secret, and refresh
token from the platform manifest + env, mints credentials, and builds a
``gmail/v1`` Discovery resource. The googleapiclient library handles access-
token refresh transparently on each request.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Scopes the seed/reset/verify scripts assume (union of core + extension).
# Individual prompts declare their own required_scopes; this is the seeder's
# capability surface. NOTE: not passed to Credentials() — google-auth would
# send these as the `scope` param on refresh, and Google rejects with
# `invalid_scope` unless they exactly match the scopes the refresh token was
# minted with. The refresh token already carries its authorized scopes;
# Gmail enforces them per request.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.metadata",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
]


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
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def subsection(title: str) -> None:
    print(f"\n  ── {title}")


# ---------------------------------------------------------------------------
# Discovery service
# ---------------------------------------------------------------------------

SERVICE: Resource | None = None


def load_token_for_stack(stack: str) -> str:
    """Return the refresh-token env value for ``stack`` from the manifest."""
    from benchmarking.config import load_platform, load_platform_env

    load_platform_env("gmail")
    platform = load_platform("gmail")
    stack_cfg = platform.stack(stack)
    return os.environ.get(stack_cfg.token_env, "")


def load_client_for_stack(stack: str) -> tuple[str, str]:
    """Return ``(client_id, client_secret)`` for ``stack`` from the env.

    Each stack has its own Google Cloud OAuth client per IMPLEMENTATION.md.
    The env vars are named ``<STACK_UPPER>_CLIENT_ID`` and
    ``<STACK_UPPER>_CLIENT_SECRET`` (e.g. ``GMAIL_CLIENT_ID``).
    """
    from benchmarking.config import load_platform_env

    load_platform_env("gmail")
    prefix = stack.upper()
    return (
        os.environ.get(f"{prefix}_CLIENT_ID", ""),
        os.environ.get(f"{prefix}_CLIENT_SECRET", ""),
    )


def build_service(
    stack: str,
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> Resource:
    """Build a Gmail Discovery resource for ``stack`` and stash it on the module.

    Any ``refresh_token`` / ``client_id`` / ``client_secret`` passed in
    overrides the manifest/env lookup (used by ``--token`` and tests).
    Exits with a friendly message when any of the three credentials is
    missing.
    """
    global SERVICE

    if refresh_token is None:
        refresh_token = load_token_for_stack(stack)
    if client_id is None or client_secret is None:
        cid_env, csecret_env = load_client_for_stack(stack)
        client_id = client_id or cid_env
        client_secret = client_secret or csecret_env

    missing = [
        name
        for name, value in (
            (f"{stack.upper()}_CLIENT_ID", client_id),
            (f"{stack.upper()}_CLIENT_SECRET", client_secret),
            (f"refresh token for stack '{stack}'", refresh_token),
        )
        if not value
    ]
    if missing:
        print(f"ERROR: missing credentials for stack {stack!r}: {', '.join(missing)}")
        print(
            "  Set these in experiments/gmail/.env (see .env.example) or pass them "
            "explicitly. See experiments/gmail/IMPLEMENTATION.md §2 for the OAuth setup."
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


def service() -> Resource:
    """Return the active service, exiting if ``build_service`` hasn't run."""
    if SERVICE is None:
        print("ERROR: gmail service not initialised — call build_service(stack) first")
        sys.exit(1)
    return SERVICE


# ---------------------------------------------------------------------------
# Workspace state
# ---------------------------------------------------------------------------

# Populated in-place by ``load_state``. Importers can ``from utils import
# THREAD_ID_MAP`` and read the dict after load — the reference stays valid.
STATE: dict = {}
THREAD_ID_MAP: dict[str, str] = {}
MESSAGE_ID_MAP: dict[str, str] = {}
LABEL_ID_MAP: dict[str, str] = {}   # keyed by label name (e.g. "Hintas/Triage")
DRAFT_ID_MAP: dict[str, str] = {}
FILTER_ID_MAP: dict[str, str] = {}
GROUND_TRUTH: dict = {}
IGNORE_LABEL_NAME_RES: list[re.Pattern] = []
IGNORE_LABEL_IDS: set[str] = set()


def resolve_state_file(explicit_path: str | None, stack: str | None = None) -> str:
    """Pick the per-stack state file. Precedence: ``explicit_path`` > stack."""
    if explicit_path:
        return explicit_path
    if stack:
        return os.path.join(SCRIPT_DIR, f"workspace_state_ids_{stack}.json")
    print("ERROR: --stack or --state-file is required to resolve the workspace state file.")
    sys.exit(2)


def load_state(state_path: str, allow_missing: bool = False) -> bool:
    """Load a workspace state file into the module-level dicts (in place).

    Returns False if ``allow_missing=True`` and the file is absent.
    Returns True after a successful load. Exits the process on hard errors.
    """
    if not os.path.exists(state_path):
        if allow_missing:
            print(f"  No state file at {state_path} — workspace has not been seeded; reset is a no-op.")
            return False
        print(
            f"ERROR: {state_path} not found. "
            f"Run seed_workspace.py against this mailbox first."
        )
        sys.exit(2)

    with open(state_path) as f:
        loaded = json.load(f)

    STATE.clear()
    STATE.update(loaded)

    for target, key in (
        (THREAD_ID_MAP,  "thread_id_map"),
        (MESSAGE_ID_MAP, "message_id_map"),
        (LABEL_ID_MAP,   "label_id_map"),
        (DRAFT_ID_MAP,   "draft_id_map"),
        (FILTER_ID_MAP,  "filter_id_map"),
    ):
        target.clear()
        target.update(STATE.get(key, {}) or {})

    GROUND_TRUTH.clear()
    GROUND_TRUTH.update(STATE.get("ground_truth", {}) or {})

    ignore = GROUND_TRUTH.get("ignore", {}) or {}
    IGNORE_LABEL_NAME_RES.clear()
    IGNORE_LABEL_NAME_RES.extend(re.compile(p) for p in ignore.get("label_name_patterns", []))
    IGNORE_LABEL_IDS.clear()
    IGNORE_LABEL_IDS.update(ignore.get("label_ids", []))

    print(f"  Loaded state ← {state_path}")
    return True


def save_state(state_path: str, payload: dict) -> None:
    """Persist a state payload to disk and refresh the in-memory mirror."""
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(payload, f, indent=2)
    STATE.clear()
    STATE.update(payload)


# ---------------------------------------------------------------------------
# ID resolvers (logical → real)
# ---------------------------------------------------------------------------

def tid(logical: str) -> str:
    """Resolve a logical thread ID (``TH_BUG247``) to the real Gmail thread id."""
    return THREAD_ID_MAP.get(logical, logical)


def mid(logical: str) -> str:
    """Resolve a logical message ID to the real Gmail message id."""
    return MESSAGE_ID_MAP.get(logical, logical)


def lid(name: str) -> str:
    """Resolve a label name (``Hintas/Triage``) to its Gmail label id.

    System labels (``INBOX``, ``UNREAD``, ``STARRED``, ``SENT``, ``TRASH``,
    ``SPAM``, ``DRAFT``, ``IMPORTANT``) are returned as-is — Gmail's API
    accepts the well-known name directly.
    """
    if name in SYSTEM_LABEL_IDS:
        return name
    return LABEL_ID_MAP.get(name, name)


def did(logical: str) -> str:
    """Resolve a logical draft id (``DRAFT_OOO_REPLY``) to the real draft id."""
    return DRAFT_ID_MAP.get(logical, logical)


def fid(logical: str) -> str:
    """Resolve a logical filter id (``FILTER_RECEIPTS``) to the real filter id."""
    return FILTER_ID_MAP.get(logical, logical)


SYSTEM_LABEL_IDS: set[str] = {
    "INBOX", "SENT", "DRAFT", "TRASH", "SPAM",
    "STARRED", "IMPORTANT", "UNREAD",
    "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS",
    "CHAT",
}


# ---------------------------------------------------------------------------
# Users + substitution
# ---------------------------------------------------------------------------

USERS: dict[str, dict] = {}
SUBS: dict[str, str] = {}


def load_users() -> dict[str, dict]:
    """Load the user cast with whole-file precedence (local > sample).

    Mirrors the Slack pattern at ``experiments/slack/scripts/seed_workspace.py:144``.
    """
    local = os.path.join(SCRIPT_DIR, "users.local.json")
    sample = os.path.join(SCRIPT_DIR, "users.json")
    path = local if os.path.exists(local) else sample
    if not os.path.exists(path):
        print("ERROR: users.json not found in experiments/gmail/scripts/")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    print(f"  [config] Loaded user records from {os.path.basename(path)}")
    USERS.clear()
    USERS.update(data)
    return data


def build_substitution_map(users: dict[str, dict], owner_email: str | None = None) -> dict[str, str]:
    """Build ``{{ID_*}} / {{EMAIL_*}} / {{NAME_*}} / {{HANDLE_*}} / {{DISPLAY_*}}``.

    Per-user keys are emitted for every entry. ``{{EMAIL_U05CLAUDE}}`` is
    overridden with ``owner_email`` if provided so the substitution always
    reflects the mailbox the seeder is actually authenticated against.
    """
    subs: dict[str, str] = {}
    for logical_id, entry in users.items():
        subs[f"{{{{ID_{logical_id}}}}}"] = entry.get("id", logical_id)
        subs[f"{{{{EMAIL_{logical_id}}}}}"] = entry.get("email", "")
        subs[f"{{{{NAME_{logical_id}}}}}"] = entry.get("name", "")
        subs[f"{{{{HANDLE_{logical_id}}}}}"] = entry.get("handle", "")
        subs[f"{{{{DISPLAY_{logical_id}}}}}"] = entry.get("display_name", "")
    if owner_email:
        subs["{{EMAIL_U05CLAUDE}}"] = owner_email
    SUBS.clear()
    SUBS.update(subs)
    return subs


_warned_placeholders: set[str] = set()


def subst(text: str) -> str:
    """Apply the substitution map to ``text``. Untouched if no placeholders.

    Warns once per unique unresolved ``{{...}}`` token left behind so seed
    typos surface early instead of silently producing literal placeholder
    text in headers / bodies.
    """
    if not text or "{{" not in text:
        return text
    out = text
    for k, v in SUBS.items():
        if k in out:
            out = out.replace(k, v)
    # Surface any unresolved placeholders the substitution map didn't cover.
    if "{{" in out:
        import re as _re
        for token in _re.findall(r"\{\{[^}]+\}\}", out):
            if token not in _warned_placeholders:
                _warned_placeholders.add(token)
                print(f"  [WARN] unresolved placeholder in seed text: {token}")
    return out


def subst_obj(obj: Any) -> Any:
    """Recursively apply ``subst`` to every string leaf in a dict/list/scalar."""
    if isinstance(obj, str):
        return subst(obj)
    if isinstance(obj, dict):
        return {k: subst_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [subst_obj(x) for x in obj]
    return obj


# ---------------------------------------------------------------------------
# Prerequisites (operator-managed)
# ---------------------------------------------------------------------------

PREREQUISITE_KEYS = (
    "email_address",
)


def load_prerequisites(stack: str) -> dict:
    """Read ``prerequisites_<stack>.local.json`` (operator-managed).

    Exits with operator instructions if the file is missing or malformed.
    Required keys: ``email_address``.
    Optional keys: ``history_id`` (informational),
    ``forwarding_address`` and ``forwarding_address_verification_status``
    (extension run only).
    """
    path = os.path.join(SCRIPT_DIR, f"prerequisites_{stack}.local.json")
    if not os.path.exists(path):
        print(f"ERROR: {path} is missing.")
        print(
            "  This file is operator-managed (gitignored). Create it with the\n"
            "  resolved mailbox identifiers before running the seeder:\n"
            "    {\n"
            f'      "email_address": "<the {stack} mailbox address>",\n'
            '      "history_id": "<users.getProfile.historyId, optional>"\n'
            "    }\n"
            "  See experiments/gmail/IMPLEMENTATION.md §4 for context."
        )
        sys.exit(2)
    with open(path) as f:
        data = json.load(f)
    missing = [k for k in PREREQUISITE_KEYS if not data.get(k)]
    if missing:
        print(f"ERROR: {path} is missing required keys: {missing}")
        sys.exit(2)
    return data
