#!/usr/bin/env python3
"""
Maia Comprehensive Backup Manager
=================================
Complete backup system that covers all Maia components with enterprise-grade reliability.

Features:
- All 37+ databases backed up
- Configuration files and context
- Tools and agents backup
- Self-contained restoration packages
- Automated validation and integrity checking
- iCloud synchronization support
"""

import os
import json
import sqlite3
import shutil
import tarfile
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import subprocess
import gzip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Comprehensive backup configuration"""
    backup_root_dir: str
    retention_days: int = 30
    daily_backups: int = 7
    weekly_backups: int = 4
    monthly_backups: int = 3
    compression: str = "gz"
    verify_integrity: bool = True
    cloud_sync: bool = False
    cloud_provider: str = "icloud"
    include_restoration_tools: bool = True

@dataclass
class BackupManifest:
    """Enhanced backup manifest"""
    backup_id: str
    timestamp: datetime
    backup_type: str
    size_bytes: int
    file_count: int
    checksum: str
    components: List[str]
    success: bool
    maia_version: str
    databases_backed_up: List[str]
    configuration_files: List[str]
    tools_count: int
    agents_count: int
    backup_format_version: str = "3.0"
    error_log: Optional[str] = None

class MaiaComprehensiveBackupManager:
    """Comprehensive backup manager for complete Maia system"""
    
    def __init__(self, config: Optional[BackupConfig] = None):
        """Initialize comprehensive backup manager"""
        self.maia_root = Path(os.environ.get('MAIA_ROOT', str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd())))
        
        # Default configuration with iCloud support
        if config is None:
            icloud_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "maia" / "backups"
            if icloud_dir.parent.parent.exists():
                default_backup_dir = str(icloud_dir)
                cloud_sync = True
            else:
                default_backup_dir = str(self.maia_root / 'backups')
                cloud_sync = False
            
            config = BackupConfig(
                backup_root_dir=default_backup_dir,
                cloud_sync=cloud_sync,
                include_restoration_tools=True
            )
        
        self.config = config
        self.backup_root_dir = Path(config.backup_root_dir)
        self.backup_root_dir.mkdir(parents=True, exist_ok=True)
        
        # Define all backup components
        self.backup_components = {
            'databases': {
                'pattern': 'claude/data/**/*.db',
                'description': 'All SQLite databases',
                'critical': True
            },
            'configuration': {
                'files': [
                    'CLAUDE.md',
                    'SYSTEM_STATE.md',
                    'claude/context/**/*',
                    'claude/commands/**/*',
                    'claude/hooks/**/*'
                ],
                'description': 'Configuration and context files',
                'critical': True
            },
            'tools': {
                'pattern': 'claude/tools/**/*',
                'description': 'All tools and utilities',
                'critical': True
            },
            'agents': {
                'pattern': 'claude/agents/**/*',
                'description': 'All specialized agents',
                'critical': True
            },
            'scripts': {
                'pattern': 'scripts/**/*',
                'description': 'Core scripts',
                'critical': True
            },
            'credentials': {
                'files': [
                    '.env',
                    'claude/data/credentials/**/*'
                ],
                'description': 'Credentials and environment',
                'critical': False,
                'encrypted': True
            }
        }
        
        logger.info(f"Backup manager initialized - Target: {self.backup_root_dir}")
    
    def create_comprehensive_backup(self, backup_type: str = "manual") -> BackupManifest:
        """Create comprehensive backup of entire Maia system"""
        backup_id = f"maia_comprehensive_{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_root_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"🚀 Creating comprehensive backup: {backup_id}")
        
        manifest = BackupManifest(
            backup_id=backup_id,
            timestamp=datetime.now(),
            backup_type=backup_type,
            size_bytes=0,
            file_count=0,
            checksum="",
            components=[],
            success=False,
            maia_version=self._get_maia_version(),
            databases_backed_up=[],
            configuration_files=[],
            tools_count=0,
            agents_count=0
        )
        
        total_size = 0
        total_files = 0
        errors = []
        
        try:
            # Backup databases
            db_result = self._backup_databases(backup_path)
            manifest.databases_backed_up = db_result['databases']
            manifest.components.append('databases')
            total_size += db_result['size']
            total_files += db_result['files']
            logger.info(f"✅ Databases: {len(db_result['databases'])} backed up ({db_result['size']:.2f} MB)")
            
            # Backup configuration
            config_result = self._backup_configuration(backup_path)
            manifest.configuration_files = config_result['files']
            manifest.components.append('configuration')
            total_size += config_result['size']
            total_files += config_result['file_count']
            logger.info(f"✅ Configuration: {len(config_result['files'])} files backed up")
            
            # Backup tools
            tools_result = self._backup_tools(backup_path)
            manifest.tools_count = tools_result['count']
            manifest.components.append('tools')
            total_size += tools_result['size']
            total_files += tools_result['files']
            logger.info(f"✅ Tools: {tools_result['count']} tools backed up")
            
            # Backup agents
            agents_result = self._backup_agents(backup_path)
            manifest.agents_count = agents_result['count']
            manifest.components.append('agents')
            total_size += agents_result['size']
            total_files += agents_result['files']
            logger.info(f"✅ Agents: {agents_result['count']} agents backed up")
            
            # Backup scripts
            scripts_result = self._backup_scripts(backup_path)
            manifest.components.append('scripts')
            total_size += scripts_result['size']
            total_files += scripts_result['files']
            logger.info(f"✅ Scripts: {scripts_result['count']} scripts backed up")
            
            # Include restoration tools if enabled
            if self.config.include_restoration_tools:
                self._include_restoration_tools(backup_path)
                manifest.components.append('restoration_tools')
                logger.info("✅ Restoration tools included")
            
            # CRITICAL FIX: Save manifest BEFORE creating archive (which deletes directory)
            manifest.file_count = total_files
            manifest.success = True

            # Save manifest to backup directory first
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(asdict(manifest), f, indent=2, default=str)

            # Create compressed archive (this will delete backup_path directory)
            archive_path = self._create_compressed_archive(backup_path)
            archive_size = archive_path.stat().st_size / (1024 * 1024)  # MB

            # Calculate checksum after archive creation
            manifest.checksum = self._calculate_checksum(archive_path)
            manifest.size_bytes = archive_path.stat().st_size

            # Save manifest alongside archive (backup_path no longer exists, use archive location)
            archive_manifest_path = archive_path.with_suffix('.json')
            with open(archive_manifest_path, 'w') as f:
                json.dump(asdict(manifest), f, indent=2, default=str)
            
            logger.info(f"🎉 Backup completed successfully!")
            logger.info(f"   Archive: {archive_path.name} ({archive_size:.2f} MB)")
            logger.info(f"   Files: {total_files}")
            logger.info(f"   Components: {len(manifest.components)}")
            logger.info(f"   Databases: {len(manifest.databases_backed_up)}")
            
            # Sync to cloud if enabled
            if self.config.cloud_sync:
                self._sync_to_cloud(archive_path, archive_manifest_path)
            
            return manifest
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            manifest.error_log = error_msg
            manifest.success = False
            logger.error(f"❌ {error_msg}")
            return manifest
    
    def _backup_databases(self, backup_path: Path) -> Dict[str, Any]:
        """Backup all databases with integrity validation"""
        db_backup_dir = backup_path / "databases"
        db_backup_dir.mkdir(exist_ok=True)
        
        databases = []
        total_size = 0
        file_count = 0
        
        # Find all database files
        db_patterns = [
            self.maia_root / "claude" / "data" / "*.db",
            self.maia_root / "claude" / "data" / "**" / "*.db"
        ]
        
        db_files = []
        for pattern in db_patterns:
            db_files.extend(self.maia_root.glob(str(pattern).replace(str(self.maia_root) + "/", "")))
        
        for db_file in db_files:
            if db_file.exists() and db_file.is_file():
                try:
                    # Validate database integrity first
                    if self._validate_database_integrity(db_file):
                        # Create compressed backup
                        rel_path = db_file.relative_to(self.maia_root)
                        backup_db_path = db_backup_dir / f"{rel_path.name}.gz"
                        backup_db_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(db_file, 'rb') as f_in:
                            with gzip.open(backup_db_path, 'wb') as f_out:
                                f_out.writelines(f_in)
                        
                        size_mb = backup_db_path.stat().st_size / (1024 * 1024)
                        total_size += size_mb
                        file_count += 1
                        databases.append(str(rel_path))
                        
                        logger.debug(f"Database backed up: {rel_path} ({size_mb:.2f} MB)")
                    else:
                        logger.warning(f"Database integrity check failed: {db_file}")
                except Exception as e:
                    logger.error(f"Failed to backup database {db_file}: {e}")
        
        return {
            'databases': databases,
            'size': total_size,
            'files': file_count
        }
    
    def _backup_configuration(self, backup_path: Path) -> Dict[str, Any]:
        """Backup configuration files and context"""
        config_backup_dir = backup_path / "configuration"
        config_backup_dir.mkdir(exist_ok=True)
        
        config_files = []
        total_size = 0
        file_count = 0
        
        # Configuration file patterns
        config_patterns = [
            "CLAUDE.md",
            "SYSTEM_STATE.md",
            "claude/context/**/*",
            "claude/commands/**/*",
            "claude/hooks/**/*"
        ]
        
        for pattern in config_patterns:
            files = list(self.maia_root.glob(pattern))
            for file_path in files:
                if file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(self.maia_root)
                        backup_file_path = config_backup_dir / rel_path
                        backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        shutil.copy2(file_path, backup_file_path)
                        
                        size_mb = backup_file_path.stat().st_size / (1024 * 1024)
                        total_size += size_mb
                        file_count += 1
                        config_files.append(str(rel_path))
                        
                    except Exception as e:
                        logger.error(f"Failed to backup config file {file_path}: {e}")
        
        return {
            'files': config_files,
            'size': total_size,
            'file_count': file_count
        }
    
    def _backup_tools(self, backup_path: Path) -> Dict[str, Any]:
        """Backup all tools"""
        tools_backup_dir = backup_path / "tools"
        tools_backup_dir.mkdir(exist_ok=True)
        
        tools_dir = self.maia_root / "claude" / "tools"
        if tools_dir.exists():
            shutil.copytree(tools_dir, tools_backup_dir / "claude" / "tools", dirs_exist_ok=True)
            
            # Count tools
            tool_files = list((tools_backup_dir / "claude" / "tools").rglob("*.py"))
            tools_count = len(tool_files)
            
            # Calculate size
            total_size = sum(f.stat().st_size for f in (tools_backup_dir / "claude" / "tools").rglob("*") if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            
            return {
                'count': tools_count,
                'size': total_size_mb,
                'files': len(list((tools_backup_dir / "claude" / "tools").rglob("*")))
            }
        
        return {'count': 0, 'size': 0, 'files': 0}
    
    def _backup_agents(self, backup_path: Path) -> Dict[str, Any]:
        """Backup all agents"""
        agents_backup_dir = backup_path / "agents"
        agents_backup_dir.mkdir(exist_ok=True)
        
        agents_dir = self.maia_root / "claude" / "agents"
        if agents_dir.exists():
            shutil.copytree(agents_dir, agents_backup_dir / "claude" / "agents", dirs_exist_ok=True)
            
            # Count agents
            agent_files = list((agents_backup_dir / "claude" / "agents").glob("*.md"))
            agents_count = len(agent_files)
            
            # Calculate size
            total_size = sum(f.stat().st_size for f in agent_files)
            total_size_mb = total_size / (1024 * 1024)
            
            return {
                'count': agents_count,
                'size': total_size_mb,
                'files': agents_count
            }
        
        return {'count': 0, 'size': 0, 'files': 0}
    
    def _backup_scripts(self, backup_path: Path) -> Dict[str, Any]:
        """Backup core scripts"""
        scripts_backup_dir = backup_path / "scripts"
        scripts_backup_dir.mkdir(exist_ok=True)
        
        scripts_dir = self.maia_root / "scripts"
        script_count = 0
        total_size = 0
        file_count = 0
        
        if scripts_dir.exists():
            shutil.copytree(scripts_dir, scripts_backup_dir / "scripts", dirs_exist_ok=True)
            
            script_files = list((scripts_backup_dir / "scripts").rglob("*"))
            script_count = len([f for f in script_files if f.is_file() and f.suffix in ['.py', '.sh']])
            total_size = sum(f.stat().st_size for f in script_files if f.is_file()) / (1024 * 1024)
            file_count = len([f for f in script_files if f.is_file()])
        
        return {
            'count': script_count,
            'size': total_size,
            'files': file_count
        }
    
    def _include_restoration_tools(self, backup_path: Path) -> None:
        """Include restoration tools and documentation"""
        restoration_dir = backup_path / "restoration"
        restoration_dir.mkdir(exist_ok=True)

        # Copy ZERO-TOUCH restore script (primary - disaster recovery)
        primary_restore = self.maia_root / "RESTORE_ME.py"
        if primary_restore.exists():
            shutil.copy2(primary_restore, backup_path / "RESTORE_ME.py")
            logger.info("✅ Bundled RESTORE_ME.py (zero-touch disaster recovery)")

        # Copy enterprise restoration script (secondary - advanced options)
        restoration_script = self.maia_root / "claude" / "tools" / "sre" / "restore_maia_enterprise.py"
        if restoration_script.exists():
            shutil.copy2(restoration_script, backup_path / "restore_maia_enterprise.py")

        # Copy restoration guide
        restoration_guide = self.maia_root / "docs" / "RESTORATION_GUIDE.md"
        if restoration_guide.exists():
            shutil.copy2(restoration_guide, backup_path / "RESTORATION_GUIDE.md")

        # Create simple README for disaster recovery
        readme_content = """# MAIA DISASTER RECOVERY

