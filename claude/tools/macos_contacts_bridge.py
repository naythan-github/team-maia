#!/usr/bin/env python3
"""
macOS Contacts Bridge - AppleScript Integration
Provides read-only access to macOS Contacts.app via AppleScript automation.

Enables stakeholder intelligence, relationship mapping, and email sender enrichment
for Personal Assistant Agent workflows.

Author: Maia Personal Assistant Agent
Phase: 84 - Contacts Intelligence Integration
Date: 2025-10-03
"""

import subprocess
import json
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MacOSContactsBridge:
    """Bridge to macOS Contacts.app using AppleScript automation."""

    def __init__(self, timeout: int = 30):
        """
        Initialize Contacts bridge.

        Args:
            timeout: Timeout for AppleScript commands (seconds)
        """
        self.timeout = timeout

    def _run_applescript(self, script: str) -> Tuple[bool, str]:
        """
        Execute AppleScript and return results.

        Args:
            script: AppleScript code to execute

        Returns:
            Tuple of (success, output/error)
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                logger.error(f"AppleScript error: {result.stderr}")
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript timeout after {self.timeout}s")
            return False, f"Command timeout after {self.timeout}s"
        except Exception as e:
            logger.error(f"AppleScript execution error: {e}")
            return False, str(e)

    def get_contact_count(self) -> int:
        """
        Get total contact count.

        Returns:
            Number of contacts
        """
        script = 'tell application "Contacts" to count every person'
        success, output = self._run_applescript(script)

        if success:
            try:
                return int(output)
            except ValueError:
                logger.error(f"Invalid count: {output}")
                return 0
        return 0

    def search_by_email(self, email: str) -> Optional[Dict]:
        """
        Search for contact by email address.

        Args:
            email: Email address to search

        Returns:
            Contact dictionary or None if not found
        """
        script = f'''
        tell application "Contacts"
            set searchEmail to "{email}"
            set matchingPeople to {{}}
            repeat with aPerson in people
                repeat with anEmail in emails of aPerson
                    if value of anEmail contains searchEmail then
                        set end of matchingPeople to aPerson
                        exit repeat
                    end if
                end repeat
            end repeat

            if (count of matchingPeople) > 0 then
                set thePerson to item 1 of matchingPeople
                set firstName to first name of thePerson
                set lastName to last name of thePerson
                set companyName to organization of thePerson
                set jobTitle to job title of thePerson
                set phoneNumbers to ""
                repeat with aPhone in phones of thePerson
                    set phoneNumbers to phoneNumbers & (value of aPhone) & ","
                end repeat
                set emailAddresses to ""
                repeat with anEmail in emails of thePerson
                    set emailAddresses to emailAddresses & (value of anEmail) & ","
                end repeat
                set noteText to note of thePerson

                return firstName & "|" & lastName & "|" & companyName & "|" & jobTitle & "|" & phoneNumbers & "|" & emailAddresses & "|" & noteText
            else
                return "NOT_FOUND"
            end if
        end tell
        '''

        success, output = self._run_applescript(script)

        if not success or output == "NOT_FOUND":
            logger.info(f"No contact found for email: {email}")
            return None

        try:
            parts = output.split('|')
            if len(parts) >= 7:
                return {
                    'first_name': parts[0] if parts[0] != 'missing value' else '',
                    'last_name': parts[1] if parts[1] != 'missing value' else '',
                    'full_name': f"{parts[0]} {parts[1]}".strip(),
                    'company': parts[2] if parts[2] != 'missing value' else '',
                    'job_title': parts[3] if parts[3] != 'missing value' else '',
                    'phones': [p for p in parts[4].split(',') if p and p != 'missing value'],
                    'emails': [e for e in parts[5].split(',') if e and e != 'missing value'],
                    'notes': parts[6] if parts[6] != 'missing value' else ''
                }
        except Exception as e:
            logger.error(f"Failed to parse contact: {e}")
            return None

        return None

    def search_by_name(self, name: str) -> List[Dict]:
        """
        Search contacts by name (partial match).

        Args:
            name: Name to search (first or last name)

        Returns:
            List of matching contact dictionaries
        """
        script = f'''
        tell application "Contacts"
            set searchName to "{name}"
            set matchingPeople to (every person whose name contains searchName)

            set resultList to {{}}
            repeat with thePerson in matchingPeople
                set firstName to first name of thePerson
                set lastName to last name of thePerson
                set companyName to organization of thePerson
                set jobTitle to job title of thePerson
                set emailCount to count of emails of thePerson

                set personInfo to firstName & "|" & lastName & "|" & companyName & "|" & jobTitle & "|" & emailCount
                set end of resultList to personInfo
            end repeat

            return resultList
        end tell
        '''

        success, output = self._run_applescript(script)

        if not success or not output:
            logger.info(f"No contacts found for name: {name}")
            return []

        contacts = []
        for line in output.split(', '):
            try:
                parts = line.split('|')
                if len(parts) >= 5:
                    contacts.append({
                        'first_name': parts[0] if parts[0] != 'missing value' else '',
                        'last_name': parts[1] if parts[1] != 'missing value' else '',
                        'full_name': f"{parts[0]} {parts[1]}".strip(),
                        'company': parts[2] if parts[2] != 'missing value' else '',
                        'job_title': parts[3] if parts[3] != 'missing value' else '',
                        'email_count': int(parts[4]) if parts[4].isdigit() else 0
                    })
            except Exception as e:
                logger.warning(f"Failed to parse contact: {e}")
                continue

        logger.info(f"Found {len(contacts)} contacts matching '{name}'")
        return contacts

    def search_by_company(self, company: str) -> List[Dict]:
        """
        Search contacts by company/organization.

        Args:
            company: Company name to search

        Returns:
            List of matching contact dictionaries
        """
        script = f'''
        tell application "Contacts"
            set searchCompany to "{company}"
            set matchingPeople to (every person whose organization contains searchCompany)

            set resultList to {{}}
            repeat with thePerson in matchingPeople
                set firstName to first name of thePerson
                set lastName to last name of thePerson
                set companyName to organization of thePerson
                set jobTitle to job title of thePerson

                set personInfo to firstName & "|" & lastName & "|" & companyName & "|" & jobTitle
                set end of resultList to personInfo
            end repeat

            return resultList
        end tell
        '''

        success, output = self._run_applescript(script)

        if not success or not output:
            logger.info(f"No contacts found for company: {company}")
            return []

        contacts = []
        for line in output.split(', '):
            try:
                parts = line.split('|')
                if len(parts) >= 4:
                    contacts.append({
                        'first_name': parts[0] if parts[0] != 'missing value' else '',
                        'last_name': parts[1] if parts[1] != 'missing value' else '',
                        'full_name': f"{parts[0]} {parts[1]}".strip(),
                        'company': parts[2] if parts[2] != 'missing value' else '',
                        'job_title': parts[3] if parts[3] != 'missing value' else ''
                    })
            except Exception as e:
                logger.warning(f"Failed to parse contact: {e}")
                continue

        logger.info(f"Found {len(contacts)} contacts at '{company}'")
        return contacts

    def get_recent_contacts(self, limit: int = 10) -> List[Dict]:
        """
        Get recently modified contacts.

        Args:
            limit: Maximum number of contacts to return

        Returns:
            List of recent contact dictionaries
        """
        script = f'''
        tell application "Contacts"
            set recentPeople to people

            set resultList to {{}}
            set counter to 0
            repeat with thePerson in recentPeople
                if counter ≥ {limit} then exit repeat

                set firstName to first name of thePerson
                set lastName to last name of thePerson
                set companyName to organization of thePerson
                set modDate to modification date of thePerson

                set personInfo to firstName & "|" & lastName & "|" & companyName & "|" & (modDate as string)
                set end of resultList to personInfo
                set counter to counter + 1
            end repeat

            return resultList
        end tell
        '''

        success, output = self._run_applescript(script)

        if not success or not output:
            logger.info("No recent contacts found")
            return []

        contacts = []
        for line in output.split(', '):
            try:
                parts = line.split('|')
                if len(parts) >= 4:
                    contacts.append({
                        'first_name': parts[0] if parts[0] != 'missing value' else '',
                        'last_name': parts[1] if parts[1] != 'missing value' else '',
                        'full_name': f"{parts[0]} {parts[1]}".strip(),
                        'company': parts[2] if parts[2] != 'missing value' else '',
                        'modification_date': parts[3]
                    })
            except Exception as e:
                logger.warning(f"Failed to parse contact: {e}")
                continue

        logger.info(f"Retrieved {len(contacts)} recent contacts")
        return contacts

    def enrich_email_sender(self, email: str, sender_name: Optional[str] = None) -> Dict:
        """
        Enrich email sender with contact information.

        Args:
            email: Sender email address
            sender_name: Optional sender name from email

        Returns:
            Enriched contact information
        """
        # Try email lookup first
        contact = self.search_by_email(email)

        if contact:
            return {
                'found': True,
                'source': 'email_match',
                'contact': contact
            }

        # Try name lookup if provided
        if sender_name:
            contacts = self.search_by_name(sender_name)
            if contacts:
                return {
                    'found': True,
                    'source': 'name_match',
                    'contact': contacts[0],  # Return best match
                    'alternatives': contacts[1:] if len(contacts) > 1 else []
                }

        return {
            'found': False,
            'source': 'not_found',
            'email': email,
            'name': sender_name
        }


def main():
    """Test contacts bridge functionality."""
    bridge = MacOSContactsBridge()

    print("\n=== macOS Contacts Bridge Test ===\n")

    # Get total count
    total = bridge.get_contact_count()
    print(f"📇 Total Contacts: {total}")

    # Search by company (Orro)
    print("\n🏢 Orro Group Contacts:")
    orro_contacts = bridge.search_by_company("Orro")
    for contact in orro_contacts[:10]:  # Show first 10
        print(f"  • {contact['full_name']}")
        if contact['job_title']:
            print(f"    {contact['job_title']}")

    # Test email enrichment
    print("\n📧 Email Enrichment Test:")
    test_email = "naythan.dawe@orro.group"
    enriched = bridge.enrich_email_sender(test_email)

    if enriched['found']:
        contact = enriched['contact']
        print(f"  ✅ Found: {contact['full_name']}")
        if contact['company']:
            print(f"     Company: {contact['company']}")
        if contact['job_title']:
            print(f"     Title: {contact['job_title']}")
    else:
        print(f"  ❌ Not found: {test_email}")

    # Export recent contacts to JSON
    print("\n💾 Exporting recent contacts to JSON...")
    recent = bridge.get_recent_contacts(limit=50)

    output_file = '/Users/naythandawe/git/maia/claude/data/contacts_export.json'
    with open(output_file, 'w') as f:
        json.dump(recent, f, indent=2, default=str)

    print(f"✅ Exported {len(recent)} contacts to {output_file}")


if __name__ == '__main__':
    main()
