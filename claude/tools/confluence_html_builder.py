#!/usr/bin/env python3
"""
Confluence HTML Builder - Generates valid Confluence storage format HTML

PURPOSE: Prevent malformed HTML by using structured builders instead of naive string replacement

INCIDENT CONTEXT: Phase 122 - Abdullah Kazim interview prep had malformed HTML on first attempt
ROOT CAUSE: Naive markdown→HTML conversion using string replacement (state-blind, structure-unaware)
SOLUTION: Template-based HTML generation with validation

USAGE:
    from claude.tools.confluence_html_builder import ConfluencePageBuilder

    builder = ConfluencePageBuilder()
    html = (builder
        .add_info_panel({"Candidate": "John Doe", "Role": "Engineer"})
        .add_heading("Strengths")
        .add_list(["10+ years experience", "Azure expert"])
        .add_expand_section("Questions", "<p>Question 1...</p>")
        .build())

STATUS: ✅ Production Ready - Phase 122 Post-Mortem
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import html
import logging

logger = logging.getLogger(__name__)


class PanelColor(Enum):
    """Standard Confluence panel colors"""
    BLUE = "#deebff"      # Info/neutral
    GREEN = "#e3fcef"     # Success
    YELLOW = "#fffae6"    # Warning
    RED = "#ffebe6"       # Error/critical
    GRAY = "#dfe1e6"      # Neutral/secondary


@dataclass
class ValidationResult:
    """HTML validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for safe Confluence content

    Prevents XSS and rendering issues
    """
    return html.escape(str(text), quote=True)


def validate_confluence_html(html_content: str) -> ValidationResult:
    """
    Validate Confluence storage format HTML before API call

    Checks for common issues:
    - Mismatched tags
    - Orphaned elements
    - Empty tags
    - Malformed macros

    Returns:
        ValidationResult with errors and warnings
    """
    errors = []
    warnings = []

    # Check tag matching
    tags_to_check = ['li', 'ul', 'ol', 'strong', 'em', 'p', 'h1', 'h2', 'h3', 'table', 'tr', 'td', 'th']
    for tag in tags_to_check:
        open_count = html_content.count(f'<{tag}>')
        close_count = html_content.count(f'</{tag}>')
        if open_count != close_count:
            errors.append(f"Mismatched <{tag}> tags: {open_count} open, {close_count} close")

    # Check for orphaned list items
    has_li = '<li>' in html_content
    has_ul = '<ul>' in html_content
    has_ol = '<ol>' in html_content
    if has_li and not has_ul and not has_ol:
        errors.append("List items <li> found without parent <ul> or <ol>")

    # Check for empty tags (usually indicates cleanup needed)
    empty_tags = ['<p></p>', '<li></li>', '<td></td>', '<strong></strong>']
    for empty in empty_tags:
        if empty in html_content:
            warnings.append(f"Empty tag found: {empty}")

    # Check macro structure
    if '<ac:structured-macro' in html_content:
        if 'ac:name=' not in html_content:
            errors.append("Macro found without ac:name attribute")

        # Check balanced macro tags
        macro_open = html_content.count('<ac:structured-macro')
        macro_close = html_content.count('</ac:structured-macro>')
        if macro_open != macro_close:
            errors.append(f"Mismatched macro tags: {macro_open} open, {macro_close} close")

    # Check for unescaped characters (potential XSS)
    dangerous_patterns = [
        ('<script>', 'Unescaped <script> tag found'),
        ('javascript:', 'Potential javascript: protocol found'),
        ('onerror=', 'Potential event handler found'),
    ]
    for pattern, message in dangerous_patterns:
        if pattern in html_content.lower():
            errors.append(f"Security issue: {message}")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


class ConfluencePageBuilder:
    """
    Builder for Confluence storage format HTML

    Provides fluent API for creating valid Confluence pages with:
    - Info panels
    - Colored panels
    - Headings
    - Lists (ordered/unordered)
    - Tables
    - Expand/collapse sections
    - Code blocks

    Example:
        builder = ConfluencePageBuilder()
        html = (builder
            .add_info_panel({"Name": "John", "Role": "Engineer"})
            .add_heading("Overview")
            .add_list(["Item 1", "Item 2"])
            .build())
    """

    def __init__(self):
        self.sections: List[str] = []
        self._validation_enabled = True

    def add_info_panel(self, content: Dict[str, str], title: Optional[str] = None) -> 'ConfluencePageBuilder':
        """
        Add info panel macro (blue background)

        Args:
            content: Dict of key-value pairs to display
            title: Optional panel title

        Returns:
            Self for chaining
        """
        items = "".join(
            f"<p><strong>{escape_html(k)}:</strong> {escape_html(v)}</p>"
            for k, v in content.items()
        )

        title_param = f'<ac:parameter ac:name="title">{escape_html(title)}</ac:parameter>' if title else ''

        self.sections.append(f"""
