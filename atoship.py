"""
atoship Python SDK
Version: 1.0.0

Professional shipping API client for Python
"""

import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class AtoshipError(Exception):
    """Base exception for atoship SDK"""
    def __init__(self, message: str, code: str = None, status: int = None):
        super().__init__(message)
        self.code = code
        self.status = status


class AtoshipClient:
    """Main client for interacting with atoship API"""
    
    def __init__(self, api_key: str, base_url: str = None, test_mode: bool = False, 
                 timeout: int = 30, max_retries: int = 3):
        """
        Initialize atoship client
        
        Args:
            api_key: Your atoship API key
            base_url: API base URL (defaults to production)
            test_mode: Whether to use test mode
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url or 'https://api.atoship.com/v1'
        self.test_mode = test_mode
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize resources
        self.addresses = AddressResource(self)
        self.parcels = ParcelResource(self)
        self.shipments = ShipmentResource(self)
        self.rates = RateResource(self)
        self.batches = BatchResource(self)
        self.insurance = InsuranceResource(self)
        self.tracking = TrackingResource(self)
        self.webhooks = WebhookResource(self)
        self.reports = ReportResource(self)
        self.orders = OrderResource(self)
        self.channels = ChannelResource(self)
        self.pickups = PickupResource(self)
    
    def request(self, method: str, path: str, data: Dict = None, params: Dict = None) -> Dict:
        """
        Make API request
        
        Args:
            method: HTTP method
            path: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            AtoshipError: If API returns an error
        """
        url = f"{self.base_url}{path}"
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'atoship-python/1.0.0'
        }
        
        if params:
            url += '?' + urlencode(params)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            result = response.json()
            
            if not response.ok:
                error = result.get('error', {})
                raise AtoshipError(
                    message=error.get('message', 'API Error'),
                    code=error.get('code'),
                    status=response.status_code
                )
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise AtoshipError(f"Request failed: {str(e)}")


class Resource:
    """Base resource class"""
    
    def __init__(self, client: AtoshipClient):
        self.client = client
        self.base_path = ''
    
    def list(self, **params) -> Dict:
        """List resources"""
        return self.client.request('GET', self.base_path, params=params)
    
    def create(self, data: Dict) -> Dict:
        """Create resource"""
        return self.client.request('POST', self.base_path, data=data)
    
    def retrieve(self, resource_id: str) -> Dict:
        """Retrieve single resource"""
        return self.client.request('GET', f"{self.base_path}/{resource_id}")
    
    def update(self, resource_id: str, data: Dict) -> Dict:
        """Update resource"""
        return self.client.request('PUT', f"{self.base_path}/{resource_id}", data=data)
    
    def delete(self, resource_id: str) -> Dict:
        """Delete resource"""
        return self.client.request('DELETE', f"{self.base_path}/{resource_id}")


class AddressResource(Resource):
    """Address management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/addresses'
    
    def verify(self, address_id: str) -> Dict:
        """Verify an address"""
        return self.client.request('POST', f"{self.base_path}/{address_id}/verify")


class ParcelResource(Resource):
    """Parcel management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/parcels'
    
    def validate(self, data: Dict) -> Dict:
        """Validate parcel specifications"""
        return self.client.request('POST', f"{self.base_path}/validate", data=data)


class ShipmentResource(Resource):
    """Shipment management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/shipments'
    
    def buy(self, shipment_id: str, rate_id: str = None) -> Dict:
        """Purchase a shipping label"""
        data = {'rate_id': rate_id} if rate_id else {}
        return self.client.request('POST', f"{self.base_path}/{shipment_id}/buy", data=data)
    
    def refund(self, shipment_id: str) -> Dict:
        """Refund a shipment"""
        return self.client.request('POST', f"{self.base_path}/{shipment_id}/refund")
    
    def insure(self, shipment_id: str, amount: float) -> Dict:
        """Add insurance to shipment"""
        return self.client.request('POST', f"{self.base_path}/{shipment_id}/insure", 
                                  data={'amount': amount})
    
    def label(self, shipment_id: str, format: str = 'pdf') -> Dict:
        """Get shipment label"""
        return self.client.request('GET', f"{self.base_path}/{shipment_id}/label",
                                  params={'format': format})
    
    def rates(self, shipment_id: str) -> Dict:
        """Refresh shipment rates"""
        return self.client.request('POST', f"{self.base_path}/{shipment_id}/rates")


class RateResource(Resource):
    """Rate calculation"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/rates'
    
    def calculate(self, data: Dict) -> Dict:
        """Calculate shipping rates"""
        return self.client.request('POST', self.base_path, data=data)
    
    def estimate(self, data: Dict) -> Dict:
        """Quick rate estimate"""
        return self.client.request('POST', f"{self.base_path}/estimate", data=data)


class BatchResource(Resource):
    """Batch operations"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/batches'
    
    def add_shipments(self, batch_id: str, shipment_ids: List[str]) -> Dict:
        """Add shipments to batch"""
        return self.client.request('POST', f"{self.base_path}/{batch_id}/add_shipments",
                                  data={'shipments': shipment_ids})
    
    def remove_shipments(self, batch_id: str, shipment_ids: List[str]) -> Dict:
        """Remove shipments from batch"""
        return self.client.request('POST', f"{self.base_path}/{batch_id}/remove_shipments",
                                  data={'shipments': shipment_ids})
    
    def buy(self, batch_id: str) -> Dict:
        """Purchase all labels in batch"""
        return self.client.request('POST', f"{self.base_path}/{batch_id}/buy")
    
    def scan_form(self, batch_id: str) -> Dict:
        """Generate SCAN form for batch"""
        return self.client.request('POST', f"{self.base_path}/{batch_id}/scan_form")


class InsuranceResource(Resource):
    """Insurance management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/insurances'
    
    def claim(self, insurance_id: str, data: Dict) -> Dict:
        """File insurance claim"""
        return self.client.request('POST', f"{self.base_path}/{insurance_id}/claim", data=data)


class TrackingResource(Resource):
    """Shipment tracking"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/trackers'
    
    def track(self, tracking_code: str, carrier: str = None) -> Dict:
        """Track a shipment"""
        data = {'tracking_code': tracking_code}
        if carrier:
            data['carrier'] = carrier
        return self.create(data)


class WebhookResource(Resource):
    """Webhook management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/webhooks'
    
    def test(self, webhook_id: str) -> Dict:
        """Test webhook endpoint"""
        return self.client.request('POST', f"{self.base_path}/{webhook_id}/test")


class ReportResource(Resource):
    """Report generation"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/reports'
    
    def download(self, report_id: str) -> Dict:
        """Download report"""
        return self.client.request('GET', f"{self.base_path}/{report_id}/download")


class OrderResource(Resource):
    """Order management"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/orders'
    
    def create_shipment(self, order_id: str, data: Dict = None) -> Dict:
        """Create shipment from order"""
        return self.client.request('POST', f"{self.base_path}/{order_id}/create_shipment",
                                  data=data or {})


class ChannelResource(Resource):
    """E-commerce channel integration"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/channels'
    
    def sync(self, channel_id: str, options: Dict = None) -> Dict:
        """Sync channel data"""
        return self.client.request('POST', f"{self.base_path}/{channel_id}/sync",
                                  data=options or {})


class PickupResource(Resource):
    """Pickup scheduling"""
    
    def __init__(self, client: AtoshipClient):
        super().__init__(client)
        self.base_path = '/pickups'
    
    def cancel(self, pickup_id: str) -> Dict:
        """Cancel pickup"""
        return self.delete(pickup_id)