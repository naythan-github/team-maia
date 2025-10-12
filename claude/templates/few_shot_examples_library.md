# Few-Shot Example Library by Pattern Type

**Created**: 2025-10-12
**Purpose**: Production-ready few-shot examples for training Maia's 46-agent ecosystem
**Source**: Google Gemini + OpenAI GPT-4.1 best practices
**Usage**: Include 2-3 relevant examples in each agent's prompt template

---

## Pattern Type 1: Tool-Calling Examples (5 examples)

### Example 1.1: DNS Specialist - SPF Record Check

```
USER: "Check if example.com has SPF record configured"

AGENT REASONING:
- Need to query DNS TXT records
- SPF records are TXT records starting with "v=spf1"
- Use dns_query tool with record_type="TXT"

ACTION:
result = self.call_tool(
    tool_name="dns_query",
    parameters={
        "domain": "example.com",
        "record_type": "TXT"
    }
)

# Filter for SPF record
spf_records = [r for r in result.records if r.startswith("v=spf1")]

RESULT:
Yes, example.com has SPF record configured:
v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all

Analysis:
- Allows email from Microsoft 365 (spf.protection.outlook.com)
- Allows email from SendGrid (sendgrid.net)
- Rejects all other senders (-all is strict policy)
- 2 DNS lookups (within 10 lookup limit ✅)
```

### Example 1.2: SRE Principal - Check Service Health

```
USER: "Is the payment-api service healthy right now?"

AGENT REASONING:
- Need real-time metrics to assess health
- Check: uptime, error rate, latency, resource utilization
- Use prometheus_query tool for current state

ACTION:
# Check if service is up
up_result = self.call_tool(
    tool_name="prometheus_query",
    parameters={
        "query": 'up{service="payment-api"}',
        "time": "now"
    }
)

# Check error rate (last 5 minutes)
error_result = self.call_tool(
    tool_name="prometheus_query",
    parameters={
        "query": 'rate(http_requests_total{service="payment-api",code=~"5.."}[5m])',
        "time": "now"
    }
)

# Check P99 latency
latency_result = self.call_tool(
    tool_name="prometheus_query",
    parameters={
        "query": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="payment-api"}[5m]))',
        "time": "now"
    }
)

RESULT:
✅ payment-api is HEALTHY

Status:
- Uptime: 100% (all instances running)
- Error Rate: 0.02% (well below 0.5% threshold)
- P99 Latency: 85ms (below 200ms SLO)
- Resource Usage: CPU 45%, Memory 62% (normal)

All metrics within acceptable ranges.
```

### Example 1.3: Azure Solutions Architect - Cost Analysis

```
USER: "What's our monthly Azure spend for production resources?"

AGENT REASONING:
- Need to query Azure Cost Management API
- Filter for production environment
- Group by resource type for breakdown
- Use azure_cost_analysis tool

ACTION:
result = self.call_tool(
    tool_name="azure_cost_analysis",
    parameters={
        "scope": "subscription/12345-67890",
        "timeframe": "MonthToDate",
        "granularity": "None",
        "filter": {
            "tags": {"Environment": "Production"}
        },
        "grouping": [{"name": "ResourceType", "type": "Dimension"}]
    }
)

RESULT:
Production Azure Spend (Month-to-Date): $48,350

Breakdown by Resource Type:
- Virtual Machines: $22,100 (46%)
- Azure SQL Database: $12,800 (26%)
- Storage Accounts: $6,200 (13%)
- Application Gateway: $4,150 (9%)
- Azure Functions: $1,800 (4%)
- Other: $1,300 (3%)

Trend: -8% vs last month (cost optimization working)

Top cost drivers:
1. VM instance type: Standard_D8s_v3 (10 instances, $18,500/month)
2. SQL Database: Premium tier (5 databases, $12,800/month)
```

### Example 1.4: Service Desk Manager - Ticket Priority Analysis

```
USER: "Analyze ticket TICKET-5432 and assign priority"

AGENT REASONING:
- Need to retrieve ticket details
- Assess impact (how many users affected)
- Assess urgency (can users work?)
- Use get_ticket tool then apply priority matrix

ACTION:
ticket = self.call_tool(
    tool_name="get_ticket",
    parameters={
        "ticket_id": "TICKET-5432"
    }
)

# Priority Matrix Assessment
impact = self._assess_impact(ticket.affected_users, ticket.affected_systems)
urgency = self._assess_urgency(ticket.description, ticket.workaround_available)

RESULT:
TICKET-5432 Priority: P1 (Critical)

Ticket Details:
- Issue: VPN connection failing for all remote users
- Affected Users: ~400 (all remote workers)
- Affected Systems: Cisco AnyConnect VPN gateway
- Workaround: None available
- Business Impact: Remote work completely blocked

Priority Justification:
- Impact: HIGH (400 users, business-critical system)
- Urgency: HIGH (no workaround, users cannot work)
- Matrix Result: HIGH Impact + HIGH Urgency = P1 Critical

Recommended Actions:
1. Escalate to network team immediately
2. Set up war room
3. Hourly updates to executive team
4. SLA: Resolution within 4 hours
```

### Example 1.5: DevOps Engineer - Deployment Status Check

```
USER: "Is the latest deployment of web-app to staging successful?"

AGENT REASONING:
- Need to check Kubernetes deployment status
- Verify all pods are ready
- Check for any deployment errors
- Use kubectl_get tool

ACTION:
deployment = self.call_tool(
    tool_name="kubectl_get",
    parameters={
        "resource": "deployment",
        "name": "web-app",
        "namespace": "staging",
        "output": "json"
    }
)

pods = self.call_tool(
    tool_name="kubectl_get",
    parameters={
        "resource": "pods",
        "namespace": "staging",
        "selector": "app=web-app",
        "output": "json"
    }
)

RESULT:
✅ Deployment SUCCESSFUL

Deployment: web-app (staging)
- Image: web-app:v2.3.1
- Replicas: 3/3 ready
- Strategy: RollingUpdate
- Age: 5 minutes

Pod Status:
- web-app-7d4f8c9b-xk2p4: Running (ready 1/1)
- web-app-7d4f8c9b-mnq8r: Running (ready 1/1)
- web-app-7d4f8c9b-zt5lw: Running (ready 1/1)

Health Checks:
- Liveness: Passing (all pods)
- Readiness: Passing (all pods)
- Service endpoints: 3/3 active

Deployment completed successfully in 3m42s.
```

---

## Pattern Type 2: ReACT (Reasoning + Acting) Examples (5 examples)

### Example 2.1: SRE Principal - Latency Spike Investigation

```
USER: "API latency spike from 100ms to 1500ms - need immediate diagnosis"

AGENT REASONING (ReACT Loop):

THOUGHT: Latency spike could be: code change, infrastructure issue, dependency problem, or resource exhaustion. Need systematic investigation.

PLAN:
1. Check recent changes (deployments, config, infrastructure)
2. Analyze resource utilization (CPU, memory, connections)
3. Profile slow requests (identify bottleneck)
4. Implement fix and validate

ACTION 1: Query recent deployments
```bash
kubectl get deployments --sort-by='.metadata.creationTimestamp' | head -5
```

OBSERVATION:
- "api-service" deployed 25 minutes ago (v2.1.5)
- Timing matches latency spike exactly
- Previous version (v2.1.4) was stable

REFLECTION: New deployment is highly suspicious. Should check what changed in v2.1.5.

ACTION 2: Review deployment diff
```bash
git diff v2.1.4..v2.1.5 -- api-service/
```

OBSERVATION:
```diff
+ # New database query added
+ def get_user_data(user_id):
+     user = User.query.get(user_id)
+     orders = Order.query.filter_by(user_id=user_id).all()  # New query
+     return {user: user, orders: orders}
```

REFLECTION: Added separate query for orders - this could be N+1 query issue if called in a loop.

ACTION 3: Check database connection count
```prometheus
db_connections{service="api-service"}
```

OBSERVATION: Connection count jumped from 50 to 400 (8x increase)

REFLECTION: Confirmed - N+1 query pattern causing connection pool exhaustion. Need immediate rollback.

ACTION 4: Rollback deployment
```bash
kubectl rollout undo deployment/api-service
```

OBSERVATION:
- Rollback completed in 90 seconds
- Latency drops to 100ms within 2 minutes
- Connection count back to 50

RESULT:
Issue resolved via rollback. Root cause: N+1 query bug in v2.1.5.

Permanent fix:
```python
# Use eager loading to prevent N+1
user = User.query.options(
    joinedload(User.orders)
).get(user_id)
```

Timeline:
- T+0: Latency spike detected
- T+5min: Root cause identified (N+1 query)
- T+7min: Rollback initiated
- T+9min: Service recovered

Prevention: Added database query count test to CI/CD pipeline.
```

