# Create CV from Databases Command

## Purpose
Generate professional CVs using integrated career databases with systematic role analysis and experience matching.

## Usage
```
create_cv_from_databases <job_description> [cv_type] [target_role]
```

## Parameters
- `job_description`: Full job posting or role requirements
- `cv_type`: "full" (detailed 2-line bullets) or "brief" (10-20 word bullets)
- `target_role`: Role title for optimization focus

## Process

### Stage 1: Role Analysis
1. **Extract Requirements**: Parse job description for key competencies
2. **Identify Keywords**: ATS optimization and role-specific terminology
3. **Assess Complexity**: Determine senior vs mid-level positioning
4. **Map Role Type**: BRM, Technology, Product, Consulting classification

### Stage 2: Database Querying
1. **Experience Selection**: Query relevant employer databases based on role requirements
   - Zetta: Current role relevance (6 experiences)
   - Telstra: Enterprise scale demonstrations (17 experiences)  
   - OneAdvanced: Technical depth and complexity (27 experiences)
   - Viadex/Halsion: Consulting and foundational experience (12 experiences)

2. **Intelligent Matching**: Score experiences against role requirements
   - Technical competency alignment
   - Industry relevance
   - Seniority level match
   - Quantified outcomes relevance

3. **Testimonial Integration**: Select supporting testimonials from feedback database
4. **USP Positioning**: Apply relevant unique selling points

### Stage 3: CV Construction
1. **Apply Methodology**: Use `claude/context/career/cv_methodology.md` framework
2. **Follow Workflow**: Use `claude/context/career/cv_workflow.md` 4-stage process
3. **Apply Standards**: Use `claude/context/career/cv_standards.md` quality frameworks
4. **Technical Competencies**: Generate dynamically from selected experiences

### Stage 4: Quality Assurance
1. **Database Integrity Check**: Verify no experience merging or metric combination
2. **Format Validation**: Ensure DOCX conversion compatibility
3. **ATS Optimization**: Keyword density and structure verification
4. **Professional Standards**: Australian English, sentence case, currency formats

## Output Structure

```markdown
# CV Generation Report

## Role Analysis Summary
**Target Role**: [Position title]
**Key Requirements**: [Top 5 competencies identified]
**Role Classification**: [BRM/Technology/Product/Consulting]
**Seniority Level**: [Senior/Principal/Director]

## Database Query Results
**Experiences Selected**: [Count by employer]
- Zetta: X experiences (current role relevance)
- Telstra: X experiences (enterprise scale)
- OneAdvanced: X experiences (technical depth)
- [Additional selections]

**Matching Score**: [Overall relevance percentage]

## Generated CV
[Complete CV following established format standards]

## Quality Verification
- ✅ Database integrity maintained
- ✅ Australian English compliance
- ✅ DOCX conversion tested
- ✅ ATS optimization complete

## Customization Applied
**Role-Specific Adaptations**: [Key modifications made]
**Keyword Integration**: [ATS terms incorporated]
**Unique Positioning**: [USPs and testimonials used]
```

## Advanced Features

### Intelligent Experience Weighting
- **Role Relevance**: Higher weight for directly applicable experiences
- **Outcome Impact**: Prioritize quantified business outcomes
- **Recency Factor**: Balance current vs historical achievements
- **Competency Coverage**: Ensure comprehensive skill demonstration

### Dynamic Bullet Allocation
- **Senior Roles**: 36 bullets (emphasize leadership and strategy)
- **Technical Roles**: 30 bullets (focus on technical delivery)
- **BRM Roles**: 32 bullets (balance relationship and process outcomes)

### Cross-Database Integration
- **Experience Databases**: Core professional achievements
- **Testimonial Database**: Third-party validation and credibility
- **USP Database**: Competitive differentiation and positioning
- **Personal Profile**: Contact details, certifications, availability

## Integration Points

### Jobs Agent Workflow
1. Email notification processing identifies opportunity
2. Role analysis determines database query strategy
3. Automated CV generation using this command
4. Quality assurance and DOCX conversion
5. Application package ready for submission

### Cross-Agent Support
- **LinkedIn Optimizer**: Uses same database for profile updates
- **Prompt Engineer**: Creates role-specific cover letter templates
- **Security Specialist**: Reviews application for privacy compliance

## Success Metrics

### Efficiency
- **Generation Time**: <15 minutes for complete CV
- **Database Coverage**: 95%+ relevant experience capture
- **Quality Consistency**: 100% format compliance

### Effectiveness
- **ATS Pass Rate**: >90% keyword optimization success
- **Professional Presentation**: Zero formatting errors
- **Role Relevance**: >85% competency alignment with job requirements

This command transforms the manual CV creation process into a systematic, data-driven workflow that consistently produces high-quality, role-optimized applications.