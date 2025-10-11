# Windows Provisioning Package (PPKG) - Implementation Guide

**Document Owner**: Endpoint Engineering Team
**Last Updated**: 2025-10-11
**Status**: Technical Implementation Guide
**Related**: 3rd Party Laptop Provisioning Strategy

---

## Executive Summary

This guide provides detailed technical implementation for Windows Provisioning Packages (PPKG), the interim solution for provisioning customer devices at 3rd party premises while Intune environments mature toward Autopilot readiness.

**Key Outcome**: Enable 3rd party vendor to provision Windows 11 devices offline with customer-specific configurations that auto-enroll to Intune on first user boot.

---

## What is a PPKG?

### Definition

A Windows Provisioning Package (PPKG) is a container file (.ppkg) that contains Windows configuration settings applied during or after Out-of-Box Experience (OOBE). It enables offline device configuration without network connectivity.

### Use Cases

| Scenario | PPKG Capability | Value |
|----------|----------------|-------|
| **3rd Party Provisioning** | Apply customer settings offline at vendor premises | No VPN/network access required |
| **Intune Enrollment** | Embed bulk enrollment token for automatic enrollment | Zero-touch Intune onboarding |
| **Company Branding** | Pre-configure wallpaper, lock screen, support info | Professional user experience |
| **Security Baseline** | Local admin account, certificates, BitLocker prep | Secure device handoff |
| **Network Pre-Config** | Wi-Fi profiles, VPN settings, DNS | Connectivity ready on first boot |

### What PPKG Can Do

✅ **Configuration (Offline)**:
- Create/modify local user accounts
- Set time zone, region, language
- Install certificates (Root CA, Intermediate CA)
- Configure Wi-Fi profiles
- Apply company branding (wallpaper, lock screen)
- Stage domain join credentials (executes when DC reachable)
- Stage Intune enrollment token (executes on first boot)
- Configure Edge/IE favorites
- Disable Windows consumer features
- Set power management policies

❌ **What PPKG Cannot Do**:
- Install applications (no Win32 app support)
- Join domain immediately offline (requires DC connectivity)
- Enroll in Intune immediately offline (happens at first boot)
- Modify Group Policy (applied after domain join)
- BitLocker encryption (done via Intune policy post-enrollment)
- Windows Updates (managed by Intune post-enrollment)

---

## PPKG Types for Customer Segments

### Type 1: Intune-Ready PPKG (60% of customers)

**For**: Customers with Intune license and basic configuration

**PPKG Contains**:
```
Required:
- Intune bulk enrollment token (180-day validity)
- Local administrator account (3rd party troubleshooting)
- Company branding (logo, wallpaper, support info)

Optional:
- Time zone/region settings
- Wi-Fi profiles (if provisioning at customer office)
- Root/Intermediate CA certificates (if customer has PKI)
```

**Workflow**:
```
3rd Party:
1. Apply Windows 11 clean image
2. Apply PPKG during/after OOBE
3. Verify PPKG applied (check wallpaper, local admin)
4. Ship device

End User:
1. Unbox → Complete OOBE
2. Sign in with work credentials (user@customer.com)
3. Intune enrollment triggers automatically
4. Company Portal installs → Apps/policies deploy
5. 15-30 minutes → Device ready
```

**Success Rate**: 90-95%

---

### Type 2: Azure AD Join PPKG (25% of customers - No Intune)

**For**: Customers with Entra ID (Azure AD) only, no device management

**PPKG Contains**:
```
Required:
- Azure AD bulk enrollment token (180-day validity)
- Local administrator account
- Company branding

Optional:
- Wi-Fi profiles
- Time zone/region
```

**Workflow**:
```
3rd Party:
1. Apply Windows 11 clean image
2. Apply PPKG
3. Ship device

End User:
1. Complete OOBE
2. Sign in with work account
3. Device Azure AD joins automatically
4. User has SSO to M365 apps
5. NO device management (user installs apps manually)
```

**Warning**: This creates unmanaged devices. Recommend Intune bootstrap service instead.

**Success Rate**: 85-90% (technical), but high operational risk

---

### Type 3: Domain Join PPKG (15% of customers - On-Prem AD)

**For**: Customers with on-premises Active Directory, no Intune

**PPKG Contains**:
```
Required:
- Domain join credentials (delegated service account)
- Target OU path
- Local administrator account
- Company branding

Optional:
- Wi-Fi profiles (for domain connectivity)
- Root/Intermediate CA certificates
```

