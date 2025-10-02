# Statusline Command

## Purpose
Display current Maia system status with tool counts and health indicators.

## Usage
```
statusline [format]
```

## Formats
- `compact` (default) - Single line KAI-style status
- `detailed` - Multi-line detailed status display  
- `minimal` - Essential information only

## Implementation
```python
# This command uses the statusline_customization.py tool
python3 claude/tools/statusline_customization.py [format]
```

## Example Output
```
🤖 Maia | Claude 4 (Sonnet) | 📁 maia | 📋 28cmd | 👥 4agents | 🔗 7mcp | 📊 15ctx | Context: ✅ 100% | Git: main
```

## Integration
- Automatically called on Maia startup
- Available as slash command: `/statusline`
- Integrated with 4-layer enforcement system
- Updates when tools/agents are added or modified
