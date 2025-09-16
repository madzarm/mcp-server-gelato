"""Template-related MCP tools."""

from typing import Any, Dict

from mcp.server.fastmcp import Context, FastMCP

from ..client.gelato_client import GelatoClient
from ..utils.exceptions import GelatoAPIError, TemplateNotFoundError


def register_template_tools(mcp: FastMCP):
    """Register all template-related tools with the MCP server."""

    @mcp.tool()
    async def get_template(
        ctx: Context,
        template_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific template.

        This tool retrieves comprehensive information about a template including
        template name, title, description, preview URL, product variants, and metadata.
        Templates are used in Gelato's e-commerce platform for creating customizable products.

        Args:
            template_id: Template unique identifier (UUID format)
                        Example: "c12a363e-0d4e-4d96-be4b-bf4138eb8743"

        Returns:
            Dictionary containing:
            - success: Boolean indicating if the retrieval was successful
            - data: Complete template information including:
              - id: Template unique identifier
              - templateName: Internal template name
              - title: Product title for display
              - description: HTML product description
              - previewUrl: URL to template preview image
              - variants: Array of product variants (sizes, colors, etc.)
              - productType: Type of product (optional)
              - vendor: Product vendor/provider (optional)
              - createdAt: Template creation timestamp (ISO 8601)
              - updatedAt: Template last update timestamp (ISO 8601)
            - message: Helpful message about the result

        Template variants contain:
        - Variant details (ID, title, product UID)
        - Variant options (size, color, etc.)
        - Image placeholders for customization (print areas, dimensions)

        Example usage:
        - Get t-shirt template: get_template("c12a363e-0d4e-4d96-be4b-bf4138eb8743")
        - Get poster template: get_template("other-template-uuid-here")

        Use this tool when you need complete template specifications, variant information,
        customization options, or product details for e-commerce integration.
        """
        client: GelatoClient = ctx.request_context.lifespan_context["client"]

        try:
            # Log the operation start
            await ctx.info(f"Retrieving template details for: {template_id}")

            # Get template via API
            template = await client.get_template(template_id)

            # Format response
            template_data = template.model_dump()

            response = {
                "success": True,
                "data": template_data,
                "message": f"Successfully retrieved template '{template_id}'"
            }

            # Add helpful context based on template data
            if template.variants:
                variant_count = len(template.variants)
                response["message"] += f" with {variant_count} variant{'s' if variant_count != 1 else ''}"

            # Log success
            await ctx.info(f"Successfully retrieved template: {template_id}")

            return response

        except TemplateNotFoundError as e:
            error_message = f"Template not found: {template_id}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_template",
                    "template_id": template_id,
                    "status_code": getattr(e, 'status_code', 404)
                }
            }

        except GelatoAPIError as e:
            error_message = f"Failed to retrieve template: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "operation": "get_template",
                    "template_id": template_id,
                    "status_code": getattr(e, 'status_code', None),
                    "response_data": getattr(e, 'response_data', {})
                }
            }

        except Exception as e:
            error_message = f"Unexpected error retrieving template: {str(e)}"
            await ctx.error(error_message)

            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "operation": "get_template",
                    "template_id": template_id
                }
            }