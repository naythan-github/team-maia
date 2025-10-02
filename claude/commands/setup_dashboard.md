# Setup Dashboard Command

**Command**: `setup_dashboard`  
**Purpose**: One-time setup and configuration of the AI Business Intelligence Dashboard for persistent, easy access  
**Category**: System Setup & Configuration  
**Phase**: 19 - Dashboard Service Management  

## Overview

This command performs comprehensive setup of the AI Business Intelligence Dashboard, ensuring it's easily accessible, persistent, and production-ready with automatic dependency management and service configuration.

## Key Capabilities

### 🚀 **One-Command Setup**
- Automatic dependency installation and validation
- Service launcher script creation for easy access
- Background service configuration with health monitoring
- Persistent service setup with auto-restart capabilities
- Production-ready deployment configuration

### 🔧 **Service Management**
- Background service operation with process monitoring
- Automatic port detection and conflict resolution
- Health checks and automatic restart on failure
- Service status monitoring and logging
- Graceful shutdown and restart capabilities

### 🌐 **Easy Access Methods**
- Convenient launcher script with intuitive commands
- Direct service manager access for advanced operations
- Browser integration for one-click dashboard access
- Status monitoring and log viewing capabilities
- Multiple deployment options (local, network, autostart)

## Usage Examples

### Initial Setup
```bash
# Complete dashboard setup (recommended)
maia setup_dashboard

# Setup with custom configuration
maia setup_dashboard --port=8080 --host=0.0.0.0

# Setup with autostart enabled
maia setup_dashboard --autostart
```

### Service Management After Setup
```bash
# Quick access via launcher script
./dashboard start          # Start dashboard service
./dashboard stop           # Stop dashboard service  
./dashboard restart        # Restart dashboard service
./dashboard status         # Show service status
./dashboard logs           # View service logs
./dashboard open           # Open dashboard in browser

# Advanced service management
python3 claude/tools/dashboard_service_manager.py start
python3 claude/tools/dashboard_service_manager.py status
python3 claude/tools/dashboard_service_manager.py install-deps
```

### Dashboard Access Methods
```bash
# Method 1: Launcher script (simplest)
./dashboard start && ./dashboard open

# Method 2: Direct URL access
open http://127.0.0.1:8050

# Method 3: Service manager
python3 claude/tools/dashboard_service_manager.py start
```

## Command Parameters

### Setup Parameters
- `--port=<port>`: Dashboard port (default: 8050)
- `--host=<host>`: Dashboard host (default: 127.0.0.1)
- `--autostart`: Enable automatic startup on system boot
- `--network`: Enable network access (host=0.0.0.0)

### Service Parameters
- `--background`: Run service in background (default: true)
- `--health-checks`: Enable health monitoring (default: true)
- `--auto-restart`: Enable automatic restart on failure (default: true)
- `--log-level=<level>`: Logging level (info, debug, warning)

### Deployment Parameters
- `--production`: Production deployment configuration
- `--install-deps`: Force dependency installation
- `--create-launcher`: Create launcher script
- `--setup-autostart`: Configure system autostart

## Setup Process

### Phase 1: Dependency Management
1. **Dependency Detection**: Scan for required packages (dash, plotly, etc.)
2. **Automatic Installation**: Install missing dependencies via pip
3. **Validation**: Verify all dependencies are correctly installed
4. **Fallback Configuration**: Configure graceful fallbacks for optional features

### Phase 2: Service Configuration
1. **Port Allocation**: Detect available ports and resolve conflicts
2. **Service Registration**: Configure background service with health monitoring
3. **Logging Setup**: Configure service logs and error handling
4. **Process Management**: Setup PID tracking and process monitoring

### Phase 3: Access Methods
1. **Launcher Script**: Create convenient `./dashboard` launcher
2. **Service Manager**: Configure advanced service management tools
3. **Browser Integration**: Setup one-click browser access
4. **Status Monitoring**: Configure service status and health checks

### Phase 4: Production Deployment
1. **Auto-Restart**: Configure automatic restart on failure
2. **System Integration**: Optional autostart on system boot
3. **Network Configuration**: Configure network access if requested
4. **Security**: Apply production security configurations

## Output Format

### Setup Success
```json
{
  "setup_status": "complete",
  "dashboard_url": "http://127.0.0.1:8050",
  "launcher_script": "${MAIA_ROOT}/dashboard",
  "service_manager": "${MAIA_ROOT}/claude/tools/dashboard_service_manager.py",
  "dependencies_installed": [
    "dash",
    "plotly", 
    "dash-bootstrap-components",
    "pandas",
    "numpy",
    "scikit-learn"
  ],
  "features_enabled": [
    "background_service",
    "health_monitoring",
    "auto_restart",
    "launcher_script",
    "browser_integration"
  ],
  "quick_start": [
    "./dashboard start",
    "./dashboard open"
  ]
}
```

