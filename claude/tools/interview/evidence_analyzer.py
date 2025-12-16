#!/usr/bin/env python3
"""
LLM-Enhanced Evidence Quality Analyzer

Provides semantic analysis of CV evidence against JD requirements using
local LLM (Ollama) to understand context, task complexity, and actual job fit.

Features:
- Evidence quality scoring with LLM reasoning
- Task complexity detection (engineering vs admin vs support)
- Certification status analysis
- Experience depth extraction
- Graceful fallback to rule-based scoring

Author: Maia System (SRE Principal Engineer)
Created: 2025-12-16
"""

import re
import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
LLM_TIMEOUT = 30  # seconds


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EvidenceQuality:
    """Result of LLM evidence quality analysis"""
    quality_score: int  # 0-100
    task_complexity: str  # engineering, administration, support, unknown
    reasoning: str
    confidence: float = 0.0  # LLM confidence in assessment


@dataclass
class CertificationStatus:
    """Result of certification status analysis"""
    status: str  # certified, preparing, expired, none
    score: int  # 0-100
    cert_name: str = ""
    details: str = ""


@dataclass
class ScaleIndicators:
    """Scale indicators extracted from evidence"""
    users: int = 0
    vms: int = 0
    regions: int = 0
    projects: int = 0
    years: int = 0


@dataclass
class EnhancedMatchResult:
    """Result of enhanced requirement matching"""
    requirement_text: str
    match_status: str  # STRONG, MODERATE, WEAK, NOT_FOUND
    score: int  # 0-100
    task_complexity: str
    llm_reasoning: str
    evidence_snippets: List[str] = field(default_factory=list)
    fallback_used: bool = False


# =============================================================================
# TASK COMPLEXITY PATTERNS
# =============================================================================

ENGINEERING_PATTERNS = [
    r'\b(design|architect|implement|develop|build)\w*\b',
    r'\bled\s+\w+\s*(migration|implementation|deployment|project)\b',
    r'\bmigrat\w+\s+\d+',  # "migrated 500 VMs"
    r'\b(ci/cd|pipeline|terraform|infrastructure as code|iac)\b',
    r'\b(federation|saml|oauth|oidc|conditional access)\b',
    r'\b(enterprise|large-scale|multi-region|high availability)\b',
    r'\b(graph api|rest api|sdk|automation framework)\b',
    r'\b(pim|privileged|zero trust)\b',
    r'\bautomation\s+framework\b',
]

ADMINISTRATION_PATTERNS = [
    r'\b(manage|configure|maintain|administer|assign|review)\w*\b',
    r'\b(group membership|license|permission|access review)\b',
    r'\b(mfa|multi-factor|policy)\b',
    r'\b(sharepoint|teams|exchange)\s*admin\b',
]

SUPPORT_PATTERNS = [
    r'\bcreated?\s+(user|account)\w*\b',  # "created user accounts"
    r'\b(reset|modify|terminate|provision)\w*\s*(user|account|password)\w*\b',
    r'\b(level [12]|l[12]|helpdesk|service desk)\b',
    r'\bprovid\w+\s+(level\s*[12]|l[12]|support)\b',
    r'\b(ticket|troubleshoot|resolve|escalat)\w*\b',
    r'\b(password reset|account creation|user onboarding)\b',
    r'\btroublesh\w+\s+\w*\s*(login|issue|problem)\b',  # "troubleshot login issues"
]


# =============================================================================
# LLM CLIENT
# =============================================================================

class OllamaClient:
    """Simple Ollama API client"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, timeout: int = LLM_TIMEOUT) -> str:
        """Generate completion from Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent scoring
                        "num_predict": 500,
                    }
                },
                timeout=timeout
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


# =============================================================================
# EVIDENCE QUALITY ANALYZER
# =============================================================================

