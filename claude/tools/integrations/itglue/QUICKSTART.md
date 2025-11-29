# ITGlue API - Quick Start Guide

**Status**: ✅ Production Ready
**Region**: Australian (AU) Instance
**Last Updated**: 2025-11-28

---

## 🚀 Quick Start (5 Minutes)

### 1. Store Your API Key
```bash
python3 -c "import keyring; keyring.set_password('maia-itglue', 'itglue-api-key-sandbox', 'YOUR_API_KEY')"
```

### 2. Test Connection
```python
from claude.tools.integrations.itglue import ITGlueClient

# Australian region
client = ITGlueClient(instance='sandbox', base_url='https://api.au.itglue.com')

# Health check
health = client.health_check()
print(f"Status: {health['status']}")  # Should be 'healthy'
```

### 3. List Organizations
```python
orgs = client.list_organizations()
for org in orgs:
    print(f"{org.name} (ID: {org.id})")
```

---

## 📋 Common Operations

### List All Entities
```python
# Organizations
orgs = client.list_organizations()

# Configurations (for specific org)
configs = client.list_configurations(organization_id='YOUR_ORG_ID')

# Passwords
passwords = client.list_passwords(organization_id='YOUR_ORG_ID')
```

**Note**: Document listing requires JWT authentication and is not supported with API key auth. Documents can be created and uploaded but not listed via the API.

### Create Configuration
```python
config = client.create_configuration(
    organization_id='4489414129010794',
    name='Web Server 01',
    configuration_type='Server',
    serial_number='SN-12345'
)
print(f"Created: {config.id}")
```

### Upload Document
```python
# Upload document with file attachment (two-step process)
doc = client.upload_document(
    organization_id='4489414129010794',
    file_path='/path/to/network_diagram.pdf',
    name='Network Diagram.pdf'
)
print(f"Uploaded: {doc.name} ({doc.size:,} bytes)")
# Returns: Document object with ID, name, size, and upload date
# File is automatically base64-encoded and attached
```

**How it works**:
1. Creates document via `POST /documents`
2. Attaches file via `POST /documents/:id/relationships/attachments` with base64 encoding
3. Returns document metadata including attachment size and upload date

**Note**: This uploads files as attachments. For native ITGlue searchable content, use Flexible Assets (see below).

### Create Flexible Assets (Native ITGlue Documentation)

**Flexible Assets** are ITGlue's native format for structured, searchable documentation.

```python
# Step 1: Create flexible asset type (one-time setup)
asset_type = client.create_flexible_asset_type(
    name='MSP Documentation',
    description='General MSP documentation with rich text content'
)
# Default fields: 'title' (Text) and 'content' (Textbox)

# Step 2: Create flexible asset from markdown file
asset = client.create_flexible_asset_from_markdown(
    organization_id='4489414129010794',
    flexible_asset_type_id=asset_type['id'],
    file_path='/path/to/network_diagram.md'
)
print(f"Created: {asset.name} (ID: {asset.id})")
# Markdown is automatically converted to HTML and stored as native ITGlue content
```

**Why Flexible Assets?**
- ✅ **Searchable** in ITGlue (not just file attachments)
- ✅ **Native format** - rendered directly in ITGlue UI
- ✅ **Structured** - custom fields for different doc types
- ✅ **Programmable** - full CRUD via API

**Comparison**:
| Feature | Document Upload | Flexible Assets |
|---------|----------------|-----------------|
| Stores files | ✅ Binary attachments | ❌ Content only |
| Searchable in ITGlue | ❌ No | ✅ Yes |
| Native ITGlue format | ❌ No | ✅ Yes |
| Requires download | ✅ Yes | ❌ No (view inline) |
| **Use case** | Reference files, PDFs | Operational docs, SOPs |

### Create Password
```python
password = client.create_password(
    organization_id='4489414129010794',
    name='Admin Password',
    username='admin',
    password='SuperSecret123!'
)
print(f"Created password: {password.id}")
```

### Link Configuration to Password
```python
success = client.link_configuration_to_password(
    configuration_id='CONFIG_ID',
    password_id='PASSWORD_ID'
)
print(f"Linked: {success}")
```

---

## 🌏 Regional Setup

### Australian Region (Your Instance)
```python
client = ITGlueClient(
    instance='sandbox',  # or 'production'
    base_url='https://api.au.itglue.com'
)
```

### US Region
```python
client = ITGlueClient(
    instance='production',
    base_url='https://api.itglue.com'
)
```

### EU Region
```python
client = ITGlueClient(
    instance='production',
    base_url='https://api.eu.itglue.com'
)
```

---

## 💾 Cache Usage

### Smart Query (Cache-First)
```python
# Try cache first, fall back to API
org = client.cache.smart_get_organization(
    org_id='4489414129010794',
    api_client=client
)
```

### Cache Statistics
```python
stats = client.cache.get_statistics()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Organizations: {stats['organization_count']}")
print(f"Cache size: {stats['cache_size_mb']:.2f} MB")
```

### Refresh Cache
```python
orgs = client.list_organizations()  # Fetches from API
client.cache.refresh_organizations(orgs)  # Updates cache
```

---

## 📊 Monitoring

### Health Check
```python
health = client.health_check()
print(health)
# {
#   'status': 'healthy',
#   'api_key_valid': True,
#   'response_time_ms': 250,
#   'circuit_breaker': {...},
#   'rate_limiter': {...}
# }
```