### Example 2.2: DNS Specialist - Email Delivery Troubleshooting

```
USER: "Emails from mydomain.com are being rejected by Gmail - fix this urgently"

AGENT REASONING (ReACT Loop):

THOUGHT: Gmail email rejection could be: SPF failure, DKIM failure, DMARC failure, IP reputation, or content issues. Need to check email authentication first.

PLAN:
1. Check SPF record configuration
2. Verify DKIM setup
3. Check DMARC policy
4. Test email authentication
5. Verify DNS propagation

ACTION 1: Query SPF record
```bash
dig +short TXT mydomain.com | grep spf1
```

OBSERVATION:
```
"v=spf1 include:spf.protection.outlook.com ~all"
```

REFLECTION: SPF exists but uses soft fail (~all). Gmail might reject with softfail. Also, only one include - need to check if SendGrid is authorized.

ACTION 2: Check actual sending IPs
```bash
# Query MTA logs for recent sends
grep "from mydomain.com" /var/log/mail.log | tail -20
```

OBSERVATION:
```
Sent from IP: 192.0.2.50 (sendgrid.net)
SPF result: softfail (not in SPF record)
```

REFLECTION: Emails are sent via SendGrid but SendGrid is NOT in SPF record! This is the root cause.

ACTION 3: Update SPF record
```bash
# Current: v=spf1 include:spf.protection.outlook.com ~all
# Fixed:  v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all
```

OBSERVATION:
- SPF record updated in DNS
- Changed ~all to -all for strict policy
- Added SendGrid authorization

REFLECTION: SPF updated, but need to verify DKIM and DMARC too.

ACTION 4: Check DKIM configuration
```bash
dig +short TXT sendgrid._domainkey.mydomain.com
```

OBSERVATION:
```
NXDOMAIN (record does not exist)
```

REFLECTION: DKIM record missing! This is second authentication failure.

ACTION 5: Create DKIM record
```bash
# Get DKIM key from SendGrid
sendgrid_dkim_key="k=rsa; p=MIGfMA0GCSq..."

# Create DKIM DNS record
# sendgrid._domainkey.mydomain.com TXT "k=rsa; p=MIGfMA0GCSq..."
```

OBSERVATION:
- DKIM record created
- Waiting for DNS propagation (2-5 minutes)

ACTION 6: Test email authentication
```bash
# Send test email
echo "Test" | mail -s "Auth Test" check-auth@mail-tester.com

# Check results
curl mail-tester.com/test-12345.json
```

OBSERVATION:
```json
{
  "spf": "pass",
  "dkim": "pass",
  "dmarc": "pass",
  "score": "10/10"
}
```

RESULT:
Email authentication FIXED ✅

Root Causes Identified & Resolved:
1. SPF record missing SendGrid (❌ → ✅)
2. DKIM record not configured (❌ → ✅)
3. SPF policy was softfail, now hardfail (~all → -all)

Changes Made:
- SPF: v=spf1 include:spf.protection.outlook.com include:sendgrid.net -all
- DKIM: Created sendgrid._domainkey.mydomain.com with public key
- DMARC: Already configured (v=DMARC1; p=quarantine)

Validation:
- Authentication test: 10/10 score
- Gmail delivery: Now accepting emails
- Deliverability: Restored

Timeline:
- T+0: Issue reported
- T+3min: SPF issue identified
- T+5min: DKIM issue identified
- T+8min: Both fixed
- T+12min: Validated working
```

### Example 2.3: Security Analyst - Suspicious Activity Investigation

```
USER: "Alert: Unusual login pattern detected for user john.doe@company.com - investigate"

AGENT REASONING (ReACT Loop):

THOUGHT: Unusual login could indicate: compromised credentials, insider threat, or false positive. Need to gather evidence before escalating.

PLAN:
1. Review login history and pattern
2. Check login locations and devices
3. Analyze access patterns after login
4. Determine if account is compromised
5. Take appropriate action

ACTION 1: Query user login history (last 30 days)
```sql
SELECT timestamp, ip_address, user_agent, mfa_used, login_result
FROM auth_logs
WHERE user_email = 'john.doe@company.com'
  AND timestamp > NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC
LIMIT 100;
```

OBSERVATION:
```
Normal pattern (last 29 days):
- Login times: 8am-6pm EST (business hours)
- Locations: New York, NY (office IP: 203.0.113.50)
- Device: MacBook Pro, Chrome browser
- MFA: Always used

TODAY's logins:
- 2:30 AM EST from IP 198.51.100.75 (Moscow, Russia)
- Device: Windows 10, Firefox
- MFA: NOT used (bypassed somehow)
- Result: SUCCESS
```

REFLECTION: HIGHLY SUSPICIOUS - midnight login from Russia, different device, MFA bypassed. This is likely a compromised account.

ACTION 2: Check how MFA was bypassed
```sql
SELECT mfa_method, mfa_backup_used, session_token
FROM auth_logs
WHERE user_email = 'john.doe@company.com'
  AND timestamp = '2025-10-12 02:30:00'
```

OBSERVATION:
```
MFA bypassed using: backup codes
Backup code used: 7 of 10 codes already consumed
Session token: Valid for 30 days (long-lived token)
```

REFLECTION: Attacker used backup codes (likely stolen). Need to check what they accessed.

ACTION 3: Analyze activity after suspicious login
```sql
SELECT timestamp, action, resource, ip_address
FROM audit_logs
WHERE user_email = 'john.doe@company.com'
  AND timestamp > '2025-10-12 02:30:00'
ORDER BY timestamp ASC;
```

OBSERVATION:
```
02:31 - Accessed customer database
02:32 - Exported customer list (50,000 records)
02:33 - Accessed financial reports
02:34 - Downloaded Q3 financial data
02:35 - Attempted to access admin panel (BLOCKED - insufficient permissions)
```

REFLECTION: CONFIRMED BREACH - Data exfiltration in progress. Immediate action required.

ACTION 4: Contain the breach
```bash
# 1. Disable account immediately
disable_user --email john.doe@company.com --reason "Security breach"

# 2. Kill all active sessions
revoke_all_sessions --user john.doe@company.com

# 3. Block attacker IP
firewall_block --ip 198.51.100.75 --reason "Compromised account access"

# 4. Alert security team
send_alert --severity CRITICAL --message "Account compromise confirmed: john.doe@company.com. Data exfiltration detected."
```

OBSERVATION:
- Account disabled ✅
- All sessions terminated ✅
- Attacker IP blocked ✅
- Security team alerted ✅

ACTION 5: Assess damage
```bash
# Check what data was exported
SELECT file_name, row_count, download_timestamp
FROM export_logs
WHERE user_email = 'john.doe@company.com'
  AND download_timestamp > '2025-10-12 02:30:00';
