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

Phase 226 additions:
- import: Import logs into per-case SQLite database (supports zip files directly)
- query: Query database by IP, user, or raw SQL
- stats: Show database statistics
- list: List all case databases

Usage:
    # Analysis (original)
    python3 m365_ir_cli.py analyze /path/to/exports --customer "CustomerName"

    # Database operations (Phase 226.1) - auto-generates case ID from zip mtime
    python3 m365_ir_cli.py import ~/Downloads/Export.zip --customer "Fyna Foods"
    # Creates: ~/.maia/ir-cases/PIR-FYNA-FOODS-2025-12-15/
    #          ├── source-files/Export.zip (moved here)
    #          ├── reports/
    #          └── PIR-FYNA-FOODS-2025-12-15_logs.db

    # Query and analysis
    python3 m365_ir_cli.py query PIR-FYNA-FOODS-2025-12-15 --ip 185.234.100.50
    python3 m365_ir_cli.py query PIR-FYNA-FOODS-2025-12-15 --user victim@example.com
    python3 m365_ir_cli.py stats PIR-FYNA-FOODS-2025-12-15
    python3 m365_ir_cli.py list

Author: Maia System
Created: 2025-12-18 (Phase 225)
Updated: 2025-01-05 (Phase 226 - Database commands)
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

# Phase 226 - Database modules
from claude.tools.m365_ir.log_database import IRLogDatabase, DEFAULT_BASE_PATH
from claude.tools.m365_ir.log_importer import LogImporter
from claude.tools.m365_ir.log_query import LogQuery
from claude.tools.m365_ir.ir_case import IRCase

# Phase 230 - Account Validator
from claude.tools.m365_ir.account_validator import AccountValidator, ValidationError


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
            # Timeline is already sorted chronologically by TimelineBuilder.build()
            print(f"  First activity: {self.timeline[0].timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Last activity: {self.timeline[-1].timestamp.strftime('%Y-%m-%d %H:%M')}")

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


def cmd_import(args):
    """Handle import command - import logs into case database."""
    print(f"\n{'='*60}")
    print(f"M365 IR DATABASE IMPORT")
    print(f"{'='*60}")

    source_path = args.exports
    is_zip = source_path.is_file() and source_path.suffix.lower() == '.zip'

    # Determine case setup based on whether case_id is provided
    if args.case_id:
        # Use existing case or explicit case ID
        case = IRCase(case_id=args.case_id, base_path=args.base_path)
        if not case.exists():
            case.initialize()
            print(f"Created case: {case.case_id}")
        else:
            print(f"Using existing case: {case.case_id}")
    elif is_zip and args.customer:
        # Create new case from zip file - use zip mtime for date
        case = IRCase.from_zip(
            zip_path=source_path,
            customer=args.customer,
            base_path=args.base_path
        )
        case.initialize()
        print(f"Created case: {case.case_id}")
        print(f"  (date from zip file: {source_path.name})")
    elif source_path.is_dir() and args.customer:
        # Create new case from directory - use earliest file mtime for date
        case = IRCase.from_directory(
            dir_path=source_path,
            customer=args.customer,
            base_path=args.base_path
        )
        case.initialize()
        print(f"Created case: {case.case_id}")
        print(f"  (date from export files)")
    else:
        # Fallback: require customer for new cases
        if not args.customer:
            print("Error: --customer required when creating new case without --case-id")
            print("Usage: m365_ir_cli.py import exports.zip --customer 'Customer Name'")
            sys.exit(1)
        # Unknown source type - use current date as fallback
        customer_slug = args.customer.upper().replace(' ', '-')[:20]
        case_id = f"PIR-{customer_slug}-{datetime.now().strftime('%Y-%m-%d')}"
        case = IRCase(case_id=case_id, base_path=args.base_path)
        case.initialize()
        print(f"Created case: {case.case_id}")

    print(f"Case directory: {case.case_dir}")

    # Move zip to source-files if importing from zip
    import_source = source_path
    if is_zip and source_path.exists():
        moved_path = case.add_source_file(source_path)
        print(f"Moved zip to: {moved_path}")
        import_source = moved_path

    # Create database
    db = case.get_database()
    db_path = db.create()
    print(f"Database: {db_path}")

    # Import logs
    importer = LogImporter(db)
    print(f"\nImporting from: {import_source}")

    results = importer.import_all(import_source)

    print(f"\nImport Results:")
    total_imported = 0
    total_failed = 0
    for log_type, result in results.items():
        print(f"  {log_type}: {result.records_imported} imported, {result.records_failed} failed")
        total_imported += result.records_imported
        total_failed += result.records_failed
        if result.errors:
            for error in result.errors[:3]:
                print(f"    - {error}")
            if len(result.errors) > 3:
                print(f"    ... and {len(result.errors) - 3} more errors")

    print(f"\nTotal: {total_imported} records imported, {total_failed} failed")
    print(f"Reports directory: {case.reports_dir}")
    print(f"\nQuery with: python3 m365_ir_cli.py query {case.case_id} --ip <ip>")


