#!/usr/bin/env python3
"""
Conversation Logger - Weekly Maia Journey Narrative System

Captures Maia-user collaborative problem-solving conversations and synthesizes
them into conversational weekly narratives for team sharing.

Purpose:
- Log conversation journeys (problem → options → refinement → solution)
- Track agents used, deliverables created, business impact
- Support privacy-first sharing (default private, opt-in to team)
- Enable weekly narrative synthesis

Database Schema:
- journey_id: UUID for unique journey identification
- timestamp: ISO 8601 format
- problem_description: User's initial pain point
- initial_question: Exact user query
- maia_options_presented: JSON array of options
- user_refinement_quote: User's actual feedback
- agents_used: JSON array of agent objects
- deliverables: JSON array of deliverable objects
- business_impact: Quantified impact statement
- meta_learning: System/workflow insights discovered
- iteration_count: Number of refinement iterations
- privacy_flag: Default True (private), False = shareable
- schema_version: Schema version (1)

Performance SLOs:
- Log operations: <50ms
- Weekly retrieval: <200ms
- Graceful degradation: Never block user workflow

Author: SRE Principal Engineer Agent
Date: 2025-11-12
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationLogger:
    """
    Conversation logging system for Maia journey narratives.

    Features:
    - Privacy-first (default private, opt-in to sharing)
    - Multi-agent tracking
    - Deliverables tracking
    - Weekly retrieval (rolling 7 days)
    - Graceful degradation (never blocks workflow)
    """

    SCHEMA_VERSION = 1
    DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "databases" / "system" / "conversations.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize conversation logger.

        Args:
            db_path: Optional custom database path (defaults to databases/system/conversations.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema if not exists."""
        try:
            # Ensure parent directories exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    journey_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    problem_description TEXT,
                    initial_question TEXT,
                    maia_options_presented TEXT,
                    user_refinement_quote TEXT,
                    agents_used TEXT,
                    deliverables TEXT,
                    business_impact TEXT,
                    meta_learning TEXT,
                    iteration_count INTEGER DEFAULT 0,
                    privacy_flag INTEGER DEFAULT 1,
                    schema_version INTEGER DEFAULT 1
                )
            """)

            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_privacy_flag ON conversations(privacy_flag)")

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Graceful degradation - log error but don't crash

    def start_journey(
        self,
        problem_description: str,
        initial_question: str
    ) -> Optional[str]:
        """
        Start a new conversation journey.

        Args:
            problem_description: User's initial pain point
            initial_question: Exact user query

        Returns:
            journey_id (UUID) if successful, None if DB unavailable
        """
        try:
            journey_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO conversations (
                    journey_id, timestamp, problem_description, initial_question,
                    privacy_flag, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (journey_id, timestamp, problem_description, initial_question, 1, self.SCHEMA_VERSION))

            conn.commit()
            conn.close()

            logger.info(f"Started journey {journey_id}")
            return journey_id

        except Exception as e:
            logger.error(f"Failed to start journey: {e}")
            return None

    def log_maia_response(
        self,
        journey_id: str,
        options_presented: List[str]
    ) -> bool:
        """
        Log Maia's response options.

        Args:
            journey_id: Journey UUID
            options_presented: List of option strings

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversations
                SET maia_options_presented = ?
                WHERE journey_id = ?
            """, (json.dumps(options_presented), journey_id))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Failed to log Maia response: {e}")
            return False

    def log_user_refinement(
        self,
        journey_id: str,
        refinement_quote: str
    ) -> bool:
        """
        Log user's refinement feedback.

        Args:
            journey_id: Journey UUID
            refinement_quote: User's actual feedback quote

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversations
                SET user_refinement_quote = ?
                WHERE journey_id = ?
            """, (refinement_quote, journey_id))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Failed to log user refinement: {e}")
            return False

    def add_agent(
        self,
        journey_id: str,
        agent_name: str,
        rationale: str
    ) -> Optional[bool]:
        """
        Add agent to journey tracking.

        Args:
            journey_id: Journey UUID
            agent_name: Name of agent (e.g., "SRE Principal Engineer")
            rationale: Why this agent was engaged

        Returns:
            True if successful, False/None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current agents_used
            cursor.execute("SELECT agents_used FROM conversations WHERE journey_id = ?", (journey_id,))
            row = cursor.fetchone()

            if row is None:
                logger.error(f"Journey {journey_id} not found")
                conn.close()
                return False

            # Parse existing agents or start fresh
            try:
                agents = json.loads(row[0]) if row[0] else []
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Corrupt agents_used data for journey {journey_id}, resetting")
                agents = []

            # Add new agent
            agents.append({
                "agent": agent_name,
                "rationale": rationale,
                "started_at": datetime.now().isoformat()
            })

            # Update database
            cursor.execute("""
                UPDATE conversations
                SET agents_used = ?
                WHERE journey_id = ?
            """, (json.dumps(agents), journey_id))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Failed to add agent: {e}")
            return None

    def add_deliverable(
        self,
        journey_id: str,
        deliverable_type: str,
        name: str,
        description: str,
        size: str
    ) -> bool:
        """
        Add deliverable to journey tracking.

        Args:
            journey_id: Journey UUID
            deliverable_type: "file", "documentation", "analysis", etc.
            name: Deliverable name
            description: Brief description
            size: Human-readable size (e.g., "9.8KB")

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current deliverables
            cursor.execute("SELECT deliverables FROM conversations WHERE journey_id = ?", (journey_id,))
            row = cursor.fetchone()

            if row is None:
                logger.error(f"Journey {journey_id} not found")
                conn.close()
                return False

            # Parse existing deliverables or start fresh
            deliverables = json.loads(row[0]) if row[0] else []

            # Add new deliverable
            deliverables.append({
                "type": deliverable_type,
                "name": name,
                "description": description,
                "size": size
            })

            # Update database
            cursor.execute("""
                UPDATE conversations
                SET deliverables = ?
                WHERE journey_id = ?
            """, (json.dumps(deliverables), journey_id))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Failed to add deliverable: {e}")
            return False

    def complete_journey(
        self,
        journey_id: str,
        business_impact: str,
        meta_learning: str,
        iteration_count: int
    ) -> bool:
        """
        Finalize journey with metadata.

        Args:
            journey_id: Journey UUID
            business_impact: Quantified impact statement
            meta_learning: System/workflow insights discovered
            iteration_count: Number of refinement iterations

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversations
                SET business_impact = ?,
                    meta_learning = ?,
                    iteration_count = ?
                WHERE journey_id = ?
            """, (business_impact, meta_learning, iteration_count, journey_id))

            conn.commit()
            conn.close()

            logger.info(f"Completed journey {journey_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to complete journey: {e}")
            return False

    def mark_shareable(self, journey_id: str) -> bool:
        """
        Mark journey as shareable (opt-in to team sharing).

        Args:
            journey_id: Journey UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversations
                SET privacy_flag = 0
                WHERE journey_id = ?
            """, (journey_id,))

            conn.commit()
            conn.close()

            logger.info(f"Marked journey {journey_id} as shareable")
            return True

        except Exception as e:
            logger.error(f"Failed to mark shareable: {e}")
            return False

    def get_week_journeys(self, include_private: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve journeys from last 7 days.

        Args:
            include_private: If False (default), only return shareable journeys

        Returns:
            List of journey dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dictionary access
            cursor = conn.cursor()

            # Calculate 7 days ago
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

            # Build query based on privacy preference
            if include_private:
                cursor.execute("""
                    SELECT * FROM conversations
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (seven_days_ago,))
            else:
                cursor.execute("""
                    SELECT * FROM conversations
                    WHERE timestamp >= ? AND privacy_flag = 0
                    ORDER BY timestamp DESC
                """, (seven_days_ago,))

            rows = cursor.fetchall()
            conn.close()

            # Convert rows to dictionaries and parse JSON fields
            journeys = []
            for row in rows:
                journey = dict(row)

                # Parse JSON fields
                for field in ['maia_options_presented', 'agents_used', 'deliverables']:
                    if journey[field]:
                        try:
                            journey[field] = json.loads(journey[field])
                        except json.JSONDecodeError:
                            journey[field] = None

                journeys.append(journey)

            return journeys

        except Exception as e:
            logger.error(f"Failed to retrieve week journeys: {e}")
            return []


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: conversation_logger.py <command> [args...]")
        print("Commands:")
        print("  start <problem> <question>")
        print("  list [--include-private]")
        print("  mark-shareable <journey_id>")
        sys.exit(1)

    logger_instance = ConversationLogger()
    command = sys.argv[1]

    if command == 'start':
        problem = sys.argv[2] if len(sys.argv) > 2 else "Test problem"
        question = sys.argv[3] if len(sys.argv) > 3 else "Test question?"
        journey_id = logger_instance.start_journey(problem, question)
        print(f"Started journey: {journey_id}")

    elif command == 'list':
        include_private = '--include-private' in sys.argv
        journeys = logger_instance.get_week_journeys(include_private=include_private)
        print(f"Found {len(journeys)} journeys:")
        for j in journeys:
            privacy = "PRIVATE" if j['privacy_flag'] else "SHAREABLE"
            print(f"  [{privacy}] {j['journey_id']}: {j['problem_description']}")

    elif command == 'mark-shareable':
        journey_id = sys.argv[2]
        logger_instance.mark_shareable(journey_id)
        print(f"Marked {journey_id} as shareable")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
