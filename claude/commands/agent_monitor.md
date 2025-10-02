# Agent Monitor Command

## Purpose
Real-time monitoring and management of Maia agents, processes, and system resources with conflict detection and performance analytics.

## Usage
```
agent_monitor <command> [options]
```

## Commands

### Status Display
```bash
agent_monitor status          # Compact status display
agent_monitor status detailed # Full dashboard view
agent_monitor status minimal  # Essential info only
```

### Process Management
```bash
agent_monitor scan           # Scan for Maia-related processes
agent_monitor conflicts      # Detect resource conflicts
agent_monitor health         # System health check
```

### Agent Registration (For Agent Scripts)
```bash
agent_monitor register <agent_name> <task> [duration]
agent_monitor update <agent_name> <progress> <action>
agent_monitor unregister <agent_name> [status]
```

## Implementation
```python
# Direct execution
python3 claude/tools/agent_monitor.py status detailed

# Via FOBs system
fob_system.execute("agent_status_monitor", format="detailed", command="status")
```

## Dashboard Output Examples

### Compact Format
```
🤖 MAIA MONITOR | ✅ HEALTHY | 2 agents active | CPU: 15.3% | Conflicts: 0
```

### Detailed Format
```
╭─ 🤖 MAIA AGENT MONITOR - 14:25:30 ────────────────────────────────────────╮
│                                                                      │
│ 📊 SYSTEM STATUS: ✅ HEALTHY (2 agents active)                       │
│                                                                      │
│ 🔄 ACTIVE AGENTS:                                                   │
│  📧 jobs_agent   [██████████████░░░░] 70% - Processing email batch    │
│     ├─ Runtime: 0:02:15  CPU: 12.4%                                │
│                                                                      │
│  🔗 linkedin_agt [████████░░░░░░░░░░] 40% - Profile optimization     │
│     ├─ Runtime: 0:01:45  CPU:  3.1%                                │
│                                                                      │
│ 💾 RESOURCE USAGE:                                                  │
│  CPU: 15.3% | Memory: 28.7% | Disk: 12.1%                         │
│                                                                      │
│ ⚠️  CONFLICTS: None detected                                        │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

## Integration Points
- **UFC System**: Monitors context file access patterns
- **FOBs Engine**: Tracks dynamic tool execution
- **Multi-Agent Commands**: Monitors orchestrated workflows
- **MCP Servers**: Tracks external service usage
- **Hook System**: Integrates with enforcement monitoring

## Agent Integration Template
```python
# For agents to self-register
from claude.tools.agent_monitor import AgentMonitor

monitor = AgentMonitor()

# At start
monitor.register_agent_status("my_agent", "Processing task", estimated_duration=300)

# During execution
monitor.update_agent_progress("my_agent", 50, "Halfway through processing")

# At completion
monitor.unregister_agent_status("my_agent", "completed")
```

## File System Structure
```
claude/status/
├── agent_states.json      # Active agent status
├── process_registry.json  # Process information
├── resource_locks.json    # File/resource locks
├── activity_log.json      # Historical activity
└── system_health.json     # Overall health metrics
```

## Performance Monitoring
- **Response Time**: <1s for status checks
- **Resource Overhead**: <2% CPU, <25MB memory
- **Update Frequency**: 30-second intervals
- **Conflict Detection**: Real-time file lock monitoring

## Advanced Features
- **Predictive Conflict Detection**: Warns before resource conflicts
- **Agent Performance Analytics**: Historical performance metrics
- **Automated Conflict Resolution**: Basic lock cleanup and queue management
- **System Health Scoring**: Comprehensive health indicators

This command provides comprehensive visibility into agent activity while maintaining minimal system overhead and preventing resource conflicts.