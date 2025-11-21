# Email Capture Strategy for Executive Information Manager

## Current Email Corpus Analysis

**Total Emails**: 313 emails indexed in Email RAG
**Composition**: Primarily meeting invitations, acceptances, and calendar notifications

## What Should Be Captured from Email

### 1. **Direct Action Requests**
Emails where someone explicitly asks you to do something:
- "Can you..."
- "Please..."
- "Need you to..."
- "Could you help with..."
- "Would you mind..."

**Priority**: HIGH (Tier 2)
**Time Sensitivity**: Based on email context (urgent/week/month)

### 2. **Questions Requiring Response**
Emails with questions directed at you:
- Ending with "?"
- "What do you think about..."
- "How should we..."
- "When can you..."

**Priority**: MEDIUM-HIGH (Tier 2-3)
**Time Sensitivity**: week (unless marked urgent)

### 3. **Follow-up Items**
Emails indicating pending actions:
- "Following up on..."
- "Just checking in on..."
- "Status update on..."
- "Any progress on..."

**Priority**: MEDIUM (Tier 3)
**Time Sensitivity**: week

### 4. **Decision Requests**
Emails requiring approval or decision:
- "Need approval for..."
- "Decision needed on..."
- "Please review and approve..."
- "Sign off on..."

**Priority**: HIGH (Tier 2)
**Decision Impact**: high
**Time Sensitivity**: week

### 5. **Escalations**
Emails indicating issues or problems:
- Subject contains: "Issue", "Problem", "Escalation", "Urgent", "ASAP"
- From: Clients or executive stakeholders
- "Need immediate..."

**Priority**: CRITICAL (Tier 1)
**Time Sensitivity**: urgent

### 6. **Commitments Made**
Emails where YOU committed to do something:
- Sent emails containing: "I will...", "I'll...", "I can..."
- Your responses to action requests

**Priority**: HIGH (Tier 2)
**Time Sensitivity**: Based on your commitment

### 7. **External Stakeholders**
Emails from:
- Clients (non-@orro.group domains)
- Vendors
- Partners
- Board members

**Priority**: MEDIUM-HIGH (Tier 2-3)
**Stakeholder Importance**: client/executive

## What Should NOT Be Captured

1. **Meeting Acceptances/Declines**
   - Subject starts with "Accepted:", "Declined:", "Tentative:"
   - No action required

2. **Calendar Notifications**
   - Auto-generated calendar reminders
   - No action beyond attending

3. **Auto-Replies**
   - "Out of office"
   - "Automatic reply:"
   - No action possible

4. **FYI/CC Emails**
   - You're CC'd (not in To: field)
   - Purely informational
   - No action requested

5. **Email Threads You've Already Responded To**
   - Check if you've already replied
   - Thread is closed

## Recommended Capture Criteria

### Tier 1 (Critical - Capture Immediately)
- Subject contains: "urgent", "asap", "critical", "escalation", "emergency"
- From: CEO, Board members, Major clients
- Body contains: "immediate action", "today", "ASAP"

### Tier 2 (High Priority - Capture Daily)
- Direct questions to you (contains "?" and you're in To: field)
- Action requests ("can you", "please", "need you to")
- Decision requests ("approval", "sign off", "review")
- External stakeholders (non-@orro.group)
- Emails with "decision", "approval", "review" in subject

### Tier 3 (Medium Priority - Capture Weekly)
- Follow-up emails
- Status requests
- Internal requests from team members
- Meeting prep materials (not just acceptances)

## Implementation Strategy

### Option 1: Keyword-Based Filtering (Current Approach)
**Pros**: Simple, fast
**Cons**: Misses context, many false positives

### Option 2: Semantic Understanding (Recommended)
Search for semantic concepts:
- "action items assigned to Naythan"
- "questions waiting for Naythan's response"
- "decisions pending Naythan's approval"
- "urgent matters requiring immediate attention"
- "external stakeholders waiting for response"

### Option 3: Hybrid Approach (Best)
1. **Keyword pre-filter**: Exclude auto-replies, acceptances
2. **Semantic search**: Find actionable content
3. **Relevance threshold**: Only capture relevance > 0.6
4. **Recency filter**: Last 7 days only
5. **Sender importance**: Weight by stakeholder tier

## Proposed Auto-Capture Logic

```python
def should_capture_email(email):
    # Exclude noise
    if email['subject'].startswith(('Accepted:', 'Automatic reply:', 'Canceled:')):
        return False

    # Check recency (last 7 days)
    if days_since(email['date']) > 7:
        return False

    # Tier 1: Urgent/Critical
    if any(word in email['subject'].lower() for word in ['urgent', 'asap', 'critical']):
        return True, 'tier1'

    # Tier 2: Action requests
    if email['relevance'] > 0.6 and contains_action_request(email['body']):
        return True, 'tier2'

    # Tier 2: External stakeholders
    if not email['sender'].endswith('@orro.group'):
        return True, 'tier2'

    # Tier 2: Decision requests
    if any(word in email['subject'].lower() for word in ['approval', 'decision', 'review', 'sign off']):
        return True, 'tier2'

    # Tier 3: Questions
    if '?' in email['body'] and email['relevance'] > 0.5:
        return True, 'tier3'

    return False, None
```

## Metrics to Track

1. **Capture Rate**: % of emails captured
2. **False Positive Rate**: % of captured emails with no real action
3. **Missed Items**: Critical emails not captured (manual review)
4. **Processing Time**: Time to review captured items
5. **Action Completion**: % of captured items actually actioned

## Next Steps

1. Implement hybrid capture logic
2. Test on last 7 days of emails
3. Review captured items for false positives
4. Refine criteria based on feedback
5. Set up daily capture with quality metrics
