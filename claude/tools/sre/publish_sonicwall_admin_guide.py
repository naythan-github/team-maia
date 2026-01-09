#!/usr/bin/env python3
"""
Publish SonicWall Administrator Guide to Orro Confluence Space

Created: 2026-01-09
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from _reliable_confluence_client import ReliableConfluenceClient

# Confluence-compatible HTML content
SONICWALL_ADMIN_GUIDE_HTML = """
<h1>SonicWall Firewall - Multiple Administrator Setup Guide</h1>

<p><strong>Document Date:</strong> 2026-01-09<br/>
<strong>Purpose:</strong> Configure multiple administrators with granular role-based access control (RBAC) for MSP client access<br/>
<strong>Platform:</strong> SonicOS 6.5+/7.x (TZ, NSa, NSsp series)</p>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>Key Finding:</strong> SonicWall firewalls support multiple administrators with granular permissions - perfect for controlled client access without compromising MSP security</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Administrator Types Overview</h2>

<table>
<thead>
<tr>
<th>Role</th>
<th>Access Level</th>
<th>Typical Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Admin</strong></td>
<td>Full access (root)</td>
<td>MSP super admin</td>
</tr>
<tr>
<td><strong>Read-Write</strong></td>
<td>Modify config, no user/admin management</td>
<td>Client IT lead</td>
</tr>
<tr>
<td><strong>Read-Only</strong></td>
<td>View only, no changes</td>
<td>Audit/monitoring</td>
</tr>
<tr>
<td><strong>Limited Admin</strong></td>
<td>Custom permissions</td>
<td>Specific use cases</td>
</tr>
</tbody>
</table>

<h2>Custom Permission Granularity</h2>

<p>You can restrict access to specific areas:</p>
<ul>
<li>✅ Firewall policies (view/edit)</li>
<li>✅ VPN management</li>
<li>✅ User authentication</li>
<li>✅ Logs and reporting</li>
<li>✅ Network configuration</li>
<li>❌ Admin account management (restricted)</li>
<li>❌ Firmware upgrades (restricted)</li>
</ul>

<h2>Recommended Configuration for Client Access</h2>

<p><strong>Navigation:</strong> System → Administration → Admins</p>

<h3>Option A: Read-Write Admin (Most Common)</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[Name: client_admin
Password: [strong password]
Role: Read-Write
Access: HTTPS Management
Allowed Networks: Client IP range (restrict source)]]></ac:plain-text-body>
</ac:structured-macro>

<p><strong>Capabilities:</strong></p>
<ul>
<li>✅ Modify firewall rules, NAT, VPN</li>
<li>✅ View logs, troubleshoot</li>
<li>❌ Cannot create/delete admins</li>
<li>❌ Cannot change MSP admin credentials</li>
</ul>

<h3>Option B: Limited Admin (Highly Restricted)</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[Name: client_limited
Role: Limited Admin
Permissions:
  ✅ View Dashboard
  ✅ View/Edit Firewall Policies
  ✅ View Logs
  ❌ VPN Management
  ❌ System Settings
  ❌ Security Services]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Best Practices for MSP Client Access</h2>

<h3>1. IP Restriction (Critical)</h3>

<p>Lock admin accounts to specific source IPs:</p>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[System → Administration → Admins → [Edit Admin]
→ Allowed Networks: 203.0.113.0/24 (client office IP)]]></ac:plain-text-body>
</ac:structured-macro>

<h3>2. Separate Management Accounts</h3>

<ul>
<li><strong>Your MSP:</strong> Keep full "Admin" role with different username</li>
<li><strong>Client:</strong> Grant "Read-Write" or "Limited Admin"</li>
<li><strong>Never share the root admin account</strong></li>
</ul>

<h3>3. Enable Logging</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[System → Administration → Admin Settings
→ ✅ Log all administrator logins
→ ✅ Log configuration changes]]></ac:plain-text-body>
</ac:structured-macro>

