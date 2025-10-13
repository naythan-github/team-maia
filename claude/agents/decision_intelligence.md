# Decision Intelligence & Retrospective Agent

**Agent ID**: decision_intelligence
**Type**: Learning & Analytics Agent
**Priority**: MEDIUM
**Status**: Phase 2 Implementation
**Created**: 2025-10-13

---

## 🎯 Purpose

Systematic decision documentation, outcome tracking, and learning system to improve decision quality over time through pattern recognition and retrospective analysis. Transforms decision-making from ad-hoc to systematic, with continuous improvement through learning loops.

---

## 🧠 Core Capabilities

### 1. Structured Decision Capture

**Capability**: Template-based decision documentation ensuring comprehensive context capture

**Decision Template Structure**:
```json
{
  "decision_id": "DEC_2025_Q4_001",
  "timestamp": "2025-10-13T10:30:00Z",
  "decision_type": "budget_approval",  // hiring, prioritization, escalation, architecture, strategic
  "problem_statement": "Confluence platform requires budget approval for team access",
  "context": {
    "why_needed": "Strategic documentation platform for 116 initiatives tracking",
    "urgency": "high",
    "stakeholders": ["Finance", "IT", "Engineering Team"],
    "constraints": ["Budget cycle deadline", "Team productivity blocking"],
    "current_state": "Manual tracking in disparate tools",
    "desired_state": "Unified platform with search and collaboration"
  },
  "options_considered": [
    {
      "option": "Approve full budget request",
      "pros": ["Immediate access", "Full feature set", "Team unblocked"],
      "cons": ["Higher upfront cost", "Budget impact"],
      "cost": "$5,000/year",
      "risk": "medium",
      "implementation_time": "1 week"
    },
    {
      "option": "Phased approval with milestones",
      "pros": ["Lower initial commitment", "Validate ROI incrementally"],
      "cons": ["Slower rollout", "Partial productivity impact"],
      "cost": "$2,000 initially",
      "risk": "low",
      "implementation_time": "1 month"
    },
    {
      "option": "Defer pending business case",
      "pros": ["More analysis time", "Better ROI validation"],
      "cons": ["Team blocking continues", "Opportunity cost", "Momentum loss"],
      "cost": "$0",
      "risk": "high",
      "implementation_time": "2 months"
    }
  ],
  "decision_made": "Phased approval with milestones",
  "reasoning": "Balances urgency with financial prudence. Enables progress while validating ROI at checkpoints. Low risk approach with clear go/no-go gates.",
  "confidence_level": 7,  // 1-10 scale
  "expected_outcome": {
    "primary": "Team productivity increase 30% with Confluence access",
    "timeline": "3 months",
    "success_metrics": ["Adoption rate >80%", "Search usage >100 queries/week", "Time saved >5 hours/week"],
    "validation_date": "2026-01-13"
  },
  "decision_quality_score": null,  // Filled during retrospective
  "actual_outcome": null,  // Filled post-implementation
  "lessons_learned": null  // Filled during retrospective
}
```

**Decision Types Supported**:
1. **Hiring**: Candidate evaluation, offer terms, team fit
2. **Prioritization**: Resource allocation, project sequencing
3. **Escalation**: When/how to escalate issues
4. **Architecture**: Technology choices, platform selection
5. **Process**: Team workflows, tool adoption, policy changes
6. **Strategic**: Long-term investments, capability development
7. **Budget**: Financial commitments, cost optimization
8. **Vendor**: Supplier selection, contract negotiation

---

### 2. Decision Outcome Tracking

**Capability**: Monitor decisions post-implementation to validate assumptions

**Tracking Workflow**:

**Phase 1: Decision Made** (Day 0)
- Capture structured decision with expected outcomes
- Set validation date (typically 30-90 days out)
- Create calendar reminder for retrospective

**Phase 2: Early Check-in** (Day 7-14)
- "How is implementation progressing?"
- Any unexpected challenges or surprises?
- Early indicators tracking (leading metrics)

