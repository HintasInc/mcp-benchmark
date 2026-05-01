# Benchmark Analysis — Hintas MCP — Run 20260430_100018__hintas__topk10_batch-off_max10_rag-off

**Scope:** 35 prompts × Hintas MCP, graded against precomputed session summaries (`analysis_data.json`).

## MCP configuration

> The variant Hintas server runs with the parameters below. When comparing two Hintas runs, this is the block to scan first — these are the only knobs that change between them.

| Parameter | Value |
|:----------|:-----:|
| `search_top_k` | **10** |
| `search_batch_enabled` | **off** |
| `search_max_results` | **10** |
| `rag_enabled` | **off** |

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt results

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List public channels with counts | L2 | ✓ PASS | 38.8s | 1,277 | 4 | 0 |
| 2 | Members of #design-reviews | L2 | ✓ PASS | 30.9s | 718 | 3 | 0 |
| 3 | Post hello in #random | L1 | ✓ PASS | 14.3s | 263 | 2 | 0 |
| 4 | Jared's profile card | L2 | ✓ PASS | 30.5s | 1,119 | 6 | 0 |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | 34.7s | 1,608 | 3 | 0 |
| 7 | Update #eng-backend topic | L1 | ✓ PASS | 16.6s | 352 | 2 | 0 |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✓ PASS | 43.4s | 1,700 | 5 | 0 |
| 10 | My DND state | L1 | ✓ PASS | 88.0s | 4,949 | 3 | 0 |
| 11 | Find Jared by email | L2 | ✗ FAIL | 23.6s | 660 | 4 | 0 |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | 47.9s | 1,378 | 5 | 0 |
| 14 | Engineering team roster | L2 | ✓ PASS | 67.0s | 3,424 | 8 | 0 |
| 15 | DM Pinkman for a call | L2 | ✓ PASS | 50.8s | 1,610 | 8 | 0 |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | 25.6s | 1,206 | 2 | 0 |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | 50.0s | 1,449 | 7 | 0 |
| 21 | Post, then edit a typo (chat.update) | L2 | ✓ PASS | 18.4s | 444 | 3 | 0 |
| 22 | Spin up #gold-master-feedback | L4 | ✓ PASS | 96.7s | 3,877 | 12 | 0 |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | 82.5s | 3,611 | 5 | 0 |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | 83.1s | 3,696 | 6 | 0 |
| 26 | Rename #eng-frontend → #eng-client | L3 | ✓ PASS | 33.0s | 876 | 3 | 0 |
| 27 | Revive #old-playtest-2025 | L3 | ✓ PASS | 43.9s | 1,628 | 6 | 0 |
| 28 | Leads presence + DND snapshot | L3 | ✓ PASS | 32.5s | 1,526 | 4 | 0 |
| 29 | Private channels I can see | L3 | ✓ PASS | 32.8s | 1,277 | 4 | 0 |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✓ PASS | 45.6s | 1,346 | 3 | 0 |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | 49.3s | 2,256 | 3 | 0 |
| 32 | #launch-2026 posting check | L3 | ✗ FAIL | 53.4s | 2,379 | 5 | 0 |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | 108.0s | 4,380 | 11 | 0 |
| 34 | Leads MPIM message | L3 | ✓ PASS | 38.0s | 1,741 | 4 | 0 |
| 35 | Kick Rhea; re-invite Ember | L3 | ◐ PARTIAL | 53.1s | 4,806 | 6 | 0 |
| 36 | Spin up incident war room | L4 | ◐ PARTIAL | 88.2s | 3,013 | 6 | 0 |
| 37 | DM every lead individually | L4 | ✓ PASS | 66.4s | 5,088 | 5 | 0 |
| 38 | BUG-247 amplification | L4 | ✓ PASS | 49.0s | 2,125 | 3 | 0 |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | 112.8s | 3,737 | 7 | 0 |
| 40 | My first post in #general | L3 | ✓ PASS | 123.7s | 5,194 | 10 | 0 |
| 42 | Top 5 reacted in #announcements | L4 | ✓ PASS | 86.5s | 9,294 | 7 | 0 |
| 43 | QA posting leaderboard + staleness DM | L4 | ✓ PASS | 69.4s | 3,333 | 3 | 0 |

