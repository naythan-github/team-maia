# Archive Extension Zone

**Purpose**: Historical preservation of deprecated functionality and experiments that didn't work out.

## Guidelines

### ✅ What Belongs Here
- Deprecated tools/agents replaced by better implementations
- Failed experiments with lessons learned
- Historical implementations for reference
- Superseded functionality
- Code with valuable patterns but no current use

### ❌ What Doesn't Belong Here
- Active code still in use
- Temporary files (use experimental/ instead)
- Broken code with no value

## Lifecycle

**Read-Only Reference**: Archive is for preservation, not active development.

**No Deletion**: Archived items are preserved indefinitely unless taking up excessive space.

**Documentation Required**: Each archived item should have context:
- Why it was deprecated
- What replaced it
- What was learned
- Date archived

## Archive Structure

Organize by category and date:
```
archive/
├── 2025/
│   ├── agents/
│   ├── tools/
│   └── experiments/
├── 2024/
│   └── ...
└── lessons_learned.md
```

## Archival Process

When archiving code:
1. Move to appropriate year/category
2. Add entry to `lessons_learned.md`
3. Remove from active documentation
4. Update references in active code
5. Note in git commit message

## Current Status

Created: 2025-10-02
Files: 0
Policy: Preserve indefinitely

**Remember**: Archive is about learning from history, not hiding failures!
