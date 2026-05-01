# Benchmark Analysis — Hintas MCP — Run 20260429_204604__hintas__topk10_batch-off_max5_rag-off

**Scope:** 48 prompts × Hintas MCP, graded against precomputed session summaries (`analysis_data.json`).

## MCP configuration

> The variant Hintas server runs with the parameters below. When comparing two Hintas runs, this is the block to scan first — these are the only knobs that change between them.

| Parameter | Value |
|:----------|:-----:|
| `search_top_k` | **10** |
| `search_batch_enabled` | **off** |
| `search_max_results` | **5** |
| `rag_enabled` | **off** |

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt results

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List public channels with counts | L2 | ✓ PASS | 24.9s | 1,126 | 3 | 0 |
| 2 | Members of #design-reviews | L2 | ✓ PASS | 37.7s | 1,343 | 6 | 0 |
| 3 | Post hello in #random | L1 | ✓ PASS | 13.1s | 264 | 2 | 0 |
| 4 | Jared's profile card | L2 | ✓ PASS | 25.1s | 949 | 4 | 0 |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | 44.0s | 2,102 | 4 | 0 |
| 7 | Update #eng-backend topic | L1 | ✓ PASS | 18.3s | 371 | 2 | 0 |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✓ PASS | 21.5s | 704 | 3 | 0 |
| 10 | My DND state | L1 | ✓ PASS | 56.7s | 2,897 | 2 | 0 |
| 11 | Find Jared by email | L2 | ✓ PASS | 43.5s | 1,097 | 6 | 0 |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | 51.8s | 1,999 | 7 | 0 |
| 14 | Engineering team roster | L2 | ✓ PASS | 59.1s | 1,506 | 6 | 0 |
| 15 | DM Pinkman for a call | L2 | ✓ PASS | 51.0s | 1,423 | 8 | 0 |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | 32.4s | 1,055 | 2 | 0 |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | 49.7s | 2,145 | 7 | 0 |
| 21 | Post, then edit a typo (chat.update) | L2 | ✓ PASS | 21.8s | 445 | 3 | 0 |
| 22 | Spin up #gold-master-feedback | L4 | ◐ PARTIAL | 99.4s | 4,842 | 19 | 0 |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | 58.5s | 3,323 | 6 | 0 |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | 89.1s | 3,843 | 11 | 0 |
| 26 | Rename #eng-frontend → #eng-client | L3 | ✓ PASS | 34.7s | 872 | 5 | 0 |
| 27 | Revive #old-playtest-2025 | L3 | ✓ PASS | 67.6s | 1,681 | 9 | 0 |
| 28 | Leads presence + DND snapshot | L3 | ✓ PASS | 45.8s | 2,192 | 5 | 0 |
| 29 | Private channels I can see | L3 | ✓ PASS | 36.8s | 1,229 | 4 | 0 |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✓ PASS | 114.8s | 3,804 | 11 | 0 |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | 61.9s | 2,566 | 10 | 0 |
| 32 | #launch-2026 posting check | L3 | ✓ PASS | 75.7s | 3,643 | 11 | 0 |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | 141.2s | 5,796 | 16 | 0 |
| 34 | Leads MPIM message | L3 | ✓ PASS | 19.9s | 744 | 2 | 0 |
| 35 | Kick Rhea; re-invite Ember | L3 | ✓ PASS | 37.2s | 3,327 | 6 | 0 |
| 36 | Spin up incident war room | L4 | ✓ PASS | 88.7s | 2,638 | 7 | 0 |
| 37 | DM every lead individually | L4 | ✓ PASS | 44.1s | 1,821 | 4 | 0 |
| 38 | BUG-247 amplification | L4 | ✓ PASS | 50.1s | 2,528 | 4 | 0 |
| 39 | Low-membership audit (ephemeral) | L4 | ✓ PASS | 29.9s | 1,280 | 5 | 0 |
| 40 | My first post in #general | L3 | ✓ PASS | 58.0s | 2,655 | 7 | 0 |
| 42 | Top 5 reacted in #announcements | L4 | ✓ PASS | 52.5s | 2,669 | 4 | 0 |
| 43 | QA posting leaderboard + staleness DM | L4 | ✓ PASS | 80.8s | 3,453 | 4 | 0 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✓ PASS | 80.5s | 4,826 | 4 | 0 |
| 45 | Mark all my conversations as read | L4 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | 74.6s | 3,326 | 7 | 0 |
| 47 | Leadership digest | L4 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✓ PASS | 40.7s | 1,344 | 4 | 0 |
| 49 | Set, list, then delete a personal reminder | L3 | ✓ PASS | 76.8s | 3,452 | 6 | 0 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ✓ PASS | 80.6s | 5,283 | 14 | 0 |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | 46.3s | 1,891 | 6 | 0 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ◐ PARTIAL | 66.3s | 3,261 | 7 | 0 |
| 55 | Close out tile-loader thread | L4 | ✓ PASS | 57.4s | 2,180 | 8 | 0 |
| 56 | Quiet-until-Monday self-DND + announce + schedule lift | L5 | ✓ PASS | 73.4s | 3,989 | 4 | 0 |
| 58 | ci-bot silence audit across channels | L5 | ✓ PASS | 197.4s | 6,090 | 12 | 0 |
| 60 | End-to-end code-freeze orchestration | L5 | ✓ PASS | 96.0s | 5,297 | 7 | 0 |

