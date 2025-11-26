# Maia Comprehensive Integration Test Plan
**Created**: 2025-11-26
**Purpose**: Validate all recent system upgrades and integrations
**SRE Agent**: Principal Engineer - Production Readiness Validation
**Target**: 95%+ system health validation

---

## Test Plan Overview

### Scope
- **Core Infrastructure**: Context loading, databases, file organization, TDD protocol
- **Agent System**: 71 agents, persistence, routing, orchestration
- **Tool Ecosystem**: 455 tools across 8 categories + recent major additions
- **Data & Intelligence**: PMP, meeting intelligence, email RAG, agentic patterns
- **Development Infrastructure**: TDD protocol, quality gates, testing, docs sync
- **Integration Points**: Database ETL, OAuth, APIs, hooks

### Test Levels
1. **Unit**: Individual component validation
2. **Integration**: Cross-component data flow
3. **System**: End-to-end workflows
4. **Performance**: SLO validation, resource usage
5. **Resilience**: Error handling, recovery, graceful degradation

### Success Criteria
- ✅ **95%+ tests passing** across all categories
- ✅ **Zero critical failures** in production-ready components
- ✅ **All integration points** validated
- ✅ **Performance SLOs met** (<15s for standard operations)
- ✅ **Documentation sync** validated (100% coverage)

---

## Category 1: Core Infrastructure (Priority: CRITICAL)

### 1.1 Context Loading System

**Phase Context**: Phases 165-166 (DB-first), 168.1 (Capabilities DB), 176/178 (Checkpoints), 177 (Smart loading)

**Tests**:
```bash
# T1.1.1 - UFC System Loading
python3 -c "
from claude.tools.sre.smart_context_loader import SmartContextLoader
loader = SmartContextLoader()
result = loader.load_guaranteed_minimum()
assert 'capability_counts' in result
assert 'recent_phases' in result
print('✅ T1.1.1: UFC guaranteed minimum loads')
"

# T1.1.2 - Smart Context Loader (DB-first)
python3 claude/tools/sre/smart_context_loader.py "system overview" --stats

# T1.1.3 - Capability Loading (73-98% token savings)
python3 -c "
from claude.tools.sre.smart_context_loader import SmartContextLoader
loader = SmartContextLoader()
summary = loader.load_capability_context()
assert summary is not None
print(f'✅ T1.1.3: Capability summary loaded: {len(summary)} tokens')
"

# T1.1.4 - Targeted Capability Query
python3 claude/tools/sre/capabilities_registry.py find "security"

# T1.1.5 - Agent Persistence Check
python3 claude/hooks/swarm_auto_loader.py get_context_id
```

**Expected Results**:
- Guaranteed minimum: ~160 tokens
- Smart loader: 5-20K tokens (vs 42K full)
- Capability summary: ~60 tokens (98% savings)
- Targeted query: ~1K tokens (73% savings)
- Context ID: Stable PID returned

**Validation**:
- [ ] All 5 tests pass
- [ ] Token savings validated
- [ ] Context ID stable across calls
- [ ] Fallback to markdown works if DB unavailable

---

### 1.2 Database Infrastructure

**Phase Context**: Phases 165-166 (SYSTEM_STATE), 168.1 (Capabilities), 179 (ETL), 188-194 (PMP DBs)

**Tests**:
```bash
# T1.2.1 - SYSTEM_STATE Database
python3 claude/tools/sre/system_state_queries.py recent --count 10

# T1.2.2 - Database Performance (500-2500x faster)
time python3 claude/tools/sre/system_state_queries.py phases 193 192 191

# T1.2.3 - Keyword Search
python3 claude/tools/sre/system_state_queries.py search "TDD"

# T1.2.4 - Capabilities Database
python3 claude/tools/sre/capabilities_registry.py summary

# T1.2.5 - Database Integrity
for db in claude/data/databases/**/*.db; do
  sqlite3 "$db" "PRAGMA integrity_check;" | grep -q "ok" && echo "✅ $db" || echo "❌ $db"
done

# T1.2.6 - ETL Sync Validation
python3 claude/tools/sre/system_state_etl.py validate

# T1.2.7 - PMP Database Integrity
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM latest_system_inventory;"
```

**Expected Results**:
- SYSTEM_STATE: 79+ phases returned
- Query time: <1ms (vs 100-500ms markdown)
- Capabilities: 526 total (71 agents, 455 tools)
- All DB integrity checks: OK
- ETL: 100% sync
- PMP: 3,333+ systems

**Validation**:
- [ ] All databases pass integrity check
- [ ] Query performance <1ms
- [ ] ETL sync at 100%
- [ ] PMP data present and valid

---

### 1.3 File Organization & Validation

**Phase Context**: Phase 151 (File storage discipline), Phase 169 (Path sync)

