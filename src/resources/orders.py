"""Order-related MCP resources."""

import json
from mcp.server.fastmcp import FastMCP

from ..models.orders import SearchOrdersParams
from ..utils.client_registry import client_registry
from ..utils.exceptions import GelatoAPIError, OrderNotFoundError


def register_order_resources(mcp: FastMCP):
    """Register all order-related resources with the MCP server."""
    
    @mcp.resource("orders://{order_id}")
    async def get_order(order_id: str) -> str:
        """
        Get detailed information about a specific order.
        
        This resource exposes comprehensive order data including items, 
        shipping information, billing details, and receipts.
        """
        client = client_registry.get_client()
        
        try:
            order = await client.get_order(order_id)
            return json.dumps(order.model_dump(), indent=2, default=str)
        
        except OrderNotFoundError as e:
            error_response = {
                "error": f"Order not found: {order_id}",
                "message": str(e),
                "order_id": order_id
            }
            return json.dumps(error_response, indent=2)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch order",
                "message": str(e),
                "order_id": order_id,
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
    
    @mcp.resource("orders://recent")
    async def get_recent_orders() -> str:
        """
        Get the 10 most recent orders.
        
        This resource provides a quick way to access recently created orders,
        useful for getting context on current order activity.
        """
        client = client_registry.get_client()
        
        try:
            # Search for recent orders with limit 10
            search_params = SearchOrdersParams(
                limit=10,
                offset=0
            )
            
            result = await client.search_orders(search_params)
            
            response_data = {
                "orders": [order.model_dump() for order in result.orders],
                "count": len(result.orders),
                "description": "10 most recent orders"
            }
            
            return json.dumps(response_data, indent=2, default=str)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch recent orders",
                "message": str(e),
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
    
    @mcp.resource("orders://drafts")
    async def get_draft_orders() -> str:
        """
        Get all draft orders.
        
        Draft orders can be edited and haven't been sent to production yet.
        This resource helps you see orders that are still being prepared.
        """
        client = client_registry.get_client()
        
        try:
            # Search for draft orders
            search_params = SearchOrdersParams(
                orderTypes=["draft"],
                limit=50
            )
            
            result = await client.search_orders(search_params)
            
            response_data = {
                "draft_orders": [order.model_dump() for order in result.orders],
                "count": len(result.orders),
                "description": "All draft orders (not yet in production)"
            }
            
            return json.dumps(response_data, indent=2, default=str)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch draft orders",
                "message": str(e),
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)