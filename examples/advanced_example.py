#!/usr/bin/env python3
"""
atoship Python SDK - Advanced Example

This example demonstrates advanced features including:
- Async batch processing with concurrency control
- CSV import/export functionality
- Rate optimization strategies
- Webhook server integration
- Performance monitoring and analytics
- Retry logic and error recovery
- Data persistence and caching
- Real-time shipment monitoring
"""

import os
import csv
import json
import asyncio
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from atoship import atoshipSDK, atoshipConfig
from atoship.models import Order, ShippingRate, ShippingLabel, TrackingInfo
from atoship.exceptions import atoshipException, RateLimitException

# Third-party imports for advanced features
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atoship_advanced_example.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Data class for tracking processing results."""
    order_number: str
    success: bool
    order_id: Optional[str] = None
    selected_rate: Optional[Dict[str, Any]] = None
    label_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    retry_count: int = 0


@dataclass
class BatchStatistics:
    """Data class for batch processing statistics."""
    total_orders: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    total_cost: float = 0.0
    average_cost: float = 0.0
    processing_time: float = 0.0
    carrier_breakdown: Dict[str, int] = None
    
    def __post_init__(self):
        if self.carrier_breakdown is None:
            self.carrier_breakdown = {}


class AdvancedShippingProcessor:
    """Advanced shipping processor with comprehensive features."""
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize the advanced processor."""
        self.config = atoshipConfig(
            api_key=os.getenv('ATOSHIP_API_KEY', 'your-api-key-here'),
            base_url=os.getenv('ATOSHIP_BASE_URL', 'https://api.atoship.com'),
            timeout=30.0,
            max_retries=3,
            debug=os.getenv('NODE_ENV') == 'development'
        )
        
        self.sdk = atoshipSDK(self.config)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Results storage
        self.results: List[ProcessingResult] = []
        self.statistics = BatchStatistics()
        
        # Create output directories
        self.setup_directories()

    def setup_directories(self) -> None:
        """Create necessary output directories."""
        directories = ['output', 'reports', 'logs', 'cache']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    async def process_csv_orders(self, csv_file_path: str, 
                               strategy: str = 'balanced',
                               max_concurrent: int = None) -> BatchStatistics:
        """Process orders from CSV file with advanced options."""
        print(f"🚀 Starting advanced batch processing from {csv_file_path}")
        start_time = datetime.now()
        
        if max_concurrent:
            self.semaphore = asyncio.Semaphore(max_concurrent)
        
        try:
            # Read and validate CSV data
            orders_data = await self.read_csv_orders(csv_file_path)
            print(f"📊 Loaded {len(orders_data)} orders from CSV")
            
            # Process orders with concurrency control
            await self.process_orders_concurrent(orders_data, strategy)
            
            # Generate comprehensive reports
            processing_time = (datetime.now() - start_time).total_seconds()
            self.statistics.processing_time = processing_time
            
            await self.generate_comprehensive_report()
            await self.export_results_to_csv()
            
            if HAS_PANDAS:
                await self.generate_pandas_analytics()
            
            print("✅ Advanced batch processing completed successfully!")
            return self.statistics
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise

    async def read_csv_orders(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Read and validate orders from CSV file."""
        orders = []
        
        async with aiofiles.open(csv_file_path, mode='r', encoding='utf-8') as file:
            content = await file.read()
            
        # Parse CSV using standard library
        csv_reader = csv.DictReader(content.splitlines())
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                order = self.transform_csv_row_to_order(row)
                if order:
                    orders.append(order)
                else:
                    logger.warning(f"Skipped invalid row {row_num}")
            except Exception as e:
                logger.error(f"Error processing row {row_num}: {e}")
        
        return orders

    def transform_csv_row_to_order(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Transform CSV row to order object with validation."""
        try:
            # Validate required fields
            required_fields = ['recipient_name', 'recipient_address1', 'recipient_city', 
                             'recipient_state', 'recipient_postal_code']
            
            for field in required_fields:
                if not row.get(field, '').strip():
                    logger.warning(f"Missing required field: {field}")
                    return None
            
            return {
                'order_number': row.get('order_number') or f'ADV-{datetime.now().timestamp():.0f}',
                'recipient_name': row['recipient_name'].strip(),
                'recipient_email': row.get('recipient_email', '').strip(),
                'recipient_phone': row.get('recipient_phone', '').strip(),
                'recipient_street1': row['recipient_address1'].strip(),
                'recipient_street2': row.get('recipient_address2', '').strip(),
                'recipient_city': row['recipient_city'].strip(),
                'recipient_state': row['recipient_state'].strip(),
                'recipient_postal_code': row['recipient_postal_code'].strip(),
                'recipient_country': row.get('recipient_country', 'US').strip(),
                'sender_name': row.get('sender_name', 'Advanced Store').strip(),
                'sender_street1': row.get('sender_address1', '456 Warehouse St').strip(),
                'sender_city': row.get('sender_city', 'Los Angeles').strip(),
                'sender_state': row.get('sender_state', 'CA').strip(),
                'sender_postal_code': row.get('sender_postal_code', '90001').strip(),
                'sender_country': row.get('sender_country', 'US').strip(),
                'items': [
                    {
                        'name': row.get('item_name', 'Default Item').strip(),
                        'sku': row.get('item_sku', 'DEFAULT-SKU').strip(),
                        'quantity': max(1, int(row.get('item_quantity', 1))),
                        'unit_price': max(0.0, float(row.get('item_price', 0))),
                        'weight': max(0.1, float(row.get('item_weight', 1))),
                        'weight_unit': row.get('item_weight_unit', 'lb').strip()
                    }
                ],
                'shipping_strategy': row.get('shipping_strategy', 'balanced').strip().lower(),
                'notes': row.get('notes', '').strip(),
                'tags': [tag.strip() for tag in row.get('tags', '').split(',') if tag.strip()],
                'priority': row.get('priority', 'standard').strip().lower()
            }
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error transforming CSV row: {e}")
            return None

    async def process_orders_concurrent(self, orders_data: List[Dict[str, Any]], 
                                      strategy: str) -> None:
        """Process orders with controlled concurrency."""
        self.statistics.total_orders = len(orders_data)
        
        # Create semaphore for concurrency control
        tasks = []
        
        for order_data in orders_data:
            task = self.process_single_order_with_semaphore(order_data, strategy)
            tasks.append(task)
        
        # Process all orders with progress reporting
        completed = 0
        batch_size = 10
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            completed += len(batch)
            progress = (completed / len(tasks)) * 100
            print(f"🔄 Progress: {completed}/{len(tasks)} orders ({progress:.1f}%)")
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                    self.statistics.failed_orders += 1
                elif result:
                    self.results.append(result)
                    if result.success:
                        self.statistics.successful_orders += 1
                        if result.label_info:
                            self.statistics.total_cost += result.label_info.get('cost', 0)
                    else:
                        self.statistics.failed_orders += 1

        # Calculate averages
        if self.statistics.successful_orders > 0:
            self.statistics.average_cost = self.statistics.total_cost / self.statistics.successful_orders

    async def process_single_order_with_semaphore(self, order_data: Dict[str, Any], 
                                                strategy: str) -> ProcessingResult:
        """Process a single order with semaphore-controlled concurrency."""
        async with self.semaphore:
            return await self.process_single_order_advanced(order_data, strategy)

    async def process_single_order_advanced(self, order_data: Dict[str, Any], 
                                          strategy: str, 
                                          max_retries: int = 3) -> ProcessingResult:
        """Process a single order with advanced features and retry logic."""
        start_time = datetime.now()
        order_number = order_data['order_number']
        
        result = ProcessingResult(order_number=order_number, success=False)
        
        for attempt in range(max_retries + 1):
            try:
                result.retry_count = attempt
                
                # Step 1: Create order
                order_response = await self.sdk.create_order(order_data)
                if not order_response.success:
                    raise Exception(f"Order creation failed: {order_response.error}")
                
                result.order_id = order_response.data.id
                
                # Step 2: Get optimized rates
                rates = await self.get_optimized_rates_with_fallback(order_data)
                if not rates:
                    raise Exception("No shipping rates available")
                
                # Step 3: Select optimal rate
                selected_rate = self.select_rate_by_strategy(rates, strategy, order_data)
                result.selected_rate = {
                    'carrier': selected_rate.carrier,
                    'service': selected_rate.service_name,
                    'cost': selected_rate.amount,
                    'estimated_days': selected_rate.estimated_days
                }
                
                # Step 4: Purchase label with retry
                label_response = await self.purchase_label_with_retry(
                    result.order_id, selected_rate, order_data
                )
                
                if label_response.success:
                    result.label_info = {
                        'label_id': label_response.data.id,
                        'tracking_number': label_response.data.tracking_number,
                        'cost': label_response.data.cost,
                        'label_url': label_response.data.label_url
                    }
                
                result.success = True
                result.processing_time = (datetime.now() - start_time).total_seconds()
                
                # Track carrier usage
                carrier = selected_rate.carrier
                if carrier not in self.statistics.carrier_breakdown:
                    self.statistics.carrier_breakdown[carrier] = 0
                self.statistics.carrier_breakdown[carrier] += 1
                
                return result
                
            except RateLimitException as e:
                logger.warning(f"Rate limit hit for {order_number}, waiting...")
                await asyncio.sleep(min(60, 2 ** attempt))  # Exponential backoff
                continue
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed for {order_number}: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    result.error = str(e)
                    result.processing_time = (datetime.now() - start_time).total_seconds()
                    logger.error(f"All attempts failed for {order_number}: {e}")
                    break
        
        return result

    async def get_optimized_rates_with_fallback(self, order_data: Dict[str, Any]) -> List[ShippingRate]:
        """Get rates with intelligent fallback strategies."""
        rate_request = self.build_rate_request(order_data)
        
        # Primary: Get all rates
        try:
            response = await self.sdk.get_rates(rate_request)
            if response.success and response.data:
                return response.data
        except Exception as e:
            logger.warning(f"Primary rate request failed: {e}")
        
        # Fallback 1: Try individual carriers
        carriers = ['USPS', 'FedEx', 'UPS']
        fallback_rates = []
        
        for carrier in carriers:
            try:
                carrier_request = {**rate_request, 'carrier': carrier}
                response = await self.sdk.get_rates(carrier_request)
                if response.success and response.data:
                    fallback_rates.extend(response.data)
            except Exception as e:
                logger.warning(f"Fallback rate request failed for {carrier}: {e}")
        
        return fallback_rates

    def select_rate_by_strategy(self, rates: List[ShippingRate], 
                              strategy: str, 
                              order_data: Dict[str, Any]) -> ShippingRate:
        """Select optimal rate based on advanced strategies."""
        if not rates:
            raise Exception("No rates available for selection")
        
        # Filter out rates that are too expensive for the order value
        order_value = sum(item['unit_price'] * item['quantity'] for item in order_data['items'])
        max_shipping = min(order_value * 0.3, 50.0)  # Max 30% of order value or $50
        
        affordable_rates = [r for r in rates if r.amount <= max_shipping]
        if not affordable_rates:
            affordable_rates = rates  # Fallback to all rates
        
        if strategy == 'cost':
            return min(affordable_rates, key=lambda r: r.amount)
        
        elif strategy == 'speed':
            return min(affordable_rates, key=lambda r: r.estimated_days)
        
        elif strategy == 'balanced':
            # Score based on normalized cost and speed
            def balanced_score(rate):
                max_cost = max(r.amount for r in affordable_rates)
                max_days = max(r.estimated_days for r in affordable_rates)
                cost_score = rate.amount / max_cost if max_cost > 0 else 0
                speed_score = rate.estimated_days / max_days if max_days > 0 else 0
                return cost_score * 0.6 + speed_score * 0.4
            
            return min(affordable_rates, key=balanced_score)
        
        elif strategy == 'premium':
            # Prefer reliable carriers with reasonable speed
            premium_carriers = ['FedEx', 'UPS']
            premium_rates = [r for r in affordable_rates if r.carrier in premium_carriers]
            if premium_rates:
                return min(premium_rates, key=lambda r: r.estimated_days)
            return self.select_rate_by_strategy(affordable_rates, 'balanced', order_data)
        
        else:
            return affordable_rates[0]

    async def purchase_label_with_retry(self, order_id: str, 
                                      selected_rate: ShippingRate,
                                      order_data: Dict[str, Any],
                                      max_retries: int = 3):
        """Purchase label with advanced retry logic."""
        label_request = self.build_label_request(order_id, selected_rate, order_data)
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.sdk.purchase_label(label_request)
                if response.success:
                    return response
                
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise Exception(f"Label purchase failed: {response.error}")
                    
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise e

    def build_rate_request(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build rate request with calculated package dimensions."""
        total_weight = sum(item['weight'] * item['quantity'] for item in order_data['items'])
        
        return {
            'from_address': {
                'street1': order_data['sender_street1'],
                'city': order_data['sender_city'],
                'state': order_data['sender_state'],
                'postal_code': order_data['sender_postal_code'],
                'country': order_data['sender_country']
            },
            'to_address': {
                'street1': order_data['recipient_street1'],
                'street2': order_data['recipient_street2'],
                'city': order_data['recipient_city'],
                'state': order_data['recipient_state'],
                'postal_code': order_data['recipient_postal_code'],
                'country': order_data['recipient_country']
            },
            'package': {
                'weight': max(total_weight, 0.1),
                'length': 12.0,
                'width': 9.0,
                'height': 6.0,
                'weight_unit': 'lb',
                'dimension_unit': 'in'
            },
            'options': {
                'signature': order_data.get('priority') == 'high',
                'insurance': total_weight > 2.0,
                'insurance_value': sum(
                    item['unit_price'] * item['quantity'] 
                    for item in order_data['items']
                ),
                'residential': True
            }
        }

    def build_label_request(self, order_id: str, 
                          selected_rate: ShippingRate, 
                          order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive label request."""
        return {
            'order_id': order_id,
            'rate_id': selected_rate.id,
            'from_address': {
                'name': order_data['sender_name'],
                'street1': order_data['sender_street1'],
                'city': order_data['sender_city'],
                'state': order_data['sender_state'],
                'postal_code': order_data['sender_postal_code'],
                'country': order_data['sender_country']
            },
            'to_address': {
                'name': order_data['recipient_name'],
                'email': order_data['recipient_email'],
                'phone': order_data['recipient_phone'],
                'street1': order_data['recipient_street1'],
                'street2': order_data['recipient_street2'],
                'city': order_data['recipient_city'],
                'state': order_data['recipient_state'],
                'postal_code': order_data['recipient_postal_code'],
                'country': order_data['recipient_country']
            },
            'package': self.build_rate_request(order_data)['package'],
            'options': {
                'label_format': 'PDF',
                'label_size': '4x6',
                'packaging': 'package',
                'references': {
                    'reference1': order_data['order_number'],
                    'reference2': f'ADV-{datetime.now().timestamp():.0f}'
                }
            }
        }

    async def generate_comprehensive_report(self) -> None:
        """Generate detailed processing report with analytics."""
        report = {
            'processing_summary': asdict(self.statistics),
            'timestamp': datetime.now().isoformat(),
            'success_rate': (self.statistics.successful_orders / self.statistics.total_orders * 100) 
                           if self.statistics.total_orders > 0 else 0,
            'detailed_results': [asdict(result) for result in self.results],
            'carrier_performance': self.analyze_carrier_performance(),
            'cost_analysis': self.analyze_costs(),
            'error_analysis': self.analyze_errors(),
            'recommendations': self.generate_recommendations()
        }
        
        # Save JSON report
        report_file = f"reports/advanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json.dumps(report, indent=2, default=str))
        
        print(f"📊 Comprehensive report saved to {report_file}")
        
        # Print summary
        print("\n📊 Processing Summary:")
        print(f"   Total Orders: {self.statistics.total_orders}")
        print(f"   Successful: {self.statistics.successful_orders}")
        print(f"   Failed: {self.statistics.failed_orders}")
        print(f"   Success Rate: {report['success_rate']:.1f}%")
        print(f"   Total Cost: ${self.statistics.total_cost:.2f}")
        print(f"   Average Cost: ${self.statistics.average_cost:.2f}")
        print(f"   Processing Time: {self.statistics.processing_time:.1f} seconds")

    def analyze_carrier_performance(self) -> Dict[str, Any]:
        """Analyze carrier performance metrics."""
        carrier_stats = {}
        
        for result in self.results:
            if result.success and result.selected_rate:
                carrier = result.selected_rate['carrier']
                if carrier not in carrier_stats:
                    carrier_stats[carrier] = {
                        'count': 0,
                        'total_cost': 0.0,
                        'total_days': 0,
                        'avg_cost': 0.0,
                        'avg_days': 0.0
                    }
                
                stats = carrier_stats[carrier]
                stats['count'] += 1
                stats['total_cost'] += result.selected_rate['cost']
                stats['total_days'] += result.selected_rate['estimated_days']
        
        # Calculate averages
        for carrier, stats in carrier_stats.items():
            if stats['count'] > 0:
                stats['avg_cost'] = stats['total_cost'] / stats['count']
                stats['avg_days'] = stats['total_days'] / stats['count']
        
        return carrier_stats

    def analyze_costs(self) -> Dict[str, Any]:
        """Analyze cost distribution and trends."""
        successful_results = [r for r in self.results if r.success and r.label_info]
        
        if not successful_results:
            return {}
        
        costs = [r.label_info['cost'] for r in successful_results]
        
        return {
            'min_cost': min(costs),
            'max_cost': max(costs),
            'avg_cost': sum(costs) / len(costs),
            'total_cost': sum(costs),
            'cost_distribution': {
                'under_10': len([c for c in costs if c < 10]),
                '10_to_20': len([c for c in costs if 10 <= c < 20]),
                '20_to_30': len([c for c in costs if 20 <= c < 30]),
                'over_30': len([c for c in costs if c >= 30])
            }
        }

    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and frequencies."""
        failed_results = [r for r in self.results if not r.success]
        
        error_types = {}
        for result in failed_results:
            error = result.error or 'Unknown error'
            if error not in error_types:
                error_types[error] = 0
            error_types[error] += 1
        
        return {
            'total_errors': len(failed_results),
            'error_types': error_types,
            'retry_analysis': {
                'orders_with_retries': len([r for r in failed_results if r.retry_count > 0]),
                'avg_retry_count': sum(r.retry_count for r in failed_results) / len(failed_results) 
                                 if failed_results else 0
            }
        }

    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on processing results."""
        recommendations = []
        
        # Carrier recommendations
        carrier_performance = self.analyze_carrier_performance()
        if carrier_performance:
            best_value_carrier = min(
                carrier_performance.items(),
                key=lambda x: x[1]['avg_cost']
            )[0]
            recommendations.append(
                f"Consider using {best_value_carrier} more frequently for cost optimization"
            )
        
        # Error rate recommendations
        error_rate = (self.statistics.failed_orders / self.statistics.total_orders * 100) \
                    if self.statistics.total_orders > 0 else 0
        
        if error_rate > 10:
            recommendations.append(
                "High error rate detected - review data quality and validation rules"
            )
        
        # Cost optimization
        cost_analysis = self.analyze_costs()
        if cost_analysis and cost_analysis['avg_cost'] > 15:
            recommendations.append(
                "Average shipping cost is high - consider bulk discounts or rate negotiation"
            )
        
        return recommendations

    async def export_results_to_csv(self) -> None:
        """Export results to CSV with comprehensive data."""
        csv_file = f"output/advanced_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        fieldnames = [
            'order_number', 'success', 'order_id', 'carrier', 'service',
            'cost', 'estimated_days', 'tracking_number', 'processing_time',
            'retry_count', 'error'
        ]
        
        async with aiofiles.open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(await f, fieldnames=fieldnames)
            await f.write(','.join(fieldnames) + '\n')  # Write header
            
            for result in self.results:
                row = {
                    'order_number': result.order_number,
                    'success': result.success,
                    'order_id': result.order_id or '',
                    'carrier': result.selected_rate['carrier'] if result.selected_rate else '',
                    'service': result.selected_rate['service'] if result.selected_rate else '',
                    'cost': result.selected_rate['cost'] if result.selected_rate else '',
                    'estimated_days': result.selected_rate['estimated_days'] if result.selected_rate else '',
                    'tracking_number': result.label_info['tracking_number'] if result.label_info else '',
                    'processing_time': f"{result.processing_time:.2f}" if result.processing_time else '',
                    'retry_count': result.retry_count,
                    'error': result.error or ''
                }
                
                # Manual CSV writing due to aiofiles limitations
                row_str = ','.join(f'"{str(v)}"' for v in row.values())
                await f.write(row_str + '\n')
        
        print(f"📄 Results exported to {csv_file}")

    async def generate_pandas_analytics(self) -> None:
        """Generate advanced analytics using pandas (if available)."""
        if not HAS_PANDAS:
            print("⚠️  Pandas not available - skipping advanced analytics")
            return
        
        print("📊 Generating pandas analytics...")
        
        # Convert results to DataFrame
        df_data = []
        for result in self.results:
            row = {
                'order_number': result.order_number,
                'success': result.success,
                'carrier': result.selected_rate['carrier'] if result.selected_rate else None,
                'cost': result.selected_rate['cost'] if result.selected_rate else None,
                'estimated_days': result.selected_rate['estimated_days'] if result.selected_rate else None,
                'processing_time': result.processing_time,
                'retry_count': result.retry_count
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Generate analytics
        analytics = {
            'success_rate_by_carrier': df[df['success']].groupby('carrier')['success'].count().to_dict(),
            'avg_cost_by_carrier': df[df['success']].groupby('carrier')['cost'].mean().to_dict(),
            'processing_time_stats': df['processing_time'].describe().to_dict(),
            'correlation_analysis': df[['cost', 'estimated_days', 'processing_time']].corr().to_dict()
        }
        
        # Save analytics
        analytics_file = f"reports/pandas_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        async with aiofiles.open(analytics_file, 'w') as f:
            await f.write(json.dumps(analytics, indent=2, default=str))
        
        print(f"📈 Pandas analytics saved to {analytics_file}")


# Webhook server implementation (if FastAPI is available)
if HAS_FASTAPI:
    app = FastAPI(title="atoship Webhook Server", version="1.0.0")
    
    class WebhookPayload(BaseModel):
        event_type: str
        data: dict
        timestamp: str
    
    @app.post("/webhook")
    async def handle_webhook(payload: WebhookPayload):
        """Handle incoming webhook notifications."""
        logger.info(f"Received webhook: {payload.event_type}")
        
        # Process different event types
        if payload.event_type == "label.purchased":
            await handle_label_purchased(payload.data)
        elif payload.event_type == "package.delivered":
            await handle_package_delivered(payload.data)
        elif payload.event_type == "package.exception":
            await handle_package_exception(payload.data)
        
        return {"status": "received"}
    
    async def handle_label_purchased(data: dict):
        """Handle label purchased event."""
        logger.info(f"Label purchased: {data.get('tracking_number')}")
    
    async def handle_package_delivered(data: dict):
        """Handle package delivered event."""
        logger.info(f"Package delivered: {data.get('tracking_number')}")
    
    async def handle_package_exception(data: dict):
        """Handle package exception event."""
        logger.warning(f"Package exception: {data.get('tracking_number')} - {data.get('description')}")


async def main():
    """Main execution function with command-line interface."""
    import sys
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
atoship Python SDK Advanced Example

Usage:
    python advanced_example.py --csv orders.csv [options]
    python advanced_example.py --webhook                    # Start webhook server
    python advanced_example.py --demo                       # Run demo with sample data
    python advanced_example.py --help                       # Show this help

Options:
    --strategy STRATEGY     # Shipping strategy: cost, speed, balanced, premium (default: balanced)
    --concurrent N          # Max concurrent operations (default: 5)
    --webhook-port PORT     # Webhook server port (default: 8000)

Environment Variables:
    ATOSHIP_API_KEY         # Required: Your atoship API key
    ATOSHIP_BASE_URL        # Optional: API base URL
    NODE_ENV                # Optional: Environment setting

Features:
    - Async batch processing with concurrency control
    - CSV import/export with validation
    - Rate optimization strategies
    - Comprehensive error handling and retry logic
    - Performance analytics and reporting
    - Webhook server integration
    - Pandas analytics (if installed)
        """)
        return
    
    # Check API key
    if not os.getenv('ATOSHIP_API_KEY'):
        print("❌ Error: ATOSHIP_API_KEY environment variable is required")
        return
    
    # Parse command line arguments
    if '--webhook' in sys.argv:
        if not HAS_FASTAPI:
            print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
            return
        
        port = 8000
        if '--webhook-port' in sys.argv:
            port_idx = sys.argv.index('--webhook-port') + 1
            if port_idx < len(sys.argv):
                port = int(sys.argv[port_idx])
        
        print(f"🚀 Starting webhook server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        return
    
    # Initialize processor
    concurrent = 5
    if '--concurrent' in sys.argv:
        concurrent_idx = sys.argv.index('--concurrent') + 1
        if concurrent_idx < len(sys.argv):
            concurrent = int(sys.argv[concurrent_idx])
    
    processor = AdvancedShippingProcessor(max_concurrent=concurrent)
    
    # Determine strategy
    strategy = 'balanced'
    if '--strategy' in sys.argv:
        strategy_idx = sys.argv.index('--strategy') + 1
        if strategy_idx < len(sys.argv):
            strategy = sys.argv[strategy_idx]
    
    # Process CSV file
    if '--csv' in sys.argv:
        csv_idx = sys.argv.index('--csv') + 1
        if csv_idx < len(sys.argv):
            csv_file = sys.argv[csv_idx]
            await processor.process_csv_orders(csv_file, strategy, concurrent)
        else:
            print("❌ Please provide CSV file path")
        return
    
    # Run demo
    if '--demo' in sys.argv:
        print("🚀 Running advanced demo with sample data...")
        
        # Create sample CSV for demo
        sample_csv = "sample_advanced_orders.csv"
        sample_orders = [
            {
                'order_number': f'DEMO-{i+1:03d}',
                'recipient_name': f'Customer {i+1}',
                'recipient_email': f'customer{i+1}@example.com',
                'recipient_address1': f'{(i+1)*100} Demo Street',
                'recipient_city': ['Seattle', 'Portland', 'San Francisco', 'Los Angeles'][i % 4],
                'recipient_state': ['WA', 'OR', 'CA', 'CA'][i % 4],
                'recipient_postal_code': ['98101', '97201', '94105', '90001'][i % 4],
                'item_name': f'Demo Product {i+1}',
                'item_sku': f'DEMO-{i+1:03d}',
                'item_quantity': 1,
                'item_price': 29.99 + (i * 5),
                'item_weight': 1.0 + (i * 0.5),
                'shipping_strategy': ['cost', 'speed', 'balanced', 'premium'][i % 4],
                'priority': ['standard', 'high'][i % 2]
            }
            for i in range(10)
        ]
        
        # Write sample CSV
        with open(sample_csv, 'w', newline='') as f:
            if sample_orders:
                writer = csv.DictWriter(f, fieldnames=sample_orders[0].keys())
                writer.writeheader()
                writer.writerows(sample_orders)
        
        # Process sample orders
        await processor.process_csv_orders(sample_csv, strategy, concurrent)
        
        # Cleanup
        os.remove(sample_csv)
        return
    
    print("❌ No valid command provided. Use --help for usage information.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Advanced example interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
        exit(1)