import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services import catalog_service


class TestCatalogService:

    @patch('app.services.catalog_service.get_supabase_admin')
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

    @patch('app.services.catalog_service.get_supabase_admin')
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

    @patch('app.services.catalog_service.get_supabase_admin')
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

    @patch('app.services.catalog_service.get_supabase_admin')
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

    @patch('app.services.catalog_service._get_client')
    @patch('app.services.catalog_service.encode_catalog_item')
    @patch('app.services.catalog_service.log_event')
    def test_create_item_generates_embedding(self, mock_log, mock_encode, mock_get_client):
        """Test create_item generates embedding and calls RPC."""
        # Setup mocks
        mock_encode.return_value = [0.1] * 768

        # Mock RPC response
        mock_response = Mock()
        mock_response.data = {'id': 'item-123', 'name': 'Test Item', 'org_id': 'org-123'}

        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client

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
        mock_encode.assert_called_once_with("Test Item", "Test description", "Test")
        mock_client.rpc.assert_called_once_with(
            'create_catalog_item_with_embedding',
            {
                'p_org_id': 'org-123',
                'p_name': 'Test Item',
                'p_description': 'Test description',
                'p_category': 'Test',
                'p_created_by': 'user-123',
                'p_status': 'active',
                'p_price': None,
                'p_pricing_type': None,
                'p_product_url': None,
                'p_vendor': None,
                'p_sku': None,
                'p_metadata': {},
                'p_embedding': [0.1] * 768
            }
        )
        assert result['id'] == 'item-123'
        assert result['name'] == 'Test Item'

    @patch('app.services.catalog_service.get_supabase_admin')
    def test_check_and_repair_embeddings_no_items(self, mock_supabase_admin):
        """Test check_and_repair_embeddings with no items."""
        mock_response = Mock()
        mock_response.data = []

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase_admin.return_value.table.return_value.select.return_value = mock_query

        result = catalog_service.check_and_repair_embeddings("org-123")

        assert result["total_items"] == 0
        assert result["repaired"] == 0

    @patch('app.services.catalog_service.get_supabase_admin')
    @patch('app.services.catalog_service.encode_catalog_item')
    def test_check_and_repair_embeddings_repairs_missing(self, mock_encode, mock_supabase_admin):
        """Test check_and_repair_embeddings repairs missing embeddings."""
        mock_encode.return_value = [0.1] * 384

        # Mock items response
        items_data = [
            {'id': 'item-1', 'name': 'Item 1', 'description': 'Desc 1', 'category': 'Cat1'},
            {'id': 'item-2', 'name': 'Item 2', 'description': 'Desc 2', 'category': 'Cat2'}
        ]

        # Mock embeddings response (only item-1 has embedding)
        embeddings_data = [{'catalog_item_id': 'item-1'}]

        mock_admin = mock_supabase_admin.return_value

        # Setup table().select() to return different results
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_query = Mock()
            mock_query.eq.return_value = mock_query
            mock_query.in_.return_value = mock_query
            mock_query.select.return_value = mock_query

            if table_name == 'catalog_items':
                mock_response = Mock()
                mock_response.data = items_data
                mock_query.execute.return_value = mock_response
            elif table_name == 'catalog_item_embeddings':
                if hasattr(mock_query, '_is_select'):
                    mock_response = Mock()
                    mock_response.data = embeddings_data
                    mock_query.execute.return_value = mock_response
                else:
                    mock_response = Mock()
                    mock_response.data = [{'catalog_item_id': 'item-2'}]
                    mock_insert = Mock()
                    mock_insert.execute.return_value = mock_response
                    mock_table.insert = Mock(return_value=mock_insert)

            mock_table.select = Mock(return_value=mock_query)
            mock_query._is_select = True
            return mock_table

        mock_admin.table = Mock(side_effect=table_side_effect)

        result = catalog_service.check_and_repair_embeddings("org-123")

        assert result["total_items"] == 2
        assert result["items_without_embeddings"] == 1
        assert result["repaired"] == 1

    @patch('app.services.catalog_service._get_client')
    @patch('app.services.catalog_service.encode_catalog_item')
    @patch('app.services.catalog_service.log_event')
    def test_create_item_with_all_fields(self, mock_log, mock_encode, mock_get_client):
        """Test create_item with all optional fields."""
        mock_encode.return_value = [0.1] * 768

        item_data = {
            'id': 'item-123',
            'name': 'Test Product',
            'org_id': 'org-123',
            'price': 99.99,
            'pricing_type': 'one_time',
            'vendor': 'TestVendor',
            'sku': 'TEST-123',
            'product_url': 'https://example.com'
        }

        mock_response = Mock()
        mock_response.data = item_data

        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = catalog_service.create_item(
            org_id="org-123",
            name="Test Product",
            description="Test description",
            category="Electronics",
            created_by="user-123",
            price=99.99,
            pricing_type="one_time",
            vendor="TestVendor",
            sku="TEST-123",
            product_url="https://example.com",
            metadata={"key": "value"}
        )

        assert result['id'] == 'item-123'
        mock_client.rpc.assert_called_once_with(
            'create_catalog_item_with_embedding',
            {
                'p_org_id': 'org-123',
                'p_name': 'Test Product',
                'p_description': 'Test description',
                'p_category': 'Electronics',
                'p_created_by': 'user-123',
                'p_status': 'active',
                'p_price': 99.99,
                'p_pricing_type': 'one_time',
                'p_product_url': 'https://example.com',
                'p_vendor': 'TestVendor',
                'p_sku': 'TEST-123',
                'p_metadata': {"key": "value"},
                'p_embedding': [0.1] * 768
            }
        )
        mock_log.assert_called_once()

    @patch('app.services.catalog_service._get_client')
    @patch('app.services.catalog_service.encode_catalog_item')
    def test_create_item_embedding_fails(self, mock_encode, mock_get_client):
        """Test create_item raises error when embedding generation fails."""
        mock_encode.side_effect = Exception("Embedding failed")

        with pytest.raises(Exception, match="Embedding failed"):
            catalog_service.create_item(
                org_id="org-123",
                name="Test Item",
                description="Test description",
                category="Test",
                created_by="user-123"
            )

    @patch('app.services.catalog_service._get_client')
    @patch('app.services.catalog_service.encode_catalog_item')
    def test_create_item_rpc_fails(self, mock_encode, mock_get_client):
        """Test create_item raises error when RPC fails (atomic rollback)."""
        mock_encode.return_value = [0.1] * 768

        # Mock RPC failure (empty data means failure)
        mock_response = Mock()
        mock_response.data = None

        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(Exception, match="Database temporarily unavailable"):
            catalog_service.create_item(
                org_id="org-123",
                name="Test Item",
                description="Test description",
                category="Test",
                created_by="user-123"
            )

    @patch('app.services.catalog_service.get_supabase_admin')
    @patch('app.services.catalog_service.encode_catalog_item')
    @patch('app.services.catalog_service.log_event')
    def test_update_item_regenerates_embedding(self, mock_log, mock_encode, mock_supabase_admin):
        """Test update_item regenerates embedding when content changes."""
        mock_encode.return_value = [0.2] * 384

        updated_data = {
            'id': 'item-123',
            'name': 'Updated Item',
            'description': 'Updated description',
            'category': 'Updated',
            'org_id': 'org-123'
        }

        mock_update_execute = Mock()
        mock_update_execute.data = [updated_data]

        mock_embed_execute = Mock()
        mock_embed_execute.data = [{'embedding': [0.2] * 384}]

        mock_admin = mock_supabase_admin.return_value

        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == 'catalog_items':
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute.return_value = mock_update_execute
                mock_update.eq.return_value = mock_eq
                mock_table.update.return_value = mock_update
            elif table_name == 'catalog_item_embeddings':
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute.return_value = mock_embed_execute
                mock_update.eq.return_value = mock_eq
                mock_table.update.return_value = mock_update
            return mock_table

        mock_admin.table = Mock(side_effect=table_side_effect)

        result = catalog_service.update_item(
            "item-123",
            {'name': 'Updated Item', 'description': 'Updated description'},
            updated_by="user-123"
        )

        assert result['name'] == 'Updated Item'
        mock_encode.assert_called_once()
        mock_log.assert_called_once()

    @patch('app.services.catalog_service.get_supabase_admin')
    def test_update_item_without_content_change(self, mock_supabase_admin):
        """Test update_item without content fields doesn't regenerate embedding."""
        updated_data = {
            'id': 'item-123',
            'price': 199.99,
            'org_id': 'org-123'
        }

        mock_update_execute = Mock()
        mock_update_execute.data = [updated_data]

        mock_update = Mock()
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_update_execute
        mock_update.eq.return_value = mock_eq

        mock_table = Mock()
        mock_table.update.return_value = mock_update

        mock_supabase_admin.return_value.table.return_value = mock_table

        result = catalog_service.update_item("item-123", {'price': 199.99})

        assert result['price'] == 199.99

    @patch('app.services.catalog_service.get_supabase_admin')
    def test_list_items_without_status_filter(self, mock_supabase):
        """Test list_items without status filter."""
        mock_response = Mock()
        mock_response.data = [
            {'id': 'item-1', 'status': 'active'},
            {'id': 'item-2', 'status': 'deprecated'}
        ]

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        result = catalog_service.list_items("org-123")

        assert len(result) == 2

    @patch('app.services.catalog_service.get_supabase_admin')
    @patch('app.services.catalog_service.encode_text')
    def test_search_items_empty_results(self, mock_encode, mock_supabase):
        """Test search_items returns empty list when no matches."""
        mock_encode.return_value = [0.1] * 384

        mock_execute = Mock()
        mock_execute.data = []

        mock_rpc = Mock()
        mock_rpc.execute.return_value = mock_execute

        mock_supabase.return_value.rpc.return_value = mock_rpc

        result = catalog_service.search_items("nonexistent", "org-123")

        assert result == []

    @patch('app.services.catalog_service.get_supabase_admin')
    def test_update_item_fails(self, mock_supabase_admin):
        """Test update_item raises exception when update fails."""
        mock_response = Mock()
        mock_response.data = None

        mock_eq = Mock()
        mock_eq.execute.return_value = mock_response

        mock_update = Mock()
        mock_update.eq.return_value = mock_eq

        mock_table = Mock()
        mock_table.update.return_value = mock_update

        mock_supabase_admin.return_value.table.return_value = mock_table

        with pytest.raises(Exception, match="Database temporarily unavailable"):
            catalog_service.update_item("item-123", {'name': 'New Name'})
