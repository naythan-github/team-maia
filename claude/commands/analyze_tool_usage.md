# Analyze Tool Usage - Comprehensive Tool Portfolio Management

## Purpose
Comprehensive analysis and optimization of Maia's tool ecosystem using the tool usage monitoring system. Identifies unused tools, duplicates, and optimization opportunities.

## Command Execution

### Stage 1: Update Tool Inventory
**Agent**: System Maintenance
**Input**: Maia ecosystem directories
**Output**: Updated tool inventory database
**Action**: Scan all tools, commands, agents, FOBs, and MCP servers

```bash
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py update
```

### Stage 2: Generate Usage Analytics
**Agent**: Analytics Processor
**Input**: Usage logs and inventory data
**Output**: Comprehensive usage report
**Parameters**:
- `days`: Analysis period (default: 30 days)
- `include_details`: Show detailed breakdowns

```bash
# Generate 30-day usage report
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report 30

# Quick 7-day summary
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py report
```

### Stage 3: Duplicate Detection Analysis
**Agent**: Pattern Recognition
**Input**: Tool metadata and capabilities
**Output**: Potential duplicate tool groups
**Method**: Capability overlap and name similarity analysis

```bash
python3 ${MAIA_ROOT}/claude/tools/tool_usage_monitor.py duplicates
```

### Stage 4: Unused Tool Identification
**Agent**: Lifecycle Analyzer
**Input**: Usage patterns and timestamps
**Output**: Tools unused for specified period
**Criteria**: No usage events + old creation date

## Expected Output Format

### Tool Inventory Summary
```
📊 TOOL INVENTORY ANALYSIS
==========================
Total Tools Discovered: 127
- Python Tools: 45
- Commands: 23
- Agents: 15
- FOBs: 8
- MCP Servers: 3
```

### Usage Analytics
```
📈 USAGE ANALYTICS (Last 30 days)
=================================
Total Usage Events: 1,247
Success Rate: 94.2%

Most Used Tools:
1. jobs_agent (87 uses, 96% success)
2. batch_job_scraper.py (45 uses, 91% success)
3. research_topic (34 uses, 97% success)
```

### Duplicate Detection Results
```
⚠️  POTENTIAL DUPLICATES DETECTED
================================
Capability Overlap: email_processing, job_analysis
- enhanced_job_monitor.py (python_tool)
- automated_job_monitor.py (python_tool)
- job_email_processor.py (python_tool)

Name Similarity: 'monitor'
- agent_monitor.py
- efficiency_monitor.py
- enhanced_agent_monitor.py
- m4_hardware_monitor.py
- performance_monitoring_dashboard.py
```

### Unused Tools Report
```
🗑️  UNUSED TOOLS (30+ days, 0 usage)
====================================
High Priority for Review:
- old_linkedin_scraper.py (180 days, 0 uses)
- deprecated_email_parser.py (120 days, 0 uses)
- test_agent_v1.py (90 days, 0 uses)
```

## Optimization Recommendations

### Immediate Actions
1. **Archive Unused Tools**: Move tools unused >90 days to `/archived/`
2. **Merge Duplicates**: Consolidate overlapping capabilities
3. **Update Documentation**: Remove references to archived tools
4. **Refactor High-Usage Tools**: Optimize frequently used tools for performance

### Strategic Actions
1. **Capability Gaps**: Identify domains with low tool coverage
2. **Usage Patterns**: Build tools for commonly manual tasks
3. **Success Rates**: Investigate and improve error-prone tools
4. **Context Optimization**: Remove unused tools from context loading

## Tool Lifecycle Management

### Archival Process
```bash
# Create archive directory
mkdir -p ${MAIA_ROOT}/claude/tools/archived/$(date +%Y-%m)

# Move unused tool with metadata
mv [unused_tool] claude/tools/archived/$(date +%Y-%m)/
echo "Archived $(date): Reason - unused >90 days" >> claude/tools/archived/ARCHIVE_LOG.md
```

### Deprecation Process
```bash
# Mark as deprecated in tool header
sed -i '1i# DEPRECATED: Use [replacement_tool] instead' [tool_file]

# Update available.md
grep -v "[deprecated_tool]" claude/context/tools/available.md > temp && mv temp claude/context/tools/available.md
```

## Quality Gates
- Tool inventory accuracy >95%
- Usage tracking coverage >90% of tool invocations
- Duplicate detection false positive rate <10%
- Archival decisions require 60+ days unused + manual review

## Integration Points
- **Context Loading**: Remove archived tools from UFC system
- **Hook Integration**: Usage logger captures real-time tool usage
- **Documentation**: Update all references in commands and agents
- **Testing**: Validate replacement tools before archiving originals

## Command Chaining
This command chains with:
- `comprehensive_save_state` - Update documentation after optimization
- `design_decision_capture` - Document tool lifecycle decisions
- `ufc_compliance_checker` - Validate context system after changes

## Success Metrics
- Reduce tool inventory by 10-20% through archival
- Eliminate 80%+ of identified duplicates
- Improve context loading speed by removing unused tools
- Increase average tool usage frequency by consolidation
