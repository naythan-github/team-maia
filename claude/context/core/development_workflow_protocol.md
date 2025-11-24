# Development Workflow Protocol
**Created**: 2025-10-02 (Phase 81)
**Updated**: 2025-11-24 (Phase 179 - Database Sync Integration)
**Purpose**: Define HOW and WHEN Maia uses experimental/ vs production directories
**Critical**: Prevents sprawl by ensuring prototypes don't pollute production

## 🚨 The Problem This Solves

**Historical Issue**: Maia builds new features directly in production directories:
- Email RAG system (Phase 80B): 3 implementations created in `claude/tools/` during development
- Should have been in experimental/ subdirectory during prototyping
- Result: 3 "production" files when only 1 should be there

**Root Cause**: Anti-sprawl system created extension zones but **never told Maia to use them**.

## 📁 Consolidated Directory Structure (Phase 170)

**Simplified model** - Everything lives within its category:

```
claude/
├── tools/
│   ├── sre/                    # Production SRE tools
│   ├── security/               # Production security tools
│   ├── productivity/           # Production productivity tools
│   ├── experimental/           # WIP tools (any category)
│   └── archive/                # Deprecated/rejected tools
│       └── 2025/               # Archived by year
├── agents/
│   ├── *.md                    # Production agents
│   ├── experimental/           # WIP agents
│   └── archive/                # Deprecated agents
└── data/
    └── (no experimental - data is data)
```

**Key principle**: `experimental/` and `archive/` are subdirectories within each category, not a separate `extensions/` hierarchy.

## 📋 Mandatory Development Workflow

### Decision Tree: Where Should This File Go?

```
START: You're about to create a new file
    ↓
[Q1] Am I building something NEW that doesn't exist yet?
    YES → GO TO EXPERIMENTAL WORKFLOW
    NO  → GO TO PRODUCTION WORKFLOW

[Q2] Am I modifying existing production code?
    YES → Edit in place (if MEDIUM protection)
    NO  → STOP - Check immutable_paths.json first

[Q3] Am I creating a test file?
    YES → claude/tools/experimental/tests/
    NO  → Continue to next question
```

### EXPERIMENTAL WORKFLOW (New Development)

**Phase 1: Prototyping** 🔬
```
Location: claude/tools/experimental/

When to Use:
- Building a NEW tool, agent, or feature
- Testing different approaches (e.g., 3 RAG implementations)
- Proof-of-concept before committing to production
- Exploring solutions to a new problem
- Research and development

Naming Rules:
- Descriptive but version indicators ALLOWED
- email_rag_v1.py ✅
- email_rag_sentence_transformers.py ✅
- email_rag_ollama_test.py ✅
- prototype_semantic_search.py ✅

Example:
User asks: "Build email semantic search"
Maia creates:
  claude/tools/experimental/email_rag_v1.py
  claude/tools/experimental/email_rag_v2_ollama.py
  claude/tools/experimental/email_rag_v3_enhanced.py
```

**Phase 2: Testing & Iteration** 🧪
```
Location: Still in experimental/

Activities:
- Test with real data
- Iterate on implementation
- Compare approaches
- Identify best solution
- Document findings

Duration: As long as needed (no rush to production)

Files Can:
- Have multiple versions
- Use messy names
- Break frequently
- Be deleted without ceremony
- Import from production (but not vice versa)
```

**Phase 3: Validation** ✅
```
Before graduation to production, verify:

[ ] Functionality works as intended
[ ] Performance is acceptable
[ ] Code quality is production-grade
[ ] Documentation exists (docstrings, comments)
[ ] No hardcoded paths or credentials
[ ] Error handling implemented
[ ] Testing completed successfully
[ ] User confirms it's valuable
[ ] Only ONE version is "the winner"

If ALL boxes checked → Ready for graduation
If ANY box unchecked → Stay in experimental/
```

