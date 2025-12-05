# PMP API Reference - Confirmed Endpoints

**Last Updated**: 2025-12-05
**Source**: Live testing against TEST and PROD instances
**Status**: Production validated

---

## Overview

ManageEngine Patch Manager Plus (PMP) Cloud API endpoints confirmed through systematic testing. This document captures all working endpoints, required scopes, and lessons learned from implementation.

**Base URLs**:
- PROD: `https://patch.manageengine.com.au`
- TEST: `https://patch.manageengine.com.au` (trial instance)

**Authentication**: OAuth 2.0 with Zoho-specific header format

---

## READ Endpoints (19 Confirmed)

### Patch Management - Summary & Reporting

| # | Endpoint | Type | Scope | Data Key | Description |
|---|----------|------|-------|----------|-------------|
| 1 | `/api/1.4/patch/summary` | Simple | PatchMgmt.READ | - | High-level patch module summary |
| 2 | `/api/1.4/patch/systemreport` | Param | PatchMgmt.READ | `?resid={id}` | Per-system patch details |
| 3 | `/api/1.4/patch/updatedbstatus` | Simple | PatchMgmt.READ | - | Patch DB update status |

### Patch Management - Patch Queries

| # | Endpoint | Type | Scope | Data Key | Records | Description |
|---|----------|------|-------|----------|---------|-------------|
| 4 | `/api/1.4/patch/allpatches` | Paginated | PatchMgmt.READ | `allpatches` | ~5,217 | All patches for managed systems |
| 5 | `/api/1.4/patch/allpatchdetails` | Param | PatchMgmt.READ | `?patchid={id}` | per-patch | Patch status across all systems |
| 6 | `/api/1.4/patch/supportedpatches` | Paginated | PatchMgmt.READ | `supportedpatches` | ~364,673 | Master patch catalog |
| 7 | `/api/1.4/patch/installedpatches` | Paginated | PatchMgmt.READ | `installedpatches` | ~3,505 | Installed patch summary |
| 8 | `/api/1.4/patch/missingpatches` | Paginated | PatchMgmt.READ | `missingpatches` | ~1,712 | Missing patch summary |

### Patch Management - System Queries

| # | Endpoint | Type | Scope | Data Key | Records | Description |
|---|----------|------|-------|----------|---------|-------------|
| 9 | `/api/1.4/patch/allsystems` | Paginated | PatchMgmt.READ | `allsystems` | ~3,364 | All systems with patch status |
| 10 | `/api/1.4/patch/scandetails` | Paginated | PatchMgmt.READ | `scandetails` | ~3,364 | Systems with scan metadata |

### Patch Management - Configuration & Policy

| # | Endpoint | Type | Scope | Data Key | Records | Description |
|---|----------|------|-------|----------|---------|-------------|
| 11 | `/api/1.4/patch/deploymentpolicies` | Paginated | PatchMgmt.READ | `deploymentpolicies` | ~92 | Deployment policies |
| 12 | `/api/1.4/patch/healthpolicy` | Simple | PatchMgmt.READ | - | 1 | Health policy settings |
| 13 | `/api/1.4/patch/viewconfig` | Paginated | PatchMgmt.READ | `viewconfig` | ~225 | Deployment configurations |
| 14 | `/api/1.4/patch/approvalsettings` | Simple | PatchMgmt.READ | - | 1 | Patch approval settings |

### System on Management (SoM)

| # | Endpoint | Type | Scope | Data Key | Records | Description |
|---|----------|------|-------|----------|---------|-------------|
| 15 | `/api/1.4/som/summary` | Simple | Common.READ | - | 1 | SoM module summary |
| 16 | `/api/1.4/som/computers` | Paginated | Common.READ | `computers` | ~3,317 | All computers & agent details |
| 17 | `/api/1.4/som/remoteoffice` | Paginated | SOM.READ | `remoteoffice` | varies | Remote office configurations |

### DCAPI Endpoints (Enhanced)

| # | Endpoint | Type | Scope | Data Key | Description |
|---|----------|------|-------|----------|-------------|
| 18 | `/dcapi/threats/patches` | Paginated | PatchMgmt.READ | `patches` | Enhanced patch list with filtering |
| 19 | `/dcapi/threats/systemreport/patches` | Paginated | PatchMgmt.READ | `systemreport` | System-patch mappings (bulk) |

---

