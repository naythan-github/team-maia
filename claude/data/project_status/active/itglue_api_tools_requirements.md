# ITGlue API Tools - Requirements

**Project**: ITGlue Full API Access for Maia
**Owner**: Naythan Dawe
**Agents**: IT Glue Specialist + SRE Principal Engineer
**Status**: Phase 2 - Requirements Documentation
**Last Updated**: 2025-11-28

---

## Core Purpose

Build production-grade ITGlue REST API tools providing full CRUD access to all ITGlue entities with local metadata caching, multi-instance support, and flexible integration architecture.

**Primary Use Case**: Document creation and import from various sources (email, filesystem, APIs)
**Future Scope**: Expand capabilities as API usage patterns emerge

---

## Success Criteria

1. ✅ Full CRUD operations for all ITGlue entities (organizations, configurations, passwords, flexible assets, documents, contacts, relationships)
2. ✅ Multi-instance support (sandbox + production with seamless switching)
3. ✅ Local metadata caching (SQLite) for smart search/query without API calls
4. ✅ Secure credential management (macOS Keychain for API keys)
5. ✅ SRE-grade error handling (rate limits, retries, circuit breakers)
6. ✅ Flexible plugin architecture for future integrations
7. ✅ 100% test coverage (unit + integration + production validation)

---

## Functional Requirements

### FR1: Authentication & Session Management
- **FR1.1**: Store API key securely in macOS Keychain
- **FR1.2**: Support multiple API keys (sandbox vs production)
- **FR1.3**: Detect API key expiry (90-day inactivity) and prompt for refresh
- **FR1.4**: Validate API key on first use (test endpoint: GET /organizations)

### FR2: Core Entity Operations (Full CRUD)

#### FR2.1: Organizations
- List all organizations
- Get organization by ID/name
- Create new organization
- Update organization metadata
- Search organizations by name/filter

#### FR2.2: Configurations (Servers, Workstations, Network Devices)
- List configurations for organization
- Get configuration by ID
- Create configuration (name, type, serial, org_id)
- Update configuration
- Link configuration to password/contact/flexible asset

#### FR2.3: Passwords
- List passwords for organization
- Get password details (encrypted field retrieval)
- Create password entry
- Update password entry
- **CRITICAL**: Never log password values in plain text

#### FR2.4: Flexible Assets (SOPs, Diagrams, Network Docs)
- List flexible assets for organization
- Get flexible asset by ID
- Create flexible asset
- Update flexible asset
- Support custom flexible asset types

#### FR2.5: Documents (PDFs, Images, Files)
- List documents for organization
- Get document metadata
- Upload document (file path → ITGlue)
- Download document (ITGlue → local file)
- Delete document

#### FR2.6: Contacts (Personnel)
- List contacts for organization
- Get contact by ID
- Create contact
- Update contact

#### FR2.7: Relationships (Entity Linking)
- Link configuration → password
- Link configuration → contact
- Link configuration → flexible asset
- Query all relationships for an entity

### FR3: Local Metadata Caching

#### FR3.1: Cache Scope (SQLite Database)
**CACHE** (fast local queries):
- Organization list (id, name, created_at, updated_at)
- Configuration metadata (id, name, type, serial_number, org_id)
- Flexible asset type templates
- Document metadata (id, name, size, upload_date, org_id) - NOT file contents
- Contact list (id, name, email, org_id)
- Relationship mappings

**DO NOT CACHE** (always fetch live):
- Password values (security)
- Document file contents (size)
- Images/attachments
- Sensitive notes/fields

#### FR3.2: Cache Operations
- **Initialize cache**: Full sync on first run
- **Refresh cache**: On-demand command or auto-detect staleness (>24 hours)
- **Smart query**: Check cache first, fall back to API if miss
- **Cache invalidation**: Update cache on write operations (create/update/delete)

### FR4: Multi-Instance Support
- **FR4.1**: Environment selection (sandbox vs production)
- **FR4.2**: Per-instance API keys stored separately in Keychain
- **FR4.3**: Per-instance cache databases (itglue_sandbox.db vs itglue_production.db)
- **FR4.4**: Easy switching: `ITGlueClient(instance='sandbox')` vs `ITGlueClient(instance='production')`

