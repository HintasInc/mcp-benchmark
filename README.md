# MCP Benchmark

**Official platform MCPs vs MCPs by [Hintas](https://hintas.com) — head-to-head, on the same prompts, against mirrored workspaces.**

---

For each platform, two stacks — the platform's official MCP (baseline) and the MCP provided by Hintas (variant) — answer the same prompts under identical conditions. The harness measures pass rate, token usage, tool-call count, wall time, and failure modes, then reports baseline − variant deltas across the prompt suite.

## Experiments and Results

Each platform was run head-to-head over a fixed prompt suite (48 prompts for Slack, 58 for Notion), with the official MCP and the Hintas MCP answering the same prompts against mirrored workspaces. The tables below summarize the per-dimension verdicts; full per-prompt breakdowns live in each platform's report.

### Slack

| Metric         | Slack MCP — Official | Slack MCP — Hintas | Δ (Hintas − Official) |
| :------------- | -------------------: | -----------------: | --------------------: |
| Success rate   |                  23% |                77% |             +54.2 pp  |
| Speed          |               16.9 s |             44.2 s |              +27.2 s  |
| Tokens         |                  590 |              1,669 |               +1,079  |

Full report: [experiments/slack/results.md](experiments/slack/results.md)

### Notion

| Metric         | Notion MCP — Official | Notion MCP — Hintas | Δ (Hintas − Official) |
| :------------- | --------------------: | ------------------: | --------------------: |
| Success rate   |                   68% |                 80% |             +12.5 pp  |
| Speed          |                45.4 s |              48.2 s |               +2.8 s  |
| Tokens         |                 2,233 |               2,126 |                 −107  |

Full report: [experiments/notion/results.md](experiments/notion/results.md)

## What gets measured

- Pass rate (per prompt, scored by an analyzer Claude session)
- Total input/output tokens
- Tool-call count
- Wall-clock time
- Failure modes (categorized)

## Quick start

Prerequisites:

- `uv` (`brew install uv`)
- `claude` CLI on `$PATH` (`npm i -g @anthropic-ai/claude-code`)
- `uv sync` to install Python deps

Run a benchmark:

```bash
uv run benchmark run --platform slack --stack slack    # baseline
uv run benchmark run --platform slack --stack hintas   # variant
```

Tokens are read from `experiments/<name>/.env` — see the platform README for the required variables.

Run `uv run benchmark --help` for the full subcommand and flag list.

## Implementation

For the harness internals — pipeline subcommands, output layout, manifest schema, and how to add a new platform — see [IMPLEMENTATION.md](IMPLEMENTATION.md).

---

Built by **[Hintas](https://hintas.com)**