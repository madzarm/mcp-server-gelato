"""Product catalog-related MCP resources."""

import json
from mcp.server.fastmcp import FastMCP

from ..utils.client_registry import client_registry
from ..utils.exceptions import CatalogNotFoundError, GelatoAPIError


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
    
    @mcp.resource("catalogs://summary")
    async def get_catalog_summary() -> str:
        """
        Get a summary of all catalogs with their basic information.
        
        This resource provides a convenient overview of all product catalogs
        in a single response, useful for getting a quick understanding of
        available product categories.
        """
        client = client_registry.get_client()
        
        try:
            catalogs = await client.list_catalogs()
            
            # Create a summary with catalog UIDs and titles
            summary_data = {
                "catalog_summary": [
                    {
                        "uid": catalog.catalogUid,
                        "title": catalog.title,
                        "resource_uri": f"catalogs://{catalog.catalogUid}"
                    }
                    for catalog in catalogs
                ],
                "total_catalogs": len(catalogs),
                "description": "Summary of all available product catalogs with resource URIs"
            }
            
            return json.dumps(summary_data, indent=2, default=str)
        
        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch catalog summary",
                "message": str(e),
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)