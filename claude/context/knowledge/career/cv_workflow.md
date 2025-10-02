# CV Creation Workflow - 4-Stage Process

**⚠️ CRITICAL: Each stage MUST be completed and verified before proceeding to the next stage.**

## Stage 1: Data Collection & Verification

### Objective
Collect and verify all source data required for CV creation with zero assumptions.

### Process
1. **Job Description Analysis**
   - Read complete JD using Read tool
   - Extract core competencies and requirements
   - Identify key responsibilities and required skills
   - Weight requirements by emphasis and frequency in JD
   - Map to search themes (leadership, stakeholder management, technical delivery)

2. **Database File Reading**
   - `claude/data/career/experiences_zetta.json`
   - `claude/data/career/experiences_telstra.json`
   - `claude/data/career/experiences_oneadvanced.json`
   - `claude/data/career/experiences_viadex.json`
   - `claude/data/career/experiences_halsion.json`
   - `claude/data/career/personal_profile.json`

3. **Employment Data Extraction**
   For each employer, extract exact data:
   - Company Name (exact from database)
   - Location (exact from database)
   - Role Title(s) (exact from database)
   - Start Date (exact from database)
   - End Date (exact from database OR "Present" only if end_date is null)
   - Current Employment status (Yes/No based on end_date field)

### Completion Criteria
- [ ] JD file read completely using Read tool
- [ ] All employer JSON files read completely using Read tool
- [ ] Employment data verification checklist completed for each employer
- [ ] No assumptions or guesswork made
- [ ] All data traced directly to source database files

---

## Stage 2: Experience Selection

### Objective
Select optimal experiences using semantic analysis and deduplication verification.

### Process
1. **Semantic Matching Analysis**
   - Use Task tool for comprehensive database search
   - Apply relevance scoring against JD requirements
   - Identify high relevance indicators:
     - Direct terminology overlap between experience and JD
     - Conceptual similarity (e.g., "demand management" matches "resource allocation")
     - Outcome alignment (cost reduction, efficiency improvement)
     - Stakeholder level matching (C-suite, executive engagement)

2. **Experience Selection Strategy**
   - **Key Achievements**: Select 4-5 highest JD relevance + 2-3 career moments (6-8 total)
   - **Professional Experience**: Select different experiences per employer for variety
   - **Cross-Database Optimization**: Pure relevance over employer constraints
   - **Complete deduplication verification**: No experience repeats between sections

3. **Selection Documentation**
   Create experience selection matrix showing:
   - Selected exp_id for each bullet position
   - Relevance score and rationale
   - Employer distribution verification
   - Deduplication confirmation

### Completion Criteria
- [ ] Semantic matching completed against all JD requirements
- [ ] Experience selection matrix completed with full deduplication
- [ ] Selected experiences span all major JD competencies
- [ ] No experience appears in multiple sections

---

## Stage 3: Content Creation

### Objective
Create complete CV content using verified data and selections with proper formatting.

### Process
1. **Content Assembly**
   - Use exact employment data from Stage 1
   - Use selected experiences from Stage 2
   - Apply proper formatting (bold openings, spacing, headers)
   - Remove all exp_id references from final content

2. **CV Section Creation**
   - **Header**: Standard format with target role title
   - **Professional Summary**: Synthesized from top-scoring themes
   - **Key Achievements**: Hybrid approach (single unified section without sub-titles)
   - **Professional Experience**: Employer-grouped with selected experiences
   - **Certifications**: From personal profile database
   - **Technical Competencies**: Dynamically generated from selected experiences
   - **Referees**: Standard line

3. **Format-Specific Application**
   - **Full CV**: 2-line comprehensive storytelling format
   - **Brief CV**: 10-20 word ultra-concise format with outcome-first structure
   - Both formats use identical bullet allocation and selection

4. **File Management**
   - Apply automatic versioning (detect highest version and increment)
   - Clean up old versions (keep current + 2 previous versions only)
   - Generate both .md and .docx formats

### Completion Criteria
- [ ] Complete, professionally formatted CV created
- [ ] Proper versioning and cleanup applied
- [ ] All content traces to verified database sources
- [ ] Format-specific presentation applied correctly

---

## Stage 4: Final Verification

### Objective
Comprehensive verification against all sources with zero tolerance for discrepancies.

### Process
1. **Data Integrity Verification**
   - Verify employment data against Stage 1 outputs
   - Use Task tool to verify all bullets against databases
   - Confirm database integrity (no merging, exact metrics)
   - Check that each bullet traces to single exp_id

2. **Format and Standards Verification**
   - Australian English compliance (optimise, centre, analyse)
   - Sentence case formatting maintained
   - Professional formatting standards applied
   - Bullet spacing and structure correct

3. **Job Description Coverage Verification**
   - Confirm all major JD requirements addressed
   - Verify semantic relevance against original analysis
   - Check keyword integration and ATS optimization
   - Validate competitive positioning

4. **Quality Assurance Checklist**
   - [ ] Each bullet traces to single exp_id with exact metrics
   - [ ] No experience merging or metric combination
   - [ ] No repetition between Key Achievements and Professional Experience
   - [ ] Australian English and sentence case maintained
   - [ ] Database integrity preserved throughout process
   - [ ] JD requirements coverage validated

### Completion Criteria
- [ ] Zero discrepancies found in verification checks
- [ ] All quality assurance criteria met
- [ ] CV ready for final delivery and application submission

---

## Error Prevention

### Common Errors to Avoid
- ❌ Assuming role titles without reading database
- ❌ Guessing employment dates or company names
- ❌ Using "Present" without verifying end_date is null
- ❌ Merging experiences from different exp_ids
- ❌ Creating new metrics or calculations
- ❌ Skipping database file reading or verification
- ❌ Combining stages or shortcuts in the process

### Success Indicators
- ✅ All data traced directly to source database files
- ✅ Complete verification checklists for each stage
- ✅ No assumptions, guesswork, or data interpretation
- ✅ Systematic stage-by-stage progression with verification

## Integration Points

### Jobs Agent Workflow
1. Email notification processing identifies opportunity
2. Role analysis determines database query strategy  
3. Automated CV generation using this 4-stage workflow
4. Quality assurance and format conversion
5. Application package ready for submission

### Command Integration
- Entry via `create_cv_from_databases` command
- Stage-specific continuation commands available
- Verification checkpoints at each stage transition
- Multi-agent orchestration support for complex applications