# Notion benchmark

We ran the Notion MCP - Official head-to-head against the Notion MCP - Hintas across 56 prompts. Both stacks answered the same prompts against two mirrored Notion workspaces (same users, pages, databases, rows, and shared/unshared boundaries), so the deltas reflect the MCP under test rather than workspace skew. Each session is locked to a single MCP with built-in tools disabled, so the agent has to succeed or fail on the server alone.

## Results

**Scope:** 56 prompts.

### Verdicts

| Metric              | Notion MCP (Official) | Notion MCP (Hintas) | Δ Hintas − Official |
| ------------------- | --------------------- | ------------------- | ------------------- |
| Total tokens        | 78,172                | 74,411              | −3,761              |
| Avg tokens / prompt | 2,233                 | 2,126               | −107                |
| Avg wall-clock (s)  | 45.4                  | 48.2                | +2.8                |
| Success rate        | 68%                   | 80%                 | +12.5 pp            |
| Tool pass rate      | 97%                   | 100%                | +2.9 pp             |


Complete benchmark results: [results.md](results.md).

## Folder layout

1. **`IMPLEMENTATION.md`**: end-to-end setup walkthrough covering workspaces, tokens, scopes, manual UI state, and the orchestrator commands. Read this before attempting to run anything.
2. **`results.md`**: the rendered benchmark results, with verdict tallies, tool-call tallies, and the apples-to-apples comparable subset, plus links into the run dirs the numbers came from.
3. **`notion.toml`**: platform manifest the orchestrator reads to discover stacks, scripts, prompt files, and analyzer prompts. Edit this only when wiring a new stack or relocating files.
4. **`prompts/`**: holds `benchmark_prompts.json` with every prompt, its difficulty, category, required scopes, success criteria, and expected tools. This is the source of truth for what gets graded.
5. **`scripts/`**: the `seed` / `reset` / `verify` workspace scripts plus the per-stack `users` and `prerequisites` files. The orchestrator calls these to bring each workspace into a known state before each prompt.
6. **`api/`**: Notion's REST API reference (OpenAPI spec). Useful when authoring new prompts or debugging why a tool call returned the shape it did.
7. **`state/`**: holds `workspace_state.md`, the canonical spec of the seeded workspace (pages, databases, rows, comments, and sharing). Treat it as the contract the seeder and graders both follow.
8. **`runs/`**: one folder per benchmark run, named `<timestamp>__<stack>[__<params>]`. Each holds `session.log`, `token_trace.json`, per-prompt subfolders, and the per-run `analysis.{json,md}` report.
9. **`final/`**: one folder per comparison, holding `final_analysis.{json,md}` (baseline vs variant) and `combined_comparison.md` (N-way) built from the runs above.

## Run the benchmark

```bash
uv run benchmark run --platform notion --stack notion   --analyze   # baseline
uv run benchmark run --platform notion --stack hintas   --analyze   # variant
uv run benchmark final --platform notion --all                      # compare
```

> NOTE: Before running this, you need two provisioned Notion workspaces, the integration tokens, the manual top-level pages and integration shares, and per-stack Claude config dirs in place first. Walk through [IMPLEMENTATION.md](IMPLEMENTATION.md) end-to-end before kicking off a run.

