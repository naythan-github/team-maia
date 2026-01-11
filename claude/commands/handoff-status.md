# Handoff Status Command

**Command**: `/handoff-status`
**Purpose**: Check automatic agent handoff system health and performance

---

## Execution Steps

### 1. Check Feature Flag Status
```bash
python3 -c "import json; d=json.load(open('claude/data/user_preferences.json')); print(f\"Handoffs enabled: {d.get('handoffs_enabled', False)}\")"
```

### 2. Read Recent Handoff Events
```bash
# Last 20 handoff events
tail -20 claude/data/handoff_events.jsonl 2>/dev/null || echo "No handoff events logged yet"
```

### 3. Generate Analytics Summary
```python
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

events_file = Path("claude/data/handoff_events.jsonl")
if not events_file.exists():
    print("No handoff events recorded yet. System is newly enabled.")
else:
    events = [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]

    # Last 24 hours
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    recent = [e for e in events if e.get("timestamp", "") > cutoff]

    # Analytics
    print(f"=== Handoff Analytics ===")
    print(f"Total events (all time): {len(events)}")
    print(f"Events (last 24h): {len(recent)}")

    # Common paths
    paths = Counter(f"{e.get('from_agent')} -> {e.get('to_agent')}" for e in events)
    print(f"\nTop handoff paths:")
    for path, count in paths.most_common(5):
        print(f"  {path}: {count}")

    # Success rate
    successes = sum(1 for e in events if e.get("success", True))
    print(f"\nSuccess rate: {successes}/{len(events)} ({100*successes/len(events):.1f}%)")
```

### 4. Check Current Session Handoff Chain
```bash
# Find current session and show handoff chain
python3 -c "
import json
from pathlib import Path

sessions_dir = Path.home() / '.maia' / 'sessions'
if sessions_dir.exists():
    sessions = sorted(sessions_dir.glob('swarm_session_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if sessions:
        session = json.loads(sessions[0].read_text())
        chain = session.get('handoff_chain', [])
        enabled = session.get('handoffs_enabled', False)
        print(f'Current session: {sessions[0].name}')
        print(f'Handoffs enabled: {enabled}')
        print(f'Current agent: {session.get(\"current_agent\")}')
        print(f'Handoff chain length: {len(chain)}')
        if chain:
            print(f'Chain: {\" -> \".join(str(h) if isinstance(h, str) else h.get(\"to\", \"?\") for h in chain)}')
"
```

---

## Output Format

```
=== Handoff System Status ===
Feature flag: ENABLED
Events logged: 42
Last 24h: 8 handoffs

Top paths:
  sre_principal -> security_specialist: 12
  dns_specialist -> azure_architect: 8

Success rate: 98.2%

Current session:
  Agent: sre_principal_engineer_agent
  Handoffs enabled: true
  Chain: [initial]
```

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| No handoffs occurring | Feature flag | Verify `handoffs_enabled: true` in user_preferences.json |
| Handoffs not logged | Events file | Check `claude/data/handoff_events.jsonl` exists and writable |
| Circular handoffs | Max limit | Check `handoffs_max` setting (default: 5) |
| Agent not found | Collaborations | Verify target agent has proper `_agent.md` file |

---

## Related Commands

- `/init` - Start session with handoff support
- `/close-session` - End session and capture handoff patterns
