# MCP Benchmark

<p align="center">
  <a href="https://hintas.com">
    <img src="./assets/hintas-banner.png" alt="Hintas" width="720" />
  </a>
</p>

<p align="center">
  <strong>Official platform MCPs vs MCPs by <a href="https://hintas.com">Hintas</a> — head-to-head, on the same prompts, against mirrored workspaces.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache 2.0" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-%E2%89%A53.10-3776AB.svg?logo=python&logoColor=white" alt="Python ≥3.10" /></a>
  <a href="#supported-platforms"><img src="https://img.shields.io/badge/platforms-Slack%20%7C%20Notion-7C3AED.svg" alt="Platforms: Slack | Notion" /></a>
  <a href="https://hintas.com"><img src="https://img.shields.io/badge/hintas.com-000000.svg?logo=safari&logoColor=white" alt="hintas.com" /></a>
</p>

---

For each platform, two stacks — the platform's official MCP (baseline) and the MCP provided by Hintas (variant) — answer the same prompts under identical conditions. The harness measures pass rate, token usage, tool-call count, wall time, and failure modes, then reports baseline − variant deltas across the prompt suite.

## Supported platforms

| Platform | Baseline MCP | Variant MCP | Setup |
|---|---|---|---|
| Slack | `slack` (official) | `hintas-slack` | [platforms/slack/README.md](platforms/slack/README.md) |
| Notion | `notion` (official) | `hintas-notion` | [platforms/notion/README.md](platforms/notion/README.md) |

## Latest results

| Platform | Comparison report |
|---|---|
| Slack | [platforms/slack/final/20260501_1927/combined_comparison.md](platforms/slack/final/20260501_1927/combined_comparison.md) |
| Notion | [platforms/notion/final/20260503_1101/combined_comparison.md](platforms/notion/final/20260503_1101/combined_comparison.md) |

Older runs are preserved under each platform's `final/<timestamp>/` directory.

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

Tokens are read from `platforms/<name>/.env` — see the platform README for the required variables.

Run `uv run benchmark --help` for the full subcommand and flag list.

## Implementation

For the harness internals — pipeline subcommands, output layout, manifest schema, and how to add a new platform — see [IMPLEMENTATION.md](IMPLEMENTATION.md).

---

<div align="center">

Built by **[Hintas](https://hintas.com)**

</div>
