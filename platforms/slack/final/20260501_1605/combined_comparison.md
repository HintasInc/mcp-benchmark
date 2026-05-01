# Combined Benchmark Comparison — Slack — 20260501_1605

**Scope:** 48 prompts × 2 stacks (baseline + 1 variant).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack` (Slack MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off` (Hintas MCP)

## Per-run reports

- Slack MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack`
- Hintas MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off`

## MCP configuration

> Each variant block shows the parameters the variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Slack MCP | Hintas MCP |
|:----------|:--------------:|:--------------:|
| `search_top_k` | **—** | **10** |
| `search_batch_enabled` | **—** | **off** |
| `search_max_results` | **—** | **8** |
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
| 11 | Find Jared by email | L2 | ◐ PARTIAL | ✓ PASS |
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
| 32 | #launch-2026 posting check | L3 | ✓ PASS | ✓ PASS |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | ✗ FAIL |
| 34 | Leads MPIM message | L3 | ✗ FAIL | ✓ PASS |
| 35 | Kick Rhea; re-invite Ember | L3 | ✗ FAIL | ◐ PARTIAL |
| 36 | Spin up incident war room | L4 | ✗ FAIL | ✓ PASS |
| 37 | DM every lead individually | L4 | ✗ FAIL | ✓ PASS |
| 38 | BUG-247 amplification | L4 | ◐ PARTIAL | ✓ PASS |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | ✓ PASS |
| 40 | My first post in #general | L3 | ◐ PARTIAL | ✓ PASS |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | ◐ PARTIAL |
| 43 | QA posting leaderboard + staleness DM | L4 | ✗ FAIL | ✓ PASS |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✗ FAIL | ◐ PARTIAL |
| 45 | Mark all my conversations as read | L4 | ✗ FAIL | ✓ PASS |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | ✗ FAIL |
| 47 | Leadership digest | L4 | ✓ PASS | ✓ PASS |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✗ FAIL | ✓ PASS |
| 49 | Set, list, then delete a personal reminder | L3 | ✗ FAIL | ◐ PARTIAL |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ◐ PARTIAL | ✓ PASS |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | ✓ PASS |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✓ PASS | ✗ FAIL |
| 55 | Close out tile-loader thread | L4 | ◐ PARTIAL | ✓ PASS |
| 56 | DND snooze + announce + schedule lift | L4 | ◐ PARTIAL | ◐ PARTIAL |
| 58 | Audit ci-bot activity across channels | L4 | ✗ FAIL | ✗ FAIL |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | L4 | ◐ PARTIAL | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 773 | 1,415 | *excl* |
| 2 | Members of #design-reviews | 800 | 1,147 | *excl* |
| 3 | Post hello in #random | 263 | 264 | +1 |
| 4 | Jared's profile card | 199 | 940 | +741 |
| 5 | Recent #announcements (oldest-first) | 521 | 1,241 | +720 |
| 7 | Update #eng-backend topic | 347 | 378 | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 602 | 869 | *excl* |
| 10 | My DND state | 368 | 2,387 | *excl* |
| 11 | Find Jared by email | 865 | 754 | *excl* |
| 13 | Ping QA team in #qa-bugs | 524 | 3,886 | +3,362 |
| 14 | Engineering team roster | 6,280 | 2,863 | *excl* |
| 15 | DM Pinkman for a call | 236 | 1,069 | *excl* |
| 17 | Schedule Monday kickoff | 515 | 1,485 | *excl* |
| 20 | Permalink to the alpha-ship announcement | 258 | 1,315 | +1,057 |
| 21 | Post, then edit a typo (chat.update) | 607 | 793 | *excl* |
| 22 | Spin up #gold-master-feedback | 653 | 2,718 | *excl* |
| 23 | BUG-### digest in #qa-bugs | 1,610 | 4,627 | +3,017 |
| 24 | Lisbon offsite RSVP tally | 782 | 2,766 | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 332 | 802 | *excl* |
| 27 | Revive #old-playtest-2025 | 842 | 1,899 | *excl* |
| 28 | Leads presence + DND snapshot | 1,001 | 2,620 | *excl* |
| 29 | Private channels I can see | 632 | 1,172 | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 725 | 1,375 | *excl* |
| 31 | ci-bot activity in #incidents | 757 | 1,196 | +439 |
| 32 | #launch-2026 posting check | 1,499 | 2,118 | +619 |
| 33 | Tomb-3 concept files | 1,661 | 4,373 | *excl* |
| 34 | Leads MPIM message | 1,911 | 773 | *excl* |
| 35 | Kick Rhea; re-invite Ember | 746 | 1,236 | *excl* |
| 36 | Spin up incident war room | 9,739 | 8,785 | *excl* |
| 37 | DM every lead individually | 420 | 1,858 | *excl* |
| 38 | BUG-247 amplification | 3,135 | 2,602 | *excl* |
| 39 | Low-membership audit (ephemeral) | 704 | 2,468 | *excl* |
| 40 | My first post in #general | 802 | 2,053 | *excl* |
| 42 | Top 5 reacted in #announcements | 1,835 | 4,988 | *excl* |
| 43 | QA posting leaderboard + staleness DM | 2,007 | 5,036 | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 2,458 | 1,602 | *excl* |
| 45 | Mark all my conversations as read | 895 | 1,546 | *excl* |
| 46 | All image attachments in #design-reviews | 1,865 | 4,575 | *excl* |
| 47 | Leadership digest | 19,549 | 5,699 | -13,850 |
| 48 | DM Pinkman, respecting DND snooze | 803 | 1,242 | *excl* |
| 49 | Set, list, then delete a personal reminder | 869 | 3,059 | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 21,133 | 3,827 | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 795 | 1,965 | +1,170 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 1,236 | 3,858 | *excl* |
| 55 | Close out tile-loader thread | 852 | 2,507 | *excl* |
| 56 | DND snooze + announce + schedule lift | 2,516 | 2,241 | *excl* |
| 58 | Audit ci-bot activity across channels | 1,483 | 2,614 | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 3,793 | 3,102 | *excl* |