def cmd_query(args):
    """Handle query command - query case database."""
    # Open database
    db = IRLogDatabase(case_id=args.case_id, base_path=args.base_path)
    if not db.exists:
        print(f"Error: Case database not found: {args.case_id}")
        print(f"Run 'import' first to create the database.")
        sys.exit(1)

    query = LogQuery(db)

    # Determine query type
    if args.ip:
        print(f"Activity for IP: {args.ip}")
        print("-" * 60)
        results = query.activity_by_ip(args.ip)
    elif args.user:
        print(f"Activity for user: {args.user}")
        print("-" * 60)
        results = query.activity_by_user(args.user)
    elif args.suspicious:
        print("Suspicious operations:")
        print("-" * 60)
        results = query.suspicious_operations()
    elif args.legacy_auth:
        # Legacy auth query with optional user filter
        if args.legacy_auth == 'all' or args.legacy_auth == '':
            print("Legacy authentication events (all):")
            print("-" * 60)
            summary = query.legacy_auth_summary()
            print(f"Total events: {summary['total_events']}")
            print(f"Unique users: {summary['unique_users']}")
            print(f"By client app: {summary['by_client_app']}")
            print(f"By country: {summary['by_country']}")
            results = query.execute("SELECT * FROM legacy_auth_logs ORDER BY timestamp DESC")
        else:
            print(f"Legacy auth for user: {args.legacy_auth}")
            print("-" * 60)
            results = query.legacy_auth_by_user(args.legacy_auth)
    elif args.password_status:
        # Password status query with optional user filter
        if args.password_status == 'all' or args.password_status == '':
            print("Password status (all users):")
            print("-" * 60)
            results = query.password_status()
        else:
            print(f"Password status for user: {args.password_status}")
            print("-" * 60)
            results = query.password_status(user=args.password_status)
    elif args.stale_passwords is not None:
        days = args.stale_passwords if args.stale_passwords > 0 else 90
        print(f"Accounts with passwords older than {days} days:")
        print("-" * 60)
        results = query.stale_passwords(days=days, enabled_only=True)
    elif args.sql:
        print(f"SQL: {args.sql}")
        print("-" * 60)
        results = query.execute(args.sql)
    else:
        print("Error: Specify --ip, --user, --suspicious, --legacy-auth, --password-status, --stale-passwords, or --sql")
        sys.exit(1)

    # Output results
    if not results:
        print("No results found.")
        return

    if args.format == 'json':
        print(json.dumps(results, indent=2, default=str))
    else:
        # Table format - adapt based on result type
        for r in results[:args.limit]:
            ts = r.get('timestamp', r.get('last_password_change', 'N/A'))
            source = r.get('source', r.get('client_app_used', 'N/A'))
            user = r.get('user', r.get('user_principal_name', 'N/A'))
            op = r.get('operation', r.get('days_since_change', 'N/A'))
            ip = r.get('ip_address', r.get('client_ip', r.get('account_enabled', 'N/A')))
            print(f"{ts} | {str(source):20} | {user:30} | {str(op):25} | {ip}")

        if len(results) > args.limit:
            print(f"\n... and {len(results) - args.limit} more results (use --limit to show more)")

    print(f"\nTotal: {len(results)} results")


