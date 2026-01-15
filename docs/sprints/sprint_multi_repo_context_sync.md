# Sprint: Multi-Repo Context Sync Fix

**Sprint ID:** SPRINT-001-REPO-SYNC
**Created:** 2026-01-15
**Sprint Length:** 2 weeks (10 working days)
**Priority:** P0 - Critical
**Owner:** DevOps Principal Architect Agent

---

## Sprint Goal

Implement repository context awareness across the Maia system to prevent cross-repo sync issues when operating on personal (`personal-github/maia`) and work (`work-github/team-maia`) repositories.

**Success Criteria:**
- ✅ 100% of git operations target correct repository
- ✅ Sessions track repository context with validation
- ✅ Cross-repo operations blocked by default (requires --force)
- ✅ Zero cross-repo commits in 7-day observation period
- ✅ All tests green (unit + integration)

---

## Sprint Backlog

### Epic 1: Dynamic MAIA_ROOT Detection (P0)
**Points:** 5 | **Days:** 2

#### Story 1.1: Create `get_maia_root()` Utility Function
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P0-P3

**Requirements:**
- Function detects MAIA_ROOT from 3 sources (priority order):
  1. `MAIA_ROOT` environment variable
  2. Walk up from `CWD` looking for `.git` + `claude/` directory
  3. Fallback to script location (backward compat)
- Returns `Path` object
- Raises `ValueError` if no valid maia repo found
- Caches result per session for performance

**TDD Specification:**

**P0 - Test-First Design:**
```python
# tests/test_maia_root_detection.py

def test_get_maia_root_from_env_variable():
    """Test MAIA_ROOT from environment variable (highest priority)."""
    with patch.dict(os.environ, {'MAIA_ROOT': '/Users/username/team-maia'}):
        result = get_maia_root()
        assert result == Path('/Users/username/team-maia')

def test_get_maia_root_from_cwd_walk():
    """Test MAIA_ROOT detection from CWD walk-up."""
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia/claude/tools')):
        result = get_maia_root()
        assert result == Path('/Users/username/team-maia')

def test_get_maia_root_fallback_to_script_location():
    """Test fallback to script location when env/CWD fail."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('pathlib.Path.cwd', return_value=Path('/tmp')):
            result = get_maia_root()
            assert 'maia' in str(result)  # Falls back to script location

def test_get_maia_root_caching():
    """Test that result is cached per session."""
    root1 = get_maia_root()
    root2 = get_maia_root()
    assert root1 is root2  # Same object reference

def test_get_maia_root_validates_structure():
    """Test that detected path has required structure."""
    with patch.dict(os.environ, {'MAIA_ROOT': '/tmp/invalid'}):
        with pytest.raises(ValueError, match="Not a valid Maia repo"):
            get_maia_root()

def test_get_maia_root_performance():
    """Test detection completes in <100ms."""
    import time
    start = time.time()
    get_maia_root()
    duration = time.time() - start
    assert duration < 0.1, f"Detection took {duration:.3f}s, expected <0.1s"
```

