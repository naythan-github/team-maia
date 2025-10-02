# Job Automation Setup Guide

## Overview
Complete automation system for monitoring JobsAgent emails and sending high-value job notifications at 9am and 1pm daily.

## System Components

### 1. Gmail API Job Fetcher (`gmail_job_fetcher.py`)
- Direct Gmail API access to bypass Zapier token limits
- Fetches complete email bodies (not snippets)
- Processes 200+ emails from past 7 days
- Extracts job URLs from SEEK emails
- Stores jobs in SQLite database

**Key Features:**
- OAuth 2.0 authentication
- Batch processing with pagination
- Day-by-day processing to handle large volumes
- Automatic job URL extraction and storage

### 2. Automated Job Monitor (`automated_job_monitor.py`)
- Comprehensive job scoring system (0-10 scale)
- HTML email notifications
- Configurable scoring criteria
- Scheduled execution support

**Scoring Criteria:**
- Keywords: "senior", "lead", "manager", "architect" (+2-3 points)
- Salary ranges: >$120k (+2), >$100k (+1)
- Location preferences: Perth, remote work (+1)
- Experience levels and specializations

### 3. Cron Job Scheduler (`setup_job_cron.py`)
- Automated cron job installation
- Status monitoring and verification
- Manual testing capabilities
- Log management

## Setup Instructions

### Step 1: Gmail API Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 Client ID credentials
5. Download `credentials.json`
6. Save as `${MAIA_ROOT}/claude/data/gmail_credentials.json`

### Step 2: Email Configuration
Edit `${MAIA_ROOT}/claude/data/job_monitor_config.json`:

```json
{
  "smtp_settings": {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "app_password": "your-app-password"
  },
  "notification_email": "your-email@gmail.com"
}
```

**Gmail App Password Setup:**
1. Enable 2-factor authentication
2. Go to Account Settings > Security > App passwords
3. Generate new app password for "Mail"
4. Use this password in config (not your regular password)

### Step 3: Install Cron Jobs
```bash
cd ${MAIA_ROOT}/claude/tools
python3 setup_job_cron.py
```

This creates two cron entries:
- `0 9 * * 1-5` - Morning digest at 9:00 AM (Mon-Fri)
- `0 13 * * 1-5` - Afternoon digest at 1:00 PM (Mon-Fri)

### Step 4: Initial Database Population
```bash
cd ${MAIA_ROOT}/claude/tools
python3 gmail_job_fetcher.py
```

## Usage Commands

### Manual Testing
```bash
# Test job monitor (no emails sent)
python3 automated_job_monitor.py --test

# Manual morning digest
python3 automated_job_monitor.py --morning

# Manual afternoon digest  
python3 automated_job_monitor.py --afternoon

# View configuration
python3 automated_job_monitor.py --config
```

### Cron Management
```bash
# Check cron status
python3 setup_job_cron.py --status

# Manual test run
python3 setup_job_cron.py --test

# Edit cron jobs directly
crontab -e

# List current cron jobs
crontab -l
```

### Database Management
```bash
# Check job count
sqlite3 ${MAIA_ROOT}/claude/data/jobs.db "SELECT COUNT(*) FROM jobs;"

# View recent high-scoring jobs
sqlite3 ${MAIA_ROOT}/claude/data/jobs.db "SELECT title, company, score FROM jobs WHERE score >= 7 ORDER BY scraped_at DESC LIMIT 10;"
```

## File Locations

```
${MAIA_ROOT}/claude/
├── tools/
│   ├── gmail_job_fetcher.py           # Gmail API fetcher
│   ├── automated_job_monitor.py       # Main monitoring system
│   ├── setup_job_cron.py             # Cron job installer
│   └── email_job_extractor.py        # URL extraction utilities
├── data/
│   ├── gmail_credentials.json         # Gmail API credentials
│   ├── gmail_token.pickle            # OAuth tokens
│   ├── job_monitor_config.json       # Email/scoring configuration
│   ├── jobs.db                       # SQLite job database
│   └── job_monitor.log               # Execution logs
└── docs/
    └── job_automation_setup.md       # This documentation
```

## Expected Results

**After full 7-day email processing:**
- 200+ emails processed
- 500-1000 unique jobs in database
- Daily high-value job notifications
- Automatic deduplication of job listings

**Email Notifications Include:**
- Jobs scoring ≥7/10 (configurable threshold)
- Company, location, salary information
- Direct links to job postings
- Score breakdown and reasoning
- Summary statistics

## Troubleshooting

### Gmail API Issues
- Ensure credentials file exists and is valid
- Check OAuth token expiration (auto-refreshes)
- Verify Gmail API is enabled in Google Cloud Console

### Email Delivery Issues
- Verify SMTP settings in configuration
- Use Gmail app password, not regular password
- Check spam folder for initial notifications

### Cron Job Issues
- Verify cron service is running: `sudo launchctl list | grep cron`
- Check log file: `${MAIA_ROOT}/claude/data/job_monitor.log`
- Test manual execution before relying on cron

### Database Issues
- Check file permissions on jobs.db
- Verify SQLite installation: `sqlite3 --version`
- Check available disk space

## Customization

### Scoring Adjustments
Edit scoring criteria in `automated_job_monitor.py`:
```python
def score_job(self, job: Dict) -> Tuple[float, List[str]]:
    # Modify scoring logic here
```

### Email Template
Customize HTML email format in `format_email_content()` method.

### Schedule Changes
Modify cron times in `setup_job_cron.py` or edit directly with `crontab -e`.

## System Monitoring

The system provides multiple monitoring mechanisms:
- Execution logs in `${MAIA_ROOT}/claude/data/job_monitor.log`
- Database statistics in email notifications
- Manual status checks via command-line tools
- Cron job verification utilities

This automation system provides comprehensive job monitoring with minimal manual intervention, delivering high-value opportunities directly to your inbox twice daily.