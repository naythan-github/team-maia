"""
M365 IR Data Quality System - Constants

Centralized configuration constants for Phase 1 system.

Created: 2026-01-07
Phase: PHASE_1_FOUNDATION
"""

# Phase 1.1: Breach Detection Thresholds
BREACH_DETECTION_THRESHOLD = 0.80  # 80% foreign success rate triggers breach alert
BREACH_ALERT_SEVERITY_CRITICAL = "CRITICAL"
BREACH_ALERT_SEVERITY_WARNING = "WARNING"

# Phase 1.2: Data Quality Thresholds
QUALITY_SCORE_THRESHOLD = 0.50  # 50% reliable fields minimum for import
UNIFORM_FIELD_THRESHOLD = 0.995  # 99.5% same value = unreliable field
POPULATION_RATE_THRESHOLD = 0.05  # 5% minimum population to consider field
DISCRIMINATORY_POWER_MINIMUM = 0.005  # Minimum discriminatory power (not enforced for binary fields)

# Phase 1.3: Status Code Management
STATUS_CODE_LOOKUP_TIMEOUT_MS = 10  # 10ms target for single lookup
UNKNOWN_CODE_DISPLAY_LIMIT = 5  # Show first 5 unknown codes in output

# Performance Targets (SLOs)
TARGET_IMPORT_DURATION_SECONDS = 30  # Full import should complete in <30s
TARGET_VERIFICATION_DURATION_SECONDS = 5  # Verification should complete in <5s
TARGET_QUALITY_CHECK_DURATION_SECONDS = 2  # Quality check should complete in <2s

# Database
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
