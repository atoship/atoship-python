#!/usr/bin/env python3
"""
atoship Python SDK - Basic Example

This example demonstrates basic usage of the atoship Python SDK including:
- SDK initialization and configuration
- Creating orders with detailed item information
- Getting shipping rates from multiple carriers
- Purchasing shipping labels
- Package tracking and status monitoring
- Address validation
- Comprehensive error handling
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from atoship import atoshipSDK, atoshipConfig
from atoship.models import Order, ShippingRate, ShippingLabel, TrackingInfo
from atoship.exceptions import (
    atoshipException,
    ValidationException,
    AuthenticationException,
    RateLimitException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atoship_basic_example.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BasicShippingExample:
    """Basic shipping operations example using atoship SDK."""
    
    def __init__(self):
        """Initialize the SDK with configuration."""
        self.config = atoshipConfig(
            api_key=os.getenv('ATOSHIP_API_KEY', 'your-api-key-here'),
            base_url=os.getenv('ATOSHIP_BASE_URL', 'https://api.atoship.com'),
            timeout=30.0,
            max_retries=3,
            debug=os.getenv('NODE_ENV') == 'development'
        )
        
        self.sdk = atoshipSDK(self.config)
        
        # Statistics tracking
        self.stats = {
            'orders_created': 0,
            'labels_purchased': 0,
            'total_cost': 0.0,
            'start_time': datetime.now()
        }

    async def run_example(self) -> None:
        """Run the complete basic example workflow."""
        print("🚀 atoship Python SDK Basic Example\n")
        
        try:
            # Step 1: Create an order
            order = await self.create_sample_order()
            if not order:
                return
            
            # Step 2: Get shipping rates
            rates = await self.get_shipping_rates(order)
            if not rates:
                return
            
            # Step 3: Purchase shipping label
            label = await self.purchase_shipping_label(order, rates[0])
            if not label:
                return
            
            # Step 4: Track the package
            await self.track_package(label.tracking_number)
            
            # Step 5: Demonstrate additional features
            await self.demonstrate_additional_features(order.id)
            
            # Step 6: Show summary
            self.show_summary()
            
            print("🎉 Basic example completed successfully!")
            
        except atoshipException as e:
            logger.error(f"atoship SDK error: {e}")
            print(f"❌ SDK Error: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"💥 Unexpected error: {e}")

    async def create_sample_order(self) -> Optional[Order]:
        """Create a sample order with detailed information."""
        print("📦 Step 1: Creating an order...")
        
        order_data = {
            'order_number': f'PY-ORDER-{int(datetime.now().timestamp())}',
            'recipient_name': 'Alice Johnson',
            'recipient_email': 'alice@example.com',
            'recipient_phone': '555-123-4567',
            'recipient_street1': '789 Python Street',
            'recipient_street2': 'Suite 200',
            'recipient_city': 'San Francisco',
            'recipient_state': 'CA',
            'recipient_postal_code': '94105',
            'recipient_country': 'US',
            'sender_name': 'Python Store',
            'sender_street1': '123 Developer Avenue',
            'sender_city': 'Los Angeles',
            'sender_state': 'CA',
            'sender_postal_code': '90001',
            'sender_country': 'US',
            'items': [
                {
                    'name': 'Python Programming Book',
                    'sku': 'BOOK-PY-001',
                    'quantity': 1,
                    'unit_price': 59.99,
                    'weight': 1.2,
                    'weight_unit': 'lb',
                    'dimensions': {
                        'length': 9.0,
                        'width': 7.0,
                        'height': 1.5,
                        'unit': 'in'
                    }
                },
                {
                    'name': 'Coding Stickers Pack',
                    'sku': 'STICKERS-001',
                    'quantity': 3,
                    'unit_price': 9.99,
                    'weight': 0.1,
                    'weight_unit': 'lb',
                    'dimensions': {
                        'length': 4.0,
                        'width': 4.0,
                        'height': 0.1,
                        'unit': 'in'
                    }
                }
            ],
            'notes': 'Educational materials - developer-friendly packaging',
            'tags': ['books', 'education', 'python', 'programming'],
            'custom_fields': {
                'customer_type': 'developer',
                'order_source': 'python-sdk-example',
                'priority': 'standard',
                'language': 'python'
            }
        }
        
        try:
            response = await self.sdk.create_order(order_data)
            
            if response.success:
                order = response.data
                self.stats['orders_created'] += 1
                
                print("✅ Order created successfully!")
                print(f"   Order ID: {order.id}")
                print(f"   Order Number: {order.order_number}")
                print(f"   Status: {order.status}")
                print(f"   Total Value: ${order.total_value:.2f}")
                print(f"   Items Count: {len(order.items)}\n")
                
                return order
            else:
                print(f"❌ Failed to create order: {response.error}")
                return None
                
        except ValidationException as e:
            print(f"❌ Validation error: {e}")
            if hasattr(e, 'details') and e.details:
                print("   Validation details:")
                for field, messages in e.details.items():
                    print(f"     {field}: {', '.join(messages)}")
            return None

    async def get_shipping_rates(self, order: Order) -> Optional[List[ShippingRate]]:
        """Get shipping rates for the order."""
        print("💰 Step 2: Getting shipping rates...")
        
        # Calculate total weight from order items
        total_weight = sum(
            item.weight * item.quantity 
            for item in order.items
        )
        
        rate_request = {
            'from_address': {
                'street1': order.sender_street1,
                'city': order.sender_city,
                'state': order.sender_state,
                'postal_code': order.sender_postal_code,
                'country': order.sender_country
            },
            'to_address': {
                'street1': order.recipient_street1,
                'street2': order.recipient_street2,
                'city': order.recipient_city,
                'state': order.recipient_state,
                'postal_code': order.recipient_postal_code,
                'country': order.recipient_country
            },
            'package': {
                'weight': max(total_weight, 1.0),  # Minimum 1 lb
                'length': 12.0,
                'width': 9.0,
                'height': 6.0,
                'weight_unit': 'lb',
                'dimension_unit': 'in'
            },
            'options': {
                'signature': False,
                'insurance': True,
                'insurance_value': order.total_value,
                'saturday_delivery': False,
                'residential': True
            }
        }
        
        try:
            response = await self.sdk.get_rates(rate_request)
            
            if response.success:
                rates = response.data
                print("✅ Shipping rates retrieved successfully!")
                
                for i, rate in enumerate(rates, 1):
                    print(f"   {i}. {rate.carrier} {rate.service_name}")
                    print(f"      Price: ${rate.amount:.2f}")
                    print(f"      Estimated Days: {rate.estimated_days}")
                    print(f"      Delivery Date: {rate.estimated_delivery_date or 'N/A'}")
                    if hasattr(rate, 'zone'):
                        print(f"      Zone: {rate.zone or 'N/A'}")
                
                print()
                return rates
            else:
                print(f"❌ Failed to get rates: {response.error}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting rates: {e}")
            return None

    async def purchase_shipping_label(self, order: Order, selected_rate: ShippingRate) -> Optional[ShippingLabel]:
        """Purchase a shipping label for the order."""
        print("🏷️  Step 3: Purchasing shipping label...")
        print(f"📋 Selected Rate: {selected_rate.carrier} {selected_rate.service_name} - ${selected_rate.amount:.2f}\n")
        
        label_request = {
            'order_id': order.id,
            'rate_id': selected_rate.id,
            'from_address': {
                'name': order.sender_name,
                'street1': order.sender_street1,
                'city': order.sender_city,
                'state': order.sender_state,
                'postal_code': order.sender_postal_code,
                'country': order.sender_country
            },
            'to_address': {
                'name': order.recipient_name,
                'email': order.recipient_email,
                'phone': order.recipient_phone,
                'street1': order.recipient_street1,
                'street2': order.recipient_street2,
                'city': order.recipient_city,
                'state': order.recipient_state,
                'postal_code': order.recipient_postal_code,
                'country': order.recipient_country
            },
            'package': {
                'weight': sum(item.weight * item.quantity for item in order.items),
                'length': 12.0,
                'width': 9.0,
                'height': 6.0,
                'weight_unit': 'lb',
                'dimension_unit': 'in'
            },
            'options': {
                'label_format': 'PDF',
                'label_size': '4x6',
                'signature': False,
                'insurance': True,
                'insurance_value': order.total_value,
                'packaging': 'package',
                'references': {
                    'reference1': order.order_number,
                    'reference2': f'PY-{int(datetime.now().timestamp())}'
                }
            }
        }
        
        try:
            response = await self.sdk.purchase_label(label_request)
            
            if response.success:
                label = response.data
                self.stats['labels_purchased'] += 1
                self.stats['total_cost'] += label.cost
                
                print("✅ Shipping label purchased successfully!")
                print(f"   Label ID: {label.id}")
                print(f"   Tracking Number: {label.tracking_number}")
                print(f"   Carrier: {label.carrier}")
                print(f"   Service: {label.service_name}")
                print(f"   Cost: ${label.cost:.2f}")
                print(f"   Label URL: {label.label_url}")
                if hasattr(label, 'void_url') and label.void_url:
                    print(f"   Void URL: {label.void_url}")
                print()
                
                return label
            else:
                print(f"❌ Failed to purchase label: {response.error}")
                return None
                
        except Exception as e:
            print(f"❌ Error purchasing label: {e}")
            return None

    async def track_package(self, tracking_number: str) -> None:
        """Track a package by tracking number."""
        print("📍 Step 4: Tracking the package...")
        
        try:
            response = await self.sdk.track_package(tracking_number)
            
            if response.success:
                tracking = response.data
                print("✅ Package tracking information retrieved!")
                print(f"   Status: {tracking.status}")
                print(f"   Carrier: {tracking.carrier}")
                if hasattr(tracking, 'service_name') and tracking.service_name:
                    print(f"   Service: {tracking.service_name}")
                print(f"   Last Updated: {tracking.last_update}")
                if hasattr(tracking, 'estimated_delivery') and tracking.estimated_delivery:
                    print(f"   Estimated Delivery: {tracking.estimated_delivery}")
                if hasattr(tracking, 'current_location') and tracking.current_location:
                    print(f"   Current Location: {tracking.current_location}")
                
                if tracking.events:
                    print("   Tracking Events:")
                    for i, event in enumerate(tracking.events, 1):
                        print(f"     {i}. {event.timestamp}: {event.description}")
                        if hasattr(event, 'location') and event.location:
                            print(f"        Location: {event.location}")
                        if hasattr(event, 'status_code') and event.status_code:
                            print(f"        Status Code: {event.status_code}")
                
                print()
            else:
                print(f"❌ Failed to track package: {response.error}")
                
        except Exception as e:
            print(f"❌ Error tracking package: {e}")

    async def demonstrate_additional_features(self, order_id: str) -> None:
        """Demonstrate additional SDK features."""
        print("🔧 Step 5: Demonstrating additional features...")
        
        # Address validation
        await self.validate_address()
        
        # Batch tracking
        await self.batch_tracking_demo()
        
        # Account metrics
        await self.get_account_metrics()
        
        # Order retrieval
        await self.get_order_details(order_id)

    async def validate_address(self) -> None:
        """Demonstrate address validation."""
        print("🏠 Address validation example...")
        
        address_data = {
            'street1': '123 Main St',
            'city': 'San Francisco',
            'state': 'CA',
            'postal_code': '94105',
            'country': 'US'
        }
        
        try:
            response = await self.sdk.validate_address(address_data)
            
            if response.success:
                validation = response.data
                print(f"✅ Address validation completed!")
                print(f"   Valid: {validation.get('is_valid', False)}")
                if validation.get('suggestions'):
                    print("   Suggestions available for improved accuracy")
                print()
            else:
                print(f"❌ Address validation failed: {response.error}")
                
        except Exception as e:
            print(f"❌ Error validating address: {e}")

    async def batch_tracking_demo(self) -> None:
        """Demonstrate batch tracking functionality."""
        print("📦 Batch tracking demonstration...")
        
        sample_tracking_numbers = [
            '1Z999AA1234567890',
            '9400111206213123456789',
            '123456789012'
        ]
        
        try:
            response = await self.sdk.track_multiple(sample_tracking_numbers)
            
            if response.success:
                print("✅ Batch tracking completed!")
                for i, result in enumerate(response.data, 1):
                    status = result.get('status', 'Unknown')
                    tracking_num = result.get('tracking_number', 'N/A')
                    print(f"   {i}. {tracking_num}: {status}")
                print()
            else:
                print(f"❌ Batch tracking failed: {response.error}")
                
        except Exception as e:
            print(f"❌ Error in batch tracking: {e}")

    async def get_account_metrics(self) -> None:
        """Get and display account metrics."""
        print("📊 Account metrics...")
        
        try:
            response = await self.sdk.get_account_metrics()
            
            if response.success:
                metrics = response.data
                print("✅ Account metrics retrieved!")
                print(f"   Orders This Month: {metrics.get('orders_this_month', 0)}")
                print(f"   Labels This Month: {metrics.get('labels_this_month', 0)}")
                print(f"   Total Spent: ${metrics.get('total_spent', 0.0):.2f}")
                print(f"   API Calls Today: {metrics.get('api_calls_today', 0)}")
                print()
            else:
                print(f"❌ Failed to get metrics: {response.error}")
                
        except Exception as e:
            print(f"❌ Error getting metrics: {e}")

    async def get_order_details(self, order_id: str) -> None:
        """Retrieve and display order details."""
        print("📋 Retrieving order details...")
        
        try:
            response = await self.sdk.get_order(order_id)
            
            if response.success:
                order = response.data
                print("✅ Order details retrieved!")
                print(f"   Order Status: {order.status}")
                if hasattr(order, 'shipping_status'):
                    print(f"   Shipping Status: {order.shipping_status or 'N/A'}")
                if hasattr(order, 'labels_count'):
                    print(f"   Labels Count: {order.labels_count or 0}")
                if hasattr(order, 'total_cost'):
                    print(f"   Total Cost: ${order.total_cost or 0.0:.2f}")
                print()
            else:
                print(f"❌ Failed to get order: {response.error}")
                
        except Exception as e:
            print(f"❌ Error getting order: {e}")

    def show_summary(self) -> None:
        """Display example execution summary."""
        duration = datetime.now() - self.stats['start_time']
        
        print("📊 Example Summary:")
        print(f"   Orders Created: {self.stats['orders_created']}")
        print(f"   Labels Purchased: {self.stats['labels_purchased']}")
        print(f"   Total Cost: ${self.stats['total_cost']:.2f}")
        print(f"   Execution Time: {duration.total_seconds():.1f} seconds")
        print()


async def main():
    """Main execution function."""
    # Check for required environment variables
    if not os.getenv('ATOSHIP_API_KEY'):
        print("❌ Error: ATOSHIP_API_KEY environment variable is required")
        print("   Please set your API key:")
        print("   export ATOSHIP_API_KEY='your-api-key-here'")
        return
    
    # Create and run the example
    example = BasicShippingExample()
    await example.run_example()


if __name__ == "__main__":
    # Handle command line arguments
    import sys
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
atoship Python SDK Basic Example

Usage:
    python basic_example.py         # Run the basic example
    python basic_example.py --help  # Show this help

Environment Variables:
    ATOSHIP_API_KEY     # Required: Your atoship API key
    ATOSHIP_BASE_URL    # Optional: API base URL (default: https://api.atoship.com)
    NODE_ENV            # Optional: Environment (development/production)

Features Demonstrated:
    - SDK initialization and configuration
    - Creating orders with detailed information
    - Getting shipping rates from multiple carriers
    - Purchasing shipping labels
    - Package tracking and monitoring
    - Address validation
    - Batch operations
    - Account metrics and reporting
    - Comprehensive error handling

Requirements:
    - Python 3.8 or higher
    - atoship-sdk package
    - Valid atoship API key
        """)
        sys.exit(0)
    
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Example interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
        sys.exit(1)