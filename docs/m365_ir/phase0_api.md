# M365 IR Phase 0 Auto-Checks - API Documentation

## Module: `claude.tools.m365_ir.phase0_auto_checks`

### Core Functions

#### `check_foreign_baseline(db_path, override_home_country=None)`

Check for foreign login baseline anomalies.

**Parameters**:
- `db_path` (str): Path to M365 IR investigation database
- `override_home_country` (str, optional): Override auto-detected home country

**Returns**:
```python
{
    'status': 'FLAGGED' | 'OK' | 'NO_DATA',
    'message': str,
    'home_country': str,
    'accounts': [{'upn': str, 'countries': [str]}]  # If FLAGGED
}
```

**Example**:
```python
from claude.tools.m365_ir.phase0_auto_checks import check_foreign_baseline

result = check_foreign_baseline('/path/to/investigation.db', override_home_country='AU')
if result['status'] == 'FLAGGED':
    print(f"Foreign logins detected from: {result['accounts']}")
```

---

#### `analyze_password_hygiene(db_path, exclude_passwordless=False)`

Analyze password hygiene metrics.

**Parameters**:
- `db_path` (str): Path to investigation database
- `exclude_passwordless` (bool): Exclude FIDO2/passwordless accounts

**Returns**:
```python
{
    'risk': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'OK' | 'NO_DATA',
    'total_accounts': int,
    'over_1_year': int,
    'over_2_years': int,
    'over_3_years': int,
    'pct_over_1_year': float
}
```

**Example**:
```python
result = analyze_password_hygiene('/path/to/db', exclude_passwordless=True)
print(f"Risk: {result['risk']}, {result['pct_over_1_year']}% passwords >1 year")
```

---

#### `analyze_password_hygiene_with_context(db_path)`

Analyze password hygiene with MFA context (Sprint 2 - B1).

**Parameters**:
- `db_path` (str): Path to investigation database

**Returns**:
```python
{
    'risk': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'OK' | 'NO_DATA',
    'total_accounts': int,
    'over_1_year': int,
    'pct_over_1_year': float,
    'mfa_rate': float | None,  # Percentage (0-100)
    'context': 'PRIMARY_VULNERABILITY' | 'SECONDARY_VULNERABILITY' | 'MODERATE_RISK' | 'UNKNOWN_MFA'
}
```

**Example**:
```python
result = analyze_password_hygiene_with_context('/path/to/db')
if result['context'] == 'PRIMARY_VULNERABILITY':
    print(f"URGENT: Password is primary security control (MFA: {result['mfa_rate']}%)")
```

---

#### `detect_dormant_accounts(db_path, exclude_service=True, window_days=60, breakglass_whitelist=None)`

Detect dormant accounts with intelligent exclusions (Sprint 2 - B2, B3).

**Parameters**:
- `db_path` (str): Path to investigation database
- `exclude_service` (bool): Exclude service accounts (default: True)
- `window_days` (int): Lookback window in days (default: 60)
- `breakglass_whitelist` (list): UPNs to exclude

**Returns**:
```python
{
    'dormant_accounts': [{'upn': str, 'days_since_login': int | None}],
    'excluded_service_accounts': [str],  # If exclude_service=True
    'excluded_breakglass_accounts': [str]  # If breakglass_whitelist provided
}
```

**Example**:
```python
whitelist = load_breakglass_whitelist()  # From config file
result = detect_dormant_accounts('/path/to/db', breakglass_whitelist=whitelist)
print(f"Dormant: {len(result['dormant_accounts'])}, Excluded service: {len(result['excluded_service_accounts'])}")
```

---

#### `get_admin_accounts(db_path, fallback_to_naming=True)`

Get admin accounts by role assignment (Sprint 2 - B5).

**Parameters**:
- `db_path` (str): Path to investigation database
- `fallback_to_naming` (bool): Use naming patterns if no role data (default: True)

**Returns**:
- `set`: Set of UPNs identified as admin accounts

**Example**:
```python
admins = get_admin_accounts('/path/to/db')
print(f"Admin accounts: {len(admins)}")
for admin in admins:
    print(f"  - {admin}")
```

---

#### `detect_logging_tampering(db_path)`

Detect audit logging tampering (Sprint 3 - C1, MITRE T1562.008).

