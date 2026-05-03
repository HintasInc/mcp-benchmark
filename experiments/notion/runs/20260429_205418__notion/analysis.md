# Notion MCP - Notion's official MCP benchmark analysis

**Scope:** 56 prompts.

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 56 |
| Success rate | 68% |
| Passes | 38 |
| Partial | 4 |
| Fails | 14 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 585 |
| Avg wall-clock | 55.0s |
| Total tokens | 158,967 |
| Avg tokens/prompt | 2,839 |
| Avg tool calls | 7.34 |
| Total tool failures | 12 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 23 | 70% | 1/6/0 |
| L3 | 18 | 56% | 2/6/0 |
| L4 | 7 | 57% | 1/2/0 |
| L5 | 5 | 100% | 0/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 10 | 80% | 0/2/0 |
| search | 10 | 80% | 0/2/0 |
| write | 12 | 67% | 2/2/0 |
| workflow | 6 | 50% | 1/2/0 |
| orchestration | 10 | 80% | 1/1/0 |
| edge_case | 8 | 38% | 0/5/0 |

<details>
<summary><h2 style="display:inline">Per-prompt results</h2></summary>

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List active workspace users | L1 | ✓ PASS | 14.3s | 466 | 1 | 0 |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | 20.9s | 768 | 2 | 0 |
| 4 | Retrieve the Bugs database schema | L2 | ✓ PASS | 14.1s | 490 | 2 | 0 |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | 19.8s | 616 | 4 | 0 |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ✓ PASS | 15.1s | 570 | 2 | 0 |
| 7 | Paginated children of Team Directory | L2 | ✗ FAIL | 26.0s | 1,222 | 2 | 0 |
| 8 | List comments on BUG-247 | L2 | ✓ PASS | 22.0s | 933 | 2 | 0 |
| 9 | Resolve a relation property | L3 | ✓ PASS | 27.8s | 405 | 3 | 0 |
| 10 | Read to_do checked states | L2 | ✓ PASS | 19.4s | 365 | 2 | 0 |
| 12 | List databases shared to the integration | L2 | ✗ FAIL | 23.5s | 714 | 2 | 0 |
| 13 | Search by title — BUG-247 | L2 | ✓ PASS | 18.7s | 467 | 1 | 0 |
| 14 | Search filtered to databases | L2 | ✓ PASS | 124.7s | 5,297 | 24 | 0 |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | 43.8s | 2,828 | 12 | 1 |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | 67.8s | 4,082 | 23 | 1 |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | 116.7s | 4,265 | 18 | 0 |
| 18 | High-severity macOS bugs | L3 | ✓ PASS | 95.1s | 4,809 | 11 | 0 |
| 19 | Paginated full-Tasks scan | L3 | ✗ FAIL | 201.1s | 10,722 | 17 | 1 |
| 20 | Meeting notes mentioning Jared | L4 | ✓ PASS | 64.0s | 4,226 | 16 | 0 |
| 21 | Press Contacts visibility | L3 | ✗ FAIL | 24.3s | 424 | 2 | 0 |
| 22 | Five most recently edited pages | L2 | ✓ PASS | 22.6s | 929 | 1 | 0 |
| 23 | Append a paragraph to Tomb-3 | L1 | ✓ PASS | 20.5s | 584 | 3 | 0 |
| 24 | Mark BUG-247 Fixed | L2 | ✓ PASS | 10.7s | 318 | 2 | 0 |
| 25 | Re-assign BUG-248 to Devon | L2 | ✓ PASS | 21.7s | 755 | 3 | 0 |
| 26 | Edit a paragraph block keeping a mention | L3 | ✗ FAIL | 109.0s | 5,456 | 5 | 0 |
| 27 | Check off a to_do | L2 | ✓ PASS | 17.1s | 731 | 2 | 0 |
| 28 | Delete a divider block | L2 | ✗ FAIL | 20.8s | 908 | 2 | 0 |
| 29 | Archive a stale page | L2 | ◐ PARTIAL | 39.4s | 1,564 | 3 | 0 |
| 30 | Comment on BUG-247 | L2 | ✓ PASS | 12.7s | 356 | 2 | 0 |
| 31 | Comment on a specific block | L3 | ◐ PARTIAL | 88.7s | 5,527 | 4 | 0 |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | 13.1s | 463 | 2 | 0 |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | 16.1s | 294 | 2 | 0 |
| 34 | Create a new task | L3 | ✓ PASS | 31.9s | 712 | 4 | 0 |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | 58.9s | 2,821 | 4 | 0 |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | 15.8s | 512 | 2 | 0 |
| 37 | Update Bugs database description | L2 | ✓ PASS | 14.1s | 407 | 3 | 0 |
| 38 | Set page icon | L2 | ✓ PASS | 11.0s | 372 | 2 | 0 |
| 39 | Convert paragraph to heading_2 (delete + append) | L4 | ✗ FAIL | 89.6s | 4,619 | 8 | 1 |
| 40 | Append a nested toggle to Launch 2026 | L3 | ◐ PARTIAL | 22.6s | 643 | 4 | 0 |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | 57.3s | 4,209 | 17 | 0 |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | 28.4s | 1,213 | 6 | 0 |
| 43 | Cross-database link | L5 | ✓ PASS | 107.3s | 7,224 | 18 | 0 |
| 44 | Weekly digest page | L5 | ✓ PASS | 154.6s | 10,968 | 23 | 2 |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | 130.3s | 6,614 | 25 | 1 |
| 46 | Meeting note from a template | L4 | ◐ PARTIAL | 207.5s | 14,150 | 14 | 1 |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | 104.2s | 6,535 | 23 | 0 |
| 48 | Archive sweep under Playtest Archive | L4 | ✗ FAIL | 187.5s | 12,905 | 0 | 0 |
| 49 | Comment fan-out on blocker bugs | L4 | ✓ PASS | 53.4s | 3,024 | 14 | 1 |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | 124.8s | 7,206 | 31 | 1 |
| 51 | Read a non-shared page | L2 | ✗ FAIL | 12.4s | 346 | 2 | 0 |
| 52 | Write to an archived page | L2 | ✗ FAIL | 133.3s | 5,063 | 15 | 0 |
| 53 | Property-type violation | L3 | ✓ PASS | 23.2s | 559 | 3 | 1 |
| 54 | Query a non-shared database | L3 | ✗ FAIL | 38.1s | 1,622 | 6 | 0 |
| 55 | Resolve a revoked user | L3 | ✓ PASS | 12.2s | 191 | 1 | 0 |
| 56 | Append to a non-shared page | L2 | ✗ FAIL | 53.2s | 2,862 | 4 | 1 |
| 57 | Pagination boundary at exact page_size | L3 | ✗ FAIL | 27.2s | 1,275 | 2 | 0 |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | 31.8s | 1,361 | 3 | 0 |

