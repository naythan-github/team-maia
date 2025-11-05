# ServiceDesk Level 2 Technical Assessment
## ANSWER KEY - CONFIDENTIAL (Final Version - No Telephony)

**⚠️ CONFIDENTIAL - FOR HIRING TEAM USE ONLY ⚠️**

**Do not distribute to candidates**

---

## Quick Answer Reference

| Q# | Answer | Domain | Difficulty | Q# | Answer | Domain | Difficulty |
|----|--------|--------|------------|----|---------|---------|-----------

|
| 1  | A      | Account | Easy | 26 | A | Security | Medium |
| 2  | A      | Account | Easy | 27 | A | Infrastructure | Medium |
| 3  | A      | Account | Easy | 28 | A | M365/Cloud | Medium |
| 4  | A      | Account | Easy | 29 | A | M365/Cloud | Medium |
| 5  | A      | M365 | Easy | 30 | A | Account | Medium |
| 6  | A      | M365 | Easy | 31 | A | Infrastructure | Medium |
| 7  | A      | Security | Easy | 32 | A | Infrastructure | Medium |
| 8  | A      | Security | Easy | 33 | A | Infrastructure | Medium |
| 9  | A      | Security | Easy | 34 | A | Infrastructure | Medium |
| 10 | A      | Infrastructure | Easy | 35 | A | Infrastructure | Medium |
| 11 | A      | Infrastructure | Easy | 36 | A | M365 | Medium |
| 12 | A      | Account | Easy | 37 | A | M365 | Medium |
| 13 | A      | Account | Medium | 38 | A | Account | Medium |
| 14 | A      | Account | Medium | 39 | A | Security | Medium |
| 15 | A      | Infrastructure | Medium | 40 | A | M365 | Medium |
| 16 | A      | Account | Medium | 41 | A | Account | Hard |
| 17 | A      | Account | Medium | 42 | A | M365 | Hard |
| 18 | A      | Account | Medium | 43 | A | M365 | Hard |
| 19 | A      | Account | Medium | 44 | A | M365 | Hard |
| 20 | A      | Account | Medium | 45 | A | Infrastructure | Hard |
| 21 | A      | M365 | Medium | 46 | A | Infrastructure | Hard |
| 22 | A      | M365 | Medium | 47 | A | Infrastructure | Hard |
| 23 | A      | Security | Medium | 48 | A | Infrastructure | Hard |
| 24 | A      | M365 | Medium | 49 | A/B | Infrastructure | Hard |
| 25 | A      | Security | Medium | 50 | A | Infrastructure | Hard |

**Note**: Question 49 accepts either A or B as correct (see detailed explanation)

---

## Test Restructuring Summary

**Changes from Previous Version**:
- ✅ **Removed**: All 10 Telephony & 3CX Administration questions
- ✅ **Added**: 10 new questions across remaining domains
- ✅ **Mixed**: All 50 questions by difficulty across all domains (no category grouping)
- ✅ **Progression**: Easy → Medium → Hard throughout test

**Domain Distribution**:
- **Account & Access Management**: 15 questions (30%)
- **Microsoft 365 & Cloud Services**: 15 questions (30%)
- **Security & Threat Management**: 7 questions (14%)
- **Infrastructure & Networking**: 13 questions (26%)

**Difficulty Distribution**:
- **Easy**: 12 questions (24%) - Foundational knowledge
- **Medium**: 28 questions (56%) - Core L2 problem-solving
- **Hard**: 10 questions (20%) - Advanced scenarios

---

## DETAILED ANSWER EXPLANATIONS

### Question 1: New User Provisioning Sequence
**Correct Answer: A** - Create AD → Sync Azure AD → Licenses → Software → Credentials

**Difficulty: Easy** | **Domain: Account Management**

**Why A is correct**: Proper dependency chain (identity first, cloud sync, services, config, credentials).

**Why others are wrong**:
- B/C/D: Incorrect dependency order

---

### Question 2: Shared Mailbox Reactivation
**Correct Answer: A** - Restore → Grant permissions → Auto-discover

**Difficulty: Easy** | **Domain: Account Management**

**Why A is correct**: Standard M365 shared mailbox workflow.

