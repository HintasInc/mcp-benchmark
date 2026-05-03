# Slack platform — Hintas vs Slack MCP

Two parallel Slack workspaces — one mirroring the other — let us A/B the official **Slack MCP** against the **Hintas Slack MCP** on identical state. Pick a stack with `--stack slack` (baseline) or `--stack hintas` (variant); see the [parent README](../../README.md) and [IMPLEMENTATION.md](../../IMPLEMENTATION.md) for orchestrator usage.

**Benchmark clock anchor:** `2026-04-19T10:00:00-07:00` — every time-relative prompt resolves against this, not your wall clock. Slack doesn't expose timestamp backdating outside paid Discovery API access, so seeded messages carry real wall-clock `ts` values; graders match by content, not absolute `ts`. The day-offset table in `state/workspace_state.v3.md` is the canonical authoring order.

## Why two workspaces

Installing both MCPs into one workspace causes OAuth-scope conflicts and cross-contamination. Each workspace must end up in identical state — same users, channels, messages, reactions, DMs, archived/deactivated boundaries — or the comparison isn't fair.

| Workspace   | MCP installed                                                | Claude config dir  | Workspace token env |
| ----------- | ------------------------------------------------------------ | ------------------ | ------------------- |
| Slack-side  | Official Slack MCP (`https://mcp.slack.com/mcp`)             | `~/.claude-slack`  | `SLACK_TOKEN`       |
| Hintas-side | Hintas Slack MCP (`https://slack-demo.infra.hintas.com/mcp`) | `~/.claude-hintas` | `HINTAS_TOKEN`      |

Tokens go in `experiments/slack/.env`:

```
SLACK_TOKEN=xoxp-<U05CLAUDE-token-from-slack-workspace>
HINTAS_TOKEN=xoxp-<U05CLAUDE-token-from-hintas-workspace>
```

Use the **User OAuth token** (`xoxp-…`), not the bot token (`xoxb-…`) — many graded calls (1:1 DM history, profile reads, reminders) require a user token.

## Per-workspace setup (do this twice — once per workspace)

### 1. Provision the workspace

- Plan: **Enterprise Grid** — required for `admin.users.*`, `admin.conversations.*`, `admin.emoji.*`, and `admin.conversations.setConversationPrefs`. Without these, several prompts can't be graded.
- Workspace name: `Hintas`. Timezone: `America/Los_Angeles`. Locale: `en-US`.
- **Discovery API: not enabled.** Some edge-case prompts assume an admin token cannot read other pairs' 1:1 DMs.
- This is destructive — prompts post, edit, delete, archive, kick, react, and DM across channels. Don't point at a real workspace.

### 2. Invite the 8 human users

Use these emails exactly, or override them in `experiments/slack/scripts/users.local.json` (gitignored, copy from `users.json`). The 9th workspace member — the `ci-bot` service account — is installed via app manifest in step 3, not invited like the humans.

| Logical ID   | Email               | Display name                            | Workspace role                                  |
| ------------ | ------------------- | --------------------------------------- | ----------------------------------------------- |
| `U02JARED`   | `jared@hintas.co`   | Jared                                   | Member, Engineering Manager                     |
| `U03PINKMAN` | `pinkman@hintas.co` | **Pinkman** *(real name `Saul Rivera`)* | Member, QA Lead                                 |
| `U04LAGOON`  | `lagoon@hintas.co`  | Lagoon                                  | Member, Marketing & Community                   |
| `U05CLAUDE`  | `miranda@hintas.co` | Miranda *(the agent)*                   | **Owner / Admin / Org Primary Owner**           |
| `U06DEVON`   | `devon@hintas.co`   | Devon                                   | Member, Backend Engineer                        |
| `U07RHEA`    | `rhea@hintas.co`    | Rhea                                    | Member, Frontend Engineer                       |
| `U08TOMAS`   | `tomas@hintas.co`   | Tomas                                   | Member, QA Tester                               |
| `U09EMBER`   | `ember@hintas.co`   | Ember                                   | Member, **then deactivate (do not delete)**     |

- **`U05CLAUDE` is the agent** — every seeded message, reaction, reminder, and file upload is authored by this account (Scenario A — single-token).
- **Pinkman's display name must be `Pinkman`**, not `Saul`. Several prompts grade on resolving the `pinkman` handle and break silently otherwise.
- **Deactivate Ember, don't delete** — `users.info` must still resolve her ID even though she's absent from `users.list?include_deleted=false`. That pattern only appears for deactivated (not deleted) users.

### 3. Add the CI bot user (`U10BOT_CI`)

The `#incidents` channel and a couple of prompts depend on a non-human author called `ci-bot`. api.slack.com → **Create New App** → **From an app manifest** → paste `experiments/slack/scripts/slack_app_manifest.json` → install → add the bot to `#incidents` and `#general`. The bot doesn't need a token exported anywhere — it just needs to exist as a workspace member so channel counts and historical authorship stay coherent.

### 4. Create the custom emoji

Slack's API doesn't expose `emoji.add` to user tokens, so this must be done by hand under Customize Workspace → Emoji:

