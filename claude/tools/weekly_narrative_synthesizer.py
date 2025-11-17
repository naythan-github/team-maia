#!/usr/bin/env python3
"""
Weekly Narrative Synthesizer for Maia Journey Narratives.

Transforms conversation data into conversational, story-driven weekly narratives
for team sharing. Demonstrates "the art of the possible with Maia."

Usage:
    python3 weekly_narrative_synthesizer.py generate
    python3 weekly_narrative_synthesizer.py generate --output /path/to/file.md
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from conversation_logger import ConversationLogger


class WeeklyNarrativeSynthesizer:
    """Generate conversational weekly narratives from conversation data."""

    def __init__(self):
        self.logger = ConversationLogger()

    def generate_weekly_narrative(self, output_path: Optional[str] = None) -> str:
        """
        Generate weekly narrative from shareable journeys.

        Args:
            output_path: Optional path to save markdown file

        Returns:
            Markdown narrative string
        """
        # Get shareable journeys from last 7 days
        try:
            journeys = self.logger.get_week_journeys(include_private=False)
        except Exception as e:
            # Graceful degradation: Generate error narrative
            import logging
            logging.error(f"Failed to retrieve journeys: {e}")
            journeys = []

        if not journeys:
            narrative = self._generate_empty_week_narrative()
        else:
            # Generate narrative sections
            header = self._generate_header(len(journeys))
            journey_narratives = [self._generate_journey_narrative(j, i+1)
                                 for i, j in enumerate(journeys)]
            stats = self._generate_stats_section(journeys)
            meta_learning = self._generate_meta_learning_section(journeys)
            footer = self._generate_footer()

            # Combine all sections
            narrative = "\n\n".join([
                header,
                *journey_narratives,
                stats,
                meta_learning,
                footer
            ])

        # Save to file if path provided
        if output_path:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(narrative)
            except Exception as e:
                import logging
                logging.error(f"Failed to write narrative to {output_path}: {e}")
                # Re-raise to inform caller
                raise

        return narrative

    def _generate_header(self, journey_count: int) -> str:
        """Generate narrative header."""
        today = datetime.now()
        week_start = today - timedelta(days=7)

        return f"""# 🎨 Discovering What's Possible with Maia
## Week of {week_start.strftime('%b %d')}-{today.strftime('%d, %Y')}

---
"""

    def _generate_journey_narrative(self, journey: Dict, number: int) -> str:
        """
        Generate conversational narrative for a single journey.

        Args:
            journey: Journey data dictionary
            number: Journey number (for title)

        Returns:
            Markdown narrative for journey
        """
        # Extract journey data
        problem = journey.get('problem_description', 'A problem')
        question = journey.get('initial_question', '')
        options = self._parse_json_field(journey.get('maia_options_presented'))
        refinement = journey.get('user_refinement_quote', '')
        agents = self._parse_json_field(journey.get('agents_used', []))
        deliverables = self._parse_json_field(journey.get('deliverables', []))
        impact = journey.get('business_impact', '')
        meta_learning = journey.get('meta_learning', '')

        # Generate title from problem and impact
        title_suffix = self._extract_title_suffix(problem, impact)

        narrative = f"""## 🚀 Journey {number}: {title_suffix}

**The Problem**
{self._make_conversational_problem(problem)}

**Our Conversation Started**
You: "{question}"

{self._format_options(options)}

{self._format_refinement(refinement)}

{self._format_agents(agents)}

{self._format_deliverables(deliverables)}

**The Impact**
{self._make_conversational_impact(impact)}

**💡 What This Shows You Can Do with Maia**
{self._make_generalized_learning(meta_learning, problem)}
"""
        return narrative

    def _generate_empty_week_narrative(self) -> str:
        """Generate narrative for week with no shareable journeys."""
        today = datetime.now()
        return f"""# 🎨 Discovering What's Possible with Maia
## Week of {today.strftime('%b %d, %Y')}

---

## No Shareable Journeys This Week

All work this week was customer-specific or contained sensitive information, so there are no shareable journeys to highlight.

