-- PMP Policy & Patch Data Extension - Phase 190
-- Extension to Phase 188/189: Adds policy and patch data storage
-- Purpose: Enable policy review, patch-to-computer mapping, and complete PMP intelligence
-- Version: 1.0 (Phase 190)
-- Date: 2025-11-25
-- Author: Patch Manager Plus API Specialist Agent

-- =============================================================================
-- POLICY TABLES
-- =============================================================================

-- Deployment Policies: How patches are deployed per organization/group
CREATE TABLE IF NOT EXISTS deployment_policies (
    policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Policy Identity
    config_id TEXT,
    config_name TEXT,
    config_description TEXT,

    -- Policy Settings
    platform_name TEXT,  -- Windows, Mac, Linux
    config_status TEXT,  -- InProgress, Draft, Executed, Suspended, Deployed
    deployment_type TEXT,

    -- Scheduling
    schedule_type TEXT,
    execution_time INTEGER,  -- Unix timestamp

    -- Targeting
    target_type TEXT,
    target_count INTEGER,

    -- Settings (JSON for complex nested data)
    settings_json TEXT,  -- Full policy settings as JSON

    -- Metadata
    created_time INTEGER,
    modified_time INTEGER,
    created_by TEXT,
    modified_by TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Health Policy: System health assessment criteria
CREATE TABLE IF NOT EXISTS health_policy (
    health_policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Health Thresholds
    healthy_threshold INTEGER,  -- Max missing patches for "Healthy"
    vulnerable_threshold INTEGER,  -- Max missing patches for "Vulnerable"
    highly_vulnerable_threshold INTEGER,  -- Max missing patches for "Highly Vulnerable"

    -- Severity Weighting
    critical_weight INTEGER,
    important_weight INTEGER,
    moderate_weight INTEGER,
    low_weight INTEGER,

    -- Settings (JSON)
    settings_json TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Approval Settings: Patch approval mode and rules
CREATE TABLE IF NOT EXISTS approval_settings (
    approval_settings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Approval Mode
    approval_mode TEXT,  -- automatic, manual, hybrid
    auto_approval_enabled BOOLEAN,

    -- Auto-Approval Rules
    auto_approve_critical BOOLEAN,
    auto_approve_security BOOLEAN,
    approval_delay_days INTEGER,

    -- Settings (JSON)
    settings_json TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- Deployment Configurations: Task execution details
CREATE TABLE IF NOT EXISTS deployment_configs (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Configuration Identity
    deployment_config_id TEXT,
    config_name TEXT,
    config_type TEXT,

    -- Status
    config_status TEXT,
    execution_status TEXT,

    -- Targeting
    platform_name TEXT,
    target_systems_count INTEGER,

    -- Patches
    patch_count INTEGER,

    -- Schedule
    scheduled_time INTEGER,
    executed_time INTEGER,

    -- Results
    success_count INTEGER,
    failure_count INTEGER,
    pending_count INTEGER,

    -- Settings (JSON)
    settings_json TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

-- =============================================================================
-- PATCH TABLES
-- =============================================================================

-- All Patches: Complete patch inventory
CREATE TABLE IF NOT EXISTS patches (
    patch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Patch Identity
    pmp_patch_id TEXT NOT NULL,  -- PMP's internal patch ID
    patch_name TEXT,
    bulletin_id TEXT,  -- MS security bulletin ID
    kb_number TEXT,  -- KB article number

    -- Classification
    vendor_name TEXT,
    product_name TEXT,
    platform_name TEXT,  -- Windows, Mac, Linux
    update_type TEXT,  -- Security Updates, Non-Security, etc.

    -- Severity
    severity INTEGER,  -- 0=Unrated, 1=Low, 2=Moderate, 3=Important, 4=Critical
    severity_label TEXT,

    -- Vulnerability
    cve_ids TEXT,  -- Comma-separated CVE IDs

    -- Status
    patch_status INTEGER,  -- 201=Installed, 202=Missing
    approval_status INTEGER,  -- 211=Approved, 0=Not Approved, 212=Declined
    download_status TEXT,

    -- Requirements
    reboot_required BOOLEAN,
    uninstall_supported BOOLEAN,

    -- Dates (Unix timestamps)
    release_date INTEGER,
    supported_date INTEGER,
    approved_date INTEGER,

    -- Size
    patch_size_bytes INTEGER,

    -- Metadata
    patch_description TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_patch_per_snapshot UNIQUE (snapshot_id, pmp_patch_id)
);

-- Patch to Computer Mapping: Which computers need which patches
CREATE TABLE IF NOT EXISTS patch_system_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Mapping
    pmp_patch_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,

    -- Status on this system
    patch_status INTEGER,  -- 201=Installed, 202=Missing, 206=Failed
    installation_status TEXT,

    -- Installation Details
    installed_time INTEGER,  -- Unix timestamp
    installation_error_code TEXT,

    -- System Details
    resource_name TEXT,
    ip_address TEXT,
    branch_office_name TEXT,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_mapping_per_snapshot UNIQUE (snapshot_id, pmp_patch_id, resource_id)
);

-- Supported Patches: Master catalog of what PMP can manage
CREATE TABLE IF NOT EXISTS supported_patches (
    supported_patch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- Patch Identity
    pmp_patch_id TEXT NOT NULL,
    patch_name TEXT,
    bulletin_id TEXT,

    -- Classification
    vendor_name TEXT,
    product_name TEXT,
    platform_name TEXT,

    -- Severity
    severity INTEGER,

    -- Requirements
    reboot_required BOOLEAN,

    -- Status
    approval_status INTEGER,

    -- Dates
    release_date INTEGER,

    -- Timestamps
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    CONSTRAINT unique_supported_patch_per_snapshot UNIQUE (snapshot_id, pmp_patch_id)
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Policy Indexes
CREATE INDEX IF NOT EXISTS idx_deployment_policies_name ON deployment_policies(config_name);
CREATE INDEX IF NOT EXISTS idx_deployment_policies_status ON deployment_policies(config_status);
CREATE INDEX IF NOT EXISTS idx_deployment_policies_platform ON deployment_policies(platform_name);

CREATE INDEX IF NOT EXISTS idx_deployment_configs_status ON deployment_configs(config_status);
CREATE INDEX IF NOT EXISTS idx_deployment_configs_platform ON deployment_configs(platform_name);

-- Patch Indexes
CREATE INDEX IF NOT EXISTS idx_patches_pmp_id ON patches(pmp_patch_id);
CREATE INDEX IF NOT EXISTS idx_patches_kb_number ON patches(kb_number);
CREATE INDEX IF NOT EXISTS idx_patches_bulletin_id ON patches(bulletin_id);
CREATE INDEX IF NOT EXISTS idx_patches_severity ON patches(severity);
CREATE INDEX IF NOT EXISTS idx_patches_vendor ON patches(vendor_name);
CREATE INDEX IF NOT EXISTS idx_patches_platform ON patches(platform_name);
CREATE INDEX IF NOT EXISTS idx_patches_approval_status ON patches(approval_status);
CREATE INDEX IF NOT EXISTS idx_patches_cve ON patches(cve_ids);

-- Patch-System Mapping Indexes
CREATE INDEX IF NOT EXISTS idx_mapping_patch_id ON patch_system_mapping(pmp_patch_id);
CREATE INDEX IF NOT EXISTS idx_mapping_resource_id ON patch_system_mapping(resource_id);
CREATE INDEX IF NOT EXISTS idx_mapping_status ON patch_system_mapping(patch_status);
CREATE INDEX IF NOT EXISTS idx_mapping_branch_office ON patch_system_mapping(branch_office_name);

-- Supported Patches Indexes
CREATE INDEX IF NOT EXISTS idx_supported_patches_pmp_id ON supported_patches(pmp_patch_id);
CREATE INDEX IF NOT EXISTS idx_supported_patches_vendor ON supported_patches(vendor_name);
CREATE INDEX IF NOT EXISTS idx_supported_patches_platform ON supported_patches(platform_name);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Latest Policy Snapshot
CREATE VIEW IF NOT EXISTS latest_deployment_policies AS
SELECT dp.*
FROM deployment_policies dp
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON dp.snapshot_id = latest.latest_snapshot_id;

-- Critical Missing Patches by Organization
CREATE VIEW IF NOT EXISTS critical_missing_patches_by_org AS
SELECT
    psm.branch_office_name as organization,
    p.kb_number,
    p.patch_name,
    p.cve_ids,
    COUNT(DISTINCT psm.resource_id) as affected_systems
FROM patch_system_mapping psm
INNER JOIN patches p ON psm.pmp_patch_id = p.pmp_patch_id AND psm.snapshot_id = p.snapshot_id
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON psm.snapshot_id = latest.latest_snapshot_id
WHERE psm.patch_status = 202  -- Missing
  AND p.severity = 4  -- Critical
GROUP BY psm.branch_office_name, p.kb_number, p.patch_name, p.cve_ids
ORDER BY affected_systems DESC;

-- Systems Missing Specific Patch (Query Template)
-- Usage: SELECT * FROM systems_missing_patch WHERE kb_number = 'KB5041580'
CREATE VIEW IF NOT EXISTS systems_missing_patch AS
SELECT
    psm.resource_name,
    psm.ip_address,
    psm.branch_office_name as organization,
    p.kb_number,
    p.patch_name,
    p.severity,
    p.cve_ids,
    psm.patch_status
FROM patch_system_mapping psm
INNER JOIN patches p ON psm.pmp_patch_id = p.pmp_patch_id AND psm.snapshot_id = p.snapshot_id
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON psm.snapshot_id = latest.latest_snapshot_id
WHERE psm.patch_status = 202;  -- Missing

-- Patch Distribution by Organization
CREATE VIEW IF NOT EXISTS patch_distribution_by_org AS
SELECT
    psm.branch_office_name as organization,
    COUNT(DISTINCT psm.resource_id) as total_systems,
    COUNT(DISTINCT CASE WHEN psm.patch_status = 202 AND p.severity = 4 THEN psm.pmp_patch_id END) as critical_missing,
    COUNT(DISTINCT CASE WHEN psm.patch_status = 202 AND p.severity = 3 THEN psm.pmp_patch_id END) as important_missing,
    COUNT(DISTINCT CASE WHEN psm.patch_status = 201 THEN psm.pmp_patch_id END) as installed_patches
FROM patch_system_mapping psm
INNER JOIN patches p ON psm.pmp_patch_id = p.pmp_patch_id AND psm.snapshot_id = p.snapshot_id
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON psm.snapshot_id = latest.latest_snapshot_id
GROUP BY psm.branch_office_name
ORDER BY critical_missing DESC;

-- =============================================================================
-- USAGE NOTES
-- =============================================================================

-- Query Examples:
--
-- 1. Get all deployment policies:
--    SELECT * FROM latest_deployment_policies;
--
-- 2. Find systems missing specific patch:
--    SELECT * FROM systems_missing_patch WHERE kb_number = 'KB5041580';
--
-- 3. Critical patches by organization:
--    SELECT * FROM critical_missing_patches_by_org;
--
-- 4. Patch distribution summary:
--    SELECT * FROM patch_distribution_by_org;
--
-- 5. Find all systems missing critical patches:
--    SELECT * FROM systems_missing_patch WHERE severity = 4;
