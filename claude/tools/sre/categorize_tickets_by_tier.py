#!/usr/bin/env python3
"""
ServiceDesk Ticket Tier Categorization (L1/L2/L3)

Categorizes all tickets by support tier following MSP industry standards:
- L1 (Tier 1): Help Desk / Service Desk - First-line support
- L2 (Tier 2): Technical Support - Escalated technical issues
- L3 (Tier 3): Subject Matter Experts - Complex/specialized issues

Industry Standard Tier Definitions:
=====================================

L1 (TIER 1) - Help Desk / Service Desk:
- Password resets and account unlocks
- Basic software troubleshooting (MS Office, browsers, email clients)
- Hardware provisioning and basic troubleshooting
- User provisioning and de-provisioning
- Printer issues and basic network connectivity
- Ticket logging and initial triage
- Knowledge base searches and documented procedures
- Remote assistance for basic issues
- Typical skills: Basic IT support, customer service, documentation
- Resolution time: <30 minutes, 60-70% First Call Resolution (FCR)

L2 (TIER 2) - Technical Support:
- Advanced application troubleshooting
- Network configuration and troubleshooting
- Server administration (basic to intermediate)
- Security incidents (malware, phishing)
- Cloud platform support (Azure, AWS, M365)
- VPN and remote access issues
- Active Directory management
- Backup and recovery operations
- Patch management and deployments
- Typical skills: System administration, networking, cloud platforms
- Resolution time: <4 hours, requires technical expertise

L3 (TIER 3) - Subject Matter Experts / Engineering:
- Complex architecture issues
- Database administration and optimization
- Advanced security incidents (breach response, forensics)
- Infrastructure design and deployment
- Custom development and integrations
- Performance tuning and optimization
- Disaster recovery planning and execution
- Vendor escalations and root cause analysis
- Typical skills: Deep specialization, architecture, development
- Resolution time: Days/weeks, project-based work

Created: 2025-10-27
Author: Maia SDM Agent
"""

import os
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import chromadb
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"


