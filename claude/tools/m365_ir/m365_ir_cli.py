#!/usr/bin/env python3
"""
M365 IR CLI - Automated M365 Incident Response Analysis

End-to-end pipeline for M365 log analysis:
- Ingest multiple exports
- Auto-detect date format
- Calculate user baselines
- Detect anomalies
- Build attack timeline
- Extract IOCs
- Map to MITRE ATT&CK
- Generate PIR report

Usage:
    python3 m365_ir_cli.py analyze /path/to/exports --customer "CustomerName"
    python3 m365_ir_cli.py analyze /export1 /export2 /export3 --customer "Oculus"

Author: Maia System
Created: 2025-12-18 (Phase 225)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.m365_ir.m365_log_parser import M365LogParser, LogType
from claude.tools.m365_ir.user_baseliner import UserBaseliner
from claude.tools.m365_ir.anomaly_detector import AnomalyDetector
from claude.tools.m365_ir.timeline_builder import TimelineBuilder
from claude.tools.m365_ir.ioc_extractor import IOCExtractor, MitreMapper
from claude.tools.m365_ir.remediation_detector import RemediationDetector, IncidentTimeline


class M365IRAnalyzer:
    """
    Complete M365 Incident Response Analyzer.

    Orchestrates all analysis components into a single pipeline.
    """

    def __init__(self, customer: str = "Customer", home_country: str = "AU"):
        self.customer = customer
        self.home_country = home_country

        # Initialize components
        self.parser = None
        self.baseliner = UserBaseliner()
        self.anomaly_detector = AnomalyDetector(home_country=home_country)
        self.timeline_builder = TimelineBuilder(home_country=home_country)
        self.ioc_extractor = IOCExtractor()
        self.mitre_mapper = MitreMapper()
        self.remediation_detector = RemediationDetector()

        # Results storage
        self.signin_entries = []
        self.audit_entries = []
        self.mailbox_entries = []
        self.legacy_entries = []
        self.baselines = {}
        self.anomalies = []
        self.timeline = []
        self.iocs = []
        self.mitre_techniques = []
        self.incident_timeline: IncidentTimeline = None

    def ingest(self, export_paths: List[Path]) -> Dict[str, int]:
        """
        Ingest log exports.

        Args:
            export_paths: List of export directory paths

        Returns:
            Dict with counts of ingested entries
        """
        print(f"\n{'='*60}")
        print(f"M365 IR ANALYZER - {self.customer}")
        print(f"{'='*60}")

        # Initialize parser with auto-detected date format
        self.parser = M365LogParser.from_export(export_paths[0])
        print(f"\n[1/7] Parsing logs...")
        print(f"  Date format detected: {self.parser.date_format}")

        # Merge sign-in logs
        self.signin_entries = self.parser.merge_exports(export_paths, LogType.SIGNIN)
        print(f"  Sign-in logs: {len(self.signin_entries)} entries")

        # Load other log types
        for export in export_paths:
            discovered = self.parser.discover_log_files(export)

            if LogType.AUDIT in discovered:
                self.audit_entries.extend(self.parser.parse_audit_logs(discovered[LogType.AUDIT]))

            if LogType.MAILBOX_AUDIT in discovered:
                self.mailbox_entries.extend(self.parser.parse_mailbox_audit(discovered[LogType.MAILBOX_AUDIT]))

            if LogType.LEGACY_AUTH in discovered:
                self.legacy_entries.extend(self.parser.parse_legacy_auth(discovered[LogType.LEGACY_AUTH]))

        print(f"  Audit logs: {len(self.audit_entries)} entries")
        print(f"  Mailbox audit: {len(self.mailbox_entries)} entries")
        print(f"  Legacy auth: {len(self.legacy_entries)} entries")

        return {
            "signin": len(self.signin_entries),
            "audit": len(self.audit_entries),
            "mailbox": len(self.mailbox_entries),
            "legacy_auth": len(self.legacy_entries),
        }

    def analyze(self) -> Dict[str, Any]:
        """
        Run full analysis pipeline.

        Returns:
            Analysis results
        """
        results = {}

        # Step 2: Detect remediation events (NEW - Phase 225.1)
        print(f"\n[2/7] Detecting remediation events...")
        self.incident_timeline = self.remediation_detector.build_incident_timeline(
            signin_entries=self.signin_entries,
            audit_entries=self.audit_entries,
            home_country=self.home_country,
        )
        if self.incident_timeline.attack_start_date:
            print(f"  Attack start: {self.incident_timeline.attack_start_date} ({self.incident_timeline.attack_start_user} from {self.incident_timeline.attack_start_country})")
        if self.incident_timeline.detection_date:
            print(f"  Remediation date: {self.incident_timeline.detection_date}")
        if self.incident_timeline.dwell_time_days is not None:
            print(f"  Dwell time: {self.incident_timeline.dwell_time_days} days")
        if self.incident_timeline.remediation_summary:
            rs = self.incident_timeline.remediation_summary
            print(f"  Users remediated: {rs.users_remediated}")
            print(f"  Remediation events: {rs.total_events} ({rs.by_type})")
        results["incident_timeline"] = self.remediation_detector.get_summary(self.incident_timeline)

        # Step 3: Calculate user baselines
        print(f"\n[3/7] Calculating user baselines...")
        self.baselines = self.baseliner.calculate_all_baselines(self.signin_entries)
        baseline_summary = self.baseliner.get_summary(self.baselines)
        print(f"  Total users: {baseline_summary['total_users']}")
        print(f"  AU-based: {baseline_summary['au_based']}")
        print(f"  US-based: {baseline_summary['us_based']} (potential false positives)")
        print(f"  Suspicious: {baseline_summary['suspicious']}")
        results["baselines"] = baseline_summary

        # Step 4: Detect anomalies
        print(f"\n[4/7] Detecting anomalies...")
        self.anomalies = self.anomaly_detector.detect_all(
            signin_entries=self.signin_entries,
            legacy_auth_entries=self.legacy_entries,
        )
        anomaly_summary = self.anomaly_detector.get_summary(self.anomalies)
        print(f"  Total anomalies: {anomaly_summary['total_anomalies']}")
        print(f"  By type: {anomaly_summary['by_type']}")
        print(f"  Users affected: {anomaly_summary['unique_users_affected']}")
        results["anomalies"] = anomaly_summary

        # Step 5: Build timeline
        print(f"\n[5/7] Building attack timeline...")
        self.timeline = self.timeline_builder.build(
            signin_entries=self.signin_entries,
            audit_entries=self.audit_entries,
            mailbox_entries=self.mailbox_entries,
        )
        timeline_summary = self.timeline_builder.get_summary(self.timeline)
        print(f"  Total events: {timeline_summary['total_events']}")
        print(f"  Date range: {timeline_summary['date_range']}")
        print(f"  Phases detected: {timeline_summary.get('phases_detected', [])}")
        results["timeline"] = timeline_summary

        # Step 6: Extract IOCs
        print(f"\n[6/7] Extracting IOCs...")
        self.iocs = self.ioc_extractor.extract(
            signin_entries=self.signin_entries,
            legacy_entries=self.legacy_entries,
        )
        ioc_summary = self.ioc_extractor.get_summary(self.iocs)
        print(f"  Total IOCs: {ioc_summary['total_iocs']}")
        print(f"  Unique IPs: {ioc_summary['unique_ips']}")
        print(f"  Unique countries: {ioc_summary['unique_countries']}")
        print(f"  Top countries: {ioc_summary['top_countries'][:5]}")
        results["iocs"] = ioc_summary

        # Step 7: Map to MITRE ATT&CK
        print(f"\n[7/7] Mapping to MITRE ATT&CK...")
        events_for_mitre = []
        for anomaly in self.anomalies:
            events_for_mitre.append((anomaly.description, "anomaly"))
        for event in self.timeline:
            events_for_mitre.append((event.action, event.source_type))

        self.mitre_techniques = self.mitre_mapper.get_techniques_for_events(events_for_mitre)
        print(f"  Techniques identified: {len(self.mitre_techniques)}")
        for t in self.mitre_techniques:
            print(f"    - {t.technique_id}: {t.name} ({t.tactic})")
        results["mitre"] = [{"id": t.technique_id, "name": t.name, "tactic": t.tactic} for t in self.mitre_techniques]

        return results

    def get_compromised_users(self) -> List[str]:
        """Get list of likely compromised users."""
        # Users with anomalies who are not US-based (US users are false positives)
        us_users = {u for u, b in self.baselines.items() if b.primary_country == "US"}
        anomaly_users = {a.user_principal_name for a in self.anomalies}

        compromised = []
        for user in anomaly_users:
            # Skip US-based users (false positives)
            if user in us_users:
                continue
            if user in self.baselines:
                baseline = self.baselines[user]
                # Compromised if: home country-based with foreign anomalies OR suspicious baseline
                if baseline.primary_country == self.home_country or baseline.is_suspicious:
                    compromised.append(user)

        return compromised

    def get_false_positives(self) -> List[str]:
        """Get list of likely false positives (US-based users)."""
        return [
            user for user, baseline in self.baselines.items()
            if baseline.primary_country == "US"
        ]

    def print_summary(self) -> None:
        """Print executive summary."""
        print(f"\n{'='*60}")
        print("EXECUTIVE SUMMARY")
        print(f"{'='*60}")

        compromised = self.get_compromised_users()
        false_positives = self.get_false_positives()
        suspicious = [u for u, b in self.baselines.items() if b.is_suspicious]

        print(f"\nCustomer: {self.customer}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Incident Timeline (Phase 225.1)
        if self.incident_timeline:
            print(f"\nIncident Timeline:")
            if self.incident_timeline.attack_start_date:
                print(f"  Attack Start: {self.incident_timeline.attack_start_date} ({self.incident_timeline.attack_start_user} from {self.incident_timeline.attack_start_country})")
            if self.incident_timeline.detection_date:
                print(f"  Remediation Date: {self.incident_timeline.detection_date}")
            if self.incident_timeline.dwell_time_days is not None:
                print(f"  Dwell Time: {self.incident_timeline.dwell_time_days} days")

        print(f"\nFindings:")
        print(f"  Compromised accounts: {len(compromised)}")
        for user in compromised[:10]:
            b = self.baselines.get(user)
            if b:
                print(f"    - {user} (baseline: {b.primary_country}, confidence: {b.confidence:.0%})")

        print(f"\n  False positives (US-based): {len(false_positives)}")
        for user in false_positives:
            print(f"    - {user}")

        print(f"\n  Suspicious (no clear baseline): {len(suspicious)}")
        for user in suspicious[:5]:
            b = self.baselines.get(user)
            if b:
                print(f"    - {user} ({b.primary_country}, {b.confidence:.0%})")

        print(f"\nAttack Summary:")
        if self.timeline:
            sorted_timeline = self.timeline_builder.sort_chronologically(self.timeline) if hasattr(self.timeline_builder, 'sort_chronologically') else self.timeline
            print(f"  First activity: {sorted_timeline[0].timestamp.strftime('%Y-%m-%d %H:%M') if sorted_timeline else 'N/A'}")
            print(f"  Last activity: {sorted_timeline[-1].timestamp.strftime('%Y-%m-%d %H:%M') if sorted_timeline else 'N/A'}")

        print(f"\nMITRE ATT&CK Techniques:")
        for t in self.mitre_techniques:
            print(f"  - {t.technique_id}: {t.name}")

    def export_results(self, output_dir: Path) -> None:
        """Export all results to output directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export IOCs
        self.ioc_extractor.export_csv(self.iocs, output_dir / "iocs.csv")
        self.ioc_extractor.export_json(self.iocs, output_dir / "iocs.json")
        print(f"\nExported IOCs to {output_dir / 'iocs.csv'}")

        # Export timeline
        timeline_md = self.timeline_builder.format_markdown(self.timeline[:100])  # Top 100 events
        (output_dir / "timeline.md").write_text(timeline_md)
        print(f"Exported timeline to {output_dir / 'timeline.md'}")

        # Export summary JSON
        summary = {
            "customer": self.customer,
            "analysis_date": datetime.now().isoformat(),
            "incident_timeline": self.remediation_detector.get_summary(self.incident_timeline) if self.incident_timeline else None,
            "compromised_users": self.get_compromised_users(),
            "false_positives": self.get_false_positives(),
            "mitre_techniques": [{"id": t.technique_id, "name": t.name, "tactic": t.tactic} for t in self.mitre_techniques],
            "ioc_summary": self.ioc_extractor.get_summary(self.iocs),
            "anomaly_summary": self.anomaly_detector.get_summary(self.anomalies),
        }
        (output_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
        print(f"Exported summary to {output_dir / 'analysis_summary.json'}")


def main():
    parser = argparse.ArgumentParser(
        description="M365 Incident Response Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze /path/to/export --customer "Acme Corp"
  %(prog)s analyze /export1 /export2 /export3 --customer "Oculus" --output ./results
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze M365 exports")
    analyze_parser.add_argument("exports", nargs="+", type=Path, help="Export directories")
    analyze_parser.add_argument("--customer", "-c", required=True, help="Customer name")
    analyze_parser.add_argument("--home-country", default="AU", help="Home country code (default: AU)")
    analyze_parser.add_argument("--output", "-o", type=Path, help="Output directory for results")

    args = parser.parse_args()

    if args.command == "analyze":
        analyzer = M365IRAnalyzer(
            customer=args.customer,
            home_country=args.home_country,
        )

        # Ingest
        analyzer.ingest(args.exports)

        # Analyze
        analyzer.analyze()

        # Print summary
        analyzer.print_summary()

        # Export if output specified
        if args.output:
            analyzer.export_results(args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
