# Slack platform — Hintas vs Slack MCP

Slack-specific setup and wiring for the `slack` platform registered in `platforms/slack/slack.toml`. Two stacks are declared — the official **Slack MCP** and the **Hintas MCP** — each pointed at its own mirrored Slack workspace. Pick one with `--stack <name>` per invocation.

Benchmark clock anchor: `2026-04-19T10:00:00-07:00`. All time-relative prompts resolve against this, not your wall clock.

## Run it

Put the workspace tokens in `platforms/slack/.env` (or `export` them), then run one stack at a time:

```bash
# platforms/slack/.env
SLACK_TOKEN=xoxp-<U05CLAUDE-token-from-slack-workspace>
HINTAS_TOKEN=xoxp-<U05CLAUDE-token-from-hintas-workspace>
```

```bash
uv run python benchmark.py --stack slack    # baseline
uv run python benchmark.py --stack hintas   # variant
```

The orchestrator reads `platforms/slack/.env` first, then falls back to the repo-root `.env`. Anything `export`ed in the shell wins over both. See the [parent README](../../README.md#where-env-is-loaded-from) for the full precedence rules. Tokens are not accepted on the command line.

`--platform slack` is the default, so it can be omitted. See the [parent README](../../README.md) for the full list of orchestrator flags (filtering, `--skip-setup`, `--dry-run`, Hintas labels).

## Prerequisites

- Two separate Slack workspaces, each with identical members, channels, and seed state, and exactly one of the two MCPs installed in each
- A `U05CLAUDE` user token (workspace owner) from each workspace

Workspace separation is mandatory — installing both MCPs into the same workspace causes OAuth scope conflicts and cross-contamination.

| Workspace | MCP installed | Claude config dir | Token env var |
|---|---|---|---|
| Hintas workspace | Hintas MCP (`https://slack-demo.infra.hintas.com/mcp`) | `~/.claude-hintas` | `HINTAS_TOKEN` |
| Slack workspace | Official Slack MCP (`https://mcp.slack.com/mcp`) | `~/.claude-slack` | `SLACK_TOKEN` |

Both workspaces must have:

- The same timezone (`America/Los_Angeles`)
- The same 10 users with identical emails and display names:

| Logical ID | Email | Display Name |
|---|---|---|
| U02JARED | jared@hintas.co | Jared |
| U03PINKMAN | pinkman@hintas.co | Pinkman |
| U04LAGOON | lagoon@hintas.co | Lagoon |
| U05CLAUDE | miranda@hintas.co | Miranda *(the agent — workspace owner)* |
| U06DEVON | devon@hintas.co | Devon |
| U07RHEA | rhea@hintas.co | Rhea |
| U08TOMAS | tomas@hintas.co | Tomas |
| U09EMBER | ember@hintas.co | Ember *(deactivate after invite)* |
| U10BOT_CI | — | ci-bot *(Slack app/bot)* |

If you use different emails, copy `platforms/slack/scripts/users.json` → `users.local.json` and map the logical IDs to your actual emails. `users.local.json` is gitignored and takes priority over the committed sample.

- The same OAuth scopes granted to both MCP installs. Core run scopes:

```
channels:history, channels:read, channels:write, channels:write.invites,
chat:write,
dnd:read, dnd:write,
groups:history, groups:read, groups:write, groups:write.invites,
im:history, im:read, im:write, im:write.topic,
mpim:history, mpim:write,
reactions:read, reactions:write,
reminders:read, reminders:write,
users.profile:read, users:read, users:read.email
```

Extension run adds: `pins:read, pins:write, files:read, files:write, search:read, emoji:read, users.profile:write, mpim:read`. Each prompt's `required_scopes` field tells you exactly what it needs.

## One-time setup

### 1. Claude config dirs for each MCP

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Create them once, then register the appropriate MCP server inside each:

```bash
mkdir -p ~/.claude-hintas ~/.claude-slack

# Hintas variant
CLAUDE_CONFIG_DIR=~/.claude-hintas claude mcp add ...

# Slack baseline
CLAUDE_CONFIG_DIR=~/.claude-slack claude mcp add ...
```

Complete the OAuth flow for each MCP once (the Slack MCP uses OAuth against the Slack endpoint; the Hintas MCP is direct HTTP).

### 2. Install Python deps and tokens

```bash
uv sync

export HINTAS_TOKEN=xoxp-<U05CLAUDE-token-from-hintas-workspace>
export SLACK_TOKEN=xoxp-<U05CLAUDE-token-from-slack-workspace>
```

### 3. Manual setup that can't be scripted

Some state needs each user's own token or admin actions and must be done once in the Slack UI on **both** workspaces:

- Custom emoji `:raider_skull:`, `:gold_gold:`, `:ship_it_raider:` (alias of `:ship_it:`) — Slack UI → Customize → Emoji
- Deactivate `U09EMBER` — Workspace Settings → Members
- Jared's DND schedule — nightly 22:00–07:00 Pacific (from Jared's own account)
- Pinkman's DND snooze — 2h pause at benchmark_now (from Pinkman's own account)