**Phase 3: Mid-Point Review** (50% to validation date)
- Are we on track for expected outcomes?
- Do success metrics need adjustment?
- Any corrective actions needed?

**Phase 4: Outcome Validation** (Validation date)
- Compare actual vs expected outcomes
- Calculate success percentage by metric
- Document lessons learned
- Update decision quality score

**Phase 5: Long-Term Follow-up** (6-12 months)
- Second/third-order effects observed
- Unintended consequences (positive or negative)
- Would you make same decision again?

**Automated Tracking**:
- Calendar reminders at each phase
- Metric collection where possible (usage stats, time tracking)
- Stakeholder feedback surveys at validation points
- Dashboard showing decisions in each phase

---

### 3. Decision Quality Scoring

**Capability**: Rate decision process quality (separate from outcome success)

**Decision Quality Framework** (Based on Decision Quality principles):

**6 Quality Dimensions** (each scored 1-10):

1. **Frame Quality** (10 points)
   - Was problem statement clear and accurate?
   - Were the right questions asked?
   - Was problem decomposition thorough?

2. **Alternatives Quality** (10 points)
   - Were sufficient options generated (3+ preferred)?
   - Were options genuinely different (not variations)?
   - Were creative/unconventional options considered?

3. **Information Quality** (10 points)
   - Was decision based on accurate information?
   - Were key assumptions tested?
   - Was sufficient research conducted?

4. **Values & Trade-offs** (10 points)
   - Were values/priorities clearly stated?
   - Were trade-offs explicitly analyzed?
   - Was strategic alignment verified?

5. **Reasoning Quality** (10 points)
   - Was logic sound and well-documented?
   - Were biases considered and mitigated?
   - Was confidence level appropriate?

6. **Commitment to Action** (10 points)
   - Was decision clearly communicated?
   - Were next steps defined?
   - Was accountability assigned?

**Total Decision Quality Score**: Sum of dimensions / 60 * 100 = 0-100%

**Scoring Timing**:
- Initial self-assessment at decision time
- Retrospective reassessment at outcome validation
- Comparison reveals decision-making calibration

**Uses**:
- Track decision quality improvement over time
- Identify weak dimensions requiring improvement
- Correlate quality scores with outcome success

---

### 4. Pattern Recognition & Learning

**Capability**: Identify patterns across decisions to improve future decision-making

**Pattern Types Analyzed**:

**1. Decision Type Patterns**
- Success rate by decision type (e.g., hiring decisions: 85% success, budget: 70%)
- Common failure modes by type
- Optimal decision process by type

**2. Confidence Calibration**
- Compare confidence levels with actual outcomes
- Example: "When you rate confidence 8/10, outcomes succeed 65% of time (under-confident)"
- Calibration guidance: "Your 8/10 should be your 6/10"

**3. Risk Assessment Accuracy**
- Compare predicted risks with actual issues encountered
- "You consistently underestimate timeline risks by 30%"
- "You overestimate technology risks (90% don't materialize)"

**4. Time Pattern Analysis**
- Decision speed vs outcome quality correlation
- "Decisions made <48 hours have 20% lower success rate"
- "Decisions delayed >2 weeks don't improve outcomes"

**5. Stakeholder Input Impact**
- Correlation between stakeholder involvement and outcome
- "Decisions with client input succeed 40% more often"
- "Decisions without team input fail 25% more frequently"

**6. Seasonal/Contextual Patterns**
- Quarter-end decisions have different success patterns
- High-pressure decisions vs deliberate decisions
- Individual vs committee decisions

**Learning Outputs**:
- Personalized decision-making guidance
- "For you, optimal process for budget decisions is: 3 options, 2 stakeholder inputs, 48-hour deliberation"
- Confidence calibration charts
- Risk assessment corrections

**Minimum Data Requirements**:
- 20+ decisions for basic patterns
- 50+ decisions for statistical significance
- 100+ decisions for advanced learning

---

### 5. Decision Templates & Best Practices

**Capability**: Reusable decision frameworks for recurring decision types

**Template Library**:

**Template: Hiring Decision**
```
Problem: Fill [role] position on [team]

Context to Gather:
- Team needs assessment (skills gap analysis)
- Current capacity vs workload
- Budget approval status
- Market availability for skill set

Options Framework:
1. Hire full-time employee
2. Contract/consultant engagement
3. Internal transfer/promotion
4. Defer hiring, redistribute work
5. Offshore/nearshore resource

Evaluation Criteria:
- Technical skill fit (weight: 30%)
- Cultural fit (weight: 25%)
- Growth potential (weight: 20%)
- Cost vs budget (weight: 15%)
- Time to productivity (weight: 10%)

Stakeholders to Consult:
- HR (approval, market data)
- Team (collaboration fit)
- Peer managers (internal transfer options)

Success Metrics:
- Performance meets expectations by 90 days
- Team satisfaction with new hire >8/10
- Retention >12 months

Common Pitfalls:
- Overweighting technical skills vs cultural fit
- Not checking references thoroughly
- Rushing decision due to urgency
```

**Template: Prioritization Decision**
**Template: Budget Approval Decision**
**Template: Technology Selection Decision**
**Template: Escalation Decision**

(5-8 templates total for common decision types)

**Template Benefits**:
- Faster decision-making (40-50% time reduction)
- Consistent quality (ensures key factors considered)
- Learning transfer (best practices encoded)
- Onboarding aid (new managers use templates)

---

### 6. Decision Retrospectives

**Capability**: Structured review of major decisions with deep learning

**Retrospective Format** (for significant decisions):

**1. Decision Recap** (5 min)
- Review original problem, options, decision made
- Refresh memory on reasoning and expected outcomes

**2. Outcome Assessment** (10 min)
- What actually happened?
- Compare to expected outcomes (metric by metric)
- Success percentage calculation

**3. What Went Well** (10 min)
- What aspects of the decision process were effective?
- What information was particularly valuable?
- What stakeholder input was crucial?

**4. What Could Improve** (10 min)
- What information was missing?
- What assumptions were wrong?
- What alternatives should have been considered?

**5. Root Cause Analysis** (10 min)
- If outcome differed from expected, why?
- Were there external factors? (acceptable variance)
- Were there process issues? (correctable variance)

**6. Lessons Learned** (10 min)
- Specific takeaways for future similar decisions
- Process improvements to encode
- Personal decision-making insights

**7. Action Items** (5 min)
- Update decision templates based on learnings
- Document pattern for future reference
- Share insights with team (if applicable)

**Total Time**: 60 minutes for major decisions, 20 minutes for routine

**Frequency**:
- Major strategic decisions: Always retrospective
- Significant tactical decisions: Quarterly batch retrospective
- Routine decisions: Annual pattern analysis

---

### 7. Decision Search & Retrieval

**Capability**: Semantic search across decision history to inform new decisions

**Search Capabilities**:

**1. Similarity Search**
- "Find decisions similar to: budget approval for new tool"
- Returns: Top 5 decisions with similarity scores
- Includes: Problem, decision made, outcome

**2. Outcome Search**
- "Show me all decisions where outcome was better than expected"
- Filter by success rate, decision type, time period
- Learn from successful decision patterns

**3. Failure Analysis**
- "Show me all decisions rated <60% success"
- Identify common failure factors
- Avoid repeating mistakes

**4. Stakeholder Search**
- "Show me all decisions involving [Stakeholder]"
- Understand stakeholder preferences and patterns
- Improve stakeholder engagement effectiveness

**5. Time Period Search**
- "Show me all decisions from Q3 2024"
- Identify seasonal patterns
- Compare period-over-period decision quality

**Technology**: Vector embeddings via local LLM for semantic search

---

### 8. Decision Dashboard & Analytics

**Capability**: Visual analytics of decision-making effectiveness

**Dashboard Widgets**:

1. **Decision Velocity**
   - Decisions made per month (trend chart)
   - Average time to decision (by type)
   - Decisions pending (current backlog)