```

OBSERVATION:
```
Exported files:
1. customer_list.csv - 50,000 customer records (PII)
2. q3_financial_report.pdf - Confidential financial data
```

RESULT:
SECURITY BREACH CONFIRMED & CONTAINED ✅

Incident Summary:
- Account: john.doe@company.com
- Compromise Method: Stolen backup codes
- Attack Origin: 198.51.100.75 (Moscow, Russia)
- Data Exfiltrated:
  - 50,000 customer records (PII) ⚠️
  - Q3 financial report (confidential) ⚠️

Containment Actions:
1. ✅ Account disabled
2. ✅ Sessions revoked
3. ✅ Attacker IP blocked
4. ✅ Security team alerted

Next Steps (URGENT):
1. Contact john.doe to verify account compromise
2. Reset credentials and regenerate MFA backup codes
3. Notify legal team (data breach notification may be required)
4. Notify affected customers (50,000 records)
5. Begin forensic analysis of exfiltrated data
6. Review: Why were backup codes not rate-limited?

Timeline:
- T+0: Alert triggered
- T+2min: Suspicious pattern confirmed
- T+5min: Breach confirmed
- T+7min: Account contained
- T+10min: Damage assessed
```

### Example 2.4: Cloud Architect - High Availability Design

```
USER: "Design a highly available architecture for our e-commerce platform that can handle Black Friday traffic"

AGENT REASONING (ReACT Loop):

THOUGHT: High availability for e-commerce requires: multi-region deployment, auto-scaling, database redundancy, and graceful degradation. Need to understand current architecture and traffic patterns first.

PLAN:
1. Analyze current architecture and bottlenecks
2. Determine Black Friday traffic requirements
3. Design multi-region HA architecture
4. Plan failover and disaster recovery
5. Calculate costs and provide recommendations

ACTION 1: Query current architecture
```bash
# Get current deployment topology
aws ec2 describe-instances --filters "Name=tag:Application,Values=ecommerce" --query 'Reservations[*].Instances[*].[InstanceType,AvailabilityZone,State.Name]'
```

OBSERVATION:
```
Current Architecture:
- Region: us-east-1 only (single region)
- AZs: us-east-1a only (single AZ)
- Web: 4x t3.large instances
- App: 4x t3.large instances
- DB: 1x db.r5.xlarge RDS (single instance, no read replicas)
- Cache: 1x cache.t3.medium ElastiCache (no cluster mode)
```

REFLECTION: CRITICAL GAPS - Single region, single AZ, single DB, no redundancy. This will fail under Black Friday load.

ACTION 2: Analyze Black Friday traffic expectations
```bash
# Get historical Black Friday data
SELECT date, max(requests_per_second), max(concurrent_users), max(db_connections)
FROM traffic_metrics
WHERE date BETWEEN '2024-11-24' AND '2024-11-27'
GROUP BY date;
```

OBSERVATION:
```
Black Friday 2024 Traffic:
- Normal traffic: 500 req/sec
- Black Friday peak: 15,000 req/sec (30x increase)
- Concurrent users: 50,000+
- Database connections: Maxed out at 100 (caused outage)
- Duration: 6-hour peak window
```

REFLECTION: 30x traffic spike, DB was bottleneck. Need massive scale-out capability and DB read replicas.

ACTION 3: Design HA architecture
```
PROPOSED ARCHITECTURE:

Multi-Region Setup:
┌─────────────────────────────────────────────────────────────┐
│ Global Layer                                                 │
│  - Route 53 with latency-based routing                      │
│  - CloudFront CDN (static assets)                           │
│  - WAF (DDoS protection)                                    │
└─────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
    ┌─────────▼────────┐      ┌────────▼─────────┐
    │ us-east-1 (Primary)│      │ us-west-2 (DR)   │
    │                    │      │                  │
    │ Multi-AZ:          │      │ Multi-AZ:        │
    │  - 3 AZs           │      │  - 3 AZs         │
    │  - ALB             │      │  - ALB           │
    │  - Auto Scaling    │      │  - Auto Scaling  │
    │    Min: 10         │      │    Min: 5        │
    │    Max: 200        │      │    Max: 100      │
    │                    │      │                  │
    │ Database:          │      │ Database:        │
    │  - RDS Multi-AZ    │      │  - Read Replica  │
    │  - 5 Read Replicas │      │  - Cross-region  │
    │                    │      │                  │
    │ Cache:             │      │ Cache:           │
    │  - ElastiCache     │      │  - ElastiCache   │
    │  - Cluster mode    │      │  - Cluster mode  │
    │  - 6 nodes         │      │  - 3 nodes       │
    └────────────────────┘      └──────────────────┘
```

OBSERVATION:
Designed architecture addresses all HA requirements:
- Multi-region (us-east-1 + us-west-2)
- Multi-AZ within each region
- Auto-scaling (10-200 instances)
- Database read replicas (5 in primary, 1 cross-region)
- Redis cluster (high availability caching)
- CDN for static assets (reduce origin load)
- WAF for DDoS protection

REFLECTION: Architecture looks good but need to validate it can handle 15,000 req/sec and estimate costs.

ACTION 4: Calculate capacity and costs
```python
# Capacity calculation
requests_per_second = 15000
avg_request_duration_ms = 50
concurrent_requests = (requests_per_second * avg_request_duration_ms) / 1000  # = 750

# Instance sizing
requests_per_instance = 100  # tested capacity
required_instances = concurrent_requests / requests_per_instance  # = 7.5 (round to 10)

# With auto-scaling: 10 min, 200 max (20x buffer)
# With multi-region: 10 primary + 5 DR = 15 instances baseline

# Cost estimation (monthly)
compute_cost = 15 * 730 * 0.0832  # t3.large $0.0832/hr = $912
db_cost = 1 * 730 * 0.48 + 5 * 730 * 0.24  # RDS primary + replicas = $1,226
cache_cost = 6 * 730 * 0.068  # ElastiCache = $298
data_transfer = 500  # Estimated cross-region transfer
total_monthly = $2,936 (baseline) + scale costs during peak
```

OBSERVATION:
- Baseline capacity: 15 instances = handles 1,500 req/sec
- Auto-scale capacity: 200 instances = handles 20,000 req/sec (33% buffer over 15K peak)
- Monthly cost: ~$3,000 baseline + $15,000 during Black Friday week
- Annual cost: ~$51,000 ($3K x 11 months + $15K Black Friday)

RESULT:
HIGH AVAILABILITY ARCHITECTURE COMPLETE ✅

Architecture Summary:
1. **Multi-Region**: us-east-1 (primary) + us-west-2 (DR)
2. **Multi-AZ**: 3 AZs in each region
3. **Auto-Scaling**: 10-200 instances (20x capacity buffer)
4. **Database**: Multi-AZ RDS + 5 read replicas + cross-region replica
5. **Caching**: Redis cluster (6 nodes primary, 3 nodes DR)
6. **CDN**: CloudFront for static assets (90% of traffic)
7. **DDoS Protection**: WAF + Shield

Capacity Validation:
- Peak load: 15,000 req/sec ✅
- Architecture capacity: 20,000 req/sec ✅
- Buffer: 33% over peak ✅

Availability Targets:
- RTO: 5 minutes (automated failover)
- RPO: 0 seconds (synchronous multi-AZ replication)
- Uptime SLA: 99.99% (4 nines)

Cost Analysis:
- Baseline: $3,000/month
- Black Friday week: $15,000
- Annual total: ~$51,000
- Cost per Black Friday transaction: $0.003 (excellent ROI)

Migration Plan:
1. Week 1-2: Set up multi-region infrastructure
2. Week 3: Database replication and testing
3. Week 4: Traffic splitting (10% to new architecture)
4. Week 5: Ramp to 50% traffic
5. Week 6: Full cutover + old architecture decommission
6. Week 7-8: Load testing and optimization
7. Week 9: Black Friday readiness validation

Recommendation: PROCEED with implementation (8-week timeline to Black Friday)
```

### Example 2.5: Technical Recruiter - Candidate Assessment

```
USER: "Review candidate Sarah Chen for Senior Backend Engineer role and provide hiring recommendation"

AGENT REASONING (ReACT Loop):

THOUGHT: Senior Backend Engineer requires: strong system design, scalability experience, coding skills, and cultural fit. Need to review resume, GitHub, and interview feedback systematically.

PLAN:
1. Review resume and experience
2. Analyze GitHub contributions
3. Review technical interview performance
4. Assess cultural fit
5. Compare to role requirements
6. Provide hire/no-hire recommendation

ACTION 1: Review resume
```yaml
Candidate: Sarah Chen
Current Role: Backend Engineer at TechCorp (3 years)
Previous: Software Engineer at StartupXYZ (2 years)
Education: BS Computer Science, Stanford University
Total Experience: 5 years

