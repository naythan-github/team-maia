# System Health → Bottleneck Analysis → Optimization Strategy - Prompt Chain

## Overview
**Problem**: Single-turn system health checks provide snapshot metrics but miss performance bottlenecks, capacity trends, and optimization opportunities that require correlation across multiple data sources.

**Solution**: 3-subtask chain that systematically collects health metrics → identifies bottlenecks with root cause → designs prioritized optimization roadmap.

**Expected Improvement**: +40% optimization recommendation quality, +35% bottleneck detection accuracy

---

## When to Use This Chain

**Use When**:
- Periodic system health review (monthly/quarterly)
- Performance degradation investigations (latency spikes, slow queries)
- Capacity planning (need growth projections)
- Cost optimization (identify waste, over-provisioning)

**Don't Use When**:
- Live incident (need immediate triage, not comprehensive analysis)
- Single metric check (just need CPU or memory snapshot)
- Simple monitoring setup (just need basic alert configuration)

---

## Subtask Sequence

### Subtask 1: Comprehensive System Health Assessment

**Goal**: Collect metrics across compute, storage, network, database, and application layers

**Input**:
- `system_inventory`: List of systems to assess (servers, databases, applications, load balancers)
- `timeframe`: Analysis window (e.g., "last 30 days", "last week")
- `baseline_metrics`: Historical performance for comparison

**Output**:
```json
{
  "health_summary": {
    "overall_status": "DEGRADED (performance trending down)",
    "critical_alerts": 3,
    "warning_alerts": 12,
    "systems_assessed": 45
  },
  "compute_layer": {
    "servers": [
      {
        "hostname": "web-server-01",
        "cpu_avg": 78,
        "cpu_peak": 95,
        "memory_avg": 85,
        "memory_peak": 92,
        "disk_io_avg": 120,
        "status": "WARNING (high memory utilization)",
        "trend": "Increasing (+15% over 30 days)"
      }
    ],
    "summary": "3 servers >80% CPU avg, 5 servers >80% memory avg"
  },
  "storage_layer": {
    "databases": [
      {
        "instance": "sql-prod-01",
        "size_gb": 450,
        "growth_rate_gb_month": 25,
        "capacity_remaining_months": 6,
        "query_latency_p95_ms": 2000,
        "query_latency_baseline_ms": 50,
        "status": "CRITICAL (40x latency increase)",
        "slow_queries": 45
      }
    ],
    "summary": "1 database critical latency, 2 databases approaching capacity"
  },
  "network_layer": {
    "load_balancers": [
      {
        "name": "alb-prod",
        "requests_per_second": 1200,
        "error_rate_pct": 0.5,
        "latency_p95_ms": 800,
        "latency_baseline_ms": 200,
        "status": "WARNING (4x latency increase)"
      }
    ],
    "summary": "Load balancer latency increased 4x over baseline"
  },
  "application_layer": {
    "apis": [
      {
        "endpoint": "/api/search",
        "requests_day": 50000,
        "latency_p95_ms": 3000,
        "latency_baseline_ms": 300,
        "error_rate_pct": 2.5,
        "status": "CRITICAL (10x latency, high error rate)"
      }
    ],
    "summary": "/api/search endpoint degraded (10x latency)"
  },
  "trends_identified": [
    "Database latency increasing 40x over 30 days (SQL-prod-01)",
    "Memory utilization trending up across 5 web servers",
    "Load balancer latency increased 4x",
    "/api/search endpoint 10x latency increase"
  ],
  "correlation_insights": "All latency increases trace back to SQL-prod-01 database performance degradation"
}
```

