# Maia Agent Ecosystem - Few-Shot Example Library

**Created**: 2025-10-11
**Purpose**: Reusable few-shot examples for all 46 agents in Phase 107 evolution
**Organization**: 4 pattern types × 5 examples each = 20 total examples

---

## Table of Contents

1. [Tool-Calling Examples](#pattern-type-1-tool-calling-examples) (5 examples)
2. [ReACT Pattern Examples](#pattern-type-2-react-reasoning--acting-examples) (5 examples)
3. [Handoff Decision Examples](#pattern-type-3-handoff-decision-examples) (5 examples)
4. [Self-Critique Examples](#pattern-type-4-self-critique-examples) (5 examples)

---

## Pattern Type 1: Tool-Calling Examples

### Generic Template
```
USER: "[User request requiring tool usage]"

AGENT REASONING:
- [Identify which tool is needed]
- [Why this tool vs alternatives]

ACTION:
[Code showing correct tool usage]

RESULT:
[Process tool output and provide user value]
```

---

### Example 1.1: DNS Query (DNS Specialist Domain)

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

---

### Example 1.2: Metrics Query (SRE Domain)

```
USER: "What's our API P95 latency for the last hour?"

AGENT REASONING:
- Need to query Prometheus for latency metrics
- P95 = 95th percentile (histogram_quantile function)
- Use prometheus_query tool with appropriate query

ACTION:
result = self.call_tool(
    tool_name="prometheus_query",
    parameters={
        "query": "histogram_quantile(0.95, http_request_duration_seconds)",
        "time_range": "1h"
    }
)

# Extract current value
current_p95 = result.data.value
slo_target = 0.300  # 300ms

RESULT:
Current API P95 latency: 245ms (last hour)
SLO target: 300ms
Status: ✅ Within SLO (18% margin)

Trend: Stable (±10ms variance over last hour)
Recommendation: No action needed, latency healthy
```

---

### Example 1.3: Azure Resource Query (Azure Solutions Architect Domain)

```
USER: "Show me all VMs in production resource group with their sizes"

AGENT REASONING:
- Need to query Azure Resource Manager API
- Filter by resource group "production"
- Resource type: Microsoft.Compute/virtualMachines
- Use azure_resource_list tool

ACTION:
result = self.call_tool(
    tool_name="azure_resource_list",
    parameters={
        "resource_group": "production",
        "resource_type": "Microsoft.Compute/virtualMachines",
        "include_properties": ["vmSize", "osType", "provisioningState"]
    }
)

# Process results
vms_summary = []
for vm in result.resources:
    vms_summary.append({
        "name": vm.name,
        "size": vm.properties.vmSize,
        "os": vm.properties.osType,
        "state": vm.properties.provisioningState
    })

RESULT:
Production VMs (5 total):

1. prod-web-01: Standard_D4s_v3 (Linux, Running)
2. prod-web-02: Standard_D4s_v3 (Linux, Running)
3. prod-db-01: Standard_E8s_v3 (Linux, Running)
4. prod-app-01: Standard_D8s_v3 (Windows, Running)
5. prod-app-02: Standard_D8s_v3 (Windows, Running)

Total compute: 32 vCPUs, 112 GB RAM
Estimated monthly cost: $1,847 (assuming 730 hours/month)
```

---

### Example 1.4: Deployment Status Check (DevOps Domain)

```
USER: "Check status of the api-service deployment"

AGENT REASONING:
- Need to query Kubernetes deployment status
- Check replica status, image version, conditions
- Use kubectl_get_deployment tool

ACTION:
result = self.call_tool(
    tool_name="kubectl_get_deployment",
    parameters={
        "deployment_name": "api-service",
        "namespace": "production",
        "include_pods": True
    }
)

# Check deployment health
deployment = result.deployment
pods = result.pods

RESULT:
api-service Deployment Status:

Replicas: 3/3 ready (100% available)
Current Image: api-service:v2.4.1
Rollout Status: Complete (deployed 2 hours ago)

Pod Health:
- api-service-7d9f8b-abc12: Running (2h, ready)
- api-service-7d9f8b-def34: Running (2h, ready)
- api-service-7d9f8b-ghi56: Running (2h, ready)

Conditions:
✅ Available: True (all replicas ready)
✅ Progressing: True (rollout complete)

Status: ✅ Healthy - All systems operational
```

---

### Example 1.5: File Content Search (General Development Domain)

```
USER: "Find all TODO comments in the codebase"

AGENT REASONING:
- Need to search file contents for pattern
- Use grep tool with case-insensitive search
- Filter for code files (exclude docs, vendor)

ACTION:
result = self.call_tool(
    tool_name="grep",
    parameters={
        "pattern": "TODO:",
        "path": ".",
        "glob": "*.{py,js,ts,go,java}",
        "case_insensitive": True,
        "output_mode": "content",
        "line_numbers": True
    }
)

# Group by file
todos_by_file = {}
for match in result.matches:
    if match.file not in todos_by_file:
        todos_by_file[match.file] = []
    todos_by_file[match.file].append({
        "line": match.line_number,
        "text": match.content.strip()
    })

RESULT:
Found 12 TODO comments across 7 files:

services/api.py (3 TODOs):
  Line 45: # TODO: Add rate limiting
  Line 108: # TODO: Implement caching layer
  Line 234: # TODO: Add retry logic for DB failures

services/auth.py (2 TODOs):
  Line 67: # TODO: Switch to OAuth2
  Line 143: # TODO: Add session expiration

[5 more files with 7 TODOs...]

Recommendation: Create tickets for high-priority TODOs (rate limiting, retry logic)
```

---

## Pattern Type 2: ReACT (Reasoning + Acting) Examples

### Generic Template
```
USER: "[Complex problem requiring investigation]"

AGENT REASONING (ReACT Loop):

THOUGHT: [Initial analysis of the problem]
PLAN: [Multi-step approach]

ACTION 1: [First investigation step]
OBSERVATION: [What was discovered]
REFLECTION: [What this tells us, adjust plan if needed]

ACTION 2: [Next step based on observation]
OBSERVATION: [New findings]
REFLECTION: [Updated understanding]

[Continue loop until resolution]

RESULT: [Final solution with complete explanation]
```

---

### Example 2.1: Performance Degradation Investigation (SRE Domain)

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

---

### Example 2.2: Email Deliverability Crisis (DNS Specialist Domain)

```
USER: "Emails suddenly going to spam - inbox placement dropped from 95% to 40%"

AGENT REASONING (ReACT Loop):

THOUGHT: Sudden deliverability drop suggests authentication failure or blacklisting. Most likely SPF/DKIM/DMARC issue.

PLAN:
1. Check email authentication status (SPF/DKIM/DMARC)
2. Check blacklist status for sending IP/domain
3. Identify root cause
4. Implement fix
5. Validate with test emails

ACTION 1: Query authentication records
```python
auth_check = self.call_tool(
    tool_name="email_auth_validator",
    parameters={
        "domain": "example.com",
        "check_spf": True,
        "check_dkim": True,
        "check_dmarc": True
    }
)
```

OBSERVATION:
- SPF: ✅ Pass (v=spf1 include:spf.protection.outlook.com -all)
- DKIM: ❌ Fail (selector mismatch - DNS has "default", email system uses "2024october")
- DMARC: ❌ Fail (45% fail rate due to DKIM failures)

REFLECTION: DKIM selector mismatch is the root cause. Email system rotated keys but DNS wasn't updated.

ACTION 2: Get correct DKIM public key
```python
dkim_key = self.call_tool(
    tool_name="get_dkim_public_key",
    parameters={
        "domain": "example.com",
        "selector": "2024october"
    }
)
```

OBSERVATION: Retrieved public key for "2024october" selector

REFLECTION: Need to publish this DNS record immediately to fix DKIM

ACTION 3: Update DNS with correct DKIM record
```
2024october._domainkey.example.com TXT "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb..."
```

OBSERVATION:
- DNS updated, propagating (TTL 300 = 5 minutes)
- Waiting for propagation...

ACTION 4: Validate fix with test emails
```python
test_result = self.call_tool(
    tool_name="send_test_email",
    parameters={
        "from": "test@example.com",
        "to": "check-auth@mail-tester.com"
    }
)
```

OBSERVATION:
- DKIM now passes ✅
- DMARC pass rate recovering (98%+)
- mail-tester.com score: 10/10
- Test emails reaching inbox (not spam)

RESULT:
Deliverability crisis resolved in 20 minutes.

Root cause: DKIM key rotation incomplete (email system updated but DNS not updated)

Fix: Published correct DKIM public key for "2024october" selector

Prevention:
- Document DKIM rotation procedure (DNS MUST be updated first)
- Add monitoring alert for DKIM failures (>1% fail rate)
- Create runbook for DKIM troubleshooting

Deliverability status: Restored to 93% inbox placement (recovering to 95% over next 24 hours)
```

---

### Example 2.3: Azure Cost Spike Investigation (Azure Solutions Architect Domain)

```
USER: "Azure bill jumped from $5K to $12K this month - help me find the cause"

AGENT REASONING (ReACT Loop):

THOUGHT: 140% cost increase suggests resource scale-out, new services, or misconfigured resources. Need to identify what changed.

PLAN:
1. Compare current vs previous month resource usage
2. Identify top cost contributors
3. Look for anomalies (over-provisioned, orphaned resources)
4. Recommend cost optimization actions

ACTION 1: Query cost breakdown by service
```python
cost_data = self.call_tool(
    tool_name="azure_cost_analysis",
    parameters={
        "time_range": "current_month",
        "group_by": "service",
        "compare_to": "previous_month"
    }
)
```

OBSERVATION:
- Compute: $2.8K (was $2.5K, +12%)
- Storage: $1.2K (was $1.1K, +9%)
- Database: $7.5K (was $1.2K, +525%) ⚠️ SPIKE
- Networking: $0.5K (was $0.2K, +150%)

REFLECTION: Database costs spiked 525% - this is the culprit. Need to dig into database resources.

ACTION 2: Analyze database resource changes
```python
db_resources = self.call_tool(
    tool_name="azure_resource_list",
    parameters={
        "resource_type": "Microsoft.Sql/servers/databases",
        "include_properties": ["sku", "maxSizeBytes", "createDate"]
    }
)
```

OBSERVATION:
- prod-db-01: Standard S2 → Premium P4 (tier change 2 weeks ago) ⚠️
- Cost: $78/month → $1,645/month (+2,011% increase)
- Change made: 2024-09-28 (2 weeks ago)

REFLECTION: Someone upgraded database tier from S2 to P4 (21x cost increase). Need to check if this was intentional and if it's actually needed.

ACTION 3: Analyze database utilization
```python
db_metrics = self.call_tool(
    tool_name="azure_monitor_metrics",
    parameters={
        "resource_id": "/subscriptions/.../databases/prod-db-01",
        "metrics": ["dtu_consumption_percent", "storage_percent"],
        "time_range": "14d"
    }
)
```

OBSERVATION:
- DTU consumption: Average 12% (P4 provides 125 DTUs, using ~15)
- Storage: 8 GB used (P4 allows 500 GB)
- Current tier: P4 (125 DTUs, $1,645/month)
- Recommended tier: S2 (50 DTUs, $75/month) - sufficient for 12% avg usage

REFLECTION: Database is massively over-provisioned. P4 tier not needed - can downgrade to S2 or even S1.

ACTION 4: Get change history
```python
change_log = self.call_tool(
    tool_name="azure_activity_log",
    parameters={
        "resource_id": "/subscriptions/.../databases/prod-db-01",
        "operation": "Microsoft.Sql/servers/databases/write",
        "time_range": "30d"
    }
)
```

OBSERVATION:
- Change made by: john.doe@company.com
- Timestamp: 2024-09-28 14:23 UTC
- Reason: "Performance testing" (from change ticket)

REFLECTION: Tier was upgraded for performance testing but never downgraded. This is the root cause of cost spike.

RESULT:
Root cause identified: Database tier upgraded from S2 to P4 for performance testing but never downgraded.

Cost impact:
- S2: $75/month
- P4: $1,645/month
- Difference: $1,570/month ($7,850 over 5 months remaining)

Immediate actions:
1. Downgrade prod-db-01 from P4 to S2 (saves $1,570/month)
2. Validate application performance after downgrade
3. If S2 insufficient, try S3 ($150/month) as middle ground

Prevention measures:
1. Create Azure Policy: Require approval for tier changes >$500/month
2. Setup Azure Cost Alert: Notify when cost increases >20% week-over-week
3. Implement tagging: "purpose" and "expires_on" for temporary upgrades
4. Schedule monthly cost review with engineering team

Projected savings: $1,570/month ($18,840/year) by downgrading to appropriate tier
```

---

### Example 2.4: Security Incident Response (Cloud Security Domain)

```
USER: "AWS security alert: Unusual API calls from unknown IP - possible compromised credentials"

AGENT REASONING (ReACT Loop):

THOUGHT: Unusual API activity could indicate compromised IAM credentials, compromised instance, or misconfigured application. Need to investigate quickly and contain if confirmed.

PLAN:
1. Identify suspicious API calls and source
2. Check IAM user/role involved
3. Assess damage (what resources accessed/modified)
4. Contain threat (disable credentials if compromised)
5. Remediate and document

ACTION 1: Query CloudTrail for unusual activity
```python
cloudtrail_events = self.call_tool(
    tool_name="aws_cloudtrail_query",
    parameters={
        "time_range": "6h",
        "filter": "unusual_activity_detected",
        "source_ip": "203.0.113.45"  # From alert
    }
)
```

OBSERVATION:
- Source IP: 203.0.113.45 (Russia - not expected)
- IAM User: prod-deployment-user
- API Calls: ListBuckets, GetObject (S3), DescribeInstances (EC2), GetSecretValue (Secrets Manager)
- Total calls: 847 in 2 hours (vs normal: 10-20/hour)
- Pattern: Automated scanning/enumeration

REFLECTION: prod-deployment-user credentials likely compromised. High volume API calls from foreign IP indicate credential theft.

ACTION 2: Check what data was accessed
```python
s3_access = self.call_tool(
    tool_name="aws_cloudtrail_query",
    parameters={
        "event_name": "GetObject",
        "user_identity": "prod-deployment-user",
        "time_range": "6h"
    }
)
```

OBSERVATION:
- Accessed buckets: prod-backups, prod-logs, prod-customer-data
- Files accessed: database-backup-2024-10-10.sql (⚠️ contains customer data)
- Total files: 37 files accessed
- Data exfiltration: Likely (large GetObject calls)

REFLECTION: Confirmed data breach. Database backup with customer data was accessed. Need immediate containment.

ACTION 3: Disable compromised credentials
```python
disable_result = self.call_tool(
    tool_name="aws_iam_disable_user",
    parameters={
        "user_name": "prod-deployment-user",
        "reason": "Security incident - compromised credentials"
    }
)
```

OBSERVATION:
- User disabled: ✅
- API calls stopped: ✅ (no new calls in last 5 minutes)
- Threat contained: ✅

REFLECTION: Immediate threat contained. Now need to assess full impact and remediate.

ACTION 4: Check for persistence mechanisms
```python
persistence_check = self.call_tool(
    tool_name="aws_iam_list_access_keys",
    parameters={"user_name": "prod-deployment-user"}
)

backdoor_check = self.call_tool(
    tool_name="aws_iam_list_users",
    parameters={"created_after": "6h"}
)
```

OBSERVATION:
- Access keys: 1 active key (the compromised one, now disabled)
- New IAM users: None created
- New IAM roles: None created
- Backdoors: None detected ✅

REFLECTION: No persistence mechanisms found. Attacker only used stolen credentials, didn't create backdoors.

RESULT:
Security incident contained and resolved.

Timeline:
- T+0: Alert received (unusual API activity)
- T+10min: Investigation confirmed compromised credentials
- T+15min: Credentials disabled, threat contained
- T+30min: Full impact assessment complete

Impact Assessment:
- Compromised credentials: prod-deployment-user (IAM user)
- Data accessed: 37 files including database backup with customer data
- Data exfiltration: Confirmed (database backup downloaded)
- Customer impact: 5,000 customer records potentially exposed
- Persistence: None detected (no backdoors created)

Immediate Actions Taken:
1. ✅ Disabled compromised IAM user credentials
2. ✅ Revoked all active sessions for user
3. ✅ Blocked source IP at WAF level
4. ✅ Enabled S3 bucket versioning (recovery option)

Required Next Steps:
1. Incident response team notification (security team, legal, PR)
2. Customer notification (GDPR/breach notification requirements)
3. Forensic analysis of how credentials were compromised
4. Rotate all credentials for prod-deployment automation
5. Implement least-privilege IAM policies (current user had excessive permissions)
6. Enable AWS GuardDuty for automated threat detection
7. Setup CloudTrail alerting for unusual API patterns

Prevention Measures:
1. Use IAM roles with temporary credentials (not long-lived access keys)
2. Implement MFA for all IAM users
3. Enable AWS GuardDuty for continuous threat monitoring
4. Restrict S3 bucket access with bucket policies (least privilege)
5. Encrypt sensitive data at rest (customer data, backups)
6. Regular IAM access review (quarterly)

Incident Status: CONTAINED - Full remediation in progress
```

---

### Example 2.5: Kubernetes Pod CrashLoop Investigation (DevOps Domain)

```
USER: "Production pods in CrashLoopBackOff - application won't start"

AGENT REASONING (ReACT Loop):

THOUGHT: CrashLoopBackOff means containers starting then immediately crashing. Could be: application bug, misconfiguration, missing dependencies, resource constraints.

PLAN:
1. Check pod status and recent events
2. Review container logs for crash reason
3. Check configuration (env vars, secrets, configmaps)
4. Identify root cause
5. Implement fix

ACTION 1: Get pod status and events
```python
pod_status = self.call_tool(
    tool_name="kubectl_get_pods",
    parameters={
        "namespace": "production",
        "selector": "app=api-service",
        "include_events": True
    }
)
```

OBSERVATION:
- Pods: 3 replicas all in CrashLoopBackOff
- Restart count: 47, 52, 48 (restarting every ~30 seconds)
- Events: "Back-off restarting failed container"
- Last state: Terminated (Exit Code: 1)

REFLECTION: All pods crashing with exit code 1 (general error). Need to check logs for specific error message.

ACTION 2: Review container logs
```python
logs = self.call_tool(
    tool_name="kubectl_logs",
    parameters={
        "pod": "api-service-7d9f8b-abc12",
        "namespace": "production",
        "tail": 50
    }
)
```

OBSERVATION:
```
[2024-10-11 14:23:45] INFO: Starting API service...
[2024-10-11 14:23:46] INFO: Loading configuration...
[2024-10-11 14:23:46] ERROR: Failed to connect to database
[2024-10-11 14:23:46] ERROR: Connection string not found: DATABASE_URL
[2024-10-11 14:23:46] FATAL: Exiting due to configuration error
```

REFLECTION: Application can't find DATABASE_URL environment variable. This is a configuration issue, not an application bug.

ACTION 3: Check environment variables
```python
env_check = self.call_tool(
    tool_name="kubectl_get_deployment",
    parameters={
        "deployment_name": "api-service",
        "namespace": "production",
        "show_env": True
    }
)
```

OBSERVATION:
Environment variables in deployment:
- APP_NAME: api-service ✅
- LOG_LEVEL: info ✅
- PORT: 8080 ✅
- DATABASE_URL: (from secret "db-credentials") ⚠️

Secret reference found, need to check if secret exists.

REFLECTION: Deployment references secret "db-credentials" for DATABASE_URL, but secret might be missing or misconfigured.

ACTION 4: Check secret existence
```python
secret_check = self.call_tool(
    tool_name="kubectl_get_secret",
    parameters={
        "secret_name": "db-credentials",
        "namespace": "production"
    }
)
```

OBSERVATION:
Error: Secret "db-credentials" not found in namespace "production"

REFLECTION: Secret is missing! This is the root cause. Need to find if it was deleted or never created.

ACTION 5: Check recent changes
```python
history = self.call_tool(
    tool_name="kubectl_events",
    parameters={
        "namespace": "production",
        "resource_type": "Secret",
        "time_range": "24h"
    }
)
```

OBSERVATION:
- Event: Secret "db-credentials" deleted at 2024-10-11 14:15 UTC
- Deleted by: cleanup-job (automated secret rotation)
- No new secret created

REFLECTION: Automated secret rotation deleted old secret but didn't create new one. Rotation job failed midway.

RESULT:
Root cause identified: Secret "db-credentials" deleted by rotation job but new secret never created.

Immediate fix:
```bash
# Recreate secret with database connection string
kubectl create secret generic db-credentials \
  --from-literal=DATABASE_URL="postgresql://user:pass@db-host:5432/dbname" \
  --namespace=production
```

Validation:
- Pods automatically restarted after secret created
- All 3 replicas now Running (0 restarts)
- Application logs show successful database connection
- Health check: ✅ Passing

Timeline:
- T+0: Pods started crashing
- T+5min: Root cause identified (missing secret)
- T+7min: Secret recreated
- T+9min: All pods healthy

Post-Incident Actions:
1. Fix secret rotation job:
   - Add validation: Ensure new secret created before deleting old one
   - Add monitoring: Alert if secret deletion without creation
   - Add rollback: Keep old secret for 5 minutes during rotation

2. Add deployment safeguards:
   - InitContainer: Validate required secrets exist before starting app
   - Liveness probe: Delay 30 seconds (give time for secret resolution)

3. Documentation:
   - Create runbook for CrashLoopBackOff troubleshooting
   - Document secret rotation procedure

Prevention: Secret rotation job fixed to ensure zero-downtime secret updates
```

---

## Pattern Type 3: Handoff Decision Examples

### Generic Template
```
USER: "[Task requiring multiple specialized agents]"

AGENT REASONING:
- [Identify scope of this agent's capabilities]
- [Identify what requires different expertise]
- [Decide on handoff with clear reasoning]

HANDOFF DECLARATION:
To: [Target agent name]
Reason: [Why this agent is needed]
Context: [What work has been completed, what's needed next]
```

---

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

---

### Example 3.2: SRE Principal Engineer → DevOps Principal Architect

```
USER: "We need automated rollback for failed deployments based on error rate spike"

AGENT REASONING:
My scope (SRE Principal Engineer):
- ✅ Define reliability requirements (error rate thresholds, rollback criteria)
- ✅ Design monitoring and alerting strategy
- ✅ Define success metrics and SLO compliance

Outside my expertise:
- ❌ CI/CD pipeline implementation (GitLab/GitHub Actions)
- ❌ Deployment automation tooling (ArgoCD, Spinnaker)
- ❌ Infrastructure as Code (Terraform, Helm)

This task requires DevOps expertise for:
1. CI/CD pipeline integration for automated rollback
2. Canary deployment implementation
3. Progressive delivery tooling configuration

WORK COMPLETED (SRE):
- Defined rollback criteria:
  - Error rate >1% for 5 minutes → automatic rollback
  - P95 latency >500ms for 5 minutes → automatic rollback
  - Availability drops below 99% → automatic rollback
- Designed monitoring queries (Prometheus)
- Defined deployment safety policy

HANDOFF DECLARATION:
To: devops_principal_architect
Reason: CI/CD pipeline automation and progressive delivery implementation required
Context:
  - Rollback criteria defined and validated with stakeholders
  - Monitoring queries ready (Prometheus format)
  - Need automated rollback in deployment pipeline
  - Need canary deployment (5% → 25% → 50% → 100% traffic)
  - Integration required: GitLab CI + ArgoCD + Prometheus

Next steps (DevOps):
1. Implement automated rollback in CI/CD pipeline
2. Configure canary deployment stages
3. Integrate Prometheus alerts with rollback automation
4. Setup progressive delivery with automatic promotion/rollback
5. Test end-to-end deployment safety
```

---

### Example 3.3: DNS Specialist → Cloud Security Principal

```
USER: "Implement DNSSEC for all client domains (50 domains) with security audit"

AGENT REASONING:
My scope (DNS Specialist):
- ✅ DNS record management and configuration
- ✅ Basic DNS security (CAA records, subdomain protection)
- ✅ DNS provider configuration

Outside my expertise:
- ❌ DNSSEC cryptographic key management (key generation, rotation, HSM integration)
- ❌ Security audit and compliance validation
- ❌ Advanced DNS security threat analysis

This task requires Cloud Security expertise for:
1. DNSSEC key generation with proper cryptographic standards
2. Key management lifecycle and rotation procedures
3. Security audit of DNS infrastructure
4. Compliance validation (SOC2, ISO27001)

WORK COMPLETED (DNS):
- Audited all 50 client domains for DNSSEC readiness
- Verified DNS providers support DNSSEC (all on Route 53/Cloudflare)
- Documented current DNS security posture (CAA records, subdomain protection)
- Identified domains requiring DNSSEC for compliance (15 critical domains)

HANDOFF DECLARATION:
To: cloud_security_principal
Reason: DNSSEC cryptographic implementation and security audit required
Context:
  - 50 client domains need DNSSEC implementation
  - 15 domains are critical (require DNSSEC for compliance)
  - All domains on Route 53 (35) or Cloudflare (15)
  - Need cryptographic key generation (KSK/ZSK)
  - Need key rotation schedule and procedures
  - Need security audit of DNS infrastructure

Next steps (Cloud Security):
1. Design DNSSEC key management strategy (key sizes, rotation schedule)
2. Generate cryptographic keys for DNSSEC (KSK/ZSK)
3. Implement key rotation automation
4. Conduct security audit of DNS infrastructure
5. Validate compliance requirements (SOC2/ISO27001)
6. Hand back to DNS Specialist for zone signing and propagation
```

---

### Example 3.4: Service Desk Manager → SRE Principal Engineer

```
USER: "We're getting 20+ customer complaints per day about slow application performance - need systematic resolution"

AGENT REASONING:
My scope (Service Desk Manager):
- ✅ Customer complaint collection and analysis
- ✅ Pattern identification from support tickets
- ✅ Communication with customers
- ✅ Escalation coordination

Outside my expertise:
- ❌ Performance troubleshooting (latency analysis, bottleneck identification)
- ❌ System architecture optimization
- ❌ Monitoring and alerting infrastructure

This task requires SRE expertise for:
1. Performance analysis (identify bottlenecks)
2. System optimization recommendations
3. Proactive monitoring to catch issues before customers complain

WORK COMPLETED (Service Desk):
- Analyzed 87 customer complaints over last 7 days
- Identified patterns:
  - Peak complaint times: 2pm-4pm EST (business hours)
  - Affected features: Dashboard loading (45%), Report generation (32%), Search (23%)
  - Severity: Average wait time 8-15 seconds (was 2-3 seconds 2 weeks ago)
- Customer impact: 15% of active users affected
- Created ticket aggregation report

HANDOFF DECLARATION:
To: sre_principal_engineer
Reason: Performance analysis and system optimization required
Context:
  - 87 complaints analyzed (pattern: dashboard/reports/search slow)
  - Performance degraded 2 weeks ago (correlates with v2.4 deployment?)
  - Peak times: 2pm-4pm EST (high user load)
  - Affected users: 15% of active user base (~500 users)
  - Customer expectations: <3 seconds, currently 8-15 seconds

Next steps (SRE):
1. Analyze performance metrics (latency, throughput, error rate)
2. Identify bottlenecks (database, API, frontend)
3. Correlate with deployment history (v2.4 suspect)
4. Implement performance improvements
5. Setup proactive monitoring (alert before customers complain)
6. Hand back resolution for customer communication
```

---

### Example 3.5: DevOps Principal Architect → Principal Cloud Architect

```
USER: "Design multi-region disaster recovery for our critical payment processing system"

AGENT REASONING:
My scope (DevOps Principal Architect):
- ✅ CI/CD pipeline architecture
- ✅ Deployment automation and tooling
- ✅ Infrastructure as Code implementation

Outside my expertise:
- ❌ Multi-region architecture design (global load balancing, data replication)
- ❌ Business continuity planning (RPO/RTO requirements)
- ❌ Disaster recovery strategy and failover orchestration

This task requires Principal Cloud Architect expertise for:
1. Multi-region architecture design
2. Data replication and consistency strategy
3. Failover automation and testing procedures
4. RPO/RTO requirement analysis

WORK COMPLETED (DevOps):
- Current infrastructure documented (single region us-east-1)
- Infrastructure as Code: Terraform modules ready for multi-region deployment
- CI/CD pipeline: Can deploy to multiple regions
- Dependencies identified: Payment gateway, database, API services

HANDOFF DECLARATION:
To: principal_cloud_architect
Reason: Multi-region disaster recovery architecture design required
Context:
  - Critical system: Payment processing (99.99% availability required)
  - Current state: Single region (us-east-1) - no DR
  - Business requirements: RPO <5 minutes, RTO <15 minutes
  - IaC ready: Terraform modules can deploy to multiple regions
  - Dependencies: Stripe (payment gateway), PostgreSQL (database), Node.js APIs

Next steps (Principal Cloud Architect):
1. Design multi-region architecture (primary + DR regions)
2. Design data replication strategy (sync vs async, consistency model)
3. Design failover orchestration (automated vs manual)
4. Define testing procedures (quarterly DR drills)
5. Calculate cost impact (dual-region operation)
6. Hand back to DevOps for IaC implementation
```

---

## Pattern Type 4: Self-Critique Examples

### Generic Template
```
USER: "[Request requiring high-quality analysis]"

INITIAL ANALYSIS:
[First-pass analysis or recommendation]

SELF-CRITIQUE:
Wait - [Question own assumptions]
[Challenge own reasoning]
[Identify potential errors or oversights]

REVISED ANALYSIS:
[Corrected analysis incorporating critique]
[Higher confidence conclusion]
```

---

### Example 4.1: SLO Recommendation (SRE Domain)

```
USER: "Recommend SLO targets for our new customer API"

INITIAL ANALYSIS:
Based on industry standards, I recommend:
- Availability SLO: 99.99% (4 nines)
- Latency SLO: P99 < 100ms
- Error Rate SLO: < 0.01%

SELF-CRITIQUE:
Wait - these targets seem aspirational without considering current baseline. Let me challenge my assumptions:

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

REVISED ANALYSIS:
Based on actual baseline data (not just industry standards), here are achievable SLOs:

1. **Availability SLO: 99.9%** (not 99.99%)
   - Current: 99.5%
   - Target: 99.9% = 43.2 minutes downtime/month
   - Achievable: Yes, with improved monitoring and faster incident response
   - Investment: Moderate (better alerting, runbooks, on-call)
   - Justification: 10x improvement in allowed downtime (3.6h → 43min) is aggressive but realistic

2. **Latency SLO: P99 < 500ms** (not 100ms)
   - Current: 450ms
   - Target: 500ms = 10% improvement buffer
   - Alternative stretch goal: P95 < 300ms (more achievable)
   - Achievable: Yes, current performance already close
   - Investment: Low (some query optimization)

3. **Error Rate SLO: < 0.5%** (not 0.01%)
   - Current: 0.3%
   - Target: 0.5% = reasonable buffer for dependency errors
   - Achievable: Yes, with improved error handling
   - Investment: Low (better retry logic, circuit breakers)
   - Justification: Allows for upstream dependency failures (realistic)

CONFIDENCE:
- Initial recommendation: 40% (aspirational, not data-driven)
- Revised recommendation: 90% (based on actual metrics, achievable targets)

KEY LESSON: Always check baseline before setting SLOs. Aspirational targets without data lead to either feature freeze (too aggressive) or meaningless SLOs (too loose).
```

---

### Example 4.2: Azure Architecture Recommendation (Azure Solutions Architect Domain)

```
USER: "Should we use Azure SQL Database or Cosmos DB for our new e-commerce platform?"

INITIAL ANALYSIS:
For e-commerce, I recommend Cosmos DB because:
- Global distribution (fast reads worldwide)
- Unlimited scale (handle Black Friday traffic)
- High availability (99.999% SLA)
- NoSQL flexibility (schema changes easy)

SELF-CRITIQUE:
Wait - I'm recommending Cosmos DB based on buzzwords without understanding the actual requirements. Let me challenge this:

1. **Do they actually need global distribution?**
   - Question: Where are their customers located?
   - Issue: If 95% of customers are in US, global distribution is overkill
   - Cost: Cosmos DB multi-region is 3-5x more expensive than single-region

2. **Do they need unlimited scale?**
   - Question: What's their expected traffic? Current scale?
   - Issue: If they're doing 100 orders/day, they don't need Cosmos DB scale
   - Cost: Cosmos DB charges per RU/s (request units) - can get expensive fast

3. **Is NoSQL the right fit?**
   - Question: Do they have relational data? (customers, orders, products, inventory)
   - Issue: E-commerce is inherently relational (orders have line items, customers have addresses)
   - Complexity: NoSQL requires denormalization and data duplication

4. **What about transactions?**
   - Question: Do they need ACID transactions? (order processing, inventory management)
   - Issue: Cosmos DB has limited transaction support vs Azure SQL Database
   - Risk: Overselling inventory if no proper transaction support

Let me ask clarifying questions instead of jumping to recommendation...

QUESTIONS FOR USER:
1. What's your expected order volume? (orders per day/month)
2. Where are your customers located? (geographic distribution)
3. What's your current/projected scale? (users, transactions, data size)
4. Do you need ACID transactions? (critical for order processing)
5. What's your budget for database? (Cosmos DB can be 5-10x more expensive)

REVISED ANALYSIS:
I can't make a proper recommendation without understanding your requirements. Let me ask some clarifying questions:

**Scale Requirements**:
- Expected order volume?
- Projected growth over next 2 years?
- Current data size (if migrating from existing system)?

**Geographic Requirements**:
- Primary customer location(s)?
- Do you need multi-region for compliance/latency?

**Functional Requirements**:
- Need for ACID transactions? (critical for e-commerce)
- Query patterns? (complex joins vs simple key-value lookups)
- Reporting requirements? (analytics, dashboards)

**Non-Functional Requirements**:
- Budget constraints?
- Acceptable downtime? (RTO/RPO)
- Team expertise? (SQL vs NoSQL experience)

Once I understand your requirements, I can make a data-driven recommendation between:
- **Azure SQL Database**: Best for relational data, ACID transactions, complex queries, lower cost
- **Cosmos DB**: Best for global distribution, massive scale (millions of transactions/day), flexible schema

My hypothesis (pending validation): Most e-commerce platforms are better served by Azure SQL Database due to relational data model, transaction requirements, and lower cost. But I need your requirements to confirm.

CONFIDENCE:
- Initial recommendation: 30% (based on assumptions, not requirements)
- Revised approach: 95% (asking right questions before recommending)

KEY LESSON: Never recommend technology without understanding requirements. "It depends" is often the right answer until you have sufficient context.
```

---

### Example 4.3: DNS Migration Strategy (DNS Specialist Domain)

```
USER: "Plan DNS migration from GoDaddy to Route 53 for 50 client domains"

INITIAL ANALYSIS:
Here's the migration plan:
1. Weekend 1: Migrate 10 domains
2. Weekend 2: Migrate 20 domains
3. Weekend 3: Migrate 20 domains
4. Timeline: 3 weekends (21 days total)

SELF-CRITIQUE:
Wait - I'm assuming weekend migrations without checking if that's necessary or optimal. Let me challenge this plan:

1. **Do we actually need weekend migrations?**
   - Question: Can we migrate during business hours with zero downtime?
   - Issue: DNS migrations with proper TTL management are zero-downtime
   - Unnecessary constraint: Forcing weekend work if not needed

2. **Why batch migrations over 3 weekends?**
   - Question: What's the risk of migrating all 50 at once?
   - Issue: If we lower TTLs properly, migration risk is low
   - Inefficiency: 3 weekends of work vs 1 day with proper automation

3. **What about TTL preparation?**
   - Missing: Current TTLs might be 24 hours (slow failback if issues)
   - Risk: If migration has issues and TTL is high, rollback takes 24 hours
   - Critical: Need to lower TTLs first (2 weeks before migration)

4. **What about validation?**
   - Missing: Pre-migration validation checklist
   - Missing: Post-migration validation procedure
   - Risk: Silent failures (DNS records missing, DNSSEC broken)

Let me redesign this migration plan with proper risk management...

REVISED ANALYSIS:
Here's a proper zero-downtime DNS migration plan:

**WEEK -2: TTL Reduction Phase**
- Goal: Lower TTLs to enable fast rollback
- Action: Reduce all TTL values to 300 seconds (5 minutes)
- Timeline: Monday of week -2
- Wait period: 7 days (allow old TTL to expire globally)
- Why: If migration has issues, only 5 minutes to rollback vs 24 hours

**WEEK -1: Preparation Phase**
- Export all DNS records from GoDaddy (automated script)
- Create Route 53 hosted zones (automated via Terraform)
- Import DNS records to Route 53 (automated)
- Validate record parity: GoDaddy vs Route 53 (automated diff)
- Identify critical services per domain (MX, web, API)
- Create monitoring: DNS resolution checks per domain
- Test migration procedure with 2 test domains

**WEEK 0: Migration Execution**
- Monday 9am: Migrate Batch 1 (10 non-critical domains)
  - Update NS records at registrar
  - Monitor for 1 hour
  - Validate resolution from multiple locations
  - If successful: Proceed
  - If issues: Rollback (5 min TTL allows fast recovery)

- Monday 11am: Migrate Batch 2 (20 medium-priority domains)
  - Same procedure with 2-hour monitoring gap

- Tuesday 9am: Migrate Batch 3 (15 domains including critical)
  - Same procedure with extended monitoring

- Wednesday 9am: Migrate Batch 4 (5 most critical domains)
  - Extra validation steps
  - Full team on standby

- Why business hours? Zero-downtime migration doesn't require weekends, allows full team availability for monitoring

**WEEK +1: TTL Restoration**
- Monday: Restore TTLs to normal values (1 hour to 24 hours)
- Decommission GoDaddy DNS after 7-day grace period
- Cost savings: $X/month by moving to Route 53

**KEY DIFFERENCES FROM INITIAL PLAN**:
1. ✅ Business hours migration (not weekends) - zero downtime achieved through proper TTL management
2. ✅ 4 days instead of 3 weekends - more efficient
3. ✅ Automated validation - catch issues early
4. ✅ Gradual batch approach - de-risk with non-critical first
5. ✅ Proper TTL lifecycle - enable fast rollback

**RISK MITIGATION**:
- Low TTLs (5 min) = fast rollback if issues
- Batch approach = contain blast radius
- Business hours = full team available
- Monitoring = immediate issue detection
- Test domains = validate procedure before production

CONFIDENCE:
- Initial plan: 50% (risky assumptions, missing critical steps)
- Revised plan: 95% (comprehensive risk management, proven methodology)

KEY LESSON: DNS migrations don't require weekend downtime if planned properly. Proper TTL management + automation + monitoring = zero-downtime business-hours migration.
```

---

### Example 4.4: Cost Optimization Recommendation (FinOps Domain)

```
USER: "Our Azure bill is $50K/month - help us save 30%"

INITIAL ANALYSIS:
To save 30% ($15K/month), I recommend:
1. Purchase Reserved Instances for VMs (save 40%)
2. Move to Spot VMs where possible (save 80%)
3. Rightsize over-provisioned resources (save 20%)
4. Delete unused resources (immediate savings)

Expected savings: $15K-20K/month

SELF-CRITIQUE:
Wait - I'm providing generic cost optimization recommendations without analyzing actual spending. Let me challenge this approach:

1. **Do we know where the $50K is actually going?**
   - Missing: Cost breakdown by service (compute, storage, networking, database)
   - Issue: Can't prioritize optimization without knowing top cost drivers
   - Risk: Optimizing wrong areas (80/20 rule - focus on top 20% of costs)

2. **Are Reserved Instances actually the right fit?**
   - Question: Do they have stable workloads? (RIs only save money if utilization is >75%)
   - Question: What's their commitment timeline? (1-year vs 3-year)
   - Risk: RI commitment without proper analysis could increase costs if workloads change

3. **Are Spot VMs feasible?**
   - Question: Can their workloads tolerate interruption? (Spot VMs can be evicted)
   - Issue: Spot VMs inappropriate for production databases, stateful apps
   - Risk: Service disruption if Spot VMs used incorrectly

4. **What about business requirements?**
   - Missing: Performance requirements, availability SLAs, compliance needs
   - Risk: Cost optimization that breaks SLAs is not actually savings

Let me request proper data before making recommendations...

QUESTIONS FOR USER:
1. Can you share Azure Cost Analysis breakdown by service?
2. What are your top 5 cost drivers? (services spending most)
3. What are your workload characteristics? (steady-state vs variable)
4. What are your SLA requirements? (can't sacrifice reliability for cost)
5. What's your commitment timeline? (affects RI recommendations)

REVISED ANALYSIS:
I need more information to provide actionable cost optimization recommendations. Here's what I need:

**Cost Analysis Required**:
```
Please provide:
1. Azure Cost Analysis export (last 3 months)
   - Breakdown by service
   - Breakdown by resource group
   - Breakdown by tag (if tagged properly)

2. Top 10 most expensive resources
   - Resource name, type, monthly cost

3. Workload characteristics
   - Which workloads are steady-state (24/7)?
   - Which are variable (batch jobs, dev/test)?
   - Which are production (cannot tolerate downtime)?
```

**Once I have this data, I can recommend:**

**High-Impact Optimizations** (likely to achieve 30% savings):
1. **Compute Optimization**:
   - Reserved Instances for steady-state VMs (30-40% savings)
   - Spot VMs for fault-tolerant workloads (60-80% savings)
   - Rightsize over-provisioned VMs (20-40% savings)
   - Auto-shutdown for dev/test VMs (70% savings on dev/test)

2. **Storage Optimization**:
   - Lifecycle management (move old data to cool/archive tiers, 50-90% savings)
   - Delete orphaned disks and snapshots (immediate savings)
   - Enable compression where applicable

3. **Database Optimization**:
   - Rightsize database SKUs based on actual usage
   - Reserved capacity for steady-state databases (30-40% savings)
   - Serverless options for variable workloads

4. **Networking Optimization**:
   - Review data egress patterns (expensive at scale)
   - Optimize inter-region traffic
   - CDN for static content (reduce bandwidth costs)

**Quick Wins** (can implement immediately):
1. Delete unused resources (find resources with 0% utilization)
2. Auto-shutdown dev/test VMs (off during nights/weekends)
3. Enable Azure Hybrid Benefit (if you have Windows licenses)
4. Review Log Analytics retention (expensive if over-retained)

**Methodology**:
1. Analyze cost breakdown (identify top 80% of costs)
2. Categorize by optimization potential (high/medium/low)
3. Prioritize by business impact (don't break SLAs)
4. Implement quick wins first (prove value)
5. Plan longer-term optimizations (RIs, architecture changes)

CONFIDENCE:
- Initial recommendation: 40% (generic advice without data)
- Revised approach: 90% (data-driven methodology)

KEY LESSON: Cost optimization requires data analysis first. Generic recommendations ("buy RIs, use Spot VMs") are useless without understanding actual spending patterns and workload characteristics.
```

---

### Example 4.5: Security Architecture Decision (Cloud Security Domain)

```
USER: "Should we implement Zero Trust architecture for our cloud infrastructure?"

INITIAL ANALYSIS:
Yes, you should implement Zero Trust because:
- Zero Trust is industry best practice
- Eliminates implicit trust (assume breach)
- Improves security posture significantly
- Required for modern cloud security

Recommendation: Implement full Zero Trust architecture immediately.

SELF-CRITIQUE:
Wait - I'm recommending a major architecture change based on buzzwords without understanding their current state, requirements, or constraints. Let me challenge this:

1. **What's their current security posture?**
   - Question: Do they have basic security controls in place? (IAM, network segmentation, encryption)
   - Issue: If basic security is missing, Zero Trust is premature
   - Analogy: Like recommending a race car to someone who doesn't have a driver's license

2. **What does "Zero Trust" actually mean for them?**
   - Issue: Zero Trust is a philosophy, not a product
   - Question: What specific implementations? (identity-based access, micro-segmentation, continuous verification)
   - Complexity: Full Zero Trust implementation is 12-24 month project

3. **What are their actual security requirements?**
   - Missing: Compliance requirements (SOC2, ISO27001, HIPAA)
   - Missing: Threat model (what are they protecting against?)
   - Missing: Risk assessment (what's their actual risk exposure?)

4. **What are their constraints?**
   - Missing: Budget (Zero Trust tools can be expensive)
   - Missing: Team expertise (requires specialized security knowledge)
   - Missing: Timeline (how urgent is this?)
   - Missing: Business impact tolerance (can they handle implementation disruption?)

5. **Is this the right priority?**
   - Question: Are there more pressing security gaps?
   - Question: What's their security maturity level?
   - Risk: Implementing advanced security while basic controls are missing

Let me reframe this with proper security consulting approach...

REVISED ANALYSIS:
I can't recommend for or against Zero Trust without understanding your current security posture and requirements. Instead, let me help you make an informed decision:

**First, let's assess your current state:**

1. **Security Maturity Assessment**:
   - Do you have basic IAM controls? (MFA, least privilege, role-based access)
   - Do you have network segmentation? (VPCs, subnets, security groups)
   - Do you have encryption at rest and in transit?
   - Do you have centralized logging and monitoring?
   - Do you have incident response procedures?

2. **Compliance Requirements**:
   - What compliance frameworks apply? (SOC2, ISO27001, HIPAA, PCI-DSS)
   - What specific security controls are required?
   - What's your timeline for compliance?

3. **Threat Model**:
   - What are your primary security concerns? (data breach, ransomware, insider threat)
   - What's your risk appetite? (high-security/low-risk vs balanced)
   - Have you had security incidents? (what type?)

4. **Constraints**:
   - Security budget? (Zero Trust tools: $50K-500K+)
   - Team size and expertise? (need security specialists)
   - Implementation timeline? (12-24 months for full Zero Trust)
   - Tolerance for operational disruption?

**Then, let's determine if Zero Trust is the right approach:**

**Zero Trust is a good fit if:**
- ✅ You have basic security controls in place (foundation exists)
- ✅ You handle sensitive data (PII, financial, healthcare)
- ✅ You have compliance requirements demanding strong access controls
- ✅ You have budget and expertise for implementation
- ✅ You're willing to commit to 12-24 month transformation
- ✅ You have executive sponsorship (organizational change required)

**Zero Trust may NOT be the right priority if:**
- ❌ Basic security controls missing (fix foundation first)
- ❌ Limited budget (focus on high-impact quick wins)
- ❌ Small team without security expertise (too complex to manage)
- ❌ Need security improvements in 3-6 months (Zero Trust takes longer)
- ❌ Low risk environment (cost/benefit doesn't justify)

**Alternative Approach - Incremental Security Improvement:**
If full Zero Trust is too ambitious right now, consider incremental improvements:

**Phase 1 (0-3 months): Security Fundamentals**
1. Implement MFA for all users (critical)
2. Enable encryption at rest and in transit
3. Network segmentation (separate production/dev/test)
4. Centralized logging (SIEM or log aggregation)
5. Vulnerability scanning and patching

**Phase 2 (3-6 months): Identity and Access**
6. Implement least privilege access (role-based)
7. Just-in-time access (temporary elevation)
8. Regular access reviews (quarterly)
9. Service accounts with rotation

**Phase 3 (6-12 months): Zero Trust Principles**
10. Identity-based access (replace IP-based)
11. Micro-segmentation (application-level controls)
12. Continuous verification (don't trust, verify)
13. Assume breach (detection + response over prevention)

**Phase 4 (12-24 months): Full Zero Trust**
14. Software-defined perimeter
15. End-to-end encryption
16. Advanced threat detection
17. Automated response

**My Recommendation** (once I have your context):
- If you're at Phase 1 maturity → Focus on fundamentals first
- If you're at Phase 2 maturity → Consider Zero Trust principles (Phase 3)
- If you're at Phase 3 maturity → Full Zero Trust makes sense (Phase 4)

CONFIDENCE:
- Initial recommendation: 20% (recommending major architecture change without context)
- Revised approach: 95% (proper security assessment methodology)

KEY LESSON: Security recommendations require context. "Implement Zero Trust" is like "lose weight" - sounds good but meaningless without understanding current state, goals, and constraints. Proper security consulting starts with assessment, not recommendations.
```

---

## Usage Guidelines

### When to Use Each Pattern Type

**Tool-Calling Examples** (Pattern Type 1):
- Use when: Demonstrating correct tool usage
- Avoid when: Complex multi-step reasoning required (use ReACT instead)
- Best for: Straightforward queries, validation tasks, data retrieval

**ReACT Pattern Examples** (Pattern Type 2):
- Use when: Complex troubleshooting, incident response, root cause analysis
- Avoid when: Simple queries with clear answers
- Best for: Production incidents, performance issues, multi-step investigations

**Handoff Decision Examples** (Pattern Type 3):
- Use when: Task requires expertise outside agent's domain
- Avoid when: Agent can complete task independently
- Best for: Cross-functional workflows, specialized expertise needs, clear responsibility boundaries

**Self-Critique Examples** (Pattern Type 4):
- Use when: High-stakes decisions, recommendations with significant impact, quality-critical outputs
- Avoid when: Simple factual queries
- Best for: Architecture decisions, cost optimization, security recommendations, SLO design

### Integration with Agent Prompts

**In Agent Definitions**:
1. Reference specific examples from this library
2. Customize examples with domain-specific details
3. Include 2+ examples per key command (mix pattern types)

**Example Integration**:
```markdown
### `email_authentication_implementation`

**Purpose**: Implement SPF/DKIM/DMARC authentication

**Few-Shot Examples:**

**Example 1: MSP Client Onboarding** (Tool-Calling Pattern)
[See Example 1.1 from Tool-Calling section, customized for email auth]

**Example 2: Email Deliverability Crisis** (ReACT Pattern)
[See Example 2.2 from ReACT section]
```

### Example Selection Criteria

Choose examples based on:
1. **Agent Domain**: Match examples to agent's specialty (DNS examples for DNS agent)
2. **Task Complexity**: Simple tasks → Tool-Calling, Complex tasks → ReACT
3. **Collaboration Needs**: Multi-agent workflows → Handoff examples
4. **Decision Quality**: High-stakes decisions → Self-Critique examples

---

## Maintenance & Evolution

### Adding New Examples

When creating new examples:
1. Follow generic template for pattern type
2. Use realistic user queries
3. Show complete problem-solving (not partial)
4. Include validation and results
5. Add to appropriate pattern type section

### Example Quality Checklist

Each example should have:
- [ ] Realistic user query
- [ ] Clear agent reasoning
- [ ] Proper tool usage (if applicable)
- [ ] Complete resolution (not partial)
- [ ] Validation performed
- [ ] Measurable outcome
- [ ] Domain-specific details

---

## End of Few-Shot Example Library

**Total Examples**: 20 (5 per pattern type)
**Status**: Production-ready for Phase 107 agent upgrades
**Next Steps**: Integrate examples into agent prompt updates (Tasks 1.5-1.9)
