#!/usr/bin/env python3
"""
KAI Integration Checkpoint System
Prevents context loss during implementation by maintaining state
"""

import json
import os
from datetime import datetime
from pathlib import Path
from claude.tools.core.path_manager import get_maia_root

class KAIIntegrationCheckpoint:
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.checkpoint_file = self.maia_root / "claude/data/kai_integration_checkpoint.json"
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
    def save_checkpoint(self, phase, step, status, notes=""):
        """Save current implementation progress"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "step": step,
            "status": status,
            "notes": notes,
            "research_file": "claude/context/core/kai_integration_research.md",
            "implementation_file": "claude/context/core/kai_integration_implementation.md",
            "next_actions": self._get_next_actions(phase, step, status)
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
        print(f"✅ Checkpoint saved: {phase}.{step} - {status}")
        
    def load_checkpoint(self):
        """Load last checkpoint for context recovery"""
        if not self.checkpoint_file.exists():
            return None
            
        with open(self.checkpoint_file, 'r') as f:
            return json.load(f)
            
    def _get_next_actions(self, phase, step, status):
        """Define next actions based on current state"""
        actions = {
            ("phase1", "minimal_claude_md", "not_started"): [
                "Backup current CLAUDE.md",
                "Analyze current structure", 
                "Design reference-based structure"
            ],
            ("phase1", "minimal_claude_md", "in_progress"): [
                "Continue refactoring CLAUDE.md",
                "Test context loading",
                "Measure token reduction"
            ],
            ("phase1", "enhanced_hooks", "not_started"): [
                "Study PAI hook system",
                "Design Python equivalent",
                "Implement dynamic requirements loading"
            ]
        }
        return actions.get((phase, step, status), ["Review implementation tracker"])
        
    def recovery_instructions(self):
        """Provide recovery instructions for context loss"""
        instructions = """
🔴 CONTEXT LOSS RECOVERY PROTOCOL 🔴

If you lose context during KAI integration implementation:

1. READ RESEARCH FINDINGS:
   cat ${MAIA_ROOT}/claude/context/core/kai_integration_research.md

2. READ IMPLEMENTATION STATUS:
   cat ${MAIA_ROOT}/claude/context/core/kai_integration_implementation.md

3. CHECK LAST CHECKPOINT:
   python3 ${MAIA_ROOT}/claude/hooks/kai_integration_checkpoint.py status

4. RESUME FROM CHECKPOINT:
   Follow next_actions from checkpoint data

5. UPDATE PROGRESS:
   Update implementation tracker after each work session
"""
        return instructions

def main():
    import sys
    checkpoint = KAIIntegrationCheckpoint()
    
    if len(sys.argv) < 2:
        print("Usage: python3 kai_integration_checkpoint.py [save|load|status|recovery]")
        return
        
    command = sys.argv[1]
    
    if command == "save":
        if len(sys.argv) != 5:
            print("Usage: save <phase> <step> <status> [notes]")
            return
        phase, step, status = sys.argv[2:5]
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        checkpoint.save_checkpoint(phase, step, status, notes)
        
    elif command == "load" or command == "status":
        data = checkpoint.load_checkpoint()
        if data:
            print(f"📍 Last Checkpoint:")
            print(f"   Phase: {data['phase']}")
            print(f"   Step: {data['step']}")
            print(f"   Status: {data['status']}")
            print(f"   Time: {data['timestamp']}")
            print(f"   Notes: {data.get('notes', 'None')}")
            print(f"📝 Next Actions:")
            for action in data.get('next_actions', []):
                print(f"   - {action}")
        else:
            print("❌ No checkpoint found")
            
    elif command == "recovery":
        print(checkpoint.recovery_instructions())
        
if __name__ == "__main__":
    main()