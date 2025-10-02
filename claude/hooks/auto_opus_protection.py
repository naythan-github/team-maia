#!/usr/bin/env python3
"""
Auto Opus Protection Hook
Automatically loads enhanced router in new context windows to prevent unauthorized Opus usage.
"""

import os
import sys
import logging
from pathlib import Path

# Add claude tools to path
claude_dir = Path(__file__).parent.parent
sys.path.insert(0, str(claude_dir))

logger = logging.getLogger(__name__)

class AutoOpusProtection:
    """Automatically initialize Opus protection on new context load."""
    
    def __init__(self):
        self.router = None
        self.protection_active = False
    
    def initialize_protection(self):
        """Initialize enhanced router with Opus permission control."""
        try:
            # Add tools directory to path for direct import
            tools_dir = Path(__file__).parent.parent / "tools"
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            
            from opus_permission_enhanced_router import EnhancedProductionLLMRouter
            self.router = EnhancedProductionLLMRouter()
            self.protection_active = True
            
            print("🔒 OPUS PROTECTION INITIALIZED")
            print("   ✅ Enhanced router loaded")
            print("   ✅ All Opus usage requires explicit permission")
            print("   ✅ Cost protection active (80% savings on security tasks)")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  Warning: Could not load enhanced router: {e}")
            print("   Opus protection not active - manual router usage required")
            return False
        except Exception as e:
            print(f"❌ Error initializing Opus protection: {e}")
            return False
    
    def get_protection_status(self):
        """Get current protection status."""
        return {
            "active": self.protection_active,
            "router_loaded": self.router is not None,
            "message": "✅ Opus protection active" if self.protection_active else "❌ Opus protection not active"
        }
    
    def route_task(self, task_description: str, token_estimate: int = 5000, interactive: bool = True):
        """Route task through enhanced router if available."""
        if self.router:
            return self.router.route_task(task_description, token_estimate, interactive)
        else:
            print("⚠️  Warning: Enhanced router not available - using default routing")
            print("   Manual Opus permission checking required")
            return None

# Global protection instance
_opus_protection = None

def get_opus_protection():
    """Get global Opus protection instance."""
    global _opus_protection
    if _opus_protection is None:
        _opus_protection = AutoOpusProtection()
        _opus_protection.initialize_protection()
    return _opus_protection

def auto_initialize_opus_protection():
    """Automatically initialize Opus protection (called on import)."""
    protection = get_opus_protection()
    return protection.get_protection_status()

# Auto-initialize when module is imported
if __name__ != "__main__":
    auto_initialize_opus_protection()

if __name__ == "__main__":
    # Test the protection system
    print("🧪 Testing Auto Opus Protection System")
    print("=" * 50)
    
    protection = get_opus_protection()
    status = protection.get_protection_status()
    
    print(f"Status: {status['message']}")
    print(f"Router loaded: {status['router_loaded']}")
    print(f"Protection active: {status['active']}")
    
    if protection.router:
        # Test routing
        test_task = "Perform security vulnerability assessment"
        result = protection.route_task(test_task, 8000, interactive=False)
        
        if result:
            print(f"\nTest routing: {test_task}")
            print(f"Route to: {result.provider.value}")
            print(f"Cost: ${result.estimated_cost:.4f}")
            print(f"Reasoning: {result.reasoning}")
        
        # Show permission stats
        report = protection.router.get_opus_permission_report()
        control = report["opus_permission_control"]
        print(f"\nPermission Control Status: {control['status']}")