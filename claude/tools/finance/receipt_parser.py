#!/usr/bin/env python3
"""
Receipt Parser - Extract structured data from OCR text

Parses receipt text to extract:
- Vendor name
- Date
- Total amount
- GST/tax amount
- Line items (optional)
- Category inference

Author: SRE Principal Engineer Agent (Maia)
Created: 2025-11-22
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Receipt:
    """Structured receipt data"""
    # Core fields
    vendor: str
    date: Optional[datetime]
    total_amount: Decimal
    currency: str = "AUD"

    # Tax breakdown
    gst_amount: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None

    # Classification
    category: str = "Uncategorized"
    tax_deductible: bool = True

    # Source tracking
    email_id: str = ""
    email_subject: str = ""
    email_date: Optional[datetime] = None
    attachment_name: str = ""

    # Raw data
    raw_text: str = ""
    ocr_confidence: float = 0.0

    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "vendor": self.vendor,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "gst_amount": str(self.gst_amount) if self.gst_amount else None,
            "subtotal": str(self.subtotal) if self.subtotal else None,
            "category": self.category,
            "tax_deductible": self.tax_deductible,
            "email_id": self.email_id,
            "email_subject": self.email_subject,
            "email_date": self.email_date.isoformat() if self.email_date else None,
            "attachment_name": self.attachment_name,
            "ocr_confidence": self.ocr_confidence,
            "processed_at": self.processed_at.isoformat(),
            "raw_text": self.raw_text
        }


class ReceiptParser:
    """
    Parse OCR text to extract structured receipt data

    Example:
        parser = ReceiptParser()
        receipt = parser.parse(ocr_text)
        print(f"Vendor: {receipt.vendor}, Total: ${receipt.total_amount}")
    """

    # Known Australian vendors and their categories
    VENDOR_PATTERNS = {
        r'bunnings': ('Bunnings Warehouse', 'Hardware'),
        r'officeworks': ('Officeworks', 'Office Supplies'),
        r'jb\s*hi[\-\s]*fi': ('JB Hi-Fi', 'Electronics'),
        r'harvey\s*norman': ('Harvey Norman', 'Electronics'),
        r'coles': ('Coles', 'Groceries'),
        r'woolworths|woolies': ('Woolworths', 'Groceries'),
        r'aldi': ('Aldi', 'Groceries'),
        r'kmart': ('Kmart', 'Retail'),
        r'big\s*w': ('Big W', 'Retail'),
        r'target': ('Target', 'Retail'),
        r'amazon': ('Amazon', 'Online Shopping'),
        r'ebay': ('eBay', 'Online Shopping'),
        r'uber\s*eats': ('Uber Eats', 'Food Delivery'),
        r'menulog': ('Menulog', 'Food Delivery'),
        r'doordash': ('DoorDash', 'Food Delivery'),
        r'mcdonald': ('McDonald\'s', 'Fast Food'),
        r'hungry\s*jack': ('Hungry Jack\'s', 'Fast Food'),
        r'kfc': ('KFC', 'Fast Food'),
        r'subway': ('Subway', 'Fast Food'),
        r'shell': ('Shell', 'Fuel'),
        r'caltex': ('Caltex', 'Fuel'),
        r'bp\b': ('BP', 'Fuel'),
        r'7[\-\s]*eleven': ('7-Eleven', 'Convenience'),
        r'ikea': ('IKEA', 'Furniture'),
        r'fantastic\s*furniture': ('Fantastic Furniture', 'Furniture'),
        r'amart': ('Amart Furniture', 'Furniture'),
        r'chemist\s*warehouse': ('Chemist Warehouse', 'Pharmacy'),
        r'priceline': ('Priceline', 'Pharmacy'),
        r'apple\s*store|apple\.com': ('Apple', 'Electronics'),
        r'microsoft': ('Microsoft', 'Software'),
        r'google': ('Google', 'Software'),
        r'aws|amazon\s*web': ('AWS', 'Cloud Services'),
        r'azure': ('Microsoft Azure', 'Cloud Services'),
        r'ssp\s*australia': ('SSP Australia', 'Food & Beverage'),
        r'grace\s*hare': ('The Grace Hare', 'Food & Beverage'),
        r'amigos': ('Amigos y Familia', 'Food & Beverage'),
        r'movida': ('MoVida', 'Food & Beverage'),
        r'vapiano': ('Vapiano', 'Food & Beverage'),
        r'namoo': ('Namoo', 'Food & Beverage'),
        r'qantas': ('Qantas', 'Travel'),
        r'virgin\s*australia': ('Virgin Australia', 'Travel'),
        r'jetstar': ('Jetstar', 'Travel'),
        # Additional vendors from receipt processing
        r'max\s*on\s*hardware': ('Max on Hardware', 'Hardware'),
        r'the\s*barracks': ('The Barracks', 'Food & Beverage'),
        r'barracks': ('The Barracks', 'Food & Beverage'),
        r'kana\s*sushi': ('Kana Sushi', 'Food & Beverage'),
        r'whalebridge': ('Whalebridge', 'Food & Beverage'),
        r'thai\s*restaurant': ('Thai Restaurant', 'Food & Beverage'),
        r'thai\s*connection': ('Thai Connection', 'Food & Beverage'),
        r'swan\s*taxis?': ('Swan Taxis', 'Travel'),
        r'rasier\s*pacific': ('Uber', 'Travel'),
        r'uber': ('Uber', 'Travel'),
    }

    # Date patterns (Australian format: DD/MM/YYYY)
    DATE_PATTERNS = [
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})',      # DD/MM/YYYY
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})\b',    # DD/MM/YY
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{4})',  # 22 Nov 2025
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})',  # Nov 22, 2025
        r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)['\u2019]?(\d{2})\b",  # 14 Nov'25
    ]

    # Amount patterns
    AMOUNT_PATTERNS = [
        r'total[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'amount\s*due[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'grand\s*total[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'balance\s*due[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'you\s*paid[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'payment[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'american\s*express[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'visa[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'mastercard[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'card[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'a\$\s*(\d+[,.]?\d*\.?\d{0,2})',  # A$17.75 format
        r'\$\s*(\d+[,.]?\d*\.?\d{0,2})\s*$',  # Amount at end of line
    ]

    # GST patterns (Australian 10% GST)
    GST_PATTERNS = [
        r'gst[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'tax[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'check\s*tax[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',  # Check Tax format
        r'includes?\s*gst[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'gst\s*included[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'total\s+includes?\s+gst\s+of[:\s]*[A\$]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',  # "Total includes GST of $2.55" (AMIGOS)
    ]

    def __init__(self):
        """Initialize parser"""
        self.month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

    def parse(self, ocr_text: str, ocr_confidence: float = 0.0) -> Receipt:
        """
        Parse OCR text and extract structured receipt data

        Args:
            ocr_text: Raw text from OCR
            ocr_confidence: OCR confidence score (0-100)

        Returns:
            Receipt dataclass with extracted data
        """
        text_lower = ocr_text.lower()

        # Extract fields
        vendor, category = self._extract_vendor(text_lower, ocr_text)
        date = self._extract_date(text_lower)
        total_amount = self._extract_amount(text_lower)
        gst_amount = self._extract_gst(text_lower)

        # Calculate subtotal if we have both GST and total
        subtotal = None
        if gst_amount and total_amount:
            subtotal = total_amount - gst_amount
        # Don't estimate GST - not all items are taxable, so GST can be 0-10% of total

        return Receipt(
            vendor=vendor,
            date=date,
            total_amount=total_amount or Decimal('0'),
            gst_amount=gst_amount,
            subtotal=subtotal,
            category=category,
            raw_text=ocr_text,
            ocr_confidence=ocr_confidence
        )

    def _extract_vendor(self, text_lower: str, original_text: str) -> tuple[str, str]:
        """Extract vendor name and category from text"""
        for pattern, (vendor_name, category) in self.VENDOR_PATTERNS.items():
            if re.search(pattern, text_lower):
                return vendor_name, category

        # Fallback: try to extract from first few lines
        lines = original_text.strip().split('\n')

        # Headers to skip (not actual vendor names)
        skip_headers = [
            'tax invoice', 'taxinvoice', 'tax  invoice',
            'receipt', 'invoice', 'order', 'docket',
            'eftpos', 'customer copy', 'merchant copy',
        ]

        for line in lines[:5]:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 3 and len(clean_line) < 50:
                # Skip lines that look like addresses or phone numbers
                if not re.match(r'^[\d\s\-\(\)]+$', clean_line):
                    if not re.search(r'\d{4,}', clean_line):  # Skip phone numbers
                        # Skip common receipt headers
                        if clean_line.lower().replace(' ', '') not in [h.replace(' ', '') for h in skip_headers]:
                            if not any(h in clean_line.lower() for h in skip_headers):
                                return clean_line, "Uncategorized"

        return "Unknown Vendor", "Uncategorized"

    def _extract_date(self, text_lower: str) -> Optional[datetime]:
        """Extract date from text"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()

                    if len(groups) == 3:
                        # Check if it's a word month format
                        if groups[0].isalpha():
                            # Month DD, YYYY format
                            month = self.month_map.get(groups[0][:3].lower())
                            day = int(groups[1])
                            year = int(groups[2])
                        elif groups[1].isalpha():
                            # DD Month YYYY or DD Month'YY format
                            day = int(groups[0])
                            month = self.month_map.get(groups[1][:3].lower())
                            year = int(groups[2])
                        else:
                            # DD/MM/YYYY or DD/MM/YY
                            day = int(groups[0])
                            month = int(groups[1])
                            year = int(groups[2])

                        # Handle 2-digit year (applies to ALL formats)
                        if year < 100:
                            year += 2000 if year < 50 else 1900

                        if month and 1 <= day <= 31 and 1 <= month <= 12:
                            return datetime(year, month, day)

                except (ValueError, TypeError):
                    continue

        return None

    def _extract_amount(self, text_lower: str) -> Optional[Decimal]:
        """Extract total amount from text"""
        # Priority 1: Look for explicit "Amount Paid", "Balance:", or "Total:" patterns (most reliable)
        priority_patterns = [
            r'amount\s*paid[:\s]*[A\$]*\$?\s*(\d+\.?\d{0,2})',
            r'balance[:\s]+[A\$]*\$?\s*(\d+\.?\d{0,2})',  # "Balance: $28.00" format (AMIGOS)
            r'total[:\s]+[A\$]*\$?\s*(\d+\.?\d{0,2})',  # "Total:" with colon
            r'you\s*paid[:\s]*[A\$]*\$?\s*(\d+\.?\d{0,2})',
        ]

        for pattern in priority_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = Decimal(amount_str)
                    # Sanity check: typical receipt is $1-$500
                    if Decimal('0.50') < amount < Decimal('500'):
                        return amount
                except (InvalidOperation, ValueError):
                    continue

        # Priority 2: Standard patterns
        amounts = []
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    amount_str = match.replace(',', '').replace(' ', '')
                    amount = Decimal(amount_str)
                    # Filter unrealistic amounts (likely OCR errors like 4817.75 from A$17.75)
                    if Decimal('0.50') < amount < Decimal('500'):
                        amounts.append(amount)
                except (InvalidOperation, ValueError):
                    continue

        # Return the largest reasonable amount
        if amounts:
            return max(amounts)

        # Fallback: find any dollar amounts with decimal points (more likely to be real)
        all_amounts = re.findall(r'\$\s*(\d{1,3}\.\d{2})\b', text_lower)
        if all_amounts:
            try:
                valid = [Decimal(a) for a in all_amounts if Decimal('0.50') < Decimal(a) < Decimal('500')]
                if valid:
                    return max(valid)
            except (InvalidOperation, ValueError):
                pass

        # Last resort: find amounts at end of lines (common receipt format: "Item Name  17.50")
        line_amounts = re.findall(r'\s(\d{1,3}\.\d{2})\s*$', text_lower, re.MULTILINE)
        if line_amounts:
            try:
                valid = [Decimal(a) for a in line_amounts if Decimal('0.50') < Decimal(a) < Decimal('500')]
                if valid:
                    return max(valid)
            except (InvalidOperation, ValueError):
                pass

        return None

    def _extract_gst(self, text_lower: str) -> Optional[Decimal]:
        """Extract GST/tax amount from text"""
        for pattern in self.GST_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = Decimal(amount_str)
                    if amount > 0:
                        return amount
                except (InvalidOperation, ValueError):
                    continue

        return None

    def format_for_confluence(self, receipt: Receipt) -> Dict[str, str]:
        """
        Format receipt data for Confluence table row

        Returns:
            Dictionary with formatted strings for each column
        """
        return {
            "date": receipt.date.strftime("%d %b %Y") if receipt.date else "Unknown",
            "vendor": receipt.vendor,
            "amount": f"${receipt.total_amount:.2f}",
            "gst": f"${receipt.gst_amount:.2f}" if receipt.gst_amount else "-",
            "category": receipt.category,
            "email_date": receipt.email_date.strftime("%d %b %Y") if receipt.email_date else "-",
            "status": "✅"
        }


def main():
    """Test parser with sample receipt text"""
    sample_text = """
    BUNNINGS WAREHOUSE
    123 Example Street
    PERTH WA 6000

    Date: 22/11/2025
    Time: 14:32

    ITEMS:
    Power Drill         $89.00
    Screws 100pk        $12.50
    Safety Glasses      $15.00

    SUBTOTAL           $116.50
    GST                 $10.59
    TOTAL              $127.09

    CARD               $127.09

    Thank you for shopping at Bunnings
    """

    print("🧾 Receipt Parser Test\n")

    parser = ReceiptParser()
    receipt = parser.parse(sample_text, ocr_confidence=95.0)

    print(f"Vendor: {receipt.vendor}")
    print(f"Category: {receipt.category}")
    print(f"Date: {receipt.date}")
    print(f"Total: ${receipt.total_amount}")
    print(f"GST: ${receipt.gst_amount}")
    print(f"Subtotal: ${receipt.subtotal}")

    print("\n--- Confluence Format ---")
    formatted = parser.format_for_confluence(receipt)
    for key, value in formatted.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
