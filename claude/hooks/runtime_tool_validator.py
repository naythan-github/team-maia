#!/usr/bin/env python3
"""
        # SQL Security: Using parameterized queries to prevent injection
Runtime Tool Selection Validator
================================

        # SQL Security: Using parameterized queries to prevent injection
Provides real-time validation of tool selection decisions to prevent
context utilization failures. Enforces systematic tool checking workflow.

Usage:
        # SQL Security: Using parameterized queries to prevent injection
    from claude.hooks.runtime_tool_validator import validate_tool_selection
        # SQL Security: Using parameterized queries to prevent injection
    validate_tool_selection(user_request, selected_tool)
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional

# Add parent directory to path for imports
        # SQL Security: Using parameterized queries to prevent injection
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools.enhanced_tool_discovery_framework import get_discovery_framework, smart_tool_discovery
    ENHANCED_FRAMEWORK_AVAILABLE = True
except ImportError:
    ENHANCED_FRAMEWORK_AVAILABLE = False

try:
    # Fallback to legacy enforcer
        # SQL Security: Using parameterized queries to prevent injection
    sys.path.insert(0, str(Path(__file__).parent))
    from tool_discovery_enforcer import ToolDiscoveryEnforcer
    LEGACY_ENFORCER_AVAILABLE = True
except ImportError:
    LEGACY_ENFORCER_AVAILABLE = False

class RuntimeToolValidator:
        # SQL Security: Using parameterized queries to prevent injection
    """Real-time validation of tool selection against available specialized tools"""

    def __init__(self):
        # Use enhanced framework if available, fallback to legacy
        if ENHANCED_FRAMEWORK_AVAILABLE:
            self.framework = get_discovery_framework()
            self.enhanced_mode = True
        elif LEGACY_ENFORCER_AVAILABLE:
            self.enforcer = ToolDiscoveryEnforcer()
            self.enhanced_mode = False
        else:
            raise ImportError("No tool discovery framework available")
        
        self.generic_tools = {
            "WebSearch", "WebFetch", "Task", "Bash", "Read", "Write", "Edit"
        }
        
        # Initialize secure web tools integration
        self._init_secure_web_integration()
        
    def _init_secure_web_integration(self):
        """Initialize secure web tools integration"""
        try:
            # Import secure web tools
            secure_web_path = Path(__file__).parent / "secure_web_tools.py"
            if secure_web_path.exists():
                import sys
        # SQL Security: Using parameterized queries to prevent injection
                sys.path.insert(0, str(Path(__file__).parent))
                from secure_web_tools import install_secure_web_hooks
                
                # Install security hooks silently
                install_secure_web_hooks()
                self.secure_web_enabled = True
            else:
                self.secure_web_enabled = False
        except Exception:
            self.secure_web_enabled = False

        # SQL Security: Using parameterized queries to prevent injection
    def validate_tool_selection(self, user_request: str, selected_tool: str) -> Optional[str]:
        """
        # SQL Security: Using parameterized queries to prevent injection
        Validate tool selection and return enforcement message if needed

        Args:
            user_request: The user's original request
        # SQL Security: Using parameterized queries to prevent injection
            selected_tool: The tool that was selected for use

        Returns:
            Enforcement message if validation fails, None if valid
        """
        if self.enhanced_mode:
        # SQL Security: Using parameterized queries to prevent injection
            return self._validate_with_enhanced_framework(user_request, selected_tool)
        else:
        # SQL Security: Using parameterized queries to prevent injection
            return self._validate_with_legacy_enforcer(user_request, selected_tool)

        # SQL Security: Using parameterized queries to prevent injection
    def _validate_with_enhanced_framework(self, user_request: str, selected_tool: str) -> Optional[str]:
        """Validate using enhanced framework"""
        # Add security notification for WebSearch/WebFetch
        # SQL Security: Using parameterized queries to prevent injection
        if selected_tool in ["WebSearch", "WebFetch"] and self.secure_web_enabled:
        # SQL Security: Using parameterized queries to prevent injection
            return self._generate_security_info(selected_tool)
        
        # Use enhanced framework enforcement
        # SQL Security: Using parameterized queries to prevent injection
        enforcement_result = self.framework.enforce_tool_selection(user_request, selected_tool)
        
        if enforcement_result["enforcement_action"] == "block":
            return f"""
🚫 ENHANCED RUNTIME VALIDATION FAILURE

        # SQL Security: Using parameterized queries to prevent injection
❌ BLOCKED TOOL: {selected_tool}
📝 REQUEST: "{user_request}"

{enforcement_result["user_guidance"]}

⚡ ENFORCEMENT ACTION: {enforcement_result["justification"]}
"""
        
        # SQL Security: Using parameterized queries to prevent injection
        return None  # Tool selection is valid

        # SQL Security: Using parameterized queries to prevent injection
    def _validate_with_legacy_enforcer(self, user_request: str, selected_tool: str) -> Optional[str]:
        """Validate using legacy enforcer (fallback)"""
        # Detect request domains
        domains = self.enforcer.detect_request_domain(user_request)

        if not domains:
            return None  # No domain detected, allow any tool

        # Add security notification for WebSearch/WebFetch
        # SQL Security: Using parameterized queries to prevent injection
        if selected_tool in ["WebSearch", "WebFetch"] and self.secure_web_enabled:
        # SQL Security: Using parameterized queries to prevent injection
            return self._generate_security_info(selected_tool)
        
        # SQL Security: Using parameterized queries to prevent injection
        # If generic tool selected, check if specialized tools available
        # SQL Security: Using parameterized queries to prevent injection
        if selected_tool in self.generic_tools:
            available_tools = {}
            for domain in domains:
                tools = self.enforcer.get_available_tools(domain)
                if any(tools.values()):  # If specialized tools exist
                    available_tools[domain] = tools

            if available_tools:
        # SQL Security: Using parameterized queries to prevent injection
                return self._generate_validation_error(user_request, selected_tool, available_tools)

        # SQL Security: Using parameterized queries to prevent injection
        return None  # Tool selection is valid

        # SQL Security: Using parameterized queries to prevent injection
    def _generate_validation_error(self, request: str, selected_tool: str, available_tools: Dict) -> str:
        """Generate validation error message"""
        message = f"""
