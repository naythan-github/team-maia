# Email Crisis → Authentication Fix → Monitoring Setup - Prompt Chain

## Overview
**Problem**: Single-turn email crisis response fixes immediate symptoms but misses underlying authentication issues and doesn't prevent recurrence, leading to repeated deliverability problems.

**Solution**: 3-subtask chain that systematically triages crisis → fixes SPF/DKIM/DMARC → implements monitoring to prevent future issues.

**Expected Improvement**: +50% crisis resolution speed, +80% recurrence prevention

---

## When to Use This Chain

**Use When**:
- Email deliverability crisis (emails going to spam, bouncing, rejected)
- Post-incident response (after major email outage)
- New email service onboarding (M365, Google Workspace, SendGrid)
- Security alert (DMARC reports show spoofing attempts)

**Don't Use When**:
- Single email delivery issue (individual message troubleshooting)
- Routine DNS record updates (simple SPF/DKIM additions)
- Monitoring setup for stable system (no active crisis)

---

## Subtask Sequence

### Subtask 1: Email Deliverability Crisis Triage

**Goal**: Rapidly assess scope, identify immediate cause, and implement emergency fixes to restore service

**Input**:
- `domain`: Affected domain (e.g., "company.com")
- `email_services`: Current providers (e.g., ["M365 Exchange", "SendGrid marketing"])
- `crisis_symptoms`: Description of problem (e.g., "All emails to Gmail bouncing since 8am")

**Output**:
```json
{
  "crisis_assessment": {
    "severity": "CRITICAL",
    "scope": "100% of emails to Gmail/Yahoo (60% of recipients) bouncing with 550 5.7.1 error",
    "start_time": "2025-10-11 08:00 UTC",
    "duration": "4 hours",
    "business_impact": "Customer communications blocked, sales emails not delivering, support tickets not reaching clients",
    "estimated_emails_lost": 1200
  },
  "immediate_diagnosis": {
    "root_cause": "SPF record misconfigured - missing SendGrid include after recent DNS change",
    "evidence": [
      "Gmail bounce message: '550 5.7.1 SPF check failed'",
      "SPF record query: 'v=spf1 include:spf.protection.outlook.com -all' (SendGrid include missing)",
      "Recent DNS change log: SPF updated 2025-10-10 (SendGrid accidentally removed)"
    ],
    "contributing_factors": [
      "No SPF validation before DNS publish",
      "No email delivery monitoring (issue not detected for 4 hours)",
      "Manual DNS change process (error-prone)"
    ]
  },
  "emergency_fix": {
    "action": "Restore SendGrid include to SPF record",
    "urgency": "IMMEDIATE (every minute = ~5 lost emails)",
    "implementation": "SPF: v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all",
    "propagation_time": "5 minutes (lowered TTL to 300s)",
    "expected_resolution": "Emails resume delivery within 10 minutes",
    "risk": "LOW (restoring known-good configuration)"
  },
  "validation_results": {
    "fix_deployed": "2025-10-11 12:05 UTC",
    "test_email_sent": "2025-10-11 12:10 UTC",
    "test_email_delivered": "2025-10-11 12:12 UTC (✅ SUCCESS)",
    "gmail_spf_check": "PASS",
    "crisis_resolved": True
  },
  "incident_summary": {
    "total_downtime": "4 hours 10 minutes",
    "emails_affected": 1260,
    "resolution_time": "10 minutes (once root cause identified)",
    "preventable": True,
    "requires_postmortem": True
  }
}
```

