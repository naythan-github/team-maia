# Handoff System Operations Runbook

## Monitoring

### Check Handoff Success Rate
```python
from claude.tools.orchestration.swarm_integration import get_handoff_analytics

analytics = get_handoff_analytics(history, days=7)
print(f"Success Rate: {analytics['success_rate']*100:.1f}%")
print(f"Total Handoffs: {analytics['total_handoffs']}")
```

### View Common Handoff Paths
```python
for path in analytics['common_paths'][:5]:
    print(f"{path['from']} → {path['to']}: {path['count']} times")
```

### Check Event Logs
```bash
# Recent handoff events
tail -20 claude/data/handoff_events.jsonl | jq '.'

# Filter by type
grep "handoff_triggered" claude/data/handoff_events.jsonl | tail -10

# Count handoffs by agent
grep "handoff_triggered" claude/data/handoff_events.jsonl | jq -r '.to_agent' | sort | uniq -c | sort -nr
```

### View Active Sessions
```bash
ls -la ~/.maia/sessions/swarm_session_*.json
cat ~/.maia/sessions/swarm_session_*.json | jq '.handoff_chain'
```

### Query Pattern Learning Database
```python
from claude.tools.orchestration.pattern_learning import HandoffPatternTracker

tracker = HandoffPatternTracker()
patterns = tracker.get_patterns(days=30)
for pattern in patterns:
    print(f"{pattern['from']} → {pattern['to']}: {pattern['count']} times, {pattern['success_rate']*100:.1f}% success")
```

## Troubleshooting

### Problem: Handoffs Not Triggering

**Symptoms**: Agent completes without handing off when it should

**Diagnosis**:
1. Check feature flag: `is_handoffs_enabled()` should return True
2. Verify agent has Collaborations: `grep "Collaborations" claude/agents/{agent}.md`
3. Check handoff tools generated: `AgentRegistry().get(agent)["handoff_tools"]`
4. Verify session has handoffs_enabled: `cat ~/.maia/sessions/swarm_session_*.json | jq '.handoffs_enabled'`

**Resolution**:
- Enable feature flag in user_preferences.json: `{"handoffs_enabled": true}`
- Add Collaborations section to agent markdown
- Restart session: `rm ~/.maia/sessions/swarm_session_*.json`
- Check agent prompt includes handoff instructions

**Example Fix**:
```bash
# Enable handoffs
echo '{"handoffs_enabled": true}' > claude/data/user_preferences.json

# Verify agent has collaborations
grep "Collaborations" claude/agents/sre_principal_engineer_agent.md

# Restart session
rm ~/.maia/sessions/swarm_session_*.json
```

### Problem: Infinite Handoff Loop

**Symptoms**: Max handoffs reached, agents passing back and forth

**Diagnosis**:
1. Check handoff chain for circular pattern: `jq '.handoff_chain' session_file.json`
2. Review agent instructions for unclear boundaries
3. Check if agents have reciprocal collaborations without clear separation

**Resolution**:
- MaxHandoffsGuard automatically stops at limit (default: 5)
- Clarify agent specialties to reduce ambiguity
- Add explicit "do not hand off for X" instructions to agents
- Review handoff reasons in chain to identify issue

**Example Fix**:
```markdown
## Integration Points

**Collaborations**: Security Specialist (security audits only)

**DO NOT hand off for**: Performance analysis, code optimization (within SRE scope)
```

### Problem: Context Lost During Handoff

**Symptoms**: Target agent doesn't have information from source agent

**Diagnosis**:
1. Check session file for context field
2. Verify context injection is working: Debug orchestrator output
3. Check for truncation (>2000 chars)
4. Review tool call input: Does source agent pass context?

**Resolution**:
- Ensure source agent includes context in tool call input
- Check inject_handoff_context() output
- Increase context limits if needed (modify build_handoff_context)
- Review agent prompt to ensure it passes context

**Example Debug**:
```python
from claude.tools.orchestration.swarm_integration import IntegratedSwarmOrchestrator

orchestrator = IntegratedSwarmOrchestrator()
orchestrator.set_mock_responses([
    {"content": [{"type": "tool_use", "name": "transfer_to_target", "input": {"context": "Test context"}}]}
])

result = orchestrator.execute_with_handoffs("source", {"query": "Test"}, max_handoffs=1)
print(result.handoff_chain[0].get("context"))  # Should show "Test context"
```

### Problem: Agent Not Found Error

**Symptoms**: "Agent X not found in registry"

**Diagnosis**:
1. Verify agent file exists: `ls claude/agents/{name}_agent.md`
2. Check name conversion (spaces → underscores, lowercase)
3. Ensure file ends with `_agent.md`
4. Check Collaborations name matches file

**Resolution**:
- Create agent file if missing
- Fix Collaborations name format to match file
- Use exact agent name without suffix in Collaborations
- Verify name_to_filename() conversion

**Example**:
```bash
# Wrong: "Security Agent" → claude/agents/security_agent_agent.md (double agent)
# Right: "Security Specialist" → claude/agents/security_specialist_agent.md

grep "Collaborations" claude/agents/*.md
# Fix: Change "Security Agent" to "Security Specialist" in Collaborations
```

### Problem: Handoff Chain Not Updating Session

**Symptoms**: Session file doesn't show recent handoffs

