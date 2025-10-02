# Market Intelligence Report Command

## Purpose
Comprehensive market analysis combining multiple data sources to generate strategic business intelligence reports for career and business decision-making.

## Agent Orchestration Chain

### Stage 1: Data Collection (Parallel Multi-Source)
```json
{
  "agents": ["Industry Research Agent", "Company Intelligence Agent", "Salary Market Agent", "Network Intelligence Agent"],
  "mode": "parallel",
  "timeout": "8 minutes", 
  "data_sources": "multiple_external_apis_and_scraping",
  "merge_strategy": "comprehensive_market_dataset"
}
```

**Industry Research Agent**:
- Input: Target industry sector + geographic focus (Perth/Australia)
- Output: Industry trends, growth projections, digital transformation patterns
- Sources: ABS data, industry reports, technology trend analysis
- Focus: BRM role evolution, government digitalization, mining tech adoption

**Company Intelligence Agent**:
- Input: Target company list + competitive landscape mapping
- Output: Company profiles, financial health, growth trajectory, culture analysis
- Sources: LinkedIn company pages, annual reports, news analysis, employee reviews
- Analysis: Organizational structure, technology adoption, leadership changes

**Salary Market Agent**:
- Input: Role specifications + seniority level + location parameters
- Output: Compensation benchmarks, market rates, negotiation intelligence
- Sources: Glassdoor, Seek salary data, recruitment market reports
- Segmentation: Government vs private, industry variations, experience premiums

**Network Intelligence Agent**:
- Input: Professional network analysis + industry connections
- Output: Key decision makers, hiring patterns, referral opportunities
- Sources: LinkedIn network analysis, industry events, professional associations
- Focus: Perth business ecosystem, government contacts, technology leaders

### Stage 2: Data Integration & Analysis (Sequential)
```json
{
  "chain": [
    {"agent": "Data Integration Specialist", "focus": "dataset_harmonization"},
    {"agent": "Market Analyst", "focus": "trend_identification"},
    {"agent": "Competitive Intelligence", "focus": "positioning_analysis"}
  ]
}
```

**Data Integration Specialist Agent**:
- Input: All parallel data collection results
- Output: Unified market intelligence database
- Process: Data cleaning, normalization, gap identification
- Quality Assurance: Cross-reference validation, confidence scoring

**Market Analyst Agent** (Prompt Engineer):
- Input: Integrated market dataset
- Output: Trend analysis with strategic implications
- Analysis:
  - Emerging role requirements and skill evolution
  - Technology adoption patterns affecting BRM roles
  - Market gaps and opportunity identification
  - Perth-specific market dynamics and advantages

**Competitive Intelligence Agent**:
- Input: Market analysis + personal profile positioning
- Output: Competitive positioning and differentiation strategy
- Components:
  - Peer analysis and benchmark positioning
  - Unique value proposition identification
  - Market positioning recommendations
  - Competitive advantages and market entry strategies

### Stage 3: Insight Generation (Parallel Specialized Analysis)
```json
{
  "agents": ["Opportunity Identifier", "Risk Assessor", "Strategy Formulator"],
  "mode": "parallel",
  "input": "complete_market_analysis",
  "focus": "actionable_business_intelligence"
}
```

**Opportunity Identifier Agent**:
- Input: Market trends + personal capabilities analysis
- Output: Specific market opportunities with action plans
- Identification:
  - Emerging role categories with high demand
  - Underserved market segments in Perth
  - Technology transformation opportunities
  - Consulting and advisory service gaps

**Risk Assessor Agent**:
- Input: Market analysis + industry volatility data
- Output: Risk assessment with mitigation strategies
- Analysis:
  - Economic factors affecting employment market
  - Industry disruption risks and timeline
  - Geographic market dependencies
  - Skill obsolescence risks and refresh requirements

**Strategy Formulator Agent** (Prompt Engineer):
- Input: Opportunities + risks + competitive positioning
- Output: Strategic recommendations with implementation roadmap
- Components:
  - Career strategy recommendations
  - Skill development priorities
  - Network expansion strategies
  - Market entry and positioning tactics

### Stage 4: Report Generation & Visualization (Sequential)
```json
{
  "chain": [
    {"agent": "Data Visualization Specialist", "focus": "charts_and_graphs"},
    {"agent": "Report Writer", "focus": "executive_summary"},
    {"agent": "Presentation Builder", "focus": "stakeholder_communication"}
  ]
}
```

**Data Visualization Specialist Agent**:
- Input: All analysis results + key metrics
- Output: Professional charts, graphs, and infographics
- Visualizations:
  - Market size and growth projections
  - Salary progression and benchmarking charts
  - Competitive positioning matrices
  - Geographic market heat maps
  - Industry trend timelines

**Report Writer Agent** (Prompt Engineer):
- Input: Complete analysis + visualizations
- Output: Professional market intelligence report
- Structure:
  - Executive summary with key findings
  - Market overview and dynamics
  - Competitive landscape analysis
  - Opportunity and risk assessment
  - Strategic recommendations
  - Implementation roadmap

