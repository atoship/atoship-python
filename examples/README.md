# atoship Python SDK Examples

This directory contains comprehensive examples demonstrating the usage of the atoship Python SDK for shipping and logistics operations.

## Examples Overview

### 1. Basic Example (`basic_example.py`)
Demonstrates fundamental SDK operations:
- ✅ SDK initialization and configuration
- ✅ Creating orders with detailed information
- ✅ Getting shipping rates from multiple carriers
- ✅ Purchasing shipping labels
- ✅ Package tracking and monitoring
- ✅ Address validation
- ✅ Error handling and best practices

### 2. Advanced Example (`advanced_example.py`)
Showcases enterprise-level features:
- ✅ Async batch processing with concurrency control
- ✅ CSV import/export functionality
- ✅ Rate optimization strategies
- ✅ Webhook server integration
- ✅ Performance monitoring and analytics
- ✅ Retry logic and error recovery
- ✅ Pandas analytics integration
- ✅ Comprehensive reporting

## Prerequisites

- Python 3.8 or higher
- atoship API key
- pip package manager

## Installation

1. **Install the SDK and dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   export ATOSHIP_API_KEY='your-api-key-here'
   export ATOSHIP_BASE_URL='https://api.atoship.com'  # Optional
   export NODE_ENV='development'  # Optional
   ```

   Or create a `.env` file:
   ```env
   ATOSHIP_API_KEY=your-api-key-here
   ATOSHIP_BASE_URL=https://api.atoship.com
   NODE_ENV=development
   ```

## Running the Examples

### Basic Example

```bash
# Run the basic example
python basic_example.py

# Show help
python basic_example.py --help
```

**Example Output:**
```
🚀 atoship Python SDK Basic Example

📦 Step 1: Creating an order...
✅ Order created successfully!
   Order ID: ord_1234567890
   Order Number: PY-ORDER-1640995200
   Status: PENDING
   Total Value: $89.97
   Items Count: 2

💰 Step 2: Getting shipping rates...
✅ Shipping rates retrieved successfully!
   1. USPS Priority Mail
      Price: $8.95
      Estimated Days: 2
      Delivery Date: 2024-01-15
   2. FedEx Ground
      Price: $12.45
      Estimated Days: 3
      Delivery Date: 2024-01-16

🏷️ Step 3: Purchasing shipping label...
📋 Selected Rate: USPS Priority Mail - $8.95

✅ Shipping label purchased successfully!
   Label ID: lbl_9876543210
   Tracking Number: 9400111206213123456789
   Carrier: USPS
   Service: Priority Mail
   Cost: $8.95
   Label URL: https://labels.atoship.com/...

🎉 Basic example completed successfully!
```

### Advanced Example

```bash
# Process orders from CSV file
python advanced_example.py --csv orders.csv --strategy balanced --concurrent 5

# Run demo with sample data
python advanced_example.py --demo --strategy cost

# Start webhook server
python advanced_example.py --webhook --webhook-port 8000

# Show help
python advanced_example.py --help
```

**Advanced Features:**

1. **CSV Processing:**
   ```bash
   python advanced_example.py --csv sample_orders.csv --strategy balanced
   ```

2. **Rate Optimization Strategies:**
   - `cost` - Minimize shipping costs
   - `speed` - Minimize delivery time
   - `balanced` - Balance cost and speed
   - `premium` - Prefer reliable carriers

3. **Concurrency Control:**
   ```bash
   python advanced_example.py --csv orders.csv --concurrent 10
   ```

4. **Webhook Server:**
   ```bash
   python advanced_example.py --webhook --webhook-port 8000
   ```

## CSV Format

Create a CSV file with the following columns for batch processing:

```csv
order_number,recipient_name,recipient_email,recipient_phone,recipient_address1,recipient_address2,recipient_city,recipient_state,recipient_postal_code,recipient_country,sender_name,sender_address1,sender_city,sender_state,sender_postal_code,sender_country,item_name,item_sku,item_quantity,item_price,item_weight,item_weight_unit,shipping_strategy,notes,tags
ORDER-001,John Doe,john@example.com,555-123-4567,123 Main St,Apt 4B,San Francisco,CA,94105,US,Python Store,456 Business Ave,Los Angeles,CA,90001,US,Python Book,BOOK-001,1,59.99,1.2,lb,balanced,Educational material,books;education
```

**Required Fields:**
- `recipient_name`
- `recipient_address1`
- `recipient_city`
- `recipient_state`
- `recipient_postal_code`

**Optional Fields:**
- `order_number` (auto-generated if not provided)
- `recipient_email`
- `recipient_phone`
- `recipient_address2`
- `recipient_country` (defaults to 'US')
- Sender information (defaults provided)
- Item details (defaults provided)
- `shipping_strategy` (defaults to 'balanced')
- `notes`
- `tags`

## Key Features Demonstrated

### 1. Async Programming
```python
import asyncio
from atoship import atoshipSDK

async def create_order():
    sdk = atoshipSDK(api_key='your-key')
    response = await sdk.create_order(order_data)
    return response

