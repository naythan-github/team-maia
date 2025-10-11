# Incident Detection → Diagnosis → Remediation → Post-Mortem Chain

## Workflow Metadata
- **Chain ID**: `incident_detection_diagnosis_remediation_chain`
- **Version**: 1.0
- **Primary Agent**: SRE Infrastructure Reliability Agent
- **Supporting Agents**: Cloud Security Principal, DevOps Principal Architect
- **Estimated Time**: 60-90 minutes (15-20 min per subtask)
- **Expected Improvement**: +45% faster incident resolution, +60% root cause identification accuracy

## Workflow Purpose
Transform incident response from reactive firefighting into systematic diagnosis and remediation with learning integration. Uses SRE best practices including incident severity classification, structured troubleshooting, and blameless post-mortems.

## Input Requirements
```json
{
  "incident_id": "INC-2025-1234",
  "reported_by": "Automated monitoring | User report | Engineering",
  "initial_symptoms": "High CPU on web servers | Database connection timeout | 500 errors",
  "affected_services": ["web-app", "api-gateway", "postgres-db"],
  "start_time": "2025-10-11T14:32:00Z",
  "customer_impact": "Critical | High | Medium | Low",
  "monitoring_alerts": ["CPU >90%", "P95 latency >5s", "Error rate >5%"],
  "environment": "Production | Staging | Development",
  "recent_changes": {
    "deployments": ["web-app v2.3.1 deployed 1 hour ago"],
    "infrastructure": ["No recent changes"],
    "configuration": ["Database connection pool increased to 100"]
  }
}
```

## Subtasks

---

### Subtask 1: Incident Detection & Triage
**Agent**: SRE Infrastructure Reliability Agent
**Goal**: Classify severity, establish incident command, gather initial telemetry
**Input Variables**: `incident_id`, `initial_symptoms`, `affected_services`, `customer_impact`, `monitoring_alerts`, `recent_changes`
**Output Variables**: `severity_classification`, `incident_command_structure`, `telemetry_snapshot`, `immediate_actions`

