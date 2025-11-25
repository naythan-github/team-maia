-- PMP Enhanced Data Extractor - Per-System Inventory Schema
-- Extension to Phase 188: Adds per-system data storage (52 fields × 3,355 systems)
-- Purpose: Enable per-organization analysis and detailed system queries
-- Version: 1.0 (Phase 189)
-- Date: 2025-11-25
-- Author: Patch Manager Plus API Specialist Agent

-- =============================================================================
-- ENHANCED SYSTEM INVENTORY TABLE
-- =============================================================================

-- Systems: Complete system inventory with all 52 fields from scandetails API
CREATE TABLE IF NOT EXISTS systems (
    system_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,

    -- System Identity
    resource_id TEXT NOT NULL,
    resource_id_string TEXT,
    resource_name TEXT NOT NULL,
    ip_address TEXT,
    mac_address TEXT,
    domain_netbios_name TEXT,

    -- Organization/Branch
    branch_office_id TEXT,
    branch_office_name TEXT NOT NULL,
    customer_id TEXT,

    -- OS Details
    os_name TEXT,
    os_platform INTEGER,
    os_platform_name TEXT,
    os_platform_id INTEGER,
    osflavor_id INTEGER,
    os_language INTEGER,
    os_language_abbr TEXT,
    service_pack TEXT,

    -- Agent Details
    agent_version TEXT,
    agent_installed_on INTEGER,  -- Unix timestamp (ms)
    agent_installed_dir TEXT,
    agent_last_contact_time INTEGER,  -- Unix timestamp (ms)
    agent_last_bootup_time INTEGER,  -- Unix timestamp (ms)
    agent_last_ds_contact_time INTEGER,  -- Unix timestamp (ms)
    agent_logged_on_users TEXT,

    -- Computer Status
    computer_live_status INTEGER,  -- 0=offline, 1=online
    computer_status_update_time INTEGER,  -- Unix timestamp (ms)
    installation_status INTEGER,

    -- Scan Details
    last_scan_time INTEGER,  -- Unix timestamp (ms)
    last_successful_scan INTEGER,  -- Unix timestamp (ms)
    last_sync_time INTEGER,  -- Unix timestamp (ms)
    scan_status INTEGER,
    patch_scan_error_code TEXT,
    scan_remarks TEXT,
    scan_remarks_args TEXT,

    -- Health Status
    resource_health_status INTEGER,  -- 1=healthy, 2=moderate, 3=highly vulnerable
    patch_status_image TEXT,
    patch_status_label TEXT,
    status_label TEXT,

    -- Metadata
    description TEXT,
    location TEXT,
    owner TEXT,
    owner_email_id TEXT,
    search_tag TEXT,
    error_kb_url TEXT,

    -- Foreign Keys
    branchmemberresourcerel_resource_id TEXT,
    branchofficedetails_branch_office_id TEXT,
    patchclientscanerror_resource_id TEXT,
    patchmgmtosinfo_resource_id TEXT,
    pmreshealthstatus_resource_id TEXT,
    oslanguage_i18n TEXT,
    oslanguage_languageid INTEGER,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,

    -- Constraints
    CONSTRAINT chk_health_status CHECK (resource_health_status IN (0, 1, 2, 3)),
    CONSTRAINT unique_system_per_snapshot UNIQUE (snapshot_id, resource_id)
);

-- =============================================================================
-- PERFORMANCE INDEXES FOR SYSTEM QUERIES
-- =============================================================================

-- System lookups
CREATE INDEX IF NOT EXISTS idx_systems_resource_id ON systems(resource_id);
CREATE INDEX IF NOT EXISTS idx_systems_resource_name ON systems(resource_name);
CREATE INDEX IF NOT EXISTS idx_systems_ip_address ON systems(ip_address);

-- Organization/Branch queries
CREATE INDEX IF NOT EXISTS idx_systems_branch_office_name ON systems(branch_office_name);
CREATE INDEX IF NOT EXISTS idx_systems_domain ON systems(domain_netbios_name);
CREATE INDEX IF NOT EXISTS idx_systems_customer_id ON systems(customer_id);

-- Health and status queries
CREATE INDEX IF NOT EXISTS idx_systems_health_status ON systems(resource_health_status);
CREATE INDEX IF NOT EXISTS idx_systems_computer_live_status ON systems(computer_live_status);
CREATE INDEX IF NOT EXISTS idx_systems_scan_status ON systems(scan_status);

-- OS distribution queries
CREATE INDEX IF NOT EXISTS idx_systems_os_platform_name ON systems(os_platform_name);
CREATE INDEX IF NOT EXISTS idx_systems_os_name ON systems(os_name);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_systems_last_scan_time ON systems(last_scan_time);
CREATE INDEX IF NOT EXISTS idx_systems_agent_last_contact ON systems(agent_last_contact_time);

