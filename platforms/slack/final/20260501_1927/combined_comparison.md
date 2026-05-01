# Combined Benchmark Comparison — Slack — 20260501_1927

**Scope:** 48 prompts × 4 stacks (baseline + 3 variants).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack` (Slack MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off` (Hintas MCP (max=5))
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off` (Hintas MCP (max=10))
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off` (Hintas MCP (max=8))

## Per-run reports

- Slack MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_205001__slack`
- Hintas MCP (max=5): [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_204604__hintas__topk10_batch-off_max5_rag-off`
- Hintas MCP (max=10): [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off`
- Hintas MCP (max=8): [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/slack/runs/20260429_230701__hintas__topk10_batch-off_max8_rag-off`

## MCP configuration

> Variant columns show the parameters each variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:----------|:--------------:|:--------------:|:--------------:|:--------------:|
| `search_top_k` | **—** | **10** | **10** | **10** |
| `search_batch_enabled` | **—** | **off** | **off** | **off** |
| `search_max_results` | **—** | **5**  ⚠ | **10**  ⚠ | **8**  ⚠ |
| `rag_enabled` | **—** | **off** | **off** | **off** |

_Parameters differing across variants: `search_max_results`._

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt verdicts

| ID | Title | Diff | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|---:|:------|:----:|:------:|:------:|:------:|:------:|
| 1 | List public channels with counts | L2 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 2 | Members of #design-reviews | L2 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 3 | Post hello in #random | L1 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 4 | Jared's profile card | L2 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 5 | Recent #announcements (oldest-first) | L2 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 7 | Update #eng-backend topic | L1 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 8 | Thumbs-up latest posted msg in #marketing | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 10 | My DND state | L1 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 11 | Find Jared by email | L2 | ◐ PARTIAL | ✓ PASS | ✗ FAIL | ✓ PASS |
| 13 | Ping QA team in #qa-bugs | L3 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 14 | Engineering team roster | L2 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 15 | DM Pinkman for a call | L2 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 17 | Schedule Monday kickoff | L2 | ✗ FAIL | ✗ FAIL | ✗ FAIL | ✗ FAIL |
| 20 | Permalink to the alpha-ship announcement | L2 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 21 | Post, then edit a typo (chat.update) | L2 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 22 | Spin up #gold-master-feedback | L4 | ✗ FAIL | ◐ PARTIAL | ✓ PASS | ✓ PASS |
| 23 | BUG-### digest in #qa-bugs | L3 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 24 | Lisbon offsite RSVP tally | L3 | ◐ PARTIAL | ◐ PARTIAL | ◐ PARTIAL | ◐ PARTIAL |
| 26 | Rename #eng-frontend → #eng-client | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 27 | Revive #old-playtest-2025 | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 28 | Leads presence + DND snapshot | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 29 | Private channels I can see | L3 | ◐ PARTIAL | ✓ PASS | ✓ PASS | ✓ PASS |
| 30 | Remove a stale reaction (reactions.remove) | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 31 | ci-bot activity in #incidents | L3 | ✓ PASS | ✓ PASS | ✓ PASS | ✓ PASS |
| 32 | #launch-2026 posting check | L3 | ✓ PASS | ✓ PASS | ✗ FAIL | ✓ PASS |
| 33 | Tomb-3 concept files | L3 | ✗ FAIL | ✗ FAIL | ✗ FAIL | ✗ FAIL |
| 34 | Leads MPIM message | L3 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 35 | Kick Rhea; re-invite Ember | L3 | ✗ FAIL | ✓ PASS | ◐ PARTIAL | ◐ PARTIAL |
| 36 | Spin up incident war room | L4 | ✗ FAIL | ✓ PASS | ◐ PARTIAL | ✓ PASS |
| 37 | DM every lead individually | L4 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 38 | BUG-247 amplification | L4 | ◐ PARTIAL | ✓ PASS | ✓ PASS | ✓ PASS |
| 39 | Low-membership audit (ephemeral) | L4 | ✗ FAIL | ✓ PASS | ✗ FAIL | ✓ PASS |
| 40 | My first post in #general | L3 | ◐ PARTIAL | ✓ PASS | ✓ PASS | ✓ PASS |
| 42 | Top 5 reacted in #announcements | L4 | ◐ PARTIAL | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 43 | QA posting leaderboard + staleness DM | L4 | ✗ FAIL | ✓ PASS | ✓ PASS | ✓ PASS |
| 44 | Self-reschedule: cancel and re-create a scheduled message | L4 | ✗ FAIL | ✓ PASS | — | ◐ PARTIAL |
| 45 | Mark all my conversations as read | L4 | ✗ FAIL | ⚠ ERROR | — | ✓ PASS |
| 46 | All image attachments in #design-reviews | L4 | ✗ FAIL | ✗ FAIL | — | ✗ FAIL |
| 47 | Leadership digest | L4 | ✓ PASS | ⚠ ERROR | — | ✓ PASS |
| 48 | DM Pinkman, respecting DND snooze | L4 | ✗ FAIL | ✓ PASS | — | ✓ PASS |
| 49 | Set, list, then delete a personal reminder | L3 | ✗ FAIL | ✓ PASS | — | ◐ PARTIAL |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | L4 | ◐ PARTIAL | ✓ PASS | — | ✓ PASS |
| 53 | Search MY DM with Jared for 'pacing' | L3 | ✓ PASS | ✓ PASS | — | ✓ PASS |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | L4 | ✓ PASS | ◐ PARTIAL | — | ✗ FAIL |
| 55 | Close out tile-loader thread | L4 | ◐ PARTIAL | ✓ PASS | — | ✓ PASS |
| 56 | DND snooze + announce + schedule lift | L4 | ◐ PARTIAL | ✓ PASS | — | ◐ PARTIAL |
| 58 | Audit ci-bot activity across channels | L4 | ✗ FAIL | ✓ PASS | — | ✗ FAIL |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | L4 | ◐ PARTIAL | ✓ PASS | — | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) | Δ Hintas MCP (max=5) vs Slack MCP | Δ Hintas MCP (max=10) vs Slack MCP | Δ Hintas MCP (max=8) vs Slack MCP |
|---:|:------|---:|---:|---:|---:|---:|---:|---:|
| 1 | List public channels with counts | 773 | 1,126 | 1,277 | 1,415 | *excl* | *excl* | *excl* |
| 2 | Members of #design-reviews | 800 | 1,343 | 718 | 1,147 | *excl* | *excl* | *excl* |
| 3 | Post hello in #random | 263 | 264 | 263 | 264 | +1 | 0 | +1 |
| 4 | Jared's profile card | 199 | 949 | 1,119 | 940 | +750 | +920 | +741 |
| 5 | Recent #announcements (oldest-first) | 521 | 2,102 | 1,608 | 1,241 | +1,581 | +1,087 | +720 |
| 7 | Update #eng-backend topic | 347 | 371 | 352 | 378 | *excl* | *excl* | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 602 | 704 | 1,700 | 869 | *excl* | *excl* | *excl* |
| 10 | My DND state | 368 | 2,897 | 4,949 | 2,387 | *excl* | *excl* | *excl* |
| 11 | Find Jared by email | 865 | 1,097 | 660 | 754 | *excl* | *excl* | *excl* |
| 13 | Ping QA team in #qa-bugs | 524 | 1,999 | 1,378 | 3,886 | +1,475 | +854 | +3,362 |
| 14 | Engineering team roster | 6,280 | 1,506 | 3,424 | 2,863 | *excl* | *excl* | *excl* |
| 15 | DM Pinkman for a call | 236 | 1,423 | 1,610 | 1,069 | *excl* | *excl* | *excl* |
| 17 | Schedule Monday kickoff | 515 | 1,055 | 1,206 | 1,485 | *excl* | *excl* | *excl* |
| 20 | Permalink to the alpha-ship announcement | 258 | 2,145 | 1,449 | 1,315 | +1,887 | +1,191 | +1,057 |
| 21 | Post, then edit a typo (chat.update) | 607 | 445 | 444 | 793 | *excl* | *excl* | *excl* |
| 22 | Spin up #gold-master-feedback | 653 | 4,842 | 3,877 | 2,718 | *excl* | *excl* | *excl* |
| 23 | BUG-### digest in #qa-bugs | 1,610 | 3,323 | 3,611 | 4,627 | +1,713 | +2,001 | +3,017 |
| 24 | Lisbon offsite RSVP tally | 782 | 3,843 | 3,696 | 2,766 | *excl* | *excl* | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 332 | 872 | 876 | 802 | *excl* | *excl* | *excl* |
| 27 | Revive #old-playtest-2025 | 842 | 1,681 | 1,628 | 1,899 | *excl* | *excl* | *excl* |
| 28 | Leads presence + DND snapshot | 1,001 | 2,192 | 1,526 | 2,620 | *excl* | *excl* | *excl* |
| 29 | Private channels I can see | 632 | 1,229 | 1,277 | 1,172 | *excl* | *excl* | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 725 | 3,804 | 1,346 | 1,375 | *excl* | *excl* | *excl* |
| 31 | ci-bot activity in #incidents | 757 | 2,566 | 2,256 | 1,196 | +1,809 | +1,499 | +439 |
| 32 | #launch-2026 posting check | 1,499 | 3,643 | 2,379 | 2,118 | +2,144 | *excl* | +619 |
| 33 | Tomb-3 concept files | 1,661 | 5,796 | 4,380 | 4,373 | *excl* | *excl* | *excl* |
| 34 | Leads MPIM message | 1,911 | 744 | 1,741 | 773 | *excl* | *excl* | *excl* |
| 35 | Kick Rhea; re-invite Ember | 746 | 3,327 | 4,806 | 1,236 | *excl* | *excl* | *excl* |
| 36 | Spin up incident war room | 9,739 | 2,638 | 3,013 | 8,785 | *excl* | *excl* | *excl* |
| 37 | DM every lead individually | 420 | 1,821 | 5,088 | 1,858 | *excl* | *excl* | *excl* |
| 38 | BUG-247 amplification | 3,135 | 2,528 | 2,125 | 2,602 | *excl* | *excl* | *excl* |
| 39 | Low-membership audit (ephemeral) | 704 | 1,280 | 3,737 | 2,468 | *excl* | *excl* | *excl* |
| 40 | My first post in #general | 802 | 2,655 | 5,194 | 2,053 | *excl* | *excl* | *excl* |
| 42 | Top 5 reacted in #announcements | 1,835 | 2,669 | 9,294 | 4,988 | *excl* | *excl* | *excl* |
| 43 | QA posting leaderboard + staleness DM | 2,007 | 3,453 | 3,333 | 5,036 | *excl* | *excl* | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 2,458 | 4,826 | — | 1,602 | *excl* | *excl* | *excl* |
| 45 | Mark all my conversations as read | 895 | 0 | — | 1,546 | *excl* | *excl* | *excl* |
| 46 | All image attachments in #design-reviews | 1,865 | 3,326 | — | 4,575 | *excl* | *excl* | *excl* |
| 47 | Leadership digest | 19,549 | 0 | — | 5,699 | *excl* | *excl* | -13,850 |
| 48 | DM Pinkman, respecting DND snooze | 803 | 1,344 | — | 1,242 | *excl* | *excl* | *excl* |
| 49 | Set, list, then delete a personal reminder | 869 | 3,452 | — | 3,059 | *excl* | *excl* | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 21,133 | 5,283 | — | 3,827 | *excl* | *excl* | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 795 | 1,891 | — | 1,965 | +1,096 | *excl* | +1,170 |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 1,236 | 3,261 | — | 3,858 | *excl* | *excl* | *excl* |
| 55 | Close out tile-loader thread | 852 | 2,180 | — | 2,507 | *excl* | *excl* | *excl* |
| 56 | DND snooze + announce + schedule lift | 2,516 | 3,989 | — | 2,241 | *excl* | *excl* | *excl* |
| 58 | Audit ci-bot activity across channels | 1,483 | 6,090 | — | 2,614 | *excl* | *excl* | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 3,793 | 5,297 | — | 3,102 | *excl* | *excl* | *excl* |