**Why others are wrong**:
- B: Shared password is security violation
- C: Distribution list for forwarding, not shared inbox
- D: Security groups for files, not mailbox

---

### Question 3: Template User Creation
**Correct Answer: A** - Copy from template → Create → Sync → Assign → Document

**Difficulty: Easy** | **Domain: Account Management**

**Why A is correct**: Template approach is efficient and reduces errors.

---

### Question 4: Agency Worker Limited Access
**Correct Answer: A** - On-premise AD only (no sync)

**Difficulty: Easy** | **Domain: Account Management**

**Why A is correct**: Domain auth without M365 licensing costs.

---

### Question 5: OneDrive/Outlook Storage
**Correct Answer: A** - Mailbox full, not OneDrive

**Difficulty: Easy** | **Domain: M365**

**Why A is correct**: Outlook storage warning indicates mailbox issue.

---

### Question 6: Cannot Open Attachments
**Correct Answer: A** - Antivirus quarantine → File associations → Outlook restrictions → Safe mode

**Difficulty: Easy** | **Domain: M365**

**Why A is correct**: Antivirus quarantine is the #1 cause of "click attachment, nothing happens." Checking this FIRST is most efficient. File associations, Outlook blocks, and safe mode test follow.

**Why others are wrong**:
- B: Mailbox full prevents receiving/sending, not opening attachments
- C: Reinstall is overkill for attachment issue
- D: Server down would prevent receiving emails entirely

**Best Practice Note**: Original version had antivirus third in sequence. Corrected to check antivirus FIRST as it's the most common cause (quarantined files can't be opened regardless of file associations).

---

### Question 7: Critical Vulnerability Response
**Correct Answer: A** - Review CVE → Identify → Patch → Prioritize → Deploy → Verify

**Difficulty: Easy** | **Domain: Security**

**Why A is correct**: Balanced vulnerability management (urgency + stability).

---

### Question 8: SSL Certificate 60-Day Expiry
**Correct Answer: A** - Verify → Check auto-renewal → Renew → Test → Deploy → Verify

**Difficulty: Easy** | **Domain: Security**

**Why A is correct**: 60-day notice allows proper planning and testing.

---

### Question 9: Motion Detection False Positives
**Correct Answer: A** - Review patterns → Sensitivity → Placement → Alert suppression

**Difficulty: Easy** | **Domain: Security**

**Why A is correct**: High-frequency false positives require tuning, not disabling.

---

### Question 10: Recurring Disk Alerts
**Correct Answer: A** - Check usage → Identify large files → Clean → Automate → Expansion

**Difficulty: Easy** | **Domain: Infrastructure**

**Why A is correct**: Recurring alerts indicate chronic problem needing root cause fix.

---

### Question 11: VM Decommissioning
**Correct Answer: A** - Approval → Backup → Delete → Release reservations → Update CMDB → Confirm

**Difficulty: Easy** | **Domain: Infrastructure**

**Why A is correct**: Complete decommissioning workflow with proper controls.

---

### Question 12: Add User to Distribution Group
**Correct Answer: A** - Verify requester authority → Confirm email → Add → Confirm

**Difficulty: Easy** | **Domain: Account Management**

**Why A is correct**: Verify authorization before making access changes.

**Why others are wrong**:
- B: Skips authorization check
- C: New member approval not required for distribution lists
- D: No need to notify entire list for additions

---

### Question 13: Restore Deleted User Account
**Correct Answer: A** - Azure AD Recycle Bin → Restore → Verify licenses restored automatically → Verify mailbox/OneDrive → Test → Document

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Azure AD has 30-day soft delete (Recycle Bin). Restoring user object automatically restores licenses, mailbox, and OneDrive. No manual license re-assignment needed.

**Why others are wrong**:
- B: INCORRECT - Can restore within 30 days via Recycle Bin
- C: New account loses all data (mailbox, OneDrive, SharePoint, Teams)
- D: On-premise only doesn't restore cloud resources (mailbox, OneDrive)

**Best Practice Note**: Microsoft automatically restores licenses when user is restored from Azure AD Recycle Bin. Manually re-assigning licenses is unnecessary and can cause duplicate assignment conflicts. Original version incorrectly stated "re-assign licenses" - corrected to "verify licenses restored automatically."

