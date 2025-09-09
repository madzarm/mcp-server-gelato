"""Order-related MCP tools."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from ..client.gelato_client import GelatoClient
from ..models.orders import CreateOrderRequest, CreateOrderItem, CreateOrderFile, MetadataObject, SearchOrdersParams
from ..models.common import ShippingAddress, ReturnAddress
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
        limit: int = 50,
        offset: int = 0,
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
        - offset: Number of results to skip for pagination (default 0, min 0)
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
            
            # Validate parameters
            if limit < 1 or limit > 100:
                return {
                    "success": False,
                    "error": {
                        "message": f"Invalid limit: {limit}. Must be between 1 and 100.",
                        "operation": "search_orders"
                    }
                }
            
            if offset < 0:
                return {
                    "success": False,
                    "error": {
                        "message": f"Invalid offset: {offset}. Must be 0 or greater.",
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
    
    @mcp.tool()
    async def create_order(
        ctx: Context,
        order_reference_id: str,
        customer_reference_id: str,
        currency: str,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        order_type: Optional[Literal["order", "draft"]] = "order",
        shipment_method_uid: Optional[str] = None,
        return_address: Optional[Dict[str, Any]] = None,
        metadata: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Gelato order.
        
        This tool creates either a production order or a draft order using the Gelato API.
        
        Args:
            ctx: MCP context for logging and client access
            order_reference_id: Your internal order ID (must be unique)
            customer_reference_id: Your internal customer ID
            currency: Currency ISO code (e.g., "USD", "EUR", "GBP")
            items: List of order items, each containing:
                - itemReferenceId (str): Your internal item ID (unique within order)
                - productUid (str): Product UID (e.g., "apparel_product_gca_t-shirt...")
                - quantity (int): Number of items to produce
                - files (list, optional): Print files with type and URL
                - pageCount (int, optional): For multipage products
            shipping_address: Shipping address dictionary containing:
                - firstName (str): Recipient first name (max 25 chars)
                - lastName (str): Recipient last name (max 25 chars)  
                - addressLine1 (str): First address line (max 35 chars)
                - city (str): City name (max 30 chars)
                - postCode (str): Postal code (max 15 chars)
                - country (str): 2-character ISO country code (e.g., "US", "GB")
                - email (str): Email address
                - addressLine2 (str, optional): Second address line
                - companyName (str, optional): Company name (max 60 chars)
                - state (str, optional): State code (required for US, CA, AU)
                - phone (str, optional): Phone number in E.123 format
                - isBusiness (bool, optional): Whether recipient is business
                - federalTaxId (str, optional): Federal tax ID (required for Brazil)
                - stateTaxId (str, optional): State tax ID (required for Brazilian companies)
                - registrationStateCode (str, optional): Registration state code
            order_type: "order" for production orders, "draft" for draft orders
            shipment_method_uid: Shipping method ("normal", "standard", "express", or specific UID)
            return_address: Optional return address (same format as shipping_address)
            metadata: Optional key-value pairs for additional order information (max 20)
        
        Returns:
            Dict containing the created order details or error information
            
        Examples:
            Simple t-shirt order:
            create_order(
                order_reference_id="order-123",
                customer_reference_id="customer-456", 
                currency="USD",
                items=[{
                    "itemReferenceId": "item-1",
                    "productUid": "apparel_product_gca_t-shirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_s_gco_white_gpr_4-4",
                    "quantity": 1,
                    "files": [{"type": "default", "url": "https://example.com/design.png"}]
                }],
                shipping_address={
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
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]
        
        try:
            # Log the operation start
            await ctx.info(f"Creating order: {order_reference_id} for customer: {customer_reference_id}")
            
            # Parse and validate items
            order_items = []
            for item_data in items:
                files = None
                if "files" in item_data and item_data["files"]:
                    files = [CreateOrderFile(**file_data) for file_data in item_data["files"]]
                
                order_item = CreateOrderItem(
                    itemReferenceId=item_data["itemReferenceId"],
                    productUid=item_data["productUid"],
                    quantity=item_data["quantity"],
                    files=files,
                    pageCount=item_data.get("pageCount"),
                    adjustProductUidByFileTypes=item_data.get("adjustProductUidByFileTypes")
                )
                order_items.append(order_item)
            
            # Parse shipping address
            shipping_addr = ShippingAddress(**shipping_address)
            
            # Parse optional return address
            return_addr = None
            if return_address:
                return_addr = ReturnAddress(**return_address)
            
            # Parse optional metadata
            metadata_objects = None
            if metadata:
                metadata_objects = [MetadataObject(**item) for item in metadata]
            
            # Create the order request
            order_request = CreateOrderRequest(
                orderType=order_type,
                orderReferenceId=order_reference_id,
                customerReferenceId=customer_reference_id,
                currency=currency,
                items=order_items,
                shippingAddress=shipping_addr,
                shipmentMethodUid=shipment_method_uid,
                returnAddress=return_addr,
                metadata=metadata_objects
            )
            
            # Create the order via API
            await ctx.info("Sending order creation request to Gelato API...")
            result = await client.create_order(order_request)
            
            await ctx.info(f"Order created successfully with ID: {result.id}")
            
            return {
                "success": True,
                "data": result.model_dump(),
                "message": f"Order {result.id} created successfully",
                "order_id": result.id,
                "order_reference_id": order_reference_id,
                "fulfillment_status": result.fulfillmentStatus,
                "financial_status": result.financialStatus
            }
        
        except GelatoAPIError as e:
            error_message = f"Failed to create order: {str(e)}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "create_order",
                    "order_reference_id": order_reference_id,
                    "customer_reference_id": customer_reference_id,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }
        
        except Exception as e:
            error_message = f"Unexpected error creating order: {str(e)}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "create_order",
                    "order_reference_id": order_reference_id,
                    "customer_reference_id": customer_reference_id
                }
            }