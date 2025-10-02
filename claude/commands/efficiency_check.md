# Efficiency Check Command

## Purpose
Analyze current session efficiency and provide token usage optimization recommendations.

## Usage
```
efficiency_check [operation_type] [file_count]
```

## Operation Types
- **edit**: Single or multi-file editing
- **search**: File searching and grep operations
- **scan**: System-wide scanning or analysis
- **git**: Git operations (commit, push, etc.)
- **analysis**: Code analysis or review

## Examples

### Check overall session efficiency
```
efficiency_check
```
→ Generates full efficiency report with metrics and recommendations

### Estimate specific operation
```
efficiency_check edit 5
```
→ Estimates tokens for editing 5 files

### Pre-operation planning
```
efficiency_check scan 100
```
→ Estimates system scan of 100 files, provides optimization strategy

## Output Format
```
🎯 Effort Estimate: [operation]
📊 Effort Level: LOW/MEDIUM/HIGH
🔢 Estimated Tokens: [number]
💡 Recommendation: [specific strategy]

## Efficiency Report
- Total tokens used in session
- Efficiency score (%)
- High-cost operations identified
- Redundant operations detected
- Specific recommendations for improvement
```

## Integration with Workflow

### Before starting work:
1. Run `efficiency_check [operation]` to estimate effort
2. Review recommendation for optimization strategy
3. Adjust approach if HIGH effort detected

### During work:
- Monitor for redundant operations
- Use state files for expensive analyses
- Batch operations when possible

### After major operations:
- Run `efficiency_check` to review session efficiency
- Identify areas for improvement
- Update approach for next session

## Efficiency Thresholds

| Effort Level | Token Range | Strategy |
|-------------|-------------|----------|
| LOW | < 50K | Direct execution |
| MEDIUM | 50K - 200K | Optimize with batching |
| HIGH | > 200K | Break across sessions |

## Best Practices

1. **Always estimate before HIGH effort operations**
2. **Save state before context might compress**
3. **Use search before read operations**
4. **Batch similar operations together**
5. **Review efficiency report at session end**

This command helps maintain optimal token usage while maximizing productivity.