**Workflow**:
```
3rd Party:
1. Apply Windows 11 clean image
2. Apply PPKG (domain join staged, not executed)
3. Ship device

End User:
1. Unbox at office (or connect VPN at home)
2. Device connects to corporate network
3. Domain join executes automatically (when DC reachable)
4. Device reboots
5. User sees domain login screen
6. Group Policy applies
```

**Critical Dependency**: Device must reach domain controller on first network connection.

**Success Rate**: 60-75% (network connectivity issues common)

**Recommended Alternative**: Ship devices to customer IT for domain join (100% success rate).

---

## PPKG Creation Process

### Prerequisites

**Tools Required**:
- Windows 11 Pro/Enterprise workstation
- Windows Configuration Designer (free from Microsoft)
  - Download: https://learn.microsoft.com/en-us/windows/configuration/provisioning-packages/provisioning-install-icd
- Administrative access to customer Intune/Azure AD tenant (for token generation)

**Information Needed from Customer**:
```
For All Customers:
- Company logo (PNG, <500KB)
- Company wallpaper (1920x1080 JPG/PNG)
- Support contact info (phone, email, IT portal URL)
- Time zone (or use default)

For Intune Customers:
- Intune Administrator access (to generate bulk enrollment token)

For Azure AD Only Customers:
- Global Administrator access (to generate Azure AD bulk token)

For On-Prem AD Customers:
- Domain name (e.g., customer.local)
- Domain join service account credentials
- Target OU path (e.g., OU=Workstations,DC=customer,DC=local)
- Root/Intermediate CA certificates (.cer files)
- Wi-Fi profiles (SSID, auth type, credentials)
```

---

### Step-by-Step: Creating Intune-Ready PPKG

#### Step 1: Generate Intune Bulk Enrollment Token

**In Customer Intune Tenant**:
```
1. Navigate to Microsoft Intune admin center
   URL: https://intune.microsoft.com

2. Go to: Devices → Enroll devices → Windows enrollment → Bulk enrollment

3. Click "Add" → Create new bulk enrollment profile
   - Profile name: "3rd Party Provisioning - [Date]"
   - Automatically enroll devices: Yes
   - Save

4. Download provisioning package
   - This downloads a .ppkg file
   - Extract the token: Open .ppkg in Windows Configuration Designer
   - Copy bulk enrollment token (Base64 string)
   - Token valid for 180 days from creation

5. Document token details:
   - Customer name
   - Token created date
   - Token expiry date (created + 180 days)
   - Set calendar reminder for renewal (2 weeks before expiry)
```

**Token Example**:
```
{
    "CloudAssignedTenantId": "12345678-1234-1234-1234-123456789abc",
    "CloudAssignedTenantDomain": "customer.onmicrosoft.com",
    "Version": 1
}
```

---

#### Step 2: Create PPKG in Windows Configuration Designer

**Launch Windows Configuration Designer**:
```
Start → Windows Configuration Designer
```

**Create New Project**:
```
1. New project → Provisioning package
2. Project name: CustomerName_PPKG_v1.0_20251011
3. Description: 3rd party provisioning package for [Customer Name]
4. Select: Common to all Windows desktop editions
5. Click Next → Finish
```

---

#### Step 3: Configure Settings

**Section 1: Runtime Settings → Accounts → ComputerAccount**

*For Intune-Ready PPKG*:
```
- Leave ComputerAccount settings blank
- Intune handles Azure AD join automatically
```

*For On-Prem Domain Join*:
```
- Account: DOMAIN\ComputerJoinSvc
- AccountPassword: [Service account password]
- Domain: customer.local
- OrganizationalUnit: OU=Workstations,DC=customer,DC=local
```

---

**Section 2: Runtime Settings → Accounts → Users**

```
Configure Local Administrator Account:

UserName: TechAdmin
Password: [Secure password, 12+ characters]
UserGroup: Administrators
```

**Documentation**: Store password securely, share with 3rd party vendor via encrypted channel.

---

**Section 3: Runtime Settings → DesktopSettings**

```
LockScreen:
- LockScreenImage: Browse → Select company wallpaper (1920x1080)

SupportInformation:
- SupportAppURL: https://support.customer.com (or IT portal)
- SupportProvider: [Customer IT Team Name]
- SupportPhone: [IT Helpdesk Phone Number]
- SupportHours: [Business hours, e.g., 8am-6pm AEST Mon-Fri]
```

---

**Section 4: Runtime Settings → Time**

```
TimeZone: AUS Eastern Standard Time
(Or appropriate time zone for customer location)
```

---

**Section 5: Runtime Settings → Certificates → ClientCertificates** (Optional)

*Only if customer has internal PKI*:

