#!/usr/bin/env python3
"""
Database Connection Manager - Optimized SQLite Connection Pool

Provides centralized, optimized database connections with pooling, caching,
and automatic lifecycle management. Replaces scattered sqlite3.connect() calls
throughout the codebase with efficient, reusable connections.

OPTIMIZATION TARGET: 101 sqlite3.connect() instances across 39 files

Benefits:
- Connection pooling and reuse
- Thread-safe operations
- Automatic error recovery
- Performance monitoring
- Resource optimization
"""

import sqlite3
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict
from queue import Queue, Empty
from claude.tools.core.path_manager import get_maia_root


@dataclass
class ConnectionMetrics:
    """Metrics for database connection performance"""
    connection_count: int = 0
    active_connections: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    avg_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_cleanup: float = field(default_factory=time.time)


@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    max_connections: int = 10
    connection_timeout: int = 30
    query_timeout: int = 10
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    cache_size: int = 10000
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"


class PooledConnection:
    """Wrapper for pooled SQLite connections"""

    def __init__(self, db_path: str, config: DatabaseConfig):
        self.db_path = db_path
        self.config = config
        self.connection = None
        self.created_at = time.time()
        self.last_used = time.time()
        self.query_count = 0
        self.is_active = False
        self.thread_id = None

        self._connect()

    def _connect(self):
        """Create optimized SQLite connection"""
        self.connection = sqlite3.connect(
            self.db_path,
            timeout=self.config.connection_timeout,
            check_same_thread=False  # Allow cross-thread usage with proper locking
        )

        # Apply optimizations
        self.connection.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
        self.connection.execute(f"PRAGMA synchronous = {self.config.synchronous}")
        self.connection.execute(f"PRAGMA cache_size = {self.config.cache_size}")

        if self.config.enable_foreign_keys:
            self.connection.execute("PRAGMA foreign_keys = ON")

        if self.config.enable_wal_mode:
            self.connection.execute("PRAGMA wal_autocheckpoint = 1000")

        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        self.connection.commit()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute query with timeout and error handling"""
        if not self.connection:
            self._connect()

        try:
            self.last_used = time.time()
            self.query_count += 1
            self.is_active = True
            self.thread_id = threading.current_thread().ident

            cursor = self.connection.cursor()
            cursor.execute(query, params)

            return cursor

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                # Retry once after brief delay
                time.sleep(0.1)
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                return cursor
            raise
        finally:
            self.is_active = False

    def executemany(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """Execute query with multiple parameter sets"""
        if not self.connection:
            self._connect()

        self.last_used = time.time()
        self.query_count += len(params_list)
        self.is_active = True

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            return cursor
        finally:
            self.is_active = False

    def commit(self):
        """Commit transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.connection:
            self.connection.rollback()

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    @property
    def age_seconds(self) -> float:
        """Get connection age in seconds"""
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        """Get idle time in seconds"""
        return time.time() - self.last_used


