# Combined Benchmark Comparison — Notion — 20260501_2334

**Scope:** 56 prompts × 2 stacks (baseline + 1 variant).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion` (Notion MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off` (Hintas MCP)

## Per-run reports

- Notion MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion`
- Hintas MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off`

## MCP configuration

> Variant columns show the parameters each variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Notion MCP | Hintas MCP |
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

| ID | Title | Diff | Notion MCP | Hintas MCP |
|---:|:------|:----:|:------:|:------:|
| 1 | List active workspace users | L1 | ✓ PASS | ✓ PASS |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | ✓ PASS |
| 4 | Retrieve the Bugs database schema | L2 | ✓ PASS | ✓ PASS |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | ✓ PASS |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ✓ PASS | ✓ PASS |
| 7 | Paginated children of Team Directory | L2 | ✗ FAIL | ✓ PASS |
| 8 | List comments on BUG-247 | L2 | ✓ PASS | ✓ PASS |
| 9 | Resolve a relation property | L3 | ✓ PASS | ✓ PASS |
| 10 | Read to_do checked states | L2 | ✓ PASS | ✓ PASS |
| 12 | List databases shared to the integration | L2 | ✗ FAIL | ✓ PASS |
| 13 | Search by title — BUG-247 | L2 | ✓ PASS | ✓ PASS |
| 14 | Search filtered to databases | L2 | ✓ PASS | ✓ PASS |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | ✓ PASS |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | ✓ PASS |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | ✓ PASS |
| 18 | High-severity macOS bugs | L3 | ✓ PASS | ✓ PASS |
| 19 | Paginated full-Tasks scan | L3 | ✗ FAIL | ✓ PASS |
| 20 | Meeting notes mentioning Jared | L4 | ✓ PASS | ✓ PASS |
| 21 | Press Contacts visibility | L3 | ✗ FAIL | ✗ FAIL |
| 22 | Five most recently edited pages | L2 | ✓ PASS | ✓ PASS |
| 23 | Append a paragraph to Tomb-3 | L1 | ✓ PASS | ✓ PASS |
| 24 | Mark BUG-247 Fixed | L2 | ✓ PASS | ✓ PASS |
| 25 | Re-assign BUG-248 to Devon | L2 | ✓ PASS | ✓ PASS |
| 26 | Edit a paragraph block keeping a mention | L3 | ✗ FAIL | ⚠ ERROR |
| 27 | Check off a to_do | L2 | ✓ PASS | ✓ PASS |
| 28 | Delete a divider block | L2 | ✗ FAIL | ✗ FAIL |
| 29 | Archive a stale page | L2 | ◐ PARTIAL | ✓ PASS |
| 30 | Comment on BUG-247 | L2 | ✓ PASS | ✗ FAIL |
| 31 | Comment on a specific block | L3 | ◐ PARTIAL | ✓ PASS |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | ✓ PASS |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | ✓ PASS |
| 34 | Create a new task | L3 | ✓ PASS | ✓ PASS |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | ✗ FAIL |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | ✓ PASS |
| 37 | Update Bugs database description | L2 | ✓ PASS | ✓ PASS |
| 38 | Set page icon | L2 | ✓ PASS | ✗ FAIL |
| 39 | Convert paragraph to heading_2 (delete + append) | L4 | ✗ FAIL | ✓ PASS |
| 40 | Append a nested toggle to Launch 2026 | L3 | ◐ PARTIAL | ✓ PASS |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | ✓ PASS |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | ✓ PASS |
| 43 | Cross-database link | L5 | ✓ PASS | ⚠ ERROR |
| 44 | Weekly digest page | L5 | ✓ PASS | ✓ PASS |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | ✓ PASS |
| 46 | Meeting note from a template | L4 | ◐ PARTIAL | ✓ PASS |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | ✓ PASS |
| 48 | Archive sweep under Playtest Archive | L4 | ✗ FAIL | ✓ PASS |
| 49 | Comment fan-out on blocker bugs | L4 | ✓ PASS | ✓ PASS |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | ✓ PASS |
| 51 | Read a non-shared page | L2 | ✗ FAIL | ✗ FAIL |
| 52 | Write to an archived page | L2 | ✗ FAIL | ⚠ ERROR |
| 53 | Property-type violation | L3 | ✓ PASS | ✓ PASS |
| 54 | Query a non-shared database | L3 | ✗ FAIL | ✗ FAIL |
| 55 | Resolve a revoked user | L3 | ✓ PASS | ✓ PASS |
| 56 | Append to a non-shared page | L2 | ✗ FAIL | ✗ FAIL |
| 57 | Pagination boundary at exact page_size | L3 | ✗ FAIL | ✓ PASS |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Notion MCP | Hintas MCP | Δ Hintas MCP vs Notion MCP |
|---:|:------|---:|---:|---:|
| 1 | List active workspace users | 466 | 633 | +167 |
| 2 | Identify the integration's bot user | 768 | 377 | -391 |
| 4 | Retrieve the Bugs database schema | 490 | 1,417 | +927 |
| 5 | Retrieve a specific bug row | 616 | 936 | +320 |
| 6 | Read the Tomb-3 page top-level blocks | 570 | 1,966 | +1,396 |
| 7 | Paginated children of Team Directory | 1,222 | 853 | *excl* |
| 8 | List comments on BUG-247 | 933 | 3,078 | +2,145 |
| 9 | Resolve a relation property | 405 | 2,890 | +2,485 |
| 10 | Read to_do checked states | 365 | 972 | +607 |
| 12 | List databases shared to the integration | 714 | 549 | *excl* |
| 13 | Search by title — BUG-247 | 467 | 1,202 | +735 |
| 14 | Search filtered to databases | 5,297 | 2,133 | -3,164 |
| 15 | Open blockers in Bugs | 2,828 | 2,258 | -570 |
| 16 | Tasks Due in next 14 days (calendar) | 4,082 | 1,480 | -2,602 |
| 17 | Overdue not-Done tasks | 4,265 | 1,132 | -3,133 |
| 18 | High-severity macOS bugs | 4,809 | 1,818 | -2,991 |
| 19 | Paginated full-Tasks scan | 10,722 | 1,509 | *excl* |
| 20 | Meeting notes mentioning Jared | 4,226 | 1,229 | -2,997 |
| 21 | Press Contacts visibility | 424 | 466 | *excl* |
| 22 | Five most recently edited pages | 929 | 489 | -440 |
| 23 | Append a paragraph to Tomb-3 | 584 | 740 | +156 |
| 24 | Mark BUG-247 Fixed | 318 | 3,109 | +2,791 |
| 25 | Re-assign BUG-248 to Devon | 755 | 3,252 | +2,497 |
| 26 | Edit a paragraph block keeping a mention | 5,456 | 0 | *excl* |
| 27 | Check off a to_do | 731 | 3,113 | +2,382 |
| 28 | Delete a divider block | 908 | 4,241 | *excl* |
| 29 | Archive a stale page | 1,564 | 883 | *excl* |
| 30 | Comment on BUG-247 | 356 | 4,504 | *excl* |
| 31 | Comment on a specific block | 5,527 | 5,410 | *excl* |
| 32 | Add a select option to Bugs.Severity | 463 | 928 | +465 |
| 33 | Rename Projects (catalog) database | 294 | 567 | +273 |
| 34 | Create a new task | 712 | 1,374 | +662 |
| 35 | Unarchive Playtest — alpha round 3 | 2,821 | 6,474 | *excl* |
| 36 | Rename Bugs.Filed property | 512 | 1,119 | +607 |
| 37 | Update Bugs database description | 407 | 807 | +400 |
| 38 | Set page icon | 372 | 507 | *excl* |
| 39 | Convert paragraph to heading_2 (delete + append) | 4,619 | 14,864 | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 643 | 1,059 | *excl* |
| 41 | Bulk-update overdue tasks | 4,209 | 7,422 | +3,213 |
| 42 | Spin up a new bug end-to-end | 1,213 | 6,247 | +5,034 |
| 43 | Cross-database link | 7,224 | 0 | *excl* |
| 44 | Weekly digest page | 10,968 | 5,689 | -5,279 |
| 45 | Catch-up sweep on overdue In-Progress tasks | 6,614 | 2,328 | -4,286 |
| 46 | Meeting note from a template | 14,150 | 9,203 | *excl* |
| 47 | Mention round-up across meetings | 6,535 | 2,002 | -4,533 |
| 48 | Archive sweep under Playtest Archive | 12,905 | 1,476 | *excl* |
| 49 | Comment fan-out on blocker bugs | 3,024 | 2,308 | -716 |
| 50 | End-to-end launch-prep | 7,206 | 2,827 | -4,379 |
| 51 | Read a non-shared page | 346 | 2,285 | *excl* |
| 52 | Write to an archived page | 5,063 | 0 | *excl* |
| 53 | Property-type violation | 559 | 1,788 | +1,229 |
| 54 | Query a non-shared database | 1,622 | 1,376 | *excl* |
| 55 | Resolve a revoked user | 191 | 1,316 | +1,125 |
| 56 | Append to a non-shared page | 2,862 | 1,330 | *excl* |
| 57 | Pagination boundary at exact page_size | 1,275 | 4,001 | *excl* |
| 58 | Update with a non-existent select option | 1,361 | 3,465 | +2,104 |

