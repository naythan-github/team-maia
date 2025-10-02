# Personal Extension Zone

**Purpose**: User-specific customizations and personal workflows that don't belong in shared core.

## Guidelines

### ✅ What Belongs Here
- Personal automation scripts
- Custom dashboard configurations
- Individual workflow preferences
- Personal data processing tools
- User-specific integrations

### ❌ What Doesn't Belong Here
- Shared system functionality
- Core capabilities needed by all users
- Production tools used across the system

## Lifecycle

**Preservation**: Personal customizations are preserved across backups but clearly separated from core.

**No Automatic Cleanup**: Personal zone files are not subject to quarterly cleanup unless explicitly flagged.

**Backup Policy**: Backed up but treated as non-critical for system restoration.

## Naming Conventions

**Flexible naming** - Use whatever makes sense for personal organization:
- Prefix with username if multi-user: `naythan_custom_dashboard.py`
- Descriptive names preferred
- Personal preference takes priority

## Integration Guidelines

If personal code needs to integrate with core system:
1. Use extension points (hooks, plugins)
2. Don't modify core files directly
3. Document integration points
4. Consider proposing as core feature if valuable to others

## Current Status

Created: 2025-10-02
Files: 0
Owner: Personal customizations

**Remember**: Personal zone is for YOU - organize it however works best!