</details>

<details>
<summary><h2 style="display:inline">Initial vs peak context</h2></summary>

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List active workspace users | 3 | 10 |
| 2 | Identify the integration's bot user | 3 | 14 |
| 4 | Retrieve the Bugs database schema | 3 | 11 |
| 5 | Retrieve a specific bug row | 3 | 16 |
| 6 | Read the Tomb-3 page top-level blocks | 3 | 12 |
| 7 | Paginated children of Team Directory | 3 | 13 |
| 8 | List comments on BUG-247 | 3 | 13 |
| 9 | Resolve a relation property | 3 | 14 |
| 10 | Read to_do checked states | 3 | 11 |
| 12 | List databases shared to the integration | 3 | 14 |
| 13 | Search by title — BUG-247 | 3 | 11 |
| 14 | Search filtered to databases | 3 | 49 |
| 15 | Open blockers in Bugs | 3 | 1,852 |
| 16 | Tasks Due in next 14 days (calendar) | 3 | 245 |
| 17 | Overdue not-Done tasks | 3 | 36 |
| 18 | High-severity macOS bugs | 3 | 28 |
| 19 | Paginated full-Tasks scan | 3 | 44 |
| 20 | Meeting notes mentioning Jared | 3 | 5,762 |
| 21 | Press Contacts visibility | 3 | 12 |
| 22 | Five most recently edited pages | 3 | 11 |
| 23 | Append a paragraph to Tomb-3 | 3 | 14 |
| 24 | Mark BUG-247 Fixed | 3 | 12 |
| 25 | Re-assign BUG-248 to Devon | 3 | 13 |
| 26 | Edit a paragraph block keeping a mention | 3 | 21 |
| 27 | Check off a to_do | 3 | 13 |
| 28 | Delete a divider block | 3 | 14 |
| 29 | Archive a stale page | 3 | 16 |
| 30 | Comment on BUG-247 | 3 | 12 |
| 31 | Comment on a specific block | 3 | 18 |
| 32 | Add a select option to Bugs.Severity | 3 | 12 |
| 33 | Rename Projects (catalog) database | 3 | 12 |
| 34 | Create a new task | 3 | 16 |
| 35 | Unarchive Playtest — alpha round 3 | 3 | 20 |
| 36 | Rename Bugs.Filed property | 3 | 12 |
| 37 | Update Bugs database description | 3 | 13 |
| 38 | Set page icon | 3 | 12 |
| 39 | Convert paragraph to heading_2 (delete + append) | 3 | 29 |
| 40 | Append a nested toggle to Launch 2026 | 3 | 17 |
| 41 | Bulk-update overdue tasks | 3 | 2,390 |
| 42 | Spin up a new bug end-to-end | 3 | 20 |
| 43 | Cross-database link | 3 | 13,557 |
| 44 | Weekly digest page | 3 | 7,784 |
| 45 | Catch-up sweep on overdue In-Progress tasks | 3 | 56 |
| 46 | Meeting note from a template | 3 | 41 |
| 47 | Mention round-up across meetings | 3 | 47 |
| 48 | Archive sweep under Playtest Archive | 3 | 138 |
| 49 | Comment fan-out on blocker bugs | 3 | 38 |
| 50 | End-to-end launch-prep | 3 | 58 |
| 51 | Read a non-shared page | 3 | 12 |
| 52 | Write to an archived page | 3 | 49 |
| 53 | Property-type violation | 3 | 14 |
| 54 | Query a non-shared database | 3 | 22 |
| 55 | Resolve a revoked user | 3 | 10 |
| 56 | Append to a non-shared page | 3 | 18 |
| 57 | Pagination boundary at exact page_size | 3 | 13 |
| 58 | Update with a non-existent select option | 3 | 15 |

