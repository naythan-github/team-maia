# L1 Service Desk - Sub-Level Progression Structure

**Purpose**: Define clear skill progression within Level 1 Service Desk from entry-level TAFE graduates to L2-ready technicians, with specific tasks, training milestones, and promotion criteria

**Last Updated**: 2025-10-08
**Version**: 1.0
**Context**: Orro Service Desk skill development pathway

---

## Executive Summary

### L1 Sub-Level Overview

| Level | Title | Experience | Supervision | FCR Target | Escalation Rate | Time in Role |
|-------|-------|------------|-------------|------------|-----------------|--------------|
| **L1A** | Service Desk Analyst (Graduate/Trainee) | 0-6 months | High supervision | 40-50% | 50-60% | 3-6 months |
| **L1B** | Service Desk Analyst (Junior) | 6-18 months | Moderate supervision | 55-65% | 35-45% | 6-12 months |
| **L1C** | Service Desk Analyst (Intermediate) | 18-36 months | Low supervision | 65-75% | 25-35% | 6-18 months |

**Progression Philosophy**: Gradual responsibility increase with clear milestones, ensuring confidence and competence before promotion

---

## L1A - Service Desk Analyst (Graduate/Trainee)

### Profile
- **Experience**: 0-6 months in IT support role
- **Education**: TAFE Cert III/IV IT, or Bachelor's Degree (recent graduate)
- **Typical Background**: First IT job, limited real-world troubleshooting experience
- **Supervision Level**: High - works under close supervision, paired with L1B/L1C mentor
- **Time in Role**: 3-6 months (minimum 3 months before L1B consideration)

### Primary Purpose
Build foundational service desk skills in a controlled environment, learning standard procedures, ticket management, and basic troubleshooting under supervision.

---

### Core Responsibilities (L1A)

#### 1. Password & Account Management (80% Resolution)

**Permitted Tasks** (Following exact procedures):
- ✅ **Reset user passwords** (Azure AD only, following documented steps)
- ✅ **Unlock user accounts** (standard lockouts, not security-related)
- ✅ **Basic MFA resets** (SMS/Authenticator app, following runbook)
- ✅ **Check account status** (disabled, expired, check properties)

**NOT Permitted** (Escalate to L1B/L1C/L2):
- ❌ Conditional Access troubleshooting (Azure AD complexity)
- ❌ Privileged account issues (admin accounts, service accounts)
- ❌ Account provisioning/deprovisioning (L1B minimum)
- ❌ License assignments (L1B minimum)

**Escalation Criteria**:
- Cannot follow standard procedure (missing steps, unclear documentation)
- User claims password already reset but still not working
- Account shows unusual properties (blocked sign-in, risky user flagged)
- Time spent >15 minutes without resolution

---

#### 2. Basic Microsoft 365 Support (60% Resolution)

**Permitted Tasks**:
- ✅ **Outlook profile issues** (re-add account, cache mode verification)
- ✅ **Email not syncing** (check connectivity, restart Outlook, verify account)
- ✅ **Calendar permissions** (view-only sharing, following templates)
- ✅ **Out of office setup** (Outlook client, following user guide)
- ✅ **Mobile device email setup** (iOS Mail, Android Gmail - step-by-step guides)
- ✅ **OneDrive sync issues** (restart sync, re-link account)
- ✅ **Teams basics** (add to team, join meeting troubleshooting)

**NOT Permitted**:
- ❌ Mail flow issues (message trace is L1B minimum)
- ❌ Shared mailbox configuration (L1B minimum)
- ❌ Distribution list management (L1B minimum)
- ❌ SharePoint permissions (L1B minimum)
- ❌ Exchange mailbox moves or advanced settings

**Escalation Criteria**:
- Step-by-step guide doesn't resolve issue
- Error messages not covered in documentation
- User reports "it worked yesterday" but now broken
- Time spent >20 minutes without resolution

---

#### 3. Basic Endpoint Support (50% Resolution)

**Permitted Tasks**:
- ✅ **VPN connection issues** (re-download VPN profile, verify credentials)
- ✅ **Printer issues** (add network printer, check queue, driver re-install from catalog)
- ✅ **Mapped drive not connecting** (disconnect/reconnect, verify credentials)
- ✅ **Software installation** (from approved catalog only, Company Portal apps)
- ✅ **Browser issues** (clear cache, reset settings, check default browser)
- ✅ **Basic Windows Update** (check for updates, verify success)

