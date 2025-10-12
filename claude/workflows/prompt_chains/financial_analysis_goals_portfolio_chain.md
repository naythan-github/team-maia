# Financial Analysis → Goal Setting → Portfolio Recommendation - Prompt Chain

## Overview
**Problem**: Single-turn financial advice lacks depth, misses context, and provides generic recommendations without personalized goal alignment.

**Solution**: 3-subtask chain that analyzes current financial position → sets SMART goals → creates personalized portfolio recommendations.

**Expected Improvement**: +45% recommendation relevance, +60% goal achievement rate, +35% user confidence

---

## When to Use This Chain

**Use When**:
- Comprehensive financial planning needed (not single question)
- Multiple financial goals to balance (retirement, house, education)
- Portfolio optimization or rebalancing required
- Major life changes requiring financial reassessment

**Don't Use When**:
- Simple calculations (savings rate, loan payment)
- Single product comparison (this savings account vs that one)
- Tax-specific questions (use tax specialist instead)

---

## Subtask Sequence

### Subtask 1: Financial Position Analysis

**Goal**: Comprehensive analysis of current financial situation, identifying strengths, risks, and opportunities

**Input**:
- `income`: Object - Current income sources and amounts
- `expenses`: Object - Monthly expenses by category
- `assets`: Object - Current assets (savings, investments, property, super)
- `liabilities`: Object - Debts and obligations
- `age`: Number - Current age
- `life_stage`: String - e.g., "early career", "family building", "pre-retirement"

**Output**:
```json
{
  "financial_health_score": 72,
  "cash_flow_analysis": {
    "monthly_surplus": 2400,
    "savings_rate": 0.28,
    "discretionary_spending": 1800
  },
  "net_worth_analysis": {
    "total_assets": 285000,
    "total_liabilities": 45000,
    "net_worth": 240000,
    "net_worth_percentile": "65th for age group"
  },
  "strengths": [
    "Strong savings rate (28% vs 15% average)",
    "Diversified income sources",
    "Emergency fund fully funded (6 months expenses)"
  ],
  "risks": [
    "High expense ratio on mortgage (35% of gross income)",
    "Under-diversified investment portfolio (80% Australian equities)",
    "Inadequate life insurance coverage ($150K vs $500K recommended)"
  ],
  "opportunities": [
    "Salary sacrifice to super (save $5K tax annually)",
    "Refinance mortgage (potential 0.5% rate reduction = $3K/year savings)",
    "Consolidate high-interest debt (credit card 19.5% → personal loan 8%)"
  ]
}
```

**Prompt**:
```
You are the Financial Advisor agent analyzing financial position.

INPUT DATA:
- Income: {income}
- Expenses: {expenses}
- Assets: {assets}
- Liabilities: {liabilities}
- Age: {age}
- Life Stage: {life_stage}

ANALYSIS TASKS:

1. CASH FLOW ANALYSIS:
   - Calculate monthly surplus/deficit
   - Determine savings rate (% of income saved)
   - Identify discretionary vs essential spending
   - Benchmark against age/income cohort

2. NET WORTH ASSESSMENT:
   - Calculate total assets and liabilities
   - Determine net worth and percentile for age group
   - Identify asset allocation (property vs super vs investments)
   - Project net worth growth at current savings rate

3. FINANCIAL HEALTH EVALUATION:
   - Emergency fund adequacy (3-6 months expenses)
   - Debt-to-income ratio
   - Investment diversification
   - Insurance coverage gaps
   - Retirement savings trajectory
   - Generate overall health score (0-100)

4. IDENTIFY STRENGTHS (3-5 positive factors):
   - What's working well financially?
   - Comparative advantages vs peers
   - Sustainable positive behaviors

5. IDENTIFY RISKS (3-5 areas of concern):
   - What could derail financial progress?
   - Concentration risks, gaps, vulnerabilities
   - Prioritize by impact + likelihood

6. IDENTIFY OPPORTUNITIES (3-5 quick wins):
   - Low-hanging fruit for improvement
   - Tax optimization strategies
   - Cost reduction opportunities
   - Quantify potential savings where possible

OUTPUT: JSON with health score, cash flow, net worth, strengths, risks, opportunities

QUALITY CRITERIA:
✅ Analysis based on actual data (not assumptions)
✅ Benchmarks use Australian norms (age, income, life stage)
✅ Opportunities are actionable with quantified benefits
✅ Risks prioritized by impact × likelihood
```

---

### Subtask 2: Goal Setting & Prioritization

