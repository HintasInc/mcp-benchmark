# Benchmark Analysis — Slack MCP — Run 20260429_205001__slack

**Scope:** 48 prompts × Slack MCP, graded against precomputed session summaries (`analysis_data.json`).

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt results

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List public channels with counts | L2 | ✗ FAIL | 19.7s | 773 | 1 | 0 |
| 2 | Members of #design-reviews | L2 | ✗ FAIL | 22.1s | 800 | 4 | 0 |
| 3 | Post hello in #random | L1 | ✓ PASS | 12.7s | 263 | 2 | 0 |
| 4 | Jared's profile card | L2 | ✓ PASS | 10.5s | 199 | 1 | 0 |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | 11.7s | 521 | 2 | 0 |
| 7 | Update #eng-backend topic | L1 | ✗ FAIL | 10.7s | 347 | 0 | 0 |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✗ FAIL | 15.3s | 602 | 2 | 0 |
| 10 | My DND state | L1 | ✗ FAIL | 13.2s | 368 | 1 | 0 |
| 11 | Find Jared by email | L2 | ◐ PARTIAL | 27.8s | 865 | 4 | 0 |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | 15.5s | 524 | 4 | 0 |
| 14 | Engineering team roster | L2 | ✗ FAIL | 156.0s | 6,280 | 27 | 0 |
| 15 | DM Pinkman for a call | L2 | ✗ FAIL | 16.1s | 236 | 1 | 0 |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | 15.1s | 515 | 0 | 0 |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | 15.0s | 258 | 1 | 0 |
| 21 | Post, then edit a typo (chat.update) | L2 | ✗ FAIL | 21.2s | 607 | 0 | 0 |
| 22 | Spin up #gold-master-feedback | L4 | ✗ FAIL | 18.7s | 653 | 0 | 0 |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | 30.2s | 1,610 | 3 | 0 |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | 32.0s | 782 | 2 | 0 |
| 26 | Rename #eng-frontend → #eng-client | L3 | ✗ FAIL | 11.2s | 332 | 0 | 0 |
| 27 | Revive #old-playtest-2025 | L3 | ✗ FAIL | 22.0s | 842 | 3 | 0 |
| 28 | Leads presence + DND snapshot | L3 | ✗ FAIL | 29.7s | 1,001 | 6 | 0 |
| 29 | Private channels I can see | L3 | ◐ PARTIAL | 19.3s | 632 | 1 | 0 |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✗ FAIL | 20.6s | 725 | 1 | 0 |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | 22.9s | 757 | 4 | 0 |
| 32 | #launch-2026 posting check | L3 | ✓ PASS | 34.8s | 1,499 | 5 | 0 |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | 42.8s | 1,661 | 8 | 0 |
| 34 | Leads MPIM message | L3 | ✗ FAIL | 42.4s | 1,911 | 7 | 2 |
| 35 | Kick Rhea; re-invite Ember | L3 | ✗ FAIL | 23.0s | 746 | 0 | 0 |
| 36 | Spin up incident war room | L4 | ✗ FAIL | 173.5s | 9,739 | 46 | 0 |
| 37 | DM every lead individually | L4 | ✗ FAIL | 16.8s | 420 | 3 | 0 |
| 38 | BUG-247 amplification | L4 | ◐ PARTIAL | 54.2s | 3,135 | 7 | 0 |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | 16.7s | 704 | 0 | 0 |
| 40 | My first post in #general | L3 | ◐ PARTIAL | 20.2s | 802 | 2 | 0 |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | 32.3s | 1,835 | 4 | 0 |
| 43 | QA posting leaderboard + staleness DM | L4 | ✗ FAIL | 39.0s | 2,007 | 3 | 0 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✗ FAIL | 43.2s | 2,458 | 1 | 0 |
| 45 | Mark all my conversations as read | L4 | ✗ FAIL | 19.0s | 895 | 0 | 0 |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | 42.6s | 1,865 | 8 | 0 |
| 47 | Leadership digest | L4 | ✓ PASS | 264.1s | 19,549 | 33 | 0 |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✗ FAIL | 17.0s | 803 | 2 | 0 |
| 49 | Set, list, then delete a personal reminder | L3 | ✗ FAIL | 18.6s | 869 | 0 | 0 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ◐ PARTIAL | 291.0s | 21,133 | 41 | 0 |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | 22.1s | 795 | 3 | 0 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✓ PASS | 29.6s | 1,236 | 5 | 0 |
| 55 | Close out tile-loader thread | L4 | ◐ PARTIAL | 18.3s | 852 | 3 | 0 |
| 56 | DND snooze + announce + schedule lift | L4 | ◐ PARTIAL | 39.9s | 2,516 | 3 | 1 |
| 58 | Audit ci-bot activity across channels | L4 | ✗ FAIL | 41.0s | 1,483 | 11 | 0 |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | L4 | ◐ PARTIAL | 64.9s | 3,793 | 8 | 0 |

