"""Unit tests for order tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.orders import register_order_tools
from src.models.orders import SearchOrdersParams
from src.utils.exceptions import GelatoAPIError, OrderNotFoundError


class MockFastMCP:
    """Mock FastMCP class for testing tool registration."""
    
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        """Mock tool decorator."""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


class TestOrderToolRegistration:
    """Test cases for order tool registration."""
    
    def test_register_order_tools(self):
        """Test that order tools are registered correctly."""
        mock_mcp = MockFastMCP()
        
        register_order_tools(mock_mcp)
        
        # Check that expected tools are registered
        expected_tools = ["search_orders", "get_order_summary"]
        
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
            assert callable(mock_mcp.tools[tool_name])


class TestSearchOrdersTool:
    """Test cases for search_orders tool function."""
    
    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
    
    async def test_search_orders_basic(self, sample_search_response):
        """Test search_orders tool with basic parameters."""
        # Set up mock client response
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call the function
        result = await search_orders_func(self.mock_context, limit=10, offset=5)
        
        # Verify the result
        assert isinstance(result, dict)
        assert "orders" in result
        assert "count" in result
        assert "parameters_used" in result
        assert len(result["orders"]) == 1
        assert result["orders"][0]["id"] == "test-order-123"
        assert result["count"] == 1
        
        # Verify client was called with correct parameters
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert isinstance(call_args, SearchOrdersParams)
        assert call_args.limit == 10
        assert call_args.offset == 5
    
    async def test_search_orders_with_filters(self, sample_search_response):
        """Test search_orders tool with various filters."""
        # Set up mock client response
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call the function with filters
        result = await search_orders_func(
            self.mock_context,
            order_types=["order"],
            countries=["US", "CA"],
            currencies=["USD"],
            financial_statuses=["paid"],
            fulfillment_statuses=["shipped"],
            search_text="John Doe",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-01-31T23:59:59Z",
            limit=25
        )
        
        # Verify the result includes filters in parameters
        assert result["parameters_used"]["order_types"] == ["order"]
        assert result["parameters_used"]["countries"] == ["US", "CA"]
        assert result["parameters_used"]["search_text"] == "John Doe"
        
        # Verify client was called with correct parameters
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.order_types == ["order"]
        assert call_args.countries == ["US", "CA"]
        assert call_args.currencies == ["USD"]
        assert call_args.search_text == "John Doe"
        assert call_args.limit == 25
    
    async def test_search_orders_empty_result(self):
        """Test search_orders tool with empty result."""
        from src.models.orders import SearchOrdersResponse
        
        # Set up mock client response with empty results
        empty_response = SearchOrdersResponse(orders=[])
        self.mock_client.search_orders.return_value = empty_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call the function
        result = await search_orders_func(self.mock_context)
        
        # Verify the result
        assert result["count"] == 0
        assert len(result["orders"]) == 0
        assert "No orders found" in result["message"]
    
    async def test_search_orders_api_error(self):
        """Test search_orders tool with API error."""
        # Set up mock client to raise error
        self.mock_client.search_orders.side_effect = GelatoAPIError(
            "Search failed",
            status_code=500
        )
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call the function - should handle error gracefully
        result = await search_orders_func(self.mock_context, limit=10)
        
        # Verify error is handled
        assert isinstance(result, dict)
        assert "error" in result
        assert "Search failed" in str(result["error"])
        assert result.get("status_code") == 500
    
    async def test_search_orders_parameter_validation(self, sample_search_response):
        """Test search_orders tool parameter validation."""
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Test with limit at boundary values
        result = await search_orders_func(self.mock_context, limit=1)
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.limit == 1
        
        result = await search_orders_func(self.mock_context, limit=100)
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.limit == 100


class TestGetOrderSummaryTool:
    """Test cases for get_order_summary tool function."""
    
    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
    
    async def test_get_order_summary_success(self, sample_order_detail):
        """Test get_order_summary tool with successful response."""
        # Set up mock client response
        self.mock_client.get_order.return_value = sample_order_detail
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        get_order_summary_func = mock_mcp.tools["get_order_summary"]
        
        # Call the function
        result = await get_order_summary_func(self.mock_context, "test-order-123")
        
        # Verify the result
        assert isinstance(result, dict)
        assert result["id"] == "test-order-123"
        assert result["orderType"] == "order"
        assert result["currency"] == "USD"
        assert "summary" in result
        
        # Verify client was called correctly
        self.mock_client.get_order.assert_called_once_with("test-order-123")
    
    async def test_get_order_summary_not_found(self):
        """Test get_order_summary tool with order not found."""
        # Set up mock client to raise OrderNotFoundError
        self.mock_client.get_order.side_effect = OrderNotFoundError("missing-order")
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        get_order_summary_func = mock_mcp.tools["get_order_summary"]
        
        # Call the function
        result = await get_order_summary_func(self.mock_context, "missing-order")
        
        # Verify error is handled
        assert isinstance(result, dict)
        assert "error" in result
        assert "Order not found" in str(result["error"])
        assert result["order_id"] == "missing-order"
    
    async def test_get_order_summary_api_error(self):
        """Test get_order_summary tool with API error."""
        # Set up mock client to raise GelatoAPIError
        self.mock_client.get_order.side_effect = GelatoAPIError(
            "Server error",
            status_code=503
        )
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        get_order_summary_func = mock_mcp.tools["get_order_summary"]
        
        # Call the function
        result = await get_order_summary_func(self.mock_context, "test-order")
        
        # Verify error is handled
        assert isinstance(result, dict)
        assert "error" in result
        assert "Server error" in str(result["error"])
        assert result.get("status_code") == 503


class TestToolContextHandling:
    """Test cases for tool context handling."""
    
    def test_tool_context_access(self):
        """Test that tools can access client through context."""
        # This test verifies the context structure expected by tools
        mock_context = MagicMock()
        mock_client = AsyncMock()
        mock_context.request_context.lifespan_context = {"client": mock_client}
        
        # Verify the context structure
        assert "client" in mock_context.request_context.lifespan_context
        assert mock_context.request_context.lifespan_context["client"] is mock_client
    
    def test_tool_without_client_context(self):
        """Test tool behavior when client is not in context."""
        # Create context without client
        mock_context = MagicMock()
        mock_context.request_context.lifespan_context = {}
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call should handle missing client gracefully
        # The actual behavior depends on implementation - might raise KeyError
        with pytest.raises(KeyError, match="client"):
            import asyncio
            asyncio.run(search_orders_func(mock_context))


class TestToolParameterHandling:
    """Test cases for tool parameter handling and validation."""
    
    def setup_method(self):
        """Set up each test."""
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
    
    async def test_search_orders_default_parameters(self, sample_search_response):
        """Test search_orders tool with default parameters."""
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call with only context (all other parameters should use defaults)
        result = await search_orders_func(self.mock_context)
        
        # Verify default parameters were used
        call_args = self.mock_client.search_orders.call_args[0][0]
        assert call_args.limit == 50  # Default limit
        assert call_args.offset == 0  # Default offset
        assert call_args.order_types is None  # Default None
    
    async def test_search_orders_parameter_serialization(self, sample_search_response):
        """Test that tool parameters are properly included in response."""
        self.mock_client.search_orders.return_value = sample_search_response
        
        # Get the tool function
        mock_mcp = MockFastMCP()
        register_order_tools(mock_mcp)
        search_orders_func = mock_mcp.tools["search_orders"]
        
        # Call with specific parameters
        result = await search_orders_func(
            self.mock_context,
            order_types=["order"],
            limit=25,
            search_text="test search"
        )
        
        # Verify parameters are included in response for debugging
        assert "parameters_used" in result
        params = result["parameters_used"]
        assert params["order_types"] == ["order"]
        assert params["limit"] == 25
        assert params["search_text"] == "test search"