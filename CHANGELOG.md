# Changelog

All notable changes to Maia will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-XX

### Added
- Multi-user collaboration support
- CODEOWNERS-based protection model (three tiers: Protected, Domain, Open)
- CI/CD pipeline with quality gates
- `contribution_reviewer.py` for defense-in-depth validation
- Auto-labeling for PRs based on changed files
- Performance baseline monitoring tool
- Emergency rollback workflow
- Team setup script (`scripts/setup-team-member.sh`)
- PathManager for portable multi-user path resolution
- Agent validation tests
- Domain-specific CI workflows (SRE, Security)

### Changed
- Personal data moved to `~/.maia/`
- Session files moved to `~/.maia/sessions/`
- Database regeneration now happens locally (not committed)
- Extended `.gitignore` for multi-user patterns

### Security
- Pre-commit hooks block personal data and secrets
- CI scans for hardcoded paths and credentials
- Branch protection requires PR review
- Trufflehog secret detection in CI

## [1.x.x] - Previous

Single-user operation. See git history for details.