Technical Skills:
- Languages: Python, Go, Java
- Databases: PostgreSQL, MongoDB, Redis
- Infrastructure: AWS, Kubernetes, Docker
- Frameworks: FastAPI, Django, gRPC

Key Projects:
- Led migration from monolith to microservices (20 services)
- Built real-time data pipeline processing 1M events/sec
- Designed and implemented caching layer (10x performance improvement)
```

OBSERVATION:
- Experience level: 5 years (meets minimum for Senior)
- Tech stack alignment: Strong (Python/Go, AWS, K8s all match our needs)
- Project scale: Impressive (1M events/sec, microservices migration)
- Leadership: Yes (led migration project)

REFLECTION: Resume looks strong. Need to validate technical depth through GitHub and interview performance.

ACTION 2: Analyze GitHub profile
```bash
# Fetch GitHub stats
gh api users/sarahchen/repos --paginate | jq '
  {
    total_repos: length,
    languages: [.[].language] | unique,
    total_stars: [.[].stargazers_count] | add,
    contribution_count: [.[].size] | add
  }
'
```

OBSERVATION:
```json
{
  "total_repos": 42,
  "languages": ["Python", "Go", "JavaScript", "Rust"],
  "total_stars": 1247,
  "top_projects": [
    {
      "name": "distributed-cache",
      "stars": 823,
      "description": "High-performance distributed caching library in Go",
      "contributors": 15
    },
    {
      "name": "event-stream-processor",
      "stars": 312,
      "description": "Real-time event processing framework",
      "contributors": 8
    }
  ],
  "recent_activity": "Very active - 1,234 contributions last year"
}
```

REFLECTION: Excellent GitHub presence - 800+ stars on distributed systems project shows strong technical credibility. Active contributor. This is above average for senior level.

ACTION 3: Review technical interview feedback
```sql
SELECT interviewer, focus_area, rating, comments
FROM interview_feedback
WHERE candidate_id = 'sarah_chen_2025'
ORDER BY interview_date;
```

OBSERVATION:
```
Interview 1 - Coding (Interviewer: Mike Johnson)
Rating: Strong Hire (4/5)
Comments: "Solved both problems efficiently. Used proper data structures. Code was clean and well-tested. Great explanation of trade-offs."

Interview 2 - System Design (Interviewer: Emily Rodriguez)
Rating: Strong Hire (4/5)
Comments: "Designed a URL shortener with excellent scalability considerations. Discussed sharding, caching, rate limiting without prompting. Asked great clarifying questions."

Interview 3 - Architecture (Interviewer: David Kim)
Rating: Hire (3/5)
Comments: "Good understanding of microservices patterns. Could improve on distributed transactions and consistency models. Solid but not exceptional."

Interview 4 - Behavioral (Interviewer: Lisa Park)
Rating: Strong Hire (4/5)
Comments: "Great communication. Handled conflict scenario well. Shows leadership potential. Cultural fit looks good."
```

REFLECTION: Strong performance across the board. Slight weakness in distributed systems theory (consistency models) but practical experience is strong. Overall positive signal.

ACTION 4: Compare to role requirements
```yaml
Senior Backend Engineer Requirements:
1. 5+ years experience: ✅ (5 years)
2. System design expertise: ✅ (microservices, 1M events/sec)
3. Python or Go proficiency: ✅ (Both)
4. AWS/K8s experience: ✅ (Production experience)
5. Leadership/mentoring: ✅ (Led migration project)
6. Open source contributions: ✅ (823-star project)
7. Strong coding skills: ✅ (4/5 rating)
8. Cultural fit: ✅ (4/5 rating)

Gap Analysis:
- Minor: Distributed consistency models (theoretical knowledge)
- Can be addressed: On-the-job learning, we have internal training
```

OBSERVATION:
Meets ALL core requirements ✅
One minor gap in distributed systems theory
Gap is addressable through mentorship

REFLECTION: Strong hire signal. Minor theoretical gap is not a blocker at this level - practical experience is more important.

ACTION 5: Check compensation expectations
```bash
# Get candidate's compensation expectations
grep "expected_compensation" candidates/sarah_chen.json
```

OBSERVATION:
```json
{
  "current_compensation": "$145,000 (base) + $30,000 (equity)",
  "expected_compensation": "$175,000 - $190,000 (base) + equity",
  "location": "San Francisco, CA"
}
```

REFLECTION: Expectations ($175-190K) are within our budget range ($170-200K for Senior Backend Engineer in SF). Compensation is not a blocker.

RESULT:
HIRING RECOMMENDATION: STRONG HIRE ✅

Candidate Summary:
- Name: Sarah Chen
- Role: Senior Backend Engineer
- Experience: 5 years (TechCorp + StartupXYZ)
- Technical Rating: 4/5 (Strong)
- Cultural Fit: 4/5 (Strong)

Strengths:
1. Proven scalability experience (1M events/sec pipeline)
2. Strong open source contributions (823-star distributed cache project)
3. Microservices expertise (led 20-service migration)
4. Tech stack alignment (Python, Go, AWS, K8s)
5. Leadership experience (led projects, mentored junior engineers)
6. Excellent coding skills (4/5 interview rating)
7. Great communication and cultural fit

Areas for Growth:
1. Distributed systems theory (consistency models) - Minor gap
   - Mitigation: Internal training, pair with senior architect

Compensation:
- Candidate expectation: $175-190K base + equity
- Our budget: $170-200K base + equity
- Recommendation: Offer $180K base + standard equity package

Interview Performance:
- Coding: Strong Hire (4/5)
- System Design: Strong Hire (4/5)
- Architecture: Hire (3/5)
- Behavioral: Strong Hire (4/5)
- Overall: Strong Hire

Next Steps:
1. Extend offer: $180K base + equity (equivalent to $200K total comp)
2. Assign mentor: David Kim (Architecture interviewer) for distributed systems growth
3. Onboarding plan: Start with microservices team (matches her experience)
4. Expected start date: 2 weeks (per candidate availability)

Confidence Level: HIGH
Recommendation: MOVE FORWARD WITH OFFER
```

---

## Pattern Type 3: Handoff Decision Examples (5 examples)

### Example 3.1: Azure Solutions Architect → DNS Specialist

```
USER: "Setup Azure Exchange Online for company.com with 500 users, including custom domain email authentication"

AGENT REASONING:
My scope (Azure Solutions Architect):
- ✅ Exchange Online provisioning and configuration
- ✅ User licensing and mailbox setup
- ✅ Exchange Online security settings

Outside my expertise:
- ❌ DNS record creation and management (SPF, DKIM, DMARC, MX)
- ❌ Email authentication best practices
- ❌ DNS provider-specific configuration

This task requires DNS expertise for:
1. MX record configuration for Exchange Online
2. SPF/DKIM/DMARC authentication setup
3. DNS validation and testing

WORK COMPLETED (Azure):
- Created Exchange Online organization
- Assigned Exchange Online Plan 2 licenses to 500 users
- Configured mailbox policies and security settings
- Generated DKIM public key for company.com
- Status: Azure side complete, needs DNS configuration

HANDOFF DECLARATION:
To: dns_specialist
Reason: DNS record creation and email authentication setup required
Context:
  - Exchange Online ready for company.com
  - Need MX records: company-com.mail.protection.outlook.com (priority 0)
  - Need SPF: include:spf.protection.outlook.com
  - DKIM selectors: selector1/selector2._domainkey.company.com
  - DKIM public keys: [provided in handoff data]
  - Need DMARC policy with monitoring setup
  - User count: 500 (for context on email volume)

Next steps (DNS Specialist):
1. Create MX records for Exchange Online
2. Implement SPF/DKIM/DMARC authentication
3. Validate DNS configuration
4. Test email flow and deliverability
```

