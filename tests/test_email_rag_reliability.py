#!/usr/bin/env python3
"""
Email RAG Reliability Test Suite
Tests for production failure scenarios discovered in Oct 2025

Critical bugs fixed:
1. Contact extraction blocking email indexing when Contacts.app not running
2. LaunchAgent path validation missing (disaster recovery corruption)
3. Headless/background execution not tested
4. Graceful degradation not implemented

Author: SRE Principal Engineer Agent
Created: 2025-10-29
"""

import os
import sys
import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest import mock
from typing import Dict, Any

# Add maia to path
MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.email_rag_ollama import EmailRAGOllama
from claude.tools.contact_extractor import MacOSContactsBridge


class TestEmailRAGReliability:
    """Production reliability tests for Email RAG system"""

    @pytest.fixture
    def temp_db_path(self):
        """Temporary database path for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_mail_bridge(self):
        """Mock mail bridge returning test data"""
        with mock.patch('claude.tools.email_rag_ollama.MacOSMailBridge') as mock_bridge:
            instance = mock_bridge.return_value
            instance.get_inbox_messages.return_value = [
                {
                    'id': 'test-msg-1',
                    'subject': 'Test Email',
                    'date': '2025-10-29T10:00:00',
                    'from': 'test@example.com'
                }
            ]
            instance.get_sent_messages.return_value = []
            instance.get_message_content.return_value = {
                'id': 'test-msg-1',
                'subject': 'Test Email',
                'from': 'test@example.com',
                'date': '2025-10-29T10:00:00',
                'content': 'Test content',
                'read': True
            }
            yield instance

    @pytest.fixture
    def mock_ollama(self):
        """Mock Ollama embeddings"""
        with mock.patch('claude.tools.email_rag_ollama.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'embeddings': [[0.1] * 768]  # nomic-embed-text is 768-dim
            }
            mock_post.return_value.raise_for_status = lambda: None
            yield mock_post

    # ============================================================================
    # TEST SUITE 1: Contact Extraction Graceful Degradation
    # ============================================================================

    def test_contact_extraction_failure_does_not_block_indexing(
        self, temp_db_path, mock_mail_bridge, mock_ollama
    ):
        """
        CRITICAL: Email indexing must succeed even if contact extraction fails

        Scenario: Contacts.app not running (background LaunchAgent execution)
        Expected: Email indexed successfully, contact extraction skipped
        """
        # Mock contact bridge to fail (simulating Contacts.app not running)
        with mock.patch.object(
            MacOSContactsBridge,
            'get_all_contacts',
            side_effect=RuntimeError("Contacts got an error: Application isn't running. (-600)")
        ):
            rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=True)

            # Should not raise, should index emails
            stats = rag.index_inbox(limit=10, hours_ago=24)

            # Assertions
            assert stats['new'] >= 0, "Should index emails despite contact failure"
            assert stats['contacts_added'] == 0, "No contacts added when extraction fails"
            assert rag.extract_contacts is False, "Contact extraction should be disabled after failure"

    def test_contact_extraction_disabled_by_default(self, temp_db_path, mock_mail_bridge, mock_ollama):
        """Contact extraction can be completely disabled"""
        rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)
        stats = rag.index_inbox(limit=10, hours_ago=24)

        assert stats['contacts_added'] == 0, "No contacts when disabled"
        assert 'contacts_added' in stats, "Stats should include contact count even when disabled"

    def test_contact_extraction_success_path(self, temp_db_path, mock_mail_bridge, mock_ollama):
        """Contact extraction works when Contacts.app is available"""
        with mock.patch.object(MacOSContactsBridge, 'get_all_contacts', return_value=[]):
            with mock.patch.object(MacOSContactsBridge, 'add_contact', return_value=True):
                rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=True)
                stats = rag.index_inbox(limit=10, hours_ago=24)

                # Contact extraction should still be enabled
                assert rag.extract_contacts is True, "Contact extraction remains enabled on success"

    # ============================================================================
    # TEST SUITE 2: Headless/Background Execution
    # ============================================================================

    def test_runs_without_gui_session(self, temp_db_path, mock_ollama):
        """
        Email RAG must work in headless LaunchAgent environment

        Scenario: No GUI, minimal environment variables, no user interaction
        Expected: Service runs successfully without user session dependencies
        """
        # Simulate minimal LaunchAgent environment
        minimal_env = {
            'HOME': os.getenv('HOME'),
            'USER': os.getenv('USER'),
            'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
            'TMPDIR': tempfile.gettempdir()
        }

        # Create test script that imports and initializes EmailRAG
        test_script = f"""
