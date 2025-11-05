# ServiceDesk Level 2 Technical Assessment
## Candidate Test Booklet - FINAL VERSION

**Position**: ServiceDesk Level 2 Support Specialist
**Test Duration**: 120 minutes
**Total Questions**: 50 multiple-choice questions
**Pass Score**: 70% (35/50 correct answers)

---

## Instructions

1. **Time Limit**: You have **120 minutes** (2 hours) to complete this assessment
2. **Question Format**: Each question has **4 possible answers (A, B, C, D)** - select the BEST answer
3. **Scoring**: Each correct answer = 1 point. No partial credit. No penalty for incorrect answers
4. **Resources**: This is an **open-book** test. You may use:
   - Internet search
   - Documentation websites (Microsoft Docs, vendor knowledge bases)
   - Personal notes
   - **NOT ALLOWED**: Communication with others, AI assistants (ChatGPT, etc.)
5. **Answer Recording**: Mark your answers clearly. If changing an answer, clearly indicate the new selection
6. **Question Progression**: Questions progress from easier to more challenging across all technical domains

---

## Test Coverage

**Technical Domains** (Mixed throughout test):
- Account & Access Management
- Microsoft 365 & Cloud Services
- Security & Threat Management
- Infrastructure & Networking

**Difficulty Progression**:
- Questions are ordered from easiest to most challenging
- All technical domains represented throughout

**Passing Requirement**: Minimum 70% overall (35/50 correct)

---

## TEST QUESTIONS

### Question 1
You receive an urgent new user request for a Speech Pathologist starting tomorrow. What is the correct account provisioning sequence?

A) Create AD account → Sync to Azure AD → Assign licenses → Configure software → Email credentials

B) Assign licenses first → Create AD account → Configure mailbox → Email credentials

C) Email credentials to manager → Create AD account → Assign licenses → Configure software

D) Configure software → Create AD account → Assign licenses → Email credentials

**Your Answer**: ______

---

### Question 2
You need to reactivate a shared mailbox and grant access to 3 users. What are the required steps?

A) Restore shared mailbox from deleted items → Grant "Full Access" and "Send As" permissions → Users auto-discover mailbox in Outlook

B) Create new user account → License it → Share password with 3 users

C) Create distribution list → Add 3 users as members → Enable mail

D) Restore mailbox → Add users to security group → Map mailbox manually

**Your Answer**: ______

---

### Question 3
You're setting up a new mobile healthcare worker who needs the same access as an existing user. What is the most EFFICIENT approach?

A) Copy permissions from existing user (template) → Create AD account → Sync → Assign copied groups/licenses → Delegate mailbox access → Document

B) Manually look up every group and license the existing user has → Create AD account → Manually add each group

C) Create AD account first → Email manager to tell you what access is needed

D) Clone the existing user's AD account completely

**Your Answer**: ______

---

### Question 4
You need to create urgent access for an agency worker who needs PC login only, NO Microsoft 365 license. What account type should you create?

A) On-premise AD account only (no Azure AD sync) with workstation logon rights

B) Full M365 account with E3 license

C) Guest user account in Azure AD

D) Local computer account on their assigned PC

**Your Answer**: ______

---

### Question 5
A user reports "Can't upload files to OneDrive" and Outlook shows storage warnings. What is the root cause?

A) User's mailbox is full (50GB limit), not OneDrive storage → Suggest archiving old emails or increasing mailbox quota

B) OneDrive sync client is broken

C) User's PC is out of disk space

D) OneDrive service is down globally

**Your Answer**: ______

---

### Question 6
A user reports they cannot open email attachments in Outlook. They click the attachment and nothing happens. What should you check?

A) Check antivirus quarantine (most common cause) → Check default file associations (is there an app for this file type?) → Check Outlook attachment restrictions (blocks .exe, .js) → Test Outlook safe mode

B) User's mailbox is full

C) Outlook needs to be reinstalled

D) Email server is down

**Your Answer**: ______

---

### Question 7
You receive a Microsoft Defender vulnerability notification for 15 endpoints with CVE-2025-12345 (CVSS 9.8 Critical). What is your response workflow?

