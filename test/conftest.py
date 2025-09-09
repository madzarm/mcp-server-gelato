"""Shared pytest fixtures and configuration for Gelato MCP Server tests."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import modules after path setup
from src.config import Settings
from src.client.gelato_client import GelatoClient
from src.models.orders import OrderSummary, SearchOrdersResponse, OrderDetail
from src.models.products import Catalog, CatalogDetail, ProductAttribute, ProductAttributeValue


@pytest.fixture
def test_settings():
    """Fixture providing test settings."""
    return Settings(
        gelato_api_key="test_api_key_minimum_10_chars",
        gelato_base_url="https://test.gelatoapis.com",
        gelato_product_url="https://test-product.gelatoapis.com",
        timeout=30.0,
        max_retries=3
    )


@pytest.fixture
def mock_httpx_client():
    """Fixture providing a mock httpx client."""
    client = MagicMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_gelato_client(test_settings, mock_httpx_client):
    """Fixture providing a mock Gelato client."""
    client = GelatoClient("test_api_key_minimum_10_chars", test_settings)
    client.session = mock_httpx_client
    return client


@pytest.fixture
def sample_catalog():
    """Fixture providing sample catalog data."""
    return Catalog(
        catalogUid="test-cards",
        title="Test Cards"
    )


@pytest.fixture
def sample_catalog_detail():
    """Fixture providing sample catalog detail data."""
    return CatalogDetail(
        catalogUid="test-cards",
        title="Test Cards",
        productAttributes=[
            ProductAttribute(
                productAttributeUid="size",
                title="Size",
                values=[
                    ProductAttributeValue(productAttributeValueUid="a5", title="A5"),
                    ProductAttributeValue(productAttributeValueUid="a4", title="A4")
                ]
            )
        ]
    )


@pytest.fixture
def sample_order_summary():
    """Fixture providing sample order summary data."""
    from datetime import datetime
    return OrderSummary(
        id="test-order-123",
        orderType="order",
        orderReferenceId="ref-123",
        customerReferenceId="cust-123",
        fulfillmentStatus="shipped",
        financialStatus="paid",
        currency="USD",
        createdAt=datetime(2024, 1, 1, 10, 0, 0),
        updatedAt=datetime(2024, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_order_detail(sample_order_summary):
    """Fixture providing sample order detail data."""
    return OrderDetail(
        id=sample_order_summary.id,
        orderType=sample_order_summary.orderType,
        orderReferenceId=sample_order_summary.orderReferenceId,
        customerReferenceId=sample_order_summary.customerReferenceId,
        fulfillmentStatus=sample_order_summary.fulfillmentStatus,
        financialStatus=sample_order_summary.financialStatus,
        currency=sample_order_summary.currency,
        createdAt=sample_order_summary.createdAt,
        updatedAt=sample_order_summary.updatedAt,
        items=[]
    )


@pytest.fixture
def sample_search_response(sample_order_summary):
    """Fixture providing sample search orders response."""
    return SearchOrdersResponse(
        orders=[sample_order_summary]
    )


@pytest.fixture
def mock_fastmcp_context():
    """Fixture providing a mock FastMCP context."""
    context = MagicMock()
    
    # Mock the client access path for tools
    mock_client = AsyncMock()
    context.request_context.lifespan_context = {"client": mock_client}
    
    # Mock logging methods
    context.debug = AsyncMock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    
    return context


@pytest.fixture(autouse=True)
def set_test_env():
    """Automatically set test environment variables."""
    os.environ["GELATO_API_KEY"] = "test_api_key_minimum_10_chars"
    os.environ["DEBUG"] = "false"
    yield
    # Cleanup
    if "GELATO_API_KEY" in os.environ:
        del os.environ["GELATO_API_KEY"]
    if "DEBUG" in os.environ:
        del os.environ["DEBUG"]


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data, status_code=200, text=None):
        self.json_data = json_data
        self.status_code = status_code
        if text is None and json_data is not None:
            try:
                # Try to serialize with default datetime handler
                self._text = json.dumps(json_data, default=str)
            except (TypeError, ValueError):
                # Fallback to string representation
                self._text = str(json_data)
        else:
            self._text = text or ""
    
    def json(self):
        return self.json_data
    
    @property
    def text(self):
        return self._text


@pytest.fixture
def mock_response():
    """Fixture providing a mock response factory."""
    return MockResponse


# Configure pytest asyncio
pytest_plugins = ['pytest_asyncio']