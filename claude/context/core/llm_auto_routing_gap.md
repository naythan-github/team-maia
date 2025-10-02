# LLM Auto-Routing Gap - System Enhancement Opportunity

**Identified**: 2025-10-01 (Phase 75)
**Status**: ⚠️ Manual routing only - No automatic Claude Code integration
**Priority**: Medium (High value, but workaround exists)

## Problem Statement

**Current State**: Maia has powerful local LLM routing infrastructure (99.3% cost savings), but Claude Code (Sonnet) doesn't automatically use it. Manual Python calls are required.

**Expected Behavior**: Claude Code should automatically route appropriate tasks to local LLMs without manual intervention.

**Actual Behavior**: User must remind Claude to use local models, or Claude must manually call Python routing tools.

## Root Cause Analysis

### What Exists ✅
1. **Production LLM Router**: `claude/tools/core/production_llm_router.py`
   - Routes tasks to optimal LLMs (local vs cloud)
   - Task classification (code, documentation, strategic, etc.)
   - Cost optimization logic (99.3% savings on code tasks)

2. **Local LLM Interface**: `claude/tools/core/optimal_local_llm_interface.py`
   - Direct ollama integration
   - Model selection (CodeLlama 13B, StarCoder2 15B, Llama 3B)
   - Quality preservation with cost savings

3. **6 Local Models Available**:
   - codellama:13b (7.4 GB) - Primary for code/technical
   - starcoder2:15b (9.1 GB) - Security/Western
   - llama3.2:3b (2.0 GB) - Lightweight tasks
   - codegemma:7b, phi4:14b, codellama:70b

### What's Missing ❌
1. **Claude Code Integration Hook**: No mechanism for Claude Code to automatically invoke local LLMs
2. **Response Interception**: No layer that intercepts Claude responses to route via router
3. **Automatic Task Detection**: Claude doesn't classify its own responses for routing

### Architecture Gap

```
Current Architecture (Manual):
User Request → Claude Sonnet → Python Tool Call → Local LLM
                     ↑                              ↓
                     └────── Manual decision ───────┘

Desired Architecture (Automatic):
User Request → Router → Local LLM (99.3% of tasks)
                    → Claude Sonnet (Strategic only)
```

## Why This Matters

### Cost Impact
- **Without Auto-Routing**: All responses use Claude Sonnet ($0.003/1k tokens)
- **With Auto-Routing**:
  - Documentation: CodeLlama 13B ($0.00002/1k tokens) - 99.3% savings
  - Code generation: CodeLlama 13B - 99.3% savings
  - Simple tasks: Llama 3B - 99.7% savings
  - Strategic only: Sonnet - Preserved quality

### Productivity Impact
- **Manual routing requires**:
  1. User reminder to use local models
  2. Claude recognition of opportunity
  3. Explicit Python tool invocation
  4. Result processing and formatting

- **Automatic routing would**:
  1. Task detected automatically
  2. Routed instantly to local LLM
  3. Result integrated seamlessly
  4. Zero user intervention

## Evidence of Gap

### Test Case: Azure AD Guide Generation
**Manual Process** (what happened today):
1. User: "Is this something local LLMs can help with?"
2. Claude: "Yes, let me check the router..."
3. Claude: *investigates system*
4. User: "3" (investigate the gap)
5. Claude: *manually calls* `ollama run codellama:13b`
6. Result: ✅ Guide generated successfully

**Ideal Process** (what should happen):
1. Claude receives: "Create Azure AD guide"
2. Auto-router detects: Task type = documentation
3. Auto-routes to: CodeLlama 13B
4. Returns: ✅ Guide generated (transparent to user)

## Current Workaround

### For Users
Explicitly request local LLM usage:
```
"Use CodeLlama to generate the Azure AD guide"
"Create tests with local LLM"
```

### For Claude Code
Manually invoke routing tools:
```python
# Explicit Python calls
ollama run codellama:13b "prompt"
python3 claude/tools/core/optimal_local_llm_interface.py generate "prompt"
```

## Proposed Solutions

### Solution A: Claude Code Extension (Ideal)
**Complexity**: High
**Impact**: Complete auto-routing

Create Claude Code extension/plugin that:
1. Intercepts all responses before generation
2. Classifies task type (code, docs, strategic, etc.)
3. Routes to local LLM or Claude based on classification
4. Returns result transparently

**Requirements**:
- Claude Code plugin API access
- Response interception capability
- Task classification integration

