#!/usr/bin/env python3
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ResumptionValidator:
    def __init__(self):
        self.critical_files = [
            'claude/context/core/anti_sprawl_master_implementation_plan.md',
            'claude/context/core/anti_sprawl_phase_1_detailed.md', 
            'claude/context/core/anti_sprawl_phase_2_detailed.md',
            'claude/context/core/anti_sprawl_phase_3_detailed.md',
            'claude/tools/anti_sprawl_progress_tracker.py'
        ]
        self.progress_db = "claude/data/anti_sprawl_progress.db"
        self.checkpoint_dir = Path("claude/data/implementation_checkpoints")
    
    def validate_resumption_capability(self) -> Dict:
        """Validate complete resumption capability"""
        validation_results = {
            'critical_files_present': False,
            'progress_tracking_functional': False,
            'checkpoint_system_ready': False,
            'resumption_instructions_clear': False,
            'database_initialized': False,
            'overall_resumable': False,
            'issues': [],
            'resumption_commands': []
        }
        
        # Check critical files
        missing_files = []
        for file_path in self.critical_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            validation_results['issues'].append(f"Missing critical files: {', '.join(missing_files)}")
        else:
            validation_results['critical_files_present'] = True
        
        # Check progress tracking system
        if Path(self.progress_db).exists():
            try:
                conn = sqlite3.connect(self.progress_db)
                cursor = conn.cursor()
                
                # Verify tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = ['phases', 'tasks', 'checkpoints', 'implementation_log']
                
                if all(table in tables for table in expected_tables):
                    validation_results['progress_tracking_functional'] = True
                    validation_results['database_initialized'] = True
                else:
                    validation_results['issues'].append("Database missing required tables")
                
                conn.close()
            except Exception as e:
                validation_results['issues'].append(f"Database error: {e}")
        else:
            validation_results['issues'].append("Progress tracking database not found")
        
        # Check checkpoint system
        if self.checkpoint_dir.exists():
            validation_results['checkpoint_system_ready'] = True
        else:
            validation_results['issues'].append("Checkpoint directory not found")
        
        # Verify resumption instructions
        master_plan_path = Path('claude/context/core/anti_sprawl_master_implementation_plan.md')
        if master_plan_path.exists():
            try:
                content = master_plan_path.read_text()
                if 'RESUMPTION PROTOCOL' in content and 'python3 claude/tools/anti_sprawl_progress_tracker.py' in content:
                    validation_results['resumption_instructions_clear'] = True
                else:
                    validation_results['issues'].append("Resumption instructions incomplete in master plan")
            except Exception as e:
                validation_results['issues'].append(f"Cannot read master plan: {e}")
        
        # Generate resumption commands
        validation_results['resumption_commands'] = self.generate_resumption_commands()
        
        # Overall assessment
        critical_checks = [
            validation_results['critical_files_present'],
            validation_results['progress_tracking_functional'],
            validation_results['checkpoint_system_ready'],
            validation_results['resumption_instructions_clear'],
            validation_results['database_initialized']
        ]
        
        validation_results['overall_resumable'] = all(critical_checks)
        
        return validation_results
    
    def generate_resumption_commands(self) -> List[str]:
        """Generate step-by-step resumption commands"""
        return [
            "# Step 1: Check current implementation status",
            "python3 claude/tools/anti_sprawl_progress_tracker.py status",
            "",
            "# Step 2: Get next task to work on", 
            "python3 claude/tools/anti_sprawl_progress_tracker.py next",
            "",
            "# Step 3: Load appropriate detailed plan",
            "# (Based on current phase from status command)",
            "# Phase 1: claude/context/core/anti_sprawl_phase_1_detailed.md",
            "# Phase 2: claude/context/core/anti_sprawl_phase_2_detailed.md", 
            "# Phase 3: claude/context/core/anti_sprawl_phase_3_detailed.md",
            "",
            "# Step 4: Start working on the task",
            "python3 claude/tools/anti_sprawl_progress_tracker.py start <task_id>",
            "",
            "# Step 5: Mark task complete when finished",
            "python3 claude/tools/anti_sprawl_progress_tracker.py complete <task_id>",
            "",
            "# Alternative: Get detailed task information",
            "python3 claude/tools/anti_sprawl_progress_tracker.py task --id=<task_id>"
        ]
    
    def test_resumption_scenario(self) -> Dict:
        """Test a complete resumption scenario"""
        test_results = {
            'scenario': 'new_context_window_resumption',
            'steps_tested': [],
            'successful_steps': 0,
            'failed_steps': 0,
            'overall_success': False
        }
        
        # Test Step 1: Status check
        try:
            result = os.popen('python3 claude/tools/anti_sprawl_progress_tracker.py status 2>/dev/null').read()
            if 'Implementation Progress' in result:
                test_results['steps_tested'].append({'step': 'status_check', 'success': True})
                test_results['successful_steps'] += 1
            else:
                test_results['steps_tested'].append({'step': 'status_check', 'success': False, 'error': 'Invalid status output'})
                test_results['failed_steps'] += 1
        except Exception as e:
            test_results['steps_tested'].append({'step': 'status_check', 'success': False, 'error': str(e)})
            test_results['failed_steps'] += 1
        
        # Test Step 2: Next task
        try:
            result = os.popen('python3 claude/tools/anti_sprawl_progress_tracker.py next 2>/dev/null').read()
            if 'Next Task' in result or 'No pending tasks' in result:
                test_results['steps_tested'].append({'step': 'next_task', 'success': True})
                test_results['successful_steps'] += 1
            else:
                test_results['steps_tested'].append({'step': 'next_task', 'success': False, 'error': 'Invalid next task output'})
                test_results['failed_steps'] += 1
        except Exception as e:
            test_results['steps_tested'].append({'step': 'next_task', 'success': False, 'error': str(e)})
            test_results['failed_steps'] += 1
        
        # Test Step 3: Master plan accessibility
        try:
            master_plan = Path('claude/context/core/anti_sprawl_master_implementation_plan.md')
            if master_plan.exists() and master_plan.stat().st_size > 1000:
                test_results['steps_tested'].append({'step': 'master_plan_access', 'success': True})
                test_results['successful_steps'] += 1
            else:
                test_results['steps_tested'].append({'step': 'master_plan_access', 'success': False, 'error': 'Master plan missing or empty'})
                test_results['failed_steps'] += 1
        except Exception as e:
            test_results['steps_tested'].append({'step': 'master_plan_access', 'success': False, 'error': str(e)})
            test_results['failed_steps'] += 1
        
        # Test Step 4: Phase plan accessibility  
        phase_plans = [
            'claude/context/core/anti_sprawl_phase_1_detailed.md',
            'claude/context/core/anti_sprawl_phase_2_detailed.md',
            'claude/context/core/anti_sprawl_phase_3_detailed.md'
        ]
        
        accessible_plans = 0
        for plan in phase_plans:
            if Path(plan).exists() and Path(plan).stat().st_size > 1000:
                accessible_plans += 1
        
        if accessible_plans == len(phase_plans):
            test_results['steps_tested'].append({'step': 'phase_plans_access', 'success': True})
            test_results['successful_steps'] += 1
        else:
            test_results['steps_tested'].append({'step': 'phase_plans_access', 'success': False, 'error': f'Only {accessible_plans}/{len(phase_plans)} plans accessible'})
            test_results['failed_steps'] += 1
        
        # Overall success assessment
        test_results['overall_success'] = test_results['failed_steps'] == 0
        
        return test_results
    
    def create_resumption_guide(self) -> str:
        """Create a comprehensive resumption guide"""
        guide = f"""# Anti-Sprawl Implementation Resumption Guide
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Purpose**: Complete guide for resuming implementation in any context window

## 🚨 EMERGENCY RESUMPTION PROTOCOL 🚨

If you are reading this in a new context window and need to resume the anti-sprawl implementation:

### STEP 1: Load Master Implementation Plan
```bash
# Read the complete implementation overview
cat claude/context/core/anti_sprawl_master_implementation_plan.md
```

### STEP 2: Check Current Progress
```bash
# Check where you left off
python3 claude/tools/anti_sprawl_progress_tracker.py status
```

### STEP 3: Get Next Task
```bash
# Find the next task to work on
python3 claude/tools/anti_sprawl_progress_tracker.py next
```

### STEP 4: Load Detailed Phase Plan
Based on the current phase from Step 2, read the appropriate detailed plan:
- **Phase 1**: `claude/context/core/anti_sprawl_phase_1_detailed.md`
- **Phase 2**: `claude/context/core/anti_sprawl_phase_2_detailed.md`
- **Phase 3**: `claude/context/core/anti_sprawl_phase_3_detailed.md`

### STEP 5: Resume Implementation
```bash
# Start the current task
python3 claude/tools/anti_sprawl_progress_tracker.py start <task_id>

# Follow the step-by-step instructions in the detailed phase plan

# Mark task complete when finished
python3 claude/tools/anti_sprawl_progress_tracker.py complete <task_id>
```

## IMPLEMENTATION FILES REFERENCE

### Master Planning
- `claude/context/core/anti_sprawl_master_implementation_plan.md` - Complete overview
- `claude/tools/anti_sprawl_progress_tracker.py` - Progress tracking system

### Detailed Phase Plans
- `claude/context/core/anti_sprawl_phase_1_detailed.md` - Phase 1: Stabilize Current Structure
- `claude/context/core/anti_sprawl_phase_2_detailed.md` - Phase 2: Automated Organization  
- `claude/context/core/anti_sprawl_phase_3_detailed.md` - Phase 3: Proactive Management

### Progress Data
- `claude/data/anti_sprawl_progress.db` - SQLite database with complete progress
- `claude/data/implementation_checkpoints/` - Checkpoint files for recovery

## VALIDATION COMMANDS

### Check System Health
```bash
# Validate resumption capability
python3 claude/tools/resumption_validator.py validate

# Test resumption scenario
python3 claude/tools/resumption_validator.py test-scenario

# Generate progress report
python3 claude/tools/anti_sprawl_progress_tracker.py report
```

### Manual Fallback
If automated tracking fails, check these files for manual progress:
- Phase completion reports in `claude/data/`
- Git commit history for implementation progress
- File modification timestamps for recent work

## TROUBLESHOOTING

### Database Issues
```bash
# Reinitialize if database is corrupted
python3 claude/tools/anti_sprawl_progress_tracker.py init
```

### Missing Files
If critical files are missing, they can be regenerated:
- Progress tracker creates missing directories automatically
- Phase plans are comprehensive and standalone
- Master plan contains all necessary information

### Context Loss Recovery
1. Read master plan for complete overview
2. Check current file structure to assess progress
3. Use git history to understand recent changes
4. Restart from last verifiable checkpoint

## SUCCESS CRITERIA

The implementation is complete when:
- All 3 phases show "completed" status
- Final validation passes all checks
- Anti-sprawl systems are operational
- Success report is generated

## SUPPORT INFORMATION

This resumption system is designed to be bulletproof against context loss. Every piece of information needed to continue implementation is preserved in the file system and database.

**Remember**: The goal is to eliminate file sprawl through systematic implementation of immutable core structures, automated organization, and proactive management systems.
"""
        
        return guide
    
    def run_complete_validation(self) -> Dict:
        """Run complete validation and testing"""
        print("🔍 Validating Anti-Sprawl Implementation Resumption Capability...")
        print("=" * 70)
        
        # Validate resumption capability
        validation = self.validate_resumption_capability()
        
        print("📋 Resumption Capability Validation:")
        checks = [
            ('Critical Files Present', validation['critical_files_present']),
            ('Progress Tracking Functional', validation['progress_tracking_functional']),
            ('Checkpoint System Ready', validation['checkpoint_system_ready']),
            ('Resumption Instructions Clear', validation['resumption_instructions_clear']),
            ('Database Initialized', validation['database_initialized'])
        ]
        
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {check_name:.<35} {status}")
        
        if validation['issues']:
            print("\n⚠️  Issues Found:")
            for issue in validation['issues']:
                print(f"   • {issue}")
        
        print("\n🧪 Testing Resumption Scenario...")
        test_results = self.test_resumption_scenario()
        
        print("📊 Resumption Test Results:")
        for step in test_results['steps_tested']:
            status = "✅ PASS" if step['success'] else "❌ FAIL"
            error = f" - {step['error']}" if not step['success'] else ""
            print(f"   {step['step']:.<35} {status}{error}")
        
        print("=" * 70)
        
        overall_success = validation['overall_resumable'] and test_results['overall_success']
        
        if overall_success:
            print("🎉 RESUMPTION VALIDATION: ALL SYSTEMS OPERATIONAL")
            print("✅ Implementation can be resumed from any context window")
            print("🔄 Complete resumption capability confirmed")
        else:
            print("⚠️  RESUMPTION VALIDATION: ISSUES DETECTED")
            print("❌ Some resumption capabilities may not work correctly")
        
        # Generate resumption guide
        guide = self.create_resumption_guide()
        guide_file = "claude/context/core/anti_sprawl_resumption_guide.md"
        with open(guide_file, 'w') as f:
            f.write(guide)
        
        print(f"\n📖 Resumption guide created: {guide_file}")
        
        return {
            'validation': validation,
            'test_results': test_results,
            'overall_success': overall_success,
            'guide_file': guide_file
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resumption_validator.py <command>")
        print("Commands:")
        print("  validate        - Validate resumption capability")
        print("  test-scenario   - Test complete resumption scenario")
        print("  create-guide    - Create resumption guide")
        print("  full-validation - Run complete validation and testing")
        return
    
    command = sys.argv[1]
    validator = ResumptionValidator()
    
    if command == 'validate':
        validation = validator.validate_resumption_capability()
        
        print("📋 Resumption Capability Validation:")
        print(f"   Overall Resumable: {'✅ Yes' if validation['overall_resumable'] else '❌ No'}")
        print(f"   Critical Files: {'✅ Present' if validation['critical_files_present'] else '❌ Missing'}")
        print(f"   Progress Tracking: {'✅ Functional' if validation['progress_tracking_functional'] else '❌ Non-functional'}")
        print(f"   Checkpoints: {'✅ Ready' if validation['checkpoint_system_ready'] else '❌ Not Ready'}")
        
        if validation['issues']:
            print("\n⚠️  Issues:")
            for issue in validation['issues']:
                print(f"   • {issue}")
        
        if validation['resumption_commands']:
            print("\n📋 Resumption Commands:")
            for command in validation['resumption_commands']:
                print(f"   {command}")
    
    elif command == 'test-scenario':
        results = validator.test_resumption_scenario()
        
        print(f"🧪 Resumption Scenario Test: {results['scenario']}")
        print(f"   Successful Steps: {results['successful_steps']}")
        print(f"   Failed Steps: {results['failed_steps']}")
        print(f"   Overall Success: {'✅ Pass' if results['overall_success'] else '❌ Fail'}")
        
        print("\n📊 Detailed Results:")
        for step in results['steps_tested']:
            status = "✅" if step['success'] else "❌"
            error = f" - {step['error']}" if not step['success'] else ""
            print(f"   {status} {step['step']}{error}")
    
    elif command == 'create-guide':
        guide = validator.create_resumption_guide()
        guide_file = "claude/context/core/anti_sprawl_resumption_guide.md"
        
        with open(guide_file, 'w') as f:
            f.write(guide)
        
        print(f"📖 Resumption guide created: {guide_file}")
    
    elif command == 'full-validation':
        validator.run_complete_validation()

if __name__ == "__main__":
    import sys
    main()