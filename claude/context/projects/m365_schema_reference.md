# M365 Schema Reference - Exact CSV Headers

**Purpose**: Reference for Phase 264 ETL Pipeline implementation
**Source**: PIR-GOOD-SAMARITAN-777777 Graph API exports
**Created**: 2026-01-10

---

## 1. Legacy Portal Export (Current - Working)

**File Pattern**: `*SignInLogs.csv`, `01_*SignInLogs.csv`

**Headers**:
```
CreatedDateTime,UserPrincipalName,UserDisplayName,AppDisplayName,IPAddress,City,Country,Device,Browser,OS,Status,RiskState,RiskLevelDuringSignIn,RiskLevelAggregated,ConditionalAccessStatus
```

**Fingerprint Columns**: `CreatedDateTime`, `UserPrincipalName`, `AppDisplayName`

---

## 2. Graph API InteractiveSignIns

**File Pattern**: `*InteractiveSignIns*.csv` (excluding `*AuthDetails*`)

**Headers** (56 columns):
```
Date (UTC),Request ID,User agent,Correlation ID,User ID,User,Username,User type,Cross tenant access type,Incoming token type,Authentication Protocol,Unique token identifier,Original transfer method,Client credential type,Token Protection - Sign In Session,Token Protection - Sign In Session StatusCode,Application,Application ID ,App owner tenant ID,Resource,Resource ID ,Resource tenant ID,Resource owner tenant ID,Home tenant ID,Home tenant name,IP address,Location,Status,Sign-in error code,Failure reason,Client app,Device ID,Browser,Operating System,Compliant,Managed,Join Type,Multifactor authentication result,Multifactor authentication auth method,Multifactor authentication auth detail,Authentication requirement,Sign-in identifier,Session ID,IP address (seen by resource),Through Global Secure Access,Global Secure Access IP address,Autonomous system  number,Flagged for review,Token issuer type,Incoming token type,Token issuer name,Latency,Conditional Access,Managed Identity type,Associated Resource Id,Federated Token Id,Federated Token Issuer
```

**Fingerprint Columns**: `Date (UTC)`, `Username`, `User`, `Client app`

**Key Field Mappings**:
| Graph API Field | Canonical Field |
|-----------------|-----------------|
| Date (UTC) | timestamp |
| Username | user_principal_name |
| User | user_display_name |
| User ID | user_id |
| Application | app_display_name |
| Application ID  | app_id |
| IP address | ip_address |
| Location | location_raw (needs parsing: "City, State, Country") |
| Status | status_raw |
| Sign-in error code | status_error_code |
| Failure reason | failure_reason |
| Client app | client_app |
| Browser | browser |
| Operating System | os |
| Compliant | device_compliant |
| Managed | device_managed |
| Join Type | device_join_type |
| Conditional Access | conditional_access_status |
| Correlation ID | correlation_id |
| Request ID | request_id |
| Multifactor authentication result | mfa_result |
| Authentication requirement | auth_requirement |
| Latency | latency_ms |

---

## 3. Graph API ApplicationSignIns (Service Principal)

**File Pattern**: `*ApplicationSignIns*.csv`

**Headers** (22 columns):
```
Date (UTC),Request ID,Correlation ID,Service principal ID,Service principal name,Credential key ID,Credential thumbprint,Application,Application ID ,App owner tenant ID,Resource,Resource ID ,Resource tenant ID,Resource owner tenant ID,Home tenant ID,Home tenant name,IP address,Location,Status,Sign-in error code,Failure reason,Conditional Access
```

**Fingerprint Columns**: `Date (UTC)`, `Service principal ID`, `Service principal name`, `Credential key ID`

**CRITICAL**: NO USER FIELDS - set `is_service_principal=1`, `user_principal_name=NULL`

**Key Field Mappings**:
| Graph API Field | Canonical Field |
|-----------------|-----------------|
| Date (UTC) | timestamp |
| Service principal ID | service_principal_id |
| Service principal name | service_principal_name |
| Application | app_display_name |
| Application ID  | app_id |
| IP address | ip_address |
| Location | location_raw |
| Status | status_raw |
| Sign-in error code | status_error_code |
| Failure reason | failure_reason |
| Conditional Access | conditional_access_status |
| Credential key ID | credential_key_id |
| Credential thumbprint | credential_thumbprint |
| Resource | resource_display_name |
| Resource ID  | resource_id |

---

## 4. Graph API NonInteractiveSignIns

**File Pattern**: `*NonInteractiveSignIns*.csv` (excluding `*AuthDetails*`)

**Headers**: Same as InteractiveSignIns (56 columns)

**Sign-in Type**: `noninteractive` (background SSO, token refresh)

---

## 5. Graph API MSISignIns

**File Pattern**: `*MSISignIns*.csv`

**Headers**: (need to extract - similar to ApplicationSignIns)

**Sign-in Type**: `managed_identity` (Azure Managed Identity)

---

## Schema Detection Algorithm

```python
def detect_schema_variant(headers: List[str]) -> SchemaVariant:
    header_set = set(h.strip().strip('"') for h in headers)

    # Check fingerprints in priority order
    if "Service principal ID" in header_set:
        return SchemaVariant.GRAPH_APPLICATION
    elif "Date (UTC)" in header_set and "Username" in header_set:
        if "Managed Identity type" in header_set:
            return SchemaVariant.GRAPH_MSI
        return SchemaVariant.GRAPH_INTERACTIVE  # or NONINTERACTIVE based on filename
    elif "CreatedDateTime" in header_set:
        return SchemaVariant.LEGACY_PORTAL
    else:
        return SchemaVariant.UNKNOWN
```

---

## Date Format Reference

| Schema | Date Field | Format | Example |
|--------|------------|--------|---------|
| Legacy Portal | CreatedDateTime | AU/US ambiguous | `3/12/2025 7:22:01 AM` |
| Graph API | Date (UTC) | ISO 8601 | `2025-12-04T08:19:41Z` |
| PowerShell | createdDateTime | ISO 8601 | `2025-12-04T08:19:41.000Z` |

---

## Location Parsing

**Legacy**: Separate `City`, `Country` columns

**Graph API**: Combined `Location` field
- Format: `City, State, Country`
- Example: `Melbourne, Victoria, AU`
- Parse with: `city, state, country = location.rsplit(', ', 2)`
