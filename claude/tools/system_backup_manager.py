#!/usr/bin/env python3
import json
import os
import sys
import shutil
import tarfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class SystemBackupManager:
    def __init__(self):
        self.backup_dir = Path("claude/data/backups")
        self.backup_registry = self.backup_dir / "backup_registry.json"
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory structure exists"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "full_system").mkdir(exist_ok=True)
        (self.backup_dir / "incremental").mkdir(exist_ok=True)
        (self.backup_dir / "critical_files").mkdir(exist_ok=True)
    
    def create_checkpoint(self, checkpoint_name: str, description: str = "") -> Dict:
        """Create a full system checkpoint"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_id = f"{checkpoint_name}_{timestamp}"
        
        backup_info = {
            'checkpoint_id': checkpoint_id,
            'checkpoint_name': checkpoint_name,
            'description': description,
            'created_date': datetime.now().isoformat(),
            'backup_type': 'full_system',
            'files_backed_up': [],
            'backup_size_bytes': 0,
            'backup_file': None,
            'restoration_verified': False,
            'status': 'creating'
        }
        
        try:
            print(f"📦 Creating checkpoint: {checkpoint_name}")
            
            # Define what to backup
            backup_paths = [
                'claude/context',
                'claude/agents', 
                'claude/tools',
                'claude/commands',
                'claude/hooks',
                'claude/data',
                'CLAUDE.md'
            ]
            
            # Create tar archive
            backup_file = self.backup_dir / "full_system" / f"{checkpoint_id}.tar.gz"
            
            with tarfile.open(backup_file, 'w:gz') as tar:
                for backup_path in backup_paths:
                    if Path(backup_path).exists():
                        tar.add(backup_path, arcname=backup_path)
                        
                        # Record files
                        if Path(backup_path).is_file():
                            backup_info['files_backed_up'].append(backup_path)
                        else:
                            for file_path in Path(backup_path).rglob('*'):
                                if file_path.is_file():
                                    backup_info['files_backed_up'].append(str(file_path))
            
            # Get backup size
            backup_info['backup_size_bytes'] = backup_file.stat().st_size
            backup_info['backup_file'] = str(backup_file)
            backup_info['status'] = 'completed'
            
            # Verify backup integrity
            if self.verify_backup_integrity(backup_file):
                backup_info['restoration_verified'] = True
            else:
                backup_info['status'] = 'verification_failed'
            
            # Register backup
            self.register_backup(backup_info)
            
            print(f"✅ Checkpoint created: {checkpoint_id}")
            print(f"   Files backed up: {len(backup_info['files_backed_up'])}")
            print(f"   Backup size: {backup_info['backup_size_bytes'] / 1024 / 1024:.1f} MB")
            print(f"   Location: {backup_file}")
            
            return backup_info
            
        except Exception as e:
            backup_info['status'] = 'failed'
            backup_info['error'] = str(e)
            print(f"❌ Checkpoint creation failed: {e}")
            return backup_info
    
    def create_incremental_backup(self, base_checkpoint: str) -> Dict:
        """Create incremental backup based on previous checkpoint"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"incremental_{timestamp}"
        
        # Find base checkpoint
        registry = self.load_backup_registry()
        base_backup = None
        
        for backup in registry.get('backups', []):
            if backup['checkpoint_name'] == base_checkpoint:
                base_backup = backup
                break
        
        if not base_backup:
            return {'error': f'Base checkpoint not found: {base_checkpoint}'}
        
        backup_info = {
            'checkpoint_id': backup_id,
            'backup_type': 'incremental',
            'base_checkpoint': base_checkpoint,
            'created_date': datetime.now().isoformat(),
            'changed_files': [],
            'new_files': [],
            'deleted_files': [],
            'status': 'creating'
        }
        
        try:
            # Compare with base checkpoint
            changes = self.detect_changes_since_backup(base_backup)
            backup_info.update(changes)
            
            if backup_info['changed_files'] or backup_info['new_files']:
                # Create incremental backup
                backup_file = self.backup_dir / "incremental" / f"{backup_id}.tar.gz"
                
                with tarfile.open(backup_file, 'w:gz') as tar:
                    for file_path in backup_info['changed_files'] + backup_info['new_files']:
                        if Path(file_path).exists():
                            tar.add(file_path, arcname=file_path)
                
                backup_info['backup_file'] = str(backup_file)
                backup_info['backup_size_bytes'] = backup_file.stat().st_size
            
            backup_info['status'] = 'completed'
            self.register_backup(backup_info)
            
            return backup_info
            
        except Exception as e:
            backup_info['status'] = 'failed'
            backup_info['error'] = str(e)
            return backup_info
    
    def backup_critical_files(self) -> Dict:
        """Backup only critical system files quickly"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"critical_{timestamp}"
        
        critical_files = [
            'claude/context/core/identity.md',
            'claude/context/core/systematic_thinking_protocol.md',
            'claude/context/core/model_selection_strategy.md',
            'claude/context/core/ufc_system.md',
            'claude/context/core/smart_context_loading.md',
            'CLAUDE.md'
        ]
        
        backup_info = {
            'checkpoint_id': backup_id,
            'backup_type': 'critical_files',
            'created_date': datetime.now().isoformat(),
            'files_backed_up': [],
            'missing_files': [],
            'status': 'creating'
        }
        
        try:
            backup_file = self.backup_dir / "critical_files" / f"{backup_id}.tar.gz"
            
            with tarfile.open(backup_file, 'w:gz') as tar:
                for file_path in critical_files:
                    if Path(file_path).exists():
                        tar.add(file_path, arcname=file_path)
                        backup_info['files_backed_up'].append(file_path)
                    else:
                        backup_info['missing_files'].append(file_path)
            
            backup_info['backup_file'] = str(backup_file)
            backup_info['backup_size_bytes'] = backup_file.stat().st_size
            backup_info['status'] = 'completed'
            
            self.register_backup(backup_info)
            
            return backup_info
            
        except Exception as e:
            backup_info['status'] = 'failed'
            backup_info['error'] = str(e)
            return backup_info
    
    def verify_backup_integrity(self, backup_file: Path) -> bool:
        """Verify backup file integrity"""
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Try to list all members
                members = tar.getmembers()
                
                # Verify we can read a few key files
                for member in members[:5]:  # Check first 5 files
                    if member.isfile():
                        tar.extractfile(member).read()
                
                return True
        except Exception:
            return False
    
    def detect_changes_since_backup(self, base_backup: Dict) -> Dict:
        """Detect changes since a previous backup"""
        changes = {
            'changed_files': [],
            'new_files': [],
            'deleted_files': []
        }
        
        base_date = datetime.fromisoformat(base_backup['created_date'])
        base_files = set(base_backup.get('files_backed_up', []))
        
        # Scan current files
        current_files = set()
        scan_paths = ['claude/context', 'claude/agents', 'claude/tools', 'claude/commands', 'claude/hooks']
        
        for scan_path in scan_paths:
            if Path(scan_path).exists():
                for file_path in Path(scan_path).rglob('*'):
                    if file_path.is_file():
                        current_files.add(str(file_path))
                        
                        # Check if file is new or changed
                        file_mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if str(file_path) not in base_files:
                            changes['new_files'].append(str(file_path))
                        elif file_mod_time > base_date:
                            changes['changed_files'].append(str(file_path))
        
        # Find deleted files
        changes['deleted_files'] = list(base_files - current_files)
        
        return changes
    
    def restore_checkpoint(self, checkpoint_name: str, target_dir: Optional[str] = None) -> Dict:
        """Restore from a checkpoint"""
        registry = self.load_backup_registry()
        backup_to_restore = None
        
        # Find the backup
        for backup in registry.get('backups', []):
            if backup['checkpoint_name'] == checkpoint_name or backup['checkpoint_id'] == checkpoint_name:
                backup_to_restore = backup
                break
        
        if not backup_to_restore:
            return {'error': f'Checkpoint not found: {checkpoint_name}'}
        
        if backup_to_restore['status'] != 'completed':
            return {'error': f'Checkpoint not completed successfully: {backup_to_restore["status"]}'}
        
        restore_info = {
            'checkpoint_restored': checkpoint_name,
            'restore_date': datetime.now().isoformat(),
            'files_restored': [],
            'restoration_target': target_dir or '.',
            'status': 'restoring'
        }
        
        try:
            backup_file = Path(backup_to_restore['backup_file'])
            if not backup_file.exists():
                return {'error': f'Backup file not found: {backup_file}'}
            
            print(f"🔄 Restoring checkpoint: {checkpoint_name}")
            print(f"   Backup file: {backup_file}")
            print(f"   Target: {restore_info['restoration_target']}")
            
            # Extract backup
            with tarfile.open(backup_file, 'r:gz') as tar:
                if target_dir:
                    tar.extractall(path=target_dir)
                else:
                    tar.extractall()
                
                restore_info['files_restored'] = [member.name for member in tar.getmembers() if member.isfile()]
            
            restore_info['status'] = 'completed'
            
            print(f"✅ Restoration completed")
            print(f"   Files restored: {len(restore_info['files_restored'])}")
            
            return restore_info
            
        except Exception as e:
            restore_info['status'] = 'failed'
            restore_info['error'] = str(e)
            print(f"❌ Restoration failed: {e}")
            return restore_info
    
    def list_checkpoints(self) -> List[Dict]:
        """List all available checkpoints"""
        registry = self.load_backup_registry()
        backups = registry.get('backups', [])
        
        # Sort by creation date, newest first
        return sorted(backups, key=lambda x: x['created_date'], reverse=True)
    
    def get_checkpoint_info(self, checkpoint_name: str) -> Optional[Dict]:
        """Get detailed information about a checkpoint"""
        registry = self.load_backup_registry()
        
        for backup in registry.get('backups', []):
            if backup['checkpoint_name'] == checkpoint_name or backup['checkpoint_id'] == checkpoint_name:
                return backup
        
        return None
    
    def delete_checkpoint(self, checkpoint_name: str) -> Dict:
        """Delete a checkpoint"""
        registry = self.load_backup_registry()
        backup_to_delete = None
        backup_index = None
        
        for i, backup in enumerate(registry.get('backups', [])):
            if backup['checkpoint_name'] == checkpoint_name or backup['checkpoint_id'] == checkpoint_name:
                backup_to_delete = backup
                backup_index = i
                break
        
        if not backup_to_delete:
            return {'error': f'Checkpoint not found: {checkpoint_name}'}
        
        try:
            # Delete backup file
            if backup_to_delete.get('backup_file'):
                backup_file = Path(backup_to_delete['backup_file'])
                if backup_file.exists():
                    backup_file.unlink()
            
            # Remove from registry
            registry['backups'].pop(backup_index)
            self.save_backup_registry(registry)
            
            return {
                'deleted_checkpoint': checkpoint_name,
                'deleted_file': backup_to_delete.get('backup_file'),
                'status': 'success'
            }
            
        except Exception as e:
            return {'error': f'Failed to delete checkpoint: {e}'}
    
    def register_backup(self, backup_info: Dict):
        """Register backup in registry"""
        registry = self.load_backup_registry()
        
        if 'backups' not in registry:
            registry['backups'] = []
        
        registry['backups'].append(backup_info)
        registry['last_updated'] = datetime.now().isoformat()
        
        self.save_backup_registry(registry)
    
    def load_backup_registry(self) -> Dict:
        """Load backup registry"""
        if self.backup_registry.exists():
            try:
                with open(self.backup_registry, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'created_date': datetime.now().isoformat(),
            'backups': []
        }
    
    def save_backup_registry(self, registry: Dict):
        """Save backup registry"""
        with open(self.backup_registry, 'w') as f:
            json.dump(registry, f, indent=2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 system_backup_manager.py <command>")
        print("Commands:")
        print("  create-checkpoint <name> [description]  - Create full system checkpoint")
        print("  backup-critical                        - Backup critical files only")
        print("  restore <checkpoint_name>              - Restore from checkpoint")
        print("  list                                   - List all checkpoints")
        print("  info <checkpoint_name>                 - Show checkpoint details")
        print("  delete <checkpoint_name>               - Delete checkpoint")
        print("  verify-checkpoint <checkpoint_name>    - Verify checkpoint integrity")
        return
    
    command = sys.argv[1]
    manager = SystemBackupManager()
    
    if command == 'create-checkpoint':
        if len(sys.argv) < 3:
            print("Usage: create-checkpoint <name> [description]")
            return
        
        checkpoint_name = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        
        result = manager.create_checkpoint(checkpoint_name, description)
        
        if result['status'] == 'completed':
            print(f"🎉 Checkpoint '{checkpoint_name}' created successfully")
        else:
            print(f"❌ Checkpoint creation failed: {result.get('error', 'Unknown error')}")
    
    elif command == 'backup-critical':
        print("⚡ Creating critical files backup...")
        result = manager.backup_critical_files()
        
        if result['status'] == 'completed':
            print(f"✅ Critical files backup completed")
            print(f"   Files backed up: {len(result['files_backed_up'])}")
            if result['missing_files']:
                print(f"   Missing files: {len(result['missing_files'])}")
                for file_path in result['missing_files']:
                    print(f"     • {file_path}")
        else:
            print(f"❌ Critical backup failed: {result.get('error', 'Unknown error')}")
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Usage: restore <checkpoint_name>")
            return
        
        checkpoint_name = sys.argv[2]
        
        # Confirm restoration
        print(f"⚠️  This will restore system to checkpoint: {checkpoint_name}")
        print("   Current files may be overwritten!")
        confirm = input("Continue? (y/N): ").lower()
        
        if confirm != 'y':
            print("❌ Restoration cancelled")
            return
        
        result = manager.restore_checkpoint(checkpoint_name)
        
        if result.get('status') == 'completed':
            print(f"🎉 System restored to checkpoint: {checkpoint_name}")
        else:
            print(f"❌ Restoration failed: {result.get('error', 'Unknown error')}")
    
    elif command == 'list':
        checkpoints = manager.list_checkpoints()
        
        if not checkpoints:
            print("📋 No checkpoints found")
            return
        
        print("📋 Available Checkpoints:")
        print("=" * 80)
        
        for backup in checkpoints:
            status_emoji = {'completed': '✅', 'failed': '❌', 'creating': '🔄'}
            emoji = status_emoji.get(backup['status'], '❓')
            
            print(f"{emoji} {backup['checkpoint_name']} ({backup['checkpoint_id']})")
            print(f"   Created: {backup['created_date'][:16]}")
            print(f"   Type: {backup['backup_type']}")
            if backup.get('files_backed_up'):
                print(f"   Files: {len(backup['files_backed_up'])}")
            if backup.get('backup_size_bytes'):
                size_mb = backup['backup_size_bytes'] / 1024 / 1024
                print(f"   Size: {size_mb:.1f} MB")
            if backup.get('description'):
                print(f"   Description: {backup['description']}")
            print()
    
    elif command == 'info':
        if len(sys.argv) < 3:
            print("Usage: info <checkpoint_name>")
            return
        
        checkpoint_name = sys.argv[2]
        info = manager.get_checkpoint_info(checkpoint_name)
        
        if not info:
            print(f"❌ Checkpoint not found: {checkpoint_name}")
            return
        
        print(f"📋 Checkpoint Information: {info['checkpoint_name']}")
        print("=" * 50)
        print(f"ID: {info['checkpoint_id']}")
        print(f"Type: {info['backup_type']}")
        print(f"Created: {info['created_date']}")
        print(f"Status: {info['status']}")
        
        if info.get('description'):
            print(f"Description: {info['description']}")
        
        if info.get('backup_file'):
            print(f"Backup file: {info['backup_file']}")
        
        if info.get('files_backed_up'):
            print(f"Files backed up: {len(info['files_backed_up'])}")
        
        if info.get('backup_size_bytes'):
            size_mb = info['backup_size_bytes'] / 1024 / 1024
            print(f"Backup size: {size_mb:.1f} MB")
        
        if info.get('restoration_verified'):
            print(f"Integrity verified: {'✅ Yes' if info['restoration_verified'] else '❌ No'}")
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Usage: delete <checkpoint_name>")
            return
        
        checkpoint_name = sys.argv[2]
        
        # Confirm deletion
        print(f"⚠️  This will permanently delete checkpoint: {checkpoint_name}")
        confirm = input("Continue? (y/N): ").lower()
        
        if confirm != 'y':
            print("❌ Deletion cancelled")
            return
        
        result = manager.delete_checkpoint(checkpoint_name)
        
        if 'error' not in result:
            print(f"✅ Checkpoint deleted: {checkpoint_name}")
        else:
            print(f"❌ Deletion failed: {result['error']}")
    
    elif command == 'verify-checkpoint':
        if len(sys.argv) < 3:
            print("Usage: verify-checkpoint <checkpoint_name>")
            return
        
        checkpoint_name = sys.argv[2]
        info = manager.get_checkpoint_info(checkpoint_name)
        
        if not info:
            print(f"❌ Checkpoint not found: {checkpoint_name}")
            return
        
        if not info.get('backup_file'):
            print(f"❌ No backup file found for checkpoint")
            return
        
        backup_file = Path(info['backup_file'])
        if not backup_file.exists():
            print(f"❌ Backup file missing: {backup_file}")
            return
        
        print(f"🔍 Verifying checkpoint: {checkpoint_name}")
        
        if manager.verify_backup_integrity(backup_file):
            print("✅ Checkpoint integrity verified")
        else:
            print("❌ Checkpoint integrity check failed")

if __name__ == "__main__":
    main()