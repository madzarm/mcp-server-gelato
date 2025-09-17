#!/usr/bin/env python3
"""CLI entry point for the Gelato MCP server."""

import os
import sys

from .server import run_server
from .utils.logging import setup_logging


def main():
    """Main CLI entry point for the Gelato MCP server."""
    # Set up logging (goes to stderr, not stdout)
    debug = os.getenv("DEBUG", "false").lower() == "true"
    logger = setup_logging(level="DEBUG" if debug else "INFO", debug=debug)

    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())