# CatalogAI MCP Server

Agentic procurement interface for Claude Desktop.

## Features

The MCP server implements **Anthropic's Code Execution with MCP pattern** for massive token reduction, alongside 17 direct tools for catalog operations.

### Code Execution Tool (⭐ Recommended)

- `execute_code` - Execute Python code in isolated Docker sandbox with catalogai SDK
  - **98.7% token reduction** for multi-step workflows
  - Auto-authenticated with your session token
  - Pre-installed catalogai_sdk for all operations
  - Secure: 512MB RAM limit, 50% CPU, 30s timeout, isolated network

**Example**: Instead of 4-5 tool calls consuming 50K tokens, write Python code that executes in one call using ~1K tokens:

```python
from catalogai import CatalogAI

client = CatalogAI()  # Auto-authenticated

# Multi-step workflow in one execution
results = client.catalog.search("laptop", limit=20)
affordable = [r for r in results if r.get('price', 9999) < 2000]
best = max(affordable, key=lambda x: x['similarity_score'])

request = client.requests.create(
    item_name=best['name'],
    justification=f"Best laptop under $2000: {best['name']}"
)
print(f"Created request {request['id']}")
```

### Direct Tools (Legacy)

### Catalog Tools
- `search_catalog` - Semantic search with vector embeddings
- `get_catalog_item` - Get item details
- `list_catalog` - Browse catalog with filters

### Request Tools
- `create_request` - Submit procurement request (with optional AI enrichment)
- `list_requests` - View requests (filter by status)
- `get_request` - Get request details
- `approve_request` - Approve request (reviewer/admin)
- `reject_request` - Reject request (reviewer/admin)

### Proposal Tools
- `create_proposal` - Create catalog change proposal (reviewer/admin)
- `list_proposals` - View proposals (filter by status)
- `get_proposal` - Get proposal details
- `approve_proposal` - Approve proposal (reviewer/admin, auto-updates catalog)
- `reject_proposal` - Reject proposal (reviewer/admin)

### AI Enrichment Tools
- `enrich_product` - Auto-populate product details with Gemini 3.0
- `enrich_products_batch` - Batch enrichment (max 20)

### Admin Tools
- `get_audit_log` - View audit events (admin)
- `check_embeddings_health` - Check/repair embeddings (admin)

## Setup

### 1. Install Dependencies

```bash
cd catalogai_mcp
pip install -e .
```

### 2. Run Seeding Script

First, seed your database with test data:

```bash
# Make sure .env has required vars
python scripts/seed_data.py
```

This creates:
- 1 organization ("Acme Corporation")
- 10 test users (3 admins, 3 reviewers, 4 requesters)
- 30 catalog items (20 hardware + 10 SaaS)
- Sample requests

**Save the credentials** printed by the script - you'll need them for MCP config.

### 3. Build Docker Sandbox (Required for Code Execution)

To use the `execute_code` tool, build the Docker sandbox:

```bash
cd catalogai_mcp
./build_sandbox.sh
```

This creates a secure, isolated container with:
- Python 3.11-slim
- catalogai_sdk pre-installed
- Non-root user (security)
- Resource limits (512MB RAM, 50% CPU, 30s timeout)

**Skip this step** if you only want to use direct tools (no code execution).

### 4. Test Setup (Optional but Recommended)

Run the setup verification script to catch issues early:

```bash
python test_setup.py
```

This checks:
- Dependencies are installed
- Environment variables are set correctly
- Supabase authentication works
- API is reachable

### 5. Configure Claude Desktop

Edit `~/.config/claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "catalogai": {
      "command": "python",
      "args": ["-m", "catalogai_mcp.server"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key-here",
        "USER_EMAIL": "admin1@acmecorp.test",
        "USER_PASSWORD": "password-from-seed-script",
        "API_URL": "http://localhost:5000"
      }
    }
  }
}
```

