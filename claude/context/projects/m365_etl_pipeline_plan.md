# M365 Multi-Schema ETL Pipeline - Implementation Plan

**Phase**: 264
**Status**: PLANNING COMPLETE - READY FOR IMPLEMENTATION
**Created**: 2026-01-10
**Priority**: CRITICAL (100 customers to scan in next month)

---

## Executive Summary

Extend the M365 IR ETL pipeline to support multiple export schema variants. Current system only handles Legacy Portal Export format, but real-world investigations require support for Graph API exports and PowerShell exports.

**Business Driver**: 100 customers to scan in the next month, each potentially using different export methods.

---

## 1. Architecture Overview

### Current State (Broken)

```
CSV Files → m365_log_parser.py (hardcoded fields) → log_importer.py → database
                    ↓
            Only works for Legacy Portal format
            Fails on Graph API exports (Date (UTC) vs CreatedDateTime)
```

### Target State

```
CSV Files → Schema Detector → Schema Registry → Schema-Aware Parser → Importer → Database
                  ↓                  ↓                   ↓
           Auto-detect         Field mappings      Normalize to
           variant             per variant         canonical model
```

---

## 2. Schema Variants to Support

### 2.1 Legacy Portal Export (Currently Working)

**Source**: Microsoft 365 Admin Center > Reports > Sign-in Logs Export

| Field | Type | Example |
|-------|------|---------|
| CreatedDateTime | AU/US ambiguous | `3/12/2025 7:22:01 AM` |
| UserPrincipalName | String | `user@contoso.com` |
| AppDisplayName | String | `Microsoft Office` |
| IPAddress | String | `192.168.1.1` |
| City | String | `Melbourne` |
| Country | String | `AU` |
| Status | String (buggy) | `Microsoft.Graph.PowerShell.Models...` |
| ConditionalAccessStatus | String | `success`, `failure`, `notApplied` |

### 2.2 Graph API Export (Currently Failing)

**Source**: Entra ID Portal "Export to CSV" or Graph Explorer

**4 File Types**:
- `InteractiveSignIns*.csv` - User interactive sign-ins
- `NonInteractiveSignIns*.csv` - Background/SSO sign-ins
- `ApplicationSignIns*.csv` - Service principal auth (NO USER FIELDS)
- `MSISignIns*.csv` - Managed Identity sign-ins

| Field | Type | Example |
|-------|------|---------|
| Date (UTC) | ISO 8601 | `2025-12-04T08:19:41Z` |
| Username | String | `user@contoso.com` |
| User | String | `John Smith` |
| Application | String | `Microsoft Office` |
| IP address | String | `192.168.1.1` |
| Location | Combined | `Melbourne, Victoria, AU` |
| Status | Clean string | `Success`, `Failure` |
| Sign-in error code | Integer | `0`, `50126` |
| Conditional Access | String | `Success`, `Not Applied` |

### 2.3 PowerShell Get-MgAuditLogSignIn

**Source**: Microsoft Graph PowerShell SDK

**Key Differences**:
- Nested JSON objects (deviceDetail, location, status)
- Different enum serialization
- May have PowerShell object references in fields

---

## 3. Implementation Phases

### Phase 1: Schema Registry Foundation (3-4 days)

**Sprint 1.1: Schema Detection (1 day)**
- [ ] Create `schema_registry.py` with SchemaVariant enum
- [ ] Implement `detect_schema_variant()` - fingerprint headers
- [ ] Test with real sample files from PIR-GOOD-SAMARITAN-777777

**Sprint 1.2: Schema Definitions (2 days)**
- [ ] Define LEGACY_PORTAL_SCHEMA (field mappings)
- [ ] Define GRAPH_INTERACTIVE_SCHEMA
- [ ] Define GRAPH_NONINTERACTIVE_SCHEMA
- [ ] Define GRAPH_APPLICATION_SCHEMA (service principal)
- [ ] Define GRAPH_MSI_SCHEMA
- [ ] Create transform functions (parse_iso_datetime, parse_graph_location, etc.)

**Sprint 1.3: Database Migration (1 day)**
- [ ] Write migration v5 script (new columns)
- [ ] Add: schema_variant, sign_in_type, is_service_principal
- [ ] Add: service_principal_id, service_principal_name
- [ ] Add: status_error_code, mfa_result, latency_ms
- [ ] Test backward compatibility

### Phase 2: Parser Integration (3-4 days)

**Sprint 2.1: Schema-Aware Parser (2 days)**
- [ ] Add `parse_with_schema()` method to m365_log_parser.py
- [ ] Location parsing (City, State, Country from combined)
- [ ] Date format handling by schema
- [ ] Service principal detection
- [ ] Status code extraction

**Sprint 2.2: Importer Updates (2 days)**
- [ ] Update `import_sign_in_logs()` for schema dispatch
- [ ] Add `import_graph_signin()` method
- [ ] Update `_import_from_directory()`
- [ ] Update `_import_from_zip()`
- [ ] Schema tracking in import_metadata

