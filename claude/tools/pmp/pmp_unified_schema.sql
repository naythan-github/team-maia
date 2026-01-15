-- ================================================================================
-- PMP Unified Schema v1.0
-- ManageEngine Patch Manager Plus - Unified Intelligence Database
--
-- Purpose: Consolidate 3 separate PMP databases into single unified schema
--   - pmp_config.db → Core metrics, systems, patches
--   - pmp_resilient.db → Metrics snapshots, compliance checks
--   - pmp_systemreports.db → System reports, patch mappings
--
-- Design Principles:
--   - Single snapshot_id as temporal anchor for all data
--   - Normalized design (no data duplication)
--   - Comprehensive indexing for query performance
--   - Foreign key cascade for data consistency
--   - Compatible with BaseIntelligenceService interface
--
-- Sprint: SPRINT-PMP-UNIFIED-001
-- Phase: P0 - Schema Design
-- Date: 2025-01-15
-- Author: SRE Principal Engineer Agent
-- ================================================================================

-- ================================================================================
-- CORE TABLES
-- ================================================================================

-- Snapshots: Temporal anchor for all PMP data
-- Every data record ties back to a specific snapshot_id
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    api_version TEXT DEFAULT '1.4',
    extraction_duration_ms INTEGER,
    status TEXT CHECK(status IN ('success', 'partial', 'failed')) DEFAULT 'success',
    error_message TEXT,

    CONSTRAINT chk_duration CHECK (extraction_duration_ms >= 0)
);

-- Systems: Computer inventory from PMP
-- Combines data from pmp_config.all_systems + pmp_systemreports.systems
CREATE TABLE IF NOT EXISTS systems (
    system_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- System Identity
    resource_id TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    computer_name TEXT,
    ip_address TEXT,
    mac_address TEXT,
    domain_name TEXT,

    -- Organization
    branch_office_id TEXT,
    branch_office_name TEXT NOT NULL,
    customer_id TEXT,

    -- OS Details
    os_name TEXT,
    os_platform_name TEXT,
    os_platform INTEGER,
    service_pack TEXT,

    -- Agent Details
    agent_version TEXT,
    agent_installed_on INTEGER,
    agent_last_contact_time INTEGER,
    last_contact_time INTEGER,

    -- Health Status
    resource_health_status INTEGER,
    computer_live_status INTEGER,
    scan_status INTEGER,

    -- Patch Counts
    total_driver_patches INTEGER,
    missing_bios_patches INTEGER,
    last_patched_time INTEGER,

    -- Scan Details
    last_scan_time INTEGER,
    last_successful_scan INTEGER,

    -- Metadata
    raw_data TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_system_per_snapshot UNIQUE (snapshot_id, resource_id)
);

-- Patches: Patch inventory from PMP
-- Combines data from pmp_config.all_patches + pmp_config.supported_patches
CREATE TABLE IF NOT EXISTS patches (
    patch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Patch Identity
    pmp_patch_id TEXT NOT NULL,
    patch_name TEXT,
    update_name TEXT,
    bulletin_id TEXT,
    kb_number TEXT,

    -- Classification
    vendor_name TEXT,
    product_name TEXT,
    platform TEXT,
    platform_name TEXT,
    update_type TEXT,
    patch_lang TEXT,

    -- Severity
    severity INTEGER,
    severity_label TEXT,

    -- Status
    patch_status INTEGER,
    approval_status INTEGER,
    is_superceded INTEGER,

    -- Requirements
    patch_noreboot INTEGER,
    patch_size INTEGER,
    installed INTEGER,

    -- Dates (Unix timestamps in milliseconds)
    patch_released_time INTEGER,
    patch_updated_time INTEGER,

    -- Metadata
    raw_data TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_patch_per_snapshot UNIQUE (snapshot_id, pmp_patch_id)
);

-- Patch-System Mapping: Which patches apply to which systems
-- From pmp_systemreports.system_reports
CREATE TABLE IF NOT EXISTS patch_system_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Mapping
    pmp_patch_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,

    -- Status on this system
    patch_status INTEGER,
    approval_status INTEGER,
    patch_deployed INTEGER,

    -- Patch Details (denormalized for query performance)
    patch_name TEXT,
    bulletin_id TEXT,
    severity INTEGER,
    is_reboot_required INTEGER,

    -- Metadata
    raw_data TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_mapping_per_snapshot UNIQUE (snapshot_id, pmp_patch_id, resource_id)
);

