#!/usr/bin/env python3
"""
Agent Performance Dashboard - Web Interface

Flask-based web dashboard for monitoring agent routing performance.
Integrates with unified dashboard hub on port 8066.

Usage:
    python3 agent_performance_dashboard_web.py
    Then open: http://127.0.0.1:8066
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, jsonify

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    from claude.tools.orchestration.performance_monitoring import (
        MetricsCollector, PerformanceAnalytics
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Import routing accuracy analyzer (Phase 122)
try:
    from claude.tools.orchestration.accuracy_analyzer import AccuracyAnalyzer
    ACCURACY_AVAILABLE = True
except ImportError:
    ACCURACY_AVAILABLE = False

app = Flask(__name__)

# Initialize monitoring
if MONITORING_AVAILABLE:
    collector = MetricsCollector()
    analytics = PerformanceAnalytics(collector)
else:
    collector = None
    analytics = None

# Initialize accuracy analyzer (Phase 122)
if ACCURACY_AVAILABLE:
    try:
        accuracy_analyzer = AccuracyAnalyzer()
    except FileNotFoundError:
        # Database doesn't exist yet
        accuracy_analyzer = None
        ACCURACY_AVAILABLE = False
else:
    accuracy_analyzer = None

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Performance Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }

        .container { max-width: 1400px; margin: 0 auto; }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .metric-label {
            color: #6b7280;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #1f2937;
        }

        .metric-value.success { color: #10b981; }
        .metric-value.warning { color: #f59e0b; }
        .metric-value.error { color: #ef4444; }

        .section {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .agent-list {
            display: grid;
            gap: 12px;
        }

        .agent-item {
            padding: 16px;
            background: #f9fafb;
            border-radius: 6px;
            border-left: 4px solid #e5e7eb;
        }

        .agent-item.excellent { border-left-color: #10b981; }
        .agent-item.good { border-left-color: #3b82f6; }
        .agent-item.warning { border-left-color: #f59e0b; }
        .agent-item.error { border-left-color: #ef4444; }

        .agent-name {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
        }

        .agent-stats {
            display: flex;
            gap: 24px;
            font-size: 13px;
            color: #6b7280;
        }

        .stat { display: flex; align-items: center; gap: 6px; }
        .stat-label { font-weight: 500; }

        .no-data {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }

        .no-data-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .refresh-info {
            text-align: center;
            color: #6b7280;
            font-size: 13px;
            margin-top: 20px;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }

        .status-indicator.success { background: #10b981; }
        .status-indicator.warning { background: #f59e0b; }
        .status-indicator.error { background: #ef4444; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading {
            animation: pulse 2s ease-in-out infinite;
        }
    </style>
    <script>
        function refreshData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => console.error('Error:', error));
        }

        function updateDashboard(data) {
            // Update metrics
            document.getElementById('total-executions').textContent = data.summary.total_executions || '0';
            document.getElementById('unique-agents').textContent = data.summary.unique_agents || '0';

            const successRate = data.summary.overall_success_rate || 0;
            const successEl = document.getElementById('success-rate');
            successEl.textContent = (successRate * 100).toFixed(1) + '%';
            successEl.className = 'metric-value ' + (successRate >= 0.95 ? 'success' : successRate >= 0.80 ? 'warning' : 'error');

            document.getElementById('avg-time').textContent = Math.round(data.summary.avg_execution_time_ms || 0) + 'ms';

            // Update agents list
            const agentsList = document.getElementById('agents-list');
            if (data.agents && data.agents.length > 0) {
                agentsList.innerHTML = data.agents.slice(0, 10).map(agent => {
                    const successRate = agent.success_rate;
                    const statusClass = successRate >= 0.95 ? 'excellent' : successRate >= 0.80 ? 'good' : successRate >= 0.60 ? 'warning' : 'error';
                    const statusIndicator = successRate >= 0.95 ? 'success' : successRate >= 0.80 ? 'success' : successRate >= 0.60 ? 'warning' : 'error';

                    return `
                        <div class="agent-item ${statusClass}">
                            <div class="agent-name">
                                <span class="status-indicator ${statusIndicator}"></span>
                                ${agent.agent_name}
                            </div>
                            <div class="agent-stats">
                                <div class="stat">
                                    <span class="stat-label">Executions:</span>
                                    <span>${agent.total_executions}</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-label">Success:</span>
                                    <span>${(agent.success_rate * 100).toFixed(1)}%</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-label">Avg Time:</span>
                                    <span>${Math.round(agent.avg_execution_time_ms)}ms</span>
                                </div>
                                <div class="stat">
                                    <span class="stat-label">Handoffs:</span>
                                    <span>${agent.total_handoffs || 0}</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                agentsList.innerHTML = `
                    <div class="no-data">
                        <div class="no-data-icon">📊</div>
                        <div>No agent execution data available yet</div>
                        <div style="margin-top: 12px; font-size: 12px;">
                            Data will appear once automatic agent routing is used
                        </div>
                    </div>
                `;
            }

            // Update bottlenecks
            const bottlenecksList = document.getElementById('bottlenecks-list');
            if (data.bottlenecks && data.bottlenecks.length > 0) {
                bottlenecksList.innerHTML = data.bottlenecks.map(b => `
                    <div class="agent-item warning">
                        <div class="agent-name">🐌 ${b.agent_name}</div>
                        <div class="agent-stats">
                            <div class="stat">
                                <span class="stat-label">Avg Time:</span>
                                <span>${Math.round(b.avg_execution_time_ms)}ms</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                bottlenecksList.innerHTML = `
                    <div class="no-data">
                        <div>✅ No bottlenecks detected - all agents performing well</div>
                    </div>
                `;
            }

            // Update accuracy metrics (Phase 122)
            if (data.accuracy) {
                const acceptanceRate = data.accuracy.overall.acceptance_rate || 0;
                const acceptanceEl = document.getElementById('acceptance-rate');
                acceptanceEl.textContent = (acceptanceRate * 100).toFixed(1) + '%';
                acceptanceEl.className = 'metric-value ' + (acceptanceRate >= 0.80 ? 'success' : acceptanceRate >= 0.60 ? 'warning' : 'error');

                document.getElementById('total-suggestions').textContent = data.accuracy.overall.total_suggestions || '0';

                const confidence = data.accuracy.overall.avg_confidence || 0;
                document.getElementById('avg-confidence').textContent = (confidence * 100).toFixed(1) + '%';

                const lowPatterns = (data.accuracy.low_patterns || []).length;
                const lowPatternsEl = document.getElementById('low-patterns');
                lowPatternsEl.textContent = lowPatterns;
                lowPatternsEl.className = 'metric-value ' + (lowPatterns === 0 ? 'success' : lowPatterns <= 2 ? 'warning' : 'error');

                // Update accuracy by category
                const categoryDiv = document.getElementById('accuracy-by-category');
                if (data.accuracy.by_category && data.accuracy.by_category.length > 0) {
                    categoryDiv.innerHTML = data.accuracy.by_category.map(cat => {
                        const rate = cat.acceptance_rate;
                        const statusClass = rate >= 0.80 ? 'excellent' : rate >= 0.60 ? 'good' : 'warning';
                        const statusIndicator = rate >= 0.80 ? 'success' : rate >= 0.60 ? 'warning' : 'error';

                        return `
                            <div class="agent-item ${statusClass}">
                                <div class="agent-name">
                                    <span class="status-indicator ${statusIndicator}"></span>
                                    ${cat.value}
                                </div>
                                <div class="agent-stats">
                                    <div class="stat">
                                        <span class="stat-label">Acceptance:</span>
                                        <span>${(cat.acceptance_rate * 100).toFixed(1)}%</span>
                                    </div>
                                    <div class="stat">
                                        <span class="stat-label">Samples:</span>
                                        <span>${cat.sample_size}</span>
                                    </div>
                                    <div class="stat">
                                        <span class="stat-label">Confidence:</span>
                                        <span>${(cat.avg_confidence * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    categoryDiv.innerHTML = `
                        <div class="no-data">
                            <div>📊 No routing accuracy data available yet</div>
                            <div style="margin-top: 12px; font-size: 12px;">
                                Data will appear once routing suggestions are tracked (Phase 122)
                            </div>
                        </div>
                    `;
                }
            }

            // Update timestamp
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }

        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);

        // Initial load
        window.addEventListener('load', refreshData);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Agent Performance Dashboard</h1>
            <p>Real-time monitoring of Phase 121 automatic agent routing</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Executions</div>
                <div class="metric-value loading" id="total-executions">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Unique Agents</div>
                <div class="metric-value loading" id="unique-agents">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value loading" id="success-rate">0%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Execution Time</div>
                <div class="metric-value loading" id="avg-time">0ms</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">🤖 Agent Performance</div>
            <div class="agent-list" id="agents-list">
                <div class="no-data loading">Loading agent data...</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">⚠️ Performance Bottlenecks (&gt;2000ms)</div>
            <div class="agent-list" id="bottlenecks-list">
                <div class="no-data loading">Loading bottleneck data...</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">🎯 Routing Accuracy (Phase 122)</div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Acceptance Rate (7 days)</div>
                    <div class="metric-value loading" id="acceptance-rate">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Suggestions</div>
                    <div class="metric-value loading" id="total-suggestions">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Confidence</div>
                    <div class="metric-value loading" id="avg-confidence">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Low Accuracy Patterns</div>
                    <div class="metric-value loading" id="low-patterns">0</div>
                </div>
            </div>

            <div id="accuracy-by-category" style="margin-top: 16px;">
                <div class="no-data loading">Loading accuracy data...</div>
            </div>
        </div>

        <div class="refresh-info">
            🔄 Auto-refreshing every 5 seconds | Last update: <span id="last-update">--:--:--</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for metrics data"""
    # Base response structure
    response = {
        'summary': {
            'total_executions': 0,
            'unique_agents': 0,
            'overall_success_rate': 0,
            'avg_execution_time_ms': 0
        },
        'agents': [],
        'bottlenecks': [],
        'failures': {},
        'routing_strategies': {},
        'timestamp': datetime.now().isoformat()
    }

    # Add performance data
    if MONITORING_AVAILABLE and analytics:
        summary = analytics.get_performance_summary()
        agent_stats = analytics.get_all_agent_statistics()
        bottlenecks = analytics.identify_bottlenecks(threshold_ms=2000)

        # Sort agents by executions
        agent_stats.sort(key=lambda x: x['total_executions'], reverse=True)

        response['summary'] = summary
        response['agents'] = agent_stats
        response['bottlenecks'] = bottlenecks

    # Add accuracy data (Phase 122)
    if ACCURACY_AVAILABLE and accuracy_analyzer:
        try:
            overall_accuracy = accuracy_analyzer.get_overall_accuracy(days=7)
            by_category = accuracy_analyzer.get_accuracy_by_category(days=7)
            low_patterns = accuracy_analyzer.identify_low_accuracy_patterns(threshold=0.60, min_sample_size=3)

            response['accuracy'] = {
                'overall': overall_accuracy,
                'by_category': [
                    {
                        'value': metric.value,
                        'acceptance_rate': metric.acceptance_rate,
                        'sample_size': metric.sample_size,
                        'avg_confidence': metric.avg_confidence
                    }
                    for metric in by_category
                ],
                'low_patterns': [
                    {
                        'pattern_type': pattern.pattern_type,
                        'pattern_value': pattern.pattern_value,
                        'acceptance_rate': pattern.acceptance_rate,
                        'severity': pattern.severity
                    }
                    for pattern in low_patterns
                ]
            }
        except Exception as e:
            # Accuracy data not available yet
            response['accuracy'] = None
    else:
        response['accuracy'] = None

    return jsonify(response)

def main():
    """Start the web dashboard"""
    port = 8066
    print(f"🎯 Starting Agent Performance Dashboard")
    print(f"🌐 Access at: http://127.0.0.1:{port}")
    print(f"🔄 Auto-refreshes every 5 seconds")
    print("")

    if not MONITORING_AVAILABLE:
        print("⚠️  Warning: Performance monitoring not available")
        print("   Dashboard will show placeholder data")
        print("")

    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == '__main__':
    main()