</details>

## Notable failures

- **#7 Paginated children of Team Directory** (L2, retrieval) — `FAIL`: The prompt requires explicit pagination with page_size=10 and reporting the number of retrieveBlockChildren calls, which Notion MCP doesn't expose — the agent acknowledged this capability gap and fell back to notion-fetch, reporting only 3 blocks and 1 call instead of the expected 11 blocks and 2 calls.
- **#12 List databases shared to the integration** (L2, retrieval) — `FAIL`: The agent returned 'Press Contacts' in the list of accessible databases, but per the access-boundary rules DB_PRESS_CONTACTS must not appear as it is not shared with the integration; this is a filtering miss because the Notion MCP search returned it and the agent included it without verifying scope.
- **#19 Paginated full-Tasks scan** (L3, search) — `FAIL`: Notion MCP does not expose a page_size parameter for queryDatabase or notion-fetch; agent used keyword searches and found only 7 tasks vs the required 12, and could not demonstrate the ceil(12/5)=3 call pagination contract; both total-count and call-count success criteria fail.
- **#21 Press Contacts visibility** (L3, search) — `FAIL`: Access boundary violation — notion-search returned DB_PRESS_CONTACTS and notion-fetch successfully retrieved its schema; per workspace_state §3.2 + §10.5 the integration is not shared to DB_PRESS_CONTACTS and all API calls should return object_not_found.
- **#26 Edit a paragraph block keeping a mention** (L3, write) — `FAIL`: Agent could not locate block B02 by its workspace_state block-id (notion-fetch renders markdown without exposing individual block IDs), so no update was made; the absence of a notion-update-page call confirms the required mutation never occurred.
- **#28 Delete a divider block** (L2, write) — `FAIL`: Agent fetched Tomb-3 content but notion-fetch renders pages as markdown which does not expose individual block IDs; without being able to identify and target B13 by block-id, no deletion was attempted — no notion-update-page call was made.
- **#35 Unarchive Playtest — alpha round 3** (L3, workflow) — `FAIL`: Archived pages do not appear in notion-search results; agent searched and fetched but could not locate P10_PLAYTEST_A3, so no unarchive was attempted — no notion-update-page call was made; the capability gap (no way to address a trashed page without its ID) prevented completion.
- **#39 Convert paragraph to heading_2 (delete + append)** (L4, workflow) — `FAIL`: Agent could not locate block B36 by its workspace_state block-id (notion-fetch renders markdown without exposing individual block IDs), so the required delete step failed; 1 failed call confirms an error during the attempted update; the delete+append sequence required by the API's block-type immutability constraint was not completed.