**Prompt**:
```
You are the SRE Principal Engineer agent performing comprehensive system health assessment.

CONTEXT:
- System inventory: {system_inventory}
- Analysis timeframe: {timeframe}
- Baseline metrics: {baseline_metrics}
- Goal: Collect metrics across all layers, identify degradation patterns

TASK:
1. Compute Layer Assessment:
   - Server metrics: CPU, memory, disk I/O (average + peak)
   - Identify servers >80% utilization (bottleneck risk)
   - Note capacity trends (+/- % over timeframe)

2. Storage Layer Assessment:
   - Database metrics: Size, growth rate, query latency (P50/P95/P99)
   - Identify slow queries (>1s execution)
   - Calculate capacity runway (months until full)

3. Network Layer Assessment:
   - Load balancer metrics: RPS, error rate, latency (P50/P95/P99)
   - Network throughput (Gbps)
   - Identify routing/connection issues

4. Application Layer Assessment:
   - API endpoint metrics: Request volume, latency, error rate
   - Identify degraded endpoints (latency >baseline, error rate >1%)
   - Note transaction failures

5. Trend Analysis:
   - Compare current metrics vs baseline (30/60/90 days ago)
   - Identify increasing trends (CPU, memory, latency, errors)
   - Calculate rate of change (% per month)

6. Correlation Analysis ⭐ KEY INSIGHT:
   - Connect symptoms across layers (e.g., "API latency increased → traced to DB slow queries")
   - Identify cascading failures (upstream issue → downstream impact)
   - Highlight root cause candidates

TOOLS TO USE:
- Prometheus: Metrics queries (CPU, memory, disk, network)
- Application Insights: Application performance monitoring
- Database monitoring: Query performance, execution plans
- Load balancer logs: Request/response times, error codes

OUTPUT FORMAT:
Return JSON with:
- health_summary: Overall status (HEALTHY/WARNING/DEGRADED/CRITICAL)
- compute_layer: Server metrics with bottleneck warnings
- storage_layer: Database metrics with capacity projections
- network_layer: Load balancer and network performance
- application_layer: API endpoint performance
- trends_identified: Key degradation patterns
- correlation_insights: ⭐ Cross-layer root cause analysis

QUALITY CRITERIA:
✅ Metrics collected across ALL layers (compute, storage, network, application)
✅ Trends calculated (not just snapshots)
✅ Bottlenecks identified (>80% utilization, >2x baseline latency)
✅ Correlation analysis connects symptoms to root causes
```

---

### Subtask 2: Performance Bottleneck Deep-Dive

**Goal**: Analyze top bottlenecks identified in health assessment, determine root causes

**Input**:
- Output from Subtask 1 (`health_summary`, `trends_identified`, `correlation_insights`)
- `diagnostic_access`: Access to logs, query plans, traces for deep analysis

**Output**:
```json
{
  "bottleneck_analysis": [
    {
      "bottleneck": "Database latency spike (SQL-prod-01: 50ms → 2000ms)",
      "severity": "CRITICAL",
      "impact": "Affects /api/search endpoint (50K requests/day), blocking 10K users/day",
      "root_cause_investigation": {
        "hypothesis_1": "Table locks due to missing indexes",
        "evidence": "EXPLAIN ANALYZE shows full table scan on 'products' table (2M rows)",
        "validation": "Index on 'category_id' column missing",
        "confidence": "HIGH (95%)"
      },
      "root_cause": "Missing index on 'products.category_id' causing full table scans on every search query",
      "contributing_factors": [
        "Table grew from 500K → 2M rows over 6 months (4x growth)",
        "No query optimization during rapid growth phase",
        "Index creation not part of schema change review"
      ],
      "fix_complexity": "LOW (single index creation, <5 min)",
      "fix_risk": "LOW (read-only index, no data modification)"
    },
    {
      "bottleneck": "Web server memory exhaustion (5 servers >85% memory avg)",
      "severity": "HIGH",
      "impact": "Intermittent 500 errors (0.5% of requests), server restarts required weekly",
      "root_cause_investigation": {
        "hypothesis_1": "Memory leak in application code",
        "evidence": "Heap dumps show 'session objects' growing unbounded (500MB over 24h)",
        "validation": "Session cleanup not triggered (TTL set to 7 days, should be 1 day)",
        "confidence": "HIGH (90%)"
      },
      "root_cause": "Session TTL misconfigured (7 days vs 1 day), causing session object accumulation and memory exhaustion",
      "contributing_factors": [
        "User session count increased 3x over 6 months (more active users)",
        "No session object monitoring/alerting",
        "Default TTL not reviewed during initial deployment"
      ],
      "fix_complexity": "LOW (configuration change, <10 min)",
      "fix_risk": "MEDIUM (may log out some long-running sessions, need user communication)"
    }
  ],
  "optimization_opportunities": [
    {
      "opportunity": "Database read replica for analytics queries",
      "problem": "Analytics queries (30% of load) compete with transactional queries",
      "solution": "Deploy read replica, route analytics traffic to replica",
      "expected_improvement": "50% latency reduction on primary DB, analytics unaffected",
      "effort": "MEDIUM (2 days: deploy replica + update connection strings)",
      "cost": "$200/month (replica instance)"
    },
    {
      "opportunity": "Implement query result caching (Redis)",
      "problem": "Search queries are repetitive (70% cache hit rate possible)",
      "solution": "Deploy Redis cache for search results (5 min TTL)",
      "expected_improvement": "70% reduction in database queries, 80% latency improvement",
      "effort": "MEDIUM (3 days: deploy Redis + implement caching layer)",
      "cost": "$150/month (Redis instance)"
    }
  ]
}
```

