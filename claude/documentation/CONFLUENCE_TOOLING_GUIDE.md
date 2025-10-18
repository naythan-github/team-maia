# Confluence Tooling Guide - Quick Reference

**Status**: ✅ PRODUCTION GUIDE
**Last Updated**: 2025-10-18
**Phase**: 129 - Confluence Tooling Consolidation

---

## 🎯 TL;DR - Use These Tools

**Page Creation/Updates**: `reliable_confluence_client.py` ⭐
**HTML Generation**: `confluence_html_builder.py` ⭐

**DO NOT USE**: `confluence_formatter.py`, `confluence_formatter_v2.py` (deprecated - cause malformed HTML)

---

## ✅ Production Tools

### 1. ReliableConfluenceClient - Page Operations ⭐ PRIMARY

**Purpose**: Create, update, retrieve Confluence pages with SRE-grade reliability

**Location**: `claude/tools/reliable_confluence_client.py`

**Import**:
```python
from claude.tools.reliable_confluence_client import ReliableConfluenceClient
```

#### Create Simple Page

```python
client = ReliableConfluenceClient()

# Generate HTML using builder (see below)
html_content = "<p>Your content here</p>"

result = client.create_page(
    space_key="Orro",           # Confluence space
    title="My Page Title",       # Page title
    content=html_content,        # Confluence storage format HTML
    parent_id=None,              # Optional: parent page ID
    validate_html=True           # Recommended: pre-flight validation
)

if result:
    print(f"✅ Page created: {result['url']}")
    print(f"   Page ID: {result['id']}")
    print(f"   Version: {result['version']}")
else:
    print("❌ Page creation failed")
```

#### Create Interview Prep Page (Pre-Built Template)

```python
client = ReliableConfluenceClient()

url = client.create_interview_prep_page(
    space_key="Orro",
    candidate_name="John Doe",
    role="Senior IDAM Engineer",
    assessment_data={
        "score": 75,
        "summary": "Strong technical candidate with Azure expertise",
        "strengths": [
            "10+ years identity management experience",
            "Azure AD/Entra ID expert",
            "Strong communication skills"
        ],
        "concerns": [
            "Limited PAM experience",
            "No leadership experience",
            "Tenure concerns (frequent job changes)"
        ],
        "question_sections": {
            "Technical Deep-Dive (10 questions)": [
                {
                    "question": "Describe your experience with Azure AD Conditional Access",
                    "looking_for": "Enterprise deployments, 5000+ users, complex policies",
                    "red_flag": "Only basic configurations, limited scope"
                }
                # ... more questions
            ],
            "Leadership & Cultural Fit (5 questions)": [
                # ... questions
            ]
        },
        "scoring_criteria": [
            {"criteria": "Technical Skills (Azure/Entra ID)", "weight": "50%", "notes": "Must be 8+/10"},
            {"criteria": "Leadership Potential", "weight": "25%", "notes": "Looking for 6+/10"},
            {"criteria": "Cultural Fit", "weight": "25%", "notes": "Must demonstrate collaboration"}
        ],
        "recommendation": "YES WITH RESERVATIONS - Strong technical skills, concerns about leadership readiness"
    }
)

print(f"✅ Interview prep created: {url}")
```

#### Update Existing Page

```python
client = ReliableConfluenceClient()

# First, get current page to retrieve version number
page = client.get_page(page_id="123456")

if page:
    result = client.update_page(
        page_id="123456",
        title="Updated Title",
        content="<p>Updated content</p>",
        version_number=page['version']['number'] + 1  # Increment version
    )
```

#### Other Operations

```python
# Get page by ID
page = client.get_page(page_id="123456")

# Search content
results = client.search_content(
    space_key="Orro",
    query="Azure AD"
)

# List spaces
spaces = client.list_spaces()

# Move page to new parent
client.move_page_to_parent(
    page_id="123456",
    new_parent_id="789012"
)

# Health check
health = client.health_check()
print(f"Service health: {health['status']}")

# Get metrics
metrics = client.get_metrics_summary()
print(f"Success rate: {metrics['success_rate']:.1f}%")
```