### Service Status
```json
{
  "service_running": true,
  "service_url": "http://127.0.0.1:8050",
  "process_id": 12345,
  "uptime": "2 hours, 15 minutes",
  "health_status": "healthy",
  "cpu_usage": 2.3,
  "memory_usage": 1.2,
  "last_health_check": "2025-01-13T14:30:22Z"
}
```

## Access Methods After Setup

### Method 1: Launcher Script (Recommended)
```bash
# Quick start
./dashboard start && ./dashboard open

# Individual commands
./dashboard start     # Start service
./dashboard status    # Check status
./dashboard logs      # View logs
./dashboard stop      # Stop service
./dashboard restart   # Restart service
./dashboard open      # Open in browser
```

### Method 2: Service Manager (Advanced)
```bash
# Start with custom configuration
python3 claude/tools/dashboard_service_manager.py start --port=8080

# Check detailed status
python3 claude/tools/dashboard_service_manager.py status

# Install/update dependencies
python3 claude/tools/dashboard_service_manager.py install-deps

# Setup autostart
python3 claude/tools/dashboard_service_manager.py setup-autostart
```

### Method 3: Direct Access
```bash
# Start dashboard directly
python3 claude/tools/ai_business_intelligence_dashboard.py

# Access via browser
open http://127.0.0.1:8050
```

## Troubleshooting

### Common Issues
- **Port Conflicts**: Service manager automatically finds available ports
- **Missing Dependencies**: Run `./dashboard install-deps` or use service manager
- **Service Won't Start**: Check logs with `./dashboard logs`
- **Permission Issues**: Ensure scripts are executable (`chmod +x dashboard`)

### Dependency Issues
```bash
# Manual dependency installation
pip3 install dash plotly dash-bootstrap-components pandas numpy scikit-learn

# Check dependency status
python3 claude/tools/dashboard_service_manager.py status
```

### Service Issues
```bash
# Force restart
./dashboard stop && ./dashboard start

# Check process status
./dashboard status

# View detailed logs
tail -f claude/data/dashboard.log
```

## Production Configuration

### Network Access
```bash
# Enable network access for team use
maia setup_dashboard --network --port=8050

# Access from other machines
# Dashboard available at: http://your-ip-address:8050
```

### Autostart Configuration
```bash
# Setup automatic startup on system boot
maia setup_dashboard --autostart

# Manual autostart setup
python3 claude/tools/dashboard_service_manager.py setup-autostart
```

### Security Considerations
- Dashboard runs locally by default (127.0.0.1)
- Network access requires explicit configuration
- Service logs contain no sensitive information
- All data processing occurs locally

## Integration Points

### Maia Ecosystem Integration
- **Phase 18 Analytics**: Automatic connection to predictive analytics engine
- **Command System**: Integrated with Maia command orchestration
- **Context Management**: Uses UFC system for configuration
- **Agent Coordination**: Coordinates with specialized agents for data

### System Integration
- **macOS LaunchAgent**: Optional autostart via LaunchAgent
- **Process Management**: Integration with system process monitoring
- **Browser Integration**: One-click access via system browser
- **Log Management**: Centralized logging with rotation and cleanup

## Best Practices

### Initial Setup
1. **Run Complete Setup**: Use `maia setup_dashboard` for comprehensive configuration
2. **Verify Dependencies**: Ensure all dependencies install successfully
3. **Test Access Methods**: Verify both launcher script and direct access work
4. **Configure Autostart**: Consider enabling autostart for persistent access

### Daily Usage
1. **Use Launcher Script**: `./dashboard start` for quickest access
2. **Monitor Health**: Check `./dashboard status` periodically
3. **View Logs**: Use `./dashboard logs` for troubleshooting
4. **Graceful Shutdown**: Use `./dashboard stop` when done

### Maintenance
1. **Regular Updates**: Update dependencies periodically
2. **Log Cleanup**: Monitor log file sizes and clean up as needed
3. **Health Monitoring**: Check service health during regular system maintenance
4. **Backup Configuration**: Backup service configuration for disaster recovery

## Professional Value

### Engineering Manager Positioning
- **Operational Excellence**: Demonstrates production service management capabilities
- **Automation Leadership**: Shows advanced automation and monitoring setup
- **System Architecture**: Exhibits sophisticated system design and deployment
- **Technical Leadership**: Showcases ability to create production-ready solutions

### AI/Automation Demonstration
- **Intelligent Monitoring**: Shows AI-powered business intelligence in action
- **Automated Operations**: Demonstrates sophisticated automation capabilities
- **Production Deployment**: Exhibits enterprise-grade deployment practices
- **Service Excellence**: Shows commitment to operational excellence and reliability

---

**Setup Achievement**: The setup_dashboard command transforms the AI Business Intelligence Dashboard from a development tool into a production-ready service with enterprise-grade deployment, monitoring, and access capabilities.

*This command ensures the dashboard is always accessible, reliable, and ready to demonstrate advanced AI/automation capabilities for Engineering Manager positioning.*