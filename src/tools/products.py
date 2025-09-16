"""Product-related MCP tools."""

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from ..client.gelato_client import GelatoClient
from ..models.products import SearchProductsRequest
from ..utils.exceptions import GelatoAPIError, CatalogNotFoundError, ProductNotFoundError


def register_product_tools(mcp: FastMCP):
    """Register all product-related tools with the MCP server."""
    
    @mcp.tool()
    async def search_products(
        ctx: Context,
        catalog_uid: str,
        attribute_filters: Optional[Dict[str, List[str]]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search products in a Gelato catalog with advanced filtering capabilities.
        
        This tool allows you to search for products within a specific catalog using 
        various attribute filters and pagination controls.
        
        Args:
            catalog_uid: Catalog unique identifier (e.g., "posters", "apparel", "mugs")
            attribute_filters: Dictionary of filters where keys are attribute names 
                             and values are lists of allowed attribute values.
                             For example: {"Orientation": ["hor", "ver"], "CoatingType": ["none"]}
            limit: Maximum number of products to return (default 50, max 100)
            offset: Number of results to skip for pagination (default 0, min 0)
        
        Returns:
            Dictionary containing:
            - success: Boolean indicating if the search was successful
            - data: Object containing products list, hits information, and pagination
            - message: Helpful message about the results
        
        Example filters:
            - Orientation filters: {"Orientation": ["hor", "ver"]}
            - Paper type filters: {"PaperType": ["100-lb-text-coated-silk"]}
            - Color filters: {"ColorType": ["4-4", "1-0"]}
            - Multiple filters: {"Orientation": ["ver"], "CoatingType": ["none", "glossy-coating"]}
        
        Available catalogs include:
            - "posters": Poster products
            - "apparel": Clothing and apparel
            - "mugs": Mug products  
            - "cards": Greeting cards and business cards
            - "calendars": Calendar products
            - "books": Photo books and notebooks
        
        The response includes attribute hits showing how many products match 
        each possible filter value, which helps refine your search.
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]
        
        try:
            # Validate parameters
            if limit < 1 or limit > 100:
                return {
                    "success": False,
                    "error": {
                        "message": f"Invalid limit: {limit}. Must be between 1 and 100.",
                        "operation": "search_products",
                        "catalog_uid": catalog_uid
                    }
                }
            
            if offset < 0:
                return {
                    "success": False,
                    "error": {
                        "message": f"Invalid offset: {offset}. Must be 0 or greater.",
                        "operation": "search_products",
                        "catalog_uid": catalog_uid
                    }
                }
            
            # Log the operation start
            await ctx.info(f"Searching products in catalog: {catalog_uid}")
            
            # Build search request
            search_request = SearchProductsRequest(
                attributeFilters=attribute_filters,
                limit=limit,
                offset=offset
            )
            
            # Log search parameters for debugging
            if attribute_filters:
                filter_summary = ", ".join([f"{k}: {v}" for k, v in attribute_filters.items()])
                await ctx.debug(f"Applying filters: {filter_summary}")
            else:
                await ctx.debug("No attribute filters applied")
            
            await ctx.debug(f"Pagination: limit={limit}, offset={offset}")
            
            # Execute search via API
            result = await client.search_products(catalog_uid, search_request)
            
            # Format response
            products_data = [product.model_dump() for product in result.products]
            hits_data = result.hits.model_dump()
            
            response = {
                "success": True,
                "data": {
                    "products": products_data,
                    "hits": hits_data,
                    "pagination": {
                        "count": len(products_data),
                        "offset": offset,
                        "limit": limit,
                        "has_more": len(products_data) == limit
                    },
                    "search_params": {
                        "catalog_uid": catalog_uid,
                        "attribute_filters": attribute_filters,
                        "limit": limit,
                        "offset": offset
                    }
                }
            }
            
            # Add helpful message based on results
            if len(products_data) == 0:
                if attribute_filters:
                    response["message"] = f"No products found in catalog '{catalog_uid}' matching the specified filters"
                else:
                    response["message"] = f"No products found in catalog '{catalog_uid}'"
            elif len(products_data) == limit:
                response["message"] = (
                    f"Found {len(products_data)} products in catalog '{catalog_uid}' "
                    f"(may have more results, use offset={offset + limit} to get next page)"
                )
            else:
                response["message"] = f"Found {len(products_data)} products in catalog '{catalog_uid}'"
            
            # Log success
            await ctx.info(f"Successfully found {len(products_data)} products")
            
            return response
        
        except CatalogNotFoundError as e:
            error_message = f"Catalog not found: {catalog_uid}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "search_products",
                    "catalog_uid": catalog_uid,
                    "status_code": getattr(e, 'status_code', 404)
                }
            }
        
        except GelatoAPIError as e:
            error_message = f"Failed to search products: {str(e)}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "search_products", 
                    "catalog_uid": catalog_uid,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }
        
        except Exception as e:
            error_message = f"Unexpected error searching products: {str(e)}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "search_products",
                    "catalog_uid": catalog_uid
                }
            }
    
    @mcp.tool()
    async def get_product(
        ctx: Context,
        product_uid: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a single product.
        
        This tool retrieves comprehensive information about a specific product including
        all attributes, weight, dimensions, supported countries, and availability details.
        
        Args:
            product_uid: Product unique identifier (e.g., "cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor")
                        You can get product UIDs from the search_products tool results.
        
        Returns:
            Dictionary containing:
            - success: Boolean indicating if the retrieval was successful
            - data: Complete product information including:
              - productUid: Product unique identifier
              - attributes: Product attributes (coating, color, orientation, etc.)
              - weight: Product weight information (flexible format)
              - supportedCountries: List of supported country codes
              - notSupportedCountries: List of unsupported country codes
              - isStockable: Whether the product has limited stock
              - isPrintable: Whether the product can be printed on
              - validPageCounts: Supported page counts for multi-page products (optional)
              - dimensions: Product dimensions (flexible format, optional)
            - message: Helpful message about the result
        
        Example usage:
            - Get poster details: get_product("posters_pf_a1_pt_200-gsm-poster-paper_cl_4-0_ver")
            - Get card details: get_product("cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor")
            - Get apparel details: get_product("apparel_product_gca_t-shirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_s_gco_white_gpr_4-4")
        
        Use this tool when you need complete product specifications, country availability,
        stock status, or other detailed product information for a specific product.
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]
        
        try:
            # Log the operation start
            await ctx.info(f"Retrieving product details for: {product_uid}")
            
            # Get product via API
            product = await client.get_product(product_uid)
            
            # Format response
            product_data = product.model_dump()
            
            response = {
                "success": True,
                "data": product_data,
                "message": f"Successfully retrieved product '{product_uid}'"
            }
            
            # Log success
            await ctx.info(f"Successfully retrieved product: {product_uid}")
            
            return response
        
        except ProductNotFoundError as e:
            error_message = f"Product not found: {product_uid}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_product",
                    "product_uid": product_uid,
                    "status_code": getattr(e, 'status_code', 404)
                }
            }
        
        except GelatoAPIError as e:
            error_message = f"Failed to retrieve product: {str(e)}"
            await ctx.error(error_message)
            
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_product",
                    "product_uid": product_uid,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }
        
        except Exception as e:
            error_message = f"Unexpected error retrieving product: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "get_product",
                    "product_uid": product_uid
                }
            }

    @mcp.tool()
    async def get_product_prices(
        ctx: Context,
        product_uid: str,
        country: Optional[str] = None,
        currency: Optional[str] = None,
        page_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get price information for all quantities of a specific product.

        This tool retrieves comprehensive pricing information for a product across
        different quantities, with optional filtering by country, currency, and page count.

        Args:
            product_uid: Product unique identifier (e.g., "cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor")
                        You can get product UIDs from the search_products tool results.
            country: Optional country ISO code (e.g., "US", "GB", "DE", "CA")
                    Filters prices to show only those available for the specified country.
            currency: Optional currency ISO code (e.g., "USD", "GBP", "EUR", "CAD")
                     Filters prices to show only those in the specified currency.
            page_count: Optional page count for multi-page products (e.g., 10, 20, 50)
                       Required for multi-page products like books, calendars, etc.

        Returns:
            Dictionary containing:
            - success: Boolean indicating if the request was successful
            - data: Object containing:
              - prices: List of price points with details:
                - productUid: Product unique identifier
                - country: Country ISO code (e.g., "US", "GB")
                - quantity: Quantity for this price point (e.g., 20, 100, 500)
                - price: Price per unit at this quantity
                - currency: Currency ISO code (e.g., "USD", "GBP")
                - pageCount: Page count for multi-page products (null for single-page)
              - search_params: The parameters used for this search
            - message: Helpful message about the results

        Example usage:
            - Basic pricing: get_product_prices(product_uid="cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor")
            - US pricing only: get_product_prices(product_uid="...", country="US")
            - Multi-page product: get_product_prices(product_uid="books_...", page_count=24)
            - Specific currency: get_product_prices(product_uid="...", currency="EUR")

        Use this tool to:
            - Get quantity-based pricing for cost calculations
            - Compare prices across different countries/currencies
            - Get pricing for multi-page products (books, calendars)
            - Plan bulk orders with quantity discounts
            - Calculate total costs for different order sizes

        The response includes pricing tiers showing how unit costs decrease with larger quantities,
        helping you optimize order sizes and understand volume discounts.
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]

        try:
            # Log the operation start
            if country or currency or page_count:
                filters_info = []
                if country:
                    filters_info.append(f"country='{country}'")
                if currency:
                    filters_info.append(f"currency='{currency}'")
                if page_count:
                    filters_info.append(f"page_count={page_count}")

                await ctx.info(f"Getting product prices for: {product_uid} filtered by {', '.join(filters_info)}")
            else:
                await ctx.info(f"Getting all available product prices for: {product_uid}")

            # Log search parameters for debugging
            await ctx.debug(f"Product UID: {product_uid}")
            await ctx.debug(f"Country filter: {country if country else 'None'}")
            await ctx.debug(f"Currency filter: {currency if currency else 'None'}")
            await ctx.debug(f"Page count: {page_count if page_count else 'None'}")

            # Execute API call
            prices = await client.get_product_prices(
                product_uid=product_uid,
                country=country,
                currency=currency,
                page_count=page_count
            )

            # Format response
            prices_data = [price.model_dump() for price in prices]

            response = {
                "success": True,
                "data": {
                    "prices": prices_data,
                    "search_params": {
                        "product_uid": product_uid,
                        "country": country,
                        "currency": currency,
                        "page_count": page_count
                    }
                }
            }

            # Add helpful message based on results
            prices_count = len(prices_data)
            if prices_count == 0:
                response["message"] = f"No price information found for product '{product_uid}'"
                if country or currency or page_count:
                    filters_info = []
                    if country:
                        filters_info.append(f"country='{country}'")
                    if currency:
                        filters_info.append(f"currency='{currency}'")
                    if page_count:
                        filters_info.append(f"page_count={page_count}")
                    response["message"] += f" with the specified filters ({', '.join(filters_info)})"
            else:
                if country or currency or page_count:
                    filters_info = []
                    if country:
                        filters_info.append(f"country='{country}'")
                    if currency:
                        filters_info.append(f"currency='{currency}'")
                    if page_count:
                        filters_info.append(f"page_count={page_count}")

                    response["message"] = f"Found {prices_count} price points for product '{product_uid}' filtered by {', '.join(filters_info)}"
                else:
                    response["message"] = f"Found {prices_count} price points for product '{product_uid}'"

            # Log success
            await ctx.info(f"Successfully retrieved {prices_count} price points")

            return response

        except ProductNotFoundError as e:
            error_message = f"Product not found: {product_uid}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_product_prices",
                    "product_uid": product_uid,
                    "status_code": getattr(e, 'status_code', 404)
                }
            }

        except GelatoAPIError as e:
            error_message = f"Failed to retrieve product prices: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_product_prices",
                    "product_uid": product_uid,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }

        except Exception as e:
            error_message = f"Unexpected error retrieving product prices: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "get_product_prices",
                    "product_uid": product_uid
                }
            }