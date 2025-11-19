# Post-Incident Review (PIR) Template - Quick Start Guide
## Security Specialist Agent - One-Page Reference

**Status**: ✅ Your NQLC PIR is now saved as a reusable template!

---

## 🚀 USING THE TEMPLATE FOR NEXT INCIDENT

### **Step 1: Create New PIR from Template** (30 seconds)

```bash
cd ~/git/maia

python3 claude/tools/security/pir_template_manager.py create \
  credential_stuffing_pir \
  ~/work_projects/CUSTOMER_incident_review/PIR_TICKET_CUSTOMER.docx \
  --ticket TICKET_NUMBER \
  --customer "Customer Name" \
  --incident-type "Incident Description" \
  --severity SEV1
```

**Example** (Next credential stuffing incident):
```bash
python3 claude/tools/security/pir_template_manager.py create \
  credential_stuffing_pir \
  ~/work_projects/acme_incident_review/PIR_4200456_ACME.docx \
  --ticket 4200456 \
  --customer "ACME Corporation" \
  --incident-type "Password Spray Attack" \
  --severity SEV1
```

**What happens**:
- ✅ Creates new DOCX with your section order
- ✅ Replaces all placeholders automatically
- ✅ Ready to populate with forensic findings

---

### **Step 2: Run Forensic Analysis** (5 minutes)

```bash
cd ~/work_projects/acme_incident_review

# Copy forensic analysis script from NQLC
cp ~/work_projects/nqlc_incident_review/forensic_analysis.py .

# Run analysis on new customer's logs
python3 forensic_analysis.py
```

**Output**:
- Compromised account list
- Attack source IPs and locations
- Timeline and patterns
- IOC report (JSON)

---

### **Step 3: Populate PIR with Findings** (2-3 hours)

Open the generated DOCX and fill in:
- Copy forensic analysis results
- Add IOCs from `ioc_report.json`
- Document root cause
- Create remediation plan
- Write lessons learned

---

### **Step 4: Security Review** (30 minutes)

**Ask Security Specialist Agent to review**:
```
"Review this PIR for accuracy and completeness:
/path/to/PIR_TICKET_CUSTOMER.docx"
```

Agent will:
- Fact-check claims against logs
- Validate technical accuracy
- Generate corrected version if needed

---

### **Step 5: Generate Executive Summary** (2 minutes)

**Ask Security Specialist Agent**:
```
"Generate 1-page executive summary from this PIR for board presentation"
```

Agent will create:
- EXECUTIVE_SUMMARY_TICKET_CUSTOMER.docx
- Key metrics, root cause, remediation status
- Board-ready format

---

## 📁 FILE ORGANIZATION

**For each incident, create**:
```
~/work_projects/
└── customer_incident_review/
    ├── PIR_TICKET_CUSTOMER.docx                    # Full PIR
    ├── EXECUTIVE_SUMMARY_TICKET_CUSTOMER.docx      # Board version
    ├── forensic_analysis.py                         # Analysis script
    ├── ioc_report.json                              # IOCs
    ├── InteractiveSignIns_DATE1_DATE2.csv          # Log files
    └── BREACH_DATABASE_CHECK_GUIDE.md              # HIBP guide
```

---

## 🎯 TEMPLATE LOCATIONS

