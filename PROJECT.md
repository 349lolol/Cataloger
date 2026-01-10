# CatalogAI

Multi-tenant enterprise procurement catalog with AI-powered search and approval workflows.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 / Flask |
| Database | Supabase (PostgreSQL + pgvector) |
| Auth | Supabase Auth (JWT with RLS) |
| AI | Google Gemini (embeddings + enrichment) |
| MCP | Model Context Protocol server for Claude |
| Container | Docker (sandboxed code execution) |

## Features

### Catalog Management
- Semantic search using vector embeddings (pgvector, 768 dimensions)
- AI product enrichment via Gemini (auto-fills description, pricing, vendor, SKU)
- Category filtering and pagination

### Multi-Tenant Security
- Row Level Security (RLS) enforced at database level
- User JWT passed to Supabase for RLS policy evaluation
- Organization isolation via `user_org_id()` helper function
- Service role reserved for embeddings and audit writes only

### Role-Based Access
- `admin` - full catalog access, audit logs, user management
- `reviewer` - approve/reject requests and proposals
- `requester` - search catalog, submit requests

### Approval Workflows
- **Requests**: employees request items, reviewers approve/reject
- **Proposals**: add/replace/deprecate catalog items with approval flow
- Auto-create proposals when approving requests

### Atomic Database Operations
- `create_catalog_item_with_embedding()` - atomic item + embedding insert
- `merge_add_item_proposal()` - atomic proposal approval for ADD_ITEM
- `merge_replace_item_proposal()` - atomic proposal approval for REPLACE_ITEM
- `merge_deprecate_item_proposal()` - atomic proposal approval for DEPRECATE_ITEM

### MCP Server
- 19 tools for Claude integration (login, whoami, catalog, requests, proposals, admin)
- Sandboxed Python code execution via Docker
- Skills module for efficient multi-step operations

### Observability
- Audit logging for compliance (immutable)
- Structured JSON logging (production)
- Health and readiness endpoints

## Project Structure

```
app/
  api/           # Flask blueprints (catalog, requests, proposals, auth, admin)
  services/      # Business logic (catalog, embedding, proposal, request, audit)
  middleware/    # Auth, rate limiting, error handling
  utils/         # Resilience utilities (retry, circuit breaker)

catalogai_sdk/   # Python SDK for API access
  client.py      # Main client class
  catalog.py     # Catalog operations
  requests.py    # Request operations
  proposals.py   # Proposal operations

catalogai_mcp/   # MCP server for Claude
  server.py      # 19 tools (login, catalog, requests, proposals, admin, code execution)
  code_executor.py  # Docker sandbox runner
  skills/        # Thin SDK wrapper for code execution
  sandbox.Dockerfile  # Isolated execution environment

supabase/
  migrations/    # 10 SQL migrations (schema, RLS, pgvector, atomic functions)

scripts/
  seed_data.py   # Seeds test orgs, users, and ~100 enterprise products

tests/           # pytest suite (unit + integration)
```

## Database Schema

- `orgs` - tenant organizations
- `org_memberships` - user-org mapping with roles
- `catalog_items` - products with metadata, pricing, vendor, status
- `catalog_item_embeddings` - vector embeddings for semantic search
- `requests` - procurement request workflow
- `proposals` - catalog change governance (ADD/REPLACE/DEPRECATE)
- `audit_events` - immutable event log

## API Endpoints

```
GET  /api/health
GET  /api/auth/verify

POST /api/catalog/search
GET  /api/catalog/items
GET  /api/catalog/items/:id
POST /api/catalog/request-new-item

GET  /api/requests
GET  /api/requests/:id
POST /api/requests/:id/review

POST /api/proposals
GET  /api/proposals
GET  /api/proposals/:id
POST /api/proposals/:id/approve
POST /api/proposals/:id/reject

POST /api/products/enrich
POST /api/products/enrich-batch

GET  /api/admin/audit-log
POST /api/admin/embeddings/check
```

## Environment Variables

```
# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=<random-key>
PORT=5001

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

# Gemini AI
GEMINI_API_KEY=<api-key>
GEMINI_MODEL=gemini-3-flash-preview
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=768

# Resilience
CIRCUIT_BREAKER_FAIL_MAX=5
CIRCUIT_BREAKER_TIMEOUT=60

# MCP
API_URL=http://localhost:5001
```

## Database Migrations

Run in order via Supabase dashboard or CLI:

1. `00001_initial_schema.sql` - base tables
2. `00002_rls_policies.sql` - RLS policies and helper functions
3. `00003_pgvector_setup.sql` - vector extension and search function
4. `00004_add_product_fields.sql` - price, vendor, SKU fields
5. `00005_fix_proposal_rls.sql` - proposal policy fixes
6. `00006_update_embedding_dimension.sql` - 768-dim vectors
7. `00007_org_memberships_service_role_policy.sql` - service role access
8. `00008_service_role_policies.sql` - additional service policies
9. `00009_atomic_create_item.sql` - atomic item creation function
10. `00010_atomic_proposal_merge.sql` - atomic proposal merge functions

## MCP Integration

Configure in Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "catalogai": {
      "command": "/path/to/mcp_venv/bin/python",
      "args": ["-m", "catalogai_mcp.server"],
      "cwd": "/path/to/Cataloger",
      "env": {
        "PYTHONPATH": "/path/to/Cataloger",
        "SUPABASE_URL": "https://xxx.supabase.co",
        "SUPABASE_KEY": "<anon-key>",
        "API_URL": "http://localhost:5001"
      }
    }
  }
}
```

MCP tools require authentication via `login(email, password)` before use.

## MCP Tools

| Tool | Description |
|------|-------------|
| `login` | Authenticate with email/password |
| `whoami` | Check authentication status |
| `search_catalog` | Semantic search |
| `get_catalog_item` | Get item by ID |
| `list_catalog` | List items with filters |
| `create_request` | Create procurement request |
| `list_requests` | List requests |
| `get_request` | Get request details |
| `approve_request` | Approve request (reviewer+) |
| `reject_request` | Reject request (reviewer+) |
| `create_proposal` | Create catalog change proposal |
| `list_proposals` | List proposals |
| `get_proposal` | Get proposal details |
| `approve_proposal` | Approve and merge proposal |
| `reject_proposal` | Reject proposal |
| `enrich_product` | AI product enrichment |
| `enrich_products_batch` | Batch enrichment (max 20) |
| `get_audit_log` | View audit events (admin) |
| `check_embeddings_health` | Repair embeddings (admin) |
| `list_skills` | Show code execution skills |
| `execute_code` | Run Python in Docker sandbox |
