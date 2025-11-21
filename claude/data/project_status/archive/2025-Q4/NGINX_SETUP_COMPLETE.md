# nginx Service Mesh - Setup Complete ✅

**Status**: Fully configured and operational
**Service Mesh Port**: 8080
**nginx Version**: 1.29.1

## ✅ What Was Installed

### nginx Installation
- Installed via: `brew install nginx`
- Location: `/opt/homebrew/Cellar/nginx/1.29.1`
- Config: `/opt/homebrew/etc/nginx/nginx.conf`
- Servers: `/opt/homebrew/etc/nginx/servers/`

### Maia Configuration
- Service mesh config: `/opt/homebrew/etc/nginx/servers/maia_dashboards.conf`
- Source config: `claude/tools/monitoring/config/nginx_dashboard_mesh.conf`
- Backup hosts: `/etc/hosts.backup.YYYYMMDD_HHMMSS`

### /etc/hosts Entries
```
127.0.0.1    hub.maia.local
127.0.0.1    ai.maia.local
127.0.0.1    dora.maia.local
127.0.0.1    governance.maia.local
```

## 🌐 Access Methods

### Option 1: Service Mesh (nginx - Port 8080)
**Enterprise architecture with reverse proxy**

```
http://localhost:8080              → nginx welcome page
http://hub.maia.local              → Unified Hub (proxied)
http://ai.maia.local               → AI Business Intelligence (proxied)
http://dora.maia.local             → DORA Metrics (proxied)
http://governance.maia.local       → Governance Dashboard (proxied)
```

**Features**:
- Path-based routing
- Health check aggregation
- WebSocket support for Dash apps
- Enterprise service discovery

### Option 2: Direct Port Access
**Simple access without nginx**

```
http://localhost:8100  → Unified Hub (direct)
http://localhost:8050  → AI Business Intelligence (direct)
http://localhost:8060  → DORA Metrics (direct)
http://localhost:8070  → Governance (direct)
http://localhost:8504  → System Status (direct)
http://localhost:8506  → Token Savings (direct)
```

## 🎯 Dashboard Control Commands

### Updated ./dashboard Script

```bash
# Start all dashboards + nginx
./dashboard start

# Stop all dashboards + nginx
./dashboard stop

# Check nginx status
./dashboard nginx

# List all URLs (direct + nginx)
./dashboard list

# Show dashboard status
./dashboard status
```

## 🔧 nginx Management

### Start/Stop nginx
```bash
# Start nginx service
brew services start nginx

# Stop nginx service
brew services stop nginx

# Restart nginx
brew services restart nginx

# Check nginx status
brew services list | grep nginx
```

### Test nginx Configuration
```bash
# Test config syntax
nginx -t

# Reload nginx (after config changes)
brew services restart nginx
```

### View nginx Logs
```bash
# Access log
tail -f /opt/homebrew/var/log/nginx/access.log

# Error log
tail -f /opt/homebrew/var/log/nginx/error.log
```

## 📊 Service Mesh Architecture

### nginx Upstream Configuration
```nginx
upstream dashboard_hub {
    server 127.0.0.1:8100;
}

upstream ai_business_intelligence {
    server 127.0.0.1:8050;
}

upstream dora_metrics {
    server 127.0.0.1:8060;
}

upstream governance_dashboard {
    server 127.0.0.1:8070;
}
```

### Virtual Hosts
- `hub.maia.local` → Port 8100
- `ai.maia.local` → Port 8050
- `dora.maia.local` → Port 8060
- `governance.maia.local` → Port 8070

### Features Enabled
- ✅ WebSocket support for Dash applications
- ✅ Proxy headers (X-Real-IP, X-Forwarded-For)
- ✅ Health check endpoints (`/health`)
- ✅ Service discovery via catch-all server

## 🚀 Quick Start

### Full Stack Launch
```bash
# 1. Start all dashboards (includes nginx)
./dashboard start

# 2. Access via service mesh
open http://localhost:8080

# 3. Or access Unified Hub directly
open http://hub.maia.local

# 4. Check status
./dashboard nginx
```

### Individual Dashboard Access
```bash
# Via nginx service mesh
open http://ai.maia.local

# Or direct port access
open http://localhost:8050
```

## 🔍 Troubleshooting

### nginx Won't Start
```bash
# Check if port 8080 is in use
lsof -i :8080

# Check nginx error log
tail -f /opt/homebrew/var/log/nginx/error.log

# Test configuration
nginx -t
```

### Can't Access *.maia.local Domains
```bash
# Check /etc/hosts entries
cat /etc/hosts | grep maia.local

# If missing, run setup script
./setup_nginx_hosts.sh

# Or manually add to /etc/hosts:
sudo nano /etc/hosts
# Add: 127.0.0.1 hub.maia.local ai.maia.local dora.maia.local governance.maia.local
```

### Dashboard Not Responding via nginx
```bash
# 1. Ensure dashboard is running on its port
./dashboard status

# 2. Test direct port access first
curl http://localhost:8100

# 3. Then test via nginx
curl http://hub.maia.local

# 4. Check nginx error logs
tail -f /opt/homebrew/var/log/nginx/error.log
```

### Port 8080 Conflict
```bash
# Check what's using port 8080
lsof -i :8080

# If needed, change nginx port in:
/opt/homebrew/etc/nginx/nginx.conf
# Change: listen 8080; to another port
```

## 📈 Benefits of Service Mesh

### Enterprise Features
1. **Unified Access Point**: Single port (8080) for all services
2. **Health Aggregation**: Centralized health checks
3. **Load Balancing**: nginx can distribute traffic
4. **WebSocket Support**: Full Dash app functionality
5. **Service Discovery**: Automatic routing to services

### Production Ready
- Health monitoring endpoints
- Proxy headers for client identification
- WebSocket support for real-time dashboards
- Graceful handling of service failures

## ✅ Setup Checklist

- [x] Install nginx via homebrew
- [x] Copy Maia dashboard mesh config
- [x] Test nginx configuration
- [x] Start nginx service
- [x] Add /etc/hosts entries
- [x] Update dashboard control script
- [x] Test service mesh access
- [x] Document setup and usage

## 🎊 Success!

**nginx service mesh fully operational!**

**Access your dashboards**:
- Service Mesh: http://localhost:8080
- Unified Hub: http://hub.maia.local
- AI Dashboard: http://ai.maia.local

**Manage services**:
```bash
./dashboard start   # Start all + nginx
./dashboard nginx   # Check nginx status
./dashboard list    # See all URLs
```

---

**Enterprise dashboard architecture restored on new MacBook!** 🚀
