#!/usr/bin/env python3
"""
Systematic Thinking Enforcement Webhook
Technical enforcement of systematic optimization framework
Blocks responses that don't follow Problem Analysis → Solution Exploration → Recommendation pattern
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class SystematicThinkingEnforcementWebhook:
    """Technical enforcement of systematic thinking framework"""
    
    def __init__(self):
        self.log_file = str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "systematic_thinking_enforcement_log.jsonl"
        self.session_start = datetime.now().isoformat()
        
        # Create log file if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("")
    
    def analyze_response_structure(self, response: str) -> Dict[str, Any]:
        """Analyze if response follows systematic thinking framework"""
        
        response_lower = response.lower()
        
        # Phase 1: Problem Decomposition indicators
        problem_analysis_indicators = [
            "problem analysis", "problem decomposition", "underlying issue",
            "stakeholders affected", "constraints", "success criteria",
            "real problem", "actual issue", "stakeholder mapping",
            "constraint analysis", "success definition"
        ]
        
        # Phase 2: Solution Exploration indicators  
        solution_exploration_indicators = [
            "solution options", "solution exploration", "option a", "option b", "option c",
            "approaches", "alternatives", "pros and cons", "trade-offs",
            "risk assessment", "implementation complexity", "multiple approaches"
        ]
        
        # Phase 3: Optimized Implementation indicators
        implementation_indicators = [
            "recommended approach", "implementation plan", "validation strategy",
            "rollback plan", "success metrics", "risk mitigation",
            "implementation", "recommendation", "optimized"
        ]
        
        # Check for systematic structure
        has_problem_analysis = any(indicator in response_lower for indicator in problem_analysis_indicators)
        has_solution_exploration = any(indicator in response_lower for indicator in solution_exploration_indicators)
        has_implementation = any(indicator in response_lower for indicator in implementation_indicators)
        
        # Check for immediate solution without analysis (anti-pattern)
        immediate_solution_patterns = [
            r"^(here's how|just|simply|you should|the solution is)",
            r"^(i'll|let me|i can help)",
            r"^(to solve this|to fix this)"
        ]
        
        immediate_solution = any(re.match(pattern, response_lower.strip()) for pattern in immediate_solution_patterns)
        
        # Count multiple solution approaches
        multiple_solutions = len(re.findall(r"option [abc]|approach [123]|alternative [123]|solution [123]", response_lower))
        
        # Systematic thinking score
        systematic_score = 0
        if has_problem_analysis:
            systematic_score += 40
        if has_solution_exploration:
            systematic_score += 35
        if has_implementation:
            systematic_score += 25
        if multiple_solutions >= 2:
            systematic_score += 20
        if immediate_solution:
            systematic_score -= 30
            
        # Determine compliance level
        if systematic_score >= 80:
            compliance = "excellent"
        elif systematic_score >= 60:
            compliance = "good"
        elif systematic_score >= 40:
            compliance = "partial"
        else:
            compliance = "poor"
            
        return {
            "systematic_score": systematic_score,
            "compliance_level": compliance,
            "has_problem_analysis": has_problem_analysis,
            "has_solution_exploration": has_solution_exploration,
            "has_implementation": has_implementation,
            "multiple_solutions": multiple_solutions,
            "immediate_solution": immediate_solution,
            "passed": systematic_score >= 60  # Minimum threshold
        }
    
    def check_response_compliance(self, response: str, task: str = "") -> Dict[str, Any]:
        """Check if response follows systematic thinking framework"""
        
        analysis = self.analyze_response_structure(response)
        
        if analysis["passed"]:
            return {
                "compliance": "passed",
                "score": analysis["systematic_score"],
                "level": analysis["compliance_level"],
                "message": f"✅ SYSTEMATIC THINKING: Response follows framework (Score: {analysis['systematic_score']}/100)",
                "feedback": self._generate_positive_feedback(analysis)
            }
        else:
            return {
                "compliance": "failed",
                "score": analysis["systematic_score"],
                "level": analysis["compliance_level"],
                "message": f"❌ SYSTEMATIC THINKING VIOLATION: Response lacks systematic analysis (Score: {analysis['systematic_score']}/100)",
                "required_improvements": self._generate_improvement_guidance(analysis),
                "framework_reminder": self._get_framework_reminder()
            }
    
    def _generate_positive_feedback(self, analysis: Dict) -> str:
        """Generate positive feedback for compliant responses"""
        feedback = []
        
        if analysis["has_problem_analysis"]:
            feedback.append("✅ Problem decomposition present")
        if analysis["has_solution_exploration"]:
            feedback.append("✅ Solution exploration included")
        if analysis["has_implementation"]:
            feedback.append("✅ Implementation guidance provided")
        if analysis["multiple_solutions"] >= 2:
            feedback.append(f"✅ Multiple approaches considered ({analysis['multiple_solutions']})")
            
        return " | ".join(feedback)
    
    def _generate_improvement_guidance(self, analysis: Dict) -> List[str]:
        """Generate specific improvement guidance"""
        improvements = []
        
        if not analysis["has_problem_analysis"]:
            improvements.append("🔍 Add problem decomposition: Analyze the real underlying issue, stakeholders, constraints, and success criteria")
            
        if not analysis["has_solution_exploration"]:
            improvements.append("💡 Include solution exploration: Present 2-3 different approaches with pros/cons and trade-offs")
            
        if not analysis["has_implementation"]:
            improvements.append("✅ Provide implementation guidance: Include validation strategy, risk mitigation, and success metrics")
            
        if analysis["multiple_solutions"] < 2:
            improvements.append("🔀 Consider multiple approaches: Present at least 2-3 solution options before recommending")
            
        if analysis["immediate_solution"]:
            improvements.append("⚠️ Avoid immediate solutions: Start with problem analysis before jumping to solutions")
            
        return improvements
    
    def _get_framework_reminder(self) -> str:
        """Get systematic thinking framework reminder"""
        return """
