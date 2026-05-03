# Hintas Notion Workspace — Pre-Seeded Ground Truth (v1)

> **Terminology**: In Notion, the top-level org is a **workspace**. Inside it, content is organized as **pages** (documents) and **databases** (collections of pages with a shared schema). A page's content is a tree of **blocks** (paragraph, heading, to_do, toggle, code, image, callout, divider, etc.). Database rows are themselves pages whose properties match the database schema. Page/database/block/user IDs are UUIDs (the API accepts dashed `8-4-4-4-12` form or undashed `32` form). **Rich text** is the inline-formatting array used inside text-bearing blocks and rich_text properties; it can contain `mention` segments (`@user`, `@page`, `@date`). The agent connects as an **integration** (a bot user) and only sees pages/databases that have been explicitly **shared** to it.

This document defines the **exact state** the Notion workspace must be in before any benchmark prompt is executed. Every prompt in `benchmark_prompts.json` is grounded in the entities below.

The workspace is built in two stages:

1. **Pre-seed (operator, one-time per workspace).** Provision the workspace, invite/revoke users, create the workspace-parented pages and the unshared `Press Contacts` database, install the integration, and record the resulting IDs in `experiments/notion/scripts/prerequisites_<stack>.local.json`. See `experiments/notion/README.md` for the exact steps.
2. **Seed (`experiments/notion/scripts/seed_workspace.py`, fully automated).** Reads the prerequisites file, verifies that the unshared targets actually return 404 to the integration and that Pinkman's display name and Ember's revoke status are correct, then creates everything else (pages, databases, rows, blocks, comments, archived state) deterministically.

Anything Notion's API can't do from an integration token (workspace-parented pages, removing per-page integration access, user invites/role/revoke, user display-name renames, status-option group bucketing, human authorship of seeded content) is either handled in stage 1 or accepted as the documented reality (e.g. all seeded comments and rows are authored by the integration bot).

---

## 0. Benchmark clock anchor

All relative time references ("this week", "next 14 days", "yesterday", "tomorrow", "next Monday") in prompts resolve against:

```
benchmark_now = 2026-04-19T10:00:00-07:00   (America/Los_Angeles, Sunday)
```

Seeded `Date` properties, `Filed`, `Embargo Date`, and the timestamps embedded in seeded mentions are computed as offsets from `benchmark_now`. Notion stamps `created_time` and `last_edited_time` from real wall-clock at seed time — graders never compare those exactly; date-window prompts only check the seeded `Date`/`Filed`/`Embargo Date`/`Due` properties, which the seed step writes deterministically.

This is the same anchor used by `experiments/slack/state/workspace_state.v3.md` so cross-platform comparisons land on the same fictional Sunday.

---

## 1. Workspace

| Field | Value |
|---|---|
| Name | `Hintas` |
| Plan | **Plus** (required for unlimited file uploads, page-history past 7 days, and the per-page share-with-integration controls used below). Free plan blocks several fixtures: file uploads larger than 5 MB, version-history reads past 7 days, and ergonomic teamspace controls. |
| Timezone | `America/Los_Angeles` |
| Locale | `en-US` |
| Notion-API version (`Notion-Version` header) | `2022-06-28` (matches `experiments/notion/api/notion_openapi.yml`) |

Studio flavor (narrative only, not under test): Hintas is a small indie game studio shipping a 3D exploration game in May 2026. The same fiction backs the Slack benchmark.

---

## 2. Users

All IDs below are stable across the benchmark. Each `user_id` is a UUID assigned by Notion at workspace creation; operators should record the actual UUIDs into the per-stack `experiments/notion/scripts/workspace_state_ids_<stack>.json` during the first seed pass and reuse them on subsequent resets. The grading labels `U01..U10` are what `success_criteria` references.

