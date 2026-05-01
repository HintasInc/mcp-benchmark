# Benchmark Analysis — Hintas MCP — Run 20260429_230701__hintas__topk10_batch-off_max8_rag-off

**Scope:** 48 prompts × Hintas MCP, graded against precomputed session summaries (`analysis_data.json`).

## MCP configuration

> The variant Hintas server runs with the parameters below. When comparing two Hintas runs, this is the block to scan first — these are the only knobs that change between them.

| Parameter | Value |
|:----------|:-----:|
| `search_top_k` | **10** |
| `search_batch_enabled` | **off** |
| `search_max_results` | **8** |
| `rag_enabled` | **off** |

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt results

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List public channels with counts | L2 | ✓ PASS | 43.3s | 1,415 | 5 | 0 |
| 2 | Members of #design-reviews | L2 | ✓ PASS | 36.5s | 1,147 | 4 | 0 |
| 3 | Post hello in #random | L1 | ✓ PASS | 19.6s | 264 | 2 | 0 |
| 4 | Jared's profile card | L2 | ✓ PASS | 35.0s | 940 | 5 | 0 |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | 26.1s | 1,241 | 3 | 0 |
| 7 | Update #eng-backend topic | L1 | ✓ PASS | 17.5s | 378 | 2 | 0 |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✓ PASS | 30.5s | 869 | 3 | 0 |
| 10 | My DND state | L1 | ✓ PASS | 46.8s | 2,387 | 2 | 0 |
| 11 | Find Jared by email | L2 | ✓ PASS | 23.9s | 754 | 5 | 0 |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | 42.5s | 3,886 | 6 | 0 |
| 14 | Engineering team roster | L2 | ✓ PASS | 61.5s | 2,863 | 7 | 0 |
| 15 | DM Pinkman for a call | L2 | ✓ PASS | 25.3s | 1,069 | 4 | 0 |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | 42.0s | 1,485 | 3 | 0 |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | 40.8s | 1,315 | 6 | 0 |
| 21 | Post, then edit a typo (chat.update) | L2 | ✓ PASS | 25.8s | 793 | 2 | 0 |
| 22 | Spin up #gold-master-feedback | L4 | ✓ PASS | 58.2s | 2,718 | 7 | 0 |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | 99.9s | 4,627 | 8 | 0 |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | 59.2s | 2,766 | 4 | 0 |
| 26 | Rename #eng-frontend to #eng-client | L3 | ✓ PASS | 26.1s | 802 | 4 | 0 |
| 27 | Revive #old-playtest-2025 | L3 | ✓ PASS | 41.0s | 1,899 | 8 | 0 |
| 28 | Leads presence + DND snapshot | L3 | ✓ PASS | 62.5s | 2,620 | 6 | 0 |
| 29 | Private channels I can see | L3 | ✓ PASS | 29.7s | 1,172 | 5 | 0 |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✓ PASS | 33.7s | 1,375 | 3 | 0 |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | 33.0s | 1,196 | 3 | 0 |
| 32 | #launch-2026 posting check | L3 | ✓ PASS | 44.3s | 2,118 | 5 | 0 |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | 117.9s | 4,373 | 13 | 0 |
| 34 | MPIM with Jared and Pinkman | L3 | ✓ PASS | 28.0s | 773 | 2 | 0 |
| 35 | Kick Rhea; re-invite Ember | L3 | ◐ PARTIAL | 30.9s | 1,236 | 4 | 0 |
| 36 | Spin up incident war room | L4 | ✓ PASS | 192.3s | 8,785 | 11 | 0 |
| 37 | DM every lead individually | L4 | ✓ PASS | 47.4s | 1,858 | 5 | 0 |
| 38 | BUG-247 amplification | L4 | ✓ PASS | 48.5s | 2,602 | 5 | 0 |
| 39 | Low-membership audit (ephemeral) | L4 | ✓ PASS | 65.1s | 2,468 | 11 | 0 |
| 40 | My first post in #general | L3 | ✓ PASS | 50.2s | 2,053 | 3 | 0 |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | 105.7s | 4,988 | 8 | 0 |
| 43 | QA posting leaderboard + staleness DM | L4 | ✓ PASS | 92.2s | 5,036 | 3 | 0 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ◐ PARTIAL | 39.2s | 1,602 | 2 | 0 |
| 45 | Mark all my conversations as read | L4 | ✓ PASS | 37.0s | 1,546 | 2 | 0 |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | 91.1s | 4,575 | 10 | 0 |
| 47 | Leadership digest | L4 | ✓ PASS | 108.4s | 5,699 | 6 | 0 |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✓ PASS | 30.9s | 1,242 | 3 | 0 |
| 49 | Set, list, then delete a personal reminder | L3 | ◐ PARTIAL | 62.9s | 3,059 | 4 | 0 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ✓ PASS | 68.0s | 3,827 | 10 | 0 |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | 55.9s | 1,965 | 7 | 0 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✗ FAIL | 61.0s | 3,858 | 6 | 0 |
| 55 | Close out tile-loader thread | L4 | ✓ PASS | 68.0s | 2,507 | 7 | 0 |
| 56 | Enable DND, post quiet-period notice, schedule end reminder | L3 | ◐ PARTIAL | 49.3s | 2,241 | 3 | 0 |
| 58 | Find ci-bot and post deploy notices to #incidents | L3 | ✗ FAIL | 57.2s | 2,614 | 4 | 0 |
| 60 | Four-step channel coordination: announce, snapshot topics, schedule resets, DM Jared | L5 | ✓ PASS | 74.5s | 3,102 | 2 | 0 |

