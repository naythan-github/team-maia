#!/usr/bin/env python3
"""
Project Recovery File Generator

Generates comprehensive project recovery files from templates to prevent context
compaction drift and project amnesia.

Usage:
    python3 generate_recovery_files.py --interactive
    python3 generate_recovery_files.py --config project_config.json
    python3 generate_recovery_files.py --project "My Project" --phases 5 --output claude/data/

Features:
    - Interactive mode with guided prompts
    - JSON config file support
    - Template-based generation with {{PLACEHOLDER}} replacement
    - Automatic directory creation
    - Validation of generated files
    - Example config generation

Author: Maia (My AI Agent)
Created: 2025-10-15
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class RecoveryFileGenerator:
    """Generates project recovery files from templates."""

    def __init__(self, template_dir: str = None):
        """Initialize generator with template directory."""
        if template_dir is None:
            # Default to script's directory
            script_dir = Path(__file__).parent
            self.template_dir = script_dir
        else:
            self.template_dir = Path(template_dir)

        self.templates = {
            'project_plan': self.template_dir / 'PROJECT_PLAN_TEMPLATE.md',
            'recovery_json': self.template_dir / 'RECOVERY_STATE_TEMPLATE.json',
            'start_here': self.template_dir / 'START_HERE_TEMPLATE.md'
        }

        # Validate templates exist
        for name, path in self.templates.items():
            if not path.exists():
                raise FileNotFoundError(f"Template not found: {path}")

    def interactive_mode(self) -> Dict[str, Any]:
        """Run interactive mode to gather project details."""
        print("🚀 Project Recovery File Generator - Interactive Mode\n")
        print("This wizard will help you create comprehensive project recovery files.")
        print("Press Ctrl+C at any time to cancel.\n")

        config = {}

        # Basic project info
        config['project_name'] = input("Project name: ").strip()
        config['project_id'] = input("Project ID (e.g., PROJECT_NAME_001): ").strip()

        # Problem and solution
        print("\n--- Problem & Solution ---")
        config['problem_one_line'] = input("Problem (one line): ").strip()
        config['solution_one_line'] = input("Solution (one line): ").strip()
        config['user_feedback'] = input("User feedback/request that triggered this: ").strip()

        # Project structure
        print("\n--- Project Structure ---")
        num_phases = int(input("Number of phases: "))
        config['total_phases'] = num_phases
        config['phases'] = []

        for i in range(1, num_phases + 1):
            print(f"\n  Phase {i}:")
            phase = {
                'phase': i,
                'name': input(f"    Name: ").strip(),
                'duration': input(f"    Duration (e.g., '30 min'): ").strip(),
                'deliverable': input(f"    Deliverable: ").strip(),
                'description': input(f"    Description: ").strip()
            }
            config['phases'].append(phase)

        # Files
        print("\n--- Files ---")
        config['files_to_create'] = []
        while True:
            file = input("File to create (empty to finish): ").strip()
            if not file:
                break
            config['files_to_create'].append(file)

        config['files_to_modify'] = []
        while True:
            file = input("File to modify (empty to finish): ").strip()
            if not file:
                break
            config['files_to_modify'].append(file)

        # Output location
        print("\n--- Output ---")
        default_output = f"claude/data/{config['project_id']}"
        config['output_dir'] = input(f"Output directory [{default_output}]: ").strip() or default_output

        # Auto-fill derived fields
        config['creation_date'] = datetime.now().strftime('%Y-%m-%d')
        config['project_status'] = 'planning_complete'
        config['current_phase'] = 0

        return config

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)

    def generate_project_plan(self, config: Dict[str, Any]) -> str:
        """Generate project plan markdown from template."""
        with open(self.templates['project_plan'], 'r') as f:
            template = f.read()

        # Build phase definitions
        phase_defs = []
        for phase in config['phases']:
            phase_defs.append(f"""### Phase {phase['phase']}: {phase['name']}
**Duration**: {phase['duration']}
**Status**: pending
**Deliverable**: {phase['deliverable']}

{phase['description']}

