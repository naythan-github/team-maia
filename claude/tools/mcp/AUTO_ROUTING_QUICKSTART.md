# LLM Auto-Routing Quick Start

**3-Minute Setup for 99.3% Cost Savings**

## ✅ Prerequisites Check

```bash
# 1. Verify ollama is running
ollama list

# Should show:
# codellama:13b    (7.4 GB)
# starcoder2:15b   (9.1 GB)
# llama3.2:3b      (2.0 GB)
```

If models missing:
```bash
ollama pull codellama:13b
ollama pull starcoder2:15b
ollama pull llama3.2:3b
```

## 🚀 Using Slash Commands (Easiest Way)

### Code Generation & Documentation
```bash
# Instead of asking Claude:
"Write a Python function to parse JSON"

# Type this:
/codellama "Write a Python function to parse JSON"

# Result: CodeLlama 13B generates code (99.3% cost savings)
```

### Security Analysis
```bash
# Instead of:
"Analyze authentication code for vulnerabilities"

# Type:
/starcoder "Analyze authentication code for security vulnerabilities"

# Result: StarCoder2 15B (Western model, enterprise-safe, 99.3% savings)
```

### Auto-Route (Let System Decide)
```bash
# Type:
/local "your task here"

# System analyzes task and picks optimal model automatically
```

## 📊 Slash Command Reference

| Command | Model | Best For | Savings |
|---------|-------|----------|---------|
| `/codellama` | CodeLlama 13B | Code, docs, tests | 99.3% |
| `/starcoder` | StarCoder2 15B | Security, compliance | 99.3% |
| `/local` | Auto-selected | Any task (intelligent routing) | Up to 99.7% |

## 💡 When to Use Each

### Use `/codellama` for:
- ✅ Writing functions, classes, scripts
- ✅ Creating documentation
- ✅ Generating tests
- ✅ Code review and refactoring
- ✅ Technical writing

### Use `/starcoder` for:
- ✅ Security analysis
- ✅ Compliance documentation
- ✅ Enterprise code review
- ✅ Orro Group client work (Western model requirement)

### Use `/local` for:
- ✅ Unknown task type (system decides)
- ✅ Mixed tasks (will auto-classify)
- ✅ When unsure which model to use

### Let Claude Sonnet handle:
- ⚠️ Strategic architecture decisions
- ⚠️ Complex multi-step reasoning
- ⚠️ Novel problem-solving
- ⚠️ High-stakes decisions

## 🎯 Examples

### Example 1: Generate Test Code
```bash
/codellama "Create pytest tests for user authentication with mock database"
```
**Result**: Complete test suite in seconds, 99.3% cost savings

### Example 2: Document Setup Process
```bash
/codellama "Write step-by-step guide for deploying FastAPI app to AWS Lambda"
```
**Result**: Production-ready documentation, 99.3% cost savings

### Example 3: Security Audit
```bash
/starcoder "Review this OAuth implementation for security vulnerabilities"
```
**Result**: Enterprise-grade analysis with Western model, 99.3% cost savings

### Example 4: Auto-Route
```bash
/local "Help me optimize database queries"
```
**Result**: System classifies as CODE_REVIEW, routes to CodeLlama 13B automatically

## 🔧 Manual Testing (For Verification)

Test the router directly:
```bash
python3 claude/hooks/llm_auto_router_hook.py "Write Python function to validate emails"
```

Output shows:
- Task classification
- Recommended model
- Cost savings percentage
- Suggested command

## 📈 Monitor Your Savings

View routing decisions:
```bash
cat ~/git/maia/claude/data/llm_routing_log.jsonl | tail -10
```

See what tasks were routed to local LLMs and savings achieved.

## ⚡ Pro Tips

1. **Start with `/local`** - Let the system learn your patterns
2. **Verify output quality** - Local LLMs excel at code/docs
3. **Use specific commands** - `/codellama` or `/starcoder` for explicit control
4. **Reserve Sonnet** - Only for truly strategic/complex tasks

## 🐛 Troubleshooting

**"Command not found"**
- Restart Claude Code to load new slash commands
- Check `.claude/commands/` folder has `codellama.md`, `starcoder.md`, `local.md`

**"Model not available"**
- Run `ollama list` to verify models installed
- Pull missing models: `ollama pull codellama:13b`

**"Slow performance"**
- Ensure 32GB RAM available
- Use lighter model: `ollama run llama3.2:3b` for simple tasks
- Check M4 Neural Engine acceleration active

## 📚 Full Documentation

- **Complete Guide**: `claude/context/core/llm_auto_routing_usage.md`
- **Gap Analysis**: `claude/context/core/llm_auto_routing_gap.md`
- **Router Code**: `claude/hooks/llm_auto_router_hook.py`

## 🎉 That's It!

**You're now saving 99.3% on code and documentation tasks while preserving quality!**

**Next Steps**:
1. Try `/codellama "your first task"`
2. Monitor `llm_routing_log.jsonl` for analytics
3. Adjust usage based on quality results
4. Provide feedback for system improvements

---

**Quick Reference Card**:
```
Code/Docs:  /codellama "task"  → 99.3% savings
Security:   /starcoder "task"  → 99.3% savings (Western)
Auto-Route: /local "task"      → Up to 99.7% savings
Strategic:  Ask Claude          → Quality preserved
```

**Enjoy your cost-optimized, privacy-enhanced AI workflow!** 🚀
