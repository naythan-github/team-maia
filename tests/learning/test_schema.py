"""
Tests for Database Schema Module

Sprint: PAI v2
Stub tests for pre-existing tool.
"""

import pytest
import sqlite3
from pathlib import Path


class TestSchemaImports:
    """Verify module can be imported and exports exist."""

    def test_module_imports(self):
        """Module can be imported without error."""
        from claude.tools.learning import schema
        assert schema is not None

    def test_init_memory_db_exists(self):
        """init_memory_db function exists."""
        from claude.tools.learning.schema import init_memory_db
        assert callable(init_memory_db)

    def test_init_learning_db_exists(self):
        """init_learning_db function exists."""
        from claude.tools.learning.schema import init_learning_db
        assert callable(init_learning_db)

    def test_init_prompts_db_exists(self):
        """init_prompts_db function exists."""
        from claude.tools.learning.schema import init_prompts_db
        assert callable(init_prompts_db)

    def test_schema_constants_exist(self):
        """Schema constants are defined."""
        from claude.tools.learning.schema import MEMORY_SCHEMA, LEARNING_SCHEMA, PROMPTS_SCHEMA
        assert MEMORY_SCHEMA is not None
        assert LEARNING_SCHEMA is not None
        assert PROMPTS_SCHEMA is not None

    def test_all_exports(self):
        """__all__ exports correct items."""
        from claude.tools.learning.schema import __all__
        assert 'init_memory_db' in __all__
        assert 'init_learning_db' in __all__
        assert 'MEMORY_SCHEMA' in __all__


class TestSchemaInitialization:
    """Test database initialization."""

    def test_memory_db_creates_tables(self, tmp_path):
        """init_memory_db creates expected tables."""
        from claude.tools.learning.schema import init_memory_db

        db_path = tmp_path / "memory.db"
        conn = init_memory_db(db_path)

        # Verify sessions table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_learning_db_creates_tables(self, tmp_path):
        """init_learning_db creates expected tables."""
        from claude.tools.learning.schema import init_learning_db

        db_path = tmp_path / "learning.db"
        conn = init_learning_db(db_path)

        # Verify patterns table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='patterns'"
        )
        assert cursor.fetchone() is not None
        conn.close()
