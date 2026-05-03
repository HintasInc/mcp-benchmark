# Notion MCP - Hintas benchmark analysis

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
| Success rate | 80% |
| Passes | 45 |
| Partial | 0 |
| Fails | 8 |
| Errors | 3 |
| Avg initial context | 3 |
| Avg peak context | 631 |
| Avg wall-clock | 69.0s |
| Total tokens | 135,401 |
| Avg tokens/prompt | 2,418 |
| Avg tool calls | 5.27 |
| Total tool failures | 0 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 24 | 75% | 0/5/1 |
| L3 | 18 | 78% | 0/3/1 |
| L4 | 6 | 100% | 0/0/0 |
| L5 | 5 | 80% | 0/0/1 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 10 | 100% | 0/0/0 |
| search | 10 | 90% | 0/1/0 |
| write | 14 | 71% | 0/3/1 |
| workflow | 4 | 75% | 0/1/0 |
| orchestration | 10 | 90% | 0/0/1 |
| edge_case | 8 | 50% | 0/3/1 |

<details>
<summary><h2 style="display:inline">Per-prompt results</h2></summary>

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | List active workspace users | L1 | ✓ PASS | 20.2s | 633 | 2 | 0 |
| 2 | Identify the integration's bot user | L1 | ✓ PASS | 18.9s | 377 | 2 | 0 |
| 4 | Retrieve the Bugs database schema | L2 | ✓ PASS | 43.2s | 1,417 | 4 | 0 |
| 5 | Retrieve a specific bug row | L2 | ✓ PASS | 29.8s | 936 | 3 | 0 |
| 6 | Read the Tomb-3 page top-level blocks | L2 | ✓ PASS | 43.2s | 1,966 | 5 | 0 |
| 7 | Paginated children of Team Directory | L2 | ✓ PASS | 30.1s | 853 | 3 | 0 |
| 8 | List comments on BUG-247 | L2 | ✓ PASS | 74.8s | 3,078 | 9 | 0 |
| 9 | Resolve a relation property | L3 | ✓ PASS | 69.2s | 2,890 | 8 | 0 |
| 10 | Read to_do checked states | L2 | ✓ PASS | 37.2s | 972 | 2 | 0 |
| 12 | List databases shared to the integration | L2 | ✓ PASS | 27.6s | 549 | 3 | 0 |
| 13 | Search by title — BUG-247 | L2 | ✓ PASS | 41.0s | 1,202 | 5 | 0 |
| 14 | Search filtered to databases | L2 | ✓ PASS | 66.8s | 2,133 | 6 | 0 |
| 15 | Open blockers in Bugs | L2 | ✓ PASS | 71.5s | 2,258 | 4 | 0 |
| 16 | Tasks Due in next 14 days (calendar) | L3 | ✓ PASS | 39.3s | 1,480 | 3 | 0 |
| 17 | Overdue not-Done tasks | L3 | ✓ PASS | 29.8s | 1,132 | 2 | 0 |
| 18 | High-severity macOS bugs | L3 | ✓ PASS | 43.3s | 1,818 | 4 | 0 |
| 19 | Paginated full-Tasks scan | L3 | ✓ PASS | 43.6s | 1,509 | 5 | 0 |
| 20 | Meeting notes mentioning Jared | L4 | ✓ PASS | 32.0s | 1,229 | 4 | 0 |
| 21 | Press Contacts visibility | L3 | ✗ FAIL | 26.8s | 466 | 3 | 0 |
| 22 | Five most recently edited pages | L2 | ✓ PASS | 21.3s | 489 | 2 | 0 |
| 23 | Append a paragraph to Tomb-3 | L1 | ✓ PASS | 30.1s | 740 | 3 | 0 |
| 24 | Mark BUG-247 Fixed | L2 | ✓ PASS | 79.8s | 3,109 | 9 | 0 |
| 25 | Re-assign BUG-248 to Devon | L2 | ✓ PASS | 75.0s | 3,252 | 15 | 0 |
| 26 | Edit a paragraph block keeping a mention | L3 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 27 | Check off a to_do | L2 | ✓ PASS | 79.4s | 3,113 | 6 | 0 |
| 28 | Delete a divider block | L2 | ✗ FAIL | 82.5s | 4,241 | 6 | 0 |
| 29 | Archive a stale page | L2 | ✓ PASS | 23.6s | 883 | 5 | 0 |
| 30 | Comment on BUG-247 | L2 | ✗ FAIL | 79.9s | 4,504 | 6 | 0 |
| 31 | Comment on a specific block | L3 | ✓ PASS | 110.5s | 5,410 | 8 | 0 |
| 32 | Add a select option to Bugs.Severity | L3 | ✓ PASS | 22.1s | 928 | 4 | 0 |
| 33 | Rename Projects (catalog) database | L2 | ✓ PASS | 16.4s | 567 | 2 | 0 |
| 34 | Create a new task | L3 | ✓ PASS | 43.8s | 1,374 | 6 | 0 |
| 35 | Unarchive Playtest — alpha round 3 | L3 | ✗ FAIL | 147.7s | 6,474 | 9 | 0 |
| 36 | Rename Bugs.Filed property | L3 | ✓ PASS | 30.4s | 1,119 | 5 | 0 |
| 37 | Update Bugs database description | L2 | ✓ PASS | 34.6s | 807 | 4 | 0 |
| 38 | Set page icon | L2 | ✗ FAIL | 22.8s | 507 | 3 | 0 |
| 39 | Convert paragraph to heading_2 (delete + append) | L3 | ✓ PASS | 292.9s | 14,864 | 14 | 0 |
| 40 | Append a nested toggle to Launch 2026 | L3 | ✓ PASS | 26.9s | 1,059 | 3 | 0 |
| 41 | Bulk-update overdue tasks | L4 | ✓ PASS | 55.2s | 7,422 | 8 | 0 |
| 42 | Spin up a new bug end-to-end | L5 | ✓ PASS | 57.9s | 6,247 | 7 | 0 |
| 43 | Cross-database link | L5 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 44 | Weekly digest page | L5 | ✓ PASS | 110.5s | 5,689 | 12 | 0 |
| 45 | Catch-up sweep on overdue In-Progress tasks | L5 | ✓ PASS | 64.2s | 2,328 | 10 | 0 |
| 46 | Meeting note from a template | L4 | ✓ PASS | 177.0s | 9,203 | 19 | 0 |
| 47 | Mention round-up across meetings | L4 | ✓ PASS | 39.4s | 2,002 | 3 | 0 |
| 48 | Archive sweep under Playtest Archive | L4 | ✓ PASS | 40.7s | 1,476 | 4 | 0 |
| 49 | Comment fan-out on blocker bugs | L4 | ✓ PASS | 48.0s | 2,308 | 5 | 0 |
| 50 | End-to-end launch-prep | L5 | ✓ PASS | 53.9s | 2,827 | 5 | 0 |
| 51 | Read a non-shared page | L2 | ✗ FAIL | 50.2s | 2,285 | 8 | 0 |
| 52 | Write to an archived page | L2 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 53 | Property-type violation | L3 | ✓ PASS | 47.6s | 1,788 | 4 | 0 |
| 54 | Read a non-shared database | L2 | ✗ FAIL | 27.6s | 1,376 | 3 | 0 |
| 55 | Mention a user that does not exist | L2 | ✓ PASS | 41.3s | 1,316 | 7 | 0 |
| 56 | Append to a non-shared page | L3 | ✗ FAIL | 30.9s | 1,330 | 4 | 0 |
| 57 | Pagination boundary at exact page_size | L3 | ✓ PASS | 37.6s | 4,001 | 3 | 0 |
| 58 | Update with a non-existent select option | L3 | ✓ PASS | 74.9s | 3,465 | 6 | 0 |

