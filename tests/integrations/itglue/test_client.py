"""
Unit tests for ITGlue API Client

Tests all core CRUD operations for ITGlue entities.
These tests use mocks - no real API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# These imports will fail until we implement - that's expected in TDD
try:
    from claude.tools.integrations.itglue.client import ITGlueClient
    from claude.tools.integrations.itglue.exceptions import (
        ITGlueAuthError,
        ITGlueRateLimitError,
        ITGlueNotFoundError,
        ITGlueAPIError
    )
    from claude.tools.integrations.itglue.models import (
        Organization,
        Configuration,
        Password,
        FlexibleAsset,
        Document,
        Contact
    )
except ImportError:
    # Expected to fail initially - TDD red phase
    pass


class TestITGlueClientAuthentication:
    """Test FR1: Authentication & Session Management"""

    def test_init_with_valid_api_key(self):
        """FR1.1: Initialize client with API key from macOS Keychain"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-api-key'):
            client = ITGlueClient(instance='sandbox')
            assert client.api_key == 'test-api-key'
            assert client.instance == 'sandbox'
            assert client.base_url == 'https://api-sandbox.itglue.com'

    def test_init_production_instance(self):
        """FR1.2: Support production instance"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='prod-api-key'):
            client = ITGlueClient(instance='production')
            assert client.instance == 'production'
            assert client.base_url == 'https://api.itglue.com'

    def test_detect_api_key_expiry(self):
        """FR1.3: Detect API key expiry (401 response)"""
        client = ITGlueClient(instance='sandbox')
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=401, json=lambda: {'errors': ['Unauthorized']})

            with pytest.raises(ITGlueAuthError, match='API key invalid or expired'):
                client.list_organizations()

    def test_validate_api_key_on_first_use(self):
        """FR1.4: Validate API key with test call"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            client = ITGlueClient(instance='sandbox')
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = Mock(
                    status_code=200,
                    json=lambda: {'data': []}
                )

                result = client.validate_api_key()
                assert result is True
                mock_request.assert_called_once()


class TestOrganizationOperations:
    """Test FR2.1: Organization CRUD operations"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_list_organizations(self, client):
        """FR2.1: List all organizations"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': [
                        {'id': '1', 'attributes': {'name': 'Acme Corp', 'created-at': '2024-01-01T00:00:00Z'}},
                        {'id': '2', 'attributes': {'name': 'Beta LLC', 'created-at': '2024-01-02T00:00:00Z'}}
                    ]
                }
            )

            orgs = client.list_organizations()
            assert len(orgs) == 2
            assert orgs[0].id == '1'
            assert orgs[0].name == 'Acme Corp'

    def test_get_organization_by_id(self, client):
        """FR2.1: Get organization by ID"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': {'id': '1', 'attributes': {'name': 'Acme Corp'}}
                }
            )

            org = client.get_organization('1')
            assert org.id == '1'
            assert org.name == 'Acme Corp'

    def test_get_organization_not_found(self, client):
        """FR2.1: Return None when organization not found"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=404)

            org = client.get_organization('999')
            assert org is None

    def test_create_organization(self, client):
        """FR2.1: Create new organization"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=201,
                json=lambda: {
                    'data': {'id': '3', 'attributes': {'name': 'New Corp'}}
                }
            )

            org = client.create_organization(name='New Corp')
            assert org.id == '3'
            assert org.name == 'New Corp'

    def test_update_organization(self, client):
        """FR2.1: Update organization metadata"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': {'id': '1', 'attributes': {'name': 'Updated Corp'}}
                }
            )

            org = client.update_organization('1', name='Updated Corp')
            assert org.name == 'Updated Corp'

    def test_search_organizations_by_name(self, client):
        """FR2.1: Search organizations by name"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': [{'id': '1', 'attributes': {'name': 'Acme Corp'}}]
                }
            )

            orgs = client.search_organizations(name='Acme')
            assert len(orgs) == 1
            assert orgs[0].name == 'Acme Corp'


class TestConfigurationOperations:
    """Test FR2.2: Configuration CRUD operations"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_list_configurations_for_org(self, client):
        """FR2.2: List configurations for organization"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': [
                        {'id': '100', 'attributes': {'name': 'Web Server', 'configuration-type-name': 'Server'}},
                        {'id': '101', 'attributes': {'name': 'Firewall', 'configuration-type-name': 'Network Device'}}
                    ]
                }
            )

            configs = client.list_configurations(organization_id='1')
            assert len(configs) == 2
            assert configs[0].name == 'Web Server'

    def test_create_configuration(self, client):
        """FR2.2: Create configuration"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=201,
                json=lambda: {
                    'data': {
                        'id': '102',
                        'attributes': {
                            'name': 'Database Server',
                            'configuration-type-name': 'Server',
                            'serial-number': 'SN12345'
                        }
                    }
                }
            )

            config = client.create_configuration(
                organization_id='1',
                name='Database Server',
                configuration_type='Server',
                serial_number='SN12345'
            )
            assert config.id == '102'
            assert config.serial_number == 'SN12345'

    def test_link_configuration_to_password(self, client):
        """FR2.2: Link configuration to password"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=200)

            result = client.link_configuration_to_password(
                configuration_id='100',
                password_id='500'
            )
            assert result is True


class TestPasswordOperations:
    """Test FR2.3: Password CRUD operations"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_list_passwords_for_org(self, client):
        """FR2.3: List passwords for organization"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': [
                        {'id': '500', 'attributes': {'name': 'Admin Password', 'username': 'admin'}},
                        {'id': '501', 'attributes': {'name': 'DB Password', 'username': 'dbuser'}}
                    ]
                }
            )

            passwords = client.list_passwords(organization_id='1')
            assert len(passwords) == 2
            assert passwords[0].name == 'Admin Password'

    def test_get_password_details(self, client):
        """FR2.3: Get password details (encrypted field)"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': {
                        'id': '500',
                        'attributes': {
                            'name': 'Admin Password',
                            'username': 'admin',
                            'password': 'encrypted_value'
                        }
                    }
                }
            )

            password = client.get_password('500')
            assert password.id == '500'
            assert password.username == 'admin'

    def test_create_password(self, client):
        """FR2.3: Create password entry"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=201,
                json=lambda: {
                    'data': {'id': '502', 'attributes': {'name': 'New Password'}}
                }
            )

            password = client.create_password(
                organization_id='1',
                name='New Password',
                username='newuser',
                password='secret123'
            )
            assert password.id == '502'

    def test_password_values_never_logged(self, client, caplog):
        """FR2.3 CRITICAL: Password values never logged"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=201,
                json=lambda: {'data': {'id': '502', 'attributes': {'name': 'Test'}}}
            )

            client.create_password(
                organization_id='1',
                name='Test Password',
                username='user',
                password='supersecret123'
            )

            # Verify password never appears in logs
            log_output = caplog.text
            assert 'supersecret123' not in log_output


