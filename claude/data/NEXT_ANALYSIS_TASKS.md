# Next Analysis Tasks - ServiceDesk Data

**Date**: 2025-10-19
**Source**: User request for additional analysis
**Status**: Pending execution

---

## Analysis Tasks Requested

### 1. Root Cause Accuracy Validation
**Task**: Review the root cause listed in TKT-Root Cause Category against the actual resolution and report on if the root cause seems accurate to you?

**Approach**:
- Sample tickets from each root cause category
- Read ticket description + resolution text + root cause classification
- Validate if root cause matches actual problem solved
- Calculate accuracy rate per category
- Identify misclassified categories

**Expected Output**:
- Root cause accuracy report (% accurate per category)
- Misclassification patterns
- Recommendations for improved categorization

---

### 2. Ticket Reassignment Rate Analysis
**Task**: Review how many times a ticket is re-handled and calculate the FCR rate

**Approach**:
- Count unique agents per ticket (from timesheets or comments)
- Calculate reassignment distribution (1 agent, 2 agents, 3+ agents)
- Compare FCR proxy (≤1 comment) vs reassignment-based FCR
- Identify teams with highest reassignment rates

**Expected Output**:
- Reassignment rate: % tickets handled by single agent
- FCR comparison: Comment-based (70.98%) vs Assignment-based
- Team-level reassignment patterns

**SQL Query**:
```sql
WITH ticket_agent_counts AS (
    SELECT
        ticket_id,
        COUNT(DISTINCT user_name) as agent_count
    FROM timesheets
    GROUP BY ticket_id
)
SELECT
    agent_count,
    COUNT(*) as ticket_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM ticket_agent_counts
GROUP BY agent_count
ORDER BY agent_count;
```

---

### 3. Team-Level FCR Calculation
**Task**: Calculate the FCR rate for each team member

**Approach**:
- Join tickets + customer_facing_comments + timesheets
- Calculate FCR per agent (tickets with ≤1 customer comment)
- Rank agents by FCR rate
- Identify top performers and training opportunities

**Expected Output**:
- Agent-level FCR leaderboard
- Team average FCR rates
- Low performers requiring coaching

**SQL Query**:
```sql
WITH customer_facing_comments AS (
    SELECT ticket_id, COUNT(*) as customer_comment_count
    FROM comments WHERE visible_to_customer = 'Yes' GROUP BY ticket_id
),
agent_fcr AS (
    SELECT
        ts.user_name,
        ts.team,
        COUNT(DISTINCT ts.ticket_id) as total_tickets,
        SUM(CASE WHEN COALESCE(cfc.customer_comment_count, 0) <= 1 THEN 1 ELSE 0 END) as fcr_tickets,
        ROUND(100.0 * SUM(CASE WHEN COALESCE(cfc.customer_comment_count, 0) <= 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT ts.ticket_id), 2) as fcr_rate
    FROM timesheets ts
    JOIN tickets t ON ts.ticket_id = t."TKT-Ticket ID"
    LEFT JOIN customer_facing_comments cfc ON ts.ticket_id = cfc.ticket_id
    WHERE t."TKT-Status" IN ('Closed', 'Resolved')
    GROUP BY ts.user_name, ts.team
    HAVING COUNT(DISTINCT ts.ticket_id) >= 10
)
SELECT * FROM agent_fcr ORDER BY fcr_rate DESC;
```

---

### 4. Team Workload Type Analysis
**Task**: Review the teams and analyse the types of tickets that each team is taking

**Approach**:
- Group tickets by team + category/type
- Calculate distribution per team
- Identify specializations vs generalists
- Compare workload complexity (resolution time per category)

**Expected Output**:
- Team workload matrix (Team × Category heatmap)
- Specialization analysis
- Complexity scoring per team

**SQL Query**:
```sql
SELECT
    t."TKT-Team" as team,
    t."TKT-Category" as category,
    COUNT(*) as ticket_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY t."TKT-Team"), 2) as pct_of_team_workload,
    ROUND(AVG(CAST((JULIANDAY(t."TKT-Actual Resolution Date") - JULIANDAY(t."TKT-Created Time")) AS REAL)), 2) as avg_resolution_days
FROM tickets t
WHERE t."TKT-Status" IN ('Closed', 'Resolved')
    AND t."TKT-Team" IS NOT NULL
GROUP BY t."TKT-Team", t."TKT-Category"
HAVING COUNT(*) >= 5
ORDER BY team, ticket_count DESC;
```

---

### 5. Incident Handling Efficiency Analysis
**Task**: Calculate the number of times each incident is handled and list the team from best to worst

**Approach**:
- Count handling events per incident (timesheet entries, reassignments, comments)
- Calculate average handling count per team
- Rank teams by efficiency (lower handling count = better)
- Identify teams with excessive handoffs

**Expected Output**:
- Team efficiency ranking (lowest avg handling count = best)
- Handling count distribution per team
- Root cause analysis for high-handling teams

**SQL Query**:
```sql
WITH incident_handling AS (
    SELECT
        t."TKT-Ticket ID" as ticket_id,
        t."TKT-Team" as team,
        COUNT(DISTINCT ts.user_name) as unique_agents,
        COUNT(DISTINCT c.comment_id) as comment_count,
        (COUNT(DISTINCT ts.user_name) + COUNT(DISTINCT c.comment_id)) as total_handling_events
    FROM tickets t
    LEFT JOIN timesheets ts ON t."TKT-Ticket ID" = ts.ticket_id
    LEFT JOIN comments c ON t."TKT-Ticket ID" = c.ticket_id
    WHERE t."TKT-Type" = 'Incident'
        AND t."TKT-Status" IN ('Closed', 'Resolved')
    GROUP BY t."TKT-Ticket ID", t."TKT-Team"
)
SELECT
    team,
    COUNT(*) as incident_count,
    ROUND(AVG(unique_agents), 2) as avg_agents_per_incident,
    ROUND(AVG(comment_count), 2) as avg_comments_per_incident,
    ROUND(AVG(total_handling_events), 2) as avg_handling_events,
    MIN(total_handling_events) as min_handling,
    MAX(total_handling_events) as max_handling
FROM incident_handling
WHERE team IS NOT NULL
GROUP BY team
HAVING COUNT(*) >= 10
ORDER BY avg_handling_events ASC;
```

---

## Execution Plan

1. **Root Cause Validation** (30 min)
   - Sample 50-100 tickets per major root cause category
   - Manual review of ticket text vs root cause classification
   - Accuracy scoring + misclassification report

2. **Reassignment Rate Analysis** (15 min)
   - SQL query execution
   - Distribution analysis
   - Team-level breakdown

3. **Team-Level FCR** (20 min)
   - SQL query execution
   - Agent leaderboard creation
   - Coaching opportunity identification

4. **Team Workload Type Analysis** (25 min)
   - SQL query execution
   - Heatmap visualization data prep
   - Specialization insights

5. **Incident Handling Efficiency** (20 min)
   - SQL query execution
   - Team ranking
   - Root cause analysis for inefficient teams

**Total Estimated Time**: ~2 hours

---

## Output Format

For each analysis:
- Executive summary (key findings)
- Detailed data tables
- Visualizations (where applicable)
- Actionable recommendations
- Integration with existing metrics analysis

---

**Next Steps**: Execute analyses in order, document findings, update INDUSTRY_STANDARD_METRICS_ANALYSIS.md with new insights.