## WRITE Endpoints (10 Confirmed on TEST Instance)

### Patch Approval Actions

| # | Endpoint | Method | API Ver | Scope | Description |
|---|----------|--------|---------|-------|-------------|
| 1 | `/api/1.4/patch/approvepatch` | POST | 1.4 | PatchMgmt.WRITE | Approve patches for deployment |
| 2 | `/api/1.4/patch/unapprovepatch` | POST | 1.4 | PatchMgmt.WRITE | Remove approval from patches |
| 3 | `/api/1.4/patch/declinepatch` | POST | 1.4 | PatchMgmt.WRITE | Decline patches (mark as skip) |

### Patch Deployment Actions

| # | Endpoint | Method | API Ver | Scope | Description |
|---|----------|--------|---------|-------|-------------|
| 4 | `/api/1.3/patch/installpatch` | POST | **1.3** | PatchMgmt.WRITE | Deploy patches to systems |
| 5 | `/api/1.3/patch/uninstallpatch` | POST | **1.3** | PatchMgmt.WRITE | Remove patches (Windows only) |

**Note**: Install/uninstall endpoints use API version **1.3**, not 1.4!

### Patch Download Actions

| # | Endpoint | Method | API Ver | Scope | Description |
|---|----------|--------|---------|-------|-------------|
| 6 | `/api/1.4/patch/downloadpatch` | POST | 1.4 | PatchMgmt.WRITE | Pre-download patches to server |

### Scan Actions

| # | Endpoint | Method | API Ver | Scope | Description |
|---|----------|--------|---------|-------|-------------|
| 7 | `/api/1.4/patch/computers/scan` | POST | 1.4 | PatchMgmt.WRITE | Scan specific computers |
| 8 | `/api/1.4/patch/computers/scanall` | POST | 1.4 | PatchMgmt.WRITE | Scan all managed computers |

### Database Actions

| # | Endpoint | Method | API Ver | Scope | Description |
|---|----------|--------|---------|-------|-------------|
| 9 | `/api/1.4/patch/updatedb` | POST | 1.4 | PatchMgmt.WRITE | Trigger patch DB update |
| 10 | `/api/1.4/patch/dbupdatestatus` | GET | 1.4 | PatchMgmt.READ | Check DB update status |

---

## OAuth Configuration

### Required Scopes

```
PatchManagerPlusCloud.Common.READ
PatchManagerPlusCloud.PatchMgmt.READ
PatchManagerPlusCloud.PatchMgmt.WRITE  # For write operations
PatchManagerPlusCloud.SOM.READ         # For SoM endpoints
```

### Authorization Header Format

```http
Authorization: Zoho-oauthtoken {access_token}
```

**Critical**: Do NOT use `Bearer` format - Zoho requires `Zoho-oauthtoken` prefix.

### Token Refresh

- Access tokens expire in ~60 minutes
- Use refresh token before expiry (recommend 80% TTL threshold)
- Store refresh token securely (macOS Keychain recommended)

---

## Pagination

### Standard Pagination (REST API 1.4)

```
GET /api/1.4/patch/allpatches?page=1
```

- Page size: **25 records** (fixed, not configurable)
- Response includes `total` field for total record count
- Calculate total pages: `ceil(total / 25)`

### DCAPI Pagination

```
GET /dcapi/threats/systemreport/patches?page=1&pageLimit=30
```

- Page size: **30 records** (default, configurable via `pageLimit`)
- Maximum `pageLimit`: 100

---

## Response Structure

### Standard Wrapper

```json
{
  "message_response": {
    "total": 5217,
    "allpatches": [
      {"patch_id": 1, "bulletin_id": "KB123456", ...},
      ...
    ]
  }
}
```

### Multi-Field Data Keys

Some endpoints return data in alternative field names:

| Endpoint | Primary Key | Alternative Keys |
|----------|-------------|------------------|
| `/api/1.4/patch/allsystems` | `allsystems` | `computers` |
| `/api/1.4/patch/scandetails` | `scandetails` | `computers` |
| `/api/1.4/som/computers` | `computers` | - |

**Always check multiple field names when parsing responses.**

---

## Lessons Learned

### Critical Issues Discovered