**Parameters**:
- `db_path` (str): Path to investigation database

**Returns**:
```python
{
    'logging_changes': [
        {
            'timestamp': str,
            'activity': str,
            'user': str,
            'source': 'entra_audit_log' | 'unified_audit_log'
        }
    ],
    'risk_level': 'CRITICAL' | 'OK',
    'mitre_technique': 'T1562.008'
}
```

**Example**:
```python
result = detect_logging_tampering('/path/to/db')
if result['risk_level'] == 'CRITICAL':
    print(f"ALERT: {len(result['logging_changes'])} logging configuration changes detected")
    for change in result['logging_changes']:
        print(f"  {change['timestamp']}: {change['activity']} by {change['user']}")
```

---

#### `detect_impossible_travel(db_path, speed_threshold_mph=500)`

Detect geographically impossible travel (Sprint 3 - C2).

**Parameters**:
- `db_path` (str): Path to investigation database
- `speed_threshold_mph` (int): Maximum reasonable speed (default: 500)

**Returns**:
```python
{
    'impossible_travel_events': [
        {
            'upn': str,
            'login1': {'timestamp': str, 'country': str, 'coords': str},
            'login2': {'timestamp': str, 'country': str, 'coords': str},
            'distance_km': float,
            'time_hours': float,
            'speed_mph': float,
            'threshold_mph': int
        }
    ],
    'risk_level': 'CRITICAL' | 'OK'
}
```

**Example**:
```python
result = detect_impossible_travel('/path/to/db')
for event in result['impossible_travel_events']:
    print(f"ALERT: {event['upn']} traveled {event['distance_km']}km in {event['time_hours']}h ({event['speed_mph']} mph)")
```

---

#### `detect_mfa_bypass(db_path, threshold_hours=24)`

Detect MFA bypass attempts (Sprint 3 - C3).

**Parameters**:
- `db_path` (str): Path to investigation database
- `threshold_hours` (int): Maximum time between enable/disable (default: 24)

**Returns**:
```python
{
    'mfa_bypass_attempts': [
        {
            'upn': str,
            'enabled_timestamp': str,
            'disabled_timestamp': str,
            'time_delta_hours': float,
            'threshold_hours': int
        }
    ],
    'risk_level': 'CRITICAL' | 'HIGH' | 'OK'  # CRITICAL if <1 hour
}
```

**Example**:
```python
result = detect_mfa_bypass('/path/to/db')
if result['mfa_bypass_attempts']:
    print(f"ALERT: {len(result['mfa_bypass_attempts'])} MFA bypass attempts detected")
    for attempt in result['mfa_bypass_attempts']:
        print(f"  {attempt['upn']}: MFA disabled {attempt['time_delta_hours']}h after enabling")
```

---

### Utility Functions

#### `is_service_account(upn)`

Check if account matches service account patterns (Sprint 2 - B2).

**Parameters**:
- `upn` (str): User principal name

**Returns**:
- `bool`: True if service account

**Example**:
```python
if is_service_account('svc_backup@contoso.com'):
    print("Service account detected")
```

---

#### `load_breakglass_whitelist()`

Load break-glass account whitelist from config (Sprint 2 - B3).

**Returns**:
- `list`: List of whitelisted UPNs

**Config File**: `~/.maia/config/breakglass_accounts.json`

**Example**:
```python
whitelist = load_breakglass_whitelist()
print(f"Whitelisted accounts: {whitelist}")
```

---

#### `get_passwordless_accounts(db_path)`

Get accounts using FIDO2/passwordless auth (Sprint 2 - B4).

**Parameters**:
- `db_path` (str): Path to investigation database

**Returns**:
- `set`: Set of UPNs using passwordless auth

**Example**:
```python
passwordless = get_passwordless_accounts('/path/to/db')
print(f"Passwordless accounts: {len(passwordless)}")
```

---

#### `calculate_distance(lat1, lon1, lat2, lon2)`

Calculate great circle distance using Haversine formula (Sprint 3 - C2 helper).

**Parameters**:
- `lat1, lon1` (float): First point coordinates (degrees)
- `lat2, lon2` (float): Second point coordinates (degrees)

**Returns**:
- `float`: Distance in kilometers