| Label | `type` | Display name | Email | Workspace role | Status |
|---|---|---|---|---|---|
| `U01MIRANDA` | `person` | Miranda Okonkwo | `miranda@hintas.co` | Workspace Owner (admin) | Active |
| `U02JARED` | `person` | Jared Blackwood | `jared@hintas.co` | Member | Active |
| `U03PINKMAN` | `person` | Saul Rivera (display: `Pinkman`) | `pinkman@hintas.co` | Member | Active |
| `U04LAGOON` | `person` | Lagoon Takahashi | `lagoon@hintas.co` | Member | Active |
| `U05CLAUDE` | `person` | Claude Ellison | `claude@hintas.co` | Member | Active |
| `U06DEVON` | `person` | Devon Park | `devon@hintas.co` | Member | Active |
| `U07RHEA` | `person` | Rhea Kapoor | `rhea@hintas.co` | Member | Active |
| `U08TOMAS` | `person` | Tomás Vidal | `tomas@hintas.co` | Member | Active |
| `U09EMBER` | `person` | Ember Shah | `ember@hintas.co` | Member | **Revoked** 2026-02-14 (workspace access removed). |
| `U10AGENT` | `bot` | `Hintas Agent` | (no email — bot owner email is `miranda@hintas.co`) | Internal integration | Active |

Notion-API specifics for graders:

- `listUsers` returns all `person` users with active workspace access plus all `bot` users — i.e. `U01..U08` and `U10AGENT`. **`U09EMBER` is NOT returned by `listUsers`** because workspace access was revoked.
- `retrieveUser` against `U09EMBER`'s last-known `user_id` still returns a user object with `person.email` populated and a `name` field — Notion does not 404 a revoked user; the agent must detect the revoked state by absence-from-`listUsers`, not by error code.
- `retrieveBotUser` returns `U10AGENT` (the agent's own bot record), with `bot.workspace_name = "Hintas"` and `bot.owner.user.id = U01MIRANDA.id`.
- Display-name resolution: prompts use **first names**. The agent must resolve first name → `user_id` either by enumerating `listUsers` and matching `name` (case-insensitive, accents-stripped for `Tomás`) or by hitting a directory mention in seeded rich-text.

---

## 3. Integration (the agent)

| Field | Value |
|---|---|
| Integration type | **Internal integration** (workspace-scoped, single-token, no OAuth flow) |
| Bot user label | `U10AGENT` |
| Bot name | `Hintas Agent` |
| Owner | `U01MIRANDA` |
| Capabilities | `read_content`, `update_content`, `insert_content`, `read_user_info`, `read_user_with_email`, `read_comments`, `insert_comments` |
| User-info option | `Read user information including email addresses` (required so `listUsers` returns `person.email` and so `users.lookup`-style flows succeed) |

### 3.1 Pages/databases shared to the integration

The integration is **explicitly shared** to:

- `P01_HINTAS_ROOT` (and via inheritance, every non-private descendant)
- `P02_TEAM_DIR`
- `P03_PROJECTS` (and descendants `P04_TOMB3`, `P05_LAUNCH26`)
- `P06_MEETING_NOTES_HOME`
- `P07_PLAYTEST_ARCHIVE`
- All four canonical databases: `DB_BUGS`, `DB_TASKS`, `DB_MEETING_NOTES`, `DB_PROJECTS`

### 3.2 Pages/databases NOT shared to the integration

The integration is **NOT shared** to:

- `P08_LEADS_ONLY` (the 🔒 Leads-only top-level page) and its child `P11_LEADS_NOTES`
- `DB_PRESS_CONTACTS` (created by the operator pre-seed; see experiments/notion/README.md)

These three IDs are recorded in the per-stack `experiments/notion/scripts/prerequisites_<stack>.local.json`. The seeder reads them and aborts unless each one returns 404 to the integration before any seeding work begins.

API behavior for non-shared targets: `retrievePage` / `retrieveDatabase` / `queryDatabase` / `retrieveBlockChildren` against a non-shared `id` return **HTTP 404** with `{"object": "error", "code": "object_not_found", "message": "Could not find …"}`. The agent must treat this as the access boundary, not as a missing entity.

`search` only returns pages/databases shared to the integration; non-shared entities never appear in results. This is load-bearing for prompt 21 (Press contacts visibility).

---

## 4. Top-level page hierarchy

The workspace is rooted at a single top-level page `Hintas` plus one private sibling. All UUIDs below are placeholders: assign real values at seed time and persist them to the per-stack `experiments/notion/scripts/workspace_state_ids_<stack>.json`. The labels (`P01..P10`) are what `success_criteria` references.

```
[workspace root]
├── P01_HINTAS_ROOT   "Hintas"                     (page, icon 🎮, parent.workspace=true)
│   ├── P02_TEAM_DIR        "Team Directory"        (page, icon 👥)
│   ├── P03_PROJECTS        "Projects"              (page, icon 📁)
│   │   ├── P04_TOMB3            "Tomb-3 Level Design"  (page, icon 🗿)
│   │   ├── P05_LAUNCH26         "Launch 2026"          (page, icon 🚀)
│   │   ├── DB_BUGS              "Bugs"                 (database)
│   │   └── DB_TASKS             "Tasks"                (database)
│   ├── P06_MEETING_NOTES_HOME  "Meeting Notes"     (page, icon 📝)
│   │   └── DB_MEETING_NOTES     "Meeting Notes"        (database)
│   ├── P07_PLAYTEST_ARCHIVE    "Playtest Archive"  (page, icon 📦)
│   │   ├── P09_PLAYTEST_A2     "Playtest — alpha round 2"   (page)
│   │   └── P10_PLAYTEST_A3     "Playtest — alpha round 3"   (page, archived/in_trash)
│   └── DB_PROJECTS             "Projects (catalog)"  (database, relation target only)
│
└── P08_LEADS_ONLY    "🔒 Leads-only"               (page, parent.workspace=true, NOT shared to integration; pre-seed)
    └── P11_LEADS_NOTES      "Leads sync notes"     (page; pre-seed)

(DB_PRESS_CONTACTS is created pre-seed at any location not shared to the integration; the operator records its id in prerequisites.local.json.)
```

Key invariants:

- `P01_HINTAS_ROOT` and `P08_LEADS_ONLY` both have `parent.type = "workspace"`, `parent.workspace = true`. The seeder cannot create workspace-parented pages — the operator creates `P01` and `P08` (with `P11_LEADS_NOTES` as a child) by hand pre-seed.
- `P10_PLAYTEST_A3` has `archived = true` and `in_trash = true`. `retrievePage` succeeds and returns it; `updatePage` / `appendBlockChildren` fail with `validation_error` ("Can't edit block in trashed page").
- `P08_LEADS_ONLY` is not shared to the integration. Search results never surface it; direct `retrievePage` returns 404.

---

## 5. Databases

Five databases are seeded. `DB_BUGS`, `DB_TASKS`, `DB_MEETING_NOTES`, `DB_PRESS_CONTACTS` carry seeded rows; `DB_PROJECTS` is a tiny relation-target catalog.

### 5.1 `DB_BUGS` — Bugs

Parent: `P03_PROJECTS`. Title: `Bugs`. Description: rich-text "Active and resolved bugs across all platforms.".

| Property | Type | Options / details |
|---|---|---|
| `Title` | `title` | The bug's one-line headline. |
| `Bug ID` | `rich_text` | `BUG-NNN` format. |
| `Severity` | `select` | `Low`, `Medium`, `High`, `Blocker` |
| `Status` | `status` | Options: `Open`, `In Progress`, `Fixed`, `Won't Fix` (groupings are unconstrained — the API can't reassign options to groups, and no prompt filters by group). |
| `Reporter` | `people` | Single person expected. |
| `Assignee` | `people` | Single person expected. |
| `Platform` | `multi_select` | `macOS`, `Windows`, `Linux`, `Switch` |
| `Filed` | `date` | Single date (no end). |
| `Related Task` | `relation` | → `DB_TASKS` (single-direction). |
| `URL` | `url` | Optional links to logs / repros. |

#### Seeded rows (label, properties)

| Label | Title | Bug ID | Severity | Status | Reporter | Assignee | Platform | Filed (offset from now) | Related Task | URL |
|---|---|---|---|---|---|---|---|---|---|---|
| `BUG245` | "Audio desync after cutscene" | `BUG-245` | Medium | In Progress | U08TOMAS | U06DEVON | macOS, Windows | 11d ago | (none) | (none) |
| `BUG246` | "Main-menu flicker on launch" | `BUG-246` | Low | Open | U03PINKMAN | (unassigned) | macOS | 13d ago | (none) | (none) |
| `BUG247` | "Save-file corruption on macOS" | `BUG-247` | **Blocker** | In Progress | U03PINKMAN | U06DEVON | macOS | 6d ago | `TASK_FIX_TILE_LOADER` | `https://ci.hintas.co/builds/842` |
| `BUG248` | "Tomb-3 door collider blocks player on revisit" | `BUG-248` | High | Open | U03PINKMAN | U07RHEA | macOS, Windows | 4d ago | (none) | (none) |
| `BUG230` | "Settings dialog scrollbar overlap" | `BUG-230` | Low | Fixed | U08TOMAS | U07RHEA | Windows | 45d ago | (none) | (none) |
| `BUG231` | "Save thumbnail blurry at 1080p" | `BUG-231` | Low | Won't Fix | U03PINKMAN | (unassigned) | Windows, Linux | 50d ago | (none) | (none) |
| `BUG244` | "Localization: French quote marks" | `BUG-244` | Medium | Fixed | U04LAGOON | U07RHEA | macOS, Windows, Linux, Switch | 18d ago | (none) | (none) |

### 5.2 `DB_TASKS` — Tasks

Parent: `P03_PROJECTS`. Title: `Tasks`. Description: rich-text "Engineering and design work.".

| Property | Type | Options / details |
|---|---|---|
| `Task` | `title` | One-line task name. |
| `Owner` | `people` | Single person. |
| `Due` | `date` | **Calendar-surface property.** Date-only (no time). |
| `Status` | `status` | Options: `Backlog`, `Up Next`, `In Progress`, `Done` (groupings are unconstrained — see §5.1). |
| `Priority` | `select` | `P0`, `P1`, `P2`, `P3` |
| `Estimate` | `number` | Days; format `number`. |
| `Tags` | `multi_select` | `eng`, `design`, `qa`, `marketing`, `launch-blocker` |
| `Project` | `relation` | → `DB_PROJECTS`. |

#### Seeded rows

`Due` offsets are computed from `benchmark_now` (Sunday 2026-04-19). Operators MUST honor these offsets at seed time so calendar prompts ("Due this week", "Due in next 14 days", "Overdue") match deterministically.

| Label | Task | Owner | Due | Status | Priority | Estimate | Tags | Project |
|---|---|---|---|---|---|---|---|---|
| `TASK_FIX_TILE_LOADER` | "Fix async tile loader chunk drop" | U06DEVON | 2026-04-21 (`+2d`) | In Progress | P0 | 2 | eng, launch-blocker | `PROJ_TOMB3` |
| `TASK_TOMB3_LIGHTING` | "Polish tomb-3 lighting passes B & C" | U01MIRANDA | 2026-04-23 (`+4d`) | In Progress | P1 | 3 | design | `PROJ_TOMB3` |
| `TASK_PRESS_LIST` | "Finalize press contact list" | U04LAGOON | 2026-04-22 (`+3d`) | Up Next | P1 | 1 | marketing, launch-blocker | `PROJ_LAUNCH` |
| `TASK_TRAILER_COPY` | "Write final trailer copy" | U04LAGOON | 2026-04-21 (`+2d`) | In Progress | P0 | 1 | marketing, launch-blocker | `PROJ_LAUNCH` |
| `TASK_BRAND_KIT` | "Brand-kit handoff to PR firm" | U01MIRANDA | 2026-04-17 (`-2d`, **overdue**) | In Progress | P1 | 1 | marketing, design | `PROJ_LAUNCH` |
| `TASK_BUG247_VERIFY` | "Verify BUG-247 fix on macOS 14.4" | U08TOMAS | 2026-04-22 (`+3d`) | Up Next | P0 | 1 | qa, launch-blocker | `PROJ_TOMB3` |
| `TASK_CONCEPT_REVIEW` | "Concept review session — tomb-3" | U05CLAUDE | 2026-04-15 (`-4d`, **overdue**) | Done | P2 | 1 | design | `PROJ_TOMB3` |
| `TASK_CHANGELOG` | "Draft alpha-build changelog" | U02JARED | 2026-04-26 (`+7d`) | Backlog | P2 | 1 | eng | `PROJ_LAUNCH` |
| `TASK_LISBON_LOGISTICS` | "Book Lisbon offsite flights" | U04LAGOON | 2026-05-15 (`+26d`) | Backlog | P3 | 2 | (none) | `PROJ_OFFSITE` |
| `TASK_MIGRATE_INVENTORY` | "Migrate inventory schema to v3" | U06DEVON | 2026-05-01 (`+12d`) | Backlog | P2 | 5 | eng | `PROJ_TOMB3` |
| `TASK_RHEA_INPUT_REBIND` | "Input rebind UI polish" | U07RHEA | 2026-04-30 (`+11d`) | Backlog | P2 | 2 | eng | `PROJ_TOMB3` |
| `TASK_QA_REGRESSION` | "Run regression suite on alpha" | U03PINKMAN | 2026-04-24 (`+5d`) | Up Next | P1 | 2 | qa, launch-blocker | `PROJ_LAUNCH` |

### 5.3 `DB_MEETING_NOTES` — Meeting Notes

Parent: `P06_MEETING_NOTES_HOME`. Title: `Meeting Notes`. Description: rich-text "Recurring syncs, design reviews, retros.".

| Property | Type | Options / details |
|---|---|---|
| `Title` | `title` | Topic of the meeting. |
| `Date` | `date` | Date + time (Pacific). |
| `Attendees` | `people` | Multiple. |
| `Type` | `select` | `standup`, `design-review`, `retro`, `all-hands` |
| `Follow-ups` | `rich_text` | **Mention surface.** Contains `@user` and `@page` mentions. |
| `Action Items` | `relation` | → `DB_TASKS`, multi-target. |

#### Seeded rows

| Label | Title | Date (offset) | Attendees | Type | Follow-ups (text) | Action Items |
|---|---|---|---|---|---|---|
| `MTG_TOMB3_REVIEW` | "Tomb-3 design review" | 2026-04-12 14:00 (`-7d`) | U01MIRANDA, U05CLAUDE, U07RHEA | design-review | "@Miranda to push the warm-rim lighting on angle B; followup tracked in @[Tomb-3 Level Design]." | `TASK_TOMB3_LIGHTING` |
| `MTG_BUG247_TRIAGE` | "BUG-247 triage" | 2026-04-13 11:00 (`-6d`) | U02JARED, U03PINKMAN, U06DEVON | standup | "@Jared owns escalation. @Devon investigates async streamer. See @[Tomb-3 Level Design] notes." | `TASK_FIX_TILE_LOADER`, `TASK_BUG247_VERIFY` |
| `MTG_LAUNCH_STANDUP` | "Launch standup" | 2026-04-17 09:00 (`-2d`) | U01MIRANDA, U02JARED, U04LAGOON, U05CLAUDE | standup | "Marketing is 60% ready. @Lagoon: trailer copy by Tuesday EOD. @Miranda: brand kit signed off." | `TASK_TRAILER_COPY`, `TASK_PRESS_LIST` |
| `MTG_ALL_HANDS` | "April all-hands" | 2026-04-06 11:00 (`-13d`) | U01MIRANDA, U02JARED, U03PINKMAN, U04LAGOON, U05CLAUDE, U06DEVON, U07RHEA, U08TOMAS | all-hands | "Recap of milestones; @Miranda demoed tomb-3 stills." | (none) |
| `MTG_QA_RETRO` | "QA retro — alpha round 2" | 2026-03-30 15:00 (`-20d`) | U03PINKMAN, U08TOMAS, U02JARED | retro | "Three repeat regressions; @Pinkman to set up nightly smoke run." | (none) |
| `MTG_ENG_PLANNING` | "Eng planning — week of 4/13" | 2026-04-13 10:00 (`-6d`) | U02JARED, U06DEVON, U07RHEA | standup | "Sprint goals locked. @Rhea on input UI; @Devon on inventory v3 spike." | `TASK_RHEA_INPUT_REBIND`, `TASK_MIGRATE_INVENTORY` |
| `MTG_PRESS_PREP` | "Press preview prep" | 2026-04-15 13:00 (`-4d`) | U04LAGOON, U05CLAUDE | standup | "Coverage embargo set to 2026-05-03. @Lagoon: press list. @Claude: legal review." | `TASK_PRESS_LIST` |
| `MTG_LEADS_SYNC` | "Leads sync" | 2026-04-09 16:00 (`-10d`) | U01MIRANDA, U02JARED, U03PINKMAN, U04LAGOON | retro | "Cadence locked: weekly Wednesdays. @Jared owns the agenda." | (none) |

### 5.4 `DB_PROJECTS` — Projects (catalog)

Parent: `P03_PROJECTS`. Title: `Projects (catalog)`. Single-purpose: relation target for `DB_TASKS.Project`.

| Property | Type | Options |
|---|---|---|
| `Name` | `title` | |
| `Lead` | `people` | Single. |
| `Status` | `status` | `Active`, `On hold`, `Done` |

| Label | Name | Lead | Status |
|---|---|---|---|
| `PROJ_TOMB3` | "Tomb-3" | U01MIRANDA | Active |
| `PROJ_LAUNCH` | "Launch 2026" | U04LAGOON | Active |
| `PROJ_OFFSITE` | "Lisbon offsite" | U05CLAUDE | On hold |

### 5.5 `DB_PRESS_CONTACTS` — Press Contacts

Title: `Press Contacts`. **Created pre-seed by the operator and NOT shared to the integration**; the id is recorded in `experiments/notion/scripts/prerequisites.local.json`.

The schema and any rows inside are opaque to the agent — every read attempt (`retrieveDatabase`, `queryDatabase`, `search`) returns `object_not_found`. The benchmark only uses this database to test access-boundary handling; rows are not seeded.

---

## 6. Block content on narrative pages

Every block below has a stable grading label (`B01..B40`) used by `success_criteria`. UUIDs are assigned at seed time. Order matters: `retrieveBlockChildren` returns children in document order.

### 6.1 `P04_TOMB3` — "Tomb-3 Level Design"

| Label | Type | Content |
|---|---|---|
| `B01` | `heading_1` | "Tomb-3 Level Design" |
| `B02` | `paragraph` | "Owner: @Miranda. Last updated: 2026-04-15." (rich_text contains a `mention.user` segment for U01MIRANDA) |
| `B03` | `heading_2` | "Pillars" |
| `B04` | `bulleted_list_item` | "Verticality — players see the goal before they reach it." |
| `B05` | `bulleted_list_item` | "Diegetic light cues — warm = safe, cool = unknown." |
| `B06` | `bulleted_list_item` | "No combat in tomb interior." |
| `B07` | `heading_2` | "Open issues" |
| `B08` | `to_do` | "Lighting pass on angle B — warm rim" (`checked: true`) |
| `B09` | `to_do` | "Lighting pass on angle E — warmer" (`checked: false`) |
| `B10` | `to_do` | "Door collider revisit (BUG-248)" (`checked: false`) |
| `B11` | `callout` | icon: 🚧, color: `yellow_background`. Text: "Save-file corruption is a launch blocker — see @[BUG-247 row]." (rich_text contains a `mention.page` to `BUG247`'s row id) |
| `B12` | `toggle` | "Reference angles (click to expand)". Has 3 children: |
| `B12_C1` | `image` (child of `B12`) | external URL: `https://assets.hintas.co/tomb3/angle_a.png` |
| `B12_C2` | `image` (child of `B12`) | external URL: `https://assets.hintas.co/tomb3/angle_b.png` |
| `B12_C3` | `image` (child of `B12`) | external URL: `https://assets.hintas.co/tomb3/angle_c.png` |
| `B13` | `divider` | (no content) |
| `B14` | `code` | language: `python`. Text: "# pseudo-code for streaming budget\nbudget = 256 * MB\nif gpu_pressure > 0.8 * budget:\n    drop_chunk()" |
| `B15` | `paragraph` | "Last reviewed by @Claude." (mention.user for U05CLAUDE) |

### 6.2 `P05_LAUNCH26` — "Launch 2026"

| Label | Type | Content |
|---|---|---|
| `B20` | `heading_1` | "Launch 2026" |
| `B21` | `paragraph` | "Ship target: 2026-05-10. Press preview: 2026-05-03." |
| `B22` | `heading_2` | "Marketing checklist" |
| `B23` | `to_do` | "Trailer copy" (`checked: false`) |
| `B24` | `to_do` | "Press list finalized" (`checked: false`) |
| `B25` | `to_do` | "Brand kit handoff" (`checked: true`) |
| `B26` | `heading_2` | "Engineering checklist" |
| `B27` | `to_do` | "BUG-247 fix verified on macOS 14.4" (`checked: false`) |
| `B28` | `to_do` | "Streaming-cert renewed" (`checked: false`) |
| `B29` | `divider` | |
| `B30` | `paragraph` | "Owner: @Lagoon. Eng-lead: @Jared." (two `mention.user` segments) |

### 6.3 `P02_TEAM_DIR` — "Team Directory"

| Label | Type | Content |
|---|---|---|
| `B35` | `heading_1` | "Team Directory" |
| `B36` | `paragraph` | "Active team members (April 2026):" |
| `B37` | `bulleted_list_item` | "@Miranda — Lead Designer" |
| `B38` | `bulleted_list_item` | "@Jared — Engineering Manager" |
| `B39` | `bulleted_list_item` | "@Pinkman — QA Lead" |
| `B40` | `bulleted_list_item` | "@Lagoon — Marketing & Community" |
| `B41` | `bulleted_list_item` | "@Devon — Backend Engineer" |
| `B42` | `bulleted_list_item` | "@Rhea — Frontend Engineer" |
| `B43` | `bulleted_list_item` | "@Tomás — QA Tester" |
| `B44` | `bulleted_list_item` | "@Claude — Founder" |

(Each item carries a `mention.user` segment.)

### 6.4 `P09_PLAYTEST_A2` — "Playtest — alpha round 2"

Three blocks: a heading, a paragraph summary, and a toggle "Raw participant notes" with a single child paragraph block. Exact content is not load-bearing; this page exists so unarchive workflows have something to operate on.

### 6.5 Pagination boundary page

`P02_TEAM_DIR` has exactly **11 children** (the 9 bullets above plus 2 trailing dividers `B45`, `B46`). Prompts that call `retrieveBlockChildren` with `page_size=10` MUST receive `has_more=true` and a `next_cursor`. This is the canonical pagination surface for graders.

---

## 7. Mentions inventory

Rich-text mentions seeded in the workspace. Every prompt that asks "find mentions of @X" should grade against this list.

| Mention | Where it appears | Mention type |
|---|---|---|
| `@Miranda` | `B02` (Tomb-3), `B37` (Team Dir), `MTG_TOMB3_REVIEW.Follow-ups`, `MTG_LAUNCH_STANDUP.Follow-ups`, `MTG_ALL_HANDS.Follow-ups` | `mention.user` |
| `@Jared` | `B30` (Launch — "Eng-lead: @Jared"), `B38` (Team Dir), `MTG_BUG247_TRIAGE.Follow-ups`, `MTG_LEADS_SYNC.Follow-ups` | `mention.user` |
| `@Pinkman` | `B39` (Team Dir), `MTG_QA_RETRO.Follow-ups` | `mention.user` |
| `@Lagoon` | `B30` (Launch — "Owner: @Lagoon"), `B40` (Team Dir), `MTG_LAUNCH_STANDUP.Follow-ups`, `MTG_PRESS_PREP.Follow-ups` | `mention.user` |
| `@Devon` | `B41` (Team Dir), `MTG_BUG247_TRIAGE.Follow-ups`, `MTG_ENG_PLANNING.Follow-ups` | `mention.user` |
| `@Rhea` | `B42` (Team Dir), `MTG_ENG_PLANNING.Follow-ups` | `mention.user` |
| `@Tomás` | `B43` (Team Dir) | `mention.user` |
| `@Claude` | `B15` (Tomb-3), `B44` (Team Dir), `MTG_PRESS_PREP.Follow-ups` | `mention.user` |
| `@[Tomb-3 Level Design]` | `MTG_TOMB3_REVIEW.Follow-ups`, `MTG_BUG247_TRIAGE.Follow-ups` | `mention.page` → `P04_TOMB3` |
| `@[BUG-247 row]` | `B11` (Tomb-3 callout) | `mention.page` → `BUG247`'s page id |
| `@[Bugs]` | (no database mentions — only page mentions are seeded) | n/a |
| `@2026-05-10` (date mention) | `B21` (Launch — "Ship target: ...") | `mention.date` |

`@Ember` is **NOT** mentioned anywhere. A prompt asks the agent to confirm that and to detect Ember's revoked-user status by absence-from-`listUsers`.

---

## 8. Comments

Five seeded comments. **All five are authored by the integration bot (`U10AGENT`)** because the seeder runs under the integration token and Notion attributes every comment to its creator. Prompts test text and threading, not author identity, for seeded comments. Comments the agent itself creates during a prompt run are also bot-authored — that property is graded directly (e.g. prompts 30 and 31 expect `author = U10AGENT`).

| Label | Parent | Content |
|---|---|---|
| `CMT01` | Page-level on `BUG247` | "@Devon can you confirm this repros on Sonoma 14.3 too?" |
| `CMT02` | Page-level on `BUG247` | "Confirmed on 14.3 and 14.4. Streamer drops chunk under 6 GB GPU pressure." |
| `CMT03` | Block-level on `B11` (callout in Tomb-3 page) | "Marking this as launch-critical — let's keep it visible." |
| `CMT04` | Block-level on `B14` (code block in Tomb-3 page) | "Real impl uses an LRU; pseudo-code is for clarity only." |
| `CMT05` | Page-level on `MTG_BUG247_TRIAGE` | "Smoke run was clean on Windows. macOS still flaky." |

`listComments` against `BUG247.id` returns `CMT01` and `CMT02` (page-level only — block-level comments aren't surfaced in page-level listings; agents must list comments per-block to find `CMT03`/`CMT04`). Per Notion's API: `listComments` returns top-level comments and threaded replies for a single discussion thread; in this seed every comment is its own thread.

---

## 9. Archived state

| Entity | State |
|---|---|
| `P10_PLAYTEST_A3` | `archived: true`, `in_trash: true`. `retrievePage` succeeds; `updatePage`/`appendBlockChildren` fail with `validation_error`. |
| (no archived databases in v1) | — |
| (no archived blocks individually) | — |

The unarchive workflow prompt (id 36) asks the agent to set `archived: false` on `P10_PLAYTEST_A3`, restoring write access.

---

## 10. Load-bearing facts agents may rely on

1. The agent connects via an internal-integration token; capabilities are exactly as listed in §3. There is no per-user impersonation.
2. `retrieveBotUser` returns `U10AGENT` with `bot.workspace_name = "Hintas"`.
3. `listUsers` returns persons `U01..U08` plus the bot `U10AGENT`. **`U09EMBER` is absent**.
4. `retrieveUser` against `U09EMBER`'s `user_id` succeeds and returns the user object — Notion does not 404 a revoked user. The agent must distinguish "revoked" from "deleted" by `listUsers` membership.
5. `search` is integration-scoped: only pages/databases shared to the integration appear in results. `P08_LEADS_ONLY` and `DB_PRESS_CONTACTS` never appear.
6. `queryDatabase` returns rows in the database's last-saved sort order unless `sorts` is supplied. Operators must NOT rely on insertion order in success_criteria; prompts that need ordering specify a `sorts` clause.
7. Pagination: `queryDatabase` and `retrieveBlockChildren` paginate via `start_cursor` + `next_cursor`; `page_size` max is `100`. The agent must follow `has_more = true` until exhausted when prompts ask for full counts.
8. Page IDs accept both dashed (`8-4-4-4-12`) and undashed (`32` hex chars) input on every endpoint. Responses always return dashed form.
9. Property updates via `updatePage` accept either property name OR property id as the key; the response uses property id. Property name matching is **case-sensitive**.
10. `archived: true` (a.k.a. trashed) blocks all writes against the entity. Set `archived: false` to restore.
11. `appendBlockChildren` accepts up to **100 children per call** and **2 levels of nesting per call**; deeper trees require a follow-up call rooted at the inserted parent block's id.
12. Rich-text rendering: `rich_text` arrays preserve order. Mentions are first-class segments with `type: "mention"` and a `mention.user` / `mention.page` / `mention.database` / `mention.date` discriminator.
13. Every seeded page, database row, block, and comment is `created_by` the integration bot (`U10AGENT`) because the seeder runs under the integration token. No prompt grades `created_by` against a human user; tests that touch authorship explicitly expect `U10AGENT` (e.g. prompts 30 and 31).

---

## 11. Reset discipline

Operators MUST reset the workspace back to this exact snapshot before every prompt run. Many prompts are destructive (create/archive/move pages, delete blocks, mutate property values, post comments, append block trees). Running prompts back-to-back without reset will invalidate the expected `success_criteria` listed in later prompts. Reset implementation is out of scope for this document; it lives in `experiments/notion/scripts/reset_workspace.py`.

---

## 12. Naming contract for prompts

Prompts refer to people by **first name only** (Miranda, Jared, Pinkman, Lagoon, Devon, Rhea, Tomás, Claude, Ember). Agents must resolve first name → `user_id` via `listUsers` (filtering by `name`) or by inspecting an existing seeded `mention.user`. Pages and databases are referenced by their human-readable title (e.g. "the Bugs database", "the Tomb-3 Level Design page"); agents resolve title → UUID via `search`.

Database rows are referenced by their `Title`/`Task`/`Name` property value (e.g. "the BUG-247 row", "the Tomb-3 lighting task"); agents resolve via `queryDatabase` with a `title` or `rich_text` filter, or via `search`.
