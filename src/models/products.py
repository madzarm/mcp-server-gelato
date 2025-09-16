"""Pydantic models for Gelato product-related API responses."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Catalog(BaseModel):
    """Basic catalog information."""
    
    catalogUid: str = Field(..., description="Catalog unique identifier")
    title: str = Field(..., description="Catalog title")


class ProductAttributeValue(BaseModel):
    """Product attribute value information."""
    
    productAttributeValueUid: str = Field(..., description="Attribute value unique identifier")
    title: str = Field(..., description="Attribute value title")


class ProductAttribute(BaseModel):
    """Product attribute information."""

    productAttributeUid: str = Field(..., description="Attribute unique identifier")
    title: str = Field(..., description="Attribute title")
    values: Any = Field(..., description="Possible attribute values (flexible format)")


class CatalogDetail(Catalog):
    """Detailed catalog information with attributes."""
    
    productAttributes: List[ProductAttribute] = Field(
        ..., 
        description="Array of product attributes and their possible values"
    )


# Search products models

class AttributeFilters(BaseModel):
    """Associative array of attribute filters for product search."""
    
    class Config:
        extra = "allow"  # Allow additional fields for dynamic attribute names


class SearchProductsRequest(BaseModel):
    """Request model for searching products in a catalog."""
    
    attributeFilters: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Associative array of attribute-based filters"
    )
    limit: Optional[int] = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of products to return (max 100)"
    )
    offset: Optional[int] = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )


class MeasureUnit(BaseModel):
    """Measurement unit with value and unit."""
    
    value: float = Field(..., description="Value in given units of measurement")
    measureUnit: str = Field(..., description="Name of the unit of measurement (grams, mm, etc)")


class ProductAttributes(BaseModel):
    """Associative array of product attributes."""
    
    class Config:
        extra = "allow"  # Allow additional fields for dynamic attribute names


class Product(BaseModel):
    """Product information from search results."""
    
    productUid: str = Field(..., description="Product unique identifier")
    attributes: Dict[str, str] = Field(..., description="Associative array of product attributes")
    weight: Any = Field(..., description="Weight of the product")
    dimensions: Any = Field(..., description="Product dimensions (Width, Height, Thickness, etc.)")
    supportedCountries: Optional[List[str]] = Field(
        None,
        description="Array of supported country codes (ISO 3166-1)"
    )


class AttributeHits(BaseModel):
    """Attribute hits showing count of products for each attribute value."""
    
    class Config:
        extra = "allow"  # Allow dynamic attribute names as keys


class FilterHits(BaseModel):
    """Filter hits containing attribute hits."""
    
    attributeHits: Dict[str, Dict[str, int]] = Field(
        ...,
        description="Associative array of attributes with hit counts for each value"
    )


class SearchProductsResponse(BaseModel):
    """Response model for product search results."""
    
    products: List[Product] = Field(..., description="List of matching products")
    hits: FilterHits = Field(..., description="Attribute hits for filtering")


class ProductDetail(BaseModel):
    """Detailed product information from single product endpoint."""
    
    productUid: str = Field(..., description="Product unique identifier")
    attributes: Dict[str, str] = Field(..., description="Associative array of product attributes")
    weight: Any = Field(..., description="Weight of the product")
    supportedCountries: List[str] = Field(..., description="Array of supported country codes (ISO 3166-1)")
    notSupportedCountries: List[str] = Field(..., description="Array of countries that are not supported")
    isStockable: bool = Field(..., description="Whether the product is a stockable item")
    isPrintable: bool = Field(..., description="Whether the product is a printable item")
    validPageCounts: Optional[List[int]] = Field(None, description="Supported page counts for multi-page products")
    dimensions: Optional[Any] = Field(None, description="Product dimensions (flexible structure)")


# Product pricing models

class ProductPrice(BaseModel):
    """Product price information for a specific quantity."""

    productUid: str = Field(..., description="Product unique identifier")
    country: str = Field(..., description="Country ISO code")
    quantity: int = Field(..., description="Quantity of the product")
    price: float = Field(..., description="Price of the product")
    currency: str = Field(..., description="Currency ISO code")
    pageCount: Optional[int] = Field(None, description="Page count for multi-page products")


# Stock availability models

class StockAvailabilityRequest(BaseModel):
    """Request model for checking stock availability."""

    products: List[str] = Field(..., description="Array of product UIDs (1-250 products)")

    def model_validate(cls, values):
        """Validate products list constraints."""
        if "products" in values:
            products = values["products"]
            if not products:
                raise ValueError("At least one product UID is required")
            if len(products) > 250:
                raise ValueError(f"Maximum 250 products allowed, got {len(products)}")
        return values


class RegionAvailability(BaseModel):
    """Stock availability information for a specific region."""

    stockRegionUid: str = Field(..., description="Stock region UID (US-CA, EU, UK, AS, OC, SA, ROW)")
    status: str = Field(..., description="Availability status")
    replenishmentDate: Optional[str] = Field(None, description="Estimated replenishment date (YYYY-MM-DD)")


class ProductAvailability(BaseModel):
    """Product availability across all regions."""

    productUid: str = Field(..., description="Product UID from the request")
    availability: List[RegionAvailability] = Field(..., description="Availability in each region")


class StockAvailabilityResponse(BaseModel):
    """Response model for stock availability check."""

    productsAvailability: List[ProductAvailability] = Field(..., description="Array of product availability in regions")