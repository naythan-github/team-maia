# Phase 0 Usage Protocol - MANDATORY
## Preventing Automation-Induced Laziness

**Created**: 2026-01-11
**Incident**: PIR-SGS-785634523 - Missed active breach due to stopping at Phase 0
**Lesson**: Phase 0 is MILE ZERO, not the finish line

---

## CRITICAL PRINCIPLE

**Phase 0 Auto-Checks = TRIAGE, NOT INVESTIGATION**

Phase 0 is designed to:
- ✅ Identify systemic vulnerabilities (password hygiene, MFA bypass, etc.)
- ✅ Flag high-priority items for investigation
- ✅ Save time on manual checks
- ✅ Provide baseline security posture

Phase 0 does NOT:
- ❌ Investigate individual compromised accounts
- ❌ Analyze conditional access failures
- ❌ Search for exfiltration indicators
- ❌ Build attack timelines
- ❌ Cross-reference risky users with actual activity

---

## MANDATORY POST-PHASE-0 WORKFLOW

### Step 1: Run Phase 0 (Automated)
```bash
python3 claude/tools/m365_ir/phase0_cli.py <db_path>
```

### Step 2: IMMEDIATE Deep Dive (Manual - DO NOT SKIP)

#### A. Investigate Every HIGH RISK User (Mandatory)

For EACH user flagged by Phase 0 or in risky_users table with HIGH/MEDIUM risk:

```sql
-- 1. Get all sign-ins for this user
SELECT timestamp, location_country, location_city, ip_address,
       app_display_name, conditional_access_status
FROM sign_in_logs
WHERE user_principal_name = '<USER>'
ORDER BY timestamp DESC;

-- 2. Check for blocked attempts
SELECT timestamp, location_country, ip_address,
       status_error_code, status_failure_reason
FROM sign_in_logs
WHERE user_principal_name = '<USER>'
  AND conditional_access_status = 'failure';

-- 3. Search UAL for suspicious activity
SELECT timestamp, operation, client_ip, object_id
FROM unified_audit_log
WHERE user_id = '<USER>'
  AND operation IN (
    'AnonymousLinkCreated',
    'SharingLinkCreated',
    'New-InboxRule',
    'Set-Mailbox'
  )
ORDER BY timestamp DESC;

-- 4. Check mailbox activity
SELECT timestamp, operation, client_ip, folder_path, subject
FROM mailbox_audit_log
WHERE user = '<USER>'
ORDER BY timestamp DESC;
```

**DO NOT proceed to next user until current user is cleared or flagged for containment.**

#### B. Search for Exfiltration Indicators (All Users)

```sql
-- Anonymous link creations (all users)
SELECT timestamp, user_id, object_id, client_ip
FROM unified_audit_log
WHERE operation = 'AnonymousLinkCreated'
ORDER BY timestamp DESC;

-- High-volume file downloads
SELECT user_id, operation, COUNT(*) as count
FROM unified_audit_log
WHERE operation IN ('FileDownloaded', 'FileSyncDownloadedFull')
GROUP BY user_id, operation
HAVING count > 100
ORDER BY count DESC;

-- External forwarding rules
SELECT user, rule_name, forward_to, redirect_to
FROM inbox_rules
WHERE (forward_to NOT LIKE '%<customer_domain>%' AND forward_to != '')
   OR (redirect_to NOT LIKE '%<customer_domain>%' AND redirect_to != '');
```

#### C. Analyze Conditional Access Failures (All Users)

```sql
-- Get all blocked login attempts
SELECT location_country, COUNT(*) as attempts,
       COUNT(DISTINCT user_principal_name) as users,
       COUNT(DISTINCT ip_address) as ips
FROM sign_in_logs
WHERE conditional_access_status = 'failure'
GROUP BY location_country
ORDER BY attempts DESC;

-- Detail blocked attempts from unexpected countries
SELECT timestamp, user_principal_name, location_country,
       location_city, ip_address, app_display_name
FROM sign_in_logs
WHERE conditional_access_status = 'failure'
  AND location_country NOT IN (<known_overseas_countries>)
ORDER BY timestamp DESC;
```

#### D. Cross-Reference Admin Activity

```sql
-- Check if risky users are admins
SELECT r.user_principal_name, r.risk_level, r.risk_state,
       a.role_name, p.days_since_change
FROM risky_users r
LEFT JOIN admin_role_assignments a
  ON r.user_principal_name = a.member_upn
LEFT JOIN password_status p
  ON r.user_principal_name = p.user_principal_name
WHERE r.risk_level IN ('high', 'medium')
ORDER BY r.risk_level, a.role_name;
```

### Step 3: Build Timeline (For Confirmed Incidents)