---

### Question 14: Update Job Title
**Correct Answer: A** - Active Directory → Update Title → Force sync → Verify in Azure AD/M365

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: In hybrid environment, AD is source of truth for user attributes.

**Why others are wrong**:
- B: M365 Admin Center changes overwritten by AD sync
- C: Manual signature doesn't fix Teams profile
- D: Azure AD to on-prem sync not supported (one-way only from AD)

---

### Question 15: Cannot Access Shared Folder
**Correct Answer: A** - Check group membership → Group permissions → Explicit Deny → Run as → Network

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: Systematic permission troubleshooting (group, permissions, deny, auth, network).

**Why others are wrong**:
- B: Direct permissions bypass group security
- C: Server restart doesn't fix permissions
- D: PC restart unlikely to fix persistent permission issue

---

### Question 16: Secure Folder Access (Group Added, Still Fails)
**Correct Answer: A** - Group membership → Group permissions → Inheritance → Test

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Group added but access denied = inheritance or explicit deny issue.

---

### Question 17: Machine Credentials Recovery
**Correct Answer: A** - Password vault → App support → Document

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Machine credentials different from user passwords.

---

### Question 18: App Access Despite Group Membership
**Correct Answer: A** - Propagation → Conditional Access → Role assignments → Cache

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Group membership isn't instant, Conditional Access can block, apps may need role assignment.

---

### Question 19: Service Principal Role Assignment
**Correct Answer: A** - Azure AD > Roles > Add assignment > Service principal

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Service principals CAN have Azure AD admin roles.

---

### Question 20: Multi-Environment Owner Assignment
**Correct Answer: A** - Add SIT/UAT, document PROD needs approval

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Follow delegation (lower environments OK, PROD needs approval).

---

### Question 21: Azure Portal Multi-User Access
**Correct Answer: A** - Service Health → Conditional Access → RBAC → Network

**Difficulty: Medium** | **Domain: M365/Cloud**

**Why A is correct**: Multi-user = check service-wide factors first.

---

### Question 22: Teams Guest Login Prompts
**Correct Answer: A** - Teams Admin Center > Meeting settings > Anonymous join

**Difficulty: Medium** | **Domain: M365**

**Why A is correct**: Meeting policies control anonymous vs guest login.

---

### Question 23: Windows Update Deployment
**Correct Answer: A** - Test → Review issues → Pilot → Monitor → Phased → Document

**Difficulty: Medium** | **Domain: Security**

**Why A is correct**: Proper patch management balances urgency with stability.

---

### Question 24: Browser-Specific Website Issue
**Correct Answer: A** - Cache → Incognito → Extensions → Update → Reset → GPO

**Difficulty: Medium** | **Domain: M365**

**Why A is correct**: Systematic browser troubleshooting.

---

### Question 25: IP Blacklisted on Firewall
**Correct Answer: A** - Logs → Verify blacklist → Threat feeds → Document → Policies → Geo-blocking

**Difficulty: Medium** | **Domain: Security**

**Why A is correct**: Security incident requires investigation.

**Note**: This is adapted from original 3CX PBX blacklist question, now generalized to firewall.

---

### Question 26: Backup Inactivity Alert
**Correct Answer: A** - Job status → Target access → Disk space → Source access → Manual test → Escalate

**Difficulty: Medium** | **Domain: Security**

**Why A is correct**: Backup failures are CRITICAL (data loss risk).

---

### Question 27: VPN Certificate Renewal
**Correct Answer: A** - Request cert → Test non-prod → Maintenance → Deploy → Test → Monitor → Document

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: VPN cert expiry = major outage, requires careful planning.

---

### Question 28: Azure VM Resource Health
**Correct Answer: A** - Resource Health → Metrics → Service Health → App logs → Remediate

**Difficulty: Medium** | **Domain: M365/Cloud**

**Why A is correct**: Azure alerts require investigation (details, metrics, platform vs app).

---

### Question 29: SPF Validation Failed
**Correct Answer: A** - SPF doesn't authorize sending IP → Check DNS → Add IP → Test → Wait for propagation

**Difficulty: Medium** | **Domain: M365/Cloud**

