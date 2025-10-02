# Maia Efficiency Protocols

## 🎯 Core Principle: Smart Planning → Precise Execution

### Token Conservation Framework

#### 🟢 Before ANY Operation
1. **Estimate effort level**: Low (<50K) / Medium (50-200K) / High (200K+)
2. **Check existing state**: Read state files before re-analyzing
3. **Plan execution path**: List specific steps before starting

#### 🔍 Search Before Read
```
❌ INEFFICIENT: Read multiple files looking for something
✅ EFFICIENT: Grep/Glob first, then Read specific matches

Example:
- Instead of: Read 10 files to find a function
- Do: Grep "function_name" → Read only matching file
```

#### 📦 Batch Operations
```
❌ INEFFICIENT: Multiple individual edits
✅ EFFICIENT: Use MultiEdit or parallel operations

Example:
- Instead of: 5 Edit calls to one file
- Do: 1 MultiEdit with all changes
```

#### 💾 State Persistence
```
❌ INEFFICIENT: Re-analyze after context compression
✅ EFFICIENT: Save analysis results, reload from state

Example:
- Instead of: Re-scan codebase after reset
- Do: Load from session state files
```

### Operational Protocols

#### 1. **Git Operations**
```markdown
BEFORE COMMIT:
1. Run validation first (UFC check, tests)
2. Batch all fixes
3. Single commit attempt

AVOID:
- Multiple commit attempts
- Reading large diffs repeatedly
- Uncommitted work across context resets
```

#### 2. **File Organization**
```markdown
BEFORE MOVING FILES:
1. Plan complete structure
2. Check dependencies
3. Execute in one pass

AVOID:
- Trial-and-error moves
- Iterative reorganization
- Reading files to determine location
```

#### 3. **Large-Scale Analysis**
```markdown
BEFORE SYSTEM-WIDE OPERATIONS:
1. Save current state
2. Use targeted searches
3. Process in batches

AVOID:
- Reading entire codebase
- Redundant file access
- Losing work to context limits
```

### Task Estimation Guide

#### Quick Reference
| Operation Type | Token Estimate | Strategy |
|---------------|---------------|----------|
| Single file edit | 5-10K | Direct execution |
| Multi-file refactor | 50-100K | Use MultiEdit, batch |
| New feature implementation | 100-200K | Break into subtasks |
| System-wide changes | 200K+ | Multi-session planning |
| Security audit | 150-300K | Save results externally |
| Documentation update | 30-50K | Single focused session |

### Efficiency Checklist

Before starting any task:
- [ ] Check if similar work was done (session files)
- [ ] Estimate token usage (use guide above)
- [ ] Plan batched operations
- [ ] Set up state persistence if needed
- [ ] Use TodoWrite for multi-step tasks

### Implementation Tools

#### 1. **Efficiency Tracker**
```python
# At start of operation
complexity = "high"  # low/medium/high
estimated_tokens = 200000
strategy = "batch operations, save state"
```

#### 2. **Smart Search Pattern**
```python
# Always search before read
files = Glob("**/*.py")
matches = Grep("pattern", files)
content = Read(matches[0])  # Read only what's needed
```

#### 3. **State Management**
```python
# Save expensive analysis
state = {
    "analysis_results": results,
    "timestamp": now(),
    "context": relevant_data
}
Write("session/analysis_state.json", state)
```

### Context Compression Strategy

When approaching context limit:
1. **Save active work state immediately**
2. **Document completed tasks**
3. **Create continuation plan**
4. **Reference state files for next session**

### Monitoring & Feedback

Track efficiency metrics:
- Token usage per task type
- Success rate of first attempts
- Time to completion
- Context compressions per session

### Emergency Protocols

If hitting token limits:
1. **STOP** complex operations immediately
2. **SAVE** current state to file
3. **DOCUMENT** next steps clearly
4. **PREPARE** for clean handoff

## Applied to Current Session

Starting now, I will:
1. Announce effort estimates before operations
2. Use batch operations by default
3. Save analysis results externally
4. Check for existing work before re-doing
5. Plan multi-step operations before starting

This protocol ensures maximum value from available tokens while maintaining quality and completeness.