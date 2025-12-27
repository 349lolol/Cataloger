# CatalogAI MCP Integration

For detailed MCP integration documentation, see [docs/guides/MCP_INTEGRATION.md](../docs/guides/MCP_INTEGRATION.md)

## Quick Setup

1. Build sandbox image:
```bash
docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .
```

2. Install MCP server:
```bash
cd catalogai_mcp
pip install -e .
```

3. Configure Claude Desktop - see full guide in docs/guides/MCP_INTEGRATION.md
