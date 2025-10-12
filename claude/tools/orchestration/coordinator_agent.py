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
        'sre': ['monitoring', 'slo', 'sli', 'reliability', 'incident', 'postmortem', 'observability'],
        'endpoint': ['laptop', 'macos', 'windows', 'endpoint', 'device', 'intune', 'jamf'],
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
        """
        complexity = 3  # Base complexity

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
    }

    def __init__(self, agent_loader: AgentLoader = None):
        """Initialize with agent loader"""
        self.agent_loader = agent_loader or AgentLoader()

    def select(self, intent: Intent, user_query: str) -> RoutingDecision:
        """
        Select optimal routing strategy and agents.

        Args:
            intent: Classified intent from IntentClassifier
            user_query: Original user query

        Returns:
            RoutingDecision with strategy, agents, context
        """
        # Determine strategy based on complexity and domains
        if intent.complexity <= 3 and len(intent.domains) == 1:
            # Simple single-domain task
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
        agent = self.DOMAIN_AGENT_MAP.get(domain, 'ai_specialists_agent')  # Fallback to AI Specialists

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
