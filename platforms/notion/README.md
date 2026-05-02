# Notion platform — Hintas vs Notion MCP

Notion-specific setup and wiring for the `notion` platform registered in `platforms/notion/notion.toml`. Two stacks are declared — the official **Notion MCP** and the **Hintas Notion MCP** — each pointed at its own mirrored Notion workspace. Pick one with `--stack <name>` per invocation.

Benchmark clock anchor: `2026-04-19T10:00:00-07:00`. All time-relative prompts resolve against this, not your wall clock.

## Run it

Put the workspace tokens in `platforms/notion/.env` (or `export` them), then run one stack at a time:

```bash
# platforms/notion/.env
NOTION_TOKEN=secret_<token-from-notion-side-internal-integration>
HINTAS_TOKEN=secret_<token-from-hintas-side-internal-integration>
```

```bash
uv run python benchmark.py --platform notion --stack notion    # baseline
uv run python benchmark.py --platform notion --stack hintas    # variant
```

The orchestrator reads `platforms/notion/.env` first, then falls back to the repo-root `.env`. Anything `export`ed in the shell wins over both. See the [parent README](../../README.md#where-env-is-loaded-from) for the full precedence rules. Tokens are not accepted on the command line.

`--platform notion` is required (`slack` is the orchestrator default). See the [parent README](../../README.md) for the full list of orchestrator flags (filtering, `--skip-setup`, `--dry-run`, Hintas labels).

## Prerequisites

- Two separate Notion **Plus** workspaces, each with identical members, pages, databases, rows, and shared/unshared boundaries, and exactly one of the two MCPs installed in each
- An internal-integration secret token (`secret_…` / `ntn_…`) from each workspace, scoped to the `Hintas Agent` integration

Workspace separation is mandatory — installing both MCPs into the same workspace mixes their per-page integration shares and contaminates the unshared-target tests.

| Workspace | MCP installed | Claude config dir | Token env var |
|---|---|---|---|
| Notion-side | Official Notion MCP | `~/.claude-notion` | `NOTION_TOKEN` |
| Hintas-side | Hintas Notion MCP | `~/.claude-notion-hintas` | `HINTAS_TOKEN` |

Both workspaces must have:

- The same timezone (`America/Los_Angeles`) and locale (`en-US`)
- The same 9 users with identical emails and display names:

| Logical ID | Email | Display Name | Role |
|---|---|---|---|
| U01MIRANDA | miranda@hintas.co | Miranda Okonkwo | Owner |
| U02JARED | jared@hintas.co | Jared Blackwood | Member |
| U03PINKMAN | pinkman@hintas.co | **Pinkman** *(display name, not "Saul")* | Member |
| U04LAGOON | lagoon@hintas.co | Lagoon Takahashi | Member |
| U05CLAUDE | claude@hintas.co | Claude Ellison | Member |
| U06DEVON | devon@hintas.co | Devon Park | Member |
| U07RHEA | rhea@hintas.co | Rhea Kapoor | Member |
| U08TOMAS | tomas@hintas.co | Tomás Vidal | Member |
| U09EMBER | ember@hintas.co | Ember Shah | Member, **then revoke** |

The agent itself is the `Hintas Agent` internal integration (a bot user `U10AGENT`), not a human member.

If you use different emails, copy `platforms/notion/scripts/users.json` → `users.local.json` and map the logical IDs to your actual emails. `users.local.json` is gitignored and takes priority over the committed sample.

- The same integration capabilities granted to both `Hintas Agent` installs. Core run capabilities:

```
read_content, update_content, insert_content,
read_user_info,
read_comments, insert_comments
```

Extension run adds: `read_user_with_email` (required for prompts that look up users by email or return `person.email` values). Each prompt's `required_scopes` field tells you exactly what it needs.

- The same shared/unshared boundaries — the `Hintas` page is shared (descendants inherit), and `🔒 Leads-only`, its child `Leads sync notes`, and the `Press Contacts` database are deliberately **not** shared. The seeder verifies these unshared targets return 404 before proceeding.

The full per-workspace setup walkthrough lives in [`prerequisites.md`](prerequisites.md).

## One-time setup

### 1. Claude config dirs for each MCP

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Create them once, then register the appropriate MCP server inside each:

```bash
mkdir -p ~/.claude-notion ~/.claude-notion-hintas

# Notion baseline
CLAUDE_CONFIG_DIR=~/.claude-notion claude mcp add ...

# Hintas variant
CLAUDE_CONFIG_DIR=~/.claude-notion-hintas claude mcp add ...
```

Complete the OAuth flow for each MCP once.

### 2. Install Python deps and tokens

```bash
uv sync

export NOTION_TOKEN=secret_<token-from-notion-side-internal-integration>
export HINTAS_TOKEN=secret_<token-from-hintas-side-internal-integration>
```

### 3. Manual setup that can't be scripted

Some state can't be reached from an integration token and must be done once in the Notion UI on **both** workspaces:

- Provision a fresh Notion **Plus** workspace named `Hintas` (timezone `America/Los_Angeles`, locale `en-US`)
- Invite the 9 users above; rename Saul Rivera's display name to `Pinkman`; revoke `ember@hintas.co` after capturing her `user_id`
- Create the top-level pages by hand (workspace-parented pages can't be created from an integration token):
  - `Hintas` — top-level page, icon 🎮 (the seeder populates the full hierarchy under this)
  - `🔒 Leads-only` — separate top-level page, with one child `Leads sync notes`
- Create the unshared `Press Contacts` database anywhere not visible to the integration (easiest: under `🔒 Leads-only`)
- Create the `Hintas Agent` internal integration with the capabilities listed above and copy its `secret_…` token
- Share `Hintas` to the integration via Connections; do **not** share `🔒 Leads-only`, `Leads sync notes`, or `Press Contacts`
- Record the resulting UUIDs in per-stack prereq files (gitignored):

```
platforms/notion/scripts/prerequisites_notion.local.json   ← Notion-side
platforms/notion/scripts/prerequisites_hintas.local.json   ← Hintas-side
```

Each file holds `P08_LEADS_ONLY`, `P11_LEADS_NOTES`, `DB_PRESS_CONTACTS`, and `U09EMBER`. The orchestrator picks the right one per stack automatically.

The full step-by-step walkthrough — including curl snippets for capturing Ember's UUID and dry-run sanity checks — is in [`prerequisites.md`](prerequisites.md).

## Filtering and variants

With `NOTION_TOKEN` and `HINTAS_TOKEN` already exported:

```bash
# Filter to specific prompts / difficulties / categories
uv run python benchmark.py --platform notion --prompt-ids 1 22 40

uv run python benchmark.py --platform notion --difficulty L1 L2 --category retrieval

# Core + Extension capabilities (~60 prompts)
uv run python benchmark.py --platform notion --feasibility core extension
```

## Adding a prompt

Append to `platforms/notion/prompts/benchmark_prompts.json`:

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

Difficulties are `L1`..`L5`. Categories: `retrieval`, `search`, `write`, `workflow`, `orchestration`, `edge_case`. `feasible_on_free_plan`: `core`, `extension`, or `infeasible`. `required_scopes` lists the integration capabilities the prompt needs (`read_content`, `update_content`, `insert_content`, `read_user_info`, `read_comments`, `insert_comments`, `read_user_with_email`).

## Notion folder layout

```
platforms/notion/
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

- **Seed fails on `No page titled 'Hintas' is shared to this integration`** — the integration was created but never connected to the `Hintas` page. Re-do the share step in the Notion UI (page `···` → Connections → add `Hintas Agent`).
- **Seed fails on `… IS visible to the integration — must be unshared`** — the integration was accidentally shared to `🔒 Leads-only`, `Leads sync notes`, or `Press Contacts`. Remove the connection from those pages/databases.
- **Seed fails on `prerequisites file is missing IDs for: …`** — the `prerequisites_<stack>.local.json` is missing one of `P08_LEADS_ONLY`, `P11_LEADS_NOTES`, `DB_PRESS_CONTACTS`, or `U09EMBER`. Capture the UUIDs from the Notion UI / `/users` endpoint and re-record them.
- **`U09EMBER … is still present in /users; expected revoked`** — Ember was invited but never removed. After capturing her `user_id`, remove her under Settings → Members.
- **`U03PINKMAN display name is …; expected 'Pinkman'`** — Saul Rivera's display name was not renamed. Rename to `Pinkman` in Members.
- **Reset fails** — check the corresponding `workspace_state_ids_<stack>.json` file exists in `platforms/notion/scripts/`. The seeder writes it during the first successful seed; the reset script auto-picks the right file based on the workspace the token authenticates against.
- **Two workspaces drift** — after several benchmark runs, the seeder should keep both workspaces aligned. If not, archive the seeded subtree under `Hintas` and re-run the seeder; the unshared targets and human-membership state are preserved.
- **OAuth refresh for Notion MCP** — if the Notion-MCP sessions all `401`, re-authenticate by running `claude` once with `CLAUDE_CONFIG_DIR=~/.claude-notion` and completing the browser flow.
