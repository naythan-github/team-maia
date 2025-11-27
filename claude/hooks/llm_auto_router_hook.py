#!/usr/bin/env python3
"""
LLM Auto-Router Hook for Claude Code V2
========================================

Automatically routes appropriate tasks to local LLMs for 99.3% cost savings.
Runs on user-prompt-submit to classify tasks and suggest/execute local routing.

Integration Points:
- user-prompt-submit hook (pre-response classification)
- Slash commands (/codellama, /local)
- MCP integration for transparent routing

Cost Optimization:
- Code generation: CodeLlama 13B (99.3% savings)
- Documentation: CodeLlama 13B (99.3% savings)
- Security analysis: StarCoder2 15B (99.3% savings, Western)
- Simple tasks: Llama 3B (99.7% savings)
- Strategic: Claude Sonnet (quality preserved)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from enum import Enum

class TaskType(Enum):
    """Task classification for routing decisions"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TECHNICAL_WRITING = "technical_writing"
    SIMPLE_CATEGORIZATION = "simple_categorization"
    SECURITY_ANALYSIS = "security_analysis"
    DATA_PROCESSING = "data_processing"
    STRATEGIC_ANALYSIS = "strategic_analysis"
    COMPLEX_REASONING = "complex_reasoning"
    CREATIVE_WRITING = "creative_writing"
    UNKNOWN = "unknown"