**Presentation Builder Agent**:
- Input: Complete report + stakeholder requirements
- Output: Executive presentation deck
- Formats:
  - Board presentation (high-level strategic overview)
  - Detailed analysis presentation (comprehensive findings)
  - One-page executive summary (key insights only)
  - Interactive dashboard (ongoing monitoring)

### Stage 5: Validation & Quality Assurance (Parallel)
```json
{
  "agents": ["Fact Checker", "Bias Detector", "Completeness Validator"],
  "mode": "parallel",
  "input": "complete_report_package",
  "output": "quality_assured_intelligence_report"
}
```

**Fact Checker Agent**:
- Input: All claims and statistics in report
- Output: Fact-checked and validated intelligence
- Process: Cross-reference with authoritative sources, flag inconsistencies
- Quality Standard: 95%+ accuracy rate for all quantitative claims

**Bias Detector Agent**:
- Input: Analysis conclusions and recommendations
- Output: Bias assessment and neutrality recommendations
- Analysis: Unconscious bias detection, perspective balance check
- Objective: Ensure balanced and objective market assessment

**Completeness Validator Agent**:
- Input: Full report against original requirements
- Output: Completeness assessment and gap identification
- Validation: All research questions addressed, stakeholder needs met
- Quality Gate: 100% requirement coverage before final delivery

## Complete Workflow Example

### Execution Flow
```bash
🚀 Market Intelligence Report Generation Started
Target: Perth BRM Market Analysis Q1 2025

├── 📊 Stage 1: Data Collection (Parallel Multi-Source)
│   ├── Industry Research Agent: Perth tech sector analysis complete
│   │   ├── Government digital transformation: $2.3B investment pipeline
│   │   ├── Mining technology adoption: 34% increase in BRM roles
│   │   ├── Professional services growth: 12% YoY in Perth market
│   │   └── Industry trends: Hybrid roles, stakeholder management evolution
│   ├── Company Intelligence Agent: 47 target organizations profiled
│   │   ├── Government agencies: 12 major departments analyzed
│   │   ├── Mining companies: 18 major players assessed
│   │   ├── Professional services: 17 consulting firms reviewed
│   │   └── Hiring patterns: 23% increase in senior BRM positions
│   ├── Salary Market Agent: Compensation analysis complete
│   │   ├── Senior BRM range: $120k-$160k (Government), $140k-$180k (Mining)
│   │   ├── Market premium: 15% for Gov+Tech experience combination
│   │   ├── Negotiation intelligence: Skills-based salary variations identified
│   │   └── Benefits analysis: Total compensation packaging trends
│   └── Network Intelligence Agent: Professional ecosystem mapped
│       ├── Key decision makers: 89 influential contacts identified
│       ├── Perth business community: 156 relevant professionals
│       ├── Government connections: 34 department heads and senior managers
│       └── Referral opportunities: 23 warm introduction possibilities
│
├── 🔗 Stage 2: Data Integration & Analysis (Sequential)
│   ├── Data Integration Specialist: Unified dataset created
│   │   ├── Data points: 2,847 verified market data points
│   │   ├── Confidence score: 91% average data reliability
│   │   ├── Coverage: 94% of research objectives addressed
│   │   └── Data gaps: 3 minor areas identified for future research
│   ├── Market Analyst: Trend analysis complete
│   │   ├── Growth opportunity: 28% increase in BRM demand projected 2025-2027
│   │   ├── Skill evolution: Technical fluency becoming essential requirement
│   │   ├── Market dynamics: Shift toward outcome-based relationship management
│   │   └── Perth advantages: Government connections, mining expertise premium
│   └── Competitive Intelligence: Positioning analysis complete
│       ├── Market position: Top 15% of Perth BRM professionals
│       ├── Unique differentiators: Gov+Mining+Tech triangle positioning
│       ├── Competitive gaps: Enterprise architecture knowledge opportunity
│       └── Market entry: 3 strategic positioning recommendations
│
├── 💡 Stage 3: Insight Generation (Parallel Specialized Analysis)
│   ├── Opportunity Identifier: 7 specific opportunities identified
│   │   ├── Government digital transformation consulting (High potential)
│   │   ├── Mining technology advisory services (Medium-High potential)
│   │   ├── BRM training and methodology development (Medium potential)
│   │   ├── Interim/contract senior BRM roles (High potential)
│   │   ├── Board advisory positions in technology adoption (Medium potential)
│   │   ├── Speaking and thought leadership opportunities (Medium potential)
│   │   └── Joint venture partnerships with consulting firms (Low-Medium potential)
│   ├── Risk Assessor: Risk profile and mitigation strategies
│   │   ├── Economic risks: Moderate (mining commodity dependency)
│   │   ├── Technology disruption: Low-Medium (automation of routine BRM tasks)
│   │   ├── Geographic risks: Low (Perth market stability)
│   │   ├── Skills risks: Low (current skillset relevance high)
│   │   └── Mitigation: Continuous learning, network diversification
│   └── Strategy Formulator: Strategic recommendations developed
│       ├── Career strategy: Focus on government technology transformation roles
│       ├── Skill development: Enterprise architecture, AI/automation awareness
│       ├── Network expansion: Strengthen government and tech startup connections
│       └── Market positioning: Establish thought leadership in Gov+Tech BRM
│
├── 📋 Stage 4: Report Generation & Visualization (Sequential)
│   ├── Data Visualization Specialist: Professional visualizations created
│   │   ├── Market size chart: Perth BRM market $47M total addressable market
│   │   ├── Salary progression: Career trajectory with compensation benchmarks
│   │   ├── Competitive matrix: Positioning against 12 key competitors
│   │   ├── Geographic heatmap: Opportunity concentration by Perth region
│   │   └── Timeline visualization: 3-year market evolution projections
│   ├── Report Writer: Comprehensive 47-page market intelligence report
│   │   ├── Executive summary: Key findings and strategic recommendations
│   │   ├── Market analysis: Deep-dive into Perth BRM ecosystem
│   │   ├── Competitive landscape: Detailed positioning and differentiation
│   │   ├── Strategic recommendations: Actionable next steps with timelines
│   │   └── Implementation roadmap: 90-day, 6-month, 12-month action plans
│   └── Presentation Builder: Multi-format deliverables created
│       ├── Executive presentation: 23 slides for stakeholder communication
│       ├── Detailed analysis: 67 slides with comprehensive findings
│       ├── One-page summary: Key insights for quick reference
│       └── Dashboard concept: Ongoing market monitoring framework
│
└── ✅ Stage 5: Validation & Quality Assurance (Parallel)
    ├── Fact Checker: 97% accuracy rate achieved
    │   ├── 2,847 data points verified against authoritative sources
    │   ├── 23 statistics cross-referenced with multiple sources
    │   └── 3 minor corrections applied for precision
    ├── Bias Detector: Balanced perspective confirmed
    │   ├── Analysis methodology: Objective and systematic approach
    │   ├── Recommendation balance: Opportunities and risks equally weighted
    │   └── Perspective diversity: Multiple stakeholder viewpoints included
    └── Completeness Validator: 100% requirement coverage
        ├── All research questions comprehensively addressed
        ├── Stakeholder information needs fully met
        └── Actionable insights and next steps clearly defined

✅ Market Intelligence Report Complete
🎯 Next Action: Review executive summary and prioritize strategic recommendations
⏱️ Total Processing Time: 34 minutes
📊 Report Quality: 97% accuracy, 100% completeness, balanced perspective
💼 Strategic Value: Clear roadmap for next 12 months of career positioning
```

