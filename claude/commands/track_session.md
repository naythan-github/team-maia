# Session Tracking Command

## Overview
Track operational metrics and performance data for VS Code vs Cursor comparison analysis.

## Usage

### Start Tracking Session
```bash
# Start VS Code baseline tracking
python3 claude/tools/session_tracker.py start vscode

# Start Cursor comparison tracking  
python3 claude/tools/session_tracker.py start cursor
```

### Manual Event Tracking
```bash
# Track context reload
python3 claude/hooks/track_context_loads.py

# Get current session stats
python3 claude/tools/session_tracker.py stats

# End current session
python3 claude/tools/session_tracker.py end
```

### Integration with Workflows
```python
# In Python tools/scripts
from session_tracker import get_session_tracker
tracker = get_session_tracker()

# Track file operations
tracker.track_file_operation("read", "agents.md", duration_ms=150)

# Track tool execution  
tracker.track_tool_execution("strategic_project_manager", duration_ms=2500, success=True)

# Track user interactions
tracker.track_user_interaction("complex_analysis", duration_ms=30000, estimated_tokens=5000)
```

## Tracked Metrics

### Context Operations
- **Context Load Events**: Full 8-file context reloads
- **Reload Frequency**: How often context needs refreshing
- **Load Time**: Duration of context loading operations
- **Token Overhead**: Estimated tokens consumed by context

### File Operations  
- **Read/Write Operations**: File system interactions
- **Operation Duration**: Time spent on file operations
- **Success Rates**: Operation completion rates

### Tool Execution
- **Tool Invocation**: Python script and command execution
- **Execution Time**: Duration of tool operations
- **Success/Failure Rates**: Tool reliability metrics

### User Interactions
- **Response Generation**: Time to complete user requests
- **Token Consumption**: Estimated token usage per interaction
- **Task Complexity**: Classification of request types

## Baseline Establishment (VS Code)

### Current Session Tracking
Run these commands throughout your current VS Code session:

```bash
# At start of each major task
python3 claude/hooks/track_context_loads.py

# After file operations
# (Manual logging until automated)

# At end of session
python3 claude/tools/session_tracker.py stats
python3 claude/tools/session_tracker.py end
```

### Key Metrics to Establish
- **Context Reload Frequency**: How often you need full context refresh
- **Task Completion Time**: Duration for complex tasks (like building project manager)
- **Token Efficiency**: Estimated token consumption patterns
- **Error/Retry Rates**: How often operations need repeating

## Cursor Comparison (Post-Migration)

### Day 1 in Cursor
```bash
# Start fresh tracking
python3 claude/tools/session_tracker.py start cursor

# Track same types of operations
# Compare efficiency metrics
```

### Comparison Analysis
```bash
# Generate comparison report
python3 claude/tools/operations_tracker.py compare

# View baseline vs current
python3 claude/tools/session_tracker.py stats
```

## Expected Improvements to Track

### Context Efficiency
- **Reduced Reloads**: Cursor's project awareness may reduce context reload needs
- **Faster Context**: Multi-file awareness vs sequential loading
- **Better Context Retention**: Less forgetting of project structure

### Task Efficiency  
- **Multi-file Operations**: Simultaneous editing across agents/tools
- **Integrated Terminal**: Direct tool execution within IDE
- **Better Navigation**: Project tree and file relationship understanding

### Development Workflow
- **Composer Mode**: Multi-file changes in single operation
- **Better Debugging**: Integrated tool execution and testing
- **Reduced Switching**: Less context switching between tools

## Success Metrics

### Quantitative
- **20%+ reduction** in context reload frequency
- **30%+ faster** multi-file operations
- **15%+ fewer** total operations needed
- **25%+ token efficiency** improvement

### Qualitative  
- **Smoother workflow** for complex projects
- **Better understanding** of project relationships
- **Reduced cognitive overhead** from context management
- **Improved development velocity** for Maia enhancements

This tracking system provides objective data for the VS Code → Cursor migration decision.