# Generate Presentation Command

## Purpose
Generate professional PowerPoint presentations for BRM, strategic planning, and executive communications using structured data and templates.

## Usage
```bash
# BRM Portfolio Review
maia generate_presentation --type brm_portfolio --data portfolio_q4_2024.json

# Interview Preparation 
maia generate_presentation --type interview_prep --company "PwC Australia" --role "Senior BRM"

# Market Intelligence Report
maia generate_presentation --type market_intelligence --sector "Perth Energy" --focus "BRM Opportunities"

# Strategic Planning Deck
maia generate_presentation --type strategic_planning --project "Digital Transformation" --client "Enterprise Client"

# Custom presentation with data file
maia generate_presentation --type custom --template "executive_brief" --data custom_data.json
```

## Parameters

### Required Parameters
- `--type`: Presentation type (brm_portfolio, interview_prep, market_intelligence, strategic_planning, custom)

### Optional Parameters
- `--data`: JSON file path with presentation data
- `--company`: Company name for company-specific presentations
- `--role`: Role title for interview preparations
- `--sector`: Industry sector for market intelligence
- `--project`: Project name for strategic planning
- `--client`: Client name for client-specific content
- `--template`: Template name for custom presentations
- `--output`: Custom output filename (without extension)

## Presentation Types

### 1. BRM Portfolio Review (`brm_portfolio`)
**Purpose**: Quarterly/annual client portfolio performance reviews
**Data Requirements**:
```json
{
  "quarter": "Q4",
  "year": "2024", 
  "portfolio_value": "3.2M",
  "satisfaction_score": "4.3/5.0",
  "revenue_growth": "+18%",
  "active_projects": "15",
  "success_rate": "96%",
  "key_achievements": [
    "Delivered $500K cost optimization program",
    "Resolved 3 critical client escalations",
    "Expanded portfolio by 25%"
  ],
  "action_items": [
    {
      "action": "Quarterly Business Review with Top 3 Clients",
      "owner": "N. Dawe",
      "timeline": "Next 30 days",
      "status": "Scheduled"
    }
  ]
}
```

### 2. Interview Preparation (`interview_prep`)
**Purpose**: Company intelligence and preparation for job interviews
**Data Requirements**:
```json
{
  "company_name": "PwC Australia",
  "role_title": "Senior Business Relationship Manager",
  "industry": "Professional Services",
  "company_size": "5,000+",
  "revenue": "1.2B",
  "growth_stage": "Stable/Expanding",
  "challenges": "Digital transformation, client experience",
  "recent_news": [
    "Announced new AI advisory practice",
    "Expanded Perth office by 30%"
  ],
  "key_executives": [
    {"name": "Jane Smith", "title": "Managing Partner", "background": "20 years consulting"}
  ]
}
```

### 3. Market Intelligence Report (`market_intelligence`)
**Purpose**: Industry analysis and opportunity assessment
**Data Requirements**:
```json
{
  "sector": "Perth Energy",
  "focus_area": "BRM Opportunities",
  "market_size": "$2.3B",
  "growth_rate": "8% annually",
  "key_players": ["Woodside", "BHP", "Fortescue"],
  "opportunities": [
    "Digital transformation initiatives",
    "ESG reporting and compliance",
    "Supply chain optimization"
  ],
  "competitive_landscape": {
    "established_firms": ["Big 4 consulting"],
    "emerging_players": ["Boutique specialists"],
    "gaps": ["Mid-tier relationship management"]
  }
}
```

### 4. Strategic Planning (`strategic_planning`)  
**Purpose**: Strategic initiative planning and roadmaps
**Data Requirements**:
```json
{
  "project_name": "Digital Transformation Initiative",
  "client_name": "Enterprise Client",
  "timeline": "18 months",
  "budget": "$2.5M",
  "current_state": "Legacy systems, manual processes",
  "future_vision": "Automated, data-driven operations",
  "key_milestones": [
    {"phase": "Assessment", "timeline": "Months 1-3", "deliverables": "Current state analysis"},
    {"phase": "Design", "timeline": "Months 4-8", "deliverables": "Solution architecture"},
    {"phase": "Implementation", "timeline": "Months 9-18", "deliverables": "System deployment"}
  ],
  "success_metrics": [
    {"metric": "Process Efficiency", "target": "+40%"},
    {"metric": "Cost Reduction", "target": "$500K annually"},
    {"metric": "User Satisfaction", "target": "4.5/5.0"}
  ]
}
```

## Command Implementation