```
For each certificate (Root CA, Intermediate CA):
1. Click Add
2. CertificateName: Customer_RootCA
3. CertificatePath: Browse → Select .cer file
4. CertificateStore: Root (for Root CA) or CA (for Intermediate)
5. Repeat for each certificate
```

---

**Section 6: Runtime Settings → Connectivity → WLANSetting → WLAN** (Optional)

*Only if customer requires pre-configured Wi-Fi*:

```
For each Wi-Fi network:
1. Click Add → Enter SSID name
2. ConnectionType: ESS (Infrastructure)
3. AutoConnect: True
4. SecurityType:
   - WPA2-Personal → Passphrase: [Wi-Fi password]
   - WPA2-Enterprise → EAPType, ServerValidation, etc.
5. Hidden: False (unless hidden SSID)
```

---

**Section 7: Runtime Settings → Provisioning → BulkEnrollment**

**THIS IS THE CRITICAL SETTING FOR INTUNE ENROLLMENT**:

```
BulkEnrollmentToken: [Paste token from Step 1]

This token enables automatic Intune enrollment on first boot.
```

---

#### Step 4: Build PPKG

```
1. Click Export → Provisioning package
2. Owner: IT Admin (or your MSP name)
3. Package version:
   - Major: 1
   - Minor: 0
   - Build: [Leave default]
4. Security:
   - Encrypt package: No (not supported by 3rd party vendor)
   - Sign package: No (unless you have code signing cert)
5. Select where to save: Choose folder
6. Click Next → Build

Output:
- CustomerName_PPKG_v1.0_20251011.ppkg
- File size: Typically 2-10 MB (depending on certificates, images)
```

---

#### Step 5: Test PPKG (CRITICAL)

**NEVER send untested PPKG to 3rd party vendor.**

**Test Process**:
```
1. Prepare test device:
   - Windows 11 Pro VM or physical device
   - Clean Windows install (fresh OOBE)

2. Apply PPKG:
   - Copy .ppkg to USB drive
   - Boot device → OOBE
   - At first OOBE screen, press Ctrl+Shift+F3 (skip to Audit Mode)
     OR complete OOBE and double-click PPKG file

3. Verify settings applied:
   - Check wallpaper changed (company branding)
   - Check local admin account created:
     lusrmgr.msc → Users → TechAdmin exists
   - Check certificates installed (if applicable):
     certmgr.msc → Trusted Root → Find customer CA cert
   - Check time zone: Settings → Time & Language

4. Test Intune enrollment:
   - Reboot device
   - Complete OOBE with test user account (or your own)
   - Sign in with customer Azure AD credentials
   - Verify Intune enrollment:
     Settings → Accounts → Access work or school
     Should show: Connected to [Customer] Azure AD
   - Wait 5-10 minutes
   - Verify Company Portal installed
   - Check Intune policies applied

5. Document test results:
   - ✅ PPKG applied successfully
   - ✅ Intune enrollment completed
   - ✅ Company Portal installed
   - ✅ [X] apps deployed
   - ❌ [Any issues discovered]
```

**If test fails**: Debug, fix PPKG, rebuild, re-test. Do NOT send to vendor until 100% working.

---

#### Step 6: Package for 3rd Party Vendor

**Create Delivery Package**:
```
Folder: CustomerName_PPKG_Delivery_v1.0_20251011/
├── CustomerName_PPKG_v1.0_20251011.ppkg (the actual package)
├── README.txt (application instructions)
├── Verification_Checklist.pdf (QA steps for vendor)
└── Contact_Info.txt (your contact for issues)
```

**README.txt Template**:
```
PPKG Application Instructions - [Customer Name]
================================================

PPKG File: CustomerName_PPKG_v1.0_20251011.ppkg
Valid Until: [Token Expiry Date]
Last Updated: 2025-10-11

APPLICATION PROCESS:
1. Apply Windows 11 Pro clean image (latest version)
2. Boot device → OOBE (Out-of-Box Experience)
3. At first screen, insert USB drive with PPKG
4. Double-click PPKG file → Click "Yes, add it"
5. Device will reboot
6. Verify company wallpaper applied (attached screenshot)
7. Complete post-imaging QA checklist
8. Package and ship device

VERIFICATION CHECKLIST:
□ Company wallpaper/lock screen visible
□ Device name follows customer naming convention (if applicable)
□ No error messages during PPKG application
□ Windows version: 22H2 or newer
□ Device boots to OOBE screen (not logged in)

TROUBLESHOOTING:
- PPKG won't apply → Ensure Windows 11 Pro (not Home)
- Error message → Screenshot and email to [your email]
- Wallpaper not changed → PPKG may not have applied, retry

CONTACT:
Technical Issues: [Your Name] - [Email] - [Phone]
Escalation: [Manager] - [Email]

IMPORTANT:
- This PPKG expires on [Date] - request updated PPKG before expiry
- Do NOT apply this PPKG to non-customer devices
- Store PPKG securely (contains customer credentials)
```

