# Cloud Cost Analysis → Optimization Planning → Implementation - Prompt Chain

## Overview
**Problem**: Single-turn cost optimization provides generic advice without detailed analysis, misses context-specific opportunities, and lacks implementation roadmap.

**Solution**: 3-subtask chain that analyzes current spending → designs optimization strategy → creates implementation plan with ROI projections.

**Expected Improvement**: +40% cost savings identified, +60% implementation success rate, +50% faster time-to-value

---

## When to Use This Chain

**Use When**:
- Cloud spend >$10K/month (meaningful optimization potential)
- Need comprehensive cost audit (not spot check)
- Planning budget reduction initiatives
- Post-migration cost optimization review
- Executive reporting on cloud efficiency

**Don't Use When**:
- Single resource query ("How much does VM X cost?")
- Real-time cost alert investigation (use single-turn)
- Quick wins already known (just implement them)

---

## Subtask Sequence

### Subtask 1: Cost Analysis & Waste Identification

**Goal**: Comprehensive analysis of cloud spending patterns, identifying waste, inefficiencies, and optimization opportunities

**Input**:
- `cloud_provider`: String - "Azure", "AWS", "GCP", or "Multi-cloud"
- `billing_data`: Object - Last 90 days billing data
- `resource_inventory`: Array - Current cloud resources
- `business_context`: Object - Growth plans, seasonal patterns, constraints

**Output**:
```json
{
  "cost_summary": {
    "total_monthly_spend": 45600,
    "trend": "+18% vs 3 months ago",
    "top_5_services": [
      {"service": "Virtual Machines", "cost": 18200, "percentage": 0.40},
      {"service": "Storage", "cost": 9100, "percentage": 0.20},
      {"service": "Networking", "cost": 6800, "percentage": 0.15},
      {"service": "Databases", "cost": 5900, "percentage": 0.13},
      {"service": "Other", "cost": 5600, "percentage": 0.12}
    ]
  },
  "waste_identified": {
    "total_waste": 12800,
    "waste_percentage": 0.28,
    "categories": [
      {
        "category": "Idle Resources",
        "monthly_waste": 5600,
        "examples": [
          "15 VMs with <5% CPU utilization (avg 2.3%)",
          "8 SQL databases with <10% DTU usage",
          "120 GB orphaned disks"
        ],
        "quick_win_potential": 5400
      },
      {
        "category": "Oversized Resources",
        "monthly_waste": 4200,
        "examples": [
          "Storage accounts using Premium when Standard sufficient (80% read-only)",
          "VMs over-provisioned (P4 when P2 adequate)",
          "App Service Plans at higher tier than needed"
        ],
        "quick_win_potential": 3800
      },
      {
        "category": "Unoptimized Purchasing",
        "monthly_waste": 3000,
        "examples": [
          "Pay-as-you-go VMs eligible for 3-year Reserved Instances",
          "No use of Azure Hybrid Benefit (40 Windows licenses unused)",
          "Dev/Test environments running 24/7"
        ],
        "quick_win_potential": 2600
      }
    ]
  },
  "optimization_opportunities": [
    {
      "opportunity": "Reserved Instances for production VMs",
      "current_cost": 12000,
      "optimized_cost": 7200,
      "monthly_savings": 4800,
      "implementation_effort": "Low",
      "risk": "Low",
      "payback_period": "Immediate"
    },
    {
      "opportunity": "Right-size oversized VMs",
      "current_cost": 8400,
      "optimized_cost": 5100,
      "monthly_savings": 3300,
      "implementation_effort": "Medium",
      "risk": "Medium",
      "payback_period": "1 month"
    }
  ],
  "benchmarking": {
    "cost_per_user": 152,
    "industry_average": 180,
    "percentile": "35th (better than average)",
    "efficiency_score": 72
  }
}
```

**Prompt**:
```
You are the FinOps Engineering agent analyzing cloud costs.

INPUT DATA:
- Provider: {cloud_provider}
- Billing: {billing_data} (last 90 days)
- Resources: {resource_inventory}
- Context: {business_context}

ANALYSIS TASKS:

1. COST SUMMARY:
   - Total monthly spend and trend
   - Top 5 services by cost (with percentages)
   - Month-over-month growth analysis
   - Identify cost spikes or anomalies

2. WASTE IDENTIFICATION:
   Categorize waste into:
   - **Idle Resources**: <5% utilization, stopped but not deleted
   - **Oversized Resources**: Over-provisioned capacity
   - **Unoptimized Purchasing**: Not using Reserved/Spot instances
   - **Orphaned Resources**: Disks, IPs, snapshots with no parent
   - **Dev/Test Running 24/7**: Non-prod environments always on

   For each waste category:
   - Quantify monthly waste
   - Provide specific examples (resource IDs, costs)
   - Estimate quick win potential (90-day savings)

3. OPTIMIZATION OPPORTUNITIES:
   Identify top 10 opportunities ranked by:
   - Monthly savings potential
   - Implementation effort (Low/Medium/High)
   - Risk level (Low/Medium/High)
   - Payback period

4. BENCHMARKING:
   - Cost per user vs industry average
   - Efficiency score (0-100)
   - Compare to similar organizations

5. TREND ANALYSIS:
   - Growth trajectory (extrapolate 12 months)
   - Seasonal patterns
   - Service-level growth rates

QUALITY CRITERIA:
✅ Waste quantified with specific resource examples
✅ Opportunities prioritized by ROI (savings ÷ effort)
✅ All costs validated against billing data
✅ Benchmarks use relevant industry comparisons
✅ Quick wins (0-30 days) flagged separately
```

