#!/usr/bin/env python3
"""
Generic Markdown to DOCX Converter with Orro Corporate Styling

Converts ANY markdown document to DOCX with Orro corporate branding:
- Aptos font (corporate standard)
- Purple table styling (_Orro Table 1)
- Standard 1.0" margins
- Professional formatting

Usage:
    python3 convert_md_to_docx.py document.md
    python3 convert_md_to_docx.py document.md --output custom.docx
    python3 convert_md_to_docx.py document.md --no-table-styles  # Skip table styling

Agent: Document Conversion Specialist Agent
Phase: 163 - Template Reorganization
"""

import sys
import subprocess
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# Template paths
MAIA_ROOT = Path.home() / "git" / "maia"
ORRO_CORPORATE_REFERENCE = MAIA_ROOT / "claude/tools/document_conversion/templates/orro_corporate_reference.docx"
TABLE_STYLE_NAME = "_Orro Table 1"


def convert_md_to_docx(input_md: Path, output_docx: Path, apply_table_styles: bool = True):
    """
    Convert Markdown to DOCX with Orro corporate styling.

    Steps:
    1. Pandoc: MD → DOCX (with Orro corporate reference template)
    2. python-docx: Apply _Orro Table 1 style to all tables (optional)
    3. python-docx: Set tables to 100% width

    Args:
        input_md: Path to input markdown file
        output_docx: Path to output DOCX file
        apply_table_styles: Whether to apply Orro table styling (default: True)

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
    print(f"🔄 Converting with Pandoc + Orro corporate styling...")

    if apply_table_styles:
        temp_output = output_docx.with_suffix('.temp.docx')
    else:
        temp_output = output_docx

    pandoc_cmd = [
        'pandoc',
        str(input_md),
        '--reference-doc', str(ORRO_CORPORATE_REFERENCE),
        '-o', str(temp_output)
    ]

    try:
        result = subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ Pandoc conversion complete")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Pandoc failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   ❌ Pandoc not found. Install: brew install pandoc")
        return False

    # Step 2: Apply table styles (optional)
    if apply_table_styles:
        print(f"🎨 Applying Orro table styles...")

        doc = Document(temp_output)

        # Check if _Orro Table 1 style exists
        style_exists = TABLE_STYLE_NAME in [s.name for s in doc.styles if hasattr(s, 'name')]

        if not style_exists:
            print(f"   ⚠️  Warning: '{TABLE_STYLE_NAME}' style not found in template")
            print(f"   Tables will use default styling")

        tables_modified = 0
        for table in doc.tables:
            try:
                # Apply Orro Table 1 style
                if style_exists:
                    table.style = TABLE_STYLE_NAME

                # Set table width to 100% using XML
                tbl = table._element
                tblPr = tbl.tblPr
                if tblPr is not None:
                    tblW = tblPr.find(qn('w:tblW'))
                    if tblW is not None:
                        tblW.set(qn('w:type'), 'pct')
                        tblW.set(qn('w:w'), '5000')  # 5000 = 100% (50.00%)
                    else:
                        # Create tblW element
                        tblW = OxmlElement('w:tblW')
                        tblW.set(qn('w:type'), 'pct')
                        tblW.set(qn('w:w'), '5000')
                        tblPr.append(tblW)

                tables_modified += 1

            except Exception as e:
                print(f"   ⚠️  Could not style table: {e}")

        print(f"   ✅ Styled {tables_modified} tables")

        # Save final output
        print(f"💾 Saving: {output_docx.name}")
        doc.save(output_docx)

        # Clean up temp file
        temp_output.unlink()

    print(f"\n✅ Conversion complete!")
    print(f"   Input:  {input_md}")
    print(f"   Output: {output_docx}")
    if apply_table_styles:
        print(f"   Tables: {tables_modified} styled with '{TABLE_STYLE_NAME}'")
    print(f"   Font: Aptos (Orro corporate standard)")
    print(f"   Margins: 1.0\" all sides")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Markdown to DOCX with Orro corporate styling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert with Orro styling
  python3 convert_md_to_docx.py technical_doc.md

  # Specify output path
  python3 convert_md_to_docx.py meeting_notes.md --output "2024-11-21 Meeting Notes.docx"

  # Skip table styling (faster for docs without tables)
  python3 convert_md_to_docx.py simple_doc.md --no-table-styles

Use Cases:
  - Technical documentation
  - Meeting notes
  - Project reports
  - Any markdown → DOCX with corporate branding
        """
    )
    parser.add_argument('input', type=Path, help='Input Markdown file')
    parser.add_argument('--output', '-o', type=Path, help='Output DOCX file (default: same name as input)')
    parser.add_argument('--no-table-styles', action='store_true', help='Skip table styling step (faster)')

    args = parser.parse_args()

    # Determine output path
    output = args.output if args.output else args.input.with_suffix('.docx')

    print("=" * 70)
    print("MARKDOWN → DOCX CONVERTER (Orro Corporate Styling)")
    print("=" * 70)
    print()

    # Convert
    success = convert_md_to_docx(args.input, output, apply_table_styles=not args.no_table_styles)

    if not success:
        sys.exit(1)

    print()
    print("🎯 NEXT STEPS:")
    print(f"   1. Open {output.name} in Word")
    print(f"   2. Verify Orro corporate styling (Aptos font, purple tables)")
    print(f"   3. Make any final adjustments")
    print()


if __name__ == "__main__":
    main()
