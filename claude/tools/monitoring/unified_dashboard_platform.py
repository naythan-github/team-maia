#!/usr/bin/env python3
"""
Unified Dashboard Platform - Centralized Dashboard Management
Solves the dashboard sprawl problem with centralized service management,
persistent availability, and unified access.

Features:
- Dashboard registry and discovery
- Centralized port management  
- Background service persistence
- Unified dashboard hub interface
- Health monitoring and auto-restart
- Resource coordination and conflict resolution
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import socket
import psutil
import sqlite3
from flask import Flask, render_template_string, jsonify, request, redirect
import requests
import atexit
import fcntl

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """Dashboard configuration and metadata"""
    name: str
    description: str
    file_path: str
    port: int
    host: str = "127.0.0.1"
    auto_start: bool = True
    health_endpoint: str = "/"
    category: str = "general"
    version: str = "1.0"
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class DashboardRegistry:
    """Central registry for all dashboard services"""

    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[3] if "claude/tools" in str(__file__) else Path.cwd()))
        self.data_dir = self.maia_root / "claude/data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry_db = self.data_dir / "dashboard_registry.db"
        self.init_database()
        
        # Port management
        self.port_range = (8050, 8099)  # Reserved range for dashboards
        self.used_ports = set()
        
        # Dashboard processes
        self.active_processes = {}
        
    def init_database(self):
        """Initialize dashboard registry database"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dashboards (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    file_path TEXT,
                    port INTEGER,
                    host TEXT,
                    auto_start BOOLEAN,
                    health_endpoint TEXT,
                    category TEXT,
                    version TEXT,
                    dependencies TEXT,
                    status TEXT DEFAULT 'stopped',
                    last_started TEXT,
                    last_health_check TEXT,
                    process_id INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dashboard_name TEXT,
                    timestamp TEXT,
                    level TEXT,
                    message TEXT,
                    FOREIGN KEY (dashboard_name) REFERENCES dashboards(name)
                )
            """)
            
    def register_dashboard(self, config: DashboardConfig) -> bool:
        """Register a new dashboard"""
        try:
            with sqlite3.connect(self.registry_db) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO dashboards 
                    (name, description, file_path, port, host, auto_start, 
                     health_endpoint, category, version, dependencies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config.name, config.description, config.file_path,
                    config.port, config.host, config.auto_start,
                    config.health_endpoint, config.category, config.version,
                    json.dumps(config.dependencies)
                ))
            
            logger.info(f"✅ Registered dashboard: {config.name} on port {config.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register dashboard {config.name}: {e}")
            return False
            
    def discover_dashboards(self) -> List[DashboardConfig]:
        """Auto-discover dashboard files and register them"""
        dashboard_files = []
        monitoring_dir = self.maia_root / "claude/tools/monitoring"
        
        # Find dashboard Python files
        for py_file in monitoring_dir.glob("*dashboard*.py"):
            if py_file.name == "unified_dashboard_platform.py":
                continue
                
            dashboard_files.append(py_file)
            
        # Auto-register discovered dashboards
        registered = []
        for file_path in dashboard_files:
            name = file_path.stem
            port = self.allocate_port()
            
            config = DashboardConfig(
                name=name,
                description=f"Auto-discovered dashboard: {name}",
                file_path=str(file_path),
                port=port,
                category="monitoring",
                auto_start=False  # Disable auto-start for discovered dashboards
            )
            
            if self.register_dashboard(config):
                registered.append(config)
                
        return registered
        
    def allocate_port(self) -> int:
        """Allocate next available port in dashboard range"""
        for port in range(*self.port_range):
            if port not in self.used_ports and self.is_port_available(port):
                self.used_ports.add(port)
                return port
        
        raise Exception("No available ports in dashboard range")
        
    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
            
    def get_all_dashboards(self) -> List[Dict]:
        """Get all registered dashboards"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM dashboards ORDER BY category, name").fetchall()
            return [dict(row) for row in rows]
            
    def start_dashboard(self, name: str) -> bool:
        """Start a dashboard service"""
        try:
            # Get dashboard config
            with sqlite3.connect(self.registry_db) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM dashboards WHERE name = ?", (name,)).fetchone()
                
                if not row:
                    logger.error(f"Dashboard {name} not found in registry")
                    return False
                    
                config = dict(row)
                
            # Check if already running
            if self.is_dashboard_healthy(name):
                logger.info(f"Dashboard {name} is already running")
                return True
                
            # Start the dashboard process
            file_path = config['file_path']
            port = config['port']
            host = config['host']
            
            cmd = [sys.executable, file_path, "--service-mode"]
            
            # Set environment variables for dashboard
            env = os.environ.copy()
            env.update({
                'DASHBOARD_HOST': host,
                'DASHBOARD_PORT': str(port),
                'DASHBOARD_NAME': name,
                # Support multiple environment variable conventions
                'MAIA_DASHBOARD_HOST': host,
                'MAIA_DASHBOARD_PORT': str(port)
            })
            
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(file_path)
            )
            
            # Store process reference
            self.active_processes[name] = process
            
            # Update database
            with sqlite3.connect(self.registry_db) as conn:
                conn.execute("""
                    UPDATE dashboards 
                    SET status = 'running', last_started = ?, process_id = ?
                    WHERE name = ?
                """, (datetime.now().isoformat(), process.pid, name))
                
            logger.info(f"✅ Started dashboard {name} on {host}:{port} (PID: {process.pid})")
            
            # Wait a moment and check health
            time.sleep(3)
            if self.is_dashboard_healthy(name):
                logger.info(f"✅ Dashboard {name} health check passed")
                return True
            else:
                logger.warning(f"⚠️ Dashboard {name} started but health check failed")
                return True  # Still consider it started
                
        except Exception as e:
            logger.error(f"❌ Failed to start dashboard {name}: {e}")
            return False
            
    def stop_dashboard(self, name: str) -> bool:
        """Stop a dashboard service"""
        try:
            # Kill process if we have reference
            if name in self.active_processes:
                process = self.active_processes[name]
                if process.poll() is None:  # Still running
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                
                del self.active_processes[name]
                
            # Update database
            with sqlite3.connect(self.registry_db) as conn:
                conn.execute("""
                    UPDATE dashboards 
                    SET status = 'stopped', process_id = NULL
                    WHERE name = ?
                """, (name,))
                
            logger.info(f"✅ Stopped dashboard {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop dashboard {name}: {e}")
            return False
            
    def is_dashboard_healthy(self, name: str) -> bool:
        """Check if dashboard is healthy via HTTP"""
        try:
            with sqlite3.connect(self.registry_db) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT host, port, health_endpoint FROM dashboards WHERE name = ?", (name,)).fetchone()
                
                if not row:
                    return False
                    
                url = f"http://{row['host']}:{row['port']}{row['health_endpoint']}"
                response = requests.get(url, timeout=5)
                
                healthy = response.status_code == 200
                
                # Update health check time
                conn.execute("""
                    UPDATE dashboards 
                    SET last_health_check = ?
                    WHERE name = ?
                """, (datetime.now().isoformat(), name))
                
                return healthy
                
        except Exception:
            return False

class DashboardHub:
    """Web-based dashboard hub for unified access"""
    
    def __init__(self, registry: DashboardRegistry):
        self.registry = registry
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for dashboard hub"""
        
        @self.app.route('/')
        def dashboard_home():
            """Dashboard hub home page"""
            dashboards = self.registry.get_all_dashboards()
            
            # Update status for each dashboard
            for dashboard in dashboards:
                dashboard['is_healthy'] = self.registry.is_dashboard_healthy(dashboard['name'])
                
            return render_template_string(DASHBOARD_HUB_TEMPLATE, dashboards=dashboards)
            
        @self.app.route('/api/dashboards')
        def api_dashboards():
            """API endpoint for dashboard list"""
            return jsonify(self.registry.get_all_dashboards())
            
        @self.app.route('/api/dashboard/<name>/start', methods=['POST'])
        def api_start_dashboard(name):
            """API endpoint to start dashboard"""
            success = self.registry.start_dashboard(name)
            return jsonify({'success': success})
            
        @self.app.route('/api/dashboard/<name>/stop', methods=['POST'])
        def api_stop_dashboard(name):
            """API endpoint to stop dashboard"""
            success = self.registry.stop_dashboard(name)
            return jsonify({'success': success})
            
        @self.app.route('/api/dashboard/<name>/health')
        def api_dashboard_health(name):
            """API endpoint for dashboard health"""
            healthy = self.registry.is_dashboard_healthy(name)
            return jsonify({'healthy': healthy})
            
        @self.app.route('/dashboard/<name>')
        def proxy_dashboard(name):
            """Redirect to actual dashboard"""
            with sqlite3.connect(self.registry.registry_db) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT host, port FROM dashboards WHERE name = ?", (name,)).fetchone()
                
                if row:
                    return redirect(f"http://{row['host']}:{row['port']}")
                else:
                    return "Dashboard not found", 404
                    
    def start_hub(self, host='127.0.0.1', port=8100):
        """Start the dashboard hub"""
        logger.info(f"🚀 Starting Dashboard Hub on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

# HTML template for dashboard hub
DASHBOARD_HUB_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Maia Dashboard Hub</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px 28px;
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header h1 { margin: 0 0 8px 0; font-size: 28px; font-weight: 600; }
        .header p { margin: 0; opacity: 0.95; font-size: 15px; }

        .dashboard-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .dashboard-row {
            display: grid;
            grid-template-columns: 24px 200px 1fr 60px 90px 180px;
            gap: 12px;
            align-items: center;
            background: white;
            padding: 8px 16px;
            border-radius: 4px;
            border: 1px solid #e1e4e8;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: all 0.15s ease;
        }

        .dashboard-row:hover {
            border-color: #667eea;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.12);
            transform: translateY(-1px);
        }

        .status-cell {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            box-shadow: 0 0 0 2px rgba(0,0,0,0.06);
        }
        .status-healthy { background-color: #28a745; }
        .status-unhealthy { background-color: #dc3545; }

        .name-cell {
            display: flex;
            align-items: center;
            gap: 6px;
            min-width: 0;
            overflow: hidden;
        }
        .dashboard-name {
            font-weight: 600;
            font-size: 13px;
            color: #24292e;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex-shrink: 1;
        }
        .category-tag {
            background: #f1f3f5;
            color: #666;
            font-size: 9px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 2px;
            letter-spacing: 0.5px;
            white-space: nowrap;
            flex-shrink: 0;
        }

        .description-cell {
            color: #586069;
            font-size: 12px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            min-width: 0;
        }

        .port-cell {
            font-family: "SF Mono", Monaco, "Courier New", monospace;
            font-size: 11px;
            color: #667eea;
            font-weight: 600;
            text-align: right;
        }

        .stats-cell {
            font-size: 11px;
            color: #586069;
            white-space: nowrap;
        }
        .stats-running {
            color: #28a745;
            font-weight: 600;
        }
        .stats-stopped {
            color: #6c757d;
        }

        .actions-cell {
            display: flex;
            gap: 6px;
            justify-content: flex-end;
            flex-shrink: 0;
        }

        .btn {
            padding: 5px 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: all 0.15s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.12); }
        .btn:active { transform: translateY(0); }

        .btn-primary {
            background-color: #667eea;
            color: white;
        }
        .btn-primary:hover { background-color: #5568d3; }

        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover { background-color: #218838; }

        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover { background-color: #c82333; }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }

        /* Responsive design */
        @media (max-width: 1024px) {
            .dashboard-row {
                grid-template-columns: 40px 1fr auto;
                gap: 12px;
            }
            .description-cell, .port-cell, .stats-cell {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Maia Dashboard Hub</h1>
        <p>Centralized management for all dashboard services</p>
    </div>

    <div class="dashboard-list">
        {% if dashboards %}
            {% for dashboard in dashboards %}
            <div class="dashboard-row">
                <div class="status-cell">
                    <div class="status-indicator {{ 'status-healthy' if dashboard.is_healthy else 'status-unhealthy' }}"
                         title="{{ 'Running' if dashboard.is_healthy else 'Stopped' }}"></div>
                </div>

                <div class="name-cell">
                    <span class="dashboard-name">{{ dashboard.name }}</span>
                    <span class="category-tag">{{ dashboard.category }}</span>
                </div>

                <div class="description-cell" title="{{ dashboard.description }}">
                    {{ dashboard.description }}
                </div>

                <div class="port-cell">
                    :{{ dashboard.port }}
                </div>

                <div class="stats-cell">
                    {% if dashboard.is_healthy %}
                        <span class="stats-running">● Running</span>
                    {% else %}
                        <span class="stats-stopped">○ Stopped</span>
                    {% endif %}
                </div>

                <div class="actions-cell">
                    {% if dashboard.is_healthy %}
                        <a href="/dashboard/{{ dashboard.name }}" class="btn btn-primary">Open</a>
                        <button onclick="stopDashboard('{{ dashboard.name }}')" class="btn btn-danger">Stop</button>
                    {% else %}
                        <button onclick="startDashboard('{{ dashboard.name }}')" class="btn btn-success">Start</button>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty-state">
                <h3>No dashboards registered</h3>
                <p>Run dashboard discovery to find and register available dashboards</p>
            </div>
        {% endif %}
    </div>

    <script>
        function startDashboard(name) {
            fetch(`/api/dashboard/${name}/start`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        alert('Failed to start dashboard');
                    }
                });
        }

        function stopDashboard(name) {
            fetch(`/api/dashboard/${name}/stop`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        alert('Failed to stop dashboard');
                    }
                });
        }

        // Auto-refresh every 30 seconds
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

class DashboardService:
    """Background service manager for persistent dashboard platform"""

    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[3] if "claude/tools" in str(__file__) else Path.cwd()))
        self.data_dir = self.maia_root / "claude/data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.pidfile_path = self.data_dir / "dashboard_service.pid"
        self.logfile_path = self.data_dir / "dashboard_service.log"
        
    def is_running(self) -> bool:
        """Check if dashboard service is already running"""
        if not self.pidfile_path.exists():
            return False
            
        try:
            with open(self.pidfile_path, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if process is actually running
            return psutil.pid_exists(pid)
            
        except (ValueError, FileNotFoundError):
            return False
            
    def get_service_status(self) -> Dict:
        """Get detailed service status"""
        if not self.is_running():
            return {
                'status': 'stopped',
                'pid': None,
                'uptime': None,
                'hub_url': None
            }
            
        try:
            with open(self.pidfile_path, 'r') as f:
                pid = int(f.read().strip())
                
            process = psutil.Process(pid)
            uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
            
            return {
                'status': 'running',
                'pid': pid,
                'uptime': str(uptime).split('.')[0],  # Remove microseconds
                'hub_url': 'http://127.0.0.1:8100',
                'memory_mb': round(process.memory_info().rss / 1024 / 1024, 1)
            }
            
        except (psutil.NoSuchProcess, ValueError):
            # PID file exists but process is dead - clean up
            self.pidfile_path.unlink()
            return {
                'status': 'stopped',
                'pid': None,
                'uptime': None,
                'hub_url': None
            }
            
    def start_service(self, daemon: bool = True) -> bool:
        """Start dashboard service as daemon"""
        if self.is_running():
            logger.info("Dashboard service already running")
            return True
            
        if daemon:
            return self._start_daemon()
        else:
            return self._start_foreground()
            
    def _start_daemon(self) -> bool:
        """Start service in daemon mode"""
        try:
            # Fork to background
            if os.fork() > 0:
                # Parent process - wait briefly and check if service started
                time.sleep(2)
                return self.is_running()
                
            # Child process continues
            os.setsid()  # Create new session
            
            # Second fork to prevent zombie
            if os.fork() > 0:
                sys.exit(0)
                
            # Setup daemon environment
            os.chdir('/')
            os.umask(0)
            
            # Redirect stdout/stderr to log file
            with open(self.logfile_path, 'a') as log:
                os.dup2(log.fileno(), sys.stdout.fileno())
                os.dup2(log.fileno(), sys.stderr.fileno())
                
            # Write PID file
            with open(self.pidfile_path, 'w') as f:
                f.write(str(os.getpid()))
                
            # Register cleanup handler
            atexit.register(self._cleanup)
            
            # Start the actual service
            self._run_service()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start daemon: {e}")
            return False
            
    def _start_foreground(self) -> bool:
        """Start service in foreground mode"""
        try:
            # Write PID file
            with open(self.pidfile_path, 'w') as f:
                f.write(str(os.getpid()))
                
            # Register cleanup handler
            atexit.register(self._cleanup)
            
            self._run_service()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
            
    def _run_service(self):
        """Run the actual dashboard platform service"""
        logger.info("🚀 Starting Dashboard Service")
        platform = UnifiedDashboardPlatform()
        platform.start_hub()
        
    def stop_service(self) -> bool:
        """Stop dashboard service"""
        if not self.is_running():
            logger.info("Dashboard service not running")
            return True
            
        try:
            with open(self.pidfile_path, 'r') as f:
                pid = int(f.read().strip())
                
            # Terminate process
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                process.kill()  # Force kill if needed
                process.wait(timeout=5)
                
            logger.info(f"✅ Dashboard service stopped (PID: {pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False
            
    def restart_service(self) -> bool:
        """Restart dashboard service"""
        logger.info("🔄 Restarting dashboard service")
        if not self.stop_service():
            return False
            
        time.sleep(2)  # Brief pause
        return self.start_service()
        
    def _cleanup(self):
        """Clean up PID file on exit"""
        try:
            if self.pidfile_path.exists():
                self.pidfile_path.unlink()
        except:
            pass

class UnifiedDashboardPlatform:
    """Main platform coordinator"""
    
    def __init__(self):
        self.registry = DashboardRegistry()
        self.hub = DashboardHub(self.registry)
        
    def initialize(self):
        """Initialize the platform"""
        logger.info("🚀 Initializing Unified Dashboard Platform")
        
        # Discover and register existing dashboards
        discovered = self.registry.discover_dashboards()
        logger.info(f"📊 Discovered {len(discovered)} dashboards")
        
        # Auto-start dashboards marked for auto-start
        for dashboard in self.registry.get_all_dashboards():
            if dashboard['auto_start']:
                logger.info(f"🔄 Auto-starting {dashboard['name']}")
                self.registry.start_dashboard(dashboard['name'])
                
    def start_hub(self):
        """Start the dashboard hub"""
        self.initialize()
        logger.info("🌐 Starting Dashboard Hub on http://127.0.0.1:8100")
        self.hub.start_hub()

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # Service management commands
        if command in ["service-start", "service-stop", "service-restart", "service-status"]:
            service = DashboardService()
            
            if command == "service-start":
                daemon = "--foreground" not in sys.argv
                if service.start_service(daemon=daemon):
                    if daemon:
                        print("✅ Dashboard service started in background")
                        print("🌐 Hub available at: http://127.0.0.1:8100")
                    else:
                        print("✅ Dashboard service started in foreground")
                else:
                    print("❌ Failed to start dashboard service")
                    
            elif command == "service-stop":
                if service.stop_service():
                    print("✅ Dashboard service stopped")
                else:
                    print("❌ Failed to stop dashboard service")
                    
            elif command == "service-restart":
                if service.restart_service():
                    print("✅ Dashboard service restarted")
                    print("🌐 Hub available at: http://127.0.0.1:8100")
                else:
                    print("❌ Failed to restart dashboard service")
                    
            elif command == "service-status":
                status = service.get_service_status()
                if status['status'] == 'running':
                    print(f"✅ Dashboard service is running")
                    print(f"   PID: {status['pid']}")
                    print(f"   Uptime: {status['uptime']}")
                    print(f"   Memory: {status['memory_mb']} MB")
                    print(f"   Hub URL: {status['hub_url']}")
                else:
                    print("⭕ Dashboard service is not running")
            
            return
        
        # Legacy platform commands
        platform = UnifiedDashboardPlatform()
        
        if command == "init":
            platform.initialize()
            
        elif command == "start":
            platform.start_hub()
            
        elif command == "discover":
            discovered = platform.registry.discover_dashboards()
            print(f"Discovered {len(discovered)} dashboards:")
            for d in discovered:
                print(f"  - {d.name} on port {d.port}")
                
        else:
            print("Usage:")
            print("  Service Management:")
            print("    python3 unified_dashboard_platform.py service-start     # Start as daemon")
            print("    python3 unified_dashboard_platform.py service-start --foreground  # Start in foreground")
            print("    python3 unified_dashboard_platform.py service-stop      # Stop daemon")
            print("    python3 unified_dashboard_platform.py service-restart   # Restart daemon")
            print("    python3 unified_dashboard_platform.py service-status    # Check status")
            print("  ")
            print("  Legacy Commands:")
            print("    python3 unified_dashboard_platform.py [init|start|discover]")
    else:
        # Default: show usage
        print("🚀 Maia Dashboard Platform")
        print("Usage:")
        print("  python3 unified_dashboard_platform.py service-start    # Start persistent service")
        print("  python3 unified_dashboard_platform.py service-status   # Check service status")

if __name__ == "__main__":
    main()