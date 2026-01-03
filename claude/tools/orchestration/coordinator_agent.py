"""
Coordinator Agent - Intelligent Routing for Multi-Agent System

Automatically classifies user intent, assesses complexity, and routes to
optimal agent(s) with appropriate coordination strategy (single, swarm, chain).

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 3
Research: claude/data/AI_SPECIALISTS_AGENT_ANALYSIS.md Section 3.2

Architecture:
    User Query → Intent Classification → Agent Selection → Routing Strategy

    Strategy Options:
    - Single Agent: Simple queries, one domain
    - Swarm: Multi-agent collaboration with handoffs
    - Prompt Chain: Structured multi-step workflows (future)
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

from agent_loader import AgentLoader

# Try to import CapabilityRegistry (optional enhancement)
try:
    from agent_capability_registry import CapabilityRegistry
    CAPABILITY_REGISTRY_AVAILABLE = True
except ImportError:
    CAPABILITY_REGISTRY_AVAILABLE = False

# Try to import ParallelExecutor (Agentic AI Phase 3)
try:
    from parallel_executor import ParallelExecutor
    PARALLEL_EXECUTOR_AVAILABLE = True
except ImportError:
    PARALLEL_EXECUTOR_AVAILABLE = False


@dataclass
class Intent:
    """Classified user intent"""
    category: str           # technical, strategic, operational, analysis, creative
    domains: List[str]      # dns, azure, financial, security, etc.
    complexity: int         # 1-10 scale
    confidence: float       # 0.0-1.0
    entities: Dict[str, Any]  # Extracted entities (domain names, numbers, etc.)


@dataclass
class RoutingDecision:
    """Routing decision with strategy and agents"""
    strategy: str           # single_agent, swarm, prompt_chain
    agents: List[str]       # Agent names to invoke
    initial_agent: str      # First agent to execute
    confidence: float       # 0.0-1.0
    reasoning: str          # Why this routing
    context: Dict[str, Any]  # Initial context for agent


class IntentClassifier:
    """
    Classifies user queries into intent categories.

    Uses keyword matching and pattern recognition (lightweight NLP).
    Future: Could upgrade to ML-based classification.
    """

    # Domain keywords (for detecting which domain query relates to)
    DOMAIN_KEYWORDS = {
        'dns': ['dns', 'domain', 'mx record', 'spf', 'dkim', 'dmarc', 'nameserver', 'dns record', 'email authentication'],
        'azure': ['azure', 'exchange online', 'm365', 'microsoft 365', 'active directory', 'entra', 'cloud', 'tenant'],
        'security': ['security', 'vulnerability', 'threat', 'compliance', 'audit', 'pentesting', 'firewall', 'encryption'],
        'financial': ['budget', 'cost', 'pricing', 'salary', 'tax', 'investment', 'super', 'finance', 'money'],
        'cloud': ['aws', 'gcp', 'cloud', 'infrastructure', 'iaac', 'terraform', 'kubernetes', 'container'],
        'servicedesk': ['ticket', 'complaint', 'service desk', 'incident', 'request', 'helpdesk'],
        'career': ['job', 'interview', 'resume', 'linkedin', 'career', 'recruiter', 'hiring'],
        'data': ['analytics', 'dashboard', 'report', 'metrics', 'kpi', 'visualization', 'data'],
        'sre': ['monitoring', 'slo', 'sli', 'reliability', 'incident', 'postmortem', 'observability', 'testing', 'test', 'validation', 'health check', 'quality check', 'performance', 'deployment', 'production', 'regression'],
        'endpoint': ['laptop', 'macos', 'windows', 'endpoint', 'device', 'intune', 'jamf'],
        'python_review': [
            # Phrase patterns (original)
            'python review', 'code review', 'efficiency review', 'pythonic',
            'code quality', 'python efficiency', 'review python', 'optimize python',
            'refactor python', 'dry violation', 'code conciseness',
            # Phase 228.1: Added flexible patterns for better detection
            'python code',      # Matches "review the python code"
            'review code',      # Matches "review code quality"
            '.py',              # Matches ".py files"
            'python script',    # Matches "review python scripts"
            'analyze python',   # Matches "analyze python code"
            'python file',      # Matches "python files"
            'refactor code',    # Matches "refactor code"
            'code efficiency',  # Matches "check code efficiency"
        ],
    }

    # Intent category patterns
    INTENT_PATTERNS = {
        'technical_question': [
            r'\b(what|how|why|when|where)\b',
            r'\b(explain|tell me|describe)\b',
            r'\?$',
        ],
        'operational_task': [
            r'\b(setup|configure|install|deploy|migrate|create)\b',
            r'\b(fix|resolve|troubleshoot|debug)\b',
            r'\b(update|upgrade|patch)\b',
        ],
        'strategic_planning': [
            r'\b(plan|strategy|roadmap|architecture)\b',
            r'\b(should I|should we|recommend|advise|suggest)\b',
            r'\b(optimize|improve|enhance)\b',
        ],
        'analysis_research': [
            r'\b(analyze|assess|evaluate|review)\b',
            r'\b(research|investigate|compare)\b',
            r'\b(report|summary|findings)\b',
        ],
        'creative_generation': [
            r'\b(write|create|generate|draft)\b',
            r'\b(blog|article|presentation|document)\b',
        ],
    }

    # Complexity indicators (patterns that suggest high complexity)
    COMPLEXITY_INDICATORS = {
        'multi_domain': 2,      # Multiple domains mentioned
        'multi_step': 2,        # "and then", "after that"
        'large_scale': 2,       # "100 users", "enterprise"
        'integration': 2,       # "integrate", "connect" - increased from 1 to 2
        'migration': 2,         # "migrate", "move from"
        'custom': 2,            # "custom", "specific" - increased from 1 to 2
        'urgent': 1,            # "urgent", "asap", "emergency"
    }

    def classify(self, user_query: str) -> Intent:
        """
        Classify user query into intent.

        Args:
            user_query: Natural language query from user

        Returns:
            Intent with category, domains, complexity, confidence
        """
        query_lower = user_query.lower()

        # Detect domains
        domains = self._detect_domains(query_lower)

        # Detect intent category
        category = self._detect_category(query_lower)

        # Assess complexity
        complexity = self._assess_complexity(query_lower, domains)

        # Extract entities
        entities = self._extract_entities(user_query)

        # Calculate confidence (simple heuristic)
        confidence = self._calculate_confidence(domains, category)

        return Intent(
            category=category,
            domains=domains,
            complexity=complexity,
            confidence=confidence,
            entities=entities
        )

    def _detect_domains(self, query_lower: str) -> List[str]:
        """Detect which domains query relates to"""
        detected = []

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if domain not in detected:
                        detected.append(domain)
                    break  # Found domain, move to next

        # If no domains detected, mark as general
        if not detected:
            detected = ['general']

        return detected

    def _detect_category(self, query_lower: str) -> str:
        """Detect intent category"""
        scores = {}

        for category, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 1
            scores[category] = score

        # Boost strategic_planning for "should I" questions
        if re.search(r'\bshould\s+i\b', query_lower, re.IGNORECASE):
            scores['strategic_planning'] = scores.get('strategic_planning', 0) + 2

        # Return category with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        # Default: operational task
        return 'operational_task'

    def _assess_complexity(self, query_lower: str, domains: List[str]) -> int:
        """
        Assess query complexity on 1-10 scale.

        Factors:
        - Number of domains (1 domain = simple, 2+ = complex)
        - Complexity indicators (migration, integration, etc.)
        - Query length (longer = more complex)
        - SRE/reliability work (always considered complex)
        """
        complexity = 3  # Base complexity

        # 🚨 SRE ENFORCEMENT BOOST (Phase 134.2)
        # Reliability/testing work is inherently complex - boost to ensure routing
        sre_keywords = [
            'test', 'testing', 'reliability', 'production', 'monitoring',
            'slo', 'sli', 'observability', 'incident', 'health check',
            'regression', 'performance', 'validation', 'integration test',
            'spot-check', 'quality check', 'deployment', 'ci/cd'
        ]
        if any(keyword in query_lower for keyword in sre_keywords):
            complexity = max(complexity, 5)  # Boost to at least 5 for SRE work

        # Multiple domains increase complexity
        if len(domains) > 1:
            complexity += self.COMPLEXITY_INDICATORS['multi_domain']

        # Check for complexity indicators
        if re.search(r'\band then\b|\bafter that\b', query_lower):
            complexity += self.COMPLEXITY_INDICATORS['multi_step']

        if re.search(r'\b\d+\s*(users?|mailboxes?|devices?)\b', query_lower):
            num_match = re.search(r'\b(\d+)\s*users?', query_lower)
            if num_match and int(num_match.group(1)) > 50:
                complexity += self.COMPLEXITY_INDICATORS['large_scale']

        if re.search(r'\bmigrate\b|\bmigration\b|\bmove from\b', query_lower):
            complexity += self.COMPLEXITY_INDICATORS['migration']

        if re.search(r'\bintegrate\b|\bconnect\b|\blink\b', query_lower):
            complexity += self.COMPLEXITY_INDICATORS['integration']

        if re.search(r'\bcustom\b|\bspecific\b|\btailored\b', query_lower):
            complexity += self.COMPLEXITY_INDICATORS['custom']

        if re.search(r'\burgent\b|\basap\b|\bemergency\b|\bimmediate\b', query_lower):
            complexity += self.COMPLEXITY_INDICATORS['urgent']

        # Cap at 10
        return min(complexity, 10)

    def _extract_entities(self, user_query: str) -> Dict[str, Any]:
        """Extract entities from query (domain names, numbers, etc.)"""
        entities = {}

        # Extract domain names (simple pattern)
        domain_pattern = r'\b([a-z0-9-]+\.(?:com|net|org|io|co|au))\b'
        domains_found = re.findall(domain_pattern, user_query.lower())
        if domains_found:
            entities['domains'] = domains_found

        # Extract numbers (user counts, budgets, etc.)
        number_pattern = r'\b(\d+)\s*(users?|mailboxes?|devices?|dollars?|AUD|USD)?\b'
        numbers_found = re.findall(number_pattern, user_query)
        if numbers_found:
            entities['numbers'] = [
                {'value': int(num[0]), 'unit': num[1] if num[1] else 'count'}
                for num in numbers_found
            ]

        # Extract email addresses
        email_pattern = r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b'
        emails_found = re.findall(email_pattern, user_query.lower())
        if emails_found:
            entities['emails'] = emails_found

        return entities

    def _calculate_confidence(self, domains: List[str], category: str) -> float:
        """Calculate confidence in classification"""
        confidence = 0.8  # Base confidence

        # 🚨 SRE ENFORCEMENT BOOST (Phase 134.2)
        # High confidence for SRE domain (reliability work is clear-cut)
        if 'sre' in domains:
            confidence = 0.9

        # Lower confidence if no specific domains detected
        if domains == ['general']:
            confidence -= 0.2

        # Higher confidence if specific category matched
        if category != 'operational_task':  # Default fallback
            confidence += 0.1

        return min(confidence, 1.0)


class AgentSelector:
    """
    Selects optimal agent(s) based on classified intent.

    Uses agent specialties, domains, and complexity to determine:
    1. Which agent(s) to use
    2. What coordination strategy (single, swarm, chain)
    3. Initial context for agents
    """

    # Domain → Agent mapping
    DOMAIN_AGENT_MAP = {
        'dns': 'dns_specialist',
        'azure': 'azure_solutions_architect',
        'security': 'cloud_security_principal',
        'financial': 'financial_advisor',
        'cloud': 'principal_cloud_architect',
        'servicedesk': 'service_desk_manager',
        'career': 'jobs_agent',
        'data': 'data_analyst',
        'sre': 'sre_principal_engineer',
        'endpoint': 'principal_endpoint_engineer',
        'python_review': 'python_code_reviewer',
    }

    def __init__(self, agent_loader: AgentLoader = None, use_capability_registry: bool = False, use_adaptive_routing: bool = True):
        """
        Initialize with agent loader and optional capability registry.

        Args:
            agent_loader: Agent loader instance
            use_capability_registry: Use CapabilityRegistry for dynamic agent matching
            use_adaptive_routing: Use AdaptiveRoutingSystem for learning thresholds (Phase 1 Agentic AI)
        """
        self.agent_loader = agent_loader or AgentLoader()
        self.use_registry = use_capability_registry and CAPABILITY_REGISTRY_AVAILABLE

        # Initialize capability registry if available
        if self.use_registry:
            try:
                self.capability_registry = CapabilityRegistry()
                print(f"✅ Capability Registry enabled ({len(self.capability_registry.capabilities)} agents)")
            except Exception as e:
                print(f"⚠️  Capability Registry failed to initialize: {e}")
                self.use_registry = False
                self.capability_registry = None
        else:
            self.capability_registry = None

        # Initialize adaptive routing system (Phase 1 Agentic AI Enhancement)
        self.use_adaptive_routing = use_adaptive_routing
        self.adaptive_routing = None
        if use_adaptive_routing:
            try:
                from adaptive_routing import AdaptiveRoutingSystem
                self.adaptive_routing = AdaptiveRoutingSystem()
            except ImportError:
                self.use_adaptive_routing = False

        # Initialize parallel executor (Phase 3 Agentic AI Enhancement)
        self.parallel_executor = None
        if PARALLEL_EXECUTOR_AVAILABLE:
            try:
                self.parallel_executor = ParallelExecutor()
            except Exception:
                pass

    def select(self, intent: Intent, user_query: str) -> RoutingDecision:
        """
        Select optimal routing strategy and agents.

        Args:
            intent: Classified intent from IntentClassifier
            user_query: Original user query

        Returns:
            RoutingDecision with strategy, agents, context
        """
        # 🚨 SRE ENFORCEMENT RULE (Phase 134.2)
        # For reliability/testing/production work, ALWAYS route to SRE Principal Engineer
        # Other agents can be consulted, but SRE delivers the final implementation
        sre_keywords = [
            'test', 'testing', 'reliability', 'production', 'monitoring',
            'slo', 'sli', 'observability', 'incident', 'health check',
            'regression', 'performance', 'validation', 'integration test',
            'spot-check', 'quality check', 'deployment', 'ci/cd'
        ]

        query_lower = user_query.lower()
        if any(keyword in query_lower for keyword in sre_keywords):
            # Route to SRE Principal Engineer for reliability work
            context = {
                'query': user_query,
                'intent_category': intent.category,
                'complexity': intent.complexity,
                'entities': intent.entities,
                'enforcement_reason': 'SRE enforcement rule - reliability/testing work'
            }

            return RoutingDecision(
                strategy='single_agent',
                agents=['sre_principal_engineer'],
                initial_agent='sre_principal_engineer',
                confidence=0.95,  # High confidence for enforced routing
                reasoning="SRE enforcement: reliability/testing work requires SRE Principal Engineer",
                context=context
            )

        # Agentic AI Phase 3: Check for parallelizable tasks
        if self.parallel_executor:
            try:
                parallel_tasks = self.parallel_executor.identify_parallel_tasks(user_query)
                if len(parallel_tasks) > 1:
                    deps = self.parallel_executor.detect_dependencies(parallel_tasks)
                    if not deps.get('has_dependencies', True):
                        return self._route_parallel(intent, user_query, parallel_tasks)
            except Exception:
                pass  # Fall through to normal routing

        # Normal routing logic for other queries
        # Determine strategy based on complexity and domains
        # Phase 1 Agentic AI: Use adaptive thresholds if available
        primary_domain = intent.domains[0] if intent.domains else 'general'

        if self.use_adaptive_routing and self.adaptive_routing:
            should_load, reasoning = self.adaptive_routing.should_load_agent(
                primary_domain, intent.complexity
            )
            agent_threshold = self.adaptive_routing.get_threshold(primary_domain).current_threshold
        else:
            # Fallback to fixed threshold
            agent_threshold = 3
            should_load = intent.complexity >= agent_threshold
            reasoning = f"Fixed threshold: {intent.complexity} >= {agent_threshold}"

        if not should_load and len(intent.domains) == 1:
            # Simple single-domain task - no agent needed
            return self._route_single_agent(intent, user_query)

        elif intent.complexity <= 6 or len(intent.domains) <= 2:
            # Medium complexity or 2 domains → Swarm (dynamic handoffs)
            return self._route_swarm(intent, user_query)

        else:
            # High complexity (7+) → Swarm with multiple agents
            return self._route_complex_swarm(intent, user_query)

    def _route_single_agent(self, intent: Intent, user_query: str) -> RoutingDecision:
        """Route to single agent (simple queries)"""
        domain = intent.domains[0]

        # Try capability-based matching first
        if self.use_registry and self.capability_registry:
            matches = self.capability_registry.match_query(user_query, top_k=1, min_score=0.4)
            if matches:
                agent = matches[0][0]  # Top match
            else:
                agent = self.DOMAIN_AGENT_MAP.get(domain, 'ai_specialists_agent')
        else:
            agent = self.DOMAIN_AGENT_MAP.get(domain, 'ai_specialists_agent')

        context = {
            'query': user_query,
            'intent_category': intent.category,
            'complexity': intent.complexity,
            'entities': intent.entities
        }

        return RoutingDecision(
            strategy='single_agent',
            agents=[agent],
            initial_agent=agent,
            confidence=intent.confidence,
            reasoning=f"Simple {domain} query, single specialist sufficient",
            context=context
        )

    def _route_swarm(self, intent: Intent, user_query: str) -> RoutingDecision:
        """Route to swarm (medium complexity, potential handoffs)"""
        # Primary domain determines initial agent
        primary_domain = intent.domains[0]
        initial_agent = self.DOMAIN_AGENT_MAP.get(primary_domain, 'ai_specialists_agent')

        # List likely agents (for context, actual handoffs determined dynamically)
        likely_agents = [
            self.DOMAIN_AGENT_MAP.get(d, 'ai_specialists_agent')
            for d in intent.domains
        ]

        context = {
            'query': user_query,
            'intent_category': intent.category,
            'complexity': intent.complexity,
            'entities': intent.entities,
            'domains_involved': intent.domains
        }

        return RoutingDecision(
            strategy='swarm',
            agents=likely_agents,
            initial_agent=initial_agent,
            confidence=intent.confidence * 0.9,  # Slightly lower for multi-agent
            reasoning=f"Multi-domain task ({', '.join(intent.domains)}), swarm collaboration recommended",
            context=context
        )

    def _route_complex_swarm(self, intent: Intent, user_query: str) -> RoutingDecision:
        """Route complex queries (7+ complexity)"""
        # For very complex tasks, start with most relevant specialist
        primary_domain = intent.domains[0]
        initial_agent = self.DOMAIN_AGENT_MAP.get(primary_domain, 'principal_cloud_architect')

        # Include all relevant agents
        agents = [
            self.DOMAIN_AGENT_MAP.get(d, 'ai_specialists_agent')
            for d in intent.domains
        ]

        context = {
            'query': user_query,
            'intent_category': intent.category,
            'complexity': intent.complexity,
            'entities': intent.entities,
            'domains_involved': intent.domains,
            'coordination_hint': 'Complex multi-agent workflow - expect multiple handoffs'
        }

        return RoutingDecision(
            strategy='swarm',
            agents=agents,
            initial_agent=initial_agent,
            confidence=intent.confidence * 0.85,  # Lower for very complex
            reasoning=f"High complexity ({intent.complexity}/10), multi-domain ({len(intent.domains)} domains), swarm collaboration required",
            context=context
        )

    def _route_parallel(
        self,
        intent: Intent,
        user_query: str,
        parallel_tasks: List[str]
    ) -> RoutingDecision:
        """
        Route to parallel execution (Agentic AI Phase 3).

        Used when query contains independent subtasks that can be
        executed concurrently (e.g., "search linkedin and github").

        Args:
            intent: Classified intent
            user_query: Original query
            parallel_tasks: List of identified parallel tasks

        Returns:
            RoutingDecision with parallel strategy
        """
        # Determine agents for each task based on domains
        primary_domain = intent.domains[0] if intent.domains else 'general'
        agents = []

        for _ in parallel_tasks:
            agent = self.DOMAIN_AGENT_MAP.get(primary_domain, 'ai_specialists_agent')
            if agent not in agents:
                agents.append(agent)

        # If multiple domains detected, add those agents
        for domain in intent.domains:
            agent = self.DOMAIN_AGENT_MAP.get(domain, 'ai_specialists_agent')
            if agent not in agents:
                agents.append(agent)

        context = {
            'query': user_query,
            'intent_category': intent.category,
            'complexity': intent.complexity,
            'entities': intent.entities,
            'parallel_tasks': parallel_tasks,
            'coordination_hint': 'Parallel execution - merge results when complete'
        }

        return RoutingDecision(
            strategy='parallel',
            agents=agents,
            initial_agent=agents[0] if agents else 'ai_specialists_agent',
            confidence=intent.confidence * 0.9,
            reasoning=f"Parallel execution: {len(parallel_tasks)} independent tasks identified",
            context=context
        )


class CoordinatorAgent:
    """
    Main Coordinator Agent for intelligent routing.

    Entry point for all user queries. Classifies intent, selects agents,
    and returns routing decision for execution.

    Usage:
        coordinator = CoordinatorAgent()
        routing = coordinator.route("Setup Azure Exchange Online")

        # Execute routing
        if routing.strategy == 'single_agent':
            # Load and execute single agent
        elif routing.strategy == 'swarm':
            # Use SwarmOrchestrator
    """

    def __init__(self, agent_loader: AgentLoader = None):
        """Initialize coordinator with classifiers and selectors"""
        self.intent_classifier = IntentClassifier()
        self.agent_selector = AgentSelector(agent_loader)
        self.routing_history: List[Dict] = []

    def route(self, user_query: str) -> RoutingDecision:
        """
        Main routing function - classifies and selects agents.

        Args:
            user_query: Natural language query from user

        Returns:
            RoutingDecision with strategy, agents, and context

        Example:
            routing = coordinator.route("Setup email authentication for example.com")
            # routing.strategy = "single_agent"
            # routing.initial_agent = "dns_specialist"
            # routing.context = {"query": "...", "entities": {...}}
        """
        # Step 1: Classify intent
        intent = self.intent_classifier.classify(user_query)

        # Step 2: Select agents and strategy
        routing = self.agent_selector.select(intent, user_query)

        # Step 3: Record routing decision (for learning)
        self._record_routing(user_query, intent, routing)

        return routing

    def _record_routing(self, query: str, intent: Intent, routing: RoutingDecision):
        """Record routing decision for pattern learning"""
        self.routing_history.append({
            'query': query,
            'intent': {
                'category': intent.category,
                'domains': intent.domains,
                'complexity': intent.complexity
            },
            'routing': {
                'strategy': routing.strategy,
                'agents': routing.agents,
                'initial_agent': routing.initial_agent
            }
        })

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing patterns"""
        if not self.routing_history:
            return {'total_routes': 0}

        strategy_counts = {}
        agent_counts = {}

        for record in self.routing_history:
            # Count strategies
            strategy = record['routing']['strategy']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            # Count initial agents
            agent = record['routing']['initial_agent']
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            'total_routes': len(self.routing_history),
            'strategies': strategy_counts,
            'most_used_agents': sorted(
                agent_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    def record_outcome(
        self,
        query: str,
        domain: str,
        complexity: int,
        agent_used: str = None,
        success: bool = True,
        quality_score: float = 0.8,
        user_corrections: int = 0
    ):
        """
        Record task outcome for adaptive routing learning.

        Phase 1 Agentic AI Enhancement: Feed outcomes back to
        AdaptiveRoutingSystem so thresholds can learn.

        Args:
            query: Original user query
            domain: Task domain (e.g., 'sre', 'security')
            complexity: Task complexity (1-10)
            agent_used: Agent that handled the task (None if no agent)
            success: Whether task completed successfully
            quality_score: Quality of result (0.0-1.0)
            user_corrections: Number of user corrections needed
        """
        if not self.agent_selector.use_adaptive_routing:
            return

        if self.agent_selector.adaptive_routing is None:
            return

        try:
            from adaptive_routing import TaskOutcome, generate_task_id
            from datetime import datetime

            outcome = TaskOutcome(
                task_id=generate_task_id(),
                timestamp=datetime.now(),
                query=query,
                domain=domain,
                complexity=complexity,
                agent_used=agent_used,
                agent_loaded=agent_used is not None,
                success=success,
                quality_score=quality_score,
                user_corrections=user_corrections
            )

            self.agent_selector.adaptive_routing.record_outcome(outcome)
        except ImportError:
            pass  # Graceful degradation

        # Phase 2: Also record to continuous evaluation system
        try:
            from continuous_eval import ContinuousEvaluationSystem, EvaluationRecord

            eval_system = ContinuousEvaluationSystem()
            eval_record = EvaluationRecord(
                task_id=generate_task_id(),
                timestamp=datetime.now(),
                agent_used=agent_used,
                query=query,
                domain=domain,
                complexity=complexity,
                output_quality=quality_score,
                task_completed=success,
                user_rating=None,
                auto_score=quality_score,
                issues_found=[]
            )
            eval_system.record_evaluation(eval_record)
        except ImportError:
            pass  # Graceful degradation


# Convenience function
def route_query(user_query: str) -> RoutingDecision:
    """
    Convenience function for quick routing.

    Usage:
        routing = route_query("Setup email for company.com")
        print(f"Strategy: {routing.strategy}")
        print(f"Initial agent: {routing.initial_agent}")
    """
    coordinator = CoordinatorAgent()
    return coordinator.route(user_query)


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE (Phase 121 - Automatic Agent Routing)
# ═══════════════════════════════════════════════════════════════════

def format_routing_output(routing: RoutingDecision) -> str:
    """
    Format routing decision for hook display.

    Returns formatted string for user-prompt-submit hook output.
    """
    if not routing:
        return ""

    # Only display routing for non-trivial queries (complexity > 3, confidence > 70%)
    if routing.complexity < 3 or routing.confidence < 0.70:
        # General query - no specific routing needed
        return None

    if not routing.agents:
        return None

    output = []
    output.append(f"   Intent: {routing.intent.category}")
    output.append(f"   Domains: {', '.join(routing.intent.domains)}")
    output.append(f"   Complexity: {routing.complexity}/10")
    output.append(f"   Confidence: {int(routing.confidence * 100)}%")
    output.append("")

    if len(routing.agents) == 1:
        output.append(f"   💡 SUGGESTED AGENT: {routing.initial_agent}")
    else:
        output.append(f"   💡 SUGGESTED AGENTS: {', '.join(routing.agents)}")

    output.append(f"   📋 Reason: {routing.reasoning}")
    output.append(f"   🎯 Strategy: {routing.strategy.upper().replace('_', ' ')}")

    return "\n".join(output)


def cli_classify(query: str, json_output: bool = False) -> int:
    """
    CLI classify command for hook integration.

    Args:
        query: User query to classify
        json_output: If True, output JSON instead of human-readable format

    Returns:
        0: Routing suggestion available
        1: Classification error
        2: No specific routing needed (general query)
    """
    try:
        coordinator = CoordinatorAgent()

        # Get intent first
        intent = coordinator.intent_classifier.classify(query)

        # Only display routing for non-trivial queries (complexity > 3, confidence > 70%)
        if intent.complexity < 3 or intent.confidence < 0.70:
            # General query - no specific routing needed
            if json_output:
                import json
                print(json.dumps({
                    "routing_needed": False,
                    "intent": {
                        "category": intent.category,
                        "domains": intent.domains,
                        "complexity": intent.complexity,
                        "confidence": intent.confidence
                    }
                }))
            return 2

        # Get routing decision
        routing = coordinator.agent_selector.select(intent, query)

        if not routing or not routing.agents:
            if json_output:
                import json
                print(json.dumps({"routing_needed": False}))
            return 2

        # JSON output format (Phase 134 - Swarm Auto-Loader integration)
        if json_output:
            import json
            output_data = {
                "routing_needed": True,
                "intent": {
                    "category": intent.category,
                    "domains": intent.domains,
                    "complexity": intent.complexity,
                    "confidence": intent.confidence,
                    "primary_domain": intent.domains[0] if intent.domains else "general"
                },
                "routing": {
                    "strategy": routing.strategy,
                    "agents": routing.agents,
                    "initial_agent": routing.initial_agent,
                    "confidence": routing.confidence,
                    "reasoning": routing.reasoning
                }
            }
            print(json.dumps(output_data))
            return 0

        # Human-readable output format (original)
        output = []
        output.append(f"   Intent: {intent.category}")
        output.append(f"   Domains: {', '.join(intent.domains)}")
        output.append(f"   Complexity: {intent.complexity}/10")
        output.append(f"   Confidence: {int(intent.confidence * 100)}%")
        output.append("")

        if len(routing.agents) == 1:
            output.append(f"   💡 SUGGESTED AGENT: {routing.initial_agent}")
        else:
            output.append(f"   💡 SUGGESTED AGENTS: {', '.join(routing.agents)}")

        output.append(f"   📋 Reason: {routing.reasoning}")
        output.append(f"   🎯 Strategy: {routing.strategy.upper().replace('_', ' ')}")

        # Display routing suggestion
        print("\n".join(output))
        return 0

    except Exception as e:
        # Classification failed - fallback to normal
        import sys
        print(f"⚠️  Classification error: {str(e)}", file=sys.stderr)
        return 1


def cli_classify_and_log(query: str) -> int:
    """
    CLI classify command with Phase 122 logging.

    Logs routing decision to routing_decisions.db for accuracy tracking.

    Returns:
        0: Routing suggestion logged
        1: Classification error
        2: No specific routing needed (general query)
    """
    try:
        # Import logger (Phase 122)
        from routing_decision_logger import RoutingDecisionLogger, RoutingIntent, RoutingDecision

        coordinator = CoordinatorAgent()

        # Get intent first
        intent = coordinator.intent_classifier.classify(query)

        # Only log non-trivial queries
        if intent.complexity < 3 or intent.confidence < 0.70:
            return 2

        # Get routing decision
        routing = coordinator.agent_selector.select(intent, query)

        if not routing or not routing.agents:
            return 2

        # Log to database (Phase 122)
        logger = RoutingDecisionLogger()

        routing_intent = RoutingIntent(
            category=intent.category,
            domains=intent.domains,
            complexity=intent.complexity,
            confidence=intent.confidence
        )

        routing_decision = RoutingDecision(
            agents=routing.agents,
            initial_agent=routing.initial_agent,
            strategy=routing.strategy,
            reasoning=routing.reasoning,
            confidence=routing.confidence
        )

        query_hash = logger.log_suggestion(query, routing_intent, routing_decision)

        # Silent success - no output (used in hook)
        return 0

    except Exception as e:
        # Silent failure - don't break hook
        import sys
        print(f"⚠️  Logging error: {str(e)}", file=sys.stderr)
        return 1


def main():
    """CLI interface for coordinator agent."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: coordinator_agent.py classify <query> [--log] [--json]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  classify <query>        - Classify query and suggest agent routing", file=sys.stderr)
        print("  classify <query> --log  - Classify and log to database (Phase 125)", file=sys.stderr)
        print("  classify <query> --json - Output JSON format (Phase 134)", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "classify":
        if len(sys.argv) < 3:
            print("Error: classify requires a query argument", file=sys.stderr)
            sys.exit(1)

        query = sys.argv[2]

        # Check for flags (Phase 125: --log, Phase 134: --json)
        flags = sys.argv[3:] if len(sys.argv) > 3 else []

        if "--log" in flags:
            exit_code = cli_classify_and_log(query)
        elif "--json" in flags:
            exit_code = cli_classify(query, json_output=True)
        else:
            exit_code = cli_classify(query, json_output=False)

        sys.exit(exit_code)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Use 'classify' command for agent routing", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