**NOT Permitted**:
- ❌ Group Policy troubleshooting (gpresult, RSoP - L1B minimum)
- ❌ Intune policy issues (L1B minimum)
- ❌ Application packaging or custom installations
- ❌ BSOD or crash diagnostics (escalate immediately)
- ❌ Driver updates beyond printer drivers

**Escalation Criteria**:
- VPN issue persists after profile re-download
- Printer driver not in approved catalog
- Software not in Company Portal or approved catalog
- Any hardware failure suspected
- Time spent >20 minutes without resolution

---

#### 4. Ticket Management (L1A Critical Skills)

**Required Skills** (Must master in first 2 weeks):
- ✅ **Accurate categorization** (Category, Subcategory, Type per standards)
- ✅ **Priority assignment** (P1/P2/P3/P4 per SLA matrix)
- ✅ **Detailed documentation** (Problem description, steps taken, outcome)
- ✅ **Escalation notes** (Provide adequate context when escalating)
- ✅ **Customer communication** (professional language, set expectations)
- ✅ **SLA awareness** (understand response/resolution time expectations)
- ✅ **Knowledge base usage** (search before escalating, link KB articles in tickets)

**Quality Standards**:
- 95%+ categorization accuracy (measured weekly)
- 100% of tickets have notes documenting actions taken
- <5% tickets sent back from L2 due to inadequate escalation notes

---

#### 5. Communication & Soft Skills (L1A Foundation)

**Required Behaviors**:
- ✅ **Professional phone etiquette** (greeting, active listening, empathy)
- ✅ **Clear written communication** (proper grammar, no jargon)
- ✅ **Set realistic expectations** (don't promise what you can't deliver)
- ✅ **Escalation without ego** ("Let me get someone who specializes in this")
- ✅ **Follow-up discipline** (check escalated tickets daily, update customer)

**Mentoring Support**:
- Shadow L1B/L1C for first week (observe calls, ticket handling)
- Buddy system: Assigned mentor for first 3 months
- Weekly 1:1 with Team Leader (progress review, coaching)

---

### L1A Training & Certification Path

#### Week 1-2: Onboarding
- Orro systems training (ServiceDesk platform, tools, access)
- Company policies (security, acceptable use, confidentiality)
- Ticket management fundamentals
- Shadow experienced L1B/L1C (observe 20+ tickets)

#### Month 1: Foundation Skills
- Password reset procedures (10+ successful resets)
- Basic M365 support (Outlook, Teams basics)
- Ticket documentation standards (100% compliance)
- Customer communication training

#### Month 2-3: Expanding Capability
- Endpoint support basics (VPN, printers, mapped drives)
- Company Portal app installations
- Knowledge base contribution (feedback on unclear articles)
- Introduction to escalation criteria

#### Month 4-6: L1B Preparation
- Increased unsupervised work (70% independent, 30% shadowed)
- Advanced M365 topics (introduction to mail flow, SharePoint basics)
- Soft skills development (handling difficult customers, prioritization)
- Self-assessment and L1B readiness discussion

#### Required Certifications (during L1A)
- **Microsoft 365 Certified: Fundamentals (MS-900)** - MANDATORY within 3 months
- **CompTIA A+** (optional but recommended for TAFE grads without)

---

### L1A Performance Metrics

**Minimum Performance Standards** (for L1B promotion consideration):

| Metric | Target | Minimum for Promotion |
|--------|--------|----------------------|
| **First Call Resolution (FCR)** | 40-50% | ≥45% (sustained 2 months) |
| **Escalation Rate** | 50-60% | <55% (appropriate escalations) |
| **Average Handle Time (AHT)** | 15-25 minutes | <25 min (not rushing quality) |
| **Customer Satisfaction (CSAT)** | >3.8/5.0 | ≥3.8/5.0 |
| **Ticket Documentation Quality** | >90% | ≥90% (peer reviewed) |
| **Categorization Accuracy** | >90% | ≥95% |
| **Time to MS-900 Certification** | 3 months | Within 4 months |

**Promotion Criteria to L1B**:
1. Minimum 3 months in L1A role
2. MS-900 certification obtained
3. Performance metrics met for 2 consecutive months
4. Team Leader approval (readiness assessment)
5. No active performance improvement plan (PIP)

---

## L1B - Service Desk Analyst (Junior)

