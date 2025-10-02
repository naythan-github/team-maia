# Intelligence Monitor Command

## Purpose
Comprehensive RSS feed monitoring and intelligence gathering for competitive analysis, industry trends, and professional development insights.

## Usage
```bash
maia intelligence_monitor [action] [options]
```

## Actions

### `sweep` - Full Intelligence Sweep
Runs complete monitoring sweep across all active RSS sources
```bash
maia intelligence_monitor sweep
```

### `quick` - Quick Update
Fast scan of high-priority sources only
```bash
maia intelligence_monitor quick
```

### `summary` - Generate Summary
Creates intelligence briefing from recent data
```bash
maia intelligence_monitor summary [days]
```

### `trending` - Trending Analysis
Shows trending keywords and topics
```bash
maia intelligence_monitor trending
```

### `sources` - Manage Sources
List, add, or modify RSS feed sources
```bash
maia intelligence_monitor sources [list|add|disable]
```

## Implementation

```python
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from claude.tools.intelligent_rss_monitor import IntelligentRSSMonitor

async def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'sweep'
    monitor = IntelligentRSSMonitor()
    
    if action == 'sweep':
        print("🔍 Running full intelligence sweep...")
        summary = await monitor.run_intelligence_sweep()
        print_summary(summary)
        
    elif action == 'quick':
        print("⚡ Quick intelligence update...")
        summary = await monitor.run_quick_scan()
        print_summary(summary)
        
    elif action == 'summary':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        summary = await monitor.generate_briefing(days)
        print_briefing(summary)
        
    elif action == 'trending':
        trends = await monitor.get_trending_analysis()
        print_trends(trends)
        
    elif action == 'sources':
        subaction = sys.argv[2] if len(sys.argv) > 2 else 'list'
        await manage_sources(monitor, subaction)

def print_summary(summary):
    """Print formatted intelligence summary"""
    print(f"\n📊 Intelligence Summary")
    print("=" * 50)
    print(f"📈 Total items: {summary.get('total_items', 0)}")
    print(f"⭐ High relevance: {summary.get('high_relevance_items', 0)}")
    
    print(f"\n📂 Categories:")
    for category, count in summary.get('categories', {}).items():
        print(f"  • {category}: {count} items")
    
    print(f"\n🔥 Trending Keywords:")
    for trend in summary.get('trending_keywords', [])[:5]:
        print(f"  • {trend['keyword']}: {trend['frequency']} mentions")
    
    print(f"\n💡 Recommendations:")
    for rec in summary.get('recommendations', []):
        print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(main())
```

## RSS Sources Included

### Engineering Management & Leadership
- **The Pragmatic Engineer** - Industry observations and engineering insights
- **The Engineering Manager** - Management resources and tutorials  
- **Rands in Repose** - Leadership and team dynamics

### Cloud Technology
- **AWS News** - Latest AWS services and updates
- **Azure Updates** - Microsoft Azure announcements
- **Google Cloud Blog** - GCP features and AI/ML advances

### Business Intelligence
- **Harvard Business Review** - Strategic insights and leadership
- **McKinsey Insights** - Transformation and operations

### AI & Technology
- **Towards Data Science** - AI/ML research and applications
- **OpenAI Blog** - Latest AI developments
- **TechCrunch** - Industry news and startup intelligence

### Australian Market
- **AFR Technology** - Australian enterprise technology
- **StartupDaily** - Local innovation and venture capital

## Intelligence Features

### Relevance Scoring
- Source priority weighting (1-5 scale)
- Keyword matching against professional interests
- Category-specific multipliers
- Content quality assessment

### Trend Analysis
- Keyword frequency tracking
- Cross-category pattern recognition
- Emerging technology identification
- Market signal detection

### Smart Filtering
- Duplicate content detection
- Content quality scoring
- Professional relevance filtering
- Industry-specific categorization

### Actionable Intelligence
- Strategic recommendations
- Technology adoption signals
- Competitive intelligence insights
- Professional development opportunities

## Database Schema

### feed_items
- Comprehensive article storage
- Relevance scoring and categorization
- Full-text content for analysis
- Deduplication via content hashing

### feed_sources
- Source configuration and management
- Performance tracking and reliability
- Priority and update frequency settings
- Success/error statistics

### intelligence_summaries
- Daily/weekly intelligence briefings
- Key insights and trending topics
- Action items and recommendations
- Historical analysis capabilities

## Integration

This command integrates with:
- **Production Deployment System** - Automated intelligence gathering
- **Executive Dashboard** - Strategic briefing generation
- **Knowledge Graph** - Cross-referencing and learning
- **Alert System** - Critical intelligence notifications

## Automation

### Daily Execution
```bash
# Add to cron for daily intelligence gathering
0 9 * * * cd ${MAIA_ROOT} && python3 -c "import asyncio; from claude.tools.intelligent_rss_monitor import IntelligentRSSMonitor; asyncio.run(IntelligentRSSMonitor().run_intelligence_sweep())"
```

### Weekly Briefings
```bash
# Weekly executive briefing generation
0 9 * * 1 cd ${MAIA_ROOT} && maia intelligence_monitor summary 7
```

This intelligence monitoring system provides comprehensive market intelligence, competitive analysis, and professional development insights tailored for engineering leadership and cloud practice development.