## Initial vs peak context

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List public channels with counts | 3 | 18 |
| 2 | Members of #design-reviews | 3 | 15 |
| 3 | Post hello in #random | 3 | 11 |
| 4 | Jared's profile card | 3 | 18 |
| 5 | Recent #announcements (oldest-first) | 3 | 16 |
| 7 | Update #eng-backend topic | 3 | 12 |
| 8 | Thumbs-up latest posted msg in #marketing | 3 | 17 |
| 10 | My DND state | 3 | 12 |
| 11 | Find Jared by email | 3 | 21 |
| 13 | Ping QA team in #qa-bugs | 3 | 5,615 |
| 14 | Engineering team roster | 3 | 24 |
| 15 | DM Pinkman for a call | 3 | 18 |
| 17 | Schedule Monday kickoff | 3 | 17 |
| 20 | Permalink to the alpha-ship announcement | 3 | 22 |
| 21 | Post, then edit a typo (chat.update) | 3 | 14 |
| 22 | Spin up #gold-master-feedback | 3 | 24 |
| 23 | BUG-### digest in #qa-bugs | 3 | 28 |
| 24 | Lisbon offsite RSVP tally | 3 | 20 |
| 26 | Rename #eng-frontend to #eng-client | 3 | 19 |
| 27 | Revive #old-playtest-2025 | 3 | 995 |
| 28 | Leads presence + DND snapshot | 3 | 26 |
| 29 | Private channels I can see | 3 | 19 |
| 30 | Remove a stale reaction (reactions.remove) | 3 | 16 |
| 31 | ci-bot activity in #incidents | 3 | 16 |
| 32 | #launch-2026 posting check | 3 | 21 |
| 33 | Tomb-3 concept files | 3 | 42 |
| 34 | MPIM with Jared and Pinkman | 3 | 9 |
| 35 | Kick Rhea; re-invite Ember | 3 | 19 |
| 36 | Spin up incident war room | 3 | 42 |
| 37 | DM every lead individually | 3 | 20 |
| 38 | BUG-247 amplification | 3 | 18 |
| 39 | Low-membership audit (ephemeral) | 3 | 33 |
| 40 | My first post in #general | 3 | 17 |
| 42 | Top 5 reacted in #announcements | 3 | 27 |
| 43 | QA posting leaderboard + staleness DM | 3 | 16 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 3 | 14 |
| 45 | Mark all my conversations as read | 3 | 13 |
| 46 | All image attachments in #design-reviews | 3 | 33 |
| 47 | Leadership digest | 3 | 22 |
| 48 | DM Pinkman, respecting DND snooze | 3 | 16 |
| 49 | Set, list, then delete a personal reminder | 3 | 19 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 3 | 31 |
| 53 | Search MY DM with Jared for 'pacing' | 3 | 22 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 3 | 25 |
| 55 | Close out tile-loader thread | 3 | 26 |
| 56 | Enable DND, post quiet-period notice, schedule end reminder | 3 | 18 |
| 58 | Find ci-bot and post deploy notices to #incidents | 3 | 21 |
| 60 | Four-step channel coordination: announce, snapshot topics, schedule resets, DM Jared | 3 | 24 |

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 48 |
| Success rate | 77% |
| Passes | 37 |
| Partial | 6 |
| Fails | 5 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 158 |
| Avg wall-clock | 53.9s |
| Total tokens | 114,108 |
| Avg tokens/prompt | 2,377 |
| Avg tool calls | 5.06 |
| Total tool failures | 0 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 10 | 90% | 0/1/0 |
| L3 | 19 | 68% | 4/2/0 |
| L4 | 15 | 73% | 2/2/0 |
| L5 | 1 | 100% | 0/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 11 | 91% | 0/1/0 |
| search | 9 | 56% | 2/2/0 |
| write | 10 | 80% | 1/1/0 |
| workflow | 5 | 40% | 2/1/0 |
| orchestration | 11 | 91% | 1/0/0 |
| edge_case | 2 | 100% | 0/0/0 |

