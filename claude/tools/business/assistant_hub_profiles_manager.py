#!/usr/bin/env python3
"""
Agent Profiles Manager - Agent Capabilities and Performance Module

Manages agent profiles, capabilities, performance tracking, and provides
intelligent agent recommendations based on historical performance and specializations.

Part of the modularized Intelligent Assistant Hub system.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class AgentCapability(Enum):
    """Capabilities that agents can possess"""
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_GENERATION = "document_generation"
    CODE_REVIEW = "code_review"
    FINANCIAL_PLANNING = "financial_planning"
    SCHEDULING = "scheduling"
    RESEARCH = "research"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CREATIVE_WRITING = "creative_writing"
    STRATEGIC_PLANNING = "strategic_planning"
    MARKET_ANALYSIS = "market_analysis"
    SYSTEM_INTEGRATION = "system_integration"
    COMPLIANCE_CHECKING = "compliance_checking"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    LEARNING = "learning"


class RequestDomain(Enum):
    """Domain categories for agent specialization"""
    CAREER = "career"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    HEALTH = "health"
    PRODUCTIVITY = "productivity"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    TRAVEL = "travel"
    PERSONAL = "personal"
    AUTOMATION = "automation"
    CREATIVE = "creative"


@dataclass
class AgentProfile:
    """Profile containing agent capabilities and performance data"""
    agent_id: str
    name: str
    description: str
    specializations: List[RequestDomain]
    capabilities: List[AgentCapability]
    performance_score: float = 0.8
    success_rate: float = 0.85
    average_response_time: float = 30.0
    last_used: Optional[float] = None
    usage_count: int = 0
    error_rate: float = 0.1
    confidence_score: float = 0.8
    user_satisfaction: float = 0.8
    context_requirements: List[str] = field(default_factory=list)
    integration_endpoints: List[str] = field(default_factory=list)
    cost_per_request: float = 0.01
    concurrent_limit: int = 5
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Post-initialization to calculate derived metrics"""
        if self.last_used is None:
            self.last_used = self.created_at


