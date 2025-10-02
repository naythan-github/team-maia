# Documentation Standards - Maia System

## Purpose
Establish consistent documentation practices that capture not just "what" but "why" for all system components, ensuring future context windows can understand implementation decisions.

## Core Principles
1. **Decision Transparency**: Every technical choice must be documented with rationale
2. **Current State Truth**: Documentation reflects actual implementation, not aspirational design
3. **Context Preservation**: Future agents should understand why decisions were made
4. **Implementation Status**: Clear distinction between planned, in-progress, and deployed components

## Mandatory Documentation Elements

### System Components
Every agent, command, or tool must include:

```markdown
## Implementation Status
- **Current State**: [Deployed/In Development/Planned/Deprecated]
- **Last Updated**: [Date]
- **Entry Point**: [Primary script/command/endpoint]
- **Dependencies**: [Required services/credentials/files]

## Design Decisions
### Decision 1: [Technology Choice]
- **Chosen**: [Selected option]
- **Alternatives Considered**: [Other options evaluated]
- **Rationale**: [Why this choice was made]
- **Trade-offs**: [What was gained/lost]

### Decision 2: [Architecture Choice]
- **Chosen**: [Selected approach]
- **Alternatives Considered**: [Other approaches evaluated]
- **Rationale**: [Why this approach was made]
- **Trade-offs**: [What was gained/lost]
```

### Command Documentation
Commands must specify:
- **Actual Implementation**: Which scripts/tools are used
- **Authentication Method**: How credentials are managed
- **Data Flow**: Inputs → Processing → Outputs
- **Error Handling**: Fallback mechanisms
- **Integration Points**: How it connects with other components

### Agent Documentation
Agents must specify:
- **Primary Capabilities**: What it actually does (not theoretical)
- **Tool Dependencies**: Which specific tools/scripts it uses
- **Data Sources**: Where it gets information
- **Output Format**: How it delivers results
- **Collaboration Patterns**: How it works with other agents

## Documentation Quality Gates

### Before Deployment
- [ ] Implementation status clearly stated
- [ ] All major design decisions documented with rationale
- [ ] Current vs planned functionality distinguished
- [ ] Dependencies explicitly listed
- [ ] Integration points mapped

### Quarterly Review
- [ ] Implementation status updated
- [ ] Deprecated components marked
- [ ] New design decisions added
- [ ] Trade-off assessments reviewed
- [ ] Context relevance validated

## Anti-Patterns to Avoid
- ❌ Documenting intended functionality without implementation status
- ❌ Technical choices without explaining rationale
- ❌ Commands that reference tools not actually used
- ❌ Generic descriptions without specific implementation details
- ❌ Missing authentication or dependency information

## Examples

### Good Documentation Example
```markdown
## Implementation Status
- **Current State**: Deployed
- **Entry Point**: `/claude/tools/automated_job_monitor.py`
- **Dependencies**: Gmail API credentials, SQLite database
- **Cron Schedule**: 9am & 1pm weekdays

## Design Decisions
### Decision 1: Gmail API vs Zapier MCP
- **Chosen**: Gmail API with `gmail_job_fetcher.py`
- **Alternatives Considered**: Zapier MCP integration
- **Rationale**: Direct API control allows custom rate limiting, offline processing, and complex email parsing
- **Trade-offs**: More complex authentication setup, but zero external dependencies
```

### Bad Documentation Example
```markdown
## Purpose
Process job emails and analyze opportunities

## Workflow
1. Get job emails
2. Score opportunities
3. Send notifications
```

## Implementation Notes
- All existing system documentation should be audited against these standards
- New components must follow these standards from creation
- Context files should reference specific implementation status when describing capabilities
- Session notes should capture design rationale decisions made during development

This ensures future Maia context windows can understand current implementation reality and the reasoning behind technical choices.