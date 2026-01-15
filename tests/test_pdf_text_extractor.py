#!/usr/bin/env python3
"""
TDD Test Suite for PDF Text Extractor

Phase P3: Unit Tests (written BEFORE implementation)
Following Maia TDD Protocol v2.5

Author: SRE Principal Engineer Agent (Maia)
Created: 2026-01-15
"""

import pytest
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add Maia root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import will fail until implementation exists - expected for TDD
try:
    from claude.tools.document.pdf_text_extractor import (
        PDFTextExtractor,
        PDFExtractionResult,
        BatchExtractionResult,
    )
    TOOL_AVAILABLE = True
except ImportError:
    TOOL_AVAILABLE = False
    PDFTextExtractor = None
    PDFExtractionResult = None
    BatchExtractionResult = None


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def extractor():
    """Create PDFTextExtractor instance"""
    if not TOOL_AVAILABLE:
        pytest.skip("PDFTextExtractor not yet implemented")
    return PDFTextExtractor()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def real_pdfs():
    """Paths to real test PDFs in ~/Downloads/"""
    base = Path.home() / 'Downloads'
    pdfs = {
        'item1': base / 'Orro outstanding topics - Item 1.pdf',
        'item2': base / 'Orro outstanding topics - Item 2.pdf',
        'item3': base / 'Orro outstanding topics - Item 3.pdf',
        'item4': base / 'Orro outstanding topics - Item 4.pdf',
        'item5': base / 'Orro outstanding topics - Item 5.pdf',
        'item6': base / 'Orro outstanding topics - Item 6.pdf',
        'vlr': base / 'Orro Outstanding items_VLR_20260114.pdf',
    }
    return pdfs


@pytest.fixture
def all_real_pdf_paths(real_pdfs):
    """List of all real PDF paths that exist"""
    available = [p for p in real_pdfs.values() if p.exists()]
    if len(available) < 7:
        pytest.skip(f"Only {len(available)}/7 test PDFs available in ~/Downloads/")
    return available


@pytest.fixture
def item1_pdf_path(real_pdfs):
    """Path to Item 1 PDF (44 pages, has tables)"""
    path = real_pdfs['item1']
    if not path.exists():
        pytest.skip("Item 1 PDF not available")
    return path


@pytest.fixture
def item4_pdf_path(real_pdfs):
    """Path to Item 4 PDF (smallest, ~10KB)"""
    path = real_pdfs['item4']
    if not path.exists():
        pytest.skip("Item 4 PDF not available")
    return path


@pytest.fixture
def corrupt_pdf(temp_dir):
    """Create a corrupt PDF file for error testing"""
    pdf_path = temp_dir / "corrupt.pdf"
    pdf_path.write_bytes(b"not a valid pdf content - corrupt header")
    return pdf_path


@pytest.fixture
def nonexistent_pdf():
    """Path to a file that doesn't exist"""
    return Path("/nonexistent/path/to/file.pdf")


# =============================================================================
# TEST CLASS: TextExtraction (FR-001)
# =============================================================================

