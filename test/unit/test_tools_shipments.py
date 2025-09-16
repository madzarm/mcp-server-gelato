"""Unit tests for shipment tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.shipments import register_shipment_tools
from src.models.shipments import ShipmentMethodsResponse, ShipmentMethod
from src.utils.exceptions import GelatoAPIError


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


class TestShipmentToolRegistration:
    """Test cases for shipment tool registration."""

    def test_register_shipment_tools(self):
        """Test that shipment tools are registered correctly."""
        mock_mcp = MockFastMCP()

        register_shipment_tools(mock_mcp)

        # Check that expected tools are registered
        expected_tools = ["list_shipment_methods"]

        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
            assert callable(mock_mcp.tools[tool_name])


class TestListShipmentMethodsTool:
    """Test cases for list_shipment_methods tool function."""

    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()

        # Register tools to get access to the list function
        mock_mcp = MockFastMCP()
        register_shipment_tools(mock_mcp)
        self.list_shipment_methods = mock_mcp.tools["list_shipment_methods"]

    async def test_list_shipment_methods_success_no_filter(self):
        """Test successful shipment methods retrieval without country filter."""

        # Mock successful API response with sample data
        mock_methods = [
            ShipmentMethod(
                shipmentMethodUid="dhl_global_parcel",
                type="normal",
                name="DHL Global Parcel",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["AT", "BE", "BG", "CH", "CY", "CZ", "DK"]
            ),
            ShipmentMethod(
                shipmentMethodUid="tnt_parcel",
                type="normal",
                name="PostNL Standard",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["NL"]
            )
        ]

        mock_response = ShipmentMethodsResponse(shipmentMethods=mock_methods)
        self.mock_client.list_shipment_methods.return_value = mock_response

        # Call the tool
        result = await self.list_shipment_methods(self.mock_context)

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["shipment_methods"]) == 2
        assert result["data"]["shipment_methods"][0]["shipmentMethodUid"] == "dhl_global_parcel"
        assert result["data"]["shipment_methods"][0]["type"] == "normal"
        assert result["data"]["shipment_methods"][0]["name"] == "DHL Global Parcel"
        assert result["data"]["shipment_methods"][0]["hasTracking"] is True
        assert result["data"]["shipment_methods"][1]["supportedCountries"] == ["NL"]
        assert result["data"]["search_params"]["country"] is None
        assert "Found 2 shipment methods" in result["message"]

        # Verify API was called correctly
        self.mock_client.list_shipment_methods.assert_called_once_with(country=None)

        # Verify logging
        self.mock_context.info.assert_called()
        self.mock_context.debug.assert_called()

    async def test_list_shipment_methods_success_with_country_filter(self):
        """Test successful shipment methods retrieval with country filter."""
        country = "US"

        # Mock successful API response filtered for US
        mock_methods = [
            ShipmentMethod(
                shipmentMethodUid="tnt_global_pack",
                type="normal",
                name="PostNL Global Pack",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["AT", "AU", "BE", "US", "CA", "DE"]
            )
        ]

        mock_response = ShipmentMethodsResponse(shipmentMethods=mock_methods)
        self.mock_client.list_shipment_methods.return_value = mock_response

        # Call the tool with country filter
        result = await self.list_shipment_methods(
            self.mock_context,
            country=country
        )

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["shipment_methods"]) == 1
        assert result["data"]["shipment_methods"][0]["shipmentMethodUid"] == "tnt_global_pack"
        assert result["data"]["search_params"]["country"] == "US"
        assert "Found 1 shipment methods available for country 'US'" in result["message"]

        # Verify API was called with country filter
        self.mock_client.list_shipment_methods.assert_called_once_with(country="US")

    async def test_list_shipment_methods_empty_results(self):
        """Test shipment methods with no results."""
        country = "XX"  # Non-existent country

        # Mock empty response
        mock_response = ShipmentMethodsResponse(shipmentMethods=[])
        self.mock_client.list_shipment_methods.return_value = mock_response

        # Call the tool
        result = await self.list_shipment_methods(
            self.mock_context,
            country=country
        )

        # Verify empty results
        assert result["success"] is True
        assert len(result["data"]["shipment_methods"]) == 0
        assert result["data"]["search_params"]["country"] == "XX"
        assert "No shipment methods found for country 'XX'" in result["message"]

    async def test_list_shipment_methods_empty_results_no_filter(self):
        """Test shipment methods with no results and no filter."""

        # Mock empty response
        mock_response = ShipmentMethodsResponse(shipmentMethods=[])
        self.mock_client.list_shipment_methods.return_value = mock_response

        # Call the tool
        result = await self.list_shipment_methods(self.mock_context)

        # Verify empty results
        assert result["success"] is True
        assert len(result["data"]["shipment_methods"]) == 0
        assert "No shipment methods found" in result["message"]

    async def test_list_shipment_methods_api_error(self):
        """Test shipment methods with general API error."""

        # Mock API error
        api_error = GelatoAPIError("Internal server error", status_code=500)
        api_error.response_data = {"detail": "Server error"}
        self.mock_client.list_shipment_methods.side_effect = api_error

        # Call the tool
        result = await self.list_shipment_methods(self.mock_context)

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "list_shipment_methods"
        assert result["error"]["country"] is None
        assert result["error"]["status_code"] == 500
        assert result["error"]["response_data"] == {"detail": "Server error"}
        assert "Internal server error" in result["error"]["message"]

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_list_shipment_methods_api_error_with_country(self):
        """Test shipment methods with API error when using country filter."""
        country = "US"

        # Mock API error
        api_error = GelatoAPIError("Bad request", status_code=400)
        self.mock_client.list_shipment_methods.side_effect = api_error

        # Call the tool
        result = await self.list_shipment_methods(
            self.mock_context,
            country=country
        )

        # Verify error response includes country
        assert result["success"] is False
        assert result["error"]["country"] == "US"
        assert result["error"]["status_code"] == 400

    async def test_list_shipment_methods_unexpected_error(self):
        """Test shipment methods with unexpected error."""

        # Mock unexpected error
        self.mock_client.list_shipment_methods.side_effect = ValueError("Unexpected validation error")

        # Call the tool
        result = await self.list_shipment_methods(self.mock_context)

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "list_shipment_methods"
        assert result["error"]["country"] is None
        assert "Unexpected error" in result["error"]["message"]
        assert "Unexpected validation error" in result["error"]["message"]

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_list_shipment_methods_realistic_response(self):
        """Test with realistic shipment methods response."""

        # Mock realistic response based on the API documentation
        mock_methods = [
            ShipmentMethod(
                shipmentMethodUid="dhl_global_parcel",
                type="normal",
                name="DHL Global Parcel",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=[
                    "AT", "BE", "BG", "CH", "CY", "CZ", "DK", "EE", "FI", "FO",
                    "FR", "GB", "GI", "GL", "GR", "HR", "HU", "IE", "IT", "LT",
                    "LU", "LV", "MT", "NG", "NL", "NO", "PL", "PT", "RO", "SE",
                    "SI", "SK"
                ]
            ),
            ShipmentMethod(
                shipmentMethodUid="dhl_parcel",
                type="normal",
                name="DHL Parcel",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["DE"]
            ),
            ShipmentMethod(
                shipmentMethodUid="tnt_global_pack",
                type="normal",
                name="PostNL Global Pack",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=[
                    "AT", "AU", "AX", "BE", "BG", "BR", "CA", "CH", "CN", "CY",
                    "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HK", "HR",
                    "HU", "IE", "IN", "IT", "JP", "LT", "LU", "LV", "MT", "NO",
                    "NZ", "PL", "PT", "RO", "RU", "SE", "SI", "SK", "TR", "US", "ZA"
                ]
            )
        ]

        mock_response = ShipmentMethodsResponse(shipmentMethods=mock_methods)
        self.mock_client.list_shipment_methods.return_value = mock_response

        # Call the tool
        result = await self.list_shipment_methods(self.mock_context)

        # Verify comprehensive response
        assert result["success"] is True
        assert len(result["data"]["shipment_methods"]) == 3

        # Verify first method details
        first_method = result["data"]["shipment_methods"][0]
        assert first_method["shipmentMethodUid"] == "dhl_global_parcel"
        assert first_method["type"] == "normal"
        assert first_method["name"] == "DHL Global Parcel"
        assert first_method["isBusiness"] is True
        assert first_method["isPrivate"] is True
        assert first_method["hasTracking"] is True
        assert "AT" in first_method["supportedCountries"]
        assert "SK" in first_method["supportedCountries"]

        # Verify third method (global pack)
        global_method = result["data"]["shipment_methods"][2]
        assert global_method["shipmentMethodUid"] == "tnt_global_pack"
        assert "US" in global_method["supportedCountries"]
        assert "ZA" in global_method["supportedCountries"]

        # Verify summary message
        assert "Found 3 shipment methods" in result["message"]


class TestShipmentMethodsIntegration:
    """Integration-style tests for shipment methods tool."""

    def setup_method(self):
        """Set up integration tests."""
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()

        mock_mcp = MockFastMCP()
        register_shipment_tools(mock_mcp)
        self.list_shipment_methods = mock_mcp.tools["list_shipment_methods"]

    async def test_country_filtering_workflow(self):
        """Test realistic workflow of filtering by country."""
        # Step 1: Get all shipment methods
        all_methods = [
            ShipmentMethod(
                shipmentMethodUid="dhl_global_parcel",
                type="normal",
                name="DHL Global Parcel",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["US", "CA", "GB", "DE"]
            ),
            ShipmentMethod(
                shipmentMethodUid="dhl_parcel",
                type="normal",
                name="DHL Parcel",
                isBusiness=True,
                isPrivate=True,
                hasTracking=True,
                supportedCountries=["DE"]
            )
        ]

        # Mock API to return all methods first
        self.mock_client.list_shipment_methods.return_value = ShipmentMethodsResponse(
            shipmentMethods=all_methods
        )

        # Get all methods
        result_all = await self.list_shipment_methods(self.mock_context)
        assert result_all["success"] is True
        assert len(result_all["data"]["shipment_methods"]) == 2
        assert result_all["data"]["search_params"]["country"] is None

        # Step 2: Filter by specific country (DE)
        de_methods = [method for method in all_methods if "DE" in method.supportedCountries]
        self.mock_client.list_shipment_methods.return_value = ShipmentMethodsResponse(
            shipmentMethods=de_methods
        )

        # Get methods for Germany
        result_de = await self.list_shipment_methods(self.mock_context, country="DE")
        assert result_de["success"] is True
        assert len(result_de["data"]["shipment_methods"]) == 2  # Both support DE
        assert result_de["data"]["search_params"]["country"] == "DE"

        # Verify both API calls were made with correct parameters
        assert self.mock_client.list_shipment_methods.call_count == 2
        calls = self.mock_client.list_shipment_methods.call_args_list
        assert calls[0][1] == {"country": None}  # First call - no filter
        assert calls[1][1] == {"country": "DE"}  # Second call - DE filter