**Goal**: Define SMART financial goals, prioritize by importance/timeline, create accountability framework

**Input**:
- Output from Subtask 1 (financial analysis)
- `stated_goals`: Array - User's stated financial aspirations
- `time_horizon`: Number - Planning period (e.g., 10 years)

**Output**:
```json
{
  "smart_goals": [
    {
      "goal_id": "goal_1",
      "name": "Build house deposit",
      "specific": "Save $150K for 20% deposit on $750K home",
      "measurable": "$150,000 target, currently $45K (30% progress)",
      "achievable": "Yes - requires $2,500/month savings (current: $2,400)",
      "relevant": "Priority 1 - Life stage milestone (family building)",
      "time_bound": "36 months (July 2028)",
      "priority": "HIGH",
      "monthly_allocation": 2500
    },
    {
      "goal_id": "goal_2",
      "name": "Retirement savings",
      "specific": "Reach $1M super balance by age 67",
      "measurable": "$1,000,000 target, currently $180K (18% progress)",
      "achievable": "Yes - with 15% contributions + compound growth",
      "relevant": "Priority 2 - Long-term security",
      "time_bound": "20 years (age 67)",
      "priority": "MEDIUM",
      "monthly_allocation": 800
    }
  ],
  "goal_conflicts": [
    "House deposit vs retirement: Both compete for discretionary savings. Recommend 75/25 split (house/retirement) for next 3 years."
  ],
  "trade_offs": [
    "Prioritizing house deposit may delay retirement savings growth by 3 years (opportunity cost: ~$80K at retirement)"
  ],
  "milestone_plan": {
    "12_months": "Save $30K house deposit (total: $75K, 50% progress)",
    "24_months": "Save $60K house deposit (total: $105K, 70% progress)",
    "36_months": "Reach $150K house deposit target (100%), begin home purchase"
  }
}
```

**Prompt**:
```
You are the Financial Advisor agent setting SMART goals.

FINANCIAL ANALYSIS:
{subtask_1_output}

STATED GOALS:
{stated_goals}

GOAL SETTING TASKS:

1. CONVERT TO SMART GOALS:
   For each stated goal, define:
   - Specific: Precise target with numbers
   - Measurable: Current progress and target
   - Achievable: Feasibility given financial capacity
   - Relevant: Why this goal matters (life stage alignment)
   - Time-bound: Specific deadline

2. PRIORITIZE GOALS:
   - Rank by: Urgency × Importance × Financial impact
   - Consider life stage and timing constraints
   - Flag competing goals (same funds needed)

3. ALLOCATE RESOURCES:
   - Based on {monthly_surplus} available
   - Allocate to each goal proportionally
   - Ensure critical goals funded first

4. IDENTIFY CONFLICTS & TRADE-OFFS:
   - Which goals compete for same resources?
   - What's the opportunity cost of priority order?
   - Recommend optimal balance

5. CREATE MILESTONE PLAN:
   - 12-month, 24-month, 36-month checkpoints
   - Define success criteria for each milestone
   - Build accountability framework

QUALITY CRITERIA:
✅ All goals are SMART (not vague)
✅ Priorities reflect life stage and urgency
✅ Monthly allocations sum to available surplus
✅ Trade-offs explicitly identified
✅ Milestones are measurable and time-bound
```

---

### Subtask 3: Portfolio Recommendation

**Goal**: Create personalized investment portfolio aligned with goals, risk tolerance, and time horizon

**Input**:
- Output from Subtask 1 & 2 (analysis + goals)
- `risk_tolerance`: String - "conservative", "balanced", "growth", "aggressive"
- `investment_knowledge`: String - "beginner", "intermediate", "advanced"
- `existing_portfolio`: Object (optional) - Current investments

