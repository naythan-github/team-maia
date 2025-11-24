# Outcome Tracking Database - Requirements

## Phase 181: Agentic AI Enhancement Project - P4

### Core Purpose
Track outcomes of agentic decisions to enable A/B testing, speculative execution path selection, and continuous improvement.

---

## Database Schema

### Table: outcomes
```sql
CREATE TABLE outcomes (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,

    -- Context
    domain TEXT NOT NULL,
    task_type TEXT,
    query_hash TEXT,  -- Hash of query for grouping similar tasks

    -- Decision
    approach TEXT NOT NULL,  -- Which approach/variant was used
    variant_id TEXT,  -- For A/B testing: 'A', 'B', 'control', etc.
    agent_used TEXT,

    -- Outcome
    success INTEGER NOT NULL,  -- 0 or 1
    quality_score REAL,  -- 0.0-1.0
    latency_ms INTEGER,
    error_type TEXT,  -- NULL if success

    -- Feedback
    user_rating INTEGER,  -- 1-5 scale, NULL if not provided
    user_correction INTEGER DEFAULT 0,  -- Was correction needed?

    -- Metadata
    metadata TEXT  -- JSON for extensible properties
);

CREATE INDEX idx_outcomes_timestamp ON outcomes(timestamp);
CREATE INDEX idx_outcomes_domain ON outcomes(domain);
CREATE INDEX idx_outcomes_approach ON outcomes(approach);
CREATE INDEX idx_outcomes_variant ON outcomes(variant_id);
```

### Table: experiments (for A/B testing)
```sql
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT DEFAULT 'active',  -- active, completed, cancelled
    variants TEXT NOT NULL,  -- JSON array of variant configs
    success_metric TEXT DEFAULT 'success_rate',
    metadata TEXT
);

CREATE INDEX idx_experiments_status ON experiments(status);
```

---

## API Interface

### OutcomeTracker Class

```python
class OutcomeTracker:
    def __init__(self, db_path: Optional[str] = None)

    # Recording
    def record_outcome(self, outcome: Outcome) -> str
    def record_batch(self, outcomes: List[Outcome]) -> List[str]

    # Querying
    def get_outcome(self, outcome_id: str) -> Optional[Outcome]
    def query_outcomes(self,
                       domain: Optional[str] = None,
                       approach: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       limit: int = 100) -> List[Outcome]

    # Analytics
    def get_success_rate(self,
                         domain: Optional[str] = None,
                         approach: Optional[str] = None,
                         days: int = 30) -> float
    def get_approach_comparison(self,
                                approaches: List[str],
                                domain: Optional[str] = None) -> Dict[str, ApproachStats]
    def get_trends(self,
                   domain: Optional[str] = None,
                   granularity: str = 'day',
                   days: int = 30) -> List[TrendPoint]

    # A/B Testing
    def create_experiment(self, experiment: Experiment) -> str
    def get_experiment_results(self, experiment_id: str) -> ExperimentResults
    def end_experiment(self, experiment_id: str, winner: Optional[str] = None) -> None

    # Health
    def health_check(self) -> Dict[str, Any]
    def get_stats(self) -> Dict[str, Any]
```

### Data Classes

```python
@dataclass
class Outcome:
    domain: str
    approach: str
    success: bool
    id: Optional[str] = None  # Auto-generated if not provided
    timestamp: Optional[datetime] = None
    task_type: Optional[str] = None
    query_hash: Optional[str] = None
    variant_id: Optional[str] = None
    agent_used: Optional[str] = None
    quality_score: Optional[float] = None
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    user_rating: Optional[int] = None
    user_correction: bool = False
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ApproachStats:
    approach: str
    total_count: int
    success_count: int
    success_rate: float
    avg_quality: Optional[float]
    avg_latency_ms: Optional[float]

@dataclass
class TrendPoint:
    period: str  # e.g., '2025-11-24'
    success_rate: float
    total_count: int
    avg_quality: Optional[float]

@dataclass
class Experiment:
    name: str
    variants: List[str]
    id: Optional[str] = None
    description: Optional[str] = None
    success_metric: str = 'success_rate'
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExperimentResults:
    experiment_id: str
    name: str
    status: str
    variant_stats: Dict[str, ApproachStats]
    winner: Optional[str]  # Statistical winner if significant
    confidence: Optional[float]  # Statistical confidence
```

---

## Test Cases

### FR1: Outcome Recording
- [ ] Record single outcome with required fields
- [ ] Record outcome with all optional fields
- [ ] Auto-generate ID and timestamp if not provided
- [ ] Record batch of outcomes
- [ ] Handle invalid quality_score (outside 0-1 range)
- [ ] Handle invalid user_rating (outside 1-5 range)

### FR2: Outcome Querying
- [ ] Get outcome by ID
- [ ] Query by domain filter
- [ ] Query by approach filter
- [ ] Query by time range
- [ ] Query with combined filters
- [ ] Respect limit parameter
- [ ] Return empty list for no matches

### FR3: Pattern Analysis
- [ ] Calculate success rate for domain
- [ ] Calculate success rate for approach
- [ ] Compare multiple approaches
- [ ] Generate daily trends
- [ ] Generate weekly trends
- [ ] Handle empty data gracefully

### FR4: A/B Testing
- [ ] Create experiment with variants
- [ ] Record outcomes with variant_id
- [ ] Get experiment results with per-variant stats
- [ ] End experiment and declare winner
- [ ] Filter outcomes by experiment

### NFR1: Performance
- [ ] Record latency < 10ms
- [ ] Query latency < 100ms for 1K records
- [ ] Handle 10K+ records without degradation

### NFR2: Reliability
- [ ] Graceful handling when DB unavailable
- [ ] Data persists across restarts
- [ ] No data loss on concurrent writes

### NFR3: Observability
- [ ] Health check returns status
- [ ] Stats include record counts
- [ ] Logging on errors

---

*Created: 2025-11-24*
*Status: Requirements Complete - Ready for Test Design*
