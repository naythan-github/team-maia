#!/usr/bin/env python3
"""
TDD Tests for Requirement-by-Requirement Matcher
Tests written BEFORE implementation per TDD methodology.

Author: Maia System (SRE Principal Engineer)
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


class TestSkillSynonyms:
    """Test skill synonym/taxonomy matching"""

    def test_synonym_dictionary_exists(self):
        """Should have a skill synonyms dictionary"""
        from claude.tools.interview.requirement_matcher import SKILL_SYNONYMS

        assert isinstance(SKILL_SYNONYMS, dict)
        assert len(SKILL_SYNONYMS) > 0

    def test_entra_id_synonyms(self):
        """Entra ID should match Azure AD, AAD"""
        from claude.tools.interview.requirement_matcher import SKILL_SYNONYMS

        assert "entra id" in SKILL_SYNONYMS
        assert "azure ad" in SKILL_SYNONYMS["entra id"]
        assert "aad" in SKILL_SYNONYMS["entra id"]

    def test_kubernetes_synonyms(self):
        """Kubernetes should match k8s, aks, eks"""
        from claude.tools.interview.requirement_matcher import SKILL_SYNONYMS

        assert "kubernetes" in SKILL_SYNONYMS
        assert "k8s" in SKILL_SYNONYMS["kubernetes"]

    def test_normalize_skill_with_synonym(self):
        """Should normalize synonyms to canonical form"""
        from claude.tools.interview.requirement_matcher import normalize_skill

        assert normalize_skill("azure ad") == "entra id"
        assert normalize_skill("aad") == "entra id"
        assert normalize_skill("k8s") == "kubernetes"
        assert normalize_skill("azure") == "azure"  # No change if not a synonym


class TestRequirementMatchDataclass:
    """Test RequirementMatch dataclass"""

    def test_requirement_match_fields(self):
        """RequirementMatch should have required fields"""
        from claude.tools.interview.requirement_matcher import RequirementMatch

        match = RequirementMatch(
            requirement_text="Azure experience required",
            requirement_type="essential",
            match_status="STRONG",
            score=85,
            evidence=["5 years Azure infrastructure"],
            matched_skills=["azure"]
        )

        assert match.requirement_text == "Azure experience required"
        assert match.requirement_type == "essential"
        assert match.match_status == "STRONG"
        assert match.score == 85
        assert len(match.evidence) == 1

    def test_match_status_values(self):
        """Match status should be STRONG, MODERATE, WEAK, or NOT_FOUND"""
        from claude.tools.interview.requirement_matcher import MatchStatus

        assert MatchStatus.STRONG.value == "STRONG"
        assert MatchStatus.MODERATE.value == "MODERATE"
        assert MatchStatus.WEAK.value == "WEAK"
        assert MatchStatus.NOT_FOUND.value == "NOT_FOUND"


class TestRequirementMatcher:
    """Test RequirementMatcher class"""

    def test_matcher_initialization(self):
        """Should create RequirementMatcher instance"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()
        assert matcher is not None

    def test_match_single_requirement_strong(self):
        """Should return STRONG match when skill directly mentioned with substantial evidence"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        requirement = "Azure cloud platform experience"
        # Rich CV with multiple Azure mentions for STRONG match
        cv_text = """
        5 years experience with Microsoft Azure, including VNets, Load Balancers, and AKS deployments.
        Led Azure migration project for 50+ VMs. Certified Azure Administrator (AZ-104).
        Deep expertise in Azure networking, Azure security, and Azure DevOps pipelines.
        """

        result = matcher.match_requirement(requirement, cv_text)

        assert result.match_status == "STRONG"
        assert result.score >= 70
        assert "azure" in [s.lower() for s in result.matched_skills]

    def test_match_single_requirement_moderate(self):
        """Should return MODERATE when skill mentioned but less evidence"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        requirement = "Terraform IaC experience"
        cv_text = "Familiar with Terraform basics. Mainly worked with ARM templates."

        result = matcher.match_requirement(requirement, cv_text)

        assert result.match_status in ["MODERATE", "WEAK"]
        assert result.score >= 30

    def test_match_single_requirement_not_found(self):
        """Should return NOT_FOUND when skill not present"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        requirement = "GCP cloud platform experience"
        cv_text = "5 years experience with Microsoft Azure."

        result = matcher.match_requirement(requirement, cv_text)

        assert result.match_status == "NOT_FOUND"
        assert result.score == 0

    def test_match_with_synonym(self):
        """Should match using synonym (Azure AD -> Entra ID)"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        requirement = "Microsoft Entra ID administration"
        cv_text = "Experienced with Azure AD user management and conditional access policies."

        result = matcher.match_requirement(requirement, cv_text)

        assert result.match_status in ["STRONG", "MODERATE"]
        assert result.score >= 50


