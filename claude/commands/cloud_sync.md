# Cloud Sync Command

Maia cross-system improvement sharing via iCloud Drive.

## Overview
Enable safe bidirectional sharing of Maia improvements between personal and work systems while maintaining security boundaries and automatic sanitization.

## Usage

### Export Improvement to Cloud
Export a tool, agent, command, or MCP for sharing with other systems:

```bash
# Export tool for work system
python3 claude/tools/cloud_sync_manager.py export \
  --improvement <tool_name> \
  --type tool \
  --target-system work \
  --sanitize-level work-safe

# Export agent for any system  
python3 claude/tools/cloud_sync_manager.py export \
  --improvement <agent_name> \
  --type agent \
  --target-system any \
  --sanitize-level work-safe

# Export command
python3 claude/tools/cloud_sync_manager.py export \
  --improvement <command_name> \
  --type command \
  --target-system work
```

### Check for Available Improvements
Check what improvements are available for import:

```bash
# Check as personal system
python3 claude/tools/cloud_sync_manager.py check

# Check as work system  
python3 claude/tools/cloud_sync_manager.py --system-id work check
```

### Import Improvement from Cloud
Import an improvement package from cloud sync:

```bash
# Import with verification (recommended)
python3 claude/tools/cloud_sync_manager.py import \
  --package <package_name.zip> \
  --verify

# Import without verification (if compatibility issues need override)
python3 claude/tools/cloud_sync_manager.py import \
  --package <package_name.zip> \
  --no-verify
```

### System Status
Check cloud sync system status:

```bash
python3 claude/tools/cloud_sync_manager.py status
```

## Improvement Types

### Tools (`--type tool`)
- Python tools from `claude/tools/`
- Related test files and documentation
- Automatic sanitization of personal paths and credentials

### Agents (`--type agent`) 
- Agent definitions from `claude/agents/`
- Agent-specific configurations and capabilities

### Commands (`--type command`)
- Command workflows from `claude/commands/`
- Multi-agent orchestration patterns

### MCP Servers (`--type mcp`)
- Complete MCP server implementations
- Dependencies and configuration files

## Sanitization Levels

### Work-Safe (`--sanitize-level work-safe`)
- Remove personal paths and credentials
- Replace with environment variables
- Remove personal context references
- Safe for corporate environments

### Personal-Safe (`--sanitize-level personal-safe`)
- Remove company-confidential information
- Minimal sanitization for personal use

## Cloud Drive Structure

```
iCloud Drive/Maia-Sync/
├── packages/
│   ├── personal-to-work/    # Personal → Work transfers
│   └── work-to-personal/    # Work → Personal transfers
├── improvements/
│   ├── pending/             # Awaiting review
│   ├── approved/            # Ready for installation
│   └── installed/           # Successfully applied
├── metadata/
│   ├── sync_log.json       # Transfer history
│   └── system_states.json   # System status tracking
└── templates/               # Reusable templates
```

## Security Features

- **Automatic Sanitization**: Removes sensitive information based on target system
- **Verification Checks**: Compatibility verification before import
- **File Integrity**: SHA256 checksums for all transferred files
- **Conflict Detection**: Prevents overwriting existing files without warning
- **Audit Trail**: Complete logging of all sync operations

## Example Workflow

### Personal System (Development)
1. Create new improvement (tool, agent, command)
2. Export for work system:
   ```bash
   python3 claude/tools/cloud_sync_manager.py export \
     --improvement new_analyzer_tool \
     --type tool \
     --target-system work \
     --sanitize-level work-safe
   ```

### Work System (Deployment)
1. Check for improvements:
   ```bash
   python3 claude/tools/cloud_sync_manager.py --system-id work check
   ```
2. Import improvement:
   ```bash
   python3 claude/tools/cloud_sync_manager.py --system-id work import \
     --package new_analyzer_tool_v20250917_191429.zip \
     --verify
   ```

## Benefits

- **Cross-System Evolution**: Both systems benefit from improvements made on either
- **Security Compliance**: Automatic sanitization maintains corporate security boundaries  
- **Version Control**: Packages include metadata for tracking and rollback
- **Conflict Prevention**: Verification prevents system corruption
- **Audit Ready**: Complete logging for compliance and debugging
- **Zero Setup**: Uses existing iCloud Drive infrastructure

## Troubleshooting

### Package Not Found
- Check iCloud Drive sync status
- Verify package name spelling
- Ensure correct system-id parameter

### Import Conflicts
- Review verification errors
- Use `--no-verify` only if safe to override
- Check for existing file versions

### Path Issues
- Verify MAIA_ROOT environment variable
- Check that CLAUDE.md exists in root directory
- Ensure script is run from correct location

This system enables seamless knowledge sharing between your personal and work Maia systems while maintaining appropriate security boundaries.