---

### PPKG Versioning and Maintenance

#### Naming Convention

```
Format: CustomerName_PPKG_v[Major].[Minor]_[YYYYMMDD].ppkg

Examples:
- ABCCorp_PPKG_v1.0_20251011.ppkg (initial)
- ABCCorp_PPKG_v1.1_20260108.ppkg (token refresh, minor update)
- ABCCorp_PPKG_v2.0_20260410.ppkg (configuration change, major update)

Version Increment Rules:
- Major (v2.0): Configuration change (new certificates, new settings)
- Minor (v1.1): Token refresh only (no other changes)
```

---

#### Token Expiry Management

**The #1 Operational Issue with PPKGs**: Expired tokens = devices won't enroll in Intune.

**Token Lifecycle**:
```
Day 0: Token created (valid for 180 days)
Day 165: Calendar reminder (15 days before expiry)
Day 170: Regenerate token + rebuild PPKG
Day 175: Test new PPKG
Day 176: Send new PPKG to 3rd party vendor
Day 180: Old token expires (old PPKG no longer works)
```

**Tracking System Required**:

Create spreadsheet: `PPKG_Token_Tracking.xlsx`

| Customer | PPKG Version | Token Created | Token Expiry | Status | Renewal Due | Next Action |
|----------|-------------|---------------|--------------|--------|-------------|-------------|
| ABC Corp | v1.0 | 2025-10-11 | 2026-04-09 | Active | 2026-03-25 | Monitor |
| XYZ Ltd | v1.1 | 2025-09-15 | 2026-03-13 | Active | 2026-02-26 | Renew soon |
| DEF Inc | v1.0 | 2025-08-01 | 2026-01-28 | **EXPIRED** | **OVERDUE** | **URGENT** |

**Automation Opportunity**:
```python
# Pseudo-code for token expiry checker
for customer in customers:
    days_until_expiry = (customer.token_expiry - today).days

    if days_until_expiry < 0:
        alert("CRITICAL: Token expired for " + customer.name)
    elif days_until_expiry < 15:
        alert("URGENT: Renew token for " + customer.name)
    elif days_until_expiry < 30:
        alert("WARNING: Token expires soon for " + customer.name)
```

---

#### Update Process

**When to Update PPKG**:
```
Trigger                          | Update Type | Timeline
---------------------------------|-------------|----------
Token expires in <15 days        | Minor (v1.1) | Immediate
Customer requests new cert       | Major (v2.0) | 1-2 weeks
Customer changes company logo    | Major (v2.0) | 1-2 weeks
Customer adds new Wi-Fi network  | Major (v2.0) | 1-2 weeks
Windows 11 version change        | Test only   | Validate PPKG works
```

**Update Workflow**:
```
1. Open original PPKG project in Windows Configuration Designer
2. Make changes (update token, add cert, etc.)
3. Increment version number
4. Build new PPKG
5. Test new PPKG (full test cycle)
6. Document changes in version notes
7. Send to 3rd party vendor with change summary
8. Archive old PPKG version (retain for 30 days)
```

---

## 3rd Party Vendor Requirements

### Technical Requirements

**Workstation Specifications**:
```
OS: Windows 11 Pro (build 22H2 or newer)
RAM: 8GB minimum
Storage: 500GB SSD
Network: Reliable internet (for Windows downloads)
USB Drives: Multiple (for PPKG distribution)
```

**Software Tools**:
```
- Windows 11 installation media (ISO)
- Rufus or similar tool (create bootable USB)
- PPKG files (from MSP)
- QA checklist (verification steps)
```

---

### Process Documentation for Vendor

**Standard Operating Procedure**:

```
DEVICE PROVISIONING PROCESS - [Customer Name]
==============================================

1. PREPARE IMAGING MEDIA
   □ Download Windows 11 Pro ISO (latest)
   □ Create bootable USB with Rufus
   □ Copy customer PPKG to separate USB drive

2. IMAGE DEVICE
   □ Boot device from USB
   □ Install Windows 11 Pro (clean install)
   □ Select: Windows 11 Pro (NOT Home)
   □ Partition: Delete all, create new
   □ Wait for installation (15-30 minutes)

3. APPLY PPKG
   □ Device boots to OOBE
   □ Insert USB with PPKG
   □ Double-click PPKG file
   □ Click "Yes, add it"
   □ Wait for device to reboot (2-5 minutes)

4. VERIFY CONFIGURATION
   □ Company wallpaper/lock screen visible
   □ Device at OOBE screen (NOT logged in)
   □ No error messages
   □ Windows version: 22H2+ (Settings → System → About)

5. QUALITY ASSURANCE
   □ Run customer-specific QA checklist
   □ Photograph device showing wallpaper (QA evidence)
   □ Apply asset tag (if applicable)
   □ Package device with documentation

6. DOCUMENTATION
   □ Serial number recorded in manifest
   □ PPKG version documented
   □ Date provisioned: [Today's date]
   □ Technician name: [Your name]

7. SHIP DEVICE
   □ Package securely
   □ Include quick start guide (if applicable)
   □ Ship to customer address
   □ Update tracking system

TROUBLESHOOTING:
- PPKG won't apply → Contact MSP immediately
- Error during imaging → Retry with fresh ISO
- Device won't boot → Hardware issue, escalate

CONTACT:
MSP Technical: [Name] - [Email] - [Phone]
Emergency: [After-hours number]
```

---

### Quality Assurance Checklist

**Vendor QA Form** (complete for each device):

```
DEVICE QA CHECKLIST - [Customer Name]
=====================================

Device Information:
□ Serial Number: _______________________
□ Model: _______________________________
□ Asset Tag (if applicable): ___________

Imaging Verification:
□ Windows 11 Pro installed (NOT Home)
□ Windows version: 22H2 or newer
□ No partitions from previous OS
□ System boots without errors

PPKG Application:
□ PPKG version: v___.___ (from filename)
□ PPKG applied successfully (no errors)
□ Device rebooted after PPKG application
□ Company wallpaper visible
□ Company lock screen visible (press Windows+L to verify)

OOBE State:
□ Device at OOBE screen (language selection)
□ NOT logged in to any account
□ No user profiles created
□ No Windows updates installed (will happen post-enrollment)

Physical Inspection:
□ Device physically undamaged
□ All ports functional
□ Power adapter included
□ Packaging materials ready

Documentation:
□ Quick start guide included (if applicable)
□ Serial number recorded in manifest
□ Photo taken (showing wallpaper as proof)

Technician:
Name: _____________________________
Date: _____________________________
Signature: _________________________

PASS / FAIL: __________

If FAIL, describe issue:
__________________________________________
__________________________________________
```

---

## Troubleshooting Guide

### Common Issues and Resolutions

#### Issue 1: PPKG Won't Apply

**Symptom**: Double-clicking PPKG shows error or nothing happens.

**Causes**:
- Windows 11 Home edition (PPKG requires Pro/Enterprise)
- Corrupted PPKG file
- PPKG built for wrong Windows version
- User doesn't have admin rights (during OOBE, not an issue)

**Resolution**:
```
1. Verify Windows edition:
   Settings → System → About → Edition
   Must be: Windows 11 Pro or Enterprise

2. Re-download PPKG from source (may be corrupted)

3. Rebuild PPKG in Windows Configuration Designer

4. If still failing, apply PPKG during OOBE instead of post-OOBE:
   - At OOBE first screen, press Windows+U (Ease of Access)
   - Browse to PPKG file
   - Apply from there
```

---

#### Issue 2: Company Branding Doesn't Apply

**Symptom**: After PPKG application, wallpaper/lock screen unchanged.

**Causes**:
- PPKG didn't actually apply (see Issue 1)
- Image files too large (>500KB can cause issues)
- Image file format unsupported (must be PNG or JPG)
- Path in PPKG incorrect

**Resolution**:
```
1. Verify PPKG applied:
   - Check if local admin account exists: lusrmgr.msc
   - If TechAdmin account doesn't exist → PPKG didn't apply

2. Rebuild PPKG with smaller image files:
   - Compress images to <500KB
   - Use PNG or JPG format
   - Resolution: 1920x1080

3. Manually verify image files in PPKG:
   - Open PPKG in Windows Configuration Designer
   - Check DesktopSettings → LockScreenImage path
```

---

#### Issue 3: Intune Enrollment Fails

**Symptom**: User completes OOBE, but Company Portal never installs or device doesn't show in Intune.

**Causes**:
- Bulk enrollment token expired (>180 days old)
- Token not included in PPKG
- User signed in with personal Microsoft account (not work account)
- Network connectivity issues (no internet access)
- Customer tenant requires MFA (blocks auto-enrollment)

