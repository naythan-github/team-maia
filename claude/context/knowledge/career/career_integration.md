# Career Integration Context

## Purpose
Defines how career management capabilities integrate within Maia's UFC system for optimal job search and application outcomes.

## Data Architecture

### Core Databases
**Location**: `claude/data/career/source-files/`

#### Employer-Specific Experience Databases
- `experiences_zetta.json` - 6 experiences (current role focus)
- `experiences_telstra.json` - 17 experiences (enterprise scale)
- `experiences_oneadvanced.json` - 27 experiences (technical depth)
- `experiences_viadex.json` - 4 experiences (consulting specialization)
- `experiences_halsion.json` - 8 experiences (foundational experience)

#### Supporting Databases
- `personal_profile.json` - Professional identity, certifications, availability
- `feedback_database.json` - 17 testimonials with structured themes
- `usp_database.json` - Core differentiators and positioning statements

### Methodology Framework
**Location**: `claude/context/career/methodology/`
- Complete CV creation process documentation
- Quality assurance frameworks
- Database query strategies
- Australian English and formatting standards

### Tools Integration
**Location**: `claude/tools/career/`
- MD-to-DOCX conversion pipeline
- Validation and testing scripts
- Format verification tools

## Agent Integration Points

### Jobs Agent Enhancement
**Primary Capabilities**:
- Direct access to experience databases for intelligent CV generation
- Automated role analysis → database query → CV customization pipeline
- Integration with email processing for job opportunity analysis

### Cross-Agent Collaboration
- **LinkedIn Optimizer Agent**: Uses experience databases for profile optimization
- **Prompt Engineer Agent**: Creates optimized templates for job applications
- **Security Specialist Agent**: Reviews application security and privacy considerations

## Workflow Integration

### Automated Job Application Pipeline
1. **Discovery**: Email notification processing → opportunity scoring
2. **Analysis**: Role requirements extraction → experience database matching
3. **Generation**: Automated CV creation using proven frameworks
4. **Optimization**: Quality assurance and formatting validation
5. **Delivery**: Application submission with tracking

### Context Loading Strategy
- Load personal profile and preferences as base context
- Query relevant experience databases based on role analysis
- Apply methodology frameworks for consistent quality
- Leverage testimonials and USPs for competitive differentiation

## Data Standards

### Database Integrity Rules
- Each experience entry linked to single `exp_id`
- No metric combination across experiences
- Exact figures only (no estimation or rounding)
- Australian English spelling and currency formats

### Quality Assurance
- Mandatory DOCX conversion testing after format changes
- Systematic validation against established frameworks
- Compliance with professional presentation standards

## Usage Patterns

### Explicit Commands
- `"Create CV for [role] using Maia career data"`
- `"Analyze job opportunities using integrated databases"`
- `"Generate application strategy with full context"`

### Agent Activation
- Jobs Agent automatically accesses career data when processing opportunities
- LinkedIn Optimizer uses experience databases for profile updates
- Prompt Engineer creates career-specific templates and optimizations

## Success Metrics

### Efficiency Gains
- CV generation: 60 minutes → 15 minutes
- Application processing: 3 daily → 10+ daily
- Quality consistency: 100% through systematic frameworks

### Quality Improvements
- Zero formatting errors through automation
- Consistent professional presentation standards
- Data-driven role targeting vs intuitive selection

This integration transforms Maia from a general AI assistant into a comprehensive career advancement system while maintaining the original job-applications repository for comparison and testing.