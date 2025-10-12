"""
Context Management System

Manages context windows for long-running multi-agent workflows,
preventing token limit issues through intelligent compression,
relevance scoring, and priority-based retention.

Components:
1. ContextItem: Individual context piece with metadata
2. ContextWindow: Token-limited context manager
3. CompressionEngine: Reduces context size via summarization
4. RelevanceScorer: Calculates importance scores
5. ContextArchive: Cold storage for old context

Usage:
    from context_management import ContextWindow

    # Create window with 100k token limit
    window = ContextWindow(max_tokens=100000)

    # Add context
    window.add("User query: Setup DNS authentication")
    window.add_agent_output("dns_specialist", "SPF records configured...")

    # Automatic compression when limit approached
    if window.needs_compression():
        window.compress()

    # Get current context for agent
    context = window.get_context_for_agent("azure_specialist")
"""

import re
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum


class ContextSource(Enum):
    """Source of context item"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    COORDINATOR = "coordinator"


class ImportanceLevel(Enum):
    """Importance level for context retention"""
    CRITICAL = 5    # Never compress (final outputs, key decisions)
    HIGH = 4        # Compress only under pressure
    MEDIUM = 3      # Normal compression
    LOW = 2         # Aggressive compression
    MINIMAL = 1     # First to compress


@dataclass
class ContextItem:
    """
    Individual piece of context with metadata.

    Tracks content, source, relevance, and provides
    token counting and compression capability.
    """
    content: str
    source: ContextSource
    timestamp: datetime
    item_id: str

    # Metadata
    agent_name: Optional[str] = None
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    keywords: Set[str] = field(default_factory=set)

    # Metrics
    token_count: int = 0
    relevance_score: float = 0.5
    reference_count: int = 0

    # Compression
    is_compressed: bool = False
    original_token_count: int = 0

    def __post_init__(self):
        """Calculate token count after initialization"""
        if self.token_count == 0:
            self.token_count = self._estimate_tokens(self.content)
            self.original_token_count = self.token_count

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Estimate token count (rough approximation).
        Rule: ~4 chars per token on average
        """
        return len(text) // 4

    def compress(self, summary: str):
        """
        Replace content with compressed version.

        Args:
            summary: Compressed/summarized content
        """
        self.content = summary
        self.token_count = self._estimate_tokens(summary)
        self.is_compressed = True

    def get_content_hash(self) -> str:
        """Get hash of content for deduplication"""
        return hashlib.md5(self.content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'content': self.content,
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'item_id': self.item_id,
            'agent_name': self.agent_name,
            'importance': self.importance.value,
            'keywords': list(self.keywords),
            'token_count': self.token_count,
            'relevance_score': self.relevance_score,
            'is_compressed': self.is_compressed,
        }


