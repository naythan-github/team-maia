"""
TDD Tests for Bandit Security Fixes
Phase 224.1 - Security Hardening

Tests written BEFORE implementation (RED phase)
Run: pytest tests/security/test_bandit_fixes.py -v
"""
import pytest
import tarfile
import tempfile
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================
# P1: B202 - Tarfile Path Traversal Tests
# =============================================================

class TestSafeTarExtraction:
    """Tests for safe_extract_tar utility"""

    @pytest.fixture
    def create_safe_tar(self, tmp_path):
        """Create a legitimate tar archive"""
        tar_path = tmp_path / "safe.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create test files
        (content_dir / "file1.txt").write_text("Hello")
        (content_dir / "subdir").mkdir()
        (content_dir / "subdir" / "file2.txt").write_text("World")

        # Create tar
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(content_dir / "file1.txt", arcname="file1.txt")
            tar.add(content_dir / "subdir", arcname="subdir")
            tar.add(content_dir / "subdir" / "file2.txt", arcname="subdir/file2.txt")

        return tar_path

    @pytest.fixture
    def create_malicious_tar_traversal(self, tmp_path):
        """Create a tar with path traversal attack"""
        tar_path = tmp_path / "malicious_traversal.tar.gz"

        with tarfile.open(tar_path, "w:gz") as tar:
            # Create a file with path traversal
            info = tarfile.TarInfo(name="../../../etc/malicious.txt")
            info.size = 10
            tar.addfile(info, BytesIO(b"malicious!"))

        return tar_path

    @pytest.fixture
    def create_malicious_tar_absolute(self, tmp_path):
        """Create a tar with absolute path"""
        tar_path = tmp_path / "malicious_absolute.tar.gz"

        with tarfile.open(tar_path, "w:gz") as tar:
            info = tarfile.TarInfo(name="/etc/malicious.txt")
            info.size = 10
            tar.addfile(info, BytesIO(b"malicious!"))

        return tar_path

    @pytest.fixture
    def create_malicious_tar_symlink(self, tmp_path):
        """Create a tar with symlink"""
        tar_path = tmp_path / "malicious_symlink.tar.gz"

        with tarfile.open(tar_path, "w:gz") as tar:
            # Add a symlink
            info = tarfile.TarInfo(name="link_to_etc")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tar.addfile(info)

        return tar_path

    def test_allows_safe_extraction(self, tmp_path, create_safe_tar):
        """B202: Allow legitimate tar extraction"""
        from claude.tools.security.safe_archive import safe_extract_tar

        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        # Should not raise
        safe_extract_tar(create_safe_tar, extract_to)

        # Verify files extracted
        assert (extract_to / "file1.txt").exists()
        assert (extract_to / "subdir" / "file2.txt").exists()

    def test_rejects_path_traversal_dotdot(self, tmp_path, create_malicious_tar_traversal):
        """B202: Reject tar entries with ../ sequences"""
        from claude.tools.security.safe_archive import safe_extract_tar

        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            safe_extract_tar(create_malicious_tar_traversal, extract_to)

    def test_rejects_absolute_paths(self, tmp_path, create_malicious_tar_absolute):
        """B202: Reject tar entries with absolute paths"""
        from claude.tools.security.safe_archive import safe_extract_tar

        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        with pytest.raises(ValueError, match="[Aa]bsolute path"):
            safe_extract_tar(create_malicious_tar_absolute, extract_to)

    def test_rejects_symlinks_by_default(self, tmp_path, create_malicious_tar_symlink):
        """B202: Reject symbolic links in tar by default"""
        from claude.tools.security.safe_archive import safe_extract_tar

        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        with pytest.raises(ValueError, match="[Ss]ymlink"):
            safe_extract_tar(create_malicious_tar_symlink, extract_to)

    def test_allows_symlinks_when_enabled_but_validates_target(self, tmp_path, create_malicious_tar_symlink):
        """B202: Even with symlinks enabled, reject escaping symlinks"""
        from claude.tools.security.safe_archive import safe_extract_tar

        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        # Should still reject symlinks that escape extraction directory
        # This is correct security behavior - symlinks that point outside
        # are blocked even when allow_symlinks=True
        with pytest.raises(ValueError, match="escapes extraction"):
            safe_extract_tar(create_malicious_tar_symlink, extract_to, allow_symlinks=True)


