"""Product catalog-related MCP resources."""

import json
from mcp.server.fastmcp import FastMCP

from ..utils.client_registry import client_registry
from ..utils.exceptions import CatalogNotFoundError, ProductNotFoundError, GelatoAPIError


def register_product_resources(mcp: FastMCP):
    """Register all product catalog-related resources with the MCP server."""
    
    @mcp.resource("catalogs://list")
    async def list_catalogs() -> str:
        """
        Get a list of all available product catalogs.
        
        This resource provides an overview of all product categories
        available through the Gelato API, such as cards, posters, apparel, etc.
        """
        client = client_registry.get_client()
        
        try:
            catalogs = await client.list_catalogs()
            
            response_data = {
                "catalogs": [catalog.model_dump() for catalog in catalogs],
                "count": len(catalogs),
                "description": "Available product catalogs"
            }
            
            return json.dumps(response_data, indent=2, default=str)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch product catalogs",
                "message": str(e),
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
    
    @mcp.resource("catalogs://{catalog_uid}")
    async def get_catalog(catalog_uid: str) -> str:
        """
        Get detailed information about a specific product catalog.
        
        This resource provides comprehensive information about a catalog
        including all available product attributes and their possible values.
        Use this to understand what variations are available for products
        in a specific category.
        """
        client = client_registry.get_client()
        
        try:
            catalog = await client.get_catalog(catalog_uid)
            return json.dumps(catalog.model_dump(), indent=2, default=str)
        
        except CatalogNotFoundError as e:
            error_response = {
                "error": f"Catalog not found: {catalog_uid}",
                "message": str(e),
                "catalog_uid": catalog_uid
            }
            return json.dumps(error_response, indent=2)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch catalog details",
                "message": str(e),
                "catalog_uid": catalog_uid,
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
    
    @mcp.resource("products://{product_uid}")
    async def get_product(product_uid: str) -> str:
        """
        Get detailed information about a specific product.
        
        This resource provides comprehensive information about a product including
        all attributes, weight, dimensions, supported countries, availability details,
        and other specifications. Use this for accessing complete product information
        when you have a specific product UID.
        
        Product UIDs can be obtained from the search_products tool or catalog listings.
        
        Examples:
        - products://cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor
        - products://posters_pf_a1_pt_200-gsm-poster-paper_cl_4-0_ver  
        - products://apparel_product_gca_t-shirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_s_gco_white_gpr_4-4
        """
        client = client_registry.get_client()
        
        try:
            product = await client.get_product(product_uid)
            
            response_data = {
                "product": product.model_dump(),
                "description": f"Detailed information for product {product_uid}"
            }
            
            return json.dumps(response_data, indent=2, default=str)
        
        except ProductNotFoundError as e:
            error_response = {
                "error": f"Product not found: {product_uid}",
                "message": str(e),
                "product_uid": product_uid
            }
            return json.dumps(error_response, indent=2)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch product details",
                "message": str(e),
                "product_uid": product_uid,
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
    
