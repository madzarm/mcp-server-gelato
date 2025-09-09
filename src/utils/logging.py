"""Logging configuration for the Gelato MCP server."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", debug: bool = False) -> logging.Logger:
    """
    Set up logging for the MCP server.
    
    MCP servers communicate via JSON-RPC on stdout, so we must ensure
    all logging goes to stderr to avoid interfering with the protocol.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        debug: Enable debug mode with more verbose output
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("gelato_mcp")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create stderr handler (never use stdout for MCP servers)
    handler = logging.StreamHandler(sys.stderr)
    
    # Set format with emoji support
    if debug:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f"gelato_mcp.{name}")
    return logging.getLogger("gelato_mcp")