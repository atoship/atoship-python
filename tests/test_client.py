"""
Tests for atoship Python SDK Client
"""

import json
import pytest
from unittest.mock import Mock, patch
import httpx

from atoship import atoshipSDK
from atoship.exceptions import (
    ValidationError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    ConfigurationError
)


@pytest.fixture
def sdk():
    """Create SDK instance for testing"""
    return atoshipSDK(api_key="test-api-key", base_url="https://api.test.com")


@pytest.fixture
def mock_response():
    """Create mock HTTP response"""
    def _mock_response(status_code=200, json_data=None):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.is_success = 200 <= status_code < 300
        response.json.return_value = json_data or {}
        return response
    return _mock_response


class TestSDKInitialization:
    """Test SDK initialization and configuration"""
    
    def test_valid_initialization(self):
        """Test SDK initialization with valid parameters"""
        sdk = atoshipSDK(api_key="test-key")
        assert sdk is not None
        
        config = sdk.get_config()
        assert config['base_url'] == "https://api.atoship.com"
        assert config['timeout'] == 30.0
        assert config['max_retries'] == 3
        assert config['debug'] is False
    
    def test_custom_configuration(self):
        """Test SDK initialization with custom configuration"""
        sdk = atoshipSDK(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            debug=True
        )
        
        config = sdk.get_config()
        assert config['base_url'] == "https://custom.api.com"
        assert config['timeout'] == 60.0
        assert config['max_retries'] == 5
        assert config['debug'] is True
    
    def test_invalid_api_key(self):
        """Test SDK initialization with invalid API key"""
        with pytest.raises(ConfigurationError):
            atoshipSDK(api_key="")
        
        with pytest.raises(ConfigurationError):
            atoshipSDK(api_key=None)
    
    def test_config_update(self, sdk):
        """Test configuration update"""
        sdk.update_config(timeout=45.0, debug=True)
        
        config = sdk.get_config()
        assert config['timeout'] == 45.0
        assert config['debug'] is True
    
    def test_config_doesnt_expose_api_key(self, sdk):
        """Test that configuration doesn't expose API key"""
        config = sdk.get_config()
        assert 'api_key' not in config
        assert 'apiKey' not in config


