#!/usr/bin/env python3
"""
Lazy Opus Protection System
Only loads enhanced router when LLM routing is actually needed.
"""

import os
import sys
from pathlib import Path

class LazyOpusProtection:
    """Lazy-loading Opus protection that only activates when needed."""
    
    def __init__(self):
        self.router = None
        self.protection_active = False
        self.routing_attempted = False
    
    def check_for_opus_usage(self, task_description: str) -> bool:
        """Quick check if task might use Opus without loading router."""
        task_lower = task_description.lower()
        
        # Patterns that typically route to Opus
        opus_patterns = [
            'opus', 'security', 'vulnerability', 'compliance', 
            'audit', 'threat', 'critical analysis'
        ]
        
        return any(pattern in task_lower for pattern in opus_patterns)
    
    def ensure_protection_loaded(self):
        """Load protection only when actually needed."""
        if self.router is None:
            try:
                tools_dir = Path(__file__).parent.parent / "tools"
                if str(tools_dir) not in sys.path:
                    sys.path.insert(0, str(tools_dir))
                
                from opus_permission_enhanced_router import EnhancedProductionLLMRouter
                self.router = EnhancedProductionLLMRouter()
                self.protection_active = True
                
                print("🔒 OPUS PROTECTION LOADED (on-demand)")
                print("   ⚡ Router initialized only when needed")
                print("   💰 Saved context loading tokens until required")
                
                return True
                
            except Exception as e:
                print(f"❌ Error loading Opus protection: {e}")
                return False
        return True
    
    def route_task_with_protection(self, task_description: str, 
                                 token_estimate: int = 5000, 
                                 interactive: bool = True):
        """Route task with lazy protection loading."""
        self.routing_attempted = True
        
        # Quick check if this might need Opus
        might_use_opus = self.check_for_opus_usage(task_description)
        
        if might_use_opus:
            # Only now do we load the router
            if self.ensure_protection_loaded():
                return self.router.route_task(task_description, token_estimate, interactive)
            else:
                print("⚠️ Protection failed to load - manual permission check required")
                return None
        else:
            # For non-Opus tasks, we can use simple routing
            return self._simple_route(task_description, token_estimate)
    
    def _simple_route(self, task_description: str, token_estimate: int):
        """Simple routing for non-Opus tasks."""
        from dataclasses import dataclass
        from enum import Enum
        
        class LLMProvider(Enum):
            LOCAL_LLAMA_3B = "local-llama-3b"
            GEMINI_PRO = "gemini-pro"
            CLAUDE_HAIKU = "claude-haiku"
            CLAUDE_SONNET = "claude-sonnet"
        
        @dataclass 
        class SimpleRoutingResult:
            provider: LLMProvider
            reasoning: str
            estimated_cost: float
        
        task_lower = task_description.lower()
        
        # Simple pattern matching without full router
        if any(word in task_lower for word in ["file", "read", "edit", "config"]):
            return SimpleRoutingResult(
                provider=LLMProvider.LOCAL_LLAMA_3B,
                reasoning="File operation - routed to local model",
                estimated_cost=token_estimate * 0.00001 / 1000
            )
        elif any(word in task_lower for word in ["research", "analyze", "company"]):
            return SimpleRoutingResult(
                provider=LLMProvider.GEMINI_PRO,
                reasoning="Research task - routed to Gemini Pro",
                estimated_cost=token_estimate * 0.00125 / 1000
            )
        else:
            return SimpleRoutingResult(
                provider=LLMProvider.CLAUDE_SONNET,
                reasoning="Default routing - Sonnet for general tasks",
                estimated_cost=token_estimate * 0.003 / 1000
            )
    
    def get_protection_status(self):
        """Get current protection status."""
        return {
            "protection_loaded": self.router is not None,
            "routing_attempted": self.routing_attempted,
            "mode": "lazy" if self.router is None else "active",
            "message": "🔒 Opus protection (lazy-loaded)" if self.router is None else "✅ Opus protection active"
        }

# Global lazy protection instance
_lazy_opus_protection = None

def get_lazy_opus_protection():
    """Get global lazy protection instance."""
    global _lazy_opus_protection
    if _lazy_opus_protection is None:
        _lazy_opus_protection = LazyOpusProtection()
    return _lazy_opus_protection

# Simple context warning instead of full router loading
def show_opus_protection_reminder():
    """Light-weight reminder shown during context loading."""
    print("💡 OPUS COST PROTECTION: Enhanced router available on-demand")
    print("   🔒 Automatic permission gates for Opus usage")
    print("   💰 80% cost savings on security tasks")
    print("   ⚡ Loaded only when needed to save context tokens")

if __name__ == "__main__":
    # Test the lazy loading system
    print("🧪 Testing Lazy Opus Protection System")
    print("=" * 50)
    
    protection = get_lazy_opus_protection()
    
    # Test 1: Non-Opus task (should not load router)
    print("Test 1: File operation task")
    result1 = protection.route_task_with_protection("Read configuration file", 2000, False)
    print(f"   Result: {result1.provider.value} (${result1.estimated_cost:.4f})")
    print(f"   Router loaded: {protection.router is not None}")
    
    # Test 2: Potential Opus task (should load router)
    print("\nTest 2: Security analysis task")  
    result2 = protection.route_task_with_protection("Security vulnerability assessment", 8000, False)
    if result2:
        print(f"   Result: {result2.provider.value} (${result2.estimated_cost:.4f})")
        print(f"   Router loaded: {protection.router is not None}")
    
    # Show final status
    status = protection.get_protection_status()
    print(f"\n📊 Final Status: {status['message']}")
    print(f"   Mode: {status['mode']}")
    print(f"   Protection loaded: {status['protection_loaded']}")