**Phase 4: Graduation to Production** 🎓
```
Location: Move from experimental/ → production directory

Steps:
1. Choose best implementation (delete/archive others)
2. Rename with semantic naming (remove version indicators)
3. Move to appropriate production directory:
   - claude/tools/{category}/{semantic_name}.py
   - claude/agents/{semantic_name}_agent.md
   - claude/commands/{semantic_name}.md
4. Update documentation:
   - SYSTEM_STATE.md (add to current phase)
   - capability_index.md (add to capabilities)
5. Database sync (MANDATORY - Phase 179):
   - python3 claude/tools/sre/capabilities_registry.py scan
   - python3 claude/tools/sre/system_state_etl.py --recent 10
6. Git commit with production marker
7. Delete/archive experimental versions

Example Graduation:
  FROM: claude/tools/experimental/email_rag_v2_ollama.py
  TO:   claude/tools/email_rag_system.py

  Archive:
    claude/tools/archive/2025/email_rag_v1_prototype.py
    claude/tools/archive/2025/email_rag_v3_rejected.py
```

### PRODUCTION WORKFLOW (Existing Code)

**When Modifying Existing Files**:
```
Check Protection Level:
1. Run: python3 claude/tools/file_lifecycle_manager.py check-file <filepath>
2. If ABSOLUTE: Content edits only, no moves/renames
3. If HIGH: Content edits only, no moves/renames
4. If MEDIUM: Content edits + new files OK, moves need consideration
5. If UNPROTECTED: Full freedom

Naming Requirements:
- Semantic naming ENFORCED
- No version indicators (_v1, _v2, _new, _old)
- No timestamps (except data/, logs/, backups/)
- Descriptive and specific

Example:
Improving existing tool:
  Edit: claude/tools/backup_manager.py (in place)
  Not:  claude/tools/backup_manager_improved.py (creates sprawl)
```

**When Creating New Production Files**:
```
STOP! Ask:
- Is this really production-ready without testing?
- Should this go to experimental/ first?

If genuinely production-ready (rare):
- Use semantic naming
- Update documentation immediately
- Add to SYSTEM_STATE.md current phase
```

## 🎯 Quick Reference for Maia

### "I'm Building Something New"
```
→ claude/tools/experimental/
→ Iterate freely
→ Test thoroughly
→ Graduate ONE winner to production
→ Archive the rest
```

### "I'm Modifying Existing Code"
```
→ Check protection level first
→ Edit in place (don't create new version)
→ Update documentation if behavior changes
```

### "I'm Testing an Approach"
```
→ claude/tools/experimental/tests/
→ OR experimental/{feature_name}_test.py
→ Keep tests in experimental/ until feature graduates
```

## 📊 Anti-Patterns to Avoid

**❌ DON'T DO THIS**:
```
Building new email search system:
  claude/tools/email_search.py
  claude/tools/email_search_v2.py
  claude/tools/email_search_enhanced.py
  claude/tools/email_search_final.py

Result: 4 production files, sprawl created
```

**✅ DO THIS INSTEAD**:
```
Building new email search system:
  claude/tools/experimental/email_search_base.py
  claude/tools/experimental/email_search_ollama.py
  claude/tools/experimental/email_search_gpu.py

Test, choose winner:
  claude/tools/email_search_system.py (graduated)

Archive losers:
  claude/tools/archive/2025/email_search_prototypes/

Result: 1 production file, clean system
```

## 🔄 Graduation Checklist Template

When graduating from experimental/ → production:

```markdown
## Graduation Review: [Feature Name]

### Experimental Files
- [ ] claude/tools/experimental/[file1].py
- [ ] claude/tools/experimental/[file2].py
- [ ] claude/tools/experimental/[file3].py

### Chosen Winner
**File**: [chosen_file].py
**Reason**: [why this approach won]

### Production Destination
**Target**: claude/tools/{category}/[semantic_name].py
**Protection Level**: MEDIUM (claude/tools/)

### Pre-Graduation Validation
- [ ] Functionality verified
- [ ] Performance acceptable
- [ ] Code quality reviewed
- [ ] Documentation complete
- [ ] Error handling robust
- [ ] No hardcoded secrets
- [ ] Testing completed
- [ ] User approved

### Documentation Updates Required
- [ ] SYSTEM_STATE.md (add to current phase)
- [ ] capability_index.md (add to capabilities)

### Cleanup Actions
- [ ] Move winner to production with semantic name
- [ ] Archive rejected prototypes
- [ ] Delete experimental originals
- [ ] Git commit with graduation message

### Post-Graduation Verification
- [ ] File in correct location
- [ ] Documentation updated
- [ ] Experimental directory cleaned
- [ ] No naming violations
- [ ] Git history clean
```

