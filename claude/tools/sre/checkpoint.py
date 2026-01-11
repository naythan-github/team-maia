#!/usr/bin/env python3
"""
Checkpoint - Compaction-Ready Progress Documentation

Phase 260.5: Structured checkpoint generation for mid-project compaction with
guaranteed resumption and agent restoration.

Generates structured checkpoint files to enable picking up work after context
compaction without losing progress or agent configuration.

Usage:
    python3 claude/tools/sre/checkpoint.py                    # Interactive
    python3 claude/tools/sre/checkpoint.py --phase "Phase 260" # With phase
    python3 claude/tools/sre/checkpoint.py --auto              # Auto-detect all
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import argparse


# Durable checkpoint storage - survives /tmp cleanup and reboots
DURABLE_CHECKPOINT_DIR = Path.home() / ".maia" / "checkpoints"


@dataclass
class ProjectState:
    """Current state of the project."""
    # Git state
    modified_files: List[str]
    staged_files: List[str]
    new_files: List[str]
    deleted_files: List[str]
    current_branch: str
    last_commit: str

    # Test state
    tests_passing: int
    tests_total: int
    test_details: str

    # Agent state
    current_agent: str
    context_id: str
    session_start: Optional[str]
    domain: str

    # Project metadata
    phase_number: Optional[int] = None
    phase_name: Optional[str] = None
    percent_complete: Optional[int] = None
    tdd_phase: Optional[str] = None

    def to_json_dict(self) -> Dict:
        """Convert state to JSON-serializable dictionary for durable storage."""
        return {
            "context_id": self.context_id,
            "created_at": datetime.now().isoformat(),
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "percent_complete": self.percent_complete,
            "tdd_phase": self.tdd_phase,
            "recommended_agent": self.recommended_agent,
            "current_agent": self.current_agent,
            "domain": self.domain,
            "session_start": self.session_start,
            "tests_passing": self.tests_passing,
            "tests_total": self.tests_total,
            "current_branch": self.current_branch,
            "last_commit": self.last_commit,
            "modified_files": self.modified_files[:20],  # Limit for JSON size
            "staged_files": self.staged_files[:20],
            "new_files": self.new_files[:20],
            "deleted_files": self.deleted_files[:20],
            "is_code_project": self.is_code_project,
            "next_action": self._suggest_next_action()
        }

    def _suggest_next_action(self) -> str:
        """Suggest specific next action based on state."""
        if self.tests_total == 0:
            return "Write tests for current implementation (TDD P3)"
        elif self.tests_passing < self.tests_total:
            return f"Fix {self.tests_total - self.tests_passing} failing tests"
        elif self.modified_files and not self.staged_files:
            return "Stage completed work: git add <files>"
        else:
            return "Continue implementation (see Next Steps section)"

    @property
    def is_code_project(self) -> bool:
        """Detect if this is a code project requiring SRE agent."""
        code_extensions = {'.py', '.ts', '.js', '.go', '.rs', '.java', '.cpp', '.c'}
        all_files = self.modified_files + self.staged_files + self.new_files
        return any(Path(f).suffix in code_extensions for f in all_files)

    @property
    def recommended_agent(self) -> str:
        """Recommend agent for resumption."""
        if self.is_code_project:
            return "sre_principal_engineer_agent"
        return self.current_agent or "sre_principal_engineer_agent"


class CheckpointGenerator:
    """
    Generate structured checkpoint files for compaction resilience.

    Ensures work can be resumed exactly where it left off after context
    compaction, with proper agent restoration.
    """

    def __init__(self, maia_root: Optional[Path] = None):
        self.maia_root = maia_root or Path(__file__).resolve().parent.parent.parent.parent
        self.checkpoint_dir = Path("/tmp")

    def gather_state(self) -> ProjectState:
        """Gather current project state from git, tests, and session."""

        # Git state
        modified = self._run_git(["diff", "--name-only"]).splitlines()
        staged = self._run_git(["diff", "--cached", "--name-only"]).splitlines()

        # Get file status (A/M/D)
        status_output = self._run_git(["status", "--short"])
        new_files = [line[3:] for line in status_output.splitlines() if line.startswith("A ")]
        deleted = [line[3:] for line in status_output.splitlines() if line.startswith("D ")]

        # Branch and commit info
        branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        last_commit = self._run_git(["log", "-1", "--oneline"]).strip()

        # Test state
        tests_passing, tests_total, test_details = self._run_tests()

        # Agent state
        agent_info = self._get_agent_info()

        return ProjectState(
            modified_files=modified,
            staged_files=staged,
            new_files=new_files,
            deleted_files=deleted,
            current_branch=branch,
            last_commit=last_commit,
            tests_passing=tests_passing,
            tests_total=tests_total,
            test_details=test_details,
            current_agent=agent_info['agent'],
            context_id=agent_info['context_id'],
            session_start=agent_info['session_start'],
            domain=agent_info['domain']
        )

    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""

    def _run_tests(self) -> Tuple[int, int, str]:
        """Run pytest and extract summary."""
        try:
            result = subprocess.run(
                ["pytest", "tests/", "-v", "--tb=short"],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )
            output = result.stdout + result.stderr

            # Parse pytest summary line
            # Looking for: "X passed" or "X passed, Y failed"
            match = re.search(r'(\d+) passed', output)
            if match:
                passed = int(match.group(1))

                # Check for failures
                fail_match = re.search(r'(\d+) failed', output)
                failed = int(fail_match.group(1)) if fail_match else 0

                total = passed + failed

                # Get last 20 lines for details
                details = '\n'.join(output.splitlines()[-20:])

                return passed, total, details

            return 0, 0, "No test results found"

        except subprocess.TimeoutExpired:
            return 0, 0, "Tests timed out after 60s"
        except Exception as e:
            return 0, 0, f"Test execution failed: {e}"

    def _get_agent_info(self) -> Dict[str, str]:
        """Get current agent and session info."""
        try:
            # Get context ID
            result = subprocess.run(
                ["python3", "claude/hooks/swarm_auto_loader.py", "get_context_id"],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                check=False
            )
            context_id = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Try to read session file
            session_file = Path.home() / ".maia" / "sessions" / f"swarm_session_{context_id}.json"
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)
                return {
                    'agent': session_data.get('current_agent', 'unknown'),
                    'context_id': context_id,
                    'session_start': session_data.get('session_start'),
                    'domain': session_data.get('domain', 'unknown')
                }

            # Fallback: read user preferences
            prefs_file = self.maia_root / "claude" / "data" / "user_preferences.json"
            if prefs_file.exists():
                with open(prefs_file) as f:
                    prefs = json.load(f)
                return {
                    'agent': prefs.get('default_agent', 'sre_principal_engineer_agent'),
                    'context_id': context_id,
                    'session_start': None,
                    'domain': 'sre'
                }

            return {
                'agent': 'sre_principal_engineer_agent',
                'context_id': context_id,
                'session_start': None,
                'domain': 'sre'
            }

        except Exception:
            return {
                'agent': 'unknown',
                'context_id': 'unknown',
                'session_start': None,
                'domain': 'unknown'
            }

    def prompt_user_info(self, state: ProjectState, args: argparse.Namespace) -> ProjectState:
        """Prompt user for checkpoint metadata."""

        if args.auto:
            # Auto-detect phase from recent commits
            state.phase_number = self._detect_phase_number()
            state.phase_name = "Auto-checkpoint"
            state.percent_complete = 50  # Default to mid-project
            state.tdd_phase = "P4"  # Default to implementation
            return state

        # Interactive prompts
        if args.phase:
            # Parse phase from argument
            match = re.match(r'(?:Phase\s+)?(\d+)(?:\s+(.+))?', args.phase, re.IGNORECASE)
            if match:
                state.phase_number = int(match.group(1))
                state.phase_name = match.group(2) or "Unknown"
        else:
            phase_input = input("Phase number (e.g., 260): ").strip()
            state.phase_number = int(phase_input) if phase_input.isdigit() else None

            phase_name = input("Phase name (e.g., 'Timeline Persistence'): ").strip()
            state.phase_name = phase_name or "Unknown"

        percent_input = input("Percent complete (0-100): ").strip()
        state.percent_complete = int(percent_input) if percent_input.isdigit() else 50

        tdd_phase = input("TDD Phase (P0-P6.5, default P4): ").strip() or "P4"
        state.tdd_phase = tdd_phase

        return state

    def _detect_phase_number(self) -> Optional[int]:
        """Try to detect phase number from recent commits."""
        try:
            commits = self._run_git(["log", "-5", "--oneline"])
            # Look for "Phase NNN" in commits
            match = re.search(r'Phase\s+(\d+)', commits, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None

    def generate_checkpoint(self, state: ProjectState) -> str:
        """Generate checkpoint markdown content."""

        # Find next checkpoint number
        checkpoint_num = self._get_next_checkpoint_number(state.phase_number)

        # Calculate status description
        status_desc = self._generate_status_description(state)

        # Generate sections
        completed = self._generate_completed_section(state)
        next_steps = self._generate_next_steps(state)
        files = self._generate_files_section(state)
        resume = self._generate_resume_section(state)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        template = f"""# Phase {state.phase_number}: {state.phase_name} - Checkpoint {checkpoint_num}