### Example 3.2: DNS Specialist → Security Analyst

```
USER: "I found suspicious DNS queries to random-looking domains from our network - investigate"

AGENT REASONING:
My scope (DNS Specialist):
- ✅ DNS query analysis and pattern detection
- ✅ Domain reputation checking
- ✅ DNS configuration and troubleshooting

Outside my expertise:
- ❌ Security threat analysis and investigation
- ❌ Malware identification
- ❌ Incident response procedures
- ❌ Forensic analysis

This task requires security expertise for:
1. Threat classification (malware, C2, data exfiltration)
2. Incident response coordination
3. Forensic investigation
4. Remediation recommendations

WORK COMPLETED (DNS):
- Analyzed DNS query logs (last 24 hours)
- Identified pattern: DGA (Domain Generation Algorithm)
- Found 247 queries to random domains from IP 10.0.5.42
- Sample domains:
  - xj2k9f3mzp.com
  - q8n4h7b2vl.net
  - r5m3t9c6dx.org
- All domains: Newly registered (< 7 days old)
- All queries: Failed (NXDOMAIN responses)
- Source IP: 10.0.5.42 (employee workstation - John Smith)
- Pattern matches known malware families (Emotet, Qakbot)

HANDOFF DECLARATION:
To: security_analyst
Reason: Suspected malware C2 communication detected - requires security investigation
Context:
  - Affected host: 10.0.5.42 (John Smith's workstation)
  - Threat indicator: DGA-based DNS queries (247 attempts in 24h)
  - Pattern: Matches Emotet/Qakbot malware behavior
  - Status: DNS queries are failing (domains don't exist yet)
  - Risk: Malware is active but C2 connection not established
  - Evidence: DNS query logs attached

Urgent actions needed (Security Analyst):
1. Isolate infected workstation (10.0.5.42) immediately
2. Perform malware forensics and identify infection vector
3. Check for lateral movement to other systems
4. Determine data exfiltration (if any)
5. Coordinate incident response and remediation
```

### Example 3.3: SRE Principal → DevOps Engineer

```
USER: "Optimize our CI/CD pipeline - builds are taking 45 minutes and blocking deployments"

AGENT REASONING:
My scope (SRE Principal):
- ✅ Performance analysis and bottleneck identification
- ✅ Infrastructure optimization recommendations
- ✅ Monitoring and observability

Outside my expertise:
- ❌ CI/CD pipeline configuration (Jenkins, GitLab CI, etc.)
- ❌ Build tool optimization (Maven, Gradle, npm, etc.)
- ❌ Container image optimization
- ❌ Pipeline-specific implementation

This task requires DevOps expertise for:
1. CI/CD pipeline reconfiguration
2. Build tool optimization
3. Caching strategy implementation
4. Pipeline parallelization

WORK COMPLETED (SRE):
- Analyzed build performance metrics
- Identified bottlenecks:
  1. Dependency downloads: 18 minutes (40% of time)
  2. Test execution: 15 minutes (33% of time)
  3. Docker image build: 12 minutes (27% of time)
- Current pipeline: Sequential stages (no parallelization)
- Infrastructure: Single CI runner (m5.large)
- Recommendations:
  1. Implement dependency caching (save 15 min)
  2. Parallelize test execution (save 10 min)
  3. Use multi-stage Docker builds (save 8 min)
  4. Add more CI runners (reduce queue time)
- Expected improvement: 45 min → 12 min (73% reduction)

HANDOFF DECLARATION:
To: devops_engineer
Reason: CI/CD pipeline optimization requires DevOps implementation expertise
Context:
  - Current build time: 45 minutes (unacceptable)
  - Target build time: <15 minutes
  - Bottlenecks identified:
    * Dependency downloads: 18 min (need caching)
    * Test execution: 15 min (need parallelization)
    * Docker builds: 12 min (need multi-stage optimization)
  - Infrastructure: Single m5.large CI runner (need horizontal scaling)
  - CI tool: GitLab CI
  - Expected improvement: 73% time reduction (45min → 12min)

Implementation tasks (DevOps Engineer):
1. Configure dependency caching (npm, Maven, pip)
2. Parallelize test stages (unit, integration, e2e)
3. Implement multi-stage Docker builds
4. Add 2 more CI runners (horizontal scaling)
5. Validate build time reduction
6. Update deployment SLAs
```

### Example 3.4: Service Desk Manager → Network Engineer

```
USER: "Multiple users reporting 'cannot access file share' - resolve this issue"

AGENT REASONING:
My scope (Service Desk Manager):
- ✅ Ticket triage and user communication
- ✅ Impact assessment and prioritization
- ✅ Basic troubleshooting coordination

Outside my expertise:
- ❌ Network infrastructure diagnostics
- ❌ File server configuration
- ❌ Network protocol troubleshooting (SMB, CIFS)
- ❌ Firewall and routing issues

This task requires network expertise for:
1. Network path validation
2. File server connectivity diagnosis
3. Protocol and firewall investigation
4. Root cause identification

WORK COMPLETED (Service Desk):
- Created incident ticket: INC-8472
- User impact assessment:
  * Affected: 45 users (accounting department)
  * Location: Building B, 3rd floor
  * File share: \\fileserver01\accounting
  * Error: "Network path not found"
- Basic troubleshooting:
  * Users can ping fileserver01 (10.0.10.50) ✅
  * Users can access other file shares ✅
  * Only \accounting share is affected ❌
  * Started 30 minutes ago (2:15 PM)
- No recent changes reported by users
- Priority: P2 (business impact - accounting blocked)

HANDOFF DECLARATION:
To: network_engineer
Reason: Network-level file share connectivity issue requires network expertise
Context:
  - Incident: INC-8472
  - Affected share: \\fileserver01\accounting
  - Affected users: 45 (accounting department, Building B, 3rd floor)
  - Symptoms: "Network path not found" error
  - Network connectivity: Ping works ✅
  - Other shares: Accessible ✅
  - Timeline: Started 2:15 PM (30 min ago)
  - Business impact: Accounting department blocked
  - Priority: P2

Diagnostics needed (Network Engineer):
1. Check SMB/CIFS port accessibility (445, 139)
2. Verify file server network configuration
3. Check firewall rules for \accounting share
4. Validate DNS resolution for fileserver01
5. Check for network segmentation issues
6. Review recent network changes
```

### Example 3.5: Financial Advisor → Legal Compliance

```
USER: "Review my investment portfolio and recommend tax-efficient strategies for 2025"

AGENT REASONING:
My scope (Financial Advisor):
- ✅ Investment portfolio analysis
- ✅ Tax-efficient investment strategies (general guidance)
- ✅ Asset allocation recommendations
- ✅ Financial planning

Outside my expertise:
- ❌ Specific tax law interpretation
- ❌ Legal compliance for complex structures
- ❌ International tax implications
- ❌ Trust and estate law

This task requires legal/compliance expertise for:
1. 2025 tax law changes affecting investments
2. Legal compliance for recommended strategies
3. Estate planning considerations
4. Regulatory requirements

WORK COMPLETED (Financial Advisor):
- Analyzed current portfolio:
  * Total value: $2.8M
  * Taxable accounts: $1.5M
  * Retirement accounts (401k, IRA): $1.3M
  * Current tax bracket: 35% (high earner)
- Identified tax inefficiencies:
  * High dividend stocks in taxable account (taxed at 20%)
  * Bonds in taxable account (ordinary income tax at 35%)
  * No tax-loss harvesting in progress
- Recommended strategies:
  1. Asset location optimization (move bonds to IRA)
  2. Tax-loss harvesting ($50K potential losses)
  3. Qualified dividend focus in taxable account
  4. Roth conversion ladder for retirement
- Potential tax savings: ~$35K annually

HANDOFF DECLARATION:
To: legal_compliance_specialist
Reason: Tax strategies require legal review for 2025 tax law compliance
Context:
  - Client portfolio: $2.8M ($1.5M taxable, $1.3M retirement)
  - Client tax bracket: 35% (high earner)
  - Recommended strategies:
    * Asset location optimization (bonds → IRA)
    * Tax-loss harvesting ($50K losses)
    * Roth conversion ladder
    * Qualified dividend strategy
  - Estimated tax savings: $35K/year
  - Client concerns:
    * 2025 tax law changes affecting investment income
    * Estate planning implications
    * AMT (Alternative Minimum Tax) considerations

Legal review needed (Legal Compliance):
1. Verify 2025 tax law compliance for all strategies
2. Review Roth conversion ladder for legal requirements
3. Assess AMT implications
4. Estate planning considerations (client has $5M estate)
5. Confirm asset location moves comply with IRS rules
6. Document legal disclaimers and disclosures
```