**Challenges**:
- Claude Code extension architecture unknown
- May not support pre-response hooks
- Potential latency concerns

### Solution B: Prompt-Based Auto-Routing (Pragmatic)
**Complexity**: Low
**Impact**: Partial auto-routing

Enhance system prompt to:
1. Always check task type before responding
2. Explicitly call routing tools for appropriate tasks
3. Make local LLM usage the default for code/docs

**Implementation**:
```markdown
# Add to CLAUDE.md or identity.md:
Before responding to code generation, documentation, or technical tasks:
1. Classify task type
2. If code/docs/technical → Call optimal_local_llm_interface.py
3. If strategic/complex → Proceed with Sonnet
4. Return result
```

**Challenges**:
- Relies on prompt adherence
- May forget to route
- Extra token usage for classification

### Solution C: Pre-Processing Hook (Hybrid)
**Complexity**: Medium
**Impact**: High auto-routing with control

Create user-prompt-submit hook:
1. Analyzes user request before Claude sees it
2. If local LLM suitable → Routes directly to local model
3. If Claude needed → Passes to Claude with routing suggestion

**Implementation**:
```python
# claude/hooks/llm_auto_router_hook.py
def analyze_and_route(user_prompt):
    task_type = classify_task(user_prompt)

    if task_type in [TaskType.CODE, TaskType.DOCS, TaskType.TECHNICAL]:
        # Route to local LLM directly
        return route_to_local_llm(user_prompt, task_type)
    else:
        # Pass to Claude with routing hint
        return {"route_to": "claude", "hint": "strategic_task"}
```

**Challenges**:
- Hook execution overhead
- Classification accuracy
- Complex multi-step tasks

## Recommended Approach

**Phase 1: Immediate (Solution B)**
- Update system prompt with explicit routing instructions
- Document manual routing patterns
- Train users to request local LLM when needed

**Phase 2: Short-term (Solution C)**
- Build pre-processing hook for common task types
- Start with conservative routing (code generation only)
- Expand to docs/technical as confidence grows

**Phase 3: Long-term (Solution A)**
- Explore Claude Code extension capabilities
- Build full auto-routing if API available
- Complete transparent local LLM integration

## Success Metrics

### When Auto-Routing Works
- **Cost Reduction**: 50%+ reduction in Sonnet token usage
- **User Experience**: No manual routing reminders needed
- **Quality Preservation**: Strategic tasks still use Sonnet
- **Transparency**: Users unaware of routing (just works)

### Measurement
```python
# Track routing effectiveness
metrics = {
    "total_requests": 100,
    "auto_routed_to_local": 60,  # 60%
    "manual_routed_to_local": 5,  # 5%
    "claude_sonnet_used": 35,     # 35%
    "cost_savings": "55%",
    "quality_maintained": True
}
```

## Implementation Timeline

### Immediate (This Session)
- [x] Document gap in this file
- [x] Prove local LLM works (Azure AD guide)
- [ ] Add routing reminder to system prompt

### Next Session (Phase 76)
- [ ] Build pre-processing hook (Solution C)
- [ ] Test with common task types
- [ ] Measure cost savings

### Future Enhancement (Phase 77+)
- [ ] Investigate Claude Code extension API
- [ ] Build full auto-routing if possible
- [ ] Achieve 60%+ automatic routing rate

## Related Documentation

- **Router Implementation**: `claude/tools/core/production_llm_router.py`
- **Local LLM Interface**: `claude/tools/core/optimal_local_llm_interface.py`
- **Model Strategy**: `claude/context/core/model_selection_strategy.md`
- **M365 Integration**: Uses local LLMs in agent design
- **Hook System**: `claude/hooks/` (model_enforcement, context_loading, etc.)

## Conclusion

**The Gap is Real**: Auto-routing infrastructure exists but isn't integrated with Claude Code's response generation.

**The Impact is Significant**: Missing 99.3% cost savings on routine tasks that could be handled by local LLMs.

**The Solution is Achievable**: Multiple approaches available, starting with prompt-based routing and evolving to automated hooks.

**Next Action**: Implement Solution B (prompt-based) immediately, build Solution C (hook-based) next session.

---

**Status**: ⚠️ **GAP DOCUMENTED** - Ready for systematic enhancement
**Value**: 💰 **HIGH** - 50-60% cost reduction potential with proper auto-routing
**Priority**: 📊 **MEDIUM** - High value but workaround exists (manual routing)
