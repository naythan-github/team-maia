# ServiceDesk Level 2 Technical Assessment
## Candidate Preparation Guide

**Congratulations on progressing to the technical assessment phase!**

This guide will help you prepare for the ServiceDesk Level 2 Technical Assessment test.

---

## Test Overview

### What to Expect
- **Format**: 50 multiple-choice questions (A, B, C, D format)
- **Duration**: 120 minutes (2 hours)
- **Question Style**: Real-world troubleshooting scenarios based on actual ServiceDesk incidents
- **Passing Score**: 70% (35/50 correct answers) AND minimum 50% in each category
- **Open Book**: You may use internet, documentation, personal notes during the test

### What's NOT Allowed
- ❌ AI assistants (ChatGPT, Claude, Copilot, etc.)
- ❌ Communication with others (messaging, calls, etc.)
- ❌ Sharing test content with others

---

## Test Categories & Topics

The test covers 5 technical domains (10 questions each):

### 1. Telephony & 3CX Administration (20%)
**Topics Covered**:
- 3CX queue configuration and troubleshooting
- SIP trunk connectivity issues
- VoIP phone provisioning
- Call routing and forwarding
- SSL certificate management for VoIP
- System logs and diagnostics

**Key Technologies**:
- 3CX Phone System
- SIP (Session Initiation Protocol)
- VoIP networking (RTP, codec)
- Spectralink/DECT wireless phones

**Study Resources**:
- 3CX Official Documentation: https://www.3cx.com/docs/
- 3CX Academy (free training): https://www.3cx.com/support/3cx-academy/
- SIP Protocol basics
- VoIP troubleshooting guides

---

### 2. Account & Access Management (20%)
**Topics Covered**:
- Active Directory user account creation and management
- Azure AD (Entra ID) synchronization
- Microsoft 365 license assignment
- Security group management
- Shared mailbox configuration
- RBAC (Role-Based Access Control)
- Service principal and managed identity roles

**Key Technologies**:
- Active Directory (on-premise)
- Azure AD / Microsoft Entra ID
- Microsoft 365 Admin Center
- Group Policy
- Conditional Access policies

**Study Resources**:
- Microsoft Learn - Identity and Access: https://learn.microsoft.com/en-us/training/paths/manage-identity-and-access/
- Azure AD documentation
- M365 admin fundamentals

---

### 3. Microsoft 365 & Cloud Services (20%)
**Topics Covered**:
- Exchange Online / Outlook troubleshooting
- SharePoint document library issues
- Microsoft Teams configuration
- Azure Virtual Desktop (AVD) connectivity
- Azure Portal access and RBAC
- Email deliverability (SPF, DKIM, DMARC)
- Database replication
- Patch management

**Key Technologies**:
- Microsoft 365 (Exchange, SharePoint, Teams, OneDrive)
- Azure services (AVD, SQL Database, Portal)
- Email authentication protocols
- Windows Update / Patch management

**Study Resources**:
- Microsoft 365 Admin Center documentation
- Azure documentation: https://learn.microsoft.com/en-us/azure/
- Exchange Online troubleshooting guides
- Azure Virtual Desktop documentation

---

### 4. Security & Threat Management (20%)
**Topics Covered**:
- Microsoft Defender vulnerability alerts
- Phishing email analysis
- Security patch prioritization and deployment
- Backup failure investigation
- VPN certificate management
- Azure Monitor alerts
- Disk capacity management
- SQL Server replication monitoring

**Key Technologies**:
- Microsoft Defender for Endpoint
- Email security (anti-phishing, anti-spam)
- SSL/TLS certificates
- Backup systems
- Security Information and Event Management (SIEM)

**Study Resources**:
- Microsoft Security documentation
- CVE (Common Vulnerabilities and Exposures) database
- Email authentication (SPF/DKIM/DMARC) guides
- SSL certificate lifecycle management

---

