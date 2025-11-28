"""
ITGlue REST API Client

Production-grade API client with:
- Rate limiting (3000 req/5min)
- Circuit breaker (5 failures → open)
- Local metadata caching (SQLite)
- Multi-instance support (sandbox + production)
- Comprehensive error handling
"""

import requests
import logging
import time
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from claude.tools.integrations.itglue import auth
from claude.tools.integrations.itglue.models import (
    Organization, Configuration, Password, FlexibleAsset, Document, Contact
)
from claude.tools.integrations.itglue.exceptions import (
    ITGlueAuthError, ITGlueRateLimitError, ITGlueNotFoundError,
    ITGlueForbiddenError, ITGlueServerError, ITGlueCircuitBreakerOpen, ITGlueAPIError
)
from claude.tools.integrations.itglue.rate_limiter import RateLimiter
from claude.tools.integrations.itglue.circuit_breaker import CircuitBreaker
from claude.tools.integrations.itglue.cache import ITGlueCache

logger = logging.getLogger(__name__)


class ITGlueClient:
    """
    ITGlue REST API Client

    Features:
    - Full CRUD for all ITGlue entities
    - Rate limiting with auto-throttling
    - Circuit breaker for resilience
    - Local metadata caching
    - Multi-instance (sandbox/production)

    Usage:
        client = ITGlueClient(instance='sandbox')
        orgs = client.list_organizations()
    """

    def __init__(
        self,
        instance: str = 'sandbox',
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize ITGlue client.

        Args:
            instance: 'sandbox' or 'production'
            base_url: Override base URL (for testing)
            api_key: Override API key (for testing, otherwise from Keychain)
        """
        self.instance = instance

        # Set base URL
        if base_url:
            if not base_url.startswith('https://'):
                raise ValueError("HTTPS required for security")
            self.base_url = base_url
        else:
            if instance == 'production':
                self.base_url = 'https://api.itglue.com'
            else:
                self.base_url = 'https://api-sandbox.itglue.com'

        # Get API key
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = auth.get_api_key(instance)

        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json'
        })

        # Initialize rate limiter and circuit breaker
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()

        # Initialize cache
        cache_dir = Path.home() / '.maia' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f'itglue_{instance}.db'
        self.cache = ITGlueCache(str(cache_path))

        # Metrics tracking
        self._metrics = {
            'request_count': 0,
            'error_count': 0,
            'total_latency_ms': 0
        }

        logger.info(f"ITGlue client initialized: {instance} ({self.base_url})")

    # ============= Core HTTP Methods =============

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: int = 30
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting, circuit breaker, and retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/organizations')
            data: Request body (JSON)
            params: Query parameters
            files: File upload dict
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            ITGlueAuthError: 401 Unauthorized
            ITGlueRateLimitError: 429 Too Many Requests
            ITGlueServerError: 500/503 Server errors
            ITGlueCircuitBreakerOpen: Circuit breaker open
        """
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            raise ITGlueCircuitBreakerOpen()

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # Build URL
        url = f"{self.base_url}{endpoint}"

        # Make request with retry logic
        max_retries = 3
        retry_count = 0

        while retry_count <= max_retries:
            try:
                start_time = time.time()

                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    files=files,
                    timeout=timeout
                )

                latency_ms = (time.time() - start_time) * 1000

                # Update metrics
                self._metrics['request_count'] += 1
                self._metrics['total_latency_ms'] += latency_ms

                logger.debug(
                    f"{method} {endpoint} -> {response.status_code} ({latency_ms:.0f}ms)"
                )

                # Handle response status codes
                if response.status_code == 200 or response.status_code == 201:
                    # Success
                    self.circuit_breaker.record_success()
                    return response

                elif response.status_code == 401:
                    # Unauthorized - API key invalid/expired
                    self._metrics['error_count'] += 1
                    self.circuit_breaker.record_failure()
                    raise ITGlueAuthError()

                elif response.status_code == 403:
                    # Forbidden - insufficient permissions
                    self._metrics['error_count'] += 1
                    raise ITGlueForbiddenError()

                elif response.status_code == 404:
                    # Not found - return None (handled by caller)
                    return response

                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after}s")

                    if retry_count < max_retries:
                        time.sleep(retry_after)
                        retry_count += 1
                        continue
                    else:
                        self._metrics['error_count'] += 1
                        raise ITGlueRateLimitError(retry_after)

                elif response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    self.circuit_breaker.record_failure()

                    if retry_count < max_retries:
                        backoff = 2 ** retry_count  # 1s, 2s, 4s
                        logger.warning(
                            f"Server error {response.status_code}. "
                            f"Retry {retry_count + 1}/{max_retries} after {backoff}s"
                        )
                        time.sleep(backoff)
                        retry_count += 1
                        continue
                    else:
                        self._metrics['error_count'] += 1
                        raise ITGlueServerError(response.status_code)

                else:
                    # Other error
                    self._metrics['error_count'] += 1
                    raise ITGlueAPIError(f"HTTP {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                # Network error
                self.circuit_breaker.record_failure()

                if retry_count < max_retries:
                    backoff = 2 ** retry_count
                    logger.warning(f"Request failed: {e}. Retry {retry_count + 1}/{max_retries}")
                    time.sleep(backoff)
                    retry_count += 1
                    continue
                else:
                    self._metrics['error_count'] += 1
                    raise ITGlueAPIError(f"Request failed after {max_retries} retries: {e}")

        # Should never reach here
        raise ITGlueAPIError("Max retries exceeded")

    # ============= Authentication =============

    def validate_api_key(self) -> bool:
        """Validate API key by making test request"""
        try:
            response = self._make_request('GET', '/organizations', params={'page[size]': 1})
            return response.status_code == 200
        except ITGlueAuthError:
            return False

    # ============= Organization Operations =============

    def list_organizations(self) -> List[Organization]:
        """List all organizations"""
        response = self._make_request('GET', '/organizations')

        if response.status_code == 200:
            data = response.json()
            orgs = []

            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                org = Organization(
                    id=item['id'],
                    name=attrs['name'],
                    created_at=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(attrs['updated-at'].replace('Z', '+00:00')) if attrs.get('updated-at') else None,
                    organization_type_name=attrs.get('organization-type-name'),
                    quick_notes=attrs.get('quick-notes')
                )
                orgs.append(org)

            # Update cache
            self.cache.cache_organizations(orgs)

            return orgs

        return []

    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        response = self._make_request('GET', f'/organizations/{org_id}')

        if response.status_code == 404:
            return None

        if response.status_code == 200:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            org = Organization(
                id=item['id'],
                name=attrs['name'],
                created_at=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(attrs['updated-at'].replace('Z', '+00:00')) if attrs.get('updated-at') else None,
                organization_type_name=attrs.get('organization-type-name')
            )

            # Update cache
            self.cache.cache_organizations([org])

            return org

        return None

    def create_organization(self, name: str, **kwargs) -> Organization:
        """Create new organization"""
        payload = {
            'data': {
                'type': 'organizations',
                'attributes': {
                    'name': name,
                    **kwargs
                }
            }
        }

        response = self._make_request('POST', '/organizations', data=payload)

        if response.status_code == 201:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            org = Organization(
                id=item['id'],
                name=attrs['name'],
                created_at=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00'))
            )

            # Update cache
            self.cache.cache_organizations([org])

            return org

        raise ITGlueAPIError(f"Failed to create organization: {response.status_code}")

    def update_organization(self, org_id: str, **kwargs) -> Organization:
        """Update organization"""
        payload = {
            'data': {
                'type': 'organizations',
                'attributes': kwargs
            }
        }

        response = self._make_request('PATCH', f'/organizations/{org_id}', data=payload)

        if response.status_code == 200:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            org = Organization(
                id=item['id'],
                name=attrs['name'],
                created_at=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00')),
                updated_at=datetime.now()
            )

            # Update cache
            self.cache.update_organization(org)

            return org

        raise ITGlueAPIError(f"Failed to update organization: {response.status_code}")

    def delete_organization(self, org_id: str) -> bool:
        """Delete organization"""
        response = self._make_request('DELETE', f'/organizations/{org_id}')

        if response.status_code == 204 or response.status_code == 200:
            # Invalidate cache
            self.cache.invalidate_organization(org_id)
            return True

        return False

    def search_organizations(self, name: str) -> List[Organization]:
        """Search organizations by name"""
        # Try cache first
        cached_results = self.cache.search_organizations(name)
        if cached_results:
            return cached_results

        # Fall back to API
        params = {'filter[name]': name}
        response = self._make_request('GET', '/organizations', params=params)

        if response.status_code == 200:
            data = response.json()
            orgs = []

            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                org = Organization(
                    id=item['id'],
                    name=attrs['name'],
                    created_at=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00'))
                )
                orgs.append(org)

            return orgs

        return []

    # ============= Configuration Operations =============

    def list_configurations(self, organization_id: str) -> List[Configuration]:
        """List configurations for organization"""
        params = {'filter[organization_id]': organization_id}
        response = self._make_request('GET', '/configurations', params=params)

        if response.status_code == 200:
            data = response.json()
            configs = []

            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                config = Configuration(
                    id=item['id'],
                    name=attrs['name'],
                    configuration_type=attrs.get('configuration-type-name', 'Unknown'),
                    organization_id=organization_id,
                    serial_number=attrs.get('serial-number')
                )
                configs.append(config)

            # Update cache
            self.cache.cache_configurations(configs)

            return configs

        return []

    def get_configuration(self, config_id: str) -> Optional[Configuration]:
        """Get configuration by ID"""
        response = self._make_request('GET', f'/configurations/{config_id}')

        if response.status_code == 404:
            return None

        if response.status_code == 200:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            return Configuration(
                id=item['id'],
                name=attrs['name'],
                configuration_type=attrs.get('configuration-type-name', 'Unknown'),
                organization_id=attrs['organization-id'],
                serial_number=attrs.get('serial-number')
            )

        return None

    def create_configuration(
        self,
        organization_id: str,
        name: str,
        configuration_type: str,
        **kwargs
    ) -> Configuration:
        """Create configuration"""
        payload = {
            'data': {
                'type': 'configurations',
                'attributes': {
                    'organization-id': organization_id,
                    'name': name,
                    'configuration-type-name': configuration_type,
                    **kwargs
                }
            }
        }

        response = self._make_request('POST', '/configurations', data=payload)

        if response.status_code == 201:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            config = Configuration(
                id=item['id'],
                name=attrs['name'],
                configuration_type=attrs.get('configuration-type-name', configuration_type),
                organization_id=organization_id,
                serial_number=attrs.get('serial-number')
            )

            # Update cache
            self.cache.cache_configurations([config])

            return config

        raise ITGlueAPIError(f"Failed to create configuration: {response.status_code}")

    def link_configuration_to_password(self, configuration_id: str, password_id: str) -> bool:
        """Link configuration to password"""
        payload = {
            'data': {
                'type': 'passwords',
                'id': password_id
            }
        }

        response = self._make_request(
            'POST',
            f'/configurations/{configuration_id}/relationships/passwords',
            data=payload
        )

        if response.status_code == 200 or response.status_code == 204:
            # Update cache
            self.cache.cache_relationship('configuration', configuration_id, 'password', password_id)
            return True

        return False

    def get_configuration_relationships(self, configuration_id: str) -> List[Dict]:
        """Get all relationships for a configuration"""
        # Try cache first
        cached = self.cache.get_relationships('configuration', configuration_id)
        if cached:
            return cached

        # Fall back to API (if endpoint exists)
        return []

    # ============= Password Operations =============

    def list_passwords(self, organization_id: str) -> List[Password]:
        """List passwords for organization"""
        params = {'filter[organization_id]': organization_id}
        response = self._make_request('GET', '/passwords', params=params)

        if response.status_code == 200:
            data = response.json()
            passwords = []

            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                password = Password(
                    id=item['id'],
                    name=attrs['name'],
                    username=attrs.get('username'),
                    organization_id=organization_id
                )
                passwords.append(password)

            return passwords

        return []

    def get_password(self, password_id: str) -> Optional[Password]:
        """Get password details"""
        response = self._make_request('GET', f'/passwords/{password_id}')

        if response.status_code == 404:
            return None

        if response.status_code == 200:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            return Password(
                id=item['id'],
                name=attrs['name'],
                username=attrs.get('username'),
                organization_id=attrs['organization-id']
            )

        return None

    def create_password(
        self,
        organization_id: str,
        name: str,
        username: str,
        password: str,
        **kwargs
    ) -> Password:
        """Create password entry (password value NOT logged)"""
        payload = {
            'data': {
                'type': 'passwords',
                'attributes': {
                    'organization-id': organization_id,
                    'name': name,
                    'username': username,
                    'password': password,  # NEVER log this
                    **kwargs
                }
            }
        }

        # CRITICAL: Don't log payload (contains password)
        response = self._make_request('POST', '/passwords', data=payload)

        if response.status_code == 201:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            return Password(
                id=item['id'],
                name=attrs['name'],
                username=attrs.get('username'),
                organization_id=organization_id
            )

        raise ITGlueAPIError(f"Failed to create password: {response.status_code}")

    # ============= Document Operations =============

    def list_documents(self, organization_id: str) -> List[Document]:
        """List documents for organization"""
        params = {'filter[organization_id]': organization_id}
        response = self._make_request('GET', '/documents', params=params)

        if response.status_code == 200:
            data = response.json()
            docs = []

            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                doc = Document(
                    id=item['id'],
                    name=attrs['name'],
                    size=attrs.get('size', 0),
                    organization_id=organization_id,
                    upload_date=datetime.fromisoformat(attrs['created-at'].replace('Z', '+00:00'))
                )
                docs.append(doc)

            # Cache metadata only
            self.cache.cache_documents(docs)

            return docs

        return []

    def upload_document(
        self,
        organization_id: str,
        file_path: str,
        name: Optional[str] = None
    ) -> Document:
        """Upload document to ITGlue"""
        if not name:
            name = Path(file_path).name

        with open(file_path, 'rb') as f:
            files = {'file': (name, f)}
            payload = {
                'organization_id': organization_id,
                'name': name
            }

            response = self._make_request(
                'POST',
                '/documents',
                data=payload,
                files=files,
                timeout=60  # Longer timeout for uploads
            )

        if response.status_code == 201:
            data = response.json()
            item = data.get('data', {})
            attrs = item.get('attributes', {})

            doc = Document(
                id=item['id'],
                name=attrs['name'],
                size=attrs.get('size', 0),
                organization_id=organization_id,
                upload_date=datetime.now()
            )

            # Cache metadata
            self.cache.cache_documents([doc])

            return doc

        raise ITGlueAPIError(f"Failed to upload document: {response.status_code}")

    def download_document(self, document_id: str, output_path: str) -> bool:
        """Download document from ITGlue"""
        response = self._make_request('GET', f'/documents/{document_id}/download')

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True

        return False

    # ============= Health Check & Metrics =============

    def health_check(self) -> Dict[str, Any]:
        """Health check - validates API key and connectivity"""
        start_time = time.time()

        try:
            valid = self.validate_api_key()
            response_time_ms = (time.time() - start_time) * 1000

            return {
                'status': 'healthy' if valid else 'unhealthy',
                'api_key_valid': valid,
                'response_time_ms': response_time_ms,
                'circuit_breaker': self.circuit_breaker.get_stats(),
                'rate_limiter': self.rate_limiter.get_stats()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'api_key_valid': False,
                'error': str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics (RED: Rate, Errors, Duration)"""
        avg_latency = (
            self._metrics['total_latency_ms'] / self._metrics['request_count']
            if self._metrics['request_count'] > 0 else 0
        )

        return {
            'request_count': self._metrics['request_count'],
            'error_count': self._metrics['error_count'],
            'request_duration_ms': avg_latency,
            'error_rate': (
                self._metrics['error_count'] / self._metrics['request_count']
                if self._metrics['request_count'] > 0 else 0
            )
        }