class TestWeightedScoring:
    """Test weighted scoring for essential vs desirable"""

    def test_essential_weight_multiplier(self):
        """Essential requirements should have 3x weight"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        # Same match, different weights
        essential_match = matcher.match_requirement(
            "Azure experience",
            "5 years Azure",
            requirement_type="essential"
        )
        desirable_match = matcher.match_requirement(
            "Azure experience",
            "5 years Azure",
            requirement_type="desirable"
        )

        assert essential_match.weighted_score == essential_match.score * 3
        assert desirable_match.weighted_score == desirable_match.score * 1

    def test_calculate_overall_score_with_weights(self):
        """Overall score should account for weights"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher, RequirementMatch

        matcher = RequirementMatcher()

        matches = [
            RequirementMatch(
                requirement_text="Azure",
                requirement_type="essential",
                match_status="STRONG",
                score=100,
                weighted_score=300,  # 100 * 3
                evidence=[],
                matched_skills=[]
            ),
            RequirementMatch(
                requirement_text="Python",
                requirement_type="desirable",
                match_status="STRONG",
                score=100,
                weighted_score=100,  # 100 * 1
                evidence=[],
                matched_skills=[]
            ),
        ]

        # Max possible: 300 + 100 = 400
        # Actual: 300 + 100 = 400
        # Score: 100%
        overall = matcher.calculate_overall_score(matches)
        assert overall == 100.0


class TestFullCVMatching:
    """Test matching full CV against JD requirements"""

    def test_match_cv_against_jd(self):
        """Should return list of RequirementMatch for all JD requirements"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        jd_requirements = [
            {"text": "Azure cloud experience", "type": "essential"},
            {"text": "PowerShell scripting", "type": "essential"},
            {"text": "Kubernetes experience", "type": "desirable"},
        ]

        cv_text = """
        Cloud Engineer with 5 years Azure experience.
        Expert in PowerShell automation and scripting.
        Basic understanding of container orchestration.
        """

        results = matcher.match_all_requirements(jd_requirements, cv_text)

        assert len(results) == 3
        assert results[0].requirement_text == "Azure cloud experience"
        assert results[0].match_status in ["STRONG", "MODERATE"]

    def test_generate_requirement_breakdown_report(self):
        """Should generate markdown report with requirement breakdown"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher

        matcher = RequirementMatcher()

        jd_requirements = [
            {"text": "Azure experience", "type": "essential"},
            {"text": "Python skills", "type": "desirable"},
        ]

        cv_text = "5 years Azure, Python developer background."

        results = matcher.match_all_requirements(jd_requirements, cv_text)
        report = matcher.generate_breakdown_report(results, "Test Candidate")

        assert "Test Candidate" in report
        assert "Azure experience" in report
        assert "✅" in report or "⚠️" in report or "❌" in report  # Status icons


class TestIntegrationWithExistingSystem:
    """Test integration with existing cv_parser and cv_search_enhanced"""

    def test_match_using_parsed_jd(self):
        """Should work with ParsedJD from cv_parser"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher
        from claude.tools.interview.cv_parser import CVParser

        matcher = RequirementMatcher()
        parser = CVParser()

        # Get a real JD
        jd = parser.get_jd("Associate Cloud Engineer")
        if jd is None:
            pytest.skip("No JD in database")

        requirements = parser.get_jd_requirements(jd['jd_id'])

        cv_text = "Azure engineer with PowerShell and Terraform skills."

        jd_reqs = [{"text": r['requirement_text'], "type": r['requirement_type']} for r in requirements]
        results = matcher.match_all_requirements(jd_reqs[:5], cv_text)  # First 5 requirements

        assert len(results) > 0
        assert all(hasattr(r, 'match_status') for r in results)

    def test_match_using_candidate_cv(self):
        """Should work with CV text from database"""
        from claude.tools.interview.requirement_matcher import RequirementMatcher
        from claude.tools.interview.cv_parser import CVParser
        import sqlite3

        matcher = RequirementMatcher()
        parser = CVParser()

        # Get CV text for a candidate
        conn = sqlite3.connect(parser.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT content_text FROM candidate_documents WHERE candidate_name LIKE '%Amritpal%' LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            pytest.skip("No CV in database")

        cv_text = row['content_text']
        requirement = "Azure cloud platform experience"

        result = matcher.match_requirement(requirement, cv_text)

        assert result.match_status in ["STRONG", "MODERATE", "WEAK", "NOT_FOUND"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