---

### Subtask 2: Optimization Strategy & Roadmap

**Goal**: Design comprehensive optimization strategy with prioritized initiatives, timeline, and resource requirements

**Input**:
- Output from Subtask 1 (cost analysis)
- `optimization_goals`: Object - Target savings, timeline, constraints
- `resource_availability`: Object - Team capacity, skillsets, tools

**Output**:
```json
{
  "optimization_strategy": {
    "target_savings": {
      "30_day": 8200,
      "90_day": 14600,
      "12_month": 18900
    },
    "strategic_pillars": [
      {
        "pillar": "Eliminate Waste",
        "initiatives": 8,
        "savings_potential": 9400,
        "percentage_of_total": 0.50
      },
      {
        "pillar": "Right-Size Resources",
        "initiatives": 5,
        "savings_potential": 5100,
        "percentage_of_total": 0.27
      },
      {
        "pillar": "Optimize Purchasing",
        "initiatives": 4,
        "savings_potential": 4400,
        "percentage_of_total": 0.23
      }
    ]
  },
  "prioritized_initiatives": [
    {
      "id": "OPT-001",
      "initiative": "Implement Reserved Instances for production VMs",
      "priority": "P0 (Critical)",
      "savings": 4800,
      "effort": "Low (4 hours)",
      "risk": "Low",
      "timeline": "Week 1",
      "owner": "Cloud Architect",
      "dependencies": ["Finance approval for 1-year commitment"],
      "success_criteria": "12 production VMs converted to RIs, $4,800/month savings realized"
    },
    {
      "id": "OPT-002",
      "initiative": "Delete orphaned resources",
      "priority": "P1 (High)",
      "savings": 1200,
      "effort": "Low (2 hours)",
      "risk": "Low",
      "timeline": "Week 1",
      "owner": "DevOps Engineer",
      "dependencies": ["Verify no dependencies"],
      "success_criteria": "120 orphaned disks deleted, 45 unattached IPs released"
    }
  ],
  "implementation_roadmap": {
    "phase_1_quick_wins": {
      "timeline": "Weeks 1-4",
      "initiatives": ["OPT-001", "OPT-002", "OPT-003", "OPT-004"],
      "total_savings": 8200,
      "resources_required": "Cloud Architect (12h), DevOps Engineer (16h)"
    },
    "phase_2_optimization": {
      "timeline": "Weeks 5-12",
      "initiatives": ["OPT-005", "OPT-006", "OPT-007"],
      "total_savings": 6400,
      "resources_required": "Cloud Architect (24h), Application Team (40h)"
    },
    "phase_3_transformation": {
      "timeline": "Months 4-12",
      "initiatives": ["OPT-008", "OPT-009", "OPT-010"],
      "total_savings": 4300,
      "resources_required": "Cloud Architect (60h), Dev Team (120h)"
    }
  },
  "governance_framework": {
    "policies": [
      "All VMs must justify Premium tier (default: Standard)",
      "Dev/Test auto-shutdown outside business hours (7pm-7am)",
      "Reserved Instance review quarterly",
      "New resource approval required for >$500/month spend"
    ],
    "monitoring": "Weekly cost review, monthly executive reporting",
    "accountability": "Service owners responsible for their cost budgets"
  }
}
```

**Prompt**: [Similar structure to Subtask 1, focusing on strategy, prioritization, roadmap, governance]

---

### Subtask 3: Implementation Plan & Runbook

**Goal**: Create detailed implementation plan with step-by-step runbooks, validation criteria, and rollback procedures

**Input**:
- Output from Subtask 2 (strategy + roadmap)
- `selected_initiatives`: Array - Initiatives approved for implementation
- `implementation_timeline`: String - Target completion date

**Output**: Detailed implementation guides for each initiative with commands, scripts, validation steps, and rollback procedures

**Prompt**: [Focuses on tactical execution, scripts, commands, testing, validation]

---

## Benefits

- **Comprehensive Analysis**: Identifies all waste categories, not just obvious ones
- **Prioritized Roadmap**: Focus on high-ROI, low-risk quick wins first
- **Executable Plans**: Step-by-step runbooks with commands and scripts
- **Risk Mitigation**: Validation criteria and rollback procedures included
- **Governance**: Long-term cost control policies prevent waste recurrence

## Execution Time

- Subtask 1 (Analysis): 45-60 minutes
- Subtask 2 (Strategy): 30-45 minutes
- Subtask 3 (Implementation): 40-60 minutes per initiative
- **Total**: 2-3 hours for complete optimization plan

## Success Criteria

- [ ] Waste identified and quantified (% of total spend)
- [ ] Top 10 opportunities ranked by ROI
- [ ] 30-day, 90-day, 12-month savings targets defined
- [ ] Initiatives prioritized and sequenced
- [ ] Implementation runbooks complete with commands
- [ ] Validation criteria defined for each initiative
- [ ] Governance policies established for ongoing cost control
