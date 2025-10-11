# Agent A/B Testing Framework

**Purpose**: Measure agent prompt improvement impact through controlled experiments

**Source**: `claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md` Section 5

---

## Quick Start

### 1. Initialize Framework

```bash
python3 claude/tools/testing/agent_ab_testing_framework.py
```

This creates:
- Test scenario library (`.json` files in `claude/data/ab_tests/`)
- Example scenarios for DNS Specialist and SRE agents

### 2. Run A/B Test

```python
from claude.tools.testing.agent_ab_testing_framework import ABTestFramework, AgentResponse

# Initialize framework
framework = ABTestFramework()

# Load test scenarios
scenarios = framework.load_scenarios("dns_specialist")

# Run baseline agent (v1) and improved agent (v2) on scenarios
# (This step requires actual agent execution - see below)

# Compare results
result = framework.run_experiment(
    agent_name="dns_specialist",
    baseline_responses=baseline_responses,
    improved_responses=improved_responses,
    baseline_version="v1",
    improved_version="v2"
)

# Generate report
print(framework.generate_report(result))

# Save results
framework.save_results(result)
```

### 3. Review Recommendation

The framework will recommend:
- **Deploy**: >15% improvement + statistically significant (p<0.05)
- **Refine**: 10-15% improvement or needs larger sample
- **Reject**: <10% improvement or regression

---

## Quality Rubric (0-100 Scale)

Every agent response is scored on 5 dimensions:

### 1. Task Completion (40 points)
- ✅ Task fully resolved: 30 pts
- ⚠️ Task partially resolved: 15 pts
- ✅ Validation performed: 5 pts
- ✅ All requirements met: 5 pts

### 2. Tool-Calling Accuracy (20 points)
- ✅ Used tools correctly: 15 pts
- ⚠️ Used tools with errors: 7 pts
- ✅ No hallucinated tools: 5 pts

### 3. Problem Decomposition (20 points)
- ✅ Showed planning: 8 pts
- ✅ Systematic approach: 7 pts
- ✅ Considered edge cases: 5 pts

### 4. Response Quality (15 points)
- ✅ Clear communication: 7 pts
- ✅ Actionable recommendations: 5 pts
- ✅ Appropriate detail level: 3 pts

### 5. Persistence (5 points)
- ✅ Continued until resolved: 3 pts
- ✅ Proactive problem solving: 2 pts

**Total**: 100 points

**Grades**:
- **A (90-100)**: Excellent, production-ready
- **B (80-89)**: Good, minor improvements possible
- **C (70-79)**: Acceptable, needs refinement
- **D (60-69)**: Poor, significant gaps
- **F (<60)**: Unacceptable, major issues

---

## Test Scenario Library

### Creating Scenarios

Each test scenario includes:
- **ID**: Unique identifier (e.g., `dns_01`)
- **Description**: Short summary
- **User Prompt**: Actual user input
- **Expected Outcomes**: List of success criteria
- **Difficulty**: `simple`, `medium`, or `complex`
- **Domain**: Agent domain (e.g., `dns`, `sre`, `azure`)

Example:

```python
TestScenario(
    id="dns_02",
    description="Email deliverability crisis",
    user_prompt="URGENT: Our emails suddenly going to spam! Need immediate fix.",
    expected_outcomes=[
        "Checks SPF, DKIM, DMARC",
        "Identifies root cause",
        "Provides fix instructions",
        "No premature stopping"
    ],
    difficulty="complex",
    domain="dns"
)
```

### Recommended Scenario Mix

For each agent, create **20+ scenarios**:
- **Simple (30%)**: 6 scenarios - straightforward tasks
- **Medium (50%)**: 10 scenarios - typical real-world complexity
- **Complex (20%)**: 4 scenarios - edge cases, emergencies

This mix ensures:
- Statistical validity (20+ samples)
- Real-world representation
- Edge case coverage

---

## Statistical Analysis

### Two-Proportion Z-Test

Tests if completion rate improvement is statistically significant:

**Hypothesis**:
- H0: No difference between baseline and improved (p1 = p2)
- H1: Improvement exists (p1 ≠ p2)

**Decision Rules**:
- **p < 0.05**: 95% confidence - statistically significant
- **p < 0.10**: 90% confidence - marginally significant
- **p ≥ 0.10**: Not significant - may be random variation

