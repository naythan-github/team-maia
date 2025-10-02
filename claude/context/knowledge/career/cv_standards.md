# CV Quality Standards & Frameworks

## Bullet Point Framework - Action-Result Method

### Core Structure Pattern
**[Action Verb] + [Specific Context/Scope] + [Method/Process] + [Quantified Outcome]**

### Framework Components

#### 1. Strong Action Verbs (Leadership-Focused)
- **Strategic**: Supported, Directed, Orchestrated, Developed, Designed
- **Execution**: Led, Implemented, Executed, Managed, Delivered
- **Collaboration**: Collaborated, Partnered, Facilitated, Coordinated
- **Impact**: Drove, Secured, Transformed, Reduced, Optimized

#### 2. Specific Context & Scope
- **Stakeholder level**: "C-Suite", "CFO", "senior leadership", "executive team"
- **Scale indicators**: "largest region", "30+ senior leaders", "$400M budget", "enterprise customers"
- **Cross-functional emphasis**: "cross-functional teams", "multiple departments", "national teams"
- **Industry context**: "healthcare client", "financial services", "government sector"

#### 3. Concrete Methods/Processes
- **Specific activities**: "customizing dashboards", "financial forecasting models", "parallel workstreams"
- **Process improvements**: "streamlining operations", "optimizing resource allocation", "automated compliance checks"
- **Strategic approaches**: "proactive stakeholder engagement", "structured customer engagement plan"

#### 4. Quantified Results
- **Financial impact**: Dollar amounts, percentage increases, cost savings, revenue generation
- **Efficiency gains**: Time reductions, process improvements, resource optimization
- **Performance metrics**: NPS improvements, satisfaction increases, error reductions
- **Timeline achievements**: Compressed schedules, early deliveries, accelerated outcomes

## Format Specifications

### Full CV Format (2-Line Bullets)
```
• **Orchestrated enterprise-wide portfolio governance transformation** across 15+ business units, implementing standardized demand intake and prioritisation frameworks that reduced decision-making cycles by 40% while maintaining 95% stakeholder satisfaction through structured executive communication protocols.
```

### Brief CV Format (10-20 Words)
```
• **Reduced decision cycles 40%** through portfolio governance transformation across 15+ business units
```

### Professional Experience Formatting

**Single Role Format:**
```markdown
**Company Name** | Location
**Job Title** | Start Date - End Date
*Company description in italics*

• **Achievement bullets** with bold openings
```

**Multiple Roles Format:**
```markdown
**Company Name** | Location
**First Job Title** | Start Date - End Date
*Company description in italics*

• **Achievement bullets** with bold openings

**Second Job Title** | Start Date - End Date

• **Achievement bullets** with bold openings
```

## Language Standards

### Australian English Requirements
- **Spelling**: optimise (not optimize), centre (not center), analyse (not analyze)
- **Currency**: $AUD format, Australian financial conventions
- **Terminology**: Australian business and government terminology
- **Dates**: DD/MM/YYYY or Month YYYY format

### Sentence Case Formatting
- **Headings**: "Professional summary" not "Professional Summary"
- **Bullet points**: Sentence case throughout
- **Certifications**: Proper case for official certification names only
- **Company names**: Exact case as per official branding

### Professional Writing Standards
- **Bold openings**: Every bullet starts with bold action phrase
- **Natural flow**: No keyword stuffing or awkward phrasing
- **Consistent tense**: Past tense for previous roles, present tense for current role
- **Active voice**: Avoid passive constructions where possible

## Quality Assurance Checklist

### Database Integrity
- [ ] Each bullet traces to single exp_id with exact metrics
- [ ] No experience merging or metric combination
- [ ] No repetition between Key Achievements and Professional Experience sections
- [ ] Exact database metrics only - never create or calculate new figures

### Format Compliance
- [ ] Australian English spelling throughout
- [ ] Sentence case formatting for all headings and bullet points
- [ ] Bold opening fragments for all bullets
- [ ] Proper spacing between sections and bullets
- [ ] Professional employment date formatting (regular dash, not em dash)

### Content Quality
- [ ] Every bullet directly supports JD requirements
- [ ] Natural language flow without keyword stuffing
- [ ] Quantified outcomes with specific metrics
- [ ] Strategic language appropriate for seniority level
- [ ] Industry-appropriate terminology and context

### ATS Optimization
- [ ] Relevant keywords naturally integrated
- [ ] Standard section headers used
- [ ] Clean formatting for parsing systems
- [ ] Contact information in standard format
- [ ] No graphics, tables, or complex formatting that could break parsing

## Conversion Standards

### Markdown to DOCX Requirements
- **Empty lines**: Use for bullet spacing in markdown (prevents inline parsing)
- **Bold formatting**: `**text**` for emphasis, proper regex parsing
- **Contact fields**: Each on separate line with label format `Label: value`
- **Section headers**: Use `##` (H2) format for proper parsing
- **Bullet format**: Use `• ` (bullet + space) consistently

### Output Modes
- **Readable**: Human reviewer optimized (larger fonts, generous spacing)
- **ATS**: Applicant Tracking System optimized (left-aligned, labeled contact info)
- **Styled**: Professional presentation (right-aligned headers, justified text)

### File Management
- **Auto-versioning**: Creates `_v2.docx`, `_v3.docx` etc. to prevent overwriting
- **Version cleanup**: Keep current + 2 previous versions only
- **Format generation**: Both .md and .docx created automatically
- **Folder organization**: Maintain clean separation between originals and outputs

## Semantic Matching Criteria

### High Relevance Indicators
- **Direct terminology overlap**: Between experience `full_context` and JD
- **Conceptual similarity**: "demand management" matches "resource allocation"
- **Outcome alignment**: Cost reduction, efficiency improvement, stakeholder satisfaction
- **Stakeholder level matching**: C-suite, executive engagement, senior leadership

### Keyword Alignment
- **Primary keywords**: From `ats_keywords` appearing in JD
- **Industry sector matches**: Between experience and target role
- **Technical competencies overlap**: Skills and technology alignment
- **Role level indicators**: Senior, principal, director terminology

### Metric Relevance
- **Quantified outcomes**: Matching JD success metrics
- **Scale indicators**: Team sizes, budget amounts, timelines, customer numbers
- **Impact measurements**: Percentages, absolute values, performance improvements
- **Timeline achievements**: Project duration, implementation speed, early delivery

This framework ensures consistent, high-quality CV production that maintains database integrity while optimizing for both human reviewers and ATS systems.