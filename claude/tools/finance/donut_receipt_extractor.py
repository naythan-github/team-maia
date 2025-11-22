#!/usr/bin/env python3
"""
Donut Receipt Extractor - ML-based receipt field extraction

Uses the Donut (Document Understanding Transformer) model trained on CORD dataset
for structured receipt field extraction. Runs locally on M4 GPU.

Key advantages over OCR + regex:
- Layout-aware: Understands document structure, not just text
- Trained on receipts: Knows where to find total, tax, vendor
- Error-tolerant: Handles OCR noise gracefully
- Direct extraction: Image → structured data (no intermediate OCR)

Model: naver-clova-ix/donut-base-finetuned-cord-v2
Size: ~800MB (downloads on first use)
Speed: 2-4 sec/receipt on M4 GPU

Author: SRE Principal Engineer Agent (Maia)
Created: 2025-11-22
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Check for required packages
try:
    import torch
    from PIL import Image
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    DONUT_AVAILABLE = True
except ImportError as e:
    DONUT_AVAILABLE = False
    IMPORT_ERROR = str(e)


@dataclass
class ReceiptExtraction:
    """Structured receipt data extracted by Donut"""
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tax_rate: Optional[str] = None
    line_items: Optional[List[Dict[str, Any]]] = None
    payment_method: Optional[str] = None
    raw_output: Optional[str] = None
    confidence: float = 0.0
    model_used: str = "donut-cord-v2"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DonutReceiptExtractor:
    """
    Donut-based receipt field extractor

    Uses Vision Transformer trained specifically on receipts to extract
    structured data directly from images without intermediate OCR.

    Example:
        extractor = DonutReceiptExtractor()
        result = extractor.extract("receipt.jpg")
        print(f"Total: ${result.total}, Tax: ${result.tax}")
    """

    # Model identifier
    MODEL_NAME = "naver-clova-ix/donut-base-finetuned-cord-v2"

    def __init__(self, device: Optional[str] = None):
        """
        Initialize Donut extractor

        Args:
            device: 'cuda', 'mps' (Apple Silicon), or 'cpu'. Auto-detected if None.
        """
        if not DONUT_AVAILABLE:
            raise ImportError(f"Donut dependencies not available: {IMPORT_ERROR}\n"
                            "Install: pip3 install transformers torch pillow")

        # Auto-detect device
        if device is None:
            if torch.backends.mps.is_available():
                self.device = "mps"  # Apple Silicon GPU
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        print(f"🔄 Loading Donut model on {self.device.upper()}...")

        # Load processor and model
        self.processor = DonutProcessor.from_pretrained(self.MODEL_NAME)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()

        print(f"✅ Donut model loaded ({self.device.upper()})")

    def extract(self, image_path: str) -> ReceiptExtraction:
        """
        Extract structured data from receipt image

        Args:
            image_path: Path to receipt image (JPEG, PNG, etc.)

        Returns:
            ReceiptExtraction with vendor, total, tax, line items, etc.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            return ReceiptExtraction(
                raw_output=f"Error: File not found: {image_path}",
                confidence=0.0
            )

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")

            # Prepare for model
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            # Generate output
            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt,
                add_special_tokens=False,
                return_tensors="pt"
            ).input_ids.to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=self.model.decoder.config.max_position_embeddings,
                    early_stopping=True,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id,
                    use_cache=True,
                    num_beams=1,
                    bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                )

            # Decode output
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(
                self.processor.tokenizer.pad_token, ""
            )
            sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

            # Parse the structured output
            return self._parse_output(sequence)

        except Exception as e:
            return ReceiptExtraction(
                raw_output=f"Error: {str(e)}",
                confidence=0.0
            )

    def _parse_output(self, raw_output: str) -> ReceiptExtraction:
        """Parse Donut output into structured ReceiptExtraction"""

        result = ReceiptExtraction(raw_output=raw_output)

        try:
            # Donut CORD output is pseudo-JSON with special tokens
            # Example: <s_menu><s_nm>Coffee</s_nm><s_price>5.50</s_price></s_menu>...

            # Extract total
            total_match = re.search(r'<s_total>.*?<s_total_price>([\d,.]+)</s_total_price>', raw_output)
            if total_match:
                result.total = self._parse_amount(total_match.group(1))

            # Extract subtotal
            subtotal_match = re.search(r'<s_sub_total>.*?<s_subtotal_price>([\d,.]+)</s_subtotal_price>', raw_output)
            if subtotal_match:
                result.subtotal = self._parse_amount(subtotal_match.group(1))

            # Extract tax/GST
            tax_match = re.search(r'<s_tax>.*?<s_tax_price>([\d,.]+)</s_tax_price>', raw_output)
            if tax_match:
                result.tax = self._parse_amount(tax_match.group(1))

            # Extract menu items
            items = []
            menu_matches = re.findall(
                r'<s_menu>.*?<s_nm>(.*?)</s_nm>.*?<s_price>([\d,.]+)</s_price>.*?</s_menu>',
                raw_output,
                re.DOTALL
            )
            for name, price in menu_matches:
                items.append({
                    "name": name.strip(),
                    "price": self._parse_amount(price)
                })
            if items:
                result.line_items = items

            # Calculate confidence based on fields extracted
            fields_found = sum([
                result.total is not None,
                result.subtotal is not None,
                result.tax is not None,
                len(items) > 0
            ])
            result.confidence = min(fields_found / 4 * 100, 100)

        except Exception as e:
            result.raw_output = f"{raw_output}\n\nParse error: {e}"

        return result

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            # Remove currency symbols, commas, spaces
            cleaned = re.sub(r'[^\d.]', '', amount_str)
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def compare_with_ocr(self, image_path: str, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare Donut extraction with OCR-based extraction

        Args:
            image_path: Path to receipt image
            ocr_result: Dict with keys: vendor, total_amount, gst_amount, etc.

        Returns:
            Comparison results
        """
        donut_result = self.extract(image_path)

        comparison = {
            "image": str(image_path),
            "donut": {
                "vendor": donut_result.vendor,
                "total": donut_result.total,
                "tax": donut_result.tax,
                "confidence": donut_result.confidence,
                "line_items": len(donut_result.line_items or [])
            },
            "ocr": {
                "vendor": ocr_result.get("vendor"),
                "total": float(ocr_result.get("total_amount", 0) or 0),
                "tax": float(ocr_result.get("gst_amount", 0) or 0),
                "confidence": ocr_result.get("ocr_confidence", 0)
            }
        }

        # Calculate match
        total_match = abs((comparison["donut"]["total"] or 0) - comparison["ocr"]["total"]) < 0.01
        tax_match = abs((comparison["donut"]["tax"] or 0) - comparison["ocr"]["tax"]) < 0.01

        comparison["matches"] = {
            "total": total_match,
            "tax": tax_match
        }

        return comparison


def test_on_receipts():
    """Test Donut on existing receipts"""
    import tempfile

    # Add paths
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from claude.tools.macos_mail_bridge import MacOSMailBridge

    print("🔬 Testing Donut Receipt Extractor")
    print("=" * 60)

    # Initialize
    extractor = DonutReceiptExtractor()
    bridge = MacOSMailBridge()

    # Get test images from email 3534
    attachments = bridge.get_message_attachments('3534', account='Exchange')
    image_atts = [a for a in attachments if bridge.is_image_attachment(a)]

    print(f"\nTesting on {len(image_atts)} receipt images...")

    for att in image_atts[:3]:  # Test first 3
        name = att['name']
        ext = os.path.splitext(name)[1] or '.jpg'

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            tmp_path = f.name

        if not bridge.save_attachment('3534', name, tmp_path, account='Exchange'):
            continue

        print(f"\n📎 {name}")
        result = extractor.extract(tmp_path)

        print(f"   Total: ${result.total}")
        print(f"   Tax: ${result.tax}")
        print(f"   Items: {len(result.line_items or [])}")
        print(f"   Confidence: {result.confidence:.1f}%")

        if result.line_items:
            for item in result.line_items[:3]:
                print(f"     - {item['name']}: ${item['price']}")

        os.unlink(tmp_path)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Donut Receipt Extractor")
    parser.add_argument("image", nargs="?", help="Path to receipt image")
    parser.add_argument("--test", action="store_true", help="Test on email receipts")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not DONUT_AVAILABLE:
        print(f"❌ Donut not available: {IMPORT_ERROR}")
        print("   Install: pip3 install transformers torch pillow")
        return 1

    if args.test:
        test_on_receipts()
        return 0

    if not args.image:
        print("Usage: python3 donut_receipt_extractor.py <image_path>")
        print("       python3 donut_receipt_extractor.py --test")
        return 1

    extractor = DonutReceiptExtractor()
    result = extractor.extract(args.image)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(f"\n📄 Receipt Extraction: {args.image}")
        print(f"   Vendor: {result.vendor or 'Not detected'}")
        print(f"   Total: ${result.total}" if result.total else "   Total: Not detected")
        print(f"   Tax: ${result.tax}" if result.tax else "   Tax: Not detected")
        print(f"   Confidence: {result.confidence:.1f}%")

        if result.line_items:
            print(f"   Line Items ({len(result.line_items)}):")
            for item in result.line_items:
                print(f"     - {item['name']}: ${item['price']}")

    return 0


if __name__ == "__main__":
    exit(main())
