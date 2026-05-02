# Combined Benchmark Comparison — Notion — 20260501_2333

**Scope:** 58 prompts × 3 stacks (baseline + 2 variants).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion` (Notion MCP)
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off` (Hintas MCP (max=10))
- Variant : `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off` (Hintas MCP (max=8))

## Per-run reports

- Notion MCP: [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205418__notion`
- Hintas MCP (max=10): [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off`
- Hintas MCP (max=8): [`analysis.md`](/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off/analysis.md)  ↳ `/Users/pratima/Documents/Projects/hintas-project/benchmarking/platforms/notion/runs/20260429_231236__hintas__topk10_batch-off_max8_rag-off`

## MCP configuration

> Variant columns show the parameters each variant run was launched with, alongside the baseline MCP (which carries no Hintas params).

| Parameter | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:----------|:--------------:|:--------------:|:--------------:|
| `search_top_k` | **—** | **10** | **10** |
| `search_batch_enabled` | **—** | **off** | **off** |
| `search_max_results` | **—** | **10**  ⚠ | **8**  ⚠ |
| `rag_enabled` | **—** | **off** | **off** |

_Parameters differing across variants: `search_max_results`._

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt verdicts

| ID | Title | Diff | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) |
|---:|:------|:----:|:------:|:------:|:------:|
| 1 | List active workspace users | L1 | ✓ PASS | ✓ PASS | ✓ PASS |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | ✓ PASS | ✓ PASS |
| 3 | Get my email address | L1 | — | — | ✗ FAIL |
| 4 | Retrieve the Bugs database schema | L2 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 7 | Paginated children of Team Directory | L2 | ✗ FAIL | ✓ PASS | ✗ FAIL |
| 8 | List comments on BUG-247 | L2 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 9 | Resolve a relation property | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 10 | Read to_do checked states | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 11 | Get a teammate's email address | L1 | — | — | ✗ FAIL |
| 12 | List databases shared to the integration | L2 | ✗ FAIL | ✓ PASS | ◐ PARTIAL |
| 13 | Search by title — BUG-247 | L2 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 14 | Search filtered to databases | L2 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 18 | High-severity macOS bugs | L3 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 19 | Paginated full-Tasks scan | L3 | ✗ FAIL | ✓ PASS | ✓ PASS |
| 20 | Meeting notes mentioning Jared | L4 | ✓ PASS | ✓ PASS | ✓ PASS |
| 21 | Press Contacts visibility | L3 | ✗ FAIL | ✗ FAIL | ✗ FAIL |
| 22 | Five most recently edited pages | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 23 | Append a paragraph to Tomb-3 | L1 | ✓ PASS | ✓ PASS | ✓ PASS |
| 24 | Mark BUG-247 Fixed | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 25 | Re-assign BUG-248 to Devon | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 26 | Edit a paragraph block keeping a mention | L3 | ✗ FAIL | ⚠ ERROR | ⚠ ERROR |
| 27 | Check off a to_do | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 28 | Delete a divider block | L2 | ✗ FAIL | ✗ FAIL | ✗ FAIL |
| 29 | Archive a stale page | L2 | ◐ PARTIAL | ✓ PASS | ✓ PASS |
| 30 | Comment on BUG-247 | L2 | ✓ PASS | ✗ FAIL | ◐ PARTIAL |
| 31 | Comment on a specific block | L3 | ◐ PARTIAL | ✓ PASS | ◐ PARTIAL |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 34 | Create a new task | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | ✗ FAIL | ✗ FAIL |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 37 | Update Bugs database description | L2 | ✓ PASS | ✓ PASS | ✓ PASS |
| 38 | Set page icon | L2 | ✓ PASS | ✗ FAIL | ✓ PASS |
| 39 | Convert paragraph to heading_2 (delete + append) | L4 | ✗ FAIL | ✓ PASS | ✗ FAIL |
| 40 | Append a nested toggle to Launch 2026 | L3 | ◐ PARTIAL | ✓ PASS | ✓ PASS |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | ✓ PASS | ✓ PASS |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | ✓ PASS | ✓ PASS |
| 43 | Cross-database link | L5 | ✓ PASS | ⚠ ERROR | ◐ PARTIAL |
| 44 | Weekly digest page | L5 | ✓ PASS | ✓ PASS | ◐ PARTIAL |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | ✓ PASS | ✓ PASS |
| 46 | Meeting note from a template | L4 | ◐ PARTIAL | ✓ PASS | ✓ PASS |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | ✓ PASS | ✓ PASS |
| 48 | Archive sweep under Playtest Archive | L4 | ✗ FAIL | ✓ PASS | ✓ PASS |
| 49 | Comment fan-out on blocker bugs | L4 | ✓ PASS | ✓ PASS | ✗ FAIL |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | ✓ PASS | ✓ PASS |
| 51 | Read a non-shared page | L2 | ✗ FAIL | ✗ FAIL | ✓ PASS |
| 52 | Write to an archived page | L2 | ✗ FAIL | ⚠ ERROR | ✓ PASS |
| 53 | Property-type violation | L3 | ✓ PASS | ✓ PASS | ✗ FAIL |
| 54 | Query a non-shared database | L3 | ✗ FAIL | ✗ FAIL | ✓ PASS |
| 55 | Resolve a revoked user | L3 | ✓ PASS | ✓ PASS | ✓ PASS |
| 56 | Append to a non-shared page | L2 | ✗ FAIL | ✗ FAIL | ✓ PASS |
| 57 | Pagination boundary at exact page_size | L3 | ✗ FAIL | ✓ PASS | ✗ FAIL |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | ✓ PASS | ✓ PASS |

