# Experimental Extension Zone

**Purpose**: Safe space for development and testing of new features without affecting production code.

## Guidelines

### ✅ What Belongs Here
- Prototype implementations
- Proof-of-concept code
- Testing new approaches
- Experimental agents/tools before production
- Research and development work

### ❌ What Doesn't Belong Here
- Production code
- Core system functionality
- Anything with dependencies from production code

## Lifecycle

**Automatic Cleanup**: Files older than 90 days are flagged for review during quarterly audits.

**Graduation Path**:
1. Develop and test in experimental/
2. Validate functionality and value
3. Move to appropriate production directory (claude/tools/, claude/agents/, etc.)
4. Update documentation

**Deprecation Path**:
1. If not valuable after testing
2. Move to claude/extensions/archive/
3. Document why it didn't work out

## Naming Conventions

**Relaxed naming rules** - Use descriptive names but version/temp indicators are allowed here:
- `feature_v1.py` ✅ (experimental only)
- `test_new_approach.py` ✅ (experimental only)
- `prototype_agent.md` ✅ (experimental only)

## Current Status

Created: 2025-10-02
Files: 0
Last Cleanup: Never (newly created)

**Remember**: No production dependencies on experimental code!
