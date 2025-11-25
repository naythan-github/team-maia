# Monthly Application Control Report Template
**Essential Eight Strategy 1 - Application Control**

---

**Report Period**: [Month Year]
**Maturity Level**: [ML1/ML2/ML3]
**Prepared by**: [Security Operations / Infrastructure Team]
**Distribution**: [CISO, IT Director, Compliance, Board (quarterly roll-up)]

---

## 1. Executive Summary

**Format**:
```
✅ Coverage: [XXX/XXX] endpoints protected ([XX]%)
⚠️ False Positives: [X] incidents, [X] resolved within SLA
🛡️ Threats Blocked: [XXX] unauthorized execution attempts
📊 Trend: [↑/↓/→] vs prior month
🔧 Action Required: [None / X critical items]
```

**Example (ML2 Environment)**:
```
✅ Coverage: 847/850 endpoints protected (99.6%)
⚠️ False Positives: 3 incidents, all resolved within 4 hours (SLA: 24h)
🛡️ Threats Blocked: 127 unauthorized execution attempts across 18 endpoints
📊 Trend: ↓ 23% blocks vs prior month
🔧 Action Required: 3 endpoints offline >30 days need investigation
```

---

## 2. Coverage & Compliance Metrics

| Metric | Target | Current | Prior Month | Status |
|--------|--------|---------|-------------|--------|
| **Endpoints Protected** | 100% | [X]% ([XXX/XXX]) | [X]% | [🟢/🟡/🔴] |
| **Ruleset Currency** | <30 days | [X] days since update | [X] days | [🟢/🟡/🔴] |
| **False Positive Rate** | <1% | [X]% ([X/XXX]) | [X]% | [🟢/🟡/🔴] |
| **Exception SLA Compliance** | >95% | [X]% ([X/X] within 24h) | [X]% | [🟢/🟡/🔴] |
| **Centralized Logging** | 100% | [X]% (SIEM active) | [X]% | [🟢/🟡/🔴] |

**Gap Analysis**:
- [List any gaps or exceptions]
- **Action**: [Remediation plan with owner and due date]

---

## 3. Threat Prevention Statistics

**Blocked Execution Attempts**:
```
Total Blocks: [XXX] ([↑/↓] [XX]% vs prior month)

By Location:
  📁 %TEMP%: [XX] blocks ([XX]%) - browser-spawned executables
  📁 Downloads: [XX] blocks ([XX]%) - direct user downloads
  📁 AppData\Local: [XX] blocks ([XX]%) - malware staging attempts
  📁 Other: [XX] blocks ([XX]%) - USB/network shares

By Endpoint:
  Top 5 endpoints: [XX] blocks ([XX]%) - investigate user behavior
  Remaining [XXX] endpoints: [XX] blocks ([XX]%) - normal distribution

Risk Level Assessment:
  🔴 Critical: [X] (APT-grade tradecraft)
  🟠 High: [X] (unsigned executables from external sources)
  🟡 Medium: [X] (browser-spawned scripts, PUA)
  🟢 Low: [X] (legacy installers, known-safe unsigned apps)
```

**Notable Incidents**:
1. **[Date]**: [Description]
   - Source: [Origin of threat]
   - Resolution: [How it was handled]
   - Severity: [Critical/High/Medium/Low]

2. **[Date]**: [Description]
   - Source: [Origin]
   - Resolution: [Action taken]
   - Severity: [Level]

---

## 4. False Positive Management

**Incidents This Month**: [X] total

| Date | Application | User/Dept | Root Cause | Resolution Time | Status |
|------|-------------|-----------|------------|-----------------|--------|
| [Date] | [app.exe] | [Dept] | [Reason] | [Xh] | [✅/⏳] |
| [Date] | [app.exe] | [Dept] | [Reason] | [Xh] | [✅/⏳] |

**SLA Performance**: [X]% resolved within 24h SLA (average: [X] hours)

**Process Improvement**:
- [Lesson learned 1]
- [Lesson learned 2]

---

## 5. Exception Requests & Approvals

**New Exceptions This Month**: [X] requests

| Request ID | Application | Justification | Risk Level | Approval | Status |
|------------|-------------|---------------|------------|----------|--------|
| EXC-YYYY-XXX | [app] | [reason] | [Low/Med/High] | [Approved/Denied] | [Active/Closed] |
| EXC-YYYY-XXX | [app] | [reason] | [Low/Med/High] | [Approved/Denied] | [Active/Closed] |

**Approval Statistics**:
- Approved: [X/X] ([XX]%)
- Denied: [X/X] ([XX]%)
- Average approval time: [X] hours (target: <24h)

**Policy Adherence**: [XX]% followed documented approval workflow

---

## 6. Ruleset Health & Maintenance

