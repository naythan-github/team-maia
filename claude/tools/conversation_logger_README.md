# Conversation Logger - Integration Guide

## Overview

The Conversation Logger captures Maia-user collaborative problem-solving conversations for weekly journey narratives and team knowledge sharing.

**Purpose**: Transform "show don't tell" conversations into shareable team learning content.

**Database Location**: `claude/data/databases/system/conversations.db` (pre-commit hook enforced)

## Architecture

### Data Schema

```python
{
  "journey_id": "uuid",
  "timestamp": "ISO 8601",
  "problem_description": "User's initial pain point",
  "initial_question": "Exact user query",
  "maia_options_presented": ["Option A", "Option B", "Option C"],
  "user_refinement_quote": "User's actual feedback",
  "agents_used": [
    {"agent": "SRE Principal Engineer", "rationale": "API validation", "started_at": "timestamp"},
    {"agent": "UI Systems Agent", "rationale": "Dashboard design", "started_at": "timestamp"}
  ],
  "deliverables": [
    {"type": "file", "name": "sma_api_discovery.py", "description": "...", "size": "9.8KB"},
    {"type": "documentation", "name": "Migration guide", "size": "9.8KB"}
  ],
  "business_impact": "95% time reduction (2 weeks → 5 min)",
  "meta_learning": "Discovered 'Assumption Testing' workflow pattern",
  "iteration_count": 2,
  "privacy_flag": true,  # DEFAULT TRUE (opt-in to sharing)
  "schema_version": 1
}
```

### Privacy Model

**Default**: `privacy_flag = True` (PRIVATE)
**Team Sharing**: Explicit opt-in via `mark_shareable(journey_id)`

**Rationale**: Privacy-first approach ensures sensitive information never accidentally shared.

## Usage Examples

### Basic Journey Lifecycle

```python
from claude.tools.conversation_logger import ConversationLogger

logger = ConversationLogger()

# 1. Start journey when user presents new problem
journey_id = logger.start_journey(
    problem_description="Need to migrate SonicWall VPN to Azure",
    initial_question="How do I migrate SonicWall SMA 500 VPN to Azure VPN Gateway?"
)

# 2. Log Maia's response options
logger.log_maia_response(
    journey_id=journey_id,
    options_presented=[
        "Option A: Manual migration using Azure Portal",
        "Option B: Automated toolkit with API discovery",
        "Option C: Hybrid approach with gradual transition"
    ]
)

# 3. Log user refinement
logger.log_user_refinement(
    journey_id=journey_id,
    refinement_quote="I like Option B but need to preserve existing firewall rules"
)

# 4. Track agents engaged
logger.add_agent(
    journey_id=journey_id,
    agent_name="SRE Principal Engineer",
    rationale="API validation and infrastructure design"
)

logger.add_agent(
    journey_id=journey_id,
    agent_name="Azure Migration Specialist",
    rationale="SonicWall-specific migration patterns"
)

# 5. Track deliverables created
logger.add_deliverable(
    journey_id=journey_id,
    deliverable_type="file",
    name="sma_api_discovery.py",
    description="SonicWall SMA API discovery and validation tool",
    size="9.8KB"
)

logger.add_deliverable(
    journey_id=journey_id,
    deliverable_type="documentation",
    name="Migration_Guide.md",
    description="Step-by-step SMA to Azure VPN migration guide",
    size="12.3KB"
)

# 6. Complete journey with impact metrics
logger.complete_journey(
    journey_id=journey_id,
    business_impact="95% time reduction (2 weeks manual → 5 min automated)",
    meta_learning="Discovered 'Assumption Testing' workflow: validate API access before building tools",
    iteration_count=2
)

# 7. Mark shareable for team (opt-in)
logger.mark_shareable(journey_id=journey_id)
```

### Weekly Retrieval (for narrative synthesis)

```python
# Get shareable journeys from last 7 days
journeys = logger.get_week_journeys(include_private=False)

for journey in journeys:
    print(f"Problem: {journey['problem_description']}")
    print(f"Impact: {journey['business_impact']}")
    print(f"Agents: {len(journey['agents_used'])} agents")
    print(f"Deliverables: {len(journey['deliverables'])} items")
    print()
```

### CLI Interface

```bash
# Start journey
python3 claude/tools/conversation_logger.py start "Migration problem" "How to migrate?"

# List shareable journeys
python3 claude/tools/conversation_logger.py list

# List all journeys (including private)
python3 claude/tools/conversation_logger.py list --include-private

# Mark journey shareable
python3 claude/tools/conversation_logger.py mark-shareable <journey_id>
```