### Profile
- **Experience**: 6-18 months in IT support role
- **Education**: TAFE Cert III/IV IT or Bachelor's + MS-900 certification
- **Typical Background**: Promoted from L1A or hired with 6-12 months helpdesk experience
- **Supervision Level**: Moderate - works independently on standard issues, supervised on complex tasks
- **Time in Role**: 6-12 months (minimum 6 months before L1C consideration)

### Primary Purpose
Handle full range of L1 tasks independently, begin learning L2 skills through shadowing, mentor L1A team members, improve FCR through deeper troubleshooting.

---

### Core Responsibilities (L1B)

#### 1. User Account Management - Full L1 Scope (90% Resolution)

**Added Capabilities** (beyond L1A):
- ✅ **User account provisioning** (following standard templates, license assignments)
- ✅ **Account deprovisioning** (disable accounts, convert mailbox to shared, following checklist)
- ✅ **Distribution list management** (add/remove members, create DLs following naming conventions)
- ✅ **Microsoft 365 license assignments** (E3, E5, Business Premium per role)
- ✅ **Basic Conditional Access troubleshooting** (check policy assignments, verify user in correct group)
- ✅ **Shared mailbox setup** (create, assign permissions, add to Outlook)

**NOT Permitted** (Escalate to L1C/L2):
- ❌ Custom permission requirements outside templates
- ❌ Group Policy modifications
- ❌ Azure AD Connect sync issues
- ❌ Dynamic group membership rules
- ❌ Admin role assignments (privileged access)

**Escalation Criteria**:
- Template doesn't fit requirements (custom permissions needed)
- License assignment fails (requires CSP/EA troubleshooting)
- Conditional Access policy conflicts detected
- Time spent >30 minutes without resolution

---

#### 2. Microsoft 365 Support - Advanced L1 (75-85% Resolution)

**Added Capabilities**:
- ✅ **Message trace** (Exchange Online, track email delivery, identify delays)
- ✅ **Shared mailbox access** (Full Access, Send As, Send on Behalf permissions)
- ✅ **Calendar delegation** (full access, editor permissions, troubleshooting)
- ✅ **SharePoint permissions** (site member, site visitor, file/folder sharing)
- ✅ **OneDrive Known Folder Move** (Desktop, Documents, Pictures sync setup)
- ✅ **Teams member management** (add/remove members, guest access following approval)
- ✅ **Teams calling basics** (transfer, hold, voicemail, call forwarding)
- ✅ **Mobile device troubleshooting** (Company Portal, Intune enrollment verification)

**NOT Permitted** (Escalate to L2):
- ❌ Mail flow rules (transport rules)
- ❌ Retention policies or litigation hold
- ❌ SharePoint site architecture changes
- ❌ Advanced Teams configurations (policies, meeting settings)
- ❌ Exchange mailbox migrations

**Escalation Criteria**:
- Message trace shows mail flow rule blocking email
- SharePoint permission inheritance issues
- Teams policy preventing user action
- Multiple M365 services affected (systemic issue)
- Time spent >40 minutes without resolution

---

#### 3. Endpoint Support - Full L1 Scope (70-80% Resolution)

**Added Capabilities**:
- ✅ **Group Policy troubleshooting basics** (gpresult, identify conflicting policies, document for L2)
- ✅ **Intune device compliance verification** (check compliance status, explain policies)
- ✅ **Company Portal troubleshooting** (re-sync device, reinstall portal, check app assignments)
- ✅ **Application deployment verification** (check Intune assignment, user device sync status)
- ✅ **Windows Update troubleshooting** (check update history, restart update service)
- ✅ **Basic Windows troubleshooting** (safe mode, system file checker, disk cleanup)
- ✅ **Antivirus/EDR alerts** (false positive identification, basic remediation per runbook)

**NOT Permitted** (Escalate to L2):
- ❌ Group Policy creation or modification
- ❌ Intune policy creation or modification
- ❌ Registry modifications
- ❌ PowerShell scripting for remediation
- ❌ Operating system repairs (DISM, in-place upgrades)

**Escalation Criteria**:
- Group Policy conflict requiring policy modification
- Intune policy preventing required action
- Windows corruption requiring advanced repair
- Application compatibility issues
- Time spent >40 minutes without resolution

---

#### 4. Software Support - Expanded L1 (65-75% Resolution)

