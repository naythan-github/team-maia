#!/usr/bin/env python3
"""
AI Business Intelligence Dashboard - Comprehensive business analytics and insights
==================================================================================

Provides AI-powered business intelligence, analytics, and strategic insights
for enterprise decision making and performance monitoring.

Author: Maia System
Version: 2.0.0
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict

# Flask and Dash imports for web service
from flask import Flask, jsonify
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

# Import existing Maia infrastructure with proper error handling
try:
    from claude.tools.predictive_analytics_engine import PredictiveAnalyticsEngine
except ImportError:
    class PredictiveAnalyticsEngine:
        def predict_career_trajectory(self, horizon_months=6):
            return {"trend": "positive", "confidence": 0.7}

try:
    from claude.tools.agent_message_bus import get_message_bus, MessageType, MessagePriority
except ImportError:
    def get_message_bus(): return None
    class MessageType: pass
    class MessagePriority: pass

@dataclass
class BusinessMetric:
    """Business metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    trend: float = 0.0

@dataclass
class BusinessInsight:
    """Business insight data structure"""
    title: str
    description: str
    category: str
    impact_score: float
    confidence: float
    recommended_actions: List[str]
    data_sources: List[str]

class AIBusinessIntelligenceDashboard:
    """
    AI-powered Business Intelligence Dashboard
    Provides comprehensive business analytics and strategic insights
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the business intelligence dashboard"""
        self.config = config or {}
        self.metrics = {}
        self.insights_cache = {}
        self.last_update = None
        
        # Initialize Dash application for web service
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.flask_server = self.app.server
        self.setup_health_endpoints()
        self.setup_layout()
        self.setup_callbacks()
        
    def add_metric(self, metric: BusinessMetric) -> None:
        """Add a business metric"""
        if metric.category not in self.metrics:
            self.metrics[metric.category] = []
        
        self.metrics[metric.category].append(metric)
        
        # Keep only last 90 days of data per category
        cutoff_date = datetime.now() - timedelta(days=90)
        self.metrics[metric.category] = [
            m for m in self.metrics[metric.category] 
            if m.timestamp >= cutoff_date
        ]
        
        self.last_update = datetime.now()
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        dashboard_data = {
            "summary": self._generate_summary(),
            "key_metrics": self._get_key_metrics(),
            "insights": self._generate_insights(),
            "trends": self._analyze_trends(),
            "recommendations": self._generate_recommendations(),
            "last_updated": self.last_update.isoformat() if self.last_update else None
        }
        
        return dashboard_data
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate dashboard summary"""
        total_metrics = sum(len(metrics) for metrics in self.metrics.values())
        active_categories = len([cat for cat, metrics in self.metrics.items() if metrics])
        
        # Calculate overall health score
        health_scores = []
        for category, metrics in self.metrics.items():
            if metrics:
                recent_metrics = [m for m in metrics if m.timestamp >= datetime.now() - timedelta(days=7)]
                if recent_metrics:
                    avg_trend = statistics.mean([m.trend for m in recent_metrics])
                    health_scores.append(max(0, min(1, 0.5 + avg_trend)))
        
        overall_health = statistics.mean(health_scores) if health_scores else 0.5
        
        return {
            "total_metrics": total_metrics,
            "active_categories": active_categories,
            "overall_health_score": overall_health,
            "health_status": self._get_health_status(overall_health),
            "data_coverage_days": 90
        }
    
    def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key business metrics"""
        key_metrics = {}
        
        for category, metrics in self.metrics.items():
            if not metrics:
                continue
                
            # Get most recent metrics
            recent_metrics = sorted(metrics, key=lambda m: m.timestamp, reverse=True)[:5]
            
            category_data = []
            for metric in recent_metrics:
                category_data.append({
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "trend": metric.trend,
                    "timestamp": metric.timestamp.isoformat()
                })
            
            key_metrics[category] = category_data
        
        return key_metrics
    
    def _generate_insights(self) -> List[Dict[str, Any]]:
        """Generate AI-powered business insights"""
        insights = []
        
        for category, metrics in self.metrics.items():
            if len(metrics) < 2:
                continue
                
            # Analyze trends
            recent_metrics = [m for m in metrics if m.timestamp >= datetime.now() - timedelta(days=30)]
            if len(recent_metrics) >= 3:
                values = [m.value for m in recent_metrics]
                trend = self._calculate_trend(values)
                
                if abs(trend) > 0.1:  # Significant trend
                    insight = BusinessInsight(
                        title=f"{category.title()} Performance {'Improving' if trend > 0 else 'Declining'}",
                        description=f"{category.title()} metrics show a {'positive' if trend > 0 else 'negative'} trend over the last 30 days",
                        category=category,
                        impact_score=abs(trend),
                        confidence=min(0.9, abs(trend) * 2),
                        recommended_actions=self._get_trend_recommendations(category, trend),
                        data_sources=[f"{len(recent_metrics)} {category} metrics"]
                    )
                    insights.append(asdict(insight))
        
        return insights[:10]  # Limit to top 10 insights
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze business trends"""
        trends = {}
        
        for category, metrics in self.metrics.items():
            if len(metrics) < 5:
                continue
            
            # Get last 30 days
            recent_metrics = [m for m in metrics if m.timestamp >= datetime.now() - timedelta(days=30)]
            if len(recent_metrics) < 3:
                continue
            
            # Sort by timestamp
            recent_metrics.sort(key=lambda m: m.timestamp)
            values = [m.value for m in recent_metrics]
            
            trend_slope = self._calculate_trend(values)
            volatility = statistics.stdev(values) if len(values) > 1 else 0
            
            trends[category] = {
                "trend_slope": trend_slope,
                "volatility": volatility,
                "data_points": len(recent_metrics),
                "period_days": 30,
                "status": "increasing" if trend_slope > 0.05 else "decreasing" if trend_slope < -0.05 else "stable"
            }
        
        return trends
    
    def _generate_recommendations(self) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Analyze overall performance
        all_trends = []
        for category, metrics in self.metrics.items():
            if len(metrics) >= 3:
                recent_values = [m.value for m in metrics[-7:]]  # Last 7 data points
                if len(recent_values) >= 2:
                    trend = self._calculate_trend(recent_values)
                    all_trends.append((category, trend))
        
        # Generate recommendations based on trends
        declining_categories = [cat for cat, trend in all_trends if trend < -0.1]
        improving_categories = [cat for cat, trend in all_trends if trend > 0.1]
        
        if declining_categories:
            recommendations.append(f"Focus attention on declining areas: {', '.join(declining_categories)}")
        
        if improving_categories:
            recommendations.append(f"Scale successful strategies from: {', '.join(improving_categories)}")
        
        if len(self.metrics) > 3:
            recommendations.append("Consider consolidating metrics to focus on key performance indicators")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope for a series of values"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status from score"""
        if health_score >= 0.8:
            return "Excellent"
        elif health_score >= 0.6:
            return "Good"
        elif health_score >= 0.4:
            return "Fair"
        else:
            return "Needs Attention"
    
    def _get_trend_recommendations(self, category: str, trend: float) -> List[str]:
        """Get recommendations based on category and trend"""
        if trend > 0:
            return [
                f"Continue current {category} strategies",
                f"Consider scaling {category} initiatives",
                f"Document {category} success factors"
            ]
        else:
            return [
                f"Review {category} processes for improvements",
                f"Investigate {category} performance issues",
                f"Consider {category} strategy adjustments"
            ]
    
    def setup_health_endpoints(self):
        """Setup standardized health check endpoints"""
        @self.flask_server.route('/health')
        def health_check():
            """Standardized health check endpoint"""
            try:
                # Calculate current health metrics
                dashboard_data = self.generate_dashboard_data()
                summary = dashboard_data.get('summary', {})
                
                uptime_seconds = int((datetime.now() - (self.last_update or datetime.now())).total_seconds())
                
                return jsonify({
                    "status": "healthy" if summary.get('overall_health_score', 0) > 0.6 else "degraded",
                    "uptime": uptime_seconds,
                    "version": "2.0.0",
                    "service": "ai_business_intelligence_dashboard",
                    "health_score": summary.get('overall_health_score', 0),
                    "active_categories": summary.get('active_categories', 0),
                    "total_metrics": summary.get('total_metrics', 0),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "uptime": 0,
                    "version": "2.0.0",
                    "service": "ai_business_intelligence_dashboard",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
    
    def setup_layout(self):
        """Setup the dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("🤖 AI Business Intelligence Dashboard", className="mb-4"),
                    html.P("Comprehensive business analytics and strategic insights", 
                           className="text-muted mb-4")
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("📊 Key Metrics", className="card-title"),
                            html.Div(id="metrics-summary")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("💡 Strategic Insights", className="card-title"),
                            html.Div(id="insights-summary")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("📈 Business Trends", className="card-title"),
                            dcc.Graph(id="trends-chart")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("🎯 Recommendations", className="card-title"),
                            html.Div(id="recommendations-list")
                        ])
                    ])
                ], width=12)
            ])
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        @self.app.callback(
            [Output('metrics-summary', 'children'),
             Output('insights-summary', 'children'),
             Output('trends-chart', 'figure'),
             Output('recommendations-list', 'children')],
            [Input('metrics-summary', 'id')]  # Dummy input for initial load
        )
        def update_dashboard(_):
            # Load sample data for demo
            self._load_sample_data()
            
            dashboard_data = self.generate_dashboard_data()
            
            # Metrics summary
            metrics_cards = []
            for category, metrics_list in self.metrics.items():
                if metrics_list:
                    latest_metric = metrics_list[-1]
                    metrics_cards.append(
                        dbc.Alert([
                            html.H6(f"{latest_metric.name}: {latest_metric.value} {latest_metric.unit}"),
                            html.Small(f"Category: {category}")
                        ], color="info", className="mb-2")
                    )
            
            # Insights summary
            insights_list = []
            for insight in dashboard_data.get('insights', [])[:3]:
                insights_list.append(
                    dbc.Alert([
                        html.H6(insight.get('title', 'Insight')),
                        html.P(insight.get('description', ''))
                    ], color="success", className="mb-2")
                )
            
            # Trends chart
            fig = go.Figure()
            for category, metrics_list in self.metrics.items():
                if metrics_list:
                    dates = [m.timestamp for m in metrics_list]
                    values = [m.value for m in metrics_list]
                    fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', name=category))
            
            fig.update_layout(title="Business Metrics Trends", xaxis_title="Date", yaxis_title="Value")
            
            # Recommendations
            recommendations = []
            for rec in dashboard_data.get('recommendations', [])[:5]:
                recommendations.append(html.Li(rec, className="mb-1"))
            
            return metrics_cards, insights_list, fig, html.Ul(recommendations)
    
    def _load_sample_data(self):
        """Load sample data for demonstration"""
        if not self.metrics:
            sample_metrics = [
                BusinessMetric("Revenue", 100000, "USD", datetime.now() - timedelta(days=30), "financial", 0.1),
                BusinessMetric("Revenue", 105000, "USD", datetime.now() - timedelta(days=20), "financial", 0.1),
                BusinessMetric("Revenue", 110000, "USD", datetime.now() - timedelta(days=10), "financial", 0.1),
                BusinessMetric("Customer Satisfaction", 4.2, "rating", datetime.now() - timedelta(days=25), "customer", 0.05),
                BusinessMetric("Customer Satisfaction", 4.3, "rating", datetime.now() - timedelta(days=15), "customer", 0.05),
                BusinessMetric("Employee Productivity", 85, "%", datetime.now() - timedelta(days=20), "operations", -0.02),
                BusinessMetric("Employee Productivity", 87, "%", datetime.now() - timedelta(days=10), "operations", -0.02)
            ]
            
            for metric in sample_metrics:
                self.add_metric(metric)
    
    def run(self, host="127.0.0.1", port=8050, debug=False):
        """Run the dashboard web service"""
        print(f"🚀 Starting AI Business Intelligence Dashboard...")
        print(f"🌐 URL: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Factory function
def create_dashboard(config: Optional[Dict[str, Any]] = None) -> AIBusinessIntelligenceDashboard:
    """Create an AI business intelligence dashboard instance"""
    return AIBusinessIntelligenceDashboard(config)

def main():
    """Main entry point with enterprise service management"""
    import sys
    
    # Check for service mode
    service_mode = "--service-mode" in sys.argv
    
    dashboard = create_dashboard()
    
    # Unified port management - use environment variable (registry-assigned)
    port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('MAIA_DASHBOARD_PORT', os.environ.get('PORT', '8054'))))
    host = os.environ.get('DASHBOARD_HOST', os.environ.get('MAIA_DASHBOARD_HOST', '127.0.0.1'))
    debug = not service_mode and os.environ.get('DEBUG', 'false').lower() == 'true'

    if not service_mode:
        # Test mode - show dashboard data summary
        data = dashboard.generate_dashboard_data()
        print(f"Dashboard generated with {data['summary']['total_metrics']} metrics")
        print(f"Health status: {data['summary']['health_status']}")

    print(f"🚀 Starting AI Business Intelligence Dashboard...")
    print(f"🌐 URL: http://{host}:{port}")
    dashboard.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()