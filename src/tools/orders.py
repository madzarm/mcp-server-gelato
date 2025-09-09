"""Order-related MCP tools."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from ..client.gelato_client import GelatoClient
from ..models.orders import SearchOrdersParams
from ..utils.exceptions import GelatoAPIError


def register_order_tools(mcp: FastMCP):
    """Register all order-related tools with the MCP server."""
    
    @mcp.tool()
    async def search_orders(
        ctx: Context,
        order_types: Optional[List[Literal["order", "draft"]]] = None,
        countries: Optional[List[str]] = None,
        currencies: Optional[List[str]] = None,
        financial_statuses: Optional[List[str]] = None,
        fulfillment_statuses: Optional[List[str]] = None,
        search_text: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = Field(default=50, le=100, description="Maximum results per page (max 100)"),
        offset: int = Field(default=0, ge=0, description="Offset for pagination"),
        order_reference_ids: Optional[List[str]] = None,
        store_ids: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search and filter Gelato orders with advanced criteria.
        
        This tool allows you to search orders using multiple filters:
        - order_types: Filter by order type ("order" for production orders, "draft" for draft orders)  
        - countries: Filter by shipping country (2-letter ISO codes like "US", "DE", "CA")
        - currencies: Filter by order currency (ISO codes like "USD", "EUR", "GBP")
        - financial_statuses: Filter by payment status ("draft", "pending", "paid", "canceled", etc.)
        - fulfillment_statuses: Filter by fulfillment status ("created", "printed", "shipped", etc.)
        - search_text: Search in customer names and order reference IDs
        - start_date: Show orders created after this date (ISO 8601 format: 2024-01-01T00:00:00Z)
        - end_date: Show orders created before this date (ISO 8601 format: 2024-12-31T23:59:59Z)
        - limit: Maximum number of results (default 50, max 100)
        - offset: Number of results to skip for pagination
        - order_reference_ids: Filter by your internal order IDs
        - store_ids: Filter by e-commerce store IDs
        - channels: Filter by order channel ("api", "shopify", "etsy", "ui")
        
        Examples:
        - Search recent orders: search_orders(limit=10)
        - Find draft orders: search_orders(order_types=["draft"])
        - Find US orders: search_orders(countries=["US"])
        - Search by customer name: search_orders(search_text="John Smith")
        - Date range search: search_orders(start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T23:59:59Z")
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]
        
        try:
            # Parse date strings if provided
            parsed_start_date = None
            parsed_end_date = None
            
            if start_date:
                try:
                    parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "message": f"Invalid start_date format: {start_date}. Use ISO 8601 format like '2024-01-01T00:00:00Z'",
                            "operation": "search_orders"
                        }
                    }
            
            if end_date:
                try:
                    parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "message": f"Invalid end_date format: {end_date}. Use ISO 8601 format like '2024-12-31T23:59:59Z'",
                            "operation": "search_orders"
                        }
                    }
            
            # Build search parameters
            search_params = SearchOrdersParams(
                orderTypes=order_types,
                countries=countries,
                currencies=currencies,
                financialStatuses=financial_statuses,
                fulfillmentStatuses=fulfillment_statuses,
                search=search_text,
                startDate=parsed_start_date,
                endDate=parsed_end_date,
                limit=limit,
                offset=offset,
                orderReferenceIds=order_reference_ids,
                storeIds=store_ids,
                channels=channels
            )
            
            # Execute search
            result = await client.search_orders(search_params)
            
            # Format response
            orders_data = [order.model_dump() for order in result.orders]
            
            response = {
                "success": True,
                "data": {
                    "orders": orders_data,
                    "pagination": {
                        "count": len(orders_data),
                        "offset": offset,
                        "limit": limit,
                        "has_more": len(orders_data) == limit
                    },
                    "search_params": search_params.model_dump(exclude_none=True)
                }
            }
            
            # Add helpful message based on results
            if len(orders_data) == 0:
                response["message"] = "No orders found matching the search criteria"
            elif len(orders_data) == limit:
                response["message"] = f"Found {len(orders_data)} orders (may have more results, use offset={offset + limit} to get next page)"
            else:
                response["message"] = f"Found {len(orders_data)} orders matching the search criteria"
            
            return response
        
        except GelatoAPIError as e:
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "search_orders",
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }
    
    @mcp.tool()
    async def get_order_summary(ctx: Context, order_id: str) -> Dict[str, Any]:
        """
        Get a quick summary of an order (alternative to the orders:// resource).
        
        This tool provides the same information as the orders://{order_id} resource
        but returns it as a tool result rather than loading it into context.
        Use this when you want to retrieve order information as part of an operation
        rather than for context loading.
        
        Args:
            order_id: The Gelato order ID to retrieve
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]
        
        try:
            order = await client.get_order(order_id)
            
            return {
                "success": True,
                "data": order.model_dump(),
                "message": f"Retrieved order {order_id} successfully"
            }
        
        except GelatoAPIError as e:
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": f"get_order_summary for order {order_id}",
                    "order_id": order_id,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }