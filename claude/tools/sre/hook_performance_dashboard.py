#!/usr/bin/env python3
"""
Hook Performance Dashboard - Phase 127 Monitoring

Real-time web dashboard for monitoring hook performance metrics:
- P50/P95/P99 latency tracking
- Output pollution monitoring
- Performance trends over time
- SLO compliance indicators
- Alert configuration

Port: 8067
Usage: python3 claude/tools/sre/hook_performance_dashboard.py

Author: Maia (Phase 127 - Monitoring & Alerting)
Created: 2025-10-17
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template_string, jsonify, request

# Add maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Dashboard configuration
DASHBOARD_PORT = 8067
DB_PATH = MAIA_ROOT / "claude" / "data" / "databases" / "system" / "performance_metrics.db"

# SLO thresholds
SLO_THRESHOLDS = {
    'slash_command': {
        'p95_latency_ms': 10,
        'status': 'excellent'
    },
    'normal': {
        'p95_latency_ms': 100,
        'status': 'good'
    },
    'build': {
        'p95_latency_ms': 1000,
        'status': 'acceptable'
    }
}


class HookPerformanceMetrics:
    """Access hook performance metrics from database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_latest_baseline(self) -> Optional[Dict]:
        """Get latest baseline performance data."""
        if not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT message_type, p50_latency_ms, p95_latency_ms, p99_latency_ms,
                       avg_output_lines, timestamp
                FROM performance_baselines
                ORDER BY timestamp DESC
                LIMIT 3
            """)

            results = {}
            for row in cursor.fetchall():
                msg_type, p50, p95, p99, output, timestamp = row
                results[msg_type] = {
                    'p50': p50,
                    'p95': p95,
                    'p99': p99,
                    'avg_output': output,
                    'timestamp': timestamp,
                    'slo_threshold': SLO_THRESHOLDS.get(msg_type, {}).get('p95_latency_ms'),
                    'slo_status': self._get_slo_status(msg_type, p95)
                }

            conn.close()
            return results if results else None

        except Exception as e:
            print(f"Error reading baseline: {e}")
            return None

    def get_performance_samples(self, limit: int = 100) -> List[Dict]:
        """Get recent performance samples."""
        if not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, message_type, latency_ms, output_lines
                FROM performance_samples
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            samples = []
            for row in cursor.fetchall():
                timestamp, msg_type, latency, output = row
                samples.append({
                    'timestamp': timestamp,
                    'message_type': msg_type,
                    'latency_ms': latency,
                    'output_lines': output
                })

            conn.close()
            return samples

        except Exception as e:
            print(f"Error reading samples: {e}")
            return []

    def get_performance_trends(self, hours: int = 24) -> Dict:
        """Get performance trends over time."""
        if not self.db_path.exists():
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT message_type,
                       AVG(latency_ms) as avg_latency,
                       MAX(latency_ms) as max_latency,
                       COUNT(*) as sample_count
                FROM performance_samples
                WHERE timestamp > ?
                GROUP BY message_type
            """, (cutoff.isoformat(),))

            trends = {}
            for row in cursor.fetchall():
                msg_type, avg_lat, max_lat, count = row
                trends[msg_type] = {
                    'avg_latency_ms': round(avg_lat, 1),
                    'max_latency_ms': max_lat,
                    'sample_count': count
                }

            conn.close()
            return trends

        except Exception as e:
            print(f"Error reading trends: {e}")
            return {}

    def _get_slo_status(self, message_type: str, p95_latency: float) -> str:
        """Determine SLO compliance status."""
        threshold = SLO_THRESHOLDS.get(message_type, {}).get('p95_latency_ms')
        if not threshold:
            return 'unknown'

        if p95_latency <= threshold:
            return 'pass'
        elif p95_latency <= threshold * 1.5:
            return 'warning'
        else:
            return 'fail'

    def get_slo_compliance_summary(self) -> Dict:
        """Get overall SLO compliance summary."""
        baseline = self.get_latest_baseline()
        if not baseline:
            return {}

        summary = {
            'total_types': len(baseline),
            'passing': 0,
            'warning': 0,
            'failing': 0
        }

        for msg_type, data in baseline.items():
            status = data['slo_status']
            if status == 'pass':
                summary['passing'] += 1
            elif status == 'warning':
                summary['warning'] += 1
            elif status == 'fail':
                summary['failing'] += 1

        summary['compliance_rate'] = summary['passing'] / summary['total_types'] if summary['total_types'] > 0 else 0

        return summary


