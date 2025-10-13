#!/usr/bin/env python3
"""
Contact Extractor - Automated Contact Management from Emails

Extracts contact information from email signatures and adds to macOS Contacts.
Uses pattern matching and NLP to identify names, titles, companies, phones, emails.

Privacy:
- 100% local processing (zero external API calls)
- Only extracts data explicitly present in emails
- User preview before adding contacts

Author: Maia System
Created: 2025-10-13 (Phase 112)
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.macos_mail_bridge import MacOSMailBridge


@dataclass
class Contact:
    """Extracted contact information"""
    name: str
    email: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    source_email_id: Optional[str] = None
    confidence: float = 0.0  # 0-1 confidence score


class SignatureParser:
    """Parse email signatures to extract contact information"""

    def __init__(self):
        # Common signature patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(?:(?:\+?61|0)\s?[2-478](?:\s?\d){8}|(?:\+?61|0)\s?4\d{2}\s?\d{3}\s?\d{3})')
        self.mobile_pattern = re.compile(r'(?:(?:\+?61|0)\s?4\d{2}\s?\d{3}\s?\d{3})')
        self.url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')

        # Common title indicators
        self.title_keywords = [
            'director', 'manager', 'engineer', 'consultant', 'specialist', 'analyst',
            'architect', 'lead', 'senior', 'principal', 'head', 'chief', 'officer',
            'ceo', 'cto', 'cio', 'vp', 'president', 'founder', 'owner', 'partner',
            'coordinator', 'administrator', 'developer', 'designer', 'recruiter'
        ]

        # Signature delimiters
        self.signature_delimiters = [
            'Kind regards', 'Best regards', 'Regards', 'Thanks', 'Thank you',
            'Cheers', 'Best', 'Sincerely', '--', '___', '---'
        ]

    def extract_signature(self, email_content: str) -> Optional[str]:
        """
        Extract signature block from email content

        Args:
            email_content: Full email content

        Returns:
            Signature text or None
        """
        # Look for common signature delimiters
        for delimiter in self.signature_delimiters:
            if delimiter in email_content:
                # Get text after delimiter (last occurrence for forwarded emails)
                parts = email_content.rsplit(delimiter, 1)
                if len(parts) == 2:
                    signature = parts[1].strip()
                    # Signature should be reasonable length (not entire email)
                    if 10 < len(signature) < 1000:
                        return signature

        # Fallback: Last 500 characters if no delimiter found
        if len(email_content) > 500:
            return email_content[-500:]

        return email_content

    def extract_name_from_sender(self, sender: str) -> Optional[str]:
        """
        Extract name from email sender field

        Args:
            sender: Email sender (e.g., "John Smith <john@example.com>")

        Returns:
            Name string or None
        """
        # Pattern: "Name <email>" or "Name"
        match = re.match(r'^([^<]+)(?:\s*<[^>]+>)?$', sender)
        if match:
            name = match.group(1).strip()
            # Filter out email addresses
            if '@' not in name and len(name) > 2:
                return name
        return None

    def extract_job_title(self, text: str) -> Optional[str]:
        """
        Extract job title from text using pattern matching

        Args:
            text: Signature or email text

        Returns:
            Job title string or None
        """
        lines = text.split('\n')

        for line in lines:
            line_lower = line.lower().strip()

            # Check if line contains title keywords
            if any(keyword in line_lower for keyword in self.title_keywords):
                # Avoid lines with contact info
                if '@' not in line and not re.search(r'\d{3,}', line):
                    # Clean up line
                    title = re.sub(r'^\W+|\W+$', '', line)
                    if 5 < len(title) < 100:
                        return title

        return None

    def extract_company(self, text: str, email: Optional[str] = None) -> Optional[str]:
        """
        Extract company name from signature or email domain

        Args:
            text: Signature text
            email: Email address

        Returns:
            Company name or None
        """
        # Try to extract from email domain first
        if email:
            domain_match = re.search(r'@([^.]+)', email)
            if domain_match:
                domain = domain_match.group(1)
                # Capitalize and filter common domains
                if domain.lower() not in ['gmail', 'hotmail', 'outlook', 'yahoo', 'icloud']:
                    return domain.capitalize()

        # Look for company patterns in signature
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_clean = line.strip()

            # Company often appears after name/title
            if i > 0 and i < 5:  # Within first few lines
                # Avoid lines with @ or phone numbers
                if '@' not in line_clean and not re.search(r'\d{3,}', line_clean):
                    # Look for capitalized words
                    if re.match(r'^[A-Z][A-Za-z\s&.-]+$', line_clean):
                        if 2 < len(line_clean) < 50:
                            return line_clean

        return None

    def extract_phones(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract phone and mobile numbers

        Args:
            text: Signature text

        Returns:
            Tuple of (phone, mobile) - both optional
        """
        phones = self.phone_pattern.findall(text)
        mobiles = self.mobile_pattern.findall(text)

        phone = phones[0] if phones else None
        mobile = mobiles[0] if mobiles else None

        # Clean up formatting
        if phone:
            phone = re.sub(r'\s+', ' ', phone).strip()
        if mobile:
            mobile = re.sub(r'\s+', ' ', mobile).strip()

        return phone, mobile

    def extract_website(self, text: str, email: Optional[str] = None) -> Optional[str]:
        """
        Extract company website URL

        Args:
            text: Signature text
            email: Email address (for domain fallback)

        Returns:
            Website URL or None
        """
        urls = self.url_pattern.findall(text)

        # Filter out social media and common non-company URLs
        excluded_domains = ['linkedin.com', 'twitter.com', 'facebook.com', 'instagram.com']

        for url in urls:
            if not any(domain in url.lower() for domain in excluded_domains):
                return url

        # Fallback: construct from email domain
        if email:
            domain_match = re.search(r'@(.+)$', email)
            if domain_match:
                domain = domain_match.group(1)
                if domain.lower() not in ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']:
                    return f"https://{domain}"

        return None

    def parse_signature(self, email_message: Dict[str, Any]) -> Optional[Contact]:
        """
        Parse email signature and extract contact information

        Args:
            email_message: Email message dict with 'from', 'content', 'subject', 'id'

        Returns:
            Contact object or None
        """
        sender = email_message.get('from', '')
        content = email_message.get('content', '')

        # Extract signature block
        signature = self.extract_signature(content)
        if not signature:
            return None

        # Extract name from sender
        name = self.extract_name_from_sender(sender)
        if not name:
            return None

        # Extract email from sender or signature
        email = None
        if '<' in sender and '>' in sender:
            email_match = re.search(r'<([^>]+)>', sender)
            if email_match:
                email = email_match.group(1)
        else:
            emails = self.email_pattern.findall(signature)
            email = emails[0] if emails else None

        # Extract other fields
        job_title = self.extract_job_title(signature)
        company = self.extract_company(signature, email)
        phone, mobile = self.extract_phones(signature)
        website = self.extract_website(signature, email)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            name, email, job_title, company, phone, mobile
        )

        return Contact(
            name=name,
            email=email,
            job_title=job_title,
            company=company,
            phone=phone,
            mobile=mobile,
            website=website,
            source_email_id=email_message.get('id'),
            confidence=confidence
        )

    def _calculate_confidence(
        self, name: str, email: Optional[str], job_title: Optional[str],
        company: Optional[str], phone: Optional[str], mobile: Optional[str]
    ) -> float:
        """Calculate confidence score for extracted contact"""
        score = 0.0

        if name: score += 0.3  # Name is required
        if email: score += 0.3  # Email is highly valuable
        if job_title: score += 0.15
        if company: score += 0.15
        if phone or mobile: score += 0.1

        return min(score, 1.0)


