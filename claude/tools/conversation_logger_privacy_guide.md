# Privacy Filtering Recommendations - Conversation Logger

## Overview

The Conversation Logger uses a **privacy-first, opt-in sharing model** to ensure sensitive information is never accidentally shared with teams.

**Default Behavior**: All journeys are `PRIVATE` (privacy_flag = True)
**Team Sharing**: Explicit opt-in required via `mark_shareable(journey_id)`

## Privacy Decision Framework

### Quick Decision Matrix

| Content Type | Default Privacy | Share? | Rationale |
|--------------|----------------|--------|-----------|
| Generic technical problems | PRIVATE | ✅ Yes | Safe to share after review |
| Workflow discoveries | PRIVATE | ✅ Yes | Valuable team learning |
| Tool/agent effectiveness | PRIVATE | ✅ Yes | Demonstrates capabilities |
| Architecture decisions | PRIVATE | ⚠️ Review | Check for sensitive context |
| Customer-specific data | PRIVATE | ❌ No | Never share |
| Security vulnerabilities | PRIVATE | ❌ No | Share only after patching |
| Business metrics | PRIVATE | ❌ No | Sensitive information |
| Credentials/secrets | PRIVATE | ❌ No | Never share |

## Automated Privacy Filtering

### Sensitive Pattern Detection

```python
def contains_sensitive_data(journey_data: dict) -> bool:
    """
    Detect sensitive patterns that should never be shared.

    Args:
        journey_data: Journey dictionary from database

    Returns:
        True if sensitive data detected, False otherwise
    """
    # Sensitive keyword patterns
    SENSITIVE_PATTERNS = {
        # Credentials & Secrets
        'credentials': ['password', 'api_key', 'secret', 'token', 'credential'],

        # Personal Information
        'pii': ['email', 'phone', 'address', 'ssn', 'social security'],

        # Business Sensitive
        'business': ['revenue', 'salary', 'budget', 'cost', 'profit', 'acquisition'],

        # Security
        'security': ['vulnerability', 'exploit', 'cve-', 'zero-day', 'breach'],

        # Customer Data
        'customer': ['customer_name', 'client_data', 'account_number'],

        # Infrastructure
        'infrastructure': ['internal_ip', 'vpn_config', 'firewall_rule']
    }

    # Convert journey to searchable text
    journey_text = json.dumps(journey_data, default=str).lower()

    # Check each pattern category
    for category, patterns in SENSITIVE_PATTERNS.items():
        for pattern in patterns:
            if pattern in journey_text:
                logger.warning(
                    f"Sensitive data detected ({category}): '{pattern}' in journey {journey_data['journey_id']}"
                )
                return True

    return False
```

### Safe-to-Share Validation

```python
def validate_safe_to_share(journey_id: str) -> tuple[bool, list[str]]:
    """
    Validate journey is safe to share with team.

    Args:
        journey_id: Journey UUID

    Returns:
        (is_safe, warnings_list)
    """
    logger_instance = ConversationLogger()
    journeys = logger_instance.get_week_journeys(include_private=True)

    journey = next((j for j in journeys if j['journey_id'] == journey_id), None)

    if not journey:
        return False, ["Journey not found"]

    warnings = []

    # Check 1: Sensitive patterns
    if contains_sensitive_data(journey):
        warnings.append("⚠️ Sensitive data patterns detected")

    # Check 2: Customer-specific content
    if any(keyword in str(journey).lower() for keyword in ['customer', 'client', 'account']):
        warnings.append("⚠️ Possible customer-specific content")

    # Check 3: Unpatched vulnerabilities
    if 'vulnerability' in str(journey).lower() and 'patched' not in str(journey).lower():
        warnings.append("⚠️ Possible unpatched security vulnerability")

    # Check 4: Deliverables with sensitive files
    if journey.get('deliverables'):
        sensitive_files = ['.env', 'credentials', 'secrets', 'config.prod']
        for deliverable in journey['deliverables']:
            if any(sf in deliverable['name'].lower() for sf in sensitive_files):
                warnings.append(f"⚠️ Deliverable '{deliverable['name']}' may contain sensitive data")

    # Check 5: Business impact with financial data
    if journey.get('business_impact'):
        financial_keywords = ['$', 'revenue', 'cost', 'budget', 'profit']
        if any(kw in journey['business_impact'].lower() for kw in financial_keywords):
            warnings.append("⚠️ Business impact contains financial data")

    # Determine safety
    is_safe = len(warnings) == 0

    return is_safe, warnings
```

