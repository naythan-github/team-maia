# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository
**GitHub**: https://github.com/naythan-orro/maia

## Requirements
- **Python 3.11+** (required)
- **pip** (Python package manager)
- **Ollama** (optional, for local LLM features - `/codellama`, `/starcoder`, `/local`)

---

# MAIA - My AI Agent v2.0

## Quick Start
```
/init           → UFC + default agent (SRE)
/init [agent]   → UFC + specific agent
/close-session  → End agent session + learning capture
```

---

## Development Commands

```bash
# Setup (first time)
./setup.sh                          # Installs deps, sets MAIA_ROOT

# Testing
pytest tests/ -v --tb=short         # Run all tests
pytest tests/test_foo.py -v         # Run single test file
pytest tests/test_foo.py::test_bar  # Run specific test function
pytest tests/ -k "keyword"          # Run tests matching keyword

# Linting
ruff check claude/tools --select=E,F,W --ignore=E501

# Verify installation
python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(MAIA_ROOT)"
```

### Pre-commit Hooks
TDD pre-commit hook blocks commits when features are failing. Bypass with `git commit --no-verify` (requires justification in `claude/data/TDD_EXEMPTIONS.md`).

---

## Architecture

```
maia/
├── claude/                    # Core system
│   ├── agents/               # 90+ specialist agents (markdown prompts)
│   ├── commands/             # Slash commands (markdown definitions)
│   ├── context/              # UFC system + context loading
│   │   └── core/             # Identity, protocols, capability index
│   ├── data/                 # Databases, user prefs, logs
│   │   └── databases/        # SQLite DBs (intelligence/system/user)
│   ├── hooks/                # Pre-commit, enforcement, auto-loaders
│   └── tools/                # Python tools organized by domain
│       ├── core/             # Paths, base utilities
│       ├── sre/              # SRE tools (smart_context_loader, save_state)
│       ├── learning/         # PAI v2 learning system
│       └── [domain]/         # Other domains (security, pmp, etc.)
├── tests/                    # Pytest tests mirroring tools structure
├── scripts/                  # Shell scripts
└── SYSTEM_STATE.md          # Phase history (use DB queries, not direct reads)
```

**Key architectural patterns:**
- **Agents** (markdown) orchestrate **Tools** (Python) - agents define behavior, tools execute
- **UFC System** (`claude/context/ufc_system.md`) must load before any response
- **Session persistence** via `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json`
- **Smart context loading** reduces token usage (5-30K vs 42K+ full file)
- **DB-first queries** for SYSTEM_STATE (500-2500x faster than markdown parsing)

---

## Context Loading Protocol

**MANDATORY**: UFC system loads FIRST, always. Use `/init` for guaranteed sequence.

| Step | Action | File/Command |
|------|--------|--------------|
| 1 | Load UFC | `claude/context/ufc_system.md` |
| 2 | Get context ID | `python3 claude/hooks/swarm_auto_loader.py get_context_id` |
| 3 | Check session | `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json` |
| 4 | Load agent | Session agent OR `claude/data/user_preferences.json` → `default_agent` OR `sre_principal_engineer_agent` |
| 5 | Start learning | `python3 -c "from claude.tools.learning.session import get_session_manager; m=get_session_manager(); m.start_session(context_id='ID', initial_query='QUERY', agent_used='AGENT')"` |

**⚠️ All 5 steps are mandatory.** Skipping step 5 breaks learning capture.

**Full protocol**: `claude/commands/init.md`

---

## Working Principles

| # | Principle | Action | Reference |
|---|-----------|--------|-----------|
| 1 | **Read Context First** | Hydrate before acting | - |
| 2 | **Use Existing Tools** | Check before creating | `find_capability.py` (DB query) |
| 3 | **Solve Once** | Turn solutions into modules | - |
| 4 | **Fix Forward** | No Band-Aid solutions, complete fixes | - |
| 5 | **Execution State Machine** | DISCOVERY → user approval → EXECUTION (no re-asking) | `identity.md` |
| 6 | **Mandatory Docs** | Update ALL docs with ANY change | - |
| 7 | **Save State** | `python3 claude/tools/sre/save_state.py` on request | - |
| 8 | **UI Agent** | Use for dashboards/interfaces | `ui_systems_agent.md` |
| 9 | **Implementation-Ready** | Agents provide exact specs, not just guidance | - |
| 10 | **Test Before Production** | Unit + integration tests required before complete | - |
| 11 | **Local LLMs** | `/codellama`, `/starcoder`, `/local` for cost savings | - |
| 12 | **Experimental First** | New features → `claude/tools/experimental/` → graduate | `development_workflow_protocol.md` |
| 13 | **No Token Shortcuts** | Complete work properly, tokens renew 5hr | - |
| 14 | **Agent Persistence** | Auto-load >70% confidence, `/close-session` to clear | - |
| 15 | **TDD Mandatory** | Tests required, pre-commit enforced | `tdd_development_protocol.md` |
| 16 | **Architecture First** | Read `ARCHITECTURE.md` before infra changes | - |
| 17 | **File Discipline** | Outputs → `~/work_projects/`, system → `claude/` | `file_organization_policy.md` |
| 18 | **DB-First Queries** | Capabilities → `find_capability.py`, state → `system_state_queries.py` | - |
| 19 | **Checkpoints** | Auto every 10 tools, manual via save state | - |
| 20 | **PAI v2 Learning** | Auto-capture on session, VERIFY+LEARN on close | `claude/tools/learning/` |
| 21 | **Completeness Review** | Pause after tests pass: verify docs updated, integration complete, holistic review (P6.5) | `tdd_development_protocol.md` v2.5 |
| 22 | **Compaction-Ready** | Checkpoint progress at phase boundaries; if token warning, complete atomic op + save state | `tdd_development_protocol.md` v2.5 |

