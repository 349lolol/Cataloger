"""
CatalogAI Python SDK - Main client
"""
import httpx


class CatalogAIClient:
    """Main client for interacting with CatalogAI API."""

    def __init__(self, base_url: str, auth_token: str):
        """
        Initialize CatalogAI client.

        Args:
            base_url: Base URL of CatalogAI API (e.g., "http://localhost:5000")
            auth_token: Supabase JWT authentication token
        """
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30.0
        )

    @property
    def catalog(self):
        """Access catalog operations."""
        from .catalog import CatalogClient
        return CatalogClient(self.client)

    @property
    def requests(self):
        """Access request operations."""
        from .requests import RequestClient
        return RequestClient(self.client)

    @property
    def proposals(self):
        """Access proposal operations."""
        from .proposals import ProposalClient
        return ProposalClient(self.client)

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
