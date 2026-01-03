#!/usr/bin/env python3
"""
TDD Tests for CV Parser - Phase 1.2
Tests written BEFORE implementation per TDD methodology.

Author: Maia System (SRE Principal Engineer)
Created: 2025-12-16
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class TestCVParserSchema:
    """Test CV schema extension to interview_search.db"""

    def test_candidate_documents_table_exists(self, test_db):
        """Schema should create candidate_documents table"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_documents'"
        )
        assert cursor.fetchone() is not None

    def test_candidate_skills_table_exists(self, test_db):
        """Schema should create candidate_skills table"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_skills'"
        )
        assert cursor.fetchone() is not None

    def test_candidate_certifications_table_exists(self, test_db):
        """Schema should create candidate_certifications table"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_certifications'"
        )
        assert cursor.fetchone() is not None

    def test_candidate_experience_table_exists(self, test_db):
        """Schema should create candidate_experience table"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_experience'"
        )
        assert cursor.fetchone() is not None

    def test_candidate_docs_fts_exists(self, test_db):
        """Schema should create FTS5 virtual table for CV search"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_docs_fts'"
        )
        assert cursor.fetchone() is not None

    def test_v_candidate_profile_view_exists(self, test_db):
        """Schema should create unified candidate profile view"""
        cursor = test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='v_candidate_profile'"
        )
        assert cursor.fetchone() is not None


class TestCVParserDataClasses:
    """Test CV parser data classes"""

    def test_parsed_cv_dataclass(self):
        """ParsedCV should contain all required fields"""
        from claude.tools.interview.cv_parser import ParsedCV

        cv = ParsedCV(
            candidate_name="John Smith",
            contact={"email": "john@example.com"},
            skills=[],
            certifications=[],
            experience=[],
            education=[],
            raw_text="Sample CV text",
            parse_confidence=0.85
        )

        assert cv.candidate_name == "John Smith"
        assert cv.parse_confidence == 0.85

    def test_skill_entry_dataclass(self):
        """SkillEntry should capture skill details"""
        from claude.tools.interview.cv_parser import SkillEntry

        skill = SkillEntry(
            name="azure",
            category="cloud",
            proficiency="expert",
            years=5,
            evidence="5 years Azure experience"
        )

        assert skill.name == "azure"
        assert skill.category == "cloud"
        assert skill.years == 5

    def test_cert_entry_dataclass(self):
        """CertEntry should capture certification details"""
        from claude.tools.interview.cv_parser import CertEntry

        cert = CertEntry(
            code="AZ-104",
            name="Azure Administrator",
            issuer="Microsoft",
            date_obtained="2023-06",
            expiry=None
        )

        assert cert.code == "AZ-104"
        assert cert.issuer == "Microsoft"


class TestCVParserExtraction:
    """Test CV text extraction"""

    def test_extract_text_from_docx(self, sample_cv_path):
        """Should extract text from docx file"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser()
        text = parser.extract_text(sample_cv_path)

        assert isinstance(text, str)
        assert len(text) > 0

    def test_extract_text_handles_missing_file(self):
        """Should raise FileNotFoundError for missing file"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser()

        with pytest.raises(FileNotFoundError):
            parser.extract_text("/nonexistent/file.docx")

    def test_compute_file_hash(self, sample_cv_path):
        """Should compute consistent SHA256 hash"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser()
        hash1 = parser.compute_file_hash(sample_cv_path)
        hash2 = parser.compute_file_hash(sample_cv_path)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestCVParserSkillExtraction:
    """Test skill extraction from CV text"""

    def test_extract_skills_basic(self):
        """Should extract common tech skills"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser()
        text = "Experienced with Azure, Terraform, and Python. 5 years of Kubernetes."

        skills = parser.extract_skills(text)
        skill_names = [s.name for s in skills]

        assert "azure" in skill_names
        assert "terraform" in skill_names
        assert "python" in skill_names

    def test_extract_certifications(self):
        """Should extract certification codes"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser()
        text = "Certifications: AZ-104 (Azure Administrator), AWS-SAA, AZ-305"

        certs = parser.extract_certifications(text)
        cert_codes = [c.code for c in certs]

        assert "AZ-104" in cert_codes
        assert "AZ-305" in cert_codes


class TestCVParserIngestion:
    """Test full CV ingestion pipeline"""

    def test_ingest_cv_creates_record(self, test_db, sample_cv_path):
        """Ingesting CV should create database record"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser(db_path=test_db.path)
        result = parser.ingest(
            cv_path=sample_cv_path,
            candidate_name="Test Candidate",
            role_title="Cloud Engineer"
        )

        assert result["status"] == "success"
        assert "document_id" in result

        # Verify in database
        cursor = test_db.execute(
            "SELECT * FROM candidate_documents WHERE document_id = ?",
            (result["document_id"],)
        )
        row = cursor.fetchone()
        assert row is not None

    def test_ingest_cv_prevents_duplicates(self, test_db, sample_cv_path):
        """Should not create duplicate records for same CV"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser(db_path=test_db.path)

        result1 = parser.ingest(sample_cv_path, "Test Candidate", "Role")
        result2 = parser.ingest(sample_cv_path, "Test Candidate", "Role")

        assert result1["document_id"] == result2["document_id"]
        assert result2["status"] == "exists"


class TestCVParserSearch:
    """Test CV search capabilities"""

    def test_fts_search_cv_content(self, test_db_with_cv):
        """Should find CV via full-text search"""
        from claude.tools.interview.cv_parser import CVParser

        parser = CVParser(db_path=test_db_with_cv.path)
        results = parser.search("azure terraform")

        assert len(results) > 0
        assert results[0]["candidate_name"] == "Test Candidate"


# Fixtures

class _TestDB:
    """Wrapper for test database connection with path attribute"""
    def __init__(self, path: str):
        self.path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        return self._conn.executescript(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()


@pytest.fixture
def test_db():
    """Create test database with CV schema"""
    from claude.tools.interview.cv_parser import CV_SCHEMA

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = _TestDB(db_path)
    db.executescript(CV_SCHEMA)
    db.commit()

    yield db

    db.close()
    os.unlink(db_path)


@pytest.fixture
def sample_cv_path():
    """Path to a sample CV for testing"""
    # Check for CV path via environment variable (portable)
    cv_path = os.environ.get("TEST_CV_PATH")
    if cv_path and os.path.exists(cv_path):
        return cv_path

    # Fallback: create a temp text file for basic testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("John Smith\nAzure, Terraform, Python\nAZ-104 certified\n5 years experience")
        return f.name


@pytest.fixture
def test_db_with_cv(test_db, sample_cv_path):
    """Test database with a CV already ingested"""
    from claude.tools.interview.cv_parser import CVParser

    parser = CVParser(db_path=test_db.path)
    parser.ingest(sample_cv_path, "Test Candidate", "Cloud Engineer")

    return test_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
