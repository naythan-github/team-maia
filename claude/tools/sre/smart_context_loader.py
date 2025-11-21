#!/usr/bin/env python3
"""
Smart Context Loader - Intent-Aware SYSTEM_STATE.md Loading

Intelligently loads relevant portions of SYSTEM_STATE.md based on query intent,
complexity, and domain. Prevents token overflow (42K+ → 5-20K adaptive loading).

Part of Phase 2: SYSTEM_STATE Intelligent Loading Project
Enhanced in Phase 165: Database-accelerated queries (100x faster)

Usage:
    from claude.tools.sre.smart_context_loader import SmartContextLoader

    loader = SmartContextLoader()
    context = loader.load_for_intent("Continue agent enhancement work")
    # Returns: Phase 2 + Phases 107-111 only (2,500 tokens)

    context = loader.load_for_intent("Why is health monitor failing?")
    # Returns: Phase 103-105 + LaunchAgent docs (3,800 tokens)

Features:
    - Intent-based phase selection (agent enhancement → Phase 2, 107-111)
    - Complexity-based depth control (simple → 10 phases, complex → 20)
    - Domain-specific loading (SRE → 103-105, Azure → 102, etc.)
    - Token budget enforcement (never exceed 20K tokens)
    - Database-accelerated queries (0.2ms vs 100-500ms) - Phase 165
    - Graceful fallback to markdown if database unavailable
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Try importing intent classifier (Phase 111 infrastructure)
try:
    import sys
    maia_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(maia_root / "tools"))
    from intent_classifier import IntentClassifier, Intent
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False
    Intent = None

# Try importing database query interface (Phase 165 infrastructure)
try:
    from system_state_queries import SystemStateQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class ContextLoadResult:
    """Result from smart context loading"""
    content: str
    phases_loaded: List[int]
    token_count: int
    loading_strategy: str
    intent_classification: Optional[Dict[str, Any]]


class SmartContextLoader:
    """
    Intelligently loads SYSTEM_STATE.md context based on query intent.

    Reduces token usage from 42K+ (full file) to 5-20K (targeted loading).
    """

    def __init__(self, maia_root: Optional[Path] = None):
        if maia_root is None:
            # Tool is in claude/tools/sre/, need to go up 3 levels to repo root
            self.maia_root = Path(__file__).resolve().parent.parent.parent.parent
        else:
            self.maia_root = Path(maia_root)

        self.system_state_path = self.maia_root / "SYSTEM_STATE.md"
        self.db_path = self.maia_root / "claude" / "data" / "databases" / "system" / "system_state.db"
        self.token_budget_max = 20000  # Maximum tokens (80% of Read tool limit)
        self.token_budget_default = 10000  # Default for standard queries

        # Initialize intent classifier if available
        self.intent_classifier = IntentClassifier() if INTENT_CLASSIFIER_AVAILABLE else None

        # Initialize database query interface if available
        self.db_queries = None
        self.use_database = False
        if DB_QUERIES_AVAILABLE and self.db_path.exists():
            try:
                self.db_queries = SystemStateQueries(self.db_path)
                self.use_database = True
                logger.info(f"Database queries enabled: {self.db_path}")
            except Exception as e:
                logger.warning(f"Database initialization failed, using markdown fallback: {e}")
                self.use_database = False
        else:
            if not DB_QUERIES_AVAILABLE:
                logger.debug("Database queries module not available")
            elif not self.db_path.exists():
                logger.debug(f"Database not found: {self.db_path}")

    def load_for_intent(self, user_query: str) -> ContextLoadResult:
        """
        Load context optimized for user query intent.

        Args:
            user_query: Natural language query from user

        Returns:
            ContextLoadResult with content, phases loaded, token count, strategy
        """
        # Step 1: Classify intent (if classifier available)
        intent = None
        if self.intent_classifier:
            intent = self.intent_classifier.classify(user_query)

        # Step 2: Determine loading strategy based on intent
        strategy, phases = self._determine_strategy(user_query, intent)

        # Step 3: Calculate token budget
        budget = self._calculate_token_budget(user_query, intent)

        # Step 4: Load selected phases
        content = self._load_phases(phases, budget)

        # Step 5: Estimate token count (rough: 4 chars per token)
        token_count = len(content) // 4

        return ContextLoadResult(
            content=content,
            phases_loaded=phases,
            token_count=token_count,
            loading_strategy=strategy,
            intent_classification=self._intent_to_dict(intent) if intent else None
        )

    def _determine_strategy(
        self,
        user_query: str,
        intent: Optional[Intent]
    ) -> Tuple[str, List[int]]:
        """
        Determine loading strategy and phase selection.

        Returns:
            (strategy_name, phase_numbers_to_load)
        """
        query_lower = user_query.lower()

        # Strategy 1: Agent Enhancement Queries
        if any(kw in query_lower for kw in ['agent', 'enhancement', 'upgrade', 'v2.2', 'template', 'few-shot', 'prompt']):
            # Check if agent-related query (intent domains OR keyword match)
            if (intent and 'agents' in intent.domains) or any(kw in query_lower for kw in ['agent', 'enhancement', 'upgrade']):
                return ("agent_enhancement", [2, 107, 108, 109, 110, 111])

        # Strategy 2: SRE/Reliability Queries
        if any(kw in query_lower for kw in ['sre', 'reliability', 'health', 'launchagent', 'service', 'monitor', 'fail']):
            # Check if SRE-related query (intent domains OR keyword match)
            if (intent and ('sre' in intent.domains or 'reliability' in intent.domains)) or \
               any(kw in query_lower for kw in ['health', 'launchagent', 'monitor', 'sre']):
                return ("sre_reliability", [103, 104, 105])

        # Strategy 3: Voice Dictation Queries
        if any(kw in query_lower for kw in ['whisper', 'voice', 'dictation', 'audio']):
            return ("voice_dictation", [101])

        # Strategy 4: Conversation Persistence Queries
        if any(kw in query_lower for kw in ['conversation', 'rag', 'persistence', 'save']):
            return ("conversation_persistence", [101, 102])

        # Strategy 5: Service Desk Queries
        if any(kw in query_lower for kw in ['service desk', 'l1', 'l2', 'l3', 'escalation']):
            return ("service_desk", [100])

        # Strategy 6: High Complexity Strategic Queries
        if intent and intent.complexity >= 8:
            # Load recent 20 phases for strategic planning
            recent_phases = self._get_recent_phases(20)
            return ("strategic_planning", recent_phases)

        # Strategy 7: Moderate Complexity Queries
        if intent and intent.complexity >= 5:
            # Load recent 15 phases
            recent_phases = self._get_recent_phases(15)
            return ("moderate_complexity", recent_phases)

        # Strategy 8: Default (Simple Queries)
        # Load header + recent 10 phases
        recent_phases = self._get_recent_phases(10)
        return ("default", recent_phases)

    def _calculate_token_budget(
        self,
        user_query: str,
        intent: Optional[Intent]
    ) -> int:
        """
        Calculate token budget based on query complexity.

        Returns:
            Token budget (5K-20K range)
        """
        if not intent:
            return self.token_budget_default

        # Base budget on complexity
        if intent.complexity >= 9:
            budget = 20000  # Maximum for very complex
        elif intent.complexity >= 7:
            budget = 15000  # High complexity
        elif intent.complexity >= 5:
            budget = 10000  # Standard
        else:
            budget = 5000   # Simple queries

        # Adjust for category
        if intent.category == 'strategic_planning':
            budget = min(int(budget * 1.5), 20000)
        elif intent.category == 'operational_task':
            budget = min(int(budget * 0.8), 15000)

        return budget

    def _get_recent_phases(self, count: int = 10) -> List[int]:
        """
        Get list of most recent phase numbers.

        Args:
            count: Number of recent phases to return

        Returns:
            List of phase numbers (e.g., [111, 110, 109, ...])
        """
        # Parse all phase numbers from file
        content = self.system_state_path.read_text()
        phase_pattern = re.compile(r'^##\s+[🔬🚀🎯🤖💼📋🎓🔗🛡️🎤📊🧠].+PHASE\s+(\d+):', re.MULTILINE | re.IGNORECASE)

        matches = phase_pattern.findall(content)
        phase_numbers = sorted(set(int(m) for m in matches), reverse=True)

        return phase_numbers[:count]

    def _load_phases_from_db(self, phase_numbers: List[int], token_budget: int) -> str:
        """
        Load phases from database (fast path - Phase 165).

        Args:
            phase_numbers: List of phase numbers to load
            token_budget: Maximum tokens to load

        Returns:
            Content string formatted as markdown
        """
        if not self.use_database or not self.db_queries:
            raise RuntimeError("Database not available")

        # Query database for requested phases
        phases = self.db_queries.get_phases_by_number(phase_numbers)

        if not phases:
            # No phases found in DB, fall back to markdown
            logger.warning(f"No phases found in database for {phase_numbers}, falling back to markdown")
            return self._load_phases_from_markdown(phase_numbers, token_budget)

        # Format as markdown with token budget enforcement
        markdown = self.db_queries.format_phases_as_markdown(phases)

        # Truncate if exceeds budget
        if len(markdown) // 4 > token_budget:
            # Remove phases until under budget
            truncated_phases = []
            current_tokens = 0

            for phase in phases:
                phase_md = self.db_queries.format_phase_as_markdown(phase)
                phase_tokens = len(phase_md) // 4

                if current_tokens + phase_tokens <= token_budget:
                    truncated_phases.append(phase)
                    current_tokens += phase_tokens
                else:
                    break

            markdown = self.db_queries.format_phases_as_markdown(truncated_phases)
            logger.info(f"Truncated to {len(truncated_phases)}/{len(phases)} phases for token budget")

        return markdown

    def _load_phases_from_markdown(self, phase_numbers: List[int], token_budget: int) -> str:
        """
        Load phases by parsing markdown file (fallback path).

        Args:
            phase_numbers: List of phase numbers to load
            token_budget: Maximum tokens to load

        Returns:
            Content string with header + selected phases
        """
        content = self.system_state_path.read_text()
        lines = content.splitlines()

        # Always include header (first ~8 lines before first phase)
        phase_pattern = re.compile(r'^##\s+[🔬🚀🎯🤖💼📋🎓🔗🛡️🎤📊🧠🗄️].+PHASE\s+\d+:', re.IGNORECASE)

        header_end = 0
        for i, line in enumerate(lines):
            if phase_pattern.match(line):
                header_end = i
                break

        header = '\n'.join(lines[:header_end])

        # Extract requested phases
        phase_sections = []
        current_phase_num = None
        current_phase_start = None

        for i, line in enumerate(lines):
            match = re.match(r'^##\s+[🔬🚀🎯🤖💼📋🎓🔗🛡️🎤📊🧠🗄️].+PHASE\s+(\d+):', line, re.IGNORECASE)
            if match:
                # Save previous phase if it's in our list
                if current_phase_num and current_phase_num in phase_numbers:
                    phase_content = '\n'.join(lines[current_phase_start:i])
                    phase_sections.append((current_phase_num, phase_content))

                # Start new phase
                current_phase_num = int(match.group(1))
                current_phase_start = i

        # Don't forget last phase
        if current_phase_num and current_phase_num in phase_numbers:
            phase_content = '\n'.join(lines[current_phase_start:])
            phase_sections.append((current_phase_num, phase_content))

        # Sort by phase number (descending - most recent first)
        phase_sections.sort(key=lambda x: x[0], reverse=True)

        # Combine with token budget enforcement
        combined = header + '\n\n'
        current_tokens = len(combined) // 4

        for phase_num, phase_content in phase_sections:
            phase_tokens = len(phase_content) // 4

            if current_tokens + phase_tokens <= token_budget:
                combined += phase_content + '\n\n---\n\n'
                current_tokens += phase_tokens
            else:
                # Budget exceeded, stop adding phases
                break

        return combined.strip()

    def _load_phases(self, phase_numbers: List[int], token_budget: int) -> str:
        """
        Load phases using best available method (DB or markdown).

        Routes to database query (fast) or markdown parsing (fallback).

        Args:
            phase_numbers: List of phase numbers to load
            token_budget: Maximum tokens to load

        Returns:
            Content string with selected phases
        """
        if self.use_database:
            try:
                return self._load_phases_from_db(phase_numbers, token_budget)
            except Exception as e:
                logger.warning(f"Database query failed, falling back to markdown: {e}")
                return self._load_phases_from_markdown(phase_numbers, token_budget)
        else:
            return self._load_phases_from_markdown(phase_numbers, token_budget)

    def _intent_to_dict(self, intent: Intent) -> Dict[str, Any]:
        """Convert Intent dataclass to dictionary for serialization."""
        if not intent:
            return None

        return {
            'category': intent.category,
            'domains': intent.domains,
            'complexity': intent.complexity,
            'confidence': intent.confidence,
            'entities': intent.entities
        }

    def load_recent_phases(self, count: int = 10) -> str:
        """
        Simple interface: Load recent N phases.

        Args:
            count: Number of recent phases to load

        Returns:
            Content string
        """
        phases = self._get_recent_phases(count)
        return self._load_phases(phases, self.token_budget_default)

    def load_specific_phases(self, phase_numbers: List[int]) -> str:
        """
        Simple interface: Load specific phases by number.

        Args:
            phase_numbers: List of phase numbers (e.g., [2, 107, 108])

        Returns:
            Content string
        """
        return self._load_phases(phase_numbers, self.token_budget_default)


def main():
    """CLI interface for testing smart context loader."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart Context Loader - Intent-aware SYSTEM_STATE.md loading"
    )
    parser.add_argument(
        'query',
        nargs='?',
        default="What's the current status?",
        help='User query to classify and load context for'
    )
    parser.add_argument(
        '--phases',
        type=int,
        nargs='+',
        help='Load specific phase numbers (e.g., --phases 2 107 108)'
    )
    parser.add_argument(
        '--recent',
        type=int,
        metavar='N',
        help='Load recent N phases'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show loading statistics only (no content)'
    )

    args = parser.parse_args()

    loader = SmartContextLoader()

    if args.phases:
        # Load specific phases
        print(f"Loading specific phases: {args.phases}")
        content = loader.load_specific_phases(args.phases)
        result = ContextLoadResult(
            content=content,
            phases_loaded=args.phases,
            token_count=len(content) // 4,
            loading_strategy="specific_phases",
            intent_classification=None
        )
    elif args.recent:
        # Load recent N phases
        print(f"Loading recent {args.recent} phases")
        content = loader.load_recent_phases(args.recent)
        phases = loader._get_recent_phases(args.recent)
        result = ContextLoadResult(
            content=content,
            phases_loaded=phases,
            token_count=len(content) // 4,
            loading_strategy="recent_phases",
            intent_classification=None
        )
    else:
        # Intent-based loading
        print(f"Query: {args.query}")
        result = loader.load_for_intent(args.query)

    # Show statistics
    print(f"\n📊 Loading Statistics:")
    print(f"  Strategy: {result.loading_strategy}")
    print(f"  Phases loaded: {result.phases_loaded}")
    print(f"  Token count: {result.token_count:,} (~{result.token_count/1000:.1f}K)")
    print(f"  Content size: {len(result.content):,} chars")

    if result.intent_classification:
        print(f"\n🎯 Intent Classification:")
        print(f"  Category: {result.intent_classification['category']}")
        print(f"  Domains: {', '.join(result.intent_classification['domains'])}")
        print(f"  Complexity: {result.intent_classification['complexity']}/10")
        print(f"  Confidence: {result.intent_classification['confidence']:.1%}")

    if not args.stats:
        print(f"\n📄 Content Preview (first 500 chars):")
        print(result.content[:500])
        print("...")


if __name__ == '__main__':
    main()
