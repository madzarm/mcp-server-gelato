"""Unit tests for custom exceptions."""

import pytest

from src.utils.exceptions import (
    AuthenticationError,
    CatalogNotFoundError,
    GelatoAPIError,
    NetworkError,
    OrderNotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class TestGelatoAPIError:
    """Test cases for GelatoAPIError (base exception)."""
    
    def test_basic_creation(self):
        """Test creating GelatoAPIError with message only."""
        error = GelatoAPIError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.status_code is None
        assert error.response_data is None
    
    def test_creation_with_status_code(self):
        """Test creating GelatoAPIError with status code."""
        error = GelatoAPIError("Test error", status_code=400)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response_data is None
    
    def test_creation_with_response_data(self):
        """Test creating GelatoAPIError with response data."""
        response_data = {"error": "Invalid request", "details": "Missing field"}
        error = GelatoAPIError("Test error", response_data=response_data)
        
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data == response_data
    
    def test_creation_with_all_parameters(self):
        """Test creating GelatoAPIError with all parameters."""
        response_data = {"error": "Server error"}
        error = GelatoAPIError("Test error", status_code=500, response_data=response_data)
        
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.response_data == response_data
    
    def test_inheritance(self):
        """Test that GelatoAPIError inherits from Exception."""
        error = GelatoAPIError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GelatoAPIError)


class TestAuthenticationError:
    """Test cases for AuthenticationError."""
    
    def test_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        
        assert str(error) == "Invalid API key"
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, AuthenticationError)
    
    def test_with_status_code(self):
        """Test AuthenticationError with status code."""
        error = AuthenticationError("Unauthorized", status_code=401)
        
        assert str(error) == "Unauthorized"
        assert error.status_code == 401


class TestNetworkError:
    """Test cases for NetworkError."""
    
    def test_creation(self):
        """Test creating NetworkError."""
        error = NetworkError("Connection timeout")
        
        assert str(error) == "Connection timeout"
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, NetworkError)
    
    def test_inheritance_chain(self):
        """Test NetworkError inheritance chain."""
        error = NetworkError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, NetworkError)


class TestRateLimitError:
    """Test cases for RateLimitError."""
    
    def test_creation(self):
        """Test creating RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, RateLimitError)
    
    def test_with_status_code(self):
        """Test RateLimitError with status code."""
        error = RateLimitError("Too many requests", status_code=429)
        
        assert str(error) == "Too many requests"
        assert error.status_code == 429


class TestServerError:
    """Test cases for ServerError."""
    
    def test_creation(self):
        """Test creating ServerError."""
        error = ServerError("Internal server error")
        
        assert str(error) == "Internal server error"
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, ServerError)
    
    def test_with_all_parameters(self):
        """Test ServerError with all parameters."""
        response_data = {"error": "Database connection failed"}
        error = ServerError("Server unavailable", status_code=503, response_data=response_data)
        
        assert str(error) == "Server unavailable"
        assert error.status_code == 503
        assert error.response_data == response_data


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Invalid request data")
        
        assert str(error) == "Invalid request data"
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, ValidationError)
    
    def test_with_response_data(self):
        """Test ValidationError with response data."""
        response_data = {
            "errors": [
                {"field": "email", "message": "Invalid format"},
                {"field": "age", "message": "Must be positive"}
            ]
        }
        error = ValidationError("Validation failed", status_code=400, response_data=response_data)
        
        assert str(error) == "Validation failed"
        assert error.status_code == 400
        assert error.response_data == response_data


class TestOrderNotFoundError:
    """Test cases for OrderNotFoundError."""
    
    def test_creation(self):
        """Test creating OrderNotFoundError."""
        order_id = "order-123"
        error = OrderNotFoundError(order_id)
        
        expected_message = f"Order not found: {order_id}"
        assert str(error) == expected_message
        assert error.order_id == order_id
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, OrderNotFoundError)
    
    def test_inheritance(self):
        """Test OrderNotFoundError inheritance."""
        error = OrderNotFoundError("test-order")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, OrderNotFoundError)


class TestCatalogNotFoundError:
    """Test cases for CatalogNotFoundError."""
    
    def test_creation(self):
        """Test creating CatalogNotFoundError."""
        catalog_uid = "nonexistent-catalog"
        error = CatalogNotFoundError(catalog_uid)
        
        expected_message = f"Catalog not found: {catalog_uid}"
        assert str(error) == expected_message
        assert error.catalog_uid == catalog_uid
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, CatalogNotFoundError)
    
    def test_inheritance(self):
        """Test CatalogNotFoundError inheritance."""
        error = CatalogNotFoundError("test-catalog")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GelatoAPIError)
        assert isinstance(error, CatalogNotFoundError)


class TestExceptionUsagePatterns:
    """Test cases for common exception usage patterns."""
    
    def test_catching_base_exception(self):
        """Test that derived exceptions can be caught as base exception."""
        exceptions_to_test = [
            AuthenticationError("Auth error"),
            NetworkError("Network error"),
            RateLimitError("Rate limit error"),
            ServerError("Server error"),
            ValidationError("Validation error"),
            OrderNotFoundError("order-123"),
            CatalogNotFoundError("catalog-456"),
        ]
        
        for exc in exceptions_to_test:
            try:
                raise exc
            except GelatoAPIError as caught:
                assert caught is exc
                assert isinstance(caught, GelatoAPIError)
    
    def test_exception_with_try_except(self):
        """Test exception handling in try/except blocks."""
        # Test specific exception catching
        try:
            raise AuthenticationError("Invalid token")
        except AuthenticationError as e:
            assert str(e) == "Invalid token"
        
        # Test base exception catching
        try:
            raise OrderNotFoundError("missing-order")
        except GelatoAPIError as e:
            assert "missing-order" in str(e)
            assert isinstance(e, OrderNotFoundError)
    
    def test_exception_attributes_preservation(self):
        """Test that exception attributes are preserved through inheritance."""
        response_data = {"details": "test details"}
        
        # Test with various exception types
        exceptions_with_attributes = [
            (AuthenticationError("Auth error", status_code=401, response_data=response_data), 401),
            (ServerError("Server error", status_code=500, response_data=response_data), 500),
            (ValidationError("Validation error", status_code=400, response_data=response_data), 400),
        ]
        
        for exc, expected_status in exceptions_with_attributes:
            assert exc.status_code == expected_status
            assert exc.response_data == response_data
            assert isinstance(exc, GelatoAPIError)
    
    def test_exception_chaining(self):
        """Test exception chaining (raising from another exception)."""
        original_error = ValueError("Original error")
        
        try:
            try:
                raise original_error
            except ValueError as e:
                raise GelatoAPIError("API error occurred") from e
        except GelatoAPIError as api_error:
            assert str(api_error) == "API error occurred"
            assert api_error.__cause__ is original_error


class TestExceptionEquality:
    """Test cases for exception equality and comparison."""
    
    def test_same_exception_types_not_equal(self):
        """Test that same exception types with different messages are not equal."""
        error1 = GelatoAPIError("Message 1")
        error2 = GelatoAPIError("Message 2")
        
        # Exceptions are not equal by default
        assert error1 != error2
    
    def test_different_exception_types_not_equal(self):
        """Test that different exception types are not equal."""
        error1 = AuthenticationError("Error")
        error2 = NetworkError("Error")
        
        assert error1 != error2
        assert type(error1) != type(error2)
    
    def test_exception_string_representation(self):
        """Test string representation of exceptions."""
        message = "Test error message"
        error = GelatoAPIError(message)
        
        assert str(error) == message
        assert repr(error).startswith("GelatoAPIError")
        assert message in repr(error)