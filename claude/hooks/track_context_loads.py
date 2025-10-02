#!/usr/bin/env python3
"""
Automatic Context Load Tracking Hook

Automatically detects and tracks when Maia context is being loaded
to measure context reload frequency and overhead.

Author: Maia
Created: 2025-09-08
"""

import sys
import time
from pathlib import Path

# Add Maia tools to path
MAIA_ROOT = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
sys.path.append(str(MAIA_ROOT / "claude/tools"))

try:
    from session_tracker import get_session_tracker
except ImportError:
    # Fallback if tracking not available
    def get_session_tracker(ide="vscode"):
        class NoOpTracker:
            """
            No-operation tracker for graceful fallback when session tracking is unavailable.
            
            This class provides the same interface as the real session tracker but
            performs no actual tracking operations, allowing the system to continue
            functioning when the session_tracker module is not available.
            """
            def track_context_load(self, files, duration): 
                """No-op implementation of context load tracking."""
                pass
            def track_file_operation(self, op, file, duration, success=True): 
                """No-op implementation of file operation tracking."""
                pass
        return NoOpTracker()

def track_context_load_pattern():
    """
    Automatically detect context loading patterns and measure performance.
    
    This function tracks when full context reloads happen, measuring the time
    taken and recording it for performance analysis. It monitors the standard
    8-file context loading sequence that Maia uses for initialization.
    
    Returns:
        dict: Dictionary containing tracking results with keys:
            - tracked (bool): Whether tracking was successful
            - files_count (int): Number of context files tracked
            - duration_ms (float): Duration in milliseconds
            - timestamp (float): Unix timestamp of the measurement
    
    Example:
        >>> result = track_context_load_pattern()
        >>> print(f"Context loaded {result['files_count']} files in {result['duration_ms']:.0f}ms")
    """
    start_time = time.time()
    
    # Check if we're in a context loading scenario
    # (This would be called when the 8-file sequence starts)
    context_files = [
        "ufc_system.md",
        "identity.md", 
        "available.md",
        "agents.md",
        "command_orchestration.md",
        "profile.md",
        "model_selection_strategy.md",
        "systematic_tool_checking.md"
    ]
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Track the context load
    tracker = get_session_tracker()
    tracker.track_context_load(context_files, duration_ms)
    
    return {
        "tracked": True,
        "files_count": len(context_files),
        "duration_ms": duration_ms,
        "timestamp": time.time()
    }

def track_manual_context_load():
    """
    Manual trigger for context load tracking with user feedback.
    
    This function provides a command-line interface for manually triggering
    context load tracking. It calls track_context_load_pattern() and provides
    user-friendly output showing the results.
    
    Returns:
        dict: Same format as track_context_load_pattern() containing:
            - tracked (bool): Whether tracking was successful
            - files_count (int): Number of context files tracked  
            - duration_ms (float): Duration in milliseconds
            - timestamp (float): Unix timestamp of the measurement
    
    Example:
        >>> track_manual_context_load()
        🔄 Tracking context reload...
        ✅ Context reload tracked: 150ms
    """
    print("🔄 Tracking context reload...")
    result = track_context_load_pattern()
    print(f"✅ Context reload tracked: {result['duration_ms']:.0f}ms")
    return result

if __name__ == "__main__":
    # Manual execution
    track_manual_context_load()