### Sample Size Guidelines

- **Minimum**: 20 scenarios per variation (40 total)
- **Recommended**: 30 scenarios per variation (60 total)
- **High-stakes**: 50+ scenarios per variation (100+ total)

Larger samples increase statistical power and reduce false positives.

---

## Example A/B Test Report

```
================================================================================
A/B TEST REPORT: dns_specialist
================================================================================

Test Date: 2025-10-11T14:30:00
Comparison: v1 (baseline) vs v2_with_examples (improved)
Sample Size: 20 scenarios per variation

BASELINE PERFORMANCE (v1):
  - Average Quality Score: 62.5/100
  - Task Completion Rate: 65.0%
  - Average Execution Time: 8500ms

IMPROVED PERFORMANCE (v2_with_examples):
  - Average Quality Score: 86.3/100
  - Task Completion Rate: 90.0%
  - Average Execution Time: 9200ms

IMPROVEMENT ANALYSIS:
  - Quality Score: +38.1% ✅
  - Completion Rate: +38.5% ✅
  - Execution Time: +8.2% ⚠️

STATISTICAL SIGNIFICANCE:
  - P-value: 0.012
  - Significant: YES ✅
  - Confidence: 95%+

RECOMMENDATION: DEPLOY
Strong improvement (+38.1%) with statistical significance (p=0.012). Ready for production.

================================================================================
```

---

## Integration with Phase 107

### Week 3-4: A/B Testing Infrastructure (Task 1.3)

**Goal**: Validate that upgraded agents (v2) are better than baseline (v1)

**Process**:
1. **Create Scenarios** (4 hours)
   - 20 scenarios for DNS Specialist
   - 20 scenarios for SRE Principal Engineer
   - 10 scenarios for Azure Solutions Architect
   - 10 scenarios for Service Desk Manager
   - 10 scenarios for AI Specialists Agent

2. **Run Baseline Tests** (4 hours)
   - Execute v1 agents on scenarios
   - Score with quality rubric
   - Record execution time

3. **Run Improved Tests** (4 hours)
   - Execute v2 agents on same scenarios
   - Score with quality rubric
   - Record execution time

4. **Analyze Results** (2 hours)
   - Run statistical tests
   - Generate comparison reports
   - Document findings

5. **Make Deployment Decision** (2 hours)
   - Review recommendations
   - Validate with stakeholders
   - Deploy if approved

**Total**: 16 hours

---

## Files Created

### Framework
- `claude/tools/testing/agent_ab_testing_framework.py` - Core framework
- `claude/tools/testing/README.md` - This documentation

### Data
- `claude/data/ab_tests/` - Test data directory
- `claude/data/ab_tests/{agent}_scenarios.json` - Test scenarios per agent
- `claude/data/ab_tests/{agent}_ab_test_{timestamp}.json` - Test results

### Example Scenarios
- DNS Specialist: 3 scenarios (simple SPF check, email crisis, migration planning)
- SRE Principal Engineer: 2 scenarios (latency spike, metrics query)

---

## Next Steps

1. **Expand Scenario Library** (Target: 20+ per priority agent)
   - Add 17 more DNS scenarios
   - Add 18 more SRE scenarios
   - Add 10 Azure scenarios
   - Add 10 Service Desk scenarios
   - Add 10 AI Specialists scenarios

2. **Run Baseline Tests** (Execute v1 agents)
   - Load original agent prompts (pre-template upgrade)
   - Run on all scenarios
   - Score and record results

3. **Run Improved Tests** (Execute v2 agents)
   - Load upgraded agent prompts (post-template upgrade)
   - Run on same scenarios
   - Score and record results

4. **Statistical Analysis**
   - Compare baseline vs improved
   - Calculate p-values
   - Generate recommendations

5. **Deploy Winners**
   - Deploy agents with >15% improvement + p<0.05
   - Refine agents with 10-15% improvement
   - Iterate on rejected agents

---

## References

- **Source Document**: `claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md` Section 5
- **Phase 107 Plan**: `claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md` Task 1.3
- **Agent Template**: `claude/templates/agent_prompt_template_v2.md`
- **Example Library**: `claude/examples/few_shot_library.md`

---

## Contact

Questions or issues? Reference Phase 107 planning documents or AI Specialists Agent for meta-agent support.