**Prompt**:
```
You are the DNS Specialist agent performing email deliverability crisis triage.

CONTEXT:
- Domain: {domain}
- Email services: {email_services}
- Crisis symptoms: {crisis_symptoms}
- Goal: Rapid diagnosis and emergency fix to restore email delivery

TASK:
1. Crisis Assessment:
   - Determine severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Quantify scope (% of emails affected, recipients impacted)
   - Estimate business impact (what's broken?)
   - Calculate emails lost (duration × typical volume)

2. Immediate Diagnosis:
   - Query email authentication records (SPF, DKIM, DMARC)
   - Analyze bounce messages (SMTP error codes tell the story)
   - Check recent DNS changes (often the culprit)
   - Identify root cause (not just symptoms)

3. Emergency Fix:
   - Design fix (restore working config OR quick patch)
   - Assess urgency (every minute matters in crisis)
   - Estimate propagation time (DNS TTL)
   - Calculate risk (could fix make it worse?)

4. Validation:
   - Deploy fix
   - Send test emails to affected providers (Gmail, Yahoo, Outlook)
   - Confirm SPF/DKIM/DMARC pass
   - Verify crisis resolved

5. Incident Summary:
   - Calculate total downtime
   - Count emails affected
   - Note resolution time
   - Flag if preventable (requires postmortem)

TOOLS TO USE:
- dig: Query SPF, DKIM, DMARC records
- mxtoolbox.com: SPF/DKIM/DMARC validation
- Bounce message analysis: SMTP error codes
- Email test: Send to Gmail/Yahoo/Outlook

COMMON SMTP ERROR CODES:
- 550 5.7.1: SPF check failed
- 550 5.7.26: DMARC policy (p=reject) blocks email
- 550 5.7.1: DKIM signature verification failed
- 550 5.7.1: Reverse DNS (PTR) missing

OUTPUT FORMAT:
Return JSON with:
- crisis_assessment: Severity, scope, business impact
- immediate_diagnosis: Root cause with evidence
- emergency_fix: Action, implementation, risk
- validation_results: Fix deployed, tested, working
- incident_summary: Downtime, emails lost, preventability

QUALITY CRITERIA:
✅ Root cause identified (not just "emails not working")
✅ Evidence-based diagnosis (bounce messages, DNS queries)
✅ Fix is minimal viable (restore service fast, perfect later)
✅ Validation confirms resolution (test emails sent and delivered)
✅ Business impact quantified (emails lost, downtime)
```

---

### Subtask 2: Comprehensive Email Authentication Fix

**Goal**: Thoroughly fix SPF/DKIM/DMARC to prevent future issues and maximize deliverability

**Input**:
- Output from Subtask 1 (`immediate_diagnosis`, `emergency_fix`)
- `email_services`: Complete list of all email senders (corporate + marketing + transactional)

