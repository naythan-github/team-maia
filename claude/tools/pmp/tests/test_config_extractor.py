#!/usr/bin/env python3
"""
PMP Configuration Extractor - Comprehensive Test Suite (TDD)
Following Test-Driven Development: Write tests BEFORE implementation

Test Coverage:
- Unit Tests: OAuth integration, data extraction, validation, compliance rules
- Integration Tests: Full workflow (API → DB → Compliance → Excel)
- Performance Tests: Extraction speed, query performance, report generation
- Error Handling Tests: API failures, token expiry, rate limiting

Author: Patch Manager Plus API Specialist Agent + SRE Principal Engineer Agent
Date: 2025-11-25
"""

import unittest
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Import modules to test (will be implemented in Phase 5-7)
try:
    from claude.tools.pmp.pmp_config_extractor import PMPConfigExtractor
    from claude.tools.pmp.pmp_compliance_analyzer import PMPComplianceAnalyzer
    from claude.tools.pmp.pmp_report_generator import PMPReportGenerator
    from claude.tools.pmp.pmp_oauth_manager import PMPOAuthManager
except ImportError:
    # Modules not yet implemented - tests will be skipped with @unittest.skipIf
    PMPConfigExtractor = None
    PMPComplianceAnalyzer = None
    PMPReportGenerator = None
    PMPOAuthManager = Mock  # OAuth manager exists from Phase 187


class TestOAuthIntegration(unittest.TestCase):
    """Test OAuth integration with existing pmp_oauth_manager.py"""

    @unittest.skipIf(PMPOAuthManager is Mock, "OAuth manager not available")
    def test_oauth_manager_instantiation(self):
        """Test OAuth manager can be instantiated"""
        manager = PMPOAuthManager()
        self.assertIsNotNone(manager)
        self.assertTrue(hasattr(manager, 'api_request'))

    @unittest.skipIf(PMPOAuthManager is Mock, "OAuth manager not available")
    def test_oauth_token_refresh_handling(self):
        """Test OAuth manager handles token refresh on 401 errors"""
        manager = PMPOAuthManager()
        # Token refresh is handled in api_request() method with _retry_count guard
        self.assertTrue(hasattr(manager, 'refresh_access_token'))
        self.assertTrue(hasattr(manager, 'get_valid_token'))

    @unittest.skipIf(PMPOAuthManager is Mock, "OAuth manager not available")
    def test_oauth_rate_limiting(self):
        """Test OAuth manager enforces rate limiting (3000 req/5min)"""
        manager = PMPOAuthManager()
        self.assertTrue(hasattr(manager, '_check_rate_limit'))
        self.assertEqual(manager.rate_limit, 3000)
        self.assertEqual(manager.rate_window, 300)