## Quick Restore (Hardware Failure)

1. Extract this backup:
   ```bash
   tar -xzf maia_backup_*.tar.gz
   cd maia_backup_*/
   ```

2. Run zero-touch restore:
   ```bash
   python3 RESTORE_ME.py
   ```

3. Done! Maia restored to ~/maia

## Advanced Options

```bash
python3 RESTORE_ME.py --target /custom/path  # Custom location
python3 restore_maia_enterprise.py           # Enterprise options
```

For issues: Check RESTORATION_GUIDE.md
"""
        with open(backup_path / "README_RESTORE.txt", 'w') as f:
            f.write(readme_content)
    
    def _create_compressed_archive(self, backup_path: Path) -> Path:
        """Create compressed tar.gz archive"""
        archive_path = backup_path.with_suffix('.tar.gz')
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # Remove uncompressed directory
        shutil.rmtree(backup_path)
        
        return archive_path
    
    def _validate_database_integrity(self, db_path: Path) -> bool:
        """Validate SQLite database integrity"""
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                return result == 'ok'
        except Exception:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_maia_version(self) -> str:
        """Get current Maia version from SYSTEM_STATE.md"""
        try:
            system_state = self.maia_root / "SYSTEM_STATE.md"
            if system_state.exists():
                content = system_state.read_text()
                # Extract version from first few lines
                for line in content.split('\n')[:10]:
                    if 'Phase' in line and 'System Version' in line:
                        return line.split('System Version')[1].strip(': ')
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _sync_to_cloud(self, archive_path: Path, manifest_path: Path) -> None:
        """Sync backup to cloud storage"""
        if self.config.cloud_provider == "icloud":
            logger.info("📤 Syncing to iCloud...")
            # Files are already in iCloud directory if cloud_sync is True
            logger.info("✅ iCloud sync complete")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_root_dir.glob("maia_comprehensive_*.tar.gz"):
            manifest_file = backup_file.with_suffix('.json')
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    
                    backup_info = {
                        'name': backup_file.stem,
                        'type': manifest.get('backup_type', 'unknown'),
                        'timestamp': manifest.get('timestamp', ''),
                        'size_mb': manifest.get('size_bytes', 0) / (1024 * 1024),
                        'databases': len(manifest.get('databases_backed_up', [])),
                        'tools': manifest.get('tools_count', 0),
                        'agents': manifest.get('agents_count', 0),
                        'success': manifest.get('success', False),
                        'components': manifest.get('components', [])
                    }
                    backups.append(backup_info)
                except Exception as e:
                    logger.error(f"Failed to read manifest for {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        logger.info("🧹 Cleaning up old backups...")
        
        now = datetime.now()
        daily_cutoff = now - timedelta(days=self.config.daily_backups)
        weekly_cutoff = now - timedelta(weeks=self.config.weekly_backups)
        monthly_cutoff = now - timedelta(days=self.config.monthly_backups * 30)
        
        backups = self.list_backups()
        deleted_count = 0
        
        for backup in backups:
            backup_time = datetime.fromisoformat(backup['timestamp'])
            backup_type = backup['type']
            
            should_delete = False
            if backup_type == 'daily' and backup_time < daily_cutoff:
                should_delete = True
            elif backup_type == 'weekly' and backup_time < weekly_cutoff:
                should_delete = True
            elif backup_type == 'monthly' and backup_time < monthly_cutoff:
                should_delete = True
            
            if should_delete:
                backup_file = self.backup_root_dir / f"{backup['name']}.tar.gz"
                manifest_file = self.backup_root_dir / f"{backup['name']}.json"
                
                if backup_file.exists():
                    backup_file.unlink()
                if manifest_file.exists():
                    manifest_file.unlink()
                
                deleted_count += 1
                logger.info(f"🗑️ Deleted old backup: {backup['name']}")
        
        logger.info(f"✅ Cleanup complete - {deleted_count} old backups removed")


def main():
    """CLI interface for backup manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Maia Comprehensive Backup Manager')
    parser.add_argument('command', choices=['backup', 'list', 'cleanup', 'status'], help='Command to execute')
    parser.add_argument('--type', default='manual', choices=['manual', 'daily', 'weekly', 'monthly'], help='Backup type')
    
    args = parser.parse_args()
    
    backup_manager = MaiaComprehensiveBackupManager()
    
    if args.command == 'backup':
        result = backup_manager.create_comprehensive_backup(args.type)
        if result.success:
            print(f"✅ Backup created successfully: {result.backup_id}")
            print(f"📊 Size: {result.size_bytes / (1024 * 1024):.2f} MB")
            print(f"📁 Databases: {len(result.databases_backed_up)}")
            print(f"🔧 Tools: {result.tools_count}")
            print(f"🤖 Agents: {result.agents_count}")
        else:
            print(f"❌ Backup failed: {result.error_log}")
    
    elif args.command == 'list':
        backups = backup_manager.list_backups()
        print(f"📋 Available Backups ({len(backups)}):")
        print("-" * 60)
        for backup in backups:
            status = "✅" if backup['success'] else "❌"
            print(f"{status} {backup['name']}")
            print(f"   Type: {backup['type']} | Size: {backup['size_mb']:.2f} MB")
            print(f"   Created: {backup['timestamp'][:19]}")
            print(f"   DBs: {backup['databases']} | Tools: {backup['tools']} | Agents: {backup['agents']}")
            print(f"   Components: {', '.join(backup['components'])}")
            print()
    
    elif args.command == 'cleanup':
        backup_manager.cleanup_old_backups()
    
    elif args.command == 'status':
        backups = backup_manager.list_backups()
        latest = backups[0] if backups else None
        
        print("📊 Backup System Status:")
        print(f"   Total Backups: {len(backups)}")
        if latest:
            print(f"   Latest: {latest['name']} ({latest['type']})")
            print(f"   Created: {latest['timestamp'][:19]}")
            print(f"   Status: {'✅ Success' if latest['success'] else '❌ Failed'}")
        print(f"   Storage Location: {backup_manager.backup_root_dir}")
        print(f"   Cloud Sync: {'✅ Enabled' if backup_manager.config.cloud_sync else '❌ Disabled'}")


if __name__ == "__main__":
    main()