---

## Pattern Type 4: Self-Critique Examples (5 examples)

### Example 4.1: SRE Principal - SLO Target Recommendations

```
USER: "Recommend SLO targets for our new customer API"

INITIAL ANALYSIS:
Based on industry standards, I recommend:
- Availability SLO: 99.99% (4 nines)
- Latency SLO: P99 < 100ms
- Error Rate SLO: < 0.01%

SELF-CRITIQUE:
Wait - these targets seem ambitious. Let me challenge my assumptions:

1. **99.99% availability = 4.3 minutes downtime per month**
   - Question: What's the current baseline? Do we have data?
   - Issue: If current availability is 99.5%, jumping to 99.99% requires massive investment
   - Concern: Overly aggressive SLO could force feature freeze

2. **P99 < 100ms latency**
   - Question: What's current P99 latency?
   - Issue: If current is 500ms, 100ms target requires architectural changes
   - Concern: May not be achievable without significant refactoring

3. **< 0.01% error rate**
   - Question: What's the error rate from dependencies?
   - Issue: If upstream APIs have 0.1% error rate, we can't achieve 0.01%
   - Concern: Impossible SLO is demotivating and useless

Let me query actual baseline metrics before recommending targets...

ACTION: Query current performance
```prometheus
# Availability (last 30 days)
avg_over_time(up{service="customer-api"}[30d])
Result: 99.5%

# Latency P99
histogram_quantile(0.99, http_request_duration_seconds)
Result: 450ms

# Error rate
sum(rate(http_requests_total{code=~"5.."}[30d])) / sum(rate(http_requests_total[30d]))
Result: 0.3%
```

OBSERVATION:
- Current availability: 99.5%
- Current P99 latency: 450ms
- Current error rate: 0.3%

REVISED ANALYSIS:
Based on actual baseline data (not just industry standards), here are achievable SLOs:

1. **Availability SLO: 99.9%** (not 99.99%)
   - Current: 99.5%
   - Target: 99.9% = 43.2 minutes downtime/month
   - Achievable: Yes, with improved monitoring and faster incident response
   - Investment: Moderate (better alerting, runbooks, on-call)

2. **Latency SLO: P99 < 500ms** (not 100ms)
   - Current: 450ms
   - Target: 500ms (10% buffer)
   - Achievable: Yes, maintain current performance
   - Future stretch goal: < 300ms (requires caching layer)

3. **Error Rate SLO: < 0.5%** (not 0.01%)
   - Current: 0.3%
   - Target: 0.5% (67% buffer)
   - Achievable: Yes, with better error handling
   - Note: Upstream dependency error rate is 0.2% (our floor)

**Self-Correction Summary**:
- Initial targets were based on "best practices" without context
- Revised targets based on actual data and constraints
- New SLOs are achievable, motivating, and provide room for improvement
- Learned to always baseline before setting targets
```

### Example 4.2: Cloud Architect - Cost Optimization

```
USER: "Optimize our AWS costs - we're spending too much"

INITIAL ANALYSIS:
Quick wins for cost optimization:
1. Purchase Reserved Instances (save 40%)
2. Use Spot Instances for batch jobs (save 70%)
3. Delete unused EBS volumes
4. Right-size over-provisioned instances

Estimated savings: ~30% ($50K/month)

SELF-CRITIQUE:
Wait - I'm making assumptions without data. Let me question my approach:

1. **Reserved Instances assumption**
   - Question: Are current workloads steady-state or variable?
   - Issue: RIs lock us in for 1-3 years
   - Concern: If workload is decreasing, RIs could increase costs

2. **Spot Instances assumption**
   - Question: Are batch jobs fault-tolerant?
   - Issue: Spot can be interrupted with 2-minute notice
   - Concern: If jobs can't handle interruption, this won't work

3. **"Over-provisioned" assumption**
   - Question: Based on what metric? CPU? Memory?
   - Issue: Low CPU doesn't mean over-provisioned (could be memory-bound)
   - Concern: Right-sizing could cause performance degradation

Let me actually analyze the cost breakdown and usage patterns...

ACTION: Analyze AWS costs
```bash
# Get cost breakdown
aws ce get-cost-and-usage --time-period Start=2025-09-01,End=2025-10-01 \
  --granularity MONTHLY --metrics BlendedCost --group-by Type=SERVICE

# Get instance utilization
aws cloudwatch get-metric-statistics --namespace AWS/EC2 \
  --metric-name CPUUtilization --dimensions Name=InstanceId,Value=* \
  --start-time 2025-09-01 --end-time 2025-10-01 --period 86400 \
  --statistics Average
```

OBSERVATION:
Cost Breakdown (actual data):
- EC2: $45K/month (27% of total)
- RDS: $58K/month (35% of total) ⚠️ LARGEST
- Data Transfer: $32K/month (19% of total)
- EBS: $15K/month (9% of total)
- Other: $17K/month (10% of total)
Total: $167K/month

Instance Utilization:
- Prod instances: 75% CPU average (well utilized ✅)
- Dev/staging: 15% CPU average (over-provisioned ❌)
- Batch jobs: Run 2 hours/day (could use Spot ✅)

REFLECTION:
My initial assumptions were WRONG:
- ❌ Focused on EC2 ($45K) but RDS is larger cost ($58K)
- ❌ Assumed prod instances over-provisioned (they're not)
- ✅ Batch jobs ARE good candidates for Spot
- ❌ Missed data transfer costs ($32K)

REVISED ANALYSIS:
Based on actual cost data, here's the real optimization plan:

1. **RDS Optimization (Biggest Impact: ~$25K/month)**
   - Current: 8 db.r5.2xlarge instances (over-provisioned)
   - Issue: Dev/staging using same size as prod
   - Action: Right-size dev/staging to db.t3.large (save $18K)
   - Action: Use Aurora Serverless v2 for low-traffic DBs (save $7K)

2. **Data Transfer Optimization ($15K/month)**
   - Current: Cross-region transfer from us-east-1 to eu-west-1
   - Issue: Downloading large datasets across regions
   - Action: Use S3 bucket replication instead (save $12K)
   - Action: Enable VPC endpoints for S3 (save $3K)

3. **Dev/Staging EC2 ($8K/month)**
   - Current: Running 24/7 at 15% utilization
   - Action: Auto-stop during nights/weekends (save $5K)
   - Action: Right-size from t3.xlarge to t3.large (save $3K)

4. **Batch Jobs - Spot Instances ($3K/month)**
   - Current: On-demand for 2 hours/day
   - Validated: Jobs ARE fault-tolerant (checkpointing enabled)
   - Action: Convert to Spot Instances (save $2K)
   - Action: Use Spot Fleet for better availability (save $1K)

5. **EBS Volume Cleanup ($2K/month)**
   - Current: 850 GB unused volumes detected
   - Action: Delete after 7-day grace period (save $2K)

Total Revised Savings: $53K/month (32% reduction, not 30%)

**Self-Correction Summary**:
- Initial plan focused on wrong services (EC2 instead of RDS)
- Assumed over-provisioning without checking actual utilization
- Missed largest cost opportunity (data transfer)
- Learned to analyze cost breakdown BEFORE recommending actions
- New plan targets highest-impact areas first
```

### Example 4.3: Security Analyst - Vulnerability Assessment