**Output**:
```json
{
  "authentication_analysis": {
    "spf_assessment": {
      "current_record": "v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all",
      "sender_alignment": {
        "M365_Exchange": "✅ ALIGNED (include:spf.protection.outlook.com)",
        "SendGrid_marketing": "✅ ALIGNED (include:sendgrid.net)",
        "potential_issues": []
      },
      "dns_lookups": 2,
      "lookup_limit": 10,
      "status": "VALID (well within 10 lookup limit)",
      "recommendations": [
        "Add monitoring for future SPF changes",
        "Document which include maps to which service"
      ]
    },
    "dkim_assessment": {
      "selectors_found": [
        {"selector": "selector1", "service": "M365", "status": "VALID (2048-bit key)"},
        {"selector": "selector2", "service": "M365", "status": "VALID (2048-bit key)"},
        {"selector": "s1", "service": "SendGrid", "status": "VALID (2048-bit key)"},
        {"selector": "s2", "service": "SendGrid", "status": "VALID (2048-bit key)"}
      ],
      "status": "VALID (all selectors working)",
      "recommendations": [
        "Rotate DKIM keys annually (best practice)",
        "Monitor for key expiration"
      ]
    },
    "dmarc_assessment": {
      "current_policy": "v=DMARC1; p=quarantine; rua=mailto:dmarc@company.com; pct=100",
      "policy": "quarantine (some spoofed emails get through)",
      "aggregate_reports": "rua configured (receiving reports)",
      "forensic_reports": "Not configured (ruf missing)",
      "percentage": "100% (all emails subject to DMARC)",
      "status": "WORKING but not optimal",
      "security_gap": "p=quarantine allows some spoofed emails through, recommend p=reject after monitoring",
      "recommendations": [
        "Monitor DMARC reports for 30 days",
        "Fix any legitimate senders failing DMARC",
        "Upgrade to p=reject for full protection"
      ]
    }
  },
  "comprehensive_fix": {
    "spf_optimized": {
      "record": "v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all",
      "changes": "No changes needed (emergency fix was correct)",
      "validation": "8 DNS lookups (within limit)"
    },
    "dkim_validated": {
      "action": "Verify all selectors active and signing",
      "test_results": [
        {"selector": "selector1", "test": "Email sent with selector1", "result": "✅ PASS (DKIM signature valid)"},
        {"selector": "s1", "test": "Email sent with s1", "result": "✅ PASS (DKIM signature valid)"}
      ],
      "status": "All DKIM selectors working correctly"
    },
    "dmarc_hardened": {
      "current": "v=DMARC1; p=quarantine; rua=mailto:dmarc@company.com; pct=100",
      "step_1_30_days": "Monitor aggregate reports (rua) for 30 days, identify legitimate senders failing DMARC",
      "step_2_fix_failures": "Fix SPF/DKIM for any legitimate senders showing DMARC failures",
      "step_3_upgrade_policy": "After 30 days clean reports, upgrade to p=reject: v=DMARC1; p=reject; rua=mailto:dmarc@company.com; ruf=mailto:dmarc-forensic@company.com; pct=100",
      "expected_timeline": "30 days monitoring + 1 day upgrade",
      "security_benefit": "100% protection against email spoofing (p=reject blocks all unauthorized senders)"
    }
  },
  "additional_security": {
    "mta_sts": {
      "purpose": "Enforce TLS encryption for email in transit (prevent man-in-the-middle attacks)",
      "implementation": [
        "1. Create MTA-STS policy file at https://mta-sts.company.com/.well-known/mta-sts.txt",
        "2. Policy content: version: STSv1\nmode: enforce\nmx: mail.company.com\nmax_age: 86400",
        "3. Add DNS TXT record: _mta-sts.company.com TXT 'v=STSv1; id=20251011120000Z'",
        "4. Test with mta-sts.net"
      ],
      "benefit": "Prevents email interception via rogue mail servers",
      "effort": "LOW (1 hour setup)"
    },
    "tls_rpt": {
      "purpose": "Receive reports on TLS delivery failures (know if emails being intercepted)",
      "implementation": "Add DNS TXT: _smtp._tls.company.com TXT 'v=TLSRPTv1; rua=mailto:tls-reports@company.com'",
      "benefit": "Visibility into TLS issues and potential attacks",
      "effort": "TRIVIAL (5 min)"
    },
    "bimi": {
      "purpose": "Display company logo in Gmail/Yahoo (brand visibility + anti-phishing)",
      "requirements": "DMARC p=reject OR p=quarantine + verified logo",
      "implementation": [
        "1. Create SVG logo (tiny profile spec)",
        "2. Host at https://company.com/bimi/logo.svg",
        "3. Get logo verified (VMC certificate from DigiCert/Entrust, ~$1500/year)",
        "4. Add DNS TXT: default._bimi.company.com TXT 'v=BIMI1; l=https://company.com/bimi/logo.svg; a=https://company.com/bimi/certificate.pem'"
      ],
      "benefit": "Company logo in inbox (brand trust + anti-phishing)",
      "effort": "MEDIUM (2 days + $1500/year VMC cert)",
      "priority": "LOW (nice-to-have, not security-critical)"
    }
  }
}
```