🧠 SYSTEMATIC THINKING FRAMEWORK REQUIRED:

Phase 1: Problem Analysis
- Real underlying issue identification
- Stakeholder mapping and impact analysis  
- Constraint analysis and success criteria
- Second/third-order consequences

Phase 2: Solution Exploration  
- Generate 2-3 different approaches
- Comprehensive pros/cons for each
- Risk assessment and complexity analysis
- Implementation trade-offs

Phase 3: Optimized Implementation
- Clear recommendation with reasoning
- Validation and testing strategy
- Risk mitigation and rollback plans
- Success measurement criteria
"""
    
    def log_enforcement_action(self, action: str, task: str, response_preview: str, analysis: Dict[str, Any]):
        """Log enforcement decisions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": self.session_start,
            "action": action,
            "task": task[:100] if task else "unknown",
            "response_preview": response_preview[:200],  # First 200 chars
            "systematic_score": analysis.get("systematic_score", 0),
            "compliance_level": analysis.get("compliance_level", "unknown"),
            "passed": analysis.get("passed", False),
            "has_problem_analysis": analysis.get("has_problem_analysis", False),
            "has_solution_exploration": analysis.get("has_solution_exploration", False),
            "has_implementation": analysis.get("has_implementation", False),
            "multiple_solutions": analysis.get("multiple_solutions", 0)
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def enforce_response_structure(self, response: str, task: str = "", context: str = "") -> Dict[str, Any]:
        """Main enforcement function for response structure"""
        
        # Skip enforcement for very short responses (< 100 chars) - likely quick answers
        if len(response.strip()) < 100:
            return {
                "allowed": True,
                "message": "✅ Short response - enforcement skipped",
                "note": "Systematic thinking enforcement applies to longer responses"
            }
        
        # Check compliance
        compliance_result = self.check_response_compliance(response, task)
        analysis = self.analyze_response_structure(response)
        
        # Log the enforcement action
        self.log_enforcement_action("response_check", task, response[:200], analysis)
        
        if compliance_result["compliance"] == "passed":
            return {
                "allowed": True,
                "message": compliance_result["message"],
                "feedback": compliance_result["feedback"],
                "score": compliance_result["score"]
            }
        else:
            return {
                "allowed": False,
                "message": compliance_result["message"],
                "improvements": compliance_result["required_improvements"], 
                "framework": compliance_result["framework_reminder"],
                "score": compliance_result["score"],
                "guidance": "Please restructure response to follow systematic thinking framework"
            }
    
    def get_enforcement_stats(self) -> Dict[str, Any]:
        """Get enforcement statistics"""
        try:
            with open(self.log_file, 'r') as f:
                logs = [json.loads(line.strip()) for line in f if line.strip()]
            
            if not logs:
                return {"total_responses": 0, "message": "No enforcement data yet"}
            
            stats = {
                "total_responses": len(logs),
                "passed": len([l for l in logs if l.get("passed", False)]),
                "failed": len([l for l in logs if not l.get("passed", False)]),
                "average_score": sum(l.get("systematic_score", 0) for l in logs) / len(logs),
                "compliance_rate": (len([l for l in logs if l.get("passed", False)]) / len(logs)) * 100,
                "problem_analysis_rate": (len([l for l in logs if l.get("has_problem_analysis", False)]) / len(logs)) * 100,
                "solution_exploration_rate": (len([l for l in logs if l.get("has_solution_exploration", False)]) / len(logs)) * 100,
                "implementation_rate": (len([l for l in logs if l.get("has_implementation", False)]) / len(logs)) * 100,
                "session": self.session_start
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Could not load stats: {e}"}

# Global enforcement instance
_systematic_thinking_enforcement = None

def get_systematic_thinking_enforcement() -> SystematicThinkingEnforcementWebhook:
    """Get global systematic thinking enforcement instance"""
    global _systematic_thinking_enforcement
    if _systematic_thinking_enforcement is None:
        _systematic_thinking_enforcement = SystematicThinkingEnforcementWebhook()
    return _systematic_thinking_enforcement

def enforce_systematic_thinking(response: str, task: str = "", context: str = "") -> Dict[str, Any]:
    """Main enforcement function"""
    enforcement = get_systematic_thinking_enforcement()
    return enforcement.enforce_response_structure(response, task, context)

def check_response_compliance(response: str) -> Dict[str, Any]:
    """Quick compliance check without logging"""
    enforcement = get_systematic_thinking_enforcement()
    return enforcement.check_response_compliance(response)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Systematic Thinking Enforcement Webhook")
    parser.add_argument("--check-response", help="Check response for systematic thinking compliance")
    parser.add_argument("--stats", action="store_true", help="Show enforcement statistics")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    args = parser.parse_args()
    
    if args.check_response:
        # Quick compliance check
        result = check_response_compliance(args.check_response)
        print(f"Score: {result['score']}/100 - {result['compliance']}")
        if result['compliance'] == "failed":
            print("Required improvements:")
            for improvement in result.get('required_improvements', []):
                print(f"  {improvement}")
        sys.exit(0)
    
    if args.stats:
        # Show enforcement statistics
        enforcement = get_systematic_thinking_enforcement()
        stats = enforcement.get_enforcement_stats()
        print("📊 Systematic Thinking Enforcement Stats:")
        print(f"   Total responses: {stats.get('total_responses', 0)}")
        print(f"   Compliance rate: {stats.get('compliance_rate', 0):.1f}%")
        print(f"   Average score: {stats.get('average_score', 0):.1f}/100")
        print(f"   Problem analysis: {stats.get('problem_analysis_rate', 0):.1f}%")
        print(f"   Solution exploration: {stats.get('solution_exploration_rate', 0):.1f}%")
        print(f"   Implementation: {stats.get('implementation_rate', 0):.1f}%")
        sys.exit(0)
    
    if args.test:
        # Test the enforcement system
        print("🧪 Testing Systematic Thinking Enforcement Webhook")
        print("=" * 60)
        
        enforcement = SystematicThinkingEnforcementWebhook()
        
        # Test cases
        test_cases = [
            # Good systematic response
            ("Good Example", """
            🔍 Problem Analysis:
            The real underlying issue is determining the best approach for implementation.
            Stakeholders include the development team and end users.
            Constraints are time and budget limitations.
            Success criteria involve user satisfaction and system performance.
            
            💡 Solution Exploration:
            Option A: Quick implementation with basic features
            - Pros: Fast delivery, lower cost
            - Cons: Limited functionality, technical debt
            
            Option B: Comprehensive solution with full features  
            - Pros: Complete functionality, scalable
            - Cons: Higher cost, longer timeline
            
            ✅ Recommended Approach: Option B
            Implementation plan includes testing phases and rollback procedures.
            """),
            
            # Poor immediate solution
            ("Bad Example", "Just use Option A. It's the best choice and will solve your problem quickly."),
            
            # Short response (should be allowed)
            ("Short Response", "Yes, that works.")
        ]
        
        for name, response in test_cases:
            print(f"\n🔍 Testing: {name}")
            result = enforce_systematic_thinking(response, f"test_{name.lower()}")
            print(f"   Result: {'✅ Allowed' if result['allowed'] else '❌ Blocked'}")
            print(f"   Score: {result.get('score', 'N/A')}/100")
            print(f"   Message: {result['message']}")
            if not result['allowed'] and 'improvements' in result:
                print("   Required improvements:")
                for improvement in result['improvements'][:2]:  # Show first 2
                    print(f"     {improvement}")
        
        # Show final stats
        stats = enforcement.get_enforcement_stats()
        print(f"\n📊 Test Results:")
        print(f"   Responses tested: {stats.get('total_responses', 0)}")
        print(f"   Compliance rate: {stats.get('compliance_rate', 0):.1f}%")
        print(f"   Average score: {stats.get('average_score', 0):.1f}/100")
        
        sys.exit(0)
    
    # Default: Show usage
    print("Systematic Thinking Enforcement Webhook")
    print("Usage:")
    print("  --check-response 'text'  Check response compliance")
    print("  --stats                  Show enforcement statistics") 
    print("  --test                   Run test suite")