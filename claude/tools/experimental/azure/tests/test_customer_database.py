"""
TDD Tests for Customer Database Manager (Multi-Tenant Isolation)

These tests ensure:
- Per-customer database isolation
- No cross-tenant data access
- Subscription ownership validation
- Proper file permissions

Tests written BEFORE implementation per TDD protocol.
Run with: pytest tests/test_customer_database.py -v
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Generator


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def customer_manager(temp_db_path: Path):
    """Create a CustomerDatabaseManager with temp path."""
    from claude.tools.experimental.azure.customer_database import CustomerDatabaseManager

    return CustomerDatabaseManager(base_path=temp_db_path)


class TestCustomerRegistration:
    """Tests for customer registration and database creation."""

    def test_register_customer_creates_database_file(self, customer_manager, temp_db_path):
        """Registering a customer should create an isolated database file."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="aus_e_mart",
            customer_name="Aus-E-Mart",
            tenant_ids=["63dff77c-b5c0-4308-85b0-d14caf72a671"],
            subscription_ids=["3681c5eb-0e60-4beb-96fa-0a067f6969ac"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Verify database file was created
        expected_db_path = temp_db_path / "customer_aus_e_mart.db"
        assert expected_db_path.exists(), f"Database file not created at {expected_db_path}"

    def test_register_customer_creates_system_db(self, customer_manager, temp_db_path):
        """Registering first customer should also create system database."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="test_customer",
            customer_name="Test Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["00000000-0000-0000-0000-000000000002"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Verify system database was created
        system_db_path = temp_db_path / "_system.db"
        assert system_db_path.exists(), "System database not created"

    def test_register_customer_adds_to_registry(self, customer_manager):
        """Registered customer should appear in customer list."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-002",
            customer_slug="nw_computing",
            customer_name="NW Computing",
            tenant_ids=["b8636094-b771-45d0-85ce-84e27c7baefb"],
            subscription_ids=[],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        customers = customer_manager.list_customers()
        slugs = [c.customer_slug for c in customers]
        assert "nw_computing" in slugs

    def test_register_duplicate_slug_raises_error(self, customer_manager):
        """Registering customer with duplicate slug should raise error."""
        from claude.tools.experimental.azure.customer_database import (
            Customer,
            CustomerDatabaseError,
        )

        customer1 = Customer(
            customer_id="cust-001",
            customer_slug="duplicate_slug",
            customer_name="First Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=[],
            created_at=datetime.now(),
        )

        customer2 = Customer(
            customer_id="cust-002",
            customer_slug="duplicate_slug",  # Same slug!
            customer_name="Second Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000002"],
            subscription_ids=[],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer1)

        with pytest.raises(CustomerDatabaseError) as exc_info:
            customer_manager.register_customer(customer2)

        assert "already exists" in str(exc_info.value).lower()


class TestDatabaseIsolation:
    """Tests for per-customer database isolation."""

    def test_customer_databases_are_separate_files(self, customer_manager, temp_db_path):
        """Each customer should have their own database file."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer_a = Customer(
            customer_id="cust-a",
            customer_slug="customer_a",
            customer_name="Customer A",
            tenant_ids=["00000000-0000-0000-0000-00000000000a"],
            subscription_ids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            created_at=datetime.now(),
        )

        customer_b = Customer(
            customer_id="cust-b",
            customer_slug="customer_b",
            customer_name="Customer B",
            tenant_ids=["00000000-0000-0000-0000-00000000000b"],
            subscription_ids=["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer_a)
        customer_manager.register_customer(customer_b)

        db_a = temp_db_path / "customer_customer_a.db"
        db_b = temp_db_path / "customer_customer_b.db"

        assert db_a.exists()
        assert db_b.exists()
        assert db_a != db_b

    def test_data_written_to_customer_a_not_visible_to_customer_b(self, customer_manager):
        """Data in Customer A's database should not be accessible from Customer B's database."""
        from claude.tools.experimental.azure.customer_database import Customer

        # Register two customers
        customer_a = Customer(
            customer_id="cust-a",
            customer_slug="customer_a",
            customer_name="Customer A",
            tenant_ids=["00000000-0000-0000-0000-00000000000a"],
            subscription_ids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            created_at=datetime.now(),
        )

        customer_b = Customer(
            customer_id="cust-b",
            customer_slug="customer_b",
            customer_name="Customer B",
            tenant_ids=["00000000-0000-0000-0000-00000000000b"],
            subscription_ids=["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer_a)
        customer_manager.register_customer(customer_b)

        # Write data to Customer A's database
        with customer_manager.get_customer_db("customer_a") as db_a:
            from claude.tools.experimental.azure.customer_database import Subscription

            sub = Subscription(
                subscription_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                subscription_name="Customer A Production",
                tenant_id="00000000-0000-0000-0000-00000000000a",
            )
            db_a.add_subscription(sub)

        # Verify Customer B cannot see Customer A's data
        with customer_manager.get_customer_db("customer_b") as db_b:
            subs = db_b.list_subscriptions()
            assert len(subs) == 0, "Customer B should not see Customer A's subscriptions"

    def test_get_customer_db_returns_isolated_instance(self, customer_manager):
        """get_customer_db should return database instance for that customer only."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="isolated_customer",
            customer_name="Isolated Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        with customer_manager.get_customer_db("isolated_customer") as db:
            # Verify the database is for the correct customer
            assert db.customer_slug == "isolated_customer"


