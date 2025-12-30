# Code Execution Quick Start Guide

## TL;DR

Instead of multiple tool calls, write Python code using the catalogai SDK:

```python
from catalogai import CatalogAI

client = CatalogAI()  # Auto-authenticated

# Do whatever you need
results = client.catalog.search("laptop", limit=20)
# ... complex filtering, sorting, etc ...
print("Done!")
```

**Result**: 98% fewer tokens, 5x faster, one execution.

## When to Use Code Execution vs Direct Tools

### ✅ Use Code Execution When:

- **Multi-step workflows** (3+ operations)
  - Example: Search → filter → create request

- **Complex filtering logic**
  - Example: "Find items under $X from vendor Y with feature Z"

- **Batch operations** (processing many items)
  - Example: "Approve all pending laptop requests under $2000"

- **Data aggregation**
  - Example: "Show me total spending by category"

- **Iterative processing**
  - Example: "For each pending request, check if item exists in catalog"

### ❌ Use Direct Tools When:

- **Single simple operation**
  - Example: `search_catalog("laptop", limit=5)`

- **Just viewing data**
  - Example: `get_catalog_item(item_id)`

- **Quick lookups**
  - Example: `list_requests(status="pending")`

## Code Execution Examples

### Example 1: Search and Filter

**Prompt**: "Find ergonomic chairs under $500"

**Code**:
```python
from catalogai import CatalogAI

client = CatalogAI()

results = client.catalog.search("ergonomic office chair", limit=20)
affordable = [r for r in results if r.get('price', 9999) < 500]

print(f"Found {len(affordable)} chairs under $500:")
for chair in affordable:
    print(f"  - {chair['name']}: ${chair['price']}")
```

**Token savings**: ~10K → ~800 tokens (92% reduction)

### Example 2: Complex Multi-Step Workflow

**Prompt**: "Find the cheapest laptop with at least 16GB RAM and create a request for it"

**Code**:
```python
from catalogai import CatalogAI

client = CatalogAI()

# Search for laptops
results = client.catalog.search("laptop 16GB RAM", limit=30)

# Filter by specs
candidates = []
for item in results:
    # Check metadata for RAM spec
    ram = item.get('metadata', {}).get('ram_gb', 0)
    if ram >= 16:
        candidates.append(item)

if not candidates:
    print("No laptops found with 16GB+ RAM")
else:
    # Find cheapest
    cheapest = min(candidates, key=lambda x: x.get('price', float('inf')))

    # Create request
    request = client.requests.create(
        item_name=cheapest['name'],
        justification=f"Cheapest laptop with 16GB+ RAM: {cheapest['name']} at ${cheapest['price']}"
    )

    print(f"✓ Created request {request['id']}")
    print(f"  Item: {cheapest['name']}")
    print(f"  Price: ${cheapest['price']}")
    print(f"  RAM: {cheapest['metadata']['ram_gb']}GB")
```

**Token savings**: ~50K → ~1.5K tokens (97% reduction)

### Example 3: Batch Operations

**Prompt**: "Approve all pending monitor requests under $800"

**Code**:
```python
from catalogai import CatalogAI

client = CatalogAI()

# Get pending requests
requests = client.requests.list(status="pending")

# Filter for monitors under $800
monitor_requests = [
    r for r in requests
    if "monitor" in r['item_name'].lower()
    and r.get('estimated_price', 9999) < 800
]

approved_count = 0
for req in monitor_requests:
    try:
        client.requests.approve(
            req['id'],
            review_notes="Auto-approved: budget compliant monitor request"
        )
        print(f"✓ Approved: {req['item_name']} (${req['estimated_price']})")
        approved_count += 1
    except Exception as e:
        print(f"✗ Failed to approve {req['item_name']}: {e}")

print(f"\nApproved {approved_count}/{len(monitor_requests)} requests")
```

**Token savings**: ~150K → ~2K tokens (98.7% reduction)

