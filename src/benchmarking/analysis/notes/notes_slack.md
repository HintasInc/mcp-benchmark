## Slack-specific surface notes

### Reading the transcript

The two stacks expose Slack's API surface differently — the same outcome may show up very differently in the `transcript`:

- **Slack MCP** publishes one tool per Slack API method (`conversations.list`, `chat.postMessage`, `users.info`, etc.). Each method invocation appears as a separate `tool_use` entry whose `tool_name` matches the API method.

- **Hintas MCP** dispatches via two generic tools: `search_tools` (capability discovery) and `call_tool_chain` (multi-step invocation). The downstream Slack methods executed by `call_tool_chain` do **not** surface as separate `tool_use` blocks — they live inside the `arguments` payload of `call_tool_chain` and inside the `result_excerpt` of its tool_result. Read those payloads to see what Slack methods Hintas actually invoked. A short `tools_invoked` list does not mean Hintas did less work; it may mean a single `call_tool_chain` ran several Slack methods internally.

### Workspace context

The benchmark uses a seeded Slack workspace where the integration is added to specific channels and DM conversations. If the model surfaces "channel not found", "user not in channel", "missing scope", or any rejection of that kind — mark **FAIL** under the verdict rules. Do not give credit for politely failing.
