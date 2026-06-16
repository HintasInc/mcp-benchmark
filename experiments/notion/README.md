# Notion benchmark

This benchmark ran the Notion MCP - Official baseline against three variants — Notion MCP - Hintas, Notion MCP - Executor, and Notion MCP - Composio — across 56 prompts. Every stack answered the same prompts against mirrored Notion workspaces (same users, pages, databases, rows, and shared/unshared boundaries), so the deltas reflect the MCP under test rather than workspace skew. Each session is locked to a single MCP with built-in tools disabled, so the agent has to succeed or fail on the server alone.

## Measured against

- **Notion MCP - Official** (baseline): [`20260429_205418__notion`](runs/20260429_205418__notion/analysis.md)
- **Notion MCP - Hintas** (variant): [`20260429_205444__hintas__topk10_batch-off_max10_rag-off`](runs/20260429_205444__hintas__topk10_batch-off_max10_rag-off/analysis.md)
- **Notion MCP - Executor** (variant): [`20260608_214637__executor`](runs/20260608_214637__executor/analysis.md)
- **Notion MCP - Composio** (variant): [`20260616_093236__composio`](runs/20260616_093236__composio/analysis.md)

## Verdict legend

- `✓ PASS`: every success criterion met, with a usable answer and no blocking tool failure.
- `◐ PARTIAL`: some criteria met, others blocked; partial multi-step work.
- `✗ FAIL`: core task not accomplished. **Includes environmental rejections.**
- `⚠ ERROR`: infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Verdict tallies


| Metric       | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
| ------------ | --------------------- | --------------------- | --------------------- | ------------------- |
| PASS         | 38                    | 40                    | 44                    | **45**              |
| PARTIAL      | 4                     | 3                     | 2                     | **0**               |
| FAIL         | 14                    | 13                    | 10                    | **8**               |
| ERROR        | 0                     | 0                     | 0                     | 3                   |
| Success rate | 68%                   | 71%                   | 79%                   | **80%**             |


## Tool-call tallies


| Metric         | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
| -------------- | --------------------- | --------------------- | --------------------- | ------------------- |
| Tools complete | 399                   | 552                   | 255                   | 295                 |
| Tools failed   | 12                    | 10                    | 2                     | **0**               |
| Tools partial  | 0                     | 0                     | 0                     | 0                   |
| Total          | 411                   | 562                   | 257                   | 295                 |
| Tool pass rate | 97%                   | 98%                   | 99%                   | **100%**            |


## Global comparable metrics

> This restricts to prompts where **every** stack passed. That's the fair apples-to-apples subset for token and speed comparisons.

- Prompts: 30


| Metric                 | Notion MCP - Official | Notion MCP - Executor | Notion MCP - Composio | Notion MCP - Hintas |
| ---------------------- | --------------------- | --------------------- | --------------------- | ------------------- |
| Total tokens           | 63,387                | 60,137                | **39,249**            | 58,550              |
| Avg tokens / prompt    | 2,113                 | 2,005                 | **1,308**             | 1,952               |
| Avg tokens / tool call | 244                   | **205**               | 302                   | 412                 |
| Avg wall-clock (s)     | 44.6                  | 47.6                  | **38.1**              | 44.4                |


## Folder layout

```
notion/
├── IMPLEMENTATION.md   # setup walkthrough
├── results.md          # rendered benchmark results
├── notion.toml         # platform manifest: stacks, scripts, prompt files, analyzer prompts
├── prompts/            # benchmark_prompts.json (source of truth)
├── scripts/            # seed / reset / verify + per-stack users/prerequisites
├── api/                # Notion REST API reference (OpenAPI)
├── state/              # workspace_state.md (seeded workspace spec)
├── runs/               # <timestamp>__<stack>[__<params>]/ per run
└── final/              # baseline-vs-variant comparison output
```

## Run the benchmark

```bash
uv run benchmark run --platform notion --stack notion   --analyze   # baseline
uv run benchmark run --platform notion --stack hintas   --analyze   # variant
uv run benchmark final --platform notion --all                      # compare
```

> NOTE: Before running this, you need two provisioned Notion workspaces, the integration tokens, the manual top-level pages and integration shares, and per-stack Claude config dirs in place first. Walk through [IMPLEMENTATION.md](./IMPLEMENTATION.md) end-to-end before kicking off a run.

