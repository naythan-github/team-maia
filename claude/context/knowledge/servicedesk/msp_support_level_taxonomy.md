# MSP Support Level Taxonomy - Industry Standard

**Purpose**: Define clear task boundaries and responsibilities across support levels to eliminate "that isn't my job" accountability gaps

**Last Updated**: 2025-10-08
**Version**: 1.0
**Context**: Modern Cloud MSP (Azure, M365, Modern Workplace)

---

## Executive Summary

### Support Level Overview

| Level | Primary Function | Typical Experience | First Call Resolution Target | Escalation Rate Target |
|-------|-----------------|-------------------|------------------------------|----------------------|
| **L1 Service Desk** | Customer-facing support, basic troubleshooting, ticket triage | 0-2 years | 60-70% | 30-40% |
| **L2 Technical Support** | Advanced troubleshooting, technical implementation, knowledge mentoring | 2-5 years | 75-85% | 15-25% |
| **L3 Senior Engineers** | Complex problem resolution, architectural design, escalation endpoint | 5+ years | 90-95% | <5% (to vendor/R&D) |
| **Infrastructure/Platform** | Proactive platform management, automation, strategic projects | 3-8 years | N/A (project-based) | N/A |

---

## Key Principles

### Escalation Philosophy
- **L1**: Handles common requests following documented procedures, escalates when procedures don't exist or fail
- **L2**: Handles complex issues requiring deeper technical knowledge, escalates when issue is systemic or requires architectural change
- **L3**: Handles architectural/systemic issues, escalates only to vendors or when product limitation identified
- **Infrastructure**: Proactive work preventing tickets, owns platform health and automation

### "That Isn't My Job" Resolution Framework
**Rule**: If a task appears in your level's responsibility list, it IS your job. Escalation is only appropriate when:
1. **Complexity Exceeded**: Issue requires knowledge/access beyond your level
2. **Process Gap**: No documented procedure exists (L1→L2 for procedure creation)
3. **Architectural Change**: Solution requires platform modification (L2→L3)
4. **Systemic Issue**: Affects multiple clients or indicates platform problem (any→Infrastructure)

---

# Level 1 (L1) - Service Desk / Helpdesk

## Primary Responsibilities
- **First point of contact** for all customer support requests
- **Basic troubleshooting** using documented procedures and knowledge base
- **Ticket triage and categorization** for proper routing
- **Customer communication** and expectation management
- **Knowledge base usage** (not creation, but feedback on gaps)

## Core Task Categories

### 1. User Account Management (95% L1 Resolution)

#### Password & Authentication
- ✅ **Reset passwords** (Azure AD, local AD, application passwords)
- ✅ **Unlock accounts** (AD lockouts, Azure AD Smart Lockout)
- ✅ **Reset MFA** (Azure MFA, Microsoft Authenticator, SMS codes)
- ✅ **Troubleshoot authentication issues** (wrong password, account disabled, expired password)
- ✅ **Guide users through self-service password reset** (SSPR configuration verification)

#### Account Provisioning (Following Templates)
- ✅ **Create new user accounts** following documented templates
- ✅ **Assign Microsoft 365 licenses** (E3, E5, Business Premium as specified)
- ✅ **Add users to distribution lists** and Microsoft 365 Groups
- ✅ **Create shared mailboxes** (following naming conventions)
- ✅ **Assign basic permissions** (SharePoint, shared drives, applications)

#### Account Deprovisioning
- ✅ **Disable user accounts** (following offboarding checklist)
- ✅ **Remove licenses** from departed users
- ✅ **Convert mailbox to shared** (retention period per policy)
- ✅ **Document access handover** requirements for managers

**Escalate to L2 when**:
- Custom permission requirements outside standard templates
- Complex mailbox delegation or forwarding rules
- Group Policy conflicts affecting account creation
- License assignment failures (requires troubleshooting CSP/EA agreements)

---

### 2. Microsoft 365 Support (80-90% L1 Resolution)

#### Outlook & Exchange Online
- ✅ **Outlook profile creation and configuration**
- ✅ **Calendar permissions** (sharing, delegate access)
- ✅ **Email forwarding setup** (basic rules)
- ✅ **Shared mailbox access** (adding to Outlook profiles)
- ✅ **Troubleshoot email delivery issues** (using message trace)
- ✅ **PST file import/export guidance**
- ✅ **Mobile device email setup** (iOS Mail, Android Gmail app)
- ✅ **Out of office configuration**

#### OneDrive & SharePoint
- ✅ **OneDrive sync client troubleshooting** (reset, re-link)
- ✅ **SharePoint permissions** (site member, site visitor assignments)
- ✅ **File sharing link creation** (anyone/specific people)
- ✅ **OneDrive storage quota questions**
- ✅ **Known Folder Move issues** (Desktop, Documents, Pictures)

