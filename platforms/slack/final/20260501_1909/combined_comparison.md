# Combined Benchmark Comparison — Slack — 20260501_1909

**Scope:** 48 prompts × 2 stacks (baseline + 1 variant).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack` (Slack MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off` (Hintas MCP)

## Per-run reports

- Slack MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack`
- Hintas MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off`

## MCP configuration

> Each variant block shows the parameters the variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Slack MCP | Hintas MCP |
|:----------|:--------------:|:--------------:|
| `search_top_k` | **—** | **10** |
| `search_batch_enabled` | **—** | **off** |
| `search_max_results` | **—** | **10** |
| `rag_enabled` | **—** | **off** |

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt verdicts

| ID | Title | Diff | Slack MCP | Hintas MCP |
|---:|:------|:----:|:------:|:------:|
| 1 | List public channels with counts | L2 | ✗ FAIL | ✓ PASS |
| 2 | Members of #design-reviews | L2 | ✗ FAIL | ✓ PASS |
| 3 | Post hello in #random | L1 | ✓ PASS | ✓ PASS |
| 4 | Jared's profile card | L2 | ✓ PASS | ✓ PASS |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | ✓ PASS |
| 7 | Update #eng-backend topic | L1 | ✗ FAIL | ✓ PASS |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✗ FAIL | ✓ PASS |
| 10 | My DND state | L1 | ✗ FAIL | ✓ PASS |
| 11 | Find Jared by email | L2 | ◐ PARTIAL | ✗ FAIL |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | ✓ PASS |
| 14 | Engineering team roster | L2 | ✗ FAIL | ✓ PASS |
| 15 | DM Pinkman for a call | L2 | ✗ FAIL | ✓ PASS |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | ✗ FAIL |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | ✓ PASS |
| 21 | Post, then edit a typo (chat.update) | L2 | ✗ FAIL | ✓ PASS |
| 22 | Spin up #gold-master-feedback | L4 | ✗ FAIL | ✓ PASS |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | ✓ PASS |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | ◐ PARTIAL |
| 26 | Rename #eng-frontend → #eng-client | L3 | ✗ FAIL | ✓ PASS |
| 27 | Revive #old-playtest-2025 | L3 | ✗ FAIL | ✓ PASS |
| 28 | Leads presence + DND snapshot | L3 | ✗ FAIL | ✓ PASS |
| 29 | Private channels I can see | L3 | ◐ PARTIAL | ✓ PASS |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✗ FAIL | ✓ PASS |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | ✓ PASS |
| 32 | #launch-2026 posting check | L3 | ✓ PASS | ✗ FAIL |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | ✗ FAIL |
| 34 | Leads MPIM message | L3 | ✗ FAIL | ✓ PASS |
| 35 | Kick Rhea; re-invite Ember | L3 | ✗ FAIL | ◐ PARTIAL |
| 36 | Spin up incident war room | L4 | ✗ FAIL | ◐ PARTIAL |
| 37 | DM every lead individually | L4 | ✗ FAIL | ✓ PASS |
| 38 | BUG-247 amplification | L4 | ◐ PARTIAL | ✓ PASS |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | ✗ FAIL |
| 40 | My first post in #general | L3 | ◐ PARTIAL | ✓ PASS |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | ✓ PASS |
| 43 | QA posting leaderboard + staleness DM | L4 | ✗ FAIL | ✓ PASS |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✗ FAIL | — |
| 45 | Mark all my conversations as read | L4 | ✗ FAIL | — |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | — |
| 47 | Leadership digest | L4 | ✓ PASS | — |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✗ FAIL | — |
| 49 | Set, list, then delete a personal reminder | L3 | ✗ FAIL | — |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ◐ PARTIAL | — |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | — |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✓ PASS | — |
| 55 | Close out tile-loader thread | L4 | ◐ PARTIAL | — |
| 56 | DND snooze + announce + schedule lift | L4 | ◐ PARTIAL | — |
| 58 | Audit ci-bot activity across channels | L4 | ✗ FAIL | — |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | L4 | ◐ PARTIAL | — |

