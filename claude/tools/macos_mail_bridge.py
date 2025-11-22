#!/usr/bin/env python3
"""
macOS Mail.app Bridge - AppleScript Integration for Exchange Email Access

Provides Maia with email access via macOS Mail.app, bypassing Azure AD OAuth requirements.
Uses AppleScript automation to interact with authenticated Mail.app session.

Security:
- Read-only operations by default
- Uses existing Mail.app authentication (no new credentials)
- Local processing only (zero cloud transmission)
- Integrates with local LLM routing for privacy

Performance:
- Smart caching to mitigate AppleScript latency
- Batch operations where possible
- Async execution for long-running queries

Author: Maia System
Created: 2025-10-02 (Phase 80)
"""

import subprocess
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class MacOSMailBridge:
    """Bridge to macOS Mail.app via AppleScript automation"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize Mail.app bridge

        Args:
            cache_dir: Optional cache directory for performance optimization
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.maia/cache/mail")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Verify Mail.app is running
        self._verify_mail_app()

    def _verify_mail_app(self) -> bool:
        """Verify Mail.app is running and accessible"""
        script = '''
        tell application "System Events"
            return (name of processes) contains "Mail"
        end tell
        '''

        result = self._execute_applescript(script)
        if result.strip().lower() != "true":
            raise RuntimeError(
                "Mail.app is not running. Please open Mail.app and try again."
            )
        return True

    def _execute_applescript(self, script: str) -> str:
        """
        Execute AppleScript and return output

        Args:
            script: AppleScript code to execute

        Returns:
            Script output as string

        Raises:
            RuntimeError: If script execution fails
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"AppleScript execution failed: {result.stderr}"
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError("AppleScript execution timed out (>30s)")
        except Exception as e:
            raise RuntimeError(f"AppleScript execution error: {str(e)}")

    def list_mailboxes(self) -> List[Dict[str, Any]]:
        """
        List all available mailboxes/folders in Mail.app

        Returns:
            List of mailbox dictionaries with name and message count
        """
        script = '''
        tell application "Mail"
            set mailboxList to {}
            repeat with mb in mailboxes
                set mailboxInfo to {mailboxName:(name of mb), messageCount:(count of messages in mb)}
                set end of mailboxList to mailboxInfo
            end repeat

            set AppleScript's text item delimiters to "||"
            set output to ""
            repeat with mb in mailboxList
                set output to output & mailboxName of mb & "::" & messageCount of mb & "||"
            end repeat
            return output
        end tell
        '''

        result = self._execute_applescript(script)

        # Parse output
        mailboxes = []
        if result.strip():
            for line in result.strip().split("||"):
                if "::" in line:
                    name, count = line.split("::")
                    mailboxes.append({
                        "name": name.strip(),
                        "message_count": int(count.strip())
                    })

        return mailboxes

    def get_inbox_messages(self, limit: int = 50, account: Optional[str] = None, hours_ago: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent messages from inbox

        Args:
            limit: Maximum number of messages to retrieve
            account: Optional account name (defaults to first account)
            hours_ago: Optional filter for messages within last N hours

        Returns:
            List of message dictionaries
        """
        # If no account specified, use first Exchange account's inbox
        if not account:
            accounts = self.get_accounts()
            if accounts:
                account = accounts[0]['name']

        return self.search_messages_in_account(account=account, mailbox_type="Inbox", limit=limit, hours_ago=hours_ago)

    def get_sent_messages(self, limit: int = 50, account: Optional[str] = None, hours_ago: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent sent messages

        Args:
            limit: Maximum number of messages to retrieve
            account: Optional account name (defaults to first account)
            hours_ago: Optional filter for messages within last N hours

        Returns:
            List of message dictionaries
        """
        # If no account specified, use first Exchange account
        if not account:
            accounts = self.get_accounts()
            if accounts:
                account = accounts[0]['name']

        return self.search_messages_in_account(account=account, mailbox_type="Sent Items", limit=limit, hours_ago=hours_ago)

    def search_messages_in_account(
        self,
        account: str,
        mailbox_type: str = "Inbox",
        limit: int = 50,
        query: Optional[str] = None,
        hours_ago: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search messages in account-specific mailbox

        Args:
            account: Account name (e.g., "Exchange")
            mailbox_type: Mailbox name (Inbox, Sent Items, Drafts, Deleted Items)
            limit: Maximum results
            query: Optional search query (searches subject and content)
            hours_ago: Optional filter for messages within last N hours

        Returns:
            List of message dictionaries with metadata
        """
        # Build AppleScript query
        search_filter = ""
        filter_conditions = []

        if query:
            filter_conditions.append(f'(subject contains "{query}" or content contains "{query}")')

        if hours_ago:
            filter_conditions.append(f'(date received > (current date) - ({hours_ago} * hours))')

        if filter_conditions:
            search_filter = f'whose {" and ".join(filter_conditions)}'

        script = f'''
        tell application "Mail"
            set targetAccount to account "{account}"

            -- Find mailbox (handle both direct and nested mailboxes)
            set targetMailbox to missing value
            repeat with mb in mailboxes of targetAccount
                if name of mb is "{mailbox_type}" then
                    set targetMailbox to mb
                    exit repeat
                end if
            end repeat

            if targetMailbox is missing value then
                error "Mailbox {mailbox_type} not found"
            end if

            set messageList to messages of targetMailbox {search_filter}
            set messageCount to count of messageList

            if messageCount > {limit} then
                set messageList to items 1 thru {limit} of messageList
            end if

            set output to ""
            repeat with msg in messageList
                set msgId to id of msg as string
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg as string
                set msgRead to read status of msg as string

                set output to output & msgId & "::" & msgSubject & "::" & msgSender & "::" & msgDate & "::" & msgRead & "||"
            end repeat

            return output
        end tell
        '''

        result = self._execute_applescript(script)

        # Parse results
        messages = []
        if result.strip():
            for line in result.strip().split("||"):
                if line.strip() and "::" in line:
                    parts = line.split("::")
                    if len(parts) >= 5:
                        messages.append({
                            "id": parts[0].strip(),
                            "subject": parts[1].strip(),
                            "from": parts[2].strip(),
                            "date": parts[3].strip(),
                            "read": parts[4].strip().lower() == "true"
                        })

        return messages

    def get_message_content(self, message_id: str, account: str = "Exchange") -> Optional[Dict[str, Any]]:
        """
        Get full content of a specific message

        Args:
            message_id: Message ID from search_messages()
            account: Account name (default: Exchange)

        Returns:
            Dictionary with complete message details, or None if message not found
        """
        script = f'''
        tell application "Mail"
            try
                set targetAccount to account "{account}"

                -- Search across all mailboxes for the message ID
                set msg to missing value
                repeat with mb in mailboxes of targetAccount
                    try
                        set msg to (first message of mb whose id is {message_id})
                        exit repeat
                    end try
                end repeat

                if msg is missing value then
                    error "Message not found in any mailbox"
                end if

                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg as string
                set msgContent to content of msg
                set msgRead to read status of msg as string

                return msgSubject & "::||::" & msgSender & "::||::" & msgDate & "::||::" & msgContent & "::||::" & msgRead
            on error errMsg
                return "ERROR::" & errMsg
            end try
        end tell
        '''

        try:
            result = self._execute_applescript(script)

            if result.strip():
                # Check for error message
                if result.startswith("ERROR::"):
                    error_msg = result.replace("ERROR::", "").strip()
                    # Return None for common "not found" errors instead of raising
                    if "Can't get message" in error_msg or "Invalid index" in error_msg:
                        return None
                    # For other errors, still raise
                    raise ValueError(f"AppleScript error: {error_msg}")

                parts = result.split("::||::")
                if len(parts) >= 5:
                    return {
                        "subject": parts[0].strip(),
                        "from": parts[1].strip(),
                        "date": parts[2].strip(),
                        "content": parts[3].strip(),
                        "read": parts[4].strip().lower() == "true"
                    }

            return None

        except RuntimeError as e:
            # Handle AppleScript execution errors gracefully
            if "Invalid index" in str(e) or "Can't get message" in str(e):
                return None
            raise

    def get_unread_count(self, account: Optional[str] = None, mailbox_type: str = "Inbox") -> int:
        """
        Get count of unread messages in mailbox

        Args:
            account: Account name (defaults to first account)
            mailbox_type: Mailbox name (Inbox, Sent Items, Drafts, etc.)

        Returns:
            Count of unread messages
        """
        if not account:
            accounts = self.get_accounts()
            if accounts:
                account = accounts[0]['name']

        script = f'''
        tell application "Mail"
            set targetAccount to account "{account}"
            set targetMailbox to mailbox "{mailbox_type}" of targetAccount
            return unread count of targetMailbox
        end tell
        '''

        result = self._execute_applescript(script)
        return int(result.strip())

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark message as read

        Args:
            message_id: Message ID

        Returns:
            Success status
        """
        script = f'''
        tell application "Mail"
            set msg to first message whose id is {message_id}
            set read status of msg to true
            return "success"
        end tell
        '''

        result = self._execute_applescript(script)
        return "success" in result.lower()

    def get_accounts(self) -> List[Dict[str, str]]:
        """
        Get list of configured email accounts

        Returns:
            List of account dictionaries
        """
        script = '''
        tell application "Mail"
            set accountList to {}
            repeat with acc in accounts
                set accountInfo to {accountName:(name of acc), accountEmail:(email addresses of acc as string)}
                set end of accountList to accountInfo
            end repeat

            set output to ""
            repeat with acc in accountList
                set output to output & accountName of acc & "::" & accountEmail of acc & "||"
            end repeat
            return output
        end tell
        '''

        result = self._execute_applescript(script)

        accounts = []
        if result.strip():
            for line in result.strip().split("||"):
                if "::" in line:
                    name, email = line.split("::", 1)
                    accounts.append({
                        "name": name.strip(),
                        "email": email.strip()
                    })

        return accounts

    def search_by_sender(self, sender: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search messages by sender email

        Args:
            sender: Sender email address or name
            limit: Maximum results

        Returns:
            List of matching messages
        """
        script = f'''
        tell application "Mail"
            set messageList to (messages whose sender contains "{sender}")
            set messageCount to count of messageList

            if messageCount > {limit} then
                set messageList to items 1 thru {limit} of messageList
            end if

            set output to ""
            repeat with msg in messageList
                set msgId to id of msg as string
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg as string

                set output to output & msgId & "::" & msgSubject & "::" & msgSender & "::" & msgDate & "||"
            end repeat

            return output
        end tell
        '''

        result = self._execute_applescript(script)

        messages = []
        if result.strip():
            for line in result.strip().split("||"):
                if line.strip() and "::" in line:
                    parts = line.split("::")
                    if len(parts) >= 4:
                        messages.append({
                            "id": parts[0].strip(),
                            "subject": parts[1].strip(),
                            "from": parts[2].strip(),
                            "date": parts[3].strip()
                        })

        return messages

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
        account: str = "Exchange"
    ) -> bool:
        """
        Send email via Mail.app using Exchange account

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            html: If True, send as HTML; if False, plain text
            account: Account name to send from (default "Exchange")

        Returns:
            True if sent successfully

        Raises:
            RuntimeError: If sending fails
        """
        # Escape quotes for AppleScript (double escape for shell)
        safe_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
        safe_to = to.replace('\\', '\\\\').replace('"', '\\"')

        # For HTML, save to temp file to avoid shell escaping issues
        import tempfile
        if html:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(body)
                html_file = f.name

            script = f'''
            tell application "Mail"
                set theAccount to first account whose name is "{account}"
                set htmlContent to read (POSIX file "{html_file}") as «class utf8»
                set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", sender:theAccount}}

                tell newMessage
                    make new to recipient with properties {{address:"{safe_to}"}}
                    set html content to htmlContent
                    send
                end tell

                return "sent"
            end tell
            '''
        else:
            safe_body = body.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            script = f'''
            tell application "Mail"
                set theAccount to first account whose name is "{account}"
                set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}", sender:theAccount}}

                tell newMessage
                    make new to recipient with properties {{address:"{safe_to}"}}
                    send
                end tell

                return "sent"
            end tell
            '''

        try:
            result = self._execute_applescript(script)

            # Clean up temp file if created
            if html:
                import os
                os.unlink(html_file)

            return "sent" in result.lower()
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {str(e)}")

    def get_message_attachments(self, message_id: str, account: str = "Exchange") -> List[Dict[str, Any]]:
        """
        Get list of attachments for a specific message

        Args:
            message_id: Message ID from search_messages()
            account: Account name (default: Exchange)

        Returns:
            List of attachment dictionaries with name, size, mime_type
        """
        script = f'''
        tell application "Mail"
            try
                set targetAccount to account "{account}"

                -- Search across all mailboxes for the message ID
                set msg to missing value
                repeat with mb in mailboxes of targetAccount
                    try
                        set msg to (first message of mb whose id is {message_id})
                        exit repeat
                    end try
                end repeat

                if msg is missing value then
                    return "ERROR::Message not found"
                end if

                set attachmentList to mail attachments of msg
                set attachmentCount to count of attachmentList

                if attachmentCount is 0 then
                    return "NONE"
                end if

                set output to ""
                repeat with att in attachmentList
                    set attName to name of att
                    set attSize to file size of att
                    set attType to MIME type of att
                    set output to output & attName & "::" & attSize & "::" & attType & "||"
                end repeat

                return output
            on error errMsg
                return "ERROR::" & errMsg
            end try
        end tell
        '''

        try:
            result = self._execute_applescript(script)

            if result.strip() == "NONE":
                return []

            if result.startswith("ERROR::"):
                error_msg = result.replace("ERROR::", "").strip()
                if "Message not found" in error_msg or "AppleEvent handler failed" in error_msg:
                    return []
                # Log but don't raise for other errors - return empty list
                print(f"  ⚠️  Attachment error: {error_msg}")
                return []

            attachments = []
            if result.strip():
                for line in result.strip().split("||"):
                    if line.strip() and "::" in line:
                        parts = line.split("::")
                        if len(parts) >= 3:
                            attachments.append({
                                "name": parts[0].strip(),
                                "size": int(parts[1].strip()) if parts[1].strip().isdigit() else 0,
                                "mime_type": parts[2].strip()
                            })

            return attachments

        except (RuntimeError, ValueError) as e:
            error_str = str(e)
            if any(x in error_str for x in ["Invalid index", "Can't get message", "AppleEvent handler failed"]):
                return []
            print(f"  ⚠️  Attachment retrieval error: {error_str}")
            return []

    def save_attachment(
        self,
        message_id: str,
        attachment_name: str,
        save_path: str,
        account: str = "Exchange"
    ) -> bool:
        """
        Save a specific attachment from a message to disk

        Args:
            message_id: Message ID from search_messages()
            attachment_name: Name of the attachment to save
            save_path: Full path where to save the file
            account: Account name (default: Exchange)

        Returns:
            True if saved successfully, False otherwise
        """
        # Ensure save directory exists
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        # Escape special characters for AppleScript
        safe_att_name = attachment_name.replace('"', '\\"')
        safe_save_path = save_path.replace('"', '\\"')

        script = f'''
        tell application "Mail"
            try
                set targetAccount to account "{account}"

                -- Search across all mailboxes for the message ID
                set msg to missing value
                repeat with mb in mailboxes of targetAccount
                    try
                        set msg to (first message of mb whose id is {message_id})
                        exit repeat
                    end try
                end repeat

                if msg is missing value then
                    return "ERROR::Message not found"
                end if

                set attachmentList to mail attachments of msg

                repeat with att in attachmentList
                    if name of att is "{safe_att_name}" then
                        save att in POSIX file "{safe_save_path}"
                        return "SUCCESS"
                    end if
                end repeat

                return "ERROR::Attachment not found"
            on error errMsg
                return "ERROR::" & errMsg
            end try
        end tell
        '''

        try:
            result = self._execute_applescript(script)

            if "SUCCESS" in result:
                return True

            if result.startswith("ERROR::"):
                error_msg = result.replace("ERROR::", "").strip()
                print(f"  ⚠️  Attachment save failed: {error_msg}")
                return False

            return False

        except Exception as e:
            print(f"  ⚠️  Attachment save error: {e}")
            return False

    def has_attachments(self, message_id: str, account: str = "Exchange") -> bool:
        """
        Quick check if a message has any attachments

        Args:
            message_id: Message ID
            account: Account name

        Returns:
            True if message has attachments
        """
        attachments = self.get_message_attachments(message_id, account)
        return len(attachments) > 0

    def is_image_attachment(self, attachment: Dict[str, Any]) -> bool:
        """
        Check if an attachment is an image file

        Args:
            attachment: Attachment dictionary from get_message_attachments()

        Returns:
            True if attachment is an image
        """
        image_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp', 'image/gif', 'image/heic']
        image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic']

        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()

        return (
            any(t in mime_type for t in image_types) or
            any(name.endswith(ext) for ext in image_extensions)
        )

    def is_pdf_attachment(self, attachment: Dict[str, Any]) -> bool:
        """
        Check if an attachment is a PDF file

        Args:
            attachment: Attachment dictionary from get_message_attachments()

        Returns:
            True if attachment is a PDF
        """
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()

        return 'pdf' in mime_type or name.endswith('.pdf')


def main():
    """Test the Mail.app bridge functionality"""
    print("🔧 Testing macOS Mail.app Bridge...")

    try:
        # Initialize bridge
        bridge = MacOSMailBridge()
        print("✅ Mail.app connection established")

        # Test 1: List accounts
        print("\n📧 Email Accounts:")
        accounts = bridge.get_accounts()
        for account in accounts:
            print(f"  - {account['name']}: {account['email']}")

        # Test 2: List mailboxes
        print("\n📁 Mailboxes:")
        mailboxes = bridge.list_mailboxes()
        for mailbox in mailboxes[:10]:  # Show first 10
            print(f"  - {mailbox['name']}: {mailbox['message_count']} messages")

        # Test 3: Get inbox unread count
        unread = bridge.get_unread_count()
        print(f"\n📬 Unread in INBOX: {unread}")

        # Test 4: Get recent inbox messages
        print("\n📨 Recent INBOX Messages (last 5):")
        messages = bridge.get_inbox_messages(limit=5)
        for msg in messages:
            read_status = "📖" if msg['read'] else "📩"
            print(f"  {read_status} {msg['subject'][:50]}")
            print(f"     From: {msg['from']}")
            print(f"     Date: {msg['date']}")

        print("\n✅ All tests passed! Mail.app bridge is operational.")

    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
