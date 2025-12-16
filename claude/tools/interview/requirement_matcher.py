#!/usr/bin/env python3
"""
Requirement-by-Requirement Matcher - Enhanced CV/JD matching with semantic understanding.

Features:
- Skill synonyms/taxonomy for better matching
- Requirement-level breakdown (not just overall score)
- Weighted scoring (essential 3x, desirable 1x)
- Evidence extraction for each match

Author: Maia System (SRE Principal Engineer)
Created: 2025-12-16
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


# =============================================================================
# SKILL SYNONYMS / TAXONOMY
# =============================================================================

SKILL_SYNONYMS = {
    # Identity & Access Management
    "entra id": ["azure ad", "aad", "microsoft entra", "azure active directory"],
    "active directory": ["ad", "on-prem ad", "windows ad"],
    "conditional access": ["ca policies", "mfa policies"],

    # Container & Orchestration
    "kubernetes": ["k8s", "aks", "eks", "gke", "openshift"],
    "docker": ["containers", "containerization", "container runtime"],
    "helm": ["helm charts", "kubernetes package"],

    # Infrastructure as Code
    "terraform": ["tf", "hashicorp terraform", "terraform cloud"],
    "infrastructure as code": ["iac", "infra as code"],
    "arm templates": ["azure resource manager", "arm"],
    "bicep": ["azure bicep"],
    "pulumi": ["pulumi iac"],
    "ansible": ["ansible automation", "ansible playbooks"],

    # Cloud Platforms
    "azure": ["microsoft azure", "azure cloud", "ms azure"],
    "aws": ["amazon web services", "amazon aws"],
    "gcp": ["google cloud", "google cloud platform"],

    # Scripting & Languages
    "powershell": ["ps", "pwsh", "powershell core"],
    "python": ["py", "python3"],
    "bash": ["shell", "shell scripting", "bash scripting"],

    # CI/CD & DevOps
    "ci/cd": ["cicd", "continuous integration", "continuous deployment", "devops pipelines"],
    "azure devops": ["ado", "azure pipelines", "vsts"],
    "github actions": ["gh actions", "github workflows"],
    "jenkins": ["jenkins pipelines", "jenkins ci"],

    # Monitoring & Observability
    "monitoring": ["observability", "telemetry"],
    "azure monitor": ["log analytics", "application insights"],
    "prometheus": ["prom", "prometheus monitoring"],
    "grafana": ["grafana dashboards"],

    # Networking
    "networking": ["network engineering", "network administration"],
    "vnet": ["virtual network", "azure vnet", "vnets"],
    "vpn": ["site-to-site vpn", "point-to-site vpn", "s2s vpn"],
    "load balancer": ["lb", "azure load balancer", "alb"],
    "firewall": ["azure firewall", "nsg", "network security group"],

    # Virtualization
    "hyper-v": ["hyperv", "hyper v", "microsoft hyper-v"],
    "vmware": ["vsphere", "esxi", "vcenter"],
    "virtualization": ["vm", "virtual machines"],

    # Databases
    "sql": ["sql server", "mssql", "t-sql", "azure sql"],
    "nosql": ["mongodb", "cosmosdb", "dynamodb"],

    # Security
    "security": ["cybersecurity", "infosec", "information security"],
    "compliance": ["governance", "audit", "regulatory compliance"],
}

# Build reverse lookup (synonym -> canonical)
SYNONYM_TO_CANONICAL = {}
for canonical, synonyms in SKILL_SYNONYMS.items():
    for synonym in synonyms:
        SYNONYM_TO_CANONICAL[synonym.lower()] = canonical
    SYNONYM_TO_CANONICAL[canonical.lower()] = canonical


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill name to its canonical form using synonyms.

    Args:
        skill: Skill name to normalize

    Returns:
        Canonical skill name, or original if no synonym found
    """
    skill_lower = skill.lower().strip()
    return SYNONYM_TO_CANONICAL.get(skill_lower, skill_lower)


# =============================================================================
# DATA CLASSES & ENUMS
# =============================================================================

class MatchStatus(Enum):
    """Match strength for a requirement"""
    STRONG = "STRONG"        # Direct match with substantial evidence
    MODERATE = "MODERATE"    # Match with some evidence
    WEAK = "WEAK"           # Mentioned but limited evidence
    NOT_FOUND = "NOT_FOUND"  # No match found


# Weight multipliers
WEIGHT_ESSENTIAL = 3
WEIGHT_DESIRABLE = 1


@dataclass
class RequirementMatch:
    """Result of matching a single requirement against CV"""
    requirement_text: str
    requirement_type: str  # essential, desirable
    match_status: str      # STRONG, MODERATE, WEAK, NOT_FOUND
    score: int             # 0-100 raw score
    evidence: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    weighted_score: int = 0  # score * weight multiplier

    def __post_init__(self):
        """Calculate weighted score after initialization"""
        if self.weighted_score == 0:
            weight = WEIGHT_ESSENTIAL if self.requirement_type == "essential" else WEIGHT_DESIRABLE
            self.weighted_score = self.score * weight


