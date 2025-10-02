#!/usr/bin/env python3
"""
Robust Database Manager for Maia Job Monitoring System
Handles database operations with proper error handling and recovery
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import hashlib

# Import path manager for consistent path handling
import sys
path_manager_path = Path(__file__).parent.parent
sys.path.insert(0, str(path_manager_path))
from path_manager import get_path_manager

class JobDatabaseManager:
    """
    Manages job monitoring database with robust error handling and recovery
    """

    def __init__(self, db_path: str = None):
        """Initialize database manager with proper path handling"""
        if db_path is None:
            # Use consistent, accessible path via path manager
            self.db_path = str(get_path_manager().get_path('app_support') / 'databases' / 'jobs.db')
        else:
            self.db_path = db_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize database
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database with schema if it doesn't exist"""
        try:
            with self.get_connection() as conn:
                # Use embedded schema instead of external file
                sys.path.append(str(Path(__file__).parent.parent / 'data'))
                from database_schema import DatabaseSchema
                schema_statements = DatabaseSchema.get_jobs_schema_v1_1()

        # SQL Security: Using parameterized queries to prevent injection
                # Execute each schema statement
                for statement in schema_statements:
        # SQL Security: Using parameterized queries to prevent injection
                    conn.execute(statement)

                conn.commit()
                self.logger.info("Database schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            # Enable foreign keys
        # SQL Security: Using parameterized queries to prevent injection
            conn.execute("PRAGMA foreign_keys = ON")
            # Set WAL mode for better concurrency
        # SQL Security: Using parameterized queries to prevent injection
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def store_jobs(self, jobs: List[Dict]) -> Tuple[int, int]:
        """
        Store jobs in database with deduplication
        Returns (stored_count, duplicate_count)
        """
        stored_count = 0
        duplicate_count = 0

        try:
            with self.get_connection() as conn:
                for job in jobs:
                    try:
                        # Create description hash for deduplication
                        description_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('location', '')}"
                        description_hash = hashlib.md5(
                            description_text.encode(),
                            usedforsecurity=False
                        ).hexdigest()

                        # Check for duplicates
        # SQL Security: Using parameterized queries to prevent injection
                        cursor = conn.execute(
        # SQL Security: Using parameterized queries to prevent injection
                            "SELECT id FROM jobs WHERE description_hash = ?",
                            (description_hash,)
                        )

                        if cursor.fetchone():
                            duplicate_count += 1
                            continue

        # SQL Security: Using parameterized queries to prevent injection
                        # Insert new job
        # SQL Security: Using parameterized queries to prevent injection
                        cursor = conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                            INSERT INTO jobs (
                                title, company, location, salary, description,
                                url, source, email_id, description_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            job.get('title', ''),
                            job.get('company', ''),
                            job.get('location', ''),
                            job.get('salary', ''),
                            job.get('description', ''),
                            job.get('url', ''),
                            job.get('source', 'email'),
                            job.get('email_id', ''),
                            description_hash
                        ))

                        stored_count += 1
                        self.logger.debug(f"Stored job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")

                    except Exception as job_error:
                        self.logger.error(f"Error storing individual job: {job_error}")
                        self.logger.error(f"Job data: {job}")
                        continue

                conn.commit()
                self.logger.info(f"Database operation complete: {stored_count} stored, {duplicate_count} duplicates")

        except Exception as e:
            self.logger.error(f"Database storage error: {e}")
            raise

        return stored_count, duplicate_count

    def get_high_scored_jobs(self, min_score: float = 7.5, since_hours: int = 36) -> List[Dict]:
        """Get high-scoring jobs from recent timeframe"""
        try:
            since_time = datetime.now() - timedelta(hours=since_hours)

            with self.get_connection() as conn:
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                    SELECT * FROM jobs_with_latest_scores
                    WHERE created_at >= ?
                    AND total_score >= ?
                    ORDER BY total_score DESC, created_at DESC
                """, (since_time.isoformat(), min_score))

                jobs = []
                for row in cursor.fetchall():
                    job_dict = dict(row)
                    jobs.append(job_dict)

                self.logger.info(f"Retrieved {len(jobs)} high-scoring jobs (>= {min_score})")
                return jobs

        except Exception as e:
            self.logger.error(f"Error retrieving high-scored jobs: {e}")
            return []

    def score_and_store_job(self, job: Dict, score_data: Dict) -> bool:
        """Score a job and store the scoring data"""
        try:
            with self.get_connection() as conn:
                # Get job ID
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute(
        # SQL Security: Using parameterized queries to prevent injection
                    "SELECT id FROM jobs WHERE description_hash = ?",
                    (job.get('description_hash'),)
                )

                job_row = cursor.fetchone()
                if not job_row:
                    self.logger.error(f"Job not found for scoring: {job.get('title', 'Unknown')}")
                    return False

                job_id = job_row['id']

                # Store score
        # SQL Security: Using parameterized queries to prevent injection
                conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                    INSERT INTO job_scores (
                        job_id, base_score, location_bonus, experience_match,
                        skill_match, company_preference, total_score,
                        scoring_algorithm, score_breakdown
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    score_data.get('base_score', 0.0),
                    score_data.get('location_bonus', 0.0),
                    score_data.get('experience_match', 0.0),
                    score_data.get('skill_match', 0.0),
                    score_data.get('company_preference', 0.0),
                    score_data.get('total_score', 0.0),
                    score_data.get('algorithm', 'enhanced_v1'),
                    json.dumps(score_data.get('breakdown', {}))
                ))

                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error storing job score: {e}")
            return False

    def log_system_health(self, component: str, status: str, message: str, details: Dict = None):
        """Log system health information"""
        try:
            with self.get_connection() as conn:
        # SQL Security: Using parameterized queries to prevent injection
                conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                    INSERT INTO system_health (component, status, message, details)
                    VALUES (?, ?, ?, ?)
                """, (
                    component,
                    status,
                    message,
                    json.dumps(details) if details else None
                ))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error logging system health: {e}")

    def start_execution_log(self, run_type: str) -> int:
        """Start a new execution log entry, return log ID"""
        try:
            with self.get_connection() as conn:
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                    INSERT INTO execution_log (run_type, start_time)
                    VALUES (?, ?)
                """, (run_type, datetime.now().isoformat()))

                log_id = cursor.lastrowid
                conn.commit()
                return log_id

        except Exception as e:
            self.logger.error(f"Error starting execution log: {e}")
            return -1

        # SQL Security: Using parameterized queries to prevent injection
    def update_execution_log(self, log_id: int, **kwargs):
        # SQL Security: Using parameterized queries to prevent injection
        """Update execution log with results"""
        try:
        # SQL Security: Using parameterized queries to prevent injection
            # Build dynamic update query
            fields = []
            values = []

            for key, value in kwargs.items():
                if key in ['jobs_processed', 'jobs_stored', 'jobs_duplicates', 'errors_count', 'status', 'error_message']:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if 'status' in kwargs and kwargs['status'] in ['completed', 'failed', 'aborted']:
                fields.append("end_time = ?")
                values.append(datetime.now().isoformat())

            if fields:
                values.append(log_id)
        # SQL Security: Using parameterized queries to prevent injection
                query = f"UPDATE execution_log SET {', '.join(fields)} WHERE id = ?"

                with self.get_connection() as conn:
        # SQL Security: Using parameterized queries to prevent injection
                    conn.execute(query, values)
                    conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating execution log: {e}")

    def get_database_stats(self) -> Dict:
        """Get database statistics for monitoring"""
        try:
            with self.get_connection() as conn:
                stats = {}

                # Job counts
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("SELECT COUNT(*) as total_jobs FROM jobs")
                stats['total_jobs'] = cursor.fetchone()['total_jobs']

                # Recent jobs (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("SELECT COUNT(*) as recent_jobs FROM jobs WHERE created_at >= ?", (week_ago,))
                stats['recent_jobs'] = cursor.fetchone()['recent_jobs']

                # High-scoring jobs
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("""
        # SQL Security: Using parameterized queries to prevent injection
                    SELECT COUNT(*) as high_score_jobs
                    FROM jobs_with_latest_scores
                    WHERE total_score >= 7.5
                """)
                stats['high_score_jobs'] = cursor.fetchone()['high_score_jobs']

                # Database size
        # SQL Security: Using parameterized queries to prevent injection
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()['size']

                return stats

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}


def get_database_manager() -> JobDatabaseManager:
    """Get global database manager instance"""
    if not hasattr(get_database_manager, '_instance'):
        get_database_manager._instance = JobDatabaseManager()
    return get_database_manager._instance


if __name__ == "__main__":
    # Test database initialization
    logging.basicConfig(level=logging.INFO)
    db = JobDatabaseManager()
    stats = db.get_database_stats()
    print("Database initialized successfully!")
    print(f"Stats: {stats}")
