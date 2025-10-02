# Stop and Fix Router Command

## Purpose
Automatic router health validation and repair system to prevent cost waste when LLM router is non-functional.

## Usage
```bash
# Check router health before expensive operations
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/llm_router_health_monitor.py check

# Validate before code generation tasks  
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/llm_router_health_monitor.py validate "Generate Python code"

# Attempt automatic repair
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/llm_router_health_monitor.py repair

# Get cost protection status
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/llm_router_health_monitor.py status
```

## Integration
Router health checks are automatically integrated into:
- **user-prompt-submit hook**: Validates router before every prompt
- **Cost protection**: Warns when router failure would cause 99.3% cost increase
- **Auto-repair**: Attempts to fix common router issues automatically

## Manual Repair Steps
If auto-repair fails:

1. **Check router files exist and are not corrupted**
2. **Verify Ollama service is running**: `ollama list`
3. **Install recommended models**: `ollama pull llama3.2:3b` and `ollama pull codellama:13b`
4. **Restore from backup**: Use router failure simulator restore function
5. **Rebuild from git history**: If backups unavailable

## Cost Protection
- **99.3% savings at risk**: Code generation costs $0.003/1k (Claude) vs $0.00002/1k (local)
- **Automatic warnings**: System blocks expensive operations when router broken
- **Pre-execution validation**: Checks router health before code generation tasks
- **Graceful degradation**: Falls back to Claude with user notification

## Testing
```bash
# Test failure scenarios
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/router_failure_simulator.py comprehensive

# Simulate corruption (for testing)
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/router_failure_simulator.py corrupt

# Restore after testing
python3 ${MAIA_ROOT}/claude/tools/🛠️_general/router_failure_simulator.py restore
```