# =============================================================================
# REQUIREMENT MATCHER
# =============================================================================

class RequirementMatcher:
    """
    Matches CV content against JD requirements with semantic understanding.

    Features:
    - Synonym matching (Azure AD = Entra ID)
    - Evidence extraction
    - Weighted scoring
    - Requirement-level breakdown
    """

    def __init__(self):
        """Initialize matcher"""
        self.skill_synonyms = SKILL_SYNONYMS
        self.synonym_lookup = SYNONYM_TO_CANONICAL

    def match_requirement(
        self,
        requirement: str,
        cv_text: str,
        requirement_type: str = "essential"
    ) -> RequirementMatch:
        """
        Match a single requirement against CV text.

        Args:
            requirement: The JD requirement text
            cv_text: Full CV text content
            requirement_type: 'essential' or 'desirable'

        Returns:
            RequirementMatch with score and evidence
        """
        cv_lower = cv_text.lower()
        req_lower = requirement.lower()

        # Extract skills mentioned in requirement
        req_skills = self._extract_skills_from_text(requirement)

        # Find matches in CV
        matched_skills = []
        evidence = []
        total_score = 0

        for skill in req_skills:
            # Get canonical form and all synonyms
            canonical = normalize_skill(skill)
            skill_variants = [canonical]
            if canonical in self.skill_synonyms:
                skill_variants.extend(self.skill_synonyms[canonical])

            # Search for any variant in CV
            for variant in skill_variants:
                if variant.lower() in cv_lower:
                    matched_skills.append(canonical)
                    # Extract evidence (context around ALL matches)
                    ev_list = self._extract_evidence(cv_text, variant)
                    evidence.extend(ev_list)
                    break

        # If no explicit skills found, try broader matching
        if not matched_skills:
            # Try matching key phrases from requirement
            key_phrases = self._extract_key_phrases(requirement)
            for phrase in key_phrases:
                if phrase.lower() in cv_lower:
                    matched_skills.append(phrase)
                    ev_list = self._extract_evidence(cv_text, phrase)
                    evidence.extend(ev_list)

        # Calculate score based on matches
        if not req_skills:
            req_skills = ["_generic_"]  # Prevent division by zero

        match_ratio = len(set(matched_skills)) / max(len(req_skills), 1)

        # Score calculation - be generous when there's good evidence
        # If we have matches AND evidence, boost the status
        has_evidence = len(evidence) > 0

        if match_ratio >= 0.5 or (match_ratio > 0 and has_evidence and len(evidence) >= 1):
            if match_ratio >= 0.8 or len(evidence) >= 2:
                total_score = 90
                status = MatchStatus.STRONG.value
            else:
                total_score = 70
                status = MatchStatus.MODERATE.value
        elif match_ratio > 0:
            total_score = 40
            status = MatchStatus.WEAK.value
        else:
            total_score = 0
            status = MatchStatus.NOT_FOUND.value

        # Boost score based on evidence depth
        if evidence:
            evidence_boost = min(len(evidence) * 5, 10)  # Up to +10 for multiple evidence
            total_score = min(total_score + evidence_boost, 100)

        return RequirementMatch(
            requirement_text=requirement,
            requirement_type=requirement_type,
            match_status=status,
            score=total_score,
            evidence=evidence[:3],  # Top 3 evidence snippets
            matched_skills=list(set(matched_skills))
        )

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skill keywords from text"""
        skills = []
        text_lower = text.lower()

        # Check for all known skills and their synonyms
        all_skills = set(self.skill_synonyms.keys())
        for synonyms in self.skill_synonyms.values():
            all_skills.update(synonyms)

        for skill in all_skills:
            if skill.lower() in text_lower:
                canonical = normalize_skill(skill)
                if canonical not in skills:
                    skills.append(canonical)

        return skills

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases for broader matching"""
        # Remove common words and extract meaningful phrases
        stop_words = {'experience', 'required', 'skills', 'knowledge', 'with', 'and', 'or', 'the', 'a', 'an', 'in', 'of'}
        words = re.findall(r'\b\w+\b', text.lower())
        phrases = [w for w in words if w not in stop_words and len(w) > 3]
        return phrases[:5]  # Top 5 key phrases

    def _extract_evidence(self, text: str, keyword: str, context_chars: int = 100) -> List[str]:
        """Extract context around ALL keyword matches"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        evidence_list = []
        seen_snippets = set()

        # Find all occurrences
        start_pos = 0
        while True:
            idx = text_lower.find(keyword_lower, start_pos)
            if idx == -1:
                break

            start = max(0, idx - context_chars)
            end = min(len(text), idx + len(keyword) + context_chars)

            snippet = text[start:end].strip()
            snippet = re.sub(r'\s+', ' ', snippet)

            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            # Avoid duplicate/overlapping snippets
            snippet_key = snippet[:50]  # Use first 50 chars as key
            if snippet_key not in seen_snippets:
                seen_snippets.add(snippet_key)
                evidence_list.append(snippet)

            start_pos = idx + len(keyword)

        return evidence_list

    def match_all_requirements(
        self,
        requirements: List[Dict[str, str]],
        cv_text: str
    ) -> List[RequirementMatch]:
        """
        Match CV against all JD requirements.

        Args:
            requirements: List of {"text": str, "type": str} dicts
            cv_text: Full CV text

        Returns:
            List of RequirementMatch objects
        """
        results = []
        for req in requirements:
            match = self.match_requirement(
                requirement=req.get("text", ""),
                cv_text=cv_text,
                requirement_type=req.get("type", "essential")
            )
            results.append(match)
        return results

    def calculate_overall_score(self, matches: List[RequirementMatch]) -> float:
        """
        Calculate overall weighted score from requirement matches.

        Args:
            matches: List of RequirementMatch objects

        Returns:
            Overall percentage score (0-100)
        """
        if not matches:
            return 0.0

        total_weighted = sum(m.weighted_score for m in matches)

        # Calculate max possible weighted score
        max_weighted = sum(
            100 * (WEIGHT_ESSENTIAL if m.requirement_type == "essential" else WEIGHT_DESIRABLE)
            for m in matches
        )

        if max_weighted == 0:
            return 0.0

        return round((total_weighted / max_weighted) * 100, 1)

    def generate_breakdown_report(
        self,
        matches: List[RequirementMatch],
        candidate_name: str
    ) -> str:
        """
        Generate markdown report with requirement-by-requirement breakdown.

        Args:
            matches: List of RequirementMatch objects
            candidate_name: Candidate's name

        Returns:
            Markdown formatted report
        """
        lines = [
            f"## Requirement Breakdown: {candidate_name}",
            "",
            f"**Overall Score:** {self.calculate_overall_score(matches):.1f}%",
            "",
            "### Essential Requirements",
            ""
        ]

        essential = [m for m in matches if m.requirement_type == "essential"]
        desirable = [m for m in matches if m.requirement_type == "desirable"]

        # Status icons
        icons = {
            "STRONG": "✅",
            "MODERATE": "⚠️",
            "WEAK": "🔸",
            "NOT_FOUND": "❌"
        }

        for m in essential:
            icon = icons.get(m.match_status, "❓")
            lines.append(f"{icon} **{m.requirement_text[:60]}{'...' if len(m.requirement_text) > 60 else ''}**")
            lines.append(f"   - Status: {m.match_status} ({m.score}%)")
            if m.matched_skills:
                lines.append(f"   - Matched: {', '.join(m.matched_skills)}")
            if m.evidence:
                lines.append(f"   - Evidence: \"{m.evidence[0][:80]}...\"")
            lines.append("")

        if desirable:
            lines.append("### Desirable Requirements")
            lines.append("")

            for m in desirable:
                icon = icons.get(m.match_status, "❓")
                lines.append(f"{icon} **{m.requirement_text[:60]}{'...' if len(m.requirement_text) > 60 else ''}**")
                lines.append(f"   - Status: {m.match_status} ({m.score}%)")
                if m.matched_skills:
                    lines.append(f"   - Matched: {', '.join(m.matched_skills)}")
                lines.append("")

        # Summary
        essential_met = len([m for m in essential if m.match_status in ["STRONG", "MODERATE"]])
        desirable_met = len([m for m in desirable if m.match_status in ["STRONG", "MODERATE"]])

        lines.append("### Summary")
        lines.append(f"- Essential met: {essential_met}/{len(essential)}")
        lines.append(f"- Desirable met: {desirable_met}/{len(desirable)}")

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for requirement matcher"""
    import argparse

    parser = argparse.ArgumentParser(description="Requirement-by-Requirement CV Matcher")
    parser.add_argument('--candidate', required=True, help='Candidate name')
    parser.add_argument('--role', required=True, help='Role title')

    args = parser.parse_args()

    from claude.tools.interview.cv_parser import CVParser
    import sqlite3

    cv_parser = CVParser()
    matcher = RequirementMatcher()

    # Get JD
    jd = cv_parser.get_jd(args.role)
    if not jd:
        print(f"JD not found: {args.role}")
        return

    requirements = cv_parser.get_jd_requirements(jd['jd_id'])
    jd_reqs = [{"text": r['requirement_text'], "type": r['requirement_type']} for r in requirements]

    # Get CV text
    conn = sqlite3.connect(cv_parser.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT content_text FROM candidate_documents WHERE candidate_name LIKE ? LIMIT 1",
        (f"%{args.candidate}%",)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"CV not found for: {args.candidate}")
        return

    cv_text = row['content_text']

    # Match
    results = matcher.match_all_requirements(jd_reqs, cv_text)
    report = matcher.generate_breakdown_report(results, args.candidate)

    print(report)


if __name__ == '__main__':
    main()
