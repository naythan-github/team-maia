# Stakeholder Relationship Intelligence Agent

**Agent ID**: stakeholder_relationship_intelligence
**Type**: Specialized Intelligence Agent
**Priority**: HIGH
**Status**: Phase 2 Implementation
**Created**: 2025-10-13

---

## 🎯 Purpose

CRM-style intelligence system for managing relationships with executives, team members, clients, and vendors in high-touch engineering management role. Provides proactive relationship health monitoring, sentiment analysis, and automated context assembly for stakeholder interactions.

---

## 🧠 Core Capabilities

### 1. Relationship Mapping & Segmentation

**Capability**: Automatically discover and classify stakeholders from communication patterns

**Segments**:
- **Direct Reports**: Team members requiring 1-on-1s, performance management, coaching
- **Skip-Level**: Visibility to team health, early warning system
- **Executive Leadership**: Senior leaders requiring strategic briefings
- **Key Collaborators**: Frequent coordination partners
- **External Clients**: High-touch customer relationships
- **Vendors/Partners**: Strategic supplier relationships

**Data Sources**:
- Email patterns (Email RAG: 313 emails indexed)
- Calendar frequency (Calendar Bridge)
- Meeting transcripts (VTT Intelligence)
- Confluence mentions (Confluence Intelligence)
- Personal Knowledge Graph connections

**Output**: Stakeholder graph with nodes (people) and edges (relationship types, strength)

---

### 2. Sentiment Analysis & Engagement Tracking

**Capability**: Analyze communication sentiment and engagement patterns over time

**Metrics**:
- **Sentiment Score**: -1.0 (negative) to +1.0 (positive)
- **Engagement Level**: high, medium, low (based on communication frequency)
- **Response Time**: Average time to respond to stakeholder
- **Communication Balance**: Outbound vs inbound ratio
- **Sentiment Trend**: Improving, stable, declining

**Analysis Method**:
- Local LLM (CodeLlama 13B) for privacy-first sentiment analysis
- Historical pattern analysis (last 30/60/90 days)
- Keyword/phrase extraction for sentiment indicators
- Meeting transcript tone analysis

**Privacy**: 100% local processing, no cloud transmission

---

### 3. Relationship Health Monitoring

**Capability**: Calculate relationship health scores and identify at-risk relationships

**Health Score Algorithm**:
```python
health_score = (
    sentiment_score * 0.30 +          # Current sentiment
    engagement_frequency * 0.25 +      # Communication cadence
    commitment_delivery * 0.20 +       # Promises kept
    response_time_score * 0.15 +       # Responsiveness
    meeting_attendance * 0.10          # Meeting participation
) * 100  # Scale to 0-100
```

**Health Categories**:
- **90-100**: Excellent (Strong relationship, proactive engagement)
- **70-89**: Good (Healthy, maintain current cadence)
- **50-69**: At Risk (Declining engagement, needs attention)
- **Below 50**: Critical (Immediate intervention required)

**Alerts**:
- Weekly digest of relationships requiring attention
- Real-time alerts for critical deterioration (>20 point drop)
- Proactive reminders (no contact in >X days based on cadence)

---

### 4. Pre-Meeting Context Assembly

**Capability**: Automatically generate comprehensive context packages before stakeholder interactions

**Context Package Includes**:
1. **Relationship Overview**
   - Current health score and trend
   - Last 3 interactions summary
   - Sentiment trajectory (improving/declining)

2. **Historical Context**
   - Past meetings with key topics/decisions
   - Email thread summaries (last 30 days)
   - Open action items and commitments

3. **Strategic Context**
   - Related strategic initiatives
   - Pending decisions involving stakeholder
   - Relevant open questions

4. **Recommended Topics**
   - Based on role and current priorities
   - Unresolved issues requiring follow-up
   - Opportunities for deeper collaboration

5. **Talking Points**
   - Celebration items (wins, milestones)
   - Concern areas (blockers, risks)
   - Development topics (for direct reports)

**Delivery**: 30 minutes before meeting via notification/email

---

### 5. Commitment Tracking & Delivery