```
USER: "We found CVE-2025-1234 in our production web servers - should we patch immediately?"

INITIAL ANALYSIS:
CVE-2025-1234 is a critical vulnerability (CVSS 9.8). Recommendation:
- **Patch immediately** (within 24 hours)
- All production web servers affected
- Risk: Remote code execution
- Priority: P0 (critical)

SELF-CRITIQUE:
Wait - "critical CVSS score" doesn't automatically mean "critical to our business." Let me question my assumptions:

1. **CVSS 9.8 = Critical?**
   - Question: Is this vulnerability actually exploitable in OUR environment?
   - Issue: CVSS assumes worst-case scenario, not our specific configuration
   - Concern: Rushing patches could cause outage (worse than vulnerability)

2. **All web servers affected?**
   - Question: Do we even use the vulnerable component?
   - Issue: Vulnerability might be in optional module we don't enable
   - Concern: Unnecessary patching could introduce instability

3. **Patch immediately = 24 hours?**
   - Question: Is there active exploitation in the wild?
   - Issue: If not actively exploited, we have time for proper testing
   - Concern: Untested patches can break production

Let me actually assess this vulnerability in the context of OUR environment...

ACTION: Detailed vulnerability analysis
```bash
# Check if vulnerable component is actually used
dpkg -l | grep "vulnerable-package"

# Check configuration
cat /etc/web-server/config.conf | grep "vulnerable-module"

# Check for active exploits
curl https://api.vulndb.com/v1/cve/CVE-2025-1234/exploits

# Check vendor patch availability
apt-cache policy vulnerable-package
```

OBSERVATION:
1. **Vulnerable package IS installed**: vulnerable-package 2.4.1
2. **BUT vulnerable module is DISABLED in our config**:
   ```
   # Vulnerable-Module: disabled (not used)
   LoadModule vulnerable_module modules/mod_vulnerable.so  # COMMENTED OUT
   ```
3. **Exploit availability**: No public exploits yet (CVE published 2 days ago)
4. **Vendor patch**: Available but marked "beta" (not stable)
5. **Our configuration**: Module is compiled in but never loaded

REFLECTION:
My initial "patch immediately" was premature because:
- ❌ Assumed vulnerability is exploitable (it's not - module disabled)
- ❌ Didn't check if we actually use the vulnerable feature
- ❌ Didn't verify exploit availability (no active threats)
- ❌ Didn't check patch stability (vendor patch is beta)

REVISED ANALYSIS:
Based on environment-specific assessment:

**Risk Assessment for OUR Environment**:
- CVSS Score: 9.8 (theoretical maximum)
- Actual Risk: LOW (module disabled in our configuration)
- Exploit Availability: None (CVE only 2 days old)
- Attack Complexity: HIGH (requires module to be loaded)

**Recommendation: DEFER IMMEDIATE PATCHING**

Rationale:
1. **Not Exploitable**: Vulnerable module is disabled in our config
2. **No Active Threats**: No public exploits available
3. **Patch Immaturity**: Vendor patch is beta (risk of regression)
4. **Time for Testing**: Can wait for stable patch release

**Risk Mitigation (Instead of Immediate Patching)**:
1. ✅ **Verify module is disabled across ALL servers** (audit)
2. ✅ **Monitor for exploit release** (set up CVE alerts)
3. ✅ **Block vulnerable URL patterns at WAF** (defense in depth)
4. ✅ **Wait for stable patch** (vendor ETA: 1 week)
5. ✅ **Test patch in staging** before production deployment

**Revised Timeline**:
- Week 1: Monitor + WAF rules (immediate)
- Week 2: Apply stable patch to staging (testing)
- Week 3: Production patching (after validation)

**Self-Correction Summary**:
- CVSS score ≠ actual risk in specific environment
- Must assess exploitability in OUR configuration
- Immediate patching isn't always best (can introduce new risks)
- Defense in depth (WAF) can buy time for proper testing
- Learned to contextual risk assessment over blanket severity ratings
```

### Example 4.4: Data Engineer - Pipeline Optimization

```
USER: "Our ETL pipeline is slow - optimize it"

INITIAL ANALYSIS:
Quick optimizations:
1. Parallelize data extraction (use multiprocessing)
2. Increase Spark executor memory
3. Add more worker nodes (horizontal scaling)
4. Use columnar format (Parquet instead of CSV)

Expected speedup: 3-5x faster

SELF-CRITIQUE:
Wait - I'm suggesting optimizations without understanding the actual bottleneck. Classic premature optimization. Let me question my approach:

1. **Parallelize extraction?**
   - Question: Is extraction even the bottleneck?
   - Issue: Could be transformation or loading that's slow
   - Concern: Adding parallelization adds complexity for no gain

2. **Increase Spark memory?**
   - Question: Is there a memory bottleneck? Any OOM errors?
   - Issue: More memory won't help if CPU-bound
   - Concern: Costs more with no performance benefit

3. **Add more workers?**
   - Question: Is the job distributed efficiently?
   - Issue: Could have data skew (one worker does all work)
   - Concern: More workers = more cost with no speedup

4. **Use Parquet?**
   - Question: What's the current I/O vs compute ratio?
   - Issue: If compute-bound, storage format doesn't matter
   - Concern: Migration effort with no actual benefit

I need to PROFILE the pipeline before recommending anything...

ACTION: Profile ETL pipeline
```python
# Profile pipeline stages
import time

stages = {
    'extract': time_extract(),
    'transform': time_transform(),
    'load': time_load()
}

# Analyze Spark job
spark.sparkContext.statusTracker.getJobInfo(jobId)

# Check resource utilization
spark.sparkContext.getExecutorMemoryStatus()
```

OBSERVATION:
Pipeline timing (actual data):
- Extract: 2 minutes (3% of total)
- Transform: 58 minutes (83% of total) ⚠️ BOTTLENECK
- Load: 10 minutes (14% of total)
- Total: 70 minutes

Spark job analysis:
- Task skew: 95% of data processed by 1 partition (highly skewed!)
- Executor memory: 30% used (NOT memory-bound)
- Executor CPU: 25% used (NOT CPU-bound either)
- I/O wait: 85% (I/O bound!)

Root cause: Single large file (150GB) processed by one partition → I/O bottleneck

REFLECTION:
ALL my initial suggestions were wrong:
- ❌ Parallelize extraction (not the bottleneck)
- ❌ Increase memory (only 30% used)
- ❌ Add workers (data skew makes them idle)
- ❌ Use Parquet (I/O is the issue, not format)

Actual problem: Data skew from single massive file + I/O bottleneck

REVISED ANALYSIS:
Based on profiling data, here's the ACTUAL optimization:

**Root Cause**:
- 150GB single file processed by 1 partition
- 95% of data in one partition (extreme skew)
- I/O wait: 85% (reading from single file is slow)

**Real Optimization Plan**:

1. **Fix Data Skew (Biggest Impact: 50x speedup)**
   - Current: 1 file = 1 partition = 1 executor working
   - Action: Split source file into 100 smaller files (1.5GB each)
   - Result: 100 partitions = 100 executors working in parallel
   - Expected speedup: 50x on transform stage (58min → 1.2min)

2. **Optimize I/O (Additional 2x speedup)**
   - Current: Reading from slow HDD storage
   - Action: Move source data to SSD-backed S3 (5x faster I/O)
   - Result: Reduce I/O wait from 85% to 20%
   - Expected speedup: 2x overall

3. **Enable Adaptive Query Execution (Free optimization)**
   - Current: Static partitions (100 set at start)
   - Action: spark.sql.adaptive.enabled = true
   - Result: Automatic partition coalescing for small files
   - Expected benefit: Better resource utilization

**Revised Performance Estimate**:
- Current: 70 minutes
- After optimizations: 1.5 minutes (47x faster!)
- Breakdown:
  * Extract: 2 min → 0.5 min (SSD storage)
  * Transform: 58 min → 1.2 min (fix skew + I/O)
  * Load: 10 min → 0.8 min (parallel writes)

**Implementation Plan**:
1. Split 150GB file into 100x 1.5GB files (one-time preprocessing)
2. Move data to SSD-backed S3 bucket
3. Enable adaptive query execution
4. Test in staging environment
5. Deploy to production

Cost: $200 (SSD storage increase)
Benefit: 47x speedup (70min → 1.5min)
ROI: Save 68.5 min per run × 10 runs/day = 11.4 hours/day saved

**Self-Correction Summary**:
- NEVER optimize without profiling first
- "Common optimizations" don't apply if not the bottleneck
- Data skew is often the hidden killer (95% in 1 partition)
- I/O bound problems need I/O solutions (not CPU/memory)
- Learned to measure first, optimize second
```

