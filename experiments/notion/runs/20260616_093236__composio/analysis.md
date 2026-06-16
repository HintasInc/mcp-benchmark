# Notion MCP - Notion MCP - Composio benchmark analysis

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
| Success rate | 79% |
| Passes | 44 |
| Partial | 2 |
| Fails | 10 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 607 |
| Avg wall-clock | 47.2s |
| Total tokens | 109,016 |
| Avg tokens/prompt | 1,947 |
| Avg tool calls | 4.59 |
| Total tool failures | 2 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 3 | 100% | 0/0/0 |
| L2 | 23 | 87% | 0/3/0 |
| L3 | 18 | 61% | 1/6/0 |
| L4 | 7 | 86% | 0/1/0 |
| L5 | 5 | 80% | 1/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 10 | 100% | 0/0/0 |
| search | 10 | 90% | 0/1/0 |
| write | 12 | 75% | 0/3/0 |
| workflow | 6 | 50% | 1/2/0 |
| orchestration | 10 | 90% | 1/0/0 |
| edge_case | 8 | 50% | 0/4/0 |

## Notable failures

- **#21 Press Contacts visibility** (L3, search) — `FAIL`: Access-boundary prompt: DB_PRESS_CONTACTS is not shared with this integration, so the task could not be completed regardless of outcome. NOTION_SEARCH_NOTION_PAGE returned empty results and the agent correctly reported the boundary without fabricating content (clean failure mode), but per grading rules all outcomes for access-boundary prompts are FAIL.
- **#26 Edit a paragraph block keeping a mention** (L3, write) — `FAIL`: Prompt intent (update block B02 date to 2026-04-19 while preserving mention.user for @Miranda) was not achieved due to two compounding issues: (1) env rejection — the agent fetched all blocks on the 'Tomb-3 Level Design' page (`NOTION_FETCH_BLOCK_CONTENTS`, has_more: false) and found no paragraph block at all, let alone B02; (2) capability gap — `NOTION_UPDATE_BLOCK` accepts only plain-text content (no rich_text array), so even if B02 were present, the structured mention.user could not be preserved.
- **#28 Delete a divider block** (L2, write) — `FAIL`: Prompt intent (delete divider block B13 from 'Tomb-3 Level Design') was not achieved due to env rejection: the agent fetched all 11 top-level blocks and 3 toggle-nested image blocks via `NOTION_FETCH_BLOCK_CONTENTS` (has_more: false on both calls) and found no divider-type block anywhere on the page, so the deletion could not be performed.
- **#35 Unarchive Playtest — alpha round 3** (L3, workflow) — `FAIL`: The prompt's intent was not achieved. The agent called NOTION_SEARCH_NOTION_PAGE but trashed pages are not indexed by Notion's search API, and there is no list-trash or restore-from-trash endpoint in the public API (version 2022-06-28) — a capability gap the agent correctly identified. The operation could not proceed without knowing the page ID in advance.
- **#39 Convert paragraph to heading_2 (delete + append)** (L4, workflow) — `FAIL`: The prompt's intent was not achieved. The agent called NOTION_FETCH_BLOCK_CONTENTS on the Team Directory page and received only 3 blocks (heading_1 'Team Directory' and two dividers) with has_more=false; NOTION_GET_PAGE_MARKDOWN confirmed the same sparse content. Block B36 ('Active team members (April 2026):') was not present, so neither the delete step nor the heading_2 append could proceed — env rejection blocking the task due to missing block content.
- **#43 Cross-database link** (L5, orchestration) — `PARTIAL`: Intent was partially achieved. The task 'Investigate BUG-248 collider' was created with correct Owner (Devon Park), Due, Status, Priority, and Tags (eng, qa), and BUG-248's Related Task relation was successfully updated to point to the new task. However, the Project field was left empty because querying the Projects database returned only 'Lisbon offsite' — the Tomb-3 project was not accessible to the integration (access-boundary env rejection), leaving a required-output gap for the Project relation.
- **#51 Read a non-shared page** (L2, edge_case) — `FAIL`: Access-boundary prompt: P08_LEADS_ONLY is deliberately not shared with the integration, so the task (reading its contents) cannot be completed — this is a FAIL per access-boundary grading rules regardless of how cleanly the agent handles it. The agent correctly acknowledged the boundary ('Access denied — cannot read 🔒 Leads-only'), search returned 'Leads sync' (a different page) and not P08_LEADS_ONLY, and no fabricated content was produced — this is the cleaner failure mode, but the verdict remains FAIL.
- **#54 Query a non-shared database** (L3, edge_case) — `FAIL`: Access-boundary prompt: DB_PRESS_CONTACTS is deliberately not shared with the integration, so the task (querying it) cannot be completed — this is a FAIL per access-boundary grading rules regardless of reporting quality. The agent made zero tool calls and reasoned directly from system context that the database was unshared, reporting cleanly ('DB_PRESS_CONTACTS is not shared with the Hintas Agent integration'); no fabricated content was produced — this is the cleaner failure mode, but the verdict is FAIL.