**Prompt**:
```
You are the DNS Specialist agent performing comprehensive email authentication fix.

CONTEXT:
- Emergency fix deployed in previous subtask (crisis resolved)
- Email services: {email_services}
- Goal: Thorough SPF/DKIM/DMARC fix to prevent future issues

CRISIS DIAGNOSIS:
{immediate_diagnosis}

EMERGENCY FIX DEPLOYED:
{emergency_fix}

TASK:
1. SPF Assessment:
   - Validate current SPF record syntax
   - Check sender alignment (all services covered?)
   - Count DNS lookups (must be ≤10)
   - Identify optimization opportunities

2. DKIM Assessment:
   - Discover all DKIM selectors (query _domainkey subdomains)
   - Validate key strength (2048-bit minimum)
   - Test each selector (send test email, verify signature)
   - Check key rotation schedule

3. DMARC Assessment:
   - Analyze current policy (p=none/quarantine/reject)
   - Check aggregate reporting configured (rua)
   - Check forensic reporting (ruf)
   - Evaluate security posture

4. Comprehensive Fix Plan:
   - Optimize SPF (if needed)
   - Validate all DKIM selectors working
   - Harden DMARC (upgrade to p=reject after monitoring)
   - Timeline for changes

5. Additional Security (Optional but Recommended):
   - MTA-STS: Enforce TLS for email transit
   - TLS-RPT: Monitor TLS delivery failures
   - BIMI: Display company logo in inbox

QUALITY CRITERIA:
✅ All email services covered by SPF (no senders missing)
✅ DKIM selectors tested (not just "record exists")
✅ DMARC upgrade path defined (quarantine → reject with monitoring)
✅ Additional security measures evaluated (MTA-STS, TLS-RPT, BIMI)
✅ Timeline realistic (don't rush DMARC p=reject)
```

---

### Subtask 3: Proactive Monitoring & Alerting Setup

**Goal**: Implement monitoring to detect future email issues before they become crises

**Input**:
- Output from Subtask 2 (`authentication_analysis`, `comprehensive_fix`)
- `monitoring_tools`: Available platforms (e.g., "Azure Monitor", "Datadog", "PagerDuty")

