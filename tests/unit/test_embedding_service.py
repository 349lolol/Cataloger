"""
Unit tests for embedding service.
"""
import pytest
import numpy as np
from unittest.mock import patch, Mock
from app.services.embedding_service import encode_text, encode_batch, encode_catalog_item


class TestEmbeddingService:
    """Test embedding service functions."""

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_text_returns_list(self, mock_get_model):
        """Test that encode_text returns a list."""
        # Mock the model
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model

        result = encode_text("test text")
        assert isinstance(result, list)
        assert len(result) == 384  # all-MiniLM-L6-v2 dimension

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_text_values_are_floats(self, mock_get_model):
        """Test that embedding values are floats."""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model

        result = encode_text("test text")
        assert all(isinstance(x, (float, np.floating)) for x in result)

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_batch_returns_list_of_lists(self, mock_get_model):
        """Test that encode_batch returns list of embeddings."""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(3, 384)
        mock_get_model.return_value = mock_model

        texts = ["text one", "text two", "text three"]
        result = encode_batch(texts)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_batch_empty_list(self, mock_get_model):
        """Test encode_batch with empty list."""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([])
        mock_get_model.return_value = mock_model

        result = encode_batch([])
        assert isinstance(result, list)

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_catalog_item_with_all_fields(self, mock_get_model):
        """Test encoding catalog item with all fields."""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model

        result = encode_catalog_item(
            name="Laptop",
            description="A high-performance laptop",
            category="Electronics"
        )
        assert isinstance(result, list)
        assert len(result) == 384

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_catalog_item_with_name_only(self, mock_get_model):
        """Test encoding catalog item with only name."""
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model

        result = encode_catalog_item(name="Laptop")
        assert isinstance(result, list)
        assert len(result) == 384

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_catalog_item_different_inputs_different_outputs(self, mock_get_model):
        """Test that different inputs produce different embeddings."""
        mock_model = Mock()
        # Return different embeddings for different calls
        mock_model.encode.side_effect = [
            np.random.rand(384),
            np.random.rand(384)
        ]
        mock_get_model.return_value = mock_model

        emb1 = encode_catalog_item(name="Laptop", category="Electronics")
        emb2 = encode_catalog_item(name="Chair", category="Furniture")
        assert emb1 != emb2

    @patch('app.services.embedding_service.get_embedding_model')
    def test_encode_catalog_item_similar_inputs_similar_outputs(self, mock_get_model):
        """Test that similar inputs produce similar embeddings."""
        mock_model = Mock()

        # Create similar embeddings (high cosine similarity)
        base_vec = np.random.rand(384)
        similar_vec = base_vec + np.random.rand(384) * 0.1  # Add small noise

        mock_model.encode.side_effect = [base_vec, similar_vec]
        mock_get_model.return_value = mock_model

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