class TierCategorizer:
    """Categorize tickets by support tier (L1/L2/L3) using industry standards"""

    def __init__(self):
        # L1 (Tier 1) patterns - Basic support, high-volume, repeatable
        self.l1_patterns = {
            # Root causes
            'root_causes': [
                'Account',           # User provisioning, password resets
                'User Modifications', # Basic config changes
                'Misc Help/Assistance' # General assistance
            ],

            # Categories (specific types that are typically L1)
            'categories': [
                'Provisioning Fault',
                'Account'
            ],

            # Keywords in title/description (L1 indicators)
            'keywords': [
                'password', 'reset', 'unlock', 'access', 'permission',
                'printer', 'email', 'outlook', 'browser', 'chrome',
                'onsite', 'phone', 'mobile', 'license', 'software install',
                'user account', 'new user', 'offboarding', 'starter',
                'leaver', 'signature', 'auto-reply', 'out of office',
                'basic', 'simple', 'cannot access', 'forgot password',
                'locked out', 'wifi', 'wireless', 'vpn login'
            ],

            # Issue types
            'issue_types': [
                'Password Reset',
                'Account Unlock',
                'User Provisioning',
                'Basic Software Install',
                'Printer Support',
                'Email Client Issues',
                'Browser Issues',
                'Hardware Provisioning'
            ]
        }

        # L2 (Tier 2) patterns - Technical support, requires expertise
        self.l2_patterns = {
            'root_causes': [
                'Software',          # Application troubleshooting
                'Hardware',          # Advanced hardware issues
                'Network',           # Network troubleshooting
                'Telephony',         # Phone system issues
                'Hosted Service',    # Cloud platform issues
                'Security',          # Security incidents
                'Alert'              # System alerts requiring investigation
            ],

            'categories': [
                'Support Tickets',   # General technical support
                'Standard',
                'Install',
                'Equipment',
                'Cloud Firewall',
                'Network',
                'Phone Lines'
            ],

            'keywords': [
                'azure', 'aws', 'cloud', 'm365', 'microsoft 365',
                'active directory', 'ad', 'group policy', 'gpo',
                'server', 'vm', 'virtual machine', 'backup', 'restore',
                'network', 'firewall', 'switch', 'router', 'dns',
                'ssl', 'certificate', 'vpn', 'remote access',
                'patch', 'deployment', 'update', 'configuration',
                'malware', 'virus', 'phishing', 'security',
                'application error', 'database', 'sql', 'api',
                'integration', 'sync', 'onedrive', 'sharepoint',
                'performance', 'slow', 'troubleshoot', 'advanced',
                'cisco', 'meraki', 'monitoring', 'alert'
            ],

            'issue_types': [
                'Azure/Cloud Platform Support',
                'Network Configuration',
                'Server Administration',
                'Security Incidents',
                'Backup/Recovery',
                'Application Troubleshooting',
                'VPN/Remote Access',
                'SSL Certificate Management'
            ]
        }

        # L3 (Tier 3) patterns - Expert-level, complex, architectural
        self.l3_patterns = {
            'root_causes': [
                'AEM',               # Application Engineering/Management
                'Internal',          # Internal infrastructure
                'Administration'     # System administration (advanced)
            ],

            'categories': [
                'Decommission',      # Infrastructure changes
                'Site Down',         # Major outages
                'Information'        # Architecture/planning
            ],

            'keywords': [
                'architecture', 'design', 'infrastructure',
                'migration', 'upgrade', 'deployment', 'implementation',
                'disaster recovery', 'dr', 'high availability', 'ha',
                'load balancing', 'clustering', 'failover',
                'optimization', 'tuning', 'performance analysis',
                'root cause', 'rca', 'forensics', 'investigation',
                'custom development', 'scripting', 'automation',
                'integration', 'api development', 'webhook',
                'vendor escalation', 'manufacturer support',
                'critical', 'outage', 'down', 'unavailable',
                'project', 'planning', 'capacity', 'roadmap',
                'complex', 'advanced', 'expert', 'specialist'
            ],

            'issue_types': [
                'Infrastructure Design',
                'Disaster Recovery',
                'Major Outage Response',
                'Complex Architecture',
                'Performance Optimization',
                'Custom Development',
                'Vendor Escalations'
            ]
        }

    def categorize_ticket(self, ticket: dict) -> str:
        """
        Categorize a single ticket as L1, L2, or L3

        Args:
            ticket: Dictionary with keys: title, description, category, root_cause

        Returns:
            'L1', 'L2', or 'L3'
        """
        title = (ticket.get('title', '') or '').lower()
        description = (ticket.get('description', '') or '').lower()
        category = ticket.get('category', '')
        root_cause = ticket.get('root_cause', '')

        combined_text = f"{title} {description}"

        # Scoring system (higher score = higher tier)
        l1_score = 0
        l2_score = 0
        l3_score = 0

        # Check root cause
        if root_cause in self.l1_patterns['root_causes']:
            l1_score += 3
        if root_cause in self.l2_patterns['root_causes']:
            l2_score += 3
        if root_cause in self.l3_patterns['root_causes']:
            l3_score += 3

        # Check category
        if category in self.l1_patterns['categories']:
            l1_score += 2
        if category in self.l2_patterns['categories']:
            l2_score += 2
        if category in self.l3_patterns['categories']:
            l3_score += 3  # Category is strong indicator for L3

        # Check keywords
        for keyword in self.l1_patterns['keywords']:
            if keyword in combined_text:
                l1_score += 1

        for keyword in self.l2_patterns['keywords']:
            if keyword in combined_text:
                l2_score += 1

        for keyword in self.l3_patterns['keywords']:
            if keyword in combined_text:
                l3_score += 1.5  # Keywords are strong indicators for L3

        # Special cases (override scoring)

        # Alert category logic
        if category == 'Alert':
            # Most alerts are L2 (monitoring, investigation)
            # Unless they're automated/acknowledged (L1)
            if 'ssl expiring' in combined_text or 'patch' in combined_text:
                return 'L1'  # Automated alerts, acknowledgment only
            else:
                return 'L2'  # Requires investigation

        # PHI Support Tickets (application-specific)
        if category == 'PHI Support Tickets':
            # Application support is typically L2
            # Unless it's basic access (L1) or complex development (L3)
            if any(kw in combined_text for kw in ['access', 'account', 'password', 'user']):
                return 'L1'
            elif any(kw in combined_text for kw in ['development', 'custom', 'integration', 'bug']):
                return 'L3'
            else:
                return 'L2'

        # Password/Access patterns (strong L1 indicators)
        if any(kw in combined_text for kw in ['password reset', 'forgot password', 'unlock account', 'cannot access']):
            return 'L1'

        # Major incidents (strong L3 indicators)
        if category == 'Site Down' or 'outage' in combined_text or 'critical' in combined_text:
            return 'L3'

        # Determine tier from scores
        if l3_score >= l2_score and l3_score >= l1_score and l3_score > 3:
            return 'L3'
        elif l1_score >= l2_score and l1_score >= l3_score and l1_score > 2:
            return 'L1'
        else:
            # Default to L2 (most technical support tickets)
            return 'L2'


# ============================================================================
# Helper Functions for main() (Phase 230 Refactoring)
# ============================================================================

