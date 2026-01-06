#!/usr/bin/env python3
"""
TDD Tests for Dual-Source Matcher - Phase 2
Tests CV + Interview verification matching.

Author: Maia System (SRE Principal Engineer + Interview Analyst)
Created: 2025-12-16
"""

import pytest
import os
import sys
from pathlib import Path
from typing import List, Dict

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class TestEnhancedDataClasses:
    """Test enhanced data classes for dual-source matching"""

    def test_enhanced_requirement_match_dataclass(self):
        """EnhancedRequirementMatch should contain CV and interview fields"""
        from claude.tools.interview.dual_source_matcher import EnhancedRequirementMatch

        match = EnhancedRequirementMatch(
            requirement="Azure experience",
            cv_match="CLAIMED",
            interview_match="STRONG",
            verification_status="VERIFIED",
            cv_evidence=["5 years Azure experience"],
            interview_evidence=["I've worked with Azure for about 5 years..."],
            confidence=0.9
        )

        assert match.cv_match == "CLAIMED"
        assert match.interview_match == "STRONG"
        assert match.verification_status == "VERIFIED"

    def test_verification_status_enum(self):
        """VerificationStatus should have correct values"""
        from claude.tools.interview.dual_source_matcher import VerificationStatus

        assert VerificationStatus.VERIFIED.value == "VERIFIED"
        assert VerificationStatus.UNVERIFIED.value == "UNVERIFIED"
        assert VerificationStatus.BONUS.value == "BONUS"
        assert VerificationStatus.NO_MATCH.value == "NO_MATCH"


class TestDualSourceMatcher:
    """Test dual-source matching logic"""

    def test_verified_status_cv_claimed_interview_strong(self):
        """CV CLAIMED + Interview STRONG = VERIFIED"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher

        matcher = DualSourceMatcher()

        cv_skills = [{"skill_name": "azure", "category": "cloud"}]
        interview_segments = [
            {"text": "I've been working with Azure for 5 years, primarily on infrastructure."},
            {"text": "My Azure experience includes VNets, Load Balancers, and AKS."}
        ]

        result = matcher.match("Azure experience", cv_skills, interview_segments)

        assert result.cv_match == "CLAIMED"
        assert result.interview_match in ["STRONG", "MODERATE"]
        assert result.verification_status == "VERIFIED"

    def test_unverified_status_cv_claimed_interview_no_match(self):
        """CV CLAIMED + Interview NO_MATCH = UNVERIFIED"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher

        matcher = DualSourceMatcher()

        cv_skills = [{"skill_name": "terraform", "category": "iac"}]
        interview_segments = [
            {"text": "I mostly work with Azure portal for deployments."},
            {"text": "We use manual processes for infrastructure."}
        ]

        result = matcher.match("Terraform experience", cv_skills, interview_segments)

        assert result.cv_match == "CLAIMED"
        assert result.interview_match == "NO_MATCH"
        assert result.verification_status == "UNVERIFIED"

    def test_bonus_status_cv_not_claimed_interview_demonstrated(self):
        """CV NOT_CLAIMED + Interview DEMONSTRATED = BONUS"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher

        matcher = DualSourceMatcher()

        cv_skills = [{"skill_name": "azure", "category": "cloud"}]  # No kubernetes
        interview_segments = [
            {"text": "I've also been learning Kubernetes recently."},
            {"text": "I deployed a few AKS clusters and really enjoyed working with k8s."}
        ]

        result = matcher.match("Kubernetes experience", cv_skills, interview_segments)

        assert result.cv_match == "NOT_CLAIMED"
        assert result.interview_match in ["STRONG", "MODERATE", "WEAK"]
        assert result.verification_status == "BONUS"

    def test_no_match_status_neither_cv_nor_interview(self):
        """CV NOT_CLAIMED + Interview NO_MATCH = NO_MATCH"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher

        matcher = DualSourceMatcher()

        cv_skills = [{"skill_name": "azure", "category": "cloud"}]
        interview_segments = [
            {"text": "I work with Windows servers mostly."},
        ]

        result = matcher.match("GCP experience", cv_skills, interview_segments)

        assert result.cv_match == "NOT_CLAIMED"
        assert result.interview_match == "NO_MATCH"
        assert result.verification_status == "NO_MATCH"

    def test_certification_matching(self):
        """Should match certifications from CV"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher

        matcher = DualSourceMatcher()

        cv_certs = [{"cert_code": "AZ-104", "issuer": "Microsoft"}]
        interview_segments = [
            {"text": "I passed my AZ-104 last year."},
        ]

        result = matcher.match_certification("AZ-104", cv_certs, interview_segments)

        assert result.cv_match == "CLAIMED"
        assert result.verification_status == "VERIFIED"


class TestVerificationReport:
    """Test verification report generation"""

    def test_generate_verification_summary(self):
        """Should generate summary of verified/unverified claims"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher, EnhancedRequirementMatch

        matcher = DualSourceMatcher()

        matches = [
            EnhancedRequirementMatch(
                requirement="Azure",
                cv_match="CLAIMED",
                interview_match="STRONG",
                verification_status="VERIFIED",
                cv_evidence=["Azure expert"],
                interview_evidence=["5 years Azure"],
                confidence=0.9
            ),
            EnhancedRequirementMatch(
                requirement="Terraform",
                cv_match="CLAIMED",
                interview_match="NO_MATCH",
                verification_status="UNVERIFIED",
                cv_evidence=["Terraform listed"],
                interview_evidence=[],
                confidence=0.3
            ),
        ]

        summary = matcher.generate_verification_summary(matches)

        assert summary["verified_count"] == 1
        assert summary["unverified_count"] == 1
        assert "Terraform" in summary["unverified_claims"]
        assert summary["alignment_score"] == 50.0  # 1/2 = 50%

    def test_generate_follow_up_questions(self):
        """Should generate follow-up questions for unverified claims"""
        from claude.tools.interview.dual_source_matcher import DualSourceMatcher, EnhancedRequirementMatch

        matcher = DualSourceMatcher()

        matches = [
            EnhancedRequirementMatch(
                requirement="Team leadership (5+ direct reports)",
                cv_match="CLAIMED",
                interview_match="NO_MATCH",
                verification_status="UNVERIFIED",
                cv_evidence=["Led team of 8"],
                interview_evidence=[],
                confidence=0.3
            ),
        ]

        questions = matcher.generate_follow_up_questions(matches)

        assert len(questions) > 0
        assert "leadership" in questions[0].lower() or "team" in questions[0].lower()


class TestIntegrationWithInterviewAnalyst:
    """Test integration with existing InterviewAnalyst"""

    def test_analyze_with_cv_data(self):
        """Should use CV data when available"""
        from claude.tools.interview.dual_source_matcher import EnhancedInterviewAnalyst

        analyst = EnhancedInterviewAnalyst()

        jd_text = """
        Cloud Engineer

        Essential:
        - Azure experience
        - Terraform skills

        Desirable:
        - Kubernetes
        """

        cv_data = {
            "skills": [
                {"skill_name": "azure", "category": "cloud"},
                {"skill_name": "terraform", "category": "iac"}
            ],
            "certifications": []
        }

        interview_data = {
            "candidate_name": "Test Candidate",
            "segments": [
                {"text": "I've worked with Azure for several years."},
                {"text": "We used Terraform but I prefer ARM templates."}
            ]
        }

        report = analyst.analyze_with_cv(jd_text, cv_data, interview_data)

        assert report.candidate_name == "Test Candidate"
        assert hasattr(report, 'verification_summary')
        assert report.verification_summary["verified_count"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
