# 3rd Party Laptop Provisioning Strategy - Interim Solution

**Document Owner**: Endpoint Engineering Team
**Last Updated**: 2025-10-11
**Status**: Strategic Planning
**Confluence Space**: Orro

---

## Executive Summary

This document outlines the interim laptop provisioning strategy for customers using a 3rd party provisioner while Intune environments mature to support full Autopilot deployment. The strategy addresses three customer segments with different infrastructure maturity levels and provides clear decision criteria, technical approaches, and business models for each.

**Key Finding**: 40% of customers lack Intune, requiring alternate provisioning approaches or Intune bootstrap services to ensure secure, manageable device deployment.

---

## Business Context

### Current State
- **3rd party provisioning**: External vendor will provision and reload laptops on their premises
- **Customer base composition**:
  - 60% have Intune (immature, no Autopilot configured)
  - 25% have Entra ID only (no device management)
  - 15% have on-premises AD only (traditional infrastructure)
- **Target state**: All customers using Autopilot (12-18 month journey)

### Challenge
Need interim provisioning solution that:
- Works at 3rd party premises (no direct customer network access)
- Accommodates customers without mature Intune
- Provides secure, manageable devices
- Creates transition path to Autopilot as customers mature

---

## Customer Segmentation & Strategies

### Segment A: Immature Intune (60% of customers)

**Infrastructure**: Entra ID/AD + Intune license (basic configuration)

**Provisioning Strategy**: Windows Provisioning Package (PPKG) with Intune Bulk Enrollment Token

#### Implementation Approach

**PPKG Configuration**:
- Intune bulk enrollment token (180-day validity)
- Local administrator account (3rd party access)
- Company branding (lock screen, wallpaper, support info)
- Time zone/region settings
- Wi-Fi profiles (optional)
- Root/Intermediate CA certificates (if customer has PKI)

**3rd Party Process**:
1. Apply Windows 11 base image (clean install)
2. Apply customer-specific PPKG during/after OOBE
3. Verify PPKG applied successfully
4. Ship device to end user

**End User Experience**:
1. Unbox device → Complete OOBE
2. Sign in with corporate credentials
3. Intune enrollment triggers automatically (via PPKG token)
4. Company Portal installs → Apps/policies apply
5. 15-30 minutes → Device ready

**Effort**: 1-4 hours per customer (initial PPKG creation), 30-60 min quarterly updates

**Success Rate**: 90-95%

#### PPKG Creation Timeline

| Customer Complexity | First PPKG | Subsequent Updates | Update Frequency |
|---------------------|------------|-------------------|------------------|
| Basic (token + branding) | 2-4 hours | 30-60 min | Quarterly (token expiry) |
| Standard (+ certs + Wi-Fi) | 2-3 hours | 45-60 min | Quarterly |
| Managed (minimal config) | 1-2 hours | 15-30 min | Semi-annually |

#### Critical Considerations

**1. Token Expiry Management**
- Bulk enrollment tokens expire after 180 days
- Requires tracking system with calendar reminders
- PPKG must be rebuilt and redistributed before expiry
- Recommend automation: Script to check token expiry across all customers

**2. PPKG Versioning**
```
Naming Convention:
CustomerName_PPKG_v1.0_20251011.ppkg (initial)
CustomerName_PPKG_v1.1_20260108.ppkg (token refresh)
CustomerName_PPKG_v2.0_20260410.ppkg (configuration change)

Version Control:
- SharePoint/secure file share with version history
- 3rd party downloads latest version only
- Archive old versions after 30 days (force update)
```

**3. BitLocker Timing**
- **DO NOT enable BitLocker in PPKG**
- Let Intune policy enable BitLocker AFTER enrollment
- Ensures recovery key escrowed to Azure AD (prevents data loss)

**4. Windows Edition Compatibility**
- Standardize on Windows 11 Pro (required for Intune management)
- PPKGs built for Pro may not work on Home edition
- Avoid edition-specific features in PPKG

**5. Customer Tenant Access**
- Requires Intune Administrator or Global Administrator role in customer tenant
- Needed to: Generate bulk tokens, test enrollment, verify device enrollment
- Alternative: Customer creates service account with Intune Device Enrollment Manager role

---

### Segment B: Entra ID Only, No Intune (25% of customers)

**Infrastructure**: Azure AD (Entra ID), no device management platform

