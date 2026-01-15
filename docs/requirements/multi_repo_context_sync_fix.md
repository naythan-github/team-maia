# Multi-Repo Context Sync Fix

**Created:** 2026-01-15
**Status:** Requirements Analysis
**Priority:** High
**Agent:** DevOps Principal Architect

---

## Executive Summary

The Maia system currently lacks repository context awareness, causing sync issues when working across multiple repositories (personal `maia` and work `team-maia`). Operations like `save state`, session loading, and git commands target the wrong repository because scripts use hardcoded paths instead of dynamic detection.

### Impact
- ❌ Git operations (commit, push) execute in wrong repository
- ❌ Session context doesn't track which repo is active
- ❌ No validation that operations target intended repository
- ❌ Context switching between repos requires manual intervention
- ❌ Risk of committing work code to personal repo or vice versa

---

## Problem Analysis

### 1. Repository Configuration

**Personal Repo:**
- Path: `/Users/username/maia`
- Remote: `https://github.com/personal-github/maia.git`
- Purpose: Personal Maia development

**Work Repo:**
- Path: `/Users/username/team-maia`
- Remote: `https://github.com/work-github/team-maia.git`
- Purpose: Team/work Maia instance

Both repos have **identical structure** and share the same codebase.

### 2. Root Cause Analysis

#### Issue #1: Hardcoded MAIA_ROOT Detection

**File:** `claude/tools/sre/save_state.py` (lines 84-88)
```python
def __init__(self, maia_root: Optional[Path] = None):
    self.maia_root = maia_root or Path(__file__).resolve().parent.parent.parent.parent
```

**Problem:**
- Uses `Path(__file__)` which resolves to **where the script is located**
- If script lives in `/Users/username/maia/`, it ALWAYS uses that repo
- Even if you run the command from `/Users/username/team-maia/`

**File:** `claude/hooks/swarm_auto_loader.py` (line ~25)
```python
MAIA_ROOT = Path(__file__).parent.parent.parent.absolute()
```

**Same issue** - hardcoded to script location, not current working directory.

#### Issue #2: Session Doesn't Track Repository Context

**File:** `~/.maia/sessions/swarm_session_2963.json`

**Current fields:**
```json
{
  "current_agent": "devops_principal_architect_agent",
  "session_start": "2026-01-15T01:07:55Z",
  "handoff_chain": [...],
  "context": {},
  "domain": "devops",
  "last_classification_confidence": 1.0,
  "query": "OTC ticket database questions"
}
```

**Missing fields:**
- `working_directory` - Which repo is this session for?
- `git_repo` - Which GitHub repo URL?
- `repo_validation` - Checksums/validation that we're in right place

**Impact:**
- Session loads but doesn't know which repo to operate on
- No validation that current directory matches session context
- Agent switches don't preserve repo context

#### Issue #3: No Repository Validation Before Critical Operations

**Critical operations with no repo validation:**

1. **`save_state.py`** - Commits and pushes without checking which repo
   ```python
   def commit_changes(self, message: str):
       subprocess.run(["git", "add", "-A"], cwd=self.maia_root)
       # Always uses hardcoded maia_root!
   ```

2. **Session loading** - Loads agent but doesn't verify repo
3. **Context loading** - Loads UFC/docs from script location, not PWD
4. **Database operations** - May reference wrong DB files

### 3. Attack Scenarios (What Goes Wrong)

#### Scenario A: Wrong Repo Commit
```bash
$ cd /Users/username/team-maia
$ claude "fix bug in servicedesk loader"
# ... makes changes to team-maia code ...
$ claude "save state"
# ❌ Commits and pushes to personal-github/maia (personal repo)
# ✅ Should commit to work-github/team-maia (work repo)
```

#### Scenario B: Context Confusion
```bash
$ cd /Users/username/team-maia
$ /init sre_principal_engineer_agent
# ❌ Loads UFC from /Users/username/maia/claude/context/
# ✅ Should load from /Users/username/team-maia/claude/context/
```

#### Scenario C: Session Persistence Mismatch
```bash
$ cd /Users/username/maia
$ /init data_analyst_agent
# Session saved for maia repo

# Later...
$ cd /Users/username/team-maia
$ claude "analyze tickets"
# ❌ Auto-loads data_analyst_agent from maia repo session
# ✅ Should prompt which repo context or create new session
```

---

## Requirements

### Functional Requirements

**FR-1: Dynamic Repository Detection**
- System MUST detect current working directory's git repository
- System MUST NOT hardcode repository path in scripts
- System MUST support multiple repos with same structure

