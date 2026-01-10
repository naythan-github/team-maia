-- Azure Cost Optimization Platform Database Schema
-- Purpose: Store cost data, resource inventory, recommendations, and optimization history
-- Database: SQLite (consistent with Maia patterns)
-- Created: 2026-01-10

-- ============================================================================
-- SUBSCRIPTIONS & TENANTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    subscription_name TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    tenant_name TEXT,
    state TEXT DEFAULT 'Enabled',
    is_customer BOOLEAN DEFAULT 0,
    customer_name TEXT,
    monthly_budget REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned TIMESTAMP
);

CREATE INDEX idx_subscriptions_customer ON subscriptions(is_customer, customer_name);

-- ============================================================================
-- COST HISTORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS cost_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id TEXT NOT NULL,
    date DATE NOT NULL,
    resource_group TEXT,
    service_name TEXT,
    resource_id TEXT,
    cost REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    meter_category TEXT,
    meter_subcategory TEXT,
    tags TEXT, -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
    UNIQUE(subscription_id, date, resource_id, service_name)
);

CREATE INDEX idx_cost_history_date ON cost_history(subscription_id, date);
CREATE INDEX idx_cost_history_service ON cost_history(service_name, date);
CREATE INDEX idx_cost_history_resource ON cost_history(resource_id, date);

