"""
Embedding service for generating vector embeddings from text.
Uses Google Gemini text-embedding-004 for semantic search capabilities.
"""
from typing import List
import google.generativeai as genai
from app.config import get_settings
from app.utils.resilience import resilient_external_call
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


def _get_embedding_model():
    """Get configured Gemini embedding model."""
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return 'models/text-embedding-004'


@resilient_external_call("gemini", max_retries=3)
def encode_text(text: str) -> List[float]:
    """
    Encode a single text string into a vector embedding using Gemini.

    Args:
        text: Input text to encode

    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    model = _get_embedding_model()
    result = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']


def encode_batch(texts: List[str], max_workers: int = 5) -> List[List[float]]:
    """
    Encode multiple texts into embedding vectors using parallel processing.

    Args:
        texts: List of input texts to encode
        max_workers: Maximum number of concurrent threads (default: 5)

    Returns:
        List of embedding vectors (maintains input order)
    """
    results = [None] * len(texts)

    def encode_with_index(index: int, text: str) -> tuple[int, List[float]]:
        """Encode text and return with index for ordering."""
        try:
            embedding = encode_text(text)
            return (index, embedding)
        except Exception as e:
            logger.error(f"Failed to encode text at index {index}: {e}")
            raise

    # Process in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(encode_with_index, i, text): i
            for i, text in enumerate(texts)
        }

        for future in as_completed(futures):
            index, embedding = future.result()
            results[index] = embedding

    return results


def encode_catalog_item(name: str, description: str = "", category: str = "") -> List[float]:
    """
    Encode a catalog item by concatenating its fields.
    This creates a rich semantic representation combining multiple attributes.

    Args:
        name: Item name
        description: Item description (optional)
        category: Item category (optional)

    Returns:
        Embedding vector representing the combined item information
    """
    # Concatenate fields with separators for better semantic meaning
    parts = [name]
    if category:
        parts.append(f"Category: {category}")
    if description:
        parts.append(description)

    combined_text = " | ".join(parts)
    return encode_text(combined_text)
