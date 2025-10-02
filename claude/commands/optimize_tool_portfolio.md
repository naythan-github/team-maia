# Optimize Tool Portfolio - Systematic Tool Ecosystem Management

## Purpose
Execute systematic optimization of Maia's tool portfolio based on usage analytics. Performs archival, consolidation, and strategic improvements to reduce complexity and improve performance.

## Prerequisites
- Run `analyze_tool_usage` first to generate usage analytics
- Review duplicate detection results manually
- Backup current tool state before optimization

## Command Execution

### Stage 1: Prepare Optimization Environment
**Agent**: System Preparation
**Input**: Current tool inventory
**Output**: Backup and analysis prep

```bash
# Create optimization workspace
mkdir -p ${MAIA_ROOT}/claude/data/tool_optimization/$(date +%Y%m%d)
cd ${MAIA_ROOT}/claude/data/tool_optimization/$(date +%Y%m%d)

# Backup current state
cp -r ${MAIA_ROOT}/claude/tools/ ./tools_backup/
cp -r ${MAIA_ROOT}/claude/commands/ ./commands_backup/
cp -r ${MAIA_ROOT}/claude/agents/ ./agents_backup/

# Generate pre-optimization report
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report 60 > pre_optimization_report.txt
```

### Stage 2: Archive Unused Tools (Automated)
**Agent**: Lifecycle Manager
**Input**: Unused tools list (>60 days, 0 usage)
**Output**: Archived tools with metadata
**Safety**: Manual confirmation for tools with >5 dependencies

```bash
# Auto-archive safe tools (no dependencies, >90 days unused)
python3 -c "
from claude.tools.tool_usage_monitor import get_tool_monitor
import shutil
from pathlib import Path
from datetime import datetime, timedelta

monitor = get_tool_monitor()
unused = monitor.get_unused_tools(90)
archive_dir = Path('${MAIA_ROOT}/claude/tools/archived') / datetime.now().strftime('%Y-%m')
archive_dir.mkdir(parents=True, exist_ok=True)

for tool in unused:
    if tool['usage_count'] == 0 and 'test' in tool['name'].lower():
        print(f'Archiving: {tool[\"name\"]} - {tool[\"usage_count\"]} uses')
        # Archive logic here
"
```

### Stage 3: Consolidate Duplicate Tools (Manual Review)
**Agent**: Integration Specialist
**Input**: Duplicate detection results
**Output**: Consolidated tools with preserved functionality
**Method**: Merge capabilities, update references

```bash
# Generate consolidation plan
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py duplicates > consolidation_candidates.txt

echo "📋 CONSOLIDATION CANDIDATES"
echo "Review the following and select primary tool for each group:"
cat consolidation_candidates.txt
```

**Manual Consolidation Process:**
1. **Identify Primary Tool**: Choose most-used or most-complete tool
2. **Merge Capabilities**: Add unique features to primary tool
3. **Update References**: Search and replace in all files
4. **Test Consolidated Tool**: Verify all functionality preserved
5. **Archive Redundant Tools**: Move duplicates to archive

### Stage 4: Optimize High-Usage Tools
**Agent**: Performance Optimizer
**Input**: Most frequently used tools
**Output**: Performance-optimized tool implementations
**Focus**: Top 10 most-used tools

```bash
# Identify optimization candidates
python3 -c "
from claude.tools.tool_usage_monitor import get_tool_monitor
monitor = get_tool_monitor()
report = monitor.generate_usage_report(30)

print('🏆 OPTIMIZATION CANDIDATES (Top Usage)')
for tool_name, usage_count, tool_type in report['most_used_tools'][:5]:
    print(f'  {tool_name} ({tool_type}): {usage_count} uses - Review for optimization')
"
```

### Stage 5: Update Documentation and Context
**Agent**: Documentation Manager
**Input**: All optimization changes
**Output**: Updated context files and documentation
**Scope**: available.md, commands, agents, system state

```bash
# Update tools available documentation
python3 -c "
from claude.tools.tool_usage_monitor import get_tool_monitor
monitor = get_tool_monitor()
count = monitor.update_tool_inventory()
print(f'✅ Updated tool inventory: {count} active tools')
"

# Generate updated available.md section
echo '# Generating updated tools documentation...'
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report 1 | head -20
```

### Stage 6: Validate and Test Optimized Portfolio
**Agent**: Quality Assurance
**Input**: Optimized tool portfolio
**Output**: Validation report and test results

```bash
# Test tool discovery system
echo "🔍 Testing systematic tool discovery..."
python3 ${MAIA_ROOT}/claude/tools/systematic_tool_discovery.py research

# Validate context loading
echo "📚 Validating UFC context system..."
python3 ${MAIA_ROOT}/claude/hooks/pre_commit_ufc.py

# Generate post-optimization report
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report 7 > post_optimization_report.txt
```

## Optimization Metrics Tracking

### Before/After Comparison
```bash
# Compare portfolio metrics
echo "📊 OPTIMIZATION IMPACT ANALYSIS"
echo "================================"

BEFORE_COUNT=$(grep -c "^- " tools_backup/available.md 2>/dev/null || echo "unknown")
AFTER_COUNT=$(python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report 1 | grep "Total Tools" | cut -d: -f2 | tr -d ' ')

echo "Tool Count: $BEFORE_COUNT → $AFTER_COUNT"
echo "Reduction: $((BEFORE_COUNT - AFTER_COUNT)) tools archived/consolidated"
```

### Performance Metrics
- **Context Loading Speed**: Measure UFC system load time
- **Tool Discovery Speed**: Time to find relevant tools
- **Memory Usage**: Reduced context size in memory
- **Maintenance Overhead**: Fewer tools to maintain

## Safety Measures

### Rollback Procedure
```bash
# If optimization causes issues, rollback
cd ${MAIA_ROOT}/claude/data/tool_optimization/$(date +%Y%m%d)
rm -rf ${MAIA_ROOT}/claude/tools/
cp -r ./tools_backup/ ${MAIA_ROOT}/claude/tools/

echo "⚠️  ROLLBACK EXECUTED - Tool portfolio restored to pre-optimization state"
```

### Gradual Optimization
- **Phase 1**: Archive obvious unused tools (>120 days, 0 usage)
- **Phase 2**: Consolidate clear duplicates (identical capabilities)
- **Phase 3**: Optimize high-usage tools (performance improvements)
- **Phase 4**: Strategic portfolio restructuring

## Expected Outcomes

### Quantitative Improvements
- **10-25% reduction** in total tool count
- **15-30% faster** context loading
- **50-80% reduction** in duplicate functionality
- **20-40% fewer** tool discovery conflicts

### Qualitative Improvements
- **Cleaner tool landscape** - easier to find right tool
- **Reduced cognitive load** - fewer choices, clearer hierarchy
- **Better maintenance** - focus effort on actively used tools
- **Improved reliability** - consolidated tools are better tested

## Integration with System Architecture

### UFC System Updates
- Remove archived tools from context loading sequences
- Update systematic tool checking workflow
- Refresh domain-specific tool mappings

### Hook System Updates
- Update tool discovery enforcer with new inventory
- Modify usage logger to track optimization impact
- Ensure all enforcement mechanisms use current tool list

## Command Chaining
- **Prerequisite**: `analyze_tool_usage`
- **Follows**: `comprehensive_save_state` - Document all changes
- **Validates**: `ufc_compliance_checker` - Ensure system integrity
- **Monitors**: Ongoing usage tracking to measure optimization success
