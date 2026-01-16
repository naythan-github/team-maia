"""
Subagent Handoff Detector - SPRINT-003 Phase 4.

Analyzes subagent results for handoff patterns and recommends
appropriate agent transitions.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple


# Explicit handoff patterns with high confidence
EXPLICIT_PATTERNS = [
    (r"transfer_to_(\w+)", "transfer_to_{target}"),
    (r"handoff to (\w+)", "handoff to {target}"),
    (r"recommend (\w+) agent", "recommend {target} agent"),
    (r"this requires (\w+) expertise", "this requires {target} expertise"),
    (r"escalate to (\w+)", "escalate to {target}"),
]

# Domain keywords mapped to specialized agents
DOMAIN_AGENT_MAP = {
    "security": "cloud_security_principal_agent",
    "authentication": "cloud_security_principal_agent",
    "authorization": "cloud_security_principal_agent",
    "vulnerability": "cloud_security_principal_agent",
    "infrastructure": "azure_infrastructure_architect_agent",
    "terraform": "azure_infrastructure_architect_agent",
    "azure": "azure_infrastructure_architect_agent",
    "ci/cd": "devops_principal_architect_agent",
    "pipeline": "devops_principal_architect_agent",
    "deployment": "devops_principal_architect_agent",
    "performance": "sre_principal_engineer_agent",
    "reliability": "sre_principal_engineer_agent",
    "monitoring": "sre_principal_engineer_agent",
}


@dataclass
class HandoffRecommendation:
    """Result of handoff analysis."""
    should_handoff: bool
    target_agent: Optional[str]
    reason: str
    context_to_pass: Optional[str]
    confidence: float  # 0.0-1.0
    detected_patterns: List[str] = field(default_factory=list)


class SubagentHandoffDetector:
    """
    Detects handoff patterns in subagent results.

    Analyzes text output from subagents to determine if a handoff
    to another agent is recommended, either explicitly or implicitly.
    """

    def __init__(self):
        """Load explicit patterns and domain keywords."""
        self.explicit_patterns = EXPLICIT_PATTERNS
        self.domain_map = DOMAIN_AGENT_MAP

    def analyze(
        self,
        subagent_result: str,
        current_agent: str
    ) -> HandoffRecommendation:
        """
        Analyze subagent result for handoff recommendations.

        Args:
            subagent_result: Text output from subagent
            current_agent: Name of current agent

        Returns:
            HandoffRecommendation with handoff decision and metadata
        """
        detected_patterns: List[str] = []

        # Check for explicit handoff patterns first (high confidence)
        explicit_result = self._check_explicit_handoff(subagent_result)
        if explicit_result:
            target, pattern_matched = explicit_result
            detected_patterns.append(pattern_matched)
            context = self._extract_context_for_handoff(subagent_result)

            return HandoffRecommendation(
                should_handoff=True,
                target_agent=target,
                reason=f"Explicit handoff pattern detected: {pattern_matched}",
                context_to_pass=context,
                confidence=0.9,
                detected_patterns=detected_patterns
            )

        # Check for domain mismatch (medium confidence)
        domain_result = self._check_domain_mismatch(subagent_result, current_agent)
        if domain_result:
            target, domain_keyword = domain_result
            context = self._extract_context_for_handoff(subagent_result)

            return HandoffRecommendation(
                should_handoff=True,
                target_agent=target,
                reason=f"Domain keyword '{domain_keyword}' suggests {target}",
                context_to_pass=context,
                confidence=0.6,
                detected_patterns=[f"domain:{domain_keyword}"]
            )

        # No handoff needed
        return HandoffRecommendation(
            should_handoff=False,
            target_agent=None,
            reason="No handoff indicators detected",
            context_to_pass=None,
            confidence=0.0,
            detected_patterns=[]
        )

    def _check_explicit_handoff(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Check for explicit handoff patterns.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (target_agent, pattern_matched) or None
        """
        text_lower = text.lower()

        for pattern, template in self.explicit_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Extract target from match group
                target = match.group(1)
                # Clean up target name
                target = self._normalize_agent_name(target)
                # Build the matched pattern string
                pattern_matched = template.format(target=target)
                return (target, pattern_matched)

        return None

    def _check_domain_mismatch(
        self,
        text: str,
        current_agent: str
    ) -> Optional[Tuple[str, str]]:
        """
        Check for domain keywords suggesting different expertise.

        Args:
            text: Text to analyze
            current_agent: Current agent name

        Returns:
            Tuple of (target_agent, domain_keyword) or None
        """
        text_lower = text.lower()
        current_agent_lower = current_agent.lower()

        # Track domain keyword matches with frequency
        domain_matches: Dict[str, int] = {}

        for keyword, target_agent in self.domain_map.items():
            # Skip if this domain matches current agent
            if keyword in current_agent_lower:
                continue
            if target_agent.lower() in current_agent_lower:
                continue

            # Count occurrences of this keyword
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
            if count > 0:
                if target_agent not in domain_matches:
                    domain_matches[target_agent] = 0
                domain_matches[target_agent] += count

        if domain_matches:
            # Return the agent with most keyword matches
            best_agent = max(domain_matches, key=domain_matches.get)
            # Find the keyword that matched
            for keyword, agent in self.domain_map.items():
                if agent == best_agent and keyword in text_lower:
                    return (best_agent, keyword)

        return None

    def _extract_context_for_handoff(self, text: str) -> str:
        """
        Extract key context to pass to next agent.

        Extracts relevant information like:
        - CVE references
        - Technical details
        - Action items

        Args:
            text: Full text to extract context from

        Returns:
            Extracted context string
        """
        context_parts = []

        # Extract CVE references
        cves = re.findall(r'CVE-\d{4}-\d+', text, re.IGNORECASE)
        if cves:
            context_parts.append(f"CVE references: {', '.join(cves)}")

        # Extract numbered items or bullet points
        bullets = re.findall(r'^\s*[-*\d]+[.)]\s*(.+)$', text, re.MULTILINE)
        if bullets:
            context_parts.append("Key points: " + "; ".join(bullets[:5]))

        # Extract sentences with key action words
        action_words = ['critical', 'important', 'urgent', 'vulnerability', 'issue', 'problem']
        for word in action_words:
            sentences = re.findall(rf'[^.]*\b{word}\b[^.]*\.', text, re.IGNORECASE)
            for sentence in sentences[:2]:
                if sentence.strip() not in context_parts:
                    context_parts.append(sentence.strip())

        if context_parts:
            return " | ".join(context_parts[:5])  # Limit context size

        # Fallback: first 200 chars
        return text[:200].strip() if len(text) > 200 else text.strip()

    def _normalize_agent_name(self, name: str) -> str:
        """
        Normalize agent name to consistent format.

        Preserves the agent name as captured from the regex,
        including any _agent suffix if present.

        Args:
            name: Raw agent name from pattern match

        Returns:
            Normalized agent name (lowercase, stripped)
        """
        # Just clean up whitespace and normalize case
        # Preserve _agent suffix if present
        return name.lower().strip()
