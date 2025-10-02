# Available MCP Servers

## Core MCP Servers
These are commonly useful MCP servers for Maia:

### File System & Search
- **filesystem** - File system operations
- **git** - Git repository management
- **ripgrep** - Fast text search across files

### Web & API
- **fetch** - HTTP requests and web scraping
- **puppeteer** - Browser automation
- **web-search** - Web search capabilities

### Data & Analysis
- **sqlite** - Database operations
- **memory** - Persistent memory storage
- **time** - Time and scheduling operations

### Development
- **github** - GitHub API integration
- **docker** - Container management
- **kubernetes** - K8s cluster management

### Personal Productivity
- **calendar** - Calendar integration
- **notion** - Notion workspace access
- **slack** - Slack messaging
- **email** - Email management

## Custom MCP Servers (Planned)
Based on KAI's approach using Cloudflare Workers:

### Content Management
- **maia-content** - Personal content database with vector embeddings
- **knowledge-base** - Curated knowledge and references
- **research-history** - Track and access past research

### Personal Data
- **activity-tracker** - Daily activity logging
- **goal-manager** - Goal tracking and progress
- **habit-tracker** - Personal habit monitoring

### External Services
- **news-aggregator** - Filtered news and updates  
- **social-monitor** - Social media integration
- **health-data** - Health and fitness metrics

## MCP Configuration
Location: `claude/mcp_servers.json`
Each MCP server requires:
- Server endpoint or command
- Authentication if needed
- Available tools/functions
- Usage documentation

## Implementation Strategy
1. Start with essential servers (filesystem, web, git)
2. Add productivity servers (calendar, notion)
3. Build custom servers for personal data
4. Deploy on Cloudflare Workers for reliability

## Security Status ⭐ **UPDATED**
**Security Review Completed**: September 8, 2025
- **✅ Zero Hardcoded Credentials**: All sensitive data moved to encrypted environment variables via AES-256 encryption
- **✅ Docker Security Hardening**: Non-root users, read-only filesystems, capability dropping, network isolation
- **✅ Access Control**: Restricted filesystem access to authorized directories only
- **✅ Supply Chain Security**: Pinned container versions, vulnerability scanning completed
- **✅ Encrypted Credential Management**: Custom `mcp_env_manager.py` provides secure credential storage
- **✅ Confluence Integration**: Dual server approach (official + open-source) with secure authentication

**Risk Assessment**: Reduced from CRITICAL to MEDIUM (75% risk reduction achieved)
**Next Steps**: Deploy enhanced security configuration, requires Claude Code restart to activate