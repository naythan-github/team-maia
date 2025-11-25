# Essential Eight Compliance Templates

This directory contains templates for ACSC Essential Eight compliance reporting and documentation.

## Available Templates

### 1. Monthly Application Control Report Template
**File**: `monthly_application_control_report_template.md`
**Purpose**: Comprehensive monthly reporting structure for Essential Eight Strategy 1 (Application Control)
**Use Case**: Monthly compliance reporting to CISO, IT Director, Compliance Manager, and Board (quarterly roll-up)

**Key Sections**:
- Executive Summary (5-bullet format)
- Coverage & Compliance Metrics
- Threat Prevention Statistics
- False Positive Management
- Exception Requests & Approvals
- Ruleset Health & Maintenance
- Maturity Level Status (ML1/ML2/ML3)
- Trend Analysis (3-month rolling)
- Action Items & Recommendations
- Supporting Data Appendices

**Maturity Level Adaptations**:
- **ML1**: Focus on coverage metrics and basic threat prevention
- **ML2**: Add exception management and quarterly validation
- **ML3**: Include hash validation tracking and external assessment preparation

**Target Audience**: Security Operations, Compliance Teams, Auditors

---

## Template Usage

1. **Copy the template** to your working directory (not in Maia repo):
   ```bash
   cp claude/templates/essential_eight/monthly_application_control_report_template.md \
      ~/work_projects/[organization]/compliance/reports/
   ```

2. **Customize** based on your environment:
   - Replace all `[XXX]` placeholders with actual values
   - Adjust metrics targets based on organizational risk appetite
   - Modify distribution list based on governance structure

3. **Populate** with actual data:
   - Export metrics from application control platform (Airlock Digital, AppLocker, Intune)
   - Query SIEM for blocked execution attempts
   - Review exception request tracking system
   - Generate trend charts from historical data

4. **Deliver** according to cadence:
   - **Monthly**: Full report to CISO, IT Director, Compliance
   - **Quarterly**: Executive summary + trends to Board Risk Committee
   - **Annual**: Complete set to external auditors

---

## Related Resources

- **ACSC Guidance**: [Essential Eight Assessment Process Guide (November 2023)](https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight/essential-eight-assessment-process-guide)
- **Agent**: `claude/agents/essential_eight_specialist_agent.md` - For maturity assessment and roadmap planning
- **Airlock Agent**: `claude/agents/airlock_digital_specialist_agent.md` - For Strategy 1 implementation details

---

## Future Templates (Planned)

- Quarterly Essential Eight Maturity Assessment Report
- Annual Implementation Report (Commonwealth entities)
- External Assessment Preparation Checklist
- Strategy-specific templates for remaining 7 strategies:
  - Strategy 2: Patch Applications
  - Strategy 3: Configure Microsoft Office Macros
  - Strategy 4: User Application Hardening
  - Strategy 5: Patch Operating Systems
  - Strategy 6: Restrict Administrative Privileges
  - Strategy 7: Multi-Factor Authentication
  - Strategy 8: Regular Backups

---

**Directory Structure**:
```
claude/templates/essential_eight/
├── README.md (this file)
├── monthly_application_control_report_template.md
└── [future templates as developed]
```

**Maintenance**: Templates updated as ACSC Essential Eight Maturity Model evolves (currently aligned with November 2023 version)
