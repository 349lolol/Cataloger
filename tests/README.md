# CatalogAI Test Suite

Comprehensive unit tests for Parts A (MVP Core Platform) and C (MCP Integration).

## Test Structure

```
tests/
├── conftest.py                     # pytest configuration & fixtures
└── unit/                           # Unit tests
    ├── __init__.py
    │
    ├── Part A - Backend Services
    │   ├── test_embedding_service.py    # Embedding generation & similarity
    │   ├── test_catalog_service.py      # Catalog CRUD & semantic search
    │   ├── test_request_service.py      # Request workflow
    │   ├── test_proposal_service.py     # Proposal governance & auto-merge
    │   └── test_audit_service.py        # Event logging
    │
    ├── Part A - API Endpoints
    │   ├── test_api_catalog.py          # Catalog endpoints + request-new-item
    │   ├── test_api_requests.py         # Request endpoints
    │   ├── test_api_proposals.py        # Proposal endpoints
    │   ├── test_api_admin.py            # Admin audit log access
    │   └── test_api_health.py           # Health & readiness checks
    │
    └── Part C - SDK & MCP
        ├── test_sdk_client.py           # Main SDK client
        ├── test_sdk_catalog.py          # SDK catalog operations
        ├── test_sdk_requests.py         # SDK request operations
        ├── test_sdk_proposals.py        # SDK proposal operations
        └── test_mcp_executor.py         # MCP code executor sandbox
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Files
```bash
# Backend services
pytest tests/unit/test_catalog_service.py
pytest tests/unit/test_proposal_service.py

# API endpoints
pytest tests/unit/test_api_catalog.py
pytest tests/unit/test_api_proposals.py

# SDK & MCP (Part C)
pytest tests/unit/test_sdk_catalog.py
pytest tests/unit/test_mcp_executor.py
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov=catalogai_sdk --cov=catalogai_mcp --cov-report=html
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

## Test Coverage

### Part A - Backend Services (5 modules)

**test_embedding_service.py** - 6 tests
- ✓ Text encoding generates 384-dim vectors
- ✓ Catalog item encoding with name/description/category
- ✓ Query encoding
- ✓ Similarity calculation (cosine similarity)
- ✓ Batch encoding
- ✓ Model caching

**test_catalog_service.py** - 7 tests
- ✓ Semantic search with pgvector
- ✓ Search with org filtering
- ✓ Get item by ID
- ✓ List items with filters
- ✓ Create item with embedding generation
- ✓ Deprecate item
- ✓ Error handling

**test_request_service.py** - 6 tests
- ✓ Create request
- ✓ Get request by ID
- ✓ List requests with status filter
- ✓ Approve request
- ✓ Reject request
- ✓ Audit logging on state changes

**test_proposal_service.py** - 8 tests
- ✓ Create ADD_ITEM proposal
- ✓ Create REPLACE_ITEM proposal
- ✓ Create DEPRECATE_ITEM proposal
- ✓ Get proposal by ID
- ✓ Approve proposal with auto-merge
- ✓ Reject proposal
- ✓ List proposals with filters
- ✓ Merge logic for each proposal type

**test_audit_service.py** - 6 tests
- ✓ Log event with details
- ✓ Get audit logs for org
- ✓ Filter by event type
- ✓ Filter by resource type/ID
- ✓ Handle missing details
- ✓ Pagination with limit

### Part A - API Endpoints (5 blueprints)

**test_api_catalog.py** - 8 tests
- ✓ Search catalog items
- ✓ Search with filters (category, status)
- ✓ Get item by ID
- ✓ List items
- ✓ **Request new item endpoint** (user-requested feature)
- ✓ Authentication required
- ✓ Org isolation (RLS)
- ✓ Error handling

**test_api_requests.py** - 7 tests
- ✓ Create request
- ✓ Missing required fields validation
- ✓ List requests
- ✓ Get request by ID
- ✓ Approve request (admin/reviewer only)
- ✓ Reject request (admin/reviewer only)
- ✓ RBAC enforcement

**test_api_proposals.py** - 10 tests
- ✓ Create ADD_ITEM proposal
- ✓ Create REPLACE_ITEM proposal
- ✓ Create DEPRECATE_ITEM proposal
- ✓ Missing proposal_type validation
- ✓ List proposals
- ✓ Filter by status
- ✓ Get proposal by ID
- ✓ Approve proposal (admin/reviewer only)
- ✓ Reject proposal (admin/reviewer only)
- ✓ RBAC enforcement

**test_api_admin.py** - 6 tests
- ✓ Get audit logs (admin only)
- ✓ Filter by event type
- ✓ Filter by resource type/ID
- ✓ Default limit applied
- ✓ Requester forbidden
- ✓ Reviewer forbidden

**test_api_health.py** - 2 tests
- ✓ Health check endpoint
- ✓ Readiness check endpoint

### Part C - SDK (4 modules)

**test_sdk_client.py** - 4 tests
- ✓ Client initialization with base_url and auth_token
- ✓ Catalog property returns CatalogClient
- ✓ Requests property returns RequestClient
- ✓ Proposals property returns ProposalClient
- ✓ Context manager support

