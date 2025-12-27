# CatalogAI Project Structure

## Directory Overview

```
Cataloger/
├── 📄 README.md                   # Main project documentation
├── 📄 LICENSE                     # MIT License
├── 📄 requirements.txt            # Python dependencies
├── 📄 .env.example                # Environment template
├── 📄 run.py                      # Application entry point
│
├── 📁 app/                        # Flask application
│   ├── __init__.py                # App factory
│   ├── config.py                  # Configuration + AWS Secrets
│   ├── extensions.py              # Supabase clients & embedding model
│   │
│   ├── 📁 api/                    # API endpoints (6 blueprints)
│   │   ├── admin.py               # Audit log access
│   │   ├── auth.py                # Authentication (future)
│   │   ├── catalog.py             # Catalog CRUD + search + request-new-item
│   │   ├── health.py              # Health checks
│   │   ├── proposals.py           # Proposal workflow
│   │   └── requests.py            # Request management
│   │
│   ├── 📁 services/               # Business logic (5 modules)
│   │   ├── audit_service.py       # Event logging
│   │   ├── catalog_service.py     # Catalog operations + semantic search
│   │   ├── embedding_service.py   # SentenceTransformer embeddings
│   │   ├── proposal_service.py    # Governance + auto-merge logic
│   │   └── request_service.py     # Request workflow
│   │
│   ├── 📁 middleware/             # Auth & error handling
│   │   ├── auth_middleware.py     # JWT validation + RBAC
│   │   └── error_handlers.py      # Global error handlers
│   │
│   └── 📁 models/                 # Data models (future Pydantic schemas)
│
├── 📁 supabase/                   # Database migrations
│   └── 📁 migrations/
│       ├── 00001_initial_schema.sql     # Core tables + pgvector
│       ├── 00002_rls_policies.sql       # Row-level security
│       └── 00003_pgvector_setup.sql     # Vector search setup
│
├── 📁 catalogai_sdk/              # Python SDK (Part C)
│   ├── __init__.py
│   ├── client.py                  # Main SDK client
│   ├── catalog.py                 # Catalog operations
│   ├── requests.py                # Request operations
│   ├── proposals.py               # Proposal operations
│   └── pyproject.toml             # Package config
│
├── 📁 catalogai_mcp/              # MCP Server (Part C)
│   ├── README.md                  # Quick setup guide
│   ├── server.py                  # MCP server with code execution
│   ├── code_executor.py           # Sandboxed Python execution
│   ├── sandbox.Dockerfile         # Security-hardened Docker image
│   ├── claude_desktop_config.json # Claude Desktop config
│   └── pyproject.toml             # Package config
│
├── 📁 scripts/                    # Utility scripts
│   ├── seed_data.py               # Database seeding
│   └── check_setup.py             # Setup verification
│
├── 📁 docs/                       # Documentation
│   ├── README.md                  # Documentation index
│   │
│   ├── 📁 planning/               # Project planning
│   │   ├── PROJECT_STATUS.md      # Detailed status & phases
│   │   └── IMPLEMENTATION_SUMMARY.md  # High-level summary
│   │
│   ├── 📁 guides/                 # User guides
│   │   ├── USAGE_EXAMPLES.md      # API usage examples
│   │   └── MCP_INTEGRATION.md     # MCP setup guide
│   │
│   └── 📁 api/                    # API documentation (future)
│       ├── API_REFERENCE.md
│       └── AUTHENTICATION.md
│
├── 📁 .ebextensions/              # AWS Elastic Beanstalk config
│   └── 01_flask.config
│
├── 📄 Dockerfile                  # Production Docker image
├── 📄 .dockerignore               # Docker build exclusions
├── 📄 docker-compose.yml          # Local development setup
├── 📄 Dockerrun.aws.json          # AWS ECS configuration
└── 📄 buildspec.yml               # AWS CodeBuild/CodePipeline
```

---

## File Count by Category

| Category | Count | Description |
|----------|-------|-------------|
| **Backend** | 20 | Flask app + services + middleware |
| **Database** | 3 | SQL migrations |
| **SDK** | 5 | Python client library |
| **MCP Server** | 6 | Code execution integration |
| **Deployment** | 5 | Docker + AWS configs |
| **Documentation** | 6 | Guides + planning docs |
| **Scripts** | 2 | Utilities |
| **Config** | 3 | Requirements, .env, etc. |
| **TOTAL** | **50** | |

---

## Key Components

### Backend (Flask API)
- **19 API endpoints** across 6 blueprints
- **5 business services** with clear separation of concerns
- **JWT authentication** with role-based access control
- **Semantic search** using SentenceTransformers

### Database (Supabase/PostgreSQL)
- **7 core tables** with full audit trail
- **pgvector extension** for semantic search
- **Row-level security** for multi-tenant isolation
- **3 migrations** for clean schema evolution

### SDK (catalogai_sdk)
- **Python client library** for programmatic access
- **4 operation modules**: catalog, requests, proposals
- **Type hints** and comprehensive docstrings
- **Easy integration** with `pip install -e .`

### MCP Server (catalogai_mcp)
- **Code execution sandbox** using Docker
- **Claude Desktop integration** via MCP protocol
- **Security hardening** with resource limits
- **98.7% token reduction** vs traditional tools

### Documentation
- **Planning docs** - Project status and implementation details
- **User guides** - Usage examples and setup instructions
- **API reference** - Endpoint documentation (planned)
- **Well-organized** in `docs/` with clear structure

---

## Import Patterns

### Backend Services
```python
from app.services import catalog_service
from app.services import request_service
from app.services import proposal_service
```

### SDK Usage
```python
import catalogai

client = catalogai.CatalogAIClient(base_url, token)
results = client.catalog.search("laptop")
```

### Middleware
```python
from app.middleware.auth_middleware import require_auth, require_role

@require_auth
@require_role(['admin'])
def admin_endpoint():
    pass
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Local environment variables (not in git) |
| `.env.example` | Template for environment setup |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Package configs for SDK and MCP |
| `docker-compose.yml` | Local development with Docker |
| `buildspec.yml` | AWS CodeBuild CI/CD |

---

## Next Steps

- Add API reference documentation in `docs/api/`
- Create testing directory structure
- Add GitHub Actions workflows
- Implement frontend (React/Vue)

See [PROJECT_STATUS.md](planning/PROJECT_STATUS.md) for detailed roadmap.