def _load_tickets_from_db() -> pd.DataFrame:
    """Load tickets from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        "TKT-Ticket ID" as ticket_id,
        "TKT-Title" as title,
        "TKT-Description" as description,
        "TKT-Solution" as solution,
        "TKT-Category" as category,
        "TKT-Status" as status,
        "TKT-Account Name" as account_name,
        "TKT-Created Time" as created_time,
        "TKT-Closed Time" as closed_time,
        "TKT-Assigned To User" as assigned_to,
        "TKT-Root Cause Category" as root_cause
    FROM tickets
    ORDER BY "TKT-Created Time" DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def _categorize_all_tickets(df: pd.DataFrame, categorizer: TierCategorizer) -> list:
    """Categorize all tickets and return tier list."""
    tiers = []
    for idx, row in df.iterrows():
        ticket = {
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'root_cause': row['root_cause']
        }
        tier = categorizer.categorize_ticket(ticket)
        tiers.append(tier)
        if (idx + 1) % 1000 == 0:
            print(f"   Processed {idx+1:,}/{len(df):,} tickets...")
    return tiers


def _print_tier_breakdown(df: pd.DataFrame, tier_counts: pd.Series) -> None:
    """Print tier breakdown summary."""
    print("="*80)
    print("📊 TIER BREAKDOWN")
    print("="*80)
    print()

    for tier in ['L1', 'L2', 'L3']:
        count = tier_counts.get(tier, 0)
        pct = count / len(df) * 100
        tier_name = {
            'L1': 'Tier 1 (Help Desk / Service Desk)',
            'L2': 'Tier 2 (Technical Support)',
            'L3': 'Tier 3 (Subject Matter Experts / Engineering)'
        }[tier]
        print(f"{tier}: {tier_name}")
        print(f"   Total Tickets: {count:,} ({pct:.1f}%)")
        print()


def _print_tier_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Print and return tier breakdown by category."""
    print("="*80)
    print("📊 TIER BREAKDOWN BY CATEGORY")
    print("="*80)
    print()

    tier_by_category = df.groupby(['category', 'Support_Tier']).size().unstack(fill_value=0)
    tier_by_category['Total'] = tier_by_category.sum(axis=1)
    tier_by_category = tier_by_category.sort_values('Total', ascending=False)

    for category in tier_by_category.index[:10]:
        print(f"{category}:")
        total = tier_by_category.loc[category, 'Total']
        for tier in ['L1', 'L2', 'L3']:
            if tier in tier_by_category.columns:
                count = tier_by_category.loc[category, tier]
                pct = count / total * 100 if total > 0 else 0
                print(f"   {tier}: {count:,} ({pct:.1f}%)")
        print()

    return tier_by_category


def _create_excel_sheets(writer, df: pd.DataFrame, tier_counts: pd.Series, tier_by_category: pd.DataFrame) -> None:
    """Create all Excel worksheets."""
    # Sheet 1: Executive Summary
    summary_data = {
        'Metric': [
            'Total Tickets', 'L1 (Help Desk) Tickets', 'L1 Percentage',
            'L2 (Technical Support) Tickets', 'L2 Percentage',
            'L3 (SME / Engineering) Tickets', 'L3 Percentage', 'Analysis Date'
        ],
        'Value': [
            f"{len(df):,}",
            f"{tier_counts.get('L1', 0):,}",
            f"{tier_counts.get('L1', 0) / len(df) * 100:.1f}%",
            f"{tier_counts.get('L2', 0):,}",
            f"{tier_counts.get('L2', 0) / len(df) * 100:.1f}%",
            f"{tier_counts.get('L3', 0):,}",
            f"{tier_counts.get('L3', 0) / len(df) * 100:.1f}%",
            pd.Timestamp.now().strftime('%Y-%m-%d')
        ]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)

    # Sheet 2: All Tickets with Tier
    df_export = df[['ticket_id', 'title', 'category', 'root_cause', 'Support_Tier',
                   'status', 'account_name', 'created_time', 'assigned_to']].copy()
    df_export.to_excel(writer, sheet_name='All Tickets with Tier', index=False)

    # Sheet 3: Tier Breakdown by Category
    tier_by_category.to_excel(writer, sheet_name='Tier by Category')

    # Sheet 4: Tier Breakdown by Root Cause
    tier_by_root_cause = df.groupby(['root_cause', 'Support_Tier']).size().unstack(fill_value=0)
    tier_by_root_cause['Total'] = tier_by_root_cause.sum(axis=1)
    tier_by_root_cause = tier_by_root_cause.sort_values('Total', ascending=False)
    tier_by_root_cause.to_excel(writer, sheet_name='Tier by Root Cause')

    # Sheet 5: Tier Breakdown by Account
    tier_by_account = df.groupby(['account_name', 'Support_Tier']).size().unstack(fill_value=0)
    tier_by_account['Total'] = tier_by_account.sum(axis=1)
    tier_by_account = tier_by_account.sort_values('Total', ascending=False).head(50)
    tier_by_account.to_excel(writer, sheet_name='Tier by Account (Top 50)')

    # Sheets 6-8: Sample Tickets by Tier
    for tier, sheet_name in [('L1', 'L1 Sample Tickets'), ('L2', 'L2 Sample Tickets'), ('L3', 'L3 Sample Tickets')]:
        samples = df[df['Support_Tier'] == tier][['ticket_id', 'title', 'category', 'root_cause', 'account_name']].head(100)
        samples.to_excel(writer, sheet_name=sheet_name, index=False)

    # Sheet 9: Staffing Recommendations
    staffing_data = {
        'Tier': ['L1', 'L2', 'L3'],
        'Tickets': [tier_counts.get('L1', 0), tier_counts.get('L2', 0), tier_counts.get('L3', 0)],
        'Percentage': [
            f"{tier_counts.get('L1', 0) / len(df) * 100:.1f}%",
            f"{tier_counts.get('L2', 0) / len(df) * 100:.1f}%",
            f"{tier_counts.get('L3', 0) / len(df) * 100:.1f}%"
        ],
        'Industry Benchmark': ['60-70%', '25-35%', '5-10%'],
        'Current vs Benchmark': ['Compare to 60-70%', 'Compare to 25-35%', 'Compare to 5-10%'],
        'Recommended FTE': ['Calculate based on volume'] * 3
    }
    pd.DataFrame(staffing_data).to_excel(writer, sheet_name='Staffing Recommendations', index=False)


