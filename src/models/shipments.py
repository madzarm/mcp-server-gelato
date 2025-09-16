"""Shipment-related model definitions."""

from typing import Any, List

from pydantic import BaseModel, Field


class ShipmentMethod(BaseModel):
    """Shipment method information."""

    shipmentMethodUid: str = Field(..., description="Unique Shipment method identifier")
    type: str = Field(..., description="Shipping service type (normal, express, pallet)")
    name: str = Field(..., description="The name of the Shipment method")
    isBusiness: bool = Field(..., description="Suitable for shipping to business addresses")
    isPrivate: bool = Field(..., description="Suitable for shipping to residential addresses")
    hasTracking: bool = Field(..., description="Provides tracking code and URL")
    supportedCountries: List[str] = Field(..., description="List of destination country ISO codes")

    class Config:
        extra = "allow"  # Allow additional fields from the API


class ShipmentMethodsResponse(BaseModel):
    """Response containing list of shipment methods."""

    shipmentMethods: List[ShipmentMethod] = Field(..., description="Array of shipment method objects")

    class Config:
        extra = "allow"  # Allow additional fields from the API