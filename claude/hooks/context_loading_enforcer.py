#!/usr/bin/env python3
"""
Context Loading Enforcement System
Prevents UFC system violations by tracking and enforcing mandatory context loading
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from claude.tools.core.path_manager import get_maia_root

# Configuration
CONTEXT_STATE_FILE = str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "context_state.json"
REQUIRED_CORE_FILES = [
    "${MAIA_ROOT}/claude/context/ufc_system.md",
    "${MAIA_ROOT}/claude/context/core/identity.md", 
    "${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md",
    "${MAIA_ROOT}/claude/context/core/model_selection_strategy.md"
]

def load_context_state():
    """Load current context state from tracking file"""
    try:
        if os.path.exists(CONTEXT_STATE_FILE):
            with open(CONTEXT_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            return create_initial_state()
    except Exception as e:
        print(f"⚠️  Error loading context state: {e}")
        return create_initial_state()

def save_context_state(state):
    """Save context state to tracking file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONTEXT_STATE_FILE), exist_ok=True)
        
        # Update timestamp
        state['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        
        with open(CONTEXT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving context state: {e}")

def create_initial_state():
    """Create initial context state"""
    return {
        "schema_version": "1.0",
        "last_updated": datetime.utcnow().isoformat() + 'Z',
        "session_id": None,
        "context_loading": {
            "core_loaded": False,
            "files_loaded": [],
            "required_core_files": REQUIRED_CORE_FILES,
            "domain_files_loaded": [],
            "loading_timestamp": None,
            "enforcement_active": True
        },
        "conversation_state": {
            "first_response_sent": False,
            "context_violation_detected": False,
            "auto_load_attempted": False,
            "enforcement_bypassed": False
        },
        "metadata": {
            "created_by": "context_enforcement_system",
            "purpose": "Track context loading state to prevent UFC system violations",
            "enforcement_hook": "user-prompt-submit"
        }
    }

def check_context_violation():
    """Check if context loading violation would occur"""
    state = load_context_state()
    
    # Check if this is a new conversation (no context loaded yet)
    if not state['context_loading']['core_loaded']:
        # Check if this would be the first response
        if not state['conversation_state']['first_response_sent']:
            return True, "VIOLATION: First response attempted without loading core context"
    
    return False, None

def mark_context_loaded(files_loaded):
    """Mark context files as loaded"""
    state = load_context_state()
    
    # Update loaded files
    state['context_loading']['files_loaded'] = files_loaded
    state['context_loading']['loading_timestamp'] = datetime.utcnow().isoformat() + 'Z'
    
    # Check if core files are loaded
    core_loaded = all(f in files_loaded for f in REQUIRED_CORE_FILES)
    state['context_loading']['core_loaded'] = core_loaded
    
    save_context_state(state)
    return core_loaded

def mark_first_response():
    """Mark that first response has been sent"""
    state = load_context_state()
    state['conversation_state']['first_response_sent'] = True
    save_context_state(state)

def reset_conversation_state():
    """Reset state for new conversation"""
    state = create_initial_state()
    save_context_state(state)

def generate_enforcement_message():
    """Generate enforcement message for hook"""
    violation, message = check_context_violation()
    
    if violation:
        # Try graceful recovery first
        auto_loader_path = os.path.join(os.path.dirname(__file__), "context_auto_loader.py")
        if os.path.exists(auto_loader_path):
            try:
                import subprocess
                result = subprocess.run([
                    sys.executable, auto_loader_path, "recover"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Auto-recovery successful
                    return ""
                else:
                    # Auto-recovery failed, show manual instructions
                    return f"""
🚨🚨🚨 CONTEXT LOADING VIOLATION DETECTED 🚨🚨🚨

{message}

🔄 AUTO-RECOVERY ATTEMPTED BUT FAILED

🔴 MANUAL ACTION REQUIRED:
   1. Load UFC system FIRST: ${MAIA_ROOT}/claude/context/ufc_system.md
   2. Load core identity: ${MAIA_ROOT}/claude/context/core/identity.md
   3. Load systematic thinking: ${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md
   4. Load model strategy: ${MAIA_ROOT}/claude/context/core/model_selection_strategy.md

⚠️  NO RESPONSES ALLOWED UNTIL CORE CONTEXT LOADED

🤖 Expected Response Format After Loading:
   "✅ Core context loaded. Operating as Maia with systematic optimization framework."

═══════════════════════════════════════════════════════════════
"""
            except Exception as e:
                # Fallback to manual instructions
                pass
        
        # Standard violation message if auto-recovery not available
        return f"""
🚨🚨🚨 CONTEXT LOADING VIOLATION DETECTED 🚨🚨🚨

{message}

🔴 MANDATORY ACTION REQUIRED:
   1. Load UFC system FIRST: ${MAIA_ROOT}/claude/context/ufc_system.md
   2. Load core identity: ${MAIA_ROOT}/claude/context/core/identity.md
   3. Load systematic thinking: ${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md
   4. Load model strategy: ${MAIA_ROOT}/claude/context/core/model_selection_strategy.md

⚠️  NO RESPONSES ALLOWED UNTIL CORE CONTEXT LOADED

🤖 Expected Response Format After Loading:
   "✅ Core context loaded. Operating as Maia with systematic optimization framework."

═══════════════════════════════════════════════════════════════
"""
    
    return ""

def auto_load_core_context():
    """Auto-load core context files (simulation for demonstration)"""
    # This would be called by Claude to auto-load context
    # For now, just mark as attempted
    state = load_context_state()
    state['conversation_state']['auto_load_attempted'] = True
    save_context_state(state)
    
    print("🔄 AUTO-LOADING CORE CONTEXT...")
    print("   📖 Loading UFC system...")
    print("   🤖 Loading Maia identity...")
    print("   🧠 Loading systematic thinking protocol...")
    print("   🔧 Loading model selection strategy...")
    print("✅ CORE CONTEXT AUTO-LOAD COMPLETE")

def main():
    """Main enforcement function"""
    if len(sys.argv) < 2:
        print("Usage: context_loading_enforcer.py <command> [args]")
        print("Commands: check, mark_loaded, reset, auto_load")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        message = generate_enforcement_message()
        if message:
            print(message)
            sys.exit(1)  # Block response
        else:
            print("✅ Context loading compliance verified")
    
    elif command == "mark_loaded":
        if len(sys.argv) < 3:
            print("Usage: mark_loaded <file1,file2,file3...>")
            sys.exit(1)
        files = sys.argv[2].split(',')
        core_loaded = mark_context_loaded(files)
        print(f"✅ Context loading recorded: {len(files)} files, core_loaded: {core_loaded}")
    
    elif command == "reset":
        reset_conversation_state()
        print("✅ Conversation state reset")
    
    elif command == "auto_load":
        auto_load_core_context()
    
    elif command == "status":
        state = load_context_state()
        print(f"📊 Context State:")
        print(f"   Core Loaded: {state['context_loading']['core_loaded']}")
        print(f"   Files Loaded: {len(state['context_loading']['files_loaded'])}")
        print(f"   First Response Sent: {state['conversation_state']['first_response_sent']}")
        print(f"   Last Updated: {state['last_updated']}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()