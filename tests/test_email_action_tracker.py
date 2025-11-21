#!/usr/bin/env python3
"""
Email Action Tracker - Comprehensive Test Suite
Tests all requirements before implementation (TDD Protocol Phase 3)

Author: Maia System
Created: 2025-11-21
TDD Phase: 3 - Test Design
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys

MAIA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Import will fail initially - that's expected for TDD
try:
    from claude.tools.email_action_tracker import (
        EmailActionTracker,
        ActionType,
        ActionStatus,
        ReplyIntent
    )
except ImportError:
    pytest.skip("email_action_tracker not implemented yet", allow_module_level=True)


class TestEmailActionStorage:
    """Test R1: Action Item Storage"""

    @pytest.fixture
    def tracker(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        tracker = EmailActionTracker(db_path=db_path)
        yield tracker

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_tc1_1_insert_action_with_all_fields(self, tracker):
        """TC1.1: Insert action item with all required fields"""
        action = {
            "message_id": "test@123",
            "thread_id": "thread@123",
            "subject": "Test Subject",
            "sender": "test@example.com",
            "action_description": "Send report",
            "action_type": ActionType.ACTION,
            "deadline": "2025-11-22T17:00:00",
            "priority": "HIGH"
        }

        action_id = tracker.create_action(**action)

        assert action_id is not None
        assert action_id > 0

    def test_tc1_2_retrieve_action_by_message_id(self, tracker):
        """TC1.2: Retrieve action by message_id"""
        action = tracker.create_action(
            message_id="msg@456",
            subject="Test",
            sender="sender@test.com",
            action_description="Do something",
            action_type=ActionType.ACTION,
            priority="MEDIUM"
        )

        retrieved = tracker.get_action_by_message_id("msg@456")

        assert retrieved is not None
        assert retrieved["message_id"] == "msg@456"
        assert retrieved["sender"] == "sender@test.com"

    def test_tc1_3_query_actions_by_status(self, tracker):
        """TC1.3: Query actions by status"""
        tracker.create_action(
            message_id="msg1",
            subject="Test1",
            sender="test@test.com",
            action_description="Task 1",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.create_action(
            message_id="msg2",
            subject="Test2",
            sender="test@test.com",
            action_description="Task 2",
            action_type=ActionType.ACTION,
            priority="MEDIUM"
        )

        pending_actions = tracker.get_actions_by_status(ActionStatus.PENDING)

        assert len(pending_actions) == 2

    def test_tc1_4_update_action_status(self, tracker):
        """TC1.4: Update action status"""
        action_id = tracker.create_action(
            message_id="msg@update",
            subject="Test Update",
            sender="test@test.com",
            action_description="Update test",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.update_action_status(action_id, ActionStatus.COMPLETED)

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.COMPLETED

    def test_tc1_5_handle_duplicate_message_id(self, tracker):
        """TC1.5: Handle duplicate message_id (constraint)"""
        tracker.create_action(
            message_id="duplicate@test",
            subject="Test",
            sender="test@test.com",
            action_description="First",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        with pytest.raises(sqlite3.IntegrityError):
            tracker.create_action(
                message_id="duplicate@test",
                subject="Test2",
                sender="test@test.com",
                action_description="Second",
                action_type=ActionType.ACTION,
                priority="HIGH"
            )


class TestActionTypeClassification:
    """Test R2: Action Type Classification"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        tracker = EmailActionTracker(db_path=db_path)
        yield tracker
        Path(db_path).unlink(missing_ok=True)

    def test_tc2_1_received_email_with_request_is_action(self, tracker):
        """TC2.1: Received email with 'can you send' → ACTION"""
        email = {
            "folder": "Inbox",
            "content": "Hi, can you send me the report?",
            "sender": "client@example.com",
            "subject": "Report Request"
        }

        action_type = tracker.classify_action_type(email)

        assert action_type == ActionType.ACTION

    def test_tc2_2_sent_email_with_request_is_waiting(self, tracker):
        """TC2.2: Sent email with 'please provide' → WAITING"""
        email = {
            "folder": "Sent",
            "content": "Please provide the cost report by Monday",
            "sender": "me@company.com",
            "subject": "Cost Report Request"
        }

        action_type = tracker.classify_action_type(email)

        assert action_type == ActionType.WAITING

    def test_tc2_3_received_email_without_request_defaults_action(self, tracker):
        """TC2.3: Received email without request → ACTION (default)"""
        email = {
            "folder": "Inbox",
            "content": "Here is some information",
            "sender": "info@example.com",
            "subject": "FYI"
        }

        action_type = tracker.classify_action_type(email)

        assert action_type == ActionType.ACTION

    def test_tc2_4_multiple_request_patterns(self, tracker):
        """TC2.4: Email with multiple request patterns"""
        email = {
            "folder": "Inbox",
            "content": "Can you send the report? Also, could you provide an update?",
            "sender": "manager@example.com",
            "subject": "Multiple Requests"
        }

        has_request = tracker.contains_request_patterns(email)

        assert has_request is True


