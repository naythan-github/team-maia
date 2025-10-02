# Process Meeting Notes - Integrated Intelligence Pipeline

## Purpose
Transform raw meeting notes into structured intelligence with automatic action item extraction, decision tracking, and multi-system integration.

## Command Usage

### Basic Processing
```bash
# Process meeting notes from text input
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "Your meeting notes here..." \
  --title "Weekly Team Standup" \
  --participants "John,Sarah,Mike" \
  --type "standup"

# Process from file
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "/path/to/meeting_notes.txt" \
  --title "Architecture Review" \
  --date "2025-01-15" \
  --type "review"
```

### Full Integration Mode
```bash
# Process with all integrations enabled
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "meeting_notes.txt" \
  --title "Sprint Planning" \
  --participants "Team Lead,Product Owner,Developers" \
  --type "planning" \
  --integrate-kms \
  --document-confluence
```

### Action Item Management
```bash
# View all pending action items
python3 claude/tools/integrated_meeting_intelligence.py pending

# Update action item status
python3 claude/tools/integrated_meeting_intelligence.py update \
  --action-id "uuid-here" \
  --status "completed"

# Get meeting summary
python3 claude/tools/integrated_meeting_intelligence.py summary \
  --meeting-id "meeting-uuid-here"
```

## Meeting Types
- **standup**: Daily standups and check-ins
- **planning**: Sprint planning, project planning
- **review**: Sprint reviews, architecture reviews
- **decision**: Decision-making meetings
- **escalation**: Issue escalation meetings
- **general**: Other meeting types

## Integration Features

### 🔗 Knowledge Management System Integration
- Automatically adds action items to unified backlog
- Cross-session persistence
- Priority-based categorization
- Deadline tracking

### 📄 Confluence Documentation
- Structured meeting documentation
- Action items table with status tracking
- Decision records with rationale
- Meeting effectiveness scoring

### 💰 Cost Optimization
- Multi-LLM routing for 58.3% cost savings
- Local processing when possible
- Intelligent content analysis

## Output Structure

The pipeline extracts and structures:

### Action Items
- Clear task descriptions
- Owner assignments
- Due dates and priorities
- Dependencies and effort estimates
- Business impact assessment

### Decisions
- Decision titles and descriptions
- Rationale and decision makers
- Stakeholder impact analysis
- Risk and benefit assessment
- Implementation timelines

### Meeting Intelligence
- Key topics and themes
- Effectiveness scoring
- Follow-up meeting recommendations
- Stakeholder context mapping

## Engineering Manager Workflows

### Daily Operations
```bash
# Process daily standup
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "standup_notes.txt" \
  --type "standup" \
  --integrate-kms

# Check pending team actions
python3 claude/tools/integrated_meeting_intelligence.py pending
```

### Sprint Ceremonies
```bash
# Sprint planning with full documentation
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "sprint_planning.md" \
  --type "planning" \
  --integrate-kms \
  --document-confluence
```

### Executive Reporting
```bash
# Process leadership meeting with Confluence documentation
python3 claude/tools/integrated_meeting_intelligence.py process \
  --notes "leadership_sync.txt" \
  --type "decision" \
  --document-confluence
```

## Advanced Features

### Automatic Prioritization
- Critical: Urgent business decisions, blockers
- High: Sprint goals, key deliverables
- Medium: Process improvements, documentation
- Low: Nice-to-have enhancements

### Stakeholder Intelligence
- Relationship mapping
- Communication preferences
- Decision-making patterns
- Follow-up requirements

### Business Value Tracking
- Meeting ROI assessment
- Decision impact analysis
- Action item value scoring
- Team productivity metrics

## Integration with Existing Tools

### Teams Integration
- Automatic transcript processing
- Meeting metadata extraction
- Participant identification

### Personal Assistant Agent
- Follow-up scheduling
- Reminder automation
- Stakeholder notifications

### Dashboard Integration
- Real-time action tracking
- Team performance metrics
- Meeting effectiveness trends

This command transforms your meeting notes from information loss risk into systematic intelligence that drives accountability and execution.