class DatabaseConnectionManager:
    """Centralized database connection manager with pooling"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pools: Dict[str, Queue] = {}
        self.active_connections: Dict[str, List[PooledConnection]] = defaultdict(list)
        self.metrics: Dict[str, ConnectionMetrics] = defaultdict(ConnectionMetrics)
        self.lock = threading.RLock()

        # Query cache for repeated operations
        self.query_cache: Dict[str, Any] = {}
        self.cache_lock = threading.Lock()

        # Background cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.logger.info("🗄️  Database Connection Manager initialized")
        self.logger.info(f"   • Max connections per DB: {self.config.max_connections}")
        self.logger.info(f"   • Connection timeout: {self.config.connection_timeout}s")
        self.logger.info(f"   • WAL mode: {self.config.enable_wal_mode}")

    def _get_pool(self, db_path: str) -> Queue:
        """Get or create connection pool for database"""
        with self.lock:
            if db_path not in self.pools:
                self.pools[db_path] = Queue(maxsize=self.config.max_connections)
                self.logger.info(f"📊 Created connection pool for: {Path(db_path).name}")
            return self.pools[db_path]

    def _get_connection(self, db_path: str) -> PooledConnection:
        """Get connection from pool or create new one"""
        pool = self._get_pool(db_path)

        try:
            # Try to get existing connection from pool
            conn = pool.get_nowait()

            # Check if connection is still valid
            if conn.connection and not conn.is_active:
                try:
                    conn.connection.execute("SELECT 1")
                    self.metrics[db_path].cache_hits += 1
                    return conn
                except sqlite3.Error:
                    conn.close()

        except Empty:
            pass

        # Create new connection
        self.metrics[db_path].cache_misses += 1
        self.metrics[db_path].connection_count += 1

        conn = PooledConnection(db_path, self.config)

        with self.lock:
            self.active_connections[db_path].append(conn)

        return conn

    def _return_connection(self, db_path: str, conn: PooledConnection):
        """Return connection to pool"""
        pool = self._get_pool(db_path)

        if not conn.is_active and conn.connection:
            try:
                pool.put_nowait(conn)
            except:
                # Pool is full, close connection
                conn.close()
                with self.lock:
                    if conn in self.active_connections[db_path]:
                        self.active_connections[db_path].remove(conn)

    @contextmanager
    def get_connection(self, db_path: str):
        """Context manager for database connections"""
        # Ensure path is absolute
        db_path = str(Path(db_path).resolve())

        conn = self._get_connection(db_path)
        start_time = time.time()

        try:
            yield conn
            conn.commit()  # Auto-commit on success

        except Exception as e:
            conn.rollback()  # Auto-rollback on error
            self.metrics[db_path].failed_queries += 1
            self.logger.error(f"Database operation failed for {Path(db_path).name}: {e}")
            raise

        finally:
            # Update metrics
            execution_time = time.time() - start_time
            metrics = self.metrics[db_path]
            metrics.total_queries += 1

            # Update average query time
            if metrics.total_queries > 1:
                metrics.avg_query_time = (
                    (metrics.avg_query_time * (metrics.total_queries - 1) + execution_time)
                    / metrics.total_queries
                )
            else:
                metrics.avg_query_time = execution_time

            self._return_connection(db_path, conn)

    def execute_query(self, db_path: str, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute query and return results"""
        with self.get_connection(db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, db_path: str, query: str, params: Tuple = ()) -> int:
        """Execute update/insert/delete and return affected rows"""
        with self.get_connection(db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def execute_many(self, db_path: str, query: str, params_list: List[Tuple]) -> int:
        """Execute query with multiple parameter sets"""
        with self.get_connection(db_path) as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount

    def execute_script(self, db_path: str, script: str):
        """Execute SQL script (for schema creation, etc.)"""
        with self.get_connection(db_path) as conn:
            conn.connection.executescript(script)

    def get_cached_query(self, cache_key: str, db_path: str, query: str, params: Tuple = (),
                        cache_duration: int = 300) -> Optional[List[sqlite3.Row]]:
        """Execute query with caching"""
        with self.cache_lock:
            if cache_key in self.query_cache:
                cached_result, timestamp = self.query_cache[cache_key]
                if time.time() - timestamp < cache_duration:
                    return cached_result

        # Cache miss - execute query
        result = self.execute_query(db_path, query, params)

        with self.cache_lock:
            self.query_cache[cache_key] = (result, time.time())

            # Limit cache size
            if len(self.query_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self.query_cache.keys(),
                                   key=lambda k: self.query_cache[k][1])[:100]
                for key in oldest_keys:
                    del self.query_cache[key]

        return result

    def _cleanup_worker(self):
        """Background cleanup of idle connections"""
        while True:
            try:
                time.sleep(60)  # Run every minute
                self._cleanup_connections()
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")

    def _cleanup_connections(self):
        """Clean up idle and old connections"""
        current_time = time.time()

        with self.lock:
            for db_path, connections in self.active_connections.items():
                connections_to_remove = []

                for conn in connections:
                    # Close connections that are idle for too long
                    if (not conn.is_active and
                        conn.idle_seconds > 300):  # 5 minutes idle
                        conn.close()
                        connections_to_remove.append(conn)

                    # Close connections that are too old
                    elif conn.age_seconds > 3600:  # 1 hour old
                        conn.close()
                        connections_to_remove.append(conn)

                for conn in connections_to_remove:
                    connections.remove(conn)

                # Update metrics
                self.metrics[db_path].active_connections = len(connections)
                self.metrics[db_path].last_cleanup = current_time

    def get_metrics(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """Get connection metrics"""
        if db_path:
            metrics = self.metrics[db_path]
            return {
                'db_path': db_path,
                'connection_count': metrics.connection_count,
                'active_connections': len(self.active_connections[db_path]),
                'total_queries': metrics.total_queries,
                'failed_queries': metrics.failed_queries,
                'success_rate': (metrics.total_queries - metrics.failed_queries) / max(metrics.total_queries, 1),
                'avg_query_time': metrics.avg_query_time,
                'cache_hits': metrics.cache_hits,
                'cache_misses': metrics.cache_misses,
                'cache_hit_rate': metrics.cache_hits / max(metrics.cache_hits + metrics.cache_misses, 1)
            }
        else:
            return {
                'total_databases': len(self.pools),
                'total_connections': sum(len(conns) for conns in self.active_connections.values()),
                'total_queries': sum(m.total_queries for m in self.metrics.values()),
                'total_cache_entries': len(self.query_cache),
                'databases': [self.get_metrics(db) for db in self.pools.keys()]
            }

    def optimize_database(self, db_path: str):
        """Run database optimization commands"""
        optimization_queries = [
            "PRAGMA optimize;",
            "VACUUM;",
            "PRAGMA wal_checkpoint(TRUNCATE);"
        ]

        with self.get_connection(db_path) as conn:
            for query in optimization_queries:
                try:
                    conn.execute(query)
                except sqlite3.Error as e:
                    self.logger.warning(f"Optimization query failed: {query} - {e}")

    def close_all(self):
        """Close all connections (for shutdown)"""
        with self.lock:
            for connections in self.active_connections.values():
                for conn in connections:
                    conn.close()

            self.active_connections.clear()
            self.pools.clear()


# Global instance
_db_manager = None

def get_db_manager() -> DatabaseConnectionManager:
    """Get global database connection manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseConnectionManager()
    return _db_manager


# Convenience functions for common operations
def execute_query(db_path: str, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """Execute query using global connection manager"""
    return get_db_manager().execute_query(db_path, query, params)


def execute_update(db_path: str, query: str, params: Tuple = ()) -> int:
    """Execute update using global connection manager"""
    return get_db_manager().execute_update(db_path, query, params)


def execute_cached_query(cache_key: str, db_path: str, query: str, params: Tuple = (),
                        cache_duration: int = 300) -> List[sqlite3.Row]:
    """Execute cached query using global connection manager"""
    return get_db_manager().get_cached_query(cache_key, db_path, query, params, cache_duration)


if __name__ == "__main__":
    # Demo and testing
    print("🗄️  Database Connection Manager - Performance Demo")
    print("=" * 60)

    manager = get_db_manager()
    test_db = "${MAIA_ROOT}/claude/security/temp/test_optimization.db"

    # Create test database
    with manager.get_connection(test_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)

    # Performance test
    import random
    start_time = time.time()

    # Insert test data
    test_data = [(f"item_{i}", random.randint(1, 1000)) for i in range(1000)]
    manager.execute_many(test_db, "INSERT INTO test_table (name, value) VALUES (?, ?)", test_data)

    # Query test data
    results = manager.execute_query(test_db, "SELECT COUNT(*) as count FROM test_table")

    end_time = time.time()

    print(f"✅ Performance Test Complete:")
    print(f"   • Inserted 1000 records")
    print(f"   • Total time: {end_time - start_time:.2f}s")
    print(f"   • Records in database: {results[0]['count']}")

    # Show metrics
    metrics = manager.get_metrics()
    print(f"\n📊 Connection Metrics:")
    print(f"   • Total databases: {metrics['total_databases']}")
    print(f"   • Total connections: {metrics['total_connections']}")
    print(f"   • Total queries: {metrics['total_queries']}")

    if metrics['databases']:
        db_metrics = metrics['databases'][0]
        print(f"   • Success rate: {db_metrics['success_rate']:.1%}")
        print(f"   • Avg query time: {db_metrics['avg_query_time']*1000:.1f}ms")
        print(f"   • Cache hit rate: {db_metrics['cache_hit_rate']:.1%}")

    print(f"\n🚀 OPTIMIZATION BENEFITS:")
    print(f"   • Connection pooling reduces overhead")
    print(f"   • WAL mode improves concurrent access")
    print(f"   • Query caching speeds up repeated operations")
    print(f"   • Automatic cleanup prevents resource leaks")

    # Cleanup
    import os
    if os.path.exists(test_db):
        os.remove(test_db)
