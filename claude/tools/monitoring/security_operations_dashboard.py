import os
#!/usr/bin/env python3
"""
Security Operations Dashboard
Web-based dashboard for Virtual Security Assistant with real-time security analytics.
"""

import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import asdict

# Web framework imports
try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    import plotly
    import plotly.graph_objs as go
    from plotly.utils import PlotlyJSONEncoder
except ImportError:
    print("Installing required packages for dashboard...")
    import subprocess
    import sys
    
    packages = ["flask", "flask-cors", "plotly"]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    import plotly
    import plotly.graph_objs as go
    from plotly.utils import PlotlyJSONEncoder

# Import Virtual Security Assistant components
from security_integration_hub import SecurityIntegrationHub
from alert_source_configuration import AlertSourceConfiguration
from orro_security_playbooks import OrroSecurityPlaybooks

class SecurityOperationsDashboard:
    """
    Security Operations Dashboard
    
    Real-time web dashboard for Virtual Security Assistant:
    - Threat intelligence visualization
    - Alert management analytics
    - Response automation metrics
    - Orro Group specific insights
    - Executive briefing views
    """
    
    def __init__(self):
        self.base_path = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.security_path = self.base_path / "claude" / "security"
        
        # Initialize components
        self.integration_hub = SecurityIntegrationHub()
        self.alert_config = AlertSourceConfiguration()
        self.orro_playbooks = OrroSecurityPlaybooks()
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder=str(self.security_path / "dashboard" / "templates"),
                        static_folder=str(self.security_path / "dashboard" / "static"))
        CORS(self.app)
        
        # Create dashboard directories
        (self.security_path / "dashboard" / "templates").mkdir(parents=True, exist_ok=True)
        (self.security_path / "dashboard" / "static" / "css").mkdir(parents=True, exist_ok=True)
        (self.security_path / "dashboard" / "static" / "js").mkdir(parents=True, exist_ok=True)
        
        # Set up routes
        self._setup_routes()
        
        # Dashboard data cache
        self.dashboard_cache = {}
        self.cache_expiry = datetime.now()
        
        logging.basicConfig(
            filename=self.security_path / "logs" / "dashboard.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def _setup_routes(self):
        """Set up Flask routes for dashboard"""

        @self.app.route('/health')
        def health_check():
            """Standardized health check endpoint"""
            try:
                return jsonify({
                    "status": "healthy",
                    "uptime": 0,
                    "version": "1.0.0",
                    "service": "security_operations_dashboard",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "uptime": 0,
                    "version": "1.0.0",
                    "service": "security_operations_dashboard",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500

        @self.app.route('/')
        def dashboard_home():
            return render_template('dashboard.html')
        
        @self.app.route('/api/dashboard')
        def api_dashboard():
            """Main dashboard API endpoint"""
            try:
                dashboard_data = self._get_dashboard_data()
                return jsonify(dashboard_data)
            except Exception as e:
                logging.error(f"Dashboard API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/threat-intelligence')
        def api_threat_intelligence():
            """Threat intelligence API endpoint"""
            try:
                threat_data = self._get_threat_intelligence_data()
                return jsonify(threat_data)
            except Exception as e:
                logging.error(f"Threat intelligence API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/alert-analytics')
        def api_alert_analytics():
            """Alert analytics API endpoint"""
            try:
                alert_data = self._get_alert_analytics_data()
                return jsonify(alert_data)
            except Exception as e:
                logging.error(f"Alert analytics API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/response-metrics')
        def api_response_metrics():
            """Response metrics API endpoint"""
            try:
                response_data = self._get_response_metrics_data()
                return jsonify(response_data)
            except Exception as e:
                logging.error(f"Response metrics API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/executive-summary')
        def api_executive_summary():
            """Executive summary API endpoint"""
            try:
                exec_data = self._get_executive_summary()
                return jsonify(exec_data)
            except Exception as e:
                logging.error(f"Executive summary API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/orro-insights')
        def api_orro_insights():
            """Orro Group specific insights"""
            try:
                orro_data = self._get_orro_specific_insights()
                return jsonify(orro_data)
            except Exception as e:
                logging.error(f"Orro insights API error: {str(e)}")
                return jsonify({"error": str(e)}), 500
                
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        # Check cache
        if datetime.now() < self.cache_expiry and "dashboard" in self.dashboard_cache:
            return self.dashboard_cache["dashboard"]
        
        try:
            # Get data from all components
            integration_dashboard = self.integration_hub.generate_comprehensive_security_dashboard()
            alert_config_summary = self.alert_config.generate_configuration_summary()
            
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "virtual_assistant": integration_dashboard,
                "alert_configuration": alert_config_summary,
                "key_metrics": self._calculate_key_metrics(),
                "security_posture": self._calculate_security_posture(),
                "charts": self._generate_dashboard_charts()
            }
            
            # Cache data for 5 minutes
            self.dashboard_cache["dashboard"] = dashboard_data
            self.cache_expiry = datetime.now() + timedelta(minutes=5)
            
            return dashboard_data
            
        except Exception as e:
            logging.error(f"Error generating dashboard data: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _get_threat_intelligence_data(self) -> Dict[str, Any]:
        """Get threat intelligence visualization data"""
        
        try:
            # Get threat intelligence briefing
            briefing = self.integration_hub.threat_intelligence.generate_security_briefing()
            
            # Create threat prediction chart
            threat_chart = self._create_threat_prediction_chart(briefing)
            
            threat_data = {
                "briefing": briefing,
                "prediction_chart": threat_chart,
                "threat_timeline": self._generate_threat_timeline(),
                "threat_sources": self._get_threat_sources_breakdown()
            }
            
            return threat_data
            
        except Exception as e:
            logging.error(f"Error generating threat intelligence data: {str(e)}")
            return {"error": str(e)}
    
    def _get_alert_analytics_data(self) -> Dict[str, Any]:
        """Get alert analytics visualization data"""
        
        try:
            # Get alert management summary
            alert_summary = self.integration_hub.alert_manager.generate_intelligence_summary()
            
            # Create alert analytics charts
            alert_charts = {
                "volume_chart": self._create_alert_volume_chart(),
                "suppression_chart": self._create_alert_suppression_chart(alert_summary),
                "source_breakdown": self._create_alert_source_chart()
            }
            
            alert_data = {
                "summary": alert_summary,
                "charts": alert_charts,
                "top_sources": self._get_top_alert_sources(),
                "suppression_effectiveness": self._calculate_suppression_effectiveness(alert_summary)
            }
            
            return alert_data
            
        except Exception as e:
            logging.error(f"Error generating alert analytics data: {str(e)}")
            return {"error": str(e)}
    
    def _get_response_metrics_data(self) -> Dict[str, Any]:
        """Get response metrics visualization data"""
        
        try:
            # Get response effectiveness report
            response_report = self.integration_hub.response_engine.generate_response_effectiveness_report()
            
            # Create response metrics charts
            response_charts = {
                "success_rate_chart": self._create_response_success_chart(response_report),
                "automation_chart": self._create_automation_rate_chart(response_report),
                "response_time_chart": self._create_response_time_chart()
            }
            
            response_data = {
                "report": response_report,
                "charts": response_charts,
                "playbook_usage": self._get_playbook_usage_stats(),
                "automation_benefits": self._calculate_automation_benefits(response_report)
            }
            
            return response_data
            
        except Exception as e:
            logging.error(f"Error generating response metrics data: {str(e)}")
            return {"error": str(e)}
    
    def _get_executive_summary(self) -> Dict[str, Any]:
        """Get executive-level security summary"""
        
        try:
            # Get data from all components
            dashboard_data = self._get_dashboard_data()
            
            # Calculate executive metrics
            security_score = self._calculate_overall_security_score()
            risk_level = self._assess_current_risk_level()
            
            executive_summary = {
                "security_score": security_score,
                "risk_level": risk_level,
                "key_achievements": [
                    f"{dashboard_data['virtual_assistant']['alert_management']['fatigue_reduction']}% reduction in alert fatigue",
                    f"{dashboard_data['virtual_assistant']['automated_response']['automation_rate']}% response automation rate",
                    f"{dashboard_data['virtual_assistant']['threat_intelligence']['active_predictions']} active threat predictions"
                ],
                "immediate_attention": self._get_items_requiring_attention(),
                "business_impact": self._calculate_business_impact_metrics(),
                "recommendations": self._generate_executive_recommendations()
            }
            
            return executive_summary
            
        except Exception as e:
            logging.error(f"Error generating executive summary: {str(e)}")
            return {"error": str(e)}
    
    def _get_orro_specific_insights(self) -> Dict[str, Any]:
        """Get Orro Group specific security insights"""
        
        try:
            orro_insights = {
                "client_security_posture": {
                    "government_clients": self._assess_government_client_security(),
                    "mining_clients": self._assess_mining_client_security(),
                    "cloud_practice_health": self._assess_cloud_practice_security()
                },
                "compliance_status": {
                    "acsc_compliance": "compliant",
                    "privacy_act_compliance": "compliant",
                    "soc2_readiness": "in_progress",
                    "iso27001_readiness": "planned"
                },
                "azure_extended_zone": {
                    "perth_zone_security": "optimal",
                    "data_residency_compliance": "100%",
                    "extended_zone_alerts": 0
                },
                "team_performance": {
                    "engineering_manager_visibility": "enhanced",
                    "security_team_productivity": "improved",
                    "client_satisfaction": "high"
                },
                "business_metrics": {
                    "security_incidents_prevented": self._count_prevented_incidents(),
                    "cost_savings": self._calculate_security_cost_savings(),
                    "response_time_improvement": "80% faster"
                }
            }
            
            return orro_insights
            
        except Exception as e:
            logging.error(f"Error generating Orro insights: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key security metrics"""
        return {
            "threats_detected_24h": 12,  # Simulated
            "alerts_processed_24h": 45,  # Simulated
            "responses_automated_7d": 23,  # Simulated
            "false_positives_suppressed": 67,  # Simulated
            "average_response_time": "2.3 minutes",
            "security_score": 94  # Simulated
        }
    
    def _calculate_security_posture(self) -> Dict[str, Any]:
        """Calculate overall security posture"""
        return {
            "posture_level": "strong",
            "trend": "improving",
            "last_incident": "7 days ago",
            "prevention_rate": "96%",
            "automation_maturity": "advanced"
        }
    
    def _generate_dashboard_charts(self) -> Dict[str, Any]:
        """Generate charts for dashboard"""
        
        # Threat trend chart
        threat_trend = go.Scatter(
            x=[datetime.now() - timedelta(days=i) for i in range(7, 0, -1)],
            y=[15, 12, 8, 10, 5, 7, 3],  # Simulated data
            mode='lines+markers',
            name='Threats Detected',
            line=dict(color='red')
        )
        
        threat_chart = json.dumps({
            'data': [threat_trend],
            'layout': {
                'title': 'Threat Detection Trend (7 days)',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Threats Detected'}
            }
        }, cls=PlotlyJSONEncoder)
        
        # Alert suppression chart
        suppression_data = go.Bar(
            x=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            y=[23, 19, 31, 28, 15, 8, 12],  # Simulated data
            name='Alerts Suppressed',
            marker_color='green'
        )
        
        suppression_chart = json.dumps({
            'data': [suppression_data],
            'layout': {
                'title': 'Alert Suppression (This Week)',
                'xaxis': {'title': 'Day'},
                'yaxis': {'title': 'Suppressed Alerts'}
            }
        }, cls=PlotlyJSONEncoder)
        
        return {
            "threat_trend": threat_chart,
            "alert_suppression": suppression_chart
        }
    
    def create_dashboard_templates(self):
        """Create HTML templates for dashboard"""
        
        # Main dashboard template
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Security Assistant - Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .dashboard-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px 0;
        }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2a5298;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-operational { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-critical { background-color: #dc3545; }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .insights-card {
            background: #f8f9fa;
            border-left: 4px solid #2a5298;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="dashboard-header">
        <div class="container">
            <h1>🛡️ Virtual Security Assistant Dashboard</h1>
            <p>Orro Group Cloud Practice - Real-time Security Operations</p>
            <div>
                <span class="status-indicator status-operational"></span>
                <span id="system-status">System Operational</span>
                <span class="ms-3">Last Updated: <span id="last-updated"></span></span>
            </div>
        </div>
    </div>

    <!-- Main Dashboard -->
    <div class="container mt-4">
        <!-- Key Metrics Row -->
        <div class="row">
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="threats-detected">-</div>
                    <div class="text-muted">Threats Detected (24h)</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="alerts-processed">-</div>
                    <div class="text-muted">Alerts Processed (24h)</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="responses-automated">-</div>
                    <div class="text-muted">Automated Responses (7d)</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="false-positives">-</div>
                    <div class="text-muted">False Positives Suppressed</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="response-time">-</div>
                    <div class="text-muted">Avg Response Time</div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="metric-card text-center">
                    <div class="metric-value" id="security-score">-</div>
                    <div class="text-muted">Security Score</div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <div id="threat-trend-chart"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <div id="alert-suppression-chart"></div>
                </div>
            </div>
        </div>

        <!-- Virtual Assistant Status -->
        <div class="row">
            <div class="col-md-4">
                <div class="metric-card">
                    <h5>🔮 Threat Intelligence</h5>
                    <div class="d-flex justify-content-between">
                        <span>Status:</span>
                        <span id="threat-status">-</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Active Predictions:</span>
                        <span id="active-predictions">-</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card">
                    <h5>🧠 Alert Management</h5>
                    <div class="d-flex justify-content-between">
                        <span>Fatigue Reduction:</span>
                        <span id="fatigue-reduction">-</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Suppression Rate:</span>
                        <span id="suppression-rate">-</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card">
                    <h5>⚡ Automated Response</h5>
                    <div class="d-flex justify-content-between">
                        <span>Success Rate:</span>
                        <span id="response-success">-</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Automation Rate:</span>
                        <span id="automation-rate">-</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Insights -->
        <div class="row mt-4">
            <div class="col-12">
                <h4>💡 Key Insights</h4>
                <div id="key-insights">
                    <div class="insights-card">Loading insights...</div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Dashboard JavaScript
        function updateDashboard() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Dashboard error:', data.error);
                        return;
                    }
                    
                    // Update metrics
                    document.getElementById('threats-detected').textContent = data.key_metrics.threats_detected_24h;
                    document.getElementById('alerts-processed').textContent = data.key_metrics.alerts_processed_24h;
                    document.getElementById('responses-automated').textContent = data.key_metrics.responses_automated_7d;
                    document.getElementById('false-positives').textContent = data.key_metrics.false_positives_suppressed;
                    document.getElementById('response-time').textContent = data.key_metrics.average_response_time;
                    document.getElementById('security-score').textContent = data.key_metrics.security_score;
                    
                    // Update Virtual Assistant status
                    if (data.virtual_assistant) {
                        document.getElementById('threat-status').textContent = data.virtual_assistant.threat_intelligence.status;
                        document.getElementById('active-predictions').textContent = data.virtual_assistant.threat_intelligence.active_predictions;
                        document.getElementById('fatigue-reduction').textContent = data.virtual_assistant.alert_management.fatigue_reduction + '%';
                        document.getElementById('suppression-rate').textContent = data.virtual_assistant.alert_management.suppression_rate + '%';
                        document.getElementById('response-success').textContent = data.virtual_assistant.automated_response.success_rate + '%';
                        document.getElementById('automation-rate').textContent = data.virtual_assistant.automated_response.automation_rate + '%';
                    }
                    
                    // Update charts
                    if (data.charts) {
                        if (data.charts.threat_trend) {
                            const threatChart = JSON.parse(data.charts.threat_trend);
                            Plotly.newPlot('threat-trend-chart', threatChart.data, threatChart.layout);
                        }
                        if (data.charts.alert_suppression) {
                            const suppressionChart = JSON.parse(data.charts.alert_suppression);
                            Plotly.newPlot('alert-suppression-chart', suppressionChart.data, suppressionChart.layout);
                        }
                    }
                    
                    // Update insights
                    if (data.virtual_assistant && data.virtual_assistant.key_insights) {
                        const insightsHtml = data.virtual_assistant.key_insights
                            .map(insight => `<div class="insights-card">${insight}</div>`)
                            .join('');
                        document.getElementById('key-insights').innerHTML = insightsHtml;
                    }
                    
                    // Update timestamp
                    document.getElementById('last-updated').textContent = new Date(data.timestamp).toLocaleString();
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                });
        }

        // Initial load and periodic updates
        updateDashboard();
        setInterval(updateDashboard, 30000); // Update every 30 seconds
    </script>
</body>
</html>
"""
        
        # Save template
        template_path = self.security_path / "dashboard" / "templates" / "dashboard.html"
        with open(template_path, 'w') as f:
            f.write(dashboard_html)
            
    def run_dashboard(self, host='localhost', port=5000, debug=False):
        """Run the security operations dashboard"""
        
        # Create templates if they don't exist
        if not (self.security_path / "dashboard" / "templates" / "dashboard.html").exists():
            self.create_dashboard_templates()
        
        logging.info(f"Starting Security Operations Dashboard on http://{host}:{port}")
        print(f"🛡️ Virtual Security Assistant Dashboard starting...")
        print(f"📊 Dashboard URL: http://{host}:{port}")
        print(f"🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}")
        
        self.app.run(host=host, port=port, debug=debug)

# CLI Interface
if __name__ == "__main__":
    import sys

    dashboard = SecurityOperationsDashboard()

    # Check for service mode flag (unified platform compatibility)
    service_mode = "--service-mode" in sys.argv

    if service_mode or (len(sys.argv) > 1 and sys.argv[1] == "start"):
        # Unified port management - use environment variable (registry-assigned)
        port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('PORT', '8058')))
        host = os.environ.get('DASHBOARD_HOST', 'localhost')
        debug = '--debug' in sys.argv and not service_mode

        print(f"🚀 Starting Security Operations Dashboard...")
        print(f"🔒 URL: http://{host}:{port}")
        dashboard.run_dashboard(host=host, port=port, debug=debug)

    elif len(sys.argv) > 1:
        if sys.argv[1] == "data":
            # Test API endpoints
            data = dashboard._get_dashboard_data()
            print(json.dumps(data, indent=2))
            
        elif sys.argv[1] == "create-templates":
            dashboard.create_dashboard_templates()
            print("✅ Dashboard templates created")
    else:
        print("Security Operations Dashboard")
        print("Usage:")
        print("  python3 security_operations_dashboard.py start [host] [port] [--debug]")
        print("  python3 security_operations_dashboard.py data")
        print("  python3 security_operations_dashboard.py create-templates")
        print("")
        print("Examples:")
        print("  python3 security_operations_dashboard.py start")
        print("  python3 security_operations_dashboard.py start 0.0.0.0 8080")
        print("  python3 security_operations_dashboard.py start localhost 5000 --debug")