class TestDocumentOperations:
    """Test FR2.5: Document CRUD operations"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_list_documents_for_org(self, client):
        """FR2.5: List documents for organization"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {
                    'data': [
                        {'id': '700', 'attributes': {'name': 'Network Diagram.pdf', 'size': 1024000}},
                        {'id': '701', 'attributes': {'name': 'Runbook.docx', 'size': 512000}}
                    ]
                }
            )

            docs = client.list_documents(organization_id='1')
            assert len(docs) == 2
            assert docs[0].name == 'Network Diagram.pdf'

    def test_upload_document(self, client):
        """FR2.5: Upload document from file path"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=201,
                json=lambda: {
                    'data': {
                        'id': '702',
                        'attributes': {'name': 'test.pdf', 'size': 2048}
                    }
                }
            )

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b'fake pdf content'

                doc = client.upload_document(
                    organization_id='1',
                    file_path='/tmp/test.pdf',
                    name='test.pdf'
                )
                assert doc.id == '702'

    def test_download_document(self, client):
        """FR2.5: Download document to local file"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                content=b'document content'
            )

            with patch('builtins.open', create=True) as mock_open:
                result = client.download_document(
                    document_id='700',
                    output_path='/tmp/output.pdf'
                )
                assert result is True
                mock_open.assert_called_once()