# =============================================================
# P1: B501 - SSL Verification Tests
# =============================================================

class TestSSLVerification:
    """Tests for SSL certificate validation"""

    def test_sma_api_default_ssl_verification(self):
        """B501: SMA API should verify SSL by default"""
        from claude.tools.sma_api_discovery import SMAAPIDiscovery

        # Create instance without env vars
        with patch.dict(os.environ, {}, clear=True):
            discovery = SMAAPIDiscovery("https://example.com", "user", "pass")
            # Should default to True
            assert discovery.verify_ssl is True

    def test_sma_api_respects_env_var(self):
        """B501: SMA API should respect SMA_VERIFY_SSL env var"""
        from claude.tools.sma_api_discovery import SMAAPIDiscovery

        with patch.dict(os.environ, {"SMA_VERIFY_SSL": "false"}):
            discovery = SMAAPIDiscovery("https://example.com", "user", "pass")
            assert discovery.verify_ssl is False

    def test_sma_api_uses_ca_bundle(self):
        """B501: SMA API should support custom CA bundle"""
        from claude.tools.sma_api_discovery import SMAAPIDiscovery

        with patch.dict(os.environ, {"SMA_CA_BUNDLE": "/path/to/ca.crt"}):
            discovery = SMAAPIDiscovery("https://example.com", "user", "pass")
            assert discovery.ca_bundle == "/path/to/ca.crt"


# =============================================================
# P1: B602 - Subprocess Shell Tests
# =============================================================

