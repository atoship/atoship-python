"""
Tests for atoship SDK models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from atoship.models import (
    Order, OrderItem, Address, ShippingRate, ShippingLabel,
    TrackingInfo, TrackingEvent, User, Plan, ApiKey, Webhook,
    CreateOrderRequest, GetRatesRequest, PurchaseLabelRequest,
    APIResponse, PaginatedResponse,
    OrderStatus, OrderSource, AddressType, UserRole, WeightUnit
)


class TestOrderModels:
    """Test order-related models"""
    
    def test_order_item_valid(self):
        """Test valid order item creation"""
        item_data = {
            "name": "Test Product",
            "sku": "TEST-SKU-001",
            "quantity": 2,
            "unitPrice": 29.99,
            "weight": 1.5,
            "weightUnit": "lb",
            "description": "Test product description"
        }
        
        item = OrderItem(**item_data)
        
        assert item.name == "Test Product"
        assert item.sku == "TEST-SKU-001"
        assert item.quantity == 2
        assert item.unit_price == 29.99
        assert item.weight == 1.5
        assert item.weight_unit == WeightUnit.LB
    
    def test_order_item_validation_errors(self):
        """Test order item validation errors"""
        # Missing required fields
        with pytest.raises(ValidationError):
            OrderItem()
        
        # Invalid quantity
        with pytest.raises(ValidationError):
            OrderItem(
                name="Test",
                sku="SKU",
                quantity=0,  # Should be > 0
                unitPrice=10.0,
                weight=1.0,
                weightUnit="lb"
            )
        
        # Invalid unit price
        with pytest.raises(ValidationError):
            OrderItem(
                name="Test",
                sku="SKU",
                quantity=1,
                unitPrice=-5.0,  # Should be > 0
                weight=1.0,
                weightUnit="lb"
            )
    
    def test_order_valid(self):
        """Test valid order creation"""
        order_data = {
            "orderNumber": "ORDER-001",
            "status": "PENDING",
            "source": "API",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "items": [
                {
                    "name": "Product 1",
                    "sku": "SKU-1",
                    "quantity": 1,
                    "unitPrice": 10.0,
                    "weight": 1.0,
                    "weightUnit": "lb"
                }
            ]
        }
        
        order = Order(**order_data)
        
        assert order.order_number == "ORDER-001"
        assert order.status == OrderStatus.PENDING
        assert order.source == OrderSource.API
        assert order.recipient_name == "John Doe"
        assert len(order.items) == 1
    
    def test_order_items_validation(self):
        """Test order items validation"""
        order_data = {
            "orderNumber": "ORDER-001",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "items": []  # Empty items should fail validation
        }
        
        with pytest.raises(ValidationError) as exc_info:
            Order(**order_data)
        
        assert "at least one item" in str(exc_info.value).lower()


class TestAddressModels:
    """Test address models"""
    
    def test_address_valid(self):
        """Test valid address creation"""
        address_data = {
            "type": "SHIPPING",
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postalCode": "94105",
            "country": "US",
            "phone": "415-555-0123",
            "email": "john@example.com"
        }
        
        address = Address(**address_data)
        
        assert address.type == AddressType.SHIPPING
        assert address.name == "John Doe"
        assert address.postal_code == "94105"
        assert address.phone == "415-555-0123"
    
    def test_address_field_aliases(self):
        """Test address field aliases work correctly"""
        # Test with camelCase (API format)
        address_data = {
            "type": "SHIPPING",
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postalCode": "94105",  # camelCase
            "country": "US",
            "isDefault": True,      # camelCase
            "isValidated": False    # camelCase
        }
        
        address = Address(**address_data)
        
        # Should map to snake_case internal fields
        assert address.postal_code == "94105"
        assert address.is_default is True
        assert address.is_validated is False
        
        # Test serialization with aliases
        data = address.dict(by_alias=True)
        assert "postalCode" in data
        assert "isDefault" in data
        assert "isValidated" in data


class TestShippingModels:
    """Test shipping-related models"""
    
    def test_shipping_rate_valid(self):
        """Test valid shipping rate creation"""
        rate_data = {
            "id": "rate-123",
            "carrier": "USPS",
            "service": "GROUND",
            "serviceName": "USPS Ground",
            "amount": 8.50,
            "currency": "USD",
            "estimatedDays": 3,
            "deliveryDate": "2024-01-18",
            "guaranteedDelivery": False
        }
        
        rate = ShippingRate(**rate_data)
        
        assert rate.id == "rate-123"
        assert rate.carrier == "USPS"
        assert rate.amount == 8.50
        assert rate.estimated_days == 3
        assert rate.guaranteed_delivery is False
    
    def test_shipping_label_valid(self):
        """Test valid shipping label creation"""
        label_data = {
            "orderId": "order-123",
            "carrier": "USPS",
            "service": "GROUND",
            "trackingNumber": "9400111206213123456789",
            "labelUrl": "https://example.com/label.pdf",
            "cost": 8.50,
            "currency": "USD",
            "status": "PURCHASED",
            "weight": 2.0
        }
        
        label = ShippingLabel(**label_data)
        
        assert label.order_id == "order-123"
        assert label.tracking_number == "9400111206213123456789"
        assert label.cost == 8.50
        assert label.weight == 2.0
    
    def test_tracking_info_valid(self):
        """Test valid tracking info creation"""
        tracking_data = {
            "trackingNumber": "1Z999AA1234567890",
            "carrier": "UPS",
            "status": "IN_TRANSIT",
            "estimatedDelivery": "2024-01-20",
            "events": [
                {
                    "timestamp": "2024-01-15T10:00:00Z",
                    "status": "PICKED_UP",
                    "description": "Package picked up",
                    "location": "San Francisco, CA",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "US"
                },
                {
                    "timestamp": "2024-01-16T14:30:00Z",
                    "status": "IN_TRANSIT",
                    "description": "In transit to destination",
                    "location": "Oakland, CA"
                }
            ]
        }
        
        tracking = TrackingInfo(**tracking_data)
        
        assert tracking.tracking_number == "1Z999AA1234567890"
        assert tracking.carrier == "UPS"
        assert tracking.status == "IN_TRANSIT"
        assert len(tracking.events) == 2
        
        # Test tracking events
        first_event = tracking.events[0]
        assert first_event.status == "PICKED_UP"
        assert first_event.city == "San Francisco"
        assert first_event.state == "CA"


class TestUserModels:
    """Test user-related models"""
    
    def test_user_valid(self):
        """Test valid user creation"""
        user_data = {
            "email": "user@example.com",
            "name": "John Doe",
            "role": "USER",
            "status": "ACTIVE",
            "planId": "plan-123",
            "labelsUsed": 50,
            "apiRequestsUsed": 1000
        }
        
        user = User(**user_data)
        
        assert user.email == "user@example.com"
        assert user.name == "John Doe"
        assert user.role == UserRole.USER
        assert user.labels_used == 50
        assert user.api_requests_used == 1000
    
    def test_user_email_validation(self):
        """Test user email validation"""
        # Valid email
        user_data = {
            "email": "valid@example.com",
            "name": "John Doe"
        }
        user = User(**user_data)
        assert user.email == "valid@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            User(email="invalid-email", name="John Doe")
    
    def test_plan_valid(self):
        """Test valid plan creation"""
        plan_data = {
            "name": "Professional",
            "price": 29.99,
            "currency": "USD",
            "interval": "MONTHLY",
            "features": ["Feature 1", "Feature 2"],
            "labelsPerMonth": 1000,
            "usersIncluded": 5,
            "apiRequestsPerDay": 10000
        }
        
        plan = Plan(**plan_data)
        
        assert plan.name == "Professional"
        assert plan.price == 29.99
        assert plan.labels_per_month == 1000
        assert plan.users_included == 5
        assert len(plan.features) == 2


class TestAPIModels:
    """Test API-related models"""
    
    def test_api_key_valid(self):
        """Test valid API key creation"""
        key_data = {
            "name": "Production API Key",
            "key": "ak_1234567890abcdef",
            "permissions": ["orders:read", "orders:write", "labels:purchase"],
            "isActive": True,
            "requestCount": 1500
        }
        
        api_key = ApiKey(**key_data)
        
        assert api_key.name == "Production API Key"
        assert api_key.key == "ak_1234567890abcdef"
        assert len(api_key.permissions) == 3
        assert api_key.is_active is True
        assert api_key.request_count == 1500
    
    def test_webhook_valid(self):
        """Test valid webhook creation"""
        webhook_data = {
            "url": "https://api.example.com/webhook",
            "events": ["order.created", "label.purchased", "package.delivered"],
            "secret": "webhook_secret_123",
            "active": True,
            "successCount": 100,
            "failureCount": 2
        }
        
        webhook = Webhook(**webhook_data)
        
        assert webhook.url == "https://api.example.com/webhook"
        assert len(webhook.events) == 3
        assert webhook.active is True
        assert webhook.success_count == 100
        assert webhook.failure_count == 2
    
    def test_webhook_url_validation(self):
        """Test webhook URL validation"""
        # Valid URL
        webhook_data = {
            "url": "https://api.example.com/webhook",
            "events": ["order.created"]
        }
        webhook = Webhook(**webhook_data)
        assert webhook.url == "https://api.example.com/webhook"
        
        # Invalid URL
        with pytest.raises(ValidationError):
            Webhook(url="not-a-valid-url", events=["order.created"])


class TestRequestModels:
    """Test request models"""
    
    def test_create_order_request_valid(self):
        """Test valid create order request"""
        request_data = {
            "orderNumber": "ORDER-001",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "items": [
                {
                    "name": "Product 1",
                    "sku": "SKU-1",
                    "quantity": 1,
                    "unitPrice": 10.0,
                    "weight": 1.0,
                    "weightUnit": "lb"
                }
            ]
        }
        
        request = CreateOrderRequest(**request_data)
        
        assert request.order_number == "ORDER-001"
        assert request.recipient_name == "John Doe"
        assert len(request.items) == 1
    
    def test_get_rates_request_valid(self):
        """Test valid get rates request"""
        request_data = {
            "fromAddress": {
                "type": "SHIPPING",
                "name": "Warehouse",
                "street1": "123 Warehouse St",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US"
            },
            "toAddress": {
                "type": "SHIPPING",
                "name": "Customer",
                "street1": "456 Customer Ave",
                "city": "Los Angeles",
                "state": "CA",
                "postalCode": "90001",
                "country": "US"
            },
            "package": {
                "weight": 2.5,
                "length": 12,
                "width": 8,
                "height": 4,
                "weightUnit": "lb",
                "dimensionUnit": "in"
            }
        }
        
        request = GetRatesRequest(**request_data)
        
        assert request.from_address.name == "Warehouse"
        assert request.to_address.name == "Customer"
        assert request.package["weight"] == 2.5
    
    def test_purchase_label_request_valid(self):
        """Test valid purchase label request"""
        request_data = {
            "orderId": "order-123",
            "rateId": "rate-456",
            "fromAddress": {
                "type": "SHIPPING",
                "name": "Warehouse",
                "street1": "123 Warehouse St",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US"
            },
            "toAddress": {
                "type": "SHIPPING", 
                "name": "Customer",
                "street1": "456 Customer Ave",
                "city": "Los Angeles",
                "state": "CA",
                "postalCode": "90001",
                "country": "US"
            },
            "package": {
                "weight": 2.5,
                "weightUnit": "lb"
            }
        }
        
        request = PurchaseLabelRequest(**request_data)
        
        assert request.order_id == "order-123"
        assert request.rate_id == "rate-456"
        assert request.from_address.name == "Warehouse"


class TestResponseModels:
    """Test response models"""
    
    def test_api_response_valid(self):
        """Test valid API response"""
        response_data = {
            "success": True,
            "data": {"id": "123", "name": "Test"},
            "requestId": "req-123",
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        response = APIResponse(**response_data)
        
        assert response.success is True
        assert response.data["id"] == "123"
        assert response.request_id == "req-123"
    
    def test_api_response_error(self):
        """Test API response with error"""
        response_data = {
            "success": False,
            "error": "Validation failed",
            "requestId": "req-456"
        }
        
        response = APIResponse(**response_data)
        
        assert response.success is False
        assert response.error == "Validation failed"
        assert response.data is None
    
    def test_paginated_response_valid(self):
        """Test valid paginated response"""
        response_data = {
            "success": True,
            "data": {
                "items": [{"id": "1"}, {"id": "2"}],
                "total": 100,
                "page": 1,
                "limit": 50,
                "hasMore": True
            },
            "requestId": "req-789"
        }
        
        response = PaginatedResponse(**response_data)
        
        assert response.success is True
        assert len(response.data["items"]) == 2
        assert response.data["total"] == 100
        assert response.data["hasMore"] is True


class TestEnums:
    """Test enum values"""
    
    def test_order_status_enum(self):
        """Test OrderStatus enum values"""
        assert OrderStatus.PENDING == "PENDING"
        assert OrderStatus.PROCESSING == "PROCESSING"
        assert OrderStatus.SHIPPED == "SHIPPED"
        assert OrderStatus.DELIVERED == "DELIVERED"
        assert OrderStatus.CANCELLED == "CANCELLED"
        assert OrderStatus.RETURNED == "RETURNED"
    
    def test_weight_unit_enum(self):
        """Test WeightUnit enum values"""
        assert WeightUnit.LB == "lb"
        assert WeightUnit.KG == "kg"
        assert WeightUnit.OZ == "oz"
        assert WeightUnit.G == "g"
    
    def test_user_role_enum(self):
        """Test UserRole enum values"""
        assert UserRole.USER == "USER"
        assert UserRole.ADMIN == "ADMIN"
        assert UserRole.SUPER_ADMIN == "SUPER_ADMIN"


if __name__ == "__main__":
    pytest.main([__file__])