**Critical Issue**: No centralized device management means:
- ❌ No app deployment (users install manually)
- ❌ No BitLocker enforcement (data loss risk)
- ❌ No compliance policies (can't restrict unmanaged device access)
- ❌ No remote wipe capability
- ❌ No Windows Update control
- ❌ No device inventory visibility

#### Option 1: Azure AD Join PPKG (No Management) ⚠️ HIGH RISK

**PPKG Configuration**:
- Azure AD join bulk token (180-day expiry)
- Local administrator account
- Company branding
- Time zone/region settings

**Reality Check**: This creates **unmanaged devices** with only SSO to M365 apps. Acceptable ONLY if:
- Customer has <20 devices
- Low security requirements (no compliance mandates)
- Users are tech-savvy (self-install apps)
- **Customer provides written acceptance of risks**

**Effort**: 1-2 hours per customer

**Success Rate**: 85-90% (technical), but high operational/security risk

---

#### Option 2: Bootstrap Intune Quick Start ✅ RECOMMENDED

**Business Case**: If customer has Microsoft 365 E3/E5/Business Premium licensing, **they already have Intune** - they're just not using it.

**Value Proposition**:
- 6-8 hour one-time setup provides professional device management
- Eliminates security/operational risks of unmanaged devices
- Creates foundation for future growth (app deployment, compliance, conditional access)

**Implementation**: Minimal Viable Intune Tenant Setup

```
Phase 1: Core Configuration (4 hours)
✅ Enable Intune in M365 Admin Center
✅ Configure automatic enrollment (Azure AD + Intune)
✅ Create Autopilot deployment profile (basic, user-driven mode)
✅ Create device compliance policy (password, BitLocker, antivirus, OS version)
✅ Create conditional access policy (require compliant device for M365 access)
✅ Generate bulk enrollment token for PPKG

Phase 2: App Deployment (2 hours)
✅ Deploy Company Portal (automatic)
✅ Deploy Microsoft 365 Apps (automatic)
✅ Deploy common apps per customer (Chrome, Adobe, Zoom)
✅ Configure Enrollment Status Page (ESP) for app installation during provisioning

Phase 3: Testing & Documentation (2 hours)
✅ Test device enrollment (pilot device)
✅ Verify compliance policy enforcement
✅ Verify app deployment success
✅ Document runbook for customer IT
✅ Knowledge transfer call (30 min)

Total Investment: 6-8 hours
```

**Deliverables**:
- Functional Intune tenant (Maturity Level 1-2)
- Bulk enrollment token for PPKG generation
- 3-5 pilot devices enrolled and tested
- Customer runbook (ongoing self-management)
- Knowledge transfer completed

**Customer Value (Annual)**:
- Avoided costs: $3,400+ (app deployment automation, reduced break-fix)
- Risk mitigation: Avoid potential breach ($50,000+ conservative)
- Gained capabilities: Remote management, compliance visibility, BitLocker enforcement, conditional access

**Ongoing Maintenance**: ~2 hours/quarter (token refresh, policy updates)

---

#### Pricing Model Options for No-Intune Customers

**Option A: Bundled Setup Fee**
```
Intune Quick Start: $[6-8 hrs × rate] one-time
Includes: Minimal Intune setup, first 10 enrollments, bulk token, runbook

Ongoing: Customer self-manages OR managed service add-on
```

**Option B: Per-Device Markup**
```
Intune-ready customers: $X per device
No-Intune customers: $X + $Y per device (bootstrap amortized)

Example: $50/device vs $75/device
($25 markup covers Intune bootstrap over 10-device order)
```

**Option C: Mandatory Managed Service** ✅ RECOMMENDED
```
No-Intune customers must sign managed service:
- Managed Intune Service: $5-10/device/month
- Includes: Setup, ongoing management, app deployment, support

Rationale: Building infrastructure requires ongoing management
           Don't create orphaned infrastructure
           Sustainable business model
```

---

### Segment C: On-Premises AD, No Intune (15% of customers)

**Infrastructure**: On-premises Active Directory, typically hybrid environments with some Azure AD sync

**Traditional Management**: Group Policy, WSUS/manual updates, file shares for apps, login scripts

#### Option 1: Domain Join PPKG (Traditional Management) 🟡 LEGACY

**PPKG Configuration**:
- Domain join credentials (requires delegated service account)
- Target OU path
- Local administrator account
- Company branding
- Wi-Fi profiles (for domain connectivity)
- Root/Intermediate CA certificates

**Critical Requirements**:

1. **Domain Join Service Account** (Customer must provide):
```
Account Requirements:
✅ Delegated permissions: Create computer objects in target OU
✅ Delegated permissions: Reset computer passwords
✅ Password never expires (or long expiry)
✅ Account is enabled
✅ Not requiring interactive login

Setup (Customer AD Admin):
1. Create service account (e.g., DOMAIN\ComputerJoinSvc)
2. Delegate "Create Computer Objects" permission on target OU
3. Provide credentials to MSP (secure transfer)
```

2. **Network Connectivity to Domain Controller**:
```
Device must reach DC for join to complete:
✅ Option A: User provisions at office (corporate network)
✅ Option B: User on VPN (domain traffic routed)
❌ Option C: User at home, no VPN (join fails)

Required Ports (Device → DC):
- Port 53 (DNS)
- Port 88 (Kerberos)
- Port 389 (LDAP)
- Port 445 (SMB/CIFS)
- Port 464 (Kerberos password change)
```

**How "Offline" Domain Join Works**:
1. 3rd party applies PPKG (device NOT on customer network)
2. PPKG caches domain join credentials in registry (encrypted)
3. Domain join task scheduled for "next network connection"
4. Device ships to end user (still in workgroup mode)
5. User boots device, connects to corporate network
6. Windows detects DC reachable → Executes domain join → Reboots
7. User sees domain login screen

**Success Rate**: 60-75% on first boot without IT intervention

**Common Failures**:
- User at home, no VPN (50% of failures)
- VPN requires domain credentials (catch-22 - 25%)
- Firewall blocks required ports (15%)
- Domain join account expired/disabled (5%)

**Effort**: 2-3 hours per customer (initial), annually updates (unless certs expire)

---

#### Option 2: PPKG Branding Only + Customer Domain Join ✅ RECOMMENDED

**Rationale**: Skip PPKG domain join entirely to avoid credential exposure and failure scenarios

**3rd Party Process**:
1. Apply minimal PPKG:
   - ✅ Company branding (wallpaper, support info)
   - ✅ Local admin account (TechAdmin)
   - ✅ Wi-Fi profiles (if applicable)
   - ❌ NO domain join credentials
2. Include printed instructions: "Contact IT at [number] to complete domain join"
3. Ship to **customer IT department** (not end user)

**Customer IT Process**:
1. Receive devices from 3rd party
2. Domain join each device (manual or scripted)
3. Verify Group Policy applied
4. Distribute to end users

**Pros**:
- ✅ 100% domain join success rate
- ✅ Customer controls domain join process
- ✅ Avoids credential management burden
- ✅ Clear handoff point (3rd party → customer IT)
- ✅ No credential exposure risk

**Cons**:
- ⚠️ Customer IT must touch every device (labor cost)
- ⚠️ Delays device distribution to end users

**Effort**: 1-2 hours per customer (minimal PPKG)

---

#### Option 3: Bootstrap Intune + Hybrid Join ✅ RECOMMENDED (FUTURE-PROOF)

**Best Long-Term Solution**: Transition customer from on-prem AD to hybrid Azure AD + Intune management

**Implementation**: 8-12 hour engagement
- Phase 1: Configure Azure AD Connect (if not already synced)
- Phase 2: Enable Hybrid Azure AD Join
- Phase 3: Configure Intune auto-enrollment
- Phase 4: Test hybrid join + Intune enrollment
- Phase 5: Generate PPKG with Intune token

**Result**: Device hybrid-joins to domain AND enrolls in Intune simultaneously

**Customer Value**:
- Keeps existing Group Policy management (backwards compatibility)
- Adds modern cloud management (Intune policies)
- Cloud-native app deployment
- Conditional access capabilities
- Smooth transition to cloud-first management

**Effort**: 8-12 hours setup (one-time), then standard PPKG process

---

## Decision Matrix: Provisioning Approach Selection

```
Customer Assessment:
        |
        ├─ Has Intune? ─── YES ─── Maturity Level?
        |                          |
        |                          ├─ Basic (license + minimal config)
        |                          |   └─> PPKG with Intune Token (2-4 hrs)
        |                          |
        |                          ├─ Managed (compliance policies, apps)
        |                          |   └─> PPKG with Intune Token (1-2 hrs)
        |                          |
        |                          └─ Optimized (Autopilot profile exists)
        |                              └─> Autopilot White Glove (30 min)
        |
        └─ Has Intune? ─── NO ─── Infrastructure Type?
                                  |
                                  ├─ Entra ID Only
                                  |   └─> Options:
                                  |       A) Azure AD Join PPKG (NO MGMT) ⚠️ High Risk
                                  |       B) Bootstrap Intune Quick Start ✅ RECOMMENDED
                                  |          (6-8 hrs + PPKG with Intune token)
                                  |
                                  └─ On-Prem AD
                                      └─> Options:
                                          A) Domain Join PPKG 🟡 Legacy (60-75% success)
                                          B) PPKG Branding + Customer Domain Join ✅ RECOMMENDED
                                          C) Bootstrap Intune + Hybrid Join ✅ FUTURE-PROOF
                                             (8-12 hrs + PPKG with Intune token)
```

---

## Standard Operating Procedure

### Step 1: Customer Qualification (Before Quoting)

**Discovery Questions**:
```
1. Identity Infrastructure:
   ☐ Entra ID (Azure AD)
   ☐ On-Prem AD
   ☐ Hybrid (AD + Entra ID synced)

2. Device Management:
   ☐ Has Intune configured (even basic)
   ☐ No Intune but has M365 licensing (E3/E5/Business Premium)
   ☐ No Intune licensing

3. Current Management Approach:
   ☐ Intune (basic/managed/optimized)
   ☐ Group Policy (on-prem AD)
   ☐ No central management

4. Device Volume:
   ☐ Current request: [X] devices
   ☐ Annual volume: [Y] devices
   ☐ Total fleet size: [Z] devices

5. Security Requirements:
   ☐ Compliance mandates (industry regulations)
   ☐ BitLocker encryption required
   ☐ Conditional access for M365 data
   ☐ Internal PKI/certificates
```

---

### Step 2: Provisioning Approach Recommendation

**Standard Customer Conversation**:
```
"We can provision devices three ways:

Option 1: Basic Provisioning (No Management)
- Devices join [Azure AD / Domain]
- No centralized management, security, or app deployment
- Price: $X/device
- Risk: High (unmanaged devices)

Option 2: Professional Provisioning with Intune ✅ RECOMMENDED
- One-time Intune setup (foundation for future)
- Secure device management
- Centralized app deployment
- BitLocker enforcement
- Remote support capability
- Price: $Y setup + $X/device
- Risk: Low (managed, secure)

Option 3: Managed Service (Ongoing Partnership)
- Intune setup included
- Ongoing device management
- App deployment as needed
- Monthly support
- Price: $Z/device/month
- Risk: Minimal (proactive management)

Most customers in your situation choose Option 2 or 3.
Which makes sense for you?"
```

---

### Step 3: PPKG Creation & Management

**PPKG Creation Matrix**:

| Customer Type | PPKG Content | Creation Time | Update Frequency | Success Rate |
|---------------|--------------|---------------|------------------|--------------|
| **Intune (Basic)** | Intune token + branding + local admin | 2-4 hours | Quarterly | 90-95% |
| **Intune (Managed)** | Intune token + branding + local admin + certs | 1-2 hours | Quarterly | 95%+ |
| **Entra-Only (No Mgmt)** | Azure AD token + branding + local admin | 1-2 hours | Quarterly | 85-90% |
| **On-Prem AD (Domain Join)** | Domain join + branding + local admin + certs | 2-3 hours | Annually | 60-75% |
| **On-Prem AD (Branding Only)** | Branding + local admin only | 1-2 hours | Annually | 100% |
| **Hybrid (Intune + AD)** | Hybrid join + Intune token + branding + certs | 2-4 hours | Quarterly | 90-95% |

**Master Template Approach** (Recommended):
```
Master PPKG Template (80% standardized):
✅ Local admin account (same username, unique password per customer)
✅ Time zone (Australia/Melbourne or user-selectable)
✅ Company branding (MSP branding + "Managed by [MSP]")
✅ Basic security settings (disable consumer features)

Customer-Specific Customization (20%):
🔧 Intune/Azure AD bulk enrollment token (must be unique)
🔧 Customer logo overlay (optional)
🔧 Wi-Fi profiles (if customer-specific)
🔧 Certificates (if customer has internal PKI)

Time Savings: First PPKG 2-4 hours → Subsequent customers 45-60 minutes
```

---

## Long-Term Transition Roadmap

### Intune Maturity Levels

**Level 1: Basic (Current State - Most Customers)**
- Intune licensing exists
- Basic device enrollment
- Minimal policies configured
- **Provisioning Solution**: PPKG with Intune token

**Level 2: Managed (3-6 months)**
- Autopilot profile configured (basic)
- Device compliance policies defined
- Conditional access enabled
- Application deployment started (Win32, LOB apps)
- **Provisioning Solution**: Autopilot White Glove (Pre-Provisioning) or PPKG

**Level 3: Optimized (6-12 months)**
- Full Autopilot deployment profiles
- Comprehensive app deployment catalog
- Windows Update for Business rings configured
- Compliance policies enforced
- Endpoint analytics enabled
- **Provisioning Solution**: Full Autopilot User-Driven (Target State)

**Level 4: Advanced (12-18 months)**
- Proactive remediation scripts
- Windows 11 feature updates automated
- Zero-touch provisioning end-to-end
- Autopilot for existing devices (reload scenarios)
- **Provisioning Solution**: Autopilot + Pre-Provisioning for VIPs

---

### Target State: Full Autopilot User-Driven Mode

**When Customers Reach Level 3+**:
```
3rd Party Process:
1. Upload device hardware IDs to customer Intune tenant
2. Ship device in factory state (no configuration)

End User Process:
1. Unbox → OOBE
2. Sign in with corporate credentials
3. Autopilot profile applies automatically (company branding, apps, policies)
4. 30-45 minutes → Fully configured device

Benefits:
✅ Zero 3rd party configuration (just hardware ID upload)
✅ User self-service provisioning
✅ Cloud-native, fully automated
✅ Consistent experience across all customers
✅ Scalable to any volume
```

---

## Risk Management

### Risk Disclosure for No-Management Provisioning

**Required for Customers Who Refuse Intune Setup**:

Document must include written acceptance of:
- ❌ No centralized app deployment (manual user installation)
- ❌ No BitLocker enforcement (data loss risk if device stolen)
- ❌ No compliance policies (can't restrict unmanaged device access to M365)
- ❌ No remote wipe capability (lost/stolen devices)
- ❌ No Windows Update control (vulnerable to unpatched security issues)
- ❌ No device inventory (no asset visibility)
- ❌ No conditional access enforcement (unmanaged devices access corporate data)
- ❌ Increased support costs (reactive break-fix vs proactive management)
- ❌ Compliance audit failures (can't demonstrate security controls)

**Customer must sign acknowledgment**: "I understand these risks and accept responsibility for security/operational consequences of unmanaged devices."

---

## Recommended Tools & Resources

### PPKG Creation
- **Windows Configuration Designer** (free from Microsoft)
- Download: https://learn.microsoft.com/en-us/windows/configuration/provisioning-packages/provisioning-install-icd

### Token Tracking
- **Token Expiry Tracker**: Spreadsheet tracking all customer tokens with 2-week expiry reminders
- Columns: Customer Name, Token Created Date, Token Expiry Date, PPKG Version, Renewal Status

### Version Control
- **SharePoint Document Library** with version history enabled
- Naming convention: `CustomerName_PPKG_v1.0_YYYYMMDD.ppkg`
- Retention: Keep last 2 versions only (force updates)

### Testing
- **Pilot Device**: Maintain 1-2 test devices per Windows edition (Pro/Enterprise)
- Test PPKG application before distributing to 3rd party
- Verify Intune enrollment completes successfully

---

## Success Metrics

### Provisioning Quality
- **PPKG Application Success Rate**: >95% (devices apply PPKG without errors)
- **Intune Enrollment Success Rate**: >90% (devices enroll within 24 hours)
- **Domain Join Success Rate**: >75% (for on-prem AD customers using PPKG domain join)
- **End User Setup Time**: <30 minutes from unbox to productivity

### Customer Satisfaction
- **3rd Party Provisioning Quality**: >95% defect-free rate
- **Customer IT Escalations**: <5% of devices require IT intervention
- **User Experience Score**: >4/5 (provisioning ease)

### Business Metrics
- **Intune Adoption Rate**: 40% → 80% customers with Intune (12 months)
- **Autopilot Readiness**: 0% → 50% customers (12 months)
- **Managed Service Conversion**: 30% of no-Intune customers sign managed service

---

## Next Steps

### Immediate (Week 1-2)
1. Create master PPKG template (standardized 80% configuration)
2. Develop customer qualification questionnaire
3. Build token expiry tracking system (spreadsheet + calendar reminders)
4. Create 3rd party SLA/runbook (PPKG application procedures)

### Short-Term (Month 1-2)
5. Document Intune Quick Start runbook (6-8 hour implementation checklist)
6. Create risk disclosure template (for no-management provisioning)
7. Develop pricing model (per-device vs managed service)
8. Pilot with 2-3 customers across all segments

### Medium-Term (Month 3-6)
9. Build customer maturity assessment scorecard (Intune readiness evaluation)
10. Create Autopilot transition plan template (customer-by-customer roadmap)
11. Develop automation scripts (PPKG generation, token expiry checks)
12. Launch customer Intune uplift program (targeted outreach to 40% no-Intune base)

---

## Appendix: Technical Reference

### PPKG Configuration Examples

#### Minimal PPKG (Intune-Ready Customer)
```
Windows Configuration Designer Settings:

1. Accounts > ComputerAccount
   - Not configured (Intune handles Azure AD join)

2. Accounts > Users
   - Create local admin: TechAdmin
   - Password: [Customer-specific, documented]

3. Policies > DesktopSettings > LockScreen
   - Background image: Company wallpaper
   - LockScreenOverlayConfiguration: Support info (phone, email, IT portal)

4. Runtime Settings > Provisioning > BulkEnrollment
   - BulkEnrollmentToken: [From customer Intune tenant]

5. Runtime Settings > Time
   - TimeZone: AUS Eastern Standard Time
```

#### Standard PPKG (Certificates + Wi-Fi)
```
Add to Minimal PPKG:

6. Certificates > ClientCertificates
   - Root CA certificate (.cer file)
   - Intermediate CA certificate (.cer file)
   - Install to: Trusted Root Certification Authorities

7. Connectivity > WLANSetting > WLAN
   - SSID: Customer-Corporate
   - ConnectionType: ESS
   - Authentication: WPA2-Enterprise
   - Encryption: AES
   - EAPType: TLS (if certificate-based)
```

#### Domain Join PPKG (On-Prem AD)
```
1. Accounts > ComputerAccount
   - Account: DOMAIN\ComputerJoinSvc
   - AccountPassword: [Encrypted in PPKG]
   - Domain: customer.local
   - OrganizationalUnit: OU=Workstations,DC=customer,DC=local

2. Accounts > Users
   - Create local admin: TechAdmin

3. Policies > DesktopSettings
   - LockScreen configuration

4. Connectivity > WiFi
   - Corporate Wi-Fi profiles (for domain connectivity)

5. Certificates
   - Root/Intermediate CA certificates (if customer has PKI)
```

---

### Required Firewall Ports

**Device → Intune/Azure AD**:
```
- 443/TCP (HTTPS - management.azure.com, login.microsoftonline.com)
- 80/TCP (HTTP - redirect to HTTPS)
- 53/UDP (DNS)

Full list: https://learn.microsoft.com/en-us/mem/intune/fundamentals/intune-endpoints
```

**Device → On-Prem Domain Controller**:
```
- 53/TCP+UDP (DNS)
- 88/TCP+UDP (Kerberos authentication)
- 389/TCP+UDP (LDAP)
- 445/TCP (SMB/CIFS)
- 464/TCP+UDP (Kerberos password change)
- 636/TCP (LDAPS - if using secure LDAP)
- 3268/TCP (Global Catalog - if multi-domain forest)
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | Principal Endpoint Engineer Agent | Initial strategy document - 3rd party provisioning analysis |

---

## Related Documentation

- **Autopilot Deployment Guide**: [Link to existing Autopilot docs]
- **Intune Configuration Standards**: [Link to Intune baseline policies]
- **Customer Maturity Assessment**: [Link to assessment framework]
- **3rd Party Vendor SLA**: [Link to vendor agreement]

---

**Questions or Feedback**: Contact Endpoint Engineering Team
