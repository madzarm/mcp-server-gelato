"""Gelato API client for making authenticated requests."""

import asyncio
import json
from typing import List, Optional

import httpx
from pydantic import ValidationError

from ..config import Settings
from ..models.orders import CreateOrderRequest, OrderDetail, SearchOrdersParams, SearchOrdersResponse
from ..models.products import Catalog, CatalogDetail, SearchProductsRequest, SearchProductsResponse, ProductPrice
from ..models.shipments import ShipmentMethodsResponse
from ..utils.auth import get_auth_headers, validate_api_key
from ..utils.exceptions import (
    AuthenticationError,
    CatalogNotFoundError,
    GelatoAPIError,
    NetworkError,
    OrderNotFoundError,
    RateLimitError,
    ServerError,
    ValidationError as GelatoValidationError,
)
from ..utils.logging import get_logger


class GelatoClient:
    """Client for interacting with Gelato APIs."""
    
    def __init__(self, api_key: str, settings: Settings):
        """
        Initialize the Gelato API client.
        
        Args:
            api_key: Gelato API key
            settings: Application settings
        """
        validate_api_key(api_key)
        self.api_key = api_key
        self.settings = settings
        self.headers = get_auth_headers(api_key)
        self.logger = get_logger("client")
        
        # Create HTTP client with timeout and retry settings
        self.session = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(self.settings.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client session."""
        if hasattr(self, 'session') and self.session:
            await self.session.aclose()
    
    async def _request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments
            
        Returns:
            HTTP response
            
        Raises:
            GelatoAPIError: For various API errors
        """
        retries = 0
        last_exception = None
        
        while retries <= self.settings.max_retries:
            try:
                response = await self.session.request(method, url, **kwargs)
                
                # Handle HTTP status codes
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise GelatoAPIError(f"Resource not found: {url}", status_code=404)
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif 400 <= response.status_code < 500:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except Exception:
                        pass
                    raise GelatoValidationError(
                        f"Client error: {response.status_code}",
                        status_code=response.status_code,
                        response_data=error_data
                    )
                elif response.status_code >= 500:
                    raise ServerError(
                        f"Server error: {response.status_code}",
                        status_code=response.status_code
                    )
                
            except httpx.TimeoutException as e:
                last_exception = NetworkError(f"Request timeout: {str(e)}")
            except httpx.NetworkError as e:
                last_exception = NetworkError(f"Network error: {str(e)}")
            except (AuthenticationError, RateLimitError, GelatoValidationError, ServerError):
                # Don't retry these errors
                raise
            except Exception as e:
                last_exception = GelatoAPIError(f"Unexpected error: {str(e)}")
            
            retries += 1
            if retries <= self.settings.max_retries:
                # Exponential backoff
                await asyncio.sleep(2 ** (retries - 1))
        
        # If we've exhausted retries, raise the last exception
        if last_exception:
            raise last_exception
        
        raise GelatoAPIError("Request failed after all retries")
    
    # Order API methods
    
    async def search_orders(self, params: SearchOrdersParams) -> SearchOrdersResponse:
        """
        Search for orders using various filters.
        
        Args:
            params: Search parameters
            
        Returns:
            Search results
            
        Raises:
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_base_url}/v4/orders:search"
        
        # Convert params to dict, excluding None values
        request_data = params.model_dump(exclude_none=True)
        
        try:
            self.logger.debug(f"Making request to: {url}")
            self.logger.debug(f"Request data: {request_data}")
            response = await self._request("POST", url, json=request_data)
            raw_data = response.text
            self.logger.debug(f"Raw response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats
                if "orders" in data:
                    # Direct format: {"orders": [...]}
                    return SearchOrdersResponse(**data)
                elif "data" in data:
                    # Wrapped format: {"data": [...], "pagination": {...}}
                    return SearchOrdersResponse(orders=data["data"])
                else:
                    self.logger.error(f"Unexpected dict response format, keys: {list(data.keys())}")
                    raise GelatoValidationError(f"Unexpected response format: dict with keys {list(data.keys())}")
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in search_orders: {str(e)}")
            raise GelatoAPIError(f"Failed to search orders: {str(e)}")
    
    async def get_order(self, order_id: str) -> OrderDetail:
        """
        Get detailed information about a specific order.
        
        Args:
            order_id: Gelato order ID
            
        Returns:
            Detailed order information
            
        Raises:
            OrderNotFoundError: If the order is not found
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_base_url}/v4/orders/{order_id}"
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = await self._request("GET", url)
            raw_data = response.text
            self.logger.debug(f"Raw response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}, "pagination": {...}}
                    return OrderDetail(**data["data"])
                else:
                    # Direct format: assume the dict is the order data
                    return OrderDetail(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError as e:
            if e.status_code == 404:
                raise OrderNotFoundError(order_id)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_order: {str(e)}")
            raise GelatoAPIError(f"Failed to get order {order_id}: {str(e)}")
    
    async def create_order(self, request: CreateOrderRequest) -> OrderDetail:
        """
        Create a new order.
        
        Args:
            request: Order creation request with all required details
            
        Returns:
            Detailed order information for the created order
            
        Raises:
            GelatoValidationError: If the request data is invalid
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_base_url}/v4/orders"
        
        try:
            # Convert request to dict and exclude None values for cleaner request
            payload = request.model_dump(exclude_none=True)
            
            self.logger.debug(f"Creating order with payload: {json.dumps(payload, indent=2, default=str)}")
            
            response = await self._request("POST", url, json=payload)
            raw_data = response.text
            self.logger.debug(f"Raw create order response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}, "pagination": {...}}
                    return OrderDetail(**data["data"])
                else:
                    # Direct format: assume the dict is the order data
                    return OrderDetail(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError:
            # Re-raise API errors without modification
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in create_order: {str(e)}")
            raise GelatoAPIError(f"Failed to create order: {str(e)}")
    
    # Product API methods
    
    async def list_catalogs(self) -> List[Catalog]:
        """
        Get list of available product catalogs.
        
        Returns:
            List of available catalogs
            
        Raises:
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_product_url}/v3/catalogs"
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = await self._request("GET", url)
            raw_data = response.text
            self.logger.debug(f"Raw response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, list):
                self.logger.debug(f"Response is a list with {len(data)} items")
                if data:
                    self.logger.debug(f"First item type: {type(data[0])}, value: {data[0]}")
                
                catalogs = []
                for i, catalog_data in enumerate(data):
                    try:
                        if isinstance(catalog_data, dict):
                            # Standard case: catalog_data is a dictionary
                            catalog = Catalog(**catalog_data)
                        elif isinstance(catalog_data, str):
                            # Handle case where API returns strings instead of objects
                            # Assume the string is the catalogUid and create a basic catalog
                            catalog = Catalog(catalogUid=catalog_data, title=catalog_data.title())
                        else:
                            self.logger.warning(f"Unexpected catalog data type at index {i}: {type(catalog_data)}")
                            continue
                        
                        catalogs.append(catalog)
                    except Exception as e:
                        self.logger.error(f"Failed to parse catalog at index {i}: {catalog_data}, error: {e}")
                        continue
                
                return catalogs
            elif isinstance(data, dict):
                # Handle wrapped response formats
                if "catalogs" in data:
                    # Format: {"catalogs": [...], "total": N}
                    return await self._parse_catalog_list(data["catalogs"])
                elif "data" in data:
                    # Format: {"data": [...], "pagination": {...}}
                    return await self._parse_catalog_list(data["data"])
                else:
                    self.logger.error(f"Unexpected dict response format, keys: {list(data.keys())}")
                    raise GelatoValidationError(f"Unexpected response format: dict with keys {list(data.keys())}")
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Unexpected response type: {type(data)}")
                
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in list_catalogs: {str(e)}")
            raise GelatoAPIError(f"Failed to list catalogs: {str(e)}")
    
    async def _parse_catalog_list(self, catalog_list: List) -> List[Catalog]:
        """Helper method to parse a list of catalog data."""
        catalogs = []
        for i, catalog_data in enumerate(catalog_list):
            try:
                if isinstance(catalog_data, dict):
                    catalog = Catalog(**catalog_data)
                elif isinstance(catalog_data, str):
                    catalog = Catalog(catalogUid=catalog_data, title=catalog_data.title())
                else:
                    self.logger.warning(f"Skipping unexpected catalog data type at index {i}: {type(catalog_data)}")
                    continue
                catalogs.append(catalog)
            except Exception as e:
                self.logger.error(f"Failed to parse catalog at index {i}: {catalog_data}, error: {e}")
                continue
        return catalogs
    
    async def get_catalog(self, catalog_uid: str) -> CatalogDetail:
        """
        Get detailed information about a specific catalog.
        
        Args:
            catalog_uid: Catalog unique identifier
            
        Returns:
            Detailed catalog information
            
        Raises:
            CatalogNotFoundError: If the catalog is not found
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_product_url}/v3/catalogs/{catalog_uid}"
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = await self._request("GET", url)
            raw_data = response.text
            self.logger.debug(f"Raw response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}, "pagination": {...}}
                    return CatalogDetail(**data["data"])
                else:
                    # Direct format: assume the dict is the catalog data
                    return CatalogDetail(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError as e:
            if e.status_code == 404:
                raise CatalogNotFoundError(catalog_uid)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_catalog: {str(e)}")
            raise GelatoAPIError(f"Failed to get catalog {catalog_uid}: {str(e)}")
    
    async def search_products(self, catalog_uid: str, request: SearchProductsRequest) -> SearchProductsResponse:
        """
        Search products in a specific catalog with filters.
        
        Args:
            catalog_uid: Catalog unique identifier
            request: Search request with filters and pagination
            
        Returns:
            Search results containing products and filter hits
            
        Raises:
            CatalogNotFoundError: If the catalog is not found
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_product_url}/v3/catalogs/{catalog_uid}/products:search"
        
        try:
            # Convert request to dict and exclude None values for cleaner request
            payload = request.model_dump(exclude_none=True)
            
            self.logger.debug(f"Searching products in catalog {catalog_uid} with payload: {json.dumps(payload, indent=2, default=str)}")
            
            response = await self._request("POST", url, json=payload)
            raw_data = response.text
            self.logger.debug(f"Raw search products response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}, "pagination": {...}}
                    return SearchProductsResponse(**data["data"])
                else:
                    # Direct format: assume the dict is the response data
                    return SearchProductsResponse(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError as e:
            if e.status_code == 404:
                raise CatalogNotFoundError(catalog_uid)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in search_products: {str(e)}")
            raise GelatoAPIError(f"Failed to search products in catalog {catalog_uid}: {str(e)}")
    
    async def get_product(self, product_uid: str) -> "ProductDetail":
        """
        Get detailed information about a single product.
        
        Args:
            product_uid: Product unique identifier
            
        Returns:
            Detailed product information
            
        Raises:
            ProductNotFoundError: If the product is not found
            GelatoAPIError: If the API request fails
        """
        from ..models.products import ProductDetail
        from ..utils.exceptions import ProductNotFoundError
        
        url = f"{self.settings.gelato_product_url}/v3/products/{product_uid}"
        
        try:
            self.logger.debug(f"Getting product: {product_uid}")
            response = await self._request("GET", url)
            
            raw_data = response.text
            self.logger.debug(f"Raw get product response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats  
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}}
                    return ProductDetail(**data["data"])
                else:
                    # Direct format: assume the dict is the product data
                    return ProductDetail(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError as e:
            if e.status_code == 404:
                raise ProductNotFoundError(product_uid)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_product: {str(e)}")
            raise GelatoAPIError(f"Failed to get product {product_uid}: {str(e)}")

    async def get_product_prices(
        self,
        product_uid: str,
        country: Optional[str] = None,
        currency: Optional[str] = None,
        page_count: Optional[int] = None
    ) -> List[ProductPrice]:
        """
        Get price information for all quantities of a product.

        Args:
            product_uid: Product unique identifier
            country: Optional country ISO code (e.g., "US", "GB", "DE")
            currency: Optional currency ISO code (e.g., "USD", "GBP", "EUR")
            page_count: Optional page count (mandatory for multi-page products)

        Returns:
            List of ProductPrice objects with quantity-based pricing

        Raises:
            ProductNotFoundError: If the product is not found
            GelatoAPIError: If the API request fails
        """
        from ..utils.exceptions import ProductNotFoundError

        url = f"{self.settings.gelato_product_url}/v3/products/{product_uid}/prices"

        # Build query parameters
        params = {}
        if country:
            params["country"] = country
        if currency:
            params["currency"] = currency
        if page_count is not None:
            params["pageCount"] = page_count

        try:
            self.logger.debug(f"Getting product prices for {product_uid} with params: {params}")
            response = await self._request("GET", url, params=params if params else None)

            raw_data = response.text
            self.logger.debug(f"Raw product prices response (first 200 chars): {raw_data[:200]}")

            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")

            if isinstance(data, list):
                # Direct array format: [{"productUid": ..., "price": ...}, ...]
                return [ProductPrice(**price_data) for price_data in data]
            elif isinstance(data, dict):
                # Handle wrapped response formats
                if "data" in data and isinstance(data["data"], list):
                    # Wrapped format: {"data": [...]}
                    return [ProductPrice(**price_data) for price_data in data["data"]]
                elif "prices" in data and isinstance(data["prices"], list):
                    # Alternative format: {"prices": [...]}
                    return [ProductPrice(**price_data) for price_data in data["prices"]]
                else:
                    self.logger.error(f"Unexpected dict response format, keys: {list(data.keys())}")
                    raise GelatoValidationError(f"Unexpected response format: dict with keys {list(data.keys())}")
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected list or dict, got {type(data)}")

        except GelatoAPIError as e:
            if e.status_code == 404:
                raise ProductNotFoundError(product_uid)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_product_prices: {str(e)}")
            raise GelatoAPIError(f"Failed to get product prices for {product_uid}: {str(e)}")

    async def check_stock_availability(self, products: List[str]) -> "StockAvailabilityResponse":
        """
        Check stock availability for multiple products across regions.

        Args:
            products: List of product UIDs to check (1-250 products)

        Returns:
            Stock availability response containing availability for each product in each region

        Raises:
            GelatoAPIError: If the API request fails or validation errors occur
        """
        from ..models.products import StockAvailabilityRequest, StockAvailabilityResponse

        # Validate input constraints
        if not products:
            raise GelatoAPIError("At least one product UID is required", status_code=400)

        if len(products) > 250:
            raise GelatoAPIError(f"Maximum 250 products allowed, got {len(products)}", status_code=400)

        url = f"{self.settings.gelato_product_url}/v3/stock/region-availability"

        try:
            # Build request payload
            request = StockAvailabilityRequest(products=products)
            payload = request.model_dump()

            self.logger.debug(f"Checking stock availability for {len(products)} products")
            response = await self._request("POST", url, json=payload)

            raw_data = response.text
            self.logger.debug(f"Raw stock availability response (first 200 chars): {raw_data[:200]}")

            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")

            if isinstance(data, dict):
                # Handle different response formats
                if "productsAvailability" in data:
                    # Direct format: {"productsAvailability": [...]}
                    return StockAvailabilityResponse(**data)
                elif "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {"productsAvailability": [...]}}
                    return StockAvailabilityResponse(**data["data"])
                else:
                    self.logger.error(f"Unexpected dict response format, keys: {list(data.keys())}")
                    raise GelatoValidationError(f"Unexpected response format: dict with keys {list(data.keys())}")
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")

        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in check_stock_availability: {str(e)}")
            raise GelatoAPIError(f"Failed to check stock availability: {str(e)}")

    # Template API methods
    
    async def get_template(self, template_id: str) -> "Template":
        """
        Get detailed information about a template.
        
        Args:
            template_id: Template unique identifier
            
        Returns:
            Detailed template information
            
        Raises:
            TemplateNotFoundError: If the template is not found
            GelatoAPIError: If the API request fails
        """
        from ..models.templates import Template
        from ..utils.exceptions import TemplateNotFoundError
        
        url = f"{self.settings.gelato_ecommerce_url}/v1/templates/{template_id}"
        
        try:
            self.logger.debug(f"Getting template: {template_id}")
            response = await self._request("GET", url)
            
            raw_data = response.text
            self.logger.debug(f"Raw get template response (first 200 chars): {raw_data[:200]}")
            
            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")
            
            if isinstance(data, dict):
                # Handle different response formats  
                if "data" in data and isinstance(data["data"], dict):
                    # Wrapped format: {"data": {...}}
                    return Template(**data["data"])
                else:
                    # Direct format: assume the dict is the template data
                    return Template(**data)
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")
                
        except GelatoAPIError as e:
            if e.status_code == 404:
                raise TemplateNotFoundError(template_id)
            raise
        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_template: {str(e)}")
            raise GelatoAPIError(f"Failed to get template {template_id}: {str(e)}")

    # Shipment API methods

    async def list_shipment_methods(self, country: Optional[str] = None) -> ShipmentMethodsResponse:
        """
        Get available shipment methods, optionally filtered by destination country.

        Args:
            country: Optional destination country ISO code (e.g., "US", "GB", "DE")
                    If provided, only shipment methods available for this country are returned

        Returns:
            Response containing list of available shipment methods

        Raises:
            GelatoAPIError: If the API request fails
        """
        url = f"{self.settings.gelato_shipment_url}/v1/shipment-methods"

        # Add country query parameter if provided
        params = {}
        if country:
            params["country"] = country

        try:
            self.logger.debug(f"Getting shipment methods with params: {params}")
            response = await self._request("GET", url, params=params if params else None)

            raw_data = response.text
            self.logger.debug(f"Raw shipment methods response (first 200 chars): {raw_data[:200]}")

            data = response.json()
            self.logger.debug(f"Parsed JSON type: {type(data)}")

            if isinstance(data, dict):
                # Handle different response formats
                if "shipmentMethods" in data:
                    # Direct format: {"shipmentMethods": [...]}
                    return ShipmentMethodsResponse(**data)
                elif "data" in data:
                    # Wrapped format: {"data": [...], "pagination": {...}}
                    if isinstance(data["data"], dict) and "shipmentMethods" in data["data"]:
                        return ShipmentMethodsResponse(**data["data"])
                    else:
                        # Assume data contains the shipmentMethods directly
                        return ShipmentMethodsResponse(shipmentMethods=data["data"])
                else:
                    self.logger.error(f"Unexpected dict response format, keys: {list(data.keys())}")
                    raise GelatoValidationError(f"Unexpected response format: dict with keys {list(data.keys())}")
            else:
                self.logger.error(f"Unexpected response type: {type(data)}")
                raise GelatoValidationError(f"Expected dict, got {type(data)}")

        except ValidationError as e:
            self.logger.error(f"Pydantic validation error: {str(e)}")
            raise GelatoValidationError(f"Invalid response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in list_shipment_methods: {str(e)}")
            raise GelatoAPIError(f"Failed to list shipment methods: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test the connection to Gelato API.
        
        Returns:
            True if connection is successful
            
        Raises:
            GelatoAPIError: If the connection test fails
        """
        try:
            await self.list_catalogs()
            return True
        except Exception as e:
            raise GelatoAPIError(f"Connection test failed: {str(e)}")