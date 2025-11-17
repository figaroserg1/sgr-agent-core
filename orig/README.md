# Original SGR demos

This folder contains the original CRM demo that inspired the deep-research agent and a
modernised variant (`rinat_dynamic_demo.py`) that showcases dynamic tool discovery.

## MCP support in `rinat_dynamic_demo.py`

The dynamic demo can now load additional tools from any Model Context Protocol (MCP)
server. At startup the script reads [`rinat_dynamic_demo.mcp.yaml`](./rinat_dynamic_demo.mcp.yaml),
expands `$VAR`/`${VAR}` placeholders using your environment, and converts the result into
an MCP configuration. Every server listed under `mcp.mcpServers` is queried and the tools
it exposes are automatically merged with the built-in CRM actions.

### Confluence MCP example

The repository ships with a ready-to-edit Confluence entry:

```yaml
mcp:
  mcpServers:
    confluence:
      url: "${CONFLUENCE_MCP_URL}"
      headers:
        Authorization: "Bearer ${CONFLUENCE_MCP_TOKEN}"
        X-Atlassian-Tenant: "${CONFLUENCE_CLOUD_ID}"
```

To enable it:

1. Export the three environment variables (`CONFLUENCE_MCP_URL`, `CONFLUENCE_MCP_TOKEN`,
   `CONFLUENCE_CLOUD_ID`) with the values issued by your Confluence MCP deployment.
2. Run `python orig/rinat_dynamic_demo.py` – the demo will load the Confluence tool list
   and dynamically add each function to the planner schema.

### Adding more MCP servers

1. Open `orig/rinat_dynamic_demo.mcp.yaml`.
2. Under `mcp.mcpServers`, add a new key (for example `sharepoint`) and specify at least a
   `url`. You can also provide `headers`, `command`, or any other standard MCP transport
   fields supported by [`fastmcp.MCPConfig`](https://github.com/modelcontextprotocol/fastmcp).
3. (Optional) Reference environment variables in the values so that secrets never land in
   source control. The demo automatically calls `os.path.expandvars`/`expanduser` on every
   string value before constructing the config.
4. Restart the demo. Each new server is queried once at startup and its tools are registered
   as first-class actions in the next-step schema without any extra code changes.
