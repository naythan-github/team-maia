-- Maia Database Schemas
-- This file defines all database structures used by Maia tools
-- Version: 2025-09-09
-- Purpose: Enable git-independent restoration of any commit's data requirements

-- =============================================================================
-- JOBS DATABASE SCHEMA
-- =============================================================================

-- Jobs table - core job tracking system
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id TEXT,
    subject TEXT,
    sender TEXT,
    url TEXT,
    company TEXT,
    role_title TEXT,
    location TEXT,
    salary TEXT,
    description TEXT,
    requirements TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score REAL DEFAULT 0.0,
    notes TEXT,
    status TEXT DEFAULT 'new'
);

-- Job analysis results
CREATE TABLE IF NOT EXISTS job_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    analysis_type TEXT,
    analysis_result TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- =============================================================================
-- PERSONAL KNOWLEDGE GRAPH SCHEMA
-- =============================================================================

-- Knowledge nodes - core entities
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 1.0,
    importance REAL DEFAULT 0.5
);

-- Relationships between nodes
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id TEXT PRIMARY KEY,
    source_node_id TEXT,
    target_node_id TEXT,
    relationship_type TEXT,
    strength REAL DEFAULT 1.0,
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(id),
    FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(id)
);

-- Pattern recognition results
CREATE TABLE IF NOT EXISTS learned_patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT,
    pattern_data TEXT, -- JSON
    success_rate REAL,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FINANCIAL INTELLIGENCE SCHEMA
-- =============================================================================

-- Financial accounts and assets
CREATE TABLE IF NOT EXISTS financial_accounts (
    id TEXT PRIMARY KEY,
    account_type TEXT,
    institution TEXT,
    account_name TEXT,
    balance REAL,
    currency TEXT DEFAULT 'AUD',
    metadata TEXT, -- JSON
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial goals and targets
CREATE TABLE IF NOT EXISTS financial_goals (
    id TEXT PRIMARY KEY,
    goal_type TEXT,
    target_amount REAL,
    current_amount REAL,
    target_date TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Investment analysis
CREATE TABLE IF NOT EXISTS investment_analysis (
    id TEXT PRIMARY KEY,
    asset_type TEXT,
    symbol TEXT,
    analysis_data TEXT, -- JSON
    recommendation TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONTACTS DATABASE SCHEMA
-- =============================================================================

-- Comprehensive contact management
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    job_title TEXT,
    phone TEXT,
    source TEXT,
    notes TEXT,
    linkedin_url TEXT,
    last_interaction TIMESTAMP,
    relationship_strength INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contact interactions log
CREATE TABLE IF NOT EXISTS contact_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    interaction_type TEXT,
    interaction_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- =============================================================================
-- OPTIMIZATION CACHE SCHEMAS
-- =============================================================================

-- Intelligent context cache
CREATE TABLE IF NOT EXISTS analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,
    analysis_type TEXT NOT NULL,
    input_summary TEXT NOT NULL,
    ai_analysis TEXT,
    complexity_score REAL,
    tokens_saved INTEGER DEFAULT 0,
    reuse_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 1.0
);

-- Pattern templates for reuse
CREATE TABLE IF NOT EXISTS pattern_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT UNIQUE,
    pattern_type TEXT,
    template_content TEXT,
    success_rate REAL DEFAULT 1.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow optimization cache
CREATE TABLE IF NOT EXISTS workflow_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_hash TEXT UNIQUE,
    workflow_type TEXT,
    optimization_data TEXT, -- JSON
    performance_metrics TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- STRATEGIC PROJECTS SCHEMA
-- =============================================================================

-- Strategic project tracking
CREATE TABLE IF NOT EXISTS strategic_projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    phase TEXT DEFAULT 'conceptual',
    priority INTEGER DEFAULT 5,
    estimated_duration TEXT,
    resources_required TEXT,
    success_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Project milestones
CREATE TABLE IF NOT EXISTS project_milestones (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    milestone_name TEXT,
    description TEXT,
    due_date TEXT,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES strategic_projects(id)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Jobs indexes
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score);
CREATE INDEX IF NOT EXISTS idx_jobs_extracted_at ON jobs(extracted_at);

-- Knowledge graph indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON knowledge_relationships(source_node_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON knowledge_relationships(target_node_id);

-- Contacts indexes
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);

-- Cache indexes
CREATE INDEX IF NOT EXISTS idx_analysis_cache_hash ON analysis_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_type ON analysis_cache(analysis_type);
