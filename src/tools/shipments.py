"""Shipment-related MCP tools."""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context, FastMCP

from ..client.gelato_client import GelatoClient
from ..utils.exceptions import GelatoAPIError


def register_shipment_tools(mcp: FastMCP):
    """Register all shipment-related tools with the MCP server."""

    @mcp.tool()
    async def list_shipment_methods(
        ctx: Context,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available shipment methods for Gelato orders.

        This tool retrieves all available shipment methods that can be used
        for delivering Gelato orders. You can optionally filter by destination
        country to see only methods available for that specific country.

        Args:
            country: Optional destination country ISO code (e.g., "US", "GB", "DE", "CA")
                    If provided, only methods that support this destination are returned.
                    Use standard 2-letter ISO country codes.

        Returns:
            Dictionary containing:
            - success: Boolean indicating if the request was successful
            - data: Object containing:
              - shipment_methods: List of available shipment methods with details:
                - shipmentMethodUid: Unique identifier (e.g., "dhl_global_parcel")
                - type: Service type ("normal", "express", "pallet")
                - name: Human-readable name (e.g., "DHL Global Parcel")
                - isBusiness: Whether suitable for business addresses
                - isPrivate: Whether suitable for residential addresses
                - hasTracking: Whether provides tracking information
                - supportedCountries: List of supported country codes
              - search_params: The parameters used for this search
            - message: Helpful message about the results

        Example usage:
            - Get all methods: list_shipment_methods()
            - Get methods for US: list_shipment_methods(country="US")
            - Get methods for Germany: list_shipment_methods(country="DE")

        Common shipment methods include:
            - DHL Global Parcel: International shipping with tracking
            - DHL Parcel: Regional shipping (e.g., Germany only)
            - PostNL Standard: Netherlands regional shipping
            - PostNL Global Pack: International shipping from Netherlands

        Use this tool to:
            - Discover available shipping options for orders
            - Check which methods support specific countries
            - Get shipping method details for order creation
            - Validate country availability before creating orders
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]

        try:
            # Log the operation start
            if country:
                await ctx.info(f"Getting shipment methods available for country: {country}")
            else:
                await ctx.info("Getting all available shipment methods")

            # Log search parameters
            await ctx.debug(f"Country filter: {country if country else 'None'}")

            # Execute API call
            result = await client.list_shipment_methods(country=country)

            # Format response
            methods_data = [method.model_dump() for method in result.shipmentMethods]

            response = {
                "success": True,
                "data": {
                    "shipment_methods": methods_data,
                    "search_params": {
                        "country": country
                    }
                }
            }

            # Add helpful message based on results
            methods_count = len(methods_data)
            if methods_count == 0:
                if country:
                    response["message"] = f"No shipment methods found for country '{country}'"
                else:
                    response["message"] = "No shipment methods found"
            elif country:
                response["message"] = f"Found {methods_count} shipment methods available for country '{country}'"
            else:
                response["message"] = f"Found {methods_count} shipment methods"

            # Log success
            await ctx.info(f"Successfully retrieved {methods_count} shipment methods")

            return response

        except GelatoAPIError as e:
            error_message = f"Failed to retrieve shipment methods: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "list_shipment_methods",
                    "country": country,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }

        except Exception as e:
            error_message = f"Unexpected error retrieving shipment methods: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "list_shipment_methods",
                    "country": country
                }
            }