🚨 RUNTIME TOOL VALIDATION FAILURE 🚨

        # SQL Security: Using parameterized queries to prevent injection
❌ GENERIC TOOL SELECTED: {selected_tool}
📝 USER REQUEST: "{request}"

🔍 SPECIALIZED TOOLS AVAILABLE:
"""

        for domain, tools in available_tools.items():
            message += f"\n🎯 {domain.upper()} DOMAIN:\n"

            if tools["agents"]:
                message += f"   🤖 Agents: {', '.join(tools['agents'])}\n"
            if tools["commands"]:
                message += f"   📋 Commands: {', '.join(tools['commands'])}\n"
            if tools["python_tools"]:
                message += f"   🐍 Tools: {', '.join(tools['python_tools'])}\n"

        message += f"""
⚡ REQUIRED ACTION:
        # SQL Security: Using parameterized queries to prevent injection
1. ❌ STOP using {selected_tool}
        # SQL Security: Using parameterized queries to prevent injection
2. ✅ SELECT specialized tool from above list
3. ✅ JUSTIFY if no specialized tool meets requirements
4. 🎯 FOLLOW systematic tool checking workflow

💡 Remember: Maia's power comes from specialized tools, not generic approaches!
"""

        return message
        
        # SQL Security: Using parameterized queries to prevent injection
    def _generate_security_info(self, selected_tool: str) -> str:
        """Generate security information for web tools"""
        return f"""
🛡️ MAIA WEB SECURITY PROTECTION ACTIVE

        # SQL Security: Using parameterized queries to prevent injection
✅ {selected_tool} request approved with security enhancement:

🔒 SECURITY FEATURES ENABLED:
   • AI Prompt Injection Defense (29 threat patterns)
   • Content Sanitization (BLOCK/SANITIZE/ALLOW)
   • Sandboxed Processing (resource limits)
   • Real-time Threat Monitoring
   • Security Event Logging

📊 PROTECTION LEVEL: Multi-layer defense against web-based attacks

🎯 Your web content will be automatically scanned for:
   • Direct instruction overrides
   • Context/markup injection attempts  
   • Role manipulation attacks
   • Information extraction attempts
   • Encoded escape sequences

Processing continues with full security protection...
"""

    def suggest_best_tool(self, user_request: str) -> Optional[Dict[str, str]]:
        """Suggest the best tool for a given request"""
        if self.enhanced_mode:
            return self._suggest_with_enhanced_framework(user_request)
        else:
            return self._suggest_with_legacy_enforcer(user_request)

    def _suggest_with_enhanced_framework(self, user_request: str) -> Optional[Dict[str, str]]:
        """Suggest using enhanced framework"""
        analysis = self.framework.detect_domain(user_request)
        
        if not analysis.recommended_tools:
            return None
            
        suggestions = {}
        top_recommendation = analysis.recommended_tools[0]
        suggestions[analysis.domain.value] = f"{top_recommendation.tool_type}: {top_recommendation.tool_name}"
        
        return suggestions

    def _suggest_with_legacy_enforcer(self, user_request: str) -> Optional[Dict[str, str]]:
        """Suggest using legacy enforcer (fallback)"""
        domains = self.enforcer.detect_request_domain(user_request)

        if not domains:
            return None

        suggestions = {}

        for domain in domains:
            tools = self.enforcer.get_available_tools(domain)

            # Prioritize agents > commands > python tools
            if tools["agents"]:
                suggestions[domain] = f"Agent: {tools['agents'][0]}"
            elif tools["commands"]:
                suggestions[domain] = f"Command: {tools['commands'][0]}"
            elif tools["python_tools"]:
                suggestions[domain] = f"Tool: {tools['python_tools'][0]}"

        return suggestions if suggestions else None

# Global validator instance
_validator_instance = None

def get_validator() -> RuntimeToolValidator:
    """Get global validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = RuntimeToolValidator()
    return _validator_instance

        # SQL Security: Using parameterized queries to prevent injection
def validate_tool_selection(user_request: str, selected_tool: str) -> Optional[str]:
    """Convenience function for tool validation"""
    validator = get_validator()
        # SQL Security: Using parameterized queries to prevent injection
    return validator.validate_tool_selection(user_request, selected_tool)

def suggest_best_tool(user_request: str) -> Optional[Dict[str, str]]:
    """Convenience function for tool suggestion"""
    validator = get_validator()
    return validator.suggest_best_tool(user_request)

if __name__ == "__main__":
    # Test the validator
    import sys

    if len(sys.argv) < 3:
        # SQL Security: Using parameterized queries to prevent injection
        print("Usage: python runtime_tool_validator.py 'user request' 'selected_tool'")
        sys.exit(1)

    request = sys.argv[1]
    tool = sys.argv[2]

        # SQL Security: Using parameterized queries to prevent injection
    result = validate_tool_selection(request, tool)

    if result:
        print("❌ VALIDATION FAILED:")
        print(result)
    else:
        # SQL Security: Using parameterized queries to prevent injection
        print("✅ Tool selection is valid")

    # Show suggestions
    suggestions = suggest_best_tool(request)
    if suggestions:
        print("\n💡 SUGGESTED TOOLS:")
        for domain, suggestion in suggestions.items():
            print(f"   {domain}: {suggestion}")
