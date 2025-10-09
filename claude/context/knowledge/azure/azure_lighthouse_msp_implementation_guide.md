# Azure Lighthouse Implementation Guide for Orro MSP

**Last Updated**: 2025-01-09
**Agent**: Azure Solutions Architect Agent
**Target Audience**: Orro technical and operations teams
**Status**: Comprehensive research complete - ready for implementation

---

## Executive Summary

Azure Lighthouse is Microsoft's solution for managed service providers (MSPs) to manage multiple customer Azure tenants from a single control plane. This guide provides complete implementation requirements for Orro to set up Azure Lighthouse access across all Azure customers.

**Key Benefits:**
- ✅ **Zero customer cost** - Free Azure service
- ✅ **Enhanced security** - Granular RBAC replaces broad AOBO access
- ✅ **Full transparency** - Customers see all Orro actions in Activity Logs
- ✅ **Partner Earned Credit** - PEC tracking through Partner ID linkage
- ✅ **CSP Integration** - Works with existing CSP program
- ✅ **Australian compliance** - IRAP PROTECTED and Essential Eight aligned

**Implementation Timeline:**
- **Conservative**: 11-13 weeks (recommended)
- **Aggressive**: 5-6 weeks
- **Per customer**: 2-3 hours effort, 15-30 days elapsed

---

## 1. Azure Lighthouse Fundamentals

### What is Azure Lighthouse?

Azure Lighthouse enables **Azure delegated resource management** where customers explicitly delegate access to their Azure subscriptions or resource groups to Orro's tenant.

### Architecture Overview

**Key Components:**

