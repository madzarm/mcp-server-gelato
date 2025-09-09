"""Unit tests for client registry."""

import pytest
from unittest.mock import MagicMock

from src.utils.client_registry import ClientRegistry, client_registry


class TestClientRegistry:
    """Test cases for ClientRegistry class."""
    
    def test_singleton_pattern(self):
        """Test that ClientRegistry follows singleton pattern."""
        registry1 = ClientRegistry()
        registry2 = ClientRegistry()
        
        # Should be the same instance
        assert registry1 is registry2
        
        # Should also be the same as global instance
        assert registry1 is client_registry
        assert registry2 is client_registry
    
    def test_set_and_get_client(self):
        """Test setting and getting client."""
        registry = ClientRegistry()
        mock_client = MagicMock()
        
        # Clear any existing client
        registry.clear_client()
        
        # Set client
        registry.set_client(mock_client)
        
        # Get client should return the same instance
        retrieved_client = registry.get_client()
        assert retrieved_client is mock_client
    
    def test_get_client_without_setting(self):
        """Test getting client when none is set raises error."""
        registry = ClientRegistry()
        registry.clear_client()  # Ensure no client is set
        
        with pytest.raises(RuntimeError, match="No Gelato client registered"):
            registry.get_client()
    
    def test_clear_client(self):
        """Test clearing client."""
        registry = ClientRegistry()
        mock_client = MagicMock()
        
        # Set client
        registry.set_client(mock_client)
        assert registry.get_client() is mock_client
        
        # Clear client
        registry.clear_client()
        
        # Should raise error when trying to get client
        with pytest.raises(RuntimeError, match="No Gelato client registered"):
            registry.get_client()
    
    def test_overwrite_client(self):
        """Test that setting a new client overwrites the old one."""
        registry = ClientRegistry()
        
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        
        # Set first client
        registry.set_client(mock_client1)
        assert registry.get_client() is mock_client1
        
        # Set second client
        registry.set_client(mock_client2)
        assert registry.get_client() is mock_client2
        assert registry.get_client() is not mock_client1


class TestClientRegistryGlobalInstance:
    """Test cases for global client_registry instance."""
    
    def test_global_instance_is_singleton(self):
        """Test that global instance follows singleton pattern."""
        new_registry = ClientRegistry()
        assert new_registry is client_registry
    
    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        mock_client = MagicMock()
        
        # Clear any existing client
        client_registry.clear_client()
        
        # Test setting and getting through global instance
        client_registry.set_client(mock_client)
        retrieved_client = client_registry.get_client()
        
        assert retrieved_client is mock_client
        
        # Test that new registry instance sees the same client
        new_registry = ClientRegistry()
        assert new_registry.get_client() is mock_client


class TestClientRegistryStateBehavior:
    """Test cases for client registry state management."""
    
    def setup_method(self):
        """Set up each test with a clean state."""
        client_registry.clear_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    def test_state_persistence_across_instances(self):
        """Test that state persists across different registry instances."""
        registry1 = ClientRegistry()
        registry2 = ClientRegistry()
        mock_client = MagicMock()
        
        # Set client through first instance
        registry1.set_client(mock_client)
        
        # Should be accessible through second instance
        assert registry2.get_client() is mock_client
    
    def test_error_message_content(self):
        """Test that error message is informative."""
        registry = ClientRegistry()
        
        with pytest.raises(RuntimeError) as exc_info:
            registry.get_client()
        
        error_message = str(exc_info.value)
        assert "No Gelato client registered" in error_message
        assert "server hasn't finished initializing" in error_message
    
    def test_multiple_operations(self):
        """Test multiple registry operations."""
        registry = ClientRegistry()
        
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        
        # Multiple set/get operations
        registry.set_client(mock_client1)
        assert registry.get_client() is mock_client1
        
        registry.set_client(mock_client2)
        assert registry.get_client() is mock_client2
        
        registry.clear_client()
        with pytest.raises(RuntimeError):
            registry.get_client()
        
        registry.set_client(mock_client1)
        assert registry.get_client() is mock_client1