**Resolution**:
```
1. Verify token validity:
   - Check PPKG creation date
   - If >180 days old → Regenerate token, rebuild PPKG

2. Verify user signed in with work account:
   - Settings → Accounts → Access work or school
   - Should show: user@customer.com
   - If personal account (user@outlook.com) → Wrong account used

3. Verify internet connectivity:
   - Open browser → Navigate to https://portal.office.com
   - If fails → Network issue

4. Manual enrollment (if auto-enrollment failed):
   - Settings → Accounts → Access work or school
   - Click "Connect"
   - Enter work email → Follow prompts
   - Company Portal will install

5. Check Intune admin center:
   - Navigate to Devices → All devices
   - Search for device by serial number
   - If not present → Enrollment definitely failed
```

---

#### Issue 4: Domain Join Fails (On-Prem AD Customers)

**Symptom**: Device doesn't join domain, stays in workgroup mode.

**Causes**:
- Device can't reach domain controller (network issue)
- Domain join account credentials expired
- Domain join account lacks permissions
- Wrong domain name in PPKG
- Target OU doesn't exist

**Resolution**:
```
1. Verify network connectivity to domain:
   - Open Command Prompt
   - ping customer.local
   - If fails → Network/DNS issue

2. Verify domain join account:
   - Contact customer IT
   - Confirm account is enabled and password correct
   - Confirm account has "Create Computer Objects" permission on target OU

3. Manual domain join (if auto-join failed):
   - Settings → System → About → Rename this PC (advanced)
   - Click "Change" → Select "Domain"
   - Enter domain name → Provide credentials
   - Reboot

4. Check Event Viewer for errors:
   - Event Viewer → Windows Logs → System
   - Filter: Source = "NetJoin"
   - Look for error codes (common: 5, 1355, 1326)
```

---

#### Issue 5: Local Admin Account Not Created

**Symptom**: TechAdmin account doesn't exist after PPKG application.