**Why A is correct**: SPF validates sending server IP against domain's DNS record.

**Why others are wrong**:
- B: SPF error = sender authentication, not recipient
- C: Mailbox full = different error
- D: Server down = different error

**Note**: This is a NEW question replacing telephony content.

---

### Question 30: Account Locked After Password Reset
**Correct Answer: A** - Check lockout status → Review Security logs for source → Unlock → Fix source → Educate

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Lockouts have specific source (old cached credentials, mobile app, etc.).

**Why others are wrong**:
- B: Unlocking without fixing source = immediate re-lock
- C: Password not the issue (already reset)
- D: Nuclear option, not needed

**Note**: This is a NEW question replacing telephony content.

---

### Question 31: DBA VPN Failure
**Correct Answer: A** - VPN logs → Account/cert validity → Firewall changes → Gateway status → Test

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: Sudden team failure = authentication, firewall, or gateway issue.

---

### Question 32: Ethernet No Connection
**Correct Answer: A** - Switch port → VLAN → Cable tester → Port security → Switch logs

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: Physical layer working (tried cable/port) = switch-side issue.

---

### Question 33: Azure Storage RBAC
**Correct Answer: A** - Storage Account > IAM > Add role > Assign managed identity

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: RBAC assigned at resource level (storage account IAM).

---

### Question 34: VPN Flapping Alerts
**Correct Answer: A** - Uptime → Flapping → ISP stability → Logs → Better alerting

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: Alerts without user complaints = flapping or alert too sensitive.

---

### Question 35: SendGrid Email Authentication
**Correct Answer: A** - SPF → DKIM → DMARC → Test → Verify

**Difficulty: Medium** | **Domain: Infrastructure**

**Why A is correct**: Sending on behalf of domain requires full email authentication.

---

### Question 36: SharePoint File Missing
**Correct Answer: A** - Recycle Bin → Permissions → Moved → Storage quota → Audit logs

**Difficulty: Medium** | **Domain: M365**

**Why A is correct**: Systematic check (deleted, permissions, moved, quota, audit trail).

**Why others are wrong**:
- B: Recoverable from Recycle Bin (93-day retention)
- C: Server restart doesn't recover deleted files
- D: Cache doesn't explain file missing for all users

**Note**: This is a NEW question replacing telephony content.

---

### Question 37: Teams Status Shows Away
**Correct Answer: A** - Auto-away timer → Power settings → Peripheral detection → Privacy settings → App update

**Difficulty: Medium** | **Domain: M365**

**Why A is correct**: Teams presence detection involves app settings, computer power, peripheral activity.

**Why others are wrong**:
- B: Internet speed doesn't affect presence status
- C: Expired license = can't use Teams at all
- D: Server down = widely reported

**Note**: This is a NEW question replacing telephony content.

---

### Question 38: Password Reset Identity Verification
**Correct Answer: A** - Documented verification process (manager approval + employee ID + additional proof) → Document method → Reset with mandatory change → Send via secure channel

**Difficulty: Medium** | **Domain: Account Management**

**Why A is correct**: Modern identity verification requires documented process with manager approval as primary method. Employee ID + additional proof provides multi-factor verification. Mandatory password change on first login adds security. Secure channel (encrypted email to manager or secure portal) prevents interception.

**Why others are wrong**:
- B: Personal email address is NOT verified - could be attacker-controlled (security risk)
- C: Single verification method too rigid - manager approval is acceptable alternative
- D: Public posting = major security violation (anyone can see password)

**Best Practice Note**:
- ❌ **REMOVED** from original answer: "security questions" (deprecated by NIST - easily guessed/researched on social media)
- ❌ **REMOVED** from original answer: "SMS to registered mobile" (vulnerable to SIM swapping and SS7 attacks)
- ✅ **EMPHASIS** on documented process with manager approval
- ✅ **ADDED** mandatory password change on first login
- ✅ **IMPROVED** secure channel specification (encrypted email to manager, not SMS)

**Security Standards**: Aligns with NIST SP 800-63B Digital Identity Guidelines and Microsoft identity protection best practices.

**Note**: This is a NEW question replacing telephony content, corrected for modern security best practices.

---

