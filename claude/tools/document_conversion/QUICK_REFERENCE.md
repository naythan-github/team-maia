# Document Conversion - Quick Reference

**Phase 163** | **November 21, 2025** | **Document Conversion Specialist Agent**

---

## 🚀 One-Line Commands

### **Generic Document (Most Common)** ⭐

```bash
# Technical docs, meeting notes, reports - ANY markdown
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py YOUR_FILE.md
```

### **PIR (Security Incidents Only)**

```bash
# Convert PIR markdown to DOCX
python3 ~/work_projects/pir_converter/convert_pir_v3.py PIR_FILE.md

# Create new PIR from template
python3 ~/git/maia/claude/tools/security/pir_template_manager.py create \
  pir_credential_stuffing_template OUTPUT.docx \
  --ticket 4200123 --customer "Company" --severity SEV1
```

---

## 📋 Decision Tree

```
What are you doing?
│
├─ Converting markdown → DOCX?
│  ├─ Is it a PIR?
│  │  └─ Use: convert_pir_v3.py
│  └─ Anything else? ⭐
│     └─ Use: convert_md_to_docx.py
│
└─ Creating PIR from scratch?
   └─ Use: pir_template_manager.py
```

---

## 📁 Template Locations

| Template | Location | Use For |
|----------|----------|---------|
| **orro_corporate_reference.docx** | `~/git/maia/claude/tools/document_conversion/templates/` | ANY markdown conversion ⭐ |
| **pir_orro_reference.docx** | `~/work_projects/pir_converter/` | PIR markdown conversion |
| **pir_credential_stuffing_template.docx** | `~/git/maia/claude/tools/security/pir_templates/` | New PIR creation (Jinja2) |

---

## 🎯 Common Use Cases

### **1. Technical Documentation**
```bash
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py ARCHITECTURE.md
```

### **2. Meeting Notes**
```bash
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py meeting_2024-11-21.md
```

### **3. Project Report**
```bash
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py project_status.md
```

### **4. PIR Conversion**
```bash
cd ~/work_projects/pir_converter
python3 convert_pir_v3.py nqlc_pir_4184007.md
```

### **5. New PIR Creation**
```bash
python3 ~/git/maia/claude/tools/security/pir_template_manager.py create \
  pir_credential_stuffing_template \
  ~/work_projects/acme_incident/PIR_4200456_ACME.docx \
  --ticket 4200456 --customer "ACME Corp" --severity SEV1
```

---

## ⚡ Fast Commands (Aliases)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Generic conversion (most common)
alias md2docx='python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py'

# PIR conversion
alias pir2docx='python3 ~/work_projects/pir_converter/convert_pir_v3.py'

# PIR template
alias pir-new='python3 ~/git/maia/claude/tools/security/pir_template_manager.py create pir_credential_stuffing_template'
```

**Usage after aliases**:
```bash
md2docx technical_doc.md              # Generic conversion
pir2docx incident_review.md           # PIR conversion
pir-new OUTPUT.docx --ticket 123      # New PIR
```

---

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| "Pandoc not found" | `brew install pandoc` |
| "Template not found" | `python3 ~/git/maia/claude/tools/document_conversion/create_clean_orro_template.py` |
| "python-docx not found" | `pip3 install python-docx` |
| Wrong template used | Check decision tree above |

---

## 📚 Full Documentation

- **Generic Conversion**: `~/git/maia/claude/tools/document_conversion/README.md`
- **PIR System**: `~/git/maia/claude/tools/security/PIR_QUICK_START.md`
- **Reorganization Details**: `~/git/maia/claude/tools/document_conversion/REORGANIZATION_SUMMARY.md`

---

**Quick Reference** | **Phase 163** | **Ready to Use**
