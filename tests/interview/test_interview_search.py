#!/usr/bin/env python3
"""
Tests for Interview Search System

TDD tests covering:
- VTT parsing
- SQLite storage and FTS5
- ChromaDB indexing
- Hybrid search
- Scoring frameworks

Author: Maia System
Created: 2025-12-15 (Phase 223)
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.interview.interview_vtt_parser import (
    InterviewVTTParser, VTTSegment, ParsedInterview
)
from claude.tools.interview.interview_scoring import InterviewScorer, ScoreResult


class TestVTTParser(unittest.TestCase):
    """Test VTT file parsing"""

    def setUp(self):
        self.parser = InterviewVTTParser()
        self.sample_vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v Naythan Dawe>Welcome to the interview. Can you tell me about your experience?</v>

00:00:05.000 --> 00:00:15.000
<v John Smith>I have 6 years of experience working with Azure and Terraform.</v>

00:00:15.000 --> 00:00:25.000
<v John Smith>I led a team of 5 engineers and implemented AKS clusters.</v>

00:00:25.000 --> 00:00:35.000
<v Naythan Dawe>That's great. What about certifications?</v>

00:00:35.000 --> 00:00:45.000
<v John Smith>I'm certified in AZ-305 and AZ-104.</v>
"""

    def test_parse_speaker_pattern(self):
        """Test speaker extraction from VTT"""
        matches = self.parser.SPEAKER_PATTERN.findall(self.sample_vtt)
        self.assertEqual(len(matches), 5)
        self.assertEqual(matches[0][0], 'Naythan Dawe')
        self.assertEqual(matches[1][0], 'John Smith')

    def test_timestamp_parsing(self):
        """Test timestamp to milliseconds conversion"""
        self.assertEqual(self.parser._parse_timestamp("00:00:00.000"), 0)
        self.assertEqual(self.parser._parse_timestamp("00:01:00.000"), 60000)
        self.assertEqual(self.parser._parse_timestamp("01:30:45.500"), 5445500)

    def test_parse_vtt_file(self):
        """Test full VTT file parsing"""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as f:
            f.write(self.sample_vtt)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)

            self.assertIsInstance(result, ParsedInterview)
            self.assertEqual(result.total_segments, 5)
            self.assertTrue(result.total_words > 0)

            # Check speaker identification
            self.assertEqual(result.speakers.get('Naythan Dawe'), 'interviewer')
            self.assertEqual(result.speakers.get('John Smith'), 'candidate')

        finally:
            os.unlink(temp_path)

    def test_identify_interviewer(self):
        """Test interviewer identification by name"""
        segments = [
            VTTSegment(0, "Naythan", "Question?"),
            VTTSegment(1, "Candidate", "Answer."),
        ]
        speakers = self.parser._identify_speakers(segments)

        self.assertEqual(speakers['Naythan'], 'interviewer')
        self.assertEqual(speakers['Candidate'], 'candidate')

    def test_file_not_found(self):
        """Test handling of missing file"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse("/nonexistent/file.vtt")


class TestInterviewScorer(unittest.TestCase):
    """Test interview scoring frameworks"""

    def setUp(self):
        self.scorer = InterviewScorer()
        self.sample_dialogue = {
            "Candidate": [
                "I have 6 years of experience with Azure and terraform",
                "I led a team of 5 engineers and mentored junior developers",
                "We implemented AKS clusters across multiple clients",
                "I'm certified in AZ-305 and AZ-104"
            ]
        }

    def test_100_point_scoring(self):
        """Test 100-point keyword-based scoring"""
        result = self.scorer.score(self.sample_dialogue, "100_point")

        self.assertIsInstance(result, ScoreResult)
        self.assertEqual(result.framework, "100_point")
        self.assertEqual(result.max_score, 100)
        self.assertTrue(result.total_score > 0)
        self.assertTrue(result.percentage >= 0)
        self.assertIn('Azure Architecture', result.breakdown)

    def test_50_point_scoring(self):
        """Test 50-point weighted scoring"""
        result = self.scorer.score(self.sample_dialogue, "50_point")

        self.assertEqual(result.framework, "50_point")
        self.assertEqual(result.max_score, 50)
        self.assertIn('leadership_validation', result.breakdown)
        self.assertIn('technical_validation', result.breakdown)

    def test_green_flag_detection(self):
        """Test detection of positive indicators"""
        result = self.scorer.score(self.sample_dialogue, "100_point")

        # Should detect certifications and Terraform
        green_flags = result.green_flags
        self.assertTrue(any('certification' in f.lower() for f in green_flags) or
                       any('terraform' in f.lower() for f in green_flags))

    def test_recommendation_generation(self):
        """Test recommendation is generated"""
        result = self.scorer.score(self.sample_dialogue, "100_point")

        self.assertIn(result.recommendation,
                     ['STRONG_HIRE', 'HIRE', 'CONSIDER', 'DO_NOT_HIRE'])
        self.assertTrue(len(result.rationale) > 0)

    def test_empty_dialogue(self):
        """Test handling of empty dialogue"""
        result = self.scorer.score({}, "100_point")

        self.assertEqual(result.total_score, 0)
        self.assertEqual(result.percentage, 0)

    def test_unknown_framework(self):
        """Test handling of unknown framework"""
        with self.assertRaises(ValueError):
            self.scorer.score(self.sample_dialogue, "unknown_framework")


class TestVTTSegment(unittest.TestCase):
    """Test VTTSegment dataclass"""

    def test_word_count_calculation(self):
        """Test automatic word count"""
        segment = VTTSegment(
            index=0,
            speaker="Test",
            text="This is a five word sentence."
        )
        self.assertEqual(segment.word_count, 6)

    def test_segment_with_timestamps(self):
        """Test segment with timestamp data"""
        segment = VTTSegment(
            index=0,
            speaker="Test",
            text="Hello",
            start_time_ms=1000,
            end_time_ms=5000
        )
        self.assertEqual(segment.start_time_ms, 1000)
        self.assertEqual(segment.end_time_ms, 5000)


class TestParsedInterview(unittest.TestCase):
    """Test ParsedInterview dataclass"""

    def test_candidate_text_extraction(self):
        """Test extracting all candidate dialogue"""
        segments = [
            VTTSegment(0, "Interviewer", "Question", speaker_role="interviewer"),
            VTTSegment(1, "Candidate", "Answer one", speaker_role="candidate"),
            VTTSegment(2, "Candidate", "Answer two", speaker_role="candidate"),
        ]
        interview = ParsedInterview(
            file_path="/test.vtt",
            segments=segments
        )

        candidate_text = interview.get_candidate_text()
        self.assertIn("Answer one", candidate_text)
        self.assertIn("Answer two", candidate_text)
        self.assertNotIn("Question", candidate_text)

    def test_dialogue_by_speaker(self):
        """Test grouping dialogue by speaker"""
        segments = [
            VTTSegment(0, "Alice", "Hello"),
            VTTSegment(1, "Bob", "Hi there"),
            VTTSegment(2, "Alice", "How are you?"),
        ]
        interview = ParsedInterview(
            file_path="/test.vtt",
            segments=segments
        )

        dialogue = interview.get_dialogue_by_speaker()
        self.assertEqual(len(dialogue['Alice']), 2)
        self.assertEqual(len(dialogue['Bob']), 1)


class TestSearchSystemIntegration(unittest.TestCase):
    """Integration tests for the full search system"""

    @classmethod
    def setUpClass(cls):
        """Set up test database in temp directory"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.sqlite_path = os.path.join(cls.temp_dir, "test_interview.db")
        cls.chroma_path = os.path.join(cls.temp_dir, "test_chroma")

    @classmethod
    def tearDownClass(cls):
        """Clean up temp directory"""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @patch('claude.tools.interview.interview_search_system.requests.post')
    def test_system_initialization(self, mock_post):
        """Test system initializes correctly"""
        from claude.tools.interview.interview_search_system import InterviewSearchSystem

        # Mock embedding response
        mock_post.return_value.json.return_value = {
            "embeddings": [[0.1] * 768]
        }
        mock_post.return_value.raise_for_status = MagicMock()

        system = InterviewSearchSystem(
            sqlite_path=self.sqlite_path,
            chroma_path=self.chroma_path
        )

        self.assertTrue(os.path.exists(self.sqlite_path))
        self.assertTrue(os.path.exists(self.chroma_path))

    def test_stats_empty_database(self):
        """Test stats on empty database"""
        from claude.tools.interview.interview_search_system import InterviewSearchSystem

        system = InterviewSearchSystem(
            sqlite_path=os.path.join(self.temp_dir, "empty.db"),
            chroma_path=os.path.join(self.temp_dir, "empty_chroma")
        )

        stats = system.get_stats()
        self.assertEqual(stats['total_interviews'], 0)
        self.assertEqual(stats['total_segments'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
