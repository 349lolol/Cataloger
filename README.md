# CatalogAI - AI-Native Procurement Catalog System

A multi-tenant procurement catalog system with semantic search, proposal-based governance, and org-scoped isolation.

> 📚 **Full Documentation**: See [docs/](docs/) for detailed guides, planning docs, and API reference

## Features

- **Semantic Search**: Vector embeddings for intelligent catalog matching using Google Gemini
- **Multi-Tenant Architecture**: Organization-level RLS (Row-Level Security) isolation in PostgreSQL
- **Approval Workflows**: Governance system for catalog changes via proposals
- **Role-Based Access Control**: Support for requester, reviewer, and admin roles
- **Audit Logging**: Immutable event log for compliance and debugging
- **AI Integration**: MCP (Model Context Protocol) server for Claude Desktop integration

## Tech Stack

- **Backend**: Flask 3.0 (Python)
- **Database**: Supabase (PostgreSQL + Auth + pgvector)
- **AI/ML**: Google Gemini (text-embedding-004, gemini-1.5-flash)
- **Deployment**: Docker + AWS ECS Fargate

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier works)
- Virtual environment tool (venv or conda)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd Cataloger
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `FLASK_SECRET_KEY`: Random secret for session management
- `GEMINI_API_KEY`: Google Gemini API key for product enrichment

### 3. Set Up Database

1. Create a Supabase project at https://supabase.com
2. Run migrations in Supabase SQL Editor (in order):
   - Execute `supabase/migrations/00001_initial_schema.sql`
   - Execute `supabase/migrations/00002_rls_policies.sql`
   - Execute `supabase/migrations/00003_pgvector_setup.sql`
   - Execute `supabase/migrations/00004_add_product_fields.sql`
   - Execute `supabase/migrations/00005_fix_proposal_rls.sql`
   - Execute `supabase/migrations/00006_update_embedding_dimension.sql` (required for Gemini embeddings)

### 4. Seed Data

```bash
python scripts/seed_data.py
```

This creates:
- 1 organization ("Acme Corporation")
- 10 test users (3 admins, 3 reviewers, 4 requesters)
- 30 catalog items (20 hardware + 10 SaaS)
- Sample requests

**Save the credentials** printed by the script - you'll need them for MCP configuration.

### 5. Run Development Server

```bash
python run.py
```

The API will be available at http://localhost:5000

## API Endpoints

### Health

- `GET /api/health` - Health check
- `GET /api/readiness` - Readiness check

### Catalog

- `POST /api/catalog/search` - Semantic search for items
- `GET /api/catalog/items` - List catalog items
- `GET /api/catalog/items/:id` - Get single item
- `POST /api/catalog/items` - Create item (admin only)
- `POST /api/catalog/request-new-item` - Request new item (creates proposal for review)

### Requests

- `POST /api/requests` - Create procurement request
- `GET /api/requests` - List requests
- `GET /api/requests/:id` - Get request details
- `POST /api/requests/:id/review` - Approve/reject request (reviewer/admin)

### Proposals

- `POST /api/proposals` - Create proposal for catalog changes
- `GET /api/proposals` - List proposals (review queue)
- `GET /api/proposals/:id` - Get proposal details
- `POST /api/proposals/:id/approve` - Approve proposal (reviewer/admin)
- `POST /api/proposals/:id/reject` - Reject proposal (reviewer/admin)

### Admin

- `GET /api/admin/audit-log` - View audit events (admin only)

## Authentication

All endpoints (except `/health` and `/readiness`) require authentication via Supabase JWT.

Include the auth token in requests:
```
Authorization: Bearer <supabase-jwt-token>
```

## Docker Deployment

### Local Development with Docker

```bash
docker-compose up
```

### Build Production Image

```bash
docker build -t catalogai:latest .
docker run -p 5000:5000 --env-file .env catalogai:latest
```

## AWS Deployment

See [docs/aws-deployment.md](docs/aws-deployment.md) for detailed AWS ECS Fargate deployment instructions.

Quick deploy with AWS Elastic Beanstalk:
```bash
eb init -p docker catalogai
eb create catalogai-prod --elb-type application
eb deploy
```

## MCP Integration

The MCP (Model Context Protocol) server provides **17 direct tools** for agentic procurement workflows through Claude Desktop.

**Features**:
- Semantic catalog search with vector embeddings
- Complete procurement request workflow
- Proposal creation and approval
- AI product enrichment via Gemini 3.0
- Audit logging and system maintenance

**Setup**:
```bash
cd catalogai_mcp
pip install -e .
```

Configure Claude Desktop with your Supabase credentials and user account from the seeding script.

See [catalogai_mcp/README.md](catalogai_mcp/README.md) for complete setup and usage instructions.

## Project Structure

```
Cataloger/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration with AWS Secrets Manager support
│   ├── extensions.py         # Supabase clients and embedding model
│   ├── api/                  # API blueprints
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── health.py
│   │   ├── proposals.py
│   │   └── requests.py
│   ├── middleware/           # Auth and error handling
│   │   ├── auth_middleware.py
│   │   └── error_handlers.py
│   └── services/             # Business logic
│       ├── audit_service.py
│       ├── catalog_service.py
│       ├── embedding_service.py
│       ├── proposal_service.py
│       └── request_service.py
├── supabase/
│   └── migrations/           # Database schema and RLS policies
├── scripts/
│   └── seed_data.py          # Database seeding script
├── catalogai_mcp/            # MCP server (Part C)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run.py                    # Application entry point
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
black app/
flake8 app/
```

## Security

- All database access enforced via RLS policies
- Service role key never exposed to frontend
- JWT validation on all authenticated endpoints
- Audit logging for compliance

## Documentation

### Quick Links
- **[Usage Examples](docs/guides/USAGE_EXAMPLES.md)** - API usage patterns and workflows
- **[MCP Integration](docs/guides/MCP_INTEGRATION.md)** - Claude Desktop setup guide
- **[Project Status](docs/planning/PROJECT_STATUS.md)** - Implementation details and roadmap
- **[Implementation Summary](docs/planning/IMPLEMENTATION_SUMMARY.md)** - High-level overview

### Documentation Structure
```
docs/
├── README.md                      # Documentation index
├── planning/                      # Project planning & status
│   ├── PROJECT_STATUS.md
│   └── IMPLEMENTATION_SUMMARY.md
├── guides/                        # User guides
│   ├── USAGE_EXAMPLES.md
│   └── MCP_INTEGRATION.md
└── api/                           # API reference (future)
```

See [docs/README.md](docs/README.md) for the full documentation index.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.
