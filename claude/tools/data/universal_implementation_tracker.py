#!/usr/bin/env python3
"""
Universal Implementation Tracker
System-wide context preservation for all major implementations
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3

class UniversalImplementationTracker:
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.data_dir = self.maia_root / "claude/data/implementations"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite database for persistent tracking
        self.db_path = self.data_dir / "implementations.db"
        self.init_database()
        
        # UFC-compliant directory structure
        self.context_dir = self.maia_root / "claude/context/core"
        self.commands_dir = self.maia_root / "claude/commands"
        
    def init_database(self):
        """Initialize SQLite database for implementation tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS implementations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT UNIQUE NOT NULL,
                    project_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    research_file TEXT,
                    implementation_file TEXT,
                    recovery_command TEXT,
                    description TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    next_actions TEXT,
                    FOREIGN KEY (project_name) REFERENCES implementations(project_name)
                )
            """)
            
    def create_implementation(self, project_name: str, project_type: str, 
                            priority: str, description: str) -> Dict[str, Any]:
        """Create new implementation tracking structure"""
        
        # Sanitize project name for file system
        safe_name = project_name.lower().replace(" ", "_").replace("-", "_")
        
        # UFC-compliant file paths
        research_file = f"claude/context/core/{safe_name}_research.md"
        implementation_file = f"claude/context/core/{safe_name}_implementation.md"
        recovery_command = f"claude/commands/resume_{safe_name}.md"
        
        # Database entry
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO implementations 
                    (project_name, project_type, priority, status, created_date, 
                     last_updated, research_file, implementation_file, recovery_command, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_name, project_type, priority, "not_started",
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    research_file, implementation_file, recovery_command, description
                ))
            except sqlite3.IntegrityError:
                return {"error": f"Implementation '{project_name}' already exists"}
        
        # Create research template
        self._create_research_template(safe_name, project_name, project_type, description)
        
        # Create implementation tracker template
        self._create_implementation_template(safe_name, project_name, project_type)
        
        # Create recovery command template
        self._create_recovery_command(safe_name, project_name)
        
        return {
            "project_name": project_name,
            "safe_name": safe_name,
            "research_file": research_file,
            "implementation_file": implementation_file,
            "recovery_command": recovery_command,
            "status": "created"
        }
        
    def save_checkpoint(self, project_name: str, phase: str, step: str, 
                       status: str, notes: str = "") -> Dict[str, Any]:
        """Save implementation checkpoint"""
        
        next_actions = self._generate_next_actions(project_name, phase, step, status)
        
        with sqlite3.connect(self.db_path) as conn:
            # Save checkpoint
            conn.execute("""
                INSERT INTO checkpoints 
                (project_name, timestamp, phase, step, status, notes, next_actions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project_name, datetime.now().isoformat(), phase, step, 
                status, notes, json.dumps(next_actions)
            ))
            
            # Update implementation status
            conn.execute("""
                UPDATE implementations 
                SET status = ?, last_updated = ?
                WHERE project_name = ?
            """, (status, datetime.now().isoformat(), project_name))
            
        return {
            "project_name": project_name,
            "checkpoint_saved": True,
            "next_actions": next_actions
        }
        
    def get_implementation(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get implementation details and latest checkpoint"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get implementation
            impl = conn.execute("""
                SELECT * FROM implementations WHERE project_name = ?
            """, (project_name,)).fetchone()
            
            if not impl:
                return None
                
            # Get latest checkpoint
            checkpoint = conn.execute("""
                SELECT * FROM checkpoints 
                WHERE project_name = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (project_name,)).fetchone()
            
            result = dict(impl)
            if checkpoint:
                result["latest_checkpoint"] = dict(checkpoint)
                result["latest_checkpoint"]["next_actions"] = json.loads(
                    checkpoint["next_actions"] or "[]"
                )
            
            return result
            
    def list_implementations(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """List all implementations, optionally filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status_filter:
                rows = conn.execute("""
                    SELECT * FROM implementations 
                    WHERE status = ? 
                    ORDER BY priority DESC, last_updated DESC
                """, (status_filter,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM implementations 
                    ORDER BY priority DESC, last_updated DESC
                """).fetchall()
                
            return [dict(row) for row in rows]
            
    def get_recovery_context(self, project_name: str) -> Dict[str, Any]:
        """Get complete recovery context for implementation"""
        impl = self.get_implementation(project_name)
        if not impl:
            return {"error": f"Implementation '{project_name}' not found"}
            
        return {
            "project_name": project_name,
            "status": impl["status"],
            "research_file": impl["research_file"],
            "implementation_file": impl["implementation_file"],
            "recovery_command": impl["recovery_command"],
            "latest_checkpoint": impl.get("latest_checkpoint"),
            "recovery_instructions": self._get_recovery_instructions(project_name)
        }
        
    def _create_research_template(self, safe_name: str, project_name: str, 
                                project_type: str, description: str):
        """Create research findings template"""
        template = f"""# {project_name} Research Findings

## Executive Summary
Date: {datetime.now().strftime('%Y-%m-%d')}
Type: {project_type}
Status: Research Phase
Description: {description}

## Research Sources
- [Add research sources and URLs]

## Key Findings
- [Document key discoveries]
- [List important insights]
- [Note architectural implications]

## Implementation Recommendations

### Priority Recommendations
1. **High Priority**: [Critical items for immediate implementation]
2. **Medium Priority**: [Important but not urgent items]
3. **Low Priority**: [Future consideration items]

### Technical Specifications
- [Document technical requirements]
- [List integration points]
- [Note compatibility considerations]

## Risk Assessment
- **Implementation Risk**: [Low/Medium/High]
- **Complexity**: [Simple/Medium/Complex]
- **Dependencies**: [List external dependencies]

## Success Metrics
- [Define measurable success criteria]
- [List validation approaches]
- [Document expected benefits]

## Context Preservation Notes
This research represents comprehensive analysis for {project_name}.
All findings are ready for implementation with clear technical specifications.
"""
        
        research_path = self.context_dir / f"{safe_name}_research.md"
        with open(research_path, 'w') as f:
            f.write(template)
            
    def _create_implementation_template(self, safe_name: str, project_name: str, 
                                      project_type: str):
        """Create implementation tracker template"""
        template = f"""# {project_name} Implementation Tracker

## Implementation Status Dashboard
Last Updated: {datetime.now().strftime('%Y-%m-%d')}
Overall Progress: 0% (Ready to Start)

## Implementation Phases

### Phase 1: [Phase Name]
- **Status**: 🔴 Not Started
- **Estimated Effort**: [Hours/Days]
- **Expected Benefit**: [Describe benefits]
- **Blockers**: None
- **Next Action**: [Specific next step]

#### Implementation Steps:
- [ ] [Step 1]
- [ ] [Step 2]
- [ ] [Step 3]

#### Technical Specifications:
```
[Add technical details]
```

### Phase 2: [Phase Name]
- **Status**: 🔴 Not Started
- **Estimated Effort**: [Hours/Days]
- **Expected Benefit**: [Describe benefits]
- **Next Action**: [Specific next step]

## Implementation Prevention Protocols

### Automated Progress Tracking
- **File**: This implementation tracker updated after each work session
- **Backup**: Research findings preserved in {safe_name}_research.md
- **Integration**: Universal checkpoint system for persistence

### Context Loss Recovery
If context is lost during implementation:
1. Read research file: claude/context/core/{safe_name}_research.md
2. Read this implementation tracker: claude/context/core/{safe_name}_implementation.md
3. Check latest checkpoint: universal_implementation_tracker.py status {project_name}
4. Resume from last completed checkpoint

## Ready-to-Execute Actions

### Immediate Next Steps:
- [List immediate actions]

### This Week:
- [List weekly goals]

### Success Validation
- [ ] [Validation criteria]
- [ ] [Testing requirements]
- [ ] [Documentation updates]
"""
        
        impl_path = self.context_dir / f"{safe_name}_implementation.md"
        with open(impl_path, 'w') as f:
            f.write(template)
            
    def _create_recovery_command(self, safe_name: str, project_name: str):
        """Create recovery command template"""
        template = f"""# Resume {project_name} Implementation

## Context Recovery Protocol

This command provides complete recovery from context loss during {project_name} implementation.

## Usage
```bash
# Get current status
python3 claude/tools/📊_data/universal_implementation_tracker.py status {project_name}

# Get recovery context
python3 claude/tools/📊_data/universal_implementation_tracker.py recovery {project_name}

# Read research findings
cat claude/context/core/{safe_name}_research.md

# Read implementation status
cat claude/context/core/{safe_name}_implementation.md
```

## Quick Recovery Steps

1. **Load Research Context**: Research findings in implementation files
2. **Check Implementation Status**: Use universal tracker for current state
3. **Resume From Checkpoint**: Follow next_actions from latest checkpoint

## Implementation Files
- Research: `claude/context/core/{safe_name}_research.md`
- Tracker: `claude/context/core/{safe_name}_implementation.md`
- Recovery: This command file

## Next Session Protocol
1. Run recovery command
2. Check status and read context files
3. Begin/continue implementation
4. Update tracker and save checkpoint
5. Commit progress to git

This ensures continuity across context resets and prevents implementation loss.
"""
        
        recovery_path = self.commands_dir / f"resume_{safe_name}.md"
        with open(recovery_path, 'w') as f:
            f.write(template)
            
    def _generate_next_actions(self, project_name: str, phase: str, 
                              step: str, status: str) -> List[str]:
        """Generate next actions based on current state"""
        # Default next actions - can be enhanced with project-specific logic
        if status == "not_started":
            return [
                f"Review {project_name} research findings",
                f"Begin {phase} implementation",
                "Set up development environment if needed"
            ]
        elif status == "in_progress":
            return [
                f"Continue {step} in {phase}",
                "Update implementation tracker",
                "Test current implementation"
            ]
        elif status == "completed":
            return [
                "Move to next phase",
                "Update documentation",
                "Commit progress to git"
            ]
        else:
            return ["Review implementation status and plan next steps"]
            
    def _get_recovery_instructions(self, project_name: str) -> str:
        """Get recovery instructions for specific implementation"""
        return f"""
🔴 CONTEXT LOSS RECOVERY PROTOCOL 🔴

For {project_name} implementation:

1. GET STATUS:
   python3 claude/tools/📊_data/universal_implementation_tracker.py status {project_name}

2. READ CONTEXT:
   - Research findings and implementation tracker files
   - Latest checkpoint information

3. RESUME IMPLEMENTATION:
   - Follow next_actions from checkpoint
   - Update progress after each session
   - Save new checkpoints regularly

4. MAINTAIN CONTINUITY:
   - Update implementation tracker
   - Commit progress to git
   - Use recovery command for future context restoration
"""

def main():
    import sys
    tracker = UniversalImplementationTracker()
    
    if len(sys.argv) < 2:
        print("Usage: universal_implementation_tracker.py [create|status|checkpoint|list|recovery]")
        return
        
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) != 6:
            print("Usage: create <project_name> <project_type> <priority> <description>")
            return
        project_name, project_type, priority, description = sys.argv[2:6]
        result = tracker.create_implementation(project_name, project_type, priority, description)
        print(f"✅ Created implementation tracking for: {project_name}")
        print(f"📄 Research file: {result['research_file']}")
        print(f"📊 Implementation file: {result['implementation_file']}")
        print(f"🔄 Recovery command: {result['recovery_command']}")
        
    elif command == "checkpoint":
        if len(sys.argv) < 6:
            print("Usage: checkpoint <project_name> <phase> <step> <status> [notes]")
            return
        project_name, phase, step, status = sys.argv[2:6]
        notes = sys.argv[6] if len(sys.argv) > 6 else ""
        result = tracker.save_checkpoint(project_name, phase, step, status, notes)
        print(f"✅ Checkpoint saved for: {project_name}")
        
    elif command == "status":
        if len(sys.argv) != 3:
            print("Usage: status <project_name>")
            return
        project_name = sys.argv[2]
        impl = tracker.get_implementation(project_name)
        if impl:
            print(f"📍 {project_name} Status:")
            print(f"   Type: {impl['project_type']}")
            print(f"   Priority: {impl['priority']}")
            print(f"   Status: {impl['status']}")
            print(f"   Last Updated: {impl['last_updated']}")
            if impl.get('latest_checkpoint'):
                cp = impl['latest_checkpoint']
                print(f"📝 Latest Checkpoint:")
                print(f"   Phase: {cp['phase']}")
                print(f"   Step: {cp['step']}")
                print(f"   Status: {cp['status']}")
                print(f"📋 Next Actions:")
                for action in cp.get('next_actions', []):
                    print(f"   - {action}")
        else:
            print(f"❌ Implementation '{project_name}' not found")
            
    elif command == "list":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        implementations = tracker.list_implementations(status_filter)
        print(f"📋 Active Implementations:")
        for impl in implementations:
            print(f"   • {impl['project_name']} ({impl['status']}) - {impl['priority']} priority")
            
    elif command == "recovery":
        if len(sys.argv) != 3:
            print("Usage: recovery <project_name>")
            return
        project_name = sys.argv[2]
        context = tracker.get_recovery_context(project_name)
        if 'error' not in context:
            print(context['recovery_instructions'])
        else:
            print(context['error'])

if __name__ == "__main__":
    main()