## Per-prompt wall-clock

| ID | Title | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) | Δ Hintas MCP (max=5) vs Slack MCP | Δ Hintas MCP (max=10) vs Slack MCP | Δ Hintas MCP (max=8) vs Slack MCP |
|---:|:------|---:|---:|---:|---:|---:|---:|---:|
| 1 | List public channels with counts | 19.7s | 24.9s | 38.8s | 43.3s | *excl* | *excl* | *excl* |
| 2 | Members of #design-reviews | 22.1s | 37.7s | 30.9s | 36.5s | *excl* | *excl* | *excl* |
| 3 | Post hello in #random | 12.7s | 13.1s | 14.3s | 19.6s | +0.4s | +1.7s | +6.9s |
| 4 | Jared's profile card | 10.5s | 25.1s | 30.5s | 35.0s | +14.7s | +20.1s | +24.5s |
| 5 | Recent #announcements (oldest-first) | 11.7s | 44.0s | 34.7s | 26.1s | +32.3s | +23.0s | +14.4s |
| 7 | Update #eng-backend topic | 10.7s | 18.3s | 16.6s | 17.5s | *excl* | *excl* | *excl* |
| 8 | Thumbs-up latest posted msg in #marketing | 15.3s | 21.5s | 43.4s | 30.5s | *excl* | *excl* | *excl* |
| 10 | My DND state | 13.2s | 56.7s | 88.0s | 46.8s | *excl* | *excl* | *excl* |
| 11 | Find Jared by email | 27.8s | 43.5s | 23.6s | 23.9s | *excl* | *excl* | *excl* |
| 13 | Ping QA team in #qa-bugs | 15.5s | 51.8s | 47.9s | 42.5s | +36.3s | +32.4s | +27.0s |
| 14 | Engineering team roster | 156.0s | 59.1s | 67.0s | 61.5s | *excl* | *excl* | *excl* |
| 15 | DM Pinkman for a call | 16.1s | 51.0s | 50.8s | 25.3s | *excl* | *excl* | *excl* |
| 17 | Schedule Monday kickoff | 15.1s | 32.4s | 25.6s | 42.0s | *excl* | *excl* | *excl* |
| 20 | Permalink to the alpha-ship announcement | 15.0s | 49.7s | 50.0s | 40.8s | +34.6s | +35.0s | +25.7s |
| 21 | Post, then edit a typo (chat.update) | 21.2s | 21.8s | 18.4s | 25.8s | *excl* | *excl* | *excl* |
| 22 | Spin up #gold-master-feedback | 18.7s | 99.4s | 96.7s | 58.2s | *excl* | *excl* | *excl* |
| 23 | BUG-### digest in #qa-bugs | 30.2s | 58.5s | 82.5s | 99.9s | +28.3s | +52.2s | +69.6s |
| 24 | Lisbon offsite RSVP tally | 32.0s | 89.1s | 83.1s | 59.2s | *excl* | *excl* | *excl* |
| 26 | Rename #eng-frontend → #eng-client | 11.2s | 34.7s | 33.0s | 26.1s | *excl* | *excl* | *excl* |
| 27 | Revive #old-playtest-2025 | 22.0s | 67.6s | 43.9s | 41.0s | *excl* | *excl* | *excl* |
| 28 | Leads presence + DND snapshot | 29.7s | 45.8s | 32.5s | 62.5s | *excl* | *excl* | *excl* |
| 29 | Private channels I can see | 19.3s | 36.8s | 32.8s | 29.7s | *excl* | *excl* | *excl* |
| 30 | Remove a stale reaction (reactions.remove) | 20.6s | 114.8s | 45.6s | 33.7s | *excl* | *excl* | *excl* |
| 31 | ci-bot activity in #incidents | 22.9s | 61.9s | 49.3s | 33.0s | +39.0s | +26.3s | +10.0s |
| 32 | #launch-2026 posting check | 34.8s | 75.7s | 53.4s | 44.3s | +40.9s | *excl* | +9.5s |
| 33 | Tomb-3 concept files | 42.8s | 141.2s | 108.0s | 117.9s | *excl* | *excl* | *excl* |
| 34 | Leads MPIM message | 42.4s | 19.9s | 38.0s | 28.0s | *excl* | *excl* | *excl* |
| 35 | Kick Rhea; re-invite Ember | 23.0s | 37.2s | 53.1s | 30.9s | *excl* | *excl* | *excl* |
| 36 | Spin up incident war room | 173.5s | 88.7s | 88.2s | 192.3s | *excl* | *excl* | *excl* |
| 37 | DM every lead individually | 16.8s | 44.1s | 66.4s | 47.4s | *excl* | *excl* | *excl* |
| 38 | BUG-247 amplification | 54.2s | 50.1s | 49.0s | 48.5s | *excl* | *excl* | *excl* |
| 39 | Low-membership audit (ephemeral) | 16.7s | 29.9s | 112.8s | 65.1s | *excl* | *excl* | *excl* |
| 40 | My first post in #general | 20.2s | 58.0s | 123.7s | 50.2s | *excl* | *excl* | *excl* |
| 42 | Top 5 reacted in #announcements | 32.3s | 52.5s | 86.5s | 105.7s | *excl* | *excl* | *excl* |
| 43 | QA posting leaderboard + staleness DM | 39.0s | 80.8s | 69.4s | 92.2s | *excl* | *excl* | *excl* |
| 44 | Self-reschedule: cancel and re-create a scheduled message | 43.2s | 80.5s | — | 39.2s | *excl* | *excl* | *excl* |
| 45 | Mark all my conversations as read | 19.0s | 300.0s | — | 37.0s | *excl* | *excl* | *excl* |
| 46 | All image attachments in #design-reviews | 42.6s | 74.6s | — | 91.1s | *excl* | *excl* | *excl* |
| 47 | Leadership digest | 264.1s | 300.0s | — | 108.4s | *excl* | *excl* | -155.6s |
| 48 | DM Pinkman, respecting DND snooze | 17.0s | 40.7s | — | 30.9s | *excl* | *excl* | *excl* |
| 49 | Set, list, then delete a personal reminder | 18.6s | 76.8s | — | 62.9s | *excl* | *excl* | *excl* |
| 52 | Find Pinkman's full name & channels (via fallback enumeration) | 291.0s | 80.6s | — | 68.0s | *excl* | *excl* | *excl* |
| 53 | Search MY DM with Jared for 'pacing' | 22.1s | 46.3s | — | 55.9s | +24.2s | *excl* | +33.8s |
| 54 | Alpha-ship reaction math + cross-ref (history-scoped) | 29.6s | 66.3s | — | 61.0s | *excl* | *excl* | *excl* |
| 55 | Close out tile-loader thread | 18.3s | 57.4s | — | 68.0s | *excl* | *excl* | *excl* |
| 56 | DND snooze + announce + schedule lift | 39.9s | 73.4s | — | 49.3s | *excl* | *excl* | *excl* |
| 58 | Audit ci-bot activity across channels | 41.0s | 197.4s | — | 57.2s | *excl* | *excl* | *excl* |
| 60 | Code freeze orchestration (announce + schedule + DM + topic) | 64.9s | 96.0s | — | 74.5s | *excl* | *excl* | *excl* |

