"""Custom exceptions for the Gelato MCP server."""


class GelatoAPIError(Exception):
    """Base exception for all Gelato API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(GelatoAPIError):
    """Raised when API key is invalid or missing."""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(GelatoAPIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class OrderNotFoundError(GelatoAPIError):
    """Raised when an order is not found."""
    
    def __init__(self, order_id: str):
        message = f"Order with ID '{order_id}' not found"
        super().__init__(message, status_code=404)


class CatalogNotFoundError(GelatoAPIError):
    """Raised when a product catalog is not found."""
    
    def __init__(self, catalog_uid: str):
        message = f"Catalog with UID '{catalog_uid}' not found"
        super().__init__(message, status_code=404)


class ValidationError(GelatoAPIError):
    """Raised when request data validation fails."""
    
    def __init__(self, message: str = "Invalid request data"):
        super().__init__(message, status_code=400)


class NetworkError(GelatoAPIError):
    """Raised when network-related errors occur."""
    
    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message, status_code=None)


class ServerError(GelatoAPIError):
    """Raised when Gelato API returns server error."""
    
    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)