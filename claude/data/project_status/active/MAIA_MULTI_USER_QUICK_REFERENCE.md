# Maia Multi-User Quick Reference

**Full Plan**: [MAIA_MULTI_USER_ARCHITECTURE_PLAN.md](./MAIA_MULTI_USER_ARCHITECTURE_PLAN.md)

---

## TL;DR

**Goal**: Share Maia with team while keeping personal data private.

**Solution**: Git repository for shared tools/agents + `~/.maia/` for personal data.

**Effort**: ~32 hours implementation.

---

## What's Shared vs Private

| Shared (Git) | Private (~/.maia/) |
|--------------|-------------------|
| Tools, Agents, Commands | Personal profile |
| Core context & protocols | User preferences |
| Tests & documentation | Personal databases |
| Hooks & enforcement | Session state |
| SYSTEM_STATE.md | Checkpoints |

---

## How It Works

```
Team Member Laptop
├── ~/maia/              ← Git clone (shared code)
│   ├── claude/tools/    ← Everyone's tools
│   ├── claude/agents/   ← Everyone's agents
│   └── [tracked in Git]
│
└── ~/.maia/             ← Local only (never shared)
    ├── data/user_preferences.json
    ├── context/personal/profile.md
    └── data/databases/user/
```

---

## Contribution Flow

```
1. git checkout -b feature/my-improvement
2. Make changes, write tests
3. /review-contribution  ← Maia validates
4. git push + create PR
5. Review → Merge
```

---

## Database Strategy

**Don't share databases** - regenerate locally:
- `capabilities.db` → regenerated from tool/agent files
- `system_state.db` → regenerated from SYSTEM_STATE.md
- User databases → stay in ~/.maia/

**After git pull**: Post-merge hook auto-regenerates.

---

## Quick Commands

| Action | Command |
|--------|---------|
| Setup (first time) | `./scripts/setup-team-member.sh` |
| Check contribution | `/review-contribution` |
| Refresh databases | `/refresh-capabilities` |
| Create PR | `gh pr create --fill` |

---

## Quality Gates

1. **Pre-commit**: No personal data, TDD compliance, file organization
2. **Pre-push**: Maia review must pass
3. **CI**: Tests, security scan, architecture check
4. **Human**: Code owner approval required

---

## Key Files

| File | Purpose |
|------|---------|
| `.github/CODEOWNERS` | Who approves what |
| `.github/CONTRIBUTING.md` | How to contribute |
| `scripts/setup-team-member.sh` | Team onboarding |
| `claude/tools/contribution_reviewer.py` | Maia review system |

---

## Implementation Phases

| Phase | Effort | Description |
|-------|--------|-------------|
| 0. Prep | 2h | GitHub repo setup |
| 1. Structure | 4h | .github/ directory |
| 2. Paths | 4h | Update path resolution |
| 3. Quality | 8h | Review system |
| 4. Migration | 2h | Move personal data |
| 5. Database | 4h | Refresh system |
| 6. Docs | 4h | Team documentation |
| 7. Test | 4h | Validation |
| **Total** | **32h** | |

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Personal data leak | Pre-commit hook blocks |
| Database conflicts | DBs not in Git |
| Breaking changes | CI + code owner review |
| Setup confusion | Automated setup script |

---

**Questions?** See full plan or ask Naythan.