-- Snapshot queries
CREATE INDEX IF NOT EXISTS idx_systems_snapshot_id ON systems(snapshot_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_systems_branch_health ON systems(branch_office_name, resource_health_status);
CREATE INDEX IF NOT EXISTS idx_systems_os_platform ON systems(os_platform_name, resource_health_status);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Latest System Inventory: Most recent snapshot with all systems
CREATE VIEW IF NOT EXISTS latest_system_inventory AS
SELECT
    s.*
FROM systems s
INNER JOIN (
    SELECT MAX(snapshot_id) as latest_snapshot_id
    FROM snapshots
    WHERE status = 'success'
) latest ON s.snapshot_id = latest.latest_snapshot_id;

-- Per-Organization Summary: System counts and health by organization
CREATE VIEW IF NOT EXISTS organization_summary AS
SELECT
    branch_office_name as organization,
    COUNT(*) as total_systems,
    SUM(CASE WHEN resource_health_status = 1 THEN 1 ELSE 0 END) as healthy_systems,
    SUM(CASE WHEN resource_health_status = 2 THEN 1 ELSE 0 END) as moderate_risk_systems,
    SUM(CASE WHEN resource_health_status = 3 THEN 1 ELSE 0 END) as high_risk_systems,
    SUM(CASE WHEN resource_health_status = 0 THEN 1 ELSE 0 END) as unknown_health_systems,
    SUM(CASE WHEN computer_live_status = 1 THEN 1 ELSE 0 END) as online_systems,
    SUM(CASE WHEN computer_live_status = 0 THEN 1 ELSE 0 END) as offline_systems,
    ROUND(100.0 * SUM(CASE WHEN resource_health_status = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as healthy_percentage,
    ROUND(100.0 * SUM(CASE WHEN resource_health_status = 3 THEN 1 ELSE 0 END) / COUNT(*), 2) as high_risk_percentage
FROM latest_system_inventory
GROUP BY branch_office_name
ORDER BY high_risk_percentage DESC;

-- OS Distribution: System counts by OS platform
CREATE VIEW IF NOT EXISTS os_distribution AS
SELECT
    os_platform_name,
    os_name,
    COUNT(*) as system_count,
    SUM(CASE WHEN resource_health_status = 3 THEN 1 ELSE 0 END) as high_risk_count,
    ROUND(100.0 * SUM(CASE WHEN resource_health_status = 3 THEN 1 ELSE 0 END) / COUNT(*), 2) as high_risk_percentage
FROM latest_system_inventory
GROUP BY os_platform_name, os_name
ORDER BY system_count DESC;

-- High Risk Systems: All systems with health status = 3
CREATE VIEW IF NOT EXISTS high_risk_systems AS
SELECT
    resource_name,
    ip_address,
    branch_office_name as organization,
    domain_netbios_name,
    os_name,
    last_scan_time,
    agent_last_contact_time,
    computer_live_status,
    scan_status
FROM latest_system_inventory
WHERE resource_health_status = 3
ORDER BY branch_office_name, resource_name;

-- Stale Systems: Systems that haven't checked in for 7+ days
CREATE VIEW IF NOT EXISTS stale_systems AS
SELECT
    resource_name,
    ip_address,
    branch_office_name as organization,
    agent_version,
    agent_last_contact_time,
    computer_live_status,
    ROUND((strftime('%s', 'now') * 1000 - agent_last_contact_time) / (1000.0 * 60 * 60 * 24), 1) as days_since_contact
FROM latest_system_inventory
WHERE agent_last_contact_time > 0
  AND (strftime('%s', 'now') * 1000 - agent_last_contact_time) > (7 * 24 * 60 * 60 * 1000)  -- 7 days
ORDER BY days_since_contact DESC;

-- Scan Failures: Systems with failed scans
CREATE VIEW IF NOT EXISTS scan_failures AS
SELECT
    resource_name,
    ip_address,
    branch_office_name as organization,
    last_scan_time,
    scan_status,
    scan_remarks,
    patch_scan_error_code
FROM latest_system_inventory
WHERE scan_status != 228  -- 228 = scanning completed successfully
ORDER BY branch_office_name, resource_name;

-- =============================================================================
-- DATA QUALITY VIEWS
-- =============================================================================

-- Data Coverage Report: What data we have vs missing
CREATE VIEW IF NOT EXISTS data_coverage_report AS
SELECT
    'Total Systems' as metric,
    COUNT(*) as count,
    '100%' as coverage
FROM latest_system_inventory
UNION ALL
SELECT
    'Systems with IP Address',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM latest_system_inventory), 2) || '%'
FROM latest_system_inventory
WHERE ip_address IS NOT NULL AND ip_address != '--'
UNION ALL
SELECT
    'Systems with MAC Address',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM latest_system_inventory), 2) || '%'
FROM latest_system_inventory
WHERE mac_address IS NOT NULL AND mac_address != '--'
UNION ALL
SELECT
    'Systems with Domain',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM latest_system_inventory), 2) || '%'
FROM latest_system_inventory
WHERE domain_netbios_name IS NOT NULL AND domain_netbios_name != '--'
UNION ALL
SELECT
    'Systems with Health Status',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM latest_system_inventory), 2) || '%'
FROM latest_system_inventory
WHERE resource_health_status > 0
UNION ALL
SELECT
    'Systems Online',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM latest_system_inventory), 2) || '%'
FROM latest_system_inventory
WHERE computer_live_status = 1;

-- =============================================================================
-- USAGE NOTES
-- =============================================================================

-- Query Examples:
--
-- 1. Get all systems for specific organization:
--    SELECT * FROM latest_system_inventory WHERE branch_office_name = 'Orro Group';
--
-- 2. Find all high-risk Windows systems:
--    SELECT * FROM latest_system_inventory
--    WHERE resource_health_status = 3 AND os_platform_name = 'Windows';
--
-- 3. Organization health summary:
--    SELECT * FROM organization_summary;
--
-- 4. Find systems that haven't scanned in 7+ days:
--    SELECT * FROM stale_systems;
--
-- 5. OS distribution across all organizations:
--    SELECT * FROM os_distribution;
