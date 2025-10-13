# System Restoration & Portability Project

## Project Status: 95% Complete → Target 98%

**Last Updated**: October 13, 2025
**Priority**: HIGH (New laptop preparation)
**Estimated Effort**: 4-6 hours
**Current Confidence**: 85% → Target 95%

---

## Executive Summary

Maia achieved 95% portability in Phase 74 with zero-configuration path management. However, 4 critical gaps prevent seamless restoration to a new laptop: missing dependency manifest, undocumented credential setup, non-portable databases, and manual system service configuration.

**Business Impact**: Laptop replacement/failure could result in 8-16 hours of manual reconstruction vs. 1-2 hours with complete restoration infrastructure.

---

## Current State Analysis

### ✅ **What Works (95%)**

1. **Path Management System** (Phase 74)
   - Auto-detects installation location via `path_manager.py`
   - Tested across different usernames and directories
   - Zero environment variables required
   - **Status**: ✅ Production ready

2. **Version Control**
   - Git repository: https://github.com/naythan-orro/maia
   - All code versioned and backed up
   - **Status**: ✅ Production ready

3. **Core System Architecture**
   - 132 documentation files use `${MAIA_ROOT}` notation
   - 45 Python tools use path_manager API
   - **Status**: ✅ Production ready

### ⚠️ **Critical Gaps (5%)**

1. **Dependency Management**: No requirements.txt (manual package installation required)
2. **Credential Management**: API keys in macOS Keychain (not portable, undocumented)
3. **Database Portability**: Local databases excluded from git (rebuild required)
4. **System Services**: LaunchAgents have absolute paths (manual reconfiguration)

---

## Project Plan

### Phase 1: Dependency Management ⭐ **HIGH PRIORITY**

**Objective**: Create comprehensive dependency manifest for automated restoration

**Tasks**:
1. Generate Python requirements.txt
   - Option A: Use existing dependency scanner
   - Option B: Export from current environment
   - Include version pinning for reproducibility

2. Document system dependencies
   - macOS specific requirements (AppleScript, Keychain)
   - External tools (Ollama, ChromaDB, Whisper)
   - Optional vs. required dependencies

3. Create validation script
   - Check all dependencies present
   - Version compatibility verification
   - Environment health check

**Deliverables**:
- `/requirements.txt` - Python packages with pinned versions
- `/claude/docs/SYSTEM_DEPENDENCIES.md` - External tools and setup
- `/claude/tools/sre/dependency_validator.py` - Automated verification

**Success Metrics**:
- Fresh virtualenv + requirements.txt = working system
- Dependency conflicts: 0
- Manual intervention: 0

---

### Phase 2: Credential Management ⭐ **HIGH PRIORITY**

**Objective**: Document and streamline credential restoration process

**Tasks**:
1. Inventory all credentials
   - API keys (Trello, GitHub, Azure AD, OpenAI)
   - OAuth tokens (Gmail, LinkedIn)
   - Session cookies
   - SSH keys
   - Database passwords

2. Create credential setup guide
   - Step-by-step restoration instructions
   - Security best practices
   - Validation tests for each credential

3. Build credential setup wizard
   - Interactive guided setup
   - Credential validation
   - Keychain integration
   - Secure storage verification

**Deliverables**:
- `/claude/docs/CREDENTIALS_SETUP.md` - Complete credential inventory and setup
- `/claude/tools/setup/credential_wizard.py` - Interactive setup script
- `/claude/tools/setup/credential_validator.py` - Test credential functionality

**Success Metrics**:
- Complete credential inventory documented
- Setup wizard guides through all credentials
- Validation confirms all credentials working
- Setup time: <30 minutes

---

### Phase 3: Database Portability ⚠️ **MEDIUM PRIORITY**

**Objective**: Enable database backup/restore for seamless migration

**Tasks**:
1. Identify all databases
   - Email RAG ChromaDB (313 emails, Phase 80B)
   - Conversation RAG ChromaDB (Phase 101-102)
   - Career databases (SQLite)
   - System state tracking databases

