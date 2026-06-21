import { Composio } from "@composio/core";
import "dotenv/config";

const composio = new Composio({ apiKey: process.env.COMPOSIO_API_KEY });

if (!process.env.NOTION_AUTH_CONFIG_ID) {
  const configs = await composio.authConfigs.list({ toolkit: "notion" });
  console.log("Notion auth configs:", configs.items.map((c) => ({ id: c.id, toolkit: c.toolkit })));
  console.log("Set NOTION_AUTH_CONFIG_ID in .env to one of these ids, then re-run.");
  process.exit(0);
}

const mcpConfig = await composio.mcp.create("notion-composio", {
  toolkits: [{ toolkit: "notion", authConfigId: process.env.NOTION_AUTH_CONFIG_ID }],
  manuallyManageConnections: false,
});

console.log("Config id:", mcpConfig.id);
console.log("Claude command:", mcpConfig.commands.claude);

const serverInstance = await composio.mcp.generate(process.env.USER_ID, mcpConfig.id);
console.log("MCP URL:", serverInstance.url);
