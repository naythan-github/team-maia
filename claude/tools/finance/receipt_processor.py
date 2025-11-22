#!/usr/bin/env python3
"""
Receipt Processor - Email → OCR → Confluence Pipeline

Orchestrates the full receipt processing workflow:
1. Detect receipt emails (from naythan.general@icloud.com, no subject, with attachment)
2. Extract image/PDF attachments
3. OCR the attachments
4. Parse structured receipt data
5. Update Confluence page with receipt log

Author: SRE Principal Engineer Agent (Maia)
Created: 2025-11-22
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add parent paths for imports
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.finance.receipt_ocr import ReceiptOCR
from claude.tools.finance.vision_ocr import HybridOCR, VisionOCR, VISION_AVAILABLE
from claude.tools.finance.receipt_parser import ReceiptParser, Receipt
from claude.tools.macos_mail_bridge import MacOSMailBridge
from claude.tools.confluence_client import ConfluenceClient


@dataclass
class ProcessingResult:
    """Result of processing a single receipt email"""
    email_id: str
    email_subject: str
    email_sender: str
    attachment_name: str
    success: bool
    receipt: Optional[Receipt] = None
    error: Optional[str] = None


class ReceiptProcessor:
    """
    Main orchestrator for receipt processing pipeline

    Example:
        processor = ReceiptProcessor()
        results = processor.process_new_receipts()
        print(f"Processed {len(results)} receipts")
    """

    # Receipt email detection criteria
    RECEIPT_SENDER = "naythan.general@icloud.com"

    # Confluence settings
    CONFLUENCE_SPACE = "NAYT"
    CONFLUENCE_PAGE_TITLE = "Work Expense Receipts 2025"

    # Processed receipts tracking
    STATE_FILE = os.path.join(MAIA_ROOT, "claude", "data", "finance", "processed_receipts.json")

    def __init__(self, use_vision: bool = True):
        """
        Initialize processor components

        Args:
            use_vision: Use Apple Vision OCR (Neural Engine) when available
        """
        self.mail_bridge = MacOSMailBridge()

        # Use HybridOCR (Vision + Tesseract fallback) for best accuracy
        if use_vision and VISION_AVAILABLE:
            self.ocr = HybridOCR(confidence_threshold=80.0)
            print("✅ Using Vision OCR (Neural Engine) with Tesseract fallback")
        else:
            self.ocr = ReceiptOCR()
            print("⚠️  Using Tesseract OCR (Vision unavailable)")

        self.parser = ReceiptParser()
        self.confluence = ConfluenceClient()

        # Load processed state
        self._state = self._load_state()

        # Ensure state directory exists
        os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        """Load processed receipts state"""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"processed_emails": {}, "receipts": [], "last_run": None}

    def _save_state(self):
        """Save processed receipts state"""
        self._state["last_run"] = datetime.now().isoformat()
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self._state, f, indent=2, default=str)

    def is_receipt_email(self, email: Dict[str, Any]) -> bool:
        """
        Check if email matches receipt criteria

        Criteria:
        - From naythan.general@icloud.com
        - No subject (or empty subject)
        - Has image/PDF attachment
        """
        sender = email.get('from', '').lower()
        subject = email.get('subject', '').strip()

        # Check sender
        if self.RECEIPT_SENDER.lower() not in sender:
            return False

        # Check subject is empty
        if subject:
            return False

        # Check for attachments (done later when we have message_id)
        return True

    def find_receipt_emails(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Find emails that match receipt criteria

        Args:
            hours_ago: Look back period in hours

        Returns:
            List of matching email dictionaries
        """
        print(f"🔍 Searching for receipt emails from {self.RECEIPT_SENDER}...")

        # Search Exchange inbox for emails FROM iCloud sender
        # (receipts forwarded from personal iCloud to work Exchange)
        try:
            messages = self.mail_bridge.get_inbox_messages(limit=100, hours_ago=hours_ago)
        except Exception as e:
            print(f"  ⚠️  Inbox search failed: {e}")
            messages = []

        receipt_emails = []
        for msg in messages:
            # Check sender
            if self.RECEIPT_SENDER.lower() not in msg.get('from', '').lower():
                continue

            # Check subject is empty
            if msg.get('subject', '').strip():
                continue

            # Check if already processed
            if msg['id'] in self._state.get("processed_emails", {}):
                continue

            # Check for image/PDF attachments
            attachments = self.mail_bridge.get_message_attachments(msg['id'], account="Exchange")
            valid_attachments = [
                a for a in attachments
                if self.mail_bridge.is_image_attachment(a) or self.mail_bridge.is_pdf_attachment(a)
            ]

            if valid_attachments:
                msg['attachments'] = valid_attachments
                receipt_emails.append(msg)

        print(f"   Found {len(receipt_emails)} new receipt emails")
        return receipt_emails

    def process_email(self, email: Dict[str, Any]) -> List[ProcessingResult]:
        """
        Process a single receipt email

        Args:
            email: Email dictionary with attachments

        Returns:
            List of ProcessingResult (one per attachment)
        """
        results = []
        email_id = email['id']
        email_subject = email.get('subject', '')
        email_sender = email.get('from', '')
        email_date_str = email.get('date', '')

        # Parse email date
        try:
            from dateutil import parser as date_parser
            email_date = date_parser.parse(email_date_str)
        except Exception:
            email_date = datetime.now()

        for attachment in email.get('attachments', []):
            att_name = attachment['name']
            print(f"  📎 Processing: {att_name}")

            try:
                # Save attachment to temp file
                with tempfile.NamedTemporaryFile(
                    suffix=Path(att_name).suffix,
                    delete=False
                ) as tmp:
                    tmp_path = tmp.name

                # Extract attachment
                saved = self.mail_bridge.save_attachment(
                    message_id=email_id,
                    attachment_name=att_name,
                    save_path=tmp_path,
                    account="Exchange"
                )

                if not saved:
                    results.append(ProcessingResult(
                        email_id=email_id,
                        email_subject=email_subject,
                        email_sender=email_sender,
                        attachment_name=att_name,
                        success=False,
                        error="Failed to save attachment"
                    ))
                    continue

                # OCR the attachment
                print(f"     🔍 Running OCR...")
                ocr_result = self.ocr.extract_with_preprocessing(tmp_path)

                if not ocr_result.success:
                    results.append(ProcessingResult(
                        email_id=email_id,
                        email_subject=email_subject,
                        email_sender=email_sender,
                        attachment_name=att_name,
                        success=False,
                        error=f"OCR failed: {ocr_result.error}"
                    ))
                    continue

                print(f"     ✅ OCR confidence: {ocr_result.confidence:.1f}%")

                # Parse receipt data
                receipt = self.parser.parse(ocr_result.text, ocr_result.confidence)
                receipt.email_id = email_id
                receipt.email_subject = email_subject
                receipt.email_date = email_date
                receipt.attachment_name = att_name

                print(f"     📝 Vendor: {receipt.vendor}")
                print(f"     💰 Total: ${receipt.total_amount}")

                results.append(ProcessingResult(
                    email_id=email_id,
                    email_subject=email_subject,
                    email_sender=email_sender,
                    attachment_name=att_name,
                    success=True,
                    receipt=receipt
                ))

                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            except Exception as e:
                results.append(ProcessingResult(
                    email_id=email_id,
                    email_subject=email_subject,
                    email_sender=email_sender,
                    attachment_name=att_name,
                    success=False,
                    error=str(e)
                ))

        # Mark email as processed
        self._state.setdefault("processed_emails", {})[email_id] = {
            "processed_at": datetime.now().isoformat(),
            "attachments": len(email.get('attachments', []))
        }

        return results

    def update_confluence_page(self, receipts: List[Receipt]) -> Optional[str]:
        """
        Update Confluence page with new receipts

        Args:
            receipts: List of Receipt objects to add

        Returns:
            Page URL if successful, None otherwise
        """
        if not receipts:
            return None

        print(f"\n📄 Updating Confluence page: {self.CONFLUENCE_PAGE_TITLE}")

        # Build markdown content
        now = datetime.now()

        # Calculate totals
        total_amount = sum(r.total_amount for r in receipts if r.total_amount)
        total_gst = sum(r.gst_amount for r in receipts if r.gst_amount)

        # Load existing receipts from state
        existing_receipts = self._state.get("receipts", [])

        # Add new receipts
        for receipt in receipts:
            existing_receipts.append(receipt.to_dict())

        # Recalculate YTD totals
        ytd_total = Decimal('0')
        ytd_gst = Decimal('0')
        for r in existing_receipts:
            try:
                ytd_total += Decimal(r.get('total_amount', '0'))
                if r.get('gst_amount'):
                    ytd_gst += Decimal(r.get('gst_amount', '0'))
            except Exception:
                pass

        # Build page content
        markdown = f"""# Work Expense Receipts 2025

**Last Updated**: {now.strftime('%d %b %Y %H:%M')}
**Total YTD**: ${ytd_total:.2f} | **GST Claimable**: ${ytd_gst:.2f}

## Receipt Log

| Date | Vendor | Amount | GST | Category | Submitted | Approved |
|------|--------|--------|-----|----------|-----------|----------|
"""

        # Add all receipts (newest first)
        sorted_receipts = sorted(
            existing_receipts,
            key=lambda r: r.get('date') or r.get('processed_at') or '',
            reverse=True
        )

        for r in sorted_receipts:
            date_str = "Unknown"
            if r.get('date'):
                try:
                    from dateutil import parser as date_parser
                    date_str = date_parser.parse(r['date']).strftime('%d %b %Y')
                except Exception:
                    date_str = r['date']

            gst_str = f"${Decimal(r.get('gst_amount', '0')):.2f}" if r.get('gst_amount') else "-"
            amount_str = f"${Decimal(r.get('total_amount', '0')):.2f}"

            markdown += f"| {date_str} | {r.get('vendor', 'Unknown')} | {amount_str} | {gst_str} | {r.get('category', '-')} | | |\n"

        markdown += """
---
*Auto-generated by Maia Receipt Processor*
"""

        try:
            # Try to update existing page, create if not exists
            url = self.confluence.update_page_from_markdown(
                space_key=self.CONFLUENCE_SPACE,
                title=self.CONFLUENCE_PAGE_TITLE,
                markdown_content=markdown
            )
            print(f"   ✅ Page updated: {url}")

            # Save state with all receipts
            self._state["receipts"] = existing_receipts
            self._save_state()

            return url

        except Exception as e:
            # Try creating new page
            try:
                url = self.confluence.create_page_from_markdown(
                    space_key=self.CONFLUENCE_SPACE,
                    title=self.CONFLUENCE_PAGE_TITLE,
                    markdown_content=markdown
                )
                print(f"   ✅ Page created: {url}")

                self._state["receipts"] = existing_receipts
                self._save_state()

                return url
            except Exception as e2:
                print(f"   ❌ Failed to update Confluence: {e2}")
                return None

    def process_new_receipts(self, hours_ago: int = 24) -> Dict[str, Any]:
        """
        Main entry point: Process all new receipt emails

        Args:
            hours_ago: Look back period

        Returns:
            Statistics dictionary
        """
        print("=" * 60)
        print("🧾 Receipt Processor - Email → OCR → Confluence")
        print("=" * 60)

        stats = {
            "emails_found": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "confluence_updated": False,
            "confluence_url": None
        }

        # Find receipt emails
        emails = self.find_receipt_emails(hours_ago)
        stats["emails_found"] = len(emails)

        if not emails:
            print("\n✅ No new receipt emails to process")
            return stats

        # Process each email
        all_receipts = []
        for email in emails:
            print(f"\n📧 Processing email from {email.get('date', 'unknown date')}")
            results = self.process_email(email)

            for result in results:
                stats["processed"] += 1
                if result.success and result.receipt:
                    stats["successful"] += 1
                    all_receipts.append(result.receipt)
                else:
                    stats["failed"] += 1
                    print(f"     ❌ Failed: {result.error}")

        # Update Confluence with all receipts
        if all_receipts:
            url = self.update_confluence_page(all_receipts)
            if url:
                stats["confluence_updated"] = True
                stats["confluence_url"] = url

        # Save state
        self._save_state()

        print("\n" + "=" * 60)
        print("📊 Processing Summary")
        print("=" * 60)
        print(f"   Emails found: {stats['emails_found']}")
        print(f"   Attachments processed: {stats['processed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        if stats['confluence_url']:
            print(f"   Confluence: {stats['confluence_url']}")

        return stats


def process_new_receipts(rag=None, hours_ago: int = 24) -> Dict[str, Any]:
    """
    Hook function for email_rag_ollama.py integration

    Args:
        rag: EmailRAGOllama instance (not used, for API compatibility)
        hours_ago: Look back period

    Returns:
        Processing statistics
    """
    try:
        processor = ReceiptProcessor()
        return processor.process_new_receipts(hours_ago)
    except Exception as e:
        print(f"⚠️  Receipt processing failed: {e}")
        return {"processed": 0, "error": str(e)}


def compare_ocr_engines(image_path: str) -> Dict[str, Any]:
    """
    Compare Vision vs Tesseract OCR on a specific image

    Args:
        image_path: Path to receipt image

    Returns:
        Comparison results with confidence scores and text
    """
    from claude.tools.finance.vision_ocr import VisionOCR

    print(f"\n🔬 OCR Engine Comparison: {image_path}")
    print("=" * 60)

    ocr = VisionOCR()
    comparison = ocr.compare_engines(image_path)

    print(f"\n📊 Results:")
    print(f"   Vision Confidence:    {comparison['vision']['confidence']:.1f}%")
    print(f"   Tesseract Confidence: {comparison['tesseract']['confidence']:.1f}%")
    print(f"   Winner: {comparison['winner'].upper()}")
    print(f"   Delta: {'+' if comparison['confidence_delta'] > 0 else ''}{comparison['confidence_delta']:.1f}%")

    return comparison


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Process receipt emails")
    parser.add_argument("--hours", type=int, default=24, help="Look back period in hours")
    parser.add_argument("--test", action="store_true", help="Test mode (don't update Confluence)")
    parser.add_argument("--compare", type=str, help="Compare OCR engines on a specific image")
    parser.add_argument("--no-vision", action="store_true", help="Disable Vision OCR, use Tesseract only")
    args = parser.parse_args()

    # OCR comparison mode
    if args.compare:
        compare_ocr_engines(args.compare)
        return 0

    processor = ReceiptProcessor(use_vision=not args.no_vision)
    stats = processor.process_new_receipts(hours_ago=args.hours)

    return 0 if stats.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    exit(main())
