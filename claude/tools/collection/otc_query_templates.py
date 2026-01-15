"""
OTC ServiceDesk pre-built query templates.

Part of P3: Pre-built SQL Query Templates
Provides common queries for team workload, user activity, and ticket analysis.

Usage:
    from claude.tools.collection.otc_query_templates import execute_template, describe_templates

    # List available templates
    print(describe_templates())

    # Execute a template
    from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService
    service = OTCIntelligenceService()
    result = execute_template("team_workload", {"team_name": "Cloud - Infrastructure"}, service)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result of a query execution."""
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    error: Optional[str] = None


# Template Registry
# Each template has: description, parameters (list), sql (parameterized query)
TEMPLATES = {
    # ===== Team Queries =====
    "team_workload": {
        "description": "Open/closed/unassigned ticket counts by team",
        "parameters": ["team_name"],
        "sql": """
            SELECT
                status,
                COUNT(*) as ticket_count
            FROM tickets
            WHERE team = %s
            GROUP BY status
            ORDER BY
                CASE status
                    WHEN 'Open' THEN 1
                    WHEN 'PendingAssignment' THEN 2
                    WHEN 'InProgress' THEN 3
                    WHEN 'Closed' THEN 4
                    ELSE 5
                END
        """
    },

    "team_backlog": {
        "description": "Unassigned tickets per team",
        "parameters": ["team_name"],
        "sql": """
            SELECT
                ticket_id,
                title,
                priority,
                created_date,
                DATEDIFF(CURRENT_DATE, created_date) as age_days
            FROM tickets
            WHERE team = %s
              AND status = 'PendingAssignment'
            ORDER BY priority DESC, created_date ASC
        """
    },

    "engineering_summary": {
        "description": "All 3 engineering queues summary",
        "parameters": [],
        "sql": """
            SELECT
                team,
                status,
                COUNT(*) as ticket_count
            FROM tickets
            WHERE team IN ('Cloud - Infrastructure', 'Cloud - Security', 'Cloud - Governance')
            GROUP BY team, status
            ORDER BY team,
                CASE status
                    WHEN 'Open' THEN 1
                    WHEN 'PendingAssignment' THEN 2
                    WHEN 'InProgress' THEN 3
                    WHEN 'Closed' THEN 4
                    ELSE 5
                END
        """
    },

    # ===== User Queries =====
    "user_workload": {
        "description": "User's open tickets with age",
        "parameters": ["user_name"],
        "sql": """
            SELECT
                ticket_id,
                title,
                priority,
                status,
                team,
                created_date,
                DATEDIFF(CURRENT_DATE, created_date) as age_days
            FROM tickets
            WHERE assignee = %s
              AND status NOT IN ('Closed', 'Incident Resolved')
            ORDER BY priority DESC, created_date ASC
        """
    },

    "user_activity": {
        "description": "30-day activity summary for a user",
        "parameters": ["user_name"],
        "sql": """
            SELECT
                status,
                COUNT(*) as ticket_count
            FROM tickets
            WHERE assignee = %s
              AND created_date > CURRENT_DATE - INTERVAL '30 days'
            GROUP BY status
            ORDER BY
                CASE status
                    WHEN 'Closed' THEN 1
                    WHEN 'Incident Resolved' THEN 2
                    WHEN 'InProgress' THEN 3
                    WHEN 'Open' THEN 4
                    ELSE 5
                END
        """
    },

    "user_hours": {
        "description": "Timesheet hours per user (last 30 days)",
        "parameters": ["user_name"],
        "sql": """
            SELECT
                DATE(work_date) as date,
                SUM(hours) as total_hours,
                COUNT(DISTINCT ticket_id) as tickets_worked
            FROM timesheets
            WHERE worker = %s
              AND work_date > CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(work_date)
            ORDER BY date DESC
        """
    },

    # ===== Ticket Analysis Queries =====
    "ticket_age_distribution": {
        "description": "Tickets by age bucket (0-7d, 7-30d, 30+d)",
        "parameters": ["team_name"],
        "sql": """
            SELECT
                CASE
                    WHEN DATEDIFF(CURRENT_DATE, created_date) < 7 THEN '0-7 days'
                    WHEN DATEDIFF(CURRENT_DATE, created_date) < 30 THEN '7-30 days'
                    ELSE '30+ days'
                END as age_bucket,
                COUNT(*) as ticket_count,
                AVG(DATEDIFF(CURRENT_DATE, created_date)) as avg_age_days
            FROM tickets
            WHERE team = %s
              AND status NOT IN ('Closed', 'Incident Resolved')
            GROUP BY age_bucket
            ORDER BY
                CASE age_bucket
                    WHEN '0-7 days' THEN 1
                    WHEN '7-30 days' THEN 2
                    ELSE 3
                END
        """
    },

    "open_tickets_by_priority": {
        "description": "Open tickets grouped by severity/priority",
        "parameters": ["team_name"],
        "sql": """
            SELECT
                priority,
                COUNT(*) as ticket_count,
                AVG(DATEDIFF(CURRENT_DATE, created_date)) as avg_age_days
            FROM tickets
            WHERE team = %s
              AND status NOT IN ('Closed', 'Incident Resolved')
            GROUP BY priority
            ORDER BY
                CASE priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                    ELSE 5
                END
        """
    },

    "recent_tickets": {
        "description": "Tickets created in last N days",
        "parameters": ["team_name", "days"],
        "sql": """
            SELECT
                ticket_id,
                title,
                priority,
                status,
                assignee,
                created_date
            FROM tickets
            WHERE team = %s
              AND created_date > CURRENT_DATE - INTERVAL '%s days'
            ORDER BY created_date DESC
        """
    },

    # ===== Quality/Audit Queries =====
    "orphaned_data_summary": {
        "description": "Count of orphaned comments/timesheets (tickets not in main table)",
        "parameters": [],
        "sql": """
            SELECT 'orphaned_comments' AS type, COUNT(*) as count
            FROM comments c
            LEFT JOIN tickets t ON c.ticket_id = t.ticket_id
            WHERE t.ticket_id IS NULL

            UNION ALL

            SELECT 'orphaned_timesheets' AS type, COUNT(*) as count
            FROM timesheets ts
            LEFT JOIN tickets t ON ts.ticket_id = t.ticket_id
            WHERE t.ticket_id IS NULL
        """
    },
}


