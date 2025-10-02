# Four-Layer Context Enforcement System

## Overview
Aggressive context loading validation system inspired by KAI's methodology to ensure 95%+ context compliance.

## Layer 1: UFC System Description (Foundation)

### File: `/claude/context/ufc_system.md`
**Purpose**: Establishes the fundamental context management system
**Status**: ✅ Already implemented

**Key Elements**:
- Filesystem as context principle
- Modular loading strategy  
- 3-level maximum depth rule
- Clean separation guidelines

## Layer 2: User Prompt Submit Hook (Enforcement)

### Implementation: Enhanced Hook System
```bash
#!/bin/bash
# Enhanced user-prompt-submit hook with aggressive validation

echo "🚨 MAIA CONTEXT ENFORCEMENT ACTIVATED 🚨"
echo ""

# Stage 1: Validate context file accessibility
CONTEXT_FILES=(
    "${MAIA_ROOT}/claude/context/ufc_system.md"
    "${MAIA_ROOT}/claude/context/core/identity.md" 
    "${MAIA_ROOT}/claude/context/tools/available.md"
    "${MAIA_ROOT}/claude/context/core/agents.md"
    "${MAIA_ROOT}/claude/context/core/command_orchestration.md"
    "${MAIA_ROOT}/claude/context/personal/profile.md"
)

echo "🔍 VALIDATING CONTEXT FILE ACCESSIBILITY..."
VALIDATION_FAILED=false

for file in "${CONTEXT_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $(basename "$file") - accessible"
    else
        echo "  ❌ $(basename "$file") - MISSING OR INACCESSIBLE"
        VALIDATION_FAILED=true
    fi
done

# Stage 2: Force context loading reminder
echo ""
echo "⚡ MANDATORY CONTEXT LOADING SEQUENCE ⚡"
echo "🔄 You MUST read these files before responding:"
echo "   1. UFC System (context management foundation)"
echo "   2. Identity (who you are as Maia)"  
echo "   3. Tools Available (capabilities and commands)"
echo "   4. Agents (specialized agent orchestration)"
echo "   5. Command Orchestration (advanced multi-agent workflows)"
echo "   6. Personal Profile (user context and preferences)"
echo ""

# Stage 3: Validation checkpoint
if [[ "$VALIDATION_FAILED" == true ]]; then
    echo "🚨 CONTEXT VALIDATION FAILED 🚨"
    echo "❌ Some context files are missing or inaccessible"
    echo "⚠️  OPERATING IN DEGRADED MODE - CONTEXT MAY BE INCOMPLETE"
else
    echo "✅ CONTEXT VALIDATION PASSED"
    echo "🎯 ALL CONTEXT FILES ACCESSIBLE - PROCEED WITH FULL CONTEXT LOADING"
fi

echo ""
echo "🤖 Maia Context Enforcement: ACTIVE"
echo "📊 Expected Response: Context loading confirmation with ✅ status"
echo ""
echo "═══════════════════════════════════════════════════════════════"
```

### Hook Installation
```bash
# Save the hook to Claude Code hooks directory
chmod +x ${MAIA_ROOT}/claude/hooks/user-prompt-submit
```

## Layer 3: Aggressive CLAUDE.md Instructions (Visual Alerts)

### Enhanced CLAUDE.md with Visual Enforcement
```markdown
# 🚨 MAIA - My AI Agent 🚨

## 🔴🔴🔴 CRITICAL: ALWAYS READ CONTEXT FILES FIRST 🔴🔴🔴

### ⚡⚡⚡ MANDATORY CONTEXT LOADING ⚡⚡⚡
🚨 BEFORE RESPONDING TO ANY REQUEST, YOU MUST READ THESE FILES IN ORDER 🚨

🎯 **ENFORCEMENT LEVEL: MAXIMUM** 🎯
📊 **SUCCESS RATE REQUIREMENT: 95%+** 📊  
⏱️  **TIMEOUT: NONE - ALWAYS LOAD CONTEXT** ⏱️

📋 **REQUIRED CONTEXT FILES** (READ IN EXACT ORDER):
1. 🏗️  `${MAIA_ROOT}/claude/context/ufc_system.md` - Understanding the UFC system
2. 🤖 `${MAIA_ROOT}/claude/context/core/identity.md` - Your identity as Maia  
3. 🛠️  `${MAIA_ROOT}/claude/context/tools/available.md` - Available tools and capabilities
4. 👥 `${MAIA_ROOT}/claude/context/core/agents.md` - Available specialized agents
5. 🔗 `${MAIA_ROOT}/claude/context/core/command_orchestration.md` - Advanced multi-agent workflows
6. 👤 `${MAIA_ROOT}/claude/context/personal/profile.md` - User profile and context

### 🔄 CONTEXT LOADING VALIDATION 🔄

**REQUIRED CONFIRMATION RESPONSE FORMAT**:
```
✅ Context loaded. Ready to assist as Maia.

