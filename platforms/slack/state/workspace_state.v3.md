# Hintas Workspace — Pre-Seeded Ground Truth (v2)

> **Terminology**: In Slack, the top-level org is a **workspace** (not a "server"). Inside a workspace, people talk in **channels** (public `#name` or private 🔒), **direct messages** (1:1 DMs), and **multi-person DMs (MPIMs)**. User and channel identifiers are opaque IDs (e.g. `U01MIRANDA`, `C001GENERAL`). Message identifiers are the message's `ts` — a string like `1744320000.000100`.

This document defines the **exact state** the Slack workspace must be in before any benchmark prompt is executed. Every prompt in `benchmark_prompts.json` is grounded in the entities below. Operators running the benchmark must create this state before running agents against it.

---

## 0. Benchmark clock anchor

All relative time references ("last 14 days", "tomorrow 09:00", "this week") in prompts are relative to:

```
benchmark_now = 2026-04-19T10:00:00-07:00   (America/Los_Angeles, a Sunday)
```

When seeding the workspace, compute every seeded message's `ts` **relative to `benchmark_now`** using the day-offsets in section 7. Do not seed with today's real wall-clock; always anchor to `benchmark_now` so that "last 14 days" windows deterministically cover the same messages on every run.

---

## 1. Workspace

| Field | Value |
|---|---|
| Name | `Hintas` |
| Domain | `hintas.slack.com` |
| Locale | `en-US` |
| Timezone | `America/Los_Angeles` |
| Plan | **Enterprise Grid** (required so `admin.users.*`, `admin.conversations.*`, `admin.emoji.*`, and channel-posting-restrictions via `admin.conversations.setConversationPrefs` are all available) |
| Discovery API | **Not enabled** — admin users cannot read other pairs' 1:1 DMs via `search.messages` or `conversations.history`. This is deliberate so edge-case prompts can be graded. |

Studio flavor (narrative only, not under test): Hintas is a small indie game studio shipping a 3D exploration game in May 2026.

---

## 2. Users

All IDs are stable across the benchmark.

| Slack ID | Display name | Real name | Email | Title | Status |
|---|---|---|---|---|---|
| `U01MIRANDA` | `miranda` | Miranda Okonkwo | `miranda@hintas.co` | Lead Designer | Active |
| `U02JARED`   | `jared`   | Jared Blackwood | `jared@hintas.co`   | Engineering Manager | Active |
| `U03PINKMAN` | `pinkman` | Saul Rivera | `pinkman@hintas.co` | QA Lead | Active |
| `U04LAGOON`  | `lagoon`  | Lagoon Takahashi | `lagoon@hintas.co`  | Marketing & Community | Active |
| `U05CLAUDE`  | `claude`  | Claude Ellison | `claude@hintas.co`  | Founder / Workspace Admin | Active (**Workspace Admin + Org Primary Owner**) |
| `U06DEVON`   | `devon`   | Devon Park | `devon@hintas.co`   | Backend Engineer | Active |
| `U07RHEA`    | `rhea`    | Rhea Kapoor | `rhea@hintas.co`    | Frontend Engineer | Active |
| `U08TOMAS`   | `tomas`   | Tomás Vidal | `tomas@hintas.co`   | QA Tester | Active |
| `U09EMBER`   | `ember`   | Ember Shah | `ember@hintas.co`   | Narrative Designer | **Deactivated** 2026-02-14 |
| `U10BOT_CI`  | `ci-bot`  | CI Bot | (bot) | Bot user (Jenkins-style CI) | Active (bot) |

Pinkman's `display_name_normalized` = `pinkman`. Pinkman's `real_name` = `Saul Rivera` (no quoted nickname in the real-name field).

### Presence & DND (required)
- `jared` has DND configured: 22:00–07:00 `America/Los_Angeles` daily. At `benchmark_now` (10:00 Sunday), the nightly window is NOT active.
- `pinkman` currently has an **ad-hoc snooze active** that ends at `benchmark_now + 2h` (= 12:00 local, Sunday).
- Everyone else has presence `auto`, no active snooze.

