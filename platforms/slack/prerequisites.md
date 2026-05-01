# Slack Benchmark — Prerequisites

Manual setup that must be completed **before** running `platforms/slack/scripts/seed_workspace.py`. The seeder will fail (or produce a partially-correct workspace) if any of these steps are skipped.

The Slack benchmark uses a two-workspace design: one workspace per MCP under test. **Repeat steps 1–7 in each of the two workspaces.** Steps 8–9 are done once on your local machine.

| Workspace | MCP wired in | Token env var |
|---|---|---|
| Slack-side | Official Slack MCP (`https://mcp.slack.com/mcp`) | `SLACK_TOKEN` |
| Hintas-side | Hintas Slack MCP (`https://slack-demo.infra.hintas.com/mcp`) | `HINTAS_TOKEN` |

Both must end up in identical state — same users, same channels, same messages, same reactions, same DMs, same archived/deactivated boundaries — otherwise the A/B comparison isn't fair. Installing both MCPs into a single workspace causes OAuth-scope conflicts and cross-contamination, so the split is mandatory, not just convenient.

Benchmark clock anchor: `2026-04-19T10:00:00-07:00`. Every seeded message's `ts` is computed relative to this anchor, not your wall clock.

---

## Per-workspace setup (do this twice)

### 1. Provision a fresh Slack workspace

