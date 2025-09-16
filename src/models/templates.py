"""Pydantic models for Gelato template-related API responses."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Template(BaseModel):
    """Template information from e-commerce API."""
    
    id: str = Field(..., description="Template id")
    templateName: str = Field(..., description="Template name")
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    previewUrl: str = Field(..., description="Main product preview URL")
    variants: List[Any] = Field(..., description="Array of variants (flexible structure)")
    productType: Optional[str] = Field(None, description="Product type for the shop's products")
    vendor: Optional[str] = Field(None, description="Product vendor/provider")
    createdAt: str = Field(..., description="Date and time when template was created (ISO 8601)")
    updatedAt: str = Field(..., description="Date and time when template was updated (ISO 8601)")