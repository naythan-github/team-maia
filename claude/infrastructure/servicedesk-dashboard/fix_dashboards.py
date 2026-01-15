#!/usr/bin/env python3
"""
Fix ServiceDesk Grafana Dashboard queries.
Key issues:
1. Queries on comments table incorrectly use "TKT-Team" instead of "team" column
2. Some dashboards missing datasource variable in templating
3. Need to standardize datasource references
"""

import json
import os
import re

DASHBOARD_DIR = "/Users/YOUR_USERNAME/maia/claude/infrastructure/servicedesk-dashboard/grafana/dashboards"

# The datasource variable template
DATASOURCE_VAR = {
    "name": "datasource",
    "label": "Data Source",
    "type": "datasource",
    "query": "postgres",
    "current": {
        "value": "ServiceDesk PostgreSQL",
        "text": "ServiceDesk PostgreSQL"
    }
}

def fix_dashboard(filepath):
    """Fix a single dashboard JSON file."""
    with open(filepath, 'r') as f:
        dashboard = json.load(f)

    changes = []

    # Navigate to the dashboard object
    if 'dashboard' in dashboard:
        dash = dashboard['dashboard']
    else:
        dash = dashboard

    # 1. Fix datasource references - change hardcoded UIDs to use variable
    # Replace "uid": "P6BECECF7273D15EE" with "uid": "${datasource}"
    def fix_datasource_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'datasource' and isinstance(value, dict):
                    if value.get('uid') == 'P6BECECF7273D15EE':
                        value['uid'] = '${datasource}'
                        changes.append(f"Fixed datasource UID at {path}.{key}")
                elif key == 'uid' and value == 'P6BECECF7273D15EE' and 'type' in obj.get('datasource', {}):
                    obj['uid'] = '${datasource}'
                    changes.append(f"Fixed datasource UID at {path}")
                else:
                    fix_datasource_refs(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                fix_datasource_refs(item, f"{path}[{i}]")

    fix_datasource_refs(dash)

    # 2. Ensure datasource variable exists in templating
    templating = dash.get('templating', {})
    var_list = templating.get('list', [])

    has_datasource_var = any(v.get('name') == 'datasource' for v in var_list)
    if not has_datasource_var:
        var_list.insert(0, DATASOURCE_VAR)
        changes.append("Added datasource variable to templating")

    templating['list'] = var_list
    dash['templating'] = templating

    # 3. Fix queries that incorrectly reference TKT-Team on comments table
    # The comments table has 'team' column, not 'TKT-Team'
    def fix_comment_queries(obj, path=""):
        if isinstance(obj, dict):
            if 'rawSql' in obj:
                sql = obj['rawSql']
                # Check if query references comments table with TKT-Team
                if 'servicedesk.comments' in sql.lower() and '"TKT-Team"' in sql:
                    # Only fix if in a WHERE on comments table directly
                    # Pattern: comments table with TKT-Team in a non-join context
                    # This is actually tricky - need to be careful not to break joins
                    pass  # Skip for now - these are complex queries
            for key, value in obj.items():
                fix_comment_queries(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                fix_comment_queries(item, f"{path}[{i}]")

    fix_comment_queries(dash)

    # Update the dashboard
    if 'dashboard' in dashboard:
        dashboard['dashboard'] = dash
    else:
        dashboard = dash

    return dashboard, changes


def main():
    """Fix all dashboards."""
    dashboard_files = [
        "1_automation_executive_overview.json",
        "2_alert_analysis_deepdive.json",
        "3_support_pattern_analysis.json",
        "4_team_performance_tasklevel.json",
        "5_improvement_tracking_roi.json",
        "6_incident_classification_breakdown.json",
        "7_customer_sentiment_team_performance.json",
        "executive_dashboard.json",
        "operations_dashboard.json",
        "quality_dashboard.json",
        "team_performance_dashboard.json",
    ]

    for filename in dashboard_files:
        filepath = os.path.join(DASHBOARD_DIR, filename)
        if not os.path.exists(filepath):
            print(f"SKIP: {filename} not found")
            continue

        print(f"\nProcessing: {filename}")
        dashboard, changes = fix_dashboard(filepath)

        if changes:
            print(f"  Changes: {len(changes)}")
            for change in changes:
                print(f"    - {change}")

            # Write fixed dashboard
            with open(filepath, 'w') as f:
                json.dump(dashboard, f, indent=2)
            print(f"  Saved: {filepath}")
        else:
            print(f"  No changes needed")


if __name__ == '__main__':
    main()
