# Notion MCP - Notion MCP - Executor benchmark analysis

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
| Success rate | 71% |
| Passes | 40 |
| Partial | 3 |
| Fails | 13 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 25 |
| Avg wall-clock | 59.0s |
| Total tokens | 154,057 |
| Avg tokens/prompt | 2,751 |
| Avg tool calls | 10.04 |
| Total tool failures | 10 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 67% | 1/0/0 |
| L2 | 23 | 78% | 0/5/0 |
| L3 | 18 | 61% | 0/7/0 |
| L4 | 7 | 86% | 0/1/0 |
| L5 | 5 | 60% | 2/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 10 | 80% | 1/1/0 |
| search | 10 | 90% | 0/1/0 |
| write | 12 | 67% | 0/4/0 |
| workflow | 6 | 67% | 0/2/0 |
| orchestration | 10 | 80% | 2/0/0 |
| edge_case | 8 | 38% | 0/5/0 |

## Notable failures

- **#2 Identify the integration's bot user** (L1, retrieval) — `PARTIAL`: The agent called `retrieveBotUser` and correctly returned the bot name 'Hintas Agent', but the API response showed `owner.type: 'workspace'` with no individual user ID — the required owner user ID was missing (required-output gap); the agent accurately reported this limitation rather than fabricating.
- **#8 List comments on BUG-247** (L2, retrieval) — `FAIL`: The agent retrieved comments from the wrong page ('Verify BUG-247 fix on macOS 14.4', a task page) rather than the BUG-247 row in the Bugs database; it found 3 identical comments ('Launch blocker — confirm status by 2026-04-22.') that are unrelated to the expected CMT01/CMT02 from the actual bug row — this is a required-output gap caused by incorrect page identification.
- **#21 Press Contacts visibility** (L3, search) — `FAIL`: Access-boundary prompt: DB_PRESS_CONTACTS is not shared with the integration. The agent correctly searched, received empty results, and reported the access limitation without fabricating content — but this prompt class always yields FAIL because the data is by design inaccessible.
- **#25 Re-assign BUG-248 to Devon** (L2, write) — `FAIL`: The agent searched for BUG-248 and found the Bugs database in results but never queried it using a 'Bug ID equals BUG-248' filter (the same technique that worked for BUG-247 in p24). It checked only the Tasks database and general search, concluded BUG-248 was inaccessible, and never retrieved Devon's user_id via listUsers or attempted updatePage.
- **#26 Edit a paragraph block keeping a mention** (L3, write) — `FAIL`: Block B02 ('Owner: @Miranda. Last updated: 2026-04-15.') was not present in the live Tomb-3 Level Design page at run time — the agent retrieved all 11 blocks and none matched the target paragraph text. The success criteria require an actual in-place edit of B02, which could not occur.
- **#35 Unarchive Playtest — alpha round 3** (L3, workflow) — `FAIL`: The Notion search API excludes in_trash=true pages, so the agent could not discover P10_PLAYTEST_A3's ID. It correctly attempted parent-page navigation (found round 2's parent, listed its children) but retrieveBlockChildren also excludes trashed blocks — only round 2 appeared. With no available API path to enumerate trash contents, the restore could not proceed.
- **#39 Convert paragraph to heading_2 (delete + append)** (L4, workflow) — `FAIL`: Block B36 ('Active team members (April 2026):' paragraph) was absent from the live Team Directory page — the agent retrieved all 3 blocks (heading_1, divider, divider; has_more=false) and confirmed no nested children. The delete+append workaround could not proceed without the precondition block existing.
- **#43 Cross-database link: create task from bug** (L5, orchestration) — `PARTIAL`: The agent created task 'Investigate BUG-248 collider' with Owner=Devon, Due=2026-04-23, Status='Up Next', Priority=P1, Tags=[eng,qa] and updated BUG-248's Related Task relation to the new task — 5 of 6 required fields correct. The Project field was left empty because Tomb-3 was not visible to the integration (only 'Lisbon offsite' appeared in scope).
