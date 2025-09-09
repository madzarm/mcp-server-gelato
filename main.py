"""Entry point for the Gelato MCP server."""

import os

from src.server import run_server
from src.utils.logging import setup_logging


def main():
    """Main entry point for the Gelato MCP server."""
    # Set up logging (goes to stderr, not stdout)
    debug = os.getenv("DEBUG", "false").lower() == "true"
    logger = setup_logging(level="DEBUG" if debug else "INFO", debug=debug)

    try:
        run_server()
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