**Example**:
```python
# NYC to Beijing
distance = calculate_distance(40.7128, -74.0060, 39.9042, 116.4074)
print(f"Distance: {distance:.2f} km")  # ~10,989 km
```

---

## Module: `claude.tools.m365_ir.phase0_cli`

### CLI Integration

#### `run_phase0_checks(db_path, output_format='summary')`

Run all Phase 0 checks and return consolidated results.

**Parameters**:
- `db_path` (str): Path to investigation database
- `output_format` (str): Output format ('json', 'table', 'summary')

**Returns**:
```python
{
    'timestamp': str,  # ISO format
    'database': str,
    'checks': {
        'password_hygiene': {...},
        'foreign_baseline': {...},
        'dormant_accounts': {...},
        'admin_accounts': {...},
        'logging_tampering': {...},
        'impossible_travel': {...},
        'mfa_bypass': {...}
    },
    'summary': {
        'critical': int,
        'high': int,
        'medium': int,
        'ok': int,
        'total_checks': int
    }
}
```

**Example**:
```python
from claude.tools.m365_ir.phase0_cli import run_phase0_checks

results = run_phase0_checks('/path/to/db', output_format='json')
print(f"Critical issues: {results['summary']['critical']}")

if results['checks']['impossible_travel']['risk_level'] == 'CRITICAL':
    # Handle impossible travel
    pass
```

---

#### `format_json(results)`, `format_table(results)`, `format_summary(results)`

Format results for display.

**Parameters**:
- `results` (dict): Output from `run_phase0_checks()`

**Returns**:
- `str`: Formatted output

**Example**:
```python
from claude.tools.m365_ir.phase0_cli import run_phase0_checks, format_table

results = run_phase0_checks('/path/to/db')
print(format_table(results))
```

---

## Database Schema Requirements

Phase 0 checks require the following tables:

**Required**:
- `password_status` (columns: `user_principal_name`, `last_password_change`, `mfa_status`, `auth_method`)
- `sign_in_logs` (columns: `user_principal_name`, `timestamp`, `location_country`, `latitude`, `longitude`, `auth_method`)

**Optional** (features degrade gracefully if missing):
- `entra_audit_log` (columns: `timestamp`, `activity`, `initiated_by`, `target_user`, `result`)
- `unified_audit_log` (columns: `timestamp`, `user_id`, `operation`, `result_status`)
- `mfa_changes` (columns: `user`, `timestamp`, `activity_display_name`, `result`)

**NULL Handling**: All queries explicitly filter NULL values (A4 pattern)

---

## Error Handling

All functions use try/finally for resource management (A2 pattern):

```python
conn = sqlite3.connect(db_path)
try:
    # Query and process
    ...
finally:
    conn.close()  # Always executed
```

**SQL Injection Prevention**: All queries use parameterized queries (A1 pattern):

```python
# Good (A1 compliant)
conn.execute("SELECT * FROM users WHERE upn = ?", (upn,))

# Bad (SQL injection risk)
conn.execute(f"SELECT * FROM users WHERE upn = '{upn}'")
```

---

## Integration Examples

### SOAR Integration

```python
from claude.tools.m365_ir.phase0_cli import run_phase0_checks

def handle_m365_incident(incident_id, db_path):
    """SOAR playbook integration"""
    results = run_phase0_checks(db_path, output_format='json')

    # Escalate critical issues
    if results['summary']['critical'] > 0:
        create_high_priority_ticket(incident_id, results)

    # Auto-remediate impossible travel
    for event in results['checks']['impossible_travel']['impossible_travel_events']:
        disable_account(event['upn'])
        force_password_reset(event['upn'])

    return results
```

### SIEM Integration

```python
import json
from claude.tools.m365_ir.phase0_cli import run_phase0_checks

def send_to_siem(db_path):
    """Send Phase 0 results to SIEM"""
    results = run_phase0_checks(db_path, output_format='json')

    # Send to Splunk/Sentinel/etc
    siem_event = {
        'sourcetype': 'm365_ir_phase0',
        'event': results
    }

    send_to_siem_endpoint(json.dumps(siem_event))
```

---

**Version**: 1.0.0 (Sprint 4)
**Last Updated**: 2026-01-10
