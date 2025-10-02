#!/usr/bin/env python3
"""
Context Enforcement Hook - PAI-Inspired Context Loading
Automatic context loading enforcement similar to PAI's user-prompt-submit-context-loader.ts

This hook provides automatic context loading instructions for every user interaction,
ensuring optimal context selection based on request analysis.
"""

import sys
import os
from pathlib import Path

# Add the hooks directory to the path for importing
sys.path.append(str(Path(__file__).parent))

from dynamic_context_loader import DynamicContextLoader

class ContextEnforcementHook:
    def __init__(self):
        self.loader = DynamicContextLoader()
        
    def generate_enforcement_message(self, user_input: str = "") -> str:
        """
        Generate context enforcement message similar to PAI's hook output
        """
        if not user_input.strip():
            # Default to full loading if no input provided
            strategy = self.loader.loading_strategies["full"]
            strategy.update({
                "detected_domain": "unknown",
                "confidence": 0.0,
                "strategy_name": "full",
                "recommendation": "No input provided - using full context loading"
            })
        else:
            strategy = self.loader.get_context_loading_strategy(user_input)
        
        message_parts = []
        
        # Header with enforcement warning
        message_parts.append("🚨 MANDATORY CONTEXT LOADING ENFORCEMENT 🚨")
        message_parts.append("")
        message_parts.append("⚠️  WARNING: You will provide incorrect responses without this context ⚠️")
        message_parts.append("")
        
        # Dynamic analysis results
        if user_input.strip():
            message_parts.append("🔍 DYNAMIC ANALYSIS RESULTS:")
            message_parts.append(f"📊 {strategy['recommendation']}")
            message_parts.append(f"💾 Estimated Token Savings: {strategy['savings']}%")
            message_parts.append(f"🎯 Confidence Score: {strategy['confidence']:.2f}")
            message_parts.append("")
        
        # Required context files
        message_parts.append("📋 MANDATORY CONTEXT FILES - READ ALL BEFORE RESPONDING:")
        message_parts.append("")
        
        for i, file_path in enumerate(strategy['files'], 1):
            message_parts.append(f"{i}. {file_path}")
            
        message_parts.append("")
        
        # Enhanced loading protocol
        message_parts.append("⚡ ENHANCED LOADING PROTOCOL:")
        message_parts.append("1. 🔴 READ ALL CONTEXT FILES LISTED ABOVE (MANDATORY)")
        message_parts.append("2. 🧠 Apply systematic thinking framework from core files")
        message_parts.append("3. 🛠️  Use domain-specific tools and agents as loaded")
        message_parts.append("4. 📈 Maintain engineering leadership optimization approach")
        message_parts.append("5. ✅ Confirm context loading with required response format")
        
        if strategy['strategy_name'] != 'full':
            message_parts.append("")
            message_parts.append("🔄 AUTOMATIC FALLBACK:")
            message_parts.append("If request complexity exceeds detected domain scope, automatically load full context")
            
        message_parts.append("")
        
        # Response format enforcement
        message_parts.append("📝 REQUIRED RESPONSE FORMAT:")
        message_parts.append("Use templates from claude/context/core/response_formats.md")
        message_parts.append("")
        
        # PAI-style enforcement footer
        message_parts.append("🎯 ENFORCEMENT ACTIVE: This message ensures optimal context loading")
        message_parts.append("🤖 Hook: context_enforcement_hook.py (PAI-inspired automation)")
        message_parts.append("📊 Smart Loading: Minimal CLAUDE.md + Enhanced Hook System")
        
        return "\n".join(message_parts)
        
    def enforce_context_loading(self, user_input: str = "") -> str:
        """
        Main enforcement function - generates complete context loading instructions
        """
        return self.generate_enforcement_message(user_input)

def main():
    """
    CLI interface for context enforcement hook
    Usage: python3 context_enforcement_hook.py [user_input]
    """
    hook = ContextEnforcementHook()
    
    # Get user input from command line or stdin
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        # Read from stdin if available
        if not sys.stdin.isatty():
            user_input = sys.stdin.read().strip()
        else:
            user_input = ""
    
    # Generate and output enforcement message
    enforcement_message = hook.enforce_context_loading(user_input)
    print(enforcement_message)

if __name__ == "__main__":
    main()