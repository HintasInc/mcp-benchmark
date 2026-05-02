# Combined Benchmark Comparison — Notion — 20260501_2325

**Scope:** 58 prompts × 2 stacks (baseline + 1 variant).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion` (Notion MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off` (Hintas MCP)

## Per-run reports

- Notion MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion`
- Hintas MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off`

## MCP configuration

> Variant columns show the parameters each variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Notion MCP | Hintas MCP |
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

| ID | Title | Diff | Notion MCP | Hintas MCP |
|---:|:------|:----:|:------:|:------:|
| 1 | List active workspace users | L1 | ✓ PASS | ✓ PASS |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | ✓ PASS |
| 3 | Get my email address | L1 | — | ✗ FAIL |
| 4 | Retrieve the Bugs database schema | L2 | ✓ PASS | ◐ PARTIAL |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | ✓ PASS |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ✓ PASS | ◐ PARTIAL |
| 7 | Paginated children of Team Directory | L2 | ✗ FAIL | ✗ FAIL |
| 8 | List comments on BUG-247 | L2 | ✓ PASS | ◐ PARTIAL |
| 9 | Resolve a relation property | L3 | ✓ PASS | ✓ PASS |
| 10 | Read to_do checked states | L2 | ✓ PASS | ✓ PASS |
| 11 | Get a teammate's email address | L1 | — | ✗ FAIL |
| 12 | List databases shared to the integration | L2 | ✗ FAIL | ◐ PARTIAL |
| 13 | Search by title — BUG-247 | L2 | ✓ PASS | ◐ PARTIAL |
| 14 | Search filtered to databases | L2 | ✓ PASS | ◐ PARTIAL |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | ✓ PASS |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | ✓ PASS |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | ✓ PASS |
| 18 | High-severity macOS bugs | L3 | ✓ PASS | ◐ PARTIAL |
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
| 30 | Comment on BUG-247 | L2 | ✓ PASS | ◐ PARTIAL |
| 31 | Comment on a specific block | L3 | ◐ PARTIAL | ◐ PARTIAL |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | ✓ PASS |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | ✓ PASS |
| 34 | Create a new task | L3 | ✓ PASS | ✓ PASS |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | ✗ FAIL |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | ✓ PASS |
| 37 | Update Bugs database description | L2 | ✓ PASS | ✓ PASS |
| 38 | Set page icon | L2 | ✓ PASS | ✓ PASS |
| 39 | Convert paragraph to heading_2 (delete + append) | L4 | ✗ FAIL | ✗ FAIL |
| 40 | Append a nested toggle to Launch 2026 | L3 | ◐ PARTIAL | ✓ PASS |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | ✓ PASS |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | ✓ PASS |
| 43 | Cross-database link | L5 | ✓ PASS | ◐ PARTIAL |
| 44 | Weekly digest page | L5 | ✓ PASS | ◐ PARTIAL |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | ✓ PASS |
| 46 | Meeting note from a template | L4 | ◐ PARTIAL | ✓ PASS |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | ✓ PASS |
| 48 | Archive sweep under Playtest Archive | L4 | ✗ FAIL | ✓ PASS |
| 49 | Comment fan-out on blocker bugs | L4 | ✓ PASS | ✗ FAIL |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | ✓ PASS |
| 51 | Read a non-shared page | L2 | ✗ FAIL | ✓ PASS |
| 52 | Write to an archived page | L2 | ✗ FAIL | ✓ PASS |
| 53 | Property-type violation | L3 | ✓ PASS | ✗ FAIL |
| 54 | Query a non-shared database | L3 | ✗ FAIL | ✓ PASS |
| 55 | Resolve a revoked user | L3 | ✓ PASS | ✓ PASS |
| 56 | Append to a non-shared page | L2 | ✗ FAIL | ✓ PASS |
| 57 | Pagination boundary at exact page_size | L3 | ✗ FAIL | ✗ FAIL |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Notion MCP | Hintas MCP | Δ Hintas MCP vs Notion MCP |
|---:|:------|---:|---:|---:|
| 1 | List active workspace users | 466 | 630 | +164 |
| 2 | Identify the integration's bot user | 768 | 557 | -211 |
| 3 | Get my email address | — | 0 | *excl* |
| 4 | Retrieve the Bugs database schema | 490 | 1,328 | *excl* |
| 5 | Retrieve a specific bug row | 616 | 2,770 | +2,154 |
| 6 | Read the Tomb-3 page top-level blocks | 570 | 1,249 | *excl* |
| 7 | Paginated children of Team Directory | 1,222 | 962 | *excl* |
| 8 | List comments on BUG-247 | 933 | 878 | *excl* |
| 9 | Resolve a relation property | 405 | 2,532 | +2,127 |
| 10 | Read to_do checked states | 365 | 2,346 | +1,981 |
| 11 | Get a teammate's email address | — | 0 | *excl* |
| 12 | List databases shared to the integration | 714 | 581 | *excl* |
| 13 | Search by title — BUG-247 | 467 | 714 | *excl* |
| 14 | Search filtered to databases | 5,297 | 864 | *excl* |
| 15 | Open blockers in Bugs | 2,828 | 2,178 | -650 |
| 16 | Tasks Due in next 14 days (calendar) | 4,082 | 1,607 | -2,475 |
| 17 | Overdue not-Done tasks | 4,265 | 1,118 | -3,147 |
| 18 | High-severity macOS bugs | 4,809 | 1,948 | *excl* |
| 19 | Paginated full-Tasks scan | 10,722 | 1,532 | *excl* |
| 20 | Meeting notes mentioning Jared | 4,226 | 944 | -3,282 |
| 21 | Press Contacts visibility | 424 | 437 | *excl* |
| 22 | Five most recently edited pages | 929 | 608 | -321 |
| 23 | Append a paragraph to Tomb-3 | 584 | 730 | +146 |
| 24 | Mark BUG-247 Fixed | 318 | 2,139 | +1,821 |
| 25 | Re-assign BUG-248 to Devon | 755 | 2,295 | +1,540 |
| 26 | Edit a paragraph block keeping a mention | 5,456 | 0 | *excl* |
| 27 | Check off a to_do | 731 | 1,488 | +757 |
| 28 | Delete a divider block | 908 | 2,800 | *excl* |
| 29 | Archive a stale page | 1,564 | 1,621 | *excl* |
| 30 | Comment on BUG-247 | 356 | 2,011 | *excl* |
| 31 | Comment on a specific block | 5,527 | 1,876 | *excl* |
| 32 | Add a select option to Bugs.Severity | 463 | 1,336 | +873 |
| 33 | Rename Projects (catalog) database | 294 | 547 | +253 |
| 34 | Create a new task | 712 | 1,194 | +482 |
| 35 | Unarchive Playtest — alpha round 3 | 2,821 | 10,662 | *excl* |
| 36 | Rename Bugs.Filed property | 512 | 1,078 | +566 |
| 37 | Update Bugs database description | 407 | 858 | +451 |
| 38 | Set page icon | 372 | 687 | +315 |
| 39 | Convert paragraph to heading_2 (delete + append) | 4,619 | 11,765 | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 643 | 1,115 | *excl* |
| 41 | Bulk-update overdue tasks | 4,209 | 1,977 | -2,232 |
| 42 | Spin up a new bug end-to-end | 1,213 | 2,549 | +1,336 |
| 43 | Cross-database link | 7,224 | 9,960 | *excl* |
| 44 | Weekly digest page | 10,968 | 4,432 | *excl* |
| 45 | Catch-up sweep on overdue In-Progress tasks | 6,614 | 1,763 | -4,851 |
| 46 | Meeting note from a template | 14,150 | 3,955 | *excl* |
| 47 | Mention round-up across meetings | 6,535 | 1,789 | -4,746 |
| 48 | Archive sweep under Playtest Archive | 12,905 | 1,439 | *excl* |
| 49 | Comment fan-out on blocker bugs | 3,024 | 2,828 | *excl* |
| 50 | End-to-end launch-prep | 7,206 | 3,428 | -3,778 |
| 51 | Read a non-shared page | 346 | 1,874 | *excl* |
| 52 | Write to an archived page | 5,063 | 11,698 | *excl* |
| 53 | Property-type violation | 559 | 2,655 | *excl* |
| 54 | Query a non-shared database | 1,622 | 1,506 | *excl* |
| 55 | Resolve a revoked user | 191 | 629 | +438 |
| 56 | Append to a non-shared page | 2,862 | 8,453 | *excl* |
| 57 | Pagination boundary at exact page_size | 1,275 | 1,172 | *excl* |
| 58 | Update with a non-existent select option | 1,361 | 1,759 | +398 |

