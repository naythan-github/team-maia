# Phase 4: Optimization & Automation - Complete Guide

**Created**: 2025-10-12
**Status**: Complete (4/4 components)
**Purpose**: Continuous improvement infrastructure for production Maia system

---

## Overview

Phase 4 implements automated systems for measuring, testing, and improving agent performance without human intervention. This infrastructure must be in place BEFORE production deployment to collect metrics from day 1.

**Key Components**:
1. **Automated Quality Scorer** - Rubric-based evaluation (0-100 scores)
2. **A/B Testing Framework** - Statistical experimentation infrastructure
3. **Experiment Queue System** - Priority-based experiment scheduling
4. **Integration Documentation** - Complete usage guide (this document)

---

## Architecture

```
Phase 4: Optimization & Automation
├── Automated Quality Scorer
│   ├── 5-criteria rubric (weighted scoring)
│   ├── Automatic evaluation (0-100)
│   ├── Score persistence (JSONL)
│   └── Historical tracking & averages
│
├── A/B Testing Framework
│   ├── Deterministic 50/50 assignment (MD5 hashing)
│   ├── Statistical analysis (Z-test, Welch's t-test)
│   ├── Automatic winner promotion (>15% + p<0.05)
│   └── Experiment lifecycle management
│
├── Experiment Queue System
│   ├── Priority-based scheduling (high/medium/low)
│   ├── Max 3 concurrent experiments
│   ├── Auto-promotion from queue
│   └── Complete experiment history
│
└── Integration Layer
    ├── Quality scores feed A/B tests
    ├── A/B tests use experiment queue
    └── Results inform agent upgrades
```

---

## 1. Automated Quality Scorer

**File**: `claude/tools/sre/automated_quality_scorer.py` (594 lines)

### Purpose
Automatically evaluate agent responses using a standardized rubric with 5 weighted criteria.

### Rubric Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Task Completion** | 40% | Requirements addressed, validation performed, edge cases considered |
| **Tool Accuracy** | 20% | Correct tools used, parameters valid, no redundancy |
| **Decomposition** | 20% | Systematic planning, logical breakdown, clear phases |
| **Response Quality** | 15% | Clear explanations, appropriate detail, well-structured |
| **Efficiency** | 5% | Token usage, execution time, minimal redundancy |

### Usage

```python
from claude.tools.sre.automated_quality_scorer import AutomatedQualityScorer

# Initialize scorer
scorer = AutomatedQualityScorer()

# Evaluate a response
response_data = {
    "status": "completed",
    "requirements": ["req1", "req2", "req3"],
    "addressed_requirements": ["req1", "req2", "req3"],
    "validation_performed": True,
    "edge_cases_considered": True,
    "tools_used": ["correct_tool_1", "correct_tool_2"],
    "expected_tools": ["correct_tool_1", "correct_tool_2"],
    "systematic_planning": True,
    "logical_breakdown": True,
    "explanation_quality": "excellent",
    "token_count": 500,
    "execution_time_seconds": 5.0
}

score = scorer.evaluate_response(
    response_data=response_data,
    agent_name="cloud_architect",
    response_id="response_001"
)

print(f"Overall Score: {score.overall_score}/100")
print(f"Task Completion: {score.criteria_scores['task_completion']}/100")
print(f"Tool Accuracy: {score.criteria_scores['tool_accuracy']}/100")
```

### Score Interpretation

- **90-100**: Exceptional performance (ideal target)
- **75-89**: Good performance (production ready)
- **60-74**: Acceptable performance (needs monitoring)
- **<60**: Poor performance (requires intervention)

### Score Persistence

Scores are automatically saved to:
```
claude/context/session/quality_scores/{response_id}.json
```

### Historical Analysis

```python
# Get average score over last 7 days
avg_score = scorer.get_average_score(
    agent_name="cloud_architect",
    time_window_days=7
)

print(f"7-day average: {avg_score}/100")
```

---

## 2. A/B Testing Framework

**File**: `claude/tools/sre/ab_testing_framework.py` (569 lines)

### Purpose
Run controlled experiments comparing prompt variants (control vs treatment) with statistical rigor.

### Features

1. **Deterministic Assignment**: MD5 hashing ensures consistent user assignment (50/50 split)
2. **Statistical Analysis**: Two-proportion Z-test + Welch's t-test
3. **Automatic Winner Promotion**: Promotes treatment if >15% improvement AND p<0.05
4. **Experiment Lifecycle**: Draft → Active → Completed → Promoted

### Usage

#### Create Experiment

