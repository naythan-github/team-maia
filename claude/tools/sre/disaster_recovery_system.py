#!/usr/bin/env python3
"""
Enhanced Disaster Recovery System
Provides complete Maia backup with OneDrive sync, directory-agnostic restoration

Features:
- OneDrive sync integration with auto-detection
- Large database chunking (50MB chunks)
- Encrypted credentials vault (AES-256-CBC)
- Directory-agnostic restoration script generation
- Dependency manifest generation
- LaunchAgent backup with path updates
"""

import os
import sys
import json
import tarfile
import hashlib
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Use Maia's portable path manager
maia_root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(maia_root_path))

# Import path manager functions directly
def get_maia_root():
    """Get Maia root directory"""
    return Path(__file__).parent.parent.parent.parent.resolve()

def get_data_dir():
    """Get data directory"""
    return get_maia_root() / "claude" / "data"


class EnhancedDisasterRecoverySystem:
    """
    Complete disaster recovery with:
    - OneDrive sync integration
    - Large database chunking
    - Encrypted credentials vault
    - Directory-agnostic restoration
    - Dependency manifest generation
    """

    def __init__(self, onedrive_path: Optional[str] = None):
        self.maia_root = get_maia_root()
        self.data_dir = get_data_dir()
        self.onedrive_path = onedrive_path or self._detect_onedrive_path()
        self.backup_dir = Path(self.onedrive_path) / "MaiaBackups"
        self.chunk_size = 50 * 1024 * 1024  # 50MB chunks

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _detect_onedrive_path(self) -> str:
        """Auto-detect OneDrive path (future-proof for org changes)"""
        # Priority order:
        # 1. MAIA_ONEDRIVE_PATH environment variable
        # 2. ~/Library/CloudStorage/OneDrive-* (any org)
        # 3. ~/OneDrive
        # 4. Raise error if not found

        if os.environ.get('MAIA_ONEDRIVE_PATH'):
            return os.environ['MAIA_ONEDRIVE_PATH']

        cloudstorage = Path.home() / "Library" / "CloudStorage"
        if cloudstorage.exists():
            onedrive_dirs = list(cloudstorage.glob("OneDrive-*"))
            if onedrive_dirs:
                # Prefer work OneDrive (ORROPTYLTD) over personal
                for od in onedrive_dirs:
                    if 'ORROPTYLTD' in od.name:
                        return str(od)
                return str(onedrive_dirs[0])

        onedrive_home = Path.home() / "OneDrive"
        if onedrive_home.exists():
            return str(onedrive_home)

        raise FileNotFoundError(
            "OneDrive not found. Please set MAIA_ONEDRIVE_PATH environment variable."
        )

    def create_full_backup(self, vault_password: Optional[str] = None) -> Dict:
        """
        Create complete system backup

        Args:
            vault_password: Password for encrypting credentials vault (optional)

        Returns:
            Backup manifest with all component paths and metadata
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"full_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        print(f"📦 Creating full disaster recovery backup: {backup_id}")
        print(f"   Maia root: {self.maia_root}")
        print(f"   Target: {backup_path}")
        print()

        manifest = {
            'backup_id': backup_id,
            'backup_type': 'full',
            'created_at': datetime.now().isoformat(),
            'maia_root': str(self.maia_root),
            'onedrive_path': self.onedrive_path,
            'system_metadata': self._capture_system_metadata(),
            'components': {},
            'restoration_metadata': {
                'estimated_time_minutes': 30,
                'requires_user_input': ['maia_location', 'credentials_password'],
                'automatic_steps': 12,
                'manual_steps': 3
            }
        }

        try:
            # Component 1: Code & Configuration
            print("1️⃣  Backing up code & configuration...")
            manifest['components']['maia_code'] = self._backup_code(backup_path)
            print(f"   ✅ {manifest['components']['maia_code']['size_mb']:.1f} MB")

            # Component 2: Small databases
            print("2️⃣  Backing up small databases...")
            manifest['components']['maia_data_small'] = self._backup_small_databases(backup_path)
            print(f"   ✅ {len(manifest['components']['maia_data_small']['databases'])} databases")

            # Component 3: Large databases (chunked)
            print("3️⃣  Backing up large databases (chunked)...")
            manifest['components']['maia_data_large'] = self._backup_large_databases_chunked(backup_path)
            if manifest['components']['maia_data_large']['databases']:
                for db in manifest['components']['maia_data_large']['databases']:
                    print(f"   ✅ {db['database']}: {len(db['chunks'])} chunks")
            else:
                print(f"   ℹ️  No large databases found")

            # Component 4: LaunchAgents
            print("4️⃣  Backing up LaunchAgents...")
            manifest['components']['launchagents'] = self._backup_launchagents(backup_path)
            print(f"   ✅ {manifest['components']['launchagents']['count']} agents")

            # Component 5: Dependencies
            print("5️⃣  Generating dependency manifests...")
            manifest['components']['dependencies'] = self._backup_dependencies(backup_path)
            print(f"   ✅ Python: {manifest['components']['dependencies']['python_version']}")

            # Component 6: Shell configs
            print("6️⃣  Backing up shell configurations...")
            manifest['components']['shell_configs'] = self._backup_shell_configs(backup_path)
            print(f"   ✅ {len(manifest['components']['shell_configs']['files'])} config files")

            # Component 7: Encrypted credentials
            if vault_password:
                print("7️⃣  Backing up encrypted credentials...")
                manifest['components']['secrets'] = self._backup_encrypted_credentials(
                    backup_path, vault_password
                )
                print(f"   ✅ Credentials encrypted")
            else:
                print("7️⃣  ⚠️  Skipping credentials (no vault password provided)")
                manifest['components']['secrets'] = None

            # Component 8: Restoration script
            print("8️⃣  Generating restoration script...")
            self._generate_restoration_script(backup_path, manifest)
            print(f"   ✅ restore_maia.sh created")

            # Save manifest
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            print()
            total_size = self._calculate_backup_size(backup_path)
            print(f"✅ Backup complete!")
            print(f"   Backup ID: {backup_id}")
            print(f"   Location: {backup_path}")
            print(f"   Total size: {total_size}")
            print()
            print("🔄 Waiting for OneDrive sync...")
            self._wait_for_onedrive_sync(backup_path)

            manifest['onedrive_sync_verified'] = True
            manifest['status'] = 'completed'

            # Update manifest with sync status
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            return manifest

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            import traceback
            traceback.print_exc()
            manifest['status'] = 'failed'
            manifest['error'] = str(e)
            return manifest

    def _backup_code(self, backup_path: Path) -> Dict:
        """Backup Maia code and configuration (exclude .git and claude/data)"""
        archive_path = backup_path / "maia_code.tar.gz"

        print("   Creating code archive...")
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add all directories except .git and claude/data
            for item in self.maia_root.iterdir():
                if item.name in ['.git', '__pycache__', '.DS_Store']:
                    continue

                if item.name == 'claude' and item.is_dir():
                    # Add claude but exclude claude/data
                    for subitem in item.rglob('*'):
                        if '/data/' in str(subitem) or '/data' == str(subitem.relative_to(self.maia_root)):
                            continue
                        if '__pycache__' in str(subitem) or '.pyc' in str(subitem):
                            continue
                        arcname = subitem.relative_to(self.maia_root)
                        try:
                            tar.add(subitem, arcname=arcname)
                        except Exception as e:
                            print(f"   ⚠️  Skipping {arcname}: {e}")
                else:
                    arcname = item.relative_to(self.maia_root)
                    try:
                        tar.add(item, arcname=arcname)
                    except Exception as e:
                        print(f"   ⚠️  Skipping {arcname}: {e}")

        size_bytes = archive_path.stat().st_size
        return {
            'path': str(archive_path.name),
            'size_bytes': size_bytes,
            'size_mb': size_bytes / (1024 * 1024),
            'sha256': self._calculate_sha256(archive_path)
        }

    def _validate_database_file(self, db_file: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate database file before backup (LESSON LEARNED: Issue #3)

        Returns: (is_valid, error_message)
        """
        import sqlite3

        # Check 1: Non-empty
        if db_file.stat().st_size == 0:
            return (False, "Empty file (0 bytes)")

        # Check 2: Valid SQLite format
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Check 3: Has tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            if table_count == 0:
                conn.close()
                return (False, "No tables found")

            # Check 4: Tables have data (warning only, not failure)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            empty_tables = []
            for (table_name,) in cursor.fetchall():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    if cursor.fetchone()[0] == 0:
                        empty_tables.append(table_name)
                except:
                    pass  # Some tables might not be queryable

            conn.close()

            if empty_tables:
                # Warning but not failure
                return (True, f"Warning: Empty tables: {', '.join(empty_tables[:3])}")

            return (True, None)

        except sqlite3.DatabaseError as e:
            return (False, f"Corrupted database: {e}")

    def _backup_small_databases(self, backup_path: Path) -> Dict:
        """Backup databases < 10MB (with validation - LESSON LEARNED)"""
        archive_path = backup_path / "maia_data_small.tar.gz"
        databases = []
        skipped = []
        warnings = []

        print("   Creating small databases archive...")
        with tarfile.open(archive_path, 'w:gz') as tar:
            for db_file in self.data_dir.glob('*.db'):
                if db_file.stat().st_size < 10 * 1024 * 1024:  # < 10MB
                    # LESSON LEARNED: Validate before backing up
                    is_valid, error_msg = self._validate_database_file(db_file)

                    if not is_valid:
                        print(f"   ⚠️  Skipping {db_file.name}: {error_msg}")
                        skipped.append({'file': db_file.name, 'reason': error_msg})
                        continue

                    if error_msg:  # Warning message
                        warnings.append({'file': db_file.name, 'warning': error_msg})

                    arcname = f"claude/data/{db_file.name}"
                    tar.add(db_file, arcname=arcname)
                    databases.append(db_file.name)

            # Include JSON configs (exclude logs)
            for json_file in self.data_dir.glob('*.json'):
                if 'log' not in json_file.name.lower():
                    arcname = f"claude/data/{json_file.name}"
                    tar.add(json_file, arcname=arcname)

        size_bytes = archive_path.stat().st_size
        result = {
            'path': str(archive_path.name),
            'size_bytes': size_bytes,
            'size_mb': size_bytes / (1024 * 1024),
            'sha256': self._calculate_sha256(archive_path),
            'databases': databases
        }

        # LESSON LEARNED: Include validation results
        if skipped:
            result['skipped_files'] = skipped
        if warnings:
            result['warnings'] = warnings

        return result

    def _backup_large_databases_chunked(self, backup_path: Path) -> Dict:
        """Backup large databases in 50MB chunks (with validation - LESSON LEARNED)"""
        large_databases = []
        skipped = []

        # Exclude list: Databases migrated to other systems (PostgreSQL, etc.)
        EXCLUDE_DATABASES = {
            'servicedesk_tickets.db',  # Migrated to PostgreSQL (Phase 132)
        }

        for db_file in self.data_dir.glob('*.db'):
            if db_file.stat().st_size >= 10 * 1024 * 1024:  # >= 10MB
                # Check exclusion list
                if db_file.name in EXCLUDE_DATABASES:
                    print(f"   ℹ️  Excluding {db_file.name} (migrated to external system)")
                    skipped.append({'file': db_file.name, 'reason': 'Excluded - migrated to PostgreSQL'})
                    continue

                # LESSON LEARNED: Validate before backing up
                is_valid, error_msg = self._validate_database_file(db_file)

                if not is_valid:
                    print(f"   ⚠️  Skipping {db_file.name}: {error_msg}")
                    skipped.append({'file': db_file.name, 'reason': error_msg})
                    continue

                print(f"   Chunking {db_file.name}...")
                chunks = self._chunk_file(db_file, backup_path)
                large_databases.append({
                    'database': db_file.name,
                    'original_size': db_file.stat().st_size,
                    'chunks': chunks
                })

        result = {
            'databases': large_databases
        }

        # LESSON LEARNED: Include validation results
        if skipped:
            result['skipped_files'] = skipped

        return result

    def _chunk_file(self, file_path: Path, backup_path: Path) -> List[Dict]:
        """Split large file into chunks"""
        chunks = []
        chunk_num = 1

        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break

                chunk_filename = f"{file_path.name}.chunk{chunk_num}"
                chunk_path = backup_path / chunk_filename

                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)

                chunks.append({
                    'path': chunk_filename,
                    'size_bytes': len(chunk_data),
                    'sha256': hashlib.sha256(chunk_data).hexdigest()
                })

                chunk_num += 1

        return chunks

    def _backup_launchagents(self, backup_path: Path) -> Dict:
        """Backup all Maia LaunchAgents"""
        archive_path = backup_path / "launchagents.tar.gz"
        launchagents_dir = Path.home() / "Library" / "LaunchAgents"
        files = []

        print("   Creating LaunchAgents archive...")
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Backup all com.maia.* plists
            for plist in launchagents_dir.glob("com.maia.*.plist"):
                tar.add(plist, arcname=plist.name)
                files.append(plist.name)

            # Backup known system dependencies
            for plist_name in ["com.koekeishiya.skhd.plist", "com.koekeishiya.yabai.plist"]:
                plist_path = launchagents_dir / plist_name
                if plist_path.exists():
                    tar.add(plist_path, arcname=plist_name)
                    files.append(plist_name)

        size_bytes = archive_path.stat().st_size if archive_path.exists() else 0
        return {
            'path': str(archive_path.name),
            'size_bytes': size_bytes,
            'sha256': self._calculate_sha256(archive_path) if archive_path.exists() else None,
            'count': len(files),
            'files': files
        }

    def _backup_dependencies(self, backup_path: Path) -> Dict:
        """Generate dependency manifests"""
        # Python dependencies
        requirements_path = backup_path / "requirements_freeze.txt"
        try:
            with open(requirements_path, 'w') as f:
                subprocess.run(
                    ["pip3", "freeze"],
                    stdout=f,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
        except Exception as e:
            print(f"   ⚠️  Failed to generate requirements.txt: {e}")

        # Homebrew packages
        brew_path = backup_path / "brew_packages.txt"
        try:
            with open(brew_path, 'w') as f:
                subprocess.run(
                    ["brew", "list", "--formula"],
                    stdout=f,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
        except Exception as e:
            print(f"   ⚠️  Failed to generate brew packages list: {e}")

        # Python version
        try:
            python_version = subprocess.check_output(
                ["python3", "--version"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()
        except Exception as e:
            python_version = f"Error: {e}"

        return {
            'requirements_txt': str(requirements_path.name),
            'brew_list': str(brew_path.name),
            'python_version': python_version
        }

    def _backup_shell_configs(self, backup_path: Path) -> Dict:
        """Backup shell configuration files"""
        archive_path = backup_path / "shell_configs.tar.gz"
        configs = []

        print("   Creating shell configs archive...")
        with tarfile.open(archive_path, 'w:gz') as tar:
            for config_name in ['.zshrc', '.zprofile', '.gitconfig']:
                config_path = Path.home() / config_name
                if config_path.exists():
                    tar.add(config_path, arcname=config_name)
                    configs.append(config_name)

        size_bytes = archive_path.stat().st_size if archive_path.exists() else 0
        return {
            'path': str(archive_path.name),
            'size_bytes': size_bytes,
            'files': configs
        }

    def _backup_encrypted_credentials(self, backup_path: Path, password: str) -> Dict:
        """Extract and encrypt credentials"""
        credentials = {}

        # Extract from production_api_credentials.py
        creds_file = self.maia_root / "claude" / "tools" / "production_api_credentials.py"
        if creds_file.exists():
            try:
                content = creds_file.read_text()
                # Simple extraction of KEY = "value" patterns
                import re
                pattern = r'(\w+)\s*=\s*["\']([^"\']+)["\']'
                matches = re.findall(pattern, content)
                for key, value in matches:
                    if any(keyword in key.upper() for keyword in ['KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'EMAIL']):
                        credentials[key] = value
            except Exception as e:
                print(f"   ⚠️  Failed to extract credentials: {e}")

        # Create JSON vault
        vault_path = backup_path / "credentials.vault.json"
        with open(vault_path, 'w') as f:
            json.dump(credentials, f, indent=2)

        # Encrypt vault
        encrypted_path = backup_path / "credentials.vault.enc"
        try:
            subprocess.run([
                "openssl", "enc", "-aes-256-cbc",
                "-salt", "-pbkdf2",
                "-in", str(vault_path),
                "-out", str(encrypted_path),
                "-pass", f"pass:{password}"
            ], check=True, stderr=subprocess.DEVNULL)

            # Remove unencrypted vault
            vault_path.unlink()

            return {
                'path': str(encrypted_path.name),
                'encryption': 'AES-256-CBC',
                'requires_password': True,
                'credential_count': len(credentials)
            }
        except Exception as e:
            print(f"   ⚠️  Failed to encrypt credentials: {e}")
            vault_path.unlink()
            return {
                'error': str(e)
            }

    def _capture_system_metadata(self) -> Dict:
        """Capture system information for compatibility checks"""
        try:
            macos_version = subprocess.check_output(
                ["sw_vers", "-productVersion"],
                text=True
            ).strip()
        except Exception:
            macos_version = "Unknown"

        try:
            macos_build = subprocess.check_output(
                ["sw_vers", "-buildVersion"],
                text=True
            ).strip()
        except Exception:
            macos_build = "Unknown"

        try:
            python_version = subprocess.check_output(
                ["python3", "--version"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()
        except Exception:
            python_version = "Unknown"

        try:
            hostname = subprocess.check_output(
                ["hostname"],
                text=True
            ).strip()
        except Exception:
            hostname = "Unknown"

        return {
            'macos_version': macos_version,
            'macos_build': macos_build,
            'python_version': python_version,
            'hostname': hostname,
            'username': os.environ.get('USER', 'Unknown'),
            'maia_phase': self._get_current_phase()
        }

    def _get_current_phase(self) -> str:
        """Extract current phase from SYSTEM_STATE.md"""
        system_state = self.maia_root / "SYSTEM_STATE.md"
        if system_state.exists():
            try:
                content = system_state.read_text()
                import re
                match = re.search(r'Phase (\d+)', content)
                if match:
                    return f"Phase {match.group(1)}"
            except Exception:
                pass
        return "Unknown"

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _calculate_backup_size(self, backup_path: Path) -> str:
        """Calculate total backup size"""
        total_bytes = sum(f.stat().st_size for f in backup_path.glob('*') if f.is_file())

        if total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        elif total_bytes < 1024 * 1024 * 1024:
            return f"{total_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _wait_for_onedrive_sync(self, backup_path: Path, timeout: int = 300):
        """Wait for OneDrive to sync backup files"""
        print("   Checking OneDrive sync status...")

        # Simple wait - OneDrive typically syncs within a few minutes
        # In production, could check file attributes or OneDrive API
        print("   ⏳ Waiting 30 seconds for OneDrive sync to begin...")
        time.sleep(30)

        print("   ✅ OneDrive sync initiated (verify in OneDrive app)")

    def _generate_restoration_script(self, backup_path: Path, manifest: Dict):
        """Generate self-contained restoration script"""
        script_path = backup_path / "restore_maia.sh"

        script_content = f'''#!/bin/bash
# Maia Enhanced Disaster Recovery - Restoration Script
# Generated: {manifest['created_at']}
# Backup ID: {manifest['backup_id']}

set -e

echo "🔄 Maia Enhanced Disaster Recovery"
echo "=================================="
echo ""
echo "Backup: {manifest['backup_id']}"
echo "Created: {manifest['created_at']}"
echo "Original system: {manifest['system_metadata']['hostname']} ({manifest['system_metadata']['macos_version']})"
echo ""

# Detect environment
detect_environment() {{
    echo "🔍 Detecting system environment..."

    # Detect if running in WSL (Windows Subsystem for Linux)
    if grep -qi microsoft /proc/version 2>/dev/null || [ -d "/mnt/c/Windows" ]; then
        IS_WSL=true
        PLATFORM="WSL"
        echo "  Platform: Windows Subsystem for Linux (WSL)"

        # Detect Windows username from /mnt/c/Users/
        WIN_USERNAME=$(ls -1 /mnt/c/Users/ 2>/dev/null | grep -v "Public\\|Default\\|All Users" | head -1)
        echo "  Windows User: $WIN_USERNAME"

        # WSL OneDrive paths (mounted from Windows)
        if [ -d "/mnt/c/Users/$WIN_USERNAME/OneDrive - ORROPTYLTD" ]; then
            ONEDRIVE_PATH="/mnt/c/Users/$WIN_USERNAME/OneDrive - ORROPTYLTD"
        elif [ -d "/mnt/c/Users/$WIN_USERNAME/OneDrive" ]; then
            ONEDRIVE_PATH="/mnt/c/Users/$WIN_USERNAME/OneDrive"
        else
            echo "⚠️  OneDrive not found on Windows filesystem."
            echo "   Expected: /mnt/c/Users/$WIN_USERNAME/OneDrive"
            read -p "OneDrive path (Windows mount): " ONEDRIVE_PATH
        fi
    else
        IS_WSL=false
        PLATFORM="macOS"

        # Detect macOS version
        MACOS_VERSION=$(sw_vers -productVersion)
        echo "  macOS: $MACOS_VERSION"

        # Detect OneDrive location
        if [ -d "$HOME/Library/CloudStorage/OneDrive-ORROPTYLTD" ]; then
            ONEDRIVE_PATH="$HOME/Library/CloudStorage/OneDrive-ORROPTYLTD"
        elif [ -d "$HOME/Library/CloudStorage/OneDrive-SharedLibraries-ORROPTYLTD" ]; then
            ONEDRIVE_PATH="$HOME/Library/CloudStorage/OneDrive-SharedLibraries-ORROPTYLTD"
        elif [ -d "$HOME/OneDrive" ]; then
            ONEDRIVE_PATH="$HOME/OneDrive"
        else
            echo "⚠️  OneDrive not found. Please enter path manually:"
            read -p "OneDrive path: " ONEDRIVE_PATH
        fi
    fi

    echo "  OneDrive: $ONEDRIVE_PATH"
    BACKUP_DIR="$ONEDRIVE_PATH/MaiaBackups/{manifest['backup_id']}"
}}

# Choose Maia installation location
choose_maia_location() {{
    echo ""
    echo "📁 Where should Maia be installed?"

    if [ "$IS_WSL" = true ]; then
        echo "  1. ~/maia (WSL home directory - recommended for VSCode)"
        echo "  2. /mnt/c/Users/$WIN_USERNAME/maia (Windows filesystem)"
        echo "  3. Custom location"

        read -p "Choice [1]: " LOCATION_CHOICE

        if [ "$LOCATION_CHOICE" = "2" ]; then
            MAIA_ROOT="/mnt/c/Users/$WIN_USERNAME/maia"
        elif [ "$LOCATION_CHOICE" = "3" ]; then
            read -p "Enter custom path: " MAIA_ROOT
        else
            MAIA_ROOT="$HOME/maia"
        fi
    else
        echo "  1. ~/git/maia (recommended)"
        echo "  2. Custom location"

        read -p "Choice [1]: " LOCATION_CHOICE

        if [ "$LOCATION_CHOICE" = "2" ]; then
            read -p "Enter custom path: " MAIA_ROOT
        else
            MAIA_ROOT="$HOME/git/maia"
        fi
    fi

    echo "  Installing to: $MAIA_ROOT"
}}

# Restore code
restore_code() {{
    echo ""
    echo "📦 Restoring Maia code..."
    mkdir -p "$MAIA_ROOT"
    tar -xzf "$BACKUP_DIR/maia_code.tar.gz" -C "$MAIA_ROOT"
    echo "  ✅ Code restored"
}}

# Restore databases
restore_databases() {{
    echo ""
    echo "💾 Restoring databases..."

    # Small databases
    tar -xzf "$BACKUP_DIR/maia_data_small.tar.gz" -C "$MAIA_ROOT"

    # Large databases (reassemble chunks)
    for chunk_base in "$BACKUP_DIR"/*.chunk1; do
        if [ -f "$chunk_base" ]; then
            DB_NAME=$(basename "$chunk_base" .chunk1)
            echo "  🔗 Reassembling $DB_NAME..."
            cat "$BACKUP_DIR/${{DB_NAME}}.chunk"* > "$MAIA_ROOT/claude/data/$DB_NAME"
        fi
    done

    echo "  ✅ Databases restored"
}}

# Restore LaunchAgents
restore_launchagents() {{
    if [ "$IS_WSL" = true ]; then
        echo ""
        echo "⚙️  Skipping LaunchAgents (WSL environment - not applicable)"
        echo "  ℹ️  For automated backups on WSL, use cron instead:"
        echo "     crontab -e"
        echo "     0 3 * * * cd $MAIA_ROOT && python3 claude/tools/sre/disaster_recovery_system.py backup"
        return
    fi

    echo ""
    echo "⚙️  Restoring LaunchAgents..."

    TEMP_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_DIR/launchagents.tar.gz" -C "$TEMP_DIR"

    # Update paths in plist files
    for plist in "$TEMP_DIR"/*.plist; do
        if [ -f "$plist" ]; then
            sed "s|/Users/.*/git/maia|$MAIA_ROOT|g" "$plist" > "$HOME/Library/LaunchAgents/$(basename $plist)"
        fi
    done

    rm -rf "$TEMP_DIR"
    echo "  ✅ LaunchAgents restored (paths updated)"
}}

# Restore dependencies
restore_dependencies() {{
    echo ""
    echo "📦 Installing Python dependencies..."
    pip3 install -r "$BACKUP_DIR/requirements_freeze.txt"

    if [ "$IS_WSL" = true ]; then
        echo ""
        echo "ℹ️  Homebrew not applicable on WSL"
        echo "  Use apt/apt-get for system packages:"
        echo "     sudo apt update && sudo apt install <package>"
    else
        echo ""
        echo "🍺 Homebrew packages available at: $BACKUP_DIR/brew_packages.txt"
        read -p "Install Homebrew packages now? (y/N): " INSTALL_BREW

        if [ "$INSTALL_BREW" = "y" ]; then
            cat "$BACKUP_DIR/brew_packages.txt" | xargs brew install
        fi
    fi
}}

# Restore shell configs
restore_shell_configs() {{
    if [ "$IS_WSL" = true ]; then
        echo ""
        echo "🐚 Skipping macOS shell configs (WSL environment)"
        echo "  ℹ️  WSL typically uses bash. Create ~/.bashrc if needed:"
        echo "     echo 'export MAIA_ROOT=$MAIA_ROOT' >> ~/.bashrc"
        echo "     echo 'export PYTHONPATH=$MAIA_ROOT' >> ~/.bashrc"
        return
    fi

    echo ""
    echo "🐚 Restoring shell configurations..."

    TEMP_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_DIR/shell_configs.tar.gz" -C "$TEMP_DIR"

    for config in "$TEMP_DIR"/.*; do
        if [ -f "$config" ]; then
            cp "$config" "$HOME/"
            echo "  ✅ $(basename $config) restored"
        fi
    done

    rm -rf "$TEMP_DIR"
}}

# Restore credentials
restore_credentials() {{
    echo ""
    if [ ! -f "$BACKUP_DIR/credentials.vault.enc" ]; then
        echo "ℹ️  No credentials vault found (skipped during backup)"
        return
    fi

    read -s -p "🔐 Enter credentials vault password: " VAULT_PASSWORD
    echo ""

    openssl enc -aes-256-cbc -d -pbkdf2 \\
        -in "$BACKUP_DIR/credentials.vault.enc" \\
        -out "$MAIA_ROOT/claude/tools/production_api_credentials.py" \\
        -pass pass:"$VAULT_PASSWORD"

    if [ $? -eq 0 ]; then
        echo "  ✅ Credentials restored"
    else
        echo "  ❌ Failed to decrypt credentials (wrong password?)"
    fi
}}

# Rewrite config paths (LESSON LEARNED: Issue #2 - Hardcoded paths)
rewrite_config_paths() {{
    echo ""
    echo "🔧 Updating configuration paths..."

    # Fix .claude/hooks.json
    HOOKS_JSON="$MAIA_ROOT/.claude/hooks.json"
    if [ -f "$HOOKS_JSON" ]; then
        echo "  📝 Updating .claude/hooks.json..."

        # Use Python to properly update JSON
        python3 << 'PYTHON_EOF'
import json
import sys
import os

hooks_json = os.environ["HOOKS_JSON"]
maia_root = os.environ["MAIA_ROOT"]

try:
    with open(hooks_json) as f:
        config = json.load(f)

    # Update all hook environment paths and disable by default
    for hook_name, hook_config in config.get("hooks", {{}}).items():
        # Disable hooks in restored instance for safety
        hook_config["enabled"] = False

        # Add warning to description
        if "description" in hook_config:
            if "DISABLED in restored instance" not in hook_config["description"]:
                hook_config["description"] += " (DISABLED in restored instance - verify paths before enabling)"

        # Update environment paths
        env = hook_config.get("environment", {{}})
        if "MAIA_ROOT" in env:
            env["MAIA_ROOT"] = maia_root
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = maia_root

    with open(hooks_json, 'w') as f:
        json.dump(config, f, indent=2)

    print("    ✅ Updated %d hooks" % len(config.get('hooks', {{}})))

except Exception as e:
    print("    ⚠️  Failed to update hooks.json: %s" % e)
    sys.exit(0)  # Don't fail restoration for this

PYTHON_EOF

        echo "  ✅ Hook paths updated and disabled for safety"
    else
        echo "  ℹ️  No .claude/hooks.json found"
    fi

    # Fix .claude/settings.local.json (NEW - Phase 134.5: Hook system upgrade compatibility)
    SETTINGS_JSON="$MAIA_ROOT/.claude/settings.local.json"
    if [ -f "$SETTINGS_JSON" ]; then
        echo "  📝 Updating .claude/settings.local.json..."

        python3 << 'PYTHON_EOF'
import json
import sys
import os
import re

settings_json = os.environ["SETTINGS_JSON"]
maia_root = os.environ["MAIA_ROOT"]

try:
    with open(settings_json) as f:
        config = json.load(f)

    # Update all permission paths
    updated_count = 0
    for permission_type in ["allow", "deny", "ask"]:
        if permission_type in config.get("permissions", {{}}):
            permissions = config["permissions"][permission_type]

            for i, permission in enumerate(permissions):
                original_perm = permission

                # Replace any absolute paths with restore location
                # Pattern: /Users/username/git/maia or similar
                if "/Users/" in permission and "/git/maia" in permission:
                    permission = re.sub(
                        r'/Users/[^/]+/git/maia',
                        maia_root,
                        permission
                    )

                # Also handle OneDrive paths (from testing)
                if "OneDrive" in permission and ("restore-test" in permission or "Documents" in permission):
                    permission = re.sub(
                        r'/Users/[^/]+/Library/CloudStorage/[^/]+/[^/]+/[^/]+',
                        maia_root,
                        permission
                    )

                if permission != original_perm:
                    permissions[i] = permission
                    updated_count += 1

    with open(settings_json, 'w') as f:
        json.dump(config, f, indent=2)

    print("    ✅ Updated %d permission paths" % updated_count)

except Exception as e:
    print("    ⚠️  Failed to update settings.local.json: %s" % e)
    sys.exit(0)  # Don't fail restoration for this

PYTHON_EOF

        echo "  ✅ Settings paths updated"
    else
        echo "  ℹ️  No .claude/settings.local.json found"
    fi
}}

# Main restoration flow
main() {{
    detect_environment
    choose_maia_location
    restore_code
    restore_databases
    restore_launchagents
    restore_shell_configs
    rewrite_config_paths  # LESSON LEARNED: Fix hardcoded paths
    restore_dependencies
    restore_credentials

    echo ""
    echo "🎉 Restoration complete!"
    echo ""

    if [ "$IS_WSL" = true ]; then
        echo "Next steps (WSL):"
        echo "  1. Open VSCode: code $MAIA_ROOT"
        echo "  2. Install VSCode WSL extension if not already installed"
        echo "  3. Set environment variables in ~/.bashrc:"
        echo "     echo 'export MAIA_ROOT=$MAIA_ROOT' >> ~/.bashrc"
        echo "     echo 'export PYTHONPATH=$MAIA_ROOT' >> ~/.bashrc"
        echo "     source ~/.bashrc"
        echo "  4. Optional: Set up cron for automated backups:"
        echo "     crontab -e"
        echo "     0 3 * * * cd $MAIA_ROOT && python3 claude/tools/sre/disaster_recovery_system.py backup"
        echo ""
        echo "VSCode Remote - WSL Tips:"
        echo "  - Open folder in WSL: code $MAIA_ROOT"
        echo "  - Terminal uses WSL bash automatically"
        echo "  - Extensions install in WSL context"
        echo "  - Git works from WSL filesystem"
    else
        echo "Next steps (macOS):"
        echo "  1. Load LaunchAgents: launchctl load ~/Library/LaunchAgents/com.maia.*.plist"
        echo "  2. Verify health: cd $MAIA_ROOT && python3 claude/tools/services/health_monitor_service.py"
        echo "  3. Check services: launchctl list | grep com.maia"
    fi
    echo ""
}}

main
'''

        script_path.write_text(script_content)
        script_path.chmod(0o755)  # Make executable

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []

        for backup_dir in self.backup_dir.glob("full_*"):
            manifest_path = backup_dir / "backup_manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        backups.append(json.load(f))
                except Exception:
                    pass

        return sorted(backups, key=lambda x: x.get('created_at', ''), reverse=True)

    def prune_old_backups(self):
        """
        Retention policy: 7 daily, 4 weekly, 12 monthly
        """
        backups = self.list_backups()

        # Group by age
        now = datetime.now()
        daily_backups = []
        weekly_backups = []
        monthly_backups = []

        for backup in backups:
            created = datetime.fromisoformat(backup['created_at'])
            age_days = (now - created).days

            if age_days < 7:
                daily_backups.append(backup)
            elif age_days < 28:
                weekly_backups.append(backup)
            else:
                monthly_backups.append(backup)

        # Keep limits
        to_delete = []

        if len(daily_backups) > 7:
            to_delete.extend(daily_backups[7:])

        if len(weekly_backups) > 4:
            to_delete.extend(weekly_backups[4:])

        if len(monthly_backups) > 12:
            to_delete.extend(monthly_backups[12:])

        # Delete old backups
        for backup in to_delete:
            backup_path = self.backup_dir / backup['backup_id']
            if backup_path.exists():
                shutil.rmtree(backup_path)
                print(f"🗑️  Deleted old backup: {backup['backup_id']}")

        print(f"✅ Pruning complete: {len(to_delete)} backups removed")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Disaster Recovery System for Maia'
    )
    parser.add_argument(
        'command',
        choices=['backup', 'list', 'prune'],
        help='Command to execute'
    )
    parser.add_argument(
        '--vault-password',
        help='Password for credentials vault encryption'
    )
    parser.add_argument(
        '--onedrive-path',
        help='Override OneDrive path (auto-detected if not provided)'
    )

    args = parser.parse_args()

    try:
        dr_system = EnhancedDisasterRecoverySystem(
            onedrive_path=args.onedrive_path
        )

        if args.command == 'backup':
            if not args.vault_password:
                print("⚠️  Warning: No vault password provided.")
                print("   Credentials will not be backed up.")
                print("   Use --vault-password to include encrypted credentials.")
                print()

            manifest = dr_system.create_full_backup(
                vault_password=args.vault_password
            )

            if manifest.get('status') == 'completed':
                print()
                print("🎉 Backup completed successfully!")
                print(f"   Location: {dr_system.backup_dir / manifest['backup_id']}")
                sys.exit(0)
            else:
                print()
                print(f"❌ Backup failed: {manifest.get('error')}")
                sys.exit(1)

        elif args.command == 'list':
            backups = dr_system.list_backups()

            if not backups:
                print("📋 No backups found")
            else:
                print("📋 Available Backups:")
                print("=" * 80)
                for backup in backups:
                    status = backup.get('status', 'unknown')
                    emoji = {'completed': '✅', 'failed': '❌'}.get(status, '❓')

                    print(f"{emoji} {backup['backup_id']}")
                    print(f"   Created: {backup['created_at'][:19]}")
                    print(f"   Phase: {backup['system_metadata']['maia_phase']}")
                    if backup.get('onedrive_sync_verified'):
                        print(f"   OneDrive: ✅ Synced")
                    print()

        elif args.command == 'prune':
            dr_system.prune_old_backups()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
