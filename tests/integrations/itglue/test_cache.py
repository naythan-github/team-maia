"""
Unit tests for ITGlue Local Metadata Cache

Tests FR3: Local Metadata Caching (SQLite)
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

try:
    from claude.tools.integrations.itglue.cache import ITGlueCache
    from claude.tools.integrations.itglue.models import Organization, Configuration, Document
except ImportError:
    # Expected to fail initially - TDD red phase
    pass


class TestCacheInitialization:
    """Test FR3.1: Cache Database Initialization"""

    def test_create_cache_database(self, tmp_path):
        """FR3.1: Create SQLite database on first run"""
        db_path = tmp_path / "itglue_test.db"
        cache = ITGlueCache(str(db_path))

        # Verify database created
        assert db_path.exists()

    def test_cache_schema_created(self, tmp_path):
        """FR3.1: Create all required tables"""
        db_path = tmp_path / "itglue_test.db"
        cache = ITGlueCache(str(db_path))

        # Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'organizations',
            'configurations',
            'documents',
            'contacts',
            'relationships',
            'cache_metadata'
        ]

        for table in expected_tables:
            assert table in tables


class TestOrganizationCaching:
    """Test caching for organizations"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_cache_organization_list(self, cache):
        """FR3.1: Cache organization metadata"""
        orgs = [
            Organization(id='1', name='Acme Corp', created_at=datetime.now()),
            Organization(id='2', name='Beta LLC', created_at=datetime.now())
        ]

        cache.cache_organizations(orgs)

        # Retrieve from cache
        cached = cache.get_organizations()
        assert len(cached) == 2
        assert cached[0].name == 'Acme Corp'

    def test_cache_organization_by_id(self, cache):
        """FR3.1: Cache and retrieve single organization"""
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now())
        cache.cache_organizations([org])

        cached = cache.get_organization('1')
        assert cached is not None
        assert cached.name == 'Acme Corp'

    def test_get_organization_not_in_cache(self, cache):
        """FR3.1: Return None when organization not cached"""
        result = cache.get_organization('999')
        assert result is None

    def test_search_organizations_by_name(self, cache):
        """FR3.1: Search cached organizations by name"""
        orgs = [
            Organization(id='1', name='Acme Corp', created_at=datetime.now()),
            Organization(id='2', name='Acme Industries', created_at=datetime.now()),
            Organization(id='3', name='Beta LLC', created_at=datetime.now())
        ]
        cache.cache_organizations(orgs)

        results = cache.search_organizations(name='Acme')
        assert len(results) == 2
        assert all('Acme' in org.name for org in results)


class TestConfigurationCaching:
    """Test caching for configurations"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_cache_configurations(self, cache):
        """FR3.1: Cache configuration metadata"""
        configs = [
            Configuration(
                id='100',
                name='Web Server',
                configuration_type='Server',
                serial_number='SN12345',
                organization_id='1'
            ),
            Configuration(
                id='101',
                name='Firewall',
                configuration_type='Network Device',
                serial_number='SN67890',
                organization_id='1'
            )
        ]

        cache.cache_configurations(configs)

        cached = cache.get_configurations(organization_id='1')
        assert len(cached) == 2
        assert cached[0].name == 'Web Server'

    def test_get_configuration_by_id(self, cache):
        """FR3.1: Retrieve configuration by ID"""
        config = Configuration(
            id='100',
            name='Web Server',
            configuration_type='Server',
            organization_id='1'
        )
        cache.cache_configurations([config])

        cached = cache.get_configuration('100')
        assert cached is not None
        assert cached.name == 'Web Server'

    def test_filter_configurations_by_type(self, cache):
        """FR3.1: Filter configurations by type"""
        configs = [
            Configuration(id='100', name='Server1', configuration_type='Server', organization_id='1'),
            Configuration(id='101', name='Server2', configuration_type='Server', organization_id='1'),
            Configuration(id='102', name='Switch1', configuration_type='Network Device', organization_id='1')
        ]
        cache.cache_configurations(configs)

        servers = cache.get_configurations(organization_id='1', configuration_type='Server')
        assert len(servers) == 2


class TestDocumentCaching:
    """Test caching for documents (metadata only, not file contents)"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_cache_document_metadata_only(self, cache):
        """FR3.1: Cache document metadata, NOT file contents"""
        docs = [
            Document(
                id='700',
                name='Network Diagram.pdf',
                size=1024000,
                upload_date=datetime.now(),
                organization_id='1'
            )
        ]

        cache.cache_documents(docs)

        cached = cache.get_documents(organization_id='1')
        assert len(cached) == 1
        assert cached[0].name == 'Network Diagram.pdf'
        assert cached[0].size == 1024000
        # Verify no file_content field cached
        assert not hasattr(cached[0], 'file_content')


