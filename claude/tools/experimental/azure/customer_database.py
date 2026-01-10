"""
Customer Database Manager for Multi-Tenant Isolation

Manages per-customer database isolation for the Azure Cost Optimization Platform.
Each customer gets their own SQLite database file to ensure complete data separation.

Key Security Features:
- Per-customer database files (no shared tables)
- Subscription ownership validation
- Restricted file permissions (0600)
- System database separate from customer data

TDD Implementation - Tests in tests/test_customer_database.py
"""

import os
import sqlite3
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager
import logging

from claude.tools.experimental.azure.validators import (
    validate_subscription_id,
    validate_tenant_id,
    validate_customer_slug,
)

logger = logging.getLogger(__name__)


class CustomerDatabaseError(Exception):
    """Raised when customer database operations fail."""
    pass


@dataclass
class Customer:
    """Customer registry entry."""
    customer_id: str
    customer_slug: str
    customer_name: str
    tenant_ids: List[str]
    subscription_ids: List[str]
    created_at: datetime
    is_active: bool = True


@dataclass
class Subscription:
    """Subscription record for a customer database."""
    subscription_id: str
    subscription_name: str
    tenant_id: str
    tenant_name: Optional[str] = None
    state: str = "Enabled"
    monthly_budget: Optional[float] = None
    last_scanned: Optional[datetime] = None


