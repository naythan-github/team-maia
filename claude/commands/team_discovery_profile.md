# Team Discovery & Profiling Command

## Purpose
Systematic team member research and profiling for Engineering Manager stakeholder intelligence using existing Maia infrastructure.

## Workflow

### Step 1: Individual Research
**Tool**: `smart_research_manager.py`
**Purpose**: Gather comprehensive professional intelligence on each team member

**Research Areas**:
- LinkedIn profile analysis (background, experience, skills)
- Public professional presence (GitHub, publications, presentations)
- Role history and career progression
- Technical expertise and specializations
- Professional network and connections

### Step 2: Profile Storage
**Tool**: `personal_knowledge_graph.py`
**Purpose**: Store team member profiles with relationship mapping

**Data Structure**:
```json
{
  "name": "Team Member Name",
  "role": "Current Position",
  "experience_level": "Junior/Mid/Senior/Principal",
  "technical_skills": ["skill1", "skill2"],
  "background": "Career summary",
  "working_style_indicators": "Observable patterns",
  "key_relationships": ["internal", "external"],
  "strengths": ["identified strengths"],
  "development_areas": ["potential growth areas"]
}
```

### Step 3: Team Analysis
**Tool**: `strategic_portfolio_analyzer.py`
**Purpose**: Analyze team dynamics, gaps, and optimization opportunities

**Analysis Dimensions**:
- Skill matrix and capability gaps
- Experience distribution and mentoring opportunities
- Communication patterns and collaboration styles
- Workload distribution and capacity analysis
- Succession planning and development pathways

## Usage

### Individual Profile Creation
```bash
# Research individual team member
python3 ${MAIA_ROOT}/claude/tools/smart_research_manager.py research "Full Name + Orro Group" --category "team_member"

# Store in knowledge graph
python3 ${MAIA_ROOT}/claude/tools/personal_knowledge_graph.py add_person [research_results]
```

### Team Analysis
```bash
# Analyze complete team dynamics
python3 ${MAIA_ROOT}/claude/tools/strategic_portfolio_analyzer.py analyze_team
```

## Output Formats

### Individual Profile Summary
- **Professional Background**: Role history and experience
- **Technical Competencies**: Skills matrix and expertise areas
- **Working Style Indicators**: Communication and collaboration patterns
- **Development Opportunities**: Growth areas and career progression paths
- **Strategic Value**: How they contribute to team objectives

### Team Intelligence Dashboard
- **Capability Matrix**: Skills coverage and gaps
- **Experience Distribution**: Junior/Senior balance
- **Collaboration Networks**: Internal relationship mapping
- **Performance Optimization**: Workload and efficiency opportunities
- **Succession Planning**: Development and promotion pathways

## Integration Points

### Morning Briefings
- Weekly team updates and intelligence
- New hiring recommendations based on gaps
- Development opportunity alerts

### Strategic Planning
- Team restructuring recommendations
- Skills development prioritization
- Succession planning updates

### Performance Management
- Data-driven team assessment
- Individual development planning
- Collaboration optimization suggestions

## Privacy & Ethics
- Focus on public professional information only
- Respect privacy boundaries and company policies
- Use intelligence for team development, not surveillance
- Maintain confidentiality of analysis and insights