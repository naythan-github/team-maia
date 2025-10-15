#!/usr/bin/env python3
"""
ServiceDesk Operations Dashboard
Real-time operational intelligence for ServiceDesk ticket analysis
Integrated with Maia Dashboard Hub
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

from flask import Flask, jsonify
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

class ServiceDeskDashboard:
    """ServiceDesk Operations Intelligence Dashboard"""

    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.flask_server = self.app.server
        self.db_path = str(DB_PATH)

        # Setup health endpoints
        self.setup_health_endpoints()

        # Initialize dashboard
        self.setup_layout()

    def setup_health_endpoints(self):
        """Standardized health check endpoint"""
        @self.flask_server.route('/health')
        def health_check():
            try:
                metrics = self.get_summary_metrics()
                return jsonify({
                    "status": "healthy",
                    "service": "servicedesk_operations_dashboard",
                    "version": "1.0.0",
                    "total_tickets": int(metrics['total_tickets']),
                    "fcr_rate": float(metrics['fcr_rate']),
                    "automation_potential": int(metrics['automation_count']),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "service": "servicedesk_operations_dashboard",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500

    def get_summary_metrics(self):
        """Get summary KPI metrics using comments table"""
        conn = sqlite3.connect(self.db_path)

        total = pd.read_sql_query("SELECT COUNT(*) as count FROM tickets", conn).iloc[0]['count']

        # FCR from comments table (Cloud roster only, 1-3 comments = Industry Standard)
        # Excludes Alert tickets for accurate work ticket FCR
        fcr_query = """
            WITH work_tickets AS (
                SELECT t.`TKT-Ticket ID` as ticket_id
                FROM tickets t
                WHERE t.`TKT-Category` != 'Alert'
            ),
            ticket_comment_counts AS (
                SELECT
                    wt.ticket_id,
                    COUNT(*) as comment_count
                FROM work_tickets wt
                INNER JOIN comments c ON wt.ticket_id = c.ticket_id
                INNER JOIN cloud_team_roster r ON c.user_name = r.username
                WHERE c.user_name IS NOT NULL AND c.user_name <> 'nan'
                GROUP BY wt.ticket_id
            )
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN comment_count <= 3 THEN 1 ELSE 0 END) as fcr
            FROM ticket_comment_counts
        """
        fcr_data = pd.read_sql_query(fcr_query, conn)
        fcr_rate = round(fcr_data.iloc[0]['fcr'] * 100.0 / fcr_data.iloc[0]['total'], 1) if fcr_data.iloc[0]['total'] > 0 else 0

        auto_query = """
            SELECT COUNT(*) as count
            FROM tickets
            WHERE "TKT-Title" LIKE '%Alert%' OR "TKT-Title" LIKE '%Sev%'
        """
        auto_count = pd.read_sql_query(auto_query, conn).iloc[0]['count']

        # Total comments and Cloud roster agents
        comments_count = pd.read_sql_query("SELECT COUNT(*) as count FROM comments", conn).iloc[0]['count']
        agents_count = pd.read_sql_query("SELECT COUNT(*) as count FROM cloud_team_roster", conn).iloc[0]['count']

        conn.close()

        return {
            'total_tickets': total,
            'fcr_rate': fcr_rate,
            'automation_count': auto_count,
            'hours_saved': round(auto_count * 0.25, 0),
            'comments_count': comments_count,
            'agents_count': agents_count,
            'tickets_with_comments': fcr_data.iloc[0]['total']
        }

    def get_fcr_by_team(self):
        """Get FCR performance by team using Industry Standard (1-3 comments)"""
        conn = sqlite3.connect(self.db_path)
        query = """
            WITH work_tickets AS (
                SELECT t.`TKT-Ticket ID` as ticket_id
                FROM tickets t
                WHERE t.`TKT-Category` != 'Alert'
            ),
            team_ticket_comments AS (
                SELECT
                    c.team,
                    c.ticket_id,
                    COUNT(*) as comment_count
                FROM work_tickets wt
                INNER JOIN comments c ON wt.ticket_id = c.ticket_id
                INNER JOIN cloud_team_roster r ON c.user_name = r.username
                WHERE c.user_name IS NOT NULL AND c.user_name <> 'nan'
                AND c.team LIKE 'Cloud -%'
                GROUP BY c.team, c.ticket_id
            ),
            team_members AS (
                SELECT
                    c.team,
                    COUNT(DISTINCT c.user_name) as member_count
                FROM comments c
                INNER JOIN cloud_team_roster r ON c.user_name = r.username
                WHERE c.team LIKE 'Cloud -%'
                GROUP BY c.team
            )
            SELECT
                ttc.team,
                COUNT(DISTINCT ttc.ticket_id) as total,
                ROUND(100.0 * SUM(CASE WHEN ttc.comment_count <= 3 THEN 1 ELSE 0 END) / COUNT(DISTINCT ttc.ticket_id), 1) as fcr_rate,
                tm.member_count as team_members
            FROM team_ticket_comments ttc
            INNER JOIN team_members tm ON ttc.team = tm.team
            GROUP BY ttc.team, tm.member_count
            HAVING total > 100
            ORDER BY fcr_rate DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_automation_opportunities(self):
        """Get top automation opportunities"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT
                SUBSTR("TKT-Title", 1, 60) as pattern,
                COUNT(*) as volume,
                ROUND(COUNT(*) * 0.25, 0) as hours_saved
            FROM tickets
            WHERE ("TKT-Title" LIKE '%Alert%' OR "TKT-Title" LIKE '%Sev%')
            GROUP BY "TKT-Title"
            HAVING volume > 50
            ORDER BY volume DESC
            LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_reassignment_distribution(self):
        """Get reassignment analysis from comments"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT
                agent_count as agents,
                COUNT(*) as ticket_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(DISTINCT ticket_id) FROM comments), 1) as percentage
            FROM (
                SELECT ticket_id, COUNT(DISTINCT user_id) as agent_count
                FROM comments
                WHERE user_id IS NOT NULL AND user_id <> 'nan'
                GROUP BY ticket_id
            )
            GROUP BY agent_count
            ORDER BY agent_count
            LIMIT 8
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_top_agents_by_workload(self):
        """Get top Cloud roster agents by comment volume"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT
                r.name,
                COUNT(*) as comments,
                COUNT(DISTINCT c.ticket_id) as tickets,
                ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT c.ticket_id), 1) as avg_comments_per_ticket
            FROM comments c
            INNER JOIN cloud_team_roster r ON c.user_name = r.username
            WHERE c.user_id IS NOT NULL AND c.user_id <> 'nan'
            GROUP BY r.name
            ORDER BY comments DESC
            LIMIT 15
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def setup_layout(self):
        """Setup dashboard layout"""

        metrics = self.get_summary_metrics()
        fcr_data = self.get_fcr_by_team()
        auto_data = self.get_automation_opportunities()
        reassignment_data = self.get_reassignment_distribution()
        agent_data = self.get_top_agents_by_workload()

        # Color-code FCR bars
        colors = ['#10b981' if x >= 70 else '#f59e0b' if x >= 40 else '#ef4444'
                 for x in fcr_data['fcr_rate']]

        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("ServiceDesk Operations Intelligence", className="text-primary"),
                    html.P(f"Cloud Teams (48 roster members) | June 26 - Oct 14, 2025 | {metrics['tickets_with_comments']:,} tickets | {metrics['comments_count']:,} comments | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                          className="text-muted")
                ])
            ], className="mb-4 mt-3"),

            # Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Tickets", className="text-muted"),
                            html.H2(f"{metrics['total_tickets']:,}", className="text-dark"),
                            html.Small(f"{metrics['tickets_with_comments']:,} with comments", className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Overall FCR Rate", className="text-muted"),
                            html.H2(f"{metrics['fcr_rate']}%",
                                   className="text-danger" if metrics['fcr_rate'] < 40 else "text-warning"),
                            html.Small("Target: 70-80% | Gap: -43 to -53 pts", className="text-danger")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Automation Candidates", className="text-muted"),
                            html.H2(f"{metrics['automation_count']:,}", className="text-primary"),
                            html.Small(f"{round(metrics['automation_count']/metrics['total_tickets']*100, 1)}% of total",
                                      className="text-muted")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Hours Saved/Month", className="text-muted"),
                            html.H2(f"{int(metrics['hours_saved']):,}", className="text-success"),
                            html.Small(f"≈ ${int(metrics['hours_saved'] * 75):,} @ $75/hr", className="text-muted")
                        ])
                    ])
                ], width=3),
            ], className="mb-4"),

            # Main Charts Row 1
            dbc.Row([
                # FCR by Team
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("First Call Resolution by Team (Cloud Roster Only)")),
                        dbc.CardBody([
                            dcc.Graph(
                                figure={
                                    'data': [go.Bar(
                                        y=fcr_data['team'],
                                        x=fcr_data['fcr_rate'],
                                        orientation='h',
                                        marker={'color': colors},
                                        text=[f"{x}% ({y} members)" for x, y in zip(fcr_data['fcr_rate'], fcr_data['team_members'])],
                                        textposition='auto'
                                    )],
                                    'layout': go.Layout(
                                        xaxis={'title': 'FCR Rate (%)', 'range': [0, 100]},
                                        yaxis={'autorange': 'reversed'},
                                        margin={'l': 200, 'r': 20, 't': 20, 'b': 50},
                                        height=400,
                                        shapes=[{
                                            'type': 'line',
                                            'x0': 70, 'x1': 70,
                                            'y0': -0.5, 'y1': len(fcr_data)-0.5,
                                            'line': {'color': '#10b981', 'width': 2, 'dash': 'dash'}
                                        }]
                                    )
                                },
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], width=6),

                # Reassignment Distribution
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Reassignment Distribution")),
                        dbc.CardBody([
                            dcc.Graph(
                                figure={
                                    'data': [go.Bar(
                                        x=reassignment_data['agents'],
                                        y=reassignment_data['ticket_count'],
                                        marker={'color': ['#10b981'] + ['#f59e0b']*(len(reassignment_data)-1)},
                                        text=[f"{x:,}<br>({y}%)" for x, y in zip(reassignment_data['ticket_count'], reassignment_data['percentage'])],
                                        textposition='auto'
                                    )],
                                    'layout': go.Layout(
                                        xaxis={'title': 'Number of Agents', 'dtick': 1},
                                        yaxis={'title': 'Ticket Count'},
                                        margin={'l': 50, 'r': 20, 't': 20, 'b': 50},
                                        height=400
                                    )
                                },
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], width=6),
            ], className="mb-4"),

            # Main Charts Row 2
            dbc.Row([
                # Top Agents by Workload
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Top 15 Cloud Team Members by Workload")),
                        dbc.CardBody([
                            dash_table.DataTable(
                                data=agent_data.to_dict('records'),
                                columns=[
                                    {'name': 'Cloud Team Member', 'id': 'name'},
                                    {'name': 'Comments', 'id': 'comments'},
                                    {'name': 'Tickets', 'id': 'tickets'},
                                    {'name': 'Avg Comments/Ticket', 'id': 'avg_comments_per_ticket'}
                                ],
                                style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '13px'},
                                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                                style_data_conditional=[{
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }],
                                page_size=15
                            )
                        ])
                    ])
                ], width=6),

                # Automation Opportunities
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Top Automation Opportunities")),
                        dbc.CardBody([
                            dash_table.DataTable(
                                data=auto_data.to_dict('records'),
                                columns=[
                                    {'name': 'Alert Pattern', 'id': 'pattern'},
                                    {'name': 'Volume', 'id': 'volume'},
                                    {'name': 'Hours Saved', 'id': 'hours_saved'}
                                ],
                                style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '13px'},
                                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                                style_data_conditional=[{
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': '#f8f9fa'
                                }]
                            )
                        ])
                    ])
                ], width=6),
            ])
        ], fluid=True)

def main():
    """Main entry point"""
    dashboard = ServiceDeskDashboard()
    print("🚀 Starting ServiceDesk Operations Dashboard...")
    print("📊 Dashboard: http://127.0.0.1:8065")
    print("🏥 Health: http://127.0.0.1:8065/health")
    dashboard.app.run(debug=False, host='0.0.0.0', port=8065)

if __name__ == '__main__':
    main()