class TestCacheRefresh:
    """Test FR3.2: Cache Operations (Refresh, Invalidation)"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_detect_cache_staleness(self, cache):
        """FR3.2: Detect cache staleness (>24 hours)"""
        # Cache organization with old timestamp
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now() - timedelta(hours=25))
        cache.cache_organizations([org])

        # Update cache metadata to simulate 25 hours ago
        with cache._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache_metadata (entity_type, last_refresh) VALUES (?, ?)",
                ('organizations', (datetime.now() - timedelta(hours=25)).isoformat())
            )

        is_stale = cache.is_stale('organizations', max_age_hours=24)
        assert is_stale is True

    def test_cache_refresh_updates_timestamp(self, cache):
        """FR3.2: Refresh updates last_refresh timestamp"""
        orgs = [Organization(id='1', name='Acme Corp', created_at=datetime.now())]
        cache.cache_organizations(orgs)

        # Get timestamp
        with cache._get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_refresh FROM cache_metadata WHERE entity_type = ?",
                ('organizations',)
            )
            timestamp1 = cursor.fetchone()[0]

        # Wait and refresh
        import time
        time.sleep(0.1)
        cache.refresh_organizations([Organization(id='2', name='Beta LLC', created_at=datetime.now())])

        # Verify timestamp updated
        with cache._get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_refresh FROM cache_metadata WHERE entity_type = ?",
                ('organizations',)
            )
            timestamp2 = cursor.fetchone()[0]

        assert timestamp2 > timestamp1

    def test_cache_invalidation_on_delete(self, cache):
        """FR3.2: Invalidate cache on write operations"""
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now())
        cache.cache_organizations([org])

        # Delete organization
        cache.invalidate_organization('1')

        # Verify removed from cache
        cached = cache.get_organization('1')
        assert cached is None

    def test_cache_invalidation_on_update(self, cache):
        """FR3.2: Update cache on write operations"""
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now())
        cache.cache_organizations([org])

        # Update organization
        updated = Organization(id='1', name='Acme Industries', created_at=datetime.now())
        cache.update_organization(updated)

        # Verify updated in cache
        cached = cache.get_organization('1')
        assert cached.name == 'Acme Industries'


class TestSmartQuery:
    """Test FR3.2: Smart Query (Cache-first, API fallback)"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_smart_query_cache_hit(self, cache):
        """FR3.2: Return from cache if available"""
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now())
        cache.cache_organizations([org])

        # Mock API client (should not be called)
        mock_client = Mock()

        result = cache.smart_get_organization('1', api_client=mock_client)
        assert result is not None
        assert result.name == 'Acme Corp'
        # Verify API not called (cache hit)
        mock_client.get_organization.assert_not_called()

    def test_smart_query_cache_miss_fallback_to_api(self, cache):
        """FR3.2: Fall back to API if cache miss"""
        # Empty cache
        mock_client = Mock()
        mock_client.get_organization.return_value = Organization(
            id='999',
            name='New Corp',
            created_at=datetime.now()
        )

        result = cache.smart_get_organization('999', api_client=mock_client)
        assert result is not None
        assert result.name == 'New Corp'
        # Verify API was called
        mock_client.get_organization.assert_called_once_with('999')

        # Verify result cached for future queries
        cached = cache.get_organization('999')
        assert cached is not None


class TestRelationshipCaching:
    """Test caching for entity relationships"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_cache_configuration_password_link(self, cache):
        """FR3.1: Cache configuration → password relationship"""
        cache.cache_relationship(
            source_type='configuration',
            source_id='100',
            target_type='password',
            target_id='500'
        )

        # Query relationships
        links = cache.get_relationships(source_type='configuration', source_id='100')
        assert len(links) == 1
        assert links[0]['target_type'] == 'password'
        assert links[0]['target_id'] == '500'

    def test_cache_multiple_relationships(self, cache):
        """FR3.1: Cache multiple relationships for one entity"""
        cache.cache_relationship('configuration', '100', 'password', '500')
        cache.cache_relationship('configuration', '100', 'contact', '200')
        cache.cache_relationship('configuration', '100', 'flexible_asset', '300')

        links = cache.get_relationships(source_type='configuration', source_id='100')
        assert len(links) == 3


class TestCacheStatistics:
    """Test cache statistics and monitoring"""

    @pytest.fixture
    def cache(self, tmp_path):
        db_path = tmp_path / "itglue_test.db"
        return ITGlueCache(str(db_path))

    def test_get_cache_statistics(self, cache):
        """NFR3.2: Cache statistics (hit rate, entity counts)"""
        # Populate cache
        cache.cache_organizations([
            Organization(id='1', name='Acme Corp', created_at=datetime.now()),
            Organization(id='2', name='Beta LLC', created_at=datetime.now())
        ])

        stats = cache.get_statistics()
        assert stats['organization_count'] == 2
        assert 'cache_size_mb' in stats
        assert 'last_refresh' in stats

    def test_track_cache_hit_rate(self, cache):
        """NFR3.2: Track cache hit rate"""
        org = Organization(id='1', name='Acme Corp', created_at=datetime.now())
        cache.cache_organizations([org])

        # Cache hit
        cache.get_organization('1')  # Hit
        cache.get_organization('1')  # Hit
        cache.get_organization('999')  # Miss

        stats = cache.get_statistics()
        # 2 hits / 3 total = 66.7% hit rate
        assert stats['cache_hit_rate'] >= 0.6