#### Reliability Features

**Built-In SRE Patterns**:
- ✅ **Circuit Breaker**: Stops requests if service degraded
- ✅ **Exponential Backoff**: Retries with 1s → 2s → 4s delays
- ✅ **Rate Limit Handling**: Respects 429 responses automatically
- ✅ **Request Timeout**: 30s timeout prevents hanging
- ✅ **Connection Pooling**: Reuses connections for performance
- ✅ **Metrics Tracking**: Success rate, latency, failure count
- ✅ **HTML Validation**: Pre-flight checks prevent malformed content

**Result**: 99%+ success rate on page creation

---

### 2. ConfluencePageBuilder - HTML Generation ⭐ PRIMARY

**Purpose**: Generate validated Confluence storage format HTML (prevents malformed pages)

**Location**: `claude/tools/confluence_html_builder.py`

**Import**:
```python
from claude.tools.confluence_html_builder import (
    ConfluencePageBuilder,
    validate_confluence_html,
    create_interview_prep_html,
    PanelColor
)
```

#### Basic Usage - Fluent API

```python
builder = ConfluencePageBuilder()

html = (builder
    .add_heading("Project Overview", level=1)
    .add_paragraph("This project aims to improve system reliability.")
    .add_heading("Key Features", level=2)
    .add_list([
        "Circuit breaker pattern",
        "Exponential backoff",
        "Comprehensive monitoring"
    ])
    .add_heading("Technical Details", level=2)
    .add_paragraph("Implementation uses Python with requests library.")
    .build()
)

# Use html with ReliableConfluenceClient
client = ReliableConfluenceClient()
client.create_page(space_key="Orro", title="Project Overview", content=html)
```

#### Advanced Features

```python
builder = ConfluencePageBuilder()

html = (builder
    # Info panel (header box)
    .add_info_panel({
        "Candidate": "John Doe",
        "Role": "Senior Engineer",
        "Date": "2025-10-18",
        "Expected Score": "75/100"
    })

    # Colored assessment panel
    .add_colored_panel(
        content="<p><strong>Overall Assessment:</strong> Strong technical candidate</p>",
        color=PanelColor.BLUE  # or "#deebff"
    )

    # Collapsible section
    .add_expand_section(
        title="Technical Questions (10)",
        content="""
            <p><strong>Q1:</strong> Describe your Azure AD experience</p>
            <ul>
                <li><strong>Looking for:</strong> Enterprise scale (5000+ users)</li>
                <li><strong>Red flag:</strong> Only basic configurations</li>
            </ul>
        """
    )

    # Table
    .add_table(
        headers=["Criteria", "Weight", "Score"],
        rows=[
            ["Technical Skills", "50%", "___/10"],
            ["Leadership", "25%", "___/10"],
            ["Cultural Fit", "25%", "___/10"]
        ]
    )

    .build()
)
```

#### Panel Colors

```python
from claude.tools.confluence_html_builder import PanelColor

# Available colors:
PanelColor.BLUE    # Info/neutral - #deebff
PanelColor.GREEN   # Success - #e3fcef
PanelColor.YELLOW  # Warning - #fffae6
PanelColor.RED     # Error/critical - #ffebe6
PanelColor.GRAY    # Neutral/secondary - #dfe1e6
```

#### HTML Validation

```python
from claude.tools.confluence_html_builder import validate_confluence_html

# Validate before sending to Confluence
html_content = "<ul><li>Item 1</li><li>Item 2</li></ul>"
result = validate_confluence_html(html_content)

if result.is_valid:
    print("✅ HTML is valid")
else:
    print("❌ HTML validation failed:")
    for error in result.errors:
        print(f"  - {error}")
    for warning in result.warnings:
        print(f"  ⚠️  {warning}")
```