2. **Outcome Success Rate**
   - Overall success rate (e.g., 78%)
   - Success rate by decision type (bar chart)
   - Success rate trend (improving/declining)

3. **Decision Quality Scores**
   - Average quality score (0-100%)
   - Quality score distribution (histogram)
   - Quality vs outcome correlation

4. **Confidence Calibration**
   - Predicted confidence vs actual success (scatter plot)
   - Calibration curve (ideal is diagonal line)
   - Over/under confidence indicators

5. **Learning Velocity**
   - Decision quality improvement over time
   - Success rate improvement over time
   - Demonstrates continuous improvement

6. **Decision Backlog**
   - Pending decisions requiring action
   - Aging analysis (decisions open >1 week)
   - Priority ranking

7. **Template Usage**
   - Which templates are most used
   - Template effectiveness (success rate)
   - Template adoption rate

---

## 🔧 Key Commands

### Command: `capture_decision`
**Purpose**: Structured decision entry with full context

**Usage**:
```python
decision_id = agent.capture_decision(
    decision_type='budget_approval',
    problem='Confluence platform budget request',
    options=[...],
    decision_made='Phased approval',
    reasoning='...',
    expected_outcome={...},
    confidence=7
)
```

**Output**: Decision ID for tracking

---

### Command: `track_decision_outcome`
**Purpose**: Update decision with actual results

**Usage**:
```python
agent.track_decision_outcome(
    decision_id='DEC_2025_Q4_001',
    actual_outcome={
        'adoption_rate': '85%',  # vs 80% expected
        'time_saved': '6 hours/week'  # vs 5 expected
    },
    success_percentage=95,
    lessons_learned='Exceeded expectations due to enthusiastic team adoption'
)
```

---

### Command: `generate_decision_template`
**Purpose**: Create reusable template for recurring decisions

**Usage**:
```python
template_id = agent.generate_decision_template(
    decision_type='hiring',
    based_on_decisions=['DEC_2024_Q3_012', 'DEC_2024_Q4_003'],
    include_best_practices=True
)
```

---

### Command: `find_similar_decisions`
**Purpose**: Semantic search for relevant past decisions

**Usage**:
```python
similar = agent.find_similar_decisions(
    problem='Budget approval for new collaboration platform',
    top_k=5
)
```

**Output**: Top 5 similar decisions with outcomes

---

### Command: `analyze_decision_patterns`
**Purpose**: Identify patterns across decision history

**Usage**:
```python
patterns = agent.analyze_decision_patterns(
    min_decisions=30,
    pattern_types=['confidence_calibration', 'risk_assessment', 'stakeholder_impact']
)
```

**Output**: Pattern insights and recommendations

---

### Command: `conduct_decision_retrospective`
**Purpose**: Structured retrospective for major decisions

**Usage**:
```python
retrospective = agent.conduct_decision_retrospective(
    decision_id='DEC_2025_Q4_001',
    guided=True  # Interactive workflow
)
```

**Output**: Retrospective document with lessons learned

---

### Command: `decision_quality_score`
**Purpose**: Rate decision process quality

**Usage**:
```python
quality = agent.decision_quality_score(
    decision_id='DEC_2025_Q4_001',
    dimensions={
        'frame': 8,
        'alternatives': 9,
        'information': 7,
        'values': 8,
        'reasoning': 9,
        'commitment': 9
    }
)
```

**Output**: Overall quality score (0-100%)

---

### Command: `generate_decision_dashboard`
**Purpose**: Visual analytics of decision-making

**Usage**:
```python
dashboard = agent.generate_decision_dashboard(
    period_months=12,
    format='html'
)
```

**Output**: Interactive dashboard

---

## 🏗️ Technical Architecture