### Deliverable Package Structure
```
market_intelligence_report_Q1_2025/
├── executive_deliverables/
│   ├── executive_summary.pdf (2 pages)
│   ├── key_findings_presentation.pptx (23 slides)
│   └── one_page_strategic_overview.pdf
├── detailed_analysis/
│   ├── comprehensive_market_report.pdf (47 pages)
│   ├── detailed_analysis_presentation.pptx (67 slides)
│   ├── data_appendix.xlsx (raw data and calculations)
│   └── methodology_notes.md
├── visualizations/
│   ├── market_size_and_growth_charts.png
│   ├── competitive_positioning_matrix.png
│   ├── salary_progression_benchmarks.png
│   ├── geographic_opportunity_heatmap.png
│   └── industry_trends_timeline.png
├── strategic_recommendations/
│   ├── 90_day_action_plan.md
│   ├── 6_month_strategic_initiatives.md
│   ├── 12_month_positioning_roadmap.md
│   └── ongoing_monitoring_framework.md
├── supporting_data/
│   ├── company_intelligence_profiles/ (47 companies)
│   ├── salary_benchmarking_data.xlsx
│   ├── network_analysis_report.md
│   └── industry_research_sources.md
└── quality_assurance/
    ├── fact_checking_report.md
    ├── bias_assessment.md
    ├── completeness_validation.md
    └── data_confidence_scores.json
```

## Integration Points

### Cross-Agent Intelligence Sharing
- **Jobs Agent** benefits from salary and company intelligence
- **LinkedIn Optimizer** uses competitive positioning insights
- **Professional Brand Optimization** leverages market opportunity identification
- **Complete Application Pipeline** incorporates company intelligence and market positioning

### Success Metrics
- **Accuracy**: >95% fact-checked data reliability
- **Completeness**: 100% research objective coverage
- **Actionability**: Clear next steps with defined timelines
- **Strategic Value**: Measurable impact on career decision-making
- **Time Efficiency**: Complete intelligence report in <45 minutes

This command provides executive-level market intelligence that transforms career and business decision-making from intuition-based to data-driven strategic planning.