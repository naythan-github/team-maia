#!/usr/bin/env python3
"""Interview Scoring - TDD Implementation"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ScoreResult:
    """Scoring result"""
    framework: str
    total_score: float
    max_score: float
    percentage: float
    breakdown: Dict[str, Any]
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    recommendation: str = ""
    rationale: str = ""


class InterviewScorer:
    """Score interviews - TDD implementation"""

    KEYWORD_CATEGORIES = {
        'Azure Architecture': {
            'max_score': 30,
            'keywords': ['azure', 'paas', 'virtual machine', 'vm', 'subscription',
                        'resource group', 'vnet', 'networking', 'app service', 'function',
                        'key vault', 'aks', 'container', 'storage', 'landing zone']
        },
        'IaC & Automation': {
            'max_score': 25,
            'keywords': ['terraform', 'infrastructure as code', 'iac', 'bicep', 'arm template',
                        'cloudformation', 'module', 'blueprint', 'automation', 'devops',
                        'ci/cd', 'pipeline', 'yaml']
        },
        'Leadership & Mentorship': {
            'max_score': 20,
            'keywords': ['team', 'lead', 'mentor', 'train', 'teach', 'junior',
                        'manage', 'delegate', 'document', 'knowledge transfer']
        },
        'MSP Multi-tenant': {
            'max_score': 15,
            'keywords': ['msp', 'managed service', 'multi-tenant', 'client', 'customer']
        },
        'Security & Governance': {
            'max_score': 10,
            'keywords': ['security', 'rbac', 'policy', 'governance', 'compliance']
        }
    }

    GREEN_FLAG_PATTERNS = [
        (r'az-305|az-104|azure architect|solution architect|aws certified', 'Senior cloud certifications'),
        (r'kubernetes|aks|eks|k8s', 'Kubernetes/container orchestration experience'),
        (r'terraform', 'Terraform expertise'),
        (r'led team|team lead|managed team|mentored|direct reports', 'Demonstrated team leadership'),
        (r'certified|certification', 'Professional certifications'),
    ]

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def score(self, dialogue: Dict[str, List[str]], framework: str = "100_point",
              role_context: Optional[str] = None) -> ScoreResult:
        """Score - implemented to pass tests"""
        import re

        if framework == "100_point":
            return self._score_100_point(dialogue)
        elif framework == "50_point":
            return self._score_50_point(dialogue)
        else:
            raise ValueError(f"Unknown framework: {framework}")

    def _score_100_point(self, dialogue: Dict[str, List[str]]) -> ScoreResult:
        """100-point scoring - implemented to pass tests"""
        import re

        all_text = ' '.join([' '.join(texts) for texts in dialogue.values()])
        all_text_lower = all_text.lower()

        scores = {}
        total = 0

        for category, config in self.KEYWORD_CATEGORIES.items():
            matches = sum(2 for kw in config['keywords'] if kw in all_text_lower)
            score = min(config['max_score'], matches)
            scores[category] = score
            total += score

        response_count = sum(len(texts) for texts in dialogue.values())

        red_flags = []
        green_flags = []

        for pattern, flag_text in self.GREEN_FLAG_PATTERNS:
            if re.search(pattern, all_text_lower):
                green_flags.append(flag_text)

        if response_count < 20:
            red_flags.append(f"Limited verbal engagement ({response_count} responses)")
        elif response_count > 50:
            green_flags.append(f"Strong verbal engagement ({response_count} responses)")

        percentage = (total / 100) * 100
        if percentage >= 60:
            recommendation = "STRONG_HIRE"
            rationale = "Strong technical coverage across key areas"
        elif percentage >= 40:
            recommendation = "CONSIDER"
            rationale = "Moderate technical fit, review gaps"
        else:
            recommendation = "DO_NOT_HIRE"
            rationale = "Insufficient technical depth demonstrated"

        return ScoreResult(
            framework="100_point",
            total_score=total,
            max_score=100,
            percentage=percentage,
            breakdown=scores,
            red_flags=red_flags,
            green_flags=green_flags,
            recommendation=recommendation,
            rationale=rationale
        )

    def _score_50_point(self, dialogue: Dict[str, List[str]]) -> ScoreResult:
        """50-point scoring - implemented to pass tests"""
        all_text = ' '.join([' '.join(texts) for texts in dialogue.values()])
        all_text_lower = all_text.lower()

        scores = {}

        leadership_keywords = ['direct reports', 'managed', 'team of', 'led', 'mentored']
        scores['leadership_validation'] = min(20, sum(1.5 for kw in leadership_keywords if kw in all_text_lower))

        career_keywords = ['long term', 'growth', 'career', 'progression']
        scores['career_motivations'] = min(10, sum(1 for kw in career_keywords if kw in all_text_lower))

        technical_keywords = ['azure', 'terraform', 'kubernetes', 'docker']
        scores['technical_validation'] = min(10, sum(1 for kw in technical_keywords if kw in all_text_lower))

        advisory_keywords = ['client', 'stakeholder', 'recommend']
        scores['client_advisory'] = min(10, sum(1 for kw in advisory_keywords if kw in all_text_lower))

        total = sum(scores.values())
        percentage = (total / 50) * 100

        if total >= 40:
            recommendation = "STRONG_HIRE"
        elif total >= 30:
            recommendation = "CONSIDER"
        else:
            recommendation = "DO_NOT_HIRE"

        return ScoreResult(
            framework="50_point",
            total_score=total,
            max_score=50,
            percentage=percentage,
            breakdown=scores,
            recommendation=recommendation,
            rationale="50-point weighted scoring"
        )