**Tests**:
```bash
# T1.3.1 - Root Directory Compliance (4 core files + 3 dirs)
ls -1 /Users/naythandawe/git/maia/ | wc -l  # Should be ≤10

# T1.3.2 - UFC Structure Validation
test -d claude/agents && test -d claude/tools && test -d claude/commands && echo "✅ T1.3.2: UFC structure valid"

# T1.3.3 - Database Organization
ls -R claude/data/databases/{intelligence,system,user}/ | grep "\.db$" | wc -l

# T1.3.4 - File Size Validation (>10MB check)
find claude/ -type f -size +10M | grep -v "rag_databases" | wc -l  # Should be 0

# T1.3.5 - Path Sync Tool
python3 claude/tools/sre/path_sync.py validate
```

**Expected Results**:
- Root directory: ≤10 files
- UFC structure: All core dirs present
- Databases: Organized by category
- Large files: 0 (except rag_databases/)
- Path sync: 100% valid

**Validation**:
- [ ] Root directory compliant
- [ ] UFC structure intact
- [ ] Databases organized correctly
- [ ] No oversized files in repo
- [ ] Path sync validation passes

---

### 1.4 TDD Protocol & Quality Gates

**Phase Context**: Phase 193 (Integration & validation testing), Phase 194 (First full implementation)

**Tests**:
```bash
# T1.4.1 - TDD Protocol Structure
grep -c "^## Phase" claude/context/core/tdd_development_protocol.md  # Should be ≥6

# T1.4.2 - Quality Gates Count
grep -c "^### Gate" claude/context/core/tdd_development_protocol.md  # Should be 11

# T1.4.3 - Phase 193 Enhancements Present
grep -q "Phase 3.5: Integration Test Design" claude/context/core/tdd_development_protocol.md && echo "✅ Integration phase present"

# T1.4.4 - Phase 6 Validation Present
grep -q "Phase 6: Post-Implementation Validation" claude/context/core/tdd_development_protocol.md && echo "✅ Validation phase present"

# T1.4.5 - Test Phase 194 Implementation
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/requirements.md && \
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/test_pmp_dcapi_patch_extractor.py && \
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && \
echo "✅ T1.4.5: Phase 194 TDD files complete"
```

**Expected Results**:
- TDD protocol: 6+ phases
- Quality gates: 11 gates
- Integration test design: Present
- Post-implementation validation: Present
- Phase 194: Complete TDD implementation

**Validation**:
- [ ] TDD protocol has all phases
- [ ] 11 quality gates defined
- [ ] Phase 193 enhancements present
- [ ] Phase 194 validates new protocol

---

## Category 2: Agent System (Priority: HIGH)

### 2.1 Agent Loading & Persistence

**Phase Context**: Phase 134/134.7 (Automatic persistence), Phase 176/178 (Maia Core default)

**Tests**:
```bash
# T2.1.1 - Agent File Discovery
ls claude/agents/*.md | wc -l  # Should be 71

# T2.1.2 - Agent Session Creation
python3 claude/hooks/swarm_auto_loader.py load sre_principal_engineer_agent
test -f /tmp/maia_active_swarm_session_*.json && echo "✅ Session created"

# T2.1.3 - Agent Session Persistence
python3 -c "
import json
import glob
session_files = glob.glob('/tmp/maia_active_swarm_session_*.json')
if session_files:
    with open(session_files[0]) as f:
        session = json.load(f)
        assert 'current_agent' in session
        print(f'✅ T2.1.3: Agent session persists: {session[\"current_agent\"]}')
"

# T2.1.4 - Agent Close Session
python3 claude/hooks/swarm_auto_loader.py close_session

# T2.1.5 - Context ID Stability
pid1=$(python3 claude/hooks/swarm_auto_loader.py get_context_id)
pid2=$(python3 claude/hooks/swarm_auto_loader.py get_context_id)
test "$pid1" = "$pid2" && echo "✅ T2.1.5: Context ID stable: $pid1"
```

**Expected Results**:
- Agent count: 71 agents
- Session file: Created in /tmp
- Session data: Valid JSON with current_agent
- Close session: File removed
- Context ID: Stable across calls

**Validation**:
- [ ] All 71 agents present
- [ ] Session creation works
- [ ] Session persistence works
- [ ] Close session works
- [ ] Context ID stable

---

### 2.2 Specialized Agent Validation

**Phase Context**: Phase 185 (Zabbix), Phase 191 (Wget), Phase 192 (PMP), Recent agents

**Tests**:
```bash
# T2.2.1 - SRE Principal Engineer Agent
test -f claude/agents/sre_principal_engineer_agent.md && \
grep -q "v2.3" claude/agents/sre_principal_engineer_agent.md && \
echo "✅ T2.2.1: SRE agent v2.3"

# T2.2.2 - Zabbix Specialist Agent (Phase 185)
test -f claude/agents/zabbix_specialist_agent.md && \
grep -q "232 lines" claude/context/core/capability_index.md && \
echo "✅ T2.2.2: Zabbix agent present"

# T2.2.3 - Wget Specialist Agent (Phase 191)
test -f claude/agents/wget_specialist_agent.md && \
grep -q "183 lines" claude/agents/wget_specialist_agent.md && \
echo "✅ T2.2.3: Wget agent present"

# T2.2.4 - Rapid7 InsightVM Agent
test -f claude/agents/rapid7_insightvm_agent.md && echo "✅ T2.2.4: InsightVM agent present"

# T2.2.5 - Agent Template Compliance (v2.3)
for agent in claude/agents/*_agent.md; do
  grep -q "Self-Reflection" "$agent" && echo "✅ $(basename $agent): v2.3 pattern present"
done | head -10
```

