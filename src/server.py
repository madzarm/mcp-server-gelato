"""Main MCP server setup for Gelato API."""

from contextlib import asynccontextmanager
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from .client.gelato_client import GelatoClient
from .config import get_settings
from .resources.orders import register_order_resources
from .resources.products import register_product_resources
from .tools.orders import register_order_tools
from .tools.products import register_product_tools
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
    
    # Load and validate settings
    try:
        settings = get_settings()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.info("💡 Please check your environment variables or .env file")
        raise
    
    # Initialize Gelato API client
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
            "settings": settings
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
    
    finally:
        # Clean up resources
        try:
            if 'client' in locals():
                await client.close()
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
    register_order_tools(mcp)
    register_product_tools(mcp)
    register_order_resources(mcp)
    register_product_resources(mcp)
    
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