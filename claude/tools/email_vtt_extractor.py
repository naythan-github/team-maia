#!/usr/bin/env python3
"""
Email VTT Extractor - Automatically extract and process VTT attachments from email
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from macos_mail_bridge import MacOSMailBridge


class EmailVTTExtractor:
    def __init__(self):
        self.mail_bridge = MacOSMailBridge()
        self.vtt_folder = Path.home() / "Library" / "CloudStorage" / "OneDrive-YOUR_ORG" / "Documents" / "1-VTT"
        self.state_file = Path.home() / ".maia" / "email_vtt_extractor_state.json"
        self.state = self._load_state()

        # Ensure VTT folder exists
        self.vtt_folder.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict:
        """Load tracking state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "processed_message_ids": [],
            "extracted_files": {},
            "last_check": None
        }

    def _save_state(self):
        """Save tracking state"""
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def find_vtt_attachments(self, limit: int = 100) -> List[Dict]:
        """Find emails with VTT attachments"""
        print("📧 Searching emails for VTT attachments...")

        # AppleScript to find emails with .vtt attachments
        script = f'''
        tell application "Mail"
            set vttEmails to {{}}
            set recentMessages to messages of inbox whose date received > (current date) - (30 * days)

            repeat with msg in recentMessages
                try
                    set msgAttachments to mail attachments of msg
                    repeat with att in msgAttachments
                        set attName to name of att
                        if attName ends with ".vtt" then
                            set msgId to id of msg
                            set msgSubject to subject of msg
                            set msgSender to sender of msg
                            set msgDate to date received of msg as string
                            set attSize to (size of att) as string

                            set emailInfo to msgId & "|||" & msgSubject & "|||" & msgSender & "|||" & msgDate & "|||" & attName & "|||" & attSize
                            set end of vttEmails to emailInfo
                        end if
                    end repeat
                end try
            end repeat

            return vttEmails
        end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ Error searching emails: {result.stderr}")
                return []

            output = result.stdout.strip()
            if not output:
                return []

            # Parse results
            vtt_emails = []
            for line in output.split(', '):
                parts = line.split('|||')
                if len(parts) >= 6:
                    vtt_emails.append({
                        'message_id': parts[0],
                        'subject': parts[1],
                        'sender': parts[2],
                        'date': parts[3],
                        'attachment_name': parts[4],
                        'attachment_size': parts[5]
                    })

            return vtt_emails

        except subprocess.TimeoutExpired:
            print("❌ Search timeout")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def extract_vtt_attachment(self, message_id: str, attachment_name: str) -> Optional[Path]:
        """Extract VTT attachment from email message"""
        print(f"📥 Extracting: {attachment_name}...")

        # Sanitize filename
        safe_filename = attachment_name.replace('/', '_').replace('\\', '_')
        output_path = self.vtt_folder / safe_filename

        # AppleScript to save attachment
        script = f'''
        tell application "Mail"
            set targetMsg to first message whose id is {message_id}
            set msgAttachments to mail attachments of targetMsg

            repeat with att in msgAttachments
                if name of att is "{attachment_name}" then
                    save att in POSIX file "{output_path}"
                    return "success"
                end if
            end repeat

            return "not_found"
        end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and 'success' in result.stdout:
                if output_path.exists():
                    print(f"✅ Saved to: {output_path}")
                    return output_path
                else:
                    print(f"⚠️  Save reported success but file not found")
                    return None
            else:
                print(f"❌ Failed to extract: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Error extracting attachment: {e}")
            return None

    def trigger_vtt_processing(self, vtt_file: Path) -> bool:
        """Trigger VTT watcher to process the file"""
        print(f"🔄 Triggering VTT intelligence pipeline...")

        # The VTT watcher should pick this up automatically via file system events
        # But we can also manually trigger the intelligence pipeline
        try:
            pipeline_script = Path(__file__).parent / "vtt_intelligence_pipeline.py"
            if pipeline_script.exists():
                result = subprocess.run(
                    ['python3', str(pipeline_script), str(vtt_file)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    print(f"✅ VTT processing complete")
                    return True
                else:
                    print(f"⚠️  VTT processing had issues: {result.stderr[:200]}")
                    return False
            else:
                print(f"⚠️  Pipeline script not found, relying on VTT watcher")
                return True

        except Exception as e:
            print(f"⚠️  Error triggering processing: {e}")
            # Not a critical failure - watcher will pick it up
            return True

    def run_extraction(self):
        """Run full extraction process"""
        print("\n" + "="*80)
        print("🎯 EMAIL VTT EXTRACTOR")
        print("="*80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Find VTT attachments
        vtt_emails = self.find_vtt_attachments()

        if not vtt_emails:
            print("✅ No VTT attachments found in recent emails")
            self.state['last_check'] = datetime.now().isoformat()
            self._save_state()
            return

        print(f"\n📎 Found {len(vtt_emails)} email(s) with VTT attachments:\n")

        extracted_count = 0
        skipped_count = 0

        for email in vtt_emails:
            message_id = email['message_id']
            attachment_name = email['attachment_name']

            # Skip if already processed
            if message_id in self.state['processed_message_ids']:
                print(f"⏭️  Skipping (already processed): {attachment_name}")
                skipped_count += 1
                continue

            print(f"\n📧 Email: {email['subject']}")
            print(f"   From: {email['sender']}")
            print(f"   Date: {email['date']}")
            print(f"   Attachment: {attachment_name} ({email['attachment_size']} bytes)")

            # Extract attachment
            vtt_path = self.extract_vtt_attachment(message_id, attachment_name)

            if vtt_path:
                # Trigger processing
                self.trigger_vtt_processing(vtt_path)

                # Track extraction
                self.state['processed_message_ids'].append(message_id)
                self.state['extracted_files'][message_id] = {
                    'filename': attachment_name,
                    'path': str(vtt_path),
                    'extracted_at': datetime.now().isoformat(),
                    'subject': email['subject'],
                    'sender': email['sender']
                }

                extracted_count += 1
                print(f"✅ Successfully extracted and queued for processing\n")
            else:
                print(f"❌ Failed to extract attachment\n")

        # Save state
        self.state['last_check'] = datetime.now().isoformat()
        self._save_state()

        # Summary
        print("\n" + "="*80)
        print(f"📊 SUMMARY:")
        print(f"   • Extracted: {extracted_count}")
        print(f"   • Skipped: {skipped_count}")
        print(f"   • Total Found: {len(vtt_emails)}")
        print("="*80 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract VTT files from email attachments")
    parser.add_argument('--force', action='store_true', help='Re-process already extracted files')

    args = parser.parse_args()

    extractor = EmailVTTExtractor()

    if args.force:
        print("⚠️  Force mode: Clearing processed message IDs")
        extractor.state['processed_message_ids'] = []

    extractor.run_extraction()


if __name__ == '__main__':
    main()