```python
from claude.tools.sre.ab_testing_framework import ABTestingFramework
from pathlib import Path

# Initialize framework
framework = ABTestingFramework()

# Create experiment
experiment = framework.create_experiment(
    name="Cloud Architect Latency Optimization",
    hypothesis="Adding ReACT pattern reduces latency by 20%",
    agent_name="cloud_architect",
    control_prompt=Path("claude/agents/cloud_architect_v2.1.md"),
    treatment_prompt=Path("claude/agents/cloud_architect_v2.2_react.md")
)

print(f"Experiment ID: {experiment.experiment_id}")
```

#### Assign Treatment

```python
# Deterministic assignment (same user always gets same arm)
treatment_arm = framework.assign_treatment(
    experiment_id="exp_001",
    user_id="nathan@example.com"
)

print(f"User assigned to: {treatment_arm}")  # "control" or "treatment"
```

#### Record Interaction

```python
# Record interaction with quality score
framework.record_interaction(
    experiment_id="exp_001",
    user_id="nathan@example.com",
    success=True,  # Task completed successfully
    quality_score=85.5,  # From quality scorer
    tokens_used=750,
    latency_ms=3200.0
)
```

#### Analyze Results

```python
# Run statistical analysis
result = framework.analyze_experiment("exp_001")

if result:
    print(f"Control: {result.control_rate:.1%} completion rate")
    print(f"Treatment: {result.treatment_rate:.1%} completion rate")
    print(f"Effect size: {result.effect_size:.1f}% improvement")
    print(f"P-value: {result.p_value:.4f}")
    print(f"Statistically significant: {result.is_significant}")
    print(f"Winner: {result.winner}")
else:
    print("Insufficient data for analysis (need 30+ interactions per arm)")
```

#### Auto-Promote Winner

```python
# Automatically promote if criteria met (>15% improvement + p<0.05)
promoted = framework.auto_promote_winner("exp_001")

if promoted:
    print(f"Promoted {promoted.winner} prompt to production!")
else:
    print("Not ready for promotion (criteria not met)")
```

### Statistical Methods

**Two-Proportion Z-Test** (Primary metric: Task completion rate)
```
H₀: p_treatment = p_control (no difference)
H₁: p_treatment ≠ p_control (difference exists)

Z = (p_treatment - p_control) / SE
SE = √[p_pooled × (1 - p_pooled) × (1/n_control + 1/n_treatment)]

Reject H₀ if p < 0.05 (95% confidence)
```

**Welch's t-test** (Secondary metric: Quality scores)
```
Tests if mean quality scores differ significantly between arms
Accounts for unequal variances between groups
```

### Promotion Criteria

Treatment arm is promoted if **ALL** conditions met:
1. ✅ Minimum 30 interactions per arm
2. ✅ Effect size >15% improvement
3. ✅ Statistical significance (p < 0.05)
4. ✅ Quality scores not significantly worse

### Experiment Persistence

Experiments are saved to:
```
claude/context/session/experiments/{experiment_id}.json
```

---

## 3. Experiment Queue System

**File**: `claude/tools/sre/experiment_queue.py` (372 lines)

### Purpose
Manage multiple concurrent experiments with priority-based scheduling.

### Features

1. **Priority Levels**: High → Medium → Low (auto-promotion order)
2. **Capacity Management**: Max 3 concurrent active experiments
3. **Auto-Start**: Queued experiments start automatically when slots available
4. **Complete History**: All experiments tracked (completed/cancelled)

### Usage

#### Initialize Queue

```python
from claude.tools.sre.experiment_queue import ExperimentQueue, Priority

# Max 3 concurrent experiments
queue = ExperimentQueue(max_concurrent=3)
```

#### Add Experiments

```python
# Add high-priority experiment
exp1 = queue.add_experiment(
    experiment_id="exp_001",
    agent_name="cloud_architect",
    priority=Priority.HIGH,
    notes="Critical latency optimization test"
)

# Add medium-priority experiment
exp2 = queue.add_experiment(
    experiment_id="exp_002",
    agent_name="jobs_agent",
    priority=Priority.MEDIUM,
    notes="Resume parsing improvement"
)

# Experiments auto-start if capacity available
```

#### Check Queue Status

```python
status = queue.get_queue_status()

print(f"Active: {status['queue_counts']['active']}/{status['capacity']['max_concurrent']}")
print(f"Queued: {status['queue_counts']['queued']}")
print(f"Available Slots: {status['capacity']['available_slots']}")

# Show active experiments
for exp in status['active_experiments']:
    print(f"  {exp['experiment_id']} ({exp['agent_name']}) - Priority: {exp['priority']}")
```

#### Manage Experiments

