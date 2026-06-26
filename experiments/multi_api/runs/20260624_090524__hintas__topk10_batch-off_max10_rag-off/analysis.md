# Multi_api MCP - Multi-API MCP - Hintas benchmark analysis

**Scope:** 23 prompts.

## Verdict legend

- `✓ PASS` — **every** task on **every** surface completed and the cross-API handoff held; usable, grounded answer.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused). On this platform, **any** failed/skipped/blocked/fabricated task fails the prompt.
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 23 |
| Success rate | 87% |
| Passes | 20 |
| Fails | 3 |
| Errors | 0 |
| Avg initial context | 3 |
| Avg peak context | 502 |
| Avg wall-clock | 141.2s |
| Total tokens | 166,821 |
| Avg tokens/prompt | 7,253 |
| Avg tool calls | 14.22 |
| Total tool failures | 33 |

> **Tool-call metrics are stack-internal, not head-to-head.** Each row counts one MCP call per `tool_use`. The baseline surfaces every API method as its own call, while the Hintas unified server runs several methods inside one `execute_tools` dispatch — so a single dispatch may hide multiple surface methods (and an internal surface failure where the wrapper returns success does not register as a failed call). Compare verdicts and tokens across stacks; treat tool-call counts as per-stack.

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L2 | 2 | 100% | 0/0/0 |
| L3 | 7 | 100% | 0/0/0 |
| L4 | 9 | 78% | 0/2/0 |
| L5 | 5 | 80% | 0/1/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| workflow | 3 | 100% | 0/0/0 |
| edge_case | 1 | 0% | 0/1/0 |
| reconciliation | 5 | 100% | 0/0/0 |
| support | 3 | 100% | 0/0/0 |
| announcement | 2 | 100% | 0/0/0 |
| onboarding | 3 | 33% | 0/2/0 |
| project_kickoff | 1 | 100% | 0/0/0 |
| incident | 1 | 100% | 0/0/0 |
| reporting | 4 | 100% | 0/0/0 |

<details>
<summary><h2 style="display:inline">Per-prompt results</h2></summary>

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | Reconcile leads across Slack and Notion | L2 | ✓ PASS | 64.8s | 3,654 | 6 | 0 |
| 2 | Mailbox owner vs Slack identity check | L2 | ✓ PASS | 74.0s | 529 | 3 | 0 |
| 3 | Find an open Notion task's Slack thread | L3 | ✓ PASS | 172.6s | 8,966 | 18 | 1 |
| 4 | Escalate a customer email into Slack | L3 | ✓ PASS | 38.7s | 1,759 | 6 | 0 |
| 5 | Cross-post a launch announcement | L4 | ✓ PASS | 165.0s | 8,703 | 19 | 2 |
| 6 | Onboard a new hire across all surfaces | L5 | ✗ FAIL | 142.5s | 8,505 | 12 | 0 |
| 7 | Spin up a project: Notion page → Slack channel → kickoff email | L4 | ✓ PASS | 219.8s | 11,919 | 22 | 2 |
| 8 | Incident report from Slack thread to Notion and email | L5 | ✓ PASS | 181.9s | 9,683 | 17 | 1 |
| 9 | Weekly digest: Slack activity → Notion → team email | L4 | ✓ PASS | 212.5s | 12,583 | 13 | 0 |
| 10 | DM individuals their open Notion tasks | L5 | ✓ PASS | 134.2s | 6,592 | 17 | 0 |
| 11 | Turn an email request into a Notion task and Slack ping | L4 | ✓ PASS | 167.7s | 7,856 | 28 | 4 |
| 12 | Announce a meeting and log attendees | L3 | ✓ PASS | 131.8s | 6,743 | 13 | 2 |
| 13 | Email a Notion page export to a stakeholder | L3 | ✓ PASS | 74.0s | 6,949 | 14 | 4 |
| 14 | Provision a private leads channel and notify by email | L4 | ✓ PASS | 111.1s | 5,512 | 18 | 2 |
| 15 | Label and triage inbound, summarize to Slack | L4 | ✓ PASS | 54.4s | 2,835 | 6 | 0 |
| 16 | Confirm a Notion assignee is reachable before assigning | L3 | ✓ PASS | 166.5s | 7,634 | 17 | 1 |
| 17 | React in Slack and mirror status in Notion | L3 | ✓ PASS | 250.5s | 12,194 | 20 | 9 |
| 19 | Digest a channel and file it under each lead in Notion | L5 | ✓ PASS | 278.2s | 14,136 | 23 | 0 |
| 20 | Create Notion meeting notes from an email thread | L4 | ✓ PASS | 148.8s | 7,455 | 14 | 0 |
| 21 | Welcome email gated on Slack join confirmation | L4 | ✗ FAIL | 87.0s | 4,505 | 8 | 2 |
| 22 | Reconcile People DB against live Slack and Gmail | L5 | ✓ PASS | 105.6s | 4,069 | 10 | 1 |
| 23 | Schedule reminder workflow across Slack and Notion | L3 | ✓ PASS | 111.9s | 5,891 | 8 | 0 |
| 24 | Idempotent re-run of project kickoff | L4 | ✗ FAIL | 155.0s | 8,149 | 15 | 2 |