```python
#!/usr/bin/env python3
"""
Generate Presentation Command Implementation
Integrates with Maia's presentation generator and data sources
"""

import argparse
import json
import os
import sys
from typing import Dict, Any

# Add tools path
sys.path.append('${MAIA_ROOT}/claude/tools')
from presentation_generator import PresentationGenerator

def load_data_file(filepath: str) -> Dict[str, Any]:
    """Load presentation data from JSON file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_brm_portfolio_presentation(args) -> str:
    """Generate BRM portfolio review presentation"""
    generator = PresentationGenerator()
    
    if args.data:
        data = load_data_file(args.data)
    else:
        # Default data structure
        data = {
            'quarter': 'Q4',
            'year': '2024',
            'portfolio_value': '2.5M',
            'satisfaction_score': '4.2/5.0',
            'revenue_growth': '+15%',
            'active_projects': '12'
        }
    
    return generator.generate_brm_portfolio_review(data)

def generate_interview_prep_presentation(args) -> str:
    """Generate interview preparation presentation"""
    generator = PresentationGenerator()
    
    if args.data:
        data = load_data_file(args.data)
    else:
        # Build from command line args
        data = {
            'company_name': args.company or 'Target Company',
            'role_title': args.role or 'Senior BRM',
            'industry': 'Professional Services',
            'company_size': '5,000+',
            'revenue': '1.2B'
        }
    
    return generator.generate_interview_prep_deck(data)

def generate_market_intelligence_presentation(args) -> str:
    """Generate market intelligence presentation"""
    # TODO: Implement market intelligence generator
    print("Market intelligence presentations coming soon!")
    return ""

def generate_strategic_planning_presentation(args) -> str:
    """Generate strategic planning presentation"""  
    # TODO: Implement strategic planning generator
    print("Strategic planning presentations coming soon!")
    return ""

def main():
    """Main command entry point"""
    parser = argparse.ArgumentParser(description='Generate Professional PowerPoint Presentations')
    
    parser.add_argument('--type', required=True, 
                       choices=['brm_portfolio', 'interview_prep', 'market_intelligence', 'strategic_planning'],
                       help='Type of presentation to generate')
    
    parser.add_argument('--data', help='JSON file path with presentation data')
    parser.add_argument('--company', help='Company name for company-specific presentations')
    parser.add_argument('--role', help='Role title for interview preparations')
    parser.add_argument('--sector', help='Industry sector for market intelligence')
    parser.add_argument('--project', help='Project name for strategic planning')
    parser.add_argument('--client', help='Client name for client-specific content')
    parser.add_argument('--output', help='Custom output filename (without extension)')
    
    args = parser.parse_args()
    
    try:
        if args.type == 'brm_portfolio':
            filepath = generate_brm_portfolio_presentation(args)
        elif args.type == 'interview_prep':
            filepath = generate_interview_prep_presentation(args)
        elif args.type == 'market_intelligence':
            filepath = generate_market_intelligence_presentation(args)
        elif args.type == 'strategic_planning':
            filepath = generate_strategic_planning_presentation(args)
        else:
            raise ValueError(f"Unknown presentation type: {args.type}")
        
        if filepath:
            print(f"✅ Presentation generated successfully: {filepath}")
            
            # Auto-open presentation (optional)
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{filepath}'")
        
    except Exception as e:
        print(f"❌ Error generating presentation: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Integration with Maia Ecosystem

### Data Source Integration
- **Jobs Database**: Pull interview preparation data from job applications
- **Company Research**: Integrate company intelligence from research agent
- **Financial Data**: Include portfolio metrics and financial analysis
- **Experience Database**: Auto-populate achievements and case studies

### Agent Coordination
- **Company Research Agent**: Provide company intelligence for interview prep
- **Jobs Agent**: Supply role requirements and market data
- **Financial Advisor**: Contribute portfolio and performance metrics
- **Personal Assistant**: Schedule presentation reviews and follow-ups

### Template Management
- **Corporate Templates**: Standardized BRM presentation formats
- **Industry-Specific**: Sector-focused layouts and content structures
- **Executive Briefing**: C-suite appropriate design and messaging
- **Client-Specific**: Customized branding and content adaptation

## Output Management

### File Organization
```
claude/data/presentations/
├── brm_portfolio/
│   ├── BRM_Portfolio_Review_20241208_143022.pptx
│   └── templates/
├── interview_prep/
│   ├── Interview_Prep_PwC_Australia_20241208_143045.pptx
│   └── templates/
├── market_intelligence/
└── strategic_planning/
```

### Version Control
- Timestamp-based filenames for version tracking
- Template versioning and update management
- Data source integration tracking
- Presentation history and reuse analytics

## Quality Standards

### Content Quality
- Executive-level messaging and language
- Data-driven insights and recommendations  
- Professional visual design and consistency
- Actionable outcomes and next steps

### Technical Quality
- Corporate color scheme and branding
- Consistent typography and spacing
- Optimized slide layouts for readability
- Cross-platform compatibility (Windows/Mac)

This command transforms business data into executive-ready presentations that drive decision-making and demonstrate professional value.
