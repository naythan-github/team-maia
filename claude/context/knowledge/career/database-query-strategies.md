# Database Query Strategies

**REMINDER: Follow core non-negotiable standards in CLAUDE.md**
- Australian English spelling (optimise not optimize, centre not center, analyse not analyze)
- Sentence case formatting for all headings and bullet points
- Never merge experiences - each bullet must be from a single exp_id
- Use exact database metrics only - never create or calculate new figures

---

## JSON Database Usage for CV Creation

### Quick Start Strategy
1. **Extract JD Requirements**: Identify core competencies, skills, and responsibilities from job description (e.g., stakeholder management, budget oversight, team leadership 10+ people)
2. **Load Employer-Specific Files**: Read individual employer JSON files based on bullet needs:
   - `experiences_zetta.json` (5 bullets) - Current role emphasis
   - `experiences_telstra.json` (7 bullets) - Core BRM/technical experience  
   - `experiences_oneadvanced.json` (7 bullets) - UK professional services experience
   - `experiences_viadex.json` (2 bullets) - Process improvement focus
   - `experiences_halsion.json` (2 bullets) - Leadership/entrepreneurship
3. **Search Each File Broadly**: Query ALL fields - `category`, `ats_keywords`, `metrics`, `achievement.brief` - not just `relevance_tags`
4. **Match Competencies First**: Prioritise experiences that demonstrate required competencies regardless of tags
5. **Apply Tags as Secondary Filter**: Use `relevance_tags` to refine selections within each employer file
6. **Filter by Impact**: Use `metrics` field to find quantified results that match role scope
7. **Use STAR Stories for ATS**: When `star_story.available = true`, extract detailed language and keywords from STAR content to enhance ATS scoring
8. **Use Testimonial Support**: Query `source-files/feedback_database.json` for feedback linked to selected experiences

### Employer File Search Strategy Examples
```json
// For unknown/new role types - Requirements-driven approach:
// 1. Load appropriate employer files (all 5 for full CV)
// 2. Search within each file across ALL fields:

// Example: JD requires "stakeholder management" + "team leadership 15+" + "cost optimisation"

// Zetta file search (5 bullets needed):
search: ats_keywords contains "stakeholder" OR category contains "business-development"

// Telstra file search (7 bullets needed): 
search: metrics.team_size >= 15 OR ats_keywords contains ["demand management", "cost optimisation"]

// OneAdvanced file search (7 bullets needed):
search: ats_keywords contains "executive engagement" OR metrics.cost_savings > 100000

// Traditional tag-based (use as secondary filter only):
filter: relevance_tags contains ["BRM", "stakeholder-management"] // AFTER competency match

// Performance optimisation with smaller files:
// Instead of loading 2000+ line database, load specific 100-200 line employer files
```

### Employer Database Statistics
- **Zetta**: 6 experiences (5 bullets) - Current role, portfolio management, revenue generation, compliance
- **Telstra**: 17 experiences (7 bullets) - BRM, crisis management, team leadership, STAR stories
- **OneAdvanced**: 27 experiences (7 bullets) - Professional services, cost optimisation, executive engagement  
- **Viadex**: 4 experiences (2 bullets) - Process improvement, automation
- **Halsion**: 8 experiences (2 bullets) - Leadership, entrepreneurship, business development
- **Complete STAR Stories**: 8 available across employers for ATS keyword enhancement
- **Testimonials**: 17 linked to specific experiences across all employers
- **File Sizes**: 100-400 lines each vs 2000+ for legacy database

## Feedback and USP Database Usage

### **Feedback Database** (`source-files/feedback_database.json`)
- **17 testimonials** from colleagues, managers, and clients
- **Structured format**: source, context, relationship, themes, full_text
- **Searchable themes**: leadership, technical-expertise, problem-solving, mentoring, etc.
- **Usage**: Query by theme or source to find supporting testimonials for CV claims

### **USP Database** (`source-files/usp_database.json`)
- **Core differentiators** and unique value propositions
- **Positioning statements** for different role types
- **Structured format**: category, description, evidence_sources, supporting_experiences
- **Usage**: Select USPs that align with job requirements and integrate into CV narrative

## Advanced Query Techniques

### Cross-Employer Pattern Matching
```json
// Find experiences across multiple employers with similar themes
search: category contains "crisis-management" AND metrics.team_size > 10

// Find cost optimisation examples with quantified savings
search: ats_keywords contains "cost" AND metrics.cost_savings exists

// Find customer-facing roles with C-level engagement
search: ats_keywords contains ["executive", "CIO", "C-suite"] AND category contains "stakeholder"
```

### Metrics-Driven Selection
```json
// High-impact financial metrics
search: metrics.revenue_increase > 1000000 OR metrics.cost_savings > 100000

// Team leadership scope
search: metrics.team_size >= 15 OR metrics.people_managed >= 10

// Geographic scope for international roles
search: keywords contains ["international", "global", "multi-country"]
```

### Performance Optimisation Tips
- **Load smaller files first**: Start with most relevant employer files
- **Use targeted searches**: Query specific fields rather than full-text search
- **Cache frequently used data**: Remember common patterns for similar roles
- **Verify data integrity**: Always trace bullets back to single exp_id source