</details>

<details>
<summary><h2 style="display:inline">Initial vs peak context</h2></summary>

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | List active workspace users | 3 | 11 |
| 2 | Identify the integration's bot user | 3 | 11 |
| 4 | Retrieve the Bugs database schema | 3 | 14 |
| 5 | Retrieve a specific bug row | 3 | 16 |
| 6 | Read the Tomb-3 page top-level blocks | 3 | 21 |
| 7 | Paginated children of Team Directory | 3 | 15 |
| 8 | List comments on BUG-247 | 3 | 31 |
| 9 | Resolve a relation property | 3 | 25 |
| 10 | Read to_do checked states | 3 | 12 |
| 12 | List databases shared to the integration | 3 | 14 |
| 13 | Search by title — BUG-247 | 3 | 18 |
| 14 | Search filtered to databases | 3 | 24 |
| 15 | Open blockers in Bugs | 3 | 20 |
| 16 | Tasks Due in next 14 days (calendar) | 3 | 16 |
| 17 | Overdue not-Done tasks | 3 | 12 |
| 18 | High-severity macOS bugs | 3 | 18 |
| 19 | Paginated full-Tasks scan | 3 | 22 |
| 20 | Meeting notes mentioning Jared | 3 | 19 |
| 21 | Press Contacts visibility | 3 | 12 |
| 22 | Five most recently edited pages | 3 | 11 |
| 23 | Append a paragraph to Tomb-3 | 3 | 15 |
| 24 | Mark BUG-247 Fixed | 3 | 30 |
| 25 | Re-assign BUG-248 to Devon | 3 | 42 |
| 26 | Edit a paragraph block keeping a mention | 0 | 0 |
| 27 | Check off a to_do | 3 | 25 |
| 28 | Delete a divider block | 3 | 26 |
| 29 | Archive a stale page | 3 | 18 |
| 30 | Comment on BUG-247 | 3 | 24 |
| 31 | Comment on a specific block | 3 | 31 |
| 32 | Add a select option to Bugs.Severity | 3 | 18 |
| 33 | Rename Projects (catalog) database | 3 | 12 |
| 34 | Create a new task | 3 | 21 |
| 35 | Unarchive Playtest — alpha round 3 | 3 | 35 |
| 36 | Rename Bugs.Filed property | 3 | 15 |
| 37 | Update Bugs database description | 3 | 15 |
| 38 | Set page icon | 3 | 15 |
| 39 | Convert paragraph to heading_2 (delete + append) | 3 | 49 |
| 40 | Append a nested toggle to Launch 2026 | 3 | 14 |
| 41 | Bulk-update overdue tasks | 3 | 15,491 |
| 42 | Spin up a new bug end-to-end | 3 | 12,640 |
| 43 | Cross-database link | 0 | 0 |
| 44 | Weekly digest page | 3 | 35 |
| 45 | Catch-up sweep on overdue In-Progress tasks | 3 | 29 |
| 46 | Meeting note from a template | 3 | 58 |
| 47 | Mention round-up across meetings | 3 | 17 |
| 48 | Archive sweep under Playtest Archive | 3 | 19 |
| 49 | Comment fan-out on blocker bugs | 3 | 23 |
| 50 | End-to-end launch-prep | 3 | 22 |
| 51 | Read a non-shared page | 3 | 27 |
| 52 | Write to an archived page | 0 | 0 |
| 53 | Property-type violation | 3 | 20 |
| 54 | Read a non-shared database | 3 | 12 |
| 55 | Mention a user that does not exist | 3 | 18 |
| 56 | Append to a non-shared page | 3 | 14 |
| 57 | Pagination boundary at exact page_size | 3 | 6,155 |
| 58 | Update with a non-existent select option | 3 | 23 |

