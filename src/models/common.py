"""Common models used across different Gelato API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Base address model."""
    
    id: Optional[str] = None
    country: str = Field(..., description="Two-character ISO 3166-1 country code")
    addressLine1: str = Field(..., description="First line of the address")
    addressLine2: Optional[str] = Field(None, description="Second line of the address")
    city: str = Field(..., description="City name")
    postCode: str = Field(..., description="Postal code or zip code")
    state: Optional[str] = Field(None, description="State or province code")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number in E.123 format")


class ShippingAddress(Address):
    """Shipping address with recipient information."""
    
    firstName: str = Field(..., description="First name of the recipient")
    lastName: str = Field(..., description="Last name of the recipient")
    companyName: Optional[str] = Field(None, description="Company name")
    isBusiness: Optional[bool] = Field(None, description="Whether recipient is a business")
    federalTaxId: Optional[str] = Field(None, description="Federal tax identification number")
    stateTaxId: Optional[str] = Field(None, description="State tax identification number")
    registrationStateCode: Optional[str] = Field(None, description="State registration code")


class BillingEntity(Address):
    """Billing entity information."""
    
    companyName: str = Field(..., description="Company name")
    companyNumber: Optional[str] = Field(None, description="Company number")
    companyVatNumber: Optional[str] = Field(None, description="Company VAT number")
    recipientName: str = Field(..., description="Recipient name")


class ReturnAddress(Address):
    """Return address information."""
    
    companyName: Optional[str] = Field(None, description="Company name for returns")


class File(BaseModel):
    """File information for print jobs."""
    
    type: Optional[str] = Field("default", description="File type/print area")
    url: str = Field(..., description="URL to download the file")


class Preview(BaseModel):
    """Preview image information."""
    
    type: str = Field(..., description="Type of preview")
    url: str = Field(..., description="URL to preview image")


class Package(BaseModel):
    """Shipping package information."""
    
    id: str = Field(..., description="Package ID")
    orderItemIds: list[str] = Field(..., description="List of order item IDs in this package")
    trackingCode: Optional[str] = Field(None, description="Tracking code")
    trackingUrl: Optional[str] = Field(None, description="Tracking URL")


class Shipment(BaseModel):
    """Shipment information."""
    
    id: str = Field(..., description="Shipment ID")
    shipmentMethodName: str = Field(..., description="Name of shipping method")
    shipmentMethodUid: str = Field(..., description="UID of shipping method")
    minDeliveryDays: int = Field(..., description="Minimum delivery days")
    maxDeliveryDays: int = Field(..., description="Maximum delivery days")
    minDeliveryDate: Optional[str] = Field(None, description="Minimum delivery date")
    maxDeliveryDate: Optional[str] = Field(None, description="Maximum delivery date")
    totalWeight: int = Field(..., description="Total weight in grams")
    fulfillmentCountry: str = Field(..., description="Fulfillment country code")
    packagesCount: int = Field(..., description="Number of packages", alias="packageCount")
    packages: list[Package] = Field(default_factory=list, description="List of packages")


class ReceiptItem(BaseModel):
    """Receipt item information."""
    
    id: str = Field(..., description="Receipt item ID")
    receiptId: str = Field(..., description="Receipt ID")
    referenceId: str = Field(..., description="Reference to order item or shipment")
    type: str = Field(..., description="Type of receipt item")
    title: str = Field(..., description="Title of receipt item")
    currency: str = Field(..., description="Currency code")
    priceBase: float = Field(..., description="Base price")
    amount: int = Field(..., description="Quantity")
    priceInitial: float = Field(..., description="Initial price")
    discount: float = Field(..., description="Discount amount")
    price: float = Field(..., description="Final price")
    vat: float = Field(..., description="VAT amount")
    priceInclVat: float = Field(..., description="Price including VAT")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class Receipt(BaseModel):
    """Order receipt information."""
    
    id: str = Field(..., description="Receipt ID")
    orderId: str = Field(..., description="Order ID")
    transactionType: str = Field(..., description="Transaction type")
    currency: str = Field(..., description="Currency code")
    items: list[ReceiptItem] = Field(..., description="List of receipt items")
    
    # Price summaries
    productsPriceInitial: float = Field(..., description="Initial products price")
    productsPriceDiscount: float = Field(..., description="Products price discount")
    productsPrice: float = Field(..., description="Products price")
    productsPriceVat: float = Field(..., description="Products VAT")
    productsPriceInclVat: float = Field(..., description="Products price including VAT")
    
    packagingPriceInitial: float = Field(..., description="Initial packaging price")
    packagingPriceDiscount: float = Field(..., description="Packaging price discount")
    packagingPrice: float = Field(..., description="Packaging price")
    packagingPriceVat: float = Field(..., description="Packaging VAT")
    packagingPriceInclVat: float = Field(..., description="Packaging price including VAT")
    
    shippingPriceInitial: float = Field(..., description="Initial shipping price")
    shippingPriceDiscount: float = Field(..., description="Shipping price discount")
    shippingPrice: float = Field(..., description="Shipping price")
    shippingPriceVat: float = Field(..., description="Shipping VAT")
    shippingPriceInclVat: float = Field(..., description="Shipping price including VAT")
    
    discount: float = Field(..., description="Total discount")
    discountVat: float = Field(..., description="Total discount VAT")
    discountInclVat: float = Field(..., description="Total discount including VAT")
    
    totalInitial: float = Field(..., description="Initial total")
    total: float = Field(..., description="Total amount")
    totalVat: float = Field(..., description="Total VAT")
    totalInclVat: float = Field(..., description="Total including VAT")