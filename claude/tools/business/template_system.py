#!/usr/bin/env python3
"""
CV Template System - Hypothesis-Driven Optimization
Creates testable CV templates and tracks performance for evidence-based improvement.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CVTemplate:
    """CV template configuration"""
    name: str
    role_type: str
    hypothesis: str
    bullet_allocation: Dict[str, int]
    emphasis_weights: Dict[str, float]
    keyword_priorities: List[str]
    selection_strategy: str
    success_metrics: List[str]

@dataclass
class ApplicationTracking:
    """Track application outcomes for template performance"""
    application_id: str
    job_title: str
    company: str
    template_used: str
    bullet_allocation: Dict[str, int]
    keyword_matches: int
    submission_date: str
    outcome: str  # pending, response, interview, rejection, offer
    response_time_days: Optional[int] = None
    feedback_notes: str = ""

class CVTemplateSystem:
    """Manage CV templates and track performance"""

    def __init__(self, data_dir: str = "get_path_manager().get_path('git_root') / 'claude' / 'data' / 'career'"):
        self.data_dir = Path(data_dir)
        self.templates_file = self.data_dir / "cv_templates.json"
        self.applications_file = self.data_dir / "application_tracking.json"
        self.templates = {}
        self.applications = []

        self.load_templates()
        self.load_applications()

    def create_initial_templates(self):
        """Create hypothesis-based templates for testing"""

        # Template 1: BRM-Focused (Stakeholder Emphasis)
        brm_template = CVTemplate(
            name="brm_stakeholder_focused",
            role_type="business_relationship_manager",
            hypothesis="BRM roles prioritize stakeholder outcomes and business value delivery over technical depth",
            bullet_allocation={
                "key_achievements": 8,
                "professional_experience": 24
            },
            emphasis_weights={
                "stakeholder_management": 1.5,
                "business_outcomes": 1.4,
                "governance": 1.3,
                "technical_delivery": 1.0,
                "team_leadership": 1.2
            },
            keyword_priorities=[
                "stakeholder", "relationship", "business value", "governance",
                "portfolio", "executive", "strategic", "outcomes",
                "client", "engagement", "delivery", "alignment"
            ],
            selection_strategy="prioritize_stakeholder_facing_experiences",
            success_metrics=[
                "application_response_rate",
                "interview_invitation_rate",
                "keyword_match_percentage",
                "time_to_response"
            ]
        )

        # Template 2: Technical-BRM Hybrid
        technical_brm_template = CVTemplate(
            name="technical_brm_hybrid",
            role_type="technical_business_manager",
            hypothesis="Technical BRM roles require balanced technical depth with relationship management skills",
            bullet_allocation={
                "key_achievements": 7,
                "professional_experience": 25
            },
            emphasis_weights={
                "technical_delivery": 1.4,
                "stakeholder_management": 1.3,
                "architecture": 1.3,
                "business_outcomes": 1.2,
                "innovation": 1.2
            },
            keyword_priorities=[
                "azure", "cloud", "architecture", "technical", "solution",
                "stakeholder", "delivery", "digital", "transformation",
                "infrastructure", "platform", "integration", "strategy"
            ],
            selection_strategy="balance_technical_and_relationship_experiences",
            success_metrics=[
                "technical_role_response_rate",
                "consultant_role_response_rate",
                "azure_keyword_effectiveness",
                "technical_interview_conversion"
            ]
        )

        # Template 3: Senior Leadership Focus
        leadership_template = CVTemplate(
            name="senior_leadership_focused",
            role_type="senior_executive",
            hypothesis="Senior roles emphasize strategic outcomes, team leadership, and organizational impact",
            bullet_allocation={
                "key_achievements": 9,
                "professional_experience": 23
            },
            emphasis_weights={
                "strategic_leadership": 1.6,
                "business_transformation": 1.5,
                "team_development": 1.4,
                "operational_excellence": 1.3,
                "stakeholder_management": 1.2
            },
            keyword_priorities=[
                "strategy", "leadership", "transformation", "executive",
                "director", "organizational", "vision", "growth",
                "governance", "board", "strategic planning", "change management"
            ],
            selection_strategy="emphasize_leadership_and_strategic_impact",
            success_metrics=[
                "senior_role_response_rate",
                "c_suite_interview_rate",
                "salary_negotiation_success",
                "leadership_keyword_effectiveness"
            ]
        )

        # Save templates
        self.templates = {
            "brm_stakeholder_focused": brm_template,
            "technical_brm_hybrid": technical_brm_template,
            "senior_leadership_focused": leadership_template
        }

        self.save_templates()
        return self.templates

    def detect_optimal_template(self, job_description: str) -> str:
        """Analyze job description and recommend template"""

        job_text = job_description.lower()

        # Count role indicators
        role_scores = {
            "brm_stakeholder_focused": 0,
            "technical_brm_hybrid": 0,
            "senior_leadership_focused": 0
        }

        # BRM indicators
        brm_keywords = ["business relationship", "stakeholder", "client", "relationship",
                       "governance", "portfolio", "account", "engagement"]
        role_scores["brm_stakeholder_focused"] = sum(1 for kw in brm_keywords if kw in job_text)

        # Technical indicators
        tech_keywords = ["azure", "cloud", "technical", "architecture", "digital",
                        "infrastructure", "platform", "solution", "technology"]
        role_scores["technical_brm_hybrid"] = sum(1 for kw in tech_keywords if kw in job_text)

        # Leadership indicators
        leadership_keywords = ["director", "head of", "vp", "chief", "executive",
                              "strategy", "leadership", "transformation", "vision"]
        role_scores["senior_leadership_focused"] = sum(1 for kw in leadership_keywords if kw in job_text)

        # Additional scoring logic
        if "senior" in job_text and any(word in job_text for word in ["manager", "director", "head"]):
            role_scores["senior_leadership_focused"] += 3

        if "azure" in job_text or "cloud" in job_text:
            role_scores["technical_brm_hybrid"] += 2

        # Return highest scoring template
        recommended_template = max(role_scores, key=role_scores.get)

        return {
            "recommended_template": recommended_template,
            "confidence_scores": role_scores,
            "reasoning": self._generate_template_reasoning(job_text, role_scores)
        }

    def apply_template_to_cv_creation(self, template_name: str, job_description: str) -> Dict[str, Any]:
        """Apply template configuration to CV creation process"""

        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = self.templates[template_name]

        # Generate CV creation configuration
        cv_config = {
            "template_applied": template_name,
            "bullet_allocation": template.bullet_allocation,
            "emphasis_weights": template.emphasis_weights,
            "target_keywords": template.keyword_priorities,
            "selection_strategy": template.selection_strategy,
            "quality_metrics": {
                "keyword_targets": self._extract_job_keywords(job_description),
                "emphasis_validation": template.emphasis_weights,
                "success_tracking": template.success_metrics
            }
        }

        return cv_config

    def track_application(self, job_title: str, company: str, template_used: str,
                         keyword_matches: int, outcome: str = "pending") -> str:
        """Track new application for performance analysis"""

        application_id = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if template_used not in self.templates:
            raise ValueError(f"Template '{template_used}' not found")

        template = self.templates[template_used]

        application = ApplicationTracking(
            application_id=application_id,
            job_title=job_title,
            company=company,
            template_used=template_used,
            bullet_allocation=template.bullet_allocation,
            keyword_matches=keyword_matches,
            submission_date=datetime.now().strftime('%Y-%m-%d'),
            outcome=outcome
        )

        self.applications.append(application)
        self.save_applications()

        return application_id

    def update_application_outcome(self, application_id: str, outcome: str,
                                  response_time_days: Optional[int] = None,
                                  feedback_notes: str = ""):
        """Update application outcome for tracking"""

        for app in self.applications:
            if app.application_id == application_id:
                app.outcome = outcome
                if response_time_days:
                    app.response_time_days = response_time_days
                if feedback_notes:
                    app.feedback_notes = feedback_notes
                break

        self.save_applications()

    def analyze_template_performance(self) -> Dict[str, Any]:
        """Analyze template performance across applications"""

        if not self.applications:
            return {"message": "No applications to analyze yet"}

        # Group applications by template
        template_performance = {}

        for app in self.applications:
            template = app.template_used
            if template not in template_performance:
                template_performance[template] = {
                    "total_applications": 0,
                    "responses": 0,
                    "interviews": 0,
                    "offers": 0,
                    "avg_response_time": 0,
                    "avg_keyword_matches": 0,
                    "applications": []
                }

            perf = template_performance[template]
            perf["total_applications"] += 1
            perf["avg_keyword_matches"] += app.keyword_matches
            perf["applications"].append(app)

            if app.outcome in ["response", "interview", "offer"]:
                perf["responses"] += 1
            if app.outcome in ["interview", "offer"]:
                perf["interviews"] += 1
            if app.outcome == "offer":
                perf["offers"] += 1

        # Calculate rates and averages
        for template, perf in template_performance.items():
            total = perf["total_applications"]
            perf["response_rate"] = perf["responses"] / total if total > 0 else 0
            perf["interview_rate"] = perf["interviews"] / total if total > 0 else 0
            perf["offer_rate"] = perf["offers"] / total if total > 0 else 0
            perf["avg_keyword_matches"] = perf["avg_keyword_matches"] / total if total > 0 else 0

        return {
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "total_applications": len(self.applications),
            "template_performance": template_performance,
            "recommendations": self._generate_optimization_recommendations(template_performance)
        }

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key terms from job description"""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', job_description.lower())
        common_words = {'with', 'have', 'will', 'work', 'team', 'role', 'this', 'that'}
        keywords = [w for w in set(words) if w not in common_words]
        return keywords[:15]

    def _generate_template_reasoning(self, job_text: str, scores: Dict[str, int]) -> str:
        """Generate reasoning for template recommendation"""
        max_template = max(scores, key=scores.get)
        max_score = scores[max_template]

        if max_score == 0:
            return "No strong indicators found - consider manual template selection"

        template_reasons = {
            "brm_stakeholder_focused": f"High stakeholder/relationship focus (score: {max_score})",
            "technical_brm_hybrid": f"Technical keywords prominent (score: {max_score})",
            "senior_leadership_focused": f"Senior leadership indicators (score: {max_score})"
        }

        return template_reasons.get(max_template, f"Best match: {max_template}")

    def _generate_optimization_recommendations(self, performance: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance data"""
        recommendations = []

        if not performance:
            return ["Need more application data for meaningful analysis"]

        # Find best performing template
        best_template = max(performance.keys(),
                           key=lambda t: performance[t]["response_rate"])
        best_rate = performance[best_template]["response_rate"]

        if best_rate > 0.2:  # >20% response rate
            recommendations.append(f"Template '{best_template}' showing strong performance ({best_rate:.1%} response rate)")
        else:
            recommendations.append("All templates below 20% response rate - consider keyword optimization")

        # Check for sample size
        total_apps = sum(p["total_applications"] for p in performance.values())
        if total_apps < 10:
            recommendations.append(f"Need more applications ({total_apps}/10 minimum) for reliable analysis")

        return recommendations

    def load_templates(self):
        """Load templates from file"""
        if self.templates_file.exists():
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                self.templates = {
                    name: CVTemplate(**template_data)
                    for name, template_data in data.items()
                }

    def save_templates(self):
        """Save templates to file"""
        with open(self.templates_file, 'w') as f:
            json.dump({
                name: asdict(template)
                for name, template in self.templates.items()
            }, f, indent=2)

    def load_applications(self):
        """Load application tracking data"""
        if self.applications_file.exists():
            with open(self.applications_file, 'r') as f:
                data = json.load(f)
                self.applications = [
                    ApplicationTracking(**app_data)
                    for app_data in data
                ]

    def save_applications(self):
        """Save application tracking data"""
        with open(self.applications_file, 'w') as f:
            json.dump([asdict(app) for app in self.applications], f, indent=2)

def main():
    """Test the template system"""
    system = CVTemplateSystem()

    # Create initial templates
    print("🎯 Creating CV Template System")
    templates = system.create_initial_templates()
    print(f"✅ Created {len(templates)} templates")

    for name, template in templates.items():
        print(f"  • {name}: {template.hypothesis}")

    # Test template detection
    sample_job = """
    Senior Business Relationship Manager - Azure Cloud Services

    Leading technology company seeks experienced BRM to manage stakeholder
    relationships across enterprise Azure implementations. Role involves
    governance, portfolio management, and client engagement.
    """

    recommendation = system.detect_optimal_template(sample_job)
    print(f"\n🔍 Template Recommendation:")
    print(f"  Recommended: {recommendation['recommended_template']}")
    print(f"  Confidence: {recommendation['confidence_scores']}")
    print(f"  Reasoning: {recommendation['reasoning']}")

    # Test application tracking
    app_id = system.track_application(
        job_title="Senior BRM - Azure Services",
        company="Test Company",
        template_used=recommendation['recommended_template'],
        keyword_matches=12
    )
    print(f"\n📊 Tracked application: {app_id}")

    # Show performance analysis structure
    analysis = system.analyze_template_performance()
    print(f"\n📈 Performance Analysis: {analysis}")

if __name__ == "__main__":
    main()