**Added Capabilities**:
- ✅ **Microsoft Office advanced support** (intermediate Excel formulas, PowerPoint templates)
- ✅ **Office activation troubleshooting** (unlicensed product, sign-in issues)
- ✅ **Office repair and reinstall** (online repair, full uninstall/reinstall)
- ✅ **Line-of-business app basics** (verify user access, check application status)
- ✅ **Adobe Acrobat Pro** (basic support, licensing verification)
- ✅ **Web browser management** (Edge admin templates, Chrome policies)

**NOT Permitted** (Escalate to L2):
- ❌ Advanced Excel (complex formulas, macros, Power Query)
- ❌ Access database support
- ❌ Line-of-business app configuration or troubleshooting
- ❌ Application packaging

**Escalation Criteria**:
- Application requires configuration changes
- LOB application errors (escalate to app specialists)
- Office issue persists after repair/reinstall
- Time spent >30 minutes without resolution

---

#### 5. Network Support - Basic L1 (50-60% Resolution)

**Added Capabilities**:
- ✅ **Advanced network diagnostics** (ipconfig /all, nslookup, tracert interpretation)
- ✅ **DHCP issues** (release/renew, verify DHCP assignment, static IP check)
- ✅ **DNS troubleshooting** (flush DNS, verify DNS servers, nslookup testing)
- ✅ **Wi-Fi troubleshooting** (signal strength, authentication types, profile management)
- ✅ **VPN troubleshooting** (client-side logs, credential verification, split tunneling awareness)

**NOT Permitted** (Escalate to L2):
- ❌ Network infrastructure troubleshooting (switches, routers, firewalls)
- ❌ DHCP server configuration
- ❌ DNS server configuration
- ❌ VPN server-side configuration
- ❌ Firewall rule requests

**Escalation Criteria**:
- Network connectivity issue affects multiple users
- DHCP/DNS issue requires server-side changes
- VPN server issue identified
- Network performance problems (latency, packet loss)
- Time spent >30 minutes without resolution

---

#### 6. Mentoring & Knowledge Transfer (New L1B Responsibility)

**Required Activities**:
- ✅ **Mentor L1A team members** (answer questions, review tickets, provide guidance)
- ✅ **Shadow L2 technicians** (1-2 hours per week, learn L2 skills)
- ✅ **Knowledge base contributions** (document solutions, update existing articles)
- ✅ **Peer reviews** (review L1A tickets for quality, provide feedback)

**Success Metrics**:
- Mentor satisfaction: L1A reports feeling supported
- Knowledge base: 1-2 article contributions per month
- L2 shadowing: Complete 10+ L2 tickets observations

---

### L1B Training & Certification Path

#### Month 1-3 (Early L1B)
- Expand M365 skills (message trace, SharePoint permissions, Teams management)
- Begin Intune fundamentals (device compliance, Company Portal)
- Soft skills training (handling escalations professionally, time management)
- Start MS-102 study (Microsoft 365 Administrator)

#### Month 4-6 (Mid L1B)
- Advanced troubleshooting techniques (systematic problem-solving)
- Network fundamentals (TCP/IP, DNS, DHCP concepts)
- Introduction to Group Policy
- Continue MS-102 study

#### Month 7-12 (Late L1B / L1C Preparation)
- Shadow L2 technicians regularly (learn advanced techniques)
- Begin taking ownership of more complex L1 issues
- Mentor L1A team members actively
- Prepare for MS-102 exam

#### Required Certifications (during L1B)
- **Microsoft 365 Certified: Administrator Associate (MS-102)** - MANDATORY within 12 months of L1B promotion
- **ITIL 4 Foundation** (optional but recommended)
- **CompTIA Network+** (optional, but helpful for networking knowledge)

---

### L1B Performance Metrics

**Minimum Performance Standards** (for L1C promotion consideration):

| Metric | Target | Minimum for Promotion |
|--------|--------|----------------------|
| **First Call Resolution (FCR)** | 55-65% | ≥60% (sustained 3 months) |
| **Escalation Rate** | 35-45% | <40% (appropriate escalations) |
| **Average Handle Time (AHT)** | 12-20 minutes | <20 min |
| **Customer Satisfaction (CSAT)** | >4.0/5.0 | ≥4.0/5.0 |
| **Ticket Documentation Quality** | >92% | ≥92% |
| **Categorization Accuracy** | >95% | ≥97% |
| **Time to MS-102 Certification** | 12 months | Within 15 months |
| **Mentoring Effectiveness** | L1A feedback | Positive feedback from mentees |

