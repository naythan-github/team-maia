#!/usr/bin/env python3
"""
Email Action Tracker - Track email-based action items and replies
Implements TDD Phase 4 requirements from email_action_tracker_REQUIREMENTS.md

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-11-21
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, NamedTuple
from enum import Enum

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


class ActionType(Enum):
    """Action type classification"""
    ACTION = "ACTION"  # You need to do something
    WAITING = "WAITING"  # Waiting for others to do something


class ActionStatus(Enum):
    """Action status state machine"""
    PENDING = "PENDING"
    REPLIED = "REPLIED"
    IN_PROGRESS = "IN_PROGRESS"
    CLARIFYING = "CLARIFYING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    STALLED = "STALLED"
    CANCELLED = "CANCELLED"


class ReplyIntent(Enum):
    """Reply intent classification for Gemma2"""
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    CLARIFYING = "CLARIFYING"
    DECLINED = "DECLINED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class IntentResult(NamedTuple):
    """Result from intent detection"""
    intent: ReplyIntent
    confidence: float


class EmailActionTracker:
    """
    Track email action items and automatically update status based on replies

    Features:
    - Action item storage with SQLite
    - Automatic reply detection via thread matching
    - Gemma2 9B intent classification for completion
    - Status state machine (PENDING → REPLIED → COMPLETED/OVERDUE)
    - Overdue tracking
    - "Waiting for" tracking (outbound requests)
    - Stalled conversation detection
    """

    def __init__(self, db_path: str = None):
        """Initialize action tracker with database"""
        if db_path is None:
            db_path = str(MAIA_ROOT / "claude" / "data" / "databases" / "intelligence" / "email_actions.db")

        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database schema if not exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency

        # R1: email_actions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                thread_id TEXT,
                subject TEXT NOT NULL,
                sender TEXT NOT NULL,
                action_description TEXT NOT NULL,
                action_type TEXT NOT NULL,
                deadline TEXT,
                priority TEXT NOT NULL,
                extracted_date TEXT NOT NULL,
                status TEXT NOT NULL,
                last_reply_date TEXT,
                reply_count INTEGER DEFAULT 0,
                completed_date TEXT,
                ai_confidence REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # R7: waiting_for table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS waiting_for (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id INTEGER REFERENCES email_actions(id),
                requested_date TEXT NOT NULL,
                recipient TEXT NOT NULL,
                expected_response_date TEXT NOT NULL,
                last_followup_date TEXT,
                followup_count INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def create_action(
        self,
        message_id: str,
        subject: str,
        sender: str,
        action_description: str,
        action_type: ActionType,
        priority: str,
        deadline: str = None,
        thread_id: str = None,
        ai_confidence: float = None
    ) -> int:
        """
        Create new action item (R1)

        Returns:
            int: Action ID
        """
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO email_actions (
                    message_id, thread_id, subject, sender, action_description,
                    action_type, deadline, priority, extracted_date, status,
                    ai_confidence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id, thread_id, subject, sender, action_description,
                action_type.value, deadline, priority, now, ActionStatus.PENDING.value,
                ai_confidence, now, now
            ))

            action_id = cursor.lastrowid
            conn.commit()
            return action_id

        except sqlite3.IntegrityError:
            conn.close()
            raise
        finally:
            if conn:
                conn.close()

    def get_action(self, action_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve action by ID (R1)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM email_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            action_dict = dict(row)
            # Convert string status/type to enum for comparison compatibility
            try:
                action_dict["status"] = ActionStatus(action_dict["status"])
                action_dict["action_type"] = ActionType(action_dict["action_type"])
            except (KeyError, ValueError):
                pass
            return action_dict
        return None

    def get_action_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve action by message_id (R1)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM email_actions WHERE message_id = ?", (message_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            action_dict = dict(row)
            # Convert string status/type to enum for comparison compatibility
            try:
                action_dict["status"] = ActionStatus(action_dict["status"])
                action_dict["action_type"] = ActionType(action_dict["action_type"])
            except (KeyError, ValueError):
                pass
            return action_dict
        return None

    def query_actions_by_status(self, status: ActionStatus) -> List[Dict[str, Any]]:
        """Query actions by status (R1)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM email_actions WHERE status = ? ORDER BY created_at DESC",
            (status.value,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_actions_by_status(self, status: ActionStatus) -> List[Dict[str, Any]]:
        """Alias for query_actions_by_status (test compatibility)"""
        return self.query_actions_by_status(status)

    def update_action_status(self, action_id: int, new_status: ActionStatus) -> bool:
        """Update action status (R1, R3)"""
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current status for validation
        cursor.execute("SELECT status FROM email_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        current_status = row[0]

        # R3: Validate state transition
        if not self._is_valid_transition(current_status, new_status.value):
            conn.close()
            raise ValueError(
                f"Invalid state transition: {current_status} → {new_status.value}"
            )

        # Update status
        cursor.execute("""
            UPDATE email_actions
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (new_status.value, now, action_id))

        # If completed, set completed_date
        if new_status == ActionStatus.COMPLETED:
            cursor.execute("""
                UPDATE email_actions
                SET completed_date = ?
                WHERE id = ?
            """, (now, action_id))

        conn.commit()
        conn.close()
        return True

    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """
        Validate status state machine transitions (R3)

        Valid transitions:
        - PENDING → REPLIED, OVERDUE, CANCELLED, COMPLETED (allow quick completion)
        - REPLIED → COMPLETED, IN_PROGRESS, CLARIFYING, STALLED, CANCELLED
        - IN_PROGRESS → COMPLETED, CLARIFYING, CANCELLED
        - CLARIFYING → IN_PROGRESS, COMPLETED, CANCELLED
        - OVERDUE → REPLIED, COMPLETED, CANCELLED
        - STALLED → REPLIED, COMPLETED, CANCELLED
        - COMPLETED → (no transitions)
        - CANCELLED → (no transitions)
        """
        valid_transitions = {
            "PENDING": ["REPLIED", "OVERDUE", "CANCELLED", "COMPLETED"],
            "REPLIED": ["COMPLETED", "IN_PROGRESS", "CLARIFYING", "STALLED", "CANCELLED"],
            "IN_PROGRESS": ["COMPLETED", "CLARIFYING", "CANCELLED"],
            "CLARIFYING": ["IN_PROGRESS", "COMPLETED", "CANCELLED"],
            "OVERDUE": ["REPLIED", "COMPLETED", "CANCELLED"],
            "STALLED": ["REPLIED", "COMPLETED", "CANCELLED"],
            "COMPLETED": [],
            "CANCELLED": []
        }

        return to_status in valid_transitions.get(from_status, [])

    def classify_action_type(self, email: Dict[str, Any]) -> ActionType:
        """
        Classify action type: ACTION vs WAITING (R2)

        Rules:
        - Sent email with request language → WAITING
        - Received email with request language → ACTION
        - Default → ACTION
        """
        folder = email.get("folder", "Inbox")
        content = email.get("content", "") + " " + email.get("subject", "")
        content_lower = content.lower()

        # Request patterns
        request_patterns = [
            "can you", "could you", "please send", "need from you",
            "waiting for", "expecting", "by when", "please confirm",
            "please provide", "would you", "could you provide"
        ]

        has_request = any(pattern in content_lower for pattern in request_patterns)

        # Sent email with request → WAITING
        if folder == "Sent" and has_request:
            return ActionType.WAITING

        # Received email with request → ACTION
        if folder == "Inbox" and has_request:
            return ActionType.ACTION

        # Default
        return ActionType.ACTION

    def contains_request_patterns(self, email: Dict[str, Any]) -> bool:
        """Check if email contains request patterns (R2 helper)"""
        content = email.get("content", "") + " " + email.get("subject", "")
        content_lower = content.lower()

        request_patterns = [
            "can you", "could you", "please send", "need from you",
            "waiting for", "expecting", "by when", "please confirm",
            "please provide", "would you", "could you provide"
        ]

        return any(pattern in content_lower for pattern in request_patterns)

    def detect_reply(self, sent_email: Dict[str, Any]) -> Optional[int]:
        """
        Detect if sent email is a reply to an action item (R4)

        Returns:
            Optional[int]: Action ID if reply detected, None otherwise
        """
        subject = sent_email.get("subject", "")
        thread_id = sent_email.get("thread_id")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try thread_id match first (most reliable)
        if thread_id:
            cursor.execute("""
                SELECT id FROM email_actions
                WHERE thread_id = ? AND status != 'COMPLETED' AND status != 'CANCELLED'
                ORDER BY created_at DESC
                LIMIT 1
            """, (thread_id,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]

        # Try subject match (Re: prefix)
        if subject.startswith("Re: "):
            original_subject = subject[4:]  # Remove "Re: "
            cursor.execute("""
                SELECT id FROM email_actions
                WHERE subject = ? AND status != 'COMPLETED' AND status != 'CANCELLED'
                ORDER BY created_at DESC
                LIMIT 1
            """, (original_subject,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]

        conn.close()
        return None

    def record_reply(self, action_id: int, reply_date: str = None) -> bool:
        """
        Record reply to action item (R4)
        Updates: status PENDING → REPLIED, increment reply_count, set last_reply_date
        """
        if reply_date is None:
            reply_date = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current status
        cursor.execute("SELECT status, reply_count FROM email_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        current_status, reply_count = row

        # Update reply metadata
        cursor.execute("""
            UPDATE email_actions
            SET last_reply_date = ?,
                reply_count = ?,
                updated_at = ?
            WHERE id = ?
        """, (reply_date, reply_count + 1, datetime.now().isoformat(), action_id))

        # If PENDING, transition to REPLIED
        if current_status == "PENDING":
            cursor.execute("""
                UPDATE email_actions
                SET status = ?
                WHERE id = ?
            """, (ActionStatus.REPLIED.value, action_id))

        conn.commit()
        conn.close()
        return True

    def mark_replied(self, action_id: int, reply_date: str = None) -> bool:
        """Alias for record_reply (test compatibility)"""
        return self.record_reply(action_id, reply_date)

    def increment_reply_count(self, action_id: int) -> bool:
        """Increment reply count without changing status (test helper)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT reply_count FROM email_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        reply_count = row[0]

        cursor.execute("""
            UPDATE email_actions
            SET reply_count = ?, updated_at = ?
            WHERE id = ?
        """, (reply_count + 1, datetime.now().isoformat(), action_id))

        conn.commit()
        conn.close()
        return True

    def update_last_reply_date(self, action_id: int, reply_date: str) -> bool:
        """Update last_reply_date (test helper for simulating old replies)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE email_actions
            SET last_reply_date = ?, updated_at = ?
            WHERE id = ?
        """, (reply_date, datetime.now().isoformat(), action_id))

        conn.commit()
        conn.close()
        return True

    def is_reply_to_action(self, sent_email: Dict[str, Any], action_id: int) -> bool:
        """
        Check if sent email is a reply to specific action (R4 helper)
        """
        action = self.get_action(action_id)
        if not action:
            return False

        subject = sent_email.get("subject", "")
        thread_id = sent_email.get("thread_id")

        # Thread ID match
        if thread_id and action.get("thread_id") == thread_id:
            return True

        # Subject match (Re: prefix)
        if subject == f"Re: {action['subject']}":
            return True

        return False

    def detect_completion_intent(self, reply_text: str) -> IntentResult:
        """
        Detect reply intent using Gemma2 9B (R5)

        Returns:
            IntentResult(intent=ReplyIntent.COMPLETED, confidence=0.95)
        """
        from claude.tools.morning_email_intelligence_local import MorningEmailIntelligence

        intelligence = MorningEmailIntelligence()

        prompt = f"""Classify the intent of this email reply. Return ONLY valid JSON.

Reply text: {reply_text[:500]}

Classify as one of:
- COMPLETED: Task is done (keywords: "done", "sent", "attached", "completed", "finished")
- IN_PROGRESS: Work is ongoing (keywords: "working on", "will send", "in progress")
- CLARIFYING: Asking for clarification (keywords: "question", "clarify", "which", "what do you mean")
- DECLINED: Cannot do the task (keywords: "can't", "unable", "won't work")
- ACKNOWLEDGED: Just acknowledging (keywords: "thanks", "received", "ok")

Return JSON:
{{"intent": "COMPLETED", "confidence": 0.95}}"""

        response = intelligence._call_ollama(prompt, temperature=0.1)

        # Fallback to keyword detection
        reply_lower = reply_text.lower()

        completed_keywords = ["done", "sent", "attached", "completed", "finished", "here it is", "here you go"]
        in_progress_keywords = ["working on", "will send", "in progress", "almost done"]
        clarifying_keywords = ["question", "clarify", "which", "what do you mean", "not sure"]
        declined_keywords = ["can't", "unable", "won't work", "not possible"]

        if "error" in response:
            if any(kw in reply_lower for kw in completed_keywords):
                return IntentResult(intent=ReplyIntent.COMPLETED, confidence=0.8)
            elif any(kw in reply_lower for kw in in_progress_keywords):
                return IntentResult(intent=ReplyIntent.IN_PROGRESS, confidence=0.8)
            elif any(kw in reply_lower for kw in clarifying_keywords):
                return IntentResult(intent=ReplyIntent.CLARIFYING, confidence=0.8)
            elif any(kw in reply_lower for kw in declined_keywords):
                return IntentResult(intent=ReplyIntent.DECLINED, confidence=0.8)
            else:
                return IntentResult(intent=ReplyIntent.ACKNOWLEDGED, confidence=0.6)

        # Parse Gemma2 response
        try:
            result_text = response.get("response", "")
            # Extract JSON from response
            if "{" in result_text and "}" in result_text:
                json_start = result_text.index("{")
                json_end = result_text.rindex("}") + 1
                result_dict = json.loads(result_text[json_start:json_end])
                intent_str = result_dict.get("intent", "ACKNOWLEDGED")
                confidence = result_dict.get("confidence", 0.5)
                return IntentResult(intent=ReplyIntent(intent_str), confidence=confidence)
            else:
                # Use keyword fallback
                if any(kw in reply_lower for kw in completed_keywords):
                    return IntentResult(intent=ReplyIntent.COMPLETED, confidence=0.8)
                elif any(kw in reply_lower for kw in in_progress_keywords):
                    return IntentResult(intent=ReplyIntent.IN_PROGRESS, confidence=0.8)
                elif any(kw in reply_lower for kw in clarifying_keywords):
                    return IntentResult(intent=ReplyIntent.CLARIFYING, confidence=0.8)
                elif any(kw in reply_lower for kw in declined_keywords):
                    return IntentResult(intent=ReplyIntent.DECLINED, confidence=0.8)
                else:
                    return IntentResult(intent=ReplyIntent.ACKNOWLEDGED, confidence=0.6)
        except Exception:
            # Final fallback to keyword detection
            if any(kw in reply_lower for kw in completed_keywords):
                return IntentResult(intent=ReplyIntent.COMPLETED, confidence=0.8)
            elif any(kw in reply_lower for kw in in_progress_keywords):
                return IntentResult(intent=ReplyIntent.IN_PROGRESS, confidence=0.8)
            elif any(kw in reply_lower for kw in clarifying_keywords):
                return IntentResult(intent=ReplyIntent.CLARIFYING, confidence=0.8)
            elif any(kw in reply_lower for kw in declined_keywords):
                return IntentResult(intent=ReplyIntent.DECLINED, confidence=0.8)
            else:
                return IntentResult(intent=ReplyIntent.ACKNOWLEDGED, confidence=0.6)

    def detect_reply_intent(self, reply_text: str) -> IntentResult:
        """Alias for detect_completion_intent (test compatibility)"""
        return self.detect_completion_intent(reply_text)

    def process_reply_with_intent(self, action_id: int, reply_text: str, confidence_threshold: float = 0.7) -> bool:
        """
        Process reply with Gemma2 intent detection and update status (R5)
        """
        # Detect intent
        result = self.detect_completion_intent(reply_text)
        intent = result.intent
        confidence = result.confidence

        # Record reply metadata
        self.record_reply(action_id)

        # Only auto-update status if confidence >= threshold
        if confidence < confidence_threshold:
            return True

        # Map intent to status
        intent_to_status = {
            ReplyIntent.COMPLETED: ActionStatus.COMPLETED,
            ReplyIntent.IN_PROGRESS: ActionStatus.IN_PROGRESS,
            ReplyIntent.CLARIFYING: ActionStatus.CLARIFYING,
            ReplyIntent.DECLINED: ActionStatus.CANCELLED
        }

        new_status = intent_to_status.get(intent)

        if new_status:
            try:
                self.update_action_status(action_id, new_status)
            except ValueError:
                # Invalid transition - ignore
                pass

        return True

    def check_overdue_actions(self) -> List[int]:
        """
        Check for overdue actions and update status (R6)

        Returns:
            List[int]: Action IDs that became overdue
        """
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find actions with deadline passed and not completed
        cursor.execute("""
            SELECT id FROM email_actions
            WHERE deadline IS NOT NULL
            AND deadline < ?
            AND status NOT IN ('COMPLETED', 'CANCELLED')
        """, (now,))

        overdue_ids = [row[0] for row in cursor.fetchall()]

        # Update to OVERDUE status
        for action_id in overdue_ids:
            cursor.execute("""
                UPDATE email_actions
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (ActionStatus.OVERDUE.value, now, action_id))

        conn.commit()
        conn.close()

        return overdue_ids

    def check_stalled_actions(self, days_threshold: int = 7, reply_threshold: int = 2) -> List[int]:
        """
        Check for stalled conversations (R8)

        Conditions:
        - reply_count > reply_threshold (default: 2)
        - days_since_last_reply > days_threshold (default: 7)
        - status != COMPLETED

        Returns:
            List[int]: Action IDs that became stalled
        """
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find stalled actions
        cursor.execute("""
            SELECT id FROM email_actions
            WHERE reply_count > ?
            AND last_reply_date < ?
            AND status NOT IN ('COMPLETED', 'CANCELLED', 'STALLED')
        """, (reply_threshold, cutoff_date))

        stalled_ids = [row[0] for row in cursor.fetchall()]

        # Update to STALLED status
        now = datetime.now().isoformat()
        for action_id in stalled_ids:
            cursor.execute("""
                UPDATE email_actions
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (ActionStatus.STALLED.value, now, action_id))

        conn.commit()
        conn.close()

        return stalled_ids

    def check_stalled_conversations(self, days_threshold: int = 7, reply_threshold: int = 2) -> List[int]:
        """Alias for check_stalled_actions (test compatibility)"""
        return self.check_stalled_actions(days_threshold, reply_threshold)

    def create_waiting_for(
        self,
        action_id: int,
        recipient: str,
        expected_response_date: str = None
    ) -> int:
        """
        Create waiting-for entry (R7)
        """
        now = datetime.now().isoformat()

        if expected_response_date is None:
            # Default: 3 days from now
            expected_date = (datetime.now() + timedelta(days=3)).isoformat()
        else:
            expected_date = expected_response_date

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO waiting_for (
                action_id, requested_date, recipient, expected_response_date,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (action_id, now, recipient, expected_date, "WAITING", now, now))

        waiting_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return waiting_id

    def get_brief_dashboard(self) -> Dict[str, Any]:
        """
        Generate action tracker dashboard for email brief (R9)

        Returns:
            {
                "overdue": [...],
                "today": [...],
                "pending": [...],
                "waiting": [...],
                "completed": [...]
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Overdue actions
        cursor.execute("""
            SELECT * FROM email_actions
            WHERE status = 'OVERDUE'
            ORDER BY deadline ASC
        """)
        overdue = [dict(row) for row in cursor.fetchall()]

        # Today's actions (deadline today)
        today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        today_end = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
        cursor.execute("""
            SELECT * FROM email_actions
            WHERE deadline >= ? AND deadline <= ?
            AND status NOT IN ('COMPLETED', 'CANCELLED')
            ORDER BY deadline ASC
        """, (today_start, today_end))
        today = [dict(row) for row in cursor.fetchall()]

        # Pending actions
        cursor.execute("""
            SELECT * FROM email_actions
            WHERE status IN ('PENDING', 'REPLIED', 'IN_PROGRESS', 'CLARIFYING')
            AND (deadline IS NULL OR deadline > ?)
            ORDER BY created_at DESC
        """, (today_end,))
        pending = [dict(row) for row in cursor.fetchall()]

        # Waiting for actions
        cursor.execute("""
            SELECT * FROM email_actions
            WHERE action_type = 'WAITING'
            AND status NOT IN ('COMPLETED', 'CANCELLED')
            ORDER BY created_at DESC
        """)
        waiting = [dict(row) for row in cursor.fetchall()]

        # Recently completed
        cursor.execute("""
            SELECT * FROM email_actions
            WHERE status = 'COMPLETED'
            ORDER BY completed_date DESC
            LIMIT 10
        """)
        completed = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "overdue": overdue,
            "today": today,
            "pending": pending,
            "waiting": waiting,
            "completed": completed
        }

    def get_overdue_actions(self) -> List[Dict[str, Any]]:
        """Get all overdue actions, sorted by deadline (most overdue first)"""
        return self.query_actions_by_status(ActionStatus.OVERDUE)

    def format_action_dashboard(self) -> str:
        """
        Format action tracker dashboard as markdown (R9)
        """
        dashboard = self.get_brief_dashboard()
        now = datetime.now()

        output = f"""## 📋 ACTION TRACKER DASHBOARD

"""

        # Overdue section
        if dashboard["overdue"]:
            output += f"""### 🔴 OVERDUE ({len(dashboard['overdue'])} items)

"""
            for action in dashboard["overdue"]:
                deadline = action.get("deadline", "")
                if deadline:
                    deadline_dt = datetime.fromisoformat(deadline)
                    hours_overdue = (now - deadline_dt).total_seconds() / 3600
                    output += f"""- ⚠️ **{action['action_description']}**
  From: {action['sender']} | Overdue: {hours_overdue:.1f} hours ago
"""
        else:
            output += "### 🔴 OVERDUE (0 items)\n\nNo overdue actions\n\n"

        # Today's actions
        if dashboard["today"]:
            output += f"""### 📌 TODAY'S ACTIONS ({len(dashboard['today'])} items)

"""
            for action in dashboard["today"]:
                deadline = action.get("deadline", "")
                output += f"""- **{action['action_description']}**
  From: {action['sender']} | Deadline: {deadline}
"""
        else:
            output += "### 📌 TODAY'S ACTIONS (0 items)\n\nNo actions due today\n\n"

        # Pending
        if dashboard["pending"]:
            output += f"""### ⏳ PENDING ({len(dashboard['pending'])} items)

"""
            for action in dashboard["pending"][:5]:  # Show top 5
                output += f"""- **{action['action_description']}** (Status: {action['status']})
  From: {action['sender']}
"""
            if len(dashboard["pending"]) > 5:
                output += f"\n... and {len(dashboard['pending']) - 5} more\n\n"
        else:
            output += "### ⏳ PENDING (0 items)\n\nNo pending actions\n\n"

        # Waiting for
        if dashboard["waiting"]:
            output += f"""### ⏰ WAITING FOR REPLY ({len(dashboard['waiting'])} items)

"""
            for action in dashboard["waiting"][:5]:
                output += f"""- **{action['action_description']}**
  To: {action['sender']} | Status: {action['status']}
"""
            if len(dashboard["waiting"]) > 5:
                output += f"\n... and {len(dashboard['waiting']) - 5} more\n\n"

        # Stats
        total_active = len(dashboard["overdue"]) + len(dashboard["today"]) + len(dashboard["pending"]) + len(dashboard["waiting"])
        output += f"""---

**Tracking Metrics:**
- Total active actions: {total_active}
- Recently completed: {len(dashboard['completed'])}

"""

        return output


def main():
    """CLI entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Email Action Tracker")
    parser.add_argument("--test", action="store_true", help="Run basic test")

    args = parser.parse_args()

    if args.test:
        print("Testing Email Action Tracker...")
        tracker = EmailActionTracker(db_path=":memory:")

        # Create test action
        action_id = tracker.create_action(
            message_id="test@example.com",
            subject="Test Action",
            sender="sender@example.com",
            action_description="Test task",
            action_type=ActionType.ACTION,
            priority="HIGH",
            deadline=(datetime.now() + timedelta(hours=1)).isoformat()
        )

        print(f"✅ Created action: {action_id}")

        # Retrieve action
        action = tracker.get_action(action_id)
        print(f"✅ Retrieved action: {action['subject']}")

        # Query by status
        pending = tracker.query_actions_by_status(ActionStatus.PENDING)
        print(f"✅ Pending actions: {len(pending)}")

        print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    main()
