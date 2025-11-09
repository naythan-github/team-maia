# Phase 124: Live Monitoring Integration

**Status**: UP NEXT
**Priority**: MEDIUM
**Estimated Time**: 6-8 hours
**Dependencies**: Phase 121 (Automatic Agent Routing), Phase 122 (Routing Accuracy Monitoring), Phase 123 (Quality Improvement Measurement)

---

## Executive Summary

Integrate performance and quality monitoring directly into the coordinator agent for real-time data collection. Eliminates external logging overhead, reduces latency, consolidates all monitoring data, and enables instant feedback loops for routing optimization. Transforms monitoring from post-hoc analysis to live operational intelligence.

---

## Problem Statement

Current monitoring architecture has gaps:
- **External Logging**: Separate tools log data after the fact
- **Latency Overhead**: Multiple write operations slow down routing
- **Data Fragmentation**: Metrics scattered across databases
- **Delayed Feedback**: Can't optimize routing in real-time
- **Maintenance Burden**: Multiple systems to maintain

Live integration consolidates everything into the coordinator for efficiency and real-time optimization.

---

## Success Criteria

1. ✅ All monitoring integrated into coordinator.route() method
2. ✅ Zero external logging tools (consolidated into coordinator)
3. ✅ <50ms monitoring overhead (minimal latency impact)
4. ✅ Real-time feedback loop (routing optimizes based on live metrics)
5. ✅ Single database for all monitoring data

---

## Technical Design

### Current Architecture (Fragmented)

```
User Query
    ↓
Coordinator suggests agents
    ↓ [External Logger 1: Routing Decision Logger]
Maia accepts/overrides
    ↓ [External Logger 2: Acceptance Tracker]
Agents execute
    ↓ [External Logger 3: Performance Metrics Collector]
Response generated
    ↓ [External Logger 4: Quality Scorer]
Result returned
```

**Problems**:
- 4 separate logging points
- 4 database writes
- Estimated latency: ~150-200ms overhead
- Data reconciliation required

### New Architecture (Integrated)

```
User Query
    ↓
Coordinator.route() [INTEGRATED MONITORING]
    ├─ Intent classification (logged inline)
    ├─ Agent selection (logged inline)
    ├─ Routing decision (logged inline)
    ├─ Execution start (timestamp)
    ↓
Agents execute
    ↓
Coordinator.complete() [INTEGRATED MONITORING]
    ├─ Execution end (timestamp)
    ├─ Quality assessment (inline)
    ├─ Acceptance detection (inline)
    └─ Single database write (batched)
    ↓
Result returned
```

**Benefits**:
- 1 logging point
- 1 database write (batched)
- Estimated latency: <50ms overhead (70% reduction)
- No reconciliation needed (all data in context)

---

## Implementation Plan

### Week 1: Database Consolidation (2 hours)

**Task 1.1: Unified Monitoring Database** (1 hour)
- Create `unified_monitoring.db`
- Merge schemas from:
  - routing_decisions.db (Phase 122)
  - quality_metrics.db (Phase 123)
  - agent_performance.db (existing)
- Add indexes for fast queries
- Migration script for existing data

**Schema**:
```sql
CREATE TABLE monitoring_events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT, -- routing, execution, quality

    -- Query context
    query_hash TEXT,
    query_category TEXT,
    query_complexity INTEGER,

    -- Routing
    intent_category TEXT,
    intent_domains TEXT, -- JSON
    suggested_agents TEXT, -- JSON
    routing_strategy TEXT,
    confidence FLOAT,

    -- Execution
    actual_agents TEXT, -- JSON
    accepted BOOLEAN,
    override_reason TEXT,
    execution_time_ms FLOAT,
    success BOOLEAN,
    error TEXT,

    -- Quality
    quality_score FLOAT,
    task_completed BOOLEAN,
    code_valid BOOLEAN,
    tests_passed BOOLEAN,

    -- Performance
    token_count INTEGER,
    context_size_kb FLOAT
);

CREATE INDEX idx_timestamp ON monitoring_events(timestamp);
CREATE INDEX idx_query_hash ON monitoring_events(query_hash);
CREATE INDEX idx_event_type ON monitoring_events(event_type);
```

**Task 1.2: Data Migration** (1 hour)
- Migrate existing data from separate databases
- Validate data integrity
- Archive old databases
- Update dashboard queries to use unified database