### Example 4.5: Product Manager - Feature Prioritization

```
USER: "Should we build dark mode or mobile app first?"

INITIAL ANALYSIS:
Build mobile app first because:
1. Mobile traffic is 60% of our users
2. Competitors have mobile apps
3. Higher revenue potential ($2M/year)
4. Dark mode is just cosmetic

Recommendation: Mobile app (Priority 1)

SELF-CRITIQUE:
Wait - I'm making a recommendation based on surface-level data without considering strategic context. Let me challenge this:

1. **60% mobile traffic?**
   - Question: Are they already accessing via mobile web?
   - Issue: If mobile web works, native app might not add value
   - Concern: Building app when web works = wasted investment

2. **Competitors have apps?**
   - Question: Are users ASKING for an app or just me seeing competitors?
   - Issue: Following competitors without user demand is reactive
   - Concern: "Competitor has it" ≠ "We need it"

3. **$2M revenue potential?**
   - Question: Where did this number come from? Is it validated?
   - Issue: Sounds like a guess, not a data-driven estimate
   - Concern: Unvalidated assumptions lead to failed projects

4. **Dark mode is cosmetic?**
   - Question: Do we have user requests for dark mode?
   - Issue: Might have accessibility benefits (not just cosmetic)
   - Concern: Dismissing user pain points as "cosmetic"

I need actual user data, not assumptions...

ACTION: Analyze user data and feedback
```sql
-- User feedback analysis
SELECT feature_request, count(*), avg(urgency_rating)
FROM user_feedback
WHERE created_date > NOW() - INTERVAL '90 days'
GROUP BY feature_request
ORDER BY count(*) DESC;

-- Mobile web vs desktop usage
SELECT device_type,
       count(distinct user_id) as users,
       avg(session_duration) as avg_session_min,
       avg(conversion_rate) as conversion_pct
FROM analytics
WHERE date > NOW() - INTERVAL '30 days'
GROUP BY device_type;

-- Revenue by platform
SELECT platform, sum(revenue) as total_revenue
FROM transactions
WHERE date > NOW() - INTERVAL '90 days'
GROUP BY platform;
```

OBSERVATION:

User Feedback (last 90 days):
1. Dark mode: 847 requests (urgency: 8.2/10) ⚠️ HIGHEST
2. Better mobile experience: 234 requests (urgency: 6.5/10)
3. Native mobile app: 89 requests (urgency: 5.1/10)

Mobile Web Analytics:
- Mobile traffic: 60% of users (confirmed)
- Mobile session duration: 2.3 min (vs desktop 8.7 min) ⚠️ LOW
- Mobile conversion rate: 1.2% (vs desktop 4.8%) ⚠️ LOW
- Mobile bounce rate: 68% (vs desktop 32%) ⚠️ HIGH

Revenue Data:
- Desktop: $8.5M/quarter
- Mobile web: $1.2M/quarter (despite 60% traffic!)
- Issue: Mobile gets 60% traffic but only 12% revenue

User Comments on Dark Mode:
- "Eye strain using app at night - need dark mode ASAP"
- "Accessibility issue - bright mode triggers migraines"
- "Using competitor app because they have dark mode"

REFLECTION:
My initial analysis was completely backwards:
- ❌ Assumed mobile app solves mobile problem (it doesn't - mobile WEB is broken)
- ❌ Ignored user feedback (847 dark mode requests vs 89 app requests)
- ❌ Didn't notice mobile conversion is 4x worse (1.2% vs 4.8%)
- ❌ Dismissed dark mode as cosmetic (it's an accessibility issue)

Real insights:
- Dark mode: 847 user requests (9.5x more than app requests)
- Mobile problem: Not lack of app, but poor mobile WEB experience
- Revenue opportunity: Fix mobile conversion (1.2% → 3% = +$2.5M)

REVISED ANALYSIS:
Based on actual user data and business metrics:

**Priority 1: Dark Mode** ✅
Rationale:
- User demand: 847 requests (9.5x more than app)
- Accessibility: Prevents migraines, eye strain (not cosmetic!)
- Competitive: Users switching to competitors for dark mode
- Quick win: 2 weeks to implement
- Revenue impact: Retain users switching to competitors (~$500K/year)
- ROI: High value, low effort

**Priority 2: Fix Mobile Web Experience** ✅
Rationale:
- Current mobile conversion: 1.2% (4x worse than desktop)
- 60% of traffic but only 12% of revenue ($1.2M vs $8.5M)
- Issues: Slow loading, poor UX, high bounce rate (68%)
- Opportunity: Improve mobile conversion 1.2% → 3% = +$2.5M/year
- Effort: 6 weeks (fix performance, responsive design, UX)
- ROI: Much higher than building new app

**Priority 3: Mobile App** (DEFERRED)
Rationale:
- User demand: Only 89 requests (low)
- Mobile web works once fixed (no need for separate app)
- Effort: 6 months + ongoing maintenance
- Uncertain ROI ($2M estimate was unvalidated)
- Defer until mobile web proven successful

**Revised Recommendation**:
1. Build dark mode (2 weeks, high user demand, accessibility)
2. Fix mobile web (6 weeks, $2.5M revenue opportunity)
3. Defer mobile app (6+ months, low demand, uncertain ROI)

Total Timeline: 8 weeks (vs 6+ months for app)
Total Revenue Impact: $3M/year ($500K dark mode + $2.5M mobile web)

**Self-Correction Summary**:
- User requests > competitor features
- Data-driven revenue estimates > gut feel
- Fix existing platforms before building new ones
- "Cosmetic" features can be accessibility wins
- Learned to validate assumptions with actual user data
```

---

## Usage Guidelines

### When to Include Each Pattern Type

1. **Tool-Calling Examples** (Pattern 1)
   - Use when: Agent has 5+ tool commands
   - Frequency: 2-3 examples per agent
   - Select: Most common tools + complex tools

2. **ReACT Examples** (Pattern 2)
   - Use when: Agent handles complex troubleshooting
   - Frequency: 1-2 examples per agent
   - Select: Representative problem-solving scenarios

3. **Handoff Examples** (Pattern 3)
   - Use when: Agent frequently collaborates with other agents
   - Frequency: 1-2 examples per agent
   - Select: Common handoff scenarios

4. **Self-Critique Examples** (Pattern 4)
   - Use when: Agent makes high-stakes decisions
   - Frequency: 1-2 examples per agent
   - Select: Scenarios where assumptions must be validated

### Example Selection Criteria

For each agent, select examples that:
- ✅ Match the agent's primary use cases
- ✅ Demonstrate systematic thinking
- ✅ Show real-world complexity (not trivial cases)
- ✅ Include both happy path and edge cases
- ✅ Are detailed enough to be instructive (not just templates)

### Integration with Agent Prompts

Include selected examples in the agent prompt template under:
```markdown
## Few-Shot Examples

### Example 1: [Tool-Calling - Primary Command]
[Insert example from Pattern Type 1]

### Example 2: [ReACT - Common Troubleshooting Scenario]
[Insert example from Pattern Type 2]

### Example 3: [Handoff - Frequent Collaboration]
[Insert example from Pattern Type 3]
```

---

**Status**: Complete ✅
**Total Examples**: 20 (5 per pattern type)
**Last Updated**: 2025-10-12
**Created By**: Maia Development Team
