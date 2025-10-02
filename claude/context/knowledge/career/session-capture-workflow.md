# Session Content Capture Workflow

**REMINDER: Follow core non-negotiable standards in CLAUDE.md**
- Australian English spelling (optimise not optimize, centre not center, analyse not analyze)
- Sentence case formatting for all headings and bullet points
- Never merge experiences - each bullet must be from a single exp_id
- Use exact database metrics only - never create or calculate new figures

---

## Session Content Capture Methodology

### During CV Sessions
1. **Maintain targeted focus** on current JD requirements (ATS optimisation priority)
2. **Simultaneously capture** all additional user details in `source-files/session-notes-[role]-[date].md`
3. **Mark content status** as "captured in DB ✅" vs "pending processing ⚠️"
4. **Document potential new experiences** even if not relevant to current JD
5. **Use attribution confirmation protocol** to prevent unintended merging (see below)

### Session Notes Structure
```markdown
# Session Notes - [Company] [Role] - [Date]

## ADDITIONAL DETAILS PROVIDED BY USER
### [Category Name]
**CAPTURED IN DATABASE:** ✅ or ⚠️
- Specific details provided...
- Additional context...

## POTENTIAL NEW EXPERIENCES TO EXTRACT
### [EMP-XXX (Candidate)]
- Category: 
- Brief:
- Details:

## DATABASE ENHANCEMENT OPPORTUNITIES
- Cross-role patterns identified
- Metrics enhancements needed
- Additional context to capture

## POST-SESSION CLEANUP PLAN
- Phase 1: Database updates
- Phase 2: Pattern analysis
- Phase 3: Validation
```

### Post-Session Database Enhancement
1. **Process session notes** into proper database entries after CV completion
2. **Create new experiences** using next sequential exp_id (e.g., ZETTA-006, OA-027)
3. **Enhance existing experiences** with additional authentic details provided
4. **Update database metadata**:
   - Increment version number
   - Update last_modified date
   - Add update_log entry describing changes
   - Update statistics (total_experiences count)

### Benefits of This Approach
- **Never lose information** provided during sessions
- **Stay focused** on immediate CV/ATS requirements
- **Build comprehensive database** progressively over time
- **Track what's captured** vs what needs processing
- **Improve future CV quality** with richer source material

## Session Notes File Naming Convention
- Format: `session-notes-[company]-[role]-[YYYY-MM-DD].md`
- Location: `source-files/` directory
- Examples:
  - `session-notes-pwc-brm-2025-08-28.md`
  - `session-notes-microsoft-tam-2025-09-15.md`
  - `session-notes-aws-csm-2025-10-02.md`

## Database Enhancement Best Practices

### Creating New Experiences
- Use next sequential exp_id for employer (e.g., ZETTA-006, OA-027)
- Follow standard JSON structure with all required fields
- Include comprehensive `full_context` with authentic details
- Add relevant `ats_keywords` for future searchability
- Set `verified: true` and appropriate dates

### Enhancing Existing Experiences
- Preserve original structure and verified status
- Add new details to `full_context` without removing existing content
- Enhance `metrics` section with newly provided quantified data
- Update `last_modified` date
- Add context to explain enhancements if significant

### Version Control
- Increment major version (1.0 → 1.1) for new experiences added
- Increment minor version (1.1 → 1.1.1) for enhancements to existing experiences
- Always add entry to `update_log` explaining changes made
- Update `total_experiences` count in statistics section

## Attribution Confirmation Protocol

**CRITICAL: To prevent unintended experience merging, use confirmation protocol for all database work.**

### **Database Enhancement Confirmations** (Required):
When user provides additional details for existing experiences:
```
CONFIRMATION REQUIRED:
You mentioned: [specific detail provided]
I believe this belongs to: exp_id XXX-### 
Current experience brief: "[current brief from database]"
CONFIRM: Does this detail belong to this specific exp_id? (Yes/No)
If No, please specify which exp_id it should go to.
```

### **Session Detail Attribution** (Required):
When capturing new information during sessions:
```
ATTRIBUTION CONFIRMATION:
New detail provided: "[user statement]"
This appears to be:
[ ] A new experience (needs new exp_id)
[ ] Enhancement to existing exp_id: XXX-###
[ ] General pattern across multiple experiences
CONFIRM: How should this be attributed?
```

### **Bullet Creation** (No Confirmation Required):
- Continue efficiently with single exp_id discipline
- One bullet = one exp_id only
- Use exact metrics from that exp_id
- No combining context from multiple sources

### **Benefits of This Protocol:**
- ✅ Prevents unconscious merging during database work
- ✅ Maintains user control over all attributions
- ✅ Creates audit trail of attribution decisions
- ✅ Keeps CV creation workflow efficient
- ✅ Protects database integrity at high-risk points