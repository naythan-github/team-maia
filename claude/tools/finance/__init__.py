"""
Finance Tools - Receipt Processing and Expense Tracking

Components:
- receipt_ocr.py: Tesseract OCR wrapper for images/PDFs
- vision_ocr.py: Apple Vision (Neural Engine) OCR with Tesseract fallback
- receipt_parser.py: Extract structured data from OCR text
- receipt_processor.py: Main orchestrator for email → OCR → Confluence pipeline
"""

from .receipt_ocr import ReceiptOCR
from .vision_ocr import VisionOCR, HybridOCR, VISION_AVAILABLE
from .receipt_parser import ReceiptParser, Receipt
from .receipt_processor import ReceiptProcessor

__all__ = [
    'ReceiptOCR',
    'VisionOCR',
    'HybridOCR',
    'VISION_AVAILABLE',
    'ReceiptParser',
    'Receipt',
    'ReceiptProcessor'
]
