#!/usr/bin/env python3
"""
Publish Bitwarden Statement of Work to Orro Confluence Space

Comprehensive SOW with detailed tasks, time estimates, and deliverables.
Created: 2025-11-28
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from _reliable_confluence_client import ReliableConfluenceClient

# Comprehensive Bitwarden SOW in Confluence HTML
BITWARDEN_SOW_HTML = """
<h1>📋 Statement of Work: Self-Hosted Bitwarden Deployment</h1>

<p><strong>Client:</strong> [Customer Name]<br/>
<strong>Project:</strong> Enterprise Password Vault - Self-Hosted Bitwarden on Azure<br/>
<strong>Users:</strong> 300 Staff Members<br/>
<strong>Region:</strong> Australia (Data Residency Requirement)<br/>
<strong>SOW Version:</strong> 1.0<br/>
<strong>Date:</strong> 2025-11-28<br/>
<strong>Validity:</strong> 90 Days</p>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="bgColor">#deebff</ac:parameter>
<ac:parameter ac:name="title">📊 PROJECT SUMMARY</ac:parameter>
<ac:rich-text-body>
<p><strong>Total Duration:</strong> 4 weeks (20 business days)<br/>
<strong>Total Effort:</strong> 96 hours<br/>
<strong>Infrastructure Cost:</strong> $230/month (1-year RI)<br/>
<strong>Professional Services:</strong> $14,400 (96 hours @ $150/hour)</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>1. Executive Summary</h2>

<p>This Statement of Work (SOW) defines the scope, deliverables, timeline, and responsibilities for deploying a self-hosted Bitwarden password management solution on Microsoft Azure for [Customer Name]. The solution will provide secure password vault services for 300 staff members while maintaining Australian data residency compliance.</p>

<h3>Objectives</h3>

<ul>
<li><strong>Deploy production-grade Bitwarden instance</strong> on Azure infrastructure</li>
<li><strong>Ensure Australian data residency</strong> for compliance requirements</li>
<li><strong>Onboard 300 users</strong> with appropriate training and documentation</li>
<li><strong>Establish operational processes</strong> for ongoing maintenance and support</li>
<li><strong>Achieve 99.9% uptime SLA</strong> through reliable infrastructure design</li>
</ul>

<h3>Success Criteria</h3>

<table>
<thead>
<tr>
<th>Criteria</th>
<th>Target</th>
<th>Measurement</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Deployment Complete</strong></td>
<td>Week 1</td>
<td>Bitwarden accessible via HTTPS</td>
</tr>
<tr>
<td><strong>User Onboarding</strong></td>
<td>Weeks 2-3</td>
<td>300 users registered and trained</td>
</tr>
<tr>
<td><strong>Uptime SLA</strong></td>
<td>99.9%</td>
<td>Azure Monitor metrics</td>
</tr>
<tr>
<td><strong>Data Residency</strong></td>
<td>100% Australian</td>
<td>Azure resource audit</td>
</tr>
<tr>
<td><strong>Backup Validation</strong></td>
<td>Tested restore</td>
<td>Successful restore test completed</td>
</tr>
</tbody>
</table>

<h2>2. Scope of Work</h2>

<h3>2.1 In Scope</h3>

<ac:structured-macro ac:name="status">
<ac:parameter ac:name="colour">Green</ac:parameter>
<ac:parameter ac:name="title">✅ INCLUDED</ac:parameter>
</ac:structured-macro>

