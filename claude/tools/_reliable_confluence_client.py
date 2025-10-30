#!/usr/bin/env python3
"""
Reliable Confluence Client with SRE Best Practices
Implements retry logic, circuit breakers, health checks, and monitoring

ENHANCEMENTS (Phase 122):
- Integrated ConfluencePageBuilder for validated HTML generation
- Added validate_confluence_html() for pre-flight checks
- Added create_interview_prep_page() helper method
"""

import os
import sys
import time
import json
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

# Import HTML builder for validated content generation
try:
    from claude.tools.confluence_html_builder import (
        ConfluencePageBuilder,
        validate_confluence_html,
        create_interview_prep_html
    )
    HTML_BUILDER_AVAILABLE = True
except ImportError:
    HTML_BUILDER_AVAILABLE = False
    logging.warning("ConfluencePageBuilder not available - HTML validation disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Service health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

@dataclass
class ServiceMetrics:
    """Track service reliability metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    average_latency: float = 0.0
    circuit_open: bool = False
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        return 100 - self.success_rate

class CircuitBreaker:
    """Circuit breaker pattern for failure isolation"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def call_succeeded(self):
        """Reset on success"""
        self.failure_count = 0
        self.state = "closed"
        
    def call_failed(self):
        """Track failures and open circuit if threshold reached"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
            
    def is_available(self) -> bool:
        """Check if service calls are allowed"""
        if self.state == "closed":
            return True
            
        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                time_passed = (datetime.now() - self.last_failure_time).seconds
                if time_passed > self.timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker moved to HALF-OPEN state")
                    return True
            return False
            
        return True  # half-open state allows one test call

class ReliableConfluenceClient:
    """
    Production-grade Confluence client with reliability patterns:
    - Exponential backoff retry logic
    - Circuit breaker for cascading failure prevention
    - Health checks and monitoring
    - Comprehensive error handling
    - Request/response validation
    """
    
    def __init__(self):
        # Confluence configuration
        self.base_url = "https://vivoemc.atlassian.net"
        self.email = "atlas.n@londonxyz.com"
        
        # API token - in production, use environment variable or secret manager
        self.api_token = os.environ.get('CONFLUENCE_API_TOKEN', 'ATATT3xFfGF0fnqzG5roVee1aNwfi7O9hzHebtXZc4DFwwVmgVuJZXZtZdzyyvplTzOM0dgUYAa9fcJoIacNmWlxhaAFBKDJeSNFegJPP1UarN_Bj3kG0ct4T8avPmVXEhO_h-iuPzhDzV8kWYtpz9l7WM8Feiw9mqNcmncioNtlsCf8ihi3Gek=5270FC8E')
        
        # Initialize monitoring
        self.metrics = ServiceMetrics()
        self.circuit_breaker = CircuitBreaker()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.backoff_multiplier = 2
        
        # Request timeout
        self.timeout = 30  # seconds
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.auth = (self.email, self.api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic and circuit breaker
        """
        if not self.circuit_breaker.is_available():
            logger.error("Circuit breaker is OPEN - refusing new requests")
            self.metrics.failed_requests += 1
            return None
            
        url = f"{self.base_url}/wiki/rest/api{endpoint}"
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                start_time = time.time()
                
                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Track latency
                latency = time.time() - start_time
                self._update_latency(latency)
                
                # Check response
                response.raise_for_status()
                
                # Success - update metrics
                self.metrics.successful_requests += 1
                self.metrics.total_requests += 1
                self.metrics.last_success = datetime.now()
                self.circuit_breaker.call_succeeded()
                
                logger.info(f"Request successful: {method} {endpoint} (latency: {latency:.2f}s)")
                return response
                
            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout after {self.timeout}s"
                logger.warning(f"Timeout on attempt {retry_count + 1}: {endpoint}")
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Connection error on attempt {retry_count + 1}: {endpoint}")
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Rate limited
                    retry_after = response.headers.get('Retry-After', self.retry_delay)
                    logger.warning(f"Rate limited - waiting {retry_after}s")
                    time.sleep(int(retry_after))
                    retry_count += 1
                    continue
                    
                last_error = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"HTTP error on attempt {retry_count + 1}: {last_error}")
                
                # Don't retry client errors (4xx except 429)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    break
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error on attempt {retry_count + 1}: {last_error}")
                
            # Exponential backoff
            retry_count += 1
            if retry_count < self.max_retries:
                delay = self.retry_delay * (self.backoff_multiplier ** (retry_count - 1))
                logger.info(f"Retrying in {delay}s... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(delay)
        
        # All retries failed
        self.metrics.failed_requests += 1
        self.metrics.total_requests += 1
        self.metrics.last_failure = datetime.now()
        self.circuit_breaker.call_failed()
        
        logger.error(f"Request failed after {retry_count} attempts: {last_error}")
        return None
        
    def _update_latency(self, latency: float):
        """Update average latency metric"""
        if self.metrics.average_latency == 0:
            self.metrics.average_latency = latency
        else:
            # Exponential moving average
            alpha = 0.3
            self.metrics.average_latency = (alpha * latency + 
                                           (1 - alpha) * self.metrics.average_latency)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return service status
        """
        health_status = HealthStatus.HEALTHY
        issues = []
        
        # Check circuit breaker
        if self.circuit_breaker.state == "open":
            health_status = HealthStatus.UNHEALTHY
            issues.append("Circuit breaker is open")
            
        # Check success rate
        if self.metrics.total_requests > 10:  # Need minimum samples
            if self.metrics.success_rate < 50:
                health_status = HealthStatus.UNHEALTHY
                issues.append(f"Low success rate: {self.metrics.success_rate:.1f}%")
            elif self.metrics.success_rate < 90:
                health_status = HealthStatus.DEGRADED
                issues.append(f"Degraded success rate: {self.metrics.success_rate:.1f}%")
                
        # Check latency
        if self.metrics.average_latency > 5:
            if health_status == HealthStatus.HEALTHY:
                health_status = HealthStatus.DEGRADED
            issues.append(f"High latency: {self.metrics.average_latency:.2f}s")
            
        # Test connection
        test_response = self._make_request('GET', '/space')
        if not test_response:
            health_status = HealthStatus.UNHEALTHY
            issues.append("Cannot connect to Confluence API")
            
        return {
            "status": health_status.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": f"{self.metrics.success_rate:.1f}%",
                "error_rate": f"{self.metrics.error_rate:.1f}%",
                "average_latency": f"{self.metrics.average_latency:.2f}s",
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_success": self.metrics.last_success.isoformat() if self.metrics.last_success else None,
                "last_failure": self.metrics.last_failure.isoformat() if self.metrics.last_failure else None
            },
            "issues": issues
        }
        
    def list_spaces(self) -> Optional[List[Dict]]:
        """List all accessible Confluence spaces"""
        response = self._make_request('GET', '/space', params={'limit': 100})
        if response:
            data = response.json()
            return data.get('results', [])
        return None

    def get_page(self, page_id: str, expand: str = 'body.storage,version') -> Optional[Dict]:
        """
        Get a Confluence page by ID

        Args:
            page_id: Confluence page ID
            expand: Comma-separated list of properties to expand (default: body.storage,version)

        Returns:
            Page data dictionary or None if failed
        """
        response = self._make_request('GET', f'/content/{page_id}', params={'expand': expand})
        if response:
            return response.json()
        return None
        
    def create_page(self, space_key: str, title: str, content: str,
                   parent_id: Optional[str] = None, validate_html: bool = True) -> Optional[Dict]:
        """
        Create a new Confluence page with HTML validation

        Args:
            space_key: Confluence space key
            title: Page title
            content: Confluence storage format HTML content
            parent_id: Optional parent page ID
            validate_html: Run HTML validation before creating (default: True)

        Returns:
            Dict with page_id, title, url, version or None if failed
        """
        # Input validation
        if not space_key or not title or not content:
            logger.error("Missing required parameters: space_key, title, or content")
            return None

        # HTML validation (Phase 122 enhancement)
        if validate_html and HTML_BUILDER_AVAILABLE:
            validation_result = validate_confluence_html(content)
            if not validation_result.is_valid:
                logger.error(f"HTML validation failed before API call:")
                for error in validation_result.errors:
                    logger.error(f"  - {error}")
                raise ValueError(f"Invalid Confluence HTML: {validation_result.errors}")

            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(f"HTML validation warning: {warning}")

        # Build request body
        body = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        if parent_id:
            body["ancestors"] = [{"id": parent_id}]

        # Create page
        response = self._make_request('POST', '/content', json=body)
        if response:
            page_data = response.json()
            page_url = f"{self.base_url}/wiki/spaces/{space_key}/pages/{page_data['id']}"
            logger.info(f"Page created successfully: {page_url}")
            return {
                "id": page_data['id'],
                "title": page_data['title'],
                "url": page_url,
                "version": page_data['version']['number']
            }
        return None
        
    def update_page(self, page_id: str, title: str, content: str, 
                   version_number: int) -> Optional[Dict]:
        """
        Update an existing Confluence page
        """
        # Input validation
        if not page_id or not title or not content:
            logger.error("Missing required parameters")
            return None
            
        body = {
            "version": {"number": version_number},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        response = self._make_request('PUT', f'/content/{page_id}', json=body)
        if response:
            page_data = response.json()
            return {
                "id": page_data['id'],
                "title": page_data['title'],
                "version": page_data['version']['number']
            }
        return None
    
    def move_page_to_parent(self, page_id: str, new_parent_id: str) -> Optional[Dict]:
        """
        Move a page to a new parent by updating its ancestors
        """
        # First get the current page to get its current version and content
        page_response = self._make_request('GET', f'/content/{page_id}?expand=body.storage,version')
        if not page_response:
            logger.error(f"Failed to retrieve page {page_id}")
            return None
            
        page_data = page_response.json()
        current_version = page_data['version']['number']
        
        # Build update body with new parent
        body = {
            "version": {"number": current_version + 1},
            "title": page_data['title'],
            "type": "page",
            "body": {
                "storage": {
                    "value": page_data['body']['storage']['value'],
                    "representation": "storage"
                }
            },
            "ancestors": [{"id": new_parent_id}]
        }
        
        response = self._make_request('PUT', f'/content/{page_id}', json=body)
        if response:
            updated_data = response.json()
            logger.info(f"Page {page_id} moved to parent {new_parent_id}")
            return {
                "id": updated_data['id'],
                "title": updated_data['title'],
                "version": updated_data['version']['number'],
                "parent_id": new_parent_id
            }
        return None

    def create_interview_prep_page(
        self,
        space_key: str,
        candidate_name: str,
        role: str,
        assessment_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create interview prep page using validated HTML builder (Phase 122)

        Args:
            space_key: Confluence space key (e.g., "Orro")
            candidate_name: Candidate's full name
            role: Job role/title
            assessment_data: Dict containing:
                - score: int (0-100)
                - summary: str (assessment summary)
                - strengths: List[str]
                - concerns: List[str]
                - question_sections: Dict[str, List[Dict]]
                - scoring_criteria: List[Dict]
                - recommendation: str

        Returns:
            Page URL if successful, None otherwise

        Example:
            client = ReliableConfluenceClient()
            url = client.create_interview_prep_page(
                space_key="Orro",
                candidate_name="John Doe",
                role="Senior Engineer",
                assessment_data={
                    "score": 75,
                    "summary": "Strong technical candidate",
                    "strengths": ["10+ years experience", "Azure expert"],
                    "concerns": ["Limited leadership"],
                    "question_sections": {
                        "Technical": [{"question": "...", "looking_for": "...", "red_flag": "..."}]
                    },
                    "scoring_criteria": [{"criteria": "Technical", "weight": "50%", "notes": "Must be 8+"}],
                    "recommendation": "PROCEED TO INTERVIEW"
                }
            )
        """
        if not HTML_BUILDER_AVAILABLE:
            logger.error("ConfluencePageBuilder not available - cannot create interview prep page")
            return None

        try:
            # Generate HTML using validated builder
            html_content = create_interview_prep_html(
                candidate_name=candidate_name,
                role=role,
                score=assessment_data['score'],
                assessment_summary=assessment_data['summary'],
                strengths=assessment_data['strengths'],
                concerns=assessment_data['concerns'],
                question_sections=assessment_data['question_sections'],
                scoring_criteria=assessment_data['scoring_criteria'],
                recommendation=assessment_data['recommendation']
            )

            # Create page (validation happens automatically)
            page_title = f"Interview Prep - {candidate_name} ({role})"
            result = self.create_page(
                space_key=space_key,
                title=page_title,
                content=html_content,
                validate_html=True  # Force validation
            )

            if result:
                logger.info(f"Interview prep page created: {result['url']}")
                return result['url']

            return None

        except Exception as e:
            logger.error(f"Failed to create interview prep page: {e}")
            return None

    def search_content(self, query: str, space_key: Optional[str] = None, 
                      limit: int = 25) -> Optional[List[Dict]]:
        """
        Search Confluence content with CQL
        """
        # Build CQL query - handle empty query case
        cql_parts = []
        
        if query and query.strip():
            cql_parts.append(f'text ~ "{query.strip()}"')
        
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
            
        # If no query provided, search all content in space (or all spaces)
        if not cql_parts:
            cql = 'type = "page"'
        else:
            cql = ' AND '.join(cql_parts)
            # Ensure we're only getting pages if no specific query
            if not query or not query.strip():
                cql += ' AND type = "page"'
            
        params = {
            'cql': cql,
            'limit': limit
        }
        
        response = self._make_request('GET', '/content/search', params=params)
        if response:
            data = response.json()
            return data.get('results', [])
        return None
        
    def get_metrics_summary(self) -> str:
        """Get formatted metrics summary for monitoring"""
        return f"""
=== Confluence Client Metrics ===
Total Requests: {self.metrics.total_requests}
Success Rate: {self.metrics.success_rate:.1f}%
Error Rate: {self.metrics.error_rate:.1f}%
Average Latency: {self.metrics.average_latency:.2f}s
Circuit Breaker: {self.circuit_breaker.state}
Last Success: {self.metrics.last_success}
Last Failure: {self.metrics.last_failure}
================================
"""

# Convenience functions for backward compatibility
def create_confluence_page(space_key: str, title: str, content: str) -> Optional[Dict]:
    """Create page with automatic client initialization"""
    client = ReliableConfluenceClient()
    return client.create_page(space_key, title, content)

def test_confluence_connection() -> bool:
    """Test connection and return health status"""
    client = ReliableConfluenceClient()
    health = client.health_check()
    print(json.dumps(health, indent=2))
    return health['status'] == 'healthy'

def list_confluence_spaces() -> Optional[List[Dict]]:
    """List all accessible spaces"""
    client = ReliableConfluenceClient()
    return client.list_spaces()

# Testing and monitoring
if __name__ == "__main__":
    print("🔧 Reliable Confluence Client - SRE Edition")
    print("=" * 50)
    
    client = ReliableConfluenceClient()
    
    # Run health check
    print("\n📊 Running health check...")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # List spaces to verify access
    print("\n📂 Listing accessible spaces...")
    spaces = client.list_spaces()
    if spaces:
        for space in spaces:  # Show all spaces
            print(f"  - {space['key']}: {space['name']}")
    
    # Show metrics
    print(client.get_metrics_summary())