A) Review CVE details and exploitability → Identify affected systems and business criticality → Check if patch available → Prioritize remediation (critical systems first) → Deploy patch or implement workaround → Verify remediation

B) Ignore the alert (too many false positives)

C) Immediately shut down all 15 affected endpoints

D) Deploy the patch to all systems simultaneously overnight without testing

**Your Answer**: ______

---

### Question 8
You receive an alert that an SSL certificate for gs1australia.com will expire in 60 days. What is your renewal workflow?

A) Verify certificate details (domain, expiry, issuer) → Check if auto-renewal configured (Let's Encrypt, Azure) → If manual: initiate renewal process → Test new certificate in non-production → Schedule production deployment → Verify renewal successful

B) Wait until 7 days before expiry to take action

C) Buy a new certificate from a different provider

D) Ignore the alert (60 days is plenty of time)

**Your Answer**: ______

---

### Question 9
You receive 682 "Motion detected" alerts from the Melbourne office airlock system over 3 months. What should you do?

A) Review alert patterns (time of day, frequency) → Check if sensor sensitivity configured correctly → Verify sensor placement (pointing at door, not hallway) → Implement alert suppression during business hours or rate limiting → Document as expected behavior if legitimate foot traffic

B) Disable all motion detection alerts (too noisy)

C) Acknowledge each alert individually (682 times)

D) Replace all motion sensors

**Your Answer**: ______

---

### Question 10
You receive recurring "disk health" alerts for server ATENASHAMI01 (32 times over 3 months). What is your remediation approach?

A) Check current disk usage and trends → Identify largest folders/files (WinDirStat, TreeSize) → Clean up temp files, logs, old backups → Implement disk cleanup automation → Consider disk expansion if legitimate growth → Monitor post-cleanup

B) Acknowledge alerts and do nothing (server still working)

C) Delete random files until disk usage drops below threshold

D) Add a second hard drive but don't clean up existing disk

**Your Answer**: ______

---

### Question 11
A client requests deletion of 3 VMs that have been shut down for 30 days (unused application). What is the proper decommissioning process?

A) Verify approval from budget owner → Take final backup of VMs → Delete VMs → Release reserved instances (if any) → Update CMDB/inventory → Confirm cost reduction with client → Document decommissioning

B) Delete VMs immediately (they're already shutdown)

C) Keep VMs indefinitely in shutdown state (no cost)

D) Delete VMs without backup (not needed, VMs were shutdown)

**Your Answer**: ______

---

### Question 12
A user needs to add another team member to an email distribution group. What should you verify before making the change?

A) Verify the requester has authority to modify the group (group owner or delegated admin) → Confirm new member's email address is correct → Add member → Send confirmation email to requester

B) Just add the member immediately (it's a simple request)

C) Require written approval from the new member first

D) Add the member and notify everyone in the distribution list

**Your Answer**: ______

---

### Question 13
A user account was deleted 20 days ago. The user's manager now requests the account be restored. What is your approach?

A) Check Azure AD Recycle Bin (30-day retention) → Restore user object → Verify licenses restored automatically → Verify mailbox and OneDrive restored → Test user login → Document restoration

B) Tell the manager the account cannot be restored (it's been deleted)

C) Create a new account with the same name

D) Restore from Active Directory on-premise backup only

**Your Answer**: ______

---

### Question 14
A user reports their job title is incorrect in email signatures and Teams. Where do you fix this?

A) Active Directory (on-premise) → Update "Title" field → Force Azure AD sync → Verify change appears in Azure AD and M365

B) Microsoft 365 Admin Center only

C) Have user update it manually in Outlook signature settings

D) Edit directly in Azure AD (changes will sync to on-premise AD)

**Your Answer**: ______

---

### Question 15
A user cannot access a newly shared folder on the file server. Other users can access it. What should you troubleshoot?

A) Check user is in the correct security group → Verify group has permissions on folder → Check for explicit Deny permissions on user account → Test with "Run as different user" to verify credentials → Check network connectivity

B) Grant direct permissions to the user immediately

C) Restart the file server

D) Have user restart their computer and try again

**Your Answer**: ______

---

### Question 16
A user should have access to a secure folder based on their role, but access is denied. The team tried adding them but it "didn't work." What should you troubleshoot?