**Causes**:
- PPKG didn't apply (see Issue 1)
- Account settings incorrect in PPKG
- Windows Home edition (doesn't support local account creation via PPKG)

**Resolution**:
```
1. Verify account manually:
   - lusrmgr.msc (Local Users and Groups)
   - Check Users → TechAdmin should exist
   - If missing → PPKG didn't apply

2. Manually create account (temporary workaround):
   - Settings → Accounts → Family & other users
   - Add account → "I don't have this person's sign-in information"
   - Add user without Microsoft account
   - Username: TechAdmin
   - Password: [Use documented password]
   - Change account type to Administrator

3. Rebuild PPKG with correct account settings
```

---

## Security Considerations

### Credential Management

**PPKG Contains Sensitive Information**:
```
High Risk:
- Intune bulk enrollment token (grants device access to tenant)
- Domain join account credentials (can join any device to domain)
- Wi-Fi passwords (network access)

Medium Risk:
- Local administrator password (device access)

Low Risk:
- Company branding, time zone, support info
```

**Security Best Practices**:

1. **Encrypt PPKG in Transit**:
   - Use encrypted file sharing (OneDrive with encryption, BitLocker USB)
   - Never email PPKG files
   - Use secure file transfer (SFTP, HTTPS upload portal)

2. **Access Control**:
   - Limit PPKG access to authorized 3rd party technicians only
   - Require NDA with 3rd party vendor
   - Audit who has access to PPKG files

3. **Credential Rotation**:
   - Domain join account: Change password every 180 days
   - Local admin account: Disable via Intune policy after 30 days
   - Bulk enrollment tokens: Regenerate every 180 days (forced by Microsoft)

4. **PPKG Storage**:
   - Store master PPKG files in secure location (not on public share)
   - Version control (track who accessed/modified)
   - Delete old PPKG versions after 30 days

5. **Local Admin Account Lifecycle**:
   ```
   Day 0: Device provisioned with TechAdmin account
   Day 1-30: 3rd party/customer IT can use account for troubleshooting
   Day 30: Intune policy disables TechAdmin account (automated)
   Day 90: Intune policy deletes TechAdmin account (automated)
   ```

   **Intune Policy Configuration**:
   ```
   Policy Name: "Disable 3rd Party Provisioning Admin Account"
   Type: Configuration Profile (Windows 10+)
   Settings: Local Users and Groups
   Action: Disable account named "TechAdmin"
   Assignment: All devices
   Schedule: 30 days after enrollment
   ```

---

### Compliance and Auditing

**Track PPKG Usage**:
```
Audit Log Fields:
- Customer name
- PPKG version
- Date created
- Created by (technician name)
- Date sent to 3rd party
- Number of devices provisioned
- Date PPKG expired/retired
- Incidents (if any)
```

**Regular Audits**:
```
Monthly:
- Review active PPKGs (ensure none expired)
- Check token expiry dates (flag renewals needed)
- Verify 3rd party vendor compliance (QA checklist completion)

Quarterly:
- Audit credential rotation (domain join accounts)
- Review local admin account lifecycle (verify disabled after 30 days)
- Validate PPKG storage security (who has access)

Annually:
- Review 3rd party vendor security controls
- Update PPKG process documentation
- Conduct security assessment of PPKG workflow
```

---

## Transition to Autopilot

### When to Deprecate PPKG

**Customer Readiness Checklist**:
```
□ Intune Maturity Level 3+ (Optimized)
□ Autopilot deployment profile configured
□ Device compliance policies enforced
□ Comprehensive app deployment catalog (Win32, LOB)
□ Windows Update for Business rings configured
□ IT team trained on Autopilot management
□ Device hardware IDs uploaded to Intune
□ Pilot group successfully provisioned via Autopilot
```

**When ALL boxes checked → Customer is Autopilot-ready**

---

### Migration Process

**Phase 1: Parallel Operation (Month 1)**
```
- Provision 80% of devices via PPKG (existing process)
- Provision 20% via Autopilot (pilot group)
- Monitor Autopilot success rate (target: >95%)
- Gather user feedback (Autopilot vs PPKG experience)
```

**Phase 2: Autopilot Primary (Month 2)**
```
- Provision 20% via PPKG (legacy/exception cases)
- Provision 80% via Autopilot (standard process)
- Document lessons learned
- Update 3rd party vendor procedures (hardware ID upload only)
```

**Phase 3: PPKG Deprecation (Month 3)**
```
- Provision 100% via Autopilot
- Archive PPKG files (retain for 90 days)
- Delete bulk enrollment tokens from Intune
- Notify 3rd party vendor: PPKG no longer used
- Update customer documentation (Autopilot-only)
```

---

### Autopilot Benefits Over PPKG

| Aspect | PPKG | Autopilot | Winner |
|--------|------|-----------|--------|
| **3rd Party Effort** | 15-20 min per device (apply PPKG) | 2 min per device (upload hardware ID) | Autopilot |
| **User Experience** | 15-30 min setup after unbox | 5-10 min setup (White Glove), 30-45 min (Standard) | Autopilot (White Glove) |
| **Token Management** | Renew every 180 days (manual) | No tokens (automatic) | Autopilot |
| **Configuration Drift** | PPKG version control issues | Always latest Intune policies | Autopilot |
| **Scalability** | Manual PPKG per customer | Fully automated | Autopilot |
| **Troubleshooting** | PPKG application failures | Rare (mostly network-related) | Autopilot |
| **Cost** | 3rd party labor ($15-20/device) | Minimal ($2-5/device) | Autopilot |

**ROI Break-Even**: Autopilot setup investment (8-16 hours) pays off after 50-100 devices provisioned.

---

## Appendix

### A. PPKG Configuration Checklist

**Before Building PPKG**:
```
Customer Information:
□ Customer name: _______________________
□ Intune/Azure AD tenant ID: ___________
□ Contact person: _______________________
□ Contact email: ________________________

Files Collected:
□ Company logo (PNG, <500KB)
□ Company wallpaper (1920x1080 JPG/PNG)
□ Root CA certificate (.cer) - if applicable
□ Intermediate CA certificate (.cer) - if applicable

Credentials Collected:
□ Intune bulk enrollment token (copied)
□ Token expiry date: _____________________
□ Local admin password: _________________ (documented securely)
□ Domain join credentials - if applicable

Settings Defined:
□ Time zone: ____________________________
□ Support phone: _________________________
□ Support email: __________________________
□ Support URL: ___________________________
□ Wi-Fi SSIDs (if applicable): ____________

Quality Checks:
□ PPKG tested on clean Windows 11 Pro device
□ Company branding verified (wallpaper, lock screen)
□ Local admin account created and functional
□ Intune enrollment successful (Company Portal installed)
□ Test took <30 minutes end-to-end

Packaging:
□ PPKG file: CustomerName_PPKG_v1.0_YYYYMMDD.ppkg
□ README.txt created
□ Verification checklist created
□ Contact info provided
□ Sent to 3rd party vendor via secure channel

Documentation:
□ PPKG version logged in tracking spreadsheet
□ Token expiry reminder set (2 weeks before expiry)
□ Test results documented
□ Customer notified (PPKG ready for production)
```

---

### B. Bulk Enrollment Token Generation (Detailed)

**Step-by-Step Screenshots** (text descriptions):

```
Screenshot 1: Intune Admin Center Home
- Navigate to: https://intune.microsoft.com
- Sign in with Intune Administrator account

Screenshot 2: Device Enrollment Menu
- Left navigation → Devices
- Click "Enroll devices"
- Click "Windows enrollment"

Screenshot 3: Bulk Enrollment
- Click "Bulk enrollment" (under Windows enrollment)
- Shows existing bulk enrollment profiles (if any)

Screenshot 4: Add Bulk Enrollment Profile
- Click "+ Add" button
- Dialog opens: "Create profile"

Screenshot 5: Profile Configuration
- Profile name: "3rd Party Provisioning - Oct 2025"
- Description: "Bulk enrollment for 3rd party vendor device provisioning"
- Automatically enroll devices: Yes
- Click "Create"

Screenshot 6: Download Provisioning Package
- Profile created successfully
- Click profile name → "Download provisioning package"
- Saves: BulkEnrollment_[date].ppkg

Screenshot 7: Extract Token
- Open downloaded .ppkg in Windows Configuration Designer
- Navigate to: Runtime settings → Provisioning → BulkEnrollment
- Copy BulkEnrollmentToken value (long Base64 string)

Screenshot 8: Token Documentation
- Paste token into secure note
- Document:
  - Customer name
  - Token created date
  - Token expiry date (created date + 180 days)
  - Profile name
- Set calendar reminder for renewal
```

---

### C. Windows Configuration Designer Quick Reference

**Common Settings Paths**:

```
Account Configuration:
├── Runtime Settings
│   ├── Accounts
│   │   ├── ComputerAccount (domain join)
│   │   └── Users (local accounts)

Branding:
├── Runtime Settings
│   ├── DesktopSettings
│   │   ├── LockScreenImage
│   │   └── SupportInformation

Time & Region:
├── Runtime Settings
│   ├── Time
│   │   └── TimeZone

Certificates:
├── Runtime Settings
│   ├── Certificates
│   │   └── ClientCertificates

Network:
├── Runtime Settings
│   ├── Connectivity
│   │   └── WLANSetting
│   │       └── WLAN (Wi-Fi profiles)

Intune Enrollment:
├── Runtime Settings
│   ├── Provisioning
│   │   └── BulkEnrollment
│   │       └── BulkEnrollmentToken
```

**Keyboard Shortcuts**:
```
Ctrl+S: Save project
Ctrl+E: Export provisioning package
Ctrl+F: Search settings
F5: Refresh
```

---

### D. Contact Information Template

**Include in PPKG Delivery Package**:

```
3RD PARTY PROVISIONING - CONTACT INFORMATION
============================================

Customer: [Customer Name]
PPKG Version: v1.0
Valid Until: [Token Expiry Date]

PRIMARY CONTACT:
Name: [Your Name]
Role: Endpoint Engineer / MSP Technician
Email: [your.email@msp.com]
Phone: [+61 X XXXX XXXX]
Hours: [8am-6pm AEST Mon-Fri]

ESCALATION CONTACT:
Name: [Manager Name]
Email: [manager.email@msp.com]
Phone: [+61 X XXXX XXXX]

AFTER-HOURS EMERGENCY:
Phone: [Emergency number]
(For critical provisioning issues only)

CUSTOMER IT CONTACT:
Name: [Customer IT Manager]
Email: [customer.it@customer.com]
Phone: [Customer IT Helpdesk]
(For end-user device issues after delivery)

TECHNICAL SUPPORT:
- PPKG won't apply: Email screenshot + device serial to [your.email]
- Device won't boot: Hardware issue, escalate to your hardware support
- User can't sign in: Customer IT issue, contact customer helpdesk
- Intune enrollment fails: Email device serial + error message to [your.email]

SLA:
- Response time: 4 business hours
- Resolution time: 1 business day
- Critical issues: 1 hour response

DOCUMENTATION:
- PPKG User Guide: [URL or SharePoint link]
- Troubleshooting FAQ: [URL]
- Video Tutorial: [URL]
```

---

### E. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | Principal Endpoint Engineer | Initial PPKG implementation guide |

---

## Related Documentation

- **3rd Party Laptop Provisioning Strategy**: High-level strategy document
- **Intune Configuration Standards**: Customer Intune setup requirements
- **Autopilot Deployment Guide**: Long-term target state documentation
- **Windows 11 SOE Standards**: Base image specifications

---

**Questions or Feedback**: Contact Endpoint Engineering Team