```python
# Pause experiment (frees slot for next queued)
queue.pause_experiment("exp_001", reason="Waiting for more data")

# Resume paused experiment
queue.start_experiment("exp_001")

# Complete experiment
queue.complete_experiment("exp_001", outcome="Treatment 18% better, promoted")

# Cancel experiment
queue.cancel_experiment("exp_002", reason="Hypothesis invalidated")

# Change priority (queued experiments only)
queue.change_priority("exp_003", Priority.HIGH)
```

#### View History

```python
# Get last 10 completed/cancelled experiments
history = queue.get_history(limit=10)

for exp in history:
    print(f"{exp.experiment_id} - Status: {exp.status}")
    print(f"  Created: {exp.created_at}")
    print(f"  Completed: {exp.completed_at}")
    print(f"  Notes: {exp.notes}")
```

### Queue States

```
QUEUED → Waiting for active slot
  ↓
ACTIVE → Running experiment (collecting data)
  ↓
COMPLETED → Finished with outcome
  or
PAUSED → Temporarily suspended
  or
CANCELLED → Terminated early
```

### Auto-Promotion Logic

When a slot becomes available (completion/pause/cancel):
1. Find highest priority QUEUED experiments (HIGH → MEDIUM → LOW)
2. Start oldest experiment at that priority level
3. Repeat until at max capacity (3 active)

### Queue Persistence

Queue state saved to:
```
claude/context/session/experiment_queue/queue.json
claude/context/session/experiment_queue/history.json
```

---

## 4. Integration Workflow

### End-to-End Example: Running an A/B Test

**Scenario**: Test new ReACT pattern for Cloud Architect agent

#### Step 1: Create Experiment & Add to Queue

```python
from claude.tools.sre.ab_testing_framework import ABTestingFramework
from claude.tools.sre.experiment_queue import ExperimentQueue, Priority
from pathlib import Path

# Initialize systems
framework = ABTestingFramework()
queue = ExperimentQueue(max_concurrent=3)

# Create experiment
experiment = framework.create_experiment(
    name="Cloud Architect ReACT Pattern",
    hypothesis="ReACT pattern improves task completion by 20%",
    agent_name="cloud_architect",
    control_prompt=Path("claude/agents/cloud_architect_v2.1.md"),
    treatment_prompt=Path("claude/agents/cloud_architect_v2.2_react.md")
)

# Add to queue (high priority)
queue.add_experiment(
    experiment_id=experiment.experiment_id,
    agent_name="cloud_architect",
    priority=Priority.HIGH,
    notes="Critical for Azure proposal workflow"
)

# Experiment auto-starts if capacity available
```

#### Step 2: Assign Users & Record Interactions

```python
from claude.tools.sre.automated_quality_scorer import AutomatedQualityScorer

scorer = AutomatedQualityScorer()

# User makes request
user_id = "nathan@example.com"

# Assign treatment arm (deterministic)
treatment_arm = framework.assign_treatment(experiment.experiment_id, user_id)

# ... agent processes request using assigned prompt ...

# Evaluate quality
response_data = {
    "status": "completed",
    "requirements": ["design_azure_architecture", "cost_optimization"],
    "addressed_requirements": ["design_azure_architecture", "cost_optimization"],
    "validation_performed": True,
    "edge_cases_considered": True,
    "tools_used": ["azure_pricing_api", "terraform_generator"],
    "expected_tools": ["azure_pricing_api", "terraform_generator"],
    "systematic_planning": True,
    "logical_breakdown": True,
    "explanation_quality": "excellent",
    "token_count": 850,
    "execution_time_seconds": 6.5
}

quality_score = scorer.evaluate_response(
    response_data=response_data,
    agent_name="cloud_architect",
    response_id=f"{experiment.experiment_id}_{user_id}_001"
)

# Record interaction
framework.record_interaction(
    experiment_id=experiment.experiment_id,
    user_id=user_id,
    success=True,  # Task completed
    quality_score=quality_score.overall_score,
    tokens_used=850,
    latency_ms=6500.0
)
```

#### Step 3: Analyze & Promote

```python
# After 30+ interactions per arm, analyze
result = framework.analyze_experiment(experiment.experiment_id)

if result and result.is_significant:
    print(f"✅ Statistically significant result!")
    print(f"   Effect size: {result.effect_size:.1f}% improvement")
    print(f"   P-value: {result.p_value:.4f}")

    # Auto-promote if criteria met
    promoted = framework.auto_promote_winner(experiment.experiment_id)

    if promoted:
        print(f"🚀 Promoted {promoted.winner} to production!")

        # Complete in queue
        queue.complete_experiment(
            experiment.experiment_id,
            outcome=f"Treatment {result.effect_size:.1f}% better, p={result.p_value:.4f}"
        )
else:
    print("❌ No significant difference found")
```

