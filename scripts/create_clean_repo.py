#!/usr/bin/env python3
"""
Maia Fresh Repository Creator - Phase 218

Creates a clean, team-shareable copy of Maia with:
- All secrets/credentials removed
- Personal data excluded
- Broken directories cleaned
- Templates created for personal configs
- Governance files added

Usage:
    python3 scripts/create_clean_repo.py [--dry-run] [--output-dir /path/to/output]

Author: Maia System
Created: 2024-12-04
"""

import os
import sys
import shutil
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Set, List, Tuple

# ============================================================================
# EXCLUSION RULES
# ============================================================================

# Directories to completely exclude (won't be copied at all)
EXCLUDE_DIRS: Set[str] = {
    # Broken directories (variable expansion failures)
    "${MAIA_ROOT}",
    "get_path_manager().get_path('backup') ",
    "claude/claude",  # Nested duplicate

    # Root-level duplicates (empty or should be consolidated)
    "data",  # Empty at root

    # Personal databases (EXCEPT whitelisted core architecture DBs)
    # Note: claude/data/databases is NOT excluded - we use file-level filtering instead
    "claude/data/rag_databases",  # All RAG DBs excluded (personal embeddings)

    # Personal context
    "claude/context/personal",
    "claude/context/💼_professional",

    # Team/org specific data
    "claude/context/knowledge/team_intelligence",

    # Cache and temp
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".eggs",
    "*.egg-info",
}

# ============================================================================
# CORE ARCHITECTURE DATABASES TO INCLUDE
# ============================================================================
# These databases are part of Maia's core architecture and provide value to team:
# - system_state.db: 108 phases of development history (searchable context)
# - capabilities.db: 567 tools/agents indexed (enables discovery)

INCLUDE_DATABASE_FILES: Set[str] = {
    "claude/data/databases/system/system_state.db",
    "claude/data/databases/system/capabilities.db",
}

# Database files to EXCLUDE (personal/project data)
EXCLUDE_DATABASE_FILES: Set[str] = {
    # User databases (all personal)
    "autonomous_alerts_naythan.db",
    "background_learning_naythan.db",
    "calendar_optimizer_naythan.db",
    "context_preparation_naythan.db",
    "contextual_memory_naythan.db",
    "continuous_monitoring_naythan.db",
    "personal_knowledge_graph.db",
    "production_deployment_naythan.db",
    "teams_meetings.db",

    # Intelligence databases (personal data)
    "adaptive_routing.db",
    "eia_intelligence.db",
    "email_actions.db",
    "outcome_tracker.db",
    "predictive_models.db",
    "security_metrics.db",

    # System databases (personal/project specific)
    "conversations.db",
    "tool_discovery.db",
    "verification_hook.db",
    "orro_application_inventory.db",
    "orro_application_inventory_v2.db",
    "implementations.db",
    "research_cache.db",
    "anti_sprawl_progress.db",
    "dora_metrics.db",
    "self_improvement.db",
    "deduplication.db",
    "performance_metrics.db",
    "system_health.db",
    "dashboard_registry.db",

    # Root level databases
    "decision_intelligence.db",
    "executive_information.db",
    "servicedesk.db",
    "stakeholder_intelligence.db",
}

# Files to completely exclude
EXCLUDE_FILES: Set[str] = {
    # Personal data
    "profile.md",
    "orro_team_list.json",
    "team_analysis.json",

    # Secrets
    ".env",

    # State files (user-specific)
    "user_preferences.json",
    "capability_cache.json",
    "confluence_intelligence.json",
    "action_completion_metrics.json",
    "vtt_intelligence.json",
    "vtt_pipeline_state.json",
    "vtt_processed.json",
    "vtt_moved.json",
    "downloads_processed.json",
    "enhanced_daily_briefing.json",
    "daily_briefing_complete.json",
    "confluence_sync_cache.json",
    "llm_routing_log.jsonl",

    # OS files
    ".DS_Store",
    "Thumbs.db",

    # Local settings
    "settings.local.json",
    "hooks.local.json",

    # Restoration logs
    "maia_restoration.log",
}