## Initial vs peak context

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List public channels with counts | 3 | 17 |
| 2 | Members of #design-reviews | 3 | 12 |
| 3 | Post hello in #random | 3 | 11 |
| 4 | Jared's profile card | 3 | 21 |
| 5 | Recent #announcements (oldest-first) | 3 | 17 |
| 7 | Update #eng-backend topic | 3 | 12 |
| 8 | Thumbs-up latest posted msg in #marketing | 3 | 21 |
| 10 | My DND state | 3 | 13 |
| 11 | Find Jared by email | 3 | 19 |
| 13 | Ping QA team in #qa-bugs | 3 | 21 |
| 14 | Engineering team roster | 3 | 29 |
| 15 | DM Pinkman for a call | 3 | 28 |
| 17 | Schedule Monday kickoff | 3 | 14 |
| 20 | Permalink to the alpha-ship announcement | 3 | 23 |
| 21 | Post, then edit a typo (chat.update) | 3 | 15 |
| 22 | Spin up #gold-master-feedback | 3 | 35 |
| 23 | BUG-### digest in #qa-bugs | 3 | 22 |
| 24 | Lisbon offsite RSVP tally | 3 | 24 |
| 26 | Rename #eng-frontend → #eng-client | 3 | 16 |
| 27 | Revive #old-playtest-2025 | 3 | 24 |
| 28 | Leads presence + DND snapshot | 3 | 18 |
| 29 | Private channels I can see | 3 | 18 |
| 30 | Remove a stale reaction (reactions.remove) | 3 | 16 |
| 31 | ci-bot activity in #incidents | 3 | 17 |
| 32 | #launch-2026 posting check | 3 | 21 |
| 33 | Tomb-3 concept files | 3 | 41 |
| 34 | Leads MPIM message | 3 | 18 |
| 35 | Kick Rhea; re-invite Ember | 3 | 6,393 |
| 36 | Spin up incident war room | 3 | 24 |
| 37 | DM every lead individually | 3 | 9,436 |
| 38 | BUG-247 amplification | 3 | 16 |
| 39 | Low-membership audit (ephemeral) | 3 | 28 |
| 40 | My first post in #general | 3 | 36 |
| 42 | Top 5 reacted in #announcements | 3 | 16,605 |
| 43 | QA posting leaderboard + staleness DM | 3 | 17 |

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 35 |
| Success rate | 77% |
| Passes | 27 |
| Partial | 3 |
| Fails | 5 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 946 |
| Avg wall-clock | 55.1s |
| Total tokens | 87,340 |
| Avg tokens/prompt | 2,495 |
| Avg tool calls | 5.09 |
| Total tool failures | 0 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 10 | 80% | 0/2/0 |
| L3 | 15 | 73% | 2/2/0 |
| L4 | 7 | 71% | 1/1/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 11 | 82% | 0/2/0 |
| search | 5 | 60% | 1/1/0 |
| write | 9 | 89% | 0/1/0 |
| workflow | 2 | 100% | 0/0/0 |
| orchestration | 6 | 67% | 1/1/0 |
| edge_case | 2 | 50% | 1/0/0 |

## Notable failures

- **#11 Find Jared by email** (L2, retrieval) — `FAIL`: Agent searched using jared@hintas.co rather than the prompt-supplied email prtmasapkota+jared@gmail.com; the wrong lookup email caused the user lookup to return an incorrect or null result.
- **#17 Schedule Monday kickoff** (L2, write) — `FAIL`: chat.scheduleMessage returned time_in_past because the target Monday (2026-04-20) had already passed by the run date (2026-04-30); the agent did not recover by scheduling a future Monday.
- **#24 Lisbon offsite RSVP tally** (L3, search) — `PARTIAL`: Agent tallied RSVP reactions on the Lisbon offsite message but could not produce per-user attribution because single-token seeding surfaces all reactions under U0AU46LC6F8 (miranda), making individual identity resolution impossible.
- **#32 #launch-2026 posting check** (L3, search) — `FAIL`: Agent called conversations_list without specifying types=private_channel, so #launch-2026 (a private channel) was excluded from the results and the agent incorrectly reported it as non-existent or inaccessible.
- **#33 Tomb-3 concept files** (L3, retrieval) — `FAIL`: The bot token lacks the files:read scope, so files_list calls on #design-reviews returned no results; agent exhausted all 11 tool calls without recovering the Tomb-3 concept files.
- **#35 Kick Rhea; re-invite Ember** (L3, edge_case) — `PARTIAL`: Agent successfully kicked Rhea from the channel, but Ember does not appear in users_list (deactivated users are not surfaced), so the re-invite step was silently skipped without a user_disabled error.
- **#36 Spin up incident war room** (L4, orchestration) — `PARTIAL`: Agent created the incident channel as incident-2026-04-30 (using the run date) rather than incident-2026-04-19 (the benchmark anchor date); remaining setup steps (topic, members, kickoff message) were completed correctly.
- **#39 Low-membership audit (ephemeral)** (L4, orchestration) — `FAIL`: Agent attempted chat_postEphemeral but the call failed because the target user is not a member of the channel the bot posted to; the ephemeral delivery requirement was never satisfied.