</details>

<details>
<summary><h2 style="display:inline">Initial vs peak context</h2></summary>

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | Reconcile leads across Slack and Notion | 3 | 38 |
| 2 | Mailbox owner vs Slack identity check | 3 | 24 |
| 3 | Find an open Notion task's Slack thread | 3 | 71 |
| 4 | Escalate a customer email into Slack | 3 | 37 |
| 5 | Cross-post a launch announcement | 3 | 93 |
| 6 | Onboard a new hire across all surfaces | 3 | 51 |
| 7 | Spin up a project: Notion page → Slack channel → kickoff email | 3 | 88 |
| 8 | Incident report from Slack thread to Notion and email | 3 | 72 |
| 9 | Weekly digest: Slack activity → Notion → team email | 3 | 53 |
| 10 | DM individuals their open Notion tasks | 3 | 75 |
| 11 | Turn an email request into a Notion task and Slack ping | 3 | 90 |
| 12 | Announce a meeting and log attendees | 3 | 56 |
| 13 | Email a Notion page export to a stakeholder | 3 | 10,157 |
| 14 | Provision a private leads channel and notify by email | 3 | 83 |
| 15 | Label and triage inbound, summarize to Slack | 3 | 38 |
| 16 | Confirm a Notion assignee is reachable before assigning | 3 | 74 |
| 17 | React in Slack and mirror status in Notion | 3 | 69 |
| 19 | Digest a channel and file it under each lead in Notion | 3 | 103 |
| 20 | Create Notion meeting notes from an email thread | 3 | 58 |
| 21 | Welcome email gated on Slack join confirmation | 3 | 44 |
| 22 | Reconcile People DB against live Slack and Gmail | 3 | 53 |
| 23 | Schedule reminder workflow across Slack and Notion | 3 | 44 |
| 24 | Idempotent re-run of project kickoff | 3 | 72 |

</details>

## Notable failures

- **#6 Onboard a new hire across all surfaces** (L5, onboarding) — `FAIL`: The required Slack DM welcome was not sent: the tool result returned priya_slack_id=null and steps_completed listed 'slack_dm_skipped_pending_account' — Priya has no active Slack account so the DM was explicitly skipped; the Notion page and welcome email completed, but the Slack DM task on the Slack surface failed.
- **#21 Welcome email gated on Slack join confirmation** (L4, onboarding) — `FAIL`: The required Slack invite failed on the Slack surface: users_lookupByEmail returned users_not_found (Ember not in workspace) and admin_users_invite failed with missing_scope: admin.users:write; because the gate condition (confirmed Slack membership) was never met, the welcome email was correctly not sent — but the core Slack task could not be completed due to the capability gap.
- **#24 Idempotent re-run of project kickoff** (L4, edge_case) — `FAIL`: The agent violated the no-duplicates constraint: notion.queryDatabase found the existing 'Atlas Migration' page (3854da5e-14d2-8165-ad53-cc0c5dcc5405, created 2026-06-20) but still created a new page (3894da5e-14d2-8151-b38d-dce29c1e2486); additionally, the kickoff email was created as a DRAFT (labelIds=[DRAFT]) rather than sent, so the leads do not have the email in their inboxes.
