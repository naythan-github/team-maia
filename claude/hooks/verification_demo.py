#!/usr/bin/env python3
"""
Verification System Demonstration
Shows how the verification hook prevents assumption-driven failures
"""

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

from claude.hooks.auto_verification_enforcer import VerificationRequiredException, verify_api_call, get_enforcer
from claude.hooks.pre_execution_verification_hook import log_assumption_failure

def demonstrate_confluence_failure_prevention():
    """Demonstrate how verification prevents the original Confluence API failures"""
    
    print("=== VERIFICATION SYSTEM DEMONSTRATION ===\n")
    print("Recreating the original Confluence API assumption failures...\n")
    
    # Simulate the original failing approaches with verification
    
    print("1. ORIGINAL FAILURE: search_confluence_content('', space_key='Maia')")
    print("   ERROR: TypeError: unexpected keyword argument 'space_key'")
    print("   CAUSE: Assumed API signature without reading implementation\n")
    
    @verify_api_call
    def attempt_confluence_search_with_space_key(query: str, space_key: str):
        """Simulate the original failing API call"""
        # This would have been the actual failing call
        return f"search_confluence_content('{query}', space_key='{space_key}')"
    
    try:
        result = attempt_confluence_search_with_space_key('', 'Maia')
        print(f"   RESULT: {result}")
    except VerificationRequiredException as e:
        print("   🚨 VERIFICATION SYSTEM BLOCKED THIS:")
        print(f"   {str(e)[:200]}...\n")
    
    print("2. ORIGINAL FAILURE: client.search_pages('space=Maia')")  
    print("   ERROR: AttributeError: object has no attribute 'search_pages'")
    print("   CAUSE: Assumed method exists without checking class implementation\n")
    
    @verify_api_call
    def attempt_nonexistent_method(space_query: str):
        """Simulate the original failing method call"""
        return f"client.search_pages('{space_query}')"
    
    try:
        result = attempt_nonexistent_method('space=Maia')
        print(f"   RESULT: {result}")
    except VerificationRequiredException as e:
        print("   🚨 VERIFICATION SYSTEM BLOCKED THIS:")
        print(f"   {str(e)[:200]}...\n")
    
    print("3. WHAT THE VERIFICATION SYSTEM ENFORCES:")
    print("   - READ claude/tools/direct_confluence_access.py FIRST")
    print("   - VERIFY method signatures and available functions")
    print("   - CHECK parameter names and types")
    print("   - THEN execute with confidence\n")
    
    # Show the correct working approach
    print("4. CORRECT APPROACH (after verification):")
    print("   - Read implementation file ✅")
    print("   - Found: DirectConfluenceClient class")
    print("   - Found: No search_pages method exists")  
    print("   - Found: Must use direct requests.get with proper parameters")
    print("   - Result: Working API call to /wiki/rest/api/content\n")

def demonstrate_statistics():
    """Show verification system statistics"""
    
    # Log some example assumption failures
    log_assumption_failure(
        assumed_interface="search_confluence_content(query, space_key='Maia')",
        actual_interface="search_confluence_content(query) - no space_key parameter",
        error_message="TypeError: unexpected keyword argument 'space_key'",
        recovery_action="Read implementation file and use direct API"
    )
    
    log_assumption_failure(
        assumed_interface="client.search_pages('space=Maia')",
        actual_interface="DirectConfluenceClient - no search_pages method",  
        error_message="AttributeError: object has no attribute 'search_pages'",
        recovery_action="Use requests.get with proper URL and parameters"
    )
    
    # Get and display statistics
    from claude.hooks.pre_execution_verification_hook import get_verification_hook
    hook = get_verification_hook()
    stats = hook.get_verification_stats()
    
    print("=== VERIFICATION SYSTEM STATISTICS ===")
    print(f"Recent assumption failures: {stats['recent_assumption_failures']}")
    print(f"Verification compliance rate: {stats['verification_compliance_rate']}%")
    print(f"Common failure patterns: {stats['common_failure_patterns']}")
    print(f"Verification events: {stats['verification_events']}")

def demonstrate_bypass_for_verified_operations():
    """Show how to bypass verification after proper verification is completed"""
    
    print("\n=== BYPASS AFTER VERIFICATION ===")
    print("Once you've properly verified the implementation, you can:")
    print("1. Use the verified approach directly")
    print("2. Or temporarily bypass verification for known-good operations\n")
    
    # Show bypass mechanism
    enforcer = get_enforcer()
    original_bypass = enforcer.bypass_verification
    
    try:
        # Enable bypass temporarily
        enforcer.bypass_verification = True
        
        @verify_api_call
        def verified_confluence_call():
            """This would now work because we've verified it's correct"""
            return "requests.get(url, headers=headers, params={'spaceKey': 'Maia'})"
        
        result = verified_confluence_call()
        print(f"✅ BYPASSED (after verification): {result}")
        
    finally:
        # Always restore verification
        enforcer.bypass_verification = original_bypass

if __name__ == "__main__":
    # Run the demonstration
    demonstrate_confluence_failure_prevention()
    demonstrate_statistics() 
    demonstrate_bypass_for_verified_operations()
    
    print("\n=== SUMMARY ===")
    print("🚨 The verification system would have PREVENTED both original failures")
    print("⚡ By enforcing READ-BEFORE-EXECUTE pattern")
    print("📊 And tracking assumption failure patterns for learning")
    print("🔧 While providing clear guidance for proper verification steps")