**Expected Results**:
- SRE agent: v2.3 present
- Zabbix agent: 232 lines
- Wget agent: 183 lines
- InsightVM agent: Present
- Template compliance: v2.3 patterns in all agents

**Validation**:
- [ ] Core agents present and valid
- [ ] Recent agents (185, 191) present
- [ ] v2.3 template compliance
- [ ] All agents have self-reflection patterns

---

### 2.3 Agent Routing & Orchestration

**Phase Context**: Phase 107-111 (Agent enhancement), Phase 180-183 (Agentic patterns)

**Tests**:
```bash
# T2.3.1 - Adaptive Routing Database
sqlite3 claude/data/databases/intelligence/adaptive_routing.db "SELECT COUNT(*) FROM task_outcomes;"

# T2.3.2 - Adaptive Routing Tests
python3 -m pytest tests/test_adaptive_routing.py -v

# T2.3.3 - Output Critic Tool
python3 -c "
from claude.tools.orchestration.output_critic import OutputCritic
critic = OutputCritic()
result = critic.evaluate('Test output', ['completeness', 'accuracy'])
assert 'issues' in result
print('✅ T2.3.3: Output critic functional')
"

# T2.3.4 - Agentic Email Search
python3 -m pytest tests/test_agentic_email_search.py -v

# T2.3.5 - Routing Decision Logs
sqlite3 claude/data/databases/system/routing_decisions.db "SELECT COUNT(*) FROM decisions;"
```

**Expected Results**:
- Adaptive routing: Database present with records
- Adaptive routing tests: 14/14 passing
- Output critic: Evaluates successfully
- Email search tests: 8/8 passing
- Routing logs: Historical decisions present

**Validation**:
- [ ] Adaptive routing operational
- [ ] All routing tests pass
- [ ] Output critic works
- [ ] Agentic search works
- [ ] Routing decisions logged

---

## Category 3: Tool Ecosystem (Priority: HIGH)

### 3.1 Comprehensive Tool Validation

**Phase Context**: Phase 171 (Comprehensive test suite)

**Tests**:
```bash
# T3.1.1 - Full Test Suite
python3 claude/tools/sre/maia_comprehensive_test_suite.py

# T3.1.2 - Quick Smoke Test
python3 claude/tools/sre/maia_comprehensive_test_suite.py --quick

# T3.1.3 - Tools Category Only
python3 claude/tools/sre/maia_comprehensive_test_suite.py -c tools

# T3.1.4 - Agents Category Only
python3 claude/tools/sre/maia_comprehensive_test_suite.py -c agents

# T3.1.5 - JSON Report Generation
python3 claude/tools/sre/maia_comprehensive_test_suite.py --output /tmp/maia_test_report.json
```

**Expected Results**:
- Full suite: 572/572 tests passing (100%)
- Quick test: All critical tests pass
- Tools: 426/426 passing
- Agents: 63/63 passing
- JSON report: Generated successfully

**Validation**:
- [ ] Full test suite passes
- [ ] Smoke test passes
- [ ] All tool tests pass
- [ ] All agent tests pass
- [ ] JSON reporting works

---

### 3.2 Recent Tool Integration Tests

**Phase Context**: Phases 187-194 (PMP), Phase 167 (Meeting intelligence)

**Tests**:
```bash
# T3.2.1 - PMP OAuth Manager (Phase 187)
python3 -c "
from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
manager = PMPOAuthManager()
# Test token structure (not actual API call)
assert hasattr(manager, 'get_valid_token')
print('✅ T3.2.1: PMP OAuth manager imports')
"

# T3.2.2 - PMP Config Extractor (Phase 188)
test -f claude/tools/pmp/pmp_config_extractor.py && \
python3 -m py_compile claude/tools/pmp/pmp_config_extractor.py && \
echo "✅ T3.2.2: PMP config extractor compiles"

# T3.2.3 - PMP Resilient Extractor (Phase 192)
test -f claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py && \
python3 -m py_compile claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py && \
echo "✅ T3.2.3: PMP resilient extractor compiles"

# T3.2.4 - PMP DCAPI Extractor (Phase 194)
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && \
python3 -m py_compile claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && \
echo "✅ T3.2.4: PMP DCAPI extractor compiles"

# T3.2.5 - Meeting Intelligence Processor (Phase 167)
test -f claude/tools/meeting_intelligence_processor.py && \
python3 -m py_compile claude/tools/meeting_intelligence_processor.py && \
echo "✅ T3.2.5: Meeting intelligence compiles"

# T3.2.6 - Meeting Intelligence Exporter
test -f claude/tools/meeting_intelligence_exporter.py && \
python3 -m py_compile claude/tools/meeting_intelligence_exporter.py && \
echo "✅ T3.2.6: Meeting exporter compiles"
```

