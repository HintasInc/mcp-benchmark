## Notion-specific surface notes

### Reading the transcript

The two stacks expose Notion's API surface differently — the same outcome may show up very differently in the `transcript`:

- **Hintas MCP** calls Notion's OpenAPI endpoints directly. Its tools are named after Notion API operations: `listUsers`, `retrieveUser`, `retrieveBotUser`, `search`, `retrieveDatabase`, `queryDatabase`, `retrievePage`, `retrievePageProperty`, `retrieveBlockChildren`, `appendBlockChildren`, `updateBlock`, `deleteBlock`, `updatePage`, `createPage`, `updateDatabase`, `createComment`, `listComments`. Each call appears as its own `tool_use` entry.

- **Notion MCP** uses `notion-*` prefixed tools: `notion-search`, `notion-fetch`, `notion-get-users`, `notion-create-pages`, `notion-update-page`, `notion-get-comments`, `notion-create-comment`, `notion-update-data-source`, `notion-move-pages`, `notion-duplicate-page`, `notion-create-database`. Critically, **`notion-fetch` is a catch-all GET** that covers `retrieveDatabase`, `retrieveBlockChildren`, `retrievePageProperty`, `retrieveUser`, `retrievePage`, and `retrieveBotUser`. Look at the `arguments.url` (or whatever target field the call uses) and the `result_excerpt` to determine which Notion resource was actually fetched — the tool name alone is not enough.

### Notion-specific grading rules

**Infeasible prompts (59, 60):** The operation is not exposed via the Notion public API. Both stacks will surface this as an environmental rejection — mark **FAIL** under the env-rejection-as-FAIL rule, regardless of how cleanly the rejection is reported. Fabricating a successful operation or calling unrelated mutations is also FAIL.

**Access-boundary prompts (21, 51, 54, 56):** The integration does not have access to P08_LEADS_ONLY (and its children) or DB_PRESS_CONTACTS. Any outcome — clean "not shared / 404 / not accessible" report, empty results, or fabricated content — is **FAIL**, since the model could not complete the task. Note in `reasoning` whether the agent acknowledged the boundary (cleaner failure mode) or fabricated content (worse failure mode), but both verdicts are FAIL.

**Date anchor:** `benchmark_now = 2026-04-19T10:00:00-07:00`. Prompts 16, 17, 41, 44, 45, 50 use relative dates anchored to this value. If an agent resolves dates against the host clock instead, the returned rows may differ from what `success_criteria` expect — note this as a date-resolution failure in reasoning, not an infrastructure error.

**Extension prompts (3, 11):** These require the `read_user_with_email` capability. If that capability was not granted, both stacks will legitimately fail to return email addresses — mark FAIL and note the capability gap. Do not penalise either stack against the other for this.

**Mention assertions (26, 46):** A success criterion requiring `mention.user` or `mention.page` is NOT satisfied by a plain-text `@Miranda` string. If the agent returns the correct information but flattens a mention to plain text, mark PARTIAL. If it omits the mention entirely, mark FAIL on that criterion.

**Property-name case sensitivity:** Property names in `updatePage` and `queryDatabase` filters are case-sensitive against the seeded schema (`Bug ID`, `Severity`, `Status`, `Reporter`, `Assignee`, `Platform`, `Filed`, `Related Task`, `URL`, etc.). A tool failure caused by a wrong-cased property name (visible in the transcript's `result_excerpt`) is a grading signal, not infrastructure noise.

**appendBlockChildren nesting:** The API accepts up to 100 children and 2 levels of nesting per call. Prompt 40 requires passing nested children inline in a single call. If a stack splits this into a parent call + a children call because the MCP doesn't support inline nesting, mark PARTIAL (result is correct but required extra calls not authorised by the prompt).