### 5. Infrastructure & Networking (20%)
**Topics Covered**:
- Azure Virtual Network (VNet) configuration
- VPN troubleshooting (site-to-site, point-to-site)
- Network switch port troubleshooting
- Azure RBAC for storage accounts
- Power BI data gateways
- VM decommissioning processes
- SendGrid email integration
- Healthcare compliance (PHI/HIPAA) for cloud

**Key Technologies**:
- Azure VNets and VPN Gateways
- Network switches (VLAN, port security)
- Azure Storage RBAC
- VNet Peering vs VPN Gateways
- Checkpoint VPN
- Power BI connectivity

**Study Resources**:
- Azure Networking documentation
- Network troubleshooting fundamentals
- Azure RBAC documentation
- HIPAA/healthcare compliance basics

---

## How to Prepare

### 1. Assess Your Current Knowledge
Review the topics above and honestly rate your familiarity:
- ✅ **Strong**: Hands-on production experience, could troubleshoot independently
- ⚠️ **Moderate**: Some experience, would need documentation/guidance
- ❌ **Weak**: Limited or no experience, need to learn

Focus your study time on **Weak** and **Moderate** areas.

---

### 2. Hands-On Practice (Most Important!)
**Recommended Practice Activities**:
- Set up a free Microsoft 365 trial (developer tenant)
- Practice user provisioning, license assignment, group management
- Set up free Azure trial account
- Practice creating VNets, VMs, RBAC assignments
- Install 3CX in VM or use free trial
- Practice call queue configuration, trunk setup

**Why Hands-On Matters**: The test asks "What would you do FIRST?" - hands-on experience builds systematic troubleshooting habits.

---

### 3. Study Systematic Troubleshooting
The test emphasizes **troubleshooting methodology**, not just technical facts.

**Effective Troubleshooting Pattern**:
1. **Gather Information**: What are the symptoms? Who's affected? When did it start?
2. **Check Obvious/Common Issues First**: Connectivity, authentication, permissions
3. **Review Logs**: System logs, event logs, application logs
4. **Isolate the Problem**: Is it one user, one site, or system-wide?
5. **Test Hypothesis**: Make a change, test, observe result
6. **Document and Communicate**: What did you find? What did you fix?

**Questions test this pattern**:
- "What should you check FIRST?" → Tests systematic approach
- "What is the MOST LIKELY cause?" → Tests diagnosis prioritization
- "What is your troubleshooting approach?" → Tests methodology

**Bad Troubleshooting Patterns** (avoid these):
- ❌ "Restart everything immediately" (no diagnosis)
- ❌ "Ignore the alert" (not taking action)
- ❌ "Call vendor support immediately" (skipping basic troubleshooting)
- ❌ "Delete and rebuild" (nuclear option without diagnosis)

---

### 4. Review Documentation Resources

**Microsoft Documentation** (essential):
- Microsoft Learn: https://learn.microsoft.com/
- Microsoft 365 Admin Docs
- Azure Docs
- Microsoft Security Docs

**Other Vendor Docs**:
- 3CX Documentation: https://www.3cx.com/docs/
- Your organization's internal wiki/KB (if available)

**General IT Resources**:
- Reddit r/sysadmin (real-world troubleshooting discussions)
- Spiceworks Community
- TechNet forums

---

### 5. Focus on Real-World Scenarios

**This test is based on ACTUAL incidents from Jul-Oct 2025**. Questions reflect real problems that your team encountered.

**Example Scenario Types**:
- User provisioning gone wrong (account created but no access)
- Email deliverability issues (legitimate emails marked as spam)
- VPN connectivity failures (worked yesterday, not today)
- Azure service health incidents (multiple users reporting issues)
- Security vulnerabilities (Defender alerts, patch prioritization)

**Study Tip**: Read case studies and incident reports to see how problems are diagnosed and resolved.

---

## Sample Questions

Here are 5 sample questions (similar style to actual test):