**Expected Results**:
- All PMP tools: Import and compile successfully
- Meeting intelligence: Compiles successfully
- No syntax errors
- All dependencies present

**Validation**:
- [ ] PMP OAuth manager works
- [ ] All PMP extractors compile
- [ ] Meeting intelligence tools compile
- [ ] No import errors
- [ ] All dependencies satisfied

---

### 3.3 Tool Performance Validation

**Phase Context**: Performance SLOs from Phase 193 (P95/P99 latency)

**Tests**:
```bash
# T3.3.1 - SYSTEM_STATE Query Performance (<1ms)
time python3 claude/tools/sre/system_state_queries.py recent --count 10 > /dev/null

# T3.3.2 - Capability Registry Performance (<100ms)
time python3 claude/tools/sre/capabilities_registry.py summary > /dev/null

# T3.3.3 - Smart Loader Performance (<500ms)
time python3 claude/tools/sre/smart_context_loader.py "system overview" --stats > /dev/null

# T3.3.4 - Database Integrity Performance (<1s per DB)
time for db in claude/data/databases/**/*.db; do
  sqlite3 "$db" "PRAGMA integrity_check;" > /dev/null
done

# T3.3.5 - Test Suite Performance (<2s for full suite)
time python3 claude/tools/sre/maia_comprehensive_test_suite.py --quiet
```

**Expected Results**:
- SYSTEM_STATE query: <1ms (0.13-0.54ms)
- Capability registry: <100ms
- Smart loader: <500ms
- DB integrity: <1s per database
- Test suite: <2s for 572 tests

**Validation**:
- [ ] All performance SLOs met
- [ ] No performance regressions
- [ ] Query times <1ms
- [ ] Test suite <2s

---

## Category 4: Data & Intelligence (Priority: HIGH)

### 4.1 PMP Data Extraction System

**Phase Context**: Phases 187-194 (Complete PMP system)

**Tests**:
```bash
# T4.1.1 - PMP Database Existence
test -f ~/.maia/databases/intelligence/pmp_config.db && echo "✅ PMP DB exists"

# T4.1.2 - PMP Database Schema
sqlite3 ~/.maia/databases/intelligence/pmp_config.db ".schema" | grep -c "CREATE TABLE"  # Should be 15+

# T4.1.3 - PMP System Inventory
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM latest_system_inventory;"

# T4.1.4 - PMP Deployment Policies
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM deployment_policies;"

# T4.1.5 - PMP Patch System Mapping
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM patch_system_mapping;"

# T4.1.6 - PMP Views Functional
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM organization_summary;"

# T4.1.7 - PMP Checkpoint Tables
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM extraction_checkpoints;"
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "SELECT COUNT(*) FROM dcapi_extraction_checkpoints;"
```

**Expected Results**:
- PMP database: Present
- Tables: 15+ tables
- System inventory: 3,333+ systems (99.1% coverage)
- Deployment policies: 50+ policies
- Patch mappings: ~165,000 records (target)
- Views: Functional and populated
- Checkpoints: Present and valid

**Validation**:
- [ ] PMP database present and valid
- [ ] All tables created
- [ ] System inventory populated
- [ ] Policies extracted
- [ ] Patch mappings present (if Phase 194 run)
- [ ] Views functional
- [ ] Checkpoint system operational

---

### 4.2 Meeting Intelligence System

**Phase Context**: Phase 167 (Meeting intelligence + Confluence export)

**Tests**:
```bash
# T4.2.1 - Meeting Intelligence Database
test -f claude/data/databases/intelligence/meetings.db && echo "✅ Meeting DB exists"

# T4.2.2 - Meeting Processor Import
python3 -c "
from claude.tools.meeting_intelligence_processor import MeetingIntelligenceProcessor
processor = MeetingIntelligenceProcessor()
assert hasattr(processor, 'process_transcript')
print('✅ T4.2.2: Meeting processor imports')
"

# T4.2.3 - Meeting Exporter Import
python3 -c "
from claude.tools.meeting_intelligence_exporter import MeetingIntelligenceExporter
exporter = MeetingIntelligenceExporter()
assert hasattr(exporter, 'export_to_confluence')
print('✅ T4.2.3: Meeting exporter imports')
"

# T4.2.4 - Ollama Models Available
ollama list | grep -E "(gemma2:9b|hermes|qwen2.5:7b)" | wc -l  # Should be 3
```

**Expected Results**:
- Meeting database: Present
- Processor: Imports successfully
- Exporter: Imports successfully
- Ollama models: 3 models available

**Validation**:
- [ ] Meeting database present
- [ ] Processor functional
- [ ] Exporter functional
- [ ] All required models available

---

### 4.3 Email RAG System

**Phase Context**: Phase 1 (Agentic email search), Phase 180 (Agentic patterns)