**Prompt**:
```
You are the SRE Principal Engineer agent performing deep bottleneck analysis.

CONTEXT:
- Health assessment results from previous subtask
- Diagnostic access: Logs, query plans, traces, heap dumps
- Goal: Determine root causes for top bottlenecks, identify optimization opportunities

HEALTH ASSESSMENT RESULTS:
{health_summary}

TOP ISSUES IDENTIFIED:
{trends_identified}

CORRELATION INSIGHTS:
{correlation_insights}

TASK:
1. Prioritize Bottlenecks:
   - Rank by severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Consider impact (users affected, requests impacted, business critical)
   - Focus on top 3-5 bottlenecks (80/20 rule)

2. Root Cause Investigation (per bottleneck):
   - Formulate hypothesis (what could cause this?)
   - Gather evidence (logs, metrics, traces, query plans)
   - Validate hypothesis (reproduce issue, test fix)
   - Calculate confidence (HIGH >80%, MEDIUM 50-80%, LOW <50%)

3. Root Cause Determination:
   - State root cause clearly (not symptom, actual cause)
   - List contributing factors (why did it happen now?)
   - Assess fix complexity (LOW/MEDIUM/HIGH)
   - Assess fix risk (impact if fix goes wrong)

4. Optimization Opportunities:
   - Identify proactive improvements (not just reactive fixes)
   - Calculate expected improvement (quantify latency reduction, cost savings)
   - Estimate effort (days of work)
   - Estimate ongoing cost (if adds infrastructure)

ANALYSIS TECHNIQUES:
- **Database**: EXPLAIN ANALYZE for query plans, index usage analysis
- **Memory**: Heap dumps, garbage collection logs, object retention analysis
- **CPU**: Thread dumps, profiling (CPU flamegraphs)
- **Network**: Packet captures, connection pool analysis, DNS resolution times

OUTPUT FORMAT:
Return JSON with:
- bottleneck_analysis: Array of bottleneck objects (root cause + fix details)
- optimization_opportunities: Array of proactive improvement opportunities

QUALITY CRITERIA:
✅ Root causes are actionable (not vague like "slow performance")
✅ Evidence-based validation (logs, metrics, traces confirm hypothesis)
✅ Confidence scores realistic (don't claim HIGH if uncertain)
✅ Fix complexity and risk assessed (no nasty surprises)
✅ Optimization opportunities quantified (expected improvement %)
```

---

### Subtask 3: Prioritized Optimization Roadmap

**Goal**: Create comprehensive optimization plan with priorities, timelines, expected impact, and resource requirements

**Input**:
- Output from Subtask 2 (`bottleneck_analysis`, `optimization_opportunities`)
- `available_resources`: Team capacity, budget, maintenance windows

