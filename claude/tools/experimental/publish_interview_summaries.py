#!/usr/bin/env python3
"""
Publish Interview Summaries to Confluence
Creates comprehensive candidate assessment pages in Confluence Orro space
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from confluence_client import ConfluenceClient
from analyze_interview_vtt import parse_vtt, analyze_technical_content

def create_interview_summary_markdown(vtt_file: str, analysis: dict) -> tuple[str, str]:
    """
    Generate comprehensive markdown summary from VTT and analysis

    Returns:
        (title, markdown_content)
    """
    candidate_name = analysis['candidate']
    score = analysis['percentage']

    # Determine hiring recommendation badge
    if score >= 60:
        recommendation = "🟢 **STRONG HIRE** - Proceed to next round"
        status_color = "success"
    elif score >= 40:
        recommendation = "🟡 **MODERATE FIT** - Consider with caveats"
        status_color = "warning"
    else:
        recommendation = "🔴 **WEAK FIT** - Review other candidates"
        status_color = "error"

    # Build markdown
    title = f"Interview Summary: {candidate_name} - Senior Cloud Engineer (Pod Lead)"

    markdown = f"""# Interview Summary: {candidate_name}

**Role**: Senior Cloud Engineer – Pod Lead
**Company**: Orro Group
**Interview Date**: November 2024
**Interviewer**: Naythan Dawe

---

## 📊 Overall Assessment

**Score**: {analysis['total']}/100 ({score}%)
**Recommendation**: {recommendation}

**Verbal Engagement**: {analysis['response_count']} responses during interview

---

## 🎯 Technical Scoring Breakdown

| Category | Score | Details |
|----------|-------|---------|
| **Azure Architecture & Services** | {analysis['scores']['Azure Architecture']}/30 | Cloud infrastructure, PaaS/IaaS, Azure services |
| **IaC & Automation** | {analysis['scores']['IaC & Automation']}/25 | Terraform, Bicep, ARM, CI/CD pipelines |
| **Leadership & Mentorship** | {analysis['scores']['Leadership & Mentorship']}/20 | Team management, training, knowledge transfer |
| **MSP Multi-tenant** | {analysis['scores']['MSP Multi-tenant']}/15 | Multi-client architecture, managed services |
| **Security & Governance** | {analysis['scores']['Security & Governance']}/10 | RBAC, policies, compliance, identity |

---

## ✅ Strengths

"""

    for flag in analysis['green_flags']:
        markdown += f"- {flag}\n"

    if analysis['red_flags']:
        markdown += "\n---\n\n## ⚠️ Concerns\n\n"
        for flag in analysis['red_flags']:
            markdown += f"- {flag}\n"

    markdown += """
---

## 📝 Interview Analysis Methodology

**Data Source**: Video transcript (VTT format) analyzed using keyword extraction and technical depth assessment

**Scoring Framework**:
- **Azure Architecture** (30 pts): Breadth of Azure services discussed, architectural understanding
- **IaC/Automation** (25 pts): Terraform, infrastructure as code, DevOps tooling
- **Leadership** (20 pts): Team management, mentorship, delegation, training
- **MSP Context** (15 pts): Multi-tenant understanding, client management, MSP operations
- **Security** (10 pts): Security-first mindset, governance, compliance awareness

**Limitations**: Automated keyword analysis may not capture nuanced technical depth. Recommend pairing with manual review of full transcript and technical deep-dive in next round.

---

## 🔄 Next Steps

"""

    if score >= 60:
        markdown += """1. ✅ **Progress to Round 2** with technical leadership panel
2. Prepare deep-dive technical scenarios (Terraform, AKS, multi-tenant architecture)
3. Validate leadership style and Pod Lead autonomy expectations
4. Assess MSP culture fit (if from enterprise background)
"""
    elif score >= 40:
        markdown += """1. 🤔 **Hold for comparison** with other candidates
2. Review full transcript for technical depth missed by automated analysis
3. Consider supplementary technical assessment if top-tier candidates unavailable
4. Validate gaps in scoring categories with targeted follow-up questions
"""
    else:
        markdown += """1. ❌ **Do not progress** to next round at this time
2. Review other candidates with stronger technical alignment
3. Consider different role if candidate has other strengths
4. Provide feedback to recruiter on ideal candidate profile
"""

    markdown += f"""
---

**Generated**: Automated interview analysis system
**Analyst**: Technical Recruitment Agent (Maia AI)
**Data Quality**: High confidence (based on {analysis['response_count']} verbal responses)
"""

    return title, markdown

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 publish_interview_summaries.py <vtt_file1> [vtt_file2] ...")
        sys.exit(1)

    # Initialize Confluence client
    client = ConfluenceClient()
    print("✅ Confluence client initialized (VivOEMC/Orro space)\n")

    results = []

    # Analyze each VTT file
    for vtt_file in sys.argv[1:]:
        path = Path(vtt_file)
        if not path.exists():
            print(f"❌ File not found: {vtt_file}")
            continue

        print(f"📄 Processing: {path.name}")

        # Extract candidate name from path
        candidate_name = path.parent.name.replace('_Pod_Lead', '').replace('_Wintel', '').replace('_', ' ')

        # Analyze transcript
        dialogue = parse_vtt(path)
        analysis = analyze_technical_content(dialogue, candidate_name)

        # Generate markdown summary
        title, markdown = create_interview_summary_markdown(vtt_file, analysis)

        # Publish to Confluence
        try:
            print(f"📤 Publishing to Confluence: {title}")
            url = client.create_page_from_markdown(
                space_key="Orro",
                title=title,
                markdown_content=markdown
            )
            print(f"✅ Published: {url}\n")
            results.append({
                'candidate': candidate_name,
                'score': analysis['percentage'],
                'url': url
            })
        except Exception as e:
            print(f"❌ Failed to publish {candidate_name}: {e}\n")

    # Summary
    print("="*80)
    print("CONFLUENCE PUBLICATION SUMMARY")
    print("="*80)

    if results:
        results.sort(key=lambda x: x['score'], reverse=True)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['candidate']} ({result['score']}%) - {result['url']}")
    else:
        print("No pages published")

    print()

if __name__ == '__main__':
    main()
