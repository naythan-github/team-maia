#!/usr/bin/env python3
"""
ServiceDesk ETL Observability Infrastructure

Provides structured logging, metrics emission, and progress tracking.
Part of Phase 0 - Prerequisites for V2 SRE-Hardened ETL Pipeline.

Features:
    - Structured JSON logging with context fields
    - Prometheus-style metrics emission
    - Real-time progress tracking with ETA
    - Health checks (connection, disk, memory)
    - Minimal performance overhead (<1ms per operation)

Usage:
    from servicedesk_etl_observability import ETLLogger, ETLMetrics, ProgressTracker

    logger = ETLLogger("Gate1_Profiler")
    metrics = ETLMetrics()
    progress = ProgressTracker(total_rows=260000)

    logger.info("Starting profiler", operation="type_detection")
    metrics.record("profiler_duration_seconds", 45.2)
    progress.update(rows_processed=1000)
"""

import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    print("WARNING: psutil not installed, memory checks unavailable", file=sys.stderr)
    psutil = None


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    """

    def __init__(self, gate_name: str):
        super().__init__()
        self.gate_name = gate_name

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'gate': self.gate_name,
            'message': record.getMessage()
        }

        # Add custom fields from extra
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ETLLogger:
    """
    Structured JSON logger for ETL pipeline.

    Provides consistent logging format across all ETL gates with
    contextual information and minimal overhead.
    """

    def __init__(self, name: str, log_file: Optional[str] = None, level: int = logging.INFO):
        """
        Initialize ETL logger.

        Args:
            name: Logger name (typically gate name like "Gate1_Profiler")
            log_file: Optional log file path (default: stdout)
            level: Logging level (default: INFO)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers
        self.logger.handlers = []

        # Add handler with JSON formatter
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler(sys.stdout)

        handler.setFormatter(JSONFormatter(name))
        self.logger.addHandler(handler)

    def _log(self, level: int, message: str, **kwargs):
        """
        Internal logging method with context fields.

        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context fields
        """
        # Create a log record with extra fields
        extra = {'extra_fields': kwargs}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs):
        """
        Log INFO level message.

        Args:
            message: Log message
            **kwargs: Additional context fields (operation, duration_ms, etc.)
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """
        Log WARNING level message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """
        Log ERROR level message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        self._log(logging.ERROR, message, **kwargs)


class ETLMetrics:
    """
    Metrics collection and emission for ETL pipeline.

    Supports Prometheus-style metrics and JSON export.
    """

    def __init__(self):
        """Initialize metrics collection."""
        self.metrics: Dict[str, float] = {}
        self.start_time = time.time()

    def record(self, metric_name: str, value: float):
        """
        Record a metric value.

        Args:
            metric_name: Metric name (e.g., 'profiler_duration_seconds')
            value: Metric value
        """
        self.metrics[metric_name] = value

    def get(self, metric_name: str) -> Optional[float]:
        """
        Get metric value.

        Args:
            metric_name: Metric name

        Returns:
            Metric value or None if not found
        """
        return self.metrics.get(metric_name)

    def increment(self, metric_name: str, amount: float = 1.0):
        """
        Increment a counter metric.

        Args:
            metric_name: Metric name
            amount: Amount to increment (default: 1.0)
        """
        current = self.metrics.get(metric_name, 0.0)
        self.metrics[metric_name] = current + amount

    def emit_prometheus(self) -> str:
        """
        Emit metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        for metric_name, value in self.metrics.items():
            lines.append(f"{metric_name} {value}")
        return '\n'.join(lines)

    def emit_json(self) -> str:
        """
        Emit metrics in JSON format.

        Returns:
            JSON-formatted metrics string
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            **self.metrics
        }
        return json.dumps(data)

    def write_to_file(self, file_path: str):
        """
        Write metrics to JSON file.

        Args:
            file_path: Output file path
        """
        with open(file_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)


class ProgressTracker:
    """
    Real-time progress tracking with ETA calculation.

    Tracks rows processed, calculates completion percentage,
    estimates time remaining, and provides human-readable output.
    """

    def __init__(self, total_rows: int):
        """
        Initialize progress tracker.

        Args:
            total_rows: Total number of rows to process
        """
        self.total = total_rows
        self.processed = 0
        self.start_time = time.time()

    def update(self, rows_processed: int):
        """
        Update progress.

        Args:
            rows_processed: Number of rows processed so far
        """
        self.processed = rows_processed

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress information.

        Returns:
            Progress dict with percent_complete, eta_seconds, eta_human, rows_per_second
        """
        elapsed = time.time() - self.start_time

        # Calculate percentage
        percent = (self.processed / self.total * 100) if self.total > 0 else 0

        # Calculate rate
        rate = self.processed / elapsed if elapsed > 0 else 0

        # Calculate ETA
        if rate > 0 and self.processed < self.total:
            remaining_rows = self.total - self.processed
            eta_seconds = remaining_rows / rate
        else:
            eta_seconds = 0

        # Format ETA human-readable
        eta_human = self._format_eta(eta_seconds)

        return {
            'total_rows': self.total,
            'processed_rows': self.processed,
            'percent_complete': round(percent, 1),
            'rows_per_second': round(rate, 1),
            'eta_seconds': round(eta_seconds, 1),
            'eta_human': eta_human
        }

    def _format_eta(self, seconds: float) -> str:
        """
        Format ETA in human-readable format.

        Args:
            seconds: ETA in seconds

        Returns:
            Human-readable string (e.g., "2m 30s")
        """
        if seconds <= 0:
            return "0s"

        minutes = int(seconds // 60)
        secs = int(seconds % 60)

        if minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def emit_progress(self, file_path: Optional[str] = None):
        """
        Emit progress to file or stdout.

        Args:
            file_path: Optional file path (default: stdout)
        """
        progress = self.get_progress()

        if file_path:
            with open(file_path, 'w') as f:
                json.dump(progress, f, indent=2)
        else:
            print(json.dumps(progress, indent=2))


def check_connection_health(conn) -> Dict[str, Any]:
    """
    Check database connection health.

    Args:
        conn: Database connection object (psycopg2 or sqlite3)

    Returns:
        Health check result dict
    """
    try:
        # PostgreSQL connection
        if hasattr(conn, 'closed'):
            alive = conn.closed == 0
        # SQLite connection
        elif hasattr(conn, 'execute'):
            # Try a simple query
            conn.execute('SELECT 1')
            alive = True
        else:
            alive = False

        return {
            'healthy': alive,
            'connection_alive': alive,
            'check_time': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'healthy': False,
            'connection_alive': False,
            'error': str(e),
            'check_time': datetime.now().isoformat()
        }


def check_disk_space_health(path: str = '/', threshold_gb: float = 1.0) -> Dict[str, Any]:
    """
    Check disk space health.

    Args:
        path: Path to check (default: root)
        threshold_gb: Minimum free space in GB (default: 1.0)

    Returns:
        Health check result dict
    """
    try:
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024**3)

        return {
            'healthy': free_gb >= threshold_gb,
            'free_gb': round(free_gb, 2),
            'threshold_gb': threshold_gb,
            'check_time': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'check_time': datetime.now().isoformat()
        }


