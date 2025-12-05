#!/usr/bin/env python3
"""
ManageEngine Patch Manager Plus OAuth 2.0 Manager v2
Environment-aware with TEST/PROD isolation and safety interlocks

SAFETY FEATURES:
- Explicit environment selection required (no default to PROD)
- Separate Keychain accounts per environment
- Separate token files per environment
- Visual banners showing active environment
- Write operation protection for PROD
"""

import json
import os
import time
import webbrowser
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from cryptography.fernet import Fernet
import keyring


class PMPOAuthManagerV2:
    """
    Environment-aware PMP OAuth 2.0 Manager with safety interlocks

    Environments:
    - TEST: naythan.me@londonxyz.com (trial instance)
    - PROD: naythan.dawe@orro.group (production instance)

    Safety Features:
    - Explicit environment selection required
    - Separate credentials per environment
    - Write protection for PROD (requires confirm_prod=True)
    - Visual banners showing active environment
    """

    VALID_ENVIRONMENTS = ['TEST', 'PROD']

    # Environment-specific configuration
    ENV_CONFIG = {
        'TEST': {
            'keychain_account': 'naythan.me@londonxyz.com',
            'keychain_prefix': 'maia_pmp_TEST',
            'token_file': Path.home() / '.maia/credentials/pmp_tokens_TEST.json.enc',
            'color': '\033[92m',  # Green
            'banner_emoji': '🧪',
            'description': 'Trial instance - safe for experimentation'
        },
        'PROD': {
            'keychain_account': 'naythan.dawe@orro.group',
            'keychain_prefix': 'maia_pmp',  # Legacy naming for backward compat
            'token_file': Path.home() / '.maia/credentials/pmp_tokens.json.enc',
            'color': '\033[91m',  # Red
            'banner_emoji': '🚨',
            'description': 'PRODUCTION - Changes affect LIVE systems!'
        }
    }

    AUTH_URL = "https://accounts.zoho.com.au/oauth/v2/auth"
    TOKEN_URL = "https://accounts.zoho.com.au/oauth/v2/token"
    REDIRECT_URI = "http://localhost:8080/oauth2callback"
    SCOPES = "PatchManagerPlusCloud.Common.READ,PatchManagerPlusCloud.PatchMgmt.READ,PatchManagerPlusCloud.PatchMgmt.UPDATE"

    RESET_COLOR = '\033[0m'

    def __init__(self, environment: str = None):
        """
        Initialize OAuth manager with explicit environment selection

        Args:
            environment: 'TEST' or 'PROD' (or set PMP_ENV env var)

        Raises:
            ValueError: If environment not specified or invalid
        """
        # SAFETY: Require explicit environment selection
        if environment is None:
            environment = os.environ.get('PMP_ENV', '').upper()
        else:
            environment = environment.upper()

        if not environment:
            raise ValueError(
                "\n" + "="*60 + "\n"
                "🛑 SAFETY: Environment must be specified!\n"
                "="*60 + "\n\n"
                "Options:\n"
                "  1. Set environment variable: PMP_ENV=TEST\n"
                "  2. Pass to constructor: PMPOAuthManagerV2(environment='TEST')\n\n"
                "Available environments:\n"
                "  - TEST: Trial instance (naythan.me@londonxyz.com)\n"
                "  - PROD: Production instance (naythan.dawe@orro.group)\n"
            )

        if environment not in self.VALID_ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {environment}. Must be one of: {self.VALID_ENVIRONMENTS}")

        self.environment = environment
        self.config = self.ENV_CONFIG[environment]
        self.TOKEN_FILE = self.config['token_file']

        # Print environment banner
        self._print_environment_banner()

        # Load environment-specific credentials from Keychain
        self.client_id = self._get_from_keychain(f"{self.config['keychain_prefix']}_client_id")
        self.client_secret = self._get_from_keychain(f"{self.config['keychain_prefix']}_client_secret")
        self.server_url = self._get_from_keychain(f"{self.config['keychain_prefix']}_server_url")

        # Get or create encryption key (per-environment)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key.encode())

        # Ensure token directory exists
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.request_times = []
        self.rate_limit = 3000
        self.rate_window = 300

    def _print_environment_banner(self):
        """Print clear visual indicator of active environment"""
        cfg = self.config
        color = cfg['color']
        reset = self.RESET_COLOR

        print(f"\n{color}{'='*60}{reset}")
        print(f"{color}{cfg['banner_emoji']} PMP ENVIRONMENT: {self.environment}{reset}")
        print(f"{color}   {cfg['description']}{reset}")
        print(f"{color}   Account: {cfg['keychain_account']}{reset}")
        print(f"{color}{'='*60}{reset}\n")

    def _get_from_keychain(self, service_name: str) -> str:
        """Retrieve credential from macOS Keychain using environment-specific account"""
        try:
            result = subprocess.run(
                ["security", "find-generic-password",
                 "-a", self.config['keychain_account'],
                 "-s", service_name,
                 "-w"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to retrieve {service_name} from Keychain for account {self.config['keychain_account']}.\n"
                f"Run setup first. Error: {e.stderr}"
            )

    def _get_or_create_encryption_key(self) -> str:
        """Get or create Fernet encryption key in Keychain (per-environment)"""
        key_name = f"maia_pmp_{self.environment.lower()}_encryption_key"
        try:
            key = keyring.get_password("maia_pmp", key_name)
            if key:
                return key
        except Exception:
            pass

        key = Fernet.generate_key().decode()
        keyring.set_password("maia_pmp", key_name, key)
        return key

    def _save_tokens(self, tokens: Dict):
        """Save tokens to encrypted file"""
        tokens['expires_at'] = time.time() + tokens.get('expires_in', 3600)
        tokens['environment'] = self.environment  # Tag with environment

        encrypted = self.cipher.encrypt(json.dumps(tokens).encode())
        self.TOKEN_FILE.write_bytes(encrypted)
        self.TOKEN_FILE.chmod(0o600)

    def _load_tokens(self) -> Optional[Dict]:
        """Load tokens from encrypted file"""
        if not self.TOKEN_FILE.exists():
            return None

        try:
            encrypted = self.TOKEN_FILE.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            tokens = json.loads(decrypted)

            # Safety check: verify tokens match current environment
            if tokens.get('environment') and tokens['environment'] != self.environment:
                print(f"⚠️  Token file is for {tokens['environment']}, not {self.environment}. Re-authorize required.")
                return None

            return tokens
        except Exception as e:
            print(f"⚠️  Failed to load tokens: {e}")
            return None

    def _is_token_valid(self, tokens: Dict) -> bool:
        """Check if access token is still valid (with 5-minute buffer)"""
        if not tokens or 'expires_at' not in tokens:
            return False
        return time.time() < (tokens['expires_at'] - 300)

    def _check_rate_limit(self):
        """Enforce rate limiting (3000 req/5min)"""
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]

        if len(self.request_times) >= self.rate_limit:
            oldest = self.request_times[0]
            sleep_time = self.rate_window - (now - oldest)
            if sleep_time > 0:
                print(f"⏱️  Rate limit reached. Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        self.request_times.append(now)

    def _check_write_permission(self, confirm_prod: bool = False):
        """
        Check if write operations are allowed

        PROD write operations require explicit confirmation
        """
        if self.environment == 'PROD' and not confirm_prod:
            raise PermissionError(
                "\n" + "="*60 + "\n"
                "🛑 PRODUCTION WRITE BLOCKED\n"
                "="*60 + "\n\n"
                "To perform write operations on PRODUCTION:\n"
                "  - Pass confirm_prod=True to the method\n"
                "  - Or use PMP_ENV=TEST for testing\n\n"
                "This safety check prevents accidental production changes.\n"
            )

    def generate_auth_url(self) -> str:
        """Generate authorization URL for user to visit"""
        params = {
            'scope': self.SCOPES,
            'client_id': self.client_id,
            'response_type': 'code',
            'access_type': 'offline',
            'redirect_uri': self.REDIRECT_URI,
            'prompt': 'consent'
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def start_callback_server(self) -> str:
        """Start local callback server to capture authorization code"""
        auth_code = None

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                if 'code' in params:
                    auth_code = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to your terminal.</p>
                        </body></html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()

            def log_message(self, format, *args):
                pass

        server = HTTPServer(('localhost', 8080), CallbackHandler)
        print("🌐 Callback server listening on http://localhost:8080")
        print("⏳ Waiting for authorization...")

        server.handle_request()

        if not auth_code:
            raise RuntimeError("Failed to capture authorization code")

        return auth_code

    def exchange_code_for_tokens(self, auth_code: str) -> Dict:
        """Exchange authorization code for access + refresh tokens"""
        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.REDIRECT_URI
        }

        response = requests.post(self.TOKEN_URL, data=data, timeout=(10, 30))

        if response.status_code != 200:
            raise RuntimeError(
                f"Token exchange failed: {response.status_code} - {response.text}"
            )

        tokens = response.json()
        self._save_tokens(tokens)
        return tokens

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        data = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.TOKEN_URL, data=data, timeout=(10, 30))

        if response.status_code != 200:
            raise RuntimeError(
                f"Token refresh failed: {response.status_code} - {response.text}"
            )

        tokens = response.json()
        if 'refresh_token' not in tokens:
            tokens['refresh_token'] = refresh_token

        self._save_tokens(tokens)
        return tokens

    def get_valid_token(self) -> str:
        """Get valid access token (refresh if needed)"""
        tokens = self._load_tokens()

        if tokens and self._is_token_valid(tokens):
            return tokens['access_token']

        if tokens and 'refresh_token' in tokens:
            print(f"🔄 [{self.environment}] Refreshing access token...")
            tokens = self.refresh_access_token(tokens['refresh_token'])
            return tokens['access_token']

        raise RuntimeError(
            f"No valid tokens found for {self.environment}. Run authorize() first."
        )

    def authorize(self):
        """Complete full OAuth authorization flow"""
        cfg = self.config
        color = cfg['color']
        reset = self.RESET_COLOR

        print(f"{color}{'='*60}{reset}")
        print(f"{color}{cfg['banner_emoji']} PMP OAuth Authorization - {self.environment}{reset}")
        print(f"{color}{'='*60}{reset}")

        auth_url = self.generate_auth_url()
        print(f"\n📋 Authorization URL:\n{auth_url}\n")
        print("🚀 Opening browser...")
        webbrowser.open(auth_url)

        auth_code = self.start_callback_server()
        print(f"✅ Authorization code received")

        print("🔄 Exchanging code for tokens...")
        tokens = self.exchange_code_for_tokens(auth_code)

        print(f"\n{color}✅ OAuth Authorization Complete for {self.environment}!{reset}")
        print(f"   Access Token: {tokens['access_token'][:20]}...")
        print(f"   Expires In: {tokens.get('expires_in', 3600)} seconds")
        print(f"   Refresh Token: {'Yes' if 'refresh_token' in tokens else 'No'}")
        print(f"\n💾 Tokens saved to: {self.TOKEN_FILE}")
        print(f"{color}{'='*60}{reset}")

    def api_request(self, method: str, endpoint: str, confirm_prod: bool = False,
                    _retry_count: int = 0, **kwargs) -> requests.Response:
        """
        Make authenticated API request with environment awareness

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            confirm_prod: Required for PROD write operations
            **kwargs: Additional arguments for requests
        """
        # Check write permission for non-GET requests
        if method.upper() != 'GET':
            self._check_write_permission(confirm_prod)

        self._check_rate_limit()

        token = self.get_valid_token()
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Zoho-oauthtoken {token}'

        url = f"{self.server_url}{endpoint}"

        # Log request with environment prefix
        env_prefix = f"[{self.environment}]"
        print(f"   {env_prefix} {method} {endpoint}")

        try:
            response = requests.request(
                method, url, headers=headers, timeout=(10, 30), **kwargs
            )

            if response.status_code == 401 and _retry_count < 1:
                print(f"⚠️  {env_prefix} Token expired. Refreshing...")
                tokens = self._load_tokens()
                if tokens and 'refresh_token' in tokens:
                    self.refresh_access_token(tokens['refresh_token'])
                    return self.api_request(method, endpoint, confirm_prod, _retry_count+1, **kwargs)
                else:
                    raise RuntimeError("Token refresh failed. Re-authorize required.")

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"⚠️  {env_prefix} Rate limited. Retrying in {retry_after}s...")
                time.sleep(retry_after)
                return self.api_request(method, endpoint, confirm_prod, **kwargs)

            elif response.status_code >= 500:
                print(f"⚠️  {env_prefix} Server error: {response.status_code}. Retrying...")
                time.sleep(5)
                return self.api_request(method, endpoint, confirm_prod, **kwargs)

            return response

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")


