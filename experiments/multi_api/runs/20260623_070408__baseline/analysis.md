# Multi_api MCP - Multi-API MCP - Baseline (Official) benchmark analysis

**Scope:** 23 prompts.

## Verdict legend

- `✓ PASS` — **every** task on **every** surface completed and the cross-API handoff held; usable, grounded answer.
- `✗ FAIL` — core task not accomplished. **Includes environmental rejections** ("user doesn't exist", "page not shared", "integration lacks access", server refused). On this platform, **any** failed/skipped/blocked/fabricated task fails the prompt.
- `⚠ ERROR` — infrastructure failure (no result, orchestrator error, or `result_subtype: error` with no usable output).

## Aggregates

| Metric | Value |
|:-------|------:|
| Prompts run | 23 |
| Success rate | 70% |
| Passes | 16 |
| Fails | 5 |
| Errors | 2 |
| Avg initial context | 3 |
| Avg peak context | 642 |
| Avg wall-clock | 139.0s |
| Total tokens | 123,660 |
| Avg tokens/prompt | 5,377 |
| Avg tool calls | 20.22 |
| Total tool failures | 23 |

> **Tool-call metrics are stack-internal, not head-to-head.** Each row counts one MCP call per `tool_use`. The baseline surfaces every API method as its own call, while the Hintas unified server runs several methods inside one `execute_tools` dispatch — so a single dispatch may hide multiple surface methods (and an internal surface failure where the wrapper returns success does not register as a failed call). Compare verdicts and tokens across stacks; treat tool-call counts as per-stack.

## Breakdown by difficulty

| Difficulty | n | Success rate | P/F/E |
|:-----------|--:|-------------:|:-----:|
| L2 | 2 | 100% | 0/0/0 |
| L3 | 7 | 86% | 0/0/1 |
| L4 | 9 | 44% | 0/4/1 |
| L5 | 5 | 80% | 0/1/0 |

## Breakdown by category

| Category | n | Success rate | P/F/E |
|:---------|--:|-------------:|:-----:|
| workflow | 3 | 67% | 0/0/1 |
| edge_case | 1 | 0% | 0/0/1 |
| reconciliation | 5 | 100% | 0/0/0 |
| support | 3 | 67% | 0/1/0 |
| announcement | 2 | 100% | 0/0/0 |
| onboarding | 3 | 0% | 0/3/0 |
| project_kickoff | 1 | 0% | 0/1/0 |
| incident | 1 | 100% | 0/0/0 |
| reporting | 4 | 100% | 0/0/0 |

<details>
<summary><h2 style="display:inline">Per-prompt results</h2></summary>

| ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails |
|---:|:------|:----:|:-------:|-----:|-------:|-----------:|-----------:|
| 1 | Reconcile leads across Slack and Notion | L2 | ✓ PASS | 63.3s | 2,625 | 14 | 2 |
| 2 | Mailbox owner vs Slack identity check | L2 | ✓ PASS | 33.7s | 1,198 | 7 | 0 |
| 3 | Find an open Notion task's Slack thread | L3 | ✓ PASS | 104.5s | 4,332 | 25 | 3 |
| 4 | Escalate a customer email into Slack | L3 | ✓ PASS | 28.6s | 1,217 | 8 | 0 |
| 5 | Cross-post a launch announcement | L4 | ✓ PASS | 192.9s | 8,690 | 33 | 1 |
| 6 | Onboard a new hire across all surfaces | L5 | ✗ FAIL | 104.0s | 5,518 | 14 | 1 |
| 7 | Spin up a project: Notion page → Slack channel → kickoff email | L4 | ✗ FAIL | 298.6s | 15,021 | 41 | 1 |
| 8 | Incident report from Slack thread to Notion and email | L5 | ✓ PASS | 220.1s | 10,032 | 36 | 3 |
| 9 | Weekly digest: Slack activity → Notion → team email | L4 | ✓ PASS | 209.2s | 10,104 | 23 | 0 |
| 10 | DM individuals their open Notion tasks | L5 | ✓ PASS | 200.7s | 10,282 | 45 | 6 |
| 11 | Turn an email request into a Notion task and Slack ping | L4 | ✗ FAIL | 121.7s | 4,235 | 23 | 0 |
| 12 | Announce a meeting and log attendees | L3 | ✓ PASS | 50.3s | 2,393 | 10 | 0 |
| 13 | Email a Notion page export to a stakeholder | L3 | ✓ PASS | 37.2s | 1,800 | 6 | 0 |
| 14 | Provision a private leads channel and notify by email | L4 | ✗ FAIL | 223.9s | 10,723 | 36 | 2 |
| 15 | Label and triage inbound, summarize to Slack | L4 | ✓ PASS | 81.9s | 3,765 | 17 | 0 |
| 16 | Confirm a Notion assignee is reachable before assigning | L3 | ✓ PASS | 90.5s | 3,749 | 19 | 0 |
| 17 | React in Slack and mirror status in Notion | L3 | ✓ PASS | 31.7s | 1,386 | 9 | 0 |
| 19 | Digest a channel and file it under each lead in Notion | L5 | ✓ PASS | 288.0s | 16,096 | 41 | 2 |
| 20 | Create Notion meeting notes from an email thread | L4 | ✓ PASS | 68.1s | 2,716 | 11 | 0 |
| 21 | Welcome email gated on Slack join confirmation | L4 | ✗ FAIL | 43.3s | 1,471 | 7 | 0 |
| 22 | Reconcile People DB against live Slack and Gmail | L5 | ✓ PASS | 105.5s | 6,307 | 40 | 2 |
| 23 | Schedule reminder workflow across Slack and Notion | L3 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |
| 24 | Idempotent re-run of project kickoff | L4 | ⚠ ERROR | 300.0s | 0 | 0 | 0 |

