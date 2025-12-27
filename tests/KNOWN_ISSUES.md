# Known Test Issues and Fixes

## Summary

The test suite was written with some assumptions about implementation that need to be aligned. Below are the main mismatches and how to fix them.

## Fixed Issues ✅

1. **Environment Configuration** - Added `setup_test_env()` fixture
2. **Embedding Service Mocking** - All tests now properly mock `get_embedding_model()`
3. **Audit Service API** - Updated to use correct function names and parameters

## Remaining Issues by Category

### 1. SDK Tests - Parameter Mismatches

#### Request Client Tests
**File**: `tests/unit/test_sdk_requests.py`
**Issue**: Tests assume different `create()` parameters

**Actual SDK API**:
```python
def create(self, search_query: str, search_results: list, justification: str = None)
```

**Test expects**:
```python
client.create(item_name="Laptop", quantity=1, urgency="normal", justification="...")
```

**Fix**: Update test_sdk_requests.py to match actual SDK signature

#### Request Client - No approve/reject methods
**Actual SDK**: Has `review(request_id, status, review_notes)` method
**Tests expect**: Separate `approve()` and `reject()` methods

**Fix Options**:
1. Update tests to use `review()` method
2. Add convenience methods `approve()` and `reject()` to SDK that wrap `review()`

#### Proposal Client Tests
**File**: `tests/unit/test_sdk_proposals.py`
**Issue**: Tests pass `deprecated_item_id` but SDK expects `replacing_item_id`

**Actual SDK**:
```python
def create(self, proposal_type, item_name=None, ..., replacing_item_id=None)
```

**Tests use**:
```python
client.create(proposal_type="REPLACE_ITEM", deprecated_item_id="item-old", ...)
```

**Fix**: Update tests to use `replacing_item_id`

### 2. Service Tests - Audit Logging Calls

#### Request & Proposal Services
**Issue**: These services likely call audit_service.log_event() but may use old parameter names

**Need to verify these files use correct audit API**:
- `app/services/request_service.py`
- `app/services/proposal_service.py`
- `app/services/catalog_service.py`

**Correct audit_service.log_event() signature**:
```python
log_event(
    org_id: str,
    actor_id: str,  # NOT user_id
    event_type: str,
    resource_type: str,
    resource_id: str,
    metadata: Optional[Dict] = None  # NOT details
)
```

### 3. Admin API Tests
**File**: `tests/unit/test_api_admin.py`
**Issue**: Tests call `audit_service.get_audit_logs()` (plural)

**Actual function**: `get_audit_log()` (singular)

**Fix**: Update `app/api/admin.py` to use correct function name

### 4. API Response Structure Mismatches

#### Lists wrapped in objects
**Issue**: Tests expect `response.json()` to return lists directly, but actual API may wrap them

**Example**:
```python
# Test expects:
assert len(results) == 2

# But API returns:
{"items": [...]}  or  {"proposals": [...]}
```

**Affected tests**:
- test_api_catalog.py
- test_api_requests.py
- test_api_proposals.py

**Fix**: Check actual API response structure and update test assertions

### 5. MCP Executor Tests
**File**: `tests/unit/test_mcp_executor.py`
**Issue**: Tests expect specific result structure

**Tests expect**:
```python
{
    "success": bool,
    "output": str,
    "exit_code": int,
    "error": str  # optional
}
```

**Fix**: Verify `catalogai_mcp/code_executor.py` returns this structure, or update tests

## Recommended Fix Order

### Phase 1: Quick Wins (30 min)
1. Fix admin API `get_audit_logs` → `get_audit_log`
2. Update SDK request tests to use correct `create()` parameters
3. Update SDK proposal tests to use `replacing_item_id`

### Phase 2: SDK Alignment (45 min)
4. Add `approve()` and `reject()` convenience methods to RequestClient
5. Update all SDK tests to match actual method signatures
6. Fix SDK test response structure expectations

### Phase 3: Service Tests (30 min)
7. Verify audit logging calls in all services use correct parameters
8. Update service tests to match actual audit logging behavior
9. Fix service test mock chain structures

### Phase 4: API Tests (45 min)
10. Verify API response structures (lists vs wrapped objects)
11. Update API tests to match actual responses
12. Fix auth middleware mocking in API tests

### Phase 5: MCP Tests (30 min)
13. Verify MCP executor actual return structure
14. Update MCP tests to match
15. Add proper Docker mocking

## Testing Strategy

After each phase, run subset of tests:

```bash
# Phase 1
pytest tests/unit/test_sdk_requests.py tests/unit/test_sdk_proposals.py -v

# Phase 2
pytest tests/unit/test_sdk_*.py -v

# Phase 3
pytest tests/unit/test_*_service.py -v

# Phase 4
pytest tests/unit/test_api_*.py -v

# Phase 5
pytest tests/unit/test_mcp_*.py -v

# All
pytest tests/unit/ -v --tb=short
```

## Quick Reference - Correct APIs

### Audit Service
```python
# Logging
audit_service.log_event(
    org_id=str,
    actor_id=str,      # was user_id
    event_type=str,
    resource_type=str,
    resource_id=str,
    metadata=dict      # was details
)

# Retrieval
audit_service.get_audit_log(  # singular, not logs
    org_id=str,
    limit=int,
    event_type=str,
    resource_type=str,
    resource_id=str
)
```

### SDK Request Client
```python
# Create
client.create(
    search_query=str,
    search_results=list,
    justification=str
)

# Review (not separate approve/reject)
client.review(
    request_id=str,
    status="approved"|"rejected",
    review_notes=str
)
```

### SDK Proposal Client
```python
# Create
client.create(
    proposal_type=str,
    item_name=str,
    item_description=str,
    item_category=str,
    item_metadata=dict,
    replacing_item_id=str,  # NOT deprecated_item_id
    request_id=str
)

# These exist
client.approve(proposal_id, review_notes)
client.reject(proposal_id, review_notes)
```

## Current Status

- **Passing**: ~20 tests (embedding service, audit service)
- **Failing**: ~87 tests (needs alignment)
- **Estimated fix time**: 2.5-3 hours for all phases
