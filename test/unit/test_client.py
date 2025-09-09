"""Unit tests for Gelato API client."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.client.gelato_client import GelatoClient
from src.models.orders import CreateOrderRequest, SearchOrdersParams
from src.utils.exceptions import (
    AuthenticationError,
    CatalogNotFoundError,
    GelatoAPIError,
    OrderNotFoundError,
    ValidationError as GelatoValidationError,
)


class TestGelatoClientInitialization:
    """Test cases for GelatoClient initialization."""
    
    def test_valid_initialization(self, test_settings):
        """Test client initializes correctly with valid settings."""
        client = GelatoClient("test_api_key_minimum_10_chars", test_settings)
        
        assert client.api_key == "test_api_key_minimum_10_chars"
        assert client.settings == test_settings
        assert client.logger is not None
        assert client.session is not None
    
    def test_invalid_api_key_initialization(self, test_settings):
        """Test client initialization fails with invalid API key."""
        with pytest.raises(AuthenticationError):
            GelatoClient("short", test_settings)
    
    async def test_context_manager(self, test_settings):
        """Test client works as async context manager."""
        async with GelatoClient("test_api_key_minimum_10_chars", test_settings) as client:
            assert client.api_key == "test_api_key_minimum_10_chars"
        # Should not raise an exception after context exit


class TestListCatalogs:
    """Test cases for list_catalogs method."""
    
    async def test_list_catalogs_standard_response(self, mock_gelato_client, mock_response, sample_catalog):
        """Test list_catalogs with standard array response."""
        # Mock response data
        response_data = [
            {"catalogUid": "cards", "title": "Cards"},
            {"catalogUid": "posters", "title": "Posters"}
        ]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalogs = await mock_gelato_client.list_catalogs()
        
        assert len(catalogs) == 2
        assert catalogs[0].catalogUid == "cards"
        assert catalogs[0].title == "Cards"
        assert catalogs[1].catalogUid == "posters"
        assert catalogs[1].title == "Posters"
    
    async def test_list_catalogs_string_array_response(self, mock_gelato_client, mock_response):
        """Test list_catalogs with string array response (edge case)."""
        response_data = ["cards", "posters", "apparel"]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalogs = await mock_gelato_client.list_catalogs()
        
        assert len(catalogs) == 3
        assert catalogs[0].catalogUid == "cards"
        assert catalogs[0].title == "Cards"  # Should be title-cased
        assert catalogs[1].catalogUid == "posters"
        assert catalogs[1].title == "Posters"
    
    async def test_list_catalogs_wrapped_response(self, mock_gelato_client, mock_response):
        """Test list_catalogs with wrapped response."""
        response_data = {
            "catalogs": [
                {"catalogUid": "mugs", "title": "Mugs"},
                {"catalogUid": "tshirts", "title": "T-Shirts"}
            ],
            "total": 2
        }
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalogs = await mock_gelato_client.list_catalogs()
        
        assert len(catalogs) == 2
        assert catalogs[0].catalogUid == "mugs"
        assert catalogs[1].catalogUid == "tshirts"
    
    async def test_list_catalogs_data_pagination_response(self, mock_gelato_client, mock_response):
        """Test list_catalogs with data/pagination response format."""
        response_data = {
            "data": [
                {"catalogUid": "cards", "title": "Cards"},
                {"catalogUid": "posters", "title": "Posters"}
            ],
            "pagination": {"total": 2, "offset": 0, "limit": 50}
        }
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalogs = await mock_gelato_client.list_catalogs()
        
        assert len(catalogs) == 2
        assert catalogs[0].catalogUid == "cards"
        assert catalogs[1].catalogUid == "posters"
    
    async def test_list_catalogs_empty_response(self, mock_gelato_client, mock_response):
        """Test list_catalogs with empty response."""
        response_data = []
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalogs = await mock_gelato_client.list_catalogs()
        
        assert len(catalogs) == 0
    
    async def test_list_catalogs_unexpected_format(self, mock_gelato_client, mock_response):
        """Test list_catalogs with unexpected response format."""
        response_data = "unexpected_string"
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        with pytest.raises(GelatoAPIError, match="Failed to list catalogs"):
            await mock_gelato_client.list_catalogs()
    
    async def test_list_catalogs_api_error(self, mock_gelato_client):
        """Test list_catalogs handles API errors."""
        mock_gelato_client._request = AsyncMock(
            side_effect=GelatoAPIError("API Error", status_code=500)
        )
        
        with pytest.raises(GelatoAPIError):
            await mock_gelato_client.list_catalogs()


class TestGetCatalog:
    """Test cases for get_catalog method."""
    
    async def test_get_catalog_success(self, mock_gelato_client, mock_response, sample_catalog_detail):
        """Test get_catalog with successful response."""
        response_data = sample_catalog_detail.model_dump()
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        catalog = await mock_gelato_client.get_catalog("test-cards")
        
        assert catalog.catalogUid == "test-cards"
        assert catalog.title == "Test Cards"
        assert len(catalog.productAttributes) == 1
    
    async def test_get_catalog_not_found(self, mock_gelato_client):
        """Test get_catalog with catalog not found."""
        mock_gelato_client._request = AsyncMock(
            side_effect=GelatoAPIError("Not found", status_code=404)
        )
        
        with pytest.raises(CatalogNotFoundError):
            await mock_gelato_client.get_catalog("nonexistent")
    
    async def test_get_catalog_unexpected_format(self, mock_gelato_client, mock_response):
        """Test get_catalog with unexpected response format."""
        response_data = ["unexpected", "array"]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        with pytest.raises(GelatoValidationError):
            await mock_gelato_client.get_catalog("test-catalog")


class TestSearchOrders:
    """Test cases for search_orders method."""
    
    async def test_search_orders_success(self, mock_gelato_client, mock_response, sample_search_response):
        """Test search_orders with successful response."""
        response_data = sample_search_response.model_dump()
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        params = SearchOrdersParams(limit=10)
        result = await mock_gelato_client.search_orders(params)
        
        assert len(result.orders) == 1
        assert result.orders[0].id == "test-order-123"
    
    async def test_search_orders_with_filters(self, mock_gelato_client, mock_response, sample_search_response):
        """Test search_orders with various filters."""
        response_data = sample_search_response.model_dump()
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        params = SearchOrdersParams(
            limit=50,
            offset=0,
            orderTypes=["order"],
            countries=["US"],
            currencies=["USD"]
        )
        result = await mock_gelato_client.search_orders(params)
        
        # Verify the request was made with correct data
        call_args = mock_gelato_client.session.request.call_args
        assert call_args[1]["json"]["limit"] == 50
        assert call_args[1]["json"]["orderTypes"] == ["order"]
        assert call_args[1]["json"]["countries"] == ["US"]
        
        assert len(result.orders) == 1
    
    async def test_search_orders_data_pagination_response(self, mock_gelato_client, mock_response, sample_order_summary):
        """Test search_orders with data/pagination response format."""
        response_data = {
            "data": [sample_order_summary.model_dump()],
            "pagination": {"total": 1, "offset": 0, "limit": 50}
        }
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        params = SearchOrdersParams(limit=10)
        result = await mock_gelato_client.search_orders(params)
        
        assert len(result.orders) == 1
        assert result.orders[0].id == "test-order-123"
    
    async def test_search_orders_unexpected_format(self, mock_gelato_client, mock_response):
        """Test search_orders with unexpected response format."""
        response_data = ["unexpected", "array"]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        params = SearchOrdersParams(limit=10)
        
        with pytest.raises(GelatoAPIError, match="Failed to search orders"):
            await mock_gelato_client.search_orders(params)


class TestGetOrder:
    """Test cases for get_order method."""
    
    async def test_get_order_success(self, mock_gelato_client, mock_response, sample_order_detail):
        """Test get_order with successful response."""
        response_data = sample_order_detail.model_dump()
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        order = await mock_gelato_client.get_order("test-order-123")
        
        assert order.id == "test-order-123"
        assert order.orderType == "order"
        assert order.currency == "USD"
    
    async def test_get_order_not_found(self, mock_gelato_client):
        """Test get_order with order not found."""
        mock_gelato_client._request = AsyncMock(
            side_effect=GelatoAPIError("Not found", status_code=404)
        )
        
        with pytest.raises(OrderNotFoundError):
            await mock_gelato_client.get_order("nonexistent")
    
    async def test_get_order_unexpected_format(self, mock_gelato_client, mock_response):
        """Test get_order with unexpected response format."""
        response_data = ["unexpected", "array"]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        with pytest.raises(GelatoValidationError):
            await mock_gelato_client.get_order("test-order")


class TestTestConnection:
    """Test cases for test_connection method."""
    
    async def test_test_connection_success(self, mock_gelato_client, mock_response):
        """Test test_connection with successful API call."""
        response_data = [{"catalogUid": "cards", "title": "Cards"}]
        
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        result = await mock_gelato_client.test_connection()
        assert result is True
    
    async def test_test_connection_failure(self, mock_gelato_client):
        """Test test_connection with API failure."""
        mock_gelato_client.session.request = AsyncMock(
            side_effect=GelatoAPIError("Connection failed", status_code=401)
        )
        
        with pytest.raises(GelatoAPIError, match="Connection test failed"):
            await mock_gelato_client.test_connection()


class TestClientErrorHandling:
    """Test cases for client error handling."""
    
    async def test_request_retry_logic(self, mock_gelato_client):
        """Test that requests are retried on network errors."""
        # Mock network error that should trigger retry
        from src.utils.exceptions import NetworkError
        
        mock_gelato_client.session.request = AsyncMock(
            side_effect=[
                NetworkError("Connection timeout"),
                NetworkError("Connection timeout"),  # Second retry
                GelatoAPIError("Final error")  # Should not retry this
            ]
        )
        
        # Should eventually raise the GelatoAPIError after retries
        with pytest.raises(GelatoAPIError):
            await mock_gelato_client._request("GET", "http://test.com")
    
    async def test_authentication_error_no_retry(self, mock_gelato_client):
        """Test that authentication errors are not retried."""
        mock_gelato_client.session.request = AsyncMock(
            side_effect=AuthenticationError("Invalid API key")
        )
        
        # Should raise immediately without retries
        with pytest.raises(AuthenticationError):
            await mock_gelato_client._request("GET", "http://test.com")
    
    async def test_close_cleanup(self, test_settings):
        """Test that client cleanup works correctly."""
        client = GelatoClient("test_api_key_minimum_10_chars", test_settings)
        
        # Mock session
        client.session = AsyncMock()
        
        await client.close()
        
        # Verify session was closed
        client.session.aclose.assert_called_once()


class TestCreateOrder:
    """Test cases for create_order method."""
    
    async def test_create_order_success(self, mock_gelato_client, mock_response, sample_order_detail):
        """Test successful order creation."""
        # Mock response
        response_data = sample_order_detail.model_dump()
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        # Create order request
        order_request = CreateOrderRequest(
            orderReferenceId="test-order-123",
            customerReferenceId="test-customer-456",
            currency="USD",
            items=[
                {
                    "itemReferenceId": "item-1",
                    "productUid": "test-product-uid",
                    "quantity": 1,
                    "files": [{"type": "default", "url": "https://example.com/design.png"}]
                }
            ],
            shippingAddress={
                "firstName": "John",
                "lastName": "Doe",
                "addressLine1": "123 Main St",
                "city": "New York",
                "postCode": "10001",
                "country": "US",
                "state": "NY",
                "email": "john@example.com"
            }
        )
        
        # Call method
        result = await mock_gelato_client.create_order(order_request)
        
        # Verify result
        assert result.id == sample_order_detail.id
        assert result.orderReferenceId == sample_order_detail.orderReferenceId
        
        # Verify API call
        mock_gelato_client.session.request.assert_called_once()
        call_args = mock_gelato_client.session.request.call_args
        assert call_args[0][0] == "POST"  # HTTP method
        assert "/v4/orders" in call_args[0][1]  # URL contains correct path
        assert "json" in call_args[1]  # JSON payload provided
    
    async def test_create_order_wrapped_response(self, mock_gelato_client, mock_response, sample_order_detail):
        """Test create_order with wrapped response format."""
        # Mock wrapped response
        wrapped_response = {
            "data": sample_order_detail.model_dump(),
            "pagination": {}
        }
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(wrapped_response)
        )
        
        order_request = CreateOrderRequest(
            orderReferenceId="test-order-123",
            customerReferenceId="test-customer-456",
            currency="USD",
            items=[
                {
                    "itemReferenceId": "item-1",
                    "productUid": "test-product-uid",
                    "quantity": 1
                }
            ],
            shippingAddress={
                "firstName": "John",
                "lastName": "Doe",
                "addressLine1": "123 Main St",
                "city": "New York",
                "postCode": "10001",
                "country": "US",
                "email": "john@example.com"
            }
        )
        
        result = await mock_gelato_client.create_order(order_request)
        
        assert result.id == sample_order_detail.id
        assert result.orderReferenceId == sample_order_detail.orderReferenceId
    
    async def test_create_order_api_error(self, mock_gelato_client):
        """Test create_order with API error."""
        # Mock API error
        mock_gelato_client.session.request = AsyncMock(
            side_effect=GelatoAPIError("API Error", status_code=400)
        )
        
        order_request = CreateOrderRequest(
            orderReferenceId="test-order-123",
            customerReferenceId="test-customer-456",
            currency="USD",
            items=[
                {
                    "itemReferenceId": "item-1",
                    "productUid": "test-product-uid",
                    "quantity": 1
                }
            ],
            shippingAddress={
                "firstName": "John",
                "lastName": "Doe",
                "addressLine1": "123 Main St",
                "city": "New York",
                "postCode": "10001",
                "country": "US",
                "email": "john@example.com"
            }
        )
        
        with pytest.raises(GelatoAPIError):
            await mock_gelato_client.create_order(order_request)
    
    async def test_create_order_validation_error(self, mock_gelato_client, mock_response):
        """Test create_order with invalid response format."""
        # Mock invalid response (non-dict)
        response_data = "invalid response"
        mock_gelato_client.session.request = AsyncMock(
            return_value=mock_response(response_data)
        )
        
        order_request = CreateOrderRequest(
            orderReferenceId="test-order-123",
            customerReferenceId="test-customer-456",
            currency="USD",
            items=[
                {
                    "itemReferenceId": "item-1",
                    "productUid": "test-product-uid",
                    "quantity": 1
                }
            ],
            shippingAddress={
                "firstName": "John",
                "lastName": "Doe",
                "addressLine1": "123 Main St",
                "city": "New York",
                "postCode": "10001",
                "country": "US",
                "email": "john@example.com"
            }
        )
        
        with pytest.raises(GelatoValidationError):
            await mock_gelato_client.create_order(order_request)