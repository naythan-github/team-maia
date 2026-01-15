#!/usr/bin/env python3
"""
PDF Text Extractor - Production-grade PDF text extraction using pdfplumber.

Extracts text, tables, and metadata from PDF files with batch processing
support and OCR fallback for scanned documents.

Features:
- Text extraction with layout preservation
- Table extraction as structured data
- Metadata extraction (page count, creation date, dimensions)
- Batch processing with parallel execution
- OCR fallback via receipt_ocr.py integration
- JSON and plain text output formats
- CLI interface with subcommands

Author: SRE Principal Engineer Agent (Maia)
Created: 2026-01-15
"""

import os
import sys
import json
import hashlib
import argparse
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# pdfplumber import with graceful degradation
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. Install: pip3 install pdfplumber")

# OCR fallback import
try:
    from claude.tools.finance.receipt_ocr import ReceiptOCR, OCRResult
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    ReceiptOCR = None
    OCRResult = None


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""
    text: str
    source_file: str
    page_count: int
    success: bool
    confidence: float = 95.0
    error: Optional[str] = None
    extraction_method: str = "pdfplumber"
    tables: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages_text: List[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class BatchExtractionResult:
    """Result of batch PDF extraction."""
    results: List[PDFExtractionResult]
    total_files: int
    success_count: int
    failure_count: int
    total_pages: int
    total_chars: int
    processing_time_ms: float
    started_at: str
    completed_at: str


# =============================================================================
# PDF TEXT EXTRACTOR
# =============================================================================

class PDFTextExtractor:
    """
    Production-grade PDF text extractor using pdfplumber.

    Extracts text, tables, and metadata from PDF files with support for
    batch processing and OCR fallback.

    Example:
        extractor = PDFTextExtractor()
        result = extractor.extract("/path/to/document.pdf")
        print(result.text)

        # Batch processing
        results = extractor.batch_extract(["/path/to/doc1.pdf", "/path/to/doc2.pdf"])
    """

    # Minimum text length threshold for OCR fallback
    OCR_THRESHOLD = 20

    def __init__(self, max_workers: int = 5, ocr_enabled: bool = True):
        """
        Initialize PDF Text Extractor.

        Args:
            max_workers: Maximum parallel workers for batch processing
            ocr_enabled: Enable OCR fallback for scanned PDFs
        """
        self.max_workers = max_workers
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE

        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError(
                "pdfplumber not installed. Install with: pip3 install pdfplumber"
            )

        # Initialize OCR if available
        self._ocr = None
        if self.ocr_enabled:
            try:
                self._ocr = ReceiptOCR()
            except Exception:
                self.ocr_enabled = False

    def extract(
        self,
        file_path: str,
        ocr_fallback: bool = True,
        extract_tables: bool = True
    ) -> PDFExtractionResult:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to PDF file
            ocr_fallback: Fall back to OCR if no text found
            extract_tables: Also extract table data

        Returns:
            PDFExtractionResult with extracted text and metadata
        """
        file_path = str(file_path)

        # Validate file exists
        if not file_path:
            return PDFExtractionResult(
                text="",
                source_file=file_path,
                page_count=0,
                success=False,
                confidence=0.0,
                error="Empty file path provided"
            )

        if not os.path.exists(file_path):
            return PDFExtractionResult(
                text="",
                source_file=file_path,
                page_count=0,
                success=False,
                confidence=0.0,
                error=f"File not found: {file_path}"
            )

        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                metadata = self._extract_metadata_internal(pdf)
                page_count = len(pdf.pages)

                # Extract text from each page
                pages_text = []
                all_tables = []

                for i, page in enumerate(pdf.pages):
                    # Text extraction
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text)

                    # Table extraction
                    if extract_tables:
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                all_tables.append({
                                    "page": i,
                                    "data": table,
                                    "rows": len(table),
                                    "cols": len(table[0]) if table else 0
                                })

                # Combine text with page breaks
                full_text = "\n\n--- Page Break ---\n\n".join(pages_text)

                # Check if OCR fallback is needed
                extraction_method = "pdfplumber"
                confidence = 95.0

                if len(full_text.strip()) < self.OCR_THRESHOLD:
                    if ocr_fallback and self.ocr_enabled and self._ocr:
                        # Try OCR fallback
                        ocr_result = self._ocr.extract_text(file_path)
                        if ocr_result.success and len(ocr_result.text) > len(full_text):
                            full_text = ocr_result.text
                            extraction_method = "ocr"
                            confidence = ocr_result.confidence
                            pages_text = [full_text]  # OCR returns single text block
                    else:
                        confidence = 30.0  # Low confidence for minimal text

                return PDFExtractionResult(
                    text=full_text,
                    source_file=file_path,
                    page_count=page_count,
                    success=True,
                    confidence=confidence,
                    extraction_method=extraction_method,
                    tables=all_tables,
                    metadata=metadata,
                    pages_text=pages_text
                )

        except Exception as e:
            return PDFExtractionResult(
                text="",
                source_file=file_path,
                page_count=0,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            List of table dictionaries with page number and data
        """
        file_path = str(file_path)

        if not os.path.exists(file_path):
            return []

        tables = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            tables.append({
                                "page": i,
                                "data": table,
                                "rows": len(table),
                                "cols": len(table[0]) if table else 0
                            })
        except Exception:
            pass

        return tables

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with PDF metadata
        """
        file_path = str(file_path)

        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        try:
            with pdfplumber.open(file_path) as pdf:
                return self._extract_metadata_internal(pdf)
        except Exception as e:
            return {"error": str(e)}

    def _extract_metadata_internal(self, pdf) -> Dict[str, Any]:
        """Extract metadata from an open pdfplumber PDF object."""
        metadata = {
            "page_count": len(pdf.pages),
        }

        # Get raw PDF metadata
        if pdf.metadata:
            for key, value in pdf.metadata.items():
                # Clean key name
                clean_key = key.lstrip('/').lower()
                metadata[clean_key] = value

            # Parse creation date if present
            if 'creationdate' in metadata:
                metadata['creation_date'] = metadata['creationdate']

        # Get page dimensions from first page
        if pdf.pages:
            first_page = pdf.pages[0]
            metadata['width'] = first_page.width
            metadata['height'] = first_page.height
            metadata['dimensions'] = f"{first_page.width}x{first_page.height}"

        return metadata

    def batch_extract(
        self,
        file_paths: List[str],
        ocr_fallback: bool = True
    ) -> BatchExtractionResult:
        """
        Extract text from multiple PDF files in parallel.

        Args:
            file_paths: List of PDF file paths
            ocr_fallback: Fall back to OCR if no text found

        Returns:
            BatchExtractionResult with all results and summary
        """
        started_at = datetime.utcnow()
        results = []

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all extraction tasks
            future_to_path = {
                executor.submit(self.extract, path, ocr_fallback): path
                for path in file_paths
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    path = future_to_path[future]
                    results.append(PDFExtractionResult(
                        text="",
                        source_file=path,
                        page_count=0,
                        success=False,
                        confidence=0.0,
                        error=str(e)
                    ))

        # Sort results by original order
        path_to_result = {r.source_file: r for r in results}
        sorted_results = [path_to_result.get(p, results[i]) for i, p in enumerate(file_paths)]

        completed_at = datetime.utcnow()
        processing_time = (completed_at - started_at).total_seconds() * 1000

        # Calculate summary statistics
        success_count = sum(1 for r in sorted_results if r.success)
        failure_count = len(sorted_results) - success_count
        total_pages = sum(r.page_count for r in sorted_results)
        total_chars = sum(len(r.text) for r in sorted_results)

        return BatchExtractionResult(
            results=sorted_results,
            total_files=len(file_paths),
            success_count=success_count,
            failure_count=failure_count,
            total_pages=total_pages,
            total_chars=total_chars,
            processing_time_ms=processing_time,
            started_at=started_at.isoformat() + "Z",
            completed_at=completed_at.isoformat() + "Z"
        )

    def format_output(
        self,
        result: PDFExtractionResult,
        format: str = "text"
    ) -> Union[str, Dict[str, Any]]:
        """
        Format extraction result for output.

        Args:
            result: PDFExtractionResult to format
            format: Output format - 'text' or 'json'

        Returns:
            Formatted output string or dictionary
        """
        if format == "json":
            return {
                "text": result.text,
                "source_file": result.source_file,
                "page_count": result.page_count,
                "success": result.success,
                "confidence": result.confidence,
                "error": result.error,
                "extraction_method": result.extraction_method,
                "tables": result.tables,
                "metadata": result.metadata,
                "extracted_at": result.extracted_at
            }
        else:
            return result.text

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for PDF Text Extractor."""
    parser = argparse.ArgumentParser(
        description="PDF Text Extractor - Extract text, tables, and metadata from PDFs"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from a PDF')
    extract_parser.add_argument('pdf_path', help='Path to PDF file')
    extract_parser.add_argument('--json', action='store_true', help='Output as JSON')
    extract_parser.add_argument('--no-ocr', action='store_true', help='Disable OCR fallback')
    extract_parser.add_argument('--no-tables', action='store_true', help='Skip table extraction')

    # Tables command
    tables_parser = subparsers.add_parser('tables', help='Extract tables from a PDF')
    tables_parser.add_argument('pdf_path', help='Path to PDF file')
    tables_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Metadata command
    metadata_parser = subparsers.add_parser('metadata', help='Extract PDF metadata')
    metadata_parser.add_argument('pdf_path', help='Path to PDF file')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch process multiple PDFs')
    batch_parser.add_argument('directory', help='Directory containing PDFs')
    batch_parser.add_argument('--pattern', default='*.pdf', help='Glob pattern (default: *.pdf)')
    batch_parser.add_argument('--output', help='Output directory for results')
    batch_parser.add_argument('--json', action='store_true', help='Output as JSON')
    batch_parser.add_argument('--workers', type=int, default=5, help='Parallel workers (default: 5)')

    # Stats command
    subparsers.add_parser('stats', help='Show extractor statistics')

    args = parser.parse_args()

    try:
        extractor = PDFTextExtractor()
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1

    if args.command == 'extract':
        result = extractor.extract(
            args.pdf_path,
            ocr_fallback=not args.no_ocr,
            extract_tables=not args.no_tables
        )

        if args.json:
            output = extractor.format_output(result, format='json')
            print(json.dumps(output, indent=2))
        else:
            if result.success:
                print(f"Pages: {result.page_count}")
                print(f"Confidence: {result.confidence:.1f}%")
                print(f"Method: {result.extraction_method}")
                print(f"\n{result.text}")
            else:
                print(f"Error: {result.error}")
                return 1

    elif args.command == 'tables':
        tables = extractor.extract_tables(args.pdf_path)

        if args.json:
            print(json.dumps(tables, indent=2))
        else:
            print(f"Found {len(tables)} tables:")
            for i, table in enumerate(tables):
                print(f"\n  Table {i+1} (Page {table['page']}, {table['rows']}x{table['cols']}):")
                if table['data']:
                    for row in table['data'][:3]:  # Show first 3 rows
                        print(f"    {row}")
                    if len(table['data']) > 3:
                        print(f"    ... ({len(table['data']) - 3} more rows)")

    elif args.command == 'metadata':
        metadata = extractor.extract_metadata(args.pdf_path)
        print(json.dumps(metadata, indent=2))

    elif args.command == 'batch':
        # Find all PDFs matching pattern
        directory = Path(args.directory).expanduser()
        pdf_files = list(directory.glob(args.pattern))

        if not pdf_files:
            print(f"No PDFs found matching '{args.pattern}' in {directory}")
            return 1

        print(f"Processing {len(pdf_files)} PDFs...")

        extractor = PDFTextExtractor(max_workers=args.workers)
        batch_result = extractor.batch_extract([str(p) for p in pdf_files])

        if args.output:
            output_dir = Path(args.output).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save individual results
            for result in batch_result.results:
                if result.success:
                    filename = Path(result.source_file).stem
                    output_file = output_dir / f"{filename}.json"
                    with open(output_file, 'w') as f:
                        json.dump(extractor.format_output(result, format='json'), f, indent=2)

            # Save summary
            summary_file = output_dir / "extraction_summary.json"
            with open(summary_file, 'w') as f:
                json.dump({
                    "total_files": batch_result.total_files,
                    "success_count": batch_result.success_count,
                    "failure_count": batch_result.failure_count,
                    "total_pages": batch_result.total_pages,
                    "total_chars": batch_result.total_chars,
                    "processing_time_ms": batch_result.processing_time_ms,
                    "started_at": batch_result.started_at,
                    "completed_at": batch_result.completed_at
                }, f, indent=2)

            print(f"Results saved to: {output_dir}")

        # Print summary
        if args.json:
            print(json.dumps({
                "total_files": batch_result.total_files,
                "success_count": batch_result.success_count,
                "failure_count": batch_result.failure_count,
                "total_pages": batch_result.total_pages,
                "processing_time_ms": batch_result.processing_time_ms
            }, indent=2))
        else:
            print(f"\nBatch Complete:")
            print(f"  Files: {batch_result.success_count}/{batch_result.total_files} succeeded")
            print(f"  Pages: {batch_result.total_pages}")
            print(f"  Characters: {batch_result.total_chars:,}")
            print(f"  Time: {batch_result.processing_time_ms:.0f}ms")

            if batch_result.failure_count > 0:
                print(f"\n  Failures:")
                for r in batch_result.results:
                    if not r.success:
                        print(f"    - {Path(r.source_file).name}: {r.error}")

    elif args.command == 'stats':
        print("PDF Text Extractor Statistics")
        print(f"  pdfplumber: {'Available' if PDFPLUMBER_AVAILABLE else 'Not installed'}")
        print(f"  OCR fallback: {'Available' if OCR_AVAILABLE else 'Not installed'}")
        print(f"  Default workers: 5")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
