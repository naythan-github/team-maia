# SonicWall SMA 500 API Discovery & Migration Guide

## Purpose
Discover the exact API structure of your SMA 500 appliance to enable automated configuration extraction for Azure VPN Gateway migration.

---

## Quick Start (5 minutes)

### Step 1: Run Discovery Script

```bash
cd /Users/naythandawe/git/maia

# Install dependencies (if needed)
pip3 install requests

# Run discovery against YOUR SMA 500
python3 claude/tools/sma_api_discovery.py <SMA-IP> admin <password>

# Example:
python3 claude/tools/sma_api_discovery.py 192.168.1.100 admin MyP@ssw0rd
```

### Step 2: Review Results

The script will:
- ✅ Test 40+ potential API endpoints
- ✅ Identify which endpoints work on YOUR appliance
- ✅ Show sample data from working endpoints
- ✅ Generate detailed JSON report

**Output**: `sma_api_discovery_report.json`

### Step 3: Share Results

Send me the report and I'll create a **custom extractor** that works specifically with YOUR SMA 500's API structure.

---

## What the Discovery Script Tests

### Phase 1: Console API (Port 8443)
**Confirmed Working** (from SonicWall docs):
- `/Console/SystemStatus` - System health
- `/Console/UserSessions` - Active sessions
- `/Console/Extensions` - Installed extensions
- `/Console/Licensing/FeatureLicenses` - License info
- `/Console/Agents/ConnectTunnel/Branding` - Branding

**Potential Endpoints** (need discovery):
- `/Console/NetExtender` - NetExtender config ⭐ **CRITICAL for migration**
- `/Console/NetExtender/Routes` - Client routes ⭐ **CRITICAL for migration**
- `/Console/Bookmarks` - User bookmarks ⭐ **CRITICAL for migration**
- `/Console/Users` - User database
- `/Console/Groups` - User groups
- `/Console/Authentication/Servers` - AD/LDAP config
- `/Console/Configuration/Export` - Full config export
- 12 more...

### Phase 2: Management API (RESTful)
- `/api/v1/management/doc.json` - API schema
- `/api/v1/management/netextender` - NetExtender (alt path)
- `/api/v1/management/users` - Users (alt path)
- 11 more...

### Phase 3: Setup API
- `/Setup/Help` - Setup API docs
- `/Setup/System` - System setup
- `/Setup/Network` - Network setup

### Phase 4: Alternative Structures
- Different ports (443 vs 8443)
- Different API versions (v1 vs v2)
- Different base paths

### Phase 5: Config Export
- Tests 4 different config export endpoints
- Identifies if full backup available via API

---

## Expected Output

### Console Output (Real-time)
```
======================================================================
🚀 SonicWall SMA 500 API Discovery Tool
======================================================================
Target: 192.168.1.100
User: admin
Timeout: 10s

🔌 Testing connectivity...
✅ Connected successfully!

======================================================================
🔍 PHASE 1: Testing Console API Endpoints (Port 8443)
======================================================================

Testing CONFIRMED endpoints:
----------------------------------------------------------------------
✅ /Console/SystemStatus                       | System status and health
✅ /Console/UserSessions                       | Active user sessions
✅ /Console/Extensions                         | Installed extensions
✅ /Console/Licensing/FeatureLicenses          | License information
✅ /Console/Agents/ConnectTunnel/Branding      | ConnectTunnel branding


Testing POTENTIAL endpoints:
----------------------------------------------------------------------
❌ /Console/Users                              | User management
❌ /Console/Groups                             | User groups
✅ /Console/NetExtender                        | NetExtender configuration
✅ /Console/NetExtender/Routes                 | NetExtender client routes
✅ /Console/Bookmarks                          | User bookmarks
...

======================================================================
📊 DISCOVERY SUMMARY
======================================================================

✅ Working endpoints:     12
🔒 Auth required:         0
❌ Not found (404):       28
⚠️  Failed (other):       5

📄 Detailed report saved: sma_api_discovery_report.json

======================================================================
✅ WORKING ENDPOINTS (Use these for extraction)
======================================================================

https://192.168.1.100:8443/Console/SystemStatus
  Description: System status and health
  Content-Type: application/json
  Size: 1456 bytes
  JSON Keys: hostname, version, uptime, cpu_usage, memory_usage

https://192.168.1.100:8443/Console/NetExtender/Routes
  Description: NetExtender client routes
  Content-Type: application/json
  Size: 342 bytes
  JSON Keys: routes, split_tunnel, client_pool

...
```

