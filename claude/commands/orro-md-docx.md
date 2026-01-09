# /orro-md-docx - Convert Markdown to Orro-Branded DOCX

Quick access to the Orro corporate document converter with full branding pipeline.

## Usage
```bash
# Convert with full Orro styling (recommended)
python3 claude/tools/document_conversion/orro_md_to_docx.py document.md

# Specify custom output path
python3 claude/tools/document_conversion/orro_md_to_docx.py document.md --output "Custom Name.docx"

# Skip table styling for faster conversion (documents without tables)
python3 claude/tools/document_conversion/orro_md_to_docx.py document.md --no-table-styles
```

## What It Does
Full Orro corporate branding pipeline:
1. **Pandoc conversion** with Orro reference template
2. **Purple table styling** with explicit RGB borders (#7030A0)
3. **Content-aware column widths** for optimal readability
4. **Orro purple headings** RGB(112, 48, 160)
5. **Aptos font** (corporate standard, 8pt in tables)
6. **1.0" margins** all sides

## Common Use Cases
- **Technical documentation** (architecture docs, RFCs)
- **Meeting notes** (like alert threshold optimization analysis)
- **Project reports** (status updates, post-mortems)
- **SIP documents** (service improvement proposals)
- **Any markdown → branded DOCX** with corporate styling

## Example
```bash
# Convert your alert threshold analysis
python3 claude/tools/document_conversion/orro_md_to_docx.py ~/work_projects/alert_threshold_optimization.md
```

## Output
- Creates `document.docx` in the same directory as input
- Full Orro corporate styling applied
- Tables with purple borders and content-aware widths
- Headings styled with Orro purple
- Ready for immediate distribution

## Implementation
Executes: `python3 claude/tools/document_conversion/orro_md_to_docx.py`

## Related Tools
- **PIR Normalizer**: `claude/tools/document/pir/pir_docx_normalizer.py` (used internally)
- **Template Creator**: `claude/tools/document_conversion/create_clean_orro_template.py`
- **Document Specialist Agent**: `claude/agents/document_conversion_specialist_agent.md`

## Searchable Keywords
orro, corporate, branding, markdown, docx, convert, word, purple, styling, tables, template
