"""Gelato MCP Server package.

A comprehensive MCP (Model Context Protocol) server for integrating with
Gelato's print-on-demand API. Provides tools and resources for order management,
product catalog exploration, and shipment tracking.
"""

__version__ = "0.1.0"
__author__ = "Maksim Madžar"
__email__ = "madzarmaksim@gmail.com"

from .server import create_server, run_server

__all__ = ["create_server", "run_server"]