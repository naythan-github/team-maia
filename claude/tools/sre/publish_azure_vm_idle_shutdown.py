#!/usr/bin/env python3
"""
Publish Azure VM Idle Shutdown Documentation to Orro Confluence Space

Uses ReliableConfluenceClient to publish Azure VM cost optimization documentation.

Created: 2026-01-11
"""

import sys
import re
from pathlib import Path

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from _reliable_confluence_client import ReliableConfluenceClient


def convert_markdown_to_confluence_html(markdown_file_path):
    """
    Convert Azure VM Idle Shutdown markdown to Confluence HTML.

    This performs basic markdown → HTML conversion with Confluence-specific macros.
    """

    with open(markdown_file_path, 'r') as f:
        content = f.read()

    # Start with raw content
    html = content

    # Remove YAML frontmatter if present
    html = re.sub(r'^---\n.*?\n---\n', '', html, flags=re.DOTALL)

    # Headers (do H3 first, then H2, then H1 to avoid conflicts)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Code blocks with language
    def replace_code_block(match):
        lang = match.group(1) or 'text'
        code = match.group(2)
        return f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{lang}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>'

    html = re.sub(r'```([a-z]*)\n(.*?)\n```', replace_code_block, html, flags=re.DOTALL)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Bold text
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)

    # Italic text
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

    # Links - convert markdown links to HTML links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Tables
    lines = html.split('\n')
    html_lines = []
    in_table = False
    table_header_done = False

    for i, line in enumerate(lines):
        if '|' in line and not in_table:
            # Start of table
            in_table = True
            table_header_done = False
            html_lines.append('<table>')

            # Parse header row
            headers = [h.strip() for h in line.split('|')[1:-1]]
            html_lines.append('<thead><tr>')
            for header in headers:
                html_lines.append(f'<th>{header}</th>')
            html_lines.append('</tr></thead>')

        elif '|' in line and in_table:
            # Check if separator row
            if '---' in line or ':-' in line:
                if not table_header_done:
                    html_lines.append('<tbody>')
                    table_header_done = True
                continue

            # Data row
            cells = [c.strip() for c in line.split('|')[1:-1]]
            html_lines.append('<tr>')
            for cell in cells:
                html_lines.append(f'<td>{cell}</td>')
            html_lines.append('</tr>')

        elif in_table and '|' not in line:
            # End of table
            in_table = False
            table_header_done = False
            html_lines.append('</tbody></table>')
            html_lines.append(line)

        else:
            html_lines.append(line)

    # Close any open table
    if in_table:
        html_lines.append('</tbody></table>')

    html = '\n'.join(html_lines)

    # Unordered lists (convert - at start of line to <li>)
    html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Wrap consecutive <li> items in <ul>
    def wrap_list_items(text):
        result = []
        in_list = False
        for line in text.split('\n'):
            if line.strip().startswith('<li>'):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                result.append(line)
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)
        if in_list:
            result.append('</ul>')
        return '\n'.join(result)

    html = wrap_list_items(html)

    # Horizontal rules
    html = re.sub(r'^---+\s*$', '<hr/>', html, flags=re.MULTILINE)

    # Paragraphs - wrap non-HTML lines in <p> tags
    lines = html.split('\n')
    html_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip if empty, already HTML, or in code block
        if not stripped or stripped.startswith('<') or stripped.startswith('![['):
            html_lines.append(line)
        else:
            # Wrap in paragraph if it's plain text
            html_lines.append(f'<p>{line}</p>')

    html = '\n'.join(html_lines)

    # Clean up excessive newlines
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html


def main():
    print("="*80)
    print("Publishing Azure VM Idle Shutdown Documentation to Orro Confluence Space")
    print("="*80)
    print()

    # Initialize Confluence client
    client = ReliableConfluenceClient()

    # Run health check
    print("🏥 Running health check...")
    health_status = client.health_check()
    print(f"   Status: {health_status['status']}")
    print(f"   Success Rate: {health_status['metrics']['success_rate']}")
    print()

    # Convert markdown to HTML
    markdown_file = Path(__file__).parent / "CONFLUENCE_Azure_VM_Idle_Shutdown.md"

    if not markdown_file.exists():
        print(f"❌ ERROR: {markdown_file} not found")
        return 1

    print(f"📄 Converting markdown to Confluence HTML...")
    print(f"   Source: {markdown_file.name}")

    try:
        html_content = convert_markdown_to_confluence_html(markdown_file)
        print(f"   ✅ Conversion complete ({len(html_content)} characters)")
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()

    # Create page in Orro space
    space_key = "Orro"
    title = "Azure VM Idle Shutdown - Cost Optimization Solution"

    print(f"📝 Creating Confluence page...")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print()

    try:
        result = client.create_page(
            space_key=space_key,
            title=title,
            content=html_content,
            validate_html=False  # Disable strict validation for basic macros
        )

        if result:
            print("="*80)
            print("✅ SUCCESS - Page Published to Confluence")
            print("="*80)
            print()
            print(f"Space: {space_key}")
            print(f"Title: {title}")
            print(f"Page ID: {result.get('id', 'Unknown')}")
            if 'url' in result:
                print(f"URL: {result['url']}")
            print()
            print("📊 View page in Confluence Orro space:")
            print("   https://vivoemc.atlassian.net/wiki/spaces/Orro/")
            print()
            return 0
        else:
            print("❌ Failed to create page (no result returned)")
            return 1

    except Exception as e:
        print(f"❌ Error creating page: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