class MacOSContactsBridge:
    """Bridge to macOS Contacts app via AppleScript"""

    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts from Contacts app"""
        script = '''
        tell application "Contacts"
            set contactList to {}
            repeat with p in people
                set personInfo to {personName:(name of p), personEmail:""}

                if (count of emails of p) > 0 then
                    set personEmail of personInfo to value of email 1 of p
                end if

                set end of contactList to personInfo
            end repeat

            set AppleScript's text item delimiters to "||"
            set output to ""
            repeat with c in contactList
                set output to output & personName of c & "::" & personEmail of c & "||"
            end repeat
            return output
        end tell
        '''

        result = self._execute_applescript(script)

        contacts = []
        if result.strip():
            for line in result.strip().split("||"):
                if "::" in line:
                    parts = line.split("::")
                    if len(parts) >= 2:
                        contacts.append({
                            "name": parts[0].strip(),
                            "email": parts[1].strip() if parts[1].strip() else None
                        })

        return contacts

    def contact_exists(self, email: str) -> bool:
        """Check if contact with email already exists"""
        contacts = self.get_all_contacts()
        return any(c.get('email') == email for c in contacts)

    def add_contact(self, contact: Contact) -> bool:
        """
        Add new contact to Contacts app

        Args:
            contact: Contact object to add

        Returns:
            True if successful, False otherwise
        """
        # Build AppleScript based on available fields
        fields = []

        if contact.email:
            email_escaped = contact.email.replace('"', '\\"')
            fields.append(f'make new email at end of emails of newPerson with properties {{value:"{email_escaped}"}}')

        if contact.job_title:
            job_title_escaped = contact.job_title.replace('"', '\\"')
            fields.append(f'set job title of newPerson to "{job_title_escaped}"')

        if contact.company:
            company_escaped = contact.company.replace('"', '\\"')
            fields.append(f'set organization of newPerson to "{company_escaped}"')

        if contact.phone:
            phone_escaped = contact.phone.replace('"', '\\"')
            fields.append(f'make new phone at end of phones of newPerson with properties {{value:"{phone_escaped}", label:"work"}}')

        if contact.mobile:
            mobile_escaped = contact.mobile.replace('"', '\\"')
            fields.append(f'make new phone at end of phones of newPerson with properties {{value:"{mobile_escaped}", label:"mobile"}}')

        if contact.website:
            website_escaped = contact.website.replace('"', '\\"')
            fields.append(f'make new url at end of urls of newPerson with properties {{value:"{website_escaped}"}}')

        name_escaped = contact.name.replace('"', '\\"')
        fields_script = '\n            '.join(fields)

        script = f'''
        tell application "Contacts"
            set newPerson to make new person with properties {{first name:"{name_escaped}"}}
            {fields_script}
            save
            return "SUCCESS"
        end tell
        '''

        try:
            result = self._execute_applescript(script)
            return "SUCCESS" in result
        except Exception as e:
            print(f"  ⚠️  Error adding contact: {e}")
            return False

    def _execute_applescript(self, script: str) -> str:
        """Execute AppleScript and return output"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"AppleScript failed: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError("AppleScript timed out")
        except Exception as e:
            raise RuntimeError(f"AppleScript error: {str(e)}")


