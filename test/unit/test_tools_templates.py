"""Unit tests for template tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.templates import register_template_tools
from src.utils.exceptions import GelatoAPIError, TemplateNotFoundError


class MockFastMCP:
    """Mock FastMCP class for testing tool registration."""
    
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        """Mock tool decorator."""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


class TestTemplateToolRegistration:
    """Test cases for template tool registration."""
    
    def test_register_template_tools(self):
        """Test that template tools are registered correctly."""
        mock_mcp = MockFastMCP()
        
        register_template_tools(mock_mcp)
        
        # Check that expected tools are registered
        expected_tools = ["get_template"]
        
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
            assert callable(mock_mcp.tools[tool_name])


class TestGetTemplateTool:
    """Test cases for get_template tool function."""
    
    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()
        
        # Register tools to get access to the get template function
        mock_mcp = MockFastMCP()
        register_template_tools(mock_mcp)
        self.get_template = mock_mcp.tools["get_template"]
    
    async def test_get_template_success(self):
        """Test successful template retrieval."""
        template_id = "c12a363e-0d4e-4d96-be4b-bf4138eb8743"
        
        # Mock successful API response with all fields from the spec
        mock_template = {
            "id": template_id,
            "templateName": "Template For Unisex Crewneck T-shirt",
            "title": "Classic Unisex Crewneck T-shirt",
            "description": "<div><p>A classic unisex t-shirt that works well with any outfit. Made of a heavier cotton with a double-stitched neckline and sleeves.</p></div>",
            "previewUrl": "https://gelato-api-test.s3.eu-west-1.amazonaws.com/ecommerce/store_product_image/448b66a9-b7bb-410f-a6ae-50ba2474fcf8/preview",
            "variants": [
                {
                    "id": "83e30e31-0aee-4eca-8a8f-dceb2455cdc1",
                    "title": "White - M",
                    "productUid": "apparel_product_gca_t-shirt_gsc_crewneck_gcu_unisex_gqa_classic_gsi_m_gco_white_gpr_4-0",
                    "variantOptions": [{"name": "Size", "value": "M"}],
                    "imagePlaceholders": [
                        {
                            "name": "ImageFront",
                            "printArea": "front",
                            "height": 137.25,
                            "width": 244
                        }
                    ]
                }
            ],
            "productType": "Printable Material",
            "vendor": "Gelato",
            "createdAt": "2023-06-13T11:02:47+0000",
            "updatedAt": "2023-06-13T11:02:47+0000"
        }
        
        from src.models.templates import Template
        self.mock_client.get_template.return_value = Template(**mock_template)
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify result
        assert result["success"] is True
        assert result["data"]["id"] == template_id
        assert result["data"]["templateName"] == "Template For Unisex Crewneck T-shirt"
        assert result["data"]["title"] == "Classic Unisex Crewneck T-shirt"
        assert len(result["data"]["variants"]) == 1
        assert result["data"]["variants"][0]["title"] == "White - M"
        assert result["data"]["productType"] == "Printable Material"
        assert result["data"]["vendor"] == "Gelato"
        assert "Successfully retrieved template" in result["message"]
        
        # Verify API was called correctly
        self.mock_client.get_template.assert_called_once_with(template_id)
        
        # Verify logging
        self.mock_context.info.assert_called()
    
    async def test_get_template_minimal_response(self):
        """Test template retrieval with minimal required fields only."""
        template_id = "minimal-template-id"
        
        # Mock response with only required fields
        mock_template = {
            "id": template_id,
            "templateName": "Minimal Template",
            "title": "Minimal Title",
            "description": "Minimal description",
            "previewUrl": "https://example.com/preview.jpg",
            "variants": [],
            "createdAt": "2023-06-13T11:02:47+0000",
            "updatedAt": "2023-06-13T11:02:47+0000"
            # No productType, vendor (optional fields)
        }
        
        from src.models.templates import Template
        self.mock_client.get_template.return_value = Template(**mock_template)
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify result
        assert result["success"] is True
        assert result["data"]["id"] == template_id
        assert result["data"]["productType"] is None  # Optional field
        assert result["data"]["vendor"] is None  # Optional field
        assert result["data"]["variants"] == []  # Empty variants list
        
        # Verify API was called correctly
        self.mock_client.get_template.assert_called_once_with(template_id)
    
    async def test_get_template_flexible_variants(self):
        """Test template retrieval with complex variant structures using Any."""
        template_id = "flexible-template-id"
        
        # Mock response with complex/flexible variant structures
        mock_template = {
            "id": template_id,
            "templateName": "Flexible Template",
            "title": "Flexible Title",
            "description": "Complex variants",
            "previewUrl": "https://example.com/preview.jpg",
            "variants": [
                # Complex variant with nested structures
                {
                    "id": "variant-1",
                    "title": "Complex Variant",
                    "productUid": "complex-product-uid",
                    "variantOptions": [
                        {"name": "Size", "value": "M"},
                        {"name": "Color", "value": "White"},
                        # Could have more complex nested data
                        {"name": "CustomOption", "value": {"nested": {"data": "whatever"}}}
                    ],
                    "imagePlaceholders": [
                        {
                            "name": "ImageFront",
                            "printArea": "front",
                            "height": 137.25,
                            "width": 244,
                            "customData": ["array", "of", "anything"]  # Flexible data
                        }
                    ],
                    "extraData": {"whatever": "structure", "api": "returns"}  # Any additional fields
                }
            ],
            "createdAt": "2023-06-13T11:02:47+0000",
            "updatedAt": "2023-06-13T11:02:47+0000"
        }
        
        from src.models.templates import Template
        self.mock_client.get_template.return_value = Template(**mock_template)
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify flexible data handling
        assert result["success"] is True
        variant = result["data"]["variants"][0]
        assert variant["title"] == "Complex Variant"
        assert variant["variantOptions"][2]["value"]["nested"]["data"] == "whatever"
        assert variant["imagePlaceholders"][0]["customData"] == ["array", "of", "anything"]
        assert variant["extraData"]["whatever"] == "structure"
    
    async def test_get_template_not_found(self):
        """Test template not found error handling."""
        template_id = "nonexistent-template-id"
        
        # Mock template not found error
        self.mock_client.get_template.side_effect = TemplateNotFoundError(template_id)
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_template"
        assert result["error"]["template_id"] == template_id
        assert result["error"]["status_code"] == 404
        assert "not found" in str(result["error"]["message"]).lower()
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_get_template_api_error(self):
        """Test general API error handling."""
        template_id = "test-template-id"
        
        # Mock API error
        api_error = GelatoAPIError("Internal server error", status_code=500)
        api_error.response_data = {"detail": "Server error"}
        self.mock_client.get_template.side_effect = api_error
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_template"
        assert result["error"]["template_id"] == template_id
        assert result["error"]["status_code"] == 500
        assert result["error"]["response_data"] == {"detail": "Server error"}
        assert "Internal server error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_get_template_unexpected_error(self):
        """Test unexpected error handling."""
        template_id = "test-template-id"
        
        # Mock unexpected error
        self.mock_client.get_template.side_effect = ValueError("Unexpected validation error")
        
        # Call the tool
        result = await self.get_template(
            self.mock_context,
            template_id=template_id
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_template"
        assert result["error"]["template_id"] == template_id
        assert "Unexpected error" in result["error"]["message"]
        assert "Unexpected validation error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()