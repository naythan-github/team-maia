#!/usr/bin/env python3
"""
TDD Tests for Azure Environment Discovery Capability Registration

Tests that the new Azure discovery protocol and script are correctly registered
in the capabilities database.
"""

import pytest
import sqlite3
from pathlib import Path
from claude.tools.core.paths import MAIA_ROOT


class TestAzureDiscoveryCapabilityRegistration:
    """Tests for registering Azure environment discovery in capabilities.db"""

    @pytest.fixture
    def capabilities_db_path(self):
        """Path to capabilities database."""
        return MAIA_ROOT / "claude/data/databases/system/capabilities.db"

    def test_capabilities_db_exists(self, capabilities_db_path):
        """Test that capabilities database exists."""
        assert capabilities_db_path.exists(), f"Capabilities DB not found at {capabilities_db_path}"

    def test_azure_discovery_protocol_registered(self, capabilities_db_path):
        """Test that azure_environment_discovery.md is registered as a capability."""
        conn = sqlite3.connect(capabilities_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, path, type, category, keywords
            FROM capabilities
            WHERE name = 'azure_environment_discovery'
        """)

        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Azure environment discovery protocol not found in capabilities.db"

        name, path, cap_type, category, keywords = result
        assert name == "azure_environment_discovery"
        assert "claude/context/protocols/azure_environment_discovery.md" in path
        assert cap_type == "protocol"
        assert category == "azure_operations"
        assert "azure" in keywords.lower()
        assert "environment" in keywords.lower()
        assert "discovery" in keywords.lower()

    def test_azure_discovery_script_registered(self, capabilities_db_path):
        """Test that environment_discovery.ps1 is registered as a tool."""
        conn = sqlite3.connect(capabilities_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, path, type, category, keywords
            FROM capabilities
            WHERE name LIKE '%environment_discovery%'
            AND type = 'tool'
        """)

        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Azure environment discovery script not found in capabilities.db"

        name, path, cap_type, category, keywords = result
        assert "environment_discovery" in name
        assert "claude/tools/azure_operations/environment_discovery.ps1" in path
        assert cap_type == "tool"
        assert category == "azure_operations"
        assert "azure" in keywords.lower()
        assert "powershell" in keywords.lower() or "script" in keywords.lower()

    def test_azure_operations_category_exists(self, capabilities_db_path):
        """Test that azure_operations category exists and has multiple capabilities."""
        conn = sqlite3.connect(capabilities_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM capabilities
            WHERE category = 'azure_operations'
        """)

        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 2, f"Expected at least 2 azure_operations capabilities, found {count}"

    def test_protocol_file_exists(self):
        """Test that azure_environment_discovery.md protocol file exists."""
        protocol_path = MAIA_ROOT / "claude/context/protocols/azure_environment_discovery.md"
        assert protocol_path.exists(), f"Protocol file not found at {protocol_path}"

    def test_discovery_script_exists(self):
        """Test that environment_discovery.ps1 script file exists."""
        script_path = MAIA_ROOT / "claude/tools/azure_operations/environment_discovery.ps1"
        assert script_path.exists(), f"Discovery script not found at {script_path}"

    def test_protocol_content_structure(self):
        """Test that protocol file has required sections."""
        protocol_path = MAIA_ROOT / "claude/context/protocols/azure_environment_discovery.md"

        with open(protocol_path, 'r') as f:
            content = f.read()

        required_sections = [
            "# Azure Environment Discovery Protocol",
            "## Quick Reference Commands",
            "## Environment Inventory",
            "## Discovery Workflow",
            "## Multi-Tenant Safety Protocol",
            "## Sandbox Access",
        ]

        for section in required_sections:
            assert section in content, f"Missing required section: {section}"

    def test_discovery_script_has_powershell_header(self):
        """Test that discovery script has proper PowerShell structure."""
        script_path = MAIA_ROOT / "claude/tools/azure_operations/environment_discovery.ps1"

        with open(script_path, 'r') as f:
            content = f.read()

        assert "#Requires -Modules" in content, "Missing PowerShell module requirements"
        assert ".SYNOPSIS" in content, "Missing PowerShell help synopsis"
        assert "param(" in content, "Missing PowerShell parameters"
