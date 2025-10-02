#!/usr/bin/env python3
"""
Smart Research Manager - Knowledge Enhancement Hybrid Approach

Extends Maia's Personal Knowledge Graph to implement intelligent research
retention vs. refresh strategy, solving the 40-60% research waste problem.

Key Features:
- Information stability-based refresh cycles
- Automatic staleness detection
- Token optimization through smart caching
- Integration with existing research agents
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Import existing Maia infrastructure with graceful fallbacks
try:
    # Cross-domain import via emoji resolver
    import sys
    from pathlib import Path
    emoji_tools_dir = Path(__file__).parent.parent / "📊_data"
    sys.path.insert(0, str(emoji_tools_dir))
    try:
        from personal_knowledge_graph_optimized import PersonalKnowledgeGraph, NodeType, get_knowledge_graph
    finally:
        if str(emoji_tools_dir) in sys.path:
            sys.path.remove(str(emoji_tools_dir))
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError:
    # Graceful fallback for missing personal_knowledge_graph_optimized
    class PersonalKnowledgeGraph: pass
    class NodeType: pass
    def get_knowledge_graph(): return None
    KNOWLEDGE_GRAPH_AVAILABLE = False

try:
    # Core utility import from general domain
    import sys
    from pathlib import Path
    general_tools_dir = Path(__file__).parent.parent / "🛠️_general"
    sys.path.insert(0, str(general_tools_dir))
    try:
        from intelligent_assistant_hub import get_assistant_hub
    finally:
        if str(general_tools_dir) in sys.path:
            sys.path.remove(str(general_tools_dir))
    ASSISTANT_HUB_AVAILABLE = True
except ImportError:
    # Graceful fallback for missing intelligent_assistant_hub
    def get_assistant_hub(): return None
    ASSISTANT_HUB_AVAILABLE = False

# Import unified research interface for integration
try:
    # Same domain import - direct reference
    from unified_research_interface import UnifiedResearchInterface
    UNIFIED_RESEARCH_AVAILABLE = True
except ImportError:
    # Graceful fallback for missing unified_research_interface
    class UnifiedResearchInterface: pass
    UNIFIED_RESEARCH_AVAILABLE = False

# Import core utilities with new import system
try:
    from claude.core import get_path_manager
    PATH_MANAGER_AVAILABLE = True
except ImportError:
    PATH_MANAGER_AVAILABLE = False
    def get_path_manager():
        return None


class StabilityTier(Enum):
    """Information stability classification for refresh cycles"""
    FOUNDATION = "foundation"      # 12+ months: company structure, leadership backgrounds
    STRATEGIC = "strategic"        # 3-6 months: initiatives, organizational changes
    DYNAMIC = "dynamic"           # weekly/monthly: news, financial performance
    REAL_TIME = "real_time"       # daily: stock price, job postings


class RefreshTrigger(Enum):
    """Events that invalidate cached research"""
    LEADERSHIP_CHANGE = "leadership_change"
    ACQUISITION = "acquisition"
    STRATEGIC_PIVOT = "strategic_pivot"
    FINANCIAL_EVENT = "financial_event"
    ORGANIZATIONAL_RESTRUCTURE = "org_restructure"
    JOB_OPPORTUNITY = "job_opportunity"
    USER_REQUEST = "user_request"


@dataclass
class ResearchMetadata:
    """Metadata for tracking research freshness and optimization"""
    stability_tier: StabilityTier
    last_refresh: datetime
    refresh_cycle_days: int
    token_cost: int
    confidence_score: float
    source_agent: str
    trigger_events: List[RefreshTrigger] = field(default_factory=list)
    refresh_count: int = 0

    @property
    def is_stale(self) -> bool:
        """Check if research has exceeded its refresh cycle"""
        age_days = (datetime.now() - self.last_refresh).days
        return age_days > self.refresh_cycle_days

    @property
    def staleness_factor(self) -> float:
        """Calculate staleness as ratio of age to cycle"""
        age_days = (datetime.now() - self.last_refresh).days
        return age_days / self.refresh_cycle_days


class SmartResearchManager:
    """
    Intelligent research management system that optimizes between fresh data and efficiency
    """

    def __init__(self, base_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "claude/data/research_cache.db"
        self.setup_database()

        # Refresh cycle defaults by stability tier (days)
        self.refresh_cycles = {
            StabilityTier.FOUNDATION: 365,    # Annual refresh for stable info
            StabilityTier.STRATEGIC: 90,      # Quarterly for strategic changes
            StabilityTier.DYNAMIC: 30,        # Monthly for dynamic info
            StabilityTier.REAL_TIME: 1        # Daily for volatile data
        }

        # Token cost estimates for different research depths
        self.token_costs = {
            "full_research": 20000,
            "strategic_refresh": 8000,
            "dynamic_refresh": 3000,
            "real_time_update": 1000
        }

    def setup_database(self):
        """Initialize SQLite database for research cache"""
        self.db_path.parent.mkdir(exist_ok=True, parents=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_cache (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    stability_tier TEXT NOT NULL,
                    last_refresh TIMESTAMP NOT NULL,
                    refresh_cycle_days INTEGER NOT NULL,
                    token_cost INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    source_agent TEXT NOT NULL,
                    research_data TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS refresh_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_data TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (entity_id) REFERENCES research_cache (entity_id)
                )
            """)

    def should_refresh_research(self, entity_id: str, request_context: Dict = None) -> Dict[str, Any]:
        """
        Smart decision engine: determine whether to refresh research or use cached

        Returns decision with reasoning for transparency
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT entity_type, entity_name, stability_tier, last_refresh,
                       refresh_cycle_days, token_cost, confidence_score, source_agent,
                       research_data
                FROM research_cache
                WHERE entity_id = ?
            """, (entity_id,))

            cached_research = cursor.fetchone()

            if not cached_research:
                return {
                    "decision": "full_research",
                    "reason": "No cached research found",
                    "estimated_tokens": self.token_costs["full_research"],
                    "priority": "high"
                }

            # Parse cached metadata
            entity_type, entity_name, tier_str, last_refresh_str, cycle_days, \
            cached_tokens, confidence, source_agent, research_data = cached_research

            tier = StabilityTier(tier_str)
            last_refresh = datetime.fromisoformat(last_refresh_str)
            age_days = (datetime.now() - last_refresh).days

            # Check for active trigger events
            trigger_cursor = conn.execute("""
                SELECT trigger_type, trigger_data FROM refresh_triggers
                WHERE entity_id = ? AND processed = FALSE
                ORDER BY detected_at DESC
            """, (entity_id,))

            active_triggers = trigger_cursor.fetchall()

            # Decision logic
            decision_factors = {
                "age_days": age_days,
                "cycle_days": cycle_days,
                "staleness_ratio": age_days / cycle_days,
                "active_triggers": len(active_triggers),
                "confidence": confidence,
                "tier": tier.value
            }

            # High priority triggers force refresh regardless of age
            high_priority_triggers = [
                RefreshTrigger.LEADERSHIP_CHANGE.value,
                RefreshTrigger.ACQUISITION.value,
                RefreshTrigger.JOB_OPPORTUNITY.value
            ]

            if any(trigger[0] in high_priority_triggers for trigger in active_triggers):
                return {
                    "decision": "targeted_refresh",
                    "reason": f"High priority trigger detected: {active_triggers[0][0]}",
                    "scope": "strategic_and_dynamic",
                    "estimated_tokens": self.token_costs["strategic_refresh"],
                    "priority": "high",
                    "factors": decision_factors
                }

            # Age-based refresh decision
            if age_days > cycle_days:
                if tier == StabilityTier.FOUNDATION:
                    return {
                        "decision": "full_research",
                        "reason": f"Foundation tier research stale ({age_days} days old)",
                        "estimated_tokens": self.token_costs["full_research"],
                        "priority": "medium",
                        "factors": decision_factors
                    }
                elif tier == StabilityTier.STRATEGIC:
                    return {
                        "decision": "strategic_refresh",
                        "reason": f"Strategic tier research needs update ({age_days} days old)",
                        "estimated_tokens": self.token_costs["strategic_refresh"],
                        "priority": "medium",
                        "factors": decision_factors
                    }
                else:  # DYNAMIC or REAL_TIME
                    return {
                        "decision": "dynamic_refresh",
                        "reason": f"Dynamic tier research stale ({age_days} days old)",
                        "estimated_tokens": self.token_costs["dynamic_refresh"],
                        "priority": "low",
                        "factors": decision_factors
                    }

            # Research is current - use cached
            return {
                "decision": "use_cached",
                "reason": f"Research is current ({age_days} days old, cycle: {cycle_days} days)",
                "estimated_tokens": 500,  # Minimal tokens for cache retrieval
                "priority": "none",
                "factors": decision_factors,
                "cached_data": research_data
            }

    def cache_research_results(self, entity_id: str, entity_type: str, entity_name: str,
                             research_data: Dict, metadata: ResearchMetadata) -> bool:
        """Store research results with metadata for future use"""

        # Convert metadata to JSON-serializable format
        metadata_dict = asdict(metadata)
        metadata_dict['stability_tier'] = metadata.stability_tier.value
        metadata_dict['last_refresh'] = metadata.last_refresh.isoformat()
        metadata_dict['trigger_events'] = [event.value if hasattr(event, 'value') else event for event in metadata.trigger_events]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO research_cache
                (entity_id, entity_type, entity_name, stability_tier, last_refresh,
                 refresh_cycle_days, token_cost, confidence_score, source_agent,
                 research_data, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                entity_id, entity_type, entity_name, metadata.stability_tier.value,
                metadata.last_refresh.isoformat(), metadata.refresh_cycle_days,
                metadata.token_cost, metadata.confidence_score, metadata.source_agent,
                json.dumps(research_data), json.dumps(metadata_dict)
            ))

            return True

    def get_research_summary(self, entity_id: str = None) -> Dict[str, Any]:
        """Get summary of cached research and optimization metrics"""

        with sqlite3.connect(self.db_path) as conn:
            if entity_id:
                cursor = conn.execute("""
                    SELECT * FROM research_cache WHERE entity_id = ?
                """, (entity_id,))
            else:
                cursor = conn.execute("SELECT * FROM research_cache")

            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            research_items = []
            total_tokens_saved = 0

            for row in results:
                item = dict(zip(columns, row))

                # Calculate potential token savings
                age_days = (datetime.now() - datetime.fromisoformat(item['last_refresh'])).days
                if age_days < item['refresh_cycle_days']:
                    # Research is current, tokens saved by using cache
                    tokens_saved = self.token_costs["full_research"] - 500
                    total_tokens_saved += tokens_saved
                    item['tokens_saved'] = tokens_saved
                    item['status'] = 'current'
                else:
                    item['tokens_saved'] = 0
                    item['status'] = 'stale'

                research_items.append(item)

            return {
                "total_cached_entities": len(research_items),
                "total_tokens_saved": total_tokens_saved,
                "current_items": len([i for i in research_items if i['status'] == 'current']),
                "stale_items": len([i for i in research_items if i['status'] == 'stale']),
                "research_items": research_items
            }

    def add_trigger_event(self, entity_id: str, trigger_type: RefreshTrigger,
                         trigger_data: Dict = None) -> bool:
        """Register a trigger event that may invalidate cached research"""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO refresh_triggers (entity_id, trigger_type, trigger_data)
                VALUES (?, ?, ?)
            """, (entity_id, trigger_type.value, json.dumps(trigger_data or {})))

            return True

    def get_optimization_report(self) -> str:
        """Generate human-readable optimization report"""
        summary = self.get_research_summary()

        report = f"""
