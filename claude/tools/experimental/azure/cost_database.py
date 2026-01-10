"""
Azure Cost Optimization Database Manager

Manages SQLite database for cost optimization platform.
Supports: cost history, resource inventory, recommendations, ML predictions

TDD Implementation - Tests in tests/test_cost_database.py
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class CostDatabaseError(Exception):
    """Raised when database operations fail."""
    pass


@dataclass
class Subscription:
    """Subscription record."""
    subscription_id: str
    subscription_name: str
    tenant_id: str
    tenant_name: Optional[str] = None
    state: str = "Enabled"
    is_customer: bool = False
    customer_name: Optional[str] = None
    monthly_budget: Optional[float] = None
    last_scanned: Optional[datetime] = None


@dataclass
class Recommendation:
    """Recommendation record."""
    subscription_id: str
    category: str
    source: str
    type: str
    title: str
    recommendation: str
    recommendation_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_group: Optional[str] = None
    impact: Optional[str] = None
    description: Optional[str] = None
    estimated_savings_monthly: Optional[float] = None
    estimated_savings_annual: Optional[float] = None
    confidence_score: float = 0.5
    status: str = "Active"
    implementation_effort: Optional[str] = None
    risk_level: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CostRecord:
    """Cost history record."""
    subscription_id: str
    date: Union[date, str]
    cost: float
    resource_group: Optional[str] = None
    service_name: Optional[str] = None
    resource_id: Optional[str] = None
    currency: str = "USD"
    meter_category: Optional[str] = None
    meter_subcategory: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class CostOptimizationDB:
    """
    Manages Azure cost optimization database.

    Usage:
        db = CostOptimizationDB()
        db.add_subscription(subscription)
        db.add_recommendation(recommendation)
        results = db.get_top_recommendations(subscription_id, limit=10)
    """

    DEFAULT_DB_PATH = Path.home() / ".maia" / "databases" / "azure_cost_optimization.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file (default: ~/.maia/databases/azure_cost_optimization.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = None
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _initialize_database(self):
        """Initialize database schema if not exists."""
        schema_path = Path(__file__).parent / "cost_optimization_schema.sql"

        if not schema_path.exists():
            raise CostDatabaseError(f"Schema file not found: {schema_path}")

        try:
            conn = self._get_connection()
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            conn.executescript(schema_sql)
            conn.commit()

            logger.info(f"Database initialized: {self.db_path}")

        except Exception as e:
            raise CostDatabaseError(f"Failed to initialize database: {e}") from e

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    def add_subscription(self, subscription: Subscription) -> None:
        """Add or update subscription."""
        try:
            conn = self._get_connection()

            conn.execute("""
                INSERT OR REPLACE INTO subscriptions (
                    subscription_id, subscription_name, tenant_id, tenant_name,
                    state, is_customer, customer_name, monthly_budget, last_scanned
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription.subscription_id,
                subscription.subscription_name,
                subscription.tenant_id,
                subscription.tenant_name,
                subscription.state,
                subscription.is_customer,
                subscription.customer_name,
                subscription.monthly_budget,
                subscription.last_scanned
            ))

            conn.commit()
            logger.debug(f"Added subscription: {subscription.subscription_id}")

        except Exception as e:
            raise CostDatabaseError(f"Failed to add subscription: {e}") from e

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM subscriptions WHERE subscription_id = ?",
                (subscription_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            raise CostDatabaseError(f"Failed to get subscription: {e}") from e

    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================

    def add_recommendation(self, rec: Recommendation) -> int:
        """Add recommendation and return ID."""
        try:
            conn = self._get_connection()

            # Generate recommendation_id if not provided
            if not rec.recommendation_id:
                import uuid
                rec.recommendation_id = str(uuid.uuid4())

            # Convert metadata dict to JSON
            metadata_json = json.dumps(rec.metadata) if rec.metadata else None

            cursor = conn.execute("""
                INSERT OR REPLACE INTO recommendations (
                    recommendation_id, subscription_id, resource_id, resource_group,
                    category, source, type, impact, title, description, recommendation,
                    estimated_savings_monthly, estimated_savings_annual, confidence_score,
                    status, implementation_effort, risk_level, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec.recommendation_id,
                rec.subscription_id,
                rec.resource_id,
                rec.resource_group,
                rec.category,
                rec.source,
                rec.type,
                rec.impact,
                rec.title,
                rec.description,
                rec.recommendation,
                rec.estimated_savings_monthly,
                rec.estimated_savings_annual,
                rec.confidence_score,
                rec.status,
                rec.implementation_effort,
                rec.risk_level,
                metadata_json
            ))

            conn.commit()
            logger.debug(f"Added recommendation: {rec.recommendation_id}")
            return cursor.lastrowid

        except Exception as e:
            raise CostDatabaseError(f"Failed to add recommendation: {e}") from e

    def get_top_recommendations(
        self,
        subscription_id: Optional[str] = None,
        limit: int = 10,
        min_savings: float = 0
    ) -> List[Dict[str, Any]]:
        """Get top recommendations by estimated savings."""
        try:
            conn = self._get_connection()

            query = """
                SELECT * FROM v_top_recommendations
                WHERE estimated_savings_annual >= ?
            """
            params = [min_savings]

            if subscription_id:
                query += " AND subscription_id = ?"
                params.append(subscription_id)

            query += " LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            raise CostDatabaseError(f"Failed to get top recommendations: {e}") from e

    def update_recommendation_status(
        self,
        recommendation_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> None:
        """Update recommendation status (Active, Dismissed, Implemented, Expired)."""
        try:
            conn = self._get_connection()

            timestamp_field = None
            if status == "Dismissed":
                timestamp_field = "dismissed_at"
            elif status == "Implemented":
                timestamp_field = "implemented_at"

            if timestamp_field:
                conn.execute(f"""
                    UPDATE recommendations
                    SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP
                    WHERE recommendation_id = ?
                """, (status, recommendation_id))
            else:
                conn.execute("""
                    UPDATE recommendations
                    SET status = ?
                    WHERE recommendation_id = ?
                """, (status, recommendation_id))

            conn.commit()
            logger.debug(f"Updated recommendation {recommendation_id} to {status}")

        except Exception as e:
            raise CostDatabaseError(f"Failed to update recommendation status: {e}") from e

    # ========================================================================
    # COST HISTORY
    # ========================================================================

    def add_cost_record(self, record: CostRecord) -> None:
        """Add cost history record."""
        try:
            conn = self._get_connection()

            # Convert date to string if needed
            record_date = record.date if isinstance(record.date, str) else record.date.isoformat()

            # Convert tags dict to JSON
            tags_json = json.dumps(record.tags) if record.tags else None

            conn.execute("""
                INSERT OR REPLACE INTO cost_history (
                    subscription_id, date, resource_group, service_name, resource_id,
                    cost, currency, meter_category, meter_subcategory, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.subscription_id,
                record_date,
                record.resource_group,
                record.service_name,
                record.resource_id,
                record.cost,
                record.currency,
                record.meter_category,
                record.meter_subcategory,
                tags_json
            ))

            conn.commit()

        except Exception as e:
            raise CostDatabaseError(f"Failed to add cost record: {e}") from e

    def get_monthly_costs(
        self,
        subscription_id: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get monthly cost summary."""
        try:
            conn = self._get_connection()

            cursor = conn.execute("""
                SELECT * FROM v_monthly_costs
                WHERE subscription_id = ?
                ORDER BY month DESC
                LIMIT ?
            """, (subscription_id, months))

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            raise CostDatabaseError(f"Failed to get monthly costs: {e}") from e

    # ========================================================================
    # RESOURCES
    # ========================================================================

    def add_resource(
        self,
        resource_id: str,
        subscription_id: str,
        resource_group: str,
        resource_name: str,
        resource_type: str,
        location: Optional[str] = None,
        sku: Optional[str] = None,
        size: Optional[str] = None,
        state: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add or update resource."""
        try:
            conn = self._get_connection()

            tags_json = json.dumps(tags) if tags else None
            properties_json = json.dumps(properties) if properties else None

            conn.execute("""
                INSERT OR REPLACE INTO resources (
                    resource_id, subscription_id, resource_group, resource_name,
                    resource_type, location, sku, size, state, tags, properties,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                resource_id, subscription_id, resource_group, resource_name,
                resource_type, location, sku, size, state, tags_json, properties_json
            ))

            conn.commit()

        except Exception as e:
            raise CostDatabaseError(f"Failed to add resource: {e}") from e

    def get_orphaned_resources(
        self,
        subscription_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get orphaned resources (unattached disks, idle IPs, etc.)."""
        try:
            conn = self._get_connection()

            query = "SELECT * FROM v_orphaned_resources"
            params = []

            if subscription_id:
                query += " WHERE subscription_id = ?"
                params.append(subscription_id)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            raise CostDatabaseError(f"Failed to get orphaned resources: {e}") from e

    # ========================================================================
    # METRICS
    # ========================================================================

    def add_metric(
        self,
        resource_id: str,
        metric_name: str,
        timestamp: Union[datetime, str],
        value: float,
        aggregation: str = "Average",
        unit: Optional[str] = None
    ) -> None:
        """Add resource performance metric."""
        try:
            conn = self._get_connection()

            timestamp_str = timestamp if isinstance(timestamp, str) else timestamp.isoformat()

            conn.execute("""
                INSERT INTO resource_metrics (
                    resource_id, metric_name, timestamp, value, aggregation, unit
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (resource_id, metric_name, timestamp_str, value, aggregation, unit))

            conn.commit()

        except Exception as e:
            raise CostDatabaseError(f"Failed to add metric: {e}") from e

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def get_savings_summary(
        self,
        subscription_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get savings potential summary."""
        try:
            conn = self._get_connection()

            query = """
                SELECT
                    COUNT(*) as total_recommendations,
                    SUM(estimated_savings_monthly) as monthly_savings,
                    SUM(estimated_savings_annual) as annual_savings,
                    SUM(CASE WHEN implementation_effort = 'Low' THEN estimated_savings_annual ELSE 0 END) as quick_wins,
                    COUNT(CASE WHEN impact = 'High' THEN 1 END) as high_impact_count
                FROM recommendations
                WHERE status = 'Active'
            """
            params = []

            if subscription_id:
                query += " AND subscription_id = ?"
                params.append(subscription_id)

            cursor = conn.execute(query, params)
            row = cursor.fetchone()

            return dict(row) if row else {}

        except Exception as e:
            raise CostDatabaseError(f"Failed to get savings summary: {e}") from e

    def store_advisor_recommendation(
        self,
        recommendation_id: str,
        subscription_id: str,
        resource_id: Optional[str],
        category: str,
        impact: str,
        problem: str,
        solution: str,
        estimated_savings: Optional[float],
        extended_properties: Dict[str, Any],
    ) -> None:
        """
        Store or update Azure Advisor recommendation.

        Args:
            recommendation_id: Advisor recommendation ID
            subscription_id: Azure subscription ID
            resource_id: Resource ID (None for subscription-level)
            category: Recommendation category (e.g., 'Cost')
            impact: Impact level ('High', 'Medium', 'Low')
            problem: Problem description
            solution: Solution description
            estimated_savings: Estimated monthly savings
            extended_properties: Additional properties from Advisor
        """
        try:
            conn = self._get_connection()

            # Convert to Recommendation dataclass format
            recommendation = Recommendation(
                subscription_id=subscription_id,
                category=category,
                source="Azure Advisor",
                type="Advisor",
                title=problem,
                recommendation=solution,
                recommendation_id=recommendation_id,
                resource_id=resource_id,
                impact=impact,
                estimated_savings_monthly=estimated_savings,
                estimated_savings_annual=estimated_savings * 12 if estimated_savings else None,
                metadata=extended_properties,
                status="Active",
            )

            self.add_recommendation(recommendation)

            logger.info(f"Stored Advisor recommendation {recommendation_id}")

        except Exception as e:
            raise CostDatabaseError(f"Failed to store Advisor recommendation: {e}") from e

    def store_resource(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        location: Optional[str],
        resource_group: str,
        subscription_id: str,
        tags: Optional[Dict[str, str]],
        properties: Optional[Dict[str, Any]],
    ) -> None:
        """
        Store or update resource from Azure Resource Graph.

        Args:
            resource_id: Azure resource ID
            resource_name: Resource name
            resource_type: Resource type (e.g., 'Microsoft.Compute/virtualMachines')
            location: Azure region
            resource_group: Resource group name
            subscription_id: Azure subscription ID
            tags: Resource tags
            properties: Resource properties from Resource Graph
        """
        try:
            conn = self._get_connection()

            # Check if resources table exists, create if needed
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    location TEXT,
                    resource_group TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    tags TEXT,
                    properties TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert or update
            conn.execute("""
                INSERT INTO resources (
                    resource_id, resource_name, resource_type, location,
                    resource_group, subscription_id, tags, properties
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(resource_id) DO UPDATE SET
                    resource_name = excluded.resource_name,
                    resource_type = excluded.resource_type,
                    location = excluded.location,
                    resource_group = excluded.resource_group,
                    subscription_id = excluded.subscription_id,
                    tags = excluded.tags,
                    properties = excluded.properties,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                resource_id,
                resource_name,
                resource_type,
                location,
                resource_group,
                subscription_id,
                json.dumps(tags) if tags else None,
                json.dumps(properties) if properties else None,
            ))

            conn.commit()

            logger.debug(f"Stored resource {resource_id}")

        except Exception as e:
            raise CostDatabaseError(f"Failed to store resource: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions

def get_db(db_path: Optional[Path] = None) -> CostOptimizationDB:
    """Get database instance."""
    return CostOptimizationDB(db_path)


def main():
    """CLI interface for database operations."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Azure Cost Optimization Database Manager")
    parser.add_argument("--db-path", type=Path, help="Database file path")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Initialize
    subparsers.add_parser("init", help="Initialize database")

    # Stats
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("--subscription-id", help="Filter by subscription")

    # Top recommendations
    top_parser = subparsers.add_parser("top", help="Show top recommendations")
    top_parser.add_argument("--subscription-id", help="Filter by subscription")
    top_parser.add_argument("--limit", type=int, default=10, help="Number of recommendations")

    args = parser.parse_args()

    try:
        db = CostOptimizationDB(args.db_path)

        if args.command == "init":
            print(f"Database initialized: {db.db_path}")
            return 0

        elif args.command == "stats":
            summary = db.get_savings_summary(args.subscription_id)
            print(json.dumps(summary, indent=2))
            return 0

        elif args.command == "top":
            recs = db.get_top_recommendations(args.subscription_id, args.limit)
            print(json.dumps(recs, indent=2, default=str))
            return 0

        else:
            parser.print_help()
            return 0

    except CostDatabaseError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())
