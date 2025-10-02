#!/usr/bin/env python3
"""
Intelligent RSS Feed Monitor & Analysis System
==============================================

Comprehensive RSS feed monitoring, intelligent filtering, and analysis system
for competitive intelligence, industry trends, and professional development.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import hashlib
import re
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import feedparser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FeedItem:
    """Structured feed item with intelligence scoring"""
    title: str
    url: str
    summary: str
    published: datetime
    source_feed: str
    category: str
    relevance_score: float
    keywords: List[str]
    content_hash: str
    full_content: Optional[str] = None
    analysis: Optional[str] = None

@dataclass
class FeedSource:
    """RSS feed source configuration"""
    name: str
    url: str
    category: str
    priority: int  # 1-5, 5 being highest
    update_frequency: int  # minutes
    keywords: List[str]
    active: bool = True

class IntelligentRSSMonitor:
    """Advanced RSS monitoring with AI-powered analysis and filtering"""
    
    def __init__(self, db_path: str = "claude/data/rss_intelligence.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._load_feed_sources()
        
    def _init_database(self):
        """Initialize SQLite database for feed data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    published TIMESTAMP,
                    source_feed TEXT,
                    category TEXT,
                    relevance_score REAL,
                    keywords TEXT,  -- JSON array
                    content_hash TEXT UNIQUE,
                    full_content TEXT,
                    analysis TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    category TEXT,
                    priority INTEGER,
                    update_frequency INTEGER,
                    keywords TEXT,  -- JSON array
                    active BOOLEAN DEFAULT 1,
                    last_updated TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT,
                    summary TEXT,
                    key_insights TEXT,  -- JSON array
                    trending_topics TEXT,  -- JSON array
                    action_items TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _load_feed_sources(self):
        """Load predefined high-value RSS feed sources"""
        sources = [
            # Engineering Management & Tech Leadership
            FeedSource("The Pragmatic Engineer", "https://blog.pragmaticengineer.com/rss", 
                      "Engineering Management", 5, 60, 
                      ["engineering management", "tech leadership", "software engineering", "team building"]),
            FeedSource("The Engineering Manager", "https://theengineeringmanager.com/feed", 
                      "Engineering Management", 5, 60,
                      ["engineering management", "leadership", "productivity", "team management"]),
            FeedSource("Rands in Repose", "https://randsinrepose.com/feed/", 
                      "Engineering Management", 4, 120,
                      ["leadership", "management", "engineering culture", "team dynamics"]),
            
            # Cloud & Infrastructure
            FeedSource("AWS News", "https://aws.amazon.com/about-aws/whats-new/recent/feed/", 
                      "Cloud Technology", 5, 30,
                      ["aws", "cloud", "infrastructure", "devops", "serverless"]),
            FeedSource("Azure Updates", "https://azure.microsoft.com/en-us/updates/feed/", 
                      "Cloud Technology", 5, 30,
                      ["azure", "microsoft", "cloud", "enterprise"]),
            FeedSource("Google Cloud Blog", "https://cloudblog.withgoogle.com/rss", 
                      "Cloud Technology", 5, 30,
                      ["gcp", "google cloud", "kubernetes", "ai", "ml"]),
            
            # Business Intelligence & Analytics
            FeedSource("Harvard Business Review", "https://feeds.hbr.org/harvardbusiness", 
                      "Business Strategy", 4, 180,
                      ["strategy", "leadership", "innovation", "digital transformation"]),
            FeedSource("McKinsey Insights", "https://www.mckinsey.com/featured-insights/rss", 
                      "Business Strategy", 4, 240,
                      ["consulting", "transformation", "technology", "operations"]),
            
            # AI & Machine Learning
            FeedSource("Towards Data Science", "https://towardsdatascience.com/feed", 
                      "AI/ML", 4, 60,
                      ["ai", "machine learning", "data science", "analytics"]),
            FeedSource("OpenAI Blog", "https://openai.com/blog/rss.xml", 
                      "AI/ML", 5, 120,
                      ["openai", "gpt", "artificial intelligence", "research"]),
            
            # Competitive Intelligence
            FeedSource("TechCrunch", "https://techcrunch.com/feed/", 
                      "Tech Industry", 3, 30,
                      ["startup", "funding", "enterprise", "technology"]),
            FeedSource("The Information", "https://www.theinformation.com/feed", 
                      "Tech Industry", 4, 60,
                      ["enterprise", "big tech", "strategy", "market intelligence"]),
            
            # Australian Market
            FeedSource("AFR Technology", "https://www.afr.com/technology/rss", 
                      "Australian Market", 4, 120,
                      ["australia", "technology", "enterprise", "digital transformation"]),
            FeedSource("StartupDaily", "https://www.startupdaily.net/feed/", 
                      "Australian Market", 3, 180,
                      ["australia", "startup", "venture capital", "innovation"])
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for source in sources:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO feed_sources 
                        (name, url, category, priority, update_frequency, keywords, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source.name, source.url, source.category, 
                        source.priority, source.update_frequency,
                        json.dumps(source.keywords), source.active
                    ))
                except sqlite3.IntegrityError:
                    pass  # Source already exists
    
    async def fetch_feed(self, source: FeedSource) -> List[FeedItem]:
        """Fetch and parse RSS feed with intelligent content extraction"""
        try:
            # Parse RSS feed
            feed = feedparser.parse(source.url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {source.name}: {feed.bozo_exception}")
            
            items = []
            for entry in feed.entries[:20]:  # Limit to recent 20 items
                # Extract content with fallback options
                content = getattr(entry, 'content', [])
                if content and hasattr(content[0], 'value'):
                    full_content = content[0].value
                else:
                    full_content = getattr(entry, 'summary', '')
                
                # Clean and extract text
                soup = BeautifulSoup(full_content, 'html.parser')
                clean_content = soup.get_text()
                
                # Generate content hash for deduplication
                content_hash = hashlib.sha256(
                    (entry.title + entry.link).encode('utf-8')
                ).hexdigest()
                
                # Extract keywords and calculate relevance
                keywords = self._extract_keywords(entry.title + " " + clean_content, source.keywords)
                relevance_score = self._calculate_relevance(keywords, source)
                
                # Parse publication date
                published = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                
                item = FeedItem(
                    title=entry.title,
                    url=entry.link,
                    summary=entry.get('summary', '')[:500],  # Truncate summary
                    published=published,
                    source_feed=source.name,
                    category=source.category,
                    relevance_score=relevance_score,
                    keywords=keywords,
                    content_hash=content_hash,
                    full_content=clean_content[:2000]  # Limit content length
                )
                
                items.append(item)
            
            # Update source statistics
            self._update_source_stats(source.name, success=True)
            logger.info(f"Fetched {len(items)} items from {source.name}")
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching feed {source.name}: {e}")
            self._update_source_stats(source.name, success=False)
            return []
    
    def _extract_keywords(self, text: str, source_keywords: List[str]) -> List[str]:
        """Extract relevant keywords using pattern matching and source context"""
        text_lower = text.lower()
        found_keywords = []
        
        # Check for source-specific keywords
        for keyword in source_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        # Industry-specific keyword patterns
        patterns = {
            'technologies': ['kubernetes', 'docker', 'terraform', 'ansible', 'jenkins', 'ci/cd'],
            'management': ['agile', 'scrum', 'kanban', 'okr', 'kpi', '1:1', 'retrospective'],
            'business': ['revenue', 'growth', 'scalability', 'roi', 'acquisition', 'retention'],
            'cloud': ['microservices', 'serverless', 'containers', 'api gateway', 'load balancer'],
            'ai_ml': ['neural network', 'deep learning', 'nlp', 'computer vision', 'llm']
        }
        
        for category, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def _calculate_relevance(self, keywords: List[str], source: FeedSource) -> float:
        """Calculate relevance score based on keywords and source priority"""
        base_score = source.priority * 0.2  # 0.2 to 1.0 based on priority
        
        # Boost score based on keyword matches
        keyword_boost = min(len(keywords) * 0.1, 0.5)  # Max 0.5 boost
        
        # Category-specific multipliers
        category_multipliers = {
            'Engineering Management': 1.2,
            'Cloud Technology': 1.1,
            'AI/ML': 1.15,
            'Business Strategy': 1.0,
            'Australian Market': 1.05
        }
        
        multiplier = category_multipliers.get(source.category, 1.0)
        
        final_score = min((base_score + keyword_boost) * multiplier, 1.0)
        return round(final_score, 3)
    
    def _update_source_stats(self, source_name: str, success: bool):
        """Update source success/error statistics"""
        with sqlite3.connect(self.db_path) as conn:
            if success:
                conn.execute("""
                    UPDATE feed_sources 
                    SET success_count = success_count + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (source_name,))
            else:
                conn.execute("""
                    UPDATE feed_sources 
                    SET error_count = error_count + 1
                    WHERE name = ?
                """, (source_name,))
    
    async def store_items(self, items: List[FeedItem]):
        """Store feed items in database with deduplication"""
        with sqlite3.connect(self.db_path) as conn:
            stored_count = 0
            for item in items:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO feed_items 
                        (title, url, summary, published, source_feed, category, 
                         relevance_score, keywords, content_hash, full_content)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.title, item.url, item.summary, item.published,
                        item.source_feed, item.category, item.relevance_score,
                        json.dumps(item.keywords), item.content_hash, item.full_content
                    ))
                    if conn.total_changes > 0:
                        stored_count += 1
                except sqlite3.IntegrityError:
                    continue  # Duplicate item, skip
            
            if stored_count > 0:
                logger.info(f"Stored {stored_count} new items")
    
    async def get_active_sources(self) -> List[FeedSource]:
        """Get list of active RSS feed sources"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT name, url, category, priority, update_frequency, keywords, active
                FROM feed_sources WHERE active = 1
                ORDER BY priority DESC
            """).fetchall()
            
            sources = []
            for row in rows:
                sources.append(FeedSource(
                    name=row[0], url=row[1], category=row[2],
                    priority=row[3], update_frequency=row[4],
                    keywords=json.loads(row[5]), active=bool(row[6])
                ))
            
            return sources
    
    async def run_intelligence_sweep(self) -> Dict[str, Any]:
        """Run complete intelligence gathering sweep across all sources"""
        logger.info("🔍 Starting intelligence sweep across all RSS sources")
        
        sources = await self.get_active_sources()
        all_items = []
        
        # Process feeds in parallel for high-priority sources
        high_priority_sources = [s for s in sources if s.priority >= 4]
        regular_sources = [s for s in sources if s.priority < 4]
        
        # Fetch high-priority sources first
        logger.info(f"📊 Processing {len(high_priority_sources)} high-priority sources")
        for source in high_priority_sources:
            items = await self.fetch_feed(source)
            all_items.extend(items)
            await asyncio.sleep(0.5)  # Brief pause to avoid overwhelming servers
        
        # Store high-priority items immediately
        await self.store_items(all_items)
        
        # Process regular sources
        logger.info(f"📈 Processing {len(regular_sources)} regular sources")
        regular_items = []
        for source in regular_sources:
            items = await self.fetch_feed(source)
            regular_items.extend(items)
            await asyncio.sleep(1)  # Longer pause for regular sources
        
        await self.store_items(regular_items)
        all_items.extend(regular_items)
        
        # Generate intelligence summary
        summary = self._generate_intelligence_summary(all_items)
        
        logger.info(f"✅ Intelligence sweep complete: {len(all_items)} items processed")
        return summary
    
    def _generate_intelligence_summary(self, items: List[FeedItem]) -> Dict[str, Any]:
        """Generate intelligent summary of collected items"""
        if not items:
            return {"status": "no_items", "message": "No items to analyze"}
        
        # Sort by relevance score
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Category analysis
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        # Extract trending keywords
        all_keywords = []
        for item in items:
            all_keywords.extend(item.keywords)
        
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        trending = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top items by relevance
        top_items = items[:15]
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_items": len(items),
            "high_relevance_items": len([i for i in items if i.relevance_score >= 0.7]),
            "categories": {cat: len(items) for cat, items in categories.items()},
            "trending_keywords": [{"keyword": k, "frequency": f} for k, f in trending],
            "top_items": [
                {
                    "title": item.title,
                    "source": item.source_feed,
                    "category": item.category,
                    "relevance_score": item.relevance_score,
                    "url": item.url,
                    "keywords": item.keywords
                }
                for item in top_items
            ],
            "recommendations": self._generate_recommendations(categories, trending)
        }
        
        return summary
    
    def _generate_recommendations(self, categories: Dict, trending_keywords: List) -> List[str]:
        """Generate actionable recommendations from intelligence data"""
        recommendations = []
        
        # Category-specific recommendations
        if 'Engineering Management' in categories and len(categories['Engineering Management']) > 5:
            recommendations.append("High activity in engineering management content - review latest leadership trends")
        
        if 'Cloud Technology' in categories:
            cloud_items = len(categories['Cloud Technology'])
            if cloud_items > 10:
                recommendations.append("Significant cloud technology updates - consider architecture review")
        
        # Trending keyword recommendations
        trending_words = [k for k, f in trending_keywords[:5]]
        if 'kubernetes' in trending_words:
            recommendations.append("Kubernetes trending - evaluate container orchestration strategy")
        
        if 'ai' in trending_words or 'machine learning' in trending_words:
            recommendations.append("AI/ML topics trending - assess AI integration opportunities")
        
        if not recommendations:
            recommendations.append("Continue monitoring industry trends across all categories")
        
        return recommendations

async def main():
    """Main execution function for testing"""
    monitor = IntelligentRSSMonitor()
    
    print("🚀 Starting Intelligent RSS Monitor")
    summary = await monitor.run_intelligence_sweep()
    
    print("\n📊 Intelligence Summary")
    print("=" * 50)
    print(f"📈 Total items processed: {summary.get('total_items', 0)}")
    print(f"⭐ High relevance items: {summary.get('high_relevance_items', 0)}")
    
    print(f"\n📂 Categories:")
    for category, count in summary.get('categories', {}).items():
        print(f"  • {category}: {count} items")
    
    print(f"\n🔥 Trending Keywords:")
    for trend in summary.get('trending_keywords', [])[:5]:
        print(f"  • {trend['keyword']}: {trend['frequency']} mentions")
    
    print(f"\n💡 Recommendations:")
    for rec in summary.get('recommendations', []):
        print(f"  • {rec}")
    
    print(f"\n⭐ Top Items by Relevance:")
    for item in summary.get('top_items', [])[:5]:
        print(f"  • {item['title']} ({item['relevance_score']}) - {item['source']}")

if __name__ == "__main__":
    asyncio.run(main())