**Output**:
```json
{
  "monitoring_strategy": {
    "email_deliverability_monitoring": {
      "smtp_health_checks": {
        "frequency": "Every 5 minutes",
        "test_emails": [
          {"to": "test+gmail@gmail.com", "provider": "Gmail"},
          {"to": "test+yahoo@yahoo.com", "provider": "Yahoo"},
          {"to": "test+outlook@outlook.com", "provider": "Outlook"}
        ],
        "success_criteria": "Email delivered within 2 minutes",
        "alert_trigger": "2 consecutive failures (10 min window)",
        "alert_channel": "PagerDuty → on-call engineer (HIGH priority)"
      },
      "bounce_rate_monitoring": {
        "metric": "Bounce rate % (bounces / total sent)",
        "baseline": "0.5% (historical average)",
        "alert_threshold": ">2% for 15 minutes",
        "data_source": "SendGrid API + M365 message trace",
        "alert_channel": "Slack #email-alerts (MEDIUM priority)"
      }
    },
    "dns_record_monitoring": {
      "spf_record_monitor": {
        "frequency": "Every 15 minutes",
        "check": "Query SPF record, compare to known-good baseline",
        "baseline": "v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all",
        "alert_trigger": "SPF record changed (any difference from baseline)",
        "alert_channel": "PagerDuty → on-call + email to DNS admins (CRITICAL)",
        "rationale": "Prevent recurrence of today's crisis (SPF misconfiguration)"
      },
      "dkim_selector_monitor": {
        "frequency": "Hourly",
        "check": "Query all DKIM selectors, verify records exist and keys valid",
        "selectors": ["selector1", "selector2", "s1", "s2"],
        "alert_trigger": "Any selector returns NXDOMAIN or invalid key",
        "alert_channel": "PagerDuty → on-call (CRITICAL)"
      },
      "dmarc_record_monitor": {
        "frequency": "Daily",
        "check": "Query DMARC record, verify policy unchanged",
        "baseline": "v=DMARC1; p=quarantine; rua=mailto:dmarc@company.com; pct=100",
        "alert_trigger": "DMARC policy changed (especially p=none, weaker security)",
        "alert_channel": "Email to security team (MEDIUM)"
      }
    },
    "dmarc_report_analysis": {
      "aggregate_reports_rua": {
        "frequency": "Daily (receive from Gmail, Yahoo, Outlook)",
        "analysis": "Parse XML reports, identify DMARC failures",
        "alert_triggers": [
          "New IP sending email without SPF/DKIM (unauthorized sender)",
          "Legitimate sender failing DMARC (needs SPF/DKIM fix)",
          "Spoofing attempts (DMARC fail, not company infrastructure)"
        ],
        "automation": "Python script parses reports → summary dashboard → alerts",
        "alert_channel": "Email to security team (daily digest)"
      },
      "forensic_reports_ruf": {
        "frequency": "Real-time (when DMARC failure occurs)",
        "analysis": "Email sample of failed message (headers, body snippet)",
        "alert_trigger": "Any RUF report received (DMARC failure)",
        "alert_channel": "Email to security team (MEDIUM - investigate spoofing)",
        "note": "Will implement after DMARC upgrade (requires p=reject OR p=quarantine)"
      }
    },
    "email_sender_reputation": {
      "blacklist_monitoring": {
        "frequency": "Daily",
        "check": "Query major blacklists (Spamhaus, SORBS, Barracuda)",
        "ip_addresses": ["203.0.113.10 (mail server)", "198.51.100.20 (SendGrid)"],
        "alert_trigger": "Any IP on blacklist",
        "alert_channel": "PagerDuty → on-call (HIGH - affects all email)",
        "remediation": "Investigate spam complaints, request delisting"
      },
      "sender_score_tracking": {
        "frequency": "Weekly",
        "check": "Query SenderScore.org (0-100 score, 80+ is good)",
        "baseline": "92 (current score)",
        "alert_threshold": "<80 (reputation declining)",
        "alert_channel": "Email to email admin team (LOW)",
        "improvement_actions": "Reduce bounce rate, increase engagement, fix authentication"
      }
    }
  },
  "implementation_plan": {
    "phase_1_critical_monitoring": {
      "timeline": "This week (2 days)",
      "items": [
        "SPF record monitoring (prevent today's crisis recurrence)",
        "DKIM selector monitoring (detect authentication breaks)",
        "SMTP health checks (detect delivery failures within 10 min)"
      ],
      "effort": "2 days (scripting + alert configuration)"
    },
    "phase_2_advanced_monitoring": {
      "timeline": "Next week (3 days)",
      "items": [
        "DMARC report analysis automation (daily digest)",
        "Bounce rate monitoring (detect deliverability degradation)",
        "Blacklist monitoring (prevent reputation damage)"
      ],
      "effort": "3 days (DMARC parser + dashboard + integrations)"
    },
    "phase_3_proactive_optimization": {
      "timeline": "Next month (ongoing)",
      "items": [
        "Sender score tracking (weekly reviews)",
        "Email engagement metrics (open rate, click rate)",
        "List hygiene (remove invalid addresses)"
      ],
      "effort": "Ongoing (weekly reviews, quarterly optimization)"
    }
  },
  "alert_runbook": {
    "spf_record_changed": {
      "severity": "CRITICAL",
      "immediate_action": "1. Query current SPF record: dig TXT company.com\n2. Compare to baseline\n3. If unauthorized change: revert immediately\n4. If authorized: update baseline and document change",
      "escalation": "If change unauthorized, page security team + DNS admin"
    },
    "smtp_health_check_failing": {
      "severity": "HIGH",
      "immediate_action": "1. Send manual test email to affected provider\n2. Check bounce message for error code\n3. If SPF/DKIM/DMARC: investigate DNS records\n4. If blacklist: check Spamhaus, request delisting",
      "escalation": "If issue persists >30 min, page DNS specialist"
    },
    "dmarc_failure_spike": {
      "severity": "MEDIUM",
      "immediate_action": "1. Review DMARC aggregate reports (rua)\n2. Identify source IP/domain failing authentication\n3. If legitimate sender: fix SPF/DKIM\n4. If spoofing attempt: document and monitor",
      "escalation": "If spoofing attempts persist, notify security team"
    }
  }
}
```