**Prompt**:
```
You are the SRE Infrastructure Reliability agent triaging a production incident.

CONTEXT:
- Incident ID: {{incident_id}}
- Reported By: {{reported_by}}
- Start Time: {{start_time}}
- Initial Symptoms: {{initial_symptoms}}
- Affected Services: {{affected_services}}
- Customer Impact: {{customer_impact}}
- Monitoring Alerts: {{monitoring_alerts}}
- Recent Changes: {{recent_changes}}

TASK:
Perform structured incident triage following SRE best practices:

1. **Severity Classification** (Use Google SRE severity matrix)
   - **SEV-1 (Critical)**: Complete service outage, revenue-impacting, customer data loss
   - **SEV-2 (High)**: Major functionality degraded, significant user impact
   - **SEV-3 (Medium)**: Minor functionality degraded, workaround available
   - **SEV-4 (Low)**: Cosmetic issue, no customer impact

   Criteria for classification:
   - Customer impact scope (% users affected)
   - Business impact (revenue, reputation, SLA)
   - Security implications (data breach, unauthorized access)
   - Blast radius (number of services affected)

2. **Incident Command Structure**
   - Incident Commander (IC): Who leads response?
   - Communications Lead: Who updates stakeholders?
   - Technical Lead: Who drives technical investigation?
   - Scribe: Who documents timeline and actions?

   For SEV-1/SEV-2, immediately page:
   - On-call SRE (technical lead)
   - Engineering manager (incident commander)
   - Customer support lead (communications)

3. **Initial Telemetry Gathering**
   Collect baseline metrics (last 1 hour):
   - **Compute**: CPU, memory, disk I/O per service
   - **Network**: Latency, throughput, error rates
   - **Application**: Request rate, error rate, P50/P95/P99 latency
   - **Database**: Connections, query duration, locks, replication lag
   - **Infrastructure**: Load balancer health, autoscaling events, pod restarts

4. **Immediate Stabilization Actions**
   - Can we roll back recent deployment? (if deployment within last 2 hours)
   - Can we scale horizontally? (increase replicas to handle load)
   - Can we fail over to standby region? (if multi-region setup)
   - Can we enable circuit breakers? (prevent cascading failures)
   - Can we shed non-critical traffic? (prioritize critical endpoints)

OUTPUT FORMAT (JSON):
{
  "severity_classification": {
    "severity": "SEV-1",
    "justification": "Complete outage of production API affecting 100% of users, revenue-impacting",
    "customer_impact_scope": "100% of users",
    "business_impact": "Revenue loss: $5K/hour, SLA breach imminent",
    "security_implications": "None identified",
    "blast_radius": "3 services (web-app, api-gateway, postgres-db)"
  },
  "incident_command_structure": {
    "incident_commander": "Sarah Chen (Engineering Manager)",
    "technical_lead": "Mike Rodriguez (On-call SRE)",
    "communications_lead": "Jane Smith (Customer Support Lead)",
    "scribe": "AI Agent (Maia SRE)",
    "war_room": "Slack #incident-response, Zoom bridge active"
  },
  "telemetry_snapshot": {
    "compute": {
      "web_app": {"cpu": "92%", "memory": "78%", "replicas": 3},
      "api_gateway": {"cpu": "45%", "memory": "60%", "replicas": 2},
      "postgres_db": {"cpu": "88%", "memory": "95%", "connections": 98}
    },
    "application_metrics": {
      "request_rate": "1200 req/s (normal: 800 req/s)",
      "error_rate": "15% (normal: 0.1%)",
      "p95_latency": "8.5s (normal: 200ms)"
    },
    "database_metrics": {
      "active_connections": "98/100 (max_connections reached)",
      "longest_query": "45s (SELECT * FROM users WHERE...)",
      "locks": "12 locks waiting",
      "replication_lag": "0s (healthy)"
    },
    "recent_events": [
      "2025-10-11T14:30:00Z - Deployment: web-app v2.3.1",
      "2025-10-11T14:32:00Z - Alert: Database connections at 95%",
      "2025-10-11T14:33:00Z - Alert: P95 latency >5s",
      "2025-10-11T14:35:00Z - Alert: Error rate >5%"
    ]
  },
  "immediate_actions": [
    {
      "action": "Roll back web-app deployment to v2.3.0",
      "rationale": "Deployment 1 hour ago correlates with incident start",
      "risk": "Low - rollback is safe, v2.3.0 was stable",
      "estimated_time": "5 minutes",
      "owner": "Mike Rodriguez (SRE)"
    },
    {
      "action": "Increase database connection pool from 100 to 200",
      "rationale": "Database connections at max capacity (98/100)",
      "risk": "Medium - may increase DB memory pressure",
      "estimated_time": "2 minutes",
      "owner": "Mike Rodriguez (SRE)"
    },
    {
      "action": "Scale web-app from 3 to 6 replicas",
      "rationale": "High CPU (92%) may indicate insufficient capacity",
      "risk": "Low - autoscaling will handle load distribution",
      "estimated_time": "3 minutes",
      "owner": "Kubernetes autoscaler"
    }
  ],
  "status_page_message": "We are investigating elevated error rates and latency. Our team is actively working on resolution. Updates every 15 minutes."
}

QUALITY CRITERIA:
✅ Severity classified using objective criteria (not subjective)
✅ Incident command structure assigned with specific names/roles
✅ Telemetry snapshot includes all critical metrics with baselines
✅ Immediate actions prioritized by risk and impact
✅ Timeline preserved with exact timestamps
```

**Expected Output Size**: 120-150 lines JSON

---

### Subtask 2: Root Cause Diagnosis
**Agent**: SRE Infrastructure Reliability Agent
**Goal**: Systematic root cause identification using 5-Whys and telemetry analysis
**Input Variables**: `subtask_1_output`, `incident_id`, `affected_services`, `recent_changes`
**Output Variables**: `root_cause_analysis`, `contributing_factors`, `evidence_trail`, `correlation_analysis`

