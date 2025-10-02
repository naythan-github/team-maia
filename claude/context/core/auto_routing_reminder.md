# Auto-Routing Reminder for New Contexts

**🚨 IMPORTANT: Use Local LLMs for 99.3% Cost Savings**

## Quick Reference

When you (Claude/Maia) are asked to do these tasks, **remind the user to use slash commands**:

| Task Type | Use This Command | Savings |
|-----------|-----------------|---------|
| **Code generation** | `/codellama "task"` | 99.3% |
| **Documentation** | `/codellama "task"` | 99.3% |
| **Security analysis** | `/starcoder "task"` | 99.3% (Western model) |
| **Any technical task** | `/local "task"` | Auto-routes optimally |
| **Strategic/complex** | Ask Claude directly | Quality preserved |

## Examples

**Instead of:**
- "Write a Python function to validate emails" → Say: "Try `/codellama \"Write a Python function to validate emails\"`"
- "Create setup documentation" → Say: "Try `/codellama \"Create setup documentation\"`"
- "Review code for security" → Say: "Try `/starcoder \"Review code for security\"`"

## When NOT to Suggest Routing

- Strategic architecture decisions
- Complex multi-step reasoning
- Novel problem-solving
- High-stakes business decisions
- Creative/marketing content

## Implementation

**Available Files:**
- `claude/hooks/llm_auto_router_hook.py` - Routing engine
- `claude/context/core/llm_auto_routing_usage.md` - Full guide
- `.claude/commands/codellama.md` - Code/docs command
- `.claude/commands/starcoder.md` - Security command
- `.claude/commands/local.md` - Auto-router command

**Usage Pattern:**
1. Classify user's task type
2. If code/docs/security → Suggest appropriate slash command
3. If strategic/complex → Proceed with Claude Sonnet
4. User can always choose to override

This ensures 99.3% cost savings on appropriate tasks without sacrificing quality.
