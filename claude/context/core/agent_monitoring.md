# Agent Monitoring System

## Overview
Real-time monitoring system for tracking active Maia agents, processes, and system activity to prevent conflicts and optimize resource usage.

## Architecture

### Components
```
Agent Monitoring System
├── Status Tracker         # Maintains agent state information
├── Process Monitor         # Detects active system processes
├── Conflict Detector       # Identifies potential resource conflicts
├── Activity Logger         # Records agent activity history
└── Dashboard Interface     # Real-time status display
```

### Status File Structure
```
/claude/status/
├── agent_states.json      # Current agent status
├── process_registry.json  # Active processes
├── resource_locks.json    # File/resource locks
├── activity_log.json      # Historical activity
└── system_health.json     # Overall system status
```

## Agent State Management

### Agent Status Schema
```json
{
  "agent_name": {
    "status": "idle|processing|error|unknown",
    "task": "current_task_description",
    "started_at": "2025-09-06T09:15:00Z",
    "last_heartbeat": "2025-09-06T09:16:30Z",
    "pid": 12345,
    "resource_usage": {
      "cpu_percent": 15.2,
      "memory_mb": 128,
      "files_open": 5
    },
    "current_files": ["file1.json", "file2.md"],
    "estimated_completion": "2025-09-06T09:20:00Z",
    "progress": 65
  }
}
```

### Supported Agents
- **Jobs Agent**: Job search automation and monitoring
- **LinkedIn Agent**: Profile optimization and networking
- **Email Agent**: Email processing and automation
- **Security Agent**: Security scans and assessments
- **Prompt Engineer**: Prompt optimization workflows
- **Research Agent**: Information gathering tasks
- **FOBs Engine**: Dynamic tool execution
- **Multi-Agent Commands**: Complex orchestrated workflows

## Monitoring Capabilities

### Real-Time Detection
1. **Process Monitoring**: Python processes with "maia" or agent names
2. **File System Watching**: Monitor key directories for agent activity
3. **Network Activity**: API calls and external service usage
4. **Resource Utilization**: CPU, memory, disk I/O per agent
5. **Heartbeat Tracking**: Regular status updates from active agents

### Conflict Prevention
1. **File Lock Management**: Prevent multiple agents accessing same files
2. **Resource Allocation**: Ensure agents don't exceed system limits
3. **Queue Management**: Serialize conflicting operations
4. **Priority Handling**: Important agents get resource priority

### Activity Logging
1. **Start/Stop Events**: Agent lifecycle tracking
2. **Task Progression**: Progress updates and milestones
3. **Error Reporting**: Failures and recovery actions
4. **Performance Metrics**: Execution times and efficiency

## Implementation Strategy

### Phase 1: Basic Status Tracking
- Agent registration and heartbeat system
- Process detection and monitoring
- Simple status file management
- Basic conflict detection

### Phase 2: Advanced Monitoring
- Resource usage tracking
- Detailed activity logging
- Performance analytics
- Automated conflict resolution

### Phase 3: Intelligence & Optimization
- Predictive conflict detection
- Resource optimization recommendations
- Agent performance analysis
- System health scoring

## Integration Points

### Agent Integration
All agents should implement:
```python
def register_agent_status(agent_name, task, estimated_duration):
    """Register agent as active"""
    pass

def update_agent_progress(agent_name, progress_percent, current_action):
    """Update agent progress"""
    pass

def unregister_agent_status(agent_name, completion_status):
    """Mark agent as completed"""
    pass
```

### System Integration
- **UFC Context**: Monitor context file access patterns
- **FOBs System**: Track dynamic tool execution
- **Advanced Commands**: Monitor multi-agent workflow progress
- **MCP Servers**: Track external service usage

## Monitoring Commands

### Status Check
```bash
agent_monitor status          # Show all agent status
agent_monitor status jobs     # Show specific agent
agent_monitor conflicts       # Show potential conflicts
agent_monitor resources       # Show resource usage
```

### Management
```bash
agent_monitor start monitoring    # Begin monitoring
agent_monitor stop monitoring     # Stop monitoring
agent_monitor clear locks         # Clear stuck locks
agent_monitor restart <agent>     # Restart specific agent
```

### Analytics
```bash
agent_monitor history             # Show activity history
agent_monitor performance        # Show performance metrics
agent_monitor health             # System health check
```

## User Interface

### Dashboard Display
```
🤖 MAIA AGENT MONITOR - 09:16:45
═══════════════════════════════════════

📊 SYSTEM STATUS: ✅ Healthy (3 agents active)

🔄 ACTIVE AGENTS:
  📧 Jobs Agent      [██████████████░░░░] 70% - Processing email notifications
     ├─ Task: Automated job scraper batch run
     ├─ Started: 09:14:22 (2m 23s ago)
     ├─ ETA: 09:17:45 (1m 22s remaining)
     └─ Files: job_monitor_config.json, pending_applications.csv

  🔗 LinkedIn Agent  [████████░░░░░░░░░░] 40% - Profile optimization
     ├─ Task: Keyword density analysis
     ├─ Started: 09:15:11 (1m 34s ago)
     └─ ETA: 09:20:00 (3m 37s remaining)

  🛠️  FOBs Engine     [██████████████████] 100% - Tool execution
     ├─ Task: professional_email_formatter
     ├─ Duration: 0.8s
     └─ Status: Completing

💾 RESOURCE USAGE:
  CPU: 23.5% | Memory: 512MB | Disk I/O: 2.3MB/s

⚠️  CONFLICTS: None detected

📝 RECENT ACTIVITY:
  09:16:32 - FOBs Engine: Executed url_summarizer successfully
  09:16:15 - Jobs Agent: Found 3 new opportunities in email batch
  09:15:58 - LinkedIn Agent: Updated profile keywords (15 changes)
```

### Alert System
```
🚨 CONFLICT DETECTED: Jobs Agent and LinkedIn Agent both accessing profile.json
💡 SUGGESTION: Queue operations or use file locking

⚡ HIGH RESOURCE USAGE: Jobs Agent using 78% CPU for 5+ minutes
💡 SUGGESTION: Consider reducing batch size or adding delays

🔄 AGENT TIMEOUT: Security Agent hasn't responded for 10 minutes
💡 SUGGESTION: Check for hung processes or restart agent
```

## Performance Metrics

### System Health Indicators
- **Agent Response Time**: <2s for status updates
- **Conflict Rate**: <5% of operations
- **System Availability**: >99% uptime
- **Resource Efficiency**: <30% average CPU usage

### Monitoring Overhead
- **Memory Usage**: <25MB for monitoring system
- **CPU Impact**: <2% additional load
- **Storage**: <10MB for logs and status files
- **Network**: Minimal (local file operations)

This system provides comprehensive visibility into agent activity while maintaining minimal overhead and preventing resource conflicts.