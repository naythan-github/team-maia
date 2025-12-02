#!/usr/bin/env python3
"""
Publish Wintel Engineer JD to Orro Confluence Space

Converts markdown JD to Confluence HTML and publishes to Orro space.

Created: 2025-12-01
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIA_ROOT / 'claude/tools'))

from _reliable_confluence_client import ReliableConfluenceClient
from confluence_html_builder import ConfluencePageBuilder


def convert_jd_to_confluence_html() -> str:
    """
    Convert Wintel Engineer JD markdown to Confluence HTML format

    Returns:
        Confluence storage format HTML string
    """
    builder = ConfluencePageBuilder()

    # Title and header
    builder.add_heading("Wintel Engineer", level=1)
    builder.add_paragraph("Position Description")

    # Position Context
    builder.add_heading("POSITION CONTEXT", level=2)

    # Position Overview
    builder.add_heading("POSITION OVERVIEW", level=2)
    builder.add_raw_html("""
<p>We are looking for a skilled Wintel Engineer with solid experience in Windows Server administration, modern workplace technologies, and cloud automation to join Orro's Microsoft Managed Services team. This client-facing role focuses on implementing Windows infrastructure and modern workspace solutions spanning Azure, Intune, and endpoint management while supporting operations across diverse SMB customer environments.</p>

<p>As a Wintel Engineer, you will be a subject matter expert for Windows platforms and modern desktop deployments, working directly with clients to implement and optimize Windows infrastructure and endpoint solutions. You will lead technical implementations, drive automation initiatives, and provide Tier 3 support for escalated infrastructure and endpoint issues. This position includes on-call responsibilities.</p>
""")

    # Position Responsibilities
    builder.add_heading("POSITION RESPONSIBILITIES", level=2)

    builder.add_heading("Client Engagement & Technical Delivery", level=3)
    builder.add_list([
        "Design, implement, and manage Windows Server environments (2016–2025) including Active Directory, Entra ID, DNS, DHCP, and Group Policy.",
        "Build and support modern workspace platforms like Microsoft Intune, Autopilot, Windows 365, and Endpoint Manager aligned to client requirements.",
        "Work directly with clients on Windows infrastructure implementations and modern desktop deployments."
    ])

    builder.add_heading("Infrastructure & Operations Management", level=3)
    builder.add_list([
        "Manage Azure virtual machines, hybrid networks, and storage environments across customer deployments.",
        "Implement and maintain Windows Server infrastructure and Azure IaaS/PaaS solutions.",
        "Lead Tier 3 support and root cause analysis for escalated Windows infrastructure and endpoint incidents."
    ])

    builder.add_heading("Security & Compliance", level=3)
    builder.add_list([
        "Drive Zero Trust security models and enforce endpoint protection policies using Microsoft Defender for Endpoint.",
        "Collaborate with security and compliance teams to ensure configurations meet audit and governance standards.",
        "Implement client security requirements and support compliance activities."
    ])

    builder.add_heading("Automation & Optimization", level=3)
    builder.add_list([
        "Automate provisioning, patching, and compliance tasks using PowerShell, Azure Automation, and Logic Apps.",
        "Develop automation scripts and deployment frameworks to improve efficiency and standardization.",
        "Maintain system availability and performance through proactive monitoring and capacity planning."
    ])

    builder.add_heading("Mentorship & Collaboration", level=3)
    builder.add_list([
        "Be the subject matter expert for Wintel platforms and modern workspace technologies.",
        "Contribute to internal knowledge bases, documentation, and best practices.",
        "Collaborate with team members on service delivery and capability building."
    ])

    # Skills, Knowledge & Experience
    builder.add_heading("SKILLS, KNOWLEDGE & EXPERIENCE", level=2)
    builder.add_list([
        "5+ years of hands-on experience in Windows Server administration and infrastructure management.",
        "3+ years working with Microsoft Modern Workspace technologies (Intune, Autopilot, Windows 365, Endpoint Manager).",
        "Strong skills in Azure IaaS/PaaS, Entra ID, PowerShell, and automation tooling (Azure Automation, Logic Apps).",
        "Knowledge of SCCM, Microsoft Defender for Endpoint, and co-management environments.",
        "Solid understanding of networking, security, identity principles, and Zero Trust frameworks.",
        "Experience working in MSP or consulting environments with multi-tenant operations.",
        "Excellent communication, problem-solving, and collaboration skills in client-facing contexts."
    ])

    # Qualifications
    builder.add_heading("QUALIFICATIONS", level=2)
    builder.add_list([
        "Bachelor's degree in Computer Science, Information Technology, or equivalent experience.",
        "5+ years of experience in Windows infrastructure engineering, endpoint management, and cloud integration.",
        "Microsoft certifications (AZ-104 Azure Administrator, MD-102 Endpoint Administrator, MS-102 Microsoft 365 Administrator) highly regarded.",
        "Experience with DevOps, Infrastructure as Code (IaC), ITIL frameworks, or Agile methodologies a plus."
    ])

    # Footer
    builder.add_horizontal_rule()
    builder.add_raw_html("""
<p><em>Published: 2025-12-01<br/>
Document Type: Position Description<br/>
Team: Microsoft Managed Services</em></p>
""")

    return builder.build()


def main():
    print("="*80)
    print("Publishing Wintel Engineer JD to Orro Confluence Space")
    print("="*80)
    print()

    # Initialize Confluence client
    client = ReliableConfluenceClient()

    # Run health check
    print("🏥 Running health check...")
    health_status = client.health_check()
    print(f"   Status: {health_status['status']}")
    print(f"   Success Rate: {health_status['metrics']['success_rate']}")
    print()

    # Convert JD to HTML
    print("📝 Converting JD to Confluence HTML...")
    jd_html = convert_jd_to_confluence_html()
    print("   ✅ Conversion complete")
    print()

    # Create page in Orro space
    space_key = "Orro"
    title = "Wintel Engineer - Position Description"

    print(f"📤 Publishing to Confluence...")
    print(f"   Space: {space_key}")
    print(f"   Title: {title}")
    print()

    try:
        result = client.create_page(
            space_key=space_key,
            title=title,
            content=jd_html
        )

        if result:
            print("="*80)
            print("✅ SUCCESS - Position Description Published to Confluence")
            print("="*80)
            print()
            print(f"Space: {space_key}")
            print(f"Title: {title}")
            print(f"Page ID: {result.get('id', 'Unknown')}")
            print()
            print("📊 View page in Confluence Orro space")
            print()
            return 0
        else:
            print("❌ Failed to create page (no result returned)")
            return 1

    except Exception as e:
        print(f"❌ Error creating page: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
