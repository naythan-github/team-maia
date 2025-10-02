# Local LLM Auto-Router

Automatically route this task to the optimal local LLM for maximum cost savings.

**Task**: $ARGUMENTS

**Auto-Routing Logic**:
1. Analyze task type (code, docs, security, simple, strategic)
2. Select optimal local model:
   - Code/Docs: CodeLlama 13B (99.3% savings)
   - Security: StarCoder2 15B (99.3% savings, Western)
   - Simple: Llama 3B (99.7% savings)
   - Strategic: Claude Sonnet (quality preserved)
3. Execute on selected model
4. Return result

Execute via Python router for intelligent model selection.