class TestOrderManagement:
    """Test order management functionality"""
    
    @pytest.fixture
    def valid_order_data(self):
        """Valid order data for testing"""
        return {
            "orderNumber": "TEST-001",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "items": [
                {
                    "name": "Test Product",
                    "sku": "TEST-SKU",
                    "quantity": 1,
                    "unitPrice": 99.99,
                    "weight": 2.0,
                    "weightUnit": "lb"
                }
            ]
        }
    
    @patch('httpx.Client.request')
    def test_create_order_success(self, mock_request, sdk, valid_order_data, mock_response):
        """Test successful order creation"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"id": "order-123", **valid_order_data}
        })
        
        response = sdk.create_order(valid_order_data)
        
        assert response.success is True
        assert response.data['id'] == "order-123"
        mock_request.assert_called_once()
    
    def test_create_order_validation_error(self, sdk):
        """Test order creation with validation errors"""
        invalid_order_data = {
            "orderNumber": "",  # Invalid: empty
            "recipientName": "John Doe",
            "items": []  # Invalid: no items
        }
        
        with pytest.raises(ValidationError) as exc_info:
            sdk.create_order(invalid_order_data)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    @patch('httpx.Client.request')
    def test_get_order(self, mock_request, sdk, mock_response):
        """Test getting order by ID"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"id": "order-123"}
        })
        
        response = sdk.get_order("order-123")
        
        assert response.success is True
        assert response.data['id'] == "order-123"
    
    @patch('httpx.Client.request')
    def test_list_orders(self, mock_request, sdk, mock_response):
        """Test listing orders with pagination"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {
                "items": [{"id": "order-1"}, {"id": "order-2"}],
                "total": 2,
                "page": 1,
                "limit": 50,
                "hasMore": False
            }
        })
        
        response = sdk.list_orders(page=1, limit=50)
        
        assert response.success is True
        assert len(response.data['items']) == 2
        assert response.data['total'] == 2
    
    @patch('httpx.Client.request')
    def test_create_orders_batch(self, mock_request, sdk, valid_order_data, mock_response):
        """Test batch order creation"""
        orders = [valid_order_data.copy() for _ in range(3)]
        for i, order in enumerate(orders):
            order["orderNumber"] = f"BATCH-{i+1:03d}"
        
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {
                "successful": orders,
                "failed": []
            }
        })
        
        response = sdk.create_orders_batch(orders)
        
        assert response.success is True
        assert len(response.data['successful']) == 3
        assert len(response.data['failed']) == 0
    
    def test_create_orders_batch_empty(self, sdk):
        """Test batch order creation with empty list"""
        with pytest.raises(ValidationError) as exc_info:
            sdk.create_orders_batch([])
        
        assert "at least one order" in str(exc_info.value).lower()
    
    def test_create_orders_batch_too_many(self, sdk, valid_order_data):
        """Test batch order creation with too many orders"""
        orders = [valid_order_data.copy() for _ in range(101)]
        
        with pytest.raises(ValidationError) as exc_info:
            sdk.create_orders_batch(orders)
        
        assert "maximum 100 orders" in str(exc_info.value).lower()


class TestShippingRates:
    """Test shipping rate functionality"""
    
    @pytest.fixture
    def rate_request(self):
        """Rate request data for testing"""
        return {
            "fromAddress": {
                "name": "Warehouse",
                "street1": "123 Warehouse St",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US"
            },
            "toAddress": {
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
    
    @patch('httpx.Client.request')
    def test_get_rates(self, mock_request, sdk, rate_request, mock_response):
        """Test getting shipping rates"""
        mock_rates = [
            {
                "id": "rate-1",
                "carrier": "USPS",
                "service": "GROUND",
                "serviceName": "USPS Ground",
                "amount": 8.50,
                "currency": "USD",
                "estimatedDays": 3
            }
        ]
        
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": mock_rates
        })
        
        response = sdk.get_rates(rate_request)
        
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0]['carrier'] == "USPS"
    
    @patch('httpx.Client.request')
    def test_compare_rates(self, mock_request, sdk, rate_request, mock_response):
        """Test comparing rates from multiple carriers"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": []
        })
        
        response = sdk.compare_rates(rate_request)
        
        assert response.success is True


