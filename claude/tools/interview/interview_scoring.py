#!/usr/bin/env python3
"""
Interview Scoring Frameworks

Multiple scoring approaches for interview analysis:
- 100-point keyword-based scoring (fast, heuristic)
- 50-point weighted framework (balanced, structured)
- LLM-based analysis (deep, nuanced)

Based on patterns from:
- claude/tools/experimental/analyze_interview_vtt.py (keyword scoring)
- claude/tools/experimental/analyze_interview_proper.py (LLM analysis)

Author: Maia System
Created: 2025-12-15 (Phase 223)
"""

import re
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ScoreResult:
    """Scoring result from any framework"""
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
    """
    Score interviews using multiple frameworks.

    Frameworks:
    - 100_point: Keyword-based technical scoring
    - 50_point: Weighted framework with leadership focus
    - llm: Full LLM analysis via Ollama
    """

    # Keyword categories for 100-point scoring
    KEYWORD_CATEGORIES = {
        'Azure Architecture': {
            'max_score': 30,
            'keywords': [
                'azure', 'paas', 'virtual machine', 'vm', 'subscription',
                'resource group', 'vnet', 'networking', 'app service', 'function',
                'key vault', 'aks', 'container', 'storage', 'landing zone',
                'entra', 'active directory', 'blob', 'cosmos'
            ]
        },
        'IaC & Automation': {
            'max_score': 25,
            'keywords': [
                'terraform', 'infrastructure as code', 'iac', 'bicep', 'arm template',
                'cloudformation', 'module', 'blueprint', 'automation', 'devops',
                'ci/cd', 'pipeline', 'yaml', 'ansible', 'pulumi', 'github actions'
            ]
        },
        'Leadership & Mentorship': {
            'max_score': 20,
            'keywords': [
                'team', 'lead', 'mentor', 'train', 'teach', 'junior',
                'manage', 'delegate', 'document', 'knowledge transfer',
                'coach', 'develop', 'upskill', 'onboard', 'performance review'
            ]
        },
        'MSP Multi-tenant': {
            'max_score': 15,
            'keywords': [
                'msp', 'managed service', 'multi-tenant', 'client', 'customer',
                'multi-client', 'shared', 'isolation', 'chargeback', 'sla',
                'service level', 'white label'
            ]
        },
        'Security & Governance': {
            'max_score': 10,
            'keywords': [
                'security', 'rbac', 'policy', 'governance', 'compliance',
                'defender', 'sentinel', 'zero trust', 'encryption', 'identity',
                'conditional access', 'mfa', 'privileged', 'audit'
            ]
        }
    }

    # Green flag patterns
    GREEN_FLAG_PATTERNS = [
        (r'az-305|az-104|azure architect|solution architect|aws certified', 'Senior cloud certifications'),
        (r'kubernetes|aks|eks|k8s', 'Kubernetes/container orchestration experience'),
        (r'terraform', 'Terraform expertise'),
        (r'led team|team lead|managed team|mentored|direct reports', 'Demonstrated team leadership'),
        (r'certified|certification', 'Professional certifications'),
        (r'production|live environment|mission critical', 'Production environment experience'),
    ]

    # Red flag patterns
    RED_FLAG_PATTERNS = [
        (r'job.{0,10}hop', 'Possible job hopping mentioned'),
        (r'never.{0,20}managed|no.{0,20}direct reports', 'No direct management experience'),
        (r'not.{0,10}certified|no.{0,10}certification', 'No certifications'),
    ]

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def score(
        self,
        dialogue: Dict[str, List[str]],
        framework: str = "100_point",
        role_context: Optional[str] = None
    ) -> ScoreResult:
        """
        Score interview dialogue using specified framework.

        Args:
            dialogue: Dict mapping speaker -> list of statements
            framework: '100_point', '50_point', or 'llm'
            role_context: Optional role requirements context

        Returns:
            ScoreResult with detailed breakdown
        """
        if framework == "100_point":
            return self._score_100_point(dialogue)
        elif framework == "50_point":
            return self._score_50_point(dialogue, role_context)
        elif framework == "llm":
            return self._score_llm(dialogue, role_context)
        else:
            raise ValueError(f"Unknown framework: {framework}")

    def _score_100_point(self, dialogue: Dict[str, List[str]]) -> ScoreResult:
        """
        100-point keyword-based scoring.

        Fast heuristic scoring based on keyword presence.
        """
        # Combine all candidate dialogue
        all_text = ' '.join([' '.join(texts) for texts in dialogue.values()])
        all_text_lower = all_text.lower()

        scores = {}
        total = 0

        # Score each category
        for category, config in self.KEYWORD_CATEGORIES.items():
            matches = sum(2 for kw in config['keywords'] if kw in all_text_lower)
            score = min(config['max_score'], matches)
            scores[category] = score
            total += score

        # Calculate response metrics
        response_count = sum(len(texts) for texts in dialogue.values())

        # Detect flags
        red_flags = []
        green_flags = []

        for pattern, flag_text in self.GREEN_FLAG_PATTERNS:
            if re.search(pattern, all_text_lower):
                green_flags.append(flag_text)

        for pattern, flag_text in self.RED_FLAG_PATTERNS:
            if re.search(pattern, all_text_lower):
                red_flags.append(flag_text)

        # Add engagement flags
        if response_count < 20:
            red_flags.append(f"Limited verbal engagement ({response_count} responses)")
        elif response_count > 50:
            green_flags.append(f"Strong verbal engagement ({response_count} responses)")

        # Determine recommendation
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

    def _score_50_point(
        self,
        dialogue: Dict[str, List[str]],
        role_context: Optional[str] = None
    ) -> ScoreResult:
        """
        50-point weighted framework with leadership focus.

        Sections:
        - Leadership Validation: 20 points (50% weight)
        - Career Motivations: 10 points (20% weight)
        - Technical Validation: 10 points (20% weight)
        - Client Advisory: 10 points (10% weight)
        """
        all_text = ' '.join([' '.join(texts) for texts in dialogue.values()])
        all_text_lower = all_text.lower()

        scores = {}

        # Section 1: Leadership (20 points)
        leadership_keywords = [
            'direct reports', 'managed', 'team of', 'led', 'mentored',
            'performance review', 'hiring', 'fired', 'coach', 'develop',
            'autonomy', 'decision', 'accountable', 'responsible for'
        ]
        leadership_matches = sum(1.5 for kw in leadership_keywords if kw in all_text_lower)
        scores['leadership'] = min(20, leadership_matches)

        # Section 2: Career (10 points)
        career_keywords = [
            'long term', 'growth', 'career', 'progression', 'stability',
            'vision', 'goal', 'aspiration', 'next step', 'development'
        ]
        career_matches = sum(1 for kw in career_keywords if kw in all_text_lower)
        scores['career'] = min(10, career_matches)

        # Section 3: Technical (10 points)
        technical_keywords = [
            'azure', 'terraform', 'kubernetes', 'docker', 'ci/cd',
            'intune', 'm365', 'endpoint', 'architecture', 'design'
        ]
        technical_matches = sum(1 for kw in technical_keywords if kw in all_text_lower)
        scores['technical'] = min(10, technical_matches)

        # Section 4: Advisory (10 points)
        advisory_keywords = [
            'client', 'stakeholder', 'pushback', 'recommend', 'advise',
            'consult', 'proposal', 'business case', 'roi', 'value'
        ]
        advisory_matches = sum(1 for kw in advisory_keywords if kw in all_text_lower)
        scores['advisory'] = min(10, advisory_matches)

        total = sum(scores.values())
        percentage = (total / 50) * 100

        # Weighted score (leadership is 50% weight)
        weighted = (
            scores['leadership'] * 0.50 +
            scores['career'] * 0.20 +
            scores['technical'] * 0.20 +
            scores['advisory'] * 0.10
        ) * 2  # Scale back to 50

        # Determine recommendation
        if total >= 40:
            recommendation = "STRONG_HIRE"
            rationale = "Strong performance across all dimensions"
        elif total >= 35:
            recommendation = "HIRE"
            rationale = "Good overall fit with some areas to develop"
        elif total >= 30:
            recommendation = "CONSIDER"
            rationale = "Moderate fit, key gaps to evaluate"
        else:
            recommendation = "DO_NOT_HIRE"
            rationale = "Insufficient evidence across key areas"

        return ScoreResult(
            framework="50_point",
            total_score=total,
            max_score=50,
            percentage=percentage,
            breakdown={
                'leadership_validation': scores['leadership'],
                'career_motivations': scores['career'],
                'technical_validation': scores['technical'],
                'client_advisory': scores['advisory'],
                'weighted_score': weighted
            },
            red_flags=[],
            green_flags=[],
            recommendation=recommendation,
            rationale=rationale
        )

    def _score_llm(
        self,
        dialogue: Dict[str, List[str]],
        role_context: Optional[str] = None
    ) -> ScoreResult:
        """
        LLM-based deep analysis using Ollama.

        Provides nuanced understanding of interview content.
        """
        # Combine dialogue into conversation format
        conversation = ""
        for speaker, texts in dialogue.items():
            for text in texts:
                conversation += f"{speaker}: {text}\n\n"

        # Limit context size
        conversation = conversation[:25000]

        role_requirements = role_context or """
        - 5+ years cloud engineering (Azure primary)
        - Infrastructure as Code (Terraform, Bicep)
        - Team leadership: direct reports, people management
        - MSP multi-tenant architecture patterns
        - Client advisory and consultative approach
        """

        prompt = f"""Analyze this interview transcript and provide a structured assessment.

ROLE REQUIREMENTS:
{role_requirements}

INTERVIEW TRANSCRIPT:
{conversation}

Provide your analysis in this exact JSON format:
{{
  "leadership_score": <0-20>,
  "leadership_evidence": "<specific quotes showing leadership>",
  "technical_score": <0-15>,
  "technical_evidence": "<specific quotes showing technical depth>",
  "career_score": <0-10>,
  "career_evidence": "<quotes about career motivations>",
  "advisory_score": <0-5>,
  "advisory_evidence": "<quotes about client advisory>",
  "red_flags": ["<concern 1>", "<concern 2>"],
  "green_flags": ["<strength 1>", "<strength 2>"],
  "recommendation": "STRONG_HIRE|HIRE|CONSIDER|DO_NOT_HIRE",
  "rationale": "<2-3 sentence summary>"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            result_text = response.json().get("response", "{}")

            # Try to parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            analysis = json.loads(result_text.strip())

            total = (
                analysis.get('leadership_score', 0) +
                analysis.get('technical_score', 0) +
                analysis.get('career_score', 0) +
                analysis.get('advisory_score', 0)
            )

            return ScoreResult(
                framework="llm",
                total_score=total,
                max_score=50,
                percentage=(total / 50) * 100,
                breakdown={
                    'leadership': analysis.get('leadership_score', 0),
                    'leadership_evidence': analysis.get('leadership_evidence', ''),
                    'technical': analysis.get('technical_score', 0),
                    'technical_evidence': analysis.get('technical_evidence', ''),
                    'career': analysis.get('career_score', 0),
                    'career_evidence': analysis.get('career_evidence', ''),
                    'advisory': analysis.get('advisory_score', 0),
                    'advisory_evidence': analysis.get('advisory_evidence', ''),
                },
                red_flags=analysis.get('red_flags', []),
                green_flags=analysis.get('green_flags', []),
                recommendation=analysis.get('recommendation', 'UNKNOWN'),
                rationale=analysis.get('rationale', '')
            )

        except json.JSONDecodeError as e:
            return ScoreResult(
                framework="llm",
                total_score=0,
                max_score=50,
                percentage=0,
                breakdown={'error': f'JSON parse error: {e}'},
                recommendation="ERROR",
                rationale="Failed to parse LLM response"
            )
        except Exception as e:
            return ScoreResult(
                framework="llm",
                total_score=0,
                max_score=50,
                percentage=0,
                breakdown={'error': str(e)},
                recommendation="ERROR",
                rationale=f"LLM analysis failed: {e}"
            )


def main():
    """Test scoring with sample data"""
    scorer = InterviewScorer()

    # Sample dialogue
    sample_dialogue = {
        "Candidate": [
            "I have 6 years of experience with Azure and terraform",
            "I led a team of 5 engineers and mentored junior developers",
            "We implemented AKS clusters across multiple clients",
            "I'm certified in AZ-305 and AZ-104"
        ]
    }

    print("\n100-Point Scoring:")
    result = scorer.score(sample_dialogue, "100_point")
    print(f"  Total: {result.total_score}/{result.max_score} ({result.percentage:.1f}%)")
    print(f"  Recommendation: {result.recommendation}")
    print(f"  Green flags: {result.green_flags}")

    print("\n50-Point Scoring:")
    result = scorer.score(sample_dialogue, "50_point")
    print(f"  Total: {result.total_score}/{result.max_score} ({result.percentage:.1f}%)")
    print(f"  Recommendation: {result.recommendation}")


if __name__ == '__main__':
    main()
