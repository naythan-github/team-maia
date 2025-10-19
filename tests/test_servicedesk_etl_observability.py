"""
Test Suite for ServiceDesk ETL Observability Infrastructure

TDD Test Suite - Created Before Implementation
Tests verify structured logging, metrics, and progress tracking.
"""

import pytest
import os
import sys
import json
import tempfile
from unittest import mock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestETLLogger:
    """Test structured logging functionality"""

    def test_etl_logger_creates_json_logs(self):
        """Verify logger creates structured JSON logs"""
        from claude.tools.sre.servicedesk_etl_observability import ETLLogger

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Test_Gate", log_file=log_file.name)
            logger.info("Test message", operation="test_op", duration_ms=123)

            # Read log file
            with open(log_file.name, 'r') as f:
                log_line = f.readline()
                log_data = json.loads(log_line)

            assert log_data['level'] == 'INFO'
            assert log_data['gate'] == 'Test_Gate'
            assert log_data['operation'] == 'test_op'
            assert log_data['duration_ms'] == 123
            assert 'timestamp' in log_data
        finally:
            os.unlink(log_file.name)

    def test_etl_logger_handles_multiple_levels(self):
        """Verify logger handles INFO, WARNING, ERROR levels"""
        from claude.tools.sre.servicedesk_etl_observability import ETLLogger

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Test_Gate", log_file=log_file.name)

            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            # Read all log lines
            with open(log_file.name, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 3

            levels = [json.loads(line)['level'] for line in lines]
            assert levels == ['INFO', 'WARNING', 'ERROR']
        finally:
            os.unlink(log_file.name)

    def test_etl_logger_includes_context_fields(self):
        """Verify logger includes custom context fields"""
        from claude.tools.sre.servicedesk_etl_observability import ETLLogger

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Gate1_Profiler", log_file=log_file.name)
            logger.info(
                "Processing batch",
                rows_processed=1000,
                batch_number=5,
                quality_score=85.5
            )

            with open(log_file.name, 'r') as f:
                log_data = json.loads(f.readline())

            assert log_data['rows_processed'] == 1000
            assert log_data['batch_number'] == 5
            assert log_data['quality_score'] == 85.5
        finally:
            os.unlink(log_file.name)


class TestETLMetrics:
    """Test metrics emission functionality"""

    def test_etl_metrics_records_values(self):
        """Verify metrics records values correctly"""
        from claude.tools.sre.servicedesk_etl_observability import ETLMetrics

        metrics = ETLMetrics()

        metrics.record('profiler_duration_seconds', 45.2)
        metrics.record('quality_score_pre_cleaning', 72.5)
        metrics.record('rows_cleaned', 260000)

        assert metrics.get('profiler_duration_seconds') == 45.2
        assert metrics.get('quality_score_pre_cleaning') == 72.5
        assert metrics.get('rows_cleaned') == 260000

    def test_etl_metrics_emits_prometheus_format(self):
        """Verify metrics can be emitted in Prometheus format"""
        from claude.tools.sre.servicedesk_etl_observability import ETLMetrics

        metrics = ETLMetrics()
        metrics.record('profiler_duration_seconds', 45.2)
        metrics.record('cleaner_duration_seconds', 120.5)
        metrics.record('rows_migrated', 260000)

        prom_output = metrics.emit_prometheus()

        assert 'profiler_duration_seconds 45.2' in prom_output
        assert 'cleaner_duration_seconds 120.5' in prom_output
        assert 'rows_migrated 260000' in prom_output

    def test_etl_metrics_emits_json_format(self):
        """Verify metrics can be emitted in JSON format"""
        from claude.tools.sre.servicedesk_etl_observability import ETLMetrics

        metrics = ETLMetrics()
        metrics.record('errors_total', 5)
        metrics.record('quality_score_post_migration', 95.2)

        json_output = metrics.emit_json()
        data = json.loads(json_output)

        assert data['errors_total'] == 5
        assert data['quality_score_post_migration'] == 95.2
        assert 'timestamp' in data

    def test_etl_metrics_increments_counters(self):
        """Verify metrics can increment counters"""
        from claude.tools.sre.servicedesk_etl_observability import ETLMetrics

        metrics = ETLMetrics()

        metrics.increment('errors_total')
        metrics.increment('errors_total')
        metrics.increment('errors_total')

        assert metrics.get('errors_total') == 3

    def test_etl_metrics_writes_to_file(self):
        """Verify metrics can be written to file"""
        from claude.tools.sre.servicedesk_etl_observability import ETLMetrics

        metrics_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        metrics_file.close()

        try:
            metrics = ETLMetrics()
            metrics.record('test_metric', 42)
            metrics.write_to_file(metrics_file.name)

            with open(metrics_file.name, 'r') as f:
                data = json.load(f)

            assert data['test_metric'] == 42
        finally:
            os.unlink(metrics_file.name)


class TestProgressTracker:
    """Test progress tracking functionality"""

    def test_progress_tracker_calculates_percentage(self):
        """Verify progress tracker calculates completion percentage"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker

        tracker = ProgressTracker(total_rows=260000)
        tracker.update(rows_processed=130000)

        progress = tracker.get_progress()

        assert progress['percent_complete'] == 50.0
        assert progress['processed_rows'] == 130000
        assert progress['total_rows'] == 260000

    def test_progress_tracker_estimates_eta(self):
        """Verify progress tracker estimates time remaining"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker
        import time

        tracker = ProgressTracker(total_rows=1000)

        # Simulate processing
        time.sleep(0.1)
        tracker.update(rows_processed=100)

        progress = tracker.get_progress()

        assert 'eta_seconds' in progress
        assert progress['eta_seconds'] > 0
        assert 'eta_human' in progress

    def test_progress_tracker_calculates_rate(self):
        """Verify progress tracker calculates rows per second"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker
        import time

        tracker = ProgressTracker(total_rows=1000)

        time.sleep(0.1)
        tracker.update(rows_processed=50)

        progress = tracker.get_progress()

        assert 'rows_per_second' in progress
        assert progress['rows_per_second'] > 0

    def test_progress_tracker_emits_to_file(self):
        """Verify progress can be written to JSON file"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker

        progress_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        progress_file.close()

        try:
            tracker = ProgressTracker(total_rows=1000)
            tracker.update(rows_processed=250)
            tracker.emit_progress(progress_file.name)

            with open(progress_file.name, 'r') as f:
                data = json.load(f)

            assert data['percent_complete'] == 25.0
            assert data['processed_rows'] == 250
        finally:
            os.unlink(progress_file.name)

    def test_progress_tracker_handles_completion(self):
        """Verify progress tracker handles 100% completion"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker

        tracker = ProgressTracker(total_rows=100)
        tracker.update(rows_processed=100)

        progress = tracker.get_progress()

        assert progress['percent_complete'] == 100.0
        assert progress['eta_seconds'] == 0

    def test_progress_tracker_formats_human_readable_eta(self):
        """Verify ETA is formatted in human-readable format"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker

        tracker = ProgressTracker(total_rows=1000)

        # Mock elapsed time and rate to get predictable ETA
        tracker.start_time = tracker.start_time - 10  # 10 seconds ago
        tracker.processed = 100

        progress = tracker.get_progress()

        # Should show minutes and seconds
        assert 'eta_human' in progress
        assert 's' in progress['eta_human']  # Contains seconds


class TestHealthChecks:
    """Test health check functionality"""

    def test_check_connection_health_detects_alive_connection(self):
        """Verify health check detects alive connection"""
        from claude.tools.sre.servicedesk_etl_observability import check_connection_health

        # Mock connection that is alive
        mock_conn = mock.MagicMock()
        mock_conn.closed = 0  # PostgreSQL connection not closed

        result = check_connection_health(mock_conn)

        assert result['healthy'] is True
        assert result['connection_alive'] is True

    def test_check_connection_health_detects_dead_connection(self):
        """Verify health check detects dead connection"""
        from claude.tools.sre.servicedesk_etl_observability import check_connection_health

        # Mock closed connection
        mock_conn = mock.MagicMock()
        mock_conn.closed = 1  # PostgreSQL connection closed

        result = check_connection_health(mock_conn)

        assert result['healthy'] is False
        assert result['connection_alive'] is False

    def test_check_disk_space_health(self):
        """Verify health check monitors disk space"""
        from claude.tools.sre.servicedesk_etl_observability import check_disk_space_health

        with mock.patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = mock.MagicMock(
                free=5 * 1024**3,  # 5GB free
                total=100 * 1024**3
            )

            result = check_disk_space_health(threshold_gb=1.0)

            assert result['healthy'] is True
            assert result['free_gb'] == 5.0

    def test_check_disk_space_health_warns_on_low_space(self):
        """Verify health check warns on low disk space"""
        from claude.tools.sre.servicedesk_etl_observability import check_disk_space_health

        with mock.patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = mock.MagicMock(
                free=500 * 1024**2,  # 500MB free
                total=100 * 1024**3
            )

            result = check_disk_space_health(threshold_gb=1.0)

            assert result['healthy'] is False
            assert result['free_gb'] < 1.0

    def test_check_memory_health(self):
        """Verify health check monitors memory usage"""
        from claude.tools.sre.servicedesk_etl_observability import check_memory_health

        with mock.patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = mock.MagicMock(
                percent=65.0,
                available=4 * 1024**3
            )

            result = check_memory_health(threshold_percent=90)

            assert result['healthy'] is True
            assert result['percent_used'] == 65.0

    def test_check_memory_health_warns_on_high_usage(self):
        """Verify health check warns on high memory usage"""
        from claude.tools.sre.servicedesk_etl_observability import check_memory_health

        with mock.patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = mock.MagicMock(
                percent=95.0,
                available=500 * 1024**2
            )

            result = check_memory_health(threshold_percent=90)

            assert result['healthy'] is False
            assert result['percent_used'] == 95.0


class TestObservabilityIntegration:
    """Integration tests for observability components"""

    def test_combined_logging_and_metrics(self):
        """Verify logger and metrics work together"""
        from claude.tools.sre.servicedesk_etl_observability import ETLLogger, ETLMetrics

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Integration_Test", log_file=log_file.name)
            metrics = ETLMetrics()

            # Simulate workflow
            logger.info("Starting profiler")
            metrics.record('profiler_start_time', datetime.now().isoformat())

            logger.info("Profiler complete", duration_ms=5000)
            metrics.record('profiler_duration_seconds', 5.0)

            # Verify both captured data
            with open(log_file.name, 'r') as f:
                logs = [json.loads(line) for line in f.readlines()]

            assert len(logs) == 2
            assert logs[0]['message'] == 'Starting profiler'
            assert logs[1]['duration_ms'] == 5000

            assert metrics.get('profiler_duration_seconds') == 5.0
        finally:
            os.unlink(log_file.name)

    def test_progress_tracking_with_logging(self):
        """Verify progress tracking integrates with logging"""
        from claude.tools.sre.servicedesk_etl_observability import ProgressTracker, ETLLogger

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Progress_Test", log_file=log_file.name)
            tracker = ProgressTracker(total_rows=1000)

            # Log progress at intervals
            for i in range(0, 1001, 250):
                tracker.update(rows_processed=i)
                progress = tracker.get_progress()
                logger.info(
                    f"Progress: {progress['percent_complete']}%",
                    **progress
                )

            # Verify logs captured progress
            with open(log_file.name, 'r') as f:
                logs = [json.loads(line) for line in f.readlines()]

            assert len(logs) == 5  # 0, 250, 500, 750, 1000
            assert logs[-1]['percent_complete'] == 100.0
        finally:
            os.unlink(log_file.name)

    def test_observability_performance_overhead(self):
        """Verify observability has minimal performance impact (<1ms per call)"""
        import time
        from claude.tools.sre.servicedesk_etl_observability import ETLLogger, ETLMetrics, ProgressTracker

        log_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        log_file.close()

        try:
            logger = ETLLogger(name="Perf_Test", log_file=log_file.name)
            metrics = ETLMetrics()
            tracker = ProgressTracker(total_rows=1000)

            # Measure 100 operations
            start = time.time()
            for i in range(100):
                logger.info("Test", iteration=i)
                metrics.record('test_metric', i)
                tracker.update(rows_processed=i)
            elapsed_ms = (time.time() - start) * 1000

            # Should be fast (<100ms for 100 operations = <1ms each)
            assert elapsed_ms < 100, f"Observability overhead too high: {elapsed_ms}ms"
        finally:
            os.unlink(log_file.name)
