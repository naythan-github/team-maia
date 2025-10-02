#!/usr/bin/env python3
"""
Dashboard Service Manager - Production Dashboard Deployment
Comprehensive service management for the AI Business Intelligence Dashboard,
ensuring persistent operation, dependency management, and easy access.

Features:
- Automatic dependency installation and management
- Background service operation with process monitoring
- Health checks and automatic restart capabilities
- Multiple access methods (local, network, tunnel)
- Service status monitoring and logging
- Production-ready deployment configuration
"""

import os
import sys
import subprocess
import time
import signal
import json
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import datetime
import socket
import urllib.request
import urllib.error
from claude.tools.core.path_manager import get_maia_root

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    host: str = "127.0.0.1"
    port: int = 8050
    debug: bool = False
    auto_restart: bool = True
    health_check_interval: int = 30
    log_file: str = str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "dashboard.log")
    pid_file: str = str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "dashboard.pid")
    service_name: str = "maia-dashboard"

@dataclass
class ServiceStatus:
    """Service status information"""
    is_running: bool
    pid: Optional[int]
    port: int
    host: str
    url: str
    uptime: Optional[str]
    last_health_check: Optional[str]
    health_status: str
    cpu_usage: Optional[float]
    memory_usage: Optional[float]

class DashboardServiceManager:
    """Comprehensive dashboard service management"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.data_dir = Path("${MAIA_ROOT}/claude/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Service tracking
        self.pid_file = Path(self.config.pid_file)
        self.log_file = Path(self.config.log_file)
        self.service_url = f"http://{self.config.host}:{self.config.port}"
        
        # Dependencies
        self.required_packages = [
            "dash",
            "plotly", 
            "dash-bootstrap-components",
            "pandas",
            "numpy",
            "scikit-learn",
            "psutil"
        ]
        
        logger.info(f"Dashboard Service Manager initialized for {self.service_url}")
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required dependencies are installed"""
        dependency_status = {}
        
        for package in self.required_packages:
            try:
                __import__(package.replace('-', '_'))
                dependency_status[package] = True
            except ImportError:
                dependency_status[package] = False
        
        return dependency_status
    
    def install_dependencies(self) -> bool:
        """Install missing dependencies"""
        missing_deps = []
        dependency_status = self.check_dependencies()
        
        for package, installed in dependency_status.items():
            if not installed:
                missing_deps.append(package)
        
        if not missing_deps:
            logger.info("All dependencies already installed")
            return True
        
        logger.info(f"Installing missing dependencies: {missing_deps}")
        
        try:
            # Use pip to install missing packages
            for package in missing_deps:
                logger.info(f"Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.error(f"Failed to install {package}: {result.stderr}")
                    return False
                else:
                    logger.info(f"Successfully installed {package}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def is_port_available(self, host: str, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return False
    
    def find_available_port(self, start_port: int = 8050, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            if self.is_port_available(self.config.host, port):
                return port
        
        raise Exception(f"No available ports found in range {start_port}-{start_port + max_attempts}")
    
    def get_service_status(self) -> ServiceStatus:
        """Get current service status"""
        pid = self.get_running_pid()
        is_running = pid is not None
        
        status = ServiceStatus(
            is_running=is_running,
            pid=pid,
            port=self.config.port,
            host=self.config.host,
            url=self.service_url,
            uptime=None,
            last_health_check=None,
            health_status="unknown",
            cpu_usage=None,
            memory_usage=None
        )
        
        if is_running and pid:
            try:
                process = psutil.Process(pid)
                status.uptime = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time()))
                status.cpu_usage = process.cpu_percent()
                status.memory_usage = process.memory_percent()
                
                # Check if dashboard is responding
                try:
                    urllib.request.urlopen(self.service_url, timeout=5)
                    status.health_status = "healthy"
                except urllib.error.URLError:
                    status.health_status = "unhealthy"
                    
                status.last_health_check = datetime.datetime.now().isoformat()
                
            except psutil.NoSuchProcess:
                status.is_running = False
                status.health_status = "process_not_found"
        
        return status
    
    def get_running_pid(self) -> Optional[int]:
        """Get PID of running dashboard service with robust detection"""
        # Method 1: Check PID file (preferred method)
        pid_from_file = self._get_pid_from_file()
        if pid_from_file:
            return pid_from_file
        
        # Method 2: Search all processes for dashboard instances
        return self._find_dashboard_processes()
    
    def _get_pid_from_file(self) -> Optional[int]:
        """Get PID from PID file if valid"""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                # Check if it's actually our dashboard process
                if self._is_dashboard_process(process):
                    return pid
            
            # PID file exists but process is not running - clean up
            self.pid_file.unlink()
            return None
            
        except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
            return None
    
    def _find_dashboard_processes(self) -> Optional[int]:
        """Find running dashboard processes by scanning all processes"""
        dashboard_pids = []
        
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if self._is_dashboard_process(proc):
                        pid = proc.info['pid']
                        
                        # Try to get connections for this process
                        try:
                            process = psutil.Process(pid)
                            connections = process.net_connections()
                            for conn in connections:
                                if (conn.status == 'LISTEN' and 
                                    conn.laddr.port in [self.config.port, 8050, 8051, 8052]):
                                    dashboard_pids.append((pid, conn.laddr.port))
                                    break
                            else:
                                # No port match, but it's a dashboard process
                                dashboard_pids.append((pid, None))
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            # Can't access connections, but it's still a dashboard process
                            dashboard_pids.append((pid, None))
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                    continue
        
        except Exception as e:
            logger.warning(f"Error scanning processes: {e}")
            return None
        
        if not dashboard_pids:
            return None
        
        # Prefer process on our configured port, otherwise return first found
        for pid, port in dashboard_pids:
            if port == self.config.port:
                logger.info(f"Found dashboard process {pid} on expected port {port}")
                return pid
        
        # Return first dashboard process found
        pid, port = dashboard_pids[0]
        if port:
            logger.info(f"Found dashboard process {pid} on port {port} (expected {self.config.port})")
            # Update our config to match the running instance
            self.config.port = port
            self.service_url = f"http://{self.config.host}:{port}"
        else:
            logger.info(f"Found dashboard process {pid} (port unknown)")
        
        return pid
    
    def _is_dashboard_process(self, process) -> bool:
        """Check if a process is a dashboard instance"""
        try:
            cmdline = process.cmdline() if hasattr(process, 'cmdline') else process.info.get('cmdline', [])
            if not cmdline:
                return False
            
            cmdline_str = " ".join(cmdline)
            
            # Check for various dashboard script patterns
            dashboard_patterns = [
                "ai_business_intelligence_dashboard",
                "dashboard_service_manager", 
                "maia_dashboard",
                "business_intelligence_dashboard"
            ]
            
            return any(pattern in cmdline_str for pattern in dashboard_patterns)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            return False
    
    def start_service(self, background: bool = True) -> bool:
        """Start the dashboard service"""
        # Check if already running
        if self.get_running_pid():
            logger.info("Dashboard service is already running")
            return True
        
        # Check dependencies
        if not self.install_dependencies():
            logger.error("Failed to install required dependencies")
            return False
        
        # Find available port if current one is taken
        if not self.is_port_available(self.config.host, self.config.port):
            logger.warning(f"Port {self.config.port} is not available, finding alternative...")
            self.config.port = self.find_available_port(self.config.port)
            self.service_url = f"http://{self.config.host}:{self.config.port}"
            logger.info(f"Using port {self.config.port}")
        
        # Prepare dashboard script
        dashboard_script = Path(str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "tools" / "ai_business_intelligence_dashboard.py"))
        
        if background:
            # Start in background
            logger.info(f"Starting dashboard service in background on {self.service_url}")
            
            # Prepare environment
            env = os.environ.copy()
            env['MAIA_DASHBOARD_HOST'] = self.config.host
            env['MAIA_DASHBOARD_PORT'] = str(self.config.port)
            env['PYTHONPATH'] = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())
            
            # Start process
            with open(self.log_file, 'a') as log_file:
                process = subprocess.Popen([
                    sys.executable, str(dashboard_script), "--service-mode"
                ], 
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())
                )
            
            # Store PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Enhanced validation with port binding verification
            logger.info("Validating service startup...")
            for attempt in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                
                # Check if process is still running
                if not self.get_running_pid():
                    logger.error(f"Dashboard process terminated unexpectedly (attempt {attempt + 1})")
                    continue
                
                # Check if port is bound
                try:
                    import urllib.request
                    urllib.request.urlopen(self.service_url, timeout=2)
                    logger.info(f"✅ Dashboard service started successfully (PID: {process.pid})")
                    logger.info(f"✅ Port {self.config.port} is bound and responding")
                    logger.info(f"🌐 Access dashboard at: {self.service_url}")
                    return True
                except urllib.error.URLError:
                    logger.debug(f"Port not yet bound (attempt {attempt + 1})")
                    continue
            
            # Final verification failed
            logger.error("❌ Dashboard service failed to bind to port within timeout")
            logger.error(f"❌ Process running but port {self.config.port} not responding")
            return False
        else:
            # Start in foreground
            logger.info(f"Starting dashboard service in foreground on {self.service_url}")
            try:
                subprocess.run([
                    sys.executable, str(dashboard_script)
                ], cwd=str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
                return True
            except KeyboardInterrupt:
                logger.info("Dashboard service stopped by user")
                return True
            except Exception as e:
                logger.error(f"Error starting dashboard: {e}")
                return False
    
    def stop_service(self) -> bool:
        """Stop the dashboard service"""
        pid = self.get_running_pid()
        
        if not pid:
            logger.info("Dashboard service is not running")
            return True
        
        try:
            logger.info(f"Stopping dashboard service (PID: {pid})")
            process = psutil.Process(pid)
            
            # Try graceful shutdown first
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                logger.warning("Graceful shutdown timed out, forcing kill")
                process.kill()
                process.wait(timeout=5)
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info("Dashboard service stopped successfully")
            return True
            
        except psutil.NoSuchProcess:
            logger.info("Process already terminated")
            if self.pid_file.exists():
                self.pid_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the dashboard service"""
        logger.info("Restarting dashboard service...")
        
        if not self.stop_service():
            return False
        
        time.sleep(2)  # Brief pause
        return self.start_service()
    
    def create_launcher_script(self) -> str:
        """Create a convenient launcher script"""
        launcher_script = Path("${MAIA_ROOT}/dashboard")
        
        script_content = f'''#!/bin/bash
# Maia Dashboard Launcher Script
# Convenient access to AI Business Intelligence Dashboard

MAIA_DIR=str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())
DASHBOARD_MANAGER="$MAIA_DIR/claude/tools/dashboard_service_manager.py"

case "$1" in
    start)
        echo "🚀 Starting Maia Dashboard..."
        python3 "$DASHBOARD_MANAGER" start
        ;;
    stop)
        echo "🛑 Stopping Maia Dashboard..."
        python3 "$DASHBOARD_MANAGER" stop
        ;;
    restart)
        echo "🔄 Restarting Maia Dashboard..."
        python3 "$DASHBOARD_MANAGER" restart
        ;;
    status)
        echo "📊 Dashboard Status:"
        python3 "$DASHBOARD_MANAGER" status
        ;;
    logs)
        echo "📋 Dashboard Logs:"
        tail -f "$MAIA_DIR/claude/data/dashboard.log"
        ;;
    open)
        echo "🌐 Opening Dashboard..."
        open "http://127.0.0.1:8050"
        ;;
    *)
        echo "Maia AI Business Intelligence Dashboard"
        echo "Usage: $0 {{start|stop|restart|status|logs|open}}"
        echo ""
        echo "Commands:"
        echo "  start   - Start dashboard service"
        echo "  stop    - Stop dashboard service"
        echo "  restart - Restart dashboard service"
        echo "  status  - Show service status"
        echo "  logs    - Show service logs"
        echo "  open    - Open dashboard in browser"
        echo ""
        echo "Quick start: $0 start && $0 open"
        exit 1
        ;;
esac
'''
        
        with open(launcher_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        launcher_script.chmod(0o755)
        
        logger.info(f"Launcher script created at: {launcher_script}")
        return str(launcher_script)
    
    def setup_autostart(self) -> bool:
        """Setup dashboard to start automatically (macOS LaunchAgent)"""
        launchd_dir = Path.home() / "Library" / "LaunchAgents"
        launchd_dir.mkdir(parents=True, exist_ok=True)
        
        plist_file = launchd_dir / "com.maia.dashboard.plist"
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maia.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${MAIA_ROOT}/claude/tools/dashboard_service_manager.py</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${MAIA_ROOT}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${MAIA_ROOT}/claude/data/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>${MAIA_ROOT}/claude/data/dashboard.error.log</string>
</dict>
</plist>'''
        
        with open(plist_file, 'w') as f:
            f.write(plist_content)
        
        # Load the service
        try:
            subprocess.run(['launchctl', 'load', str(plist_file)], check=True)
            logger.info("Dashboard autostart configured successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup autostart: {e}")
            return False
    
    def display_status(self):
        """Display comprehensive service status"""
        status = self.get_service_status()
        
        print("🎯 Maia AI Business Intelligence Dashboard Status")
        print("=" * 50)
        print(f"Service Running: {'✅ Yes' if status.is_running else '❌ No'}")
        print(f"Service URL: {status.url}")
        print(f"Health Status: {status.health_status}")
        
        if status.is_running:
            print(f"Process ID: {status.pid}")
            print(f"Uptime: {status.uptime}")
            print(f"CPU Usage: {status.cpu_usage:.1f}%" if status.cpu_usage else "CPU Usage: N/A")
            print(f"Memory Usage: {status.memory_usage:.1f}%" if status.memory_usage else "Memory Usage: N/A")
            print(f"Last Health Check: {status.last_health_check}")
        
        print(f"\n📊 Quick Access:")
        print(f"   🌐 Open Dashboard: open {status.url}")
        print(f"   📋 View Logs: tail -f {self.log_file}")
        print(f"   🔄 Restart Service: python3 {__file__} restart")
        
        # Dependency status
        deps = self.check_dependencies()
        missing = [pkg for pkg, installed in deps.items() if not installed]
        
        if missing:
            print(f"\n⚠️  Missing Dependencies: {', '.join(missing)}")
            print(f"   Install with: python3 {__file__} install-deps")
        else:
            print(f"\n✅ All dependencies installed")

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Maia Dashboard Service Manager")
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'install-deps', 'setup-launcher', 'setup-autostart'], 
                       help='Action to perform')
    parser.add_argument('--host', default='127.0.0.1', help='Dashboard host')
    parser.add_argument('--port', type=int, default=8050, help='Dashboard port')
    parser.add_argument('--foreground', action='store_true', help='Run in foreground')
    
    args = parser.parse_args()
    
    config = DashboardConfig(host=args.host, port=args.port)
    manager = DashboardServiceManager(config)
    
    if args.action == 'start':
        success = manager.start_service(background=not args.foreground)
        if success and not args.foreground:
            print(f"🚀 Dashboard started successfully!")
            print(f"   🌐 Access at: {manager.service_url}")
            print(f"   📊 Status: python3 {__file__} status")
            print(f"   🛑 Stop: python3 {__file__} stop")
        sys.exit(0 if success else 1)
        
    elif args.action == 'stop':
        success = manager.stop_service()
        print("🛑 Dashboard stopped" if success else "❌ Failed to stop dashboard")
        sys.exit(0 if success else 1)
        
    elif args.action == 'restart':
        success = manager.restart_service()
        if success:
            print(f"🔄 Dashboard restarted successfully!")
            print(f"   🌐 Access at: {manager.service_url}")
        else:
            print("❌ Failed to restart dashboard")
        sys.exit(0 if success else 1)
        
    elif args.action == 'status':
        manager.display_status()
        
    elif args.action == 'install-deps':
        success = manager.install_dependencies()
        print("✅ Dependencies installed" if success else "❌ Failed to install dependencies")
        sys.exit(0 if success else 1)
        
    elif args.action == 'setup-launcher':
        launcher_path = manager.create_launcher_script()
        print(f"✅ Launcher script created at: {launcher_path}")
        print(f"   Usage: {launcher_path} {{start|stop|restart|status|logs|open}}")
        
    elif args.action == 'setup-autostart':
        success = manager.setup_autostart()
        print("✅ Autostart configured" if success else "❌ Failed to setup autostart")
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()