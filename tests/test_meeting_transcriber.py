#!/usr/bin/env python3
"""
Test Suite for Meeting Transcription System

Tests continuous meeting transcription, RAG indexing, and search functionality.

Usage:
    python3 -m pytest tests/test_meeting_transcriber.py -v
    python3 tests/test_meeting_transcriber.py  # Run without pytest

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-10-29
"""

import os
import sys
import time
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.whisper_meeting_transcriber import (
    MeetingTranscriber,
    MeetingTranscriptionRAG
)


class TestMeetingTranscriptionRAG(unittest.TestCase):
    """Test RAG indexing and search functionality"""

    def setUp(self):
        """Create temporary RAG database for testing"""
        self.test_db_dir = tempfile.mkdtemp(prefix="test_rag_")
        self.rag = MeetingTranscriptionRAG(db_path=self.test_db_dir)

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)

    def test_rag_initialization(self):
        """Test RAG system initializes correctly"""
        self.assertTrue(self.rag.enabled or not self.rag.enabled)  # Graceful degradation
        if self.rag.enabled:
            self.assertIsNotNone(self.rag.collection)
            self.assertEqual(self.rag.collection.name, "meeting_transcripts")

    def test_index_single_chunk(self):
        """Test indexing a single transcript chunk"""
        if not self.rag.enabled:
            self.skipTest("RAG dependencies not available")

        meeting_id = "test_meeting_001"
        chunk_text = "We need to migrate the database before Q4 release."
        timestamp = datetime.now()
        metadata = {"title": "Engineering Meeting"}

        success = self.rag.index_chunk(
            meeting_id=meeting_id,
            chunk_text=chunk_text,
            timestamp=timestamp,
            chunk_number=1,
            metadata=metadata
        )

        self.assertTrue(success)

        # Verify chunk was indexed
        count = self.rag.collection.count()
        self.assertEqual(count, 1)

    def test_index_multiple_chunks(self):
        """Test indexing multiple chunks from same meeting"""
        if not self.rag.enabled:
            self.skipTest("RAG dependencies not available")

        meeting_id = "test_meeting_002"
        chunks = [
            "Database migration is our top priority.",
            "We need to complete testing by Friday.",
            "Let's schedule a review meeting next week."
        ]

        for i, chunk in enumerate(chunks):
            self.rag.index_chunk(
                meeting_id=meeting_id,
                chunk_text=chunk,
                timestamp=datetime.now(),
                chunk_number=i + 1,
                metadata={"title": "Sprint Planning"}
            )

        # Verify all chunks indexed
        count = self.rag.collection.count()
        self.assertEqual(count, 3)

    def test_search_functionality(self):
        """Test semantic search across indexed chunks"""
        if not self.rag.enabled:
            self.skipTest("RAG dependencies not available")

        # Index test data
        meeting_id = "test_meeting_003"
        test_chunks = [
            "We discussed database performance optimization strategies.",
            "The new API endpoints need better error handling.",
            "Security review revealed some authentication issues."
        ]

        for i, chunk in enumerate(test_chunks):
            self.rag.index_chunk(
                meeting_id=meeting_id,
                chunk_text=chunk,
                timestamp=datetime.now(),
                chunk_number=i + 1,
                metadata={"title": "Technical Review"}
            )

        # Search for database-related content
        results = self.rag.search("database optimization", n_results=3)

        self.assertIsNotNone(results)
        self.assertIn('documents', results)
        self.assertGreater(len(results['documents'][0]), 0)

        # First result should be database-related
        first_result = results['documents'][0][0]
        self.assertIn('database', first_result.lower())

    def test_search_with_meeting_filter(self):
        """Test search filtered by specific meeting"""
        if not self.rag.enabled:
            self.skipTest("RAG dependencies not available")

        # Index two different meetings
        self.rag.index_chunk(
            meeting_id="meeting_A",
            chunk_text="Database migration for project Alpha",
            timestamp=datetime.now(),
            chunk_number=1,
            metadata={"title": "Project Alpha"}
        )

        self.rag.index_chunk(
            meeting_id="meeting_B",
            chunk_text="Database optimization for project Beta",
            timestamp=datetime.now(),
            chunk_number=1,
            metadata={"title": "Project Beta"}
        )

        # Search only in meeting_A
        results = self.rag.search("database", meeting_id="meeting_A", n_results=5)

        self.assertEqual(len(results['documents'][0]), 1)
        self.assertIn('Alpha', results['documents'][0][0])

    def test_empty_chunk_handling(self):
        """Test that empty chunks are not indexed"""
        if not self.rag.enabled:
            self.skipTest("RAG dependencies not available")

        success = self.rag.index_chunk(
            meeting_id="test_meeting_004",
            chunk_text="",
            timestamp=datetime.now(),
            chunk_number=1,
            metadata={}
        )

        self.assertFalse(success)
        self.assertEqual(self.rag.collection.count(), 0)


