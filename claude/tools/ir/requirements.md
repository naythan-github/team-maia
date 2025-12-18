# IR (Incident Response) Automation Tools - TDD Requirements

**Phase**: 224
**Created**: December 18, 2025
**Owner**: SRE Principal Engineer Agent
**Scale Target**: 100+ investigations/month

---

## 1. Problem Statement

Manual security investigation process takes 12+ hours per investigation:
- 4 hours initial triage (CSV parsing, pattern identification)
- 4 hours log analysis (cross-referencing, anomaly detection)
- 4 hours PIR creation (structuring findings)

With 100 investigations/month, this is unsustainable (1200+ hours/month).

### Lessons from Fyna Investigation

| Finding | Implication |
|---------|-------------|
| Safari on Windows = always spoofed | Need impossible UA detection |
| Budget VPS IPs (Hostinger) = high risk | Need IP enrichment |
| Multi-tenant apps don't appear in service principals | Need OAuth analysis |
| Customer explanations need verification | Need verification tracking |
| 4AM consent = suspicious | Need off-hours detection |

---

## 2. Component 1: IR Knowledge Base (`ir_knowledge.db`)

### 2.1 Purpose
Cumulative learning database storing IOCs, patterns, and verified apps across all investigations.

### 2.2 Schema Requirements

```sql
-- Core tables
investigations        -- Track each investigation
iocs                  -- Indicators of Compromise (IPs, domains, etc.)
suspicious_patterns   -- Detected patterns (spoofed UA, off-hours, etc.)
verified_apps         -- Known legitimate OAuth apps
customer_services     -- Verified third-party services per customer
attack_types          -- Taxonomy of attack types
```

### 2.3 Acceptance Criteria

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| KB-001 | Create new investigation record | Record created with ID, customer, date |
| KB-002 | Add IOC to investigation | IOC linked to investigation with context |
| KB-003 | Query IOC by IP address | Returns all investigations where IP appeared |
| KB-004 | Add suspicious pattern | Pattern stored with confidence score |
| KB-005 | Query patterns by type | Returns all instances of pattern type |
| KB-006 | Add verified OAuth app | App stored with permissions and verification date |
| KB-007 | Check if app is verified | Returns True/False with details |
| KB-008 | Add customer service mapping | Service linked to customer with expected IPs |
| KB-009 | Check if IP matches known service | Returns service name or None |
| KB-010 | Get investigation summary | Returns counts of IOCs, patterns, findings |

### 2.4 Sample Data (Fyna Investigation)

```python
# Investigation
investigation_id = "PIR-FYNA-2025-001"
customer = "Fyna Foods"
tenant = "fynafoods.onmicrosoft.com"
status = "OPEN"

# IOCs
iocs = [
    {"type": "ip", "value": "97.93.69.128", "context": "Malicious - rodneyt attack", "status": "BLOCKED"},
    {"type": "ip", "value": "93.127.215.4", "context": "zacd foreign access - Hostinger US", "status": "MONITOR"},
    {"type": "ip_range", "value": "2605:6400:*", "context": "michellev Azure CLI - FranTech", "status": "INVESTIGATE"},
]

# Patterns
patterns = [
    {"type": "impossible_ua", "signature": "Safari.*Windows", "confidence": 1.0},
    {"type": "off_hours_consent", "signature": "consent.*0[0-5]:[0-9]{2}", "confidence": 0.8},
    {"type": "budget_vps", "signature": "Hostinger|BuyVM|FranTech", "confidence": 0.7},
]

# Unverified apps
unverified_apps = [
    {"app_id": "683b8f3c-cc24-4eda-9fd3-bf7f29551704", "permissions": 89, "risk": "CRITICAL"},
    {"app_id": "239c5db2-f196-40ef-b83e-ed8f85e5cd49", "permissions": 50, "risk": "HIGH"},
    {"app_id": "b09caa3b-b4cd-4c15-b903-b5dd1f21dbe6", "permissions": 4, "risk": "MEDIUM"},
]
```

---

## 3. Component 2: Quick Triage Tool (`ir_quick_triage.py`)

### 3.1 Purpose
Automated first-pass analysis of investigation data. Flags HIGH/MEDIUM/LOW risk items.

### 3.2 Input Requirements

| Input Type | Format | Required Fields |
|------------|--------|-----------------|
| Sign-in logs | CSV | userPrincipalName, ipAddress, location, userAgent, appDisplayName, createdDateTime, status |
| Audit logs | CSV | activityDisplayName, initiatedBy, targetResources, activityDateTime |
| OAuth consents | CSV | clientId, consentType, scope, principalId |

### 3.3 Detection Rules

| Rule ID | Name | Logic | Confidence |
|---------|------|-------|------------|
| UA-001 | Impossible User Agent | Safari AND Windows | 1.0 (100%) |
| UA-002 | Spoofed Mobile | Mobile UA from datacenter IP | 0.9 (90%) |
| IP-001 | Known Malicious | IP in ir_knowledge.db malicious list | 1.0 (100%) |
| IP-002 | Budget VPS | IP matches Hostinger/BuyVM/etc. ASN | 0.7 (70%) |
| IP-003 | Datacenter IP | IP in known datacenter ranges | 0.6 (60%) |
| TIME-001 | Off-Hours Consent | OAuth consent 00:00-05:59 local | 0.8 (80%) |
| TIME-002 | Off-Hours Sign-in | Sign-in 00:00-05:59 local (non-automated) | 0.5 (50%) |
| OAUTH-001 | Excessive Permissions | App has >50 permissions | 0.9 (90%) |
| OAUTH-002 | Legacy Protocol Access | IMAP/POP/EAS permissions | 0.8 (80%) |
| OAUTH-003 | Unknown Multi-tenant App | App not in service principals | 0.7 (70%) |
| PATTERN-001 | Consistent Foreign IP | Single foreign IP over extended period | 0.6 (60%) |