**Promotion Criteria to L1C**:
1. Minimum 6 months in L1B role
2. MS-102 certification obtained
3. Performance metrics met for 3 consecutive months
4. Demonstrated mentoring capability (L1A feedback)
5. Team Leader approval (readiness assessment)
6. Successfully completed 10+ L2 shadowing sessions

---

## L1C - Service Desk Analyst (Intermediate)

### Profile
- **Experience**: 18-36 months in IT support role
- **Education**: TAFE Cert III/IV IT or Bachelor's + MS-900 + MS-102 certifications
- **Typical Background**: Promoted from L1B, nearly L2-ready
- **Supervision Level**: Low - works independently, only complex/systemic issues require supervision
- **Time in Role**: 6-18 months (minimum 6 months before L2 consideration)

### Primary Purpose
Operate at top of L1 capability, handle complex L1 issues independently, actively mentor L1A/L1B, shadow L2 regularly preparing for promotion, reduce L2 escalation burden through advanced troubleshooting.

---

### Core Responsibilities (L1C)

#### 1. User Account Management - Expert L1 (95% Resolution)

**Added Capabilities** (beyond L1B):
- ✅ **Complex provisioning scenarios** (multi-role users, hybrid identity basics)
- ✅ **Advanced group management** (mail-enabled security groups, Microsoft 365 Groups)
- ✅ **Basic Conditional Access analysis** (identify policy causing block, recommend fix to L2)
- ✅ **Azure AD troubleshooting basics** (sign-in logs interpretation, identify common errors)
- ✅ **Guest user management** (B2B invitations, guest access troubleshooting)

**NOT Permitted** (Escalate to L2):
- ❌ Azure AD Connect modifications
- ❌ Conditional Access policy creation/modification
- ❌ Privileged Identity Management (PIM)
- ❌ Dynamic group rule creation
- ❌ Custom roles or admin unit configurations

**Escalation Criteria**:
- Issue requires architectural change
- Azure AD Connect sync issues
- Conditional Access policy modification needed
- Privileged access involved
- Time spent >45 minutes without resolution (L1C investigates deeper before escalating)

---

#### 2. Microsoft 365 Support - Near L2 Capability (85-90% Resolution)

**Added Capabilities**:
- ✅ **Advanced message trace analysis** (identify mail flow issues, recommend rules to L2)
- ✅ **Mailbox delegation complex scenarios** (automapping, shared mailbox delegates)
- ✅ **SharePoint troubleshooting** (permission inheritance, broken inheritance identification)
- ✅ **Teams advanced troubleshooting** (policies impact analysis, recommend policy changes to L2)
- ✅ **Power Automate basic support** (verify flows running, identify common errors)
- ✅ **Exchange Online basics** (mailbox properties, quota management, forwarding rules)
- ✅ **Mobile device management** (Intune enrollment troubleshooting, app protection policies)

**NOT Permitted** (Escalate to L2):
- ❌ Mail flow rule creation
- ❌ Retention policy configuration
- ❌ SharePoint site collection administration
- ❌ Teams policy creation/modification
- ❌ Power Automate flow creation (support only)

**Escalation Criteria**:
- Mail flow rule modification required
- Retention or compliance policies involved
- SharePoint requires structural change
- Teams policy change needed
- Time spent >60 minutes without clear path to resolution

---

#### 3. Endpoint Support - Advanced L1 (80-85% Resolution)

**Added Capabilities**:
- ✅ **Advanced Group Policy troubleshooting** (identify conflicting GPOs, document impact for L2)
- ✅ **Intune troubleshooting** (identify policy conflicts, check device sync status, enrollment errors)
- ✅ **Windows troubleshooting advanced** (Event Viewer analysis, common error identification)
- ✅ **Application installation troubleshooting** (investigate installation failures, check dependencies)
- ✅ **Performance troubleshooting basics** (Task Manager, Resource Monitor, identify resource hogs)
- ✅ **BitLocker recovery** (retrieve recovery key, guide user through unlock)

**NOT Permitted** (Escalate to L2):
- ❌ Group Policy creation/modification
- ❌ Intune policy creation/modification
- ❌ Registry editing (even under supervision)
- ❌ PowerShell remediation scripts
- ❌ Operating system in-place upgrades

