# Notion platform — Hintas vs Notion MCP

Two parallel Notion workspaces — one mirroring the other — let us A/B the official **Notion MCP** against the **Hintas Notion MCP** on identical state. Pick a stack with `--stack notion` (baseline) or `--stack hintas` (variant); see the [parent README](../../README.md) and [IMPLEMENTATION.md](../../IMPLEMENTATION.md) for orchestrator usage.

**Benchmark clock anchor:** `2026-04-19T10:00:00-07:00` — every time-relative prompt resolves against this, not your wall clock.

## Why two workspaces

Installing both MCPs into the same Notion workspace mixes their per-page integration shares and contaminates the unshared-target tests. Each workspace must end up in identical state — same users, pages, databases, rows, and shared/unshared boundaries — or the comparison isn't fair.


| Workspace   | MCP installed       | Workspace token env |
| ----------- | ------------------- | ------------------- |
| Notion-side | Official Notion MCP | `NOTION_TOKEN`      |
| Hintas-side | Hintas Notion MCP   | `HINTAS_TOKEN`      |


Tokens go in `experiments/notion/.env`:

```
NOTION_TOKEN=ntn_<token-from-Notion-side-Hintas-Agent-integration>
HINTAS_TOKEN=ntn_<token-from-Hintas-side-Hintas-Agent-integration>
```

Use the **internal integration secret** (`ntn_…` or `secret_…`) from each workspace's own `Hintas Agent` integration — not a single token shared between them.

## Per-workspace setup (do this twice — once per workspace)

### 1. Provision the workspace

- Workspace name: `Hintas`. Timezone: `America/Los_Angeles`. Locale: `en-US`.
- This is destructive — prompts create, archive, restore, rename, mutate, and comment on pages. Don't point at a real workspace.

### 2. Invite the 9 users

Invite the users that are specified in `experiments/notion/scripts/users.json`. This can be overridden using `experiments/notion/scripts/users.local.json`. The user whose token will be used for the benchmarking, their `benchmark-author` should be set to true.

**Pinkman's display name must be `Pinkman`**, not `Saul Rivera` — several prompts grade on resolving the `pinkman` handle and break silently otherwise.

After inviting Ember, **capture her user ID before revoking access** — the benchmark tests that revoked-but-resolvable pattern, which only appears for revoked (not deleted) users:

```bash
curl https://api.notion.com/v1/users \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" | jq '.results[] | select(.person.email=="ember@hintas.co") | .id'
```

Then Settings → Members → remove `ember@hintas.co`.

### 3. Create the manual top-level entities

Notion's integration tokens can't create workspace-parented pages or grant their own integration access — these have to be made by hand from the sidebar:

- `**Hintas**` — top-level page, icon 🎮 (the seeder populates the full hierarchy under this).
- `**🔒 Leads-only**` — separate top-level page (sibling, not under `Hintas`), with one child page `**Leads sync notes**`.
- `**Press Contacts**` — empty database, parented anywhere not visible to the integration (easiest: under `🔒 Leads-only`). Schema and rows aren't graded — the test is that the integration can't see it.

Copy each entity's UUID from its URL or share-link panel; you'll record them in step 5.

### 4. Create the `Hintas Agent` internal integration

Settings → Integrations → **Develop your own integrations** → **New integration**. Type must be **Internal** — public OAuth integrations don't expose a static `secret_…` token. Capabilities for a core run:

```
read_content, update_content, insert_content,
read_user_info,
read_comments, insert_comments
```

Extension run adds `read_user_with_email` (required for prompts that look up users by email or read `person.email`). Each prompt's `required_scopes` field lists exactly what it needs.

Save and copy the secret token (`secret_…` or `ntn_…`). Then on each top-level page in the sidebar, click `···` → **Connections** → add `Hintas Agent`:

- ✅ Share `Hintas` (descendants inherit).
- ❌ Don't share `🔒 Leads-only`, `Leads sync notes`, or `Press Contacts`. The seeder verifies these return 404 before proceeding.

### 5. Record the per-workspace pre-seed IDs

