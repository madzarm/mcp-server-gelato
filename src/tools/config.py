"""Configuration tools for the Gelato MCP server."""

import os
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

from ..client.gelato_client import GelatoClient
from ..config import get_settings
from ..utils.client_registry import client_registry
from ..utils.exceptions import AuthenticationError, GelatoAPIError
from ..utils.logging import get_logger


def register_config_tools(mcp: FastMCP):
    """Register configuration tools with the FastMCP server."""

    @mcp.tool()
    async def configure_gelato(api_key: str) -> Dict[str, Any]:
        """
        Configure the Gelato MCP server with your API key.

        Args:
            api_key: Your Gelato API key from https://developers.gelato.com/

        Returns:
            Configuration status and connection test result
        """
        logger = get_logger("config-tool")

        # Validate API key format (basic check)
        if not api_key or not api_key.strip():
            return {
                "success": False,
                "error": "API key cannot be empty",
                "message": "Please provide a valid Gelato API key"
            }

        if len(api_key.strip()) < 10:
            return {
                "success": False,
                "error": "API key appears to be too short",
                "message": "Gelato API keys are typically longer than 10 characters"
            }

        try:
            # Set the API key in the environment for this session
            # Note: This only affects the current process
            os.environ["GELATO_API_KEY"] = api_key.strip()
            logger.info("🔑 API key set in environment")

            # Load settings with the new API key
            settings = get_settings(validate_api_key=True)
            logger.info("⚙️ Settings loaded and validated")

            # Create and test Gelato client
            client = GelatoClient(
                api_key=settings.gelato_api_key,
                settings=settings
            )

            logger.info("🔍 Testing connection to Gelato API...")
            await client.test_connection()
            logger.info("✅ Successfully connected to Gelato API")

            # Register the client for use by tools and resources
            client_registry.set_client(client)
            logger.info("📝 Client registered for resource access")

            return {
                "success": True,
                "message": "Successfully configured and connected to Gelato API",
                "api_endpoints": {
                    "orders": settings.gelato_base_url,
                    "products": settings.gelato_product_url,
                    "shipments": settings.gelato_shipment_url
                },
                "note": "Configuration is active for this session. To persist across restarts, set GELATO_API_KEY in your environment."
            }

        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed: {e}")
            return {
                "success": False,
                "error": "Authentication failed",
                "message": str(e),
                "help": "Please check that your API key is valid and active"
            }

        except GelatoAPIError as e:
            logger.error(f"❌ Failed to connect to Gelato API: {e}")
            return {
                "success": False,
                "error": "Connection failed",
                "message": str(e),
                "help": "Please check your network connection and API key"
            }

        except Exception as e:
            logger.error(f"❌ Unexpected error during configuration: {e}")
            return {
                "success": False,
                "error": "Configuration failed",
                "message": str(e),
                "help": "Please try again or check the server logs for details"
            }

    @mcp.tool()
    async def check_gelato_config() -> Dict[str, Any]:
        """
        Check the current Gelato API configuration status.

        Returns:
            Current configuration status and connection info
        """
        logger = get_logger("config-check")

        try:
            # Check if client is registered
            if client_registry.is_configured():
                client = client_registry.get_client()
                logger.info("✅ Client is configured and registered")

                # Try to get current settings
                try:
                    settings = get_settings(validate_api_key=False)
                    api_key_configured = settings.is_configured()
                except Exception:
                    api_key_configured = False

                return {
                    "configured": True,
                    "api_key_set": api_key_configured,
                    "client_registered": True,
                    "status": "ready",
                    "message": "Gelato API is configured and ready to use",
                    "endpoints": {
                        "orders": settings.gelato_base_url if api_key_configured else "Not available",
                        "products": settings.gelato_product_url if api_key_configured else "Not available",
                        "shipments": settings.gelato_shipment_url if api_key_configured else "Not available"
                    }
                }
            else:
                logger.info("❌ No client configured")
                return {
                    "configured": False,
                    "api_key_set": False,
                    "client_registered": False,
                    "status": "not_configured",
                    "message": "Gelato API is not configured",
                    "help": "Use the configure_gelato tool to set up your API key"
                }

        except Exception as e:
            logger.error(f"❌ Error checking configuration: {e}")
            return {
                "configured": False,
                "error": str(e),
                "status": "error",
                "message": "Error checking configuration",
                "help": "Use the configure_gelato tool to set up your API key"
            }