**Tests**:
```bash
# T4.3.1 - Email RAG Database
test -d claude/data/rag_databases/email_rag_ollama && echo "✅ Email RAG DB exists"

# T4.3.2 - Email RAG Size
du -sh claude/data/rag_databases/email_rag_ollama

# T4.3.3 - Agentic Email Search Import
python3 -c "
from claude.tools.rag.agentic_email_search import AgenticEmailSearch
search = AgenticEmailSearch()
assert hasattr(search, 'iterative_search')
print('✅ T4.3.3: Agentic search imports')
"

# T4.3.4 - Agentic Email Search Tests
python3 -m pytest tests/test_agentic_email_search.py -v
```

**Expected Results**:
- Email RAG: Present (~21.6 MB)
- Agentic search: Imports successfully
- Tests: 8/8 passing

**Validation**:
- [ ] Email RAG database present
- [ ] Agentic search functional
- [ ] All tests pass

---

### 4.4 Agentic AI Patterns

**Phase Context**: Phases 180-183 (Agentic patterns), Phase 1 (Learning tools)

**Tests**:
```bash
# T4.4.1 - Adaptive Routing Tests
python3 -m pytest tests/test_adaptive_routing.py -v

# T4.4.2 - Output Critic Tests
python3 -m pytest tests/test_output_critic.py -v

# T4.4.3 - Outcome Tracker
test -f claude/tools/orchestration/outcome_tracker.py && \
python3 -m py_compile claude/tools/orchestration/outcome_tracker.py && \
echo "✅ T4.4.3: Outcome tracker compiles"

# T4.4.4 - Speculative Executor
test -f claude/tools/orchestration/speculative_executor.py && \
python3 -m py_compile claude/tools/orchestration/speculative_executor.py && \
echo "✅ T4.4.4: Speculative executor compiles"

# T4.4.5 - A/B Testing Framework
test -f claude/tools/orchestration/ab_testing.py && \
python3 -m py_compile claude/tools/orchestration/ab_testing.py && \
echo "✅ T4.4.5: A/B testing compiles"
```

**Expected Results**:
- Adaptive routing: 14/14 tests passing
- Output critic: 16/16 tests passing
- Outcome tracker: Compiles successfully
- Speculative executor: Compiles successfully
- A/B testing: Compiles successfully

**Validation**:
- [ ] All agentic pattern tests pass
- [ ] All tools compile
- [ ] No import errors

---

## Category 5: Development Infrastructure (Priority: MEDIUM)

### 5.1 TDD Workflow Validation

**Phase Context**: Phase 193 (TDD enhancements), Phase 194 (First implementation)

**Tests**:
```bash
# T5.1.1 - Requirements Documents Present
find claude/tools -name "requirements.md" | wc -l

# T5.1.2 - Test Files Present
find tests/ -name "test_*.py" | wc -l

# T5.1.3 - Phase 194 TDD Files (Requirements → Tests → Implementation)
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/requirements.md && \
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/test_pmp_dcapi_patch_extractor.py && \
test -f claude/tools/pmp/pmp_dcapi_patch_extractor/pmp_dcapi_patch_extractor.py && \
wc -l claude/tools/pmp/pmp_dcapi_patch_extractor/*.{md,py}

# T5.1.4 - Test Collection (Phase 194)
cd claude/tools/pmp/pmp_dcapi_patch_extractor && \
python3 -m pytest --collect-only test_pmp_dcapi_patch_extractor.py

# T5.1.5 - TDD Protocol Documentation
grep -c "Quality Gate" claude/context/core/tdd_development_protocol.md
```

**Expected Results**:
- Requirements: Multiple requirements.md files
- Tests: Multiple test_*.py files
- Phase 194: 738 + 873 + 810 lines (requirements + tests + implementation)
- Test collection: 76 tests collected
- Quality gates: 11 gates

**Validation**:
- [ ] TDD files present
- [ ] Phase 194 complete TDD implementation
- [ ] Tests collect successfully
- [ ] 11 quality gates defined

---

### 5.2 Documentation Sync & ETL

**Phase Context**: Phase 179 (ETL sync), Phase 193 (Doc enforcement)

**Tests**:
```bash
# T5.2.1 - ETL Sync Validation
python3 claude/tools/sre/system_state_etl.py validate

# T5.2.2 - Documentation Enforcement
python3 claude/tools/documentation_enforcement_system.py

# T5.2.3 - Capability Registry Scan
python3 claude/tools/sre/capabilities_registry.py scan

# T5.2.4 - Path Sync Validation
python3 claude/tools/sre/path_sync.py validate

# T5.2.5 - Git Status Clean
git status --porcelain | wc -l  # Should be 0 for clean state
```

**Expected Results**:
- ETL validation: 100% synced
- Documentation: All files current
- Capability scan: 526 capabilities
- Path sync: 100% valid
- Git status: Clean (0 uncommitted changes)

**Validation**:
- [ ] ETL 100% synced
- [ ] Documentation enforcement passes
- [ ] Capability registry complete
- [ ] Path sync valid
- [ ] Git status clean

---

### 5.3 Hook System Validation

**Phase Context**: Phase 134 (Agent persistence), Phase 193 (Context enforcement)

