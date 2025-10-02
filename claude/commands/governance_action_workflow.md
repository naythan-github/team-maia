# Repository Governance Action Workflow

## Overview
Systematic workflow to execute actionable remediation of governance violations detected by the Repository Governance system.

## Phase 1: Violation Processing Pipeline

### Step 1: Generate Actionable Violation List
```bash
# Generate structured violation report with remediation mapping
python3 claude/tools/governance/repository_analyzer.py scan --output-format=remediation > /tmp/governance_violations.json
```

### Step 2: Execute Systematic Remediation
```bash
# Process violations with automated fixes
python3 claude/tools/governance/remediation_engine.py fix --input-file=/tmp/governance_violations.json --safe-mode=true
```

### Step 3: Validate Remediation Results
```bash
# Re-scan after fixes to measure improvement
python3 claude/tools/governance/repository_analyzer.py scan --compare-previous
```

## Phase 2: Root Directory Cleanup

### Priority Actions for 44→<20 Files:
1. **Move Configuration Files**: `.gitignore`, config files → `config/`
2. **Archive Old Files**: Timestamp-based files → `archive/historical/2025/`
3. **Consolidate Documentation**: README variants → single comprehensive README.md
4. **Project Organization**: Standalone projects → `projects/` with proper structure

### Automated Cleanup Command:
```bash
# Execute root directory cleanup with backup
python3 claude/tools/governance/root_directory_cleanup.py --target-files=20 --backup-mode=full
```

## Phase 3: Archive Consolidation

### Systematic Archive Management:
1. **Identify Scattered Archives**: Find all 18 misplaced archive directories
2. **Consolidate to Standard Location**: Move all to `archive/historical/YYYY/`
3. **Update Dependencies**: Fix any broken paths post-consolidation
4. **Validate Integrity**: Ensure no essential files lost

### Archive Consolidation Command:
```bash
# Consolidate all archives with dependency checking
python3 claude/tools/governance/archive_consolidator.py --dry-run=false --verify-dependencies=true
```

## Phase 4: Continuous Monitoring

### Automated Governance Maintenance:
```bash
# Set up filesystem monitoring for prevention
python3 claude/tools/governance/filesystem_monitor.py start --daemon-mode=true

# Schedule weekly governance health checks
crontab -e
# Add: 0 2 * * 1 python3 ${MAIA_ROOT}/claude/tools/governance/weekly_governance_audit.py
```

## Phase 5: Success Validation

### Key Metrics to Achieve:
- **Health Score**: 0.0 → 8.0+ (target: >7.0)
- **Root Files**: 44 → <20 files
- **Archive Organization**: 18 scattered → 1 consolidated location
- **Violation Count**: 19 → <5 violations

### Validation Commands:
```bash
# Complete governance assessment
python3 claude/tools/governance/repository_analyzer.py comprehensive-audit

# Dashboard metrics verification  
curl -s http://127.0.0.1:8070/api/metrics | jq '.file_counts.root_files'
```

## Implementation Strategy

### Immediate Actions (Next 30 minutes):
1. Create missing remediation pipeline tools
2. Execute root directory cleanup (safe mode)
3. Consolidate archive directories
4. Re-scan for validation

### System Integration:
- Connect analyzer output to remediation input
- Enable ML learning from remediation history
- Automate governance maintenance workflows
- Integrate with UDH dashboard for monitoring

## Safety Measures
- **Full Backup**: Complete system backup before any changes
- **Safe Mode**: Test all changes in dry-run mode first
- **Rollback Capability**: Maintain rollback scripts for all operations
- **Validation Gates**: Verify system integrity after each phase

This workflow transforms the governance system from detection-only to complete violation resolution with measurable improvement outcomes.