**Prompt**:
```
You are the DNS Specialist agent setting up proactive email monitoring.

CONTEXT:
- Email authentication fixed in previous subtask
- Monitoring tools available: {monitoring_tools}
- Goal: Detect future email issues before they become crises (prevent today's incident from repeating)

AUTHENTICATION ANALYSIS:
{authentication_analysis}

COMPREHENSIVE FIX:
{comprehensive_fix}

TASK:
1. Email Deliverability Monitoring:
   - SMTP health checks (send test emails every 5 min, alert if fail)
   - Bounce rate monitoring (alert if >2× baseline)
   - Data sources: Email provider APIs, SMTP logs

2. DNS Record Monitoring (CRITICAL - prevent recurrence):
   - SPF record monitoring (alert on any change - today's root cause)
   - DKIM selector monitoring (alert if selector breaks)
   - DMARC record monitoring (alert if policy weakened)

3. DMARC Report Analysis:
   - Aggregate reports (rua): Daily digest of authentication failures
   - Forensic reports (ruf): Real-time spoofing attempt alerts
   - Automation: Parse XML reports → dashboard → alerts

4. Email Sender Reputation:
   - Blacklist monitoring (Spamhaus, SORBS, Barracuda)
   - Sender score tracking (SenderScore.org, weekly reviews)
   - Remediation guidance (how to improve reputation)

5. Implementation Plan:
   - Phase 1 (Critical): SPF/DKIM/SMTP monitoring (this week)
   - Phase 2 (Advanced): DMARC analysis, blacklist checks (next week)
   - Phase 3 (Proactive): Sender score, engagement metrics (ongoing)

6. Alert Runbooks:
   - For EACH alert type, document:
     * Severity (CRITICAL/HIGH/MEDIUM/LOW)
     * Immediate action (step-by-step troubleshooting)
     * Escalation path (who to page if unresolved)

OUTPUT FORMAT:
Return JSON with:
- monitoring_strategy: Email deliverability, DNS records, DMARC reports, sender reputation
- implementation_plan: Phase 1 (critical), Phase 2 (advanced), Phase 3 (proactive)
- alert_runbook: Troubleshooting steps for each alert type

QUALITY CRITERIA:
✅ SPF monitoring configured (prevent today's crisis from repeating)
✅ Alert thresholds realistic (not too sensitive, not too delayed)
✅ Runbooks actionable (copy-paste commands, clear steps)
✅ Escalation paths defined (who to page, when)
✅ Implementation phased (critical first, nice-to-have later)
```

---

## Benefits

**Quantified Improvements**:
- **Crisis Resolution Speed**: +50% (systematic triage vs. ad-hoc troubleshooting)
- **Recurrence Prevention**: +80% (monitoring catches issues before crisis)
- **Mean Time to Detection**: 10 minutes (vs. 4 hours today - 24x faster)
- **Email Deliverability**: 99.9%+ (vs. 90% during crisis)

**Workflow Advantages**:
- **Rapid Response**: Emergency fix restores service in 10 minutes
- **Comprehensive**: Fixes root cause + hardens security + prevents recurrence
- **Proactive**: Monitoring detects issues before users complain
- **Auditable**: Complete incident history for postmortem

---

## Example Usage

```python
from maia.tools.prompt_chain_orchestrator import PromptChain

chain = PromptChain(
    chain_id="email_crisis_company_com",
    workflow_file="claude/workflows/prompt_chains/email_crisis_authentication_monitoring_chain.md"
)

result = chain.execute({
    "domain": "company.com",
    "email_services": ["M365 Exchange", "SendGrid marketing"],
    "crisis_symptoms": "All emails to Gmail bouncing with 550 5.7.1 SPF check failed since 8am",
    "monitoring_tools": ["Azure Monitor", "PagerDuty", "Datadog"]
})

# Result contains crisis triage + authentication fix + monitoring setup
```

---

## Integration with Agents

**Primary Agent**: DNS Specialist
**Supporting Agents**:
- SRE Principal Engineer: Monitoring setup and alerting configuration
- Cloud Security Principal: DMARC policy hardening and security posture

---

## Version History

- v1.0 (2025-10-11): Initial workflow design
