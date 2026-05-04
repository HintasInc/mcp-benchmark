# Slack benchmark: implementation

Two parallel Slack workspaces, with one mirroring the other, allow A/B testing of the **Slack MCP - Official** against the **Slack MCP - Hintas** on identical state. Pick a stack with `--stack slack` (baseline) or `--stack hintas` (variant); see the [parent README](../../README.md) and [root IMPLEMENTATION.md](../../IMPLEMENTATION.md) for orchestrator usage.

## Why two workspaces

Installing both MCPs into one workspace causes OAuth-scope conflicts and cross-contamination. Each workspace must end up in identical state (same users, channels, messages, reactions, DMs, and archived/deactivated boundaries), or the comparison isn't fair.


| Workspace   | MCP installed                                                  | Workspace token env |
| ----------- | -------------------------------------------------------------- | ------------------- |
| Slack-side  | Slack MCP - Official (`https://mcp.slack.com/mcp`)             | `SLACK_TOKEN`       |
| Hintas-side | Slack MCP - Hintas (`https://slack-demo.infra.hintas.com/mcp`) | `HINTAS_TOKEN`      |


Tokens go in `experiments/slack/.env` (see `.env.example`). Use the **User OAuth token** (`xoxp-…`), not the bot token (`xoxb-…`).

## Workspace contract


| Field          | Value                 |
| -------------- | --------------------- |
| Workspace name | `Hintas`              |
| Timezone       | `America/Los_Angeles` |
| Locale         | `en-US`               |


## Per-workspace setup

> Repeat for both workspaces. The workspace is destructive: prompts post, edit, delete, archive, kick, react, and DM across channels. Don't point at a real workspace.

### 1. Invite the 8 human users

Invite the users specified in `experiments/slack/scripts/users.json` (overridable via `users.local.json`). The user whose token will be used for benchmarking should have `benchmark-author: true`.The 9th workspace member, the `ci-bot` service account, is installed via app manifest in step 3 rather than invited like the humans.

- `**U05CLAUDE` is the agent**: every seeded message, reaction, reminder, and file upload is authored by this account (Scenario A, single-token).
- **Pinkman's display name must be `Pinkman`**, not `Saul`. Several prompts grade on resolving the `pinkman` handle and break silently otherwise.
- **Deactivate Ember, don't delete**: `users.info` must still resolve her ID even though she's absent from `users.list?include_deleted=false`. That pattern only appears for deactivated (not deleted) users.

### 2. Add the CI bot user (`U10BOT_CI`)

The `#incidents` channel and a couple of prompts depend on a non-human author called `ci-bot`. Go to api.slack.com → **Create New App** → **From an app manifest** → paste `experiments/slack/scripts/slack_app_manifest.json` → install → add the bot to `#incidents` and `#general`. The bot doesn't need a token exported anywhere; it just needs to exist as a workspace member so channel counts and historical authorship stay coherent.

### 3. Create the custom emoji

Slack's API doesn't expose `emoji.add` to user tokens, so this must be done by hand under Customize Workspace → Emoji:

