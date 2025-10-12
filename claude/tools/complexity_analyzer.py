#!/usr/bin/env python3
"""
Complexity Analyzer - Assess query complexity for routing decisions

Analyzes queries to determine complexity (1-10 scale) based on multiple
factors including domains, phases, ambiguity, scale, and urgency.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 3
Purpose: Help coordinator agent make intelligent routing decisions
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ComplexityLevel(Enum):
    """Complexity levels with numeric values"""
    TRIVIAL = (1, 2)        # 1-2: Definitions, lookups
    SIMPLE = (3, 4)         # 3-4: Single-domain, clear steps
    MODERATE = (5, 6)       # 5-6: Multi-phase or cross-domain
    COMPLEX = (7, 8)        # 7-8: Multi-domain, diagnosis + remediation
    VERY_COMPLEX = (9, 10)  # 9-10: Strategic, 4+ phases


@dataclass
class ComplexityAssessment:
    """Complexity assessment result"""
    score: int              # 1-10 scale
    level: ComplexityLevel  # TRIVIAL, SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX
    factors: Dict[str, int] # Contributing factors with scores
    phases: List[str]       # Detected phases (diagnosis, remediation, validation, etc.)
    reasoning: str          # Why this complexity score
    confidence: float       # 0.0-1.0


class ComplexityAnalyzer:
    """
    Analyzes query complexity for routing decisions.

    Complexity assessment based on:
    - Number of domains involved
    - Number of phases/steps required
    - Ambiguity of requirements
    - Scale (users, systems, data volume)
    - Urgency indicators
    - Cross-system dependencies
    """

    # Complexity factors with point values
    COMPLEXITY_FACTORS = {
        'multi_domain': 2,          # Multiple domains (Azure + DNS + Security)
        'multi_phase': 2,           # Multiple execution phases (diagnosis → remediation)
        'diagnosis_required': 2,    # Need to investigate before acting
        'ambiguous_requirements': 1, # Vague/unclear requirements
        'large_scale': 2,           # 100+ users, enterprise-wide
        'cross_system': 2,          # Multiple systems/integrations
        'migration': 2,             # Major changes, migrations
        'urgent': 1,                # High priority, time-sensitive
        'strategic': 2,             # Architecture, roadmap, planning
        'custom': 1,                # Non-standard, custom solutions
    }

    # Phase indicators (patterns that suggest specific phases)
    PHASE_PATTERNS = {
        'diagnosis': [
            r'\b(why|investigate|find out|diagnose|identify|analyze|assess)\b',
            r'\b(not working|broken|issue|problem)\b',
        ],
        'planning': [
            r'\b(plan|strategy|roadmap|design|architecture)\b',
            r'\b(should I|should we|recommend|approach)\b',
        ],
        'implementation': [
            r'\b(setup|configure|install|deploy|create|build)\b',
            r'\b(implement|develop|code|write)\b',
        ],
        'remediation': [
            r'\b(fix|resolve|repair|correct|remediate)\b',
            r'\b(troubleshoot|debug)\b',
        ],
        'validation': [
            r'\b(test|verify|validate|check|confirm)\b',
            r'\b(ensure|guarantee)\b',
        ],
        'optimization': [
            r'\b(optimize|improve|enhance|refactor|tune)\b',
            r'\b(performance|efficiency)\b',
        ],
        'migration': [
            r'\b(migrate|move|transition|switch|upgrade)\b',
            r'\b(from .+ to)\b',
        ],
        'monitoring': [
            r'\b(monitor|track|alert|observe|dashboard)\b',
            r'\b(metrics|slo|sli)\b',
        ],
    }

    # Scale indicators
    SCALE_PATTERNS = {
        'small': (r'\b(1|2|3|4|5|few|couple)\s+(user|server|device|tenant)', 1),
        'medium': (r'\b([1-4]\d|50)\s+(user|server|device|tenant)', 2),
        'large': (r'\b(\d{3,}|[5-9]\d|100\+?)\s+(user|server|device|tenant)', 3),
        'enterprise': (r'\b(enterprise|organization-wide|company-wide|global)\b', 3),
    }

    def analyze(
        self,
        query: str,
        domains: List[str],
        category: str,
        entities: Dict[str, Any] = None
    ) -> ComplexityAssessment:
        """
        Analyze query complexity.

        Args:
            query: User query text
            domains: Detected domains (from IntentClassifier)
            category: Intent category (from IntentClassifier)
            entities: Extracted entities (from IntentClassifier)

        Returns:
            ComplexityAssessment with score, level, factors, reasoning
        """
        query_lower = query.lower()
        factors = {}
        base_score = 3  # Start with SIMPLE baseline

        # Factor 1: Multi-domain complexity
        if len(domains) > 1 and 'general' not in domains:
            factors['multi_domain'] = self.COMPLEXITY_FACTORS['multi_domain']
            base_score += factors['multi_domain']

        # Factor 2: Detect phases
        phases = self._detect_phases(query_lower)
        if len(phases) >= 3:
            factors['multi_phase'] = self.COMPLEXITY_FACTORS['multi_phase']
            base_score += factors['multi_phase']

        # Factor 3: Diagnosis required
        if 'diagnosis' in phases or any(pattern in query_lower for pattern in ['why', 'investigate', 'find out']):
            factors['diagnosis_required'] = self.COMPLEXITY_FACTORS['diagnosis_required']
            base_score += factors['diagnosis_required']

        # Factor 4: Ambiguous requirements
        ambiguity_indicators = ['not working', 'broken', 'issues', 'problems', 'terrible', 'bad']
        if any(indicator in query_lower for indicator in ambiguity_indicators):
            factors['ambiguous_requirements'] = self.COMPLEXITY_FACTORS['ambiguous_requirements']
            base_score += factors['ambiguous_requirements']

        # Factor 5: Scale assessment
        scale_score = self._assess_scale(query_lower, entities)
        if scale_score >= 2:
            factors['large_scale'] = self.COMPLEXITY_FACTORS['large_scale']
            base_score += factors['large_scale']

        # Factor 6: Cross-system integration
        integration_patterns = ['integrate', 'connect', 'sync', 'link', 'between']
        if any(pattern in query_lower for pattern in integration_patterns):
            factors['cross_system'] = self.COMPLEXITY_FACTORS['cross_system']
            base_score += factors['cross_system']

        # Factor 7: Migration complexity
        if 'migration' in phases or re.search(r'\b(migrate|move from|transition)\b', query_lower):
            factors['migration'] = self.COMPLEXITY_FACTORS['migration']
            base_score += factors['migration']

        # Factor 8: Urgency
        if re.search(r'\b(urgent|asap|emergency|critical|immediately)\b', query_lower):
            factors['urgent'] = self.COMPLEXITY_FACTORS['urgent']
            base_score += factors['urgent']

        # Factor 9: Strategic planning
        if category == 'strategic_planning' or 'planning' in phases:
            factors['strategic'] = self.COMPLEXITY_FACTORS['strategic']
            base_score += factors['strategic']

        # Factor 10: Custom/specific requirements
        if re.search(r'\b(custom|specific|tailored|bespoke)\b', query_lower):
            factors['custom'] = self.COMPLEXITY_FACTORS['custom']
            base_score += factors['custom']

        # Cap at 10
        final_score = min(base_score, 10)

        # Determine complexity level
        level = self._determine_level(final_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(final_score, factors, phases, domains, category)

        # Calculate confidence
        confidence = self._calculate_confidence(factors, phases)

        return ComplexityAssessment(
            score=final_score,
            level=level,
            factors=factors,
            phases=phases,
            reasoning=reasoning,
            confidence=confidence
        )

    def _detect_phases(self, query_lower: str) -> List[str]:
        """Detect execution phases required"""
        detected_phases = []

        for phase, patterns in self.PHASE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    if phase not in detected_phases:
                        detected_phases.append(phase)
                    break  # Found phase, move to next

        return detected_phases

    def _assess_scale(self, query_lower: str, entities: Dict[str, Any] = None) -> int:
        """Assess scale complexity (1-3)"""
        scale_score = 0

        # Check scale patterns
        for scale_type, (pattern, score) in self.SCALE_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                scale_score = max(scale_score, score)

        # Check entities for scale information
        if entities and 'scale' in entities:
            # Extract number from scale entity
            for scale_info in entities['scale']:
                if isinstance(scale_info, tuple):
                    num_str = scale_info[0]
                    # Convert '500' or '5k' to number
                    if 'k' in num_str.lower():
                        num = int(num_str.lower().replace('k', '')) * 1000
                    else:
                        num = int(num_str)

                    if num >= 100:
                        scale_score = max(scale_score, 3)
                    elif num >= 50:
                        scale_score = max(scale_score, 2)

        return scale_score

    def _determine_level(self, score: int) -> ComplexityLevel:
        """Determine complexity level from score"""
        if score <= 2:
            return ComplexityLevel.TRIVIAL
        elif score <= 4:
            return ComplexityLevel.SIMPLE
        elif score <= 6:
            return ComplexityLevel.MODERATE
        elif score <= 8:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX

    def _generate_reasoning(
        self,
        score: int,
        factors: Dict[str, int],
        phases: List[str],
        domains: List[str],
        category: str
    ) -> str:
        """Generate human-readable reasoning for complexity score"""
        reasoning_parts = [f"Complexity: {score}/10 ({self._determine_level(score).name})"]

        # Explain factors
        if factors:
            factor_list = [f"{name.replace('_', ' ')} (+{value})" for name, value in factors.items()]
            reasoning_parts.append(f"Factors: {', '.join(factor_list)}")

        # Explain phases
        if phases:
            reasoning_parts.append(f"Phases: {', '.join(phases)} ({len(phases)} phases)")

        # Explain domains
        if len(domains) > 1 and 'general' not in domains:
            reasoning_parts.append(f"Multi-domain: {', '.join(domains)}")

        # Category context
        reasoning_parts.append(f"Category: {category}")

        return " | ".join(reasoning_parts)

    def _calculate_confidence(self, factors: Dict[str, int], phases: List[str]) -> float:
        """Calculate confidence in complexity assessment"""
        confidence = 0.7  # Base confidence

        # Boost for multiple factors (more signals = higher confidence)
        if len(factors) >= 3:
            confidence += 0.15
        elif len(factors) >= 2:
            confidence += 0.10

        # Boost for clear phases detected
        if len(phases) >= 2:
            confidence += 0.10

        # Cap at 0.95
        return min(confidence, 0.95)

    def suggest_routing_strategy(self, complexity: ComplexityAssessment, domains: List[str]) -> str:
        """
        Suggest routing strategy based on complexity.

        Returns: "single_agent", "swarm", or "prompt_chain"
        """
        score = complexity.score
        phases = complexity.phases

        # Single agent: Simple queries, one domain
        if score <= 4 and len(domains) == 1:
            return "single_agent"

        # Prompt chain: Structured workflow, 3+ phases, high complexity
        if len(phases) >= 3 and score >= 7:
            # Check if phases are sequential/structured
            sequential_phases = ['diagnosis', 'planning', 'implementation', 'validation']
            if any(phase in phases for phase in sequential_phases):
                return "prompt_chain"

        # Swarm: Multi-domain, diagnosis needed, moderate-high complexity
        if score >= 5 or len(domains) > 1 or 'diagnosis' in phases:
            return "swarm"

        # Default: single agent
        return "single_agent"


def demo():
    """Demonstrate complexity analyzer"""
    analyzer = ComplexityAnalyzer()

    test_cases = [
        {
            "query": "What's the difference between SPF and DKIM?",
            "domains": ["dns"],
            "category": "technical_question",
            "entities": {"dns_concepts": ["SPF", "DKIM"]}
        },
        {
            "query": "Our Azure tenant's email deliverability is terrible. Fix it.",
            "domains": ["azure", "dns"],
            "category": "operational_task",
            "entities": {}
        },
        {
            "query": "Setup SPF record for example.com",
            "domains": ["dns"],
            "category": "operational_task",
            "entities": {"domain_names": ["example.com"], "dns_concepts": ["SPF"]}
        },
        {
            "query": "Migrate 500 users from on-premises Exchange to Exchange Online with zero downtime",
            "domains": ["azure", "endpoint"],
            "category": "operational_task",
            "entities": {"scale": [("500", "users")], "azure_services": ["Exchange Online"]}
        },
        {
            "query": "Analyze service desk complaints, identify root causes, and create action plan",
            "domains": ["servicedesk"],
            "category": "analysis_research",
            "entities": {}
        },
    ]

    print("=" * 80)
    print("Complexity Analyzer Demo")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test['query']}")
        print("-" * 80)

        assessment = analyzer.analyze(
            query=test['query'],
            domains=test['domains'],
            category=test['category'],
            entities=test['entities']
        )

        print(f"Score: {assessment.score}/10")
        print(f"Level: {assessment.level.name}")
        print(f"Phases: {', '.join(assessment.phases) if assessment.phases else 'None detected'}")
        print(f"Factors: {assessment.factors}")
        print(f"Reasoning: {assessment.reasoning}")
        print(f"Confidence: {assessment.confidence:.2f}")

        # Suggest routing strategy
        strategy = analyzer.suggest_routing_strategy(assessment, test['domains'])
        print(f"Suggested Strategy: {strategy.upper()}")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    demo()