**FR-2: Session Repository Tracking**
- Sessions MUST track `working_directory` (absolute path)
- Sessions MUST track `git_repo` (remote origin URL)
- Sessions MUST track `git_branch` (current branch)
- Sessions MUST include `repo_validation` (git commit hash at session start)

**FR-3: Repository Validation**
- Critical operations (commit, push, db writes) MUST validate repo context
- System MUST warn if current directory ≠ session repo
- System MUST block operations if validation fails (unless --force)

**FR-4: Context Isolation**
- Sessions for different repos MUST NOT interfere
- Context loading MUST use current repo's files, not script location
- Database paths MUST be repo-relative

**FR-5: Explicit Repo Switching**
- User MUST be able to switch repos mid-session
- System MUST prompt to save/close current session before switch
- System MUST create new session for new repo

### Non-Functional Requirements

**NFR-1: Backward Compatibility**
- Existing sessions without repo context MUST still load
- System MUST migrate old sessions on first load
- Default to personal repo (`/Users/username/maia`) for legacy sessions

**NFR-2: Performance**
- Repo detection MUST complete in <100ms
- Validation MUST NOT add >50ms to critical operations

**NFR-3: Safety**
- System MUST NEVER commit to wrong repo
- System MUST block cross-repo operations by default
- Override requires explicit --force flag with confirmation

---

## Proposed Solution Architecture

### 1. Dynamic MAIA_ROOT Detection

**Replace hardcoded `Path(__file__)` with:**

```python
def get_maia_root() -> Path:
    """
    Detect MAIA_ROOT dynamically from current working directory.

    Strategy:
    1. Check MAIA_ROOT environment variable
    2. Walk up from CWD looking for .git + claude/ directory
    3. Fallback to script location (backward compat)

    Returns:
        Path to maia repository root
    """
    # 1. Check environment variable (highest priority)
    if 'MAIA_ROOT' in os.environ:
        root = Path(os.environ['MAIA_ROOT'])
        if (root / 'claude').exists() and (root / '.git').exists():
            return root

    # 2. Walk up from current working directory
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / 'claude').exists() and (parent / '.git').exists():
            return parent

    # 3. Fallback to script location (backward compat)
    return Path(__file__).resolve().parent.parent.parent.parent
```

**Modify all scripts:**
- `save_state.py` - Use `get_maia_root()` instead of hardcoded path
- `swarm_auto_loader.py` - Use `get_maia_root()` instead of `__file__`
- `smart_context_loader.py` - Dynamic detection
- All tools in `claude/tools/` - Use `MAIA_ROOT` from `core/paths.py`

### 2. Enhanced Session Schema

**Add to session JSON:**
```json
{
  "current_agent": "...",
  "session_start": "...",

  "repository": {
    "working_directory": "/Users/username/team-maia",
    "git_remote_url": "https://github.com/work-github/team-maia.git",
    "git_branch": "main",
    "git_commit_hash": "7bcaaeb...",
    "session_start_commit": "7bcaaeb...",
    "repo_type": "work"  # "personal" | "work"
  },

  "validation": {
    "last_validated": "2026-01-15T07:45:00Z",
    "validation_passed": true,
    "current_directory_matches": true
  }
}
```

### 3. Repository Validator

**New tool:** `claude/tools/sre/repo_validator.py`

```python
class RepositoryValidator:
    """Validates current directory matches session repository context."""

    def validate_session_repo(self, session_file: Path) -> ValidationResult:
        """
        Validate current repo matches session.

        Checks:
        1. CWD matches session working_directory
        2. Git remote URL matches session git_remote_url
        3. Git branch matches (warn if different, not blocking)

        Returns:
            ValidationResult with passed/failed and details
        """
        pass

    def block_operation_if_invalid(self, operation: str) -> bool:
        """
        Block operation if repo validation fails.

        Args:
            operation: Name of operation (commit, push, db_write)

        Returns:
            True if allowed, False if blocked
        """
        pass
```

### 4. Modified Save State Flow

**Update `save_state.py`:**

