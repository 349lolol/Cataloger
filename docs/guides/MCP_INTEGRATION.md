# CatalogAI MCP Server - Code Execution Integration

This MCP (Model Context Protocol) server enables Claude Desktop and other AI assistants to interact with CatalogAI by writing and executing Python code.

## Why Code Execution vs. Simple Tools?

Traditional MCP tools require all data to flow through the AI's context, which is expensive and slow. Code execution allows Claude to:

1. **Write Python code** that directly interacts with your catalog system
2. **Process data locally** before returning results (massive token savings)
3. **Use control flow** (loops, conditionals) natively in code
4. **Filter large datasets** without loading everything into context

**Result: 98.7% reduction in token usage** for data-heavy operations.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude Desktop / Chat Interface                │
│  "Compare prices from 3 vendors for laptops"    │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │  1. Claude writes     │
       │     Python code       │
       └───────────┬───────────┘
                   │
       ┌───────────▼────────────────────────────┐
       │  2. Code Execution Sandbox             │
       │     (Secure Python environment)        │
       └───────────┬────────────────────────────┘
                   │
       ┌───────────▼───────────────────────────┐
       │  3. MCP Server (Code API)             │
       │     - Exposes Python SDK              │
       │     - catalogai.catalog.search()      │
       └──────────────────┬────────────────────┘
                          │
       ┌──────────────────▼────────────────────┐
       │   Flask REST API (Business Logic)     │
       └──────────────────┬────────────────────┘
                          │
                   Supabase PostgreSQL
```

## Setup

### 1. Build Sandbox Docker Image

```bash
# From Cataloger/ root directory
docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .
```

### 2. Install MCP Server Dependencies

```bash
cd catalogai_mcp
pip install -e .
```

### 3. Configure Claude Desktop

Copy the MCP server configuration to Claude Desktop:

**On macOS:**
```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Linux:**
```bash
cp claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
```

**On Windows:**
```bash
copy claude_desktop_config.json %APPDATA%\Claude\claude_desktop_config.json
```

Update the path in the config file to point to your actual Cataloger directory.

### 4. Run CatalogAI API

Make sure the Flask API is running:
```bash
cd ..
python run.py
```

### 5. Test in Claude Desktop

Restart Claude Desktop and try asking:

> "Search the catalog for laptops and show me the top 3 results"

Claude will write Python code using the catalogai SDK and execute it!

## Example Usage

### Basic Catalog Search

**User asks Claude:**
> "Find me Dell laptops in the catalog"

**Claude writes code:**
```python
import catalogai
import os

client = catalogai.CatalogAIClient(
    base_url=os.getenv("CATALOGAI_API_URL"),
    auth_token=os.getenv("CATALOGAI_AUTH_TOKEN")
)

results = client.catalog.search(query="Dell laptop", limit=5)
for item in results:
    print(f"- {item['item_name']}: {item['similarity_score']:.2f}")
```

**Code executes in sandbox and returns:**
```
- Dell Latitude 7430 Laptop: 0.89
```

### Complex Operations

**User asks Claude:**
> "Create a proposal to add a new printer to the catalog"

**Claude writes code:**
```python
import catalogai
import os

client = catalogai.CatalogAIClient(
    base_url=os.getenv("CATALOGAI_API_URL"),
    auth_token=os.getenv("CATALOGAI_AUTH_TOKEN")
)

# Create proposal
proposal = client.proposals.create(
    proposal_type="ADD_ITEM",
    item_name="HP LaserJet Pro M404dn",
    item_description="Monochrome laser printer with duplex printing",
    item_category="Office Equipment",
    item_metadata={"brand": "HP", "type": "printer"}
)

print(f"Created proposal ID: {proposal['id']}")
print(f"Status: {proposal['status']}")
```

## Security

The code execution environment is sandboxed with:

- **CPU Limits**: 50% of one core
- **Memory Limits**: 512MB max
- **Execution Timeout**: 10 seconds
- **Network Isolation**: Only Flask API accessible
- **Read-Only File System**: Except /tmp
- **Restricted Imports**: Only catalogai SDK and safe builtins

## Troubleshooting

### "Docker image not found"

Build the sandbox image:
```bash
docker build -f catalogai_mcp/sandbox.Dockerfile -t catalogai-sandbox:latest .
```

### "Connection refused to API"

Make sure the Flask API is running on port 5000:
```bash
python run.py
```

### "Authentication failed"

You need a valid Supabase JWT token. The token should be passed in the `user_context` parameter.

## Advanced: Custom Tools

You can add more MCP tools in [server.py](server.py):

```python
@mcp.tool()
async def approve_pending_proposals(max_count: int = 5) -> dict:
    """Auto-approve up to max_count pending proposals."""
    # Implementation here
    pass
```

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [CatalogAI SDK Documentation](../catalogai_sdk/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
