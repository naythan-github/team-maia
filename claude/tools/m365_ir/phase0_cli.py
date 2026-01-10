"""
M365 IR Phase 0 Auto-Checks CLI
Sprint 4: Production Integration

Command-line interface for running Phase 0 automated security checks
on M365 IR investigation databases.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Handle both module import and direct script execution
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from claude.tools.m365_ir import phase0_auto_checks as checks
else:
    from . import phase0_auto_checks as checks


def run_phase0_checks(db_path: str, output_format: str = 'summary') -> Dict[str, Any]:
    """
    Run all Phase 0 automated checks and return results.

    Args:
        db_path: Path to M365 IR investigation database
        output_format: Output format ('json', 'table', 'summary')

    Returns:
        dict: Consolidated results from all checks
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'database': db_path,
        'checks': {},
        'summary': {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'ok': 0,
            'total_checks': 0
        }
    }

    # Sprint 1: Core Security Checks
    try:
        password_result = checks.analyze_password_hygiene_with_context(db_path)
        results['checks']['password_hygiene'] = password_result
        _update_summary(results['summary'], password_result.get('risk', 'OK'))
    except Exception as e:
        results['checks']['password_hygiene'] = {'error': str(e)}

    try:
        foreign_result = checks.check_foreign_baseline(db_path)
        results['checks']['foreign_baseline'] = foreign_result
        if foreign_result.get('status') == 'FLAGGED':
            _update_summary(results['summary'], 'HIGH')
        else:
            _update_summary(results['summary'], 'OK')
    except Exception as e:
        results['checks']['foreign_baseline'] = {'error': str(e)}

    # Sprint 2: False Positive Prevention
    try:
        dormant_result = checks.detect_dormant_accounts(
            db_path,
            exclude_service=True,
            breakglass_whitelist=checks.load_breakglass_whitelist()
        )
        results['checks']['dormant_accounts'] = dormant_result
        if dormant_result['dormant_accounts']:
            _update_summary(results['summary'], 'MEDIUM')
        else:
            _update_summary(results['summary'], 'OK')
    except Exception as e:
        results['checks']['dormant_accounts'] = {'error': str(e)}

    try:
        admin_accounts = checks.get_admin_accounts(db_path)
        results['checks']['admin_accounts'] = {
            'count': len(admin_accounts),
            'accounts': list(admin_accounts)
        }
        _update_summary(results['summary'], 'OK')  # Informational only
    except Exception as e:
        results['checks']['admin_accounts'] = {'error': str(e)}

    # Sprint 3: False Negative Prevention
    try:
        logging_result = checks.detect_logging_tampering(db_path)
        results['checks']['logging_tampering'] = logging_result
        _update_summary(results['summary'], logging_result.get('risk_level', 'OK'))
    except Exception as e:
        results['checks']['logging_tampering'] = {'error': str(e)}

    try:
        travel_result = checks.detect_impossible_travel(db_path)
        results['checks']['impossible_travel'] = travel_result
        _update_summary(results['summary'], travel_result.get('risk_level', 'OK'))
    except Exception as e:
        results['checks']['impossible_travel'] = {'error': str(e)}

    try:
        mfa_bypass_result = checks.detect_mfa_bypass(db_path)
        results['checks']['mfa_bypass'] = mfa_bypass_result
        _update_summary(results['summary'], mfa_bypass_result.get('risk_level', 'OK'))
    except Exception as e:
        results['checks']['mfa_bypass'] = {'error': str(e)}

    return results


def _update_summary(summary: Dict[str, int], risk_level: str):
    """Update summary counters based on risk level."""
    summary['total_checks'] += 1
    risk_lower = risk_level.lower()
    if risk_lower == 'critical':
        summary['critical'] += 1
    elif risk_lower == 'high':
        summary['high'] += 1
    elif risk_lower == 'medium':
        summary['medium'] += 1
    else:
        summary['ok'] += 1


