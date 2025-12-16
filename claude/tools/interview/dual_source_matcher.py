#!/usr/bin/env python3
"""
Dual-Source Matcher - CV + Interview Verification System

Extends the Interview Analyst with CV data integration for:
- Verification of CV claims against interview evidence
- Detection of bonus skills demonstrated but not on CV
- Generation of follow-up questions for unverified claims

Author: Maia System (SRE Principal Engineer + Interview Analyst)
Created: 2025-12-16 (Phase 2: CV Integration)
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.interview.interview_analyst import (
    RequirementMatcher,
    RequirementMatch,
    JDParser,
    ParsedJD,
    FitReport,
    FitReportGenerator
)


# =============================================================================
# DATA CLASSES
# =============================================================================

class VerificationStatus(Enum):
    """Verification status for CV claims vs interview evidence"""
    VERIFIED = "VERIFIED"       # CV claimed AND interview demonstrated
    UNVERIFIED = "UNVERIFIED"   # CV claimed but NOT discussed in interview
    BONUS = "BONUS"             # NOT on CV but demonstrated in interview
    NO_MATCH = "NO_MATCH"       # Neither CV nor interview


@dataclass
class EnhancedRequirementMatch:
    """Enhanced requirement match with CV + Interview dual-source"""
    requirement: str
    cv_match: str                       # CLAIMED, NOT_CLAIMED
    interview_match: str                # STRONG, MODERATE, WEAK, NO_MATCH
    verification_status: str            # VERIFIED, UNVERIFIED, BONUS, NO_MATCH
    cv_evidence: List[str] = field(default_factory=list)
    interview_evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class EnhancedFitReport(FitReport):
    """Enhanced fit report with CV verification data"""
    verification_summary: Dict[str, Any] = field(default_factory=dict)
    unverified_claims: List[str] = field(default_factory=list)
    bonus_skills: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    cv_interview_alignment: float = 0.0


# =============================================================================
# DUAL SOURCE MATCHER
# =============================================================================

class DualSourceMatcher:
    """
    Matches requirements against both CV and interview data.

    Verification Logic:
    - CV CLAIMED + Interview STRONG/MODERATE = VERIFIED
    - CV CLAIMED + Interview WEAK/NO_MATCH = UNVERIFIED
    - CV NOT_CLAIMED + Interview STRONG/MODERATE/WEAK = BONUS
    - CV NOT_CLAIMED + Interview NO_MATCH = NO_MATCH
    """

    # Skill name normalization mappings
    SKILL_ALIASES = {
        'kubernetes': ['k8s', 'aks', 'eks', 'gke'],
        'terraform': ['iac', 'infrastructure as code'],
        'azure': ['microsoft azure', 'az-'],
        'aws': ['amazon web services'],
        'gcp': ['google cloud'],
        'python': ['py'],
        'powershell': ['ps1'],
        'docker': ['containers'],
        'active directory': ['ad', 'azure ad', 'entra'],
    }

    def __init__(self):
        self.interview_matcher = RequirementMatcher()

    def match(
        self,
        requirement: str,
        cv_skills: List[Dict],
        interview_segments: List[Dict],
        cv_certs: Optional[List[Dict]] = None
    ) -> EnhancedRequirementMatch:
        """
        Match a requirement against CV skills and interview segments.

        Args:
            requirement: The requirement text (e.g., "Azure experience")
            cv_skills: List of skill dicts from candidate_skills table
            interview_segments: List of segment dicts with 'text' field
            cv_certs: Optional list of certification dicts

        Returns:
            EnhancedRequirementMatch with verification status
        """
        # Extract key terms from requirement
        key_terms = self._extract_key_terms(requirement)

        # Check CV for claim
        cv_match, cv_evidence = self._check_cv(key_terms, cv_skills, cv_certs or [])

        # Check interview for demonstration
        interview_result = self.interview_matcher.match(requirement, interview_segments)
        interview_match = interview_result.match_strength
        interview_evidence = interview_result.evidence

        # Determine verification status
        verification_status = self._determine_verification_status(cv_match, interview_match)

        # Calculate confidence
        confidence = self._calculate_confidence(cv_match, interview_match, interview_result.confidence)

        return EnhancedRequirementMatch(
            requirement=requirement,
            cv_match=cv_match,
            interview_match=interview_match,
            verification_status=verification_status,
            cv_evidence=cv_evidence,
            interview_evidence=interview_evidence,
            confidence=confidence
        )

    def match_certification(
        self,
        cert_requirement: str,
        cv_certs: List[Dict],
        interview_segments: List[Dict]
    ) -> EnhancedRequirementMatch:
        """
        Match a certification requirement.

        Args:
            cert_requirement: Certification code (e.g., "AZ-104")
            cv_certs: List of certification dicts from candidate_certifications
            interview_segments: Interview segments

        Returns:
            EnhancedRequirementMatch
        """
        cert_code = cert_requirement.upper()

        # Check CV for cert
        cv_match = "NOT_CLAIMED"
        cv_evidence = []

        for cert in cv_certs:
            if cert.get('cert_code', '').upper() == cert_code:
                cv_match = "CLAIMED"
                cv_evidence.append(f"{cert.get('cert_code')} ({cert.get('issuer', 'Unknown')})")
                break

        # Check interview for mention
        interview_result = self.interview_matcher.match(cert_requirement, interview_segments)

        verification_status = self._determine_verification_status(cv_match, interview_result.match_strength)

        return EnhancedRequirementMatch(
            requirement=cert_requirement,
            cv_match=cv_match,
            interview_match=interview_result.match_strength,
            verification_status=verification_status,
            cv_evidence=cv_evidence,
            interview_evidence=interview_result.evidence,
            confidence=interview_result.confidence if cv_match == "CLAIMED" else 0.5
        )

    def _extract_key_terms(self, requirement: str) -> List[str]:
        """Extract normalized key terms from requirement"""
        # Remove common words
        stop_words = {'experience', 'with', 'in', 'and', 'or', 'the', 'a', 'an',
                      'years', 'year', 'strong', 'good', 'knowledge', 'of', 'skills'}

        words = re.findall(r'\b\w+\b', requirement.lower())
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]

        # Expand with aliases
        expanded = set(key_terms)
        for term in key_terms:
            for base, aliases in self.SKILL_ALIASES.items():
                if term == base or term in aliases:
                    expanded.add(base)
                    expanded.update(aliases)

        return list(expanded)

    def _check_cv(
        self,
        key_terms: List[str],
        cv_skills: List[Dict],
        cv_certs: List[Dict]
    ) -> Tuple[str, List[str]]:
        """Check if requirement is claimed in CV"""
        evidence = []

        # Check skills
        for skill in cv_skills:
            skill_name = skill.get('skill_name', '').lower()
            for term in key_terms:
                if term in skill_name or skill_name in term:
                    evidence.append(f"Skill: {skill.get('skill_name')} ({skill.get('category', 'general')})")
                    break

            # Also check aliases
            for base, aliases in self.SKILL_ALIASES.items():
                if skill_name == base or skill_name in aliases:
                    if base in key_terms or any(a in key_terms for a in aliases):
                        if f"Skill: {skill.get('skill_name')}" not in evidence:
                            evidence.append(f"Skill: {skill.get('skill_name')} ({skill.get('category', 'general')})")

        # Check certs for skill-related terms
        for cert in cv_certs:
            cert_code = cert.get('cert_code', '').lower()
            for term in key_terms:
                if term in cert_code:
                    evidence.append(f"Cert: {cert.get('cert_code')}")

        if evidence:
            return "CLAIMED", evidence
        return "NOT_CLAIMED", []

    def _determine_verification_status(self, cv_match: str, interview_match: str) -> str:
        """Determine verification status from CV and interview results"""
        if cv_match == "CLAIMED":
            if interview_match in ["STRONG", "MODERATE", "WEAK"]:
                # Any interview mention verifies a CV claim (WEAK = mentioned but limited depth)
                return VerificationStatus.VERIFIED.value
            else:
                return VerificationStatus.UNVERIFIED.value
        else:  # NOT_CLAIMED
            if interview_match in ["STRONG", "MODERATE", "WEAK"]:
                return VerificationStatus.BONUS.value
            else:
                return VerificationStatus.NO_MATCH.value

    def _calculate_confidence(self, cv_match: str, interview_match: str, interview_confidence: float) -> float:
        """Calculate overall confidence score"""
        if cv_match == "CLAIMED" and interview_match in ["STRONG", "MODERATE"]:
            # Verified - high confidence
            return min(0.95, interview_confidence + 0.15)
        elif cv_match == "CLAIMED" and interview_match in ["WEAK", "NO_MATCH"]:
            # Unverified - medium confidence (CV claim exists)
            return 0.4
        elif cv_match == "NOT_CLAIMED" and interview_match in ["STRONG", "MODERATE"]:
            # Bonus - good confidence from interview
            return interview_confidence
        else:
            # No match - low confidence
            return 0.1

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_verification_summary(self, matches: List[EnhancedRequirementMatch]) -> Dict[str, Any]:
        """Generate summary of verification results"""
        verified = [m for m in matches if m.verification_status == "VERIFIED"]
        unverified = [m for m in matches if m.verification_status == "UNVERIFIED"]
        bonus = [m for m in matches if m.verification_status == "BONUS"]
        no_match = [m for m in matches if m.verification_status == "NO_MATCH"]

        total_claims = len(verified) + len(unverified)
        alignment_score = (len(verified) / total_claims * 100) if total_claims > 0 else 0

        return {
            "verified_count": len(verified),
            "unverified_count": len(unverified),
            "bonus_count": len(bonus),
            "no_match_count": len(no_match),
            "verified_claims": [m.requirement for m in verified],
            "unverified_claims": [m.requirement for m in unverified],
            "bonus_skills": [m.requirement for m in bonus],
            "alignment_score": round(alignment_score, 1)
        }

    def generate_follow_up_questions(self, matches: List[EnhancedRequirementMatch]) -> List[str]:
        """Generate follow-up questions for unverified claims"""
        questions = []

        for match in matches:
            if match.verification_status == "UNVERIFIED":
                req = match.requirement

                # Generate contextual question
                if "leadership" in req.lower() or "team" in req.lower():
                    questions.append(
                        f"Your CV mentions team leadership - can you describe your team structure and direct reports?"
                    )
                elif "years" in req.lower():
                    questions.append(
                        f"Can you walk me through your experience with {req.split()[0]}? How long have you used it?"
                    )
                else:
                    questions.append(
                        f"Your CV lists '{req}' - can you give me a specific example of using this in a project?"
                    )

        return questions


# =============================================================================
# ENHANCED INTERVIEW ANALYST
# =============================================================================

class EnhancedInterviewAnalyst:
    """
    Interview Analyst with CV integration.

    Extends the standard InterviewAnalyst to use CV data for
    verification and enhanced reporting.
    """

    def __init__(self):
        self.jd_parser = JDParser()
        self.dual_matcher = DualSourceMatcher()
        self.report_generator = FitReportGenerator()

    def analyze_with_cv(
        self,
        jd_text: str,
        cv_data: Dict[str, Any],
        interview_data: Dict[str, Any]
    ) -> EnhancedFitReport:
        """
        Analyze interview with CV data for verification.

        Args:
            jd_text: Job description text
            cv_data: Dict with 'skills' and 'certifications' lists
            interview_data: Dict with 'candidate_name' and 'segments'

        Returns:
            EnhancedFitReport with verification summary
        """
        # Parse JD
        parsed_jd = self.jd_parser.parse(jd_text)

        # Get CV data
        cv_skills = cv_data.get('skills', [])
        cv_certs = cv_data.get('certifications', [])

        # Get interview data
        candidate_name = interview_data.get('candidate_name', 'Unknown')
        segments = interview_data.get('segments', [])

        # Match all requirements with dual-source
        all_requirements = (
            parsed_jd.essential +
            parsed_jd.desirable +
            parsed_jd.nice_to_have
        )

        matches = []
        for requirement in all_requirements:
            match = self.dual_matcher.match(requirement, cv_skills, segments, cv_certs)
            matches.append(match)

        # Generate verification summary
        verification_summary = self.dual_matcher.generate_verification_summary(matches)

        # Generate follow-up questions
        follow_up_questions = self.dual_matcher.generate_follow_up_questions(matches)

        # Generate base fit report (using interview matches)
        base_matches = [
            RequirementMatch(
                requirement=m.requirement,
                match_strength=m.interview_match,
                evidence=m.interview_evidence,
                confidence=m.confidence
            )
            for m in matches
        ]

        base_report = self.report_generator.generate(candidate_name, parsed_jd, base_matches)

        # Create enhanced report
        return EnhancedFitReport(
            candidate_name=base_report.candidate_name,
            role_title=base_report.role_title,
            overall_fit_score=base_report.overall_fit_score,
            breakdown=base_report.breakdown,
            recommendation=base_report.recommendation,
            summary=base_report.summary,
            verification_summary=verification_summary,
            unverified_claims=verification_summary.get('unverified_claims', []),
            bonus_skills=verification_summary.get('bonus_skills', []),
            follow_up_questions=follow_up_questions,
            cv_interview_alignment=verification_summary.get('alignment_score', 0)
        )

    def analyze_by_candidate_name(
        self,
        jd_text: str,
        candidate_name: str,
        interview_id: Optional[str] = None
    ) -> EnhancedFitReport:
        """
        Analyze by candidate name, loading CV and interview from database.

        Args:
            jd_text: Job description text
            candidate_name: Candidate's name
            interview_id: Optional specific interview ID

        Returns:
            EnhancedFitReport
        """
        from claude.tools.interview.cv_parser import CVParser
        from claude.tools.interview.interview_search_system import InterviewSearchSystem

        # Load CV data
        cv_parser = CVParser()
        cv_skills = cv_parser.get_skills(candidate_name)
        cv_certs = cv_parser.get_certifications(candidate_name)

        cv_data = {
            'skills': cv_skills,
            'certifications': cv_certs
        }

        # Load interview data
        interview_system = InterviewSearchSystem()
        conn = interview_system._get_connection()

        try:
            if interview_id:
                cursor = conn.execute(
                    """SELECT i.candidate_name, s.text_content as text
                       FROM interviews i
                       JOIN interview_segments s ON i.interview_id = s.interview_id
                       WHERE i.interview_id = ?""",
                    (interview_id,)
                )
            else:
                cursor = conn.execute(
                    """SELECT i.candidate_name, s.text_content as text
                       FROM interviews i
                       JOIN interview_segments s ON i.interview_id = s.interview_id
                       WHERE i.candidate_name = ?
                       ORDER BY i.interview_date DESC""",
                    (candidate_name,)
                )

            rows = cursor.fetchall()

            if not rows:
                raise ValueError(f"No interview found for candidate: {candidate_name}")

            interview_data = {
                'candidate_name': candidate_name,
                'segments': [{'text': row['text']} for row in rows]
            }

        finally:
            conn.close()

        return self.analyze_with_cv(jd_text, cv_data, interview_data)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for dual-source matcher"""
    import argparse

    parser = argparse.ArgumentParser(description="Dual-Source CV+Interview Matcher")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze candidate with CV verification')
    analyze_parser.add_argument('--candidate', required=True, help='Candidate name')
    analyze_parser.add_argument('--jd', required=True, help='Path to JD file')
    analyze_parser.add_argument('--interview-id', help='Optional specific interview ID')

    args = parser.parse_args()

    if args.command == 'analyze':
        # Read JD
        with open(args.jd, 'r') as f:
            jd_text = f.read()

        analyst = EnhancedInterviewAnalyst()
        report = analyst.analyze_by_candidate_name(jd_text, args.candidate, args.interview_id)

        print(f"\n{'='*60}")
        print(f"ENHANCED FIT REPORT: {report.candidate_name}")
        print(f"{'='*60}")
        print(f"Role: {report.role_title}")
        print(f"Overall Fit Score: {report.overall_fit_score}/100")
        print(f"Recommendation: {report.recommendation}")
        print(f"\n--- CV/Interview Alignment: {report.cv_interview_alignment}% ---")
        print(f"Verified Claims: {report.verification_summary.get('verified_count', 0)}")
        print(f"Unverified Claims: {report.verification_summary.get('unverified_count', 0)}")
        print(f"Bonus Skills: {report.verification_summary.get('bonus_count', 0)}")

        if report.unverified_claims:
            print(f"\nUnverified Claims:")
            for claim in report.unverified_claims:
                print(f"  - {claim}")

        if report.bonus_skills:
            print(f"\nBonus Skills (not on CV):")
            for skill in report.bonus_skills:
                print(f"  - {skill}")

        if report.follow_up_questions:
            print(f"\nSuggested Follow-up Questions:")
            for i, q in enumerate(report.follow_up_questions, 1):
                print(f"  {i}. {q}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
