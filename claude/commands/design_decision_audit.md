# Design Decision Audit Command

## Purpose
Systematic audit and improvement of design decision documentation across the Maia ecosystem to ensure future context windows can understand implementation rationale.

## Implementation Status
- **Current State**: ⚠️ Manual Process (Automated tool pending - Phase 103 Week 3)
- **Last Updated**: 2025-10-09 (Phase 103 - SRE Reliability Sprint)
- **Entry Point**: Manual review using template from save_state.md
- **Dependencies**: None (manual process)

## Usage

### Manual Design Decision Capture
Design decisions are now captured manually during save state using JSON template.

**Template** (from save_state.md):
```json
{
  "decision_id": "phase_NNN_decision_N",
  "date": "2025-MM-DD",
  "title": "Decision Title",
  "context": "Why was this decision needed?",
  "alternatives_considered": ["Option A", "Option B", "Option C"],
  "chosen_solution": "Option B",
  "rationale": "Why Option B was chosen",
  "trade_offs": "What we gave up choosing Option B",
  "validation": "How we know this was the right choice"
}
```

**Save to**: `claude/context/session/decisions/phase_NNN_decision_N.json`

### Manual Audit Process
```bash
# 1. List all decision files
find claude/context/session/decisions -name "*.json" -type f

# 2. Review each decision for completeness
# 3. Check that major phases have documented decisions
# 4. Verify alternatives and rationale are clear
```

## What Gets Audited

### Core Components Checked
- **Agents**: All active agents in `claude/agents/`
- **Tools**: Critical infrastructure tools in `claude/tools/`
- **Commands**: Advanced orchestration commands
- **System Infrastructure**: Hub, message bus, context manager

### Compliance Criteria
- ✅ Implementation Status documented
- ✅ Design Decisions section exists
- ✅ Current State vs planned clearly distinguished
- ✅ Entry Points and dependencies listed
- ✅ Trade-off analysis included

### Scoring System
- **90-100%**: Excellent documentation
- **70-89%**: Good, minor gaps
- **60-69%**: Adequate, needs improvement
- **<60%**: Critical gaps requiring immediate attention

## Design Decisions

### Decision 1: JSON + Markdown Dual Format
- **Chosen**: Store decisions in both JSON (structured) and Markdown (readable)
- **Alternatives Considered**: Pure markdown, pure JSON, database storage
- **Rationale**: JSON enables programmatic analysis while markdown provides human readability
- **Trade-offs**: Slight storage overhead but maximum flexibility for future tooling

### Decision 2: Component-Level Audit Focus
- **Chosen**: Audit individual component files for documentation compliance
- **Alternatives Considered**: Git history analysis, automated code scanning
- **Rationale**: Documentation quality is about human-readable rationale, not just code coverage
- **Trade-offs**: Manual effort required but higher quality insights

### Decision 3: Centralized Decision Registry
- **Chosen**: Single registry file tracking all decisions with metadata
- **Alternatives Considered**: Distributed files, git-based tracking
- **Rationale**: Enables system-wide impact analysis and relationship mapping
- **Trade-offs**: Single point of coordination but better visibility

## Expected Output

### Audit Report Format
```
🔍 Performing system-wide documentation audit...

📊 Audit Results (2025-01-07)
Overall Compliance: 73.4%
Components Audited: 12

🚨 Critical Gaps (3 components <60%)
  - claude/tools/some_tool.py: 45.2%
  - claude/agents/old_agent.md: 52.8%

💡 Recommendations
  - Priority focus on components with <60% compliance
  - Implement mandatory documentation review process
```

### Benefits
- **Context Preservation**: Future Maia instances understand "why" behind decisions
- **Quality Assurance**: Systematic identification of documentation gaps
- **Decision Tracking**: Centralized visibility into system evolution rationale
- **Process Improvement**: Template-driven decision capture

This command ensures Maia maintains high-quality decision documentation as the system evolves.