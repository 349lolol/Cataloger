"""
CatalogAI Skills - thin wrapper around SDK for code execution.

Usage:
    from skills import catalog, reqs, proposals

    results = catalog.search("laptop")
    pending = reqs.list_all(status="pending")
"""
from catalogai_sdk import CatalogAI

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = CatalogAI()
    return _client


class _CatalogSkills:
    def search(self, query, limit=10, threshold=0.3):
        """Semantic search. Returns list of matching items."""
        return _get_client().catalog.search(query=query, limit=limit, threshold=threshold)

    def get(self, item_id):
        """Get item by ID."""
        return _get_client().catalog.get(item_id=item_id)

    def list_items(self, limit=50, status="active"):
        """List catalog items."""
        return _get_client().catalog.list(limit=limit, status=status)

    def request_new(self, name, justification, use_ai=True):
        """Request a new item be added to catalog."""
        return _get_client().catalog.request_new_item(
            name=name, justification=justification, use_ai_enrichment=use_ai
        )


class _RequestSkills:
    def get(self, request_id):
        """Get request by ID."""
        return _get_client().requests.get(request_id=request_id)

    def list_all(self, status=None, limit=50):
        """List requests. Status: pending/approved/rejected."""
        return _get_client().requests.list(status=status, limit=limit)

    def review(self, request_id, status, notes=None):
        """Approve or reject a request. Status: approved/rejected."""
        return _get_client().requests.review(
            request_id=request_id, status=status, review_notes=notes
        )


class _ProposalSkills:
    def get(self, proposal_id):
        """Get proposal by ID."""
        return _get_client().proposals.get(proposal_id=proposal_id)

    def list_all(self, status=None, limit=50):
        """List proposals. Status: pending/approved/rejected/merged."""
        return _get_client().proposals.list(status=status, limit=limit)

    def create(self, proposal_type, item_name, item_description, item_category, **kwargs):
        """Create proposal. Types: ADD_ITEM, REPLACE_ITEM, DEPRECATE_ITEM."""
        return _get_client().proposals.create(
            proposal_type=proposal_type,
            item_name=item_name,
            item_description=item_description,
            item_category=item_category,
            **kwargs
        )

    def approve(self, proposal_id, notes=None):
        """Approve and merge proposal."""
        return _get_client().proposals.approve(proposal_id=proposal_id, review_notes=notes)

    def reject(self, proposal_id, notes=None):
        """Reject proposal."""
        return _get_client().proposals.reject(proposal_id=proposal_id, review_notes=notes)


# Singleton instances - use 'reqs' to avoid shadowing requests library
catalog = _CatalogSkills()
reqs = _RequestSkills()
proposals = _ProposalSkills()
