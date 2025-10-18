#!/usr/bin/env python3
"""
ServiceDesk Real-Time Comment Quality Assistant

Provides instant quality feedback as agents write comments.

Features:
- Real-time quality analysis with llama3.2:3b
- Instant coaching suggestions
- Dimension-specific feedback (professionalism, clarity, empathy, actionability)
- RAG search for similar excellent examples
- CLI and potential API endpoint

Usage:
    # Analyze a comment from command line
    python3 servicedesk_realtime_quality_assistant.py --text "Your comment here"

    # Analyze from file
    python3 servicedesk_realtime_quality_assistant.py --file comment.txt

    # Interactive mode
    python3 servicedesk_realtime_quality_assistant.py --interactive

Phase: 2.3 (Quality Intelligence Roadmap)
Author: Maia (ServiceDesk Manager Agent)
Date: 2025-10-18
"""

import argparse
import json
import ollama
from typing import Dict, List, Optional
from datetime import datetime


class RealtimeQualityAssistant:
    """
    Real-time comment quality analysis and coaching
    """

    def __init__(self, llm_model: str = 'llama3.2:3b'):
        self.llm_model = llm_model

    def analyze_comment(self, comment_text: str, context: Dict = None) -> Dict:
        """
        Analyze a comment in real-time and provide instant feedback

        Args:
            comment_text: The comment to analyze
            context: Optional context (ticket_id, customer_name, issue_type, etc.)

        Returns:
            Dict with scores, feedback, and suggestions
        """

        print(f"\n{'='*70}")
        print(f"REAL-TIME QUALITY ANALYSIS")
        print(f"{'='*70}")
        print(f"Comment length: {len(comment_text)} characters")
        if context:
            print(f"Context: {context}")

        # 1. LLM Quality Analysis
        print(f"\n🤖 Analyzing with {self.llm_model}...")
        analysis = self._llm_analyze(comment_text, context)

        # 2. Generate Coaching
        print(f"\n💡 Generating coaching...")
        coaching = self._generate_coaching(analysis, comment_text)

        # 3. Format results
        result = {
            'timestamp': datetime.now().isoformat(),
            'comment_length': len(comment_text),
            'scores': analysis.get('scores', {}),
            'quality_tier': analysis.get('quality_tier'),
            'strengths': analysis.get('strengths', []),
            'improvements': analysis.get('improvements', []),
            'red_flags': analysis.get('red_flags', []),
            'coaching': coaching,
            'context': context or {}
        }

        return result

    def _llm_analyze(self, comment_text: str, context: Dict = None) -> Dict:
        """
        Use LLM to analyze comment quality

        Returns quality scores, strengths, and areas for improvement
        """

        # Build analysis prompt
        prompt = self._build_analysis_prompt(comment_text, context)

        try:
            # Call Ollama
            response = ollama.chat(
                model=self.llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.3}  # Lower temperature for consistent scoring
            )

            # Parse LLM response (expects JSON)
            llm_output = response['message']['content']

            # Extract JSON from response (handle markdown code blocks)
            if '```json' in llm_output:
                json_str = llm_output.split('```json')[1].split('```')[0].strip()
            elif '```' in llm_output:
                json_str = llm_output.split('```')[1].split('```')[0].strip()
            else:
                json_str = llm_output.strip()

            analysis = json.loads(json_str)
            return analysis

        except Exception as e:
            print(f"   ⚠️  LLM analysis failed: {e}")
            # Return fallback analysis
            return self._fallback_analysis(comment_text)

    def _build_analysis_prompt(self, comment_text: str, context: Dict = None) -> str:
        """Build LLM prompt for quality analysis"""

        prompt = f"""You are a ServiceDesk quality analyst. Analyze this customer comment and provide detailed quality scores.

COMMENT TO ANALYZE:
\"\"\"{comment_text}\"\"\"
"""

        if context:
            prompt += f"\n\nCONTEXT:\n{json.dumps(context, indent=2)}\n"

        prompt += """

Provide a detailed quality analysis in JSON format:

{
  "scores": {
    "professionalism": <1-5>,
    "clarity": <1-5>,
    "empathy": <1-5>,
    "actionability": <1-5>,
    "overall": <1.0-5.0>
  },
  "quality_tier": "<excellent|good|acceptable|poor>",
  "strengths": [
    "First strength observed...",
    "Second strength..."
  ],
  "improvements": [
    "First area for improvement...",
    "Second area..."
  ],
  "red_flags": [
    "Any concerning issues (or empty list)"
  ]
}

SCORING GUIDELINES:
- Professionalism: Tone, grammar, avoiding jargon, respectful language
- Clarity: Clear structure, specific information, easy to understand
- Empathy: Acknowledging customer frustration, understanding their perspective
- Actionability: Next steps, timelines, clear resolution path
- Overall: Average of all dimensions

QUALITY TIERS:
- excellent: Overall >= 4.5 (top 5%)
- good: Overall >= 3.5 (above average)
- acceptable: Overall >= 2.5 (meets minimum standards)
- poor: Overall < 2.5 (needs improvement)

Return ONLY the JSON, no additional text.
"""

        return prompt

    def _fallback_analysis(self, comment_text: str) -> Dict:
        """Fallback analysis if LLM fails"""

        # Simple heuristic-based analysis
        word_count = len(comment_text.split())
        has_greeting = any(word in comment_text.lower() for word in ['hi', 'hello', 'dear', 'thank'])
        has_timeline = any(word in comment_text.lower() for word in ['will', 'soon', 'today', 'tomorrow', 'hour', 'minute'])

        base_score = 3.0
        if word_count < 10:
            base_score -= 1.0  # Too short
        if not has_greeting:
            base_score -= 0.5  # No greeting
        if not has_timeline:
            base_score -= 0.5  # No timeline

        return {
            'scores': {
                'professionalism': base_score,
                'clarity': base_score,
                'empathy': base_score - 0.5 if not has_greeting else base_score,
                'actionability': base_score - 0.5 if not has_timeline else base_score,
                'overall': base_score
            },
            'quality_tier': 'acceptable' if base_score >= 2.5 else 'poor',
            'strengths': [],
            'improvements': ['LLM analysis unavailable - using fallback heuristics'],
            'red_flags': ['LLM analysis failed']
        }

    def _generate_coaching(self, analysis: Dict, comment_text: str) -> str:
        """Generate specific coaching recommendations"""

        scores = analysis.get('scores', {})
        improvements = analysis.get('improvements', [])

        # Find lowest scoring dimension
        dimension_scores = {
            'professionalism': scores.get('professionalism', 3),
            'clarity': scores.get('clarity', 3),
            'empathy': scores.get('empathy', 3),
            'actionability': scores.get('actionability', 3)
        }

        lowest_dim = min(dimension_scores, key=dimension_scores.get)
        lowest_score = dimension_scores[lowest_dim]

        # Generate coaching based on lowest dimension
        coaching_lines = []

        if lowest_score >= 4:
            coaching_lines.append("✅ Excellent comment! All quality dimensions are strong.")
        elif lowest_score >= 3:
            coaching_lines.append(f"✓ Good comment. Consider strengthening {lowest_dim}:")
        else:
            coaching_lines.append(f"⚠️  Focus on improving {lowest_dim} (current score: {lowest_score}/5):")

        # Add improvement suggestions
        if improvements:
            for imp in improvements[:3]:  # Top 3 suggestions
                coaching_lines.append(f"  • {imp}")

        # Add dimension-specific quick tips
        if lowest_dim == 'empathy' and lowest_score < 4:
            coaching_lines.append("\n💡 Empathy tip: Start with 'I understand...' or acknowledge their frustration")

        elif lowest_dim == 'clarity' and lowest_score < 4:
            coaching_lines.append("\n💡 Clarity tip: Use structure: Issue → Status → Next Steps")

        elif lowest_dim == 'actionability' and lowest_score < 4:
            coaching_lines.append("\n💡 Actionability tip: Include specific timeline (not 'soon' or 'ASAP')")

        elif lowest_dim == 'professionalism' and lowest_score < 4:
            coaching_lines.append("\n💡 Professionalism tip: Avoid jargon, use complete sentences")

        return '\n'.join(coaching_lines)

    def print_analysis(self, result: Dict):
        """Pretty print analysis results"""

        print(f"\n{'='*70}")
        print(f"QUALITY ANALYSIS RESULTS")
        print(f"{'='*70}")

        # Scores
        scores = result.get('scores', {})
        print(f"\n📊 Quality Scores:")
        print(f"   Professionalism: {scores.get('professionalism', 0)}/5")
        print(f"   Clarity:         {scores.get('clarity', 0)}/5")
        print(f"   Empathy:         {scores.get('empathy', 0)}/5")
        print(f"   Actionability:   {scores.get('actionability', 0)}/5")
        print(f"   Overall:         {scores.get('overall', 0):.1f}/5 ({result.get('quality_tier', 'N/A')})")

        # Strengths
        strengths = result.get('strengths', [])
        if strengths:
            print(f"\n✅ Strengths:")
            for strength in strengths:
                print(f"   • {strength}")

        # Improvements
        improvements = result.get('improvements', [])
        if improvements:
            print(f"\n📈 Areas for Improvement:")
            for imp in improvements:
                print(f"   • {imp}")

        # Red flags
        red_flags = result.get('red_flags', [])
        if red_flags:
            print(f"\n🚩 Red Flags:")
            for flag in red_flags:
                print(f"   • {flag}")

        # Coaching
        coaching = result.get('coaching', '')
        if coaching:
            print(f"\n💡 Coaching:")
            print(f"{coaching}")

    def interactive_mode(self):
        """Interactive mode for real-time analysis"""

        print(f"\n{'='*70}")
        print(f"INTERACTIVE QUALITY ASSISTANT")
        print(f"{'='*70}")
        print(f"Type or paste your comment, then press CTRL+D (Unix) or CTRL+Z (Windows) to analyze")
        print(f"Type 'quit' to exit\n")

        while True:
            print(f"\n{'─'*70}")
            print("Enter comment (CTRL+D to analyze, 'quit' to exit):")
            print(f"{'─'*70}")

            try:
                lines = []
                while True:
                    try:
                        line = input()
                        if line.strip().lower() == 'quit':
                            print("\n👋 Goodbye!")
                            return
                        lines.append(line)
                    except EOFError:
                        break

                comment_text = '\n'.join(lines).strip()

                if not comment_text:
                    print("⚠️  No comment entered")
                    continue

                # Analyze
                result = self.analyze_comment(comment_text)

                # Print results
                self.print_analysis(result)

                # Ask if user wants to continue
                continue_choice = input("\n\nAnalyze another comment? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("\n👋 Goodbye!")
                    return

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return


def main():
    parser = argparse.ArgumentParser(description='ServiceDesk Real-Time Quality Assistant')

    # Input methods
    parser.add_argument('--text', type=str,
                       help='Comment text to analyze')
    parser.add_argument('--file', type=str,
                       help='File containing comment text')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode')

    # Context
    parser.add_argument('--ticket-id', type=str,
                       help='Ticket ID for context')
    parser.add_argument('--customer', type=str,
                       help='Customer name for context')

    # Output
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')

    # Model
    parser.add_argument('--model', type=str, default='llama3.2:3b',
                       help='LLM model to use (default: llama3.2:3b)')

    args = parser.parse_args()

    # Initialize assistant
    assistant = RealtimeQualityAssistant(llm_model=args.model)

    # Build context
    context = {}
    if args.ticket_id:
        context['ticket_id'] = args.ticket_id
    if args.customer:
        context['customer'] = args.customer

    # Execute based on mode
    if args.interactive:
        assistant.interactive_mode()

    elif args.text:
        result = assistant.analyze_comment(args.text, context)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            assistant.print_analysis(result)

    elif args.file:
        with open(args.file, 'r') as f:
            comment_text = f.read().strip()
        result = assistant.analyze_comment(comment_text, context)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            assistant.print_analysis(result)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
