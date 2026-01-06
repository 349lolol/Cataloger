# CatalogAI

Multi-tenant enterprise procurement catalog with AI-powered search and approval workflows.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 / Flask |
| Database | Supabase (PostgreSQL + pgvector) |
| Auth | Supabase Auth (JWT) |
| AI | Google Gemini (embeddings + enrichment) |
| MCP | Model Context Protocol server for Claude |
| Container | Docker |

## Features

### Catalog Management
- Semantic search using vector embeddings (pgvector, 768 dimensions)
- AI product enrichment (auto-fills description, pricing, vendor, SKU)
- Category filtering and pagination

### Multi-Tenant Security
- Row Level Security (RLS) on all tables
- Organization isolation at database level
- Service role for backend admin operations

### Role-Based Access
- `admin` - full catalog access, audit logs
- `reviewer` - approve/reject requests and proposals
- `requester` - search catalog, submit requests

### Approval Workflows
- **Requests**: employees request items, reviewers approve/reject
- **Proposals**: add/replace/deprecate catalog items with approval flow
- Auto-create proposals when approving requests

### MCP Server
- 17 direct API tools for Claude integration
- Sandboxed Python code execution (Docker)
- SDK exposed as code API for efficient token usage

### Observability
- Audit logging for compliance
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
  server.py      # 17 tools
  code_executor.py  # Docker sandbox

supabase/
  migrations/    # 8 SQL migrations (schema, RLS, pgvector)

scripts/
  seed_data.py   # Seeds ~100 enterprise products

tests/           # pytest suite
```

## Database Schema

- `orgs` - tenant organizations
- `org_memberships` - user-org mapping with roles
- `catalog_items` - products with metadata, pricing, vendor
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

POST /api/requests
GET  /api/requests
GET  /api/requests/:id
POST /api/requests/:id/review

POST /api/proposals
GET  /api/proposals
GET  /api/proposals/:id
POST /api/proposals/:id/approve
POST /api/proposals/:id/reject

POST /api/products/enrich
GET  /api/admin/audit-log
```

## Environment Variables

```
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=768
```

## Database Migrations

Run in order:
1. `00001_initial_schema.sql`
2. `00002_rls_policies.sql`
3. `00003_pgvector_setup.sql`
4. `00004_add_product_fields.sql`
5. `00005_fix_proposal_rls.sql`
6. `00006_update_embedding_dimension.sql`

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
python run.py

# Seed database
python scripts/seed_data.py

# Run tests
pytest
```

## MCP Integration

Configure in Claude Desktop:

```json
{
  "mcpServers": {
    "catalogai": {
      "command": "python",
      "args": ["-m", "catalogai_mcp"],
      "env": {
        "SUPABASE_URL": "...",
        "USER_EMAIL": "...",
        "USER_PASSWORD": "..."
      }
    }
  }
}
```
