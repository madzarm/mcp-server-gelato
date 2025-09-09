"""Unit tests for order resources."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.resources.orders import register_order_resources
from src.utils.client_registry import client_registry
from src.utils.exceptions import GelatoAPIError, OrderNotFoundError


class MockFastMCP:
    """Mock FastMCP class for testing resource registration."""
    
    def __init__(self):
        self.resources = {}
    
    def resource(self, uri_pattern):
        """Mock resource decorator."""
        def decorator(func):
            self.resources[uri_pattern] = func
            return func
        return decorator


class TestOrderResourceRegistration:
    """Test cases for order resource registration."""
    
    def test_register_order_resources(self):
        """Test that order resources are registered correctly."""
        mock_mcp = MockFastMCP()
        
        register_order_resources(mock_mcp)
        
        # Check that all expected resources are registered
        expected_resources = [
            "orders://{order_id}",
            "orders://recent",
            "orders://drafts"
        ]
        
        for resource_uri in expected_resources:
            assert resource_uri in mock_mcp.resources
            assert callable(mock_mcp.resources[resource_uri])


class TestGetOrderResource:
    """Test cases for get_order resource function."""
    
    def setup_method(self):
        """Set up each test with a mock client."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_get_order_success(self, sample_order_detail):
        """Test get_order resource with successful order retrieval."""
        # Set up mock
        self.mock_client.get_order.return_value = sample_order_detail
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call the function
        result = await get_order_func("test-order-123")
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "test-order-123"
        assert parsed_result["orderType"] == "order"
        assert parsed_result["currency"] == "USD"
        
        # Verify client was called correctly
        self.mock_client.get_order.assert_called_once_with("test-order-123")
    
    async def test_get_order_not_found(self):
        """Test get_order resource with order not found error."""
        # Set up mock to raise OrderNotFoundError
        self.mock_client.get_order.side_effect = OrderNotFoundError("missing-order")
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call the function
        result = await get_order_func("missing-order")
        
        # Verify error response
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "Order not found: missing-order" in parsed_result["error"]
        assert parsed_result["order_id"] == "missing-order"
    
    async def test_get_order_api_error(self):
        """Test get_order resource with generic API error."""
        # Set up mock to raise GelatoAPIError
        self.mock_client.get_order.side_effect = GelatoAPIError(
            "Server error", 
            status_code=500
        )
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call the function
        result = await get_order_func("test-order")
        
        # Verify error response
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert parsed_result["error"] == "Failed to fetch order"
        assert parsed_result["order_id"] == "test-order"
        assert parsed_result["status_code"] == 500


