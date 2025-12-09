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

# Try importing capabilities registry (Phase 168 infrastructure)
try:
    from capabilities_registry import CapabilitiesRegistry
    CAPABILITIES_REGISTRY_AVAILABLE = True
except ImportError:
    try:
        # Fallback: Try importing from same directory using path manipulation
        import sys
        _sre_tools_path = str(Path(__file__).resolve().parent)
        if _sre_tools_path not in sys.path:
            sys.path.insert(0, _sre_tools_path)
        from capabilities_registry import CapabilitiesRegistry
        CAPABILITIES_REGISTRY_AVAILABLE = True
    except ImportError:
        CAPABILITIES_REGISTRY_AVAILABLE = False

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
    memory_context: Optional[str] = None  # Phase 220: Cross-session memory


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
        self.capabilities_db_path = self.maia_root / "claude" / "data" / "databases" / "system" / "capabilities.db"
        self.capability_index_path = self.maia_root / "claude" / "context" / "core" / "capability_index.md"
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

        # Initialize capabilities registry if available (Phase 168)
        self.capabilities_registry = None
        self.use_capabilities_db = False
        if CAPABILITIES_REGISTRY_AVAILABLE and self.capabilities_db_path.exists():
            try:
                self.capabilities_registry = CapabilitiesRegistry(self.capabilities_db_path)
                self.use_capabilities_db = True
                logger.info(f"Capabilities registry enabled: {self.capabilities_db_path}")
            except Exception as e:
                logger.warning(f"Capabilities registry initialization failed, using markdown fallback: {e}")
                self.use_capabilities_db = False
        else:
            if not CAPABILITIES_REGISTRY_AVAILABLE:
                logger.debug("Capabilities registry module not available")
            elif not self.capabilities_db_path.exists():
                logger.debug(f"Capabilities database not found: {self.capabilities_db_path}")

    def load_for_intent(self, user_query: str, include_memory: bool = True) -> ContextLoadResult:
        """
        Load context optimized for user query intent.

        Args:
            user_query: Natural language query from user
            include_memory: Include relevant past work from conversation memory (Phase 220)

        Returns:
            ContextLoadResult with content, phases loaded, token count, strategy, memory
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

        # Step 5: Load conversation memory (Phase 220)
        memory_context = None
        if include_memory:
            memory_context = self._load_conversation_memory(user_query)

        # Step 6: Estimate token count (rough: 4 chars per token)
        token_count = len(content) // 4
        if memory_context:
            token_count += len(memory_context) // 4

        return ContextLoadResult(
            content=content,
            phases_loaded=phases,
            token_count=token_count,
            loading_strategy=strategy,
            intent_classification=self._intent_to_dict(intent) if intent else None,
            memory_context=memory_context
        )

    def _load_conversation_memory(self, query: str) -> Optional[str]:
        """
        Load relevant past work from conversation memory (Phase 220).

        Graceful degradation - returns None on any failure.

        Args:
            query: User query to find relevant past work

        Returns:
            Formatted memory context or None
        """
        try:
            from claude.tools.memory import get_session_memory
            memory = get_session_memory(query, max_results=3, min_relevance=0.3)
            return memory if memory else None
        except ImportError:
            logger.debug("Conversation memory not available")
            return None
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
            return None

    def _determine_strategy(
        self,
        user_query: str,
        intent: Optional[Intent]
    ) -> Tuple[str, List[int]]:
        """
        Determine loading strategy and phase selection.

        Phase 177 Enhancement: Uses dynamic DB keyword search instead of
        hardcoded phase numbers. Domain keywords still used for strategy
        naming, but phases come from DB search results.

        Returns:
            (strategy_name, phase_numbers_to_load)
        """
        query_lower = user_query.lower()

        # Domain keyword mappings (for strategy naming and search terms)
        domain_keywords = {
            'agent_enhancement': ['agent', 'enhancement', 'upgrade', 'template', 'few-shot', 'prompt', 'swarm', 'routing'],
            'sre_reliability': ['sre', 'reliability', 'health', 'launchagent', 'monitor', 'performance', 'database'],
            'voice_dictation': ['whisper', 'voice', 'dictation', 'audio', 'transcri'],
            'conversation_persistence': ['conversation', 'rag', 'persistence', 'chromadb', 'embedding'],
            'service_desk': ['service desk', 'servicedesk', 'ticket', 'l1', 'l2', 'l3', 'escalation', 'autotask'],
            'security': ['security', 'credential', 'authentication', 'oauth', 'encryption'],
            'document': ['document', 'docx', 'markdown', 'pandoc', 'conversion'],
            'meeting': ['meeting', 'transcript', 'intelligence', 'summary', 'action item'],
        }

        # Step 1: Identify matching domain
        matched_domain = None
        matched_keywords = []
        for domain, keywords in domain_keywords.items():
            matches = [kw for kw in keywords if kw in query_lower]
            if matches:
                matched_domain = domain
                matched_keywords = matches
                break

        # Step 2: If domain matched, search DB for relevant phases
        if matched_domain and self.use_database and self.db_queries:
            try:
                phases = self._search_phases_by_keywords(matched_keywords, limit=10)
                if phases:
                    return (matched_domain, phases)
            except Exception as e:
                logger.warning(f"DB search failed for {matched_domain}: {e}")

        # Step 3: Check intent complexity for strategic queries
        if intent and intent.complexity >= 8:
            recent_phases = self._get_recent_phases(20)
            return ("strategic_planning", recent_phases)

        if intent and intent.complexity >= 5:
            recent_phases = self._get_recent_phases(15)
            return ("moderate_complexity", recent_phases)

        # Step 4: Default - recent phases
        recent_phases = self._get_recent_phases(10)
        return ("default", recent_phases)

    def _search_phases_by_keywords(self, keywords: List[str], limit: int = 10) -> List[int]:
        """
        Search database for phases matching any of the given keywords.

        Args:
            keywords: List of keywords to search for
            limit: Maximum phases to return

        Returns:
            List of phase numbers (most recent first, deduplicated)
        """
        if not self.use_database or not self.db_queries:
            return []

        all_phases = set()
        for keyword in keywords[:3]:  # Limit to 3 keywords for performance
            try:
                results = self.db_queries.get_phases_by_keyword(keyword, limit=5)
                for phase in results:
                    all_phases.add(int(float(phase.phase_number)))
            except Exception:
                pass

        # Sort descending (most recent first) and limit
        return sorted(all_phases, reverse=True)[:limit]

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

        Phase 177 Enhancement: Uses DB-first for performance (<1ms),
        falls back to markdown parsing only when DB unavailable.

        Args:
            count: Number of recent phases to return

        Returns:
            List of phase numbers (e.g., [176, 175, 174, ...])
        """
        # DB-first path (fast: <1ms)
        if self.use_database and self.db_queries:
            try:
                return self.db_queries.get_recent_phase_numbers(count)
            except Exception as e:
                logger.warning(f"DB phase lookup failed, falling back to markdown: {e}")

        # Markdown fallback (slow: ~10ms for 2.1MB file)
        try:
            content = self.system_state_path.read_text()
            phase_pattern = re.compile(r'^##\s+[🔬🚀🎯🤖💼📋🎓🔗🛡️🎤📊🧠🗄️🚨📚📧📐].+PHASE\s+(\d+):', re.MULTILINE | re.IGNORECASE)

            matches = phase_pattern.findall(content)
            phase_numbers = sorted(set(int(m) for m in matches), reverse=True)

            return phase_numbers[:count]
        except Exception as e:
            logger.error(f"Failed to get recent phases: {e}")
            return []  # Return empty list instead of failing

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

    def load_guaranteed_minimum(self) -> str:
        """
        Load guaranteed minimum context - ALWAYS succeeds.

        Phase 177: Tier 0 context that never fails, providing basic awareness
        even when databases and files are unavailable.

        Returns:
            Compact context string (<200 tokens) with:
            - Capability summary (counts by type)
            - Recent phase titles (last 5)

        Reliability:
            - Never raises exceptions
            - Falls back to static content if all sources fail
            - Execution time <50ms guaranteed

        Example:
            >>> loader = SmartContextLoader()
            >>> context = loader.load_guaranteed_minimum()
            >>> print(context)
            **Maia Context Summary**
            Capabilities: 250 (49 agents, 201 tools)
            Recent: Phase 176, Phase 175, Phase 174, Phase 173, Phase 172
        """
        output = []
        output.append("**Maia Context Summary**")

        # Part 1: Capability summary (safe)
        try:
            cap_summary = self._get_capability_summary_safe()
            output.append(cap_summary)
        except Exception:
            output.append("Capabilities: Available (query for details)")

        # Part 1.5: Discovery hint (Phase 192 - always visible)
        output.append("🔍 **Discovery**: Use `load_capability_context(query='X')` for Phase 0 checks")

        # Part 2: Recent phase titles (safe)
        try:
            phase_titles = self._get_recent_phase_titles_safe(5)
            output.append(phase_titles)
        except Exception:
            output.append("Recent work: Available (query for details)")

        # Fallback if both failed
        if len(output) == 1:
            output.append("Maia AI assistant ready. Use smart loader for context.")

        return '\n'.join(output)

    def _get_capability_summary_safe(self) -> str:
        """
        Get capability summary with multiple fallback levels.

        Returns:
            Formatted string like "Capabilities: 250 (49 agents, 201 tools)"
        """
        # Level 1: Try capabilities registry (DB)
        if self.use_capabilities_db and self.capabilities_registry:
            try:
                summary = self.capabilities_registry.get_summary()
                return f"Capabilities: {summary['total']} ({summary['agents']} agents, {summary['tools']} tools)"
            except Exception:
                pass

        # Level 2: Try get_capability_summary method
        try:
            summary = self.get_capability_summary()
            if summary.get('total', 0) > 0:
                return f"Capabilities: {summary['total']} ({summary.get('agents', 0)} agents, {summary.get('tools', 0)} tools)"
        except Exception:
            pass

        # Level 3: Static fallback
        return "Capabilities: 200+ tools and 49 agents available"

    def _get_recent_phase_titles_safe(self, count: int = 5) -> str:
        """
        Get recent phase titles with fallback.

        Returns:
            Formatted string like "Recent: Phase 176, Phase 175, ..."
        """
        # Level 1: Try DB for phase numbers
        try:
            phases = self._get_recent_phases(count)
            if phases:
                phase_list = ", ".join(f"Phase {p}" for p in phases[:count])
                return f"Recent: {phase_list}"
        except Exception:
            pass

        # Level 2: Static fallback
        return "Recent work: Multiple active phases (query for details)"

    def load_capability_context(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        cap_type: Optional[str] = None,
        limit: int = 50
    ) -> str:
        """
        Load capability context using DB-first with markdown fallback.

        Phase 168 Integration: Uses capabilities.db for fast queries,
        falls back to capability_index.md if DB unavailable.

        Args:
            query: Optional search query (e.g., "security", "sre")
            category: Optional category filter (e.g., "sre", "security", "data")
            cap_type: Optional type filter ("tool" or "agent")
            limit: Maximum capabilities to return (default 50)

        Returns:
            Formatted markdown string with relevant capabilities
        """
        if self.use_capabilities_db:
            try:
                return self._load_capabilities_from_db(query, category, cap_type, limit)
            except Exception as e:
                logger.warning(f"Capabilities DB query failed, falling back to markdown: {e}")
                return self._load_capabilities_from_markdown()
        else:
            return self._load_capabilities_from_markdown()

    def _load_capabilities_from_db(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        cap_type: Optional[str] = None,
        limit: int = 50
    ) -> str:
        """
        Load capabilities from database (fast path - Phase 168).

        Returns formatted markdown with only relevant capabilities.
        Token savings: ~97% (3K → ~100 tokens for targeted queries)
        """
        if not self.capabilities_registry:
            raise RuntimeError("Capabilities registry not available")

        output = []
        output.append("# Relevant Capabilities")
        output.append("")

        if query:
            # Search by query
            results = self.capabilities_registry.find(query, cap_type=cap_type, limit=limit)
            output.append(f"**Query**: `{query}`")
        elif category:
            # List by category
            results = self.capabilities_registry.list_by_category(category=category, cap_type=cap_type)
            output.append(f"**Category**: `{category}`")
        else:
            # Get summary for general context
            summary = self.capabilities_registry.get_summary()
            output.append(f"**Total Capabilities**: {summary['total']} ({summary['agents']} agents, {summary['tools']} tools)")
            output.append("")
            output.append("**Categories**: " + ", ".join(sorted(summary['by_category'].keys())))
            output.append("")
            output.append("*Use `python3 claude/tools/sre/capabilities_registry.py find <query>` for specific lookups*")
            return '\n'.join(output)

        if not results:
            output.append("*No matching capabilities found*")
            return '\n'.join(output)

        output.append(f"**Found**: {len(results)} capabilities")
        output.append("")

        # Group by type
        agents = [r for r in results if r['type'] == 'agent']
        tools = [r for r in results if r['type'] == 'tool']

        if agents:
            output.append("## Agents")
            output.append("| Name | Category | Purpose |")
            output.append("|------|----------|---------|")
            for a in agents[:20]:  # Limit to 20 per type for token control
                purpose = (a['purpose'] or '')[:50] + ('...' if a['purpose'] and len(a['purpose']) > 50 else '')
                output.append(f"| {a['name']} | {a['category'] or '-'} | {purpose} |")
            output.append("")

        if tools:
            output.append("## Tools")
            output.append("| Name | Category | Purpose |")
            output.append("|------|----------|---------|")
            for t in tools[:30]:  # Limit to 30 for token control
                purpose = (t['purpose'] or '')[:50] + ('...' if t['purpose'] and len(t['purpose']) > 50 else '')
                output.append(f"| {t['name']} | {t['category'] or '-'} | {purpose} |")
            output.append("")

        return '\n'.join(output)

    def _load_capabilities_from_markdown(self) -> str:
        """
        Load capabilities from markdown file (fallback path).

        Returns full capability_index.md content (~3K tokens).
        """
        if self.capability_index_path.exists():
            content = self.capability_index_path.read_text()
            # Truncate if very large (shouldn't happen but safety check)
            max_chars = 15000  # ~3.75K tokens
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n*[Truncated for token budget]*"
            return content
        else:
            return "# Capability Index\n\n*capability_index.md not found*"

    def get_capability_summary(self) -> Dict[str, Any]:
        """
        Get capability statistics without loading full content.

        Returns dict with counts by type and category.
        """
        if self.use_capabilities_db and self.capabilities_registry:
            return self.capabilities_registry.get_summary()
        else:
            # Fallback: return basic info
            return {
                'total': 0,
                'agents': 0,
                'tools': 0,
                'by_category': {},
                'source': 'unavailable'
            }


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