## Notable failures

- **#17 Schedule Monday kickoff** (L2, write) — `FAIL`: The Slack API rejected the schedule request with 'time_in_past' because the requested date (2026-04-20 09:00 PT) predates the benchmark run (2026-04-29); the scheduled message was never created. This is an environment rejection blocking the task.
- **#24 Lisbon offsite RSVP tally** (L3, search) — `PARTIAL`: Agent correctly found the thread and classified all 3 replies semantically (yes/no/yes), but could not attribute replies to distinct named users because all thread messages share the same user ID (single-token seeding); the RSVP count is correct but individual attribution is missing.
- **#33 Tomb-3 concept files** (L3, retrieval) — `FAIL`: Agent found the message (ts=1777518503.147229) but could not retrieve file metadata (name, size, mimetype) because the token lacks the files:read scope; the required output of file details was not delivered.
- **#35 Kick Rhea; re-invite Ember** (L3, write) — `PARTIAL`: Rhea was successfully kicked (conversations_kick ok:true), but the agent found no user named Ember in the workspace and did not attempt an API invite — it never received nor reported an API error conveying deactivated/disabled state as the success criteria requires.
- **#42 Top 5 reacted in #announcements** (L4, search) — `PARTIAL`: Agent correctly identified the top message (Alpha build, ts=1777518497.192279) and ranked by total reaction count, but chat_getPermalink returned invalid_auth for all messages — permalinks were not delivered as required by success criteria.
- **#44 Self-reschedule: cancel and re-create a scheduled message** (L4, orchestration) — `PARTIAL`: The rescheduled message (Q0B0BE3T6CX, '[rescheduled] Weekly marketing standup...', 2026-05-01 10:00 PDT) was successfully created, but the initial 09:00 schedule failed with time_in_past and no chat_deleteScheduledMessage call was made — the delete criterion is unmet.
- **#49 Set, list, then delete a personal reminder** (L3, workflow) — `PARTIAL`: reminders_add succeeded (id=Rm0B0PGSLNA1, time=1777582800, text='Check trailer copy'), but reminders_list returned empty immediately after creation — the mid-run list criterion was not met. The delete call also returned not_found due to the same ephemeral state issue.
- **#56 Enable DND, post quiet-period notice, schedule end reminder** (L3, workflow) — `PARTIAL`: DND snooze enabled (ok:true, snooze_remaining=82800s) and quiet-period notice posted to #general (ok:true, ts=1777523033.883699) with exact required text. Scheduled end reminder failed with time_in_past (timestamp 1776701100 = 2026-04-20 09:05 PDT is prior to run date 2026-04-29), so the third criterion was not met.
