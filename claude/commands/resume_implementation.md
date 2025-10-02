# Resume Implementation - Universal Recovery Command

## Overview
Universal command for resuming any implementation after context loss or session reset.

## Usage
```bash
# List all implementations
python3 claude/tools/📊_data/universal_implementation_tracker.py list

# Get status of specific implementation
python3 claude/tools/📊_data/universal_implementation_tracker.py status <project_name>

# Get full recovery context
python3 claude/tools/📊_data/universal_implementation_tracker.py recovery <project_name>

# Resume specific implementation (auto-generated command)
# Use: claude/commands/implementations/resume_<project_name>.md
```

## Quick Recovery Protocol

### Step 1: Identify Implementation
```bash
# List active implementations
python3 claude/tools/📊_data/universal_implementation_tracker.py list in_progress
```

### Step 2: Get Implementation Context
```bash
# Get current status and next actions
python3 claude/tools/📊_data/universal_implementation_tracker.py status <project_name>
```

### Step 3: Load Research Context
- Read research file: `claude/context/implementations/<project>_research.md`
- Read implementation tracker: `claude/context/implementations/<project>_implementation.md`

### Step 4: Resume Implementation
- Follow next_actions from latest checkpoint
- Update implementation tracker after each session
- Save new checkpoints regularly

## Implementation-Specific Commands

Each implementation gets its own recovery command:
- `claude/commands/implementations/resume_<project>.md`
- Tailored recovery instructions for specific project
- Direct file paths and project-specific context

## Universal System Features

### Automatic Template Generation
When creating new implementation tracking:
```bash
python3 claude/tools/📊_data/universal_implementation_tracker.py create \
  "Project Name" "project_type" "priority" "Description of project"
```

This automatically creates:
- Research findings template
- Implementation tracker template  
- Project-specific recovery command
- Database entries for checkpoint tracking

### Checkpoint System
Save implementation progress:
```bash
python3 claude/tools/📊_data/universal_implementation_tracker.py checkpoint \
  "Project Name" "phase" "step" "status" "Optional notes"
```

### Context Preservation
- **SQLite Database**: Persistent implementation tracking across sessions
- **File Templates**: Standardized research and implementation documentation
- **Recovery Commands**: Automated generation of project-specific recovery procedures
- **Git Integration**: All implementation files committed with save_state command

## Implementation Status Meanings

- **not_started**: Implementation ready but not begun
- **in_progress**: Active implementation with checkpoints
- **completed**: Implementation finished successfully
- **blocked**: Implementation stopped due to dependencies/issues

## Integration with Existing Systems

### Save State Command
- Enhanced save_state now preserves all implementation contexts
- Automatic checkpoint saving during system state preservation
- Implementation continuity across context resets

### Knowledge Management System
- Implementation tracking integrates with existing project management
- Cross-session persistence through SQLite database
- Professional project organization and milestone tracking

### UFC System
- Implementation files organized under `claude/context/implementations/`
- Recovery commands under `claude/commands/implementations/`
- Consistent with existing Maia architecture patterns

## Error Recovery

### Context Loss During Implementation
1. Run this universal recovery command
2. Identify which implementation you were working on
3. Load implementation-specific context
4. Resume from last checkpoint

### Missing Implementation Data
1. Check if implementation exists in tracker database
2. Recreate implementation tracking if needed
3. Restore from git history if files are missing
4. Use research files to reconstruct context

This universal system ensures no implementation progress is ever lost and provides consistent recovery procedures across all projects.