### Question 39: Phishing Analysis
**Correct Answer: A** - Headers → URL reputation → Search similar → Quarantine → Report → User education → Document

**Difficulty: Medium** | **Domain: Security**

**Why A is correct**: Complete phishing response (analyze, scope, remediate, protect, educate).

---

### Question 40: Cannot Send External Emails
**Correct Answer: A** - Send connectors → Permissions → Transport rules → Mailbox config → Mail flow logs

**Difficulty: Medium** | **Domain: M365**

**Why A is correct**: Internal works, external fails = transport/routing issue.

**Why others are wrong**:
- B: Mailbox full prevents receiving, not sending
- C: Password reset wouldn't affect only external mail
- D: Multiple invalid recipients unlikely, plus no bounce-back

**Note**: This is a NEW question replacing telephony content.

---

### Question 41: Azure AD Group Owner Failure
**Correct Answer: A** - Lacks Azure AD role → Group synced from on-prem → Guest restrictions

**Difficulty: Hard** | **Domain: Account Management**

**Why A is correct**: Three common causes for owner assignment failures.

---

### Question 42: SharePoint Document Not Visible
**Correct Answer: A** - Check-in status → Item permissions → View filters → Approval workflow

**Difficulty: Hard** | **Domain: M365**

**Why A is correct**: Four main causes (not checked in, permissions, filters, approval).

**Note**: 82-comment, 359-hour ticket (high complexity).

---

### Question 43: AVD Multi-User Connection Issues
**Correct Answer: A** - Host pool → User assignments → Session hosts → Diagnostics → Test

**Difficulty: Hard** | **Domain: M365**

**Why A is correct**: Different errors = different causes, systematic approach needed.

**Note**: 79-comment, 149-hour ticket (high complexity).

---

### Question 44: Email Deliverability Issues
**Correct Answer: A** - SPF/DKIM/DMARC → IP reputation → Content → Mail logs → Gradual remediation

**Difficulty: Hard** | **Domain: M365**

**Why A is correct**: Complex deliverability requires systematic analysis.

**Note**: 102-comment, 770-hour ticket (HIGHEST complexity).

---

### Question 45: Recurring Database Replication Failure
**Correct Answer: A** - Agent status → Network → Disk → Alerts → Monitoring → Root cause pattern

**Difficulty: Hard** | **Domain: Infrastructure**

**Why A is correct**: Repeat failures = underlying issue, full investigation needed.

---

### Question 46: SQL Replication Agent Failure
**Correct Answer: A** - SQL Agent service → Replication monitor → Job history → Network → Disk

**Difficulty: Hard** | **Domain: Infrastructure**

**Why A is correct**: Systematic diagnosis before action.

---

### Question 47: Healthcare PHI Azure Security
**Correct Answer: A** - HIPAA compliance → Network isolation → Conditional Access → Encryption → Audit → Vendor coordination → Testing

**Difficulty: Hard** | **Domain: Infrastructure**

**Why A is correct**: Healthcare PHI requires strict compliance (all elements critical).

**Note**: MOST COMPLEX ticket (94 comments, 2,330 hours = 97 days).

---

### Question 48: Power BI VNet Gateway
**Correct Answer: A** - Virtual Network (VNet) Data Gateway

**Difficulty: Hard** | **Domain: Infrastructure**

**Why A is correct**: VNet Data Gateway allows Power BI to access Azure VNets securely.

---

### Question 49: VNet-to-VNet Connection
**Correct Answer: A or B** - VPN Gateways + Connection OR VNet Peering

**Difficulty: Hard** | **Domain: Infrastructure**

**Scoring Note**: Accept EITHER A or B as correct.

**Why A is correct**: VNet-to-VNet uses VPN gateways (as question specifies).
**Why B is ALSO correct**: VNet Peering is superior modern method (faster, cheaper).

---

### Question 50: Production VPN Connectivity Alerts
**Correct Answer: A** - Service Health → Metrics → Tunnel reset → BGP routing → Zone-redundant → Support

**Difficulty: Hard** | **Domain: Infrastructure**

**Why A is correct**: Production VPN requires thorough investigation.

---

## Scoring Guidelines

### Overall Scoring
- **Pass**: 35/50 (70%)
- **Strong**: 40/50 (80%)
- **Excellent**: 45/50 (90%)

