import os
import sys
import httpx
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

mcp = FastMCP("catalogai")

_auth_state = {
    "access_token": None,
    "user_id": None,
    "org_id": None,
    "user_role": None,
    "api_url": None
}


def authenticate():
    supabase_url = os.getenv('SUPABASE_URL')
    user_email = os.getenv('USER_EMAIL')
    user_password = os.getenv('USER_PASSWORD')
    api_url = os.getenv('API_URL', 'http://localhost:5000')

    if not all([supabase_url, user_email, user_password]):
        raise ValueError("Missing: SUPABASE_URL, USER_EMAIL, USER_PASSWORD")

    auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"

    try:
        response = httpx.post(
            auth_url,
            json={"email": user_email, "password": user_password},
            headers={"apikey": os.getenv('SUPABASE_KEY')},
            timeout=10.0
        )
        response.raise_for_status()

        data = response.json()
        access_token = data.get('access_token')
        user = data.get('user', {})

        if not access_token:
            raise ValueError("No access token in response")

        _auth_state['access_token'] = access_token
        _auth_state['user_id'] = user.get('id')
        _auth_state['api_url'] = api_url

        user_info = _api_call('GET', '/api/auth/verify')
        if user_info:
            _auth_state['org_id'] = user_info.get('org_id')
            _auth_state['user_role'] = user_info.get('role')

        print(f"Authenticated as {user_email}", file=sys.stderr)
        print(f"  Org: {_auth_state['org_id']}, Role: {_auth_state['user_role']}", file=sys.stderr)

    except Exception as e:
        raise RuntimeError(f"Authentication failed: {str(e)}")


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