-- Vulnerabilities: CVE tracking
-- Future expansion for CVE-patch mapping
CREATE TABLE IF NOT EXISTS vulnerabilities (
    vulnerability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- CVE Identity
    cve_id TEXT NOT NULL,
    cve_year INTEGER,

    -- Severity
    cvss_score REAL,
    cvss_severity TEXT,

    -- Associated Patches
    pmp_patch_ids TEXT,

    -- Metadata
    description TEXT,
    published_date TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_cve_per_snapshot UNIQUE (snapshot_id, cve_id)
);

-- ================================================================================
-- METRICS TABLES
-- ================================================================================

-- Patch Metrics: Aggregate patch statistics per snapshot
-- From pmp_resilient.patch_metrics
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

-- Severity Metrics: Patch severity breakdown per snapshot
-- From pmp_resilient.severity_metrics
CREATE TABLE IF NOT EXISTS severity_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    critical_count INTEGER DEFAULT 0,
    important_count INTEGER DEFAULT 0,
    moderate_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    unrated_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,

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

-- System Health Metrics: System health statistics per snapshot
-- From pmp_resilient.system_health_metrics
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

    number_of_apd_tasks INTEGER DEFAULT 0,

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
    )
);

-- Vulnerability DB Metrics: Vulnerability database status per snapshot
-- From pmp_resilient.vulnerability_db_metrics
CREATE TABLE IF NOT EXISTS vulnerability_db_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    last_db_update_status TEXT,
    last_db_update_time INTEGER,
    is_auto_db_update_disabled BOOLEAN DEFAULT 0,
    db_update_in_progress BOOLEAN DEFAULT 0,

    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- ================================================================================
-- POLICY & COMPLIANCE TABLES
-- ================================================================================

-- Deployment Policies: Patch deployment configurations
-- From pmp_config.deployment_policies
CREATE TABLE IF NOT EXISTS deployment_policies (
    policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Policy Identity
    template_id INTEGER,
    template_name TEXT,

    -- Status
    creation_time INTEGER,
    modified_time INTEGER,
    is_template_alive INTEGER,
    set_as_default INTEGER,
    user_id INTEGER,

    -- Metadata
    raw_data TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Deployment Tasks: Automated patch deployment tasks
-- From pmp_config (apd_summary)
CREATE TABLE IF NOT EXISTS deployment_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Task Identity
    apd_task_id TEXT,
    task_name TEXT,

    -- Status
    task_status TEXT,
    execution_status TEXT,

    -- Targeting
    platform_name TEXT,
    target_systems_count INTEGER,

    -- Schedule
    scheduled_time INTEGER,
    executed_time INTEGER,

    -- Results
    success_count INTEGER,
    failure_count INTEGER,
    pending_count INTEGER,

    -- Metadata
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Compliance Checks: Compliance framework validation results
-- From pmp_resilient.compliance_checks
CREATE TABLE IF NOT EXISTS compliance_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    check_name TEXT NOT NULL,
    check_category TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),

    details TEXT,
    threshold_value REAL,
    actual_value REAL,

    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,

    CONSTRAINT chk_category CHECK (check_category IN ('essential_eight', 'cis', 'custom'))
);

-- ================================================================================
-- PERFORMANCE INDEXES
-- ================================================================================

