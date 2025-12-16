#!/usr/bin/env python3
"""
Publish ServiceDesk Tier Analysis to Confluence

Creates Confluence pages in Orro space with tier analysis findings.

Created: 2025-10-27
Author: Maia SDM Agent
"""

import sys
import subprocess
import tempfile
from pathlib import Path

MAIA_ROOT = Path(__file__).resolve().parents[3]

# Tier Analysis Summary (Confluence-compatible HTML)
TIER_ANALYSIS_CONTENT = """
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

<h3>Cost Analysis</h3>

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

<h2>Tier Breakdown</h2>

<h3>L1 (Tier 1) - Help Desk / Service Desk</h3>
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

<h3>L2 (Tier 2) - Technical Support</h3>
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

<h3>L3 (Tier 3) - Subject Matter Experts / Engineering</h3>
<p><strong>Current:</strong> 394 tickets (3.6%)<br/>
<strong>Target:</strong> 547-1,094 tickets (5-10%)<br/>
<strong>Status:</strong> <ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter><ac:parameter ac:name="title">Within benchmark</ac:parameter></ac:structured-macro></p>

<p><strong>What L3 Handles:</strong></p>
<ul>
<li>Infrastructure design</li>
<li>Major outages (Site Down)</li>
<li>Decommissioning projects</li>
<li>Complex database issues</li>
<li>Custom integrations</li>
<li>Vendor escalations</li>
</ul>

<h2>Recommended Actions</h2>

<h3>Phase 1: Quick Wins (0-3 months, $20K)</h3>
<ul>
<li>L1 Training - Chrome, OneDrive, M365 basics</li>
<li>Password reset self-service portal</li>
<li>Document top 50 L1 issues (knowledge base)</li>
</ul>
<p><strong>Expected:</strong> 500-800 tickets → L1 | <strong>Savings:</strong> $50K/year</p>

<h3>Phase 2: Automation (3-6 months, $50K)</h3>
<ul>
<li>SSL expiring alert automation (100+ tickets/quarter)</li>
<li>Patch deployment automation (80+ tickets/quarter)</li>
<li>Azure resource health auto-remediation</li>
</ul>
<p><strong>Expected:</strong> 720 tickets/year automated | <strong>Savings:</strong> $100K/year</p>

<h3>Phase 3: Self-Service (6-12 months, $80K)</h3>
<ul>
<li>Full self-service portal (access, password, config)</li>
<li>AI-powered knowledge base</li>
<li>Chatbot for L1 issues</li>
</ul>
<p><strong>Expected:</strong> 1,500-2,000 tickets/year self-service | <strong>Savings:</strong> $150K/year</p>

<h3>Phase 4: Optimization (12+ months, $30K/year)</h3>
<ul>
<li>Continuous improvement</li>
<li>Monthly tier monitoring</li>
<li>L1 FCR at 70%</li>
</ul>
<p><strong>Expected:</strong> Full optimization | <strong>Savings:</strong> $296K/year</p>

<h2>Staffing Recommendations</h2>

<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>No Redundancies Required</strong></p>
<p>Recommendation: <strong>Upskill 2 L2 staff to L1 roles</strong> (no layoffs)</p>
<p>Additional Savings: $100-150K/year (L2 → L1 hourly rate difference)</p>
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

<h2>Attachments</h2>

<p><strong>Excel Reports Available:</strong></p>
<ul>
<li><strong>ServiceDesk_Tier_Analysis_L1_L2_L3.xlsx</strong> (773 KB) - Complete tier analysis with 9 worksheets</li>
<li><strong>ServiceDesk_Semantic_Analysis_Report.xlsx</strong> (1.8 MB) - Semantic insights with 10 worksheets</li>
</ul>

<p><em>Contact Naythan Dawe or Maia System for Excel reports and detailed breakdowns.</em></p>

<h2>Next Steps</h2>

<ol>
<li><strong>This Week:</strong> Review tier analysis findings with leadership</li>
<li><strong>Month 1:</strong> Approve Phase 1 budget ($20K) and schedule L1 training</li>
<li><strong>Months 2-6:</strong> Implement automation (Phase 2) and self-service portal (Phase 3)</li>
<li><strong>6-12 months:</strong> Achieve full optimization (60% L1, 35% L2, 5% L3)</li>
</ol>

<p><strong>Analysis Completed:</strong> 2025-10-27<br/>
<strong>Delivered By:</strong> Maia SDM Agent</p>
"""

def create_confluence_page(space_key: str, title: str, content: str, parent_id: str = None):
    """Create Confluence page using reliable_confluence_client.py"""

    # Save content to temp file (B108: use tempfile.gettempdir() for portability)
    content_file = Path(tempfile.gettempdir()) / "confluence_tier_analysis_content.html"
    with open(content_file, 'w') as f:
        f.write(content)

    # Build command
    cmd = [
        'python3',
        str(MAIA_ROOT / 'claude/tools/reliable_confluence_client.py'),
        'create-page',
        '--space', space_key,
        '--title', title,
        '--content-file', str(content_file)
    ]

    if parent_id:
        cmd.extend(['--parent-id', parent_id])

    print(f"📝 Creating Confluence page: '{title}' in space '{space_key}'")
    print(f"   Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Page created successfully!")
        print(result.stdout)
        return True
    else:
        print(f"❌ Error creating page:")
        print(result.stderr)
        return False


def main():
    print("="*80)
    print("Publishing ServiceDesk Tier Analysis to Confluence")
    print("="*80)
    print()

    # Publish to Orro space
    space_key = "Orro"
    title = "ServiceDesk Support Tier Analysis (L1/L2/L3) - 2025-10-27"

    success = create_confluence_page(
        space_key=space_key,
        title=title,
        content=TIER_ANALYSIS_CONTENT
    )

    if success:
        print()
        print("="*80)
        print("✅ PUBLICATION COMPLETE")
        print("="*80)
        print()
        print(f"Page published to Confluence space: {space_key}")
        print(f"Page title: {title}")
        print()
        print("🔗 View in Confluence: https://orrogroup.atlassian.net/wiki/spaces/Orro")
    else:
        print()
        print("❌ Publication failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