2. Create export utilities
   - ChromaDB → JSON export
   - SQLite → SQL dump
   - Metadata preservation
   - Compression for large datasets

3. Build import/rebuild scripts
   - Automated database reconstruction
   - Data integrity verification
   - Performance optimization (parallel indexing)

4. Implement backup automation
   - Scheduled exports to cloud storage
   - Incremental backups
   - Retention policies

**Deliverables**:
- `/claude/tools/databases/export_all_databases.py` - Complete database export
- `/claude/tools/databases/import_all_databases.py` - Automated restoration
- `/claude/tools/databases/backup_scheduler.py` - Automated backup service
- `/backups/` - Database backup directory (git-ignored)

**Success Metrics**:
- All databases exportable to portable format
- Import completes successfully on fresh system
- Data integrity: 100% (checksums match)
- Backup automation running

---

### Phase 4: System Service Configuration ⚠️ **LOW PRIORITY**

**Objective**: Automate macOS system integration setup

**Tasks**:
1. Audit current system services
   - VTT Watcher LaunchAgent (Phase 83)
   - Health Monitor background services
   - Automation triggers
   - Scheduled tasks

2. Create LaunchAgent generator
   - Template-based generation
   - Auto-detects paths using path_manager
   - User/group configuration
   - Log rotation setup

3. Build service setup script
   - Install all LaunchAgents
   - Enable and start services
   - Verify service health
   - Logging configuration

**Deliverables**:
- `/claude/tools/setup/generate_launchagents.py` - Dynamic LaunchAgent creation
- `/claude/tools/setup/install_services.sh` - Service installation script
- `/claude/docs/SYSTEM_SERVICES.md` - Service documentation

**Success Metrics**:
- All services installable via script
- Services start automatically after reboot
- No hardcoded paths in service configs
- Service health monitoring active

---

### Phase 5: Master Restoration Orchestrator 🎯 **INTEGRATION**

**Objective**: Single-command restoration from git clone to working system

**Tasks**:
1. Create master setup script
   - Guided setup wizard
   - Dependency installation
   - Credential configuration
   - Database restoration
   - Service installation
   - Validation suite

2. Build restoration documentation
   - Pre-requisites (git, Python, Homebrew)
   - Step-by-step instructions
   - Troubleshooting guide
   - Rollback procedures

3. Testing on clean system
   - Fresh macOS VM testing
   - Different username testing
   - Different installation path testing
   - Performance validation

**Deliverables**:
- `/setup.py` - Master restoration orchestrator
- `/claude/docs/RESTORATION_GUIDE.md` - Complete restoration documentation
- `/claude/tools/sre/restoration_validator.py` - Post-setup validation suite

**Success Metrics**:
- Time to working system: <2 hours (vs. 8-16 hours manual)
- Success rate: 95%+ on fresh system
- User intervention: Minimal (credentials only)
- Validation pass rate: 100%

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| **Credential loss** | Medium | HIGH | Document + encrypted vault backup (1Password) |
| **Dependency version conflicts** | High | MEDIUM | Pin exact versions, test on multiple Python versions |
| **Database corruption during export** | Low | MEDIUM | Checksums, validation, incremental backups |
| **macOS version incompatibility** | Medium | LOW | Document minimum macOS version, test on multiple versions |
| **Path hardcoding regression** | Low | LOW | Git pre-commit hook enforcement (already exists) |
| **API breaking changes** | Low | MEDIUM | Version pin external services, document API versions |

---

## Implementation Timeline

### Week 1: Foundation (8 hours)
- **Day 1-2**: Phase 1 - Dependency Management (4 hours)
- **Day 3-4**: Phase 2 - Credential Management (4 hours)

### Week 2: Data & Services (6 hours)
- **Day 1-2**: Phase 3 - Database Portability (4 hours)
- **Day 3**: Phase 4 - System Services (2 hours)

### Week 3: Integration & Testing (6 hours)
- **Day 1-2**: Phase 5 - Master Orchestrator (4 hours)
- **Day 3**: Testing & Documentation (2 hours)

**Total Effort**: 20 hours
**Timeline**: 3 weeks (part-time)
**Urgency**: Medium (no immediate laptop replacement planned)

