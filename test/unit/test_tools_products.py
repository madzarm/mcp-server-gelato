"""Unit tests for product tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.products import register_product_tools
from src.models.products import SearchProductsResponse, Product, FilterHits
from src.utils.exceptions import GelatoAPIError, CatalogNotFoundError


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


class TestProductToolRegistration:
    """Test cases for product tool registration."""
    
    def test_register_product_tools(self):
        """Test that product tools are registered correctly."""
        mock_mcp = MockFastMCP()
        
        register_product_tools(mock_mcp)
        
        # Check that expected tools are registered
        expected_tools = ["search_products", "get_product_prices", "check_stock_availability"]
        
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
            assert callable(mock_mcp.tools[tool_name])


class TestSearchProductsTool:
    """Test cases for search_products tool function."""
    
    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()
        
        # Register tools to get access to the search function
        mock_mcp = MockFastMCP()
        register_product_tools(mock_mcp)
        self.search_products = mock_mcp.tools["search_products"]
    
    async def test_search_products_success_no_filters(self):
        """Test successful product search without filters."""
        catalog_uid = "posters"
        
        # Mock successful API response
        mock_product = Product(
            productUid="test-product-uid",
            attributes={"Orientation": "ver", "CoatingType": "none"},
            weight={"value": 100.5, "measureUnit": "grams"},
            dimensions={"Width": {"value": 210, "measureUnit": "mm"}},
            supportedCountries=["US", "CA"]
        )
        
        mock_response = SearchProductsResponse(
            products=[mock_product],
            hits=FilterHits(attributeHits={"Orientation": {"ver": 1, "hor": 2}})
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["data"]["products"]) == 1
        assert result["data"]["products"][0]["productUid"] == "test-product-uid"
        assert result["data"]["pagination"]["count"] == 1
        assert result["data"]["pagination"]["has_more"] is False
        assert result["data"]["search_params"]["catalog_uid"] == catalog_uid
        assert result["message"] == "Found 1 products in catalog 'posters'"
        
        # Verify API was called correctly
        self.mock_client.search_products.assert_called_once()
        call_args = self.mock_client.search_products.call_args
        assert call_args[0][0] == catalog_uid  # catalog_uid
        assert call_args[0][1].attributeFilters is None  # no filters
        assert call_args[0][1].limit == 50  # default limit
        assert call_args[0][1].offset == 0  # default offset
        
        # Verify logging
        self.mock_context.info.assert_called()
        self.mock_context.debug.assert_called()
    
    async def test_search_products_success_with_filters(self):
        """Test successful product search with attribute filters."""
        catalog_uid = "posters"
        filters = {"Orientation": ["ver"], "CoatingType": ["none", "glossy-coating"]}
        
        # Mock successful API response with multiple products
        mock_products = [
            Product(
                productUid="product-1",
                attributes={"Orientation": "ver", "CoatingType": "none"},
                weight={"value": 100.5, "measureUnit": "grams"},
                dimensions={"Width": {"value": 210, "measureUnit": "mm"}}
            ),
            Product(
                productUid="product-2",
                attributes={"Orientation": "ver", "CoatingType": "glossy-coating"},
                weight={"value": 105.0, "measureUnit": "grams"},
                dimensions={"Width": {"value": 210, "measureUnit": "mm"}}
            )
        ]
        
        mock_response = SearchProductsResponse(
            products=mock_products,
            hits=FilterHits(attributeHits={
                "Orientation": {"ver": 2, "hor": 5},
                "CoatingType": {"none": 1, "glossy-coating": 1, "matt-coating": 3}
            })
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Call the tool with filters and custom pagination
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid,
            attribute_filters=filters,
            limit=10,
            offset=5
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["data"]["products"]) == 2
        assert result["data"]["products"][0]["productUid"] == "product-1"
        assert result["data"]["products"][1]["productUid"] == "product-2"
        assert result["data"]["pagination"]["limit"] == 10
        assert result["data"]["pagination"]["offset"] == 5
        assert result["data"]["search_params"]["attribute_filters"] == filters
        assert "hits" in result["data"]
        assert "attributeHits" in result["data"]["hits"]
        
        # Verify API was called with correct parameters
        call_args = self.mock_client.search_products.call_args
        assert call_args[0][0] == catalog_uid
        assert call_args[0][1].attributeFilters == filters
        assert call_args[0][1].limit == 10
        assert call_args[0][1].offset == 5
    
    async def test_search_products_pagination_has_more(self):
        """Test search products with pagination indicating more results."""
        catalog_uid = "apparel"
        limit = 2
        
        # Mock response with exactly 'limit' number of products (indicates more results)
        mock_products = [
            Product(
                productUid=f"product-{i}",
                attributes={"Size": "M"},
                weight={"value": 100.0, "measureUnit": "grams"},
                dimensions={"Width": {"value": 300, "measureUnit": "mm"}}
            )
            for i in range(limit)
        ]
        
        mock_response = SearchProductsResponse(
            products=mock_products,
            hits=FilterHits(attributeHits={"Size": {"S": 10, "M": 15, "L": 20}})
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid,
            limit=limit,
            offset=10
        )
        
        # Verify pagination indicates more results
        assert result["success"] is True
        assert result["data"]["pagination"]["has_more"] is True
        assert "may have more results" in result["message"]
        assert "offset=12" in result["message"]  # suggests next offset
    
    async def test_search_products_no_results(self):
        """Test search products with no results."""
        catalog_uid = "mugs"
        filters = {"Color": ["nonexistent-color"]}
        
        # Mock empty response
        mock_response = SearchProductsResponse(
            products=[],
            hits=FilterHits(attributeHits={"Color": {"red": 5, "blue": 3}})
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid,
            attribute_filters=filters
        )
        
        # Verify empty results
        assert result["success"] is True
        assert len(result["data"]["products"]) == 0
        assert result["data"]["pagination"]["count"] == 0
        assert result["data"]["pagination"]["has_more"] is False
        assert "No products found in catalog 'mugs' matching the specified filters" in result["message"]
    
    async def test_search_products_no_results_no_filters(self):
        """Test search products with no results and no filters."""
        catalog_uid = "empty-catalog"
        
        # Mock empty response
        mock_response = SearchProductsResponse(
            products=[],
            hits=FilterHits(attributeHits={})
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid
        )
        
        # Verify empty results
        assert result["success"] is True
        assert len(result["data"]["products"]) == 0
        assert "No products found in catalog 'empty-catalog'" in result["message"]
    
    async def test_search_products_catalog_not_found(self):
        """Test search products with non-existent catalog."""
        catalog_uid = "nonexistent-catalog"
        
        # Mock catalog not found error
        self.mock_client.search_products.side_effect = CatalogNotFoundError(catalog_uid)
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "search_products"
        assert result["error"]["catalog_uid"] == catalog_uid
        assert result["error"]["status_code"] == 404
        assert "not found" in str(result["error"]["message"]).lower()
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_search_products_api_error(self):
        """Test search products with general API error."""
        catalog_uid = "posters"
        
        # Mock API error
        api_error = GelatoAPIError("Internal server error", status_code=500)
        api_error.response_data = {"detail": "Server error"}
        self.mock_client.search_products.side_effect = api_error
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "search_products"
        assert result["error"]["catalog_uid"] == catalog_uid
        assert result["error"]["status_code"] == 500
        assert result["error"]["response_data"] == {"detail": "Server error"}
        assert "Internal server error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_search_products_unexpected_error(self):
        """Test search products with unexpected error."""
        catalog_uid = "posters"
        
        # Mock unexpected error
        self.mock_client.search_products.side_effect = ValueError("Unexpected validation error")
        
        # Call the tool
        result = await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "search_products"
        assert result["error"]["catalog_uid"] == catalog_uid
        assert "Unexpected error" in result["error"]["message"]
        assert "Unexpected validation error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_search_products_parameter_validation(self):
        """Test that search products tool passes parameters correctly."""
        catalog_uid = "test-catalog"
        filters = {"TestAttr": ["value1", "value2"]}
        limit = 25
        offset = 100
        
        # Mock successful response
        mock_response = SearchProductsResponse(
            products=[],
            hits=FilterHits(attributeHits={})
        )
        self.mock_client.search_products.return_value = mock_response
        
        # Call tool with all parameters
        await self.search_products(
            self.mock_context,
            catalog_uid=catalog_uid,
            attribute_filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Verify all parameters were passed correctly to the client
        call_args = self.mock_client.search_products.call_args
        request = call_args[0][1]  # SearchProductsRequest object
        
        assert call_args[0][0] == catalog_uid
        assert request.attributeFilters == filters
        assert request.limit == limit
        assert request.offset == offset


class TestSearchProductsIntegration:
    """Integration-style tests for search_products tool."""
    
    def setup_method(self):
        """Set up integration tests."""
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()
        
        mock_mcp = MockFastMCP()
        register_product_tools(mock_mcp)
        self.search_products = mock_mcp.tools["search_products"]
    
    async def test_realistic_poster_search(self):
        """Test realistic poster search with typical filters."""
        # Simulate a real poster search
        mock_products = [
            Product(
                productUid="8pp-accordion-fold_pf_dl_pt_100-lb-text-coated-silk_cl_4-4_ft_8pp-accordion-fold-ver_ver",
                attributes={
                    "CoatingType": "none",
                    "ColorType": "4-4", 
                    "FoldingType": "8pp-accordion-fold-ver",
                    "Orientation": "ver",
                    "PaperFormat": "DL",
                    "PaperType": "100-lb-text-coated-silk",
                    "ProductStatus": "activated",
                    "ProtectionType": "none",
                    "SpotFinishingType": "none",
                    "Variable": "no"
                },
                weight={"value": 12.308, "measureUnit": "grams"},
                dimensions={
                    "Thickness": {"value": 0.14629, "measureUnit": "mm"},
                    "Width": {"value": 99, "measureUnit": "mm"},
                    "Height": {"value": 210, "measureUnit": "mm"}
                },
                supportedCountries=["US", "CA", "GB"]
            )
        ]
        
        mock_response = SearchProductsResponse(
            products=mock_products,
            hits=FilterHits(attributeHits={
                "CoatingType": {
                    "glossy-protection": 1765,
                    "matt-protection": 1592,
                    "glossy-coating": 102,
                    "none": 2137
                },
                "Orientation": {
                    "hor": 3041,
                    "ver": 1590
                }
            })
        )
        
        self.mock_client.search_products.return_value = mock_response
        
        # Search for vertical posters with no coating
        result = await self.search_products(
            self.mock_context,
            catalog_uid="posters",
            attribute_filters={"Orientation": ["ver"], "CoatingType": ["none"]},
            limit=50
        )
        
        # Verify comprehensive response
        assert result["success"] is True
        assert len(result["data"]["products"]) == 1
        
        product = result["data"]["products"][0]
        assert product["productUid"] == "8pp-accordion-fold_pf_dl_pt_100-lb-text-coated-silk_cl_4-4_ft_8pp-accordion-fold-ver_ver"
        assert product["attributes"]["Orientation"] == "ver"
        assert product["attributes"]["CoatingType"] == "none"
        assert product["weight"]["value"] == 12.308
        assert product["weight"]["measureUnit"] == "grams"
        assert "Height" in product["dimensions"]
        assert product["supportedCountries"] == ["US", "CA", "GB"]
        
        # Verify hits data
        hits = result["data"]["hits"]["attributeHits"]
        assert hits["CoatingType"]["none"] == 2137
        assert hits["Orientation"]["ver"] == 1590


class TestGetProductTool:
    """Test cases for get_product tool function."""
    
    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()
        
        # Register tools to get access to the get product function
        mock_mcp = MockFastMCP()
        register_product_tools(mock_mcp)
        self.get_product = mock_mcp.tools["get_product"]
    
    async def test_get_product_success(self):
        """Test successful product retrieval."""
        product_uid = "8pp-accordion-fold_pf_dl_pt_100-lb-text-coated-silk_cl_4-4_ft_8pp-accordion-fold-ver_ver"
        
        # Mock successful API response with all fields from the spec
        mock_product_detail = {
            "productUid": product_uid,
            "attributes": {
                "CoatingType": "none",
                "ColorType": "4-4",
                "FoldingType": "8pp-accordion-fold-ver",
                "Orientation": "ver",
                "PaperFormat": "DL",
                "PaperType": "100-lb-text-coated-silk",
                "ProductStatus": "activated",
                "ProtectionType": "none",
                "SpotFinishingType": "none",
                "Variable": "no"
            },
            "weight": {"value": 1.341, "measureUnit": "grams"},
            "supportedCountries": ["US", "CA"],
            "notSupportedCountries": ["BD", "BM", "BR", "AI", "DO", "IS"],
            "isStockable": False,
            "isPrintable": True,
            "validPageCounts": [5, 10, 20, 30]
        }
        
        from src.models.products import ProductDetail
        self.mock_client.get_product.return_value = ProductDetail(**mock_product_detail)
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify result
        assert result["success"] is True
        assert result["data"]["productUid"] == product_uid
        assert result["data"]["attributes"]["CoatingType"] == "none"
        assert result["data"]["weight"]["value"] == 1.341
        assert result["data"]["supportedCountries"] == ["US", "CA"]
        assert result["data"]["notSupportedCountries"] == ["BD", "BM", "BR", "AI", "DO", "IS"]
        assert result["data"]["isStockable"] is False
        assert result["data"]["isPrintable"] is True
        assert result["data"]["validPageCounts"] == [5, 10, 20, 30]
        assert "Successfully retrieved product" in result["message"]
        
        # Verify API was called correctly
        self.mock_client.get_product.assert_called_once_with(product_uid)
        
        # Verify logging
        self.mock_context.info.assert_called()
    
    async def test_get_product_minimal_response(self):
        """Test product retrieval with minimal required fields only."""
        product_uid = "cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor"
        
        # Mock response with only required fields
        mock_product_detail = {
            "productUid": product_uid,
            "attributes": {"CardType": "business", "Orientation": "hor"},
            "weight": {"value": 2.5, "measureUnit": "grams"},
            "supportedCountries": ["US"],
            "notSupportedCountries": [],
            "isStockable": True,
            "isPrintable": True
            # validPageCounts is optional and not included
        }
        
        from src.models.products import ProductDetail
        self.mock_client.get_product.return_value = ProductDetail(**mock_product_detail)
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify result
        assert result["success"] is True
        assert result["data"]["productUid"] == product_uid
        assert result["data"]["validPageCounts"] is None  # Optional field
        assert result["data"]["isStockable"] is True
        assert result["data"]["isPrintable"] is True
        
        # Verify API was called correctly
        self.mock_client.get_product.assert_called_once_with(product_uid)
    
    async def test_get_product_flexible_data_types(self):
        """Test product retrieval with flexible weight and dimensions."""
        product_uid = "flexible-product-uid"
        
        # Mock response with flexible data types using Any
        mock_product_detail = {
            "productUid": product_uid,
            "attributes": {"Type": "flexible"},
            "weight": "lightweight",  # String instead of object
            "supportedCountries": ["US", "CA"],
            "notSupportedCountries": ["BD"],
            "isStockable": False,
            "isPrintable": True,
            "dimensions": {  # Complex dimensions structure
                "Width": {"value": 210, "measureUnit": "mm"},
                "Assemblytype": "fixed_one_stack",  # The problematic string value
                "ComplexField": {"nested": {"data": "whatever"}}
            }
        }
        
        from src.models.products import ProductDetail
        self.mock_client.get_product.return_value = ProductDetail(**mock_product_detail)
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify flexible data handling
        assert result["success"] is True
        assert result["data"]["weight"] == "lightweight"  # String weight
        assert result["data"]["dimensions"]["Assemblytype"] == "fixed_one_stack"  # String dimension
        assert result["data"]["dimensions"]["ComplexField"]["nested"]["data"] == "whatever"
    
    async def test_get_product_not_found(self):
        """Test product not found error handling."""
        product_uid = "nonexistent-product-uid"
        
        # Mock product not found error
        from src.utils.exceptions import ProductNotFoundError
        self.mock_client.get_product.side_effect = ProductNotFoundError(product_uid)
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_product"
        assert result["error"]["product_uid"] == product_uid
        assert result["error"]["status_code"] == 404
        assert "not found" in str(result["error"]["message"]).lower()
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_get_product_api_error(self):
        """Test general API error handling."""
        product_uid = "test-product-uid"
        
        # Mock API error
        from src.utils.exceptions import GelatoAPIError
        api_error = GelatoAPIError("Internal server error", status_code=500)
        api_error.response_data = {"detail": "Server error"}
        self.mock_client.get_product.side_effect = api_error
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_product"
        assert result["error"]["product_uid"] == product_uid
        assert result["error"]["status_code"] == 500
        assert result["error"]["response_data"] == {"detail": "Server error"}
        assert "Internal server error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()
    
    async def test_get_product_unexpected_error(self):
        """Test unexpected error handling."""
        product_uid = "test-product-uid"
        
        # Mock unexpected error
        self.mock_client.get_product.side_effect = ValueError("Unexpected validation error")
        
        # Call the tool
        result = await self.get_product(
            self.mock_context,
            product_uid=product_uid
        )
        
        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_product"
        assert result["error"]["product_uid"] == product_uid
        assert "Unexpected error" in result["error"]["message"]
        assert "Unexpected validation error" in result["error"]["message"]
        
        # Verify error was logged
        self.mock_context.error.assert_called_once()

class TestGetProductPricesTool:
    """Test cases for get_product_prices tool function."""

    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()

        # Register tools to get access to the get product prices function
        mock_mcp = MockFastMCP()
        register_product_tools(mock_mcp)
        self.get_product_prices = mock_mcp.tools["get_product_prices"]

    async def test_get_product_prices_success_basic(self):
        """Test successful product price retrieval with only product_uid."""
        product_uid = "cards_pf_bb_pt_110-lb-cover-uncoated_cl_4-0_hor"

        # Mock successful API response
        from src.models.products import ProductPrice
        mock_prices = [
            ProductPrice(
                productUid=product_uid,
                country="US",
                quantity=20,
                price=87.883871,
                currency="USD",
                pageCount=None
            ),
            ProductPrice(
                productUid=product_uid,
                country="US",
                quantity=400,
                price=1365.982879,
                currency="USD",
                pageCount=None
            ),
            ProductPrice(
                productUid=product_uid,
                country="US",
                quantity=700,
                price=2151.28277,
                currency="USD",
                pageCount=None
            )
        ]

        self.mock_client.get_product_prices.return_value = mock_prices

        # Call the tool
        result = await self.get_product_prices(
            self.mock_context,
            product_uid=product_uid
        )

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["prices"]) == 3
        assert result["data"]["prices"][0]["productUid"] == product_uid
        assert result["data"]["prices"][0]["country"] == "US"
        assert result["data"]["prices"][0]["quantity"] == 20
        assert result["data"]["prices"][0]["price"] == 87.883871
        assert result["data"]["prices"][0]["currency"] == "USD"
        assert result["data"]["prices"][0]["pageCount"] is None
        assert result["data"]["search_params"]["product_uid"] == product_uid
        assert result["data"]["search_params"]["country"] is None
        assert result["data"]["search_params"]["currency"] is None
        assert result["data"]["search_params"]["page_count"] is None
        assert "Found 3 price points for product" in result["message"]

        # Verify API was called correctly
        self.mock_client.get_product_prices.assert_called_once_with(
            product_uid=product_uid,
            country=None,
            currency=None,
            page_count=None
        )

        # Verify logging
        self.mock_context.info.assert_called()
        self.mock_context.debug.assert_called()

    async def test_get_product_prices_empty_results(self):
        """Test product prices with no results."""
        product_uid = "nonexistent-product"

        # Mock empty response
        self.mock_client.get_product_prices.return_value = []

        # Call the tool
        result = await self.get_product_prices(
            self.mock_context,
            product_uid=product_uid
        )

        # Verify empty results
        assert result["success"] is True
        assert len(result["data"]["prices"]) == 0
        assert "No price information found for product" in result["message"]

    async def test_get_product_prices_product_not_found(self):
        """Test product prices with non-existent product."""
        product_uid = "nonexistent-product-uid"

        # Mock product not found error
        from src.utils.exceptions import ProductNotFoundError
        self.mock_client.get_product_prices.side_effect = ProductNotFoundError(product_uid)

        # Call the tool
        result = await self.get_product_prices(
            self.mock_context,
            product_uid=product_uid
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_product_prices"
        assert result["error"]["product_uid"] == product_uid
        assert result["error"]["status_code"] == 404
        assert "not found" in str(result["error"]["message"]).lower()

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_get_product_prices_api_error(self):
        """Test product prices with general API error."""
        product_uid = "test-product-uid"

        # Mock API error
        api_error = GelatoAPIError("Internal server error", status_code=500)
        api_error.response_data = {"detail": "Server error"}
        self.mock_client.get_product_prices.side_effect = api_error

        # Call the tool
        result = await self.get_product_prices(
            self.mock_context,
            product_uid=product_uid
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "get_product_prices"
        assert result["error"]["product_uid"] == product_uid
        assert result["error"]["status_code"] == 500
        assert result["error"]["response_data"] == {"detail": "Server error"}
        assert "Internal server error" in result["error"]["message"]

        # Verify error was logged
        self.mock_context.error.assert_called_once()


class TestCheckStockAvailabilityTool:
    """Test cases for check_stock_availability tool function."""

    def setup_method(self):
        """Set up each test."""
        # Create a mock context with client access
        self.mock_context = MagicMock()
        self.mock_client = AsyncMock()
        self.mock_context.request_context.lifespan_context = {"client": self.mock_client}
        self.mock_context.info = AsyncMock()
        self.mock_context.debug = AsyncMock()
        self.mock_context.error = AsyncMock()

        # Register tools to get access to the check stock availability function
        mock_mcp = MockFastMCP()
        register_product_tools(mock_mcp)
        self.check_stock_availability = mock_mcp.tools["check_stock_availability"]

    async def test_check_stock_availability_success_single_product(self):
        """Test stock availability check with single product."""
        products = ["wall_hanger_product_whs_290-mm_whc_white_whm_wood_whp_w14xt20-mm"]

        # Mock successful API response
        from src.models.products import StockAvailabilityResponse, ProductAvailability, RegionAvailability

        mock_response = StockAvailabilityResponse(
            productsAvailability=[
                ProductAvailability(
                    productUid=products[0],
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="in-stock",
                            replenishmentDate=None
                        ),
                        RegionAvailability(
                            stockRegionUid="EU",
                            status="out-of-stock-replenishable",
                            replenishmentDate="2024-02-13"
                        ),
                        RegionAvailability(
                            stockRegionUid="UK",
                            status="in-stock",
                            replenishmentDate=None
                        )
                    ]
                )
            ]
        )

        self.mock_client.check_stock_availability.return_value = mock_response

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["productsAvailability"]) == 1

        product_availability = result["data"]["productsAvailability"][0]
        assert product_availability["productUid"] == products[0]
        assert len(product_availability["availability"]) == 3

        # Check specific availability statuses
        us_ca_availability = next(a for a in product_availability["availability"] if a["stockRegionUid"] == "US-CA")
        assert us_ca_availability["status"] == "in-stock"
        assert us_ca_availability["replenishmentDate"] is None

        eu_availability = next(a for a in product_availability["availability"] if a["stockRegionUid"] == "EU")
        assert eu_availability["status"] == "out-of-stock-replenishable"
        assert eu_availability["replenishmentDate"] == "2024-02-13"

        assert "Successfully checked stock availability for 1 products" in result["message"]

        # Verify API was called correctly
        self.mock_client.check_stock_availability.assert_called_once_with(products)

        # Verify logging
        self.mock_context.info.assert_called()

    async def test_check_stock_availability_success_multiple_products(self):
        """Test stock availability check with multiple products."""
        products = [
            "wall_hanger_product_whs_290-mm_whc_white_whm_wood_whp_w14xt20-mm",
            "frame_and_poster_product_frs_300x400-mm_frc_black_frm_wood_frp_w12xt22-mm"
        ]

        # Mock successful API response
        from src.models.products import StockAvailabilityResponse, ProductAvailability, RegionAvailability

        mock_response = StockAvailabilityResponse(
            productsAvailability=[
                ProductAvailability(
                    productUid=products[0],
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="in-stock",
                            replenishmentDate=None
                        )
                    ]
                ),
                ProductAvailability(
                    productUid=products[1],
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="non-stockable",
                            replenishmentDate=None
                        )
                    ]
                )
            ]
        )

        self.mock_client.check_stock_availability.return_value = mock_response

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["productsAvailability"]) == 2
        assert "Successfully checked stock availability for 2 products" in result["message"]

        # Verify API was called correctly
        self.mock_client.check_stock_availability.assert_called_once_with(products)

    async def test_check_stock_availability_empty_products_list(self):
        """Test stock availability check with empty products list."""
        products = []

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["message"] == "At least one product UID is required"
        assert result["error"]["operation"] == "check_stock_availability"

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_check_stock_availability_too_many_products(self):
        """Test stock availability check with too many products (>250)."""
        # Create 251 product UIDs
        products = [f"product-uid-{i}" for i in range(251)]

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["message"] == "Maximum 250 products allowed, got 251"
        assert result["error"]["operation"] == "check_stock_availability"

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_check_stock_availability_api_error_too_many_products(self):
        """Test stock availability with API error for too many products."""
        products = ["product1", "product2"]

        # Mock API error for too many products
        api_error = GelatoAPIError("Too many products requested: 273 of maximum 250.", status_code=400)
        api_error.response_data = {
            "code": "invalid_request_too_many_products",
            "message": "Too many products requested: 273 of maximum 250."
        }
        self.mock_client.check_stock_availability.side_effect = api_error

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "check_stock_availability"
        assert result["error"]["status_code"] == 400
        assert "Too many products requested" in result["error"]["message"]
        assert result["error"]["response_data"]["code"] == "invalid_request_too_many_products"

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_check_stock_availability_api_error_no_products(self):
        """Test stock availability with API error for no products."""
        products = ["product1"]

        # Mock API error for no products provided
        api_error = GelatoAPIError("No products provided, at least one is required.", status_code=400)
        api_error.response_data = {
            "code": "invalid_request_products_not_provided",
            "message": "No products provided, at least one is required."
        }
        self.mock_client.check_stock_availability.side_effect = api_error

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "check_stock_availability"
        assert result["error"]["status_code"] == 400
        assert "No products provided" in result["error"]["message"]
        assert result["error"]["response_data"]["code"] == "invalid_request_products_not_provided"

        # Verify error was logged
        self.mock_context.error.assert_called_once()

    async def test_check_stock_availability_mixed_statuses(self):
        """Test stock availability with mixed availability statuses."""
        products = [
            "existing-product",
            "non-existing-product",
            "non-stockable-product"
        ]

        # Mock API response with mixed statuses
        from src.models.products import StockAvailabilityResponse, ProductAvailability, RegionAvailability

        mock_response = StockAvailabilityResponse(
            productsAvailability=[
                ProductAvailability(
                    productUid="existing-product",
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="in-stock",
                            replenishmentDate=None
                        ),
                        RegionAvailability(
                            stockRegionUid="EU",
                            status="out-of-stock",
                            replenishmentDate=None
                        )
                    ]
                ),
                ProductAvailability(
                    productUid="non-existing-product",
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="not-supported",
                            replenishmentDate=None
                        ),
                        RegionAvailability(
                            stockRegionUid="EU",
                            status="not-supported",
                            replenishmentDate=None
                        )
                    ]
                ),
                ProductAvailability(
                    productUid="non-stockable-product",
                    availability=[
                        RegionAvailability(
                            stockRegionUid="US-CA",
                            status="non-stockable",
                            replenishmentDate=None
                        )
                    ]
                )
            ]
        )

        self.mock_client.check_stock_availability.return_value = mock_response

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify result
        assert result["success"] is True
        assert len(result["data"]["productsAvailability"]) == 3

        # Verify different statuses are present
        product_avails = result["data"]["productsAvailability"]

        # Check existing product has in-stock status
        existing_product = next(p for p in product_avails if p["productUid"] == "existing-product")
        us_ca_status = next(a["status"] for a in existing_product["availability"] if a["stockRegionUid"] == "US-CA")
        assert us_ca_status == "in-stock"

        # Check non-existing product has not-supported status
        non_existing_product = next(p for p in product_avails if p["productUid"] == "non-existing-product")
        us_ca_status = next(a["status"] for a in non_existing_product["availability"] if a["stockRegionUid"] == "US-CA")
        assert us_ca_status == "not-supported"

        # Check non-stockable product has non-stockable status
        non_stockable_product = next(p for p in product_avails if p["productUid"] == "non-stockable-product")
        us_ca_status = next(a["status"] for a in non_stockable_product["availability"] if a["stockRegionUid"] == "US-CA")
        assert us_ca_status == "non-stockable"

        assert "Successfully checked stock availability for 3 products" in result["message"]

    async def test_check_stock_availability_general_api_error(self):
        """Test stock availability with general API error."""
        products = ["product1"]

        # Mock general API error
        api_error = GelatoAPIError("We had a problem with our server. Problem reported. Try again later.", status_code=500)
        api_error.response_data = {
            "code": "internal_server_error",
            "message": "We had a problem with our server. Problem reported. Try again later."
        }
        self.mock_client.check_stock_availability.side_effect = api_error

        # Call the tool
        result = await self.check_stock_availability(
            self.mock_context,
            products=products
        )

        # Verify error response
        assert result["success"] is False
        assert result["error"]["operation"] == "check_stock_availability"
        assert result["error"]["status_code"] == 500
        assert "server" in result["error"]["message"].lower()

        # Verify error was logged
        self.mock_context.error.assert_called_once()
