"""
Shared prompt loader with user-attribute substitution.

Each platform's prompts JSON may contain user-attribute placeholders that
are resolved against the platform's user map at
`<platform>/scripts/users.local.json` (gitignored override) or
`<platform>/scripts/users.json`.

Two file formats are supported:

  Legacy (notion):  flat `{logical_id: email}` map. Name/handle/display_name
                    are derived from the email local part (plus-addressing
                    aware), and no benchmark author is identified.

  Structured (slack): `{logical_id: {id, email, name, handle, display_name,
                       "benchmark-author"}}`. Fields are taken verbatim and
                       the entry flagged `"benchmark-author": true` is also
                       exposed via the AUTHOR_* placeholders.

Per-user placeholders (logical_id is the top-level key, e.g. `U02JARED`):

    {{ID_<logical_id>}}            — the entry's `id` (logical ID at rest;
                                     real Slack ID after lookup at runtime)
    {{EMAIL_<logical_id>}}         — the entry's email
    {{NAME_<logical_id>}}          — the display name (what Slack/Notion UI
                                     renders for the user)
    {{DISPLAY_NAME_<logical_id>}}  — alias of NAME, matches the JSON field
    {{FULL_NAME_<logical_id>}}     — full real name (e.g. "Jared Blackwood")
    {{HANDLE_<logical_id>}}        — username/handle (e.g. "jared")
    {{MENTION_<logical_id>}}       — Slack mention token "<@<id>>"

Benchmark-author placeholders (resolved from the entry where
`"benchmark-author": true`):

    {{AUTHOR_ID}}, {{AUTHOR_EMAIL}}, {{AUTHOR_NAME}}, {{AUTHOR_FULL_NAME}},
    {{AUTHOR_HANDLE}}, {{AUTHOR_DISPLAY_NAME}}, {{AUTHOR_MENTION}}

Per-prompt schema (every platform's prompts JSON must conform):

    Required fields:
      id                       int   — stable numeric identifier
      title                    str   — short label shown in run reports
      prompt                   str   — instruction handed to the agent
      difficulty               str   — one of L1..L5
      category                 str   — retrieval / write / search / ...
      feasible_on_free_plan    str   — "core" | "extension" | "infeasible"
      success_criteria         list[str] — grading bullets
      required_scopes          list[str] — auth scopes the agent needs

    Optional fields:
      infeasible_reason        str   — why a prompt is infeasible on free
      notes                    str   — graders' annotations / variant notes
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _name_from_email(email: str) -> str:
    """Derive a display name from an email local-part, handling plus-addressing."""
    local = email.split("@", 1)[0]
    if "+" in local:
        local = local.rsplit("+", 1)[1]
    return local


def _expand_legacy_entry(logical_id: str, email: str) -> dict[str, Any]:
    handle = _name_from_email(email)
    name = handle.title()
    return {
        "id": logical_id,
        "email": email,
        "name": name,
        "handle": handle,
        "display_name": name,
        "benchmark-author": False,
    }


def load_user_map(prompts_file: Path) -> dict[str, dict[str, Any]]:
    """
    Load the platform's user map and return a `{logical_id: entry}` dict
    where each entry has the structured schema described in the module
    docstring. Legacy `{logical_id: email}` files are auto-expanded.
    """
    scripts_dir = Path(prompts_file).resolve().parent.parent / "scripts"
    local = scripts_dir / "users.local.json"
    sample = scripts_dir / "users.json"
    if local.exists():
        path = local
    elif sample.exists():
        path = sample
    else:
        return {}
    with open(path) as f:
        raw = json.load(f)
    if raw and all(isinstance(v, str) for v in raw.values()):
        return {logical_id: _expand_legacy_entry(logical_id, email) for logical_id, email in raw.items()}
    return raw


def load_email_map(prompts_file: Path) -> dict[str, str]:
    """Return a flat `{logical_id: email}` map for callers that only need emails."""
    return {logical_id: entry.get("email", "") for logical_id, entry in load_user_map(prompts_file).items()}


def build_substitutions(users: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Expand the structured user map into the full placeholder table."""
    subs: dict[str, str] = {}
    author: dict[str, Any] | None = None
    for logical_id, entry in users.items():
        uid = entry.get("id") or logical_id
        email = entry.get("email", "")
        full_name = entry.get("name", "")
        handle = entry.get("handle", "")
        display_name = entry.get("display_name", "") or full_name
        subs[f"{{{{ID_{logical_id}}}}}"] = uid
        subs[f"{{{{EMAIL_{logical_id}}}}}"] = email
        subs[f"{{{{NAME_{logical_id}}}}}"] = display_name
        subs[f"{{{{DISPLAY_NAME_{logical_id}}}}}"] = display_name
        subs[f"{{{{FULL_NAME_{logical_id}}}}}"] = full_name
        subs[f"{{{{HANDLE_{logical_id}}}}}"] = handle
        subs[f"{{{{MENTION_{logical_id}}}}}"] = f"<@{uid}>"
        if entry.get("benchmark-author"):
            author = entry
    if author:
        author_id = author.get("id", "")
        author_display = author.get("display_name", "") or author.get("name", "")
        subs["{{AUTHOR_ID}}"] = author_id
        subs["{{AUTHOR_EMAIL}}"] = author.get("email", "")
        subs["{{AUTHOR_NAME}}"] = author_display
        subs["{{AUTHOR_DISPLAY_NAME}}"] = author.get("display_name", "")
        subs["{{AUTHOR_FULL_NAME}}"] = author.get("name", "")
        subs["{{AUTHOR_HANDLE}}"] = author.get("handle", "")
        subs["{{AUTHOR_MENTION}}"] = f"<@{author_id}>"
    return subs


def substitute(value: Any, subs: dict[str, str]) -> Any:
    if not subs:
        return value
    if isinstance(value, str):
        for placeholder, replacement in subs.items():
            value = value.replace(placeholder, replacement)
        return value
    if isinstance(value, list):
        return [substitute(v, subs) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, subs) for k, v in value.items()}
    return value


def load_prompts(prompts_file: str | Path) -> list[dict]:
    path = Path(prompts_file)
    with open(path) as f:
        data = json.load(f)
    subs = build_substitutions(load_user_map(path))
    global_assumptions = substitute(data.get("global_assumptions", []), subs)
    context_preamble = _render_context_preamble(global_assumptions)
    prompts = []
    for p in data["prompts"]:
        sub_p = substitute(p, subs)
        sub_p["_context_preamble"] = context_preamble
        prompts.append(sub_p)
    return prompts


def _render_context_preamble(global_assumptions: list[str] | dict | None) -> str:
    if not global_assumptions:
        return ""
    if isinstance(global_assumptions, dict):
        lines = [str(v) for v in global_assumptions.values()]
    else:
        lines = [str(x) for x in global_assumptions]
    body = "\n".join(f"- {line}" for line in lines if line)
    return f"Context (global assumptions for this benchmark run):\n{body}\n\nTask:\n"
