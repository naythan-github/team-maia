# Email Action Tracker - Requirements Specification

**Version**: 1.0
**Date**: 2025-11-21
**Status**: Requirements Complete ✅
**TDD Protocol**: Phase 1 Complete

---

## Problem Statement

Users receive action items via email but have no systematic way to track what's pending, what's been completed via replies, what's overdue, and what they're waiting for from others. This leads to:
- Missed commitments
- Dropped follow-ups
- Poor visibility of pending work
- Manual effort to track email-based tasks

---

## Success Criteria

1. **Zero Missed Actions**: 100% capture of action items from emails
2. **Automatic Detection**: Status updates via reply analysis (no manual input required for 80%+ cases)
3. **Clear Visibility**: Dashboard showing OVERDUE/TODAY/PENDING/WAITING at a glance
4. **Relationship Health**: Track response patterns for "waiting for" items

---

## Functional Requirements

### R1: Action Item Storage
**Purpose**: Persistent tracking of all email-derived action items

**Acceptance Criteria**:
- ✅ Store action items with: id, message_id, thread_id, subject, sender, description, deadline, priority, status
- ✅ Link to original email via message_id
- ✅ Support concurrent access (SQLite with WAL mode)
- ✅ CRUD operations: create, read, update, delete
- ✅ Query by: status, deadline, sender, date range

**Database Schema**:
```sql
CREATE TABLE email_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    action_description TEXT NOT NULL,
    action_type TEXT NOT NULL,           -- 'ACTION' or 'WAITING'
    deadline TEXT,
    priority TEXT NOT NULL,              -- 'HIGH', 'MEDIUM'
    extracted_date TEXT NOT NULL,
    status TEXT NOT NULL,                -- See R3
    last_reply_date TEXT,
    reply_count INTEGER DEFAULT 0,
    completed_date TEXT,
    ai_confidence REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Test Cases**:
- TC1.1: Insert action item with all fields
- TC1.2: Retrieve action by message_id
- TC1.3: Query actions by status
- TC1.4: Update action status
- TC1.5: Handle duplicate message_id (constraint)

---

### R2: Action Type Classification
**Purpose**: Distinguish between YOUR actions vs WAITING for others

**Acceptance Criteria**:
- ✅ ACTION type: Received emails requesting you to do something
- ✅ WAITING type: Sent emails requesting others to do something
- ✅ Auto-classification based on email folder (Inbox → ACTION, Sent → WAITING)
- ✅ Detection of request language patterns

**Classification Rules**:
```python
def classify_action_type(email):
    # Sent email with request language → WAITING
    if email.folder == "Sent" and contains_request_patterns(email):
        return "WAITING"

    # Received email with request language → ACTION
    if email.folder == "Inbox" and contains_request_patterns(email):
        return "ACTION"

    return "ACTION"  # Default
```

**Request Patterns**:
- "can you", "please send", "need from you", "could you provide"
- "waiting for", "expecting", "by when", "please confirm"

**Test Cases**:
- TC2.1: Received email with "can you send" → ACTION
- TC2.2: Sent email with "please provide" → WAITING
- TC2.3: Received email without request → ACTION (default)
- TC2.4: Multiple request patterns in one email

---

### R3: Status State Machine
**Purpose**: Track lifecycle of action items

**States**:
1. **PENDING**: Initial state, no action taken
2. **REPLIED**: You replied to thread (for ACTION type)
3. **IN_PROGRESS**: Work in progress (detected from reply content)
4. **CLARIFYING**: Asking for more info (detected from reply)
5. **COMPLETED**: Task done (detected from reply or manual)
6. **OVERDUE**: Deadline passed, not completed
7. **STALLED**: Multiple replies (>2) but no completion after 7+ days
8. **CANCELLED**: Manually marked as no longer needed

**State Transitions**:
```
PENDING → REPLIED (reply detected)
REPLIED → COMPLETED (completion keywords detected)
REPLIED → IN_PROGRESS (progress keywords detected)
REPLIED → CLARIFYING (question keywords detected)
PENDING → OVERDUE (deadline passed)
REPLIED → STALLED (>7 days, >2 replies, no completion)
ANY → CANCELLED (manual)
```

**Acceptance Criteria**:
- ✅ All state transitions enforced
- ✅ Automatic OVERDUE transition at deadline
- ✅ Track state change history
- ✅ Prevent invalid transitions

**Test Cases**:
- TC3.1: PENDING → REPLIED on reply detection
- TC3.2: PENDING → OVERDUE when deadline passes
- TC3.3: REPLIED → COMPLETED with completion keywords
- TC3.4: REPLIED → STALLED after 7 days + 2 replies
- TC3.5: Invalid transition raises error

---

### R4: Automatic Reply Detection
**Purpose**: Detect when you reply to action item threads

**Acceptance Criteria**:
- ✅ Thread matching via subject (Re: prefix)
- ✅ Thread matching via message_id reference
- ✅ Update status PENDING → REPLIED
- ✅ Record reply timestamp
- ✅ Increment reply_count
- ✅ Handle multiple replies to same thread

**Thread Matching Logic**:
```python
def is_reply_to_action(sent_email, action):
    # Subject match: "Re: Original Subject"
    if sent_email.subject == f"Re: {action.subject}":
        return True

    # Thread ID match (if available)
    if sent_email.thread_id == action.thread_id:
        return True

    return False
