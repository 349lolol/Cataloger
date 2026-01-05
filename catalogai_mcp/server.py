"""
MCP Server for CatalogAI - Agentic Procurement Interface.

Provides direct tools for catalog operations, procurement workflows,
and analytics. Authenticates on startup using Supabase credentials.
"""
import os
import sys
import httpx
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MCP server instance
mcp = FastMCP("catalogai")

# Global state for authentication
_auth_state = {
    "access_token": None,
    "user_id": None,
    "org_id": None,
    "user_role": None,
    "api_url": None
}


def authenticate():
    """
    Authenticate user on MCP server startup.

    Reads credentials from environment variables:
    - SUPABASE_URL: Supabase project URL
    - USER_EMAIL: User's email
    - USER_PASSWORD: User's password
    - API_URL: CatalogAI API base URL (default: http://localhost:5000)
    """
    supabase_url = os.getenv('SUPABASE_URL')
    user_email = os.getenv('USER_EMAIL')
    user_password = os.getenv('USER_PASSWORD')
    api_url = os.getenv('API_URL', 'http://localhost:5000')

    if not all([supabase_url, user_email, user_password]):
        raise ValueError(
            "Missing required environment variables: "
            "SUPABASE_URL, USER_EMAIL, USER_PASSWORD"
        )

    # Authenticate with Supabase
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

        # Store auth state
        _auth_state['access_token'] = access_token
        _auth_state['user_id'] = user.get('id')
        _auth_state['api_url'] = api_url

        # Get user's org and role from API
        user_info = _api_call('GET', '/api/auth/verify')
        if user_info:
            _auth_state['org_id'] = user_info.get('org_id')
            _auth_state['user_role'] = user_info.get('role')

        print(f"✅ Authenticated as {user_email}", file=sys.stderr)
        print(f"   User ID: {_auth_state['user_id']}", file=sys.stderr)
        print(f"   Org ID: {_auth_state['org_id']}", file=sys.stderr)
        print(f"   Role: {_auth_state['user_role']}", file=sys.stderr)

    except Exception as e:
        raise RuntimeError(f"Authentication failed: {str(e)}")


class APIError(Exception):
    """Custom exception for API errors with status code and message."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


def _api_call(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """
    Make authenticated API call to CatalogAI backend.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        **kwargs: Additional arguments for httpx request

    Returns:
        Response JSON data

    Raises:
        RuntimeError: If not authenticated
        APIError: If API returns an error status code
        Exception: For network or other errors
    """
    if not _auth_state['access_token']:
        raise RuntimeError("Not authenticated. Call authenticate() first.")

    url = f"{_auth_state['api_url']}{endpoint}"
    headers = {
        'Authorization': f"Bearer {_auth_state['access_token']}",
        'Content-Type': 'application/json'
    }

    try:
        response = httpx.request(
            method,
            url,
            headers=headers,
            timeout=30.0,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        # Try to extract error message from response
        try:
            error_data = e.response.json()
            error_msg = error_data.get('error', e.response.text)
        except Exception:
            error_msg = e.response.text
        raise APIError(e.response.status_code, error_msg)
    except httpx.TimeoutException:
        raise Exception("Request timed out - API server may be unavailable")
    except httpx.ConnectError:
        raise Exception("Connection failed - API server may be unavailable")


# ============================================================================
# CATALOG TOOLS
# ============================================================================

@mcp.tool()
def search_catalog(query: str, limit: int = 10, threshold: float = 0.3) -> Dict[str, Any]:
    """
    Search catalog items using semantic similarity.

    Uses vector embeddings to find products matching the natural language query.

    Args:
        query: Natural language search query (e.g., "laptop for video editing")
        limit: Maximum number of results (default: 10)
        threshold: Minimum similarity score 0-1 (default: 0.3)

    Returns:
        List of matching catalog items with similarity scores

    Example:
        search_catalog("ergonomic office chair", limit=5)
    """
    return _api_call(
        'POST',
        '/api/catalog/search',
        json={'query': query, 'limit': limit, 'threshold': threshold}
    )


@mcp.tool()
def get_catalog_item(item_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a catalog item.

    Args:
        item_id: Catalog item UUID

    Returns:
        Full catalog item details including price, vendor, specs, etc.
    """
    return _api_call('GET', f'/api/catalog/items/{item_id}')