**Escalation Criteria**:
- Issue requires policy modification
- Operating system corruption requiring DISM/repair
- Application compatibility issue (requires testing)
- Performance issue requiring deep analysis
- Time spent >60 minutes without resolution

---

#### 4. Complex Issue Ownership (L1C Specialty)

**Added Capabilities**:
- ✅ **Multi-service issues** (affect M365 + endpoint, coordinate troubleshooting)
- ✅ **Recurring issues** (identify patterns, document for L2 systemic analysis)
- ✅ **VIP user support** (handle escalated users requiring white-glove service)
- ✅ **Extended troubleshooting** (complex issues requiring 60-90 minutes investigation)
- ✅ **Vendor coordination** (coordinate with Microsoft support under L2 direction)

**Success Criteria**:
- L1C closes 85%+ of assigned tickets without L2 escalation
- L1C identifies systemic issues proactively (benefit entire client base)
- L1C provides detailed escalation notes when required (L2 rarely sends back)

---

#### 5. Mentoring & Knowledge Leadership (L1C Focus)

**Required Activities**:
- ✅ **Mentor L1A and L1B** (primary mentor role, answer complex questions)
- ✅ **Conduct peer training sessions** (monthly knowledge sharing, common issues)
- ✅ **Knowledge base leadership** (review articles, ensure accuracy, propose new articles)
- ✅ **Quality assurance** (review L1A/L1B tickets, provide constructive feedback)
- ✅ **Shadow L2 extensively** (4-6 hours per week minimum, prepare for L2 role)

**Success Metrics**:
- Mentee satisfaction: L1A/L1B report L1C as helpful and knowledgeable
- Knowledge base: 2-3 high-quality article contributions per quarter
- Training sessions: Conduct 1 peer training per month
- L2 shadowing: Complete 20+ L2 ticket observations

---

### L1C Training & Certification Path

#### Month 1-6 (Early L1C)
- Master all L1 technical capabilities
- Begin L2 skill development (shadowing extensively)
- Leadership development (mentoring, training delivery)
- Start studying for advanced certifications (MD-102, AZ-104)

#### Month 7-12 (Late L1C / L2 Preparation)
- Advanced troubleshooting methodologies
- Project participation (small projects, learn project workflows)
- Documentation excellence (write L2-quality escalation notes)
- Prepare for L2 promotion assessment

#### Month 13-18 (L2-Ready)
- Operate at near-L2 level (L2 colleagues treat as peer)
- Lead L1 team in absence of Team Leader
- Mentor L1A/L1B extensively
- Ready for L2 promotion when opening available

#### Required Certifications (during L1C)
- **Microsoft 365 Certified: Endpoint Administrator Associate (MD-102)** - RECOMMENDED within 18 months
- **Microsoft Certified: Azure Administrator Associate (AZ-104)** - OPTIONAL but valuable for L2 promotion
- **ITIL 4 Foundation** - RECOMMENDED for process understanding

---

### L1C Performance Metrics

**Minimum Performance Standards** (for L2 promotion consideration):

| Metric | Target | Minimum for Promotion |
|--------|--------|----------------------|
| **First Call Resolution (FCR)** | 65-75% | ≥70% (sustained 3 months) |
| **Escalation Rate** | 25-35% | <30% (appropriate escalations) |
| **Average Handle Time (AHT)** | 15-25 minutes | <25 min (complex issues take time) |
| **Customer Satisfaction (CSAT)** | >4.3/5.0 | ≥4.3/5.0 |
| **Ticket Documentation Quality** | >95% | ≥95% (L2-quality notes) |
| **Categorization Accuracy** | >97% | ≥98% |
| **Mentoring Effectiveness** | L1A/L1B feedback | Consistently positive feedback |
| **Knowledge Base Contributions** | 2-3 per quarter | ≥2 high-quality articles per quarter |

**Promotion Criteria to L2**:
1. Minimum 6 months in L1C role (12-18 months typical)
2. MD-102 certification obtained (or in progress with completion date)
3. Performance metrics met for 3 consecutive months
4. Demonstrated L2-level technical capability (via shadowing assessments)
5. Strong mentoring track record (L1A/L1B feedback)
6. Team Leader and L2 team approval (readiness assessment)
7. L2 position available (not automatic, depends on headcount)

---

## Progression Summary Table

### Technical Capability Progression