## Integration Points

### 1. Integration with coordinator_agent.py

**When**: Coordinator agent orchestrates multi-agent workflows

**How**:

```python
from claude.tools.conversation_logger import ConversationLogger

class CoordinatorAgent:
    def __init__(self):
        self.logger = ConversationLogger()
        self.current_journey = None

    def handle_user_query(self, problem, question):
        # Start journey
        self.current_journey = self.logger.start_journey(
            problem_description=problem,
            initial_question=question
        )

    def present_options(self, options):
        # Log Maia's response
        if self.current_journey:
            self.logger.log_maia_response(
                journey_id=self.current_journey,
                options_presented=options
            )

    def engage_agent(self, agent_name, rationale):
        # Track agent engagement
        if self.current_journey:
            self.logger.add_agent(
                journey_id=self.current_journey,
                agent_name=agent_name,
                rationale=rationale
            )

    def track_deliverable(self, filepath, description):
        # Track file creation
        if self.current_journey:
            size = f"{os.path.getsize(filepath) / 1024:.1f}KB"
            self.logger.add_deliverable(
                journey_id=self.current_journey,
                deliverable_type="file",
                name=os.path.basename(filepath),
                description=description,
                size=size
            )
```

### 2. Integration with save_state.md Workflow

**File**: `claude/commands/save_state.md`

**Addition**: Add journey completion step

```markdown
## Save State Workflow

1. Complete documentation updates
2. Run tests
3. **NEW: Complete active journey (if exists)**
   ```python
   from claude.tools.conversation_logger import ConversationLogger
   logger = ConversationLogger()

   # Complete journey with impact
   logger.complete_journey(
       journey_id=current_journey_id,
       business_impact="<describe impact>",
       meta_learning="<insights discovered>",
       iteration_count=<iterations>
   )
   ```
4. Git commit and push
5. Update SYSTEM_STATE.md
```

### 3. Integration with Team Knowledge Sharing Agent

**When**: Weekly team update generation

**How**:

```python
from claude.tools.conversation_logger import ConversationLogger

def generate_weekly_narrative():
    logger = ConversationLogger()

    # Get shareable journeys from last week
    journeys = logger.get_week_journeys(include_private=False)

    # Synthesize into narrative
    narrative = f"# This Week with Maia - {date.today()}\n\n"

    for journey in journeys:
        narrative += f"## {journey['problem_description']}\n\n"
        narrative += f"**Challenge**: {journey['initial_question']}\n\n"

        if journey['agents_used']:
            agents = ", ".join([a['agent'] for a in journey['agents_used']])
            narrative += f"**Approach**: Engaged {agents}\n\n"

        if journey['deliverables']:
            narrative += f"**Deliverables**:\n"
            for d in journey['deliverables']:
                narrative += f"- {d['name']} ({d['size']}): {d['description']}\n"
            narrative += "\n"

        if journey['business_impact']:
            narrative += f"**Impact**: {journey['business_impact']}\n\n"

        if journey['meta_learning']:
            narrative += f"**Learning**: {journey['meta_learning']}\n\n"

        narrative += "---\n\n"

    return narrative
```

## Privacy Considerations for Team Sharing

### Privacy Flag Behavior

- **Default**: `privacy_flag = True` (PRIVATE)
- **Shareable**: `privacy_flag = False` (explicit opt-in)
- **Retrieval**: `get_week_journeys()` excludes private by default

### When to Mark Shareable

**SAFE to share**:
- Generic technical problems (migrations, integrations, optimizations)
- Workflow discoveries and meta-learning insights
- Tool/agent effectiveness demonstrations
- Architecture decisions and trade-offs

**DO NOT share** (keep private):
- Customer-specific data or configurations
- Security vulnerabilities before patching
- Sensitive business metrics or financials
- Personal information or credentials
- Pre-announcement features or strategies

### Recommendation Pattern

```python
def should_mark_shareable(journey_data):
    """
    Decision framework for marking journeys shareable.

    Returns: bool
    """
    # Check for sensitive keywords
    sensitive_patterns = [
        'password', 'credential', 'api_key', 'secret',
        'customer_name', 'revenue', 'salary', 'vulnerability'
    ]

    journey_text = json.dumps(journey_data).lower()

    if any(pattern in journey_text for pattern in sensitive_patterns):
        return False

    # Check if deliverables contain sensitive data
    if journey_data.get('deliverables'):
        for d in journey_data['deliverables']:
            if 'credentials' in d['description'].lower():
                return False

    # Default: mark shareable if passes filters
    return True
```

