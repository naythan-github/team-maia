#!/usr/bin/env python3
"""
Save State - Enforced Documentation Protocol

Phase 233: Automated save_state with blocking enforcement
Phase 233.1: Comprehensive documentation verification
Phase 233.2: Auto-sync both capabilities.db and system_state.db

Ensures all documentation is updated before commits:
1. Auto-detect what changed (new tools, agents, commands)
2. Block commit if required docs not updated
3. Sync capabilities.db on every save
4. Sync system_state.db when SYSTEM_STATE.md modified
5. Require SYSTEM_STATE.md for significant work
6. Verify capability counts match actual files
7. Check CLAUDE.md if protocols/hooks changed
8. Validate cross-references exist

Usage:
    python3 claude/tools/sre/save_state.py              # Interactive mode
    python3 claude/tools/sre/save_state.py --check      # Check only, no commit
    python3 claude/tools/sre/save_state.py --force      # Skip blocks (emergency only)
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re

from claude.tools.core.paths import get_maia_root


@dataclass
class ChangeAnalysis:
    """Analysis of what changed in this session."""
    new_tools: List[str]
    new_agents: List[str]
    new_commands: List[str]
    modified_files: List[str]
    deleted_files: List[str]

    # Documentation status
    capability_index_modified: bool
    agents_md_modified: bool
    system_state_modified: bool
    claude_md_modified: bool

    @property
    def needs_capability_index(self) -> bool:
        """True if new tools/agents require capability_index update."""
        return bool(self.new_tools or self.new_agents)

    @property
    def needs_agents_md(self) -> bool:
        """True if new agents require agents.md update."""
        return bool(self.new_agents)

    @property
    def needs_system_state(self) -> bool:
        """True if significant work requires SYSTEM_STATE.md update."""
        # Significant = new tools, new agents, or > 5 modified files
        return bool(self.new_tools or self.new_agents or len(self.modified_files) > 5)

    @property
    def is_significant(self) -> bool:
        """True if this is significant work (not just minor edits)."""
        return (
            bool(self.new_tools) or
            bool(self.new_agents) or
            bool(self.new_commands) or
            len(self.modified_files) > 3
        )


class SaveState:
    """
    Enforced save state protocol.

    Blocks commits when required documentation is missing.
    Auto-syncs both capabilities.db and system_state.db.
    """

    def __init__(self, maia_root: Optional[Path] = None):
        self.maia_root = maia_root or get_maia_root()
        self.tools_dir = self.maia_root / "claude" / "tools"
        self.agents_dir = self.maia_root / "claude" / "agents"
        self.commands_dir = self.maia_root / "claude" / "commands"

    def analyze_changes(self) -> ChangeAnalysis:
        """
        Analyze git changes to determine what documentation is needed.

        Uses git diff --name-status to detect:
        - New files (A)
        - Modified files (M)
        - Deleted files (D)
        """
        # Get staged and unstaged changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.maia_root,
            capture_output=True,
            text=True
        )

        new_tools = []
        new_agents = []
        new_commands = []
        modified_files = []
        deleted_files = []

        capability_index_modified = False
        agents_md_modified = False
        system_state_modified = False
        claude_md_modified = False

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            status = line[:2].strip()
            filepath = line[3:].strip()

            # Handle renamed files (R status shows old -> new)
            if ' -> ' in filepath:
                filepath = filepath.split(' -> ')[1]

            # Categorize changes
            if status in ('A', '?'):  # Added or untracked
                if filepath.startswith('claude/tools/') and filepath.endswith('.py'):
                    # Exclude __pycache__ and test files
                    if '__pycache__' not in filepath and not filepath.startswith('tests/'):
                        new_tools.append(filepath)
                elif filepath.startswith('claude/agents/') and filepath.endswith('.md'):
                    new_agents.append(filepath)
                elif filepath.startswith('claude/commands/') and filepath.endswith('.md'):
                    new_commands.append(filepath)

            if status in ('M', 'A', '?'):  # Modified or added
                modified_files.append(filepath)

                # Check doc files
                if 'capability_index.md' in filepath:
                    capability_index_modified = True
                if filepath == 'claude/context/core/agents.md':
                    agents_md_modified = True
                if filepath == 'SYSTEM_STATE.md':
                    system_state_modified = True
                if filepath == 'CLAUDE.md':
                    claude_md_modified = True

            if status == 'D':
                deleted_files.append(filepath)

        return ChangeAnalysis(
            new_tools=new_tools,
            new_agents=new_agents,
            new_commands=new_commands,
            modified_files=modified_files,
            deleted_files=deleted_files,
            capability_index_modified=capability_index_modified,
            agents_md_modified=agents_md_modified,
            system_state_modified=system_state_modified,
            claude_md_modified=claude_md_modified
        )

    def check_documentation(self, analysis: ChangeAnalysis) -> Tuple[bool, List[str]]:
        """
        Check if required documentation has been updated.

        Returns:
            (passes, list of blocking issues)
        """
        issues = []

        # Check capability_index.md
        if analysis.needs_capability_index and not analysis.capability_index_modified:
            issues.append(
                f"❌ NEW TOOLS/AGENTS DETECTED but capability_index.md not updated:\n"
                f"   Tools: {', '.join(analysis.new_tools[:5])}\n"
                f"   Agents: {', '.join(analysis.new_agents[:5])}\n"
                f"   → Add entries to claude/context/core/capability_index.md"
            )

        # Check agents.md
        if analysis.needs_agents_md and not analysis.agents_md_modified:
            issues.append(
                f"❌ NEW AGENTS DETECTED but agents.md not updated:\n"
                f"   {', '.join(analysis.new_agents[:5])}\n"
                f"   → Add entries to claude/context/core/agents.md"
            )

        # Check SYSTEM_STATE.md
        if analysis.needs_system_state and not analysis.system_state_modified:
            issues.append(
                f"❌ SIGNIFICANT WORK DETECTED but SYSTEM_STATE.md not updated:\n"
                f"   New tools: {len(analysis.new_tools)}\n"
                f"   New agents: {len(analysis.new_agents)}\n"
                f"   Modified files: {len(analysis.modified_files)}\n"
                f"   → Add phase entry to SYSTEM_STATE.md"
            )

        return (len(issues) == 0, issues)

    def verify_capability_counts(self) -> Tuple[bool, List[str]]:
        """
        Verify capability_index.md counts match actual files.

        Returns:
            (passes, list of warnings)
        """
        warnings = []

        # Count actual tools
        actual_tools = 0
        for tools_subdir in self.tools_dir.iterdir():
            if tools_subdir.is_dir() and not tools_subdir.name.startswith('.'):
                actual_tools += len(list(tools_subdir.glob('*.py')))
            elif tools_subdir.suffix == '.py':
                actual_tools += 1

        # Count actual agents
        actual_agents = len(list(self.agents_dir.glob('*.md')))

        # Read capability_index.md for claimed counts
        cap_index = self.maia_root / "claude" / "context" / "core" / "capability_index.md"
        if cap_index.exists():
            content = cap_index.read_text()

            # Extract claimed counts (e.g., "501 tools, 94 agents")
            import re
            match = re.search(r'\*\*Total\*\*:\s*(\d+)\s*tools,\s*(\d+)\s*agents', content)
            if match:
                claimed_tools = int(match.group(1))
                claimed_agents = int(match.group(2))

                # Allow 10% variance (some tools may be in subdirs, etc.)
                tool_diff = abs(actual_tools - claimed_tools)
                agent_diff = abs(actual_agents - claimed_agents)

                if tool_diff > claimed_tools * 0.1:
                    warnings.append(
                        f"⚠️ TOOL COUNT MISMATCH:\n"
                        f"   capability_index.md claims: {claimed_tools} tools\n"
                        f"   Actual files found: {actual_tools} tools\n"
                        f"   → Update capability_index.md header"
                    )

                if agent_diff > claimed_agents * 0.1:
                    warnings.append(
                        f"⚠️ AGENT COUNT MISMATCH:\n"
                        f"   capability_index.md claims: {claimed_agents} agents\n"
                        f"   Actual files found: {actual_agents} agents\n"
                        f"   → Update capability_index.md header"
                    )

        return (len(warnings) == 0, warnings)

    def check_protocol_changes(self, analysis: ChangeAnalysis) -> Tuple[bool, List[str]]:
        """
        Check if protocol/hook changes require CLAUDE.md update.

        Returns:
            (passes, list of warnings)
        """
        warnings = []

        # Files that affect CLAUDE.md working principles
        protocol_files = [
            'claude/hooks/',
            'claude/commands/',
            'claude/context/core/',
            '.claude/commands/',
        ]

        protocol_changed = any(
            any(f.startswith(prefix) for prefix in protocol_files)
            for f in analysis.modified_files
        )

        # If protocol files changed but CLAUDE.md not updated, warn
        if protocol_changed and not analysis.claude_md_modified:
            changed_protocols = [
                f for f in analysis.modified_files
                if any(f.startswith(prefix) for prefix in protocol_files)
            ]
            warnings.append(
                f"⚠️ PROTOCOL FILES CHANGED but CLAUDE.md not updated:\n"
                f"   Changed: {', '.join(changed_protocols[:3])}{'...' if len(changed_protocols) > 3 else ''}\n"
                f"   → Review if CLAUDE.md working principles need updating"
            )

        return (len(warnings) == 0, warnings)

    def verify_documentation_completeness(self, analysis: ChangeAnalysis) -> Tuple[bool, List[str]]:
        """
        Verify all significant changes are documented somewhere.

        Returns:
            (passes, list of issues)
        """
        issues = []

        # Check if any new files are not in capability_index
        if analysis.new_tools:
            cap_index = self.maia_root / "claude" / "context" / "core" / "capability_index.md"
            if cap_index.exists():
                content = cap_index.read_text()
                undocumented = []
                for tool in analysis.new_tools:
                    tool_name = Path(tool).stem
                    if tool_name not in content and f'`{tool_name}`' not in content:
                        undocumented.append(tool)

                if undocumented and analysis.capability_index_modified:
                    # Modified but still missing entries
                    issues.append(
                        f"⚠️ NEW TOOLS NOT IN capability_index.md:\n"
                        f"   {', '.join(undocumented[:5])}\n"
                        f"   → Add entries for these tools"
                    )

        return (len(issues) == 0, issues)

    def sync_capabilities_db(self) -> Tuple[bool, str]:
        """
        Sync capabilities.db with current tools/agents.

        Returns:
            (success, message)
        """
        registry_path = self.maia_root / "claude" / "tools" / "sre" / "capabilities_registry.py"

        if not registry_path.exists():
            return False, "capabilities_registry.py not found"

        try:
            result = subprocess.run(
                ["python3", str(registry_path), "scan"],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Extract counts from output
                output = result.stdout
                return True, f"✅ Capabilities DB synced\n{output.strip()}"
            else:
                return False, f"⚠️ Capabilities sync warning: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "⚠️ Capabilities sync timed out"
        except Exception as e:
            return False, f"⚠️ Capabilities sync error: {e}"

    def sync_system_state_db(self) -> Tuple[bool, str]:
        """
        Sync system_state.db with SYSTEM_STATE.md.

        Runs system_state_etl.py to extract, transform, and load phase data
        from markdown into SQLite database.

        Returns:
            (success, message)
        """
        etl_path = self.maia_root / "claude" / "tools" / "sre" / "system_state_etl.py"

        if not etl_path.exists():
            return False, "system_state_etl.py not found"

        try:
            result = subprocess.run(
                ["python3", str(etl_path)],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=60  # ETL can be slower than capabilities scan
            )

            if result.returncode == 0:
                # Extract phase count from output
                output = result.stdout
                return True, f"✅ System State DB synced\n{output.strip()}"
            else:
                return False, f"⚠️ System State sync warning: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "⚠️ System State sync timed out"
        except Exception as e:
            return False, f"⚠️ System State sync error: {e}"

    def run_security_check(self) -> Tuple[bool, str]:
        """
        Run security check for secrets in staged files.

        Returns:
            (passes, message)
        """
        checker_path = self.maia_root / "claude" / "tools" / "sre" / "save_state_security_checker.py"

        if not checker_path.exists():
            return True, "⚠️ Security checker not found (skipped)"

        try:
            result = subprocess.run(
                ["python3", str(checker_path), "--verbose"],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, "✅ Security check passed"
            else:
                return False, f"❌ Security check failed:\n{result.stdout}\n{result.stderr}"

        except Exception as e:
            return True, f"⚠️ Security check error (continuing): {e}"

    def commit_changes(self, message: str) -> Tuple[bool, str]:
        """
        Stage all changes and commit.

        Returns:
            (success, message)
        """
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.maia_root,
                check=True
            )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.maia_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return True, f"✅ Committed: {result.stdout.strip().split(chr(10))[0]}"
            else:
                if "nothing to commit" in result.stdout:
                    return True, "ℹ️ Nothing to commit"
                return False, f"❌ Commit failed: {result.stderr}"

        except Exception as e:
            return False, f"❌ Commit error: {e}"

    def push_changes(self) -> Tuple[bool, str]:
        """
        Push to remote.

        Returns:
            (success, message)
        """
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.maia_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, "✅ Pushed to remote"
            else:
                return False, f"❌ Push failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "❌ Push timed out"
        except Exception as e:
            return False, f"❌ Push error: {e}"

    def run(self, check_only: bool = False, force: bool = False) -> int:
        """
        Run the save state protocol.

        Args:
            check_only: Only check, don't commit
            force: Skip blocking checks (emergency only)

        Returns:
            0 on success, 1 on failure
        """
        print("=" * 60)
        print("🔍 SAVE STATE - Documentation Enforcement")
        print("=" * 60)
        print()

        # 1. Analyze changes
        print("📋 Analyzing changes...")
        analysis = self.analyze_changes()

        print(f"   New tools: {len(analysis.new_tools)}")
        print(f"   New agents: {len(analysis.new_agents)}")
        print(f"   New commands: {len(analysis.new_commands)}")
        print(f"   Modified files: {len(analysis.modified_files)}")
        print()

        if not analysis.modified_files and not analysis.new_tools and not analysis.new_agents:
            print("ℹ️ No changes to save")
            return 0

        # 2. Check documentation
        print("📝 Checking documentation updates...")
        passes, issues = self.check_documentation(analysis)

        if not passes:
            print()
            for issue in issues:
                print(issue)
                print()

            if not force:
                print("=" * 60)
                print("🚫 BLOCKED: Update documentation before committing")
                print("   Use --force to bypass (NOT RECOMMENDED)")
                print("=" * 60)
                return 1
            else:
                print("⚠️ FORCE MODE: Bypassing documentation checks")
                print()
        else:
            print("   ✅ All required documentation updated")
            print()

        # 2b. Comprehensive verification (warnings, non-blocking)
        print("🔍 Running comprehensive verification...")
        all_warnings = []

        # Capability count verification
        count_ok, count_warnings = self.verify_capability_counts()
        all_warnings.extend(count_warnings)

        # Protocol changes check
        protocol_ok, protocol_warnings = self.check_protocol_changes(analysis)
        all_warnings.extend(protocol_warnings)

        # Documentation completeness
        doc_ok, doc_warnings = self.verify_documentation_completeness(analysis)
        all_warnings.extend(doc_warnings)

        if all_warnings:
            print()
            for warning in all_warnings:
                print(warning)
                print()
            print("   ⚠️ Review warnings above (non-blocking)")
        else:
            print("   ✅ All verifications passed")
        print()

        if check_only:
            print("ℹ️ Check only mode - not committing")
            return 0

        # 3. Sync capabilities DB
        print("🔄 Syncing capabilities database...")
        sync_ok, sync_msg = self.sync_capabilities_db()
        print(f"   {sync_msg}")
        print()

        # 3b. Sync system state DB (if SYSTEM_STATE.md modified)
        if analysis.system_state_modified:
            print("🔄 Syncing system state database...")
            state_sync_ok, state_sync_msg = self.sync_system_state_db()
            print(f"   {state_sync_msg}")
            print()

        # 4. Security check
        print("🔒 Running security check...")
        sec_ok, sec_msg = self.run_security_check()
        print(f"   {sec_msg}")

        if not sec_ok and not force:
            print("🚫 BLOCKED: Fix security issues before committing")
            return 1
        print()

        # 5. Generate commit message
        commit_msg = self._generate_commit_message(analysis)
        print("📝 Commit message:")
        print("-" * 40)
        print(commit_msg[:500] + "..." if len(commit_msg) > 500 else commit_msg)
        print("-" * 40)
        print()

        # 6. Commit
        print("💾 Committing changes...")
        commit_ok, commit_msg_result = self.commit_changes(commit_msg)
        print(f"   {commit_msg_result}")

        if not commit_ok:
            return 1
        print()

        # 7. Push
        print("🚀 Pushing to remote...")
        push_ok, push_msg = self.push_changes()
        print(f"   {push_msg}")

        if not push_ok:
            print("⚠️ Commit succeeded but push failed - push manually")
            return 1

        print()
        print("=" * 60)
        print("✅ SAVE STATE COMPLETE")
        print("=" * 60)

        return 0

    def _generate_commit_message(self, analysis: ChangeAnalysis) -> str:
        """Generate structured commit message."""
        # Determine type
        if analysis.new_tools or analysis.new_agents:
            prefix = "feat"
            emoji = "✨"
        elif any('fix' in f.lower() for f in analysis.modified_files):
            prefix = "fix"
            emoji = "🐛"
        else:
            prefix = "docs"
            emoji = "📝"

        # Build summary
        parts = []
        if analysis.new_tools:
            parts.append(f"{len(analysis.new_tools)} new tools")
        if analysis.new_agents:
            parts.append(f"{len(analysis.new_agents)} new agents")
        if analysis.new_commands:
            parts.append(f"{len(analysis.new_commands)} new commands")

        summary = ", ".join(parts) if parts else f"{len(analysis.modified_files)} files updated"

        # Build body
        body_parts = []
        if analysis.new_tools:
            body_parts.append("## New Tools")
            for tool in analysis.new_tools[:10]:
                body_parts.append(f"- {tool}")
            if len(analysis.new_tools) > 10:
                body_parts.append(f"- ... and {len(analysis.new_tools) - 10} more")

        if analysis.new_agents:
            body_parts.append("\n## New Agents")
            for agent in analysis.new_agents[:5]:
                body_parts.append(f"- {agent}")

        body = "\n".join(body_parts) if body_parts else ""

        message = f"""{emoji} {prefix}: {summary}

{body}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        return message.strip()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Save State - Enforced Documentation Protocol")
    parser.add_argument("--check", action="store_true", help="Check only, don't commit")
    parser.add_argument("--force", action="store_true", help="Bypass blocks (emergency only)")

    args = parser.parse_args()

    save_state = SaveState()
    return save_state.run(check_only=args.check, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
