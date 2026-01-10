"""
Tests for atoship SDK utilities
"""

import pytest

from atoship.utils import (
    format_tracking_number,
    validate_email,
    validate_url,
    validate_phone,
    validate_postal_code,
    normalize_address,
    validate_order_data,
    validate_order_item,
    build_query_params,
    join_url,
    mask_sensitive_data,
    calculate_package_weight,
    get_default_package_dimensions,
    format_currency
)
from atoship.models import OrderItem, WeightUnit


class TestFormatting:
    """Test formatting functions"""
    
    def test_format_tracking_number(self):
        """Test tracking number formatting"""
        # Test whitespace removal and case conversion
        assert format_tracking_number("  1z999aa1234567890  ") == "1Z999AA1234567890"
        assert format_tracking_number("1z999aa1234567890") == "1Z999AA1234567890"
        assert format_tracking_number("9400111206213123456789") == "9400111206213123456789"
        
        # Test already formatted
        assert format_tracking_number("1Z999AA1234567890") == "1Z999AA1234567890"
    
    def test_format_currency(self):
        """Test currency formatting"""
        assert format_currency(29.99, "USD") == "$29.99"
        assert format_currency(29.99, "EUR") == "€29.99"
        assert format_currency(29.99, "GBP") == "£29.99"
        assert format_currency(29.99, "CAD") == "29.99 CAD"
        
        # Test case insensitive
        assert format_currency(29.99, "usd") == "$29.99"


class TestValidation:
    """Test validation functions"""
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert validate_email("user@example.com") is True
        assert validate_email("test.email+tag@domain.co.uk") is True
        assert validate_email("user123@test-domain.org") is True
        
        # Invalid emails
        assert validate_email("invalid-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@@domain.com") is False
        assert validate_email("") is False
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        assert validate_url("https://example.com") is True
        assert validate_url("http://api.example.com/webhook") is True
        assert validate_url("https://subdomain.example.com:8080/path") is True
        
        # Invalid URLs
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False  # Wrong scheme
        assert validate_url("https://") is False
        assert validate_url("") is False
    
    def test_validate_phone(self):
        """Test phone number validation"""
        # Valid phone numbers
        assert validate_phone("415-555-0123") is True
        assert validate_phone("(415) 555-0123") is True
        assert validate_phone("4155550123") is True
        assert validate_phone("+1-415-555-0123") is True
        assert validate_phone("+44 20 7946 0958") is True  # UK number
        
        # Invalid phone numbers
        assert validate_phone("123") is False  # Too short
        assert validate_phone("123456789012345678901234567890") is False  # Too long
        assert validate_phone("") is False
        assert validate_phone("abc-def-ghij") is False  # No digits
    
    def test_validate_postal_code(self):
        """Test postal code validation"""
        # US ZIP codes
        assert validate_postal_code("94105", "US") is True
        assert validate_postal_code("94105-1234", "US") is True
        assert validate_postal_code("12345", "US") is True
        
        # Invalid US ZIP codes
        assert validate_postal_code("1234", "US") is False  # Too short
        assert validate_postal_code("123456", "US") is False  # Too long
        assert validate_postal_code("ABCDE", "US") is False  # Letters
        
        # Canadian postal codes
        assert validate_postal_code("K1A 0A6", "CA") is True
        assert validate_postal_code("K1A0A6", "CA") is True  # No space
        assert validate_postal_code("M5V 3A8", "CA") is True
        
        # Invalid Canadian postal codes
        assert validate_postal_code("12345", "CA") is False
        assert validate_postal_code("K1A", "CA") is False  # Too short
        
        # UK postal codes (simplified)
        assert validate_postal_code("SW1A 1AA", "GB") is True
        assert validate_postal_code("M1 1AA", "GB") is True
        assert validate_postal_code("M60 1NW", "GB") is True
        
        # Other countries (basic validation)
        assert validate_postal_code("10115", "DE") is True  # Germany
        assert validate_postal_code("75001", "FR") is True  # France
        assert validate_postal_code("100-0001", "JP") is True  # Japan


class TestAddressNormalization:
    """Test address normalization"""
    
    def test_normalize_address(self):
        """Test address data normalization"""
        address_data = {
            "name": "  John Doe  ",
            "company": "  Acme Corp  ",
            "street1": "  123 Main St  ",
            "city": "  san francisco  ",
            "state": "  ca  ",
            "postalCode": "  94105  ",
            "country": "  us  ",
            "phone": "  415-555-0123  ",
            "email": "  john@example.com  "
        }
        
        normalized = normalize_address(address_data)
        
        assert normalized["name"] == "John Doe"
        assert normalized["company"] == "Acme Corp"
        assert normalized["street1"] == "123 Main St"
        assert normalized["state"] == "CA"
        assert normalized["postalCode"] == "94105"
        assert normalized["country"] == "US"
        assert normalized["phone"] == "415-555-0123"
        assert normalized["email"] == "john@example.com"


