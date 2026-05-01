# Combined Benchmark Comparison — Slack — 20260501_1912

**Scope:** 48 prompts × 2 stacks (baseline + 1 variant).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack` (Slack MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off` (Hintas MCP)

## Per-run reports

- Slack MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack`
- Hintas MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off`

## MCP configuration

> Each variant block shows the parameters the variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Slack MCP | Hintas MCP |
|:----------|:--------------:|:--------------:|
| `search_top_k` | **—** | **10** |
| `search_batch_enabled` | **—** | **off** |
| `search_max_results` | **—** | **5** |
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
| 22 | Spin up #gold-master-feedback | L4 | ✗ FAIL | ◐ PARTIAL |
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
| 35 | Kick Rhea; re-invite Ember | L3 | ✗ FAIL | ✓ PASS |
| 36 | Spin up incident war room | L4 | ✗ FAIL | ✓ PASS |
| 37 | DM every lead individually | L4 | ✗ FAIL | ✓ PASS |
| 38 | BUG-247 amplification | L4 | ◐ PARTIAL | ✓ PASS |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | ✓ PASS |
| 40 | My first post in #general | L3 | ◐ PARTIAL | ✓ PASS |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | ✓ PASS |
| 43 | QA posting leaderboard + staleness DM | L4 | ✗ FAIL | ✓ PASS |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✗ FAIL | ✓ PASS |
| 45 | Mark all my conversations as read | L4 | ✗ FAIL | ⚠ ERROR |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | ✗ FAIL |
| 47 | Leadership digest | L4 | ✓ PASS | ⚠ ERROR |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✗ FAIL | ✓ PASS |
| 49 | Set, list, then delete a personal reminder | L3 | ✗ FAIL | ✓ PASS |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ◐ PARTIAL | ✓ PASS |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | ✓ PASS |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✓ PASS | ◐ PARTIAL |
| 55 | Close out tile-loader thread | L4 | ◐ PARTIAL | ✓ PASS |
| 56 | DND snooze + announce + schedule lift | L4 | ◐ PARTIAL | ✓ PASS |
| 58 | Audit ci-bot activity across channels | L4 | ✗ FAIL | ✓ PASS |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | L4 | ◐ PARTIAL | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 773 | 1,126 | *excl* |
| 2 | Members of #design-reviews | 800 | 1,343 | *excl* |
| 3 | Post hello in #random | 263 | 264 | +1 |
| 4 | Jared's profile card | 199 | 949 | +750 |
| 5 | Recent #announcements (oldest-first) | 521 | 2,102 | +1,581 |
| 7 | Update #eng-backend topic | 347 | 371 | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 602 | 704 | *excl* |
| 10 | My DND state | 368 | 2,897 | *excl* |
| 11 | Find Jared by email | 865 | 1,097 | *excl* |
| 13 | Ping QA team in #qa-bugs | 524 | 1,999 | +1,475 |
| 14 | Engineering team roster | 6,280 | 1,506 | *excl* |
| 15 | DM Pinkman for a call | 236 | 1,423 | *excl* |
| 17 | Schedule Monday kickoff | 515 | 1,055 | *excl* |
| 20 | Permalink to the alpha-ship announcement | 258 | 2,145 | +1,887 |
| 21 | Post, then edit a typo (chat.update) | 607 | 445 | *excl* |
| 22 | Spin up #gold-master-feedback | 653 | 4,842 | *excl* |
| 23 | BUG-### digest in #qa-bugs | 1,610 | 3,323 | +1,713 |
| 24 | Lisbon offsite RSVP tally | 782 | 3,843 | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 332 | 872 | *excl* |
| 27 | Revive #old-playtest-2025 | 842 | 1,681 | *excl* |
| 28 | Leads presence + DND snapshot | 1,001 | 2,192 | *excl* |
| 29 | Private channels I can see | 632 | 1,229 | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 725 | 3,804 | *excl* |
| 31 | ci-bot activity in #incidents | 757 | 2,566 | +1,809 |
| 32 | #launch-2026 posting check | 1,499 | 3,643 | +2,144 |
| 33 | Tomb-3 concept files | 1,661 | 5,796 | *excl* |
| 34 | Leads MPIM message | 1,911 | 744 | *excl* |
| 35 | Kick Rhea; re-invite Ember | 746 | 3,327 | *excl* |
| 36 | Spin up incident war room | 9,739 | 2,638 | *excl* |
| 37 | DM every lead individually | 420 | 1,821 | *excl* |
| 38 | BUG-247 amplification | 3,135 | 2,528 | *excl* |
| 39 | Low-membership audit (ephemeral) | 704 | 1,280 | *excl* |
| 40 | My first post in #general | 802 | 2,655 | *excl* |
| 42 | Top 5 reacted in #announcements | 1,835 | 2,669 | *excl* |
| 43 | QA posting leaderboard + staleness DM | 2,007 | 3,453 | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 2,458 | 4,826 | *excl* |
| 45 | Mark all my conversations as read | 895 | 0 | *excl* |
| 46 | All image attachments in #design-reviews | 1,865 | 3,326 | *excl* |
| 47 | Leadership digest | 19,549 | 0 | *excl* |
| 48 | DM Pinkman, respecting DND snooze | 803 | 1,344 | *excl* |
| 49 | Set, list, then delete a personal reminder | 869 | 3,452 | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 21,133 | 5,283 | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 795 | 1,891 | +1,096 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 1,236 | 3,261 | *excl* |
| 55 | Close out tile-loader thread | 852 | 2,180 | *excl* |
| 56 | DND snooze + announce + schedule lift | 2,516 | 3,989 | *excl* |
| 58 | Audit ci-bot activity across channels | 1,483 | 6,090 | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 3,793 | 5,297 | *excl* |

