#!/usr/bin/env python3
"""
Normalize Markdown Formatting for DOCX Conversion

Takes markdown files with variable/inconsistent formatting and normalizes them
to Orro standards for clean DOCX conversion.

Fixes:
- Inconsistent bullet characters (-, *, +) → standardized •
- Paragraph-style text → sentence-level bullets
- Missing trailing spaces for markdown line breaks
- Inconsistent heading levels
- Mixed line endings

Use Case: Clean up markdown files from any source before DOCX conversion

Usage:
    python3 normalize_markdown.py INPUT.md
    python3 normalize_markdown.py INPUT.md --output cleaned.md
    python3 normalize_markdown.py INPUT.md --bullets-only  # Only fix bullets, skip other formatting

Agent: Document Conversion Specialist Agent
Phase: 177 - JD Formatting Automation
"""

import sys
import re
from pathlib import Path
import argparse


def normalize_bullets(text: str) -> str:
    """
    Normalize bullet formatting:
    - Replace -, *, + with •
    - Ensure space after bullet
    - Add trailing spaces for markdown line breaks
    """
    lines = text.split('\n')
    normalized = []

    for line in lines:
        # Match common bullet patterns: -, *, +, •
        bullet_match = re.match(r'^(\s*)([-*+•])\s+(.+)$', line)

        if bullet_match:
            indent, bullet, content = bullet_match.groups()
            # Normalize to • with trailing spaces
            normalized.append(f'{indent}• {content.rstrip()}  ')
        else:
            normalized.append(line)

    return '\n'.join(normalized)


def split_paragraphs_to_bullets(text: str, under_headers: bool = True) -> str:
    """
    Convert paragraph-style text to sentence-level bullets.

    Args:
        text: Input text
        under_headers: Only bulletize paragraphs under headers (default: True)
    """
    lines = text.split('\n')
    result = []
    i = 0
    in_bullet_context = False

    while i < len(lines):
        line = lines[i].strip()

        # Detect headers (markdown # syntax)
        if line.startswith('#'):
            result.append(lines[i])
            in_bullet_context = under_headers
            i += 1
            continue

        # Skip existing bullets
        if re.match(r'^[-*+•]\s+', line):
            result.append(lines[i])
            i += 1
            continue

        # Skip empty lines
        if not line:
            result.append(lines[i])
            in_bullet_context = False
            i += 1
            continue

        # Check if line looks like paragraph text (ends with period, has multiple sentences)
        is_paragraph = (
            line.endswith('.') and
            '. ' in line and
            (in_bullet_context or not under_headers)
        )

        if is_paragraph:
            # Split into sentences and bulletize
            sentences = split_sentences(line)
            for sentence in sentences:
                result.append(f'• {sentence}  ')
        else:
            result.append(lines[i])

        i += 1

    return '\n'.join(result)


def split_sentences(text: str) -> list:
    """
    Split text into sentences, protecting common abbreviations.
    """
    # Protect abbreviations
    text = text.replace('e.g.', 'E_G_')
    text = text.replace('i.e.', 'I_E_')
    text = text.replace('etc.', 'ETC_')
    text = text.replace('Dr.', 'DR_')
    text = text.replace('Mr.', 'MR_')
    text = text.replace('Ms.', 'MS_')
    text = text.replace('Mrs.', 'MRS_')

    # Split on '. ' (period + space)
    parts = text.split('. ')

    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Restore abbreviations
        part = part.replace('E_G_', 'e.g.')
        part = part.replace('I_E_', 'i.e.')
        part = part.replace('ETC_', 'etc.')
        part = part.replace('DR_', 'Dr.')
        part = part.replace('MR_', 'Mr.')
        part = part.replace('MS_', 'Ms.')
        part = part.replace('MRS_', 'Mrs.')

        # Add period if missing
        if not part.endswith('.'):
            part += '.'

        sentences.append(part)

    return sentences


def normalize_headers(text: str) -> str:
    """
    Normalize header formatting:
    - Ensure space after # characters
    - Remove extra whitespace
    """
    lines = text.split('\n')
    normalized = []

    for line in lines:
        # Match markdown headers
        header_match = re.match(r'^(#{1,6})\s*(.+)$', line)

        if header_match:
            hashes, content = header_match.groups()
            # Normalize: hashes + space + content
            normalized.append(f'{hashes} {content.strip()}')
        else:
            normalized.append(line)

    return '\n'.join(normalized)