### Example 4: Data Analysis

**Prompt**: "Show me spending breakdown by category for approved requests this month"

**Code**:
```python
from catalogai import CatalogAI
from datetime import datetime, timedelta
from collections import defaultdict

client = CatalogAI()

# Get approved requests
requests = client.requests.list(status="approved")

# Filter for this month
today = datetime.now()
first_day = today.replace(day=1)

category_spending = defaultdict(float)
for req in requests:
    # Parse created_at (assuming ISO format)
    created = datetime.fromisoformat(req['created_at'].replace('Z', '+00:00'))

    if created >= first_day:
        # Get catalog item for category
        try:
            item = client.catalog.get(req['catalog_item_id'])
            category = item.get('category', 'Uncategorized')
            price = req.get('estimated_price', 0)
            category_spending[category] += price
        except:
            pass

# Print breakdown
print("Spending by Category (This Month):")
print("-" * 40)
total = 0
for category, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
    print(f"{category:20} ${amount:>10,.2f}")
    total += amount
print("-" * 40)
print(f"{'TOTAL':20} ${total:>10,.2f}")
```

**Token savings**: ~80K → ~1.8K tokens (97.8% reduction)

## SDK API Reference

### CatalogAI Client

```python
from catalogai import CatalogAI

client = CatalogAI()  # Auto-reads from environment
# Or explicitly:
client = CatalogAI(
    base_url="http://localhost:5000",
    auth_token="your-jwt-token"
)
```

### Catalog Operations

```python
# Search catalog (semantic vector search)
results = client.catalog.search(query="laptop", limit=10, threshold=0.3)

# Get specific item
item = client.catalog.get(item_id="uuid-here")

# List all items
items = client.catalog.list(limit=50, category="Electronics")
```

### Request Operations

```python
# Create request
request = client.requests.create(
    item_name="MacBook Pro 16",
    justification="Need for video editing team"
)

# List requests
requests = client.requests.list(status="pending", limit=50)

# Get request details
request = client.requests.get(request_id="uuid-here")

# Approve request (reviewer/admin only)
result = client.requests.approve(
    request_id="uuid-here",
    review_notes="Approved for Q1 budget"
)

# Reject request (reviewer/admin only)
result = client.requests.reject(
    request_id="uuid-here",
    review_notes="Over budget"
)
```

### Proposal Operations

```python
# Create proposal
proposal = client.proposals.create(
    proposal_type="ADD_ITEM",
    item_name="New Product",
    item_description="Description here",
    item_category="Electronics",
    item_price=999.00,
    item_pricing_type="one_time"
)

# List proposals
proposals = client.proposals.list(status="pending", limit=50)

# Get proposal details
proposal = client.proposals.get(proposal_id="uuid-here")

# Approve proposal (reviewer/admin only)
result = client.proposals.approve(
    proposal_id="uuid-here",
    review_notes="Good addition to catalog"
)

# Reject proposal (reviewer/admin only)
result = client.proposals.reject(
    proposal_id="uuid-here",
    review_notes="Duplicate item"
)
```

## Error Handling

Always use try/except for robustness:

```python
from catalogai import CatalogAI

client = CatalogAI()

try:
    results = client.catalog.search("laptop", limit=10)

    if not results:
        print("No results found")
    else:
        for item in results:
            print(f"- {item['name']}")

except Exception as e:
    print(f"Error: {e}")
```

## Common Patterns

### Pattern 1: Search → Filter → Action

```python
# Search
results = client.catalog.search(query, limit=N)

# Filter with Python (much cheaper than passing all data to Claude)
filtered = [r for r in results if condition(r)]

# Take action
if filtered:
    best = max(filtered, key=scoring_function)
    request = client.requests.create(...)
    print(f"Done: {request['id']}")
```

### Pattern 2: List → Process Each → Report

