# Completion Checklist Command

## Purpose
Validate that work is truly complete before declaring "done". Prevents the common pattern of finishing technical implementation but forgetting documentation, integration, and testing.

## Usage
```
/complete              # Full checklist
/complete --quick      # Essential checks only (git + capabilities)
```

## When to Use
- Before saying "done", "complete", or "finished"
- Before closing a session
- After implementing any new tool, agent, or command
- After multi-step tasks

---

## Checklist Execution

### 1. Git Status Check
Run:
```bash
git status --short
```

**PASS**: No uncommitted changes, or all changes are intentionally staged
**WARN**: Unstaged changes exist
**FAIL**: Uncommitted changes to core files (tools, agents, commands)

---

### 2. Capability Registration Check
Find unregistered capabilities:

```bash
# Get files modified in this session (last 24h or since session start)
find claude/tools claude/agents claude/commands -name "*.py" -o -name "*.md" -mmin -60 2>/dev/null | head -20

# Cross-reference with capabilities.db
sqlite3 claude/data/databases/system/capabilities.db "SELECT path FROM capabilities"
```

**PASS**: All new/modified files in tools/agents/commands are registered
**WARN**: New files exist but aren't registered
**FAIL**: Core tools missing from capabilities.db

Quick registration if needed:
```bash
python3 claude/tools/core/find_capability.py --refresh  # If available
# Or manually:
sqlite3 claude/data/databases/system/capabilities.db "INSERT INTO capabilities (name, type, path, category, purpose, keywords, status) VALUES ('filename.py', 'tool', 'claude/tools/domain/filename.py', 'category', 'purpose description', 'keyword1,keyword2', 'production')"
```

---

### 3. Documentation Check
For each new/modified file, verify:

**Tools (.py files)**:
- Has module docstring at top
- Public functions have docstrings
- Complex logic has inline comments

**Agents (.md files)**:
- Has `## Purpose` section
- Has usage examples
- Has clear success criteria

**Commands (.md files)**:
- Has `## Usage` section
- Has `## When to Use` section

**PASS**: All new files have appropriate documentation
**WARN**: Minor documentation gaps
**FAIL**: New tool/agent with no documentation

---

### 4. Testing Check
For new Python files in `claude/tools/`:

```bash
# Find new tool files
NEW_TOOLS=$(find claude/tools -name "*.py" -mmin -60 ! -name "__init__.py" ! -name "__pycache__" 2>/dev/null)

# Check for corresponding test files
for tool in $NEW_TOOLS; do
    test_file="tests/$(echo $tool | sed 's|claude/tools/|test_|' | sed 's|/|_|g')"
    # Or: tests/domain/test_filename.py pattern
done
```

**PASS**: All new tools have corresponding test files
**WARN**: Test file exists but has fewer tests than public functions
**FAIL**: New tool with no test file

---

### 5. Learning Capture Check
Verify PAI v2 session is active:

```bash
python3 -c "from claude.tools.learning.session import get_session_manager; m=get_session_manager(); print('Session active' if m.current_session else 'No session')"
```

**PASS**: Session active, learning will be captured on `/close-session`
**WARN**: Session not found (may lose learnings)
**FAIL**: Learning system unavailable

---

## Output Format

```
/complete Checklist
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Git Status                              [PASS]
  Working tree clean

Capability Registration                 [WARN]
  Unregistered: claude/tools/new/feature.py

Documentation                           [PASS]
  All files documented

Testing                                 [FAIL]
  Missing: tests/new/test_feature.py

Learning Capture                        [PASS]
  Session 52335 active

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Result: 3/5 PASS | 1 WARN | 1 FAIL

Blockers (must fix):
1. Create tests/new/test_feature.py

Warnings (should fix):
1. Register claude/tools/new/feature.py in capabilities.db
```

---

## Quick Mode (--quick)

Only runs:
1. Git Status Check
2. Capability Registration Check

Use when documentation and tests are known to be complete.

---

## Integration with Workflow

### Automatic Trigger Points
This command should be invoked:
- When user says "is it done?" or similar
- Before any `/close-session`
- After completing TodoWrite items marked "complete"

### Principle 21 Enforcement
This command enforces CLAUDE.md Principle #21:
> **Completeness Review** - Pause after tests pass: verify docs updated, integration complete, holistic review

---

## Success Criteria
- 0 FAIL items = Ready to declare complete
- 0 FAIL + 0 WARN = Fully complete
- Any FAIL = Not complete, must address blockers
