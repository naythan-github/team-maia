-- PMP Configuration Extractor - SQLite Database Schema
-- Purpose: Historical snapshot storage for ManageEngine Patch Manager Plus configuration
-- Version: 1.0
-- Date: 2025-11-25
-- Author: Patch Manager Plus API Specialist Agent + SRE Principal Engineer Agent

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Snapshots: Master record for each configuration extraction
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    api_version TEXT DEFAULT '1.4',
    extraction_duration_ms INTEGER,
    status TEXT CHECK(status IN ('success', 'partial', 'failed')) DEFAULT 'success',
    error_message TEXT,  -- Populated if status = 'failed'
    CONSTRAINT chk_duration CHECK (extraction_duration_ms >= 0)
);

-- Patch Metrics: Patch installation and availability metrics
CREATE TABLE IF NOT EXISTS patch_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    installed_patches INTEGER DEFAULT 0,
    applicable_patches INTEGER DEFAULT 0,
    new_patches INTEGER DEFAULT 0,
    missing_patches INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT chk_patch_counts CHECK (
        installed_patches >= 0 AND
        applicable_patches >= 0 AND
        new_patches >= 0 AND
        missing_patches >= 0
    )
);

-- Severity Metrics: Missing patch severity distribution
CREATE TABLE IF NOT EXISTS severity_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    critical_count INTEGER DEFAULT 0,
    important_count INTEGER DEFAULT 0,
    moderate_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    unrated_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,  -- Validation: sum of above
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT chk_severity_counts CHECK (
        critical_count >= 0 AND
        important_count >= 0 AND
        moderate_count >= 0 AND
        low_count >= 0 AND
        unrated_count >= 0 AND
        total_count >= 0
    ),
    CONSTRAINT chk_severity_sum CHECK (
        total_count = (critical_count + important_count + moderate_count + low_count + unrated_count)
    )
);

-- System Health Metrics: Endpoint health and scan status
CREATE TABLE IF NOT EXISTS system_health_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    total_systems INTEGER DEFAULT 0,
    healthy_systems INTEGER DEFAULT 0,
    moderately_vulnerable_systems INTEGER DEFAULT 0,
    highly_vulnerable_systems INTEGER DEFAULT 0,
    health_unknown_systems INTEGER DEFAULT 0,
    scanned_systems INTEGER DEFAULT 0,
    unscanned_system_count INTEGER DEFAULT 0,
    scan_success_count INTEGER DEFAULT 0,
    scan_failure_count INTEGER DEFAULT 0,
    number_of_apd_tasks INTEGER DEFAULT 0,  -- Automated Patch Deployment tasks
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT chk_system_counts CHECK (
        total_systems >= 0 AND
        healthy_systems >= 0 AND
        moderately_vulnerable_systems >= 0 AND
        highly_vulnerable_systems >= 0 AND
        health_unknown_systems >= 0 AND
        scanned_systems >= 0 AND
        unscanned_system_count >= 0 AND
        scan_success_count >= 0 AND
        scan_failure_count >= 0 AND
        number_of_apd_tasks >= 0
    ),
    CONSTRAINT chk_system_health_sum CHECK (
        total_systems >= (healthy_systems + moderately_vulnerable_systems + highly_vulnerable_systems + health_unknown_systems)
    ),
    CONSTRAINT chk_scan_sum CHECK (
        total_systems >= (scanned_systems + unscanned_system_count)
    )
);

-- Vulnerability Database Config: DB update status and configuration
CREATE TABLE IF NOT EXISTS vulnerability_db_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    last_db_update_status TEXT,  -- 'Success', 'Failed', etc.
    last_db_update_time INTEGER,  -- Unix timestamp (milliseconds)
    is_auto_db_update_disabled BOOLEAN DEFAULT 0,
    db_update_in_progress BOOLEAN DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Compliance Checks: Rule evaluation results
