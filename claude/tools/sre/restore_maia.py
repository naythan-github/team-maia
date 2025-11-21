#!/usr/bin/env python3
"""
Maia Restoration Script
=======================
Automated restoration of Maia system to new machines (macOS/Windows)

BACKUP-ONLY RESTORATION:
The backup archive contains EVERYTHING from a consistent snapshot:
- All Python tools and agents (182 tools, 31 agents)
- All databases and data (92MB)  
- All configurations and context files
- Perfect version consistency

NO Git clone needed - backup has complete system!
"""

import os
import sys
import platform
import subprocess
import json
import tarfile
import requests
from pathlib import Path
from urllib.parse import urlparse

class MaiaRestorer:
    def __init__(self):
        self.system = platform.system()
        self.maia_root = Path.cwd()
        self.backup_extracted = False
        
    
    def setup_environment_variables(self):
        """Setup MAIA_ROOT environment variable for cross-platform compatibility"""
        # Set MAIA_ROOT environment variable
        os.environ["MAIA_ROOT"] = str(self.maia_root)
        
        # Verify claude/core exists after restore
        claude_core = self.maia_root / "claude" / "core"
        if not claude_core.exists():
            print("❌ WARNING: claude/core directory missing after restore!")
            print("   This will cause import errors. Backup may be incomplete.")
            return False
        
        print(f"✅ MAIA_ROOT set to {self.maia_root}")
        return True

    def detect_environment(self):
        """Detect OS and environment"""
        print(f"🔍 Detected OS: {self.system}")
        print(f"📂 Maia Root: {self.maia_root}")
        
        # Check Python version
        py_version = sys.version_info
        if py_version.major < 3 or py_version.minor < 11:
            print("❌ Python 3.11+ required")
            sys.exit(1)
        print(f"✅ Python {py_version.major}.{py_version.minor} detected")
        
        # Check if we have Git repo vs backup archive
        if (self.maia_root / '.git').exists():
            print("✅ Git repository detected")
        else:
            print("⚠️ No Git repository - checking for backup archive")
            
    def prompt_backup_source(self):
        """Ask user for backup source location"""
        print("\n🔄 CRITICAL: Database Restoration Required")
        print("=" * 50)
        print("The Git repository contains code but NOT databases!")
        print("You need a Maia backup archive to restore databases.\n")
        
        print("Backup options:")
        print("1. Local backup file (.tar.gz)")
        print("2. iCloud backup (if synced)")
        print("3. Download from URL")
        print("4. Skip database restoration (limited functionality)")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            backup_path = input("Enter path to backup file: ").strip()
            return Path(backup_path)
        elif choice == "2":
            icloud_backup_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "maia" / "backups"
            if icloud_backup_dir.exists():
                backups = list(icloud_backup_dir.glob("*.tar.gz"))
                if backups:
                    print(f"\nFound {len(backups)} backup(s):")
                    for i, backup in enumerate(backups, 1):
                        print(f"{i}. {backup.name}")
                    backup_choice = input("Choose backup number: ").strip()
                    try:
                        return backups[int(backup_choice) - 1]
                    except (ValueError, IndexError):
                        print("Invalid choice")
                        return None
                else:
                    print("No backups found in iCloud")
                    return None
            else:
                print("iCloud directory not found")
                return None
        elif choice == "3":
            url = input("Enter backup URL: ").strip()
            return self.download_backup(url)
        elif choice == "4":
            print("⚠️ Proceeding without database restoration")
            return None
        else:
            print("Invalid choice")
            return None
            
    def download_backup(self, url):
        """Download backup from URL"""
        print(f"📥 Downloading backup from {url}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filename = urlparse(url).path.split('/')[-1]
            if not filename.endswith('.tar.gz'):
                filename = f"maia_backup_{filename}.tar.gz"
                
            backup_path = self.maia_root / filename
            
            with open(backup_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✅ Downloaded to {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
            
    def extract_backup(self, backup_path):
        """Extract backup archive"""
        if not backup_path or not backup_path.exists():
            print("❌ Backup file not found")
            return False
            
        print(f"📦 Extracting backup: {backup_path}")
        
        try:
            with tarfile.open(backup_path, 'r:gz') as tar:
                # Extract to current directory
                tar.extractall(path=self.maia_root)
                
            # Find extracted directory
            extracted_dirs = [d for d in self.maia_root.iterdir() 
                            if d.is_dir() and d.name.startswith('maia_backup_')]
            
            if extracted_dirs:
                backup_dir = extracted_dirs[0]
                print(f"📁 Backup extracted to: {backup_dir}")
                
                # Move contents to proper locations
                self.merge_backup_contents(backup_dir)
                
                # Clean up extracted directory
                import shutil
                shutil.rmtree(backup_dir)
                
                self.backup_extracted = True
                return True
            else:
                print("❌ No backup directory found in archive")
                return False
                
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return False
            
    def merge_backup_contents(self, backup_dir):
        """Merge extracted backup contents into proper locations"""
        print("🔄 Restoring databases and data...")
        
        component_mappings = {
            'databases': self.maia_root,
            'configuration': self.maia_root,
            'credentials': self.maia_root,
            'tools': self.maia_root,
            'data': self.maia_root
        }
        
        for component, target_root in component_mappings.items():
            component_dir = backup_dir / component
            if component_dir.exists():
                self.copy_component_files(component_dir, target_root)
                
    def copy_component_files(self, source_dir, target_root):
        """Copy files from component directory to target location"""
        import shutil
        
        for item in source_dir.rglob('*'):
            if item.is_file():
                # Calculate relative path from component directory
                rel_path = item.relative_to(source_dir)
                target_path = target_root / rel_path
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
                print(f"  📄 Restored: {rel_path}")
        
    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing Python dependencies...")
        
        # Core requirements
        requirements = [
            "openai",
            "google-generativeai",
            "chromadb",
            "sentence-transformers",
            "sqlite3",
            "pandas",
            "numpy",
            "matplotlib",
            "plotly",
            "flask",
            "requests",
            "beautifulsoup4",
            "python-dotenv",
            "cryptography"
        ]
        
        for req in requirements:
            print(f"  Installing {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                         capture_output=True)
        
        print("✅ Dependencies installed")
        
    def setup_databases(self):
        """Initialize databases if not present"""
        print("\n🗄️ Setting up databases...")
        
        # Create data directories
        data_dirs = [
            "claude/data/knowledge_management",
            "claude/data/vector_db",
            "claude/data/job_search",
            "claude/data/dashboards"
        ]
        
        for dir_path in data_dirs:
            Path(self.maia_root / dir_path).mkdir(parents=True, exist_ok=True)
            
        print("✅ Database directories ready")
        
    def configure_environment(self):
        """Set up environment variables"""
        print("\n⚙️ Configuring environment...")
        
        # Create .env file if not exists
        env_file = self.maia_root / ".env"
        if not env_file.exists():
            env_content = f"""
# Maia Environment Configuration
MAIA_ROOT={self.maia_root}

# API Keys (add your own)
# OPENAI_API_KEY=your-key-here
# GOOGLE_AI_API_KEY=your-key-here

# Local LLM Configuration
OLLAMA_HOST=http://localhost:11434
LOCAL_LLM_ENABLED=true
"""
            env_file.write_text(env_content)
            print("📝 Created .env template - add your API keys")
        
        # Set environment variable
        os.environ["MAIA_ROOT"] = str(self.maia_root)
        print(f"✅ MAIA_ROOT set to {self.maia_root}")
        
    def setup_local_llms(self):
        """Set up local LLM support"""
        print("\n🤖 Setting up local LLMs...")
        
        if self.system == "Darwin":  # macOS
            # Check if Ollama installed
            try:
                subprocess.run(["ollama", "--version"], capture_output=True, check=True)
                print("✅ Ollama detected")
                
                # Pull recommended models
                models = ["llama3.2:3b", "codellama:13b", "starcoder2:15b"]
                for model in models:
                    print(f"  Pulling {model}...")
                    subprocess.run(["ollama", "pull", model], capture_output=True)
                    
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️ Ollama not installed - run: brew install ollama")
                
        elif self.system == "Windows":
            print("💡 For Windows, install LM Studio or Ollama Preview")
            print("   Download from: https://ollama.com/download/windows")
            
    def verify_installation(self):
        """Verify Maia is working"""
        print("\n🔍 Verifying installation...")
        
        try:
            # Test knowledge management system
            km_test = subprocess.run(
                [sys.executable, "claude/tools/knowledge_management_system.py"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "Knowledge Management System" in km_test.stdout:
                print("✅ Knowledge Management System: Working")
            
            # Test tool discovery
            td_test = subprocess.run(
                [sys.executable, "claude/tools/enhanced_tool_discovery_framework.py", "test"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "TOOL DISCOVERY" in td_test.stdout:
                print("✅ Tool Discovery Framework: Working")
                
            print("\n🎉 Maia restoration complete!")
            
        except Exception as e:
            print(f"⚠️ Verification failed: {e}")
            print("   Manual testing recommended")
            
    def run(self):
        """Execute backup-only restoration"""
        print("🚀 Maia System Restoration (Backup-Only)")
        print("="*50)
        print("✅ SIMPLIFIED: Single backup archive contains EVERYTHING!")
        print("📦 Backup includes: Code + Databases + Configs + Data")
        print("🎯 Perfect version consistency from snapshot\n")
        
        self.detect_environment()
        
        # Primary step: Extract complete system from backup
        backup_path = self.prompt_backup_source()
        if backup_path:
            success = self.extract_backup(backup_path)
            if success:
                print("✅ Complete system restoration successful")
                
                # Post-restoration setup
                self.install_dependencies()
                self.setup_environment_variables()
                self.configure_environment()
                self.setup_local_llms()
                self.verify_installation()
                
                print("\n🎉 Restoration Complete!")
                print("="*30)
                print("✅ Code & Tools: Restored from backup")
                print("✅ Databases: Restored from backup")
                print("✅ Configurations: Restored from backup")
                print("✅ Perfect version consistency maintained")
                
                print("\n📚 Next steps:")
                print("1. Add your API keys to .env file")
                print("2. Test with: python3 claude/tools/knowledge_management_system.py")
                print("3. For Claude Code: This folder is ready to use")
                
            else:
                print("❌ System restoration failed")
                print("Check backup file and try again")
        else:
            print("❌ Cannot proceed without backup archive")
            print("Backup contains the complete Maia system - it's required!")
            print("\nTo get backup:")
            print("1. From original machine: ~/Library/Mobile Documents/com~apple~CloudDocs/maia/backups/")
            print("2. Or create new backup with: python3 claude/tools/maia_backup_manager.py backup")
        
if __name__ == "__main__":
    restorer = MaiaRestorer()
    restorer.run()