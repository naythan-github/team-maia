# Find Perth Restaurants Command

## Overview
Command interface for the Perth Restaurant Discovery Agent - your expert guide to Perth's exceptional dining scene.

## Usage Patterns

### Quick Restaurant Discovery
```
Find me a good Italian restaurant in Fremantle for tonight, party of 4, budget around $50 per person
```

### Occasion-Specific Recommendations  
```
I need a romantic date night restaurant in Perth CBD, modern Australian, willing to spend $100+ per person
```

### Neighborhood Exploration
```
What are the best restaurants in Northbridge? Looking for authentic Asian cuisine, casual dining
```

### Special Requirements
```
Find restaurants in Mount Lawley with excellent vegetarian options, good for business lunch, quiet atmosphere
```

## Command Parameters

### Core Search Parameters
- **Cuisine**: italian, asian, modern_australian, seafood, mediterranean, indian, thai, japanese, french, mexican
- **Location**: perth_cbd, fremantle, northbridge, mount_lawley, subiaco, cottesloe, leeming, applecross, or specific suburbs
- **Budget**: $20-40, $40-70, $70-100, $100+ per person
- **Party Size**: 2, 4, 6, 8+ people
- **Occasion**: date_night, family_dinner, business_lunch, celebration, casual_meal, group_event

### Timing Parameters  
- **When**: tonight, tomorrow, this_weekend, next_week, specific_date
- **Time**: lunch (12-3pm), early_dinner (5:30-7pm), dinner (7-10pm), late_dining (after 10pm)
- **Flexibility**: exact_time, flexible_within_hour, any_available_time

### Dining Preferences
- **Atmosphere**: intimate, lively, quiet, outdoor, waterfront, rooftop, casual, upmarket
- **Special Requirements**: vegetarian_friendly, gluten_free_options, private_dining, large_groups
- **Booking Preference**: walk_in_friendly, reservation_required, online_booking

## Agent Orchestration

### Stage 1: Context Analysis
**Agent**: Perth Restaurant Discovery Agent
**Input**: User request with dining preferences
**Process**: 
- Parse dining requirements and occasion
- Identify Perth location preferences
- Determine budget and party size constraints
**Output**: Structured search parameters

### Stage 2: Restaurant Discovery  
**Agent**: Perth Restaurant Discovery Agent  
**Input**: Search parameters from Stage 1
**Process**:
- Search Perth restaurant database with local expertise
- Check real-time availability and current status
- Gather recent reviews and social media intelligence
- Apply Perth-specific knowledge (parking, transport, neighborhood)
**Output**: Ranked restaurant recommendations with intelligence

### Stage 3: Booking Strategy
**Agent**: Perth Restaurant Discovery Agent
**Input**: Restaurant recommendations
**Process**:
- Analyze availability across preferred dates/times
- Generate booking links and reservation strategies  
- Provide Perth-specific logistics (parking, transport)
- Include pre/post-dining activity suggestions
**Output**: Actionable dining plan with booking guidance

## Enhanced Features

### Perth Local Intelligence
- **Seasonal Awareness**: Perth's dining seasons and outdoor dining opportunities
- **Event Integration**: Restaurant recommendations around Perth events and festivals  
- **Transport Integration**: Public transport routes, parking availability, Uber estimates
- **Weather Consideration**: Outdoor dining based on Perth weather forecasts
- **Cultural Context**: Perth dining customs, booking culture, local favorites

### Real-Time Intelligence
- **Live Availability**: Current table availability across booking platforms
- **Social Media Monitoring**: Instagram/Facebook for current specials and atmosphere
- **Menu Updates**: Seasonal menu changes and chef specials
- **Review Trends**: Recent review analysis and service quality indicators

### Hidden Gem Discovery
- **Emerging Venues**: New restaurants and chef movements
- **Local Secrets**: Neighborhood favorites and insider recommendations  
- **Pop-up Events**: Temporary dining experiences and food festivals
- **Off-Peak Gems**: Great restaurants during typically busy times

## Example Workflows

### Romantic Date Night Discovery
```markdown
**Input**: "Find romantic restaurants in Perth for Saturday night, budget $80-120 per person"

**Stage 1**: Context Analysis
- Occasion: Date night (intimate atmosphere priority)
- Location: Perth metro (flexible within 30 min drive)  
- Budget: Premium ($80-120pp)
- Party: 2 people
- Timing: Saturday evening

**Stage 2**: Restaurant Discovery
- **Top Pick**: Wildflower (Perth CBD) - Modern Australian, stunning views
- **Alternative**: Long Chim (Perth CBD) - Thai, intimate booths
- **Hidden Gem**: Petition Wine Bar (CBD) - Wine-focused, cozy atmosphere

**Output**: Detailed recommendations with booking links, parking tips, and pre-dinner drink suggestions
```

### Family Celebration Planning
```markdown
**Input**: "Need a family-friendly restaurant in Fremantle for 8 people, including kids, celebrating grandpa's 70th"

**Stage 1**: Context Analysis  
- Occasion: Family celebration (accommodating atmosphere)
- Location: Fremantle (specific request)
- Group: 8 people including children
- Special: Birthday celebration (cake/dessert consideration)

**Stage 2**: Restaurant Discovery
- **Family Focus**: Kid-friendly menus and atmosphere
- **Celebration Ready**: Private dining areas or celebration-friendly venues
- **Fremantle Specialists**: Local venues with character and history

**Output**: Family-optimized recommendations with group booking guidance and celebration coordination tips
```

## Integration Points

### Calendar Integration
- Automatically suggests dining for upcoming occasions
- Integrates with Perth event calendar for optimal timing
- Considers work schedules and meeting locations

### Perth Services Integration  
- **Transport**: Transperth routes, parking availability, ride-sharing estimates
- **Weather**: Outdoor dining recommendations based on Perth forecasts
- **Events**: Restaurant suggestions around concerts, AFL games, festivals

### Personal Learning
- Remembers successful restaurant recommendations
- Tracks dining preferences and occasion patterns
- Adapts to Perth neighborhood preferences over time

## Success Metrics

- **Discovery Relevance**: 95%+ recommendations rated as "perfect match" for occasion
- **Booking Success**: 90%+ successful reservations when following booking strategy
- **Perth Authenticity**: 98% recommendations showcase genuine Perth dining culture
- **Hidden Gem Hit Rate**: 40% recommendations are venues user hadn't discovered independently

This command transforms restaurant discovery from generic online searches into expert Perth dining curation with local intelligence and real-time availability.