@mcp.tool()
def list_catalog(limit: int = 50, category: Optional[str] = None) -> Dict[str, Any]:
    """
    List catalog items with optional filtering.

    Args:
        limit: Maximum number of items to return (default: 50)
        category: Filter by category (optional)

    Returns:
        List of catalog items
    """
    params = {'limit': limit}
    if category:
        params['category'] = category

    return _api_call('GET', '/api/catalog/items', params=params)


# ============================================================================
# REQUEST TOOLS
# ============================================================================

@mcp.tool()
def create_request(
    product_name: str,
    justification: str,
    use_ai_enrichment: bool = True
) -> Dict[str, Any]:
    """
    Create a new procurement request.

    Args:
        product_name: Name/description of product needed
        justification: Business justification for the request
        use_ai_enrichment: Use Gemini AI to enrich product details (default: True)

    Returns:
        Created request with ID

    Example:
        create_request(
            product_name="MacBook Pro 16 inch M3 Max",
            justification="Need for video editing team",
            use_ai_enrichment=True
        )
    """
    return _api_call(
        'POST',
        '/api/catalog/request-new-item',
        json={
            'name': product_name,
            'justification': justification,
            'use_ai_enrichment': use_ai_enrichment
        }
    )


@mcp.tool()
def list_requests(
    status: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List procurement requests.

    Args:
        status: Filter by status (pending, approved, rejected) - optional
        limit: Maximum number of results (default: 50)

    Returns:
        List of requests
    """
    params = {'limit': limit}
    if status:
        params['status'] = status

    return _api_call('GET', '/api/requests', params=params)


@mcp.tool()
def get_request(request_id: str) -> Dict[str, Any]:
    """
    Get details of a specific request.

    Args:
        request_id: Request UUID

    Returns:
        Full request details
    """
    return _api_call('GET', f'/api/requests/{request_id}')


@mcp.tool()
def approve_request(
    request_id: str,
    review_notes: Optional[str] = None,
    create_proposal: bool = False,
    proposal_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Approve a procurement request (reviewer/admin only).

    Args:
        request_id: Request UUID to approve
        review_notes: Optional notes about the approval
        create_proposal: Auto-create proposal after approval (default: False)
        proposal_data: Proposal details if create_proposal=True

    Returns:
        Updated request (and proposal if created)

    Example:
        approve_request(
            request_id="abc-123",
            review_notes="Approved for Q1 budget",
            create_proposal=True,
            proposal_data={
                "proposal_type": "ADD_ITEM",
                "item_name": "MacBook Pro 16 M3 Max",
                "item_description": "...",
                "item_category": "Computers",
                "item_price": 3499.00,
                "item_pricing_type": "one_time"
            }
        )
    """
    payload = {
        'status': 'approved',
        'review_notes': review_notes
    }

    if create_proposal and proposal_data:
        payload['create_proposal'] = proposal_data

    return _api_call('POST', f'/api/requests/{request_id}/review', json=payload)


@mcp.tool()
def reject_request(request_id: str, review_notes: str) -> Dict[str, Any]:
    """
    Reject a procurement request (reviewer/admin only).

    Args:
        request_id: Request UUID to reject
        review_notes: Required notes explaining rejection

    Returns:
        Updated request
    """
    return _api_call(
        'POST',
        f'/api/requests/{request_id}/review',
        json={'status': 'rejected', 'review_notes': review_notes}
    )


# ============================================================================
# PROPOSAL TOOLS
# ============================================================================

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
    """
    Create a catalog change proposal (reviewer/admin only).

    Args:
        proposal_type: Type - "ADD_ITEM", "REPLACE_ITEM", or "DEPRECATE_ITEM"
        item_name: Product name
        item_description: Product description
        item_category: Product category
        item_price: Price in USD (optional)
        item_pricing_type: "one_time", "monthly", "yearly", or "usage_based" (optional)
        item_vendor: Vendor name (optional)
        item_sku: SKU or product code (optional)
        item_product_url: Product URL (optional)
        item_metadata: Additional metadata dict (optional)
        replacing_item_id: Item to replace (required for REPLACE_ITEM/DEPRECATE_ITEM)
        request_id: Associated request ID (optional)

    Returns:
        Created proposal with ID
    """
    payload = {
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
    }

    return _api_call('POST', '/api/proposals', json=payload)


@mcp.tool()
def list_proposals(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    List catalog change proposals.

    Args:
        status: Filter by status (pending, approved, rejected, merged) - optional
        limit: Maximum number of results (default: 50)

    Returns:
        List of proposals
    """
    params = {'limit': limit}
    if status:
        params['status'] = status

    return _api_call('GET', '/api/proposals', params=params)


@mcp.tool()
def get_proposal(proposal_id: str) -> Dict[str, Any]:
    """
    Get details of a specific proposal.

    Args:
        proposal_id: Proposal UUID

    Returns:
        Full proposal details
    """
    return _api_call('GET', f'/api/proposals/{proposal_id}')


@mcp.tool()
def approve_proposal(proposal_id: str, review_notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Approve a catalog change proposal (reviewer/admin only).

    This automatically updates the catalog based on the proposal type.

    Args:
        proposal_id: Proposal UUID to approve
        review_notes: Optional notes about the approval

    Returns:
        Updated proposal and created/updated catalog item
    """
    return _api_call(
        'POST',
        f'/api/proposals/{proposal_id}/approve',
        json={'review_notes': review_notes}
    )


@mcp.tool()
def reject_proposal(proposal_id: str, review_notes: str) -> Dict[str, Any]:
    """
    Reject a catalog change proposal (reviewer/admin only).

    Args:
        proposal_id: Proposal UUID to reject
        review_notes: Required notes explaining rejection

    Returns:
        Updated proposal
    """
    return _api_call(
        'POST',
        f'/api/proposals/{proposal_id}/reject',
        json={'review_notes': review_notes}
    )


# ============================================================================
# AI ENRICHMENT TOOLS
# ============================================================================

@mcp.tool()
def enrich_product(product_name: str, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Use Gemini AI to auto-populate product details from just a name.

    Args:
        product_name: Product name to enrich (e.g., "MacBook Pro 16 M3 Max")
        category: Optional category hint for better accuracy

    Returns:
        Enriched product data with vendor, price, SKU, specs, etc.

    Example:
        enrich_product("Dell XPS 15 9530", category="Computers")
    """
    payload = {'product_name': product_name}
    if category:
        payload['category'] = category

    return _api_call('POST', '/api/products/enrich', json=payload)


@mcp.tool()
def enrich_products_batch(product_names: List[str]) -> Dict[str, Any]:
    """
    Enrich multiple products in batch (max 20).

    Args:
        product_names: List of product names to enrich

    Returns:
        List of enriched product data
    """
    if len(product_names) > 20:
        return {"error": "Maximum 20 products per batch"}

    return _api_call(
        'POST',
        '/api/products/enrich-batch',
        json={'product_names': product_names}
    )


# ============================================================================
# ANALYTICS & ADMIN TOOLS
# ============================================================================

@mcp.tool()
def get_audit_log(
    limit: int = 100,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get audit log events (admin only).

    Args:
        limit: Maximum number of events (default: 100)
        event_type: Filter by event type (optional)
        resource_type: Filter by resource type (optional)

    Returns:
        List of audit events
    """
    params = {'limit': limit}
    if event_type:
        params['event_type'] = event_type
    if resource_type:
        params['resource_type'] = resource_type

    return _api_call('GET', '/api/admin/audit-log', params=params)


@mcp.tool()
def check_embeddings_health() -> Dict[str, Any]:
    """
    Check catalog embeddings health and repair if needed (admin only).

    Returns:
        Report of embedding status and any repairs performed
    """
    return _api_call('POST', '/api/admin/embeddings/check')


# ============================================================================
# CODE EXECUTION TOOL
# ============================================================================

@mcp.tool()
def execute_code(code: str, description: str = "Execute Python code") -> str:
    """
    Execute Python code in an isolated Docker sandbox with catalogai_sdk available.

    This tool dramatically reduces token usage by allowing Claude to write Python code
    that performs complex multi-step operations, instead of making multiple direct tool calls.

    The sandbox has the catalogai SDK pre-installed and auto-authenticated:

    ```python
    from catalogai_sdk import CatalogAI

    client = CatalogAI()  # Auto-authenticated with your token
    ```

    ## SDK Reference

    ### Catalog Operations (client.catalog)
    ```python
    # Search catalog with semantic similarity
    results = client.catalog.search(query="laptop for video editing", threshold=0.3, limit=10)
    # Returns: list of items with 'similarity_score'

    # List all catalog items
    items = client.catalog.list(status=None, limit=100)
    # Returns: list of catalog items

    # Get single item by ID
    item = client.catalog.get(item_id="uuid-here")
    # Returns: catalog item dict

    # Create item directly (admin only)
    item = client.catalog.create(name="...", description="...", category="...", metadata={})

    # Request new item (creates proposal for review)
    result = client.catalog.request_new_item(
        name="MacBook Pro 16 M3",
        description="High-performance laptop",
        category="Computers",
        metadata={},
        justification="Needed for video editing team"
    )
    ```

    ### Request Operations (client.requests)
    ```python
    # Create procurement request with search results
    request = client.requests.create(
        search_query="ergonomic chair",
        search_results=[{"id": "...", "name": "...", "similarity_score": 0.85}],
        justification="Team needs better seating"
    )

    # List requests
    requests = client.requests.list(status="pending", created_by=None, limit=100)
    # status options: "pending", "approved", "rejected"

    # Get single request
    request = client.requests.get(request_id="uuid-here")

    # Review request (reviewer/admin only)
    result = client.requests.review(
        request_id="uuid-here",
        status="approved",  # or "rejected"
        review_notes="Approved for Q1 budget"
    )
    ```

    ### Proposal Operations (client.proposals)
    ```python
    # Create proposal (reviewer/admin only)
    proposal = client.proposals.create(
        proposal_type="ADD_ITEM",  # or "REPLACE_ITEM", "DEPRECATE_ITEM"
        item_name="Product Name",
        item_description="Description",
        item_category="Category",
        item_metadata={},
        replacing_item_id=None,  # required for REPLACE/DEPRECATE
        request_id=None  # optional link to request
    )

    # List proposals
    proposals = client.proposals.list(status="pending", limit=100)
    # status options: "pending", "approved", "rejected", "merged"

    # Get single proposal
    proposal = client.proposals.get(proposal_id="uuid-here")

    # Approve proposal (reviewer/admin only)
    result = client.proposals.approve(proposal_id="uuid-here", review_notes="LGTM")

    # Reject proposal (reviewer/admin only)
    result = client.proposals.reject(proposal_id="uuid-here", review_notes="Not needed")
    ```

    Args:
        code: Python code to execute (must be valid Python 3.11)
        description: Brief description of what the code does

    Returns:
        The output (stdout/stderr) from code execution

    Example:
        execute_code('''
from catalogai_sdk import CatalogAI

client = CatalogAI()

# Search for laptops and filter by price
results = client.catalog.search("laptop", limit=20)
affordable = [r for r in results if r.get('price', 9999) < 2000]

if affordable:
    best = max(affordable, key=lambda x: x.get('similarity_score', 0))
    print(f"Best match: {best['name']} - ${best.get('price', 'N/A')}")

    # Request this item be added if not already in catalog
    result = client.catalog.request_new_item(
        name=best['name'],
        justification=f"Best laptop under $2000 for team"
    )
    print(f"Created proposal: {result['proposal']['id']}")
else:
    print("No laptops found under $2000")
''', description="Find and request best laptop under $2000")

    Security:
        - Code runs in isolated Docker container
        - 512MB memory limit, 50% CPU quota, 30s timeout
        - Non-root user, read-only filesystem except /tmp
        - Network access only to API
    """
    # Import code executor
    from catalogai_mcp.code_executor import CodeExecutor

    # Initialize executor if not already done
    if not hasattr(execute_code, '_executor'):
        execute_code._executor = CodeExecutor(image_name="catalogai-sandbox:latest")

    # Prepare execution context
    context = {
        "api_url": _auth_state['api_url'],
        "auth_token": _auth_state['access_token']
    }

    # Execute code in sandbox
    result = execute_code._executor.execute(code, context)

    if result['status'] == 'error':
        return f"Error executing code:\n{result['output']}"
    else:
        return result['output']


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

def main():
    """Run MCP server with authentication."""
    try:
        # Authenticate on startup
        print("🔐 Authenticating MCP server...", file=sys.stderr)
        authenticate()
        print("✅ MCP server ready!\n", file=sys.stderr)

        # Run server
        mcp.run(transport="stdio")

    except Exception as e:
        print(f"❌ Failed to start MCP server: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
