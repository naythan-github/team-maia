# Smart Context Loading System

## 🔴 SMART CONTEXT LOADING 🔴 ⭐ **ENABLED - 12-62% EFFICIENCY GAIN**

### 🚨 **CRITICAL UFC REQUIREMENT** 🚨
**THE UFC SYSTEM IS NON-NEGOTIABLE** - It defines the entire context management architecture. EVERY new context window MUST load UFC first, regardless of domain or task complexity.

### 🔒 **AUTOMATED ENFORCEMENT SYSTEM** ⭐ **NEW - PRODUCTION ACTIVE**
**ZERO-VIOLATION PROTECTION**: Context loading enforcement system automatically prevents UFC violations:
- **Pre-Response Hook**: `user-prompt-submit` hook validates context loading before any response
- **State Tracking**: `claude/data/context_state.json` tracks loaded files and conversation state  
- **Auto-Recovery**: `context_auto_loader.py` attempts graceful recovery when violations detected
- **Manual Fallback**: Clear instructions provided when auto-recovery fails
- **100% Coverage**: No response possible without proper context loading sequence

**MANDATORY CORE (Always Load - NO EXCEPTIONS)**:
1. `${MAIA_ROOT}/claude/context/ufc_system.md` - **🚨 FOUNDATION - NEVER SKIP** - Understanding the UFC system
2. `${MAIA_ROOT}/claude/context/core/identity.md` - Your identity as Maia **WITH SYSTEMATIC THINKING FRAMEWORK**
3. `${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md` - **MANDATORY SYSTEMATIC OPTIMIZATION FRAMEWORK**
4. `${MAIA_ROOT}/claude/context/core/model_selection_strategy.md` - **MANDATORY MODEL ENFORCEMENT** (Sonnet default, ask permission for Opus)
5. `${MAIA_ROOT}/claude/context/core/file_organization_policy.md` - **FILE STORAGE RULES** (prevents repository pollution, ~2.5K tokens)
6. **Smart SYSTEM_STATE Loading** ⭐ **DATABASE-ACCELERATED - 500-2500x FASTER (Phase 165-166)**
   - **Primary Path** ⭐ **NEW**: Database query interface (0.13-0.54ms, 500-2500x faster than markdown)
     - **Tool**: `python3 claude/tools/sre/system_state_queries.py [command]`
     - **Commands**: `recent --count N`, `search KEYWORD`, `phases N1 N2 N3`, `context N`
     - **Coverage**: 60 phases (100%), 9-year history (2016-2025)
     - **Smart Loader Integration**: Automatically uses database (transparent to user)
   - **Secondary Path**: Smart context loader with markdown parsing (100-500ms, legacy fallback)
     - **Tool**: `python3 claude/tools/sre/smart_context_loader.py "user_query_context"`
     - **Performance**: 83% average token reduction (42K → 5-20K adaptive)
     - **Graceful Fallback**: Used automatically when database unavailable
   - **Query-Adaptive**:
     - Agent enhancement queries → Phases 2, 107-111 (~4K tokens, 90% reduction)
     - SRE/reliability queries → Phases 103-105 (~8K tokens, 80% reduction)
     - Strategic planning → Recent 20 phases (~13K tokens, 69% reduction)
     - Simple queries → Recent 10 phases (~3K tokens, 93% reduction)
   - **⚠️ DEPRECATED**: Direct SYSTEM_STATE.md reads (500-2500x slower than database)
   - **Manual Usage**:
     ```bash
     # DATABASE QUERIES (PREFERRED - 500x faster)
     python3 claude/tools/sre/system_state_queries.py recent --count 10 --markdown
     python3 claude/tools/sre/system_state_queries.py search "database"
     python3 claude/tools/sre/system_state_queries.py phases 165 164 163

     # SMART LOADER (automatic DB integration)
     python3 claude/tools/sre/smart_context_loader.py "Continue agent enhancement work"
     python3 claude/tools/sre/smart_context_loader.py "your query" --stats
     python3 claude/tools/sre/smart_context_loader.py --phases 2 107 108
     python3 claude/tools/sre/smart_context_loader.py --recent 15
     ```
   - **Locations**:
     - Query Interface: `${MAIA_ROOT}/claude/tools/sre/system_state_queries.py`
     - Smart Loader: `${MAIA_ROOT}/claude/tools/sre/smart_context_loader.py`
     - Database: `${MAIA_ROOT}/claude/data/databases/system/system_state.db`
   - **Documentation**: See `claude/context/core/capability_index.md` (SYSTEM_STATE Query Interface section)

**DOMAIN-SMART LOADING (Load Based on Request)**:
- **Simple Tasks** (math, basic questions): CORE ONLY (62% savings)
- **Research/Analysis**: CORE + available.md + agents.md + systematic_tool_checking.md (25% savings)
- **Security Tasks**: CORE + available.md + agents.md + systematic_tool_checking.md (25% savings)
- **Personal/Productivity**: CORE + profile.md + agents.md (37% savings)
- **Technical/Cloud**: CORE + available.md + agents.md + command_orchestration.md + systematic_tool_checking.md (12% savings)
- **Design Tasks**: CORE + agents.md + command_orchestration.md (37% savings)
- **Complex Multi-Domain**: ALL FILES (traditional full loading - 0% savings)

**SMART LOADING PROTOCOL**:
- **Enhanced Hook System**: Use `claude/hooks/dynamic_context_loader.py` for automated analysis
- **Domain Detection**: AI-powered request classification with 87.5% accuracy
- **Automatic Context Selection**: Load CORE files + domain-relevant files based on detected patterns
- **Fallback Protection**: If uncertain or complex → fallback to FULL traditional loading
- **High Confidence Threshold**: Quality preservation with confidence scoring

**ENHANCED AUTOMATION** ⭐ **NEW - PHASE 1.2 KAI INTEGRATION**:
```bash
# Automatic context analysis
python3 claude/hooks/dynamic_context_loader.py analyze "your request here"

# Generate context loading instructions
python3 claude/hooks/dynamic_context_loader.py generate "your request here"
```

**FALLBACK TO FULL LOADING**:
- `${MAIA_ROOT}/claude/context/tools/available.md` - Available tools and capabilities
- `${MAIA_ROOT}/claude/context/core/agents.md` - Available specialized agents
- `${MAIA_ROOT}/claude/context/core/command_orchestration.md` - Advanced multi-agent workflows
- `${MAIA_ROOT}/claude/context/personal/profile.md` - User profile and context
- `${MAIA_ROOT}/claude/context/core/systematic_tool_checking.md` - Mandatory tool discovery workflow