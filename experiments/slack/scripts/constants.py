"""
Slack benchmark workspace constants — shared by reset / seed / verify.

These describe the seeded baseline (Scenario A: U01MIRANDA merged into the
agent U05CLAUDE). Reset restores to this snapshot, seed creates it, verify
asserts the live workspace still matches it.
"""
from __future__ import annotations

from benchmarking.clock import BENCHMARK_NOW_EPOCH

# ---------------------------------------------------------------------------
# Channel topology
# ---------------------------------------------------------------------------

CHANNEL_SEED_NAMES: dict[str, str] = {
    "C001GENERAL":     "general",
    "C002RANDOM":      "random",
    "C003ENGBACK":     "eng-backend",
    "C004ENGFRONT":    "eng-frontend",
    "C005DESIGNRV":    "design-reviews",
    "C006QA":          "qa-bugs",
    "C007MKT":         "marketing",
    "C009INCIDENTS":   "incidents",
    "C010ANNOUNCE":    "announcements",
    "C008LAUNCH":      "launch-2026",
    "C012LEADS":       "leads-only",
    "C011OLDPLAYTEST": "old-playtest-2025",
}

CHANNEL_SEED_TOPICS: dict[str, str] = {
    "C001GENERAL":     "Welcome! Keep it friendly.",
    "C002RANDOM":      "Lower the stakes.",
    "C003ENGBACK":     "Servers, tools, build pipeline.",
    "C004ENGFRONT":    "UI, rendering, input.",
    "C005DESIGNRV":    "Post work, give crits, be kind.",
    "C006QA":          "File with BUG-### prefix.",
    "C007MKT":         "Voice of the game.",
    "C009INCIDENTS":   "Paging the team only.",
    "C010ANNOUNCE":    "Shipping notices and studio news.",
    "C008LAUNCH":      "",
    "C012LEADS":       "",
    "C011OLDPLAYTEST": "",
}

CHANNEL_SEED_PRIVATE: dict[str, bool] = {
    "C008LAUNCH": True,
    "C012LEADS":  True,
}

CHANNEL_SEED_ARCHIVED: set[str] = {"C011OLDPLAYTEST"}

# Membership the **reset** script restores. Reset cannot re-add the bot
# account (U10BOT_CI) — it lacks an email and can only join via OAuth — so
# the bot is omitted here. Seed includes the bot in its own member sets.
CHANNEL_MEMBERS: dict[str, list[str]] = {
    "C001GENERAL":   ["U02JARED", "U03PINKMAN", "U04LAGOON", "U05CLAUDE", "U06DEVON", "U07RHEA", "U08TOMAS"],
    "C002RANDOM":    ["U02JARED", "U03PINKMAN", "U04LAGOON", "U05CLAUDE", "U06DEVON", "U07RHEA", "U08TOMAS"],
    "C003ENGBACK":   ["U02JARED", "U06DEVON", "U05CLAUDE"],
    "C004ENGFRONT":  ["U02JARED", "U07RHEA", "U05CLAUDE", "U06DEVON"],
    "C005DESIGNRV":  ["U05CLAUDE", "U07RHEA", "U06DEVON"],
    "C006QA":        ["U03PINKMAN", "U08TOMAS", "U02JARED", "U05CLAUDE"],
    "C007MKT":       ["U04LAGOON", "U05CLAUDE"],
    "C009INCIDENTS": ["U02JARED", "U06DEVON", "U07RHEA", "U03PINKMAN", "U05CLAUDE"],
    "C010ANNOUNCE":  ["U02JARED", "U03PINKMAN", "U04LAGOON", "U05CLAUDE", "U06DEVON", "U07RHEA", "U08TOMAS"],
    "C008LAUNCH":    ["U02JARED", "U04LAGOON", "U05CLAUDE"],
    "C012LEADS":     ["U02JARED", "U03PINKMAN", "U04LAGOON", "U05CLAUDE"],
}

# ---------------------------------------------------------------------------
# Reactions — agent-authored only (Scenario A)
# ---------------------------------------------------------------------------

# (msg_label, emoji, channel_logical_id) — author is always U05CLAUDE.
SEED_REACTIONS: list[tuple[str, str, str]] = [
    ("M1",  "eyes",            "C010ANNOUNCE"),
    ("M1",  "+1",              "C010ANNOUNCE"),
    ("M5",  "fire",             "C005DESIGNRV"),
    ("M5",  "art",              "C005DESIGNRV"),
    ("M11", "raider_skull",     "C002RANDOM"),
    ("M17", "ship_it_raider",   "C002RANDOM"),
]

# ---------------------------------------------------------------------------
# Standup scheduled message
# ---------------------------------------------------------------------------

STANDUP_CHANNEL: str = "C007MKT"
STANDUP_TEXT: str = "Weekly marketing standup — drop blockers below."
STANDUP_POST_AT_EPOCH: int = int(BENCHMARK_NOW_EPOCH + 23 * 3600)

# ---------------------------------------------------------------------------
# Sweep ignore list
# ---------------------------------------------------------------------------

# Channel names matching these regexes are structurally unavoidable per
# workspace and are skipped by the reset/verify sweep. Slack's auto-created
# `all-<workspace-name>` channel is the canonical example: it cannot be
# archived and its name varies per workspace.
IGNORE_NAME_PATTERNS: list[str] = [
    r"^all-",
]