# File patterns to exclude (glob-style)
EXCLUDE_PATTERNS: List[str] = [
    "*.db",
    "*.sqlite3",
    "*.db-shm",
    "*.db-wal",
    "*.pyc",
    "*.pyo",
    "*_naythan*.db",
    "contextual_memory_*.db",
]

# Files that need password sanitization
FILES_WITH_PASSWORDS: Set[str] = {
    "servicedesk_sentiment_analyzer_postgres.py",
    "servicedesk_quality_analyzer_postgres.py",
    "DASHBOARD_7_IMPLEMENTATION_REPORT.md",
    "DASHBOARD_INSTALLATION_GUIDE.md",
    "migrate_sqlite_to_postgres.py",
    "PHASE_1_SAVED_STATE.md",
    "PHASE_1_INFRASTRUCTURE_COMPLETE.md",
    "PHASE_1_TEST_RESULTS.md",
    "DASHBOARD_6_FIX_REPORT.md",
    "DASHBOARD_STATUS.md",
    "DASHBOARD_FIX_REPORT.md",
}

# Password patterns to sanitize
PASSWORD_PATTERNS: List[Tuple[str, str]] = [
    (r"ServiceDesk2025!SecurePass", "POSTGRES_PASSWORD_HERE"),
    (r"Grafana2025!SecureAdmin", "GRAFANA_PASSWORD_HERE"),
    (r"password['\"]?\s*[:=]\s*['\"]?ServiceDesk2025[^'\"]*['\"]?",
     "password: 'POSTGRES_PASSWORD_HERE'"),
]

# Hardcoded path patterns to fix
PATH_PATTERNS: List[Tuple[str, str]] = [
    (r"/Users/YOUR_USERNAME/git/maia", "${MAIA_ROOT}"),
    (r"/Users/YOUR_USERNAME", "${HOME}"),
    (r"/Users/naythan/git/maia", "${MAIA_ROOT}"),
]

# Email patterns to sanitize
EMAIL_PATTERNS: List[Tuple[str, str]] = [
    (r"naythan\.dawe@orro\.group", "your.email@company.com"),
    (r"naythan\.general@gmail\.com", "your.personal@email.com"),
    (r"nd25@londonxyz\.com", "your.email@domain.com"),
]

# ============================================================================
# TEMPLATE FILES TO CREATE
# ============================================================================

TEMPLATES = {
    "claude/data/user_preferences.json.template": """{
  "default_agent": "sre_principal_engineer_agent",
  "fallback_agent": "sre_principal_engineer_agent",
  "version": "1.0",
  "description": "User-specific preferences for Maia system behavior",
  "updated": "YYYY-MM-DDTHH:MM:SSZ"
}
""",

    "claude/context/personal/profile.md.template": """# Personal Profile

## Identity
- **Name**: YOUR_NAME
- **Role**: YOUR_ROLE
- **Email**: your.email@company.com

## Work Context
- **Company**: YOUR_COMPANY
- **Team**: YOUR_TEAM
- **Location**: YOUR_LOCATION

## Preferences
(Add your personal preferences here)

## Notes
(Any personal notes or context)
""",

    "claude/infrastructure/servicedesk-dashboard/.env.template": """# ServiceDesk Dashboard Environment Variables
# Copy this to .env and fill in your values

# PostgreSQL
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=servicedesk
POSTGRES_USER=servicedesk_user

# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password_here
GRAFANA_SECRET_KEY=generate_with_openssl_rand_base64_32

# Backup
BACKUP_SCHEDULE=0 2 * * *
""",

    "claude/data/local_services.json.template": """{
  "ollama": {
    "url": "http://localhost:11434",
    "embedding_model": "nomic-embed-text",
    "required": false,
    "setup_docs": "https://ollama.ai/download"
  },
  "dashboard": {
    "host": "127.0.0.1",
    "port": 8070
  }
}
""",
}

