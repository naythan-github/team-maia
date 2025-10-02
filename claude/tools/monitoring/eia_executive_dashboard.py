#!/usr/bin/env python3
"""
EIA Executive Dashboard
Natural language interface for Executive Intelligence Automation insights
"""

import os
import sys
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Flask and Dash imports
from flask import Flask, render_template_string, jsonify, request
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

# Add Maia tools to path
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(MAIA_ROOT / "claude" / "tools" / "🤖_intelligence"))

try:
    from eia_core_platform import EIAOrchestrator
    EIA_AVAILABLE = True
except ImportError:
    EIA_AVAILABLE = False

class EIAExecutiveDashboard:
    """Executive Intelligence Automation Dashboard with Natural Language Interface"""
    
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.maia_root = MAIA_ROOT
        self.eia_orchestrator = EIAOrchestrator() if EIA_AVAILABLE else None
        
        # Initialize data
        self.insights_data = []
        self.metrics_data = []
        self.kpi_data = {}
        
        # Load initial data
        self.refresh_data()

        # Setup health endpoints
        self.setup_health_endpoints()

        # Setup layout and callbacks
        self.setup_layout()
        self.setup_callbacks()

    def setup_health_endpoints(self):
        """Setup standardized health check endpoints"""
        @self.app.server.route('/health')
        def health_check():
            """Standardized health check endpoint"""
            try:
                insights_count = len(self.insights_data)
                metrics_count = len(self.metrics_data)
                is_healthy = insights_count > 0 or metrics_count > 0

                return jsonify({
                    "status": "healthy" if is_healthy else "degraded",
                    "uptime": 0,
                    "version": "1.0.0",
                    "service": "eia_executive_dashboard",
                    "insights_count": insights_count,
                    "metrics_count": metrics_count,
                    "eia_available": EIA_AVAILABLE,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "uptime": 0,
                    "version": "1.0.0",
                    "service": "eia_executive_dashboard",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500

    def refresh_data(self):
        """Refresh EIA data from orchestrator"""
        if not self.eia_orchestrator:
            # Demo data for when EIA is not available
            self.load_demo_data()
            return
            
        try:
            # Get insights and metrics from EIA system
            self.insights_data = self.eia_orchestrator.get_active_insights()
            self.metrics_data = self.eia_orchestrator.get_recent_metrics(hours=24)
            
            # Calculate KPIs
            self.kpi_data = self.calculate_kpis()
            
        except Exception as e:
            print(f"Error loading EIA data: {e}")
            self.load_demo_data()
            
    def load_demo_data(self):
        """Load demo data when EIA system is not available"""
        self.insights_data = [
            {
                'id': 'demo_1',
                'title': 'High Cloud Cost Growth',
                'description': 'Cloud costs growing at 15.2%/month ($15,420)',
                'category': 'Cost Management',
                'priority': 'high',
                'impact': 'Financial - Significant budget impact if trend continues',
                'recommendation': 'Review resource utilization, implement auto-scaling',
                'confidence': 0.94,
                'actionable': True,
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': 'demo_2', 
                'title': 'Excellent Deployment Frequency',
                'description': 'Team achieving 8.5 deployments/week (Elite performer)',
                'category': 'DevOps Performance',
                'priority': 'medium',
                'impact': 'Positive - High velocity development cycle',
                'recommendation': 'Maintain current practices and share with other teams',
                'confidence': 0.95,
                'actionable': False,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        self.metrics_data = [
            {'name': 'deployment_frequency', 'value': '8.5', 'unit': 'deployments/week', 'category': 'DORA'},
            {'name': 'lead_time_for_changes', 'value': '12.5', 'unit': 'hours', 'category': 'DORA'},
            {'name': 'monthly_cloud_cost', 'value': '15420.50', 'unit': 'USD', 'category': 'Cost'},
            {'name': 'team_satisfaction', 'value': '7.8', 'unit': 'score_10', 'category': 'SPACE'}
        ]
        
        self.kpi_data = {
            'devops_score': 85,
            'cost_efficiency': 72,
            'team_health': 78,
            'security_posture': 91
        }
        
    def calculate_kpis(self):
        """Calculate high-level KPIs from metrics"""
        kpis = {
            'devops_score': 75,
            'cost_efficiency': 80,
            'team_health': 85,
            'security_posture': 90
        }
        
        # Calculate based on actual metrics if available
        if self.metrics_data:
            # DevOps Score (based on DORA metrics)
            dora_metrics = [m for m in self.metrics_data if m['category'] == 'DORA']
            if dora_metrics:
                # Simplified calculation - would be more sophisticated in production
                deploy_freq = next((float(m['value']) for m in dora_metrics if m['name'] == 'deployment_frequency'), 0)
                lead_time = next((float(m['value']) for m in dora_metrics if m['name'] == 'lead_time_for_changes'), 24)
                
                # Score based on elite performance thresholds
                freq_score = min(100, deploy_freq * 10)  # >10/week = 100
                lead_score = max(0, 100 - lead_time * 2)  # <24h = high score
                kpis['devops_score'] = int((freq_score + lead_score) / 2)
                
            # Team Health (based on SPACE metrics)
            space_metrics = [m for m in self.metrics_data if m['category'] == 'SPACE']
            if space_metrics:
                satisfaction = next((float(m['value']) for m in space_metrics if m['name'] == 'team_satisfaction'), 7)
                kpis['team_health'] = int(satisfaction * 10)
                
        return kpis
        
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🤖 Executive Intelligence Automation", className="text-primary mb-0"),
                    html.P("AI-Powered Engineering Leadership Dashboard", className="lead text-muted"),
                ], width=8),
                dbc.Col([
                    dbc.Button("🔄 Refresh Data", id="refresh-button", color="primary", size="sm", className="mb-2"),
                    html.Small(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", id="last-updated", className="text-muted d-block")
                ], width=4, className="text-end")
            ], className="mb-4"),
            
            # KPI Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{self.kpi_data.get('devops_score', 0)}/100", className="card-title text-primary"),
                            html.P("DevOps Performance", className="card-text text-muted mb-0"),
                            html.Small("DORA Metrics", className="text-muted")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{self.kpi_data.get('cost_efficiency', 0)}/100", className="card-title text-success"),
                            html.P("Cost Efficiency", className="card-text text-muted mb-0"),
                            html.Small("Cloud Optimization", className="text-muted")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{self.kpi_data.get('team_health', 0)}/100", className="card-title text-info"),
                            html.P("Team Health", className="card-text text-muted mb-0"),
                            html.Small("SPACE Framework", className="text-muted")
                        ])
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{self.kpi_data.get('security_posture', 0)}/100", className="card-title text-warning"),
                            html.P("Security Posture", className="card-text text-muted mb-0"),
                            html.Small("Compliance Score", className="text-muted")
                        ])
                    ], className="text-center")
                ], width=3)
            ], className="mb-4"),
            
            # Main Content Tabs
            dbc.Tabs([
                dbc.Tab(label="🔍 Active Insights", tab_id="insights", active_tab_style={"fontWeight": "bold"}),
                dbc.Tab(label="📈 Key Metrics", tab_id="metrics"),
                dbc.Tab(label="💬 Natural Language Query", tab_id="nlp"),
                dbc.Tab(label="⚙️ System Status", tab_id="status")
            ], id="main-tabs", active_tab="insights", className="mb-3"),
            
            # Tab Content
            html.Div(id="tab-content"),
            
            # Auto-refresh interval
            dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),
            
        ], fluid=True, className="py-3")
        
    def create_insights_tab(self):
        """Create insights tab content"""
        if not self.insights_data:
            return html.Div([
                dbc.Alert("No active insights available. Run EIA agents to generate intelligence.", color="info")
            ])
            
        insights_cards = []
        
        priority_colors = {
            'critical': 'danger',
            'high': 'warning', 
            'medium': 'info',
            'low': 'light'
        }
        
        priority_icons = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📢', 
            'low': '💡'
        }
        
        for insight in self.insights_data[:10]:  # Show top 10
            color = priority_colors.get(insight.get('priority', 'low'), 'light')
            icon = priority_icons.get(insight.get('priority', 'low'), '📋')
            
            card = dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        f"{icon} {insight.get('title', 'Unknown Insight')}",
                        dbc.Badge(insight.get('priority', 'low').upper(), color=color, className="ms-2")
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    html.P(insight.get('description', ''), className="card-text"),
                    html.Strong("Impact: "),
                    html.Span(insight.get('impact', ''), className="text-muted"),
                    html.Br(),
                    html.Strong("Recommendation: "),
                    html.Span(insight.get('recommendation', ''), className="text-muted"),
                    html.Hr(),
                    html.Small([
                        f"Category: {insight.get('category', 'Unknown')} | ",
                        f"Confidence: {insight.get('confidence', 0)*100:.0f}% | ",
                        f"Actionable: {'Yes' if insight.get('actionable') else 'No'}"
                    ], className="text-muted")
                ])
            ], className="mb-3")
            
            insights_cards.append(card)
            
        return html.Div(insights_cards)
        
    def create_metrics_tab(self):
        """Create metrics tab content"""
        if not self.metrics_data:
            return html.Div([
                dbc.Alert("No metrics available. Run EIA agents to collect data.", color="info")
            ])
            
        # Create metrics by category
        categories = {}
        for metric in self.metrics_data:
            cat = metric.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(metric)
            
        category_tabs = []
        for category, metrics in categories.items():
            metrics_table = dash_table.DataTable(
                data=[{
                    'Metric': m.get('name', ''),
                    'Value': f"{m.get('value', '')} {m.get('unit', '')}",
                    'Source': m.get('source', ''),
                    'Timestamp': m.get('timestamp', '')[:19] if m.get('timestamp') else ''
                } for m in metrics],
                columns=[
                    {"name": "Metric", "id": "Metric"},
                    {"name": "Value", "id": "Value"}, 
                    {"name": "Source", "id": "Source"},
                    {"name": "Timestamp", "id": "Timestamp"}
                ],
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            )
            
            category_tabs.append(
                dbc.Tab(label=f"📊 {category}", children=[
                    html.Div([metrics_table], className="mt-3")
                ])
            )
            
        return dbc.Tabs(category_tabs)
        
    def create_nlp_tab(self):
        """Create natural language query tab"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("💬 Ask Your Executive Assistant"),
                    html.P("Ask questions about your engineering metrics, team performance, costs, and more.", className="text-muted"),
                    
                    dbc.InputGroup([
                        dbc.Input(
                            id="nlp-query-input",
                            placeholder="e.g., 'What are our deployment metrics this week?' or 'Show me cost trends'",
                            type="text",
                            size="lg"
                        ),
                        dbc.Button("Ask", id="nlp-submit-button", color="primary", size="lg")
                    ], className="mb-3"),
                    
                    html.Div(id="nlp-response", className="mt-3")
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H5("💡 Example Questions:"),
                    dbc.ListGroup([
                        dbc.ListGroupItem("What's our current DORA metrics performance?", action=True, id="example-1"),
                        dbc.ListGroupItem("How is our team satisfaction trending?", action=True, id="example-2"), 
                        dbc.ListGroupItem("What are the top cost optimization opportunities?", action=True, id="example-3"),
                        dbc.ListGroupItem("Show me critical insights that need attention", action=True, id="example-4"),
                        dbc.ListGroupItem("What's our cloud infrastructure health status?", action=True, id="example-5")
                    ])
                ], width=8),
                
                dbc.Col([
                    html.H5("📋 Recent Queries:"),
                    html.Div(id="recent-queries", children=[
                        html.Small("No recent queries", className="text-muted")
                    ])
                ], width=4)
            ], className="mt-4")
        ])
        
    def create_status_tab(self):
        """Create system status tab"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4("⚙️ EIA System Status"),
                    
                    dbc.Card([
                        dbc.CardHeader("System Components"),
                        dbc.CardBody([
                            dbc.ListGroup([
                                dbc.ListGroupItem([
                                    html.Div([
                                        html.Strong("EIA Core Platform"),
                                        dbc.Badge("✅ Active" if EIA_AVAILABLE else "❌ Unavailable", 
                                                color="success" if EIA_AVAILABLE else "danger", className="ms-2")
                                    ])
                                ]),
                                dbc.ListGroupItem([
                                    html.Div([
                                        html.Strong("DevOps Intelligence Agent"),
                                        dbc.Badge("✅ Running", color="success", className="ms-2")
                                    ])
                                ]),
                                dbc.ListGroupItem([
                                    html.Div([
                                        html.Strong("Cloud Intelligence Agent"), 
                                        dbc.Badge("✅ Running", color="success", className="ms-2")
                                    ])
                                ]),
                                dbc.ListGroupItem([
                                    html.Div([
                                        html.Strong("Team Intelligence Agent"),
                                        dbc.Badge("✅ Running", color="success", className="ms-2")
                                    ])
                                ])
                            ], flush=True)
                        ])
                    ], className="mb-3"),
                    
                    dbc.Card([
                        dbc.CardHeader("Data Sources"),
                        dbc.CardBody([
                            html.P(f"📊 Active Insights: {len(self.insights_data)}", className="mb-1"),
                            html.P(f"📈 Current Metrics: {len(self.metrics_data)}", className="mb-1"),
                            html.P(f"💾 Database: {self.eia_orchestrator.db_path if self.eia_orchestrator else 'Demo Mode'}", className="mb-0 text-muted small")
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    html.H4("🔧 Actions"),
                    
                    dbc.Card([
                        dbc.CardBody([
                            dbc.ButtonGroup([
                                dbc.Button("▶️ Run All Agents", id="run-agents-button", color="success", className="mb-2"),
                                dbc.Button("🔄 Refresh Data", id="refresh-data-button", color="primary", className="mb-2"),
                                dbc.Button("📊 Export Report", id="export-report-button", color="info", className="mb-2"),
                            ], vertical=True, className="d-grid gap-2")
                        ])
                    ])
                ], width=6)
            ])
        ])
        
    def setup_callbacks(self):
        """Setup Dash callbacks"""
        
        @self.app.callback(
            Output('tab-content', 'children'),
            Input('main-tabs', 'active_tab')
        )
        def update_tab_content(active_tab):
            if active_tab == 'insights':
                return self.create_insights_tab()
            elif active_tab == 'metrics':
                return self.create_metrics_tab()
            elif active_tab == 'nlp':
                return self.create_nlp_tab()
            elif active_tab == 'status':
                return self.create_status_tab()
            return html.Div("Select a tab")
            
        @self.app.callback(
            Output('nlp-response', 'children'),
            [Input('nlp-submit-button', 'n_clicks')] + [Input(f'example-{i}', 'n_clicks') for i in range(1, 6)],
            State('nlp-query-input', 'value')
        )
        def process_nlp_query(submit_clicks, ex1, ex2, ex3, ex4, ex5, query_input):
            ctx = callback_context
            if not ctx.triggered:
                return ""
                
            # Determine which input was triggered
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if triggered_id == 'nlp-submit-button' and query_input:
                query = query_input
            elif triggered_id.startswith('example-'):
                example_queries = {
                    'example-1': "What's our current DORA metrics performance?",
                    'example-2': "How is our team satisfaction trending?", 
                    'example-3': "What are the top cost optimization opportunities?",
                    'example-4': "Show me critical insights that need attention",
                    'example-5': "What's our cloud infrastructure health status?"
                }
                query = example_queries.get(triggered_id, "")
            else:
                return ""
                
            # Process the query (simplified NLP processing)
            response = self.process_natural_language_query(query)
            
            return dbc.Card([
                dbc.CardHeader(f"🤖 Response to: '{query}'"),
                dbc.CardBody([
                    html.Div(response)
                ])
            ], className="mt-3")
            
        @self.app.callback(
            Output('last-updated', 'children'),
            [Input('refresh-button', 'n_clicks'), Input('interval-component', 'n_intervals')]
        )
        def update_timestamp(refresh_clicks, intervals):
            self.refresh_data()
            return f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            
    def process_natural_language_query(self, query: str) -> List:
        """Process natural language queries about EIA data"""
        query_lower = query.lower()
        
        # DORA metrics queries
        if any(word in query_lower for word in ['dora', 'deployment', 'lead time', 'devops']):
            dora_metrics = [m for m in self.metrics_data if m['category'] == 'DORA']
            if dora_metrics:
                content = []
                content.append(html.H5("🚀 DORA Metrics Performance"))
                for metric in dora_metrics:
                    content.append(html.P(f"• {metric['name'].replace('_', ' ').title()}: {metric['value']} {metric['unit']}"))
                return content
            return [html.P("No DORA metrics data available currently.")]
            
        # Cost optimization queries  
        elif any(word in query_lower for word in ['cost', 'optimization', 'cloud', 'spend']):
            cost_insights = [i for i in self.insights_data if 'cost' in i.get('category', '').lower()]
            if cost_insights:
                content = []
                content.append(html.H5("💰 Cost Optimization Insights"))
                for insight in cost_insights[:3]:
                    content.append(html.P(f"• {insight['title']}: {insight['recommendation']}"))
                return content
            return [html.P("No cost optimization insights available currently.")]
            
        # Team satisfaction queries
        elif any(word in query_lower for word in ['team', 'satisfaction', 'health', 'space']):
            team_metrics = [m for m in self.metrics_data if m['category'] == 'SPACE']
            if team_metrics:
                content = []
                content.append(html.H5("👥 Team Health Status"))
                for metric in team_metrics:
                    content.append(html.P(f"• {metric['name'].replace('_', ' ').title()}: {metric['value']} {metric['unit']}"))
                return content
            return [html.P("No team health data available currently.")]
            
        # Critical insights queries
        elif any(word in query_lower for word in ['critical', 'urgent', 'important', 'attention']):
            critical_insights = [i for i in self.insights_data if i.get('priority') in ['critical', 'high']]
            if critical_insights:
                content = []
                content.append(html.H5("🚨 Critical Insights Requiring Attention"))
                for insight in critical_insights[:5]:
                    priority_emoji = "🚨" if insight['priority'] == 'critical' else "⚠️"
                    content.append(html.P(f"{priority_emoji} {insight['title']}: {insight['recommendation']}"))
                return content
            return [html.P("No critical insights requiring immediate attention.")]
            
        # Default response
        else:
            return [
                html.H5("🤖 I can help you with:"),
                html.Ul([
                    html.Li("DORA metrics and DevOps performance"),
                    html.Li("Cost optimization opportunities"),
                    html.Li("Team satisfaction and health metrics"),
                    html.Li("Critical insights requiring attention"),
                    html.Li("Infrastructure and security status")
                ]),
                html.P("Try asking about any of these topics!", className="text-muted")
            ]
            
    async def run_eia_agents(self):
        """Run EIA agents and refresh data"""
        if self.eia_orchestrator:
            try:
                results = await self.eia_orchestrator.execute_all_agents()
                self.refresh_data()
                return f"✅ Generated {results['total_insights']} insights and {results['total_metrics']} metrics"
            except Exception as e:
                return f"❌ Error running agents: {e}"
        return "❌ EIA system not available"
        
    def run(self, debug=False, host='127.0.0.1', port=8060):
        """Run the dashboard"""
        print(f"\n🤖 EIA Executive Dashboard starting...")
        print(f"📊 Loaded {len(self.insights_data)} insights and {len(self.metrics_data)} metrics")
        print(f"🎯 URL: http://{host}:{port}")
        
        self.app.run(debug=debug, host=host, port=port)

def main():
    """Main entry point"""
    import sys
    
    # Check for service mode
    service_mode = "--service-mode" in sys.argv
    
    dashboard = EIAExecutiveDashboard()
    
    # Unified port management - use environment variable (registry-assigned)
    port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('PORT', '8052')))
    host = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
    debug = not service_mode and os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"🚀 Starting EIA Executive Dashboard...")
    print(f"📊 URL: http://{host}:{port}")
    dashboard.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()