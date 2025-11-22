#!/usr/bin/env python3
"""
Email Job URL Extractor for JobsAgent emails
Processes SEEK job alert emails and extracts job URLs for database storage
"""

import re
import json
import sqlite3
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import hashlib

def extract_urls_from_email(email_body):
    """Extract job URLs from SEEK email body text"""
    # Pattern to match SEEK job URLs
    seek_pattern = r'https://www\.seek\.com\.au/job/(\d+)\?[^\s\[\]]*'

    urls = []
    matches = re.finditer(seek_pattern, email_body)

    for match in matches:
        full_url = match.group(0)
        job_id = match.group(1)

        # Normalize URL by removing ALL query parameters for deduplication
        # Store only the base URL to prevent duplicates
        clean_url = f"https://www.seek.com.au/job/{job_id}"

        urls.append({
            'url': clean_url,
            'job_id': job_id,
            'original_url': full_url
        })

    return urls

def extract_job_details_from_email(email_body):
    """Extract job details visible in email preview"""
    jobs = []

    # Split email into job sections (rough approach)
    # Look for job title patterns followed by company and location
    lines = email_body.split('\n')
    current_job = None

    for line in lines:
        line = line.strip()

        # Skip empty lines and image placeholders
        if not line or line.startswith('[') or line.startswith('http'):
            continue

        # Check if this line contains a job URL
        if 'seek.com.au/job/' in line:
            url_match = re.search(r'https://www\.seek\.com\.au/job/(\d+)[^\s\]]*', line)
            if url_match and current_job:
                current_job['url'] = url_match.group(0)
                current_job['job_id'] = url_match.group(1)
                jobs.append(current_job)
                current_job = None

        # Potential job title (not containing common footer text)
        elif line and not any(skip in line.lower() for skip in [
            'seek', 'job alert', 'email', 'privacy', 'unsubscribe',
            'download', 'app', 'view all', 'posted on', 'jobs you may'
        ]):
            # If we see something that looks like a title, start a new job
            if len(line.split()) <= 8:  # Reasonable title length
                current_job = {
                    'title': line,
                    'company': None,
                    'location': None,
                    'salary': None
                }
            # If we have a current job, this might be company or location
            elif current_job and not current_job.get('company'):
                current_job['company'] = line
            elif current_job and not current_job.get('location') and ('WA' in line or 'Perth' in line):
                current_job['location'] = line
            elif current_job and not current_job.get('salary') and ('$' in line or 'package' in line.lower()):
                current_job['salary'] = line

    return jobs

def store_jobs_in_db(jobs, db_path=None):
    """Store extracted jobs in the database"""
    if db_path is None:
        db_path = Path(__file__).parent.parent / 'data' / 'databases' / 'user' / 'jobs.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stored_count = 0
    duplicate_count = 0

    for job in jobs:
        try:
            # Create description hash for deduplication
            description_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('location', '')}"
            description_hash = hashlib.md5(description_text.encode(), usedforsecurity=False).hexdigest()

            cursor.execute('''
                INSERT OR IGNORE INTO jobs
                (url, job_id, title, company, location, salary_text,
                 description_hash, scraped_at, source, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job['url'],
                job['job_id'],
                job.get('title'),
                job.get('company'),
                job.get('location'),
                job.get('salary'),
                description_hash,
                datetime.now(),
                'email',
                json.dumps(job)
            ))

            if cursor.rowcount > 0:
                stored_count += 1
            else:
                duplicate_count += 1

        except Exception as e:
            print(f"Error storing job {job.get('job_id')}: {e}")

    conn.commit()
    conn.close()

    return stored_count, duplicate_count

def process_email_batch(email_data):
    """Process a batch of emails and extract/store job URLs"""
    results = {
        'processed_emails': 0,
        'extracted_jobs': 0,
        'stored_jobs': 0,
        'duplicate_jobs': 0,
        'errors': []
    }

    for email in email_data:
        try:
            results['processed_emails'] += 1

            # Extract URLs from email body
            urls = extract_urls_from_email(email['body_plain'])

            # Extract job details from email content
            job_details = extract_job_details_from_email(email['body_plain'])

            # Merge URL and detail data
            merged_jobs = []
            for url_data in urls:
                # Try to find matching job details
                job_data = url_data.copy()

                # Look for details that might match this job ID
                for detail in job_details:
                    if detail.get('job_id') == url_data['job_id'] or not detail.get('job_id'):
                        job_data.update({k: v for k, v in detail.items() if v and k != 'job_id'})
                        break

                # Add email metadata
                job_data.update({
                    'email_date': email['date'],
                    'email_subject': email['subject'],
                    'from_email': email['from']['email']
                })

                merged_jobs.append(job_data)

            results['extracted_jobs'] += len(merged_jobs)

            # Store in database
            if merged_jobs:
                stored, duplicates = store_jobs_in_db(merged_jobs)
                results['stored_jobs'] += stored
                results['duplicate_jobs'] += duplicates

        except Exception as e:
            error_msg = f"Error processing email {email.get('id', 'unknown')}: {e}"
            results['errors'].append(error_msg)
            print(error_msg)

    return results

if __name__ == "__main__":
    # Test with sample data
    print("Email Job URL Extractor ready for batch processing")