def check_memory_health(threshold_percent: float = 90.0) -> Dict[str, Any]:
    """
    Check memory usage health.

    Args:
        threshold_percent: Maximum memory usage percent (default: 90.0)

    Returns:
        Health check result dict
    """
    if psutil is None:
        return {
            'healthy': True,
            'warning': 'psutil not installed, memory check skipped',
            'check_time': datetime.now().isoformat()
        }

    try:
        mem = psutil.virtual_memory()

        return {
            'healthy': mem.percent < threshold_percent,
            'percent_used': round(mem.percent, 1),
            'threshold_percent': threshold_percent,
            'available_gb': round(mem.available / (1024**3), 2),
            'check_time': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'check_time': datetime.now().isoformat()
        }


# Example usage
if __name__ == '__main__':
    # Demonstrate observability components
    print("=== ETL Observability Demo ===\n")

    # Logger demo
    logger = ETLLogger("Demo_Gate")
    logger.info("Starting demo", operation="demo")
    logger.warning("Warning example", issue="none")
    logger.error("Error example", error_code=500)

    print("\n=== Metrics Demo ===\n")

    # Metrics demo
    metrics = ETLMetrics()
    metrics.record('profiler_duration_seconds', 45.2)
    metrics.record('quality_score', 85.5)
    metrics.increment('errors_total')
    metrics.increment('errors_total')

    print("Prometheus format:")
    print(metrics.emit_prometheus())

    print("\nJSON format:")
    print(metrics.emit_json())

    print("\n=== Progress Tracking Demo ===\n")

    # Progress tracker demo
    tracker = ProgressTracker(total_rows=1000)

    for i in range(0, 1001, 250):
        tracker.update(rows_processed=i)
        progress = tracker.get_progress()
        print(f"Progress: {progress['percent_complete']}% - ETA: {progress['eta_human']}")
        time.sleep(0.1)

    print("\n=== Health Checks Demo ===\n")

    # Health checks demo
    disk_health = check_disk_space_health()
    print(f"Disk health: {json.dumps(disk_health, indent=2)}")

    mem_health = check_memory_health()
    print(f"Memory health: {json.dumps(mem_health, indent=2)}")
