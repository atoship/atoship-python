#!/usr/bin/env python3
"""
Batch operations example for atoship Python SDK

This example demonstrates:
- Creating multiple orders in batch
- Tracking multiple packages at once
- Processing results and handling errors
"""

import os
import time
from atoship import atoshipSDK
from atoship.exceptions import ValidationError


def main():
    """Run batch operations examples"""
    
    api_key = os.getenv('ATOSHIP_API_KEY')
    if not api_key:
        print("Please set ATOSHIP_API_KEY environment variable")
        return
    
    # Create SDK instance
    sdk = atoshipSDK(api_key=api_key, debug=False)
    
    print("📦 atoship Python SDK - Batch Operations Example\n")
    
    try:
        # 1. Create multiple orders in batch
        print("1. Creating multiple orders in batch...")
        
        # Prepare batch order data
        orders = []
        for i in range(5):
            order_data = {
                "orderNumber": f"BATCH-{i+1:03d}",
                "recipientName": f"Customer {i+1}",
                "recipientStreet1": f"{100 + i} Main Street",
                "recipientCity": "San Francisco",
                "recipientState": "CA",
                "recipientPostalCode": "94105",
                "recipientCountry": "US",
                "recipientPhone": f"415-555-{1000 + i:04d}",
                "recipientEmail": f"customer{i+1}@example.com",
                "items": [
                    {
                        "name": f"Product {i+1}",
                        "sku": f"PROD-{i+1:03d}",
                        "quantity": 1 + (i % 3),  # Vary quantity
                        "unitPrice": 19.99 + (i * 5),  # Vary price
                        "weight": 1.0 + (i * 0.2),  # Vary weight
                        "weightUnit": "lb"
                    }
                ],
                "notes": f"Batch order {i+1}",
                "tags": ["batch", f"group-{(i // 2) + 1}"]
            }
            orders.append(order_data)
        
        print(f"   Preparing {len(orders)} orders for batch creation...")
        
        response = sdk.create_orders_batch(orders)
        if response.success:
            successful = response.data.get('successful', [])
            failed = response.data.get('failed', [])
            
            print(f"✅ Batch creation completed:")
            print(f"   Successful: {len(successful)}")
            print(f"   Failed: {len(failed)}")
            
            if successful:
                print("   Successful orders:")
                for order in successful:
                    print(f"     • {order['orderNumber']}: {order['id']}")
            
            if failed:
                print("   Failed orders:")
                for failure in failed:
                    print(f"     • {failure['orderNumber']}: {failure['error']}")
        else:
            print(f"❌ Batch creation failed: {response.error}")
            return
        
        # 2. List and process orders
        print("\n2. Listing recent orders...")
        
        response = sdk.list_orders(page=1, limit=10, source="API")
        if response.success:
            orders_data = response.data
            items = orders_data.get('items', [])
            total = orders_data.get('total', 0)
            
            print(f"✅ Found {len(items)} recent orders (total: {total}):")
            
            for order in items[:5]:  # Show first 5
                status = order.get('status', 'Unknown')
                order_number = order.get('orderNumber', 'N/A')
                items_count = len(order.get('items', []))
                print(f"   • {order_number}: {status} ({items_count} items)")
        else:
            print(f"❌ Failed to list orders: {response.error}")
        
        # 3. Track multiple packages (demo with sample tracking numbers)
        print("\n3. Tracking multiple packages...")
        
        # Sample tracking numbers for demo
        tracking_numbers = [
            "1Z999AA1234567890",  # UPS
            "9400111206213123456789",  # USPS
            "1234567890",  # FedEx
            "1Z999BB9876543210",  # UPS
            "9400222317224234567890"  # USPS
        ]
        
        print(f"   Tracking {len(tracking_numbers)} packages...")
        
        response = sdk.track_multiple(tracking_numbers)
        if response.success:
            results = response.data.get('results', [])
            print(f"✅ Tracking results for {len(results)} packages:")
            
            for result in results:
                tracking_num = result.get('trackingNumber', 'Unknown')
                status = result.get('status', 'Unknown')
                carrier = result.get('carrier', 'Unknown')
                events_count = len(result.get('events', []))
                
                print(f"   • {tracking_num}: {status} ({carrier}, {events_count} events)")
                
                # Show latest event if available
                events = result.get('events', [])
                if events:
                    latest = events[-1]
                    print(f"     Latest: {latest.get('description', 'N/A')} ({latest.get('timestamp', 'N/A')})")
        else:
            print(f"❌ Failed to track packages: {response.error}")
        
        # 4. Address book operations
        print("\n4. Managing address book...")
        
        # Create sample addresses
        addresses = [
            {
                "type": "SHIPPING",
                "name": "West Coast Warehouse",
                "company": "atoship Logistics",
                "street1": "123 Warehouse Drive",
                "city": "San Francisco",
                "state": "CA",
                "postalCode": "94105",
                "country": "US",
                "phone": "415-555-0100",
                "isDefault": True
            },
            {
                "type": "SHIPPING",
                "name": "East Coast Distribution",
                "company": "atoship Logistics",
                "street1": "456 Distribution Way",
                "city": "New York",
                "state": "NY",
                "postalCode": "10001",
                "country": "US",
                "phone": "212-555-0200"
            }
        ]
        
        saved_addresses = []
        for addr in addresses:
            response = sdk.save_address(addr)
            if response.success:
                saved_addresses.append(response.data)
                print(f"   ✅ Saved address: {addr['name']}")
            else:
                print(f"   ❌ Failed to save address {addr['name']}: {response.error}")
        
        # List all addresses
        response = sdk.list_addresses()
        if response.success:
            all_addresses = response.data.get('items', [])
            print(f"   📍 Total addresses in book: {len(all_addresses)}")
        
        # 5. Performance monitoring
        print("\n5. Monitoring API performance...")
        
        start_time = time.time()
        
        # Make several API calls to demonstrate performance
        operations = [
            ("Health Check", lambda: sdk.health_check()),
            ("Get Profile", lambda: sdk.get_profile()),
            ("List Carriers", lambda: sdk.list_carriers()),
            ("Get Usage", lambda: sdk.get_usage())
        ]
        
        results = []
        for name, operation in operations:
            op_start = time.time()
            try:
                response = operation()
                op_time = time.time() - op_start
                status = "✅ Success" if response.success else "❌ Failed"
                results.append((name, status, op_time))
            except Exception as e:
                op_time = time.time() - op_start
                results.append((name, f"❌ Error: {str(e)[:50]}", op_time))
        
        total_time = time.time() - start_time
        
        print(f"   Performance results (total: {total_time:.2f}s):")
        for name, status, duration in results:
            print(f"     • {name}: {status} ({duration:.2f}s)")
        
        print("\n🎉 Batch operations example completed successfully!")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    finally:
        sdk.close()


if __name__ == "__main__":
    main()