## Per-prompt total tokens

| ID | Title | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) | Δ Hintas MCP (max=10) vs Notion MCP | Δ Hintas MCP (max=8) vs Notion MCP |
|---:|:------|---:|---:|---:|---:|---:|
| 1 | List active workspace users | 466 | 633 | 630 | +167 | +164 |
| 2 | Identify the integration's bot user | 768 | 377 | 557 | -391 | -211 |
| 3 | Get my email address | — | — | 0 | *excl* | *excl* |
| 4 | Retrieve the Bugs database schema | 490 | 1,417 | 1,328 | +927 | *excl* |
| 5 | Retrieve a specific bug row | 616 | 936 | 2,770 | +320 | +2,154 |
| 6 | Read the Tomb-3 page top-level blocks | 570 | 1,966 | 1,249 | +1,396 | *excl* |
| 7 | Paginated children of Team Directory | 1,222 | 853 | 962 | *excl* | *excl* |
| 8 | List comments on BUG-247 | 933 | 3,078 | 878 | +2,145 | *excl* |
| 9 | Resolve a relation property | 405 | 2,890 | 2,532 | +2,485 | +2,127 |
| 10 | Read to_do checked states | 365 | 972 | 2,346 | +607 | +1,981 |
| 11 | Get a teammate's email address | — | — | 0 | *excl* | *excl* |
| 12 | List databases shared to the integration | 714 | 549 | 581 | *excl* | *excl* |
| 13 | Search by title — BUG-247 | 467 | 1,202 | 714 | +735 | *excl* |
| 14 | Search filtered to databases | 5,297 | 2,133 | 864 | -3,164 | *excl* |
| 15 | Open blockers in Bugs | 2,828 | 2,258 | 2,178 | -570 | -650 |
| 16 | Tasks Due in next 14 days (calendar) | 4,082 | 1,480 | 1,607 | -2,602 | -2,475 |
| 17 | Overdue not-Done tasks | 4,265 | 1,132 | 1,118 | -3,133 | -3,147 |
| 18 | High-severity macOS bugs | 4,809 | 1,818 | 1,948 | -2,991 | *excl* |
| 19 | Paginated full-Tasks scan | 10,722 | 1,509 | 1,532 | *excl* | *excl* |
| 20 | Meeting notes mentioning Jared | 4,226 | 1,229 | 944 | -2,997 | -3,282 |
| 21 | Press Contacts visibility | 424 | 466 | 437 | *excl* | *excl* |
| 22 | Five most recently edited pages | 929 | 489 | 608 | -440 | -321 |
| 23 | Append a paragraph to Tomb-3 | 584 | 740 | 730 | +156 | +146 |
| 24 | Mark BUG-247 Fixed | 318 | 3,109 | 2,139 | +2,791 | +1,821 |
| 25 | Re-assign BUG-248 to Devon | 755 | 3,252 | 2,295 | +2,497 | +1,540 |
| 26 | Edit a paragraph block keeping a mention | 5,456 | 0 | 0 | *excl* | *excl* |
| 27 | Check off a to_do | 731 | 3,113 | 1,488 | +2,382 | +757 |
| 28 | Delete a divider block | 908 | 4,241 | 2,800 | *excl* | *excl* |
| 29 | Archive a stale page | 1,564 | 883 | 1,621 | *excl* | *excl* |
| 30 | Comment on BUG-247 | 356 | 4,504 | 2,011 | *excl* | *excl* |
| 31 | Comment on a specific block | 5,527 | 5,410 | 1,876 | *excl* | *excl* |
| 32 | Add a select option to Bugs.Severity | 463 | 928 | 1,336 | +465 | +873 |
| 33 | Rename Projects (catalog) database | 294 | 567 | 547 | +273 | +253 |
| 34 | Create a new task | 712 | 1,374 | 1,194 | +662 | +482 |
| 35 | Unarchive Playtest — alpha round 3 | 2,821 | 6,474 | 10,662 | *excl* | *excl* |
| 36 | Rename Bugs.Filed property | 512 | 1,119 | 1,078 | +607 | +566 |
| 37 | Update Bugs database description | 407 | 807 | 858 | +400 | +451 |
| 38 | Set page icon | 372 | 507 | 687 | *excl* | +315 |
| 39 | Convert paragraph to heading_2 (delete + append) | 4,619 | 14,864 | 11,765 | *excl* | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 643 | 1,059 | 1,115 | *excl* | *excl* |
| 41 | Bulk-update overdue tasks | 4,209 | 7,422 | 1,977 | +3,213 | -2,232 |
| 42 | Spin up a new bug end-to-end | 1,213 | 6,247 | 2,549 | +5,034 | +1,336 |
| 43 | Cross-database link | 7,224 | 0 | 9,960 | *excl* | *excl* |
| 44 | Weekly digest page | 10,968 | 5,689 | 4,432 | -5,279 | *excl* |
| 45 | Catch-up sweep on overdue In-Progress tasks | 6,614 | 2,328 | 1,763 | -4,286 | -4,851 |
| 46 | Meeting note from a template | 14,150 | 9,203 | 3,955 | *excl* | *excl* |
| 47 | Mention round-up across meetings | 6,535 | 2,002 | 1,789 | -4,533 | -4,746 |
| 48 | Archive sweep under Playtest Archive | 12,905 | 1,476 | 1,439 | *excl* | *excl* |
| 49 | Comment fan-out on blocker bugs | 3,024 | 2,308 | 2,828 | -716 | *excl* |
| 50 | End-to-end launch-prep | 7,206 | 2,827 | 3,428 | -4,379 | -3,778 |
| 51 | Read a non-shared page | 346 | 2,285 | 1,874 | *excl* | *excl* |
| 52 | Write to an archived page | 5,063 | 0 | 11,698 | *excl* | *excl* |
| 53 | Property-type violation | 559 | 1,788 | 2,655 | +1,229 | *excl* |
| 54 | Query a non-shared database | 1,622 | 1,376 | 1,506 | *excl* | *excl* |
| 55 | Resolve a revoked user | 191 | 1,316 | 629 | +1,125 | +438 |
| 56 | Append to a non-shared page | 2,862 | 1,330 | 8,453 | *excl* | *excl* |
| 57 | Pagination boundary at exact page_size | 1,275 | 4,001 | 1,172 | *excl* | *excl* |
| 58 | Update with a non-existent select option | 1,361 | 3,465 | 1,759 | +2,104 | +398 |

