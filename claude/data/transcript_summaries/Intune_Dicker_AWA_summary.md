# Executive Summary: Intune, Dicker Data, AWA Discussion

**Meeting Date**: October 3, 2025
**Processed**: 2025-10-03 19:15 by Maia Personal Assistant

## 1. Meeting Overview
- **Date**: October 3, 2025
- **Participants**: Martin Dunn (Orro), Naythan Dawe (Orro), Harpreet Kaur (Orro)
- **Duration**: Approximately 33 minutes
- **Meeting Type**: Technical discussion and vendor coordination

## 2. Problem Statement
- **E-waste/Shredex vendor agreement**: Need to establish vendor relationship for e-waste disposal services
- **AWA out-of-scope work**: Service desk engineers being pressured by SDMs to perform out-of-scope field services without proper authorization or charging mechanisms
- **SDM boundary issues**: SDMs requesting field services without confirming if work is chargeable or within contract scope
- **Intune deployment tracking**: Lack of visibility into which customers have Intune configured and which don't
- **Revenue leakage**: Field service costs (Uber, engineer time) not being billed to customers

## 3. Proposed Solutions

### E-waste/Shredex
- Use Shredex (AMG sister company) as e-waste vendor
- Implement cost-plus pricing model (10-15% margin)
- Open book approach - customer pays vendor cost plus agreed margin
- Formalize terms and conditions
- Leverage existing AMG vendor relationship for simplicity

### AWA Field Services
- Establish clear process requiring written customer acceptance of charges before dispatching field engineers
- Move to AWA outsourced model for all field services to improve ticket hygiene and data tracking
- Create field service request workflow with clear approval gates
- Service desk to log jobs in AWA web portal manually (interim solution)

### SDM Boundary Setting
- Naythan to address in fortnightly SDM meeting (blameless approach)
- Services team to report continued issues over next two weeks
- Meeting with Richard to discuss systemic issues
- Require services team to escalate to Naythan before accepting out-of-scope requests

### Intune Tracking
- Mariel to update customer spreadsheet with granular subcategories
- Services team (Peter/Dylan or Trevor) to audit Lighthouse portal to determine active Intune deployments
- Create yes/no radio button tracking system
- Potential PowerShell automation if Trevor has appropriate access

## 4. Architecture Decisions
- **Field Services**: Transition to outsourced model (AWA/Dicker Data) rather than building internal capability
- **Intune Onboarding**: Significant project scope ($50K-$500K per customer depending on size) - defer until pod structure established
- **Contract Management**: Future integration between contract management system and OTC ticket system to automate chargeable/non-chargeable determination
- **Provisioning Workflow**: Dicker Data handles Intune pre-registration, AWA handles on-site deployment, Service Desk coordinates

## 5. Technical Risks
- **Missing data on current state**: Unknown how many customers actively use Intune; licensing may be activated but not fully deployed
- **License complexity**: Some customers have partial Intune activation (1 license) giving limited functionality
- **OTC system limitations**: Custom fields/checkboxes may disappear due to monolith architecture and insufficient developers
- **Training gaps**: Service desk lacks clear guidance on when work is chargeable
- **Process dependency**: Cannot implement new-world processes without first fixing old-world revenue leakage

## 6. Action Items

| Owner | Action | Deadline |
|-------|--------|----------|
| Martin | Draft formal e-waste/Shredex terms and conditions | Next week |
| Martin | Create shared Excel task tracker for AWA/Dicker/Intune work | Immediate |
| Martin | Take AWA network request to network team (documented process exists) | Next week |
| Naythan | Provide subcategory list to Mariel for customer spreadsheet update | Next week |
| Naythan | Get services team to audit Intune deployments via Lighthouse | Next week |
| Naythan | Address SDM boundary issues in fortnightly meeting (blameless) | Next fortnightly meeting |
| Naythan | Meeting with Richard to discuss out-of-scope work systemic issues | Scheduled |
| Naythan | Provide Intune deployment status report | Next week |
| Harpreet | Validate field service scenarios with Amrit | Monday |
| Harpreet | Test field service process with Hamish | Next week |
| Services Team | Report any continued SDM pressure for out-of-scope work | Next 2 weeks |

## 7. Dependencies
- **Contract management system**: Required for automated chargeable/non-chargeable determination - not yet built
- **Intune customer list**: Blocks Dicker Data pricing negotiations (volume-based pricing)
- **Pod structure**: Must be established before major Intune onboarding projects can proceed
- **Lighthouse access**: Trevor needs full access this week to enable PowerShell auditing
- **Wednesday meeting with Hamish**: Next milestone for AWA/Dicker/Intune project review

## 8. Executive Summary
This meeting addressed critical vendor coordination and revenue leakage issues around field services and device provisioning. The team agreed to establish Shredex for e-waste with cost-plus pricing, transition to outsourced field services via AWA to improve billing and ticket hygiene, and set clear boundaries with SDMs who pressure engineers to perform out-of-scope work. A customer Intune deployment audit is underway to support Dicker Data vendor negotiations, though major Intune onboarding projects are deferred until the pod structure is established due to their complexity and cost ($50K-$500K per customer).