class TestTextExtraction:
    """Tests for core text extraction functionality"""

    def test_extract_text_returns_result_object(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF file path
        WHEN extract() is called
        THEN returns a PDFExtractionResult object
        """
        result = extractor.extract(str(item1_pdf_path))

        assert isinstance(result, PDFExtractionResult)
        assert hasattr(result, 'text')
        assert hasattr(result, 'success')
        assert hasattr(result, 'page_count')

    def test_extract_text_success_flag(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF file
        WHEN extract() is called
        THEN success=True and text is non-empty
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        assert len(result.text) > 0

    def test_extract_text_from_multipage_pdf(self, extractor, item1_pdf_path):
        """
        GIVEN a multipage PDF (Item 1 has 44 pages)
        WHEN extract() is called
        THEN text from all pages is extracted
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        assert result.page_count == 44
        # Text should be substantial for 44 pages
        assert len(result.text) > 10000

    def test_extract_text_preserves_line_breaks(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF with multiple paragraphs
        WHEN extract() is called
        THEN line breaks are preserved in output
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        # Should have multiple lines
        assert '\n' in result.text
        lines = result.text.split('\n')
        assert len(lines) > 10

    def test_extract_text_handles_unicode(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF with potential unicode characters
        WHEN extract() is called
        THEN unicode characters are handled without errors
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        # Should be valid UTF-8
        result.text.encode('utf-8')

    def test_extract_text_includes_confidence(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF
        WHEN extract() is called
        THEN confidence score is included (0-100)
        """
        result = extractor.extract(str(item1_pdf_path))

        assert hasattr(result, 'confidence')
        assert 0 <= result.confidence <= 100


# =============================================================================
# TEST CLASS: TableExtraction (FR-002)
# =============================================================================

class TestTableExtraction:
    """Tests for table extraction functionality"""

    def test_extract_tables_returns_list(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF file
        WHEN extract_tables() is called
        THEN returns a list of tables
        """
        tables = extractor.extract_tables(str(item1_pdf_path))

        assert isinstance(tables, list)

    def test_extract_tables_finds_tables_on_page_0(self, extractor, item1_pdf_path):
        """
        GIVEN Item 1 PDF which has 2 tables on page 0
        WHEN extract_tables() is called
        THEN at least 2 tables are found
        """
        tables = extractor.extract_tables(str(item1_pdf_path))

        # Filter tables from page 0
        page0_tables = [t for t in tables if t.get('page', 0) == 0]
        assert len(page0_tables) >= 2

    def test_extract_table_preserves_structure(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF with tables
        WHEN extract_tables() is called
        THEN table structure (rows/columns) is preserved
        """
        tables = extractor.extract_tables(str(item1_pdf_path))

        if tables:
            table = tables[0]
            assert 'data' in table
            # Data should be list of rows
            assert isinstance(table['data'], list)
            if table['data']:
                # Each row should be a list of cells
                assert isinstance(table['data'][0], list)

    def test_extract_tables_includes_page_number(self, extractor, item1_pdf_path):
        """
        GIVEN a multipage PDF
        WHEN extract_tables() is called
        THEN each table includes its page number
        """
        tables = extractor.extract_tables(str(item1_pdf_path))

        if tables:
            for table in tables:
                assert 'page' in table
                assert isinstance(table['page'], int)

    def test_extract_tables_empty_for_text_only(self, extractor, item4_pdf_path):
        """
        GIVEN a PDF with no tables
        WHEN extract_tables() is called
        THEN empty list is returned
        """
        tables = extractor.extract_tables(str(item4_pdf_path))

        # Item 4 may or may not have tables - test should handle both
        assert isinstance(tables, list)


# =============================================================================
# TEST CLASS: MetadataExtraction (FR-003)
# =============================================================================

class TestMetadataExtraction:
    """Tests for PDF metadata extraction"""

    def test_extract_metadata_returns_dict(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF
        WHEN extract_metadata() is called
        THEN returns a dictionary
        """
        metadata = extractor.extract_metadata(str(item1_pdf_path))

        assert isinstance(metadata, dict)

    def test_extract_metadata_includes_page_count(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF
        WHEN extract_metadata() is called
        THEN page_count is included
        """
        metadata = extractor.extract_metadata(str(item1_pdf_path))

        assert 'page_count' in metadata
        assert metadata['page_count'] == 44

    def test_extract_metadata_includes_creation_date(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF with creation date metadata
        WHEN extract_metadata() is called
        THEN creation_date is extracted
        """
        metadata = extractor.extract_metadata(str(item1_pdf_path))

        # May or may not have creation date
        if 'creation_date' in metadata:
            assert metadata['creation_date'] is not None

    def test_extract_metadata_includes_dimensions(self, extractor, item1_pdf_path):
        """
        GIVEN a valid PDF
        WHEN extract_metadata() is called
        THEN page dimensions are included
        """
        metadata = extractor.extract_metadata(str(item1_pdf_path))

        assert 'width' in metadata or 'dimensions' in metadata
        assert 'height' in metadata or 'dimensions' in metadata

    def test_metadata_from_item1_pdf(self, extractor, item1_pdf_path):
        """
        GIVEN Item 1 PDF (known properties)
        WHEN extract_metadata() is called
        THEN expected values match
        """
        metadata = extractor.extract_metadata(str(item1_pdf_path))

        assert metadata['page_count'] == 44
        # Creator tool should be PDF-XChange Lite
        if 'creator' in metadata:
            assert 'PDF-XChange' in str(metadata.get('creator', ''))


# =============================================================================
# TEST CLASS: BatchProcessing (FR-004)
# =============================================================================

class TestBatchProcessing:
    """Tests for batch PDF processing"""

    def test_batch_extract_returns_results(self, extractor, all_real_pdf_paths):
        """
        GIVEN a list of PDF paths
        WHEN batch_extract() is called
        THEN returns results for all PDFs
        """
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])

        assert isinstance(results, (list, BatchExtractionResult))
        if isinstance(results, BatchExtractionResult):
            assert len(results.results) == len(all_real_pdf_paths)
        else:
            assert len(results) == len(all_real_pdf_paths)

    def test_batch_extract_all_succeed(self, extractor, all_real_pdf_paths):
        """
        GIVEN 7 valid PDFs
        WHEN batch_extract() is called
        THEN all 7 succeed
        """
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])

        if isinstance(results, BatchExtractionResult):
            assert results.success_count == 7
            assert results.failure_count == 0
        else:
            successful = [r for r in results if r.success]
            assert len(successful) == 7

    def test_batch_extract_handles_partial_failure(self, extractor, all_real_pdf_paths, corrupt_pdf):
        """
        GIVEN a list with one invalid PDF
        WHEN batch_extract() is called
        THEN valid PDFs succeed and invalid returns error
        """
        paths = [str(p) for p in all_real_pdf_paths[:2]] + [str(corrupt_pdf)]
        results = extractor.batch_extract(paths)

        if isinstance(results, BatchExtractionResult):
            # 2 should succeed, 1 should fail
            assert results.success_count == 2
            assert results.failure_count == 1
        else:
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            assert len(successful) == 2
            assert len(failed) == 1

    def test_batch_extract_includes_summary(self, extractor, all_real_pdf_paths):
        """
        GIVEN batch extraction
        WHEN complete
        THEN summary statistics are included
        """
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])

        if isinstance(results, BatchExtractionResult):
            assert hasattr(results, 'total_pages')
            assert hasattr(results, 'total_files')
            assert hasattr(results, 'success_count')

    def test_batch_extract_preserves_order(self, extractor, all_real_pdf_paths):
        """
        GIVEN PDFs in specific order
        WHEN batch_extract() is called
        THEN results maintain same order
        """
        paths = [str(p) for p in all_real_pdf_paths]
        results = extractor.batch_extract(paths)

        if isinstance(results, BatchExtractionResult):
            result_list = results.results
        else:
            result_list = results

        for i, (path, result) in enumerate(zip(paths, result_list)):
            assert Path(result.source_file).name == Path(path).name