**Diagnosis**:
1. Check file permissions: `ls -la ~/.maia/sessions/`
2. Verify add_handoff_to_session() is called
3. Check for write errors in logs
4. Ensure context_id is correct

**Resolution**:
- Fix permissions: `chmod 644 ~/.maia/sessions/*.json`
- Check session manager initialization
- Verify context_id matches between orchestrator and session
- Review exception handling in session_handoffs.py

### Problem: High Handoff Latency

**Symptoms**: Handoffs taking >1s to execute

**Diagnosis**:
1. Profile orchestrator execution
2. Check agent registry caching
3. Review API call times
4. Check session file I/O

**Resolution**:
- Agent registry caches automatically
- Use mock mode for testing to eliminate API latency
- Optimize context building for large contexts
- Consider async session updates

## Recovery Procedures

### Stuck Session
```bash
# Clear session and restart
rm ~/.maia/sessions/swarm_session_*.json

# Or manually edit to reset handoff chain
jq '.handoff_chain = []' session_file.json > tmp.json && mv tmp.json session_file.json
```

### Corrupted Session File
```bash
# Backup and recreate
mkdir -p ~/.maia/sessions/backup/
mv ~/.maia/sessions/swarm_session_*.json ~/.maia/sessions/backup/

# Next query will create fresh session
```

### Disable Handoffs Emergency
```python
# In user_preferences.json
{"handoffs_enabled": false}

# Or programmatically
from claude.tools.orchestration.feature_flags import disable_handoffs
disable_handoffs()
```

### Reset Pattern Learning Data
```bash
# Backup patterns database
cp claude/data/databases/intelligence/patterns.db claude/data/databases/intelligence/patterns.db.backup

# Clear handoff patterns (keeps schema)
sqlite3 claude/data/databases/intelligence/patterns.db "DELETE FROM handoff_patterns;"
```

## Performance Tuning

### Reduce Handoff Overhead
- Keep context concise (<2000 chars)
- Limit handoff chain depth (default max: 5)
- Use agent caching (AgentRegistry caches automatically)
- Mock API calls during testing

### Optimize Common Paths
- Review analytics for frequent handoffs
- Consider merging agents if always paired (>90% handoff rate)
- Pre-compute context for common workflows
- Add direct handoff instructions for known patterns

### Context Size Optimization
```python
# Example: Summarize context before handoff
def summarize_context(context, max_len=1500):
    if len(context) <= max_len:
        return context
    # Keep first 500 and last 1000 chars
    return context[:500] + "\n...\n" + context[-1000:]
```

## Health Checks

### Daily
- [ ] Check handoff success rate >95%
- [ ] Review failed handoff events in logs
- [ ] Verify no stuck sessions (sessions >24h old)
- [ ] Check event log size (<100MB)

### Weekly
- [ ] Analyze common handoff paths
- [ ] Review pattern learning effectiveness
- [ ] Check agent collaboration coverage (run agent_audit.py)
- [ ] Verify feature flag status matches expectations

### Monthly
- [ ] Audit agent Collaborations sections for accuracy
- [ ] Review and update handoff limits (max_handoffs)
- [ ] Performance benchmark validation (<1ms overhead)
- [ ] Archive old event logs (>90 days)

## Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Handoff success rate | >95% | <90% |
| Average handoff latency | <1ms | >10ms |
| Max handoffs hit rate | <5% | >20% |
| Circular handoffs | 0% | >1% |
| Session file write failures | 0% | >0% |
| Pattern learning capture rate | 100% | <95% |

## Alerting

### Setup Alerts
```python
# Example: Monitor handoff failures
from claude.tools.orchestration.feature_flags import log_handoff_event

def check_handoff_health():
    with open("claude/data/handoff_events.jsonl") as f:
        events = [json.loads(line) for line in f if "handoff_failed" in line]
        recent = [e for e in events if is_recent(e["timestamp"], hours=24)]
        if len(recent) > 10:
            alert("High handoff failure rate: {} failures in 24h".format(len(recent)))
```

### Common Alert Scenarios
1. **High failure rate**: >10 failures in 24h - investigate agent configurations
2. **Max handoffs exceeded**: >5 occurrences in 24h - review agent boundaries
3. **Session file errors**: Any write failures - check permissions
4. **Pattern learning gaps**: <95% capture rate - verify tracker initialization

## Debugging Tools

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from claude.tools.orchestration.swarm_integration import IntegratedSwarmOrchestrator
orchestrator = IntegratedSwarmOrchestrator()
# All internal operations now logged
```

### Trace Handoff Execution
```python
result = orchestrator.execute_with_handoffs(
    initial_agent="test_agent",
    task={"query": "Debug test"},
    max_handoffs=3
)

print("Handoff Chain:")
for i, handoff in enumerate(result.handoff_chain):
    print(f"{i+1}. {handoff['from']} → {handoff['to']}")
    print(f"   Reason: {handoff.get('reason', 'N/A')}")
    print(f"   Context: {handoff.get('context', 'N/A')[:100]}...")
```

### Test Handoff Flow
```python
# Unit test handoff detection
from claude.tools.orchestration.handoff_executor import HandoffDetector

detector = HandoffDetector()
response = {"content": [{"type": "tool_use", "name": "transfer_to_security_specialist", "input": {"context": "Test"}}]}
handoff = detector.detect_handoff(response)
assert handoff is not None
assert handoff["target"] == "security_specialist"
```
