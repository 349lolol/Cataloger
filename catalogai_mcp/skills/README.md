# CatalogAI Skills

## Usage
```python
from skills import catalog, reqs, proposals
import json

# Chain operations without round-tripping through LLM
pending = reqs.list_all(status="pending")
for req in pending:
    matches = catalog.search(req["search_query"])
    print(json.dumps({"request": req["id"], "matches": len(matches)}))
```

## Available Functions

### catalog
- `search(query, limit=10, threshold=0.3)` - Semantic search
- `get(item_id)` - Get item by ID
- `list_items(limit=50, status="active")` - List catalog items
- `request_new(name, justification, use_ai=True)` - Request new item

### reqs (requests)
- `get(request_id)` - Get request details
- `list_all(status=None, limit=50)` - List requests (status: pending/approved/rejected)
- `review(request_id, status, notes=None)` - Approve/reject request

### proposals
- `get(proposal_id)` - Get proposal details
- `list_all(status=None, limit=50)` - List proposals
- `create(proposal_type, item_name, item_description, item_category, **kwargs)` - Create proposal
- `approve(proposal_id, notes=None)` - Approve and merge
- `reject(proposal_id, notes=None)` - Reject proposal

## Rules
- Output JSON only via `print(json.dumps(result))`
- Chain operations in code - don't return intermediate results
- Keep code minimal