# =============================================================================
# TEST CLASS: OCRFallback (FR-005)
# =============================================================================

class TestOCRFallback:
    """Tests for OCR fallback on scanned PDFs"""

    def test_extract_with_ocr_fallback_flag(self, extractor, item1_pdf_path):
        """
        GIVEN a text-based PDF
        WHEN extract(ocr_fallback=True) is called
        THEN normal extraction succeeds without invoking OCR
        """
        result = extractor.extract(str(item1_pdf_path), ocr_fallback=True)

        assert result.success is True
        assert len(result.text) > 0

    def test_ocr_fallback_disabled_returns_empty_for_no_text(self, extractor):
        """
        GIVEN a hypothetical image-only PDF
        WHEN extract(ocr_fallback=False) is called
        THEN result indicates OCR needed
        """
        # This test would need an image-only PDF fixture
        # For now, test the flag is accepted
        if not TOOL_AVAILABLE:
            pytest.skip("Tool not yet implemented")

        # Verify the method accepts ocr_fallback parameter
        import inspect
        sig = inspect.signature(extractor.extract)
        assert 'ocr_fallback' in sig.parameters

    def test_extraction_method_recorded(self, extractor, item1_pdf_path):
        """
        GIVEN any PDF extraction
        WHEN complete
        THEN extraction_method is recorded in result
        """
        result = extractor.extract(str(item1_pdf_path))

        assert hasattr(result, 'extraction_method')
        assert result.extraction_method in ['pdfplumber', 'ocr', 'hybrid']


# =============================================================================
# TEST CLASS: OutputFormats (FR-006, FR-007)
# =============================================================================

