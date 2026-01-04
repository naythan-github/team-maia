# /memory - Maia Memory Search

Search and browse your session history.

## Usage

```
/memory search <query>    - Search past sessions
/memory recent [n]        - Show N recent sessions (default 5)
/memory domain <name>     - Show sessions by domain
/memory context <query>   - Get relevant context for current task
```

## Examples

```
/memory search authentication
/memory recent 10
/memory domain sre
/memory context "fix memory leak"
```

## Implementation

When user invokes /memory, execute the appropriate MaiaMemory method:

```python
from claude.tools.learning.memory import get_memory

memory = get_memory()

# For /memory search <query>
results = memory.search(query, limit=10)

# For /memory recent [n]
results = memory.get_recent(limit=n)

# For /memory domain <name>
results = memory.get_by_domain(domain, limit=10)

# For /memory context <query>
context = memory.get_context_for_query(query)
```

## Output Format

### Search Results
```
## Session Search: "<query>"

### [date] - [initial_query]
**Status**: completed | **Agent**: sre_agent | **Domain**: sre
**Summary**: [summary_text]
---
```

### Recent Sessions
```
## Recent Sessions

| Date | Query | Agent | Domain | Status |
|------|-------|-------|--------|--------|
| 2026-01-04 | Fix auth bug | security_agent | security | completed |
```

## Storage

All data stored in `~/.maia/memory/`:
- `memory.db` - SQLite with FTS5 for search
- `summaries/` - Human-readable markdown files by date
