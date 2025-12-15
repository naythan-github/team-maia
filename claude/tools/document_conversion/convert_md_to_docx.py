#!/usr/bin/env python3
"""
Generic Markdown to DOCX Converter with Orro Corporate Styling

Converts ANY markdown document to DOCX with Orro corporate branding:
- Aptos font (corporate standard)
- Purple table styling with explicit RGB borders
- Content-aware column widths
- Orro purple headings RGB(112, 48, 160)
- Standard 1.0" margins

Full Pipeline:
1. Pandoc: MD → DOCX (with Orro corporate reference template)
2. PIR Normalizer: Explicit RGB borders, content-aware widths, Aptos font
3. Purple headings: Apply Orro purple to all headings

Usage:
    python3 convert_md_to_docx.py document.md
    python3 convert_md_to_docx.py document.md --output custom.docx
    python3 convert_md_to_docx.py document.md --no-table-styles  # Skip table styling

Agent: Document Conversion Specialist Agent
Phase: 163 - Template Reorganization (Updated Dec 2025 with full pipeline)
"""

import sys
import subprocess
from pathlib import Path

# Portable path resolution - derive from script location
# This file is at: claude/tools/document_conversion/convert_md_to_docx.py
# Maia root is 4 levels up
MAIA_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from docx import Document
from docx.shared import RGBColor

# Import the normalizer functions for proper OOXML formatting
from claude.tools.document.pir.pir_docx_normalizer import normalize_document

# Template paths
ORRO_CORPORATE_REFERENCE = MAIA_ROOT / "claude/tools/document_conversion/templates/orro_corporate_reference.docx"
TABLE_STYLE_NAME = "_Orro Table 1"
ORRO_PURPLE = RGBColor(112, 48, 160)


def apply_purple_headings(doc_path: Path) -> int:
    """
    Apply Orro purple color to all headings in the document.

    Args:
        doc_path: Path to the DOCX file

    Returns:
        Number of headings colored
    """
    doc = Document(str(doc_path))
    headings_colored = 0

    for paragraph in doc.paragraphs:
        if paragraph.style.name in ['Heading 1', 'Heading 2', 'Heading 3']:
            for run in paragraph.runs:
                run.font.color.rgb = ORRO_PURPLE
            headings_colored += 1

    doc.save(str(doc_path))
    return headings_colored


def convert_md_to_docx(input_md: Path, output_docx: Path, apply_table_styles: bool = True):
    """
    Convert Markdown to DOCX with full Orro corporate styling.

    Full Pipeline:
    1. Pandoc: MD → DOCX (with Orro corporate reference template)
    2. PIR Normalizer: Explicit RGB borders, content-aware widths, Aptos font
    3. Purple headings: Apply Orro purple to all headings

    Args:
        input_md: Path to input markdown file
        output_docx: Path to output DOCX file
        apply_table_styles: Whether to apply full Orro table styling (default: True)

    Returns:
        bool: True if successful, False otherwise
    """

    if not input_md.exists():
        print(f"❌ Error: Input file not found: {input_md}")
        return False

    if not ORRO_CORPORATE_REFERENCE.exists():
        print(f"❌ Error: Orro corporate reference template not found: {ORRO_CORPORATE_REFERENCE}")
        print(f"   Run: python3 {MAIA_ROOT}/claude/tools/document_conversion/create_clean_orro_template.py")
        return False

    # Step 1: Pandoc conversion
    print(f"📄 Reading: {input_md.name}")
    print(f"🔄 Step 1: Pandoc conversion with Orro template...")

    pandoc_cmd = [
        'pandoc',
        str(input_md),
        '--reference-doc', str(ORRO_CORPORATE_REFERENCE),
        '-o', str(output_docx)
    ]

    try:
        subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ Pandoc conversion complete")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Pandoc failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   ❌ Pandoc not found. Install: brew install pandoc")
        return False

    # Step 2: Apply full Orro styling via normalizer
    if apply_table_styles:
        print(f"🎨 Step 2: PIR Normalizer (explicit RGB borders, content-aware widths, Aptos font)...")

        try:
            stats = normalize_document(
                output_docx,
                output_docx,  # Overwrite in place
                verbose=True,
                content_aware=True,
                table_style=TABLE_STYLE_NAME
            )
            print(f"   ✅ Normalized {stats['tables_fixed']} tables with Orro styling")
        except Exception as e:
            print(f"   ⚠️  Normalizer warning: {e}")
            print(f"   Continuing with basic styling...")

        # Step 3: Apply purple headings
        print(f"💜 Step 3: Applying Orro purple to headings...")
        headings_colored = apply_purple_headings(output_docx)
        print(f"   ✅ Applied Orro purple to {headings_colored} headings")

    print(f"\n✅ Conversion complete!")
    print(f"   Input:  {input_md}")
    print(f"   Output: {output_docx}")
    if apply_table_styles:
        print(f"   Tables: Styled with explicit RGB borders (Orro purple #7030A0)")
        print(f"   Headings: {headings_colored} styled with Orro purple RGB(112, 48, 160)")
        print(f"   Columns: Content-aware widths")
        print(f"   Font: Aptos 8pt in tables")
    print(f"   Margins: 1.0\" all sides")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Markdown to DOCX with full Orro corporate styling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert with full Orro styling (recommended)
  python3 convert_md_to_docx.py technical_doc.md

  # Specify output path
  python3 convert_md_to_docx.py meeting_notes.md --output "2024-11-21 Meeting Notes.docx"

  # Skip table styling (faster for docs without tables)
  python3 convert_md_to_docx.py simple_doc.md --no-table-styles

Full Pipeline:
  1. Pandoc conversion with Orro reference template
  2. PIR Normalizer: Explicit RGB borders, content-aware column widths, Aptos font
  3. Orro purple headings: RGB(112, 48, 160)

Use Cases:
  - Technical documentation
  - Meeting notes
  - Project reports
  - SIP documents
  - Any markdown → DOCX with Orro corporate branding
        """
    )
    parser.add_argument('input', type=Path, help='Input Markdown file')
    parser.add_argument('--output', '-o', type=Path, help='Output DOCX file (default: same name as input)')
    parser.add_argument('--no-table-styles', action='store_true', help='Skip table styling step (faster)')

    args = parser.parse_args()

    # Determine output path
    output = args.output if args.output else args.input.with_suffix('.docx')

    print("=" * 70)
    print("MARKDOWN → DOCX CONVERTER (Full Orro Corporate Pipeline)")
    print("=" * 70)
    print()

    # Convert
    success = convert_md_to_docx(args.input, output, apply_table_styles=not args.no_table_styles)

    if not success:
        sys.exit(1)

    print()
    print("🎯 NEXT STEPS:")
    print(f"   1. Open {output.name} in Word")
    print(f"   2. Verify Orro corporate styling (purple borders, Aptos font)")
    print(f"   3. Make any final adjustments")
    print()


if __name__ == "__main__":
    main()
