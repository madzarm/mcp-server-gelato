"""Main MCP server setup for Gelato API."""

from contextlib import asynccontextmanager
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from .client.gelato_client import GelatoClient
from .config import get_settings
from .resources.orders import register_order_resources
from .resources.products import register_product_resources
from .resources.templates import register_template_resources
from .tools.config import register_config_tools
from .tools.orders import register_order_tools
from .tools.products import register_product_tools
from .tools.shipments import register_shipment_tools
from .tools.templates import register_template_tools
from .utils.client_registry import client_registry
from .utils.exceptions import AuthenticationError, GelatoAPIError
from .utils.logging import get_logger


@asynccontextmanager
async def lifespan(server: FastMCP):
    """
    Manage server startup and shutdown lifecycle.
    
    This function initializes the Gelato API client with authentication
    and validates the connection during server startup.
    """
    logger = get_logger("server")
    
    # Load settings without API key validation initially
    try:
        settings = get_settings(validate_api_key=False)
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("💡 Please check your environment variables or .env file")
        raise
    
    # Check if API key is configured
    if settings.is_configured():
        # Initialize Gelato API client with API key
        try:
            client = GelatoClient(
                api_key=settings.gelato_api_key,
                settings=settings
            )

            # Test connection to ensure API key is valid
            logger.info("🔍 Testing connection to Gelato API...")
            await client.test_connection()
            logger.info("✅ Successfully connected to Gelato API")

            # Register client with registry for resource access
            client_registry.set_client(client)
            logger.info("📝 Client registered for resource access")

            # Yield context with initialized resources
            yield {
                "client": client,
                "settings": settings,
                "configured": True
            }

        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed: {e}")
            logger.info("💡 Please check your GELATO_API_KEY environment variable")
            raise

        except GelatoAPIError as e:
            logger.error(f"❌ Failed to connect to Gelato API: {e}")
            logger.info("💡 Please check your network connection and API key")
            raise

        except Exception as e:
            logger.error(f"❌ Unexpected error during startup: {e}")
            raise
    else:
        # API key not configured - start in unconfigured mode
        logger.warning("⚠️ GELATO_API_KEY not configured")
        logger.info("💡 Server starting in unconfigured mode")
        logger.info("💡 Use the configure_gelato tool to set up your API key")

        # Clear any existing client and yield context without connection
        client_registry.clear_client()
        yield {
            "client": None,
            "settings": settings,
            "configured": False
        }

    # Clean up resources on exit
    try:
        # Get client from registry for cleanup
        try:
            current_client = client_registry.get_client()
            if current_client:
                await current_client.close()
        except RuntimeError:
            # No client registered, which is fine
            pass
        # Clear client registry
        client_registry.clear_client()
    except Exception as e:
        logger.warning(f"⚠️ Error during cleanup: {e}")


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server.
    
    Returns:
        Configured FastMCP server instance
    """
    # Create MCP server
    mcp = FastMCP(
        name="Gelato Print API",
        instructions=(
            "MCP server for Gelato print-on-demand API. "
            "I can help you search orders, get order details, and explore product catalogs. "
            "Use resources like orders://{order_id} to load order data into context, "
            "or tools like search_orders for complex queries."
        ),
        lifespan=lifespan
    )
    
    # Register all tools and resources
    register_config_tools(mcp)
    register_order_tools(mcp)
    register_product_tools(mcp)
    register_shipment_tools(mcp)
    register_template_tools(mcp)
    register_order_resources(mcp)
    register_product_resources(mcp)
    register_template_resources(mcp)
    
    return mcp


# Global server instance
server = create_server()


def run_server():
    """Run the MCP server."""
    logger = get_logger("runner")
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise


if __name__ == "__main__":
    run_server()