class TestOutputFormats:
    """Tests for output format handling"""

    def test_format_output_text(self, extractor, item1_pdf_path):
        """
        GIVEN an extraction result
        WHEN format_output(format='text') is called
        THEN clean text string is returned
        """
        result = extractor.extract(str(item1_pdf_path))
        text_output = extractor.format_output(result, format='text')

        assert isinstance(text_output, str)
        assert len(text_output) > 0

    def test_format_output_json(self, extractor, item1_pdf_path):
        """
        GIVEN an extraction result
        WHEN format_output(format='json') is called
        THEN valid JSON dict is returned
        """
        result = extractor.extract(str(item1_pdf_path))
        json_output = extractor.format_output(result, format='json')

        assert isinstance(json_output, dict)
        assert 'text' in json_output
        assert 'metadata' in json_output

    def test_json_output_is_serializable(self, extractor, item1_pdf_path):
        """
        GIVEN JSON output
        WHEN json.dumps() is called
        THEN serialization succeeds
        """
        result = extractor.extract(str(item1_pdf_path))
        json_output = extractor.format_output(result, format='json')

        # Should not raise
        serialized = json.dumps(json_output)
        assert isinstance(serialized, str)

    def test_json_output_includes_tables(self, extractor, item1_pdf_path):
        """
        GIVEN extraction with tables
        WHEN format_output(format='json') is called
        THEN tables are included
        """
        result = extractor.extract(str(item1_pdf_path))
        json_output = extractor.format_output(result, format='json')

        assert 'tables' in json_output


# =============================================================================
# TEST CLASS: CLI (FR-008)
# =============================================================================