📊 Context Status:
- UFC System: ✅ Loaded
- Identity: ✅ Loaded  
- Tools: ✅ Loaded
- Agents: ✅ Loaded
- Orchestration: ✅ Loaded
- Profile: ✅ Loaded

🎯 Operating Mode: Full Context
🤖 Agent: Maia (My AI Agent)
📈 Context Confidence: 100%
```

### 🚨 FAILURE MODES 🚨
**IF CONTEXT LOADING FAILS**:
- ❌ DO NOT proceed with user request
- 🔄 RETRY context loading immediately  
- 📢 REPORT specific context loading failure
- ⚠️  OPERATE in degraded mode only if absolutely necessary

**IF CONTEXT IS INCOMPLETE**:
- ⚠️  ACKNOWLEDGE degraded mode operation
- 📊 REPORT which context files failed to load
- 🔄 ATTEMPT recovery before proceeding
```

### Updated CLAUDE.md Implementation
```markdown
# 🚨 MAIA - My AI Agent 🚨

## CRITICAL: ALWAYS READ CONTEXT FILES FIRST

### 🔴 MANDATORY CONTEXT LOADING 🔴
Before responding to ANY request, you MUST read these files IN ORDER:
1. `${MAIA_ROOT}/claude/context/ufc_system.md` - Understanding the UFC system
2. `${MAIA_ROOT}/claude/context/core/identity.md` - Your identity as Maia
3. `${MAIA_ROOT}/claude/context/tools/available.md` - Available tools and capabilities
4. `${MAIA_ROOT}/claude/context/core/agents.md` - Available specialized agents
5. `${MAIA_ROOT}/claude/context/core/command_orchestration.md` - Advanced multi-agent workflows
6. `${MAIA_ROOT}/claude/context/personal/profile.md` - User profile and context

### 🚨 ENFORCEMENT REQUIREMENTS 🚨
- **Context Loading**: MANDATORY on every interaction
- **Success Rate**: Must achieve 95%+ context compliance
- **Validation**: Confirm context loading with ✅ status message
- **Failure Handling**: Retry context loading before proceeding

### Response Confirmation
After reading context files, confirm with:
"✅ Context loaded. Ready to assist as Maia."
```

## Layer 4: Symlink Strategy (Inheritance)

### Cross-Repository Context Inheritance
**Status**: ✅ Implemented via symlinks

**Coverage**: 
- ✅ 4/8 repositories now have Maia context symlinks
- ⚠️  4/8 repositories have existing CLAUDE.md files (need --force option)

**Verification**:
```bash
python3 claude/tools/setup_context_symlinks.py verify
```

**Full Implementation**:
```bash
python3 claude/tools/setup_context_symlinks.py setup --force
```

## Implementation Status

### Layer 1: UFC Foundation ✅
- File exists and defines context management system
- Loaded in mandatory context sequence
- Establishes 3-level depth limit and modular loading

### Layer 2: Hook Enforcement 🔄 (Needs Installation)
```bash
# Create the enhanced hook file
mkdir -p ${MAIA_ROOT}/claude/hooks
```

### Layer 3: Visual Alerts ✅ 
- CLAUDE.md already has mandatory context loading
- Can be enhanced with more visual indicators
- Confirmation response format defined

### Layer 4: Symlinks ✅
- Tool created and tested
- 4/8 repositories successfully linked
- Verification system in place

## Success Metrics

### Context Loading Compliance
- **Target**: 95%+ successful context loading
- **Current**: Baseline measurement needed
- **Measurement**: Hook validation + confirmation responses

### Context Quality Indicators
- **Full Context**: All 6 files loaded successfully
- **Partial Context**: 4-5 files loaded (degraded mode)
- **Failed Context**: <4 files loaded (retry required)

### User Experience
- **Response Time**: Context loading adds <10 seconds
- **Reliability**: Consistent context availability across sessions
- **Consistency**: Same context across all repositories

## Next Steps

1. **Install Enhanced Hook**: Deploy user-prompt-submit hook with validation
2. **Test Enforcement**: Verify 4-layer system effectiveness  
3. **Measure Baseline**: Establish current context loading success rate
4. **Optimize Performance**: Reduce context loading time while maintaining compliance