def _api_call(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    if not _auth_state['access_token']:
        raise RuntimeError("Not authenticated")

    url = f"{_auth_state['api_url']}{endpoint}"
    headers = {
        'Authorization': f"Bearer {_auth_state['access_token']}",
        'Content-Type': 'application/json'
    }

    try:
        response = httpx.request(method, url, headers=headers, timeout=30.0, **kwargs)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            error_msg = error_data.get('error', e.response.text)
        except Exception:
            error_msg = e.response.text
        raise APIError(e.response.status_code, error_msg)
    except httpx.TimeoutException:
        raise Exception("Request timed out")
    except httpx.ConnectError:
        raise Exception("Connection failed")


# Catalog Tools

@mcp.tool()
def search_catalog(query: str, limit: int = 10, threshold: float = 0.3) -> Dict[str, Any]:
    """Search catalog items using semantic similarity."""
    return _api_call('POST', '/api/catalog/search', json={'query': query, 'limit': limit, 'threshold': threshold})


@mcp.tool()
def get_catalog_item(item_id: str) -> Dict[str, Any]:
    """Get catalog item details by ID."""
    return _api_call('GET', f'/api/catalog/items/{item_id}')


@mcp.tool()
def list_catalog(limit: int = 50, category: Optional[str] = None) -> Dict[str, Any]:
    """List catalog items with optional category filter."""
    params = {'limit': limit}
    if category:
        params['category'] = category
    return _api_call('GET', '/api/catalog/items', params=params)


# Request Tools

@mcp.tool()
def create_request(product_name: str, justification: str, use_ai_enrichment: bool = True) -> Dict[str, Any]:
    """Create a new procurement request."""
    return _api_call('POST', '/api/catalog/request-new-item', json={
        'name': product_name,
        'justification': justification,
        'use_ai_enrichment': use_ai_enrichment
    })


@mcp.tool()
def list_requests(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """List procurement requests. Status: pending, approved, rejected."""
    params = {'limit': limit}
    if status:
        params['status'] = status
    return _api_call('GET', '/api/requests', params=params)


@mcp.tool()
def get_request(request_id: str) -> Dict[str, Any]:
    """Get request details by ID."""
    return _api_call('GET', f'/api/requests/{request_id}')


@mcp.tool()
def approve_request(
    request_id: str,
    review_notes: Optional[str] = None,
    create_proposal: bool = False,
    proposal_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Approve a procurement request (reviewer/admin only)."""
    payload = {'status': 'approved', 'review_notes': review_notes}
    if create_proposal and proposal_data:
        payload['create_proposal'] = proposal_data
    return _api_call('POST', f'/api/requests/{request_id}/review', json=payload)


@mcp.tool()
def reject_request(request_id: str, review_notes: str) -> Dict[str, Any]:
    """Reject a procurement request (reviewer/admin only)."""
    return _api_call('POST', f'/api/requests/{request_id}/review', json={'status': 'rejected', 'review_notes': review_notes})


# Proposal Tools

@mcp.tool()
def create_proposal(
    proposal_type: str,
    item_name: str,
    item_description: str,
    item_category: str,
    item_price: Optional[float] = None,
    item_pricing_type: Optional[str] = None,
    item_vendor: Optional[str] = None,
    item_sku: Optional[str] = None,
    item_product_url: Optional[str] = None,
    item_metadata: Optional[Dict[str, Any]] = None,
    replacing_item_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a catalog change proposal. Types: ADD_ITEM, REPLACE_ITEM, DEPRECATE_ITEM."""
    return _api_call('POST', '/api/proposals', json={
        'proposal_type': proposal_type,
        'item_name': item_name,
        'item_description': item_description,
        'item_category': item_category,
        'item_price': item_price,
        'item_pricing_type': item_pricing_type,
        'item_vendor': item_vendor,
        'item_sku': item_sku,
        'item_product_url': item_product_url,
        'item_metadata': item_metadata or {},
        'replacing_item_id': replacing_item_id,
        'request_id': request_id
    })


@mcp.tool()
def list_proposals(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """List proposals. Status: pending, approved, rejected, merged."""
    params = {'limit': limit}
    if status:
        params['status'] = status
    return _api_call('GET', '/api/proposals', params=params)


@mcp.tool()
def get_proposal(proposal_id: str) -> Dict[str, Any]:
    """Get proposal details by ID."""
    return _api_call('GET', f'/api/proposals/{proposal_id}')


@mcp.tool()
def approve_proposal(proposal_id: str, review_notes: Optional[str] = None) -> Dict[str, Any]:
    """Approve a proposal (reviewer/admin only). Auto-updates catalog."""
    return _api_call('POST', f'/api/proposals/{proposal_id}/approve', json={'review_notes': review_notes})


@mcp.tool()
def reject_proposal(proposal_id: str, review_notes: str) -> Dict[str, Any]:
    """Reject a proposal (reviewer/admin only)."""
    return _api_call('POST', f'/api/proposals/{proposal_id}/reject', json={'review_notes': review_notes})


# AI Enrichment Tools

@mcp.tool()
def enrich_product(product_name: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Use Gemini AI to auto-populate product details from a name."""
    payload = {'product_name': product_name}
    if category:
        payload['category'] = category
    return _api_call('POST', '/api/products/enrich', json=payload)


@mcp.tool()
def enrich_products_batch(product_names: List[str]) -> Dict[str, Any]:
    """Enrich multiple products in batch (max 20)."""
    if len(product_names) > 20:
        return {"error": "Maximum 20 products per batch"}
    return _api_call('POST', '/api/products/enrich-batch', json={'product_names': product_names})


# Admin Tools

@mcp.tool()
def get_audit_log(limit: int = 100, event_type: Optional[str] = None, resource_type: Optional[str] = None) -> Dict[str, Any]:
    """Get audit log events (admin only)."""
    params = {'limit': limit}
    if event_type:
        params['event_type'] = event_type
    if resource_type:
        params['resource_type'] = resource_type
    return _api_call('GET', '/api/admin/audit-log', params=params)


@mcp.tool()
def check_embeddings_health() -> Dict[str, Any]:
    """Check and repair catalog embeddings (admin only)."""
    return _api_call('POST', '/api/admin/embeddings/check')


# Skills Tool

@mcp.tool()
def list_skills() -> str:
    """List available skills for code execution."""
    skills_readme = os.path.join(os.path.dirname(__file__), 'skills', 'README.md')
    with open(skills_readme) as f:
        return f.read()


# Code Execution Tool

@mcp.tool()
def execute_code(code: str, description: str = "Execute Python code") -> str:
    """
    Execute Python code in Docker sandbox.

    For multi-step operations, use the skills module:
    ```python
    from skills import catalog, reqs, proposals
    import json

    # Example: find matches for pending requests
    pending = reqs.list_all(status="pending")
    result = []
    for req in pending:
        matches = catalog.search(req["search_query"], limit=3)
        result.append({"request_id": req["id"], "matches": matches})
    print(json.dumps(result))
    ```

    Run `list_skills` tool first to see all available functions.
    Output JSON only - no formatting, no emojis.

    Security: 512MB RAM, 50% CPU, 30s timeout, isolated network.
    """
    from catalogai_mcp.code_executor import CodeExecutor

    if not hasattr(execute_code, '_executor'):
        execute_code._executor = CodeExecutor(image_name="catalogai-sandbox:latest")

    context = {
        "api_url": _auth_state['api_url'],
        "auth_token": _auth_state['access_token']
    }

    result = execute_code._executor.execute(code, context)

    if result['status'] == 'error':
        return f"Error:\n{result['output']}"
    return result['output']


def main():
    try:
        print("Authenticating MCP server...", file=sys.stderr)
        authenticate()
        print("MCP server ready\n", file=sys.stderr)
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"Failed to start: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