## Per-prompt wall-clock

| ID | Title | Notion MCP | Hintas MCP | Δ Hintas MCP vs Notion MCP |
|---:|:------|---:|---:|---:|
| 1 | List active workspace users | 14.3s | 15.6s | +1.3s |
| 2 | Identify the integration's bot user | 20.9s | 18.0s | -3.0s |
| 3 | Get my email address | — | 0.0s | *excl* |
| 4 | Retrieve the Bugs database schema | 14.1s | 30.9s | *excl* |
| 5 | Retrieve a specific bug row | 19.8s | 68.3s | +48.6s |
| 6 | Read the Tomb-3 page top-level blocks | 15.1s | 26.1s | *excl* |
| 7 | Paginated children of Team Directory | 26.0s | 29.8s | *excl* |
| 8 | List comments on BUG-247 | 22.0s | 27.1s | *excl* |
| 9 | Resolve a relation property | 27.8s | 51.2s | +23.4s |
| 10 | Read to_do checked states | 19.4s | 60.2s | +40.8s |
| 11 | Get a teammate's email address | — | 0.0s | *excl* |
| 12 | List databases shared to the integration | 23.5s | 17.4s | *excl* |
| 13 | Search by title — BUG-247 | 18.7s | 15.8s | *excl* |
| 14 | Search filtered to databases | 124.7s | 18.9s | *excl* |
| 15 | Open blockers in Bugs | 43.8s | 43.7s | -0.1s |
| 16 | Tasks Due in next 14 days (calendar) | 67.8s | 35.3s | -32.5s |
| 17 | Overdue not-Done tasks | 116.7s | 27.1s | -89.6s |
| 18 | High-severity macOS bugs | 95.1s | 38.6s | *excl* |
| 19 | Paginated full-Tasks scan | 201.1s | 38.1s | *excl* |
| 20 | Meeting notes mentioning Jared | 64.0s | 22.8s | -41.2s |
| 21 | Press Contacts visibility | 24.3s | 17.2s | *excl* |
| 22 | Five most recently edited pages | 22.6s | 19.9s | -2.7s |
| 23 | Append a paragraph to Tomb-3 | 20.5s | 21.9s | +1.4s |
| 24 | Mark BUG-247 Fixed | 10.7s | 70.1s | +59.5s |
| 25 | Re-assign BUG-248 to Devon | 21.7s | 86.8s | +65.1s |
| 26 | Edit a paragraph block keeping a mention | 109.0s | 300.0s | *excl* |
| 27 | Check off a to_do | 17.1s | 39.0s | +22.0s |
| 28 | Delete a divider block | 20.8s | 60.2s | *excl* |
| 29 | Archive a stale page | 39.4s | 44.8s | *excl* |
| 30 | Comment on BUG-247 | 12.7s | 58.3s | *excl* |
| 31 | Comment on a specific block | 88.7s | 52.2s | *excl* |
| 32 | Add a select option to Bugs.Severity | 13.1s | 48.8s | +35.7s |
| 33 | Rename Projects (catalog) database | 16.1s | 16.5s | +0.3s |
| 34 | Create a new task | 31.9s | 36.8s | +4.9s |
| 35 | Unarchive Playtest — alpha round 3 | 58.9s | 231.9s | *excl* |
| 36 | Rename Bugs.Filed property | 15.8s | 35.7s | +19.8s |
| 37 | Update Bugs database description | 14.1s | 32.9s | +18.8s |
| 38 | Set page icon | 11.0s | 19.1s | +8.1s |
| 39 | Convert paragraph to heading_2 (delete + append) | 89.6s | 213.9s | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 22.6s | 24.6s | *excl* |
| 41 | Bulk-update overdue tasks | 57.3s | 54.1s | -3.3s |
| 42 | Spin up a new bug end-to-end | 28.4s | 73.5s | +45.2s |
| 43 | Cross-database link | 107.3s | 187.5s | *excl* |
| 44 | Weekly digest page | 154.6s | 79.2s | *excl* |
| 45 | Catch-up sweep on overdue In-Progress tasks | 130.3s | 48.5s | -81.8s |
| 46 | Meeting note from a template | 207.5s | 75.9s | *excl* |
| 47 | Mention round-up across meetings | 104.2s | 30.2s | -74.0s |
| 48 | Archive sweep under Playtest Archive | 187.5s | 35.5s | *excl* |
| 49 | Comment fan-out on blocker bugs | 53.4s | 58.5s | *excl* |
| 50 | End-to-end launch-prep | 124.8s | 70.2s | -54.6s |
| 51 | Read a non-shared page | 12.4s | 41.5s | *excl* |
| 52 | Write to an archived page | 133.3s | 222.2s | *excl* |
| 53 | Property-type violation | 23.2s | 57.5s | *excl* |
| 54 | Query a non-shared database | 38.1s | 33.5s | *excl* |
| 55 | Resolve a revoked user | 12.2s | 19.1s | +6.8s |
| 56 | Append to a non-shared page | 53.2s | 131.3s | *excl* |
| 57 | Pagination boundary at exact page_size | 27.2s | 27.7s | *excl* |
| 58 | Update with a non-existent select option | 31.8s | 44.0s | +12.2s |

