# Implementation

Use this when you're adding a platform, debugging the pipeline, or reading run output.

> **Before running anything**, complete the per-platform setup — workspaces, tokens, manual UI state, and Claude config dirs. The harness assumes both stacks are already provisioned.
>
> - Slack: [experiments/slack/README.md](experiments/slack/README.md)
> - Notion: [experiments/notion/README.md](experiments/notion/README.md)

## Pipeline

All pipelines are subcommands of `uv run benchmark`. Tokens are read from `experiments/<platform>/.env` then `<repo>/.env`; never passed on the command line.


| Command      | What it does                                                                         |
| ------------ | ------------------------------------------------------------------------------------ |
| `run`        | Reset → seed → benchmark one stack. Add `--analyze` to chain per-run grading.        |
| `precompute` | Parse a run dir's `session.log` + `token_trace.json` into `analysis_data.json`.      |
| `analyze`    | Per-run LLM grading → `analysis.{json,md}` in the run dir. Auto-runs `precompute`.   |
| `final`      | LLM-graded baseline-vs-variant comparison → `final_analysis.{json,md}`.              |
| `aggregate`  | Deterministic 2-stack rollup from existing `analysis.json` files (no LLM).           |
| `combine`    | Deterministic N-way comparison (1 baseline + N variants) → `combined_comparison.md`. |
| `scaffold`   | Generate the skeleton for a new platform.                                            |


Run `uv run benchmark <command> --help` for flags.

### Typical flow

```bash
# 1. Run baseline and variant (one stack at a time).
uv run benchmark run --platform slack --stack slack    --analyze
uv run benchmark run --platform slack --stack hintas   --analyze

# 2. Compare them.
uv run benchmark final --platform slack --all
```

`--analyze` is optional; `analyze` can be invoked later against any run dir.

## Output layout

```
experiments/<platform>/
├── runs/<timestamp>__<stack>[__<variant-params>]/
│   ├── p<id>/
│   │   ├── session.log          # raw stream-json from claude
│   │   ├── token_trace.json     # per-turn token snapshots
│   │   └── verify_report.json   # post-reset drift check (if --verify)
│   ├── results.json             # per-prompt metrics (no raw output)
│   ├── analysis_data.json       # precompute output
│   ├── per_prompt_analysis/p<id>.json   # incremental grader output
│   ├── analysis.json            # per-run grading
│   └── analysis.md              # rendered report
└── final/<timestamp>/
    ├── final_analysis.{json,md} # baseline vs variant (final / aggregate)
    └── combined_comparison.md   # N-way (combine)
```

Run-dir naming: `<timestamp>__<stack>` for baseline; variant runs append a Hintas param summary (e.g. `__topk10_batch-off_max5_rag-off`) so repeat runs against different server configs don't collide.

## Manifest schema

Each platform is described by `experiments/<name>/<name>.toml`. Adding a platform is data-only — no orchestrator changes.

Each session is locked to its stack's MCP: built-in tools are disabled and only `mcp__<server>__*` is allowed, so the agent must succeed or fail on the MCP under test.

## Adding a new platform

```bash
uv run benchmark scaffold <name> \
    --display-name "<Title>" \
    --baseline-stack <baseline> --baseline-display "<Baseline MCP>" \
    --variant-stack  hintas    --variant-display  "Hintas MCP"
```

This generates:

- `experiments/<name>/<name>.toml`
- `experiments/<name>/{api,prompts,scripts,state}/`
- `experiments/<name>/prompts/benchmark_prompts.json`
- `experiments/<name>/scripts/{reset,seed,verify}_workspace.py` (TODO stubs)
- `src/benchmarking/analysis/per_run/<name>_analysis_prompt.md` (TODO placeholder)

Then:

1. Implement the three workspace scripts. Each must accept `--stack <name>` and read the workspace token from `$<DOWNSTREAM_TOKEN_ENV>`.
2. Author `experiments/<name>/prompts/benchmark_prompts.json` (see the platform README for the prompt schema).
3. Register the MCP server in each stack's `CLAUDE_CONFIG_DIR` (`claude mcp add …`) and complete OAuth.
4. Fill in the analyzer prompt and (optional) `src/benchmarking/analysis/notes/notes_<name>.md` for platform-specific grading rules.
5. Write `experiments/<name>/README.md` covering the per-workspace setup (manual UI state, scopes, tokens, sanity-check commands).

`uv run benchmark run --platform <name> --stack <baseline> --dry-run` exercises the wiring without calling Claude.