## Initial vs peak context

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List public channels with counts | 3 | 11 |
| 2 | Members of #design-reviews | 3 | 16 |
| 3 | Post hello in #random | 3 | 11 |
| 4 | Jared's profile card | 3 | 10 |
| 5 | Recent #announcements (oldest-first) | 3 | 11 |
| 7 | Update #eng-backend topic | 3 | 6 |
| 8 | Thumbs-up latest posted msg in #marketing | 3 | 12 |
| 10 | My DND state | 3 | 10 |
| 11 | Find Jared by email | 3 | 17 |
| 13 | Ping QA team in #qa-bugs | 3 | 18 |
| 14 | Engineering team roster | 3 | 722 |
| 15 | DM Pinkman for a call | 3 | 10 |
| 17 | Schedule Monday kickoff | 3 | 6 |
| 20 | Permalink to the alpha-ship announcement | 3 | 10 |
| 21 | Post, then edit a typo (chat.update) | 3 | 6 |
| 22 | Spin up #gold-master-feedback | 3 | 6 |
| 23 | BUG-### digest in #qa-bugs | 3 | 17 |
| 24 | Lisbon offsite RSVP tally | 3 | 13 |
| 26 | Rename #eng-frontend → #eng-client | 3 | 6 |
| 27 | Revive #old-playtest-2025 | 3 | 17 |
| 28 | Leads presence + DND snapshot | 3 | 21 |
| 29 | Private channels I can see | 3 | 11 |
| 30 | Remove a stale reaction (reactions.remove) | 3 | 11 |
| 31 | ci-bot activity in #incidents | 3 | 17 |
| 32 | #launch-2026 posting check | 3 | 20 |
| 33 | Tomb-3 concept files | 3 | 23 |
| 34 | Leads MPIM message | 3 | 26 |
| 35 | Kick Rhea; re-invite Ember | 3 | 6 |
| 36 | Spin up incident war room | 3 | 1,057 |
| 37 | DM every lead individually | 3 | 16 |
| 38 | BUG-247 amplification | 3 | 441 |
| 39 | Low-membership audit (ephemeral) | 3 | 6 |
| 40 | My first post in #general | 3 | 12 |
| 42 | Top 5 reacted in #announcements | 3 | 16 |
| 43 | QA posting leaderboard + staleness DM | 3 | 15 |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 3 | 10 |
| 45 | Mark all my conversations as read | 3 | 6 |
| 46 | All image attachments in #design-reviews | 3 | 24 |
| 47 | Leadership digest | 3 | 489 |
| 48 | DM Pinkman, respecting DND snooze | 3 | 13 |
| 49 | Set, list, then delete a personal reminder | 3 | 6 |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 3 | 11,072 |
| 53 | Search MY DM with Jared for 'pacing' | 3 | 13 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 3 | 19 |
| 55 | Close out tile-loader thread | 3 | 15 |
| 56 | DND snooze + announce + schedule lift | 3 | 14 |
| 58 | Audit ci-bot activity across channels | 3 | 26 |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 3 | 29 |

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 48 |
| Success rate | 23% |
| Passes | 11 |
| Partial | 10 |
| Fails | 27 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 299 |
| Avg wall-clock | 41.6s |
| Total tokens | 103,198 |
| Avg tokens/prompt | 2,150 |
| Avg tool calls | 5.69 |
| Total tool failures | 3 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 33% | 0/2/0 |
| L2 | 10 | 30% | 1/6/0 |
| L3 | 17 | 29% | 3/9/0 |
| L4 | 18 | 11% | 6/10/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 11 | 27% | 2/6/0 |
| search | 10 | 40% | 4/2/0 |
| write | 9 | 22% | 0/7/0 |
| workflow | 3 | 0% | 0/3/0 |
| orchestration | 11 | 9% | 3/7/0 |
| edge_case | 4 | 25% | 1/2/0 |

