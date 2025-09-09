"""Pydantic models for Gelato product-related API responses."""

from typing import List

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
    values: List[ProductAttributeValue] = Field(..., description="List of possible attribute values")


class CatalogDetail(Catalog):
    """Detailed catalog information with attributes."""
    
    productAttributes: List[ProductAttribute] = Field(
        ..., 
        description="Array of product attributes and their possible values"
    )