A) Check if user is in the correct security group → Verify group has permissions on folder → Check for permission inheritance issues → Test access

B) Grant direct user permissions to the folder immediately

C) Have the user try a different browser

D) Restart the file server

**Your Answer**: ______

---

### Question 17
A user needs to recover machine credentials for a statutory reporting application (MIPS). They forgot the password and need to submit urgent returns. What is your approach?

A) Check if machine credentials are stored in IT password vault → If not, contact application support to regenerate credentials → Document location

B) Reset the user's AD password

C) Have the user contact the government department directly

D) Tell user credentials cannot be recovered, they must register a new account

**Your Answer**: ______

---

### Question 18
A user is in the correct Azure AD groups for an application but still gets access denied. What should you check?

A) Group membership propagation time → Conditional Access policies → Application role assignments → Browser cache/cookies

B) Just remove and re-add user to groups

C) Have user try a different PC

D) Restart the application server

**Your Answer**: ______

---

### Question 19
A developer requests Power Platform Administrator role for a managed identity (service principal) used in GitHub Actions. How do you assign this?

A) Azure AD > Roles and Administrators > Power Platform Administrator > Add assignment > Select service principal (application object)

B) Power Platform Admin Center > Security > Add user > Enter service principal name

C) Cannot assign admin roles to service principals, only users

D) Create a shared admin account and give credentials to the developer

**Your Answer**: ______

---

### Question 20
You're asked to add someone as owner to multiple environment groups (SIT, UAT, PROD). The request mentions "Manager will need to handle PROD." What should you do?

A) Add owner to SIT and UAT groups, document that PROD requires manager approval (escalate or reassign PROD portion)

B) Add owner to all three groups including PROD (they requested it)

C) Reject the entire request until manager approves

D) Add owner to PROD only since SIT/UAT are less important

**Your Answer**: ______

---

### Question 21
Multiple users report inability to access the Azure Portal. What is your troubleshooting priority order?

A) Check Azure Service Health Dashboard → Check organization's Conditional Access policies → Check user permissions (RBAC) → Test from different network

B) Reset all user passwords immediately

C) Restart your organization's Azure subscription

D) Have all users clear browser cache

**Your Answer**: ______

---

### Question 22
External users joining your Teams meetings are prompted to log in as guests instead of joining anonymously. Board members find this confusing. What setting controls this?

A) Teams Admin Center → Meetings → Meeting settings → Anonymous users can join a meeting (toggle) → Participants → Guest access settings

B) Azure AD → External Identities → Guest user access (change permissions)

C) Users must install Teams desktop app to avoid guest login

D) This is normal Teams behavior and cannot be changed

**Your Answer**: ______

---

### Question 23
A critical Windows security update (KB5063878) was released. What is the proper deployment approach for your production environment?

A) Test in non-production environment → Review Microsoft known issues → Deploy to pilot group → Monitor 48-72 hours → Deploy to production in phases → Document and communicate

B) Deploy to all production servers immediately (it's a security update)

C) Wait for Microsoft to force install it automatically

D) Skip testing and deploy overnight to avoid user complaints

**Your Answer**: ______

---

### Question 24
A website works in Edge but not Chrome. What is your troubleshooting sequence?

A) Clear Chrome cache/cookies → Test in Chrome Incognito mode (disables extensions) → Check for Chrome extensions blocking site → Update Chrome → Reset Chrome settings → Check for group policy restrictions

B) Uninstall and reinstall Chrome

C) Tell user to use Edge permanently

D) Contact website administrator to fix their site

**Your Answer**: ______

---

### Question 25
You receive an alert that IP 185.243.5.103 has been blacklisted on your organization's firewall for attempted unauthorized access. What should you investigate?

A) Check firewall logs for attack pattern from this IP → Verify blacklist is working (no successful connections) → Check if IP is known malicious (AbuseIPDB, threat feeds) → Document incident → Review security policies → Consider geographic blocking

B) Immediately whitelist the IP (might be a customer)

C) Restart the firewall to clear the blacklist

D) Ignore automated blacklist alerts (too many)

**Your Answer**: ______

---

### Question 26
You receive a "Backup Image Manager - Inactivity" alert indicating no successful backups for 48 hours. What is your investigation priority?