## Verdict tallies

| Metric | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|---:|
| PASS | 11 | 40 | 27 | 37 |
| PARTIAL | 10 | 3 | 3 | 6 |
| FAIL | 27 | 3 | 5 | 5 |
| ERROR | 0 | 2 | 0 | 0 |
| Pass rate | 23% | 83% | 77% | 77% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|---:|
| Tools complete | 270 | 294 | 178 | 243 |
| Tools failed | 3 | 0 | 0 | 0 |
| Tools partial | 0 | 0 | 0 | 0 |
| Total | 273 | 294 | 178 | 243 |
| Tool pass rate | 99% | 100% | 100% | 100% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31` (count: 7)
- Excluded count: 41

| Metric | Slack MCP | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|---:|
| Total tokens | 4,132 | 13,348 | 11,684 | 13,469 |
| Avg tokens / prompt | 590 | 1,907 | 1,669 | 1,924 |
| Avg tokens / tool call | 243 | 334 | 377 | 408 |
| Avg peak context | 13 | 198 | 19 | 818 |
| Avg initial context | 3.00 | 3.00 | 3.00 | 3.00 |
| Avg wall-clock (s) | 16.9 | 43.5 | 44.2 | 42.4 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.
> Each variant column group uses its own pair-specific intersection, so baseline values differ across groups.

- Slack MCP ∩ Hintas MCP (max=5): n=9, IDs `3, 4, 5, 13, 20, 23, 31, 32, 53`
- Slack MCP ∩ Hintas MCP (max=10): n=7, IDs `3, 4, 5, 13, 20, 23, 31`
- Slack MCP ∩ Hintas MCP (max=8): n=10, IDs `3, 4, 5, 13, 20, 23, 31, 32, 47, 53`

| Metric | Slack MCP (Hintas MCP (max=5) pair) | Hintas MCP (max=5) | Δ (Hintas MCP (max=5) − Slack MCP) | Slack MCP (Hintas MCP (max=10) pair) | Hintas MCP (max=10) | Δ (Hintas MCP (max=10) − Slack MCP) | Slack MCP (Hintas MCP (max=8) pair) | Hintas MCP (max=8) | Δ (Hintas MCP (max=8) − Slack MCP) |
|:-------|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total tokens | 6,426 | 18,882 | +12,456 | 4,132 | 11,684 | +7,552 | 25,975 | 23,251 | -2,724 |
| Avg tokens / prompt | 714 | 2,098 | +1,384 | 590 | 1,669 | +1,079 | 2,598 | 2,325 | -272 |
| Avg tokens / tool call | 257 | 331 | +74 | 243 | 377 | +134 | 448 | 456 | +8 |
| Avg peak context | 14 | 160 | +146 | 13 | 19 | +5 | 62 | 579 | +518 |
| Avg initial context | 3.00 | 3.00 | 0.00 | 3.00 | 3.00 | 0.00 | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 19.5 | 47.3 | +27.9 | 16.9 | 44.2 | +27.2 | 43.9 | 50.5 | +6.6 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Slack MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS). Cells show the winner: `✓` = variant wins, `base` = baseline wins.

| Metric | Hintas MCP (max=5) | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|:---:|:---:|:---:|
| Accuracy | ✓ +60.4 pp | ✓ +54.2 pp | ✓ +54.2 pp |
| Speed | base +58.8% | base +61.7% | base +13.1% |
| Tokens | base +66.0% | base +64.6% | ✓ +10.5% |
| Peak context | base +91.2% | base +28.8% | base +89.4% |
| Tool reliability | ✓ | ✓ | ✓ |
| **Overall winner** | **base** | **base** | **✓** |