Check back next week for more "art of the possible" examples!

---

_Generated by Maia • Week of {today.strftime('%b %d, %Y')}_
"""

    def _generate_stats_section(self, journeys: List[Dict]) -> str:
        """Generate weekly statistics section."""
        journey_count = len(journeys)

        # Calculate average iterations
        iterations = [j.get('iteration_count', 1) for j in journeys]
        avg_iterations = sum(iterations) / len(iterations) if iterations else 0

        # Count agent handoffs
        agent_counts = {}
        for j in journeys:
            agents = self._parse_json_field(j.get('agents_used', []))
            for agent_data in agents:
                agent_name = agent_data.get('agent', 'Unknown') if isinstance(agent_data, dict) else str(agent_data)
                agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1

        # Format agent breakdown
        agent_breakdown = ", ".join([f"{name}: {count}" for name, count in
                                    sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)])

        return f"""## 📊 This Week's Pattern

**{journey_count} problem-solving journey{"s" if journey_count != 1 else ""}**
**Average refinements: {avg_iterations:.1f} iterations** {"(you didn't accept first solution - good!)" if avg_iterations > 1 else ""}
**Agent handoffs: {sum(agent_counts.values())} total** ({agent_breakdown})

**The Meta-Pattern**
Most journeys started with "how do I do X?" and shifted to "wait, is there a better way?" That second question is where the magic happens.
"""

    def _generate_meta_learning_section(self, journeys: List[Dict]) -> str:
        """Extract and present meta-learning patterns across journeys."""
        # Extract all meta-learning entries
        learnings = [j.get('meta_learning', '') for j in journeys if j.get('meta_learning')]

        if not learnings:
            return """## 🎓 New Ways of Working Discovered This Week

No explicit patterns documented this week, but each journey added to your Maia collaboration toolkit.
"""

        # For now, list unique patterns (future: could cluster similar patterns)
        unique_patterns = list(set(learnings))

        pattern_list = "\n".join([f"**Pattern**: {pattern}" for pattern in unique_patterns])

        # Generate actionable takeaway from first pattern
        takeaway = self._extract_takeaway(unique_patterns[0]) if unique_patterns else "Keep exploring new ways to collaborate with Maia."

        return f"""## 🎓 New Ways of Working Discovered This Week

{pattern_list}

**Try this next time**: {takeaway}
"""

    def _generate_footer(self) -> str:
        """Generate narrative footer."""
        today = datetime.now()
        return f"""---