class TestConfigExtractor(unittest.TestCase):
    """Test PMP configuration extraction engine"""

    def setUp(self):
        """Setup test database and mock OAuth manager"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"

    def tearDown(self):
        """Cleanup test database"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_extractor_initialization(self):
        """Test extractor initializes with OAuth manager and database"""
        extractor = PMPConfigExtractor(db_path=self.test_db)
        self.assertIsNotNone(extractor.oauth_manager)
        self.assertTrue(self.test_db.exists())

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_api_summary_extraction(self):
        """Test extraction from /api/1.4/patch/summary endpoint"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        # Mock API response
        mock_response = {
            "message_response": {
                "summary": {
                    "patch_summary": {
                        "installed_patches": 3566,
                        "applicable_patches": 5301,
                        "new_patches": 34362,
                        "missing_patches": 1735
                    },
                    "missing_patch_severity_summary": {
                        "critical_count": 139,
                        "important_count": 452,
                        "moderate_count": 549,
                        "low_count": 60,
                        "unrated_count": 534,
                        "total_count": 1734
                    },
                    "system_summary": {
                        "total_systems": 3358,
                        "healthy_systems": 1721,
                        "moderately_vulnerable_systems": 308,
                        "highly_vulnerable_systems": 1300,
                        "health_unknown_systems": 29
                    },
                    "patch_scan_summary": {
                        "scanned_systems": 3320,
                        "unscanned_system_count": 38,
                        "scan_success_count": 3295,
                        "scan_failure_count": 25
                    },
                    "vulnerability_db_summary": {
                        "last_db_update_status": "Success",
                        "last_db_update_time": 1764052565661,
                        "is_auto_db_update_disabled": True,
                        "db_update_in_progress": False
                    },
                    "apd_summary": {
                        "number_of_apd_tasks": 70
                    }
                }
            },
            "status": "success"
        }

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            mock_api.return_value.json.return_value = mock_response
            mock_api.return_value.status_code = 200

            snapshot_id = extractor.extract_snapshot()
            self.assertIsNotNone(snapshot_id)
            self.assertGreater(snapshot_id, 0)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_data_validation_schema(self):
        """Test data validation ensures all required fields present"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        # Test valid data passes validation
        valid_data = {
            "patch_summary": {"installed_patches": 100, "missing_patches": 10},
            "severity_summary": {"critical_count": 5, "important_count": 3},
            "system_summary": {"total_systems": 50, "healthy_systems": 40}
        }
        self.assertTrue(extractor.validate_data(valid_data))

        # Test invalid data fails validation (missing required field)
        invalid_data = {
            "patch_summary": {"installed_patches": 100}  # missing_patches missing
        }
        self.assertFalse(extractor.validate_data(invalid_data))

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_data_validation_ranges(self):
        """Test data validation checks value ranges"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        # Test negative counts fail validation
        invalid_data = {
            "patch_summary": {"installed_patches": -10, "missing_patches": 5}
        }
        self.assertFalse(extractor.validate_data(invalid_data))

        # Test zero values pass validation (valid state)
        valid_data = {
            "patch_summary": {"installed_patches": 0, "missing_patches": 0}
        }
        self.assertTrue(extractor.validate_data(valid_data))

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_data_validation_consistency(self):
        """Test data validation checks internal consistency"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        # Test severity counts sum to total
        valid_data = {
            "severity_summary": {
                "critical_count": 10,
                "important_count": 20,
                "moderate_count": 30,
                "low_count": 5,
                "unrated_count": 5,
                "total_count": 70  # Sum matches
            }
        }
        self.assertTrue(extractor.validate_data(valid_data))

        # Test mismatched sum fails validation
        invalid_data = {
            "severity_summary": {
                "critical_count": 10,
                "important_count": 20,
                "moderate_count": 30,
                "low_count": 5,
                "unrated_count": 5,
                "total_count": 100  # Sum doesn't match (should be 70)
            }
        }
        self.assertFalse(extractor.validate_data(invalid_data))


