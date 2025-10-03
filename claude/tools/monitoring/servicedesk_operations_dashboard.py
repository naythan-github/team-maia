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
                    "total_tickets": metrics['total_tickets'],
                    "fcr_rate": metrics['fcr_rate'],
                    "automation_potential": metrics['automation_count'],
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
        """Get summary KPI metrics"""
        conn = sqlite3.connect(self.db_path)

        total = pd.read_sql_query("SELECT COUNT(*) as count FROM tickets", conn).iloc[0]['count']

        fcr_query = """
            SELECT
                COUNT(DISTINCT t."TKT-Ticket ID") as total,
                COUNT(DISTINCT CASE WHEN eng_count = 1 THEN t."TKT-Ticket ID" END) as fcr
            FROM tickets t
            LEFT JOIN (
                SELECT crm_id, COUNT(DISTINCT user_username) as eng_count
                FROM timesheets GROUP BY crm_id
            ) ts ON t."TKT-Ticket ID" = ts.crm_id
        """
        fcr_data = pd.read_sql_query(fcr_query, conn)
        fcr_rate = round(fcr_data.iloc[0]['fcr'] * 100.0 / fcr_data.iloc[0]['total'], 1) if fcr_data.iloc[0]['total'] > 0 else 0

        auto_query = """
            SELECT COUNT(*) as count
            FROM tickets
            WHERE "TKT-Title" LIKE '%Alert%' OR "TKT-Title" LIKE '%Sev%'
        """
        auto_count = pd.read_sql_query(auto_query, conn).iloc[0]['count']

        conn.close()

        return {
            'total_tickets': total,
            'fcr_rate': fcr_rate,
            'automation_count': auto_count,
            'hours_saved': round(auto_count * 0.25, 0)
        }

    def get_fcr_by_team(self):
        """Get FCR performance by team"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT
                t."TKT-Team" as team,
                COUNT(DISTINCT t."TKT-Ticket ID") as total,
                ROUND(COUNT(DISTINCT CASE WHEN eng_count = 1 THEN t."TKT-Ticket ID" END) * 100.0 /
                      COUNT(DISTINCT t."TKT-Ticket ID"), 1) as fcr_rate
            FROM tickets t
            LEFT JOIN (
                SELECT crm_id, COUNT(DISTINCT user_username) as eng_count
                FROM timesheets GROUP BY crm_id
            ) ts ON t."TKT-Ticket ID" = ts.crm_id
            GROUP BY t."TKT-Team"
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

    def setup_layout(self):
        """Setup dashboard layout"""

        metrics = self.get_summary_metrics()
        fcr_data = self.get_fcr_by_team()
        auto_data = self.get_automation_opportunities()

        # Color-code FCR bars
        colors = ['#10b981' if x >= 70 else '#f59e0b' if x >= 40 else '#ef4444'
                 for x in fcr_data['fcr_rate']]

        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("ServiceDesk Operations Intelligence", className="text-primary"),
                    html.P(f"Analysis Period: July-Dec 2025 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                          className="text-muted")
                ])
            ], className="mb-4 mt-3"),

            # Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Tickets", className="text-muted"),
                            html.H2(f"{metrics['total_tickets']:,}", className="text-dark")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Overall FCR Rate", className="text-muted"),
                            html.H2(f"{metrics['fcr_rate']}%",
                                   className="text-danger" if metrics['fcr_rate'] < 40 else "text-warning"),
                            html.Small("Target: 70%", className="text-muted")
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

            # Main Charts
            dbc.Row([
                # FCR by Team
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("First Call Resolution by Team")),
                        dbc.CardBody([
                            dcc.Graph(
                                figure={
                                    'data': [go.Bar(
                                        y=fcr_data['team'],
                                        x=fcr_data['fcr_rate'],
                                        orientation='h',
                                        marker={'color': colors},
                                        text=[f"{x}%" for x in fcr_data['fcr_rate']],
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
                                style_cell={'textAlign': 'left', 'padding': '10px'},
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
    dashboard.app.run(debug=True, host='0.0.0.0', port=8065)

if __name__ == '__main__':
    main()
