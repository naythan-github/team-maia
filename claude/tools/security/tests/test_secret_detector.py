#!/usr/bin/env python3
"""
Tests for Secret Detection System
TDD: Tests written BEFORE implementation
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSecretDetector:
    """Test suite for SecretDetector class"""

    def test_import(self):
        """Tool should be importable"""
        from secret_detector import SecretDetector
        assert SecretDetector is not None

    def test_instantiation(self):
        """Should create instance without errors"""
        from secret_detector import SecretDetector
        detector = SecretDetector()
        assert detector is not None

    def test_detect_api_keys(self):
        """Should detect common API key patterns"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        api_keys = [
            "AKIAIOSFODNN7EXAMPLE",  # AWS Access Key
            "sk-proj-abc123def456ghi789jkl012mno345",  # OpenAI style
            "ghp_1234567890abcdefghijklmnopqrstuvwx",  # GitHub PAT
            "xoxb-123456789012-1234567890123-AbCdEfGhIjKlMnOpQrStUvWx",  # Slack
        ]

        for key in api_keys:
            result = detector.scan_text(f"API_KEY={key}")
            assert len(result['findings']) > 0, f"Failed to detect: {key}"

    def test_detect_private_keys(self):
        """Should detect private key patterns"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy
-----END RSA PRIVATE KEY-----"""

        result = detector.scan_text(private_key)
        assert len(result['findings']) > 0
        assert any('private_key' in f['type'].lower() for f in result['findings'])

    def test_detect_passwords(self):
        """Should detect password patterns"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        password_texts = [
            'password = "SuperSecret123!"',
            'PASSWORD=hunter2',
            'db_password: "my$ecretP@ss"',
            'PASSWD="notasecret"',
        ]

        for text in password_texts:
            result = detector.scan_text(text)
            assert len(result['findings']) > 0, f"Failed to detect password in: {text}"

    def test_detect_connection_strings(self):
        """Should detect database connection strings"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        conn_strings = [
            "mongodb://user:password123@localhost:27017/db",
            "postgresql://admin:secret@db.example.com:5432/production",
            "mysql://root:pass@127.0.0.1/mydb",
        ]

        for conn in conn_strings:
            result = detector.scan_text(conn)
            assert len(result['findings']) > 0, f"Failed to detect: {conn}"

    def test_no_false_positives_on_placeholders(self):
        """Should not flag obvious placeholders"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        placeholders = [
            "API_KEY=your-api-key-here",
            "password=<INSERT_PASSWORD>",
            "token=REPLACE_ME",
            "secret=${SECRET_FROM_ENV}",
            "key=xxxxxxxxxxxxxxx",
        ]

        for placeholder in placeholders:
            result = detector.scan_text(placeholder)
            # Should either not detect or flag as low confidence
            if len(result['findings']) > 0:
                assert all(f['confidence'] < 0.5 for f in result['findings']), \
                    f"False positive on placeholder: {placeholder}"

    def test_scan_file(self):
        """Should scan files for secrets"""
        from secret_detector import SecretDetector
        import tempfile
        import os

        detector = SecretDetector()

        # Create temp file with a secret
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('API_KEY = "sk-test123456789abcdefghij"\n')
            f.write('def main():\n')
            f.write('    pass\n')
            temp_path = f.name

        try:
            result = detector.scan_file(temp_path)
            assert len(result['findings']) > 0
            assert result['file_path'] == temp_path
        finally:
            os.unlink(temp_path)

    def test_detect_jwt_tokens(self):
        """Should detect JWT tokens"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = detector.scan_text(f"Authorization: Bearer {jwt}")
        assert len(result['findings']) > 0

    def test_severity_levels(self):
        """Should assign severity levels to findings"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        result = detector.scan_text('aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"')
        assert len(result['findings']) > 0
        assert 'severity' in result['findings'][0]
        assert result['findings'][0]['severity'] in ['critical', 'high', 'medium', 'low']

    def test_get_stats(self):
        """Should track detection statistics"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        detector.scan_text("normal text without secrets")
        detector.scan_text("API_KEY=sk-secret123456")

        stats = detector.get_stats()
        assert 'total_scans' in stats
        assert stats['total_scans'] >= 2


class TestSecretPatterns:
    """Test specific secret patterns"""

    def test_cloud_provider_keys(self):
        """Should detect various cloud provider credentials"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        cloud_secrets = [
            ("AWS", "AKIAIOSFODNN7EXAMPLE"),
            ("Azure", "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=abc123=="),
            ("GCP", '"type": "service_account"'),
        ]

        for provider, secret in cloud_secrets:
            result = detector.scan_text(secret)
            assert len(result['findings']) > 0, f"Failed to detect {provider} credential"

    def test_env_file_format(self):
        """Should detect secrets in .env file format"""
        from secret_detector import SecretDetector
        detector = SecretDetector()

        env_content = """
DATABASE_URL=postgres://user:secretpass@localhost/db
STRIPE_SECRET_KEY=sk_live_abc123xyz789
SENDGRID_API_KEY=SG.abcdefghij.klmnopqrstuvwxyz
"""
        result = detector.scan_text(env_content)
        assert len(result['findings']) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
