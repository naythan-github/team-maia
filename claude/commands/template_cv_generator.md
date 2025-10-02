# Template CV Generator Command

## Purpose
Advanced CV creation using hypothesis-driven templates with systematic performance tracking and optimization.

## Usage
```
template_cv_generator <job_file> [options]
```

## Quick Start Examples
```bash
# Auto-detect template and generate CV
template_cv_generator ./pwc_brm_job.txt

# Use specific template
template_cv_generator ./azure_architect_job.txt --template=technical_brm_hybrid

# Generate with tracking
template_cv_generator ./job.txt --track-application --company="PwC" 
```

## Parameters
- `job_file`: Path to job description file
- `--template`: Override auto-detection with specific template
- `--track-application`: Track this application for performance analysis
- `--company`: Company name for tracking (required with --track-application)
- `--cv-type`: "full" (default) or "brief" format
- `--output-modes`: "all" (default), "styled", "ats", "readable"
- `--analyze-performance`: Show template performance analysis

## Available Templates

### 1. BRM Stakeholder Focused
**Hypothesis**: BRM roles prioritize stakeholder outcomes over technical depth
- **Bullet Allocation**: 8 key achievements, 24 professional experience
- **Emphasis**: Stakeholder management (1.5x), Business outcomes (1.4x)
- **Keywords**: stakeholder, governance, business value, portfolio
- **Best For**: Business Relationship Manager, Account Manager, Client Partner

### 2. Technical BRM Hybrid  
**Hypothesis**: Technical BRM roles need balanced technical and relationship skills
- **Bullet Allocation**: 7 key achievements, 25 professional experience
- **Emphasis**: Technical delivery (1.4x), Stakeholder management (1.3x)
- **Keywords**: azure, cloud, architecture, stakeholder, solution
- **Best For**: Technical BRM, Solution Manager, Cloud Consultant

### 3. Senior Leadership Focused
**Hypothesis**: Senior roles emphasize strategic outcomes and organizational impact
- **Bullet Allocation**: 9 key achievements, 23 professional experience  
- **Emphasis**: Strategic leadership (1.6x), Business transformation (1.5x)
- **Keywords**: strategy, leadership, transformation, director
- **Best For**: Director, Head of, VP, Principal roles

## Workflow Integration

### Stage 1: Template Intelligence (Automated)
```python
# Job analysis and template recommendation
job_analysis = analyze_job_requirements(job_description)
template_recommendation = detect_optimal_template(job_analysis)

print(f"Recommended: {template_recommendation['template']}")
print(f"Confidence: {template_recommendation['scores']}")
print(f"Reasoning: {template_recommendation['reasoning']}")
```

### Stage 2: Template Application (Semi-Automated)
```python
# Apply template to CV creation process
cv_config = apply_template_configuration(
    template=selected_template,
    job_requirements=job_analysis,
    experience_database=career_databases
)

# Template-specific experience selection
selected_experiences = weight_experiences_by_template(
    experiences=all_experiences,
    template_weights=cv_config.emphasis_weights,
    target_bullets=cv_config.bullet_allocation
)
```

### Stage 3: CV Generation (Using Existing 4-Stage Process)
```python
# Enhanced CV creation with template guidance
cv_content = create_cv_with_template(
    selected_experiences=selected_experiences,
    template_config=cv_config,
    format_type=cv_type
)

# Apply template-specific optimizations
optimized_cv = apply_template_optimizations(
    cv_content=cv_content,
    template=selected_template,
    job_keywords=job_analysis.keywords
)
```

### Stage 4: Performance Tracking (Automated)
```python
# Track application for template performance analysis
if track_application:
    application_id = track_cv_application(
        job_title=job_analysis.title,
        company=company,
        template_used=selected_template.name,
        keyword_matches=cv_optimization.keyword_count
    )
    print(f"Application tracked: {application_id}")
```

## Template Performance Analysis

### Usage
```bash
# View template performance
template_cv_generator --analyze-performance

# Update application outcomes
template_cv_generator --update-application app_20250906_180235 --outcome=interview
```