def cmd_stats(args):
    """Handle stats command - show database statistics."""
    db = IRLogDatabase(case_id=args.case_id, base_path=args.base_path)
    if not db.exists:
        print(f"Error: Case database not found: {args.case_id}")
        sys.exit(1)

    print(f"Case: {args.case_id}")
    print(f"Database: {db.db_path}")
    print("-" * 40)

    stats = db.get_stats()
    total = 0
    for table, count in stats.items():
        print(f"  {table:25} {count:>8}")
        total += count

    print("-" * 40)
    print(f"  {'TOTAL':25} {total:>8}")


def cmd_list(args):
    """Handle list command - list all case databases."""
    base_path = Path(args.base_path)

    if not base_path.exists():
        print(f"No cases found in {base_path}")
        return

    print(f"Cases in {base_path}:")
    print("-" * 60)

    cases = []
    for case_dir in sorted(base_path.iterdir()):
        if not case_dir.is_dir():
            continue

        db_file = case_dir / f"{case_dir.name}_logs.db"
        if db_file.exists():
            # Get file stats
            stat = db_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')

            # Get record counts
            db = IRLogDatabase(case_id=case_dir.name, base_path=str(base_path))
            stats = db.get_stats()
            total_records = sum(stats.values())

            cases.append({
                'case_id': case_dir.name,
                'size_mb': size_mb,
                'modified': modified,
                'records': total_records
            })

    if not cases:
        print("No case databases found.")
        return

    for case in cases:
        print(f"  {case['case_id']:30} {case['records']:>8} records  {case['size_mb']:>6.2f} MB  {case['modified']}")

    print(f"\nTotal: {len(cases)} cases")


def cmd_validate_account(args):
    """
    Handle validate-account command - validate single compromised account.

    Phase 230: Account validation with hard enforcement of timestamp checks.
    """
    base_path = Path(args.base_path)
    db = IRLogDatabase(case_id=args.case_id, base_path=str(base_path))

    if not db.exists:
        print(f"❌ Error: Case database not found: {args.case_id}")
        print(f"   Expected: {db.db_path}")
        return 1

    print(f"Validating account: {args.account}")
    print("-" * 80)

    try:
        validator = AccountValidator(str(db.db_path), args.account)
        result = validator.validate()

        # Print lifecycle info
        lifecycle = result['lifecycle']
        print(f"\n✅ VALIDATION PASSED")
        print(f"\nAccount Lifecycle:")
        print(f"  Created: {lifecycle['created_date']}")
        print(f"  Status: {lifecycle['current_status']}")
        print(f"  Password age: {lifecycle['password_age_days']:,} days ({lifecycle['password_age_days']/365:.1f} years)")

        if lifecycle['disabled_date']:
            print(f"  Disabled: {lifecycle['disabled_date']}")
            print(f"  Disabled by: {lifecycle['disabled_by']}")
            print(f"  Disable reason: {lifecycle.get('disable_reason', 'N/A')}")

        if lifecycle['re_enabled']:
            print(f"  Re-enabled: {lifecycle['re_enabled_date']}")

        # Print compromise evidence
        compromise = result['compromise']
        foreign = compromise['foreign_logins']

        print(f"\nCompromise Evidence:")
        print(f"  Foreign logins: {foreign['total_foreign_logins']:,}")

        if foreign['first_foreign_login']:
            print(f"  First foreign login: {foreign['first_foreign_login']}")
            print(f"  Last foreign login: {foreign['last_foreign_login']}")
            print(f"  Countries: {', '.join(foreign['countries'][:5])}")

        print(f"  SMTP abuse events: {compromise['smtp_abuse_count']}")

        # Print warnings and errors
        sanity = result['sanity_check']

        if sanity['warnings']:
            print(f"\n⚠️  WARNINGS ({len(sanity['warnings'])}):")
            for w in sanity['warnings']:
                print(f"  [{w['type']}] {w['message']}")
                print(f"    Action required: {w['action_required']}")

        if sanity['errors']:
            print(f"\n❌ ERRORS ({len(sanity['errors'])}):")
            for e in sanity['errors']:
                print(f"  [{e['type']}] {e['message']}")
                print(f"    Action required: {e['action_required']}")

        # Print root cause
        print(f"\nRoot Cause Category: {result['root_cause_category']}")

        return 0

    except ValidationError as e:
        print(f"\n❌ VALIDATION FAILED")
        print(f"\n{str(e)}")
        return 1


