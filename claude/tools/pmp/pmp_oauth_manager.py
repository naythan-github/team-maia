#!/usr/bin/env python3
"""
ManageEngine Patch Manager Plus OAuth 2.0 Manager
Production-grade OAuth implementation with macOS Keychain integration
"""

import json
import time
import webbrowser
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from cryptography.fernet import Fernet
import keyring

class PMPOAuthManager:
    """
    ManageEngine PMP OAuth 2.0 Manager with macOS Keychain integration

    Security Features:
    - Client ID/Secret in macOS Keychain (OS-encrypted)
    - Tokens in encrypted file (Fernet + Keychain key)
    - Auto-refresh before expiry (55-minute timer)
    - Rate limiting (3000 req/5min)
    - Error handling (401, 403, 429, 500)
    """

    AUTH_URL = "https://accounts.zoho.com.au/oauth/v2/auth"
    TOKEN_URL = "https://accounts.zoho.com.au/oauth/v2/token"
    REDIRECT_URI = "http://localhost:8080/oauth2callback"
    SCOPES = "PatchManagerPlusCloud.restapi.READ,PatchManagerPlusCloud.PatchMgmt.READ,PatchManagerPlusCloud.PatchMgmt.UPDATE"

    KEYCHAIN_ACCOUNT = "naythan.dawe@orro.group"
    TOKEN_FILE = Path.home() / ".maia/credentials/pmp_tokens.json.enc"

    def __init__(self):
        """Initialize OAuth manager with Keychain integration"""
        self.client_id = self._get_from_keychain("maia_pmp_client_id")
        self.client_secret = self._get_from_keychain("maia_pmp_client_secret")
        self.server_url = self._get_from_keychain("maia_pmp_server_url")

        # Get or create encryption key in Keychain
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key.encode())

        # Ensure token directory exists
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.request_times = []
        self.rate_limit = 3000  # requests per 5 minutes
        self.rate_window = 300  # 5 minutes in seconds

    def _get_from_keychain(self, service_name: str) -> str:
        """Retrieve credential from macOS Keychain"""
        try:
            result = subprocess.run(
                ["security", "find-generic-password",
                 "-a", self.KEYCHAIN_ACCOUNT,
                 "-s", service_name,
                 "-w"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to retrieve {service_name} from Keychain. "
                f"Run setup first. Error: {e.stderr}"
            )

    def _get_or_create_encryption_key(self) -> str:
        """Get or create Fernet encryption key in Keychain"""
        try:
            key = keyring.get_password("maia_pmp", "encryption_key")
            if key:
                return key
        except Exception:
            pass

        # Create new key
        key = Fernet.generate_key().decode()
        keyring.set_password("maia_pmp", "encryption_key", key)
        return key

    def _save_tokens(self, tokens: Dict):
        """Save tokens to encrypted file"""
        # Add expiry timestamp
        tokens['expires_at'] = time.time() + tokens.get('expires_in', 3600)

        # Encrypt and save
        encrypted = self.cipher.encrypt(json.dumps(tokens).encode())
        self.TOKEN_FILE.write_bytes(encrypted)
        self.TOKEN_FILE.chmod(0o600)  # Owner read/write only

    def _load_tokens(self) -> Optional[Dict]:
        """Load tokens from encrypted file"""
        if not self.TOKEN_FILE.exists():
            return None

        try:
            encrypted = self.TOKEN_FILE.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted)
        except Exception as e:
            print(f"⚠️  Failed to load tokens: {e}")
            return None

    def _is_token_valid(self, tokens: Dict) -> bool:
        """Check if access token is still valid (with 5-minute buffer)"""
        if not tokens or 'expires_at' not in tokens:
            return False
        return time.time() < (tokens['expires_at'] - 300)  # 5-minute buffer

    def _check_rate_limit(self):
        """Enforce rate limiting (3000 req/5min)"""
        now = time.time()
        # Remove requests older than 5 minutes
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]

        if len(self.request_times) >= self.rate_limit:
            oldest = self.request_times[0]
            sleep_time = self.rate_window - (now - oldest)
            if sleep_time > 0:
                print(f"⏱️  Rate limit reached. Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        self.request_times.append(now)

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
                pass  # Suppress logs

        server = HTTPServer(('localhost', 8080), CallbackHandler)
        print("🌐 Callback server listening on http://localhost:8080")
        print("⏳ Waiting for authorization...")

        # Handle one request then shutdown
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
        # Preserve refresh token if not returned
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
            print("🔄 Refreshing access token...")
            tokens = self.refresh_access_token(tokens['refresh_token'])
            return tokens['access_token']

        raise RuntimeError(
            "No valid tokens found. Run authorize() first to complete OAuth flow."
        )

    def authorize(self):
        """Complete full OAuth authorization flow"""
        print("=" * 60)
        print("ManageEngine PMP OAuth 2.0 Authorization")
        print("=" * 60)

        # Generate and open authorization URL
        auth_url = self.generate_auth_url()
        print(f"\n📋 Authorization URL:\n{auth_url}\n")
        print("🚀 Opening browser...")
        webbrowser.open(auth_url)

        # Start callback server
        auth_code = self.start_callback_server()
        print(f"✅ Authorization code received")

        # Exchange for tokens
        print("🔄 Exchanging code for tokens...")
        tokens = self.exchange_code_for_tokens(auth_code)

        print("\n✅ OAuth Authorization Complete!")
        print(f"   Access Token: {tokens['access_token'][:20]}...")
        print(f"   Expires In: {tokens.get('expires_in', 3600)} seconds")
        print(f"   Refresh Token: {'Yes' if 'refresh_token' in tokens else 'No'}")
        print(f"\n💾 Tokens saved to: {self.TOKEN_FILE}")
        print("=" * 60)

    def api_request(self, method: str, endpoint: str, _retry_count: int = 0, **kwargs) -> requests.Response:
        """
        Make authenticated API request with rate limiting and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/1.4/patch/allpatches')
            _retry_count: Internal recursion guard
            **kwargs: Additional arguments for requests (params, json, etc.)
        """
        self._check_rate_limit()

        token = self.get_valid_token()
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Zoho-oauthtoken {token}'

        # Use server_url (patch.manageengine.com.au) not api_domain
        # PMP Cloud uses patch.manageengine.com.au with OAuth tokens
        url = f"{self.server_url}{endpoint}"

        try:
            response = requests.request(
                method, url, headers=headers, timeout=(10, 30), **kwargs
            )

            # Handle common errors
            if response.status_code == 401 and _retry_count < 1:
                print("⚠️  Token expired or invalid. Refreshing...")
                tokens = self._load_tokens()
                if tokens and 'refresh_token' in tokens:
                    self.refresh_access_token(tokens['refresh_token'])
                    # Retry with new token (max 1 retry)
                    return self.api_request(method, endpoint, _retry_count=_retry_count+1, **kwargs)
                else:
                    raise RuntimeError("Token refresh failed. Re-authorize required.")

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"⚠️  Rate limited. Retrying in {retry_after}s...")
                time.sleep(retry_after)
                return self.api_request(method, endpoint, **kwargs)

            elif response.status_code >= 500:
                print(f"⚠️  Server error: {response.status_code}. Retrying...")
                time.sleep(5)
                return self.api_request(method, endpoint, **kwargs)

            if response.status_code >= 400:
                # Log error details for debugging
                error_detail = f"Status: {response.status_code}, Body: {response.text[:200]}"
                print(f"⚠️  API Error Details: {error_detail}")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")


def main():
    """CLI interface for OAuth manager"""
    import sys

    manager = PMPOAuthManager()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 pmp_oauth_manager.py authorize    # Complete OAuth flow")
        print("  python3 pmp_oauth_manager.py test         # Test API connectivity")
        print("  python3 pmp_oauth_manager.py refresh      # Force token refresh")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'authorize':
        manager.authorize()

    elif command == 'test':
        print("🧪 Testing API connectivity...")

        # Test 1: Patch summary
        print("\n1️⃣  GET /api/1.4/patch/summary")
        response = manager.api_request('GET', '/api/1.4/patch/summary')
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   ✅ Success: {data}")

        # Test 2: Patch query (limited)
        print("\n2️⃣  GET /api/1.4/patch/allpatches?limit=5")
        response = manager.api_request('GET', '/api/1.4/patch/allpatches', params={'limit': 5})
        data = response.json()
        patch_count = len(data.get('patches', data.get('data', [])))
        print(f"   ✅ Success: {patch_count} patches returned")

        print("\n✅ All API tests passed!")

    elif command == 'refresh':
        print("🔄 Forcing token refresh...")
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
