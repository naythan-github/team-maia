#!/usr/bin/env python3
"""
Publish ServiceDesk Tier Analysis to Orro Confluence Space

Uses reliable_confluence_client.py to properly publish content.

Created: 2025-10-27
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from reliable_confluence_client import ReliableConfluenceClient

# Confluence-compatible HTML content
TIER_ANALYSIS_HTML = """
<h1>ServiceDesk Support Tier Analysis (L1/L2/L3)</h1>

<p><strong>Analysis Date:</strong> 2025-10-27<br/>
<strong>Total Tickets Analyzed:</strong> 10,939<br/>
<strong>Categorization Method:</strong> MSP Industry Standards</p>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>CRITICAL FINDING:</strong> Support team is handling 28% more L2 tickets than industry standard</p>
<ul>
<li>2,500-3,000 tickets should be L1 instead of L2</li>
<li>Cost Impact: ~$296K/year opportunity</li>
<li>Resolution Time: L2 tickets take 4x longer than L1</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Executive Summary</h2>

<h3>Current Distribution vs Industry Benchmark</h3>

<table>
<thead>
<tr>
<th>Tier</th>
<th>Current</th>
<th>Industry Benchmark</th>
<th>Status</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>L1</strong> (Help Desk / Service Desk)</td>
<td><strong>33.3%</strong> (3,646 tickets)</td>
<td>60-70%</td>
<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Red</ac:parameter><ac:parameter ac:name="title">27% below benchmark</ac:parameter></ac:structured-macro></td>
</tr>
<tr>
<td><strong>L2</strong> (Technical Support)</td>
<td><strong>63.1%</strong> (6,899 tickets)</td>
<td>25-35%</td>
<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Red</ac:parameter><ac:parameter ac:name="title">28% above benchmark</ac:parameter></ac:structured-macro></td>
</tr>
<tr>
<td><strong>L3</strong> (SME / Engineering)</td>
<td><strong>3.6%</strong> (394 tickets)</td>
<td>5-10%</td>
<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter><ac:parameter ac:name="title">Within benchmark</ac:parameter></ac:structured-macro></td>
</tr>
</tbody>
</table>

<h2>Financial Impact</h2>

<table>
<thead>
<tr>
<th>Scenario</th>
<th>Annual Cost</th>
<th>Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td>Current Cost</td>
<td><strong>$2,101,350</strong></td>
<td>33.3% L1, 63.1% L2, 3.6% L3</td>
</tr>
<tr>
<td>Optimized Cost</td>
<td><strong>$1,805,075</strong></td>
<td>60% L1, 35% L2, 5% L3 (industry benchmark)</td>
</tr>
<tr>
<td><strong>Potential Savings</strong></td>
<td><strong>$296,275/year</strong></td>
<td><strong>14% cost reduction</strong></td>
</tr>
</tbody>
</table>

<h2>Recommended Actions</h2>

<h3>Phase 1: Quick Wins (0-3 months, $20K investment)</h3>
<ul>
<li>L1 Training - Chrome, OneDrive, M365 basics</li>
<li>Password reset self-service portal</li>
<li>Document top 50 L1 issues (knowledge base)</li>
</ul>
<p><strong>Expected Impact:</strong> 500-800 tickets → L1<br/>
<strong>Savings:</strong> $50K/year</p>

<h3>Phase 2: Automation (3-6 months, $50K investment)</h3>
<ul>
<li>SSL expiring alert automation (100+ tickets/quarter)</li>
<li>Patch deployment automation (80+ tickets/quarter)</li>
<li>Azure resource health auto-remediation</li>
</ul>
<p><strong>Expected Impact:</strong> 720 tickets/year automated<br/>
<strong>Savings:</strong> $100K/year</p>

<h3>Phase 3: Self-Service (6-12 months, $80K investment)</h3>
<ul>
<li>Full self-service portal (access, password, config)</li>
<li>AI-powered knowledge base</li>
<li>Chatbot for L1 issues</li>
</ul>
<p><strong>Expected Impact:</strong> 1,500-2,000 tickets/year self-service<br/>
<strong>Savings:</strong> $150K/year</p>

<h2>Staffing Recommendations</h2>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>No Redundancies Required</strong></p>
<p><strong>Recommendation:</strong> Upskill 2 L2 staff to L1 roles (no layoffs)</p>
<p><strong>Additional Savings:</strong> $100-150K/year (L2 → L1 hourly rate difference)</p>
</ac:rich-text-body>
</ac:structured-macro>

