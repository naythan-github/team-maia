#!/usr/bin/env python3
"""
Prepare DOCX for Markdown Conversion

Fixes common issues when converting Word documents to markdown:
- Removes Unicode line separators (U+2028, U+2029)
- Splits paragraph text into sentence-level bullets
- Adds trailing spaces for proper markdown rendering
- Handles merged section headers

Use Case: Clean up Word docs before converting to markdown/DOCX with pandoc

Usage:
    python3 prepare_docx_for_markdown.py INPUT.docx
    python3 prepare_docx_for_markdown.py INPUT.docx --output cleaned.md

Agent: Document Conversion Specialist Agent
Phase: 177 - JD Formatting Automation
"""

import sys
import subprocess
from pathlib import Path
import argparse


def docx_to_text(path: Path) -> str:
    """
    Convert DOCX to plain text using macOS textutil.
    Removes Unicode line separators that cause formatting issues.
    """
    result = subprocess.run(
        ['textutil', '-convert', 'txt', '-stdout', str(path)],
        capture_output=True,
        text=True
    )
    # Replace Unicode line/paragraph separators with spaces
    text = result.stdout.replace('\u2028', ' ').replace('\u2029', ' ')
    return text


def bulletize(text: str) -> str:
    """
    Convert paragraph text into sentence-level bullets.

    - Splits on '. ' (period + space)
    - Protects common abbreviations (e.g., i.e., etc.)
    - Adds bullet character (•)
    - Adds two trailing spaces for markdown hard line break
    """
    # Protect abbreviations from sentence splitting
    text = text.replace('\u2028', ' ').replace('\u2029', ' ')
    text = text.replace('e.g.', 'E_G_')
    text = text.replace('i.e.', 'I_E_')
    text = text.replace('etc.', 'ETC_')

    # Split into sentences
    parts = text.split('. ')
    bullets = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Restore abbreviations
        part = part.replace('E_G_', 'e.g.')
        part = part.replace('I_E_', 'i.e.')
        part = part.replace('ETC_', 'etc.')

        # Add period if missing
        if not part.endswith('.'):
            part += '.'

        # Add bullet + two trailing spaces (markdown line break)
        bullets.append(f'• {part}  ')

    return '\n'.join(bullets)


def process_generic_document(input_docx: Path, output_md: Path):
    """
    Generic document processor - converts DOCX to cleaned markdown.

    Handles:
    - Section headers (## format)
    - Subsection headers (### format)
    - Paragraph text converted to bullets
    - Unicode separator cleanup
    """
    raw = docx_to_text(input_docx)
    lines = raw.split('\n')

    out = []
    i = 0

    print(f"📄 Processing: {input_docx.name}")
    print(f"   Lines: {len(lines)}")

    sections_found = 0
    bullets_created = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Detect section headers (ALL CAPS, no period at end)
        if line.isupper() and not line.endswith('.'):
            out.append(f'## {line}\n')
            sections_found += 1
            i += 1

            # Check if next line is content or subsection
            if i < len(lines):
                next_line = lines[i].strip()

                # If next line starts with content, it might be merged
                if next_line and not next_line.isupper():
                    # Check if it's a subsection header or content
                    if i+1 < len(lines) and lines[i+1].strip().endswith('.'):
                        # It's a subsection header
                        out.append(f'### {next_line}')
                        i += 1

                        # Collect paragraph for bulletizing
                        para = []
                        while i < len(lines):
                            p = lines[i].strip()
                            if not p or p.isupper():
                                break
                            # Check if next line is another subsection
                            if i+1 < len(lines):
                                peek = lines[i+1].strip()
                                if peek and not peek.endswith('.') and not p.endswith('.'):
                                    break
                            para.append(p)
                            i += 1

                        if para:
                            bullets = bulletize(' '.join(para))
                            bullets_created += len(bullets.split('\n'))
                            out.append(bullets)
                            out.append('')
                    else:
                        # It's regular content under the section
                        para = [next_line]
                        i += 1
                        while i < len(lines):
                            p = lines[i].strip()
                            if not p or p.isupper():
                                break
                            para.append(p)
                            i += 1

                        if para:
                            out.append(' '.join(para) + '\n')
            continue

        i += 1

    # Write output
    with open(output_md, 'w') as f:
        f.write('\n'.join(out))

    print(f"   ✅ Sections: {sections_found}")
    print(f"   ✅ Bullets: {bullets_created}")
    print(f"💾 Saved: {output_md.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare DOCX for markdown conversion - clean bullets and formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (outputs INPUT.md)
  python3 prepare_docx_for_markdown.py job_description.docx

  # Specify output path
  python3 prepare_docx_for_markdown.py draft.docx --output clean.md

What it fixes:
  - Unicode line separators (U+2028, U+2029) from Word
  - Paragraph-style text → sentence-level bullets
  - Missing markdown line breaks (adds 2 trailing spaces)
  - Merged section headers (splits properly)
        """
    )
    parser.add_argument('input', type=Path, help='Input DOCX file')
    parser.add_argument('--output', '-o', type=Path, help='Output markdown file (default: INPUT.md)')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: File not found: {args.input}")
        sys.exit(1)

    if not args.input.suffix.lower() == '.docx':
        print(f"❌ Error: Input must be a .docx file")
        sys.exit(1)

    # Determine output path
    output = args.output if args.output else args.input.with_suffix('.md')

    print("=" * 70)
    print("DOCX → MARKDOWN PREPARATION")
    print("=" * 70)
    print()

    try:
        process_generic_document(args.input, output)
        print()
        print("✅ Complete!")
        print()
        print("🎯 NEXT STEPS:")
        print(f"   1. Review {output.name}")
        print(f"   2. Make any manual adjustments if needed")
        print(f"   3. Convert to styled DOCX:")
        print(f"      python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py {output}")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
