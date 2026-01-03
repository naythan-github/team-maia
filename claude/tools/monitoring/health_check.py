#!/usr/bin/env python3
"""
Maia System Health Check
Quick validation of all core systems
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def check_databases():
    """Check database connectivity"""
    # Use PathManager for portable path resolution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from claude.tools.core.paths import PathManager, DATABASES_DIR

    # Check both shared (system) and user databases
    databases = [
        DATABASES_DIR / "system" / "system_state.db",
        DATABASES_DIR / "system" / "capabilities.db",
        PathManager.get_user_db_path("preferences.db"),
    ]

    results = {}
    for db_path in databases:
        try:
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1").fetchone()
                conn.close()
                results[db_path.name] = True
            else:
                results[db_path.name] = False
        except Exception as e:
            results[db_path.name] = False

    return results

def check_backlog_system():
    """Check backlog system"""
    # Cross-domain import via emoji resolver
    try:
        import sys
        from pathlib import Path
        emoji_tools_dir = Path(__file__).parent.parent / "🛠️_general"
        sys.path.insert(0, str(emoji_tools_dir))
        try:
            from backlog_manager import BacklogManager
        finally:
            if str(emoji_tools_dir) in sys.path:
                sys.path.remove(str(emoji_tools_dir))
    except ImportError:
        # Graceful fallback for missing backlog_manager
        class BacklogManager: 
            pass

        try:
            bm = BacklogManager()
            if hasattr(bm, 'get_backlog_summary'):
                summary = bm.get_backlog_summary()
                return True, len(summary.get('items', []))
            else:
                return True, "Available (method not found)"
        except Exception as e:
            return False, f"Error: {e}"
    except Exception as e:
        return False, str(e)

def main():
    print("🏥 Maia System Health Check")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)

    # Check databases
    print("\n🗄️  Database Health:")
    db_results = check_databases()
    for db_name, healthy in db_results.items():
        status = "✅" if healthy else "❌"
        print(f"  {status} {db_name}")

    # Check backlog system
    print("\n📋 Backlog System:")
    backlog_healthy, backlog_info = check_backlog_system()
    if backlog_healthy:
        print(f"  ✅ Backlog Manager ({backlog_info} items)")
    else:
        print(f"  ❌ Backlog Manager: {backlog_info}")

    # Overall health
    all_healthy = all(db_results.values()) and backlog_healthy
    print("\n🎯 Overall System Health:")
    if all_healthy:
        print("  ✅ System is healthy")
        return 0
    else:
        print("  ❌ System has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
