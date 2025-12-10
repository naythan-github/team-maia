#!/usr/bin/env python3
"""
PIR Converter v3 - Markdown to DOCX with Table Style Application

Uses Pandoc + python-docx to:
1. Convert MD → DOCX with Pandoc (preserves structure)
2. Apply "_Orro Table 1" style to all tables (preserves formatting)

This solves the table formatting issue while keeping all other template styles.

Usage:
    python3 convert_pir_v3.py input.md
    python3 convert_pir_v3.py input.md --output custom.docx

Agent: Document Conversion Specialist + SRE Principal Engineer
"""

import sys
import subprocess
from pathlib import Path
from docx import Document

# Paths - relative to this script's location for portability
SCRIPT_DIR = Path(__file__).parent
REFERENCE_TEMPLATE = SCRIPT_DIR / "templates" / "pir_orro_reference.docx"
TABLE_STYLE_NAME = "_Orro Table 1"


def convert_with_table_styles(input_md: Path, output_docx: Path):
    """
    Convert MD to DOCX using Pandoc, then apply table styles.

    Steps:
    1. Pandoc: MD → DOCX (with reference template)
    2. python-docx: Apply _Orro Table 1 style to all tables
    3. python-docx: Set tables to 100% width
    """

    # Step 1: Pandoc conversion
    print(f"📄 Reading: {input_md.name}")
    print(f"🔄 Converting with Pandoc...")

    temp_output = output_docx.with_suffix('.temp.docx')

    pandoc_cmd = [
        'pandoc',
        str(input_md),
        '--reference-doc', str(REFERENCE_TEMPLATE),
        '-o', str(temp_output)
    ]

    try:
        subprocess.run(pandoc_cmd, check=True, capture_output=True)
        print(f"   ✅ Pandoc conversion complete")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Pandoc failed: {e.stderr.decode()}")
        return False

    # Step 2: Apply table styles
    print(f"🎨 Applying table styles...")

    doc = Document(temp_output)

    # Check if style exists
    style_exists = TABLE_STYLE_NAME in doc.styles
    if not style_exists:
        print(f"   ⚠️  Warning: '{TABLE_STYLE_NAME}' style not found in template")
        print(f"   Available table styles:")
        for style in doc.styles:
            if style.type == 2:  # Table style
                print(f"      - {style.name}")

    tables_modified = 0
    for table in doc.tables:
        try:
            # Apply Orro Table 1 style
            if style_exists:
                table.style = TABLE_STYLE_NAME

            # Note: Width, borders, fonts are handled by pir_docx_normalizer.py
            # which correctly handles OOXML element ordering and explicit RGB colors

            tables_modified += 1

        except Exception as e:
            print(f"   ⚠️  Could not style table: {e}")

    print(f"   ✅ Styled {tables_modified} tables")

    # Step 3: Save final output
    print(f"💾 Saving: {output_docx.name}")
    doc.save(output_docx)

    # Clean up temp file
    temp_output.unlink()

    print(f"\n✅ Conversion complete!")
    print(f"   Input:  {input_md}")
    print(f"   Output: {output_docx}")
    print(f"   Tables: {tables_modified} styled with '{TABLE_STYLE_NAME}'")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert PIR Markdown to DOCX with table styles"
    )
    parser.add_argument('input', type=Path, help='Input Markdown file')
    parser.add_argument('--output', '-o', type=Path, help='Output DOCX file')

    args = parser.parse_args()

    # Determine output path
    output = args.output if args.output else args.input.with_suffix('.docx')

    # Check inputs
    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)

    if not REFERENCE_TEMPLATE.exists():
        print(f"❌ Error: Reference template not found: {REFERENCE_TEMPLATE}")
        sys.exit(1)

    print("=" * 70)
    print("PIR CONVERTER v3 - Pandoc + Table Style Application")
    print("=" * 70)
    print()

    # Convert
    success = convert_with_table_styles(args.input, output)

    if success:
        print()
        print("🎯 NEXT STEPS:")
        print(f"   1. Open {output.name} in Word")
        print(f"   2. Verify table formatting (purple borders, 100% width)")
        print(f"   3. Verify fonts (Aptos)")
        print()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
