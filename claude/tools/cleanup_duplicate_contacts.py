#!/usr/bin/env python3
"""
Cleanup duplicate contacts in macOS Contacts app

This script finds and removes duplicate contacts based on email address,
keeping only the most complete contact (most fields populated).
"""

import subprocess
import sys
from typing import List, Dict, Any
from collections import defaultdict


class ContactsCleaner:
    """Remove duplicate contacts from macOS Contacts app"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def _execute_applescript(self, script: str) -> str:
        """Execute AppleScript and return result"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript error: {e.stderr}")

    def get_all_contacts_detailed(self) -> List[Dict[str, Any]]:
        """Get all contacts with detailed info"""
        script = '''
        tell application "Contacts"
            set contactList to {}
            repeat with p in people
                set personId to id of p
                set personName to name of p
                set personEmail to ""
                set personPhone to ""
                set personCompany to ""
                set personTitle to ""
                set fieldCount to 0

                if (count of emails of p) > 0 then
                    set personEmail to value of email 1 of p
                    set fieldCount to fieldCount + 1
                end if

                if (count of phones of p) > 0 then
                    set personPhone to value of phone 1 of p
                    set fieldCount to fieldCount + 1
                end if

                try
                    set personCompany to organization of p
                    if personCompany is not "" then
                        set fieldCount to fieldCount + 1
                    end if
                end try

                try
                    set personTitle to job title of p
                    if personTitle is not "" then
                        set fieldCount to fieldCount + 1
                    end if
                end try

                set personInfo to {personId:personId, personName:personName, personEmail:personEmail, personPhone:personPhone, personCompany:personCompany, personTitle:personTitle, fieldCount:fieldCount}
                set end of contactList to personInfo
            end repeat

            set AppleScript's text item delimiters to "||"
            set output to ""
            repeat with c in contactList
                set output to output & personId of c & "::" & personName of c & "::" & personEmail of c & "::" & personPhone of c & "::" & personCompany of c & "::" & personTitle of c & "::" & fieldCount of c & "||"
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
                    if len(parts) >= 7:
                        contacts.append({
                            "id": parts[0].strip(),
                            "name": parts[1].strip(),
                            "email": parts[2].strip() if parts[2].strip() else None,
                            "phone": parts[3].strip() if parts[3].strip() else None,
                            "company": parts[4].strip() if parts[4].strip() else None,
                            "title": parts[5].strip() if parts[5].strip() else None,
                            "field_count": int(parts[6].strip()) if parts[6].strip() else 0
                        })

        return contacts

    def delete_contact_by_id(self, contact_id: str) -> bool:
        """Delete a contact by its ID"""
        script = f'''
        tell application "Contacts"
            delete (first person whose id is "{contact_id}")
            save
            return "SUCCESS"
        end tell
        '''

        try:
            result = self._execute_applescript(script)
            return "SUCCESS" in result
        except Exception as e:
            print(f"  ⚠️  Error deleting contact: {e}")
            return False

    def find_duplicates(self, contacts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicate contacts by email or name (for contacts without email)"""
        groups = defaultdict(list)

        for contact in contacts:
            if contact['email']:
                # Group by email if available
                key = f"email:{contact['email']}"
                groups[key].append(contact)
            else:
                # Group by name if no email
                key = f"name:{contact['name']}"
                groups[key].append(contact)

        # Only return groups with duplicates
        return {key: group for key, group in groups.items() if len(group) > 1}

    def select_best_contact(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select the best contact from duplicates

        Priority:
        1. Most fields populated (field_count)
        2. If tied, keep first one (arbitrary but consistent)
        """
        return max(duplicates, key=lambda c: c['field_count'])

    def cleanup(self) -> Dict[str, Any]:
        """Find and remove duplicate contacts"""
        print("=" * 60)
        print(f"🧹 Contact Duplicate Cleanup - {'DRY RUN' if self.dry_run else 'LIVE MODE'}")
        print("=" * 60)

        # Get all contacts
        print("\n📇 Loading contacts...")
        contacts = self.get_all_contacts_detailed()
        print(f"✅ Found {len(contacts)} total contacts\n")

        # Find duplicates
        print("🔍 Finding duplicates...")
        duplicate_groups = self.find_duplicates(contacts)

        if not duplicate_groups:
            print("✅ No duplicates found!\n")
            return {"total": len(contacts), "duplicates": 0, "deleted": 0}

        print(f"⚠️  Found {len(duplicate_groups)} groups with duplicates\n")

        stats = {
            "total": len(contacts),
            "duplicate_groups": len(duplicate_groups),
            "duplicate_contacts": sum(len(group) - 1 for group in duplicate_groups.values()),
            "deleted": 0,
            "errors": 0
        }

        # Process each duplicate group
        for key, duplicates in duplicate_groups.items():
            best = self.select_best_contact(duplicates)
            to_delete = [c for c in duplicates if c['id'] != best['id']]

            # Format display based on key type
            if key.startswith("email:"):
                display_key = f"📧 {key.replace('email:', '')}"
            else:
                display_key = f"👤 {key.replace('name:', '')}"

            print(f"{display_key} ({len(duplicates)} copies)")
            print(f"   ✅ KEEP: {best['name']} (ID: {best['id'][:8]}..., {best['field_count']} fields)")

            for contact in to_delete:
                print(f"   ❌ DELETE: {contact['name']} (ID: {contact['id'][:8]}..., {contact['field_count']} fields)")

                if not self.dry_run:
                    if self.delete_contact_by_id(contact['id']):
                        stats["deleted"] += 1
                    else:
                        stats["errors"] += 1

            print()

        # Summary
        print("=" * 60)
        print("📊 Summary")
        print("=" * 60)
        print(f"  Total contacts: {stats['total']}")
        print(f"  Duplicate groups: {stats['duplicate_groups']}")
        print(f"  Duplicate contacts to remove: {stats['duplicate_contacts']}")

        if not self.dry_run:
            print(f"  Deleted: {stats['deleted']}")
            print(f"  Errors: {stats['errors']}")
        else:
            print(f"\n💡 Run with --live to actually delete duplicates")

        print("=" * 60)

        return stats


def main():
    """Main entry point"""
    dry_run = "--live" not in sys.argv

    cleaner = ContactsCleaner(dry_run=dry_run)
    cleaner.cleanup()


if __name__ == "__main__":
    main()
