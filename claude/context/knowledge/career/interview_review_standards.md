# Interview Review Standards

## Purpose
Standardized format for post-interview analysis and documentation in Confluence.

## Template Location
**Python Tool**: `/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/Recruitment/Templates/interview_review_confluence_template.py`

## Standard Format

### 1. Overview Section
- **Duration**: Interview length in minutes
- **Format**: Video/Phone/In-person
- **Interviewer**: Name(s)
- **Role**: Position title
- **Overall Score**: X/75 with percentage
- **Recommendation**: Clear decision (Strong Yes/Yes/Yes with reservations/Maybe/No)

### 2. Scoring Summary Table
| Category | Score | Assessment |
|----------|-------|------------|
| Technical Skills | X/50 | [Summary] |
| People Leadership | X/25 | [Summary] |
| **Total** | **X/75** | **Percentage** |

**Scoring Guides**:

**Technical (out of 50)**:
- 45-50: Exceptional - Exceeds requirements
- 40-44: Strong - Meets all requirements
- 35-39: Good - Meets core requirements
- 30-34: Adequate - Meets minimum requirements
- <30: Below requirements - Gaps identified

**Leadership (out of 25)**:
- 23-25: Exceptional leadership potential
- 20-22: Strong leadership qualities
- 17-19: Good foundation, needs development
- 14-16: Limited leadership evidence
- <14: Insufficient leadership demonstration

### 3. Technical Assessment (Detailed)

**Core Skills Table**:
| Skill Area | Score (1-5) | Evidence |
|------------|-------------|----------|
| [Primary Skill] | X/5 | Bullet points with specific examples |
| [Secondary Skill] | X/5 | Bullet points |
| ... | | |

**Technical Gaps Identified**:
- Gap 1 - Impact: High/Medium/Low - Trainable: Yes/No
- Gap 2 - Impact: High/Medium/Low - Trainable: Yes/No

### 4. People Leadership Assessment

**Leadership Dimensions Table**:
| Dimension | Score (1-5) | Assessment |
|-----------|-------------|------------|
| Self-Awareness | X/5 | Evidence + specific examples |
| Accountability | X/5 | Evidence + specific examples |
| Growth Mindset | X/5 | Evidence + specific examples |
| Team Orientation | X/5 | Evidence + specific examples |
| Communication | X/5 | Evidence + specific examples |

**Leadership Dimensions Explained**:
- **Self-Awareness**: Understands strengths, weaknesses, values, impact on others
- **Accountability**: Owns mistakes, learns from failures, doesn't externalize problems
- **Growth Mindset**: Continuous learning, seeks feedback, embraces challenges
- **Team Orientation**: Collaboration, mentoring, builds others up vs solo hero
- **Communication**: Clear, empathetic, adjusts to audience, professional

### 5. Critical Issues Section (If Applicable)

**Format**:
- **Issue Title** (e.g., "Current Tenure - 6 months")
- **Question Asked**: What was probed
- **Response**: Key quotes from answer
- **Assessment**: Satisfied/Concern/Red Flag
- **Reasoning**: Why this assessment