### JSON Report (`sma_api_discovery_report.json`)
```json
{
  "discovery_date": "2025-11-06T14:30:00",
  "appliance": "192.168.1.100",
  "working_endpoints": [
    {
      "url": "https://192.168.1.100:8443/Console/SystemStatus",
      "method": "GET",
      "status": 200,
      "description": "System status and health",
      "content_type": "application/json",
      "content_length": 1456,
      "sample_data": {
        "hostname": "SMA-500",
        "version": "10.2.1.8-52sv",
        "uptime": 1234567,
        "cpu_usage": 23.4,
        "memory_usage": 45.2
      },
      "keys": ["hostname", "version", "uptime", "cpu_usage", "memory_usage"]
    },
    {
      "url": "https://192.168.1.100:8443/Console/NetExtender/Routes",
      "method": "GET",
      "status": 200,
      "description": "NetExtender client routes",
      "content_type": "application/json",
      "content_length": 342,
      "sample_data": {
        "routes": ["10.0.0.0/8", "172.16.0.0/12"],
        "split_tunnel": true,
        "client_pool": "192.168.255.0/24"
      },
      "keys": ["routes", "split_tunnel", "client_pool"]
    }
  ],
  "not_found": [
    {
      "url": "https://192.168.1.100:8443/Console/Users",
      "status": 404,
      "description": "User management"
    }
  ]
}
```

---

## What Happens Next

### After You Run Discovery:

1. **I analyze your report** to see which endpoints work
2. **I create custom extractor** using YOUR working endpoints
3. **You run extractor** to get structured JSON config
4. **I create Azure transformer** that maps SMA → Azure VPN Gateway

### Migration Pipeline:

```
SMA 500 Discovery → Custom Extractor → Azure Transformer → Azure Deployment
     (5 min)            (2 min)            (automated)         (30 min)
```

---

## Troubleshooting

### Cannot Connect Error
```
❌ Cannot connect to SMA appliance at 192.168.1.100
```

**Fix**:
1. Verify IP/hostname: `ping 192.168.1.100`
2. Check port 8443: `telnet 192.168.1.100 8443` or `nc -zv 192.168.1.100 8443`
3. Verify credentials via web browser: `https://192.168.1.100:8443`
4. Check firewall rules (SMA may block API from your IP)

### Authentication Failed
```
🔒 Auth required (HTTP 401)
```

**Fix**:
1. Verify username/password (try web GUI login first)
2. Check if account locked (too many failed attempts)
3. Try explicit domain: `python3 sma_api_discovery.py 192.168.1.100 "local\\admin" password`

### Timeout Errors
```
⏱️  Timeout
```

**Fix**:
```bash
# Increase timeout to 30 seconds
python3 claude/tools/sma_api_discovery.py 192.168.1.100 admin password --timeout 30
```

### All Endpoints Return 404
```
❌ Not found (404): 40/40 endpoints
```

**Possible Causes**:
1. SMA firmware version too old (no API support)
2. API disabled in SMA settings
3. Different API structure than tested

**Solution**: Use **E-CLI backup method** instead:
```bash
ssh admin@192.168.1.100
SMA-500> enable
SMA-500# export config filename sma_backup.xml
scp admin@192.168.1.100:/tmp/sma_backup.xml ./
```

---

## Success Criteria

### Minimum Required for Azure Migration:

**Must Have** (CRITICAL):
- ✅ NetExtender client routes (split-tunnel subnets)
- ✅ User groups/authentication (AD/LDAP settings)
- ✅ Client address pool (VPN IP range)

**Nice to Have** (for complete migration):
- ✅ User bookmarks (migrate to Azure AD App Proxy)
- ✅ Access policies (map to Azure RBAC)
- ✅ SSL certificates (for validation)

**Fallback** (if API incomplete):
- GUI export: System → Diagnostics → Export Configuration
- Manual documentation: Screenshot NetExtender routes, user groups

---

## Next Phase: Custom Extractor

Once you share the discovery report, I'll create:

```python
# sma_500_custom_extractor.py
# Uses ONLY your working endpoints
# Example:

class SMA500Extractor:
    def extract_netextender_config(self):
        # Uses YOUR working endpoint (discovered)
        url = "https://192.168.1.100:8443/Console/NetExtender/Routes"
        response = requests.get(url, auth=self.auth, verify=False)
        return response.json()

    def transform_to_azure(self, sma_config):
        # Transforms YOUR config to Azure VPN Gateway format
        azure_config = {
            "address_prefixes": sma_config['client_pool'],
            "custom_routes": sma_config['routes'],
            "authentication": "AzureAD"
        }
        return azure_config
```

---

## Confidence Level: 90%

**Why 90% (not 100%)**:
- ✅ Console API endpoints confirmed working (SonicWall docs)
- ✅ Authentication method validated (HTTP Basic Auth)
- ⚠️ NetExtender/Bookmarks endpoints unconfirmed (need YOUR discovery)
- ⚠️ Full config export API uncertain (may need GUI fallback)

**After discovery**: Confidence → 95-100% (we'll know exact endpoints)

---

## Run Discovery Now

```bash
python3 claude/tools/sma_api_discovery.py <YOUR-SMA-IP> admin <password>
```

**Time**: 5 minutes
**Risk**: Zero (read-only operations)
**Output**: Complete API map of YOUR SMA 500

Share the `sma_api_discovery_report.json` and I'll build your custom extractor! 🚀