| Task Category | L1A (0-6mo) | L1B (6-18mo) | L1C (18-36mo) | L2 (36mo+) |
|---------------|-------------|--------------|---------------|------------|
| **Password Reset** | Basic only | All types | All types + analysis | All types + policy design |
| **Account Provisioning** | ❌ No | ✅ Standard templates | ✅ Complex scenarios | ✅ Custom + automation |
| **Microsoft 365 Basic** | ✅ Following guides | ✅ Independent | ✅ Advanced troubleshooting | ✅ Configuration changes |
| **M365 Advanced** | ❌ No | ✅ Message trace basics | ✅ Message trace + analysis | ✅ Mail flow rules |
| **SharePoint** | ❌ No | ✅ Basic permissions | ✅ Advanced permissions | ✅ Site architecture |
| **Endpoint Basics** | ✅ Following guides | ✅ Independent | ✅ Advanced troubleshooting | ✅ GPO/Intune policies |
| **Group Policy** | ❌ No | ✅ Identify issues | ✅ Detailed analysis | ✅ Create/modify policies |
| **Intune** | ❌ No | ✅ Verify compliance | ✅ Troubleshoot enrollment | ✅ Create policies |
| **Networking** | ❌ No | ✅ Basic diagnostics | ✅ Advanced diagnostics | ✅ Infrastructure changes |
| **Mentoring** | ❌ No | ✅ L1A only | ✅ L1A + L1B | ✅ All levels |
| **Projects** | ❌ No | ❌ Assist only | ❌ Assist only | ✅ Own small projects |

---

### Certification Progression Path

| Level | Required Certifications | Recommended | Nice to Have | Timeline |
|-------|------------------------|-------------|--------------|----------|
| **L1A** | MS-900 (Fundamentals) | CompTIA A+ | ITIL 4 Foundation | 3 months |
| **L1B** | MS-900 + MS-102 (Admin) | ITIL 4 Foundation | CompTIA Network+ | 12 months total |
| **L1C** | MS-900 + MS-102 + MD-102 (Endpoint) | AZ-104 (Azure Admin) | ITIL 4 Foundation | 18 months total |
| **L2** | MS-900 + MS-102 + MD-102 | AZ-104 + SC-900 (Security) | ITIL 4 Practitioner | Ongoing |

---

### Time in Role & Promotion Expectations

| Progression | Minimum Time | Typical Time | Fast Track | Notes |
|-------------|--------------|--------------|------------|-------|
| **L1A → L1B** | 3 months | 4-6 months | 3 months | Strong TAFE grads with MS-900 can progress quickly |
| **L1B → L1C** | 6 months | 8-12 months | 6 months | MS-102 certification required |
| **L1C → L2** | 6 months | 12-18 months | 9 months | Depends on L2 position availability |
| **L1A → L2 Total** | 15 months | 24-36 months | 18 months | Average journey from graduate to L2 |

**Fast Track Criteria**:
- Consistently exceeds performance metrics
- Obtains certifications ahead of schedule
- Demonstrates exceptional technical aptitude
- Strong mentoring and leadership skills
- Business need for acceleration (team gaps, high performer retention)

---

## Management & Oversight

### Team Leader Responsibilities

**L1A Management** (High Touch):
- Daily check-ins (first 2 weeks)
- Weekly 1:1 meetings (first 3 months)
- Buddy assignment (pair with L1B/L1C mentor)
- Close monitoring of metrics (daily review)
- Immediate coaching on quality issues

**L1B Management** (Moderate Touch):
- Weekly or bi-weekly 1:1 meetings
- Monitor FCR and escalation rates
- Provide stretch opportunities (complex tickets)
- Career development discussions (L1C pathway)
- Certification progress tracking

**L1C Management** (Light Touch):
- Monthly 1:1 meetings (career development focus)
- Monitor L2-readiness indicators
- Provide L2 shadowing opportunities
- Leadership development coaching
- L2 promotion preparation when position available

---

### Performance Review Cycle

**L1A** (Monthly for first 3 months, then quarterly):
- Metric review (FCR, escalation rate, quality)
- Certification progress (MS-900 timeline)
- Areas for improvement (specific coaching)
- L1B readiness assessment (after 3 months)

**L1B** (Quarterly):
- Metric review (FCR targets, quality)
- Certification progress (MS-102 timeline)
- Mentoring effectiveness (L1A feedback)
- L1C readiness assessment (after 6 months)