```python
class SaveState:
    def __init__(self, maia_root: Optional[Path] = None):
        # Use dynamic detection
        self.maia_root = maia_root or get_maia_root()

        # Validate we're in a maia repo
        if not self._is_valid_maia_repo(self.maia_root):
            raise ValueError(f"Not a valid Maia repo: {self.maia_root}")

    def _validate_repo_context(self) -> bool:
        """Validate current repo matches expected context."""
        validator = RepositoryValidator()
        result = validator.validate_current_repo(self.maia_root)

        if not result.passed:
            print(f"❌ REPO VALIDATION FAILED:")
            print(f"   Current: {Path.cwd()}")
            print(f"   Expected: {self.maia_root}")
            print(f"   Remote: {result.current_remote}")
            print(f"\n   Use --force to override (NOT RECOMMENDED)")
            return False

        return True

    def run(self, check_only: bool = False, force: bool = False):
        # Add repo validation before commit
        if not force:
            if not self._validate_repo_context():
                return 1

        # ... existing flow ...
```

### 5. Session Manager Updates

**Modify `claude/tools/learning/session.py`:**

```python
def start_session(self, context_id: str, initial_query: str, agent_used: str):
    """Start session with repository tracking."""

    # Detect current repo
    repo_info = self._detect_repository()

    session_data = {
        "current_agent": agent_used,
        "session_start": datetime.utcnow().isoformat() + 'Z',
        "query": initial_query,
        "repository": repo_info,
        "validation": {
            "last_validated": datetime.utcnow().isoformat() + 'Z',
            "validation_passed": True,
            "current_directory_matches": True
        }
    }

    # ... save session ...

def _detect_repository(self) -> dict:
    """Detect current repository context."""
    maia_root = get_maia_root()

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
    repo_type = 'work' if 'team-maia' in git_remote else 'personal'

    return {
        "working_directory": str(maia_root),
        "git_remote_url": git_remote,
        "git_branch": git_branch,
        "git_commit_hash": git_commit[:7],
        "session_start_commit": git_commit[:7],
        "repo_type": repo_type
    }
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (P1 - Critical)

**Task 1.1:** Create `get_maia_root()` utility
- **File:** `claude/tools/core/paths.py`
- **Logic:** Environment var → CWD walk-up → Fallback
- **Testing:** Unit tests for all three paths

**Task 1.2:** Create `RepositoryValidator`
- **File:** `claude/tools/sre/repo_validator.py`
- **Methods:** `validate_session_repo()`, `block_operation_if_invalid()`
- **Testing:** Mock git commands, test pass/fail scenarios

**Task 1.3:** Update session schema
- **File:** `claude/tools/learning/session.py`
- **Add:** `repository` and `validation` fields
- **Migration:** Handle old sessions without repo context

### Phase 2: Script Updates (P2 - High)

**Task 2.1:** Update `save_state.py`
- Replace `Path(__file__)` with `get_maia_root()`
- Add `_validate_repo_context()` before commits
- Add `--force` override with warning

**Task 2.2:** Update `swarm_auto_loader.py`
- Replace `MAIA_ROOT = Path(__file__)...` with `get_maia_root()`
- Add repo validation on session load
- Warn if CWD ≠ session repo

**Task 2.3:** Update `smart_context_loader.py`
- Use dynamic MAIA_ROOT
- Load context from correct repo

### Phase 3: User Experience (P3 - Medium)

**Task 3.1:** Add repo status to `/init`
- Show current repo in UFC header
- Display repo type (personal/work)
- Show git branch

**Task 3.2:** Create `/switch-repo` command
- Prompt to save current session
- Close active session
- Validate target repo exists
- Create new session for target repo

**Task 3.3:** Update session listing
- Show repo context in session list
- Filter sessions by repo
- Warn about repo mismatches

### Phase 4: Safety & Validation (P4 - High)

**Task 4.1:** Add pre-commit repo validation
- Hook before every commit
- Block if CWD ≠ session repo
- Require --force override

**Task 4.2:** Add database path validation
- Ensure DB operations use correct repo's DBs
- Warn if accessing wrong repo's data

**Task 4.3:** Add comprehensive testing
- Integration tests for multi-repo scenarios
- Test cross-repo operation blocking
- Test session migration

---

## Testing Strategy

### Unit Tests

**Test:** `test_get_maia_root()`
```python
def test_get_maia_root_from_env():
    """Test MAIA_ROOT from environment variable."""
    with patch.dict(os.environ, {'MAIA_ROOT': '/tmp/maia'}):
        assert get_maia_root() == Path('/tmp/maia')

def test_get_maia_root_from_cwd():
    """Test MAIA_ROOT detection from CWD walk-up."""
    # Mock CWD with claude/ and .git/
    assert get_maia_root().name == 'maia'

def test_get_maia_root_fallback():
    """Test fallback to script location."""
    # When env not set and CWD walk-up fails
    assert 'maia' in str(get_maia_root())
