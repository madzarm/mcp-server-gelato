"""Unit tests for Pydantic models."""

from datetime import datetime
from typing import List

import pytest
from pydantic import ValidationError

from src.models.common import Address, ShippingAddress, File
from src.models.orders import OrderDetail, OrderSummary, SearchOrdersParams, SearchOrdersResponse
from src.models.products import Catalog, CatalogDetail, ProductAttribute, ProductAttributeValue


class TestCommonModels:
    """Test cases for common models."""
    
    def test_address_creation(self):
        """Test Address model creation."""
        address_data = {
            "addressLine1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postCode": "10001",
            "country": "US",
            "email": "john@example.com"
        }
        
        address = Address(**address_data)
        
        assert address.addressLine1 == "123 Main St"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postCode == "10001"
        assert address.country == "US"
        assert address.email == "john@example.com"
    
    def test_address_with_optional_fields(self):
        """Test Address model with optional fields."""
        address_data = {
            "addressLine1": "456 Oak Ave",
            "addressLine2": "Suite 100",
            "city": "Los Angeles",
            "state": "CA",
            "postCode": "90210",
            "country": "US",
            "email": "jane@acme.com",
            "phone": "+1-555-123-4567"
        }
        
        address = Address(**address_data)
        
        assert address.addressLine2 == "Suite 100"
        assert address.phone == "+1-555-123-4567"
    
    def test_address_missing_required_fields(self):
        """Test Address model with missing required fields."""
        address_data = {
            "addressLine1": "123 Main St",
            # Missing country, city, postCode, email
        }
        
        with pytest.raises(ValidationError):
            Address(**address_data)
    
    def test_file_creation(self):
        """Test File model creation."""
        file_data = {
            "type": "front",
            "url": "https://example.com/file.png"
        }
        
        print_file = File(**file_data)
        
        assert print_file.type == "front"
        assert print_file.url == "https://example.com/file.png"
    
    def test_file_default_type(self):
        """Test File model with default type."""
        file_data = {
            "url": "https://example.com/file.pdf"
        }
        
        print_file = File(**file_data)
        
        assert print_file.type == "default"
        assert print_file.url == "https://example.com/file.pdf"
    
    def test_shipping_address_creation(self):
        """Test ShippingAddress model creation."""
        address_data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "addressLine1": "123 Main St",
            "city": "New York", 
            "postCode": "10001",
            "country": "US",
            "email": "jane@example.com"
        }
        
        address = ShippingAddress(**address_data)
        
        assert address.firstName == "Jane"
        assert address.lastName == "Smith"
        assert address.addressLine1 == "123 Main St"
        assert address.city == "New York"


class TestProductModels:
    """Test cases for product models."""
    
    def test_catalog_creation(self):
        """Test Catalog model creation."""
        catalog_data = {
            "catalogUid": "cards",
            "title": "Greeting Cards"
        }
        
        catalog = Catalog(**catalog_data)
        
        assert catalog.catalogUid == "cards"
        assert catalog.title == "Greeting Cards"
    
    def test_catalog_missing_fields(self):
        """Test Catalog model with missing required fields."""
        with pytest.raises(ValidationError):
            Catalog(catalogUid="cards")  # Missing title
        
        with pytest.raises(ValidationError):
            Catalog(title="Cards")  # Missing catalogUid
    
    def test_product_attribute_value_creation(self):
        """Test ProductAttributeValue model creation."""
        value_data = {
            "productAttributeValueUid": "a5",
            "title": "A5 Size"
        }
        
        value = ProductAttributeValue(**value_data)
        
        assert value.productAttributeValueUid == "a5"
        assert value.title == "A5 Size"
    
    def test_product_attribute_creation(self):
        """Test ProductAttribute model creation."""
        attribute_data = {
            "productAttributeUid": "size",
            "title": "Size Options",
            "values": [
                {"productAttributeValueUid": "a4", "title": "A4"},
                {"productAttributeValueUid": "a5", "title": "A5"}
            ]
        }
        
        attribute = ProductAttribute(**attribute_data)
        
        assert attribute.productAttributeUid == "size"
        assert attribute.title == "Size Options"
        assert len(attribute.values) == 2
        assert attribute.values[0].productAttributeValueUid == "a4"
        assert attribute.values[1].productAttributeValueUid == "a5"
    
    def test_catalog_detail_creation(self):
        """Test CatalogDetail model creation."""
        catalog_data = {
            "catalogUid": "posters",
            "title": "Posters",
            "productAttributes": [
                {
                    "productAttributeUid": "size",
                    "title": "Size",
                    "values": [
                        {"productAttributeValueUid": "a3", "title": "A3"},
                        {"productAttributeValueUid": "a2", "title": "A2"}
                    ]
                },
                {
                    "productAttributeUid": "material",
                    "title": "Material",
                    "values": [
                        {"productAttributeValueUid": "matte", "title": "Matte"},
                        {"productAttributeValueUid": "glossy", "title": "Glossy"}
                    ]
                }
            ]
        }
        
        catalog = CatalogDetail(**catalog_data)
        
        assert catalog.catalogUid == "posters"
        assert catalog.title == "Posters"
        assert len(catalog.productAttributes) == 2
        assert catalog.productAttributes[0].productAttributeUid == "size"
        assert catalog.productAttributes[1].productAttributeUid == "material"
        assert len(catalog.productAttributes[0].values) == 2
    
    def test_catalog_detail_inheritance(self):
        """Test that CatalogDetail inherits from Catalog."""
        catalog_data = {
            "catalogUid": "test",
            "title": "Test Catalog",
            "productAttributes": []
        }
        
        catalog_detail = CatalogDetail(**catalog_data)
        
        assert isinstance(catalog_detail, Catalog)
        assert isinstance(catalog_detail, CatalogDetail)


