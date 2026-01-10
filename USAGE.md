# CatalogAI Usage Guide

This guide walks you through setting up and running CatalogAI from scratch.

## Prerequisites

- Python 3.11+
- Docker (for MCP code execution)
- Supabase account (free tier works)
- Google Cloud account (for Gemini API)

## 1. Supabase Setup

### Create Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and keys from Settings > API:
   - `SUPABASE_URL` - Project URL
   - `SUPABASE_KEY` - anon/public key
   - `SUPABASE_SERVICE_ROLE_KEY` - service_role key (keep secret)

### Run Migrations

In the Supabase SQL Editor, run each migration file in order:

```
supabase/migrations/00001_initial_schema.sql
supabase/migrations/00002_rls_policies.sql
supabase/migrations/00003_pgvector_setup.sql
supabase/migrations/00004_add_product_fields.sql
supabase/migrations/00005_fix_proposal_rls.sql
supabase/migrations/00006_update_embedding_dimension.sql
supabase/migrations/00007_org_memberships_service_role_policy.sql
supabase/migrations/00008_service_role_policies.sql
supabase/migrations/00009_atomic_create_item.sql
supabase/migrations/00010_atomic_proposal_merge.sql
```

## 2. Gemini API Setup

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Note your `GEMINI_API_KEY`

## 3. Environment Configuration

Create `.env` in the project root:

```bash
# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=$(openssl rand -hex 32)
FLASK_APP=run.py
PORT=5001

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=768

# Resilience
CIRCUIT_BREAKER_FAIL_MAX=5
CIRCUIT_BREAKER_TIMEOUT=60

# MCP
API_URL=http://localhost:5001
```

## 4. Flask API Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Seed Test Data

```bash
python scripts/seed_data.py
```

This creates:
- 2 test organizations (Acme Corp, TechStart Inc)
- 6 test users with different roles
- ~100 enterprise catalog items with embeddings

Note the generated passwords - you'll need them to log in.

### Run the Server

```bash
python run.py
```

Server runs at `http://localhost:5001`

### Verify It Works

```bash
curl http://localhost:5001/api/health
# {"status": "healthy"}
```

## 5. MCP Server Setup (Optional)

The MCP server lets Claude Desktop interact with CatalogAI directly.

### Create Separate Virtual Environment

```bash
python -m venv mcp_venv
source mcp_venv/bin/activate
pip install -r catalogai_mcp/requirements.txt
pip install -e catalogai_sdk/
```

### Build Docker Sandbox (for code execution)

```bash
./catalogai_mcp/build_sandbox.sh
```

### Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "catalogai": {
      "command": "/absolute/path/to/mcp_venv/bin/python",
      "args": ["-m", "catalogai_mcp.server"],
      "cwd": "/absolute/path/to/Cataloger",
      "env": {
        "PYTHONPATH": "/absolute/path/to/Cataloger",
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key",
        "API_URL": "http://localhost:5001"
      }
    }
  }
}
```

Replace `/absolute/path/to/` with your actual paths.

### Restart Claude Desktop

After updating the config, restart Claude Desktop. The MCP server should connect.

### Using MCP Tools

In Claude Desktop, you must first authenticate:

```
Use the login tool with:
- email: admin1@acmecorp.test
- password: (password from seed script)
```

Then you can use other tools like `search_catalog`, `list_requests`, etc.

## 6. Test Users

The seed script creates these users (passwords shown during seeding):

| Email | Role | Organization |
|-------|------|--------------|
| admin1@acmecorp.test | admin | Acme Corp |
| reviewer1@acmecorp.test | reviewer | Acme Corp |
| user1@acmecorp.test | requester | Acme Corp |
| admin1@techstart.test | admin | TechStart Inc |
| reviewer1@techstart.test | reviewer | TechStart Inc |
| user1@techstart.test | requester | TechStart Inc |

To reset a password via Supabase:

```bash
curl -X PUT "https://your-project.supabase.co/auth/v1/admin/users/{user_id}" \
  -H "apikey: your-service-role-key" \
  -H "Authorization: Bearer your-service-role-key" \
  -H "Content-Type: application/json" \
  -d '{"password": "NewPassword123"}'
```

## 7. API Authentication

All API endpoints (except `/api/health`) require a Bearer token.

### Get a Token

```bash
curl -X POST "https://your-project.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: your-anon-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin1@acmecorp.test", "password": "your-password"}'
```

Response includes `access_token`.

### Use the Token

```bash
curl http://localhost:5001/api/catalog/items \
  -H "Authorization: Bearer your-access-token"
```

## 8. Common Operations

### Search Catalog

```bash
curl -X POST http://localhost:5001/api/catalog/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop for development", "limit": 5}'
```

### Create a Request

```bash
curl -X POST http://localhost:5001/api/catalog/request-new-item \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standing Desk",
    "justification": "Need ergonomic workspace",
    "use_ai_enrichment": true
  }'
```

### List Pending Requests (Reviewer)

```bash
curl "http://localhost:5001/api/requests?status=pending" \
  -H "Authorization: Bearer $REVIEWER_TOKEN"
```

### Approve a Request

```bash
curl -X POST http://localhost:5001/api/requests/{request_id}/review \
  -H "Authorization: Bearer $REVIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "review_notes": "Approved for Q1 budget"}'
```

## 9. Running Tests

```bash
source venv/bin/activate
pytest
```

For coverage:

```bash
pytest --cov=app --cov-report=html
```

## 10. Troubleshooting

### Port 5000 in use (macOS)

macOS uses port 5000 for AirPlay. The app defaults to 5001, but if you see conflicts:

```bash
# Check what's using the port
lsof -i :5001

# Or change PORT in .env
PORT=5002
```

### MCP Server Disconnected

1. Check Flask is running on the correct port
2. Verify PYTHONPATH in Claude Desktop config
3. Check MCP venv has all dependencies
4. Look at Claude Desktop logs for errors

### Authentication Fails

1. Verify SUPABASE_KEY is the anon key (not service role)
2. Check the user exists and password is correct
3. Ensure user has org membership (required for API access)

### Embeddings Not Working

1. Verify GEMINI_API_KEY is valid
2. Check embedding dimension matches (768)
3. Run embeddings health check as admin:
   ```bash
   curl -X POST http://localhost:5001/api/admin/embeddings/check \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```
