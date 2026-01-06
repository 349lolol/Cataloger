import os
import httpx
from typing import Optional


class CatalogAIClient:
    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv('CATALOGAI_API_URL')
            if not base_url:
                raise ValueError("base_url not provided and CATALOGAI_API_URL not set")

        if auth_token is None:
            auth_token = os.getenv('CATALOGAI_AUTH_TOKEN')
            if not auth_token:
                raise ValueError("auth_token not provided and CATALOGAI_AUTH_TOKEN not set")

        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30.0
        )

    @property
    def catalog(self):
        from .catalog import CatalogClient
        return CatalogClient(self.client)

    @property
    def requests(self):
        from .requests import RequestClient
        return RequestClient(self.client)

    @property
    def proposals(self):
        from .proposals import ProposalClient
        return ProposalClient(self.client)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