</details>

<details>
<summary><h2 style="display:inline">Initial vs peak context</h2></summary>

| ID | Title | Initial | Peak |
|---:|:------|--------:|-----:|
| 1 | Reconcile leads across Slack and Notion | 3 | 61 |
| 2 | Mailbox owner vs Slack identity check | 3 | 45 |
| 3 | Find an open Notion task's Slack thread | 3 | 79 |
| 4 | Escalate a customer email into Slack | 3 | 49 |
| 5 | Cross-post a launch announcement | 3 | 148 |
| 6 | Onboard a new hire across all surfaces | 3 | 61 |
| 7 | Spin up a project: Notion page → Slack channel → kickoff email | 3 | 2,039 |
| 8 | Incident report from Slack thread to Notion and email | 3 | 183 |
| 9 | Weekly digest: Slack activity → Notion → team email | 3 | 145 |
| 10 | DM individuals their open Notion tasks | 3 | 124 |
| 11 | Turn an email request into a Notion task and Slack ping | 3 | 118 |
| 12 | Announce a meeting and log attendees | 3 | 49 |
| 13 | Email a Notion page export to a stakeholder | 3 | 40 |
| 14 | Provision a private leads channel and notify by email | 3 | 154 |
| 15 | Label and triage inbound, summarize to Slack | 3 | 86 |
| 16 | Confirm a Notion assignee is reachable before assigning | 3 | 85 |
| 17 | React in Slack and mirror status in Notion | 3 | 52 |
| 19 | Digest a channel and file it under each lead in Notion | 3 | 10,448 |
| 20 | Create Notion meeting notes from an email thread | 3 | 679 |
| 21 | Welcome email gated on Slack join confirmation | 3 | 41 |
| 22 | Reconcile People DB against live Slack and Gmail | 3 | 84 |
| 23 | Schedule reminder workflow across Slack and Notion | 0 | 0 |
| 24 | Idempotent re-run of project kickoff | 0 | 0 |

</details>

## Notable failures

- **#6 Onboard a new hire across all surfaces** (L5, onboarding) — `FAIL`: Slack tasks failed: `slack_search_users` returned no results for Priya's email and no `slack_invite_user` or equivalent tool exists in the Slack MCP, so neither the channel invite nor the Slack DM could be executed (capability gap on Slack surface). Notion and Gmail tasks did complete (existing Priya Nakamura page updated to 'In progress', welcome email draft created linking the Notion page), but with Slack entirely blocked the prompt is FAIL.
- **#7 Spin up a project: Notion page → Slack channel → kickoff email** (L4, project_kickoff) — `FAIL`: The Slack 'set channel topic' task failed due to a capability gap: no `set_topic` or equivalent tool is available in the Slack MCP, so the Notion page URL was posted as a channel message rather than set as the formal topic. The prompt explicitly requires 'set its topic to the Notion page URL'. Notion page creation and Gmail draft both succeeded with real data and the cross-surface handoff (Notion URL in message/email) held.
- **#11 Turn an email request into a Notion task and Slack ping** (L4, support) — `FAIL`: The Notion surface failed entirely: the Notion MCP server never connected during the session (repeated ToolSearch attempts returned 'No matching deferred tools found' for Notion), so the 'Add SSO docs' task could not be created. With no Notion task URL, the Slack DM to Lagoon and the Gmail reply to Rhea were also not sent. The agent correctly diagnosed the blocker and halted rather than fabricating results.
- **#14 Provision a private leads channel and notify by email** (L4, onboarding) — `FAIL`: The Slack 'set channel topic to Leads-only planning' task failed due to a capability gap: no set_topic tool exists in the Slack MCP, so the agent posted 'Channel topic: Leads-only planning' as a message rather than setting the formal channel topic. The prompt explicitly requires 'set the topic to Leads-only planning'. Channel creation and lead invites succeeded (`slack_create_conversation` returned channel ID `C0BCJ8DNSUA`), and the Gmail draft was created, but the topic task is a required-output gap on the Slack surface.
- **#23 Schedule reminder workflow across Slack and Notion** (L3, workflow) — `ERROR`: Session timed out after 300 seconds with `has_result=false` and `orchestrator_error='timed out after 300s'` — no output was produced. Infrastructure failure; no agent behaviour to assess.
- **#24 Idempotent re-run of project kickoff** (L4, edge_case) — `ERROR`: Session timed out after 300 seconds with `has_result=false` and `orchestrator_error='timed out after 300s'` — no output was produced. Infrastructure failure; no agent behaviour to assess.
- **#21 Welcome email gated on Slack join confirmation** (L4, onboarding) — `FAIL`: The Slack invite task failed: Ember (`prtmasapkota+ember@gmail.com`) is not a workspace member (`slack_search_users` returned no match), and no tool exists to provision or invite a new user to the workspace, so she cannot be added to `#general`. With the gate condition unmet (channel membership not confirmed), the welcome email was correctly not sent. The required Slack invite task is a capability gap blocking the entire prompt.