## Per-prompt wall-clock

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 19.7s | 43.3s | *excl* |
| 2 | Members of #design-reviews | 22.1s | 36.5s | *excl* |
| 3 | Post hello in #random | 12.7s | 19.6s | +6.9s |
| 4 | Jared's profile card | 10.5s | 35.0s | +24.5s |
| 5 | Recent #announcements (oldest-first) | 11.7s | 26.1s | +14.4s |
| 7 | Update #eng-backend topic | 10.7s | 17.5s | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 15.3s | 30.5s | *excl* |
| 10 | My DND state | 13.2s | 46.8s | *excl* |
| 11 | Find Jared by email | 27.8s | 23.9s | *excl* |
| 13 | Ping QA team in #qa-bugs | 15.5s | 42.5s | +27.0s |
| 14 | Engineering team roster | 156.0s | 61.5s | *excl* |
| 15 | DM Pinkman for a call | 16.1s | 25.3s | *excl* |
| 17 | Schedule Monday kickoff | 15.1s | 42.0s | *excl* |
| 20 | Permalink to the alpha-ship announcement | 15.0s | 40.8s | +25.7s |
| 21 | Post, then edit a typo (chat.update) | 21.2s | 25.8s | *excl* |
| 22 | Spin up #gold-master-feedback | 18.7s | 58.2s | *excl* |
| 23 | BUG-### digest in #qa-bugs | 30.2s | 99.9s | +69.6s |
| 24 | Lisbon offsite RSVP tally | 32.0s | 59.2s | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 11.2s | 26.1s | *excl* |
| 27 | Revive #old-playtest-2025 | 22.0s | 41.0s | *excl* |
| 28 | Leads presence + DND snapshot | 29.7s | 62.5s | *excl* |
| 29 | Private channels I can see | 19.3s | 29.7s | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 20.6s | 33.7s | *excl* |
| 31 | ci-bot activity in #incidents | 22.9s | 33.0s | +10.0s |
| 32 | #launch-2026 posting check | 34.8s | 44.3s | +9.5s |
| 33 | Tomb-3 concept files | 42.8s | 117.9s | *excl* |
| 34 | Leads MPIM message | 42.4s | 28.0s | *excl* |
| 35 | Kick Rhea; re-invite Ember | 23.0s | 30.9s | *excl* |
| 36 | Spin up incident war room | 173.5s | 192.3s | *excl* |
| 37 | DM every lead individually | 16.8s | 47.4s | *excl* |
| 38 | BUG-247 amplification | 54.2s | 48.5s | *excl* |
| 39 | Low-membership audit (ephemeral) | 16.7s | 65.1s | *excl* |
| 40 | My first post in #general | 20.2s | 50.2s | *excl* |
| 42 | Top 5 reacted in #announcements | 32.3s | 105.7s | *excl* |
| 43 | QA posting leaderboard + staleness DM | 39.0s | 92.2s | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 43.2s | 39.2s | *excl* |
| 45 | Mark all my conversations as read | 19.0s | 37.0s | *excl* |
| 46 | All image attachments in #design-reviews | 42.6s | 91.1s | *excl* |
| 47 | Leadership digest | 264.1s | 108.4s | -155.6s |
| 48 | DM Pinkman, respecting DND snooze | 17.0s | 30.9s | *excl* |
| 49 | Set, list, then delete a personal reminder | 18.6s | 62.9s | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 291.0s | 68.0s | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 22.1s | 55.9s | +33.8s |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 29.6s | 61.0s | *excl* |
| 55 | Close out tile-loader thread | 18.3s | 68.0s | *excl* |
| 56 | DND snooze + announce + schedule lift | 39.9s | 49.3s | *excl* |
| 58 | Audit ci-bot activity across channels | 41.0s | 57.2s | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 64.9s | 74.5s | *excl* |

## Verdict tallies

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| PASS | 11 | 37 |
| PARTIAL | 10 | 6 |
| FAIL | 27 | 5 |
| ERROR | 0 | 0 |
| Pass rate | 23% | 77% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Tools complete | 270 | 243 |
| Tools failed | 3 | 0 |
| Tools partial | 0 | 0 |
| Total | 273 | 243 |
| Tool pass rate | 99% | 100% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31, 32, 47, 53` (count: 10)
- Excluded count: 38

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Total tokens | 25,975 | 23,251 |
| Avg tokens / prompt | 2,598 | 2,325 |
| Avg tokens / tool call | 448 | 456 |
| Avg peak context | 62 | 579 |
| Avg initial context | 3.00 | 3.00 |
| Avg wall-clock (s) | 43.9 | 50.5 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.

### Slack MCP vs Hintas MCP

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31, 32, 47, 53` (count: 10)

| Metric | Slack MCP | Hintas MCP | Δ (Hintas MCP − Slack MCP) |
|:-------|---:|---:|---:|
| Total tokens | 25,975 | 23,251 | -2,724 |
| Avg tokens / prompt | 2,598 | 2,325 | -272 |
| Avg tokens / tool call | 448 | 456 | +8 |
| Avg peak context | 62 | 579 | +518 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 43.9 | 50.5 | +6.6 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Slack MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS).

| Metric | Slack MCP | Hintas MCP |
|:-------|:---:|:---:|
| Accuracy | — | +54.2 pp |
| Speed | +13.1% | — |
| Tokens | — | +10.5% |
| Peak context | +89.4% | — |
| Tool reliability | — | ✓ |
| **Overall winner** | — | **✓** |