_Generated by Maia • Week of {today.strftime('%b %d, %Y')}_
"""

    def _extract_title_suffix(self, problem: str, impact: str) -> str:
        """Extract conversational title from problem and impact."""
        # Simple extraction - can be enhanced
        problem_short = problem[:50] + "..." if len(problem) > 50 else problem
        if impact and "%" in impact:
            return f"From \"{problem_short}\" to significant time savings"
        return f"Solving: {problem_short}"

    def _make_conversational_problem(self, problem: str) -> str:
        """Convert problem description to conversational tone."""
        # Add "You had..." framing if not already present
        if problem.lower().startswith("you "):
            return problem
        return f"You had {problem.lower()}. "

    def _format_options(self, options: List) -> str:
        """Format Maia's options in conversational style."""
        if not options:
            return "Maia explored several approaches."

        # Convert to conversational bullets
        formatted = "Maia explored these paths:\n"
        for opt in options[:5]:  # Limit to 5 options
            opt_text = opt if isinstance(opt, str) else str(opt)
            formatted += f"→ {opt_text}\n"

        return formatted.strip()

    def _format_refinement(self, refinement: str) -> str:
        """Format user refinement quote."""
        if not refinement:
            return ""

        return f"""**You Refined the Approach**
"{refinement}"

Smart call. This is where we shifted gears.
"""

    def _format_agents(self, agents: List) -> str:
        """Format agent engagement section."""
        if not agents:
            return ""

        if len(agents) == 1:
            agent_data = agents[0]
            agent_name = agent_data.get('agent', 'Unknown') if isinstance(agent_data, dict) else str(agent_data)
            rationale = agent_data.get('rationale', '') if isinstance(agent_data, dict) else ''

            return f"""**Built a Specialist to Help**
Since this needed {rationale.lower() if rationale else "specialized expertise"}, we brought in the **{agent_name}** to tackle it properly.
"""
        else:
            # Multiple agents
            agent_list = []
            for agent_data in agents:
                agent_name = agent_data.get('agent', 'Unknown') if isinstance(agent_data, dict) else str(agent_data)
                agent_list.append(agent_name)

            agents_text = " → ".join([f"**{a}**" for a in agent_list])
            return f"""**Worked with Multiple Specialists**
This journey needed expertise across domains, so we collaborated with: {agents_text}
"""

    def _format_deliverables(self, deliverables: List) -> str:
        """Format deliverables section."""
        if not deliverables:
            return ""

        formatted = "**What Got Delivered**\n"
        for d in deliverables[:5]:  # Limit to 5
            if isinstance(d, dict):
                name = d.get('name', 'Unknown')
                desc = d.get('description', '')
                size = d.get('size', '')

                line = f"- {name}"
                if desc:
                    line += f" ({desc})"
                if size:
                    line += f" - {size}"
                formatted += line + "\n"
            else:
                formatted += f"- {str(d)}\n"

        return formatted.strip()

    def _make_conversational_impact(self, impact: str) -> str:
        """Convert impact to conversational tone."""
        if not impact:
            return "This saved significant time and effort."

        # Impact is already conversational from logger
        return impact

    def _make_generalized_learning(self, meta_learning: str, problem: str) -> str:
        """Generate generalized learning from meta-learning and problem."""
        if meta_learning:
            # Extract pattern name if present
            if "pattern" in meta_learning.lower():
                return f"You discovered the {meta_learning}. Next time you face a similar challenge, remember this approach worked well."
            return meta_learning

        # Fallback generic learning
        return "When facing complex problems, break them down and explore multiple approaches before committing to one path."

    def _extract_takeaway(self, pattern: str) -> str:
        """Extract actionable takeaway from pattern."""
        # Simple extraction - can be enhanced with pattern matching
        if "assumption" in pattern.lower():
            return "Before building anything big, ask 'what's my riskiest assumption?' and validate that first."
        elif "automation" in pattern.lower():
            return "When you hit a 'this will take forever' problem, ask Maia to explore automation options."
        else:
            return f"Apply the {pattern} approach to similar problems."

    def _parse_json_field(self, field) -> List:
        """Parse JSON field (handles both JSON string and parsed list/dict)."""
        if isinstance(field, (list, dict)):
            return field if isinstance(field, list) else [field]
        if isinstance(field, str):
            try:
                parsed = json.loads(field)
                return parsed if isinstance(parsed, list) else [parsed]
            except (json.JSONDecodeError, TypeError):
                return []
        return []


def main():
    """CLI interface for narrative synthesizer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate weekly Maia journey narratives"
    )
    parser.add_argument(
        'command',
        choices=['generate'],
        help='Command to execute'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: claude/data/narratives/weekly_narrative_YYYY_MM_DD.md)'
    )

    args = parser.parse_args()

    synthesizer = WeeklyNarrativeSynthesizer()

    if args.command == 'generate':
        # Default output path
        if not args.output:
            today = datetime.now()
            output_dir = Path(__file__).parent.parent / 'data' / 'narratives'
            args.output = str(output_dir / f"weekly_narrative_{today.strftime('%Y_%m_%d')}.md")

        print(f"Generating weekly narrative...")
        narrative = synthesizer.generate_weekly_narrative(args.output)

        if narrative:
            print(f"✅ Narrative generated: {args.output}")
            print(f"\nPreview (first 500 chars):\n{narrative[:500]}...\n")
        else:
            print("❌ Failed to generate narrative")
            sys.exit(1)


if __name__ == '__main__':
    main()
