# Benchmark Analysis — Hintas MCP — Run 20260429_231236__hintas__topk10_batch-off_max8_rag-off

**Scope:** 58 prompts × Hintas MCP, graded against precomputed session summaries (`analysis_data.json`).

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
| 1 | List active workspace users | L1 | ✓ PASS | 15.6s | 630 | 2 | 0 |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | 18.0s | 557 | 2 | 0 |
| 3 | Get my email address | L1 | ✗ FAIL | 0.0s | 0 | 0 | 0 |
| 4 | Retrieve the Bugs database schema | L2 | ◐ PARTIAL | 30.9s | 1,328 | 4 | 0 |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | 68.3s | 2,770 | 8 | 0 |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ◐ PARTIAL | 26.1s | 1,249 | 2 | 0 |
| 7 | Paginated children of Team Directory | L2 | ✗ FAIL | 29.8s | 962 | 3 | 0 |
| 8 | List comments on BUG-247 | L2 | ◐ PARTIAL | 27.1s | 878 | 3 | 0 |
| 9 | Resolve a relation property | L3 | ✓ PASS | 51.2s | 2,532 | 6 | 0 |
| 10 | Read to_do checked states | L2 | ✓ PASS | 60.2s | 2,346 | 6 | 0 |
| 11 | Get a teammate's email address | L1 | ✗ FAIL | 0.0s | 0 | 0 | 0 |
| 12 | List databases shared to the integration | L2 | ◐ PARTIAL | 17.4s | 581 | 3 | 0 |
| 13 | Search by title - BUG-247 | L2 | ◐ PARTIAL | 15.8s | 714 | 2 | 0 |
| 14 | Search filtered to databases | L2 | ◐ PARTIAL | 18.9s | 864 | 2 | 0 |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | 43.7s | 2,178 | 4 | 0 |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | 35.3s | 1,607 | 4 | 0 |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | 27.1s | 1,118 | 2 | 0 |
| 18 | High-severity macOS bugs | L3 | ◐ PARTIAL | 38.6s | 1,948 | 3 | 0 |
| 19 | Paginated full-Tasks scan | L3 | ✓ PASS | 38.1s | 1,532 | 4 | 0 |
| 20 | Meeting notes mentioning Jared | L4 | ✓ PASS | 22.8s | 944 | 4 | 0 |
| 21 | Press Contacts visibility | L3 | ✗ FAIL | 17.2s | 437 | 2 | 0 |
| 22 | Five most recently edited pages | L2 | ✓ PASS | 19.9s | 608 | 2 | 0 |
| 23 | Append a paragraph to Tomb-3 | L1 | ✓ PASS | 21.9s | 730 | 3 | 0 |
| 24 | Mark BUG-247 Fixed | L2 | ✓ PASS | 70.1s | 2,139 | 9 | 0 |
| 25 | Re-assign BUG-248 to Devon | L2 | ✓ PASS | 86.8s | 2,295 | 9 | 0 |
| 26 | Edit a paragraph block keeping a mention | L3 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 27 | Check off a to_do | L2 | ✓ PASS | 39.0s | 1,488 | 6 | 0 |
| 28 | Delete a divider block | L2 | ✗ FAIL | 60.2s | 2,800 | 6 | 0 |
| 29 | Archive 'Playtest — alpha round 2' | L2 | ✓ PASS | 44.8s | 1,621 | 5 | 0 |
| 30 | Comment on BUG-247 row | L2 | ◐ PARTIAL | 58.3s | 2,011 | 8 | 0 |
| 31 | Comment on callout block B11 | L2 | ◐ PARTIAL | 52.2s | 1,876 | 7 | 0 |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | 48.8s | 1,336 | 7 | 0 |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | 16.5s | 547 | 2 | 0 |
| 34 | Create a new task | L3 | ✓ PASS | 36.8s | 1,194 | 6 | 0 |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | 231.9s | 10,662 | 11 | 0 |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | 35.7s | 1,078 | 4 | 0 |
| 37 | Update Bugs database description | L2 | ✓ PASS | 32.9s | 858 | 4 | 0 |
| 38 | Set page icon | L2 | ✓ PASS | 19.1s | 687 | 3 | 0 |
| 39 | Convert paragraph to heading_2 (delete + append) | L4 | ✗ FAIL | 213.9s | 11,765 | 11 | 0 |
| 40 | Append a nested toggle to Launch 2026 | L3 | ✓ PASS | 24.6s | 1,115 | 3 | 0 |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | 54.1s | 1,977 | 5 | 0 |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | 73.5s | 2,549 | 10 | 0 |
| 43 | Cross-database link | L5 | ◐ PARTIAL | 187.5s | 9,960 | 13 | 0 |
| 44 | Weekly digest page | L5 | ◐ PARTIAL | 79.2s | 4,432 | 9 | 0 |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | 48.5s | 1,763 | 7 | 0 |
| 46 | Meeting note from a template | L4 | ✓ PASS | 75.9s | 3,955 | 12 | 0 |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | 30.2s | 1,789 | 3 | 0 |
| 48 | Archive sweep under Playtest Archive | L4 | ✓ PASS | 35.5s | 1,439 | 5 | 0 |
| 49 | Comment fan-out on blocker bugs | L4 | ✗ FAIL | 58.5s | 2,828 | 6 | 0 |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | 70.2s | 3,428 | 6 | 0 |
| 51 | Read a non-shared page | L2 | ✓ PASS | 41.5s | 1,874 | 4 | 0 |
| 52 | Write to an archived page | L2 | ✓ PASS | 222.2s | 11,698 | 16 | 0 |
| 53 | Property-type violation | L3 | ✗ FAIL | 57.5s | 2,655 | 4 | 0 |
| 54 | Query a non-shared database | L3 | ✓ PASS | 33.5s | 1,506 | 3 | 0 |
| 55 | Resolve a revoked user | L3 | ✓ PASS | 19.1s | 629 | 3 | 0 |
| 56 | Append to a non-shared page | L2 | ✓ PASS | 131.3s | 8,453 | 13 | 0 |
| 57 | Pagination boundary at exact page_size | L3 | ✗ FAIL | 27.7s | 1,172 | 5 | 0 |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | 44.0s | 1,759 | 5 | 0 |

