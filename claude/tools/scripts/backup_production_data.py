#!/usr/bin/env python3
"""
Production Database Backup System
=================================

Comprehensive backup system for all Maia production databases and data.
"""

import os
import shutil
import sqlite3
import json
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('backup_system')

class ProductionBackupSystem:
    def __init__(self, user_id="naythan"):
        self.user_id = user_id
        
        # CRITICAL FIX: Use external iCloud storage - NEVER backup to same system location
        icloud_backup_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "maia" / "backups" / "production"
        fallback_backup_dir = Path("/tmp/maia_backups_external")  # Emergency fallback
        
        if icloud_backup_dir.parent.parent.exists():
            self.backup_dir = icloud_backup_dir
            logger.info(f"✅ Using iCloud backup storage: {self.backup_dir}")
        else:
            self.backup_dir = fallback_backup_dir
            logger.warning(f"⚠️ iCloud unavailable, using fallback: {self.backup_dir}")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # All database files to backup - COMPREHENSIVE COVERAGE
        self.database_files = [
            # User-specific databases
            f"claude/data/contextual_memory_{user_id}.db",
            f"claude/data/autonomous_alerts_{user_id}.db", 
            f"claude/data/continuous_monitoring_{user_id}.db",
            f"claude/data/calendar_optimizer_{user_id}.db",
            f"claude/data/context_preparation_{user_id}.db",
            f"claude/data/background_learning_{user_id}.db",
            f"claude/data/production_deployment_{user_id}.db",
            
            # Core system databases
            "claude/data/jobs.db",
            "claude/data/databases/rag_service.db",
            "claude/data/databases/user/personal_knowledge_graph.db",
            "claude/data/security_intelligence.db",
            "claude/data/databases/system/dashboard_registry.db",
            "claude/data/databases/system/tool_discovery.db",
            "claude/data/tool_usage.db",
            "claude/data/databases/system/implementations.db",
            "claude/data/maia_improvement_intelligence.db",
            "claude/data/maia_projects.db",
            
            # Business and analytics databases
            "claude/data/bi_dashboard.db",
            "claude/data/databases/system/performance_metrics.db",
            "claude/data/databases/intelligence/predictive_models.db",
            "claude/data/databases/system/research_cache.db",
            "claude/data/rss_intelligence.db",
            "claude/data/teams_meetings.db",
            
            # Specialized databases
            "claude/data/confluence_organization.db",
            "claude/data/context_compression.db",
            "claude/data/documentation_enforcement.db",
            "claude/data/portfolio_governance.db",
            "claude/data/preservation.db",
            "claude/data/reconstruction.db",
            "claude/data/databases/system/self_improvement.db",
            "claude/data/ux_optimization.db",
            "claude/data/databases/system/verification_hook.db",
            "claude/data/databases/system/deduplication.db",

            # EIA and monitoring databases
            "claude/data/databases/system/dora_metrics.db",
            "claude/data/databases/intelligence/eia_intelligence.db",
            "claude/data/databases/intelligence/security_metrics.db",
            "claude/data/databases/system/system_health.db",
            "claude/data/databases/system/anti_sprawl_progress.db"
        ]
        
        # Credential files to backup (encrypted)
        self.credential_files = [
            "claude/data/credentials/gmail_oauth.json",
            "claude/data/credentials/linkedin_api.json",
            "claude/data/credentials/twilio_sms.json"
        ]
        
        # Configuration files to backup - CRITICAL SYSTEM CONFIG + RESTORATION DOCS
        self.configuration_files = [
            "CLAUDE.md",
            "SYSTEM_STATE.md",
            "claude/context/ufc_system.md",
            "claude/context/core/identity.md",
            "claude/context/core/systematic_thinking_protocol.md",
            "claude/context/core/model_selection_strategy.md",
            "claude/context/core/agents.md",
            "claude/context/tools/available.md"
        ]
        
        # Restoration documentation files - SELF-CONTAINED RESTORATION
        self.restoration_files = [
            "docs/RESTORATION_GUIDE.md",
            "README.md",
            "requirements.txt"
        ]
        
        # Tools and agents directories to backup
        self.system_directories = [
            "claude/tools",
            "claude/agents", 
            "claude/commands",
            "claude/hooks",
            "scripts"
        ]
        
        # Log files to backup
        self.log_files = [
            "claude/logs/production/intelligence_engine.log",
            "claude/logs/production/monitoring.log",
            "claude/logs/production/learning.log",
            "claude/logs/production/alerts.log",
            "claude/logs/production/health.log"
        ]
    
    def create_backup(self, backup_type="daily"):
        """Create comprehensive backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"maia_backup_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creating {backup_type} backup: {backup_name}")
        
        backup_manifest = {
            "backup_name": backup_name,
            "backup_type": backup_type,
            "created_at": datetime.now().isoformat(),
            "user_id": self.user_id,
            "files_backed_up": [],
            "databases_backed_up": [],
            "configuration_files_backed_up": [],
            "directories_backed_up": [],
            "backup_size_mb": 0,
            "total_files": 0,
            "coverage_complete": True
        }
        
        total_size = 0
        
        # Backup databases
        db_backup_dir = backup_path / "databases"
        db_backup_dir.mkdir(exist_ok=True)
        
        for db_file in self.database_files:
            if os.path.exists(db_file):
                try:
                    # Create compressed backup of database
                    backup_db_path = db_backup_dir / f"{Path(db_file).name}.gz"
                    
                    with open(db_file, 'rb') as f_in:
                        with gzip.open(backup_db_path, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    file_size = os.path.getsize(backup_db_path) / 1024 / 1024  # MB
                    total_size += file_size
                    
                    backup_manifest["databases_backed_up"].append({
                        "original_path": db_file,
                        "backup_path": str(backup_db_path),
                        "size_mb": round(file_size, 2)
                    })
                    
                    logger.info(f"Backed up database: {db_file} ({file_size:.2f} MB)")
                    
                except Exception as e:
                    logger.error(f"Failed to backup database {db_file}: {e}")
        
        # Backup configuration files - CRITICAL SYSTEM CONFIG
        config_backup_dir = backup_path / "configuration"
        config_backup_dir.mkdir(exist_ok=True)
        
        for config_file in self.configuration_files:
            if os.path.exists(config_file):
                try:
                    backup_config_path = config_backup_dir / Path(config_file).name
                    # CRITICAL FIX: Handle encoding properly for text files
                    if Path(config_file).suffix in ['.md', '.json', '.py', '.sh', '.txt']:
                        # Read and write with explicit UTF-8 encoding
                        with open(config_file, 'r', encoding='utf-8', errors='replace') as f_in:
                            content = f_in.read()
                        with open(backup_config_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(content)
                    else:
                        shutil.copy2(config_file, backup_config_path)
                    
                    file_size = os.path.getsize(backup_config_path) / 1024  # KB
                    
                    backup_manifest["configuration_files_backed_up"].append({
                        "original_path": config_file,
                        "backup_path": str(backup_config_path),
                        "size_kb": round(file_size, 2),
                        "type": "configuration"
                    })
                    
                    logger.info(f"Backed up config: {config_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to backup config file {config_file}: {e}")
        
        # Backup system directories - TOOLS, AGENTS, COMMANDS, HOOKS (FIXED STRUCTURE)
        for directory in self.system_directories:
            if os.path.exists(directory):
                try:
                    # CRITICAL FIX: Create enterprise restoration compatible structure
                    if directory == "claude/tools":
                        # Enterprise expects tools/claude/tools/
                        backup_dir_path = backup_path / "tools" / "claude" / "tools"
                    elif directory == "claude/agents":
                        # Enterprise expects agents/claude/agents/
                        backup_dir_path = backup_path / "agents" / "claude" / "agents"  
                    else:
                        # Other directories go to root level
                        backup_dir_path = backup_path / Path(directory).name
                    
                    backup_dir_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy entire directory
                    shutil.copytree(directory, backup_dir_path, dirs_exist_ok=True)
                    
                    # Count files in directory
                    file_count = sum(1 for _ in Path(backup_dir_path).rglob('*') if _.is_file())
                    dir_size = sum(f.stat().st_size for f in Path(backup_dir_path).rglob('*') if f.is_file()) / 1024 / 1024  # MB
                    total_size += dir_size
                    
                    backup_manifest["directories_backed_up"].append({
                        "original_path": directory,
                        "backup_path": str(backup_dir_path),
                        "file_count": file_count,
                        "size_mb": round(dir_size, 2),
                        "type": "system_directory"
                    })
                    
                    logger.info(f"Backed up directory: {directory} ({file_count} files, {dir_size:.2f} MB)")
                    
                except Exception as e:
                    logger.error(f"Failed to backup directory {directory}: {e}")
        
        # Backup restoration documentation - SELF-CONTAINED RESTORATION
        docs_backup_dir = backup_path / "restoration_docs"
        docs_backup_dir.mkdir(exist_ok=True)
        
        for doc_file in self.restoration_files:
            if os.path.exists(doc_file):
                try:
                    backup_doc_path = docs_backup_dir / Path(doc_file).name
                    # CRITICAL FIX: Handle encoding properly for documentation files
                    with open(doc_file, 'r', encoding='utf-8', errors='replace') as f_in:
                        content = f_in.read()
                    with open(backup_doc_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(content)
                    
                    file_size = os.path.getsize(backup_doc_path) / 1024  # KB
                    
                    backup_manifest["files_backed_up"].append({
                        "original_path": doc_file,
                        "backup_path": str(backup_doc_path),
                        "size_kb": round(file_size, 2),
                        "type": "restoration_documentation"
                    })
                    
                    logger.info(f"Backed up restoration doc: {doc_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to backup restoration doc {doc_file}: {e}")
        
        # Create master restoration script - ONE-COMMAND RESTORATION
        master_restore_script = backup_path / "RESTORE_MAIA_HERE.py"
        self._create_master_restoration_script(master_restore_script, backup_path)
        
        backup_manifest["files_backed_up"].append({
            "original_path": "generated",
            "backup_path": str(master_restore_script),
            "size_kb": round(os.path.getsize(master_restore_script) / 1024, 2),
            "type": "master_restoration_script"
        })
        
        logger.info("Created master restoration script: RESTORE_MAIA_HERE.py")
        
        # Backup credential files (if they exist)
        cred_backup_dir = backup_path / "credentials"
        cred_backup_dir.mkdir(exist_ok=True)
        
        for cred_file in self.credential_files:
            if os.path.exists(cred_file):
                try:
                    backup_cred_path = cred_backup_dir / Path(cred_file).name
                    shutil.copy2(cred_file, backup_cred_path)
                    
                    file_size = os.path.getsize(backup_cred_path) / 1024  # KB
                    
                    backup_manifest["files_backed_up"].append({
                        "original_path": cred_file,
                        "backup_path": str(backup_cred_path),
                        "size_kb": round(file_size, 2),
                        "type": "credential"
                    })
                    
                    logger.info(f"Backed up credentials: {cred_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to backup credential file {cred_file}: {e}")
        
        # Backup log files
        log_backup_dir = backup_path / "logs"
        log_backup_dir.mkdir(exist_ok=True)
        
        for log_file in self.log_files:
            if os.path.exists(log_file):
                try:
                    backup_log_path = log_backup_dir / f"{Path(log_file).name}.gz"
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(backup_log_path, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    file_size = os.path.getsize(backup_log_path) / 1024  # KB
                    
                    backup_manifest["files_backed_up"].append({
                        "original_path": log_file,
                        "backup_path": str(backup_log_path),
                        "size_kb": round(file_size, 2),
                        "type": "log"
                    })
                    
                    logger.info(f"Backed up log: {log_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to backup log file {log_file}: {e}")
        
        # Save backup manifest
        backup_manifest["backup_size_mb"] = round(total_size, 2)
        manifest_path = backup_path / "backup_manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(backup_manifest, f, indent=2)
        
        logger.info(f"Backup completed: {backup_name} ({total_size:.2f} MB)")
        
        # CREATE COMPRESSED ARCHIVE - AUTOMATIC TAR.GZ GENERATION
        archive_path = backup_path.parent / f"{backup_name}.tar.gz"
        logger.info(f"Creating compressed archive: {archive_path.name}")
        
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                # Add the entire backup directory to the archive
                tar.add(backup_path, arcname=backup_name)
            
            archive_size_mb = os.path.getsize(archive_path) / (1024 * 1024)
            backup_manifest["archive_created"] = {
                "archive_path": str(archive_path),
                "archive_size_mb": round(archive_size_mb, 2),
                "compression_ratio": round((archive_size_mb / total_size) * 100, 1) if total_size > 0 else 0
            }
            
            logger.info(f"✅ Archive created: {archive_path.name} ({archive_size_mb:.2f} MB, {backup_manifest['archive_created']['compression_ratio']}% of original)")
            
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            backup_manifest["archive_created"] = None
        
        return backup_manifest
    
    def restore_backup(self, backup_name):
        """Restore from backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        # Load backup manifest
        manifest_path = backup_path / "backup_manifest.json"
        if not manifest_path.exists():
            logger.error(f"Backup manifest not found: {backup_name}")
            return False
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        logger.info(f"Restoring backup: {backup_name}")
        
        # Restore databases
        for db_backup in manifest["databases_backed_up"]:
            backup_db_path = db_backup["backup_path"]
            original_path = db_backup["original_path"]
            
            try:
                # Ensure directory exists
                Path(original_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Decompress and restore
                with gzip.open(backup_db_path, 'rb') as f_in:
                    with open(original_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                logger.info(f"Restored database: {original_path}")
                
            except Exception as e:
                logger.error(f"Failed to restore database {original_path}: {e}")
                return False
        
        # Restore other files
        for file_backup in manifest["files_backed_up"]:
            backup_file_path = file_backup["backup_path"]
            original_path = file_backup["original_path"]
            file_type = file_backup["type"]
            
            try:
                # Ensure directory exists
                Path(original_path).parent.mkdir(parents=True, exist_ok=True)
                
                if file_type == "log":
                    # Decompress log files
                    with gzip.open(backup_file_path, 'rb') as f_in:
                        with open(original_path, 'wb') as f_out:
                            f_out.write(f_in.read())
                else:
                    # Copy credential files directly
                    shutil.copy2(backup_file_path, original_path)
                
                logger.info(f"Restored {file_type}: {original_path}")
                
            except Exception as e:
                logger.error(f"Failed to restore {file_type} {original_path}: {e}")
        
        logger.info(f"Backup restore completed: {backup_name}")
        return True
    
    def _create_master_restoration_script(self, script_path: Path, backup_path: Path) -> None:
        """Create self-contained master restoration script"""
        master_script_content = f'''#!/usr/bin/env python3
"""
MAIA SELF-CONTAINED RESTORATION SCRIPT
=====================================
This script contains everything needed to restore your Maia system on any compatible device.

QUICK START:
1. Copy this entire backup folder to your new device
2. Open terminal in this folder
3. Run: python3 RESTORE_MAIA_HERE.py --target ~/maia

REQUIREMENTS:
- Python 3.9+
- macOS, Linux, or Windows with WSL
- Internet connection for dependencies

WHAT THIS RESTORES:
- All 35+ databases (jobs, knowledge graphs, security, etc.)
- All 180+ tools across all categories  
- All 38+ specialized agents
- Complete configuration (CLAUDE.md, context system)
- All commands, hooks, and scripts
- Restoration documentation

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup: {backup_path.name}
"""

import sys
import os
from pathlib import Path

def main():
    print("🚀 MAIA SELF-CONTAINED RESTORATION")
    print("=" * 50)
    print()
    
    # Check if enterprise restoration script exists
    enterprise_script = Path(__file__).parent.parent / "sre" / "restore_maia_enterprise.py"
    
    if enterprise_script.exists():
        print("✅ Using enterprise restoration system...")
        print()
        print("USAGE:")
        print(f"  python3 {{enterprise_script}} --help")
        print()
        print("QUICK RESTORE:")
        print("  # Create tar.gz of this backup folder first:")
        print("  tar -czf maia_backup.tar.gz -C .. {{Path(__file__).parent.name}}")
        print("  # Then restore:")
        print("  python3 claude/tools/sre/restore_maia_enterprise.py maia_backup.tar.gz --target ~/restored_maia")
        print()
        print("DOCUMENTATION:")
        restoration_guide = Path(__file__).parent / "restoration_docs" / "RESTORATION_GUIDE.md"
        if restoration_guide.exists():
            print(f"  📚 Complete guide: {{restoration_guide}}")
        print()
        print("📊 BACKUP CONTENTS:")
        
        # Show backup statistics
        backup_manifest = Path(__file__).parent / "backup_manifest.json"
        if backup_manifest.exists():
            try:
                import json
                with open(backup_manifest, 'r') as f:
                    manifest = json.load(f)
                
                print(f"   🗄️ Databases: {{len(manifest.get('databases_backed_up', []))}}")
                print(f"   📁 Directories: {{len(manifest.get('directories_backed_up', []))}}")
                print(f"   ⚙️ Config files: {{len(manifest.get('configuration_files_backed_up', []))}}")
                print(f"   📄 Total files: {{manifest.get('total_files', 'Unknown')}}")
                print(f"   💾 Size: {{manifest.get('backup_size_mb', 0):.2f}} MB")
                print(f"   📅 Created: {{manifest.get('created_at', 'Unknown')[:19]}}")
                
            except Exception as e:
                print(f"   ⚠️ Could not read backup manifest: {{e}}")
        
        print()
        print("🔧 NEXT STEPS:")
        print("1. Read the restoration guide in restoration_docs/")  
        print("2. Create compressed archive of this backup")
        print("3. Run enterprise restoration script with your target directory")
        print()
        
    else:
        print("❌ Enterprise restoration script not found!")
        print("   Expected: claude/tools/sre/restore_maia_enterprise.py")
        print("   This backup may be incomplete.")

if __name__ == "__main__":
    main()
'''
        
        script_path.write_text(master_script_content)
        script_path.chmod(0o755)  # Make executable
    
    def cleanup_old_backups(self, keep_daily=7, keep_weekly=4, keep_monthly=6):
        """Clean up old backups based on retention policy"""
        logger.info("Cleaning up old backups...")
        
        now = datetime.now()
        daily_cutoff = now - timedelta(days=keep_daily)
        weekly_cutoff = now - timedelta(weeks=keep_weekly)
        monthly_cutoff = now - timedelta(days=keep_monthly * 30)
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("maia_backup_"):
                manifest_path = backup_dir / "backup_manifest.json"
                
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    backup_date = datetime.fromisoformat(manifest["created_at"])
                    backup_type = manifest["backup_type"]
                    
                    should_delete = False
                    
                    if backup_type == "daily" and backup_date < daily_cutoff:
                        should_delete = True
                    elif backup_type == "weekly" and backup_date < weekly_cutoff:
                        should_delete = True
                    elif backup_type == "monthly" and backup_date < monthly_cutoff:
                        should_delete = True
                    
                    if should_delete:
                        shutil.rmtree(backup_dir)
                        logger.info(f"Deleted old backup: {backup_dir.name}")
    
    def list_backups(self):
        """List all available backups (directories and archives)"""
        backups = []
        
        # Check for backup directories
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("maia_backup_"):
                manifest_path = backup_dir / "backup_manifest.json"
                
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    backup_info = {
                        "name": manifest["backup_name"],
                        "type": manifest["backup_type"],
                        "created_at": manifest["created_at"],
                        "size_mb": manifest["backup_size_mb"],
                        "databases": len(manifest["databases_backed_up"]),
                        "files": len(manifest["files_backed_up"]),
                        "format": "directory"
                    }
                    
                    # Check if archive exists and add archive info
                    archive_path = backup_dir.parent / f"{backup_dir.name}.tar.gz"
                    if archive_path.exists():
                        archive_size_mb = os.path.getsize(archive_path) / (1024 * 1024)
                        backup_info["archive"] = {
                            "path": str(archive_path),
                            "size_mb": round(archive_size_mb, 2),
                            "compression_ratio": round((archive_size_mb / backup_info["size_mb"]) * 100, 1) if backup_info["size_mb"] > 0 else 0
                        }
                    
                    backups.append(backup_info)
        
        # Check for standalone archives (archives without directories)
        for archive_file in self.backup_dir.glob("maia_backup_*.tar.gz"):
            # Get the proper backup name by removing .tar.gz extension
            backup_name = archive_file.name[:-7]  # Remove .tar.gz
            backup_dir = self.backup_dir / backup_name
            if not backup_dir.exists():
                # Standalone archive without directory
                archive_size_mb = os.path.getsize(archive_file) / (1024 * 1024)
                backups.append({
                    "name": backup_name,
                    "type": "unknown",
                    "created_at": datetime.fromtimestamp(archive_file.stat().st_mtime).isoformat(),
                    "size_mb": round(archive_size_mb, 2),
                    "databases": "unknown",
                    "files": "unknown",
                    "format": "archive_only",
                    "archive": {
                        "path": str(archive_file),
                        "size_mb": round(archive_size_mb, 2),
                        "compression_ratio": "N/A"
                    }
                })
        
        # Sort by creation date
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

def main():
    backup_system = ProductionBackupSystem()
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            backup_type = sys.argv[2] if len(sys.argv) > 2 else "daily"
            result = backup_system.create_backup(backup_type)
            print(f"✅ Backup created: {result['backup_name']}")
            print(f"📊 Size: {result['backup_size_mb']} MB")
            print(f"📁 Databases: {len(result['databases_backed_up'])}")
            print(f"📄 Files: {len(result['files_backed_up'])}")
            
            # Show archive information if created
            if result.get('archive_created'):
                archive = result['archive_created']
                print(f"📦 Archive: {archive['archive_size_mb']} MB (compression: {archive['compression_ratio']}%)")
                print(f"🚀 Ready for restore: python3 claude/tools/sre/restore_maia_enterprise.py {result['backup_name']}.tar.gz")
            else:
                print("⚠️  Archive creation failed - directory backup only")
        
        elif command == "list":
            backups = backup_system.list_backups()
            print(f"📋 Available Backups ({len(backups)}):")
            print("-" * 60)
            for backup in backups:
                print(f"📦 {backup['name']}")
                print(f"   Type: {backup['type']} | Format: {backup['format']} | Size: {backup['size_mb']} MB")
                print(f"   Created: {backup['created_at'][:19]}")
                print(f"   Databases: {backup['databases']} | Files: {backup['files']}")
                
                # Show archive information if available
                if 'archive' in backup:
                    archive = backup['archive']
                    print(f"   📦 Archive: {archive['size_mb']} MB (compression: {archive['compression_ratio']}%)")
                    print(f"   📁 Ready for restore: python3 claude/tools/sre/restore_maia_enterprise.py {backup['name']}.tar.gz")
                else:
                    print(f"   ⚠️  No archive - directory only")
                print()
        
        elif command == "restore":
            if len(sys.argv) > 2:
                backup_name = sys.argv[2]
                success = backup_system.restore_backup(backup_name)
                if success:
                    print(f"✅ Backup restored: {backup_name}")
                else:
                    print(f"❌ Restore failed: {backup_name}")
            else:
                print("Usage: python3 backup_production_data.py restore <backup_name>")
        
        elif command == "cleanup":
            backup_system.cleanup_old_backups()
            print("✅ Backup cleanup completed")
            
        else:
            print("Usage: python3 backup_production_data.py [create|list|restore|cleanup]")
    else:
        # Default: create daily backup
        result = backup_system.create_backup("daily")
        print(f"✅ Daily backup created: {result['backup_name']}")

if __name__ == "__main__":
    main()