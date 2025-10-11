# Tool Discovery Architecture - Root Cause Analysis

**Date**: 2025-10-11
**Issue**: Maia regularly can't find tools despite having 282 actual tools implemented
**Investigation Status**: ✅ COMPLETE - Root causes identified

---

## Executive Summary

**Problem**: Tool discovery failures despite having 282 Python tools implemented
**Root Causes**: 3 architectural issues causing 83 phantom dependencies and discovery confusion
**Impact**: Documentation/reality mismatch, reference sprawl, no centralized registry

---

## Evidence

### Quantitative Metrics
- **Actual tools**: 282 Python files in `claude/tools/`
- **Documented tools**: 454 tool references
- **Phantom tools**: 83 (documented but don't exist)
- **Reference sprawl**: 896 tool references across 104 markdown files
- **Average references per tool**: 3.2 mentions per tool

### Phantom Tool Examples
```
❌ systematic_tool_discovery.py (referenced, doesn't exist)
❌ rag_document_connectors.py (referenced, doesn't exist)
❌ enterprise_monitoring_agent.py (referenced, doesn't exist)
❌ cloud_sync_manager.py (referenced, doesn't exist)
❌ conversation_detector.py (documented in Phase 102, but in claude/hooks/ not claude/tools/)
❌ dynamic_context_loader.py (referenced, doesn't exist)
```

---

## Root Cause #1: No Centralized Tool Registry

### Problem
No single source of truth for available tools. Discovery happens through:
1. Filesystem scanning (`find claude/tools -name "*.py"`)
2. Documentation parsing (`grep -r "claude/tools/" **/*.md`)
3. Manual maintenance of `claude/context/tools/available.md`
4. Agent memory of previously used tools

### Evidence
- `available.md` has 120 tool references but is manually maintained
- `automation_schedule.md` has 12 tool references (cron-style)
- 104 other markdown files contain 764 additional tool references
- **No automated sync** between filesystem reality and documentation

### Impact
- Stale documentation: Tools deleted but still referenced
- Missing documentation: Tools created but not documented
- Claude can't reliably answer "what tools exist?"
- Discovery requires file reads + context parsing

---

## Root Cause #2: Tool Reference Sprawl

### Problem
Tool paths appear in 104 different files without consistent naming or structure:
- Commands reference tools directly: `python3 claude/tools/foo.py`
- Agents reference tools in examples: "Use `bar.py` to analyze..."
- Documentation embeds tool paths: "Monitor with `baz.py --dashboard`"
- Session logs capture tool usage: "Ran qux.py successfully"

### Evidence
```bash
# Tool references scattered across:
claude/commands/*.md              (68 files, 200+ references)
claude/context/core/*.md           (22 files, 350+ references)
claude/agents/*.md                 (26 files, 100+ references)
claude/context/session/*.md        (Session summaries, 150+ references)
claude/data/*.md                   (Project docs, 96+ references)
```

### Impact
- **Reference rot**: When tool moved/renamed, 3.2 references need updating
- **Inconsistent paths**: Some use `claude/tools/`, others just tool name
- **Discovery confusion**: Multiple conflicting references to same tool
- **Maintenance burden**: Can't update tool info without hunting 100+ files

---

## Root Cause #3: Documentation/Reality Mismatch (Phantom Dependencies)

### Problem
83 phantom dependencies - tools documented but don't exist. Causes:

**Cause 3A: Planned but Never Built**
- Tool documented in design phase but implementation never happened
- Example: `systematic_tool_discovery.py` (planned for Phase 82, never built)

**Cause 3B: Refactored/Renamed Without Doc Update**
- Tool renamed but old references remain
- Example: Email RAG consolidation (3 implementations → 1, old refs not cleaned)

**Cause 3C: Wrong Location Assumptions**
- Tool exists but in different directory
- Example: `conversation_detector.py` lives in `claude/hooks/` not `claude/tools/`

**Cause 3D: Session Compression Artifacts**
- Session summaries reference tools from incomplete attempts
- Example: Phase 102 summary mentions tools that were designed but not deployed

### Evidence
```bash
# Phantom detection from dependency validator:
Tool Inventory: 454 tools (documented)
Actual Tools: 282 tools (filesystem)
Phantom Dependencies: 83 tools (documented but missing)

# Critical phantoms (5+ references each):
systematic_tool_discovery.py → 6 references
enterprise_monitoring_agent.py → 5 references
cloud_sync_manager.py → 11 references
rag_document_connectors.py → 4 references
```

### Impact
- **Discovery failures**: Claude tries to use phantom tool, fails
- **Trust erosion**: User asks "use tool X", Claude can't find it
- **Context pollution**: Phantom refs waste tokens in context loading
- **Validation failure**: Dependency graph shows 42.4/100 health

---

## Architecture Weaknesses

### Current "Discovery" Process
1. Claude receives user request
2. Smart context loader loads `claude/context/tools/available.md`
3. Claude reads tool descriptions from markdown
4. Claude assumes tool exists at documented path
5. **FAILURE POINT**: Tool doesn't exist or path is wrong
6. Claude reports "can't find tool" to user

### Missing Components
- ❌ **Tool Registry**: No canonical list of tools with metadata
- ❌ **Auto-Discovery**: No filesystem scanning with caching
- ❌ **Validation**: No pre-flight check that documented tools exist
- ❌ **Version Control**: No tracking of tool lifecycle (created, deprecated, deleted)
- ❌ **Reference Tracking**: No awareness of where tools are referenced
- ❌ **Sync Mechanism**: No automation to keep docs aligned with reality

---

## Contributing Factors

### Factor 1: Rapid Development Velocity
- 282 tools created across 105 phases (avg 2.7 tools/phase)
- High creation rate → documentation lag
- Multiple developers/sessions → inconsistent practices

### Factor 2: Session-Based Development
- Tools created in one session, documented in another
- Session summaries create historical references
- Phantom tools from incomplete implementations persist in summaries

### Factor 3: No Enforcement
- No pre-commit hooks validating tool references
- No CI/CD checking documentation completeness
- No save_state validation of tool inventory
- Dependency validator exists but not in critical path

### Factor 4: UFC System Design
- UFC assumes human-maintained documentation accuracy
- No programmatic "ground truth" layer
- Markdown flexibility allows reference drift

---

## Proposed Solution Architecture

### Solution 1: Centralized Tool Registry (Immediate, High Impact)

**Implementation**: Single JSON registry as source of truth
```json
{
  "version": "1.0",
  "last_updated": "2025-10-11T13:30:00Z",
  "tools": [
    {
      "name": "launchagent_health_monitor",
      "path": "claude/tools/sre/launchagent_health_monitor.py",
      "category": "sre",
      "status": "production",
      "description": "Schedule-aware health monitoring for LaunchAgent services",
      "capabilities": ["health-check", "metrics", "slo-tracking"],
      "cli_usage": "python3 {path} --dashboard",
      "dependencies": ["launchctl", "plistlib"],
      "created": "2025-10-11",
      "last_modified": "2025-10-11",
      "references": [
        "claude/context/tools/available.md:66",
        "claude/commands/save_state.md:22"
      ]
    }
  ]
}
```

**File**: `claude/data/tool_registry.json`

**Benefits**:
- Single source of truth (filesystem + metadata)
- Machine-readable for validation
- Tracks references for impact analysis
- Enables automated discovery

**Integration**:
- Smart context loader reads registry instead of scanning
- save_state validates registry sync before commit
- Dependency validator checks registry completeness

---

### Solution 2: Auto-Discovery Script (Immediate, Medium Impact)

**Implementation**: Filesystem scanner with caching
```python
# claude/tools/sre/tool_registry_sync.py

def discover_tools() -> List[Dict]:
    """Scan claude/tools/ for Python files, extract metadata"""
    tools = []
    for py_file in Path("claude/tools").rglob("*.py"):
        # Extract docstring, CLI args, dependencies
        metadata = extract_metadata(py_file)
        tools.append({
            "path": str(py_file),
            "name": py_file.stem,
            "category": py_file.parent.name,
            "metadata": metadata
        })
    return tools

def sync_registry():
    """Update tool_registry.json from filesystem reality"""
    discovered = discover_tools()
    registry = load_registry()

    # Merge: keep documented metadata, add new tools, mark deleted
    synced = merge_with_registry(discovered, registry)

    # Validate: check for phantoms
    phantoms = validate_references(synced)

    save_registry(synced)
    return {"synced": len(synced), "phantoms": len(phantoms)}
```

**Usage**:
```bash
# Manual sync
python3 claude/tools/sre/tool_registry_sync.py --sync

# Validation only
python3 claude/tools/sre/tool_registry_sync.py --validate

# Auto-run in save_state.md
```

**Benefits**:
- Automatic discovery of new tools
- Detection of deleted tools (phantoms)
- Low maintenance burden

---

### Solution 3: Reference Consolidation (Phase 2, High Impact)

**Problem**: 896 tool references across 104 files

**Solution**: Consolidate references to registry lookups

**Before** (scattered refs):
```markdown
# claude/commands/foo.md
Run health check: `python3 claude/tools/sre/launchagent_health_monitor.py --dashboard`

# claude/agents/bar.md
Use launchagent_health_monitor.py to check services

# claude/context/tools/available.md
- **LaunchAgent Health**: Monitor services with SLO tracking
  - File: claude/tools/sre/launchagent_health_monitor.py
```

**After** (registry refs):
```markdown
# claude/commands/foo.md
Run health check: `maia tool run launchagent_health_monitor --dashboard`

# claude/agents/bar.md
Use tool `launchagent_health_monitor` to check services

# claude/context/tools/available.md
- **LaunchAgent Health**: Monitor services with SLO tracking
  - Tool ID: launchagent_health_monitor (see tool_registry.json)
```

**Benefits**:
- Single reference per tool (registry ID)
- Tool renames don't break 100+ references
- Easy to find all tool usages
- Supports aliasing and versioning

---

### Solution 4: Save State Validation (Immediate, Critical)

**Integration Point**: `claude/commands/save_state.md` Phase 2.1

**Add Pre-Flight Check**:
```markdown
#### 2.1 Tool Registry Validation ⭐ **CRITICAL**
python3 claude/tools/sre/tool_registry_sync.py --validate

**Exit codes**:
- 0 = PASS (registry synced, no phantoms)
- 1 = WARNING (minor drift, can proceed)
- 2 = CRITICAL (phantoms detected, fix before commit)

**Action if CRITICAL**: Run --sync to update registry, review phantoms
```

**Benefits**:
- Prevents phantom dependencies from entering git
- Forces documentation alignment with reality
- Creates feedback loop for tool maintenance

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. ✅ Root cause analysis (DONE - this document)
2. 🔨 Build tool_registry.json (seed with current 282 tools)
3. 🔨 Build tool_registry_sync.py (discover + validate)
4. 🔨 Integrate validation into save_state.md Phase 2.1

**Outcome**: Stop accumulating new phantoms

### Phase 2: Cleanup (Week 2)
1. 🔨 Run sync, identify 83 phantoms
2. 🔨 For each phantom: build tool OR remove references
3. 🔨 Update documentation to reference registry
4. 🔨 Achieve 0 phantoms, 100% registry coverage

**Outcome**: Clean slate, documentation matches reality

### Phase 3: Consolidation (Week 3)
1. 🔨 Migrate scattered references to registry IDs
2. 🔨 Update smart_context_loading.py to use registry
3. 🔨 Add tool lifecycle tracking (created, deprecated, deleted)
4. 🔨 Build tool discovery CLI: `maia tool list/search/info`

**Outcome**: Centralized tool management

### Phase 4: Automation (Week 4)
1. 🔨 Add pre-commit hook: validate tool references
2. 🔨 Add LaunchAgent: sync registry every 6 hours
3. 🔨 Build tool usage analytics (which tools actually used)
4. 🔨 Deprecation workflow (mark, warn, remove)

**Outcome**: Self-maintaining tool ecosystem

---

## Success Metrics

### Immediate (Post Phase 1)
- ✅ Tool registry created (282 tools documented)
- ✅ Sync script functional (discover + validate)
- ✅ save_state validation catches phantoms (0 new phantoms)

### 30 Days (Post Phase 2)
- ✅ 0 phantom dependencies (down from 83)
- ✅ 100% tool coverage in registry
- ✅ Dependency validator health: 42.4 → 90+ / 100

### 90 Days (Post Phase 3-4)
- ✅ Tool references consolidated (896 → ~200 registry refs)
- ✅ Discovery latency <1s (cached registry)
- ✅ Tool utilization tracked (identify unused tools)
- ✅ Zero "can't find tool" user reports

---

## Open Questions

### Q1: Should registry be JSON or SQLite?
**Answer**: Start JSON (human-readable, git-trackable), migrate to SQLite if >1000 tools

### Q2: How to handle tool versioning?
**Answer**: Phase 4 - add version field, support v1/v2 coexistence during migrations

### Q3: What about external tools (npm, pip packages)?
**Answer**: Separate registry section for dependencies, link to requirements.txt

### Q4: Should we auto-generate available.md from registry?
**Answer**: Yes - Phase 3, make available.md a view over registry

---

## Related Issues

### Issue #1: Phantom Dependencies (83 tools)
**Tracked By**: dependency_graph_validator.py
**Fix**: Phase 2 cleanup

### Issue #2: Reference Sprawl (896 refs, 104 files)
**Impact**: Maintenance burden, reference rot
**Fix**: Phase 3 consolidation

### Issue #3: No Tool Lifecycle Management
**Impact**: Can't deprecate tools gracefully
**Fix**: Phase 3 lifecycle tracking

### Issue #4: Smart Context Loading Inefficiency
**Impact**: Re-scans filesystem on every request
**Fix**: Phase 1 registry caching

---

## Appendix A: Phantom Tool List (Top 20)

```
1. systematic_tool_discovery.py (6 refs) - Planned Phase 82, never built
2. cloud_sync_manager.py (11 refs) - Refactored into multiple tools
3. rag_document_connectors.py (4 refs) - Design doc, not implemented
4. enterprise_monitoring_agent.py (5 refs) - Wrong location (agents not tools)
5. conversation_detector.py (3 refs) - In claude/hooks/ not claude/tools/
6. dynamic_context_loader.py (2 refs) - In claude/context/core/ not tools
7. system_status_overview.py (1 ref) - Command not tool
8. agent_voice_identity_enhancer.py (1 ref) - Abandoned experiment
9. rag_background_service.py (14 refs) - Renamed to multiple RAG tools
10. intelligent_context_cache.py (10 refs) - Absorbed into context loader
... (63 more)
```

---

## Appendix B: Tool Categories (Current)

```
claude/tools/ (282 tools)
├── sre/ (7 tools) - SRE reliability, monitoring, health checks
├── security/ (12 tools) - Security scanning, compliance, hardening
├── mcp/ (45 tools) - MCP server integrations
├── optimization/ (8 tools) - Performance, caching, efficiency
├── ai/ (18 tools) - Local LLM routing, embeddings
├── data/ (35 tools) - ETL, cleaning, analysis
├── automation/ (52 tools) - Background services, schedulers
├── integration/ (28 tools) - APIs, webhooks, connectors
├── documentation/ (15 tools) - Confluence, markdown, generators
├── personal/ (22 tools) - Email, calendar, contacts
└── (root) (40 tools) - Utilities, one-off scripts
```

**Observation**: 7 tools have `sre/` prefix, suggesting category structure works

---

## Appendix C: Reference Density Analysis

**High Reference Density** (Stable, Core Tools):
- whisper_dictation_server.py: 10 refs (voice input critical path)
- conversation_rag_ollama.py: 6 refs (knowledge management)
- launchagent_health_monitor.py: 5 refs (just created, already referenced)

**Medium Reference Density** (Active Tools):
- vtt_watcher.py: 8 refs (meeting intelligence)
- email_rag_indexer.py: 4 refs (email search)
- confluence_sync.py: 3 refs (documentation automation)

**Low/Zero Reference Density** (Unused or New):
- 180 tools with 0-1 references (64% of tools)
- Candidates for deprecation or documentation improvement

---

## Conclusion

Tool discovery failures stem from **lack of centralized registry** + **reference sprawl** + **documentation drift**. Solution: Build tool_registry.json as single source of truth, auto-sync from filesystem, validate in save_state, consolidate scattered references. 4-week phased implementation achieves 0 phantoms and self-maintaining tool ecosystem.

**Next Action**: Build tool_registry.json and sync script (Phase 1, Week 1)