### Sample Question 1 (Telephony)
You receive an alert that calls to extension 500 are dropping. The 3CX dashboard shows "insufficient trunks" error. What is your FIRST troubleshooting step?

A) Restart the 3CX server immediately
B) Check current trunk utilization and compare to licensed capacity
C) Disable the extension to stop alerts
D) Contact telephony provider to purchase more trunks

<details>
<summary>Click to see answer</summary>
<strong>Answer: B</strong> - Always diagnose before acting. Check if all trunks are actually in use, if there's a misconfiguration, or if licensing expired. Options A, C, D take action without diagnosis.
</details>

---

### Sample Question 2 (Account Management)
You need to create a new user account for an employee starting tomorrow. What is the correct provisioning sequence?

A) Create AD account → Sync to Azure AD → Assign licenses → Configure access → Email credentials
B) Assign licenses first → Create AD account → Configure mailbox → Email credentials
C) Email credentials to manager → Create AD account → Assign licenses → Configure access
D) Configure access → Create AD account → Assign licenses → Email credentials

<details>
<summary>Click to see answer</summary>
<strong>Answer: A</strong> - Identity (AD account) must exist first, then sync to cloud, then licenses (enable services), then configure, finally send credentials. Options B, C, D have incorrect dependency order.
</details>

---

### Sample Question 3 (M365 & Cloud)
Multiple users report they cannot access the Azure Portal. What is your troubleshooting priority order?

A) Check Azure Service Health → Check Conditional Access policies → Check user RBAC permissions → Test from different network
B) Reset all user passwords immediately
C) Restart Azure subscription
D) Have all users clear browser cache

<details>
<summary>Click to see answer</summary>
<strong>Answer: A</strong> - Multi-user issue requires checking service-wide factors first: service health (outage?), Conditional Access (blocking policy?), permissions (RBAC removed?), network (firewall?). Options B, C, D don't follow systematic approach.
</details>

---

### Sample Question 4 (Security)
You receive a Microsoft Defender alert for CVE-2025-12345 (CVSS 9.8 Critical) affecting 15 endpoints. What is your response workflow?

A) Review CVE details → Identify affected systems → Check patch availability → Prioritize remediation → Deploy patch → Verify
B) Ignore the alert (too many false positives)
C) Immediately shut down all 15 endpoints
D) Deploy patch to all systems overnight without testing

<details>
<summary>Click to see answer</summary>
<strong>Answer: A</strong> - Proper vulnerability management balances urgency with stability: understand threat, scope impact, check solution, prioritize (critical systems first), deploy, verify. Option B is negligent, C causes outage, D risks breaking systems.
</details>

---

### Sample Question 5 (Infrastructure)
A workstation has no ethernet connection. User tried different cable and wall port - still no connection. WiFi works. What is your next troubleshooting step?

A) Check switch port status → Check VLAN configuration → Test cable run → Check port security → Check switch logs
B) Reinstall network drivers on workstation
C) Replace the workstation NIC
D) Tell user to use WiFi permanently

<details>
<summary>Click to see answer</summary>
<strong>Answer: A</strong> - Physical layer is working (tried cable/port), so issue is likely switch-side: port disabled?, wrong VLAN?, cable run damaged?, MAC filtering?, switch errors? Option B unlikely (WiFi works = drivers OK), C is premature, D doesn't diagnose problem.
</details>

---

## Test Day Tips

### Before the Test
✅ **Get a good night's sleep** - 2-hour tests require sustained focus
✅ **Have documentation bookmarked** - Microsoft Docs, 3CX docs, etc.
✅ **Set up quiet environment** (if remote) - no distractions
✅ **Test your internet connection** - ensure stability
✅ **Have scratch paper and pen** - for notes and calculations
✅ **Eat a good meal** - you'll be testing for 2 hours

