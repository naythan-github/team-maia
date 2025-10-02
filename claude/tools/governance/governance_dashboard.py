#!/usr/bin/env python3
"""
Governance Dashboard - Phase 4 Component
Web interface for repository governance monitoring
"""

import os
import json
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import sys
from pathlib import Path
from claude.tools.core.path_manager import get_maia_root

# Add governance tools to path (dynamic path resolution)
MAIA_ROOT = Path(__file__).resolve().parents[3]  # Up to /maia root
sys.path.append(str(MAIA_ROOT / "claude" / "tools" / "governance"))

try:
    from claude.tools.governance.repository_analyzer import RepositoryAnalyzer
    from claude.tools.governance.filesystem_monitor import FileSystemMonitor
    from claude.tools.governance.enhanced_policy_engine import EnhancedPolicyEngine
    ENHANCED_POLICY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("Make sure governance components are properly installed")
    ENHANCED_POLICY_AVAILABLE = False

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('governance_dashboard.html')

@app.route('/health')
def health_check():
    """Standardized health check endpoint"""
    try:
        # Basic health check without complex dependencies
        return jsonify({
            "status": "healthy",
            "uptime": 0,
            "version": "1.0.0",
            "service": "governance_dashboard",
            "components_available": ENHANCED_POLICY_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "uptime": 0,
            "version": "1.0.0",
            "service": "governance_dashboard",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/health')
def health_status():
    """API endpoint for health status"""
    try:
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze_structure()
        
        return jsonify({
            "status": "healthy" if analysis["health_score"] > 7.0 else "degraded",
            "health_score": analysis["health_score"],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "health_score": 0.0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/violations')
def get_violations():
    """API endpoint for violation data"""
    try:
        monitor = FileSystemMonitor()
        violations = monitor.get_violations_summary()
        
        return jsonify(violations)
    except Exception as e:
        return jsonify({
            "total_violations": 0,
            "high_severity_count": 0,
            "recent_violations": [],
            "error": str(e)
        }), 500

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for governance metrics"""
    try:
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze_structure()
        
        return jsonify({
            "file_counts": analysis["file_counts"],
            "sprawl_indicators": analysis["sprawl_indicators"],
            "tool_analysis": analysis["tool_analysis"],
            "ufc_compliance": analysis["ufc_compliance"]
        })
    except Exception as e:
        return jsonify({
            "file_counts": {},
            "sprawl_indicators": [],
            "tool_analysis": {},
            "ufc_compliance": {},
            "error": str(e)
        }), 500

@app.route('/api/remediation')
def get_remediation_status():
    """API endpoint for remediation status"""
    try:
        # Check if remediation engine is available
        from claude.tools.governance.remediation_engine import RemediationEngine
        engine = RemediationEngine()
        
        # Check for backups (indicates recent activity)
        backup_dir = engine.backup_dir
        backups = []
        if backup_dir.exists():
            backups = [f.name for f in backup_dir.iterdir() if f.is_file()]
        
        return jsonify({
            "remediation_available": True,
            "recent_backups": len(backups),
            "backup_files": backups[-5:] if backups else [],  # Last 5 backups
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "remediation_available": False,
            "recent_backups": 0,
            "backup_files": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/enhanced_policy')
def get_enhanced_policy_status():
    """API endpoint for enhanced policy engine status"""
    try:
        if not ENHANCED_POLICY_AVAILABLE:
            return jsonify({
                "enhanced_policy_available": False,
                "error": "Enhanced Policy Engine not available"
            }), 500
        
        engine = EnhancedPolicyEngine()
        health = engine.integration_health_check()
        recommendations = engine.generate_adaptive_policies()
        
        return jsonify({
            "enhanced_policy_available": True,
            "ml_available": health["ml_available"],
            "models_trained": health["models_trained"],
            "violation_history_size": health["violation_history_size"],
            "recommendations_count": len(recommendations),
            "recommendations": [
                {
                    "type": rec.policy_type,
                    "recommendation": rec.recommendation,
                    "confidence": rec.confidence,
                    "impact": rec.impact_estimate
                } for rec in recommendations[:3]  # Top 3 recommendations
            ],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "enhanced_policy_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/system_status')
def get_system_status():
    """API endpoint for overall system status"""
    try:
        # Check all components
        components = {
            "repository_analyzer": False,
            "filesystem_monitor": False,
            "remediation_engine": False,
            "enhanced_policy_engine": False,
            "ufc_system": False
        }
        
        # Test repository analyzer
        try:
            analyzer = RepositoryAnalyzer()
            analyzer.analyze_structure()
            components["repository_analyzer"] = True
        except Exception:
            pass
        
        # Test filesystem monitor
        try:
            monitor = FileSystemMonitor()
            monitor.get_violations_summary()
            components["filesystem_monitor"] = True
        except Exception:
            pass
        
        # Test remediation engine
        try:
            from claude.tools.governance.remediation_engine import RemediationEngine
            engine = RemediationEngine()
            components["remediation_engine"] = True
        except Exception:
            pass
        
        # Test enhanced policy engine
        try:
            if ENHANCED_POLICY_AVAILABLE:
                policy_engine = EnhancedPolicyEngine()
                health = policy_engine.integration_health_check()
                components["enhanced_policy_engine"] = health["ml_available"] and health["governance_components"]
        except Exception:
            pass
        
        # Test UFC system
        try:
            ufc_file = "${MAIA_ROOT}/claude/context/ufc_system.md"
            if os.path.exists(ufc_file):
                components["ufc_system"] = True
        except Exception:
            pass
        
        working_components = sum(1 for v in components.values() if v)
        total_components = len(components)
        
        return jsonify({
            "components": components,
            "working_components": working_components,
            "total_components": total_components,
            "system_health": f"{working_components}/{total_components}",
            "operational": working_components >= 3,  # At least 3/4 components working
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "components": {},
            "working_components": 0,
            "total_components": 4,
            "system_health": "0/4",
            "operational": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    import sys

    # Check for service mode flag
    service_mode = "--service-mode" in sys.argv

    # Unified port management - use environment variable (registry-assigned)
    port = int(os.environ.get('DASHBOARD_PORT', os.environ.get('PORT', '8072')))
    host = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
    debug = not service_mode and os.environ.get('DEBUG', 'false').lower() == 'true'

    if not service_mode:
        print("🚀 Starting Maia Repository Governance Dashboard...")
        print(f"📊 Dashboard will be available at: http://{host}:{port}")
        print("🔗 API endpoints:")
        print("   /api/health - Repository health status")
        print("   /api/violations - Current violations")
        print("   /api/metrics - Governance metrics")
        print("   /api/remediation - Remediation status")
        print("   /api/system_status - Overall system status")
        print("\n✅ Starting Flask server...")

    print(f"🚀 Starting Governance Dashboard on {host}:{port}")
    app.run(debug=debug, port=port, host=host, use_reloader=False)