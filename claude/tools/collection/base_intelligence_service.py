"""Base intelligence service for unified intelligence framework.

Provides abstract base class for all intelligence collection services
(Trello, Grafana, Dynatrace, etc.) with standardized interfaces for
data freshness, querying, and refresh operations.

Sprint: SPRINT-UFC-001 (Unified Intelligence Framework)
Phase: 265
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class QueryResult:
    """Standardized query result across all intelligence services.

    Attributes:
        data: List of result records as dictionaries
        source: Name of the data source (e.g., "trello", "grafana")
        extraction_timestamp: When the data was extracted/cached
        is_stale: Whether data exceeds staleness threshold
        staleness_warning: Human-readable warning if data is stale
        query_time_ms: Query execution time in milliseconds
    """

    data: List[Dict[str, Any]]
    source: str
    extraction_timestamp: datetime
    is_stale: bool = False
    staleness_warning: Optional[str] = None
    query_time_ms: int = 0

    def __post_init__(self):
        """Auto-detect staleness based on extraction timestamp."""
        if self.extraction_timestamp:
            days_old = (datetime.now() - self.extraction_timestamp).days
            if days_old > 7 and not self.is_stale:
                self.is_stale = True
                self.staleness_warning = f"Data is {days_old} days old"


@dataclass
class FreshnessInfo:
    """Data freshness information for a source.

    Attributes:
        last_refresh: Timestamp of last successful refresh
        days_old: Age of data in days
        is_stale: Whether data exceeds staleness threshold
        record_count: Number of records in the dataset
        warning: Optional human-readable warning message
    """

    last_refresh: Optional[datetime]
    days_old: int
    is_stale: bool
    record_count: int
    warning: Optional[str] = None


class BaseIntelligenceService(ABC):
    """Abstract base for all intelligence services.

    Provides unified interface for:
    - Data freshness reporting (get_data_freshness_report)
    - Raw SQL/query execution (query_raw)
    - Data refresh operations (refresh)
    - Staleness detection (is_stale)

    Subclasses must implement the three abstract methods.
    """

    STALENESS_THRESHOLD_DAYS = 7

    @abstractmethod
    def get_data_freshness_report(self) -> Dict[str, FreshnessInfo]:
        """Get freshness information for all data sources.

        Returns:
            Dictionary mapping source name to FreshnessInfo
        """
        pass

    @abstractmethod
    def query_raw(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute raw SQL query against intelligence database.

        Args:
            sql: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            QueryResult with data, source, timestamp, and staleness info
        """
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """Refresh intelligence data from source APIs.

        Returns:
            True if refresh successful, False otherwise
        """
        pass

    def is_stale(self) -> bool:
        """Check if any data sources are stale.

        Returns:
            True if any source exceeds staleness threshold
        """
        report = self.get_data_freshness_report()
        return any(info.is_stale for info in report.values())