class TestStatusStateMachine:
    """Test R3: Status State Machine"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        tracker = EmailActionTracker(db_path=db_path)
        yield tracker
        Path(db_path).unlink(missing_ok=True)

    def test_tc3_1_pending_to_replied_on_reply_detection(self, tracker):
        """TC3.1: PENDING → REPLIED on reply detection"""
        action_id = tracker.create_action(
            message_id="msg@reply",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.mark_replied(action_id)

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.REPLIED

    def test_tc3_2_pending_to_overdue_when_deadline_passes(self, tracker):
        """TC3.2: PENDING → OVERDUE when deadline passes"""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()

        action_id = tracker.create_action(
            message_id="msg@overdue",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH",
            deadline=yesterday
        )

        tracker.check_overdue_actions()

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.OVERDUE

    def test_tc3_3_replied_to_completed_with_keywords(self, tracker):
        """TC3.3: REPLIED → COMPLETED with completion keywords"""
        action_id = tracker.create_action(
            message_id="msg@complete",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.mark_replied(action_id)

        reply_content = "Attached the report. Task is done."
        intent = tracker.detect_reply_intent(reply_content)

        if intent.intent == ReplyIntent.COMPLETED and intent.confidence >= 0.7:
            tracker.update_action_status(action_id, ActionStatus.COMPLETED)

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.COMPLETED

    def test_tc3_4_replied_to_stalled_after_7_days(self, tracker):
        """TC3.4: REPLIED → STALLED after 7 days + 2 replies"""
        action_id = tracker.create_action(
            message_id="msg@stall",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        # Simulate 3 replies over 8 days
        tracker.mark_replied(action_id)
        tracker.increment_reply_count(action_id)
        tracker.increment_reply_count(action_id)

        # Manually set last_reply_date to 8 days ago
        eight_days_ago = (datetime.now() - timedelta(days=8)).isoformat()
        tracker.update_last_reply_date(action_id, eight_days_ago)

        tracker.check_stalled_conversations()

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.STALLED

    def test_tc3_5_invalid_transition_raises_error(self, tracker):
        """TC3.5: Invalid state transition raises error"""
        action_id = tracker.create_action(
            message_id="msg@invalid",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        # Mark as completed first
        tracker.update_action_status(action_id, ActionStatus.COMPLETED)

        # Try to mark as pending (invalid)
        with pytest.raises(ValueError, match="Invalid state transition"):
            tracker.update_action_status(action_id, ActionStatus.PENDING)


class TestReplyDetection:
    """Test R4: Automatic Reply Detection"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        tracker = EmailActionTracker(db_path=db_path)
        yield tracker
        Path(db_path).unlink(missing_ok=True)

    def test_tc4_1_reply_with_re_subject_matches_action(self, tracker):
        """TC4.1: Reply with 'Re: Subject' matches action"""
        action_id = tracker.create_action(
            message_id="original@msg",
            subject="Report Request",
            sender="client@test.com",
            action_description="Send report",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        sent_email = {
            "subject": "Re: Report Request",
            "message_id": "reply@msg",
            "folder": "Sent"
        }

        matched = tracker.is_reply_to_action(sent_email, action_id)

        assert matched is True

    def test_tc4_2_reply_increments_reply_count(self, tracker):
        """TC4.2: Reply increments reply_count"""
        action_id = tracker.create_action(
            message_id="msg@count",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        action_before = tracker.get_action(action_id)
        assert action_before["reply_count"] == 0

        tracker.mark_replied(action_id)

        action_after = tracker.get_action(action_id)
        assert action_after["reply_count"] == 1

    def test_tc4_3_first_reply_changes_status_to_replied(self, tracker):
        """TC4.3: First reply changes status to REPLIED"""
        action_id = tracker.create_action(
            message_id="msg@first",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.mark_replied(action_id)

        action = tracker.get_action(action_id)
        assert action["status"] == ActionStatus.REPLIED

    def test_tc4_4_multiple_replies_to_same_action(self, tracker):
        """TC4.4: Multiple replies to same action"""
        action_id = tracker.create_action(
            message_id="msg@multi",
            subject="Test",
            sender="test@test.com",
            action_description="Task",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        tracker.mark_replied(action_id)
        tracker.increment_reply_count(action_id)
        tracker.increment_reply_count(action_id)

        action = tracker.get_action(action_id)
        assert action["reply_count"] == 3

    def test_tc4_5_reply_to_different_thread_no_match(self, tracker):
        """TC4.5: Reply to different thread doesn't match"""
        action_id = tracker.create_action(
            message_id="msg@a",
            subject="Subject A",
            sender="test@test.com",
            action_description="Task A",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        sent_email = {
            "subject": "Re: Subject B",  # Different subject
            "message_id": "reply@b",
            "folder": "Sent"
        }

        matched = tracker.is_reply_to_action(sent_email, action_id)

        assert matched is False


class TestCompletionDetection:
    """Test R5: Completion Detection (Gemma2 9B)"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        tracker = EmailActionTracker(db_path=db_path)
        yield tracker
        Path(db_path).unlink(missing_ok=True)

    def test_tc5_1_attached_export_indicates_completed(self, tracker):
        """TC5.1: 'Attached the export' → COMPLETED"""
        reply_text = "Hi, attached the export as requested."

        intent = tracker.detect_reply_intent(reply_text)

        assert intent.intent == ReplyIntent.COMPLETED
        assert intent.confidence >= 0.7

    def test_tc5_2_working_on_it_indicates_in_progress(self, tracker):
        """TC5.2: 'Working on it' → IN_PROGRESS"""
        reply_text = "I'm currently working on this, will send by EOD."

        intent = tracker.detect_reply_intent(reply_text)

        assert intent.intent == ReplyIntent.IN_PROGRESS
        assert intent.confidence >= 0.7

    def test_tc5_3_which_export_indicates_clarifying(self, tracker):
        """TC5.3: 'Which export?' → CLARIFYING"""
        reply_text = "Which export did you need specifically?"

        intent = tracker.detect_reply_intent(reply_text)

        assert intent.intent == ReplyIntent.CLARIFYING
        assert intent.confidence >= 0.7

    def test_tc5_4_cant_do_indicates_declined(self, tracker):
        """TC5.4: 'Can't do this' → DECLINED"""
        reply_text = "Unfortunately, I can't complete this task."

        intent = tracker.detect_reply_intent(reply_text)

        assert intent.intent == ReplyIntent.DECLINED
        assert intent.confidence >= 0.7

    def test_tc5_5_low_confidence_no_auto_change(self, tracker):
        """TC5.5: Low confidence (<0.7) → no automatic status change"""
        reply_text = "Thanks"  # Ambiguous

        intent = tracker.detect_reply_intent(reply_text)

        # Should have low confidence or be ACKNOWLEDGED
        assert intent.confidence < 0.7 or intent.intent == ReplyIntent.ACKNOWLEDGED


class TestBriefIntegration:
    """Test R9: Integration with Email Intelligence Brief"""

    @pytest.fixture
    def tracker(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        tracker = EmailActionTracker(db_path=db_path)
        yield tracker
        Path(db_path).unlink(missing_ok=True)

    def test_tc9_1_format_brief_with_zero_actions(self, tracker):
        """TC9.1: Format brief with 0 actions"""
        brief = tracker.format_action_dashboard()

        assert "0 items" in brief or "No actions" in brief

    def test_tc9_2_format_brief_with_all_states(self, tracker):
        """TC9.2: Format brief with actions in all states"""
        # Create actions in different states
        overdue_id = tracker.create_action(
            message_id="msg@overdue",
            subject="Overdue Task",
            sender="test@test.com",
            action_description="Overdue",
            action_type=ActionType.ACTION,
            priority="HIGH",
            deadline=(datetime.now() - timedelta(days=1)).isoformat()
        )
        tracker.check_overdue_actions()

        tracker.create_action(
            message_id="msg@pending",
            subject="Pending Task",
            sender="test@test.com",
            action_description="Pending",
            action_type=ActionType.ACTION,
            priority="HIGH"
        )

        brief = tracker.format_action_dashboard()

        assert "OVERDUE" in brief
        assert "PENDING" in brief

    def test_tc9_3_performance_100_actions_under_2_sec(self, tracker):
        """TC9.3: Performance: 100 actions < 2 seconds"""
        import time

        # Create 100 actions
        for i in range(100):
            tracker.create_action(
                message_id=f"msg@{i}",
                subject=f"Task {i}",
                sender="test@test.com",
                action_description=f"Task {i}",
                action_type=ActionType.ACTION,
                priority="MEDIUM"
            )

        start = time.time()
        brief = tracker.format_action_dashboard()
        elapsed = time.time() - start

        assert elapsed < 2.0
        assert brief is not None

    def test_tc9_4_correct_sorting_within_categories(self, tracker):
        """TC9.4: Correct sorting within each category"""
        # Create overdue actions with different urgency
        tracker.create_action(
            message_id="msg@overdue1",
            subject="Overdue 1",
            sender="test@test.com",
            action_description="Overdue 1 day",
            action_type=ActionType.ACTION,
            priority="HIGH",
            deadline=(datetime.now() - timedelta(days=1)).isoformat()
        )

        tracker.create_action(
            message_id="msg@overdue3",
            subject="Overdue 3",
            sender="test@test.com",
            action_description="Overdue 3 days",
            action_type=ActionType.ACTION,
            priority="HIGH",
            deadline=(datetime.now() - timedelta(days=3)).isoformat()
        )

        tracker.check_overdue_actions()

        overdue_actions = tracker.get_overdue_actions()

        # Should be sorted by most overdue first (3 days before 1 day)
        assert len(overdue_actions) == 2
        assert "Overdue 3" in overdue_actions[0]["subject"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
