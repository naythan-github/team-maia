#!/usr/bin/env python3
"""
Model Enforcement Webhook
Technical enforcement of Sonnet default with Opus permission gates
Blocks Opus usage without explicit user permission
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Portable path resolution
try:
    from claude.tools.core.paths import DATA_DIR
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from claude.tools.core.paths import DATA_DIR

class ModelEnforcementWebhook:
    """Technical enforcement of model selection policies"""

    def __init__(self):
        # Use portable paths
        self.log_file = Path(DATA_DIR) / 'model_enforcement_log.jsonl'

        self.permission_cache = {}
        self.session_start = datetime.now().isoformat()

        # Create log file if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()
    
    def check_opus_permission(self, task_description: str, context: str = "") -> Dict[str, Any]:
        """Check if Opus usage is permitted for this task"""
        
        # Analyze task to see if Opus might be justified
        task_lower = task_description.lower()
        context_lower = context.lower()
        
        # Security-related tasks that might justify Opus
        security_keywords = [
            'security', 'vulnerability', 'audit', 'compliance', 
            'threat', 'risk assessment', 'penetration test', 'exploit'
        ]
        
        # Critical business keywords that might justify Opus  
        critical_keywords = [
            'critical business', 'high stakes', 'strategic decision',
            'board presentation', 'acquisition', 'merger', 'legal'
        ]
        
        # Tasks that should NEVER use Opus
        never_opus_keywords = [
            'linkedin', 'profile optimization', 'content strategy',
            'blog post', 'social media', 'email', 'calendar',
            'file operation', 'read file', 'data processing',
            'simple analysis', 'basic research', 'formatting'
        ]
        
        # Check if task should never use Opus
        if any(keyword in task_lower or keyword in context_lower for keyword in never_opus_keywords):
            return {
                "permission": "denied",
                "reason": "Task should use Sonnet - no Opus justification",
                "recommended_model": "sonnet",
                "cost_savings": "80% cost reduction with Sonnet",
                "message": f"❌ OPUS BLOCKED: '{task_description[:50]}...' should use Sonnet (5x cheaper, same quality)"
            }
        
        # Check if task might justify Opus
        might_need_opus = any(keyword in task_lower or keyword in context_lower for keyword in security_keywords + critical_keywords)
        
        if might_need_opus:
            return {
                "permission": "request_required", 
                "reason": "Task might benefit from Opus capabilities",
                "recommended_model": "sonnet_first",
                "cost_comparison": "Opus: $0.075 vs Sonnet: $0.015 per session",
                "message": f"⚠️  OPUS REQUEST: Task '{task_description[:50]}...' might benefit from Opus. Try Sonnet first? (5x cheaper)"
            }
        
        # Default: Sonnet is sufficient
        return {
            "permission": "denied",
            "reason": "Standard task - Sonnet provides 90% capability at 20% cost",
            "recommended_model": "sonnet", 
            "cost_savings": "80% cost reduction with Sonnet",
            "message": f"✅ SONNET RECOMMENDED: '{task_description[:50]}...' - perfect for Sonnet"
        }
    
    def log_enforcement_action(self, action: str, task: str, decision: Dict[str, Any]):
        """Log enforcement decisions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": self.session_start,
            "action": action,
            "task": task[:100],  # Truncate for privacy
            "decision": decision["permission"],
            "reason": decision["reason"],
            "recommended_model": decision.get("recommended_model"),
            "message": decision["message"]
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def enforce_pre_execution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-execution enforcement hook"""
        
        task_description = request.get("task", request.get("prompt", ""))
        context = request.get("context", "")
        requested_model = request.get("model", "unknown")
        
        # Check if Opus is being requested
        if "opus" in requested_model.lower():
            decision = self.check_opus_permission(task_description, context)
            self.log_enforcement_action("opus_request", task_description, decision)
            
            if decision["permission"] == "denied":
                print(decision["message"])
                return {
                    "allowed": False,
                    "redirect_model": "sonnet",
                    "message": decision["message"],
                    "cost_savings": decision.get("cost_savings")
                }
            elif decision["permission"] == "request_required":
                print(decision["message"])
                # In a real implementation, this would prompt the user
                # For now, default to Sonnet
                return {
                    "allowed": False,
                    "redirect_model": "sonnet", 
                    "message": "Defaulting to Sonnet - request permission for Opus if needed",
                    "cost_savings": "80% cost reduction vs Opus"
                }
        
        # Allow Sonnet and local models
        return {
            "allowed": True,
            "message": f"✅ Model enforcement passed: {requested_model}"
        }
    
    def enforce_continue_command(self) -> Dict[str, Any]:
        """Special enforcement for 'continue' commands when tokens overflow"""
        
        print("🚨 CONTINUE COMMAND DETECTED - Enforcing model selection")
        print("💡 Token overflow often triggers unwanted Opus usage")
        
        # Force Sonnet for continue commands
        decision = {
            "permission": "denied",
            "reason": "Continue commands should use Sonnet for consistency",
            "recommended_model": "sonnet",
            "message": "🔒 CONTINUE ENFORCEMENT: Using Sonnet to prevent Opus escalation"
        }
        
        self.log_enforcement_action("continue_command", "token_overflow_continue", decision)
        
        return {
            "allowed": False,
            "redirect_model": "sonnet",
            "message": decision["message"],
            "note": "Continue commands automatically use Sonnet to prevent cost escalation"
        }
    
    def get_enforcement_stats(self) -> Dict[str, Any]:
        """Get enforcement statistics"""
        try:
            with open(self.log_file, 'r') as f:
                logs = [json.loads(line.strip()) for line in f if line.strip()]
            
            stats = {
                "total_requests": len(logs),
                "opus_blocked": len([l for l in logs if l["decision"] == "denied"]),
                "sonnet_recommended": len([l for l in logs if l["recommended_model"] == "sonnet"]),
                "continue_enforcements": len([l for l in logs if l["action"] == "continue_command"]),
                "estimated_cost_savings": len([l for l in logs if l["decision"] == "denied"]) * 0.06,  # $0.06 per Opus prevention
                "session": self.session_start
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Could not load stats: {e}"}

# Global enforcement instance
_model_enforcement = None

def get_model_enforcement() -> ModelEnforcementWebhook:
    """Get global model enforcement instance"""
    global _model_enforcement
    if _model_enforcement is None:
        _model_enforcement = ModelEnforcementWebhook()
    return _model_enforcement

def enforce_model_selection(task: str, model: str = "unknown", context: str = "") -> Dict[str, Any]:
    """Main enforcement function"""
    enforcement = get_model_enforcement()
    
    request = {
        "task": task,
        "model": model,
        "context": context
    }
    
    return enforcement.enforce_pre_execution(request)

def enforce_continue_command() -> Dict[str, Any]:
    """Enforce model selection for continue commands"""
    enforcement = get_model_enforcement()
    return enforcement.enforce_continue_command()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Enforcement Webhook")
    parser.add_argument("--check-task", help="Check task for model enforcement")
    parser.add_argument("--continue-command", action="store_true", help="Enforce continue command")
    args = parser.parse_args()
    
    if args.check_task:
        # Quick enforcement check for hook integration
        result = enforce_model_selection(args.check_task, "opus")  # Assume Opus to test enforcement
        if not result["allowed"]:
            print(f"🔒 {result['message']}")
            print(f"   💰 {result.get('cost_savings', 'Cost protection active')}")
        sys.exit(0)
    
    if args.continue_command:
        # Continue command enforcement
        result = enforce_continue_command()
        print(result["message"])
        sys.exit(0)
    
    # Default: Test the enforcement system
    print("🧪 Testing Model Enforcement Webhook")
    print("=" * 50)
    
    enforcement = ModelEnforcementWebhook()
    
    # Test cases
    test_cases = [
        ("LinkedIn profile optimization", "opus"),
        ("Security vulnerability assessment", "opus"),
        ("Blog post creation", "opus"), 
        ("Continue with the analysis", "opus"),
        ("Strategic cloud architecture", "sonnet"),
    ]
    
    for task, model in test_cases:
        print(f"\n🔍 Testing: '{task}' with {model}")
        result = enforce_model_selection(task, model)
        print(f"   Result: {'✅ Allowed' if result['allowed'] else '❌ Blocked'}")
        print(f"   Message: {result['message']}")
        if not result['allowed']:
            print(f"   Redirect: {result.get('redirect_model')}")
    
    # Test continue command
    print(f"\n🔍 Testing: Continue command enforcement")
    result = enforce_continue_command()
    print(f"   Result: {'✅ Allowed' if result['allowed'] else '❌ Blocked'}")
    print(f"   Message: {result['message']}")
    
    # Show stats
    stats = enforcement.get_enforcement_stats()
    print(f"\n📊 Enforcement Stats:")
    print(f"   Total requests: {stats.get('total_requests', 0)}")
    print(f"   Opus blocked: {stats.get('opus_blocked', 0)}")
    print(f"   Continue enforcements: {stats.get('continue_enforcements', 0)}")
    print(f"   Estimated savings: ${stats.get('estimated_cost_savings', 0):.2f}")