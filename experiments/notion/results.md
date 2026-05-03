# Benchmark Comparison — Notion

**Scope:** 56 prompts

## Measured against

- **Notion's official MCP** (baseline) — `[20260429_205418__notion](runs/20260429_205418__notion/analysis.md)`
- **Hintas's Notion MCP** (variant) — `[20260429_205444__hintas__topk10_batch-off_max10_rag-off](runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off/analysis.md)`

## Verdict legend

- `✓ PASS` — every success criterion met; usable answer; no blocking tool failure.
- `◐ PARTIAL` — some criteria met, others blocked; partial multi-step work.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** 
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Verdict tallies


| Metric       | Notion's official MCP | Hintas's Notion MCP |
| ------------ | --------------------- | ------------------- |
| PASS         | 38                    | 45                  |
| PARTIAL      | 4                     | 0                   |
| FAIL         | 14                    | 8                   |
| ERROR        | 0                     | 3                   |
| Success rate | 68%                   | 80%                 |


## Tool-call tallies


| Metric         | Notion's official MCP | Hintas's Notion MCP |
| -------------- | --------------------- | ------------------- |
| Tools complete | 399                   | 295                 |
| Tools failed   | 12                    | 0                   |
| Tools partial  | 0                     | 0                   |
| Total          | 411                   | 295                 |
| Tool pass rate | 97%                   | 100%                |


## Global comparable metrics

> For each variant, this restricts to prompts where **both** the baseline and that variant passed — the fair apples-to-apples subset for token and speed comparisons.

- Comparable prompt IDs: `1, 2, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 27, 32, 33, 34, 36, 37, 41, 42, 44, 45, 47, 49, 50, 53, 55, 58` (count: 35)
- Excluded count: 21


| Metric                 | Notion MCP - Official | Notion MCP - Hintas | Δ Hintas - Official |
| ---------------------- | --------------------- | ------------------- | ------------------- |
| Total tokens           | 78,172                | 74,411              | -3,761              |
| Avg tokens / prompt    | 2,233                 | 2,126               | -107                |
| Avg tokens / tool call | 267                   | 400                 | +133                |
| Avg wall-clock (s)     | 45.4                  | 48.2                | +2.8                |
| Success rate           | 68%                   | 80%                 | +12.5 pp            |
| Tool pass rate         | 97%                   | 100%                | +2.9 pp             |


