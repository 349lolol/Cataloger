"""
Embedding service for generating vector embeddings from text.
Uses SentenceTransformer for semantic search capabilities.
"""
from typing import List
import numpy as np
from app.extensions import get_embedding_model


def encode_text(text: str) -> List[float]:
    """
    Encode a single text string into a vector embedding.

    Args:
        text: Input text to encode

    Returns:
        List of floats representing the embedding vector (384 dimensions)
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def encode_batch(texts: List[str]) -> List[List[float]]:
    """
    Encode multiple texts into embedding vectors (batch processing).

    Args:
        texts: List of input texts to encode

    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


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
