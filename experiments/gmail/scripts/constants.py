"""
Gmail benchmark seed declarations.

All entities the seeder creates live here as plain-data structures. The seeder
walks these in order; the resetter / verifier diff the live mailbox against
them. Per-user placeholder strings (``{{EMAIL_*}}``, ``{{NAME_*}}``, ...) are
expanded at seed time from the resolved ``users.json`` / ``users.local.json``
view.

Timing
------
Every message's ``offset_hours`` is interpreted as a delta from
``benchmark_now = 2026-04-19T10:00:00-07:00`` (see ``src/benchmarking/clock.py``).
Negative offsets are in the past; positive offsets in the future. The seeder
formats the Date header as RFC 2822 and ``messages.import_`` is called with
``internalDateSource='dateHeader'`` so Gmail's ``internalDate`` matches.

Threading
---------
The first message in a thread is imported without ``In-Reply-To``; the seeder
captures the returned ``threadId`` and reuses it for subsequent messages so
Gmail groups them. Each follow-up's ``In-Reply-To`` / ``References`` headers
are chained to the previous message's ``Message-ID``.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

# User-defined labels seeded into the mailbox (IMPLEMENTATION.md §"Mailbox overview").
# Order matters: parent labels must exist before nested children (Gmail represents
# nesting via the "/" separator but creates parents implicitly — still, list them
# explicitly so the ground-truth diff is exact).
SEEDED_LABELS: list[str] = [
    "Hintas",
    "Hintas/Triage",
    "Hintas/Follow-up",
    "Receipts",
    "Press",
    "Ops/Bugs",
]


# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------
#
# Each entry produces one Gmail thread. Messages within the entry share the
# thread; ``labels`` applies to every message in the thread (Gmail's labels are
# message-scoped but threads.get returns the union, which is what prompts grade
# against).
#
# Fields per message:
#   logical_id      string key into MESSAGE_ID_MAP
#   from / to / cc  RFC 5322 address strings (placeholders allowed)
#   subject         string (first message's subject becomes the thread subject)
#   offset_hours    float, signed, relative to BENCHMARK_NOW
#   body            plain-text body
#   attachments     optional list of {"filename": str, "content": str, "mime": str}
# ---------------------------------------------------------------------------

SEEDED_THREADS: list[dict] = [
    # ----- TH_BUG247 — referenced by prompts 7, 12, 14, 21, 22, 32, 33, 43, 51
    {
        "logical_id": "TH_BUG247",
        "labels": ["INBOX", "UNREAD", "STARRED", "Ops/Bugs"],
        "messages": [
            {
                "logical_id": "MSG_BUG247_1",
                "from": "{{NAME_U06DEVON}} <{{EMAIL_U06DEVON}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "BUG-247: save-file corruption on macOS",
                "offset_hours": -96,
                "body": (
                    "Repro: load level 4, save, quit, reopen. About 4/10 runs the save "
                    "is corrupted and the game crashes on load.\n\n"
                    "Happens on macOS 14 only — Windows and Linux are fine. Filing as "
                    "BUG-247.\n\nDevon"
                ),
            },
            {
                "logical_id": "MSG_BUG247_2",
                "from": "{{NAME_U08TOMAS}} <{{EMAIL_U08TOMAS}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": "{{EMAIL_U06DEVON}}",
                "subject": "Re: BUG-247: save-file corruption on macOS",
                "offset_hours": -90,
                "body": (
                    "I can repro. It's the async streamer dropping the last chunk when "
                    "GPU memory is tight — the save header writes before the body "
                    "finishes flushing.\n\nTomás"
                ),
            },
            {
                "logical_id": "MSG_BUG247_3",
                "from": "{{NAME_U08TOMAS}} <{{EMAIL_U08TOMAS}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": "{{EMAIL_U06DEVON}}",
                "subject": "Re: BUG-247: save-file corruption on macOS",
                "offset_hours": -84,
                "body": (
                    "Attaching the repro log from a corrupted run. Look at the last 20 "
                    "lines — the chunk-flush ack never arrives before the header write.\n\nTomás"
                ),
                "attachments": [
                    {
                        "filename": "repro.log",
                        "mime": "text/plain",
                        "content": (
                            "[2026-04-15 09:12:03] streamer: chunk 0x4f loaded\n"
                            "[2026-04-15 09:12:03] streamer: chunk 0x50 loaded\n"
                            "[2026-04-15 09:12:04] streamer: chunk 0x51 requested\n"
                            "[2026-04-15 09:12:04] save: header write begin\n"
                            "[2026-04-15 09:12:04] gpu: mem pressure, evicting 0x4e\n"
                            "[2026-04-15 09:12:05] streamer: chunk 0x51 stalled, retry 1\n"
                            "[2026-04-15 09:12:05] save: header write commit\n"
                            "[2026-04-15 09:12:06] save: body write begin (chunk 0x51 missing)\n"
                            "[2026-04-15 09:12:06] save: body write commit (truncated)\n"
                            "[2026-04-15 09:12:06] streamer: chunk 0x51 timeout\n"
                            "[2026-04-15 09:12:07] save: integrity check FAIL\n"
                        ),
                    }
                ],
            },
        ],
    },

    # ----- TH_OKR_DIGEST — referenced by prompt 17 ("Q1 OKR digest")
    # Note: CATEGORY_UPDATES is classifier-managed; we use messages.insert
    # (which bypasses classification) so CATEGORY_* would not be assignable
    # via labelIds anyway. Prompts that depend on CATEGORY_UPDATES classify
    # results will see whatever Gmail's UI-driven recategorization picks.
    {
        "logical_id": "TH_OKR_DIGEST",
        "labels": ["INBOX", "UNREAD"],
        "messages": [
            {
                "logical_id": "MSG_OKR_DIGEST_1",
                "from": "Hintas Ops <ops@hintas.co>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Q1 OKR digest — week of Apr 13",
                "offset_hours": -120,
                "body": (
                    "Weekly OKR digest:\n"
                    "- Launch readiness: 62%\n"
                    "- Brand kit: complete\n"
                    "- Backend perf: green\n"
                    "- Marketing: 60% ready, 2 blockers"
                ),
            },
        ],
    },

    # ----- TH_OLD_PROMO — referenced by prompts 18 (untrash) and 44 (modify trashed)
    {
        "logical_id": "TH_OLD_PROMO",
        "labels": ["TRASH"],
        "messages": [
            {
                "logical_id": "MSG_OLD_PROMO_1",
                "from": "Acme Promotions <promos@acme.example>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Spring sale — 30% off through April 18",
                "offset_hours": -240,
                "body": "Limited time spring sale. Discount applies at checkout.",
            },
        ],
    },

    # ----- TH_LAGOON_LATEST — referenced by prompt 15 (latest from Lagoon)
    {
        "logical_id": "TH_LAGOON_LATEST",
        "labels": ["INBOX", "UNREAD"],
        "messages": [
            {
                "logical_id": "MSG_LAGOON_1",
                "from": "{{NAME_U04LAGOON}} <{{EMAIL_U04LAGOON}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Trailer cut feedback",
                "offset_hours": -30,
                "body": (
                    "Reviewed the v3 trailer cut. The pacing on the second tomb shot "
                    "drags — let's tighten by 1.5s. Otherwise it's locked.\n\nLagoon"
                ),
            },
        ],
    },

    # ----- Threads from Miranda — referenced by prompt 16 (star 14d), prompts 4/5 etc.
    {
        "logical_id": "TH_MIRANDA_BRAND",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_MIRANDA_BRAND_1",
                "from": "{{NAME_U01MIRANDA}} <{{EMAIL_U01MIRANDA}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Brand kit final — legal approved",
                "offset_hours": -120,
                "body": "Brand kit final draft attached, legal signed off. Locking it.",
            },
        ],
    },
    {
        "logical_id": "TH_MIRANDA_PRESS",
        "labels": ["INBOX", "UNREAD", "Press"],
        "messages": [
            {
                "logical_id": "MSG_MIRANDA_PRESS_1",
                "from": "{{NAME_U01MIRANDA}} <{{EMAIL_U01MIRANDA}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": "{{EMAIL_U04LAGOON}}",
                "subject": "Press preview deck — draft",
                "offset_hours": -60,
                "body": (
                    "Draft of the May 3 press preview deck. Need a final review by "
                    "Tuesday EOD."
                ),
            },
        ],
    },

    # ----- TH_JARED_THREAD — referenced by prompt 5 (find Jared's threads)
    {
        "logical_id": "TH_JARED_FREEZE",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_JARED_FREEZE_1",
                "from": "{{NAME_U02JARED}} <{{EMAIL_U02JARED}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": "{{EMAIL_U06DEVON}}",
                "subject": "Code freeze rules — week of 04/25",
                "offset_hours": -48,
                "body": "Reminder: no merges after Friday 5pm PT. Hotfixes only.",
            },
        ],
    },

    # ----- TH_PINKMAN — referenced by handle "pinkman"
    {
        "logical_id": "TH_PINKMAN_LEGAL",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_PINKMAN_LEGAL_1",
                "from": "{{NAME_U03PINKMAN}} <{{EMAIL_U03PINKMAN}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Legal: contractor MSA renewal",
                "offset_hours": -72,
                "body": "Renewal for the Q2 contractor MSA is ready for signature.",
            },
        ],
    },

    # ----- Devon (in addition to TH_BUG247)
    {
        "logical_id": "TH_DEVON_BUG246",
        "labels": ["INBOX", "Ops/Bugs"],
        "messages": [
            {
                "logical_id": "MSG_DEVON_BUG246_1",
                "from": "{{NAME_U06DEVON}} <{{EMAIL_U06DEVON}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "BUG-246: main-menu flicker on launch",
                "offset_hours": -200,
                "body": "Low-sev — main menu flickers on first launch only. Cosmetic.",
            },
        ],
    },

    # ----- Rhea — eng manager, sender
    {
        "logical_id": "TH_RHEA_ROADMAP",
        "labels": ["INBOX", "UNREAD", "Hintas/Triage"],
        "messages": [
            {
                "logical_id": "MSG_RHEA_ROADMAP_1",
                "from": "{{NAME_U07RHEA}} <{{EMAIL_U07RHEA}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Q2 roadmap — sync needed",
                "offset_hours": -6,
                "body": "Quick sync this week? Want to align on Q2 themes.",
            },
        ],
    },

    # ----- Tomas — eng, sometimes CC's claude
    {
        "logical_id": "TH_TOMAS_PERF",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_TOMAS_PERF_1",
                "from": "{{NAME_U08TOMAS}} <{{EMAIL_U08TOMAS}}>",
                "to": "{{EMAIL_U07RHEA}}",
                "cc": "{{EMAIL_U05CLAUDE}}",
                "subject": "Perf numbers from last build",
                "offset_hours": -36,
                "body": "Frame-pacing improvements landed. P99 frame-time down 14%.",
            },
        ],
    },

    # ----- Ember — deactivated external sender, archive-only
    {
        "logical_id": "TH_EMBER_ARCHIVE",
        "labels": ["Hintas"],  # not in inbox, no UNREAD
        "messages": [
            {
                "logical_id": "MSG_EMBER_1",
                "from": "{{NAME_U09EMBER}} <{{EMAIL_U09EMBER}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "[archived] Old playtest feedback",
                "offset_hours": -2400,
                "body": "Saved feedback from the 2025 playtest. Archived for reference.",
            },
        ],
    },

    # ----- Receipts — captured by FILTER_RECEIPTS
    {
        "logical_id": "TH_RECEIPT_AWS",
        "labels": ["Receipts"],
        "messages": [
            {
                "logical_id": "MSG_RECEIPT_AWS_1",
                "from": "AWS Billing <receipts@aws.example>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Your AWS invoice for March 2026",
                "offset_hours": -360,
                "body": "Total due: $214.37. Auto-charged to card on file.",
            },
        ],
    },

    # ----- Promotion older than 14d — referenced by prompt 27 (bulk-archive promotions)
    # CATEGORY_PROMOTIONS is classifier-managed; see the note on TH_OKR_DIGEST.
    {
        "logical_id": "TH_PROMO_OLD",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_PROMO_OLD_1",
                "from": "Megastore <deals@megastore.example>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Last chance — 40% off everything",
                "offset_hours": -480,  # 20 days ago
                "body": "Mega sale ends tonight. Don't miss out.",
            },
        ],
    },

    # ----- Recent promo (within 14d, should NOT be archived by prompt 27)
    {
        "logical_id": "TH_PROMO_RECENT",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_PROMO_RECENT_1",
                "from": "Newsletter <hello@newsletter.example>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "April highlights",
                "offset_hours": -120,
                "body": "This month's newsletter — top picks for game design.",
            },
        ],
    },

    # ----- Today (2026-04-19) unread inbox — referenced by prompt 26
    {
        "logical_id": "TH_TODAY_DEVON",
        "labels": ["INBOX", "UNREAD"],
        "messages": [
            {
                "logical_id": "MSG_TODAY_DEVON_1",
                "from": "{{NAME_U06DEVON}} <{{EMAIL_U06DEVON}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Build green this morning",
                "offset_hours": -2,
                "body": "CI is green on main. Promoting build #4218 to staging.",
            },
        ],
    },
    {
        "logical_id": "TH_TODAY_RHEA",
        "labels": ["INBOX", "UNREAD"],
        "messages": [
            {
                "logical_id": "MSG_TODAY_RHEA_1",
                "from": "{{NAME_U07RHEA}} <{{EMAIL_U07RHEA}}>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "Sprint demo — Wednesday 2pm",
                "offset_hours": -1,
                "body": "Calendar invite incoming for Wed 2pm. Confirm if that works.",
            },
        ],
    },

    # ----- CC-only thread (claude in Cc, not To) — referenced by prompt 31
    {
        "logical_id": "TH_CC_ONLY",
        "labels": ["INBOX"],
        "messages": [
            {
                "logical_id": "MSG_CC_ONLY_1",
                "from": "{{NAME_U04LAGOON}} <{{EMAIL_U04LAGOON}}>",
                "to": "{{EMAIL_U01MIRANDA}}",
                "cc": "{{EMAIL_U05CLAUDE}}",
                "subject": "FYI: trailer asset locked",
                "offset_hours": -18,
                "body": "Trailer asset is final, sending to PR. Looping you in.",
            },
        ],
    },

    # ----- Spam — referenced by prompt 28 (empty spam)
    {
        "logical_id": "TH_SPAM_1",
        "labels": ["SPAM"],
        "messages": [
            {
                "logical_id": "MSG_SPAM_1",
                "from": "Lucky Winner <noreply@spam.example>",
                "to": "{{EMAIL_U05CLAUDE}}",
                "cc": None,
                "subject": "You won! Claim your prize",
                "offset_hours": -50,
                "body": "Click here to claim. Limited time.",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Outbound messages already in SENT (authored by the agent)
# ---------------------------------------------------------------------------

SEEDED_OUTBOUND: list[dict] = [
    {
        "logical_id": "MSG_SENT_BUG_TRIAGE",
        "from": "{{NAME_U05CLAUDE}} <{{EMAIL_U05CLAUDE}}>",
        "to": "{{EMAIL_U07RHEA}}",
        "cc": "{{EMAIL_U06DEVON}}",
        "subject": "Bug triage notes — week of 04/12",
        "offset_hours": -150,
        "body": "Triage notes attached. BUG-247 is the blocker.",
        "labels": ["SENT"],
    },
    {
        "logical_id": "MSG_SENT_FREEZE_REPLY",
        "from": "{{NAME_U05CLAUDE}} <{{EMAIL_U05CLAUDE}}>",
        "to": "{{EMAIL_U02JARED}}",
        "cc": None,
        "subject": "Re: Code freeze rules — week of 04/25",
        "offset_hours": -47,
        "body": "Got it. Will pass to the eng channels.",
        "labels": ["SENT"],
    },
]


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------

SEEDED_DRAFTS: list[dict] = [
    {
        "logical_id": "DRAFT_OOO_REPLY",
        "from": "{{NAME_U05CLAUDE}} <{{EMAIL_U05CLAUDE}}>",
        "to": "{{EMAIL_U02JARED}}",
        "cc": None,
        "subject": "Re: covering my inbox",
        "body": (
            "Quick draft — finalize before I send.\n\n"
            "I'll be out 4/22 → 4/29. Default response handler is on. Ping me on "
            "Slack for true emergencies."
        ),
    },
    {
        "logical_id": "DRAFT_BUG_UPDATE",
        "from": "{{NAME_U05CLAUDE}} <{{EMAIL_U05CLAUDE}}>",
        "to": "{{EMAIL_U07RHEA}}",
        "cc": "{{EMAIL_U06DEVON}}",
        "subject": "Bug triage — weekly update",
        "body": (
            "Weekly bug triage rollup:\n"
            "- BUG-247: in flight, fix shipping today\n"
            "- BUG-246: deferred to next sprint\n"
            "- BUG-245: closed"
        ),
    },
]


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

SEEDED_FILTERS: list[dict] = [
    {
        "logical_id": "FILTER_RECEIPTS",
        "criteria": {"from": "receipts@aws.example OR receipts@stripe.example"},
        "action": {"addLabelIds": ["Receipts"]},  # label names; resolved to ids at seed time
    },
    {
        "logical_id": "FILTER_PRESS",
        "criteria": {"from": "press@gameinformer.example OR journalists@kotaku.example"},
        "action": {"addLabelIds": ["Press"]},
    },
]


# ---------------------------------------------------------------------------
# Verifier drift boundaries (entities to ignore when diffing)
# ---------------------------------------------------------------------------

# Label names that may legitimately exist outside the seeded set without
# counting as drift (system labels, Gmail categories, etc.).
IGNORE_LABEL_NAME_PATTERNS: list[str] = [
    r"^CATEGORY_",          # Gmail auto-categorizes; sometimes appears as user-visible
]

# System label IDs that prompts reference; never flagged as drift.
SYSTEM_LABELS: set[str] = {
    "INBOX", "SENT", "DRAFT", "TRASH", "SPAM",
    "STARRED", "IMPORTANT", "UNREAD",
    "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS",
    "CHAT",
}