### Auth scopes (required MCP scope set)
The MCP acts with a **user token belonging to `U05CLAUDE`** holding (at minimum): `channels:read`, `channels:write`, `channels:manage`, `channels:history`, `groups:read`, `groups:write`, `groups:history`, `im:read`, `im:write`, `im:history`, `mpim:read`, `mpim:write`, `mpim:history`, `chat:write`, `chat:write.public`, `reactions:read`, `reactions:write`, `pins:read`, `pins:write`, `files:read`, `files:write`, `users:read`, `users:read.email`, `users.profile:read`, `users.profile:write`, `usergroups:read`, `usergroups:write`, `dnd:read`, `dnd:write`, `emoji:read`, `reminders:read`, `reminders:write`, `search:read`, `admin.users:write`, `admin.conversations:write`.

The token distribution class is **"Marketplace-equivalent"** (Tier 3 / `limit=999` / 50-ish rpm). Benchmarks that hit bulk `conversations.history` will NOT fall under the post-May-2025 1-rpm, 15-item cap.

---

## 3. Channels

### 3.1 Public channels

| ID | Name | Creator | Created (days before `benchmark_now`) | Topic | Purpose | Members |
|---|---|---|---|---|---|---|
| `C001GENERAL` | `general` | U05CLAUDE | 400d | "Welcome! Keep it friendly." | Company-wide | Everyone active (incl. ci-bot) |
| `C002RANDOM` | `random` | U05CLAUDE | 400d | "Lower the stakes." | Off-topic | Everyone active |
| `C003ENGBACK` | `eng-backend` | U02JARED | 350d | "Servers, tools, build pipeline." | Backend eng | Jared, Devon, Claude, ci-bot |
| `C004ENGFRONT` | `eng-frontend` | U02JARED | 350d | "UI, rendering, input." | Frontend eng | Jared, Rhea, Claude, **Devon** |
| `C005DESIGNRV` | `design-reviews` | U01MIRANDA | 330d | "Post work, give crits, be kind." | Design reviews | Miranda, Claude, Rhea, **Devon** |
| `C006QA` | `qa-bugs` | U03PINKMAN | 300d | "File with BUG-### prefix." | Bug triage | Pinkman, Tomás, Jared, Claude |
| `C007MKT` | `marketing` | U04LAGOON | 300d | "Voice of the game." | Marketing / social | Lagoon, Claude |
| `C009INCIDENTS` | `incidents` | U05CLAUDE | 200d | "Paging the team only." | Incidents | Jared, Devon, Rhea, Pinkman, Claude, **ci-bot** |
| `C010ANNOUNCE` | `announcements` | U05CLAUDE | 400d | "Admins only post." | Official announcements | Everyone active (read); admins post |

*Note*: Devon has been added to `#eng-frontend` and `#design-reviews` (vs. v1) so that destructive prompts (kick/leave) have a valid target. ci-bot has been added to `#incidents` (vs. v1) so the ci-bot-in-incidents prompts are coherent.

`#announcements` has a per-channel posting restriction of **admins + owners only** (enforced via `admin.conversations.setConversationPrefs` at seed time). Claude is an admin; other humans cannot post there.

### 3.2 Private channels

| ID | Name | Creator | Created (days before `benchmark_now`) | Members |
|---|---|---|---|---|
| `C008LAUNCH` | `launch-2026` | U04LAGOON | 120d | Miranda, Jared, Lagoon, Claude |
| `C012LEADS` | `leads-only` | U05CLAUDE | 180d | Miranda, Jared, Pinkman, Lagoon, Claude |

### 3.3 Archived channels

| ID | Name | State |
|---|---|---|
| `C011OLDPLAYTEST` | `old-playtest-2025` | **Archived** 160d before `benchmark_now`. Created by U05CLAUDE. |

### 3.4 Direct messages

Each of the DMs below MUST already have history (seed messages are in section 7).