If ANY of the above queries find suspicious activity:
1. Build chronological timeline of events
2. Map to MITRE ATT&CK framework
3. Identify IOCs
4. Determine data exfiltration scope
5. Recommend containment actions

---

## CASE STUDY: PIR-SGS-785634523

### What Phase 0 Found
- ✅ rbrady@goodsams.org.au flagged as HIGH RISK (2025-12-10)
- ✅ Password hygiene crisis (76.1%)
- ✅ Zero MFA enforcement

### What Phase 0 MISSED
- ❌ rbrady had login attempts from Luxembourg, Romania (blocked)
- ❌ rbrady had successful logins from US, France, Luxembourg
- ❌ rbrady created anonymous sharing link (data exfiltration)
- ❌ 88 total blocked login attempts from 5 countries
- ❌ 3 additional suspicious accounts (tibouri, gobrien, edelaney)

### What Happened
**Initial report**: Listed rbrady as HIGH RISK, did not investigate WHY
**User requested deep dive**: "previous IRs found suspicious behaviours"
**Deep dive found**: Active breach with data exfiltration

**Result**: If user hadn't requested deep dive, breach would have continued undetected.

---

## RED FLAGS THAT REQUIRE IMMEDIATE DEEP DIVE

If Phase 0 returns ANY of these, do NOT stop at Phase 0:

1. **HIGH RISK users flagged** → Investigate each one individually
2. **MEDIUM RISK users flagged** → At minimum, check sign-in patterns
3. **Logging tampering detected** → Check who made changes, verify legitimacy
4. **MFA bypass attempts** → Investigate affected accounts
5. **Impossible travel detected** → Build timeline, check for compromise
6. **Dormant accounts + admin roles** → Verify account necessity

**If in doubt, ALWAYS do the deep dive.**

---

## METRICS TO PREVENT LAZINESS

After Phase 0, you should have:

### Minimum Investigation Depth
- [ ] Every HIGH RISK user individually investigated (100% coverage)
- [ ] At least 50% of MEDIUM RISK users spot-checked
- [ ] Conditional access failures analyzed (all countries)
- [ ] Exfiltration indicators searched (anonymous links, etc.)
- [ ] Admin activity cross-referenced with risky users

### Time Investment
- Phase 0 execution: ~5 seconds
- Post-Phase-0 deep dive: ~15-30 minutes minimum
- If deep dive takes <10 minutes, you're probably being lazy

### Report Quality Check
Before submitting report, ask:
- Did I investigate WHY each user was flagged as risky?
- Did I search for exfiltration indicators proactively?
- Did I check blocked login attempts?
- Could a customer say "but what about X?" and I'd have to say "I didn't check"?

---

## AUTOMATION IS A TOOL, NOT A REPLACEMENT

**Good use of Phase 0**:
```
1. Run Phase 0 → Get systemic findings (1 min)
2. Use findings to prioritize deep dive
3. Investigate each HIGH RISK user manually (15-20 min)
4. Search for indicators Phase 0 doesn't check (10 min)
5. Build comprehensive report (10 min)
Total: 35-40 min for thorough IR
```

**Bad use of Phase 0** (what happened):
```
1. Run Phase 0 → Get systemic findings (1 min)
2. Write report based on Phase 0 output (5 min)
3. Submit report
Total: 6 min - INCOMPLETE INVESTIGATION
```

---

## COMMITMENT

**As an M365 IR Agent, I commit to:**

1. **Never treat Phase 0 as investigation completion** - it's the starting point
2. **Always investigate HIGH RISK users individually** - understand WHY they're flagged
3. **Proactively search for exfiltration** - don't wait to be asked
4. **Query CA failures automatically** - blocked attempts are attack indicators
5. **Cross-reference everything** - risky users × sign-ins × UAL × mailbox audit
6. **Build timelines for suspicious activity** - not just list findings
7. **Be thorough, not fast** - tokens renew, breaches don't pause

**If I deliver a report without doing deep dive post-Phase-0, I have failed my mission.**

---

## ENFORCEMENT

This protocol is MANDATORY for all M365 IR investigations.

**Violation indicators**:
- Report submitted <15 minutes after Phase 0
- HIGH RISK users listed without individual investigation
- No CA failure analysis included
- No proactive exfiltration search performed
- User has to request "deep dive" after initial report

**If any violation occurs**: This protocol has been ignored. Return to Step 2 and complete deep dive.

---

**Version**: 1.0
**Last Updated**: 2026-01-11
**Incident That Created This**: PIR-SGS-785634523 - Missed rbrady breach
**Never Forget**: Automation accelerates investigation, it doesn't replace it