- `:raider_skull:` — custom 128×128 PNG. Used in seeded reactions on `M11`.
- `:gold_gold:` — custom 128×128 PNG. Must end up with **zero usage** in seeded reactions (prompt 57 asserts this).
- `:ship_it_raider:` — **alias of `:ship_it:`** (use Slack UI's "Add alias"), not a fresh upload. The alias path is exercised by prompt grading.

### 5. Configure DND and snooze (from each user's own session)

Slack's DND endpoints only edit the calling user's own state, so these must be set from the relevant account:

- **Jared (`U02JARED`)** — DND schedule `22:00–07:00` Pacific, every day. At `benchmark_now` (Sunday 10:00 PT) the nightly window is **not** active; that's intentional.
- **Pinkman (`U03PINKMAN`)** — snooze for **2 hours** at the start of each benchmark run, so the snooze ends at `benchmark_now + 2h` (= 12:00 PT Sunday). This isn't durable across days; re-arm before each run.

Everyone else stays on presence `auto` with no active snooze.

### 6. Get the `U05CLAUDE` user token

Sign in as Miranda, create a Slack app, and grant the scopes the benchmark requires. Core run set:

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

Extension run adds: `pins:read, pins:write, files:read, files:write, search:read, emoji:read, users.profile:write, mpim:read`. Each prompt's `required_scopes` field lists exactly what it needs.

Install the app and copy the **User OAuth Token** (`xoxp-…`) into the env var matrix above.

## Local machine setup

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated:

```bash
mkdir -p ~/.claude-slack ~/.claude-hintas

CLAUDE_CONFIG_DIR=~/.claude-slack  claude mcp add slack        ...
CLAUDE_CONFIG_DIR=~/.claude-hintas claude mcp add hintas-slack ...
```

Run `claude` once with each `CLAUDE_CONFIG_DIR` to complete the OAuth flow.

## Sanity-check and seed

```bash
# Dry-run each workspace; should auth, list users, and stop with a "would create" plan.
SLACK_TOKEN=$SLACK_TOKEN  uv run python experiments/slack/scripts/seed_workspace.py --verify
SLACK_TOKEN=$HINTAS_TOKEN uv run python experiments/slack/scripts/seed_workspace.py --verify
```

Drop `--verify` to seed for real. The seeder keys its state file by Slack's `team_id` so the two workspaces don't clobber each other. The orchestrator (`uv run benchmark run`) handles seed/reset/verify automatically per stack — these direct invocations are only for sanity-checking and recovery.

### Post-seed UI fixups

Slack's API doesn't cover the following — do them in the Slack UI in **both** workspaces after the seeder finishes:

1. **`#announcements` posting restriction.** Channel settings → Posting permissions → **Specific people** → admins + owners only. Several prompts grade on the assumption that non-admins receive `restricted_action` when posting here.
2. **Confirm `#old-playtest-2025` is archived.** The seeder archives it on first creation, but a previous test run may have unarchived it.
3. **Re-arm Pinkman's 2h snooze** if the seeder is being run more than ~2h before the benchmark.

## Adding a prompt

Append to `experiments/slack/prompts/benchmark_prompts.json`:

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

Difficulties: `L1`..`L5`. Categories: `retrieval`, `search`, `write`, `workflow`, `orchestration`, `edge_case`. `feasible_on_free_plan`: `core`, `extension`, or `infeasible`.

## Folder layout

```
experiments/slack/
├── slack.toml                      # platform manifest
├── prompts/benchmark_prompts.json  # 65 prompts, success criteria, expected tools
├── scripts/
│   ├── seed_workspace.py           # full idempotent workspace seed
│   ├── reset_workspace.py          # per-prompt state restore
│   ├── verify_workspace.py         # post-reset state check
│   ├── users.json                  # committed sample email mapping
│   ├── users.local.json            # optional gitignored override
│   └── workspace_state_<team>.json # auto-generated per workspace by seeder
├── api/                            # Slack API reference (OpenAPI + summary)
└── state/workspace_state.v3.md     # canonical seeded state spec
```

## Troubleshooting

- **Seed fails on `name_taken`** — workspace has stale channels. Either delete them in the Slack UI or let the seeder continue; it detects and reuses existing channels.
- **Reset fails** — check `workspace_state_<team_id>.json` exists. The seeder writes it on first successful seed; the reset script auto-picks the right file from `auth.test`'s `team_id`.
- **Two workspaces drift** — archive both and re-invite members; the seeder's channel/message wipe only covers agent-authored state.

## Known limits of single-token Scenario A

Every seeded message, reaction, reminder, scheduled message, and file upload is authored by `U05CLAUDE` (the agent), not by the human users (`U02JARED`, `U03PINKMAN`, …) named in the message tables of `state/workspace_state.v3.md`. Prompts that grade `author_id` against humans will diverge from the spec unless an operator manually re-authors key items from each user's own session. The `ci-bot` messages (`M12`, `M12b`) in `#incidents` are similarly skipped — bot tokens cannot author them via `chat.postMessage`.
