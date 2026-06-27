# Multi-API benchmark

This benchmark ran the Multi-API MCP - Baseline (Official) head-to-head against the Multi-API MCP - Hintas across 23 prompts that each span two or three surfaces — Slack, Gmail, and Notion — in a single session. Each prompt chains dependent steps across systems, where a value produced on one surface feeds the next.

The two stacks differ only in how those surfaces are served:

- **Baseline** — the **individual official MCP servers**, one per system (Slack's official server, Notion's official server, and the Gmail connector), stitched together into a single session.
- **Hintas** — a **single MCP server that contains all three systems**, serving Slack, Gmail, and Notion.

Both stacks answered the same prompts against mirrored workspaces on every surface, so the deltas reflect the server architecture under test rather than workspace skew. Grading is strictly binary and all-or-nothing: a prompt passes only when every task on every surface it touches — plus any cross-surface handoff — completed.

## Measured against

- **Multi-API MCP - Baseline (Official)** (baseline): `[20260623_070408__baseline](runs/20260623_070408__baseline/analysis.md)`
- **Multi-API MCP - Hintas** (variant): `[20260624_090524__hintas__topk10_batch-off_max10_rag-off](runs/20260624_090524__hintas__topk10_batch-off_max10_rag-off/analysis.md)`

## Verdict legend

This platform is graded **binary** — there is no `PARTIAL`.

- `✓ PASS`: every required task, on every surface the prompt touches plus any cross-surface handoff, was completed.
- `✗ FAIL`: any required task failed, was skipped, was blocked, or was fabricated. **Includes environmental rejections.**
- `⚠ ERROR`: infrastructure failure (no result, orchestrator error/timeout, or `result_subtype: error` with no usable output).

## Verdict tallies


| Metric       | Multi-API MCP - Baseline (Official) | Multi-API MCP - Hintas |
| ------------ | ----------------------------------- | ---------------------- |
| PASS         | 16                                  | 20                     |
| FAIL         | 5                                   | 3                      |
| ERROR        | 2                                   | 0                      |
| Success rate | 70%                                 | 87%                    |


> NOTE: The prompt suite defines 24 prompts; `p18` was not run on either stack, so both runs cover 23. The two baseline `ERROR`s (`p23`, `p24`) are 300 s orchestrator timeouts, not graded task failures, and contribute 0 tokens to the totals below.

## Tool-call tallies


| Metric         | Multi-API MCP - Baseline (Official) | Multi-API MCP - Hintas |
| -------------- | ----------------------------------- | ---------------------- |
| Tools complete | 442                                 | 294                    |
| Tools failed   | 23                                  | 33                     |
| Tools partial  | 0                                   | 0                      |
| Total          | 465                                 | 327                    |
| Tool pass rate | 95%                                 | 90%                    |


## Global comparable metrics

> For each variant, this restricts to prompts where **both** the baseline and that variant passed. That's the fair apples-to-apples subset for token and speed comparisons.

- Comparable prompt IDs: `1, 2, 3, 4, 5, 8, 9, 10, 12, 13, 15, 16, 17, 19, 20, 22` (count: 16)
- Excluded count: 7


| Metric                 | Multi-API MCP - Baseline (Official) | Multi-API MCP - Hintas | Δ Hintas - Official |
| ---------------------- | ----------------------------------- | ---------------------- | ------------------- |
| Total tokens           | 86,692                              | 114,484                | +27,792             |
| Avg tokens / prompt    | 5,418                               | 7,155                  | +1,737              |
| Avg tokens / tool call | 252                                 | 530                    | +278                |
| Avg peak context       | 772                                 | 692                    | -80                 |
| Avg wall-clock (s)     | 112.9                               | 140.9                  | +28.0               |
| Success rate           | 70%                                 | 87%                    | +17.4 pp            |
| Tool pass rate         | 95%                                 | 90%                    | -5.1 pp             |


## Final verdict


| Category                            | Winner                              | Margin  |
| ----------------------------------- | ----------------------------------- | ------- |
| Accuracy (success rate)             | Multi-API MCP - Hintas              | 17.4 pp |
| Speed (avg wall-clock)              | Multi-API MCP - Baseline (Official) | 19.9%   |
| Token efficiency (comparable total) | Multi-API MCP - Baseline (Official) | 24.3%   |
| Peak context (comparable avg)       | Multi-API MCP - Hintas              | 10.4%   |
| Tool reliability (tool success)     | Multi-API MCP - Baseline (Official) | 5.1 pp  |


## Folder layout

```
multi_api/
├── multi_api.toml     # platform manifest: surfaces, baseline/hintas stacks, analyzer prompt
├── .env(.example)     # per-surface, per-stack credentials (BASELINE_*/HINTAS_*)
├── prompts/           # benchmark_prompts.json (source of truth)
├── scripts/           # per-surface seed / reset (slack, gmail, notion) + common.py
└── runs/              # <timestamp>__<stack>[__<params>]/ per run
```

## Run the benchmark

```bash
uv run benchmark run --platform multi_api --stack baseline --analyze   # baseline (stitched official servers)
uv run benchmark run --platform multi_api --stack hintas   --analyze   # variant  (unified Hintas server)
uv run benchmark analyze --platform multi_api --all                    # (re)grade existing runs
```

> NOTE: Before running this, you need provisioned Slack, Gmail, and Notion workspaces on both stacks, the per-surface `BASELINE_*`/`HINTAS_*` credentials populated in `experiments/multi_api/.env`, and per-stack Claude config dirs (`~/.claude-multi-api-baseline`, `~/.claude-multi-api-hintas`) in place first. The baseline reaches Gmail through the account-synced claude.ai Gmail connector (connector mode), so its login must have that connector authorized and all other account connectors denied.

