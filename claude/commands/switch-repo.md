# Switch Repository - Safe Multi-Repo Context Switching

**Purpose**: Gracefully switch between repositories (personal/work) with proper session cleanup
**Command**: `/switch-repo` | "switch repo" | "change repository"
**Status**: ✅ Production | **SPRINT-001-REPO-SYNC**: Multi-repo context awareness

---

## What It Does

Safely switches repository context by:
1. Running `/close-session` workflow (save uncommitted changes, capture learning)
2. Clearing MAIA_ROOT cache to detect new repository
3. Guiding user to switch directories manually
4. Prompting for new `/init` to start fresh session

## When to Use

| Scenario | Use `/switch-repo` |
|----------|-------------------|
| Switching from personal to work repo | ✅ Yes |
| Switching from work to personal repo | ✅ Yes |
| Working in same repo, different branch | ❌ No - just switch branches |
| Multiple Claude Code windows (different repos) | ❌ No - each has independent session |

## Workflow

```
USER: /switch-repo

ASSISTANT:
📋 Switching Repository Context...

Step 1: Closing current session
✅ Running /close-session workflow
  - Checking for uncommitted changes...
  - Capturing learning insights...
  - Cleaning up session file...

Step 2: Clearing repository cache
✅ MAIA_ROOT cache cleared

Step 3: Switch directories
📂 Current repository: /Users/username/maia (personal-github/maia)

Please run ONE of the following to switch:
  cd ~/team-maia              # Switch to work repo
  cd ~/maia                   # Switch to personal repo
  cd ~/path/to/other-maia     # Switch to another maia clone

Step 4: Start new session
After switching directories, run:
  /init [agent_name]

This will create a new session with correct repository context.

⚠️  Important: Repository validation is now active!
    - Sessions track repository context
    - Cross-repo git operations will be blocked
    - Use force=True only if intentionally working cross-repo
```

## Technical Details

### What Happens Behind the Scenes

1. **Close Current Session**:
   - Calls `close_session()` from `swarm_auto_loader.py`
   - Saves uncommitted changes (if user confirms)
   - Runs VERIFY + LEARN (PAI v2 learning)
   - Deletes `~/.maia/sessions/swarm_session_{CONTEXT_ID}.json`

2. **Clear Cache**:
   ```python
   from claude.tools.core.paths import clear_maia_root_cache
   clear_maia_root_cache()  # Next get_maia_root() will re-detect from CWD
   ```

3. **Guide User**:
   - Shows current repo (directory + git remote)
   - Provides `cd` commands for known repos
   - Reminds to run `/init` after switching

4. **Validation Ready**:
   - New session will capture new repo context
   - Repository validator will block cross-repo operations
   - Clean separation between repo contexts

## Validation Behavior After Switch

Once you switch repos and run `/init`, the new session will:
- ✅ Capture working directory, git remote URL, branch
- ✅ Validate git operations match new repo context
- ✅ Block accidental commits to wrong repository
- ✅ Provide clear error messages on repo mismatch

## Alternative: Manual Approach

If you prefer manual control:
```bash
# 1. Close session
/close-session

# 2. Switch directory
cd ~/team-maia

# 3. Clear cache manually (optional - auto-detects on next /init)
python3 -c "from claude.tools.core.paths import clear_maia_root_cache; clear_maia_root_cache()"

# 4. Start new session
/init sre_principal_engineer_agent
```

## Error Scenarios

### Uncommitted Changes
```
⚠️  Uncommitted changes detected:
    M  claude/tools/example.py
    A  tests/test_example.py

Options:
  1. Save changes first (recommended): Run "save state"
  2. Continue without saving: Type "skip"
  3. Cancel repo switch: Type "cancel"
```

### Active Session Without Repo Field (Legacy)
```
ℹ️  Legacy session detected (no repository tracking)
   This is expected for sessions created before SPRINT-001-REPO-SYNC.
   Closing session and switching repos normally...
```

## Related Commands

- `/close-session`: Clean shutdown (without repo switch)
- `/init [agent]`: Initialize new session with repository context
- `save state`: Commit changes before switching

## Implementation

**Function**: `switch_repository()` in `claude/hooks/swarm_auto_loader.py` (future enhancement)
**Current**: Manual workflow using existing `/close-session` + cache clearing
**Validation**: `claude/tools/sre/repo_validator.py`

---

**Sprint**: SPRINT-001-REPO-SYNC
**Story**: 6.2 - Create /switch-repo Command
**Created**: 2026-01-15
