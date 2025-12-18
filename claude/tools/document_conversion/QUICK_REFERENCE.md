# Document Conversion - Quick Reference

**Phase 163** | **November 21, 2025** | **Document Conversion Specialist Agent**

---

## 🚀 One-Line Commands

### **Generic Document (Most Common)** ⭐

```bash
# Technical docs, meeting notes, reports - ANY markdown
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py YOUR_FILE.md
```

### **Job Descriptions** ⭐ **NEW - Phase 177**

```bash
# Cleanup existing DOCX (fix bullets, formatting)
python3 ~/maia/claude/tools/document_conversion/prepare_docx_for_markdown.py JD.docx

# Convert cleaned markdown to styled DOCX
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py JD.md
```

### **PIR (Security Incidents)**

```bash
# Convert PIR markdown to DOCX (uses same converter - handles PIR tables automatically)
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py PIR_FILE.md

# Create new PIR from template
python3 ~/maia/claude/tools/document/pir/pir_template_manager.py create \
  pir_credential_stuffing_template OUTPUT.docx \
  --ticket 4200123 --customer "Company" --severity SEV1
```

---

## 📋 Decision Tree

```
What are you doing?
│
├─ Job Description?
│  ├─ Cleanup existing DOCX? → prepare_docx_for_markdown.py
│  ├─ New from template? → job_description_template_lean.md
│  └─ Convert to styled DOCX? → convert_md_to_docx.py
│
├─ Converting markdown → DOCX?
│  └─ Use: convert_md_to_docx.py ⭐ (handles ALL documents including PIRs)
│
└─ Creating PIR from scratch?
   └─ Use: pir_template_manager.py
```

---

## 📁 Template Locations

| Template | Location | Use For |
|----------|----------|---------|
| **job_description_template_lean.md** ⭐ | `~/maia/claude/templates/` | New JDs (Orro standard) |
| **job_description_template.md** | `~/maia/claude/templates/` | New JDs (comprehensive) |
| **orro_corporate_reference.docx** | `~/maia/claude/tools/document_conversion/templates/` | ANY markdown conversion ⭐ |
| **pir_orro_reference.docx** | `~/maia/claude/tools/document/pir/templates/` | PIR markdown conversion |
| **pir_credential_stuffing_template.docx** | `~/maia/claude/tools/document/pir/templates/` | New PIR creation (Jinja2) |

---

## 🎯 Common Use Cases

### **1. Technical Documentation**
```bash
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py ARCHITECTURE.md
```

### **2. Meeting Notes**
```bash
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py meeting_2024-11-21.md
```

### **3. Project Report**
```bash
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py project_status.md
```

### **4. PIR Conversion**
```bash
python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py nqlc_pir_4184007.md
```

### **5. New PIR Creation**
```bash
python3 ~/maia/claude/tools/document/pir/pir_template_manager.py create \
  pir_credential_stuffing_template \
  ~/work_projects/acme_incident/PIR_4200456_ACME.docx \
  --ticket 4200456 --customer "ACME Corp" --severity SEV1
```

---

## ⚡ Fast Commands (Aliases)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Generic conversion (handles ALL documents including PIRs)
alias md2docx='python3 ~/maia/claude/tools/document_conversion/convert_md_to_docx.py'

# PIR template
alias pir-new='python3 ~/maia/claude/tools/document/pir/pir_template_manager.py create pir_credential_stuffing_template'
```

**Usage after aliases**:
```bash
md2docx technical_doc.md              # Any document (including PIRs)
pir-new OUTPUT.docx --ticket 123      # New PIR from template
```

---

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| "Pandoc not found" | `brew install pandoc` |
| "Template not found" | `python3 ~/maia/claude/tools/document_conversion/create_clean_orro_template.py` |
| "python-docx not found" | `pip3 install python-docx` |
| Wrong template used | Check decision tree above |

---

## 📚 Full Documentation

- **Generic Conversion**: `~/maia/claude/tools/document_conversion/README.md`
- **PIR System**: `~/maia/claude/tools/document/pir/PIR_QUICK_START.md`
- **Reorganization Details**: `~/maia/claude/tools/document_conversion/REORGANIZATION_SUMMARY.md`

---

**Quick Reference** | **Phase 163** | **Ready to Use**