## Notable failures

- **#1 List public channels with counts** (L2, retrieval) — `FAIL`: Intent not achieved. The prompt explicitly requires member count per channel, but slack_search_channels does not return num_members; the result shows '—' for every row. This is a required-output gap / capability gap: the MCP does not expose a method that returns member counts alongside channel listings.
- **#2 Members of #design-reviews** (L2, retrieval) — `FAIL`: Intent not achieved. The Slack MCP exposes no conversations.members-equivalent tool; the agent searched message history and found only Miranda Okonkwo as a poster, explicitly noting 'other members may exist who haven't posted'. This is a capability gap — the full channel roster cannot be recovered from message history alone.
- **#7 Update #eng-backend topic** (L1, write) — `FAIL`: Intent not achieved. The Slack MCP exposes no conversations.setTopic-equivalent tool; agent confirmed this in its thinking block and returned instructions for manual steps instead of completing the task. This is a capability gap.
- **#8 Thumbs-up latest posted msg in #marketing** (L3, write) — `FAIL`: Intent not achieved. Agent correctly identified the most recently posted message ('Trailer draft goes live Thursday...', ts=1777510269.918759) via slack_read_channel, but reported 'none of the Slack tools I have access to support reactions' — a capability gap that blocked completion.
- **#22 Spin up #gold-master-feedback** (L4, orchestration) — `FAIL`: Intent not achieved. All three core operations — channel creation, topic setting, and user invitation — are blocked by capability gaps; the MCP exposes none of conversations.create, conversations.setTopic, or conversations.invite. Agent correctly enumerated what it could and couldn't do without fabricating progress.
- **#24 Lisbon offsite RSVP tally** (L3, search) — `PARTIAL`: Partially achieved. Agent correctly located the message (ts=1777510261.892909), read its thread, and semantically classified the three replies as 2 yes ('Count me in.', 'Yes! Booking flights now.') and 1 no ('Can’t make it — wedding that week.'). However, the prompt asks 'who RSVP’d yes/no' — all replies surface as Miranda Okonkwo (single-token workspace seeding), so individual attribution to Jared/Pinkman/Lagoon could not be provided, a required-output gap driven by workspace state.
- **#26 Rename #eng-frontend → #eng-client** (L3, workflow) — `FAIL`: Intent not achieved. The MCP exposes no conversations.rename-equivalent tool; agent confirmed this and offered only manual instructions. Neither the rename nor the follow-up message was posted — capability gap.
- **#27 Revive #old-playtest-2025** (L3, workflow) — `FAIL`: Intent not achieved. Agent found the archived channel (C0AV0TZSB2L) and both users (Pinkman U0AU47YJWEA, Tomas U0AV0HQ44BS), but the MCP exposes no conversations.unarchive or conversations.invite tools — capability gaps blocked all three required actions (unarchive, post, invite).