## Per-prompt total tokens

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 773 | 1,277 | *excl* |
| 2 | Members of #design-reviews | 800 | 718 | *excl* |
| 3 | Post hello in #random | 263 | 263 | 0 |
| 4 | Jared's profile card | 199 | 1,119 | +920 |
| 5 | Recent #announcements (oldest-first) | 521 | 1,608 | +1,087 |
| 7 | Update #eng-backend topic | 347 | 352 | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 602 | 1,700 | *excl* |
| 10 | My DND state | 368 | 4,949 | *excl* |
| 11 | Find Jared by email | 865 | 660 | *excl* |
| 13 | Ping QA team in #qa-bugs | 524 | 1,378 | +854 |
| 14 | Engineering team roster | 6,280 | 3,424 | *excl* |
| 15 | DM Pinkman for a call | 236 | 1,610 | *excl* |
| 17 | Schedule Monday kickoff | 515 | 1,206 | *excl* |
| 20 | Permalink to the alpha-ship announcement | 258 | 1,449 | +1,191 |
| 21 | Post, then edit a typo (chat.update) | 607 | 444 | *excl* |
| 22 | Spin up #gold-master-feedback | 653 | 3,877 | *excl* |
| 23 | BUG-### digest in #qa-bugs | 1,610 | 3,611 | +2,001 |
| 24 | Lisbon offsite RSVP tally | 782 | 3,696 | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 332 | 876 | *excl* |
| 27 | Revive #old-playtest-2025 | 842 | 1,628 | *excl* |
| 28 | Leads presence + DND snapshot | 1,001 | 1,526 | *excl* |
| 29 | Private channels I can see | 632 | 1,277 | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 725 | 1,346 | *excl* |
| 31 | ci-bot activity in #incidents | 757 | 2,256 | +1,499 |
| 32 | #launch-2026 posting check | 1,499 | 2,379 | *excl* |
| 33 | Tomb-3 concept files | 1,661 | 4,380 | *excl* |
| 34 | Leads MPIM message | 1,911 | 1,741 | *excl* |
| 35 | Kick Rhea; re-invite Ember | 746 | 4,806 | *excl* |
| 36 | Spin up incident war room | 9,739 | 3,013 | *excl* |
| 37 | DM every lead individually | 420 | 5,088 | *excl* |
| 38 | BUG-247 amplification | 3,135 | 2,125 | *excl* |
| 39 | Low-membership audit (ephemeral) | 704 | 3,737 | *excl* |
| 40 | My first post in #general | 802 | 5,194 | *excl* |
| 42 | Top 5 reacted in #announcements | 1,835 | 9,294 | *excl* |
| 43 | QA posting leaderboard + staleness DM | 2,007 | 3,333 | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 2,458 | — | *excl* |
| 45 | Mark all my conversations as read | 895 | — | *excl* |
| 46 | All image attachments in #design-reviews | 1,865 | — | *excl* |
| 47 | Leadership digest | 19,549 | — | *excl* |
| 48 | DM Pinkman, respecting DND snooze | 803 | — | *excl* |
| 49 | Set, list, then delete a personal reminder | 869 | — | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 21,133 | — | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 795 | — | *excl* |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 1,236 | — | *excl* |
| 55 | Close out tile-loader thread | 852 | — | *excl* |
| 56 | DND snooze + announce + schedule lift | 2,516 | — | *excl* |
| 58 | Audit ci-bot activity across channels | 1,483 | — | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 3,793 | — | *excl* |