**Validation Checks**:
- Tag matching (ul/ol/li, strong, em, p, h1-h6, table, tr, td, th)
- Orphaned elements (li without ul/ol)
- Empty tags (cleanup indicators)
- Macro structure validation

---

## ❌ Deprecated Tools - Do Not Use

### 1. confluence_formatter.py 🗑️ DEPRECATED

**Status**: DEPRECATED - Moved to `claude/tools/deprecated/`

**Issue**: Naive markdown→HTML string replacement causes malformed HTML

**Replacement**: Use `ConfluencePageBuilder` instead

**Phase 122 Incident**: Abdullah Kazim interview prep had malformed HTML requiring manual fix
- **Root Cause**: String replacement was state-blind, created orphaned `<li>` tags
- **Resolution**: Created `confluence_html_builder.py` with template-based generation

**DO NOT USE THIS TOOL**

---

### 2. confluence_formatter_v2.py 🗑️ DEPRECATED

**Status**: DEPRECATED - Moved to `claude/tools/deprecated/`

**Issue**: Same problems as v1, failed improvement attempt

**Replacement**: Use `ConfluencePageBuilder` instead

**DO NOT USE THIS TOOL**

---

### 3. create_azure_lighthouse_confluence_pages.py 🗑️ ARCHIVED

**Status**: ARCHIVED - Moved to `claude/extensions/experimental/archive/confluence_migrations/`

**Issue**: One-time migration script, no longer needed

**Purpose**: Migrated Azure Lighthouse documentation (completed)

**DO NOT USE THIS TOOL**

---

## 📚 Full Example - End-to-End Workflow

```python
#!/usr/bin/env python3
"""
Complete Confluence page creation workflow
Demonstrates best practices with production tools
"""

from claude.tools.reliable_confluence_client import ReliableConfluenceClient
from claude.tools.confluence_html_builder import (
    ConfluencePageBuilder,
    validate_confluence_html,
    PanelColor
)

# Step 1: Build HTML content using builder
builder = ConfluencePageBuilder()

html = (builder
    .add_heading("System Reliability Report", level=1)

    .add_info_panel({
        "Date": "2025-10-18",
        "Status": "Production Ready",
        "Success Rate": "99.2%"
    })

    .add_heading("Key Metrics", level=2)
    .add_colored_panel(
        content="""
            <p><strong>Availability:</strong> 99.9%</p>
            <p><strong>P95 Latency:</strong> 120ms</p>
            <p><strong>Error Rate:</strong> 0.1%</p>
        """,
        color=PanelColor.GREEN
    )

    .add_heading("Recent Improvements", level=2)
    .add_list([
        "Implemented circuit breaker pattern",
        "Added exponential backoff retries",
        "Enhanced monitoring and alerting"
    ])

    .add_heading("Detailed Metrics", level=2)
    .add_expand_section(
        title="View Full Metrics Table",
        content="""
            <table>
                <tbody>
                    <tr><th>Metric</th><th>Value</th><th>Target</th></tr>
                    <tr><td>Availability</td><td>99.9%</td><td>99.9%</td></tr>
                    <tr><td>P95 Latency</td><td>120ms</td><td>300ms</td></tr>
                    <tr><td>Error Rate</td><td>0.1%</td><td>0.5%</td></tr>
                </tbody>
            </table>
        """
    )

    .build()
)

# Step 2: Validate HTML before sending
validation = validate_confluence_html(html)

if not validation.is_valid:
    print("❌ HTML validation failed:")
    for error in validation.errors:
        print(f"  - {error}")
    exit(1)

print("✅ HTML validation passed")

# Step 3: Create page with ReliableConfluenceClient
client = ReliableConfluenceClient()

result = client.create_page(
    space_key="Orro",
    title="System Reliability Report - 2025-10-18",
    content=html,
    validate_html=True  # Extra validation layer
)

if result:
    print(f"✅ Page created successfully!")
    print(f"   URL: {result['url']}")
    print(f"   Page ID: {result['id']}")
    print(f"   Version: {result['version']}")
else:
    print("❌ Page creation failed")

    # Check metrics for debugging
    metrics = client.get_metrics_summary()
    print(f"\nClient Metrics:")
    print(f"  Success Rate: {metrics['success_rate']:.1f}%")
    print(f"  Circuit Breaker: {metrics.get('circuit_breaker_state', 'unknown')}")
```