Timestamp backdating is not available on the free plan, so seeded messages carry real wall-clock timestamps. Graders match messages by content, not by absolute `ts`.

## Filtering and variants

With `SLACK_TOKEN` and `HINTAS_TOKEN` already exported:

```bash
# Filter to specific prompts / difficulties / categories
uv run python benchmark.py --prompt-ids 1 22 40

uv run python benchmark.py --difficulty L1 L2 --category retrieval

# Core + Extension scopes (~60 prompts)
uv run python benchmark.py --feasibility core extension
```

## Adding a prompt

Append to `platforms/slack/prompts/benchmark_prompts.json`:

```json
{
  "id": 66,
  "title": "Short descriptive title",
  "difficulty": "L2",
  "category": "retrieval",
  "feasible_on_free_plan": "core",
  "required_scopes": ["channels:read"],
  "prompt": "What the agent is actually asked to do.",
  "success_criteria": [
    "Returns N public channels.",
    "Each entry includes member count."
  ]
}
```

Difficulties are `L1`..`L5`. Categories: `retrieval`, `search`, `write`, `workflow`, `orchestration`, `edge_case`. `feasible_on_free_plan`: `core`, `extension`, or `infeasible`.

## Slack folder layout

```
platforms/slack/
├── slack.toml                      # platform manifest
├── prompts/benchmark_prompts.json  # 65 prompts, success criteria, expected tools
├── scripts/
│   ├── seed_workspace.py           # full idempotent workspace seed
│   ├── reset_workspace.py          # per-prompt state restore
│   ├── verify_workspace.py         # post-reset state check
│   ├── users.json                  # committed sample email mapping
│   ├── users.local.json            # optional gitignored override
│   └── workspace_state_ids_<team>.json  # auto-generated per workspace by seeder
├── api/                            # Slack API reference (OpenAPI + summary)
└── state/workspace_state.v3.md     # canonical seeded state spec
```

## Troubleshooting

- **Seed fails on `name_taken`** — the workspace has stale channels. Either delete them in the Slack UI or let the seeder continue; it detects and reuses existing channels.
- **Reset fails** — check the corresponding `workspace_state_ids_<team>.json` file exists in `platforms/slack/scripts/`. The seeder writes it during the first successful seed. The reset script auto-picks the right file from `auth.test`'s `team_id`.
- **Two workspaces drift** — after several benchmark runs, the seeder should keep both workspaces aligned. If not, archive both and re-invite members; the seeder's channel/message wipe only covers agent-authored state.
- **OAuth refresh for Slack MCP** — if the Slack-MCP sessions all `401`, re-authenticate by running `claude` once with `CLAUDE_CONFIG_DIR=~/.claude-slack` and completing the browser flow.
