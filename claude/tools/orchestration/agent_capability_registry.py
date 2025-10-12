"""
Agent Capability Registry

Dynamic agent discovery and capability matching system that extracts
metadata from agent markdown files and enables intelligent routing
based on actual agent capabilities, not hardcoded mappings.

Architecture:
1. CapabilityExtractor: Parses agent markdown for metadata
2. AgentCapability: Dataclass representing agent capabilities
3. CapabilityRegistry: Central registry with search/match capabilities
4. CapabilityMatcher: Scoring engine for query-to-agent matching

Usage:
    from agent_capability_registry import CapabilityRegistry

    # Auto-discover agents and extract capabilities
    registry = CapabilityRegistry()

    # Find agents by domain
    dns_agents = registry.find_by_domain('dns')

    # Match query to best agent(s)
    matches = registry.match_query("Setup email authentication")
    # Returns: [(agent_name, confidence_score), ...]
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict


@dataclass
class AgentCapability:
    """
    Represents an agent's capabilities extracted from markdown.

    Capabilities include:
    - Domains: Technical domains (dns, azure, security, etc.)
    - Skills: Specific skills (SPF configuration, migration, etc.)
    - Tools: Tools/platforms agent can work with
    - Prerequisites: Required knowledge/context for agent
    - Performance: Historical performance metrics
    - Metadata: Version, last updated, source file
    """
    agent_name: str
    domains: Set[str] = field(default_factory=set)
    skills: Set[str] = field(default_factory=set)
    tools: Set[str] = field(default_factory=set)
    prerequisites: Set[str] = field(default_factory=set)
    specialties: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    handoff_capable: bool = False
    version: str = "unknown"
    source_file: Optional[Path] = None
    last_updated: Optional[datetime] = None

    # Purpose and full content for semantic matching
    purpose: str = ""
    full_content: str = ""

    # Performance metrics (populated from usage history)
    avg_response_time: Optional[float] = None
    success_rate: Optional[float] = None
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)"""
        data = asdict(self)
        # Convert sets to lists for JSON
        data['domains'] = list(self.domains)
        data['skills'] = list(self.skills)
        data['tools'] = list(self.tools)
        data['prerequisites'] = list(self.prerequisites)
        # Convert Path to string
        if self.source_file:
            data['source_file'] = str(self.source_file)
        # Convert datetime to ISO string
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapability':
        """Create from dictionary"""
        # Convert lists back to sets
        data['domains'] = set(data.get('domains', []))
        data['skills'] = set(data.get('skills', []))
        data['tools'] = set(data.get('tools', []))
        data['prerequisites'] = set(data.get('prerequisites', []))
        # Convert string back to Path
        if data.get('source_file'):
            data['source_file'] = Path(data['source_file'])
        # Convert ISO string back to datetime
        if data.get('last_updated'):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


