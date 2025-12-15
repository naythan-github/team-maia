#!/usr/bin/env python3
"""
TDD Tests for Interview Analyst - JD Matching System

Tests written FIRST, implementation follows.
Phase 223.2: Interview Analyst Agent
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class TestJDParser:
    """Test JD parsing into structured requirements"""

    def test_parse_jd_text_extracts_requirements(self):
        """JD text should be parsed into categorized requirements"""
        from claude.tools.interview.interview_analyst import JDParser

        jd_text = """
        Cloud Hybrid Pod Lead

        Essential Requirements:
        - 5+ years Azure experience
        - Strong Terraform/IaC skills
        - Team leadership experience

        Desirable:
        - Kubernetes experience
        - Multi-cloud (AWS/GCP)

        Nice to Have:
        - Azure certifications (AZ-305, AZ-104)
        """

        parser = JDParser()
        result = parser.parse(jd_text)

        assert result.role_title == "Cloud Hybrid Pod Lead"
        assert len(result.essential) >= 3
        assert len(result.desirable) >= 1
        assert len(result.nice_to_have) >= 1
        assert "azure" in result.essential[0].lower()

    def test_parse_jd_handles_bullet_formats(self):
        """Parser should handle various bullet point formats"""
        from claude.tools.interview.interview_analyst import JDParser

        jd_text = """
        Role: Senior Engineer

        Requirements:
        • Python programming
        * Docker containers
        - CI/CD pipelines
        """

        parser = JDParser()
        result = parser.parse(jd_text)

        assert len(result.essential) >= 3

    def test_parse_jd_empty_returns_empty_requirements(self):
        """Empty JD should return empty requirements"""
        from claude.tools.interview.interview_analyst import JDParser

        parser = JDParser()
        result = parser.parse("")

        assert result.essential == []
        assert result.desirable == []
        assert result.nice_to_have == []


class TestRequirementMatcher:
    """Test matching requirements against interview content"""

    def test_match_finds_evidence_for_requirement(self):
        """Matcher should find relevant interview segments for a requirement"""
        from claude.tools.interview.interview_analyst import RequirementMatcher

        matcher = RequirementMatcher()

        # Mock interview search results
        interview_segments = [
            {"speaker": "Candidate", "text": "I have 8 years of Azure experience including AKS and Functions"},
            {"speaker": "Candidate", "text": "I led a team of 5 engineers for 3 years"},
        ]

        requirement = "5+ years Azure experience"
        result = matcher.match(requirement, interview_segments)

        assert result.requirement == requirement
        assert result.match_strength in ["STRONG", "MODERATE", "WEAK", "NO_MATCH"]
        assert len(result.evidence) > 0

    def test_match_returns_no_match_when_not_found(self):
        """Matcher should return NO_MATCH when requirement not evidenced"""
        from claude.tools.interview.interview_analyst import RequirementMatcher

        matcher = RequirementMatcher()

        interview_segments = [
            {"speaker": "Candidate", "text": "I work with databases and SQL"},
        ]

        requirement = "Kubernetes orchestration experience"
        result = matcher.match(requirement, interview_segments)

        assert result.match_strength == "NO_MATCH"

    def test_match_with_semantic_search(self):
        """Matcher should use semantic search for nuanced matching"""
        from claude.tools.interview.interview_analyst import RequirementMatcher

        matcher = RequirementMatcher()

        # "container orchestration" should semantically match "Kubernetes"
        interview_segments = [
            {"speaker": "Candidate", "text": "I manage container orchestration using k8s clusters"},
        ]

        requirement = "Kubernetes experience"
        result = matcher.match(requirement, interview_segments)

        assert result.match_strength in ["STRONG", "MODERATE"]


class TestFitReportGenerator:
    """Test fit report generation"""

    def test_generate_report_structure(self):
        """Report should have proper structure"""
        from claude.tools.interview.interview_analyst import (
            FitReportGenerator, ParsedJD, RequirementMatch
        )

        generator = FitReportGenerator()

        parsed_jd = ParsedJD(
            role_title="Cloud Engineer",
            essential=["Azure experience", "Terraform skills"],
            desirable=["Kubernetes"],
            nice_to_have=["Certifications"]
        )

        matches = [
            RequirementMatch(requirement="Azure experience", match_strength="STRONG",
                           evidence=["8 years Azure..."], confidence=0.9),
            RequirementMatch(requirement="Terraform skills", match_strength="MODERATE",
                           evidence=["Used terraform..."], confidence=0.7),
        ]

        report = generator.generate(
            candidate_name="John Smith",
            parsed_jd=parsed_jd,
            matches=matches
        )

        assert report.candidate_name == "John Smith"
        assert report.role_title == "Cloud Engineer"
        assert report.overall_fit_score > 0
        assert report.overall_fit_score <= 100
        assert "essential_results" in report.breakdown

    def test_generate_report_calculates_weighted_score(self):
        """Score should weight essential > desirable > nice_to_have"""
        from claude.tools.interview.interview_analyst import (
            FitReportGenerator, ParsedJD, RequirementMatch
        )

        generator = FitReportGenerator()

        # All STRONG matches
        parsed_jd = ParsedJD(
            role_title="Engineer",
            essential=["Req1"],
            desirable=["Req2"],
            nice_to_have=["Req3"]
        )

        all_strong = [
            RequirementMatch(requirement="Req1", match_strength="STRONG", evidence=["..."], confidence=0.9),
            RequirementMatch(requirement="Req2", match_strength="STRONG", evidence=["..."], confidence=0.9),
            RequirementMatch(requirement="Req3", match_strength="STRONG", evidence=["..."], confidence=0.9),
        ]

        report = generator.generate("Candidate", parsed_jd, all_strong)
        assert report.overall_fit_score >= 85  # High score for all strong

    def test_generate_recommendation(self):
        """Report should include hire recommendation"""
        from claude.tools.interview.interview_analyst import (
            FitReportGenerator, ParsedJD, RequirementMatch
        )

        generator = FitReportGenerator()

        parsed_jd = ParsedJD(role_title="Engineer", essential=["Req1"], desirable=[], nice_to_have=[])

        strong_match = [
            RequirementMatch(requirement="Req1", match_strength="STRONG", evidence=["..."], confidence=0.9)
        ]

        report = generator.generate("Candidate", parsed_jd, strong_match)
        assert report.recommendation in ["STRONG_HIRE", "HIRE", "CONSIDER", "DO_NOT_HIRE"]


class TestInterviewAnalyst:
    """Integration tests for full analyst workflow"""

    def test_analyze_interview_against_jd(self):
        """Full workflow: JD + Interview → Fit Report"""
        from claude.tools.interview.interview_analyst import InterviewAnalyst

        analyst = InterviewAnalyst()

        jd_text = """
        Cloud Engineer

        Essential:
        - Azure experience
        - Terraform skills

        Desirable:
        - Kubernetes
        """

        # Mock interview data
        interview_data = {
            "candidate_name": "Test Candidate",
            "segments": [
                {"speaker": "Test Candidate", "text": "I have 5 years Azure and Terraform experience"},
            ]
        }

        report = analyst.analyze(jd_text, interview_data)

        assert report.candidate_name == "Test Candidate"
        assert report.role_title == "Cloud Engineer"
        assert report.overall_fit_score > 0

    def test_analyze_with_interview_id(self):
        """Analyst should fetch interview from database by ID"""
        from claude.tools.interview.interview_analyst import InterviewAnalyst

        analyst = InterviewAnalyst()

        jd_text = "Cloud Engineer\nEssential: Azure"

        # This should work with a real interview ID from the database
        # For TDD, we test the interface exists
        assert hasattr(analyst, 'analyze_by_interview_id')

    def test_compare_multiple_candidates(self):
        """Analyst should compare multiple candidates against same JD"""
        from claude.tools.interview.interview_analyst import InterviewAnalyst

        analyst = InterviewAnalyst()

        jd_text = "Engineer\nEssential: Python"

        interviews = [
            {"candidate_name": "Alice", "segments": [{"speaker": "Alice", "text": "Python expert"}]},
            {"candidate_name": "Bob", "segments": [{"speaker": "Bob", "text": "Java developer"}]},
        ]

        comparison = analyst.compare(jd_text, interviews)

        assert len(comparison.rankings) == 2
        assert comparison.rankings[0].candidate_name in ["Alice", "Bob"]


class TestDataClasses:
    """Test data class structures"""

    def test_parsed_jd_dataclass(self):
        """ParsedJD should have correct fields"""
        from claude.tools.interview.interview_analyst import ParsedJD

        jd = ParsedJD(
            role_title="Engineer",
            essential=["req1"],
            desirable=["req2"],
            nice_to_have=["req3"]
        )

        assert jd.role_title == "Engineer"
        assert jd.essential == ["req1"]

    def test_requirement_match_dataclass(self):
        """RequirementMatch should have correct fields"""
        from claude.tools.interview.interview_analyst import RequirementMatch

        match = RequirementMatch(
            requirement="Test",
            match_strength="STRONG",
            evidence=["evidence text"],
            confidence=0.85
        )

        assert match.requirement == "Test"
        assert match.match_strength == "STRONG"
        assert match.confidence == 0.85

    def test_fit_report_dataclass(self):
        """FitReport should have correct fields"""
        from claude.tools.interview.interview_analyst import FitReport

        report = FitReport(
            candidate_name="John",
            role_title="Engineer",
            overall_fit_score=75,
            breakdown={"essential_results": []},
            recommendation="CONSIDER",
            summary="Good fit overall"
        )

        assert report.candidate_name == "John"
        assert report.overall_fit_score == 75