## Per-prompt wall-clock

| ID | Title | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) | Δ Hintas MCP (max=10) vs Notion MCP | Δ Hintas MCP (max=8) vs Notion MCP |
|---:|:------|---:|---:|---:|---:|---:|
| 1 | List active workspace users | 14.3s | 20.2s | 15.6s | +5.9s | +1.3s |
| 2 | Identify the integration's bot user | 20.9s | 18.9s | 18.0s | -2.1s | -3.0s |
| 3 | Get my email address | — | — | 0.0s | *excl* | *excl* |
| 4 | Retrieve the Bugs database schema | 14.1s | 43.2s | 30.9s | +29.1s | *excl* |
| 5 | Retrieve a specific bug row | 19.8s | 29.8s | 68.3s | +10.0s | +48.6s |
| 6 | Read the Tomb-3 page top-level blocks | 15.1s | 43.2s | 26.1s | +28.1s | *excl* |
| 7 | Paginated children of Team Directory | 26.0s | 30.1s | 29.8s | *excl* | *excl* |
| 8 | List comments on BUG-247 | 22.0s | 74.8s | 27.1s | +52.8s | *excl* |
| 9 | Resolve a relation property | 27.8s | 69.2s | 51.2s | +41.4s | +23.4s |
| 10 | Read to_do checked states | 19.4s | 37.2s | 60.2s | +17.8s | +40.8s |
| 11 | Get a teammate's email address | — | — | 0.0s | *excl* | *excl* |
| 12 | List databases shared to the integration | 23.5s | 27.6s | 17.4s | *excl* | *excl* |
| 13 | Search by title — BUG-247 | 18.7s | 41.0s | 15.8s | +22.3s | *excl* |
| 14 | Search filtered to databases | 124.7s | 66.8s | 18.9s | -57.9s | *excl* |
| 15 | Open blockers in Bugs | 43.8s | 71.5s | 43.7s | +27.7s | -0.1s |
| 16 | Tasks Due in next 14 days (calendar) | 67.8s | 39.3s | 35.3s | -28.5s | -32.5s |
| 17 | Overdue not-Done tasks | 116.7s | 29.8s | 27.1s | -86.9s | -89.6s |
| 18 | High-severity macOS bugs | 95.1s | 43.3s | 38.6s | -51.8s | *excl* |
| 19 | Paginated full-Tasks scan | 201.1s | 43.6s | 38.1s | *excl* | *excl* |
| 20 | Meeting notes mentioning Jared | 64.0s | 32.0s | 22.8s | -32.0s | -41.2s |
| 21 | Press Contacts visibility | 24.3s | 26.8s | 17.2s | *excl* | *excl* |
| 22 | Five most recently edited pages | 22.6s | 21.3s | 19.9s | -1.3s | -2.7s |
| 23 | Append a paragraph to Tomb-3 | 20.5s | 30.1s | 21.9s | +9.6s | +1.4s |
| 24 | Mark BUG-247 Fixed | 10.7s | 79.8s | 70.1s | +69.2s | +59.5s |
| 25 | Re-assign BUG-248 to Devon | 21.7s | 75.0s | 86.8s | +53.3s | +65.1s |
| 26 | Edit a paragraph block keeping a mention | 109.0s | 300.0s | 300.0s | *excl* | *excl* |
| 27 | Check off a to_do | 17.1s | 79.4s | 39.0s | +62.3s | +22.0s |
| 28 | Delete a divider block | 20.8s | 82.5s | 60.2s | *excl* | *excl* |
| 29 | Archive a stale page | 39.4s | 23.6s | 44.8s | *excl* | *excl* |
| 30 | Comment on BUG-247 | 12.7s | 79.9s | 58.3s | *excl* | *excl* |
| 31 | Comment on a specific block | 88.7s | 110.5s | 52.2s | *excl* | *excl* |
| 32 | Add a select option to Bugs.Severity | 13.1s | 22.1s | 48.8s | +8.9s | +35.7s |
| 33 | Rename Projects (catalog) database | 16.1s | 16.4s | 16.5s | +0.2s | +0.3s |
| 34 | Create a new task | 31.9s | 43.8s | 36.8s | +11.9s | +4.9s |
| 35 | Unarchive Playtest — alpha round 3 | 58.9s | 147.7s | 231.9s | *excl* | *excl* |
| 36 | Rename Bugs.Filed property | 15.8s | 30.4s | 35.7s | +14.6s | +19.8s |
| 37 | Update Bugs database description | 14.1s | 34.6s | 32.9s | +20.5s | +18.8s |
| 38 | Set page icon | 11.0s | 22.8s | 19.1s | *excl* | +8.1s |
| 39 | Convert paragraph to heading_2 (delete + append) | 89.6s | 292.9s | 213.9s | *excl* | *excl* |
| 40 | Append a nested toggle to Launch 2026 | 22.6s | 26.9s | 24.6s | *excl* | *excl* |
| 41 | Bulk-update overdue tasks | 57.3s | 55.2s | 54.1s | -2.2s | -3.3s |
| 42 | Spin up a new bug end-to-end | 28.4s | 57.9s | 73.5s | +29.5s | +45.2s |
| 43 | Cross-database link | 107.3s | 300.0s | 187.5s | *excl* | *excl* |
| 44 | Weekly digest page | 154.6s | 110.5s | 79.2s | -44.1s | *excl* |
| 45 | Catch-up sweep on overdue In-Progress tasks | 130.3s | 64.2s | 48.5s | -66.1s | -81.8s |
| 46 | Meeting note from a template | 207.5s | 177.0s | 75.9s | *excl* | *excl* |
| 47 | Mention round-up across meetings | 104.2s | 39.4s | 30.2s | -64.8s | -74.0s |
| 48 | Archive sweep under Playtest Archive | 187.5s | 40.7s | 35.5s | *excl* | *excl* |
| 49 | Comment fan-out on blocker bugs | 53.4s | 48.0s | 58.5s | -5.4s | *excl* |
| 50 | End-to-end launch-prep | 124.8s | 53.9s | 70.2s | -70.9s | -54.6s |
| 51 | Read a non-shared page | 12.4s | 50.2s | 41.5s | *excl* | *excl* |
| 52 | Write to an archived page | 133.3s | 300.0s | 222.2s | *excl* | *excl* |
| 53 | Property-type violation | 23.2s | 47.6s | 57.5s | +24.4s | *excl* |
| 54 | Query a non-shared database | 38.1s | 27.6s | 33.5s | *excl* | *excl* |
| 55 | Resolve a revoked user | 12.2s | 41.3s | 19.1s | +29.1s | +6.8s |
| 56 | Append to a non-shared page | 53.2s | 30.9s | 131.3s | *excl* | *excl* |
| 57 | Pagination boundary at exact page_size | 27.2s | 37.6s | 27.7s | *excl* | *excl* |
| 58 | Update with a non-existent select option | 31.8s | 74.9s | 44.0s | +43.1s | +12.2s |