### Expected Performance by Difficulty
- **Easy Questions (12 total)**: Strong candidates 10-12/12 (83-100%)
- **Medium Questions (28 total)**: Strong candidates 20-24/28 (71-86%)
- **Hard Questions (10 total)**: Strong candidates 5-8/10 (50-80%)

### Candidate Evaluation Matrix

**90-100% (45-50 correct) - EXCELLENT**
- Likely: 11-12 Easy + 25-28 Medium + 8-10 Hard
- **Recommendation**: Strong Hire - Senior L2 or Lead
- **Profile**: Systematic troubleshooting across all domains and difficulty levels

**80-89% (40-44 correct) - STRONG**
- Likely: 10-12 Easy + 22-25 Medium + 5-8 Hard
- **Recommendation**: Hire - Solid L2
- **Profile**: Good foundation, strong on easy/medium, some advanced capability

**70-79% (35-39 correct) - PASS**
- Likely: 9-11 Easy + 19-22 Medium + 3-6 Hard
- **Recommendation**: Consider - Junior-Mid L2
- **Profile**: Meets minimum, may struggle with advanced scenarios

**60-69% (30-34 correct) - BORDERLINE FAIL**
- Likely: 8-10 Easy + 16-20 Medium + 2-5 Hard
- **Recommendation**: Likely Pass (below 70%)
- **Note**: Weak on foundational questions is concerning

**Below 60% (<30 correct) - FAIL**
- **Recommendation**: Do Not Progress
- **Note**: If <9/12 on Easy questions, fundamental gaps exist

---

## Domain Performance Analysis

**Track Performance by Domain**:
- **Account Management** (15 questions): Q1-4, 12-14, 16-20, 30, 38, 41
- **M365 & Cloud** (15 questions): Q5-6, 21-22, 24, 28-29, 36-37, 40, 42-44
- **Security** (7 questions): Q7-9, 23, 25-26, 39
- **Infrastructure** (13 questions): Q10-11, 15, 27, 31-35, 45-50

**Strong Candidate Profile**:
- **All domains ≥70%**: Well-rounded
- **3-4 domains ≥80%**: Strong with identifiable specialty
- **Weak in 1 domain (<60%)**: Trainable if not critical path

**Concerning Patterns**:
- Weak in Account Management = fundamental AD/Azure AD gaps
- Weak in M365 = limited Microsoft 365 admin experience
- Weak in Security = security awareness concerns (red flag)
- Weak in Infrastructure = limited networking/Azure knowledge

---

## New Questions Added (Replacing Telephony)

**Q12**: Add user to distribution group (Authorization verification)
**Q13**: Restore deleted user account (Azure AD Recycle Bin)
**Q14**: Update job title (Hybrid AD sync)
**Q15**: Cannot access shared folder (Permission troubleshooting)
**Q29**: SPF validation failed (Email authentication)
**Q30**: Account locked after password reset (Lockout source identification)
**Q36**: SharePoint file missing (Deleted file recovery)
**Q37**: Teams status shows away (Presence detection)
**Q38**: Password reset identity verification (Alternative verification methods)
**Q40**: Cannot send external emails (Mail flow troubleshooting)

**All new questions based on real tickets and common L2 scenarios.**

---

## Test Administration Notes

**Advantages of Mixed-Domain Structure**:
✅ Tests breadth of knowledge (not siloed by category)
✅ More realistic (L2 technicians don't get "only M365 tickets today")
✅ Progressive difficulty easier to manage (time allocation)
✅ Reduces pattern recognition (can't memorize "all account questions are easy")

**Time Management**:
- Easy questions (Q1-12): ~24 minutes (2 min each)
- Medium questions (Q13-40): ~70 minutes (2.5 min each)
- Hard questions (Q41-50): ~26 minutes (2.6 min each)
- Review: ~10 minutes
- **Total**: 120 minutes

---

**Document Version**: 3.0 (Final - No Telephony, Mixed Domains)
**Last Updated**: 2025-11-05
**Prepared By**: Technical Recruitment Agent (Maia System)
**Based On**: Real ServiceDesk ticket data (7,969 closed tickets, Jul-Oct 2025)