## Initial vs peak context

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List public channels with counts | 3 | 15 |
| 2 | Members of #design-reviews | 3 | 15 |
| 3 | Post hello in #random | 3 | 11 |
| 4 | Jared's profile card | 3 | 17 |
| 5 | Recent #announcements (oldest-first) | 3 | 19 |
| 7 | Update #eng-backend topic | 3 | 12 |
| 8 | Thumbs-up latest posted msg in #marketing | 3 | 15 |
| 10 | My DND state | 3 | 12 |
| 11 | Find Jared by email | 3 | 23 |
| 13 | Ping QA team in #qa-bugs | 3 | 1,255 |
| 14 | Engineering team roster | 3 | 20 |
| 15 | DM Pinkman for a call | 3 | 26 |
| 17 | Schedule Monday kickoff | 3 | 14 |
| 20 | Permalink to the alpha-ship announcement | 3 | 27 |
| 21 | Post, then edit a typo (chat.update) | 3 | 15 |
| 22 | Spin up #gold-master-feedback | 3 | 1,258 |
| 23 | BUG-### digest in #qa-bugs | 3 | 23 |
| 24 | Lisbon offsite RSVP tally | 3 | 35 |
| 26 | Rename #eng-frontend → #eng-client | 3 | 18 |
| 27 | Revive #old-playtest-2025 | 3 | 29 |
| 28 | Leads presence + DND snapshot | 3 | 749 |
| 29 | Private channels I can see | 3 | 17 |
| 30 | Remove a stale reaction (reactions.remove) | 3 | 30 |
| 31 | ci-bot activity in #incidents | 3 | 33 |
| 32 | #launch-2026 posting check | 3 | 35 |
| 33 | Tomb-3 concept files | 3 | 44 |
| 34 | Leads MPIM message | 3 | 12 |
| 35 | Kick Rhea; re-invite Ember | 3 | 4,312 |
| 36 | Spin up incident war room | 3 | 24 |
| 37 | DM every lead individually | 3 | 19 |
| 38 | BUG-247 amplification | 3 | 18 |
| 39 | Low-membership audit (ephemeral) | 3 | 18 |
| 40 | My first post in #general | 3 | 24 |
| 42 | Top 5 reacted in #announcements | 3 | 20 |
| 43 | QA posting leaderboard + staleness DM | 3 | 18 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 3 | 19 |
| 45 | Mark all my conversations as read | 0 | 0 |
| 46 | All image attachments in #design-reviews | 3 | 28 |
| 47 | Leadership digest | 0 | 0 |
| 48 | DM Pinkman, respecting DND snooze | 3 | 17 |
| 49 | Set, list, then delete a personal reminder | 3 | 25 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 3 | 39 |
| 53 | Search MY DM with Jared for 'pacing' | 3 | 17 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 3 | 24 |
| 55 | Close out tile-loader thread | 3 | 31 |
| 56 | Quiet-until-Monday self-DND + announce + schedule lift | 3 | 19 |
| 58 | ci-bot silence audit across channels | 3 | 34 |
| 60 | End-to-end code-freeze orchestration | 3 | 20 |

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 48 |
| Success rate | 83% |
| Passes | 40 |
| Partial | 3 |
| Fails | 3 |
| Errors | 2 |
| Avg initial context | 3 |
| Avg peak context | 177 |
| Avg wall-clock | 69.3s |
| Total tokens | 115,271 |
| Avg tokens/prompt | 2,401 |
| Avg tool calls | 6.12 |
| Total tool failures | 0 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 10 | 90% | 0/1/0 |
| L3 | 17 | 88% | 1/1/0 |
| L4 | 15 | 67% | 2/1/2 |
| L5 | 3 | 100% | 0/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 11 | 91% | 0/1/0 |
| search | 9 | 67% | 2/1/0 |
| write | 9 | 89% | 0/1/0 |
| workflow | 3 | 100% | 0/0/0 |
| orchestration | 13 | 77% | 1/0/2 |
| edge_case | 3 | 100% | 0/0/0 |