class TestSubscriptionOwnershipValidation:
    """Tests for subscription ownership validation."""

    def test_validate_subscription_ownership_returns_true_for_owned(self, customer_manager):
        """Validation should return True for subscriptions owned by customer."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="owner_customer",
            customer_name="Owner Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=[
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            ],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        assert customer_manager.validate_subscription_ownership(
            "owner_customer", "11111111-1111-1111-1111-111111111111"
        )
        assert customer_manager.validate_subscription_ownership(
            "owner_customer", "22222222-2222-2222-2222-222222222222"
        )

    def test_validate_subscription_ownership_returns_false_for_unowned(self, customer_manager):
        """Validation should return False for subscriptions not owned by customer."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="limited_customer",
            customer_name="Limited Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Try to validate a subscription not in the customer's list
        assert not customer_manager.validate_subscription_ownership(
            "limited_customer", "99999999-9999-9999-9999-999999999999"
        )

    def test_validate_subscription_ownership_raises_for_unknown_customer(self, customer_manager):
        """Validation should raise error for unknown customer slug."""
        from claude.tools.experimental.azure.customer_database import CustomerDatabaseError

        with pytest.raises(CustomerDatabaseError) as exc_info:
            customer_manager.validate_subscription_ownership(
                "nonexistent_customer", "11111111-1111-1111-1111-111111111111"
            )

        assert "not found" in str(exc_info.value).lower()

    def test_get_customer_by_subscription_returns_correct_customer(self, customer_manager):
        """Should return the customer that owns a given subscription."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer_a = Customer(
            customer_id="cust-a",
            customer_slug="customer_a",
            customer_name="Customer A",
            tenant_ids=["00000000-0000-0000-0000-00000000000a"],
            subscription_ids=["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            created_at=datetime.now(),
        )

        customer_b = Customer(
            customer_id="cust-b",
            customer_slug="customer_b",
            customer_name="Customer B",
            tenant_ids=["00000000-0000-0000-0000-00000000000b"],
            subscription_ids=["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer_a)
        customer_manager.register_customer(customer_b)

        found_customer = customer_manager.get_customer_by_subscription(
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        )

        assert found_customer is not None
        assert found_customer.customer_slug == "customer_b"

    def test_get_customer_by_subscription_returns_none_for_unknown(self, customer_manager):
        """Should return None for subscription not belonging to any customer."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="only_customer",
            customer_name="Only Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        found = customer_manager.get_customer_by_subscription(
            "99999999-9999-9999-9999-999999999999"
        )

        assert found is None


class TestDatabaseFilePermissions:
    """Tests for database file security."""

    @pytest.mark.skipif(os.name == "nt", reason="File permissions work differently on Windows")
    def test_customer_database_has_restricted_permissions(self, customer_manager, temp_db_path):
        """Customer database files should have restricted permissions (0600)."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="secure_customer",
            customer_name="Secure Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        db_path = temp_db_path / "customer_secure_customer.db"
        mode = oct(db_path.stat().st_mode)[-3:]

        # Should be 600 (owner read/write only)
        assert mode == "600", f"Expected permissions 600, got {mode}"

    @pytest.mark.skipif(os.name == "nt", reason="File permissions work differently on Windows")
    def test_system_database_has_restricted_permissions(self, customer_manager, temp_db_path):
        """System database should have restricted permissions (0600)."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="any_customer",
            customer_name="Any Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=[],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        system_db_path = temp_db_path / "_system.db"
        mode = oct(system_db_path.stat().st_mode)[-3:]

        assert mode == "600", f"Expected permissions 600, got {mode}"


