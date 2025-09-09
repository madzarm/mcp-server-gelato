"""Base class for MCP tools."""

from typing import Any, Dict

from ..client.gelato_client import GelatoClient
from ..utils.exceptions import GelatoAPIError


class BaseTool:
    """Base class for all Gelato MCP tools."""
    
    def __init__(self, client: GelatoClient):
        """
        Initialize the base tool.
        
        Args:
            client: Gelato API client instance
        """
        self.client = client
    
    def format_response(self, data: Any, success: bool = True, message: str = None) -> Dict[str, Any]:
        """
        Format tool response in a consistent way.
        
        Args:
            data: Response data
            success: Whether the operation was successful
            message: Optional message to include
            
        Returns:
            Formatted response dictionary
        """
        response = {
            "success": success,
            "data": data
        }
        
        if message:
            response["message"] = message
            
        return response
    
    def format_error_response(self, error: GelatoAPIError, operation: str = "operation") -> Dict[str, Any]:
        """
        Format error response in a consistent way.
        
        Args:
            error: The API error
            operation: Description of the operation that failed
            
        Returns:
            Formatted error response dictionary
        """
        return {
            "success": False,
            "error": {
                "message": str(error),
                "operation": operation,
                "status_code": getattr(error, 'status_code', None),
                "response_data": getattr(error, 'response_data', {})
            }
        }