**Capability**: Monitor promises made to stakeholders and alert on delivery risks

**Tracked Commitments**:
- Explicit promises in emails ("I'll send you...", "I'll have this by...")
- Meeting action items assigned to you
- Deliverables mentioned in conversations
- Follow-up commitments ("I'll get back to you on...")

**Risk Scoring**:
- **Green**: On track, >2 days until due
- **Yellow**: Due soon, <2 days remaining
- **Red**: Overdue or at risk

**Alerts**:
- Daily digest of commitments due today/tomorrow
- Overdue alerts with stakeholder impact assessment
- Weekly summary for review

---

### 6. Communication Pattern Analysis

**Capability**: Identify communication imbalances and neglected relationships

**Patterns Analyzed**:
- **Communication Frequency**: Contacts per week by stakeholder
- **Initiation Balance**: Who initiates contact more often
- **Response Time**: Average response time to each stakeholder
- **Communication Channels**: Email vs meetings vs chat preferences
- **Time of Day**: Preferred communication times

**Insights**:
- "You haven't contacted [Stakeholder] in 3 weeks (cadence: weekly)"
- "Response time to [Client] increased from 2 hours to 12 hours"
- "[Executive] prefers morning meetings (80% scheduled 9-11 AM)"
- "Communication with [Team Member] is 90% task-focused, consider career development discussion"

---

### 7. Proactive Engagement Recommendations

**Capability**: Generate personalized engagement plans by stakeholder segment

**Recommendations Include**:
- **Suggested Cadence**: Based on role and importance
- **Next Touchpoint**: Recommended date/time
- **Discussion Topics**: Tailored to relationship type
- **Engagement Channel**: Preferred method (1-on-1, email, informal chat)

**Example Output**:
```
Stakeholder: Hamish (Executive Leadership)
Health: 85/100 (Good)
Last Contact: 5 days ago
Recommended Action: Schedule 1-on-1 this week
Topics:
  - Q4 strategic initiative progress
  - Resource needs for Azure Extended Zone positioning
  - Team engagement metrics (30% → 60% improvement)
Channel: 30-min video call (preferred morning)
```

---

### 8. Relationship Dashboard & Visualization

**Capability**: Visual map of stakeholder landscape with health indicators

**Dashboard Widgets**:
1. **Relationship Health Overview**: Grid of stakeholders with color-coded health
2. **At-Risk Relationships**: List requiring immediate attention
3. **Upcoming 1-on-1s**: Next 7 days with prep status
4. **Commitment Tracker**: Promises due this week
5. **Communication Heatmap**: Frequency by stakeholder over time
6. **Sentiment Trends**: 30-day sentiment trajectory
7. **Engagement Recommendations**: Top 5 actions this week

**Technology**: Web dashboard (Flask) or terminal UI (rich library)

---

## 🔧 Key Commands

### Command: `map_stakeholder_landscape`
**Purpose**: Discover and classify all stakeholders from communication data

**Usage**:
```python
agent.map_stakeholder_landscape(
    sources=['email', 'calendar', 'confluence', 'vtt'],
    lookback_days=90
)
```

**Output**: Stakeholder graph with segments and relationships

---

### Command: `analyze_relationship_health`
**Purpose**: Calculate health scores and identify risks

**Usage**:
```python
health_report = agent.analyze_relationship_health(
    stakeholder_id='hamish@orro.com',
    include_history=True
)
```

**Output**:
```json
{
  "stakeholder": "Hamish",
  "health_score": 85,
  "trend": "stable",
  "sentiment": 0.7,
  "engagement_level": "high",
  "last_contact": "5 days ago",
  "recommended_action": "Schedule 1-on-1 this week",
  "risk_factors": []
}
```

---

### Command: `generate_engagement_plan`
**Purpose**: Create weekly engagement plan across all stakeholders

**Usage**:
```python
plan = agent.generate_engagement_plan(week='2025-10-14')
```

**Output**: Prioritized list of touchpoints with recommended topics

---

### Command: `pre_meeting_context_assembly`
**Purpose**: Generate comprehensive context package before meeting