## Notable failures

- **#17 Schedule Monday kickoff** (L2, write) — `FAIL`: Slack API rejected the request with time_in_past error. The benchmark anchor is 2026-04-19 but the run occurred 2026-04-29; 'next Monday' (2026-04-20) was already 9 days in the past. No scheduled message was created — capability gap due to temporal mismatch between anchor and run date.
- **#22 Spin up #gold-master-feedback** (L4, orchestration) — `PARTIAL`: Channel #gold-master-feedback already existed in archived state; agent unarchived it rather than creating a new channel. Topic, invites (Jared, Pinkman, Lagoon), and welcome message were all completed correctly. The 'create new channel' aspect of the prompt intent is not satisfied — the existing channel was repurposed instead.
- **#24 Lisbon offsite RSVP tally** (L3, search) — `PARTIAL`: Agent found all 3 thread replies under the Lisbon offsite post but all share user ID U0AU46LC6F8 (Miranda) — a demo workspace seeding limitation. Agent semantically inferred 2 yes / 1 no from message text but could not produce a multi-person attribution breakdown. Intent partially achieved: tally count is correct but per-person attribution is impossible via the API.
- **#33 Tomb-3 concept files** (L3, retrieval) — `FAIL`: Agent found the message referencing 'Tomb-level 3 concept pass' in #design-reviews but the Slack API returned no file attachment metadata. A global files_list scan across the workspace also returned zero files. The demo workspace has no stored file metadata — required output cannot be produced.
- **#45 Mark all my conversations as read** (L4, orchestration) — `ERROR`: Timed out after 300s with no tool calls completed. Infrastructure timeout before any work could begin.
- **#46 All image attachments in #design-reviews** (L4, search) — `FAIL`: Agent exhaustively searched #design-reviews history and ran a workspace-wide files_list; no file attachment metadata exists in the demo workspace. The channel has 3 messages but zero files surfaced by the API. Required output (image attachment list) cannot be produced.
- **#47 Leadership digest** (L4, orchestration) — `ERROR`: Timed out after 300s with no tool calls completed. Infrastructure timeout before any work could begin.
- **#54 Alpha-ship reaction math + cross-ref (history-scoped)** (L4, search) — `PARTIAL`: Agent found the alpha-ship message and reported reaction total as 2 (live workspace count) vs benchmark-seeded expectation of 6 — workspace drift. The cross-reference channel count returned 0 vs expected 1 due to a time-window filter that excluded the seeded message. Reaction summary is present but counts diverge from seeded state; cross-ref miss is a filtering issue rather than pure drift.