class CustomerDatabase:
    """
    Isolated database for a single customer.

    This class provides access to a customer's isolated database.
    It should only be obtained through CustomerDatabaseManager.get_customer_db().
    """

    def __init__(self, db_path: Path, customer_slug: str):
        """
        Initialize customer database.

        Args:
            db_path: Path to the SQLite database file
            customer_slug: Customer identifier
        """
        self.db_path = db_path
        self.customer_slug = customer_slug
        self._conn: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_subscription(self, subscription: Subscription) -> None:
        """Add or update a subscription."""
        conn = self._get_connection()
        try:
            # Validate subscription ID format
            validate_subscription_id(subscription.subscription_id)
            validate_tenant_id(subscription.tenant_id)

            conn.execute("""
                INSERT OR REPLACE INTO subscriptions (
                    subscription_id, subscription_name, tenant_id, tenant_name,
                    state, monthly_budget, last_scanned
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription.subscription_id,
                subscription.subscription_name,
                subscription.tenant_id,
                subscription.tenant_name,
                subscription.state,
                subscription.monthly_budget,
                subscription.last_scanned.isoformat() if subscription.last_scanned else None,
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise CustomerDatabaseError(f"Failed to add subscription: {e}") from e

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """List all subscriptions in this customer's database."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM subscriptions")
        return [dict(row) for row in cursor.fetchall()]

    def store_resource(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        location: str,
        resource_group: str,
        subscription_id: str,
        tags: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store or update a resource in the database.

        Args:
            resource_id: Full Azure resource ID
            resource_name: Resource name
            resource_type: Resource type (e.g., Microsoft.Compute/virtualMachines)
            location: Azure region
            resource_group: Resource group name
            subscription_id: Azure subscription ID
            tags: Resource tags (optional)
            properties: Additional resource properties (optional)
        """
        import json
        conn = self._get_connection()
        try:
            # Convert tags dict to JSON string
            tags_json = json.dumps(tags) if tags else None

            conn.execute("""
                INSERT INTO resources (
                    resource_id, resource_name, resource_type, location,
                    resource_group, subscription_id, tags, last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(resource_id) DO UPDATE SET
                    resource_name = excluded.resource_name,
                    resource_type = excluded.resource_type,
                    location = excluded.location,
                    resource_group = excluded.resource_group,
                    tags = excluded.tags,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                resource_id, resource_name, resource_type, location,
                resource_group, subscription_id, tags_json
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise CustomerDatabaseError(f"Failed to store resource: {e}") from e

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
        extended_properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store an Azure Advisor recommendation in the database.

        Args:
            recommendation_id: Unique recommendation ID
            subscription_id: Azure subscription ID
            resource_id: Affected resource ID (optional)
            category: Recommendation category (Cost, Security, etc.)
            impact: Impact level (High, Medium, Low)
            problem: Problem description
            solution: Recommended solution
            estimated_savings: Monthly savings estimate (USD)
            extended_properties: Additional metadata (optional)
        """
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO recommendations (
                    recommendation_id, subscription_id, resource_id, category,
                    source, type, impact, title, recommendation,
                    estimated_savings_monthly, estimated_savings_annual, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(recommendation_id) DO UPDATE SET
                    status = excluded.status,
                    estimated_savings_monthly = excluded.estimated_savings_monthly,
                    estimated_savings_annual = excluded.estimated_savings_annual
            """, (
                recommendation_id,
                subscription_id,
                resource_id,
                category,
                'AzureAdvisor',  # source
                category,  # type
                impact,
                problem,  # title
                solution,  # recommendation text
                estimated_savings,  # monthly
                estimated_savings * 12 if estimated_savings else None,  # annual
                'Active'
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise CustomerDatabaseError(f"Failed to store recommendation: {e}") from e

    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get all recommendations from the database.

        Returns:
            List of recommendation dictionaries
        """
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM recommendations
            ORDER BY estimated_savings_monthly DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class CustomerDatabaseManager:
    """
    Manages per-customer database isolation.

    Each customer gets their own SQLite database file.
    The system database (_system.db) contains only the customer registry,
    not any customer-specific data.

    Usage:
        manager = CustomerDatabaseManager()
        manager.register_customer(customer)

        with manager.get_customer_db("customer_slug") as db:
            db.add_subscription(sub)
    """

    DEFAULT_BASE_PATH = Path.home() / ".maia" / "databases" / "azure_cost_optimization"

    # Schema for customer databases
    CUSTOMER_DB_SCHEMA = """
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id TEXT PRIMARY KEY,
            subscription_name TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            tenant_name TEXT,
            state TEXT DEFAULT 'Enabled',
            monthly_budget REAL,
            last_scanned TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cost_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id TEXT NOT NULL,
            date DATE NOT NULL,
            resource_group TEXT,
            service_name TEXT,
            resource_id TEXT,
            cost REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resources (
            resource_id TEXT PRIMARY KEY,
            subscription_id TEXT NOT NULL,
            resource_group TEXT NOT NULL,
            resource_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            location TEXT,
            sku TEXT,
            state TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id TEXT UNIQUE,
            subscription_id TEXT NOT NULL,
            resource_id TEXT,
            category TEXT NOT NULL,
            source TEXT NOT NULL,
            type TEXT NOT NULL,
            impact TEXT,
            title TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            estimated_savings_monthly REAL,
            estimated_savings_annual REAL,
            confidence_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resource_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            value REAL NOT NULL,
            aggregation TEXT DEFAULT 'Average',
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resource_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT NOT NULL UNIQUE,
            classification TEXT NOT NULL,
            business_criticality TEXT,
            source TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            decommission_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS workload_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_schedule TEXT,
            confidence REAL NOT NULL,
            observation_days INTEGER DEFAULT 30,
            peak_hours TEXT,
            is_validated INTEGER DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS data_collection_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL UNIQUE,
            last_successful TIMESTAMP,
            last_attempted TIMESTAMP,
            data_lag_hours REAL,
            is_healthy INTEGER DEFAULT 1,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_cost_history_date ON cost_history(subscription_id, date);
        CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type);
        CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status, subscription_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_resource ON resource_metrics(resource_id, metric_name);
    """

    # Schema for system database (NO customer data)
    SYSTEM_DB_SCHEMA = """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            customer_slug TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            tenant_ids TEXT NOT NULL,
            subscription_ids TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ml_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            model_type TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model_name, model_version)
        );

        CREATE TABLE IF NOT EXISTS data_lag_config (
            data_source TEXT PRIMARY KEY,
            typical_lag_hours REAL NOT NULL,
            max_lag_hours REAL NOT NULL,
            notes TEXT
        );

        INSERT OR IGNORE INTO data_lag_config VALUES
            ('azure_cost_management', 48, 72, 'Cost data 24-72h behind'),
            ('azure_monitor', 4, 8, 'Metrics 1-4h behind'),
            ('azure_advisor', 24, 48, 'Advisor refreshes daily'),
            ('azure_resource_graph', 1, 2, 'Near real-time');

        CREATE INDEX IF NOT EXISTS idx_customers_slug ON customers(customer_slug);
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize customer database manager.

        Args:
            base_path: Base directory for database files
        """
        self.base_path = base_path or self.DEFAULT_BASE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)

        self._system_db_path = self.base_path / "_system.db"
        self._system_conn: Optional[sqlite3.Connection] = None
        self._ensure_system_db()

    def _ensure_system_db(self):
        """Ensure system database exists and is initialized."""
        if not self._system_db_path.exists():
            self._init_system_db()

    def _init_system_db(self):
        """Initialize the system database."""
        conn = sqlite3.connect(str(self._system_db_path))
        try:
            conn.executescript(self.SYSTEM_DB_SCHEMA)
            conn.commit()
        finally:
            conn.close()

        # Set restricted permissions
        self._set_restricted_permissions(self._system_db_path)

    def _set_restricted_permissions(self, path: Path):
        """Set file permissions to 0600 (owner read/write only)."""
        try:
            os.chmod(path, 0o600)
        except OSError as e:
            logger.warning(f"Could not set permissions on {path}: {e}")

    def _get_system_conn(self) -> sqlite3.Connection:
        """Get connection to system database."""
        if self._system_conn is None:
            self._system_conn = sqlite3.connect(str(self._system_db_path))
            self._system_conn.row_factory = sqlite3.Row
        return self._system_conn

    def _get_customer_db_path(self, customer_slug: str) -> Path:
        """Get path to customer database file."""
        return self.base_path / f"customer_{customer_slug}.db"

    def register_customer(self, customer: Customer) -> None:
        """
        Register a new customer and create their isolated database.

        Args:
            customer: Customer details

        Raises:
            CustomerDatabaseError: If customer slug already exists
        """
        # Validate slug
        validate_customer_slug(customer.customer_slug)

        # Validate tenant/subscription IDs
        for tid in customer.tenant_ids:
            validate_tenant_id(tid)
        for sid in customer.subscription_ids:
            validate_subscription_id(sid)

        conn = self._get_system_conn()

        # Check for duplicate slug
        cursor = conn.execute(
            "SELECT customer_slug FROM customers WHERE customer_slug = ?",
            (customer.customer_slug,)
        )
        if cursor.fetchone():
            raise CustomerDatabaseError(
                f"Customer with slug '{customer.customer_slug}' already exists"
            )

        try:
            # Add to registry
            conn.execute("""
                INSERT INTO customers (
                    customer_id, customer_slug, customer_name,
                    tenant_ids, subscription_ids, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.customer_id,
                customer.customer_slug,
                customer.customer_name,
                json.dumps(customer.tenant_ids),
                json.dumps(customer.subscription_ids),
                1 if customer.is_active else 0,
                customer.created_at.isoformat(),
            ))
            conn.commit()

            # Create customer database
            self._create_customer_db(customer.customer_slug)

            logger.info(f"Registered customer: {customer.customer_slug}")

        except Exception as e:
            conn.rollback()
            raise CustomerDatabaseError(f"Failed to register customer: {e}") from e

    def _create_customer_db(self, customer_slug: str) -> None:
        """Create and initialize a customer database."""
        db_path = self._get_customer_db_path(customer_slug)

        conn = sqlite3.connect(str(db_path))
        try:
            conn.executescript(self.CUSTOMER_DB_SCHEMA)
            conn.commit()
        finally:
            conn.close()

        # Set restricted permissions
        self._set_restricted_permissions(db_path)

    def list_customers(self, active_only: bool = True) -> List[Customer]:
        """
        List registered customers.

        Args:
            active_only: If True, only return active customers

        Returns:
            List of Customer objects
        """
        conn = self._get_system_conn()

        query = "SELECT * FROM customers"
        if active_only:
            query += " WHERE is_active = 1"

        cursor = conn.execute(query)
        customers = []

        for row in cursor.fetchall():
            customers.append(Customer(
                customer_id=row["customer_id"],
                customer_slug=row["customer_slug"],
                customer_name=row["customer_name"],
                tenant_ids=json.loads(row["tenant_ids"]),
                subscription_ids=json.loads(row["subscription_ids"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                is_active=bool(row["is_active"]),
            ))

        return customers

    def get_customer(self, customer_slug: str) -> Optional[Customer]:
        """
        Get customer by slug.

        Args:
            customer_slug: Customer identifier

        Returns:
            Customer object or None if not found
        """
        conn = self._get_system_conn()
        cursor = conn.execute(
            "SELECT * FROM customers WHERE customer_slug = ?",
            (customer_slug,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        return Customer(
            customer_id=row["customer_id"],
            customer_slug=row["customer_slug"],
            customer_name=row["customer_name"],
            tenant_ids=json.loads(row["tenant_ids"]),
            subscription_ids=json.loads(row["subscription_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            is_active=bool(row["is_active"]),
        )

    @contextmanager
    def get_customer_db(self, customer_slug: str) -> Generator[CustomerDatabase, None, None]:
        """
        Get isolated database instance for a customer.

        Args:
            customer_slug: Customer identifier

        Yields:
            CustomerDatabase instance

        Raises:
            CustomerDatabaseError: If customer not found
        """
        # Verify customer exists
        customer = self.get_customer(customer_slug)
        if not customer:
            raise CustomerDatabaseError(f"Customer '{customer_slug}' not found")

        db_path = self._get_customer_db_path(customer_slug)
        if not db_path.exists():
            raise CustomerDatabaseError(f"Database for customer '{customer_slug}' not found")

        db = CustomerDatabase(db_path, customer_slug)
        try:
            yield db
        finally:
            db.close()

    def validate_subscription_ownership(
        self,
        customer_slug: str,
        subscription_id: str
    ) -> bool:
        """
        Verify subscription belongs to customer.

        Args:
            customer_slug: Customer identifier
            subscription_id: Azure subscription ID

        Returns:
            True if subscription belongs to customer, False otherwise

        Raises:
            CustomerDatabaseError: If customer not found
        """
        customer = self.get_customer(customer_slug)
        if not customer:
            raise CustomerDatabaseError(f"Customer '{customer_slug}' not found")

        return subscription_id in customer.subscription_ids

    def get_customer_by_subscription(
        self,
        subscription_id: str
    ) -> Optional[Customer]:
        """
        Find customer that owns a subscription.

        Args:
            subscription_id: Azure subscription ID

        Returns:
            Customer object or None if not found
        """
        for customer in self.list_customers():
            if subscription_id in customer.subscription_ids:
                return customer
        return None

    def add_subscription_to_customer(
        self,
        customer_slug: str,
        subscription_id: str
    ) -> None:
        """
        Add a subscription to an existing customer.

        Args:
            customer_slug: Customer identifier
            subscription_id: Azure subscription ID to add

        Raises:
            CustomerDatabaseError: If customer not found
        """
        # Validate subscription ID
        validate_subscription_id(subscription_id)

        customer = self.get_customer(customer_slug)
        if not customer:
            raise CustomerDatabaseError(f"Customer '{customer_slug}' not found")

        # Check if already added (idempotent)
        if subscription_id in customer.subscription_ids:
            return

        # Update subscription list
        new_subscription_ids = customer.subscription_ids + [subscription_id]

        conn = self._get_system_conn()
        try:
            conn.execute("""
                UPDATE customers
                SET subscription_ids = ?, updated_at = ?
                WHERE customer_slug = ?
            """, (
                json.dumps(new_subscription_ids),
                datetime.now().isoformat(),
                customer_slug,
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise CustomerDatabaseError(f"Failed to add subscription: {e}") from e

    def close(self):
        """Close all database connections."""
        if self._system_conn:
            self._system_conn.close()
            self._system_conn = None
