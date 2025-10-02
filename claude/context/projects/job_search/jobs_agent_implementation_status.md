# Jobs Agent - Implementation Status & Design Decisions

## Implementation Status
- **Current State**: Deployed and Active
- **Last Updated**: 2025-09-07
- **Primary Entry Point**: `/claude/tools/automated_job_monitor.py`
- **Cron Schedule**: 9am & 1pm weekdays via crontab
- **Database**: SQLite at `/claude/data/jobs.db` (616 jobs stored)
- **Authentication**: Gmail API credentials (configured)
- **Notification Status**: Uses Zapier MCP for email notifications (designed hybrid approach)

## System Architecture

### Current Data Flow
1. **Cron Trigger** → `automated_job_monitor.py --morning/afternoon`
2. **Email Fetch** → `gmail_job_fetcher.py` (Gmail API)
3. **Job Extraction** → `email_job_extractor.py` (URL parsing)
4. **Job Scoring** → `enhanced_profile_scorer.py` (AI analysis)
5. **Storage** → SQLite database with full job metadata
6. **Notifications** → Zapier MCP email alerts (hybrid architecture)

### Database Schema
- **616 total jobs** captured
- **Recent activity**: Last scrape Sept 6, 2025 at 9:52am
- **High-scoring jobs identified**: 12 jobs >= 7.0 threshold
- **Data retention**: All historical job data preserved

## Design Decisions

### ⚠️ INCOMPLETE - REQUIRES USER INPUT ⚠️
*This section needs input from the user about design decisions made during development that the current context window has forgotten.*

### Decision 1: Gmail API vs Zapier MCP (Email Reading)
- **Chosen**: Gmail API with `gmail_job_fetcher.py`
- **Alternatives Considered**: Zapier MCP Gmail integration
- **Rationale**: Zapier MCP responses exceeded token limits when fetching job emails with full content needed for URL extraction and parsing
- **Trade-offs**: More complex authentication setup and direct API management, but unlimited content access without token constraints

### Decision 2: SQLite vs External Database
- **Chosen**: SQLite local database
- **Alternatives Considered**: [NEED USER INPUT]
- **Rationale**: [NEED USER INPUT]
- **Trade-offs**: [NEED USER INPUT]

### Decision 3: Cron Schedule (9am/1pm weekdays)
- **Chosen**: Twice daily automated runs
- **Alternatives Considered**: [NEED USER INPUT]
- **Rationale**: [NEED USER INPUT]
- **Trade-offs**: [NEED USER INPUT]

### Decision 4: [OTHER DECISIONS USER REMEMBERS]
- **Chosen**: [NEED USER INPUT]
- **Alternatives Considered**: [NEED USER INPUT]
- **Rationale**: [NEED USER INPUT]
- **Trade-offs**: [NEED USER INPUT]

## Current Issues Identified
1. **Notification Integration**: Need to verify Zapier MCP email sending is working for job alerts
2. **Command Documentation Mismatch**: Commands reference `gmail_find_email()` but system uses `gmail_job_fetcher.py`
3. **Missing Test Suite**: No automated testing of email processing pipeline

## Hybrid Architecture Rationale
- **Email Reading**: Gmail API (token limit workaround)
- **Email Sending**: Zapier MCP (integration simplicity)
- **Processing**: Python scripts (full control)
- **Storage**: SQLite (zero maintenance)

## Integration Points
- **Career Database**: Access to experience data for CV generation
- **LinkedIn Optimizer Agent**: Share job market intelligence
- **Company Research Agent**: Enhanced company analysis for applications
- **Notification System**: Email alerts (currently non-functional)

## Success Metrics (Current Performance)
- **Job Capture**: 48 new jobs processed in latest run
- **Deduplication**: 274 duplicates successfully filtered
- **Scoring Accuracy**: 12 high-priority opportunities identified
- **System Uptime**: 100% (cron jobs running consistently)
- **Database Integrity**: No data loss, clean schema structure

---

**⚡ ACTION REQUIRED**: User input needed to complete design decision documentation before this can be considered final implementation status.