**Get values from**:
- `SUPABASE_URL` & `SUPABASE_KEY` - From your Supabase project settings
- `USER_EMAIL` & `USER_PASSWORD` - From seeding script output
- `API_URL` - Your Flask API URL (default: http://localhost:5000)

### 5. Start Flask API

```bash
python run.py
```

### 6. Restart Claude Desktop

Claude Desktop will automatically connect to your MCP server on startup.

## Usage Examples

### Code Execution Workflow (⭐ Recommended for Multi-Step Tasks)

**Scenario**: Find chairs under $500, create request for the most ergonomic one

```
You: "Find office chairs under $500 and request the most ergonomic one"

Claude generates Python code and calls execute_code:

from catalogai import CatalogAI

client = CatalogAI()

# Search for ergonomic chairs
results = client.catalog.search("ergonomic office chair", limit=20)
affordable = [r for r in results if r.get('price', 9999) < 500]

if not affordable:
    print("No chairs found under $500")
else:
    # Find most ergonomic (highest similarity score)
    best = max(affordable, key=lambda x: x['similarity_score'])

    # Create request
    request = client.requests.create(
        item_name=best['name'],
        justification=f"Most ergonomic chair under $500: {best['name']} at ${best['price']}"
    )
    print(f"✓ Created request {request['id']} for {best['name']}")

Output: "✓ Created request REQ-123 for Herman Miller Sayl Chair"

Token usage: ~1,200 tokens (vs ~15,000 with direct tools)
```

**Why this is better**:
- Single tool call instead of 4-5 chained calls
- Complex filtering logic in Python (cheaper than passing all data to Claude)
- Only final output returned to Claude (98% less token usage)
- Faster execution (no round trips between tools)

### Direct Tool Examples (For Simple Operations)

### Search Catalog
```
You: "Search for laptops suitable for video editing"

Claude calls: search_catalog("laptop video editing", limit=5)

Response: Returns 5 laptops with specs, prices, similarity scores
```

### Create Request with AI Enrichment
```
You: "I need a Herman Miller Aeron chair for our office"

Claude calls:
1. enrich_product("Herman Miller Aeron Chair")
   → Gets price, SKU, specs from Gemini
2. create_request(
     product_name="Herman Miller Aeron Chair Size B",
     justification="Office ergonomics improvement",
     use_ai_enrichment=True
   )

Response: Request created with full product details
```

### Approve Request Workflow
```
You: "Show me pending requests and approve the laptop one"

Claude calls:
1. list_requests(status="pending")
   → Finds "laptop for video editing" request
2. approve_request(
     request_id="abc-123",
     review_notes="Approved for Q1 budget"
   )

Response: Request approved
```

### Multi-Step Agentic Workflow
```
You: "We need 5 new MacBook Pros for the engineering team.
      Search if we have them, if not create a request and proposal."

Claude orchestrates:
1. search_catalog("MacBook Pro")
   → Finds existing but different model
2. enrich_product("MacBook Pro 16 M3 Max")
   → Gets current specs and pricing
3. create_request(...)
   → Creates procurement request
4. approve_request(..., create_proposal=True, proposal_data={...})
   → Auto-creates proposal
5. approve_proposal(...)
   → Adds to catalog

All from one conversational prompt!
```

## Authentication

The MCP server authenticates **once on startup** using Supabase credentials, then reuses the JWT token for all API calls. This is secure and mimics how a real client application works.

**User Roles**:
- **Requester**: Can search, create requests, view own requests
- **Reviewer**: All requester permissions + approve/reject requests/proposals
- **Admin**: All reviewer permissions + audit logs, system maintenance

Switch users by changing `USER_EMAIL` and `USER_PASSWORD` in the config.

## Troubleshooting

### "Authentication failed"
- Check `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Verify user credentials from seeding script
- Make sure Flask API is running

### "API Error 401"
- JWT token may have expired (restart MCP server)
- Check user has proper role for the operation

### "Tool not working"
- Check Claude Desktop logs: Help → View Logs
- Verify Flask API is accessible at `API_URL`
- Ensure you ran database migrations

## Architecture

```
Claude Desktop
      ↓
  MCP Server (catalogai_mcp/server.py)
  - Authenticates on startup
  - Holds JWT token
  - Exposes 17 tools
      ↓
  Flask REST API (localhost:5000)
  - Validates JWT
  - Enforces RBAC
  - Calls services
      ↓
  Supabase (PostgreSQL + pgvector)
  - RLS policies
  - Vector search
  - Auth
```

## Next Steps

1. **Test with different roles** - Try requester, reviewer, admin users
2. **Build complex workflows** - Chain multiple tools in one conversation
3. **Deploy to production** - Update `API_URL` to your production endpoint
4. **Add custom tools** - Extend server.py with domain-specific operations

## Development

To modify the MCP server:

1. Edit `catalogai_mcp/server.py`
2. Add new `@mcp.tool()` functions
3. Restart Claude Desktop to reload

The server uses FastMCP framework - see [FastMCP docs](https://github.com/jlowin/fastmcp) for more info.
