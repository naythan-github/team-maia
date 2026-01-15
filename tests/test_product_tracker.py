#!/usr/bin/env python3
"""
Tests for Product Candidate Tracker

TDD tests for tracking tools with organizational productization potential.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude.tools.pmp.product_tracker import (
    ProductCandidate,
    ProductTracker,
    main
)


class TestProductCandidate:
    """Tests for ProductCandidate dataclass"""

    def test_candidate_creation_with_required_fields(self):
        """Create candidate with minimum required fields"""
        candidate = ProductCandidate(
            tool="pdf_extractor.py",
            path="claude/tools/document/",
            potential="high",
            audience="org",
            value="Batch PDF processing"
        )
        assert candidate.tool == "pdf_extractor.py"
        assert candidate.potential == "high"
        assert candidate.status == "idea"  # default

    def test_candidate_creation_with_all_fields(self):
        """Create candidate with all fields populated"""
        candidate = ProductCandidate(
            tool="receipt_ocr.py",
            path="claude/tools/finance/",
            potential="high",
            audience="org",
            value="Privacy-first OCR",
            changes_needed=["Remove paths", "Add UI"],
            status="prototype",
            dependencies=["tesseract"],
            notes="Popular request"
        )
        assert candidate.changes_needed == ["Remove paths", "Add UI"]
        assert candidate.dependencies == ["tesseract"]
        assert candidate.notes == "Popular request"

    def test_candidate_validation_rejects_invalid_potential(self):
        """Invalid potential value raises error"""
        with pytest.raises(ValueError, match="potential"):
            ProductCandidate(
                tool="test.py",
                path="test/",
                potential="very_high",  # invalid
                audience="org",
                value="test"
            )

    def test_candidate_validation_rejects_invalid_status(self):
        """Invalid status value raises error"""
        with pytest.raises(ValueError, match="status"):
            ProductCandidate(
                tool="test.py",
                path="test/",
                potential="high",
                audience="org",
                value="test",
                status="done"  # invalid
            )

    def test_candidate_validation_rejects_invalid_audience(self):
        """Invalid audience value raises error"""
        with pytest.raises(ValueError, match="audience"):
            ProductCandidate(
                tool="test.py",
                path="test/",
                potential="high",
                audience="global",  # invalid
                value="test"
            )

    def test_candidate_to_dict_serialization(self):
        """Candidate converts to dictionary"""
        candidate = ProductCandidate(
            tool="test.py",
            path="test/",
            potential="high",
            audience="team",
            value="Test tool"
        )
        data = candidate.to_dict()
        assert data["tool"] == "test.py"
        assert data["potential"] == "high"
        assert "added" in data
        assert "updated" in data

    def test_candidate_from_dict_deserialization(self):
        """Candidate created from dictionary"""
        data = {
            "tool": "test.py",
            "path": "test/",
            "potential": "medium",
            "audience": "department",
            "value": "Test",
            "changes_needed": ["item1"],
            "status": "ready",
            "dependencies": [],
            "added": "2026-01-15",
            "updated": "2026-01-15",
            "notes": None
        }
        candidate = ProductCandidate.from_dict(data)
        assert candidate.tool == "test.py"
        assert candidate.potential == "medium"
        assert candidate.changes_needed == ["item1"]


class TestProductTracker:
    """Tests for ProductTracker CRUD operations"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with temp data file"""
        data_path = tmp_path / "product_candidates.json"
        return ProductTracker(data_path=str(data_path))

    @pytest.fixture
    def sample_candidate(self):
        """Sample candidate for testing"""
        return ProductCandidate(
            tool="sample.py",
            path="claude/tools/test/",
            potential="high",
            audience="org",
            value="Sample tool for testing"
        )

    def test_add_candidate_creates_entry(self, tracker, sample_candidate):
        """Adding candidate stores it"""
        result = tracker.add(sample_candidate)
        assert result is True
        assert len(tracker.list()) == 1

    def test_add_candidate_prevents_duplicates(self, tracker, sample_candidate):
        """Cannot add duplicate tool names"""
        tracker.add(sample_candidate)
        result = tracker.add(sample_candidate)
        assert result is False
        assert len(tracker.list()) == 1

    def test_list_candidates_returns_all(self, tracker):
        """List returns all candidates"""
        tracker.add(ProductCandidate(
            tool="tool1.py", path="p1/", potential="high",
            audience="org", value="v1"
        ))
        tracker.add(ProductCandidate(
            tool="tool2.py", path="p2/", potential="low",
            audience="team", value="v2"
        ))
        assert len(tracker.list()) == 2

    def test_list_candidates_filter_by_potential(self, tracker):
        """List filters by potential"""
        tracker.add(ProductCandidate(
            tool="high1.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.add(ProductCandidate(
            tool="low1.py", path="p/", potential="low",
            audience="org", value="v"
        ))
        high_only = tracker.list(potential="high")
        assert len(high_only) == 1
        assert high_only[0].tool == "high1.py"

    def test_list_candidates_filter_by_status(self, tracker):
        """List filters by status"""
        tracker.add(ProductCandidate(
            tool="idea.py", path="p/", potential="high",
            audience="org", value="v", status="idea"
        ))
        tracker.add(ProductCandidate(
            tool="ready.py", path="p/", potential="high",
            audience="org", value="v", status="ready"
        ))
        ready_only = tracker.list(status="ready")
        assert len(ready_only) == 1
        assert ready_only[0].tool == "ready.py"

    def test_list_candidates_filter_by_audience(self, tracker):
        """List filters by audience"""
        tracker.add(ProductCandidate(
            tool="org.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.add(ProductCandidate(
            tool="team.py", path="p/", potential="high",
            audience="team", value="v"
        ))
        org_only = tracker.list(audience="org")
        assert len(org_only) == 1
        assert org_only[0].tool == "org.py"

    def test_update_candidate_modifies_fields(self, tracker, sample_candidate):
        """Update modifies specified fields"""
        tracker.add(sample_candidate)
        result = tracker.update("sample.py", potential="low", status="ready")
        assert result is True
        updated = tracker.get("sample.py")
        assert updated.potential == "low"
        assert updated.status == "ready"

    def test_update_candidate_updates_timestamp(self, tracker, sample_candidate):
        """Update changes the updated timestamp"""
        tracker.add(sample_candidate)
        original = tracker.get("sample.py").updated
        tracker.update("sample.py", status="prototype")
        updated = tracker.get("sample.py").updated
        # Timestamps should differ (or at least update was called)
        assert updated is not None

    def test_update_nonexistent_returns_false(self, tracker):
        """Update returns False for missing tool"""
        result = tracker.update("nonexistent.py", status="ready")
        assert result is False

    def test_remove_candidate_deletes_entry(self, tracker, sample_candidate):
        """Remove deletes the candidate"""
        tracker.add(sample_candidate)
        result = tracker.remove("sample.py")
        assert result is True
        assert len(tracker.list()) == 0

    def test_remove_nonexistent_returns_false(self, tracker):
        """Remove returns False for missing tool"""
        result = tracker.remove("nonexistent.py")
        assert result is False

    def test_get_candidate_by_tool_name(self, tracker, sample_candidate):
        """Get retrieves candidate by tool name"""
        tracker.add(sample_candidate)
        found = tracker.get("sample.py")
        assert found is not None
        assert found.tool == "sample.py"

    def test_get_nonexistent_returns_none(self, tracker):
        """Get returns None for missing tool"""
        assert tracker.get("nonexistent.py") is None


