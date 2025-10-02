#!/usr/bin/env python3
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class AntiSprawlProgressTracker:
    def __init__(self):
        self.db_path = "claude/data/anti_sprawl_progress.db"
        self.checkpoint_dir = Path("claude/data/implementation_checkpoints")
        self.initialize_database()
        self.ensure_checkpoint_directory()
    
    def initialize_database(self):
        """Initialize progress tracking database"""
        # Ensure data directory exists
        Path("claude/data").mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase_number INTEGER NOT NULL,
                phase_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_date TEXT,
                completion_date TEXT,
                estimated_duration_hours INTEGER,
                actual_duration_hours INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase_id INTEGER NOT NULL,
                task_number TEXT NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_date TEXT,
                completion_date TEXT,
                estimated_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                notes TEXT,
                deliverables TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (phase_id) REFERENCES phases (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_type TEXT NOT NULL,
                checkpoint_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS implementation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize phases if not exist
        cursor.execute('SELECT COUNT(*) FROM phases')
        if cursor.fetchone()[0] == 0:
            self.initialize_default_phases(cursor)
        
        conn.commit()
        conn.close()
    
    def initialize_default_phases(self, cursor):
        """Initialize default phase structure"""
        phases = [
            (1, "Stabilize Current Structure", 40),  # 5-7 hours
            (2, "Automated Organization", 80),       # 10-12 hours  
            (3, "Proactive Management", 20)          # 2-3 hours
        ]
        
        for phase_num, phase_name, duration in phases:
            cursor.execute('''
                INSERT INTO phases (phase_number, phase_name, estimated_duration_hours)
                VALUES (?, ?, ?)
            ''', (phase_num, phase_name, duration))
        
        # Initialize tasks for each phase
        tasks = {
            1: [  # Phase 1
                ("1.1", "Current File Structure Audit", 120),
                ("1.2", "Define Immutable Core Structure", 60),
                ("1.3", "Identify Naming Convention Violations", 60),
                ("1.4", "Create File Lifecycle Manager", 120),
                ("1.5", "Phase 1 Validation and Documentation", 60)
            ],
            2: [  # Phase 2  
                ("2.1", "Enhanced File Lifecycle Manager", 120),
                ("2.2", "Semantic Naming Enforcement", 120),
                ("2.3", "Automated File Organization System", 180),
                ("2.4", "Phase 2 Validation and Integration", 60)
            ],
            3: [  # Phase 3
                ("3.1", "Automated Quarterly Audit System", 60),
                ("3.2", "Growth Pattern Detection and Capacity Planning", 60),
                ("3.3", "Documentation Maintenance Automation", 30),
                ("3.4", "Phase 3 Validation and Final System Integration", 30)
            ]
        }
        
        for phase_num, task_list in tasks.items():
            for task_number, task_name, duration in task_list:
                cursor.execute('''
                    INSERT INTO tasks (phase_id, task_number, task_name, estimated_duration_minutes)
                    VALUES (?, ?, ?, ?)
                ''', (phase_num, task_number, task_name, duration))
    
    def ensure_checkpoint_directory(self):
        """Ensure checkpoint directory exists"""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_status(self) -> Dict:
        """Get current implementation status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get phase status
        cursor.execute('''
            SELECT phase_number, phase_name, status, 
                   estimated_duration_hours, actual_duration_hours
            FROM phases 
            ORDER BY phase_number
        ''')
        phases = cursor.fetchall()
        
        # Get current task
        cursor.execute('''
            SELECT t.phase_id, t.task_number, t.task_name, t.status
            FROM tasks t
            JOIN phases p ON t.phase_id = p.id
            WHERE t.status IN ('pending', 'in_progress')
            ORDER BY p.phase_number, t.task_number
            LIMIT 1
        ''')
        current_task = cursor.fetchone()
        
        # Get overall progress
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "completed"')
        completed_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tasks')
        total_tasks = cursor.fetchone()[0]
        
        conn.close()
        
        status = {
            'phases': [
                {
                    'number': p[0],
                    'name': p[1], 
                    'status': p[2],
                    'estimated_hours': p[3],
                    'actual_hours': p[4]
                } for p in phases
            ],
            'current_task': {
                'phase_id': current_task[0] if current_task else None,
                'task_number': current_task[1] if current_task else None,
                'task_name': current_task[2] if current_task else None,
                'status': current_task[3] if current_task else None
            } if current_task else None,
            'progress': {
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks,
                'percentage': round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
            }
        }
        
        return status
    
    def get_next_task(self, phase: Optional[int] = None) -> Optional[Dict]:
        """Get next task to work on"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if phase:
            cursor.execute('''
                SELECT t.id, t.task_number, t.task_name, t.status, 
                       t.estimated_duration_minutes, p.phase_name
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE p.phase_number = ? AND t.status IN ('pending', 'in_progress')
                ORDER BY t.task_number
                LIMIT 1
            ''', (phase,))
        else:
            cursor.execute('''
                SELECT t.id, t.task_number, t.task_name, t.status,
                       t.estimated_duration_minutes, p.phase_name
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE t.status IN ('pending', 'in_progress')
                ORDER BY p.phase_number, t.task_number
                LIMIT 1
            ''')
        
        task = cursor.fetchone()
        conn.close()
        
        if task:
            return {
                'id': task[0],
                'task_number': task[1],
                'task_name': task[2],
                'status': task[3],
                'estimated_minutes': task[4],
                'phase_name': task[5]
            }
        
        return None
    
    def start_task(self, task_id: str) -> bool:
        """Mark task as started"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find task by task_number or id
        if task_id.count('.') > 0:  # Task number format like "1.1"
            cursor.execute('''
                UPDATE tasks 
                SET status = 'in_progress', start_date = ?
                WHERE task_number = ?
            ''', (datetime.now().isoformat(), task_id))
        else:  # Numeric ID
            cursor.execute('''
                UPDATE tasks 
                SET status = 'in_progress', start_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), int(task_id)))
        
        success = cursor.rowcount > 0
        
        if success:
            self.log_action("start_task", task_id, "Task marked as in progress")
        
        conn.commit()
        conn.close()
        
        return success
    
    def complete_task(self, task_id: str, notes: Optional[str] = None) -> bool:
        """Mark task as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find task by task_number or id
        if task_id.count('.') > 0:  # Task number format
            cursor.execute('''
                SELECT id, start_date FROM tasks WHERE task_number = ?
            ''', (task_id,))
        else:  # Numeric ID
            cursor.execute('''
                SELECT id, start_date FROM tasks WHERE id = ?
            ''', (int(task_id),))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        task_db_id, start_date = result
        
        # Calculate duration if task was started
        duration_minutes = None
        if start_date:
            start_time = datetime.fromisoformat(start_date)
            duration_minutes = int((datetime.now() - start_time).total_seconds() / 60)
        
        # Update task
        cursor.execute('''
            UPDATE tasks 
            SET status = 'completed', completion_date = ?, 
                actual_duration_minutes = ?, notes = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), duration_minutes, notes, task_db_id))
        
        success = cursor.rowcount > 0
        
        if success:
            self.log_action("complete_task", task_id, f"Task completed. Duration: {duration_minutes} minutes")
            self.create_checkpoint("task_completion", {
                'task_id': task_id,
                'completion_date': datetime.now().isoformat(),
                'duration_minutes': duration_minutes,
                'notes': notes
            })
        
        conn.commit()
        conn.close()
        
        return success
    
    def complete_phase(self, phase_number: int) -> bool:
        """Mark entire phase as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if all tasks in phase are completed
        cursor.execute('''
            SELECT COUNT(*) FROM tasks t
            JOIN phases p ON t.phase_id = p.id
            WHERE p.phase_number = ? AND t.status != 'completed'
        ''', (phase_number,))
        
        pending_tasks = cursor.fetchone()[0]
        if pending_tasks > 0:
            conn.close()
            return False
        
        # Mark phase as completed
        cursor.execute('''
            UPDATE phases 
            SET status = 'completed', completion_date = ?
            WHERE phase_number = ?
        ''', (datetime.now().isoformat(), phase_number))
        
        success = cursor.rowcount > 0
        
        if success:
            self.log_action("complete_phase", str(phase_number), f"Phase {phase_number} completed")
            self.create_checkpoint("phase_completion", {
                'phase_number': phase_number,
                'completion_date': datetime.now().isoformat()
            })
        
        conn.commit()
        conn.close()
        
        return success
    
    def complete_project(self) -> bool:
        """Mark entire project as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if all phases are completed
        cursor.execute('SELECT COUNT(*) FROM phases WHERE status != "completed"')
        pending_phases = cursor.fetchone()[0]
        
        if pending_phases > 0:
            conn.close()
            return False
        
        # Create final project completion checkpoint
        self.create_checkpoint("project_completion", {
            'completion_date': datetime.now().isoformat(),
            'total_phases': 3,
            'project_status': 'completed'
        })
        
        self.log_action("complete_project", "anti_sprawl_implementation", "Entire project completed successfully")
        
        conn.close()
        return True
    
    def create_checkpoint(self, checkpoint_type: str, data: Dict):
        """Create a checkpoint for resumability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO checkpoints (checkpoint_type, checkpoint_data)
            VALUES (?, ?)
        ''', (checkpoint_type, json.dumps(data)))
        
        conn.commit()
        conn.close()
        
        # Also save to file system
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'type': checkpoint_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'status': self.get_current_status()
            }, f, indent=2)
    
    def log_action(self, action: str, target: str, details: str, status: str = "success"):
        """Log an action to the implementation log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO implementation_log (action, target, details, status)
            VALUES (?, ?, ?, ?)
        ''', (action, target, details, status))
        
        conn.commit()
        conn.close()
    
    def get_task_details(self, task_id: str) -> Optional[Dict]:
        """Get detailed information about a specific task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_id.count('.') > 0:  # Task number format
            cursor.execute('''
                SELECT t.*, p.phase_name, p.phase_number
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE t.task_number = ?
            ''', (task_id,))
        else:  # Numeric ID
            cursor.execute('''
                SELECT t.*, p.phase_name, p.phase_number
                FROM tasks t
                JOIN phases p ON t.phase_id = p.id
                WHERE t.id = ?
            ''', (int(task_id),))
        
        task = cursor.fetchone()
        conn.close()
        
        if task:
            return {
                'id': task[0],
                'phase_id': task[1],
                'task_number': task[2],
                'task_name': task[3],
                'status': task[4],
                'start_date': task[5],
                'completion_date': task[6],
                'estimated_minutes': task[7],
                'actual_minutes': task[8],
                'notes': task[9],
                'deliverables': task[10],
                'phase_name': task[12],
                'phase_number': task[13]
            }
        
        return None
    
    def generate_progress_report(self) -> str:
        """Generate comprehensive progress report"""
        status = self.get_current_status()
        
        report = f"""# Anti-Sprawl Implementation Progress Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Progress
- **Completed Tasks**: {status['progress']['completed_tasks']}/{status['progress']['total_tasks']}
- **Progress**: {status['progress']['percentage']}%

## Phase Status
"""
        
        for phase in status['phases']:
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            emoji = status_emoji.get(phase['status'], "❓")
            
            report += f"### {emoji} Phase {phase['number']}: {phase['name']}\n"
            report += f"- **Status**: {phase['status'].title()}\n"
            report += f"- **Estimated**: {phase['estimated_hours']} hours\n"
            if phase['actual_hours']:
                report += f"- **Actual**: {phase['actual_hours']} hours\n"
            report += "\n"
        
        if status['current_task']:
            report += f"## Current Task\n"
            report += f"**{status['current_task']['task_number']}**: {status['current_task']['task_name']}\n"
            report += f"**Status**: {status['current_task']['status']}\n\n"
        
        return report

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 anti_sprawl_progress_tracker.py <command>")
        print("Commands:")
        print("  init                    - Initialize progress tracking")
        print("  status                  - Show current status")
        print("  next [--phase=N]        - Get next task")
        print("  start <task_id>         - Start working on task")
        print("  complete <task_id>      - Mark task as completed")
        print("  complete-phase <N>      - Mark phase as completed")
        print("  complete-project        - Mark entire project as completed")
        print("  task --id=<task_id>     - Get task details")
        print("  report                  - Generate progress report")
        return
    
    command = sys.argv[1]
    tracker = AntiSprawlProgressTracker()
    
    if command == 'init':
        print("✅ Progress tracking initialized")
        print("📊 Database created with default phases and tasks")
        
    elif command == 'status':
        status = tracker.get_current_status()
        print(f"📊 Implementation Progress: {status['progress']['percentage']}%")
        print(f"📋 Tasks: {status['progress']['completed_tasks']}/{status['progress']['total_tasks']} completed")
        
        print("\n📁 Phase Status:")
        for phase in status['phases']:
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            emoji = status_emoji.get(phase['status'], "❓")
            print(f"   {emoji} Phase {phase['number']}: {phase['name']} ({phase['status']})")
        
        if status['current_task']:
            print(f"\n🎯 Current Task: {status['current_task']['task_number']} - {status['current_task']['task_name']}")
        else:
            print("\n🎉 No pending tasks - implementation may be complete!")
    
    elif command == 'next':
        phase = None
        if len(sys.argv) > 2 and sys.argv[2].startswith('--phase='):
            phase = int(sys.argv[2].split('=')[1])
        
        task = tracker.get_next_task(phase)
        if task:
            print(f"📝 Next Task: {task['task_number']} - {task['task_name']}")
            print(f"📂 Phase: {task['phase_name']}")
            print(f"⏱️  Estimated: {task['estimated_minutes']} minutes")
            print(f"📋 Status: {task['status']}")
            print(f"\n🚀 To start: python3 anti_sprawl_progress_tracker.py start {task['task_number']}")
        else:
            print("🎉 No pending tasks found!")
    
    elif command == 'start':
        if len(sys.argv) < 3:
            print("Usage: start <task_id>")
            return
        
        task_id = sys.argv[2]
        if tracker.start_task(task_id):
            print(f"🚀 Started task {task_id}")
        else:
            print(f"❌ Failed to start task {task_id}")
    
    elif command == 'complete':
        if len(sys.argv) < 3:
            print("Usage: complete <task_id> [notes]")
            return
        
        task_id = sys.argv[2]
        notes = sys.argv[3] if len(sys.argv) > 3 else None
        
        if tracker.complete_task(task_id, notes):
            print(f"✅ Completed task {task_id}")
        else:
            print(f"❌ Failed to complete task {task_id}")
    
    elif command == 'complete-phase':
        if len(sys.argv) < 3:
            print("Usage: complete-phase <phase_number>")
            return
        
        phase_number = int(sys.argv[2])
        if tracker.complete_phase(phase_number):
            print(f"🎉 Completed Phase {phase_number}!")
        else:
            print(f"❌ Cannot complete Phase {phase_number} - pending tasks remain")
    
    elif command == 'complete-project':
        if tracker.complete_project():
            print("🎉🎉🎉 PROJECT COMPLETE! 🎉🎉🎉")
            print("✅ Anti-sprawl implementation successfully finished")
            print("🚀 Maia system now automatically prevents file sprawl")
        else:
            print("❌ Cannot complete project - pending phases remain")
    
    elif command == 'task':
        task_id = None
        for arg in sys.argv[2:]:
            if arg.startswith('--id='):
                task_id = arg.split('=')[1]
                break
        
        if not task_id:
            print("Usage: task --id=<task_id>")
            return
        
        task = tracker.get_task_details(task_id)
        if task:
            print(f"📝 Task: {task['task_number']} - {task['task_name']}")
            print(f"📂 Phase: {task['phase_number']} - {task['phase_name']}")
            print(f"📋 Status: {task['status']}")
            print(f"⏱️  Estimated: {task['estimated_minutes']} minutes")
            if task['actual_minutes']:
                print(f"⏱️  Actual: {task['actual_minutes']} minutes")
            if task['start_date']:
                print(f"🚀 Started: {task['start_date']}")
            if task['completion_date']:
                print(f"✅ Completed: {task['completion_date']}")
            if task['notes']:
                print(f"📝 Notes: {task['notes']}")
        else:
            print(f"❌ Task {task_id} not found")
    
    elif command == 'report':
        report = tracker.generate_progress_report()
        print(report)
        
        # Save report to file
        report_file = f"claude/data/progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()