**Prompt**:
```
You are the SRE Infrastructure Reliability agent conducting systematic root cause diagnosis.

CONTEXT:
- Incident: {{incident_id}} ({{subtask_1_output.severity_classification.severity}})
- Telemetry: {{subtask_1_output.telemetry_snapshot}}
- Immediate Actions Taken: {{subtask_1_output.immediate_actions}}
- Affected Services: {{affected_services}}
- Recent Changes: {{recent_changes}}

TASK:
Perform structured root cause analysis using multiple methodologies:

1. **5-Whys Analysis**
   Start with observed symptom and ask "Why?" 5 times:

   Example:
   - **Symptom**: API returning 500 errors at 15% rate
   - **Why 1?** Database connection pool exhausted (98/100 connections)
   - **Why 2?** Web app creating too many connections
   - **Why 3?** Connection leak in new deployment (v2.3.1)
   - **Why 4?** New feature didn't close connections in error path
   - **Why 5?** Code review missed edge case testing

   **Root Cause**: Insufficient error path testing in code review process

2. **Timeline Correlation Analysis**
   Map events chronologically to identify trigger:
   - When did metrics first deviate from baseline?
   - What changed in the 2 hours before incident?
   - Are there recurring patterns (daily/weekly cycles)?
   - Was there a deployment, config change, or traffic spike?

3. **Cross-Service Dependency Analysis**
   Identify cascading failures:
   - Which service degraded first?
   - How did failure propagate to dependent services?
   - Were circuit breakers triggered?
   - Did retry storms amplify the issue?

4. **Infrastructure Layer Analysis**
   Check all layers of the stack:
   - **Application**: Code bugs, memory leaks, infinite loops
   - **Platform**: Kubernetes, Docker, orchestration issues
   - **Database**: Slow queries, locks, replication lag
   - **Network**: Latency, packet loss, DNS issues
   - **Cloud**: VM performance, disk throttling, regional outage

5. **Evidence Collection**
   Gather concrete evidence supporting root cause:
   - Log samples showing errors
   - Metrics graphs showing correlation
   - Code diffs from recent deployment
   - Configuration changes
   - External dependency status (third-party APIs)

OUTPUT FORMAT (JSON):
{
  "root_cause_analysis": {
    "five_whys": {
      "symptom": "API returning 500 errors at 15% rate, P95 latency 8.5s",
      "why_1": {
        "question": "Why are we getting 500 errors?",
        "answer": "Database connection pool exhausted (98/100 connections)",
        "evidence": "Database metric: active_connections=98, max_connections=100"
      },
      "why_2": {
        "question": "Why is connection pool exhausted?",
        "answer": "Web app creating more connections than expected",
        "evidence": "Web app logs: 'Connection pool timeout after 30s'"
      },
      "why_3": {
        "question": "Why is web app creating more connections?",
        "answer": "Connection leak in new deployment v2.3.1",
        "evidence": "Code diff: UserService.java added new feature without proper connection cleanup"
      },
      "why_4": {
        "question": "Why does new feature leak connections?",
        "answer": "Error path doesn't close database connection in finally block",
        "evidence": "Code review: https://github.com/org/repo/pull/1234/files#L45"
      },
      "why_5": {
        "question": "Why did code review miss this?",
        "answer": "No unit test coverage for error paths, manual testing only covered happy path",
        "evidence": "Coverage report: UserService error path 0% coverage"
      },
      "root_cause": "Insufficient error path testing in code review process allowed connection leak to reach production"
    },
    "primary_root_cause": "Connection leak in UserService.java error handling path (v2.3.1 deployment)",
    "root_cause_category": "Software Bug - Resource Leak"
  },
  "contributing_factors": [
    {
      "factor": "Database connection pool too small (100 connections)",
      "impact": "Medium",
      "explanation": "Amplified impact of connection leak. Production traffic requires 150+ connections for normal operation."
    },
    {
      "factor": "No automated rollback on elevated error rate",
      "impact": "Medium",
      "explanation": "Deployment succeeded despite immediate error rate increase. Should have triggered automatic rollback."
    },
    {
      "factor": "Insufficient pre-production testing",
      "impact": "High",
      "explanation": "Staging environment has smaller connection pool (50) than production (100), masking the issue."
    }
  ],
  "evidence_trail": [
    {
      "timestamp": "2025-10-11T14:30:00Z",
      "event": "Deployment: web-app v2.3.1",
      "evidence_type": "Deployment log",
      "evidence": "kubectl rollout history deployment/web-app"
    },
    {
      "timestamp": "2025-10-11T14:32:00Z",
      "event": "Database connections reached 95%",
      "evidence_type": "Metric",
      "evidence": "SELECT count(*) FROM pg_stat_activity WHERE state='active'; -- Result: 95"
    },
    {
      "timestamp": "2025-10-11T14:33:00Z",
      "event": "Error logs: 'Connection pool timeout'",
      "evidence_type": "Application log",
      "evidence": "java.sql.SQLException: Cannot get connection, pool exhausted"
    },
    {
      "timestamp": "2025-10-11T14:35:00Z",
      "event": "Error rate >5% threshold breached",
      "evidence_type": "Metric",
      "evidence": "Grafana dashboard: API error rate = 15%"
    }
  ],
  "correlation_analysis": {
    "deployment_correlation": {
      "deployment_time": "2025-10-11T14:30:00Z",
      "incident_start_time": "2025-10-11T14:32:00Z",
      "time_delta": "2 minutes",
      "correlation_confidence": "Very High (deployment is likely trigger)"
    },
    "traffic_correlation": {
      "traffic_pattern": "Normal (1200 req/s, baseline 800 req/s)",
      "spike_observed": false,
      "correlation_confidence": "Low (traffic spike not the cause)"
    },
    "infrastructure_correlation": {
      "infrastructure_changes": "None in last 24 hours",
      "cloud_incidents": "No Azure incidents in region",
      "correlation_confidence": "Very Low (infrastructure not the cause)"
    }
  },
  "affected_code": {
    "file": "src/main/java/com/example/UserService.java",
    "method": "getUserPreferences()",
    "lines": "142-165",
    "issue": "Connection not closed in catch block",
    "code_snippet": "catch (SQLException e) {\n    logger.error(\"Database error\", e);\n    return null; // <-- Missing: conn.close()\n}"
  }
}

QUALITY CRITERIA:
✅ 5-Whys methodology applied with evidence for each "Why"
✅ Primary root cause identified with category (bug/config/infrastructure)
✅ Contributing factors listed with impact assessment
✅ Evidence trail chronological with exact timestamps
✅ Correlation analysis quantified (confidence levels)
```