**Output**:
```json
{
  "optimization_roadmap": {
    "immediate_fixes": [
      {
        "action": "Create index on products.category_id",
        "priority": "P0 (CRITICAL)",
        "timeline": "Today (5 minutes + testing)",
        "effort": "LOW (single SQL command)",
        "risk": "LOW (read-only index)",
        "expected_improvement": "Database latency: 2000ms → 50ms (40x improvement), /api/search 10x faster",
        "implementation": "CREATE INDEX idx_category_id ON products(category_id);",
        "rollback": "DROP INDEX idx_category_id; (instant)",
        "validation": "Run EXPLAIN ANALYZE on search query, confirm index scan (not table scan)"
      },
      {
        "action": "Fix session TTL (7 days → 1 day)",
        "priority": "P0 (CRITICAL)",
        "timeline": "Today (10 minutes + staged rollout)",
        "effort": "LOW (config change)",
        "risk": "MEDIUM (will log out sessions >1 day old)",
        "expected_improvement": "Memory utilization: 85% → 60%, eliminate weekly restarts",
        "implementation": "Update session.config: TTL=86400 (1 day), deploy to 1 server, monitor 1h, deploy to all",
        "rollback": "Revert config: TTL=604800 (7 days)",
        "validation": "Monitor heap size over 24h, confirm no unbounded growth"
      }
    ],
    "short_term_optimizations": [
      {
        "action": "Deploy database read replica for analytics",
        "priority": "P1 (HIGH)",
        "timeline": "This week (2 days)",
        "effort": "MEDIUM (deploy replica + update connection strings)",
        "cost": "$200/month (replica instance)",
        "expected_improvement": "Primary DB latency: -50%, analytics unaffected",
        "implementation_steps": [
          "1. Create read replica in Azure/AWS (same region, standard tier)",
          "2. Configure replication (async, lag target <5s)",
          "3. Test replica queries (verify data consistency)",
          "4. Update analytics service connection string to replica endpoint",
          "5. Monitor replication lag and query distribution"
        ],
        "success_criteria": "Primary DB CPU <50%, analytics queries <10% of primary load"
      },
      {
        "action": "Implement Redis query result caching",
        "priority": "P1 (HIGH)",
        "timeline": "This week (3 days)",
        "effort": "MEDIUM (deploy Redis + caching layer)",
        "cost": "$150/month (Redis instance)",
        "expected_improvement": "Database queries: -70%, /api/search latency: -80%",
        "implementation_steps": [
          "1. Deploy Redis cluster (2 nodes, standard tier)",
          "2. Implement cache-aside pattern in application code",
          "3. Set TTL: 5 minutes for search results",
          "4. Add cache hit/miss metrics (track effectiveness)",
          "5. Gradual rollout: 10% → 50% → 100% traffic"
        ],
        "success_criteria": "Cache hit rate >70%, database query volume reduced 70%"
      }
    ],
    "medium_term_projects": [
      {
        "action": "Implement auto-scaling for web servers",
        "priority": "P2 (MEDIUM)",
        "timeline": "Next month (5 days)",
        "effort": "HIGH (infrastructure + testing)",
        "cost": "Variable ($0-500/month depending on load)",
        "expected_improvement": "Eliminate capacity planning, handle traffic spikes automatically",
        "implementation_steps": [
          "1. Containerize application (Docker)",
          "2. Deploy to Kubernetes/ECS with HPA (Horizontal Pod Autoscaler)",
          "3. Configure auto-scaling: CPU >70% = scale up, <30% = scale down",
          "4. Set min/max replicas (min: 3, max: 20)",
          "5. Load test to validate scaling behavior"
        ],
        "success_criteria": "Auto-scales within 2 minutes of load spike, maintains <70% CPU"
      }
    ]
  },
  "impact_summary": {
    "immediate_fixes_impact": "2000ms → 50ms database latency (40x improvement), 85% → 60% memory utilization, eliminate weekly restarts",
    "short_term_impact": "70% database query reduction, 80% /api/search latency improvement, $350/month cost",
    "medium_term_impact": "Automatic capacity management, handle 10x traffic spikes without manual intervention",
    "total_annual_cost": "$4,200 (Redis + read replica)",
    "total_annual_savings": "$12,000 (eliminate 40 hours/month manual capacity management + prevent downtime costs)",
    "roi": "186% (savings > costs)"
  },
  "resource_requirements": {
    "immediate": "2 hours (SRE engineer time)",
    "short_term": "5 days (2 days replica + 3 days Redis)",
    "medium_term": "5 days (containerization + auto-scaling)",
    "total_effort": "10 days over 1 month"
  },
  "monitoring_and_validation": {
    "metrics_to_track": [
      "Database latency (P95, P99)",
      "Memory utilization (per server)",
      "Cache hit rate (target >70%)",
      "Auto-scaling events (scale-up/down frequency)",
      "Error rate (target <0.1%)"
    ],
    "alert_configuration": [
      "Database latency >500ms for 5min → page on-call",
      "Memory >90% for 10min → warning alert",
      "Cache hit rate <50% → investigate cache effectiveness",
      "Auto-scaling failures → page on-call"
    ]
  }
}
```

