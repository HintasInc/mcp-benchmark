## Gmail-specific surface notes

### Reading the transcript

The two stacks expose Gmail's API surface differently — the same outcome may show up very differently in the `transcript`:

- **Gmail MCP** publishes one tool per Gmail API operation, prefixed `mcp__claude_ai_gmail__*`: `search_threads`, `get_thread`, `list_labels`, `create_label`, `update_label`, `delete_label`, `label_thread`, `unlabel_thread`, `list_drafts`, `create_draft`, etc. Each call appears as its own `tool_use` entry whose name matches the operation.

- **Hintas MCP** dispatches via three generic tools, prefixed `mcp__hintas-gmail__*`: `search_tools` (capability discovery), `tool_info` (schema lookup), and `call_tool_chain` (multi-step invocation). The downstream Gmail operations executed by `call_tool_chain` do **not** surface as separate `tool_use` blocks — they live inside the `arguments` payload of `call_tool_chain` and inside the `result_excerpt` of its tool_result. Read those payloads to see what Gmail operations Hintas actually invoked. A short `tools_invoked` list does not mean Hintas did less work; one `call_tool_chain` may run several Gmail operations internally.

### Gmail-specific grading rules

**Date anchor:** `benchmark_now = 2026-04-19T10:00:00-07:00` (America/Los_Angeles). Prompts 6, 16, 24, 26, 27, 30, 46, 49, 50 use relative dates ("today", "last 14 days", "newer_than:30d", date windows) anchored to this value. The runner currently does NOT inject `benchmark_now` into the agent's prompt, so the agent will resolve relative dates against the host wall-clock. If the agent's `q=` query (or its date arithmetic) uses a date that does not align with `2026-04-19`, the returned rows will not match the seeded target set — note this as a **date-resolution failure** in `reasoning` and grade as **FAIL** (not PARTIAL, not infrastructure error) when the divergence causes target threads to be missed or non-target threads to be touched. Do not accept "no results, so nothing to do" as a PASS when the seeded ground truth would have produced a non-empty target set under `benchmark_now`.

**Empty-result vacuous PASSes:** When the agent reports "no threads match / nothing to do / zero results", verify against the seeded workspace expectation before grading PASS. If the seed contains threads that should have matched the prompt's target criteria (under `benchmark_now` and the documented label/sender/state layout in `experiments/gmail/IMPLEMENTATION.md` §"Mailbox overview"), the empty result is a **search failure** — grade **FAIL**, not PASS. PASS for an empty result is reserved for prompts where the seed is genuinely empty for the queried slice (e.g. p27 bulk-archive promotions when no CATEGORY_PROMOTIONS threads are seeded).

**Infeasible prompts (53, 54, 55):** Operations not exposed by the Gmail API under a single-user OAuth token (reading another user's mailbox, provisioning a Gmail account, generating an S/MIME certificate). The agent is graded on **clean failure reporting**: PASS if the agent identifies the operation as infeasible and explains why without fabricating a successful outcome; FAIL if the agent claims success, calls unrelated mutations, or hallucinates state.

**Extension-scope prompts (34, 35, 36, 37, 38, 40, 41, 42, 50):** Require `gmail.settings.basic` / `gmail.settings.sharing` scopes. If the operator's token lacks these scopes, the call will return `403 Insufficient Permission` — mark **FAIL** under the env-rejection-as-FAIL rule and note the scope gap in `reasoning`. Do not penalise either stack against the other for a scope gap that affects both equally.

**Cross-server tool leakage:** The runner restricts the session to `mcp__<server>__*`, but if multiple MCP servers are registered in the stack's `CLAUDE_CONFIG_DIR`, the agent may invoke tools from other servers (e.g. Slack search) when the Gmail call should have been used. If the transcript shows the agent calling `mcp__claude_ai_Slack__*` or other non-Gmail tools to answer a Gmail prompt, grade **FAIL** — the Gmail capability under test was not exercised. Examples: p33 "Download an attachment" where the agent searched Slack instead of Gmail.

**Label admin operations (`update_label`, `delete_label`):** `update_label` and `delete_label` on user-defined labels require `gmail.modify`. A `403 The caller does not have permission` from these calls is a real capability gap on the operator's OAuth token — grade FAIL on the prompt and note the scope gap. Do not treat this as the agent's fault.

**System-label rejection prompts (45):** Renaming a system label (`INBOX`, `SENT`, `STARRED`, etc.) is rejected by Gmail with a 400. The agent is graded on identifying and surfacing the rejection cleanly. PASS if the agent reports "cannot rename system label" without attempting workaround mutations; FAIL if it tries to rename or fabricates success.

**Trash semantics (44):** Operations on trashed threads require the agent to search with `in:trash` (default `threads.list` excludes TRASH). If the agent searches with a subject literal or other query that does not include `in:trash`, it will not find the seeded trashed thread — grade FAIL with "missed trash inclusion" in `reasoning`.

**`users.getProfile` vs inferred-identity (1):** Prompt 1 ("Who am I?") requires the agent to source the mailbox owner's email and message/thread totals from `users.getProfile` (`emailAddress`, `messagesTotal`, `threadsTotal`). If the agent infers the email from message headers and counts threads manually from `search_threads` results instead, grade **PARTIAL** — the answer may be factually correct but the criteria require the canonical API call.