```

**Test Cases**:
- TC4.1: Reply with "Re: Subject" matches action
- TC4.2: Reply increments reply_count
- TC4.3: First reply changes status to REPLIED
- TC4.4: Multiple replies to same action
- TC4.5: Reply to different thread doesn't match

---

### R5: Completion Detection (Gemma2 9B)
**Purpose**: Analyze reply content to determine completion

**Acceptance Criteria**:
- ✅ Use Gemma2 9B for intent classification
- ✅ Detect completion keywords: "done", "sent", "attached", "completed", "finished"
- ✅ Detect progress keywords: "working on", "will send", "in progress"
- ✅ Detect clarification: "question", "clarify", "which"
- ✅ Update status based on detected intent
- ✅ Confidence score ≥ 0.7 required for auto-status change

**Intent Classification**:
```python
def detect_reply_intent(reply_text):
    prompt = f"""Classify email reply intent:

    Reply: {reply_text}

    Return JSON:
    {{"intent": "COMPLETED|IN_PROGRESS|CLARIFYING|DECLINED|ACKNOWLEDGED",
      "confidence": 0.95}}
    """

    result = call_gemma2(prompt)
    return result
```

**Intent Mapping**:
- COMPLETED → status: COMPLETED
- IN_PROGRESS → status: IN_PROGRESS
- CLARIFYING → status: CLARIFYING
- DECLINED → status: CANCELLED
- ACKNOWLEDGED → status: REPLIED (no change)

**Test Cases**:
- TC5.1: "Attached the export" → COMPLETED
- TC5.2: "Working on it" → IN_PROGRESS
- TC5.3: "Which export?" → CLARIFYING
- TC5.4: "Can't do this" → DECLINED/CANCELLED
- TC5.5: Low confidence (<0.7) → no auto-change

---

### R6: Overdue Tracking
**Purpose**: Automatic flagging when deadlines pass

**Acceptance Criteria**:
- ✅ Hourly check: deadline < now() and status != COMPLETED
- ✅ Auto-update status to OVERDUE
- ✅ Calculate hours/days overdue
- ✅ Priority sort: most overdue first

**Test Cases**:
- TC6.1: Deadline passed, status PENDING → OVERDUE
- TC6.2: Deadline passed, status COMPLETED → no change
- TC6.3: Calculate days overdue correctly
- TC6.4: Sort by overdue duration (DESC)

---

### R7: "Waiting For" Tracking
**Purpose**: Track when YOU'RE waiting for others to respond

**Acceptance Criteria**:
- ✅ Detect outbound requests in sent emails
- ✅ Store as WAITING type action
- ✅ Track expected response time (default: 3 days)
- ✅ Alert when no response after expected time
- ✅ Track follow-up count

**Database Schema**:
```sql
CREATE TABLE waiting_for (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER REFERENCES email_actions(id),
    requested_date TEXT NOT NULL,
    recipient TEXT NOT NULL,
    expected_response_date TEXT NOT NULL,
    last_followup_date TEXT,
    followup_count INTEGER DEFAULT 0,
    status TEXT NOT NULL,            -- 'WAITING', 'RECEIVED', 'OVERDUE'
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Test Cases**:
- TC7.1: Sent email with "can you" creates WAITING entry
- TC7.2: Expected response = deadline or +3 days
- TC7.3: No reply after expected time → OVERDUE
- TC7.4: Reply received → status RECEIVED
- TC7.5: Track multiple follow-ups

---

### R8: Stalled Conversation Detection
**Purpose**: Identify conversations that went nowhere

**Acceptance Criteria**:
- ✅ Conditions: reply_count > 2 AND days_since_last_reply > 7 AND status != COMPLETED
- ✅ Auto-update status to STALLED
- ✅ Surface in brief for manual resolution

**Test Cases**:
- TC8.1: 3 replies + 8 days no activity → STALLED
- TC8.2: 2 replies + 10 days → not STALLED (needs >2)
- TC8.3: 3 replies + 5 days → not STALLED (needs >7)
- TC8.4: COMPLETED action never becomes STALLED

---

### R9: Integration with Email Intelligence Brief
**Purpose**: Display action tracker in hourly brief

**Acceptance Criteria**:
- ✅ Dashboard section in email brief
- ✅ Group by status: OVERDUE / TODAY / PENDING / WAITING / COMPLETED
- ✅ Sort: OVERDUE by urgency, TODAY by deadline, others by creation date
- ✅ Show statistics: total tracked, completion rate, overdue count
- ✅ Performance: query + format < 2 seconds

**Brief Format**:
```markdown
## 📋 ACTION TRACKER DASHBOARD

### 🔴 OVERDUE (2 items)
1. ⚠️ Send IT Glue export to Moir Group
   Deadline: 3 hours ago | Status: PENDING

### 📌 TODAY'S ACTIONS (5 items)
...

### ⏳ WAITING FOR REPLY (3 items)
...

## 📈 TRACKING METRICS
- Completion rate: 87% (20/23 this week)
- Avg completion time: 1.8 days
```

**Test Cases**:
- TC9.1: Format brief with 0 actions
- TC9.2: Format brief with actions in all states
- TC9.3: Performance: 100 actions < 2 sec
- TC9.4: Correct sorting within each category

---

## Non-Functional Requirements

### NFR1: Performance
- Database queries: < 100ms (95th percentile)
- Hourly update cycle: < 30 seconds total
- Gemma2 batch processing: 50 emails at once
- Brief generation: < 2 seconds

### NFR2: Data Retention
- Active actions: indefinite
- Completed actions: 90 days
- Archive after 90 days (keep for metrics)
- Database cleanup: monthly job

### NFR3: Reliability
- SQLite WAL mode for concurrency
- Atomic transactions for state changes
- Graceful degradation if Gemma2 unavailable
- Error logging for all failures

### NFR4: Maintainability
- 100% test coverage for core logic
- Comprehensive logging
- Clear error messages
- Documentation for all public APIs

---

## Edge Cases

### EC1: Vague Deadlines
**Scenario**: "Can you send this soon?"
**Handling**: Default deadline = extracted_date + 3 days

### EC2: Multiple People on Thread
**Scenario**: Email CC'd to multiple people
**Handling**: Track primary sender only (From: field)

### EC3: Split Threads
**Scenario**: Email thread diverges into multiple topics
**Handling**: Track by original message_id, first reply wins

### EC4: Cancelled Actions
**Scenario**: "Never mind, not needed anymore"
**Handling**: Status = CANCELLED, remove from active views

### EC5: Ambiguous Reply Intent
**Scenario**: "Thanks" (is it done or just acknowledged?)
**Handling**: If confidence < 0.7, status = REPLIED (no auto-complete)

---

## Integration Points

1. **MacOS Mail Bridge** (existing)
   - Fetch inbox and sent emails
   - Thread identification via message_id

2. **Email RAG** (existing)
   - Historical thread context
   - Sender patterns for "waiting for" alerts

3. **Gemma2 9B** (existing)
   - Reply intent classification
   - Confidence scoring

4. **Morning Email Intelligence** (existing)
   - Add action tracker dashboard section
   - Hourly update cycle integration

5. **Stakeholder Intelligence** (future - Phase 4)
   - Feed reply patterns for relationship health
   - Track responsiveness metrics

6. **GTD Tracker** (future - Phase 4)
   - Bi-directional sync
   - @email tag management

---

## Out of Scope (Phase 1)

- ❌ GTD tracker integration (Phase 4)
- ❌ Web dashboard UI (Phase 5)
- ❌ Email sending from tracker
- ❌ Calendar integration
- ❌ Mobile notifications
- ❌ Multi-user support

---

## Acceptance Testing Scenarios

### Scenario 1: End-to-End Action Flow
1. Receive email: "Can you send report by Friday 5PM?"
2. Action created: PENDING, deadline Friday 5PM
3. Thursday: Reply "Working on it" → IN_PROGRESS
4. Friday 2PM: Reply "Attached" → COMPLETED
5. Verify: completion_time = 1.5 days, on-time

### Scenario 2: Overdue Detection
1. Action deadline: Today 5PM
2. No reply sent
3. Hourly check at 6PM: status → OVERDUE
4. Brief shows: "1 OVERDUE action"

### Scenario 3: Waiting For Flow
1. Send email: "Please provide Azure costs by Monday"
2. WAITING entry created, expected Monday
3. Monday passes, no reply → OVERDUE for follow-up
4. Brief shows: "1 follow-up needed"

---

**Requirements Sign-Off**: ✅ Complete
**Next Phase**: Test Design (Phase 3)
**Estimated Implementation**: 6-8 hours
