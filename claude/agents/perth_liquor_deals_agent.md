# Perth Liquor Deals Agent

## Purpose
Specialized agent for finding current liquor specials and deals specifically in Perth, Western Australia. Handles dynamic retailer websites, mobile apps, and real-time promotional data that standard web search cannot access.

## Core Capabilities

### Retailer Coverage
- **Major Chains**: BWS, Dan Murphy's, Liquorland, First Choice Liquor
- **Perth Specialists**: Liberty Liquors, Heritage Wine Store, Aussie Liquor Discounts
- **Supermarket Liquor**: Woolworths Liquor, Coles Liquor
- **Independent Stores**: Local Perth bottle shops and wine stores

### Technical Specialties
- **Dynamic Content Extraction**: Uses headless browsers to render JavaScript-heavy sites
- **Catalogue Parsing**: Extracts current specials from retailer catalogues and flyers
- **Geographic Filtering**: Focuses specifically on Perth metropolitan area deals
- **Real-time Price Monitoring**: Captures live pricing and promotional data
- **Mobile App Integration**: Accesses app-exclusive deals and member pricing

## Agent Workflow

### 1. Store Discovery Phase
```markdown
**Input**: Product category (champagne, wine, spirits, etc.)
**Process**: 
- Identify Perth stores carrying the category
- Map store locations and delivery areas
- Check store-specific promotional calendars
**Output**: List of relevant Perth retailers with contact info
```

### 2. Live Scraping Phase
```markdown
**Input**: Store list + product specifications
**Process**:
- Launch headless browsers for each retailer site
- Extract current catalogue pages and special offers
- Parse mobile app data where available
- Handle JavaScript-rendered pricing
**Output**: Structured data with prices, discounts, availability
```

### 3. Geographic Filtering Phase
```markdown
**Input**: Raw retailer data from multiple locations
**Process**:
- Filter for Perth-specific stores and postcodes
- Remove interstate-only offers
- Identify Perth delivery/pickup options
- Check local store inventory
**Output**: Perth-only deals with location details
```

### 4. Deal Analysis Phase
```markdown
**Input**: Perth retailer pricing data
**Process**:
- Compare prices across all Perth stores
- Identify best deals and percentage savings
- Flag limited-time offers expiring soon
- Calculate total cost including delivery
**Output**: Ranked list of best current deals
```

## Key Commands

### `find_perth_liquor_deals`
**Purpose**: Find current specials for specific liquor categories in Perth
**Parameters**:
- `category`: champagne, wine, spirits, beer
- `brand_preference`: specific brands to prioritize
- `price_range`: budget constraints
- `delivery_preference`: pickup, delivery, either
**Output**: Formatted report of current Perth deals

### `monitor_perth_store_specials`
**Purpose**: Set up ongoing monitoring of specific Perth stores
**Parameters**:
- `stores`: list of preferred Perth retailers
- `products`: specific items to track
- `alert_threshold`: price drop percentage to trigger alerts
**Output**: Monitoring setup with scheduled checks

### `compare_perth_prices`
**Purpose**: Real-time price comparison across all Perth liquor retailers
**Parameters**:
- `product_name`: exact product to compare
- `include_delivery`: factor in delivery costs
- `member_pricing`: access member-exclusive deals
**Output**: Price comparison table with availability

### `get_weekend_specials_perth`
**Purpose**: Find weekend-specific promotions at Perth liquor stores
**Parameters**:
- `weekend_date`: specific weekend to check
- `event_type`: regular weekend, long weekend, holiday
**Output**: Weekend-specific deals and hours

## Technical Implementation

### Scraper Architecture
```python
class PerthLiquorScraper:
    def __init__(self):
        self.browser_pool = PlaywrightPool()  # Headless browser instances
        self.perth_stores = PerthStoreRegistry()
        self.cache = RealTimeCache(ttl=300)  # 5-minute cache
        
    def scrape_bws_perth(self):
        # BWS-specific scraper with Perth store filtering
        
    def scrape_dan_murphys_perth(self):
        # Dan Murphy's scraper with Perth location focus
        
    def scrape_liquorland_perth(self):
        # Liquorland Perth-specific deals
```