class TestGetRecentOrdersResource:
    """Test cases for get_recent_orders resource function."""
    
    def setup_method(self):
        """Set up each test with a mock client."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_get_recent_orders_success(self, sample_search_response):
        """Test get_recent_orders resource with successful response."""
        # Set up mock
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_recent_orders_func = mock_mcp.resources["orders://recent"]
        
        # Call the function
        result = await get_recent_orders_func()
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "orders" in parsed_result
        assert "count" in parsed_result
        assert "description" in parsed_result
        assert len(parsed_result["orders"]) == 1
        assert parsed_result["orders"][0]["id"] == "test-order-123"
        assert "10 most recent orders" in parsed_result["description"]
        
        # Verify client was called with correct parameters
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.limit == 10
        assert call_args.offset == 0
    
    async def test_get_recent_orders_empty_response(self):
        """Test get_recent_orders resource with empty response."""
        from src.models.orders import SearchOrdersResponse
        
        # Set up mock with empty response
        empty_response = SearchOrdersResponse(orders=[])
        self.mock_client.search_orders.return_value = empty_response
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_recent_orders_func = mock_mcp.resources["orders://recent"]
        
        # Call the function
        result = await get_recent_orders_func()
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert parsed_result["count"] == 0
        assert len(parsed_result["orders"]) == 0
    
    async def test_get_recent_orders_api_error(self):
        """Test get_recent_orders resource with API error."""
        # Set up mock to raise GelatoAPIError
        self.mock_client.search_orders.side_effect = GelatoAPIError(
            "Search failed",
            status_code=503
        )
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_recent_orders_func = mock_mcp.resources["orders://recent"]
        
        # Call the function
        result = await get_recent_orders_func()
        
        # Verify error response
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert parsed_result["error"] == "Failed to fetch recent orders"
        assert parsed_result["status_code"] == 503


class TestGetDraftOrdersResource:
    """Test cases for get_draft_orders resource function."""
    
    def setup_method(self):
        """Set up each test with a mock client."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_get_draft_orders_success(self):
        """Test get_draft_orders resource with successful response."""
        from src.models.orders import SearchOrdersResponse, OrderSummary
        from datetime import datetime
        
        # Create draft order
        draft_order = OrderSummary(
            id="draft-order-123",
            orderType="draft",
            orderReferenceId="draft-ref-123",
            customerReferenceId="cust-123",
            fulfillmentStatus="draft",
            financialStatus="draft",
            currency="USD",
            createdAt=datetime(2024, 1, 1, 10, 0, 0),
            updatedAt=datetime(2024, 1, 1, 10, 0, 0)
        )
        
        draft_response = SearchOrdersResponse(orders=[draft_order])
        self.mock_client.search_orders.return_value = draft_response
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_draft_orders_func = mock_mcp.resources["orders://drafts"]
        
        # Call the function
        result = await get_draft_orders_func()
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "orders" in parsed_result
        assert len(parsed_result["orders"]) == 1
        assert parsed_result["orders"][0]["id"] == "draft-order-123"
        assert parsed_result["orders"][0]["orderType"] == "draft"
        assert "draft orders" in parsed_result["description"]
        
        # Verify client was called with correct parameters
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.order_types == ["draft"]
        assert call_args.limit == 50


class TestResourceErrorHandling:
    """Test cases for resource error handling."""
    
    def setup_method(self):
        """Set up each test."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_resource_with_no_client(self):
        """Test resource function when no client is registered."""
        # Clear the client
        client_registry.clear_client()
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call should raise RuntimeError
        with pytest.raises(RuntimeError, match="No Gelato client registered"):
            await get_order_func("test-order")
    
    async def test_resource_json_serialization_error(self):
        """Test resource function when JSON serialization fails."""
        # Create a mock order that can't be serialized
        mock_order = MagicMock()
        mock_order.model_dump.side_effect = Exception("Serialization error")
        
        self.mock_client.get_order.return_value = mock_order
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call should handle the error gracefully
        # The actual implementation might catch this and return an error response
        with pytest.raises(Exception, match="Serialization error"):
            await get_order_func("test-order")


class TestResourceResponseFormats:
    """Test cases for resource response format validation."""
    
    def setup_method(self):
        """Set up each test with a mock client."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_get_order_response_format(self, sample_order_detail):
        """Test that get_order resource returns properly formatted JSON."""
        self.mock_client.get_order.return_value = sample_order_detail
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call the function
        result = await get_order_func("test-order-123")
        
        # Verify it's valid JSON
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        
        # Verify it contains expected fields
        required_fields = ["id", "orderType", "orderReferenceId", "customerReferenceId"]
        for field in required_fields:
            assert field in parsed_result
    
    async def test_error_response_format(self):
        """Test that error responses have consistent format."""
        self.mock_client.get_order.side_effect = OrderNotFoundError("missing-order")
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_order_func = mock_mcp.resources["orders://{order_id}"]
        
        # Call the function
        result = await get_order_func("missing-order")
        
        # Verify error response format
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        
        # Verify error response structure
        assert "error" in parsed_result
        assert "message" in parsed_result
        assert "order_id" in parsed_result
        assert parsed_result["order_id"] == "missing-order"
    
    async def test_recent_orders_response_format(self, sample_search_response):
        """Test that recent orders resource returns properly formatted JSON."""
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_order_resources(mock_mcp)
        get_recent_orders_func = mock_mcp.resources["orders://recent"]
        
        # Call the function
        result = await get_recent_orders_func()
        
        # Verify response format
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        
        # Verify response structure
        assert "orders" in parsed_result
        assert "count" in parsed_result
        assert "description" in parsed_result
        assert isinstance(parsed_result["orders"], list)
        assert isinstance(parsed_result["count"], int)
        assert isinstance(parsed_result["description"], str)