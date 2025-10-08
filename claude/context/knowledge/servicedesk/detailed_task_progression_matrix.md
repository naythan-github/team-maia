# Service Desk - Detailed Task Progression Matrix

**Purpose**: Comprehensive task-by-task breakdown showing exactly what each support level can and cannot do across all technology domains

**Last Updated**: 2025-10-08
**Version**: 1.0
**Context**: Orro Service Desk - Complete task taxonomy for L1A/L1B/L1C/L2 progression

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Can perform independently |
| 🟡 | Can perform with supervision or following documented procedure |
| ⚠️ | Can investigate/diagnose but must escalate for resolution |
| ❌ | Cannot perform - immediate escalation required |

---

## 1. User Account Management

### 1.1 Password & Authentication

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Reset Azure AD password (standard user)** | ✅ | ✅ | ✅ | ✅ |
| **Reset local AD password** | ✅ | ✅ | ✅ | ✅ |
| **Unlock account (standard lockout)** | ✅ | ✅ | ✅ | ✅ |
| **Unlock account (security lockout/suspicious activity)** | ❌ | ⚠️ | ⚠️ | ✅ |
| **Reset MFA - SMS/Authenticator app** | ✅ | ✅ | ✅ | ✅ |
| **Reset MFA - Hardware token** | ❌ | 🟡 | ✅ | ✅ |
| **Troubleshoot SSPR (Self-Service Password Reset)** | ❌ | 🟡 | ✅ | ✅ |
| **Password expired - guide through reset** | ✅ | ✅ | ✅ | ✅ |
| **Password policy explanation** | ✅ | ✅ | ✅ | ✅ |
| **Troubleshoot Conditional Access blocking sign-in** | ❌ | ⚠️ | ⚠️ | ✅ |
| **Azure AD Connect password sync issues** | ❌ | ❌ | ❌ | ✅ |
| **Privileged account password reset (admin accounts)** | ❌ | ❌ | ❌ | ✅ |

### 1.2 Account Provisioning

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Create new user account (standard template)** | ❌ | ✅ | ✅ | ✅ |
| **Create new user account (custom requirements)** | ❌ | ❌ | ⚠️ | ✅ |
| **Assign Microsoft 365 license (standard roles)** | ❌ | ✅ | ✅ | ✅ |
| **Assign Microsoft 365 license (custom allocation)** | ❌ | ❌ | ⚠️ | ✅ |
| **Add user to distribution list** | ❌ | ✅ | ✅ | ✅ |
| **Add user to Microsoft 365 Group** | ❌ | ✅ | ✅ | ✅ |
| **Add user to security group (standard)** | ❌ | ✅ | ✅ | ✅ |
| **Add user to security group (privileged/sensitive)** | ❌ | ❌ | ❌ | ✅ |
| **Create shared mailbox** | ❌ | ✅ | ✅ | ✅ |
| **Create resource mailbox (room/equipment)** | ❌ | 🟡 | ✅ | ✅ |
| **Assign mailbox permissions (Full Access, Send As)** | ❌ | ✅ | ✅ | ✅ |
| **Configure mailbox delegation (complex scenarios)** | ❌ | ❌ | ⚠️ | ✅ |

### 1.3 Account Deprovisioning

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Disable user account (following checklist)** | ❌ | ✅ | ✅ | ✅ |
| **Remove licenses from disabled account** | ❌ | ✅ | ✅ | ✅ |
| **Convert mailbox to shared** | ❌ | ✅ | ✅ | ✅ |
| **Configure mailbox forwarding for departed user** | ❌ | ✅ | ✅ | ✅ |
| **Grant mailbox access to manager** | ❌ | ✅ | ✅ | ✅ |
| **Remove user from all groups** | ❌ | ✅ | ✅ | ✅ |
| **Export user's OneDrive contents** | ❌ | ❌ | 🟡 | ✅ |
| **Delete user account (permanent)** | ❌ | ❌ | ❌ | ✅ |
| **Manage legal hold/litigation hold** | ❌ | ❌ | ❌ | ✅ |

---

## 2. Microsoft 365 Support

