## Multi-API surface notes

These prompts span **Slack, Gmail, and Notion** in a single session. Each prompt's
`apis` field lists which surfaces it touches; `cross_api_dependency` names the value
that must be carried from one surface to the next. **Grading is strictly binary**: a
prompt is **PASS** only when *every* task on *every* surface in `apis` completed and the
cross-API handoff held; if *any* required task failed, was skipped, was blocked, or was
fabricated, the verdict is **FAIL**. There is no PARTIAL on this platform.

### Reading the transcript

The two stacks reach the three surfaces very differently — the same outcome can look
very different in the `transcript`:

- **Baseline (official, stitched)** exposes one tool surface per stitched server:
  - **Slack** — one tool per Slack API method (`conversations.list`, `chat.postMessage`,
    `users.info`, …); each appears as its own `tool_use`.
  - **Notion** — `notion-*` tools (`notion-search`, `notion-fetch`, `notion-create-pages`, …).
    `notion-fetch` is a catch-all GET; read `arguments`/`result_excerpt` to see which
    Notion resource was actually fetched.
  - **Gmail** — the hosted Gmail connector, tools prefixed `claude_ai_Gmail`
    (`search_threads`, `create_draft`, `label_message`, …); each appears as its own `tool_use`.

- **Hintas (unified server)** serves all three surfaces from one MCP. If it dispatches
  through generic tools (e.g. `search_tools` for discovery and `call_tool_chain` for
  execution), the downstream Slack/Gmail/Notion methods will **not** surface as separate
  `tool_use` blocks — they live inside the `arguments` payload of the dispatch call and
  inside its `result_excerpt`. Read those payloads to see what each surface actually did.
  A short `tools_invoked` list does **not** mean Hintas did less work; a single dispatch
  call may run several methods across multiple surfaces internally.

In both stacks, decide what landed on each surface from the actual tool **arguments and
results**, not from the tool name alone.

### Cross-API grading (binary)

- **Per-surface verification.** Walk the transcript surface by surface for every entry in
  `apis`. Confirm each one's work landed (right method, real data, no blocking error). PASS
  requires *all* of them; if even one surface's required work did not land, the verdict is
  **FAIL**. There is no partial credit for completing some surfaces but not others.
- **Handoff integrity.** The `cross_api_dependency` value (an ID, email, or page produced
  upstream) must be the *real* value carried downstream. A fabricated or mismatched handoff,
  or a skipped dependent step, is **FAIL**. Name the failing surface and the broken handoff
  in `reasoning`.

### Feasibility and access boundaries

- **`feasible_on_free_plan`** is `"core"` or `"extension"`:
  - `"core"` — every surface is doable on the seeded plan; grade normally.
  - `"extension"` — one surface's operation may require a capability beyond the free plan
    (e.g. Slack `conversations.kick` needs `channels:manage`, often gated). Grading stays
    binary: if a required task could not be completed — **even when it was legitimately
    plan-gated** — the prompt is **FAIL**, because not all tasks were completed. Use
    `noteworthy_paths` to record whether the agent *cleanly reported* the block (good
    behaviour) or *fabricated* success / fired unrelated mutations (bad behaviour); that
    distinction informs the writeup, not the verdict.
- **Environmental rejection on a feasible surface** — "channel not found", "user not in
  channel", "missing scope", "page not shared", "404 / not accessible" where the prompt and
  plan should have allowed the operation — blocks that surface, and any blocked required
  task makes the prompt **FAIL**. Do not give credit for politely failing a surface that
  should have worked.

### Comparing tool-call metrics across stacks

The per-run aggregates (`avg tool calls`, `total tool failures`) count one MCP `tool_use`
per call. These are **not directly comparable across stacks**: the baseline surfaces every
API method as its own call (so a 3-surface workflow shows many calls/failures), while the
Hintas unified server runs several methods *inside* one `execute_tools` dispatch (so the
same workflow shows one call, and an internal surface failure where the wrapper returns
success does not register as a failed call). Read the dispatch payloads to judge what
actually happened per surface; treat the raw counts as stack-internal, not head-to-head.