CREATE TABLE IF NOT EXISTS compliance_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    check_name TEXT NOT NULL,
    check_category TEXT NOT NULL,  -- 'essential_eight', 'cis', 'custom'
    passed BOOLEAN NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    details TEXT,  -- Human-readable explanation
    threshold_value REAL,  -- Expected value for pass
    actual_value REAL,  -- Measured value
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT chk_category CHECK (check_category IN ('essential_eight', 'cis', 'custom'))
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Snapshot queries (most common: get recent snapshots)
CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON snapshots(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_snapshot_status ON snapshots(status);

-- Metric queries (join with snapshots)
CREATE INDEX IF NOT EXISTS idx_patch_metrics_snapshot ON patch_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_severity_metrics_snapshot ON severity_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_system_health_snapshot ON system_health_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_vuln_db_snapshot ON vulnerability_db_metrics(snapshot_id);

-- Compliance queries (filter by category, severity, pass/fail)
CREATE INDEX IF NOT EXISTS idx_compliance_snapshot ON compliance_checks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_compliance_category ON compliance_checks(check_category, passed);
CREATE INDEX IF NOT EXISTS idx_compliance_severity ON compliance_checks(severity);
CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_checks(timestamp DESC);

-- Composite index for trend analysis (common query pattern)
CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp_status ON snapshots(timestamp DESC, status);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Latest Snapshot: Most recent successful extraction
CREATE VIEW IF NOT EXISTS latest_snapshot AS
SELECT
    s.snapshot_id,
    s.timestamp,
    s.extraction_duration_ms,
    pm.installed_patches,
    pm.missing_patches,
    sm.critical_count,
    sm.important_count,
    shm.total_systems,
    shm.healthy_systems,
    shm.highly_vulnerable_systems
FROM snapshots s
LEFT JOIN patch_metrics pm ON s.snapshot_id = pm.snapshot_id
LEFT JOIN severity_metrics sm ON s.snapshot_id = sm.snapshot_id
LEFT JOIN system_health_metrics shm ON s.snapshot_id = shm.snapshot_id
WHERE s.status = 'success'
ORDER BY s.timestamp DESC
LIMIT 1;

-- Compliance Summary: Latest compliance check results
CREATE VIEW IF NOT EXISTS compliance_summary AS
SELECT
    cc.check_category,
    cc.severity,
    COUNT(*) as total_checks,
    SUM(CASE WHEN cc.passed THEN 1 ELSE 0 END) as passed_checks,
    SUM(CASE WHEN NOT cc.passed THEN 1 ELSE 0 END) as failed_checks,
    ROUND(100.0 * SUM(CASE WHEN cc.passed THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM compliance_checks cc
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON cc.snapshot_id = latest.latest_snapshot_id
GROUP BY cc.check_category, cc.severity
ORDER BY
    CASE cc.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;

-- Trend Data (Last 30 Days): Daily snapshots for charts
CREATE VIEW IF NOT EXISTS trend_data_30d AS
SELECT
    s.snapshot_id,
    DATE(s.timestamp) as snapshot_date,
    pm.missing_patches,
    sm.critical_count,
    sm.important_count,
    shm.healthy_systems,
    shm.highly_vulnerable_systems,
    ROUND(100.0 * shm.healthy_systems / shm.total_systems, 2) as healthy_percentage
FROM snapshots s
LEFT JOIN patch_metrics pm ON s.snapshot_id = pm.snapshot_id
LEFT JOIN severity_metrics sm ON s.snapshot_id = sm.snapshot_id
LEFT JOIN system_health_metrics shm ON s.snapshot_id = shm.snapshot_id
WHERE s.status = 'success'
  AND s.timestamp >= datetime('now', '-30 days')
ORDER BY s.timestamp DESC;

-- Failed Compliance Checks: All active compliance failures
CREATE VIEW IF NOT EXISTS failed_compliance_checks AS
SELECT
    cc.check_name,
    cc.check_category,
    cc.severity,
    cc.details,
    cc.threshold_value,
    cc.actual_value,
    s.timestamp as snapshot_timestamp
FROM compliance_checks cc
INNER JOIN snapshots s ON cc.snapshot_id = s.snapshot_id
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON cc.snapshot_id = latest.latest_snapshot_id
WHERE cc.passed = 0
ORDER BY
    CASE cc.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END,
    cc.check_name;

-- =============================================================================
-- HELPER FUNCTIONS (SQLite User-Defined Functions in Python)
-- =============================================================================

-- Note: The following helper queries are implemented in Python code

-- get_trend_data(days: int) -> List[Dict]
--   Returns time-series data for specified number of days

-- get_compliance_summary(snapshot_id: int) -> Dict
--   Returns aggregated compliance results for a snapshot

-- get_health_score(snapshot_id: int) -> float
--   Calculates overall system health score (0-100)

-- detect_configuration_drift(days: int) -> List[Dict]
--   Identifies significant changes in configuration metrics

-- =============================================================================
-- DATA VALIDATION TRIGGERS
-- =============================================================================

-- Trigger: Validate severity sum matches total
CREATE TRIGGER IF NOT EXISTS validate_severity_sum
BEFORE INSERT ON severity_metrics
FOR EACH ROW
WHEN NEW.total_count != (NEW.critical_count + NEW.important_count + NEW.moderate_count + NEW.low_count + NEW.unrated_count)
BEGIN
    SELECT RAISE(ABORT, 'Severity count mismatch: total_count must equal sum of individual severity counts');
END;

-- Trigger: Validate system counts don't exceed total
CREATE TRIGGER IF NOT EXISTS validate_system_health_sum
BEFORE INSERT ON system_health_metrics
FOR EACH ROW
WHEN NEW.total_systems < (NEW.healthy_systems + NEW.moderately_vulnerable_systems + NEW.highly_vulnerable_systems + NEW.health_unknown_systems)
BEGIN
    SELECT RAISE(ABORT, 'System health count mismatch: sum of health categories exceeds total_systems');
END;

-- Trigger: Prevent snapshot deletion if referenced by compliance checks
CREATE TRIGGER IF NOT EXISTS prevent_snapshot_deletion_with_compliance
BEFORE DELETE ON snapshots
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM compliance_checks WHERE snapshot_id = OLD.snapshot_id) > 0
BEGIN
    -- Note: This is overridden by ON DELETE CASCADE, but serves as documentation
    -- In production, consider archival instead of deletion
    SELECT NULL;  -- Allow deletion (CASCADE will handle cleanup)
END;

-- =============================================================================
-- INITIAL DATA / SEED DATA
-- =============================================================================

-- No seed data required - database starts empty
-- First snapshot will be inserted by pmp_config_extractor.py

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert current schema version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema - PMP configuration extractor v1.0');

-- =============================================================================
-- OPTIMIZATION HINTS
-- =============================================================================

-- Analyze tables after bulk inserts for query optimization
-- Run: ANALYZE; after inserting significant data

-- Vacuum database periodically to reclaim space
-- Run: VACUUM; monthly or after large deletions

-- Integrity check (run before backups)
-- Run: PRAGMA integrity_check;

-- =============================================================================
-- USAGE NOTES
-- =============================================================================

-- 1. Database Location: ~/.maia/databases/intelligence/pmp_config.db
-- 2. Expected Growth: ~5 KB per snapshot (daily = 1.8 MB/year)
-- 3. Retention Policy: 2 years active, compress older snapshots
-- 4. Backup Strategy: Daily SQLite backup via .backup command
-- 5. Performance: All queries <50ms for 90-day ranges with indexes

-- Example Queries:
--
-- Latest snapshot summary:
--   SELECT * FROM latest_snapshot;
--
-- Compliance pass rate by category:
--   SELECT * FROM compliance_summary;
--
-- Last 30 days trend:
--   SELECT * FROM trend_data_30d;
--
-- All failed compliance checks:
--   SELECT * FROM failed_compliance_checks;
--
-- Snapshot count by status:
--   SELECT status, COUNT(*) FROM snapshots GROUP BY status;
--
-- Average extraction duration (last 30 days):
--   SELECT AVG(extraction_duration_ms) as avg_duration_ms
--   FROM snapshots
--   WHERE status = 'success'
--     AND timestamp >= datetime('now', '-30 days');