**test_sdk_catalog.py** - 6 tests
- ✓ Search catalog
- ✓ Search error handling
- ✓ Get item by ID
- ✓ List items with filters
- ✓ **Request new item** (SDK method for user-requested feature)
- ✓ HTTP error handling

**test_sdk_requests.py** - 8 tests
- ✓ Create request
- ✓ Create with metadata
- ✓ Get request by ID
- ✓ List requests
- ✓ Filter by status
- ✓ Approve request
- ✓ Reject request
- ✓ Error handling

**test_sdk_proposals.py** - 12 tests
- ✓ Create ADD_ITEM proposal
- ✓ Create REPLACE_ITEM proposal
- ✓ Create DEPRECATE_ITEM proposal
- ✓ Create with metadata
- ✓ Get proposal by ID
- ✓ List proposals
- ✓ Filter by status
- ✓ Filter by proposal_type
- ✓ Approve proposal
- ✓ Reject proposal
- ✓ Optional review notes
- ✓ Error handling

### Part C - MCP Code Executor

**test_mcp_executor.py** - 11 tests
- ✓ Executor initialization
- ✓ Execute simple Python code
- ✓ Execute code with CatalogAI SDK
- ✓ Timeout enforcement (10s limit)
- ✓ Resource limits (512MB RAM, 50% CPU)
- ✓ Network isolation (bridge mode)
- ✓ Error handling with traceback
- ✓ Container cleanup
- ✓ Allowed imports (standard library)
- ✓ Context validation
- ✓ Temporary file creation

## Test Statistics

| Category | Files | Tests | Coverage |
|----------|-------|-------|----------|
| **Backend Services** | 5 | 33 | Part A |
| **API Endpoints** | 5 | 33 | Part A |
| **Python SDK** | 4 | 30 | Part C |
| **MCP Executor** | 1 | 11 | Part C |
| **Total** | **15** | **107** | **A + C** |

## Fixtures (conftest.py)

Shared fixtures for all tests:

- `app` - Flask app instance with testing config
- `client` - Flask test client for API endpoint tests
- `auth_headers` - Authorization headers with Bearer token
- `mock_user_token` - Mock JWT token for testing
- `mock_user` - Mock user data
- `mock_org_id` - Mock organization ID
- `sample_catalog_item` - Sample catalog item data
- `sample_request` - Sample request data
- `sample_proposal` - Sample proposal data

## Mocking Strategy

All tests use mocks to avoid external dependencies:

- **Supabase calls** - Mocked with `unittest.mock.Mock`
- **Embedding model** - Mocked to avoid loading actual model
- **Docker containers** - Mocked for MCP executor tests
- **JWT verification** - Mocked for auth middleware
- **HTTP requests** - Mocked for SDK tests

## Key Testing Patterns

### 1. Service Layer Tests
```python
@patch('app.services.catalog_service.get_supabase_client')
def test_search_items(mock_supabase_getter):
    # Arrange: Setup mock responses
    # Act: Call service method
    # Assert: Verify results and mock calls
```

### 2. API Endpoint Tests
```python
@patch('app.middleware.auth_middleware.verify_jwt_token')
@patch('app.api.catalog.catalog_service')
def test_search_endpoint(mock_service, mock_jwt, client):
    # Arrange: Setup auth and service mocks
    # Act: Make HTTP request via test client
    # Assert: Verify response status and data
```

### 3. SDK Tests
```python
def test_sdk_method():
    mock_client = Mock()
    mock_response = Mock()
    # Arrange: Setup mock HTTP client
    # Act: Call SDK method
    # Assert: Verify HTTP call and result
```

### 4. MCP Executor Tests
```python
def test_executor(executor):
    mock_container = Mock()
    # Arrange: Setup Docker container mock
    # Act: Execute code in sandbox
    # Assert: Verify resource limits and output
```

## RBAC Testing

All API endpoint tests verify role-based access control:

- **Requester role** - Can create requests/proposals, view own items
- **Reviewer role** - Can approve/reject requests and proposals
- **Admin role** - Full access including audit logs
- **Tests verify** - 403 Forbidden when insufficient permissions

## Org Isolation Testing

Tests verify multi-tenant isolation:

- All service calls include `org_id` parameter
- API endpoints use `g.org_id` from auth middleware
- Mock assertions verify org filtering

## Error Handling

Tests cover error scenarios:

- Missing required fields → 400 Bad Request
- Unauthorized access → 401 Unauthorized
- Insufficient permissions → 403 Forbidden
- Resource not found → 404 Not Found
- HTTP errors from Supabase → Propagated correctly
- Docker execution errors → Graceful handling

## Next Steps

1. **Add integration tests** - End-to-end workflow tests with real Supabase
2. **Add performance tests** - Vector search performance benchmarks
3. **Add security tests** - SQL injection, XSS, CSRF prevention
4. **Increase coverage** - Aim for 90%+ code coverage
5. **Add E2E tests** - Full user workflows from SDK to database

## Running in CI/CD

Recommended GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    pytest tests/ --cov=app --cov=catalogai_sdk --cov=catalogai_mcp
    pytest tests/ --junitxml=test-results.xml
```
