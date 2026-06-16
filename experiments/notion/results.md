# Combined Benchmark Comparison — Notion — 20260616_1205

**Scope:** 56 prompts × 4 stacks (baseline + 3 variants).

## Measured against

- **Notion MCP - Official** (baseline) — [`20260429_205418__notion`](runs/20260429_205418__notion/analysis.md)
- **Notion MCP - Executor** (variant) — [`20260608_214637__executor`](runs/20260608_214637__executor/analysis.md)
- **Notion MCP - Composio** (variant) — [`20260616_093236__composio`](runs/20260616_093236__composio/analysis.md)
- **Notion MCP - Hintas** (variant) — [`20260429_205444__hintas__topk10_batch-off_max10_rag-off`](runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off/analysis.md)

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** 
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Verdict tallies

| Metric | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
|:-------|---:|---:|---:|---:|
| PASS | 38 | 40 | 44 | 45 |
| PARTIAL | 4 | 3 | 2 | 0 |
| FAIL | 14 | 13 | 10 | 8 |
| ERROR | 0 | 0 | 0 | 3 |
| Success rate | 68% | 71% | 79% | 80% |

## Tool-call tallies

| Metric | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
|:-------|---:|---:|---:|---:|
| Tools complete | 399 | 552 | 255 | 295 |
| Tools failed | 12 | 10 | 2 | 0 |
| Tools partial | 0 | 0 | 0 | 0 |
| Total | 411 | 562 | 257 | 295 |
| Tool pass rate | 97% | 98% | 99% | 100% |

## Global comparable metrics
> Only the prompts where every stack passed are included.
- Included count: 30 (prompt IDs: `1, 4, 5, 6, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 27, 32, 33, 34, 36, 37, 41, 42, 45, 47, 49, 50, 53, 55`)
- Excluded count: 26

| Metric | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
|:-------|---:|---:|---:|---:|
| Total tokens | 63,387 | 60,137 | 39,249 | 58,550 |
| Avg tokens / prompt | 2,113 | 2,005 | 1,308 | 1,952 |
| Avg tokens / tool call | 244 | 205 | 302 | 412 |
| Avg wall-clock (s) | 44.6 | 47.6 | 38.1 | 44.4 |

## Per-pair comparable metrics (baseline ∩ variant PASS)

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token and speed comparisons.
> Each variant column group uses its own pair-specific intersection, so baseline values differ across groups.

- Notion MCP - Official ∩ Notion MCP - Executor: n=32, IDs `1, 4, 5, 6, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 27, 30, 32, 33, 34, 36, 37, 38, 41, 42, 45, 47, 49, 50, 53, 55`
- Notion MCP - Official ∩ Notion MCP - Composio: n=36, IDs `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 30, 32, 33, 34, 36, 37, 38, 41, 42, 44, 45, 47, 49, 50, 53, 55`
- Notion MCP - Official ∩ Notion MCP - Hintas: n=35, IDs `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 44, 45, 47, 49, 50, 53, 55, 58`

| Metric | Notion MCP - Official (Executor pair) | Notion MCP - Executor | Δ Executor - Official | Notion MCP - Official (Composio pair) | Notion MCP - Composio | Δ Composio - Official | Notion MCP - Official (Hintas pair) | Notion MCP - Hintas | Δ Hintas - Official |
|:-------|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Total tokens | 64,115 | 65,145 | +1,030 | 77,539 | 60,931 | -16,608 | 78,172 | 74,411 | -3,761 |
| Avg tokens / prompt | 2,004 | 2,036 | +32 | 2,154 | 1,693 | -461 | 2,233 | 2,126 | -107 |
| Avg tokens / tool call | 243 | 206 | -37 | 264 | 356 | +93 | 267 | 400 | +133 |
| Avg wall-clock (s) | 42.5 | 48.0 | +5.4 | 43.9 | 44.3 | +0.4 | 45.4 | 48.2 | +2.8 |
| Success rate | 68% | 71% | +3.6 pp | 68% | 79% | +10.7 pp | 68% | 80% | +12.5 pp |
| Tool pass rate | 97% | 98% | +1.1 pp | 97% | 99% | +2.1 pp | 97% | 100% | +2.9 pp |