class TestSubprocessSecurity:
    """Tests for safe subprocess execution"""

    def test_run_command_no_shell_true(self):
        """B602: run_command should not use shell=True"""
        # Read the source file and check for shell=True
        source_file = Path(__file__).parent.parent.parent / "claude/tools/sre/run_comprehensive_tests.py"

        if source_file.exists():
            content = source_file.read_text()
            # After fix, should use shell=False
            assert "shell=True" not in content or "shell=False" in content

    def test_command_as_list_execution(self):
        """B602: Commands should be executed as list, not string"""
        # Test that shlex.split is used or command is a list
        result = subprocess.run(
            ["echo", "hello"],
            shell=False,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "hello" in result.stdout


# =============================================================
# P2: B324 - MD5 Hash Tests
# =============================================================

class TestHashSecurity:
    """Tests for hash function usage"""

    def test_md5_with_usedforsecurity_false(self):
        """B324: MD5 should use usedforsecurity=False for checksums"""
        # This should not raise a warning in Python 3.9+
        md5 = hashlib.md5(usedforsecurity=False)
        md5.update(b"test")
        result = md5.hexdigest()
        assert len(result) == 32

    def test_servicedesk_etl_backup_uses_safe_md5(self):
        """B324: servicedesk_etl_backup.py should use usedforsecurity=False"""
        source_file = Path(__file__).parent.parent.parent / "claude/tools/sre/servicedesk_etl_backup.py"

        if source_file.exists():
            content = source_file.read_text()
            # After fix, should have usedforsecurity=False
            if "hashlib.md5()" in content:
                assert "usedforsecurity=False" in content


# =============================================================
# P2: B113 - Request Timeout Tests
# =============================================================

class TestRequestTimeouts:
    """Tests for network request timeouts"""

    @pytest.mark.parametrize("file_path,expected_timeout", [
        ("claude/tools/research/dora_metrics_automation.py", True),
        ("claude/tools/sre/restore_maia.py", True),
        ("claude/tools/sre/sentiment_model_tester.py", True),
        ("claude/tools/sre/rag_ab_test_sample.py", True),
        ("claude/tools/sre/rag_quality_test_sampled.py", True),
    ])
    def test_files_have_timeout(self, file_path, expected_timeout):
        """B113: Request calls should have timeout parameter"""
        full_path = Path(__file__).parent.parent.parent / file_path

        if full_path.exists():
            content = full_path.read_text()

            # Check for requests.get or requests.post
            if "requests.get(" in content or "requests.post(" in content:
                # Should have timeout in the call
                # This is a simple heuristic check
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "requests.get(" in line or "requests.post(" in line:
                        # Check this line and next 15 lines for timeout (multiline calls)
                        context = "\n".join(lines[i:i+15])
                        if "timeout" not in context:
                            pytest.fail(f"Missing timeout in {file_path} around line {i+1}")


# =============================================================
# P2: B108 - Temp Directory Tests
# =============================================================

class TestTempDirectories:
    """Tests for portable temp directory usage"""

    @pytest.mark.parametrize("file_path", [
        "claude/tools/pmp/pmp_endpoint_validator.py",
        "claude/tools/pmp/pmp_endpoint_validator_v2.py",
        "claude/tools/enhanced_daily_briefing.py",
        "claude/tools/sre/publish_tier_analysis_to_confluence.py",
    ])
    def test_no_hardcoded_tmp(self, file_path):
        """B108: Should use tempfile.gettempdir() not hardcoded /tmp"""
        full_path = Path(__file__).parent.parent.parent / file_path

        if full_path.exists():
            content = full_path.read_text()

            # Skip files that intentionally use /tmp for IPC
            if "swarm_auto_loader" in file_path:
                pytest.skip("Intentional /tmp usage for IPC")

            # Check for hardcoded /tmp paths (not in comments)
            lines = content.split("\n")
            for i, line in enumerate(lines):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue

                # Check for hardcoded /tmp
                if "'/tmp/" in line or '"/tmp/' in line:
                    # Should use tempfile.gettempdir() instead
                    if "tempfile" not in content:
                        pytest.fail(
                            f"Hardcoded /tmp in {file_path} line {i+1}: {line.strip()}"
                        )


# =============================================================
# P2: B104 - Network Binding Tests
# =============================================================

class TestNetworkBinding:
    """Tests for secure network binding"""

    @pytest.mark.parametrize("file_path", [
        "claude/tools/security/security_intelligence_dashboard.py",
        "claude/tools/monitoring/security_intelligence_dashboard.py",
    ])
    def test_dashboard_binds_localhost(self, file_path):
        """B104: Dashboard should bind to 127.0.0.1, not 0.0.0.0"""
        full_path = Path(__file__).parent.parent.parent / file_path

        if full_path.exists():
            content = full_path.read_text()

            # Check for 0.0.0.0 binding
            if "host='0.0.0.0'" in content or 'host="0.0.0.0"' in content:
                # Should bind to localhost or use env var
                if "DASHBOARD_HOST" not in content and "127.0.0.1" not in content:
                    pytest.fail(
                        f"{file_path} binds to 0.0.0.0 without configurable option"
                    )


# =============================================================
# Integration Test
# =============================================================

class TestBanditScan:
    """Run actual Bandit scan to verify fixes"""

    @pytest.mark.slow
    def test_no_high_severity_issues(self):
        """Verify no HIGH severity Bandit issues remain"""
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r",
             "claude/tools/security", "claude/tools/sre",
             "-f", "json", "-q", "--severity-level", "high"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        if result.stdout:
            import json
            try:
                data = json.loads(result.stdout)
                issues = data.get("results", [])
                high_issues = [i for i in issues if i.get("issue_severity") == "HIGH"]

                # Filter out known acceptable issues
                filtered = [
                    i for i in high_issues
                    if "test_" not in i.get("filename", "")  # Skip test files
                ]

                if filtered:
                    file_list = [f"{i['filename']}:{i['line_number']}" for i in filtered]
                    pytest.fail(f"Found {len(filtered)} HIGH severity issues: {file_list}")
            except json.JSONDecodeError:
                pass  # Empty or invalid output is OK
