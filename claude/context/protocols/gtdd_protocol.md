# GTDD Protocol (Grafana Test-Driven Development)

**Version:** 1.0
**Created:** 2026-01-08
**Purpose:** Prevent debugging loops when developing/modifying Grafana dashboards
**Trigger:** User says "GTDD", "use TDD for Grafana", or "follow the Grafana protocol"

---

## Core Principle

**Never trust an automated test until you've manually verified one case in the target environment.**

---

## Phase 0: Environment Validation

Before any dashboard work, verify:

```bash
# 1. Database accessible
PGPASSWORD='...' psql -h localhost -U servicedesk_user -d servicedesk -c "SELECT 1"

# 2. Grafana running
curl -s -u admin:admin http://localhost:3000/api/health | jq .

# 3. Datasource configured
curl -s -u admin:admin http://localhost:3000/api/datasources | jq '.[].name'
```

---

## Phase 1: Red - Verify Actual Failure

### 1.1 Manual Query Test (MANDATORY)

Before writing ANY automated test, manually run ONE query in psql:

```bash
# Extract a query from dashboard JSON
PGPASSWORD='...' psql -h localhost -U servicedesk_user -d servicedesk << 'EOF'
-- Paste the raw query here, manually substituting variables:
-- ${team:raw} -> Cloud - Infrastructure','Cloud - Security','Cloud - L3 Escalation
-- $__timeFilter(col) -> col >= NOW() - INTERVAL '30 days'
SELECT COUNT(*) FROM servicedesk.tickets
WHERE "TKT-Team" IN ('Cloud - Infrastructure','Cloud - Security','Cloud - L3 Escalation');
EOF
```

### 1.2 Understand Grafana Variable Substitution

| Variable Pattern | Grafana Substitutes With | Your Test Must Do |
|------------------|--------------------------|-------------------|
| `'${team:raw}'` | `'Value1','Value2'` | Replace entire `'${team:raw}'` including quotes |
| `${team:raw}` | `Value1','Value2` (no outer quotes) | Replace just `${team:raw}` |
| `$__timeFilter(col)` | `col BETWEEN '...' AND '...'` | Replace with `col >= NOW() - INTERVAL '30 days'` or `1=1` |

**Critical:** If query has `IN ('${team:raw}')`, the `allValue` should NOT have outer quotes since Grafana adds them.

### 1.3 Automated Test Script Template

Only after manual verification passes, use this validated pattern:

```python
import psycopg2
import json
import os
import re

def test_dashboard_queries(dashboard_path: str) -> dict:
    """
    TDD-compliant dashboard query tester.
    Returns: {'ok': int, 'no_data': int, 'error': int, 'errors': []}
    """
    conn = psycopg2.connect(
        host='localhost', port=5432, database='servicedesk',
        user='servicedesk_user', password='...'
    )

    with open(dashboard_path) as f:
        data = json.load(f)

    dashboard = data.get('dashboard', data)
    results = {'ok': 0, 'no_data': 0, 'error': 0, 'errors': []}

    for panel in dashboard.get('panels', []):
        for target in panel.get('targets', []):
            sql = target.get('rawSql', '')
            if not sql:
                continue

            # CORRECT substitution - replace INCLUDING surrounding quotes
            test_sql = sql.replace(
                "'${team:raw}'",
                "'Cloud - Infrastructure','Cloud - Security','Cloud - L3 Escalation'"
            )
            test_sql = re.sub(r'\$__timeFilter\([^)]*\)', '1=1', test_sql)
            test_sql = re.sub(
                r'\$__timeGroup\([^)]+\)',
                "DATE_TRUNC('day', \"TKT-Created Time\")",
                test_sql
            )

            try:
                cur = conn.cursor()
                cur.execute(test_sql)
                rows = cur.fetchall()
                cur.close()

                if rows and rows[0][0] is not None:
                    results['ok'] += 1
                else:
                    results['no_data'] += 1
            except Exception as e:
                results['error'] += 1
                results['errors'].append({
                    'panel': panel.get('title'),
                    'error': str(e)[:150]
                })

    conn.close()
    return results
```

---

## Phase 2: Green - Fix Until Working

### 2.1 Common Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `syntax error at or near "\"` | JSON escaping issue | Check for `\\'` that should be `'` |
| `column "X" does not exist` | Wrong table/column | Verify schema: `\d servicedesk.tablename` |
| `relation does not exist` | Wrong schema | Add `servicedesk.` prefix |
| Double quotes in output | `''value''` | Check `allValue` doesn't have extra quotes |

### 2.2 Schema Reference Query

```sql
-- Get all columns for a table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'servicedesk'
  AND table_name = 'tickets'
ORDER BY ordinal_position;
```

### 2.3 Fix One Panel, Verify, Repeat

Do NOT batch fix. For each broken panel:
1. Fix the query
2. Run manual test in psql
3. Confirm it works
4. Move to next

---

## Phase 3: Verify in Target Environment

### 3.1 Reimport Dashboard

```python
import requests
import json

with open('dashboard.json') as f:
    data = json.load(f)

resp = requests.post(
    'http://localhost:3000/api/dashboards/db',
    json=data,
    auth=('admin', 'admin')
)
print(resp.json())
```

### 3.2 Visual Verification (REQUIRED)

Open Grafana in browser and verify:
- [ ] Dashboard loads without errors
- [ ] Team filter dropdown appears
- [ ] Selecting a team filters data correctly
- [ ] "All" option shows combined data
- [ ] Panels show expected data ranges

---

## Phase 4: Refactor

Only after all panels work:
- Optimize slow queries (add indexes if needed)
- Standardize panel naming
- Align grid positions
- Add descriptions

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Trust automated test without manual verification | Test script bugs mask real state | Always manual-test one query first |
| Batch fix multiple panels | Can't isolate which fix broke things | Fix one, verify, repeat |
| Assume query is broken because test fails | Test substitution may be wrong | Verify in psql with exact query |
| Fix JSON without understanding Grafana rendering | JSON escaping != Grafana behavior | Test in actual Grafana |

---

## Checklist Before Declaring Done

- [ ] Manual query test passed in psql
- [ ] Automated test shows 0 errors
- [ ] Dashboard reimported to Grafana
- [ ] Visual verification in browser completed
- [ ] Team filter works correctly
- [ ] Git commit with passing state

---

## Quick Reference: Variable Templating

```json
{
  "templating": {
    "list": [{
      "name": "team",
      "type": "custom",
      "query": "All,Team A,Team B",
      "multi": true,
      "includeAll": true,
      "allValue": "Team A','Team B",
      "current": {
        "text": ["All"],
        "value": ["All"]
      }
    }]
  }
}
```

**allValue explanation:** When user selects "All", Grafana substitutes `${team:raw}` with the `allValue`. Since the query has `IN ('${team:raw}')`, Grafana produces:
```sql
IN ('Team A','Team B')
```

Therefore `allValue` should NOT have outer quotes - Grafana adds them from the query pattern.
