"""
Unit tests for embedding service.
Tests the Gemini-based embedding generation functions.
"""
import pytest
from unittest.mock import patch, Mock
from app.services.embedding_service import encode_text, encode_batch, encode_catalog_item


class TestEmbeddingService:
    """Test embedding service functions."""

    @patch('app.services.embedding_service.genai')
    def test_encode_text_returns_list(self, mock_genai):
        """Test that encode_text returns a list."""
        # Mock the Gemini API response
        mock_genai.embed_content.return_value = {
            'embedding': [0.1] * 768
        }

        result = encode_text("test text")
        assert isinstance(result, list)
        assert len(result) == 768  # Gemini text-embedding-004 dimension

    @patch('app.services.embedding_service.genai')
    def test_encode_text_values_are_floats(self, mock_genai):
        """Test that embedding values are floats."""
        mock_genai.embed_content.return_value = {
            'embedding': [0.5] * 768
        }

        result = encode_text("test text")
        assert all(isinstance(x, (float, int)) for x in result)

    @patch('app.services.embedding_service.genai')
    def test_encode_batch_returns_list_of_lists(self, mock_genai):
        """Test that encode_batch returns list of embeddings."""
        # Return different embeddings for different calls
        mock_genai.embed_content.side_effect = [
            {'embedding': [0.1] * 768},
            {'embedding': [0.2] * 768},
            {'embedding': [0.3] * 768}
        ]

        texts = ["text one", "text two", "text three"]
        result = encode_batch(texts, max_workers=1)  # Use 1 worker for deterministic order
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(emb) == 768 for emb in result)

    @patch('app.services.embedding_service.genai')
    def test_encode_batch_empty_list(self, mock_genai):
        """Test encode_batch with empty list."""
        result = encode_batch([])
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('app.services.embedding_service.genai')
    def test_encode_catalog_item_with_all_fields(self, mock_genai):
        """Test encoding catalog item with all fields."""
        mock_genai.embed_content.return_value = {
            'embedding': [0.1] * 768
        }

        result = encode_catalog_item(
            name="Laptop",
            description="A high-performance laptop",
            category="Electronics"
        )
        assert isinstance(result, list)
        assert len(result) == 768

        # Verify the API was called with concatenated text
        call_args = mock_genai.embed_content.call_args
        assert 'Laptop' in call_args[1]['content']
        assert 'Electronics' in call_args[1]['content']

    @patch('app.services.embedding_service.genai')
    def test_encode_catalog_item_with_name_only(self, mock_genai):
        """Test encoding catalog item with only name."""
        mock_genai.embed_content.return_value = {
            'embedding': [0.1] * 768
        }

        result = encode_catalog_item(name="Laptop")
        assert isinstance(result, list)
        assert len(result) == 768

    @patch('app.services.embedding_service.genai')
    def test_encode_catalog_item_different_inputs_different_outputs(self, mock_genai):
        """Test that different inputs produce different embeddings."""
        # Return different embeddings for different calls
        mock_genai.embed_content.side_effect = [
            {'embedding': [0.1] * 768},
            {'embedding': [0.9] * 768}
        ]

        emb1 = encode_catalog_item(name="Laptop", category="Electronics")
        emb2 = encode_catalog_item(name="Chair", category="Furniture")
        assert emb1 != emb2

    @patch('app.services.embedding_service.genai')
    def test_encode_catalog_item_similar_inputs_similar_outputs(self, mock_genai):
        """Test that similar inputs produce similar embeddings."""
        # Create similar embeddings (high cosine similarity)
        base_vec = [0.5] * 768
        similar_vec = [0.55] * 768  # Slightly different

        mock_genai.embed_content.side_effect = [
            {'embedding': base_vec},
            {'embedding': similar_vec}
        ]

        emb1 = encode_catalog_item(name="Laptop", description="Computer")
        emb2 = encode_catalog_item(name="Computer", description="Laptop")

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            import math
            dot_product = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            return dot_product / (mag_a * mag_b) if mag_a > 0 and mag_b > 0 else 0

        similarity = cosine_similarity(emb1, emb2)
        assert similarity > 0.7  # Similar items should have high similarity

    @patch('app.services.embedding_service.genai')
    def test_encode_text_calls_gemini_correctly(self, mock_genai):
        """Test that encode_text calls Gemini API with correct parameters."""
        mock_genai.embed_content.return_value = {
            'embedding': [0.1] * 768
        }

        encode_text("test query")

        mock_genai.embed_content.assert_called_once()
        call_args = mock_genai.embed_content.call_args
        assert call_args[1]['model'] == 'models/text-embedding-004'
        assert call_args[1]['content'] == 'test query'
        assert call_args[1]['task_type'] == 'retrieval_document'