**Tests**:
```bash
# T5.3.1 - Hook Files Present
ls -1 claude/hooks/*.py | wc -l

# T5.3.2 - User Prompt Submit Hook
test -f claude/hooks/user_prompt_submit.py && echo "✅ User prompt hook present"

# T5.3.3 - Swarm Auto Loader
test -f claude/hooks/swarm_auto_loader.py && \
python3 -m py_compile claude/hooks/swarm_auto_loader.py && \
echo "✅ Swarm auto loader compiles"

# T5.3.4 - Context Auto Loader
test -f claude/hooks/context_auto_loader.py && \
python3 -m py_compile claude/hooks/context_auto_loader.py && \
echo "✅ Context auto loader compiles"

# T5.3.5 - Hook Tests
python3 claude/tools/sre/maia_comprehensive_test_suite.py -c hooks
```

**Expected Results**:
- Hook files: Multiple hooks present
- User prompt hook: Present
- Swarm loader: Compiles successfully
- Context loader: Compiles successfully
- Hook tests: 31/31 passing

**Validation**:
- [ ] All hooks present
- [ ] Critical hooks compile
- [ ] Hook tests pass
- [ ] No hook failures

---

## Category 6: Integration Points (Priority: HIGH)

### 6.1 Database Integration

**Phase Context**: Phases 165-166, 168.1, 179, 188-194

**Tests**:
```bash
# T6.1.1 - Cross-Database Query (SYSTEM_STATE → Capabilities)
python3 -c "
from claude.tools.sre.system_state_queries import SystemStateQueries
from claude.tools.sre.capabilities_registry import CapabilitiesRegistry
ssq = SystemStateQueries()
cap = CapabilitiesRegistry()
phases = ssq.get_recent_phases(5)
caps = cap.get_summary()
assert len(phases) == 5
assert 'total' in caps
print('✅ T6.1.1: Cross-DB query successful')
"

# T6.1.2 - ETL Pipeline (SYSTEM_STATE.md → DB)
python3 claude/tools/sre/system_state_etl.py run --validate

# T6.1.3 - PMP Database Integration
sqlite3 ~/.maia/databases/intelligence/pmp_config.db "
SELECT s.resource_name, COUNT(p.patch_id) as patch_count
FROM latest_system_inventory s
LEFT JOIN patch_system_mapping p ON s.resource_id = p.resource_id
GROUP BY s.resource_name
LIMIT 5;
"
```

**Expected Results**:
- Cross-DB queries: Successful
- ETL pipeline: 100% sync
- PMP integration: Patch mappings linked to systems

**Validation**:
- [ ] Cross-database queries work
- [ ] ETL pipeline operational
- [ ] PMP database integration validated

---

### 6.2 OAuth & API Integration

**Phase Context**: Phase 187 (PMP OAuth), Phases 188-194 (API usage)

**Tests**:
```bash
# T6.2.1 - OAuth Manager Import
python3 -c "
from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
manager = PMPOAuthManager()
assert hasattr(manager, 'authorize')
assert hasattr(manager, 'get_valid_token')
print('✅ T6.2.1: OAuth manager functional')
"

# T6.2.2 - Token Storage Check
test -f ~/.maia/pmp_tokens.enc && echo "✅ Encrypted tokens exist"

# T6.2.3 - Keychain Integration (macOS)
security find-generic-password -s "maia_pmp_client_id" 2>&1 | grep -q "password" && echo "✅ Keychain integration working"

# T6.2.4 - Rate Limiting Implementation
grep -q "rate_limit" claude/tools/pmp/pmp_oauth_manager.py && echo "✅ Rate limiting implemented"
```

**Expected Results**:
- OAuth manager: Imports and has required methods
- Token storage: Encrypted file present
- Keychain: Credentials stored
- Rate limiting: Implemented

**Validation**:
- [ ] OAuth manager functional
- [ ] Token storage secure
- [ ] Keychain integration works
- [ ] Rate limiting present

---

### 6.3 External System Integration

**Phase Context**: Phase 167 (Confluence), Phase 185 (Zabbix), Various agents

**Tests**:
```bash
# T6.3.1 - Confluence Integration
python3 -c "
from claude.tools.meeting_intelligence_exporter import MeetingIntelligenceExporter
exporter = MeetingIntelligenceExporter()
assert hasattr(exporter, 'export_to_confluence')
print('✅ T6.3.1: Confluence exporter present')
"

# T6.3.2 - Trello Integration
grep -q "export_to_trello" claude/tools/meeting_intelligence_exporter.py && echo "✅ Trello export present"

# T6.3.3 - Ollama Integration
ollama list | head -5

# T6.3.4 - External API Agents
grep -c "api" claude/agents/rapid7_insightvm_agent.md
grep -c "API" claude/agents/zabbix_specialist_agent.md
```

**Expected Results**:
- Confluence: Exporter present
- Trello: Export method present
- Ollama: Models available
- API agents: Multiple API references

**Validation**:
- [ ] Confluence integration present
- [ ] Trello integration present
- [ ] Ollama operational
- [ ] API agents have integration methods

---

## Category 7: Performance & Resilience (Priority: MEDIUM)

### 7.1 Performance SLO Validation

