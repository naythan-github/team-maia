#!/usr/bin/env python3
"""
Interview VTT Analysis Tool
Parses VTT transcript files and scores candidates against role requirements
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

def parse_vtt(file_path):
    """Parse VTT file and extract speaker dialogue"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract speaker lines with <v Speaker>text</v> format
    speaker_pattern = r'<v (.+?)>(.+?)</v>'
    matches = re.findall(speaker_pattern, content, re.DOTALL)

    # Group by speaker
    dialogue = defaultdict(list)
    for speaker, text in matches:
        # Skip interviewer (Naythan)
        if 'Naythan' not in speaker and 'Orro' not in speaker:
            dialogue[speaker].append(text.strip())

    return dialogue

def analyze_technical_content(dialogue, candidate_name):
    """Analyze technical content and score against Senior Cloud Engineer - Pod Lead requirements"""

    # Combine all candidate dialogue
    all_text = ' '.join([' '.join(texts) for texts in dialogue.values()])
    all_text_lower = all_text.lower()

    # Role requirements scoring (from Senior Cloud Engineer - Pod Lead)
    scores = {}

    # Azure Architecture & Services (30 points)
    azure_keywords = ['azure', 'paas', 'virtual machine', 'vm', 'subscription',
                     'resource group', 'vnet', 'networking', 'app service', 'function',
                     'key vault', 'aks', 'container', 'storage', 'landing zone']
    scores['Azure Architecture'] = min(30, sum(2 for kw in azure_keywords if kw in all_text_lower))

    # Infrastructure as Code / Terraform (25 points)
    iac_keywords = ['terraform', 'infrastructure as code', 'iac', 'bicep', 'arm template',
                   'cloudformation', 'module', 'blueprint', 'automation', 'devops',
                   'ci/cd', 'pipeline', 'yaml']
    scores['IaC & Automation'] = min(25, sum(2 for kw in iac_keywords if kw in all_text_lower))

    # Team Leadership & Mentorship (20 points)
    leadership_keywords = ['team', 'lead', 'mentor', 'train', 'teach', 'junior',
                          'manage', 'delegate', 'document', 'knowledge transfer',
                          'coach', 'develop', 'upskill']
    scores['Leadership & Mentorship'] = min(20, sum(2 for kw in leadership_keywords if kw in all_text_lower))

    # MSP / Multi-tenant Architecture (15 points)
    msp_keywords = ['msp', 'managed service', 'multi-tenant', 'client', 'customer',
                   'multi-client', 'shared', 'isolation', 'chargeback', 'sla']
    scores['MSP Multi-tenant'] = min(15, sum(2 for kw in msp_keywords if kw in all_text_lower))

    # Security & Governance (10 points)
    security_keywords = ['security', 'rbac', 'policy', 'governance', 'compliance',
                        'defender', 'sentinel', 'zero trust', 'encryption', 'identity']
    scores['Security & Governance'] = min(10, sum(2 for kw in security_keywords if kw in all_text_lower))

    # Communication quality - count substantive responses
    response_count = sum(len(texts) for texts in dialogue.values())
    avg_response_length = len(all_text) / max(response_count, 1)
    communication_score = min(10, int(avg_response_length / 20))  # Longer responses = better communication

    # Red flags
    red_flags = []
    if 'job' in all_text_lower and 'hop' in all_text_lower:
        red_flags.append("Possible job hopping mentioned")
    if response_count < 20:
        red_flags.append("Limited verbal engagement (<20 responses)")
    if 'certification' not in all_text_lower and 'certified' not in all_text_lower:
        red_flags.append("No certifications mentioned")

    # Green flags
    green_flags = []
    if any(kw in all_text_lower for kw in ['az-305', 'az-104', 'azure architect', 'solution architect', 'aws certified']):
        green_flags.append("Senior cloud certifications (AZ-305/AZ-104/AWS)")
    if 'kubernetes' in all_text_lower or 'aks' in all_text_lower or 'eks' in all_text_lower:
        green_flags.append("Kubernetes/container orchestration experience")
    if 'terraform' in all_text_lower:
        green_flags.append("Terraform expertise")
    if any(kw in all_text_lower for kw in ['led team', 'team lead', 'managed team', 'mentored']):
        green_flags.append("Demonstrated team leadership")
    if response_count > 50:
        green_flags.append("Strong verbal engagement")

    total_score = sum(scores.values())

    return {
        'candidate': candidate_name,
        'scores': scores,
        'total': total_score,
        'max_possible': 100,
        'percentage': round((total_score / 100) * 100, 1),
        'response_count': response_count,
        'red_flags': red_flags,
        'green_flags': green_flags
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_interview_vtt.py <vtt_file1> [vtt_file2] ...")
        sys.exit(1)

    results = []

    for vtt_file in sys.argv[1:]:
        path = Path(vtt_file)
        if not path.exists():
            print(f"❌ File not found: {vtt_file}")
            continue

        # Extract candidate name from path
        candidate_name = path.parent.name.replace('_Pod_Lead', '').replace('_Wintel', '').replace('_', ' ')

        dialogue = parse_vtt(path)
        analysis = analyze_technical_content(dialogue, candidate_name)
        results.append(analysis)

    # Sort by total score
    results.sort(key=lambda x: x['total'], reverse=True)

    # Print results
    print("\n" + "="*80)
    print("INTERVIEW TRANSCRIPT ANALYSIS - SENIOR CLOUD ENGINEER (POD LEAD) ROLE")
    print("="*80 + "\n")

    for i, result in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"RANK #{i}: {result['candidate']}")
        print(f"{'='*80}")
        print(f"\nOVERALL SCORE: {result['total']}/{result['max_possible']} ({result['percentage']}%)")
        print(f"Verbal Engagement: {result['response_count']} responses\n")

        print("TECHNICAL SCORING BREAKDOWN:")
        for category, score in result['scores'].items():
            max_score = {'Azure Architecture': 30, 'IaC & Automation': 25,
                        'Leadership & Mentorship': 20, 'MSP Multi-tenant': 15,
                        'Security & Governance': 10}[category]
            bar = '█' * (score // 2) + '░' * ((max_score - score) // 2)
            print(f"  {category:.<30} {score:>2}/{max_score} {bar}")

        if result['green_flags']:
            print("\n✅ STRENGTHS:")
            for flag in result['green_flags']:
                print(f"  • {flag}")

        if result['red_flags']:
            print("\n⚠️  CONCERNS:")
            for flag in result['red_flags']:
                print(f"  • {flag}")

    print("\n" + "="*80)
    print("HIRING RECOMMENDATION")
    print("="*80 + "\n")

    if results:
        top_candidate = results[0]
        if top_candidate['total'] >= 60:
            recommendation = "STRONG HIRE - Proceed to next round"
        elif top_candidate['total'] >= 40:
            recommendation = "MODERATE FIT - Consider with caveats"
        else:
            recommendation = "WEAK FIT - Review other candidates"

        print(f"Top Candidate: {top_candidate['candidate']}")
        print(f"Score: {top_candidate['percentage']}%")
        print(f"Recommendation: {recommendation}\n")

if __name__ == '__main__':
    main()