</details>

## Notable failures

- **#21 Press Contacts visibility** (L3, search) — `FAIL`: Access-boundary prompt: the integration cannot see the Press Contacts database. The agent searched and returned 0 results, reporting cleanly that the database is not accessible — no fabrication. Per grading rules, any outcome on access-boundary prompts is FAIL.
- **#26 Edit a paragraph block keeping a mention** (L3, write) — `ERROR`: Orchestrator timed out after 300 seconds before the agent produced any output; no tool calls were made and no result was returned.
- **#28 Delete a divider block** (L2, write) — `FAIL`: The divider block B13 does not exist on the Tomb-3 Level Design page; the workspace has drifted and the block was absent before the run. The agent correctly performed a full recursive scan, confirmed no divider blocks exist at any level, and reported the situation accurately — but the required target object was missing so the deletion could not be performed.
- **#35 Unarchive Playtest — alpha round 3** (L3, workflow) — `FAIL`: Agent correctly identified that the Notion API excludes trashed pages from search and block-children responses, making it impossible to locate the page ID needed to call `updatePage` with `archived: false`. Agent was unable to restore the page and correctly asked the user for the page ID instead of fabricating a result.
- **#43 Cross-database link** (L5, orchestration) — `ERROR`: Orchestrator timed out after 300s before the agent made any tool calls (0 complete calls, 0 tokens consumed). No work was performed.
- **#51 Read a non-shared page** (L2, edge_case) — `FAIL`: Access boundary: '🔒 Leads-only' page does not appear in the integration's search results (not shared). Agent correctly reported no access and did not fabricate contents, but the primary task (reading page contents) hit a hard access boundary.
- **#52 Write to an archived page** (L2, edge_case) — `ERROR`: Orchestrator timed out after 300s before the agent made any tool calls (0 complete calls, 0 tokens consumed). No work was performed.
- **#30 Comment on BUG-247** (L2, write) — `FAIL`: Comment was posted on the wrong page: 'Verify BUG-247 fix on macOS 14.4' (a Tasks row) instead of the BUG-247 Bugs database row ('Save-file corruption on macOS', ID 3504da5e-14d2-81c3-bceb-ec22081daee1). The agent relied only on title search for 'BUG-247' and never queried the Bugs database by Bug ID property to locate the actual bug row.
