# Slack benchmark

We ran the Slack MCP - Official head-to-head against the Slack MCP - Hintas across 48 prompts. Both stacks answered the same prompts against two mirrored Slack workspaces (same users, channels, messages, reactions, DMs, and archived/deactivated boundaries), so the deltas reflect the MCP under test rather than workspace skew. Each session is locked to a single MCP with built-in tools disabled, so the agent has to succeed or fail on the server alone.

## Results

**Scope:** 48 prompts.

### Verdicts


| Metric              | Slack MCP (Official) | Slack MCP (Hintas) | Δ Hintas − Official |
| ------------------- | -------------------- | ------------------ | ------------------- |
| Total tokens        | 4,132                | 11,684             | +7,552              |
| Avg tokens / prompt | 590                  | 1,669              | +1,079              |
| Avg wall-clock (s)  | 16.9                 | 44.2               | +27.2               |
| Success rate        | 23%                  | 77%                | +54.2 pp            |
| Tool pass rate      | 99%                  | 100%               | +1.1 pp             |


Complete benchmark results: [results.md](results.md).

## Folder layout

1. `**IMPLEMENTATION.md`**: end-to-end setup walkthrough covering workspaces, tokens, scopes, manual UI fixups, and the orchestrator commands. Read this before attempting to run anything.
2. `**results.md**`: the rendered benchmark results, with verdict tallies, tool-call tallies, and the apples-to-apples comparable subset, plus links into the run dirs the numbers came from.
3. `**slack.toml**`: platform manifest the orchestrator reads to discover stacks, scripts, prompt files, and analyzer prompts. Edit this only when wiring a new stack or relocating files.
4. `**prompts/**`: holds `benchmark_prompts.json` with every prompt, its difficulty, category, required scopes, success criteria, and expected tools. This is the source of truth for what gets graded.
5. `**scripts/**`: the `seed` / `reset` / `verify` workspace scripts plus the per-stack `users` and app-manifest files. The orchestrator calls these to bring each workspace into a known state before each prompt.
6. `**api/**`: Slack's Web API reference (OpenAPI spec). Useful when authoring new prompts or debugging why a tool call returned the shape it did.
7. `**runs/**`: one folder per benchmark run, named `<timestamp>__<stack>[__<params>]`. Each holds `session.log`, `token_trace.json`, per-prompt subfolders, and the per-run `analysis.{json,md}` report.
8. `**final/**`: one folder per comparison, holding `final_analysis.{json,md}` (baseline vs variant) and `combined_comparison.md` (N-way) built from the runs above.

## Run the benchmark

```bash
uv run benchmark run --platform slack --stack slack    --analyze   # baseline
uv run benchmark run --platform slack --stack hintas   --analyze   # variant
uv run benchmark final --platform slack --all                      # compare
```

> NOTE: Before running this, you need two provisioned Slack workspaces, the right scopes, manual UI fixups, and per-stack Claude config dirs in place first. Walk through [IMPLEMENTATION.md](IMPLEMENTATION.md) end-to-end before kicking off a run.