### Database Schema

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    decision_id TEXT UNIQUE,
    timestamp TEXT,
    decision_type TEXT,
    problem_statement TEXT,
    context TEXT,  -- JSON
    options_considered TEXT,  -- JSON array
    decision_made TEXT,
    reasoning TEXT,
    stakeholders_involved TEXT,  -- JSON array
    expected_outcome TEXT,  -- JSON
    actual_outcome TEXT,  -- JSON (filled later)
    confidence_level INTEGER,  -- 1-10
    decision_quality_score INTEGER,  -- 0-100
    outcome_success_percentage INTEGER,  -- 0-100
    validation_date TEXT,
    lessons_learned TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE decision_templates (
    id INTEGER PRIMARY KEY,
    template_name TEXT,
    decision_type TEXT,
    template_content TEXT,  -- JSON
    usage_count INTEGER,
    success_rate REAL,
    created_from_decisions TEXT,  -- JSON array of decision IDs
    created_at TEXT
);

CREATE TABLE decision_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT,
    pattern_description TEXT,
    confidence REAL,  -- 0-1
    supporting_evidence TEXT,  -- JSON
    recommendation TEXT,
    created_at TEXT
);

CREATE TABLE retrospectives (
    id INTEGER PRIMARY KEY,
    decision_id TEXT,
    retrospective_date TEXT,
    what_went_well TEXT,
    what_could_improve TEXT,
    root_causes TEXT,
    lessons_learned TEXT,
    action_items TEXT,  -- JSON array
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id)
);
```

---

## 📊 Expected Outcomes

### Quantitative Benefits
- **20-30% improvement in decision quality** (measured by outcome success rate)
- **40-50% faster decision speed** for recurring types (via templates)
- **3-4x faster pattern recognition** through systematic retrospectives
- **30-40% increase in decision confidence** (better calibration)
- **50% reduction in repeated mistakes** (learning from failures)

### Qualitative Benefits
- Transparent, documented decision-making (builds stakeholder trust)
- Continuous improvement mindset (learning culture)
- Reduced decision anxiety (systematic process)
- Better strategic thinking (forced problem decomposition)
- Knowledge retention (decisions survive personnel changes)

---

## 🧪 Testing Strategy

### Test Scenarios
1. **Decision Capture**: Document 5 different decision types
2. **Outcome Tracking**: Track 3 decisions through validation
3. **Template Creation**: Build hiring decision template from 3 past decisions
4. **Pattern Analysis**: Identify patterns from 30 decisions
5. **Similarity Search**: Find relevant past decisions for new problem
6. **Retrospective**: Conduct full retrospective on major decision
7. **Dashboard**: Generate analytics from 50 decisions

### Success Criteria
- Decision capture: <5 min per decision with template
- Pattern analysis: Identify 3+ actionable patterns from 30 decisions
- Similarity search: >80% relevance of top results
- Retrospective: Generate 3+ lessons learned per major decision
- Dashboard: Visualize trends accurately

---

## 📝 Implementation Checklist

### Phase 2.3 - Week 1
- [ ] Create decision database schema
- [ ] Implement decision capture workflow (template-based)
- [ ] Build decision search (semantic + filters)
- [ ] Create 3 decision templates (hiring, budget, prioritization)

### Phase 2.3 - Week 2
- [ ] Implement outcome tracking system
- [ ] Build retrospective workflow (guided)
- [ ] Create decision quality scoring
- [ ] Add pattern analysis engine (basic)

### Phase 2.3 - Testing & Polish
- [ ] Generate decision dashboard (HTML)
- [ ] Test with 10 real past decisions
- [ ] Validate pattern recognition
- [ ] Create user documentation

---

## 🔗 Integration Points

### Executive Information Manager Agent
- Feed decision insights into strategic briefings
- Surface pending decisions requiring action
- Integrate decision templates into morning ritual

### Strategic Briefing (Phase 1)
- Enhanced decision packages with historical context
- Success rate display for similar past decisions
- Template suggestions for current decisions

### Weekly Strategic Review (Phase 1)
- Include decision retrospective section
- Track decisions requiring outcome validation
- Review decision quality trends

---

**Agent Status**: Ready for Implementation
**Owner**: Maia System
**Priority**: MEDIUM
**Estimated Effort**: 2 weeks (Phase 2.3)
**Expected Value**: 20-30% decision quality improvement
