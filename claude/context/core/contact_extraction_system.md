# Comprehensive Gmail Contact Extraction System

## Overview

The Comprehensive Gmail Contact Extraction System is a robust, large-scale contact extraction solution built for the Maia AI Agent system. It processes thousands of emails from Gmail to extract contact information with intelligent deduplication, progress tracking, and error recovery capabilities.

## System Architecture

### Core Components

1. **ComprehensiveContactExtractor** (`comprehensive_contact_extractor.py`)
   - Enhanced contact extraction with advanced pattern matching
   - Intelligent fuzzy matching and deduplication
   - Confidence scoring for extracted contacts
   - Database management and contact persistence

2. **GmailMassContactProcessor** (`gmail_mass_contact_processor.py`)
   - Large-scale Gmail processing with rate limiting
   - Batch processing with progress tracking
   - Resumable sessions with checkpoint system
   - Error handling and recovery mechanisms

3. **ContactExtractionManager** (`contact_extraction_manager.py`)
   - System monitoring and health checks
   - Analytics and reporting
   - Session management and cleanup
   - Integration with Google Contacts sync

4. **Setup and Initialization** (`setup_contact_extraction.py`)
   - System initialization and configuration
   - Testing and validation utilities
   - Sample data generation

### Key Features

- **Large-Scale Processing**: Handle thousands of emails efficiently
- **Rate Limit Compliance**: Respect Gmail API limits automatically
- **Progress Persistence**: Resume interrupted processing seamlessly
- **Intelligent Extraction**: Extract contacts from headers, signatures, and content
- **Advanced Deduplication**: Fuzzy matching to merge similar contacts
- **Confidence Scoring**: Rate extraction quality for better data management
- **Comprehensive Monitoring**: Health checks, analytics, and reporting
- **Error Recovery**: Robust error handling with retry mechanisms

## Database Schema

### Contacts Table
```sql
contacts (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT, 
    company TEXT,
    job_title TEXT,
    phone TEXT,
    source_email_ids TEXT,      -- JSON array of source email IDs
    interaction_count INTEGER,   -- Number of email interactions
    confidence_score REAL,       -- Extraction confidence (0.0-1.0)
    extraction_source TEXT,      -- 'header', 'signature', 'content'
    first_seen DATETIME,
    last_seen DATETIME,
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    synced_to_google BOOLEAN,
    google_contact_id TEXT
)
```

### Processing State Table
```sql
processing_state (
    id INTEGER PRIMARY KEY,
    email_id TEXT UNIQUE,
    processed_at DATETIME,
    processing_time_ms INTEGER,
    contacts_extracted INTEGER,
    error_message TEXT
)
```

### Extraction Sessions Table
```sql
extraction_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    start_time DATETIME,
    end_time DATETIME,
    total_emails INTEGER,
    processed_emails INTEGER,
    contacts_extracted INTEGER,
    status TEXT,               -- 'active', 'completed', 'failed', 'paused'
    error_message TEXT
)
```

## Usage Guide

### Initial Setup

1. **Run the setup script**:
   ```bash
   python3 claude/tools/setup_contact_extraction.py
   ```

2. **Check system health**:
   ```bash
   python3 claude/tools/contact_extraction_manager.py --health
   ```

### Basic Operations

#### Small Test Extraction
```bash
python3 claude/tools/gmail_mass_contact_processor.py --max-emails 100
```

#### Full Mailbox Analysis (Dry Run)
```bash
python3 claude/tools/gmail_mass_contact_processor.py --dry-run
```

#### Date Range Processing
```bash
python3 claude/tools/gmail_mass_contact_processor.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --batch-size 100
```

#### Resume Interrupted Session
```bash
python3 claude/tools/gmail_mass_contact_processor.py --resume
```

### Monitoring and Management

#### System Health Check
```bash
python3 claude/tools/contact_extraction_manager.py --health
```

#### View Active Sessions
```bash
python3 claude/tools/contact_extraction_manager.py --sessions
```