@dataclass
class AgentPerformanceMetrics:
    """Performance tracking for an agent"""
    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_performance_update: float = field(default_factory=time.time)
    request_history: List[Dict[str, Any]] = field(default_factory=list)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    domain_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate current success rate"""
        if self.total_requests == 0:
            return 0.85  # Default
        return self.successful_requests / self.total_requests

    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if self.successful_requests == 0:
            return 30.0  # Default
        return self.total_response_time / self.successful_requests


class AgentProfilesManager:
    """Manages agent profiles, capabilities, and performance tracking"""

    def __init__(self):
        self.agent_profiles = self._initialize_agent_profiles()
        self.performance_metrics = {
            agent_id: AgentPerformanceMetrics(agent_id=agent_id)
            for agent_id in self.agent_profiles.keys()
        }
        self.recommendation_cache = {}
        self.profile_update_history = []

    def _initialize_agent_profiles(self) -> Dict[str, AgentProfile]:
        """Initialize all agent profiles with their capabilities"""
        profiles = {}

        # Personal Assistant Agent
        profiles["personal_assistant"] = AgentProfile(
            agent_id="personal_assistant",
            name="Personal Assistant",
            description="General-purpose personal productivity and life management",
            specializations=[RequestDomain.PERSONAL, RequestDomain.PRODUCTIVITY, RequestDomain.COMMUNICATION],
            capabilities=[
                AgentCapability.SCHEDULING, AgentCapability.DOCUMENT_GENERATION,
                AgentCapability.COMMUNICATION, AgentCapability.AUTOMATION
            ],
            performance_score=0.85,
            success_rate=0.88,
            average_response_time=25.0,
            context_requirements=["user_preferences", "calendar_data", "personal_goals"]
        )

        # Career Development Agent
        profiles["career_development"] = AgentProfile(
            agent_id="career_development",
            name="Career Development Agent",
            description="Career planning, job search, and professional development",
            specializations=[RequestDomain.CAREER, RequestDomain.LEARNING, RequestDomain.COMMUNICATION],
            capabilities=[
                AgentCapability.STRATEGIC_PLANNING, AgentCapability.MARKET_ANALYSIS,
                AgentCapability.DOCUMENT_GENERATION, AgentCapability.RESEARCH
            ],
            performance_score=0.82,
            success_rate=0.79,
            average_response_time=45.0,
            context_requirements=["resume", "linkedin_profile", "career_goals", "job_market_data"]
        )

        # Financial Intelligence Agent
        profiles["financial_intelligence"] = AgentProfile(
            agent_id="financial_intelligence",
            name="Financial Intelligence Agent",
            description="Financial planning, investment analysis, and wealth management",
            specializations=[RequestDomain.FINANCIAL, RequestDomain.RESEARCH],
            capabilities=[
                AgentCapability.FINANCIAL_PLANNING, AgentCapability.DATA_ANALYSIS,
                AgentCapability.MARKET_ANALYSIS, AgentCapability.STRATEGIC_PLANNING
            ],
            performance_score=0.88,
            success_rate=0.85,
            average_response_time=35.0,
            context_requirements=["financial_data", "investment_portfolio", "tax_info", "market_data"]
        )

        # Security Agent
        profiles["security"] = AgentProfile(
            agent_id="security",
            name="Security Agent",
            description="Cybersecurity analysis, compliance, and threat assessment",
            specializations=[RequestDomain.TECHNICAL],
            capabilities=[
                AgentCapability.SECURITY_ANALYSIS, AgentCapability.COMPLIANCE_CHECKING,
                AgentCapability.CODE_REVIEW, AgentCapability.RESEARCH
            ],
            performance_score=0.90,
            success_rate=0.92,
            average_response_time=40.0,
            context_requirements=["system_architecture", "security_policies", "compliance_requirements"]
        )

        # Research Agent
        profiles["research"] = AgentProfile(
            agent_id="research",
            name="Research Agent",
            description="Information gathering, analysis, and knowledge synthesis",
            specializations=[RequestDomain.RESEARCH, RequestDomain.LEARNING],
            capabilities=[
                AgentCapability.RESEARCH, AgentCapability.DATA_ANALYSIS,
                AgentCapability.DOCUMENT_GENERATION, AgentCapability.MARKET_ANALYSIS
            ],
            performance_score=0.83,
            success_rate=0.81,
            average_response_time=50.0,
            context_requirements=["research_sources", "domain_expertise", "previous_research"]
        )

        # LinkedIn Optimizer Agent
        profiles["linkedin_optimizer"] = AgentProfile(
            agent_id="linkedin_optimizer",
            name="LinkedIn Optimizer Agent",
            description="LinkedIn profile optimization and professional networking",
            specializations=[RequestDomain.CAREER, RequestDomain.COMMUNICATION],
            capabilities=[
                AgentCapability.CREATIVE_WRITING, AgentCapability.MARKET_ANALYSIS,
                AgentCapability.STRATEGIC_PLANNING, AgentCapability.DOCUMENT_GENERATION
            ],
            performance_score=0.80,
            success_rate=0.77,
            average_response_time=30.0,
            context_requirements=["linkedin_profile", "industry_trends", "career_goals"]
        )

        # Developer Agent
        profiles["developer"] = AgentProfile(
            agent_id="developer",
            name="Developer Agent",
            description="Software development, code review, and technical architecture",
            specializations=[RequestDomain.TECHNICAL],
            capabilities=[
                AgentCapability.CODE_REVIEW, AgentCapability.SYSTEM_INTEGRATION,
                AgentCapability.PERFORMANCE_OPTIMIZATION, AgentCapability.AUTOMATION
            ],
            performance_score=0.87,
            success_rate=0.89,
            average_response_time=38.0,
            context_requirements=["codebase", "technical_requirements", "architecture_docs"]
        )

        # Writer Agent
        profiles["writer"] = AgentProfile(
            agent_id="writer",
            name="Writer Agent",
            description="Content creation, editing, and creative writing",
            specializations=[RequestDomain.CREATIVE, RequestDomain.COMMUNICATION],
            capabilities=[
                AgentCapability.CREATIVE_WRITING, AgentCapability.DOCUMENT_GENERATION,
                AgentCapability.COMMUNICATION
            ],
            performance_score=0.84,
            success_rate=0.86,
            average_response_time=32.0,
            context_requirements=["writing_style_guide", "target_audience", "content_goals"]
        )

        return profiles

    def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Get agent profile by ID"""
        return self.agent_profiles.get(agent_id)

    def get_all_profiles(self) -> Dict[str, AgentProfile]:
        """Get all agent profiles"""
        return self.agent_profiles.copy()

    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentProfile]:
        """Get all agents that have a specific capability"""
        return [
            profile for profile in self.agent_profiles.values()
            if capability in profile.capabilities
        ]

    def get_agents_by_domain(self, domain: RequestDomain) -> List[AgentProfile]:
        """Get all agents specialized in a specific domain"""
        return [
            profile for profile in self.agent_profiles.values()
            if domain in profile.specializations
        ]

    def get_top_performing_agents(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top performing agents by performance score"""
        agents = [(agent_id, profile.performance_score)
                 for agent_id, profile in self.agent_profiles.items()]
        return sorted(agents, key=lambda x: x[1], reverse=True)[:limit]

    def update_agent_performance(self, agent_id: str, success: bool,
                               response_time: float, domain: Optional[RequestDomain] = None,
                               error_details: Optional[str] = None):
        """Update agent performance metrics"""
        if agent_id not in self.performance_metrics:
            self.performance_metrics[agent_id] = AgentPerformanceMetrics(agent_id=agent_id)

        metrics = self.performance_metrics[agent_id]
        profile = self.agent_profiles.get(agent_id)

        # Update basic metrics
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
            metrics.total_response_time += response_time
        else:
            metrics.failed_requests += 1

            # Record error
            if error_details:
                metrics.error_history.append({
                    'timestamp': time.time(),
                    'error': error_details,
                    'domain': domain.value if domain else None
                })

        # Update domain-specific performance
        if domain:
            domain_key = domain.value
            if domain_key not in metrics.domain_performance:
                metrics.domain_performance[domain_key] = {'requests': 0, 'successes': 0, 'avg_time': 0.0}

            domain_perf = metrics.domain_performance[domain_key]
            domain_perf['requests'] += 1
            if success:
                domain_perf['successes'] += 1
                # Update average time
                prev_avg = domain_perf['avg_time']
                domain_perf['avg_time'] = ((prev_avg * (domain_perf['successes'] - 1)) + response_time) / domain_perf['successes']

        # Update profile with new metrics
        if profile:
            profile.success_rate = metrics.success_rate
            profile.average_response_time = metrics.average_response_time
            profile.last_used = time.time()
            profile.usage_count += 1
            profile.error_rate = metrics.failed_requests / metrics.total_requests

            # Recalculate performance score
            profile.performance_score = self._calculate_performance_score(profile, metrics)

        metrics.last_performance_update = time.time()

        # Keep history limited
        if len(metrics.request_history) > 100:
            metrics.request_history = metrics.request_history[-100:]
        if len(metrics.error_history) > 50:
            metrics.error_history = metrics.error_history[-50:]

    def _calculate_performance_score(self, profile: AgentProfile, metrics: AgentPerformanceMetrics) -> float:
        """Calculate overall performance score for an agent"""
        # Weighted combination of metrics
        success_weight = 0.4
        speed_weight = 0.2
        reliability_weight = 0.2
        satisfaction_weight = 0.2

        # Success rate component (0-1)
        success_component = metrics.success_rate

        # Speed component (inverse of response time, normalized)
        max_acceptable_time = 120.0
        speed_component = max(0, 1 - (metrics.average_response_time / max_acceptable_time))

        # Reliability component (inverse of error rate)
        reliability_component = max(0, 1 - profile.error_rate)

        # Satisfaction component (from profile)
        satisfaction_component = profile.user_satisfaction

        performance_score = (
            success_component * success_weight +
            speed_component * speed_weight +
            reliability_component * reliability_weight +
            satisfaction_component * satisfaction_weight
        )

        return min(1.0, max(0.0, performance_score))

    def get_agent_recommendations(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get proactive agent recommendations based on context"""
        recommendations = []
        current_time = time.time()

        # Check cache first
        cache_key = str(hash(str(context))) if context else "default"
        if cache_key in self.recommendation_cache:
            cache_entry = self.recommendation_cache[cache_key]
            if current_time - cache_entry['timestamp'] < 300:  # 5 minute cache
                return cache_entry['recommendations']

        # Generate fresh recommendations

        # 1. Underutilized high-performing agents
        for agent_id, profile in self.agent_profiles.items():
            if profile.performance_score > 0.85 and profile.usage_count < 5:
                recommendations.append({
                    'agent': agent_id,
                    'action': f'Try using {profile.name} for {profile.specializations[0].value} tasks',
                    'reason': 'High-performing agent with low usage',
                    'priority': 'medium',
                    'confidence': 0.7
                })

        # 2. Context-based recommendations
        if context:
            if 'recent_domains' in context:
                for domain in context['recent_domains']:
                    specialized_agents = self.get_agents_by_domain(RequestDomain(domain))
                    if specialized_agents:
                        best_agent = max(specialized_agents, key=lambda x: x.performance_score)
                        recommendations.append({
                            'agent': best_agent.agent_id,
                            'action': f'Leverage {best_agent.name} for {domain} tasks',
                            'reason': f'Specialized in {domain} with {best_agent.success_rate:.1%} success rate',
                            'priority': 'high',
                            'confidence': 0.85
                        })

        # 3. Performance-based recommendations
        low_performing = [
            (agent_id, profile) for agent_id, profile in self.agent_profiles.items()
            if profile.success_rate < 0.7
        ]

        for agent_id, profile in low_performing:
            recommendations.append({
                'agent': agent_id,
                'action': f'Review {profile.name} performance and consider alternatives',
                'reason': f'Success rate below threshold ({profile.success_rate:.1%})',
                'priority': 'low',
                'confidence': 0.6
            })

        # 4. Quick wins from financial intelligence
        financial_metrics = self._get_quick_financial_metrics()
        if financial_metrics and financial_metrics.get('optimization_opportunities'):
            recommendations.append({
                'agent': 'financial_intelligence',
                'action': 'Review financial optimization opportunities',
                'reason': 'Potential savings identified in spending patterns',
                'priority': 'high',
                'confidence': 0.8
            })

        # Sort by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: (priority_order[x['priority']], x['confidence']), reverse=True)

        # Limit recommendations
        recommendations = recommendations[:5]

        # Cache results
        self.recommendation_cache[cache_key] = {
            'timestamp': current_time,
            'recommendations': recommendations
        }

        return recommendations

    def _get_quick_financial_metrics(self) -> Dict[str, Any]:
        """Get quick financial metrics (placeholder)"""
        # In real implementation, would connect to financial systems
        return {
            'optimization_opportunities': True,
            'potential_savings': 150.0,
            'budget_variance': -0.05,
            'investment_performance': 0.08
        }

    def get_agent_utilization(self) -> Dict[str, float]:
        """Calculate agent utilization rates"""
        total_requests = sum(
            metrics.total_requests for metrics in self.performance_metrics.values()
        )

        if total_requests == 0:
            return {agent_id: 0.0 for agent_id in self.agent_profiles.keys()}

        return {
            agent_id: metrics.total_requests / total_requests
            for agent_id, metrics in self.performance_metrics.items()
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        utilization = self.get_agent_utilization()
        top_performers = self.get_top_performing_agents()

        total_requests = sum(metrics.total_requests for metrics in self.performance_metrics.values())
        total_successes = sum(metrics.successful_requests for metrics in self.performance_metrics.values())

        return {
            'total_agents': len(self.agent_profiles),
            'total_requests': total_requests,
            'overall_success_rate': total_successes / max(total_requests, 1),
            'top_performers': top_performers,
            'agent_utilization': utilization,
            'most_used_agent': max(utilization.items(), key=lambda x: x[1])[0] if utilization else None,
            'least_used_agent': min(utilization.items(), key=lambda x: x[1])[0] if utilization else None,
            'average_response_time': sum(
                profile.average_response_time for profile in self.agent_profiles.values()
            ) / len(self.agent_profiles)
        }

    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        profile = self.get_agent_profile(agent_id)
        if not profile:
            return None

        metrics = self.performance_metrics.get(agent_id)

        return {
            'profile': {
                'agent_id': profile.agent_id,
                'name': profile.name,
                'description': profile.description,
                'specializations': [spec.value for spec in profile.specializations],
                'capabilities': [cap.value for cap in profile.capabilities],
                'context_requirements': profile.context_requirements
            },
            'performance': {
                'performance_score': profile.performance_score,
                'success_rate': profile.success_rate,
                'average_response_time': profile.average_response_time,
                'error_rate': profile.error_rate,
                'usage_count': profile.usage_count,
                'last_used': profile.last_used
            },
            'metrics': {
                'total_requests': metrics.total_requests if metrics else 0,
                'successful_requests': metrics.successful_requests if metrics else 0,
                'failed_requests': metrics.failed_requests if metrics else 0,
                'domain_performance': metrics.domain_performance if metrics else {}
            } if metrics else None
        }

    def add_agent_profile(self, profile: AgentProfile) -> bool:
        """Add a new agent profile"""
        if profile.agent_id in self.agent_profiles:
            return False  # Agent already exists

        self.agent_profiles[profile.agent_id] = profile
        self.performance_metrics[profile.agent_id] = AgentPerformanceMetrics(agent_id=profile.agent_id)

        self.profile_update_history.append({
            'action': 'add_profile',
            'agent_id': profile.agent_id,
            'timestamp': time.time()
        })

        return True

    def update_agent_profile(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing agent profile"""
        if agent_id not in self.agent_profiles:
            return False

        profile = self.agent_profiles[agent_id]

        # Update allowed fields
        allowed_fields = ['name', 'description', 'specializations', 'capabilities',
                         'context_requirements', 'integration_endpoints', 'user_satisfaction']

        for field, value in updates.items():
            if field in allowed_fields and hasattr(profile, field):
                setattr(profile, field, value)

        self.profile_update_history.append({
            'action': 'update_profile',
            'agent_id': agent_id,
            'updates': updates,
            'timestamp': time.time()
        })

        return True