class RelevanceScorer:
    """
    Calculates relevance scores for context items.

    Scoring factors:
    - Recency: Newer items score higher
    - Reference count: Frequently accessed items score higher
    - Keyword match: Items matching current domain/task score higher
    - Importance level: Explicit importance boosts score
    """

    # Scoring weights
    RECENCY_WEIGHT = 0.3
    REFERENCE_WEIGHT = 0.2
    KEYWORD_WEIGHT = 0.3
    IMPORTANCE_WEIGHT = 0.2

    def __init__(self):
        self.current_keywords: Set[str] = set()

    def set_current_context(self, keywords: Set[str]):
        """Set keywords for current task/domain"""
        self.current_keywords = keywords

    def score(self, item: ContextItem, now: datetime = None) -> float:
        """
        Calculate relevance score (0.0 to 1.0).

        Args:
            item: Context item to score
            now: Current timestamp (for recency calculation)

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if now is None:
            now = datetime.now()

        # Recency score (exponential decay)
        age_hours = (now - item.timestamp).total_seconds() / 3600
        recency_score = max(0.0, 1.0 - (age_hours / 24))  # Decay over 24 hours

        # Reference count score (logarithmic)
        reference_score = min(1.0, item.reference_count / 10)

        # Keyword match score
        if self.current_keywords and item.keywords:
            matches = len(self.current_keywords & item.keywords)
            keyword_score = min(1.0, matches / max(len(self.current_keywords), 1))
        else:
            keyword_score = 0.5  # Neutral if no keywords

        # Importance score
        importance_score = item.importance.value / 5.0

        # Weighted sum
        total_score = (
            recency_score * self.RECENCY_WEIGHT +
            reference_score * self.REFERENCE_WEIGHT +
            keyword_score * self.KEYWORD_WEIGHT +
            importance_score * self.IMPORTANCE_WEIGHT
        )

        return total_score


class CompressionEngine:
    """
    Reduces context size through summarization and deduplication.

    Strategies:
    1. Extract key points (for agent outputs)
    2. Remove redundant information
    3. Collapse similar items
    """

    def summarize_agent_output(self, content: str, max_tokens: int = 200) -> str:
        """
        Summarize agent output to key points.

        Args:
            content: Full agent output
            max_tokens: Target token count

        Returns:
            Summarized content
        """
        # Extract key information patterns
        key_patterns = [
            r'(?:##?\s+)(.+)',  # Headers
            r'(?:\*\*|__)(.+?)(?:\*\*|__)',  # Bold text
            r'(?:RESULT|OUTPUT|CONCLUSION|KEY POINTS?):?\s*(.+)',  # Explicit results
            r'(?:✅|✓)\s*(.+)',  # Success markers
            r'(?:❌|✗)\s*(.+)',  # Failure markers
        ]

        key_points = []
        for pattern in key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            key_points.extend(matches)

        # If we found key points, use them
        if key_points:
            summary = "Key points:\n" + "\n".join(f"- {p.strip()}" for p in key_points[:5])
        else:
            # Fallback: Take first and last sentences
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            if len(sentences) > 2:
                summary = f"{sentences[0]}. ... {sentences[-1]}."
            else:
                summary = ". ".join(sentences[:2])

        # Truncate to max_tokens
        estimated_tokens = len(summary) // 4
        if estimated_tokens > max_tokens:
            char_limit = max_tokens * 4
            summary = summary[:char_limit] + "..."

        return summary

    def deduplicate(self, items: List[ContextItem]) -> List[ContextItem]:
        """
        Remove duplicate items based on content hash.

        Args:
            items: List of context items

        Returns:
            Deduplicated list
        """
        seen_hashes = set()
        unique_items = []

        for item in items:
            content_hash = item.get_content_hash()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_items.append(item)

        return unique_items


class ContextWindow:
    """
    Manages context window with token limits.

    Features:
    - Automatic compression when approaching limits
    - Relevance-based retention
    - Priority queue for important items
    - Archive support for old context
    """

    def __init__(
        self,
        max_tokens: int = 100000,
        compression_threshold: float = 0.8,
        archive_dir: Path = None
    ):
        """
        Initialize context window.

        Args:
            max_tokens: Maximum token count (default 100k)
            compression_threshold: Compress when at X% of max (default 80%)
            archive_dir: Directory for archived context
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self.items: List[ContextItem] = []

        # Engines
        self.scorer = RelevanceScorer()
        self.compressor = CompressionEngine()

        # Archive
        if archive_dir is None:
            archive_dir = Path(__file__).parent.parent.parent / "context" / "session" / "context_archive"
        self.archive_dir = archive_dir
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Metrics
        self.total_items_added = 0
        self.total_compressions = 0
        self.total_archived = 0

    def add(
        self,
        content: str,
        source: ContextSource = ContextSource.USER,
        importance: ImportanceLevel = ImportanceLevel.MEDIUM,
        agent_name: Optional[str] = None,
        keywords: Set[str] = None
    ) -> ContextItem:
        """
        Add item to context window.

        Args:
            content: Context content
            source: Source of context
            importance: Importance level
            agent_name: Agent name if from agent
            keywords: Domain keywords

        Returns:
            Created ContextItem
        """
        item = ContextItem(
            content=content,
            source=source,
            timestamp=datetime.now(),
            item_id=f"{source.value}_{self.total_items_added}",
            agent_name=agent_name,
            importance=importance,
            keywords=keywords or set()
        )

        self.items.append(item)
        self.total_items_added += 1

        # Update relevance scores
        self._update_relevance_scores()

        # Check if compression needed
        if self.needs_compression():
            self.compress()

        return item

    def add_agent_output(
        self,
        agent_name: str,
        output: str,
        importance: ImportanceLevel = ImportanceLevel.HIGH,
        keywords: Set[str] = None
    ) -> ContextItem:
        """Convenience method for adding agent output"""
        return self.add(
            content=output,
            source=ContextSource.AGENT,
            importance=importance,
            agent_name=agent_name,
            keywords=keywords
        )

    def get_current_token_count(self) -> int:
        """Get total token count of all items"""
        return sum(item.token_count for item in self.items)

    def get_utilization(self) -> float:
        """Get context window utilization (0.0 to 1.0)"""
        return self.get_current_token_count() / self.max_tokens

    def needs_compression(self) -> bool:
        """Check if compression is needed"""
        return self.get_utilization() >= self.compression_threshold

    def compress(self, target_utilization: float = 0.6):
        """
        Compress context to target utilization.

        Strategy:
        1. Deduplicate items
        2. Compress low-relevance items
        3. Archive oldest items if needed

        Args:
            target_utilization: Target utilization after compression
        """
        print(f"🗜️  Compressing context (current: {self.get_current_token_count()} tokens, {self.get_utilization():.1%} full)")

        # Step 1: Deduplicate
        original_count = len(self.items)
        self.items = self.compressor.deduplicate(self.items)
        if len(self.items) < original_count:
            print(f"  Deduplicated: {original_count} → {len(self.items)} items")

        # Step 2: Compress low-relevance items
        items_compressed = 0
        for item in sorted(self.items, key=lambda x: x.relevance_score):
            if self.get_utilization() <= target_utilization:
                break

            # Skip already compressed or critical items
            if item.is_compressed or item.importance == ImportanceLevel.CRITICAL:
                continue

            # Compress
            if item.source == ContextSource.AGENT:
                summary = self.compressor.summarize_agent_output(item.content)
                item.compress(summary)
                items_compressed += 1

        if items_compressed > 0:
            print(f"  Compressed: {items_compressed} items")

        # Step 3: Archive if still over target
        if self.get_utilization() > target_utilization:
            archived = self._archive_oldest_items(target_utilization)
            if archived > 0:
                print(f"  Archived: {archived} items")

        self.total_compressions += 1
        print(f"✅ Compression complete (now: {self.get_current_token_count()} tokens, {self.get_utilization():.1%} full)")

    def get_context_for_agent(
        self,
        agent_name: str,
        include_recent: int = 5,
        include_by_relevance: int = 10
    ) -> str:
        """
        Get context formatted for agent.

        Strategy:
        - Always include N most recent items
        - Include top M items by relevance score
        - Format as markdown

        Args:
            agent_name: Target agent name
            include_recent: Number of recent items to include
            include_by_relevance: Number of items by relevance

        Returns:
            Formatted context string
        """
        # Update relevance scores
        self._update_relevance_scores()

        # Get recent items
        recent_items = self.items[-include_recent:] if len(self.items) >= include_recent else self.items

        # Get relevant items
        relevant_items = sorted(self.items, key=lambda x: x.relevance_score, reverse=True)[:include_by_relevance]

        # Combine (deduplicate by ID)
        selected_items = {item.item_id: item for item in recent_items + relevant_items}
        selected = sorted(selected_items.values(), key=lambda x: x.timestamp)

        # Format
        lines = [f"# Context for {agent_name}\n"]

        for item in selected:
            source_label = f"[{item.source.value.upper()}"
            if item.agent_name:
                source_label += f":{item.agent_name}"
            source_label += "]"

            lines.append(f"\n## {source_label} ({item.timestamp.strftime('%H:%M:%S')})")
            lines.append(item.content)
            if item.is_compressed:
                lines.append("*(compressed)*")

        # Increment reference count
        for item in selected:
            item.reference_count += 1

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get context window statistics"""
        return {
            'total_items': len(self.items),
            'total_tokens': self.get_current_token_count(),
            'utilization': self.get_utilization(),
            'max_tokens': self.max_tokens,
            'items_added': self.total_items_added,
            'compressions': self.total_compressions,
            'archived': self.total_archived,
            'items_by_source': {
                source.value: sum(1 for item in self.items if item.source == source)
                for source in ContextSource
            },
            'compressed_items': sum(1 for item in self.items if item.is_compressed),
        }

    def _update_relevance_scores(self):
        """Update relevance scores for all items"""
        now = datetime.now()
        for item in self.items:
            item.relevance_score = self.scorer.score(item, now)

    def _archive_oldest_items(self, target_utilization: float) -> int:
        """Archive oldest items until target utilization reached"""
        archived_count = 0

        # Sort by timestamp (oldest first)
        sorted_items = sorted(self.items, key=lambda x: x.timestamp)

        items_to_keep = []
        items_to_archive = []

        for item in sorted_items:
            # Always keep critical items
            if item.importance == ImportanceLevel.CRITICAL:
                items_to_keep.append(item)
                continue

            # Check if we can stop archiving
            potential_tokens = sum(i.token_count for i in items_to_keep)
            if potential_tokens / self.max_tokens <= target_utilization:
                items_to_keep.append(item)
            else:
                items_to_archive.append(item)

        # Archive items
        if items_to_archive:
            self._write_to_archive(items_to_archive)
            archived_count = len(items_to_archive)
            self.total_archived += archived_count

        self.items = items_to_keep
        return archived_count

    def _write_to_archive(self, items: List[ContextItem]):
        """Write items to archive file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        archive_file = self.archive_dir / f"context_archive_{date_str}.jsonl"

        with archive_file.open('a') as f:
            for item in items:
                f.write(json.dumps(item.to_dict()) + '\n')