### 3.4 Acceptance Criteria

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| QT-001 | Detect Safari on Windows | Flag as HIGH risk, UA-001 |
| QT-002 | Detect known malicious IP | Flag as HIGH risk, IP-001 |
| QT-003 | Detect Hostinger IP | Flag as MEDIUM risk, IP-002 |
| QT-004 | Detect 4AM consent | Flag as MEDIUM risk, TIME-001 |
| QT-005 | Detect 89-permission app | Flag as HIGH risk, OAUTH-001 |
| QT-006 | Detect legacy protocol consent | Flag as MEDIUM risk, OAUTH-002 |
| QT-007 | Process empty CSV | Return empty results, no error |
| QT-008 | Process malformed CSV | Return error with line number |
| QT-009 | Generate triage report | Markdown report with HIGH/MEDIUM/LOW sections |
| QT-010 | Cross-reference with knowledge base | Enrich findings with prior investigation data |

### 3.5 Output Format

```markdown
# Triage Report: {customer_name}
Generated: {timestamp}

## HIGH RISK (Immediate Investigation)

| User | Finding | Rule | Confidence | Details |
|------|---------|------|------------|---------|
| zacd@fyna.com.au | Impossible UA | UA-001 | 100% | Safari on Windows10 |

## MEDIUM RISK (Investigation Needed)

| User | Finding | Rule | Confidence | Details |
|------|---------|------|------------|---------|
| juliang@fyna.com.au | Off-hours consent | TIME-001 | 80% | 4:09 AM consent |

## LOW RISK (Monitor)

...

## CLEAN (No Action)

...

## Summary
- HIGH: 2 items
- MEDIUM: 4 items
- LOW: 3 items
- CLEAN: 45 items
```

---

## 4. Component 3: Knowledge Query Tool (`ir_knowledge_query.py`)

### 4.1 Purpose
CLI tool for quick lookups against the knowledge base.

### 4.2 Commands

```bash
# IP lookup
ir_knowledge_query.py ip 93.127.215.4
# Output: "Hostinger US - Budget VPS - seen in 1 investigation (Fyna Foods)"

# App lookup
ir_knowledge_query.py app 683b8f3c-cc24-4eda-9fd3-bf7f29551704
# Output: "UNKNOWN - Not in verified apps - 89 permissions - INVESTIGATE"

# Pattern check
ir_knowledge_query.py pattern "Safari.*Windows"
# Output: "Known impossible UA pattern - 100% confidence - always spoofed"

# Customer service check
ir_knowledge_query.py service fyna usemotion
# Output: "UNVERIFIED - zacd claims Usemotion, setup date not confirmed"

# Stats
ir_knowledge_query.py stats
# Output: "Investigations: 1, IOCs: 4, Patterns: 3, Verified Apps: 0"
```

### 4.3 Acceptance Criteria

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| KQ-001 | Query known malicious IP | Returns "MALICIOUS" with context |
| KQ-002 | Query unknown IP | Returns "UNKNOWN" |
| KQ-003 | Query verified app | Returns "VERIFIED" with permissions |
| KQ-004 | Query unverified app | Returns "UNVERIFIED" or "UNKNOWN" |
| KQ-005 | Query known pattern | Returns pattern details |
| KQ-006 | Query customer service | Returns verification status |
| KQ-007 | Get statistics | Returns counts for all tables |
| KQ-008 | Invalid command | Returns usage help |

---

## 5. Integration Requirements

### 5.1 Database Location
```
~/maia/claude/data/databases/intelligence/ir_knowledge.db
```

### 5.2 Tool Location
```
~/maia/claude/tools/ir/
├── requirements.md          # This file
├── ir_knowledge.py          # Database module
├── ir_quick_triage.py       # Triage tool
├── ir_knowledge_query.py    # CLI query tool
├── test_ir_knowledge.py     # Tests for knowledge base
├── test_ir_quick_triage.py  # Tests for triage tool
└── README.md                # Usage documentation
```

### 5.3 Dependencies
- Python 3.9+
- sqlite3 (standard library)
- csv (standard library)
- re (standard library)
- No external dependencies (production-ready)

---

## 6. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Triage time | 4 hours | 30 min | Time to first risk assessment |
| False positive rate | N/A | <10% | Manual review of flagged items |
| Pattern reuse | 0% | >80% | IOCs/patterns from prior investigations |
| Investigation time | 12 hours | 3 hours | Total time per investigation |

---

## 7. Test Execution

```bash
# Run all tests
cd ~/maia/claude/tools/ir
python3 -m pytest test_*.py -v

# Run specific test
python3 -m pytest test_ir_knowledge.py::test_add_ioc -v
```

---

**Document Status**: REQUIREMENTS COMPLETE - Ready for test implementation