```

**Test:** `test_repo_validator()`
```python
def test_validate_session_repo_passes():
    """Test validation passes when repo matches."""
    validator = RepositoryValidator()
    result = validator.validate_session_repo(session_file)
    assert result.passed is True

def test_validate_session_repo_fails_wrong_directory():
    """Test validation fails when CWD wrong."""
    # Session for team-maia, but CWD is maia
    validator = RepositoryValidator()
    result = validator.validate_session_repo(session_file)
    assert result.passed is False
    assert 'directory mismatch' in result.reason
```

### Integration Tests

**Test:** End-to-end multi-repo workflow
```python
def test_multi_repo_workflow():
    """Test complete workflow across both repos."""
    # 1. Start in personal repo
    os.chdir('/Users/username/maia')
    run_command('/init sre_principal_engineer_agent')

    # 2. Make changes and save
    run_command('save state')

    # 3. Verify commit went to personal repo
    assert get_last_commit_repo() == 'personal-github/maia'

    # 4. Switch to work repo
    os.chdir('/Users/username/team-maia')
    run_command('/init data_analyst_agent')

    # 5. Make changes and save
    run_command('save state')

    # 6. Verify commit went to work repo
    assert get_last_commit_repo() == 'work-github/team-maia'
```

**Test:** Cross-repo operation blocking
```python
def test_cross_repo_operation_blocked():
    """Test that operations are blocked across repos."""
    # 1. Start session in personal repo
    os.chdir('/Users/username/maia')
    session_id = start_session('personal_work')

    # 2. Switch to work repo WITHOUT closing session
    os.chdir('/Users/username/team-maia')

    # 3. Try to commit - should be BLOCKED
    result = run_command('save state')
    assert result.returncode == 1
    assert 'REPO VALIDATION FAILED' in result.output
```

---

## Success Metrics

### Functional Success
- ✅ 100% of git operations target correct repository
- ✅ Sessions correctly track repository context
- ✅ Cross-repo operations blocked by default
- ✅ Old sessions migrate without errors

### Performance Success
- ✅ Repo detection completes in <100ms
- ✅ Validation adds <50ms to operations
- ✅ No noticeable latency in session loading

### Safety Success
- ✅ Zero cross-repo commits in 30-day observation
- ✅ 100% of repo mismatches caught before commit
- ✅ Force override requires explicit confirmation

---

## Risks & Mitigations

**Risk 1: Breaking existing workflows**
- **Mitigation:** Backward compatibility mode for old sessions
- **Mitigation:** Gradual rollout with feature flag

**Risk 2: Performance degradation**
- **Mitigation:** Cache MAIA_ROOT detection per session
- **Mitigation:** Skip validation for read-only operations

**Risk 3: False positive blocks**
- **Mitigation:** Clear error messages with resolution steps
- **Mitigation:** `--force` override always available

**Risk 4: Migration complexity**
- **Mitigation:** Auto-migrate sessions on first load
- **Mitigation:** Keep old schema as fallback

---

## Open Questions

1. **Environment variable priority:** Should `MAIA_ROOT` env var override CWD detection?
   - **Recommendation:** Yes, env var = highest priority for explicit control

2. **Session sharing:** Should sessions be repo-specific or shared?
   - **Recommendation:** Repo-specific, no sharing across repos

3. **Database isolation:** Should each repo have separate capability/system DBs?
   - **Recommendation:** Yes, full isolation for data integrity

4. **Force override logging:** Should force overrides be logged/audited?
   - **Recommendation:** Yes, log to `claude/data/audit.log`

---

## Next Steps

1. **Review with user** - Validate requirements and approach
2. **Create TDD spec** - Write failing tests for core functionality
3. **Implement Phase 1** - `get_maia_root()` and `RepositoryValidator`
4. **Test in isolation** - Verify repo detection works both repos
5. **Implement Phase 2** - Update critical scripts
6. **Integration testing** - End-to-end multi-repo workflow
7. **Documentation** - Update CLAUDE.md with multi-repo guidance

---

## References

- **Files analyzed:**
  - `claude/tools/sre/save_state.py`
  - `claude/hooks/swarm_auto_loader.py`
  - `~/.maia/sessions/swarm_session_2963.json`
  - `claude/tools/learning/session.py`

- **Repositories:**
  - Personal: `/Users/username/maia` → `personal-github/maia`
  - Work: `/Users/username/team-maia` → `work-github/team-maia`

- **Related protocols:**
  - `claude/context/core/development_workflow_protocol.md`
  - `claude/context/core/tdd_development_protocol.md`
