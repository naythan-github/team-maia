# Smart Context Loading Command

## Overview
Dynamic context loading system inspired by PAI architecture that reduces token usage by 12-62% while maintaining system capabilities.

## Usage

### Basic Smart Loading
```python
from claude.tools.dynamic_context_loader import smart_context_loading

# Analyze and load context intelligently
result = smart_context_loading("Research Microsoft Azure strategy")
context = result['context']
report = result['loading_report']

print(f"Loaded {len(context)} files")
print(f"Token savings: {report['estimated_token_savings']}")
```

### Context Analysis Only
```python
from claude.tools.dynamic_context_loader import analyze_context_loading

# Get loading statistics without loading
stats = analyze_context_loading("What is 2+2?")
print(f"Would load {stats['files_to_load']}/{stats['traditional_files']} files")
print(f"Estimated savings: {stats['estimated_savings']}")
```

### Command Line Interface
```bash
# Test context loading analysis
python3 claude/tools/dynamic_context_loader.py

# Analyze specific request
python3 -c "
import sys; sys.path.append('${MAIA_ROOT}')
from claude.tools.dynamic_context_loader import analyze_context_loading
stats = analyze_context_loading('$1')
print(f'Domain: {stats[\"domain\"]}')
print(f'Files: {stats[\"files_to_load\"]}/{stats[\"traditional_files\"]}')
print(f'Savings: {stats[\"estimated_savings\"]}')
"
```

## Loading Strategies

### MINIMAL (62% savings)
- **Core Only**: UFC + Identity + Model Strategy
- **Use Cases**: Simple math, basic questions, gratitude
- **Files**: 3/8 (claude/context/ufc_system.md, core/identity.md, core/model_selection_strategy.md)

### DOMAIN_SMART (12-37% savings)
- **Smart Loading**: Core + domain-specific context
- **Use Cases**: Research, security, financial, technical, cloud, design, personal
- **Files**: 5-7/8 (core + relevant domain files)

### FULL_TRADITIONAL (0% savings)
- **Complete Context**: All 8 mandatory files (current behavior)
- **Use Cases**: Complex multi-domain requests, low confidence detection
- **Files**: 8/8 (maintains existing functionality)

## Domain Detection

### Research Domain
**Triggers**: company, analyze, research, investigate, market, competitor, industry, trends
**Context**: available.md + agents.md + systematic_tool_checking.md

### Security Domain  
**Triggers**: security, audit, vulnerability, compliance, threat, risk, penetration, CVE
**Context**: available.md + agents.md + systematic_tool_checking.md

### Financial Domain
**Triggers**: financial, investment, tax, super, portfolio, cost, budget, money
**Context**: available.md + agents.md + profile.md

### Technical Domain
**Triggers**: code, program, develop, architecture, infrastructure, devops, monitor, performance
**Context**: available.md + agents.md + command_orchestration.md + systematic_tool_checking.md

### Cloud Domain
**Triggers**: azure, aws, cloud, kubernetes, terraform, migration, container
**Context**: available.md + agents.md + command_orchestration.md + profile.md

### Personal Domain
**Triggers**: schedule, calendar, email, task, productivity, workflow, personal
**Context**: profile.md + agents.md

### Design Domain
**Triggers**: design, UI, UX, interface, wireframe, mockup, prototype, usability  
**Context**: agents.md + command_orchestration.md

## Performance Metrics

### Token Savings by Request Type
- **Simple Math**: "2+2" → 62% savings (3/8 files)
- **Research**: "Research Microsoft" → 25% savings (6/8 files)  
- **Security**: "Audit security" → 25% savings (6/8 files)
- **Design**: "Design interface" → 37% savings (5/8 files)
- **Financial**: "Analyze portfolio" → 25% savings (6/8 files)
- **Personal**: "Schedule meeting" → 62% savings (3/8 files)

### Confidence Scoring
- **High Confidence (0.8-1.0)**: Use detected domain strategy
- **Medium Confidence (0.3-0.7)**: Use domain-smart loading with logging
- **Low Confidence (0.0-0.3)**: Fallback to full traditional loading

## Integration with Existing Systems

### UFC System Compatibility
- Maintains mandatory core context (UFC + Identity + Model Strategy)
- Preserves all existing functionality when full loading is used
- Backward compatible with traditional loading approach

### Agent System Integration
- Loads agent context based on detected domain requirements
- Ensures appropriate agents are available for domain-specific tasks
- Maintains orchestration capabilities when needed

### Tool Discovery Integration
- Loads systematic_tool_checking.md for domains requiring tool usage
- Ensures tool discovery framework is available when needed
- Preserves 4-layer enforcement for technical domains

## Best Practices

### When to Use Smart Loading
- ✅ Single-domain requests with clear patterns
- ✅ Simple tasks not requiring full system capabilities
- ✅ Performance-critical scenarios with token constraints
- ✅ Batch processing of similar request types

### When to Use Full Loading
- ❌ Multi-domain complex requests
- ❌ Uncertain or ambiguous request patterns  
- ❌ Critical system operations requiring all context
- ❌ New request types not yet pattern-matched

### Development Guidelines
- Test new request patterns with analyze_context_loading() first
- Monitor confidence scores to identify improvement opportunities
- Add new domain patterns based on usage analysis
- Maintain backward compatibility with full loading mode

## Future Enhancements

### Planned Improvements
1. **Machine Learning Integration**: Pattern learning from usage history
2. **Contextual Memory**: Remember user preferences for loading strategies
3. **Performance Monitoring**: Real-time token usage and savings tracking
4. **Adaptive Thresholds**: Dynamic confidence adjustment based on success rates

### Integration Opportunities
1. **Predictive Context Loader**: Enhanced with smart loading patterns
2. **KAI Integration Manager**: Smart context as KAI capability
3. **Cost Optimization System**: Integration with existing 99.7% savings
4. **Performance Analytics**: Dashboard integration for loading metrics

## Error Handling

### Graceful Fallbacks
- Missing context files → Log warning, continue with available files
- Import errors → Fallback to traditional full loading
- Pattern detection errors → Default to domain-smart loading
- File permission errors → Skip problematic files, load remainder

### Monitoring and Debugging
- Detailed logging of loading decisions and reasoning
- Performance metrics for token usage and response times
- Error tracking for failed file loads and pattern detection
- Usage analytics for optimization and improvement

---

**Status**: ✅ Phase 1 Implementation Complete
**Performance**: 12-62% token savings across different request types
**Integration**: Fully compatible with existing Maia architecture
**Next Phase**: Hierarchical Life Domain Organization