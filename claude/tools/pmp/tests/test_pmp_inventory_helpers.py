"""
Tests for pmp_api_inventory.py helper functions.

TDD: Phase 4 refactoring - decompose run_full_inventory (149 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctionsExist:
    """RED: Verify helper functions exist after refactoring."""

    def test_get_endpoint_definitions_exists(self):
        """Helper for getting endpoint configuration."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        assert hasattr(inventory, '_get_endpoint_definitions')
        assert callable(inventory._get_endpoint_definitions)

    def test_test_all_endpoints_exists(self):
        """Helper for testing all endpoints."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        assert hasattr(inventory, '_test_all_endpoints')
        assert callable(inventory._test_all_endpoints)

    def test_print_inventory_summary_exists(self):
        """Helper for printing inventory summary."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        assert hasattr(inventory, '_print_inventory_summary')
        assert callable(inventory._print_inventory_summary)


class TestGetEndpointDefinitions:
    """Test _get_endpoint_definitions helper."""

    def test_returns_dict(self):
        """Should return a dictionary of endpoint configs."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        endpoints = inventory._get_endpoint_definitions()
        assert isinstance(endpoints, dict)

    def test_contains_required_endpoints(self):
        """Should include core endpoints."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        endpoints = inventory._get_endpoint_definitions()

        # Must have these core endpoints
        assert 'System Inventory' in endpoints
        assert 'All Patches' in endpoints
        assert 'Missing Patches' in endpoints

    def test_endpoint_structure(self):
        """Each endpoint should have required keys."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)
        endpoints = inventory._get_endpoint_definitions()

        for name, config in endpoints.items():
            assert 'endpoint' in config, f"{name} missing 'endpoint'"
            assert 'description' in config, f"{name} missing 'description'"
            assert config['endpoint'].startswith('/'), f"{name} endpoint should start with /"


class TestTestAllEndpoints:
    """Test _test_all_endpoints helper."""

    def test_returns_results_and_counts(self):
        """Should return results dict and count tuple."""
        from pmp_api_inventory import PMPAPIInventory

        # Create mock inventory without calling __init__
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)

        # Mock test_endpoint method
        inventory.test_endpoint = MagicMock(return_value={
            'status': 'success',
            'total_records': 10,
            'all_fields': ['field1', 'field2'],
            'response_time_ms': 50.0
        })

        # Mock endpoint definitions
        endpoints = {
            'Test Endpoint': {
                'endpoint': '/api/test',
                'description': 'Test',
                'params': {}
            }
        }

        # Patch time.sleep to speed up test
        with patch('time.sleep'):
            results, counts = inventory._test_all_endpoints(endpoints)

        assert isinstance(results, dict)
        assert isinstance(counts, tuple)
        assert len(counts) == 3  # success, empty, error
        assert counts[0] == 1  # 1 success


class TestPrintInventorySummary:
    """Test _print_inventory_summary helper."""

    def test_prints_counts(self, capsys):
        """Should print summary statistics."""
        from pmp_api_inventory import PMPAPIInventory
        inventory = PMPAPIInventory.__new__(PMPAPIInventory)

        inventory._print_inventory_summary(
            total_endpoints=10,
            success_count=7,
            empty_count=2,
            error_count=1
        )

        captured = capsys.readouterr()
        assert 'SUMMARY' in captured.out
        assert '10' in captured.out  # total
        assert '7' in captured.out   # success
