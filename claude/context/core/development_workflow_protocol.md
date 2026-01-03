# Development Workflow Protocol v2.3 (Compressed)

**Purpose**: Define experimental → production directory usage to prevent sprawl
**Updated**: 2025-11-24 (Phase 179 - Database Sync Integration)

---

## Directory Structure

```
claude/
├── tools/
│   ├── sre/               # Production SRE tools
│   ├── security/          # Production security tools
│   ├── experimental/      # WIP tools (any category)
│   └── archive/2025/      # Deprecated/rejected
├── agents/
│   ├── *.md               # Production agents
│   ├── experimental/      # WIP agents
│   └── archive/           # Deprecated agents
└── data/                  # No experimental (data is data)
```

---

## Decision Tree

```
Creating new file?
├── NEW feature/tool → experimental/ (prototype freely)
├── MODIFYING existing → Edit in place (check protection level)
└── TEST file → experimental/tests/
```

---

## Workflow Phases

### Phase 1: Prototype 🔬
**Location**: `claude/tools/experimental/`
- Building NEW tool/agent/feature
- Testing different approaches
- Proof-of-concept before production
- Naming: version indicators OK (`email_rag_v1.py`, `prototype_*.py`)

### Phase 2: Test & Iterate 🧪
**Location**: Still in experimental/
- Test with real data, compare approaches
- Files can break, have multiple versions, be deleted
- Import FROM production OK, NOT vice versa

### Phase 3: Validation ✅
**Checklist before graduation**:
- [ ] Functionality works
- [ ] Performance acceptable
- [ ] Code quality production-grade
- [ ] Documentation exists
- [ ] No hardcoded paths/credentials
- [ ] Error handling implemented
- [ ] Testing completed
- [ ] User confirmed value
- [ ] Only ONE version is "winner"

### Phase 4: Graduation 🎓
**Steps**:
1. Choose best implementation (delete/archive others)
2. Rename with semantic naming (remove version indicators)
3. Move to production directory
4. Update documentation (SYSTEM_STATE.md, capability_index.md)
5. **Database sync (MANDATORY)**:
   ```bash
   python3 claude/tools/sre/capabilities_registry.py scan
   python3 claude/tools/sre/system_state_etl.py --recent 10
   ```
6. Git commit with production marker
7. Delete/archive experimental versions

---

## Quick Reference

| Scenario | Action |
|----------|--------|
| Building new | → `experimental/` → iterate → graduate ONE winner |
| Modifying existing | → Check protection → Edit in place → Update docs |
| Testing approach | → `experimental/tests/` or `experimental/{name}_test.py` |

---

## Anti-Patterns

**❌ DON'T**:
```
claude/tools/email_search.py
claude/tools/email_search_v2.py
claude/tools/email_search_enhanced.py
```
Result: 4 production files = sprawl

**✅ DO**:
```
claude/tools/experimental/email_search_*.py  # Prototype
claude/tools/email_search_system.py          # ONE graduated
claude/tools/archive/2025/email_prototypes/  # Archive losers
```

---

## Graduation Checklist Template

```markdown
## Graduation: [Feature Name]

### Experimental Files
- [ ] experimental/[file1].py
- [ ] experimental/[file2].py

### Winner
**File**: [chosen].py | **Reason**: [why]

### Production Target
`claude/tools/{category}/[semantic_name].py`

### Validation
- [ ] Functionality ✓ | Performance ✓ | Quality ✓
- [ ] Documentation ✓ | Error handling ✓ | Testing ✓

### Post-Graduation
- [ ] SYSTEM_STATE.md updated
- [ ] capability_index.md updated
- [ ] Databases synced
- [ ] Git committed
- [ ] Experimental cleaned
```

---

## Success Metrics

- New features start in experimental/ (100%)
- Only 1 version graduates to production
- Documentation updated during graduation
- Production directories have 0 version indicators

---

*v2.3 | 403→~150 lines (~63% reduction) | Core workflow preserved*
