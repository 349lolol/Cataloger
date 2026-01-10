import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from app.services.product_enrichment_service import (
    enrich_product,
    enrich_product_batch,
    _get_gemini_client
)


class TestProductEnrichmentService:

    @patch('app.services.product_enrichment_service.get_settings')
    @patch('app.services.product_enrichment_service.genai')
    def test_get_gemini_client(self, mock_genai, mock_settings):
        mock_settings.return_value.GEMINI_API_KEY = 'test-key'
        mock_settings.return_value.GEMINI_MODEL = 'gemini-pro'
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model

        result = _get_gemini_client()

        mock_genai.configure.assert_called_once_with(api_key='test-key')
        mock_genai.GenerativeModel.assert_called_once_with('gemini-pro')
        assert result == mock_model

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_success(self, mock_settings, mock_get_client):
        # Mock settings
        mock_settings.return_value = Mock()

        # Mock Gemini response
        mock_model = Mock()
        enriched_data = {
            "name": "MacBook Pro 16-inch (M3 Max, 2023)",
            "description": "High-performance laptop with M3 Max chip",
            "category": "Electronics",
            "vendor": "Apple",
            "price": 3499.00,
            "pricing_type": "one_time",
            "product_url": "https://www.apple.com/macbook-pro/",
            "sku": "MRW13LL/A",
            "metadata": {"brand": "Apple", "processor": "M3 Max"},
            "confidence": "high"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("MacBook Pro 16 inch M3 Max")

        assert result["name"] == "MacBook Pro 16-inch (M3 Max, 2023)"
        assert result["vendor"] == "Apple"
        assert result["price"] == 3499.00
        assert result["confidence"] == "high"
        assert isinstance(result["metadata"], dict)

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_with_category(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "Dell XPS 15",
            "description": "Premium laptop",
            "category": "Electronics",
            "vendor": "Dell",
            "price": 1999.00,
            "pricing_type": "one_time",
            "product_url": "https://dell.com/xps",
            "sku": "XPS15-001",
            "metadata": {},
            "confidence": "high"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("Dell XPS 15", category="Electronics")

        assert result["category"] == "Electronics"
        assert result["vendor"] == "Dell"

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_with_context(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "Logitech Mouse",
            "description": "Wireless mouse",
            "category": "Electronics",
            "vendor": "Logitech",
            "price": 99.99,
            "pricing_type": "one_time",
            "product_url": None,
            "sku": None,
            "metadata": {},
            "confidence": "medium"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product(
            "Logitech Mouse",
            category="Electronics",
            additional_context="For gaming"
        )

        assert result["name"] == "Logitech Mouse"

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_handles_markdown_response(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": "Test",
            "vendor": "TestVendor",
            "price": None,
            "pricing_type": None,
            "product_url": None,
            "sku": None,
            "metadata": {},
            "confidence": "low"
        }

        mock_response = Mock()
        # Wrap in markdown code block
        mock_response.text = f"```json\n{json.dumps(enriched_data)}\n```"
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("Test Product")

        assert result["name"] == "Test Product"
        assert result["confidence"] == "low"

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_missing_required_field(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        # Missing 'vendor' field
        enriched_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": "Test",
            "confidence": "low"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        with pytest.raises(Exception, match="Missing required field"):
            enrich_product("Test Product")

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_empty_required_field(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "category": "Test",
            "vendor": "TestVendor",
            "confidence": "low"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        with pytest.raises(Exception, match="Missing required field"):
            enrich_product("Test Product")

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_invalid_json(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        mock_response = Mock()
        mock_response.text = "This is not JSON"
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        with pytest.raises(ValueError, match="Failed to parse Gemini response"):
            enrich_product("Test Product")

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_adds_empty_metadata(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "Test Product",
            "description": "Test description",
            "category": "Test",
            "vendor": "TestVendor",
            "confidence": "medium"
            # No metadata field
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("Test Product")

        assert "metadata" in result
        assert isinstance(result["metadata"], dict)
        assert result["metadata"] == {}

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_gemini_exception(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_model

        with pytest.raises(Exception):
            enrich_product("Test Product")

    @patch('app.services.product_enrichment_service.enrich_product')
    def test_enrich_product_batch_success(self, mock_enrich):
        mock_enrich.side_effect = [
            {"name": "Product 1", "vendor": "Vendor1", "description": "Desc1",
             "category": "Cat1", "confidence": "high", "metadata": {}},
            {"name": "Product 2", "vendor": "Vendor2", "description": "Desc2",
             "category": "Cat2", "confidence": "high", "metadata": {}},
        ]

        results = enrich_product_batch(["Product 1", "Product 2"])

        assert len(results) == 2
        assert results[0]["name"] == "Product 1"
        assert results[1]["name"] == "Product 2"

    @patch('app.services.product_enrichment_service.enrich_product')
    def test_enrich_product_batch_with_error(self, mock_enrich):
        mock_enrich.side_effect = [
            {"name": "Product 1", "vendor": "Vendor1", "description": "Desc1",
             "category": "Cat1", "confidence": "high", "metadata": {}},
            Exception("Enrichment failed"),
            {"name": "Product 3", "vendor": "Vendor3", "description": "Desc3",
             "category": "Cat3", "confidence": "high", "metadata": {}},
        ]

        results = enrich_product_batch(["Product 1", "Product 2", "Product 3"])

        assert len(results) == 3
        assert results[0]["name"] == "Product 1"
        assert results[1]["name"] == "Product 2"  # Original name preserved
        assert results[1]["confidence"] == "low"
        assert "error" in results[1]
        assert results[2]["name"] == "Product 3"

    @patch('app.services.product_enrichment_service.enrich_product')
    def test_enrich_product_batch_empty_list(self, mock_enrich):
        results = enrich_product_batch([])

        assert results == []
        mock_enrich.assert_not_called()

    @patch('app.services.product_enrichment_service.enrich_product')
    def test_enrich_product_batch_all_failures(self, mock_enrich):
        mock_enrich.side_effect = Exception("API Error")

        results = enrich_product_batch(["Product 1", "Product 2"])

        assert len(results) == 2
        assert all(r["confidence"] == "low" for r in results)
        assert all("error" in r for r in results)

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_null_price(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "Custom Product",
            "description": "Custom pricing",
            "category": "Services",
            "vendor": "CustomVendor",
            "price": None,
            "pricing_type": None,
            "product_url": None,
            "sku": None,
            "metadata": {},
            "confidence": "medium"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("Custom Product")

        assert result["price"] is None
        assert result["pricing_type"] is None

    @patch('app.services.product_enrichment_service._get_gemini_client')
    @patch('app.services.product_enrichment_service.get_settings')
    def test_enrich_product_usage_based_pricing(self, mock_settings, mock_get_client):
        mock_settings.return_value = Mock()

        enriched_data = {
            "name": "AWS S3",
            "description": "Cloud storage service",
            "category": "Cloud Services",
            "vendor": "Amazon Web Services",
            "price": 0.023,
            "pricing_type": "usage_based",
            "product_url": "https://aws.amazon.com/s3/",
            "sku": "S3-STANDARD",
            "metadata": {"unit": "per GB/month"},
            "confidence": "high"
        }

        mock_response = Mock()
        mock_response.text = json.dumps(enriched_data)
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_model

        result = enrich_product("AWS S3")

        assert result["pricing_type"] == "usage_based"
        assert result["metadata"]["unit"] == "per GB/month"
