"""Authentication utilities for Gelato API."""

from typing import Dict

from .exceptions import AuthenticationError


def get_auth_headers(api_key: str) -> Dict[str, str]:
    """
    Get authentication headers for Gelato API requests.
    
    Args:
        api_key: The Gelato API key
        
    Returns:
        Dictionary containing authentication headers
        
    Raises:
        AuthenticationError: If API key is invalid or missing
    """
    if not api_key or api_key.strip() == "":
        raise AuthenticationError("API key is required")
    
    return {
        "X-API-KEY": api_key.strip(),
        "Content-Type": "application/json",
    }


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format (basic validation).
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if API key format looks valid
        
    Raises:
        AuthenticationError: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise AuthenticationError("API key must be a non-empty string")
    
    api_key = api_key.strip()
    if len(api_key) < 10:  # Basic length check
        raise AuthenticationError("API key appears to be too short")
    
    return True