## Initial vs peak context

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List active workspace users | 3 | 11 |
| 2 | Identify the integration's bot user | 3 | 12 |
| 3 | Get my email address | 0 | 0 |
| 4 | Retrieve the Bugs database schema | 3 | 14 |
| 5 | Retrieve a specific bug row | 3 | 30 |
| 6 | Read the Tomb-3 page top-level blocks | 3 | 12 |
| 7 | Paginated children of Team Directory | 3 | 15 |
| 8 | List comments on BUG-247 | 3 | 16 |
| 9 | Resolve a relation property | 3 | 23 |
| 10 | Read to_do checked states | 3 | 23 |
| 11 | Get a teammate's email address | 0 | 0 |
| 12 | List databases shared to the integration | 3 | 14 |
| 13 | Search by title - BUG-247 | 3 | 11 |
| 14 | Search filtered to databases | 3 | 12 |
| 15 | Open blockers in Bugs | 3 | 19 |
| 16 | Tasks Due in next 14 days (calendar) | 3 | 19 |
| 17 | Overdue not-Done tasks | 3 | 13 |
| 18 | High-severity macOS bugs | 3 | 15 |
| 19 | Paginated full-Tasks scan | 3 | 17 |
| 20 | Meeting notes mentioning Jared | 3 | 18 |
| 21 | Press Contacts visibility | 3 | 12 |
| 22 | Five most recently edited pages | 3 | 11 |
| 23 | Append a paragraph to Tomb-3 | 3 | 15 |
| 24 | Mark BUG-247 Fixed | 3 | 26 |
| 25 | Re-assign BUG-248 to Devon | 3 | 30 |
| 26 | Edit a paragraph block keeping a mention | 0 | 0 |
| 27 | Check off a to_do | 3 | 19 |
| 28 | Delete a divider block | 3 | 24 |
| 29 | Archive 'Playtest — alpha round 2' | 3 | 18 |
| 30 | Comment on BUG-247 row | 3 | 22 |
| 31 | Comment on callout block B11 | 3 | 21 |
| 32 | Add a select option to Bugs.Severity | 3 | 23 |
| 33 | Rename Projects (catalog) database | 3 | 14 |
| 34 | Create a new task | 3 | 20 |
| 35 | Unarchive Playtest — alpha round 3 | 3 | 41 |
| 36 | Rename Bugs.Filed property | 3 | 14 |
| 37 | Update Bugs database description | 3 | 15 |
| 38 | Set page icon | 3 | 15 |
| 39 | Convert paragraph to heading_2 (delete + append) | 3 | 38 |
| 40 | Append a nested toggle to Launch 2026 | 3 | 16 |
| 41 | Bulk-update overdue tasks | 3 | 22 |
| 42 | Spin up a new bug end-to-end | 3 | 33 |
| 43 | Cross-database link | 3 | 41 |
| 44 | Weekly digest page | 3 | 29 |
| 45 | Catch-up sweep on overdue In-Progress tasks | 3 | 20 |
| 46 | Meeting note from a template | 3 | 31 |
| 47 | Mention round-up across meetings | 3 | 17 |
| 48 | Archive sweep under Playtest Archive | 3 | 22 |
| 49 | Comment fan-out on blocker bugs | 3 | 26 |
| 50 | End-to-end launch-prep | 3 | 25 |
| 51 | Read a non-shared page | 3 | 19 |
| 52 | Write to an archived page | 3 | 53 |
| 53 | Property-type violation | 3 | 19 |
| 54 | Query a non-shared database | 3 | 16 |
| 55 | Resolve a revoked user | 3 | 14 |
| 56 | Append to a non-shared page | 3 | 5,144 |
| 57 | Pagination boundary at exact page_size | 3 | 20 |
| 58 | Update with a non-existent select option | 3 | 23 |

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 58 |
| Success rate | 62% |
| Passes | 36 |
| Partial | 11 |
| Fails | 10 |
| Errors | 1 |
| Avg initial context | 3 |
| Avg peak context | 108 |
| Avg wall-clock | 57.0s |
| Total tokens | 133,851 |
| Avg tokens/prompt | 2,308 |
| Avg tool calls | 5.19 |
| Total tool failures | 0 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 5 | 60% | 0/2/0 |
| L2 | 24 | 58% | 8/2/0 |
| L3 | 17 | 65% | 1/4/1 |
| L4 | 7 | 71% | 0/2/0 |
| L5 | 5 | 60% | 2/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 12 | 42% | 4/3/0 |
| search | 10 | 60% | 3/1/0 |
| write | 12 | 67% | 2/1/1 |
| workflow | 6 | 67% | 0/2/0 |
| orchestration | 10 | 70% | 2/1/0 |
| edge_case | 8 | 75% | 0/2/0 |

