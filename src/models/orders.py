"""Pydantic models for Gelato order-related API responses."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .common import (
    BillingEntity,
    File,
    Preview,
    Receipt,
    ReturnAddress,
    Shipment,
    ShippingAddress,
)


class ItemOption(BaseModel):
    """Item option (e.g., envelope)."""
    
    id: str = Field(..., description="Option ID")
    type: str = Field(..., description="Option type")
    productUid: str = Field(..., description="Product UID for this option")
    quantity: int = Field(..., description="Option quantity")


class OrderItem(BaseModel):
    """Order item information."""
    
    id: str = Field(..., description="Item ID")
    itemReferenceId: str = Field(..., description="Your internal item reference ID")
    productUid: str = Field(..., description="Product UID")
    files: List[File] = Field(..., description="List of files for printing")
    processedFileUrl: Optional[str] = Field(None, description="Processed file URL")
    quantity: int = Field(..., description="Item quantity")
    fulfillmentStatus: str = Field(..., description="Item fulfillment status")
    previews: List[Preview] = Field(default_factory=list, description="Item previews")
    options: Optional[List[ItemOption]] = Field(default_factory=list, description="Item options")
    pageCount: Optional[int] = Field(None, description="Page count for multipage products")


class OrderSummary(BaseModel):
    """Order summary from search results."""
    
    id: str = Field(..., description="Gelato order ID")
    orderType: Literal["order", "draft"] = Field(..., description="Order type")
    orderReferenceId: str = Field(..., description="Your internal order reference ID")
    customerReferenceId: str = Field(..., description="Your internal customer reference ID")
    fulfillmentStatus: str = Field(..., description="Current fulfillment status")
    financialStatus: str = Field(..., description="Current financial status")
    currency: Optional[str] = Field(None, description="Order currency")
    channel: Optional[str] = Field(None, description="Order channel")
    country: Optional[str] = Field(None, description="Country code")
    firstName: Optional[str] = Field(None, description="Recipient first name")
    lastName: Optional[str] = Field(None, description="Recipient last name")
    itemsCount: Optional[int] = Field(None, description="Number of items in order")
    totalInclVat: Optional[str] = Field(None, description="Total including VAT")
    storeId: Optional[str] = Field(None, description="E-commerce store ID")
    connectedOrderIds: List[str] = Field(default_factory=list, description="Connected order IDs")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    orderedAt: Optional[datetime] = Field(None, description="Order placement timestamp")


class OrderDetail(OrderSummary):
    """Detailed order information."""
    
    items: List[OrderItem] = Field(..., description="Order items")
    shippingAddress: Optional[ShippingAddress] = Field(None, description="Shipping address")
    billingEntity: Optional[BillingEntity] = Field(None, description="Billing entity")
    returnAddress: Optional[ReturnAddress] = Field(None, description="Return address")
    shipment: Optional[Shipment] = Field(None, description="Shipment information")
    receipts: List[Receipt] = Field(default_factory=list, description="Order receipts")


class SearchOrdersParams(BaseModel):
    """Parameters for searching orders."""
    
    channels: Optional[List[str]] = Field(None, description="List of order channels")
    countries: Optional[List[str]] = Field(None, description="List of countries")
    currencies: Optional[List[str]] = Field(None, description="List of currencies")
    endDate: Optional[datetime] = Field(None, description="End date for search")
    financialStatuses: Optional[List[str]] = Field(None, description="Financial statuses")
    fulfillmentStatuses: Optional[List[str]] = Field(None, description="Fulfillment statuses")
    ids: Optional[List[str]] = Field(None, description="List of Gelato order IDs")
    limit: Optional[int] = Field(50, description="Maximum results per page", le=100)
    offset: Optional[int] = Field(0, description="Offset for pagination", ge=0)
    orderReferenceId: Optional[str] = Field(None, description="Your internal order reference ID")
    orderReferenceIds: Optional[List[str]] = Field(None, description="List of your order reference IDs")
    orderTypes: Optional[List[Literal["order", "draft"]]] = Field(None, description="Order types")
    search: Optional[str] = Field(None, description="Search string")
    startDate: Optional[datetime] = Field(None, description="Start date for search")
    storeIds: Optional[List[str]] = Field(None, description="List of store IDs")


class SearchOrdersResponse(BaseModel):
    """Response from order search API."""
    
    orders: List[OrderSummary] = Field(..., description="List of orders matching search criteria")