## 🛡️ Protection Integration

**File Lifecycle Manager Integration**:
```python
# When creating new files, lifecycle manager should:
1. Check if file is in experimental/ → Allow any naming
2. Check if file is in production/ → Enforce semantic naming
3. Check if modifying protected files → Block based on protection level
```

**Git Pre-Commit Hook Integration**:
```bash
# Hook should warn:
- New files in claude/tools/ without SYSTEM_STATE.md update
- Multiple similar files in production (e.g., tool_v1.py, tool_v2.py)
- Experimental files being committed as production
```

## 📝 Maia Self-Check Questions

**Before creating ANY new file, ask**:
1. Is this experimental or production?
2. If experimental: Am I using experimental/ directory?
3. If production: Have I graduated from experimental/ properly?
4. Am I creating duplicate/versioned files in production?
5. Have I updated documentation for production changes?

## 🎓 Example: Email RAG System (Corrected Workflow)

**What SHOULD have happened in Phase 80B**:

```
Day 1: Prototyping
User: "Build email semantic search with RAG"
Maia: "I'll prototype in experimental/"
  CREATE: claude/tools/experimental/email_rag_base.py
  CREATE: claude/tools/experimental/email_rag_ollama.py
  CREATE: claude/tools/experimental/email_rag_enhanced.py

Day 2: Testing
Maia: "Testing all three approaches..."
  Test sentence-transformers approach
  Test ollama nomic-embed-text approach
  Test ollama + LLM semantic approach

Day 2: Winner Selection
Maia: "email_rag_ollama.py performed best (0.048s/email, good relevance)"
User: "Great, make it production"

Day 2: Graduation
Maia: "Graduating to production..."
  MOVE: experimental/email_rag_ollama.py
    → claude/tools/email_rag_system.py

  ARCHIVE:
    experimental/email_rag_base.py
    → archive/2025/email_prototypes/base_approach.py

    experimental/email_rag_enhanced.py
    → archive/2025/email_prototypes/enhanced_llm_approach.py

  UPDATE: SYSTEM_STATE.md with Phase 80B
  UPDATE: capability_index.md with email RAG capability

Result: 1 production file, 2 archived prototypes, clean system
```

## 🔧 Enforcement Mechanisms

**Automated**:
1. File lifecycle manager checks directory before allowing creation
2. Pre-commit hook warns about new production files
3. Quarterly audit flags experimental files >90 days old

**Manual (Maia)**:
1. Self-check before creating files
2. Follow decision tree
3. Use graduation checklist
4. Update documentation during graduation

## 📊 Success Metrics

This protocol is working when:
- New features start in experimental/ (100% compliance)
- Only 1 version graduates to production (no sprawl)
- Documentation updated during graduation (not after)
- Experimental/ directory regularly cleaned (quarterly)
- Production directories have 0 version indicators in filenames
- Clear audit trail from prototype → production

## 🚨 Red Flags

**Warning signs this protocol is being violated**:
- Multiple similar files in claude/tools/ (e.g., tool_v1.py, tool_v2.py)
- New files in production without SYSTEM_STATE.md update
- Empty experimental/ directory (nothing being prototyped)
- Version indicators in production filenames
- Features going directly to production without testing

## 📅 Review Schedule

**Quarterly Audit**:
1. Review experimental/ directory
2. Flag files >90 days old for decision:
   - Graduate to production?
   - Archive as failed experiment?
   - Delete as no longer relevant?
3. Check production directories for sprawl indicators
4. Verify documentation matches actual files

**Version**: 2.0 (2025-11-22)
**Next Review**: 2025-12-31 (Q1 2026)
