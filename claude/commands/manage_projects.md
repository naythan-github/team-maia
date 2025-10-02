# Manage Projects Command

## Overview
Comprehensive project and task management with persistent storage and smart organization.

## Usage
```bash
maia manage_projects [command] [options]
```

## Available Commands

### Project Overview
- `summary` - Display project status overview and statistics
- `active` - List all active projects  
- `next` - Show next tasks to work on (top 5 by priority)
- `domains` - Show projects organized by domain

### Project Management
- `create <title> <domain>` - Create new project
- `activate <project_id>` - Move project to active status
- `complete <project_id>` - Mark project as completed
- `archive <project_id>` - Archive completed project

### Task Management  
- `tasks <project_id>` - List tasks for a project
- `add_task <project_id> <title>` - Add task to project
- `start_task <task_id>` - Mark task as active
- `finish_task <task_id>` - Complete a task

### Idea Capture
- `capture <idea_text>` - Capture idea for later processing
- `ideas` - List unprocessed ideas
- `process_idea <idea_id> <project_id>` - Convert idea to project/task

## Examples

### Basic Project Management
```bash
# Get overview of all projects
maia manage_projects summary

# See what to work on next
maia manage_projects next

# Create new engineering management project
maia manage_projects create "Team Performance Dashboard" engineering_management

# Capture quick idea
maia manage_projects capture "Build automated performance review system"
```

### Domain-Focused Work
```bash
# See all active engineering projects
maia manage_projects active engineering_management

# List Maia development projects
maia manage_projects active maia_development

# Show personal projects
maia manage_projects active personal
```

### Task Workflow
```bash
# Add tasks to a project
maia manage_projects add_task PROJECT_ID "Design database schema"
maia manage_projects add_task PROJECT_ID "Build REST API"
maia manage_projects add_task PROJECT_ID "Create dashboard UI"

# Start working on highest priority task
maia manage_projects start_task TASK_ID

# Complete task when done
maia manage_projects finish_task TASK_ID
```

## Domain Organization

### Engineering Management
- Team performance systems
- Cloud practice development  
- Orro Group integration projects
- Client engagement tools

### Maia Development
- Infrastructure improvements
- New agent development
- System optimizations
- Maia 2.0 planning

### Personal
- Financial planning
- Health and fitness
- Travel planning
- Learning goals

### Career
- Professional development
- Certification planning
- Network building
- Skill development

## Integration Features

### Automatic Idea Capture
- Detects recommendations from Maia conversations
- Auto-categorizes by domain based on keywords
- Smart priority assignment based on urgency indicators
- Converts TodoWrite items to persistent projects

### Context Preservation
- SQLite database survives context resets
- Project history and progress tracking
- Cross-session memory of priorities and status
- Integration with existing backlog management

### Smart Organization  
- Priority matrix (Impact vs Effort)
- Due date tracking and reminders
- Progress tracking (0-100%)
- Tag-based organization
- Hierarchical project structure

## CLI Quick Reference
```bash
# Daily workflow
maia manage_projects next           # What to work on
maia manage_projects capture "idea" # Quick idea logging
maia manage_projects summary        # Status check

# Project management
maia manage_projects active         # Current projects
maia manage_projects create "title" domain
maia manage_projects tasks PROJECT_ID

# Idea processing
maia manage_projects ideas          # Review captured ideas
maia manage_projects process_idea ID PROJECT_ID
```

This system provides persistent project management that works across context resets while integrating with Maia's existing automation capabilities.