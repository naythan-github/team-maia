# Orro Operational Procedures

**Purpose**: Standard operational workflows for Orro/NW Computing work.
**Load When**: Any Orro-related work (security assessments, document creation, customer deliverables).

---

## Document Conversion - MANDATORY TOOL

**When user says**: "Orro docx conversion", "convert to Orro format", "run through Orro conversion", "create Orro document"

**ALWAYS USE**:
```bash
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py <file.md>
```

**NEVER USE** raw pandoc directly - it lacks Orro corporate styling.

### What the Tool Provides
- Orro purple headings: RGB(112, 48, 160)
- Aptos font family
- 1.0" margins
- Corporate table styling
- Professional formatting

### Decision Tree
```
User wants DOCX?
└─ Use: convert_md_to_docx.py (handles ALL documents including PIRs)
```

---

## Security Assessments

**Output Location**: `~/work_projects/{customer}_security_assessment/`

**Standard Deliverables**:
1. `{Customer}_Security_Assessment.md` - Initial findings
2. `{Customer}_PIR_Security_Investigation.md` - Post-Incident Report (if incident)
3. `{Customer}_Verification_Actions.md` - Open items requiring action

**Conversion**: Always convert final deliverables to DOCX using the tool above.

---

## Quick Reference

| Task | Tool |
|------|------|
| MD → DOCX (all documents) | `convert_md_to_docx.py` |
| New PIR from template | `pir_template_manager.py` |
| Job Description cleanup | `prepare_docx_for_markdown.py` |

---

**Version**: 1.0 | **Created**: December 2025 | **Owner**: SRE Principal Engineer Agent
