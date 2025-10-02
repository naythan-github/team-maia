# Manage Backlog Command

**Purpose**: Interactive management of Maia's recommendation and todo backlog
**Category**: Productivity & Planning
**Usage**: Session planning, task prioritization, progress tracking

## Command Overview

This command provides comprehensive management of Maia's persistent backlog system, allowing you to review, organize, and act on accumulated recommendations and todos from previous sessions.

## Parameters

- `action`: The backlog management action to perform
  - `summary` - Display backlog overview and statistics
  - `export` - Export backlog to markdown for review
  - `review` - Interactive review of pending items
  - `complete` - Mark items as completed
  - `prioritize` - Adjust item priorities
  - `clean` - Remove outdated or duplicate items

- `category` (optional): Filter by category (security, mcp, agents, deployment, etc.)
- `priority` (optional): Filter by priority (high, medium, low)
- `limit` (optional): Limit number of items to display/process

## Execution Steps

### 1. Initialize Backlog Manager
```python
from claude.tools.backlog_manager import get_backlog_manager
manager = get_backlog_manager()
```

### 2. Execute Action

#### Summary Action
- Load current backlog state
- Calculate statistics by category and priority
- Display formatted summary with key metrics
- Highlight high-priority and overdue items

#### Export Action
- Generate comprehensive markdown report
- Include all active items with full context
- Organize by category and priority
- Save to dated export file

#### Review Action
- Present items interactively for user decision
- Show item details, context, and creation date
- Allow updating priority, category, or completion status
- Track review progress and decisions

#### Complete Action
- Mark specified items as completed
- Move to completed items archive
- Add completion notes and timestamp
- Update backlog statistics

### 3. Display Results
- Show action outcome and statistics
- Provide recommendations for next steps
- Highlight any items requiring attention
- Update session context with backlog state

## Integration Points

### Auto-Capture System
- Hooks automatically capture recommendations from Maia outputs
- Natural language processing identifies actionable items
- Context detection categorizes and prioritizes automatically

### Session Planning
- Review backlog at session start for context
- Identify high-priority items for immediate action
- Plan session activities based on accumulated recommendations

### Progress Tracking
- Track completion rates by category
- Monitor recommendation patterns over time
- Identify recurring themes requiring systematic solutions

## Output Format

### Summary Format
```markdown
# Maia Backlog Summary
**Total Active Items**: 23
**High Priority**: 5 items
**Categories**: security (8), mcp (6), agents (4), deployment (3), system (2)

## Recent High Priority Items
- 🔴 Conduct comprehensive macOS security audit (ID: a1b2c3d4)
- 🔴 Implement automated backup system (ID: e5f6g7h8)

## Category Breakdown
**Security** (8 items): vulnerability monitoring, system hardening, audit tasks
**MCP** (6 items): server deployment, integration testing, documentation
```

### Export Format
- Comprehensive markdown with full item details
- Organized sections by category and priority
- Includes creation dates, context, and effort estimates
- Suitable for offline review and planning

## Usage Examples

```bash
# Get backlog overview
maia manage_backlog summary

# Review high-priority security items
maia manage_backlog review category=security priority=high

# Export full backlog for offline review
maia manage_backlog export

# Mark specific items as completed
maia manage_backlog complete item_ids=a1b2c3d4,e5f6g7h8

# Clean outdated items
maia manage_backlog clean older_than=30days
```

## Benefits

1. **Never Lose Ideas**: Automatic capture of all Maia recommendations
2. **Systematic Planning**: Organized approach to acting on suggestions  
3. **Progress Visibility**: Clear tracking of implementation progress
4. **Context Preservation**: Full context maintained across sessions
5. **Priority Management**: Dynamic prioritization based on changing needs

## Implementation Notes

- Backlog persisted in `/claude/context/backlog/` directory
- JSON format for programmatic access
- Markdown exports for human review
- Integration with existing TodoWrite system
- Hooks capture recommendations automatically during sessions

This command transforms Maia from reactive assistance to proactive productivity partnership by ensuring every valuable recommendation is captured, organized, and actionable.
