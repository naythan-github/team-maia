# PIR Document Pipeline

Post-Incident Review (PIR) document conversion and formatting tools.

## Directory Structure

```
pir/
├── convert_pir.py           # MD → DOCX converter (Pandoc + table styles)
├── pir_docx_normalizer.py   # DOCX formatting normalizer
├── pir_template_manager.py  # Template management utilities
├── templates/
│   ├── pir_orro_reference.docx              # Pandoc reference template
│   ├── pir_credential_stuffing_template.*   # Credential stuffing PIR template
│   └── pir_standard_structure.json          # Standard PIR structure definition
└── README.md
```

## Usage

### Full Pipeline (MD → Styled DOCX)

```bash
# Step 1: Convert markdown to DOCX with table styles
python3 claude/tools/document/pir/convert_pir.py input.md -o output.docx

# Step 2: Normalize formatting (tables, spacing, borders)
python3 claude/tools/document/pir/pir_docx_normalizer.py output.docx
```

### Normalizer Only (existing DOCX)

```bash
python3 claude/tools/document/pir/pir_docx_normalizer.py document.docx
```

## Formatting Applied

### Tables
- **Width**: 100% page width
- **Font**: Aptos 8pt
- **Borders**: Orro purple (#7030A0 top/bottom, #CBC6F3 horizontal dividers)
- **Column sizing**: Content-aware (10% min, 60% max per column)
- **Cell spacing**: 2pt before/after

### Paragraphs
- **Headings**: 12pt before, 6pt after
- **Body text**: 6pt after
- **Lists**: 2pt before/after (tight)

## Tests

```bash
# Run all PIR tests
python3 -m pytest tests/test_pir_docx_normalizer.py tests/test_convert_pir_v3_integration.py -v
```

## Dependencies

- `python-docx`: DOCX manipulation
- `pandoc`: Markdown to DOCX conversion (external)
