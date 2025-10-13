#!/usr/bin/env python3
"""
Dynamic Context Loader - Enhanced Hook System
PAI-inspired dynamic requirements loading for Maia

Automatically analyzes user requests and provides intelligent context loading
recommendations based on request domain and complexity.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class DynamicContextLoader:
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.context_dir = self.maia_root / "claude/context"
        
        # Domain patterns for request classification
        self.domain_patterns = {
            "simple": [
                r"\b(what is|how much|calculate|math|simple question)\b",
                r"\d+\s*[\+\-\*/]\s*\d+",  # Basic math
                r"\b(yes|no|true|false)\b.*\?",  # Yes/no questions
                r"\b(hello|hi|hey|thanks|thank you|good morning|good afternoon)\b",  # Greetings
                r"\b(add|subtract|multiply|divide|sum|total|count)\b",  # Math operations
                r"^(hi|hello|hey)$"  # Simple greetings
            ],
            "research": [
                r"\b(research|analyze|investigate|study|compare|review)\b",
                r"\b(find information|look up|search for|tell me about)\b",
                r"\b(latest|current|recent|trends|market)\b",
                r"\b(competitive analysis|intelligence|insights)\b"
            ],
            "security": [
                r"\b(security|vulnerability|vulnerabilities|threat|attack|breach|incident)\b",
                r"\b(penetration test|pentest|audit|compliance|SOC)\b",
                r"\b(malware|phishing|ransomware|firewall|encryption)\b",
                r"\b(SIEM|IDS|IPS|SOAR|threat hunting)\b",
                r"\b(check|scan|test|assess).*\b(security|vulnerabilities)\b"
            ],
            "personal": [
                r"\b(calendar|schedule|meeting|appointment|email)\b",
                r"\b(personal|private|my|productivity|workflow)\b",
                r"\b(finance|budget|expenses|investment|banking)\b",
                r"\b(health|fitness|goals|habits|tracking)\b"
            ],
            "technical": [
                r"\b(code|programming|development|software|application)\b",
                r"\b(database|API|integration|deployment|architecture)\b",
                r"\b(python|javascript|typescript|sql|docker|kubernetes)\b",
                r"\b(bug|error|debug|troubleshoot|performance)\b"
            ],
            "cloud": [
                r"\b(cloud|AWS|Azure|GCP|infrastructure|DevOps)\b",
                r"\b(terraform|ansible|CI/CD|pipeline|container)\b",
                r"\b(monitoring|alerting|logging|metrics|observability)\b",
                r"\b(scalability|availability|reliability|disaster recovery)\b"
            ],
            "design": [
                r"\b(design|UI|UX|interface|visual|mockup|wireframe)\b",
                r"\b(branding|logo|color|typography|layout|composition)\b",
                r"\b(user experience|user interface|interaction|prototype)\b",
                r"\b(figma|sketch|adobe|photoshop|illustrator)\b"
            ],
            "business": [
                r"\b(business|strategy|market|customer|revenue|profit)\b",
                r"\b(proposal|presentation|report|analysis|metrics)\b",
                r"\b(project management|team|leadership|operations)\b",
                r"\b(ROI|KPI|dashboard|executive|stakeholder)\b"
            ]
        }
        
        # Context loading strategies
        self.loading_strategies = {
            "minimal": {
                "description": "Core files only (62% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md", 
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md"
                ],
                "savings": 62
            },
            "research": {
                "description": "Research and analysis focused (25% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md", 
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/tools/available.md",
                    "claude/context/core/agents.md",
                    "claude/context/core/systematic_tool_checking.md"
                ],
                "savings": 25
            },
            "security": {
                "description": "Security analysis focused (25% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md", 
                    "claude/context/tools/available.md",
                    "claude/context/core/agents.md",
                    "claude/context/core/systematic_tool_checking.md"
                ],
                "savings": 25
            },
            "personal": {
                "description": "Personal productivity focused (37% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/personal/profile.md",
                    "claude/context/core/agents.md"
                ],
                "savings": 37
            },
            "technical": {
                "description": "Technical development focused (12% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/tools/available.md",
                    "claude/context/core/agents.md",
                    "claude/context/core/command_orchestration.md",
                    "claude/context/core/systematic_tool_checking.md"
                ],
                "savings": 12
            },
            "cloud": {
                "description": "Cloud infrastructure focused (12% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/tools/available.md", 
                    "claude/context/core/agents.md",
                    "claude/context/core/command_orchestration.md",
                    "claude/context/core/systematic_tool_checking.md"
                ],
                "savings": 12
            },
            "design": {
                "description": "Design workflow focused (37% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/core/agents.md",
                    "claude/context/core/command_orchestration.md"
                ],
                "savings": 37
            },
            "full": {
                "description": "Complete context loading (0% savings)",
                "files": [
                    "claude/context/ufc_system.md",
                    "claude/context/core/identity.md",
                    "claude/context/core/systematic_thinking_protocol.md",
                    "claude/context/core/model_selection_strategy.md",
                    "claude/context/tools/available.md",
                    "claude/context/core/agents.md", 
                    "claude/context/core/command_orchestration.md",
                    "claude/context/personal/profile.md",
                    "claude/context/core/systematic_tool_checking.md"
                ],
                "savings": 0
            }
        }
        
    def analyze_request(self, user_input: str) -> Tuple[str, float]:
        """
        Analyze user request and determine optimal domain classification
        Returns: (domain, confidence_score)
        """
        user_input_lower = user_input.lower()
        domain_scores = {}
        
        # Score each domain based on pattern matches
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, user_input_lower, re.IGNORECASE))
                score += matches
            
            # Normalize score by pattern count and input length
            if len(patterns) > 0:
                normalized_score = score / len(patterns)
                domain_scores[domain] = normalized_score
        
        # Find highest scoring domain
        if not domain_scores or max(domain_scores.values()) == 0:
            return "full", 0.0
            
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = min(domain_scores[best_domain], 1.0)  # Cap at 1.0
        
        # High confidence threshold for domain-specific loading
        if confidence >= 0.2:  # Lowered threshold for better detection
            return best_domain, confidence
        else:
            return "full", confidence
            
    def get_context_loading_strategy(self, user_input: str) -> Dict:
        """
        Get optimal context loading strategy based on user input
        """
        domain, confidence = self.analyze_request(user_input)
        
        # Map domain to loading strategy
        domain_mapping = {
            "simple": "minimal",
            "research": "research", 
            "security": "security",
            "personal": "personal",
            "technical": "technical",
            "cloud": "cloud",
            "design": "design",
            "business": "research"  # Business maps to research strategy
        }
        
        strategy_name = domain_mapping.get(domain, "full")
        strategy = self.loading_strategies[strategy_name].copy()
        
        strategy.update({
            "detected_domain": domain,
            "confidence": confidence,
            "strategy_name": strategy_name,
            "recommendation": self._generate_recommendation(domain, confidence, strategy_name)
        })
        
        return strategy
        
    def _generate_recommendation(self, domain: str, confidence: float, strategy: str) -> str:
        """Generate human-readable recommendation"""
        if confidence >= 0.7:
            confidence_desc = "High confidence"
        elif confidence >= 0.3:
            confidence_desc = "Medium confidence"
        else:
            confidence_desc = "Low confidence"
            
        return f"{confidence_desc} {domain} domain detected - using {strategy} loading strategy"
        
    def generate_context_instructions(self, user_input: str) -> str:
        """
        Generate context loading instructions similar to PAI's hook output
        """
        strategy = self.get_context_loading_strategy(user_input)
        
        instructions = []
        instructions.append("🔴 DYNAMIC CONTEXT LOADING ACTIVATED 🔴")
        instructions.append(f"📊 Analysis: {strategy['recommendation']}")
        instructions.append(f"💾 Token Savings: {strategy['savings']}%")
        instructions.append("")
        instructions.append("📋 REQUIRED CONTEXT FILES:")
        
        for file_path in strategy['files']:
            instructions.append(f"- {file_path}")
            
        instructions.append("")
        instructions.append("⚡ LOADING PROTOCOL:")
        instructions.append("1. Read all required context files listed above")
        instructions.append("2. Apply systematic thinking framework from core files")
        instructions.append("3. Use domain-specific tools and agents as loaded")
        instructions.append("4. Maintain engineering leadership optimization approach")
        
        if strategy['strategy_name'] != 'full':
            instructions.append("")
            instructions.append("🔄 FALLBACK: If request complexity exceeds domain scope, load full context")
            
        return "\n".join(instructions)
        
    def test_domain_detection(self, test_cases: List[Tuple[str, str]]) -> Dict:
        """Test domain detection accuracy"""
        results = {"correct": 0, "total": 0, "details": []}
        
        for test_input, expected_domain in test_cases:
            detected_domain, confidence = self.analyze_request(test_input)
            correct = detected_domain == expected_domain
            
            results["details"].append({
                "input": test_input,
                "expected": expected_domain,
                "detected": detected_domain, 
                "confidence": confidence,
                "correct": correct
            })
            
            if correct:
                results["correct"] += 1
            results["total"] += 1
            
        results["accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0
        return results


def load_system_state_smart(user_query: str = None) -> str:
    """
    Load SYSTEM_STATE.md intelligently using smart context loader.

    Args:
        user_query: User's query for intent-based loading

    Returns:
        SYSTEM_STATE content optimized for query (5-20K tokens)
    """
    import subprocess
    import sys

    maia_root = Path(__file__).parent.parent.parent
    loader_path = maia_root / "claude" / "tools" / "sre" / "smart_context_loader.py"

    # Default query if none provided
    if not user_query:
        user_query = "What is the current system status?"

    try:
        # Invoke smart loader
        result = subprocess.run(
            [sys.executable, str(loader_path), user_query],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return result.stdout
        else:
            # Fallback to recent phases
            print(f"⚠️  Smart loader failed, falling back to recent phases", file=sys.stderr)
            system_state = maia_root / "SYSTEM_STATE.md"
            if system_state.exists():
                lines = system_state.read_text().splitlines()
                # Load recent 1000 lines (approximately Phases 97-111)
                return '\n'.join(lines[-1000:])
            else:
                return "⚠️  SYSTEM_STATE.md not found"

    except Exception as e:
        # Fallback on any error
        print(f"⚠️  Smart loader exception: {e}, falling back", file=sys.stderr)
        system_state = maia_root / "SYSTEM_STATE.md"
        if system_state.exists():
            lines = system_state.read_text().splitlines()
            return '\n'.join(lines[-1000:])
        else:
            return "⚠️  SYSTEM_STATE.md not found"


def main():
    """CLI interface for testing dynamic context loader"""
    import sys
    
    loader = DynamicContextLoader()
    
    if len(sys.argv) < 2:
        print("Usage: python3 dynamic_context_loader.py [analyze|generate|test] <input>")
        print("Examples:")
        print("  python3 dynamic_context_loader.py analyze 'help me debug this code'")
        print("  python3 dynamic_context_loader.py generate 'research market trends'") 
        print("  python3 dynamic_context_loader.py test")
        return
        
    command = sys.argv[1]
    
    if command == "analyze":
        if len(sys.argv) < 3:
            print("Error: analyze command requires input text")
            return
            
        user_input = " ".join(sys.argv[2:])
        domain, confidence = loader.analyze_request(user_input)
        strategy = loader.get_context_loading_strategy(user_input)
        
        print(f"Input: {user_input}")
        print(f"Detected Domain: {domain}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Strategy: {strategy['strategy_name']}")
        print(f"Token Savings: {strategy['savings']}%")
        print(f"Files to Load: {len(strategy['files'])}")
        
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: generate command requires input text")
            return
            
        user_input = " ".join(sys.argv[2:])
        instructions = loader.generate_context_instructions(user_input)
        print(instructions)
        
    elif command == "test":
        test_cases = [
            ("what is 2+2", "simple"),
            ("help me debug this Python code", "technical"),
            ("research market trends for AI", "research"),
            ("check for security vulnerabilities", "security"),
            ("schedule a meeting tomorrow", "personal"),
            ("deploy to AWS infrastructure", "cloud"),
            ("design a new logo", "design"),
            ("hello how are you", "simple")
        ]
        
        results = loader.test_domain_detection(test_cases)
        print(f"Domain Detection Test Results:")
        print(f"Accuracy: {results['accuracy']:.2%}")
        print(f"Correct: {results['correct']}/{results['total']}")
        print("\nDetails:")
        for detail in results["details"]:
            status = "✅" if detail["correct"] else "❌"
            print(f"{status} '{detail['input']}' -> {detail['detected']} (expected: {detail['expected']}, confidence: {detail['confidence']:.2f})")

if __name__ == "__main__":
    main()