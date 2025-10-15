# Agent Performance Dashboard

## Purpose
View real-time agent routing performance metrics including success rates, execution times, bottlenecks, and failure analysis.

## Usage
```bash
# View current dashboard
python3 claude/tools/orchestration/agent_performance_dashboard.py

# Watch mode (live updates every 5 seconds)
python3 claude/tools/orchestration/agent_performance_dashboard.py --watch

# JSON output (for scripting)
python3 claude/tools/orchestration/agent_performance_dashboard.py --format json
```

## What It Shows

### 📊 System Overview
- Total agent executions
- Number of unique agents used
- Overall success rate
- Average execution time

### 🤖 Agent Performance
Per-agent statistics showing:
- Total executions
- Success rate (✅ >95%, ⚠️ 80-95%, ❌ <80%)
- Average execution time
- Number of handoffs to other agents

### ⚠️ Performance Bottlenecks
Agents taking >2000ms on average:
- Slow agents identified
- Average execution time shown
- Helps prioritize optimization work

### ❌ Failure Analysis
- Total failure count and rate
- Failures by agent
- Common error types

### 🎯 Routing Strategy Effectiveness
- Single agent vs swarm performance
- Success rates by strategy
- Helps validate Phase 121 routing decisions

## When to Use

1. **After implementing Phase 121 routing** - Monitor how automatic routing is performing
2. **Performance debugging** - Identify slow agents
3. **Optimization planning** - Find agents needing improvement
4. **Success validation** - Verify agent quality

## Example Output

```
╭──────────────────────────────────────────────────────────────╮
│           🎯 MAIA AGENT PERFORMANCE DASHBOARD                │
│                    2025-10-15 22:00:00                       │
╰──────────────────────────────────────────────────────────────╯

📊 SYSTEM OVERVIEW
────────────────────────────────────────────────────────────────
  Total Executions:     45
  Unique Agents:        5
  Overall Success Rate: 95.6%
  Avg Execution Time:   1234ms

🤖 AGENT PERFORMANCE
────────────────────────────────────────────────────────────────
  ✅ financial_advisor
     Executions:  18 | Success: 100.0% | Avg Time:   1100ms | Handoffs: 2
  ✅ azure_solutions_architect
     Executions:  12 | Success: 91.7% | Avg Time:   1800ms | Handoffs: 5
...
```

## Integration with Phase 121

This dashboard monitors the automatic agent routing system implemented in Phase 121:
- Tracks which agents are being suggested
- Monitors acceptance rates
- Measures routing strategy effectiveness
- Identifies optimization opportunities

## Data Source

Metrics are collected by `claude/tools/orchestration/performance_monitoring.py` and stored in:
- Location: `claude/data/metrics/`
- Format: JSON files organized by date
- Retention: Configurable (default: 30 days)

## Notes

- Data starts accumulating once Phase 121 automatic routing is active
- First run will show test data from performance monitoring system
- Real routing data appears after queries trigger agent suggestions
- Watch mode requires terminal to stay open

## Future Enhancements

Planned improvements:
- Historical trend analysis
- Agent comparison reports
- Automated alerting for performance degradation
- Integration with monitoring dashboards
