# Gmail benchmark

This benchmark ran the Gmail MCP - Official head-to-head against the Gmail MCP - Hintas across 42 prompts. Both stacks answered the same prompts against two mirrored Gmail mailboxes (same threads, labels, drafts, filters, send-as aliases, and read/unread/starred boundaries), so the deltas reflect the MCP under test rather than mailbox skew. Each session is locked to a single MCP with built-in tools disabled, so the agent has to succeed or fail on the server alone.

## Measured against

- **Gmail MCP - Official** (baseline): [`20260520_190538__gmail`](runs/20260520_190538__gmail/analysis.md)
- **Gmail MCP - Hintas** (variant): [`20260522_170409__hintas__topk10_batch-off_max10_rag-off`](runs/20260522_170409__hintas__topk10_batch-off_max10_rag-off/analysis.md)

## Verdict legend

- `✓ PASS`: every success criterion met, with a usable answer and no blocking tool failure.
- `◐ PARTIAL`: some criteria met, others blocked; partial multi-step work.
- `✗ FAIL`: core task not accomplished. **Includes environmental rejections.**
- `⚠ ERROR`: infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Verdict tallies


| Metric       | Gmail MCP - Official | Gmail MCP - Hintas |
| ------------ | -------------------- | ------------------ |
| PASS         | 21                   | 30                 |
| PARTIAL      | 8                    | 5                  |
| FAIL         | 13                   | 7                  |
| ERROR        | 0                    | 0                  |
| Success rate | 50%                  | 71%                |


## Tool-call tallies


| Metric         | Gmail MCP - Official | Gmail MCP - Hintas |
| -------------- | -------------------- | ------------------ |
| Tools complete | 115                  | 161                |
| Tools failed   | 3                    | 18                 |
| Tools partial  | 0                    | 0                  |
| Total          | 118                  | 179                |
| Tool pass rate | 97%                  | 90%                |


## Global comparable metrics

> For each variant, this restricts to prompts where **both** the baseline and that variant passed. That's the fair apples-to-apples subset for token and speed comparisons.

- Comparable prompt IDs: `3, 4, 5, 7, 8, 9, 12, 13, 14, 15, 17, 27, 29, 31, 43, 45, 46, 48` (count: 18)
- Excluded count: 24


| Metric                 | Gmail MCP - Official | Gmail MCP - Hintas | Δ Hintas - Official |
| ---------------------- | -------------------- | ------------------ | ------------------- |
| Total tokens           | 15,267               | 39,335             | +24,068             |
| Avg tokens / prompt    | 848                  | 2,185              | +1,337              |
| Avg tokens / tool call | 339                  | 546                | +207                |
| Avg peak context       | 29                   | 20                 | -9                  |
| Avg wall-clock (s)     | 29.5                 | 56.9               | +27.4               |
| Success rate           | 50%                  | 71%                | +21.4 pp            |
| Tool pass rate         | 97%                  | 90%                | -7.0 pp             |


## Final verdict

| Category                            | Winner               | Margin   |
| ----------------------------------- | -------------------- | -------- |
| Accuracy (success rate)             | Gmail MCP - Hintas   | 21.4 pp  |
| Speed (avg wall-clock)              | Gmail MCP - Official | 48.2%    |
| Token efficiency (comparable total) | Gmail MCP - Official | 61.2%    |
| Peak context (comparable avg)       | Gmail MCP - Hintas   | 31.3%    |
| Tool reliability (tool success)     | Gmail MCP - Official | 7.0 pp   |


## Folder layout

```
gmail/
├── IMPLEMENTATION.md   # setup walkthrough
├── results.md          # rendered benchmark results
├── gmail.toml          # platform manifest: stacks, scripts, prompt files, analyzer prompts
├── prompts/            # benchmark_prompts.json (source of truth)
├── scripts/            # seed / reset / verify + per-stack users/prerequisites
├── api/                # Gmail API reference (OpenAPI)
├── state/              # workspace_state.md (seeded mailbox spec)
├── runs/               # <timestamp>__<stack>[__<params>]/ per run
└── final/              # baseline-vs-variant comparison output
```

## Run the benchmark

```bash
uv run benchmark run --platform gmail --stack gmail    --analyze   # baseline
uv run benchmark run --platform gmail --stack hintas   --analyze   # variant
uv run benchmark final --platform gmail --all                      # compare
```

> NOTE: Before running this, you need two provisioned Gmail mailboxes, the right OAuth scopes, manual UI fixups (forwarding-address verification), and per-stack Claude config dirs in place first. Walk through [IMPLEMENTATION.md](./IMPLEMENTATION.md) end-to-end before kicking off a run.