## Notable failures

- **#3 Get my email address** (L1, retrieval) — `FAIL`: Extension prompt requiring read_user_with_email capability. The Notion MCP integration does not expose a method to return the authenticated bot user's email address; retrieveBotUser returns name and avatar but not email, so the capability gap causes a FAIL.
- **#4 Retrieve the Bugs database schema** (L2, retrieval) — `PARTIAL`: Retrieved all properties correctly from the Bugs database, but the schema shows an extra 'Reported 1' date property (a duplicate) that is not in the expected 10-property workspace_state schema; the expected 'Filed' property name maps to 'Reported' in actual data, so property count and naming drifts slightly.
- **#13 Search by title - BUG-247** (L2, search) — `PARTIAL`: Search returned two pages mentioning BUG-247 and the Bugs database, but did not return the actual BUG-247 row (page object in DB_BUGS) since the Notion search API returns title matches not row-level property matches. Results are grounded in tool data but the required BUG-247 row object was not directly returned.
- **#14 Search filtered to databases** (L2, search) — `PARTIAL`: Retrieved all databases with correct sort order, but returned 6 databases including extra 'Projects (catalog)' and duplicate 'Project Catalog' entries beyond the expected 4; DB_PRESS_CONTACTS correctly absent.
- **#26 Edit a paragraph block keeping a mention** (L3, write) — `ERROR`: Infrastructure failure: has_result=false, orchestrator_error='timed out after 300s', no tool calls were made, no usable output produced.
- **#28 Delete a divider block** (L2, write) — `FAIL`: Agent could not find the divider block B13 on the page (workspace_state §6.1 specifies 15 blocks but agent sees only 11 top-level blocks); the delete was never performed as the target block was not located.
- **#35 Unarchive Playtest — alpha round 3** (L3, workflow) — `FAIL`: Agent exhaustively searched the accessible workspace but could not locate the trashed 'Playtest — alpha round 3' page (Notion search API excludes trashed pages); no updatePage was called, so the page remains in_trash=true.
- **#39 Convert paragraph to heading_2 (delete + append)** (L4, workflow) — `FAIL`: Agent could not find block B36 ('Active team members (April 2026):') on the Team Directory page — the page had only 3 blocks due to workspace drift; no delete or append was performed.
