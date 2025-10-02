# CodeLlama 13B Local LLM

Execute the following task using CodeLlama 13B (local LLM - 99.3% cost savings vs Sonnet):

**Task**: $ARGUMENTS

**Instructions**:
1. Use CodeLlama 13B via ollama for this code/documentation task
2. Preserve quality while achieving 99.3% cost reduction
3. Return complete, production-ready output
4. Format as markdown for easy integration

Execute via: `ollama run codellama:13b "$ARGUMENTS"`