## Per-prompt wall-clock

| ID | Title | Notion MCP | Hintas MCP | Δ Hintas MCP vs Notion MCP |
|---:|:------|---:|---:|---:|
| 1 | List active workspace users | 14.3s | 20.2s | +5.9s |
| 2 | Identify the integration's bot user | 20.9s | 18.9s | -2.1s |
| 4 | Retrieve the Bugs database schema | 14.1s | 43.2s | +29.1s |
| 5 | Retrieve a specific bug row | 19.8s | 29.8s | +10.0s |
| 6 | Read the Tomb-3 page top-level blocks | 15.1s | 43.2s | +28.1s |
| 7 | Paginated children of Team Directory | 26.0s | 30.1s | *excl* |
| 8 | List comments on BUG-247 | 22.0s | 74.8s | +52.8s |
| 9 | Resolve a relation property | 27.8s | 69.2s | +41.4s |
| 10 | Read to_do checked states | 19.4s | 37.2s | +17.8s |
| 12 | List databases shared to the integration | 23.5s | 27.6s | *excl* |
| 13 | Search by title — BUG-247 | 18.7s | 41.0s | +22.3s |
| 14 | Search filtered to databases | 124.7s | 66.8s | -57.9s |
| 15 | Open blockers in Bugs | 43.8s | 71.5s | +27.7s |
| 16 | Tasks Due in next 14 days (calendar) | 67.8s | 39.3s | -28.5s |
| 17 | Overdue not-Done tasks | 116.7s | 29.8s | -86.9s |
| 18 | High-severity macOS bugs | 95.1s | 43.3s | -51.8s |
| 19 | Paginated full-Tasks scan | 201.1s | 43.6s | *excl* |
| 20 | Meeting notes mentioning Jared | 64.0s | 32.0s | -32.0s |
| 21 | Press Contacts visibility | 24.3s | 26.8s | *excl* |
| 22 | Five most recently edited pages | 22.6s | 21.3s | -1.3s |
| 23 | Append a paragraph to Tomb-3 | 20.5s | 30.1s | +9.6s |
| 24 | Mark BUG-247 Fixed | 10.7s | 79.8s | +69.2s |
| 25 | Re-assign BUG-248 to Devon | 21.7s | 75.0s | +53.3s |
| 26 | Edit a paragraph block keeping a mention | 109.0s | 300.0s | *excl* |
| 27 | Check off a to_do | 17.1s | 79.4s | +62.3s |
| 28 | Delete a divider block | 20.8s | 82.5s | *excl* |
| 29 | Archive a stale page | 39.4s | 23.6s | *excl* |
| 30 | Comment on BUG-247 | 12.7s | 79.9s | *excl* |
| 31 | Comment on a specific block | 88.7s | 110.5s | *excl* |
| 32 | Add a select option to Bugs.Severity | 13.1s | 22.1s | +8.9s |
| 33 | Rename Projects (catalog) database | 16.1s | 16.4s | +0.2s |
| 34 | Create a new task | 31.9s | 43.8s | +11.9s |
| 35 | Unarchive Playtest — alpha round 3 | 58.9s | 147.7s | *excl* |
| 36 | Rename Bugs.Filed property | 15.8s | 30.4s | +14.6s |
| 37 | Update Bugs database description | 14.1s | 34.6s | +20.5s |
| 38 | Set page icon | 11.0s | 22.8s | *excl* |
| 39 | Convert paragraph to heading_2 (delete + append) | 89.6s | 292.9s | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 22.6s | 26.9s | *excl* |
| 41 | Bulk-update overdue tasks | 57.3s | 55.2s | -2.2s |
| 42 | Spin up a new bug end-to-end | 28.4s | 57.9s | +29.5s |
| 43 | Cross-database link | 107.3s | 300.0s | *excl* |
| 44 | Weekly digest page | 154.6s | 110.5s | -44.1s |
| 45 | Catch-up sweep on overdue In-Progress tasks | 130.3s | 64.2s | -66.1s |
| 46 | Meeting note from a template | 207.5s | 177.0s | *excl* |
| 47 | Mention round-up across meetings | 104.2s | 39.4s | -64.8s |
| 48 | Archive sweep under Playtest Archive | 187.5s | 40.7s | *excl* |
| 49 | Comment fan-out on blocker bugs | 53.4s | 48.0s | -5.4s |
| 50 | End-to-end launch-prep | 124.8s | 53.9s | -70.9s |
| 51 | Read a non-shared page | 12.4s | 50.2s | *excl* |
| 52 | Write to an archived page | 133.3s | 300.0s | *excl* |
| 53 | Property-type violation | 23.2s | 47.6s | +24.4s |
| 54 | Query a non-shared database | 38.1s | 27.6s | *excl* |
| 55 | Resolve a revoked user | 12.2s | 41.3s | +29.1s |
| 56 | Append to a non-shared page | 53.2s | 30.9s | *excl* |
| 57 | Pagination boundary at exact page_size | 27.2s | 37.6s | *excl* |
| 58 | Update with a non-existent select option | 31.8s | 74.9s | +43.1s |

