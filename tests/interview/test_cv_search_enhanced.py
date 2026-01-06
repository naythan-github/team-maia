#!/usr/bin/env python3
"""
TDD Tests for Enhanced CV Search - Optional Enhancements
Tests ChromaDB search, pre-interview questions, bulk comparison.

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


class TestPreInterviewQuestionGenerator:
    """Test pre-interview question generation"""

    def test_generate_returns_questions_object(self):
        """Should return PreInterviewQuestions dataclass"""
        from claude.tools.interview.cv_search_enhanced import PreInterviewQuestionGenerator

        generator = PreInterviewQuestionGenerator()

        jd_text = """
        Cloud Engineer

        Essential:
        - Azure experience
        - Terraform skills
        """

        questions = generator.generate(jd_text, "Amritpal Singh Sohal")

        assert questions.candidate_name == "Amritpal Singh Sohal"
        assert questions.role_title == "Cloud Engineer"

    def test_generates_skill_verification_questions(self):
        """Should generate skill verification questions from CV"""
        from claude.tools.interview.cv_search_enhanced import PreInterviewQuestionGenerator

        generator = PreInterviewQuestionGenerator()

        jd_text = "Cloud Engineer\nEssential:\n- Azure"
        questions = generator.generate(jd_text, "Amritpal Singh Sohal")

        assert len(questions.skill_verification_questions) > 0

    def test_generates_gap_probing_questions(self):
        """Should generate questions for JD requirements not on CV"""
        from claude.tools.interview.cv_search_enhanced import PreInterviewQuestionGenerator

        generator = PreInterviewQuestionGenerator()

        jd_text = """
        Cloud Engineer

        Essential:
        - Exotic technology XYZ
        - Rare framework ABC
        """

        questions = generator.generate(jd_text, "Amritpal Singh Sohal")

        # Should have gap questions since these skills aren't on CV
        assert len(questions.gap_probing_questions) > 0

    def test_generates_certification_questions(self):
        """Should generate cert questions if candidate has certs"""
        from claude.tools.interview.cv_search_enhanced import PreInterviewQuestionGenerator

        generator = PreInterviewQuestionGenerator()

        jd_text = "Cloud Engineer\nEssential:\n- Azure certs"
        questions = generator.generate(jd_text, "Manikrishna Suddala")  # Has AZ-104

        # Manikrishna has certs, should have cert questions
        assert len(questions.certification_questions) > 0


class TestBulkCandidateComparator:
    """Test bulk candidate comparison"""

    def test_compare_returns_report(self):
        """Should return BulkComparisonReport"""
        from claude.tools.interview.cv_search_enhanced import BulkCandidateComparator

        comparator = BulkCandidateComparator()

        jd_text = """
        Associate Cloud Engineer

        Essential:
        - Azure experience
        - PowerShell scripting
        """

        candidates = ["Amritpal Singh Sohal", "Mamta Sharma"]
        report = comparator.compare(jd_text, candidates)

        assert report.role_title == "Associate Cloud Engineer"
        assert len(report.candidates) == 2
        assert report.top_candidate in candidates

    def test_candidates_ranked_by_score(self):
        """Should rank candidates by overall score descending"""
        from claude.tools.interview.cv_search_enhanced import BulkCandidateComparator

        comparator = BulkCandidateComparator()

        jd_text = "Cloud Engineer\nEssential:\n- Azure\n- Terraform"
        candidates = ["Amritpal Singh Sohal", "Mamta Sharma", "Manikrishna Suddala"]

        report = comparator.compare(jd_text, candidates)

        # Should be sorted by score descending
        scores = [c.overall_score for c in report.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_comparison_matrix_generated(self):
        """Should generate comparison matrix dict"""
        from claude.tools.interview.cv_search_enhanced import BulkCandidateComparator

        comparator = BulkCandidateComparator()

        jd_text = "Cloud Engineer\nEssential:\n- Azure"
        candidates = ["Amritpal Singh Sohal", "Mamta Sharma"]

        report = comparator.compare(jd_text, candidates)

        assert "Amritpal Singh Sohal" in report.comparison_matrix
        assert "score" in report.comparison_matrix["Amritpal Singh Sohal"]

    def test_generate_comparison_table_markdown(self):
        """Should generate markdown table"""
        from claude.tools.interview.cv_search_enhanced import BulkCandidateComparator

        comparator = BulkCandidateComparator()

        jd_text = "Cloud Engineer\nEssential:\n- Azure"
        candidates = ["Amritpal Singh Sohal"]

        report = comparator.compare(jd_text, candidates)
        table = comparator.generate_comparison_table(report)

        assert "## Candidate Comparison" in table
        assert "Amritpal Singh Sohal" in table
        assert "|" in table  # Table formatting


class TestEnhancedCVSearch:
    """Test ChromaDB semantic search (when available)"""

    def test_search_instance_creation(self):
        """Should create EnhancedCVSearch instance"""
        from claude.tools.interview.cv_search_enhanced import EnhancedCVSearch

        search = EnhancedCVSearch()
        assert search is not None

    def test_chunk_text_splits_correctly(self):
        """Should chunk text with overlap"""
        from claude.tools.interview.cv_search_enhanced import EnhancedCVSearch

        search = EnhancedCVSearch()

        text = "A" * 5000  # 5000 chars
        chunks = search._chunk_text(text, chunk_size=2000, overlap=200)

        assert len(chunks) >= 2
        # First chunk should be ~2000 chars
        assert len(chunks[0]) <= 2100

    def test_get_stats(self):
        """Should return stats dict"""
        from claude.tools.interview.cv_search_enhanced import EnhancedCVSearch

        search = EnhancedCVSearch()
        stats = search.get_stats()

        assert "chromadb_available" in stats
        assert "chroma_path" in stats


class TestDataClasses:
    """Test data class structures"""

    def test_cv_search_result_dataclass(self):
        """CVSearchResult should have correct fields"""
        from claude.tools.interview.cv_search_enhanced import CVSearchResult

        result = CVSearchResult(
            document_id="test-123",
            candidate_name="Test",
            chunk_text="Sample text",
            relevance_score=0.85
        )

        assert result.document_id == "test-123"
        assert result.relevance_score == 0.85

    def test_pre_interview_questions_dataclass(self):
        """PreInterviewQuestions should have all question categories"""
        from claude.tools.interview.cv_search_enhanced import PreInterviewQuestions

        questions = PreInterviewQuestions(
            candidate_name="Test",
            role_title="Engineer",
            skill_verification_questions=["Q1"],
            experience_depth_questions=["Q2"],
            gap_probing_questions=["Q3"],
            certification_questions=["Q4"],
            general_questions=["Q5"]
        )

        assert len(questions.skill_verification_questions) == 1
        assert len(questions.general_questions) == 1

    def test_candidate_comparison_dataclass(self):
        """CandidateComparison should have score fields"""
        from claude.tools.interview.cv_search_enhanced import CandidateComparison

        comp = CandidateComparison(
            candidate_name="Test",
            overall_score=75.5,
            cv_skills_count=10,
            cv_certs_count=2,
            jd_match_percentage=80.0,
            strengths=["Azure"],
            gaps=["Terraform"],
            recommendation="HIRE"
        )

        assert comp.overall_score == 75.5
        assert comp.recommendation == "HIRE"

    def test_bulk_comparison_report_dataclass(self):
        """BulkComparisonReport should contain candidates list"""
        from claude.tools.interview.cv_search_enhanced import BulkComparisonReport, CandidateComparison

        report = BulkComparisonReport(
            role_title="Engineer",
            candidates=[],
            top_candidate="Test",
            comparison_matrix={},
            generated_at="2025-12-16"
        )

        assert report.role_title == "Engineer"
        assert report.top_candidate == "Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
