#!/usr/bin/env python3
"""
Basic usage example for atoship Python SDK

This example demonstrates the most common operations:
- Creating an order
- Getting shipping rates
- Purchasing a label
- Tracking a package
"""

import os
from atoship import atoshipSDK
from atoship.exceptions import ValidationError, AuthenticationError


def main():
    """Run basic SDK usage examples"""
    
    # Initialize SDK with API key from environment
    api_key = os.getenv('ATOSHIP_API_KEY')
    if not api_key:
        print("Please set ATOSHIP_API_KEY environment variable")
        return
    
    # Create SDK instance
    sdk = atoshipSDK(
        api_key=api_key,
        debug=True  # Enable debug logging to see requests/responses
    )
    
    print("🚀 atoship Python SDK - Basic Usage Example\n")
    
    try:
        # 1. Create an order
        print("1. Creating an order...")
        order_data = {
            "orderNumber": "EXAMPLE-001",
            "recipientName": "John Doe",
            "recipientCompany": "Acme Corp",
            "recipientStreet1": "123 Main Street",
            "recipientStreet2": "Suite 100",
            "recipientCity": "San Francisco",
            "recipientState": "CA",
            "recipientPostalCode": "94105",
            "recipientCountry": "US",
            "recipientPhone": "415-555-0123",
            "recipientEmail": "john.doe@acme.com",
            "items": [
                {
                    "name": "Wireless Headphones",
                    "sku": "WH-001",
                    "quantity": 1,
                    "unitPrice": 99.99,
                    "weight": 1.2,
                    "weightUnit": "lb",
                    "description": "Premium wireless noise-canceling headphones"
                },
                {
                    "name": "Phone Case",
                    "sku": "PC-002",
                    "quantity": 2,
                    "unitPrice": 19.99,
                    "weight": 0.3,
                    "weightUnit": "lb",
                    "description": "Protective phone case with screen protector"
                }
            ],
            "notes": "Handle with care - electronics",
            "tags": ["electronics", "fragile"]
        }
        
        response = sdk.create_order(order_data)
        if response.success:
            order_id = response.data['id']
            print(f"✅ Order created successfully: {order_id}")
        else:
            print(f"❌ Failed to create order: {response.error}")
            return
        
        # 2. Get shipping rates
        print("\n2. Getting shipping rates...")
        rate_request = {
            "fromAddress": {
                "name": "atoship Warehouse",
                "company": "atoship Inc.",
                "street1": "123 Warehouse Street",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US",
                "type": "SHIPPING"
            },
            "toAddress": {
                "name": "John Doe",
                "company": "Acme Corp",
                "street1": "123 Main Street",
                "street2": "Suite 100",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US",
                "type": "SHIPPING"
            },
            "package": {
                "weight": 1.8,  # Total weight from items
                "length": 12,
                "width": 8,
                "height": 4,
                "weightUnit": "lb",
                "dimensionUnit": "in"
            },
            "options": {
                "signature": False,
                "insurance": True,
                "insuranceValue": 139.97
            }
        }
        
        response = sdk.get_rates(rate_request)
        if response.success:
            rates = response.data
            print(f"✅ Found {len(rates)} shipping rates:")
            
            for rate in rates[:3]:  # Show first 3 rates
                print(f"   • {rate['carrier']} {rate['serviceName']}: ${rate['amount']:.2f} ({rate['estimatedDays']} days)")
            
            # Use the first rate for label purchase
            if rates:
                selected_rate = rates[0]
                rate_id = selected_rate['id']
            else:
                print("❌ No shipping rates available")
                return
        else:
            print(f"❌ Failed to get rates: {response.error}")
            return
        
        # 3. Purchase a shipping label
        print("\n3. Purchasing shipping label...")
        label_request = {
            "orderId": order_id,
            "rateId": rate_id,
            "fromAddress": rate_request["fromAddress"],
            "toAddress": rate_request["toAddress"],
            "package": rate_request["package"],
            "options": rate_request.get("options", {})
        }
        
        response = sdk.purchase_label(label_request)
        if response.success:
            label = response.data
            tracking_number = label['trackingNumber']
            label_url = label['labelUrl']
            print(f"✅ Label purchased successfully!")
            print(f"   Tracking Number: {tracking_number}")
            print(f"   Label URL: {label_url}")
            print(f"   Cost: ${label['cost']:.2f}")
        else:
            print(f"❌ Failed to purchase label: {response.error}")
            return
        
        # 4. Track the package
        print("\n4. Tracking the package...")
        response = sdk.track_package(tracking_number)
        if response.success:
            tracking = response.data
            print(f"✅ Package tracking information:")
            print(f"   Status: {tracking['status']}")
            print(f"   Carrier: {tracking['carrier']}")
            print(f"   Events: {len(tracking.get('events', []))}")
            
            # Show recent events
            events = tracking.get('events', [])
            if events:
                print("   Recent events:")
                for event in events[-3:]:  # Show last 3 events
                    print(f"     • {event['timestamp']}: {event['description']}")
        else:
            print(f"❌ Failed to track package: {response.error}")
        
        # 5. Get account usage
        print("\n5. Checking account usage...")
        response = sdk.get_usage()
        if response.success:
            usage = response.data
            print(f"✅ Account usage:")
            print(f"   Labels used: {usage.get('labelsUsed', 0)}")
            print(f"   API requests: {usage.get('apiRequestsUsed', 0)}")
        else:
            print(f"❌ Failed to get usage: {response.error}")
        
        print("\n🎉 Basic usage example completed successfully!")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
        if e.details:
            print(f"   Details: {e.details}")
    except AuthenticationError as e:
        print(f"❌ Authentication Error: {e.message}")
        print("   Please check your API key")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    finally:
        # Close SDK to clean up resources
        sdk.close()


if __name__ == "__main__":
    main()