**Expected Output Size**: 180-220 lines JSON

---

### Subtask 3: Remediation & Recovery
**Agent**: SRE Infrastructure Reliability Agent + DevOps Principal Architect
**Goal**: Execute remediation plan, validate recovery, prevent recurrence
**Input Variables**: `subtask_1_output`, `subtask_2_output`, `incident_id`, `affected_services`
**Output Variables**: `remediation_plan`, `recovery_validation`, `prevention_measures`, `timeline`

**Prompt**:
```
You are the SRE agent executing incident remediation and recovery.

CONTEXT:
- Incident: {{incident_id}} ({{subtask_1_output.severity_classification.severity}})
- Root Cause: {{subtask_2_output.root_cause_analysis.primary_root_cause}}
- Contributing Factors: {{subtask_2_output.contributing_factors}}
- Immediate Actions Taken: {{subtask_1_output.immediate_actions}}
- Affected Services: {{affected_services}}

TASK:
Execute systematic remediation following SRE recovery playbook:

1. **Immediate Remediation** (Stop the bleeding)
   - Roll back problematic deployment
   - Scale infrastructure to handle load
   - Enable circuit breakers to prevent cascading failures
   - Redirect traffic to healthy region (if multi-region)
   - Kill long-running queries (if database issue)

2. **Root Cause Fix** (Permanent solution)
   - Code fix: Patch the bug identified in root cause analysis
   - Configuration fix: Adjust settings (e.g., increase connection pool)
   - Infrastructure fix: Add capacity or redundancy
   - Process fix: Update deployment checklist or runbook

3. **Recovery Validation** (Confirm system health)
   - Metrics returned to baseline:
     * Error rate <0.5% (baseline: 0.1%)
     * P95 latency <500ms (baseline: 200ms)
     * CPU <70% (baseline: 60%)
     * Database connections <80% capacity
   - End-to-end smoke tests passing
   - Customer reports confirm resolution
   - No new alerts firing

4. **Prevention Measures** (Never repeat)
   - **Detection**: Add monitoring/alerts to catch this earlier
   - **Prevention**: Add automated checks to prevent deployment
   - **Mitigation**: Add circuit breakers or rate limiting
   - **Testing**: Add test cases to catch this in CI/CD

5. **Communication** (Stakeholder updates)
   - Internal: Engineering, support, executives
   - External: Status page update, customer emails (if needed)
   - Timing: Updates every 15 min during incident, final "all clear" message

OUTPUT FORMAT (JSON):
{
  "remediation_plan": {
    "immediate_actions": [
      {
        "action": "Roll back web-app from v2.3.1 to v2.3.0",
        "command": "kubectl rollout undo deployment/web-app",
        "executed_at": "2025-10-11T14:40:00Z",
        "executed_by": "Mike Rodriguez (SRE)",
        "result": "Success - rollout completed in 3 minutes",
        "impact": "Error rate dropped from 15% to 2% within 2 minutes"
      },
      {
        "action": "Increase database connection pool from 100 to 200",
        "command": "kubectl set env deployment/web-app DB_MAX_CONNECTIONS=200",
        "executed_at": "2025-10-11T14:43:00Z",
        "executed_by": "Mike Rodriguez (SRE)",
        "result": "Success - pods restarted with new config",
        "impact": "Database connection utilization dropped to 40%"
      },
      {
        "action": "Scale web-app from 3 to 6 replicas",
        "command": "kubectl scale deployment/web-app --replicas=6",
        "executed_at": "2025-10-11T14:45:00Z",
        "executed_by": "Kubernetes HPA (autoscaler)",
        "result": "Success - 6 pods running",
        "impact": "CPU utilization dropped from 92% to 55%"
      }
    ],
    "root_cause_fix": {
      "fix_description": "Add proper connection cleanup in UserService error path",
      "code_change": {
        "file": "src/main/java/com/example/UserService.java",
        "method": "getUserPreferences()",
        "diff": "```diff\n- catch (SQLException e) {\n-     logger.error(\"Database error\", e);\n-     return null;\n- }\n+ catch (SQLException e) {\n+     logger.error(\"Database error\", e);\n+     return null;\n+ } finally {\n+     if (conn != null) conn.close();\n+ }\n```"
      },
      "pull_request": "https://github.com/org/repo/pull/1245",
      "code_review": "Reviewed by 2 senior engineers, approved",
      "testing": "Unit test coverage: 100% (happy path + error path), integration tests passed",
      "deployment_plan": "Deploy to staging tomorrow, production in 24 hours after soak test"
    }
  },
  "recovery_validation": {
    "metrics_health": {
      "error_rate": {
        "current": "0.08%",
        "baseline": "0.1%",
        "status": "✅ Healthy (below baseline)"
      },
      "p95_latency": {
        "current": "180ms",
        "baseline": "200ms",
        "status": "✅ Healthy (below baseline)"
      },
      "cpu_utilization": {
        "current": "55%",
        "baseline": "60%",
        "status": "✅ Healthy (below baseline)"
      },
      "database_connections": {
        "current": "78/200 (39%)",
        "baseline": "60/100 (60%)",
        "status": "✅ Healthy (well below capacity)"
      }
    },
    "smoke_tests": [
      {
        "test": "User login flow",
        "result": "✅ Passed (response time: 120ms)"
      },
      {
        "test": "Get user preferences (affected endpoint)",
        "result": "✅ Passed (response time: 95ms)"
      },
      {
        "test": "Database connection pool stress test",
        "result": "✅ Passed (150 concurrent connections handled)"
      }
    ],
    "customer_reports": {
      "support_tickets": "0 new tickets in last 30 minutes",
      "social_media": "No complaints on Twitter/Reddit",
      "status_page": "Updated to 'All Systems Operational'"
    },
    "recovery_time": {
      "incident_start": "2025-10-11T14:32:00Z",
      "incident_resolved": "2025-10-11T14:50:00Z",
      "total_duration": "18 minutes",
      "mttr_target": "30 minutes",
      "status": "✅ Within SLA"
    }
  },
  "prevention_measures": {
    "detection_improvements": [
      {
        "measure": "Add alert: Database connection pool >80% for 2 minutes",
        "rationale": "Current alert at 95% is too late, need earlier warning",
        "implementation": "Grafana alert rule",
        "owner": "SRE team",
        "deadline": "2025-10-12"
      },
      {
        "measure": "Add dashboard: Connection pool utilization by service",
        "rationale": "Visibility into which service is consuming connections",
        "implementation": "Grafana dashboard",
        "owner": "SRE team",
        "deadline": "2025-10-13"
      }
    ],
    "prevention_improvements": [
      {
        "measure": "Add pre-deployment check: Error rate must remain <1% for 5 minutes post-deploy",
        "rationale": "Automatic rollback on elevated error rate",
        "implementation": "Argo Rollouts progressive delivery",
        "owner": "DevOps team",
        "deadline": "2025-10-20"
      },
      {
        "measure": "Add SonarQube rule: Detect unclosed resources (connections, files, streams)",
        "rationale": "Catch resource leaks in code review",
        "implementation": "SonarQube custom rule",
        "owner": "Platform Engineering team",
        "deadline": "2025-10-18"
      },
      {
        "measure": "Increase staging database connection pool to match production",
        "rationale": "Staging should mimic production to catch capacity issues",
        "implementation": "Terraform config update",
        "owner": "Infrastructure team",
        "deadline": "2025-10-14"
      }
    ],
    "testing_improvements": [
      {
        "measure": "Add unit test template for error path testing",
        "rationale": "Ensure all new features test both happy path and error path",
        "implementation": "PR template + CI enforcement",
        "owner": "Engineering leads",
        "deadline": "2025-10-15"
      },
      {
        "measure": "Add load test: Simulate connection pool exhaustion",
        "rationale": "Catch resource leaks before production deployment",
        "implementation": "K6 load test script in CI/CD",
        "owner": "QA team",
        "deadline": "2025-10-25"
      }
    ]
  },
  "communication_log": [
    {
      "timestamp": "2025-10-11T14:35:00Z",
      "channel": "Status page",
      "message": "Investigating elevated error rates. Updates every 15 minutes.",
      "audience": "Customers"
    },
    {
      "timestamp": "2025-10-11T14:45:00Z",
      "channel": "Slack #incidents",
      "message": "Rollback complete, error rate down to 2%. Monitoring recovery.",
      "audience": "Internal engineering"
    },
    {
      "timestamp": "2025-10-11T14:50:00Z",
      "channel": "Status page",
      "message": "Incident resolved. All systems operational. Post-mortem in 48 hours.",
      "audience": "Customers"
    },
    {
      "timestamp": "2025-10-11T15:00:00Z",
      "channel": "Email",
      "message": "Executive summary sent to CTO and VP Engineering",
      "audience": "Leadership"
    }
  ]
}

