# CatalogAI Usage Examples

## Common Workflows

### 1. Search for an Item

**Scenario**: User needs to find a laptop

```bash
curl -X POST http://localhost:5000/api/catalog/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "laptop for software development",
    "limit": 5
  }'
```

**Response**:
```json
{
  "results": [
    {
      "item_id": "...",
      "item_name": "Dell Latitude 7430 Laptop",
      "item_description": "14\" laptop with Intel Core i7, 16GB RAM, 512GB SSD",
      "similarity_score": 0.89
    }
  ]
}
```

---

### 2. Request New Item (When Search Fails)

**Scenario**: User searches but doesn't find what they need

```bash
# Step 1: Search returns no good results
curl -X POST http://localhost:5000/api/catalog/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "standing desk converter"}'

# Returns: No good matches

# Step 2: Request new item
curl -X POST http://localhost:5000/api/catalog/request-new-item \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIVO Standing Desk Converter",
    "description": "Height-adjustable standing desk converter, fits on existing desks",
    "category": "Furniture",
    "justification": "Need for ergonomic workspace setup"
  }'
```

**Response**:
```json
{
  "message": "New item request submitted for review",
  "proposal": {
    "id": "proposal-uuid",
    "status": "pending",
    "proposal_type": "ADD_ITEM"
  },
  "next_steps": "A reviewer will approve or reject your request..."
}
```

---

### 3. Reviewer Approves New Item Request

**Scenario**: Admin reviews and approves the pending proposal

```bash
# Step 1: List pending proposals
curl -X GET "http://localhost:5000/api/proposals?status=pending" \
  -H "Authorization: Bearer <admin-token>"

# Step 2: Approve the proposal
curl -X POST http://localhost:5000/api/proposals/<proposal-id>/approve \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "review_notes": "Approved - good ergonomic addition"
  }'
```

**Result**: Item is automatically added to catalog with embedding generated!

---

### 4. Using the Python SDK

**Scenario**: Programmatic access via catalogai SDK

```python
import catalogai

# Initialize client
client = catalogai.CatalogAIClient(
    base_url="http://localhost:5000",
    auth_token="<your-supabase-jwt>"
)

# Search catalog
results = client.catalog.search("ergonomic mouse", limit=5)
for item in results:
    print(f"- {item['item_name']}: {item['similarity_score']:.2f}")

# Request new item if search fails
if not results or results[0]['similarity_score'] < 0.5:
    proposal = client.catalog.request_new_item(
        name="Logitech MX Vertical Mouse",
        description="Ergonomic vertical mouse for reduced wrist strain",
        category="Electronics",
        justification="Team reported RSI issues"
    )
    print(f"Proposal submitted: {proposal['proposal']['id']}")
```

---

### 5. MCP Integration with Claude

**Scenario**: Using Claude Desktop to interact with catalog

**User asks Claude**:
> "Search my catalog for standing desks. If there aren't any good ones, request a new adjustable standing desk."

**Claude writes and executes**:
```python
import catalogai
import os

client = catalogai.CatalogAIClient(
    base_url=os.getenv("CATALOGAI_API_URL"),
    auth_token=os.getenv("CATALOGAI_AUTH_TOKEN")
)

# Search for standing desks
results = client.catalog.search("standing desk", limit=5)

if not results or results[0]['similarity_score'] < 0.6:
    # No good matches, request new item
    proposal = client.catalog.request_new_item(
        name="Autonomous SmartDesk Pro",
        description="Electric height-adjustable standing desk, 48x30 inches",
        category="Furniture",
        justification="No suitable standing desks in current catalog"
    )
    print(f"✅ Submitted new item request (Proposal ID: {proposal['proposal']['id']})")
    print(f"📝 Status: {proposal['proposal']['status']}")
else:
    print(f"Found {len(results)} standing desks:")
    for item in results:
        print(f"- {item['item_name']} (score: {item['similarity_score']:.2f})")
```

---

### 6. Complete Procurement Workflow

**Full workflow from search to approval**:

```python
import catalogai

client = catalogai.CatalogAIClient(base_url="...", auth_token="...")

# 1. User searches
results = client.catalog.search("wireless keyboard")

# 2. User creates a request
request = client.requests.create(
    search_query="wireless keyboard",
    search_results=results,
    justification="Need new keyboards for dev team"
)

# 3. Reviewer approves request
request = client.requests.review(
    request_id=request['id'],
    status="approved",
    review_notes="Budget approved"
)

# 4. If no suitable item, propose new one
proposal = client.proposals.create(
    proposal_type="ADD_ITEM",
    item_name="Logitech MX Keys",
    item_description="Wireless illuminated keyboard",
    item_category="Electronics",
    request_id=request['id']
)

# 5. Admin approves proposal → item added to catalog!
proposal = client.proposals.approve(
    proposal_id=proposal['id'],
    review_notes="Good choice, approved"
)
```

---

## Common Patterns

### Pattern 1: Search → Request New Item
When search doesn't return good results, immediately request a new item:

```python
results = client.catalog.search(query)
if not results or max(r['similarity_score'] for r in results) < 0.5:
    # No good match, request new item
    client.catalog.request_new_item(...)
```

### Pattern 2: Batch Approval
Admin approves multiple pending proposals:

```python
proposals = client.proposals.list(status="pending")
for p in proposals:
    if should_approve(p):
        client.proposals.approve(p['id'], review_notes="Auto-approved")
```

### Pattern 3: Semantic Search with Fallback
Try semantic search, fall back to listing by category:

```python
results = client.catalog.search(query, threshold=0.4)
if not results:
    # Fallback to category browse
    results = client.catalog.list(status="active", limit=20)
```

---

## API Response Examples

### Successful Search
```json
{
  "results": [
    {
      "item_id": "uuid",
      "item_name": "Dell Latitude 7430",
      "item_description": "Business laptop...",
      "item_category": "Electronics",
      "item_metadata": {"brand": "Dell"},
      "item_status": "active",
      "similarity_score": 0.89
    }
  ]
}
```

### New Item Request
```json
{
  "message": "New item request submitted for review",
  "proposal": {
    "id": "proposal-uuid",
    "org_id": "org-uuid",
    "proposal_type": "ADD_ITEM",
    "proposed_by": "user-uuid",
    "item_name": "...",
    "status": "pending",
    "created_at": "2025-12-26T..."
  },
  "next_steps": "A reviewer will approve or reject your request..."
}
```

### Error Response
```json
{
  "error": "Item name is required"
}
```

---

## Testing the API

### Using curl

```bash
# Health check (no auth required)
curl http://localhost:5000/api/health

# Search (requires auth)
curl -X POST http://localhost:5000/api/catalog/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop", "limit": 5}'

# Request new item
curl -X POST http://localhost:5000/api/catalog/request-new-item \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "description": "Test description",
    "category": "Test"
  }'
```

### Using Python requests

```python
import requests

headers = {"Authorization": f"Bearer {token}"}

# Search
response = requests.post(
    "http://localhost:5000/api/catalog/search",
    headers=headers,
    json={"query": "laptop", "limit": 5}
)
results = response.json()

# Request new item
response = requests.post(
    "http://localhost:5000/api/catalog/request-new-item",
    headers=headers,
    json={
        "name": "New Item",
        "description": "Description here",
        "category": "Electronics"
    }
)
proposal = response.json()
```

---

## Next Steps

See also:
- [README.md](README.md) - Setup guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Implementation details
- [catalogai_mcp/README.md](catalogai_mcp/README.md) - MCP integration
