# Broken Files Investigation - For Original Maia System

## Context
During anti-sprawl cleanup analysis (Phase 81), discovered several files that appear to be broken stubs or have import issues. Need to verify if these were broken before backup/restore or are new issues.

## Files to Investigate

### 1. backlog_manager.py - CRITICAL PRODUCTION ISSUE

**File**: `claude/tools/backlog_manager.py`
**Size**: 27 bytes (1 line)
**Content**: `"""Emoji domain package"""`
**Status**: Appears to be a stub

**Import References Found**:
```python
# In claude/hooks/auto_backlog_capture.py:
from claude.tools.backlog_manager import get_backlog_manager

# In claude/hooks/todo_to_backlog_bridge.py:
from claude.tools.backlog_manager import get_backlog_manager

# In claude/tools/monitoring/health_check.py:
from backlog_manager import BacklogManager
```

**Question**: Is backlog_manager.py functional in original system? Does it contain actual BacklogManager class and get_backlog_manager() function, or is it a stub there too?

**Test Command**:
```bash
python3 -c "from claude.tools.backlog_manager import get_backlog_manager; print('SUCCESS')"
```

---

### 2. Stub File Pairs - All 1-Line Files

**Pattern**: All contain only `"""Emoji domain package"""`

#### Pair 1: rag_document_connectors
- `claude/tools/rag_document_connectors.py` (27 bytes, 1 line)
- `claude/tools/data/rag_document_connectors.py` (27 bytes, 1 line)

**Question**: Is there a real rag_document_connectors implementation elsewhere? Or were these always stubs?

**Test**: Search for actual RAG document connector implementation

---

#### Pair 2: backlog_manager (duplicate location)
- `claude/tools/automation/backlog_manager.py` (27 bytes, 1 line)

**Question**: Was there supposed to be a backlog manager in automation/ subdirectory?

---

#### Pair 3: real_data_job_analyzer
- `claude/tools/real_data_job_analyzer.py` (27 bytes, 1 line)
- `claude/tools/data/real_data_job_analyzer.py` (27 bytes, 1 line)

**Question**: Is there a real job analyzer implementation?

---

#### Pair 4: personal_knowledge_graph_optimized
- `claude/tools/personal_knowledge_graph_optimized.py` (27 bytes, 1 line)
- `claude/tools/data/personal_knowledge_graph_optimized.py` (27 bytes, 1 line)

**Import Reference**:
```python
# In claude/tools/research/smart_research_manager.py:
from personal_knowledge_graph_optimized import PersonalKnowledgeGraph, NodeType, get_knowledge_graph
```

**Question**: Does personal_knowledge_graph_optimized.py actually exist with these functions? This import will fail if it's just a stub.

**Test Command**:
```bash
python3 -c "from personal_knowledge_graph_optimized import PersonalKnowledgeGraph; print('SUCCESS')"
```

---

#### Pair 5: agent_message_bus
- `claude/tools/agent_message_bus.py` (27 bytes, 1 line)
- `claude/tools/communication/agent_message_bus.py` (27 bytes, 1 line)

**Question**: Is there a real message bus implementation?

---

#### Pair 6: autonomous_alert_system
- `claude/tools/autonomous_alert_system.py` (27 bytes, 1 line)
- `claude/tools/communication/autonomous_alert_system.py` (27 bytes, 1 line)

**Question**: Is there a real alert system implementation?

---

#### Pair 7: rag_background_service
- `claude/tools/rag_background_service.py` (27 bytes, 1 line)
- `claude/tools/data/rag_background_service.py` (27 bytes, 1 line)

**Question**: Is there a real RAG background service?

---

### 3. personal_knowledge_graph stub in data/

**File**: `claude/tools/data/personal_knowledge_graph.py` (27 bytes, 1 line)
**Production File**: `claude/tools/personal_knowledge_graph.py` (921 lines, functional)

**Import Reference**:
```python
# In claude/tools/automation/multi_modal_processor.py:
from claude.tools.personal_knowledge_graph import get_knowledge_graph, NodeType
```

**Question**: Is the data/ stub intentional? Or leftover from refactoring?

---

## Investigation Tasks for Original Maia System

Please run the following checks on the **original (pre-backup/restore)** Maia system:

### Task 1: Check backlog_manager functionality
```bash
# Check file content
cat claude/tools/backlog_manager.py

# Test import
python3 -c "from claude.tools.backlog_manager import get_backlog_manager; bm = get_backlog_manager(); print(f'SUCCESS: {type(bm).__name__}')"

# Expected: Should show BacklogManager class, not stub
```

### Task 2: Check personal_knowledge_graph_optimized
```bash
# Check file content
cat claude/tools/personal_knowledge_graph_optimized.py

# Test import
python3 -c "from personal_knowledge_graph_optimized import PersonalKnowledgeGraph; print('SUCCESS')"

# Expected: Should import successfully if file is real
```

### Task 3: Find all stub files
```bash
# Find all files containing only the stub pattern
find claude/tools -type f -name "*.py" -exec sh -c 'test $(wc -c < "$1") -eq 27 && echo "$1: $(cat "$1")"' _ {} \;

# Count stub files
find claude/tools -type f -name "*.py" -size -50c | wc -l

# Expected: How many stub files exist in original system?
```

### Task 4: Check for import failures
```bash
# Test all imports that reference the stub files
python3 -c "from claude.hooks.auto_backlog_capture import *; print('auto_backlog_capture: OK')"
python3 -c "from claude.hooks.todo_to_backlog_bridge import *; print('todo_to_backlog_bridge: OK')"
python3 -c "from claude.tools.research.smart_research_manager import *; print('smart_research_manager: OK')"

# Expected: Should these imports work? Or do they fail in original system too?
```

### Task 5: Search for actual implementations
```bash
# Search for BacklogManager class definition
grep -r "class BacklogManager" claude --include="*.py"

# Search for RAG document connectors
grep -r "class.*DocumentConnector\|def.*document.*connector" claude --include="*.py"

# Search for PersonalKnowledgeGraph optimized
grep -r "class PersonalKnowledgeGraph" claude/tools/personal_knowledge_graph_optimized.py

# Expected: Where are the real implementations?
```

---

## Questions to Answer

1. **Were these files always stubs?** Or did backup/restore lose the actual implementations?

2. **Are imports broken in original system?** Or do these imports work because files are different?

3. **What is "Emoji domain package"?** Is this a placeholder pattern? Why is it used?

4. **Which files are safe to delete?** If they're stubs in original system too, they can be cleaned up.

5. **Which files need restoration?** If they had real content before, need to restore from earlier backup.

---

## Expected Results

**If files are stubs in original system**:
→ Safe to delete during cleanup
→ Imports are broken there too
→ These are abandoned/incomplete features

**If files are real in original system**:
→ Backup/restore lost implementations
→ Need to restore from earlier backup
→ Critical to fix before using system

**If some are real, some are stubs**:
→ Mixed situation requiring case-by-case analysis
→ Priority: Fix imports that are actively used (backlog_manager, personal_knowledge_graph_optimized)

---

## Comparison Checklist

Please provide the following from original Maia system:

- [ ] File sizes for all 18 stub files (are they 27 bytes there too?)
- [ ] Content of backlog_manager.py (is it functional?)
- [ ] Content of personal_knowledge_graph_optimized.py (does it exist?)
- [ ] Import test results (do the imports work?)
- [ ] grep results for class definitions
- [ ] Any error logs showing import failures

This will help determine if Phase 81's anti-sprawl system revealed pre-existing issues or if backup/restore caused data loss.