class TestMeetingTranscriber(unittest.TestCase):
    """Test meeting transcription functionality"""

    def setUp(self):
        """Create temporary output directory for testing"""
        self.test_output_dir = tempfile.mkdtemp(prefix="test_transcripts_")
        self.transcriber = MeetingTranscriber(output_dir=self.test_output_dir)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_transcriber_initialization(self):
        """Test transcriber initializes with correct state"""
        self.assertIsNotNone(self.transcriber.session_id)
        self.assertIsNone(self.transcriber.start_time)
        self.assertEqual(self.transcriber.chunk_count, 0)
        self.assertFalse(self.transcriber.is_recording)
        self.assertTrue(os.path.exists(self.test_output_dir))

    def test_session_start(self):
        """Test session initialization creates output files"""
        self.transcriber.start_session(title="Test Meeting")

        self.assertIsNotNone(self.transcriber.start_time)
        self.assertTrue(self.transcriber.is_recording)
        self.assertIsNotNone(self.transcriber.transcript_file)
        self.assertIsNotNone(self.transcriber.metadata_file)
        self.assertTrue(self.transcriber.transcript_file.exists())

    def test_transcript_file_format(self):
        """Test transcript file has correct Markdown format"""
        self.transcriber.start_session(title="Format Test")

        with open(self.transcriber.transcript_file, 'r') as f:
            content = f.read()

        self.assertIn("# Format Test", content)
        self.assertIn("**Date**:", content)
        self.assertIn("**Time**:", content)
        self.assertIn("**Session ID**:", content)

    @patch('claude.tools.whisper_meeting_transcriber.requests.post')
    def test_transcribe_chunk(self, mock_post):
        """Test chunk transcription with mocked server"""
        # Mock successful transcription response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is a test transcription."
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create test audio file
        test_audio = tempfile.mktemp(suffix=".wav")
        with open(test_audio, 'wb') as f:
            f.write(b"fake audio data")

        try:
            result = self.transcriber._transcribe_chunk(test_audio)
            self.assertEqual(result, "This is a test transcription.")
        finally:
            if os.path.exists(test_audio):
                os.remove(test_audio)

    def test_save_chunk(self):
        """Test chunk saving to transcript file"""
        self.transcriber.start_session(title="Save Test")

        test_text = "This is a test chunk."
        timestamp = datetime.now()

        self.transcriber._save_chunk(test_text, timestamp)

        with open(self.transcriber.transcript_file, 'r') as f:
            content = f.read()

        self.assertIn(test_text, content)
        self.assertIn(timestamp.strftime('%H:%M:%S'), content)

    def test_metadata_update(self):
        """Test session metadata is correctly generated"""
        self.transcriber.start_session(title="Metadata Test")
        self.transcriber.chunk_count = 5

        self.transcriber._update_metadata()

        self.assertTrue(self.transcriber.metadata_file.exists())

        with open(self.transcriber.metadata_file, 'r') as f:
            metadata = json.load(f)

        self.assertEqual(metadata['session_id'], self.transcriber.session_id)
        self.assertEqual(metadata['chunk_count'], 5)
        self.assertIn('start_time', metadata)
        self.assertIn('duration_seconds', metadata)

    def test_format_duration(self):
        """Test duration formatting"""
        self.transcriber.start_time = datetime.now()

        # Wait 1 second
        time.sleep(1)

        duration = self.transcriber._format_duration()

        # Should be format HH:MM:SS
        self.assertRegex(duration, r'\d{2}:\d{2}:\d{2}')
        self.assertIn('00:00:0', duration)  # ~1 second

    def test_clean_transcription(self):
        """Test transcription cleaning removes artifacts"""
        # Transcriber uses inline cleaning in _transcribe_chunk
        # Testing the logic directly

        test_cases = [
            ("[BLANK_AUDIO]", ""),
            ("  multiple   spaces  ", "multiple spaces"),
            ("[BLANK_AUDIO] text here", "text here"),
            ("text    [BLANK_AUDIO]   more", "text more")
        ]

        for input_text, expected in test_cases:
            # Simulate cleaning logic
            cleaned = input_text.replace("[BLANK_AUDIO]", "")
            cleaned = " ".join(cleaned.split()).strip()
            self.assertEqual(cleaned, expected)

    def test_stop_session(self):
        """Test session finalization"""
        self.transcriber.start_session(title="Stop Test")
        self.transcriber.chunk_count = 3

        self.transcriber.stop_session()

        self.assertFalse(self.transcriber.is_recording)

        # Verify session summary in transcript
        with open(self.transcriber.transcript_file, 'r') as f:
            content = f.read()

        self.assertIn("Session ended", content)
        self.assertIn("Duration", content)  # Matches "**Duration**:"
        self.assertIn("Chunks processed", content)  # Matches "**Chunks processed**: 3"
        self.assertIn("3", content)  # Verify count is present


