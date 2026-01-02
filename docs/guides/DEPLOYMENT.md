# Deployment & Testing Guide

This guide covers deploying CatalogAI for beta testing and production environments.

## Pre-Deployment Checklist

- [ ] All tests passing (`python -m pytest tests/ -q`)
- [ ] Environment variables configured
- [ ] Supabase database migrations applied
- [ ] Gemini API key obtained and tested

## Environment Configuration

### Required Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJ...` |
| `GEMINI_API_KEY` | Google Gemini API key | `AI...` |
| `FLASK_SECRET_KEY` | Random secret (32+ chars) | `your-random-secret` |
| `FLASK_ENV` | Environment mode | `production` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `CIRCUIT_BREAKER_FAIL_MAX` | `5` | Failures before circuit opens |
| `CIRCUIT_BREAKER_TIMEOUT` | `60` | Seconds before circuit resets |
| `RETRY_MAX_ATTEMPTS` | `3` | Connection error retry attempts |
| `RETRY_RATE_LIMIT_ATTEMPTS` | `5` | Rate limit retry attempts |

## Database Setup

Run migrations in Supabase SQL Editor in order:

1. `supabase/migrations/00001_initial_schema.sql` - Core tables
2. `supabase/migrations/00002_rls_policies.sql` - Row-level security
3. `supabase/migrations/00003_pgvector_setup.sql` - Vector search extension
4. `supabase/migrations/00004_add_product_fields.sql` - Extended product fields
5. `supabase/migrations/00005_fix_proposal_rls.sql` - RLS policy fixes
6. `supabase/migrations/00006_update_embedding_dimension.sql` - 768-dim embeddings

## Local Development

### Flask Development Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py
```

### Gunicorn (Production-like)

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 run:app
```

## Docker Deployment

### Build Image

```bash
docker build -t catalogai:latest .
```

### Run Container

```bash
docker run -d \
  --name catalogai \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  catalogai:latest
```

### Verify Deployment

```bash
# Liveness check
curl http://localhost:5000/api/health

# Readiness check (verifies database + Gemini)
curl http://localhost:5000/api/readiness
```

Expected responses:

```json
// /api/health
{"status": "healthy", "uptime_seconds": 123}

// /api/readiness
{"status": "ready", "checks": {"database": true, "gemini_api": true}, "uptime_seconds": 123}
```

## AWS Deployment

### Elastic Beanstalk

Use the included `Dockerrun.aws.json`:

```bash
eb init -p docker catalogai
eb create catalogai-beta --single
eb setenv SUPABASE_URL=... SUPABASE_KEY=... # etc
```

### ECS/Fargate

Use the included `buildspec.yml` with CodeBuild:

```bash
aws codebuild start-build --project-name catalogai
```

### AWS Secrets Manager (Production)

Enable in `.env`:

```bash
USE_AWS_SECRETS=true
AWS_SECRET_NAME=catalogai/production
AWS_REGION=us-east-1
```

## MCP Server Setup

For Claude Desktop integration:

1. Configure environment:
```bash
export USER_EMAIL=your-email@example.com
export USER_PASSWORD=your-password
export API_URL=http://localhost:5000
```

2. Run MCP server:
```bash
python -m catalogai_mcp.server
```

3. Add to Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "catalogai": {
      "command": "python",
      "args": ["-m", "catalogai_mcp.server"],
      "env": {
        "USER_EMAIL": "...",
        "USER_PASSWORD": "...",
        "API_URL": "http://localhost:5000"
      }
    }
  }
}
```

## Beta Testing Scenarios

### 1. Health & Readiness

```bash
# Should return 200
curl -s http://localhost:5000/api/health | jq .
curl -s http://localhost:5000/api/readiness | jq .
```

### 2. Authentication Flow

```bash
# Get JWT from Supabase
TOKEN=$(curl -s -X POST \
  "https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' \
  | jq -r '.access_token')

# Use JWT for API calls
curl -s http://localhost:5000/api/auth/verify \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 3. Catalog Search

```bash
curl -s -X POST http://localhost:5000/api/catalog/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop for development", "limit": 5}' | jq .
```

### 4. Create Catalog Item (Admin)

```bash
curl -s -X POST http://localhost:5000/api/catalog/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro 16",
    "description": "High-performance laptop",
    "category": "Electronics",
    "price": 2499.00,
    "vendor": "Apple"
  }' | jq .
```

### 5. Product Enrichment

```bash
curl -s -X POST http://localhost:5000/api/products/enrich \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Dell XPS 15"}' | jq .
```

### 6. Multi-Tenant Isolation

Test that users can only see their org's data:

1. Create users in different orgs
2. Add catalog items as each user
3. Search as each user - verify they only see own org's items

### 7. Role-Based Access

| Role | Can Do | Cannot Do |
|------|--------|-----------|
| `requester` | Search, create requests | Create items, approve |
| `reviewer` | Above + approve requests | Create items |
| `admin` | All operations | - |

### 8. Error Handling

```bash
# Invalid auth
curl -s http://localhost:5000/api/catalog/items \
  -H "Authorization: Bearer invalid" | jq .
# Expected: 401 Unauthorized

# Invalid input
curl -s -X POST http://localhost:5000/api/catalog/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "threshold": 5.0}' | jq .
# Expected: 400 Bad Request (threshold must be 0.0-1.0)
```

## Monitoring

### Logs

```bash
# Docker logs
docker logs -f catalogai

# Gunicorn access logs are written to stdout
# Error logs are written to stderr
```

### Health Check Endpoints

| Endpoint | Purpose | Check Frequency |
|----------|---------|-----------------|
| `/api/health` | Liveness probe | Every 10s |
| `/api/readiness` | Readiness probe | Every 30s |

### Audit Log

Admin users can view audit events:

```bash
curl -s "http://localhost:5000/api/admin/audit-log?limit=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 503 on `/readiness` | Database unreachable | Check Supabase connection |
| 401 on all requests | Invalid/expired JWT | Re-authenticate with Supabase |
| Empty search results | No embeddings generated | Check Gemini API key |
| Slow searches | Many items, no index | Verify migration 00006 applied |

### Debug Mode

For development debugging:

```bash
FLASK_ENV=development FLASK_DEBUG=1 python run.py
```

## Performance Expectations

| Operation | Expected Latency |
|-----------|------------------|
| Health check | < 10ms |
| Readiness check | < 100ms |
| Semantic search | < 500ms |
| Product enrichment | 2-5s (Gemini API) |
| Batch enrichment (20 items) | 10-15s (parallel) |

## Security Notes

- JWT tokens expire after ~1 hour (Supabase default)
- All endpoints except health checks require authentication
- Row-level security enforces org isolation at database level
- Service role key should never be exposed to clients
- Use HTTPS in production (configure via load balancer)