### Metrics (RED)
```python
metrics = client.get_metrics()
print(f"Requests: {metrics['request_count']}")
print(f"Errors: {metrics['error_count']}")
print(f"Avg Latency: {metrics['request_duration_ms']:.0f}ms")
print(f"Error Rate: {metrics['error_rate']:.1%}")
```

### Rate Limiter Status
```python
rate_stats = client.rate_limiter.get_stats()
print(f"Usage: {rate_stats['current_requests']}/{rate_stats['max_requests']}")
print(f"Utilization: {rate_stats['utilization_percent']:.1f}%")
```

---

## 🔧 Advanced Usage

### Batch Operations
```python
# Create multiple configurations
configs_to_create = [
    {'name': 'Web Server 01', 'type': 'Server'},
    {'name': 'Web Server 02', 'type': 'Server'},
    {'name': 'Database Server', 'type': 'Server'},
]

for config_data in configs_to_create:
    config = client.create_configuration(
        organization_id='YOUR_ORG_ID',
        name=config_data['name'],
        configuration_type=config_data['type']
    )
    print(f"Created: {config.name}")
```

### Search Organizations
```python
# Search by name
results = client.search_organizations(name='Acme')
for org in results:
    print(f"Found: {org.name}")
```

### Download Document
```python
success = client.download_document(
    document_id='DOC_ID',
    output_path='/tmp/downloaded_file.pdf'
)
print(f"Downloaded: {success}")
```

---

## 🚨 Error Handling

```python
from claude.tools.integrations.itglue.exceptions import (
    ITGlueAuthError,
    ITGlueRateLimitError,
    ITGlueNotFoundError,
    ITGlueAPIError
)

try:
    orgs = client.list_organizations()
except ITGlueAuthError:
    print("API key invalid or expired")
except ITGlueRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after_seconds}s")
except ITGlueNotFoundError as e:
    print(f"Not found: {e.resource_type} {e.resource_id}")
except ITGlueAPIError as e:
    print(f"API error: {e}")
```

---

## 📖 Example Workflows

### Workflow 1: Onboard New Client
```python
# 1. Create organization
org = client.create_organization(name='New Client Co')

# 2. Create server configuration
server = client.create_configuration(
    organization_id=org.id,
    name='Primary Server',
    configuration_type='Server',
    serial_number='SN-12345'
)

# 3. Create admin password
password = client.create_password(
    organization_id=org.id,
    name='Server Admin Password',
    username='administrator',
    password='TempPassword123!'
)

# 4. Link server to password
client.link_configuration_to_password(server.id, password.id)

# 5. Upload network diagram
doc = client.upload_document(
    organization_id=org.id,
    file_path='/path/to/diagram.pdf',
    name='Network Diagram.pdf'
)

print(f"✅ Onboarded {org.name}")
```

### Workflow 2: Audit All Organizations
```python
# List all organizations
orgs = client.list_organizations()

print(f"📊 ITGlue Audit Report")
print(f"Total Organizations: {len(orgs)}")
print()

for org in orgs:
    # Count assets
    configs = client.list_configurations(org.id)
    docs = client.list_documents(org.id)
    passwords = client.list_passwords(org.id)

    print(f"{org.name}:")
    print(f"  Configurations: {len(configs)}")
    print(f"  Documents: {len(docs)}")
    print(f"  Passwords: {len(passwords)}")
    print()
```

---

## ⚠️ API Limitations

ITGlue's API has some quirks with document operations:

### Document Operations with API Key Auth
✅ **Works**: `POST /documents` - Create document
✅ **Works**: `POST /documents/:id/relationships/attachments` - Attach files
❌ **Doesn't Work**: `GET /documents` - No listing endpoint
❌ **Doesn't Work**: `GET /documents/:id` - Requires JWT auth (not API key)

### Workarounds
- **Document Upload**: Use `client.upload_document()` - creates document + attaches file in one call
- **Document Tracking**: Keep document IDs from creation responses (no listing available)
- **Flexible Assets**: Consider using Flexible Assets for documentation that needs to be queried

### What This Means
You can create and upload documents via API, but can't list or retrieve them with API key authentication. Documents are viewable in ITGlue UI via the returned `resource-url`.

---

## 🔐 Security Best Practices

1. **API Key Storage**: Always use macOS Keychain (never hardcode)
2. **Password Logging**: Client automatically redacts passwords from logs
3. **HTTPS Only**: Client enforces HTTPS (rejects HTTP URLs)
4. **Key Rotation**: Rotate API keys every 90 days
5. **Least Privilege**: Use read-only keys for queries, read/write for operations

---

## 🐛 Troubleshooting

### Problem: 401 Unauthorized
**Solution**: Check API key is active in ITGlue portal

### Problem: Rate limit errors
**Solution**: Client auto-retries. Check rate limiter stats if persists

### Problem: Circuit breaker open
**Solution**: Wait 60 seconds or reset: `client.circuit_breaker.reset()`

### Problem: Cache stale data
**Solution**: `client.cache.refresh_organizations(client.list_organizations())`

---

## 📚 Full Documentation

- **Requirements**: `claude/data/project_status/active/itglue_api_tools_requirements.md`
- **Architecture**: `claude/tools/integrations/itglue/ARCHITECTURE.md`
- **API Docs**: https://api.itglue.com/developer/

---

**Your Setup**:
- ✅ Region: Australian (AU)
- ✅ Base URL: `https://api.au.itglue.com`
- ✅ Organization: NDawe Sandbox2 (ID: 4489414129010794)
- ✅ API Key: Stored in Keychain
- ✅ All systems operational!

**Ready to use!** 🚀
