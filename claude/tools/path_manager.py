#!/usr/bin/env python3
"""
Centralized Path Management for Maia System
Handles all file system paths with proper fallbacks and directory creation
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import logging
from claude.tools.core.path_manager import get_maia_root

logger = logging.getLogger(__name__)


class MaiaPathManager:
    """
    Centralized path management following macOS standards
    """

    def __init__(self):
        """Initialize path manager with proper macOS structure"""
        self._base_paths = self._determine_base_paths()
        self._ensure_directories_exist()

    def _determine_base_paths(self) -> Dict[str, Path]:
        """Determine base paths following macOS conventions"""
        home = Path.home()

        # Primary paths following macOS Application Support pattern
        app_support = home / "Library" / "Application Support" / "Maia"
        git_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))

        # Backup location in iCloud (if available)
        icloud_path = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "maia-backups"

        # Fallback if iCloud is not available
        fallback_backup = home / ".maia-backups"
        backup_path = icloud_path if icloud_path.parent.exists() else fallback_backup

        return {
            'app_support': app_support,
            'git_root': git_root,
            'backup': backup_path,
            'code': git_root / "claude" / "tools",
            'context': git_root / "claude" / "context",
            'config_templates': git_root / "claude" / "context" / "templates",
            'schemas': git_root / "claude" / "tools" / "core" / "schemas",

            # Application Support subdirectories
            'config': app_support / "config",
            'databases': app_support / "databases",
            'logs': app_support / "logs",
            'cache': app_support / "cache",
            'temp': app_support / "temp",

            # Backup subdirectories
            'db_backups': backup_path / "databases",
            'config_backups': backup_path / "config",
            'recovery_scripts': backup_path / "recovery"
        }

    def _ensure_directories_exist(self):
        """Create all required directories"""
        for name, path in self._base_paths.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {name} -> {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {name} at {path}: {e}")
                # For critical directories, this should fail fast
                if name in ['app_support', 'config', 'databases', 'logs']:
                    raise RuntimeError(f"Cannot create critical directory {name}: {e}")

    def get_path(self, path_name: str) -> Path:
        """Get a path by name with validation"""
        if path_name not in self._base_paths:
            raise ValueError(f"Unknown path name: {path_name}. Available: {list(self._base_paths.keys())}")

        path = self._base_paths[path_name]

        # Ensure parent directory exists for files
        if not path.exists() and '.' in path.name:
            path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def get_database_path(self, db_name: str) -> Path:
        """Get database file path"""
        return self.get_path('databases') / f"{db_name}.db"

    def get_config_path(self, config_name: str) -> Path:
        """Get configuration file path"""
        return self.get_path('config') / f"{config_name}.json"

    def get_log_path(self, log_name: str) -> Path:
        """Get log file path"""
        return self.get_path('logs') / f"{log_name}.log"

    def get_backup_path(self, backup_type: str, filename: str) -> Path:
        """Get backup file path"""
        backup_dir = self.get_path(f"{backup_type}_backups")
        return backup_dir / filename

    def get_all_paths(self) -> Dict[str, str]:
        """Get all paths as strings for logging/debugging"""
        return {name: str(path) for name, path in self._base_paths.items()}

    def validate_system_paths(self) -> Dict[str, bool]:
        """Validate that all critical paths are accessible"""
        validation_results = {}
        critical_paths = ['app_support', 'databases', 'logs', 'config', 'backup']

        for path_name in critical_paths:
            try:
                path = self.get_path(path_name)
                # Test write access
                test_file = path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                validation_results[path_name] = True
                logger.debug(f"Path validation passed: {path_name}")
            except Exception as e:
                validation_results[path_name] = False
                logger.error(f"Path validation failed: {path_name} - {e}")

        return validation_results

    def get_migration_plan(self) -> Dict:
        """Generate migration plan from current file locations"""
        current_locations = {
            'jobs_db': Path("get_path_manager().get_path('git_root') / 'claude' / 'data' / 'jobs.db'"),
            'job_monitor_config': Path("${MAIA_ROOT}/claude/context/tools/config/job_monitor_config.json"),
            'gmail_credentials': Path("get_path_manager().get_path('git_root') / 'claude' / 'data' / 'google_credentials'"),
            'logs_dir': Path("${MAIA_ROOT}/claude/data"),
        }

        migration_plan = {
            'moves': [],
            'creates': [],
            'backups': []
        }

        for name, current_path in current_locations.items():
            if current_path.exists():
                if name == 'jobs_db':
                    new_path = self.get_database_path('jobs')
                    backup_path = self.get_backup_path('db', f'jobs_pre_migration_{datetime.now().strftime("%Y%m%d_%H%M")}.db')

                    migration_plan['backups'].append({
                        'source': current_path,
                        'backup': backup_path,
                        'description': 'Backup existing jobs database'
                    })

                    migration_plan['moves'].append({
                        'source': current_path,
                        'destination': new_path,
                        'description': 'Move jobs database to Application Support'
                    })

        return migration_plan


# Global instance
_path_manager = None

def get_path_manager() -> MaiaPathManager:
    """Get global path manager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = MaiaPathManager()
    return _path_manager


if __name__ == "__main__":
    # Test path manager
    logging.basicConfig(level=logging.DEBUG)

    pm = MaiaPathManager()

    print("🗂️  Maia Path Manager Test")
    print("=" * 40)

    # Display all paths
    for name, path in pm.get_all_paths().items():
        print(f"{name:20}: {path}")

    print("\n🔍 Path Validation")
    print("=" * 40)

    validation = pm.validate_system_paths()
    for path_name, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"{status} {path_name}")

    # Test specific path access
    print(f"\n📊 Database path: {pm.get_database_path('jobs')}")
    print(f"⚙️  Config path: {pm.get_config_path('job_monitor')}")
    print(f"📝 Log path: {pm.get_log_path('job_monitor')}")
    print(f"💾 Backup path: {pm.get_backup_path('db', 'jobs_backup.db')}")