---

## 🔧 Troubleshooting

### Page Creation Fails

**Check 1: HTML Validation**
```python
from claude.tools.confluence_html_builder import validate_confluence_html

result = validate_confluence_html(your_html)
if not result.is_valid:
    print("Errors:", result.errors)
```

**Check 2: Service Health**
```python
client = ReliableConfluenceClient()
health = client.health_check()
print(f"Status: {health['status']}")
```

**Check 3: Metrics**
```python
metrics = client.get_metrics_summary()
print(f"Success rate: {metrics['success_rate']:.1f}%")
print(f"Circuit breaker: {metrics.get('circuit_breaker_state')}")
```

### Common Issues

**Issue**: "Mismatched tags" validation error
**Solution**: Use `ConfluencePageBuilder` instead of manual HTML - it ensures proper nesting

**Issue**: Page created but looks wrong in Confluence
**Solution**: You're using markdown or wrong HTML format - use Confluence storage format via `ConfluencePageBuilder`

**Issue**: "Circuit breaker is OPEN" error
**Solution**: Service is degraded, wait 60 seconds for circuit to reset to half-open

---

## 📊 Production Reliability

### Current Metrics (Post-Phase 122)

- **Success Rate**: 99%+ (first attempt)
- **Average Latency**: 1-2 seconds
- **Retry Rate**: <5%
- **Circuit Breaker Opens**: 0 (never)
- **Malformed HTML Incidents**: 0 (since Phase 122)

### SLA Targets

- **Availability**: 99.9%
- **P95 Latency**: <3 seconds
- **Error Rate**: <1%
- **Malformed HTML**: 0%

---

## 🎯 Best Practices

### ✅ DO

1. **Always use `ConfluencePageBuilder`** for HTML generation
2. **Validate HTML** before creating pages (`validate_confluence_html()`)
3. **Use `ReliableConfluenceClient`** for all Confluence API operations
4. **Check return values** - handle None gracefully
5. **Use pre-built templates** when available (e.g., `create_interview_prep_page()`)

### ❌ DON'T

1. **Don't write HTML manually** - use builder to prevent malformed content
2. **Don't use deprecated formatters** - they cause reliability issues
3. **Don't skip validation** - it catches errors before API calls
4. **Don't ignore retry logic** - let the client handle transient failures
5. **Don't create duplicate tools** - check this guide first

---

## 📚 Related Documentation

- **Audit Report**: `claude/documentation/CONFLUENCE_TOOLING_AUDIT_REPORT.md`
- **Best Practices**: `claude/documentation/confluence_html_conversion_best_practices.md`
- **Project Plan**: `claude/data/CONFLUENCE_TOOLING_CONSOLIDATION_PROJECT.md`
- **Phase 122 Incident**: `SYSTEM_STATE.md` - Search "Phase 122"

---

## 🔗 Quick Links

**Production Tools**:
- [reliable_confluence_client.py](../tools/reliable_confluence_client.py:1)
- [confluence_html_builder.py](../tools/confluence_html_builder.py:1)

**Deprecated Tools** (do not use):
- [confluence_formatter.py](../tools/deprecated/confluence_formatter.py:1) ❌
- [confluence_formatter_v2.py](../tools/deprecated/confluence_formatter_v2.py:1) ❌

---

**Last Updated**: 2025-10-18
**Phase**: 129 - Confluence Tooling Consolidation
**Status**: ✅ Production Guide - Use These Tools