### Sample Analysis Output
```
📊 Template Performance Analysis (as of 2025-09-06)

Total Applications: 15 across 3 templates

BRM Stakeholder Focused (8 applications):
  ✅ Response Rate: 37.5% (3/8)
  📞 Interview Rate: 25.0% (2/8)  
  🎯 Avg Keywords: 14.2
  ⏱️  Avg Response Time: 8.3 days

Technical BRM Hybrid (5 applications):
  ✅ Response Rate: 60.0% (3/5) 
  📞 Interview Rate: 40.0% (2/5)
  🎯 Avg Keywords: 18.6
  ⏱️  Avg Response Time: 5.8 days

Senior Leadership Focused (2 applications):
  ✅ Response Rate: 50.0% (1/2)
  📞 Interview Rate: 50.0% (1/2)
  🎯 Avg Keywords: 12.0
  ⏱️  Avg Response Time: 12.0 days

🏆 Best Performing: Technical BRM Hybrid
📈 Recommendations:
  - Technical hybrid template shows highest interview conversion
  - Consider emphasizing Azure/cloud keywords more heavily
  - BRM template needs keyword optimization
```

## Advanced Features

### Template Optimization Learning
```python
class TemplateEvolution:
    def analyze_successful_applications(self):
        """Learn from successful applications to optimize templates"""
        
    def suggest_template_improvements(self):
        """Data-driven template enhancement recommendations"""
        
    def create_custom_template(self, successful_patterns):
        """Generate new template based on proven success patterns"""
```

### A/B Testing Framework  
```python
# Test different approaches systematically
ab_test_config = {
    "test_name": "brm_keyword_emphasis", 
    "variant_a": "stakeholder_heavy",
    "variant_b": "outcome_heavy",
    "sample_size": 10,
    "success_metric": "response_rate"
}
```

### Role-Specific Customization
```yaml
pwc_brm_template:
  base_template: "brm_stakeholder_focused"
  customizations:
    keyword_boost: ["consulting", "advisory", "methodology"]
    emphasis_adjustment:
      consulting_experience: 1.3
      client_advisory: 1.4
    bullet_reallocation:
      consulting_bullets: +2
      internal_operations: -2
```

## Output Structure

```markdown
# Template CV Generation Report

## Template Application Summary
**Selected Template**: Technical BRM Hybrid
**Confidence Score**: 85% (Azure keywords: 8, Stakeholder terms: 5)
**Hypothesis**: Technical BRM roles need balanced technical/relationship skills

## Experience Selection Results
**Total Experiences**: 28 selected from 62 available
**Template Weighting Applied**:
- Technical delivery: 1.4x weight (12 experiences)
- Stakeholder management: 1.3x weight (8 experiences)  
- Architecture: 1.3x weight (5 experiences)
- Business outcomes: 1.2x weight (3 experiences)

**Bullet Allocation**: 7 key achievements, 25 professional experience

## CV Generation Output
- ✅ CV_Naythan_Dawe_Senior_Technical_BRM_v13.md
- ✅ CV_Naythan_Dawe_Senior_Technical_BRM_v13_styled.docx
- ✅ CV_Naythan_Dawe_Senior_Technical_BRM_v13_ats.docx
- ✅ CV_Naythan_Dawe_Senior_Technical_BRM_v13_readable.docx

## Performance Tracking
**Application ID**: app_20250906_182045
**Tracking Metrics**:
- Template used: technical_brm_hybrid
- Keyword matches: 18 of 24 job requirements
- Target response rate: >40% (based on template history)
- Expected interview rate: >25%

## Optimization Insights
🎯 **Template Alignment**: 87% match with job requirements
📊 **Historical Performance**: This template averages 60% response rate
🔄 **Continuous Learning**: Data will improve template optimization
```

## Integration Benefits

### Jobs Agent Workflow
1. **Email Processing**: New opportunity identified
2. **Template Intelligence**: `template_cv_generator job.txt --track-application`
3. **Automated Generation**: 3-5 minutes vs 15+ minutes manual
4. **Performance Learning**: Each application improves template optimization

### Success Tracking
- **Response Rate Optimization**: Learn what works in your specific market
- **Template Evolution**: Build evidence-based approaches
- **Competitive Intelligence**: Understand effective positioning strategies
- **ROI Measurement**: Track time investment vs outcome success

This system transforms CV creation from a **manual craft** into a **systematic, learning approach** that improves with each application while maintaining the quality and accuracy of your excellent database foundation.

## Getting Started

1. **Run Initial Setup**: `python3 claude/tools/career/cv_template_system.py`
2. **Generate First CV**: `template_cv_generator your_job.txt --track-application --company="Target Company"`
3. **Update Outcomes**: Track responses and interviews for template learning
4. **Analyze Performance**: After 5-10 applications, review template effectiveness
5. **Optimize**: Adjust templates based on real performance data

The system learns and improves with each application, building your competitive advantage through systematic optimization.