QUALITY CRITERIA:
✅ Immediate actions executed with timestamps and results
✅ Root cause fix includes code diff and testing validation
✅ Recovery validated across multiple dimensions (metrics, tests, customer reports)
✅ Prevention measures categorized (detection, prevention, testing)
✅ Communication log chronological with all stakeholder updates
```

**Expected Output Size**: 250-300 lines JSON

---

### Subtask 4: Blameless Post-Mortem
**Agent**: SRE Infrastructure Reliability Agent
**Goal**: Document lessons learned, action items, and process improvements
**Input Variables**: `subtask_1_output`, `subtask_2_output`, `subtask_3_output`, `incident_id`
**Output Variables**: `post_mortem_document`, `action_items`, `lessons_learned`, `process_improvements`

**Prompt**:
```
You are the SRE agent writing a blameless post-mortem following Google SRE practices.

CONTEXT:
- Incident: {{incident_id}} ({{subtask_1_output.severity_classification.severity}})
- Root Cause: {{subtask_2_output.root_cause_analysis.primary_root_cause}}
- Remediation: {{subtask_3_output.remediation_plan}}
- Recovery Time: {{subtask_3_output.recovery_validation.recovery_time}}
- Prevention Measures: {{subtask_3_output.prevention_measures}}

TASK:
Write comprehensive blameless post-mortem following this structure:

1. **Executive Summary** (3-4 sentences)
   - What happened?
   - What was the impact?
   - What was the root cause?
   - What are we doing to prevent recurrence?

2. **Timeline** (Chronological event log)
   - All significant events from detection to resolution
   - Format: `HH:MM - Event description`
   - Include both automated and human actions

3. **Root Cause Analysis** (5-Whys + evidence)
   - Primary root cause with full explanation
   - Contributing factors
   - Why existing safeguards didn't prevent this

4. **Impact Assessment**
   - Customer impact (users affected, duration)
   - Business impact (revenue loss, SLA breach)
   - Internal impact (engineering time, opportunity cost)

5. **What Went Well** (Positive outcomes)
   - What worked as expected?
   - What helped us resolve quickly?
   - What demonstrated system resilience?

6. **What Went Wrong** (Areas for improvement)
   - What failed or didn't exist?
   - What slowed down resolution?
   - What amplified the impact?

7. **Action Items** (Concrete next steps with owners)
   - Detection improvements
   - Prevention improvements
   - Process improvements
   - Each item has: description, owner, deadline, priority

8. **Lessons Learned** (Systemic insights)
   - What did we learn about our systems?
   - What did we learn about our processes?
   - What did we learn about our team?

OUTPUT FORMAT (Markdown):
```markdown
# Post-Mortem: {{incident_id}}

**Date**: 2025-10-11
**Authors**: SRE Team (Mike Rodriguez, Sarah Chen)
**Status**: Draft → Review → Final
**Severity**: {{severity}}
**Duration**: {{duration}} minutes

---

## Executive Summary

On October 11, 2025 at 14:32 UTC, our production API experienced elevated error rates (15%) and latency (P95: 8.5s) for 18 minutes, affecting 100% of users. The root cause was a connection leak in a new feature deployed in web-app v2.3.1, which exhausted the database connection pool. We resolved the incident by rolling back the deployment and increasing connection pool capacity. Estimated customer impact: $1.5K revenue loss and 200 support tickets. We are implementing automated rollback on error rate spikes and improving code review coverage for error paths to prevent recurrence.

---

## Timeline (All times UTC)

**14:30** - Deployment: web-app v2.3.1 rolled out to production (3 pods)
**14:32** - 🔴 Alert: Database connections at 95% (Grafana)
**14:33** - 🔴 Alert: P95 latency >5s (Prometheus)
**14:35** - 🔴 Alert: Error rate >5% (CloudWatch)
**14:36** - Incident declared SEV-1, war room established
**14:38** - Initial investigation: Correlation identified between deployment and incident
**14:40** - **Action**: Rollback deployment to v2.3.0 initiated
**14:43** - Rollback complete, error rate dropped to 2%
**14:43** - **Action**: Increased database connection pool from 100 to 200
**14:45** - **Action**: Scaled web-app from 3 to 6 replicas
**14:47** - Metrics returning to baseline, recovery validated
**14:50** - 🟢 Incident resolved, all metrics healthy
**14:55** - Post-incident review scheduled for 2025-10-13

**Total Duration**: 18 minutes (MTTR target: 30 minutes ✅)

---

## Root Cause Analysis

### Primary Root Cause
Connection leak in `UserService.getUserPreferences()` method introduced in web-app v2.3.1. The error handling path did not close database connections in the `catch` block, causing connections to accumulate until the pool was exhausted.

### 5-Whys Drill-Down
1. **Why did we get 500 errors?** → Database connection pool exhausted (98/100)
2. **Why was the pool exhausted?** → Web app leaked connections
3. **Why did it leak connections?** → New feature (v2.3.1) didn't close connections in error path
4. **Why did error path miss cleanup?** → Code review didn't catch missing `finally` block
5. **Why did code review miss it?** → No automated check for resource leaks, manual review focused on happy path only

**Root Cause Category**: Software Bug - Resource Leak

### Contributing Factors
1. **Insufficient connection pool capacity**: Production pool (100) was undersized for normal traffic (150+ needed)
2. **No automated rollback**: Deployment succeeded despite immediate 15% error rate
3. **Staging environment mismatch**: Staging pool (50) smaller than production (100), issue not caught in testing

---

## Impact Assessment

### Customer Impact
- **Users Affected**: 100% (all API users)
- **Duration**: 18 minutes
- **Severity**: Complete API outage, unable to access application
- **Support Tickets**: 200 tickets received during incident
- **Estimated Revenue Loss**: $1.5K (based on $5K/hour revenue)

### Business Impact
- **SLA Breach**: 99.9% uptime SLA allows 43 minutes/month downtime. This incident consumed 42% of monthly budget.
- **Reputation**: Minor - quick resolution and transparent communication minimized impact
- **Opportunity Cost**: 4 engineers × 1 hour = 4 engineering hours diverted from roadmap work

### Technical Impact
- **Services Affected**: web-app, api-gateway, postgres-db (3 services)
- **Data Loss**: None
- **Security Impact**: None

---

## What Went Well

✅ **Fast detection**: Incident detected within 2 minutes of deployment (automated monitoring)
✅ **Clear incident command**: War room established immediately, roles assigned
✅ **Rapid correlation**: Deployment identified as likely cause within 6 minutes
✅ **Effective rollback**: Rollback completed in 3 minutes, error rate dropped immediately
✅ **Good communication**: Status page updated every 15 minutes, customers informed
✅ **Within SLA**: Resolved in 18 minutes (target: 30 minutes)

---

## What Went Wrong

❌ **Code review missed bug**: Manual code review didn't catch missing connection cleanup
❌ **No automated resource leak detection**: No tooling to detect unclosed resources
❌ **Insufficient test coverage**: Error path had 0% unit test coverage
❌ **Staging environment mismatch**: Staging didn't match production capacity, issue not caught
❌ **No automated rollback**: Deployment succeeded despite immediate error rate spike
❌ **Connection pool too small**: Production pool undersized for normal traffic

---

## Action Items

### High Priority (Complete within 1 week)

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Deploy hotfix v2.3.2 with connection cleanup | Dev Team | 2025-10-12 | In Progress |
| Add alert: DB connection pool >80% for 2 min | SRE Team | 2025-10-12 | Not Started |
| Increase staging DB pool to match production | Infra Team | 2025-10-14 | Not Started |

### Medium Priority (Complete within 2 weeks)

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Add SonarQube rule to detect unclosed resources | Platform Team | 2025-10-18 | Not Started |
| Implement automated rollback on error rate >5% | DevOps Team | 2025-10-20 | Not Started |
| Add PR template requiring error path testing | Eng Leads | 2025-10-15 | Not Started |

### Low Priority (Complete within 1 month)

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Add load test simulating connection pool exhaustion | QA Team | 2025-10-25 | Not Started |
| Review all services for similar connection leak patterns | SRE Team | 2025-11-01 | Not Started |

---

## Lessons Learned

### System Lessons
1. **Database is single point of failure**: Connection pool exhaustion brought down entire API. Need circuit breakers to fail gracefully.
2. **Staging ≠ Production**: Environment differences masked production issues. Staging must match production capacity.
3. **Monitoring gaps exist**: We had alerts for high error rates but not for resource exhaustion trends.

### Process Lessons
1. **Code review is insufficient alone**: Human review misses edge cases. Need automated static analysis.
2. **Test coverage metrics are misleading**: 80% overall coverage hid 0% coverage on critical error paths.
3. **Deployment velocity vs. safety trade-off**: Fast deployments are good, but need automated safety checks (progressive delivery).

### Team Lessons
1. **Incident response was effective**: Clear roles, fast correlation, decisive action. Team performed well under pressure.
2. **Blameless culture works**: Focus on process improvements, not individual blame, led to candid discussion.
3. **Documentation matters**: Runbooks and playbooks enabled fast resolution by on-call engineer.

---

## Appendix

### Code Diff (Root Cause)
```java
// BEFORE (v2.3.1 - buggy)
catch (SQLException e) {
    logger.error("Database error", e);
    return null; // ← Missing connection cleanup
}

