"""
atoship Python SDK

Official Python SDK for the atoship API.
Provides a comprehensive, type-safe interface for all atoship shipping and logistics operations.
"""

from .client import atoshipSDK
from .models import *
from .exceptions import *

__version__ = "1.0.0"
__author__ = "atoship Team"
__email__ = "support@atoship.com"

__all__ = [
    "atoshipSDK",
    # Models
    "Order",
    "OrderItem", 
    "Address",
    "ShippingRate",
    "ShippingLabel",
    "TrackingInfo",
    "TrackingEvent",
    "User",
    "Plan",
    "ApiKey",
    "Webhook",
    "CarrierAccount",
    "MonitoringMetrics",
    "PerformanceMetrics",
    # Exceptions
    "atoshipError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError", 
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
    "ConfigurationError",
]