def describe_templates() -> str:
    """
    Return human-readable summary of all available templates.

    Returns:
        Markdown-formatted string describing all templates.
    """
    lines = ["# OTC ServiceDesk Query Templates", ""]

    # Group templates by category
    categories = {
        "Team Queries": ["team_workload", "team_backlog", "engineering_summary"],
        "User Queries": ["user_workload", "user_activity", "user_hours"],
        "Ticket Analysis": ["ticket_age_distribution", "open_tickets_by_priority", "recent_tickets"],
        "Quality/Audit": ["orphaned_data_summary"],
    }

    for category, template_names in categories.items():
        lines.append(f"## {category}")
        lines.append("")

        for name in template_names:
            if name in TEMPLATES:
                template = TEMPLATES[name]
                params_str = ", ".join(template["parameters"]) if template["parameters"] else "none"
                lines.append(f"### `{name}`")
                lines.append(f"**Description**: {template['description']}")
                lines.append(f"**Parameters**: {params_str}")
                lines.append("")

    lines.append(f"**Total Templates**: {len(TEMPLATES)}")

    return "\n".join(lines)


def execute_template(template_name: str, params: Dict[str, Any], service: Any) -> QueryResult:
    """
    Execute a named template with parameters.

    Args:
        template_name: Name of the template from TEMPLATES registry
        params: Dictionary of parameter values (keys must match template's parameters list)
        service: OTCIntelligenceService instance to execute the query

    Returns:
        QueryResult with success status, data, and row count

    Raises:
        KeyError: If template_name not found
        ValueError: If required parameters missing
    """
    if template_name not in TEMPLATES:
        raise KeyError(f"Template '{template_name}' not found. Available: {list(TEMPLATES.keys())}")

    template = TEMPLATES[template_name]

    # Validate parameters
    required_params = template["parameters"]
    missing_params = [p for p in required_params if p not in params]
    if missing_params:
        raise ValueError(f"Missing required parameters for '{template_name}': {missing_params}")

    # Build parameter tuple in correct order
    param_values = tuple(params[p] for p in required_params)

    # Execute query through service
    result = service.execute_query(template["sql"], param_values)

    return result