// AFTER (v2.3.2 - fixed)
catch (SQLException e) {
    logger.error("Database error", e);
    return null;
} finally {
    if (conn != null) conn.close(); // ← Proper cleanup
}
```

### Related Incidents
- **INC-2024-0892** (2024-08-15): Similar connection leak in AuthService (resolved)
- **INC-2024-1045** (2024-09-22): Database connection pool exhaustion due to traffic spike (unrelated)

### References
- [Google SRE Book: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)
- [Azure Database Connection Best Practices](https://learn.microsoft.com/azure/database-connection-pooling)
- [OWASP: Improper Resource Shutdown](https://owasp.org/www-community/vulnerabilities/Improper_Resource_Shutdown)

---

**Post-Mortem Review Meeting**: 2025-10-13 at 10:00 UTC
**Attendees**: Engineering, SRE, Product, Support
**Status**: Draft (awaiting review)
```

QUALITY CRITERIA:
✅ Executive summary concise (3-4 sentences)
✅ Timeline chronological with exact timestamps
✅ Root cause explained with 5-Whys methodology
✅ Impact quantified (users, revenue, time)
✅ Action items have owners, deadlines, and priorities
✅ Blameless tone (focus on systems/processes, not individuals)
```

**Expected Output Size**: 400-500 lines Markdown

---

## Final Output Aggregation

After all subtasks complete, aggregate into comprehensive incident report:

```json
{
  "incident_summary": {
    "incident_id": "{{incident_id}}",
    "severity": "{{subtask_1_output.severity_classification.severity}}",
    "duration": "18 minutes",
    "root_cause": "{{subtask_2_output.root_cause_analysis.primary_root_cause}}",
    "customer_impact": "100% of users affected for 18 minutes",
    "resolution": "Rollback deployment + increase connection pool capacity"
  },
  "detection_and_triage": "{{subtask_1_output}}",
  "root_cause_diagnosis": "{{subtask_2_output}}",
  "remediation_and_recovery": "{{subtask_3_output}}",
  "post_mortem": "{{subtask_4_output}}"
}
```

## Context Enrichment Flow

**Subtask 1** → **Subtask 2**:
- Telemetry snapshot → Root cause diagnosis baseline
- Immediate actions → Consider impact on diagnosis

**Subtask 2** → **Subtask 3**:
- Root cause → Permanent fix specification
- Contributing factors → Additional prevention measures

**Subtask 3** → **Subtask 4**:
- Remediation timeline → Post-mortem timeline
- Recovery validation → Impact assessment
- Prevention measures → Action items

## Success Metrics

**Baseline (Before Prompt Chain)**:
- Mean Time to Resolution (MTTR): 45 minutes
- Root cause identification: 55% accuracy
- Recurrence rate: 15% of incidents repeat within 6 months

**Target (With Prompt Chain)**:
- MTTR: 25 minutes (+45% improvement)
- Root cause identification: 90% accuracy (+35 percentage points)
- Recurrence rate: 5% (+67% reduction)

## Usage Example

```bash
python claude/tools/orchestration/prompt_chain_orchestrator.py \
  --chain-id incident_detection_diagnosis_remediation_chain \
  --workflow-file claude/workflows/prompt_chains/incident_detection_diagnosis_remediation_chain.md \
  --input '{
    "incident_id": "INC-2025-1234",
    "reported_by": "Automated monitoring",
    "initial_symptoms": "API returning 500 errors at 15% rate",
    "affected_services": ["web-app", "api-gateway", "postgres-db"],
    "start_time": "2025-10-11T14:32:00Z",
    "customer_impact": "Critical",
    "monitoring_alerts": ["Database connections >95%", "P95 latency >5s", "Error rate >5%"],
    "environment": "Production",
    "recent_changes": {
      "deployments": ["web-app v2.3.1 deployed 1 hour ago"],
      "infrastructure": ["No recent changes"],
      "configuration": ["Database connection pool increased to 100"]
    }
  }'
```

## Notes

- **Subtask 1** provides rapid triage and stabilization
- **Subtask 2** performs systematic root cause analysis using 5-Whys
- **Subtask 3** executes remediation with validation
- **Subtask 4** captures lessons learned and action items
- This chain implements Google SRE best practices for incident management
- Blameless post-mortem culture is critical for organizational learning