- `D01_MI_JA` — Miranda ↔ Jared (1:1)
- `D02_PI_LA` — Pinkman ↔ Lagoon (1:1)
- `D03_MI_CL` — Miranda ↔ Claude (1:1)
- `D04_JA_CL` — Jared ↔ Claude (1:1)

### 3.5 Multi-person DMs

- `G01_LEADS_MPIM` — Miranda + Jared + Pinkman (no Lagoon, no Claude)

---

## 4. User groups

| ID | Handle | Name | Members | Default channels |
|---|---|---|---|---|
| `S01LEADS`   | `leads`     | Department Leads  | Miranda, Jared, Pinkman, Lagoon | — |
| `S02ENG`     | `engineers` | All engineers     | Jared, Devon, Rhea | `#eng-backend`, `#eng-frontend` |
| `S03QA`      | `qa`        | QA team           | Pinkman, Tomás | `#qa-bugs` |
| `S04MKT`     | `marketing` | Marketing         | Lagoon | `#marketing` |

---

## 5. Custom emoji (required)

| Name | Type | Added (days before `benchmark_now`) |
|---|---|---|
| `:raider_skull:` | custom image | 50d |
| `:gold_gold:` | custom image | 35d |
| `:ship_it_raider:` | alias of `:ship_it:` | 30d |

Verification note for prompt 57: `:gold_gold:` must have **zero** usage in seeded reactions. `:raider_skull:` must appear in reactions. `:ship_it_raider:` must appear in reactions at least once (so the alias-handling path is testable).

---

## 6. Pins, reactions, reminders, scheduled messages, files

### 6.1 Pinned messages