### Phase 3: Verification & Timeline (2-3 days)

- [ ] Update auth_verifier.py for Graph API status codes
- [ ] Handle service principal authentication patterns
- [ ] Update timeline_builder.py for service principal events
- [ ] Add sign-in type filtering

### Phase 4: PowerShell Schema (2-3 days)

- [ ] Obtain PowerShell export samples
- [ ] Define POWERSHELL_V1_SCHEMA
- [ ] Handle nested JSON expansion
- [ ] Integration tests

### Phase 5: Testing & Validation (2-3 days)

- [ ] Cross-schema import test
- [ ] Real-world sample validation (PIR-GOOD-SAMARITAN ZIPs)
- [ ] Performance benchmarks
- [ ] Documentation updates

---

## 4. Database Schema Changes (Migration v5)

```sql
-- New columns for sign_in_logs
ALTER TABLE sign_in_logs ADD COLUMN schema_variant TEXT;
ALTER TABLE sign_in_logs ADD COLUMN sign_in_type TEXT;
ALTER TABLE sign_in_logs ADD COLUMN is_service_principal INTEGER DEFAULT 0;
ALTER TABLE sign_in_logs ADD COLUMN service_principal_id TEXT;
ALTER TABLE sign_in_logs ADD COLUMN service_principal_name TEXT;
ALTER TABLE sign_in_logs ADD COLUMN user_id TEXT;
ALTER TABLE sign_in_logs ADD COLUMN request_id TEXT;
ALTER TABLE sign_in_logs ADD COLUMN status_error_code INTEGER;
ALTER TABLE sign_in_logs ADD COLUMN failure_reason TEXT;
ALTER TABLE sign_in_logs ADD COLUMN auth_requirement TEXT;
ALTER TABLE sign_in_logs ADD COLUMN mfa_result TEXT;
ALTER TABLE sign_in_logs ADD COLUMN latency_ms INTEGER;
ALTER TABLE sign_in_logs ADD COLUMN device_compliant INTEGER;
ALTER TABLE sign_in_logs ADD COLUMN device_managed INTEGER;
ALTER TABLE sign_in_logs ADD COLUMN credential_key_id TEXT;
ALTER TABLE sign_in_logs ADD COLUMN resource_id TEXT;
ALTER TABLE sign_in_logs ADD COLUMN resource_display_name TEXT;

-- Indexes
CREATE INDEX idx_signin_type ON sign_in_logs(sign_in_type);
CREATE INDEX idx_signin_schema ON sign_in_logs(schema_variant);
CREATE INDEX idx_signin_service_principal ON sign_in_logs(is_service_principal);
```

---

## 5. File Structure

```
claude/tools/m365_ir/
├── schema_registry.py          # NEW: Schema definitions and detection
├── schema_transforms.py        # NEW: Field transformation functions
├── m365_log_parser.py          # EXTEND: Add schema-aware parsing
├── log_importer.py             # EXTEND: Schema dispatch
├── log_database.py             # EXTEND: New columns
├── migrations/
│   └── migrate_v5.py           # NEW: Multi-schema migration
└── tests/
    ├── test_schema_registry.py      # NEW
    ├── test_schema_transforms.py    # NEW
    ├── test_graph_api_import.py     # NEW
    └── test_multi_schema_import.py  # NEW
```

---

## 6. Test Data Available

From PIR-GOOD-SAMARITAN-777777:
```
/Users/naythandawe/work_projects/ir_cases/PIR-GOOD-SAMARITAN-777777/source-files/
├── SGS_2025-11-04_2025-12-04_1_1.zip  (moved, Graph API format)
├── SGS_2025-11-04_2025-12-04_extracted.zip
└── SGS_2025-11-28_2025-12-05_1.zip
```

Contains:
- InteractiveSignIns: 9K+ records
- NonInteractiveSignIns: 100K+ records
- ApplicationSignIns: 49K+ records
- MSISignIns: 300+ records

---

## 7. Success Criteria

| Metric | Target |
|--------|--------|
| Schema detection accuracy | >95% |
| Field mapping coverage | >90% |
| Import success rate | >99% |
| Backward compatibility | 100% existing tests pass |
| Test coverage | 136 new tests |

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Service principal has no user_principal_name | Set is_service_principal=1, use service_principal_name |
| Location format varies | Parse into city/state/country components |
| Unknown schema variants | Store with schema_variant='UNKNOWN', log warning |
| Microsoft changes schemas | Version tracking, fuzzy matching |

---

## 9. Related Context

- **Phase 263**: Pattern matching fix (COMPLETE) - files now recognized
- **PIR-GOOD-SAMARITAN-777777**: Test case with 3 ZIPs using Graph API format
- **Current Verdict**: NO BREACH (attack window covered Nov 24 - Jan 8)
- **Gap Data**: Nov 4-23 (will be recovered after ETL pipeline complete)