### Week 2: Coordinator Integration (4 hours)

**Task 2.1: Monitoring Manager Class** (2 hours)
- Create `monitoring_manager.py`
- Lightweight monitoring class integrated into coordinator
- Batched database writes (reduce I/O)
- Async writes (non-blocking)
- Error handling and graceful degradation

```python
class MonitoringManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.batch = []
        self.batch_size = 10

    def log_event(self, event_data: dict):
        """Add event to batch, write when batch full"""
        self.batch.append(event_data)
        if len(self.batch) >= self.batch_size:
            self._flush()

    def _flush(self):
        """Write batch to database (async)"""
        # Async database write
        pass

    def context_manager(self):
        """Context manager for automatic flushing"""
        return MonitoringContext(self)
```

**Task 2.2: Coordinator Integration** (2 hours)
- Modify `coordinator_agent.py`
- Add monitoring at key points:
  - Start of route() - capture intent classification
  - Agent selection - capture routing decision
  - End of route() - capture execution start
  - Callback for completion - capture results
- Pass monitoring context to agents
- Single flush at end of request

```python
class CoordinatorAgent:
    def __init__(self):
        self.monitor = MonitoringManager('unified_monitoring.db')

    def route(self, query: str) -> RoutingDecision:
        with self.monitor.context_manager() as ctx:
            # Classify intent
            intent = self.intent_classifier.classify(query)
            ctx.log_intent(intent)

            # Select agents
            routing = self.agent_selector.select(intent, query)
            ctx.log_routing(routing)

            # Execute (agents log their own performance inline)
            start_time = time.time()
            result = self._execute(routing)
            execution_time = (time.time() - start_time) * 1000

            # Quality assessment (inline)
            quality = self._assess_quality(result)
            ctx.log_quality(quality)

            # Acceptance detection (inline)
            acceptance = self._detect_acceptance(routing, result)
            ctx.log_acceptance(acceptance)

            return result
            # Flush happens automatically on context exit
```

### Week 3: Real-Time Feedback Loop (2 hours)

**Task 3.1: Live Optimization** (1 hour)
- Use monitoring data to optimize routing in real-time
- If agent has low success rate → reduce confidence
- If category has low accuracy → adjust thresholds
- If quality drops → trigger review
- Cache recent metrics for fast lookup

**Task 3.2: Performance Tuning** (1 hour)
- Benchmark monitoring overhead
- Optimize database writes (batch size, async)
- Reduce memory footprint
- Target: <50ms overhead per request

---

## Deliverables

### Code Components
1. **monitoring_manager.py** (250 lines)
   - Lightweight monitoring class
   - Batched writes
   - Async I/O
   - Context manager

2. **unified_monitoring.db schema** (100 lines SQL)
   - Consolidated schema
   - Indexes for performance
   - Migration scripts

3. **coordinator_agent.py updates** (150 lines modified)
   - Monitoring integration
   - Quality assessment inline
   - Acceptance detection inline
   - Feedback loop

4. **data_migrator.py** (150 lines)
   - Migrate data from old databases
   - Validation
   - Archive old databases

### Databases
- **unified_monitoring.db** - Single source of truth for all monitoring
- **Archive**: routing_decisions.db, quality_metrics.db, agent_performance.db (backed up)

### Documentation
- **Live Monitoring Architecture** - How integrated monitoring works
- **Performance Tuning Guide** - How to optimize monitoring overhead
- **Migration Guide** - How data was migrated

---

## Performance Optimization

### Latency Reduction Strategy

**Before (External Logging)**:
- 4 separate database writes: ~150-200ms
- File I/O overhead: ~50ms
- Lock contention: ~20ms
- **Total**: ~220-270ms overhead per request

**After (Integrated Monitoring)**:
- 1 batched database write: ~30ms
- Async I/O (non-blocking): 0ms perceived
- No lock contention: 0ms
- **Total**: <50ms overhead per request
- **Improvement**: 77-81% latency reduction

### Memory Optimization

- Batch size: 10 events (configurable)
- Estimated memory: ~5KB per event × 10 = ~50KB
- Flush on batch full or request end
- Graceful degradation if database unavailable

### Database Optimization

- Write-ahead logging (WAL mode)
- Indexes on common query patterns
- Vacuum on schedule (weekly)
- Archive old data (>90 days)

---

## Real-Time Feedback Loop

### Optimization Triggers