## Verdict tallies

| Metric | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|
| PASS | 38 | 45 | 36 |
| PARTIAL | 4 | 0 | 11 |
| FAIL | 14 | 8 | 10 |
| ERROR | 0 | 3 | 1 |
| Pass rate | 68% | 80% | 62% |

## Tool-call tallies (every prompt, regardless of verdict)

| Metric | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|
| Tools complete | 399 | 295 | 297 |
| Tools failed | 12 | 0 | 0 |
| Tools partial | 0 | 0 | 4 |
| Total | 411 | 295 | 301 |
| Tool pass rate | 97% | 100% | 99% |

## Global comparable metrics (every stack PASS)

- Comparable prompt IDs: `1, 2, 5, 9, 10, 15, 16, 17, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 45, 47, 50, 55, 58` (count: 26)
- Excluded count: 32

| Metric | Notion MCP | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|---:|---:|---:|
| Total tokens | 51,055 | 53,012 | 40,849 |
| Avg tokens / prompt | 1,964 | 2,039 | 1,571 |
| Avg tokens / tool call | 242 | 402 | 317 |
| Avg peak context | 411 | 1,099 | 20 |
| Avg initial context | 3.00 | 3.00 | 3.00 |
| Avg wall-clock (s) | 41.0 | 44.9 | 41.9 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token, speed, and context comparisons.
> Each variant column group uses its own pair-specific intersection, so baseline values differ across groups.