**L1C** (Quarterly):
- Metric review (near-L2 performance)
- Leadership development (mentoring, training delivery)
- L2 shadowing progress
- L2 readiness assessment (ongoing)

---

## Benefits of Sub-Level Structure

### For Orro

1. **Clear Career Path** - TAFE graduates see 18-24 month pathway to L2, improving retention
2. **Reduced L2 Escalations** - L1C handles complex L1 issues, reducing L2 burden by 15-20%
3. **Improved FCR** - Graduated responsibility increases overall L1 FCR from 50% to 65-70%
4. **Quality Hiring** - Can confidently hire TAFE grads knowing structured development exists
5. **Mentoring Culture** - Formalized mentoring builds team cohesion and knowledge transfer
6. **Performance Clarity** - Clear metrics and promotion criteria reduce "when do I get promoted?" questions

### For Team Members

1. **Clear Expectations** - Know exactly what's required at each level
2. **Achievable Milestones** - 3-6 month increments feel attainable vs 2-3 year L1→L2 jump
3. **Recognition** - Sub-level promotions provide regular recognition and motivation
4. **Skill Development** - Structured training path ensures comprehensive skill building
5. **Career Progression** - Transparent pathway from graduate to L2 in 18-24 months
6. **Fair Compensation** - Sub-levels can have salary bands reflecting increasing capability

### For Customers

1. **Better Service** - L1C handling complex issues means faster resolution
2. **Fewer Handoffs** - Graduated capability reduces escalations and ticket bouncing
3. **Consistent Quality** - Structured training ensures all L1 staff meet standards
4. **Faster FCR** - Overall L1 capability improvement raises first-call resolution rates

---

## Implementation Recommendations

### Phase 1: Immediate (Week 1-2)

1. **Map Current Team to Sub-Levels**
   - Assess current L1 team members against L1A/L1B/L1C criteria
   - Assign sub-levels based on experience, certifications, performance
   - Communicate new structure and what it means for each person

2. **Update Job Descriptions**
   - Create three distinct job descriptions (L1A, L1B, L1C)
   - Define clear responsibilities per sub-level
   - Add to Confluence for transparency

3. **Establish Mentoring Pairs**
   - Assign each L1A a mentor (L1B or L1C)
   - Define mentor responsibilities and time commitment
   - Set up regular mentor check-ins

### Phase 2: Short-Term (Month 1-2)

4. **Training Program Launch**
   - Develop L1A onboarding curriculum (Week 1-4 program)
   - Create L1B skill development plan
   - Design L1C L2-preparation program

5. **Performance Metrics Tracking**
   - Implement sub-level specific metrics tracking
   - Weekly metric reviews with Team Leader
   - Monthly performance reporting

6. **Certification Support**
   - Budget approval for certification costs (MS-900, MS-102, MD-102)
   - Study materials provided (Microsoft Learn, practice exams)
   - Certification achievement bonuses (optional incentive)

### Phase 3: Medium-Term (Month 3-6)

7. **Compensation Structure**
   - Define salary bands per sub-level
   - Plan salary adjustments for sub-level promotions
   - Budget approval for ongoing promotions

8. **Knowledge Base Enhancement**
   - Develop L1A-specific guides (step-by-step, screenshot-heavy)
   - Create L1B advanced troubleshooting guides
   - Build L1C near-L2 reference materials

9. **Review and Refine**
   - Gather feedback from team on sub-level structure
   - Adjust promotion criteria if needed
   - Celebrate first L1A→L1B and L1B→L1C promotions

---

## Success Metrics (Orro-Wide)

### 6-Month Targets (Post-Implementation)

| Metric | Baseline (Current) | 6-Month Target | 12-Month Target |
|--------|-------------------|----------------|-----------------|
| **Overall L1 FCR** | ~55% (estimated) | 60% | 65-70% |
| **L2 Escalation Rate** | ~40% (estimated) | 35% | 30% |
| **L1 Turnover** | 25-30% annually | 20% | 15% |
| **MS-900 Certification Rate** | Unknown | 100% of L1A+ | 100% maintained |
| **MS-102 Certification Rate** | Unknown | 80% of L1B+ | 100% of L1C+ |
| **Average Time L1→L2** | 24-36 months | 24 months | 18-24 months |

---

**Document Maintained By**: Service Desk Manager Agent | Maia
**Version**: 1.0
**Date**: 2025-10-08
**Next Review**: 2026-01-08 (Quarterly)
