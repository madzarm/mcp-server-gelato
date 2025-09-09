"""Base class for MCP resources."""

import json
from typing import Any, Dict

from ..client.gelato_client import GelatoClient
from ..utils.exceptions import GelatoAPIError


class BaseResource:
    """Base class for all Gelato MCP resources."""
    
    def __init__(self, client: GelatoClient):
        """
        Initialize the base resource.
        
        Args:
            client: Gelato API client instance
        """
        self.client = client
    
    def format_json_response(self, data: Any) -> str:
        """
        Format data as pretty-printed JSON string.
        
        Args:
            data: Data to format
            
        Returns:
            Pretty-printed JSON string
        """
        if hasattr(data, 'model_dump'):
            # Pydantic model
            return json.dumps(data.model_dump(), indent=2, default=str)
        elif isinstance(data, (list, dict)):
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps({"data": data}, indent=2, default=str)
    
    async def handle_api_error(self, error: GelatoAPIError) -> str:
        """
        Handle API errors and return formatted error message.
        
        Args:
            error: The API error to handle
            
        Returns:
            Formatted error message
        """
        error_info = {
            "error": str(error),
            "status_code": getattr(error, 'status_code', None),
            "response_data": getattr(error, 'response_data', {})
        }
        return json.dumps(error_info, indent=2)