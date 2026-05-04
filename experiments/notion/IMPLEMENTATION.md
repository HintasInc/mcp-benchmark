# Notion benchmark: implementation

Two parallel Notion workspaces, with one mirroring the other, allow A/B testing of the **Notion MCP - Official** against the **Notion MCP - Hintas** on identical state. Pick a stack with `--stack notion` (baseline) or `--stack hintas` (variant); see the [parent README](../../README.md) and [root IMPLEMENTATION.md](../../IMPLEMENTATION.md) for orchestrator usage.

## Why two workspaces

Installing both MCPs into the same Notion workspace mixes their per-page integration shares and contaminates the unshared-target tests. Each workspace must end up in identical state (same users, pages, databases, rows, and shared/unshared boundaries), or the comparison isn't fair.


| Workspace   | MCP installed       | Workspace token env |
| ----------- | ------------------- | ------------------- |
| Notion-side | Notion MCP - Official| `NOTION_TOKEN`      |
| Hintas-side | Notion MCP - Hintas   | `HINTAS_TOKEN`      |


Tokens go in `experiments/notion/.env` (see `.env.example`). Use the **internal integration secret** (`ntn_…` or `secret_…`) from each workspace's own `Hintas Agent` integration, not a single token shared between them.

## Workspace contract


| Field                   | Value                 |
| ----------------------- | --------------------- |
| Workspace name          | `Hintas`              |
| Timezone                | `America/Los_Angeles` |
| Locale                  | `en-US`               |
| `Notion-Version` header | `2022-06-28`          |


## Per-workspace setup

> Repeat for both workspaces. The workspace is destructive: prompts create, archive, restore, rename, mutate, and comment on pages. Don't point at a real workspace.

### 1. Invite the 9 users

Invite the users specified in `experiments/notion/scripts/users.json` (overridable via `users.local.json`). The user whose token will be used for benchmarking should have `benchmark-author: true`.

- `**U03PINKMAN`**: legal name is `Saul Rivera`, but the workspace **display name must be `Pinkman`**. Several prompts grade on resolving the `pinkman` handle.
- `**U09EMBER**`: invite first, **capture her user ID, then revoke access**. The benchmark tests the revoked-but-resolvable pattern.

### 2. Create the manual top-level entities

Notion's integration tokens can't create workspace-parented pages or grant their own integration access, so these have to be made by hand from the sidebar:

- `**Hintas`**: top-level page, icon 🎮. The seeder populates the full hierarchy under this.
- `**🔒 Leads-only**`: separate top-level page (sibling, not under `Hintas`), with one child page `**Leads sync notes**`.
- `**Press Contacts**`: empty database, parented anywhere not visible to the integration (easiest is under `🔒 Leads-only`).

Copy each entity's UUID from its URL or share-link panel; record them in step 4.

### 3. Create the `Hintas Agent` internal integration

Settings → Integrations → **Develop your own integrations** → **New integration**. Type must be **Internal** (public OAuth integrations don't expose a static `secret_…` token). Capabilities for a core run:

```
read_content, update_content, insert_content,
read_user_info,
read_comments, insert_comments
```

Extension run adds `read_user_with_email`. Each prompt's `required_scopes` field lists exactly what it needs.

Save and copy the secret token. Then on each top-level page in the sidebar, click `···` → **Connections** → add `Hintas Agent`:

- ✅ Share `Hintas` (descendants inherit).
- ❌ Don't share `🔒 Leads-only`, `Leads sync notes`, or `Press Contacts`. The seeder verifies these return 404 before proceeding.

### 4. Record the per-workspace pre-seed IDs

Save the UUIDs for the entities created in step 2 (and Ember's user ID) in `experiments/notion/scripts/prerequisites.json`. The orchestrator picks the right one automatically based on the stack name.

## Local machine setup

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Run `claude` once with each `CLAUDE_CONFIG_DIR` specified in `notion.toml` to complete the OAuth flow. MCP authentication must be completed manually before starting the benchmark.

## Sanity-check and seed

```bash
# Dry-run; auths, lists users, and stops with a "would create" plan.
uv run python experiments/notion/scripts/seed_workspace.py --verify \
  --state-file <path-to-state> \
  --prereq-file <path-to-prereq>
```

Drop `--verify` to seed for real. The orchestrator (`uv run benchmark run`) handles seed/reset/verify automatically per stack, so direct invocations are only for sanity-checking and recovery.

## Workspace overview

The seeder builds out a small game-studio workspace under `Hintas` with the entities a prompt suite needs to exercise read, write, search, and access-boundary paths.

- **Pages**: a team directory, project pages for in-flight games (`Tomb-3`, `Launch-26`), meeting notes, a playtest archive (one page archived to test restore), and assorted sub-pages with mixed block types (callouts, toggles with image children, and code blocks).
- **Databases**: `Bugs` (`BUG-NNN` IDs), `Tasks` (with a calendar-surface `Due` date), and `Meeting Notes` (with a `Follow-ups` rich-text column carrying user/page mentions).
- **Comments**: page-level and block-level comments seeded on the Tomb-3 and BUG-247 surfaces, all authored by the integration bot.
- **Access boundaries**: `🔒 Leads-only`, `Leads sync notes`, and `Press Contacts` are intentionally **not** shared with the integration. Calls against them return 404, and they never appear in `search` results.
- **User semantics**: `U09EMBER` is revoked. She's absent from `listUsers`, but `retrieveUser` against her last-known ID still returns her record. `@Ember` is intentionally absent from all seeded content.

The full ground truth (UUIDs, titles, schemas, row values, mention segments, and comment contents) lives in `experiments/notion/scripts/workspace_state_ids_<stack>.json` (auto-emitted by the seeder) and `state/workspace_state.md`. The seed/reset/verify scripts own that contract, so operators don't need to track it by hand.

## Reset

Most prompts are destructive, so the workspace is reset before every prompt run. The orchestrator handles this automatically; for direct invocations use `experiments/notion/scripts/reset_workspace.py`.