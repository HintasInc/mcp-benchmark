# Notion Benchmark — Prerequisites

Manual setup that must be completed **before** running `platforms/notion/scripts/seed_workspace.py`. The seeder will fail (or produce a partially-correct workspace) if any of these steps are skipped.

The Notion benchmark mirrors the Slack benchmark's two-workspace design: one workspace per MCP under test. **Repeat steps 1–5 in each of the two workspaces.** Steps 6–8 are done once on your local machine.

| Workspace | MCP wired in | Token env var |
|---|---|---|
| Notion-side | Official Notion MCP | `NOTION_TOKEN` |
| Hintas-side | Hintas Notion MCP | `HINTAS_TOKEN` |

Both must end up in identical state — same users, same pages, same databases, same rows, same archived content, same shared/unshared boundaries — otherwise the A/B comparison isn't fair.

---

## Per-workspace setup (do this twice)

### 1. Provision a fresh Notion Plus workspace

- Sign up at [notion.so](https://notion.so) for a brand-new workspace.
- Plan: **Plus** (required for unlimited file uploads, page-history past 7 days, and per-page integration share controls).
- Workspace name: `Hintas`.
- Do **not** point this at a real workspace — prompts create, archive, restore, rename, mutate, and comment on pages, databases, and blocks.
- Settings → Settings & Members → Settings:
  - Timezone: `America/Los_Angeles`
  - Locale: `en-US`

### 2. Invite the 9 users

Settings → Members → Invite. Use exactly these emails, or override them by copying `platforms/notion/scripts/users.json` → `platforms/notion/scripts/users.local.json` (gitignored) and editing the values to your real emails.

| Logical ID | Email | Display name | Workspace role |
|---|---|---|---|
| `U01MIRANDA` | `miranda@hintas.co` | Miranda Okonkwo | Owner |
| `U02JARED` | `jared@hintas.co` | Jared Blackwood | Member |
| `U03PINKMAN` | `pinkman@hintas.co` | **Pinkman** (display name, not "Saul") | Member |
| `U04LAGOON` | `lagoon@hintas.co` | Lagoon Takahashi | Member |
| `U05CLAUDE` | `claude@hintas.co` | Claude Ellison | Member |
| `U06DEVON` | `devon@hintas.co` | Devon Park | Member |
| `U07RHEA` | `rhea@hintas.co` | Rhea Kapoor | Member |
| `U08TOMAS` | `tomas@hintas.co` | Tomás Vidal | Member |
| `U09EMBER` | `ember@hintas.co` | Ember Shah | Member, **then revoke** |

After inviting `U09EMBER`, remove their workspace access (Settings → Members → row menu → Remove). The benchmark explicitly tests that `U09EMBER` is absent from `listUsers` but still resolvable via `retrieveUser` — that pattern only appears for revoked (not deleted) users.

### 3. Create the top-level pages manually

Internal integrations can't create pages with `parent.workspace = true`, so create these by hand from the sidebar:

- **`Hintas`** — top-level page, icon 🎮. The seeder will populate this with the full hierarchy.
- **`🔒 Leads-only`** — separate top-level page (sibling, not under `Hintas`).
  - Add one child page inside it titled **`Leads sync notes`**.

Copy each page's UUID (from its URL or the share-link panel) — you'll record them in step 6.

### 3b. Create `Press Contacts` database manually

Notion doesn't expose a "remove this integration's access" endpoint, so we can't have the seeder create a database and then unshare it. Instead, create an empty database that's never shared to the integration:

- Anywhere not visible to `Hintas Agent` works — easiest is to make it a child of `🔒 Leads-only` (which is already unshared).
- Name it **`Press Contacts`**. Schema and rows are not graded — the benchmark only tests that the integration can't see it.
- Copy the database UUID — you'll record it in step 6.

### 4. Create the internal integration

This is what `NOTION_TOKEN` / `HINTAS_TOKEN` actually points to. **Do not** try to use the token from a public OAuth integration — public integrations don't expose a static `secret_…` token.

Settings → Integrations → **Develop your own integrations** → **New integration**:

- Name: `Hintas Agent`
- Associated workspace: this workspace
- Type: **Internal**
- Capabilities — check all of:
  - Read content
  - Update content
  - Insert content
  - **Read user information including email addresses**
  - Read comments
  - Insert comments
- Save, then copy the secret token (starts with `secret_` or `ntn_`).

This is the value you'll export as `NOTION_TOKEN` (in the Notion-side workspace) or `HINTAS_TOKEN` (in the Hintas-side workspace).

### 5. Share the right pages to the integration

On each page in the sidebar, click `···` → **Connections** → Add `Hintas Agent`:

- ✅ Share `Hintas` (descendants inherit the connection automatically).
- ❌ Do **NOT** share `🔒 Leads-only`, its child `Leads sync notes`, or the `Press Contacts` database.

The seeder verifies it can find a `Hintas` page shared to the integration, and it verifies that the three unshared targets actually return 404 — it will abort with a clear error if either side is wrong.

### 6. Capture Ember's user id (before revoking)

Step 2 instructed you to invite Ember and then revoke access. The benchmark needs her `user_id` to remain resolvable via `retrieveUser` after revocation, so capture it **before** removing her:

```bash
curl https://api.notion.com/v1/users \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" | jq '.results[] | select(.person.email=="ember@hintas.co") | .id'
```

Record the UUID, then go back to **Settings → Members → remove `ember@hintas.co`**.

### 7. Record the pre-seed IDs (per workspace)

Each workspace has its own UUIDs for the entities created in steps 3, 3b, and 6. Use one prerequisites file per workspace; the orchestrator picks the right one automatically based on the stack name (`notion` or `hintas`):

```
platforms/notion/scripts/prerequisites_notion.local.json   ← Notion-side workspace
platforms/notion/scripts/prerequisites_hintas.local.json   ← Hintas-side workspace
```

Both files are gitignored (`*.local.json`). Each one looks like this:

```json
{
  "P08_LEADS_ONLY":     "<UUID of the 🔒 Leads-only page>",
  "P11_LEADS_NOTES":    "<UUID of the Leads sync notes page>",
  "DB_PRESS_CONTACTS":  "<UUID of the Press Contacts database>",
  "U09EMBER":           "<UUID of Ember Shah, captured before revoke>"
}
```

`benchmark.py` passes `--prereq-file platforms/notion/scripts/prerequisites_<stack>.local.json` to the seeder for each stack. If you run the seeder by hand against a single workspace, pass the flag explicitly:

```bash
NOTION_TOKEN=$NOTION_TOKEN uv run python platforms/notion/scripts/seed_workspace.py \
  --prereq-file platforms/notion/scripts/prerequisites_notion.local.json
```

`--prereq-file` is required when running the seeder by hand; the orchestrator (`benchmark.py`) supplies it automatically per stack.

### 8. Wire each MCP into its workspace

The MCP that the agent uses at benchmark time is separate from the internal integration above. Both can coexist.

- Notion-side workspace → install the official Notion MCP via its OAuth flow.
- Hintas-side workspace → install the Hintas Notion MCP via its OAuth flow.

---

## Local machine setup (do this once)

### 9. Claude config dirs

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Create them once, then register each MCP server inside its config dir using `claude mcp add` (or by editing `config.json` directly):

```bash
mkdir -p ~/.claude-notion ~/.claude-notion-hintas

# Notion baseline → register the official Notion MCP server here
CLAUDE_CONFIG_DIR=~/.claude-notion claude mcp add ...

# Hintas variant → register the Hintas Notion MCP server here
CLAUDE_CONFIG_DIR=~/.claude-notion-hintas claude mcp add ...
```

Then run `claude` once with each `CLAUDE_CONFIG_DIR` to complete the OAuth flow.

### 10. Export both tokens

```bash
export NOTION_TOKEN=secret_<token-from-notion-side-internal-integration>
export HINTAS_TOKEN=secret_<token-from-hintas-side-internal-integration>
```

The orchestrator (`benchmark.py`) reads both, then invokes each script twice — once per workspace, swapping the token into the `NOTION_TOKEN` slot. The seed/reset/verify scripts themselves only read `NOTION_TOKEN`; that's intentional.

---

## Sanity-check before seeding

From the repo root, with both tokens exported:

```bash
# Dry-run against each workspace; each should auth, list users, and stop with a
# "would create" plan if the workspace is empty.
NOTION_TOKEN=$NOTION_TOKEN uv run python platforms/notion/scripts/seed_workspace.py --verify \
  --state-file platforms/notion/scripts/workspace_state_ids_notion.json \
  --prereq-file platforms/notion/scripts/prerequisites_notion.local.json
NOTION_TOKEN=$HINTAS_TOKEN uv run python platforms/notion/scripts/seed_workspace.py --verify \
  --state-file platforms/notion/scripts/workspace_state_ids_hintas.json \
  --prereq-file platforms/notion/scripts/prerequisites_hintas.local.json
```

Common dry-run errors and what to fix:

- `No page titled 'Hintas' is shared to this integration` → revisit step 5.
- `These active users are missing from /users` → revisit step 2.
- `U03PINKMAN display name is …; expected 'Pinkman'` → revisit step 2 (rename Saul Rivera → Pinkman in Members).
- `U09EMBER … is still present in /users; expected revoked` → finish step 2 (remove ember@hintas.co).
- `prerequisites file is missing IDs for: …` → revisit step 7.
- `… IS visible to the integration — must be unshared` → revisit step 5 (remove integration access for that page/database).

---

## Live seed

```bash
NOTION_TOKEN=$NOTION_TOKEN uv run python platforms/notion/scripts/seed_workspace.py \
  --state-file platforms/notion/scripts/workspace_state_ids_notion.json \
  --prereq-file platforms/notion/scripts/prerequisites_notion.local.json
NOTION_TOKEN=$HINTAS_TOKEN uv run python platforms/notion/scripts/seed_workspace.py \
  --state-file platforms/notion/scripts/workspace_state_ids_hintas.json \
  --prereq-file platforms/notion/scripts/prerequisites_hintas.local.json
```

Each run writes the per-stack `workspace_state_ids_<stack>.json`. The orchestrator picks the right one automatically based on the stack name.

After seeding, run the verifier:

```bash
NOTION_TOKEN=$NOTION_TOKEN uv run python platforms/notion/scripts/verify_workspace.py \
  --state-file platforms/notion/scripts/workspace_state_ids_notion.json --report drift_notion.json
NOTION_TOKEN=$HINTAS_TOKEN uv run python platforms/notion/scripts/verify_workspace.py \
  --state-file platforms/notion/scripts/workspace_state_ids_hintas.json --report drift_hintas.json
```

Hard drift count should be 0 in both. `P08_LEADS_ONLY`, `P11_LEADS_NOTES`, and `DB_PRESS_CONTACTS` returning 404 are **expected** and reported as info, not drift.

---

## Then run the benchmark

With both tokens loaded into `platforms/notion/.env` and both workspaces verified clean:

```bash
uv run python benchmark.py --platform notion --stack notion    # baseline
uv run python benchmark.py --platform notion --stack hintas    # variant
```

See the parent [`README.md`](../../README.md) for filtering flags (`--prompt-ids`, `--difficulty`, `--category`, `--feasibility`, `--skip-setup`, `--dry-run`).

---

## Known limits of single-token Scenario A

Same constraint as the Slack benchmark: every seeded row, block, and comment is `created_by` the integration bot, not by the human users (`U01MIRANDA`, `U02JARED`, …). The benchmark accepts this — `workspace_state.md` §8 documents that all seeded comments are bot-authored, and no prompt grades `created_by` against a human user.