**Template Files** (Don't modify directly):
```
~/git/maia/claude/tools/security/pir_templates/
├── credential_stuffing_pir.docx     # Your template
└── credential_stuffing_pir.json     # Metadata
```

**Tools**:
```
~/git/maia/claude/tools/security/
├── pir_template_manager.py          # Template manager
├── PIR_TEMPLATE_SYSTEM.md           # Full documentation
└── PIR_QUICK_START.md               # This file
```

---

## 📝 AVAILABLE PLACEHOLDERS

Your template supports automatic replacement:

| Placeholder | Replace With |
|-------------|--------------|
| `{{TICKET_NUMBER}}` | Service desk ticket (e.g., 4200456) |
| `{{CUSTOMER_NAME}}` | Customer name (e.g., "ACME Corporation") |
| `{{INCIDENT_TYPE}}` | Incident description (e.g., "Password Spray") |
| `{{SEVERITY}}` | SEV1, SEV2, SEV3, or SEV4 |
| `{{INCIDENT_DATE}}` | Date detected (YYYY-MM-DD) |
| `{{REPORT_DATE}}` | Auto-filled with today's date |
| `{{ANALYST_NAME}}` | Auto-filled with "Security Specialist Agent (Maia)" |

---

## 🔧 TEMPLATE MANAGEMENT COMMANDS

**List available templates**:
```bash
python3 claude/tools/security/pir_template_manager.py list
```

**Save new template** (when you customize another PIR):
```bash
python3 claude/tools/security/pir_template_manager.py save \
  /path/to/completed/PIR.docx \
  template_name \
  --description "When to use this template" \
  --incident-type "incident_category"
```

**Create from template**:
```bash
python3 claude/tools/security/pir_template_manager.py create \
  template_name \
  /path/to/output.docx \
  --ticket TICKET \
  --customer "Customer" \
  --incident-type "Type" \
  --severity SEV1
```

---

## 💡 TIPS & BEST PRACTICES

### **Customizing Templates**

✅ **DO**:
- Modify section order for your workflow
- Add/remove sections as needed
- Save variations as new templates

❌ **DON'T**:
- Edit template files directly (create new version instead)
- Remove placeholder syntax `{{PLACEHOLDER}}`
- Delete forensic methodology sections

### **Reusing Forensic Analysis**

The `forensic_analysis.py` script works for ANY M365/Azure AD credential stuffing incident:

1. Copy script to new incident folder
2. Update CSV filename in script (line 245)
3. Run analysis
4. Results auto-populate report

### **Version Control**

**Track template changes**:
```bash
# Template files are in Maia repo
cd ~/git/maia
git add claude/tools/security/pir_templates/
git commit -m "Updated credential stuffing PIR template"
git push
```

---

## 📊 TIME SAVINGS

**Without Template**:
- PIR creation: 8-12 hours
- Formatting: 2-3 hours
- Total: **10-15 hours**

**With Template**:
- Template creation: 1 minute
- Forensic analysis: 5 minutes (automated)
- Data population: 2-3 hours
- Review: 30 minutes
- Total: **3-4 hours**

**Savings**: **70-75% time reduction** (7-11 hours saved per incident)

---

## 🆘 TROUBLESHOOTING

**Problem**: "Template not found"
**Solution**: Run `python3 pir_template_manager.py list` to see available templates

**Problem**: "Placeholders not replaced"
**Solution**: Ensure you used `--ticket` and `--customer` flags when creating PIR

**Problem**: "Script fails with import error"
**Solution**: Run `pip3 install python-docx` to install required library

**Problem**: "Want to update template with changes"
**Solution**: Save modified PIR as new template with different name (e.g., `credential_stuffing_pir_v2`)

---

## 📞 NEXT STEPS

**For your next credential stuffing incident**:

1. ✅ Run `create` command with new ticket/customer details (30 sec)
2. ✅ Run forensic analysis on new logs (5 min)
3. ✅ Populate PIR with findings (2-3 hours)
4. ✅ Security Specialist review (30 min)
5. ✅ Generate executive summary (2 min)
6. ✅ Distribute to client (ready!)

**Total time**: 3-4 hours (vs 10-15 hours manual)

---

## 📚 MORE INFORMATION

**Full Documentation**: `~/git/maia/claude/tools/security/PIR_TEMPLATE_SYSTEM.md`

**Forensic Tools**:
- `forensic_analysis.py` - Automated log analysis
- `BREACH_DATABASE_CHECK_GUIDE.md` - HIBP instructions
- `SECURITY_REVIEW_POST_INCIDENT_REPORT.md` - Validation methodology

**Questions?**
- Ask Security Specialist Agent: "How do I [task] with PIR templates?"
- Review template documentation above
- Check example in `~/work_projects/nqlc_incident_review/`

---

**Created**: November 19, 2025 (Phase 158 - NQLC Incident #4184007)
**Template Saved**: ✅ credential_stuffing_pir.docx
**Status**: Ready for next incident