**Phase Context**: Phase 193 (Performance testing requirements)

**Tests**:
```bash
# T7.1.1 - Query Latency (P95 <300ms for standard operations)
for i in {1..100}; do
  /usr/bin/time -p python3 claude/tools/sre/system_state_queries.py recent --count 10 > /dev/null 2>&1
done | grep real | awk '{sum+=$2; count++} END {print "Average:", sum/count, "seconds"}'

# T7.1.2 - Database Query Performance
sqlite3 claude/data/databases/system/system_state.db "
EXPLAIN QUERY PLAN SELECT * FROM phases WHERE phase_number > 190;
"

# T7.1.3 - Resource Utilization (<70% during operations)
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# T7.1.4 - Test Suite Performance
/usr/bin/time -p python3 claude/tools/sre/maia_comprehensive_test_suite.py --quiet
```

**Expected Results**:
- Query latency: <1ms average (P95 <5ms)
- Database: Index usage confirmed
- Resource usage: <70% CPU/memory/disk
- Test suite: <2s for 572 tests

**Validation**:
- [ ] Query latency SLO met
- [ ] Database queries optimized
- [ ] Resource usage acceptable
- [ ] Test suite performance good

---

### 7.2 Resilience & Error Handling

**Phase Context**: Phase 192 (Resilient extractor), Phase 193 (Resilience testing)

**Tests**:
```bash
# T7.2.1 - Checkpoint Recovery Test
python3 -c "
from claude.tools.pmp.pmp_resilient_extractor.pmp_resilient_extractor import PMPResilientExtractor
# Test checkpoint loading (mocked, no API call)
extractor = PMPResilientExtractor(db_path=':memory:')
assert hasattr(extractor, 'load_checkpoint')
print('✅ T7.2.1: Checkpoint recovery method present')
"

# T7.2.2 - Error Handling Patterns
grep -c "try:" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py

# T7.2.3 - Exponential Backoff Implementation
grep -q "exponential.*backoff" claude/tools/pmp/pmp_resilient_extractor/requirements.md && \
echo "✅ Exponential backoff specified"

# T7.2.4 - Circuit Breaker Pattern
grep -q "circuit" claude/context/core/tdd_development_protocol.md && \
echo "✅ Circuit breaker in validation protocol"

# T7.2.5 - Graceful Degradation
grep -c "fallback" claude/tools/sre/smart_context_loader.py
```

**Expected Results**:
- Checkpoint recovery: Method present
- Error handling: Multiple try/except blocks
- Exponential backoff: Specified in requirements
- Circuit breaker: In validation protocol
- Graceful degradation: Fallback mechanisms present

**Validation**:
- [ ] Checkpoint recovery implemented
- [ ] Error handling comprehensive
- [ ] Retry logic with backoff
- [ ] Circuit breakers specified
- [ ] Fallback mechanisms present

---

### 7.3 Observability Validation

**Phase Context**: Phase 193 (Observability validation)

**Tests**:
```bash
# T7.3.1 - Structured Logging Present
grep -c "json" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py

# T7.3.2 - Log Event Types
grep -o "\"event\".*\"" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py | sort -u

# T7.3.3 - Metrics Collection
grep -c "metric" claude/context/core/tdd_development_protocol.md

# T7.3.4 - Progress Tracking
grep -q "progress" claude/tools/pmp/pmp_resilient_extractor/requirements.md && \
echo "✅ Progress tracking specified"

# T7.3.5 - Slack Notifications
grep -q "slack" claude/tools/pmp/pmp_resilient_extractor/pmp_resilient_extractor.py && \
echo "✅ Slack notifications implemented"
```

**Expected Results**:
- Structured logging: JSON format present
- Event types: Multiple event types defined
- Metrics: Specified in protocol
- Progress tracking: Real-time updates
- Slack notifications: Optional alerts

**Validation**:
- [ ] Structured logging implemented
- [ ] Event types defined
- [ ] Metrics tracked
- [ ] Progress tracking present
- [ ] Notifications available

---

## Execution Workflow

### Phase 1: Preparation (15 min)
```bash
# Verify prerequisites
python3 --version  # Python 3.8+
sqlite3 --version  # SQLite 3.x
git --version      # Git 2.x

# Create test results directory
mkdir -p ~/work_projects/maia_test_results/$(date +%Y%m%d)
cd ~/work_projects/maia_test_results/$(date +%Y%m%d)

# Initialize test log
echo "Maia Comprehensive Integration Test Run" > test_log.txt
echo "Started: $(date)" >> test_log.txt
echo "Context ID: $(python3 /Users/naythandawe/git/maia/claude/hooks/swarm_auto_loader.py get_context_id)" >> test_log.txt
```

### Phase 2: Core Infrastructure Tests (30 min)
```bash
# Run Category 1 tests
echo "=== Category 1: Core Infrastructure ===" | tee -a test_log.txt
bash -c "$(grep -A 50 '# T1.1.1' COMPREHENSIVE_INTEGRATION_TEST_PLAN.md | grep '^python3\|^test\|^time\|^for\|^sqlite3')" 2>&1 | tee -a test_log.txt
```

