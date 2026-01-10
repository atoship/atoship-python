"""
atoship Python SDK Client
"""

import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
from pydantic import ValidationError as PydanticValidationError

from .models import *
from .exceptions import *
from .utils import (
    format_tracking_number,
    validate_order_data,
    build_query_params,
    join_url,
    retry_with_backoff,
    mask_sensitive_data
)


class atoshipSDK:
    """
    atoship Python SDK Client
    
    Provides a comprehensive interface to the atoship API for shipping and logistics operations.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.atoship.com",
        timeout: float = 30.0,
        max_retries: int = 3,
        debug: bool = False
    ):
        """
        Initialize atoship SDK client
        
        Args:
            api_key: Your atoship API key
            base_url: Base URL for the API (default: https://api.atoship.com)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries for failed requests (default: 3)
            debug: Enable debug logging (default: False)
        
        Raises:
            ConfigurationError: If API key is invalid
        """
        
        if not api_key or not isinstance(api_key, str):
            raise ConfigurationError("API key is required and must be a string")
        
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._max_retries = max_retries
        self._debug = debug
        
        # Initialize HTTP client
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                'User-Agent': 'atoship-Python-SDK/1.0.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-API-Key': api_key
            }
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client"""
        if hasattr(self, '_client'):
            self._client.close()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current SDK configuration (excluding sensitive data)"""
        return {
            'base_url': self._base_url,
            'timeout': self._timeout,
            'max_retries': self._max_retries,
            'debug': self._debug
        }
    
    def update_config(self, **kwargs):
        """Update SDK configuration"""
        if 'timeout' in kwargs:
            self._timeout = kwargs['timeout']
        if 'max_retries' in kwargs:
            self._max_retries = kwargs['max_retries']
        if 'debug' in kwargs:
            self._debug = kwargs['debug']
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
        
        Returns:
            Response data as dictionary
        
        Raises:
            Various atoshipError subclasses based on response
        """
        
        url = join_url(self._base_url, endpoint)
        
        # Build query parameters
        if params:
            query_params = build_query_params(params)
            if query_params:
                url += '?' + urlencode(query_params)
        
        # Prepare request data
        json_data = None
        if data:
            json_data = json.dumps(data, default=str)
        
        if self._debug:
            print(f"atoship SDK: {method} {url}")
            if data:
                masked_data = mask_sensitive_data(data)
                print(f"atoship SDK: Request data: {masked_data}")
        
        # Make request with retry logic
        @retry_with_backoff
        def make_request():
            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    content=json_data
                )
                
                if self._debug:
                    print(f"atoship SDK: Response status: {response.status_code}")
                
                return self._handle_response(response)
            
            except httpx.TimeoutException:
                raise TimeoutError("Request timed out")
            except httpx.NetworkError as e:
                raise NetworkError(f"Network error: {str(e)}")
            except httpx.HTTPError as e:
                raise NetworkError(f"HTTP error: {str(e)}")
        
        return make_request()
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and convert to appropriate format or exception"""
        
        try:
            response_data = response.json()
        except (json.JSONDecodeError, ValueError):
            response_data = {'error': 'Invalid JSON response'}
        
        if self._debug:
            print(f"atoship SDK: Response data: {response_data}")
        
        if response.is_success:
            return response_data
        
        # Handle error responses
        error = create_error_from_response(response.status_code, response_data)
        raise error
    
    def _validate_and_convert(self, data: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Validate data against Pydantic model and return dict"""
        try:
            model_instance = model_class(**data)
            return model_instance.dict(by_alias=True)
        except PydanticValidationError as e:
            raise ValidationError(f"Validation error: {str(e)}")
    
    # Order Management
    
    def create_order(self, order_data: Dict[str, Any]) -> APIResponse:
        """
        Create a new order
        
        Args:
            order_data: Order information including recipient details and items
        
        Returns:
            APIResponse with created order data
        """
        
        # Validate order data
        validation_errors = validate_order_data(order_data)
        if validation_errors:
            raise ValidationError(f"Order validation failed: {'; '.join(validation_errors)}")
        
        # Convert to proper format
        validated_data = self._validate_and_convert(order_data, CreateOrderRequest)
        
        response_data = self._make_request('POST', '/api/orders', validated_data)
        return APIResponse(**response_data)
    
    def get_order(self, order_id: str) -> APIResponse:
        """Get order by ID"""
        response_data = self._make_request('GET', f'/api/orders/{order_id}')
        return APIResponse(**response_data)
    
    def list_orders(
        self,
        page: int = 1,
        limit: int = 50,
        status: Optional[str] = None,
        source: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> PaginatedResponse:
        """
        List orders with pagination and filtering
        
        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 50, max: 100)
            status: Filter by order status
            source: Filter by order source
            date_from: Filter orders from date (ISO format)
            date_to: Filter orders to date (ISO format)
        
        Returns:
            PaginatedResponse with order list
        """
        
        params = {
            'page': page,
            'limit': min(limit, 100),  # Enforce max limit
            'status': status,
            'source': source,
            'dateFrom': date_from,
            'dateTo': date_to
        }
        
        response_data = self._make_request('GET', '/api/orders', params=params)
        return PaginatedResponse(**response_data)
    
    def update_order(self, order_id: str, order_data: Dict[str, Any]) -> APIResponse:
        """Update an existing order"""
        response_data = self._make_request('PUT', f'/api/orders/{order_id}', order_data)
        return APIResponse(**response_data)
    
    def delete_order(self, order_id: str) -> APIResponse:
        """Delete an order"""
        response_data = self._make_request('DELETE', f'/api/orders/{order_id}')
        return APIResponse(**response_data)
    
    def create_orders_batch(self, orders: List[Dict[str, Any]]) -> APIResponse:
        """
        Create multiple orders in a batch
        
        Args:
            orders: List of order data dictionaries
        
        Returns:
            APIResponse with batch creation results
        """
        
        if not orders or len(orders) == 0:
            raise ValidationError("At least one order is required for batch creation")
        
        if len(orders) > 100:
            raise ValidationError("Maximum 100 orders allowed per batch")
        
        # Validate each order
        for i, order_data in enumerate(orders):
            validation_errors = validate_order_data(order_data)
            if validation_errors:
                raise ValidationError(f"Order {i+1} validation failed: {'; '.join(validation_errors)}")
        
        response_data = self._make_request('POST', '/api/orders/batch', {'orders': orders})
        return APIResponse(**response_data)
    
    # Shipping Rates
    
    def get_rates(self, rate_request: Dict[str, Any]) -> APIResponse:
        """
        Get shipping rates for a package
        
        Args:
            rate_request: Rate request with from/to addresses and package details
        
        Returns:
            APIResponse with available shipping rates
        """
        
        validated_data = self._validate_and_convert(rate_request, GetRatesRequest)
        response_data = self._make_request('POST', '/api/shipping/rates', validated_data)
        return APIResponse(**response_data)
    
    def compare_rates(self, rate_request: Dict[str, Any]) -> APIResponse:
        """Get and compare rates from multiple carriers"""
        validated_data = self._validate_and_convert(rate_request, GetRatesRequest)
        response_data = self._make_request('POST', '/api/shipping/rates/compare', validated_data)
        return APIResponse(**response_data)
    
    # Label Management
    
    def purchase_label(self, label_request: Dict[str, Any]) -> APIResponse:
        """
        Purchase a shipping label
        
        Args:
            label_request: Label purchase request with rate and address details
        
        Returns:
            APIResponse with purchased label information
        """
        
        validated_data = self._validate_and_convert(label_request, PurchaseLabelRequest)
        response_data = self._make_request('POST', '/api/shipping/labels', validated_data)
        return APIResponse(**response_data)
    
    def get_label(self, label_id: str) -> APIResponse:
        """Get label by ID"""
        response_data = self._make_request('GET', f'/api/shipping/labels/{label_id}')
        return APIResponse(**response_data)
    
    def list_labels(
        self,
        page: int = 1,
        limit: int = 50,
        status: Optional[str] = None,
        carrier: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> PaginatedResponse:
        """List shipping labels with pagination and filtering"""
        
        params = {
            'page': page,
            'limit': min(limit, 100),
            'status': status,
            'carrier': carrier,
            'dateFrom': date_from,
            'dateTo': date_to
        }
        
        response_data = self._make_request('GET', '/api/shipping/labels', params=params)
        return PaginatedResponse(**response_data)
    
    def cancel_label(self, label_id: str) -> APIResponse:
        """Cancel a shipping label"""
        response_data = self._make_request('POST', f'/api/shipping/labels/{label_id}/cancel')
        return APIResponse(**response_data)
    
    def refund_label(self, label_id: str) -> APIResponse:
        """Request refund for a shipping label"""
        response_data = self._make_request('POST', f'/api/shipping/labels/{label_id}/refund')
        return APIResponse(**response_data)
    
    # Tracking
    
    def track_package(self, tracking_number: str, carrier: Optional[str] = None) -> APIResponse:
        """
        Track a package by tracking number
        
        Args:
            tracking_number: Package tracking number
            carrier: Carrier name (optional, auto-detected if not provided)
        
        Returns:
            APIResponse with tracking information
        """
        
        formatted_tracking = format_tracking_number(tracking_number)
        params = {}
        if carrier:
            params['carrier'] = carrier
        
        response_data = self._make_request(
            'GET', 
            f'/api/tracking/{formatted_tracking}',
            params=params
        )
        return APIResponse(**response_data)
    
    def track_multiple(self, tracking_numbers: List[str]) -> APIResponse:
        """Track multiple packages"""
        if len(tracking_numbers) > 50:
            raise ValidationError("Maximum 50 tracking numbers allowed per request")
        
        data = {
            'trackingNumbers': [format_tracking_number(tn) for tn in tracking_numbers]
        }
        
        response_data = self._make_request('POST', '/api/tracking/batch', data)
        return APIResponse(**response_data)
    
    # Address Management
    
    def validate_address(self, address_data: Dict[str, Any]) -> APIResponse:
        """Validate an address"""
        validated_data = self._validate_and_convert(address_data, Address)
        response_data = self._make_request('POST', '/api/addresses/validate', validated_data)
        return APIResponse(**response_data)
    
    def suggest_addresses(self, query: str, country: str = 'US') -> APIResponse:
        """Get address suggestions based on query"""
        params = {'q': query, 'country': country}
        response_data = self._make_request('GET', '/api/addresses/suggest', params=params)
        return APIResponse(**response_data)
    
    def save_address(self, address_data: Dict[str, Any]) -> APIResponse:
        """Save an address to address book"""
        validated_data = self._validate_and_convert(address_data, Address)
        response_data = self._make_request('POST', '/api/addresses', validated_data)
        return APIResponse(**response_data)
    
    def list_addresses(self, page: int = 1, limit: int = 50) -> PaginatedResponse:
        """List saved addresses"""
        params = {'page': page, 'limit': min(limit, 100)}
        response_data = self._make_request('GET', '/api/addresses', params=params)
        return PaginatedResponse(**response_data)
    
    def get_address(self, address_id: str) -> APIResponse:
        """Get address by ID"""
        response_data = self._make_request('GET', f'/api/addresses/{address_id}')
        return APIResponse(**response_data)
    
    def update_address(self, address_id: str, address_data: Dict[str, Any]) -> APIResponse:
        """Update an address"""
        response_data = self._make_request('PUT', f'/api/addresses/{address_id}', address_data)
        return APIResponse(**response_data)
    
    def delete_address(self, address_id: str) -> APIResponse:
        """Delete an address"""
        response_data = self._make_request('DELETE', f'/api/addresses/{address_id}')
        return APIResponse(**response_data)
    
    # User and Account Management
    
    def get_profile(self) -> APIResponse:
        """Get user profile information"""
        response_data = self._make_request('GET', '/api/profile')
        return APIResponse(**response_data)
    
    def update_profile(self, profile_data: Dict[str, Any]) -> APIResponse:
        """Update user profile"""
        response_data = self._make_request('PUT', '/api/profile', profile_data)
        return APIResponse(**response_data)
    
    def get_usage(self) -> APIResponse:
        """Get account usage statistics"""
        response_data = self._make_request('GET', '/api/account/usage')
        return APIResponse(**response_data)
    
    def get_billing(self) -> APIResponse:
        """Get billing information"""
        response_data = self._make_request('GET', '/api/account/billing')
        return APIResponse(**response_data)
    
    # API Key Management
    
    def create_api_key(self, key_data: Dict[str, Any]) -> APIResponse:
        """Create a new API key"""
        validated_data = self._validate_and_convert(key_data, ApiKey)
        response_data = self._make_request('POST', '/api/keys', validated_data)
        return APIResponse(**response_data)
    
    def list_api_keys(self) -> APIResponse:
        """List API keys"""
        response_data = self._make_request('GET', '/api/keys')
        return APIResponse(**response_data)
    
    def revoke_api_key(self, key_id: str) -> APIResponse:
        """Revoke an API key"""
        response_data = self._make_request('DELETE', f'/api/keys/{key_id}')
        return APIResponse(**response_data)
    
    # Webhook Management
    
    def create_webhook(self, webhook_data: Dict[str, Any]) -> APIResponse:
        """Create a new webhook"""
        validated_data = self._validate_and_convert(webhook_data, Webhook)
        response_data = self._make_request('POST', '/api/webhooks', validated_data)
        return APIResponse(**response_data)
    
    def list_webhooks(self) -> APIResponse:
        """List webhooks"""
        response_data = self._make_request('GET', '/api/webhooks')
        return APIResponse(**response_data)
    
    def get_webhook(self, webhook_id: str) -> APIResponse:
        """Get webhook by ID"""
        response_data = self._make_request('GET', f'/api/webhooks/{webhook_id}')
        return APIResponse(**response_data)
    
    def update_webhook(self, webhook_id: str, webhook_data: Dict[str, Any]) -> APIResponse:
        """Update a webhook"""
        response_data = self._make_request('PUT', f'/api/webhooks/{webhook_id}', webhook_data)
        return APIResponse(**response_data)
    
    def delete_webhook(self, webhook_id: str) -> APIResponse:
        """Delete a webhook"""
        response_data = self._make_request('DELETE', f'/api/webhooks/{webhook_id}')
        return APIResponse(**response_data)
    
    def test_webhook(self, webhook_id: str) -> APIResponse:
        """Test a webhook by sending a test event"""
        response_data = self._make_request('POST', f'/api/webhooks/{webhook_id}/test')
        return APIResponse(**response_data)
    
    # Carrier Management
    
    def list_carriers(self) -> APIResponse:
        """List available carriers"""
        response_data = self._make_request('GET', '/api/carriers')
        return APIResponse(**response_data)
    
    def get_carrier(self, carrier_code: str) -> APIResponse:
        """Get carrier information"""
        response_data = self._make_request('GET', f'/api/carriers/{carrier_code}')
        return APIResponse(**response_data)
    
    def add_carrier_account(self, account_data: Dict[str, Any]) -> APIResponse:
        """Add a new carrier account"""
        validated_data = self._validate_and_convert(account_data, CarrierAccount)
        response_data = self._make_request('POST', '/api/carrier-accounts', validated_data)
        return APIResponse(**response_data)
    
    def list_carrier_accounts(self) -> APIResponse:
        """List carrier accounts"""
        response_data = self._make_request('GET', '/api/carrier-accounts')
        return APIResponse(**response_data)
    
    def update_carrier_account(self, account_id: str, account_data: Dict[str, Any]) -> APIResponse:
        """Update carrier account"""
        response_data = self._make_request('PUT', f'/api/carrier-accounts/{account_id}', account_data)
        return APIResponse(**response_data)
    
    def delete_carrier_account(self, account_id: str) -> APIResponse:
        """Delete carrier account"""
        response_data = self._make_request('DELETE', f'/api/carrier-accounts/{account_id}')
        return APIResponse(**response_data)
    
    # Monitoring and Analytics
    
    def get_monitoring_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> APIResponse:
        """Get monitoring metrics"""
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        response_data = self._make_request('GET', '/api/monitoring/metrics', params=params)
        return APIResponse(**response_data)
    
    def get_performance_metrics(self) -> APIResponse:
        """Get performance metrics"""
        response_data = self._make_request('GET', '/api/monitoring/performance')
        return APIResponse(**response_data)
    
    def get_analytics(
        self,
        metric: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[str] = None
    ) -> APIResponse:
        """Get analytics data"""
        params = {'metric': metric}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        if group_by:
            params['groupBy'] = group_by
        
        response_data = self._make_request('GET', '/api/analytics', params=params)
        return APIResponse(**response_data)
    
    # Utility Methods
    
    def health_check(self) -> APIResponse:
        """Check API health status"""
        response_data = self._make_request('GET', '/api/health')
        return APIResponse(**response_data)
    
    def get_system_status(self) -> APIResponse:
        """Get system status information"""
        response_data = self._make_request('GET', '/api/status')
        return APIResponse(**response_data)