#### Microsoft Teams
- ✅ **Add/remove team members**
- ✅ **Basic Teams troubleshooting** (can't join meetings, audio issues)
- ✅ **Guest access requests** (following approval process)
- ✅ **Teams channel creation**
- ✅ **Teams calling basics** (transfer, hold, voicemail)

**Escalate to L2 when**:
- Mail flow rules affecting entire organization
- SharePoint site architecture or structural changes
- Advanced Teams configurations (policies, meeting settings, calling plans)
- Compliance or retention policy modifications
- Exchange transport rules or connector issues

---

### 3. Endpoint Support - Windows/Mac (70-80% L1 Resolution)

#### Common Desktop Issues
- ✅ **VPN connection troubleshooting** (credentials, re-download VPN profile)
- ✅ **Printer installation and configuration** (network printers, driver installation)
- ✅ **Mapped drive issues** (reconnect, credential updates)
- ✅ **Software installation** (from approved software catalog)
- ✅ **Browser issues** (cache clearing, reset settings, default browser)
- ✅ **Windows Update issues** (basic troubleshooting, check for updates)
- ✅ **Antivirus/EDR alerts** (false positives, basic remediation following runbooks)

#### Intune/MDM Support
- ✅ **Device enrollment verification** (check Intune compliance)
- ✅ **Company Portal troubleshooting** (re-sync, re-install)
- ✅ **Application deployment issues** (check Intune assignment, user device sync)
- ✅ **Basic compliance policy explanation** (BitLocker, password requirements)

#### macOS Support
- ✅ **Mac VPN configuration**
- ✅ **Mac printer setup**
- ✅ **Microsoft Office installation on Mac**
- ✅ **Basic keychain password issues**

**Escalate to L2 when**:
- Group Policy conflicts or modifications needed
- Intune policy creation or modification
- Persistent BSOD or kernel panics
- Application compatibility issues (requires testing)
- Hardware failures (after basic diagnostics)

---

### 4. Software Support (60-70% L1 Resolution)

#### Microsoft Office Applications
- ✅ **Office activation issues** (license verification, sign-in troubleshooting)
- ✅ **Office application crashes** (repair, reinstall)
- ✅ **Basic Word/Excel/PowerPoint support** (formatting, basic formulas)
- ✅ **Office updates** (manual update trigger, version checks)

#### Common Business Applications
- ✅ **Adobe Acrobat Reader** installation and basic support
- ✅ **Web browser support** (Edge, Chrome - installation, default browser)
- ✅ **Zoom/Teams** meeting client support (download, install, basic troubleshooting)
- ✅ **Application access issues** (login problems, licensing verification)

**Escalate to L2 when**:
- Advanced Excel/Access support (complex formulas, macros, database issues)
- Line-of-business application issues (CRM, ERP, custom apps)
- Software packaging or deployment issues
- Application integration problems

---

### 5. Mobile Device Support (70-80% L1 Resolution)

#### iOS Devices
- ✅ **Email configuration** (Outlook app, iOS Mail app)
- ✅ **Wi-Fi troubleshooting**
- ✅ **MDM enrollment** (Company Portal, device compliance)
- ✅ **App installation from Company Portal**
- ✅ **Basic iOS troubleshooting** (restart, forget/re-add network)

#### Android Devices
- ✅ **Email configuration** (Outlook app, Gmail app)
- ✅ **Wi-Fi troubleshooting**
- ✅ **MDM enrollment**
- ✅ **App installation from Company Portal**

**Escalate to L2 when**:
- MDM policy conflicts
- DEP/ABM enrollment issues (Apple Business Manager)
- Advanced mobile security concerns
- Mobile application management (MAM) policy issues

---

### 6. Basic Network Support (50-60% L1 Resolution)

#### Connectivity Issues
- ✅ **Basic network troubleshooting** (ipconfig, ping, tracert)
- ✅ **Wi-Fi connectivity issues** (forget/re-add network, check signal strength)
- ✅ **Internet connectivity verification** (check service status, router reboot guidance)
- ✅ **VPN connectivity** (basic troubleshooting, credential verification)

**Escalate to L2 when**:
- Network infrastructure issues (switches, routers, firewalls)
- DHCP/DNS configuration issues
- Network performance problems (latency, packet loss)
- Firewall rule modifications

---

### 7. Security & Access (40-50% L1 Resolution)

#### Basic Security Tasks
- ✅ **Malware alert triage** (following incident response runbook)
- ✅ **Phishing email reporting** (forward to security team, user guidance)
- ✅ **Suspicious activity reporting** (escalate to security team)
- ✅ **Security awareness guidance** (password best practices, phishing identification)

#### Access Requests
- ✅ **Basic access requests** (following approval matrix)
- ✅ **Application access** (standard permissions from templates)
- ✅ **File share permissions** (following principle of least privilege templates)

**Escalate to L2 when**:
- Security incidents requiring investigation
- Custom permission requirements outside templates
- Compliance-related access requests (audit, legal hold)
- Advanced security policy questions

---

### 8. General Support Tasks (L1 Ownership)

#### Ticket Management
- ✅ **Accurate ticket categorization** (category, severity, priority)
- ✅ **Detailed ticket documentation** (steps taken, resolution, customer communication)
- ✅ **Customer communication** (status updates, resolution confirmation)
- ✅ **SLA monitoring** (escalate when breaches imminent)
- ✅ **Knowledge base feedback** (report gaps, unclear procedures)

#### Proactive Communication
- ✅ **Scheduled maintenance notifications** (following communication templates)
- ✅ **Service outage updates** (status page updates, customer notifications)
- ✅ **Password expiry reminders**

---

## L1 Escalation Criteria

### When to Escalate to L2

#### Complexity
- Issue not covered by knowledge base procedures
- Troubleshooting steps exhausted without resolution
- Requires advanced technical knowledge (Group Policy, PowerShell, advanced networking)

#### Access/Permissions
- Requires elevated permissions not granted to L1
- Requires infrastructure access (servers, network equipment)
- Requires tenant-level configuration changes

#### Systemic Issues
- Issue affects multiple users
- Indicates platform or service problem
- Requires architectural analysis

#### Time Investment
- Issue exceeds 30-45 minutes of troubleshooting time (L1 threshold)
- Complex research required
- Requires vendor engagement

#### Customer Escalation
- Customer requests senior technician
- VIP customer requiring white-glove service
- Customer dissatisfaction with L1 resolution attempts

---

## L1 Success Metrics

### Performance Targets
- **First Call Resolution (FCR)**: 60-70%
- **Average Handle Time (AHT)**: 10-20 minutes
- **Escalation Rate**: 30-40%
- **Customer Satisfaction (CSAT)**: >4.0/5.0
- **SLA Compliance**: >95%

### Quality Metrics
- **Documentation Quality**: >90% tickets with clear notes
- **Categorization Accuracy**: >95%
- **Knowledge Base Usage**: >80% of tickets reference KB articles

---

## L1 Required Skills & Certifications

### Technical Skills (Minimum)
- Windows 10/11 desktop support
- Microsoft 365 administration basics (user management, licensing)
- Active Directory fundamentals
- Basic networking (TCP/IP, DNS, DHCP concepts)
- Ticket system proficiency (ServiceDesk, Jira, etc.)

### Recommended Certifications
- **Microsoft 365 Certified: Fundamentals (MS-900)** - Foundation knowledge
- **CompTIA A+** - Desktop support fundamentals
- **Microsoft 365 Certified: Modern Desktop Administrator Associate (MD-102)** - Endpoint management
- **ITIL 4 Foundation** - Service management best practices

### Soft Skills
- Excellent customer communication
- Patience and empathy
- Time management
- Documentation discipline
- Ability to follow procedures precisely

---

# Level 2 (L2) - Technical Support

## Primary Responsibilities
- **Advanced troubleshooting** requiring deep technical knowledge
- **Technical implementations** (complex configurations, migrations)
- **Knowledge base creation** and documentation
- **L1 mentoring and training**
- **Procedure development** for recurring issues
- **Proactive problem identification** and resolution

## Core Task Categories

### 1. Advanced User Account Management (90%+ L2 Resolution)

#### Complex Provisioning
- ✅ **Complex user provisioning** (VIP users, specialized access, multi-tenant)
- ✅ **Hybrid identity troubleshooting** (Azure AD Connect sync issues)
- ✅ **Advanced MFA configurations** (conditional access policies, named locations)
- ✅ **Dynamic group membership** rule creation and troubleshooting
- ✅ **Administrative role assignments** (following RBAC principles)
- ✅ **Guest user management** and B2B collaboration setup

#### Advanced Authentication
- ✅ **Single Sign-On (SSO) troubleshooting** (SAML, OAuth, OIDC)
- ✅ **Application integration** (Azure AD app registrations, service principals)
- ✅ **Conditional Access policy** creation and troubleshooting
- ✅ **Password hash sync troubleshooting**
- ✅ **Pass-through authentication issues**

**Escalate to L3 when**:
- Hybrid identity architecture changes (multiple forests, complex AD sync)
- Custom federation configurations (ADFS, third-party IdP)
- Identity governance and lifecycle management (PIM, access reviews)
- Cross-tenant migrations or mergers

---

### 2. Microsoft 365 Advanced Support (85-90% L2 Resolution)

#### Exchange Online Advanced
- ✅ **Mail flow rules** (transport rules, anti-spam, DLP)
- ✅ **Retention policies** and litigation hold setup
- ✅ **Advanced mailbox permissions** (Full Access, Send As, Send on Behalf)
- ✅ **Exchange hybrid troubleshooting** (mail flow, free/busy)
- ✅ **Email encryption** (S/MIME, OME)
- ✅ **Resource mailbox configuration** (room/equipment booking policies)
- ✅ **Distribution list management** (dynamic distribution lists, moderation)

#### SharePoint Advanced
- ✅ **SharePoint site architecture design**
- ✅ **Information architecture** (content types, columns, metadata)
- ✅ **Advanced permissions** (permission inheritance, custom permission levels)
- ✅ **SharePoint migration** (content migration from file shares)
- ✅ **Hub site configuration**
- ✅ **Search configuration** (managed properties, refiners)
- ✅ **Power Automate flows** for SharePoint automation

#### Teams Advanced
- ✅ **Teams policies** (messaging, meeting, calling policies)
- ✅ **Teams Phone System setup** (calling plans, direct routing basics)
- ✅ **Teams Rooms configuration**
- ✅ **Teams governance** (naming policies, expiration policies)
- ✅ **Private channels** and shared channels setup
- ✅ **Teams app deployment** and custom app policies

**Escalate to L3 when**:
- Exchange hybrid architecture changes
- SharePoint custom development (SPFx, web parts)
- Teams direct routing advanced scenarios (SBC configuration)
- Tenant-to-tenant migration planning
- Advanced compliance architecture (retention, DLP, information barriers)

---

### 3. Endpoint Management - Advanced (80-90% L2 Resolution)

#### Intune/Endpoint Manager
- ✅ **Intune policy creation** (configuration profiles, compliance policies)
- ✅ **Application deployment** (Win32 apps, LOB apps, MSI packaging)
- ✅ **Windows Autopilot deployment**
- ✅ **Device configuration profiles** (Wi-Fi, VPN, certificates)
- ✅ **Conditional Access integration** with Intune compliance
- ✅ **Endpoint security policies** (Defender settings, disk encryption)
- ✅ **Update rings and feature update policies**

#### Group Policy Management
- ✅ **Group Policy creation and troubleshooting**
- ✅ **GPO replication and inheritance issues**
- ✅ **Group Policy modeling and troubleshooting tools** (gpresult, RSoP)
- ✅ **Loopback processing** and advanced GPO configurations

#### Operating System Support
- ✅ **Windows 10/11 advanced troubleshooting** (event logs, performance monitor)
- ✅ **Windows feature updates** (troubleshooting upgrade failures)
- ✅ **Driver issues** (identification, replacement, rollback)
- ✅ **Registry modifications** (documented, approved changes)
- ✅ **Performance optimization** (startup programs, services, disk cleanup)
- ✅ **macOS advanced troubleshooting** (system logs, safe mode, disk utility)

**Escalate to L3 when**:
- Intune architecture design (tenant strategy, multi-tenant management)
- Custom Intune scripts requiring advanced PowerShell or shell scripting
- Operating system kernel issues or deep system troubleshooting
- Complex Windows Autopilot scenarios (hybrid join, self-deploying mode)

---

### 4. Application Support - Advanced (70-80% L2 Resolution)

#### Line-of-Business Applications
- ✅ **CRM/ERP support** (Dynamics, Salesforce, SAP - common issues)
- ✅ **Database connectivity issues** (ODBC, connection strings, SQL client tools)
- ✅ **Application compatibility troubleshooting** (App-V, MSIX, compatibility mode)
- ✅ **Application performance issues** (process monitoring, resource utilization)

#### Collaboration and Productivity
- ✅ **Advanced Office support** (complex Excel formulas, Access databases, PowerPoint automation)
- ✅ **Power Platform basics** (Power Automate, Power Apps - user support)
- ✅ **Adobe Creative Cloud** administration and support
- ✅ **Visio, Project** installation and licensing

#### Software Deployment
- ✅ **Application packaging** (MSI, MSIX, Win32)
- ✅ **Software deployment troubleshooting** (Intune, ConfigMgr, Group Policy)
- ✅ **License management** (volume licensing, subscription tracking)

**Escalate to L3 when**:
- Application architecture design or major changes
- Custom application development or integration
- Database administration tasks (SQL Server DBA work)
- Complex Power Platform solutions (requiring developer expertise)

---

### 5. Network Support - Advanced (60-70% L2 Resolution)

#### Network Troubleshooting
- ✅ **Advanced network diagnostics** (Wireshark, network monitoring tools)
- ✅ **DHCP server configuration**
- ✅ **DNS troubleshooting** (nslookup, dig, zone transfers)
- ✅ **VPN configuration** (client and server-side troubleshooting)
- ✅ **Network performance analysis** (latency, bandwidth utilization)

#### Network Services
- ✅ **File share access** (DFS, SMB permissions, NFS)
- ✅ **Print server management** (print queues, driver management, print policies)
- ✅ **Network device basic configuration** (switches, access points - basic tasks)

**Escalate to L3 when**:
- Network architecture changes (VLANs, subnets, routing)
- Firewall rule creation or security policy changes
- WAN/SD-WAN configuration
- Network infrastructure upgrades

---

### 6. Security Support - Advanced (50-60% L2 Resolution)

#### Security Operations
- ✅ **Security incident response** (following playbooks, containment actions)
- ✅ **Microsoft Defender investigation** (alerts, threat hunting basics)
- ✅ **Endpoint isolation** and remediation
- ✅ **Security policy deployment** (Intune security baselines)
- ✅ **BitLocker management** (recovery keys, troubleshooting)
- ✅ **Certificate management** (certificate deployment, renewal, troubleshooting)

#### Compliance Support
- ✅ **DLP policy implementation** (basic policies)
- ✅ **Retention label application**
- ✅ **Sensitivity labels** (manual application, troubleshooting)
- ✅ **Audit log searches** (M365 compliance center)

**Escalate to L3 when**:
- Complex security incidents (ransomware, data breach, advanced persistent threats)
- Security architecture design (zero trust, defense-in-depth strategies)
- Advanced threat hunting and forensics
- Compliance framework implementation (ISO 27001, SOC 2, HIPAA)

---

### 7. Server & Infrastructure Support (40-50% L2 Resolution)

#### Windows Server Support
- ✅ **Windows Server basic administration** (services, event logs, updates)
- ✅ **Active Directory user/computer management**
- ✅ **File server support** (share permissions, quotas, DFS)
- ✅ **DHCP/DNS server basic troubleshooting**
- ✅ **IIS basic administration** (website management, app pools)

#### Azure Support (Basic)
- ✅ **Azure VM basic support** (start/stop, resize, basic diagnostics)
- ✅ **Azure networking basics** (NSG rules, simple troubleshooting)
- ✅ **Azure backup verification** (backup status, test restores)
- ✅ **Azure Monitor alerts** (alert creation, basic queries)

**Escalate to L3/Infrastructure when**:
- Server architecture or infrastructure design
- Domain controller issues or AD forest/domain changes
- Complex Azure architecture (landing zones, hub-spoke, multi-region)
- Performance tuning at infrastructure layer

---

### 8. Projects & Implementations (L2 Project Ownership)

#### Small-Medium Projects
- ✅ **User migrations** (mailbox migrations, OneDrive migrations)
- ✅ **Desktop rollouts** (Autopilot deployment, imaging)
- ✅ **Application deployments** (new software rollouts)
- ✅ **Office 365 tenant configuration** (following design from L3)
- ✅ **Small office network setup** (<25 users)

#### Documentation & Knowledge Management
- ✅ **Knowledge base article creation** (from recurring tickets)
- ✅ **Runbook development** (procedures for L1 team)
- ✅ **Technical documentation** (as-built documentation, configuration guides)
- ✅ **Training material creation** (end-user guides, video walkthroughs)

**Escalate to L3 when**:
- Large-scale projects (>100 users, multi-site, complex dependencies)
- Projects requiring architectural design
- Projects with significant business risk
- Budget and resource planning beyond L2 scope

---

## L2 Escalation Criteria

### When to Escalate to L3

#### Architectural Changes
- Solution requires platform architecture modifications
- Infrastructure design or capacity planning
- Multi-tenant or cross-tenant scenarios

#### Systemic/Platform Issues
- Issue indicates product bug or limitation
- Affects multiple clients or broad user population
- Requires vendor escalation (Microsoft, vendor support)

#### Advanced Expertise Required
- Requires deep specialization (networking, security, development)
- Complex PowerShell or scripting beyond L2 capability
- Performance tuning at infrastructure level

#### Project Complexity
- Project scope exceeds L2 resources/timeline
- Project requires cross-functional coordination
- High-risk changes requiring change advisory board approval

---

## L2 Success Metrics

### Performance Targets
- **First Call Resolution (FCR)**: 75-85% (for issues escalated from L1)
- **Average Resolution Time**: 2-4 hours (for L2-appropriate issues)
- **Escalation Rate**: 15-25% (of tickets assigned to L2)
- **Customer Satisfaction (CSAT)**: >4.2/5.0
- **SLA Compliance**: >95%

### Quality Metrics
- **Knowledge Base Contribution**: 1-2 articles per month
- **Documentation Quality**: >95% tickets with detailed technical notes
- **L1 Mentoring**: 2-4 hours per month coaching L1 team
- **Procedure Development**: 1-2 new runbooks per quarter

---

## L2 Required Skills & Certifications

### Technical Skills (Minimum)
- Advanced Windows 10/11 administration
- Microsoft 365 administration (user, Exchange, SharePoint, Teams)
- Intune/Endpoint Manager administration
- Active Directory and Azure AD administration
- PowerShell scripting (intermediate level)
- Networking fundamentals (subnets, VLANs, routing basics)
- Security best practices (least privilege, defense-in-depth)

### Recommended Certifications
- **Microsoft 365 Certified: Administrator Expert (MS-102)** - M365 administration
- **Microsoft Certified: Azure Administrator Associate (AZ-104)** - Azure fundamentals
- **Microsoft Certified: Security, Compliance, and Identity Fundamentals (SC-900)** - Security basics
- **Microsoft 365 Certified: Endpoint Administrator Associate (MD-102)** - Intune/Endpoint Manager
- **CompTIA Network+** - Networking knowledge
- **ITIL 4 Foundation** - Service management

### Soft Skills
- Analytical problem-solving
- Technical documentation writing
- Mentoring and teaching ability
- Project coordination
- Customer-facing communication for complex issues

---

# Level 3 (L3) - Senior Engineers / Subject Matter Experts

## Primary Responsibilities
- **Complex technical problem resolution** serving as escalation endpoint
- **Architectural design and planning** for infrastructure and applications
- **Strategic technical projects** with business impact
- **Platform engineering** and automation development
- **Vendor liaison** and product expertise
- **Technical leadership** and advanced troubleshooting
- **Change advisory board participation**

## Core Task Categories

### 1. Identity & Access Management (95%+ L3 Resolution)

#### Advanced Identity Architecture
- ✅ **Azure AD Connect complex scenarios** (multi-forest, custom attribute flows)
- ✅ **Azure AD B2B/B2C architecture design**
- ✅ **Federated identity design** (ADFS, third-party IdP integration)
- ✅ **Privileged Identity Management (PIM)** design and implementation
- ✅ **Access reviews and governance** automation
- ✅ **Entitlement management** (access packages, lifecycle workflows)
- ✅ **Hybrid identity security** (PHS, PTA, federation selection)

#### Advanced Authentication & Authorization
- ✅ **Certificate-based authentication** infrastructure
- ✅ **FIDO2 passwordless authentication** deployment
- ✅ **Custom conditional access policies** with complex logic
- ✅ **Risk-based authentication** and Identity Protection
- ✅ **RBAC architecture design** (Azure RBAC, M365 RBAC, custom roles)

**Escalate to Vendor when**:
- Product limitations identified
- Bugs requiring engineering team investigation
- Feature requests for roadmap consideration

---

### 2. Microsoft 365 Architecture (90%+ L3 Resolution)

#### Exchange Online Architecture
- ✅ **Exchange hybrid architecture design** (multi-forest, complex routing)
- ✅ **Advanced mail flow design** (connectors, accepted domains, mail routing)
- ✅ **Public folder migration and architecture**
- ✅ **Exchange Online Protection** tuning and optimization
- ✅ **Journal and compliance archiving** architecture
- ✅ **Large mailbox migrations** (>10,000 mailboxes)

#### SharePoint Online Architecture
- ✅ **SharePoint Online site architecture** (hub sites, information architecture)
- ✅ **SharePoint migration strategy** (large-scale content migration)
- ✅ **Custom SharePoint development** (SPFx, Power Platform integration)
- ✅ **SharePoint governance framework** design
- ✅ **SharePoint search architecture** and optimization
- ✅ **Content type hub** and managed metadata design

#### Teams Enterprise Architecture
- ✅ **Teams Phone System advanced** (Direct Routing, SBC configuration)
- ✅ **Teams Rooms at scale** (conference room standardization)
- ✅ **Teams governance automation** (lifecycle management, naming, retention)
- ✅ **Teams network optimization** (QoS, traffic steering, bandwidth planning)
- ✅ **Teams compliance architecture** (information barriers, retention, DLP)

#### Power Platform Architecture
- ✅ **Power Platform environment strategy**
- ✅ **Power Platform governance** (DLP, CoE Starter Kit)
- ✅ **Complex Power Automate flows** (error handling, approval workflows)
- ✅ **Power Apps architecture** (data modeling, integration patterns)
- ✅ **Power BI workspace architecture** and security

**Escalate to Vendor when**:
- Microsoft product bugs
- Feature limitations requiring escalation to product group
- Complex scenarios requiring Microsoft CSS engagement

---

### 3. Endpoint Management Architecture (90%+ L3 Resolution)

#### Intune Architecture
- ✅ **Intune tenant architecture design** (multi-tenant, Intune for Education)
- ✅ **Co-management strategy** (ConfigMgr + Intune)
- ✅ **Windows Autopilot architecture** (pre-provisioning, self-deploying mode, hybrid join)
- ✅ **Complex Intune policies** (custom OMA-URI, ADMX ingestion)
- ✅ **Advanced scripting** (Proactive Remediations, custom deployments)
- ✅ **Intune device enrollment restrictions** and platform-specific policies

#### Configuration Manager (SCCM)
- ✅ **ConfigMgr architecture design** (hierarchy, boundaries, distribution points)
- ✅ **Operating system deployment** (task sequences, driver management)
- ✅ **Software distribution architecture** (packages, applications, supersedence)
- ✅ **Compliance settings and baselines**
- ✅ **ConfigMgr performance tuning**

#### Advanced Operating System Support
- ✅ **Windows Servicing strategy** (feature updates, quality updates, rings)
- ✅ **Windows image management** (custom images, feature optimization)
- ✅ **macOS management at scale** (Jamf Pro, Intune for macOS)
- ✅ **Linux endpoint management** (if applicable to business)

**Escalate to Vendor when**:
- Intune/ConfigMgr product bugs
- Operating system bugs requiring Microsoft/Apple support
- Hardware compatibility issues requiring OEM support

---

### 4. Security Architecture & Operations (85-95% L3 Resolution)

#### Security Architecture
- ✅ **Zero Trust architecture design** (identity, devices, apps, infrastructure)
- ✅ **Microsoft Defender for Endpoint** deployment and tuning
- ✅ **Microsoft Defender for Cloud Apps** (CASB architecture)
- ✅ **Microsoft Sentinel** (SIEM deployment, custom rules, playbooks)
- ✅ **Threat modeling and risk assessment**
- ✅ **Security baseline design** (CIS, Microsoft Security Baselines)

#### Advanced Security Operations
- ✅ **Complex security incident response** (ransomware, data breach, APT)
- ✅ **Threat hunting** (advanced KQL queries, behavioral analytics)
- ✅ **Security automation** (SOAR playbooks, automated remediation)
- ✅ **Penetration testing remediation** (working with security testing teams)
- ✅ **Vulnerability management program** design

#### Compliance & Governance
- ✅ **Compliance framework implementation** (ISO 27001, SOC 2, NIST, HIPAA)
- ✅ **Information protection architecture** (sensitivity labels, DLP, encryption)
- ✅ **Retention and records management** (retention policies, disposition)
- ✅ **eDiscovery and legal hold** architecture
- ✅ **Insider risk management** design

**Escalate to Vendor when**:
- Advanced persistent threats requiring Microsoft DART engagement
- Security product limitations
- Compliance framework questions requiring legal/auditor input

---

### 5. Network & Infrastructure Architecture (90%+ L3 Resolution)

#### Network Architecture
- ✅ **Network design** (LAN, WAN, VLAN, subnetting, routing)
- ✅ **SD-WAN architecture** and deployment
- ✅ **Firewall architecture** (rule design, security policy, high availability)
- ✅ **VPN architecture** (site-to-site, client VPN, split tunneling)
- ✅ **Wireless architecture** (controller-based, cloud-managed, RF planning)
- ✅ **Network security** (segmentation, micro-segmentation, NAC)

#### On-Premises Infrastructure
- ✅ **Active Directory architecture** (forest design, domain structure, site topology)
- ✅ **Domain controller deployment** (placement, replication, FSMO roles)
- ✅ **File server architecture** (DFS, namespaces, replication)
- ✅ **Hyper-V architecture** (clustering, live migration, storage)
- ✅ **Backup and disaster recovery** architecture

#### Azure Infrastructure
- ✅ **Azure landing zone design** (hub-spoke, management groups, subscriptions)
- ✅ **Azure networking** (Virtual Networks, VPN Gateway, ExpressRoute, Azure Firewall)
- ✅ **Azure Virtual Desktop** architecture and deployment
- ✅ **Azure Site Recovery** (disaster recovery planning)
- ✅ **Azure infrastructure as code** (Bicep, Terraform, ARM templates)
- ✅ **Azure governance** (policies, blueprints, cost management)

**Escalate to Vendor when**:
- Hardware failures requiring OEM support (Cisco, HPE, Dell EMC)
- Azure platform issues requiring Microsoft support
- ISP circuit issues

---

### 6. Collaboration & Telephony Architecture (85-90% L3 Resolution)

#### Telephony Systems
- ✅ **3CX architecture** (on-prem, cloud, hybrid deployment)
- ✅ **SIP trunking configuration** and optimization
- ✅ **Teams Direct Routing** (SBC configuration, number porting)
- ✅ **Contact center architecture** (call queues, auto attendants, IVR)
- ✅ **Call recording and compliance** (legal requirements, storage)

#### Unified Communications
- ✅ **UC strategy** (Teams as platform vs multi-vendor)
- ✅ **Meeting room standardization** (Teams Rooms, Zoom Rooms)
- ✅ **UC performance optimization** (QoS, bandwidth, call analytics)

**Escalate to Vendor when**:
- Carrier/SIP trunk provider issues
- 3CX product limitations
- Microsoft Teams Phone System platform issues

---

### 7. Application Architecture & Integration (70-80% L3 Resolution)

#### Application Integration
- ✅ **API integration design** (REST, SOAP, GraphQL)
- ✅ **Microsoft Graph API** development and automation
- ✅ **Azure Logic Apps** (complex workflows, enterprise integration)
- ✅ **Azure Functions** (serverless automation)
- ✅ **Azure API Management** design

#### Line-of-Business Applications
- ✅ **Application architecture assessment**
- ✅ **Application migration planning** (cloud readiness, dependencies)
- ✅ **Database design and optimization** (for DBAs with infrastructure focus)
- ✅ **Application performance monitoring** (Application Insights, custom telemetry)

**Escalate to Vendor when**:
- Application vendor support required
- Custom development requiring dedicated developers
- Database architecture requiring dedicated DBA expertise

---

### 8. Automation & DevOps (L3 Ownership)

#### Infrastructure as Code
- ✅ **Terraform/Bicep/ARM template development**
- ✅ **Git version control** for infrastructure code
- ✅ **CI/CD pipelines** (Azure DevOps, GitHub Actions)
- ✅ **Infrastructure automation testing**

#### PowerShell Automation
- ✅ **Advanced PowerShell scripting** (error handling, logging, modules)
- ✅ **PowerShell DSC** (Desired State Configuration)
- ✅ **Azure Automation** runbooks and scheduled tasks
- ✅ **Microsoft Graph PowerShell** automation

#### Operational Automation
- ✅ **Proactive monitoring and alerting** (Azure Monitor, Log Analytics)
- ✅ **Self-healing systems** (auto-remediation scripts)
- ✅ **Backup automation and verification**
- ✅ **Reporting automation** (executive dashboards, operational reports)

---

### 9. Strategic Projects (L3 Leadership)

#### Large-Scale Projects
- ✅ **Tenant migrations** (merger/acquisition scenarios)
- ✅ **Multi-site network rollouts**
- ✅ **Cloud migration programs** (lift-and-shift, re-architecture)
- ✅ **Zero Trust implementation programs**
- ✅ **Disaster recovery planning and testing**

#### Technical Leadership
- ✅ **Technical design authority** (architecture reviews, design sign-off)
- ✅ **Change Advisory Board (CAB) leadership**
- ✅ **Technical strategy development**
- ✅ **Vendor management** (technical relationship management)
- ✅ **L1/L2 technical mentoring** (advanced training, coaching)

---

## L3 Escalation Criteria

### When to Escalate to Vendor/External

#### Vendor Support Required
- Product bugs identified and proven
- Product limitations requiring feature requests
- Complex scenarios requiring vendor engineering team
- Warranty/support contract issues (hardware RMA, etc.)

#### Specialized Expertise Required
- Security incidents requiring forensics specialists
- Legal/compliance questions requiring legal counsel
- Application development requiring dedicated dev team
- Database administration requiring dedicated DBA (if not in L3 skillset)

---

## L3 Success Metrics

### Performance Targets
- **Resolution Rate**: 90-95% (of issues escalated to L3)
- **Escalation Rate**: <5% (only to vendors/external specialists)
- **Project Success Rate**: >90% on-time, on-budget
- **Customer Satisfaction (CSAT)**: >4.5/5.0
- **SLA Compliance**: >98%

### Strategic Metrics
- **Automation Development**: 2-4 automation projects per quarter
- **Technical Documentation**: Architecture diagrams, design documents maintained
- **Knowledge Transfer**: 4-8 hours per month advanced training for L1/L2
- **Vendor Relationship**: Regular engagement with key vendors (Microsoft TAM, etc.)

---

## L3 Required Skills & Certifications

### Technical Skills (Advanced)
- Expert-level Microsoft 365 and Azure administration
- Advanced PowerShell scripting and automation
- Infrastructure as Code (Terraform, Bicep, ARM)
- Networking expertise (routing, switching, firewalls)
- Security architecture and operations
- Enterprise architecture methodologies (TOGAF, Zachman)
- Project management fundamentals

### Recommended Certifications
- **Microsoft 365 Certified: Administrator Expert (MS-102)** - M365 advanced
- **Microsoft Certified: Azure Solutions Architect Expert (AZ-305)** - Azure architecture
- **Microsoft Certified: Security Operations Analyst Associate (SC-200)** - Security operations
- **Microsoft Certified: DevOps Engineer Expert (AZ-400)** - DevOps automation
- **Microsoft Certified: Cybersecurity Architect Expert (SC-100)** - Security architecture
- **Cisco CCNP** or equivalent - Advanced networking
- **TOGAF** or enterprise architecture certification

### Soft Skills
- Executive communication (C-level presentations)
- Strategic thinking and planning
- Project leadership
- Vendor negotiation
- Mentoring and coaching
- Business acumen and financial understanding

---

# Infrastructure / Platform Engineering Team

## Primary Responsibilities
- **Proactive platform management** preventing tickets before they occur
- **Platform health and optimization** (performance, capacity, availability)
- **Automation and tooling development** to reduce manual toil
- **Strategic infrastructure projects** (upgrades, migrations, new services)
- **Service reliability engineering** (monitoring, alerting, incident prevention)
- **Platform architecture** and continuous improvement

## Core Task Categories

### 1. Platform Operations (Infrastructure Ownership)

#### Azure Infrastructure Management
- ✅ **Azure subscription and tenant management**
- ✅ **Azure cost optimization** (reserved instances, right-sizing, orphaned resources)
- ✅ **Azure governance** (policies, management groups, tagging strategy)
- ✅ **Azure Monitor and Log Analytics** architecture and optimization
- ✅ **Azure Backup and Site Recovery** management
- ✅ **Azure capacity planning** and forecasting

#### On-Premises Infrastructure
- ✅ **Active Directory health and optimization**
- ✅ **Hyper-V cluster management**
- ✅ **Storage infrastructure** (SAN, NAS, backup appliances)
- ✅ **Network infrastructure** (core switches, routers, firewalls)
- ✅ **Server patching and maintenance** (automated where possible)

#### Microsoft 365 Tenant Management
- ✅ **Tenant health monitoring** (service health, message center)
- ✅ **Microsoft 365 feature rollout** management (targeted release, standard release)
- ✅ **Microsoft 365 roadmap tracking** and impact assessment
- ✅ **Microsoft 365 capacity planning** (mailbox quotas, storage limits)

---

### 2. Monitoring & Alerting (Proactive Prevention)

#### Alert Management
- ✅ **Alert tuning and suppression** (reduce alert noise)
- ✅ **Alert correlation** (identify related alerts, root cause analysis)
- ✅ **Alert routing automation** (send right alerts to right teams)
- ✅ **Self-healing alert remediation** (automated fix deployment)

#### Platform Monitoring
- ✅ **Azure Monitor** (VMs, storage, networking, services)
- ✅ **Microsoft 365 health monitoring** (service uptime, performance)
- ✅ **Network monitoring** (bandwidth utilization, latency, packet loss)
- ✅ **Application performance monitoring** (APM for critical apps)
- ✅ **Security monitoring** (Defender, Sentinel, firewall logs)

#### Performance Baselines
- ✅ **Performance baseline establishment** (normal vs abnormal behavior)
- ✅ **Trend analysis** (capacity planning, growth forecasting)
- ✅ **Anomaly detection** (machine learning-based alerting)

---

### 3. Automation & Tooling (Reducing Manual Toil)

#### Service Automation
- ✅ **Automated provisioning** (users, mailboxes, devices)
- ✅ **Automated remediation** (common issues auto-fixed)
- ✅ **Automated reporting** (health reports, capacity reports)
- ✅ **Automated compliance** (policy enforcement, configuration drift detection)

#### Automation Platforms
- ✅ **Azure Automation** (runbooks, DSC, update management)
- ✅ **Power Platform** (Power Automate flows for operations)
- ✅ **Azure DevOps pipelines** (infrastructure deployment)
- ✅ **Custom automation tools** (Python, PowerShell, APIs)

#### Self-Service Portals
- ✅ **Service catalog** (user self-service requests)
- ✅ **Automation portal** (IT team self-service tools)
- ✅ **Password reset self-service** (SSPR)

---

### 4. Reliability Engineering (SRE Practices)

#### Service Level Objectives (SLOs)
- ✅ **SLO definition** (availability, performance, latency targets)
- ✅ **SLI monitoring** (service level indicators tracking)
- ✅ **Error budget management** (balance velocity and reliability)

#### Incident Prevention
- ✅ **Blameless post-mortems** (learn from incidents)
- ✅ **Chaos engineering** (proactive failure testing)
- ✅ **Redundancy and failover testing**
- ✅ **Disaster recovery testing** (quarterly/annual DR drills)

#### Capacity Planning
- ✅ **Resource forecasting** (compute, storage, network, licensing)
- ✅ **Scalability planning** (growth accommodation)
- ✅ **Cost forecasting** (budget planning for infrastructure growth)

---

### 5. Platform Projects (Strategic Initiatives)

#### Infrastructure Upgrades
- ✅ **Operating system upgrades** (Windows Server in-place/migration)
- ✅ **Hypervisor upgrades** (Hyper-V, ESXi version upgrades)
- ✅ **Network equipment upgrades** (switch/router firmware, hardware refresh)
- ✅ **Microsoft 365 tenant upgrades** (new feature rollouts)

#### New Service Deployments
- ✅ **New Azure service adoption** (evaluate, pilot, production)
- ✅ **New Microsoft 365 workload rollout** (Teams, Power Platform, Viva)
- ✅ **New security tool deployment** (EDR, CASB, SIEM)
- ✅ **New monitoring tool deployment**

#### Migrations
- ✅ **Datacenter migrations** (physical to virtual, on-prem to Azure)
- ✅ **Cloud migrations** (workload migration, re-architecture)
- ✅ **Platform consolidation** (merging tenants, decommissioning legacy)

---

### 6. Security & Compliance (Platform Level)

#### Platform Security
- ✅ **Vulnerability management** (patch management, vulnerability scanning)
- ✅ **Security hardening** (CIS benchmarks, security baselines)
- ✅ **Security monitoring** (SIEM rule development, threat detection)
- ✅ **Penetration testing coordination** (remediation planning)

#### Compliance Management
- ✅ **Compliance framework maintenance** (ISO 27001, SOC 2, etc.)
- ✅ **Audit preparation** (evidence collection, control testing)
- ✅ **Policy enforcement** (technical controls for compliance policies)
- ✅ **Compliance reporting** (management reports, audit reports)

---

### 7. Vendor & Relationship Management

#### Vendor Coordination
- ✅ **Microsoft TAM relationship** (technical account management)
- ✅ **Vendor roadmap reviews** (evaluate new features, plan adoption)
- ✅ **Vendor escalation management** (P1/P2 incidents)
- ✅ **Licensing optimization** (EA true-ups, license management)

#### Service Provider Management
- ✅ **ISP relationship management** (circuit issues, upgrades)
- ✅ **Cloud provider management** (Azure, AWS, GCP)
- ✅ **SaaS vendor management** (Salesforce, Adobe, etc.)

---

### 8. Documentation & Knowledge Management

#### Architecture Documentation
- ✅ **Network diagrams** (logical, physical)
- ✅ **Azure architecture diagrams** (subscription hierarchy, networking)
- ✅ **Data flow diagrams** (integration architecture)
- ✅ **Security architecture documentation**

#### Operations Documentation
- ✅ **Runbook maintenance** (operational procedures)
- ✅ **Standard Operating Procedures (SOPs)**
- ✅ **Infrastructure configuration baseline documentation**
- ✅ **Disaster recovery plans**

---

## Infrastructure Team Success Metrics

### Operational Metrics
- **Platform Availability**: >99.5% uptime (per SLA)
- **Alert Noise Reduction**: <10% false positive alerts
- **Mean Time To Detect (MTTD)**: <5 minutes for critical issues
- **Mean Time To Resolve (MTTR)**: <30 minutes for critical platform issues
- **Automation Coverage**: >50% of repetitive tasks automated

### Strategic Metrics
- **Ticket Prevention**: 20-30% reduction in platform-related tickets year-over-year
- **Project Delivery**: >90% on-time, on-budget
- **Cost Optimization**: 10-15% annual cost savings from optimization efforts
- **Security Posture**: Zero critical vulnerabilities, 100% patch compliance

---

## Infrastructure Team Required Skills & Certifications

### Technical Skills (Advanced)
- Enterprise infrastructure architecture
- Multi-cloud platform management (Azure, AWS, GCP)
- Automation and scripting (PowerShell, Python, Terraform)
- Networking and security (deep expertise)
- Monitoring and observability (Azure Monitor, Grafana, ELK)
- SRE methodologies (SLO/SLI, error budgets, post-mortems)

### Recommended Certifications
- **Microsoft Certified: Azure Administrator Associate (AZ-104)**
- **Microsoft Certified: Azure Solutions Architect Expert (AZ-305)**
- **Microsoft Certified: DevOps Engineer Expert (AZ-400)**
- **Cisco CCNP** or equivalent
- **CompTIA Security+** or CISSP
- **ITIL 4** (Practitioner or higher)

### Soft Skills
- Strategic planning
- Cross-functional collaboration
- Vendor negotiation
- Budget management
- Operational discipline

---

# Support Level Quick Reference Matrix

## Ticket Routing Decision Tree

| Ticket Type | Primary Owner | Escalate To | Notes |
|-------------|---------------|-------------|-------|
| **Password reset, account unlock** | L1 | N/A | 100% L1 ownership |
| **Basic software install** | L1 | L2 if packaging needed | Standard catalog = L1 |
| **Email delivery issue** | L1 | L2 if mail flow rules involved | Message trace = L1 |
| **Printer driver issue** | L1 | L2 if Group Policy involved | Basic install = L1 |
| **VPN connectivity** | L1 | L2 if VPN server config needed | Client-side = L1 |
| **MFA reset** | L1 | L2 if Conditional Access involved | Standard reset = L1 |
| **Intune policy creation** | L2 | L3 if architecture change | Implementation = L2 |
| **Exchange mail flow rule** | L2 | L3 if tenant-wide impact | Standard rules = L2 |
| **Complex SharePoint permissions** | L2 | L3 if custom development | Standard permissions = L2 |
| **Security incident (malware)** | L2 | L3 if ransomware/breach | Containment = L2, investigation = L3 |
| **Application packaging** | L2 | L3 if complex dependencies | Standard MSI/MSIX = L2 |
| **Azure VM performance issue** | L2 | Infrastructure if Azure platform | VM troubleshooting = L2 |
| **Network performance problem** | L2 | L3/Infrastructure | Basic diagnostics = L2 |
| **Azure architecture design** | L3 | N/A | 100% L3 ownership |
| **Tenant migration** | L3 | N/A | L3 project leadership |
| **Zero Trust implementation** | L3 | N/A | L3 architecture |
| **Alert automation** | Infrastructure | N/A | Platform team ownership |
| **Azure cost optimization** | Infrastructure | N/A | FinOps focus |
| **Platform monitoring** | Infrastructure | N/A | Proactive operations |

---

# Resolving "That Isn't My Job" Conflicts

## Accountability Framework

### Clear Ownership Rules

1. **"If it's in your level's task list, it IS your job"**
   - No deflection allowed if task clearly documented in your level
   - Escalation only permitted per documented escalation criteria
   - Performance reviews include accountability for owned tasks

2. **"Escalation requires justification"**
   - Must document why escalating (complexity, access, time, etc.)
   - Ticket notes must explain escalation reason
   - L2/L3 can send back if escalation criteria not met

3. **"Gray areas go to manager decision"**
   - Manager/team lead determines ownership for ambiguous tasks
   - Document decision to prevent future conflicts
   - Update taxonomy document with clarification

4. **"Continuous learning eliminates gray areas"**
   - L1 trained on new procedures (expands L1 capability)
   - L2 develops new runbooks (moves work from L2 to L1)
   - L3 implements automation (removes work from all levels)

### Conflict Resolution Process

**Step 1**: Check this taxonomy document
- Is task clearly assigned to a level?
- Are escalation criteria met?

**Step 2**: Check knowledge base
- Does procedure exist?
- Is procedure current and accurate?

**Step 3**: Manager escalation
- If still unclear, escalate to management
- Manager determines ownership based on:
  - Team capacity
  - Skill availability
  - Customer impact
  - Learning opportunity

**Step 4**: Document decision
- Update taxonomy if needed
- Create runbook if procedure gap
- Train team on clarification

---

## Implementation Recommendations

### For Orro Deployment

1. **Distribute this taxonomy** to all technical staff
2. **Train team leads** on enforcement and conflict resolution
3. **Update ticketing system** with routing rules based on taxonomy
4. **Create escalation workflows** that reference this document
5. **Performance reviews** include adherence to taxonomy
6. **Quarterly taxonomy reviews** (update based on new services, feedback)

### Success Criteria

- **Reduced escalation conflicts**: <5% tickets disputed for ownership
- **Improved FCR**: L1 60%+ (from understanding ownership)
- **Faster resolution**: Clear ownership = faster action
- **Better team morale**: Clarity reduces frustration

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Next Review**: 2026-01-08 (Quarterly)
**Owner**: Service Desk Manager
**Maintained By**: Maia Service Desk Manager Agent