<table>
<thead>
<tr>
<th>Tier</th>
<th>Current FTE</th>
<th>Recommended FTE</th>
<th>Change</th>
</tr>
</thead>
<tbody>
<tr>
<td>L1</td>
<td>2-3 FTE</td>
<td>4-5 FTE</td>
<td>+2 (reskilled from L2)</td>
</tr>
<tr>
<td>L2</td>
<td>5-6 FTE</td>
<td>3-4 FTE</td>
<td>-2 (moved to L1)</td>
</tr>
<tr>
<td>L3</td>
<td>1 FTE</td>
<td>1 FTE</td>
<td>No change</td>
</tr>
<tr>
<td><strong>Total</strong></td>
<td><strong>8-10 FTE</strong></td>
<td><strong>8-10 FTE</strong></td>
<td><strong>No headcount change</strong></td>
</tr>
</tbody>
</table>

<h2>Detailed Tier Breakdown</h2>

<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">L1 (Tier 1) - Help Desk / Service Desk (Click to expand)</ac:parameter>
<ac:rich-text-body>
<p><strong>Current:</strong> 3,646 tickets (33.3%)<br/>
<strong>Target:</strong> 6,563-7,657 tickets (60-70%)<br/>
<strong>Gap:</strong> 2,917-4,011 tickets SHORT</p>

<p><strong>What L1 Handles:</strong></p>
<ul>
<li>Password resets, account unlocks</li>
<li>User provisioning (starters/leavers)</li>
<li>Basic email/Outlook issues</li>
<li>Printer support</li>
<li>Simple access requests</li>
<li>SSL expiring alerts (acknowledgment only)</li>
</ul>

<p><strong>Current Distribution by Category:</strong></p>
<ul>
<li>Support Tickets: 39.3% L1 (should be ~60%)</li>
<li>Alert: 21.9% L1 (could be 40%+ with automation)</li>
<li>PHI Support: 52.6% L1 (good coverage)</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">L2 (Tier 2) - Technical Support (Click to expand)</ac:parameter>
<ac:rich-text-body>
<p><strong>Current:</strong> 6,899 tickets (63.1%)<br/>
<strong>Target:</strong> 2,735-3,829 tickets (25-35%)<br/>
<strong>Excess:</strong> 3,070-4,164 tickets TOO MANY</p>

<p><strong>What L2 Handles:</strong></p>
<ul>
<li>Azure/M365 platform support</li>
<li>Network troubleshooting</li>
<li>Server administration</li>
<li>Security incidents</li>
<li>Advanced application issues</li>
<li>VPN/remote access</li>
<li>Backup/recovery operations</li>
</ul>

<ac:structured-macro ac:name="warning">
<ac:rich-text-body>
<p><strong>Problem:</strong> Many "L2" tickets are actually L1-level but escalated due to:</p>
<ul>
<li>L1 skill gaps (Chrome, OneDrive, basic Azure)</li>
<li>Missing knowledge base (no documented procedures)</li>
<li>No self-service (everything requires human)</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>
</ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">L3 (Tier 3) - Subject Matter Experts / Engineering (Click to expand)</ac:parameter>
<ac:rich-text-body>
<p><strong>Current:</strong> 394 tickets (3.6%)<br/>
<strong>Target:</strong> 547-1,094 tickets (5-10%)<br/>
<strong>Status:</strong> Within benchmark (appropriate usage)</p>

<p><strong>What L3 Handles:</strong></p>
<ul>
<li>Infrastructure design</li>
<li>Major outages (Site Down)</li>
<li>Decommissioning projects</li>
<li>Complex database issues</li>
<li>Custom integrations</li>
<li>Vendor escalations</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Supporting Documents</h2>

<p><strong>Excel Reports Available:</strong></p>
<ul>
<li><strong>ServiceDesk_Tier_Analysis_L1_L2_L3.xlsx</strong> (773 KB) - Complete tier analysis with 9 worksheets</li>
<li><strong>ServiceDesk_Semantic_Analysis_Report.xlsx</strong> (1.8 MB) - Semantic insights with 10 worksheets</li>
</ul>

<p><em>Contact Naythan Dawe or Maia System for Excel reports and detailed breakdowns.</em></p>

<hr/>

<p><strong>Analysis Completed:</strong> 2025-10-27<br/>
<strong>Delivered By:</strong> Maia SDM Agent<br/>
<strong>Analyzed Tickets:</strong> 10,939 tickets (100% coverage)</p>
"""


def main():
    print("="*80)
    print("Publishing ServiceDesk Tier Analysis to Orro Confluence Space")
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
    title = "ServiceDesk Support Tier Analysis (L1/L2/L3) - 2025-10-27"

    print(f"📝 Creating Confluence page...")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print()

    try:
        result = client.create_page(
            space_key=space_key,
            title=title,
            content=TIER_ANALYSIS_HTML
        )

        if result:
            print("="*80)
            print("✅ SUCCESS - Page Published to Confluence")
            print("="*80)
            print()
            print(f"Space: {space_key}")
            print(f"Title: {title}")
            print(f"Page ID: {result.get('id', 'Unknown')}")
            print()
            print("📊 View page in Confluence Orro space")
            print()
            return 0
        else:
            print("❌ Failed to create page (no result returned)")
            return 1

    except Exception as e:
        print(f"❌ Error creating page: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