**Date**: {timestamp}
**Status**: {status_desc} ({state.percent_complete}% done)
**Tests Passing**: {state.tests_passing}/{state.tests_total}
**Agent**: {state.current_agent}
**TDD Phase**: {state.tdd_phase or 'Unknown'}
**Context ID**: {state.context_id}

---

## Completed Components

{completed}

---

## Next Steps (Remaining {100 - (state.percent_complete or 50)}%)

{next_steps}

---

## Files Modified/Created

{files}

---

## Test Coverage

```
{state.test_details}
```

**Total**: {state.tests_passing}/{state.tests_total} tests passing

---

## Resume Instructions ⚠️ CRITICAL FOR POST-COMPACTION

### Step 1: Restore Agent (MANDATORY for code projects)
```bash
# Ensure {state.recommended_agent} loads (prevents terrible code from generic agent)
/init {state.recommended_agent.replace('_agent', '').replace('_principal_engineer', '').replace('_', ' ')}
```

**Why**: After compaction, agent session may not persist. Without proper agent, code quality degrades significantly.

### Step 2: Load Checkpoint Context
```bash
# Read this file
cat /tmp/CHECKPOINT_PHASE_{state.phase_number}_{checkpoint_num}.md

# Verify git state matches checkpoint
git status
```

### Step 3: Verify Environment
```bash
# Run tests to confirm state
pytest tests/ -v --tb=short

# Expected: {state.tests_passing}/{state.tests_total} passing (same as checkpoint)
```