A) Check backup job status and logs → Verify backup target (disk/network) accessibility → Check disk space on backup destination → Verify source system (VM/server) accessibility → Test manual backup → Escalate if hardware failure suspected

B) Ignore it (backups probably running fine, just not reporting)

C) Delete old backups to free space and retry

D) Disable the alert (too noisy)

**Your Answer**: ______

---

### Question 27
Your VPN gateway SSL certificate expires in 2 weeks. What is your renewal and deployment plan?

A) Request new certificate for all VPN URLs (SAN cert or wildcard) → Test certificate in non-production VPN gateway → Schedule maintenance window → Deploy to production gateways → Test user connectivity → Monitor for issues → Document process

B) Wait until the certificate expires, then renew it immediately

C) Renew only the primary URL, ignore the redundant gateways

D) VPN certificates auto-renew, no action needed

**Your Answer**: ______

---

### Question 28
You receive an Azure Monitor alert: "ResourceHealthUnhealthyAlert" for production VM "webapp-prod-01." What should you do?

A) Check Azure Portal > Resource Health for details → Review VM metrics (CPU, memory, disk, network) → Check Azure Service Health (platform issue?) → Check application logs if VM accessible → Remediate specific issue or restart if needed

B) Immediately restart the VM without investigation

C) Ignore the alert (Azure sends too many false positives)

D) Open a P1 ticket with Microsoft Support immediately

**Your Answer**: ______

---

### Question 29
A user reports an email bounced back with error "550 5.7.1 Sender Policy Framework (SPF) validation failed." What does this mean and how do you fix it?

A) Your organization's SPF record doesn't authorize the sending server's IP → Check DNS SPF record → Add missing IP address or include statement → Test with mail-tester.com → Wait for DNS propagation (up to 24 hours)

B) The recipient's email address is invalid

C) User's mailbox is full

D) Email server is down

**Your Answer**: ______

---

### Question 30
A user cannot log in after a password reset. They get "Your account has been locked" message. What should you check?

A) Check Active Directory for account lockout status → Review Security Event Logs for lockout source (workstation, mobile device, old credential) → Unlock account → Identify and fix lockout source (cached credentials, mobile app) → Educate user

B) Just unlock the account and tell user to try again

C) Reset the password again

D) Delete and recreate the user account

**Your Answer**: ______

---

### Question 31
Your on-call DBA team suddenly cannot connect to Checkpoint VPN to access production databases. VPN was working yesterday. What do you check FIRST?

A) VPN server logs for authentication failures → Check if DBA user accounts/certificates still valid → Verify firewall rules changed recently → Check Checkpoint gateway status → Test with known-working account

B) Have all DBAs reinstall VPN client

C) Assume Checkpoint VPN is down, tell DBAs to wait

D) Give DBAs direct database access bypassing VPN (emergency)

**Your Answer**: ______

---

### Question 32
A workstation (FYNA090) has no ethernet connection. User tried different cable and different wall port - still no connection. WiFi works. What is your next troubleshooting step?

A) Check switch port status (enabled? errors?) → Check VLAN configuration on switch port → Test cable run with cable tester → Check for port security violations (MAC address filtering) → Check switch logs for the port

B) Reinstall network drivers on workstation

C) Replace the workstation NIC

D) Tell user to use WiFi permanently

**Your Answer**: ______

---

### Question 33
A developer requests "Storage Blob Data Reader" role for managed identity "polar-etl" on storage account "nwmphnpolarprod." How do you assign this?

A) Azure Portal > Storage Account > Access Control (IAM) > Add role assignment > Select "Storage Blob Data Reader" > Assign to "polar-etl" (managed identity) > Verify with developer

B) Azure AD > Managed Identities > polar-etl > Add role > Storage Blob Data Reader

C) Storage Account > Settings > Access Keys > Share key with developer

D) This is impossible - managed identities cannot access storage accounts

**Your Answer**: ______

---

### Question 34
You receive 41 "VPN connectivity changed" alerts over 3 months for the Bundaberg site VPN tunnel. Users have not reported issues. What should you investigate?