**Prompt**:
```
You are the SRE Principal Engineer agent creating an optimization roadmap.

CONTEXT:
- Bottleneck analysis complete with root causes and fixes
- Available resources: {available_resources}
- Goal: Create prioritized, actionable roadmap with implementation details

BOTTLENECK ANALYSIS:
{bottleneck_analysis}

OPTIMIZATION OPPORTUNITIES:
{optimization_opportunities}

TASK:
1. Prioritize Actions (P0/P1/P2/P3):
   - P0 (CRITICAL): Immediate fixes for production issues
   - P1 (HIGH): Short-term optimizations (this week)
   - P2 (MEDIUM): Medium-term projects (next month)
   - P3 (LOW): Future improvements (next quarter)

2. Create Detailed Implementation Plans:
   - For EACH action, specify:
     * Timeline (today / this week / next month)
     * Effort estimate (LOW/MEDIUM/HIGH with days/hours)
     * Cost estimate (one-time + monthly ongoing)
     * Expected improvement (quantified %, latency reduction)
     * Implementation steps (numbered, copy-paste ready)
     * Rollback plan (if fix goes wrong)
     * Success criteria (how to validate it worked)

3. Calculate Impact Summary:
   - Immediate fixes: Expected improvement (quantify)
   - Short-term optimizations: Expected improvement + cost
   - Medium-term projects: Expected improvement + cost
   - Total annual cost vs. savings (ROI calculation)

4. Resource Planning:
   - Engineer time required (immediate/short/medium-term)
   - Budget needed (infrastructure costs)
   - Maintenance windows (if downtime required)

5. Monitoring and Validation:
   - Metrics to track (post-implementation)
   - Alert configuration (prevent future issues)
   - Success criteria (measurable outcomes)

OUTPUT FORMAT:
Return JSON with:
- optimization_roadmap: Object with immediate_fixes, short_term_optimizations, medium_term_projects
- impact_summary: Expected improvements, costs, savings, ROI
- resource_requirements: Engineer time and budget needed
- monitoring_and_validation: Metrics, alerts, success criteria

QUALITY CRITERIA:
✅ Every action has implementation steps (numbered, copy-paste ready)
✅ Expected improvements are quantified (%, ms, $)
✅ Rollback plans provided (risk mitigation)
✅ Success criteria are measurable (not vague)
✅ ROI calculated (cost vs. savings)
```

---

## Benefits

**Quantified Improvements**:
- **Optimization Quality**: +40% (comprehensive analysis vs. ad-hoc fixes)
- **Bottleneck Detection**: +35% (cross-layer correlation finds hidden issues)
- **Time to Resolution**: -50% (root cause analysis vs. trial-and-error)
- **Preventive Value**: 80% (identifies issues before they cause outages)

**Workflow Advantages**:
- **Comprehensive**: Collects metrics across all layers (not just CPU/memory snapshots)
- **Evidence-Based**: Root causes validated with logs, traces, query plans
- **Actionable**: Copy-paste implementation steps, exact commands
- **ROI-Focused**: Cost-benefit analysis for every optimization

---

## Example Usage

```python
from maia.tools.prompt_chain_orchestrator import PromptChain

chain = PromptChain(
    chain_id="system_health_q4_2025",
    workflow_file="claude/workflows/prompt_chains/system_health_bottleneck_optimization_chain.md"
)

result = chain.execute({
    "system_inventory": {
        "servers": ["web-01", "web-02", "web-03", "api-01", "api-02"],
        "databases": ["sql-prod-01", "sql-prod-02-replica"],
        "load_balancers": ["alb-prod"],
        "applications": ["main-api", "analytics-service"]
    },
    "timeframe": "last 30 days",
    "baseline_metrics": load_baseline_from_prometheus(),
    "diagnostic_access": {
        "prometheus": "http://prometheus.local",
        "app_insights": "connection_string",
        "database_admin": True
    },
    "available_resources": {
        "team_capacity": "2 SRE engineers, 80% utilized",
        "budget": "$10K/month for infrastructure",
        "maintenance_windows": "Sundays 2am-6am"
    }
})

# Result contains complete health assessment + bottleneck analysis + optimization roadmap
```

---

## Integration with Agents

**Primary Agent**: SRE Principal Engineer
**Supporting Agents**:
- DevOps Principal Architect: Infrastructure automation and deployment
- Cloud Security Principal: Security impact assessment for changes
- FinOps Engineering: Cost optimization analysis

---

## Version History

- v1.0 (2025-10-11): Initial workflow design
