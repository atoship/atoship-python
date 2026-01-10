"""
Utility functions for atoship SDK
"""

import re
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from .models import CreateOrderRequest, OrderItem, Address


def format_tracking_number(tracking_number: str) -> str:
    """Format tracking number by removing whitespace and converting to uppercase"""
    return tracking_number.strip().upper()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_phone(phone: str) -> bool:
    """Validate phone number format (basic validation)"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if we have 10-15 digits (international format)
    return 10 <= len(digits) <= 15


def validate_postal_code(postal_code: str, country: str = 'US') -> bool:
    """Validate postal code format based on country"""
    postal_code = postal_code.strip().upper()
    
    if country.upper() == 'US':
        # US ZIP code: 12345 or 12345-6789
        return bool(re.match(r'^\d{5}(-\d{4})?$', postal_code))
    elif country.upper() == 'CA':
        # Canadian postal code: A1A 1A1
        return bool(re.match(r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$', postal_code))
    elif country.upper() == 'GB':
        # UK postal code (simplified)
        return bool(re.match(r'^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$', postal_code))
    else:
        # Basic validation for other countries (alphanumeric, 3-10 chars)
        return bool(re.match(r'^[A-Z0-9\s-]{3,10}$', postal_code))


def normalize_address(address: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize address data"""
    normalized = address.copy()
    
    # Normalize postal code
    if 'postalCode' in normalized and 'country' in normalized:
        normalized['postalCode'] = normalized['postalCode'].strip().upper()
    
    # Normalize country code
    if 'country' in normalized:
        normalized['country'] = normalized['country'].strip().upper()
    
    # Normalize state/province
    if 'state' in normalized:
        normalized['state'] = normalized['state'].strip().upper()
    
    # Trim string fields
    string_fields = ['name', 'company', 'street1', 'street2', 'city', 'phone', 'email']
    for field in string_fields:
        if field in normalized and normalized[field]:
            normalized[field] = normalized[field].strip()
    
    return normalized


def validate_order_data(order_data: Dict[str, Any]) -> List[str]:
    """Validate order data and return list of validation errors"""
    errors = []
    
    # Required fields
    required_fields = [
        'orderNumber',
        'recipientName',
        'recipientStreet1',
        'recipientCity',
        'recipientState',
        'recipientPostalCode',
        'recipientCountry',
        'items'
    ]
    
    for field in required_fields:
        if field not in order_data or not order_data[field]:
            errors.append(f"'{field}' is required")
    
    # Validate recipient email if provided
    if 'recipientEmail' in order_data and order_data['recipientEmail']:
        if not validate_email(order_data['recipientEmail']):
            errors.append("Invalid recipient email format")
    
    # Validate recipient phone if provided
    if 'recipientPhone' in order_data and order_data['recipientPhone']:
        if not validate_phone(order_data['recipientPhone']):
            errors.append("Invalid recipient phone format")
    
    # Validate postal code
    if 'recipientPostalCode' in order_data and 'recipientCountry' in order_data:
        if not validate_postal_code(order_data['recipientPostalCode'], order_data['recipientCountry']):
            errors.append("Invalid postal code format")
    
    # Validate items
    if 'items' in order_data:
        if not isinstance(order_data['items'], list) or len(order_data['items']) == 0:
            errors.append("At least one item is required")
        else:
            for i, item in enumerate(order_data['items']):
                item_errors = validate_order_item(item, i)
                errors.extend(item_errors)
    
    return errors


def validate_order_item(item: Dict[str, Any], index: int) -> List[str]:
    """Validate individual order item"""
    errors = []
    prefix = f"Item {index + 1}"
    
    # Required fields
    required_fields = ['name', 'sku', 'quantity', 'unitPrice', 'weight', 'weightUnit']
    
    for field in required_fields:
        if field not in item or item[field] is None:
            errors.append(f"{prefix}: '{field}' is required")
    
    # Validate numeric fields
    if 'quantity' in item:
        if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
            errors.append(f"{prefix}: quantity must be a positive integer")
    
    if 'unitPrice' in item:
        if not isinstance(item['unitPrice'], (int, float)) or item['unitPrice'] <= 0:
            errors.append(f"{prefix}: unitPrice must be a positive number")
    
    if 'weight' in item:
        if not isinstance(item['weight'], (int, float)) or item['weight'] <= 0:
            errors.append(f"{prefix}: weight must be a positive number")
    
    # Validate weight unit
    if 'weightUnit' in item:
        valid_units = ['lb', 'kg', 'oz', 'g']
        if item['weightUnit'] not in valid_units:
            errors.append(f"{prefix}: weightUnit must be one of {valid_units}")
    
    return errors


def build_query_params(params: Dict[str, Any]) -> Dict[str, str]:
    """Build query parameters, converting values to strings and filtering None values"""
    query_params = {}
    
    for key, value in params.items():
        if value is not None:
            if isinstance(value, bool):
                query_params[key] = 'true' if value else 'false'
            elif isinstance(value, list):
                query_params[key] = ','.join(str(v) for v in value)
            else:
                query_params[key] = str(value)
    
    return query_params


def join_url(base_url: str, path: str) -> str:
    """Safely join base URL with path"""
    if not base_url.endswith('/'):
        base_url += '/'
    
    if path.startswith('/'):
        path = path[1:]
    
    return urljoin(base_url, path)


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff"""
    
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Don't retry on the last attempt
                if attempt == max_retries:
                    break
                
                # Check if error is retriable
                from .exceptions import is_retriable_error
                if not is_retriable_error(e):
                    break
                
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
        
        # Re-raise the last exception
        raise last_exception
    
    return wrapper


def mask_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str] = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary for logging"""
    
    if sensitive_fields is None:
        sensitive_fields = ['password', 'apiKey', 'api_key', 'secret', 'token', 'key']
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if key.lower() in [field.lower() for field in sensitive_fields]:
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                masked_data[key] = '***'
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, sensitive_fields)
    
    return masked_data


def calculate_package_weight(items: List[OrderItem]) -> float:
    """Calculate total package weight from order items"""
    total_weight = 0.0
    
    for item in items:
        item_weight = item.weight * item.quantity
        
        # Convert to pounds if needed
        if item.weight_unit == 'kg':
            item_weight *= 2.20462
        elif item.weight_unit == 'oz':
            item_weight /= 16
        elif item.weight_unit == 'g':
            item_weight /= 453.592
        
        total_weight += item_weight
    
    return total_weight


def get_default_package_dimensions(weight: float) -> Dict[str, float]:
    """Get default package dimensions based on weight"""
    
    if weight <= 1:
        return {'length': 6, 'width': 4, 'height': 2}
    elif weight <= 5:
        return {'length': 12, 'width': 8, 'height': 4}
    elif weight <= 10:
        return {'length': 16, 'width': 12, 'height': 6}
    elif weight <= 20:
        return {'length': 20, 'width': 16, 'height': 8}
    else:
        return {'length': 24, 'width': 18, 'height': 12}


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount"""
    
    if currency.upper() == 'USD':
        return f"${amount:.2f}"
    elif currency.upper() == 'EUR':
        return f"€{amount:.2f}"
    elif currency.upper() == 'GBP':
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency.upper()}"