---

## Performance Metrics

### Automated Quality Scorer
- **Evaluation Time**: <100ms per response
- **Storage**: ~2KB per score (JSON)
- **Accuracy**: Rubric-based (consistent, reproducible)

### A/B Testing Framework
- **Assignment Time**: <5ms (MD5 hashing)
- **Analysis Time**: <50ms (statistical tests)
- **Minimum Sample**: 30 interactions per arm
- **False Positive Rate**: 5% (p<0.05 threshold)

### Experiment Queue System
- **Queue Operations**: <10ms (JSON persistence)
- **Max Concurrent**: 3 experiments (configurable)
- **Priority Levels**: 3 (high/medium/low)

---

## Data Persistence

```
claude/context/session/
├── quality_scores/
│   └── {response_id}.json         # Individual quality scores
├── experiments/
│   └── {experiment_id}.json       # Experiment state & metrics
└── experiment_queue/
    ├── queue.json                 # Active/queued/paused experiments
    └── history.json               # Completed/cancelled experiments
```

---

## Best Practices

### Quality Scoring
1. **Capture Complete Context**: Include all rubric fields in response_data
2. **Historical Tracking**: Monitor 7-day averages for trend detection
3. **Threshold Alerts**: Set up alerts for scores <60 (poor performance)

### A/B Testing
1. **Clear Hypotheses**: Define expected improvement and mechanism
2. **Minimum Sample Size**: Wait for 30+ interactions per arm (statistical power)
3. **Multiple Metrics**: Track completion rate + quality scores + latency
4. **Conservative Promotion**: Require >15% improvement (avoid false positives)

### Experiment Queue
1. **Priority Assignment**: High = revenue-critical, Medium = operational, Low = experimental
2. **Capacity Management**: Keep 3 concurrent max (avoid dilution)
3. **Regular Reviews**: Check queue status daily, adjust priorities
4. **Clean History**: Archive completed experiments after 90 days

---

## Troubleshooting

### Quality Scorer Returns Low Scores
**Symptom**: Scores consistently <60 despite good responses

**Diagnosis**:
```python
score = scorer.evaluate_response(response_data, "agent_name", "response_id")
print(f"Criteria breakdown:")
for criterion, value in score.criteria_scores.items():
    print(f"  {criterion}: {value}/100")
print(f"\nFeedback: {score.feedback}")
```

**Solutions**:
- Check which criteria are scoring low
- Ensure response_data includes all required fields
- Review feedback for specific issues

### A/B Test Shows No Significant Difference
**Symptom**: P-value >0.05 even with large sample

**Diagnosis**:
```python
result = framework.analyze_experiment(experiment_id)
print(f"Control: {result.control_rate:.1%} ({result.control_arm.interactions} interactions)")
print(f"Treatment: {result.treatment_rate:.1%} ({result.treatment_arm.interactions} interactions)")
print(f"Effect size: {result.effect_size:.1f}%")
```

**Solutions**:
- Increase sample size (need more data)
- Check if treatment actually different from control
- Verify hypothesis is testable with current metrics

### Experiment Queue Not Auto-Starting
**Symptom**: Experiments stuck in QUEUED despite available slots

**Diagnosis**:
```python
status = queue.get_queue_status()
print(f"Active: {status['queue_counts']['active']}/{status['capacity']['max_concurrent']}")
print(f"Queued: {status['queue_counts']['queued']}")

# Check for errors in queue file
import json
with open(queue.queue_file) as f:
    print(json.dumps(json.load(f), indent=2))
```

**Solutions**:
- Verify max_concurrent not reached
- Check queue.json for corrupted entries
- Call `queue._try_auto_start()` manually to force check

---

## Future Enhancements

### Phase 4.1 (Planned)
- **Real-time Dashboards**: Grafana visualization for quality scores
- **Slack Notifications**: Auto-alert on significant A/B test results
- **Bayesian A/B Testing**: Continuous monitoring (stop experiments early)

### Phase 4.2 (Planned)
- **Multi-Armed Bandits**: Test 3+ variants simultaneously
- **Quality Score Predictions**: ML model to predict scores before execution
- **Experiment Templates**: Pre-configured experiments for common tests

---

## References

- **Quality Scorer Source**: `claude/tools/sre/automated_quality_scorer.py`
- **A/B Testing Source**: `claude/tools/sre/ab_testing_framework.py`
- **Queue System Source**: `claude/tools/sre/experiment_queue.py`
- **Test Suite**: `claude/tools/sre/test_quality_scorer.py` (6/6 passing)

---

**Status**: Production Ready ✅
**Last Updated**: 2025-10-12
**Maintained By**: Maia Development Team