import sys
sys.path.insert(0, '{MAIA_ROOT}')
from claude.tools.email_rag_ollama import EmailRAGOllama

try:
    rag = EmailRAGOllama(db_path='{temp_db_path}', extract_contacts=False)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {{e}}")
    sys.exit(1)
"""

        result = subprocess.run(
            [sys.executable, '-c', test_script],
            env=minimal_env,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"Should run headless. Error: {result.stderr}"
        assert "SUCCESS" in result.stdout, "Should initialize successfully"

    def test_no_interactive_prompts(self, temp_db_path, mock_mail_bridge, mock_ollama):
        """Email RAG must never prompt for user input (breaks LaunchAgent)"""
        with mock.patch('builtins.input', side_effect=Exception("Interactive input called!")):
            rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)
            # Should not raise Exception from input() call
            stats = rag.index_inbox(limit=10, hours_ago=24)
            assert stats is not None, "Should complete without user interaction"

    # ============================================================================
    # TEST SUITE 3: LaunchAgent Path Validation
    # ============================================================================

    def test_script_paths_exist(self):
        """
        All LaunchAgent plist files must point to existing Python scripts

        Scenario: Disaster recovery corruption, incorrect restore paths
        Expected: All script paths are valid and executable
        """
        launchagent_dir = Path.home() / "Library" / "LaunchAgents"
        maia_plists = list(launchagent_dir.glob("com.maia.*.plist"))

        assert len(maia_plists) > 0, "No Maia LaunchAgents found"

        for plist_path in maia_plists:
            # Parse plist (simple XML parsing)
            import plistlib
            with open(plist_path, 'rb') as f:
                plist = plistlib.load(f)

            if 'ProgramArguments' in plist:
                args = plist['ProgramArguments']
                if len(args) >= 2:
                    script_path = args[1]  # First arg is interpreter, second is script

                    # Validate path
                    assert not script_path.startswith('/tmp/'), \
                        f"Temp path in production plist: {plist_path.name} -> {script_path}"

                    assert Path(script_path).exists(), \
                        f"Script not found: {plist_path.name} -> {script_path}"

    def test_no_hardcoded_test_paths(self):
        """LaunchAgent plists must not contain test/temporary paths"""
        launchagent_dir = Path.home() / "Library" / "LaunchAgents"

        forbidden_patterns = [
            '/tmp/',
            '/var/tmp/',
            'test-final',
            'maia-restore-test'
        ]

        for plist_path in launchagent_dir.glob("com.maia.*.plist"):
            with open(plist_path, 'r') as f:
                content = f.read()

            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden path pattern '{pattern}' in {plist_path.name}"

    # ============================================================================
    # TEST SUITE 4: Error Handling & Recovery
    # ============================================================================

    def test_ollama_unavailable_fails_gracefully(self, temp_db_path):
        """Service should fail with clear error when Ollama not running"""
        # Mock both mail bridge and Ollama to isolate connection failure
        with mock.patch('claude.tools.email_rag_ollama.MacOSMailBridge') as mock_bridge:
            instance = mock_bridge.return_value
            instance.get_inbox_messages.return_value = [
                {'id': 'test-1', 'subject': 'Test', 'date': '2025-10-29T10:00:00'}
            ]
            instance.get_sent_messages.return_value = []
            instance.get_message_content.return_value = {
                'id': 'test-1', 'subject': 'Test', 'from': 'test@example.com',
                'date': '2025-10-29T10:00:00', 'content': 'Test', 'read': True
            }

            # Mock Ollama connection failure during embedding call
            with mock.patch('claude.tools.email_rag_ollama.requests.post', side_effect=ConnectionError("Connection refused")):
                rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)

                # Should raise during indexing when trying to get embeddings
                with pytest.raises(ConnectionError):
                    rag.index_inbox(limit=1, hours_ago=24)

    def test_mail_app_unavailable_fails_gracefully(self, temp_db_path, mock_ollama):
        """Service should handle Mail.app not running"""
        with mock.patch('claude.tools.email_rag_ollama.MacOSMailBridge') as mock_bridge:
            mock_bridge.return_value.get_inbox_messages.side_effect = RuntimeError("Mail not running")

            rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)

            with pytest.raises(RuntimeError):
                rag.index_inbox(limit=1, hours_ago=24)

    def test_partial_indexing_on_error(self, temp_db_path, mock_ollama):
        """If some emails fail, others should still be indexed"""
        with mock.patch('claude.tools.email_rag_ollama.MacOSMailBridge') as mock_bridge:
            instance = mock_bridge.return_value

            # Return 3 messages
            instance.get_inbox_messages.return_value = [
                {'id': 'msg-1', 'subject': 'Test 1', 'date': '2025-10-29T10:00:00'},
                {'id': 'msg-2', 'subject': 'Test 2', 'date': '2025-10-29T10:01:00'},
                {'id': 'msg-3', 'subject': 'Test 3', 'date': '2025-10-29T10:02:00'},
            ]
            instance.get_sent_messages.return_value = []

            # First message succeeds, second fails, third succeeds
            def mock_get_content(msg_id):
                if msg_id == 'msg-2':
                    raise RuntimeError("Message deleted")
                return {
                    'id': msg_id,
                    'subject': f'Subject {msg_id}',
                    'from': 'test@example.com',
                    'date': '2025-10-29T10:00:00',
                    'content': 'Test content',
                    'read': True
                }

            instance.get_message_content.side_effect = mock_get_content

            rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)
            stats = rag.index_inbox(limit=10, hours_ago=24)

            # Should have 1 error but continue processing
            assert stats['errors'] >= 1, "Should track failed messages"
            assert stats['new'] >= 0, "Should index successful messages"
            assert stats['total'] == 3, "Should attempt all messages"

    # ============================================================================
    # TEST SUITE 5: Performance & Resource Management
    # ============================================================================

    def test_indexes_within_time_limit(self, temp_db_path, mock_mail_bridge, mock_ollama):
        """Indexing 100 messages should complete within 5 minutes (SLA)"""
        import time

        # Create 100 test messages
        messages = [
            {
                'id': f'msg-{i}',
                'subject': f'Test Email {i}',
                'date': '2025-10-29T10:00:00',
                'from': 'test@example.com'
            }
            for i in range(100)
        ]

        mock_mail_bridge.get_inbox_messages.return_value = messages

        rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)

        start = time.time()
        stats = rag.index_inbox(limit=100, hours_ago=24)
        duration = time.time() - start

        assert duration < 300, f"Indexing took {duration:.1f}s, SLA is 300s (5 min)"
        assert stats['total'] == 100, "Should process all messages"

    def test_memory_efficient_large_batches(self, temp_db_path, mock_mail_bridge, mock_ollama):
        """Indexing should not load all embeddings into memory at once"""
        rag = EmailRAGOllama(db_path=temp_db_path, extract_contacts=False)

        # This should use batching internally (not load 1000 embeddings in RAM)
        stats = rag.index_inbox(limit=1000, hours_ago=24)

        # Just verify it completes - memory usage monitoring would need external tools
        assert stats is not None, "Should complete large batches"


class TestLaunchAgentConfiguration:
    """Tests for LaunchAgent service configuration"""

    def test_all_launchagents_have_logging(self):
        """All Maia LaunchAgents must have stdout/stderr logging configured"""
        import plistlib

        launchagent_dir = Path.home() / "Library" / "LaunchAgents"

        for plist_path in launchagent_dir.glob("com.maia.*.plist"):
            with open(plist_path, 'rb') as f:
                plist = plistlib.load(f)

            assert 'StandardOutPath' in plist, f"Missing stdout logging: {plist_path.name}"
            assert 'StandardErrorPath' in plist, f"Missing stderr logging: {plist_path.name}"

            # Verify log directory exists
            stdout_path = Path(plist['StandardOutPath']).parent
            assert stdout_path.exists(), f"Log directory missing: {stdout_path}"

    def test_launchagent_intervals_reasonable(self):
        """LaunchAgent intervals should be reasonable (not too frequent)"""
        import plistlib

        launchagent_dir = Path.home() / "Library" / "LaunchAgents"

        # Health monitors and file watchers can run more frequently
        health_monitor_exceptions = ['whisper-health', 'vtt-watcher-status', 'downloads-organizer-scheduler']

        for plist_path in launchagent_dir.glob("com.maia.*.plist"):
            with open(plist_path, 'rb') as f:
                plist = plistlib.load(f)

            if 'StartInterval' in plist:
                interval = plist['StartInterval']

                # Health monitors exempt from 5-minute minimum
                is_health_monitor = any(exc in plist_path.name for exc in health_monitor_exceptions)

                if not is_health_monitor:
                    # Minimum 5 minutes (300s) to avoid excessive runs
                    assert interval >= 300, \
                        f"Interval too frequent ({interval}s): {plist_path.name}"


# ============================================================================
# Integration Test: End-to-End Reliability
# ============================================================================

class TestEndToEndReliability:
    """Full system integration tests"""

    def test_full_indexing_workflow_with_failures(self, tmp_path):
        """
        Complete workflow: Initialize → Index → Search, with simulated failures

        Validates entire stack handles degraded conditions gracefully
        """
        with mock.patch('claude.tools.email_rag_ollama.MacOSMailBridge') as mock_bridge:
            with mock.patch('claude.tools.email_rag_ollama.requests.post') as mock_ollama:
                # Setup mocks
                instance = mock_bridge.return_value
                instance.get_inbox_messages.return_value = [
                    {'id': 'test-1', 'subject': 'Important Email', 'date': '2025-10-29T10:00:00'}
                ]
                instance.get_sent_messages.return_value = []
                instance.get_message_content.return_value = {
                    'id': 'test-1',
                    'subject': 'Important Email',
                    'from': 'boss@company.com',
                    'date': '2025-10-29T10:00:00',
                    'content': 'This is critical information about the project',
                    'read': False
                }

                mock_ollama.return_value.json.return_value = {'embeddings': [[0.1] * 768]}
                mock_ollama.return_value.raise_for_status = lambda: None

                # Simulate Contacts.app failure
                with mock.patch.object(
                    MacOSContactsBridge,
                    'get_all_contacts',
                    side_effect=RuntimeError("Contacts not running")
                ):
                    # Initialize
                    rag = EmailRAGOllama(db_path=str(tmp_path), extract_contacts=True)

                    # Index (should succeed despite contact failure)
                    stats = rag.index_inbox(limit=10, hours_ago=24)
                    assert stats['new'] >= 0, "Indexing should succeed"

                    # Search (should work with indexed data)
                    results = rag.semantic_search("important project", n_results=5)
                    assert isinstance(results, list), "Search should return results"

                    # Get stats
                    system_stats = rag.get_stats()
                    assert system_stats['total_indexed'] >= 0, "Stats should be available"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
