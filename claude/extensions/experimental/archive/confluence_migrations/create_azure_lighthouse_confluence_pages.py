#!/usr/bin/env python3
"""
⚠️  ARCHIVED - MIGRATION COMPLETE ⚠️

This was a one-time migration script for Azure Lighthouse documentation.
Migration has been completed and this script is no longer needed.

PURPOSE: Migrated Azure Lighthouse docs to Confluence Orro space (completed ~Jan 2025)
STATUS: Archived to claude/extensions/experimental/archive/confluence_migrations/ (Phase 129)
REPLACEMENT: Use reliable_confluence_client.py + confluence_html_builder.py for new page creation

For ongoing Confluence operations:
- Create pages: claude/tools/reliable_confluence_client.py
- Generate HTML: claude/tools/confluence_html_builder.py
- See guide: claude/documentation/CONFLUENCE_TOOLING_GUIDE.md

ORIGINAL DESCRIPTION (for historical reference):
Create complete Azure Lighthouse documentation in Confluence Orro space
"""

import sys
import warnings

# Deprecation warning
warnings.warn(
    "create_azure_lighthouse_confluence_pages.py is ARCHIVED (migration complete). "
    "Use reliable_confluence_client.py for new page creation. "
    "See claude/documentation/CONFLUENCE_TOOLING_GUIDE.md",
    DeprecationWarning,
    stacklevel=2
)

sys.path.insert(0, '/Users/naythandawe/git/maia/claude/tools')
from reliable_confluence_client import ReliableConfluenceClient
import time