### Step 4: Continue from Exact Point
**Current Branch**: {state.current_branch}
**Last Commit**: {state.last_commit}

**Next Action**: {self._suggest_next_action(state)}

### Step 5: Update Checkpoint When Phase Complete
```bash
# After completing next component
/checkpoint  # Generates CHECKPOINT_PHASE_{state.phase_number}_{checkpoint_num + 1}.md
```

---

## Git State at Checkpoint

```
{self._format_git_status(state)}
```

**Branch**: {state.current_branch}
**Last Commit**: {state.last_commit}

---

## Context Metadata

| Property | Value |
|----------|-------|
| Context ID | {state.context_id} |
| Session Start | {state.session_start or 'N/A'} |
| Agent | {state.current_agent} |
| Domain | {state.domain} |
| TDD Phase | {state.tdd_phase or 'Unknown'} |
| Checkpoint Time | {timestamp} |
| Project Type | {'Code (requires SRE agent)' if state.is_code_project else 'Docs'} |

---

## Compaction Safety Checklist

- ✅ This checkpoint file saved to `/tmp/`
- {'✅' if state.staged_files else '⚠️'} Git changes {'staged' if state.staged_files else 'documented as WIP'}
- ✅ Tests in known state ({state.tests_passing}/{state.tests_total})
- ✅ Resume instructions include `/init` for agent restoration
- {'✅' if state.is_code_project else 'N/A'} SRE agent restoration for code project

---

## Auto-Recovery Protocol

If compaction happens unexpectedly:

1. **Check for checkpoint**: `ls -lt /tmp/CHECKPOINT_* | head -1`
2. **Restore agent**: `/init {state.recommended_agent.replace('_agent', '').replace('_principal_engineer', '').replace('_', ' ')}` (for code projects)
3. **Read checkpoint**: Review completed/next sections
4. **Verify state**: `git status` + `pytest` should match checkpoint
5. **Resume**: Execute "Next Action" from resume instructions
"""

        return template

    def _get_next_checkpoint_number(self, phase_number: Optional[int]) -> int:
        """Find next available checkpoint number for this phase."""
        if not phase_number:
            return 1

        existing = list(self.checkpoint_dir.glob(f"CHECKPOINT_PHASE_{phase_number}_*.md"))
        if not existing:
            return 1

        # Extract checkpoint numbers
        numbers = []
        for f in existing:
            match = re.search(r'CHECKPOINT_PHASE_\d+_(\d+)\.md', f.name)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    def _generate_status_description(self, state: ProjectState) -> str:
        """Generate human-readable status description."""
        if state.tests_total == 0:
            return "Implementation in progress"
        elif state.tests_passing == state.tests_total:
            return f"All tests passing ({state.tests_total}/{state.tests_total})"
        else:
            return f"Tests: {state.tests_passing}/{state.tests_total} passing"

    def _generate_completed_section(self, state: ProjectState) -> str:
        """Generate completed components section."""
        # Auto-detect from staged files
        if state.staged_files:
            components = []
            for f in state.staged_files:
                if f.endswith('.py'):
                    components.append(f"✅ Implemented `{f}`")
                elif f.endswith('.md'):
                    components.append(f"✅ Documented `{f}`")

            if components:
                return "\n".join(f"- {c}" for c in components)

        return "_(User should fill in completed components)_"

    def _generate_next_steps(self, state: ProjectState) -> str:
        """Generate next steps section."""
        # Auto-detect from modified files
        if state.modified_files:
            steps = []
            for f in state.modified_files[:5]:  # Top 5
                steps.append(f"- Complete work on `{f}`")
            return "\n".join(steps)

        return "_(User should fill in next steps)_"

    def _generate_files_section(self, state: ProjectState) -> str:
        """Generate files modified/created section."""
        sections = []

        if state.modified_files:
            sections.append(f"**Modified** ({len(state.modified_files)} files):")
            for f in state.modified_files[:10]:  # Top 10
                sections.append(f"- {f}")
            if len(state.modified_files) > 10:
                sections.append(f"- ... and {len(state.modified_files) - 10} more")

        if state.new_files:
            sections.append(f"\n**Created** ({len(state.new_files)} files):")
            for f in state.new_files[:10]:
                sections.append(f"- {f}")
            if len(state.new_files) > 10:
                sections.append(f"- ... and {len(state.new_files) - 10} more")

        if state.deleted_files:
            sections.append(f"\n**Deleted** ({len(state.deleted_files)} files):")
            for f in state.deleted_files[:10]:
                sections.append(f"- {f}")

        if state.staged_files:
            sections.append(f"\n**Staged** ({len(state.staged_files)} files):")
            for f in state.staged_files[:10]:
                sections.append(f"- {f}")
            if len(state.staged_files) > 10:
                sections.append(f"- ... and {len(state.staged_files) - 10} more")

        return "\n".join(sections) if sections else "No files modified"

    def _format_git_status(self, state: ProjectState) -> str:
        """Format git status output."""
        lines = []

        if state.staged_files:
            lines.append("Staged changes:")
            for f in state.staged_files[:10]:
                lines.append(f"  M {f}")

        if state.modified_files:
            lines.append("\nUnstaged changes:")
            for f in state.modified_files[:10]:
                lines.append(f"  M {f}")

        if state.new_files:
            lines.append("\nNew files:")
            for f in state.new_files[:10]:
                lines.append(f"  A {f}")

        return "\n".join(lines) if lines else "Working tree clean"

    def _suggest_next_action(self, state: ProjectState) -> str:
        """Suggest specific next action based on state."""
        if state.tests_total == 0:
            return "Write tests for current implementation (TDD P3)"
        elif state.tests_passing < state.tests_total:
            return f"Fix {state.tests_total - state.tests_passing} failing tests"
        elif state.modified_files and not state.staged_files:
            return "Stage completed work: git add <files>"
        else:
            return "Continue implementation (see Next Steps section)"

    def _generate_resume_section(self, state: ProjectState) -> str:
        """Generate resume instructions."""
        # This is already in the template
        return ""

    def save_checkpoint(self, content: str, state: ProjectState) -> Path:
        """Save checkpoint file and return path."""
        checkpoint_num = self._get_next_checkpoint_number(state.phase_number)
        filename = f"CHECKPOINT_PHASE_{state.phase_number}_{checkpoint_num}.md"
        filepath = self.checkpoint_dir / filename

        filepath.write_text(content)

        # Also save durable checkpoint for compaction survival
        try:
            self.save_durable_checkpoint(state, content)
        except Exception as e:
            # Non-blocking - log error but don't fail
            print(f"Warning: Durable checkpoint save failed: {e}")

        return filepath

    def save_durable_checkpoint(
        self,
        state: ProjectState,
        markdown_content: Optional[str] = None
    ) -> Optional[Path]:
        """
        Save checkpoint to durable storage for compaction survival.

        Saves both JSON (machine-readable) and markdown (human-readable) formats
        to ~/.maia/checkpoints/{context_id}/.

        Phase 264: Auto-resume system - durable checkpoints that survive
        /tmp cleanup and enable automatic restoration after compaction.

        Args:
            state: Current project state
            markdown_content: Optional pre-generated markdown content

        Returns:
            Path to the JSON checkpoint file, or None on failure
        """
        try:
            # Create context-specific checkpoint directory
            context_dir = DURABLE_CHECKPOINT_DIR / state.context_id
            context_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"checkpoint_{timestamp}.json"
            md_filename = f"checkpoint_{timestamp}.md"

            json_path = context_dir / json_filename
            md_path = context_dir / md_filename

            # Save JSON format (machine-readable for auto-restore)
            json_data = state.to_json_dict()

            # Atomic write: temp file + rename
            json_tmp = json_path.with_suffix('.tmp')
            with open(json_tmp, 'w') as f:
                json.dump(json_data, f, indent=2)
            json_tmp.rename(json_path)

            # Save markdown format (human-readable)
            if markdown_content:
                md_tmp = md_path.with_suffix('.tmp')
                with open(md_tmp, 'w') as f:
                    f.write(markdown_content)
                md_tmp.rename(md_path)

            # Cleanup old checkpoints (keep last 5 per context)
            self._cleanup_old_durable_checkpoints(context_dir, keep=5)

            return json_path

        except Exception as e:
            # Non-blocking - log error but don't fail
            try:
                log_dir = Path.home() / ".maia" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                with open(log_dir / "checkpoint_errors.log", 'a') as f:
                    f.write(f"{datetime.now().isoformat()} [ERROR] Durable checkpoint failed: {e}\n")
            except Exception:
                pass
            return None

    def _cleanup_old_durable_checkpoints(self, context_dir: Path, keep: int = 5):
        """
        Remove old checkpoints, keeping only the most recent N.

        Args:
            context_dir: Directory containing checkpoints for a context
            keep: Number of recent checkpoints to keep
        """
        try:
            json_files = sorted(
                context_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Delete older checkpoints
            for old_file in json_files[keep:]:
                try:
                    old_file.unlink()
                    # Also delete corresponding markdown if exists
                    md_file = old_file.with_suffix('.md')
                    if md_file.exists():
                        md_file.unlink()
                except Exception:
                    pass  # Non-blocking

        except Exception:
            pass  # Non-blocking


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate compaction-ready checkpoint documentation"
    )
    parser.add_argument(
        "--phase",
        help="Phase description (e.g., 'Phase 260 Timeline Persistence')"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect all information (no prompts)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🔍 CHECKPOINT GENERATOR")
    print("=" * 60)
    print()

    generator = CheckpointGenerator()

    # Gather state
    print("📋 Gathering project state...")
    state = generator.gather_state()

    print(f"   Modified files: {len(state.modified_files)}")
    print(f"   Staged files: {len(state.staged_files)}")
    print(f"   Tests: {state.tests_passing}/{state.tests_total}")
    print(f"   Agent: {state.current_agent}")
    print(f"   Project type: {'Code' if state.is_code_project else 'Docs'}")
    print()

    # Get user input
    if not args.auto:
        print("📝 Checkpoint metadata (press Enter to skip)...")
    state = generator.prompt_user_info(state, args)
    print()

    # Generate checkpoint
    print("🔨 Generating checkpoint document...")
    content = generator.generate_checkpoint(state)

    # Save checkpoint
    print("💾 Saving checkpoint...")
    filepath = generator.save_checkpoint(content, state)

    print()
    print("=" * 60)
    print("✅ CHECKPOINT SAVED")
    print("=" * 60)
    print(f"📄 File: {filepath}")
    print()
    print("🔄 Resume after compaction:")
    print(f"   cat {filepath}")
    if state.is_code_project:
        agent_name = state.recommended_agent.replace('_agent', '').replace('_principal_engineer', '').replace('_', ' ')
        print(f"   /init {agent_name}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
