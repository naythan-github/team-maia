#!/usr/bin/env python3
"""
TDD Tests for EvidenceManifest Parser

Priority 2: Chain of custody metadata + SHA256 verification
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude.tools.m365_ir.m365_log_parser import (
    M365LogParser,
    LogType,
    LOG_FILE_PATTERNS,
)


# Sample manifest JSON (UTF-8 for testing - real files are UTF-16 LE)
SAMPLE_MANIFEST_JSON = {
    "InvestigationId": "56561ac7-c1ee-47f2-bdc2-d2e08405bb5b",
    "CollectionVersion": "2.1.0-Production",
    "CollectedAt": "2026-01-08T09:39:46.0388264+08:00",
    "CollectedBy": "ORROAD\\alex.olver",
    "CollectedOn": "ORRO6JV924173GT",
    "DateRangeStart": "2025-10-10T08:38:39.8932316+08:00",
    "DateRangeEnd": "2026-01-08T08:38:39.8932316+08:00",
    "DaysBack": 90,
    "Files": [
        {
            "FileName": "01_SignInLogs.csv",
            "SHA256": "78AFCF2AEEC45729FB601C1308BA08ABEEE84828C6D0EB3187E4665AEBF058F0",
            "Size": 1316519,
            "Records": 3201
        },
        {
            "FileName": "13_TransportRules.csv",
            "SHA256": "B3C43ED97CB56DFA7D6A5B667A6C79A1143766FC8A",
            "Size": 1963,
            "Records": 8
        }
    ]
}


class TestLogTypeEnum:
    """Test that EVIDENCE_MANIFEST is in LogType enum."""

    def test_evidence_manifest_in_enum(self):
        assert hasattr(LogType, 'EVIDENCE_MANIFEST')
        assert LogType.EVIDENCE_MANIFEST.value == "evidence_manifest"


class TestFilePatternMatching:
    """Test file pattern matching for evidence manifest."""

    def test_pattern_matches_manifest_file(self):
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.EVIDENCE_MANIFEST)
        assert pattern is not None

        assert re.match(pattern, "_EVIDENCE_MANIFEST.json")

    def test_pattern_rejects_other_files(self):
        import re
        pattern = LOG_FILE_PATTERNS.get(LogType.EVIDENCE_MANIFEST)

        assert not re.match(pattern, "01_SignInLogs.csv")
        assert not re.match(pattern, "manifest.json")


class TestEvidenceManifestDataclass:
    """Test EvidenceManifestEntry dataclass."""

    def test_dataclass_has_required_fields(self):
        from claude.tools.m365_ir.m365_log_parser import EvidenceManifestEntry

        required_fields = [
            'investigation_id', 'collection_version', 'collected_at',
            'collected_by', 'collected_on', 'date_range_start',
            'date_range_end', 'days_back', 'files'
        ]

        entry_fields = [f.name for f in EvidenceManifestEntry.__dataclass_fields__.values()]
        for field in required_fields:
            assert field in entry_fields, f"Missing field: {field}"


class TestEvidenceManifestParser:
    """Test M365LogParser.parse_evidence_manifest() method."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    @pytest.fixture
    def sample_json_path_utf8(self, tmp_path):
        """Create UTF-8 encoded manifest for testing."""
        json_file = tmp_path / "_EVIDENCE_MANIFEST.json"
        json_file.write_text(json.dumps(SAMPLE_MANIFEST_JSON), encoding='utf-8')
        return json_file

    @pytest.fixture
    def sample_json_path_utf16(self, tmp_path):
        """Create UTF-16 LE encoded manifest (like real exports)."""
        json_file = tmp_path / "_EVIDENCE_MANIFEST.json"
        content = json.dumps(SAMPLE_MANIFEST_JSON)
        # Write with UTF-16 LE BOM
        with open(json_file, 'wb') as f:
            f.write(b'\xff\xfe')  # UTF-16 LE BOM
            f.write(content.encode('utf-16-le'))
        return json_file

    def test_parse_returns_entry(self, parser, sample_json_path_utf8):
        """Parser should return EvidenceManifestEntry object."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)

        from claude.tools.m365_ir.m365_log_parser import EvidenceManifestEntry
        assert isinstance(entry, EvidenceManifestEntry)

    def test_parse_extracts_investigation_id(self, parser, sample_json_path_utf8):
        """Parser should extract investigation ID."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)
        assert entry.investigation_id == "56561ac7-c1ee-47f2-bdc2-d2e08405bb5b"

    def test_parse_extracts_collection_version(self, parser, sample_json_path_utf8):
        """Parser should extract collection version."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)
        assert entry.collection_version == "2.1.0-Production"

    def test_parse_extracts_collected_by(self, parser, sample_json_path_utf8):
        """Parser should extract who collected the evidence."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)
        assert entry.collected_by == "ORROAD\\alex.olver"

    def test_parse_extracts_days_back(self, parser, sample_json_path_utf8):
        """Parser should extract days back value."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)
        assert entry.days_back == 90

    def test_parse_extracts_files_list(self, parser, sample_json_path_utf8):
        """Parser should extract files with SHA256 hashes."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf8)

        assert isinstance(entry.files, list)
        assert len(entry.files) == 2

        first_file = entry.files[0]
        assert first_file['FileName'] == "01_SignInLogs.csv"
        assert 'SHA256' in first_file
        assert first_file['Records'] == 3201

    def test_parse_handles_utf16_encoding(self, parser, sample_json_path_utf16):
        """Parser should handle UTF-16 LE encoded files."""
        entry = parser.parse_evidence_manifest(sample_json_path_utf16)
        assert entry.investigation_id == "56561ac7-c1ee-47f2-bdc2-d2e08405bb5b"


class TestIntegrityVerification:
    """Test SHA256 verification functionality."""

    @pytest.fixture
    def parser(self):
        return M365LogParser(date_format="AU")

    def test_get_file_hashes_returns_dict(self, parser, tmp_path):
        """get_file_hashes should return filename→SHA256 mapping."""
        json_file = tmp_path / "_EVIDENCE_MANIFEST.json"
        json_file.write_text(json.dumps(SAMPLE_MANIFEST_JSON), encoding='utf-8')

        entry = parser.parse_evidence_manifest(json_file)
        hashes = entry.get_file_hashes()

        assert isinstance(hashes, dict)
        assert "01_SignInLogs.csv" in hashes
        assert hashes["01_SignInLogs.csv"] == "78AFCF2AEEC45729FB601C1308BA08ABEEE84828C6D0EB3187E4665AEBF058F0"


class TestRealDataParsing:
    """Test with actual FYNA data if available."""

    FYNA_MANIFEST_PATH = Path("/tmp/fyna_extract/TenantWide_Investigation_20260108_083839/_EVIDENCE_MANIFEST.json")

    @pytest.mark.skipif(
        not FYNA_MANIFEST_PATH.exists(),
        reason="FYNA sample data not available"
    )
    def test_parse_real_fyna_manifest(self):
        """Parse actual FYNA evidence manifest."""
        parser = M365LogParser(date_format="AU")
        entry = parser.parse_evidence_manifest(self.FYNA_MANIFEST_PATH)

        assert entry.investigation_id == "56561ac7-c1ee-47f2-bdc2-d2e08405bb5b"
        assert entry.collection_version == "2.1.0-Production"
        assert entry.days_back == 90
        assert len(entry.files) > 10  # Should have multiple files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
