#!/usr/bin/env python3
"""
RAG System Health Monitor - SRE Observability Tool

Monitors health and status of all Maia RAG systems providing observability
into data freshness, storage usage, query performance, and error rates.

SRE Pattern: RAG System Observability - Real-time health monitoring with
storage and performance metrics tracking.

Usage:
    python3 claude/tools/sre/rag_system_health_monitor.py --dashboard
    python3 claude/tools/sre/rag_system_health_monitor.py --summary
    python3 claude/tools/sre/rag_system_health_monitor.py --detailed
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class RAGSystemHealthMonitor:
    """Health monitoring for all RAG systems"""

    def __init__(self):
        self.home = Path.home()
        self.maia_data = self.home / ".maia"
        self.rag_systems = self._discover_rag_systems()

    def _discover_rag_systems(self) -> List[Dict]:
        """Discover all RAG system storage locations"""
        systems = []

        # Known RAG system patterns
        rag_patterns = [
            ("conversation_rag", "Conversation RAG", "conversation_rag_ollama.py"),
            ("email_rag_ollama", "Email RAG (Ollama)", "email_rag_ollama.py"),
            ("email_rag_enhanced", "Email RAG (Enhanced)", "email_rag_enhanced.py"),
            ("email_rag", "Email RAG (Legacy)", "email_rag_system.py"),
            ("system_state_rag", "System State RAG", "system_state_rag_ollama.py"),
            ("meeting_rag_ollama", "Meeting RAG", "integrated_meeting_intelligence.py"),
        ]

        for dir_name, display_name, tool_name in rag_patterns:
            rag_path = self.maia_data / dir_name
            if rag_path.exists():
                systems.append({
                    'name': display_name,
                    'path': rag_path,
                    'tool': tool_name,
                    'directory': dir_name
                })

        return systems

    def get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes"""
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total

    def get_chromadb_stats(self, rag_path: Path) -> Optional[Dict]:
        """Get ChromaDB collection statistics"""
        try:
            # ChromaDB stores data in chroma.sqlite3
            db_path = rag_path / "chroma.sqlite3"
            if not db_path.exists():
                return None

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get document count from embeddings table
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            doc_count = cursor.fetchone()[0]

            # Get collection info
            cursor.execute("SELECT name FROM collections")
            collections = [row[0] for row in cursor.fetchall()]

            conn.close()

            return {
                'document_count': doc_count,
                'collections': collections,
                'collection_count': len(collections)
            }
        except Exception as e:
            return {'error': str(e)}

    def get_last_modified(self, path: Path) -> Optional[datetime]:
        """Get most recent modification time in directory"""
        try:
            latest = None
            for item in path.rglob('*'):
                if item.is_file():
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if latest is None or mtime > latest:
                        latest = mtime
            return latest
        except Exception:
            return None

    def analyze_rag_system(self, system: Dict) -> Dict:
        """Analyze health of a single RAG system"""
        path = system['path']

        analysis = {
            'name': system['name'],
            'status': 'UNKNOWN',
            'health': 'UNKNOWN',
            'path': str(path),
            'tool': system['tool'],
            'directory': system['directory']
        }

        # Check if directory exists
        if not path.exists():
            analysis['status'] = 'NOT_FOUND'
            analysis['health'] = 'MISSING'
            return analysis

        # Get storage size
        size_bytes = self.get_directory_size(path)
        size_mb = size_bytes / (1024 * 1024)
        analysis['storage_size_mb'] = round(size_mb, 2)

        # Get ChromaDB stats
        chroma_stats = self.get_chromadb_stats(path)
        if chroma_stats:
            analysis['chromadb_stats'] = chroma_stats
            if 'error' not in chroma_stats:
                analysis['document_count'] = chroma_stats['document_count']
                analysis['collections'] = chroma_stats['collections']

        # Get last modified time
        last_modified = self.get_last_modified(path)
        if last_modified:
            analysis['last_modified'] = last_modified.isoformat()
            age_hours = (datetime.now() - last_modified).total_seconds() / 3600
            analysis['age_hours'] = round(age_hours, 1)

            # Determine freshness health
            if age_hours < 24:
                analysis['freshness'] = 'FRESH'
            elif age_hours < 72:
                analysis['freshness'] = 'RECENT'
            elif age_hours < 168:  # 1 week
                analysis['freshness'] = 'STALE'
            else:
                analysis['freshness'] = 'VERY_STALE'

        # Overall health assessment
        if analysis.get('document_count', 0) > 0:
            analysis['status'] = 'OPERATIONAL'
            if analysis.get('freshness') in ['FRESH', 'RECENT']:
                analysis['health'] = 'HEALTHY'
            elif analysis.get('freshness') == 'STALE':
                analysis['health'] = 'DEGRADED'
            else:
                analysis['health'] = 'CRITICAL'
        elif size_mb > 0.1:
            analysis['status'] = 'INITIALIZED'
            analysis['health'] = 'UNKNOWN'
        else:
            analysis['status'] = 'EMPTY'
            analysis['health'] = 'NOT_CONFIGURED'

        return analysis

    def generate_health_report(self) -> Dict:
        """Generate comprehensive RAG health report"""
        print("🔍 Analyzing RAG Systems...\n")

        analyses = []
        for system in self.rag_systems:
            analysis = self.analyze_rag_system(system)
            analyses.append(analysis)

        # Calculate overall statistics
        total = len(analyses)
        healthy = len([a for a in analyses if a['health'] == 'HEALTHY'])
        degraded = len([a for a in analyses if a['health'] == 'DEGRADED'])
        critical = len([a for a in analyses if a['health'] == 'CRITICAL'])
        unknown = len([a for a in analyses if a['health'] == 'UNKNOWN'])
        missing = len([a for a in analyses if a['health'] == 'MISSING'])
        not_configured = len([a for a in analyses if a['health'] == 'NOT_CONFIGURED'])

        total_docs = sum(a.get('document_count', 0) for a in analyses)
        total_storage_mb = sum(a.get('storage_size_mb', 0) for a in analyses)

        # Calculate health score
        if total > 0:
            health_score = (healthy / total) * 100
        else:
            health_score = 0

        overall_health = 'HEALTHY' if health_score >= 75 else \
                        'DEGRADED' if health_score >= 50 else \
                        'CRITICAL' if health_score >= 25 else 'FAILED'

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_rag_systems': total,
                'healthy': healthy,
                'degraded': degraded,
                'critical': critical,
                'unknown': unknown,
                'missing': missing,
                'not_configured': not_configured,
                'health_score': round(health_score, 1),
                'overall_health': overall_health,
                'total_documents': total_docs,
                'total_storage_mb': round(total_storage_mb, 2)
            },
            'systems': analyses
        }

        return report

    def print_dashboard(self, report: Dict, detailed: bool = False):
        """Print RAG system health dashboard"""
        print("="*70)
        print("📊 RAG SYSTEM HEALTH DASHBOARD")
        print("="*70)

        summary = report['summary']

        # Overall health status
        health = summary['overall_health']
        if health == 'HEALTHY':
            status_icon = "✅"
        elif health == 'DEGRADED':
            status_icon = "⚠️"
        elif health == 'CRITICAL':
            status_icon = "🔴"
        else:
            status_icon = "🚨"

        print(f"\n{status_icon} Overall Health: {health}")
        print(f"📈 Health Score: {summary['health_score']}%\n")

        print(f"📊 Summary:")
        print(f"   Total RAG Systems: {summary['total_rag_systems']}")
        print(f"   Healthy: {summary['healthy']} ✅")
        print(f"   Degraded: {summary['degraded']} ⚠️")
        print(f"   Critical: {summary['critical']} 🔴")
        print(f"   Unknown: {summary['unknown']} ❓")
        print(f"   Not Configured: {summary['not_configured']} 💤")
        print(f"   Total Documents: {summary['total_documents']:,}")
        print(f"   Total Storage: {summary['total_storage_mb']:.2f} MB")

        # System details
        systems = report['systems']
        print(f"\n📋 RAG System Status:")
        print(f"   {'System Name':<30} {'Health':<12} {'Docs':<8} {'Storage':<10} {'Freshness'}")
        print(f"   {'-'*30} {'-'*12} {'-'*8} {'-'*10} {'-'*10}")

        for system in systems:
            name = system['name'][:29]
            health = system['health']
            docs = system.get('document_count', 0)
            storage = f"{system.get('storage_size_mb', 0):.1f} MB"
            freshness = system.get('freshness', 'N/A')

            # Health icon
            if health == 'HEALTHY':
                health_icon = "✅"
            elif health == 'DEGRADED':
                health_icon = "⚠️"
            elif health == 'CRITICAL':
                health_icon = "🔴"
            elif health == 'NOT_CONFIGURED':
                health_icon = "💤"
            else:
                health_icon = "❓"

            print(f"   {name:<30} {health_icon} {health:<10} {docs:<8} {storage:<10} {freshness}")

        print("\n" + "="*70)

        # Detailed information
        if detailed:
            print("\n🔍 Detailed Analysis:")
            for system in systems:
                print(f"\n📦 {system['name']}")
                print(f"   Path: {system['path']}")
                print(f"   Tool: {system['tool']}")
                print(f"   Status: {system['status']}")
                if 'last_modified' in system:
                    print(f"   Last Modified: {system['last_modified']}")
                    print(f"   Age: {system['age_hours']:.1f} hours")
                if 'collections' in system:
                    print(f"   Collections: {', '.join(system['collections'])}")

        # Recommendations
        if summary['degraded'] > 0 or summary['critical'] > 0:
            print(f"\n⚠️  RECOMMENDATIONS:")
            for system in systems:
                if system['health'] == 'CRITICAL':
                    print(f"   🚨 {system['name']}: Data very stale ({system.get('age_hours', 0):.1f}h) - re-index needed")
                elif system['health'] == 'DEGRADED':
                    print(f"   ⚠️  {system['name']}: Data stale ({system.get('age_hours', 0):.1f}h) - consider refresh")

        print("="*70 + "\n")

    def print_summary(self, report: Dict):
        """Print brief summary"""
        summary = report['summary']
        print(f"RAG Systems: {summary['total_rag_systems']}")
        print(f"Health Score: {summary['health_score']}%")
        print(f"Healthy: {summary['healthy']}, Degraded: {summary['degraded']}, Critical: {summary['critical']}")
        print(f"Total Documents: {summary['total_documents']:,}")
        print(f"Total Storage: {summary['total_storage_mb']:.2f} MB")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG System Health Monitor - SRE Observability Tool"
    )
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Show health dashboard'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show brief summary'
    )
    parser.add_argument(
        '--json',
        type=str,
        help='Save report as JSON to specified file'
    )

    args = parser.parse_args()

    if not (args.dashboard or args.summary or args.json):
        parser.print_help()
        return 1

    monitor = RAGSystemHealthMonitor()
    report = monitor.generate_health_report()

    if args.dashboard:
        monitor.print_dashboard(report, detailed=args.detailed)
    elif args.summary:
        monitor.print_summary(report)

    if args.json:
        json_path = Path(args.json)
        json_path.write_text(json.dumps(report, indent=2))
        print(f"📄 Report saved to: {json_path}")

    # Exit code based on health
    if report['summary']['overall_health'] in ['CRITICAL', 'FAILED']:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
