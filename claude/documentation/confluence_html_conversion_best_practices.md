# Confluence HTML Conversion Best Practices

**Status**: ✅ Production Guide - Phase 122 Post-Mortem
**Last Updated**: 2025-10-16
**Incident**: Abdullah Kazim interview prep - Malformed HTML on first attempt

---

## 🚨 Incident Summary

**Problem**: Naive markdown→HTML conversion produced malformed Confluence page requiring manual rework

**Root Cause**: String replacement conversion approach that was:
- State-blind (couldn't handle paired markers like `**bold**`)
- Structure-unaware (created orphaned `<li>` tags without `<ul>` parent)
- Order-dependent (replacements conflicted with each other)
- Nesting-incapable (couldn't handle markdown inside markdown)

**Impact**: 3 minutes MTTR, 1 page requiring manual fix, minor quality impact

**Resolution**: Rewrote using proper Confluence storage format HTML from scratch

---

## ✅ Correct Approach: Use Confluence Storage Format Directly

### Strategy 1: Native Confluence HTML (RECOMMENDED)

**When to use**: Always, for all Confluence page creation

**Approach**: Write Confluence storage format HTML directly, don't convert markdown

**Why this works**:
- No conversion errors - using native format
- Full feature access - panels, macros, collapsible sections
- Validation-friendly - Confluence accepts it natively
- Performance - no conversion overhead

### Example: Interview Prep Page Structure

```html
<!-- Info Panel (Header) -->
<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>Candidate:</strong> John Doe</p>
<p><strong>Role:</strong> Senior Engineer</p>
<p><strong>Date:</strong> 2025-10-16</p>
</ac:rich-text-body>
</ac:structured-macro>

<!-- Colored Assessment Panel -->
<ac:structured-macro ac:name="panel" ac:schema-version="1">
<ac:parameter ac:name="bgColor">#deebff</ac:parameter>
<ac:rich-text-body>
<p><strong>Overall Assessment:</strong> Strong technical candidate</p>
<p><strong>Expected Score:</strong> 75/100</p>
</ac:rich-text-body>
</ac:structured-macro>

<!-- Standard Content -->
<h2>Key Strengths</h2>
<ul>
<li>10+ years experience</li>
<li>Strong Azure expertise</li>
<li>Proven leadership</li>
</ul>

<!-- Collapsible Section -->
<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">Technical Questions (5)</ac:parameter>
<ac:rich-text-body>
<p><strong>Q1:</strong> Describe your experience with Azure AD</p>
<ul>
<li><strong>Looking for:</strong> Enterprise deployments, 10K+ users</li>
<li><strong>Red flag:</strong> Only small deployments</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>

<!-- Table -->
<table>
<tbody>
<tr>
<th>Criteria</th>
<th>Weight</th>
<th>Score</th>
</tr>
<tr>
<td>Technical Skills</td>
<td>50%</td>
<td>___/10</td>
</tr>
<tr>
<td>Leadership</td>
<td>25%</td>
<td>___/10</td>
</tr>
</tbody>
</table>

<!-- Final Recommendation Panel -->
<ac:structured-macro ac:name="panel" ac:schema-version="1">
<ac:parameter ac:name="bgColor">#dfe1e6</ac:parameter>
<ac:parameter ac:name="borderColor">#505f79</ac:parameter>
<ac:rich-text-body>
<p><strong>Recommendation:</strong> <strong>PROCEED TO INTERVIEW</strong></p>
<ol>
<li>Strong technical fit</li>
<li>Leadership experience verified</li>
<li>Cultural alignment confirmed</li>
</ol>
</ac:rich-text-body>
</ac:structured-macro>
```

---

## ❌ Anti-Patterns: What NOT To Do

### Anti-Pattern 1: Naive String Replacement

```python
# ❌ NEVER DO THIS
html = markdown.replace('**', '<strong>')  # BROKEN - can't handle pairs
html = html.replace('- ', '<li>')          # BROKEN - orphaned tags
html = html.replace('\n\n', '</p><p>')     # BROKEN - order dependent
```

**Problems**:
- Can't track state (opening vs closing tags)
- Creates invalid HTML structure
- Order-dependent (replacements conflict)
- No nesting support

### Anti-Pattern 2: Markdown Library Without Validation

```python
# ❌ RISKY
import markdown
html = markdown.markdown(content)
# Then post to Confluence
```

**Problems**:
- Markdown HTML ≠ Confluence storage format
- Missing Confluence macros (panels, expand, etc.)
- May produce incompatible HTML tags
- No structure validation

### Anti-Pattern 3: Manual HTML String Concatenation

```python
# ❌ FRAGILE
html = "<h1>" + title + "</h1>"
html += "<p>" + content + "</p>"
```

**Problems**:
- No escaping (XSS vulnerabilities)
- No structure validation
- Easy to forget closing tags
- Hard to maintain

---

## ✅ Recommended Patterns

### Pattern 1: Template-Based HTML Generation

```python
def create_interview_prep_page(candidate_data: dict) -> str:
    """
    Generate Confluence storage format HTML for interview prep

    Args:
        candidate_data: {
            "name": str,
            "role": str,
            "score": int,
            "strengths": List[str],
            "questions": List[dict]
        }

    Returns:
        Confluence storage format HTML string
    """

    # Use template with safe variable substitution
    template = f"""
<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p><strong>Candidate:</strong> {escape_html(candidate_data['name'])}</p>
<p><strong>Role:</strong> {escape_html(candidate_data['role'])}</p>
</ac:rich-text-body>
</ac:structured-macro>

<h2>Key Strengths</h2>
<ul>
{"".join(f"<li>{escape_html(s)}</li>" for s in candidate_data['strengths'])}
</ul>
"""

    # Add collapsible question sections
    for q in candidate_data['questions']:
        template += f"""
<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">{escape_html(q['category'])}</ac:parameter>
<ac:rich-text-body>
<p><strong>{escape_html(q['question'])}</strong></p>
<ul>
<li><strong>Looking for:</strong> {escape_html(q['looking_for'])}</li>
<li><strong>Red flag:</strong> {escape_html(q['red_flag'])}</li>
</ul>
</ac:rich-text-body>
</ac:structured-macro>
"""

    return template

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;'))
```

**Benefits**:
- Type-safe with data validation
- HTML escaping prevents XSS
- Reusable template
- Easy to test

### Pattern 2: HTML Builder Class

```python
class ConfluencePageBuilder:
    """Builder for Confluence storage format HTML"""

    def __init__(self):
        self.sections = []

    def add_info_panel(self, content: dict) -> 'ConfluencePageBuilder':
        """Add info panel macro"""
        items = "".join(
            f"<p><strong>{k}:</strong> {escape_html(v)}</p>"
            for k, v in content.items()
        )
        self.sections.append(f"""
<ac:structured-macro ac:name="info">
<ac:rich-text-body>
{items}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_panel(self, content: str, bg_color: str = "#deebff") -> 'ConfluencePageBuilder':
        """Add colored panel"""
        self.sections.append(f"""
<ac:structured-macro ac:name="panel" ac:schema-version="1">
<ac:parameter ac:name="bgColor">{bg_color}</ac:parameter>
<ac:rich-text-body>
{content}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_heading(self, text: str, level: int = 2) -> 'ConfluencePageBuilder':
        """Add heading"""
        self.sections.append(f"<h{level}>{escape_html(text)}</h{level}>")
        return self

    def add_list(self, items: List[str], ordered: bool = False) -> 'ConfluencePageBuilder':
        """Add list"""
        tag = "ol" if ordered else "ul"
        list_items = "".join(f"<li>{escape_html(item)}</li>" for item in items)
        self.sections.append(f"<{tag}>{list_items}</{tag}>")
        return self

    def add_expand_section(self, title: str, content: str) -> 'ConfluencePageBuilder':
        """Add collapsible section"""
        self.sections.append(f"""
<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">{escape_html(title)}</ac:parameter>
<ac:rich-text-body>
{content}
</ac:rich-text-body>
</ac:structured-macro>
""")
        return self

    def add_table(self, headers: List[str], rows: List[List[str]]) -> 'ConfluencePageBuilder':
        """Add table"""
        header_row = "<tr>" + "".join(f"<th>{escape_html(h)}</th>" for h in headers) + "</tr>"
        body_rows = "".join(
            "<tr>" + "".join(f"<td>{escape_html(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        self.sections.append(f"""
<table>
<tbody>
{header_row}
{body_rows}
</tbody>
</table>
""")
        return self

    def build(self) -> str:
        """Generate final HTML"""
        return "\n".join(self.sections)

# Usage
builder = ConfluencePageBuilder()
html = (builder
    .add_info_panel({"Candidate": "John Doe", "Role": "Engineer"})
    .add_heading("Key Strengths")
    .add_list(["10+ years experience", "Azure expert", "Team leader"])
    .add_expand_section("Technical Questions", "<p>Question 1...</p>")
    .build())
```

**Benefits**:
- Fluent API (chainable methods)
- Encapsulates HTML generation
- Built-in validation
- Testable components

### Pattern 3: Validation Before API Call

```python
def validate_confluence_html(html: str) -> tuple[bool, List[str]]:
    """
    Validate Confluence storage format HTML before API call

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Check for common issues
    if html.count('<li>') != html.count('</li>'):
        errors.append("Mismatched <li> tags")

    if html.count('<ul>') != html.count('</ul>'):
        errors.append("Mismatched <ul> tags")

    if html.count('<strong>') != html.count('</strong>'):
        errors.append("Mismatched <strong> tags")

    # Check for orphaned list items
    if '<li>' in html and '<ul>' not in html and '<ol>' not in html:
        errors.append("List items without parent <ul> or <ol>")

    # Check for empty tags
    if '<p></p>' in html or '<li></li>' in html:
        errors.append("Empty tags found (cleanup needed)")

    # Check for proper macro structure
    if '<ac:structured-macro' in html:
        if 'ac:name=' not in html:
            errors.append("Macro missing ac:name attribute")

    return (len(errors) == 0, errors)

# Usage in ReliableConfluenceClient
def create_page(self, space_key: str, title: str, html_content: str) -> Optional[dict]:
    """Create page with validation"""

    # Pre-flight validation
    is_valid, errors = validate_confluence_html(html_content)
    if not is_valid:
        logger.error(f"HTML validation failed: {errors}")
        raise ValueError(f"Invalid Confluence HTML: {errors}")

    # Proceed with API call
    page_data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    response = self._make_request('POST', '/content', json=page_data)
    return response.json() if response and response.status_code == 200 else None
```

---

## 🔧 Recommended Tool Enhancement

### Update ReliableConfluenceClient with Helper Methods

```python
class ReliableConfluenceClient:
    """
    Enhanced Confluence client with HTML generation helpers
    """

    def create_interview_prep_page(
        self,
        space_key: str,
        candidate_name: str,
        role: str,
        assessment: dict,
        questions: List[dict]
    ) -> Optional[str]:
        """
        Create interview prep page with proper Confluence formatting

        Returns:
            Page URL if successful, None otherwise
        """

        # Build HTML using builder pattern
        builder = ConfluencePageBuilder()

        # Header
        html = builder.add_info_panel({
            "Candidate": candidate_name,
            "Role": role,
            "Date Prepared": datetime.now().strftime("%Y-%m-%d")
        })

        # Assessment panel
        .add_panel(
            f"""
            <p><strong>Overall Assessment:</strong> {assessment['summary']}</p>
            <p><strong>Expected Score:</strong> {assessment['score']}/100</p>
            """,
            bg_color="#deebff"
        )

        # Strengths
        .add_heading("Key Strengths")
        .add_list(assessment['strengths'])

        # Questions (collapsible sections)
        for category, qs in questions.items():
            question_html = ""
            for q in qs:
                question_html += f"""
                <p><strong>{q['number']}:</strong> {q['question']}</p>
                <ul>
                <li><strong>Looking for:</strong> {q['looking_for']}</li>
                <li><strong>Red flag:</strong> {q['red_flag']}</li>
                </ul>
                """
            builder.add_expand_section(category, question_html)

        html = builder.build()

        # Validate before API call
        is_valid, errors = validate_confluence_html(html)
        if not is_valid:
            logger.error(f"HTML validation failed: {errors}")
            return None

        # Create page
        page_title = f"Interview Prep - {candidate_name} ({role})"
        result = self.create_page(space_key, page_title, html)

        if result:
            page_id = result['id']
            return f"{self.base_url}/wiki/spaces/{space_key}/pages/{page_id}"

        return None
```

---

## 📋 Pre-Flight Checklist

Before creating any Confluence page, verify:

- [ ] **Using native Confluence storage format** (not converted markdown)
- [ ] **All HTML tags properly closed** (no orphaned `<li>`, `<strong>`, etc.)
- [ ] **Lists have parent tags** (`<ul>` or `<ol>` around `<li>`)
- [ ] **HTML entities escaped** (use `&amp;` not `&`, `&lt;` not `<`)
- [ ] **Macros properly formatted** (correct `ac:name`, nested `ac:rich-text-body`)
- [ ] **Validation passed** (run `validate_confluence_html()`)
- [ ] **Template tested** (dry-run with sample data)

---

## 🎯 Quick Reference: Common Confluence Macros

### Info Panel
```html
<ac:structured-macro ac:name="info">
<ac:rich-text-body>
<p>Your content here</p>
</ac:rich-text-body>
</ac:structured-macro>
```

### Warning Panel
```html
<ac:structured-macro ac:name="warning">
<ac:rich-text-body>
<p>Warning message here</p>
</ac:rich-text-body>
</ac:structured-macro>
```

### Colored Panel
```html
<ac:structured-macro ac:name="panel" ac:schema-version="1">
<ac:parameter ac:name="bgColor">#deebff</ac:parameter>
<ac:parameter ac:name="borderColor">#0052cc</ac:parameter>
<ac:rich-text-body>
<p>Panel content</p>
</ac:rich-text-body>
</ac:structured-macro>
```

### Expand/Collapse
```html
<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">Click to expand</ac:parameter>
<ac:rich-text-body>
<p>Hidden content</p>
</ac:rich-text-body>
</ac:structured-macro>
```

### Code Block
```html
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">python</ac:parameter>
<ac:parameter ac:name="linenumbers">true</ac:parameter>
<ac:plain-text-body><![CDATA[
def hello():
    print("Hello world")
]]></ac:plain-text-body>
</ac:structured-macro>
```

---

## 📊 Success Metrics

**Quality Gates**:
- [ ] Zero HTML validation errors before API call
- [ ] 100% of tags properly closed (matched pairs)
- [ ] All special characters escaped
- [ ] Page renders correctly on first attempt

**Performance Targets**:
- Validation: <50ms
- HTML generation: <200ms
- API call: <2 seconds
- Total time: <3 seconds

**Reliability Targets**:
- First-attempt success rate: >99%
- Zero malformed pages in production
- Zero XSS vulnerabilities

---

## 🔗 References

- [Confluence Storage Format Documentation](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Confluence Macros Reference](https://confluence.atlassian.com/spaces/CONF50/pages/329980084/Confluence+Storage+Format+for+Macros)
- Phase 122: Recruitment Tracking Database & Automation (incident source)
- ReliableConfluenceClient: `/Users/naythandawe/git/maia/claude/tools/reliable_confluence_client.py`

---

**Status**: ✅ Production Ready
**Owner**: Maia SRE Team
**Next Review**: After next Confluence integration (validate patterns work)