#### Generate Analytics Report
```bash
python3 claude/tools/contact_extraction_manager.py --report analytics
```

#### View Processing Statistics
```bash
python3 claude/tools/comprehensive_contact_extractor.py --stats
```

### Google Contacts Integration

#### Check Sync Status
```bash
python3 claude/tools/contact_extraction_manager.py --sync-status
```

#### Prepare Contacts for Sync
```bash
python3 claude/tools/comprehensive_contact_extractor.py --prepare-sync
```

## Configuration

### Rate Limiting
- Default: 10 requests per second
- Gmail API limits: 250 requests per 100 seconds per user
- Automatic backoff on rate limit hits

### Batch Processing
- Default batch size: 50 emails
- Checkpoint interval: 100 emails
- Maximum retries: 3 per email

### Extraction Sources
1. **Header Extraction**: From, To, CC fields
2. **Signature Extraction**: Email signatures with contact info
3. **Content Extraction**: Email addresses in body content

### Confidence Scoring
- Header contacts: 0.9 confidence
- Signature contacts: 0.5-0.9 (based on information richness)
- Content contacts: 0.6 confidence
- Enhanced with name/company information: +0.1-0.3

## Performance Considerations

### Processing Speed
- Typical rate: 2-5 emails per second
- Large mailboxes (50k+ emails): 8-24 hours
- Rate limited by Gmail API quotas

### Resource Usage
- Memory: ~50-100MB during processing
- Database size: ~1MB per 1,000 contacts
- Log files: ~10MB per session

### Optimization Tips
1. Process in date ranges for large mailboxes
2. Use appropriate batch sizes (50-200)
3. Run during off-peak hours
4. Monitor system health regularly

## Error Handling

### Common Issues and Solutions

1. **Rate Limit Exceeded**
   - System automatically waits and retries
   - Consider reducing batch size

2. **Authentication Errors**
   - Re-run Gmail authentication
   - Check credentials file permissions

3. **Database Lock Errors**
   - Ensure only one extraction process runs
   - Use session management features

4. **Memory Issues**
   - Reduce batch size
   - Process in smaller date ranges

### Recovery Mechanisms
- Automatic session checkpointing
- Failed email tracking and retry
- Session status monitoring
- Database integrity checks

## Integration with Maia System

### UFC Context Integration
- Extraction results stored in UFC-compatible format
- Progress tracking via Maia's task management
- Error reporting through Maia's logging system

### Workflow Integration
- Can be triggered by Maia agents
- Results feed into other Maia tools
- Supports batch and real-time processing

### Data Export
- JSON export for other systems
- CSV export for spreadsheet analysis
- Direct Google Contacts sync via MCP Zapier

## Security and Privacy

### Data Protection
- Local database storage only
- No cloud storage of email content
- Contact data encrypted in transit to Google

### Access Control
- Gmail OAuth 2.0 authentication
- Read-only Gmail access
- User-controlled Google Contacts sync

### Compliance
- GDPR-friendly local processing
- User consent for Google sync
- Audit trail of all operations

## Troubleshooting

### Common Commands
```bash
# System health check
python3 claude/tools/contact_extraction_manager.py --health

# Repair stuck sessions
python3 claude/tools/contact_extraction_manager.py --repair

# Database optimization
python3 claude/tools/contact_extraction_manager.py --optimize

# View detailed logs
tail -f claude/data/gmail_mass_processing.log
```

### Debug Mode
Set logging level to DEBUG in the Python files for detailed output.

### Performance Monitoring
- Check processing rates in analytics
- Monitor error rates in system health
- Review session progress regularly

## Future Enhancements

### Planned Features
1. Real-time email processing
2. Advanced contact enrichment
3. Machine learning for better extraction
4. Multi-language support
5. Integration with CRM systems

### Scaling Considerations
- Multi-threaded processing
- Distributed processing support
- Cloud deployment options
- Enterprise-grade monitoring

---

For technical support or questions about the Contact Extraction System, refer to the logs in `${MAIA_ROOT}/claude/data/` or use the built-in diagnostic tools.