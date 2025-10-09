#!/usr/bin/env python3
"""
Conversation Detector - Automated Significant Conversation Detection

Analyzes conversation context to identify discussions worth preserving.
Integrated with Maia's hook system (Phase 34) for automated knowledge capture.

Author: Maia System
Created: 2025-10-09 (Phase 102 - Automated Conversation Detection)
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path


class ConversationDetector:
    """Detect significant conversations worthy of persistence"""

    def __init__(self):
        self.maia_root = Path(__file__).resolve().parents[2]

        # Conversation significance indicators
        self.significance_patterns = {
            "decisions": {
                "patterns": [
                    r"\b(decided|decision|agreed|consensus|concluded|determined)\b",
                    r"\b(we should|let's|going to|will|shall)\b",
                    r"\b(approach is|strategy is|plan is|recommendation)\b",
                    r"\b(final decision|agreed upon|settled on)\b"
                ],
                "weight": 3.0
            },
            "recommendations": {
                "patterns": [
                    r"\b(recommend|suggestion|propose|advise|should)\b",
                    r"\b(best practice|optimal approach|preferred method)\b",
                    r"\b(key points?|main recommendations?|action items?)\b",
                    r"\b(steps? (to|for)|process|methodology|framework)\b"
                ],
                "weight": 2.5
            },
            "problem_solving": {
                "patterns": [
                    r"\b(problem|issue|challenge|obstacle|difficulty)\b",
                    r"\b(solution|fix|resolve|address|handle)\b",
                    r"\b(troubleshoot|debug|investigate|analyze)\b",
                    r"\b(root cause|underlying issue|core problem)\b"
                ],
                "weight": 2.0
            },
            "planning": {
                "patterns": [
                    r"\b(plan|planning|roadmap|timeline|schedule)\b",
                    r"\b(phase \d+|stage \d+|step \d+|milestone)\b",
                    r"\b(project|initiative|implementation|rollout)\b",
                    r"\b(scope|requirements|deliverables|objectives)\b"
                ],
                "weight": 2.0
            },
            "people_management": {
                "patterns": [
                    r"\b(team member|colleague|employee|staff)\b",
                    r"\b(discipline|performance|behavior|conduct)\b",
                    r"\b(1:1|one-on-one|meeting|discussion|feedback)\b",
                    r"\b(HR|human resources|management|leadership)\b"
                ],
                "weight": 2.5
            },
            "learning": {
                "patterns": [
                    r"\b(learned|lesson|insight|discovery|realization)\b",
                    r"\b(understanding|knowledge|expertise|experience)\b",
                    r"\b(remember|recall|note|important|critical)\b",
                    r"\b(takeaway|conclusion|finding|observation)\b"
                ],
                "weight": 1.5
            },
            "research": {
                "patterns": [
                    r"\b(research|analysis|investigation|study)\b",
                    r"\b(findings|results|conclusions|insights)\b",
                    r"\b(data|evidence|metrics|statistics)\b",
                    r"\b(comparison|evaluation|assessment)\b"
                ],
                "weight": 1.5
            }
        }

        # Multi-turn conversation indicators
        self.conversation_depth_indicators = [
            r"\b(earlier|previously|you mentioned|we discussed)\b",
            r"\b(building on|continuing|following up)\b",
            r"\b(as we talked about|as you said|back to)\b",
            r"\b(let's move on to|next|also|furthermore)\b"
        ]

        # Length thresholds (character counts)
        self.min_length_significant = 500  # Minimum for potential significance
        self.min_length_complex = 1500     # Definitely complex/important

        # User engagement patterns
        self.engagement_patterns = [
            r"\b(that'?s helpful|good point|interesting|thanks?|appreciate)\b",
            r"\b(makes sense|understand|got it|clear)\b",
            r"\b(yes|yeah|correct|right|exactly)\b",
            r"\b(great|excellent|perfect|good)\b"
        ]

        # Exclusion patterns (trivial conversations)
        self.trivial_patterns = [
            r"^(hi|hello|hey|thanks?|thank you|bye|goodbye)\.?$",
            r"^(yes|no|ok|okay|sure)\.?$",
            r"^(load|save|list|show|help)$",
            r"^\d+\s*[\+\-\*/]\s*\d+$"  # Simple math
        ]

    def analyze_conversation(
        self,
        conversation_text: str,
        turn_count: int = 1,
        user_responses: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze conversation for significance

        Args:
            conversation_text: Full conversation content
            turn_count: Number of back-and-forth turns
            user_responses: List of user messages (for engagement analysis)

        Returns:
            Dictionary with significance score, detected topics, and recommendation
        """

        # Check trivial patterns first
        if self._is_trivial(conversation_text):
            return {
                "significant": False,
                "score": 0.0,
                "reason": "Trivial conversation (greeting, simple command, etc.)",
                "recommendation": "skip",
                "detected_topics": []
            }

        # Calculate significance scores
        topic_scores = {}
        detected_topics = []

        for topic, config in self.significance_patterns.items():
            score = 0.0
            matches = []

            for pattern in config["patterns"]:
                found = re.findall(pattern, conversation_text, re.IGNORECASE)
                if found:
                    matches.extend(found)
                    score += len(found) * config["weight"]

            if score > 0:
                topic_scores[topic] = score
                detected_topics.append(topic)

        # Calculate base significance score
        total_score = sum(topic_scores.values())

        # Apply multipliers

        # Length multiplier
        length_multiplier = 1.0
        text_length = len(conversation_text)
        if text_length >= self.min_length_complex:
            length_multiplier = 1.5
        elif text_length >= self.min_length_significant:
            length_multiplier = 1.2

        # Conversation depth multiplier (multi-turn bonus)
        depth_score = 0
        for pattern in self.conversation_depth_indicators:
            depth_score += len(re.findall(pattern, conversation_text, re.IGNORECASE))

        depth_multiplier = 1.0 + (depth_score * 0.1)  # +10% per depth indicator
        depth_multiplier = min(depth_multiplier, 2.0)  # Cap at 2x

        # User engagement multiplier
        engagement_score = 0
        if user_responses:
            for response in user_responses:
                for pattern in self.engagement_patterns:
                    engagement_score += len(re.findall(pattern, response, re.IGNORECASE))

        engagement_multiplier = 1.0 + (engagement_score * 0.05)  # +5% per engagement signal
        engagement_multiplier = min(engagement_multiplier, 1.5)  # Cap at 1.5x

        # Final score
        final_score = total_score * length_multiplier * depth_multiplier * engagement_multiplier

        # Normalize to 0-100 scale
        normalized_score = min(final_score * 2, 100)  # Rough normalization

        # Determine significance and recommendation
        is_significant = normalized_score >= 20.0  # Threshold for significance

        if normalized_score >= 50.0:
            recommendation = "definitely_save"
            reason = "High significance: Multiple important topics, substantial depth"
        elif normalized_score >= 35.0:
            recommendation = "recommend_save"
            reason = "Moderate significance: Important discussion worth preserving"
        elif normalized_score >= 20.0:
            recommendation = "consider_save"
            reason = "Low-moderate significance: May be worth saving"
        else:
            recommendation = "skip"
            reason = "Low significance: Not worth preserving"

        return {
            "significant": is_significant,
            "score": round(normalized_score, 1),
            "reason": reason,
            "recommendation": recommendation,
            "detected_topics": detected_topics,
            "topic_scores": topic_scores,
            "multipliers": {
                "length": round(length_multiplier, 2),
                "depth": round(depth_multiplier, 2),
                "engagement": round(engagement_multiplier, 2)
            },
            "metadata": {
                "text_length": text_length,
                "turn_count": turn_count,
                "depth_indicators": depth_score,
                "engagement_signals": engagement_score
            }
        }

    def _is_trivial(self, text: str) -> bool:
        """Check if conversation is trivial"""
        text_stripped = text.strip().lower()

        # Very short
        if len(text_stripped) < 20:
            for pattern in self.trivial_patterns:
                if re.match(pattern, text_stripped, re.IGNORECASE):
                    return True

        return False

    def extract_topics_and_tags(self, conversation_text: str) -> Tuple[List[str], List[str]]:
        """
        Extract likely topics and generate tags from conversation

        Returns:
            (topics, tags) tuple
        """
        topics = []
        tags = set()

        # Extract topics from detected patterns
        for topic, config in self.significance_patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, conversation_text, re.IGNORECASE):
                    topics.append(topic)
                    # Convert topic to tag format
                    tags.add(topic.replace("_", "-"))
                    break  # One match per topic category

        # Extract domain-specific tags
        domain_keywords = {
            "hr": ["HR", "discipline", "performance", "team member"],
            "management": ["management", "leadership", "1:1", "meeting"],
            "technical": ["code", "bug", "implementation", "system"],
            "planning": ["plan", "roadmap", "phase", "project"],
            "research": ["research", "analysis", "findings", "study"],
            "strategy": ["strategy", "approach", "methodology", "framework"]
        }

        for tag, keywords in domain_keywords.items():
            for keyword in keywords:
                if re.search(rf"\b{keyword}\b", conversation_text, re.IGNORECASE):
                    tags.add(tag)
                    break

        return topics, sorted(list(tags))

    def generate_save_prompt(self, analysis: Dict, conversation_preview: str) -> str:
        """Generate user prompt for conversation saving"""

        prompt = []

        prompt.append("\n" + "="*70)
        prompt.append("💾 CONVERSATION WORTH SAVING DETECTED")
        prompt.append("="*70)

        prompt.append(f"\n📊 Significance Score: {analysis['score']}/100")
        prompt.append(f"🎯 Recommendation: {analysis['recommendation'].replace('_', ' ').title()}")
        prompt.append(f"💡 Reason: {analysis['reason']}")

        if analysis['detected_topics']:
            prompt.append(f"\n📋 Detected Topics: {', '.join(analysis['detected_topics'])}")

        prompt.append(f"\n📝 Preview: {conversation_preview[:150]}...")

        prompt.append("\n❓ Would you like to save this conversation?")
        prompt.append("   Type: /save-conversation  (guided interface)")
        prompt.append("   Or: 'yes save' for quick save with auto-extraction")
        prompt.append("   Or: 'skip' to dismiss")

        prompt.append("="*70 + "\n")

        return "\n".join(prompt)


