#!/usr/bin/env python3
"""
Gmail Job Fetcher - Direct Gmail API access for JobsAgent emails
Fetches and processes job emails without token limitations
"""

import os
import json
import base64
import sqlite3
import webbrowser
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailJobFetcher:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        """Initialize Gmail API client"""
        self.service = None
        self.credentials_file = credentials_file
        self.token_file = token_file

    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None

        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)

                print("\n🌐 Manual Chrome Authentication Required")
                print("=" * 50)
                print("We'll provide you a URL to open in Chrome manually.")
                print("This avoids Firefox compatibility issues.")
                print("")

                # Use manual flow instead of automatic browser opening
                creds = flow.run_local_server(port=0, open_browser=False)

                print("\n✅ Authentication completed successfully!")

            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        return True

    def get_label_id(self, label_name='JobsAgent'):
        """Get the label ID for JobsAgent emails"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            return None
        except Exception as e:
            print(f"Error getting label: {e}")
            return None

    def fetch_emails_batch(self, query, max_results=10):
        """Fetch a batch of emails with full content"""
        try:
            # Get message IDs first
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                # Fetch full message content
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()

                # Extract email data
                email_data = self.parse_email(message)
                if email_data:
                    emails.append(email_data)

            return emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def parse_email(self, message):
        """Parse email message to extract job information"""
        try:
            headers = message['payload'].get('headers', [])

            # Extract header information
            subject = ''
            from_email = ''
            date = ''

            for header in headers:
                name = header['name']
                value = header['value']

                if name == 'Subject':
                    subject = value
                elif name == 'From':
                    from_email = value
                elif name == 'Date':
                    date = value

            # Extract body
            body = self.get_message_body(message['payload'])

            return {
                'id': message['id'],
                'subject': subject,
                'from': from_email,
                'date': date,
                'body': body
            }

        except Exception as e:
            print(f"Error parsing email: {e}")
            return None

    def get_message_body(self, payload):
        """Extract body from email payload"""
        body = ''

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return body

    def fetch_jobs_from_date_range(self, start_date, end_date, batch_size=10):
        """Fetch all JobsAgent emails from a date range"""
        query = f'label:JobsAgent after:{start_date} before:{end_date}'

        all_emails = []
        page_token = None
        total_fetched = 0

        print(f"Fetching emails from {start_date} to {end_date}...")

        while True:
            try:
                # Build request with pagination
                if page_token:
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=batch_size,
                        pageToken=page_token
                    ).execute()
                else:
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=batch_size
                    ).execute()

                messages = results.get('messages', [])

                # Fetch full content for each message
                for msg in messages:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()

                    email_data = self.parse_email(message)
                    if email_data:
                        all_emails.append(email_data)
                        total_fetched += 1

                        if total_fetched % 10 == 0:
                            print(f"  Fetched {total_fetched} emails...")

                # Check for more pages
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except Exception as e:
                print(f"Error in batch fetch: {e}")
                break

        print(f"Total fetched: {total_fetched} emails")
        return all_emails


def extract_and_store_jobs(emails):
    """Extract job URLs from emails and store in database"""
    import sys
    sys.path.append(str(Path(__file__).parent))
    from email_job_extractor import extract_urls_from_email, store_jobs_in_db

    total_extracted = 0
    total_stored = 0
    total_duplicates = 0

    for email in emails:
        # Extract URLs from email body
        urls = extract_urls_from_email(email['body'])

        # Prepare job records
        jobs = []
        for url_data in urls:
            job = {
                'url': url_data['url'],
                'job_id': url_data['job_id'],
                'email_date': email['date'],
                'email_subject': email['subject']
            }

            # Try to extract basic info from email body
            # This is a simple extraction - can be enhanced
            lines = email['body'].split('\n')
            for i, line in enumerate(lines):
                if url_data['job_id'] in line:
                    # Look for title (usually line before URL)
                    if i > 0:
                        job['title'] = lines[i-1].strip()
                    # Look for company (usually line after URL)
                    if i < len(lines) - 2:
                        job['company'] = lines[i+1].strip()
                        job['location'] = lines[i+2].strip()
                    break

            jobs.append(job)

        # Store in database
        if jobs:
            stored, duplicates = store_jobs_in_db(jobs)
            total_extracted += len(jobs)
            total_stored += stored
            total_duplicates += duplicates

    return {
        'extracted': total_extracted,
        'stored': total_stored,
        'duplicates': total_duplicates
    }


def main():
    """Main execution"""
    print("=" * 60)
    print("Gmail Job Fetcher - Direct API Access")
    print("=" * 60)

    # Check for credentials
    cred_file = Path(__file__).parent.parent / 'data' / 'gmail_credentials.json'
    token_file = Path(__file__).parent.parent / 'data' / 'gmail_token.pickle'

    if not os.path.exists(cred_file):
        print("\n⚠️  Gmail API credentials not found!")
        print("\nTo set up Gmail API access:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download credentials.json")
        print(f"6. Save as: {cred_file}")
        return

    # Initialize fetcher
    fetcher = GmailJobFetcher(cred_file, token_file)

    print("\n🔐 Authenticating with Gmail API...")
    if not fetcher.authenticate():
        print("❌ Authentication failed")
        return

    print("✅ Authentication successful!")

    # Define date range (past 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Process day by day
    current_date = start_date
    all_stats = {'extracted': 0, 'stored': 0, 'duplicates': 0}

    while current_date < end_date:
        next_date = current_date + timedelta(days=1)

        date_str = current_date.strftime('%Y/%m/%d')
        next_str = next_date.strftime('%Y/%m/%d')

        print(f"\n📅 Processing {current_date.strftime('%B %d, %Y')}...")

        # Fetch emails for this day
        emails = fetcher.fetch_jobs_from_date_range(date_str, next_str, batch_size=20)

        if emails:
            # Extract and store jobs
            stats = extract_and_store_jobs(emails)
            all_stats['extracted'] += stats['extracted']
            all_stats['stored'] += stats['stored']
            all_stats['duplicates'] += stats['duplicates']

            print(f"  📊 Results: {len(emails)} emails, {stats['extracted']} jobs extracted, {stats['stored']} new, {stats['duplicates']} duplicates")

        current_date = next_date

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"📧 Total jobs extracted: {all_stats['extracted']}")
    print(f"✅ New jobs stored: {all_stats['stored']}")
    print(f"🔄 Duplicates skipped: {all_stats['duplicates']}")

    # Check database
    db_path = Path(__file__).parent.parent / 'data' / 'databases' / 'user' / 'jobs.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(DISTINCT url) FROM jobs')
    total = cursor.fetchone()[0]
    conn.close()

    print(f"💾 Total unique jobs in database: {total}")


if __name__ == '__main__':
    main()