## Per-prompt wall-clock

| ID | Title | Slack MCP | Hintas MCP | Δ Hintas MCP vs Slack MCP |
|---:|:------|---:|---:|---:|
| 1 | List public channels with counts | 19.7s | 24.9s | *excl* |
| 2 | Members of #design-reviews | 22.1s | 37.7s | *excl* |
| 3 | Post hello in #random | 12.7s | 13.1s | +0.4s |
| 4 | Jared's profile card | 10.5s | 25.1s | +14.7s |
| 5 | Recent #announcements (oldest-first) | 11.7s | 44.0s | +32.3s |
| 7 | Update #eng-backend topic | 10.7s | 18.3s | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 15.3s | 21.5s | *excl* |
| 10 | My DND state | 13.2s | 56.7s | *excl* |
| 11 | Find Jared by email | 27.8s | 43.5s | *excl* |
| 13 | Ping QA team in #qa-bugs | 15.5s | 51.8s | +36.3s |
| 14 | Engineering team roster | 156.0s | 59.1s | *excl* |
| 15 | DM Pinkman for a call | 16.1s | 51.0s | *excl* |
| 17 | Schedule Monday kickoff | 15.1s | 32.4s | *excl* |
| 20 | Permalink to the alpha-ship announcement | 15.0s | 49.7s | +34.6s |
| 21 | Post, then edit a typo (chat.update) | 21.2s | 21.8s | *excl* |
| 22 | Spin up #gold-master-feedback | 18.7s | 99.4s | *excl* |
| 23 | BUG-### digest in #qa-bugs | 30.2s | 58.5s | +28.3s |
| 24 | Lisbon offsite RSVP tally | 32.0s | 89.1s | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 11.2s | 34.7s | *excl* |
| 27 | Revive #old-playtest-2025 | 22.0s | 67.6s | *excl* |
| 28 | Leads presence + DND snapshot | 29.7s | 45.8s | *excl* |
| 29 | Private channels I can see | 19.3s | 36.8s | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 20.6s | 114.8s | *excl* |
| 31 | ci-bot activity in #incidents | 22.9s | 61.9s | +39.0s |
| 32 | #launch-2026 posting check | 34.8s | 75.7s | +40.9s |
| 33 | Tomb-3 concept files | 42.8s | 141.2s | *excl* |
| 34 | Leads MPIM message | 42.4s | 19.9s | *excl* |
| 35 | Kick Rhea; re-invite Ember | 23.0s | 37.2s | *excl* |
| 36 | Spin up incident war room | 173.5s | 88.7s | *excl* |
| 37 | DM every lead individually | 16.8s | 44.1s | *excl* |
| 38 | BUG-247 amplification | 54.2s | 50.1s | *excl* |
| 39 | Low-membership audit (ephemeral) | 16.7s | 29.9s | *excl* |
| 40 | My first post in #general | 20.2s | 58.0s | *excl* |
| 42 | Top 5 reacted in #announcements | 32.3s | 52.5s | *excl* |
| 43 | QA posting leaderboard + staleness DM | 39.0s | 80.8s | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 43.2s | 80.5s | *excl* |
| 45 | Mark all my conversations as read | 19.0s | 300.0s | *excl* |
| 46 | All image attachments in #design-reviews | 42.6s | 74.6s | *excl* |
| 47 | Leadership digest | 264.1s | 300.0s | *excl* |
| 48 | DM Pinkman, respecting DND snooze | 17.0s | 40.7s | *excl* |
| 49 | Set, list, then delete a personal reminder | 18.6s | 76.8s | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 291.0s | 80.6s | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 22.1s | 46.3s | +24.2s |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 29.6s | 66.3s | *excl* |
| 55 | Close out tile-loader thread | 18.3s | 57.4s | *excl* |
| 56 | DND snooze + announce + schedule lift | 39.9s | 73.4s | *excl* |
| 58 | Audit ci-bot activity across channels | 41.0s | 197.4s | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 64.9s | 96.0s | *excl* |

## Verdict tallies

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| PASS | 11 | 40 |
| PARTIAL | 10 | 3 |
| FAIL | 27 | 3 |
| ERROR | 0 | 2 |
| Pass rate | 23% | 83% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Tools complete | 270 | 294 |
| Tools failed | 3 | 0 |
| Tools partial | 0 | 0 |
| Total | 273 | 294 |
| Tool pass rate | 99% | 100% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31, 32, 53` (count: 9)
- Excluded count: 39

| Metric | Slack MCP | Hintas MCP |
|:-------|---:|---:|
| Total tokens | 6,426 | 18,882 |
| Avg tokens / prompt | 714 | 2,098 |
| Avg tokens / tool call | 257 | 331 |
| Avg peak context | 14 | 160 |
| Avg initial context | 3.00 | 3.00 |
| Avg wall-clock (s) | 19.5 | 47.3 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.

### Slack MCP vs Hintas MCP

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31, 32, 53` (count: 9)

| Metric | Slack MCP | Hintas MCP | Δ (Hintas MCP − Slack MCP) |
|:-------|---:|---:|---:|
| Total tokens | 6,426 | 18,882 | +12,456 |
| Avg tokens / prompt | 714 | 2,098 | +1,384 |
| Avg tokens / tool call | 257 | 331 | +74 |
| Avg peak context | 14 | 160 | +146 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 19.5 | 47.3 | +27.9 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Slack MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS).

| Metric | Slack MCP | Hintas MCP |
|:-------|:---:|:---:|
| Accuracy | — | +60.4 pp |
| Speed | +58.8% | — |
| Tokens | +66.0% | — |
| Peak context | +91.2% | — |
| Tool reliability | — | ✓ |
| **Overall winner** | **✓** | — |