def remove_trailing_whitespace(text: str, preserve_bullet_spaces: bool = True) -> str:
    """
    Remove trailing whitespace from lines, but preserve intentional trailing spaces on bullets.
    """
    lines = text.split('\n')
    cleaned = []

    for line in lines:
        if preserve_bullet_spaces and re.match(r'^(\s*)•\s+.+\s{2}$', line):
            # Preserve bullets with 2 trailing spaces
            cleaned.append(line)
        else:
            # Strip trailing whitespace
            cleaned.append(line.rstrip())

    return '\n'.join(cleaned)


def normalize_line_endings(text: str) -> str:
    """
    Normalize line endings to \n (Unix style).
    """
    # Replace Windows (\r\n) and old Mac (\r) line endings
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    return text


def normalize_markdown(
    input_text: str,
    bullets_only: bool = False,
    split_paragraphs: bool = True
) -> str:
    """
    Complete markdown normalization pipeline.

    Args:
        input_text: Raw markdown text
        bullets_only: Only normalize bullets, skip other fixes
        split_paragraphs: Convert paragraphs to bullets

    Returns:
        Normalized markdown text
    """
    text = input_text

    # Always normalize line endings
    text = normalize_line_endings(text)

    if bullets_only:
        # Only fix bullet formatting
        text = normalize_bullets(text)
    else:
        # Full normalization
        text = normalize_headers(text)

        if split_paragraphs:
            text = split_paragraphs_to_bullets(text)

        text = normalize_bullets(text)
        text = remove_trailing_whitespace(text, preserve_bullet_spaces=True)

    return text


def main():
    parser = argparse.ArgumentParser(
        description="Normalize markdown formatting for DOCX conversion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full normalization (bullets, headers, paragraph splitting)
  python3 normalize_markdown.py draft.md

  # Only fix bullets (preserve everything else)
  python3 normalize_markdown.py draft.md --bullets-only

  # Specify output path
  python3 normalize_markdown.py draft.md --output clean.md

  # Skip paragraph splitting (only normalize existing bullets)
  python3 normalize_markdown.py draft.md --no-split-paragraphs

What it fixes:
  - Inconsistent bullets (-, *, +) → standardized •
  - Missing trailing spaces on bullets
  - Paragraph text → sentence-level bullets
  - Inconsistent header formatting
  - Mixed line endings

Ready for:
  - Orro DOCX conversion (convert_md_to_docx.py)
  - Version control (consistent formatting)
  - Clean markdown rendering
        """
    )
    parser.add_argument('input', type=Path, help='Input markdown file')
    parser.add_argument('--output', '-o', type=Path, help='Output file (default: INPUT_normalized.md)')
    parser.add_argument('--bullets-only', action='store_true', help='Only normalize bullets, skip other formatting')
    parser.add_argument('--no-split-paragraphs', action='store_true', help='Do not split paragraphs into bullets')

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: File not found: {args.input}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output = args.output
    else:
        output = args.input.with_stem(f'{args.input.stem}_normalized')

    print("=" * 70)
    print("MARKDOWN NORMALIZATION")
    print("=" * 70)
    print()
    print(f"📄 Reading: {args.input.name}")

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        input_text = f.read()

    # Normalize
    normalized = normalize_markdown(
        input_text,
        bullets_only=args.bullets_only,
        split_paragraphs=not args.no_split_paragraphs
    )

    # Write output
    with open(output, 'w', encoding='utf-8') as f:
        f.write(normalized)

    print(f"💾 Saved: {output.name}")
    print()

    # Show what changed
    original_lines = input_text.split('\n')
    normalized_lines = normalized.split('\n')

    bullets_before = sum(1 for line in original_lines if re.match(r'^[-*+•]\s+', line.strip()))
    bullets_after = sum(1 for line in normalized_lines if re.match(r'^•\s+', line.strip()))

    print("📊 Changes:")
    print(f"   Lines: {len(original_lines)} → {len(normalized_lines)}")
    print(f"   Bullets: {bullets_before} → {bullets_after}")

    if args.bullets_only:
        print(f"   Mode: Bullets only")
    else:
        print(f"   Mode: Full normalization")

    print()
    print("✅ Normalization complete!")
    print()
    print("🎯 NEXT STEPS:")
    print(f"   1. Review {output.name}")
    print(f"   2. Convert to DOCX:")
    print(f"      python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py {output}")
    print()


if __name__ == "__main__":
    main()
