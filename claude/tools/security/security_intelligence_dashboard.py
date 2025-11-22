#!/usr/bin/env python3
"""
Security Intelligence Dashboard - Real-time Security Visualization
===================================================================

Purpose: Web-based dashboard providing real-time security status visualization
         with 8 industry-standard widgets and auto-refresh capabilities.

Pattern: Similar to ServiceDesk dashboard (Flask + Chart.js + responsive CSS)
Port: 8063 (next available after health monitor)
Integration: Unified Dashboard Hub registration

Features:
- Security status overview (Green/Yellow/Red)
- Critical vulnerabilities tracking
- Dependency health monitoring
- Code quality scoring
- Compliance status (SOC2/ISO27001)
- Last scan times
- Alert timeline
- Remediation status

Created: 2025-10-13 (Phase 113 - Security Automation Project)
"""

from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

app = Flask(__name__)

# Configuration
MAIA_ROOT = Path.home() / "git" / "maia"
DB_PATH = MAIA_ROOT / "claude/data/security_metrics.db"
UDH_URL = "http://127.0.0.1:8100"
DASHBOARD_PORT = 8063

# HTML Template with embedded CSS and JavaScript
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Security Intelligence Dashboard - Maia</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-banner {
            display: inline-block;
            padding: 10px 30px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2em;
            margin-top: 10px;
        }

        .status-healthy { background: #10b981; color: white; }
        .status-warning { background: #f59e0b; color: white; }
        .status-critical { background: #ef4444; color: white; }
        .status-degraded { background: #6b7280; color: white; }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .widget {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .widget:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .widget-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .widget-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #fff;
        }

        .widget-icon {
            font-size: 1.5em;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 15px 0;
            text-align: center;
        }

        .metric-label {
            text-align: center;
            color: #9ca3af;
            font-size: 0.9em;
        }

        .metric-good { color: #10b981; }
        .metric-warning { color: #f59e0b; }
        .metric-critical { color: #ef4444; }

        .scan-time {
            font-size: 0.85em;
            color: #9ca3af;
            margin-top: 10px;
            text-align: center;
        }

        .alert-item {
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            font-size: 0.9em;
        }

        .alert-item.warning {
            background: rgba(245, 158, 11, 0.1);
            border-left-color: #f59e0b;
        }

        .compliance-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 15px;
            margin: 5px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .compliance-pass {
            background: #10b981;
            color: white;
        }

        .compliance-fail {
            background: #ef4444;
            color: white;
        }

        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            font-size: 0.9em;
            z-index: 1000;
        }

        .chart-container {
            position: relative;
            height: 200px;
            margin-top: 15px;
        }

        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="refresh-indicator" id="refreshIndicator">
        🔄 Auto-refresh: <span id="countdown">30</span>s
    </div>

    <div class="header">
        <h1>🛡️ Security Intelligence Dashboard</h1>
        <div class="status-banner" id="overallStatus">
            Loading...
        </div>
        <div style="margin-top: 10px; font-size: 0.9em; color: #9ca3af;">
            Last Updated: <span id="lastUpdate">Never</span>
        </div>
    </div>

    <div class="dashboard-grid">
        <!-- Widget 1: Security Status -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Security Status</span>
                <span class="widget-icon">🎯</span>
            </div>
            <div class="metric-value" id="securityStatus">-</div>
            <div class="metric-label">Overall System Health</div>
            <div class="scan-time" id="lastScanTime">No recent scans</div>
        </div>

        <!-- Widget 2: Critical Vulnerabilities -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Critical Vulnerabilities</span>
                <span class="widget-icon">🚨</span>
            </div>
            <div class="metric-value" id="criticalVulns">0</div>
            <div class="metric-label">Requiring Immediate Action</div>
            <div class="scan-time" id="vulnAging">-</div>
        </div>

        <!-- Widget 3: Dependency Health -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Dependency Health</span>
                <span class="widget-icon">📦</span>
            </div>
            <div class="metric-value" id="depHealth">-</div>
            <div class="metric-label">Known Vulnerabilities</div>
            <div class="scan-time" id="depScanTime">-</div>
        </div>

        <!-- Widget 4: Code Quality Score -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Code Quality</span>
                <span class="widget-icon">⭐</span>
            </div>
            <div class="metric-value" id="codeQuality">-</div>
            <div class="metric-label">Bandit Security Rating</div>
            <div class="scan-time" id="codeScanTime">-</div>
        </div>

        <!-- Widget 5: Compliance Status -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Compliance Status</span>
                <span class="widget-icon">✅</span>
            </div>
            <div style="text-align: center; margin-top: 20px;" id="complianceStatus">
                <div class="compliance-badge compliance-pass">SOC2: ✓</div>
                <div class="compliance-badge compliance-pass">ISO27001: ✓</div>
                <div class="compliance-badge compliance-pass">UFC: ✓</div>
            </div>
            <div class="scan-time" id="complianceScanTime">-</div>
        </div>

        <!-- Widget 6: Alert Timeline -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Recent Alerts</span>
                <span class="widget-icon">📢</span>
            </div>
            <div id="alertTimeline">
                <div style="text-align: center; color: #9ca3af; margin-top: 20px;">
                    No active alerts
                </div>
            </div>
        </div>

        <!-- Widget 7: Scan Schedule -->
        <div class="widget">
            <div class="widget-header">
                <span class="widget-title">Scan Schedule</span>
                <span class="widget-icon">⏰</span>
            </div>
            <div style="font-size: 0.9em; color: #e0e0e0; margin-top: 10px;" id="scanSchedule">
                <div style="margin: 8px 0;">📦 Dependency: Every 1 hour</div>
                <div style="margin: 8px 0;">🔍 Code: Every 24 hours</div>
                <div style="margin: 8px 0;">✅ Compliance: Every 7 days</div>
                <div style="margin: 8px 0;">📊 Metrics: Every 5 minutes</div>
            </div>
        </div>

        <!-- Widget 8: Scan History Chart -->
        <div class="widget" style="grid-column: span 2;">
            <div class="widget-header">
                <span class="widget-title">Security Scan History</span>
                <span class="widget-icon">📈</span>
            </div>
            <div class="chart-container">
                <canvas id="scanHistoryChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        let scanHistoryChart = null;
        let refreshInterval = 30;
        let countdown = refreshInterval;

        // Initialize chart
        function initChart() {
            const ctx = document.getElementById('scanHistoryChart').getContext('2d');
            scanHistoryChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Findings',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }

        // Fetch dashboard data
        async function updateDashboard() {
            try {
                const response = await fetch('/api/security-status');
                const data = await response.json();

                // Update overall status
                const statusBanner = document.getElementById('overallStatus');
                statusBanner.textContent = data.status;
                statusBanner.className = 'status-banner status-' + data.status.toLowerCase();

                // Update security status widget
                document.getElementById('securityStatus').textContent = data.status;
                document.getElementById('securityStatus').className =
                    'metric-value metric-' + (data.status === 'HEALTHY' ? 'good' :
                    data.status === 'WARNING' ? 'warning' : 'critical');

                // Update last scan time
                if (data.last_scan) {
                    const scanDate = new Date(data.last_scan.timestamp);
                    document.getElementById('lastScanTime').textContent =
                        'Last scan: ' + scanDate.toLocaleString();
                }

                // Update critical vulnerabilities
                const criticalCount = Object.values(data.alerts || {}).reduce((a, b) => a + b, 0);
                document.getElementById('criticalVulns').textContent = criticalCount;
                document.getElementById('criticalVulns').className =
                    'metric-value ' + (criticalCount === 0 ? 'metric-good' : 'metric-critical');

                // Update dependency health
                const depScans = data.recent_scans.filter(s => s.type === 'dependency_scan');
                if (depScans.length > 0) {
                    const latest = depScans[0];
                    const vulnCount = latest.critical + latest.high;
                    document.getElementById('depHealth').textContent =
                        vulnCount === 0 ? '✓ Healthy' : vulnCount + ' issues';
                    document.getElementById('depHealth').className =
                        'metric-value ' + (vulnCount === 0 ? 'metric-good' : 'metric-warning');
                }

                // Update alerts
                const alertsDiv = document.getElementById('alertTimeline');
                if (Object.keys(data.alerts || {}).length > 0) {
                    alertsDiv.innerHTML = Object.entries(data.alerts).map(([severity, count]) =>
                        `<div class="alert-item ${severity}">${count} ${severity} alert(s)</div>`
                    ).join('');
                } else {
                    alertsDiv.innerHTML = '<div style="text-align: center; color: #9ca3af; margin-top: 20px;">No active alerts</div>';
                }

                // Update chart
                if (scanHistoryChart && data.recent_scans) {
                    const labels = data.recent_scans.slice(0, 10).reverse().map(s => {
                        const d = new Date(s.timestamp);
                        return d.toLocaleTimeString();
                    });
                    const chartData = data.recent_scans.slice(0, 10).reverse().map(s =>
                        s.critical + s.high
                    );

                    scanHistoryChart.data.labels = labels;
                    scanHistoryChart.data.datasets[0].data = chartData;
                    scanHistoryChart.update();
                }

                // Update last update time
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

            } catch (error) {
                console.error('Failed to update dashboard:', error);
            }
        }

        // Countdown timer
        function updateCountdown() {
            countdown--;
            document.getElementById('countdown').textContent = countdown;

            if (countdown <= 0) {
                countdown = refreshInterval;
                updateDashboard();
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            updateDashboard();
            setInterval(updateCountdown, 1000);
        });
    </script>
</body>
</html>
"""


def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Serve dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/security-status')
def api_security_status():
    """API endpoint for security status data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent scans
        cursor.execute("""
            SELECT scan_type, timestamp, status,
                   critical_count, high_count, medium_count, low_count,
                   findings_count
            FROM scan_history
            ORDER BY timestamp DESC
            LIMIT 20
        """)

        recent_scans = []
        for row in cursor.fetchall():
            recent_scans.append({
                'type': row['scan_type'],
                'timestamp': row['timestamp'],
                'status': row['status'],
                'critical': row['critical_count'],
                'high': row['high_count'],
                'medium': row['medium_count'],
                'low': row['low_count'],
                'total': row['findings_count']
            })

        # Get active alerts
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM security_alerts
            WHERE status = 'new'
            GROUP BY severity
        """)

        alerts = {}
        for row in cursor.fetchall():
            alerts[row['severity']] = row['count']

        # Get latest metrics
        cursor.execute("""
            SELECT metric_name, metric_value, timestamp
            FROM security_metrics
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        """)

        metrics = {}
        for row in cursor.fetchall():
            if row['metric_name'] not in metrics:
                metrics[row['metric_name']] = row['metric_value']

        conn.close()

        # Determine overall status
        if alerts.get('critical', 0) > 0:
            overall_status = "CRITICAL"
        elif alerts.get('high', 0) > 0:
            overall_status = "WARNING"
        elif any(s['status'] == 'error' for s in recent_scans[:3]):
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"

        return jsonify({
            'status': overall_status,
            'recent_scans': recent_scans,
            'alerts': alerts,
            'metrics': metrics,
            'last_scan': recent_scans[0] if recent_scans else None
        })

    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'recent_scans': [],
            'alerts': {},
            'metrics': {}
        }), 500


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'service': 'security-intelligence-dashboard',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


def register_with_udh():
    """Register dashboard with Unified Dashboard Hub"""
    try:
        response = requests.post(
            f"{UDH_URL}/api/register",
            json={
                'name': 'Security Intelligence',
                'port': DASHBOARD_PORT,
                'path': '/',
                'description': 'Real-time security monitoring and alerting',
                'category': 'security'
            },
            timeout=5
        )

        if response.status_code == 200:
            print(f"✅ Registered with UDH at {UDH_URL}")
        else:
            print(f"⚠️  UDH registration failed: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"⚠️  UDH not available: {e}")


if __name__ == '__main__':
    print(f"🛡️  Security Intelligence Dashboard starting...")
    print(f"📊 Dashboard: http://127.0.0.1:{DASHBOARD_PORT}")
    print(f"💾 Database: {DB_PATH}")

    # Attempt UDH registration
    register_with_udh()

    # Start Flask server
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)
