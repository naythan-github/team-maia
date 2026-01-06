# Enhanced Learning Pattern Library
**Phase 237.3: Richer Learning Capture**

## Overview

The enhanced pattern library extends the original 5 learning types with 7 additional patterns, enabling richer and more nuanced learning capture from conversations.

### Pattern Categories

| Category | Count | Purpose |
|----------|-------|---------|
| **Original** | 5 | Core UOC patterns (decisions, solutions, outcomes, handoffs, checkpoints) |
| **Enhanced** | 7 | Advanced patterns (refactoring, error recovery, optimization, learning, breakthrough, test, security) |
| **Total** | 12 | Comprehensive learning taxonomy |

---

## Original Patterns (Phase 237.1)

### 1. Decision
**Purpose**: Captures explicit choices made with reasoning

**Confidence**: 0.9 (high)

**Patterns**:
- `decided to (\w+)`
- `chose (\w+) over (\w+)`
- `went with (\w+)`
- `using (\w+) because`
- `selected (\w+)`

**Example**:
```
"I decided to use SQLite because it requires no external service."
→ Learning captured with type='decision'
```

---

### 2. Solution
**Purpose**: Captures problem-solving approaches and fixes

**Confidence**: 0.95 (very high)

**Patterns**:
- `fixed (.*?) by (.*?)`
- `root cause was (.*?)`
- `resolved by (.*?)`
- `solved (.*?) with (.*?)`
- `debugged (.*?)`

**Example**:
```
"Fixed the timeout error by increasing the connection pool size."
→ Learning captured with type='solution'
```

---

### 3. Outcome
**Purpose**: Captures results of actions (success/failure)

**Confidence**: 0.85 (high)

**Patterns**:
- `✅.*?worked`
- `✅.*?complete`
- `✅.*?passed`
- `failed because (.*?)`
- `blocked by (.*?)`
- `error:? (.*?)`

**Example**:
```
"✅ Tests passed after implementing the fix."
→ Learning captured with type='outcome'
```

---

### 4. Handoff
**Purpose**: Captures agent transitions

**Confidence**: 1.0 (maximum - very specific pattern)

**Patterns**:
- `HANDOFF DECLARATION:`
- `To: (\w+)_agent`
- `handing off to (\w+)`

**Example**:
```
"HANDOFF DECLARATION:
To: python_code_reviewer_agent"
→ Learning captured with type='handoff'
```

---

### 5. Checkpoint
**Purpose**: Captures save points (commits, deploys, state saves)

**Confidence**: 0.9 (high)

**Patterns**:
- `save state`
- `git commit`
- `deployed to`
- `git push`
- `✅.*?committed`

**Example**:
```
"✅ Changes committed to repository"
→ Learning captured with type='checkpoint'
```

---

## Enhanced Patterns (Phase 237.3)

### 6. Refactoring
**Purpose**: Captures code quality improvements and cleanup

**Confidence**: 0.88 (high)

**PAI v2 Mapping**: workflow

**Patterns**:
- `refactor(?:ed|ing) (.*?)`
- `cleaned up (.*?)`
- `extracted (.*?) into (.*?)`
- `simplified (.*?)`
- `restructured (.*?)`

**Examples**:
```
"Refactored the authentication module to use dependency injection."
"Cleaned up duplicate code by extracting common logic."
"Simplified the error handling with a decorator pattern."
```

**Use Cases**:
- Code restructuring
- Removing duplication
- Improving readability
- Extracting abstractions

---

### 7. Error Recovery
**Purpose**: Captures error → fix sequences

**Confidence**: 0.92 (very high)

**PAI v2 Mapping**: tool_sequence

**Patterns**:
- `(?:encountered|caught) (.*?Error|.*?Exception)(.*?)`
- `handled (.*?) by (.*?)`
- `recovered from (.*?)`
- `exception (.*?) and (.*?)`

**Examples**:
```
"Encountered TypeError: cannot concatenate str and int. Fixed by adding explicit type conversion."
"Caught FileNotFoundError and handled it by creating the missing directory."
"Recovered from database lock by implementing retry logic."
```

**Use Cases**:
- Exception handling
- Error diagnosis
- Recovery strategies
- Defensive programming