# HTML Template for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Hook Performance Dashboard - Phase 127</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
        }
        .header h1 { font-size: 32px; margin-bottom: 8px; color: white; }
        .header .subtitle { opacity: 0.9; font-size: 14px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }
        .stat-card h3 {
            font-size: 14px;
            color: #8b949e;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .stat-label { font-size: 13px; color: #8b949e; }
        .status-pass { color: #3fb950; }
        .status-warning { color: #d29922; }
        .status-fail { color: #f85149; }
        .status-unknown { color: #8b949e; }
        .metric-table {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .metric-table h2 {
            padding: 20px;
            border-bottom: 1px solid #30363d;
            font-size: 18px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 20px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }
        th {
            background: #0d1117;
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        td { font-size: 14px; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-excellent { background: #1a7f37; color: white; }
        .badge-good { background: #1f6feb; color: white; }
        .badge-acceptable { background: #d29922; color: #0d1117; }
        .badge-pass { background: #238636; color: white; }
        .badge-warning { background: #9e6a03; color: white; }
        .badge-fail { background: #da3633; color: white; }
        .footer {
            text-align: center;
            padding: 20px;
            color: #8b949e;
            font-size: 13px;
        }
        .refresh-note {
            background: #1c2128;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 13px;
            border-left: 3px solid #1f6feb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Hook Performance Dashboard</h1>
            <div class="subtitle">Phase 127: Architecture Review & Performance Optimization | Real-time Monitoring</div>
        </div>

        <div class="refresh-note">
            ⏱️ Auto-refresh: Every 30 seconds | Last updated: {{ now }} | <a href="/api/metrics" style="color: #58a6ff;">JSON API</a>
        </div>

        {% if not baseline %}
        <div class="metric-table">
            <h2>📊 No Performance Data Available</h2>
            <div style="padding: 40px 20px; text-align: center; color: #8b949e;">
                <p style="margin-bottom: 12px;">Performance metrics will appear once baseline is established.</p>
                <p>Run: <code style="background: #0d1117; padding: 4px 8px; border-radius: 4px;">python3 claude/tools/sre/hook_performance_profiler.py baseline</code></p>
            </div>
        </div>
        {% else %}

        <div class="stats-grid">
            <div class="stat-card">
                <h3>SLO Compliance</h3>
                <div class="stat-value status-{{ 'pass' if slo_summary.compliance_rate >= 0.8 else 'warning' }}">
                    {{ (slo_summary.compliance_rate * 100)|round|int }}%
                </div>
                <div class="stat-label">
                    {{ slo_summary.passing }}/{{ slo_summary.total_types }} types passing
                </div>
            </div>

            {% for msg_type, data in baseline.items() %}
            <div class="stat-card">
                <h3>{{ msg_type.replace('_', ' ').title() }}</h3>
                <div class="stat-value status-{{ data.slo_status }}">{{ data.p95|int }}ms</div>
                <div class="stat-label">
                    P95 Latency (SLO: {{ data.slo_threshold }}ms)
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="metric-table">
            <h2>📈 Current Performance Baseline</h2>
            <table>
                <thead>
                    <tr>
                        <th>Message Type</th>
                        <th>P50 Latency</th>
                        <th>P95 Latency</th>
                        <th>P99 Latency</th>
                        <th>Avg Output</th>
                        <th>SLO Status</th>
                        <th>Recorded</th>
                    </tr>
                </thead>
                <tbody>
                    {% for msg_type, data in baseline.items() %}
                    <tr>
                        <td><strong>{{ msg_type.replace('_', ' ').title() }}</strong></td>
                        <td>{{ data.p50|int }}ms</td>
                        <td class="status-{{ data.slo_status }}"><strong>{{ data.p95|int }}ms</strong></td>
                        <td>{{ data.p99|int }}ms</td>
                        <td>{{ data.avg_output }} lines</td>
                        <td>
                            <span class="badge badge-{{ data.slo_status }}">{{ data.slo_status }}</span>
                        </td>
                        <td style="color: #8b949e; font-size: 12px;">{{ data.timestamp[:19] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% if trends %}
        <div class="metric-table">
            <h2>📊 Performance Trends (Last 24 Hours)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Message Type</th>
                        <th>Avg Latency</th>
                        <th>Max Latency</th>
                        <th>Sample Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for msg_type, data in trends.items() %}
                    <tr>
                        <td><strong>{{ msg_type.replace('_', ' ').title() }}</strong></td>
                        <td>{{ data.avg_latency_ms }}ms</td>
                        <td>{{ data.max_latency_ms|int }}ms</td>
                        <td>{{ data.sample_count }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <div class="metric-table">
            <h2>🎯 SLO Thresholds</h2>
            <table>
                <thead>
                    <tr>
                        <th>Message Type</th>
                        <th>P95 Threshold</th>
                        <th>Classification</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Slash Commands</strong></td>
                        <td>10ms</td>
                        <td><span class="badge badge-excellent">Excellent</span></td>
                        <td>System commands bypass all validation</td>
                    </tr>
                    <tr>
                        <td><strong>Normal Messages</strong></td>
                        <td>100ms</td>
                        <td><span class="badge badge-good">Good</span></td>
                        <td>Standard user prompts with validation</td>
                    </tr>
                    <tr>
                        <td><strong>Build Requests</strong></td>
                        <td>1000ms</td>
                        <td><span class="badge badge-acceptable">Acceptable</span></td>
                        <td>Includes capability check (Phase 0)</td>
                    </tr>
                </tbody>
            </table>
        </div>

        {% endif %}

        <div class="footer">
            Phase 127: Architecture Review & Performance Optimization<br>
            SRE Principal Engineer Agent | Maia System | 2025-10-17
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Render main dashboard."""
    metrics = HookPerformanceMetrics(DB_PATH)

    baseline = metrics.get_latest_baseline()
    trends = metrics.get_performance_trends(hours=24)
    slo_summary = metrics.get_slo_compliance_summary()

    return render_template_string(
        DASHBOARD_HTML,
        baseline=baseline,
        trends=trends,
        slo_summary=slo_summary,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


@app.route('/api/metrics')
def api_metrics():
    """JSON API endpoint for metrics."""
    metrics = HookPerformanceMetrics(DB_PATH)

    return jsonify({
        'baseline': metrics.get_latest_baseline(),
        'trends': metrics.get_performance_trends(hours=24),
        'slo_summary': metrics.get_slo_compliance_summary(),
        'recent_samples': metrics.get_performance_samples(limit=20),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'dashboard': 'hook_performance',
        'port': DASHBOARD_PORT,
        'db_exists': DB_PATH.exists(),
        'timestamp': datetime.now().isoformat()
    })


def main():
    """Start dashboard server."""
    import argparse

    parser = argparse.ArgumentParser(description='Hook Performance Dashboard')
    parser.add_argument('--port', type=int, default=DASHBOARD_PORT, help=f'Port (default: {DASHBOARD_PORT})')
    parser.add_argument('--host', default='127.0.0.1', help='Host (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()

    print(f"""
╭────────────────────────────────────────────────────────────────╮
│  🎯 Hook Performance Dashboard - Phase 127                    │
│  Starting on http://{args.host}:{args.port}                           │
│  Database: {str(DB_PATH.relative_to(MAIA_ROOT)):<40}│
╰────────────────────────────────────────────────────────────────╯
    """)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