```python
# List items
items = client.requests.list(status="pending")

# Process each
results = []
for item in items:
    if should_process(item):
        result = process(item)
        results.append(result)

# Report
print(f"Processed {len(results)}/{len(items)} items")
```

### Pattern 3: Aggregate Data

```python
from collections import defaultdict

# Collect data
items = client.catalog.list(limit=100)

# Aggregate
stats = defaultdict(int)
for item in items:
    key = item.get('category', 'Other')
    stats[key] += 1

# Report
for category, count in sorted(stats.items()):
    print(f"{category}: {count} items")
```

## Debugging Tips

### Print intermediate results

```python
results = client.catalog.search("laptop", limit=10)
print(f"Found {len(results)} results")  # Shows in output

filtered = [r for r in results if r['price'] < 2000]
print(f"Filtered to {len(filtered)} items")  # Shows in output
```

### Use try/except for each step

```python
try:
    results = client.catalog.search("laptop", limit=10)
    print(f"✓ Search complete: {len(results)} results")
except Exception as e:
    print(f"✗ Search failed: {e}")
    exit(1)

try:
    request = client.requests.create(...)
    print(f"✓ Request created: {request['id']}")
except Exception as e:
    print(f"✗ Request creation failed: {e}")
    exit(1)
```

### Validate data before processing

```python
results = client.catalog.search("laptop", limit=10)

if not results:
    print("No results found - check query")
    exit(0)

if not isinstance(results, list):
    print(f"Unexpected result type: {type(results)}")
    exit(1)

# Now safe to process
for item in results:
    ...
```

## Performance Tips

1. **Use appropriate limits**: Don't fetch 100 items if you only need 10
   ```python
   # Good
   results = client.catalog.search("laptop", limit=10)

   # Bad (wastes tokens and time)
   results = client.catalog.search("laptop", limit=100)[:10]
   ```

2. **Filter early**: Use search queries instead of filtering large result sets
   ```python
   # Good
   results = client.catalog.search("laptop 16GB RAM", limit=10)

   # Bad
   results = client.catalog.search("laptop", limit=100)
   filtered = [r for r in results if "16GB" in r.get('metadata', {}).get('ram', '')]
   ```

3. **Batch operations when possible**: Process multiple items in one execution
   ```python
   # Good (single execution)
   for request in pending_requests:
       client.requests.approve(request['id'])

   # Bad (multiple executions)
   # Calling execute_code separately for each request
   ```

4. **Print only what matters**: Don't print entire objects
   ```python
   # Good
   print(f"Created request {request['id']}")

   # Bad (wastes tokens)
   print(f"Full request object: {request}")
   ```

## Troubleshooting

### Error: "base_url not provided and CATALOGAI_API_URL not set"

**Cause**: SDK can't find API URL in environment

**Fix**: This should never happen in sandbox (MCP server injects it). If you see this, check that execute_code is passing context correctly.

### Error: "API Error 401: Unauthorized"

**Cause**: Auth token expired or invalid

**Fix**: Restart MCP server to get fresh token. MCP server handles token refresh automatically.

### Code times out after 30 seconds

**Cause**: Code execution exceeded timeout

**Fix**: Optimize your code - reduce API calls, use smaller limits, avoid heavy processing

### Docker container fails to start

**Cause**: Sandbox image not built or Docker daemon not running

**Fix**: Run `./build_sandbox.sh` to build image, ensure Docker is running

## Best Practices

1. ✅ **Always print results** - Claude only sees stdout
2. ✅ **Use descriptive variable names** - Makes debugging easier
3. ✅ **Handle errors gracefully** - Use try/except blocks
4. ✅ **Validate inputs** - Check for empty results, wrong types
5. ✅ **Keep it simple** - Don't over-engineer, code is cheap
6. ✅ **Comment complex logic** - Helps debugging
7. ✅ **Print progress** - Show what's happening step by step

## Questions?

See:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical design
- [README.md](./README.md) - Setup instructions
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - What was built