def main():
    """CLI interface for environment-aware OAuth manager"""
    import sys

    # Check for environment
    env = os.environ.get('PMP_ENV', '').upper()

    if len(sys.argv) < 2:
        print("="*60)
        print("PMP OAuth Manager v2 - Environment-Aware")
        print("="*60)
        print("\nUsage:")
        print("  PMP_ENV=TEST python3 pmp_oauth_manager_v2.py authorize")
        print("  PMP_ENV=TEST python3 pmp_oauth_manager_v2.py test")
        print("  PMP_ENV=TEST python3 pmp_oauth_manager_v2.py refresh")
        print("\nEnvironments:")
        print("  TEST - Trial instance (naythan.me@londonxyz.com)")
        print("  PROD - Production instance (naythan.dawe@orro.group)")
        print("\n🛑 SAFETY: Environment MUST be specified via PMP_ENV")
        sys.exit(1)

    command = sys.argv[1]

    try:
        manager = PMPOAuthManagerV2()  # Will fail if no env specified
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    if command == 'authorize':
        manager.authorize()

    elif command == 'test':
        print(f"🧪 Testing API connectivity for {manager.environment}...")

        print("\n1️⃣  GET /api/1.4/patch/summary")
        response = manager.api_request('GET', '/api/1.4/patch/summary')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")

        print("\n2️⃣  GET /api/1.4/patch/allpatches (first page)")
        response = manager.api_request('GET', '/api/1.4/patch/allpatches', params={'page': 1})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'message_response' in data:
                data = data['message_response']
            total = data.get('total', 'unknown')
            print(f"   ✅ Success: {total} total patches")
        else:
            print(f"   ❌ Failed: {response.text[:200]}")

        print(f"\n✅ API test complete for {manager.environment}!")

    elif command == 'refresh':
        print(f"🔄 Forcing token refresh for {manager.environment}...")
        tokens = manager._load_tokens()
        if tokens and 'refresh_token' in tokens:
            new_tokens = manager.refresh_access_token(tokens['refresh_token'])
            print(f"✅ Token refreshed: {new_tokens['access_token'][:20]}...")
        else:
            print("❌ No refresh token found. Re-authorize required.")

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