**Current Ruleset Composition**:
```
Publisher Rules: [XXX] ([XX]%) - Zero maintenance ✅
Path Rules: [XXX] ([XX]%) - Low maintenance 🟡
Hash Rules: [XXX] ([XX]%) - Annual validation required ⚠️

Total Applications Managed: [X,XXX]
Last Ruleset Update: [Date] ([X] days ago)
Deprecated Rules: [X]
```

**Maintenance Actions**:
- [Date]: [Action taken]
  - [Details]
  - Result: [Outcome]

**Upcoming Validation** (ML3 Requirement):
- [Quarter Year]: [Validation activity]
- Target completion: [Date]
- Owner: [Team/Person]

---

## 7. Maturity Level Status

**Current Maturity**: [ML1/ML2/ML3]

**ML[X] Requirements Status**:
| Requirement | Status | Evidence |
|-------------|--------|----------|
| Application control implemented | [✅/⏳/❌] | [Evidence description] |
| Centralized logging enabled | [✅/⏳/❌] | [Evidence description] |
| Exceptions documented | [✅/⏳/❌] | [Evidence description] |
| Quarterly validation testing | [✅/⏳/❌] | [Evidence description] |
| Publisher/path/hash rules | [✅/⏳/❌] | [Evidence description] |

**Path to ML[X+1]** (If applicable):
- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]
- **Timeline**: [Target completion date]

---

## 8. Trend Analysis (Last 3 Months)

**Blocked Execution Attempts**:
```
[Month-2]: [XXX] blocks
[Month-1]: [XXX] blocks ([↑/↓][XX]%)
[Month]: [XXX] blocks ([↑/↓][XX]%)

Trend: [↑/↓/→] [Description of trend]
```

**False Positive Rate**:
```
[Month-2]: [X.XX]% ([X] incidents)
[Month-1]: [X.XX]% ([X] incidents)
[Month]: [X.XX]% ([X] incidents)

Trend: [↑/↓/→] [Description]
```

**Coverage**:
```
[Month-2]: [XX.X]% ([XXX/XXX])
[Month-1]: [XX.X]% ([XXX/XXX])
[Month]: [XX.X]% ([XXX/XXX])

Trend: [↑/↓/→] [Description]
```

---

## 9. Action Items & Recommendations

**Immediate Actions** (This Month):
1. **Priority: [High/Medium/Low]** - [Action description]
   - Owner: [Team/Person]
   - Action: [Specific steps]
   - Due: [Date]

2. **Priority: [High/Medium/Low]** - [Action description]
   - Owner: [Team/Person]
   - Action: [Specific steps]
   - Due: [Date]

**Upcoming Actions** (Next Quarter):
1. **[Quarter Year]** - [Action description]
   - Owner: [Team/Person]
   - Effort: [Estimated hours]
   - Due: [Date]

**Strategic Recommendations**:
1. **[Recommendation Title]**: [Description]
   - Benefit: [Expected outcome]
   - Effort: [Investment required]

2. **[Recommendation Title]**: [Description]
   - Benefit: [Expected outcome]
   - Investment: [Cost/hours]

---

## 10. Appendix: Supporting Data

**A. High-Risk Block Details**
- [Detailed log entries for high-severity blocks]

**B. Exception Request Detail**
- [Full text of exception requests with risk assessments]

**C. Configuration Changes**
- [Git commit log or change log of ruleset modifications]

**D. SIEM Query Results**
- [Raw data: all blocked execution attempts for audit trail]

---

## Report Delivery & Distribution

**Format**: PDF + Excel dashboard (for metric trending)

**Distribution List**:
- **Weekly**: Security Operations (operational metrics only)
- **Monthly**: CISO, IT Director, Compliance Manager
- **Quarterly**: Board Risk Committee (executive summary + trend analysis)
- **Annual**: External auditors (full reports + appendices)

**Retention**: 7 years (Commonwealth: 10 years for audit compliance)

---

## Usage Notes

**Purpose**: This template provides a comprehensive monthly reporting structure for Essential Eight Strategy 1 (Application Control) compliance reporting.

**Maturity Level Adaptations**:
- **ML1**: Focus on coverage metrics and basic threat prevention
- **ML2**: Add exception management and quarterly validation
- **ML3**: Include hash validation tracking and external assessment preparation

**Customization**:
- Adjust metrics targets based on organizational risk appetite
- Modify distribution list based on governance structure
- Add/remove sections based on stakeholder requirements

**Key Principle**: Monthly reports should be **operational** (drive actions) not just **informational** (report status). Every metric should answer: "What decision does this enable?"

---

**Template Version**: 1.0
**Created**: 2025-11-25
**Source**: Essential Eight Specialist Agent v2.3
**Related**: ACSC Essential Eight Assessment Process Guide (November 2023)
