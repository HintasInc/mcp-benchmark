# Final Benchmark Analysis — Gmail — 20260523_1147

**Scope:** 42 prompts × 2 stacks (Gmail MCP - Official, Gmail MCP - Hintas).

- Baseline: `/Users/pratima/Documents/Projects/hintas-project/benchmarking/experiments/gmail/runs/20260520_190538__gmail` (Gmail MCP - Official)
- Variant:  `/Users/pratima/Documents/Projects/hintas-project/benchmarking/experiments/gmail/runs/20260522_170409__hintas__topk10_batch-off_max10_rag-off` (Gmail MCP - Hintas)

## Per-run reports

- Gmail MCP - Official: [`analysis.md`](../../runs/20260520_190538__gmail/analysis.md)  ↳ `../../runs/20260520_190538__gmail`
- Gmail MCP - Hintas: [`analysis.md`](../../runs/20260522_170409__hintas__topk10_batch-off_max10_rag-off/analysis.md)  ↳ `../../runs/20260522_170409__hintas__topk10_batch-off_max10_rag-off`

## MCP configuration

> The variant Hintas server runs with the parameters below. When comparing two Hintas runs (A vs B), this is the block to scan first — these are the only knobs that change between them.

| Parameter | Gmail MCP - Official (`gmail`) | Gmail MCP - Hintas (`hintas`) |
|:----------|:----------------:|:----------------:|
| `search_top_k` | **—** | **10** |
| `search_batch_enabled` | **—** | **off** |
| `search_max_results` | **—** | **10** |
| `rag_enabled` | **—** | **off** |

_Only the variant stack carries Hintas parameters; baseline is the unmodified MCP._

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused).
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Per-prompt results

| ID | Title | Diff | Gmail MCP - Official | Gmail MCP - Hintas | G Tok | G Tok | G Time | G Time | ΔTok | ΔTime |
|---:|:------|:----:|:------:|:------:|---:|---:|---:|---:|---:|---:|
| 1 | Who am I? | L1 | ◐ PARTIAL | ✓ PASS | 1,179 | 310 | 31.3s | 17.1s | *excl* | *excl* |
| 2 | List all labels | L1 | ◐ PARTIAL | ✓ PASS | 469 | 459 | 14.1s | 16.5s | *excl* | *excl* |
| 3 | Count unread in inbox | L1 | ✓ PASS | ✓ PASS | 318 | 517 | 13.0s | 32.8s | +199 | +19.8 |
| 4 | Latest 10 inbox subjects | L2 | ✓ PASS | ✓ PASS | 494 | 1,131 | 16.0s | 31.3s | +637 | +15.3 |
| 5 | Find Jared's threads | L2 | ✓ PASS | ✓ PASS | 995 | 1,435 | 27.0s | 34.4s | +440 | +7.4 |
| 6 | Threads with attachments | L2 | ✗ FAIL | ✓ PASS | 1,927 | 1,674 | 59.0s | 41.6s | *excl* | *excl* |
| 7 | Read BUG-247 thread | L2 | ✓ PASS | ✓ PASS | 599 | 3,795 | 25.7s | 78.1s | +3,196 | +52.4 |
| 8 | Starred threads | L2 | ✓ PASS | ✓ PASS | 268 | 2,509 | 13.2s | 67.3s | +2,241 | +54.1 |
| 9 | List drafts | L1 | ✓ PASS | ✓ PASS | 206 | 613 | 11.3s | 19.7s | +407 | +8.3 |
| 10 | Create a 'Hintas/Triage' label | L1 | ✓ PASS | ✗ FAIL | 301 | 346 | 17.2s | 14.5s | *excl* | *excl* |
| 11 | Rename a label | L2 | ✗ FAIL | ✓ PASS | 361 | 475 | 18.0s | 19.5s | *excl* | *excl* |
| 12 | Apply label to a thread | L2 | ✓ PASS | ✓ PASS | 352 | 1,989 | 37.7s | 45.0s | +1,637 | +7.3 |
| 13 | Remove a label from threads | L3 | ✓ PASS | ✓ PASS | 492 | 1,332 | 21.9s | 90.2s | +840 | +68.3 |
| 14 | Archive a thread | L2 | ✓ PASS | ✓ PASS | 318 | 2,870 | 23.0s | 67.2s | +2,552 | +44.2 |
| 15 | Mark thread as read | L2 | ✓ PASS | ✓ PASS | 307 | 531 | 41.9s | 20.4s | +224 | -21.5 |
| 16 | Star a thread | L2 | ✗ FAIL | ✓ PASS | 192 | 812 | 12.1s | 27.9s | *excl* | *excl* |
| 17 | Trash a thread | L2 | ✓ PASS | ✓ PASS | 275 | 866 | 15.5s | 28.8s | +591 | +13.3 |
| 18 | Untrash a thread | L2 | ✓ PASS | ◐ PARTIAL | 577 | 563 | 22.5s | 19.8s | *excl* | *excl* |
| 19 | Create a draft | L2 | ✗ FAIL | ✓ PASS | 340 | 1,476 | 11.4s | 32.3s | *excl* | *excl* |
| 20 | Send a new email | L2 | ✗ FAIL | ✗ FAIL | 221 | 1,799 | 19.8s | 57.8s | *excl* | *excl* |
| 21 | Reply within a thread | L3 | ✗ FAIL | ✗ FAIL | 491 | 798 | 33.5s | 26.7s | *excl* | *excl* |
| 22 | Forward a thread | L3 | ◐ PARTIAL | ✗ FAIL | 1,302 | 3,478 | 42.5s | 83.1s | *excl* | *excl* |
| 23 | Send a draft | L2 | ✗ FAIL | ✗ FAIL | 251 | 716 | 12.4s | 35.9s | *excl* | *excl* |
| 24 | Update a draft | L3 | ◐ PARTIAL | ✓ PASS | 1,608 | 3,890 | 39.5s | 69.3s | *excl* | *excl* |
| 25 | Delete a draft | L1 | ✗ FAIL | ✗ FAIL | 1,740 | 841 | 39.4s | 30.4s | *excl* | *excl* |
| 26 | Triage today's unread | L3 | ✗ FAIL | ✓ PASS | 927 | 2,122 | 25.6s | 46.1s | *excl* | *excl* |
| 27 | Bulk-archive promotions | L3 | ✓ PASS | ✓ PASS | 1,425 | 2,802 | 57.9s | 82.1s | +1,377 | +24.2 |
| 28 | Empty Spam | L3 | ✗ FAIL | ✗ FAIL | 158 | 790 | 7.0s | 34.1s | *excl* | *excl* |
| 29 | Senders of unread inbox | L3 | ✓ PASS | ✓ PASS | 1,271 | 1,655 | 32.0s | 42.9s | +384 | +10.9 |
| 30 | Threads with no reply from me | L4 | ◐ PARTIAL | ✓ PASS | 4,075 | 4,318 | 88.6s | 86.6s | *excl* | *excl* |
| 31 | Threads I'm CC'd on only | L3 | ✓ PASS | ✓ PASS | 1,865 | 4,219 | 54.2s | 86.4s | +2,354 | +32.3 |
| 32 | Read body of a specific message | L2 | ✓ PASS | ◐ PARTIAL | 703 | 4,505 | 30.6s | 72.9s | *excl* | *excl* |
| 33 | Download an attachment | L3 | ✗ FAIL | ✓ PASS | 497 | 3,665 | 18.6s | 64.5s | *excl* | *excl* |
| 43 | Conflicting label modify | L3 | ✓ PASS | ✓ PASS | 1,202 | 976 | 40.4s | 31.1s | -226 | -9.2 |
| 44 | Operate on a trashed thread | L2 | ✗ FAIL | ✓ PASS | 1,016 | 3,573 | 35.7s | 93.1s | *excl* | *excl* |
| 45 | Rename a system label (reject) | L2 | ✓ PASS | ✓ PASS | 227 | 200 | 11.0s | 8.2s | -27 | -2.8 |
| 46 | Search by date window | L2 | ✓ PASS | ✓ PASS | 3,345 | 8,599 | 60.9s | 193.6s | +5,254 | +132.7 |
| 47 | Bulk relabel (label migration) | L4 | ◐ PARTIAL | ◐ PARTIAL | 813 | 3,246 | 36.8s | 95.9s | *excl* | *excl* |
| 48 | Quiet labels audit | L4 | ✓ PASS | ✓ PASS | 1,308 | 3,296 | 28.5s | 65.2s | +1,988 | +36.7 |
| 49 | Senders with no reply from me | L4 | ◐ PARTIAL | ✓ PASS | 8,634 | 2,786 | 167.3s | 63.1s | *excl* | *excl* |
| 51 | Triage and reply to a single thread | L5 | ◐ PARTIAL | ◐ PARTIAL | 2,540 | 8,412 | 63.8s | 164.4s | *excl* | *excl* |
| 52 | Send-and-label round trip | L4 | ✗ FAIL | ◐ PARTIAL | 1,256 | 5,361 | 29.2s | 223.3s | *excl* | *excl* |

