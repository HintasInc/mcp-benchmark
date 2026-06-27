"""
Shared helpers for the multi-API benchmark seed/reset scripts.

The multi-API stack drives three surfaces — Slack, Gmail, Notion — from one
prompt suite. Each surface keeps its own ``seed_<api>.py`` / ``reset_<api>.py``
pair (so a surface can be re-seeded in isolation), but they share the generic
plumbing here: console output, dry-run flag, the persona cast, {{TOKEN}}
substitution, and JSON state I/O.

Unlike the single-API experiments these scripts are standalone: each reads its
own surface token straight from the environment (``SLACK_TOKEN``,
``GMAIL_TOKEN`` + client creds, ``NOTION_TOKEN``) rather than resolving a stack
from a platform manifest. The per-surface state file is written next to the
script as ``workspace_state_<api>.json`` and is the answer key both the matching
reset script and the graders read back.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Re-exported so seed/reset scripts import the benchmark clock from one place.
from benchmarking.clock import BENCHMARK_NOW, BENCHMARK_NOW_EPOCH  # noqa: E402,F401

# ---------------------------------------------------------------------------
# Environment files
# ---------------------------------------------------------------------------
# Load experiments/multi_api/.env (then the repo-root .env) on import so the
# seed/reset scripts pick up BASELINE_*/HINTAS_* tokens without the caller
# having to `source` anything first. Mirrors benchmarking.config.load_platform_env:
# already-set process env vars win (override=False), and the platform .env
# takes precedence over the repo .env.

def _load_env_files() -> None:
    from dotenv import load_dotenv
    from benchmarking.paths import REPO_ROOT

    platform_env = os.path.join(os.path.dirname(SCRIPT_DIR), ".env")  # experiments/multi_api/.env
    for path in (platform_env, os.path.join(str(REPO_ROOT), ".env")):
        if os.path.exists(path):
            load_dotenv(path, override=False)


_load_env_files()

# ---------------------------------------------------------------------------
# Stacks
# ---------------------------------------------------------------------------
# The suite compares two stacks against separate, independently-seeded
# workspaces (one Slack workspace + Gmail mailbox + Notion workspace each):
#   * baseline — the official single-API MCP servers stitched together.
#   * hintas   — one Hintas MCP server serving all three APIs.
# Each surface's credentials are resolved from a stack-prefixed env var so the
# two stacks never cross-contaminate: BASELINE_<VAR> for baseline, HINTAS_<VAR>
# for hintas (e.g. BASELINE_SLACK_TOKEN vs HINTAS_SLACK_TOKEN).
STACKS = ("baseline", "hintas")
STACK_ENV_PREFIX = {"baseline": "BASELINE_", "hintas": "HINTAS_"}


def add_stack_arg(parser) -> None:
    """Register the shared ``--stack`` flag (defaults to baseline)."""
    parser.add_argument(
        "--stack", choices=STACKS, default="baseline",
        help="Which workspace set to target (default: baseline). Selects the "
             "BASELINE_*/HINTAS_* env vars and the per-stack state file.",
    )


def stack_env(stack: str, base: str, default: str = "") -> str:
    """Read a stack-scoped env var, e.g. ``stack_env('hintas', 'SLACK_TOKEN')``
    → ``os.environ['HINTAS_SLACK_TOKEN']``."""
    return os.environ.get(f"{STACK_ENV_PREFIX[stack]}{base}", default)

# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

DRY_RUN: bool = False


def set_dry_run(value: bool) -> None:
    global DRY_RUN
    DRY_RUN = value


def log(msg: str) -> None:
    print(f"  {'[DRY]' if DRY_RUN else '[OK ]'} {msg}")


def warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def err(msg: str) -> None:
    print(f"  [ERR ] {msg}", file=sys.stderr)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def subsection(title: str) -> None:
    print(f"\n  ── {title}")


# ---------------------------------------------------------------------------
# Persona cast (shared across all three surfaces)
# ---------------------------------------------------------------------------

USERS: dict[str, dict] = {}
SUBS: dict[str, str] = {}


def load_users() -> dict[str, dict]:
    """Load the persona cast with whole-file precedence (local > committed).

    The same ``users.json`` resolves a person across Slack, Gmail and Notion by
    email — cross-surface identity reconciliation is part of what the suite
    measures, so every script reads from this one cast.
    """
    local = os.path.join(SCRIPT_DIR, "users.local.json")
    sample = os.path.join(SCRIPT_DIR, "users.json")
    path = local if os.path.exists(local) else sample
    if not os.path.exists(path):
        err("users.json not found in experiments/multi_api/scripts/")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    print(f"  [config] Loaded persona cast from {os.path.basename(path)}")
    USERS.clear()
    USERS.update(data)
    return data


def users_in_teams(*teams: str) -> list[str]:
    """Logical ids whose ``team`` is one of ``teams`` (e.g. ``users_in_teams('leads')``)."""
    return [lid for lid, e in USERS.items() if e.get("team") in teams]


def leads() -> list[str]:
    """Logical ids of the 'leads' group."""
    return users_in_teams("leads")


def team_distribution() -> list[str]:
    """All active humans the 'team' email distribution targets.

    Every persona with team in {leads, members} — i.e. all active humans except
    the acting agent and the not-yet-provisioned candidate.
    """
    return users_in_teams("leads", "members")


def agent_logical_id() -> str:
    """The acting agent — the single ``benchmark-author=true`` entry."""
    for lid, e in USERS.items():
        if e.get("benchmark-author"):
            return lid
    return "U05CLAUDE"


def build_substitution_map(owner_email: str | None = None) -> dict[str, str]:
    """Build ``{{ID_*}} / {{EMAIL_*}} / {{NAME_*}} / {{HANDLE_*}} / {{DISPLAY_*}}``.

    ``{{EMAIL_<agent>}}`` is overridden with ``owner_email`` when provided so
    substitution reflects the mailbox/identity actually authenticated against.
    """
    subs: dict[str, str] = {}
    for logical_id, entry in USERS.items():
        subs[f"{{{{ID_{logical_id}}}}}"] = entry.get("id", logical_id)
        subs[f"{{{{EMAIL_{logical_id}}}}}"] = entry.get("email", "")
        subs[f"{{{{NAME_{logical_id}}}}}"] = entry.get("name", "")
        subs[f"{{{{HANDLE_{logical_id}}}}}"] = entry.get("handle", "")
        subs[f"{{{{DISPLAY_{logical_id}}}}}"] = entry.get("display_name", "")
    if owner_email:
        subs[f"{{{{EMAIL_{agent_logical_id()}}}}}"] = owner_email
    SUBS.clear()
    SUBS.update(subs)
    return subs


_warned_placeholders: set[str] = set()


def subst(text: str) -> str:
    """Apply the substitution map, warning once per unresolved ``{{token}}``."""
    if not text or "{{" not in text:
        return text
    out = text
    for k, v in SUBS.items():
        if k in out:
            out = out.replace(k, v)
    if "{{" in out:
        for token in re.findall(r"\{\{[^}]+\}\}", out):
            if token not in _warned_placeholders:
                _warned_placeholders.add(token)
                warn(f"unresolved placeholder in seed text: {token}")
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


def email_of(logical_id: str) -> str:
    return USERS.get(logical_id, {}).get("email", "")


def name_of(logical_id: str) -> str:
    return USERS.get(logical_id, {}).get("name", "")


# ---------------------------------------------------------------------------
# State file I/O (generic — each surface owns its own key set)
# ---------------------------------------------------------------------------

def default_state_path(api: str, stack: str) -> str:
    """``experiments/multi_api/scripts/workspace_state_<api>_<stack>.json``."""
    return os.path.join(SCRIPT_DIR, f"workspace_state_{api}_{stack}.json")


def resolve_state_file(explicit_path: str | None, api: str, stack: str) -> str:
    """Pick the state file: ``--state-file`` override, else the per-(api,stack) default."""
    return explicit_path or default_state_path(api, stack)


def save_state(state_path: str, payload: dict) -> None:
    """Persist a state payload as pretty JSON."""
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Saved → {state_path}")


def load_state(state_path: str, allow_missing: bool = False) -> dict | None:
    """Load a state file. Returns the dict, or ``None`` when missing+allowed.

    Exits the process on a hard miss so each reset script avoids the boilerplate.
    """
    if not os.path.exists(state_path):
        if allow_missing:
            print(f"  No state file at {state_path} — surface not seeded; reset is a no-op.")
            return None
        err(f"{state_path} not found. Run the matching seed_<api>.py first.")
        sys.exit(2)
    with open(state_path) as f:
        data = json.load(f)
    print(f"  Loaded state ← {state_path}")
    return data


# ---------------------------------------------------------------------------
# Token guard
# ---------------------------------------------------------------------------

def require_env(var: str, hint: str) -> str:
    """Return ``os.environ[var]`` or exit with a friendly message."""
    val = os.environ.get(var, "")
    if not val:
        err(f"Set {var} env var or pass --token. {hint}")
        sys.exit(1)
    return val
