# Orro Application Inventory System - Requirements

**Project**: Production-grade application inventory extraction from email
**Agent**: SRE Principal Engineer Agent
**Started**: 2025-11-21
**Status**: Requirements Phase

---

## Functional Requirements

### FR-1: Email Data Extraction
- **MUST** extract full email bodies, not 200-char previews
- **MUST** search across all 1,415 indexed emails
- **MUST** handle semantic search with Ollama embeddings
- **MUST** extract application names via regex patterns + NER-like matching
- **MUST** extract vendor names (Microsoft, Atlassian, etc.)
- **MUST** extract stakeholder information (name, email, role)

### FR-2: Database Schema
- **MUST** support: applications, vendors, stakeholders, mentions, app_stakeholders
- **MUST** enforce foreign key constraints
- **MUST** prevent duplicate applications (normalize "M365" → "Microsoft 365")
- **MUST** track first_seen, last_seen dates for applications
- **MUST** track mention frequency per application

### FR-3: Data Quality
- **MUST** validate email dates before insertion
- **MUST** validate application names (non-empty, reasonable length)
- **MUST** deduplicate application mentions
- **MUST** normalize application names (case-insensitive matching)
- **MUST** handle vendor extraction and linking

### FR-4: Progress Tracking
- **MUST** save progress every 5 queries (checkpointing)
- **MUST** support resume from checkpoint on failure
- **MUST** log extraction progress (current query, apps found, errors)
- **MUST** report final statistics (apps, vendors, stakeholders, mentions)

### FR-5: Query Operations
- **MUST** support listing applications with sorting (by mentions, name, date)
- **MUST** support filtering by category, status, vendor
- **MUST** support exporting to CSV
- **MUST** support statistics reporting

---

## Non-Functional Requirements

### NFR-1: Reliability
- **MUST** use database transactions (commit on success, rollback on failure)
- **MUST** handle email RAG API errors gracefully (retry with exponential backoff)
- **MUST** prevent data corruption (atomic operations)
- **MUST** survive partial failures (continue processing remaining queries)
- **MUST** achieve >95% extraction success rate

### NFR-2: Performance
- **MUST** implement rate limiting (1-2s delay between Ollama queries)
- **MUST** use batch database operations (executemany for inserts)
- **MUST** complete extraction of 1,415 emails in <30 minutes
- **MUST** use database indexes for fast queries
- **MUST** avoid N+1 query patterns

### NFR-3: Security
- **MUST** use parameterized SQL queries (no string interpolation)
- **MUST** validate all user inputs
- **MUST** prevent SQL injection attacks
- **MUST** handle database connection cleanup (context managers)

### NFR-4: Observability
- **MUST** log all extraction operations (structured logging)
- **MUST** track error rates per query type
- **MUST** report performance metrics (queries/sec, apps/min)
- **MUST** provide detailed error messages for debugging

### NFR-5: Maintainability
- **MUST** externalize regex patterns (config file, not hardcoded)
- **MUST** support adding new application patterns without code changes
- **MUST** provide clear error messages
- **MUST** have >80% test coverage

---

## Email RAG API Integration

### Correct API Usage
```python
# ✅ CORRECT: Get full email body via message_id
results = email_rag.semantic_search(query, n_results=20)
for result in results:
    message_id = result['message_id']
    full_email = email_rag.mail_bridge.get_message_by_id(message_id)
    body = full_email.get('body', '')  # Full email body
```

### API Response Schema
```python
{
    'subject': str,
    'sender': str,
    'date': str,
    'relevance': float,
    'preview': str,  # ❌ Only 200 chars - DO NOT USE
    'message_id': str  # ✅ Use this to get full body
}
```

---

## Application Name Normalization

### Deduplication Rules
- "Microsoft 365" = "M365" = "Office 365" = "O365" → **Microsoft 365**
- "Azure AD" = "Entra ID" → **Microsoft Entra ID**
- "Jira" = "Jira Service Management" → **Jira**
- "Datto RMM" = "Datto" → **Datto RMM**

### Normalization Map (Externalized Config)
```json
{
  "microsoft_365": ["M365", "Office 365", "O365", "Microsoft 365"],
  "azure_ad": ["Azure AD", "Entra ID", "Microsoft Entra ID"],
  "jira": ["Jira", "Jira Service Management", "JSM"],
  "datto_rmm": ["Datto", "Datto RMM"]
}
```

---

## Vendor Extraction Rules

### Vendor Mapping
- Microsoft 365 → Microsoft Corporation
- Azure → Microsoft Corporation
- Confluence/Jira → Atlassian
- Datto → Datto, Inc.
- SonicWall → SonicWall Inc.
- Autotask → Datto (acquired)

---

## Database Schema (Updated)

```sql
-- Applications
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    canonical_name TEXT NOT NULL,  -- Normalized name
    vendor_id INTEGER,
    category TEXT,
    description TEXT,
    url TEXT,
    status TEXT DEFAULT 'active',
    first_seen DATE,
    last_seen DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Vendors
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL UNIQUE,
    website TEXT,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stakeholders
CREATE TABLE stakeholders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT,
    department TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application-Stakeholder relationships
CREATE TABLE app_stakeholders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    stakeholder_id INTEGER NOT NULL,
    relationship_type TEXT,  -- 'user', 'admin', 'vendor_contact'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    UNIQUE(application_id, stakeholder_id)
);

-- Email mentions
CREATE TABLE mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    email_subject TEXT,
    email_from TEXT,
    email_date DATE,
    context_snippet TEXT,
    message_id TEXT,  -- For deduplication
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    UNIQUE(application_id, message_id)  -- Prevent duplicate mentions
);

-- Extraction progress tracking
CREATE TABLE extraction_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    query_index INTEGER NOT NULL,
    total_queries INTEGER NOT NULL,
    apps_found INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Test Coverage Requirements

### Unit Tests (20+ tests)
1. Database initialization
2. Application normalization (10 test cases)
3. Vendor extraction
4. Email date validation
5. Stakeholder extraction
6. Pattern matching accuracy

### Integration Tests (15+ tests)
1. Email RAG API integration
2. Full extraction workflow
3. Transaction rollback on error
4. Checkpoint resume
5. Deduplication logic
6. Batch insert performance

### Performance Tests (5+ tests)
1. Extract 100 emails in <5 minutes
2. Database query performance (<100ms for list operations)
3. Rate limiting compliance (1-2s between queries)

---

## Success Criteria

- ✅ Extract applications from all 1,415 emails
- ✅ Achieve >90% application detection accuracy
- ✅ Complete extraction in <30 minutes
- ✅ Zero data corruption (all transactions atomic)
- ✅ >80% test coverage
- ✅ Handle API failures gracefully (>95% success rate)
- ✅ Support resume from checkpoint

---

## Implementation Plan

**Phase 1**: Database Layer (1 hour)
- Schema creation with foreign key enforcement
- Transaction management
- Batch operations
- Progress tracking

**Phase 2**: Extraction Logic (1.5 hours)
- Email RAG integration (full body retrieval)
- Application pattern matching
- Vendor extraction
- Stakeholder extraction
- Rate limiting

**Phase 3**: Data Quality (1 hour)
- Normalization logic
- Deduplication
- Validation
- Error handling

**Phase 4**: Testing (1.5 hours)
- Unit tests
- Integration tests
- Performance validation

**Total Estimated Time**: 5 hours (includes testing)

---

**Next Step**: Implement database layer with TDD