---

### 8. Optimization
**Purpose**: Captures performance improvements

**Confidence**: 0.90 (high)

**PAI v2 Mapping**: tool_sequence

**Patterns**:
- `optimiz(?:ed|ing) (.*?)`
- `improved performance (.*?)`
- `reduc(?:ed|ing) (.*?) from (.*?) to (.*?)`
- `speed(?:ed)? up (.*?)`
- `increas(?:ed|ing) (.*?) by (.*?)`

**Examples**:
```
"Optimized database queries by adding an index, reducing query time from 2s to 50ms."
"Improved performance by implementing caching, reducing API calls by 80%."
"Sped up the build process with parallel compilation."
```

**Use Cases**:
- Performance tuning
- Latency reduction
- Throughput improvements
- Resource optimization

---

### 9. Learning
**Purpose**: Captures explicit insights and realizations

**Confidence**: 0.95 (very high - explicit learnings are highly valuable)

**PAI v2 Mapping**: workflow

**Patterns**:
- `learned that (.*?)`
- `realized that (.*?)`
- `understood that (.*?)`
- `discovered (.*?) works (.*?)`
- `found that (.*?)`

**Examples**:
```
"Learned that SQLite performs better for small datasets (<100K rows)."
"Realized that the bottleneck was in serialization, not the database."
"Understood that connection pooling is critical for high-traffic APIs."
```

**Use Cases**:
- Domain knowledge acquisition
- Best practice discovery
- Performance insights
- Architecture understanding

---

### 10. Breakthrough
**Purpose**: Captures major discoveries and key insights

**Confidence**: 0.98 (highest - breakthroughs are critical)

**PAI v2 Mapping**: workflow

**Patterns**:
- `breakthrough:? (.*?)`
- `key insight:? (.*?)`
- `discovered that (.*?)`
- `major finding:? (.*?)`
- `eureka:? (.*?)`

**Examples**:
```
"Breakthrough: Discovered that the memory leak was caused by circular references."
"Key insight: The issue only occurs when multiple threads access the cache simultaneously."
"Major finding: The vulnerability affects all versions before 2.5.0."
```

**Use Cases**:
- Critical problem solving
- Root cause analysis
- Architecture revelations
- Security discoveries

---

### 11. Test
**Purpose**: Captures testing-related learnings

**Confidence**: 0.87 (good)

**PAI v2 Mapping**: tool_sequence

**Patterns**:
- `added (.*?) tests? (.*?)`
- `test(?:ed|ing) (.*?)`
- `(?:test )?coverage (.*?)`
- `wrote tests? for (.*?)`
- `verify(?:ied|ing) (.*?) works (.*?)`

**Examples**:
```
"Added integration tests to verify the authentication flow works end-to-end."
"Increased test coverage from 75% to 95% by adding edge case tests."
"Wrote tests for all API endpoints with mock data."
```

**Use Cases**:
- Test strategy
- Coverage improvements
- Quality assurance
- Verification approaches

---

### 12. Security
**Purpose**: Captures security fixes and vulnerability handling

**Confidence**: 0.93 (very high - security is critical)

**PAI v2 Mapping**: tool_sequence

**Patterns**:
- `(?:fixed|patched) (.*?)vulnerability (.*?)`
- `(?:SQL injection|XSS|CSRF|security) (.*?)`
- `sanitiz(?:ed|ing) (.*?)`
- `(?:identified|found) (.*?)vulnerability (.*?)`
- `security (fix|patch|update) (.*?)`

**Examples**:
```
"Fixed SQL injection vulnerability by using parameterized queries."
"Identified XSS vulnerability in user input handling and sanitized all content."
"Security patch: Updated authentication to prevent CSRF attacks."
```

**Use Cases**:
- Vulnerability fixes
- Security hardening
- Attack prevention
- Compliance improvements

---

## Pattern Confidence Scoring

Confidence scores reflect pattern specificity and importance:

| Confidence Range | Interpretation |
|------------------|---------------|
| 0.95-1.0 | Highest priority (breakthrough, learning, solution, handoff) |
| 0.90-0.94 | Very high importance (error_recovery, optimization, security) |
| 0.85-0.89 | High confidence (refactoring, decision, outcome, test) |
| 0.70-0.84 | Good confidence (checkpoint, test) |
| <0.70 | Lower confidence (default fallback) |