class EvidenceQualityAnalyzer:
    """
    LLM-enhanced evidence quality analysis.

    Analyzes CV evidence against JD requirements to determine:
    - Quality of match (not just keyword presence)
    - Task complexity level
    - Certification status
    - Experience depth
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize analyzer with LLM client"""
        self.llm_client = OllamaClient(model=model)
        self._llm_available = None

    @property
    def llm_available(self) -> bool:
        """Check if LLM is available (cached)"""
        if self._llm_available is None:
            self._llm_available = self.llm_client.is_available()
        return self._llm_available

    def analyze_evidence(
        self,
        requirement: str,
        evidence: str
    ) -> EvidenceQuality:
        """
        Analyze evidence quality using LLM.

        Args:
            requirement: JD requirement text
            evidence: CV evidence text

        Returns:
            EvidenceQuality with score and reasoning
        """
        # Try LLM first
        if self.llm_available:
            try:
                return self._analyze_with_llm(requirement, evidence)
            except Exception:
                pass  # Fall through to rule-based

        # Fallback to rule-based
        return self._analyze_rule_based(requirement, evidence)

    def _analyze_with_llm(self, requirement: str, evidence: str) -> EvidenceQuality:
        """Use LLM for semantic analysis"""
        prompt = f"""Analyze this CV evidence against a job requirement. Be strict and accurate.

REQUIREMENT: {requirement}

CV EVIDENCE: {evidence}

Evaluate:
1. Does the evidence show the candidate can actually do what the requirement asks?
2. What is the task complexity level? (engineering=designs/architects, administration=configures/manages, support=creates users/resets passwords)
3. Is there depth of experience or just surface-level mention?

Respond in JSON format only:
{{"quality_score": <0-100>, "task_complexity": "<engineering|administration|support|unknown>", "reasoning": "<one sentence explanation>"}}

Be strict:
- User account creation/password resets = support level (score < 50)
- Managing groups/licenses = administration level (score 50-75)
- Designing policies/architecture = engineering level (score 75-100)
- "Preparing for certification" != "Certified"

JSON response:"""

        response = self.llm_client.generate(prompt)

        # Parse JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return EvidenceQuality(
                    quality_score=max(0, min(100, int(data.get("quality_score", 50)))),
                    task_complexity=data.get("task_complexity", "unknown"),
                    reasoning=data.get("reasoning", ""),
                    confidence=0.8
                )
        except (json.JSONDecodeError, ValueError):
            pass

        # If parsing fails, fall back to rule-based
        return self._analyze_rule_based(requirement, evidence)

    def _analyze_rule_based(self, requirement: str, evidence: str) -> EvidenceQuality:
        """Rule-based fallback analysis"""
        evidence_lower = evidence.lower()

        # Detect task complexity
        complexity = self.detect_task_complexity(evidence)

        # Score based on complexity
        if complexity == "engineering":
            score = 85
        elif complexity == "administration":
            score = 60
        elif complexity == "support":
            score = 35
        else:
            score = 50

        # Adjust based on experience depth
        years = self.extract_years_experience(evidence)
        if years >= 5:
            score = min(100, score + 10)
        elif years >= 3:
            score = min(100, score + 5)

        return EvidenceQuality(
            quality_score=score,
            task_complexity=complexity,
            reasoning=f"Rule-based: {complexity} level tasks detected",
            confidence=0.5
        )

    def detect_task_complexity(self, text: str) -> str:
        """
        Detect task complexity level from text.

        Args:
            text: Evidence text

        Returns:
            Complexity level: engineering, administration, support, or unknown
        """
        text_lower = text.lower()

        # Check engineering patterns
        engineering_score = sum(
            1 for pattern in ENGINEERING_PATTERNS
            if re.search(pattern, text_lower, re.IGNORECASE)
        )

        # Check administration patterns
        admin_score = sum(
            1 for pattern in ADMINISTRATION_PATTERNS
            if re.search(pattern, text_lower, re.IGNORECASE)
        )

        # Check support patterns
        support_score = sum(
            1 for pattern in SUPPORT_PATTERNS
            if re.search(pattern, text_lower, re.IGNORECASE)
        )

        # Determine complexity based on highest score
        max_score = max(engineering_score, admin_score, support_score)

        if max_score == 0:
            return "unknown"
        elif engineering_score == max_score:
            return "engineering"
        elif admin_score == max_score:
            return "administration"
        else:
            return "support"

    def analyze_certification_status(
        self,
        evidence: str,
        cert_name: str
    ) -> CertificationStatus:
        """
        Analyze certification status from evidence.

        Args:
            evidence: CV text mentioning certifications
            cert_name: Certification to check for

        Returns:
            CertificationStatus with status and score
        """
        evidence_lower = evidence.lower()
        cert_lower = cert_name.lower()

        # Check for "preparing" or "studying"
        preparing_patterns = [
            r'prepar\w*\s+for\s+.*' + re.escape(cert_lower),
            r'study\w*\s+for\s+.*' + re.escape(cert_lower),
            r'working\s+towards?\s+.*' + re.escape(cert_lower),
            r'pursuing\s+.*' + re.escape(cert_lower),
        ]

        for pattern in preparing_patterns:
            if re.search(pattern, evidence_lower):
                return CertificationStatus(
                    status="preparing",
                    score=25,
                    cert_name=cert_name,
                    details="Preparing for certification"
                )

        # Check for "expired"
        expired_patterns = [
            r'expired\s+.*' + re.escape(cert_lower),
            r'previously\s+held\s+.*' + re.escape(cert_lower),
            r'' + re.escape(cert_lower) + r'.*expired',
        ]

        for pattern in expired_patterns:
            if re.search(pattern, evidence_lower):
                return CertificationStatus(
                    status="expired",
                    score=60,
                    cert_name=cert_name,
                    details="Certification expired"
                )

        # Check for active certification
        certified_patterns = [
            r'certified\s+.*' + re.escape(cert_lower),
            r'' + re.escape(cert_lower) + r'.*certifi',
            r'obtained\s+.*' + re.escape(cert_lower),
            r'passed\s+.*' + re.escape(cert_lower),
            r'hold\w*\s+.*' + re.escape(cert_lower),
        ]

        for pattern in certified_patterns:
            if re.search(pattern, evidence_lower):
                return CertificationStatus(
                    status="certified",
                    score=100,
                    cert_name=cert_name,
                    details="Active certification"
                )

        # Check if cert name mentioned at all (might be certified but not explicit)
        if cert_lower in evidence_lower:
            # Could be certified, give moderate score
            return CertificationStatus(
                status="certified",
                score=100,
                cert_name=cert_name,
                details="Certification mentioned"
            )

        return CertificationStatus(
            status="none",
            score=0,
            cert_name=cert_name,
            details="Certification not found"
        )

    def extract_years_experience(self, text: str) -> int:
        """
        Extract years of experience from text.

        Args:
            text: CV text

        Returns:
            Years of experience (0 if not found)
        """
        text_lower = text.lower()

        # Pattern: "X years" or "X+ years"
        patterns = [
            r'(\d+)\+?\s*years?',
            r'over\s+(\d+)\s*years?',
            r'(\d+)\s*\+\s*years?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))

        # Check for written numbers
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        for word, num in number_words.items():
            if f'{word} year' in text_lower:
                return num

        return 0

    def extract_scale_indicators(self, text: str) -> ScaleIndicators:
        """
        Extract scale indicators from text.

        Args:
            text: CV text

        Returns:
            ScaleIndicators with users, VMs, regions, etc.
        """
        text_lower = text.lower()

        # Extract users
        users = 0
        users_match = re.search(r'(\d+)(?:,\d+)*\+?\s*users?', text_lower)
        if users_match:
            users = int(users_match.group(1).replace(',', ''))

        # Extract VMs
        vms = 0
        vms_match = re.search(r'(\d+)(?:,\d+)*\+?\s*(?:vms?|virtual machines?)', text_lower)
        if vms_match:
            vms = int(vms_match.group(1).replace(',', ''))

        # Extract regions
        regions = 0
        regions_match = re.search(r'(\d+)\s*regions?', text_lower)
        if regions_match:
            regions = int(regions_match.group(1))

        # Extract projects
        projects = 0
        projects_match = re.search(r'(\d+)\s*projects?', text_lower)
        if projects_match:
            projects = int(projects_match.group(1))

        return ScaleIndicators(
            users=users,
            vms=vms,
            regions=regions,
            projects=projects,
            years=self.extract_years_experience(text)
        )


# =============================================================================
# ENHANCED REQUIREMENT MATCHER
# =============================================================================

class EnhancedRequirementMatcher:
    """
    Enhanced requirement matcher that uses LLM for semantic analysis.

    Combines keyword matching with LLM-based evidence quality assessment
    for more accurate scoring.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize enhanced matcher"""
        self.analyzer = EvidenceQualityAnalyzer(model=model)

        # Import original matcher for keyword extraction
        from claude.tools.interview.requirement_matcher import (
            RequirementMatcher, SKILL_SYNONYMS, normalize_skill
        )
        self.base_matcher = RequirementMatcher()
        self.skill_synonyms = SKILL_SYNONYMS
        self.normalize_skill = normalize_skill

    def _call_llm(self, prompt: str) -> str:
        """Call LLM (can be mocked in tests)"""
        return self.analyzer.llm_client.generate(prompt)

    def match_requirement_enhanced(
        self,
        requirement: str,
        cv_text: str,
        requirement_type: str = "essential"
    ) -> EnhancedMatchResult:
        """
        Match requirement with LLM-enhanced scoring.

        Args:
            requirement: JD requirement text
            cv_text: Full CV text
            requirement_type: 'essential' or 'desirable'

        Returns:
            EnhancedMatchResult with LLM-informed score
        """
        # First, use base matcher to find relevant evidence
        base_result = self.base_matcher.match_requirement(
            requirement, cv_text, requirement_type
        )

        # If no match found by keywords, return early
        if base_result.match_status == "NOT_FOUND":
            return EnhancedMatchResult(
                requirement_text=requirement,
                match_status="NOT_FOUND",
                score=0,
                task_complexity="unknown",
                llm_reasoning="No keyword matches found in CV",
                evidence_snippets=[],
                fallback_used=False
            )

        # Get evidence snippets
        evidence_text = " ".join(base_result.evidence) if base_result.evidence else cv_text[:1000]

        # Analyze evidence quality with LLM
        try:
            quality = self.analyzer.analyze_evidence(requirement, evidence_text)
            fallback_used = quality.confidence < 0.7
        except Exception:
            # Fallback to rule-based
            quality = self.analyzer._analyze_rule_based(requirement, evidence_text)
            fallback_used = True

        # Determine match status based on LLM score
        if quality.quality_score >= 75:
            match_status = "STRONG"
        elif quality.quality_score >= 50:
            match_status = "MODERATE"
        elif quality.quality_score > 0:
            match_status = "WEAK"
        else:
            match_status = "NOT_FOUND"

        return EnhancedMatchResult(
            requirement_text=requirement,
            match_status=match_status,
            score=quality.quality_score,
            task_complexity=quality.task_complexity,
            llm_reasoning=quality.reasoning,
            evidence_snippets=base_result.evidence[:3] if base_result.evidence else [],
            fallback_used=fallback_used
        )


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for evidence analyzer testing"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM-Enhanced Evidence Analyzer")
    parser.add_argument('--requirement', '-r', required=True, help='JD requirement')
    parser.add_argument('--evidence', '-e', required=True, help='CV evidence text')
    parser.add_argument('--model', '-m', default=DEFAULT_MODEL, help='Ollama model')

    args = parser.parse_args()

    analyzer = EvidenceQualityAnalyzer(model=args.model)

    print(f"\nAnalyzing evidence quality...")
    print(f"Model: {args.model}")
    print(f"LLM available: {analyzer.llm_available}")

    result = analyzer.analyze_evidence(args.requirement, args.evidence)

    print(f"\n=== Results ===")
    print(f"Quality Score: {result.quality_score}/100")
    print(f"Task Complexity: {result.task_complexity}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Confidence: {result.confidence:.0%}")


if __name__ == '__main__':
    main()