## Verdict tallies

| Stack | PASS | PARTIAL | FAIL | ERROR | Success rate |
|:------|---:|---:|---:|---:|---:|
| Gmail MCP - Official | 21 | 8 | 13 | 0 | 50% |
| Gmail MCP - Hintas | 30 | 5 | 7 | 0 | 71% |

## Tool-call tallies (every prompt, regardless of verdict)

| Stack | Tools complete | Tools failed | Tools partial | Total | Tool success rate |
|:------|---:|---:|---:|---:|---:|
| Gmail MCP - Official | 115 | 3 | 0 | 118 | 97% |
| Gmail MCP - Hintas | 161 | 18 | 0 | 179 | 90% |

## Comparable-only metrics (both stacks PASS)

- Comparable prompt IDs: `3, 4, 5, 7, 8, 9, 12, 13, 14, 15, 17, 27, 29, 31, 43, 45, 46, 48` (count: 18)
- Excluded prompt IDs:   `1, 2, 6, 10, 11, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 30, 32, 33, 44, 47, 49, 51, 52` (count: 24)

| Metric | Gmail MCP - Official | Gmail MCP - Hintas | Δ (G − G) |
|:-------|---:|---:|---:|
| Total tokens | 15,267 | 39,335 | -24,068 |
| Avg tokens / prompt | 848 | 2,185 | -1,337 |
| Avg tokens / tool call | 339 | 546 | -207 |
| Avg peak context | 29 | 20 | +9 |
| Avg initial context | 3.00 | 3.00 | 0.00 |
| Avg wall-clock (s) | 29.5 | 56.9 | -27.4 |

## Final verdict

| Category | Winner | Margin |
|:---------|:------:|---:|
| Accuracy (success rate) | Gmail MCP - Hintas | 21.4 pp |
| Speed (avg wall-clock) | Gmail MCP - Official | 48.2% |
| Token efficiency (comparable total) | Gmail MCP - Official | 61.2% |
| Peak context (comparable avg) | Gmail MCP - Hintas | 31.3% |
| Tool reliability (tool success rate) | Gmail MCP - Official | — |

Gmail MCP - Official wins on accuracy=Gmail MCP - Hintas (21.4pp), speed=Gmail MCP - Official (48.2%), tokens=Gmail MCP - Official (61.2%).
