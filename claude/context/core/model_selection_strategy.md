# Model Selection Strategy

## Security Status ⭐ Phase 1 Complete (2025-09-30)
**Rating**: 7.5/10 (up from 4.5/10) - All P0 vulnerabilities eliminated
**Validation**: 19/19 security tests passing
**Fixes**: Opus enforcement, command injection prevention, path traversal elimination

## 🚨 OPUS COST PROTECTION (Lazy-Loaded)
**Efficient approach**: Loads only when Opus-risk tasks detected (saves ~13K tokens/$0.039 per context)
```python
from claude.hooks.lazy_opus_protection import get_lazy_opus_protection
protection = get_lazy_opus_protection()
```

## Model Routing Overview
Multi-LLM intelligent routing with enhanced Opus permission control, maintaining full functionality while delivering cost optimization.

---

## Model Tiers

### 🏠 Local Llama 3.2 3B - 99.7% cost reduction ($0.00001/1k tokens) ⭐ M4 OPTIMIZED
**Auto-routed**: Ultra-lightweight tasks with M4 Neural Engine optimization
File operations, basic bash, data processing (JSON/CSV), log parsing, text transformations, plugin templates
**Hardware**: M4 Neural Engine (38 TOPS), 24GB unified memory, 30.4 tokens/sec, zero network latency

### 🏠 Local Llama 3.2 8B - 99.3% cost reduction ($0.00002/1k tokens)
**Auto-routed**: Medium complexity with local privacy
Code analysis, documentation, technical explanations, advanced data processing
**Hardware**: Apple Silicon GPU, high-memory configs (32GB+)

### 🏠 Local CodeLlama 7B - 99.3% cost reduction ($0.00002/1k tokens) ⭐ CODE-SPECIALIZED
**Auto-routed**: Code-specialized tasks with M4 optimization
Code generation/implementation, debugging, technical docs, refactoring, plugin development
**Hardware**: M4 Neural Engine optimized for development workflows

### 🏠 StarCoder2 15B - 99.3% cost reduction ($0.00002/1k tokens) ⭐ SECURITY-FOCUSED
**Auto-routed**: Advanced code with security-first approach
Complex code generation/refactoring, architecture analysis, debugging, plugin migration
**Security**: Western/auditable model, transparent training, no DeepSeek exposure
**Hardware**: 9.1GB model optimized for M4 Neural Engine

### 🏠 CodeLlama 13B - 99.3% cost reduction ($0.00002/1k tokens) ⭐ META CODE MODEL
**Auto-routed**: Meta's proven code model for complex development
Enterprise code generation, large-scale refactoring, complex algorithms, production optimization
**Security**: Meta/Facebook model with transparent training
**Hardware**: 7.4GB model with M4 optimization

### ⚡ Gemini Flash - 99% cost reduction ($0.00003/1k tokens)
**Auto-routed**: Cloud-based ultra-cheap operations (fallback for local models)
File operations (local unavailable), large context (1M tokens), batch processing, templates

### 🔍 Gemini Pro - 58.3% cost reduction ($0.00125/1k tokens)
**Auto-routed**: Research and analysis
Company/market research, industry trends, technology best practices, competitive analysis, content generation

### 🚀 Claude Sonnet - Quality preservation (default strategic model)
**Auto-routed**: Strategic analysis and complex reasoning
Strategic planning/roadmaps, multi-step decisions, agent orchestration, personal assistance, complex business analysis

### 🎯 Claude Opus - Premium capability (ask permission)
**Auto-routed**: Critical security and high-stakes analysis
Security vulnerability assessments, critical business decisions, complex architecture, high-stakes strategy

**ENHANCED PERMISSION PROTOCOL** ✅ FULLY ENFORCED:
1. **Technical**: `model_enforcement_webhook.py` blocks unauthorized Opus
2. **Agents**: All 26 agents updated with Sonnet defaults, Opus permission requirements
3. **Continue protection**: Special enforcement for token overflow scenarios
4. **Hook integration**: `user-prompt-submit` runs enforcement on every request
5. **Audit trail**: All enforcement logged with cost savings tracking

🔒 **ACTIVE PROTECTION**:
LinkedIn optimization → ❌ Opus blocked | Continue commands → 🔒 Sonnet enforced | Security tasks → ⚠️ Permission request | Standard tasks → ✅ Sonnet recommended (80% savings)

