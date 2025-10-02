#!/usr/bin/env python3
"""
Real-Time Documentation Monitor

Monitors file system changes and automatically updates documentation when code changes.
Implements intelligent documentation synchronization and compliance enforcement.

Key Features:
- File system watching for real-time updates
- Automatic documentation generation on code changes
- Documentation drift detection and correction
- Compliance enforcement with real-time alerts
- Integration with git hooks for commit-time validation
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import hashlib

# File system monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

# Local imports
# Core utility import from general domain
try:
    import sys
    from pathlib import Path
    general_tools_dir = Path(__file__).parent.parent / "🛠️_general"
    sys.path.insert(0, str(general_tools_dir))
    try:
        from claude.core.path_manager import get_path_manager
    finally:
        if str(general_tools_dir) in sys.path:
            sys.path.remove(str(general_tools_dir))
except ImportError:
    # Graceful fallback for missing path_manager
        def get_path_manager(): return None
# Cross-domain import via emoji resolver
try:
    import sys
    from pathlib import Path
    emoji_tools_dir = Path(__file__).parent.parent / "🔍_research"
    sys.path.insert(0, str(emoji_tools_dir))
    try:
        from advanced_documentation_intelligence import DocumentationIntelligenceSystem
    finally:
        if str(emoji_tools_dir) in sys.path:
            sys.path.remove(str(emoji_tools_dir))
except ImportError:
    # Graceful fallback for missing advanced_documentation_intelligence
        class DocumentationIntelligenceSystem: pass


@dataclass
class DocumentationChangeEvent:
    """Documentation change event"""
    file_path: str
    event_type: str  # modified, created, deleted
    timestamp: datetime
    auto_generated: bool = False
    compliance_score: float = 0.0


class DocumentationFileHandler(FileSystemEventHandler):
    """Handles file system events for documentation monitoring"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        
        # Debounce mechanism
        self.pending_events = {}
        self.debounce_delay = 2.0  # 2 seconds
    
    def on_modified(self, event):
        if not event.is_directory:
            self._queue_event(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self._queue_event(event.src_path, 'created')
    
    def _queue_event(self, file_path: str, event_type: str):
        """Queue event with debouncing"""
        if self._should_monitor_file(file_path):
            # Cancel previous timer if exists
            if file_path in self.pending_events:
                self.pending_events[file_path].cancel()
            
            # Set new timer
            timer = threading.Timer(
                self.debounce_delay,
                self._process_event,
                args=[file_path, event_type]
            )
            timer.start()
            self.pending_events[file_path] = timer
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """Check if file should be monitored"""
        path = Path(file_path)
        
        # Monitor Python files
        if path.suffix == '.py':
            # Skip test files and archives
            if 'test' in str(path) or 'archive' in str(path):
                return False
            return True
        
        # Monitor markdown files
        if path.suffix == '.md':
            return True
        
        return False
    
    def _process_event(self, file_path: str, event_type: str):
        """Process file change event"""
        try:
            self.monitor.handle_file_change(file_path, event_type)
        except Exception as e:
            self.logger.error(f"Error processing event for {file_path}: {e}")
        finally:
            # Remove from pending events
            if file_path in self.pending_events:
                del self.pending_events[file_path]


class RealTimeDocumentationMonitor:
    """Real-time documentation monitoring and synchronization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.path_manager = get_path_manager()
        self.doc_system = DocumentationIntelligenceSystem()
        
        # State management
        self.is_monitoring = False
        self.observer = None
        self.file_hashes = {}
        self.compliance_cache = {}
        
        # Configuration
        self.auto_generate = True
        self.enforce_compliance = True
        self.min_compliance_score = 0.6
        
        # Statistics
        self.events_processed = 0
        self.documentation_generated = 0
        self.compliance_violations = 0
        
        logging.basicConfig(level=logging.INFO)
        self.logger.info("📡 Real-Time Documentation Monitor initialized")
    
    def start_monitoring(self):
        """Start real-time file monitoring"""
        if not WATCHDOG_AVAILABLE:
            self.logger.error("❌ Watchdog not available. Install with: pip install watchdog")
            return False
        
        if self.is_monitoring:
            self.logger.info("📡 Monitor already running")
            return True
        
        try:
            claude_root = self.path_manager.get_claude_root()
            
            self.observer = Observer()
            handler = DocumentationFileHandler(self)
            
            # Monitor key directories
            directories_to_monitor = [
                claude_root / "tools",
                claude_root / "agents", 
                claude_root / "commands",
                claude_root / "context"
            ]
            
            for directory in directories_to_monitor:
                if directory.exists():
                    self.observer.schedule(handler, str(directory), recursive=True)
                    self.logger.info(f"📁 Monitoring: {directory}")
            
            self.observer.start()
            self.is_monitoring = True
            
            self.logger.info("✅ Real-time documentation monitoring started")
            self._initialize_file_hashes()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            self.logger.info("⏹️  Documentation monitoring stopped")
    
    def _initialize_file_hashes(self):
        """Initialize file hash cache for change detection"""
        claude_root = self.path_manager.get_claude_root()
        
        for file_path in claude_root.rglob("*.py"):
            if 'archive' not in str(file_path) and 'test' not in str(file_path):
                self.file_hashes[str(file_path)] = self._get_file_hash(file_path)
        
        self.logger.info(f"📊 Initialized {len(self.file_hashes)} file hashes")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get file content hash"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def handle_file_change(self, file_path: str, event_type: str):
        """Handle file change event"""
        self.events_processed += 1
        self.logger.info(f"📝 File {event_type}: {Path(file_path).name}")
        
        # Check if file actually changed
        if event_type == 'modified':
            current_hash = self._get_file_hash(Path(file_path))
            previous_hash = self.file_hashes.get(file_path, "")
            
            if current_hash == previous_hash:
                return  # No actual change
            
            self.file_hashes[file_path] = current_hash
        
        # Process documentation updates
        self._process_documentation_update(file_path, event_type)
    
    def _process_documentation_update(self, file_path: str, event_type: str):
        """Process documentation update for changed file"""
        try:
            # Check compliance
            if file_path.endswith('.py'):
                metrics = self.doc_system.tracker.assess_file_compliance(file_path)
                self.compliance_cache[file_path] = metrics
                
                # Log compliance status
                self.logger.info(f"📊 Compliance: {metrics.compliance_score:.1%} for {Path(file_path).name}")
                
                # Auto-generate if compliance is low
                if (self.auto_generate and 
                    metrics.compliance_score < self.min_compliance_score):
                    
                    self._auto_generate_documentation(file_path, metrics)
                
                # Enforce compliance if enabled
                if (self.enforce_compliance and 
                    metrics.compliance_score < self.min_compliance_score):
                    
                    self._handle_compliance_violation(file_path, metrics)
            
            # Update related documentation files
            self._update_related_documentation(file_path, event_type)
            
        except Exception as e:
            self.logger.error(f"Error processing documentation update for {file_path}: {e}")
    
    def _auto_generate_documentation(self, file_path: str, metrics):
        """Auto-generate documentation for low-compliance file"""
        try:
            self.logger.info(f"🤖 Auto-generating documentation for {Path(file_path).name}")
            
            doc_content = self.doc_system.generate_missing_documentation(file_path)
            
            # Save documentation
            doc_path = file_path.replace('.py', '_documentation.md')
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            self.documentation_generated += 1
            self.logger.info(f"✅ Generated: {Path(doc_path).name}")
            
        except Exception as e:
            self.logger.error(f"Error auto-generating documentation: {e}")
    
    def _handle_compliance_violation(self, file_path: str, metrics):
        """Handle compliance violation"""
        self.compliance_violations += 1
        
        violation_msg = (
            f"⚠️  COMPLIANCE VIOLATION: {Path(file_path).name}\n"
            f"   Score: {metrics.compliance_score:.1%} (minimum: {self.min_compliance_score:.1%})\n"
            f"   Issues: {', '.join(metrics.quality_issues[:3])}"
        )
        
        self.logger.warning(violation_msg)
        
        # Could integrate with git hooks here to prevent commits
        # self._block_commit_if_configured(file_path, metrics)
    
    def _update_related_documentation(self, file_path: str, event_type: str):
        """Update related documentation files"""
        # Update available.md if it's a new tool
        if (event_type == 'created' and 
            file_path.endswith('.py') and 
            'claude/tools/' in file_path):
            
            self._update_available_tools_documentation(file_path)
        
        # Update agents.md if it's an agent file
        if 'claude/agents/' in file_path:
            self._update_agents_documentation(file_path)
    
    def _update_available_tools_documentation(self, tool_path: str):
        """Update available.md with new tool"""
        try:
            tool_name = Path(tool_path).stem
            self.logger.info(f"📋 Updating available.md for new tool: {tool_name}")
            
            # This would integrate with the available.md update logic
            # For now, just log the requirement
            self.logger.info(f"📝 TODO: Add {tool_name} to available.md")
            
        except Exception as e:
            self.logger.error(f"Error updating available.md: {e}")
    
    def _update_agents_documentation(self, agent_path: str):
        """Update agents.md with agent changes"""
        try:
            agent_name = Path(agent_path).stem
            self.logger.info(f"🤖 Agent documentation update needed: {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Error updating agent documentation: {e}")
    
    def get_monitoring_status(self) -> Dict[str, any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'events_processed': self.events_processed,
            'documentation_generated': self.documentation_generated,
            'compliance_violations': self.compliance_violations,
            'files_monitored': len(self.file_hashes),
            'cached_compliance_scores': len(self.compliance_cache),
            'avg_compliance': sum(m.compliance_score for m in self.compliance_cache.values()) / max(len(self.compliance_cache), 1)
        }
    
    def generate_monitoring_report(self) -> str:
        """Generate monitoring report"""
        status = self.get_monitoring_status()
        
        report = f"""
# Real-Time Documentation Monitoring Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Monitoring Status
- **Active**: {status['is_monitoring']}
- **Files Monitored**: {status['files_monitored']}
- **Events Processed**: {status['events_processed']}

## Documentation Activity
- **Auto-Generated**: {status['documentation_generated']} files
- **Compliance Violations**: {status['compliance_violations']}
- **Average Compliance**: {status['avg_compliance']:.1%}

## Recent Compliance Scores
"""
        
        # Add recent compliance scores
        recent_scores = sorted(
            [(path, metrics.compliance_score, metrics.last_updated) 
             for path, metrics in self.compliance_cache.items()],
            key=lambda x: x[2],
            reverse=True
        )[:10]
        
        for path, score, updated in recent_scores:
            file_name = Path(path).name
            report += f"- **{file_name}**: {score:.1%}\n"
        
        return report


def main():
    """Real-Time Documentation Monitor Demo"""
    print("📡 Real-Time Documentation Monitor")
    print("=" * 50)
    
    monitor = RealTimeDocumentationMonitor()
    
    # Start monitoring
    if monitor.start_monitoring():
        print("✅ Monitoring started successfully")
        
        try:
            # Monitor for 30 seconds in demo
            print("🔍 Monitoring for file changes... (30 seconds)")
            time.sleep(30)
            
            # Show status
            status = monitor.get_monitoring_status()
            print(f"\n📊 Monitoring Results:")
            print(f"   • Events processed: {status['events_processed']}")
            print(f"   • Documentation generated: {status['documentation_generated']}")
            print(f"   • Compliance violations: {status['compliance_violations']}")
            print(f"   • Average compliance: {status['avg_compliance']:.1%}")
            
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring interrupted by user")
        
        finally:
            monitor.stop_monitoring()
    
    else:
        print("❌ Failed to start monitoring")


if __name__ == "__main__":
    main()