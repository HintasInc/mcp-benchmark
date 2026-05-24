# Gmail MCP - Gmail MCP - Official benchmark analysis

**Scope:** 42 prompts.

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met; partial multi-step or one criterion missed.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 42 |
| Success rate | 50% |
| Passes | 21 |
| Partial | 8 |
| Fails | 13 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 44 |
| Avg wall-clock | 33.5s |
| Total tokens | 46,845 |
| Avg tokens/prompt | 1,115 |
| Avg tool calls | 2.81 |
| Total tool failures | 3 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L1 | 6 | 50% | 2/1/0 |
| L2 | 19 | 63% | 0/7/0 |
| L3 | 11 | 45% | 2/4/0 |
| L4 | 5 | 20% | 3/1/0 |
| L5 | 1 | 0% | 1/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 9 | 67% | 2/1/0 |
| search | 8 | 62% | 2/1/0 |
| write | 17 | 41% | 2/8/0 |
| orchestration | 5 | 20% | 2/2/0 |
| edge_case | 3 | 67% | 0/1/0 |

## Notable failures

- **#1 Who am I?** (L1, retrieval) — `PARTIAL`: Agent identified the correct email address (saranyasapkota0@gmail.com) and reported 20 threads / 22 messages, but derived all values from search_threads enumeration rather than calling users.getProfile. The success criterion requires email and counts to be sourced from users.getProfile on userId='me'; inferring the email from toRecipients headers and manually summing messages across paginated search results does not satisfy the grading rule.
- **#2 List all labels** (L1, retrieval) — `PARTIAL`: list_labels returned all 6 user-defined labels correctly (Hintas, Hintas/Triage, Hintas/Follow-up, Receipts, Press, Ops/Bugs). System labels were added from model training knowledge rather than the tool — CATEGORY_PERSONAL, CATEGORY_UPDATES, CATEGORY_FORUMS, CATEGORY_PROMOTIONS, and CATEGORY_SOCIAL are absent from the output. The success criterion requires at least one CATEGORY_* label to appear, sourced from labels.list.
- **#6 Threads with attachments** (L2, search) — `FAIL`: Date-resolution failure: the agent anchored its 30-day lookback to host wall-clock May 20, 2026, and searched after:2026/04/20. Under benchmark_now (April 19, 2026), the correct 30-day cutoff is March 20 — which would include the BUG-247 thread containing an attachment dated April 16. The agent's search window excluded this thread, producing an incorrect empty result for the attachment query.
- **#11 Rename a label** (L2, write) — `FAIL`: list_labels succeeded and identified the target label. update_label returned HTTP 403 'The caller does not have permission' — the OAuth token lacks the gmail.modify scope required for label mutation. The rename was not completed.
- **#16 Star a thread** (L2, write) — `FAIL`: Date-resolution failure: agent searched 'from:miranda after:2026/05/06' (14 days before host wall-clock May 20). Under benchmark_now (April 19), the correct 14-day window covers April 5–19, which includes Miranda's April 17 thread. The shifted search window excluded this thread, causing the agent to report no matching threads and take no action.
- **#26 Triage today's unread** (L3, orchestration) — `FAIL`: Date-resolution failure: agent searched 'after:2026/05/20 before:2026/05/21' (host wall-clock 'today'). Under benchmark_now, 'today' is April 19, 2026, which has 3 unread threads (Sprint demo, Build green, Q2 roadmap). The shifted date window returned no results, and triage of the correct threads was not performed.
- **#30 Threads with no reply from me** (L4, search) — `PARTIAL`: Date-resolution failure: newer_than:30d against host wall-clock (May 20) returned empty because all seeded threads are from April. Agent compensated by broadening to newer_than:35d and found 10 threads from April 15–19. Content is correct and grounded in tool data, but the agent frames the result as 'outside the 30-day window' — the task's scope was not met precisely even though the final thread list is accurate under a shifted window.
- **#44 Operate on a trashed thread** (L2, edge_case) — `FAIL`: Agent searched for the literal string 'TH_OLD_PROMO' in trash instead of searching in:trash generically to discover what is there. The actual trashed thread is 'Spring sale — 30% off through April 18'. Because the agent searched by a fixture ID that doesn't appear in search results, it missed the target thread and took no action.