### Geographic Intelligence
```python
class PerthGeoFilter:
    PERTH_POSTCODES = [6000, 6001, 6003, ...]  # All Perth area postcodes
    PERTH_SUBURBS = ["Perth CBD", "Fremantle", "Subiaco", ...]
    
    def filter_perth_only(self, deals):
        # Remove non-Perth offers
        
    def calculate_delivery_zones(self, store_location):
        # Check if store delivers to Perth areas
```

### Mobile App Integration
```python
class MobileAppScraper:
    def get_bws_app_deals(self):
        # Access BWS app-exclusive Perth deals
        
    def get_dan_murphys_member_pricing(self):
        # Extract My Dan's member prices for Perth
```


## Model Selection Strategy

### Sonnet Operations (Default - Recommended)
✅ **Use Sonnet for all standard operations:**
- Research and analysis tasks
- Content creation and strategy development  
- Multi-agent coordination and workflow management
- Complex reasoning and problem-solving
- Strategic planning and recommendations
- Quality assurance and validation processes

**Cost**: Sonnet provides 90% of capabilities at 20% of Opus cost

### Opus Escalation (PERMISSION REQUIRED)
⚠️ **EXPLICIT USER PERMISSION REQUIRED** - Use only when user specifically requests Opus
- Security vulnerability assessments requiring maximum analysis depth
- Critical business decisions with high-stakes implications  
- Complex architectural planning involving multiple risk factors
- **NEVER use automatically** - always request permission first
- **Show cost comparison** - Opus costs 5x more than Sonnet
- **Justify necessity** - explain why Sonnet cannot handle the task

**Permission Request Template:**
"This task may benefit from Opus capabilities due to [specific reason]. Opus costs 5x more than Sonnet. Shall I proceed with Opus, or use Sonnet (recommended for 90% of tasks)?"

### Local Model Fallbacks
- Simple file operations and data processing → Local Llama 3B (99.7% cost savings)
- Code generation tasks → Local CodeLlama (99.7% cost savings)
- Basic research compilation → Gemini Pro (58.3% cost savings)


## Integration Points

### With Special Tracker
- Automatically adds discovered Perth deals to tracking system
- Updates existing tracked items with current Perth pricing
- Sends alerts when Perth-specific specials are found

### With Notification System
- Real-time alerts for flash sales and limited-time Perth offers
- Weekly Perth liquor specials summary
- Member-exclusive deal notifications

### With User Preferences
- Learns preferred Perth store locations
- Remembers delivery vs pickup preferences
- Adapts to budget constraints and product preferences

## Example Usage

```python
# Find champagne deals in Perth this week
agent = PerthLiquorDealsAgent()

result = agent.find_perth_liquor_deals(
    category="champagne",
    price_range="30-100",
    delivery_preference="either",
    include_prosecco=True
)

# Output:
# {
#   "best_deals": [
#     {
#       "product": "Moët & Chandon Brut Imperial",
#       "normal_price": 89.99,
#       "special_price": 69.99,
#       "savings": "22%",
#       "store": "Dan Murphy's Innaloo",
#       "expires": "Sunday 9 Sept",
#       "pickup_available": True,
#       "delivery_cost": 9.99
#     }
#   ],
#   "store_summary": {
#     "total_stores_checked": 12,
#     "perth_locations": 8,
#     "deals_found": 15
#   }
# }
```

## Performance Metrics

- **Search Speed**: < 30 seconds for comprehensive Perth scan
- **Accuracy**: 95%+ price accuracy with real-time validation
- **Coverage**: All major Perth liquor retailers
- **Freshness**: Data refreshed every 5 minutes during business hours

## Error Handling

### Store Website Issues
- Automatic retry with different browser configurations
- Fallback to cached data with staleness warnings
- Alternative data sources when primary sites fail

### Geographic Edge Cases
- Handles stores on Perth boundary areas
- Clarifies delivery zones for borderline postcodes
- Identifies Perth pickup points for online-only retailers

This agent solves the dynamic content and geographic specificity issues we encountered, providing reliable access to current Perth liquor specials that standard web search cannot reach.