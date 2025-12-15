# Bitwarden Specialist Agent - Requirements

## Purpose
Create a specialist agent for Bitwarden CLI operations, secrets management, and credential handling with emphasis on open-source, self-hosted, and organization-focused workflows.

## Core Requirements

### 1. Authentication & Session Management
- Handle `bw login` and `bw unlock` workflows
- Manage `BW_SESSION` environment variable
- Support cloud and self-hosted servers (`--server` flag)
- Detect authentication/session state
- Logout security best practices

### 2. Secret Retrieval
- Get specific items by name/UUID
- Retrieve passwords, fields, notes, cards, identities
- JSON output parsing (designed for jq integration)
- Template-based retrieval (`bw get template`)
- Organization-scoped queries

### 3. Organization & Collection Management
- List organizations
- List and create collections
- Move items to organizations
- Share items via collections
- Confirm invited members
- Organization exports

### 4. Item Management
- Create new items (login, card, identity, secure note)
- Update existing items
- Delete items (with confirmation)
- Edit custom fields and attachments
- Template-based creation

### 5. Self-Hosted Deployment Support
- Connect to self-hosted instances
- Environment variable configuration
- Backup/export workflows
- Multi-instance management (cloud + self-hosted)

### 6. Advanced Features
- **Send**: Temporary secret sharing (ephemeral links)
- **Secrets Manager**: DevOps/CI-CD secrets (separate product)
- **Generate**: Secure password/passphrase generation
- **Attach**: File attachments to items

### 7. Security Best Practices
- Never log credentials in plain text
- Secure `BW_SESSION` handling and cleanup
- Use `--nointeraction` for automation
- Validate JSON output before parsing
- Lock vault after operations (`bw lock`)

### 8. Integration Patterns
- Export to environment variables
- JSON parsing with jq
- CI/CD pipeline integration
- Backup automation (cloud + self-hosted)
- Secret rotation workflows

## Technical Specifications

### Dependencies
- Bitwarden CLI (`bw`) v2023.9.0+
- Installation: `npm install -g @bitwarden/cli` or platform packages
- Optional: `jq` for JSON parsing
- Authentication: Username/password, API key, or SSO

### Common Operations

#### Authentication
```bash
# Cloud login
bw login

# Self-hosted login
bw config server https://vault.example.com
bw login

# Unlock (after login)
export BW_SESSION=$(bw unlock --raw)

# Check status
bw status
```

#### Retrieval
```bash
# Get password
bw get password "Item Name"

# Get entire item as JSON
bw get item "Item Name"

# Get with jq parsing
bw get item "Item Name" | jq -r '.login.password'

# List all items
bw list items

# Search items
bw list items --search "production"
```

#### Organizations & Collections
```bash
# List organizations
bw list organizations

# List collections
bw list collections --organizationid <org-id>

# Move item to organization
bw move <item-id> <org-id>

# Confirm member
bw confirm org <org-id> <member-id>
```

#### Create/Update
```bash
# Get creation template
bw get template item

# Create login item
echo '{"type":1,"name":"New Login","login":{"username":"user@example.com","password":"secret"}}' | bw encode | bw create item

# Edit item
bw edit item <item-id>

# Generate password
bw generate --length 20 --special
```

#### Self-Hosted Operations
```bash
# Configure self-hosted server
bw config server https://vault.company.com

# Export for backup
bw export --output backup.json --format json

# Sync vault
bw sync
```

#### Send (Temporary Sharing)
```bash
# Create text send
bw send create "Secret message"

# Create file send
bw send create --file document.pdf

# List sends
bw send list
```

## Success Criteria

### Functional
- ✅ Retrieve secrets programmatically
- ✅ Manage authentication state (cloud + self-hosted)
- ✅ Create/update items via templates
- ✅ Manage organizations and collections
- ✅ Handle self-hosted instances
- ✅ Create and manage Sends
- ✅ Handle errors gracefully

### Security
- ✅ No credential logging
- ✅ Secure `BW_SESSION` handling
- ✅ Automatic vault locking
- ✅ Minimal exposure window

### Usability
- ✅ Clear examples in agent definition
- ✅ Common workflows documented
- ✅ jq integration patterns
- ✅ Self-hosted deployment guidance
- ✅ Error troubleshooting

## Agent Capabilities Structure

### Commands
- `authenticate` - Handle login/unlock and session management
- `get_secret` - Retrieve specific credentials with jq parsing
- `list_items` - Search and discover items
- `create_item` - Add new secrets via templates
- `update_item` - Modify existing items
- `manage_org` - Organization and collection operations
- `send_secret` - Create temporary Send links
- `self_host_ops` - Self-hosted instance operations
- `rotate_secret` - Update and propagate credentials

### Example Workflows
1. **Self-hosted deployment** - Configure server, login, sync, export backup
2. **Organization secret sharing** - Create item, move to org, share via collection
3. **CI/CD integration** - Unlock vault, retrieve secrets, inject to env, lock vault
4. **Temporary secret sharing** - Create Send with expiration, share link
5. **Multi-instance management** - Switch between cloud and self-hosted vaults

## Key Differences from 1Password

| Feature | Bitwarden | 1Password |
|---------|-----------|-----------|
| **Open Source** | ✅ Yes (auditable) | ❌ No (proprietary) |
| **Self-Hosted** | ✅ Full support | ❌ Cloud-only |
| **CLI Command** | `bw` | `op` |
| **Session Mgmt** | `BW_SESSION` env var | Session tokens |
| **Organizations** | Collections-based | Vault-based |
| **Output Format** | JSON (jq-friendly) | JSON + table formats |
| **Temporary Sharing** | Send feature | Share links |
| **Secrets Manager** | Separate product | Enterprise feature |
| **Cost** | Free self-hosted | Paid service |

## Integration Points

### Collaborations
- **Security Specialist Agent**: Credential rotation policies, security audits, self-hosted security
- **Cloud Specialist Agent**: Self-hosted infrastructure deployment (Docker, Kubernetes)
- **DevOps Agent**: CI/CD secrets management, Secrets Manager integration
- **SRE Agent**: Backup automation, disaster recovery, incident response

### Handoff Scenarios
- Self-hosted infrastructure → Cloud Specialist
- Security audit needed → Security Specialist
- CI/CD pipeline design → DevOps Agent
- Disaster recovery → SRE Agent

## Model Selection
- **Sonnet**: All standard operations (retrieve, create, update, list, Send)
- **Opus**: Enterprise self-hosted migrations, complex organization policy design, multi-instance orchestration

## Notes
- CLI installation: `npm install -g @bitwarden/cli` (Node.js required)
- Self-hosted: Docker Compose recommended for deployment
- API rate limits: Cloud instances have rate limiting, self-hosted configurable
- Send feature: Requires premium or organization subscription
- Secrets Manager: Separate CLI (`bws`) for machine secrets
- Attachments: Premium feature for files >100MB
- jq highly recommended for JSON parsing workflows