### FR5: Error Handling & Resilience

#### FR5.1: API Rate Limiting (3000 req/5min)
- Track request count in rolling 5-minute window
- Auto-throttle when approaching limit (e.g., 80% threshold)
- Respect `Retry-After` header on 429 responses
- Exponential backoff: 60s → 120s → 240s

#### FR5.2: HTTP Error Handling
- **401 Unauthorized**: API key invalid/expired → prompt for refresh
- **403 Forbidden**: Insufficient permissions → log and fail gracefully
- **404 Not Found**: Entity doesn't exist → return None (not exception)
- **429 Too Many Requests**: Rate limited → auto-retry after delay
- **500 Internal Server Error**: ITGlue issue → exponential backoff (3 retries)
- **503 Service Unavailable**: Maintenance window → log and fail

#### FR5.3: Network Resilience
- Connection timeout: 30 seconds
- Read timeout: 60 seconds
- Circuit breaker: Open after 5 consecutive failures, close after 60s cooldown

### FR6: Integration Architecture (Future-Proof)

#### FR6.1: Plugin System
- Event hooks: `on_document_created`, `on_organization_updated`, `on_password_rotated`
- Registration API: `ITGlueClient.register_plugin(callback, event_type)`
- Example future plugins:
  - ServiceDesk Integration: Ticket close → upload resolution
  - Email Intelligence: Parse email → extract attachments → upload
  - PSA Sync: Daily company list sync

#### FR6.2: Extensibility Points
- Custom entity types (via flexible assets)
- Batch operations (process 100+ orgs in one call)
- Async support (for high-volume operations)

---

## Non-Functional Requirements

### NFR1: Security
- **NFR1.1**: API keys stored in macOS Keychain (NEVER in code or config files)
- **NFR1.2**: Password values never logged (even in debug mode)
- **NFR1.3**: HTTPS only (enforce TLS 1.2+)
- **NFR1.4**: Minimal credential exposure window

### NFR2: Performance
- **NFR2.1**: Single API call latency: <2 seconds (P95)
- **NFR2.2**: Cache query latency: <100ms (P95)
- **NFR2.3**: Bulk query (100 orgs): <30 seconds
- **NFR2.4**: Document upload (10MB): <10 seconds

### NFR3: Observability
- **NFR3.1**: Structured logging (JSON format)
- **NFR3.2**: Metrics: API request count, latency, error rate, cache hit rate
- **NFR3.3**: Request tracing: Log request ID for debugging
- **NFR3.4**: Health check: `ITGlueClient.health_check()` → validates API key + connectivity

### NFR4: Maintainability
- **NFR4.1**: Type hints for all public APIs (mypy strict mode)
- **NFR4.2**: Docstrings for all public methods (Google style)
- **NFR4.3**: 100% test coverage for core operations
- **NFR4.4**: Runbook for common operations (in ARCHITECTURE.md)

---

## Out of Scope (Phase 1)

- Webhook receiver (ITGlue → Maia notifications)
- Advanced search (full-text search across all entities)
- Bulk import from external sources (PSA, RMM, CSV)
- Real-time sync (watch for changes)
- GraphQL API (only REST API v1.4)

---

## Acceptance Criteria

### Phase 1: Core API Client
- [ ] Authenticate with API key (sandbox + production)
- [ ] CRUD operations for all 7 entity types
- [ ] Rate limiting and retry logic working
- [ ] macOS Keychain integration for API keys
- [ ] SQLite cache database created and operational

### Phase 2: Metadata Caching
- [ ] Cache initialized with full sync
- [ ] Smart query (cache-first, API fallback)
- [ ] Cache refresh on-demand
- [ ] Cache invalidation on write operations

### Phase 3: Production Validation
- [ ] 100% test coverage (unit + integration)
- [ ] Performance validation (latency < SLOs)
- [ ] Circuit breaker tested (simulated failures)
- [ ] Observability verified (logs/metrics working)
- [ ] Runbook documented

---

## Technical Specifications

