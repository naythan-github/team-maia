# Prompt Templates Command

## Purpose
Generate reusable, high-quality prompt templates for common use cases with clear customization points.

## Usage
```
prompt_templates <use_case> [domain] [complexity_level]
```

## Template Categories

### Business Templates
- **Strategic Analysis**: Market research, competitive analysis, business planning
- **Executive Communication**: Reports, presentations, stakeholder updates
- **Process Optimization**: Workflow analysis, efficiency improvements
- **Client Management**: Relationship building, needs assessment, solution design

### Technical Templates
- **Code Review**: Quality assessment, optimization suggestions, security analysis
- **System Design**: Architecture planning, technical specifications, integration design
- **Troubleshooting**: Problem diagnosis, solution development, testing protocols
- **Documentation**: Technical writing, API documentation, user guides

### Creative Templates
- **Content Creation**: Marketing copy, blog posts, social media, newsletters
- **Ideation**: Brainstorming, creative problem solving, innovation workshops
- **Storytelling**: Narrative development, brand messaging, case studies

## Template Structure

### Standard Format
```markdown
# [Template Name]

## Purpose
[Clear description of what this template achieves]

## Use Cases
- [Specific scenario 1]
- [Specific scenario 2]
- [Specific scenario 3]

## Template

### Context Section
[DOMAIN]: {Insert domain/industry context}
[BACKGROUND]: {Insert relevant background information}
[CONSTRAINTS]: {Insert any limitations or requirements}

### Task Section
[ROLE]: You are an expert {role_type} with deep experience in {domain}.
[OBJECTIVE]: {Clear statement of desired outcome}
[DELIVERABLES]: {Specific output requirements}

### Process Section
[APPROACH]: {Methodology to follow}
[STEPS]: 
1. {Step 1 with specific actions}
2. {Step 2 with specific actions}
3. {Step 3 with specific actions}

### Output Section
[FORMAT]: {Structure requirements}
[STYLE]: {Tone and communication style}
[LENGTH]: {Approximate word count or scope}

## Customization Points
- **{Variable1}**: [Description and examples]
- **{Variable2}**: [Description and examples]
- **{Variable3}**: [Description and examples]

## Example Usage
[Filled-in example showing the template in action]

## Variations
- **Simplified Version**: [For basic use cases]
- **Advanced Version**: [For complex scenarios]
- **Domain-Specific**: [Tailored for specific industries]
```

## Output Format

```markdown
# Prompt Template Generation

## Request Analysis
**Use Case**: [Identified use case]
**Domain**: [Relevant domain or industry]
**Complexity**: [Basic/Intermediate/Advanced]
**Primary Goal**: [Main objective]

## Generated Templates

### Template 1: [Name]
[Full template following standard structure]

### Template 2: [Name] (Variation)
[Alternative approach or specialized version]

## Implementation Guide

### Setup Instructions
1. [How to customize the template]
2. [Required information to gather]
3. [Variables to define]

### Usage Examples
- **Scenario A**: [Example with filled variables]
- **Scenario B**: [Different context example]
- **Scenario C**: [Edge case or advanced usage]

### Optimization Tips
- [How to improve results]
- [Common pitfalls to avoid]
- [When to modify the template]

## Template Library Integration
**Category**: [Where this fits in the library]
**Tags**: [Keywords for searchability]
**Related Templates**: [Cross-references to similar templates]
**Update Schedule**: [When to review and refresh]
```

## Quality Standards

### Template Requirements
- **Clarity**: Unambiguous instructions and expectations
- **Flexibility**: Easy to adapt for different contexts
- **Completeness**: All necessary components included
- **Efficiency**: Optimal token usage for maximum impact

### Customization Guidelines
- Use clear variable naming conventions
- Provide specific examples for each variable
- Include guidance on when to modify vs. use as-is
- Offer both basic and advanced variations

### Documentation Standards
- Explain the rationale behind template design
- Include real-world usage examples
- Provide troubleshooting guidance
- Maintain version history for improvements

## Advanced Features

### Meta-Templates
- Templates that generate other templates
- Systematic approach to template creation
- Automated customization based on parameters

### Conditional Logic
- Templates that adapt based on input variables
- Dynamic sections that appear/disappear as needed
- Smart defaults that reduce customization effort

### Template Chaining
- Linking templates for complex multi-stage workflows
- Maintaining context across template sequences
- Optimized handoffs between template stages