- `#launch-2026`: message `M7` (Lagoon's launch checklist). Pin added by Lagoon.
- `#general`: message `M8` (Miranda's "Team Lisbon offsite"). Pin added by Miranda.
- `#eng-backend`: message `P1` — Jared's "Code freeze rules: no merges after Friday 5pm PT." seeded 45 days before `benchmark_now`.

### 6.2 Reactions (required)

- `M1` (announcements / alpha ship): `:eyes:` from Miranda, Jared, Lagoon; `:+1:` from Devon, Rhea, Pinkman.
- `M5` (design review): `:fire:` from Jared, Claude; `:art:` from Rhea.
- `M11` (random / :raider_skull: rollout): `:raider_skull:` from Miranda, Devon, Rhea, Tomás.
- `M17` (random / memes): `:ship_it_raider:` from Miranda, Rhea.

### 6.3 Scheduled messages (must exist at `benchmark_now`)

- Lagoon has ONE scheduled message in `#marketing`, with `post_at = benchmark_now + 23h` (i.e., Monday 09:00 Pacific), text: `"Weekly marketing standup — drop blockers below."`

No other scheduled messages exist.

### 6.4 Reminders (must exist)

- Miranda (U01MIRANDA) has a reminder: text `"Review tomb-3 crits"`, scheduled for `benchmark_now + 8h` (= 18:00 Sunday Pacific). Owned by Miranda.

### 6.5 Files (must exist)

- `F01_LVL3_CONCEPTS.zip`, uploaded by Miranda to `#design-reviews` with `M5` (approx 4.2 MB, `application/zip`).
- `F02_BUG247_LOG.txt`, uploaded by Pinkman to `#qa-bugs` with `M6` (approx 38 KB, `text/plain`).
- `F03_TRAILER_DRAFT.mp4`, uploaded by Lagoon to `#marketing` with `M15` (approx 112 MB, `video/mp4`).
- Three image files (`tomb3_angle_a.png`, `tomb3_angle_b.png`, `tomb3_angle_c.png`, each ~2 MB, `image/png`) uploaded by Miranda **alongside** `M5` in `#design-reviews`.

---

## 7. Seeded messages — canonical ts & text

Every `ts` below is expressed as a **day-offset from `benchmark_now`**. Operators should compute the real `ts` as `benchmark_now_epoch - (offset_days × 86400) + minor_seconds_offset`. Labels `M1..M20`, `P1`, `T1..T2` are grading labels only; agents must discover ts at runtime.

| Label | Channel | Author | Offset (days ago) | Text |
|---|---|---|---|---|
| `M1` | `#announcements` | Claude | 10 | "Alpha build shipping 2026-05-10. Lock your features by 2026-04-25." |
| `M1b` | `#announcements` | Claude | 40 | "Welcome Rhea to the team!" |
| `M1c` | `#announcements` | Claude | 25 | "Reminder: studio all-hands Monday 11am." |
| `M1d` | `#announcements` | Claude | 4 | "Press preview scheduled for 2026-05-03." |
| `M1e` | `#announcements` | Claude | 1 | "Reminder: code freeze discussion tomorrow in #eng-backend." |
| `P1` | `#eng-backend` | Jared | 45 | "Code freeze rules: no merges after Friday 5pm PT." (**pinned**) |
| `M2` | `#eng-backend` | Jared | 8 | "Investigating crash in level-4 tile loader. Repro on macOS 14 only." (parent of thread `T1`) |
| `M3` | `#eng-backend` | Devon | 8 (5 min after M2) | "I can repro. It's the async streamer dropping a chunk when GPU memory is tight." (reply in `T1`) |
| `M4` | `#eng-backend` | Pinkman | 8 (10 min after M2) | "Filed as BUG-247. Tagging @engineers." (reply in `T1`) |
| `M2b` | `#eng-backend` | Devon | 5 | "Shipped fix for tile loader on branch `fix/tile-loader-async`. PR #12345." |
| `M2c` | `#eng-backend` | Jared | 3 | "Reminder: no merges after 5pm Friday." |
| `M5` | `#design-reviews` | Miranda | 7 | "Tomb-level 3 concept pass — five angles attached. Looking for crits on the lighting." (3 image files + `F01_LVL3_CONCEPTS.zip`) |
| `M5b` | `#design-reviews` | Rhea | 7 (20 min after M5) | "The lighting in angle B is gorgeous. Angle E feels flat — try warming the rim." |
| `M5c` | `#design-reviews` | Claude | 6 | "Agree with Rhea — B and C are the keepers." |
| `M6` | `#qa-bugs` | Pinkman | 6 | "BUG-247: save-file corruption on macOS. Reproduces 4/10 runs. Blocker." (attached `F02_BUG247_LOG.txt`) |
| `M6b` | `#qa-bugs` | Pinkman | 13 | "BUG-246: main-menu flicker on launch (low)." |
| `M6c` | `#qa-bugs` | Tomás | 11 | "BUG-245: audio desync after cutscene (medium)." |
| `M6d` | `#qa-bugs` | Pinkman | 4 | "BUG-248: tomb-3 door collider blocks player on revisit (high)." |
| `M6e` | `#qa-bugs` | Jared | 2 | "Triaging the open BUG-### list at 2pm." |
| `M7` | `#launch-2026` | Lagoon | 5 | "Launch checklist v3 — owners: me/mkt, Miranda/brand, Jared/eng." (**pinned**) |
| `M7b` | `#launch-2026` | Lagoon | 2 | "Marketing side is 60% ready — blockers in thread below." |
| `M7c` | `#launch-2026` | Miranda | 2 (30 min after M7b) | "Brand kit finalized. Legal approved the name." |
| `M7d` | `#launch-2026` | Jared | 2 (60 min after M7b) | "Eng side has 2 open blockers: BUG-247 and the streaming cert." |
| `M8` | `#general` | Miranda | 4 | "Team Lisbon offsite: 2026-06-10 → 2026-06-14. RSVP in thread." (**pinned**, parent of thread `T2`) |
| `M9` | `#general` | Jared | 4 (10 min after M8) | "Count me in." (reply in `T2`) |
| `M10` | `#general` | Pinkman | 4 (20 min after M8) | "Can't make it — wedding that week." (reply in `T2`) |
| `M10b` | `#general` | Lagoon | 4 (40 min after M8) | "Yes! Booking flights now." (reply in `T2`) |
| `M10c` | `#general` | Claude | 60 | "Welcome to Hintas's Slack workspace." |
| `M10d` | `#general` | Claude | 14 | "FYI — alpha demo will be shared with press mid-May." |
| `M11` | `#random` | Lagoon | 3 | "New :raider_skull: emoji is live. Use responsibly." |
| `M11b` | `#random` | Lagoon | 20 | "Rec of the week: 'Annihilation' on rewatch hits different." |
| `M17` | `#random` | Devon | 2 | "Finally shipped it :ship_it_raider:" |
| `M12` | `#incidents` | ci-bot | 1.2 (= ~28.8h ago) | "🚨 Build #842 failed on `main`. See logs: https://ci.hintas.co/builds/842" |
| `M12b` | `#incidents` | ci-bot | 0.08 (= ~2h ago) | "✅ Build #843 passed on `main`." |
| `M13` | `D01_MI_JA` | Miranda | 2 | "Quick sync on boss fight pacing at 3pm?" |
| `M14` | `D01_MI_JA` | Jared | 2 (5 min after M13) | "Works. Huddle?" |
| `M13b` | `D03_MI_CL` | Miranda | 6 | "Claude — can we chat about tomb-3 pacing when you have a sec?" |
| `M13c` | `D03_MI_CL` | Claude | 6 (15 min after M13b) | "Any time — ping me." |
| `M15` | `#marketing` | Lagoon | 4 | "Trailer draft goes live Thursday. I need final copy by EOD Tuesday." (attached `F03_TRAILER_DRAFT.mp4`) |
| `M15b` | `#marketing` | Lagoon | 10 | "Press list for review — spreadsheet in thread." |
| `M16` | `G01_LEADS_MPIM` | Miranda | 9 | "Leads syncs from now on in here if we don't need Claude." |

### Threads

- `T1` (parent `M2` in `#eng-backend`): replies `M3`, `M4`.
- `T2` (parent `M8` in `#general`): replies `M9`, `M10`, `M10b`.

---

## 8. Load-bearing facts agents may rely on

1. Every human user has a profile photo and a job title set.
2. `jared@hintas.co`, `miranda@hintas.co`, `pinkman@hintas.co`, `lagoon@hintas.co` all resolve via `users.lookupByEmail`.
3. `#announcements` has admin-only posting via `admin.conversations.setConversationPrefs`. Claude (admin) can post; non-admins cannot.
4. `#old-playtest-2025` is archived — writes fail until unarchived.
5. `ember@hintas.co` resolves to a **deactivated** user (`deleted=true`); invites to any channel fail with a user-disabled-style error.
6. `ci-bot` is a bot member of `#general`, `#random`, `#eng-backend`, `#incidents`. Do not DM it; do not add humans to conversations on its behalf.
7. The agent's token is `U05CLAUDE`'s **user token** (not a bot token), granting `search.messages` access to conversations Claude is a member of.
8. **Discovery API is NOT enabled**. Claude cannot read `D01_MI_JA` (Miranda ↔ Jared DM) or `D02_PI_LA` (Pinkman ↔ Lagoon DM) — he is not a member.
9. `conversations.history` returns messages **newest-first**. Agents must reverse for "oldest-first" presentation.
10. Reaction emoji names are passed to `reactions.add`/`reactions.remove` **without colons** (e.g. `name=+1`, `name=wave`).

---

## 9. Reset discipline

Operators MUST reset the workspace back to this exact snapshot before every prompt run. Many prompts are destructive (create channels, rename, archive, delete messages, unpin, kick members, update profiles). Running prompts back-to-back without reset will invalidate the expected success criteria listed in later prompts. See `benchmark_prompts.json → setup_instructions → STEP 4`.

## 10. Naming contract for prompts

Prompts refer to people by **first name only** (Miranda, Jared, Pinkman, Lagoon, Devon, Rhea, Tomás, Ember). Agents must resolve first name → Slack user ID via `users.list`, `users.lookupByEmail`, or equivalent. Channels are referenced by their `#channel-name`; agents must resolve to channel IDs via `conversations.list` or equivalent.
