# Unified Filesystem-based Context (UFC) System

⚠️  **CRITICAL: DO NOT MOVE THIS FILE** ⚠️  
**Location**: `${MAIA_ROOT}/claude/context/ufc_system.md`  
**Reason**: Required by CLAUDE.md mandatory context loading sequence  
**Dependencies**: New context windows expect this exact path  

## Overview
The UFC system is the foundation of Maia's context management. It provides a modular, hierarchical structure for organizing all knowledge, tools, and project-specific information.

## Core Principles
1. **Filesystem as Context**: The directory structure IS the context system
2. **Modular Loading**: Load only what's needed for the current task
3. **Optimized Nesting**: Maximum 4-5 levels where justified by complexity (performance analysis shows zero impact)
4. **Clean Separation**: Don't pollute project repos with context files

## Directory Structure

```
claude/
├── context/            # Context management system
│   ├── core/           # Core system configurations
│   ├── projects/        # Project-specific contexts
│   ├── tools/          # Tool definitions and capabilities
│   ├── personal/       # Personal data and preferences
│   └── knowledge/      # Domain knowledge and references
├── agents/             # Specialized agent definitions
├── commands/           # Custom command implementations
├── tools/              # Executable tools and utilities
├── hooks/              # System hooks and validation
└── data/               # Structured data assets and databases
```

## Loading Strategy
1. Core context loads first (system understanding)
2. Project context loads based on current directory
3. Tools load as needed based on task requirements
4. Personal context provides user-specific knowledge

## Important Rules
- Maximum 4-5 levels of nesting where complexity justifies it (3 levels preferred for simplicity)
- Each file should focus on ONE specific area
- Use clear, descriptive filenames
- Keep files concise and focused
- Update regularly but maintain consistency

### Nesting Guidelines
- **3 Levels**: Default maximum for most use cases (claude/context/core/identity.md)
- **4-5 Levels**: Allowed for complex specialized domains requiring granular organization
- **Performance Note**: Modern APFS and Python pathlib handle deep nesting efficiently (zero measurable impact)