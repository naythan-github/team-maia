#!/usr/bin/env python3
"""
Proper Interview Analysis using Local LLM
Analyzes full VTT transcripts against actual questions asked and Pod Lead framework
Uses local LLM for nuanced understanding of responses
"""

import sys
import json
import subprocess
from pathlib import Path

def parse_vtt_full(file_path):
    """Parse full VTT file and extract Q&A dialogue"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    # Extract all dialogue with timestamps
    pattern = r'<v (.+?)>(.+?)</v>'
    matches = re.findall(pattern, content, re.DOTALL)

    dialogue = []
    for speaker, text in matches:
        dialogue.append({
            'speaker': speaker,
            'text': text.strip()
        })

    return dialogue

def create_analysis_prompt(candidate_name, dialogue, jd_requirements):
    """Create prompt for local LLM to analyze interview"""

    # Combine dialogue into conversation format
    conversation = "\n\n".join([
        f"{d['speaker']}: {d['text']}" for d in dialogue
    ])

    prompt = f"""You are a senior technical recruiter analyzing an interview transcript for a Senior Cloud Engineer - Pod Lead role.

**CANDIDATE**: {candidate_name}

**ROLE REQUIREMENTS (from JD)**:
{jd_requirements}

**SCORING FRAMEWORK** (50 points total, weighted):
Section 1: Leadership Validation (20 points, 50% weight)
- Direct people management experience (reports, performance reviews, hiring authority)
- Pod Lead readiness (autonomy, decision-making)
- Mentorship and team development
- Performance management

Section 2: Career Motivations (10 points, 20% weight)
- Career trajectory and role movement patterns
- Long-term vision and stability
- Motivation for role

Section 3: Technical Validation (10 points, 20% weight)
- Azure architecture depth
- Infrastructure as Code / Terraform
- M365/Endpoint management (Intune, etc.)
- Multi-cloud experience

Section 4: Client Advisory & Innovation (10 points, 10% weight)
- Client pushback and advisory skills
- Service innovation and continuous improvement
- Consultative approach

**INTERVIEW TRANSCRIPT**:
{conversation[:25000]}  # Limit to first 25K chars to fit in context

**TASK**: Analyze this interview transcript and provide:

1. **Questions Asked**: List the main questions the interviewer (Naythan) asked
2. **Section Scoring**: Score each section (1-5 per question, aggregate to section total)
3. **Evidence**: Quote specific responses that support scores
4. **Red Flags**: Any concerns (job hopping, gaps in experience, lack of depth)
5. **Strengths**: Clear demonstrations of capability
6. **Final Score**: Total /50 with weighted calculation
7. **Recommendation**: STRONG HIRE (40-50) | HIRE (35-39) | CONSIDER (30-34) | DO NOT HIRE (<30)

Output format (JSON):
{{
  "questions_asked": ["Question 1", "Question 2", ...],
  "section_1_leadership": {{
    "score": X,
    "max": 20,
    "evidence": "Quoted responses demonstrating leadership..."
  }},
  "section_2_career": {{
    "score": X,
    "max": 10,
    "evidence": "..."
  }},
  "section_3_technical": {{
    "score": X,
    "max": 10,
    "evidence": "..."
  }},
  "section_4_advisory": {{
    "score": X,
    "max": 10,
    "evidence": "..."
  }},
  "red_flags": ["Flag 1", "Flag 2"],
  "strengths": ["Strength 1", "Strength 2"],
  "total_score": X,
  "weighted_score": X,
  "recommendation": "STRONG HIRE|HIRE|CONSIDER|DO NOT HIRE",
  "rationale": "Brief explanation of recommendation..."
}}
"""

    return prompt

def analyze_with_local_llm(prompt, model="llama3.2"):
    """Send prompt to local LLM via Ollama"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=120
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_interview_proper.py <vtt_file>")
        sys.exit(1)

    vtt_file = sys.argv[1]
    path = Path(vtt_file)

    if not path.exists():
        print(f"❌ File not found: {vtt_file}")
        sys.exit(1)

    # Extract candidate name
    candidate_name = path.parent.name.replace('_Pod_Lead', '').replace('_', ' ')

    print(f"\n{'='*80}")
    print(f"ANALYZING: {candidate_name}")
    print(f"{'='*80}\n")

    # Parse VTT
    print("📄 Parsing interview transcript...")
    dialogue = parse_vtt_full(vtt_file)
    print(f"✅ Extracted {len(dialogue)} dialogue segments\n")

    # JD Requirements
    jd_requirements = """
    - 5+ years cloud engineering (Azure primary)
    - Infrastructure as Code (Terraform, Bicep, ARM)
    - Team leadership: 3-5 direct reports, people management (not just mentorship)
    - MSP multi-tenant architecture patterns
    - M365/Intune/Endpoint management
    - Client advisory and consultative selling
    - Service innovation and continuous improvement
    - Pod Lead: 60% hands-on, 40% leadership
    """

    # Create analysis prompt
    prompt = create_analysis_prompt(candidate_name, dialogue, jd_requirements)

    # Analyze with local LLM
    print("🤖 Analyzing with local LLM (llama3.2)...")
    print("   This may take 30-60 seconds...\n")

    analysis = analyze_with_local_llm(prompt)

    print(f"{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}\n")
    print(analysis)

if __name__ == '__main__':
    main()