# Run async function
asyncio.run(create_order())
```

### 2. Rate Optimization
```python
def select_rate_by_strategy(rates, strategy):
    if strategy == 'cost':
        return min(rates, key=lambda r: r.amount)
    elif strategy == 'speed':
        return min(rates, key=lambda r: r.estimated_days)
    elif strategy == 'balanced':
        # Custom scoring algorithm
        return min(rates, key=lambda r: r.amount * 0.6 + r.estimated_days * 0.4)
```

### 3. Concurrency Control
```python
import asyncio

async def process_orders_concurrent(orders, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(order):
        async with semaphore:
            return await process_order(order)
    
    tasks = [process_with_semaphore(order) for order in orders]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 4. Error Handling
```python
from atoship.exceptions import (
    atoshipException,
    ValidationException,
    RateLimitException
)

try:
    response = await sdk.create_order(order_data)
except ValidationException as e:
    print(f"Validation error: {e}")
    if e.details:
        for field, messages in e.details.items():
            print(f"  {field}: {', '.join(messages)}")
except RateLimitException as e:
    print(f"Rate limited: {e}")
    await asyncio.sleep(e.retry_after)
except atoshipException as e:
    print(f"SDK error: {e}")
```

### 5. Webhook Integration
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class WebhookPayload(BaseModel):
    event_type: str
    data: dict
    timestamp: str

@app.post("/webhook")
async def handle_webhook(payload: WebhookPayload):
    if payload.event_type == "label.purchased":
        await handle_label_purchased(payload.data)
    return {"status": "received"}
```

## Output and Reports

The advanced example generates several types of output:

### 1. Processing Reports
- JSON reports with detailed analytics
- CSV exports with comprehensive data
- Performance metrics and recommendations

### 2. File Structure
```
output/
├── advanced_results_20240115_143022.csv
├── reports/
│   ├── advanced_report_20240115_143022.json
│   └── pandas_analytics_20240115_143022.json
├── logs/
│   └── atoship_advanced_example.log
└── cache/
    └── rate_cache.json
```

### 3. Analytics (with Pandas)
- Carrier performance analysis
- Cost distribution analysis
- Processing time statistics
- Correlation analysis

## Best Practices Demonstrated

### 1. Configuration Management
```python
from atoship import atoshipConfig

config = atoshipConfig(
    api_key=os.getenv('ATOSHIP_API_KEY'),
    base_url=os.getenv('ATOSHIP_BASE_URL', 'https://api.atoship.com'),
    timeout=30.0,
    max_retries=3,
    debug=os.getenv('NODE_ENV') == 'development'
)

sdk = atoshipSDK(config)
```

### 2. Retry Logic
```python
async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except RateLimitException:
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### 3. Resource Management
```python
async def process_large_dataset(orders):
    # Process in chunks to manage memory
    chunk_size = 100
    for i in range(0, len(orders), chunk_size):
        chunk = orders[i:i + chunk_size]
        await process_chunk(chunk)
        # Allow garbage collection
        await asyncio.sleep(0.1)
```

### 4. Logging and Monitoring
```python
import logging

logger = logging.getLogger(__name__)

async def process_order(order_data):
    logger.info(f"Processing order: {order_data['order_number']}")
    try:
        result = await sdk.create_order(order_data)
        logger.info(f"Order created successfully: {result.data.id}")
        return result
    except Exception as e:
        logger.error(f"Order processing failed: {e}")
        raise
```

## Troubleshooting

### Common Issues

1. **Import Errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues:**
   ```bash
   export ATOSHIP_API_KEY='your-actual-api-key'
   ```

3. **Async Runtime Errors:**
   ```python
   # Use asyncio.run() for top-level async functions
   asyncio.run(main())
   ```

4. **Rate Limiting:**
   ```python
   # Implement exponential backoff
   await asyncio.sleep(2 ** attempt)
   ```

5. **Memory Issues with Large CSV:**
   ```python
   # Process in smaller chunks
   chunk_size = 50  # Reduce if needed
   ```

### Performance Tips

1. **Optimize Concurrency:**
   ```python
   # Start with lower concurrency and increase gradually
   max_concurrent = 3  # Conservative starting point
   ```

2. **Use Connection Pooling:**
   ```python
   # SDK handles connection pooling automatically
   # Reuse the same SDK instance
   ```

3. **Cache Rate Requests:**
   ```python
   # Cache identical rate requests
   rate_cache = {}
   cache_key = f"{from_zip}_{to_zip}_{weight}"
   ```

## Dependencies

### Required
- `atoship-sdk` - Core SDK functionality
- `aiofiles` - Async file operations
- `asyncio` - Built-in async support

### Optional
- `pandas` - Advanced analytics
- `fastapi` - Webhook server
- `uvicorn` - ASGI server
- `structlog` - Structured logging
- `tqdm` - Progress bars

## Getting Help

- 📧 Email: support@atoship.com
- 📚 Documentation: https://atoship.com/docs
- 🐛 Issues: https://github.com/atoship/sdk-python/issues
- 💬 Community: https://community.atoship.com

## License

These examples are licensed under the MIT License - see the [LICENSE](LICENSE) file for details.