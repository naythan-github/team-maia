#!/usr/bin/env python3
"""
Add panel descriptions and help text panels to all ServiceDesk Grafana dashboards
"""

import json
import sys
from pathlib import Path

# Dashboard help text and panel descriptions
DASHBOARD_METADATA = {
    "7_customer_sentiment_team_performance.json": {
        "help_text": """**Dashboard Purpose**: Analyze customer sentiment and team performance using AI-powered sentiment analysis combined with SLA, response time, and quality metrics.

**Key Metrics**:
- **LLM Sentiment Analysis**: Google DeepMind's gemma2:9b model (83% accuracy) analyzes customer comments for positive/negative/neutral/mixed sentiment
- **Team Performance Score**: Composite metric combining SLA compliance (30%), response speed (30%), and positive sentiment rate (40%)
- **Quality Metrics**: AI-powered quality scoring (professionalism, clarity, empathy, actionability)

**Time Range**: July 2025 - Present | **Refresh**: Every 5 minutes

**Use Cases**: Identify top performers, track sentiment trends, improve customer satisfaction, prioritize training needs""",
        "panel_descriptions": {
            "Total Customer-Facing Comments": "Total number of comments visible to customers since July 2025. Excludes internal notes and system-generated comments.",
            "Positive Sentiment Rate (Keyword)": "Legacy keyword-based sentiment detection (32% accuracy). Counts comments containing words like 'thank', 'great', 'excellent'. Superseded by LLM analysis.",
            "Average Team SLA Compliance": "Overall SLA compliance rate across all team members. Target: >95% compliance for optimal customer satisfaction.",
            "Average Comment Quality Score": "AI-powered quality assessment (1.0-3.0 scale) measuring professionalism, clarity, empathy, and actionability. Based on llama3.1:8b analysis.",
            "Ranked Team Performance": "Top 20 team members ranked by composite performance score: SLA (30%) + Speed (30%) + Sentiment (40%). Higher scores indicate better overall performance.",
            "Positive vs Negative Comments by Agent": "Bar chart comparing positive and negative sentiment counts for top 15 agents. Helps identify coaching opportunities and top performers.",
            "Sentiment Trend Over Time": "Stacked area chart showing daily sentiment distribution (positive/neutral/negative) over 94 days. Reveals sentiment patterns and trends.",
            "Quality Score Distribution": "Distribution of quality scores across all comments. Shows percentage of excellent (2.5-3.0), good (2.0-2.5), acceptable (1.5-2.0), and poor (<1.5) responses.",
            "Average Quality by Team Member": "Top 15 team members by average quality score. Highlights best communicators and identifies training needs.",
            "LLM Positive Sentiment Rate": "AI-powered positive sentiment rate using gemma2:9b model (83% accuracy, +51% improvement over keywords). Analyzes actual comment meaning, not just keywords.",
            "LLM Sentiment Distribution": "Pie chart showing sentiment breakdown from LLM analysis: Positive (appreciation/success), Negative (frustration/failure), Neutral (informational/ongoing), Mixed (both positive and negative elements)."
        }
    },
    "1_automation_executive_overview.json": {
        "help_text": """**Dashboard Purpose**: Single-pane executive view of ServiceDesk automation opportunities and potential cost savings.

**Key Metrics**:
- **Total Tickets**: 10,939 tickets analyzed (July-October 2025 baseline)
- **Automation Opportunities**: 4,842 tickets (82.2% of total) identified as automatable
- **Annual Savings Potential**: ~$952K based on $80/hr labor cost, 2-hour average handling time

**Top Quick Wins**:
1. Motion/Sensor Alerts: 960 tickets → $268K/year
2. Access/Permission Requests: 908 tickets → $253K/year
3. Azure Resource Health: 678 tickets → $189K/year

**Use Cases**: Executive reporting, ROI justification, automation prioritization, baseline establishment""",
        "panel_descriptions": {
            "Total Tickets Analyzed": "Total tickets in July-October 2025 baseline period. This establishes the pre-automation baseline for measuring future improvements.",
            "Automation Opportunities": "Tickets identified as automation candidates using pattern matching. Represents potential workload reduction through automation.",
            "Automation Coverage %": "Percentage of tickets that could be automated. Green zone (>70%) indicates high automation potential. Target: 80%+.",
            "Annual Savings Potential": "Estimated annual cost savings from automating identified opportunities. Calculation: automatable tickets × $80/hr × 2hr average × 365-day projection.",
            "Quick Wins (Motion Alerts)": "Highest volume automation opportunity. Motion/sensor alerts are repetitive, rule-based, and ideal for automation.",
            "Status: Pre-Automation": "Current implementation phase. Changes to 'In Progress' or 'Implemented' as automation is deployed.",
            "Ticket Volume Trend (Daily)": "Daily ticket volume over baseline period. Shows workload patterns (spiky, 50-167/day) and helps capacity planning.",
            "Automation Opportunity Trend (Weekly)": "Weekly count of automation candidates. Consistent ~300-400/week indicates stable automation potential.",
            "Top 5 Automation Opportunities": "Highest-value automation targets ranked by volume and estimated savings. Prioritize top patterns for maximum ROI."
        }
    },
    "2_alert_analysis_deepdive.json": {
        "help_text": """**Dashboard Purpose**: Deep-dive analysis of alert patterns for automation scoping and implementation planning.

**Alert Categories** (2,931 total):
- **Motion/Sensor Alerts**: 960 tickets ($268K/year savings potential)
- **Azure Resource Health**: 678 tickets ($189K/year)
- **Patch Deployment Failures**: 555 tickets ($155K/year)
- **Network Connectivity**: 490 tickets ($137K/year)
- **SSL Certificate Expiry**: 248 tickets ($69K/year)

**Use Cases**: Automation requirement gathering, pattern identification, repetitive alert detection, technical scoping""",
        "panel_descriptions": {
            "Motion/Sensor Alerts Time Series": "Daily motion/sensor alert volume. Peaks around 15/day. Highly repetitive pattern ideal for automation.",
            "Patch Deployment Failures Time Series": "Daily patch failure alerts. Predictable pattern following patch deployment schedules.",
            "Azure Resource Health Distribution": "Breakdown of Azure health alert types (VM stopped, network issues, etc.). Helps scope Azure automation requirements.",
            "Network Connectivity Issues": "Network alert patterns over time. Shows outage patterns and helps identify infrastructure issues.",
            "SSL Certificate Expiry Alerts Heatmap": "Day-of-week heatmap showing SSL certificate alert patterns. Enables proactive certificate renewal automation.",
            "Top 10 Repetitive Alerts": "Most frequently recurring alert patterns. High repetition = high automation value.",
            "Alert Category Distribution": "Pie chart showing alert category breakdown. Helps prioritize automation efforts by volume.",
            "Total Alert Tickets": "Total alert-based tickets in baseline period. Establishes alert automation potential.",
            "Estimated Alert Automation ROI": "Projected annual savings from automating all alert handling. Based on volume × $80/hr × 1.5hr average."
        }
    },
    "3_support_pattern_analysis.json": {
        "help_text": """**Dashboard Purpose**: Analyze support request patterns for automation opportunity identification and complexity assessment.

**Support Categories** (1,849 total):
- **Access/Permission Requests**: 908 tickets ($253K/year) - High automation potential
- **Email/Mailbox Issues**: 526 tickets ($147K/year) - Medium complexity
- **Password Reset Requests**: 196 tickets ($55K/year) - Low complexity, quick win
- **Software Installation**: 125 tickets ($35K/year) - Medium complexity
- **License/Activation**: 94 tickets ($26K/year) - Medium automation potential

**Use Cases**: Support automation scoping, self-service portal design, workflow automation planning, complexity assessment""",
        "panel_descriptions": {
            "Access/Permission Requests Trend": "Daily access request volume. Consistent pattern indicates stable automation opportunity.",
            "Email Issues Distribution": "Breakdown of email problem types (mailbox full, send/receive issues). Helps design email troubleshooting automation.",
            "Password Reset Trend": "Password reset request volume over time. Classic automation target - predictable, rule-based, high volume.",
            "Software Installation Complexity": "Installation request patterns and complexity indicators. Some automatable via SCCM/Intune, others require manual intervention.",
            "License/Activation Issues": "License-related support tickets. Partial automation potential (license checking, key distribution).",
            "Support Pattern Distribution": "Pie chart showing support category breakdown by volume. Prioritize largest slices for automation.",
            "Total Support Tickets": "Total support request tickets. Establishes support automation baseline.",
            "Support Automation Recommendations": "Table listing patterns with automation complexity ratings (Low/Medium/High) and estimated effort."
        }
    },
    "4_team_performance_tasklevel.json": {
        "help_text": """**Dashboard Purpose**: Analyze team workload distribution, performance metrics, and identify bottlenecks.

**Key Findings**:
- **PendingAssignment Backlog**: 3,131 tickets (28.6%) - Critical bottleneck requiring attention
- **Resolution Time Improvement**: 75% faster (5.3 days → 1.09 days, July→October)
- **Task Distribution**: 41.4% Communications, 25% Administration, 31.9% Technical, 1.8% Expert
- **Top Performer**: Robert Quito (1,002 tickets, 88.9% close rate)

**Use Cases**: Workload balancing, performance evaluation, bottleneck identification, capacity planning""",
        "panel_descriptions": {
            "Tickets by Assignee": "Bar chart showing ticket distribution across team members. Helps identify workload imbalances.",
            "Task Distribution by Type": "Pie chart of ticket categories (Comms/Admin/Technical/Expert). Shows skill requirements and workload composition.",
            "Top Performers by Close Rate": "Team members ranked by successful ticket closure rate. Highlights efficient resolvers.",
            "Tickets in PendingAssignment": "Backlog of unassigned tickets (3,131 = 28.6%). Critical metric - high values indicate assignment bottleneck.",
            "Resolution Time Trend": "Average ticket resolution time over period. Shows 75% improvement (5.3 → 1.09 days).",
            "Workload Heatmap": "Day-of-week × hour-of-day heatmap showing peak ticket volumes. Helps scheduling and capacity planning.",
            "Team Performance Table": "Detailed table with tickets handled, close rate, avg resolution time per team member.",
            "Task Complexity Distribution": "Breakdown of task complexity levels. Helps assess skill requirements and training needs."
        }
    },
    "5_improvement_tracking_roi.json": {
        "help_text": """**Dashboard Purpose**: Track automation implementation progress and measure ROI against baseline metrics.

**Baseline Period**: July-October 2025 (pre-automation)
**Status**: Currently showing baseline metrics - will update as automation is deployed

**Tracked Metrics**:
- Ticket volume reduction (automation vs manual handling)
- Resolution time improvements
- Cost savings (actual vs estimated)
- Automation deployment dates and effectiveness

**Use Cases**: ROI validation, automation effectiveness tracking, before/after comparison, executive reporting""",
        "panel_descriptions": {
            "Baseline Total Tickets": "Pre-automation baseline ticket volume (10,939). Reference point for measuring automation impact.",
            "Baseline Automation Opportunities": "Pre-automation automatable ticket count (4,842). Target for automation deployment.",
            "Baseline Annual Cost": "Estimated annual cost without automation (~$952K). Benchmark for savings calculation.",
            "Ticket Volume Before/After": "Time-series comparing ticket volumes before and after automation. Shows automation effectiveness.",
            "Resolution Time Before/After": "Average resolution time comparison. Measures efficiency gains from automation.",
            "Cost Savings Trend": "Cumulative cost savings from automation over time. Tracks ROI realization.",
            "Automation Deployment Timeline": "Annotations showing when each automation was deployed. Links deployments to metric changes.",
            "Actual vs Estimated Savings": "Comparison of projected savings vs actual measured savings. Validates business case.",
            "Post-Automation Status": "Current automation implementation status. Updates as automations are deployed.",
            "ROI by Automation Type": "Breakdown of ROI by automation category (alerts, access, patches, etc.). Identifies highest-performing automations.",
            "Baseline vs Current Metrics Table": "Side-by-side comparison of baseline and current metrics. Shows before/after impact.",
            "Next Automation Priorities": "Recommended next automation targets based on ROI potential and complexity.",
            "Automation Coverage Progress": "Gauge showing percentage of automation opportunities implemented. Target: 80%+ coverage."
        }
    },
    "6_incident_classification_breakdown.json": {
        "help_text": """**Dashboard Purpose**: Classify and analyze incidents by technology stack (Cloud, Telecommunications, Networking) for targeted automation and resource allocation.

**Classification Breakdown** (6,903 incidents):
- **Cloud**: 78.56% (5,424 incidents) - File shares, Azure, Office 365
- **Telecommunications**: 18.56% (1,281 incidents) - Calling issues, mobile, conferencing
- **Networking**: 2.88% (199 incidents) - VPN, switches, connectivity

**Key Insights**:
- File share issues (738) dominate Cloud category
- Calling problems (98.22%) dominate Telecommunications
- VPN issues (51.58%) lead Networking category

**Use Cases**: Technology-specific automation planning, vendor management, infrastructure investment prioritization""",
        "panel_descriptions": {
            "Primary Classification Distribution": "Pie chart showing Cloud/Telecom/Networking breakdown. Shows technology stack focus areas.",
            "Total Incidents Classified": "Total incidents analyzed and classified. Establishes classification baseline.",
            "Cloud Incidents": "Total cloud-related incidents (Azure, Office 365, file shares). Largest category at 78.56%.",
            "Telecommunications Incidents": "Total telecom incidents (calling, mobile, conferencing). Second-largest at 18.56%.",
            "Networking Incidents": "Total networking incidents (VPN, switches, connectivity). Smallest category at 2.88%.",
            "Cloud Sub-Categories": "Breakdown of cloud incident types. File shares (738) is highest, indicating storage automation opportunity.",
            "Telecommunications Sub-Categories": "Telecom incident breakdown. Calling issues dominate (98.22%) - potential for vendor escalation automation.",
            "Networking Sub-Categories": "Network incident types. VPN (51.58%) highest - opportunity for VPN troubleshooting automation.",
            "Incident Trend by Classification": "Time-series showing incident volumes by category over time. Reveals seasonal patterns.",
            "Recent Cloud Incidents": "Latest cloud incidents for quick review. Helps identify emerging issues.",
            "Recent Telecom Incidents": "Latest telecom tickets. Useful for trend spotting and vendor issue tracking.",
            "Recent Networking Incidents": "Latest network issues. Helps infrastructure team prioritize work."
        }
    }
}

