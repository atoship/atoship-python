# atoship Python SDK

[![PyPI version](https://badge.fury.io/py/atoship-sdk.svg)](https://badge.fury.io/py/atoship-sdk)
[![Python Support](https://img.shields.io/pypi/pyversions/atoship-sdk.svg)](https://pypi.org/project/atoship-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for the atoship API. Provides a comprehensive, type-safe interface for all atoship shipping and logistics operations.

## Features

- 🚀 **Complete API Coverage** - Support for all atoship API endpoints
- 🔒 **Type Safety** - Full type annotations with Pydantic models
- 🛡️ **Error Handling** - Comprehensive error handling with custom exceptions
- 🔄 **Retry Logic** - Automatic retry with exponential backoff for transient failures
- 📝 **Validation** - Request/response validation with detailed error messages
- 🐍 **Pythonic** - Follows Python best practices and conventions
- 📚 **Well Documented** - Comprehensive documentation with examples

## Installation

```bash
pip install atoship-sdk
```

## Quick Start

```python
from atoship import atoshipSDK

# Initialize the SDK
sdk = atoshipSDK(api_key="your-api-key")

# Create an order
order_data = {
    "orderNumber": "ORDER-001",
    "recipientName": "John Doe",
    "recipientStreet1": "123 Main St",
    "recipientCity": "San Francisco",
    "recipientState": "CA",
    "recipientPostalCode": "94105",
    "recipientCountry": "US",
    "items": [
        {
            "name": "Product Name",
            "sku": "PROD-001",
            "quantity": 1,
            "unitPrice": 29.99,
            "weight": 2.0,
            "weightUnit": "lb"
        }
    ]
}

try:
    response = sdk.create_order(order_data)
    if response.success:
        print(f"Order created: {response.data['id']}")
    else:
        print(f"Error: {response.error}")
except Exception as e:
    print(f"SDK Error: {e}")
```

## Authentication

The SDK requires an API key for authentication. You can obtain an API key from your atoship dashboard.

```python
# Initialize with API key
sdk = atoshipSDK(api_key="your-api-key")

# Optional: Custom configuration
sdk = atoshipSDK(
    api_key="your-api-key",
    base_url="https://api.atoship.com",  # Custom base URL
    timeout=30.0,                        # Request timeout in seconds
    max_retries=3,                       # Maximum retry attempts
    debug=True                           # Enable debug logging
)
```

## Core Features

### Order Management

```python
# Create a single order
response = sdk.create_order(order_data)

# Create multiple orders in batch
orders = [order_data_1, order_data_2, order_data_3]
response = sdk.create_orders_batch(orders)

# List orders with filtering
response = sdk.list_orders(
    page=1,
    limit=50,
    status="PENDING",
    date_from="2024-01-01",
    date_to="2024-01-31"
)

# Get specific order
response = sdk.get_order("order-id")

# Update order
response = sdk.update_order("order-id", updated_data)

# Delete order
response = sdk.delete_order("order-id")
```

### Shipping Rates

```python
# Get shipping rates
rate_request = {
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

response = sdk.get_rates(rate_request)

# Compare rates from multiple carriers
response = sdk.compare_rates(rate_request)
```

### Label Management

```python
# Purchase shipping label
label_request = {
    "orderId": "order-id",
    "rateId": "rate-id",
    "fromAddress": from_address,
    "toAddress": to_address,
    "package": package_details
}

response = sdk.purchase_label(label_request)

# List labels
response = sdk.list_labels(
    page=1,
    limit=50,
    status="PURCHASED",
    carrier="USPS"
)

# Get label details
response = sdk.get_label("label-id")

# Cancel label
response = sdk.cancel_label("label-id")

# Request refund
response = sdk.refund_label("label-id")
```

### Package Tracking

```python
# Track single package
response = sdk.track_package("1Z999AA1234567890")

# Track with specific carrier
response = sdk.track_package("1Z999AA1234567890", carrier="UPS")

# Track multiple packages
tracking_numbers = ["1Z999AA1234567890", "9400111206213123456789"]
response = sdk.track_multiple(tracking_numbers)
```

### Address Management

```python
# Validate address
address_data = {
    "name": "John Doe",
    "street1": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94105",
    "country": "US"
}

response = sdk.validate_address(address_data)

# Get address suggestions
response = sdk.suggest_addresses("123 Main St, San Francisco", country="US")

# Save address to address book
response = sdk.save_address(address_data)

# List saved addresses
response = sdk.list_addresses()
```

### Webhook Management

```python
# Create webhook
webhook_data = {
    "url": "https://your-site.com/webhook",
    "events": ["order.created", "label.purchased", "package.delivered"],
    "secret": "your-webhook-secret"
}

response = sdk.create_webhook(webhook_data)

# List webhooks
response = sdk.list_webhooks()

# Test webhook
response = sdk.test_webhook("webhook-id")
```

## Error Handling

The SDK provides comprehensive error handling with specific exception types:

```python
from atoship import (
    atoshipSDK,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ServerError
)

try:
    response = sdk.create_order(order_data)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Details: {e.details}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except NotFoundError as e:
    print(f"Resource not found: {e.message}")
except ServerError as e:
    print(f"Server error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Response Format

All SDK methods return an `APIResponse` or `PaginatedResponse` object:

```python
# Standard API Response
class APIResponse:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

# Paginated Response (for list operations)
class PaginatedResponse:
    success: bool
    data: Dict[str, Any]  # Contains 'items', 'total', 'page', etc.
    error: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

# Usage example
response = sdk.list_orders()
if response.success:
    orders = response.data['items']
    total = response.data['total']
    has_more = response.data['hasMore']
else:
    print(f"Error: {response.error}")
```

## Advanced Usage

### Context Manager

Use the SDK as a context manager to ensure proper cleanup:

```python
with atoshipSDK(api_key="your-api-key") as sdk:
    response = sdk.get_profile()
    # SDK will automatically close HTTP connections when exiting
```

### Configuration Updates

Update SDK configuration at runtime:

```python
sdk = atoshipSDK(api_key="your-api-key")

# Update configuration
sdk.update_config(
    timeout=60.0,
    max_retries=5,
    debug=True
)

# Get current configuration
config = sdk.get_config()
print(f"Current timeout: {config['timeout']}")
```

### Debug Mode

Enable debug mode to see detailed request/response information:

```python
sdk = atoshipSDK(api_key="your-api-key", debug=True)

# Or enable at runtime
sdk.update_config(debug=True)

# Debug output will show:
# - Request URLs and methods
# - Request data (with sensitive fields masked)
# - Response status codes
# - Response data
```

## Type Safety

The SDK provides full type safety with Pydantic models:

```python
from atoship.models import Order, OrderItem, Address, ShippingRate

# All models are properly typed
order: Order = Order(**order_data)
address: Address = Address(**address_data)

# IDE will provide full autocomplete and type checking
# Validation errors are caught at runtime with detailed messages
```

## Data Models

The SDK includes comprehensive data models for all API entities:

- `Order` - Order information and status
- `OrderItem` - Individual order line items
- `Address` - Shipping and billing addresses
- `ShippingRate` - Available shipping rates
- `ShippingLabel` - Purchased shipping labels
- `TrackingInfo` - Package tracking information
- `User` - User account information
- `ApiKey` - API key management
- `Webhook` - Webhook configuration
- `CarrierAccount` - Carrier account settings

## Validation

The SDK performs comprehensive validation:

```python
# Order validation includes:
# - Required fields checking
# - Email format validation
# - Phone number validation
# - Postal code validation by country
# - Item quantity and pricing validation
# - Weight and dimension validation

# Address validation includes:
# - Required field checking
# - Country-specific postal code formats
# - Email and phone format validation

# All validation errors include detailed messages
try:
    response = sdk.create_order(invalid_order_data)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    # e.message will contain specific field errors
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0
- pydantic >= 2.0.0
- typing-extensions >= 4.5.0

## Development

### Installation for Development

```bash
git clone https://github.com/atoship/sdk-python
cd sdk-python
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black atoship/
isort atoship/
```

### Type Checking

```bash
mypy atoship/
```

### Linting

```bash
flake8 atoship/
```

## Examples

See the [examples/](examples/) directory for comprehensive usage examples:

- [Basic Order Management](examples/basic_order_management.py)
- [Shipping Rate Comparison](examples/rate_comparison.py)
- [Label Purchasing Workflow](examples/label_workflow.py)
- [Package Tracking](examples/tracking.py)
- [Webhook Setup](examples/webhooks.py)
- [Address Validation](examples/address_validation.py)
- [Batch Operations](examples/batch_operations.py)

## Support

- 📧 Email: support@atoship.com
- 📚 Documentation: https://docs.atoship.com/sdk/python
- 🐛 Issues: https://github.com/atoship/sdk-python/issues
- 💬 Community: https://community.atoship.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.