---

## Two-Model Strategy ⭐ DATA-DRIVEN

**Usage analysis (230 requests)**:
- 53% simple operations (file, bash, data) → **Llama 3B always loaded (2GB)**
- 6% code generation → **CodeLlama 13B on-demand (7.4GB)**
- 18% strategic analysis → **Claude Sonnet**
- Research/Security → **Gemini Pro/Claude Opus** as needed

**Implementation**:
- Base: Llama 3.2 3B permanently loaded (21.1 tokens/sec, 2GB RAM)
- Code: CodeLlama 13B lazy-loaded for code tasks (12 tokens/sec, 7.4GB RAM)
- Switching: Only 6% of requests (code generation)
- Resource efficiency: 9.4GB total vs 12GB single large model
- Battery optimization: Prevents constant 22B model thermal load
- SSD protection: Minimal swap reduces wear

---

## System Status ⭐ PRODUCTION OPERATIONAL

✅ Router tools restored and validated functional
✅ 5 local models + 3 Claude models = 8 total operational
✅ Local models: codellama:13b, starcoder2:15b, codestral:22b, codellama:7b, llama3.2:3b
✅ Intelligent routing operational with 99.3% cost savings on code tasks
✅ Cost optimization verified: $0.00002/1k vs $0.003/1k Sonnet (99.3% savings)
✅ Task classification active: Code auto-routed to local models
✅ Integration ready: Available for existing tools
✅ Quality maintained: Strategic analysis uses Claude for optimal reasoning
✅ Hardware efficient: Local execution preserves privacy

---

## Cost Impact ⭐ VALIDATED

- **Verified savings**: 99.3% reduction for code generation ($0.00002 vs $0.003 per 1k tokens)
- **Local performance**: 5.5 tokens/sec average, $0.000008 cost for complex code
- **Router effectiveness**: Automatic task classification correctly routing to optimal models
- **Quality validation**: Production-ready output at 99.3% cost savings
- **File operations**: Local Llama 3B near-zero cost
- **Code tasks**: CodeLlama 13B/StarCoder2 15B with 99.3% savings vs Claude
- **Strategic analysis**: Claude Sonnet/Opus preserved for high-value reasoning
- **Privacy enhanced**: Sensitive code remains local with zero cloud transmission

---

## Usage Commands

### Method 3 Optimal Interface ⭐ PHASE 34
```bash
# Simple tasks with optimal token efficiency
python3 claude/tools/optimal_local_llm_interface.py task "What is 2+2?"

# Code generation with automatic CodeLlama selection
python3 claude/tools/optimal_local_llm_interface.py code "Create CSV parser function"

# General prompts with model-specific optimization
python3 claude/tools/optimal_local_llm_interface.py generate "Explain Python decorators"

# List available models and status
python3 claude/tools/optimal_local_llm_interface.py models

# Download models through native interface
python3 claude/tools/optimal_local_llm_interface.py pull llama3.2:3b
```

### Legacy Commands (Still Supported)
```bash
# Test router with local model integration
python3 claude/tools/production_llm_router.py

# Direct code generation with CodeLlama 13B
python3 claude/tools/local_llm_codegen.py <original_tool_path> <plugin_name>

# Quick health check
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "Test: 2+3=", "stream": false}' | jq -r '.response'

# System status including hardware detection
python3 claude/tools/maia_cost_optimizer.py status

# Analyze usage patterns
python3 claude/tools/maia_cost_optimizer.py analyze

# Enable optimization for specific domains
python3 claude/tools/maia_cost_optimizer.py enable research

# Test Engineering Manager workflow
python3 claude/tools/maia_cost_optimizer.py test engineering_workflows

# Check local model availability and GPU usage
ollama list && ollama ps
```

### 🔧 Method 3 Implementation ⭐ PHASE 34 BREAKTHROUGH
**Upgrade**: Migrated from HTTP API to native Ollama Python library
**Token explosion eliminated**: Streaming JSON responses (10-50x token multiplication) resolved
**Context compression prevention**: Massive streaming responses no longer trigger compression
**Implementation**: `optimal_local_llm_interface.py` with connection pooling and type safety
**Performance**: Enhanced error handling, SSL warnings eliminated, model-specific optimization, intelligent task routing