Each workspace has its own UUIDs for the entities created in step 3 (and Ember's user ID). Save them in a per-stack file (gitignored, `*.local.json`); the orchestrator picks the right one automatically based on the stack name.

```
experiments/notion/scripts/prerequisites_notion.local.json   ← Notion-side
experiments/notion/scripts/prerequisites_hintas.local.json   ← Hintas-side
```

Each file:

```json
{
  "P08_LEADS_ONLY":     "<UUID of 🔒 Leads-only>",
  "P11_LEADS_NOTES":    "<UUID of Leads sync notes>",
  "DB_PRESS_CONTACTS":  "<UUID of Press Contacts database>",
  "U09EMBER":           "<UUID of Ember Shah>"
}
```

## Local machine setup

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated:

```bash
mkdir -p ~/.claude-notion ~/.claude-notion-hintas

CLAUDE_CONFIG_DIR=~/.claude-notion        claude mcp add notion        ...
CLAUDE_CONFIG_DIR=~/.claude-notion-hintas claude mcp add hintas-notion ...
```

Run `claude` once with each `CLAUDE_CONFIG_DIR` to complete the OAuth flow. The authentication for the MCP servers must be completed manually before starting the benchmarking.

## Sanity-check and seed

```bash
# Dry-run each workspace; should auth, list users, and stop with a "would create" plan.
NOTION_TOKEN=$NOTION_TOKEN uv run python experiments/notion/scripts/seed_workspace.py --verify \
  --state-file experiments/notion/scripts/workspace_state_ids_notion.json \
  --prereq-file experiments/notion/scripts/prerequisites_notion.local.json
NOTION_TOKEN=$HINTAS_TOKEN uv run python experiments/notion/scripts/seed_workspace.py --verify \
  --state-file experiments/notion/scripts/workspace_state_ids_hintas.json \
  --prereq-file experiments/notion/scripts/prerequisites_hintas.local.json
```

Drop `--verify` to seed for real. The orchestrator (`uv run benchmark run`) handles seed/reset/verify automatically per stack — these direct invocations are only for sanity-checking and recovery.

## Adding a prompt

Append to `experiments/notion/prompts/benchmark_prompts.json`:

```json
{
  "id": 61,
  "title": "Short descriptive title",
  "difficulty": "L2",
  "category": "retrieval",
  "feasible_on_free_plan": "core",
  "required_scopes": ["read_content"],
  "prompt": "What the agent is actually asked to do.",
  "success_criteria": [
    "Returns N rows from DB_TASKS.",
    "Each row includes Owner and Due."
  ]
}
```

Difficulties: `L1`..`L5`. Categories: `retrieval`, `search`, `write`, `workflow`, `orchestration`, `edge_case`. `feasible_on_free_plan`: `core`, `extension`, or `infeasible`. `required_scopes` lists the integration capabilities the prompt needs (`read_content`, `update_content`, `insert_content`, `read_user_info`, `read_comments`, `insert_comments`, `read_user_with_email`).

## Folder layout

```
experiments/notion/
├── notion.toml                     # platform manifest
├── prompts/benchmark_prompts.json  # 60 prompts, success criteria, expected tools
├── scripts/
│   ├── seed_workspace.py           # full idempotent workspace seed
│   ├── reset_workspace.py          # per-prompt state restore
│   ├── verify_workspace.py         # post-reset state check
│   ├── users.json                  # committed sample email mapping
│   ├── users.local.json            # optional gitignored override
│   ├── prerequisites_<stack>.local.json    # per-stack pre-seed UUIDs (gitignored)
│   └── workspace_state_ids_<stack>.json    # auto-generated per workspace by seeder
├── api/                            # Notion API reference (OpenAPI)
└── state/workspace_state.md        # canonical seeded state spec
```

## Troubleshooting

- `**No page titled 'Hintas' is shared to this integration**` — re-do the share step (page `···` → Connections → add `Hintas Agent`).
- `**… IS visible to the integration — must be unshared**` — the integration was accidentally connected to `🔒 Leads-only`, `Leads sync notes`, or `Press Contacts`. Remove the connection from those entities.
- `**prerequisites file is missing IDs for: …**` — capture the missing UUID(s) and re-record into `prerequisites_<stack>.local.json`.
- `**U09EMBER … is still present in /users; expected revoked**` — Ember was invited but never removed. After capturing her UUID, remove her under Settings → Members.
- `**U03PINKMAN display name is …; expected 'Pinkman'**` — rename Saul Rivera's display name to `Pinkman` in Members.
- **Reset fails** — check `workspace_state_ids_<stack>.json` exists. The seeder writes it on first successful seed; reset auto-picks the right file based on the workspace the token authenticates against.
- **Two workspaces drift** — archive the seeded subtree under `Hintas` in the misaligned workspace and re-run the seeder. Unshared targets and human-membership state are preserved.

## Known limits of single-token Scenario A

Every seeded row, block, and comment is `created_by` the integration bot, not by the human users (`U01MIRANDA`, `U02JARED`, …). `state/workspace_state.md` §8 documents that all seeded comments are bot-authored, and no prompt grades `created_by` against a human user.