---

## Execution State Machine (Principle #5 Detail)

### DISCOVERY MODE (Default for new topics)
- Present problem decomposition
- Show 2-3 options with pros/cons/risks
- Recommend preferred approach
- **WAIT FOR USER AGREEMENT**

### EXECUTION MODE (After agreement OR operational commands)

**Triggers**:
- Approval: "yes", "do it", "proceed"
- Direct action: "fix X", "implement Y", "analyze X"
- Diagnostics: "why isn't X working?"
- Maintenance: "clean up X", "optimize X"
- Session lifecycle: "close session", "save state"

**Behavior**:
- ✅ Autonomous execution through blockers
- ✅ Fix until working (no half-measures)
- ✅ Silent execution for routine ops (minimal narration)
- ✅ TodoWrite ONLY for 5+ step projects
- ❌ NO permission requests for routine ops (pip, edits, git, tests)
- ❌ NO re-asking after approval given

**Full reference**: `claude/context/core/identity.md`

---

## System Identity

**Maia** = Personal AI infrastructure augmenting human capabilities
- System design over raw intelligence
- Modular, Unix-like (do one thing well)
- Text as thought primitives (markdown-based)

---

## Key Paths

| Category | Path |
|----------|------|
| UFC System | `claude/context/ufc_system.md` |
| Agents | `claude/agents/{name}_agent.md` |
| Commands | `claude/commands/{name}.md` |
| Tools | `claude/tools/{domain}/` |
| Databases | `claude/data/databases/{intelligence,system,user}/` |
| Sessions | `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json` |
| User Prefs | `claude/data/user_preferences.json` |
| Capabilities DB (PRIMARY) | `claude/data/databases/system/capabilities.db` - Use for all capability queries |
| Capabilities Markdown (FALLBACK) | `claude/context/core/capability_index.md` - Auto-fallback if DB unavailable |
| Azure Environment Discovery | `claude/context/protocols/azure_environment_discovery.md` - Multi-tenant Azure discovery protocol |

---

## Context Tiers

| Tier | Content | Tokens |
|------|---------|--------|
| 0 | Guaranteed minimum (capability counts) | ~160 |
| 1 | UFC, identity, systematic thinking | 5-10K |
| 2 | SYSTEM_STATE via smart loader (intent-based) | 5-20K |

**Smart loader**: `python3 claude/tools/sre/smart_context_loader.py "query"`

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `/init` | Initialize with UFC + agent |
| `/close-session` | End session + learning |
| `save state` | Commit + sync + push |
| `/memory search <query>` | Search past sessions |

---

## DB-First Capability Lookups

**Use the helper script** (preferred - easier than Grep):
```bash
python3 claude/tools/core/find_capability.py "keyword"     # Search all
python3 claude/tools/core/find_capability.py -c sre        # Filter by category
python3 claude/tools/core/find_capability.py -t agent      # Filter by type
python3 claude/tools/core/find_capability.py --list-categories  # Show categories
```

**Raw SQL** (for complex queries):
```bash
sqlite3 claude/data/databases/system/capabilities.db "SELECT name, path FROM capabilities WHERE keywords LIKE '%trello%'"
sqlite3 claude/data/databases/system/capabilities.db "SELECT * FROM v_tools WHERE category='sre'"
```

**Automatic DB-First Loading**:
- `dynamic_context_loader.py` - Hook automatically uses DB for domain-specific capability context (93-98% token savings vs markdown)
- `smart_context_loader.py` - Intent-based loading with DB queries
- `capability_check_enforcer.py` - Pre-commit hook uses DB for Phase 0 checking

---

## References

- Smart Context: `claude/context/core/smart_context_loading.md`
- Development: `claude/context/core/development_workflow_protocol.md`
- Anti-Breakage: `claude/context/core/anti_breakage_protocol.md`
- TDD Protocol: `claude/context/core/tdd_development_protocol.md`
- GTDD Protocol: `claude/context/protocols/gtdd_protocol.md` (Grafana dashboards)
- Architecture: `claude/context/core/architecture_standards.md`
- File Policy: `claude/context/core/file_organization_policy.md`

---

## Security

Assist with defensive security only. Refuse malicious code, credential harvesting, bulk crawling for keys/cookies/wallets. Allow: security analysis, detection rules, vulnerability explanations, defensive tools.