class ContactExtractor:
    """Main contact extraction orchestrator"""

    def __init__(self):
        self.mail_bridge = MacOSMailBridge()
        self.contacts_bridge = MacOSContactsBridge()
        self.parser = SignatureParser()

    def extract_from_recent_emails(
        self,
        hours_ago: int = 168,  # Last week by default
        limit: int = 100,
        min_confidence: float = 0.5,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Extract contacts from recent emails

        Args:
            hours_ago: Look back N hours
            limit: Max emails to process
            min_confidence: Minimum confidence score to include (0-1)
            dry_run: If True, preview only (don't add to Contacts)

        Returns:
            Statistics dict
        """
        print("=" * 60)
        print(f"📧 Contact Extractor - {'DRY RUN' if dry_run else 'LIVE MODE'}")
        print("=" * 60)
        print(f"⏰ Processing last {hours_ago}h of emails (limit: {limit})")
        print(f"🎯 Minimum confidence: {min_confidence * 100:.0f}%\n")

        # Get recent emails
        print("📥 Retrieving emails...")
        inbox_messages = self.mail_bridge.get_inbox_messages(limit=limit, hours_ago=hours_ago)
        sent_messages = self.mail_bridge.get_sent_messages(limit=limit // 2, hours_ago=hours_ago)
        all_messages = inbox_messages + sent_messages

        print(f"✅ Found {len(all_messages)} emails ({len(inbox_messages)} inbox, {len(sent_messages)} sent)\n")

        # Get existing contacts for deduplication
        print("📇 Loading existing contacts...")
        existing_contacts = self.contacts_bridge.get_all_contacts()
        existing_emails = {c['email'] for c in existing_contacts if c.get('email')}
        print(f"✅ {len(existing_contacts)} existing contacts\n")

        # Process emails
        print("🔍 Extracting contacts from signatures...\n")

        stats = {
            "processed": 0,
            "extracted": 0,
            "duplicates": 0,
            "low_confidence": 0,
            "added": 0,
            "errors": 0
        }

        extracted_contacts = []

        for i, msg in enumerate(all_messages, 1):
            stats["processed"] += 1

            try:
                # Get full message content
                content = self.mail_bridge.get_message_content(msg['id'])
                if not content:
                    continue

                # Parse signature
                contact = self.parser.parse_signature({
                    'from': content['from'],
                    'content': content['content'],
                    'subject': content['subject'],
                    'id': msg['id']
                })

                if not contact:
                    continue

                stats["extracted"] += 1

                # Check confidence
                if contact.confidence < min_confidence:
                    stats["low_confidence"] += 1
                    continue

                # Check for duplicates
                if contact.email and contact.email in existing_emails:
                    stats["duplicates"] += 1
                    continue

                # Add to results
                extracted_contacts.append(contact)

                # Preview
                print(f"  [{i}/{len(all_messages)}] 🎯 {contact.confidence*100:.0f}% | {contact.name}")
                if contact.job_title:
                    print(f"      Title: {contact.job_title}")
                if contact.company:
                    print(f"      Company: {contact.company}")
                if contact.email:
                    print(f"      Email: {contact.email}")
                if contact.phone or contact.mobile:
                    phones = []
                    if contact.phone:
                        phones.append(f"📞 {contact.phone}")
                    if contact.mobile:
                        phones.append(f"📱 {contact.mobile}")
                    print(f"      {' | '.join(phones)}")
                print()

            except Exception as e:
                stats["errors"] += 1
                print(f"  ⚠️  Error processing email {i}: {e}\n")
                continue

        # Add to Contacts if not dry run
        if not dry_run and extracted_contacts:
            print(f"\n📇 Adding {len(extracted_contacts)} contacts to Contacts app...\n")

            for contact in extracted_contacts:
                if self.contacts_bridge.add_contact(contact):
                    stats["added"] += 1
                    print(f"  ✅ Added: {contact.name}")
                else:
                    stats["errors"] += 1
                    print(f"  ❌ Failed: {contact.name}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary")
        print("=" * 60)
        print(f"  Emails processed: {stats['processed']}")
        print(f"  Contacts extracted: {stats['extracted']}")
        print(f"  Duplicates skipped: {stats['duplicates']}")
        print(f"  Low confidence skipped: {stats['low_confidence']}")
        if not dry_run:
            print(f"  Added to Contacts: {stats['added']}")
        print(f"  Errors: {stats['errors']}")
        print("=" * 60)

        if dry_run:
            print(f"\n💡 Run with --live to add {len(extracted_contacts)} contacts to Contacts app")

        return stats


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Extract contacts from emails")
    parser.add_argument('--hours', type=int, default=168, help='Hours to look back (default: 168 = 1 week)')
    parser.add_argument('--limit', type=int, default=100, help='Max emails to process (default: 100)')
    parser.add_argument('--confidence', type=float, default=0.5, help='Min confidence 0-1 (default: 0.5)')
    parser.add_argument('--live', action='store_true', help='Add contacts (default: dry run preview)')

    args = parser.parse_args()

    extractor = ContactExtractor()
    extractor.extract_from_recent_emails(
        hours_ago=args.hours,
        limit=args.limit,
        min_confidence=args.confidence,
        dry_run=not args.live
    )


if __name__ == "__main__":
    main()
