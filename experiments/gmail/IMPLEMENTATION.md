# Gmail benchmark: implementation

Two parallel Gmail mailboxes, with one mirroring the other, allow A/B testing of the **Gmail MCP - Official** against the **Gmail MCP - Hintas** on identical state. Pick a stack with `--stack gmail` (baseline) or `--stack hintas` (variant); see the [parent README](../../README.md) and [root IMPLEMENTATION.md](../../IMPLEMENTATION.md) for orchestrator usage.

## Why two mailboxes

Gmail OAuth tokens are scoped to a single Google account, and pointing both MCPs at one mailbox lets each stack's writes (labels, filters, sent items, send-as aliases, vacation settings) leak into the other's reads. Each mailbox must end up in identical state (same threads, drafts, labels, filters, send-as aliases, and vacation/forwarding settings), or the comparison isn't fair.


| Mailbox     | MCP installed                          | Mailbox token env |
| ----------- | -------------------------------------- | ----------------- |
| Gmail-side  | Gmail MCP - Official                   | `GMAIL_TOKEN`     |
| Hintas-side | Gmail MCP - Hintas                     | `HINTAS_TOKEN`    |


Tokens go in `experiments/gmail/.env` (see `.env.example`). Use the **user OAuth refresh token** issued by each mailbox's own Google Cloud OAuth client — not a single token shared between them, and not a service-account or domain-wide-delegation credential (the benchmark deliberately exercises the single-user mailbox surface).

## Mailbox contract


| Field                  | Value                          |
| ---------------------- | ------------------------------ |
| Owner display name     | `{{NAME_U05CLAUDE}}`           |
| Owner email            | `{{EMAIL_U05CLAUDE}}`          |
| Timezone               | `America/Los_Angeles`          |
| Locale                 | `en-US`                        |
| Benchmark wall-clock   | `2026-04-19T10:00:00-07:00`    |


## Per-mailbox setup

> Repeat for both mailboxes. The mailbox is destructive: prompts read, label, archive, trash, untrash, delete, draft, send, reply, forward, create/delete filters, and toggle vacation/forwarding settings. Don't point at a real mailbox.

### 1. Provision (or repurpose) a Gmail account

Use a fresh consumer Gmail account, a Workspace user on a test domain you control, **or any existing Gmail account you're willing to wipe**. The mailbox gets reset to the seeded baseline before every prompt — pre-existing mail, labels, filters, drafts, send-as aliases, and signed-up forwarding addresses will be purged. Before the first seed, empty `Trash`, `Spam`, and `All Mail`, and delete any pre-existing user-defined labels / filters / send-as aliases / vacation responder / forwarding addresses so the seeded snapshot is the only state.

The other people referenced in the prompts (`{{NAME_U01MIRANDA}}`, `{{NAME_U02JARED}}`, …, `{{NAME_U09EMBER}}`) **do not need real Gmail accounts** — they only appear as `From` / `To` / `Cc` headers on seeded inbound messages and as destinations for sends the agent performs. The seeder reads their addresses from `users.json` (see step 4) and substitutes them into headers verbatim.

- **`{{NAME_U03PINKMAN}}` (legal name `Saul Rivera`)**: prompts refer to him by the first-name handle `pinkman`. He must be addressable as `pinkman` either via a contact entry (Contacts → New contact, first name `Pinkman`) or by appearing as the From-display-name on seeded inbound messages. Prompts that grade on resolving the `pinkman` handle break silently otherwise.
- **`{{NAME_U09EMBER}}`**: deactivated external sender. Her address appears on inbound messages in the archive but the seeder never sends to her, and no outbound prompts target her.

### 2. Create the Google Cloud OAuth client

Each mailbox needs its own OAuth 2.0 client (one for the `gmail` stack, one for the `hintas` stack) so refresh tokens don't cross-contaminate.