**Usage**:
```python
context = agent.pre_meeting_context_assembly(meeting_id='cal_123')
```

**Output**: Full context package (as described in capability #4)

---

### Command: `track_commitment_status`
**Purpose**: Monitor all commitments to stakeholders

**Usage**:
```python
commitments = agent.track_commitment_status(
    filter='due_this_week',
    stakeholder='hamish@orro.com'  # optional
)
```

**Output**: List of commitments with risk scores

---

### Command: `identify_relationship_risks`
**Purpose**: Proactive alerts for declining relationships

**Usage**:
```python
risks = agent.identify_relationship_risks(threshold=70)
```

**Output**: List of at-risk relationships with intervention recommendations

---

### Command: `stakeholder_communication_audit`
**Purpose**: Analyze communication patterns for imbalances

**Usage**:
```python
audit = agent.stakeholder_communication_audit(period_days=30)
```

**Output**:
```json
{
  "total_stakeholders": 15,
  "neglected": [
    {"name": "Trevor", "last_contact": "15 days", "expected_cadence": "weekly"}
  ],
  "overdue_responses": [
    {"name": "Mariele", "waiting_days": 3, "subject": "Subcategory list"}
  ],
  "communication_balance": {
    "outbound_initiated": 45,
    "inbound_initiated": 55
  }
}
```

---

### Command: `generate_relationship_dashboard`
**Purpose**: Create visual stakeholder map with health indicators

**Usage**:
```python
dashboard = agent.generate_relationship_dashboard(format='html')
```

**Output**: HTML dashboard or terminal visualization

---

## 🏗️ Technical Architecture

### Data Storage

**Stakeholder Database** (SQLite):
```sql
CREATE TABLE stakeholders (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    role TEXT,
    segment TEXT,  -- direct_report, executive, client, etc.
    importance_score INTEGER,  -- 1-10
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE relationship_metrics (
    id INTEGER PRIMARY KEY,
    stakeholder_id INTEGER,
    date TEXT,
    sentiment_score REAL,
    engagement_level TEXT,
    health_score INTEGER,
    response_time_hours REAL,
    communication_count INTEGER,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
);

CREATE TABLE commitments (
    id INTEGER PRIMARY KEY,
    stakeholder_id INTEGER,
    commitment_text TEXT,
    source TEXT,  -- email, meeting, etc.
    source_id TEXT,
    due_date TEXT,
    status TEXT,  -- pending, delivered, overdue
    created_at TEXT,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
);

CREATE TABLE interactions (
    id INTEGER PRIMARY KEY,
    stakeholder_id INTEGER,
    interaction_type TEXT,  -- email, meeting, call
    date TEXT,
    sentiment_score REAL,
    summary TEXT,
    topics TEXT,  -- JSON array
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id)
);
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│    Stakeholder Relationship Intelligence Agent      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                 Data Sources                        │
├─────────────────────────────────────────────────────┤
│ • EmailRAG (313 emails, sentiment extraction)      │
│ • CalendarBridge (meeting frequency)                │
│ • ConversationRAG (past discussions)                │
│ • VTT Intelligence (meeting transcripts)            │
│ • Confluence Intelligence (mentions, collaboration) │
│ • Personal Knowledge Graph (relationships)          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              Analysis Layer                         │
├─────────────────────────────────────────────────────┤
│ • LocalLLMSentiment (CodeLlama 13B)                 │
│ • EngagementCalculator (frequency analysis)         │
│ • HealthScoreEngine (multi-factor algorithm)        │
│ • CommitmentExtractor (NLP for promises)            │
│ • PatternAnalyzer (communication patterns)          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                Output Layer                         │
├─────────────────────────────────────────────────────┤
│ • Health Dashboard (HTML/Terminal)                  │
│ • Pre-Meeting Briefs (JSON/Markdown)                │
│ • Alert System (Email/Notification)                 │
│ • Weekly Engagement Plan (Formatted report)         │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Expected Outcomes

### Quantitative Benefits
- **40-50% improvement in stakeholder satisfaction** (measured via feedback)
- **Identify relationship risks 2-4 weeks earlier** (proactive vs reactive)
- **80% reduction in pre-meeting context gathering time** (automated assembly)
- **100% commitment tracking visibility** (vs spotty manual tracking)
- **2-3x increase in strategic networking time** (freed from tactical follow-ups)

### Qualitative Benefits
- Never miss important relationship deterioration signals
- Consistent communication cadence with key stakeholders
- Always prepared for stakeholder interactions
- Proactive engagement vs reactive firefighting
- Data-driven relationship management decisions

---

## 🧪 Testing Strategy

### Test Scenarios
1. **Stakeholder Discovery**: Identify 10+ stakeholders from email/calendar
2. **Sentiment Analysis**: Analyze 30-day email sentiment for 3 stakeholders
3. **Health Score Calculation**: Generate scores for 5 diverse relationships
4. **Pre-Meeting Context**: Assemble package for upcoming 1-on-1
5. **Commitment Extraction**: Find 5+ commitments from recent emails
6. **Risk Identification**: Flag 2+ at-risk relationships
7. **Communication Audit**: Analyze 30-day patterns for neglect

### Success Criteria
- Stakeholder discovery: >90% accuracy vs manual list
- Sentiment analysis: ±0.2 alignment with human assessment
- Health scores: Correlate with relationship outcomes
- Context packages: Include all relevant history (<5% false negatives)
- Commitment extraction: >85% recall of explicit promises
- Risk alerts: Identify issues before manual detection

---

## 📝 Implementation Checklist

### Phase 2.1 - Week 1
- [ ] Create stakeholder database schema
- [ ] Implement stakeholder discovery from email/calendar
- [ ] Build basic sentiment analysis with CodeLlama
- [ ] Calculate initial health scores for 5 stakeholders

### Phase 2.1 - Week 2
- [ ] Implement commitment extraction from emails
- [ ] Build interaction history tracking
- [ ] Create health score dashboard (terminal UI)
- [ ] Add relationship risk alerts

### Phase 2.1 - Week 3
- [ ] Implement pre-meeting context assembly
- [ ] Build engagement plan generator
- [ ] Create communication audit analyzer
- [ ] Add weekly digest report

### Phase 2.1 - Testing & Polish
- [ ] Run all test scenarios
- [ ] Validate with real stakeholder data
- [ ] Create agent documentation
- [ ] Integrate with Phase 1 systems

---

## 🔗 Integration Points

### Strategic Executive Briefing
- Provide relationship intelligence section
- Surface stakeholders requiring attention
- Include sentiment trends in daily brief

### Meeting Context Auto-Assembly
- Enhance attendee enrichment with sentiment
- Add relationship health indicators
- Provide historical interaction summaries

### Weekly Strategic Review
- Populate stakeholder review section
- Generate 1-on-1 prep checklist
- Track relationship health trends

### GTD Action Tracker
- Link commitments to @stakeholder-[name] contexts
- Alert on overdue commitments by stakeholder
- Integrate with @waiting-for for response tracking

---

## 🚀 Future Enhancements (Phase 3+)

1. **Predictive Analytics**: ML model to predict relationship deterioration
2. **Automated Engagement**: Draft emails/meeting requests based on cadence
3. **Network Analysis**: Identify key connectors and influence paths
4. **Cross-Stakeholder Insights**: Detect coalition-building opportunities
5. **Voice of Customer**: Aggregate client sentiment across organization
6. **Team Health Monitoring**: Track team member engagement patterns

---

## 📚 References

- Personal Knowledge Graph: `claude/tools/personal_knowledge_graph.py`
- Email RAG: `claude/tools/email_rag_ollama.py`
- Calendar Bridge: `claude/tools/macos_calendar_bridge.py`
- VTT Intelligence: `claude/tools/vtt_intelligence_processor.py`
- Phase 1 Meeting Context: `claude/extensions/experimental/meeting_context_auto_assembly.py`

---

**Agent Status**: Ready for Implementation
**Owner**: Maia Executive Information Manager
**Priority**: HIGH
**Estimated Effort**: 2-3 weeks (Phase 2.1)
**Expected Value**: 40-50% stakeholder satisfaction improvement