def create_all_pages():
    client = ReliableConfluenceClient()
    parent_id = "3133243394"  # Executive Summary page
    pages_created = []

    print("📄 Creating Azure Lighthouse Confluence pages in Orro space...")
    print("=" * 70)

    # Page 2: Technical Prerequisites
    print("\n📋 Creating Page 2: Technical Prerequisites & Requirements...")
    content2 = """
<h1>Azure Lighthouse - Technical Prerequisites & Requirements</h1>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>Parent Document:</strong> Azure Lighthouse Implementation - Executive Summary</p>
<p><strong>Target Audience:</strong> Orro Technical Teams | <strong>Last Updated:</strong> 2025-01-09</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Orro (Managing Tenant) Requirements</h2>

<h3>Azure AD Security Groups Structure</h3>
<pre>
Orro-Azure-LH-L1-ServiceDesk → Reader, Monitoring Reader
Orro-Azure-LH-L2-Engineers → Contributor, Support Request Contributor
Orro-Azure-LH-L3-Architects → Contributor (via PIM)
Orro-Azure-LH-Security → Security Admin
Orro-Azure-LH-Admins → Delegation Delete Role
Orro-Azure-LH-PIM-Approvers → PIM approval function
</pre>

<h3>Licensing (Optional - for PIM only)</h3>
<ul>
<li><strong>Required:</strong> EMS E5 or Azure AD Premium P2</li>
<li><strong>Cost:</strong> $8-16 USD/user/month</li>
<li><strong>Only for:</strong> Users activating eligible (JIT) roles</li>
<li><strong>Decision:</strong> Start without PIM, add later if needed</li>
</ul>

<h3>Microsoft Partner Network</h3>
<ul>
<li>Create service principal associated with Partner ID</li>
<li>Include in every ARM template for PEC tracking</li>
<li>CSP customers: Use ARM templates (not Marketplace)</li>
</ul>

<h2>Customer (Managed Tenant) Requirements</h2>

<h3>Minimum Requirements</h3>
<table>
<tr><th>Requirement</th><th>Details</th></tr>
<tr><td>Active Azure Subscription</td><td>At least one subscription</td></tr>
<tr><td>Owner-level Access</td><td>User deploying needs Owner role</td></tr>
<tr><td>Non-Guest Account</td><td>Must be member user in customer tenant</td></tr>
<tr><td>Licenses</td><td>NONE - standard Azure subscription sufficient</td></tr>
</table>

<h2>Azure RBAC Roles Reference</h2>

<h3>Supported Roles (Commonly Used)</h3>
<table>
<tr><th>Role Name</th><th>Role ID</th><th>Use Case</th></tr>
<tr><td>Reader</td><td>acdd72a7-3385-48ef-bd42-f606fba81ae7</td><td>L1 monitoring</td></tr>
<tr><td>Contributor</td><td>b24988ac-6180-42a0-ab88-20f7382dd24c</td><td>L2/L3 operations</td></tr>
<tr><td>Monitoring Reader</td><td>43d0d8ad-25c7-4714-9337-8ba259a9fe05</td><td>L1 monitoring</td></tr>
<tr><td>Security Admin</td><td>fb1c8493-542b-42f4-a55d-6e525e11384b</td><td>Security team</td></tr>
<tr><td>Backup Contributor</td><td>5e467623-bb1f-42f4-a55d-6e525e11384b</td><td>Backup operations</td></tr>
<tr><td>Delegation Delete Role</td><td>91c1777a-f3dc-4fae-b103-61d183457e46</td><td><strong>MUST INCLUDE</strong></td></tr>
</table>

<h3>NOT Supported</h3>
<ul>
<li>Owner role</li>
<li>User Access Administrator (limited support)</li>
<li>Roles with DataActions permissions</li>
<li>Custom roles</li>
</ul>

<h2>Implementation Checklist</h2>

<h3>Week 1-2: Orro Internal Setup</h3>
<ul>
<li>[ ] Document Orro's Azure AD Tenant ID</li>
<li>[ ] Create all security groups listed above</li>
<li>[ ] Assign Orro staff to appropriate groups</li>
<li>[ ] Document all group Object IDs</li>
<li>[ ] Create service principal for Partner ID</li>
<li>[ ] Register Microsoft.ManagedServices resource provider</li>
<li>[ ] Decide: Use PIM or not? (can add later)</li>
</ul>

<h3>Before Each Customer Onboarding</h3>
<ul>
<li>[ ] Verify customer contact has Owner role</li>
<li>[ ] Confirm customer's Tenant ID and Subscription ID</li>
<li>[ ] Confirm Microsoft.ManagedServices registered in customer subscription</li>
</ul>
"""

    result2 = client.create_page(
        space_key="Orro",
        title="Azure Lighthouse - Technical Prerequisites",
        content=content2,
        parent_id=parent_id
    )

    if result2:
        print(f"✅ Created: {result2['url']}")
        pages_created.append(result2)
        time.sleep(2)
    else:
        print("❌ Failed to create Page 2")

    # Page 3: ARM Templates & Deployment
    print("\n📋 Creating Page 3: ARM Templates & Deployment Methods...")

    content3 = """
<h1>Azure Lighthouse - ARM Templates & Deployment Methods</h1>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>Parent Document:</strong> Azure Lighthouse Implementation - Executive Summary</p>
<p><strong>Target Audience:</strong> Orro Technical Teams | <strong>Last Updated:</strong> 2025-01-09</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>ARM Template Structure</h2>

<h3>Main Template Components</h3>
<p>Two Azure resources required:</p>
<ol>
<li><strong>Registration Definition</strong>: Defines what access Orro needs (reusable)</li>
<li><strong>Registration Assignment</strong>: Activates definition for specific customer scope</li>
</ol>

<h3>Basic Template Example</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">json</ac:parameter>
<ac:plain-text-body><![CDATA[
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "mspOfferName": {
      "type": "string",
      "defaultValue": "Orro Managed Azure Services"
    },
    "managedByTenantId": {
      "type": "string",
      "defaultValue": "ORRO-TENANT-ID-HERE"
    },
    "authorizations": {
      "type": "array"
    }
  },
  "variables": {
    "mspRegistrationName": "[guid(parameters('mspOfferName'))]",
    "mspAssignmentName": "[guid(parameters('mspOfferName'))]"
  },
  "resources": [
    {
      "type": "Microsoft.ManagedServices/registrationDefinitions",
      "apiVersion": "2022-10-01",
      "name": "[variables('mspRegistrationName')]",
      "properties": {
        "registrationDefinitionName": "[parameters('mspOfferName')]",
        "managedByTenantId": "[parameters('managedByTenantId')]",
        "authorizations": "[parameters('authorizations')]"
      }
    },
    {
      "type": "Microsoft.ManagedServices/registrationAssignments",
      "apiVersion": "2022-10-01",
      "name": "[variables('mspAssignmentName')]",
      "dependsOn": [
        "[resourceId('Microsoft.ManagedServices/registrationDefinitions/', variables('mspRegistrationName'))]"
      ],
      "properties": {
        "registrationDefinitionId": "[resourceId('Microsoft.ManagedServices/registrationDefinitions/', variables('mspRegistrationName'))]"
      }
    }
  ]
}
]]></ac:plain-text-body>
</ac:structured-macro>

<h3>Parameters File Example</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">json</ac:parameter>
<ac:plain-text-body><![CDATA[
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "mspOfferName": {
      "value": "Orro Managed Azure Services"
    },
    "managedByTenantId": {
      "value": "ORRO-TENANT-ID-GUID"
    },
    "authorizations": {
      "value": [
        {
          "principalId": "L1-SERVICEDESK-GROUP-OBJECT-ID",
          "roleDefinitionId": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
          "principalIdDisplayName": "Orro L1 Service Desk - Reader"
        },
        {
          "principalId": "L2-ENGINEERS-GROUP-OBJECT-ID",
          "roleDefinitionId": "b24988ac-6180-42a0-ab88-20f7382dd24c",
          "principalIdDisplayName": "Orro L2 Engineers - Contributor"
        },
        {
          "principalId": "ADMIN-GROUP-OBJECT-ID",
          "roleDefinitionId": "91c1777a-f3dc-4fae-b103-61d183457e46",
          "principalIdDisplayName": "Orro Admin - Delegation Delete Role"
        },
        {
          "principalId": "PARTNER-ID-SPN-OBJECT-ID",
          "roleDefinitionId": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
          "principalIdDisplayName": "Orro Partner ID Service Principal"
        }
      ]
    }
  }
}
]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Deployment Methods</h2>

<h3>Method 1: Azure Portal (Recommended for Manual Phase)</h3>
<ol>
<li>Customer logs into Azure Portal</li>
<li>Navigate to <strong>Deploy a custom template</strong></li>
<li>Select <strong>Build your own template in the editor</strong></li>
<li>Paste ARM template JSON → Save</li>
<li>Upload parameters file or fill manually</li>
<li>Select <strong>Subscription</strong> scope</li>
<li>Review + Create → Deploy</li>
<li>Wait 15-60 minutes for sync</li>
<li>Verify in Orro's tenant: Azure Lighthouse → My customers</li>
</ol>

<h3>Method 2: Azure CLI</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">bash</ac:parameter>
<ac:plain-text-body><![CDATA[
# Login to customer tenant
az login --tenant "customer-tenant-id"

# Set subscription context
az account set --subscription "customer-sub-id"

# Deploy template at subscription scope
az deployment sub create \
  --name "OrroLighthouseOnboarding" \
  --location "australiaeast" \
  --template-file lighthouse-template.json \
  --parameters @lighthouse-parameters.json

# Verify deployment
az managedservices definition list
az managedservices assignment list
]]></ac:plain-text-body>
</ac:structured-macro>

<h3>Method 3: PowerShell</h3>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">powershell</ac:parameter>
<ac:plain-text-body><![CDATA[
# Login to customer tenant
Connect-AzAccount -Tenant "customer-tenant-id"

# Set subscription context
Set-AzContext -SubscriptionId "customer-sub-id"

# Deploy template at subscription scope
New-AzSubscriptionDeployment `
  -Name "OrroLighthouseOnboarding" `
  -Location "australiaeast" `
  -TemplateFile lighthouse-template.json `
  -TemplateParameterFile lighthouse-parameters.json

# Verify deployment
Get-AzManagedServicesDefinition
Get-AzManagedServicesAssignment
]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Template Customization for Orro</h2>

<h3>Step 1: Gather Object IDs</h3>
<p>Run these commands in Orro's Azure AD:</p>

<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">bash</ac:parameter>
<ac:plain-text-body><![CDATA[
# Get Orro's Tenant ID
az account show --query tenantId -o tsv

# Get Security Group Object IDs
az ad group show --group "Orro-Azure-LH-L1-ServiceDesk" --query objectId -o tsv
az ad group show --group "Orro-Azure-LH-L2-Engineers" --query objectId -o tsv
az ad group show --group "Orro-Azure-LH-Admins" --query objectId -o tsv

# Get Service Principal Object ID (for Partner ID)
az ad sp show --id "service-principal-app-id" --query objectId -o tsv
]]></ac:plain-text-body>
</ac:structured-macro>

<h3>Step 2: Create Parameters Template</h3>
<p>Save as <code>lighthouse-parameters-TEMPLATE.json</code> with Orro's actual IDs filled in</p>

<h3>Step 3: Per-Customer Customization</h3>
<p>For each customer, only need to change:</p>
<ul>
<li><code>mspOfferName</code>: "Orro Managed Services - [Customer Name]"</li>
<li>Nothing else changes! (That's the power of reusable templates)</li>
</ul>

<h2>Verification Steps</h2>

<h3>From Orro's Tenant</h3>
<ol>
<li>Navigate to <strong>Azure Lighthouse</strong> service</li>
<li>Select <strong>My customers</strong></li>
<li>Verify customer subscription appears in list</li>
<li>Click customer → verify authorizations are correct</li>
<li>Test access: Try viewing resources in customer subscription</li>
</ol>

<h3>From Customer's Tenant</h3>
<ol>
<li>Navigate to <strong>Service providers</strong></li>
<li>Verify Orro's offer is listed</li>
<li>View delegated scopes and permissions</li>
<li>Check Activity Log for Orro's test actions</li>
</ol>
"""

    result3 = client.create_page(
        space_key="Orro",
        title="Azure Lighthouse - ARM Templates & Deployment",
        content=content3,
        parent_id=parent_id
    )

    if result3:
        print(f"✅ Created: {result3['url']}")
        pages_created.append(result3)
        time.sleep(2)
    else:
        print("❌ Failed to create Page 3")

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully created {len(pages_created)} pages in Confluence")
    print("\nCreated Pages:")
    for i, page in enumerate(pages_created, 2):
        print(f"{i}. {page['title']}")
        print(f"   URL: {page['url']}")

    return pages_created

if __name__ == "__main__":
    create_all_pages()