-- Snapshots indexes
CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON snapshots(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_snapshot_status ON snapshots(status);
CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp_status ON snapshots(timestamp DESC, status);

-- Systems indexes
CREATE INDEX IF NOT EXISTS idx_systems_snapshot_id ON systems(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_systems_resource_id ON systems(resource_id);
CREATE INDEX IF NOT EXISTS idx_systems_resource_name ON systems(resource_name);
CREATE INDEX IF NOT EXISTS idx_systems_ip_address ON systems(ip_address);
CREATE INDEX IF NOT EXISTS idx_systems_branch_office_name ON systems(branch_office_name);
CREATE INDEX IF NOT EXISTS idx_systems_health_status ON systems(resource_health_status);
CREATE INDEX IF NOT EXISTS idx_systems_os_platform_name ON systems(os_platform_name);
CREATE INDEX IF NOT EXISTS idx_systems_branch_health ON systems(branch_office_name, resource_health_status);

-- Patches indexes
CREATE INDEX IF NOT EXISTS idx_patches_snapshot_id ON patches(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_patches_pmp_patch_id ON patches(pmp_patch_id);
CREATE INDEX IF NOT EXISTS idx_patches_bulletin_id ON patches(bulletin_id);
CREATE INDEX IF NOT EXISTS idx_patches_severity ON patches(severity);
CREATE INDEX IF NOT EXISTS idx_patches_platform ON patches(platform_name);

-- Patch-System Mapping indexes
CREATE INDEX IF NOT EXISTS idx_mapping_snapshot_id ON patch_system_mapping(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_mapping_pmp_patch_id ON patch_system_mapping(pmp_patch_id);
CREATE INDEX IF NOT EXISTS idx_mapping_resource_id ON patch_system_mapping(resource_id);
CREATE INDEX IF NOT EXISTS idx_mapping_patch_status ON patch_system_mapping(patch_status);

-- Vulnerabilities indexes
CREATE INDEX IF NOT EXISTS idx_vuln_snapshot_id ON vulnerabilities(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_vuln_cve_id ON vulnerabilities(cve_id);
CREATE INDEX IF NOT EXISTS idx_vuln_severity ON vulnerabilities(cvss_severity);

-- Metrics indexes
CREATE INDEX IF NOT EXISTS idx_patch_metrics_snapshot ON patch_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_severity_metrics_snapshot ON severity_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_system_health_snapshot ON system_health_metrics(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_vuln_db_snapshot ON vulnerability_db_metrics(snapshot_id);

-- Policy & Compliance indexes
CREATE INDEX IF NOT EXISTS idx_deployment_policies_snapshot ON deployment_policies(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_deployment_tasks_snapshot ON deployment_tasks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_compliance_snapshot ON compliance_checks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_compliance_category ON compliance_checks(check_category, passed);
CREATE INDEX IF NOT EXISTS idx_compliance_severity ON compliance_checks(severity);
CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_checks(timestamp DESC);

-- ================================================================================
-- DATA INTEGRITY TRIGGERS
-- ================================================================================

-- Validate severity sum on insert
CREATE TRIGGER IF NOT EXISTS validate_severity_sum
BEFORE INSERT ON severity_metrics
FOR EACH ROW
WHEN NEW.total_count != (NEW.critical_count + NEW.important_count + NEW.moderate_count + NEW.low_count + NEW.unrated_count)
BEGIN
    SELECT RAISE(ABORT, 'Severity count mismatch: total_count must equal sum of individual severity counts');
END;

-- Validate system health sum on insert
CREATE TRIGGER IF NOT EXISTS validate_system_health_sum
BEFORE INSERT ON system_health_metrics
FOR EACH ROW
WHEN NEW.total_systems < (NEW.healthy_systems + NEW.moderately_vulnerable_systems + NEW.highly_vulnerable_systems + NEW.health_unknown_systems)
BEGIN
    SELECT RAISE(ABORT, 'System health count mismatch: sum of health categories exceeds total_systems');
END;

-- ================================================================================
-- UTILITY VIEWS
-- ================================================================================

-- Latest Snapshot: Most recent successful snapshot with key metrics
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

-- Compliance Summary: Compliance status by category and severity
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

-- Trend Data: 30-day historical trend
CREATE VIEW IF NOT EXISTS trend_data_30d AS
SELECT
    s.snapshot_id,
    DATE(s.timestamp) as snapshot_date,
    pm.missing_patches,
    sm.critical_count,
    sm.important_count,
    shm.healthy_systems,
    shm.highly_vulnerable_systems,
    ROUND(100.0 * shm.healthy_systems / NULLIF(shm.total_systems, 0), 2) as healthy_percentage
FROM snapshots s
LEFT JOIN patch_metrics pm ON s.snapshot_id = pm.snapshot_id
LEFT JOIN severity_metrics sm ON s.snapshot_id = sm.snapshot_id
LEFT JOIN system_health_metrics shm ON s.snapshot_id = shm.snapshot_id
WHERE s.status = 'success'
  AND s.timestamp >= datetime('now', '-30 days')
ORDER BY s.timestamp DESC;

-- Organization Summary: System health by organization
CREATE VIEW IF NOT EXISTS organization_summary AS
SELECT
    sys.branch_office_name as organization,
    COUNT(*) as total_systems,
    SUM(CASE WHEN sys.resource_health_status = 1 THEN 1 ELSE 0 END) as healthy_systems,
    SUM(CASE WHEN sys.resource_health_status = 2 THEN 1 ELSE 0 END) as moderate_risk_systems,
    SUM(CASE WHEN sys.resource_health_status = 3 THEN 1 ELSE 0 END) as high_risk_systems,
    ROUND(100.0 * SUM(CASE WHEN sys.resource_health_status = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as healthy_percentage
FROM systems sys
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON sys.snapshot_id = latest.latest_snapshot_id
GROUP BY sys.branch_office_name
ORDER BY high_risk_systems DESC;

-- ================================================================================
-- SCHEMA VERSION TRACKING
-- ================================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Unified PMP schema v1.0 - Initial design with 12 core tables');
