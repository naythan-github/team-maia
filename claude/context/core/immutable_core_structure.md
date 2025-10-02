# Immutable Core Structure Definition
**Created**: 2025-09-30
**Status**: LOCKED - These paths never change
**Purpose**: Prevent file sprawl through immutable foundation

## Core Directories (NEVER MOVE OR RENAME)

### claude/context/core/
**Purpose**: System identity and core behavior
**Immutability**: ABSOLUTE - No file moves, only content updates
**Files**:
- identity.md (System identity and capabilities)
- systematic_thinking_protocol.md (Reasoning framework)
- model_selection_strategy.md (LLM routing strategy)
- ufc_system.md (Unified context management)
- smart_context_loading.md (Context optimization)

### claude/context/tools/
**Purpose**: Tool definitions and capabilities
**Immutability**: HIGH - Structure stable, content evolves
**Files**:
- available.md (Current tool inventory)

### claude/context/personal/
**Purpose**: User profile and preferences
**Immutability**: HIGH - Personal context stability
**Files**:
- profile.md (User context and preferences)

### claude/agents/
**Purpose**: Agent definitions and configurations
**Immutability**: MEDIUM - New agents added, existing ones stable
**Naming Convention**: {function}_agent.md (semantic, not version-based)
**Current Count**: 46 agent files
**Extension Strategy**: Add new agents, preserve existing definitions

### claude/tools/
**Purpose**: Executable tool implementations
**Immutability**: MEDIUM - New tools added, core tools stable
**Naming Convention**: {category}/{function}.py OR {function}.py (semantic, not version-based)
**Current Count**: 226 tool files
**Extension Strategy**: Organized by category subdirectories where appropriate

### claude/commands/
**Purpose**: Workflow orchestration definitions
**Immutability**: MEDIUM - New commands added, core commands stable
**Naming Convention**: {workflow_name}.md (semantic, not version-based)
**Current Count**: 78 command files
**Extension Strategy**: Add new commands, preserve existing workflows

### claude/hooks/
**Purpose**: System hooks and automation
**Immutability**: HIGH - Critical system integration points
**Current Count**: 25 hook files
**Extension Strategy**: Core hooks protected, new hooks carefully reviewed

### claude/data/
**Purpose**: Databases, logs, and system state
**Immutability**: LOW - Dynamic data storage
**Extension Strategy**: Structured subdirectories for different data types

## Extension Zones (SAFE FOR CHANGES)

### archive/
**Purpose**: Historical preservation and deprecated functionality
**Immutability**: HIGH - Historical preservation (read-only reference)
**Current State**: 677 archived files
**Management**: Periodic consolidation, never delete historical records

### claude/extensions/experimental/
**Purpose**: Safe development and testing space
**Immutability**: LOW - Frequent changes expected
**Cleanup**: Quarterly review and cleanup
**Policy**: No production dependencies on experimental code

### claude/extensions/personal/
**Purpose**: User-specific customizations
**Immutability**: LOW - Personal preference evolution
**Backup**: Preserved but not core-critical

### claude/extensions/archive/
**Purpose**: Deprecated but preserved functionality
**Immutability**: HIGH - Historical preservation
**Access**: Read-only reference

## Naming Conventions

### Semantic Naming Principles
1. **Function Over Evolution**: Names describe WHAT, not WHEN
   - ✅ GOOD: `jobs_agent.md`, `financial_advisor_agent.md`
   - ❌ BAD: `jobs_agent_v2.md`, `new_financial_advisor.md`

2. **No Version Indicators**: Versions tracked in git, not filenames
   - ✅ GOOD: `backup_manager.py`
   - ❌ BAD: `backup_manager_v3.py`, `backup_manager_final.py`

3. **No Temporal Indicators**: No "new", "old", "temp", "updated"
   - ✅ GOOD: `context_loader.py`
   - ❌ BAD: `new_context_loader.py`, `context_loader_updated.py`

4. **Descriptive and Specific**: Clear function identification
   - ✅ GOOD: `systematic_thinking_enforcement_webhook.py`
   - ❌ BAD: `webhook.py`, `enforcement.py`

### Directory-Specific Conventions

**Agents** (`claude/agents/`):
- Pattern: `{function}_agent.md`
- Example: `jobs_agent.md`, `security_specialist_agent.md`

**Tools** (`claude/tools/`):
- Pattern: `{function}.py` OR `{category}/{function}.py`
- Examples: `backup_manager.py`, `governance/dependency_scanner.py`

**Commands** (`claude/commands/`):
- Pattern: `{workflow_name}.md`
- Example: `save_state.md`, `backup_to_icloud.md`

**Context** (`claude/context/`):
- Pattern: `{category}/{specific_context}.md`
- Example: `core/identity.md`, `tools/available.md`

## Enforcement Mechanisms

### Automated Protection
1. **Pre-commit Hooks**: Block core directory modifications
2. **File Lifecycle Manager**: Prevent core file moves/renames
3. **Naming Validator**: Ensure semantic consistency
4. **CI/CD Integration**: Automated validation in deployment

### Manual Protection
1. **Documentation**: Clear immutability status
2. **Code Reviews**: Catch violations during review
3. **Team Training**: Awareness of immutable core
4. **Periodic Audits**: Quarterly validation checks

## Violation Response Protocol

### Core Directory Changes
1. **Block Immediately**: Prevent the change via pre-commit hook
2. **Investigate Cause**: Why was change attempted?
3. **Provide Alternative**: Guide to appropriate extension zone
4. **Update Protection**: Strengthen prevention mechanisms if bypass occurred

### Naming Convention Violations
1. **Flag for Review**: Identify non-semantic names
2. **Suggest Alternative**: Provide semantic name
3. **Update Gradually**: Fix over time, don't break system
4. **Document Decision**: Record rationale for any exceptions

### Emergency Bypass Procedures
**ONLY for critical system recovery:**
1. Create bypass flag: `touch claude/data/protection_bypass.flag`
2. Perform necessary emergency changes
3. Document changes: Update changelog with justification
4. Remove bypass: `rm claude/data/protection_bypass.flag`
5. Post-recovery audit: Review changes for compliance restoration

## Success Metrics

### Stability Metrics
- **Core File Moves**: Target 0 per quarter after stabilization
- **Naming Violations**: Target <5 per quarter for new files
- **Context Loading Success**: 95% → 99.5% reliability
- **Agent Discovery Success**: 99.2% → 99.8% reliability

### Organizational Metrics
- **File Discovery Time**: Reduce by 50%
- **Maintenance Overhead**: 3 hours/week → 30 minutes/quarter
- **Onboarding Efficiency**: New contributor ramp-up time reduced 40%

## Review and Update Schedule

### Quarterly Reviews
- **Q1**: Review core structure integrity
- **Q2**: Audit naming compliance
- **Q3**: Evaluate extension zone utilization
- **Q4**: Annual comprehensive assessment

### Update Process
1. **Propose Change**: Document rationale and impact
2. **Impact Analysis**: Assess breaking change risk
3. **Approval Required**: Explicit approval for core structure changes
4. **Migration Plan**: Detailed plan for any necessary changes
5. **Validation**: Post-change validation and rollback capability

## Historical Context

**Created**: Phase 1 of Anti-Sprawl Implementation (2025-09-30)
**Problem Addressed**: File sprawl threatening system reliability
**Current State**: 952 files across 10 categories
**Critical Insight**: 677 files (71%) already archived, demonstrating sprawl impact

This immutable core structure establishes the foundation for long-term system stability and prevents the chaos of uncontrolled file growth.