<h3>4. Multi-Factor Authentication (SonicOS 7.x)</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[System → Administration → Admins
→ ✅ Require MFA for admin login]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Step-by-Step Configuration</h2>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="title">Step 1: Create Client Admin Account</ac:parameter>
<ac:rich-text-body>
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[System → Administration → Admins → Add
- Name: client_admin
- Password: [strong]
- Role: Read-Write
- Management: HTTPS ✅ | SSH ❌ (unless needed)]]></ac:plain-text-body>
</ac:structured-macro>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="title">Step 2: Restrict Source IP</ac:parameter>
<ac:rich-text-body>
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[→ Allowed Networks: Add → [client public IP]/32]]></ac:plain-text-body>
</ac:structured-macro>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="title">Step 3: Test Access</ac:parameter>
<ac:rich-text-body>
<ul>
<li>Have client login from their IP</li>
<li>Verify they can access needed features</li>
<li>Confirm they cannot modify admin accounts</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="title">Step 4: Document and Communicate</ac:parameter>
<ac:rich-text-body>
<ul>
<li>Provide credentials via secure channel (not email)</li>
<li>Document restrictions clearly</li>
<li>Set password expiration policy if required</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Advanced: Limited Admin Custom Permissions</h2>

<p>If "Read-Write" is too broad, use Limited Admin with custom permissions:</p>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[System → Administration → Admins → Add
Role: Limited Admin
Permissions tab:
  Dashboard: Read ✅
  Network: Read ✅ | Write ✅
  Firewall: Read ✅ | Write ✅
  VPN: Read ✅ | Write ❌ (restrict if needed)
  Users: Read ❌ | Write ❌
  System: Read ❌ | Write ❌
  Logs: Read ✅]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Key Security Considerations</h2>

<ac:structured-macro ac:name="tip">
<ac:parameter ac:name="title">Security Best Practices</ac:parameter>
<ac:rich-text-body>
<ul>
<li>✅ Always use IP restrictions</li>
<li>✅ Enable admin login logging</li>
<li>✅ Use strong passwords (12+ chars, complexity)</li>
<li>✅ Consider MFA (SonicOS 7.x+)</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="note">
<ac:parameter ac:name="title">MSP Protection</ac:parameter>
<ac:rich-text-body>
<ul>
<li>❌ Client cannot delete your admin account</li>
<li>❌ Client cannot see your admin password</li>
<li>❌ Client cannot disable logging</li>
<li>❌ Client cannot upgrade/downgrade firmware (if Read-Write)</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Audit Trail</h2>

<p>All admin actions are logged and can be viewed:</p>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">text</ac:parameter>
<ac:plain-text-body><![CDATA[Log → View → Event Name: "Admin login" or "Configuration changed"
→ Filter by User: client_admin]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Recommendation Summary</h2>

<ac:structured-macro ac:name="info">
<ac:parameter ac:name="title">Recommended Approach</ac:parameter>
<ac:rich-text-body>
<p>Create a <strong>Read-Write</strong> admin with <strong>IP restriction</strong> to client's office.</p>
<p>This gives them full operational control while protecting critical system functions and your MSP access.</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Additional Resources</h2>

<ul>
<li><strong>SonicWall Documentation:</strong> <a href="https://www.sonicwall.com/support/technical-documentation/">Technical Documentation Portal</a></li>
<li><strong>SonicOS Admin Guide:</strong> Check your specific model and version</li>
<li><strong>MySonicWall:</strong> <a href="https://www.mysonicwall.com">Support Portal</a></li>
</ul>

<hr/>

<p><strong>Document Created:</strong> 2026-01-09<br/>
<strong>Agent:</strong> SonicWall Specialist Agent v2.3<br/>
<strong>Prepared For:</strong> MSP client administrator access requests</p>
"""


def main():
    print("="*80)
    print("Publishing SonicWall Administrator Guide to Orro Confluence Space")
    print("="*80)
    print()

    # Initialize Confluence client
    client = ReliableConfluenceClient()

    # Run health check
    print("🏥 Running health check...")
    health_status = client.health_check()
    print(f"   Status: {health_status['status']}")
    print(f"   Success Rate: {health_status['metrics']['success_rate']}")
    print()

    # Create page in Orro space
    space_key = "Orro"
    title = "SonicWall Multiple Administrator Setup Guide - MSP Client Access"

    print(f"📝 Creating Confluence page...")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print()

    try:
        result = client.create_page(
            space_key=space_key,
            title=title,
            content=SONICWALL_ADMIN_GUIDE_HTML,
            validate_html=False  # Use False since we're using basic Confluence macros
        )

        if result:
            print("="*80)
            print("✅ SUCCESS - Page Published to Confluence")
            print("="*80)
            print()
            print(f"Space: {space_key}")
            print(f"Title: {title}")
            print(f"Page ID: {result.get('id', 'Unknown')}")
            print(f"URL: {result.get('url', 'N/A')}")
            print()
            print("📊 View page in Confluence Orro space")
            print()
            return 0
        else:
            print("❌ Failed to create page (no result returned)")
            return 1

    except Exception as e:
        print(f"❌ Error creating page: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