<ac:structured-macro ac:name="info">
{title_param}
<ac:rich-text-body>
{items}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_warning_panel(self, content: str, title: Optional[str] = None) -> 'ConfluencePageBuilder':
        """
        Add warning panel macro (yellow background)

        Args:
            content: HTML content for panel
            title: Optional panel title

        Returns:
            Self for chaining
        """
        title_param = f'<ac:parameter ac:name="title">{escape_html(title)}</ac:parameter>' if title else ''

        self.sections.append(f"""
<ac:structured-macro ac:name="warning">
{title_param}
<ac:rich-text-body>
{content}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_panel(
        self,
        content: str,
        bg_color: str = PanelColor.BLUE.value,
        border_color: Optional[str] = None,
        title: Optional[str] = None
    ) -> 'ConfluencePageBuilder':
        """
        Add colored panel

        Args:
            content: HTML content for panel
            bg_color: Background color (hex or PanelColor enum)
            border_color: Optional border color (hex)
            title: Optional panel title

        Returns:
            Self for chaining
        """
        title_param = f'<ac:parameter ac:name="title">{escape_html(title)}</ac:parameter>' if title else ''
        border_param = f'<ac:parameter ac:name="borderColor">{border_color}</ac:parameter>' if border_color else ''

        self.sections.append(f"""
<ac:structured-macro ac:name="panel" ac:schema-version="1">
<ac:parameter ac:name="bgColor">{bg_color}</ac:parameter>
{border_param}
{title_param}
<ac:rich-text-body>
{content}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_heading(self, text: str, level: int = 2) -> 'ConfluencePageBuilder':
        """
        Add heading

        Args:
            text: Heading text
            level: Heading level (1-6)

        Returns:
            Self for chaining
        """
        if level < 1 or level > 6:
            raise ValueError(f"Heading level must be 1-6, got {level}")

        self.sections.append(f"<h{level}>{escape_html(text)}</h{level}>")
        return self

    def add_paragraph(self, text: str) -> 'ConfluencePageBuilder':
        """
        Add paragraph

        Args:
            text: Paragraph text

        Returns:
            Self for chaining
        """
        self.sections.append(f"<p>{escape_html(text)}</p>")
        return self

    def add_list(self, items: List[str], ordered: bool = False) -> 'ConfluencePageBuilder':
        """
        Add list (ordered or unordered)

        Args:
            items: List items
            ordered: True for <ol>, False for <ul>

        Returns:
            Self for chaining
        """
        tag = "ol" if ordered else "ul"
        list_items = "".join(f"<li>{escape_html(item)}</li>" for item in items)
        self.sections.append(f"<{tag}>{list_items}</{tag}>")
        return self

    def add_expand_section(self, title: str, content: str) -> 'ConfluencePageBuilder':
        """
        Add collapsible expand/collapse section

        Args:
            title: Section title (visible when collapsed)
            content: HTML content (visible when expanded)

        Returns:
            Self for chaining
        """
        self.sections.append(f"""
<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">{escape_html(title)}</ac:parameter>
<ac:rich-text-body>
{content}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        header_row: bool = True
    ) -> 'ConfluencePageBuilder':
        """
        Add table

        Args:
            headers: Column headers
            rows: Table rows (list of lists)
            header_row: True to use <th> for headers, False for <td>

        Returns:
            Self for chaining
        """
        header_tag = "th" if header_row else "td"
        header_html = "<tr>" + "".join(f"<{header_tag}>{escape_html(h)}</{header_tag}>" for h in headers) + "</tr>"

        body_rows = "".join(
            "<tr>" + "".join(f"<td>{escape_html(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )

        self.sections.append(f"""
<table>
<tbody>
{header_html}
{body_rows}
</tbody>
</table>
""")
        return self

    def add_code_block(
        self,
        code: str,
        language: str = "python",
        line_numbers: bool = True
    ) -> 'ConfluencePageBuilder':
        """
        Add code block with syntax highlighting

        Args:
            code: Code content
            language: Programming language for syntax highlighting
            line_numbers: Show line numbers

        Returns:
            Self for chaining
        """
        line_num_param = f'<ac:parameter ac:name="linenumbers">{str(line_numbers).lower()}</ac:parameter>' if line_numbers else ''

        self.sections.append(f"""
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">{escape_html(language)}</ac:parameter>
{line_num_param}
<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>
</ac:structured-macro>
""")
        return self

    def add_horizontal_rule(self) -> 'ConfluencePageBuilder':
        """Add horizontal rule (<hr />)"""
        self.sections.append("<hr />")
        return self

    def add_raw_html(self, html_content: str) -> 'ConfluencePageBuilder':
        """
        Add raw HTML content (use with caution)

        Note: Content is NOT escaped - ensure it's safe before adding

        Args:
            html_content: Raw HTML string

        Returns:
            Self for chaining
        """
        self.sections.append(html_content)
        return self

    def enable_validation(self, enabled: bool = True) -> 'ConfluencePageBuilder':
        """Enable or disable HTML validation on build()"""
        self._validation_enabled = enabled
        return self

    def build(self, validate: bool = True) -> str:
        """
        Generate final Confluence storage format HTML

        Args:
            validate: Run validation before returning (default: True)

        Returns:
            Confluence storage format HTML string

        Raises:
            ValueError: If validation fails and validation is enabled
        """
        html_content = "\n".join(self.sections)

        if validate and self._validation_enabled:
            result = validate_confluence_html(html_content)

            # Log warnings
            for warning in result.warnings:
                logger.warning(f"HTML validation warning: {warning}")

            # Raise errors
            if not result.is_valid:
                error_msg = f"HTML validation failed:\n" + "\n".join(f"  - {e}" for e in result.errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

        return html_content


# Helper function for common use case: Interview prep pages
def create_interview_prep_html(
    candidate_name: str,
    role: str,
    score: int,
    assessment_summary: str,
    strengths: List[str],
    concerns: List[str],
    question_sections: Dict[str, List[Dict[str, str]]],
    scoring_criteria: List[Dict[str, Any]],
    recommendation: str
) -> str:
    """
    Generate interview prep page HTML using standard template

    Args:
        candidate_name: Candidate's full name
        role: Job role/title
        score: Expected score (0-100)
        assessment_summary: Brief assessment text
        strengths: List of key strengths
        concerns: List of critical concerns
        question_sections: Dict of {section_name: [questions]} where each question has:
            - 'question': str
            - 'looking_for': str
            - 'red_flag': str
        scoring_criteria: List of dicts with:
            - 'criteria': str
            - 'weight': str (e.g., "15%")
            - 'notes': str
        recommendation: Final recommendation text

    Returns:
        Confluence storage format HTML
    """
    builder = ConfluencePageBuilder()

    # Header panel
    builder.add_info_panel({
        "Candidate": candidate_name,
        "Role": role,
        "Date Prepared": "2025-10-16",
        "Prepared For": "Interview Team"
    })

    # Assessment panel
    builder.add_panel(
        f"""
<p><strong>Overall Assessment:</strong> {escape_html(assessment_summary)}</p>
<p><strong>Expected Score:</strong> {score}/100</p>
""",
        bg_color=PanelColor.BLUE.value
    )

    # Strengths
    builder.add_heading("Key Strengths")
    builder.add_list(strengths)

    # Concerns
    builder.add_heading("Critical Concerns")
    builder.add_list(concerns)

    builder.add_horizontal_rule()

    # Question sections (collapsible)
    for section_name, questions in question_sections.items():
        question_html = ""
        for i, q in enumerate(questions, 1):
            question_html += f"""
<p><strong>Q{i}:</strong> {escape_html(q['question'])}</p>
<ul>
<li><strong>Looking for:</strong> {escape_html(q['looking_for'])}</li>
<li><strong>Red flag:</strong> {escape_html(q['red_flag'])}</li>
</ul>
"""
        builder.add_expand_section(section_name, question_html)

    builder.add_horizontal_rule()

    # Scoring rubric table
    builder.add_heading("Scoring Rubric")
    headers = ["Criteria", "Weight", "Score /10", "Notes"]
    rows = [
        [c['criteria'], c['weight'], "___/10", c['notes']]
        for c in scoring_criteria
    ]
    builder.add_table(headers, rows)

    # Final recommendation panel
    builder.add_panel(
        f"<p><strong>Recommendation:</strong> {escape_html(recommendation)}</p>",
        bg_color=PanelColor.GRAY.value
    )

    return builder.build()


if __name__ == "__main__":
    # Test the builder
    builder = ConfluencePageBuilder()
    html = (builder
        .add_info_panel({"Test": "Value", "Status": "Active"})
        .add_heading("Test Section")
        .add_list(["Item 1", "Item 2", "Item 3"])
        .add_expand_section("Details", "<p>Hidden content</p>")
        .add_table(
            headers=["Column 1", "Column 2"],
            rows=[["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]]
        )
        .build())

    print("Generated HTML:")
    print(html)
    print("\nValidation passed! ✅")