- Notion MCP ∩ Hintas MCP (max=10): n=35, IDs `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 44, 45, 47, 49, 50, 53, 55, 58`
- Notion MCP ∩ Hintas MCP (max=8): n=27, IDs `1, 2, 5, 9, 10, 15, 16, 17, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 38, 41, 42, 45, 47, 50, 55, 58`

| Metric | Notion MCP (Hintas MCP (max=10) pair) | Hintas MCP (max=10) | Δ (Hintas MCP (max=10) − Notion MCP) | Notion MCP (Hintas MCP (max=8) pair) | Hintas MCP (max=8) | Δ (Hintas MCP (max=8) − Notion MCP) |
|:-------|---:|---:|---:|---:|---:|---:|
| Total tokens | 78,172 | 74,411 | -3,761 | 51,427 | 41,536 | -9,891 |
| Avg tokens / prompt | 2,233 | 2,126 | -107 | 1,905 | 1,538 | -366 |
| Avg tokens / tool call | 267 | 400 | +133 | 241 | 315 | +73 |
| Avg peak context | 533 | 823 | +290 | 396 | 19 | -377 |
| Avg initial context | 3.00 | 3.00 | 0.00 | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 45.4 | 48.2 | +2.8 | 39.9 | 41.1 | +1.2 |

## Pairwise verdicts (each variant vs baseline)

Baseline: **Notion MCP**. Speed / token / context margins use the per-pair comparable subset (both stacks PASS). Cells show the winner: `✓` = variant wins, `base` = baseline wins.

| Metric | Hintas MCP (max=10) | Hintas MCP (max=8) |
|:-------|:---:|:---:|
| Accuracy | ✓ +12.5 pp | base +5.8 pp |
| Speed | base +5.8% | base +2.8% |
| Tokens | ✓ +4.8% | ✓ +19.2% |
| Peak context | base +35.2% | ✓ +95.1% |
| Tool reliability | ✓ | ✓ |
| **Overall winner** | **✓** | **✓** |
