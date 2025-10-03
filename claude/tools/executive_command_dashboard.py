#!/usr/bin/env python3
"""
Executive Command Dashboard
Real-time visibility into strategic initiatives, operational tasks, and team health

Author: Maia Personal Assistant Agent
Phase: 86.4 - Executive Command Center
Date: 2025-10-03
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px

from claude.tools.confluence_intelligence_processor import ConfluenceIntelligenceProcessor
from claude.tools.vtt_intelligence_processor import VTTIntelligenceProcessor


class ExecutiveCommandDashboard:
    """Executive command center dashboard"""

    def __init__(self, port: int = 8070):
        """Initialize dashboard"""
        self.port = port
        self.confluence_intel = ConfluenceIntelligenceProcessor()
        self.vtt_intel = VTTIntelligenceProcessor()

        self.app = Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            html.H1("🎯 Executive Command Center",
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),

            # Refresh interval
            dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),

            # Top KPIs
            html.Div(id='kpi-cards', style={'marginBottom': 30}),

            # Main sections
            html.Div([
                # Strategic view
                html.Div([
                    html.H2("📈 Strategic Initiatives", style={'color': '#3498db'}),
                    html.Div(id='strategic-view')
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top',
                         'padding': 20, 'backgroundColor': '#ecf0f1', 'borderRadius': 10, 'marginRight': '2%'}),

                # Operational view
                html.Div([
                    html.H2("⚙️ Operational Status", style={'color': '#e74c3c'}),
                    html.Div(id='operational-view')
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top',
                         'padding': 20, 'backgroundColor': '#ecf0f1', 'borderRadius': 10}),
            ], style={'marginBottom': 30}),

            # Bottom sections
            html.Div([
                # Decisions needed
                html.Div([
                    html.H2("🎯 Decisions Needed", style={'color': '#f39c12'}),
                    html.Div(id='decisions-view')
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top',
                         'padding': 20, 'backgroundColor': '#ecf0f1', 'borderRadius': 10, 'marginRight': '2%'}),

                # Open questions
                html.Div([
                    html.H2("❓ Open Questions", style={'color': '#9b59b6'}),
                    html.Div(id='questions-view')
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top',
                         'padding': 20, 'backgroundColor': '#ecf0f1', 'borderRadius': 10}),
            ]),

            html.Div([
                html.P(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': 30})
            ])
        ], style={'fontFamily': 'Arial, sans-serif', 'padding': 30, 'backgroundColor': '#f8f9fa'})

    def _setup_callbacks(self):
        """Setup dashboard callbacks"""

        @self.app.callback(
            [Output('kpi-cards', 'children'),
             Output('strategic-view', 'children'),
             Output('operational-view', 'children'),
             Output('decisions-view', 'children'),
             Output('questions-view', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            # Get data
            confluence_summary = self.confluence_intel.get_executive_summary()
            vtt_actions = self.vtt_intel.get_pending_actions_for_owner("Naythan")

            # KPI Cards
            kpis = html.Div([
                self._create_kpi_card("Strategic Initiatives",
                                     confluence_summary.get('strategic_initiatives', 0),
                                     "#3498db"),
                self._create_kpi_card("Operational Tasks",
                                     confluence_summary.get('total_action_items', 0) + len(vtt_actions),
                                     "#e74c3c"),
                self._create_kpi_card("Decisions Needed",
                                     confluence_summary.get('decisions_needed', 0),
                                     "#f39c12"),
                self._create_kpi_card("Open Questions",
                                     confluence_summary.get('pending_questions', 0),
                                     "#9b59b6"),
            ], style={'display': 'flex', 'justifyContent': 'space-around'})

            # Strategic view
            strategic_items = self.confluence_intel.intelligence.get('strategic_initiatives', [])[:10]
            strategic = html.Div([
                html.Ul([
                    html.Li(f"{item['initiative'][:80]}...",
                           style={'marginBottom': 10, 'fontSize': 14})
                    for item in strategic_items
                ])
            ])

            # Operational view - combine Confluence + VTT actions
            operational_items = self.confluence_intel.intelligence.get('action_items', [])[:5]
            operational = html.Div([
                html.H4("From Confluence:", style={'color': '#16a085'}),
                html.Ul([
                    html.Li(f"{item['action'][:60]}... ({item['category']})",
                           style={'marginBottom': 8, 'fontSize': 13})
                    for item in operational_items
                ]),
                html.H4("From Meetings:", style={'color': '#16a085', 'marginTop': 15}),
                html.Ul([
                    html.Li(f"{action['action'][:60]}... (Due: {action['deadline']})",
                           style={'marginBottom': 8, 'fontSize': 13})
                    for action in vtt_actions[:5]
                ])
            ])

            # Decisions
            decisions = self.confluence_intel.intelligence.get('decisions_needed', [])[:8]
            decisions_view = html.Div([
                html.Ul([
                    html.Li([
                        html.Span(f"{dec['decision'][:70]}...",
                                 style={'fontWeight': 'bold' if dec['urgency'] == 'high' else 'normal'}),
                        html.Span(f" [{dec['urgency']}]",
                                 style={'color': '#e74c3c' if dec['urgency'] == 'high' else '#95a5a6',
                                       'fontSize': 12, 'marginLeft': 10})
                    ], style={'marginBottom': 10})
                    for dec in decisions
                ])
            ])

            # Questions
            questions = self.confluence_intel.intelligence.get('questions', [])[:8]
            questions_view = html.Div([
                html.Ul([
                    html.Li(f"{q['question'][:80]}... ({q['category']})",
                           style={'marginBottom': 10, 'fontSize': 13})
                    for q in questions
                ])
            ])

            return kpis, strategic, operational, decisions_view, questions_view

    def _create_kpi_card(self, title: str, value: int, color: str):
        """Create KPI card"""
        return html.Div([
            html.H3(str(value), style={'fontSize': 48, 'margin': 0, 'color': color}),
            html.P(title, style={'fontSize': 14, 'color': '#7f8c8d', 'margin': 5})
        ], style={
            'textAlign': 'center',
            'padding': 20,
            'backgroundColor': 'white',
            'borderRadius': 10,
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'width': '22%'
        })

    def run(self):
        """Run dashboard"""
        print(f"\n🎯 Executive Command Dashboard starting...")
        print(f"📊 Dashboard: http://127.0.0.1:{self.port}")
        print(f"🔄 Auto-refresh: Every 30 seconds\n")
        self.app.run(debug=False, port=self.port, host='127.0.0.1')


def main():
    """CLI entry"""
    import argparse

    parser = argparse.ArgumentParser(description="Executive Command Dashboard")
    parser.add_argument("--port", type=int, default=8070, help="Port to run on")

    args = parser.parse_args()

    dashboard = ExecutiveCommandDashboard(port=args.port)
    dashboard.run()


if __name__ == "__main__":
    main()
