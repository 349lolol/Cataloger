"""
Unit tests for embedding service.
"""
import pytest
from app.services.embedding_service import encode_text, encode_batch, encode_catalog_item


class TestEmbeddingService:
    """Test embedding service functions."""

    def test_encode_text_returns_list(self):
        """Test that encode_text returns a list."""
        result = encode_text("test text")
        assert isinstance(result, list)
        assert len(result) == 384  # all-MiniLM-L6-v2 dimension

    def test_encode_text_values_are_floats(self):
        """Test that embedding values are floats."""
        result = encode_text("test text")
        assert all(isinstance(x, float) for x in result)

    def test_encode_batch_returns_list_of_lists(self):
        """Test that encode_batch returns list of embeddings."""
        texts = ["text one", "text two", "text three"]
        result = encode_batch(texts)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)

    def test_encode_batch_empty_list(self):
        """Test encode_batch with empty list."""
        result = encode_batch([])
        assert result == []

    def test_encode_catalog_item_with_all_fields(self):
        """Test encoding catalog item with all fields."""
        result = encode_catalog_item(
            name="Laptop",
            description="A high-performance laptop",
            category="Electronics"
        )
        assert isinstance(result, list)
        assert len(result) == 384

    def test_encode_catalog_item_with_name_only(self):
        """Test encoding catalog item with only name."""
        result = encode_catalog_item(name="Laptop")
        assert isinstance(result, list)
        assert len(result) == 384

    def test_encode_catalog_item_different_inputs_different_outputs(self):
        """Test that different inputs produce different embeddings."""
        emb1 = encode_catalog_item(name="Laptop", category="Electronics")
        emb2 = encode_catalog_item(name="Chair", category="Furniture")
        assert emb1 != emb2

    def test_encode_catalog_item_similar_inputs_similar_outputs(self):
        """Test that similar inputs produce similar embeddings."""
        emb1 = encode_catalog_item(name="Laptop", description="Computer")
        emb2 = encode_catalog_item(name="Computer", description="Laptop")

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            import math
            dot_product = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            return dot_product / (mag_a * mag_b)

        similarity = cosine_similarity(emb1, emb2)
        assert similarity > 0.7  # Similar items should have high similarity