class TestOrderModels:
    """Test cases for order models."""
    
    def test_order_summary_creation(self):
        """Test OrderSummary model creation."""
        order_data = {
            "id": "order-123",
            "orderType": "order",
            "orderReferenceId": "ref-123",
            "customerReferenceId": "cust-123",
            "fulfillmentStatus": "shipped",
            "financialStatus": "paid",
            "currency": "USD",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T12:00:00Z"
        }
        
        order = OrderSummary(**order_data)
        
        assert order.id == "order-123"
        assert order.orderType == "order"
        assert order.orderReferenceId == "ref-123"
        assert order.customerReferenceId == "cust-123"
        assert order.fulfillmentStatus == "shipped"
        assert order.financialStatus == "paid"
        assert order.currency == "USD"
        assert isinstance(order.createdAt, datetime)
        assert isinstance(order.updatedAt, datetime)
    
    def test_order_detail_creation(self):
        """Test OrderDetail model creation."""
        order_data = {
            "id": "order-456",
            "orderType": "order",
            "orderReferenceId": "ref-456",
            "customerReferenceId": "cust-456",
            "fulfillmentStatus": "printed",
            "financialStatus": "paid",
            "currency": "EUR",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T12:00:00Z",
            "items": [
                {
                    "itemReferenceId": "item-1",
                    "productUid": "test-product",
                    "quantity": 1,
                    "files": [{"url": "https://example.com/test.png"}]
                }
            ]
        }
        
        order = OrderDetail(**order_data)
        
        assert order.id == "order-456"
        assert order.currency == "EUR"
        assert len(order.items) == 1
        assert order.items[0].itemReferenceId == "item-1"
        assert isinstance(order, OrderSummary)  # Should inherit from OrderSummary
    
    def test_search_orders_params_creation(self):
        """Test SearchOrdersParams model creation."""
        params_data = {
            "limit": 25,
            "offset": 10,
            "order_types": ["order", "draft"],
            "countries": ["US", "CA"],
            "currencies": ["USD", "CAD"],
            "search_text": "John Doe"
        }
        
        params = SearchOrdersParams(**params_data)
        
        assert params.limit == 25
        assert params.offset == 10
        assert params.order_types == ["order", "draft"]
        assert params.countries == ["US", "CA"]
        assert params.currencies == ["USD", "CAD"]
        assert params.search_text == "John Doe"
    
    def test_search_orders_params_defaults(self):
        """Test SearchOrdersParams model with default values."""
        params = SearchOrdersParams()
        
        assert params.limit == 50
        assert params.offset == 0
        assert params.order_types is None
        assert params.countries is None
        assert params.currencies is None
    
    def test_search_orders_params_validation(self):
        """Test SearchOrdersParams model validation."""
        # Test limit validation
        with pytest.raises(ValidationError):
            SearchOrdersParams(limit=0)  # Should be > 0
        
        with pytest.raises(ValidationError):
            SearchOrdersParams(limit=101)  # Should be <= 100
        
        # Test offset validation
        with pytest.raises(ValidationError):
            SearchOrdersParams(offset=-1)  # Should be >= 0
    
    def test_search_orders_response_creation(self):
        """Test SearchOrdersResponse model creation."""
        response_data = {
            "orders": [
                {
                    "id": "order-1",
                    "orderType": "order",
                    "orderReferenceId": "ref-1",
                    "customerReferenceId": "cust-1",
                    "fulfillmentStatus": "created",
                    "financialStatus": "paid",
                    "currency": "USD",
                    "createdAt": "2024-01-01T10:00:00Z",
                    "updatedAt": "2024-01-01T10:00:00Z"
                },
                {
                    "id": "order-2",
                    "orderType": "draft",
                    "orderReferenceId": "ref-2",
                    "customerReferenceId": "cust-2",
                    "fulfillmentStatus": "draft",
                    "financialStatus": "draft",
                    "currency": "EUR",
                    "createdAt": "2024-01-01T11:00:00Z",
                    "updatedAt": "2024-01-01T11:00:00Z"
                }
            ]
        }
        
        response = SearchOrdersResponse(**response_data)
        
        assert len(response.orders) == 2
        assert response.orders[0].id == "order-1"
        assert response.orders[1].id == "order-2"
        assert all(isinstance(order, OrderSummary) for order in response.orders)
    
    def test_search_orders_response_empty(self):
        """Test SearchOrdersResponse model with empty orders."""
        response_data = {"orders": []}
        
        response = SearchOrdersResponse(**response_data)
        
        assert len(response.orders) == 0
        assert isinstance(response.orders, list)