class TestOrderValidation:
    """Test order validation functions"""
    
    def test_validate_order_data_valid(self):
        """Test validation of valid order data"""
        order_data = {
            "orderNumber": "ORDER-001",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "recipientEmail": "john@example.com",
            "recipientPhone": "415-555-0123",
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
        
        errors = validate_order_data(order_data)
        assert len(errors) == 0
    
    def test_validate_order_data_missing_fields(self):
        """Test validation with missing required fields"""
        order_data = {
            "orderNumber": "",  # Invalid: empty
            "recipientName": "John Doe",
            # Missing recipientStreet1, recipientCity, etc.
            "items": []  # Invalid: empty
        }
        
        errors = validate_order_data(order_data)
        assert len(errors) > 0
        
        # Check specific error messages
        error_text = " ".join(errors).lower()
        assert "ordernumber" in error_text
        assert "recipientstreet1" in error_text
        assert "items" in error_text
    
    def test_validate_order_data_invalid_email(self):
        """Test validation with invalid email"""
        order_data = {
            "orderNumber": "ORDER-001",
            "recipientName": "John Doe",
            "recipientStreet1": "123 Main St",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "recipientEmail": "invalid-email",  # Invalid
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
        
        errors = validate_order_data(order_data)
        assert len(errors) > 0
        assert any("email" in error.lower() for error in errors)
    
    def test_validate_order_item_valid(self):
        """Test validation of valid order item"""
        item_data = {
            "name": "Product 1",
            "sku": "SKU-1",
            "quantity": 2,
            "unitPrice": 29.99,
            "weight": 1.5,
            "weightUnit": "lb"
        }
        
        errors = validate_order_item(item_data, 0)
        assert len(errors) == 0
    
    def test_validate_order_item_invalid(self):
        """Test validation of invalid order item"""
        item_data = {
            "name": "",  # Invalid: empty
            "sku": "SKU-1",
            "quantity": 0,  # Invalid: must be > 0
            "unitPrice": -5.0,  # Invalid: must be > 0
            "weight": 0,  # Invalid: must be > 0
            "weightUnit": "invalid"  # Invalid: not in enum
        }
        
        errors = validate_order_item(item_data, 0)
        assert len(errors) > 0
        
        error_text = " ".join(errors).lower()
        assert "name" in error_text
        assert "quantity" in error_text
        assert "unitprice" in error_text
        assert "weight" in error_text
        assert "weightunit" in error_text


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_build_query_params(self):
        """Test query parameter building"""
        params = {
            "page": 1,
            "limit": 50,
            "active": True,
            "inactive": False,
            "tags": ["tag1", "tag2"],
            "empty": None,
            "search": "test query"
        }
        
        query_params = build_query_params(params)
        
        assert query_params["page"] == "1"
        assert query_params["limit"] == "50"
        assert query_params["active"] == "true"
        assert query_params["inactive"] == "false"
        assert query_params["tags"] == "tag1,tag2"
        assert query_params["search"] == "test query"
        assert "empty" not in query_params  # None values filtered out
    
    def test_join_url(self):
        """Test URL joining"""
        # Basic joining
        assert join_url("https://api.example.com", "orders") == "https://api.example.com/orders"
        assert join_url("https://api.example.com/", "orders") == "https://api.example.com/orders"
        assert join_url("https://api.example.com", "/orders") == "https://api.example.com/orders"
        assert join_url("https://api.example.com/", "/orders") == "https://api.example.com/orders"
        
        # Complex paths
        assert join_url("https://api.example.com", "api/v1/orders") == "https://api.example.com/api/v1/orders"
        assert join_url("https://api.example.com/api", "orders/123") == "https://api.example.com/api/orders/123"
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        data = {
            "username": "john_doe",
            "password": "secret123",
            "apiKey": "ak_1234567890abcdef",
            "api_key": "key_abcdef1234567890",
            "secret": "webhook_secret",
            "token": "token_xyz789",
            "normal_field": "normal_value",
            "nested": {
                "key": "nested_secret",
                "value": "normal_nested"
            }
        }
        
        masked = mask_sensitive_data(data)
        
        # Sensitive fields should be masked
        assert masked["password"] == "se****23"
        assert masked["apiKey"] == "ak***************ef"
        assert masked["api_key"] == "ke***************90"
        assert masked["secret"] == "we***********et"
        assert masked["token"] == "to*******89"
        
        # Normal fields should remain unchanged
        assert masked["username"] == "john_doe"
        assert masked["normal_field"] == "normal_value"
        
        # Nested sensitive fields should be masked
        assert masked["nested"]["key"] == "ne***********et"
        assert masked["nested"]["value"] == "normal_nested"
    
    def test_calculate_package_weight(self):
        """Test package weight calculation"""
        items = [
            OrderItem(
                name="Item 1",
                sku="SKU-1",
                quantity=2,
                unitPrice=10.0,
                weight=1.5,
                weightUnit=WeightUnit.LB
            ),
            OrderItem(
                name="Item 2",
                sku="SKU-2", 
                quantity=1,
                unitPrice=20.0,
                weight=0.5,
                weightUnit=WeightUnit.LB
            )
        ]
        
        total_weight = calculate_package_weight(items)
        assert total_weight == 3.5  # (1.5 * 2) + (0.5 * 1)
    
    def test_calculate_package_weight_unit_conversion(self):
        """Test package weight calculation with unit conversion"""
        items = [
            OrderItem(
                name="Item 1",
                sku="SKU-1",
                quantity=1,
                unitPrice=10.0,
                weight=1.0,
                weightUnit=WeightUnit.KG  # Should convert to ~2.20462 lbs
            ),
            OrderItem(
                name="Item 2",
                sku="SKU-2",
                quantity=1,
                unitPrice=20.0,
                weight=16.0,
                weightUnit=WeightUnit.OZ  # Should convert to 1 lb
            )
        ]
        
        total_weight = calculate_package_weight(items)
        assert abs(total_weight - 3.20462) < 0.001  # ~2.20462 + 1.0
    
    def test_get_default_package_dimensions(self):
        """Test default package dimensions"""
        # Light package
        dims = get_default_package_dimensions(0.5)
        assert dims == {'length': 6, 'width': 4, 'height': 2}
        
        # Medium package
        dims = get_default_package_dimensions(3.0)
        assert dims == {'length': 12, 'width': 8, 'height': 4}
        
        # Heavy package
        dims = get_default_package_dimensions(25.0)
        assert dims == {'length': 24, 'width': 18, 'height': 12}


if __name__ == "__main__":
    pytest.main([__file__])