## Per-prompt wall-clock

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 19.7s | 38.8s | *excl* |
| 2 | Members of #design-reviews | 22.1s | 30.9s | *excl* |
| 3 | Post hello in #random | 12.7s | 14.3s | +1.7s |
| 4 | Jared's profile card | 10.5s | 30.5s | +20.1s |
| 5 | Recent #announcements (oldest-first) | 11.7s | 34.7s | +23.0s |
| 7 | Update #eng-backend topic | 10.7s | 16.6s | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 15.3s | 43.4s | *excl* |
| 10 | My DND state | 13.2s | 88.0s | *excl* |
| 11 | Find Jared by email | 27.8s | 23.6s | *excl* |
| 13 | Ping QA team in #qa-bugs | 15.5s | 47.9s | +32.4s |
| 14 | Engineering team roster | 156.0s | 67.0s | *excl* |
| 15 | DM Pinkman for a call | 16.1s | 50.8s | *excl* |
| 17 | Schedule Monday kickoff | 15.1s | 25.6s | *excl* |
| 20 | Permalink to the alpha-ship announcement | 15.0s | 50.0s | +35.0s |
| 21 | Post, then edit a typo (chat.update) | 21.2s | 18.4s | *excl* |
| 22 | Spin up #gold-master-feedback | 18.7s | 96.7s | *excl* |
| 23 | BUG-### digest in #qa-bugs | 30.2s | 82.5s | +52.2s |
| 24 | Lisbon offsite RSVP tally | 32.0s | 83.1s | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 11.2s | 33.0s | *excl* |
| 27 | Revive #old-playtest-2025 | 22.0s | 43.9s | *excl* |
| 28 | Leads presence + DND snapshot | 29.7s | 32.5s | *excl* |
| 29 | Private channels I can see | 19.3s | 32.8s | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 20.6s | 45.6s | *excl* |
| 31 | ci-bot activity in #incidents | 22.9s | 49.3s | +26.3s |
| 32 | #launch-2026 posting check | 34.8s | 53.4s | *excl* |
| 33 | Tomb-3 concept files | 42.8s | 108.0s | *excl* |
| 34 | Leads MPIM message | 42.4s | 38.0s | *excl* |
| 35 | Kick Rhea; re-invite Ember | 23.0s | 53.1s | *excl* |
| 36 | Spin up incident war room | 173.5s | 88.2s | *excl* |
| 37 | DM every lead individually | 16.8s | 66.4s | *excl* |
| 38 | BUG-247 amplification | 54.2s | 49.0s | *excl* |
| 39 | Low-membership audit (ephemeral) | 16.7s | 112.8s | *excl* |
| 40 | My first post in #general | 20.2s | 123.7s | *excl* |
| 42 | Top 5 reacted in #announcements | 32.3s | 86.5s | *excl* |
| 43 | QA posting leaderboard + staleness DM | 39.0s | 69.4s | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 43.2s | — | *excl* |
| 45 | Mark all my conversations as read | 19.0s | — | *excl* |
| 46 | All image attachments in #design-reviews | 42.6s | — | *excl* |
| 47 | Leadership digest | 264.1s | — | *excl* |
| 48 | DM Pinkman, respecting DND snooze | 17.0s | — | *excl* |
| 49 | Set, list, then delete a personal reminder | 18.6s | — | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 291.0s | — | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 22.1s | — | *excl* |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 29.6s | — | *excl* |
| 55 | Close out tile-loader thread | 18.3s | — | *excl* |
| 56 | DND snooze + announce + schedule lift | 39.9s | — | *excl* |
| 58 | Audit ci-bot activity across channels | 41.0s | — | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 64.9s | — | *excl* |

## Verdict tallies

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| PASS | 11 | 27 |
| PARTIAL | 10 | 3 |
| FAIL | 27 | 5 |
| ERROR | 0 | 0 |
| Pass rate | 23% | 77% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Tools complete | 270 | 178 |
| Tools failed | 3 | 0 |
| Tools partial | 0 | 0 |
| Total | 273 | 178 |
| Tool pass rate | 99% | 100% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31` (count: 7)
- Excluded count: 41

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Total tokens | 4,132 | 11,684 |
| Avg tokens / prompt | 590 | 1,669 |
| Avg tokens / tool call | 243 | 377 |
| Avg peak context | 13 | 19 |
| Avg initial context | 3.00 | 3.00 |
| Avg wall-clock (s) | 16.9 | 44.2 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.

### Slack MCP vs Hintas MCP

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31` (count: 7)

| Metric | Slack MCP | Hintas MCP | Δ (Hintas MCP − Slack MCP) |
|:-------|---:|---:|---:|
| Total tokens | 4,132 | 11,684 | +7,552 |
| Avg tokens / prompt | 590 | 1,669 | +1,079 |
| Avg tokens / tool call | 243 | 377 | +134 |
| Avg peak context | 13 | 19 | +5 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 16.9 | 44.2 | +27.2 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Slack MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS).

| Metric | Slack MCP | Hintas MCP |
|:-------|:---:|:---:|
| Accuracy | — | +54.2 pp |
| Speed | +61.7% | — |
| Tokens | +64.6% | — |
| Peak context | +28.8% | — |
| Tool reliability | — | ✓ |
| **Overall winner** | **✓** | — |
