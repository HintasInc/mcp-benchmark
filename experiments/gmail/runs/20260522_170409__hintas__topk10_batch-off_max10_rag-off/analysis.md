# Gmail MCP - Gmail MCP - Hintas benchmark analysis

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
| Success rate | 71% |
| Passes | 30 |
| Partial | 5 |
| Fails | 7 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 20 |
| Avg wall-clock | 58.6s |
| Total tokens | 95,750 |
| Avg tokens/prompt | 2,280 |
| Avg tool calls | 4.26 |
| Total tool failures | 18 |

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L2 | 3 | 100% | 0/0/0 |
| L3 | 2 | 100% | 0/0/0 |
| L4 | 4 | 50% | 2/0/0 |
| L5 | 1 | 0% | 1/0/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| retrieval | 1 | 100% | 0/0/0 |
| search | 6 | 100% | 0/0/0 |
| orchestration | 3 | 0% | 3/0/0 |
| edge_case | 3 | 100% | 0/0/0 |

## Notable failures

- **#10 Create a 'Hintas/Triage' label** (easy, labels) — `FAIL`: Agent described the label creation in its text response and showed invocation syntax but made zero actual MCP tool calls (tool_calls.total=0, tools_invoked=[]). No labels.create API call was executed, so the label was not created.
- **#18 Untrash a thread** (medium, modify) — `PARTIAL`: Agent correctly called threads.untrash but operated on the Bug triage draft (most recent item in Trash) instead of the target thread TH_OLD_PROMO. The correct API mechanism was used but applied to the wrong thread.
- **#20 Send a new email** (medium, send) — `FAIL`: The Gmail API's messages.send endpoint is not available in the Hintas MCP scope. Agent correctly identified the capability gap and reported it cannot send emails.
- **#21 Reply within a thread** (medium, send) — `FAIL`: The Gmail API's messages.send endpoint is not available in the Hintas MCP scope, making threaded replies impossible. Agent correctly identified the capability gap.
- **#23 Send a draft** (medium, drafts) — `FAIL`: drafts.send endpoint is disabled in the Hintas MCP scope. Agent correctly identified the capability gap and reported it cannot send the draft.
- **#25 Delete a draft** (easy, drafts) — `FAIL`: drafts.delete endpoint is disabled in the Hintas MCP scope. Agent correctly identified the capability gap and reported it cannot delete the draft.
- **#28 Empty Spam** (hard, modify) — `FAIL`: messages.delete and messages.batchDelete endpoints are not available in the Hintas MCP scope. Agent correctly identified the capability gap and could not permanently delete spam messages.
- **#32 Read body of a specific message** (medium, read) — `PARTIAL`: Agent had multiple base64 decode failures and ultimately returned Tomas's message body ('Attaching the repro log...') instead of Devon's first message ('Repro: load level 4...') from the BUG-247 thread. Correct thread was located but wrong message body was returned.
