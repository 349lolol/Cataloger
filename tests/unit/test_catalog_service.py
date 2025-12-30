"""
Unit tests for catalog service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services import catalog_service


class TestCatalogService:
    """Test catalog service functions."""

    @patch('app.services.catalog_service.get_supabase_client')
    @patch('app.services.catalog_service.encode_text')
    def test_search_items_calls_rpc(self, mock_encode, mock_supabase):
        """Test that search_items calls Supabase RPC."""
        # Setup mocks
        mock_encode.return_value = [0.1] * 384
        mock_rpc = Mock()
        mock_execute = Mock()
        mock_execute.data = [{'item_name': 'Test Item'}]
        mock_rpc.execute.return_value = mock_execute
        mock_supabase.return_value.rpc.return_value = mock_rpc

        # Call function
        result = catalog_service.search_items(
            query="test query",
            org_id="org-123",
            threshold=0.3,
            limit=10
        )

        # Assertions
        mock_encode.assert_called_once_with("test query")
        mock_supabase.return_value.rpc.assert_called_once()
        assert result == [{'item_name': 'Test Item'}]

    @patch('app.services.catalog_service.get_supabase_client')
    def test_get_item_returns_item(self, mock_supabase):
        """Test get_item returns item data."""
        # Setup mock
        mock_single = Mock()
        mock_execute = Mock()
        mock_execute.data = {'id': 'item-123', 'name': 'Test Item'}
        mock_single.execute.return_value = mock_execute

        mock_eq = Mock()
        mock_eq.single.return_value = mock_single

        mock_select = Mock()
        mock_select.eq.return_value = mock_eq

        mock_supabase.return_value.table.return_value.select.return_value = mock_select

        # Call function
        result = catalog_service.get_item("item-123")

        # Assertions
        assert result == {'id': 'item-123', 'name': 'Test Item'}

    @patch('app.services.catalog_service.get_supabase_client')
    def test_get_item_raises_exception_when_not_found(self, mock_supabase):
        """Test get_item raises exception when item not found."""
        # Setup mock to return None (item not found)
        mock_response = Mock()
        mock_response.data = None

        # Create a mock query that supports chaining
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.single.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        # Call function and expect exception
        with pytest.raises(Exception, match="Catalog item not found"):
            catalog_service.get_item("nonexistent-item")

    @patch('app.services.catalog_service.get_supabase_client')
    def test_list_items_with_status_filter(self, mock_supabase):
        """Test list_items with status filter."""
        # Setup mock
        mock_response = Mock()
        mock_response.data = [{'id': 'item-1', 'status': 'active'}]

        # Create a mock query that supports chaining
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        # Call function
        result = catalog_service.list_items("org-123", status="active", limit=50)

        # Assertions
        assert len(result) == 1
        assert result[0]['status'] == 'active'

    @patch('app.services.catalog_service.get_supabase_admin')
    @patch('app.services.catalog_service.encode_catalog_item')
    def test_create_item_generates_embedding(self, mock_encode, mock_supabase_admin):
        """Test create_item generates and stores embedding."""
        # Setup mocks
        mock_encode.return_value = [0.1] * 384

        # Mock catalog item creation
        mock_item_execute = Mock()
        mock_item_execute.data = [{'id': 'item-123', 'name': 'Test Item'}]
        mock_supabase_admin.return_value.table.return_value.insert.return_value.execute.return_value = mock_item_execute

        # Call function
        result = catalog_service.create_item(
            org_id="org-123",
            name="Test Item",
            description="Test description",
            category="Test",
            metadata={},
            created_by="user-123"
        )

        # Assertions
        mock_encode.assert_called_once()
        assert result['id'] == 'item-123'
        assert result['name'] == 'Test Item'