- Sign up at [slack.com](https://slack.com) for a brand-new workspace.
- Plan: **Enterprise Grid** (required so `admin.users.*`, `admin.conversations.*`, `admin.emoji.*`, and `admin.conversations.setConversationPrefs` are all available — without these, several prompts can't be graded).
- Workspace name: `Hintas`.
- Do **not** point this at a real workspace — prompts post, edit, delete, archive, kick, react, and DM across channels and members.
- Workspace Settings → Settings & Permissions → Settings:
  - Timezone: `America/Los_Angeles`
  - Locale: `en-US`
- Discovery API: **Not enabled**. Some edge-case prompts grade on the assumption that an admin token cannot read other pairs' 1:1 DMs.

### 2. Invite the 9 users

Workspace Settings → Manage Members → Invite People. Use exactly these emails, or override them by copying `platforms/slack/scripts/users.json` → `platforms/slack/scripts/users.local.json` (gitignored) and editing the values to your real emails.

| Logical ID | Email | Display name | Workspace role |
|---|---|---|---|
| `U02JARED`   | `jared@hintas.co`   | Jared    | Member, Engineering Manager |
| `U03PINKMAN` | `pinkman@hintas.co` | **Pinkman** (display name, real name `Saul Rivera`) | Member, QA Lead |
| `U04LAGOON`  | `lagoon@hintas.co`  | Lagoon   | Member, Marketing & Community |
| `U05CLAUDE`  | `miranda@hintas.co` | Miranda *(the agent — Workspace Owner + Org Primary Owner)* | **Owner / Admin** |
| `U06DEVON`   | `devon@hintas.co`   | Devon    | Member, Backend Engineer |
| `U07RHEA`    | `rhea@hintas.co`    | Rhea     | Member, Frontend Engineer |
| `U08TOMAS`   | `tomas@hintas.co`   | Tomas    | Member, QA Tester |
| `U09EMBER`   | `ember@hintas.co`   | Ember    | Member, **then deactivate** |

Two notes on the user list:

- **`U05CLAUDE` is the agent.** All seeded messages, reactions, reminders, and file uploads will be authored by this account (Scenario A — single-token). The previous `U01MIRANDA` persona is collapsed into `U05CLAUDE`.
- **Pinkman's display name must be `Pinkman`**, not `Saul`. Pinkman's real name is `Saul Rivera`. Several prompts grade on resolving the `pinkman` handle; getting this wrong breaks them silently.

After inviting `U09EMBER`, deactivate the account (Workspace Settings → Manage Members → row menu → Deactivate Account). The benchmark explicitly tests that `U09EMBER` is absent from active-user lists but still resolvable via `users.info` — that pattern only appears for deactivated (not deleted) users.

### 3. Add the CI bot user (`U10BOT_CI`)

The `incidents` channel and a couple of prompts depend on a non-human author called `ci-bot`. Create it as a Slack app:

- api.slack.com → **Create New App** → **From an app manifest** → pick this workspace.
- Paste the contents of `platforms/slack/scripts/slack_app_manifest.json`.
- Install the app to the workspace.
- Add the bot user to `#incidents` and `#general` (the seeder will pick it up by membership; it does not invite the bot itself).

The bot does not need its own token exported anywhere — it just needs to exist as a workspace member so that channel membership counts and historical message authorship are coherent.

### 4. Create the custom emoji

The Slack API does **not** expose `emoji.add` to user tokens, so this must be done by hand. Workspace Settings → Customize Workspace → Emoji → Add Custom Emoji:

- `:raider_skull:` — custom image, any 128×128 PNG. Used in seeded reactions on `M11`.
- `:gold_gold:` — custom image, any 128×128 PNG. Must end up with **zero usage** in seeded reactions (prompt 57 asserts this).
- `:ship_it_raider:` — **alias of `:ship_it:`**, not a fresh upload. The Slack UI exposes "Add alias" specifically for this. The alias path is exercised by prompt grading.

### 5. Configure DND and snooze (requires non-agent tokens)

These can't be set from `U05CLAUDE`'s token because Slack's DND endpoints only edit the calling user's own DND state. Sign in as the relevant user (or have them do it) and set:

- **Jared (`U02JARED`)** — Preferences → Notifications → Notify me only between → **22:00–07:00**, every day, `America/Los_Angeles`. At `benchmark_now` (Sunday 10:00 PT) the nightly window is **not** active; this is intentional.
- **Pinkman (`U03PINKMAN`)** — at the time you start a benchmark run, snooze notifications for **2 hours** so the snooze ends at `benchmark_now + 2h` (= 12:00 PT Sunday). Because real wall-clock is not `benchmark_now`, you may need to re-trigger this snooze just before each benchmark run; it is not durable across days.

Everyone else stays on presence `auto` with no active snooze.

### 6. Get the `U05CLAUDE` user token

Sign in as Miranda (`miranda@hintas.co`, `U05CLAUDE`) and create a Slack app with a user token holding the scope set the benchmark requires. The minimum core set is:

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

Extension prompts add: `pins:read, pins:write, files:read, files:write, search:read, emoji:read, users.profile:write, mpim:read`. Each prompt's `required_scopes` field tells you exactly what it needs.

Install the app to the workspace, then copy the **User OAuth Token** (`xoxp-…`). This is the value you'll export as `SLACK_TOKEN` (in the Slack-side workspace) or `HINTAS_TOKEN` (in the Hintas-side workspace).

> The bot token (`xoxb-…`) is **not** what the benchmark runs against — many graded calls (1:1 DM history, profile reads, reminders) require a user token. Use `xoxp-…`.

### 7. Wire each MCP into its workspace

The MCP that the agent uses at benchmark time is separate from the user token above. Both can coexist — the user token drives `seed_workspace.py` / `reset_workspace.py` / `verify_workspace.py`; the MCP drives the actual benchmark prompts.

- Slack-side workspace → install the **official Slack MCP** via its OAuth flow (endpoint `https://mcp.slack.com/mcp`).
- Hintas-side workspace → install the **Hintas Slack MCP** via its OAuth flow (endpoint `https://slack-demo.infra.hintas.com/mcp`).

Do not install both into the same workspace.

---

## Local machine setup (do this once)

### 8. Claude config dirs

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Create them once, then register each MCP server inside its config dir using `claude mcp add` (or by editing `config.json` directly):

```bash
mkdir -p ~/.claude-slack ~/.claude-hintas

# Slack baseline → register the official Slack MCP (https://mcp.slack.com/mcp)
CLAUDE_CONFIG_DIR=~/.claude-slack claude mcp add ...

# Hintas variant → register the Hintas Slack MCP (https://slack-demo.infra.hintas.com/mcp)
CLAUDE_CONFIG_DIR=~/.claude-hintas claude mcp add ...
```

Then run `claude` once with each `CLAUDE_CONFIG_DIR` to complete the OAuth flow.

### 9. Export both tokens

```bash
export SLACK_TOKEN=xoxp-<U05CLAUDE-token-from-slack-side-workspace>
export HINTAS_TOKEN=xoxp-<U05CLAUDE-token-from-hintas-side-workspace>
```

The orchestrator (`benchmark.py`) reads both, then invokes each script twice — once per workspace, swapping the token into the `SLACK_TOKEN` slot. The seed/reset/verify scripts themselves only read `SLACK_TOKEN`; that's intentional.

You can also commit these to a local `.env` (gitignored) — see `.env.example` at the repo root.

---

## Sanity-check before seeding

From the repo root, with both tokens exported:

```bash
# Dry-run against each workspace; each should auth, list users, and stop with a
# "would create" plan if the workspace is empty.
SLACK_TOKEN=$SLACK_TOKEN  uv run python platforms/slack/scripts/seed_workspace.py --verify
SLACK_TOKEN=$HINTAS_TOKEN uv run python platforms/slack/scripts/seed_workspace.py --verify
```

If either dry-run reports `Could not resolve <email>`, revisit step 2 (and `users.local.json` if you used custom emails).
If the auth check warns that the workspace name is not `Hintas`, double-check you exported the right token.

---

## Live seed

```bash
SLACK_TOKEN=$SLACK_TOKEN  uv run python platforms/slack/scripts/seed_workspace.py
SLACK_TOKEN=$HINTAS_TOKEN uv run python platforms/slack/scripts/seed_workspace.py
```

Each run writes `platforms/slack/scripts/workspace_state_ids_<team_id>.json` — keyed by Slack's `team_id`, so running twice from the same checkout against two workspaces does **not** clobber state. `reset_workspace.py` auto-picks the right file from `auth.test`'s `team_id` on each invocation.

---

## Post-seed UI fixups

Slack's API doesn't cover the following — do them in the Slack UI in **both** workspaces after the seeder finishes:

1. **`#announcements` posting restriction.** Channel settings → Posting permissions → **Specific people** → admins + owners only. Several prompts grade on the assumption that non-admins receive `restricted_action` when posting here.
2. **Confirm `#old-playtest-2025` is archived.** The seeder archives it on first creation, but a previous test run may have unarchived it. Channel header → Settings → Archive if needed.
3. **Confirm `U09EMBER` is deactivated**, not deleted. `users.info` must still resolve the ID; `users.list?include_deleted=false` must omit it.
4. **Confirm Pinkman's display name is `Pinkman`**, real name `Saul Rivera`.
5. **Re-arm Pinkman's 2h snooze** if the seeder is being run more than ~2h before the benchmark (see step 5).

After the fixups, run the verifier:

```bash
SLACK_TOKEN=$SLACK_TOKEN  uv run python platforms/slack/scripts/verify_workspace.py
SLACK_TOKEN=$HINTAS_TOKEN uv run python platforms/slack/scripts/verify_workspace.py
```

Hard drift count should be 0 in both.

---

## Then run the benchmark

With both tokens loaded into `platforms/slack/.env` and both workspaces verified clean:

```bash
uv run python benchmark.py --stack slack    # baseline
uv run python benchmark.py --stack hintas   # variant
```

`--platform slack` is the default and can be omitted. See the parent [`README.md`](../../README.md) for filtering flags (`--prompt-ids`, `--difficulty`, `--category`, `--feasibility`, `--skip-setup`, `--dry-run`).

---

## Known limits of single-token Scenario A

Every seeded message, reaction, reminder, scheduled message, and file upload is authored by `U05CLAUDE` (the agent), not by the human users (`U02JARED`, `U03PINKMAN`, …) named in the message tables of `state/workspace_state.v3.md`. Prompts that grade `author_id` against humans will diverge from the spec unless an operator manually re-authors key items from each user's own session. The `ci-bot` messages (`M12`, `M12b`) in `#incidents` are similarly skipped — bot tokens cannot author them via `chat.postMessage`.

Timestamp backdating is not available outside of paid Discovery API access, so seeded messages carry real wall-clock `ts` values rather than offsets from `benchmark_now`. Graders match messages by content, not by absolute `ts`. The day-offset table in `state/workspace_state.v3.md` is the canonical authoring order; the seeder applies offsets only as `oldest`/`latest` window hints, not as on-the-wire timestamps.
