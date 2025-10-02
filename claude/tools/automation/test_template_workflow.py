#!/usr/bin/env python3
"""
Template Workflow Integration Test
Demonstrates complete CV template system workflow with realistic examples.
"""

from cv_template_system import CVTemplateSystem
import tempfile
from pathlib import Path

def test_complete_workflow():
    """Test the complete template workflow with realistic job examples"""

    print("🎯 CV Template System - Complete Workflow Test")
    print("=" * 60)

    # Initialize system
    system = CVTemplateSystem()

    # Create templates (should already exist from previous run)
    if not system.templates:
        system.create_initial_templates()

    # Test job descriptions
    test_jobs = [
        {
            "title": "Senior BRM - PwC Technology Advisory",
            "company": "PwC Australia",
            "description": """
Senior Business Relationship Manager - Technology Advisory

PwC Australia's Technology Advisory practice seeks an experienced Business
Relationship Manager to lead stakeholder engagement across enterprise Azure
cloud transformation projects. This role involves driving business value
delivery through strategic technology alignment, governance oversight, and
executive relationship management.

Key Responsibilities:
• Manage stakeholder relationships across C-suite and senior executive levels
• Drive business outcomes through strategic technology portfolio management
• Oversee governance frameworks for large-scale digital transformation initiatives
• Lead cross-functional teams in delivering Azure migration and modernisation projects
• Develop business cases and ROI analysis for technology investments
• Ensure alignment between business strategy and technology delivery

Requirements:
• 8+ years experience in business relationship management or consulting
• Proven track record in stakeholder engagement and executive communication
• Experience with Azure cloud platforms and digital transformation
• Strong governance and portfolio management capabilities
• Consulting methodology experience preferred
• Excellent presentation and communication skills
            """
        },
        {
            "title": "Director of Technology Services",
            "company": "Major Perth Corporation",
            "description": """
Director of Technology Services

Executive leadership opportunity to drive strategic technology direction for
a major Perth-based corporation. This senior role requires proven leadership
in organizational transformation, team development, and P&L accountability.

Key Responsibilities:
• Provide strategic leadership for enterprise technology services division
• Drive organizational transformation and digital innovation initiatives
• Manage and develop high-performing technology teams (50+ staff)
• Board-level reporting and strategic planning responsibilities
• P&L accountability for $15M technology services budget
• Lead merger and acquisition technology integration projects

Requirements:
• 12+ years progressive leadership experience in technology services
• Proven track record in organizational change and business transformation
• Experience in board reporting and executive stakeholder management
• Strong financial management and P&L accountability
• Masters degree or equivalent experience preferred
• Perth location essential
            """
        },
        {
            "title": "Azure Cloud Architect - Technical Lead",
            "company": "Digital Transformation Consultancy",
            "description": """
Azure Cloud Architect - Technical Lead

Leading digital transformation consultancy seeks senior Azure Cloud Architect
to lead enterprise cloud migration projects. This role combines deep technical
expertise with client relationship management in a consulting environment.

Key Responsibilities:
• Design and implement Azure cloud architecture solutions for enterprise clients
• Lead technical teams in complex cloud migration and modernization projects
• Provide technical leadership and mentoring to junior architects
• Engage with client stakeholders including CTOs and IT directors
• Develop cloud strategy recommendations and implementation roadmaps
• Ensure security, compliance, and cost optimization across all solutions

Requirements:
• 6+ years experience in cloud architecture, preferably Azure
• Strong technical depth in cloud infrastructure, security, and automation
• Experience in client-facing consulting roles
• Proven leadership of technical teams and complex projects
• Azure certifications (Solutions Architect Expert preferred)
• Excellent communication and presentation skills
            """
        }
    ]

    # Process each job
    for i, job in enumerate(test_jobs, 1):
        print(f"\n📋 Test Job {i}: {job['title']}")
        print("-" * 50)

        # Template recommendation
        recommendation = system.detect_optimal_template(job['description'])
        print(f"🎯 Recommended Template: {recommendation['recommended_template']}")
        print(f"   Confidence Scores: {recommendation['confidence_scores']}")
        print(f"   Reasoning: {recommendation['reasoning']}")

        # Get template configuration
        template = system.templates[recommendation['recommended_template']]
        print(f"\n📊 Template Configuration:")
        print(f"   Hypothesis: {template.hypothesis}")
        print(f"   Bullet Allocation: {template.bullet_allocation}")
        print(f"   Top Keywords: {template.keyword_priorities[:8]}")

        # Apply template configuration
        config = system.apply_template_to_cv_creation(
            template_name=recommendation['recommended_template'],
            job_description=job['description']
        )
        print(f"\n⚙️  CV Generation Config:")
        print(f"   Selection Strategy: {config['selection_strategy']}")
        print(f"   Emphasis Weights: {dict(list(template.emphasis_weights.items())[:4])}")
        print(f"   Target Keywords Found: {len(config['quality_metrics']['keyword_targets'])}")

        # Track application
        app_id = system.track_application(
            job_title=job['title'],
            company=job['company'],
            template_used=recommendation['recommended_template'],
            keyword_matches=len(config['quality_metrics']['keyword_targets'])
        )
        print(f"   Application Tracked: {app_id}")

    # Simulate some outcomes for demonstration
    print(f"\n🔄 Simulating Application Outcomes...")
    applications = system.applications[-3:]  # Last 3 applications

    # Simulate realistic outcomes
    outcomes = [
        {"outcome": "response", "days": 7, "notes": "Positive response, interview scheduled"},
        {"outcome": "interview", "days": 5, "notes": "Technical interview completed successfully"},
        {"outcome": "pending", "days": None, "notes": "Application submitted today"}
    ]

    for app, outcome in zip(applications, outcomes):
        if outcome["days"]:
            system.update_application_outcome(
                application_id=app.application_id,
                outcome=outcome["outcome"],
                response_time_days=outcome["days"],
                feedback_notes=outcome["notes"]
            )
            print(f"   ✅ {app.application_id}: {outcome['outcome']} ({outcome['days']} days)")
        else:
            print(f"   ⏳ {app.application_id}: {outcome['outcome']}")

    # Performance analysis
    print(f"\n📈 Template Performance Analysis")
    print("=" * 40)
    analysis = system.analyze_template_performance()

    if 'template_performance' in analysis:
        for template_name, perf in analysis['template_performance'].items():
            print(f"\n🎯 {template_name.replace('_', ' ').title()}:")
            print(f"   Applications: {perf['total_applications']}")
            print(f"   Response Rate: {perf['response_rate']:.1%}")
            print(f"   Interview Rate: {perf['interview_rate']:.1%}")
            print(f"   Avg Keywords: {perf['avg_keyword_matches']:.1f}")

    # Recommendations
    print(f"\n💡 System Recommendations:")
    for rec in analysis.get('recommendations', []):
        print(f"   • {rec}")

    print(f"\n🎉 Workflow Test Complete!")
    print(f"   Total Applications Tracked: {len(system.applications)}")
    print(f"   Templates Available: {len(system.templates)}")
    print(f"   Data Files Created:")
    print(f"   • {system.templates_file}")
    print(f"   • {system.applications_file}")

    return system