def cmd_validate_all(args):
    """
    Handle validate-all command - validate all compromised accounts.

    Phase 230: Batch validation for all accounts with foreign login activity.
    """
    base_path = Path(args.base_path)
    db = IRLogDatabase(case_id=args.case_id, base_path=str(base_path))

    if not db.exists:
        print(f"❌ Error: Case database not found: {args.case_id}")
        print(f"   Expected: {db.db_path}")
        return 1

    # Get all accounts with foreign logins
    import sqlite3
    conn = sqlite3.connect(str(db.db_path))
    cursor = conn.cursor()

    print(f"Finding compromised accounts in {args.case_id}...")
    print()

    cursor.execute("""
        SELECT DISTINCT user_principal_name
        FROM sign_in_logs
        WHERE location_country NOT IN ('AU', 'Australia')
        ORDER BY user_principal_name
    """)

    accounts = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not accounts:
        print("No compromised accounts found (no foreign logins detected)")
        return 0

    print(f"Found {len(accounts)} compromised accounts. Validating...")
    print("=" * 80)

    results = []
    failures = []

    for account in accounts:
        print(f"\n{account}:")

        try:
            validator = AccountValidator(str(db.db_path), account)
            result = validator.validate()

            # Summary output
            lifecycle = result['lifecycle']
            compromise = result['compromise']
            sanity = result['sanity_check']

            status_emoji = "✅"
            if sanity['warnings']:
                status_emoji = "⚠️ "
            if sanity['errors']:
                status_emoji = "❌"

            print(f"  {status_emoji} Status: {lifecycle['current_status']}")
            print(f"  {status_emoji} Foreign logins: {compromise['foreign_logins']['total_foreign_logins']:,}")
            print(f"  {status_emoji} Password age: {lifecycle['password_age_days']:,} days")
            print(f"  {status_emoji} Root cause: {result['root_cause_category']}")

            if sanity['warnings']:
                print(f"  {status_emoji} Warnings: {len(sanity['warnings'])}")
                for w in sanity['warnings']:
                    print(f"     - [{w['type']}] {w['severity']}")

            if sanity['errors']:
                print(f"  {status_emoji} Errors: {len(sanity['errors'])}")
                for e in sanity['errors']:
                    print(f"     - [{e['type']}] {e['severity']}")

            results.append({'account': account, 'status': 'VALIDATED', 'result': result})

        except ValidationError as e:
            print(f"  ❌ VALIDATION FAILED")
            print(f"     {str(e)[:100]}...")
            failures.append({'account': account, 'error': str(e)})

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total accounts: {len(accounts)}")
    print(f"Validated: {len(results)}")
    print(f"Failed: {len(failures)}")

    if failures:
        print(f"\n❌ FAILED VALIDATIONS ({len(failures)}):")
        for f in failures:
            print(f"  - {f['account']}")
            print(f"    {f['error'][:100]}...")

    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(
        description="M365 Incident Response Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analysis (original Phase 225)
  %(prog)s analyze /path/to/export --customer "Acme Corp"
  %(prog)s analyze /export1 /export2 /export3 --customer "Oculus" --output ./results

  # Database operations (Phase 226)
  %(prog)s import /path/to/exports.zip --case-id PIR-ACME-2025-001   # Direct zip import
  %(prog)s import /path/to/extracted/ --case-id PIR-ACME-2025-001    # Directory import
  %(prog)s query PIR-ACME-2025-001 --ip 185.234.100.50
  %(prog)s query PIR-ACME-2025-001 --user victim@example.com
  %(prog)s query PIR-ACME-2025-001 --suspicious
  %(prog)s query PIR-ACME-2025-001 --legacy-auth                     # All legacy auth events
  %(prog)s query PIR-ACME-2025-001 --legacy-auth user@example.com    # Legacy auth for user
  %(prog)s query PIR-ACME-2025-001 --password-status                 # All password status
  %(prog)s query PIR-ACME-2025-001 --stale-passwords 90              # Passwords older than 90 days
  %(prog)s query PIR-ACME-2025-001 --sql "SELECT * FROM sign_in_logs WHERE location_country = 'Russia'"
  %(prog)s stats PIR-ACME-2025-001
  %(prog)s list

  # Account validation (Phase 230)
  %(prog)s validate-account PIR-ACME-2025-001 ben@example.com      # Validate single account
  %(prog)s validate-all PIR-ACME-2025-001                          # Validate all compromised accounts
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common arguments for database commands
    db_base_path = DEFAULT_BASE_PATH

    # Analyze command (original)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze M365 exports (original pipeline)")
    analyze_parser.add_argument("exports", nargs="+", type=Path, help="Export directories")
    analyze_parser.add_argument("--customer", "-c", required=True, help="Customer name")
    analyze_parser.add_argument("--home-country", default="AU", help="Home country code (default: AU)")
    analyze_parser.add_argument("--output", "-o", type=Path, help="Output directory for results")

    # Import command (Phase 226)
    import_parser = subparsers.add_parser("import", help="Import logs into case database (supports zip files)")
    import_parser.add_argument("exports", type=Path, help="Export directory or zip file to import")
    import_parser.add_argument("--case-id", help="Case identifier (auto-generated if not provided)")
    import_parser.add_argument("--customer", "-c", help="Customer name (used for auto-generated case ID)")
    import_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases (default: {db_base_path})")

    # Query command (Phase 226)
    query_parser = subparsers.add_parser("query", help="Query case database")
    query_parser.add_argument("case_id", help="Case identifier")
    query_parser.add_argument("--ip", help="Query by IP address")
    query_parser.add_argument("--user", help="Query by user email/UPN")
    query_parser.add_argument("--suspicious", action="store_true", help="Show suspicious operations")
    query_parser.add_argument("--legacy-auth", nargs='?', const='all', help="Query legacy auth (optionally filter by user)")
    query_parser.add_argument("--password-status", nargs='?', const='all', help="Query password status (optionally filter by user)")
    query_parser.add_argument("--stale-passwords", type=int, nargs='?', const=90, help="Find passwords older than N days (default: 90)")
    query_parser.add_argument("--sql", help="Execute raw SQL query")
    query_parser.add_argument("--format", choices=['table', 'json'], default='table', help="Output format")
    query_parser.add_argument("--limit", type=int, default=50, help="Limit results (default: 50)")
    query_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases")

    # Stats command (Phase 226)
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("case_id", help="Case identifier")
    stats_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases")

    # List command (Phase 226)
    list_parser = subparsers.add_parser("list", help="List all case databases")
    list_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases")

    # Validate-account command (Phase 230)
    validate_account_parser = subparsers.add_parser("validate-account", help="Validate single compromised account")
    validate_account_parser.add_argument("case_id", help="Case identifier")
    validate_account_parser.add_argument("account", help="User principal name (email) to validate")
    validate_account_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases")

    # Validate-all command (Phase 230)
    validate_all_parser = subparsers.add_parser("validate-all", help="Validate all compromised accounts")
    validate_all_parser.add_argument("case_id", help="Case identifier")
    validate_all_parser.add_argument("--base-path", default=db_base_path, help=f"Base path for case databases")

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

    elif args.command == "import":
        cmd_import(args)

    elif args.command == "query":
        cmd_query(args)

    elif args.command == "stats":
        cmd_stats(args)

    elif args.command == "list":
        cmd_list(args)

    elif args.command == "validate-account":
        sys.exit(cmd_validate_account(args))

    elif args.command == "validate-all":
        sys.exit(cmd_validate_all(args))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
