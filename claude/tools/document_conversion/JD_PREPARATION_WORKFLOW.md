# Job Description Preparation Workflow

**Phase 177** | **November 26, 2024** | **Technical Recruitment Agent**

Complete workflow for creating and formatting job descriptions for Word conversion.

---

## 📋 Overview

**Problem**: Word documents with paragraph-style text don't convert cleanly to markdown, and markdown bullets don't render properly in Word without proper formatting.

**Solution**: Two-step process:
1. **Prepare**: Clean DOCX → Bulletized Markdown
2. **Convert**: Markdown → Styled DOCX (Orro branding)

---

## 🚀 Quick Start

### New JD from Template
```bash
# 1. Copy template
cp ~/git/maia/claude/templates/job_description_template_lean.md "Senior Cloud Architect.md"

# 2. Fill in content (manually edit the file)

# 3. Convert to DOCX with Orro styling
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py "Senior Cloud Architect.md"
```

### Existing DOCX Cleanup
```bash
# 1. Prepare DOCX (add bullets, fix formatting)
python3 ~/git/maia/claude/tools/document_conversion/prepare_docx_for_markdown.py "Draft JD.docx"

# 2. Review and edit Draft JD.md if needed

# 3. Convert back to styled DOCX
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py "Draft JD.md"
```

---

## 📐 Template Structure

**Location**: `~/git/maia/claude/templates/job_description_template_lean.md`

**Based on**: Orro Pod Lead JD format (Senior Cloud Engineer)

### Sections
1. **Position Context** - Metadata table (title, location, team, etc.)
2. **Position Overview** - 2 paragraphs (role description)
3. **Position Responsibilities** - 4-5 categories with sentence-level bullets
4. **Skills, Knowledge & Experience** - 6-8 bullet points
5. **Qualifications** - Degree, experience, certifications

### Formatting Rules
- **Bullets**: Use `•` character (not `-` dash)
- **Sentences**: Each sentence = separate bullet
- **Trailing spaces**: Add 2 spaces after each bullet for markdown rendering
- **Headers**: Use `##` for sections, `###` for subsections

---

## 🛠️ Tools Reference

### 1. Template
**File**: `~/git/maia/claude/templates/job_description_template_lean.md`

**Purpose**: Starting point for new JDs

**Usage**: Copy, fill placeholders `[...]`, delete usage notes

### 2. DOCX Preparation Script
**File**: `~/git/maia/claude/tools/document_conversion/prepare_docx_for_markdown.py`

**Purpose**: Clean existing Word docs for markdown conversion

**What it fixes**:
- Unicode line separators (`\u2028`, `\u2029`) from Word
- Paragraph-style text → sentence-level bullets
- Missing markdown line breaks (adds 2 trailing spaces)
- Merged section headers

**Usage**:
```bash
python3 prepare_docx_for_markdown.py INPUT.docx
python3 prepare_docx_for_markdown.py INPUT.docx --output custom.md
```

### 3. Markdown to DOCX Converter
**File**: `~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py`

**Purpose**: Convert markdown to styled Word document

**Orro Styling**:
- Aptos font (corporate standard)
- Purple headings RGB(112, 48, 160)
- 1.0" margins
- Purple table styling (_Orro Table 1)

**Usage**:
```bash
python3 convert_md_to_docx.py INPUT.md
python3 convert_md_to_docx.py INPUT.md --output custom.docx
```

---

## 🔄 Complete Workflow Examples

### Example 1: New JD from Scratch

```bash
# Step 1: Copy template
cd ~/git/maia/claude/templates
cp job_description_template_lean.md ~/Desktop/"DevOps Engineer.md"

# Step 2: Edit file (manually)
# - Replace [Role Title] with "DevOps Engineer"
# - Fill in Position Context metadata
# - Write Position Overview (2 paragraphs)
# - Add responsibilities (4-5 sections, 3 bullets each)
# - Add skills (6-8 bullets)
# - Add qualifications (3 bullets)
# - Delete usage notes

# Step 3: Convert to DOCX
cd ~/Desktop
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py "DevOps Engineer.md"

# Result: DevOps Engineer.docx with Orro styling
```

### Example 2: Cleanup Existing Word Doc

```bash
# Step 1: Prepare DOCX (bulletize content)
python3 ~/git/maia/claude/tools/document_conversion/prepare_docx_for_markdown.py \
  "Old JD Draft.docx"

# Result: Old JD Draft.md (cleaned markdown)

# Step 2: Review and edit if needed
open "Old JD Draft.md"  # Make manual edits

# Step 3: Convert to styled DOCX
python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py \
  "Old JD Draft.md"

# Result: Old JD Draft.docx with Orro styling
```

### Example 3: Batch Process Multiple JDs

```bash
# Create batch script
cat > convert_all_jds.sh << 'EOF'
#!/bin/bash
for file in *.md; do
  echo "Converting: $file"
  python3 ~/git/maia/claude/tools/document_conversion/convert_md_to_docx.py "$file"
done
EOF

chmod +x convert_all_jds.sh

# Run batch conversion
./convert_all_jds.sh
```

---

## 🎯 Quality Checklist

Before final Word document:
- [ ] All bullets use `•` character (not dashes)
- [ ] Each sentence is a separate bullet
- [ ] Two spaces after each bullet (markdown rendering)
- [ ] Section headers properly formatted (`##` and `###`)
- [ ] No Unicode separators in text
- [ ] Position Context metadata complete
- [ ] Overview is 2 paragraphs
- [ ] 4-5 responsibility sections with 3 bullets each
- [ ] 6-8 skills bullets
- [ ] 3 qualification bullets

After DOCX conversion:
- [ ] Aptos font applied
- [ ] Headings are Orro purple
- [ ] 1.0" margins all sides
- [ ] No formatting artifacts
- [ ] Bullets render correctly (separate lines)

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bullets on same line in markdown preview | Missing 2 trailing spaces - run prepare script |
| Unicode characters in output | Word used line separators - run prepare script |
| Wrong font in DOCX | Template missing - run `create_clean_orro_template.py` |
| Merged section headers | prepare script will split them |
| Paragraph style instead of bullets | Run prepare script to bulletize |

---

## 📚 Related Documentation

- **Template**: `~/git/maia/claude/templates/job_description_template_lean.md`
- **Conversion Guide**: `~/git/maia/claude/tools/document_conversion/README.md`
- **Quick Reference**: `~/git/maia/claude/tools/document_conversion/QUICK_REFERENCE.md`
- **Role Structure**: OneDrive → `Recruitment/Roles/Role descriptions/ROLE_STRUCTURE_SUMMARY.md`

---

## 📊 Phase 177 Deliverables

**Templates Created**:
- ✅ `job_description_template_lean.md` - Lean JD template (Orro standard)
- ✅ `job_description_template.md` - Full JD template (comprehensive)

**Tools Created**:
- ✅ `prepare_docx_for_markdown.py` - DOCX cleanup and bulletization
- ✅ Workflow documentation (this file)

**Process Validated**:
- ✅ 8 Orro JDs converted successfully
- ✅ Bullet formatting working in markdown and Word
- ✅ Orro styling applied correctly
- ✅ Repeatable workflow documented

---

**Status**: ✅ **READY** - Production workflow for JD preparation and conversion