### API Details
- **Base URL (Production)**: `https://api.itglue.com`
- **Base URL (Sandbox)**: `https://api-sandbox.itglue.com` (assumed, confirm)
- **Authentication**: `x-api-key: YOUR_API_KEY` header
- **Rate Limit**: 3000 requests per 5-minute window
- **API Version**: v1.4 (latest stable)
- **Response Format**: JSON

### Key Endpoints
```
GET    /organizations              # List all organizations
GET    /organizations/:id          # Get organization by ID
POST   /organizations              # Create organization
PATCH  /organizations/:id          # Update organization

GET    /configurations             # List configurations
POST   /configurations             # Create configuration
PATCH  /configurations/:id         # Update configuration

GET    /passwords                  # List passwords
POST   /passwords                  # Create password
PATCH  /passwords/:id              # Update password

GET    /flexible_assets            # List flexible assets
POST   /flexible_assets            # Create flexible asset

GET    /documents                  # List documents
POST   /documents                  # Upload document
GET    /documents/:id/download     # Download document

GET    /contacts                   # List contacts
POST   /contacts                   # Create contact

# Relationships
POST   /configurations/:id/relationships/passwords
POST   /configurations/:id/relationships/contacts
```

### Technology Stack
- **Language**: Python 3.11+
- **HTTP Client**: `requests` library (session with connection pooling)
- **Cache Database**: SQLite 3
- **Keychain Access**: `keyring` library (macOS Keychain backend)
- **Testing**: pytest (unit + integration tests)
- **Type Checking**: mypy (strict mode)

### File Structure
```
claude/tools/integrations/itglue/
├── __init__.py
├── client.py              # ITGlueClient (main API wrapper)
├── auth.py                # macOS Keychain integration
├── cache.py               # SQLite metadata cache
├── models.py              # Pydantic models for entities
├── exceptions.py          # Custom exceptions
├── rate_limiter.py        # Rate limiting logic
└── circuit_breaker.py     # Circuit breaker pattern

claude/data/databases/system/
├── itglue_sandbox.db      # Sandbox cache
└── itglue_production.db   # Production cache

tests/integrations/itglue/
├── test_client.py         # Unit tests
├── test_cache.py          # Cache tests
├── test_integration.py    # Integration tests (real API)
└── test_production.py     # Production validation tests
```

---

## Dependencies

### Python Packages (requirements.txt)
```
requests>=2.31.0          # HTTP client
keyring>=24.0.0           # macOS Keychain access
pydantic>=2.0.0           # Data validation
pytest>=7.4.0             # Testing framework
pytest-cov>=4.1.0         # Coverage reporting
mypy>=1.5.0               # Type checking
```

### System Requirements
- Python 3.11+
- macOS (for Keychain integration)
- SQLite 3.35+
- ITGlue API key (sandbox + production)

---

## Risk Mitigation

### Risk 1: API Key Expiry (90-day inactivity)
- **Mitigation**: Log warning at 80 days, auto-detect 401 responses, prompt for refresh

### Risk 2: Rate Limit Exhaustion
- **Mitigation**: Conservative throttling (80% threshold), exponential backoff, queue for later

### Risk 3: Cache Staleness
- **Mitigation**: Timestamp tracking, auto-refresh on 24-hour threshold, manual refresh command

### Risk 4: Network Instability
- **Mitigation**: Circuit breaker (5 failures → open), connection pooling, retry logic

### Risk 5: Large Document Uploads (OOM)
- **Mitigation**: Streaming uploads, file size validation (warn >50MB), chunked transfer

---

## Open Questions (To Resolve During Implementation)

1. Sandbox URL confirmation (assumed `api-sandbox.itglue.com`)
2. API key naming convention in Keychain (`itglue-api-key-sandbox` vs `itglue-api-key-production`)
3. Cache refresh strategy (daily auto vs on-demand only)
4. Batch operation API support (unclear from docs, test during implementation)

---

**Status**: Requirements Complete ✅
**Next Phase**: Phase 3 - Test Design
**Agent Reload Command**: `load it_glue_specialist_agent` (if context lost)
