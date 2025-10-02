# Dependency Repair Plan - Critical System Recovery

## Overview
Based on comprehensive dependency scan, the repository governance cleanup caused **CRITICAL_FAILURE** with 259 broken imports, 1,935 missing files, and 5,433 orphaned references. This plan provides systematic repair approach.

## Scan Results Summary
- **System Health Status**: CRITICAL_FAILURE
- **Broken Imports**: 259 (8 critical)
- **Missing Files**: 1,935
- **Orphaned References**: 5,433
- **System Integrity Issues**: 1

## Repair Strategy - 3 Phase Approach

### **PHASE 1: CRITICAL IMPORT RESTORATION (Priority: CRITICAL)**
**Objective**: Restore 8 critical modules that are breaking core functionality

#### Critical Modules to Restore:
1. `claude.tools.servicedesk_analytics_fob` - ServiceDesk analytics system
2. `claude.tools.backlog_manager` - Project management functionality  
3. `claude.tools.path_manager` - File path management
4. `claude.tools.advanced_documentation_intelligence` - Documentation processing
5. `claude.tools.m4_integration_manager` - M4 Neural Engine integration
6. `claude.tools.intelligent_rss_monitor` - RSS monitoring system
7. `claude.tools.rag_background_service` - RAG service functionality
8. Additional critical tools identified in scan

#### Repair Actions:
```bash
# Step 1: Identify archived locations
find archive/historical/2025/tools_old -name "*servicedesk*" -name "*.py"
find archive/historical/2025/tools_old -name "*backlog*" -name "*.py"
find archive/historical/2025/tools_old -name "*path_manager*" -name "*.py"

# Step 2: Restore to active locations
mv archive/historical/2025/tools_old/servicedesk_analytics_fob.py claude/tools/
mv archive/historical/2025/tools_old/servicedesk/ claude/tools/servicedesk/

# Step 3: Validate imports work
python3 -c "from claude.tools.servicedesk_analytics_fob import ServiceDeskAnalytics"
```

### **PHASE 2: SERVICEDESK FOB ECOSYSTEM RESTORATION (Priority: CRITICAL)**  
**Objective**: Restore complete ServiceDesk FOB ecosystem that powers analytics dashboard

#### ServiceDesk FOBs to Restore (9 files):
1. `servicedesk_analytics_fob.py` - Main analytics engine
2. `servicedesk/core_analytics_fob.py` - Core analytics functionality
3. `servicedesk/temporal_analytics_fob.py` - Time-based analysis
4. `servicedesk/client_intelligence_fob.py` - Client relationship analysis
5. `servicedesk/automation_intelligence_fob.py` - Automation opportunity detection
6. `servicedesk/training_intelligence_fob.py` - Skills gap analysis
7. `servicedesk/escalation_intelligence_fob.py` - Escalation pattern analysis
8. `servicedesk/base_fob.py` - Base FOB functionality
9. `servicedesk/orchestrator_fob.py` - FOB coordination

#### Repair Actions:
```bash
# Create ServiceDesk tools directory
mkdir -p claude/tools/servicedesk

# Restore all ServiceDesk FOBs
cp -r archive/historical/2025/tools_old/servicedesk_analytics_fob.py claude/tools/
cp -r archive/historical/2025/tools_old/servicedesk/* claude/tools/servicedesk/

# Validate ServiceDesk dashboard functionality
cd projects/analytics/servicedesk_dashboard_local
python3 app.py  # Should now work without import errors
```

### **PHASE 3: FILE REFERENCE REPAIR (Priority: HIGH)**
**Objective**: Fix 1,935 missing file references and update paths

#### High Priority File Reference Categories:
1. **Python Files**: 847 missing .py references
2. **Configuration Files**: 423 missing .json/.yaml references  
3. **Documentation Files**: 665 missing .md references

#### Repair Approach:
1. **Automated Path Updates**: Use find/replace for predictable patterns
2. **Manual Review**: Complex references requiring human judgment
3. **Deprecation**: Remove references to truly obsolete files

#### Repair Scripts:
```bash
# Update common path patterns
find . -name "*.py" -exec sed -i 's|claude/tools/servicedesk_analytics_fob|claude/tools/servicedesk_analytics_fob|g' {} \;
find . -name "*.py" -exec sed -i 's|from servicedesk_analytics_fob|from claude.tools.servicedesk_analytics_fob|g' {} \;

# Update project imports  
find projects/ -name "*.py" -exec sed -i 's|from claude.tools.servicedesk|from claude.tools.servicedesk|g' {} \;
```

## Implementation Sequence

### **Immediate Actions (Next 1 Hour)**
1. **Phase 1**: Restore 8 critical modules
2. **Validate**: Test critical imports work
3. **Phase 2**: Restore ServiceDesk FOB ecosystem  
4. **Test**: Verify ServiceDesk dashboard functionality

### **Short Term (Next 4 Hours)**
1. **Phase 3**: Begin systematic file reference repair
2. **Priority**: Focus on .py and .json references first
3. **Validation**: Test system integrity after each batch

### **Medium Term (Next Day)**
1. **Complete**: All high-priority file reference repairs
2. **Validation**: Comprehensive system testing
3. **Documentation**: Update system health metrics
4. **Prevention**: Integrate dependency scanning into governance

## Success Criteria

### **Phase 1 Success Metrics**
- [ ] All 8 critical imports resolve successfully
- [ ] No ImportError exceptions in critical modules
- [ ] ServiceDesk dashboard can import required modules

### **Phase 2 Success Metrics**  
- [ ] ServiceDesk Analytics Dashboard operational (http://localhost:5001)
- [ ] All 9 FOBs importable and functional
- [ ] FOB orchestrator can coordinate analytics pipeline

### **Phase 3 Success Metrics**
- [ ] <100 high-priority missing file references remaining
- [ ] All .py imports resolve correctly
- [ ] System health status improves from CRITICAL_FAILURE

### **Overall Success Metrics**
- [ ] System health status: CRITICAL_FAILURE → HEALTHY
- [ ] Broken imports: 259 → <10
- [ ] System integrity issues: 1 → 0
- [ ] All production dashboards functional

## Risk Mitigation

### **Backup Strategy**
- [ ] Create snapshot before any restore operations
- [ ] Maintain rollback capability for each phase
- [ ] Test in isolation before system-wide deployment

### **Validation Strategy**  
- [ ] Import testing after each module restoration
- [ ] Functional testing of restored components
- [ ] Integration testing with dependent systems

### **Monitoring Strategy**
- [ ] Re-run dependency scan after each phase
- [ ] Track improvement metrics in real-time
- [ ] Alert on any regression in system health

## Tools and Scripts

### **Repair Automation Scripts**
- `claude/tools/governance/dependency_scanner.py` - System scanning
- `claude/tools/governance/dependency_repair.py` - Automated repair execution
- `claude/commands/validate_system_integrity.md` - Validation procedures

### **Validation Commands**
```bash
# System health check
python3 claude/tools/governance/dependency_scanner.py scan

# Import validation
python3 -c "import claude.tools.servicedesk_analytics_fob"

# Dashboard functionality test
curl http://localhost:5001/api/health
curl http://127.0.0.1:8070/api/health
```

This systematic repair approach will restore system functionality while implementing proper dependency validation to prevent future breakage.