#!/usr/bin/env python3
"""
Automated Intelligence Brief Generator
=====================================

Generates daily/weekly intelligence briefings from RSS monitoring data
for executive decision making and strategic planning.
"""

import asyncio
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from claude.tools.intelligent_rss_monitor import IntelligentRSSMonitor

class IntelligenceBrief:
    """Generate executive intelligence briefings"""
    
    def __init__(self):
        self.monitor = IntelligentRSSMonitor()
        self.db_path = self.monitor.db_path
    
    async def generate_daily_brief(self) -> str:
        """Generate daily intelligence briefing"""
        yesterday = datetime.now() - timedelta(days=1)
        items = self._get_items_since(yesterday)
        
        if not items:
            await self.monitor.run_intelligence_sweep()
            items = self._get_items_since(yesterday)
        
        brief = self._format_executive_brief(items, "Daily", 1)
        return brief
    
    async def generate_weekly_brief(self) -> str:
        """Generate weekly intelligence briefing"""
        week_ago = datetime.now() - timedelta(days=7)
        items = self._get_items_since(week_ago)
        
        brief = self._format_executive_brief(items, "Weekly", 7)
        return brief
    
    def _get_items_since(self, since_date: datetime) -> list:
        """Get feed items since specified date"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT title, url, summary, source_feed, category, 
                       relevance_score, keywords, published
                FROM feed_items 
                WHERE processed_at >= ? 
                ORDER BY relevance_score DESC, published DESC
                LIMIT 50
            """, (since_date.isoformat(),)).fetchall()
            
            items = []
            for row in rows:
                items.append({
                    'title': row[0],
                    'url': row[1], 
                    'summary': row[2],
                    'source_feed': row[3],
                    'category': row[4],
                    'relevance_score': row[5],
                    'keywords': json.loads(row[6]) if row[6] else [],
                    'published': row[7]
                })
            
            return items
    
    def _format_executive_brief(self, items: list, period: str, days: int) -> str:
        """Format items into executive briefing"""
        if not items:
            return f"# {period} Intelligence Brief - {datetime.now().strftime('%Y-%m-%d')}\n\nNo new intelligence items found in the last {days} day(s)."
        
        # Categorize items
        categories = {}
        for item in items:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        # Extract trending keywords
        all_keywords = []
        for item in items:
            all_keywords.extend(item.get('keywords', []))
        
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        trending = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Generate briefing
        brief = f"""# {period} Intelligence Brief
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Period:** Last {days} day(s)  
**Items Analyzed:** {len(items)}  
**High Priority Items:** {len([i for i in items if i['relevance_score'] >= 0.8])}

## 🎯 Executive Summary

{self._generate_executive_summary(items, categories, trending)}

## 📊 Key Intelligence by Category

"""
        
        for category, cat_items in categories.items():
            if not cat_items:
                continue
                
            brief += f"### {category} ({len(cat_items)} items)\n\n"
            
            # Top 3 items in each category
            for item in cat_items[:3]:
                brief += f"**{item['title']}** ({item['relevance_score']})\n"
                brief += f"*{item['source_feed']}*\n"
                if item['summary']:
                    brief += f"{item['summary'][:150]}...\n"
                brief += f"🔗 [Read More]({item['url']})\n\n"
        
        brief += f"## 🔥 Trending Topics\n\n"
        for keyword, freq in trending:
            brief += f"- **{keyword.title()}**: {freq} mentions\n"
        
        brief += f"\n## 💡 Strategic Recommendations\n\n"
        recommendations = self._generate_strategic_recommendations(categories, trending, items)
        for rec in recommendations:
            brief += f"- {rec}\n"
        
        brief += f"\n## 📈 Intelligence Metrics\n\n"
        brief += f"- **Total Sources Monitored**: {len(set(item['source_feed'] for item in items))}\n"
        brief += f"- **Categories Covered**: {len(categories)}\n"
        brief += f"- **Average Relevance Score**: {sum(item['relevance_score'] for item in items) / len(items):.2f}\n"
        brief += f"- **Critical Items** (>0.9 relevance): {len([i for i in items if i['relevance_score'] >= 0.9])}\n"
        
        brief += f"\n---\n*Generated by Maia Intelligence System - {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        return brief
    
    def _generate_executive_summary(self, items: list, categories: dict, trending: list) -> str:
        """Generate executive summary of intelligence findings"""
        high_priority_count = len([i for i in items if i['relevance_score'] >= 0.8])
        
        summary = f"Analysis of {len(items)} intelligence items reveals {high_priority_count} high-priority developments across {len(categories)} key areas. "
        
        # Identify most active category
        most_active = max(categories.items(), key=lambda x: len(x[1]))
        summary += f"**{most_active[0]}** shows highest activity with {len(most_active[1])} items. "
        
        # Top trending topics
        if trending:
            top_trends = [t[0] for t in trending[:3]]
            summary += f"Key trends include: **{', '.join(top_trends)}**. "
        
        # Strategic implications
        if 'Cloud Technology' in categories and len(categories['Cloud Technology']) > 5:
            summary += "Cloud technology developments indicate accelerated adoption requiring architecture review. "
        
        if 'AI/ML' in categories and any(word in str(trending) for word in ['llm', 'ai']):
            summary += "AI/ML advancement signals significant integration opportunities. "
        
        if 'Engineering Management' in categories and len(categories['Engineering Management']) > 3:
            summary += "Leadership content surge suggests industry focus on management excellence."
        
        return summary
    
    def _generate_strategic_recommendations(self, categories: dict, trending: list, items: list) -> list:
        """Generate strategic recommendations based on intelligence analysis"""
        recommendations = []
        
        # Category-based recommendations
        if 'Cloud Technology' in categories:
            cloud_count = len(categories['Cloud Technology'])
            if cloud_count >= 5:
                recommendations.append(f"**Cloud Strategy Review**: {cloud_count} cloud developments indicate need for architecture assessment and multi-cloud strategy evaluation")
        
        if 'Engineering Management' in categories:
            mgmt_count = len(categories['Engineering Management'])
            if mgmt_count >= 3:
                recommendations.append(f"**Leadership Development**: {mgmt_count} management articles suggest focus on team performance and cultural transformation")
        
        if 'AI/ML' in categories:
            ai_count = len(categories['AI/ML'])
            recommendations.append(f"**AI Integration Assessment**: {ai_count} AI developments require evaluation of integration opportunities and competitive implications")
        
        # Trending-based recommendations
        trending_words = [t[0] for t in trending[:5]]
        
        if 'kubernetes' in trending_words:
            recommendations.append("**Container Strategy**: Kubernetes trending indicates need for container orchestration evaluation")
        
        if any(word in trending_words for word in ['llm', 'ai', 'chatgpt', 'machine learning']):
            recommendations.append("**AI Transformation**: AI technology prominence requires strategic AI integration roadmap")
        
        if 'startup' in trending_words or 'funding' in trending_words:
            recommendations.append("**Market Intelligence**: Startup activity suggests new competitive threats or partnership opportunities")
        
        # Relevance-based recommendations
        critical_items = [i for i in items if i['relevance_score'] >= 0.9]
        if critical_items:
            recommendations.append(f"**Critical Review Required**: {len(critical_items)} high-priority items need immediate executive attention")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("**Continue Monitoring**: Maintain intelligence gathering across all categories for emerging opportunities")
        
        return recommendations[:5]  # Limit to top 5 recommendations

async def main():
    """Main execution for intelligence briefing generation"""
    brief_type = sys.argv[1] if len(sys.argv) > 1 else 'daily'
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    intelligence = IntelligenceBrief()
    
    print(f"📊 Generating {brief_type} intelligence briefing...")
    
    if brief_type.lower() == 'weekly':
        briefing = await intelligence.generate_weekly_brief()
    else:
        briefing = await intelligence.generate_daily_brief()
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(briefing)
        print(f"📄 Briefing saved to: {output_file}")
    else:
        print("\n" + "="*80)
        print(briefing)
        print("="*80)

if __name__ == "__main__":
    asyncio.run(main())