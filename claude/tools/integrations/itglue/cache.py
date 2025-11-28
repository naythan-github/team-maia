"""
SQLite metadata cache for ITGlue API

Caches metadata (NOT sensitive data like passwords or file contents) for fast local queries.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path

from claude.tools.integrations.itglue.models import (
    Organization, Configuration, Document, Contact, Relationship
)

logger = logging.getLogger(__name__)


class ITGlueCache:
    """
    SQLite-based metadata cache for ITGlue entities.

    Caches: Organizations, configurations, documents (metadata only), contacts, relationships
    Does NOT cache: Password values, document contents, sensitive fields
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

        # Track cache hits/misses for statistics
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(f"ITGlue cache initialized at {db_path}")

    def _init_database(self) -> None:
        """Create database schema if not exists"""
        with self._get_connection() as conn:
            # Organizations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT,
                    organization_type_name TEXT,
                    quick_notes TEXT,
                    cached_at TEXT NOT NULL
                )
            """)

            # Configurations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    configuration_type TEXT,
                    organization_id TEXT NOT NULL,
                    serial_number TEXT,
                    asset_tag TEXT,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    cached_at TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_configs_org ON configurations(organization_id)")

            # Documents table (metadata only, NOT file contents)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    size INTEGER,
                    organization_id TEXT NOT NULL,
                    upload_date TEXT,
                    content_type TEXT,
                    cached_at TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_org ON documents(organization_id)")

            # Contacts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    title TEXT,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    cached_at TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_org ON contacts(organization_id)")

            # Relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    created_at TEXT,
                    cached_at TEXT NOT NULL,
                    PRIMARY KEY (source_type, source_id, target_type, target_id)
                )
            """)

            # Cache metadata (track last refresh times)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    entity_type TEXT PRIMARY KEY,
                    last_refresh TEXT NOT NULL,
                    record_count INTEGER
                )
            """)

            conn.commit()
            logger.debug("Database schema initialized")

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ============= Organization Operations =============

    def cache_organizations(self, orgs: List[Organization]) -> None:
        """Cache organization list"""
        with self._get_connection() as conn:
            cached_at = datetime.now().isoformat()
            for org in orgs:
                conn.execute("""
                    INSERT OR REPLACE INTO organizations
                    (id, name, created_at, updated_at, organization_type_name, quick_notes, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    org.id, org.name,
                    org.created_at.isoformat() if org.created_at else None,
                    org.updated_at.isoformat() if org.updated_at else None,
                    org.organization_type_name, org.quick_notes, cached_at
                ))

            # Update metadata
            conn.execute("""
                INSERT OR REPLACE INTO cache_metadata (entity_type, last_refresh, record_count)
                VALUES ('organizations', ?, ?)
            """, (cached_at, len(orgs)))

            conn.commit()
            logger.info(f"Cached {len(orgs)} organizations")

    def get_organizations(self) -> List[Organization]:
        """Get all cached organizations"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM organizations ORDER BY name")
            rows = cursor.fetchall()

            if rows:
                self._cache_hits += 1
                return [self._row_to_organization(row) for row in rows]

            self._cache_misses += 1
            return []

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get single organization by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
            row = cursor.fetchone()

            if row:
                self._cache_hits += 1
                return self._row_to_organization(row)

            self._cache_misses += 1
            return None

    def search_organizations(self, name: str) -> List[Organization]:
        """Search organizations by name (case-insensitive)"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM organizations WHERE name LIKE ? ORDER BY name",
                (f"%{name}%",)
            )
            rows = cursor.fetchall()
            return [self._row_to_organization(row) for row in rows]

    def update_organization(self, org: Organization) -> None:
        """Update cached organization"""
        self.cache_organizations([org])

    def invalidate_organization(self, org_id: str) -> None:
        """Remove organization from cache"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
            conn.commit()
            logger.debug(f"Invalidated organization {org_id}")

    # ============= Configuration Operations =============

    def cache_configurations(self, configs: List[Configuration]) -> None:
        """Cache configuration list"""
        with self._get_connection() as conn:
            cached_at = datetime.now().isoformat()
            for config in configs:
                conn.execute("""
                    INSERT OR REPLACE INTO configurations
                    (id, name, configuration_type, organization_id, serial_number,
                     asset_tag, notes, created_at, updated_at, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config.id, config.name, config.configuration_type, config.organization_id,
                    config.serial_number, config.asset_tag, config.notes,
                    config.created_at.isoformat() if config.created_at else None,
                    config.updated_at.isoformat() if config.updated_at else None,
                    cached_at
                ))
            conn.commit()
            logger.info(f"Cached {len(configs)} configurations")

    def get_configurations(self, organization_id: str, configuration_type: Optional[str] = None) -> List[Configuration]:
        """Get configurations for organization, optionally filtered by type"""
        with self._get_connection() as conn:
            if configuration_type:
                cursor = conn.execute(
                    "SELECT * FROM configurations WHERE organization_id = ? AND configuration_type = ?",
                    (organization_id, configuration_type)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM configurations WHERE organization_id = ?",
                    (organization_id,)
                )

            rows = cursor.fetchall()
            return [self._row_to_configuration(row) for row in rows]

    def get_configuration(self, config_id: str) -> Optional[Configuration]:
        """Get single configuration by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM configurations WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            return self._row_to_configuration(row) if row else None

    # ============= Document Operations =============

    def cache_documents(self, docs: List[Document]) -> None:
        """Cache document metadata (NOT file contents)"""
        with self._get_connection() as conn:
            cached_at = datetime.now().isoformat()
            for doc in docs:
                conn.execute("""
                    INSERT OR REPLACE INTO documents
                    (id, name, size, organization_id, upload_date, content_type, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.id, doc.name, doc.size, doc.organization_id,
                    doc.upload_date.isoformat(), doc.content_type, cached_at
                ))
            conn.commit()
            logger.info(f"Cached {len(docs)} document metadata entries")

    def get_documents(self, organization_id: str) -> List[Document]:
        """Get document metadata for organization"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE organization_id = ?",
                (organization_id,)
            )
            rows = cursor.fetchall()
            return [self._row_to_document(row) for row in rows]

    # ============= Relationship Operations =============

    def cache_relationship(self, source_type: str, source_id: str, target_type: str, target_id: str) -> None:
        """Cache entity relationship"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO relationships
                (source_type, source_id, target_type, target_id, created_at, cached_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_type, source_id, target_type, target_id,
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()

    def get_relationships(self, source_type: str, source_id: str) -> List[Dict[str, str]]:
        """Get all relationships for an entity"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM relationships WHERE source_type = ? AND source_id = ?",
                (source_type, source_id)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ============= Smart Query (Cache-first with API fallback) =============

    def smart_get_organization(self, org_id: str, api_client=None, allow_stale: bool = False) -> Optional[Organization]:
        """
        Smart query: Try cache first, fall back to API if miss.

        Args:
            org_id: Organization ID
            api_client: ITGlueClient instance for API fallback
            allow_stale: Return stale cache data if API fails
        """
        # Try cache first
        cached = self.get_organization(org_id)
        if cached:
            return cached

        # Cache miss - fetch from API
        if api_client:
            try:
                org = api_client.get_organization(org_id)
                if org:
                    # Update cache
                    self.cache_organizations([org])
                return org
            except Exception as e:
                logger.warning(f"API fallback failed: {e}")
                if allow_stale and cached:
                    return cached

        return None

    # ============= Cache Management =============

    def is_stale(self, entity_type: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is stale"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_refresh FROM cache_metadata WHERE entity_type = ?",
                (entity_type,)
            )
            row = cursor.fetchone()

            if not row:
                return True  # No cache data = stale

            last_refresh = datetime.fromisoformat(row['last_refresh'])
            age = datetime.now() - last_refresh

            return age > timedelta(hours=max_age_hours)

    def refresh_organizations(self, orgs: List[Organization]) -> None:
        """Refresh organization cache (clears old data)"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM organizations")
            conn.commit()
        self.cache_organizations(orgs)
        logger.info(f"Refreshed organization cache with {len(orgs)} records")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._get_connection() as conn:
            org_count = conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]
            config_count = conn.execute("SELECT COUNT(*) FROM configurations").fetchone()[0]
            doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            contact_count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

            # Get database file size
            db_size_bytes = Path(self.db_path).stat().st_size

            # Calculate hit rate
            total_queries = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_queries) if total_queries > 0 else 0

            # Get last refresh times
            cursor = conn.execute("SELECT entity_type, last_refresh FROM cache_metadata")
            last_refresh = {row['entity_type']: row['last_refresh'] for row in cursor.fetchall()}

            return {
                'organization_count': org_count,
                'configuration_count': config_count,
                'document_count': doc_count,
                'contact_count': contact_count,
                'cache_size_mb': db_size_bytes / (1024 * 1024),
                'cache_hit_rate': hit_rate,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'last_refresh': last_refresh
            }

    # ============= Helper Methods =============

    def _row_to_organization(self, row: sqlite3.Row) -> Organization:
        """Convert database row to Organization model"""
        return Organization(
            id=row['id'],
            name=row['name'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            organization_type_name=row['organization_type_name'],
            quick_notes=row['quick_notes']
        )

    def _row_to_configuration(self, row: sqlite3.Row) -> Configuration:
        """Convert database row to Configuration model"""
        return Configuration(
            id=row['id'],
            name=row['name'],
            configuration_type=row['configuration_type'],
            organization_id=row['organization_id'],
            serial_number=row['serial_number'],
            asset_tag=row['asset_tag'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        """Convert database row to Document model"""
        return Document(
            id=row['id'],
            name=row['name'],
            size=row['size'],
            organization_id=row['organization_id'],
            upload_date=datetime.fromisoformat(row['upload_date']),
            content_type=row['content_type']
        )
