# Benchmark Comparison: Slack

**Scope:** 48 prompts

## Measured against

- **Slack MCP - Official** (baseline): `[20260429_205001__slack](runs/20260429_205001__slack/analysis.md)`
- **Slack MCP - Hintas** (variant): `[20260430_100018__hintas__topk10_batch-off_max10_rag-off](runs/20260430_100018__hintas__topk10_batch-off_max10_rag-off/analysis.md)`

## Verdict legend

- `✓ PASS`: every success criterion met, with a usable answer and no blocking tool failure.
- `◐ PARTIAL`: some criteria met, others blocked; partial multi-step work.
- `✗ FAIL`: core task not accomplished. **Includes environmental rejections.**
- `⚠ ERROR`: infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Verdict tallies


| Metric       | Slack MCP - Official | Slack MCP - Hintas |
| ------------ | -------------------- | ------------------ |
| PASS         | 11                   | 27                 |
| PARTIAL      | 10                   | 3                  |
| FAIL         | 27                   | 5                  |
| ERROR        | 0                    | 0                  |
| Success rate | 23%                  | 77%                |


## Tool-call tallies


| Metric         | Slack MCP - Official | Slack MCP - Hintas |
| -------------- | -------------------- | ------------------ |
| Tools complete | 270                  | 178                |
| Tools failed   | 3                    | 0                  |
| Tools partial  | 0                    | 0                  |
| Total          | 273                  | 178                |
| Tool pass rate | 99%                  | 100%               |


## Global comparable metrics

> For each variant, this restricts to prompts where **both** the baseline and that variant passed. That's the fair apples-to-apples subset for token and speed comparisons.

- Comparable prompt IDs: `3, 4, 5, 13, 20, 23, 31` (count: 7)
- Excluded count: 41


| Metric                 | Slack MCP - Official | Slack MCP - Hintas | Δ Hintas - Official |
| ---------------------- | -------------------- | ------------------ | ------------------- |
| Total tokens           | 4,132                | 11,684             | +7,552              |
| Avg tokens / prompt    | 590                  | 1,669              | +1,079              |
| Avg tokens / tool call | 243                  | 377                | +134                |
| Avg wall-clock (s)     | 16.9                 | 44.2               | +27.2               |
| Success rate           | 23%                  | 77%                | +54.2 pp            |
| Tool pass rate         | 99%                  | 100%               | +1.1 pp             |