class TestRateLimiting:
    """Test FR5.1: API Rate Limiting (3000 req/5min)"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_track_request_count(self, client):
        """FR5.1: Track requests in rolling 5-minute window"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {'data': []}
            )

            # Make 10 requests
            for _ in range(10):
                client.list_organizations()

            # Verify rate limiter tracked them
            assert client.rate_limiter.request_count >= 10

    def test_auto_throttle_at_80_percent(self, client):
        """FR5.1: Auto-throttle when approaching limit (80% = 2400 reqs)"""
        client.rate_limiter.request_count = 2400

        with patch('time.sleep') as mock_sleep:
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = Mock(
                    status_code=200,
                    json=lambda: {'data': []}
                )

                client.list_organizations()
                # Should introduce delay to throttle
                mock_sleep.assert_called_once()

    def test_handle_429_rate_limit_response(self, client):
        """FR5.1: Respect Retry-After header on 429"""
        with patch.object(client, '_make_request') as mock_request:
            # First call returns 429, second succeeds
            mock_request.side_effect = [
                Mock(status_code=429, headers={'Retry-After': '60'}),
                Mock(status_code=200, json=lambda: {'data': []})
            ]

            with patch('time.sleep') as mock_sleep:
                result = client.list_organizations()
                # Should sleep for Retry-After duration
                mock_sleep.assert_called_with(60)

    def test_exponential_backoff_on_repeated_429(self, client):
        """FR5.1: Exponential backoff: 60s → 120s → 240s"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                Mock(status_code=429, headers={'Retry-After': '60'}),
                Mock(status_code=429, headers={'Retry-After': '60'}),
                Mock(status_code=429, headers={'Retry-After': '60'}),
                Mock(status_code=200, json=lambda: {'data': []})
            ]

            with patch('time.sleep') as mock_sleep:
                client.list_organizations()
                # Verify exponential backoff delays
                assert mock_sleep.call_count == 3


class TestErrorHandling:
    """Test FR5.2: HTTP Error Handling"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_401_unauthorized_raises_auth_error(self, client):
        """FR5.2: 401 → ITGlueAuthError (API key invalid)"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=401)

            with pytest.raises(ITGlueAuthError):
                client.list_organizations()

    def test_403_forbidden_logs_and_fails(self, client):
        """FR5.2: 403 → Log and fail gracefully"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=403)

            with pytest.raises(ITGlueAPIError, match='Forbidden'):
                client.list_organizations()

    def test_404_not_found_returns_none(self, client):
        """FR5.2: 404 → Return None (not exception)"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=404)

            result = client.get_organization('999')
            assert result is None

    def test_500_internal_error_retries_3_times(self, client):
        """FR5.2: 500 → Exponential backoff (3 retries)"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                Mock(status_code=500),
                Mock(status_code=500),
                Mock(status_code=500),
                Mock(status_code=200, json=lambda: {'data': []})
            ]

            with patch('time.sleep'):
                result = client.list_organizations()
                assert mock_request.call_count == 4


class TestCircuitBreaker:
    """Test FR5.3: Circuit Breaker Pattern"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_circuit_opens_after_5_failures(self, client):
        """FR5.3: Open circuit after 5 consecutive failures"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=500)

            # 5 failures should open circuit
            for _ in range(5):
                try:
                    client.list_organizations()
                except:
                    pass

            # Next call should fail fast (circuit open)
            assert client.circuit_breaker.is_open() is True

    def test_circuit_closes_after_cooldown(self, client):
        """FR5.3: Close circuit after 60s cooldown"""
        # Open circuit
        client.circuit_breaker.open()
        assert client.circuit_breaker.is_open() is True

        # Fast-forward 61 seconds
        with patch('time.time') as mock_time:
            mock_time.return_value = datetime.now().timestamp() + 61
            assert client.circuit_breaker.is_open() is False


class TestMultiInstance:
    """Test FR4: Multi-Instance Support (Sandbox vs Production)"""

    def test_sandbox_instance_uses_correct_url(self):
        """FR4.4: Sandbox instance uses api-sandbox.itglue.com"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='sandbox-key'):
            client = ITGlueClient(instance='sandbox')
            assert client.base_url == 'https://api-sandbox.itglue.com'

    def test_production_instance_uses_correct_url(self):
        """FR4.4: Production instance uses api.itglue.com"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='prod-key'):
            client = ITGlueClient(instance='production')
            assert client.base_url == 'https://api.itglue.com'

    def test_separate_api_keys_per_instance(self):
        """FR4.2: Per-instance API keys stored separately"""
        with patch('claude.tools.integrations.itglue.auth.get_api_key') as mock_get_key:
            mock_get_key.side_effect = lambda instance: f'{instance}-api-key'

            sandbox = ITGlueClient(instance='sandbox')
            production = ITGlueClient(instance='production')

            assert sandbox.api_key == 'sandbox-api-key'
            assert production.api_key == 'production-api-key'


class TestHealthCheck:
    """Test NFR3.4: Health Check"""

    @pytest.fixture
    def client(self):
        with patch('claude.tools.integrations.itglue.auth.get_api_key', return_value='test-key'):
            return ITGlueClient(instance='sandbox')

    def test_health_check_validates_connectivity(self, client):
        """NFR3.4: Health check validates API key + connectivity"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                json=lambda: {'data': []}
            )

            health = client.health_check()
            assert health['status'] == 'healthy'
            assert health['api_key_valid'] is True
            assert 'response_time_ms' in health

    def test_health_check_detects_api_key_invalid(self, client):
        """NFR3.4: Health check detects invalid API key"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=401)

            health = client.health_check()
            assert health['status'] == 'unhealthy'
            assert health['api_key_valid'] is False
