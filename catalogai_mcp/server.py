"""CatalogAI MCP server for Claude integration."""
import os
import sys
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

mcp = FastMCP("catalogai")

_auth_state = {
    "access_token": None,
    "user_id": None,
    "org_id": None,
    "user_role": None,
    "api_url": None
}


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


def _do_login(email: str, password: str) -> Dict[str, Any]:
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    api_url = os.getenv('API_URL', 'http://localhost:5001')

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")

    response = httpx.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={"apikey": supabase_key},
        timeout=10.0
    )
    response.raise_for_status()

    data = response.json()
    access_token = data.get('access_token')
    if not access_token:
        raise ValueError("No access token in response")

    _auth_state['access_token'] = access_token
    _auth_state['user_id'] = data.get('user', {}).get('id')
    _auth_state['api_url'] = api_url

    user_info = _api_call('GET', '/api/auth/verify')
    if user_info:
        _auth_state['org_id'] = user_info.get('org_id')
        _auth_state['user_role'] = user_info.get('role')

    return {
        "status": "authenticated",
        "user_id": _auth_state['user_id'],
        "org_id": _auth_state['org_id'],
        "role": _auth_state['user_role']
    }


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
            error_msg = e.response.json().get('error', e.response.text)
        except Exception:
            error_msg = e.response.text
        raise APIError(e.response.status_code, error_msg)
    except httpx.TimeoutException:
        raise Exception("Request timed out")
    except httpx.ConnectError:
        raise Exception("Connection failed")


@mcp.tool()
def login(email: str, password: str) -> Dict[str, Any]:
    """Login with email/password. Required before using other tools."""
    try:
        return _do_login(email, password)
    except httpx.HTTPStatusError as e:
        return {"error": f"Authentication failed: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def whoami() -> Dict[str, Any]:
    """Check authentication status."""
    if not _auth_state['access_token']:
        return {"authenticated": False, "message": "Not logged in"}
    return {
        "authenticated": True,
        "user_id": _auth_state['user_id'],
        "org_id": _auth_state['org_id'],
        "role": _auth_state['user_role']
    }


@mcp.tool()
def search_catalog(query: str, limit: int = 10, threshold: float = 0.3) -> Dict[str, Any]:
    """Semantic search for catalog items."""
    return _api_call('POST', '/api/catalog/search', json={'query': query, 'limit': limit, 'threshold': threshold})


@mcp.tool()
def get_catalog_item(item_id: str) -> Dict[str, Any]:
    """Get catalog item by ID."""
    return _api_call('GET', f'/api/catalog/items/{item_id}')


@mcp.tool()
def list_catalog(limit: int = 50, category: Optional[str] = None) -> Dict[str, Any]:
    """List catalog items."""
    params = {'limit': limit}
    if category:
        params['category'] = category
    return _api_call('GET', '/api/catalog/items', params=params)


@mcp.tool()
def create_request(product_name: str, justification: str, use_ai_enrichment: bool = True) -> Dict[str, Any]:
    """Create procurement request."""
    return _api_call('POST', '/api/catalog/request-new-item', json={
        'name': product_name,
        'justification': justification,
        'use_ai_enrichment': use_ai_enrichment
    })


@mcp.tool()
def list_requests(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """List requests. Status: pending/approved/rejected."""
    params = {'limit': limit}
    if status:
        params['status'] = status
    return _api_call('GET', '/api/requests', params=params)


@mcp.tool()
def get_request(request_id: str) -> Dict[str, Any]:
    """Get request by ID."""
    return _api_call('GET', f'/api/requests/{request_id}')


@mcp.tool()
def approve_request(
    request_id: str,
    review_notes: Optional[str] = None,
    create_proposal: bool = False,
    proposal_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Approve request (reviewer/admin)."""
    payload = {'status': 'approved', 'review_notes': review_notes}
    if create_proposal and proposal_data:
        payload['create_proposal'] = proposal_data
    return _api_call('POST', f'/api/requests/{request_id}/review', json=payload)


@mcp.tool()
def reject_request(request_id: str, review_notes: str) -> Dict[str, Any]:
    """Reject request (reviewer/admin)."""
    return _api_call('POST', f'/api/requests/{request_id}/review', json={'status': 'rejected', 'review_notes': review_notes})


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
    """Create catalog proposal. Types: ADD_ITEM/REPLACE_ITEM/DEPRECATE_ITEM."""
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
    """List proposals. Status: pending/approved/rejected/merged."""
    params = {'limit': limit}
    if status:
        params['status'] = status
    return _api_call('GET', '/api/proposals', params=params)


@mcp.tool()
def get_proposal(proposal_id: str) -> Dict[str, Any]:
    """Get proposal by ID."""
    return _api_call('GET', f'/api/proposals/{proposal_id}')


@mcp.tool()
def approve_proposal(proposal_id: str, review_notes: Optional[str] = None) -> Dict[str, Any]:
    """Approve and merge proposal (reviewer/admin)."""
    return _api_call('POST', f'/api/proposals/{proposal_id}/approve', json={'review_notes': review_notes})


@mcp.tool()
def reject_proposal(proposal_id: str, review_notes: str) -> Dict[str, Any]:
    """Reject proposal (reviewer/admin)."""
    return _api_call('POST', f'/api/proposals/{proposal_id}/reject', json={'review_notes': review_notes})


@mcp.tool()
def enrich_product(product_name: str, category: Optional[str] = None) -> Dict[str, Any]:
    """AI-enrich product details from name."""
    payload = {'product_name': product_name}
    if category:
        payload['category'] = category
    return _api_call('POST', '/api/products/enrich', json=payload)


@mcp.tool()
def enrich_products_batch(product_names: List[str]) -> Dict[str, Any]:
    """Batch enrich products (max 20)."""
    if len(product_names) > 20:
        return {"error": "Maximum 20 products per batch"}
    return _api_call('POST', '/api/products/enrich-batch', json={'product_names': product_names})


@mcp.tool()
def get_audit_log(limit: int = 100, event_type: Optional[str] = None, resource_type: Optional[str] = None) -> Dict[str, Any]:
    """Get audit log (admin only)."""
    params = {'limit': limit}
    if event_type:
        params['event_type'] = event_type
    if resource_type:
        params['resource_type'] = resource_type
    return _api_call('GET', '/api/admin/audit-log', params=params)


@mcp.tool()
def check_embeddings_health() -> Dict[str, Any]:
    """Check/repair embeddings (admin only)."""
    return _api_call('POST', '/api/admin/embeddings/check')


@mcp.tool()
def list_skills() -> str:
    """List skills for code execution."""
    skills_readme = os.path.join(os.path.dirname(__file__), 'skills', 'README.md')
    with open(skills_readme) as f:
        return f.read()


@mcp.tool()
def execute_code(code: str, description: str = "Execute Python code") -> str:
    """Execute Python in Docker sandbox. Use skills module for multi-step ops. Run list_skills first."""
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
    print("CatalogAI MCP server starting...", file=sys.stderr)
    print("Use login(email, password) to authenticate.\n", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