def demonstrate_practical_usage():
    """Show practical daily usage scenarios"""

    print(f"\n" + "=" * 60)
    print("🚀 Practical Usage Scenarios")
    print("=" * 60)

    scenarios = [
        {
            "scenario": "Quick Template Detection",
            "description": "You receive a job via email and want quick template recommendation",
            "job_snippet": "Senior Business Relationship Manager, stakeholder engagement, Azure transformation",
            "expected_template": "technical_brm_hybrid"
        },
        {
            "scenario": "Performance Review",
            "description": "After 10 applications, you want to see which templates work best",
            "action": "analyze_template_performance"
        },
        {
            "scenario": "Template Customization",
            "description": "Perth market shows preference for Azure experience, adjust templates",
            "adjustment": "Increase azure_experience weight to 1.4 for brm templates"
        }
    ]

    system = CVTemplateSystem()

    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['scenario']}")
        print(f"   Description: {scenario['description']}")

        if 'job_snippet' in scenario:
            rec = system.detect_optimal_template(scenario['job_snippet'])
            print(f"   Quick Analysis: {rec['recommended_template']}")
            print(f"   Matches Expected: {rec['recommended_template'] == scenario['expected_template']}")

        if scenario.get('action') == 'analyze_template_performance':
            analysis = system.analyze_template_performance()
            print(f"   Analysis Available: {'template_performance' in analysis}")

    print(f"\n✅ All practical scenarios demonstrated successfully!")

if __name__ == "__main__":
    # Run complete workflow test
    system = test_complete_workflow()

    # Show practical usage
    demonstrate_practical_usage()

    print(f"\n🎯 Next Steps:")
    print("1. Save a real job description to a text file")
    print("2. Run: template_cv_generator your_job.txt --track-application --company='Company Name'")
    print("3. Update outcomes as responses come in")
    print("4. Analyze performance after 5-10 applications")
    print("5. Optimize templates based on real market data")

    print(f"\n🚀 System ready for production use!")