class TestSystemDatabase:
    """Tests for the system database (metadata, no customer data)."""

    def test_system_db_contains_customer_registry(self, customer_manager, temp_db_path):
        """System database should contain customer registry."""
        from claude.tools.experimental.azure.customer_database import Customer
        import sqlite3

        customer = Customer(
            customer_id="cust-001",
            customer_slug="registered_customer",
            customer_name="Registered Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Directly check system database
        system_db_path = temp_db_path / "_system.db"
        conn = sqlite3.connect(str(system_db_path))
        cursor = conn.execute("SELECT customer_slug FROM customers")
        slugs = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "registered_customer" in slugs

    def test_system_db_does_not_contain_customer_data(self, customer_manager, temp_db_path):
        """System database should NOT contain customer-specific data tables."""
        from claude.tools.experimental.azure.customer_database import Customer
        import sqlite3

        customer = Customer(
            customer_id="cust-001",
            customer_slug="data_customer",
            customer_name="Data Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Check that system database doesn't have customer data tables
        system_db_path = temp_db_path / "_system.db"
        conn = sqlite3.connect(str(system_db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        # System DB should NOT have these tables (they belong in customer DBs)
        forbidden_tables = ["cost_history", "resources", "recommendations", "resource_metrics"]
        for table in forbidden_tables:
            assert table not in tables, f"System DB should not contain '{table}' table"


class TestCustomerDatabaseContext:
    """Tests for customer database context manager."""

    def test_context_manager_closes_connection(self, customer_manager):
        """Context manager should properly close database connection."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="context_customer",
            customer_name="Context Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=[],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Use context manager
        with customer_manager.get_customer_db("context_customer") as db:
            # Do something with db
            pass

        # After context exits, connection should be closed
        # Accessing db outside context should fail or db should be closed
        assert db._conn is None or not db._conn

    def test_get_customer_db_for_unknown_customer_raises(self, customer_manager):
        """Getting database for unknown customer should raise error."""
        from claude.tools.experimental.azure.customer_database import CustomerDatabaseError

        with pytest.raises(CustomerDatabaseError) as exc_info:
            with customer_manager.get_customer_db("nonexistent_customer"):
                pass

        assert "not found" in str(exc_info.value).lower()


class TestAddSubscriptionToCustomer:
    """Tests for adding subscriptions to existing customers."""

    def test_add_subscription_to_customer(self, customer_manager):
        """Should be able to add subscription to existing customer."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="growing_customer",
            customer_name="Growing Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Add new subscription
        customer_manager.add_subscription_to_customer(
            "growing_customer", "22222222-2222-2222-2222-222222222222"
        )

        # Verify ownership
        assert customer_manager.validate_subscription_ownership(
            "growing_customer", "22222222-2222-2222-2222-222222222222"
        )

    def test_add_duplicate_subscription_is_idempotent(self, customer_manager):
        """Adding same subscription twice should be idempotent (no error)."""
        from claude.tools.experimental.azure.customer_database import Customer

        customer = Customer(
            customer_id="cust-001",
            customer_slug="idempotent_customer",
            customer_name="Idempotent Customer",
            tenant_ids=["00000000-0000-0000-0000-000000000001"],
            subscription_ids=["11111111-1111-1111-1111-111111111111"],
            created_at=datetime.now(),
        )

        customer_manager.register_customer(customer)

        # Add same subscription twice - should not raise
        customer_manager.add_subscription_to_customer(
            "idempotent_customer", "11111111-1111-1111-1111-111111111111"
        )
        customer_manager.add_subscription_to_customer(
            "idempotent_customer", "11111111-1111-1111-1111-111111111111"
        )

        # Still should only have one entry (no duplicates)
        customer = customer_manager.get_customer("idempotent_customer")
        assert customer.subscription_ids.count("11111111-1111-1111-1111-111111111111") == 1
