"""Unit tests for authentication utilities."""

import pytest

from src.utils.auth import get_auth_headers, validate_api_key
from src.utils.exceptions import AuthenticationError


class TestGetAuthHeaders:
    """Test cases for get_auth_headers function."""
    
    def test_valid_api_key(self):
        """Test get_auth_headers with valid API key."""
        api_key = "valid_api_key_123"
        headers = get_auth_headers(api_key)
        
        assert headers["X-API-KEY"] == api_key
        assert headers["Content-Type"] == "application/json"
    
    def test_api_key_with_whitespace(self):
        """Test get_auth_headers strips whitespace."""
        api_key = "  valid_api_key_123  "
        headers = get_auth_headers(api_key)
        
        assert headers["X-API-KEY"] == "valid_api_key_123"
    
    def test_empty_api_key(self):
        """Test get_auth_headers with empty API key raises error."""
        with pytest.raises(AuthenticationError, match="API key is required"):
            get_auth_headers("")
    
    def test_none_api_key(self):
        """Test get_auth_headers with None API key raises error."""
        with pytest.raises(AuthenticationError, match="API key is required"):
            get_auth_headers(None)
    
    def test_whitespace_only_api_key(self):
        """Test get_auth_headers with whitespace-only API key raises error."""
        with pytest.raises(AuthenticationError, match="API key is required"):
            get_auth_headers("   ")


class TestValidateApiKey:
    """Test cases for validate_api_key function."""
    
    def test_valid_api_key(self):
        """Test validate_api_key with valid API key."""
        api_key = "valid_api_key_123"
        result = validate_api_key(api_key)
        assert result is True
    
    def test_valid_api_key_with_whitespace(self):
        """Test validate_api_key strips and validates."""
        api_key = "  valid_api_key_123  "
        result = validate_api_key(api_key)
        assert result is True
    
    def test_empty_string_api_key(self):
        """Test validate_api_key with empty string raises error."""
        with pytest.raises(AuthenticationError, match="API key must be a non-empty string"):
            validate_api_key("")
    
    def test_none_api_key(self):
        """Test validate_api_key with None raises error."""
        with pytest.raises(AuthenticationError, match="API key must be a non-empty string"):
            validate_api_key(None)
    
    def test_non_string_api_key(self):
        """Test validate_api_key with non-string input raises error."""
        with pytest.raises(AuthenticationError, match="API key must be a non-empty string"):
            validate_api_key(123)
        
        with pytest.raises(AuthenticationError, match="API key must be a non-empty string"):
            validate_api_key(["api_key"])
    
    def test_short_api_key(self):
        """Test validate_api_key with too short API key raises error."""
        with pytest.raises(AuthenticationError, match="API key appears to be too short"):
            validate_api_key("short")
    
    def test_whitespace_only_api_key(self):
        """Test validate_api_key with whitespace-only API key raises error."""
        with pytest.raises(AuthenticationError, match="API key appears to be too short"):
            validate_api_key("   ")
    
    def test_minimum_length_api_key(self):
        """Test validate_api_key with minimum valid length."""
        api_key = "1234567890"  # Exactly 10 characters
        result = validate_api_key(api_key)
        assert result is True
    
    def test_long_api_key(self):
        """Test validate_api_key with long API key."""
        api_key = "very_long_api_key_that_should_be_valid_12345678901234567890"
        result = validate_api_key(api_key)
        assert result is True


class TestAuthIntegration:
    """Integration tests for auth utilities."""
    
    def test_auth_workflow(self):
        """Test complete authentication workflow."""
        api_key = "test_api_key_minimum_10_chars"
        
        # Validate the key
        is_valid = validate_api_key(api_key)
        assert is_valid is True
        
        # Get headers
        headers = get_auth_headers(api_key)
        assert headers["X-API-KEY"] == api_key
        assert headers["Content-Type"] == "application/json"
    
    def test_auth_workflow_with_invalid_key(self):
        """Test authentication workflow with invalid key."""
        api_key = "short"
        
        # Validation should fail
        with pytest.raises(AuthenticationError):
            validate_api_key(api_key)
        
        # Headers should also fail
        with pytest.raises(AuthenticationError):
            get_auth_headers("")