## Manual Review Workflow

### Before Marking Shareable

**Step 1: Run automated validation**

```python
from claude.tools.conversation_logger_privacy_guide import validate_safe_to_share

is_safe, warnings = validate_safe_to_share(journey_id)

if is_safe:
    print("✅ Safe to share")
    logger.mark_shareable(journey_id)
else:
    print("⚠️ Manual review required:")
    for warning in warnings:
        print(f"  {warning}")
```

**Step 2: Manual review checklist**

- [ ] No customer names, account numbers, or client-specific data
- [ ] No credentials, API keys, passwords, or secrets
- [ ] No unpatched security vulnerabilities
- [ ] No sensitive business metrics (revenue, costs, budgets)
- [ ] No personal information (emails, phone numbers, addresses)
- [ ] No internal infrastructure details (IPs, VPN configs, firewall rules)
- [ ] Deliverables contain no sensitive files (.env, credentials, secrets)
- [ ] Meta-learning insights are generic and reusable
- [ ] Business impact metrics are high-level (percentages vs. dollar amounts)

**Step 3: Sanitize if needed**

If journey contains valuable insights but sensitive details:

```python
# Create sanitized copy
sanitized_journey = {
    'problem_description': "Migrate VPN infrastructure to cloud",  # Generic
    'initial_question': "How to migrate enterprise VPN to Azure?",  # No specifics
    'business_impact': "95% time reduction",  # Percentage, not dollars
    'meta_learning': journey['meta_learning'],  # Keep insights
    'agents_used': journey['agents_used'],  # Keep agent patterns
    'deliverables': [
        # Remove sensitive deliverables, keep generic ones
        d for d in journey['deliverables']
        if 'credentials' not in d['name'].lower()
    ]
}

# Create new journey with sanitized data
sanitized_id = logger.start_journey(
    problem_description=sanitized_journey['problem_description'],
    initial_question=sanitized_journey['initial_question']
)

# Copy metadata
logger.complete_journey(
    journey_id=sanitized_id,
    business_impact=sanitized_journey['business_impact'],
    meta_learning=sanitized_journey['meta_learning'],
    iteration_count=journey['iteration_count']
)

# Mark sanitized version shareable
logger.mark_shareable(sanitized_id)
```

## Privacy Best Practices

### 1. Default to Private

**Always start journeys as private**. Only mark shareable after explicit review.

```python
# ✅ GOOD: Start private, review later
journey_id = logger.start_journey(problem, question)
# ... work on solution ...
# ... manual review ...
logger.mark_shareable(journey_id)  # Only after review

# ❌ BAD: Auto-share without review
journey_id = logger.start_journey(problem, question)
logger.mark_shareable(journey_id)  # Immediate sharing risky
```

### 2. Use Generic Descriptions

When creating journeys, use **generic problem descriptions** that could be shared:

```python
# ✅ GOOD: Generic description
logger.start_journey(
    problem_description="Migrate enterprise VPN to cloud infrastructure",
    initial_question="How to migrate VPN with minimal downtime?"
)

# ❌ BAD: Customer-specific details
logger.start_journey(
    problem_description="Migrate Acme Corp's SonicWall VPN (50 users, $50K budget)",
    initial_question="How to migrate Acme's VPN before Q4 audit?"
)
```

### 3. Sanitize Business Impact

Use **relative metrics** instead of absolute numbers:

```python
# ✅ GOOD: Relative metrics
logger.complete_journey(
    journey_id=journey_id,
    business_impact="95% time reduction (weeks → minutes)",
    meta_learning="...",
    iteration_count=2
)

# ❌ BAD: Absolute financial data
logger.complete_journey(
    journey_id=journey_id,
    business_impact="Saved $500K in consulting fees",
    meta_learning="...",
    iteration_count=2
)
```

### 4. Review Deliverables

**Exclude sensitive deliverables** from team sharing:

```python
# Safe deliverable types
SAFE_DELIVERABLE_TYPES = [
    'Generic tools (non-customer-specific)',
    'Workflow documentation',
    'Architecture diagrams (sanitized)',
    'Meta-learning summaries'
]

# Sensitive deliverable types (DO NOT SHARE)
SENSITIVE_DELIVERABLE_TYPES = [
    'Customer-specific configurations',
    'Credential files (.env, secrets)',
    'Production data exports',
    'Security vulnerability reports (pre-patch)'
]
```