1. **Managing Tenant** (Orro's Azure AD tenant)
   - Contains Orro's user accounts, security groups, service principals
   - Source of identity for accessing customer resources
   - Where management tools and monitoring dashboards reside

2. **Managed Tenant** (Customer's Azure AD tenant)
   - Customer retains full ownership and control
   - Hosts the delegated subscriptions/resource groups
   - Stores all Activity Log entries for Orro's actions

3. **Registration Definition**
   - Template defining what access Orro needs (roles and principals)
   - Includes offer name, description, authorizations array
   - Reusable across multiple customers

4. **Registration Assignment**
   - Activates the Registration Definition for a specific customer scope
   - Created per subscription or resource group
   - Links customer resources to Orro's managing tenant

5. **Cross-Tenant Authorization**
   - Azure AD identity from Orro's tenant
   - Azure RBAC role assignment in customer's subscription
   - No credentials exchanged between tenants

**Security Model:**
- **Identity-based access**: Uses Azure AD identities, not shared credentials
- **Audit logging**: Every action logged in customer's tenant (90-day retention minimum)
- **Customer control**: Customers can remove delegation anytime
- **MFA enforcement**: Applies from managing tenant policies
- **Conditional Access**: Must be configured on Orro's tenant (customer CA policies don't apply to delegated access)

---

## 2. Prerequisites & Requirements

### A. Orro (MSP) Tenant Requirements

#### Required Azure AD Resources

1. **Azure AD Tenant**: Orro's existing Azure AD tenant

2. **Security Groups**: Create dedicated security groups for role-based access
   - Recommended structure:
     - `Orro-Azure-LH-L1-ServiceDesk` (Reader, Monitoring Reader)
     - `Orro-Azure-LH-L2-Engineers` (Contributor, Support Request Contributor)
     - `Orro-Azure-LH-L3-Architects` (Contributor, Policy Contributor)
     - `Orro-Azure-LH-Security` (Security Admin, Security Reader)
     - `Orro-Azure-LH-Admins` (Delegation management)
     - `Orro-Azure-LH-PIM-Approvers` (PIM approval function)

3. **Service Principals**: Optional but recommended for automation
   - Create per-customer service principals for better isolation
   - Implement secret rotation process

#### Required Licenses (for PIM/Eligible Authorizations)

- **Enterprise Mobility + Security E5 (EMS E5)** OR **Azure AD Premium P2**
- License required on **Orro's tenant only** (not customer tenants)
- Only needed for users who will activate eligible (JIT) roles
- Standard (permanent) authorizations don't require these licenses
- **Cost**: ~$8-16 USD/user/month

#### Microsoft Partner Network

- **Partner ID**: Link Orro's Partner ID to track customer engagement
  - Create service principal associated with Partner ID
  - Include in every customer onboarding for Partner Earned Credit (PEC)
  - Enables recognition for Azure Lighthouse activities

- **CSP Integration** (if applicable):
  - Azure Lighthouse works with CSP program subscriptions
  - Standard onboarding process applies to CSP subscriptions
  - Users with Admin Agent role can perform onboarding
  - **Important**: Private Marketplace offers NOT supported for CSP subscriptions (use ARM templates instead)

#### Resource Provider Registration

- **Microsoft.ManagedServices** resource provider must be registered in Orro's subscriptions
- Failure to register causes deployment errors

### B. Customer Tenant Requirements

#### Minimum Requirements

1. **Active Azure Subscription**: Customer must have at least one active Azure subscription
2. **Owner-level Access**: Onboarding user needs Owner role OR these specific permissions:
   - `Microsoft.Authorization/roleAssignments/write`
   - `Microsoft.Authorization/roleAssignments/delete`
   - `Microsoft.Authorization/roleAssignments/read`
3. **Non-Guest Account**: Deployment must be done by non-guest user in customer tenant

#### No License Requirements

- Customers do NOT need any special licenses
- No Azure AD Premium requirement for customers
- Standard Azure subscription is sufficient

### C. Required Azure RBAC Roles

#### Supported Roles for Delegation

Azure Lighthouse supports all Azure **built-in roles** EXCEPT:
- ❌ **Owner** role (not supported)
- ❌ **User Access Administrator** (limited support - only for assigning to managed identities)
- ❌ **Roles with DataActions** permissions (e.g., Storage Blob Data Contributor)
- ❌ **Custom roles** (not supported)
- ❌ **Classic subscription administrator roles** (not supported)

#### Commonly Used Roles for MSP Operations

**Tier 1 - Service Desk / Monitoring:**
- Reader (`acdd72a7-3385-48ef-bd42-f606fba81ae7`)
- Monitoring Reader (`43d0d8ad-25c7-4714-9337-8ba259a9fe05`)
- Log Analytics Reader (`73c42c96-874c-492b-b04d-ab87d138a893`)
- Support Request Contributor (`cfd33db0-3dd1-45e3-aa9d-cdbdf3b6f24e`)

**Tier 2 - Engineering / Operations:**
- Contributor (`b24988ac-6180-42a0-ab88-20f7382dd24c`)
- Backup Contributor (`5e467623-bb1f-42f4-a55d-6e525e11384b`)
- Backup Operator (`00c29273-979b-4161-815c-10b084fb9324`)
- Virtual Machine Contributor (`9980e02c-c2be-4d73-94e8-173b1dc7cf3c`)
- Network Contributor (`4d97b98b-1d4f-4787-a291-c67834d212e7`)
- Storage Account Contributor (`17d1049b-9a84-46fb-8f53-869881c3d3ab`)

**Tier 3 - Architecture / Security:**
- Security Admin (`fb1c8493-542b-42f4-a55d-6e525e11384b`)
- Security Reader (`39bc4728-0917-49c7-9d2c-d95423bc2eb4`)
- Policy Contributor (`b24988ac-6180-42a0-ab88-20f7382dd24c`)
- Monitoring Contributor (`749f88d5-cbae-40b8-bcfc-e573ddc772fa`)

**Essential for MSP Management:**
- **Managed Services Registration Assignment Delete Role** (`91c1777a-f3dc-4fae-b103-61d183457e46`)
  - MUST include in every onboarding
  - Allows Orro to remove delegation if needed
  - Without this, only customer can remove access

---

## 3. Technical Implementation

### A. ARM Template Structure

#### Basic ARM Template Components

**Main Template (registrationDefinition + registrationAssignment):**

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "mspOfferName": {
      "type": "string",
      "defaultValue": "Orro Managed Azure Services"
    },
    "mspOfferDescription": {
      "type": "string",
      "defaultValue": "24/7 Azure management and support | Contact: support@orro.com.au"
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
        "description": "[parameters('mspOfferDescription')]",
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
```

#### Parameters File - Standard Authorizations Example

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "mspOfferName": {
      "value": "Orro Managed Azure Services"
    },
    "mspOfferDescription": {
      "value": "24/7 Azure infrastructure management and support | Contact: support@orro.com.au"
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
          "principalId": "L1-SERVICEDESK-GROUP-OBJECT-ID",
          "roleDefinitionId": "43d0d8ad-25c7-4714-9337-8ba259a9fe05",
          "principalIdDisplayName": "Orro L1 Service Desk - Monitoring Reader"
        },
        {
          "principalId": "L2-ENGINEERS-GROUP-OBJECT-ID",
          "roleDefinitionId": "b24988ac-6180-42a0-ab88-20f7382dd24c",
          "principalIdDisplayName": "Orro L2 Engineers - Contributor"
        },
        {
          "principalId": "L2-ENGINEERS-GROUP-OBJECT-ID",
          "roleDefinitionId": "cfd33db0-3dd1-45e3-aa9d-cdbdf3b6f24e",
          "principalIdDisplayName": "Orro L2 Engineers - Support Request Contributor"
        },
        {
          "principalId": "SECURITY-TEAM-GROUP-OBJECT-ID",
          "roleDefinitionId": "fb1c8493-542b-42f4-a55d-6e525e11384b",
          "principalIdDisplayName": "Orro Security Team - Security Admin"
        },
        {
          "principalId": "PARTNER-ID-SERVICE-PRINCIPAL-OBJECT-ID",
          "roleDefinitionId": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
          "principalIdDisplayName": "Orro Partner ID Service Principal"
        },
        {
          "principalId": "ADMIN-GROUP-OBJECT-ID",
          "roleDefinitionId": "91c1777a-f3dc-4fae-b103-61d183457e46",
          "principalIdDisplayName": "Orro Admin - Managed Services Registration Assignment Delete Role"
        }
      ]
    }
  }
}
```

### B. Deployment Methods

#### Method 1: Azure Portal Deployment (Recommended for First Time)

**Steps:**
1. Gather Information (Orro Tenant ID, Customer Subscription ID, Security Group Object IDs)
2. Create ARM Templates (template + parameters file)
3. Customer Deploys via Azure Portal:
   - Navigate to **Deploy a custom template**
   - Upload or paste ARM template
   - Fill parameters or upload parameters file
   - Select **Subscription** or **Resource Group** scope
   - Review + Create → Deploy
4. Wait for sync (15-60 minutes)
5. Verify delegation in Orro's **My customers** page

#### Method 2: Azure CLI Deployment

```bash
# Set variables
CUSTOMER_SUBSCRIPTION_ID="customer-sub-id"
TEMPLATE_FILE="lighthouse-template.json"
PARAMETERS_FILE="lighthouse-parameters.json"

# Login to customer tenant
az login --tenant "customer-tenant-id"

# Set subscription context
az account set --subscription $CUSTOMER_SUBSCRIPTION_ID

# Deploy template at subscription scope
az deployment sub create \
  --name "OrroLighthouseOnboarding" \
  --location "australiaeast" \
  --template-file $TEMPLATE_FILE \
  --parameters @$PARAMETERS_FILE

# Verify deployment
az managedservices definition list
az managedservices assignment list
```

#### Method 3: PowerShell Deployment

```powershell
# Set variables
$CustomerSubscriptionId = "customer-sub-id"
$TemplateFile = "lighthouse-template.json"
$ParametersFile = "lighthouse-parameters.json"

# Login to customer tenant
Connect-AzAccount -Tenant "customer-tenant-id"

# Set subscription context
Set-AzContext -SubscriptionId $CustomerSubscriptionId

# Deploy template at subscription scope
New-AzSubscriptionDeployment `
  -Name "OrroLighthouseOnboarding" `
  -Location "australiaeast" `
  -TemplateFile $TemplateFile `
  -TemplateParameterFile $ParametersFile

# Verify deployment
Get-AzManagedServicesDefinition
Get-AzManagedServicesAssignment
```

### C. PIM Eligible Authorizations (Advanced)

For just-in-time access requiring EMS E5 or Azure AD Premium P2 license.

#### Eligible Authorization Structure

```json
{
  "eligibleAuthorizations": {
    "value": [
      {
        "principalId": "L3-ARCHITECTS-GROUP-OBJECT-ID",
        "roleDefinitionId": "b24988ac-6180-42a0-ab88-20f7382dd24c",
        "principalIdDisplayName": "Orro L3 Architects - Contributor (JIT)",
        "justInTimeAccessPolicy": {
          "multiFactorAuthProvider": "Azure",
          "maximumActivationDuration": "PT8H",
          "managedByTenantApprovers": [
            {
              "principalId": "APPROVER-GROUP-OR-USER-ID"
            }
          ]
        }
      }
    ]
  }
}
```

**Key Properties:**
- **multiFactorAuthProvider**: `Azure` (require MFA) or `None`
- **maximumActivationDuration**: Between PT30M (30 min) and PT8H (8 hours)
- **managedByTenantApprovers**: Up to 10 approvers (optional - if empty, auto-approval)

**Important Notes:**
- Users activating eligible roles MUST have at least Reader access via permanent authorization
- Service principals CANNOT be used for eligible authorizations
- All activating users in Orro's tenant need EMS E5 or Azure AD P2 license

---

## 4. Security & Governance

### A. Just-in-Time Access with PIM

**When to Use PIM:**
- High-privilege roles (Contributor, Security Admin)
- Infrequent access scenarios
- Compliance requirements for time-limited access
- Break-glass emergency access

**PIM Configuration Best Practices:**

1. **Activation Duration**
   - L2 Standard Tasks: 4 hours
   - L3 Projects: 8 hours
   - Emergency Break-Glass: 2 hours

2. **Multi-Factor Authentication**
   - Always require MFA for activation
   - Configure in `multiFactorAuthProvider: Azure`

3. **Approval Workflow**
   - No approval: Low-risk roles for trusted staff
   - Single approver: Medium-risk roles
   - Dual approval: High-risk or break-glass scenarios

**Activation Process for Orro Staff:**
1. Navigate to **Azure AD Privileged Identity Management**
2. Select **Azure resources**
3. Find customer subscription
4. Select role to activate
5. Provide justification (required)
6. Request activation
7. Wait for approval (if required)
8. Access granted for configured duration

### B. Multi-Factor Authentication Requirements

**Critical Security Requirement:**

**Conditional Access Policies in Azure Lighthouse:**
- Policies on **customer tenants** do NOT apply to delegated access
- Policies on **Orro's tenant** DO apply to all staff accessing customer resources

**Orro Must Configure:**

1. **Baseline MFA Policy**
   - Require MFA for ALL users in Orro's tenant
   - Applies to all Azure portal access
   - Applies to Azure CLI/PowerShell authentication

2. **Example Conditional Access Policy:**

```
Name: Require MFA for Azure Management
Users: All Orro staff with Azure access
Cloud apps: Microsoft Azure Management
Conditions: Any location
Grant: Require multi-factor authentication + Require compliant device
Session: Sign-in frequency = 8 hours
```

### C. Audit Logging and Visibility

**Where Logs Are Stored:**

All Azure Lighthouse activity is logged in the **customer's Azure Activity Log**, not Orro's. This ensures customer transparency and control.

**What Gets Logged:**
- Every action performed by Orro users
- Identity of the user (from Orro's tenant)
- Timestamp, resource affected, operation performed
- Result (success/failure)
- PIM role activation/deactivation
- Delegation creation/removal

**Accessing Logs from Orro's Tenant:**

```bash
# List activity for a specific customer
az monitor activity-log list \
  --subscription "customer-subscription-id" \
  --start-time "2025-01-01" \
  --end-time "2025-01-31" \
  --query "[?caller contains 'orro.com.au']"
```

**Customer Visibility:**

Customers can view:
1. **Service Provider Offers** - All active delegations, delegated scopes, assigned roles
2. **Activity Log** - Real-time view of all Orro actions
3. **Role Assignments** - Delegated role assignments at resource IAM level
4. **PIM Activations** - When Orro users activate elevated roles

Customers can control:
1. **Remove Delegation Anytime** - Takes effect immediately
2. **Export Audit Data** - Download Activity Log for compliance
3. **View Delegation Details** - Exact permissions granted

---

## 5. Operational Best Practices

### A. Recommended RBAC Role Assignments

#### Tier 1 - Service Desk / NOC

**Responsibilities:** Monitoring, alerting, incident triage, basic troubleshooting

**Recommended Roles:**
- Reader (permanent)
- Monitoring Reader (permanent)
- Log Analytics Reader (permanent)
- Support Request Contributor (permanent)

**Rationale:** View-only access minimizes risk while enabling monitoring workflows

#### Tier 2 - Engineers / Specialists

**Responsibilities:** Incident resolution, change implementation, backup management, standard operations

**Recommended Roles:**
- Contributor (permanent at RG scope, eligible at subscription scope)
- Backup Contributor (permanent)
- Virtual Machine Contributor (permanent)
- Network Contributor (permanent)

**Rationale:** Scope to resource groups limits blast radius; subscription-level via PIM for escalations

#### Tier 3 - Architects / Senior Engineers

**Responsibilities:** Complex problem resolution, architecture changes, policy implementation, emergency response

**Recommended Roles:**
- Contributor (eligible/PIM with approval)
- Policy Contributor (eligible/PIM)
- Monitoring Contributor (eligible/PIM)

**Rationale:** High-privilege access only when needed with approval workflow

### B. Security Group Structure

**Recommended Azure AD Security Group Hierarchy:**

```
Orro-Azure-LH-All
├── Orro-Azure-LH-L1-ServiceDesk
├── Orro-Azure-LH-L2-Engineers
│   ├── Orro-Azure-LH-L2-Windows
│   ├── Orro-Azure-LH-L2-Linux
│   ├── Orro-Azure-LH-L2-Network
│   └── Orro-Azure-LH-L2-Backup
├── Orro-Azure-LH-L3-Architects
├── Orro-Azure-LH-Security
├── Orro-Azure-LH-PIM-Approvers
└── Orro-Azure-LH-Admins
```

**Group Management Best Practices:**
- **Naming Convention**: `Orro-Azure-LH-[Tier]-[Function]`
- **Group Type**: Security (not Microsoft 365)
- **Membership Type**: Assigned (not dynamic, for auditability)
- **Membership Reviews**: Quarterly via Azure AD Access Reviews
- **Onboarding**: Add new staff to groups as part of onboarding workflow
- **Offboarding**: Remove from all groups immediately upon departure

### C. Monitoring and Management at Scale

#### Unified Monitoring Dashboard

**Azure Monitor Workbook Example:**

Create custom workbook for cross-customer visibility:
- VM count by customer
- Active Orro users per customer
- PIM activation frequency
- Security alerts across all customers
- Cost trends by customer

**Azure Resource Graph Queries:**

Query across all customer subscriptions:

```kusto
Resources
| where subscriptionId in ({delegated_subscriptions})
| where type == 'microsoft.compute/virtualmachines'
| extend powerState = tostring(properties.extended.instanceView.powerState.displayStatus)
| project name, resourceGroup, subscriptionId, powerState, location
| order by subscriptionId, name
```

**Key Metrics to Monitor:**

1. **Resource Health** - VM availability, service health incidents
2. **Security & Compliance** - Secure score, policy compliance, security alerts
3. **Cost Management** - Subscription spend trends, budget alerts
4. **Operational Metrics** - Active Orro users, PIM activations, support requests

---

## 6. Orro-Specific Considerations

### A. Australian Compliance Requirements

#### IRAP PROTECTED Certification

**Azure Platform:**
- 113 Azure services certified at PROTECTED classification
- Australian data centers (Australia East, Australia Southeast, Australia Central)

**Azure Lighthouse Compliance:**
- Management plane feature (no data storage)
- Customer data remains in customer's tenant and regions
- Customer responsibility to assess in their risk framework

**For Orro Customers Requiring IRAP PROTECTED:**

1. **Data Residency**
   - Deploy all resources in Australia East or Australia Southeast regions
   - Use Azure Policy to enforce region restrictions

2. **Access Controls**
   - Document all Orro users with customer access
   - Enforce MFA for all Orro staff
   - Implement PIM for elevated access
   - Conduct quarterly access reviews

3. **Audit & Logging**
   - Enable Azure Activity Log export to customer's Log Analytics
   - Retain logs per customer retention policy (typically 7 years for government)

#### Essential Eight Alignment

| Essential Eight Control | Azure Lighthouse Capability |
|------------------------|----------------------------|
| Application Control | Azure Policy enforcement across delegations |
| Patch Applications | Visibility via Azure Update Management |
| Restrict Administrative Privileges | PIM for just-in-time elevation |
| Patch Operating Systems | Visibility via Azure Update Management |
| Multi-Factor Authentication | Enforced via Orro's Conditional Access policies |
| Regular Backups | Azure Backup monitoring and management |

### B. Microsoft CSP Integration

**Integration Benefits:**

1. **AOBO Replacement**
   - AOBO provides blanket access via Admin Agent role
   - Azure Lighthouse provides granular, auditable access
   - Recommend transitioning from AOBO to Lighthouse for security

2. **Partner Earned Credit (PEC)**
   - Link Orro's Partner ID to all Lighthouse delegations
   - Earn PEC for eligible Azure services under Azure plan
   - Requires service principal with Partner ID association

**CSP-Specific Limitations:**

- **Private Marketplace Offers**: NOT supported for CSP subscriptions (use ARM templates)
- **Admin Agent Role**: Still available but use sparingly with Lighthouse

**Recommended Workflow for CSP Customers:**

1. **Initial Access**: Use Admin Agent role (AOBO)
2. **Deploy Lighthouse**: Use ARM templates
3. **Transition Operations**: Move daily operations to Lighthouse access
4. **Retain AOBO**: Keep Admin Agent role for emergency/break-glass only
5. **Audit Regularly**: Review usage of AOBO vs Lighthouse access

### C. Change Management for Customer Communication

**Customer Communication Timeline:**

**Phase 1: Pre-Announcement (2-3 months before)**
- Internal Orro training on Azure Lighthouse
- Identify pilot customers
- Develop FAQs and documentation

**Phase 2: Customer Notification (1 month before)**
- Email to all customers explaining Azure Lighthouse
- Highlight benefits (security, transparency, efficiency)
- Provide timeline

**Phase 3: Customer Engagement (2-3 weeks before)**
- Schedule individual calls with customers
- Demonstrate Azure Lighthouse features
- Review permissions being requested

**Phase 4: Onboarding (deployment week)**
- Send deployment instructions
- Schedule deployment call
- Complete onboarding

**Phase 5: Post-Deployment (1 week after)**
- Follow-up call to ensure satisfaction
- Provide customer with activity log queries
- Gather feedback

**Sample Customer Communication Email Template:**

```
Subject: Enhancing Azure Management Security with Azure Lighthouse

Dear [Customer Name],

Orro is implementing Azure Lighthouse to improve the security and transparency
of our Azure managed services for you. Azure Lighthouse is Microsoft's
recommended approach for managed service providers to securely access customer
environments.

**What's Changing:**
- More granular access controls (specific roles instead of broad permissions)
- Enhanced visibility for you into all actions we perform
- Just-in-time access for elevated operations
- Improved audit logging and compliance

**What Stays the Same:**
- Our 24/7 support commitment
- Your service level agreements
- Monthly billing and reporting
- Your ability to revoke our access anytime

**Benefits to You:**
- Better Security: Minimum permissions needed for each task
- Full Transparency: See every action in your Azure Activity Log
- Compliance: Enhanced audit trail for regulatory requirements
- Control: Remove our access instantly at any time

**Next Steps:**
1. Review the attached Azure Lighthouse FAQ document
2. Schedule a deployment call: [contact information]
3. We'll provide ARM templates and guide you through deployment

If you have any questions, please contact your account manager [Name] at [Email].

Thank you for your continued partnership.

Best regards,
[Your Name]
Orro
```

---

## 7. Common Pitfalls & Solutions

### Known Issues During Setup

#### Issue 1: "Microsoft.ManagedServices Resource Provider Not Registered"

**Solution:**
```bash
# Customer must run in their subscription
az provider register --namespace Microsoft.ManagedServices

# Verify registration
az provider show --namespace Microsoft.ManagedServices --query "registrationState"
```

#### Issue 2: "Deployment User Lacks Permissions"

**Solution:**
- Verify user has Owner role on subscription or resource group
- Alternative: Grant specific permissions:
  - Microsoft.Authorization/roleAssignments/write
  - Microsoft.Authorization/roleAssignments/delete
  - Microsoft.Authorization/roleAssignments/read

#### Issue 3: "Delegation Not Appearing in Orro's Tenant"

**Solutions:**
1. Wait 30 minutes and refresh (sync delay 15-60 minutes)
2. Verify managedByTenantId matches Orro's tenant ID exactly
3. Ensure at least one authorization includes Reader role
4. Check Azure Service Health for platform issues

#### Issue 4: "Role with DataActions Cannot Be Assigned"

**Solution:**
- Use supported roles only (no DataActions)
- For storage scenarios, use access keys or SAS tokens instead
- Consider customer granting direct role assignment for specific scenarios

### Customer Objections and How to Address Them

#### Objection 1: "We don't want to give external access to our Azure environment"

**Response:**
- Empathize with security concerns
- Educate on enhanced security:
  - No shared credentials
  - Granular RBAC
  - All actions logged with staff names
  - Instant revocation capability
  - JIT access for elevated operations
- Offer to start with read-only access or specific resource groups

#### Objection 2: "We need to review this with our security team first"

**Response:**
- Support thorough security review
- Provide documentation:
  - Azure Lighthouse security whitepaper
  - List of exact permissions requested
  - Sample ARM templates
  - Microsoft official documentation
- Offer call with Orro security architect

#### Objection 3: "This seems like it will disrupt our operations"

**Response:**
- Reassure: Zero downtime or service interruption
- Explain: Metadata operation only, no changes to running resources
- Evidence: Successful onboarding track record
- Flexibility: Schedule deployment at preferred time (including off-hours)

---

## 8. Implementation Checklist

### Pre-Implementation Phase

**Orro Internal Preparation:**

- [ ] Verify Orro's Azure AD tenant ID
- [ ] Create Azure AD security groups (L1/L2/L3/Security/Admins/PIM-Approvers)
- [ ] Assign users to security groups
- [ ] Verify/purchase EMS E5 or Azure AD P2 licenses (if using PIM)
- [ ] Create service principal for Partner ID linkage
- [ ] Register Microsoft.ManagedServices resource provider
- [ ] Set up Azure Monitor workspace for cross-customer monitoring
- [ ] Create ARM template repository
- [ ] Configure PIM settings in Azure AD
- [ ] Document internal procedures

**Customer Communication Preparation:**

- [ ] Develop customer FAQ document
- [ ] Create onboarding guide
- [ ] Draft announcement email
- [ ] Prepare demonstration materials
- [ ] Create activity log query examples
- [ ] Develop monthly operational report template

### Pilot Phase

**Select Pilot Customers:**
- [ ] Identify 2-3 pilot customers (low-complexity, strong relationship)
- [ ] Schedule pilot kickoff meetings
- [ ] Send pilot customer communications

**Pilot Deployment:**
- [ ] Create customer-specific parameters files
- [ ] Verify customer contact has Owner role
- [ ] Send ARM templates
- [ ] Guide customer through deployment
- [ ] Verify delegation and test access
- [ ] Create customer dashboard

**Pilot Review:**
- [ ] Conduct retrospective meeting
- [ ] Gather feedback from Orro staff and customers
- [ ] Refine templates and processes

### Production Rollout Phase

**Wave Planning:**
- [ ] Categorize customers by complexity
- [ ] Create rollout schedule (Wave 1: Simple, Wave 2: Medium, Wave 3: Complex)

**Customer Onboarding (per customer):**
- [ ] Send announcement email (T-14 days)
- [ ] Schedule onboarding call (T-7 days)
- [ ] Create customer-specific parameters file
- [ ] Send ARM templates (T-3 days)
- [ ] Conduct deployment call (T-0)
- [ ] Deploy and verify access
- [ ] Provide customer with monitoring links
- [ ] Conduct 30-day review call (T+30)

### Operational Excellence Phase

- [ ] Create unified monitoring dashboard
- [ ] Set up cross-customer Resource Graph queries
- [ ] Configure Activity Log alerts
- [ ] Conduct quarterly access reviews
- [ ] Implement Azure Policy at scale
- [ ] Monitor delegation status
- [ ] Annual security assessment

---

## 9. Implementation Timeline

### Conservative Timeline (Recommended)

| Phase | Duration | Key Activities |
|-------|----------|---------------|
| **Planning & Design** | 2 weeks | Define groups, create templates, prepare docs |
| **Internal Setup** | 1 week | Create Azure AD groups, configure PIM, set up monitoring |
| **Pilot Deployment** | 2 weeks | Onboard 2-3 pilot customers, test, refine |
| **Production Rollout** | 6-8 weeks | Wave 1 (simple), Wave 2 (medium), Wave 3 (complex) |
| **Operational Excellence** | Ongoing | Quarterly reviews, optimization |
| **Total** | **11-13 weeks** | |

### Aggressive Timeline

| Phase | Duration |
|-------|----------|
| **Planning & Setup** | 1 week |
| **Pilot** | 1 week |
| **Production Rollout** | 3-4 weeks |
| **Total** | **5-6 weeks** |

### Per-Customer Onboarding Time

- **Elapsed**: 15-30 days (communication timeline)
- **Effort**: 2-3 hours per customer
- **Deployment**: 30-60 minutes

---

## 10. Next Steps for Orro

**Immediate Actions (Week 1-2):**

1. Create Azure AD security groups
2. Document Orro's tenant ID and group object IDs
3. Purchase EMS E5 / Azure AD P2 licenses (if using PIM)
4. Create service principal for Partner ID linking

**Week 3: Template Development**

1. Customize ARM templates with Orro's details
2. Create parameters file template
3. Test deployment in Orro's lab/test subscription

**Week 4-5: Pilot**

1. Select 2 pilot customers
2. Complete pilot deployments
3. Gather feedback and refine

**Week 6+: Production Rollout**

1. Execute phased rollout across customer base
2. Monitor and optimize

---

## 11. Support Resources

- **Microsoft Docs**: https://learn.microsoft.com/azure/lighthouse/
- **ARM Template Samples**: https://github.com/Azure/Azure-Lighthouse-samples
- **Microsoft Support**: Open support ticket via Azure portal
- **Community**: Azure Lighthouse discussions in Microsoft Tech Community

---

## Document Control

- **Created**: 2025-01-09
- **Agent**: Azure Solutions Architect Agent
- **Sources**: Microsoft Learn, Azure documentation, MSP best practices (2024-2025)
- **Review Cycle**: Quarterly (Azure Lighthouse features evolve regularly)
- **Location**: `/Users/naythandawe/git/maia/claude/context/knowledge/azure/azure_lighthouse_msp_implementation_guide.md`

---

**End of Azure Lighthouse Implementation Guide for Orro MSP**
