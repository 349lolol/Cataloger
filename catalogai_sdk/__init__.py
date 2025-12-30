"""CatalogAI Python SDK."""
from .client import CatalogAIClient

# Alias for cleaner imports
CatalogAI = CatalogAIClient

__all__ = ['CatalogAIClient', 'CatalogAI']
__version__ = '0.1.0'
