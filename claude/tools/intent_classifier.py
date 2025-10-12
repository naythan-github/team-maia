#!/usr/bin/env python3
"""
Intent Classifier - Classify user queries for intelligent routing

Classifies user queries into intent categories, detects relevant domains,
and extracts entities for optimal agent routing.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 3
Source: claude/tools/orchestration/coordinator_agent.py
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Intent:
    """Classified user intent"""
    category: str           # technical_question, operational_task, strategic_planning, analysis_research, creative_generation
    domains: List[str]      # dns, azure, financial, security, cloud, etc.
    complexity: int         # 1-10 scale
    confidence: float       # 0.0-1.0
    entities: Dict[str, Any]  # Extracted entities (domain names, numbers, services, etc.)


class IntentClassifier:
    """
    Classifies user queries into intent categories.

    Uses keyword matching and pattern recognition (lightweight NLP).
    Future: Could upgrade to ML-based classification.
    """

    # Domain keywords (for detecting which domain query relates to)
    DOMAIN_KEYWORDS = {
        'dns': ['dns', 'domain', 'mx record', 'spf', 'dkim', 'dmarc', 'nameserver', 'dns record', 'email authentication', 'mail server'],
        'azure': ['azure', 'exchange online', 'm365', 'microsoft 365', 'active directory', 'entra', 'cloud', 'tenant', 'o365', 'office 365'],
        'security': ['security', 'vulnerability', 'threat', 'compliance', 'audit', 'pentesting', 'firewall', 'encryption', 'malware', 'breach'],
        'financial': ['budget', 'cost', 'pricing', 'salary', 'tax', 'investment', 'super', 'finance', 'money', 'roi', 'expense'],
        'cloud': ['aws', 'gcp', 'cloud', 'infrastructure', 'iaac', 'terraform', 'kubernetes', 'container', 'docker', 'k8s'],
        'servicedesk': ['ticket', 'complaint', 'service desk', 'incident', 'request', 'helpdesk', 'escalation', 'user issue'],
        'career': ['job', 'interview', 'resume', 'linkedin', 'career', 'recruiter', 'hiring', 'cv', 'application'],
        'data': ['analytics', 'dashboard', 'report', 'metrics', 'kpi', 'visualization', 'data', 'bi', 'reporting'],
        'sre': ['monitoring', 'slo', 'sli', 'reliability', 'incident', 'postmortem', 'observability', 'uptime', 'mttr'],
        'endpoint': ['laptop', 'macos', 'windows', 'endpoint', 'device', 'intune', 'jamf', 'soe', 'workstation'],
        'network': ['network', 'firewall', 'vpn', 'routing', 'switch', 'load balancer', 'wan', 'lan'],
        'devops': ['ci/cd', 'pipeline', 'deployment', 'automation', 'jenkins', 'github actions', 'gitlab'],
        'blog': ['blog', 'article', 'post', 'content', 'seo', 'publishing', 'writing'],
    }

    # Intent category patterns
    INTENT_PATTERNS = {
        'technical_question': [
            r'\b(what|how|why|when|where|which)\b',
            r'\b(explain|tell me|describe|show me)\b',
            r'\?$',  # Ends with question mark
            r'\b(difference between|compare)\b',
        ],
        'operational_task': [
            r'\b(setup|configure|install|deploy|migrate|create)\b',
            r'\b(fix|resolve|troubleshoot|debug|repair)\b',
            r'\b(update|upgrade|patch|implement)\b',
            r'\b(build|develop|design)\b',
        ],
        'strategic_planning': [
            r'\b(plan|strategy|roadmap|architecture)\b',
            r'\b(should I|should we|recommend|advise|suggest)\b',
            r'\b(optimize|improve|enhance|refactor)\b',
            r'\b(best practice|approach|methodology)\b',
        ],
        'analysis_research': [
            r'\b(analyze|assess|evaluate|review|audit)\b',
            r'\b(research|investigate|compare|benchmark)\b',
            r'\b(report|summary|findings|insights)\b',
            r'\b(metrics|statistics|data|trends)\b',
        ],
        'creative_generation': [
            r'\b(write|create|generate|draft|compose)\b',
            r'\b(blog|article|presentation|document|email)\b',
            r'\b(design|mockup|prototype)\b',
        ],
    }

    # Complexity indicators (patterns that suggest high complexity)
    COMPLEXITY_INDICATORS = {
        'multi_domain': 2,      # Multiple domains mentioned
        'multi_step': 2,        # "and then", "after that", sequential phases
        'large_scale': 2,       # "100 users", "enterprise", "organization-wide"
        'integration': 2,       # "integrate", "connect", cross-system
        'migration': 2,         # "migrate", "move from", major changes
        'custom': 2,            # "custom", "specific", non-standard
        'urgent': 1,            # "urgent", "asap", "emergency", "critical"
        'diagnosis': 2,         # "why", "investigate", "find out" - requires investigation
        'vague': 1,             # "not working", "broken", "issues" - unclear requirements
    }

    def classify(self, user_query: str, context: Dict[str, Any] = None) -> Intent:
        """
        Classify user query into intent.

        Args:
            user_query: Natural language query from user
            context: Optional context (user history, preferences, previous interactions)

        Returns:
            Intent with category, domains, complexity, confidence, entities
        """
        query_lower = user_query.lower()

        # Detect domains
        domains = self._detect_domains(query_lower)

        # Detect intent category
        category = self._detect_category(query_lower)

        # Assess complexity
        complexity = self._assess_complexity(query_lower, domains, user_query)

        # Extract entities
        entities = self._extract_entities(user_query, domains)

        # Calculate confidence (simple heuristic)
        confidence = self._calculate_confidence(domains, category, complexity)

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
        if re.search(r'\bshould\s+(i|we)\b', query_lower, re.IGNORECASE):
            scores['strategic_planning'] = scores.get('strategic_planning', 0) + 2

        # Boost operational_task for action verbs
        if re.search(r'\b(fix|resolve|setup|configure)\b', query_lower, re.IGNORECASE):
            scores['operational_task'] = scores.get('operational_task', 0) + 1

        # Return category with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        # Default: operational task (most common)
        return 'operational_task'

    def _assess_complexity(self, query_lower: str, domains: List[str], original_query: str) -> int:
        """
        Assess query complexity on 1-10 scale.

        Factors:
        - Number of domains (1 domain = simple, 2+ = complex)
        - Complexity indicators (migration, integration, etc.)
        - Query length (longer = more complex)
        - Ambiguity (vague requirements increase complexity)
        """
        complexity = 3  # Base complexity

        # Factor 1: Multiple domains increase complexity
        if len(domains) > 1:
            complexity += self.COMPLEXITY_INDICATORS['multi_domain']

        # Factor 2: Check for complexity indicators
        indicators = {
            'multi_step': [r'\b(and then|after that|followed by|next|step)\b'],
            'large_scale': [r'\b(\d{2,}|\d+k)\s+(users|servers|devices|tenants)\b', r'\b(enterprise|organization-wide|company-wide)\b'],
            'integration': [r'\b(integrate|connect|sync|link|bridge)\b'],
            'migration': [r'\b(migrate|move from|transition|switch from)\b'],
            'custom': [r'\b(custom|specific|tailored|bespoke)\b'],
            'urgent': [r'\b(urgent|asap|emergency|critical|immediately|now)\b'],
            'diagnosis': [r'\b(why|investigate|find out|diagnose|root cause)\b'],
            'vague': [r'\b(not working|broken|issues|problems|terrible|bad)\b'],
        }

        for indicator, patterns in indicators.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    complexity += self.COMPLEXITY_INDICATORS[indicator]
                    break  # Only count each indicator once

        # Factor 3: Query length (longer queries often more complex)
        word_count = len(original_query.split())
        if word_count > 30:
            complexity += 2
        elif word_count > 15:
            complexity += 1

        # Factor 4: Question marks (multiple questions = complex)
        question_count = original_query.count('?')
        if question_count > 1:
            complexity += 1

        # Cap at 10
        return min(complexity, 10)

    def _extract_entities(self, user_query: str, domains: List[str]) -> Dict[str, Any]:
        """
        Extract relevant entities from query.

        Examples:
        - Domain names: example.com
        - Email addresses: user@example.com
        - Numbers: 100 users, $5000
        - Services: Exchange Online, Azure AD
        """
        entities = {}

        # Extract domain names (DNS)
        if 'dns' in domains:
            domain_pattern = r'\b([a-z0-9-]+\.)+[a-z]{2,}\b'
            domain_matches = re.findall(domain_pattern, user_query, re.IGNORECASE)
            if domain_matches:
                entities['domain_names'] = domain_matches

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, user_query)
        if email_matches:
            entities['email_addresses'] = email_matches

        # Extract numbers (users, costs, etc.)
        number_pattern = r'\b(\d+[km]?)\s+(users?|servers?|devices?|tenants?)\b'
        number_matches = re.findall(number_pattern, user_query, re.IGNORECASE)
        if number_matches:
            entities['scale'] = number_matches

        # Extract cost/budget
        cost_pattern = r'\$(\d{1,3}(,\d{3})*(\.\d{2})?|(\d+))[km]?'
        cost_matches = re.findall(cost_pattern, user_query, re.IGNORECASE)
        if cost_matches:
            entities['costs'] = [match[0] for match in cost_matches]

        # Extract Azure services
        if 'azure' in domains:
            azure_services = ['Exchange Online', 'Azure AD', 'Entra ID', 'SharePoint', 'Teams', 'Intune']
            found_services = [svc for svc in azure_services if svc.lower() in user_query.lower()]
            if found_services:
                entities['azure_services'] = found_services

        # Extract DNS concepts
        if 'dns' in domains:
            dns_concepts = ['SPF', 'DKIM', 'DMARC', 'MX', 'A record', 'CNAME', 'TXT record', 'NS record']
            found_concepts = [concept for concept in dns_concepts if concept.lower() in user_query.lower()]
            if found_concepts:
                entities['dns_concepts'] = found_concepts

        return entities

    def _calculate_confidence(self, domains: List[str], category: str, complexity: int) -> float:
        """
        Calculate classification confidence (0.0-1.0).

        Higher confidence when:
        - Clear domain keywords detected
        - Strong category match
        - Reasonable complexity (not edge cases)
        """
        confidence = 0.7  # Base confidence

        # Boost for non-general domains (specific domain keywords found)
        if 'general' not in domains:
            confidence += 0.15

        # Boost for multiple domain detections (reinforcement)
        if len(domains) > 1 and 'general' not in domains:
            confidence += 0.05

        # Slight penalty for very high complexity (might be misclassified)
        if complexity >= 9:
            confidence -= 0.05

        # Slight penalty for very low complexity (might be too simple)
        if complexity <= 2:
            confidence -= 0.05

        # Cap at 0.95 (never 100% certain)
        return min(confidence, 0.95)


def demo():
    """Demonstrate intent classifier"""
    classifier = IntentClassifier()

    test_queries = [
        "What's the difference between SPF and DKIM?",
        "Our Azure tenant's email deliverability is terrible. Fix it.",
        "Setup SPF record for example.com",
        "Analyze last 30 days of service desk complaints and find root causes",
        "Should I migrate to Azure or stay on-premises?",
        "Write a blog post about DNS security best practices",
        "Check if our 500 users can access the VPN",
        "Urgent: Production down, need immediate investigation",
    ]

    print("=" * 80)
    print("Intent Classifier Demo")
    print("=" * 80)

    for query in test_queries:
        print(f"\n📋 Query: {query}")
        print("-" * 80)

        intent = classifier.classify(query)

        print(f"Category: {intent.category}")
        print(f"Domains: {', '.join(intent.domains)}")
        print(f"Complexity: {intent.complexity}/10")
        print(f"Confidence: {intent.confidence:.2f}")
        if intent.entities:
            print(f"Entities: {intent.entities}")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    demo()