class TestDatabaseOperations(unittest.TestCase):
    """Test SQLite database operations"""

    def setUp(self):
        """Setup test database"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"

    def tearDown(self):
        """Cleanup test database"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_database_schema_creation(self):
        """Test database schema is created with all required tables"""
        extractor = PMPConfigExtractor(db_path=self.test_db)
        extractor.init_database()

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Check all 5 tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {
            'snapshots',
            'patch_metrics',
            'severity_metrics',
            'system_health_metrics',
            'compliance_checks'
        }
        self.assertTrue(required_tables.issubset(tables))

        conn.close()

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_database_indexes_created(self):
        """Test database indexes are created for performance"""
        extractor = PMPConfigExtractor(db_path=self.test_db)
        extractor.init_database()

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        required_indexes = {
            'idx_snapshot_timestamp',
            'idx_patch_metrics_snapshot',
            'idx_severity_metrics_snapshot',
            'idx_system_health_snapshot',
            'idx_compliance_snapshot'
        }
        self.assertTrue(required_indexes.issubset(indexes))

        conn.close()

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_snapshot_insert(self):
        """Test snapshot can be inserted and retrieved"""
        extractor = PMPConfigExtractor(db_path=self.test_db)
        extractor.init_database()

        snapshot_id = extractor.create_snapshot(status='success', duration_ms=4200)
        self.assertIsNotNone(snapshot_id)
        self.assertGreater(snapshot_id, 0)

        # Verify snapshot was inserted
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        conn.close()

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_metrics_insert(self):
        """Test all metrics tables can be populated"""
        extractor = PMPConfigExtractor(db_path=self.test_db)
        extractor.init_database()

        snapshot_id = extractor.create_snapshot(status='success', duration_ms=4200)

        # Insert patch metrics
        extractor.insert_patch_metrics(snapshot_id, {
            'installed_patches': 3566,
            'applicable_patches': 5301,
            'new_patches': 34362,
            'missing_patches': 1735
        })

        # Insert severity metrics
        extractor.insert_severity_metrics(snapshot_id, {
            'critical_count': 139,
            'important_count': 452,
            'moderate_count': 549,
            'low_count': 60,
            'unrated_count': 534
        })

        # Insert system health metrics
        extractor.insert_system_health_metrics(snapshot_id, {
            'total_systems': 3358,
            'healthy_systems': 1721,
            'moderately_vulnerable_systems': 308,
            'highly_vulnerable_systems': 1300,
            'health_unknown_systems': 29,
            'scanned_systems': 3320,
            'unscanned_system_count': 38,
            'scan_success_count': 3295,
            'scan_failure_count': 25
        })

        # Verify all metrics inserted
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patch_metrics WHERE snapshot_id = ?", (snapshot_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT COUNT(*) FROM severity_metrics WHERE snapshot_id = ?", (snapshot_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT COUNT(*) FROM system_health_metrics WHERE snapshot_id = ?", (snapshot_id,))
        self.assertEqual(cursor.fetchone()[0], 1)

        conn.close()


class TestComplianceAnalyzer(unittest.TestCase):
    """Test compliance rule evaluation engine"""

    def setUp(self):
        """Setup test database with sample data"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"

    def tearDown(self):
        """Cleanup test database"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_essential_eight_critical_patches(self):
        """Test Essential Eight L2/3: Critical patches within 48h rule"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 5 critical patches (threshold <= 5)
        result = analyzer.check_essential_eight_critical_patches(critical_count=5)
        self.assertTrue(result.passed)
        self.assertEqual(result.severity, 'CRITICAL')
        self.assertEqual(result.category, 'essential_eight')

        # Test FAIL: 10 critical patches (threshold <= 5)
        result = analyzer.check_essential_eight_critical_patches(critical_count=10)
        self.assertFalse(result.passed)
        self.assertIn('10 critical', result.details.lower())

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_essential_eight_important_patches(self):
        """Test Essential Eight L2/3: Important patches within 30 days rule"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 50 important patches (threshold <= 50)
        result = analyzer.check_essential_eight_important_patches(important_count=50)
        self.assertTrue(result.passed)

        # Test FAIL: 100 important patches (threshold <= 50)
        result = analyzer.check_essential_eight_important_patches(important_count=100)
        self.assertFalse(result.passed)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_essential_eight_vulnerability_rate(self):
        """Test Essential Eight L2: System vulnerability rate <= 5%"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 100 highly vulnerable out of 3000 systems (3.3%)
        result = analyzer.check_system_vulnerability_rate(
            highly_vulnerable_systems=100,
            total_systems=3000
        )
        self.assertTrue(result.passed)

        # Test FAIL: 200 highly vulnerable out of 3000 systems (6.7%)
        result = analyzer.check_system_vulnerability_rate(
            highly_vulnerable_systems=200,
            total_systems=3000
        )
        self.assertFalse(result.passed)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_essential_eight_scan_coverage(self):
        """Test Essential Eight L1: Scan coverage >= 95%"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 3200 scanned out of 3358 systems (95.3%)
        result = analyzer.check_scan_coverage(
            scanned_systems=3200,
            total_systems=3358
        )
        self.assertTrue(result.passed)

        # Test FAIL: 3000 scanned out of 3358 systems (89.3%)
        result = analyzer.check_scan_coverage(
            scanned_systems=3000,
            total_systems=3358
        )
        self.assertFalse(result.passed)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_cis_control_7_1(self):
        """Test CIS Control 7.1: Vulnerability scanning deployed (95% coverage)"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        result = analyzer.check_cis_7_1_scan_deployment(
            scanned_systems=3200,
            total_systems=3358
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.category, 'cis')

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_cis_control_7_2(self):
        """Test CIS Control 7.2: Critical patches remediated (0 critical within 30 days)"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 0 critical patches
        result = analyzer.check_cis_7_2_critical_remediation(critical_count=0)
        self.assertTrue(result.passed)

        # Test FAIL: 5 critical patches
        result = analyzer.check_cis_7_2_critical_remediation(critical_count=5)
        self.assertFalse(result.passed)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_custom_healthy_system_ratio(self):
        """Test Custom MSP Rule: Healthy system ratio >= 60%"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        # Test PASS: 2100 healthy out of 3358 systems (62.5%)
        result = analyzer.check_healthy_system_ratio(
            healthy_systems=2100,
            total_systems=3358
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.category, 'custom')

        # Test FAIL: 1500 healthy out of 3358 systems (44.7%)
        result = analyzer.check_healthy_system_ratio(
            healthy_systems=1500,
            total_systems=3358
        )
        self.assertFalse(result.passed)

    @unittest.skipIf(PMPComplianceAnalyzer is None, "Analyzer not yet implemented")
    def test_run_all_compliance_checks(self):
        """Test running all compliance checks returns results for all rules"""
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)

        snapshot_data = {
            'critical_count': 5,
            'important_count': 40,
            'highly_vulnerable_systems': 100,
            'total_systems': 3358,
            'scanned_systems': 3200,
            'healthy_systems': 2100,
            'scan_success_count': 3150,
            'unscanned_system_count': 30,
            'number_of_apd_tasks': 50
        }

        results = analyzer.run_all_checks(snapshot_data)

        # Should return results for all compliance checks (10+ rules)
        self.assertGreaterEqual(len(results), 10)

        # Each result should have required fields
        for result in results:
            self.assertIsNotNone(result.check_name)
            self.assertIsNotNone(result.category)
            self.assertIn(result.severity, ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
            self.assertIsInstance(result.passed, bool)


class TestExcelReportGenerator(unittest.TestCase):
    """Test Excel report generation"""

    def setUp(self):
        """Setup test database and output directory"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"
        self.output_dir = Path(self.test_dir) / "reports"
        self.output_dir.mkdir()

    def tearDown(self):
        """Cleanup test files"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPReportGenerator is None, "Generator not yet implemented")
    def test_compliance_dashboard_generation(self):
        """Test compliance dashboard Excel report is generated"""
        generator = PMPReportGenerator(db_path=self.test_db)

        report_path = generator.generate_compliance_dashboard(
            output_dir=self.output_dir,
            days=30
        )

        self.assertTrue(report_path.exists())
        self.assertEqual(report_path.suffix, '.xlsx')
        self.assertLess(report_path.stat().st_size, 10 * 1024 * 1024)  # < 10 MB

    @unittest.skipIf(PMPReportGenerator is None, "Generator not yet implemented")
    def test_compliance_dashboard_worksheets(self):
        """Test compliance dashboard contains all required worksheets"""
        generator = PMPReportGenerator(db_path=self.test_db)

        report_path = generator.generate_compliance_dashboard(
            output_dir=self.output_dir,
            days=30
        )

        # Load Excel file and check worksheets
        import openpyxl
        workbook = openpyxl.load_workbook(report_path)

        required_worksheets = {
            'Executive Summary',
            'Trend Charts',
            'Compliance Checks',
            'Severity Analysis',
            'Recommendations'
        }
        actual_worksheets = set(workbook.sheetnames)

        self.assertTrue(required_worksheets.issubset(actual_worksheets))

    @unittest.skipIf(PMPReportGenerator is None, "Generator not yet implemented")
    def test_trend_analysis_report(self):
        """Test trend analysis report generation"""
        generator = PMPReportGenerator(db_path=self.test_db)

        report_path = generator.generate_trend_analysis(
            output_dir=self.output_dir,
            days=90
        )

        self.assertTrue(report_path.exists())
        self.assertEqual(report_path.suffix, '.xlsx')

    @unittest.skipIf(PMPReportGenerator is None, "Generator not yet implemented")
    def test_report_generation_performance(self):
        """Test report generation completes within 30 seconds"""
        generator = PMPReportGenerator(db_path=self.test_db)

        start_time = time.time()
        report_path = generator.generate_compliance_dashboard(
            output_dir=self.output_dir,
            days=90
        )
        duration = time.time() - start_time

        self.assertLess(duration, 30.0)  # Must complete in <30 seconds


class TestErrorHandling(unittest.TestCase):
    """Test error handling and retry logic"""

    def setUp(self):
        """Setup test database"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"

    def tearDown(self):
        """Cleanup test database"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_401_token_refresh_handling(self):
        """Test 401 error triggers token refresh and retry"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            # First call returns 401, second call succeeds
            mock_api.side_effect = [
                Mock(status_code=401, text='{"error":"Unauthorized"}'),
                Mock(status_code=200, json=lambda: {"message_response": {"summary": {}}})
            ]

            # Should retry after 401 and succeed
            result = extractor.extract_snapshot()
            self.assertEqual(mock_api.call_count, 2)  # Initial + retry

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_429_rate_limit_handling(self):
        """Test 429 error respects Retry-After header"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            # First call returns 429 with Retry-After: 60
            mock_429 = Mock(status_code=429, headers={'Retry-After': '5'})
            mock_200 = Mock(status_code=200, json=lambda: {"message_response": {"summary": {}}})

            mock_api.side_effect = [mock_429, mock_200]

            # Should wait and retry
            start_time = time.time()
            result = extractor.extract_snapshot()
            duration = time.time() - start_time

            self.assertGreaterEqual(duration, 4.0)  # Should wait ~5 seconds
            self.assertEqual(mock_api.call_count, 2)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_500_server_error_retry(self):
        """Test 500 errors are retried with exponential backoff"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            # Two 500 errors, then success
            mock_500 = Mock(status_code=500, text='Internal Server Error')
            mock_200 = Mock(status_code=200, json=lambda: {"message_response": {"summary": {}}})

            mock_api.side_effect = [mock_500, mock_500, mock_200]

            result = extractor.extract_snapshot()
            self.assertEqual(mock_api.call_count, 3)  # 2 failures + 1 success

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_timeout_partial_snapshot(self):
        """Test API timeout creates partial snapshot with status='partial'"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            mock_api.side_effect = TimeoutError("API timeout after 30 seconds")

            snapshot_id = extractor.extract_snapshot()

            # Should create snapshot with status='partial'
            conn = sqlite3.connect(self.test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            status = cursor.fetchone()[0]
            conn.close()

            self.assertEqual(status, 'partial')

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_consecutive_failures_alert(self):
        """Test 3 consecutive failures triggers alert"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        with patch.object(extractor.oauth_manager, 'api_request') as mock_api:
            mock_api.side_effect = Exception("API unavailable")

            # Simulate 3 consecutive failures
            for i in range(3):
                try:
                    extractor.extract_snapshot()
                except Exception:
                    pass

            # Should have logged alert condition
            self.assertTrue(extractor.should_alert_consecutive_failures())


class TestPerformance(unittest.TestCase):
    """Test performance requirements"""

    def setUp(self):
        """Setup test database with sample data"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"

    def tearDown(self):
        """Cleanup test database"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_extraction_performance(self):
        """Test full extraction completes in <10 seconds"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        start_time = time.time()
        snapshot_id = extractor.extract_snapshot()
        duration = time.time() - start_time

        self.assertLess(duration, 10.0)
        self.assertIsNotNone(snapshot_id)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_database_insert_performance(self):
        """Test database insert completes in <100ms"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        snapshot_id = extractor.create_snapshot(status='success', duration_ms=5000)

        start_time = time.time()
        extractor.insert_patch_metrics(snapshot_id, {
            'installed_patches': 3566,
            'applicable_patches': 5301,
            'new_patches': 34362,
            'missing_patches': 1735
        })
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        self.assertLess(duration, 100.0)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_query_performance_30_days(self):
        """Test 30-day trend query completes in <50ms"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        # Insert 30 snapshots (simulate daily extractions)
        for i in range(30):
            snapshot_id = extractor.create_snapshot(status='success', duration_ms=5000)
            extractor.insert_patch_metrics(snapshot_id, {
                'installed_patches': 3566 + i,
                'missing_patches': 1735 - i
            })

        # Query last 30 days
        start_time = time.time()
        results = extractor.get_trend_data(days=30)
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        self.assertLess(duration, 50.0)
        self.assertEqual(len(results), 30)

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_database_growth_rate(self):
        """Test database growth ~5 KB per snapshot"""
        extractor = PMPConfigExtractor(db_path=self.test_db)

        initial_size = self.test_db.stat().st_size

        # Insert 10 snapshots
        for i in range(10):
            snapshot_id = extractor.create_snapshot(status='success', duration_ms=5000)
            extractor.insert_patch_metrics(snapshot_id, {'installed_patches': 3566})
            extractor.insert_severity_metrics(snapshot_id, {'critical_count': 139})
            extractor.insert_system_health_metrics(snapshot_id, {'total_systems': 3358})

        final_size = self.test_db.stat().st_size
        growth_per_snapshot = (final_size - initial_size) / 10

        # Should be ~5 KB per snapshot (allow 2-8 KB range for SQLite overhead)
        self.assertGreater(growth_per_snapshot, 2000)  # > 2 KB
        self.assertLess(growth_per_snapshot, 8000)     # < 8 KB


class TestIntegrationWorkflow(unittest.TestCase):
    """Test full end-to-end workflow"""

    def setUp(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = Path(self.test_dir) / "test_pmp_config.db"
        self.output_dir = Path(self.test_dir) / "reports"
        self.output_dir.mkdir()

    def tearDown(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir)

    @unittest.skipIf(any(x is None for x in [PMPConfigExtractor, PMPComplianceAnalyzer, PMPReportGenerator]),
                     "Integration components not yet implemented")
    def test_full_workflow_extract_analyze_report(self):
        """Test complete workflow: API → DB → Compliance → Excel"""
        # Phase 1: Extract configuration
        extractor = PMPConfigExtractor(db_path=self.test_db)
        snapshot_id = extractor.extract_snapshot()
        self.assertIsNotNone(snapshot_id)

        # Phase 2: Analyze compliance
        analyzer = PMPComplianceAnalyzer(db_path=self.test_db)
        compliance_results = analyzer.analyze_snapshot(snapshot_id)
        self.assertGreater(len(compliance_results), 0)

        # Phase 3: Generate Excel report
        generator = PMPReportGenerator(db_path=self.test_db)
        report_path = generator.generate_compliance_dashboard(
            output_dir=self.output_dir,
            days=30
        )
        self.assertTrue(report_path.exists())

        # Verify end-to-end workflow completed successfully
        self.assertLess(report_path.stat().st_size, 10 * 1024 * 1024)  # < 10 MB

    @unittest.skipIf(PMPConfigExtractor is None, "Extractor not yet implemented")
    def test_concurrent_extraction_handling(self):
        """Test concurrent extractions are prevented (lock file)"""
        extractor1 = PMPConfigExtractor(db_path=self.test_db)
        extractor2 = PMPConfigExtractor(db_path=self.test_db)

        # Start first extraction (should acquire lock)
        with patch.object(extractor1.oauth_manager, 'api_request'):
            # Simulate long-running extraction
            import threading
            lock_acquired = threading.Event()

            def extract1():
                extractor1.extract_snapshot()
                lock_acquired.set()

            thread1 = threading.Thread(target=extract1)
            thread1.start()

            # Second extraction should fail with lock error
            with self.assertRaises(RuntimeError) as context:
                extractor2.extract_snapshot()

            self.assertIn('lock', str(context.exception).lower())
            thread1.join()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
