#!/usr/bin/env python3
"""
Receipt OCR - Tesseract wrapper for extracting text from receipt images/PDFs

Uses local Tesseract OCR for 100% privacy - no cloud services.

Supported formats:
- Images: PNG, JPG, JPEG, TIFF, BMP, GIF, HEIC
- Documents: PDF (converted to images first)

Author: SRE Principal Engineer Agent (Maia)
Created: 2025-11-22
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    import pytesseract
    from PIL import Image
except ImportError:
    raise ImportError("Missing dependencies. Install: pip3 install pytesseract pillow")

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PDF support unavailable. Install: pip3 install pdf2image")


@dataclass
class OCRResult:
    """Result of OCR processing"""
    text: str                    # Extracted text
    confidence: float            # Average confidence (0-100)
    source_file: str             # Original file path
    pages: int                   # Number of pages processed
    success: bool                # Whether OCR succeeded
    error: Optional[str] = None  # Error message if failed


class ReceiptOCR:
    """
    Tesseract OCR wrapper optimized for receipt processing

    Example:
        ocr = ReceiptOCR()
        result = ocr.extract_text("/path/to/receipt.jpg")
        print(result.text)
    """

    # Supported image formats
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}

    def __init__(self, lang: str = 'eng', tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR engine

        Args:
            lang: Tesseract language code (default: 'eng')
            tesseract_cmd: Path to tesseract binary (auto-detected if None)
        """
        self.lang = lang

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Verify tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            self.tesseract_version = str(version)
        except Exception as e:
            raise RuntimeError(f"Tesseract not found. Install: brew install tesseract. Error: {e}")

    def extract_text(self, file_path: str) -> OCRResult:
        """
        Extract text from an image or PDF file

        Args:
            file_path: Path to image or PDF file

        Returns:
            OCRResult with extracted text and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return OCRResult(
                text="",
                confidence=0.0,
                source_file=str(file_path),
                pages=0,
                success=False,
                error=f"File not found: {file_path}"
            )

        ext = file_path.suffix.lower()

        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext in self.IMAGE_EXTENSIONS or ext == '.heic':
            return self._process_image(file_path)
        else:
            return OCRResult(
                text="",
                confidence=0.0,
                source_file=str(file_path),
                pages=0,
                success=False,
                error=f"Unsupported file format: {ext}"
            )

    def _find_best_rotation(self, image: Image.Image) -> tuple[Image.Image, int]:
        """
        Find the best rotation for OCR by testing 0, 90, 180, 270 degrees

        Returns:
            Tuple of (rotated_image, rotation_degrees)
        """
        best_image = image
        best_rotation = 0
        best_score = 0

        # Receipt keywords to detect correct orientation
        keywords = ['total', 'gst', 'tax', 'amount', 'receipt', 'invoice', 'subtotal', 'payment']

        for rotation in [0, 90, 180, 270]:
            rotated = image.rotate(rotation, expand=True)

            # Quick OCR to check orientation
            try:
                text = pytesseract.image_to_string(rotated).lower()
                data = pytesseract.image_to_data(rotated, output_type=pytesseract.Output.DICT)
                confidences = [c for c in data['conf'] if c > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0

                # Score based on keywords found and confidence
                keyword_count = sum(1 for k in keywords if k in text)
                score = (keyword_count * 20) + avg_conf  # Weight keywords heavily

                if score > best_score:
                    best_score = score
                    best_image = rotated
                    best_rotation = rotation
            except Exception:
                continue

        return best_image, best_rotation

    def _process_image(self, image_path: Path) -> OCRResult:
        """Process a single image file with auto-rotation detection"""
        try:
            # Handle HEIC format (convert to PNG first)
            if image_path.suffix.lower() == '.heic':
                image_path = self._convert_heic(image_path)

            # Open and process image
            image = Image.open(image_path)

            # Convert to RGB if needed (for transparency handling)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            # Auto-detect best rotation for receipts
            image, rotation = self._find_best_rotation(image)
            if rotation != 0:
                print(f"     📐 Auto-rotated {rotation}° for better OCR")

            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)

            # Extract text
            text = pytesseract.image_to_string(image, lang=self.lang)

            # Calculate average confidence (excluding -1 values which indicate no text)
            confidences = [c for c in data['conf'] if c > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                source_file=str(image_path),
                pages=1,
                success=True
            )

        except Exception as e:
            return OCRResult(
                text="",
                confidence=0.0,
                source_file=str(image_path),
                pages=0,
                success=False,
                error=str(e)
            )

    def _process_pdf(self, pdf_path: Path) -> OCRResult:
        """Process a PDF file (convert pages to images, then OCR)"""
        if not PDF_SUPPORT:
            return OCRResult(
                text="",
                confidence=0.0,
                source_file=str(pdf_path),
                pages=0,
                success=False,
                error="PDF support not available. Install: pip3 install pdf2image"
            )

        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)

            all_text = []
            total_confidence = 0.0

            for i, image in enumerate(images):
                # Convert to RGB if needed
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')

                # OCR the page
                text = pytesseract.image_to_string(image, lang=self.lang)
                all_text.append(text.strip())

                # Get confidence
                data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
                confidences = [c for c in data['conf'] if c > 0]
                if confidences:
                    total_confidence += sum(confidences) / len(confidences)

            avg_confidence = total_confidence / len(images) if images else 0.0

            return OCRResult(
                text="\n\n--- Page Break ---\n\n".join(all_text),
                confidence=avg_confidence,
                source_file=str(pdf_path),
                pages=len(images),
                success=True
            )

        except Exception as e:
            return OCRResult(
                text="",
                confidence=0.0,
                source_file=str(pdf_path),
                pages=0,
                success=False,
                error=str(e)
            )

    def _convert_heic(self, heic_path: Path) -> Path:
        """Convert HEIC to PNG for processing"""
        try:
            # Use sips (macOS built-in) to convert HEIC
            import subprocess

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name

            result = subprocess.run(
                ['sips', '-s', 'format', 'png', str(heic_path), '--out', tmp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"HEIC conversion failed: {result.stderr}")

            return Path(tmp_path)

        except Exception as e:
            raise RuntimeError(f"Failed to convert HEIC: {e}")

    def preprocess_for_receipts(self, image_path: str) -> str:
        """
        Preprocess image for better receipt OCR accuracy

        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Noise reduction

        Args:
            image_path: Path to original image

        Returns:
            Path to preprocessed image (temporary file)
        """
        try:
            from PIL import ImageEnhance, ImageFilter

            image = Image.open(image_path)

            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Slight sharpening
            image = image.filter(ImageFilter.SHARPEN)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(tmp.name, 'PNG')
                return tmp.name

        except Exception as e:
            # If preprocessing fails, return original
            print(f"  ⚠️  Preprocessing failed, using original: {e}")
            return image_path

    def extract_with_preprocessing(self, file_path: str) -> OCRResult:
        """
        Extract text with preprocessing for better accuracy

        Tries:
        1. Preprocessed image
        2. Original image (fallback)

        Returns best result based on confidence score.
        """
        # First try with preprocessing
        preprocessed_path = self.preprocess_for_receipts(file_path)
        result_preprocessed = self.extract_text(preprocessed_path)

        # Clean up temp file if created
        if preprocessed_path != file_path and os.path.exists(preprocessed_path):
            os.unlink(preprocessed_path)

        # Also try original
        result_original = self.extract_text(file_path)

        # Return the one with higher confidence
        if result_preprocessed.confidence > result_original.confidence:
            return result_preprocessed
        return result_original


def main():
    """Test OCR functionality"""
    import sys

    print("🔍 Receipt OCR - Tesseract Wrapper\n")

    try:
        ocr = ReceiptOCR()
        print(f"✅ Tesseract {ocr.tesseract_version} ready")
        print(f"   Language: {ocr.lang}")
        print(f"   PDF support: {'✅' if PDF_SUPPORT else '❌'}")

        # If file path provided, process it
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            print(f"\n📄 Processing: {file_path}")

            result = ocr.extract_with_preprocessing(file_path)

            if result.success:
                print(f"✅ OCR Complete")
                print(f"   Pages: {result.pages}")
                print(f"   Confidence: {result.confidence:.1f}%")
                print(f"\n--- Extracted Text ---\n")
                print(result.text[:2000])  # First 2000 chars
                if len(result.text) > 2000:
                    print(f"\n... [{len(result.text) - 2000} more characters]")
            else:
                print(f"❌ OCR Failed: {result.error}")
        else:
            print("\nUsage: python3 receipt_ocr.py <image_or_pdf_path>")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