**Confidence Boosting**:
- Patterns with multiple regex groups get +0.05 confidence
- More specific patterns (e.g., `chose X over Y because Z`) score higher

---

## Integration with PAI v2

Enhanced patterns map to PAI v2 pattern types:

| Extraction Type | PAI v2 Type | Rationale |
|----------------|-------------|-----------|
| decision, refactoring, learning, breakthrough, outcome, handoff, checkpoint | `workflow` | Represent workflow patterns and process knowledge |
| solution, error_recovery, optimization, test, security | `tool_sequence` | Represent tool usage patterns and technical sequences |

### Pattern Storage

When learnings are captured:
1. Extracted from conversation via regex patterns
2. Mapped to PAI v2 pattern type
3. Stored in `patterns` table with unique ID (`pat_abc123...`)
4. Pattern ID stored in `conversation_snapshots.learning_ids` for cross-reference

---

## Usage Examples

### Example 1: Multi-Pattern Conversation

```
Assistant: "Refactored the API handler to use async/await for better performance.
Optimized database queries, reducing latency from 500ms to 50ms.
Learned that connection pooling is critical for high-traffic APIs.
Fixed security vulnerability by adding CSRF token validation.
Added comprehensive test coverage for all endpoints."
```

**Patterns Captured**:
1. `refactoring`: "Refactored the API handler..."
2. `optimization`: "Optimized database queries, reducing latency..."
3. `learning`: "Learned that connection pooling..."
4. `security`: "Fixed security vulnerability..."
5. `test`: "Added comprehensive test coverage..."

---

### Example 2: Error Recovery Sequence

```
User: "The application is crashing on startup"
Assistant: "Encountered FileNotFoundError when loading config.
Debugged and found the config file path was incorrect.
Fixed by updating the path to use absolute paths instead of relative.
Added error handling to provide helpful message if config is missing.
Tested with various config scenarios to verify robustness."
```

**Patterns Captured**:
1. `error_recovery`: "Encountered FileNotFoundError..."
2. `solution`: "Debugged and found... Fixed by updating..."
3. `test`: "Tested with various config scenarios..."

---

## Testing

**Test Coverage**: 18 comprehensive tests for enhanced patterns

```bash
# Run enhanced pattern tests
python3 -m pytest tests/learning/test_extraction_enhanced.py -v

# Test specific pattern type
python3 -m pytest tests/learning/test_extraction_enhanced.py::test_extract_refactoring_pattern -v

# Run all learning tests (313 total)
python3 -m pytest tests/learning/ -v
```

---

## Performance

**Pattern Matching Performance**:
- 0.05s for 1000 messages (100x faster than 5s target)
- Regex patterns compiled once at initialization
- Efficient pattern matching with `finditer()`

**Storage Performance**:
- <100ms to store patterns in PAI v2 database
- Batch inserts for multiple learnings
- Indexed queries for fast retrieval

---

## Future Enhancements

### Phase 237.4: Analytics Dashboard
- Pattern frequency analysis
- Learning trends over time
- Most common pattern types
- Correlation between patterns

### Phase 237.5: Semantic Patterns
- LLM-based pattern detection
- Context-aware classification
- Custom pattern definitions per user

### Phase 237.6: Pattern Recommendations
- Suggest similar learnings from past conversations
- Pattern-based retrieval ("show me all optimizations")
- Learning reinforcement ("you've seen this pattern 3 times")

---

## References

- Pattern Implementation: [extraction.py](extraction.py)
- PAI v2 Bridge: [pai_v2_bridge.py](pai_v2_bridge.py)
- Tests: [test_extraction_enhanced.py](../../tests/learning/test_extraction_enhanced.py)
- Original Patterns: [PRECOMPACT_README.md](PRECOMPACT_README.md)

---

**Version**: 1.0 (Phase 237.3)
**Author**: Maia
**Date**: 2026-01-06
**Test Coverage**: 313 tests (312 passing)
**Pattern Count**: 12 types (5 original + 7 enhanced)