class TestPackageTracking:
    """Test package tracking functionality"""
    
    @patch('httpx.Client.request')
    def test_track_package(self, mock_request, sdk, mock_response):
        """Test tracking a single package"""
        tracking_number = "1Z999AA1234567890"
        mock_tracking = {
            "trackingNumber": tracking_number,
            "carrier": "UPS",
            "status": "IN_TRANSIT",
            "events": [
                {
                    "timestamp": "2024-01-15T10:00:00Z",
                    "status": "PICKED_UP",
                    "description": "Package picked up",
                    "location": "San Francisco, CA"
                }
            ]
        }
        
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": mock_tracking
        })
        
        response = sdk.track_package(tracking_number)
        
        assert response.success is True
        assert response.data['trackingNumber'] == tracking_number
        assert len(response.data['events']) == 1
    
    @patch('httpx.Client.request')
    def test_track_package_with_carrier(self, mock_request, sdk, mock_response):
        """Test tracking package with specific carrier"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"trackingNumber": "1Z999AA1234567890"}
        })
        
        sdk.track_package("1Z999AA1234567890", carrier="UPS")
        
        # Verify request was made with carrier parameter
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert "carrier=UPS" in args[1] or "carrier" in str(kwargs)
    
    @patch('httpx.Client.request')
    def test_track_multiple_packages(self, mock_request, sdk, mock_response):
        """Test tracking multiple packages"""
        tracking_numbers = ["1Z999AA1234567890", "9400111206213123456789"]
        
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"results": []}
        })
        
        response = sdk.track_multiple(tracking_numbers)
        
        assert response.success is True
    
    def test_track_multiple_too_many(self, sdk):
        """Test tracking too many packages at once"""
        tracking_numbers = [f"track-{i:03d}" for i in range(51)]
        
        with pytest.raises(ValidationError) as exc_info:
            sdk.track_multiple(tracking_numbers)
        
        assert "maximum 50 tracking numbers" in str(exc_info.value).lower()


class TestErrorHandling:
    """Test error handling functionality"""
    
    @patch('httpx.Client.request')
    def test_authentication_error(self, mock_request, sdk, mock_response):
        """Test handling authentication errors"""
        mock_request.return_value = mock_response(401, {
            "error": "Invalid API key",
            "code": "AUTHENTICATION_ERROR"
        })
        
        with pytest.raises(AuthenticationError):
            sdk.get_profile()
    
    @patch('httpx.Client.request')
    def test_rate_limit_error(self, mock_request, sdk, mock_response):
        """Test handling rate limit errors"""
        mock_request.return_value = mock_response(429, {
            "error": "Rate limit exceeded",
            "code": "RATE_LIMIT_EXCEEDED",
            "details": {"retryAfter": 60}
        })
        
        with pytest.raises(RateLimitError) as exc_info:
            sdk.get_profile()
        
        assert exc_info.value.retry_after == 60
    
    @patch('httpx.Client.request')
    def test_network_error(self, mock_request, sdk):
        """Test handling network errors"""
        mock_request.side_effect = httpx.NetworkError("Connection failed")
        
        with pytest.raises(NetworkError):
            sdk.get_profile()
    
    @patch('httpx.Client.request')
    def test_timeout_error(self, mock_request, sdk):
        """Test handling timeout errors"""
        mock_request.side_effect = httpx.TimeoutException("Request timed out")
        
        with pytest.raises(NetworkError):  # TimeoutError is wrapped in NetworkError
            sdk.get_profile()


class TestAddressManagement:
    """Test address management functionality"""
    
    @pytest.fixture
    def address_data(self):
        """Address data for testing"""
        return {
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postalCode": "94105",
            "country": "US",
            "type": "SHIPPING"
        }
    
    @patch('httpx.Client.request')
    def test_validate_address(self, mock_request, sdk, address_data, mock_response):
        """Test address validation"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"valid": True, "normalized": address_data}
        })
        
        response = sdk.validate_address(address_data)
        
        assert response.success is True
    
    @patch('httpx.Client.request')
    def test_suggest_addresses(self, mock_request, sdk, mock_response):
        """Test address suggestions"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"suggestions": []}
        })
        
        response = sdk.suggest_addresses("123 Main St", country="US")
        
        assert response.success is True


class TestWebhookManagement:
    """Test webhook management functionality"""
    
    @pytest.fixture
    def webhook_data(self):
        """Webhook data for testing"""
        return {
            "url": "https://example.com/webhook",
            "events": ["order.created", "label.purchased"],
            "secret": "webhook-secret"
        }
    
    @patch('httpx.Client.request')
    def test_create_webhook(self, mock_request, sdk, webhook_data, mock_response):
        """Test webhook creation"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"id": "webhook-123", **webhook_data}
        })
        
        response = sdk.create_webhook(webhook_data)
        
        assert response.success is True
        assert response.data['id'] == "webhook-123"
    
    @patch('httpx.Client.request')
    def test_list_webhooks(self, mock_request, sdk, mock_response):
        """Test listing webhooks"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"webhooks": []}
        })
        
        response = sdk.list_webhooks()
        
        assert response.success is True


class TestContextManager:
    """Test context manager functionality"""
    
    def test_context_manager(self):
        """Test SDK as context manager"""
        with atoshipSDK(api_key="test-key") as sdk:
            assert sdk is not None
            config = sdk.get_config()
            assert config is not None
        
        # SDK should be properly closed after context exit
        # (httpx.Client.close() should have been called)


class TestUtilityMethods:
    """Test utility methods"""
    
    @patch('httpx.Client.request')
    def test_health_check(self, mock_request, sdk, mock_response):
        """Test health check"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"status": "healthy"}
        })
        
        response = sdk.health_check()
        
        assert response.success is True
        assert response.data['status'] == "healthy"
    
    @patch('httpx.Client.request')
    def test_get_system_status(self, mock_request, sdk, mock_response):
        """Test system status"""
        mock_request.return_value = mock_response(200, {
            "success": True,
            "data": {"system": "operational"}
        })
        
        response = sdk.get_system_status()
        
        assert response.success is True


if __name__ == "__main__":
    pytest.main([__file__])