### During the Test
✅ **Read questions carefully** - look for "FIRST," "MOST LIKELY," "BEST"
✅ **Use all 120 minutes** - don't rush, review answers if time permits
✅ **Answer all questions** - no penalty for wrong answers, so guess if unsure
✅ **Use internet/documentation** - but don't spend 10 minutes per question researching
✅ **Trust your experience** - if you've seen the issue before, go with your instinct
✅ **Flag difficult questions** - skip and come back if stuck

### Time Management
- **120 minutes / 50 questions = ~2.4 minutes per question**
- Aim to finish in 90-100 minutes, leaving 20-30 for review
- Don't spend >5 minutes on any single question
- Budget time per category:
  - Category 1 (Q1-10): 25 minutes
  - Category 2 (Q11-20): 25 minutes
  - Category 3 (Q21-30): 25 minutes
  - Category 4 (Q31-40): 25 minutes
  - Category 5 (Q41-50): 25 minutes
  - Review: 20 minutes

### Answering Multiple-Choice Strategy
1. **Read question carefully** - identify what's being asked
2. **Eliminate obviously wrong answers** - usually 1-2 answers are clearly incorrect
3. **Compare remaining options** - which is MOST systematic? FIRST step? MOST LIKELY?
4. **Select BEST answer** - not just "an" answer, but the BEST one
5. **Move on** - don't overthink, trust your knowledge

---

## What NOT to Worry About

❌ **Memorizing syntax** - you can look up PowerShell commands, Azure CLI syntax
❌ **Obscure scenarios** - test focuses on common L2 issues, not exotic edge cases
❌ **Perfect scores** - 70% is passing, 80%+ is strong, 90%+ is excellent (not required)
❌ **One wrong category** - as long as you're ≥50% in each category and ≥70% overall, you pass

---

## After the Test

### Results Timeline
- **Scoring**: Within 2 business days
- **Pass notification**: Email with interview invitation
- **Fail notification**: Polite email with general feedback

### Next Steps if You Pass
- **Technical Interview**: 60-90 minutes with technical scenarios and behavioral questions
- **Reference Checks**: We'll contact your provided references
- **Offer**: Typically within 1 week of successful interview

### If You Don't Pass This Time
- Your resume stays on file for 12 months
- You may request general feedback on weak areas
- We encourage you to study those areas and apply again in 6-12 months

---

## Frequently Asked Questions

**Q: Can I use ChatGPT or AI assistants during the test?**
A: No. This violates test policy and will result in disqualification.

**Q: Can I use Microsoft documentation websites?**
A: Yes! This is an open-book test. Microsoft Docs, vendor documentation, and your personal notes are allowed.

**Q: What if I don't know the answer to a question?**
A: Make your best guess - there's no penalty for wrong answers. Use elimination strategy.

**Q: How much weight does this test have in hiring decision?**
A: The test is a qualifying filter (must pass to proceed to interview), but interview performance and cultural fit are equally important.

**Q: Can I retake the test if I fail?**
A: Not immediately for the same role. You may reapply in 6-12 months and take the test again (questions may be updated).

**Q: Will I get to see which questions I got wrong?**
A: No, to preserve test integrity. But we'll provide category-level feedback (e.g., "strong in M365, weak in networking").

**Q: Is this test vendor-certified?**
A: No, it's custom-built for this organization based on real ServiceDesk incidents. It assesses practical troubleshooting, not certification knowledge.

---

## Mindset for Success

**Remember**:
- This test assesses **problem-solving methodology** more than memorized facts
- **Systematic troubleshooting** (check logs, isolate problem, test hypothesis) beats reactive approaches ("restart everything")
- **Security awareness** is critical - never ignore security alerts or choose insecure shortcuts
- **Communication and documentation** are part of good technical work (options that skip these are usually wrong)
- **Your real-world experience matters** - if you've worked L2 ServiceDesk, trust your instincts

**You've got this!**

Good luck on the assessment. We look forward to reviewing your results!

---

**Questions?**
Contact: [HR/Recruitment Contact Email]

---

**Guide Version**: 1.0
**Prepared By**: Technical Recruitment Team
**Last Updated**: 2025-11-05