def _print_key_insights(df: pd.DataFrame, tier_counts: pd.Series) -> None:
    """Print key insights and recommendations."""
    print("="*80)
    print("🎯 KEY INSIGHTS")
    print("="*80)
    print()

    l1_pct = tier_counts.get('L1', 0) / len(df) * 100
    l2_pct = tier_counts.get('L2', 0) / len(df) * 100
    l3_pct = tier_counts.get('L3', 0) / len(df) * 100

    print(f"Current Distribution:")
    print(f"   L1: {l1_pct:.1f}% (Industry: 60-70%)")
    print(f"   L2: {l2_pct:.1f}% (Industry: 25-35%)")
    print(f"   L3: {l3_pct:.1f}% (Industry: 5-10%)")
    print()

    if l1_pct < 60:
        print(f"⚠️  L1 below industry benchmark ({l1_pct:.1f}% vs 60-70%)")
        print(f"   → Opportunity: Shift more tickets to L1 via automation/training")
    elif l1_pct > 70:
        print(f"✅ L1 above industry benchmark ({l1_pct:.1f}% vs 60-70%)")
        print(f"   → Good L1 deflection, efficient first-line support")

    if l2_pct > 35:
        print(f"⚠️  L2 above industry benchmark ({l2_pct:.1f}% vs 25-35%)")
        print(f"   → Opportunity: Improve L1 FCR, reduce L2 escalations")

    if l3_pct > 10:
        print(f"⚠️  L3 above industry benchmark ({l3_pct:.1f}% vs 5-10%)")
        print(f"   → Opportunity: Improve L2 expertise, reduce L3 escalations")


def main():
    """Categorize ServiceDesk tickets by tier (refactored - Phase 230)."""
    print("📊 Categorizing ServiceDesk Tickets by Support Tier (L1/L2/L3)...\n")

    # Load and categorize tickets
    df = _load_tickets_from_db()
    print(f"✅ Loaded {len(df):,} tickets from database\n")

    categorizer = TierCategorizer()
    print("🔍 Categorizing tickets by tier...")
    df['Support_Tier'] = _categorize_all_tickets(df, categorizer)
    print(f"\n✅ Categorization complete!\n")

    # Get tier counts and display results
    tier_counts = df['Support_Tier'].value_counts()
    _print_tier_breakdown(df, tier_counts)
    tier_by_category = _print_tier_by_category(df)

    # Save to Excel
    print("="*80)
    print("💾 SAVING RESULTS TO EXCEL")
    print("="*80)
    print()

    output_path = MAIA_ROOT / "claude/data/ServiceDesk_Tier_Analysis_L1_L2_L3.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        _create_excel_sheets(writer, df, tier_counts, tier_by_category)

    print(f"✅ Excel report saved: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    print()

    # Print insights
    _print_key_insights(df, tier_counts)


if __name__ == "__main__":
    main()