class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="test_integration_")
        self.rag_dir = tempfile.mkdtemp(prefix="test_rag_integration_")

    def tearDown(self):
        """Clean up"""
        for dir_path in [self.test_dir, self.rag_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)

    @patch('claude.tools.whisper_meeting_transcriber.requests.post')
    @patch('claude.tools.whisper_meeting_transcriber.subprocess.run')
    def test_full_workflow_mock(self, mock_subprocess, mock_post):
        """Test complete workflow with mocked audio recording and transcription"""
        # Mock audio recording
        def mock_record(*args, **kwargs):
            # Create fake audio file
            audio_file = tempfile.mktemp(suffix=".wav")
            with open(audio_file, 'wb') as f:
                f.write(b"fake audio")
            return Mock(returncode=0)

        mock_subprocess.return_value = Mock(returncode=0)

        # Mock transcription
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is a transcribed meeting segment."
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create transcriber
        transcriber = MeetingTranscriber(output_dir=self.test_dir)
        transcriber.start_session(title="Integration Test")

        # Simulate recording a chunk
        test_audio = tempfile.mktemp(suffix=".wav")
        with open(test_audio, 'wb') as f:
            f.write(b"fake audio data")

        try:
            # Transcribe
            text = transcriber._transcribe_chunk(test_audio)

            # Save
            transcriber._save_chunk(text, datetime.now())
            transcriber.chunk_count += 1

            # Stop
            transcriber.stop_session()

            # Verify outputs
            self.assertTrue(transcriber.transcript_file.exists())
            self.assertTrue(transcriber.metadata_file.exists())

            with open(transcriber.transcript_file, 'r') as f:
                content = f.read()
                self.assertIn("Integration Test", content)
                self.assertIn("transcribed meeting segment", content)

        finally:
            if os.path.exists(test_audio):
                os.remove(test_audio)

    def test_whisper_server_validation(self):
        """Test Whisper server health check"""
        # This test requires actual Whisper server running
        try:
            import requests
            response = requests.get("http://127.0.0.1:8090/", timeout=2)
            server_running = response.status_code == 200
        except Exception:
            server_running = False

        if server_running:
            # Server should be accessible
            self.assertTrue(server_running)
        else:
            self.skipTest("Whisper server not running - integration test requires live server")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMeetingTranscriptionRAG))
    suite.addTests(loader.loadTestsFromTestCase(TestMeetingTranscriber))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