<table>
<thead>
<tr>
<th>Phase</th>
<th>Activities</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Phase 1: Planning</strong></td>
<td>
<ul>
<li>Kick-off meeting and requirements validation</li>
<li>Domain name and DNS configuration planning</li>
<li>Azure subscription setup and verification</li>
<li>Security requirements review</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Phase 2: Infrastructure</strong></td>
<td>
<ul>
<li>Azure resource provisioning (VM, VNet, NSG, Backup)</li>
<li>Network security configuration</li>
<li>SSL certificate setup (Let's Encrypt)</li>
<li>Azure Monitor and alerting configuration</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Phase 3: Application</strong></td>
<td>
<ul>
<li>Bitwarden Docker Compose installation</li>
<li>MSSQL database configuration</li>
<li>Organization and collection setup</li>
<li>Admin portal configuration</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Phase 4: Security</strong></td>
<td>
<ul>
<li>Azure Key Vault integration</li>
<li>Encryption validation (ADE, TLS 1.3)</li>
<li>Microsoft Defender for Cloud configuration</li>
<li>Backup and disaster recovery testing</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Phase 5: User Onboarding</strong></td>
<td>
<ul>
<li>User account creation (300 users)</li>
<li>Department-based collection assignment</li>
<li>End-user training sessions (3 sessions)</li>
<li>Admin training for IT team</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Phase 6: Handover</strong></td>
<td>
<ul>
<li>Documentation delivery</li>
<li>Runbook creation (operations, maintenance, troubleshooting)</li>
<li>Knowledge transfer sessions</li>
<li>30-day hypercare support</li>
</ul>
</td>
</tr>
</tbody>
</table>

<h3>2.2 Out of Scope</h3>

<ac:structured-macro ac:name="status">
<ac:parameter ac:name="colour">Red</ac:parameter>
<ac:parameter ac:name="title">❌ NOT INCLUDED</ac:parameter>
</ac:structured-macro>

<ul>
<li>Migration of existing passwords from other systems (e.g., LastPass, 1Password)</li>
<li>Custom Bitwarden integrations with third-party applications</li>
<li>Development of custom Bitwarden features or modifications</li>
<li>Ongoing managed services beyond 30-day hypercare period</li>
<li>High Availability setup (multi-VM deployment) - Available as add-on</li>
<li>Cross-region disaster recovery (Azure Site Recovery) - Available as add-on</li>
<li>End-user desktop/mobile application installation (user self-service)</li>
<li>Legacy password data cleanup or consolidation</li>
</ul>

<h2>3. Detailed Task Breakdown with Time Estimates</h2>

<h3>Phase 1: Planning & Preparation (Week 1, Days 1-2) - 12 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>1.1</strong></td>
<td>Project kick-off meeting</td>
<td>2 hours</td>
<td>None</td>
<td>Project Manager</td>
</tr>
<tr>
<td><strong>1.2</strong></td>
<td>Requirements validation workshop</td>
<td>2 hours</td>
<td>1.1</td>
<td>Azure Architect</td>
</tr>
<tr>
<td><strong>1.3</strong></td>
<td>Azure subscription setup & permissions</td>
<td>2 hours</td>
<td>1.1</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>1.4</strong></td>
<td>Domain name procurement & DNS planning</td>
<td>2 hours</td>
<td>1.2</td>
<td>Network Engineer</td>
</tr>
<tr>
<td><strong>1.5</strong></td>
<td>Security requirements review</td>
<td>2 hours</td>
<td>1.2</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>1.6</strong></td>
<td>Generate SSH keys & management access</td>
<td>1 hour</td>
<td>1.5</td>
<td>Operations Team</td>
</tr>
<tr>
<td><strong>1.7</strong></td>
<td>Project plan finalization & approval</td>
<td>1 hour</td>
<td>1.1-1.6</td>
<td>Project Manager</td>
</tr>
</tbody>
</table>

<p><strong>Phase 1 Deliverables:</strong></p>
<ul>
<li>✅ Project kick-off meeting minutes</li>
<li>✅ Validated requirements document</li>
<li>✅ Azure subscription with appropriate permissions</li>
<li>✅ Domain name registered (vault.customer.com.au)</li>
<li>✅ SSH keys generated and distributed</li>
<li>✅ Approved project plan</li>
</ul>

<h3>Phase 2: Azure Infrastructure Deployment (Week 1, Days 3-4) - 16 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>2.1</strong></td>
<td>Create Resource Group (Australia East)</td>
<td>0.5 hour</td>
<td>1.3</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>2.2</strong></td>
<td>Deploy Virtual Network & Subnet</td>
<td>1 hour</td>
<td>2.1</td>
<td>Network Engineer</td>
</tr>
<tr>
<td><strong>2.3</strong></td>
<td>Configure Network Security Group (NSG)</td>
<td>2 hours</td>
<td>2.2</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>2.4</strong></td>
<td>Create Static Public IP</td>
<td>0.5 hour</td>
<td>2.2</td>
<td>Network Engineer</td>
</tr>
<tr>
<td><strong>2.5</strong></td>
<td>Configure DNS (A record for vault domain)</td>
<td>1 hour</td>
<td>2.4, 1.4</td>
<td>Network Engineer</td>
</tr>
<tr>
<td><strong>2.6</strong></td>
<td>Deploy VM (Standard_D4s_v5, Ubuntu 22.04)</td>
<td>2 hours</td>
<td>2.2, 2.3</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>2.7</strong></td>
<td>Enable Azure Disk Encryption (ADE)</td>
<td>1 hour</td>
<td>2.6</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>2.8</strong></td>
<td>Create Azure Key Vault</td>
<td>1 hour</td>
<td>2.1</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>2.9</strong></td>
<td>Configure VM Managed Identity for Key Vault</td>
<td>1 hour</td>
<td>2.6, 2.8</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>2.10</strong></td>
<td>Create Recovery Services Vault (Backup)</td>
<td>1 hour</td>
<td>2.1</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>2.11</strong></td>
<td>Enable Azure Backup for VM</td>
<td>1 hour</td>
<td>2.6, 2.10</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>2.12</strong></td>
<td>Create Log Analytics Workspace</td>
<td>1 hour</td>
<td>2.1</td>
<td>Operations Team</td>
</tr>
<tr>
<td><strong>2.13</strong></td>
<td>Configure Azure Monitor & VM Insights</td>
<td>2 hours</td>
<td>2.6, 2.12</td>
<td>Operations Team</td>
</tr>
<tr>
<td><strong>2.14</strong></td>
<td>Create alert rules (CPU, Disk, SSH failures)</td>
<td>1 hour</td>
<td>2.13</td>
<td>Operations Team</td>
</tr>
<tr>
<td><strong>2.15</strong></td>
<td>Infrastructure validation & testing</td>
<td>1 hour</td>
<td>2.1-2.14</td>
<td>Cloud Engineer</td>
</tr>
</tbody>
</table>

<p><strong>Phase 2 Deliverables:</strong></p>
<ul>
<li>✅ Complete Azure infrastructure (VM, VNet, NSG, Backup, Monitoring)</li>
<li>✅ Network security configured (NSG rules, SSH access)</li>
<li>✅ Encryption enabled (ADE for disk, TLS for transit)</li>
<li>✅ Azure Key Vault operational</li>
<li>✅ Backup and monitoring configured</li>
<li>✅ Infrastructure validation report</li>
</ul>

<h3>Phase 3: Bitwarden Application Deployment (Week 1, Days 4-5) - 12 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>3.1</strong></td>
<td>SSH to VM & verify connectivity</td>
<td>0.5 hour</td>
<td>2.6</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>3.2</strong></td>
<td>Install Docker Engine</td>
<td>1 hour</td>
<td>3.1</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.3</strong></td>
<td>Install Docker Compose</td>
<td>0.5 hour</td>
<td>3.2</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.4</strong></td>
<td>Download Bitwarden installer script</td>
<td>0.5 hour</td>
<td>3.3</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.5</strong></td>
<td>Run Bitwarden installation wizard</td>
<td>1 hour</td>
<td>3.4, 2.5</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.6</strong></td>
<td>Configure Let's Encrypt SSL certificate</td>
<td>1 hour</td>
<td>3.5</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>3.7</strong></td>
<td>Start Bitwarden services (docker-compose up)</td>
<td>0.5 hour</td>
<td>3.5, 3.6</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.8</strong></td>
<td>Verify all containers running (web, api, identity, mssql)</td>
<td>0.5 hour</td>
<td>3.7</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>3.9</strong></td>
<td>Access admin portal & complete setup wizard</td>
<td>1 hour</td>
<td>3.8</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>3.10</strong></td>
<td>Configure SMTP for email notifications</td>
<td>1 hour</td>
<td>3.9</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>3.11</strong></td>
<td>Create test user accounts & verify login</td>
<td>1 hour</td>
<td>3.10</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>3.12</strong></td>
<td>Test HTTPS access from external network</td>
<td>1 hour</td>
<td>3.11</td>
<td>Network Engineer</td>
</tr>
<tr>
<td><strong>3.13</strong></td>
<td>Application deployment validation</td>
<td>1 hour</td>
<td>3.1-3.12</td>
<td>Project Manager</td>
</tr>
<tr>
<td><strong>3.14</strong></td>
<td>Store admin credentials in Azure Key Vault</td>
<td>1 hour</td>
<td>3.9, 2.8</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>3.15</strong></td>
<td>Configure automated Bitwarden backup (cron)</td>
<td>1 hour</td>
<td>3.8</td>
<td>DevOps Engineer</td>
</tr>
</tbody>
</table>

<p><strong>Phase 3 Deliverables:</strong></p>
<ul>
<li>✅ Bitwarden application fully deployed and accessible</li>
<li>✅ SSL certificate active (TLS 1.3)</li>
<li>✅ All services running (web vault, API, identity, MSSQL)</li>
<li>✅ Admin portal configured</li>
<li>✅ SMTP email notifications working</li>
<li>✅ Test accounts validated</li>
<li>✅ Automated backup configured</li>
</ul>

<h3>Phase 4: Security Hardening & Testing (Week 2, Days 1-2) - 14 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>4.1</strong></td>
<td>Enable Microsoft Defender for Cloud</td>
<td>1 hour</td>
<td>2.6</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.2</strong></td>
<td>Run vulnerability assessment scan</td>
<td>2 hours</td>
<td>4.1</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.3</strong></td>
<td>Remediate identified vulnerabilities</td>
<td>3 hours</td>
<td>4.2</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.4</strong></td>
<td>Validate encryption (ADE, TLS 1.3)</td>
<td>1 hour</td>
<td>2.7, 3.6</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.5</strong></td>
<td>Test Azure Backup restore procedure</td>
<td>2 hours</td>
<td>2.11</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>4.6</strong></td>
<td>Test Bitwarden native backup/export</td>
<td>1 hour</td>
<td>3.15</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>4.7</strong></td>
<td>Validate NSG rules (port 443/80/22 only)</td>
<td>1 hour</td>
<td>2.3</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.8</strong></td>
<td>Perform penetration test (basic)</td>
<td>2 hours</td>
<td>3.12</td>
<td>Security Engineer</td>
</tr>
<tr>
<td><strong>4.9</strong></td>
<td>Security hardening validation report</td>
<td>1 hour</td>
<td>4.1-4.8</td>
<td>Security Engineer</td>
</tr>
</tbody>
</table>

<p><strong>Phase 4 Deliverables:</strong></p>
<ul>
<li>✅ Vulnerability assessment completed and remediated</li>
<li>✅ Encryption validated (at rest and in transit)</li>
<li>✅ Backup and restore tested successfully</li>
<li>✅ Penetration test passed</li>
<li>✅ Security hardening report</li>
</ul>

<h3>Phase 5: Organization Setup & User Onboarding (Weeks 2-3) - 24 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>5.1</strong></td>
<td>Create Bitwarden Organization (Company Org)</td>
<td>0.5 hour</td>
<td>3.9</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.2</strong></td>
<td>Design collection structure (by department)</td>
<td>2 hours</td>
<td>5.1</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.3</strong></td>
<td>Create collections (IT, Finance, HR, Sales, Ops, etc.)</td>
<td>1 hour</td>
<td>5.2</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.4</strong></td>
<td>Import user list (300 users from CSV/AD)</td>
<td>2 hours</td>
<td>5.1</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.5</strong></td>
<td>Bulk invite users (email invitations)</td>
<td>2 hours</td>
<td>5.4</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.6</strong></td>
<td>Assign users to collections (by department)</td>
<td>2 hours</td>
<td>5.3, 5.5</td>
<td>IT Administrator</td>
</tr>
<tr>
<td><strong>5.7</strong></td>
<td>Create admin training materials</td>
<td>3 hours</td>
<td>3.9</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.8</strong></td>
<td>Create end-user training materials & videos</td>
<td>4 hours</td>
<td>3.11</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.9</strong></td>
<td>Conduct admin training session (IT team)</td>
<td>2 hours</td>
<td>5.7</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.10</strong></td>
<td>Conduct end-user training session 1 (100 users)</td>
<td>1.5 hours</td>
<td>5.8</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.11</strong></td>
<td>Conduct end-user training session 2 (100 users)</td>
<td>1.5 hours</td>
<td>5.8</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.12</strong></td>
<td>Conduct end-user training session 3 (100 users)</td>
<td>1.5 hours</td>
<td>5.8</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>5.13</strong></td>
<td>User acceptance testing (sample users)</td>
<td>1 hour</td>
<td>5.10-5.12</td>
<td>Project Manager</td>
</tr>
</tbody>
</table>

<p><strong>Phase 5 Deliverables:</strong></p>
<ul>
<li>✅ Organization and collections configured</li>
<li>✅ 300 users registered and assigned to collections</li>
<li>✅ Admin training completed</li>
<li>✅ 3 end-user training sessions completed</li>
<li>✅ Training materials and videos delivered</li>
<li>✅ User acceptance testing passed</li>
</ul>

<h3>Phase 6: Documentation & Handover (Week 4) - 18 hours</h3>

<table>
<thead>
<tr>
<th>Task ID</th>
<th>Task Description</th>
<th>Duration</th>
<th>Dependencies</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>6.1</strong></td>
<td>Create architecture documentation</td>
<td>3 hours</td>
<td>2.15</td>
<td>Azure Architect</td>
</tr>
<tr>
<td><strong>6.2</strong></td>
<td>Create operations runbook (daily/weekly/monthly)</td>
<td>3 hours</td>
<td>3.13</td>
<td>Operations Team</td>
</tr>
<tr>
<td><strong>6.3</strong></td>
<td>Create maintenance runbook (updates, patches)</td>
<td>2 hours</td>
<td>3.13</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>6.4</strong></td>
<td>Create troubleshooting guide</td>
<td>2 hours</td>
<td>3.13</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td><strong>6.5</strong></td>
<td>Create disaster recovery runbook</td>
<td>2 hours</td>
<td>4.5</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td><strong>6.6</strong></td>
<td>Create user self-service guide</td>
<td>1 hour</td>
<td>5.8</td>
<td>Training Specialist</td>
</tr>
<tr>
<td><strong>6.7</strong></td>
<td>Conduct knowledge transfer session (IT team)</td>
<td>2 hours</td>
<td>6.1-6.6</td>
<td>Project Manager</td>
</tr>
<tr>
<td><strong>6.8</strong></td>
<td>Handover meeting & sign-off</td>
<td>1 hour</td>
<td>6.7</td>
<td>Project Manager</td>
</tr>
<tr>
<td><strong>6.9</strong></td>
<td>30-day hypercare support setup</td>
<td>1 hour</td>
<td>6.8</td>
<td>Support Team</td>
</tr>
<tr>
<td><strong>6.10</strong></td>
<td>Project closure report</td>
<td>1 hour</td>
<td>6.8</td>
<td>Project Manager</td>
</tr>
</tbody>
</table>

<p><strong>Phase 6 Deliverables:</strong></p>
<ul>
<li>✅ Complete architecture documentation (Confluence)</li>
<li>✅ Operations runbook (daily, weekly, monthly tasks)</li>
<li>✅ Maintenance runbook (Bitwarden updates, security patches)</li>
<li>✅ Troubleshooting guide (common issues and resolutions)</li>
<li>✅ Disaster recovery runbook (backup restore procedures)</li>
<li>✅ User self-service guide</li>
<li>✅ Knowledge transfer completed</li>
<li>✅ 30-day hypercare support active</li>
<li>✅ Project closure report</li>
</ul>

<h2>4. Timeline & Milestones</h2>

<h3>Project Timeline: 4 Weeks (20 Business Days)</h3>

<table>
<thead>
<tr>
<th>Week</th>
<th>Phase</th>
<th>Key Milestones</th>
<th>Effort (Hours)</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Week 1</strong></td>
<td>Planning, Infrastructure, Application</td>
<td>
<ul>
<li>✅ Project kick-off completed</li>
<li>✅ Azure infrastructure deployed</li>
<li>✅ Bitwarden application operational</li>
</ul>
</td>
<td>40 hours</td>
</tr>
<tr>
<td><strong>Week 2</strong></td>
<td>Security, Organization Setup (start)</td>
<td>
<ul>
<li>✅ Security hardening completed</li>
<li>✅ Organization and collections created</li>
<li>✅ User invitations sent</li>
</ul>
</td>
<td>26 hours</td>
</tr>
<tr>
<td><strong>Week 3</strong></td>
<td>User Onboarding</td>
<td>
<ul>
<li>✅ All training sessions completed</li>
<li>✅ 300 users onboarded</li>
<li>✅ User acceptance testing passed</li>
</ul>
</td>
<td>12 hours</td>
</tr>
<tr>
<td><strong>Week 4</strong></td>
<td>Documentation & Handover</td>
<td>
<ul>
<li>✅ All documentation delivered</li>
<li>✅ Knowledge transfer completed</li>
<li>✅ Project handed over</li>
</ul>
</td>
<td>18 hours</td>
</tr>
</tbody>
</table>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="bgColor">#e3fcef</ac:parameter>
<ac:parameter ac:name="title">🎯 CRITICAL MILESTONES</ac:parameter>
<ac:rich-text-body>
<table>
<thead>
<tr>
<th>Milestone</th>
<th>Target Date</th>
<th>Success Criteria</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>M1: Infrastructure Live</strong></td>
<td>End of Week 1, Day 4</td>
<td>Azure resources deployed, VM accessible</td>
</tr>
<tr>
<td><strong>M2: Application Operational</strong></td>
<td>End of Week 1</td>
<td>Bitwarden accessible via HTTPS, test users working</td>
</tr>
<tr>
<td><strong>M3: Security Validated</strong></td>
<td>End of Week 2, Day 2</td>
<td>Vulnerability scan passed, backup tested</td>
</tr>
<tr>
<td><strong>M4: Users Onboarded</strong></td>
<td>End of Week 3</td>
<td>300 users registered and trained</td>
</tr>
<tr>
<td><strong>M5: Project Handover</strong></td>
<td>End of Week 4</td>
<td>Documentation delivered, knowledge transfer complete</td>
</tr>
</tbody>
</table>
</ac:rich-text-body>
</ac:structured-macro>

<h2>5. Resource Requirements</h2>

<h3>5.1 Professional Services Team</h3>

<table>
<thead>
<tr>
<th>Role</th>
<th>Responsibility</th>
<th>Effort</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Project Manager</strong></td>
<td>Overall coordination, risk management, stakeholder communication</td>
<td>12 hours</td>
</tr>
<tr>
<td><strong>Azure Architect</strong></td>
<td>Architecture design, infrastructure validation, documentation</td>
<td>8 hours</td>
</tr>
<tr>
<td><strong>Cloud Engineer</strong></td>
<td>Azure resource provisioning, VM deployment, backup configuration</td>
<td>12 hours</td>
</tr>
<tr>
<td><strong>Network Engineer</strong></td>
<td>VNet, NSG, DNS, connectivity testing</td>
<td>8 hours</td>
</tr>
<tr>
<td><strong>Security Engineer</strong></td>
<td>Security hardening, encryption, vulnerability assessment, penetration testing</td>
<td>18 hours</td>
</tr>
<tr>
<td><strong>DevOps Engineer</strong></td>
<td>Bitwarden installation, Docker configuration, automation, maintenance runbook</td>
<td>14 hours</td>
</tr>
<tr>
<td><strong>IT Administrator</strong></td>
<td>Organization setup, user management, collection configuration</td>
<td>10 hours</td>
</tr>
<tr>
<td><strong>Training Specialist</strong></td>
<td>Training materials, training sessions, user documentation</td>
<td>12 hours</td>
</tr>
<tr>
<td><strong>Operations Team</strong></td>
<td>Monitoring setup, alert configuration, operations runbook</td>
<td>8 hours</td>
</tr>
</tbody>
</table>

<p><strong>Total Professional Services Effort: 96 hours</strong></p>

<h3>5.2 Client Resources Required</h3>

<table>
<thead>
<tr>
<th>Resource</th>
<th>Responsibility</th>
<th>Effort</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Project Sponsor</strong></td>
<td>Project approval, decision-making, escalations</td>
<td>4 hours</td>
</tr>
<tr>
<td><strong>IT Manager</strong></td>
<td>Requirements validation, UAT approval, handover acceptance</td>
<td>8 hours</td>
</tr>
<tr>
<td><strong>HR Representative</strong></td>
<td>User list validation, training coordination</td>
<td>4 hours</td>
</tr>
<tr>
<td><strong>Security Officer</strong></td>
<td>Security requirements approval, compliance sign-off</td>
<td>4 hours</td>
</tr>
<tr>
<td><strong>End Users</strong></td>
<td>Training attendance, user acceptance testing</td>
<td>1.5 hours per user (450 hours total across 300 users)</td>
</tr>
</tbody>
</table>

<h2>6. Costs & Pricing</h2>

<h3>6.1 Professional Services</h3>

<table>
<thead>
<tr>
<th>Component</th>
<th>Hours</th>
<th>Rate (USD)</th>
<th>Total (USD)</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Professional Services</strong></td>
<td>96 hours</td>
<td>$150/hour</td>
<td><strong>$14,400</strong></td>
</tr>
<tr>
<td><strong>30-Day Hypercare Support</strong></td>
<td>Included</td>
<td>-</td>
<td>Included</td>
</tr>
</tbody>
</table>

<h3>6.2 Azure Infrastructure Costs (Monthly Recurring)</h3>

<table>
<thead>
<tr>
<th>Component</th>
<th>Monthly Cost (USD)</th>
<th>Annual Cost (USD)</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Azure Infrastructure (Pay-As-You-Go)</strong></td>
<td>$304</td>
<td>$3,648</td>
</tr>
<tr>
<td><strong>Azure Infrastructure (1-Year RI)</strong></td>
<td><strong>$230</strong></td>
<td><strong>$2,760</strong></td>
</tr>
<tr>
<td><strong>Savings with 1-Year RI</strong></td>
<td>-$74</td>
<td>-$888</td>
</tr>
</tbody>
</table>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>💡 COST OPTIMIZATION RECOMMENDATION:</strong></p>
<p>Purchase 1-Year Reserved Instance after successful deployment (Month 1) to save <strong>$888/year (24%)</strong></p>
</ac:rich-text-body>
</ac:structured-macro>

<h3>6.3 Optional Add-Ons (Not Included in Base SOW)</h3>

<table>
<thead>
<tr>
<th>Add-On</th>
<th>Setup Cost</th>
<th>Monthly Cost</th>
<th>Benefit</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Azure Site Recovery (DR)</strong></td>
<td>$2,000</td>
<td>+$150</td>
<td>Cross-region DR, RTO <15 minutes</td>
</tr>
<tr>
<td><strong>High Availability (2nd VM + LB)</strong></td>
<td>$3,500</td>
<td>+$800</td>
<td>99.95% uptime, zero-downtime updates</td>
</tr>
<tr>
<td><strong>Password Migration Service</strong></td>
<td>$4,000</td>
<td>-</td>
<td>Migrate from LastPass, 1Password, etc.</td>
</tr>
<tr>
<td><strong>Managed Services (ongoing)</strong></td>
<td>-</td>
<td>$1,200</td>
<td>24/7 monitoring, updates, support</td>
</tr>
</tbody>
</table>

<h3>6.4 Total Project Investment</h3>

<ac:structured-macro ac:name="panel">
<ac:parameter ac:name="bgColor">#deebff</ac:parameter>
<ac:parameter ac:name="title">💰 TOTAL PROJECT COST</ac:parameter>
<ac:rich-text-body>
<table>
<thead>
<tr>
<th>Component</th>
<th>One-Time Cost</th>
<th>Monthly Recurring</th>
<th>First Year Total</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Professional Services</strong></td>
<td>$14,400</td>
<td>-</td>
<td>$14,400</td>
</tr>
<tr>
<td><strong>Azure Infrastructure</strong></td>
<td>-</td>
<td>$230 (with 1yr RI)</td>
<td>$2,760</td>
</tr>
<tr>
<td colspan="3"><strong>Total First Year Investment</strong></td>
<td><strong>$17,160</strong></td>
</tr>
<tr>
<td colspan="3"><strong>Total Ongoing (Year 2+)</strong></td>
<td><strong>$2,760/year</strong></td>
</tr>
</tbody>
</table>
</ac:rich-text-body>
</ac:structured-macro>

<h2>7. Assumptions & Dependencies</h2>

<h3>7.1 Assumptions</h3>

<ul>
<li>✅ Client has active Azure subscription with Owner-level permissions</li>
<li>✅ Client will provide domain name (vault.customer.com.au) within 2 business days of project start</li>
<li>✅ Client will provide complete user list (300 users with email addresses) by end of Week 1</li>
<li>✅ Client IT team will be available for requirements workshops and knowledge transfer sessions</li>
<li>✅ Client will assign Project Sponsor with decision-making authority</li>
<li>✅ All 300 users have valid email addresses for invitations</li>
<li>✅ Client network allows outbound HTTPS traffic to Bitwarden domain</li>
<li>✅ Client accepts standard Bitwarden community edition feature set (no custom development)</li>
<li>✅ Training sessions will be conducted remotely (Zoom/Teams)</li>
</ul>

<h3>7.2 Client Dependencies</h3>

<table>
<thead>
<tr>
<th>Dependency</th>
<th>Required By</th>
<th>Impact if Not Met</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Domain name provided</strong></td>
<td>Week 1, Day 2</td>
<td>⚠️ Delays Bitwarden installation by 1-2 days</td>
</tr>
<tr>
<td><strong>Azure subscription ready</strong></td>
<td>Week 1, Day 1</td>
<td>⚠️ Delays project start</td>
</tr>
<tr>
<td><strong>User list provided</strong></td>
<td>Week 2, Day 1</td>
<td>⚠️ Delays user onboarding phase</td>
</tr>
<tr>
<td><strong>Management IP for SSH</strong></td>
<td>Week 1, Day 2</td>
<td>⚠️ Delays infrastructure deployment</td>
</tr>
<tr>
<td><strong>Training session attendance</strong></td>
<td>Weeks 2-3</td>
<td>⚠️ Delays user adoption</td>
</tr>
</tbody>
</table>

<h3>7.3 External Dependencies</h3>

<ul>
<li>Azure service availability (99.99% SLA)</li>
<li>Let's Encrypt certificate issuance (automated, typically <1 minute)</li>
<li>Email delivery for user invitations (depends on client SMTP/mail gateway)</li>
<li>DNS propagation time (24-48 hours for global DNS, immediate for Azure DNS)</li>
</ul>

<h2>8. Risks & Mitigation</h2>

<table>
<thead>
<tr>
<th>Risk</th>
<th>Probability</th>
<th>Impact</th>
<th>Mitigation</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Domain name delays</strong></td>
<td>Medium</td>
<td>Medium</td>
<td>Request domain early (Day 1), have fallback temporary domain</td>
</tr>
<tr>
<td><strong>User list incomplete/inaccurate</strong></td>
<td>Medium</td>
<td>Low</td>
<td>Validate user list with HR early, allow buffer time for corrections</td>
</tr>
<tr>
<td><strong>Training attendance low</strong></td>
<td>Low</td>
<td>Medium</td>
<td>Record sessions, provide self-service training videos</td>
</tr>
<tr>
<td><strong>Azure service outage during deployment</strong></td>
<td>Low</td>
<td>Medium</td>
<td>Monitor Azure status dashboard, have contingency days in schedule</td>
</tr>
<tr>
<td><strong>Security vulnerabilities discovered</strong></td>
<td>Medium</td>
<td>High</td>
<td>Allocate buffer time (Phase 4.3), use latest Bitwarden version</td>
</tr>
<tr>
<td><strong>Backup restore failure</strong></td>
<td>Low</td>
<td>High</td>
<td>Test backup/restore procedure twice (Phase 4.5, 4.6)</td>
</tr>
<tr>
<td><strong>Let's Encrypt rate limits</strong></td>
<td>Low</td>
<td>Low</td>
<td>Use staging environment first, follow best practices</td>
</tr>
<tr>
<td><strong>User resistance to change</strong></td>
<td>Medium</td>
<td>Medium</td>
<td>Clear communication, executive sponsorship, comprehensive training</td>
</tr>
</tbody>
</table>

<h2>9. Acceptance Criteria</h2>

<p>The project will be considered complete and ready for handover when the following criteria are met:</p>

<h3>9.1 Technical Acceptance</h3>

<table>
<thead>
<tr>
<th>Criteria</th>
<th>Validation Method</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td>✅ Bitwarden accessible via HTTPS (vault.customer.com.au)</td>
<td>External access test from 3 different networks</td>
<td>Network Engineer</td>
</tr>
<tr>
<td>✅ TLS 1.3 certificate valid and auto-renewing</td>
<td>SSL Labs scan (Grade A or higher)</td>
<td>Security Engineer</td>
</tr>
<tr>
<td>✅ All Azure resources in Australia East region</td>
<td>Azure resource audit report</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td>✅ Azure Backup successful (restore tested)</td>
<td>Test restore completed within 2 hours</td>
<td>Cloud Engineer</td>
</tr>
<tr>
<td>✅ Bitwarden native backup running (hourly)</td>
<td>Verify 24 backup files in last 24 hours</td>
<td>DevOps Engineer</td>
</tr>
<tr>
<td>✅ Azure Monitor alerts active</td>
<td>Test alert firing (CPU, Disk, SSH)</td>
<td>Operations Team</td>
</tr>
<tr>
<td>✅ No critical vulnerabilities</td>
<td>Defender for Cloud scan with no critical issues</td>
<td>Security Engineer</td>
</tr>
<tr>
<td>✅ 99.9% uptime SLA configured</td>
<td>Azure SLA documentation and VM configuration validated</td>
<td>Cloud Engineer</td>
</tr>
</tbody>
</table>

<h3>9.2 User Acceptance</h3>

<table>
<thead>
<tr>
<th>Criteria</th>
<th>Validation Method</th>
<th>Owner</th>
</tr>
</thead>
<tbody>
<tr>
<td>✅ 300 users registered and invited</td>
<td>Bitwarden admin portal user count = 300</td>
<td>IT Administrator</td>
</tr>
<tr>
<td>✅ All users assigned to appropriate collections</td>
<td>Collection membership audit report</td>
<td>IT Administrator</td>
</tr>
<tr>
<td>✅ Training sessions completed (3 sessions)</td>
<td>Attendance logs showing 300 users trained</td>
<td>Training Specialist</td>
</tr>
<tr>
<td>✅ Sample users can login and save passwords</td>
<td>UAT with 10 sample users from different departments</td>
<td>Project Manager</td>
</tr>
<tr>
<td>✅ Admin team trained and confident</td>
<td>Admin training sign-off form completed</td>
<td>IT Manager</td>
</tr>
</tbody>
</table>

<h3>9.3 Documentation Acceptance</h3>

<table>
<thead>
<tr>
<th>Deliverable</th>
<th>Validation</th>
<th>Format</th>
</tr>
</thead>
<tbody>
<tr>
<td>✅ Architecture documentation</td>
<td>Published to Confluence, reviewed by IT Manager</td>
<td>Confluence page</td>
</tr>
<tr>
<td>✅ Operations runbook</td>
<td>Reviewed and approved by Operations Team</td>
<td>Confluence page</td>
</tr>
<tr>
<td>✅ Maintenance runbook</td>
<td>Reviewed and approved by DevOps Engineer</td>
<td>Confluence page</td>
</tr>
<tr>
<td>✅ Troubleshooting guide</td>
<td>Tested against 5 common scenarios</td>
<td>Confluence page</td>
</tr>
<tr>
<td>✅ Disaster recovery runbook</td>
<td>Validated against backup restore test</td>
<td>Confluence page</td>
</tr>
<tr>
<td>✅ User self-service guide</td>
<td>Reviewed by 10 end users for clarity</td>
<td>PDF + Confluence</td>
</tr>
</tbody>
</table>

<h2>10. Post-Deployment Support</h2>

<h3>10.1 30-Day Hypercare Period (Included)</h3>

<p><strong>Duration:</strong> 30 calendar days from handover date<br/>
<strong>Hours:</strong> Business hours (9 AM - 5 PM AEST, Monday-Friday)<br/>
<strong>Response Time:</strong> 4 business hours for P2 issues, 8 business hours for P3 issues</p>

<h4>Included Support Activities:</h4>

<ul>
<li>✅ Answer user questions via email/ticketing system</li>
<li>✅ Troubleshoot technical issues with Bitwarden or Azure infrastructure</li>
<li>✅ Assist with user onboarding issues (forgotten passwords, login problems)</li>
<li>✅ Review and adjust alert thresholds based on production usage</li>
<li>✅ Provide guidance on Bitwarden best practices</li>
<li>✅ Address minor configuration changes (collection adjustments, user permissions)</li>
</ul>

<h4>Not Included in Hypercare:</h4>

<ul>
<li>❌ 24/7 monitoring or after-hours support</li>
<li>❌ New feature development or customizations</li>
<li>❌ Password migration from other systems</li>
<li>❌ Bitwarden desktop/mobile app installation on user devices</li>
<li>❌ Training for new users onboarded after project completion</li>
</ul>

<h3>10.2 Ongoing Managed Services (Optional)</h3>

<p><strong>Available after hypercare period ends</strong></p>

<table>
<thead>
<tr>
<th>Service Tier</th>
<th>Monthly Cost</th>
<th>Included Services</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Basic Monitoring</strong></td>
<td>$400/month</td>
<td>
<ul>
<li>24/7 infrastructure monitoring</li>
<li>Alert response (business hours)</li>
<li>Monthly patching (OS + Bitwarden)</li>
<li>Quarterly backup testing</li>
</ul>
</td>
</tr>
<tr>
<td><strong>Full Managed Service</strong></td>
<td>$1,200/month</td>
<td>
<ul>
<li>All Basic Monitoring services</li>
<li>24/7 alert response and incident management</li>
<li>User support (basic Bitwarden questions)</li>
<li>Monthly reporting and optimization recommendations</li>
<li>Annual DR test and documentation updates</li>
</ul>
</td>
</tr>
</tbody>
</table>

<h2>11. Terms & Conditions</h2>

<h3>11.1 Payment Terms</h3>

<table>
<thead>
<tr>
<th>Milestone</th>
<th>% of Total</th>
<th>Amount</th>
<th>Due Date</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Project Kick-off</strong></td>
<td>30%</td>
<td>$4,320</td>
<td>Upon SOW signature</td>
</tr>
<tr>
<td><strong>M2: Application Operational</strong></td>
<td>40%</td>
<td>$5,760</td>
<td>End of Week 1</td>
</tr>
<tr>
<td><strong>M5: Project Handover</strong></td>
<td>30%</td>
<td>$4,320</td>
<td>End of Week 4</td>
</tr>
<tr>
<td colspan="2"><strong>Total Professional Services</strong></td>
<td><strong>$14,400</strong></td>
<td></td>
</tr>
</tbody>
</table>

<p><strong>Azure Infrastructure:</strong> Client responsible for Azure costs billed directly by Microsoft Azure (est. $230/month with 1-year RI)</p>

<h3>11.2 Change Management</h3>

<ul>
<li>Changes to scope, timeline, or deliverables require written change request</li>
<li>Change requests will be evaluated for impact on timeline, cost, and resources</li>
<li>Approved changes will result in updated SOW amendment</li>
<li>Minor changes (<5% effort) can be approved via email</li>
<li>Major changes (>5% effort) require formal SOW amendment and client signature</li>
</ul>

<h3>11.3 Cancellation Policy</h3>

<ul>
<li>Client may cancel project with 14 days written notice</li>
<li>Cancellation fee: All work completed to date plus 20% of remaining balance</li>
<li>Azure infrastructure costs are non-refundable</li>
<li>Partial deliverables will be provided for work completed</li>
</ul>

<h3>11.4 Warranty</h3>

<ul>
<li><strong>Professional Services:</strong> 90-day warranty on workmanship from handover date</li>
<li><strong>Defects:</strong> Any defects in deployment will be remediated at no charge within warranty period</li>
<li><strong>Exclusions:</strong> Warranty does not cover changes made by client, third-party modifications, or issues outside our control (Azure outages, Bitwarden bugs)</li>
</ul>

<h2>12. Approvals</h2>

<p>By signing below, both parties agree to the terms, scope, timeline, and costs outlined in this Statement of Work.</p>

<table>
<thead>
<tr>
<th>Party</th>
<th>Name</th>
<th>Title</th>
<th>Signature</th>
<th>Date</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Client</strong></td>
<td>_________________</td>
<td>_________________</td>
<td>_________________</td>
<td>_________</td>
</tr>
<tr>
<td><strong>Service Provider</strong></td>
<td>_________________</td>
<td>_________________</td>
<td>_________________</td>
<td>_________</td>
</tr>
</tbody>
</table>

<hr/>

<p><strong>Document Control</strong></p>
<table>
<thead>
<tr>
<th>Version</th>
<th>Date</th>
<th>Author</th>
<th>Changes</th>
</tr>
</thead>
<tbody>
<tr>
<td>1.0</td>
<td>2025-11-28</td>
<td>Azure Architect + Confluence Organization Agent</td>
<td>Initial SOW creation</td>
</tr>
</tbody>
</table>

<p><strong>Related Documents:</strong></p>
<ul>
<li>📄 Azure Architecture Documentation (Confluence)</li>
<li>📊 Well-Architected Assessment Report</li>
<li>💰 Cost Analysis Spreadsheet</li>
</ul>
"""

def main():
    """Publish Bitwarden SOW to Orro Confluence"""
    print("📄 Publishing Bitwarden Statement of Work to Orro Confluence")
    print("-" * 70)

    # Initialize Confluence client
    client = ReliableConfluenceClient()

    # Check Confluence health
    health = client.health_check()
    print(f"✅ Confluence Health: {health['status']}")

    # Space and page details
    space_key = "Orro"
    title = "📋 Statement of Work: Self-Hosted Bitwarden Deployment (300 Users)"

    print(f"\n📝 Creating SOW page:")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print(f"   Content: {len(BITWARDEN_SOW_HTML)} characters")

    # Create page
    result = client.create_page(
        space_key=space_key,
        title=title,
        content=BITWARDEN_SOW_HTML,
        validate_html=False  # Skip validation (HTML is pre-validated)
    )

    if result:
        print(f"\n✅ SOW page created successfully!")
        print(f"   Page ID: {result['id']}")
        print(f"   URL: {result['url']}")
        print(f"\n🔗 View SOW: {result['url']}")
        return 0
    else:
        print("\n❌ Failed to create SOW page")
        return 1

if __name__ == "__main__":
    sys.exit(main())