## Performance Validation

### Test Results

From `test_conversation_logger.py`:

- **Log operations**: <50ms (requirement: <50ms) ✅
- **Weekly retrieval**: <200ms (requirement: <200ms) ✅
- **Database path**: `databases/system/conversations.db` ✅
- **Graceful degradation**: Handles DB unavailable ✅

### Performance Characteristics

- **Database**: SQLite (file-based, ~20KB for empty DB)
- **Indexing**: Timestamp + privacy_flag indices
- **Atomic writes**: Each operation commits immediately
- **Concurrent updates**: Safe (SQLite ACID guarantees)
- **Scaling**: Tested with 10+ journeys, <200ms retrieval

## Error Handling

### Graceful Degradation

**Principle**: Conversation logging NEVER blocks user workflow

**Implementation**:
- Invalid DB path → Returns `None`, logs error
- Corrupt data → Resets to valid state, logs warning
- DB unavailable → Continues working, logs error
- All errors logged but not raised

**Example**:

```python
journey_id = logger.start_journey(problem, question)

if journey_id is None:
    # DB unavailable - continue without logging
    print("Note: Journey logging unavailable (continuing)")
else:
    # Log normally
    logger.add_agent(journey_id, agent_name, rationale)
```

## Testing

### Run Test Suite

```bash
# Run all tests
python3 -m pytest tests/test_conversation_logger.py -v

# Run specific test class
python3 -m pytest tests/test_conversation_logger.py::TestPrivacyFiltering -v

# Run with coverage
python3 -m pytest tests/test_conversation_logger.py --cov=claude.tools.conversation_logger
```

### Test Coverage

- Database schema validation ✅
- Conversation lifecycle (start → log → complete) ✅
- Multiple agents tracking ✅
- Deliverables tracking ✅
- Privacy filtering (default private, opt-in shareable) ✅
- Weekly retrieval (rolling 7 days) ✅
- Data integrity (atomic writes, concurrent updates) ✅
- Graceful degradation (DB unavailable, corrupt data) ✅
- Performance requirements (<50ms log, <200ms retrieval) ✅

## Troubleshooting

### Database Not Created

**Symptom**: No database file at expected path

**Solution**:
```bash
# Check parent directories exist
ls -la claude/data/databases/system/

# Create manually if needed
mkdir -p claude/data/databases/system/

# Test logger
python3 claude/tools/conversation_logger.py start "Test" "Test?"
```

### Pre-commit Hook Rejection

**Symptom**: `❌ Database not in claude/data/databases/ subdirectory`

**Solution**: Database MUST be at `claude/data/databases/system/conversations.db`

```python
# WRONG
db_path = "claude/data/conversations.db"

# CORRECT
db_path = "claude/data/databases/system/conversations.db"
```

### Performance Degradation

**Symptom**: Retrieval >200ms

**Check**:
```bash
# Count journeys
sqlite3 claude/data/databases/system/conversations.db \
  "SELECT COUNT(*) FROM conversations"

# Check indices
sqlite3 claude/data/databases/system/conversations.db \
  ".indices conversations"
```

**Solution**: If >1000 journeys, consider archival strategy:
```sql
-- Archive journeys >90 days old
DELETE FROM conversations
WHERE timestamp < datetime('now', '-90 days');
```

## Next Steps

### Phase 2: Narrative Synthesis (Team Knowledge Sharing Agent)

1. Read weekly journeys via `get_week_journeys()`
2. Synthesize into conversational narrative
3. Publish to Confluence via Confluence Organization Agent
4. Generate visual summaries (agent usage, deliverable types, impact metrics)

### Phase 3: Analytics Dashboard

- Agent engagement patterns
- Business impact trends
- Meta-learning insights catalog
- Privacy compliance reporting

## References

- **Implementation**: `claude/tools/conversation_logger.py`
- **Tests**: `tests/test_conversation_logger.py`
- **Database Schema**: `claude/data/databases/system/conversations.db`
- **Pre-commit Hook**: `claude/hooks/pre_commit_file_organization.py`
- **Development Decisions**: `claude/context/core/development_decisions.md` (Weekly Maia Journey Narrative System)

---

**Status**: Production-ready (26/26 tests passing, pre-commit hook compliant)
**Last Updated**: 2025-11-12
**Author**: SRE Principal Engineer Agent
