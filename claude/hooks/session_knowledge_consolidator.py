#!/usr/bin/env python3
"""
Session Knowledge Consolidator
Automatically captures TodoWrite items and consolidates them into master backlog
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add tools path for knowledge management system
maia_root = os.getenv("MAIA_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
tools_path = os.path.join(maia_root, "claude", "tools")
sys.path.append(tools_path)

try:
    from knowledge_management_system import KnowledgeManagementSystem
    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False

class SessionKnowledgeConsolidator:
    """Consolidates session knowledge into persistent storage"""
    
    def __init__(self):
        self.kms = KnowledgeManagementSystem() if KMS_AVAILABLE else None
        # Use Maia data directory for session files instead of /tmp
        maia_root = os.getenv("MAIA_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        session_dir = Path(maia_root) / "claude" / "data" / "knowledge_management"
        session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = session_dir / "current_session_todos.json"
    
    def capture_session_todos(self, todos: list):
        """Capture session todos to temporary storage"""
        session_data = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "todos": todos,
            "consolidated": False
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def consolidate_session(self) -> dict:
        """Consolidate session todos into master backlog"""
        if not self.kms:
            return {"error": "Knowledge management system not available"}
        
        if not self.session_file.exists():
            return {"message": "No session todos to consolidate"}
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            if session_data.get("consolidated"):
                return {"message": "Session already consolidated"}
            
            # Consolidate todos
            todos = session_data.get("todos", [])
            consolidated_count = self.kms.consolidate_session_todos(todos)
            
            # Mark as consolidated
            session_data["consolidated"] = True
            session_data["consolidation_timestamp"] = datetime.now().isoformat()
            session_data["consolidated_count"] = consolidated_count
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return {
                "message": f"Consolidated {consolidated_count} items from session",
                "session_id": session_data["session_id"],
                "consolidated_count": consolidated_count
            }
            
        except Exception as e:
            return {"error": f"Consolidation failed: {str(e)}"}
    
    def get_session_summary(self) -> dict:
        """Get summary of current session todos"""
        if not self.session_file.exists():
            return {"message": "No active session"}
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            todos = session_data.get("todos", [])
            
            status_counts = {}
            for todo in todos:
                status = todo.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "session_id": session_data["session_id"],
                "total_todos": len(todos),
                "by_status": status_counts,
                "consolidated": session_data.get("consolidated", False),
                "consolidation_ready": len([t for t in todos if t.get("status") == "completed"]) > 0
            }
            
        except Exception as e:
            return {"error": f"Failed to get session summary: {str(e)}"}
    
    def auto_consolidate_on_completion(self, todos: list):
        """Automatically consolidate when todos are marked complete"""
        # Only consolidate if we have significant completed items
        completed_items = [t for t in todos if t.get("status") == "completed"]
        
        if len(completed_items) >= 3:  # Threshold for auto-consolidation
            self.capture_session_todos(todos)
            return self.consolidate_session()
        
        return {"message": "Not enough completed items for auto-consolidation"}

def consolidate_current_session():
    """CLI function to consolidate current session"""
    consolidator = SessionKnowledgeConsolidator()
    result = consolidator.consolidate_session()
    print(json.dumps(result, indent=2))

def session_summary():
    """CLI function to show session summary"""
    consolidator = SessionKnowledgeConsolidator()
    result = consolidator.get_session_summary()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "consolidate":
            consolidate_current_session()
        elif sys.argv[1] == "summary":
            session_summary()
        else:
            print("Usage: session_knowledge_consolidator.py [consolidate|summary]")
    else:
        consolidate_current_session()