def format_json(results: Dict[str, Any]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def format_table(results: Dict[str, Any]) -> str:
    """Format results as ASCII table."""
    output = []
    output.append("=" * 80)
    output.append("M365 IR Phase 0 Auto-Checks - Results")
    output.append("=" * 80)
    output.append(f"Database: {results['database']}")
    output.append(f"Timestamp: {results['timestamp']}")
    output.append("")

    # Password Hygiene
    if 'password_hygiene' in results['checks']:
        pw = results['checks']['password_hygiene']
        if 'error' in pw:
            output.append(f"[ERROR] Password Hygiene: {pw['error']}")
        else:
            output.append(f"[{pw.get('risk', 'OK')}] Password Hygiene")
            output.append(f"  - {pw.get('pct_over_1_year', 0)}% of {pw.get('total_accounts', 0)} accounts have passwords >1 year old")
            if 'mfa_rate' in pw:
                output.append(f"  - MFA enforcement: {pw['mfa_rate']}% ({pw.get('context', 'UNKNOWN')})")
        output.append("")

    # Foreign Baseline
    if 'foreign_baseline' in results['checks']:
        fb = results['checks']['foreign_baseline']
        if 'error' in fb:
            output.append(f"[ERROR] Foreign Baseline: {fb['error']}")
        else:
            status = fb.get('status', 'OK')
            output.append(f"[{status}] Foreign Sign-ins")
            if status == 'FLAGGED':
                output.append(f"  - {len(fb.get('accounts', []))} accounts with sign-ins from foreign countries")
            else:
                output.append(f"  - No unusual foreign sign-ins detected")
        output.append("")

    # Dormant Accounts
    if 'dormant_accounts' in results['checks']:
        da = results['checks']['dormant_accounts']
        if 'error' in da:
            output.append(f"[ERROR] Dormant Accounts: {da['error']}")
        else:
            dormant_count = len(da.get('dormant_accounts', []))
            if dormant_count > 0:
                output.append(f"[MEDIUM] Dormant Accounts")
                output.append(f"  - {dormant_count} accounts with no recent sign-ins")
            else:
                output.append(f"[OK] Dormant Accounts")
                output.append(f"  - No dormant accounts detected")
            if 'excluded_service_accounts' in da:
                output.append(f"  - {len(da['excluded_service_accounts'])} service accounts excluded")
            if 'excluded_breakglass_accounts' in da:
                output.append(f"  - {len(da['excluded_breakglass_accounts'])} break-glass accounts whitelisted")
        output.append("")

    # Logging Tampering (T1562.008)
    if 'logging_tampering' in results['checks']:
        lt = results['checks']['logging_tampering']
        if 'error' in lt:
            output.append(f"[ERROR] Logging Tampering: {lt['error']}")
        else:
            risk = lt.get('risk_level', 'OK')
            changes = lt.get('logging_changes', [])
            output.append(f"[{risk}] Logging Tampering (T1562.008)")
            if changes:
                output.append(f"  - {len(changes)} logging configuration changes detected")
                for change in changes[:3]:  # Show first 3
                    output.append(f"    • {change.get('timestamp')}: {change.get('activity')}")
            else:
                output.append(f"  - No logging tampering detected")
        output.append("")

    # Impossible Travel
    if 'impossible_travel' in results['checks']:
        it = results['checks']['impossible_travel']
        if 'error' in it:
            output.append(f"[ERROR] Impossible Travel: {it['error']}")
        else:
            risk = it.get('risk_level', 'OK')
            events = it.get('impossible_travel_events', [])
            output.append(f"[{risk}] Impossible Travel")
            if events:
                output.append(f"  - {len(events)} impossible travel events detected")
                for event in events[:3]:  # Show first 3
                    output.append(f"    • {event['upn']}: {event['login1']['country']} → {event['login2']['country']} in {event['time_hours']}h ({event['speed_mph']} mph)")
            else:
                output.append(f"  - No impossible travel detected")
        output.append("")

    # MFA Bypass
    if 'mfa_bypass' in results['checks']:
        mb = results['checks']['mfa_bypass']
        if 'error' in mb:
            output.append(f"[ERROR] MFA Bypass: {mb['error']}")
        else:
            risk = mb.get('risk_level', 'OK')
            attempts = mb.get('mfa_bypass_attempts', [])
            output.append(f"[{risk}] MFA Bypass Detection")
            if attempts:
                output.append(f"  - {len(attempts)} MFA bypass attempts detected")
                for attempt in attempts[:3]:  # Show first 3
                    output.append(f"    • {attempt['upn']}: MFA disabled {attempt['time_delta_hours']}h after enabling")
            else:
                output.append(f"  - No MFA bypass attempts detected")
        output.append("")

    # Summary
    summary = results['summary']
    output.append("=" * 80)
    output.append("Summary")
    output.append("=" * 80)
    output.append(f"  CRITICAL issues: {summary['critical']}")
    output.append(f"  HIGH issues:     {summary['high']}")
    output.append(f"  MEDIUM issues:   {summary['medium']}")
    output.append(f"  OK checks:       {summary['ok']}")
    output.append(f"  Total checks:    {summary['total_checks']}")
    output.append("=" * 80)

    return "\n".join(output)


def format_summary(results: Dict[str, Any]) -> str:
    """Format results as brief summary."""
    output = []
    output.append("M365 IR Phase 0 Auto-Checks - Summary")
    output.append("=" * 50)

    summary = results['summary']

    # Critical issues
    if summary['critical'] > 0:
        output.append(f"\n⚠️  CRITICAL: {summary['critical']} issue(s) require immediate attention")
        for check_name, check_result in results['checks'].items():
            if check_result.get('risk') == 'CRITICAL' or check_result.get('risk_level') == 'CRITICAL':
                output.append(f"  • {check_name.replace('_', ' ').title()}")

    # High issues
    if summary['high'] > 0:
        output.append(f"\n⚠️  HIGH: {summary['high']} issue(s) need review")
        for check_name, check_result in results['checks'].items():
            if check_result.get('risk') == 'HIGH' or check_result.get('risk_level') == 'HIGH':
                output.append(f"  • {check_name.replace('_', ' ').title()}")

    # Medium issues
    if summary['medium'] > 0:
        output.append(f"\n📊 MEDIUM: {summary['medium']} issue(s) for review")

    # All OK
    if summary['critical'] == 0 and summary['high'] == 0 and summary['medium'] == 0:
        output.append("\n✅ All checks passed - no critical issues detected")

    output.append(f"\nTotal checks run: {summary['total_checks']}")
    output.append("\nRun with --format=table for detailed results")

    return "\n".join(output)


def main(db_path: str, output_format: str = 'summary'):
    """
    Main CLI entry point.

    Args:
        db_path: Path to M365 IR investigation database
        output_format: Output format ('json', 'table', 'summary')
    """
    try:
        results = run_phase0_checks(db_path, output_format)

        if output_format == 'json':
            print(format_json(results))
        elif output_format == 'table':
            print(format_table(results))
        else:  # summary (default)
            print(format_summary(results))

        # Exit code based on severity
        if results['summary']['critical'] > 0:
            sys.exit(2)  # Critical issues found
        elif results['summary']['high'] > 0:
            sys.exit(1)  # High issues found
        else:
            sys.exit(0)  # No critical/high issues

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='M365 IR Phase 0 Auto-Checks')
    parser.add_argument('db_path', help='Path to M365 IR investigation database')
    parser.add_argument(
        '--format',
        choices=['json', 'table', 'summary'],
        default='summary',
        help='Output format (default: summary)'
    )

    args = parser.parse_args()
    main(args.db_path, args.format)