---

## Success Criteria

### Minimum Viable Restoration (Phase 1-2)
- [ ] requirements.txt exists and installs successfully
- [ ] Credentials documented and restorable
- [ ] Core system functional on new laptop
- **Target**: Manual restoration in <4 hours

### Complete Restoration (Phase 1-5)
- [ ] Single-command setup from git clone
- [ ] All databases restored automatically
- [ ] All services configured and running
- [ ] Validation suite passes 100%
- [ ] Documentation comprehensive
- **Target**: Automated restoration in <2 hours

### Enterprise-Grade (Stretch Goal)
- [ ] Automated testing on multiple macOS versions
- [ ] CI/CD pipeline for restoration testing
- [ ] Disaster recovery playbook
- [ ] Backup monitoring and alerting
- **Target**: 99% restoration success rate

---

## Resource Requirements

### Technical Resources
- **Development Environment**: Current Maia system for testing
- **Testing Environment**: Clean macOS VM or external drive boot
- **Backup Storage**: Cloud storage for database backups (Dropbox/iCloud)

### External Dependencies
- **Homebrew**: Package manager for macOS tools
- **Python 3.9+**: Core runtime environment
- **Git**: Version control and deployment
- **1Password/Bitwarden**: Credential vault for secure backup

### Documentation Standards
- Follow UFC system documentation patterns
- Use response format templates
- Update SYSTEM_STATE.md with progress
- Maintain portability_guide.md

---

## Maintenance Plan

### Ongoing Activities
1. **Dependency Updates**: Quarterly review and update requirements.txt
2. **Credential Audits**: Annual credential rotation and documentation review
3. **Backup Validation**: Monthly test database restore from backups
4. **Restoration Testing**: Quarterly full restoration test on clean system

### Monitoring Metrics
- **Backup Success Rate**: Target 100%
- **Backup Storage Usage**: Monitor and optimize
- **Restoration Test Results**: Track success rate trends
- **Time to Restore**: Measure and optimize

### Documentation Updates
- Keep RESTORATION_GUIDE.md current with system changes
- Update SYSTEM_DEPENDENCIES.md when adding new tools
- Maintain CREDENTIALS_SETUP.md with API changes
- Document all restoration test results

---

## Related Projects

- **Phase 74**: Portability Foundation (100% path management)
- **Phase 78**: Security Scanner Suite (dependency management patterns)
- **Phase 101-102**: Conversation RAG (database portability patterns)
- **Anti-Breakage Protocol**: System preservation and validation

---

## Appendix: Current State Metrics

### Portability Scorecard
| Category | Score | Status |
|----------|-------|--------|
| **Core System** | 100% | ✅ Complete |
| **Path Management** | 100% | ✅ Complete |
| **Documentation** | 95% | ⚠️ 178 cosmetic path references |
| **Dependencies** | 0% | ❌ No requirements.txt |
| **Credentials** | 0% | ❌ Undocumented |
| **Databases** | 0% | ❌ Not portable |
| **Services** | 50% | ⚠️ Manual setup required |
| **Overall** | 95% | ⚠️ 4 gaps preventing full restoration |

### Files Requiring Attention
- **178 occurrences** of `/Users/naythandawe` across 72 files (cosmetic, non-blocking)
- **0 requirements.txt** files (blocking)
- **0 credential documentation** (blocking)
- **Database backups**: Manual only (blocking)

---

## Next Steps

### Immediate Actions (This Week)
1. Generate requirements.txt from current environment
2. Create credential inventory spreadsheet
3. Test database export utilities

### Short-term Goals (This Month)
1. Complete Phase 1-2 (Dependencies + Credentials)
2. Document minimum viable restoration process
3. Test restoration on external drive

### Long-term Goals (This Quarter)
1. Complete all 5 phases
2. Test on clean macOS VM
3. Achieve 98% restoration confidence
4. Document lessons learned in SYSTEM_STATE.md

---

**Project Owner**: Maia System
**Stakeholder**: User (naythandawe)
**Priority**: HIGH
**Status**: Planning Complete → Ready for Execution
