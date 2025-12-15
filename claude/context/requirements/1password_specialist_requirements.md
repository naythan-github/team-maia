# 1Password Specialist Agent - Requirements

## Purpose
Create a specialist agent for 1Password CLI operations, secrets management, and secure credential handling within Maia workflows.

## Core Requirements

### 1. Authentication & Session Management
- Handle `op signin` workflows
- Manage session tokens
- Support multiple accounts/vaults
- Detect authentication state

### 2. Secret Retrieval
- Get specific items by name/UUID
- Retrieve passwords, fields, documents
- Support vault-specific queries
- Handle item references (op://vault/item/field)

### 3. Vault Operations
- List available vaults
- Search across vaults
- Vault-scoped operations
- Team/shared vault support

### 4. Item Management
- Create new items (login, password, secure note, etc.)
- Update existing items
- Delete items (with confirmation)
- Add/update custom fields

### 5. Security Best Practices
- Never log credentials in plain text
- Secure environment variable injection
- Session token cleanup
- Minimal permission scopes

### 6. Integration Patterns
- Export to environment variables
- Config file injection
- Temporary credential usage
- Secret rotation workflows

## Technical Specifications

### Dependencies
- 1Password CLI (`op`) v2.0+
- Installation: `brew install 1password-cli` (macOS)
- Authentication: Service account tokens or user signin

### Common Operations

#### Authentication
```bash
# Interactive signin
op signin

# Using service account token
export OP_SERVICE_ACCOUNT_TOKEN="ops_..."
```

#### Retrieval
```bash
# Get password
op item get "Item Name" --fields password

# Get entire item as JSON
op item get "Item Name" --format json

# Get specific vault item
op item get "Item Name" --vault "Vault Name"
```

#### Search & List
```bash
# List all items
op item list

# List vaults
op vault list

# Search items
op item list --categories login --tags production
```

#### Create/Update
```bash
# Create login item
op item create --category login --title "New Login" \
  --vault "Personal" \
  username="user@example.com" \
  password="$(op generate password)"

# Update field
op item edit "Item Name" username="newuser@example.com"
```

## Success Criteria

### Functional
- ✅ Retrieve secrets programmatically
- ✅ Manage authentication state
- ✅ Create/update items
- ✅ Search and discover items
- ✅ Handle errors gracefully

### Security
- ✅ No credential logging
- ✅ Secure token handling
- ✅ Session cleanup
- ✅ Minimal exposure window

### Usability
- ✅ Clear examples in agent definition
- ✅ Common workflows documented
- ✅ Integration patterns provided
- ✅ Error troubleshooting guidance

## Agent Capabilities Structure

### Commands
- `authenticate` - Handle signin and session management
- `get_secret` - Retrieve specific credentials
- `list_items` - Search and discover items
- `create_item` - Add new secrets
- `update_item` - Modify existing items
- `inject_env` - Export to environment variables
- `rotate_secret` - Update and propagate credentials

### Example Workflows
1. **Secret retrieval for deployment** - Get DB credentials, inject to env, run deployment
2. **Credential rotation** - Generate new password, update 1Password, update target system
3. **Config injection** - Pull secrets, populate config template, deploy
4. **Audit & discovery** - List all production credentials, check last updated dates

## Integration Points

### Collaborations
- **Security Specialist Agent**: Credential rotation policies, security audits
- **Cloud Specialist Agent**: Secrets injection for cloud deployments
- **DevOps Agent**: CI/CD secrets management
- **SRE Agent**: Incident response credential access

### Handoff Scenarios
- Security audit needed → Security Specialist
- Cloud resource deployment → Cloud Specialist
- Secret rotation policy → Security Specialist

## Model Selection
- **Sonnet**: All standard operations (retrieve, create, update, list)
- **Opus**: Complex multi-vault migrations, enterprise policy design

## Notes
- CLI must be installed (`op --version`)
- Service account tokens recommended for automation
- Biometric unlock supported on macOS for interactive use
- API rate limits: ~10 requests/second per account
