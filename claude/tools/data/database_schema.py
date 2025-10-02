#!/usr/bin/env python3
"""
Database Schema Definitions for Maia System
"""

class DatabaseSchema:
    """Database schema definitions for Maia job monitoring system"""
    
    @staticmethod
    def get_jobs_schema_v1_1():
        """Get the job monitoring database schema v1.1"""
        return [
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                salary TEXT,
                description TEXT,
                url TEXT,
                source TEXT DEFAULT 'email',
                email_id TEXT,
                description_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS job_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                base_score REAL DEFAULT 0.0,
                location_bonus REAL DEFAULT 0.0,
                experience_match REAL DEFAULT 0.0,
                skill_match REAL DEFAULT 0.0,
                company_preference REAL DEFAULT 0.0,
                total_score REAL DEFAULT 0.0,
                scoring_algorithm TEXT DEFAULT 'enhanced_v1',
                score_breakdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                jobs_processed INTEGER DEFAULT 0,
                jobs_stored INTEGER DEFAULT 0,
                jobs_duplicates INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT
            )
            """,
            """
            CREATE VIEW IF NOT EXISTS jobs_with_latest_scores AS
            SELECT 
                j.*,
                js.base_score,
                js.location_bonus,
                js.experience_match,
                js.skill_match,
                js.company_preference,
                js.total_score,
                js.scoring_algorithm,
                js.score_breakdown
            FROM jobs j
            LEFT JOIN job_scores js ON j.id = js.job_id
            WHERE js.id = (
                SELECT MAX(id) FROM job_scores WHERE job_id = j.id
            ) OR js.id IS NULL
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(description_hash)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_job_scores_total ON job_scores(total_score)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_system_health_component ON system_health(component, created_at)
            """
        ]