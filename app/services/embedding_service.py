"""
Embedding service for generating vector embeddings from text.
Uses Google Gemini text-embedding-004 for semantic search capabilities.
"""
from typing import List
import google.generativeai as genai
from app.config import get_settings


def _get_embedding_model():
    """Get configured Gemini embedding model."""
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return 'models/text-embedding-004'


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


def encode_batch(texts: List[str]) -> List[List[float]]:
    """
    Encode multiple texts into embedding vectors (batch processing).

    Args:
        texts: List of input texts to encode

    Returns:
        List of embedding vectors
    """
    model = _get_embedding_model()
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])
    return embeddings


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
