"""Template-related MCP resources."""

import json
from mcp.server.fastmcp import FastMCP

from ..utils.client_registry import client_registry
from ..utils.exceptions import TemplateNotFoundError, GelatoAPIError


def register_template_resources(mcp: FastMCP):
    """Register all template-related resources with the MCP server."""

    @mcp.resource("templates://{template_id}")
    async def get_template(template_id: str) -> str:
        """
        Get detailed information about a specific template.

        This resource provides comprehensive information about a template including
        template name, title, description, preview URL, product variants, and metadata.
        Use this for accessing complete template information when you have a template ID.

        Template IDs are UUIDs that can be obtained from e-commerce platform integrations
        or template listing APIs.

        Examples:
        - templates://c12a363e-0d4e-4d96-be4b-bf4138eb8743
        - templates://other-template-uuid-here

        Template information includes:
        - Basic details (name, title, description, preview)
        - Product variants with sizes, colors, and options
        - Image placeholders for customization areas
        - Print area dimensions and specifications
        - Creation and update timestamps
        """
        client = client_registry.get_client()

        try:
            template = await client.get_template(template_id)

            response_data = {
                "template": template.model_dump(),
                "description": f"Detailed template information for {template_id}"
            }

            return json.dumps(response_data, indent=2, default=str)

        except TemplateNotFoundError as e:
            error_response = {
                "error": f"Template not found: {template_id}",
                "message": str(e),
                "template_id": template_id
            }
            return json.dumps(error_response, indent=2)

        except GelatoAPIError as e:
            error_response = {
                "error": "Failed to fetch template details",
                "message": str(e),
                "template_id": template_id,
                "status_code": getattr(e, 'status_code', None)
            }
            return json.dumps(error_response, indent=2)