# ============================================================================
# GOVERNANCE FILES TO CREATE
# ============================================================================

GOVERNANCE_FILES = {
    ".github/CODEOWNERS": """# Maia CODEOWNERS - Defines code review requirements by zone

# ═══════════════════════════════════════════════════════════════
# 🟢 ZONE 1: Open Contribution (1 approval from any contributor)
# ═══════════════════════════════════════════════════════════════

# Project-specific tools
claude/tools/pmp/               @naythan-orro/maia-contributors
claude/tools/servicedesk/       @naythan-orro/maia-contributors
claude/tools/business/          @naythan-orro/maia-contributors
claude/tools/finance/           @naythan-orro/maia-contributors
claude/tools/integrations/      @naythan-orro/maia-contributors
claude/tools/experimental/      @naythan-orro/maia-contributors
claude/tools/communication/     @naythan-orro/maia-contributors
claude/tools/productivity/      @naythan-orro/maia-contributors
claude/tools/research/          @naythan-orro/maia-contributors

# Documentation
docs/                           @naythan-orro/maia-contributors
claude/documentation/           @naythan-orro/maia-contributors

# ═══════════════════════════════════════════════════════════════
# 🟡 ZONE 2: Guided Contribution (2 approvals from maintainers)
# ═══════════════════════════════════════════════════════════════

# Core utilities
claude/tools/core/              @naythan-orro/maia-maintainers
claude/tools/sre/               @naythan-orro/maia-maintainers
claude/tools/security/          @naythan-orro/maia-maintainers
claude/tools/monitoring/        @naythan-orro/maia-maintainers
claude/tools/orchestration/     @naythan-orro/maia-maintainers

# Test infrastructure
tests/                          @naythan-orro/maia-maintainers

# ═══════════════════════════════════════════════════════════════
# 🔴 ZONE 3: Architectural (RFC + Owner approval required)
# ═══════════════════════════════════════════════════════════════

# System behavior & identity
CLAUDE.md                       @YOUR_USERNAME
claude/context/core/            @YOUR_USERNAME
claude/context/ufc_system.md    @YOUR_USERNAME

# Enforcement & hooks
claude/hooks/                   @YOUR_USERNAME

# CI/CD & governance
.github/                        @YOUR_USERNAME

# RFCs
claude/rfcs/                    @YOUR_USERNAME
""",

    ".github/PULL_REQUEST_TEMPLATE.md": """## Summary
<!-- Brief description of changes -->

## Type of Change
- [ ] 🟢 Zone 1: New tool/integration/documentation
- [ ] 🟡 Zone 2: Core utility/test infrastructure change
- [ ] 🔴 Zone 3: Architectural change (requires RFC)

## Changes Made
<!-- List the key changes -->
-

## Testing
<!-- How was this tested? -->
- [ ] Tests pass locally (`pytest tests/`)
- [ ] Manual testing completed
- [ ] No new security issues introduced

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if applicable)
- [ ] No hardcoded paths or credentials
- [ ] No personal data included

## Related Issues
<!-- Link any related issues -->
Closes #

---
🤖 Generated with Maia
""",

    "CONTRIBUTING.md": """# Contributing to Maia

Welcome! This guide explains how to contribute to Maia.

## Contribution Zones

Maia uses a tiered contribution model to balance innovation with stability.

### 🟢 Zone 1: Open Contribution
**What**: New tools, integrations, custom agents, team commands, documentation
**Process**: Fork → Branch → PR → 1 team approval → Merge
**Time**: Usually same day

Great for:
- Adding a tool for your project
- Creating a custom agent
- Writing documentation
- Adding integrations

### 🟡 Zone 2: Guided Contribution
**What**: Changes to core tools, base agents, test infrastructure
**Process**: Fork → Branch → PR → 2 maintainer approvals → Merge
**Time**: 1-3 days

Great for:
- Improving existing tools
- Fixing bugs in core utilities
- Adding test coverage

### 🔴 Zone 3: Architectural Changes
**What**: System behavior, core protocols, hooks, CLAUDE.md
**Process**: RFC → Discussion (7 days) → Owner approval → Implementation PR
**Time**: 1-2 weeks

Required for:
- Changing how agents load/behave
- Modifying the UFC system
- Adding new enforcement hooks
- Changing CI/CD pipelines

**Note**: Don't be discouraged! RFCs ensure we think through changes carefully.
All ideas are welcome.

## Getting Started

1. Clone the repository:
   ```bash
   git clone git@github.com:naythan-orro/maia.git
   cd maia
   ```

2. Run setup:
   ```bash
   ./scripts/setup.sh
   ```

3. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

4. Make your changes and test:
   ```bash
   pytest tests/
   ```

5. Submit a PR

## Code Style

- Python: Follow PEP 8
- Use type hints where practical
- Write docstrings for public functions
- No hardcoded paths - use `path_manager.py`
- No credentials in code - use environment variables

## Testing

All changes should include tests where applicable:
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_file.py -v

# Run with coverage
pytest tests/ --cov=claude
```

## Questions?

Open an issue or ask in the team channel.
""",

    "LICENSE": """MIT License

Copyright (c) 2024 Orro Group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",

    "claude/rfcs/0000-template.md": """# RFC-NNNN: Title

## Status
Draft | Under Review | Accepted | Rejected | Implemented

## Author
@username

## Summary
One paragraph explaining the proposed change.

## Motivation
Why is this change needed? What problem does it solve?

## Detailed Design
How will this work? Include:
- Files changed
- Behavior changes
- Migration path

## Alternatives Considered
What other approaches were considered? Why were they rejected?

## Impact Assessment
- **Blast radius**: Which systems/users affected?
- **Risk level**: Low/Medium/High
- **Rollback plan**: How to undo if problems occur?

## Open Questions
What's still uncertain?

## Timeline
Proposed implementation timeline (optional).
""",

    ".github/workflows/test.yml": """name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ -v --tb=short

    - name: Check for secrets
      run: |
        # Basic secret detection
        ! grep -r "ServiceDesk2025\\|Grafana2025\\|password.*=" --include="*.py" --include="*.md" claude/ || exit 1
""",
}

SETUP_SCRIPT = """#!/bin/bash
# Maia Setup Script
# Run this after cloning to set up your personal environment

set -e

echo "🚀 Setting up Maia for $USER..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAIA_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$MAIA_ROOT"

# Create personal directories
echo "📁 Creating personal directories..."
mkdir -p claude/context/personal
mkdir -p claude/data/databases/{intelligence,system,user}
mkdir -p claude/data/rag_databases

# Copy templates
echo "📝 Creating personal config files from templates..."

if [ ! -f claude/data/user_preferences.json ]; then
    cp claude/data/user_preferences.json.template claude/data/user_preferences.json
    echo "   ✅ Created user_preferences.json"
fi

if [ ! -f claude/context/personal/profile.md ]; then
    cp claude/context/personal/profile.md.template claude/context/personal/profile.md
    echo "   ✅ Created personal profile.md"
fi

if [ -f claude/infrastructure/servicedesk-dashboard/.env.template ]; then
    if [ ! -f claude/infrastructure/servicedesk-dashboard/.env ]; then
        cp claude/infrastructure/servicedesk-dashboard/.env.template claude/infrastructure/servicedesk-dashboard/.env
        echo "   ✅ Created servicedesk .env (edit with your passwords)"
    fi
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt --quiet
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  No requirements.txt found"
fi

# Install git hooks for file organization enforcement
echo ""
echo "🔗 Installing git hooks..."
if [ -d .git/hooks ]; then
    # Pre-commit hook: File organization + TDD enforcement
    if [ -f claude/hooks/pre_commit_file_organization.py ]; then
        ln -sf ../../claude/hooks/pre_commit_file_organization.py .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo "   ✅ Pre-commit hook installed (file organization enforcement)"
    fi

    # TDD enforcement gate (Phase 217)
    if [ -f claude/hooks/pre_commit_tdd_gate.py ]; then
        # Chain TDD gate to pre-commit (runs after file org check)
        echo "   ✅ TDD enforcement gate available (Phase 217)"
    fi
else
    echo "   ⚠️  Not a git repo - skipping hooks (run 'git init' first)"
fi

# Verify path manager works
echo ""
echo "🔍 Verifying Maia installation..."
if python3 -c "from claude.tools.core.path_manager import get_maia_root; print(f'   ✅ MAIA_ROOT: {get_maia_root()}')" 2>/dev/null; then
    echo "   ✅ Path manager working"
else
    echo "   ⚠️  Path manager not found (may need to adjust PYTHONPATH)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit claude/context/personal/profile.md with your info"
echo "  2. Edit claude/data/user_preferences.json if needed"
echo "  3. Run: pytest tests/ to verify everything works"
echo ""
echo "📊 Included databases (ready to use):"
echo "  • system_state.db - 108 phases of development history"
echo "  • capabilities.db - 567 tools/agents indexed"
echo ""
echo "📝 Note: Other databases will auto-create when first used."
echo "   Tools use 'CREATE TABLE IF NOT EXISTS' pattern."
echo ""
echo "🔍 Optional: Set up local LLM for RAG features:"
echo "   brew install ollama && ollama pull nomic-embed-text"
echo ""
echo "For help: see CONTRIBUTING.md"
echo "═══════════════════════════════════════════════════════════"
"""

GITIGNORE_ADDITIONS = """
# ═══════════════════════════════════════════════════════════════
# PERSONAL DATA (never commit)
# ═══════════════════════════════════════════════════════════════

# Personal context
claude/context/personal/
claude/context/💼_professional/

# Personal databases
claude/data/databases/
claude/data/rag_databases/

# Personal preferences (use template)
claude/data/user_preferences.json
claude/data/local_services.json

# Team/org data
claude/context/knowledge/team_intelligence/

# ═══════════════════════════════════════════════════════════════
# STATE & CACHE FILES (environment-specific)
# ═══════════════════════════════════════════════════════════════

claude/data/*.json
!claude/data/*.template.json
!claude/data/immutable_paths.json

claude/data/capability_cache.json
claude/data/confluence_intelligence.json
claude/data/action_completion_metrics.json
claude/data/*_pipeline_state.json
claude/data/llm_routing_log.jsonl

# ═══════════════════════════════════════════════════════════════
# SECRETS & CREDENTIALS
# ═══════════════════════════════════════════════════════════════

.env
*.pem
*.key
credentials.json
*_credentials.json
secrets.yaml

# ═══════════════════════════════════════════════════════════════
# LOCAL SETTINGS
# ═══════════════════════════════════════════════════════════════

.claude/settings.local.json
.claude/hooks.local.json

# ═══════════════════════════════════════════════════════════════
# BUILD & CACHE
# ═══════════════════════════════════════════════════════════════

__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
.eggs/
*.egg
.pytest_cache/
.coverage
htmlcov/

# ═══════════════════════════════════════════════════════════════
# OS & IDE
# ═══════════════════════════════════════════════════════════════

.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp
*.swo
*~

# ═══════════════════════════════════════════════════════════════
# LOGS
# ═══════════════════════════════════════════════════════════════

*.log
logs/
claude/logs/
"""


# ============================================================================
# MAIN SCRIPT
# ============================================================================

class CleanRepoCreator:
    def __init__(self, source_dir: Path, output_dir: Path, dry_run: bool = False):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.stats = {
            "copied": 0,
            "excluded": 0,
            "sanitized": 0,
            "templates_created": 0,
            "governance_created": 0,
        }

    def should_exclude_dir(self, rel_path: str) -> bool:
        """Check if directory should be excluded."""
        for exclude in EXCLUDE_DIRS:
            if rel_path == exclude or rel_path.startswith(exclude + "/"):
                return True
            if exclude in rel_path.split("/"):
                return True
        return False

    def should_exclude_file(self, filename: str, rel_path: str) -> bool:
        """Check if file should be excluded."""
        # Normalize path separators
        rel_path_normalized = rel_path.replace("\\", "/")

        # WHITELIST CHECK: Core architecture databases are always included
        if rel_path_normalized in INCLUDE_DATABASE_FILES:
            return False  # Explicitly include

        # BLACKLIST CHECK: Excluded database files
        if filename in EXCLUDE_DATABASE_FILES:
            return True

        # Check exact filename
        if filename in EXCLUDE_FILES:
            return True

        # Check patterns
        import fnmatch
        for pattern in EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def sanitize_content(self, content: str, filename: str) -> Tuple[str, bool]:
        """Sanitize file content, return (content, was_modified)."""
        modified = False

        # Sanitize passwords
        if filename in FILES_WITH_PASSWORDS:
            for pattern, replacement in PASSWORD_PATTERNS:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    content = new_content
                    modified = True

        # Sanitize hardcoded paths
        for pattern, replacement in PATH_PATTERNS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                modified = True

        # Sanitize emails (only in certain files)
        if filename.endswith(('.py', '.md', '.json')):
            for pattern, replacement in EMAIL_PATTERNS:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True

        return content, modified

    def copy_file(self, src: Path, dst: Path) -> bool:
        """Copy a single file with sanitization."""
        try:
            # Read content
            try:
                with open(src, 'r', encoding='utf-8') as f:
                    content = f.read()
                is_text = True
            except UnicodeDecodeError:
                # Binary file
                is_text = False

            if is_text:
                # Sanitize
                content, was_sanitized = self.sanitize_content(content, src.name)
                if was_sanitized:
                    self.stats["sanitized"] += 1

                if not self.dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    with open(dst, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                # Binary file - copy as-is
                if not self.dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            self.stats["copied"] += 1
            return True

        except Exception as e:
            print(f"  ❌ Error copying {src}: {e}")
            return False

    def copy_directory(self) -> None:
        """Copy source directory to output with exclusions."""
        print(f"📂 Copying from {self.source_dir} to {self.output_dir}")
        print("")

        for root, dirs, files in os.walk(self.source_dir):
            rel_root = os.path.relpath(root, self.source_dir)
            if rel_root == ".":
                rel_root = ""

            # Filter directories (modifies in-place to prevent descent)
            dirs[:] = [d for d in dirs if not self.should_exclude_dir(
                os.path.join(rel_root, d) if rel_root else d
            )]

            for filename in files:
                rel_path = os.path.join(rel_root, filename) if rel_root else filename

                if self.should_exclude_file(filename, rel_path):
                    self.stats["excluded"] += 1
                    continue

                src_path = Path(root) / filename
                dst_path = self.output_dir / rel_path

                self.copy_file(src_path, dst_path)

    def create_templates(self) -> None:
        """Create template files."""
        print("📝 Creating template files...")

        for rel_path, content in TEMPLATES.items():
            dst_path = self.output_dir / rel_path

            if not self.dry_run:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dst_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.stats["templates_created"] += 1
            print(f"   ✅ {rel_path}")

    def create_governance_files(self) -> None:
        """Create governance files."""
        print("📋 Creating governance files...")

        for rel_path, content in GOVERNANCE_FILES.items():
            dst_path = self.output_dir / rel_path

            if not self.dry_run:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dst_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            self.stats["governance_created"] += 1
            print(f"   ✅ {rel_path}")

    def create_setup_script(self) -> None:
        """Create setup script."""
        print("🔧 Creating setup script...")

        dst_path = self.output_dir / "scripts" / "setup.sh"

        if not self.dry_run:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dst_path, 'w', encoding='utf-8') as f:
                f.write(SETUP_SCRIPT)
            os.chmod(dst_path, 0o755)

        print(f"   ✅ scripts/setup.sh")

    def update_gitignore(self) -> None:
        """Update .gitignore with new rules."""
        print("📝 Updating .gitignore...")

        gitignore_path = self.output_dir / ".gitignore"

        if not self.dry_run:
            # Read existing if present
            existing = ""
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    existing = f.read()

            # Append new rules
            with open(gitignore_path, 'w') as f:
                f.write(existing)
                f.write("\n" + GITIGNORE_ADDITIONS)

        print(f"   ✅ .gitignore updated")

    def create_empty_dirs(self) -> None:
        """Create empty directories with .gitkeep files."""
        print("📁 Creating directory structure...")

        dirs_to_create = [
            "claude/context/personal",
            "claude/data/databases/intelligence",
            "claude/data/databases/system",
            "claude/data/databases/user",
            "claude/data/rag_databases",
            "claude/rfcs",
            "docs",
        ]

        for dir_path in dirs_to_create:
            full_path = self.output_dir / dir_path
            if not self.dry_run:
                full_path.mkdir(parents=True, exist_ok=True)
                gitkeep = full_path / ".gitkeep"
                gitkeep.touch()
            print(f"   ✅ {dir_path}/")

    def print_summary(self) -> None:
        """Print summary statistics."""
        print("")
        print("═" * 60)
        print("📊 SUMMARY")
        print("═" * 60)
        print(f"   Files copied:           {self.stats['copied']}")
        print(f"   Files excluded:         {self.stats['excluded']}")
        print(f"   Files sanitized:        {self.stats['sanitized']}")
        print(f"   Templates created:      {self.stats['templates_created']}")
        print(f"   Governance files:       {self.stats['governance_created']}")
        print("")
        print(f"   Output directory:       {self.output_dir}")
        print("═" * 60)

        if self.dry_run:
            print("⚠️  DRY RUN - no files were actually created")
        else:
            print("")
            print("✅ Fresh repository created!")
            print("")
            print("Next steps:")
            print(f"   1. cd {self.output_dir}")
            print("   2. git init")
            print("   3. git add .")
            print("   4. git commit -m 'Initial commit: Clean Maia repository'")
            print("   5. Create new GitHub repo and push")
            print("   6. Configure branch protection in GitHub settings")
            print("   7. Create GitHub teams: maia-contributors, maia-maintainers")

    def run(self) -> None:
        """Run the full creation process."""
        print("═" * 60)
        print("🚀 MAIA FRESH REPOSITORY CREATOR")
        print("═" * 60)
        print(f"   Source: {self.source_dir}")
        print(f"   Output: {self.output_dir}")
        print(f"   Mode:   {'DRY RUN' if self.dry_run else 'LIVE'}")
        print("═" * 60)
        print("")

        if not self.dry_run and self.output_dir.exists():
            print(f"⚠️  Output directory exists: {self.output_dir}")
            response = input("   Delete and recreate? [y/N]: ")
            if response.lower() != 'y':
                print("   Aborted.")
                return
            shutil.rmtree(self.output_dir)

        # Create output directory
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Run steps
        self.copy_directory()
        self.create_templates()
        self.create_governance_files()
        self.create_setup_script()
        self.update_gitignore()
        self.create_empty_dirs()

        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Create a clean, team-shareable Maia repository"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: ~/git/maia-team)"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=None,
        help="Source directory (default: current Maia installation)"
    )

    args = parser.parse_args()

    # Determine source directory
    if args.source_dir:
        source_dir = Path(args.source_dir)
    else:
        # Auto-detect from script location
        source_dir = Path(__file__).parent.parent

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path.home() / "git" / "maia-team"

    # Validate source
    if not (source_dir / "CLAUDE.md").exists():
        print(f"❌ Error: {source_dir} doesn't look like a Maia installation")
        print("   (CLAUDE.md not found)")
        sys.exit(1)

    # Run
    creator = CleanRepoCreator(source_dir, output_dir, args.dry_run)
    creator.run()


if __name__ == "__main__":
    main()