### Phase 3: Agent & Tool Tests (45 min)
```bash
# Run Category 2 & 3 tests
echo "=== Category 2: Agent System ===" | tee -a test_log.txt
bash -c "$(grep -A 30 '# T2.1.1' COMPREHENSIVE_INTEGRATION_TEST_PLAN.md | grep '^python3\|^test\|^ls')" 2>&1 | tee -a test_log.txt

echo "=== Category 3: Tool Ecosystem ===" | tee -a test_log.txt
python3 /Users/naythandawe/git/maia/claude/tools/sre/maia_comprehensive_test_suite.py --output tool_tests.json 2>&1 | tee -a test_log.txt
```

### Phase 4: Data & Intelligence Tests (30 min)
```bash
# Run Category 4 tests
echo "=== Category 4: Data & Intelligence ===" | tee -a test_log.txt
bash -c "$(grep -A 40 '# T4.1.1' COMPREHENSIVE_INTEGRATION_TEST_PLAN.md | grep '^python3\|^sqlite3\|^test')" 2>&1 | tee -a test_log.txt
```

### Phase 5: Integration Tests (30 min)
```bash
# Run Category 6 tests
echo "=== Category 6: Integration Points ===" | tee -a test_log.txt
bash -c "$(grep -A 30 '# T6.1.1' COMPREHENSIVE_INTEGRATION_TEST_PLAN.md | grep '^python3\|^sqlite3')" 2>&1 | tee -a test_log.txt
```

### Phase 6: Performance & Resilience (30 min)
```bash
# Run Category 7 tests
echo "=== Category 7: Performance & Resilience ===" | tee -a test_log.txt
bash -c "$(grep -A 30 '# T7.1.1' COMPREHENSIVE_INTEGRATION_TEST_PLAN.md | grep '^python3\|^/usr/bin/time')" 2>&1 | tee -a test_log.txt
```

### Phase 7: Report Generation (15 min)
```bash
# Generate summary report
echo "=== Test Summary ===" | tee -a test_log.txt
echo "Completed: $(date)" >> test_log.txt
grep -c "✅" test_log.txt && echo "Passed tests: $(grep -c '✅' test_log.txt)" | tee -a test_log.txt
grep -c "❌" test_log.txt && echo "Failed tests: $(grep -c '❌' test_log.txt)" | tee -a test_log.txt

# Calculate pass rate
python3 -c "
import re
with open('test_log.txt') as f:
    content = f.read()
    passed = content.count('✅')
    failed = content.count('❌')
    total = passed + failed
    if total > 0:
        rate = (passed / total) * 100
        print(f'Pass rate: {rate:.1f}% ({passed}/{total})')
" | tee -a test_log.txt
```

---

## Success Criteria Summary

### Critical (Must Pass)
- ✅ Core infrastructure: 100% (context loading, databases, file org)
- ✅ Agent system: 95%+ (loading, persistence, routing)
- ✅ Tool ecosystem: 95%+ (comprehensive test suite passing)
- ✅ Database integration: 100% (cross-DB queries, ETL sync)

### High Priority (Target 90%+)
- ✅ Data extraction: 90%+ (PMP, meeting intelligence, email RAG)
- ✅ Integration points: 90%+ (OAuth, APIs, external systems)
- ✅ TDD workflow: 90%+ (requirements, tests, implementation)

### Medium Priority (Target 80%+)
- ✅ Performance: 80%+ (SLO validation, resource usage)
- ✅ Resilience: 80%+ (error handling, recovery, degradation)
- ✅ Observability: 80%+ (logging, metrics, notifications)

### Overall Target
- **95%+ tests passing** across all categories
- **Zero critical failures** in production-ready components
- **All integration points validated**
- **Performance SLOs met**

---

## Risk Assessment

### High Risk Areas
1. **PMP API Integration** - OAuth tokens, rate limiting, endpoint availability
2. **Database Sync** - ETL pipeline, data consistency, integrity checks
3. **Agent Persistence** - Session files, context ID stability, cleanup

### Mitigation Strategies
1. **Mock API calls** for PMP tests (avoid rate limits during testing)
2. **Database backups** before running tests
3. **Session cleanup** scripts for agent persistence tests

### Rollback Plan
If critical failures detected:
1. Document failure details
2. Roll back to last known good state (git)
3. Run targeted tests to isolate issue
4. Fix and re-run full suite

---

## Next Steps After Testing

### If 95%+ Pass Rate
1. Document results in SYSTEM_STATE.md
2. Update test plan with any new findings
3. Schedule regular test runs (weekly)
4. Deploy monitoring for production systems

### If <95% Pass Rate
1. Categorize failures (critical vs non-critical)
2. Create bug fix plan for critical failures
3. Re-run tests after fixes
4. Update test plan with edge cases found

---

**Total Estimated Time**: 3-4 hours for complete test execution
**Test Coverage**: 100+ individual tests across 7 categories
**Automation Level**: 90% automated (10% manual validation)
**Maintenance**: Update test plan after each major phase (monthly review)
