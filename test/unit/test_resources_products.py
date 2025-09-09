"""Unit tests for product resources."""

import json
from unittest.mock import AsyncMock

import pytest

from src.resources.products import register_product_resources
from src.utils.client_registry import client_registry
from src.utils.exceptions import CatalogNotFoundError, GelatoAPIError


class MockFastMCP:
    """Mock FastMCP class for testing resource registration."""
    
    def __init__(self):
        self.resources = {}
    
    def resource(self, uri_pattern):
        """Mock resource decorator."""
        def decorator(func):
            self.resources[uri_pattern] = func
            return func
        return decorator


class TestProductResourceRegistration:
    """Test cases for product resource registration."""
    
    def test_register_product_resources(self):
        """Test that product resources are registered correctly."""
        mock_mcp = MockFastMCP()
        
        register_product_resources(mock_mcp)
        
        # Check that all expected resources are registered
        expected_resources = [
            "catalogs://list",
            "catalogs://{catalog_uid}",
            "catalogs://summary"
        ]
        
        for resource_uri in expected_resources:
            assert resource_uri in mock_mcp.resources
            assert callable(mock_mcp.resources[resource_uri])


class TestCatalogResources:
    """Test cases for catalog resource functions."""
    
    def setup_method(self):
        """Set up each test with a mock client."""
        self.mock_client = AsyncMock()
        client_registry.set_client(self.mock_client)
    
    def teardown_method(self):
        """Clean up after each test."""
        client_registry.clear_client()
    
    async def test_list_catalogs_success(self, sample_catalog):
        """Test list_catalogs resource with successful response."""
        # Set up mock
        self.mock_client.list_catalogs.return_value = [sample_catalog]
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_product_resources(mock_mcp)
        list_catalogs_func = mock_mcp.resources["catalogs://list"]
        
        # Call the function
        result = await list_catalogs_func()
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "catalogs" in parsed_result
        assert "count" in parsed_result
        assert "description" in parsed_result
        assert len(parsed_result["catalogs"]) == 1
        assert parsed_result["catalogs"][0]["catalogUid"] == "test-cards"
        assert parsed_result["count"] == 1
    
    async def test_list_catalogs_api_error(self):
        """Test list_catalogs resource with API error."""
        # Set up mock to raise GelatoAPIError
        self.mock_client.list_catalogs.side_effect = GelatoAPIError(
            "Server error",
            status_code=500
        )
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_product_resources(mock_mcp)
        list_catalogs_func = mock_mcp.resources["catalogs://list"]
        
        # Call the function
        result = await list_catalogs_func()
        
        # Verify error response
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert parsed_result["error"] == "Failed to fetch product catalogs"
        assert parsed_result["status_code"] == 500
    
    async def test_get_catalog_success(self, sample_catalog_detail):
        """Test get_catalog resource with successful response."""
        # Set up mock
        self.mock_client.get_catalog.return_value = sample_catalog_detail
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_product_resources(mock_mcp)
        get_catalog_func = mock_mcp.resources["catalogs://{catalog_uid}"]
        
        # Call the function
        result = await get_catalog_func("test-cards")
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert parsed_result["catalogUid"] == "test-cards"
        assert parsed_result["title"] == "Test Cards"
        assert "productAttributes" in parsed_result
        
        # Verify client was called correctly
        self.mock_client.get_catalog.assert_called_once_with("test-cards")
    
    async def test_get_catalog_not_found(self):
        """Test get_catalog resource with catalog not found error."""
        # Set up mock to raise CatalogNotFoundError
        self.mock_client.get_catalog.side_effect = CatalogNotFoundError("missing-catalog")
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_product_resources(mock_mcp)
        get_catalog_func = mock_mcp.resources["catalogs://{catalog_uid}"]
        
        # Call the function
        result = await get_catalog_func("missing-catalog")
        
        # Verify error response
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "Catalog not found: missing-catalog" in parsed_result["error"]
        assert parsed_result["catalog_uid"] == "missing-catalog"
    
    async def test_get_catalog_summary_success(self, sample_catalog):
        """Test get_catalog_summary resource with successful response."""
        # Set up mock
        self.mock_client.list_catalogs.return_value = [sample_catalog]
        
        # Get the resource function
        mock_mcp = MockFastMCP()
        register_product_resources(mock_mcp)
        get_summary_func = mock_mcp.resources["catalogs://summary"]
        
        # Call the function
        result = await get_summary_func()
        
        # Verify the result
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "catalog_summary" in parsed_result
        assert "total_catalogs" in parsed_result
        assert "description" in parsed_result
        assert len(parsed_result["catalog_summary"]) == 1
        
        # Verify summary format
        summary_item = parsed_result["catalog_summary"][0]
        assert summary_item["uid"] == "test-cards"
        assert summary_item["title"] == "Test Cards"
        assert summary_item["resource_uri"] == "catalogs://test-cards"