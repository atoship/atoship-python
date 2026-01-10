"""
Data models for atoship SDK
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class WeightUnit(str, Enum):
    LB = "lb"
    KG = "kg"
    OZ = "oz"
    G = "g"


class DimensionUnit(str, Enum):
    IN = "in"
    CM = "cm"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class OrderSource(str, Enum):
    MANUAL = "MANUAL"
    API = "API"
    CSV = "CSV"
    SHOPIFY = "SHOPIFY"
    EBAY = "EBAY"
    AMAZON = "AMAZON"


class AddressType(str, Enum):
    SHIPPING = "SHIPPING"
    BILLING = "BILLING"


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class LabelStatus(str, Enum):
    PENDING = "PENDING"
    PURCHASED = "PURCHASED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PlanInterval(str, Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class Address(BaseModel):
    """Address model"""
    id: Optional[str] = None
    type: AddressType
    name: str
    company: Optional[str] = None
    street1: str
    street2: Optional[str] = None
    city: str
    state: str
    postal_code: str = Field(alias="postalCode")
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_default: Optional[bool] = Field(default=False, alias="isDefault")
    is_validated: Optional[bool] = Field(default=False, alias="isValidated")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        use_enum_values = True


class OrderItem(BaseModel):
    """Order item model"""
    id: Optional[str] = None
    name: str
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0, alias="unitPrice")
    weight: float = Field(gt=0)
    weight_unit: WeightUnit = Field(alias="weightUnit")
    description: Optional[str] = None
    hs_code: Optional[str] = Field(default=None, alias="hsCode")
    origin_country: Optional[str] = Field(default=None, alias="originCountry")
    value: Optional[float] = None

    class Config:
        populate_by_name = True
        use_enum_values = True


class Order(BaseModel):
    """Order model"""
    id: Optional[str] = None
    order_number: str = Field(alias="orderNumber")
    status: OrderStatus = OrderStatus.PENDING
    source: OrderSource = OrderSource.MANUAL

    # Recipient information
    recipient_name: str = Field(alias="recipientName")
    recipient_company: Optional[str] = Field(default=None, alias="recipientCompany")
    recipient_street1: str = Field(alias="recipientStreet1")
    recipient_street2: Optional[str] = Field(default=None, alias="recipientStreet2")
    recipient_city: str = Field(alias="recipientCity")
    recipient_state: str = Field(alias="recipientState")
    recipient_postal_code: str = Field(alias="recipientPostalCode")
    recipient_country: str = Field(alias="recipientCountry")
    recipient_phone: Optional[str] = Field(default=None, alias="recipientPhone")
    recipient_email: Optional[str] = Field(default=None, alias="recipientEmail")

    # Package information
    package_length: Optional[float] = Field(default=None, alias="packageLength")
    package_width: Optional[float] = Field(default=None, alias="packageWidth")
    package_height: Optional[float] = Field(default=None, alias="packageHeight")
    package_weight: Optional[float] = Field(default=None, alias="packageWeight")
    weight_unit: Optional[WeightUnit] = Field(default=None, alias="weightUnit")
    dimension_unit: Optional[DimensionUnit] = Field(default=None, alias="dimensionUnit")

    # Order items
    items: List[OrderItem]

    # Addresses
    from_address_id: Optional[str] = Field(default=None, alias="fromAddressId")
    to_address_id: Optional[str] = Field(default=None, alias="toAddressId")

    # Timestamps
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    shipped_at: Optional[datetime] = Field(default=None, alias="shippedAt")
    delivered_at: Optional[datetime] = Field(default=None, alias="deliveredAt")

    # Additional metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, alias="customFields")

    class Config:
        populate_by_name = True
        use_enum_values = True

    @validator("items")
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one item is required")
        return v


class ShippingRate(BaseModel):
    """Shipping rate model"""
    id: str
    carrier: str
    service: str
    service_name: str = Field(alias="serviceName")
    amount: float
    currency: str = "USD"
    estimated_days: int = Field(alias="estimatedDays")
    delivery_date: Optional[str] = Field(default=None, alias="deliveryDate")
    guaranteed_delivery: Optional[bool] = Field(default=False, alias="guaranteedDelivery")
    residential: Optional[bool] = Field(default=False)
    signature_required: Optional[bool] = Field(default=False, alias="signatureRequired")
    package_id: Optional[str] = Field(default=None, alias="packageId")
    rate_id: Optional[str] = Field(default=None, alias="rateId")

    class Config:
        populate_by_name = True


class ShippingLabel(BaseModel):
    """Shipping label model"""
    id: Optional[str] = None
    order_id: str = Field(alias="orderId")
    carrier: str
    service: str
    tracking_number: str = Field(alias="trackingNumber")
    label_url: str = Field(alias="labelUrl")
    cost: float
    currency: str = "USD"
    status: LabelStatus = LabelStatus.PENDING
    purchased_at: Optional[datetime] = Field(default=None, alias="purchasedAt")
    refunded_at: Optional[datetime] = Field(default=None, alias="refundedAt")

    # Package information
    weight: float
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

    # Delivery information
    estimated_delivery_date: Optional[str] = Field(default=None, alias="estimatedDeliveryDate")
    delivered_at: Optional[datetime] = Field(default=None, alias="deliveredAt")

    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        use_enum_values = True


class TrackingEvent(BaseModel):
    """Tracking event model"""
    timestamp: str
    status: str
    description: str
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class TrackingInfo(BaseModel):
    """Tracking information model"""
    tracking_number: str = Field(alias="trackingNumber")
    carrier: str
    status: str
    estimated_delivery: Optional[str] = Field(default=None, alias="estimatedDelivery")
    events: List[TrackingEvent]
    last_update: Optional[str] = Field(default=None, alias="lastUpdate")

    class Config:
        populate_by_name = True


class Plan(BaseModel):
    """Plan model"""
    id: Optional[str] = None
    name: str
    price: float
    currency: str = "USD"
    interval: PlanInterval
    features: List[str]
    labels_per_month: int = Field(alias="labelsPerMonth")
    users_included: int = Field(alias="usersIncluded")
    api_requests_per_day: int = Field(alias="apiRequestsPerDay")
    is_active: Optional[bool] = Field(default=True, alias="isActive")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    class Config:
        populate_by_name = True
        use_enum_values = True


class User(BaseModel):
    """User model"""
    id: Optional[str] = None
    email: str
    name: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    plan_id: Optional[str] = Field(default=None, alias="planId")
    plan: Optional[Plan] = None

    # Usage information
    labels_used: Optional[int] = Field(default=0, alias="labelsUsed")
    api_requests_used: Optional[int] = Field(default=0, alias="apiRequestsUsed")
    last_login_at: Optional[datetime] = Field(default=None, alias="lastLoginAt")
    login_count: Optional[int] = Field(default=0, alias="loginCount")

    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True
        use_enum_values = True

    @validator("email")
    def validate_email(cls, v):
        import re
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v


class ApiKey(BaseModel):
    """API key model"""
    id: Optional[str] = None
    name: str
    key: Optional[str] = None  # Only returned when creating
    permissions: List[str]
    is_active: Optional[bool] = Field(default=True, alias="isActive")
    last_used_at: Optional[datetime] = Field(default=None, alias="lastUsedAt")
    request_count: Optional[int] = Field(default=0, alias="requestCount")
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    class Config:
        populate_by_name = True


class Webhook(BaseModel):
    """Webhook model"""
    id: Optional[str] = None
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    last_triggered_at: Optional[datetime] = Field(default=None, alias="lastTriggeredAt")
    success_count: Optional[int] = Field(default=0, alias="successCount")
    failure_count: Optional[int] = Field(default=0, alias="failureCount")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    class Config:
        populate_by_name = True

    @validator("url")
    def validate_url(cls, v):
        import re
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        if not re.match(pattern, v):
            raise ValueError("Invalid URL format")
        return v


class CarrierAccount(BaseModel):
    """Carrier account model"""
    id: Optional[str] = None
    carrier: str
    account_name: str = Field(alias="accountName")
    is_active: bool = Field(default=True, alias="isActive")
    is_default: Optional[bool] = Field(default=False, alias="isDefault")
    credentials: Dict[str, Any]
    last_used_at: Optional[datetime] = Field(default=None, alias="lastUsedAt")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    class Config:
        populate_by_name = True


class MonitoringMetrics(BaseModel):
    """Monitoring metrics model"""
    total_requests: int = Field(alias="totalRequests")
    successful_requests: int = Field(alias="successfulRequests")
    failed_requests: int = Field(alias="failedRequests")
    avg_response_time: float = Field(alias="avgResponseTime")
    p95_response_time: float = Field(alias="p95ResponseTime")
    error_rate: float = Field(alias="errorRate")
    top_endpoints: List[Dict[str, Union[str, int, float]]] = Field(alias="topEndpoints")
    errors: List[Dict[str, Union[str, int]]]

    class Config:
        populate_by_name = True


class PerformanceMetrics(BaseModel):
    """Performance metrics model"""
    system_health: str = Field(alias="systemHealth")
    uptime: float
    response_time: Dict[str, float] = Field(alias="responseTime")
    throughput: Dict[str, float]
    resources: Dict[str, float]
    database: Dict[str, Union[int, Dict[str, float]]]

    class Config:
        populate_by_name = True


# Request models
class CreateOrderRequest(BaseModel):
    """Create order request model"""
    order_number: str = Field(alias="orderNumber")
    recipient_name: str = Field(alias="recipientName")
    recipient_company: Optional[str] = Field(default=None, alias="recipientCompany")
    recipient_street1: str = Field(alias="recipientStreet1")
    recipient_street2: Optional[str] = Field(default=None, alias="recipientStreet2")
    recipient_city: str = Field(alias="recipientCity")
    recipient_state: str = Field(alias="recipientState")
    recipient_postal_code: str = Field(alias="recipientPostalCode")
    recipient_country: str = Field(alias="recipientCountry")
    recipient_phone: Optional[str] = Field(default=None, alias="recipientPhone")
    recipient_email: Optional[str] = Field(default=None, alias="recipientEmail")
    items: List[OrderItem]
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, alias="customFields")

    class Config:
        populate_by_name = True


class GetRatesRequest(BaseModel):
    """Get rates request model"""
    from_address: Address = Field(alias="fromAddress")
    to_address: Address = Field(alias="toAddress")
    package: Dict[str, Union[float, str]]
    options: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class PurchaseLabelRequest(BaseModel):
    """Purchase label request model"""
    order_id: Optional[str] = Field(default=None, alias="orderId")
    rate_id: str = Field(alias="rateId")
    from_address: Address = Field(alias="fromAddress")
    to_address: Address = Field(alias="toAddress")
    package: Dict[str, Union[float, str]]
    options: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


# Response models
class APIResponse(BaseModel):
    """Base API response model"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: Optional[str] = Field(default=None, alias="requestId")
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    request_id: Optional[str] = Field(default=None, alias="requestId")
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True