1. **Low Success Rate** (Agent < 80% success)
   - Action: Reduce confidence score by 10%
   - Effect: Less likely to be selected
   - Duration: Until success rate improves

2. **High Override Rate** (Category > 30% overrides)
   - Action: Adjust intent classification thresholds
   - Effect: Better agent matching
   - Review: Weekly

3. **Quality Regression** (Category drops >10%)
   - Action: Alert + manual review
   - Effect: Investigate root cause
   - Review: Immediate

4. **Performance Bottleneck** (Agent >5s avg)
   - Action: Reduce parallel usage
   - Effect: Prevent slowdowns
   - Review: Daily

### Feedback Loop Implementation

```python
class FeedbackLoop:
    def __init__(self, monitor: MonitoringManager):
        self.monitor = monitor
        self.cache = {}  # Recent metrics cache

    def check_and_optimize(self):
        """Run after each routing decision"""
        # Get recent metrics (last 100 requests)
        metrics = self.monitor.get_recent_metrics(limit=100)

        # Check agent success rates
        for agent in metrics['agents']:
            if agent['success_rate'] < 0.80:
                self._reduce_agent_confidence(agent['name'])

        # Check category override rates
        for category in metrics['categories']:
            if category['override_rate'] > 0.30:
                self._adjust_category_thresholds(category['name'])

        # Check quality scores
        for category in metrics['quality']:
            if category['quality_drop_pct'] > 10:
                self._alert_quality_regression(category['name'])
```

---

## Migration Strategy

### Phase 1: Parallel Operation (1 week)
- New integrated monitoring runs alongside old system
- Validate data consistency
- Compare results
- Zero user impact

### Phase 2: Gradual Cutover (1 week)
- Dashboards read from unified database
- Old loggers still write (backup)
- Monitor for issues
- Rollback available

### Phase 3: Full Migration (1 day)
- Disable old loggers
- Archive old databases
- Update documentation
- Monitoring fully integrated

---

## Success Metrics

### Immediate (Week 1-2)
- Database consolidation: 3 databases → 1 unified database
- Data migration: 100% of historical data migrated
- Schema validation: All queries work with new schema

### Short-term (Month 1)
- Latency reduction: <50ms monitoring overhead (77-81% improvement)
- Real-time optimization: Feedback loop operational
- Zero data loss: All monitoring events captured

### Long-term (Month 2-3)
- Quality improvement: +5% from real-time optimization
- Maintenance reduction: 1 system instead of 4
- Feedback effectiveness: Measurable routing improvement from live optimization

---

## Risk Mitigation

### Risk 1: Data Loss During Migration
**Mitigation**: Parallel operation period, backup all databases, validation scripts

### Risk 2: Performance Degradation
**Mitigation**: Benchmark before/after, async writes, rollback plan

### Risk 3: Monitoring Failures Block Routing
**Mitigation**: Graceful degradation - routing works even if monitoring fails

### Risk 4: Database Corruption
**Mitigation**: WAL mode, regular backups, corruption detection

---

## Integration Points

- **Phase 121**: Coordinator Agent (integrate monitoring)
- **Phase 122**: Routing Accuracy Monitoring (use unified database)
- **Phase 123**: Quality Improvement Measurement (use unified database)
- **Agent Performance Dashboard**: Update to query unified database
- **Weekly Review**: Include monitoring health metrics

---

## Future Enhancements

- **Distributed Monitoring**: Multi-instance coordination
- **Real-Time Alerts**: Push notifications for critical issues
- **ML Optimization**: Train model on monitoring data for routing
- **Monitoring API**: External systems query monitoring data
- **Multi-User Support**: Per-user monitoring and optimization

---

## Estimated ROI

**Investment**: 8 hours development + 1 hour/week monitoring

**Return**:
- Latency reduction: 77-81% faster (220-270ms → <50ms)
- Maintenance reduction: 4 systems → 1 system (75% less maintenance)
- Real-time optimization: +5% quality improvement from feedback loop
- Data consistency: Single source of truth (no reconciliation)
- Development velocity: Easier to add new monitoring features

**Payback**: Immediate (latency reduction alone valuable), full ROI in 4-6 weeks

---

## Status: READY FOR IMPLEMENTATION

Dependencies met. Phase 121-123 operational. Can start Week 1 immediately after Phase 123 completion. Parallel operation strategy ensures zero risk.
