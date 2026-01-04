# Maia Initialization Command

Initialize Maia with guaranteed UFC + agent loading sequence.

## Usage
- `/init` - Load UFC + default/session agent
- `/init security` - Load UFC + security agent
- `/init sre` - Load UFC + SRE agent

## Protocol (ALWAYS in this order)

### Step 1: UFC System (MANDATORY)
Read and confirm: `claude/context/ufc_system.md`

### Step 2: Check Agent Session
```bash
# Get context ID first
CONTEXT_ID=$(python3 claude/hooks/swarm_auto_loader.py get_context_id)

# Check for session file
cat ~/.maia/sessions/swarm_session_${CONTEXT_ID}.json 2>/dev/null
```

### Step 3: Determine Agent
Priority order:
1. **Explicit request**: If user specified agent (e.g., `/init security`), load that agent
2. **Active session**: If session file exists, load `current_agent` from session
3. **Default preference**: Load from `claude/data/user_preferences.json` → `default_agent` field
4. **System fallback**: `sre_principal_engineer_agent`

### Step 4: Load Agent
Read: `claude/agents/{agent_name}.md` OR `claude/agents/{agent_name}_agent.md`

### Step 5: Create/Update Session
If no session exists OR agent changed, create session file:
```json
{
  "current_agent": "{agent_name}",
  "session_start": "{ISO timestamp}",
  "handoff_chain": ["{agent_name}"],
  "context": {},
  "domain": "{agent_domain}",
  "last_classification_confidence": 1.0,
  "query": "Manual init"
}
```

### Step 6: Confirm
Report:
- UFC loaded
- Agent active: {agent_name}
- Session: new/existing
- Context ID: {id}

## Key Rules
- UFC **ALWAYS** loads first - no exceptions
- Never skip UFC even when agent is explicitly requested
- Agent loading happens AFTER UFC confirmation