if __name__ == '__main__':
    print("=" * 70)
    print("CONTEXT MANAGEMENT SYSTEM - DEMO")
    print("=" * 70)

    # Create context window (small limit for demo)
    window = ContextWindow(max_tokens=5000, compression_threshold=0.7)

    print(f"\n📊 Initial state:")
    print(f"  Max tokens: {window.max_tokens}")
    print(f"  Compression threshold: {window.compression_threshold:.0%}")

    # Add some context
    print(f"\n📝 Adding context...")

    window.add("User wants to setup email authentication", ContextSource.USER, ImportanceLevel.HIGH, keywords={'dns', 'email'})

    # Simulate agent outputs
    long_output = """
    # DNS Specialist Analysis

    I've analyzed your domain configuration and here's what we need to do:

    ## SPF Record
    Configure SPF record to authorize mail servers:
    v=spf1 include:_spf.google.com ~all

    ## DKIM Setup
    Generate 2048-bit DKIM key pair and publish public key in DNS.

    ## DMARC Policy
    Start with monitoring policy: v=DMARC1; p=none; rua=mailto:dmarc@example.com

    This will take approximately 24-48 hours for DNS propagation.
    """ * 5  # Repeat to make it large

    window.add_agent_output("dns_specialist", long_output, ImportanceLevel.HIGH, keywords={'dns', 'email', 'spf', 'dkim'})
    window.add_agent_output("azure_specialist", "Azure Exchange Online configured successfully. " * 100, ImportanceLevel.MEDIUM, keywords={'azure', 'exchange'})
    window.add_agent_output("security_specialist", "Security audit completed - no issues found. " * 100, ImportanceLevel.MEDIUM, keywords={'security', 'audit'})
    window.add_agent_output("migration_specialist", "Migration plan developed for 200 users. " * 80, ImportanceLevel.LOW, keywords={'migration', 'azure'})

    # Check stats
    stats = window.get_stats()
    print(f"\n📊 After adding context:")
    print(f"  Total items: {stats['total_items']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Utilization: {stats['utilization']:.1%}")
    print(f"  Compressed items: {stats['compressed_items']}")

    # Get context for agent
    print(f"\n📋 Context for next agent:")
    context = window.get_context_for_agent("final_agent", include_recent=3, include_by_relevance=5)
    print(f"  Length: {len(context)} chars")
    print(f"  Token estimate: {len(context) // 4}")

    # Final stats
    final_stats = window.get_stats()
    print(f"\n📊 Final stats:")
    print(f"  Utilization: {final_stats['utilization']:.1%}")
    print(f"  Compressions: {final_stats['compressions']}")
    print(f"  Archived: {final_stats['archived']}")

    print("\n" + "=" * 70)
    print("Context management ready for production!")
    print("=" * 70)
