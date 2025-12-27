# Actual Implementation Patterns

## Discovered Patterns from Code Review

### Service Layer Pattern

All services use consistent function naming and return types:

```python
# CREATE operations
def create_<resource>(org_id, created_by, ...params) -> Dict

# READ operations
def get_<resource>(resource_id) -> Optional[Dict]
def list_<resources>(org_id, filters..., limit=100) -> List[Dict]

# UPDATE operations
def review_<resource>(resource_id, reviewed_by, status, notes) -> Dict
def approve_<resource>(resource_id, reviewed_by, notes) -> Dict
def reject_<resource>(resource_id, reviewed_by, notes) -> Dict
```

### API Endpoint Pattern

APIs wrap list responses in objects, single resources returned directly:

```python
# List endpoints return: {"<resources>": [...]}
GET /api/requests → {"requests": [...]}
GET /api/proposals → {"proposals": [...]}
GET /api/admin/audit-log → {"events": [...]}

# Single resource endpoints return object directly
GET /api/requests/:id → {id, org_id, ...}
POST /api/requests → {id, org_id, ...}
```

### Audit Logging Pattern

```python
log_event(
    org_id=str,
    event_type=str,        # format: 'resource.action' (e.g., 'request.created')
    actor_id=str,          # user performing action
    resource_type=str,     # resource type (e.g., 'request')
    resource_id=str,       # UUID of resource
    metadata=dict          # additional data
)
```

## Actual Implementations

### Request Service

```python
# app/services/request_service.py
def create_request(org_id, created_by, search_query, search_results, justification=None)
def get_request(request_id)
def list_requests(org_id, status=None, created_by=None, limit=100)
def review_request(request_id, reviewed_by, status, review_notes=None)
```

**Audit Events**: `request.created`, `request.approved`, `request.rejected`

### Request API

```python
# app/api/requests.py
POST   /api/requests              → create, returns request object
GET    /api/requests              → list, returns {"requests": [...]}
GET    /api/requests/:id          → get, returns request object
POST   /api/requests/:id/review   → review, returns request object
```

**Request Body for create**:
```json
{
  "search_query": "laptop",
  "search_results": [...],
  "justification": "optional"
}
```

**Request Body for review**:
```json
{
  "status": "approved" | "rejected",
  "review_notes": "optional"
}
```

### Proposal Service

Pattern discovered from grep - need to verify:
- `create_proposal()`
- `get_proposal()`
- `list_proposals()`
- `approve_proposal()`
- `reject_proposal()`

### Audit Service

```python
# app/services/audit_service.py
def log_event(org_id, actor_id, event_type, resource_type, resource_id, metadata=None)
def get_audit_log(org_id, limit=100, event_type=None, resource_type=None, resource_id=None)
```

### Admin API

```python
# app/api/admin.py
GET /api/admin/audit-log → {"events": [...]}
```

## SDK Implementations

### Request Client

```python
# catalogai_sdk/requests.py
def create(search_query, search_results, justification=None)
def get(request_id)
def list(status=None, created_by=None, limit=100)
def review(request_id, status, review_notes=None)
```

**Note**: SDK has `review()` method, NOT separate `approve()`/`reject()`

### Proposal Client

```python
# catalogai_sdk/proposals.py
def create(proposal_type, item_name, item_description, item_category, item_metadata, replacing_item_id, request_id)
def get(proposal_id)
def list(status=None, limit=100)
def approve(proposal_id, review_notes=None)
def reject(proposal_id, review_notes=None)
```

**Note**: SDK has `approve()` and `reject()` methods

### Catalog Client

```python
# catalogai_sdk/catalog.py
def search(query, limit=10, threshold=0.3)
def get(item_id)
def list(status=None, category=None, limit=100)
def request_new_item(name, description, category, metadata, justification)
```

## Key Differences from Tests

1. **Request Service**: Uses `search_query` + `search_results`, NOT `item_name` + `quantity`
2. **Request API**: Has `/review` endpoint, NOT separate `/approve` and `/reject`
3. **Request SDK**: Has `review()` method, NOT `approve()` and `reject()`
4. **Proposal SDK**: Uses `replacing_item_id`, NOT `deprecated_item_id`
5. **Admin API**: Returns `{"events": [...]}`, NOT bare list
6. **List APIs**: All wrap in object like `{"requests": [...]}`, NOT bare lists

## Test Fixes Needed

### High Priority
1. Fix request service tests - use correct create() params
2. Fix request SDK tests - use review() instead of approve/reject
3. Fix proposal SDK tests - use replacing_item_id
4. Fix admin API tests - expect {"events": [...]}
5. Fix all API list tests - expect wrapped responses

### Medium Priority
6. Fix service audit logging mocks - use actor_id not user_id
7. Fix all mock response structures to match Supabase patterns
8. Update service tests to match actual function signatures

### Pattern for List Response Tests

```python
# WRONG
response = client.get('/api/requests')
data = json.loads(response.data)
assert len(data) == 2  # ❌ data is object, not list

# RIGHT
response = client.get('/api/requests')
data = json.loads(response.data)
assert len(data["requests"]) == 2  # ✅ correct
```

### Pattern for SDK List Tests

```python
# SDK unwraps for convenience
response.json.return_value = {"requests": [...]}
...
return response.json()["requests"]  # SDK returns unwrapped list
```