| Issue | Impact | Resolution | Reference |
|-------|--------|------------|-----------|
| **PRIMARY KEY bug** | 99.98% data loss (58,591 records lost) | Use `patch_id` as PK, not `update_id` | PRIMARY_KEY_BUG_POSTMORTEM.md |
| **OAuth scope prefix** | 401 Unauthorized | Must use `PatchManagerPlusCloud.*` prefix | pmp_oauth_manager.py |
| **Auth header format** | API rejection | Use `Zoho-oauthtoken` NOT `Bearer` | Bug fix #2 |
| **Single field checking** | Missing data | Check multiple data key alternatives | Bug fix #3 |
| **HTML throttling** | JSON parse errors | Detect `<!DOCTYPE` before JSON parsing | Bug fix #4 |
| **Install API version** | 404 errors | Use API **1.3** for install/uninstall | pmp_action_handler.py |

### Field Uniqueness Warning

| Field | Unique? | Safe as PK? | Notes |
|-------|---------|-------------|-------|
| `patch_id` | Yes | Yes | Globally unique identifier |
| `update_id` | **No** | **No** | Sequential 0-9 repeating! |
| `resource_id` | Yes | Yes | System unique identifier |
| `template_id` | Yes | Yes | Policy unique identifier |

### Rate Limiting

- **Requests per second**: ~4 (0.25s delay recommended)
- **Daily quota**: Limited (varies by plan)
- **Throttling response**: HTML page (not JSON)
- **429 handling**: Honor `Retry-After` header

---

## Request Examples

### Approve Patches

```bash
curl -X POST "https://patch.manageengine.com.au/api/1.4/patch/approvepatch" \
  -H "Authorization: Zoho-oauthtoken {token}" \
  -H "Content-Type: application/json" \
  -d '{"PatchIDs": [12345, 12346]}'
```

### Deploy Patches (Draft Mode)

```bash
curl -X POST "https://patch.manageengine.com.au/api/1.3/patch/installpatch" \
  -H "Authorization: Zoho-oauthtoken {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "PatchIDs": [12345],
    "ConfigName": "Test Deployment",
    "DeploymentPolicyTemplateID": 1,
    "actionToPerform": "Draft"
  }'
```

### Paginated Read

```bash
curl "https://patch.manageengine.com.au/api/1.4/patch/allpatches?page=1" \
  -H "Authorization: Zoho-oauthtoken {token}"
```

---

## Environment Safety

### Environment Isolation

| Environment | Keychain Account | Color Code | Safety |
|-------------|-----------------|------------|--------|
| TEST | `naythan.me@londonxyz.com` | Green | Safe for testing |
| PROD | `mspcentral@icloud.com` | Red | Requires confirmation |

### Safety Protocol

1. **Always set `PMP_ENV`** before any operations
2. **Write operations**: Require explicit environment selection
3. **Draft mode**: Use `actionToPerform: "Draft"` for safe testing
4. **Prod writes**: Require additional confirmation flag

```bash
# Safe testing
PMP_ENV=TEST python3 pmp_action_handler.py approve --patch-ids 12345

# Production (blocked without confirmation)
PMP_ENV=PROD python3 pmp_action_handler.py approve --patch-ids 12345
# Error: Production writes require --confirm-prod flag
```

---

## Tools Reference

| Tool | Purpose | Usage |
|------|---------|-------|
| `pmp_oauth_manager_v2.py` | Environment-aware OAuth | `PMPOAuthManagerV2()` |
| `pmp_action_handler.py` | Write operations | `PMP_ENV=TEST python3 pmp_action_handler.py` |
| `pmp_endpoint_validator_v2.py` | Test all endpoints | `PMP_ENV=TEST python3 pmp_endpoint_validator_v2.py` |
| `pmp_complete_intelligence_extractor.py` | Full data extraction | `python3 pmp_complete_intelligence_extractor.py` |
| `pmp_dcapi_patch_extractor.py` | DCAPI bulk extraction | `python3 pmp_dcapi_patch_extractor.py` |

---

## Related Documentation

- [PRIMARY_KEY_BUG_POSTMORTEM.md](PRIMARY_KEY_BUG_POSTMORTEM.md) - Critical data loss incident
- [TEST_EXECUTION_GUIDE.md](TEST_EXECUTION_GUIDE.md) - Test execution procedures
- [../pmp_tdd_checklist.md](../pmp_tdd_checklist.md) - Mandatory TDD checklist

---

**Prepared by**: SRE Principal Engineer Agent
**Validated**: 2025-12-05
**Next Review**: On any new endpoint discovery