def add_help_panel(dashboard_data, help_text):
    """Add a text panel at the top of the dashboard with help information"""

    # Shift all existing panels down by 4 rows to make room for help panel
    for panel in dashboard_data['dashboard']['panels']:
        if 'gridPos' in panel:
            panel['gridPos']['y'] += 4

    # Create help panel
    help_panel = {
        "id": 999,  # Use high ID to avoid conflicts
        "type": "text",
        "title": "📘 Dashboard Guide",
        "gridPos": {"h": 4, "w": 24, "x": 0, "y": 0},
        "options": {
            "mode": "markdown",
            "content": help_text
        },
        "transparent": False,
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        }
    }

    # Insert at the beginning
    dashboard_data['dashboard']['panels'].insert(0, help_panel)

    return dashboard_data

def add_panel_descriptions(dashboard_data, panel_descriptions):
    """Add description field to panels based on their title"""

    for panel in dashboard_data['dashboard']['panels']:
        if panel.get('type') == 'row':
            continue  # Skip row panels

        title = panel.get('title', '')
        if title in panel_descriptions:
            panel['description'] = panel_descriptions[title]

    return dashboard_data

def process_dashboard(filepath, metadata):
    """Process a single dashboard file"""

    print(f"Processing {filepath.name}...")

    # Read dashboard JSON
    with open(filepath, 'r') as f:
        dashboard_data = json.load(f)

    # Add help panel
    dashboard_data = add_help_panel(dashboard_data, metadata['help_text'])

    # Add panel descriptions
    dashboard_data = add_panel_descriptions(dashboard_data, metadata['panel_descriptions'])

    # Write back
    with open(filepath, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"  ✅ Added help panel and {len(metadata['panel_descriptions'])} panel descriptions")

def main():
    dashboard_dir = Path("/Users/naythandawe/git/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards")

    if not dashboard_dir.exists():
        print(f"❌ Dashboard directory not found: {dashboard_dir}")
        sys.exit(1)

    print("🚀 Adding help panels and descriptions to dashboards...\n")

    processed = 0
    for filename, metadata in DASHBOARD_METADATA.items():
        filepath = dashboard_dir / filename

        if not filepath.exists():
            print(f"⚠️  Skipping {filename} (not found)")
            continue

        try:
            process_dashboard(filepath, metadata)
            processed += 1
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n✅ Processed {processed}/{len(DASHBOARD_METADATA)} dashboards")
    print("\n📊 Next steps:")
    print("1. Re-import dashboards: ./scripts/import_dashboards.sh")
    print("2. Open Grafana: http://localhost:3000")
    print("3. Hover over panel titles to see descriptions (ℹ️ icon)")
    print("4. View dashboard help panel at the top of each dashboard")

if __name__ == "__main__":
    main()