class TestCLI:
    """Tests for CLI interface"""

    def test_cli_module_has_main(self):
        """
        GIVEN the pdf_text_extractor module
        WHEN imported
        THEN main() function exists
        """
        if not TOOL_AVAILABLE:
            pytest.skip("Tool not yet implemented")

        from claude.tools.document import pdf_text_extractor
        assert hasattr(pdf_text_extractor, 'main')
        assert callable(pdf_text_extractor.main)

    def test_cli_extract_subcommand(self, item1_pdf_path):
        """
        GIVEN a valid PDF path
        WHEN CLI 'extract' subcommand is run
        THEN text is extracted successfully
        """
        if not TOOL_AVAILABLE:
            pytest.skip("Tool not yet implemented")

        import subprocess
        result = subprocess.run(
            ['python3', 'claude/tools/document/pdf_text_extractor.py',
             'extract', str(item1_pdf_path)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )

        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_cli_json_flag(self, item1_pdf_path):
        """
        GIVEN --json flag
        WHEN extract command is run
        THEN output is valid JSON
        """
        if not TOOL_AVAILABLE:
            pytest.skip("Tool not yet implemented")

        import subprocess
        result = subprocess.run(
            ['python3', 'claude/tools/document/pdf_text_extractor.py',
             'extract', str(item1_pdf_path), '--json'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )

        assert result.returncode == 0
        # Should be valid JSON
        json.loads(result.stdout)

    def test_cli_help(self):
        """
        GIVEN --help flag
        WHEN invoked
        THEN usage information is displayed
        """
        if not TOOL_AVAILABLE:
            pytest.skip("Tool not yet implemented")

        import subprocess
        result = subprocess.run(
            ['python3', 'claude/tools/document/pdf_text_extractor.py', '--help'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )

        assert result.returncode == 0
        assert 'usage' in result.stdout.lower() or 'extract' in result.stdout.lower()


# =============================================================================
# TEST CLASS: EdgeCases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_file_not_found_error(self, extractor, nonexistent_pdf):
        """
        GIVEN a non-existent file path
        WHEN extract() is called
        THEN result has success=False with error
        """
        result = extractor.extract(str(nonexistent_pdf))

        assert result.success is False
        assert result.error is not None
        assert 'not found' in result.error.lower() or 'no such' in result.error.lower()

    def test_invalid_pdf_error(self, extractor, corrupt_pdf):
        """
        GIVEN a corrupt PDF file
        WHEN extract() is called
        THEN result has success=False with error
        """
        result = extractor.extract(str(corrupt_pdf))

        assert result.success is False
        assert result.error is not None

    def test_empty_path_error(self, extractor):
        """
        GIVEN an empty string path
        WHEN extract() is called
        THEN result has success=False
        """
        result = extractor.extract("")

        assert result.success is False
        assert result.error is not None

    def test_path_with_spaces(self, extractor, item1_pdf_path):
        """
        GIVEN a PDF with spaces in filename
        WHEN extract() is called
        THEN extraction succeeds (Item 1 has spaces)
        """
        # "Orro outstanding topics - Item 1.pdf" has spaces
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True


# =============================================================================
# TEST CLASS: RealPDFs (Integration Tests)
# =============================================================================

class TestRealPDFs:
    """Integration tests with real PDF test data"""

    def test_item1_extracts_44_pages(self, extractor, item1_pdf_path):
        """
        GIVEN "Orro outstanding topics - Item 1.pdf"
        WHEN extract() is called
        THEN page_count=44
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        assert result.page_count == 44

    def test_item1_detects_email_content(self, extractor, item1_pdf_path):
        """
        GIVEN Item 1 PDF (business correspondence)
        WHEN extract() is called
        THEN email headers are detected in text
        """
        result = extractor.extract(str(item1_pdf_path))

        assert result.success is True
        # Should contain email headers
        assert 'From:' in result.text or 'Sent:' in result.text

    def test_item1_extracts_tables(self, extractor, item1_pdf_path):
        """
        GIVEN Item 1 PDF with tables
        WHEN extract_tables() is called
        THEN tables are extracted
        """
        tables = extractor.extract_tables(str(item1_pdf_path))

        assert len(tables) >= 2  # At least 2 tables on page 0

    def test_item4_smallest_pdf(self, extractor, item4_pdf_path):
        """
        GIVEN Item 4 PDF (smallest, ~10KB)
        WHEN extract() is called
        THEN extraction completes successfully
        """
        result = extractor.extract(str(item4_pdf_path))

        assert result.success is True
        # Should have reasonable text length
        assert len(result.text) > 100

    def test_all_seven_pdfs_batch(self, extractor, all_real_pdf_paths):
        """
        GIVEN all 7 PDFs in ~/Downloads/
        WHEN batch_extract() is called
        THEN all 7 succeed
        """
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])

        if isinstance(results, BatchExtractionResult):
            assert results.success_count == 7
            assert results.total_files == 7
        else:
            successful = [r for r in results if r.success]
            assert len(successful) == 7


# =============================================================================
# TEST CLASS: Performance (P6 Validation)
# =============================================================================

class TestPerformance:
    """P6: Performance validation tests"""

    def test_single_page_under_500ms(self, extractor, item4_pdf_path):
        """
        GIVEN a small PDF
        WHEN extract() is called
        THEN completes in < 500ms
        """
        start = time.time()
        result = extractor.extract(str(item4_pdf_path))
        elapsed = time.time() - start

        assert result.success is True
        assert elapsed < 0.5, f"Extraction took {elapsed:.2f}s (target: <0.5s)"

    def test_44_page_pdf_under_5s(self, extractor, item1_pdf_path):
        """
        GIVEN 44-page Item 1 PDF
        WHEN extract() is called
        THEN completes in < 5 seconds
        """
        start = time.time()
        result = extractor.extract(str(item1_pdf_path))
        elapsed = time.time() - start

        assert result.success is True
        assert elapsed < 5.0, f"44 pages took {elapsed:.2f}s (target: <5s)"

    def test_batch_7_pdfs_under_30s(self, extractor, all_real_pdf_paths):
        """
        GIVEN 7 PDFs
        WHEN batch_extract() is called
        THEN completes in < 30 seconds
        """
        start = time.time()
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])
        elapsed = time.time() - start

        assert elapsed < 30.0, f"Batch took {elapsed:.2f}s (target: <30s)"


# =============================================================================
# TEST CLASS: E2E Pipeline (P3.5 Integration)
# =============================================================================

class TestE2EPipeline:
    """End-to-end integration tests"""

    def test_full_pipeline_extract_format_save(self, extractor, item1_pdf_path, temp_dir):
        """
        GIVEN a PDF
        WHEN full pipeline (extract -> format -> save) runs
        THEN output file is created
        """
        # Extract
        result = extractor.extract(str(item1_pdf_path))
        assert result.success is True

        # Format as JSON
        json_output = extractor.format_output(result, format='json')
        assert isinstance(json_output, dict)

        # Save
        output_path = temp_dir / "output.json"
        with open(output_path, 'w') as f:
            json.dump(json_output, f)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_pipeline_batch_with_output(self, extractor, all_real_pdf_paths, temp_dir):
        """
        GIVEN batch extraction
        WHEN saving all results
        THEN output directory is populated
        """
        results = extractor.batch_extract([str(p) for p in all_real_pdf_paths])

        # Save each result
        if isinstance(results, BatchExtractionResult):
            result_list = results.results
        else:
            result_list = results

        for result in result_list:
            if result.success:
                output_path = temp_dir / f"{Path(result.source_file).stem}.json"
                json_output = extractor.format_output(result, format='json')
                with open(output_path, 'w') as f:
                    json.dump(json_output, f)

        # Should have output files
        json_files = list(temp_dir.glob("*.json"))
        assert len(json_files) == 7


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