Use **panel macro** with orange background (#FFF4E5) for tenure/red flag discussions.

### 6. Standout Interview Moments

**Positive Moments** (Green panel #E3FCEF):
1. **Title**: Brief description
   - **Quote**: Verbatim from interview
   - **Why impressive**: Specific reasoning

**Concerning Moments** (Red panel #FFEBE6):
1. **Title**: Brief description
   - **Quote**: Verbatim from interview
   - **Why concerning**: Specific reasoning

**Guideline**: Include 3-5 positive moments, 1-3 concerning moments. Always use direct quotes as evidence.

### 7. Second Interview Questions (If Applicable)

Use **expand macro** titled "Critical Probes for Second Interview"

**Format**:
1. **[Dimension]**: *"Question text in italics"*
2. **[Dimension]**: *"Question text in italics"*

**Focus areas**:
- Accountability probes (if gap identified)
- Decision acceptance (if resistance pattern)
- Performance management (if leadership role)
- Retention (if tenure concerns)

### 8. Interview vs CV Comparison

**Table Format**:
| Metric | CV Score | Interview Score | Variance |
|--------|----------|-----------------|----------|
| Overall | X/100 | X/75 (Y%) | [Indicator] |
| Technical | X/50 | X/50 | ✅/⚠️ |
| Leadership | X/20 | X/25 | ✅/⚠️ |

**Variance Indicators**:
- ✅ Exceeded CV (+5% or more)
- ✅ Confirmed CV (-5% to +5%)
- ⚠️ Below CV (-5% or less)

### 9. Final Recommendation

Use **panel macro** with color based on recommendation:
- **Green** (#E3FCEF): Strong Yes, Yes
- **Orange** (#FFF4E5): Yes with reservations, Maybe
- **Red** (#FFEBE6): No, Pass

**Include**:
- **Recommendation**: Clear statement
- **Rationale**: 2-3 sentences explaining decision
- **Critical Success Factors**: If "Yes with reservations", list 3-4 conditions
- **Next Steps**: Second interview, reference checks, technical assessment, etc.

---

## Confluence Formatting Standards

### Macros Used
- **Info macro**: Overall score summary
- **Warning macro**: Critical concerns section
- **Panel macro**: Colored backgrounds for context
  - Green (#E3FCEF): Positive moments
  - Orange (#FFF4E5): Tenure/concerns discussion
  - Red (#FFEBE6): Concerning moments, rejection
- **Expand macro**: Collapsible sections (second interview questions)

### Typography
- **H1**: Page title only (Candidate name)
- **H2**: Major sections (Technical Assessment, Leadership Assessment, etc.)
- **H3**: Subsections (Core Skills, Technical Gaps, etc.)
- **Bold**: Key terms, dimension names, scores
- **Italic**: Quotes from interview (use with quotation marks)
- **Code**: Not used in interview reviews

### Tables
- Always include header row
- Use **bold** for row/column labels
- Keep cells concise (bullet points for evidence)
- Use X/Y format for scores (e.g., 42/50)

---

## Usage Examples

### Generate Review Programmatically

```python
from interview_review_confluence_template import (
    InterviewReviewTemplate,
    InterviewScore,
    TechnicalSkill,
    LeadershipDimension,
    InterviewMoment
)

template = InterviewReviewTemplate()

scores = InterviewScore(technical=42, leadership=19)

technical_skills = [
    TechnicalSkill(
        name="Intune/Autopilot Expertise",
        score=5,
        evidence=[
            "Maintains personal M365 Business Premium tenant",
            "Has complete baseline configurations ready",
            "Unprompted knowledge of CIPP/Enforcer tools"
        ]
    ),
    # ... more skills
]

leadership_dimensions = [
    LeadershipDimension(
        name="Self-Awareness",
        score=4,
        assessment="Clear about values mismatch, comfortable sharing personal background"
    ),
    # ... more dimensions
]

positive_moments = [
    InterviewMoment(
        title="Personal Lab Investment",
        quote="I ended up paying for my own business premium tenant...",
        why_notable="Demonstrates genuine passion beyond job requirements"
    ),
    # ... more moments
]

page_url = template.generate_review(
    candidate_name="Taylor Barkle",
    role_title="Senior Endpoint Engineer",
    interviewer="Naythan Dawe",
    duration_minutes=53,
    cv_score=82,
    scores=scores,
    technical_skills=technical_skills,
    leadership_dimensions=leadership_dimensions,
    positive_moments=positive_moments,
    concerning_moments=[...],
    technical_gaps=["SCCM depth - primarily cloud-focused"],
    second_interview_questions=[...],
    recommendation="✅ Yes with reservations - Proceed to second interview",
    space_key="Orro"
)

print(f"Review created: {page_url}")
```

### CLI Usage

```bash
python3 interview_review_confluence_template.py \
    --candidate "Taylor Barkle" \
    --role "Senior Endpoint Engineer" \
    --interviewer "Naythan Dawe" \
    --duration 53 \
    --cv-score 82 \
    --technical-score 42 \
    --leadership-score 19 \
    --space-key "Orro"
```

---

## Quality Checklist

Before publishing interview review, verify:

- [ ] Overall score calculated correctly (Technical + Leadership)
- [ ] All scores include evidence with specific examples
- [ ] At least 3 direct quotes included (positive or concerning)
- [ ] Technical gaps list includes impact and trainability assessment
- [ ] Leadership dimensions scored on consistent 1-5 scale
- [ ] Recommendation matches score (e.g., 61/75 shouldn't be "Strong Yes")
- [ ] Second interview questions address identified gaps
- [ ] CV comparison includes variance indicators
- [ ] Critical success factors listed if "with reservations"
- [ ] Page title format: "Interview Analysis - [Name] ([Role])"

---

## Integration with Recruitment Workflow

### Before Interview
1. Review CV analysis (if available)
2. Prepare priority questions based on CV gaps
3. Have template ready for live note-taking

### During Interview
1. Take raw notes on key responses
2. Mark standout moments (positive/concerning)
3. Score technical skills in real-time (1-5)

### After Interview (within 1 hour)
1. Complete leadership dimension scoring
2. Add direct quotes for standout moments
3. Write overall recommendation
4. Generate Confluence page using template
5. Share link with hiring team

### Second Interview (if applicable)
1. Provide second interviewer with first interview analysis
2. Focus second interview on identified gaps
3. Update original page with second interview findings
4. Make final hiring recommendation

---

## Reference Example

**Live Example**: [Taylor Barkle Interview Analysis](https://vivoemc.atlassian.net/wiki/spaces/Orro/pages/3135897602/Interview+Analysis+-+Taylor+Barkle+Senior+Endpoint+Engineer)

This page demonstrates the full template implementation with:
- Complete scoring breakdown
- Direct quotes from 53-minute interview
- Technical and leadership assessments
- Standout moments with context
- Second interview questions
- Final recommendation with success factors

---

**Maintained by**: Maia System
**Last Updated**: 2025-10-13
**Status**: ✅ Active - Standard for all Orro recruitment interviews
