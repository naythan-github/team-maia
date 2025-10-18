#!/usr/bin/env python3
"""
⚠️  DEPRECATED - DO NOT USE ⚠️

This tool has been superseded by confluence_html_builder.py

REASON: Naive string replacement causes malformed HTML (state-blind, structure-unaware)
INCIDENT: Phase 122 - Abdullah Kazim interview prep had malformed HTML requiring manual rework
ROOT CAUSE: String replacement cannot handle paired markers, creates orphaned tags
REPLACEMENT: Use ConfluencePageBuilder for validated, template-based HTML generation
MIGRATION GUIDE: See claude/documentation/CONFLUENCE_TOOLING_GUIDE.md

Production Tool: claude/tools/reliable_confluence_client.py + confluence_html_builder.py
Status: Moved to claude/tools/deprecated/ (Phase 129)

ORIGINAL DESCRIPTION (for historical reference):
Confluence Storage Format Formatter
Converts markdown to proper Confluence storage format HTML
"""

import re
import html
import warnings

# Deprecation warning
warnings.warn(
    "confluence_formatter.py is DEPRECATED. Use confluence_html_builder.py instead. "
    "See claude/documentation/CONFLUENCE_TOOLING_GUIDE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


def markdown_to_confluence_storage(markdown_text: str) -> str:
    """
    Convert markdown to Confluence storage format (HTML)

    Handles:
    - Headers (h1-h6)
    - Bold, italic, code
    - Tables
    - Lists (ordered and unordered)
    - Code blocks
    - Emojis and special characters
    """

    lines = markdown_text.split('\n')
    result = []
    in_code_block = False
    in_table = False
    in_list = False
    list_level = 0
    code_lang = ''

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                result.append('</code></ac:plain-text-body></ac:structured-macro>')
                in_code_block = False
                code_lang = ''
            else:
                code_lang = line[3:].strip()
                result.append(f'<ac:structured-macro ac:name="code" ac:schema-version="1">')
                if code_lang:
                    result.append(f'<ac:parameter ac:name="language">{html.escape(code_lang)}</ac:parameter>')
                result.append('<ac:plain-text-body><![CDATA[')
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            result.append(html.escape(line))
            i += 1
            continue

        # Headers
        if line.startswith('#'):
            # Close any open lists
            if in_list:
                result.append('</ul>' * list_level)
                in_list = False
                list_level = 0

            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                result.append(f'<h{level}>{html.escape(title)}</h{level}>')
                i += 1
                continue

        # Tables
        if '|' in line and not in_table:
            # Start table
            in_table = True
            result.append('<table class="wrapped"><tbody>')

        if in_table and '|' in line:
            # Parse table row
            cells = [c.strip() for c in line.split('|')[1:-1]]  # Remove empty first/last

            # Skip separator rows
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue

            result.append('<tr>')
            for cell in cells:
                # Process inline formatting
                cell_html = process_inline_formatting(cell)
                result.append(f'<td>{cell_html}</td>')
            result.append('</tr>')
            i += 1
            continue
        elif in_table and '|' not in line:
            # End table
            result.append('</tbody></table>')
            in_table = False

        # Lists
        list_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            content = list_match.group(2)

            new_level = indent // 2 + 1

            if not in_list:
                result.append('<ul>')
                in_list = True
                list_level = 1
            elif new_level > list_level:
                result.append('<ul>' * (new_level - list_level))
                list_level = new_level
            elif new_level < list_level:
                result.append('</ul>' * (list_level - new_level))
                list_level = new_level

            content_html = process_inline_formatting(content)
            result.append(f'<li>{content_html}</li>')
            i += 1
            continue

        # Close lists if we hit non-list content
        if in_list and not list_match:
            result.append('</ul>' * list_level)
            in_list = False
            list_level = 0

        # Horizontal rule
        if re.match(r'^---+$', line):
            result.append('<hr />')
            i += 1
            continue

        # Blockquotes
        if line.startswith('>'):
            content = line[1:].strip()
            content_html = process_inline_formatting(content)
            result.append(f'<blockquote><p>{content_html}</p></blockquote>')
            i += 1
            continue

        # Empty lines
        if not line.strip():
            result.append('<p>&nbsp;</p>')
            i += 1
            continue

        # Regular paragraphs
        content_html = process_inline_formatting(line)
        result.append(f'<p>{content_html}</p>')
        i += 1

    # Close any remaining open tags
    if in_code_block:
        result.append('</code></ac:plain-text-body></ac:structured-macro>')
    if in_table:
        result.append('</tbody></table>')
    if in_list:
        result.append('</ul>' * list_level)

    return '\n'.join(result)


def process_inline_formatting(text: str) -> str:
    """
    Process inline markdown formatting (bold, italic, code, links)
    Preserves emojis and special characters
    """
    # Don't escape special characters yet - process markdown first

    # Code inline (before other formatting)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold (** or __)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic (* or _)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    # Now escape HTML entities (but preserve tags we just created)
    # This is a simplified approach - in production use proper HTML parser

    return text


def main():
    """CLI interface for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: confluence_formatter.py <markdown_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        markdown = f.read()

    confluence_html = markdown_to_confluence_storage(markdown)
    print(confluence_html)


if __name__ == '__main__':
    main()