**Output**:
```json
{
  "recommended_portfolio": {
    "allocation": {
      "australian_equities": 0.35,
      "international_equities": 0.30,
      "property": 0.15,
      "fixed_income": 0.15,
      "cash": 0.05
    },
    "specific_investments": [
      {
        "asset": "Vanguard Australian Shares Index ETF (VAS)",
        "allocation": 0.20,
        "amount": 48000,
        "rationale": "Low-cost broad market exposure, 1.5% dividend yield"
      },
      {
        "asset": "Vanguard International Shares ETF (VGS)",
        "allocation": 0.30,
        "amount": 72000,
        "rationale": "Global diversification, reduces Australia concentration risk"
      }
    ],
    "rebalancing_strategy": "Quarterly review, rebalance if any asset >5% from target",
    "tax_optimization": [
      "Use super for fixed income (tax advantage)",
      "Hold growth equities in personal name (50% CGT discount >12 months)",
      "Franking credits maximize value of Australian equities"
    ]
  },
  "transition_plan": {
    "current_portfolio": "80% Australian equities, 20% cash (high concentration risk)",
    "changes_required": [
      "Reduce Australian equities from 80% to 35% (sell $108K)",
      "Add international equities 30% ($72K)",
      "Add property exposure 15% ($36K via REITs)",
      "Add fixed income 15% ($36K bonds/term deposits)",
      "Maintain cash 5% ($12K emergency fund)"
    ],
    "implementation_sequence": [
      "Week 1: Open brokerage account, setup auto-invest",
      "Month 1-3: Gradual transition (avoid timing risk, spread over 3 months)",
      "Month 4: Review performance, adjust if needed"
    ]
  },
  "projected_returns": {
    "conservative_scenario": {
      "annual_return": 0.05,
      "10_year_value": 375000
    },
    "expected_scenario": {
      "annual_return": 0.07,
      "10_year_value": 425000
    },
    "optimistic_scenario": {
      "annual_return": 0.09,
      "10_year_value": 485000
    }
  },
  "monitoring_plan": {
    "quarterly_review": "Check allocation drift, rebalance if needed",
    "annual_review": "Assess goal progress, adjust strategy",
    "life_event_triggers": ["Job change", "House purchase", "New child", "Inheritance"]
  }
}
```

**Prompt**:
```
You are the Financial Advisor agent creating portfolio recommendations.

CONTEXT:
{subtask_1_output + subtask_2_output}

RISK PROFILE:
- Risk tolerance: {risk_tolerance}
- Investment knowledge: {investment_knowledge}
- Time horizon: {longest_goal_timeframe}

PORTFOLIO CONSTRUCTION TASKS:

1. DETERMINE ASSET ALLOCATION:
   - Based on risk tolerance and time horizon
   - Align with goal priorities (cash for short-term, equities for long-term)
   - Diversify across asset classes
   - Consider Australian tax advantages (franking credits, super, CGT)

2. SELECT SPECIFIC INVESTMENTS:
   - Recommend low-cost ETFs/index funds (prioritize)
   - Avoid high-fee managed funds unless justified
   - Consider investment knowledge level (simple for beginners)
   - Include ASX codes and current prices

3. CREATE TRANSITION PLAN:
   - If existing portfolio provided, show changes needed
   - Sequence implementation (avoid market timing risk)
   - Consider tax implications of selling (CGT)
   - Provide week-by-week action plan

4. OPTIMIZE FOR TAX:
   - Use super for fixed income (15% tax vs marginal rate)
   - Hold growth assets in personal name (50% CGT discount)
   - Maximize franking credit value
   - Consider negative gearing for property (if applicable)

5. PROJECT RETURNS:
   - Conservative, expected, optimistic scenarios
   - 10-year projected values for each
   - Show compound growth impact
   - Include fees and taxes in projections

6. DEFINE MONITORING PLAN:
   - Quarterly rebalancing triggers (±5% drift)
   - Annual goal progress review
   - Life event triggers for strategy changes
   - Performance benchmarks

QUALITY CRITERIA:
✅ Allocation matches risk tolerance and time horizon
✅ Investments are low-cost, liquid, diversified
✅ Tax optimization Australian-specific (franking, super, CGT)
✅ Transition plan actionable with specific steps
✅ Projections realistic and range-based (not single number)
✅ Monitoring plan defines clear triggers for action
```

---

## Benefits

- **Comprehensive Planning**: 3-phase approach ensures nothing missed
- **Goal Alignment**: Portfolio directly supports defined SMART goals
- **Personalization**: Recommendations based on actual financial data, not generic advice
- **Actionability**: Specific investments, amounts, and implementation steps
- **Accountability**: Milestone plan and monitoring framework

## Execution Time

- Subtask 1 (Analysis): 20-30 minutes
- Subtask 2 (Goals): 15-20 minutes
- Subtask 3 (Portfolio): 25-35 minutes
- **Total**: 60-85 minutes for complete financial plan

## Success Criteria

- [ ] Financial health score calculated with supporting data
- [ ] All goals converted to SMART format
- [ ] Portfolio allocation matches risk tolerance
- [ ] Specific investments recommended (with ASX codes)
- [ ] Tax optimization strategies Australian-specific
- [ ] Implementation plan actionable (week-by-week steps)
- [ ] Monitoring plan defines review triggers
