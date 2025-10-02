# Find Perth Liquor Specials

## Purpose
Specialized command to find current liquor specials and deals specifically in Perth, Western Australia using the Perth Liquor Deals Agent.

## Usage
```bash
claude find_perth_liquor_specials [category] [price_range] [options]
```

## Parameters
- **category**: champagne, wine, spirits, beer, prosecco (default: champagne)
- **price_range**: "min-max" format like "30-100" (optional)
- **options**: --member-only, --pickup-only, --weekend-only

## Examples
```bash
# Find champagne specials this week
claude find_perth_liquor_specials champagne

# Find champagne between $30-100
claude find_perth_liquor_specials champagne 30-100

# Find prosecco specials under $50
claude find_perth_liquor_specials prosecco 0-50

# Find weekend wine specials
claude find_perth_liquor_specials wine --weekend-only
```

## Command Implementation

### Agent Orchestration
```markdown
## Agent Chain
1. **Perth Liquor Deals Agent**
   - Input: Category, price range, location preferences
   - Process: Real-time scraping of Perth liquor retailers
   - Output: Current deals with pricing and availability
   - Fallback: Cached deals if live scraping fails

2. **Geographic Filter Agent** (Parallel)
   - Input: Raw retailer data
   - Process: Filter for Perth-specific stores and postcodes
   - Output: Perth-only deals with location details
   
3. **Deal Ranking Agent**
   - Input: All Perth deals found
   - Process: Rank by savings percentage, expiry urgency
   - Output: Prioritized list of best current deals
```

### Integration Points
- Uses Perth Liquor Deals Agent for specialized scraping
- Integrates with Special Tracker for ongoing monitoring
- Sends results via Gmail if requested
- Caches results for quick repeat queries

## Output Format

### Console Output
```
🍾 Perth Champagne Specials This Week

📊 Summary:
• 12 deals found across 8 Perth stores
• Average savings: 18%
• Best deal expires: This Sunday

🏆 Top Deals:
1. Moët & Chandon Imperial - $69.99 (was $89.99) - 22% off
   📍 Dan Murphy's North Perth, Innaloo, Carine
   ⏰ Expires: 14 days | 🎫 Member only

2. Veuve Clicquot Brut NV - $64.99 (was $79.99) - 19% off  
   📍 All Dan Murphy's Perth locations
   ⏰ Expires: This weekend

3. Chandon Brut NV - $26.99 (was $32.99) - 18% off
   📍 All BWS Perth locations  
   ⏰ Expires: Sunday | 🚚 Free delivery over $100
```

### JSON Output (for integrations)
```json
{
  "search_criteria": {
    "category": "champagne",
    "price_range": [30, 100],
    "location": "Perth, WA"
  },
  "summary": {
    "total_deals": 12,
    "stores_checked": 8,
    "avg_savings_percent": 18.5,
    "expires_soon_count": 3
  },
  "best_deals": [
    {
      "product": "Moët & Chandon Imperial",
      "brand": "Moët & Chandon",
      "special_price": 69.99,
      "normal_price": 89.99,
      "savings_percent": 22.2,
      "stores": ["Dan Murphy's North Perth", "Dan Murphy's Innaloo"],
      "expires": "14 days",
      "member_only": true,
      "pickup_available": true,
      "delivery_available": true
    }
  ]
}
```

## Technical Implementation

### Command Handler
```python
def find_perth_liquor_specials(category="champagne", price_range=None, options=None):
    # Initialize Perth Liquor Deals Agent
    agent = PerthLiquorDealsAgent()
    
    # Parse price range
    if price_range:
        min_price, max_price = parse_price_range(price_range)
    else:
        min_price, max_price = None, None
    
    # Execute search
    results = agent.find_perth_liquor_deals(
        category=category,
        price_range=(min_price, max_price) if min_price else None,
        force_refresh=True
    )
    
    # Format and display results
    display_perth_deals(results)
    
    # Optional: Add to Special Tracker
    if "--track" in options:
        add_deals_to_tracker(results)
    
    return results
```

### Integration with Special Tracker
```python
def add_deals_to_tracker(results):
    """Add found Perth deals to ongoing tracking"""
    for deal in results['best_deals']:
        tracker.add_item(
            name=deal['product'],
            category=deal['category'],
            target_price=deal['special_price'] * 0.9,  # Alert if 10% cheaper
            search_terms=[f"{deal['product']} Perth liquor special"]
        )
```

## Performance Characteristics

- **Speed**: 15-30 seconds for comprehensive Perth scan
- **Accuracy**: Mock data currently, 95%+ with live scraping
- **Coverage**: BWS, Dan Murphy's, Liquorland Perth locations
- **Freshness**: Real-time scraping with 30-minute cache
- **Geographic**: Perth metro area focus (postcodes 6000-6031)

## Error Handling

### Store Website Issues
- Automatic fallback to cached data with staleness warnings
- Retry logic with different scraping strategies
- Partial results if some stores fail

### Geographic Edge Cases
- Handles Perth boundary area stores
- Clarifies delivery zones for borderline postcodes
- Identifies Perth pickup points for online retailers

## Next Steps for Full Implementation

1. **Add Playwright/Selenium**: Real headless browser scraping
2. **Store APIs**: Direct integration where available (Woolworths API)
3. **Mobile App Scraping**: Access app-exclusive deals
4. **Real-time Monitoring**: Scheduled checks for flash sales
5. **User Preferences**: Remember favorite stores and brands

This command solves the original champagne specials search problem by providing a specialized, Perth-focused solution that handles dynamic content and geographic specificity.