- Google Cloud Console → **APIs & Services → Library** → enable **Gmail API**.
- **APIs & Services → OAuth consent screen** → User type **External** → add `{{EMAIL_U05CLAUDE}}` as a test user (keeps the app in Testing mode so refresh tokens don't expire after 7 days for that account).
- **APIs & Services → Credentials → Create credentials → OAuth client ID** → application type **Desktop app**. Download the client JSON.

Required scopes for a core run (granted on the consent screen):

```
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.compose
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.labels
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.metadata
```

Extension run adds `gmail.settings.basic` (vacation responder, filters, send-as aliases, IMAP/POP) and `gmail.settings.sharing` (auto-forwarding). Each prompt's `required_scopes` field lists exactly what it needs.

Run the OAuth flow once against this client signed in as `{{EMAIL_U05CLAUDE}}`, accept the full scope set, and capture the **refresh token**. Put it in the env var matrix above.

### 3. Pre-create the verification-gated entities

A few mailbox entities require Google to send a confirmation email and the operator to click through manually. The seeder cannot complete these handshakes, so they have to be in place before seeding starts.

- **Forwarding address** (extension run only): Settings → Forwarding and POP/IMAP → **Add a forwarding address** → confirm via the link Google sends to the forwarding target. The seeder enables/disables auto-forwarding against this verified address but cannot create the verification record itself.
- **S/MIME signing certificate**: NOT a prerequisite. The benchmark intentionally probes the `[INFEASIBLE] Generate an S/MIME certificate` path; leave S/MIME unconfigured so the agent's failure-reporting behavior can be graded.

### 4. Record the cast and per-mailbox pre-seed IDs

Two files, mirroring the slack/notion layout:

- **`experiments/gmail/scripts/users.json`** (committed) — the canonical cast with placeholder `@hintas.co` addresses. The `benchmark-author: true` flag is on `U05CLAUDE` because the Gmail agent acts as the mailbox owner, not as Miranda.
- **`experiments/gmail/scripts/users.local.json`** (gitignored, overrides `users.json`) — your real addresses. Copy `users.json` to `users.local.json` and replace each `email` field; the seeder reads the override automatically when present. This is where the per-mailbox `U05CLAUDE.email` (the actual `{{EMAIL_U05CLAUDE}}` Gmail address) goes. For the other 8 users, sub-addressing (`yourname+jared@gmail.com`) is fine since they're header-only.

Per-stack mailbox-resolved IDs (the agent's `users.getProfile` `emailAddress` and `historyId`, plus the resolved verification status of any forwarding address) are written to `experiments/gmail/scripts/prerequisites_<stack>.local.json` by the seeder on first run — you don't fill this one in by hand. The orchestrator picks the right one automatically based on the stack name.

Prompts reference users via `{{ID_*}}`, `{{EMAIL_*}}`, and `{{NAME_*}}` placeholders; the seeder substitutes them into seeded message headers, draft bodies, and grading expectations from the merged `users.json` + `users.local.json` view.

## Local machine setup

The benchmark routes each session through a separate Claude config dir to keep the two MCPs isolated. Run `claude` once with each `CLAUDE_CONFIG_DIR` specified in `gmail.toml` to complete the OAuth flow. MCP authentication must be completed manually before starting the benchmark.

## Sanity-check and seed

```bash
# Dry-run; auths, calls users.getProfile, and stops with a "would create" plan.
uv run python experiments/gmail/scripts/seed_workspace.py --verify
```

Drop `--verify` to seed for real. The seeder keys its state file by the mailbox's `emailAddress` so the two mailboxes don't clobber each other. The orchestrator (`uv run benchmark run`) handles seed/reset/verify automatically per stack, so these direct invocations are only for sanity-checking and recovery.

## Mailbox overview

The seeder builds out the `{{EMAIL_U05CLAUDE}}` mailbox with the entities a prompt suite needs to exercise read, write, search, and capability-coverage paths.

- **Threads and messages**: seeded inbound threads across senders (Miranda, Jared, Pinkman/Saul, Lagoon, Devon, Rhea, Tomas, Ember), one bug thread (`TH_BUG247` — subject contains `BUG-247`), a newsletter thread (`TH_OKR_DIGEST`), and assorted mixed-attachment / starred / unread states. `internalDate` is set relative to `benchmark_now = 2026-04-19T10:00:00-07:00`.
- **Labels**: user-defined labels `Hintas`, `Hintas/Triage`, `Hintas/Follow-up`, `Receipts`, `Press`, `Ops/Bugs` (nesting expressed via `/`). System labels (`INBOX`, `SENT`, `DRAFT`, `TRASH`, `SPAM`, `STARRED`, `IMPORTANT`, `UNREAD`, `CATEGORY_*`) are baseline-Gmail and not seeded.
- **Drafts**: a small set of seeded drafts (e.g., `DRAFT_OOO_REPLY`, `DRAFT_BUG_UPDATE`) authored by the agent.
- **Filters**: `FILTER_RECEIPTS` (auto-labels `receipts@…` senders) and `FILTER_PRESS` (auto-labels press contacts). Other filters are absent so the create-filter prompts can be graded against a known baseline.
- **Send-as aliases**: primary `{{EMAIL_U05CLAUDE}}` only. No S/MIME entries.
- **Vacation responder**: disabled at baseline; the `set vacation responder` prompts toggle it on.
- **Capability boundaries**: prompts deliberately probe operations that aren't exposed by the Gmail API on a single-user token (admin operations, S/MIME generation, reading other mailboxes). The agent is graded on clean failure reporting, not on completing them.

Under single-token Scenario A, every seeded SENT message, draft, label, filter, and send-as alias is authored by `{{EMAIL_U05CLAUDE}}` (the agent) under `userId='me'`. Inbound messages carry the listed external/internal senders in their `From` headers via `messages.import` (or equivalent), even though no real Gmail account on the other side delivered them.

The full ground truth (thread IDs, message IDs, label IDs, filter IDs, draft IDs, send-as alias addresses) lives in `experiments/gmail/scripts/workspace_state_ids_<stack>.json` (auto-emitted by the seeder). The seed/reset/verify scripts own that contract, so operators don't need to track it by hand.

## Reset

Most prompts are destructive, so the mailbox is reset before every prompt run. The orchestrator handles this automatically; for direct invocations use `experiments/gmail/scripts/reset_workspace.py`, which loads `workspace_state_ids_<stack>.json` written by the seeder.