🧠 Smart Research Manager - Optimization Report

📊 Cache Performance:
- Total Cached Entities: {summary['total_cached_entities']}
- Current Research Items: {summary['current_items']}
- Stale Items Needing Refresh: {summary['stale_items']}
- Total Tokens Saved: {summary['total_tokens_saved']:,}

💡 Efficiency Gains:
- Cache Hit Rate: {(summary['current_items'] / max(summary['total_cached_entities'], 1)) * 100:.1f}%
- Estimated Cost Savings: ${summary['total_tokens_saved'] * 0.01:.2f} (at $10/1M tokens)

🎯 Next Actions:
"""

        stale_count = summary['stale_items']
        if stale_count > 0:
            report += f"- {stale_count} entities need research refresh\n"
        else:
            report += "- All research is current ✅\n"

        if summary['total_tokens_saved'] > 50000:
            report += "- Significant optimization achieved - system is highly efficient\n"

        return report


# Global instance
_research_manager = None

def get_research_manager() -> SmartResearchManager:
    """Get global research manager instance"""
    global _research_manager
    if _research_manager is None:
        _research_manager = SmartResearchManager()
    return _research_manager


def main():
    """CLI interface for Smart Research Manager"""
    import sys

    manager = get_research_manager()

    if len(sys.argv) < 2:
        print("Usage: python smart_research_manager.py [command] [args...]")
        print("Commands: check <entity_id>, summary, report")
        return

    command = sys.argv[1]

    if command == "check" and len(sys.argv) > 2:
        entity_id = sys.argv[2]
        decision = manager.should_refresh_research(entity_id)
        print(json.dumps(decision, indent=2))

    elif command == "summary":
        summary = manager.get_research_summary()
        print(json.dumps(summary, indent=2))

    elif command == "report":
        report = manager.get_optimization_report()
        print(report)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
