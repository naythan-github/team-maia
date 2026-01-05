"""
M365 Incident Response Analysis Tool

Automated log parsing, baseline detection, anomaly identification,
timeline building, and PIR generation for M365 security incidents.

Phase 225: Initial implementation
Phase 226: Per-investigation SQLite storage (IR Log Database)
Phase 229: Compression for raw_record and audit_data (zlib level 6)

Author: Maia System
Created: 2025-12-18 (Phase 225)
Updated: 2025-01-05 (Phase 229)
"""

__version__ = "1.2.0"

# Compression utilities (Phase 229)
from .compression import compress_json, decompress_json, is_compressed, COMPRESSION_LEVEL

# Core database classes
from .log_database import IRLogDatabase
from .log_importer import LogImporter, ImportResult
from .log_query import LogQuery

# Existing parser classes
from .m365_log_parser import (
    M365LogParser,
    LogType,
    SignInLogEntry,
    AuditLogEntry,
    MailboxAuditEntry,
    LegacyAuthEntry,
)

__all__ = [
    # Phase 229 - Compression
    'compress_json',
    'decompress_json',
    'is_compressed',
    'COMPRESSION_LEVEL',
    # Phase 226 - Database
    'IRLogDatabase',
    'LogImporter',
    'ImportResult',
    'LogQuery',
    # Phase 225 - Parser
    'M365LogParser',
    'LogType',
    'SignInLogEntry',
    'AuditLogEntry',
    'MailboxAuditEntry',
    'LegacyAuthEntry',
]