def main():
    """CLI interface for testing conversation detector"""
    import sys

    detector = ConversationDetector()

    if len(sys.argv) < 2:
        print("Usage: python3 conversation_detector.py [analyze|test] <text>")
        print("\nExamples:")
        print("  python3 conversation_detector.py analyze 'We discussed team discipline...'")
        print("  python3 conversation_detector.py test")
        return

    command = sys.argv[1]

    if command == "analyze":
        if len(sys.argv) < 3:
            print("Error: analyze requires conversation text")
            return

        text = " ".join(sys.argv[2:])
        analysis = detector.analyze_conversation(text)

        print(f"\n📊 Conversation Analysis\n")
        print(f"Significant: {'✅ Yes' if analysis['significant'] else '❌ No'}")
        print(f"Score: {analysis['score']}/100")
        print(f"Recommendation: {analysis['recommendation']}")
        print(f"Reason: {analysis['reason']}")
        print(f"\nDetected Topics: {', '.join(analysis['detected_topics']) or 'None'}")
        print(f"\nMultipliers:")
        for k, v in analysis['multipliers'].items():
            print(f"  {k}: {v}x")

        if analysis['significant']:
            topics, tags = detector.extract_topics_and_tags(text)
            print(f"\nSuggested Tags: {', '.join(tags)}")

    elif command == "test":
        test_cases = [
            ("Hi", False, "Trivial greeting"),
            ("load", False, "Simple command"),
            ("We discussed how to handle team member using inappropriate language. Decided on private 1:1 approach with clear behavioral standards while supporting workload. Created meeting template and documentation plan.", True, "People management decision"),
            ("I researched the best approach for implementing RAG system. Found that nomic-embed-text embeddings work well. Recommend ChromaDB for persistence.", True, "Research and recommendations"),
            ("what is 2+2", False, "Simple math question"),
            ("Let's plan the project roadmap. Phase 1 will focus on MVP, Phase 2 on scaling. Key milestones include beta launch in Q2.", True, "Project planning")
        ]

        print("\n🧪 Conversation Detection Test Suite\n")
        print("="*70)

        correct = 0
        for text, expected_significant, description in test_cases:
            analysis = detector.analyze_conversation(text)
            is_correct = analysis['significant'] == expected_significant

            status = "✅" if is_correct else "❌"
            print(f"\n{status} {description}")
            print(f"   Text: '{text[:50]}...'")
            print(f"   Expected: {'Significant' if expected_significant else 'Trivial'}")
            print(f"   Detected: {'Significant' if analysis['significant'] else 'Trivial'} (score: {analysis['score']})")

            if is_correct:
                correct += 1

        print(f"\n{'='*70}")
        print(f"Accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%)")


if __name__ == "__main__":
    main()