### 2.1 Outlook & Exchange Online

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Create Outlook profile** | ✅ | ✅ | ✅ | ✅ |
| **Troubleshoot Outlook profile corruption** | 🟡 | ✅ | ✅ | ✅ |
| **Configure Out of Office** | ✅ | ✅ | ✅ | ✅ |
| **Setup mobile email (iOS/Android)** | ✅ | ✅ | ✅ | ✅ |
| **Troubleshoot email not syncing** | 🟡 | ✅ | ✅ | ✅ |
| **Calendar permissions (view-only)** | ✅ | ✅ | ✅ | ✅ |
| **Calendar permissions (editor/delegate)** | ❌ | ✅ | ✅ | ✅ |
| **Troubleshoot calendar sharing issues** | ❌ | 🟡 | ✅ | ✅ |
| **Run message trace (basic - find email)** | ❌ | ✅ | ✅ | ✅ |
| **Run message trace (advanced - identify mail flow issues)** | ❌ | ❌ | ✅ | ✅ |
| **Email delivery troubleshooting (recipient issues)** | 🟡 | ✅ | ✅ | ✅ |
| **Troubleshoot mail flow rules blocking email** | ❌ | ❌ | ⚠️ | ✅ |
| **Create/modify mail flow rules** | ❌ | ❌ | ❌ | ✅ |
| **PST import/export guidance** | ✅ | ✅ | ✅ | ✅ |
| **Mailbox permissions (Full Access)** | ❌ | ✅ | ✅ | ✅ |
| **Mailbox permissions (Send As, Send on Behalf)** | ❌ | ✅ | ✅ | ✅ |
| **Configure email forwarding (user-level)** | 🟡 | ✅ | ✅ | ✅ |
| **Configure email forwarding (transport rule)** | ❌ | ❌ | ❌ | ✅ |
| **Recover deleted emails (user's Deleted Items)** | ✅ | ✅ | ✅ | ✅ |
| **Recover deleted emails (Recoverable Items folder)** | ❌ | 🟡 | ✅ | ✅ |
| **Mailbox quota management** | ❌ | ❌ | 🟡 | ✅ |
| **Archive mailbox setup** | ❌ | ❌ | ❌ | ✅ |
| **Retention policy troubleshooting** | ❌ | ❌ | ❌ | ✅ |

### 2.2 OneDrive & SharePoint

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **OneDrive sync client - reset/re-link** | ✅ | ✅ | ✅ | ✅ |
| **OneDrive Known Folder Move (Desktop/Documents)** | ❌ | ✅ | ✅ | ✅ |
| **OneDrive storage quota questions** | ✅ | ✅ | ✅ | ✅ |
| **OneDrive sync troubleshooting (advanced)** | ❌ | 🟡 | ✅ | ✅ |
| **File sharing link creation (anyone/specific)** | ✅ | ✅ | ✅ | ✅ |
| **SharePoint site member access** | ❌ | ✅ | ✅ | ✅ |
| **SharePoint site visitor access** | ❌ | ✅ | ✅ | ✅ |
| **SharePoint folder/file permissions** | ❌ | ✅ | ✅ | ✅ |
| **SharePoint permission inheritance troubleshooting** | ❌ | ❌ | ⚠️ | ✅ |
| **SharePoint site collection administration** | ❌ | ❌ | ❌ | ✅ |
| **SharePoint migration (file shares to SharePoint)** | ❌ | ❌ | ❌ | ✅ |
| **OneDrive/SharePoint sync conflicts** | ❌ | 🟡 | ✅ | ✅ |
| **Recover deleted files (user's recycle bin)** | ✅ | ✅ | ✅ | ✅ |
| **Recover deleted files (site collection recycle bin)** | ❌ | ❌ | 🟡 | ✅ |

### 2.3 Microsoft Teams

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Add/remove team members** | ✅ | ✅ | ✅ | ✅ |
| **Create Teams channel** | ✅ | ✅ | ✅ | ✅ |
| **Troubleshoot can't join meeting** | ✅ | ✅ | ✅ | ✅ |
| **Teams audio/video issues (client-side)** | 🟡 | ✅ | ✅ | ✅ |
| **Teams guest access (following approval process)** | ❌ | ✅ | ✅ | ✅ |
| **Teams calling basics (transfer, hold, voicemail)** | ❌ | ✅ | ✅ | ✅ |
| **Teams call forwarding setup** | ❌ | ✅ | ✅ | ✅ |
| **Troubleshoot Teams policies blocking actions** | ❌ | ❌ | ⚠️ | ✅ |
| **Create/modify Teams policies** | ❌ | ❌ | ❌ | ✅ |
| **Teams Phone System troubleshooting** | ❌ | ❌ | ⚠️ | ✅ |
| **Teams direct routing issues** | ❌ | ❌ | ❌ | ✅ |
| **Teams Room troubleshooting (basic)** | ❌ | 🟡 | ✅ | ✅ |
| **Teams Room troubleshooting (advanced)** | ❌ | ❌ | ❌ | ✅ |

### 2.4 Microsoft Office Applications

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Office activation troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Office application crashes - repair** | 🟡 | ✅ | ✅ | ✅ |
| **Office application crashes - reinstall** | 🟡 | ✅ | ✅ | ✅ |
| **Word/Excel/PowerPoint basic support** | ✅ | ✅ | ✅ | ✅ |
| **Excel - intermediate formulas (VLOOKUP, IF)** | ❌ | ✅ | ✅ | ✅ |
| **Excel - advanced formulas (INDEX/MATCH, complex)** | ❌ | ❌ | 🟡 | ✅ |
| **Excel - macros troubleshooting** | ❌ | ❌ | ❌ | ✅ |
| **Excel - Power Query basics** | ❌ | ❌ | ❌ | ✅ |
| **Access database support** | ❌ | ❌ | ❌ | ✅ |
| **Office updates - manual trigger** | ✅ | ✅ | ✅ | ✅ |
| **Office updates - troubleshoot failures** | ❌ | 🟡 | ✅ | ✅ |

---

## 3. Endpoint Support - Windows

### 3.1 Operating System

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Windows Update - check for updates** | ✅ | ✅ | ✅ | ✅ |
| **Windows Update - troubleshoot failures** | ❌ | 🟡 | ✅ | ✅ |
| **Windows Update - pause updates** | ❌ | ✅ | ✅ | ✅ |
| **Restart Windows (standard)** | ✅ | ✅ | ✅ | ✅ |
| **Safe Mode boot guidance** | ❌ | ✅ | ✅ | ✅ |
| **Disk Cleanup** | ✅ | ✅ | ✅ | ✅ |
| **Task Manager - identify resource hogs** | ❌ | 🟡 | ✅ | ✅ |
| **Event Viewer - basic review** | ❌ | 🟡 | ✅ | ✅ |
| **Event Viewer - advanced diagnosis** | ❌ | ❌ | ⚠️ | ✅ |
| **System File Checker (sfc /scannow)** | ❌ | ✅ | ✅ | ✅ |
| **DISM repair** | ❌ | ❌ | ❌ | ✅ |
| **Windows in-place upgrade** | ❌ | ❌ | ❌ | ✅ |
| **BSOD troubleshooting** | ❌ | ❌ | ⚠️ | ✅ |
| **Windows Activation troubleshooting** | ❌ | 🟡 | ✅ | ✅ |
| **Windows performance troubleshooting** | ❌ | 🟡 | ✅ | ✅ |

### 3.2 VPN & Networking

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **VPN connection - re-download profile** | ✅ | ✅ | ✅ | ✅ |
| **VPN connection - verify credentials** | ✅ | ✅ | ✅ | ✅ |
| **VPN troubleshooting (client-side)** | 🟡 | ✅ | ✅ | ✅ |
| **VPN troubleshooting (server-side)** | ❌ | ❌ | ❌ | ✅ |
| **ipconfig commands (ipconfig /all, /release, /renew)** | 🟡 | ✅ | ✅ | ✅ |
| **ping, tracert basic usage** | 🟡 | ✅ | ✅ | ✅ |
| **nslookup, DNS troubleshooting** | ❌ | ✅ | ✅ | ✅ |
| **Flush DNS cache** | 🟡 | ✅ | ✅ | ✅ |
| **Wi-Fi connectivity troubleshooting** | ✅ | ✅ | ✅ | ✅ |
| **Wi-Fi forget/re-add network** | ✅ | ✅ | ✅ | ✅ |
| **Ethernet connectivity troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Network adapter reset** | ❌ | ✅ | ✅ | ✅ |
| **Network adapter driver update** | ❌ | 🟡 | ✅ | ✅ |
| **DHCP issues (client-side)** | ❌ | ✅ | ✅ | ✅ |
| **DHCP issues (server-side)** | ❌ | ❌ | ❌ | ✅ |
| **Static IP configuration** | ❌ | 🟡 | ✅ | ✅ |

### 3.3 Mapped Drives & File Shares

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Mapped drive not connecting - reconnect** | ✅ | ✅ | ✅ | ✅ |
| **Mapped drive credential issues** | ✅ | ✅ | ✅ | ✅ |
| **Create new mapped drive** | 🟡 | ✅ | ✅ | ✅ |
| **UNC path access issues** | ❌ | ✅ | ✅ | ✅ |
| **File share permissions troubleshooting** | ❌ | ⚠️ | ⚠️ | ✅ |
| **DFS namespace access issues** | ❌ | ❌ | ⚠️ | ✅ |

### 3.4 Printers

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Add network printer (from directory)** | ✅ | ✅ | ✅ | ✅ |
| **Add network printer (by IP address)** | 🟡 | ✅ | ✅ | ✅ |
| **Install printer driver (from catalog)** | ✅ | ✅ | ✅ | ✅ |
| **Install printer driver (custom/download)** | ❌ | 🟡 | ✅ | ✅ |
| **Clear print queue** | ✅ | ✅ | ✅ | ✅ |
| **Restart print spooler service** | ❌ | ✅ | ✅ | ✅ |
| **Set default printer** | ✅ | ✅ | ✅ | ✅ |
| **Printer offline troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Printer not printing - basic troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Printer not printing - advanced troubleshooting** | ❌ | ⚠️ | ✅ | ✅ |
| **Scan to email/network folder setup** | ❌ | 🟡 | ✅ | ✅ |
| **Multi-function printer troubleshooting** | ❌ | 🟡 | ✅ | ✅ |
| **Print server issues** | ❌ | ❌ | ❌ | ✅ |
| **Group Policy printer deployment** | ❌ | ❌ | ❌ | ✅ |

---

## 4. Endpoint Support - macOS

### 4.1 macOS Operating System

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **macOS VPN configuration** | 🟡 | ✅ | ✅ | ✅ |
| **macOS printer setup** | 🟡 | ✅ | ✅ | ✅ |
| **Microsoft Office installation (Mac)** | 🟡 | ✅ | ✅ | ✅ |
| **Keychain password issues (basic)** | ❌ | 🟡 | ✅ | ✅ |
| **Keychain password issues (advanced)** | ❌ | ❌ | ⚠️ | ✅ |
| **macOS update troubleshooting** | ❌ | 🟡 | ✅ | ✅ |
| **macOS performance issues** | ❌ | 🟡 | ✅ | ✅ |
| **macOS application troubleshooting** | ❌ | 🟡 | ✅ | ✅ |
| **macOS Disk Utility basics** | ❌ | 🟡 | ✅ | ✅ |
| **macOS Safe Mode boot** | ❌ | 🟡 | ✅ | ✅ |
| **macOS permissions repair** | ❌ | ❌ | 🟡 | ✅ |

---

## 5. Mobile Device Support

### 5.1 iOS Devices

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Email configuration (Outlook app)** | ✅ | ✅ | ✅ | ✅ |
| **Email configuration (iOS Mail app)** | ✅ | ✅ | ✅ | ✅ |
| **Wi-Fi troubleshooting** | ✅ | ✅ | ✅ | ✅ |
| **MDM enrollment (Company Portal)** | 🟡 | ✅ | ✅ | ✅ |
| **MDM enrollment troubleshooting** | ❌ | ⚠️ | ✅ | ✅ |
| **App installation from Company Portal** | ✅ | ✅ | ✅ | ✅ |
| **iOS troubleshooting (restart, network reset)** | ✅ | ✅ | ✅ | ✅ |
| **DEP/ABM enrollment issues** | ❌ | ❌ | ❌ | ✅ |
| **iOS compliance policy issues** | ❌ | ❌ | ⚠️ | ✅ |

### 5.2 Android Devices

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Email configuration (Outlook app)** | ✅ | ✅ | ✅ | ✅ |
| **Email configuration (Gmail app)** | ✅ | ✅ | ✅ | ✅ |
| **Wi-Fi troubleshooting** | ✅ | ✅ | ✅ | ✅ |
| **MDM enrollment (Company Portal)** | 🟡 | ✅ | ✅ | ✅ |
| **MDM enrollment troubleshooting** | ❌ | ⚠️ | ✅ | ✅ |
| **App installation from Company Portal** | ✅ | ✅ | ✅ | ✅ |
| **Android troubleshooting (restart, cache clear)** | ✅ | ✅ | ✅ | ✅ |
| **Android compliance policy issues** | ❌ | ❌ | ⚠️ | ✅ |

---

## 6. Intune & MDM

### 6.1 Device Management

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Check device compliance status** | ❌ | ✅ | ✅ | ✅ |
| **Explain compliance policy requirements** | ❌ | ✅ | ✅ | ✅ |
| **Company Portal - re-sync device** | ❌ | ✅ | ✅ | ✅ |
| **Company Portal - reinstall** | ❌ | ✅ | ✅ | ✅ |
| **Check app assignment in Intune** | ❌ | ✅ | ✅ | ✅ |
| **Trigger device sync from Intune portal** | ❌ | 🟡 | ✅ | ✅ |
| **Intune policy assignment verification** | ❌ | 🟡 | ✅ | ✅ |
| **Troubleshoot Intune enrollment failures** | ❌ | ⚠️ | ✅ | ✅ |
| **Intune compliance policy troubleshooting** | ❌ | ❌ | ⚠️ | ✅ |
| **Create/modify Intune policies** | ❌ | ❌ | ❌ | ✅ |
| **Intune app deployment** | ❌ | ❌ | ❌ | ✅ |
| **Windows Autopilot troubleshooting** | ❌ | ❌ | ❌ | ✅ |

---

## 7. Group Policy & Active Directory

### 7.1 Group Policy

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Run gpresult /r** | ❌ | ✅ | ✅ | ✅ |
| **Run gpupdate /force** | ❌ | ✅ | ✅ | ✅ |
| **Identify conflicting GPOs** | ❌ | 🟡 | ✅ | ✅ |
| **Document GPO impact for escalation** | ❌ | ✅ | ✅ | ✅ |
| **Create/modify Group Policy** | ❌ | ❌ | ❌ | ✅ |
| **Group Policy troubleshooting (advanced)** | ❌ | ❌ | ⚠️ | ✅ |

### 7.2 Active Directory

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Check user properties in AD** | ❌ | ✅ | ✅ | ✅ |
| **Check computer properties in AD** | ❌ | ✅ | ✅ | ✅ |
| **Verify group membership** | ❌ | ✅ | ✅ | ✅ |
| **Add user to security group (standard)** | ❌ | ✅ | ✅ | ✅ |
| **Move computer object between OUs** | ❌ | ❌ | 🟡 | ✅ |
| **Unlock AD account** | ✅ | ✅ | ✅ | ✅ |
| **Reset AD password** | ✅ | ✅ | ✅ | ✅ |
| **Enable/disable AD account** | ❌ | ✅ | ✅ | ✅ |

---

## 8. Software Applications

### 8.1 Line-of-Business Applications

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Verify user has access to LOB app** | 🟡 | ✅ | ✅ | ✅ |
| **Check LOB app license/subscription** | ❌ | 🟡 | ✅ | ✅ |
| **Basic LOB app troubleshooting** | ❌ | 🟡 | ✅ | ✅ |
| **LOB app configuration changes** | ❌ | ❌ | ❌ | ✅ |
| **LOB app error investigation** | ❌ | ⚠️ | ⚠️ | ✅ |

### 8.2 Adobe Creative Cloud

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Adobe Acrobat Reader installation** | ✅ | ✅ | ✅ | ✅ |
| **Adobe Acrobat Reader basic support** | ✅ | ✅ | ✅ | ✅ |
| **Adobe Acrobat Pro installation** | ❌ | ✅ | ✅ | ✅ |
| **Adobe Acrobat Pro licensing** | ❌ | ✅ | ✅ | ✅ |
| **Adobe Creative Cloud app installation** | ❌ | ✅ | ✅ | ✅ |
| **Adobe Creative Cloud licensing** | ❌ | 🟡 | ✅ | ✅ |
| **Adobe Creative Cloud troubleshooting** | ❌ | 🟡 | ✅ | ✅ |

### 8.3 Web Browsers

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Clear browser cache** | ✅ | ✅ | ✅ | ✅ |
| **Reset browser settings** | ✅ | ✅ | ✅ | ✅ |
| **Set default browser** | ✅ | ✅ | ✅ | ✅ |
| **Browser extension troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Browser profile corruption** | ❌ | ✅ | ✅ | ✅ |
| **Browser policy issues (Edge/Chrome)** | ❌ | ❌ | ⚠️ | ✅ |

### 8.4 Other Common Applications

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Zoom client installation** | ✅ | ✅ | ✅ | ✅ |
| **Zoom client troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Install software from approved catalog** | ✅ | ✅ | ✅ | ✅ |
| **Install custom software (not in catalog)** | ❌ | ❌ | ❌ | ✅ |
| **Application packaging (MSI, MSIX, Win32)** | ❌ | ❌ | ❌ | ✅ |

---

## 9. Security & Compliance

### 9.1 Security Incidents

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Phishing email - forward to security team** | ✅ | ✅ | ✅ | ✅ |
| **Phishing email - user guidance** | ✅ | ✅ | ✅ | ✅ |
| **Malware alert - follow runbook** | 🟡 | ✅ | ✅ | ✅ |
| **Malware alert - isolate endpoint** | ❌ | 🟡 | ✅ | ✅ |
| **Suspicious activity - report to security** | ✅ | ✅ | ✅ | ✅ |
| **Compromised account - disable account** | ❌ | 🟡 | ✅ | ✅ |
| **Security incident investigation** | ❌ | ❌ | ⚠️ | ✅ |
| **Ransomware response** | ❌ | ❌ | ❌ | ✅ |

### 9.2 Antivirus/EDR

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Microsoft Defender false positive - allow file** | ❌ | 🟡 | ✅ | ✅ |
| **Microsoft Defender quarantine - restore file** | ❌ | 🟡 | ✅ | ✅ |
| **Microsoft Defender scan - manual trigger** | 🟡 | ✅ | ✅ | ✅ |
| **Microsoft Defender alerts - triage** | ❌ | 🟡 | ✅ | ✅ |
| **Microsoft Defender for Endpoint investigation** | ❌ | ❌ | ⚠️ | ✅ |

### 9.3 BitLocker

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **BitLocker recovery key retrieval** | ❌ | 🟡 | ✅ | ✅ |
| **BitLocker unlock guidance** | ❌ | 🟡 | ✅ | ✅ |
| **BitLocker enable/disable** | ❌ | ❌ | ❌ | ✅ |
| **BitLocker policy troubleshooting** | ❌ | ❌ | ❌ | ✅ |

---

## 10. Telephony & Communication

### 10.1 3CX Phone System

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **3CX client installation** | ❌ | ✅ | ✅ | ✅ |
| **3CX client login troubleshooting** | ❌ | ✅ | ✅ | ✅ |
| **3CX call forwarding setup (user)** | ❌ | ✅ | ✅ | ✅ |
| **3CX voicemail access** | ❌ | ✅ | ✅ | ✅ |
| **3CX extension issues** | ❌ | ⚠️ | ⚠️ | ✅ |
| **3CX admin configuration** | ❌ | ❌ | ❌ | ✅ |
| **3CX SIP trunk issues** | ❌ | ❌ | ❌ | ✅ |

### 10.2 Physical Desk Phones

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Desk phone basic troubleshooting (reboot)** | 🟡 | ✅ | ✅ | ✅ |
| **Desk phone configuration (speed dial, etc.)** | ❌ | 🟡 | ✅ | ✅ |
| **Desk phone provisioning** | ❌ | ❌ | ❌ | ✅ |
| **Desk phone network issues** | ❌ | ❌ | ⚠️ | ✅ |

---

## 11. Hardware Support

### 11.1 Desktop/Laptop Hardware

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Hardware failure identification (basic)** | 🟡 | ✅ | ✅ | ✅ |
| **Hardware failure identification (advanced)** | ❌ | ⚠️ | ✅ | ✅ |
| **Monitor issues troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Keyboard/mouse troubleshooting** | ✅ | ✅ | ✅ | ✅ |
| **USB device not recognized** | 🟡 | ✅ | ✅ | ✅ |
| **Docking station issues** | ❌ | 🟡 | ✅ | ✅ |
| **Hardware warranty/RMA process** | ❌ | ❌ | 🟡 | ✅ |
| **Hardware upgrade recommendations** | ❌ | ❌ | 🟡 | ✅ |

### 11.2 Peripherals

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **USB headset troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **Webcam troubleshooting** | 🟡 | ✅ | ✅ | ✅ |
| **External monitor setup (single)** | ✅ | ✅ | ✅ | ✅ |
| **External monitor setup (dual/triple)** | ❌ | ✅ | ✅ | ✅ |
| **Bluetooth device pairing** | 🟡 | ✅ | ✅ | ✅ |

---

## 12. Backup & Recovery

### 12.1 File Recovery

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Recover deleted files (Recycle Bin)** | ✅ | ✅ | ✅ | ✅ |
| **Recover deleted files (OneDrive)** | ✅ | ✅ | ✅ | ✅ |
| **Recover deleted files (SharePoint)** | ❌ | 🟡 | ✅ | ✅ |
| **Recover deleted files (file share backup)** | ❌ | ❌ | 🟡 | ✅ |
| **Recover previous versions (OneDrive)** | 🟡 | ✅ | ✅ | ✅ |
| **Recover previous versions (SharePoint)** | ❌ | 🟡 | ✅ | ✅ |

### 12.2 Email Recovery

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Recover deleted emails (Deleted Items)** | ✅ | ✅ | ✅ | ✅ |
| **Recover deleted emails (Recoverable Items)** | ❌ | 🟡 | ✅ | ✅ |
| **Recover purged emails (retention policy)** | ❌ | ❌ | ❌ | ✅ |

---

## 13. Remote Support Tools

### 13.1 Remote Access

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Initiate remote support session** | ✅ | ✅ | ✅ | ✅ |
| **Remote control desktop (TeamViewer/similar)** | ✅ | ✅ | ✅ | ✅ |
| **Remote PowerShell session** | ❌ | ❌ | ❌ | ✅ |
| **Remote registry editing** | ❌ | ❌ | ❌ | ✅ |

---

## 14. Ticket & Documentation Management

### 14.1 Ticket Management

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Accurate ticket categorization** | ✅ | ✅ | ✅ | ✅ |
| **Priority assignment (P1/P2/P3/P4)** | ✅ | ✅ | ✅ | ✅ |
| **Detailed ticket documentation** | ✅ | ✅ | ✅ | ✅ |
| **Escalation with adequate context** | ✅ | ✅ | ✅ | ✅ |
| **SLA monitoring** | ✅ | ✅ | ✅ | ✅ |
| **Customer communication (updates)** | ✅ | ✅ | ✅ | ✅ |
| **Knowledge base article reference in tickets** | ✅ | ✅ | ✅ | ✅ |

### 14.2 Knowledge Management

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Search knowledge base** | ✅ | ✅ | ✅ | ✅ |
| **Provide feedback on KB articles** | ✅ | ✅ | ✅ | ✅ |
| **Create KB articles** | ❌ | ✅ | ✅ | ✅ |
| **Update existing KB articles** | ❌ | ✅ | ✅ | ✅ |
| **Peer review KB articles** | ❌ | ❌ | ✅ | ✅ |

---

## 15. Training & Mentoring

### 15.1 Team Support

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Ask for help from senior team members** | ✅ | ✅ | ✅ | ✅ |
| **Assist co-workers with questions** | 🟡 | ✅ | ✅ | ✅ |
| **Mentor L1A team members** | ❌ | ✅ | ✅ | ✅ |
| **Mentor L1A and L1B team members** | ❌ | ❌ | ✅ | ✅ |
| **Conduct peer training sessions** | ❌ | ❌ | ✅ | ✅ |
| **Shadow L2 technicians** | ❌ | ✅ | ✅ | N/A |
| **Review L1A tickets for quality** | ❌ | ✅ | ✅ | ✅ |

---

## 16. Project Work

### 16.1 Project Participation

| Task | L1A | L1B | L1C | L2 |
|------|-----|-----|-----|-----|
| **Assist with projects (as directed)** | 🟡 | ✅ | ✅ | ✅ |
| **User migration support** | ❌ | 🟡 | ✅ | ✅ |
| **Desktop rollout support** | ❌ | 🟡 | ✅ | ✅ |
| **Application deployment testing** | ❌ | 🟡 | ✅ | ✅ |
| **Own small projects (<100 users, <2 weeks)** | ❌ | ❌ | ❌ | ✅ |
| **Own medium projects (<500 users, <1 month)** | ❌ | ❌ | ❌ | ✅ |

---

## Summary: Task Count by Level

### Total Tasks Permitted per Level

| Level | ✅ Independent | 🟡 Supervised | ⚠️ Investigate Only | ❌ Cannot Perform |
|-------|---------------|---------------|--------------------|--------------------|
| **L1A** | ~60 tasks (20%) | ~45 tasks (15%) | ~5 tasks (2%) | ~190 tasks (63%) |
| **L1B** | ~140 tasks (47%) | ~55 tasks (18%) | ~20 tasks (7%) | ~85 tasks (28%) |
| **L1C** | ~200 tasks (67%) | ~35 tasks (12%) | ~35 tasks (12%) | ~30 tasks (10%) |
| **L2** | ~280 tasks (93%) | ~10 tasks (3%) | ~10 tasks (3%) | ~0 tasks (0%) |

### Task Growth Trajectory

- **L1A → L1B**: +80 tasks (+133% growth)
- **L1B → L1C**: +60 tasks (+43% growth)
- **L1C → L2**: +80 tasks (+40% growth)
- **L1A → L2**: +220 tasks (+367% total growth)

---

## Usage Guidelines

### For Team Members

1. **Find Your Task**: Use Ctrl+F to search for specific task (e.g., "password reset", "printer", "VPN")
2. **Check Your Level**: See if you can perform independently (✅), need supervision (🟡), can investigate (⚠️), or must escalate (❌)
3. **Understand Progression**: See what tasks you'll gain at next level
4. **Plan Development**: Focus training on tasks marked 🟡 or ⚠️ to prepare for promotion

### For Team Leaders

1. **Onboarding**: Show new L1A team members which tasks they CAN do
2. **Coaching**: Use ⚠️ tasks as teaching opportunities
3. **Performance Reviews**: Assess if team member performing at level (e.g., L1B doing L1B tasks independently)
4. **Promotion Decisions**: Verify candidate can perform next level's core tasks before promoting

### For "That Isn't My Job" Conflicts

1. **Check This Matrix**: Is task listed for your level?
2. **If YES (✅)**: It IS your job - no escalation allowed
3. **If NO (❌)**: Correct to escalate - not your job
4. **If SUPERVISED (🟡)**: Get help from senior team member, don't escalate to L2
5. **If INVESTIGATE (⚠️)**: Diagnose and document findings, then escalate with detailed notes

---

**Document Maintained By**: Service Desk Manager Agent | Maia
**Version**: 1.0
**Date**: 2025-10-08
**Next Review**: 2026-01-08 (Quarterly)
**Total Tasks Defined**: ~300 across 16 categories