## Verdict tallies

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| PASS | 38 | 36 |
| PARTIAL | 4 | 11 |
| FAIL | 14 | 10 |
| ERROR | 0 | 1 |
| Pass rate | 68% | 62% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| Tools complete | 399 | 297 |
| Tools failed | 12 | 0 |
| Tools partial | 0 | 4 |
| Total | 411 | 301 |
| Tool pass rate | 97% | 99% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `1, 2, 5, 9, 10, 15, 16, 17, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 38, 41, 42, 45, 47, 50, 55, 58` (count: 27)
- Excluded count: 31

| Metric | Notion MCP | Hintas MCP |
|:-------|---:|---:|
| Total tokens | 51,427 | 41,536 |
| Avg tokens / prompt | 1,905 | 1,538 |
| Avg tokens / tool call | 241 | 315 |
| Avg peak context | 396 | 19 |
| Avg initial context | 3.00 | 3.00 |
| Avg wall-clock (s) | 39.9 | 41.1 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.

- Comparable prompt IDs: `1, 2, 5, 9, 10, 15, 16, 17, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 38, 41, 42, 45, 47, 50, 55, 58` (count: 27)

| Metric | Notion MCP | Hintas MCP | Δ (Hintas MCP − Notion MCP) |
|:-------|---:|---:|---:|
| Total tokens | 51,427 | 41,536 | -9,891 |
| Avg tokens / prompt | 1,905 | 1,538 | -366 |
| Avg tokens / tool call | 241 | 315 | +73 |
| Avg peak context | 396 | 19 | -377 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 39.9 | 41.1 | +1.2 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Notion MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS). Cells show the winner: `✓` = variant wins, `base` = baseline wins.

| Metric | Hintas MCP |
|:-------|:---:|
| Accuracy | base +5.8 pp |
| Speed | base +2.8% |
| Tokens | ✓ +19.2% |
| Peak context | ✓ +95.1% |
| Tool reliability | ✓ |
| **Overall winner** | **✓** |
