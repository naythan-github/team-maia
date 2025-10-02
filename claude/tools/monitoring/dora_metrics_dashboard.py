#!/usr/bin/env python3
"""
DORA Metrics Dashboard
Real-time visualization of DevOps Research and Assessment (DORA) metrics
Integrated with EIA system for enterprise intelligence automation
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Flask and Dash imports
from flask import Flask, jsonify
import dash
from dash import dcc, html, Input, Output, callback_context, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

# Add Maia tools to path
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(MAIA_ROOT / "claude" / "tools" / "🤖_intelligence"))

try:
    from dora_metrics_automation import DORAMetricsCollector, DORAMetric
    DORA_AVAILABLE = True
except ImportError:
    DORA_AVAILABLE = False
    print("⚠️ DORA Metrics Automation not available")

class DORAMetricsDashboard:
    """DORA Metrics Dashboard with EIA Integration"""
    
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.flask_server = self.app.server
        self.maia_root = MAIA_ROOT
        self.data_dir = self.maia_root / "claude/data/eia"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "dora_metrics.db"
        
        # Initialize DORA collector
        self.collector = DORAMetricsCollector() if DORA_AVAILABLE else None
        
        # Setup health endpoints
        self.setup_health_endpoints()
        
        # Initialize dashboard layout
        self.setup_layout()
        self.setup_callbacks()
        
        # Load initial data
        self.refresh_metrics()
        
    def setup_health_endpoints(self):
        """Setup standardized health check endpoints"""
        @self.flask_server.route('/health')
        def health_check():
            """Standardized health check endpoint"""
            try:
                # Get latest DORA metrics
                metrics = self.refresh_metrics()
                latest_metrics = metrics[-1] if metrics else {}
                
                # Calculate performance level for health assessment
                performance = self._calculate_performance_level(latest_metrics)
                is_healthy = performance.get('level') in ['Elite', 'High']
                
                return jsonify({
                    "status": "healthy" if is_healthy else "degraded",
                    "uptime": 0,  # Could be enhanced with actual uptime tracking
                    "version": "1.0.0",
                    "service": "dora_metrics_dashboard",
                    "performance_level": performance.get('level', 'Unknown'),
                    "deployment_frequency": latest_metrics.get('deployment_frequency', 0),
                    "lead_time_hours": latest_metrics.get('lead_time_for_changes', 0),
                    "change_failure_rate": latest_metrics.get('change_failure_rate', 0),
                    "recovery_time_hours": latest_metrics.get('mean_time_to_recovery', 0),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "uptime": 0,
                    "version": "1.0.0",
                    "service": "dora_metrics_dashboard",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
    
    def setup_layout(self):
        """Setup dashboard layout"""
        
        # Header
        header = dbc.Row([
            dbc.Col([
                html.H1("🎯 DORA Metrics Dashboard", className="text-center mb-3"),
                html.P("Real-time DevOps performance monitoring and intelligence", 
                      className="text-center text-muted")
            ])
        ], className="mb-4")
        
        # KPI Cards
        kpi_row = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Deployment Frequency", className="card-title"),
                        html.H2(id="deployment-freq", className="text-primary"),
                        html.P(id="deployment-status", className="text-muted")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Lead Time", className="card-title"),
                        html.H2(id="lead-time", className="text-success"),
                        html.P(id="lead-time-status", className="text-muted")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Change Failure Rate", className="card-title"),
                        html.H2(id="failure-rate", className="text-warning"),
                        html.P(id="failure-status", className="text-muted")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Recovery Time", className="card-title"),
                        html.H2(id="recovery-time", className="text-info"),
                        html.P(id="recovery-status", className="text-muted")
                    ])
                ])
            ], md=3)
        ], className="mb-4")
        
        # Performance Summary
        performance_card = dbc.Card([
            dbc.CardHeader("🏆 DORA Performance Level"),
            dbc.CardBody([
                html.Div(id="performance-level", className="text-center mb-3"),
                html.Div(id="performance-description", className="text-muted")
            ])
        ], className="mb-4")
        
        # Charts Row
        charts_row = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 DORA Metrics Trends"),
                    dbc.CardBody([
                        dcc.Graph(id="dora-trends")
                    ])
                ])
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎯 Performance Breakdown"),
                    dbc.CardBody([
                        dcc.Graph(id="performance-radar")
                    ])
                ])
            ], md=4)
        ], className="mb-4")
        
        # Recommendations
        recommendations_card = dbc.Card([
            dbc.CardHeader("💡 Recommendations"),
            dbc.CardBody([
                html.Div(id="recommendations")
            ])
        ], className="mb-4")
        
        # Refresh controls
        controls = dbc.Row([
            dbc.Col([
                dbc.Button("🔄 Refresh Metrics", id="refresh-btn", 
                          color="primary", className="me-2"),
                html.Span(id="last-updated", className="text-muted")
            ])
        ])
        
        # Combine all components
        self.app.layout = dbc.Container([
            header,
            kpi_row,
            performance_card,
            charts_row,
            recommendations_card,
            controls,
            dcc.Interval(id="auto-refresh", interval=300000, n_intervals=0)  # 5 minutes
        ], fluid=True)
        
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output("deployment-freq", "children"),
             Output("deployment-status", "children"),
             Output("lead-time", "children"),
             Output("lead-time-status", "children"),
             Output("failure-rate", "children"),
             Output("failure-status", "children"),
             Output("recovery-time", "children"),
             Output("recovery-status", "children"),
             Output("performance-level", "children"),
             Output("performance-description", "children"),
             Output("dora-trends", "figure"),
             Output("performance-radar", "figure"),
             Output("recommendations", "children"),
             Output("last-updated", "children")],
            [Input("refresh-btn", "n_clicks"),
             Input("auto-refresh", "n_intervals")]
        )
        def update_dashboard(n_clicks, n_intervals):
            """Update all dashboard components"""
            
            # Refresh metrics
            metrics = self.refresh_metrics()
            
            if not metrics:
                return self._empty_dashboard()
            
            # Extract latest metrics
            latest = metrics[-1] if metrics else {}
            
            # KPI values
            deployment_freq = f"{latest.get('deployment_frequency', 0):.1f}/week"
            deployment_status = "Elite" if latest.get('deployment_frequency', 0) > 10 else "High"
            
            lead_time_hours = latest.get('lead_time_for_changes', 0)
            lead_time = f"{lead_time_hours:.1f}h" if lead_time_hours < 24 else f"{lead_time_hours/24:.1f}d"
            lead_time_status = "Elite" if lead_time_hours < 24 else "High"
            
            failure_rate = f"{latest.get('change_failure_rate', 0)*100:.1f}%"
            failure_status = "Elite" if latest.get('change_failure_rate', 0) < 0.1 else "High"
            
            recovery_time = f"{latest.get('mean_time_to_recovery', 0):.1f}h"
            recovery_status = "Elite" if latest.get('mean_time_to_recovery', 0) < 1 else "High"
            
            # Performance level
            performance = self._calculate_performance_level(latest)
            performance_badge = dbc.Badge(performance['level'], 
                                        color=performance['color'], 
                                        className="fs-3")
            performance_desc = html.P(performance['description'])
            
            # Create trend chart
            trend_fig = self._create_trend_chart(metrics)
            
            # Create radar chart
            radar_fig = self._create_radar_chart(latest)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(latest)
            
            # Last updated
            last_updated = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            
            return (
                deployment_freq, deployment_status,
                lead_time, lead_time_status, 
                failure_rate, failure_status,
                recovery_time, recovery_status,
                performance_badge, performance_desc,
                trend_fig, radar_fig,
                recommendations, last_updated
            )
            
    def refresh_metrics(self) -> List[Dict]:
        """Refresh DORA metrics from database"""
        
        if not DORA_AVAILABLE:
            return self._demo_metrics()
            
        try:
            # Collect fresh metrics
            if self.collector:
                self.collector.collect_all_metrics()
            
            # Read from database
            metrics = []
            if self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT * FROM dora_metrics 
                        ORDER BY collected_at DESC 
                        LIMIT 30
                    """)
                    
                    columns = [desc[0] for desc in cursor.description]
                    for row in cursor.fetchall():
                        metrics.append(dict(zip(columns, row)))
                        
            return metrics
            
        except Exception as e:
            print(f"Error refreshing metrics: {e}")
            return self._demo_metrics()
            
    def _demo_metrics(self) -> List[Dict]:
        """Generate demo metrics data"""
        return [
            {
                'deployment_frequency': 8.5,
                'lead_time_for_changes': 12.5,
                'change_failure_rate': 0.067,
                'mean_time_to_recovery': 2.3,
                'collected_at': datetime.now().isoformat()
            }
        ]
        
    def _calculate_performance_level(self, metrics: Dict) -> Dict:
        """Calculate DORA performance level"""
        
        if not metrics:
            return {'level': 'Unknown', 'color': 'secondary', 'description': 'No data available'}
        
        # DORA performance criteria
        deployment_freq = metrics.get('deployment_frequency', 0)
        lead_time = metrics.get('lead_time_for_changes', float('inf'))
        failure_rate = metrics.get('change_failure_rate', 1)
        recovery_time = metrics.get('mean_time_to_recovery', float('inf'))
        
        # Elite performers
        if (deployment_freq > 10 and lead_time < 24 and 
            failure_rate < 0.1 and recovery_time < 1):
            return {
                'level': 'Elite', 
                'color': 'success',
                'description': 'Top 10% of performers. Exceptional DevOps capabilities.'
            }
        # High performers
        elif (deployment_freq > 1 and lead_time < 168 and 
              failure_rate < 0.2 and recovery_time < 24):
            return {
                'level': 'High', 
                'color': 'primary',
                'description': 'Strong DevOps performance with room for elite optimization.'
            }
        # Medium performers
        elif (deployment_freq > 0.1 and lead_time < 720 and
              failure_rate < 0.3 and recovery_time < 168):
            return {
                'level': 'Medium', 
                'color': 'warning',
                'description': 'Moderate performance. Focus on automation and processes.'
            }
        else:
            return {
                'level': 'Low', 
                'color': 'danger',
                'description': 'Significant improvement opportunities across all metrics.'
            }
            
    def _create_trend_chart(self, metrics: List[Dict]) -> go.Figure:
        """Create DORA metrics trend chart"""
        
        if not metrics:
            return go.Figure().add_annotation(text="No data available")
        
        df = pd.DataFrame(metrics)
        
        fig = go.Figure()
        
        # Add traces for each metric (normalized)
        if 'deployment_frequency' in df.columns:
            fig.add_trace(go.Scatter(
                y=df['deployment_frequency'],
                name='Deployment Frequency',
                line_color='#1f77b4'
            ))
        
        if 'lead_time_for_changes' in df.columns:
            # Invert lead time (lower is better)
            fig.add_trace(go.Scatter(
                y=100 - df['lead_time_for_changes'], 
                name='Lead Time (inverted)',
                line_color='#2ca02c'
            ))
        
        fig.update_layout(
            title="DORA Metrics Trends",
            xaxis_title="Time",
            yaxis_title="Performance Score",
            height=400
        )
        
        return fig
        
    def _create_radar_chart(self, metrics: Dict) -> go.Figure:
        """Create performance radar chart"""
        
        if not metrics:
            return go.Figure().add_annotation(text="No data available")
        
        # Normalize metrics to 0-100 scale
        deployment_score = min(metrics.get('deployment_frequency', 0) * 10, 100)
        lead_time_score = max(100 - metrics.get('lead_time_for_changes', 0), 0)
        failure_score = max(100 - metrics.get('change_failure_rate', 0) * 1000, 0)
        recovery_score = max(100 - metrics.get('mean_time_to_recovery', 0) * 10, 0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[deployment_score, lead_time_score, failure_score, recovery_score],
            theta=['Deployment Frequency', 'Lead Time', 'Change Success', 'Recovery Speed'],
            fill='toself',
            name='Current Performance'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            height=300
        )
        
        return fig
        
    def _generate_recommendations(self, metrics: Dict) -> List:
        """Generate improvement recommendations"""
        
        if not metrics:
            return [html.Li("No data available for recommendations")]
        
        recommendations = []
        
        # Check deployment frequency
        if metrics.get('deployment_frequency', 0) < 1:
            recommendations.append(
                html.Li("🚀 Increase deployment frequency through automation and CI/CD optimization")
            )
        
        # Check lead time
        if metrics.get('lead_time_for_changes', 0) > 24:
            recommendations.append(
                html.Li("⚡ Reduce lead time by streamlining development and testing processes")
            )
        
        # Check failure rate
        if metrics.get('change_failure_rate', 0) > 0.2:
            recommendations.append(
                html.Li("🛡️ Improve change success rate with better testing and quality gates")
            )
        
        # Check recovery time
        if metrics.get('mean_time_to_recovery', 0) > 24:
            recommendations.append(
                html.Li("🔧 Reduce recovery time through better monitoring and response automation")
            )
        
        if not recommendations:
            recommendations.append(
                html.Li("🎉 Excellent performance! Consider sharing best practices with other teams")
            )
        
        return recommendations
        
    def _empty_dashboard(self):
        """Return empty dashboard values"""
        empty_fig = go.Figure().add_annotation(text="No data available")
        
        return (
            "N/A", "No data", "N/A", "No data", 
            "N/A", "No data", "N/A", "No data",
            dbc.Badge("Unknown", color="secondary"), 
            html.P("No data available"),
            empty_fig, empty_fig,
            [html.Li("No recommendations available")],
            "Never updated"
        )
        
    def run(self, debug=False, host='127.0.0.1', port=8061):
        """Run the dashboard"""
        print(f"\n🎯 DORA Metrics Dashboard starting...")
        print(f"📊 Database: {self.db_path}")
        print(f"🌐 URL: http://{host}:{port}")
        
        self.app.run(debug=debug, host=host, port=port)

def main():
    """Main entry point"""
    import sys
    
    # Check for service mode
    service_mode = "--service-mode" in sys.argv
    
    dashboard = DORAMetricsDashboard()
    
    # Unified port management - use environment variable (registry-assigned)
    port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('PORT', '8057')))
    host = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
    debug = not service_mode and os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"🚀 Starting DORA Metrics Dashboard...")
    print(f"📊 URL: http://{host}:{port}")
    dashboard.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()