**P1 - Tests Fail (Red):**
- Run: `pytest tests/test_maia_root_detection.py -v`
- Expected: All 6 tests FAIL (function doesn't exist yet)

**P2 - Minimal Implementation:**
```python
# claude/tools/core/paths.py

from pathlib import Path
from typing import Optional
import os

_maia_root_cache: Optional[Path] = None

def get_maia_root() -> Path:
    """
    Detect MAIA_ROOT dynamically from multiple sources.

    Priority:
    1. MAIA_ROOT environment variable
    2. Walk up from CWD looking for .git + claude/ directory
    3. Fallback to script location (backward compat)

    Returns:
        Path to maia repository root

    Raises:
        ValueError: If no valid maia repo found

    Performance:
        Result is cached per session, <100ms on first call
    """
    global _maia_root_cache

    # Return cached result
    if _maia_root_cache is not None:
        return _maia_root_cache

    # 1. Check environment variable (highest priority)
    if 'MAIA_ROOT' in os.environ:
        root = Path(os.environ['MAIA_ROOT'])
        if _is_valid_maia_repo(root):
            _maia_root_cache = root
            return root
        else:
            raise ValueError(f"MAIA_ROOT env var points to invalid repo: {root}")

    # 2. Walk up from current working directory
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if _is_valid_maia_repo(parent):
            _maia_root_cache = parent
            return parent

    # 3. Fallback to script location (backward compat)
    script_root = Path(__file__).resolve().parent.parent.parent
    if _is_valid_maia_repo(script_root):
        _maia_root_cache = script_root
        return script_root

    raise ValueError("No valid Maia repository found")


def _is_valid_maia_repo(path: Path) -> bool:
    """
    Validate that path is a valid Maia repository.

    Checks:
    - .git directory exists
    - claude/ directory exists
    - Path is readable

    Args:
        path: Path to check

    Returns:
        True if valid Maia repo
    """
    try:
        return (
            path.exists() and
            path.is_dir() and
            (path / '.git').exists() and
            (path / 'claude').exists() and
            (path / 'claude').is_dir()
        )
    except (OSError, PermissionError):
        return False


def clear_maia_root_cache():
    """Clear cached MAIA_ROOT (for testing)."""
    global _maia_root_cache
    _maia_root_cache = None
```

**P3 - Tests Pass (Green):**
- Run: `pytest tests/test_maia_root_detection.py -v`
- Expected: All 6 tests PASS

**P4 - Refactor:**
- Add type hints
- Add docstrings
- Performance optimization (caching)

**P5 - Integration Test:**
```python
def test_get_maia_root_both_repos():
    """Integration test: Verify works in both repos."""
    # Test in personal repo
    os.chdir('/Users/username/maia')
    clear_maia_root_cache()
    assert get_maia_root() == Path('/Users/username/maia')

    # Test in work repo
    os.chdir('/Users/username/team-maia')
    clear_maia_root_cache()
    assert get_maia_root() == Path('/Users/username/team-maia')
```

**P6 - Code Review:**
- **Handoff to:** Python Code Reviewer Agent
- **Acceptance:** 0 MUST-FIX issues

**P6.5 - Completeness Review:**
- ✅ Tests pass
- ✅ Documentation updated
- ✅ Integration complete
- ✅ No regressions

**Acceptance Criteria:**
- [x] Function detects repo from env var, CWD, and fallback
- [x] Validation ensures .git + claude/ exist
- [x] Caching works (same object returned)
- [x] Performance <100ms
- [x] All tests green

---

#### Story 1.2: Update All Scripts to Use `get_maia_root()`
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P0-P3

**Files to Update:**
1. `claude/tools/sre/save_state.py` (line 85)
2. `claude/hooks/swarm_auto_loader.py` (line ~25)
3. `claude/tools/sre/smart_context_loader.py`
4. `claude/tools/learning/session.py`
5. Any other scripts using `Path(__file__)` for MAIA_ROOT

**TDD Specification:**

**P0 - Test-First Design:**
```python
# tests/test_script_maia_root_usage.py

def test_save_state_uses_dynamic_maia_root():
    """Test save_state.py uses get_maia_root() not hardcoded path."""
    from claude.tools.sre.save_state import SaveState

    # Mock CWD to team-maia
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        clear_maia_root_cache()
        save_state = SaveState()
        assert save_state.maia_root == Path('/Users/username/team-maia')

def test_swarm_auto_loader_uses_dynamic_maia_root():
    """Test swarm_auto_loader.py uses get_maia_root()."""
    # Import after mocking CWD
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        clear_maia_root_cache()
        # Re-import to pick up new MAIA_ROOT
        import importlib
        import claude.hooks.swarm_auto_loader as sal
        importlib.reload(sal)
        assert sal.MAIA_ROOT == Path('/Users/username/team-maia')

def test_session_manager_uses_dynamic_maia_root():
    """Test session manager uses get_maia_root()."""
    from claude.tools.learning.session import get_session_manager

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        clear_maia_root_cache()
        manager = get_session_manager()
        # Verify manager's internal paths use maia repo
        assert 'team-maia' not in str(manager.sessions_dir)
```

**P1 - Tests Fail (Red):**
- Run: `pytest tests/test_script_maia_root_usage.py -v`
- Expected: All tests FAIL (scripts still use hardcoded paths)

**P2 - Minimal Implementation:**

Update each script:

```python
# claude/tools/sre/save_state.py (lines 84-88)
# BEFORE:
def __init__(self, maia_root: Optional[Path] = None):
    self.maia_root = maia_root or Path(__file__).resolve().parent.parent.parent.parent

# AFTER:
from claude.tools.core.paths import get_maia_root

def __init__(self, maia_root: Optional[Path] = None):
    self.maia_root = maia_root or get_maia_root()
```

```python
# claude/hooks/swarm_auto_loader.py (line ~25)
# BEFORE:
MAIA_ROOT = Path(__file__).parent.parent.parent.absolute()

# AFTER:
from claude.tools.core.paths import get_maia_root
MAIA_ROOT = get_maia_root()
```

**P3 - Tests Pass (Green):**
- Run: `pytest tests/test_script_maia_root_usage.py -v`
- Expected: All tests PASS

**Acceptance Criteria:**
- [x] save_state.py uses `get_maia_root()`
- [x] swarm_auto_loader.py uses `get_maia_root()`
- [x] smart_context_loader.py uses `get_maia_root()`
- [x] session.py uses `get_maia_root()`
- [x] Tests verify dynamic detection works

---

### Epic 2: Repository Validator (P0)
**Points:** 8 | **Days:** 3

#### Story 2.1: Create `RepositoryValidator` Class
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P0-P3

**Requirements:**
- Validates current repo matches session repository
- Checks: CWD, git remote URL, git branch
- Returns structured validation result
- Blocks operations if validation fails

**TDD Specification:**

**P0 - Test-First Design:**
```python
# tests/test_repo_validator.py

def test_validator_passes_when_repo_matches():
    """Test validation passes when current repo matches session."""
    validator = RepositoryValidator()

    # Mock session with team-maia context
    session_data = {
        "repository": {
            "working_directory": "/Users/username/team-maia",
            "git_remote_url": "https://github.com/work-github/team-maia.git",
            "git_branch": "main"
        }
    }

    # Mock CWD to match
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        with patch('subprocess.run') as mock_run:
            # Mock git remote
            mock_run.return_value = MagicMock(
                stdout="https://github.com/work-github/team-maia.git\n",
                returncode=0
            )

            result = validator.validate_session_repo(session_data)
            assert result.passed is True
            assert result.warnings == []

def test_validator_fails_when_directory_mismatch():
    """Test validation fails when CWD doesn't match session."""
    validator = RepositoryValidator()

    # Session for team-maia
    session_data = {
        "repository": {
            "working_directory": "/Users/username/team-maia",
            "git_remote_url": "https://github.com/work-github/team-maia.git"
        }
    }

    # But we're in personal maia
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        result = validator.validate_session_repo(session_data)
        assert result.passed is False
        assert 'directory mismatch' in result.reason.lower()

def test_validator_fails_when_remote_url_mismatch():
    """Test validation fails when git remote URL doesn't match."""
    validator = RepositoryValidator()

    session_data = {
        "repository": {
            "working_directory": "/Users/username/team-maia",
            "git_remote_url": "https://github.com/work-github/team-maia.git"
        }
    }

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        with patch('subprocess.run') as mock_run:
            # Mock wrong remote URL
            mock_run.return_value = MagicMock(
                stdout="https://github.com/personal-github/maia.git\n",
                returncode=0
            )

            result = validator.validate_session_repo(session_data)
            assert result.passed is False
            assert 'remote url mismatch' in result.reason.lower()

def test_validator_warns_when_branch_mismatch():
    """Test validation warns (not fails) when branch differs."""
    validator = RepositoryValidator()

    session_data = {
        "repository": {
            "working_directory": "/Users/username/team-maia",
            "git_remote_url": "https://github.com/work-github/team-maia.git",
            "git_branch": "main"
        }
    }

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        with patch('subprocess.run') as mock_run:
            def mock_subprocess(cmd, **kwargs):
                if 'remote' in cmd:
                    return MagicMock(stdout="https://github.com/work-github/team-maia.git\n", returncode=0)
                elif 'branch' in cmd:
                    return MagicMock(stdout="feature-branch\n", returncode=0)

            mock_run.side_effect = mock_subprocess

            result = validator.validate_session_repo(session_data)
            assert result.passed is True  # Branch mismatch is warning only
            assert len(result.warnings) == 1
            assert 'branch' in result.warnings[0].lower()

def test_validator_handles_legacy_sessions_without_repo():
    """Test validator passes for old sessions without repository field."""
    validator = RepositoryValidator()

    # Old session format (no repository field)
    session_data = {
        "current_agent": "sre_principal_engineer_agent",
        "session_start": "2026-01-01T00:00:00Z"
    }

    result = validator.validate_session_repo(session_data)
    assert result.passed is True
    assert 'legacy session' in result.reason.lower()
```

**P1 - Tests Fail (Red):**
- Run: `pytest tests/test_repo_validator.py -v`
- Expected: All 6 tests FAIL (class doesn't exist)

**P2 - Minimal Implementation:**
```python
# claude/tools/sre/repo_validator.py

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import subprocess

@dataclass
class ValidationResult:
    """Result of repository validation."""
    passed: bool
    reason: str
    warnings: List[str]
    current_directory: Optional[Path] = None
    current_remote: Optional[str] = None
    current_branch: Optional[str] = None


class RepositoryValidator:
    """Validates current repository matches session context."""

    def validate_session_repo(self, session_data: dict) -> ValidationResult:
        """
        Validate current repo matches session.

        Args:
            session_data: Session JSON data

        Returns:
            ValidationResult with pass/fail and details
        """
        # Handle legacy sessions (no repository field)
        if 'repository' not in session_data:
            return ValidationResult(
                passed=True,
                reason="Legacy session (no repository field) - assumed valid",
                warnings=["Session format is old, consider re-initializing"]
            )

        repo_data = session_data['repository']
        warnings = []

        # Get current repo info
        current_dir = Path.cwd()
        current_remote = self._get_git_remote()
        current_branch = self._get_git_branch()

        # 1. Check working directory
        expected_dir = Path(repo_data['working_directory'])
        if current_dir != expected_dir:
            return ValidationResult(
                passed=False,
                reason=f"Directory mismatch: Current={current_dir}, Expected={expected_dir}",
                warnings=[],
                current_directory=current_dir,
                current_remote=current_remote,
                current_branch=current_branch
            )

        # 2. Check git remote URL
        expected_remote = repo_data['git_remote_url']
        if current_remote != expected_remote:
            return ValidationResult(
                passed=False,
                reason=f"Remote URL mismatch: Current={current_remote}, Expected={expected_remote}",
                warnings=[],
                current_directory=current_dir,
                current_remote=current_remote,
                current_branch=current_branch
            )

        # 3. Check git branch (warning only, not blocking)
        expected_branch = repo_data.get('git_branch', 'main')
        if current_branch != expected_branch:
            warnings.append(
                f"Branch differs: Current={current_branch}, Session={expected_branch}"
            )

        return ValidationResult(
            passed=True,
            reason="Validation passed - repository matches session",
            warnings=warnings,
            current_directory=current_dir,
            current_remote=current_remote,
            current_branch=current_branch
        )

    def _get_git_remote(self) -> str:
        """Get current git remote origin URL."""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _get_git_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
```

**P3 - Tests Pass (Green):**
- Run: `pytest tests/test_repo_validator.py -v`
- Expected: All 6 tests PASS

**P6 - Code Review:**
- **Handoff to:** Python Code Reviewer Agent
- **Acceptance:** 0 MUST-FIX issues

**Acceptance Criteria:**
- [x] Validates directory, remote URL, branch
- [x] Fails on directory/remote mismatch
- [x] Warns (not fails) on branch mismatch
- [x] Handles legacy sessions gracefully
- [x] Returns structured ValidationResult

---

### Epic 3: Enhanced Session Schema (P0)
**Points:** 8 | **Days:** 3

#### Story 3.1: Update Session Manager with Repository Tracking
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P0-P3

**Requirements:**
- Add `repository` field to session JSON
- Track: working_directory, git_remote_url, git_branch, git_commit_hash, repo_type
- Add `validation` field with last_validated timestamp
- Auto-migrate old sessions on first load

**TDD Specification:**

**P0 - Test-First Design:**
```python
# tests/test_session_repo_tracking.py

def test_session_includes_repository_field():
    """Test new sessions include repository tracking."""
    manager = get_session_manager()

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        session_id = manager.start_session(
            context_id='test_123',
            initial_query='test query',
            agent_used='sre_principal_engineer_agent'
        )

        # Load session
        session_data = manager.load_session(session_id)

        # Verify repository field exists
        assert 'repository' in session_data
        assert session_data['repository']['working_directory'] == '/Users/username/team-maia'
        assert 'team-maia' in session_data['repository']['git_remote_url']
        assert session_data['repository']['repo_type'] == 'work'

def test_session_detects_personal_repo():
    """Test session correctly identifies personal repo."""
    manager = get_session_manager()

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        session_id = manager.start_session(
            context_id='test_456',
            initial_query='test query',
            agent_used='data_analyst_agent'
        )

        session_data = manager.load_session(session_id)
        assert session_data['repository']['repo_type'] == 'personal'
        assert 'personal-github' in session_data['repository']['git_remote_url']

def test_session_validation_field_exists():
    """Test sessions include validation tracking."""
    manager = get_session_manager()

    session_id = manager.start_session(
        context_id='test_789',
        initial_query='test',
        agent_used='sre_principal_engineer_agent'
    )

    session_data = manager.load_session(session_id)
    assert 'validation' in session_data
    assert session_data['validation']['validation_passed'] is True
    assert 'last_validated' in session_data['validation']

def test_old_sessions_migrate_on_load():
    """Test old sessions without repository field are migrated."""
    manager = get_session_manager()

    # Create old-style session
    old_session = {
        "current_agent": "sre_principal_engineer_agent",
        "session_start": "2026-01-01T00:00:00Z",
        "query": "old session"
    }

    # Save old session
    session_file = Path('~/.maia/sessions/swarm_session_999.json').expanduser()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(json.dumps(old_session, indent=2))

    # Load session - should auto-migrate
    migrated = manager.load_session('999')

    # Verify migration
    assert 'repository' in migrated
    assert 'validation' in migrated
    assert migrated['validation']['warnings'][0] == 'Migrated from legacy format'
```

**P2 - Minimal Implementation:**
```python
# claude/tools/learning/session.py

from claude.tools.core.paths import get_maia_root
import subprocess

class SessionManager:
    # ... existing code ...

    def start_session(self, context_id: str, initial_query: str, agent_used: str) -> str:
        """Start new session with repository tracking."""

        # Detect current repository
        repo_info = self._detect_repository()

        session_data = {
            "current_agent": agent_used,
            "session_start": datetime.utcnow().isoformat() + 'Z',
            "query": initial_query,
            "context": {},
            "domain": self._classify_domain(agent_used),

            # NEW: Repository tracking
            "repository": repo_info,

            # NEW: Validation status
            "validation": {
                "last_validated": datetime.utcnow().isoformat() + 'Z',
                "validation_passed": True,
                "current_directory_matches": True,
                "warnings": []
            }
        }

        # Save session
        session_file = self.sessions_dir / f"swarm_session_{context_id}.json"
        session_file.write_text(json.dumps(session_data, indent=2))

        return context_id

    def _detect_repository(self) -> dict:
        """
        Detect current repository context.

        Returns:
            Repository info dict with:
            - working_directory
            - git_remote_url
            - git_branch
            - git_commit_hash
            - session_start_commit
            - repo_type
        """
        maia_root = get_maia_root()

        # Get git info
        git_remote = subprocess.run(
            ['git', '-C', str(maia_root), 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True
        ).stdout.strip()

        git_branch = subprocess.run(
            ['git', '-C', str(maia_root), 'branch', '--show-current'],
            capture_output=True, text=True
        ).stdout.strip()

        git_commit = subprocess.run(
            ['git', '-C', str(maia_root), 'rev-parse', 'HEAD'],
            capture_output=True, text=True
        ).stdout.strip()

        # Determine repo type from remote URL
        if 'team-maia' in git_remote:
            repo_type = 'work'
        elif 'personal-github' in git_remote or 'naythan' in git_remote:
            repo_type = 'personal'
        else:
            repo_type = 'unknown'

        return {
            "working_directory": str(maia_root),
            "git_remote_url": git_remote,
            "git_branch": git_branch,
            "git_commit_hash": git_commit[:7],
            "session_start_commit": git_commit[:7],
            "repo_type": repo_type
        }

    def load_session(self, context_id: str) -> dict:
        """Load session with auto-migration for legacy sessions."""
        session_file = self.sessions_dir / f"swarm_session_{context_id}.json"

        if not session_file.exists():
            return {}

        session_data = json.loads(session_file.read_text())

        # Auto-migrate legacy sessions
        if 'repository' not in session_data:
            session_data = self._migrate_legacy_session(session_data)
            # Save migrated version
            session_file.write_text(json.dumps(session_data, indent=2))

        return session_data

    def _migrate_legacy_session(self, old_session: dict) -> dict:
        """Migrate old session format to new format with repository tracking."""

        # Detect current repo (best effort)
        repo_info = self._detect_repository()

        # Add repository and validation fields
        migrated = old_session.copy()
        migrated['repository'] = repo_info
        migrated['validation'] = {
            "last_validated": datetime.utcnow().isoformat() + 'Z',
            "validation_passed": True,
            "current_directory_matches": True,
            "warnings": ["Migrated from legacy format - repository context may be inaccurate"]
        }

        return migrated
```

**P3 - Tests Pass (Green):**
- Run: `pytest tests/test_session_repo_tracking.py -v`
- Expected: All 4 tests PASS

**Acceptance Criteria:**
- [x] New sessions include repository field
- [x] Repository type detected correctly (personal/work)
- [x] Validation field tracks status
- [x] Legacy sessions auto-migrate on load
- [x] Migrated sessions save with new format

---

### Epic 4: Save State Validation (P0)
**Points:** 5 | **Days:** 2

#### Story 4.1: Add Repo Validation to `save_state.py`
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P0-P3

**Requirements:**
- Validate repo context before commit/push
- Block if validation fails (unless --force)
- Clear error messages with resolution steps
- Log force overrides to audit log

**TDD Specification:**

**P0 - Test-First Design:**
```python
# tests/test_save_state_validation.py

def test_save_state_blocks_when_wrong_repo():
    """Test save_state blocks commit when in wrong repo."""
    # Create session for team-maia
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        manager = get_session_manager()
        session_id = manager.start_session('test_123', 'test', 'sre_principal_engineer_agent')

    # Switch to personal maia (without closing session)
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        save_state = SaveState()
        exit_code = save_state.run(check_only=False, force=False)

        # Should be blocked
        assert exit_code == 1
        # Verify no commit was made
        # (check git log)

def test_save_state_allows_force_override():
    """Test save_state allows --force override."""
    # Session for team-maia, but in personal maia
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        save_state = SaveState()
        exit_code = save_state.run(check_only=False, force=True)

        # Should succeed with warning
        assert exit_code == 0

def test_save_state_logs_force_override():
    """Test force override is logged to audit.log."""
    audit_log = Path('claude/data/audit.log')

    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/maia')):
        save_state = SaveState()
        save_state.run(check_only=False, force=True)

    # Verify audit log entry
    assert audit_log.exists()
    log_content = audit_log.read_text()
    assert 'FORCE OVERRIDE' in log_content
    assert 'repo validation bypassed' in log_content.lower()

def test_save_state_passes_when_repo_matches():
    """Test save_state passes when in correct repo."""
    with patch('pathlib.Path.cwd', return_value=Path('/Users/username/team-maia')):
        # Create session and save state in same repo
        manager = get_session_manager()
        manager.start_session('test_456', 'test', 'sre_principal_engineer_agent')

        save_state = SaveState()
        exit_code = save_state.run(check_only=True, force=False)

        assert exit_code == 0
```

**P2 - Minimal Implementation:**
```python
# claude/tools/sre/save_state.py

from claude.tools.core.paths import get_maia_root
from claude.tools.sre.repo_validator import RepositoryValidator

class SaveState:
    def __init__(self, maia_root: Optional[Path] = None):
        # Use dynamic detection
        self.maia_root = maia_root or get_maia_root()
        self.validator = RepositoryValidator()

        # Validate we're in a maia repo
        if not self._is_valid_maia_repo(self.maia_root):
            raise ValueError(f"Not a valid Maia repo: {self.maia_root}")

    def _validate_repo_context(self) -> Tuple[bool, str]:
        """
        Validate current repo matches session context.

        Returns:
            (passed, error_message)
        """
        # Load current session
        context_id = self._get_current_context_id()
        if not context_id:
            # No active session, skip validation
            return True, ""

        manager = get_session_manager()
        session_data = manager.load_session(context_id)

        # Validate
        result = self.validator.validate_session_repo(session_data)

        if not result.passed:
            error_msg = f"""
❌ REPO VALIDATION FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Directory: {result.current_directory}
Current Remote:    {result.current_remote}

Session Directory: {session_data['repository']['working_directory']}
Session Remote:    {session_data['repository']['git_remote_url']}

Reason: {result.reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOLUTION:

1. If you want to save in the CURRENT repo:
   $ cd {result.current_directory}
   $ /close-session    # Close the old session
   $ /init             # Start new session
   $ save state

2. If you want to save in the SESSION repo:
   $ cd {session_data['repository']['working_directory']}
   $ save state

3. To override this check (NOT RECOMMENDED):
   $ python3 claude/tools/sre/save_state.py --force

   ⚠️  Force override will be logged to audit.log
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            return False, error_msg

        # Check for warnings
        if result.warnings:
            for warning in result.warnings:
                print(f"⚠️  {warning}")

        return True, ""

    def _log_force_override(self, reason: str):
        """Log force override to audit log."""
        audit_log = self.maia_root / "claude" / "data" / "audit.log"
        audit_log.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().isoformat()
        entry = f"""
[{timestamp}] FORCE OVERRIDE
Action: save_state --force
Reason: {reason}
CWD: {Path.cwd()}
MAIA_ROOT: {self.maia_root}
User: {os.getenv('USER', 'unknown')}
"""
        with open(audit_log, 'a') as f:
            f.write(entry)

    def run(self, check_only: bool = False, force: bool = False) -> int:
        """Run the save state protocol with repo validation."""
        print("=" * 60)
        print("🔍 SAVE STATE - Documentation Enforcement")
        print("=" * 60)
        print()

        # NEW: Validate repo context
        if not force:
            print("🔍 Validating repository context...")
            passed, error_msg = self._validate_repo_context()

            if not passed:
                print(error_msg)
                return 1

            print("   ✅ Repository validation passed")
            print()
        else:
            print("⚠️  FORCE MODE: Skipping repository validation")
            self._log_force_override("Repo validation bypassed")
            print()

        # ... rest of existing flow ...
```

**P3 - Tests Pass (Green):**
- Run: `pytest tests/test_save_state_validation.py -v`
- Expected: All 4 tests PASS

**Acceptance Criteria:**
- [x] Blocks commit when repo doesn't match session
- [x] Allows --force override with warning
- [x] Logs force overrides to audit.log
- [x] Passes when repo matches session
- [x] Clear error messages with resolution steps

---

### Epic 5: Integration & Testing (P1)
**Points:** 8 | **Days:** 3

#### Story 5.1: End-to-End Multi-Repo Workflow Tests
**Agent:** SRE Principal Engineer | **Model:** Sonnet | **TDD Phase:** P5

**Requirements:**
- Test complete workflow across both repos
- Test cross-repo operation blocking
- Test session persistence and migration
- Performance benchmarks (<100ms overhead)

**TDD Specification:**

```python
# tests/integration/test_multi_repo_workflow.py

@pytest.mark.integration
def test_complete_multi_repo_workflow():
    """Integration test: Full workflow across both repos."""
    # 1. Start in personal repo
    os.chdir('/Users/username/maia')
    clear_maia_root_cache()

    # Initialize session
    context_id = run_command('/init sre_principal_engineer_agent')
    assert context_id is not None

    # Make changes
    test_file = Path('test_file.txt')
    test_file.write_text('personal repo test')

    # Save state
    result = run_command('save state')
    assert result.returncode == 0

    # Verify commit went to personal repo
    last_commit_repo = get_last_commit_repo()
    assert 'personal-github/maia' in last_commit_repo

    # 2. Switch to work repo
    os.chdir('/Users/username/team-maia')
    clear_maia_root_cache()

    # Close old session and start new
    run_command('/close-session')
    context_id = run_command('/init data_analyst_agent')

    # Make changes
    test_file = Path('test_file.txt')
    test_file.write_text('work repo test')

    # Save state
    result = run_command('save state')
    assert result.returncode == 0

    # Verify commit went to work repo
    last_commit_repo = get_last_commit_repo()
    assert 'work-github/team-maia' in last_commit_repo

@pytest.mark.integration
def test_cross_repo_operation_blocked():
    """Test that cross-repo operations are blocked."""
    # 1. Start session in personal repo
    os.chdir('/Users/username/maia')
    session_id = run_command('/init sre_principal_engineer_agent')

    # 2. Switch to work repo WITHOUT closing session
    os.chdir('/Users/username/team-maia')
    clear_maia_root_cache()

    # 3. Try to save state - should be BLOCKED
    result = run_command('save state')
    assert result.returncode == 1
    assert 'REPO VALIDATION FAILED' in result.output
    assert 'Resolution' in result.output

@pytest.mark.integration
def test_session_migration():
    """Test legacy session migration."""
    # Create old-style session
    old_session = {
        "current_agent": "sre_principal_engineer_agent",
        "session_start": "2026-01-01T00:00:00Z"
    }

    session_file = Path('~/.maia/sessions/swarm_session_legacy.json').expanduser()
    session_file.write_text(json.dumps(old_session, indent=2))

    # Load session - should auto-migrate
    manager = get_session_manager()
    migrated = manager.load_session('legacy')

    # Verify migration
    assert 'repository' in migrated
    assert 'validation' in migrated

    # Verify saved with new format
    reloaded = manager.load_session('legacy')
    assert reloaded == migrated

@pytest.mark.integration
@pytest.mark.performance
def test_repo_detection_performance():
    """Test repo detection completes in <100ms."""
    import time

    # Clear cache
    clear_maia_root_cache()

    # Time detection
    start = time.time()
    maia_root = get_maia_root()
    duration = time.time() - start

    assert duration < 0.1, f"Detection took {duration:.3f}s, expected <0.1s"

    # Test cached performance (should be <1ms)
    start = time.time()
    maia_root2 = get_maia_root()
    cached_duration = time.time() - start

    assert cached_duration < 0.001, f"Cached lookup took {cached_duration:.3f}s"
    assert maia_root is maia_root2  # Same object
```

**Acceptance Criteria:**
- [x] Complete workflow works in both repos
- [x] Cross-repo operations blocked
- [x] Legacy sessions migrate automatically
- [x] Performance <100ms for detection, <1ms cached

---

### Epic 6: Documentation & UX (P2)
**Points:** 5 | **Days:** 2

#### Story 6.1: Update Agent Documentation
**Agent:** Prompt Engineer | **Model:** Sonnet

**Files to Update:**
1. `claude/agents/devops_principal_architect_agent.md` - Add repo context guidance
2. `claude/agents/sre_principal_engineer_agent.md` - Add save_state repo validation
3. `CLAUDE.md` - Add multi-repo workflow section

**Requirements:**
- Document multi-repo workflow in CLAUDE.md
- Update agent docs with repo context awareness
- Add troubleshooting guide for validation failures

**Acceptance Criteria:**
- [x] CLAUDE.md has "Multi-Repo Workflow" section
- [x] Agent docs mention repo validation
- [x] Troubleshooting guide complete

#### Story 6.2: Create `/switch-repo` Command
**Agent:** SRE Principal Engineer | **Model:** Sonnet

**Requirements:**
- Prompt to save current session
- Close active session
- Validate target repo exists
- Create new session for target repo

**Acceptance Criteria:**
- [x] Command prompts to save before switch
- [x] Validates target repo exists
- [x] Creates new session in target repo
- [x] Tests pass

---

## Agent & Model Mapping

### Phase 1: Core Infrastructure (Days 1-2)

**Sprint Day 1-2:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 1.1: `get_maia_root()` | SRE Principal Engineer | Sonnet | Standard implementation, well-defined requirements |
| Story 1.2: Update scripts | SRE Principal Engineer | Sonnet | Mechanical refactoring, low complexity |
| Code Review | Python Code Reviewer | Sonnet | Standard code review, efficiency patterns |

### Phase 2: Repository Validator (Days 3-5)

**Sprint Day 3-5:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 2.1: `RepositoryValidator` | SRE Principal Engineer | Sonnet | Clear requirements, structured validation logic |
| Integration Tests | SRE Principal Engineer | Sonnet | Standard testing patterns |
| Code Review | Python Code Reviewer | Sonnet | Standard review |

### Phase 3: Session Manager (Days 6-8)

**Sprint Day 6-8:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 3.1: Session schema update | SRE Principal Engineer | Sonnet | Well-defined schema changes |
| Migration logic | SRE Principal Engineer | Sonnet | Standard data migration |
| Code Review | Python Code Reviewer | Sonnet | Review migration safety |

### Phase 4: Save State Validation (Day 9)

**Sprint Day 9:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 4.1: save_state validation | SRE Principal Engineer | Sonnet | Clear validation requirements |
| Audit logging | SRE Principal Engineer | Sonnet | Simple logging implementation |
| Code Review | Python Code Reviewer | Sonnet | Security review (audit log) |

### Phase 5: Integration & Testing (Day 10)

**Sprint Day 10:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 5.1: Integration tests | SRE Principal Engineer | Sonnet | Standard integration testing |
| Performance benchmarks | SRE Principal Engineer | Sonnet | Measure and optimize |
| Final validation | Data Analyst | Sonnet | Test database queries work correctly |

### Phase 6: Documentation (Day 11)

**Sprint Day 11:**
| Task | Agent | Model | Reasoning |
|------|-------|-------|-----------|
| Story 6.1: Agent docs | Prompt Engineer | Sonnet | Documentation updates |
| Story 6.2: `/switch-repo` cmd | SRE Principal Engineer | Sonnet | New command implementation |
| CLAUDE.md updates | Prompt Engineer | Sonnet | User-facing documentation |

---

## Dependencies & Handoffs

### Handoff Flow

```
DevOps (Architecture)
    ↓ [Requirements Doc]
SRE (Implementation - Story 1.1)
    ↓ [get_maia_root() complete]
Python Reviewer (Code Review)
    ↓ [0 MUST-FIX]
SRE (Implementation - Story 1.2)
    ↓ [Scripts updated]
Python Reviewer (Code Review)
    ↓ [0 MUST-FIX]
SRE (Implementation - Story 2.1)
    ↓ [RepositoryValidator complete]
Python Reviewer (Code Review)
    ↓ [0 MUST-FIX]
SRE (Implementation - Story 3.1)
    ↓ [Session schema updated]
Python Reviewer (Code Review)
    ↓ [0 MUST-FIX]
SRE (Implementation - Story 4.1)
    ↓ [save_state validation complete]
Python Reviewer (Code Review)
    ↓ [0 MUST-FIX]
SRE (Integration Tests - Story 5.1)
    ↓ [All tests green]
Data Analyst (Validation)
    ↓ [DB queries work]
Prompt Engineer (Documentation - Story 6.1, 6.2)
    ↓ [Docs complete]
DevOps (Sprint Review)
```

### Critical Dependencies

**Story 1.2 → Story 2.1:**
- `get_maia_root()` must be complete before validator can use it

**Story 2.1 → Story 3.1:**
- `RepositoryValidator` must exist before session manager can validate

**Story 3.1 → Story 4.1:**
- Session schema with repository field must exist before save_state can validate

**Story 4.1 → Story 5.1:**
- All components must be complete before integration testing

---

## Risk Management

### High Risks

**Risk 1: Breaking Existing Workflows**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Backward compatibility for legacy sessions
  - Gradual rollout with feature flag
  - Comprehensive testing before deployment
- **Owner:** SRE Principal Engineer

**Risk 2: Performance Regression**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Performance benchmarks in tests (<100ms requirement)
  - Caching for `get_maia_root()`
  - Validation only on critical operations
- **Owner:** SRE Principal Engineer

**Risk 3: False Positive Blocks**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Clear error messages with resolution steps
  - `--force` override always available
  - Warning (not blocking) for branch mismatch
- **Owner:** DevOps Principal Architect

### Medium Risks

**Risk 4: Migration Complexity**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Auto-migration on session load
  - Keep old schema as fallback
  - Test migration with real old sessions
- **Owner:** SRE Principal Engineer

---

## Definition of Done

### Story Level DoD
- [ ] All P0-P6.5 TDD phases complete
- [ ] Unit tests pass (100% coverage for new code)
- [ ] Integration tests pass
- [ ] Code review complete (0 MUST-FIX issues)
- [ ] Documentation updated
- [ ] No regressions in existing functionality

### Epic Level DoD
- [ ] All stories in epic complete
- [ ] Epic-level integration tests pass
- [ ] Performance benchmarks met
- [ ] Security review complete (for validation/audit)

### Sprint Level DoD
- [ ] All epics complete
- [ ] End-to-end workflow tested in both repos
- [ ] Zero cross-repo commits in test observation
- [ ] Documentation complete and published
- [ ] Sprint demo prepared
- [ ] Retrospective completed

---

## Sprint Metrics

### Velocity Tracking
- **Planned Points:** 39
- **Completed Points:** [To be updated]
- **Velocity:** [To be calculated]

### Quality Metrics
- **Test Coverage:** Target >90%
- **Code Review Score:** Target >95/100
- **MUST-FIX Issues:** Target 0

### Performance Metrics
- **Repo Detection:** <100ms (first call), <1ms (cached)
- **Validation Overhead:** <50ms per operation
- **Session Load Time:** <200ms

---

## Daily Standup Template

**What did I complete yesterday?**
- [Story/Task completed]

**What will I work on today?**
- [Story/Task for today]

**Any blockers?**
- [Blockers or dependencies]

**Agent handoffs needed?**
- [Agent → Agent for what]

---

## Sprint Review Checklist

### Demo Preparation
- [ ] Test in personal repo (`personal-github/maia`)
- [ ] Test in work repo (`work-github/team-maia`)
- [ ] Demo cross-repo blocking
- [ ] Demo force override with audit log
- [ ] Show performance metrics

### Success Validation
- [ ] Make commits in both repos successfully
- [ ] Attempt cross-repo commit (verify blocked)
- [ ] Load old session (verify migration)
- [ ] Check audit log for force overrides
- [ ] Verify performance <100ms

---

## Next Sprint Planning

**Carry Over:**
- Any incomplete stories from this sprint

**Future Enhancements:**
- Repo context in CLI prompt (show current repo)
- Auto-switch repo on `cd` (bash hook)
- Multi-repo analytics (which repo gets more commits)
- Repo-specific configuration profiles

---

## References

- **Requirements:** `docs/requirements/multi_repo_context_sync_fix.md`
- **TDD Protocol:** `claude/context/core/tdd_development_protocol.md`
- **Agent Handoffs:** `claude/context/tools/agent_handoff_developer_guide.md`
- **Code Review:** `claude/agents/python_code_reviewer_agent.md`