A) Review VPN tunnel uptime and stability metrics → Check for VPN tunnel flapping (up/down/up) → Review ISP stability at Bundaberg site → Check VPN gateway logs for disconnection reasons → Implement more intelligent alerting (sustained down > 5 min instead of every change)

B) Ignore the alerts since users aren't complaining

C) Rebuild the VPN tunnel from scratch

D) Upgrade the VPN gateway to higher tier

**Your Answer**: ______

---

### Question 35
An application uses SendGrid to send emails on behalf of your domain (@wqphn.com.au) but recipients mark emails as spam. Authentication checks fail. What needs to be configured?

A) Add SendGrid IPs to your domain's SPF record → Configure DKIM signing in SendGrid and publish DKIM records in DNS → Configure DMARC policy → Test email authentication with mail-tester.com → Verify SendGrid domain authentication

B) Just whitelist SendGrid in your firewall

C) Change the email "From" address to sendgrid.net domain

D) Stop using SendGrid and send directly from Exchange

**Your Answer**: ______

---

### Question 36
A user reports inability to access a shared file on SharePoint. The file was there yesterday. What should you check?

A) Check if file was deleted (Recycle Bin) → Check user's permissions on file/folder → Check if file was moved to different location → Check SharePoint site storage quota → Check audit logs for file activity

B) Tell user the file is permanently gone

C) Restart SharePoint server

D) Have user clear browser cache and try again

**Your Answer**: ______

---

### Question 37
A user reports their Teams status shows "Away" even when actively working. What could cause this?

A) Teams desktop app settings (Auto-away timer) → Computer power settings (screen saver/sleep mode) → Peripheral activity not detected (mouse/keyboard) → Presence privacy settings → Teams app needs update

B) User's internet connection is slow

C) Microsoft 365 license expired

D) Teams server is down

**Your Answer**: ______

---

### Question 38
A user requests urgent password reset but you cannot reach them by phone and their email is inaccessible (that's why they need reset). How do you verify their identity?

A) Use documented verification process (manager approval via phone/email + employee ID verification + additional proof of identity) → Document verification method used → Reset password with mandatory change on first login → Send temporary password via secure channel (encrypted email to manager or secure portal)

B) Reset the password and email it to their personal email address they provide

C) Refuse to reset without phone verification

D) Reset password and post it on company Slack/Teams channel for them to see

**Your Answer**: ______

---

### Question 39
A user reports a suspicious email with subject "Urgent: Your password will expire today - click here to update." What is your analysis and response workflow?

A) Analyze email headers (sender address, SPF/DKIM results, reply-to) → Check URL reputation (if link present) → Search mailbox for similar emails to other users → Quarantine/delete if phishing → Report to security team → Send user awareness reminder → Document indicators of compromise

B) Immediately delete the email from user's mailbox without analysis

C) Click the link to see if it's really phishing

D) Reply to the sender asking if they're legitimate

**Your Answer**: ______

---

### Question 40
A new user cannot send external emails - only internal. External recipients never receive the emails, no bounce-back error. What should you check?

A) Check mailbox send connectors → Check if user has "Send As" or "Send on Behalf" permissions issues → Check Exchange transport rules blocking external mail → Check if mailbox is configured correctly in Exchange → Check mail flow logs for the user's sent messages

B) User's mailbox is full

C) User's password needs to be reset

D) External recipient's email addresses are all invalid

**Your Answer**: ______

---

### Question 41
You try to add an owner to an Azure AD group but the operation fails. What could cause this?

A) User doesn't have required Azure AD role (Groups Administrator) → Group type doesn't allow owner assignment (synced from on-prem) → User object is guest account with restrictions

B) Internet connection is slow

C) The group has too many members

D) Azure AD is down globally

**Your Answer**: ______

---

### Question 42
A user uploaded a document to SharePoint but it doesn't appear in the "Published" library view. Other users can't see it. What should you check FIRST?

A) Document version history and check-in status → Item-level permissions → Library view filters → Content approval workflow status

B) Delete and re-upload the document

C) Restart SharePoint server

D) Have user try a different browser

**Your Answer**: ______

---

### Question 43
Multiple users report AVD connection issues. Some get "No resources available" and others get authentication errors. What is your diagnostic approach?