- `:raider_skull:`: custom 128×128 PNG. Used in seeded reactions on `M11`.
- `:gold_gold:`: custom 128×128 PNG. Must end up with **zero usage** in seeded reactions (prompt 57 asserts this).
- `:ship_it_raider:`: an **alias of `:ship_it:`** (use Slack UI's "Add alias"), not a fresh upload. The alias path is exercised by prompt grading.

### 4. Configure DND and snooze (from each user's own session)

Slack's DND endpoints only edit the calling user's own state, so these must be set from the relevant account:

- **Jared (`U02JARED`)**: DND schedule `22:00–07:00` Pacific, every day. At `benchmark_now` (Sunday 10:00 PT) the nightly window is **not** active; that's intentional.
- **Pinkman (`U03PINKMAN`)**: snooze for **2 hours** at the start of each benchmark run, so the snooze ends at `benchmark_now + 2h` (= 12:00 PT Sunday). This isn't durable across days, so re-arm before each run.

Everyone else stays on presence `auto` with no active snooze.

### 5. Get the `U05CLAUDE` user token

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

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Run `claude` once with each `CLAUDE_CONFIG_DIR` specified in `slack.toml` to complete the OAuth flow. MCP authentication must be completed manually before starting the benchmark.

## Sanity-check and seed

```bash
# Dry-run each workspace; should auth, list users, and stop with a "would create" plan.
uv run python experiments/slack/scripts/seed_workspace.py --verify
```

Drop `--verify` to seed for real. The seeder keys its state file by Slack's `team_id` so the two workspaces don't clobber each other. The orchestrator (`uv run benchmark run`) handles seed/reset/verify automatically per stack, so these direct invocations are only for sanity-checking and recovery.

## Workspace overview

The seeder builds out the `Hintas` workspace with the entities a prompt suite needs to exercise read, write, search, and access-boundary paths.

- **Channels**: 9 public (`#general`, `#random`, `#eng-backend`, `#eng-frontend`, `#design-reviews`, `#qa-bugs`, `#marketing`, `#incidents`, `#announcements`), 2 private (`#launch-2026`, `#leads-only`), and 1 archived (`#old-playtest-2025`). `#announcements` is admin-post-only.
- **DMs and MPIMs**: 4 seeded 1:1 DMs and a 3-person MPIM (Miranda + Jared + Pinkman). The agent is a member of two DMs; the other two are intentionally unreadable to test the Discovery-API-disabled boundary.
- **Messages, threads, pins**: ~30 seeded messages across channels and DMs, two threads (parents in `#eng-backend` and `#general`), and pinned messages in `#launch-2026`, `#general`, and `#eng-backend`. One scheduled `#marketing` message at `benchmark_now + 23h`.
- **Reactions and emoji**: three custom emoji (`:raider_skull:`, `:gold_gold:`, `:ship_it_raider:` aliasing `:ship_it:`). Seeded reactions cover the standard, custom-image, and alias paths. `:gold_gold:` has zero seeded usage by design.
- **Reminders and files**: Miranda holds a single reminder for `benchmark_now + 8h`. Files are uploaded alongside seeded messages in `#design-reviews`, `#qa-bugs`, and `#marketing`.
- **Access boundaries**: private channels return `not_in_channel` for non-members, `#old-playtest-2025` is archived (writes fail until unarchived), and Discovery API is intentionally NOT enabled so the agent token cannot read DMs it isn't a party to.
- **User semantics**: `U09EMBER` is **deactivated** (not deleted), so `users.lookupByEmail` resolves her, but channel invites fail with a user-disabled error. `U10BOT_CI` (`ci-bot`) is a workspace bot member of `#general`, `#random`, `#eng-backend`, and `#incidents`. Do not DM it.

Under single-token Scenario A, every seeded message, reaction, reminder, scheduled message, and file upload is authored by `U05CLAUDE` (the agent), not by the human users (`U02JARED`, `U03PINKMAN`, …) the seeder attributes them to. Prompts that grade `author_id` against humans will diverge from the seeder's intent unless an operator manually re-authors key items from each user's own session. The `ci-bot` messages in `#incidents` are similarly skipped, since bot tokens cannot author them via `chat.postMessage`.

The full ground truth (channel IDs, message `ts` map, file IDs, reaction inventory, and thread parents) lives in `experiments/slack/scripts/workspace_state_<stack>.json` (auto-emitted by the seeder). The seed/reset/verify scripts own that contract, so operators don't need to track it by hand.

## Reset

Most prompts are destructive, so the workspace is reset before every prompt run. The orchestrator handles this automatically; for direct invocations use `experiments/slack/scripts/reset_workspace.py`, which loads `workspace_state_<team_id>.json` written by the seeder.