class TestModelSerialization:
    """Test cases for model serialization and deserialization."""
    
    def test_catalog_serialization(self):
        """Test Catalog model serialization."""
        catalog = Catalog(catalogUid="test", title="Test Catalog")
        
        # Test model_dump
        data = catalog.model_dump()
        expected_data = {"catalogUid": "test", "title": "Test Catalog"}
        assert data == expected_data
        
        # Test round-trip
        catalog_restored = Catalog(**data)
        assert catalog_restored.catalogUid == catalog.catalogUid
        assert catalog_restored.title == catalog.title
    
    def test_order_summary_serialization(self):
        """Test OrderSummary model serialization."""
        created_at = datetime(2024, 1, 1, 10, 0, 0)
        updated_at = datetime(2024, 1, 1, 12, 0, 0)
        
        order = OrderSummary(
            id="order-123",
            orderType="order",
            orderReferenceId="ref-123",
            customerReferenceId="cust-123",
            fulfillmentStatus="shipped",
            financialStatus="paid",
            currency="USD",
            createdAt=created_at,
            updatedAt=updated_at
        )
        
        # Test model_dump
        data = order.model_dump()
        assert data["id"] == "order-123"
        assert data["createdAt"] == created_at
        assert data["updatedAt"] == updated_at
        
        # Test round-trip
        order_restored = OrderSummary(**data)
        assert order_restored.id == order.id
        assert order_restored.createdAt == order.createdAt
    
    def test_model_dump_exclude_none(self):
        """Test model_dump with exclude_none option."""
        params = SearchOrdersParams(limit=25)  # Only set limit, others are None
        
        # Standard dump includes None values
        data_with_none = params.model_dump()
        assert "order_types" in data_with_none
        assert data_with_none["order_types"] is None
        
        # Dump excluding None values
        data_exclude_none = params.model_dump(exclude_none=True)
        assert "order_types" not in data_exclude_none
        assert data_exclude_none["limit"] == 25
        assert data_exclude_none["offset"] == 0  # 0 is not None, so included


class TestModelValidation:
    """Test cases for model validation edge cases."""
    
    def test_string_length_validation(self):
        """Test string length validation where applicable."""
        # Test empty strings
        with pytest.raises(ValidationError):
            Catalog(catalogUid="", title="Test")
        
        with pytest.raises(ValidationError):
            Catalog(catalogUid="test", title="")
    
    def test_datetime_parsing(self):
        """Test datetime parsing from various formats."""
        # ISO format string
        order = OrderSummary(
            id="test",
            orderType="order",
            orderReferenceId="ref",
            customerReferenceId="cust",
            fulfillmentStatus="created",
            financialStatus="paid",
            currency="USD",
            createdAt="2024-01-01T10:00:00Z",
            updatedAt="2024-01-01T12:00:00+00:00"
        )
        
        assert isinstance(order.createdAt, datetime)
        assert isinstance(order.updatedAt, datetime)
    
    def test_nested_model_validation(self):
        """Test validation of nested models."""
        # Invalid nested File
        with pytest.raises(ValidationError):
            File(type="front")  # Missing required 'url' field
        
        # Valid nested models
        file_obj = File(type="front", url="https://example.com/test.png")
        
        assert file_obj.type == "front"
        assert isinstance(file_obj, File)