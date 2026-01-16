"""
Spawn Decision Engine - Determines when to delegate to a subagent.

Part of SPRINT-003 Phase 2 implementation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
import re


class SpawnReason(Enum):
    """Reasons to spawn a subagent."""
    MULTI_FILE_EXPLORATION = "multi_file_exploration"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    HEAVY_RESEARCH = "heavy_research"
    SPRINT_MODE_ACTIVE = "sprint_mode_active"
    EXPLICIT_REQUEST = "explicit_request"
    CONTEXT_PRESERVATION = "context_preservation"


class NoSpawnReason(Enum):
    """Reasons NOT to spawn a subagent."""
    SIMPLE_TASK = "simple_task"
    SPECIFIC_FILE_KNOWN = "specific_file_known"
    DIRECT_EDIT = "direct_edit"
    SINGLE_COMMAND = "single_command"


@dataclass
class SpawnDecision:
    """Result of spawn decision analysis."""
    should_spawn: bool
    reason: Enum  # SpawnReason or NoSpawnReason
    confidence: float  # 0.0 to 1.0
    recommended_agent: Optional[str] = None
    explanation: str = ""


class SpawnDecisionEngine:
    """
    Analyzes queries to determine if spawning a subagent is beneficial.

    Decision factors:
    - Query patterns (exploration vs direct action)
    - Number of files involved
    - Sprint mode status
    - Complexity indicators
    """

    # Patterns that indicate exploration/research (spawn)
    EXPLORATION_PATTERNS = [
        r'\bhow\s+(does|do|is|are)\b',
        r'\bwhere\s+(is|are)\b',
        r'\bfind\s+all\b',
        r'\banalyze\b',
        r'\bexplore\b',
        r'\barchitecture\b',
        r'\bwhat\s+is\s+the\b',
        r'\breview\s+the\b',
    ]

    # Patterns that indicate direct action (no spawn)
    DIRECT_ACTION_PATTERNS = [
        r'\bedit\b',
        r'\bread\s+file\b',
        r'\bread\s+the\b',
        r'\brun\b',
        r'\bexecute\b',
        r'\bcommit\b',
        r'\bpush\b',
    ]

    # Agent recommendation patterns
    AGENT_PATTERNS = {
        'cloud_security_principal_agent': [
            r'\bsecurity\b',
            r'\bauth(entication|orization)?\b',
            r'\bpermission\b',
            r'\baccess\s+control\b',
        ],
        'sre_principal_engineer_agent': [
            r'\binfrastructure\b',
            r'\bterraform\b',
            r'\bazure\b',
            r'\breliability\b',
            r'\bmonitoring\b',
        ],
        'devops_principal_architect_agent': [
            r'\bpipeline\b',
            r'\bci/cd\b',
            r'\bdeploy\b',
            r'\bbuild\b',
        ],
    }

    def __init__(self):
        """Initialize the spawn decision engine."""
        pass

    def analyze(
        self,
        query: str,
        session_context: Dict[str, Any],
        files_mentioned: List[str]
    ) -> SpawnDecision:
        """
        Analyze whether to spawn a subagent.

        Args:
            query: User query text
            session_context: Current session state (may contain sprint_mode)
            files_mentioned: List of file paths mentioned in query

        Returns:
            SpawnDecision with recommendation
        """
        query_lower = query.lower()

        # Priority 1: Check sprint mode
        sprint_decision = self._check_sprint_mode(session_context)
        if sprint_decision:
            return sprint_decision

        # Priority 2: Check for direct action patterns (no spawn)
        direct_decision = self._check_direct_patterns(query_lower, files_mentioned)
        if direct_decision:
            return direct_decision

        # Priority 3: Check for exploration patterns (spawn)
        exploration_decision = self._check_exploration_patterns(query_lower)
        if exploration_decision:
            return exploration_decision

        # Priority 4: Check multiple files (spawn)
        if len(files_mentioned) > 3:
            recommended_agent = self._get_recommended_agent(query_lower, SpawnReason.MULTI_FILE_EXPLORATION)
            return SpawnDecision(
                should_spawn=True,
                reason=SpawnReason.MULTI_FILE_EXPLORATION,
                confidence=0.75,
                recommended_agent=recommended_agent,
                explanation=f"Multiple files mentioned ({len(files_mentioned)} files) suggests complex multi-file task"
            )

        # Default: ambiguous case, medium confidence no-spawn
        return SpawnDecision(
            should_spawn=False,
            reason=NoSpawnReason.SIMPLE_TASK,
            confidence=0.5,
            recommended_agent=None,
            explanation="Query does not match strong spawn or no-spawn patterns"
        )

    def _check_sprint_mode(self, session_context: Dict[str, Any]) -> Optional[SpawnDecision]:
        """
        Check if sprint mode is active in session.

        Sprint mode biases toward spawning for better task decomposition.

        Args:
            session_context: Session state dictionary

        Returns:
            SpawnDecision if sprint mode is active, None otherwise
        """
        if session_context.get("sprint_mode") is True:
            recommended_agent = "sre_principal_engineer_agent"  # Default for sprint
            return SpawnDecision(
                should_spawn=True,
                reason=SpawnReason.SPRINT_MODE_ACTIVE,
                confidence=0.85,
                recommended_agent=recommended_agent,
                explanation="Sprint mode active - delegating to subagent for structured task execution"
            )
        return None

    def _check_exploration_patterns(self, query: str) -> Optional[SpawnDecision]:
        """
        Check if query matches exploration patterns.

        Args:
            query: Query text (lowercase)

        Returns:
            SpawnDecision if exploration pattern found, None otherwise
        """
        # Pattern descriptions for better explanations
        pattern_descriptions = {
            r'\bhow\s+(does|do|is|are)\b': 'how does',
            r'\bwhere\s+(is|are)\b': 'where is',
            r'\bfind\s+all\b': 'find',
            r'\banalyze\b': 'analyze',
            r'\bexplore\b': 'explore',
            r'\barchitecture\b': 'architecture',
            r'\bwhat\s+is\s+the\b': 'what is',
            r'\breview\s+the\b': 'review',
        }

        for pattern in self.EXPLORATION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                recommended_agent = self._get_recommended_agent(query, SpawnReason.MULTI_FILE_EXPLORATION)
                pattern_desc = pattern_descriptions.get(pattern, 'exploration pattern')
                return SpawnDecision(
                    should_spawn=True,
                    reason=SpawnReason.MULTI_FILE_EXPLORATION,
                    confidence=0.8,
                    recommended_agent=recommended_agent,
                    explanation=f"Query matches exploration pattern '{pattern_desc}' - requires multi-file analysis"
                )
        return None

    def _check_direct_patterns(
        self,
        query: str,
        files_mentioned: List[str]
    ) -> Optional[SpawnDecision]:
        """
        Check if query matches direct action patterns.

        Args:
            query: Query text (lowercase)
            files_mentioned: List of files mentioned

        Returns:
            SpawnDecision if direct action pattern found, None otherwise
        """
        # Check for direct action verbs
        for pattern in self.DIRECT_ACTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                # Determine specific reason
                if re.search(r'\bedit\b', query, re.IGNORECASE):
                    reason = NoSpawnReason.DIRECT_EDIT
                    explanation = "Direct edit command - no need to spawn subagent"
                elif re.search(r'\bread\s+(file|the)\b', query, re.IGNORECASE):
                    reason = NoSpawnReason.SPECIFIC_FILE_KNOWN
                    explanation = "Reading specific file - direct action preferred"
                elif re.search(r'\b(run|execute)\b', query, re.IGNORECASE):
                    reason = NoSpawnReason.SINGLE_COMMAND
                    explanation = "Single command execution - no spawn needed"
                else:
                    reason = NoSpawnReason.DIRECT_EDIT
                    explanation = "Direct action pattern detected - no spawn needed"

                return SpawnDecision(
                    should_spawn=False,
                    reason=reason,
                    confidence=0.75,
                    recommended_agent=None,
                    explanation=explanation
                )

        # Check for specific file with no exploration indicators
        if len(files_mentioned) == 1 and not re.search(r'\b(how|analyze|explore)\b', query, re.IGNORECASE):
            return SpawnDecision(
                should_spawn=False,
                reason=NoSpawnReason.SPECIFIC_FILE_KNOWN,
                confidence=0.7,
                recommended_agent=None,
                explanation="Single specific file mentioned - direct action likely"
            )

        return None

    def _get_recommended_agent(self, query: str, reason: SpawnReason) -> str:
        """
        Determine which agent to recommend based on query content.

        Args:
            query: Query text (lowercase)
            reason: Reason for spawning

        Returns:
            Agent name (defaults to sre_principal_engineer_agent)
        """
        # Check each agent's patterns
        for agent_name, patterns in self.AGENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return agent_name

        # Default to SRE agent
        return "sre_principal_engineer_agent"