class CapabilityExtractor:
    """
    Extracts capabilities from agent markdown files.

    Extraction strategies:
    1. Structured sections (## Core Capabilities, ## Specialties)
    2. YAML frontmatter (if present)
    3. Keyword detection in purpose/overview
    4. Integration points section
    5. Handoff declaration patterns
    """

    # Domain keyword patterns
    DOMAIN_PATTERNS = {
        'dns': r'\b(dns|domain|mx|spf|dkim|dmarc|nameserver|zone file)\b',
        'azure': r'\b(azure|entra|m365|exchange online|sharepoint|teams)\b',
        'security': r'\b(security|compliance|threat|vulnerability|audit|encryption)\b',
        'financial': r'\b(financial|tax|super|investment|budget|cost)\b',
        'cloud': r'\b(aws|gcp|cloud|terraform|kubernetes|docker)\b',
        'servicedesk': r'\b(ticket|incident|service desk|helpdesk|complaint)\b',
        'career': r'\b(job|resume|cv|interview|linkedin|career)\b',
        'data': r'\b(data|analytics|dashboard|report|visualization|kpi)\b',
        'sre': r'\b(sre|monitoring|observability|slo|sli|incident response)\b',
        'endpoint': r'\b(endpoint|laptop|macos|windows|intune|jamf|device)\b',
    }

    # Skill keyword patterns (more granular than domains)
    SKILL_PATTERNS = {
        'email_authentication': r'\b(spf|dkim|dmarc|email authentication)\b',
        'migration': r'\b(migrat(e|ion)|move|transfer|transition)\b',
        'configuration': r'\b(configur(e|ation)|setup|implement)\b',
        'troubleshooting': r'\b(troubleshoot|debug|diagnose|fix|resolve)\b',
        'architecture': r'\b(architect(ure)?|design|pattern|blueprint)\b',
        'automation': r'\b(automat(e|ion)|script|orchestrat(e|ion))\b',
        'analysis': r'\b(analy(ze|sis)|assess|evaluate|review)\b',
        'planning': r'\b(plan|strategy|roadmap)\b',
    }

    def extract(self, agent_file: Path) -> AgentCapability:
        """
        Extract capabilities from agent markdown file.

        Args:
            agent_file: Path to agent markdown file

        Returns:
            AgentCapability with extracted metadata
        """
        content = agent_file.read_text()
        agent_name = self._extract_agent_name(agent_file.stem)

        capability = AgentCapability(
            agent_name=agent_name,
            source_file=agent_file,
            last_updated=datetime.fromtimestamp(agent_file.stat().st_mtime),
            version=self._detect_version(agent_file.stem),
            full_content=content  # Store for semantic matching
        )

        # Extract purpose
        capability.purpose = self._extract_purpose(content)

        # Extract domains
        capability.domains = self._extract_domains(content)

        # Extract skills
        capability.skills = self._extract_skills(content)

        # Extract tools/platforms
        capability.tools = self._extract_tools(content)

        # Extract specialties from structured sections
        capability.specialties = self._extract_specialties(content)

        # Extract integration points
        capability.integration_points = self._extract_integration_points(content)

        # Extract prerequisites
        capability.prerequisites = self._extract_prerequisites(content)

        # Check for handoff capability
        capability.handoff_capable = self._has_handoff_support(content)

        return capability

    def _extract_agent_name(self, file_stem: str) -> str:
        """Extract agent name from filename"""
        # Remove _agent, _v2, _v1 suffixes
        name = file_stem.replace('_agent_v2', '').replace('_agent_v1', '').replace('_agent', '')
        return name

    def _detect_version(self, file_stem: str) -> str:
        """Detect agent version from filename"""
        if '_v2' in file_stem:
            return 'v2'
        elif '_v1' in file_stem:
            return 'v1'
        else:
            return 'base'

    def _extract_purpose(self, content: str) -> str:
        """Extract agent purpose from first section"""
        # Look for **Purpose**: pattern
        purpose_match = re.search(r'\*\*Purpose\*\*:\s*([^\n]+)', content, re.IGNORECASE)
        if purpose_match:
            return purpose_match.group(1).strip()

        # Fallback: First sentence of content
        first_sentences = re.findall(r'^[^#\n][^\n]{20,200}[.!?]', content, re.MULTILINE)
        if first_sentences:
            return first_sentences[0].strip()

        return ""

    def _extract_domains(self, content: str) -> Set[str]:
        """Extract technical domains from content"""
        content_lower = content.lower()
        domains = set()

        for domain, pattern in self.DOMAIN_PATTERNS.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                domains.add(domain)

        return domains

    def _extract_skills(self, content: str) -> Set[str]:
        """Extract specific skills from content"""
        content_lower = content.lower()
        skills = set()

        for skill, pattern in self.SKILL_PATTERNS.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                skills.add(skill)

        return skills

    def _extract_tools(self, content: str) -> Set[str]:
        """Extract tools/platforms from content"""
        # Common tools patterns
        tool_patterns = [
            r'\b(azure portal|powershell|terraform|ansible|kubernetes)\b',
            r'\b(dns manager|bind|cloudflare|route53)\b',
            r'\b(exchange admin center|microsoft 365 admin)\b',
            r'\b(python|bash|javascript|typescript)\b',
        ]

        tools = set()
        content_lower = content.lower()

        for pattern in tool_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            tools.update(matches)

        return tools

    def _extract_specialties(self, content: str) -> List[str]:
        """Extract specialties from structured sections"""
        specialties = []

        # Look for ## Specialties or ## Core Capabilities sections
        specialty_section = re.search(
            r'##\s+(?:Specialt(?:ies|y)|Core Capabilities|Expertise)\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if specialty_section:
            section_content = specialty_section.group(1)
            # Extract bullet points
            bullets = re.findall(r'[-*]\s+\*\*([^*]+)\*\*', section_content)
            specialties.extend(bullets)

        return specialties[:10]  # Limit to top 10

    def _extract_integration_points(self, content: str) -> List[str]:
        """Extract integration points (other agents this agent works with)"""
        integration_points = []

        # Look for ## Integration Points section
        integration_section = re.search(
            r'##\s+Integration Points?\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if integration_section:
            section_content = integration_section.group(1)
            # Extract agent names mentioned
            agent_mentions = re.findall(r'\b(\w+_\w+(?:_\w+)?)\s+[Aa]gent\b', section_content)
            integration_points.extend(agent_mentions)

        return integration_points[:10]

    def _extract_prerequisites(self, content: str) -> Set[str]:
        """Extract prerequisites from content"""
        prerequisites = set()

        # Look for Prerequisites or Required Context sections
        prereq_section = re.search(
            r'##\s+(?:Prerequisites|Required Context|Dependencies)\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if prereq_section:
            section_content = prereq_section.group(1)
            # Extract bullet points
            bullets = re.findall(r'[-*]\s+([^\n]+)', section_content)
            prerequisites.update(b.strip() for b in bullets[:5])

        return prerequisites

    def _has_handoff_support(self, content: str) -> bool:
        """Check if agent has handoff capability"""
        # Look for HANDOFF DECLARATION pattern or explicit handoff mention
        return bool(
            re.search(r'HANDOFF DECLARATION', content, re.IGNORECASE) or
            re.search(r'handoff.*(?:support|capability|pattern)', content, re.IGNORECASE)
        )


class CapabilityRegistry:
    """
    Central registry of agent capabilities.

    Provides:
    - Auto-discovery of agents from directory
    - Capability-based search
    - Query-to-agent matching
    - Performance tracking
    """

    def __init__(self, agents_dir: Path = None):
        """
        Initialize registry.

        Args:
            agents_dir: Directory containing agent markdown files
        """
        if agents_dir is None:
            # Default to claude/agents relative to this file
            agents_dir = Path(__file__).parent.parent.parent / "agents"

        self.agents_dir = agents_dir
        self.extractor = CapabilityExtractor()
        self.capabilities: Dict[str, AgentCapability] = {}

        # Indexes for fast lookup
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)
        self.skill_index: Dict[str, Set[str]] = defaultdict(set)
        self.tool_index: Dict[str, Set[str]] = defaultdict(set)

        # Auto-discover on init
        if self.agents_dir.exists():
            self.discover_agents()

    def discover_agents(self) -> int:
        """
        Discover and index all agents in directory.

        Returns:
            Number of agents discovered
        """
        if not self.agents_dir.exists():
            print(f"⚠️  Agent directory not found: {self.agents_dir}")
            return 0

        agent_files = list(self.agents_dir.glob("*_agent*.md"))

        for agent_file in agent_files:
            try:
                capability = self.extractor.extract(agent_file)
                self.add_capability(capability)
            except Exception as e:
                print(f"⚠️  Failed to extract capabilities from {agent_file.name}: {e}")

        print(f"✅ Discovered {len(self.capabilities)} agents with capabilities")
        return len(self.capabilities)

    def add_capability(self, capability: AgentCapability):
        """Add agent capability to registry and update indexes"""
        self.capabilities[capability.agent_name] = capability

        # Update indexes
        for domain in capability.domains:
            self.domain_index[domain].add(capability.agent_name)

        for skill in capability.skills:
            self.skill_index[skill].add(capability.agent_name)

        for tool in capability.tools:
            self.tool_index[tool].add(capability.agent_name)

    def get_capability(self, agent_name: str) -> Optional[AgentCapability]:
        """Get capability for specific agent"""
        return self.capabilities.get(agent_name)

    def find_by_domain(self, domain: str) -> List[AgentCapability]:
        """Find all agents with specific domain"""
        agent_names = self.domain_index.get(domain, set())
        return [self.capabilities[name] for name in agent_names]

    def find_by_skill(self, skill: str) -> List[AgentCapability]:
        """Find all agents with specific skill"""
        agent_names = self.skill_index.get(skill, set())
        return [self.capabilities[name] for name in agent_names]

    def find_by_tool(self, tool: str) -> List[AgentCapability]:
        """Find all agents that use specific tool"""
        agent_names = self.tool_index.get(tool, set())
        return [self.capabilities[name] for name in agent_names]

    def match_query(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Match query to best agents using capability-based scoring.

        Args:
            query: User query string
            top_k: Return top K matches
            min_score: Minimum confidence score (0-1)

        Returns:
            List of (agent_name, confidence_score) sorted by score
        """
        matcher = CapabilityMatcher(self)
        return matcher.match(query, top_k=top_k, min_score=min_score)

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            'total_agents': len(self.capabilities),
            'domains': len(self.domain_index),
            'skills': len(self.skill_index),
            'tools': len(self.tool_index),
            'handoff_capable': sum(1 for c in self.capabilities.values() if c.handoff_capable),
            'domain_coverage': {
                domain: len(agents)
                for domain, agents in self.domain_index.items()
            }
        }

    def export_to_json(self, output_file: Path):
        """Export registry to JSON"""
        data = {
            'agents': {
                name: capability.to_dict()
                for name, capability in self.capabilities.items()
            },
            'stats': self.get_stats(),
            'exported_at': datetime.now().isoformat()
        }

        output_file.write_text(json.dumps(data, indent=2))
        print(f"✅ Exported registry to {output_file}")


class CapabilityMatcher:
    """
    Scores agents based on query-to-capability matching.

    Scoring strategy:
    1. Domain match: High weight (0.4)
    2. Skill match: Medium weight (0.3)
    3. Tool match: Low weight (0.2)
    4. Performance history: Bonus (0.1)
    """

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.extractor = CapabilityExtractor()

    def match(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Match query to agents and return scored results.

        Returns:
            List of (agent_name, score) sorted by descending score
        """
        # Extract domains/skills from query
        query_domains = self.extractor._extract_domains(query)
        query_skills = self.extractor._extract_skills(query)
        query_tools = self.extractor._extract_tools(query)

        scores = {}

        for agent_name, capability in self.registry.capabilities.items():
            score = self._score_capability(
                capability,
                query_domains,
                query_skills,
                query_tools,
                query  # Pass full query for specificity matching
            )

            if score >= min_score:
                scores[agent_name] = score

        # Sort by score descending
        sorted_matches = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_matches[:top_k]

    def _score_capability(
        self,
        capability: AgentCapability,
        query_domains: Set[str],
        query_skills: Set[str],
        query_tools: Set[str],
        query: str
    ) -> float:
        """
        Score capability against query.

        Scoring:
        - Domain overlap: 0.4 * (|intersection| / |query domains|)
        - Skill overlap: 0.3 * (|intersection| / |query skills|)
        - Tool overlap: 0.1 * (|intersection| / |query tools|)
        - Keyword specificity: 0.2 * (keyword density in purpose + name match)
        """
        score = 0.0

        # Domain match
        if query_domains:
            domain_intersection = len(query_domains & capability.domains)
            score += 0.4 * (domain_intersection / len(query_domains))

        # Skill match
        if query_skills:
            skill_intersection = len(query_skills & capability.skills)
            score += 0.3 * (skill_intersection / len(query_skills))

        # Tool match
        if query_tools:
            tool_intersection = len(query_tools & capability.tools)
            score += 0.1 * (tool_intersection / len(query_tools))

        # Keyword specificity (check query keywords in purpose + agent name)
        specificity = self._calculate_specificity(query, capability)
        score += 0.2 * specificity

        return score

    def _calculate_specificity(self, query: str, capability: AgentCapability) -> float:
        """
        Calculate how specifically the agent matches the query keywords.

        Checks:
        1. Query keywords in agent name (highest weight)
        2. Query keywords in purpose (medium weight)
        3. Keyword density in specialties (lower weight)
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w{4,}\b', query_lower))  # Words 4+ chars

        specificity = 0.0

        # Agent name match (0.5 weight)
        agent_name_lower = capability.agent_name.lower()
        name_matches = sum(1 for word in query_words if word in agent_name_lower)
        if query_words:
            specificity += 0.5 * (name_matches / len(query_words))

        # Purpose match (0.3 weight)
        purpose_lower = capability.purpose.lower()
        purpose_matches = sum(1 for word in query_words if word in purpose_lower)
        if query_words and capability.purpose:
            specificity += 0.3 * (purpose_matches / len(query_words))

        # Specialty match (0.2 weight)
        specialties_text = " ".join(capability.specialties).lower()
        specialty_matches = sum(1 for word in query_words if word in specialties_text)
        if query_words and capability.specialties:
            specificity += 0.2 * (specialty_matches / len(query_words))

        return min(specificity, 1.0)  # Cap at 1.0


# Convenience functions
def create_registry(agents_dir: Path = None) -> CapabilityRegistry:
    """Create and populate capability registry"""
    return CapabilityRegistry(agents_dir=agents_dir)


def match_agent(query: str, registry: CapabilityRegistry = None) -> List[Tuple[str, float]]:
    """
    Convenience function to match query to agents.

    Args:
        query: User query
        registry: Existing registry (creates new if None)

    Returns:
        List of (agent_name, confidence_score)
    """
    if registry is None:
        registry = create_registry()

    return registry.match_query(query)


if __name__ == '__main__':
    print("=" * 70)
    print("AGENT CAPABILITY REGISTRY - DEMO")
    print("=" * 70)

    # Create registry and discover agents
    registry = create_registry()
    print(f"\n📊 Registry Stats:")
    stats = registry.get_stats()
    for key, value in stats.items():
        if key != 'domain_coverage':
            print(f"  {key}: {value}")

    print(f"\n📊 Domain Coverage:")
    for domain, count in stats['domain_coverage'].items():
        print(f"  {domain}: {count} agents")

    # Test queries
    print("\n" + "=" * 70)
    print("CAPABILITY MATCHING EXAMPLES")
    print("=" * 70)

    test_queries = [
        "Setup email authentication with SPF and DKIM",
        "Migrate 200 users to Azure Exchange Online",
        "Troubleshoot DNS propagation issues",
        "Design cloud architecture for enterprise",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        matches = registry.match_query(query, top_k=3, min_score=0.4)
        if matches:
            for agent_name, score in matches:
                capability = registry.get_capability(agent_name)
                print(f"  {agent_name}: {score:.3f}")
                print(f"    Purpose: {capability.purpose[:80]}...")
                print(f"    Domains: {', '.join(list(capability.domains)[:3])}")
                print(f"    Skills: {', '.join(list(capability.skills)[:3])}")
        else:
            print(f"  No strong matches (all < 0.4)")