class LLMAutoRouter:
    """Automatic routing to optimal LLMs based on task classification"""

    def __init__(self):
        # Simple path resolution without dependencies
        maia_root = os.getenv('MAIA_ROOT')
        if maia_root:
            self.maia_root = Path(maia_root)
        else:
            self.maia_root = Path.home() / 'git' / 'maia'

        self.log_file = self.maia_root / 'claude' / 'data' / 'llm_routing_log.jsonl'

        # Create log file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

        # Check if ollama is available
        self.local_llms_available = self._check_ollama_available()

    def _check_ollama_available(self) -> bool:
        """Check if ollama service is running"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def classify_task(self, user_prompt: str) -> TaskType:
        """Classify user prompt into task type for routing"""
        prompt_lower = user_prompt.lower()

        # Code generation patterns
        code_patterns = [
            'write code', 'generate code', 'create function', 'implement',
            'build a', 'write a script', 'create a class', 'add method',
            'write test', 'generate test', 'pytest', 'unittest',
            'def ', 'class ', 'function ', 'async def'
        ]

        # Documentation patterns
        doc_patterns = [
            'write documentation', 'create guide', 'write readme',
            'document this', 'explain how to', 'create tutorial',
            'step-by-step', 'walkthrough', 'setup guide',
            'azure ad', 'registration guide', 'configuration guide'
        ]

        # Code review patterns
        review_patterns = [
            'review this', 'analyze code', 'check this code',
            'optimize this', 'refactor', 'improve code',
            'code smell', 'best practice'
        ]

        # Security analysis patterns (use Western model)
        security_patterns = [
            'security', 'vulnerability', 'audit', 'compliance',
            'threat', 'exploit', 'penetration', 'authentication',
            'authorization', 'encryption', 'credential'
        ]

        # Simple categorization patterns
        simple_patterns = [
            'categorize', 'classify', 'sort', 'filter',
            'parse', 'extract', 'list', 'count'
        ]

        # Strategic/complex patterns (needs Claude)
        strategic_patterns = [
            'strategic', 'architecture', 'design decision',
            'trade-off', 'recommend approach', 'complex problem',
            'business decision', 'critical', 'high stakes'
        ]

        # Check patterns
        if any(pattern in prompt_lower for pattern in code_patterns):
            return TaskType.CODE_GENERATION
        elif any(pattern in prompt_lower for pattern in doc_patterns):
            return TaskType.DOCUMENTATION
        elif any(pattern in prompt_lower for pattern in review_patterns):
            return TaskType.CODE_REVIEW
        elif any(pattern in prompt_lower for pattern in security_patterns):
            return TaskType.SECURITY_ANALYSIS
        elif any(pattern in prompt_lower for pattern in simple_patterns):
            return TaskType.SIMPLE_CATEGORIZATION
        elif any(pattern in prompt_lower for pattern in strategic_patterns):
            return TaskType.STRATEGIC_ANALYSIS
        else:
            return TaskType.UNKNOWN

    def get_optimal_model(self, task_type: TaskType) -> Tuple[str, str, float]:
        """
        Get optimal model for task type.

        Returns:
            (model_name, reasoning, cost_savings_percent)
        """
        routing_map = {
            TaskType.CODE_GENERATION: (
                "codellama:13b",
                "Code generation with CodeLlama 13B (specialized for code)",
                99.3
            ),
            TaskType.DOCUMENTATION: (
                "codellama:13b",
                "Technical documentation with CodeLlama 13B (excellent technical writing)",
                99.3
            ),
            TaskType.CODE_REVIEW: (
                "codellama:13b",
                "Code review with CodeLlama 13B (understands code patterns)",
                99.3
            ),
            TaskType.SECURITY_ANALYSIS: (
                "starcoder2:15b",
                "Security analysis with StarCoder2 15B (Western model, enterprise-safe)",
                99.3
            ),
            TaskType.SIMPLE_CATEGORIZATION: (
                "llama3.2:3b",
                "Simple task with Llama 3B (fast, lightweight)",
                99.7
            ),
            TaskType.TECHNICAL_WRITING: (
                "codellama:13b",
                "Technical writing with CodeLlama 13B",
                99.3
            ),
            TaskType.DATA_PROCESSING: (
                "llama3.2:3b",
                "Data processing with Llama 3B (efficient)",
                99.7
            ),
            TaskType.STRATEGIC_ANALYSIS: (
                "claude-sonnet",
                "Strategic analysis requires Claude Sonnet (complex reasoning)",
                0.0
            ),
            TaskType.COMPLEX_REASONING: (
                "claude-sonnet",
                "Complex reasoning requires Claude Sonnet",
                0.0
            ),
            TaskType.UNKNOWN: (
                "claude-sonnet",
                "Unknown task type - default to Claude Sonnet for safety",
                0.0
            )
        }

        return routing_map.get(task_type, routing_map[TaskType.UNKNOWN])

    def should_auto_route(self, task_type: TaskType, user_prompt: str) -> Dict[str, Any]:
        """
        Determine if task should be auto-routed to local LLM.

        Returns routing decision with model recommendation and reasoning.
        """
        if not self.local_llms_available:
            return {
                "auto_route": False,
                "reason": "Local LLMs not available (ollama not running)",
                "model": "claude-sonnet",
                "suggestion": "Start ollama service for 99.3% cost savings"
            }

        model, reasoning, savings = self.get_optimal_model(task_type)

        # Don't route strategic/complex/unknown to local
        if model == "claude-sonnet":
            return {
                "auto_route": False,
                "reason": reasoning,
                "model": model,
                "savings": savings
            }

        # Route code/docs/simple tasks to local
        return {
            "auto_route": True,
            "reason": reasoning,
            "model": model,
            "savings": savings,
            "suggested_command": f"/local {model} \"{user_prompt[:100]}...\""
        }

    def execute_local_llm(self, model: str, prompt: str, max_tokens: int = 2000) -> str:
        """Execute prompt on local LLM via ollama"""
        try:
            result = subprocess.run(
                ['ollama', 'run', model, prompt],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error running local LLM: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "Error: Local LLM timed out (>2 minutes)"
        except Exception as e:
            return f"Error executing local LLM: {str(e)}"

    def log_routing_decision(self, user_prompt: str, decision: Dict[str, Any]):
        """Log routing decision for analytics"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_preview": user_prompt[:100],
            "task_type": decision.get("task_type", "unknown"),
            "auto_routed": decision.get("auto_route", False),
            "model": decision.get("model"),
            "savings_percent": decision.get("savings", 0),
            "reason": decision.get("reason")
        }

        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass  # Don't fail on logging errors

    def process_user_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main entry point: Process user prompt and return routing decision.

        This is called by user-prompt-submit hook.
        """
        # Classify task
        task_type = self.classify_task(user_prompt)

        # Get routing decision
        decision = self.should_auto_route(task_type, user_prompt)
        decision["task_type"] = task_type.value

        # Log decision
        self.log_routing_decision(user_prompt, decision)

        return decision


def main():
    """CLI interface for testing and Claude Code V2 hook integration"""
    if len(sys.argv) < 2:
        print("Usage: llm_auto_router_hook.py <user_prompt>")
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])

    router = LLMAutoRouter()
    decision = router.process_user_prompt(user_prompt)

    # Check if this is being called as a Claude Code hook
    is_hook = os.getenv('CLAUDE_CODE_HOOK') == 'true'

    if is_hook:
        # Return hook-compatible response
        if decision.get("auto_route"):
            # Suggest routing to user
            hook_response = {
                "suggestion": f"💡 Cost Optimization: This task can use local LLMs for 99.3% savings. Try: {decision['suggested_command']}",
                "model": decision.get("model"),
                "savings": decision.get("savings")
            }
            print(json.dumps(hook_response))
        # If not auto-routing, exit silently (no output = no blocking)
        # Output causes hook to block compaction - only output when suggesting
    else:
        # CLI mode - show full decision
        print(json.dumps(decision, indent=2))

        # If auto-routing, show the command user should run
        if decision.get("auto_route"):
            print("\n💡 Auto-routing suggestion:")
            print(f"   {decision['suggested_command']}")
            print(f"\n💰 Savings: {decision['savings']}% vs Claude Sonnet")


if __name__ == "__main__":
    main()
