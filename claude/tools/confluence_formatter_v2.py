#!/usr/bin/env python3
"""
Confluence Storage Format Formatter V2
Based on actual working Confluence pages
Uses proper macros and table structure that renders correctly
"""

import re
import html as html_lib


def markdown_to_confluence_storage(markdown_text: str) -> str:
    """
    Convert markdown to Confluence storage format (HTML)
    Based on proven formatting from working Confluence pages
    """

    lines = markdown_text.split('\n')
    result = []
    in_code_block = False
    in_table = False
    table_header = False
    in_list = False
    code_lang = ''
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code blocks with ```
        if line.startswith('```'):
            if in_code_block:
                # Close code block
                code_content = '\n'.join(code_lines)
                result.append('<pre>')
                result.append(html_lib.escape(code_content))
                result.append('</pre>')
                in_code_block = False
                code_lines = []
                code_lang = ''
            else:
                code_lang = line[3:].strip()
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            if in_list:
                result.append('</ul>')
                in_list = False

            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            result.append(f'<h{level}>{html_lib.escape(title)}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+$', line):
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append('<hr />')
            i += 1
            continue

        # Tables - use proper thead/tbody structure
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                result.append('<table>')
                table_header = True  # First row is header

            # Parse table row
            cells = [c.strip() for c in line.split('|')[1:-1]]

            # Skip separator rows (|---|---|)
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue

            if table_header:
                result.append('<thead>')
                result.append('<tr>')
                for cell in cells:
                    cell_html = process_inline_formatting(cell)
                    result.append(f'<th>{cell_html}</th>')
                result.append('</tr>')
                result.append('</thead>')
                result.append('<tbody>')
                table_header = False
            else:
                result.append('<tr>')
                for cell in cells:
                    cell_html = process_inline_formatting(cell)
                    result.append(f'<td>{cell_html}</td>')
                result.append('</tr>')

            i += 1
            continue
        elif in_table:
            # End table
            result.append('</tbody></table>')
            in_table = False
            table_header = False

        # Lists (unordered)
        list_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        if list_match:
            if not in_list:
                result.append('<ul>')
                in_list = True

            content = list_match.group(2)
            content_html = process_inline_formatting(content)
            result.append(f'<li>{content_html}</li>')
            i += 1
            continue

        # Close lists if we hit non-list content
        if in_list and not list_match:
            result.append('</ul>')
            in_list = False

        # Info panels (look for blockquotes or special markers)
        if line.startswith('>'):
            content = line[1:].strip()
            content_html = process_inline_formatting(content)
            result.append('<blockquote>')
            result.append(f'<p>{content_html}</p>')
            result.append('</blockquote>')
            i += 1
            continue

        # Empty lines - skip them
        if not line.strip():
            i += 1
            continue

        # Regular paragraphs
        content_html = process_inline_formatting(line)
        result.append(f'<p>{content_html}</p>')
        i += 1

    # Close any remaining open tags
    if in_code_block:
        code_content = '\n'.join(code_lines)
        result.append('<pre>')
        result.append(html_lib.escape(code_content))
        result.append('</pre>')
    if in_table:
        result.append('</tbody></table>')
    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


def process_inline_formatting(text: str) -> str:
    """
    Process inline markdown formatting
    Preserves emojis and special characters
    """
    # Code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold (** or __)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic (* or _) - but not if part of **
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    # Arrow symbols
    text = text.replace('→', '&rarr;')
    text = text.replace('←', '&larr;')

    # Preserve emojis and checkboxes (they work as-is in Confluence)
    # ✅ ❌ ⚠️ 🟡 etc - no conversion needed

    return text


def main():
    """CLI interface for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: confluence_formatter_v2.py <markdown_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        markdown = f.read()

    confluence_html = markdown_to_confluence_storage(markdown)
    print(confluence_html)


if __name__ == '__main__':
    main()
