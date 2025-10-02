#!/usr/bin/env python3
"""
TodoWrite to Backlog Bridge
Automatically captures TodoWrite items and saves them to persistent backlog
"""

import sys
import os
import json
from pathlib import Path

# Add Maia to path
sys.path.append(str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()))

try:
    from claude.tools.backlog_manager import get_backlog_manager
    
    def capture_todos_to_backlog(todos_json: str, context: str = ""):
        """Capture TodoWrite items to persistent backlog"""
        try:
            if isinstance(todos_json, str):
                todos = json.loads(todos_json) if todos_json.strip() else []
            else:
                todos = todos_json
            
            if not todos:
                return
            
            manager = get_backlog_manager()
            captured_count = 0
            
            for todo in todos:
                if todo.get("status") == "pending":  # Only capture pending items
                    # Determine priority from content
                    content = todo["content"].lower()
                    priority = "medium"
                    if any(word in content for word in ['urgent', 'critical', 'asap', 'immediately']):
                        priority = "high"
                    elif any(word in content for word in ['future', 'later', 'eventually', 'consider']):
                        priority = "low"
                    
                    # Determine category from content
                    category = "general"
                    if any(word in content for word in ['security', 'vulnerability', 'audit']):
                        category = "security"
                    elif any(word in content for word in ['mcp', 'server', 'integration']):
                        category = "mcp"
                    elif any(word in content for word in ['agent', 'orchestration']):
                        category = "agents"
                    elif any(word in content for word in ['system', 'macos', 'environment']):
                        category = "system"
                    elif any(word in content for word in ['documentation', 'readme', 'docs']):
                        category = "documentation"
                    
                    # Add to backlog
                    manager.add_recommendation(
                        title=todo["content"],
                        description=todo.get("activeForm", todo["content"]),
                        category=category,
                        priority=priority,
                        context=f"Auto-captured from TodoWrite session: {context}",
                        estimated_effort="unknown"
                    )
                    captured_count += 1
            
            if captured_count > 0:
                print(f"📋 Captured {captured_count} todos to persistent backlog")
            
        except Exception as e:
            # Don't interrupt normal operation
            print(f"⚠️ Backlog capture failed: {e}")
    
    # Function available for external use
    __all__ = ['capture_todos_to_backlog']

except ImportError:
    # If backlog manager not available, create stub
    def capture_todos_to_backlog(todos_json, context=""):
        print("⚠️ Backlog manager not available - todos not persisted")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        todos_data = sys.argv[1]
        context = sys.argv[2] if len(sys.argv) > 2 else ""
        capture_todos_to_backlog(todos_data, context)
