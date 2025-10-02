# Confluence Formatting Standards - Maia System

## Problem Analysis: Inconsistent Formatting Quality

### Root Causes Identified
1. **No standardized converter**: Ad-hoc string replacements vs proper HTML parsing
2. **Table structure ignored**: Missing `<table><tbody><tr><td>` hierarchy  
3. **List nesting broken**: Orphaned `<li>` tags without proper `<ul>` closure
4. **Storage format confusion**: Rich text vs storage format requirements
5. **Unicode handling inconsistent**: Emojis and special characters not preserved

## Solution: Structured Formatting Pipeline

### Mandatory Confluence Formatting Process
1. **Use dedicated formatter**: `claude/tools/confluence_formatter.py`
2. **Proper HTML structure**: Complete tag hierarchy with closing tags
3. **Table formatting**: Full `<table class="wrapped"><tbody>` structure
4. **List handling**: Proper nesting with complete `<ul><li>` closure
5. **Unicode preservation**: Maintain emojis (✅❌⚡🔍💡) and special characters

### Quality Standards

#### Headers
```html
<h1>Executive Summary</h1>
<h2>Section Title</h2>
<h3>Subsection</h3>
```

#### Tables
```html
<table class="wrapped">
<tbody>
<tr><td>Header 1</td><td>Header 2</td></tr>
<tr><td>✅ Data</td><td>Content</td></tr>
</tbody>
</table>
```

#### Lists
```html
<ul>
<li>First item with <strong>bold</strong> text</li>
<li>Second item with ⚡ emoji</li>
</ul>
```

#### Inline Formatting
- **Bold**: `<strong>text</strong>`
- **Italic**: `<em>text</em>`
- **Code**: `<code>text</code>`
- **Emojis**: Preserve Unicode directly

### Implementation Rules

#### When Creating Confluence Pages
1. **Always use** `confluence_formatter.py` for markdown conversion
2. **Test format** with small sample before full page creation
3. **Validate structure** - proper opening/closing tags
4. **Preserve content** - no information loss during conversion

#### Quality Checkpoints
- [ ] Headers properly nested (h1 > h2 > h3)
- [ ] Tables have complete structure with tbody
- [ ] Lists are properly closed
- [ ] Emojis and special characters preserved
- [ ] No orphaned HTML tags
- [ ] Paragraphs properly wrapped in `<p>` tags

### Tools and Resources

#### Primary Tool
`${MAIA_ROOT}/claude/tools/confluence_formatter.py`
- Handles markdown → Confluence storage format
- Proper HTML structure generation
- Unicode character preservation
- Table and list formatting

#### Usage Pattern
```python
from claude.tools.confluence_formatter import markdown_to_confluence_storage
confluence_content = markdown_to_confluence_storage(markdown_text)
```

#### API Integration
```python
page_data = {
    'type': 'page',
    'title': 'Page Title',
    'space': {'key': 'SpaceKey'},
    'body': {
        'storage': {
            'value': confluence_content,
            'representation': 'storage'
        }
    }
}
```

### Performance Monitoring

#### Success Indicators
- Pages display correctly in Confluence
- Tables render with proper alignment
- Lists show proper bullet/number formatting
- Emojis and special characters visible
- No HTML rendering errors

#### Failure Indicators
- Broken table layouts
- Orphaned list items
- Missing emojis or special characters
- Raw HTML tags visible in page
- Content formatting inconsistencies

### Future Improvements

#### Planned Enhancements
1. **Rich media support**: Images, attachments, macros
2. **Advanced tables**: Merged cells, styling
3. **Code block highlighting**: Language-specific formatting
4. **Link processing**: Internal and external link handling
5. **Template integration**: Standard page layouts

#### Integration Points
- UFC context system for content source
- Knowledge graph for intelligent formatting
- Agent system for specialized page types
- Quality assurance automation

This standardization ensures consistent, professional Confluence page formatting across all Maia system interactions.