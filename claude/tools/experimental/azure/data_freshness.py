"""
Azure Cost Optimization Data Freshness Handler

Tracks and handles Azure's 24-72 hour cost data lag to prevent
false recommendations based on incomplete data.

TDD Implementation - Tests in tests/test_data_freshness.py
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple


# Known Azure data lags (in hours)
# These are conservative estimates based on Azure documentation
DATA_LAG_HOURS: Dict[str, int] = {
    "cost_management": 48,  # 24-72hr, use 48 as safe default
    "azure_monitor": 4,  # 1-4hr for metrics
    "azure_advisor": 24,  # Daily refresh
    "resource_graph": 1,  # Near real-time
}

# Default lag for unknown data types
DEFAULT_LAG_HOURS = 48


@dataclass
class DataFreshness:
    """
    Represents data freshness for a collection.

    Used to determine if data is reliable enough for recommendations.
    """

    data_type: str
    last_collection: datetime
    expected_lag_hours: float
    actual_lag_hours: float
    is_stale: bool
    warning_message: Optional[str] = None

    @property
    def effective_as_of(self) -> datetime:
        """
        When the data actually represents (accounting for lag).

        Example: If collected at 2026-01-10 12:00 with 48hr lag,
        the data is effective as of 2026-01-08 12:00.
        """
        return self.last_collection - timedelta(hours=self.expected_lag_hours)


@dataclass
class CollectionStatus:
    """Internal tracking of collection status."""

    data_type: str
    last_successful: Optional[datetime] = None
    last_attempted: Optional[datetime] = None
    is_healthy: bool = True
    error_message: Optional[str] = None
    first_collection: Optional[datetime] = None


class DataFreshnessManager:
    """
    Manages data freshness awareness for accurate recommendations.

    Key Responsibilities:
    - Track when data was last collected
    - Calculate safe query date ranges that account for data lag
    - Detect stale data and generate warnings
    - Verify minimum observation periods for recommendations

    Usage:
        manager = DataFreshnessManager()

        # Before generating recommendations
        freshness = manager.get_freshness("cost_management")
        if freshness.is_stale:
            logger.warning(freshness.warning_message)

        # Adjust queries to account for lag
        safe_end_date = manager.get_safe_query_end_date("cost_management")
    """

    def __init__(self):
        """Initialize the freshness manager."""
        self._collection_statuses: Dict[str, CollectionStatus] = {}

    def get_safe_query_end_date(self, data_type: str) -> datetime:
        """
        Get safe end date that accounts for data lag.

        Args:
            data_type: Type of data (cost_management, azure_monitor, etc.)

        Returns:
            datetime that is safe to use as query end date
        """
        lag_hours = DATA_LAG_HOURS.get(data_type, DEFAULT_LAG_HOURS)
        return datetime.now() - timedelta(hours=lag_hours)

    def is_data_complete_for_date(self, data_type: str, target_date: date) -> bool:
        """
        Check if data is likely complete for a given date.

        Args:
            data_type: Type of data
            target_date: The date to check

        Returns:
            True if data for target_date is likely complete
        """
        safe_datetime = self.get_safe_query_end_date(data_type)
        safe_date = safe_datetime.date()
        return target_date < safe_date

    def get_freshness_warning(self, data_type: str) -> str:
        """
        Get warning message about data freshness.

        Args:
            data_type: Type of data

        Returns:
            Warning message string
        """
        lag = DATA_LAG_HOURS.get(data_type, DEFAULT_LAG_HOURS)
        effective_time = datetime.now() - timedelta(hours=lag)
        effective_str = effective_time.strftime("%Y-%m-%d %H:%M")

        return (
            f"Note: {data_type} data may be incomplete for the last {lag} hours. "
            f"Recommendations based on data effective as of {effective_str}."
        )

    def update_collection_status(
        self,
        data_type: str,
        last_successful: Optional[datetime] = None,
        is_healthy: bool = True,
        last_attempted: Optional[datetime] = None,
        error_message: Optional[str] = None,
        first_collection: Optional[datetime] = None,
    ) -> None:
        """
        Update the collection status for a data type.

        Args:
            data_type: Type of data
            last_successful: When data was last successfully collected
            is_healthy: Whether collection is currently healthy
            last_attempted: When collection was last attempted
            error_message: Error message if collection failed
            first_collection: When data collection first started (for observation period)
        """
        if data_type not in self._collection_statuses:
            self._collection_statuses[data_type] = CollectionStatus(data_type=data_type)

        status = self._collection_statuses[data_type]

        if last_successful is not None:
            status.last_successful = last_successful
            # Set first_collection if not already set
            if status.first_collection is None:
                status.first_collection = first_collection or last_successful

        if last_attempted is not None:
            status.last_attempted = last_attempted

        status.is_healthy = is_healthy

        if error_message is not None:
            status.error_message = error_message

        if first_collection is not None:
            status.first_collection = first_collection

    def get_collection_status(self, data_type: str) -> Optional[Dict]:
        """
        Get the collection status for a data type.

        Args:
            data_type: Type of data

        Returns:
            Dictionary with status info or None if not tracked
        """
        status = self._collection_statuses.get(data_type)
        if status is None:
            return None

        return {
            "data_type": status.data_type,
            "last_successful": status.last_successful,
            "last_attempted": status.last_attempted,
            "is_healthy": status.is_healthy,
            "error_message": status.error_message,
            "first_collection": status.first_collection,
        }

    def get_freshness(self, data_type: str) -> DataFreshness:
        """
        Get freshness information for a data type.

        Args:
            data_type: Type of data

        Returns:
            DataFreshness object with current freshness status
        """
        expected_lag = DATA_LAG_HOURS.get(data_type, DEFAULT_LAG_HOURS)
        status = self._collection_statuses.get(data_type)

        if status is None or status.last_successful is None:
            # No collection ever - return stale
            return DataFreshness(
                data_type=data_type,
                last_collection=datetime.min,
                expected_lag_hours=expected_lag,
                actual_lag_hours=float("inf"),
                is_stale=True,
                warning_message=f"No data collected for {data_type}. "
                f"Run data collection first.",
            )

        # Calculate actual lag
        now = datetime.now()
        actual_lag_hours = (now - status.last_successful).total_seconds() / 3600

        # Data is stale if we haven't collected within the expected refresh window
        # (i.e., actual time since collection exceeds expected data lag)
        is_stale = actual_lag_hours > expected_lag

        warning_message = None
        if is_stale:
            warning_message = (
                f"Data for {data_type} is stale. "
                f"Last collected {actual_lag_hours:.1f} hours ago "
                f"(expected refresh every {expected_lag} hours)."
            )

        return DataFreshness(
            data_type=data_type,
            last_collection=status.last_successful,
            expected_lag_hours=expected_lag,
            actual_lag_hours=actual_lag_hours,
            is_stale=is_stale,
            warning_message=warning_message,
        )

    def get_all_freshness(self) -> List[DataFreshness]:
        """
        Get freshness status for all tracked data types.

        Returns:
            List of DataFreshness objects
        """
        result = []

        # Include all tracked statuses
        for data_type in self._collection_statuses:
            result.append(self.get_freshness(data_type))

        # Also include known data types that aren't tracked yet
        for data_type in DATA_LAG_HOURS:
            if data_type not in self._collection_statuses:
                result.append(self.get_freshness(data_type))

        return result

    def get_safe_date_range(
        self,
        data_type: str,
        lookback_days: int,
    ) -> Tuple[date, date]:
        """
        Get a safe date range for analysis that accounts for data lag.

        Args:
            data_type: Type of data
            lookback_days: Number of days to look back

        Returns:
            Tuple of (start_date, end_date) that is safe to query
        """
        safe_end_datetime = self.get_safe_query_end_date(data_type)
        end_date = safe_end_datetime.date()
        start_date = end_date - timedelta(days=lookback_days)

        return (start_date, end_date)

    def has_minimum_observation_period(
        self,
        data_type: str,
        min_days: int,
    ) -> bool:
        """
        Check if we have minimum observation period for reliable recommendations.

        Args:
            data_type: Type of data
            min_days: Minimum number of days required

        Returns:
            True if observation period is sufficient
        """
        status = self._collection_statuses.get(data_type)

        if status is None or status.first_collection is None:
            return False

        observation_period = datetime.now() - status.first_collection
        return observation_period.days >= min_days