## Verdict tallies

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| PASS | 38 | 45 |
| PARTIAL | 4 | 0 |
| FAIL | 14 | 8 |
| ERROR | 0 | 3 |
| Pass rate | 68% | 80% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| Tools complete | 399 | 295 |
| Tools failed | 12 | 0 |
| Tools partial | 0 | 0 |
| Total | 411 | 295 |
| Tool pass rate | 97% | 100% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 44, 45, 47, 49, 50, 53, 55, 58` (count: 35)
- Excluded count: 21

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| Total tokens | 78,172 | 74,411 |
| Avg tokens / prompt | 2,233 | 2,126 |
| Avg tokens / tool call | 267 | 400 |
| Avg peak context | 533 | 823 |
| Avg initial context | 3.00 | 3.00 |
| Avg wall-clock (s) | 45.4 | 48.2 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.

- Comparable prompt IDs: `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 44, 45, 47, 49, 50, 53, 55, 58` (count: 35)

| Metric | Notion MCP | Hintas MCP | Δ (Hintas MCP − Notion MCP) |
|:-------|---:|---:|---:|
| Total tokens | 78,172 | 74,411 | -3,761 |
| Avg tokens / prompt | 2,233 | 2,126 | -107 |
| Avg tokens / tool call | 267 | 400 | +133 |
| Avg peak context | 533 | 823 | +290 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 45.4 | 48.2 | +2.8 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Notion MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS). Cells show the winner: `✓` = variant wins, `base` = baseline wins.

| Metric | Hintas MCP |
|:-------|:---:|
| Accuracy | ✓ +12.5 pp |
| Speed | base +5.8% |
| Tokens | ✓ +4.8% |
| Peak context | base +35.2% |
| Tool reliability | ✓ |
| **Overall winner** | **✓** |