A) Check AVD host pool status and capacity → Check user group assignments → Check session host availability → Review connection diagnostics logs → Test with different error users

B) Tell all users to restart their computers

C) Restart all AVD session hosts immediately

D) Increase AVD host pool capacity

**Your Answer**: ______

---

### Question 44
A client's legitimate emails consistently go to recipients' junk folders. This has been ongoing for weeks. What should you analyze?

A) Sender's SPF, DKIM, DMARC records → IP reputation (blacklists) → Email content analysis (spam triggers) → Recipients' mail server logs (if accessible) → Gradual remediation plan

B) Just whitelist the sender in your users' Outlook

C) Change the email subject line to avoid spam keywords

D) Switch to a different email service provider immediately

**Your Answer**: ______

---

### Question 45
Database replication between DB1 and DB2 failed. This is the second time in two weeks. What should you investigate?

A) Check replication agent status and logs → Verify network connectivity between DB servers → Check disk space on both servers → Review why alerts didn't fire → Set up proper monitoring → Identify root cause pattern

B) Manually re-sync DB2 from DB1 backup and close ticket

C) Restart both database servers

D) Increase database server memory

**Your Answer**: ______

---

### Question 46
You receive an alert: "Replication: agent failure on pausembaxdb1." What should you do FIRST?

A) Check SQL Server Agent service status → Review replication monitor for specific error → Check replication agent job history → Verify network connectivity between servers → Check disk space on both publisher and subscriber

B) Restart the SQL Server service immediately

C) Delete and recreate replication from scratch

D) Call Microsoft Support immediately

**Your Answer**: ______

---

### Question 47
You're tasked with securing connection to a healthcare PHI (Protected Health Information) Azure Virtual Desktop server for Tasmania primary health. What considerations are CRITICAL?

A) HIPAA/healthcare compliance requirements → Network isolation (NSG, VPN, Private Link) → Conditional Access policies (MFA, trusted locations) → Data encryption in transit and at rest → Audit logging → Vendor coordination (Azure, healthcare IT, security team) → Phased implementation with testing

B) Just give users the AVD URL and login credentials

C) Set up VPN access using default configuration

D) Copy configuration from existing non-healthcare AVD

**Your Answer**: ______

---

### Question 48
Power BI needs to connect to Azure SQL Database in a different VNet. What type of gateway is required?

A) Virtual Network (VNet) Data Gateway - allows Power BI Service to access Azure resources in VNets without public endpoints

B) On-premises Data Gateway (standard) - for on-premise SQL servers only

C) No gateway needed - Power BI can connect directly to Azure SQL Database with public endpoint

D) Azure VPN Gateway - connects networks

**Your Answer**: ______

---

### Question 49
You need to create a VNet-to-VNet connection between TEST environment and PROD environment for database replication testing. What Azure components are required?

A) VNet Gateway in TEST → VNet Gateway in PROD → VNet-to-VNet connection (bidirectional) → Update route tables if needed → Test connectivity → Configure NSGs to allow replication traffic

B) Just peer the VNets (VNet Peering)

C) Site-to-Site VPN from TEST to on-premise, then on-premise to PROD

D) Copy database backup over instead of replication

**Your Answer**: ______

---

### Question 50
You receive "VPN connectivity changed" alerts for your Azure East region VPN (12 times). This is a critical production VPN connecting Azure regions. What is your response?

A) Check Azure Service Health for VPN Gateway service issues → Review VPN gateway metrics (tunnel status, bandwidth, packet loss) → Check for VPN tunnel reset events → Verify BGP routing if using route-based VPN → Consider zone-redundant gateway for higher SLA → Open Azure support case if persistent issues

B) Restart the VPN gateway during business hours

C) Switch all production traffic to secondary region immediately

D) Ignore (12 alerts over 3 months is normal)

**Your Answer**: ______

---

## End of Test

**Please review your answers before submitting.**

**Scoring Information**:
- Pass: 35/50 (70%)
- Strong: 40/50 (80%)
- Excellent: 45/50 (90%)

**Test Structure**:
- Questions progress from easier to more challenging
- All domains (Account, M365, Security, Infrastructure) mixed throughout

**Candidate Name**: ________________________________

**Date**: ________________________________

**Signature**: ________________________________