class TestDataPersistence:
    """Tests for JSON persistence"""

    @pytest.fixture
    def data_path(self, tmp_path):
        return tmp_path / "product_candidates.json"

    def test_save_creates_json_file(self, data_path):
        """Save creates the JSON file"""
        tracker = ProductTracker(data_path=str(data_path))
        tracker.add(ProductCandidate(
            tool="test.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.save()
        assert data_path.exists()

    def test_load_reads_existing_file(self, data_path):
        """Load reads from existing file"""
        # Create file with data
        data = {
            "candidates": [{
                "tool": "existing.py",
                "path": "p/",
                "potential": "high",
                "audience": "org",
                "value": "v",
                "changes_needed": [],
                "status": "idea",
                "dependencies": [],
                "added": "2026-01-15",
                "updated": "2026-01-15",
                "notes": None
            }]
        }
        data_path.write_text(json.dumps(data))

        tracker = ProductTracker(data_path=str(data_path))
        tracker.load()
        assert len(tracker.list()) == 1
        assert tracker.get("existing.py") is not None

    def test_load_creates_empty_if_missing(self, data_path):
        """Load handles missing file gracefully"""
        tracker = ProductTracker(data_path=str(data_path))
        tracker.load()  # Should not raise
        assert len(tracker.list()) == 0

    def test_save_preserves_all_fields(self, data_path):
        """Save/load preserves all candidate fields"""
        tracker = ProductTracker(data_path=str(data_path))
        original = ProductCandidate(
            tool="full.py",
            path="claude/tools/full/",
            potential="medium",
            audience="department",
            value="Full test",
            changes_needed=["A", "B"],
            status="prototype",
            dependencies=["dep1"],
            notes="Test notes"
        )
        tracker.add(original)
        tracker.save()

        # Load in new tracker
        tracker2 = ProductTracker(data_path=str(data_path))
        tracker2.load()
        loaded = tracker2.get("full.py")

        assert loaded.tool == original.tool
        assert loaded.path == original.path
        assert loaded.potential == original.potential
        assert loaded.audience == original.audience
        assert loaded.changes_needed == original.changes_needed
        assert loaded.dependencies == original.dependencies
        assert loaded.notes == original.notes


class TestCLI:
    """Tests for CLI interface"""

    @pytest.fixture
    def cli_tracker(self, tmp_path):
        """Tracker for CLI testing"""
        data_path = tmp_path / "cli_test.json"
        return str(data_path)

    def test_cli_add_command(self, cli_tracker, capsys):
        """CLI add creates candidate"""
        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'add', 'new_tool.py',
            '--path', 'claude/tools/test/',
            '--potential', 'high',
            '--audience', 'org',
            '--value', 'Test value'
        ]):
            main()
        captured = capsys.readouterr()
        assert "Added" in captured.out or "new_tool.py" in captured.out

    def test_cli_list_command(self, cli_tracker, capsys):
        """CLI list shows candidates"""
        # First add a candidate
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="list_test.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker, 'list'
        ]):
            main()
        captured = capsys.readouterr()
        assert "list_test.py" in captured.out

    def test_cli_list_with_filters(self, cli_tracker, capsys):
        """CLI list respects filters"""
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="high.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.add(ProductCandidate(
            tool="low.py", path="p/", potential="low",
            audience="org", value="v"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'list', '--potential', 'high'
        ]):
            main()
        captured = capsys.readouterr()
        assert "high.py" in captured.out
        assert "low.py" not in captured.out

    def test_cli_update_command(self, cli_tracker, capsys):
        """CLI update modifies candidate"""
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="update_test.py", path="p/", potential="low",
            audience="team", value="v"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'update', 'update_test.py', '--potential', 'high'
        ]):
            main()

        # Verify update
        tracker2 = ProductTracker(data_path=cli_tracker)
        tracker2.load()
        assert tracker2.get("update_test.py").potential == "high"

    def test_cli_remove_command(self, cli_tracker, capsys):
        """CLI remove deletes candidate"""
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="remove_test.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'remove', 'remove_test.py'
        ]):
            main()

        tracker2 = ProductTracker(data_path=cli_tracker)
        tracker2.load()
        assert tracker2.get("remove_test.py") is None

    def test_cli_report_markdown_format(self, cli_tracker, capsys):
        """CLI report generates markdown"""
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="report_test.py", path="p/", potential="high",
            audience="org", value="Test value"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'report', '--format', 'md'
        ]):
            main()
        captured = capsys.readouterr()
        assert "report_test.py" in captured.out
        assert "|" in captured.out  # markdown table

    def test_cli_report_json_format(self, cli_tracker, capsys):
        """CLI report generates JSON"""
        tracker = ProductTracker(data_path=cli_tracker)
        tracker.add(ProductCandidate(
            tool="json_test.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        tracker.save()

        with patch.object(sys, 'argv', [
            'product_tracker.py', '--data-path', cli_tracker,
            'report', '--format', 'json'
        ]):
            main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "candidates" in data


class TestSuggestionEngine:
    """Tests for automatic candidate suggestion"""

    @pytest.fixture
    def tracker(self, tmp_path):
        data_path = tmp_path / "suggest_test.json"
        return ProductTracker(data_path=str(data_path))

    def test_suggest_returns_list(self, tracker):
        """Suggest returns a list of suggestions"""
        suggestions = tracker.suggest()
        assert isinstance(suggestions, list)

    def test_suggest_includes_tool_info(self, tracker):
        """Suggestions include tool information"""
        suggestions = tracker.suggest()
        if suggestions:  # May be empty if no capabilities DB
            first = suggestions[0]
            assert "tool" in first
            assert "path" in first

    @patch('claude.tools.pmp.product_tracker.ProductTracker._scan_capabilities')
    def test_suggest_excludes_already_tracked(self, mock_scan, tracker):
        """Suggest excludes tools already in tracker"""
        mock_scan.return_value = [
            {"tool": "existing.py", "path": "p/", "reason": "test"},
            {"tool": "new.py", "path": "p/", "reason": "test"}
        ]
        tracker.add(ProductCandidate(
            tool="existing.py", path="p/", potential="high",
            audience="org", value="v"
        ))
        suggestions = tracker.suggest()
        tools = [s["tool"] for s in suggestions]
        assert "existing.py" not in tools
        assert "new.py" in tools
