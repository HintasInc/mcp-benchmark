# MCP benchmark harness

Single-stack benchmark of an MCP server. For each prompt, the harness runs one Claude session against a mirrored workspace and measures pass rate, token usage, tool-call count, wall-clock time, and failure modes. The official MCP for a platform only needs to be benchmarked once; the Hintas MCP can be re-run repeatedly against different server-side parameter configurations.

The harness itself is platform-agnostic. Each platform (Slack, …) lives under `platforms/<name>/` with its own TOML manifest plus three workspace scripts (reset, seed, verify).

## Prerequisites

- `uv` installed (`brew install uv`)
- `claude` CLI on `$PATH` (`npm i -g @anthropic-ai/claude-code`)
- Python deps synced (`uv sync`)
- Platform-specific workspace setup (tokens, MCP configs, seed state) — see the platform's own README

## Quick start

```bash
uv run benchmark run --platform <name> --stack <stack-name>
```

(Equivalent to `uv run python -m benchmarking run --platform <name> --stack <stack-name>`.)

`benchmark` is a single entrypoint with subcommands — `run`, `analyze`, `final`, `aggregate`, `combine`, `precompute`. Run `uv run benchmark --help` to see the full list. Each platform declares one or more stacks; `--stack` selects which one to benchmark. Tokens come from `<platform>/.env` (or `<repo>/.env`, or the shell environment) — they are not accepted on the command line.

The `run` subcommand executes the full pipeline for the selected stack:

1. **Reset** — restores the workspace to baseline.
2. **Seed** — full re-seed of the workspace.
3. **Benchmark** — for each selected prompt, resets the workspace, then launches one MCP session and captures `session.log` + `token_trace.json`.

Each invocation lives in `platforms/<platform>/runs/<timestamp>__<stack>[__<param-summary>]/`. Repeat Hintas runs with different `--search-top-k` / `--search-batch-enabled` / `--search-max-results` / `--rag-enabled` flags get distinct directories so they don't overwrite each other (the params are configured on the Hintas server itself; the script accepts them only as labels).

### Where `.env` is loaded from

The orchestrator loads `.env` files in this order, with the first match winning (later files do **not** override variables already set):

1. `platforms/<platform>/.env` — platform-specific (e.g. `platforms/slack/.env`). **Preferred location** for workspace tokens (`HINTAS_TOKEN`, `SLACK_TOKEN`, …).
2. `<repo-root>/.env` — fallback for values shared across platforms.
3. The process environment — anything you `export`ed in your shell takes precedence over both files.

Both files are gitignored. A repo-root `.env.example` documents the expected variables; copy it into the platform directory you're working with.

## Registered platforms

| Platform | Setup | Run |
|---|---|---|
| [slack](platforms/slack/README.md) | [platforms/slack/README.md](platforms/slack/README.md) | `SLACK_TOKEN` + `HINTAS_TOKEN` → `uv run benchmark run --platform slack --stack <slack\|hintas>` |

The orchestrator loads `platforms/<name>/<name>.toml` to discover the stacks, token env vars, prompts file, and workspace scripts.

## The four ways to run

Pick the entrypoint that matches what you already have on disk. Examples use `--platform slack`.

### 1. Run the benchmark only (no analysis)

```bash
uv run benchmark run --platform slack --stack hintas
```

Output: `platforms/slack/runs/<timestamp>__hintas[__<params>]/` containing `p<id>/session.log` + `token_trace.json` + `results.json`.

### 2. Run the benchmark and chain per-run analysis

```bash
uv run benchmark run --platform slack --stack hintas --analyze
```

Same as #1, plus a Phase 4 that grades the new run dir → `analysis.json` + `analysis.md` inside it.

### 3. Skip the benchmark; grade existing session logs

```bash
# one run dir
uv run benchmark analyze --platform slack \
    --runs platforms/slack/runs/<timestamp>__hintas

# every run dir under platforms/slack/runs/
uv run benchmark analyze --platform slack --all
```

Auto-runs `precompute` (raw logs → `analysis_data.json`), then writes `analysis.{json,md}`. Resumable via `per_prompt_analysis/p<id>.json`; add `--regrade` to force re-grading, `--prompt-ids 1 2 5` to focus on a subset.

### 4. Skip everything; compare existing per-run analyses

All three modes read each run dir's existing `analysis.json` and produce a cross-stack report under `platforms/<platform>/final/<timestamp>/`.

```bash
# LLM-graded head-to-head (exactly 2 run dirs: baseline + variant)
uv run benchmark final --platform slack --all
# or explicit:
uv run benchmark final --platform slack \
    --runs platforms/slack/runs/<ts>__slack \
           platforms/slack/runs/<ts>__hintas__<params>

# Deterministic 2-stack rollup (no LLM)
uv run benchmark aggregate --platform slack --all

# Deterministic N-stack: 1 baseline + N variants
uv run benchmark combine --platform slack \
    --baseline platforms/slack/runs/<ts>__slack \
    --variants platforms/slack/runs/<ts>__hintas__<paramsA> \
               platforms/slack/runs/<ts>__hintas__<paramsB>
```

Output: `final_analysis.{json,md}` (`final` / `aggregate`) or `combined_comparison.md` (`combine`).

## Common flags

```bash
# Filter to specific prompts / difficulties / categories
--prompt-ids 1 22 40
--difficulty L1 L2
--category retrieval

# Feasibility gate (platform-defined; slack supports core/extension)
--feasibility core extension

# Skip setup when you know the workspace is already clean
--skip-setup

# Hintas-only labels (encoded into the run-dir name; configured server-side)
--search-top-k 20 --search-batch-enabled --search-max-results 15 --rag-enabled

# No claude invocations, placeholder logs only
--dry-run --prompt-ids 1
```

## Output layout

Each run dir holds exactly one stack's session logs at the top level — no outer stack folder:

```
platforms/<platform>/runs/
├── 20260422_080812__slack/
│   ├── p1/
│   │   ├── session.log            # stream-json JSONL of the run
│   │   └── token_trace.json       # chronological token snapshots
│   ├── p2/
│   └── results.json               # raw per-session metrics + stack name
└── 20260422_081530__hintas__topk10_batch-off_max10_rag-off/
    ├── p1/, p2/, …
    └── results.json
```

The official-MCP run dir name is just `<timestamp>__<stack>`; Hintas runs add the parameter summary so repeat sweeps don't collide.

`session.log` starts with a few `#`-prefixed header lines, then one JSON object per line (Claude's stream-json output). `token_trace.json` extracts per-turn token snapshots — initial context load, after each tool call, final totals.

## Troubleshooting

- **`claude CLI not found`** — `npm i -g @anthropic-ai/claude-code` and make sure `$(npm prefix -g)/bin` is on `$PATH`.
- **Run dir already exists** — two invocations within the same second collide. Wait a moment and re-run, or pass `--run-subdir` explicitly.
- **Platform-specific failures** (seed errors, OAuth refresh, workspace drift) — see the platform's own README.
