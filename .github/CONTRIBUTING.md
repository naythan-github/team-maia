# Contributing to Maia

Welcome to Maia! This guide explains how to contribute effectively.

## Quick Start

```bash
# 1. Clone and setup
git clone git@github.com:ORG/maia.git
cd maia
./scripts/setup-team-member.sh

# 2. Create branch
git checkout -b feature/your-feature

# 3. Make changes, commit, push
git add .
git commit -m "feat: your feature description"
git push -u origin feature/your-feature

# 4. Create PR on GitHub
```

## Protection Tiers

| Tier | Paths | Approval Required |
|------|-------|-------------------|
| **Protected** | `claude/agents/`, `claude/hooks/`, `claude/context/core/`, `CLAUDE.md` | Core team |
| **Domain** | `claude/tools/sre/`, `claude/tools/security/`, etc. | Domain team + visibility |
| **Open** | `claude/extensions/`, `claude/tools/experimental/` | CI only |

## Branch Naming

| Pattern | Use |
|---------|-----|
| `feature/description` | New functionality |
| `fix/description` | Bug fixes |
| `docs/description` | Documentation only |
| `refactor/description` | Code improvement |

## Commit Messages

Use conventional commits:

```
feat: add new tool for X
fix: resolve issue with Y
docs: update README
refactor: simplify Z logic
test: add tests for W
```

## What Gets Checked

### Pre-Commit (Local)
- No personal data (usernames, home paths)
- No hardcoded secrets
- TDD compliance (if applicable)

### CI (Remote)
- All pre-commit checks
- Tests pass
- Linting passes
- Security scan (Trufflehog)
- Contribution review

## Development Workflow

1. **New tools** should start in `claude/tools/experimental/`
2. **Test thoroughly** before graduation to production
3. **Use TDD** - write tests first
4. **Update docs** when changing functionality

## Local Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific domain tests
python -m pytest tests/sre/ -v
python -m pytest tests/core/ -v

# Run contribution reviewer locally
python3 claude/hooks/contribution_reviewer.py --local -v

# Check performance baseline
python3 claude/tools/sre/performance_baseline.py --check
```

## Getting Help

- **Documentation**: This file + README.md
- **Questions**: #maia-support channel
- **Issues**: Create GitHub issue

## Code of Conduct

Be respectful. Help each other. Build great tools.
