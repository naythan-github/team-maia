#!/usr/bin/env python3
"""
Auto Verification Enforcer
Automatically intercepts and validates high-risk operations before execution
"""

import functools
import inspect
import re
from typing import Any, Callable, Dict, List
import sys
import os
from pathlib import Path

# Add maia root to path for imports
maia_root = os.environ.get('MAIA_ROOT')
if not maia_root:
    current_file = Path(__file__)
    for parent in current_file.parents:
        if (parent / 'claude').exists() and (parent / 'CLAUDE.md').exists():
            maia_root = str(parent)
            break
    if not maia_root:
        maia_root = str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd())

sys.path.insert(0, maia_root)

from claude.hooks.pre_execution_verification_hook import get_verification_hook, log_assumption_failure

class VerificationEnforcer:
    """Decorator-based system for enforcing verification"""
    
    def __init__(self):
        self.hook = get_verification_hook()
        self.bypass_verification = False  # Emergency bypass
        
    def require_verification(self, action_type: str, risk_level: str = "auto"):
        """Decorator to require verification before function execution"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.bypass_verification:
                    return func(*args, **kwargs)
                
                # Extract target resource from function arguments
                target_resource = self._extract_target_resource(func, args, kwargs)
                
                # Create action description
                action_description = f"{func.__name__}({', '.join(str(arg)[:50] for arg in args[:2])})"
                
                # Enforce verification
                verification_result = self.hook.enforce_verification(
                    action_type, action_description, target_resource
                )
                
                if not verification_result['allowed']:
                    error_msg = f"""
🚨 VERIFICATION REQUIRED 🚨

Function: {func.__name__}
Risk Level: {verification_result['risk_level']}
Reason: {verification_result['message']}

Required Actions:
{chr(10).join('- ' + req for req in verification_result.get('requirements', []))}

Suggested Verification Steps:
{chr(10).join('- ' + action for action in verification_result.get('suggested_actions', []))}

Complete verification first, then retry the operation.
                    """
                    raise VerificationRequiredException(error_msg)
                
                # If verified, proceed with function
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Log if this appears to be an assumption failure
                    if any(indicator in str(e).lower() for indicator in ['not found', 'does not exist', 'unexpected keyword', 'has no attribute']):
                        log_assumption_failure(
                            assumed_interface=f"{func.__name__}({', '.join(str(arg)[:30] for arg in args[:2])})",
                            actual_interface="Unknown - failed execution",
                            error_message=str(e),
                            recovery_action="Manual error recovery required"
                        )
                    raise
                    
            return wrapper
        return decorator
    
    def _extract_target_resource(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Extract target resource from function arguments"""
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Look for common resource indicators
        resource_indicators = ['file_path', 'path', 'url', 'script_path', 'target', 'resource']
        
        for param_name, value in bound_args.arguments.items():
            if param_name.lower() in resource_indicators:
                return str(value)
            
            # Check if value looks like a file path
            if isinstance(value, str) and ('/' in value or '\\' in value or value.endswith('.py')):
                return value
        
        return f"{func.__module__}.{func.__name__}" if hasattr(func, '__module__') else func.__name__

class VerificationRequiredException(Exception):
    """Exception raised when verification is required but not completed"""
    pass

# Global enforcer instance
_enforcer = None

def get_enforcer() -> VerificationEnforcer:
    """Get global verification enforcer"""
    global _enforcer
    if _enforcer is None:
        _enforcer = VerificationEnforcer()
    return _enforcer

# Common decorators for high-risk operations
def verify_api_call(func: Callable) -> Callable:
    """Decorator for API calls that need verification"""
    return get_enforcer().require_verification("api_call", "HIGH")(func)

def verify_file_operation(func: Callable) -> Callable:
    """Decorator for file operations that need verification"""
    return get_enforcer().require_verification("file_operation", "MEDIUM")(func)

def verify_bash_execution(func: Callable) -> Callable:
    """Decorator for bash commands that need verification"""  
    return get_enforcer().require_verification("bash_command", "HIGH")(func)

# Monkey-patching for existing problematic patterns
class VerificationInterceptor:
    """Intercepts and validates common failure patterns"""
    
    def __init__(self):
        self.hook = get_verification_hook()
        self.original_functions = {}
        
    def patch_requests_calls(self):
        """Patch requests library calls to require verification"""
        try:
            import requests
            
            # Store original functions
            self.original_functions['requests.get'] = requests.get
            self.original_functions['requests.post'] = requests.post
            
            # Create verified versions
            @verify_api_call
            def verified_get(*args, **kwargs):
                return self.original_functions['requests.get'](*args, **kwargs)
                
            @verify_api_call  
            def verified_post(*args, **kwargs):
                return self.original_functions['requests.post'](*args, **kwargs)
            
            # Monkey patch
            requests.get = verified_get
            requests.post = verified_post
            
            return True
        except ImportError:
            return False
    
    def patch_file_operations(self):
        """Patch built-in file operations"""
        import builtins
        
        # Store original
        self.original_functions['open'] = builtins.open
        
        @verify_file_operation
        def verified_open(*args, **kwargs):
            return self.original_functions['open'](*args, **kwargs)
        
        # Monkey patch
        builtins.open = verified_open
        
        return True
    
    def restore_original_functions(self):
        """Restore original functions (for testing/emergency)"""
        try:
            import requests
            import builtins
            
            if 'requests.get' in self.original_functions:
                requests.get = self.original_functions['requests.get']
                requests.post = self.original_functions['requests.post']
                
            if 'open' in self.original_functions:
                builtins.open = self.original_functions['open']
                
            return True
        except Exception:
            return False

# Global interceptor
_interceptor = None

def get_interceptor() -> VerificationInterceptor:
    """Get global verification interceptor"""
    global _interceptor
    if _interceptor is None:
        _interceptor = VerificationInterceptor()
    return _interceptor

def enable_global_verification():
    """Enable global verification for common operations"""
    interceptor = get_interceptor()
    results = {
        'requests_patched': interceptor.patch_requests_calls(),
        'file_ops_patched': interceptor.patch_file_operations()
    }
    return results

def disable_global_verification():
    """Disable global verification (emergency use only)"""
    interceptor = get_interceptor()
    return interceptor.restore_original_functions()

if __name__ == "__main__":
    # Test the enforcement system
    
    @verify_api_call
    def test_api_call(url: str, method: str = "GET"):
        """Test function that should require verification"""
        return f"Making {method} request to {url}"
    
    # This should raise VerificationRequiredException
    try:
        result = test_api_call("https://api.example.com/data")
        print(f"SUCCESS: {result}")
    except VerificationRequiredException as e:
        print(f"VERIFICATION REQUIRED:\n{e}")
    
    # Test global patching
    print("\nTesting global verification patching...")
    patch_results = enable_global_verification()
    print(f"Patch results: {patch_results}")
    
    # Test that requests would now require verification
    try:
        import requests
        # This should now require verification
        # requests.get("https://httpbin.org/json")
        print("Requests patching successful (test skipped to avoid actual HTTP call)")
    except Exception as e:
        print(f"Expected verification requirement: {e}")