**Checkpoint**: Deliverable exists and validated
""")

        # Build timeline table
        timeline_rows = []
        for phase in config['phases']:
            timeline_rows.append(f"| Phase {phase['phase']} | {phase['duration']} | TBD | TBD | Pending |")

        # Replace placeholders
        replacements = {
            '{{PROJECT_NAME}}': config.get('project_name', 'Unnamed Project'),
            '{{PROJECT_ID}}': config.get('project_id', 'PROJECT_001'),
            '{{CREATION_DATE}}': config.get('creation_date', datetime.now().strftime('%Y-%m-%d')),
            '{{PROJECT_STATUS}}': config.get('project_status', 'planning_complete'),
            '{{CURRENT_PHASE}}': str(config.get('current_phase', 0)),
            '{{TOTAL_PHASES}}': str(config.get('total_phases', len(config.get('phases', [])))),
            '{{PROBLEM_DESCRIPTION}}': config.get('problem_one_line', 'TBD'),
            '{{SOLUTION_DESCRIPTION}}': config.get('solution_one_line', 'TBD'),
            '{{TOTAL_DURATION}}': self._calculate_total_duration(config.get('phases', [])),
            '{{DELIVERABLE_COUNT}}': str(len(config.get('files_to_create', []))),
            '{{SUCCESS_CRITERIA_SUMMARY}}': 'TBD',
            '{{ACHIEVEMENT_DESCRIPTION}}': config.get('solution_one_line', 'TBD'),
            '{{USER_FEEDBACK}}': config.get('user_feedback', 'TBD'),
            '{{ROOT_CAUSE_ANALYSIS}}': 'TBD',
            '{{IMPACT_ANALYSIS}}': 'TBD',
            '{{DETAILED_SOLUTION_DESIGN}}': config.get('solution_one_line', 'TBD'),
            '{{ARCHITECTURE_DESCRIPTION}}': 'TBD',
            '{{COMPONENT_LIST}}': 'TBD',
            '{{PHASE_DEFINITIONS}}': '\n'.join(phase_defs),
            '{{FILES_TO_CREATE_LIST}}': '\n'.join(f"- {f}" for f in config.get('files_to_create', [])),
            '{{FILES_TO_MODIFY_LIST}}': '\n'.join(f"- {f}" for f in config.get('files_to_modify', [])),
            '{{SUCCESS_METRICS_TABLE}}': 'TBD',
            '{{PROJECT_FILE_PATH}}': f"{config.get('output_dir', 'TBD')}/{config.get('project_id', 'PROJECT')}.md",
            '{{RECOVERY_JSON_PATH}}': f"{config.get('output_dir', 'TBD')}/{config.get('project_id', 'PROJECT')}_RECOVERY.json",
            '{{DETAILED_PHASE_GUIDE}}': 'TBD - See phase definitions above',
            '{{TEST_SCENARIOS}}': 'TBD',
            '{{VALIDATION_CRITERIA}}': 'TBD',
            '{{ACCEPTANCE_TESTS}}': 'TBD',
            '{{COMPLETED_PHASES_LIST}}': 'None yet',
            '{{CURRENT_PHASE_STATUS}}': 'Planning complete',
            '{{REMAINING_WORK_LIST}}': f"All {config.get('total_phases', 0)} phases pending",
            '{{RELATED_DOCS_LIST}}': 'TBD',
            '{{KEY_INSIGHTS}}': 'TBD',
            '{{LESSONS_LEARNED}}': 'TBD - Will be updated as project progresses',
            '{{TIMELINE_TABLE_ROWS}}': '\n'.join(timeline_rows),
            '{{STAKEHOLDER_INFO}}': 'TBD',
            '{{CONFIDENCE_LEVEL}}': 'TBD',
            '{{NEXT_CHECKPOINT}}': f"Phase 1: {config.get('phases', [{}])[0].get('name', 'TBD') if config.get('phases') else 'TBD'}",
            '{{LAST_UPDATED_DATE}}': datetime.now().strftime('%Y-%m-%d'),
            '{{LAST_UPDATED_BY}}': 'Maia (Generator Script)'
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def generate_recovery_json(self, config: Dict[str, Any]) -> str:
        """Generate recovery state JSON from template."""
        with open(self.templates['recovery_json'], 'r') as f:
            template = f.read()

        # Build phase array
        phase_array = []
        for phase in config['phases']:
            phase_array.append(json.dumps({
                'phase': phase['phase'],
                'name': phase['name'],
                'duration': phase['duration'],
                'status': 'pending',
                'deliverable': phase['deliverable'],
                'description': phase['description'],
                'checkpoint': 'Deliverable exists and validated'
            }, indent=4))

        # Build phase progress object
        phase_progress = {}
        for i in range(1, config.get('total_phases', 0) + 1):
            phase_progress[f'phase_{i}'] = {
                'started': None,
                'completed': None,
                'deliverable_exists': False,
                'notes': ''
            }

        # Replace placeholders
        replacements = {
            '{{PROJECT_ID}}': config.get('project_id', 'PROJECT_001'),
            '{{PROJECT_FILE_PATH}}': f"{config.get('output_dir', 'claude/data')}/{config.get('project_id', 'PROJECT')}.md",
            '{{CREATION_DATE}}': config.get('creation_date', datetime.now().strftime('%Y-%m-%d')),
            '{{PROJECT_STATUS}}': config.get('project_status', 'planning_complete'),
            '{{CURRENT_PHASE_NUMBER}}': str(config.get('current_phase', 0)),
            '{{TOTAL_PHASES}}': str(config.get('total_phases', 0)),
            '{{QUICK_SUMMARY}}': config.get('solution_one_line', 'TBD'),
            '{{PROBLEM_ONE_LINE}}': config.get('problem_one_line', 'TBD'),
            '{{SOLUTION_ONE_LINE}}': config.get('solution_one_line', 'TBD'),
            '{{PHASE_ARRAY_ITEMS}}': ',\n    '.join(phase_array),
            '{{FILES_TO_CREATE_ARRAY}}': ',\n    '.join(f'"{f}"' for f in config.get('files_to_create', [])),
            '{{FILES_TO_MODIFY_ARRAY}}': ',\n    '.join(f'"{f}"' for f in config.get('files_to_modify', [])),
            '{{SUCCESS_METRICS_OBJECT}}': '"tbd": "Define success metrics"',
            '{{PHASE_PROGRESS_OBJECT}}': json.dumps(phase_progress, indent=4)[1:-1],  # Remove outer braces
            '{{LAST_UPDATED_DATE}}': datetime.now().strftime('%Y-%m-%d'),
            '{{LAST_UPDATED_BY}}': 'Maia (Generator Script)',
            '{{KEY_INSIGHT}}': config.get('solution_one_line', 'TBD')
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        # Validate JSON
        try:
            json.loads(template)
        except json.JSONDecodeError as e:
            print(f"WARNING: Generated JSON is invalid: {e}")
            print("You may need to manually fix the JSON file.")

        return template

    def generate_start_here(self, config: Dict[str, Any]) -> str:
        """Generate START_HERE guide from template."""
        with open(self.templates['start_here'], 'r') as f:
            template = f.read()

        # Build phase summary
        phase_summary = []
        for i, phase in enumerate(config.get('phases', []), 1):
            phase_summary.append(f"{i}. ⏳ {phase['name']} ({phase['duration']})")

        # Build deliverable check commands
        check_commands = []
        for phase in config.get('phases', []):
            deliverable = phase['deliverable']
            check_commands.append(f'ls -la {deliverable} 2>/dev/null || echo "Phase {phase["phase"]}: Not started"')

        # Replace placeholders
        replacements = {
            '{{PROJECT_NAME}}': config.get('project_name', 'Unnamed Project'),
            '{{PROBLEM_ONE_LINE}}': config.get('problem_one_line', 'TBD'),
            '{{SOLUTION_ONE_LINE}}': config.get('solution_one_line', 'TBD'),
            '{{RECOVERY_JSON_PATH}}': f"{config.get('output_dir', 'claude/data')}/{config.get('project_id', 'PROJECT')}_RECOVERY.json",
            '{{PROJECT_FILE_PATH}}': f"{config.get('output_dir', 'claude/data')}/{config.get('project_id', 'PROJECT')}.md",
            '{{DELIVERABLE_CHECK_COMMANDS}}': '\n'.join(check_commands),
            '{{TOTAL_PHASES}}': str(config.get('total_phases', 0)),
            '{{TOTAL_DURATION}}': self._calculate_total_duration(config.get('phases', [])),
            '{{PHASE_SUMMARY_LIST}}': '\n'.join(phase_summary),
            '{{USER_FEEDBACK}}': config.get('user_feedback', 'TBD'),
            '{{ROOT_CAUSE_ONE_LINE}}': config.get('problem_one_line', 'TBD'),
            '{{SOLUTION_BULLET_POINTS}}': config.get('solution_one_line', 'TBD'),
            '{{EXPECTED_RESULT}}': 'TBD',
            '{{START_HERE_PATH}}': f"{config.get('output_dir', 'claude/data')}/implementation_checkpoints/{config.get('project_id', 'PROJECT')}_START_HERE.md"
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def _calculate_total_duration(self, phases: List[Dict]) -> str:
        """Calculate total project duration from phase durations."""
        # Simple implementation - just concatenate
        # Could be enhanced to parse and sum actual time
        if not phases:
            return 'TBD'

        durations = [p.get('duration', '') for p in phases]
        return ', '.join(durations)

    def generate_all(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate all three recovery files."""
        return {
            'project_plan': self.generate_project_plan(config),
            'recovery_json': self.generate_recovery_json(config),
            'start_here': self.generate_start_here(config)
        }

    def write_files(self, config: Dict[str, Any], generated: Dict[str, str]):
        """Write generated files to disk."""
        output_dir = Path(config.get('output_dir', 'claude/data'))
        project_id = config.get('project_id', 'PROJECT')

        # Create directories
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'implementation_checkpoints').mkdir(parents=True, exist_ok=True)

        # Write files
        files_written = []

        # Project plan
        plan_path = output_dir / f"{project_id}.md"
        with open(plan_path, 'w') as f:
            f.write(generated['project_plan'])
        files_written.append(plan_path)

        # Recovery JSON
        json_path = output_dir / f"{project_id}_RECOVERY.json"
        with open(json_path, 'w') as f:
            f.write(generated['recovery_json'])
        files_written.append(json_path)

        # Start here
        start_path = output_dir / 'implementation_checkpoints' / f"{project_id}_START_HERE.md"
        with open(start_path, 'w') as f:
            f.write(generated['start_here'])
        files_written.append(start_path)

        return files_written

    def generate_example_config(self, output_path: str = 'project_config_example.json'):
        """Generate an example configuration file."""
        example = {
            "project_name": "Example Project",
            "project_id": "EXAMPLE_PROJECT_001",
            "problem_one_line": "Current process takes too long and is error-prone",
            "solution_one_line": "Automate the process with validation and monitoring",
            "user_feedback": "Can you help me automate this tedious manual process?",
            "total_phases": 3,
            "phases": [
                {
                    "phase": 1,
                    "name": "Setup and Configuration",
                    "duration": "30 min",
                    "deliverable": "claude/tools/example_tool.py",
                    "description": "Create initial tool structure and configuration"
                },
                {
                    "phase": 2,
                    "name": "Core Implementation",
                    "duration": "1 hour",
                    "deliverable": "Working prototype with basic features",
                    "description": "Implement core functionality and validation"
                },
                {
                    "phase": 3,
                    "name": "Testing and Documentation",
                    "duration": "30 min",
                    "deliverable": "Test suite and usage docs",
                    "description": "Add tests and documentation"
                }
            ],
            "files_to_create": [
                "claude/tools/example_tool.py",
                "claude/tools/tests/test_example_tool.py"
            ],
            "files_to_modify": [
                "claude/context/tools/available.md",
                "SYSTEM_STATE.md"
            ],
            "output_dir": "claude/data/EXAMPLE_PROJECT_001",
            "creation_date": datetime.now().strftime('%Y-%m-%d'),
            "project_status": "planning_complete",
            "current_phase": 0
        }

        with open(output_path, 'w') as f:
            json.dump(example, f, indent=2)

        print(f"✅ Example configuration written to: {output_path}")
        print(f"   Edit this file and run: python3 {__file__} --config {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate project recovery files from templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 generate_recovery_files.py --interactive

  # From config file
  python3 generate_recovery_files.py --config my_project.json

  # Generate example config
  python3 generate_recovery_files.py --example-config
        """
    )

    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('--config', '-c', type=str,
                        help='Load configuration from JSON file')
    parser.add_argument('--example-config', action='store_true',
                        help='Generate an example configuration file')
    parser.add_argument('--output', '-o', type=str,
                        help='Output directory (overrides config)')

    args = parser.parse_args()

    try:
        generator = RecoveryFileGenerator()

        if args.example_config:
            generator.generate_example_config()
            return 0

        # Get configuration
        if args.interactive:
            config = generator.interactive_mode()
        elif args.config:
            config = generator.load_config(args.config)
        else:
            print("Error: Must specify either --interactive or --config")
            parser.print_help()
            return 1

        # Override output if specified
        if args.output:
            config['output_dir'] = args.output

        # Generate files
        print("\n🔨 Generating recovery files...")
        generated = generator.generate_all(config)

        # Write to disk
        print("💾 Writing files...")
        files_written = generator.write_files(config, generated)

        # Success
        print("\n✅ Project recovery files generated successfully!\n")
        print("Files created:")
        for file in files_written:
            print(f"  ✓ {file}")

        print(f"\n📁 Output directory: {config.get('output_dir')}")
        print(f"\n🚀 Next steps:")
        print(f"   1. Review generated files for accuracy")
        print(f"   2. Fill in 'TBD' sections in project plan")
        print(f"   3. Begin Phase 1 implementation")
        print(f"   4. Update recovery JSON after each phase")

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
