#!/usr/bin/env python3
"""
Security Intelligence Monitor for Maia
=====================================

Monitors AI security threats, prompt injection techniques, and cybersecurity 
advisories to keep Maia's defenses current with evolving threat landscape.
"""

import asyncio
import sqlite3
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys
import feedparser
import hashlib
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Same domain import - direct reference
try:
    from intelligent_rss_monitor import IntelligentRSSMonitor
    RSS_AVAILABLE = True
except ImportError:
    # Graceful fallback for missing intelligent_rss_monitor
    class IntelligentRSSMonitor: 
        pass
    RSS_AVAILABLE = False
    print("⚠️ RSS monitor not available - using fallback mode")

class SecurityIntelligenceMonitor:
    """Monitor security threats and AI vulnerabilities for proactive defense"""
    
    def __init__(self):
        self.db_path = Path("claude/data/security_intelligence.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_security_db()
        
        # Security-focused RSS feeds
        self.security_feeds = {
            'ai_safety': [
                'https://blog.anthropic.com/rss.xml',
                'https://openai.com/blog/rss.xml',
                'https://feeds.feedburner.com/oreilly/radar/tech'
            ],
            'cybersecurity': [
                'https://feeds.feedburner.com/TheHackersNews',
                'https://krebsonsecurity.com/feed/',
                'https://feeds.feedburner.com/securityweek'
            ],
            'ai_research': [
                'https://arxiv.org/rss/cs.AI',
                'https://arxiv.org/rss/cs.CR',  # Cryptography and Security
                'https://arxiv.org/rss/cs.CL'   # Computation and Language
            ]
        }
        
        # Security intelligence keywords
        self.threat_keywords = {
            'prompt_injection': [
                'prompt injection', 'jailbreaking', 'prompt engineering attack',
                'adversarial prompts', 'model manipulation', 'llm attack',
                'ai red team', 'prompt hacking', 'system prompt leak',
                'instruction following attack', 'context hijacking'
            ],
            'ai_security': [
                'ai safety', 'llm security', 'ai vulnerability', 'model safety',
                'ai ethics', 'alignment', 'ai robustness', 'model security',
                'ai governance', 'responsible ai', 'ai risk assessment'
            ],
            'cybersecurity': [
                'cve', 'zero day', 'vulnerability', 'exploit', 'malware',
                'phishing', 'social engineering', 'security advisory',
                'security patch', 'threat intelligence', 'incident response'
            ],
            'api_security': [
                'api security', 'oauth vulnerability', 'jwt exploit',
                'rest api security', 'graphql security', 'webhook security',
                'rate limiting', 'authentication bypass', 'authorization flaw'
            ]
        }
        
        # Injection pattern extraction regex
        self.pattern_extractors = {
            'direct_command': re.compile(r'["\']([^"\']*(?:ignore|forget|override|disregard)[^"\']*)["\']', re.IGNORECASE),
            'role_change': re.compile(r'["\']([^"\']*(?:you are|act as|pretend to be)[^"\']*)["\']', re.IGNORECASE),
            'system_manipulation': re.compile(r'["\']([^"\']*(?:system|instruction|prompt)[^"\']*)["\']', re.IGNORECASE)
        }
        
    def _init_security_db(self):
        """Initialize security intelligence database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS security_threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE,
                    title TEXT,
                    description TEXT,
                    threat_type TEXT,
                    severity TEXT,
                    source_url TEXT,
                    discovered_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS injection_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE,
                    pattern_type TEXT,
                    confidence REAL,
                    source_threat_id INTEGER,
                    effectiveness_rating INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_threat_id) REFERENCES security_threats (id)
                );
                
                CREATE TABLE IF NOT EXISTS security_briefings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    briefing_date TEXT,
                    threat_count INTEGER,
                    new_patterns INTEGER,
                    critical_alerts INTEGER,
                    briefing_content TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS pattern_effectiveness (
                    pattern_id INTEGER,
                    test_date TEXT,
                    detection_rate REAL,
                    false_positive_rate REAL,
                    notes TEXT,
                    FOREIGN KEY (pattern_id) REFERENCES injection_patterns (id)
                );
            ''')
    
    async def scan_security_feeds(self) -> Dict[str, Any]:
        """Scan security feeds for new threats and vulnerabilities"""
        print("🔍 Scanning security intelligence feeds...")
        
        threats_found = []
        new_patterns = []
        
        for category, feeds in self.security_feeds.items():
            for feed_url in feeds:
                try:
                    print(f"  📡 Scanning {category}: {feed_url}")
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:10]:  # Latest 10 entries
                        threat = await self._analyze_security_entry(entry, category)
                        if threat:
                            threats_found.append(threat)
                            
                            # Extract potential injection patterns
                            patterns = self._extract_injection_patterns(entry)
                            new_patterns.extend(patterns)
                            
                except Exception as e:
                    print(f"  ⚠️ Error scanning {feed_url}: {e}")
                    continue
        
        # Store findings
        stored_threats = self._store_security_threats(threats_found)
        stored_patterns = self._store_injection_patterns(new_patterns)
        
        return {
            'scan_date': datetime.now().isoformat(),
            'feeds_scanned': sum(len(feeds) for feeds in self.security_feeds.values()),
            'threats_found': len(threats_found),
            'threats_stored': stored_threats,
            'patterns_found': len(new_patterns),
            'patterns_stored': stored_patterns,
            'categories': list(self.security_feeds.keys())
        }
    
    async def _analyze_security_entry(self, entry: Any, category: str) -> Optional[Dict]:
        """Analyze RSS entry for security relevance"""
        content = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        
        # Check for security keywords
        threat_type = None
        severity = 'low'
        
        for ttype, keywords in self.threat_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in content)
            if matches >= 2:  # Multiple keyword matches
                threat_type = ttype
                severity = 'high' if matches >= 4 else 'medium'
                break
            elif matches == 1:
                threat_type = ttype
                severity = 'low'
        
        if not threat_type:
            return None
            
        return {
            'title': entry.get('title', ''),
            'description': entry.get('summary', ''),
            'threat_type': threat_type,
            'severity': severity,
            'source_url': entry.get('link', ''),
            'discovered_date': entry.get('published', ''),
            'category': category
        }
    
    def _extract_injection_patterns(self, entry: Any) -> List[Dict]:
        """Extract potential injection patterns from security content"""
        content = f"{entry.get('title', '')} {entry.get('summary', '')}"
        patterns = []
        
        for pattern_type, regex in self.pattern_extractors.items():
            matches = regex.findall(content)
            for match in matches:
                if len(match) > 10 and len(match) < 200:  # Reasonable length
                    patterns.append({
                        'pattern': match,
                        'pattern_type': pattern_type,
                        'confidence': 0.7,  # Medium confidence from research
                        'source_url': entry.get('link', '')
                    })
        
        return patterns
    
    def _store_security_threats(self, threats: List[Dict]) -> int:
        """Store security threats in database"""
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for threat in threats:
                # Create hash for deduplication
                content_hash = hashlib.md5(
                    f"{threat['title']}{threat['source_url']}".encode()
                ).hexdigest()
                
                try:
                    conn.execute('''
                        INSERT INTO security_threats 
                        (content_hash, title, description, threat_type, severity, source_url, discovered_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        content_hash, threat['title'], threat['description'],
                        threat['threat_type'], threat['severity'], 
                        threat['source_url'], threat['discovered_date']
                    ))
                    stored_count += 1
                except sqlite3.IntegrityError:
                    # Already exists
                    continue
                    
        return stored_count
    
    def _store_injection_patterns(self, patterns: List[Dict]) -> int:
        """Store injection patterns for potential defense updates"""
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for pattern in patterns:
                try:
                    conn.execute('''
                        INSERT INTO injection_patterns 
                        (pattern, pattern_type, confidence)
                        VALUES (?, ?, ?)
                    ''', (pattern['pattern'], pattern['pattern_type'], pattern['confidence']))
                    stored_count += 1
                except sqlite3.IntegrityError:
                    # Already exists
                    continue
                    
        return stored_count
    
    def get_security_briefing(self, days: int = 7) -> Dict[str, Any]:
        """Generate security intelligence briefing"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Get recent threats
            threats = conn.execute('''
                SELECT threat_type, severity, COUNT(*) as count
                FROM security_threats 
                WHERE created_at >= ?
                GROUP BY threat_type, severity
                ORDER BY count DESC
            ''', (start_date.isoformat(),)).fetchall()
            
            # Get new patterns
            patterns = conn.execute('''
                SELECT pattern_type, COUNT(*) as count
                FROM injection_patterns
                WHERE created_at >= ?
                GROUP BY pattern_type
                ORDER BY count DESC
            ''', (start_date.isoformat(),)).fetchall()
            
            # Get critical alerts
            critical = conn.execute('''
                SELECT title, threat_type, source_url
                FROM security_threats
                WHERE severity = 'high' AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (start_date.isoformat(),)).fetchall()
        
        return {
            'period': f'{days} days',
            'threats_by_type': dict((f"{t[0]}_{t[1]}", t[2]) for t in threats),
            'patterns_by_type': dict(patterns),
            'critical_alerts': [{'title': c[0], 'type': c[1], 'url': c[2]} for c in critical],
            'total_threats': sum(t[2] for t in threats),
            'total_patterns': sum(p[1] for p in patterns),
            'generated_at': datetime.now().isoformat()
        }
    
    def suggest_pattern_updates(self) -> List[Dict]:
        """Suggest new patterns for prompt injection defense"""
        with sqlite3.connect(self.db_path) as conn:
            # Get high-confidence patterns not yet deployed
            patterns = conn.execute('''
                SELECT pattern, pattern_type, confidence, COUNT(*) as frequency
                FROM injection_patterns
                WHERE confidence >= 0.6
                GROUP BY pattern, pattern_type
                HAVING frequency >= 2
                ORDER BY confidence DESC, frequency DESC
                LIMIT 10
            ''').fetchall()
        
        suggestions = []
        for pattern, ptype, confidence, freq in patterns:
            suggestions.append({
                'pattern': pattern,
                'type': ptype,
                'confidence': confidence,
                'frequency': freq,
                'recommended_action': 'add_to_defense' if confidence >= 0.8 else 'test_first'
            })
        
        return suggestions

def main():
    """Main execution for security intelligence monitoring"""
    monitor = SecurityIntelligenceMonitor()
    
    import argparse
    parser = argparse.ArgumentParser(description='Security Intelligence Monitor')
    parser.add_argument('--scan', action='store_true', help='Scan security feeds')
    parser.add_argument('--briefing', type=int, default=7, help='Generate briefing for N days')
    parser.add_argument('--patterns', action='store_true', help='Suggest pattern updates')
    
    args = parser.parse_args()
    
    if args.scan:
        print("🛡️ Security Intelligence Monitor - Feed Scan")
        print("=" * 50)
        result = asyncio.run(monitor.scan_security_feeds())
        print(f"✅ Scan complete:")
        print(f"   📡 Feeds scanned: {result['feeds_scanned']}")
        print(f"   🚨 Threats found: {result['threats_found']} (stored: {result['threats_stored']})")
        print(f"   🎯 Patterns found: {result['patterns_found']} (stored: {result['patterns_stored']})")
        
    elif args.patterns:
        print("🎯 Pattern Update Suggestions")
        print("=" * 30)
        suggestions = monitor.suggest_pattern_updates()
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion['type']}: {suggestion['pattern'][:50]}...")
            print(f"   Confidence: {suggestion['confidence']:.1f}, Action: {suggestion['recommended_action']}")
        
    else:
        print("📊 Security Intelligence Briefing")
        print("=" * 35)
        briefing = monitor.get_security_briefing(args.briefing)
        print(f"Period: {briefing['period']}")
        print(f"Total threats: {briefing['total_threats']}")
        print(f"New patterns: {briefing['total_patterns']}")
        print(f"Critical alerts: {len(briefing['critical_alerts'])}")
        
        if briefing['critical_alerts']:
            print("\n🚨 Critical Alerts:")
            for alert in briefing['critical_alerts']:
                print(f"  • {alert['title'][:60]}...")

if __name__ == "__main__":
    main()