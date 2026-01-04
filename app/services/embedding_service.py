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


EXPECTED_EMBEDDING_DIMENSION = 768


@resilient_external_call("gemini", max_retries=3)
def encode_text(text: str) -> List[float]:
    """
    Encode a single text string into a vector embedding using Gemini.

    Args:
        text: Input text to encode

    Returns:
        List of floats representing the embedding vector (768 dimensions)

    Raises:
        ValueError: If embedding is missing or has wrong dimensions
    """
    model = _get_embedding_model()
    result = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document"
    )

    embedding = result.get('embedding')
    if not embedding:
        raise ValueError("Gemini returned no embedding")
    if len(embedding) != EXPECTED_EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}"
        )

    return embedding


def encode_batch(
    texts: List[str],
    max_workers: int = 5,
    timeout_per_item: float = 30.0
) -> List[List[float]]:
    """
    Encode multiple texts into embedding vectors using parallel processing.

    Args:
        texts: List of input texts to encode
        max_workers: Maximum number of concurrent threads (default: 5)
        timeout_per_item: Timeout in seconds for each embedding call (default: 30)

    Returns:
        List of embedding vectors (maintains input order).
        Failed embeddings will be None - caller should handle this.

    Raises:
        ValueError: If all embeddings fail
    """
    if not texts:
        return []

    results = [None] * len(texts)
    failed_count = 0

    def encode_with_index(index: int, text: str) -> tuple[int, List[float]]:
        """Encode text and return with index for ordering."""
        embedding = encode_text(text)
        return (index, embedding)

    # Process in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(encode_with_index, i, text): i
            for i, text in enumerate(texts)
        }

        for future in as_completed(futures):
            original_index = futures[future]
            try:
                index, embedding = future.result(timeout=timeout_per_item)
                results[index] = embedding
            except TimeoutError:
                logger.error(f"Timeout encoding text at index {original_index}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Failed to encode text at index {original_index}: {e}")
                failed_count += 1

    # Raise if all embeddings failed
    if failed_count == len(texts):
        raise ValueError(f"All {len(texts)} embedding requests failed")

    if failed_count > 0:
        logger.warning(f"{failed_count}/{len(texts)} embeddings failed, results contain None values")

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
