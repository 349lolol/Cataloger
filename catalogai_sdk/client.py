"""
CatalogAI Python SDK - Main client
"""
import os
import httpx
from typing import Optional


class CatalogAIClient:
    """Main client for interacting with CatalogAI API."""

    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize CatalogAI client.

        Args:
            base_url: Base URL of CatalogAI API (e.g., "http://localhost:5000")
                     If not provided, reads from CATALOGAI_API_URL env var
            auth_token: Supabase JWT authentication token
                       If not provided, reads from CATALOGAI_AUTH_TOKEN env var
        """
        # Read from environment if not provided
        if base_url is None:
            base_url = os.getenv('CATALOGAI_API_URL')
            if not base_url:
                raise ValueError(
                    "base_url not provided and CATALOGAI_API_URL not set in environment"
                )

        if auth_token is None:
            auth_token = os.getenv('CATALOGAI_AUTH_TOKEN')
            if not auth_token:
                raise ValueError(
                    "auth_token not provided and CATALOGAI_AUTH_TOKEN not set in environment"
                )

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