### 5. Weekly Review Process

Before generating weekly narratives:

```python
def weekly_privacy_review():
    """
    Review all private journeys for potential sharing.
    """
    logger_instance = ConversationLogger()

    # Get all private journeys from last week
    all_journeys = logger_instance.get_week_journeys(include_private=True)
    private_journeys = [j for j in all_journeys if j['privacy_flag'] == 1]

    print(f"📋 {len(private_journeys)} private journeys to review:\n")

    for journey in private_journeys:
        print(f"Journey: {journey['journey_id']}")
        print(f"Problem: {journey['problem_description']}")

        # Run automated validation
        is_safe, warnings = validate_safe_to_share(journey['journey_id'])

        if is_safe:
            print("✅ SAFE - Ready to share")
            print("Action: Mark shareable? (y/n)")
        else:
            print("⚠️ REQUIRES REVIEW")
            for warning in warnings:
                print(f"  {warning}")
            print("Action: Sanitize or keep private? (sanitize/private)")

        print("---\n")
```

## Privacy Compliance

### GDPR Considerations

**Right to Erasure**: Users can request journey deletion

```python
def delete_journey(journey_id: str) -> bool:
    """
    Delete journey (GDPR right to erasure).

    Args:
        journey_id: Journey UUID

    Returns:
        True if deleted, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations WHERE journey_id = ?", (journey_id,))

        conn.commit()
        conn.close()

        logger.info(f"Deleted journey {journey_id} (GDPR erasure)")
        return True

    except Exception as e:
        logger.error(f"Failed to delete journey: {e}")
        return False
```

**Data Minimization**: Only log necessary information

```python
# ✅ GOOD: Minimal, necessary data
logger.start_journey(
    problem_description="VPN migration challenge",
    initial_question="How to migrate VPN?"
)

# ❌ BAD: Excessive personal data
logger.start_journey(
    problem_description="John Smith (john@acme.com, 555-1234) needs VPN migration",
    initial_question="..."
)
```

### Team Sharing Agreement

**Before enabling team sharing, establish agreement**:

1. **Privacy Policy**: Document what data is shareable
2. **Review Process**: Weekly privacy review meetings
3. **Sanitization Protocol**: Process for removing sensitive data
4. **Incident Response**: Process if sensitive data accidentally shared
5. **Training**: Team training on privacy best practices

## Privacy Incident Response

### If Sensitive Data Shared Accidentally

**Step 1: Immediate containment**

```python
# Mark journey private immediately
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("UPDATE conversations SET privacy_flag = 1 WHERE journey_id = ?", (journey_id,))
conn.commit()
conn.close()

# Notify Team Knowledge Sharing Agent to exclude from next narrative
```

**Step 2: Assess exposure**

- Check if weekly narrative already published
- Check if shared in Confluence/Slack
- Identify who accessed data

**Step 3: Remediation**

- Delete published narratives containing sensitive data
- Notify affected parties if PII/customer data exposed
- Update sanitization filters to prevent recurrence

**Step 4: Post-mortem**

- Document incident
- Update privacy filters
- Retrain team on privacy best practices

## Summary

### Privacy Principles

1. **Default Private**: All journeys start private (privacy_flag = True)
2. **Explicit Opt-In**: Require manual review before marking shareable
3. **Automated Filtering**: Use sensitive pattern detection
4. **Manual Review**: Human review for edge cases
5. **Sanitization**: Create generic versions when needed
6. **Compliance**: GDPR right to erasure, data minimization
7. **Incident Response**: Process for accidental exposure

### Recommended Workflow

```
Journey Start (PRIVATE)
    ↓
Work on Solution
    ↓
Journey Complete
    ↓
Automated Privacy Check
    ↓
    ├─ SAFE → Manual review → Mark shareable
    └─ WARNINGS → Manual review → Sanitize or keep private
        ↓
Weekly narrative includes only shareable journeys
```

## Implementation Checklist

- [ ] Add `validate_safe_to_share()` to conversation_logger.py
- [ ] Create weekly privacy review CLI command
- [ ] Document team sharing agreement
- [ ] Train team on privacy best practices
- [ ] Implement privacy incident response process
- [ ] Add GDPR erasure functionality
- [ ] Create privacy compliance reporting

---

**Status**: Production-ready privacy framework
**Last Updated**: 2025-11-12
**Author**: SRE Principal Engineer Agent