-- ============================================================================
-- RESOURCE INVENTORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS resources (
    resource_id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    resource_group TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    location TEXT,
    sku TEXT,
    size TEXT,
    state TEXT,
    tags TEXT, -- JSON blob
    properties TEXT, -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

CREATE INDEX idx_resources_subscription ON resources(subscription_id);
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_state ON resources(state);

-- ============================================================================
-- PERFORMANCE METRICS (for ML-based rightsizing)
-- ============================================================================

CREATE TABLE IF NOT EXISTS resource_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value REAL NOT NULL,
    aggregation TEXT DEFAULT 'Average', -- Average, Max, Min, P95, etc.
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_metrics_resource ON resource_metrics(resource_id, metric_name, timestamp);
CREATE INDEX idx_metrics_timestamp ON resource_metrics(timestamp);

-- ============================================================================
-- RECOMMENDATIONS (Azure Advisor + Custom Engines)
-- ============================================================================

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT UNIQUE, -- Azure Advisor ID or generated UUID
    subscription_id TEXT NOT NULL,
    resource_id TEXT,
    resource_group TEXT,
    category TEXT NOT NULL, -- Cost, Performance, Security, etc.
    source TEXT NOT NULL, -- 'Azure Advisor', 'ML Rightsizing', 'Waste Detection', etc.
    type TEXT NOT NULL, -- 'Rightsizing', 'Orphaned Resource', 'Reserved Instance', etc.
    impact TEXT, -- High, Medium, Low
    title TEXT NOT NULL,
    description TEXT,
    recommendation TEXT NOT NULL,
    estimated_savings_monthly REAL,
    estimated_savings_annual REAL,
    confidence_score REAL DEFAULT 0.5, -- 0.0-1.0 for ML predictions
    status TEXT DEFAULT 'Active', -- Active, Dismissed, Implemented, Expired
    implementation_effort TEXT, -- Low, Medium, High
    risk_level TEXT, -- Low, Medium, High
    metadata TEXT, -- JSON blob for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMP,
    implemented_at TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_recommendations_subscription ON recommendations(subscription_id, status);
CREATE INDEX idx_recommendations_source ON recommendations(source, category);
CREATE INDEX idx_recommendations_savings ON recommendations(estimated_savings_annual DESC);
CREATE INDEX idx_recommendations_status ON recommendations(status);

-- ============================================================================
-- OPTIMIZATION ACTIONS (for ML training and ROI tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS optimization_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT NOT NULL,
    subscription_id TEXT NOT NULL,
    resource_id TEXT,
    action_type TEXT NOT NULL, -- 'Resize', 'Delete', 'Reserved Instance', etc.
    action_details TEXT, -- JSON blob
    estimated_savings REAL,
    actual_savings REAL,
    cost_before REAL,
    cost_after REAL,
    implemented_by TEXT,
    implemented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_date TIMESTAMP, -- When we measured actual savings
    success BOOLEAN,
    notes TEXT,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_actions_recommendation ON optimization_actions(recommendation_id);
CREATE INDEX idx_actions_date ON optimization_actions(implemented_at);
CREATE INDEX idx_actions_success ON optimization_actions(success);

-- ============================================================================
-- RESERVED INSTANCES & COMMITMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS reserved_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id TEXT NOT NULL,
    reservation_id TEXT UNIQUE,
    resource_type TEXT NOT NULL, -- VM, SQL Database, etc.
    sku TEXT,
    location TEXT,
    quantity INTEGER,
    term TEXT, -- '1 Year', '3 Year'
    start_date DATE,
    end_date DATE,
    cost REAL,
    utilization_percent REAL,
    last_utilization_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

CREATE INDEX idx_ri_subscription ON reserved_instances(subscription_id);
CREATE INDEX idx_ri_expiry ON reserved_instances(end_date);

-- ============================================================================
-- COST ANOMALIES (for anomaly detection)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cost_anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id TEXT NOT NULL,
    resource_id TEXT,
    service_name TEXT,
    anomaly_date DATE NOT NULL,
    expected_cost REAL NOT NULL,
    actual_cost REAL NOT NULL,
    deviation_percent REAL NOT NULL,
    severity TEXT, -- High (>50%), Medium (20-50%), Low (<20%)
    status TEXT DEFAULT 'New', -- New, Investigating, Resolved, False Positive
    root_cause TEXT,
    resolution TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_anomalies_date ON cost_anomalies(anomaly_date DESC);
CREATE INDEX idx_anomalies_severity ON cost_anomalies(severity, status);

-- ============================================================================
-- TAG COMPLIANCE (for governance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tag_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    required_tags TEXT NOT NULL, -- JSON array of required tag names
    present_tags TEXT, -- JSON object of actual tags
    missing_tags TEXT, -- JSON array of missing tag names
    compliance_score REAL, -- 0.0-1.0
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_tag_compliance_subscription ON tag_compliance(subscription_id);
CREATE INDEX idx_tag_compliance_score ON tag_compliance(compliance_score);

-- ============================================================================
-- ML MODEL METADATA (for tracking model versions and performance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'Rightsizing', 'Anomaly Detection', etc.
    algorithm TEXT, -- 'Random Forest', 'Isolation Forest', etc.
    features TEXT, -- JSON array of feature names
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_samples INTEGER,
    accuracy REAL,
    precision_score REAL,
    recall REAL,
    f1_score REAL,
    model_path TEXT, -- Path to serialized model file
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    UNIQUE(model_name, model_version)
);

CREATE INDEX idx_ml_models_active ON ml_models(model_type, is_active);

-- ============================================================================
-- ML PREDICTIONS (for tracking prediction accuracy)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    resource_id TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    predicted_value REAL,
    confidence REAL,
    actual_value REAL, -- Filled in after validation period
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_date TIMESTAMP,
    was_correct BOOLEAN,
    FOREIGN KEY (model_id) REFERENCES ml_models(id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

CREATE INDEX idx_predictions_model ON ml_predictions(model_id);
CREATE INDEX idx_predictions_validation ON ml_predictions(validation_date);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active recommendations with highest ROI
CREATE VIEW IF NOT EXISTS v_top_recommendations AS
SELECT
    r.id,
    r.subscription_id,
    s.subscription_name,
    r.resource_id,
    r.category,
    r.type,
    r.title,
    r.estimated_savings_annual,
    r.confidence_score,
    r.impact,
    r.implementation_effort,
    r.created_at
FROM recommendations r
JOIN subscriptions s ON r.subscription_id = s.subscription_id
WHERE r.status = 'Active'
ORDER BY r.estimated_savings_annual DESC;

-- Monthly cost trends by subscription
CREATE VIEW IF NOT EXISTS v_monthly_costs AS
SELECT
    subscription_id,
    strftime('%Y-%m', date) as month,
    SUM(cost) as total_cost,
    COUNT(DISTINCT resource_id) as resource_count,
    COUNT(DISTINCT service_name) as service_count
FROM cost_history
GROUP BY subscription_id, month
ORDER BY subscription_id, month DESC;

-- Resource utilization summary (for rightsizing)
CREATE VIEW IF NOT EXISTS v_resource_utilization AS
SELECT
    r.resource_id,
    r.resource_name,
    r.resource_type,
    r.subscription_id,
    AVG(CASE WHEN m.metric_name = 'Percentage CPU' THEN m.value END) as avg_cpu,
    MAX(CASE WHEN m.metric_name = 'Percentage CPU' THEN m.value END) as max_cpu,
    AVG(CASE WHEN m.metric_name = 'Network In' THEN m.value END) as avg_network_in,
    COUNT(DISTINCT m.timestamp) as metric_samples
FROM resources r
LEFT JOIN resource_metrics m ON r.resource_id = m.resource_id
WHERE m.timestamp >= datetime('now', '-30 days')
GROUP BY r.resource_id;

-- Orphaned resources (potential waste)
CREATE VIEW IF NOT EXISTS v_orphaned_resources AS
SELECT
    r.resource_id,
    r.resource_name,
    r.resource_type,
    r.subscription_id,
    r.state,
    r.location,
    COALESCE(ch.avg_monthly_cost, 0) as estimated_monthly_cost
FROM resources r
LEFT JOIN (
    SELECT resource_id, AVG(cost) * 30 as avg_monthly_cost
    FROM cost_history
    WHERE date >= date('now', '-30 days')
    GROUP BY resource_id
) ch ON r.resource_id = ch.resource_id
WHERE
    (r.resource_type LIKE '%/disks' AND r.state = 'Unattached')
    OR (r.resource_type LIKE '%/publicIPAddresses' AND r.state NOT IN ('Attached', 'Associated'))
    OR (r.resource_type LIKE '%/networkInterfaces' AND r.state != 'Attached');

-- Savings summary by customer
CREATE VIEW IF NOT EXISTS v_savings_by_customer AS
SELECT
    s.customer_name,
    s.subscription_id,
    COUNT(r.id) as active_recommendations,
    SUM(r.estimated_savings_monthly) as monthly_savings_potential,
    SUM(r.estimated_savings_annual) as annual_savings_potential,
    SUM(CASE WHEN r.implementation_effort = 'Low' THEN r.estimated_savings_annual ELSE 0 END) as quick_wins_potential
FROM subscriptions s
LEFT JOIN recommendations r ON s.subscription_id = r.subscription_id
WHERE r.status = 'Active'
GROUP BY s.customer_name, s.subscription_id;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_cost_history_composite ON cost_history(subscription_id, date, service_name);
CREATE INDEX IF NOT EXISTS idx_metrics_composite ON resource_metrics(resource_id, metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_composite ON recommendations(subscription_id, status, estimated_savings_annual DESC);
