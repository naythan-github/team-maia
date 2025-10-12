#!/usr/bin/env python3
"""
Meta-Learning System
Adaptive prompt optimization based on user feedback and interaction patterns

Purpose:
- Learn user preferences from feedback patterns (corrections, ratings, style)
- Adapt agent prompts dynamically per user
- Track effectiveness of adaptations over time
- Generate insights for system-wide improvements

Author: Maia (Phase 5: Advanced Research)
Created: 2025-10-12
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

@dataclass
class UserFeedback:
    """User feedback on agent interaction"""
    feedback_id: str
    user_id: str
    agent_name: str
    interaction_id: str
    timestamp: str
    feedback_type: str  # "correction", "rating", "preference", "complaint"
    content: str
    rating: Optional[float] = None  # 1-5 scale
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserFeedback':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class UserPreferenceProfile:
    """Learned preferences for a user"""
    user_id: str
    detail_level: str  # "minimal", "standard", "comprehensive"
    tone: str  # "professional", "friendly", "direct"
    format_preference: str  # "bullets", "paragraphs", "mixed"
    code_style: str  # "verbose", "concise", "commented"
    explanation_depth: str  # "high-level", "balanced", "detailed"
    common_corrections: List[str]
    avg_rating: float
    interaction_count: int
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferenceProfile':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class PromptAdaptation:
    """Adaptation applied to agent prompt for user"""
    adaptation_id: str
    user_id: str
    agent_name: str
    adaptation_type: str  # "detail_level", "tone", "format", "style"
    original_value: str
    adapted_value: str
    created_at: str
    effectiveness_score: Optional[float] = None  # Based on subsequent ratings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptAdaptation':
        """Create from dictionary"""
        return cls(**data)

class MetaLearningSystem:
    """
    Learns user preferences and adapts prompts dynamically

    Features:
    - User preference profiling (detail level, tone, format)
    - Pattern detection (common corrections, feedback themes)
    - Dynamic prompt adaptation (per-user customization)
    - Effectiveness tracking (A/B test adaptations)
    """

    def __init__(self):
        """Initialize meta-learning system"""
        self.maia_root = Path(__file__).resolve().parents[3]
        self.session_dir = self.maia_root / "claude" / "context" / "session"
        self.feedback_dir = self.session_dir / "user_feedback"
        self.profiles_dir = self.session_dir / "user_profiles"
        self.adaptations_dir = self.session_dir / "prompt_adaptations"

        # Create directories
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.adaptations_dir.mkdir(parents=True, exist_ok=True)

    def record_feedback(
        self,
        user_id: str,
        agent_name: str,
        interaction_id: str,
        feedback_type: str,
        content: str,
        rating: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """
        Record user feedback on interaction

        Args:
            user_id: User identifier
            agent_name: Agent that handled interaction
            interaction_id: Interaction identifier
            feedback_type: Type of feedback ("correction", "rating", "preference", "complaint")
            content: Feedback content
            rating: Optional 1-5 rating
            metadata: Optional additional data

        Returns:
            UserFeedback object
        """
        feedback_id = f"fb_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            agent_name=agent_name,
            interaction_id=interaction_id,
            timestamp=datetime.now().isoformat(),
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            metadata=metadata
        )

        # Save feedback
        feedback_file = self.feedback_dir / f"{feedback_id}.json"
        with open(feedback_file, 'w') as f:
            json.dump(feedback.to_dict(), f, indent=2)

        # Update user profile
        self._update_user_profile(feedback)

        return feedback

    def _update_user_profile(self, feedback: UserFeedback):
        """Update user preference profile based on feedback"""
        profile = self.get_user_profile(feedback.user_id)

        if not profile:
            # Create new profile with defaults
            profile = UserPreferenceProfile(
                user_id=feedback.user_id,
                detail_level="standard",
                tone="professional",
                format_preference="mixed",
                code_style="concise",
                explanation_depth="balanced",
                common_corrections=[],
                avg_rating=0.0,
                interaction_count=0,
                last_updated=datetime.now().isoformat()
            )

        # Update based on feedback type
        if feedback.feedback_type == "correction":
            profile.common_corrections.append(feedback.content)
            # Keep last 20 corrections
            profile.common_corrections = profile.common_corrections[-20:]

            # Detect patterns in corrections
            self._detect_preference_patterns(profile, feedback)

        if feedback.rating is not None:
            # Update average rating
            total = profile.avg_rating * profile.interaction_count + feedback.rating
            profile.interaction_count += 1
            profile.avg_rating = total / profile.interaction_count

        profile.last_updated = datetime.now().isoformat()

        # Save profile
        self._save_user_profile(profile)

    def _detect_preference_patterns(self, profile: UserPreferenceProfile, feedback: UserFeedback):
        """Detect preference patterns from correction content"""
        content_lower = feedback.content.lower()

        # Detail level
        if any(word in content_lower for word in ["too verbose", "too long", "tldr", "shorter"]):
            profile.detail_level = "minimal"
        elif any(word in content_lower for word in ["more detail", "elaborate", "explain more"]):
            profile.detail_level = "comprehensive"

        # Tone
        if any(word in content_lower for word in ["too formal", "stiff", "robotic"]):
            profile.tone = "friendly"
        elif any(word in content_lower for word in ["too casual", "unprofessional"]):
            profile.tone = "professional"
        elif any(word in content_lower for word in ["get to the point", "just tell me"]):
            profile.tone = "direct"

        # Format
        if any(word in content_lower for word in ["bullet points", "list format", "bullets"]):
            profile.format_preference = "bullets"
        elif any(word in content_lower for word in ["paragraph", "narrative", "flowing"]):
            profile.format_preference = "paragraphs"

        # Code style
        if any(word in content_lower for word in ["more comments", "explain code", "what does this do"]):
            profile.code_style = "verbose"
        elif any(word in content_lower for word in ["too many comments", "clean code", "concise"]):
            profile.code_style = "concise"

        # Explanation depth
        if any(word in content_lower for word in ["why", "reasoning", "rationale", "deeper"]):
            profile.explanation_depth = "detailed"
        elif any(word in content_lower for word in ["high level", "overview", "summary"]):
            profile.explanation_depth = "high-level"

    def get_user_profile(self, user_id: str) -> Optional[UserPreferenceProfile]:
        """Get user preference profile"""
        profile_file = self.profiles_dir / f"{user_id}.json"

        if not profile_file.exists():
            return None

        with open(profile_file, 'r') as f:
            data = json.load(f)
            return UserPreferenceProfile.from_dict(data)

    def _save_user_profile(self, profile: UserPreferenceProfile):
        """Save user preference profile"""
        profile_file = self.profiles_dir / f"{profile.user_id}.json"
        with open(profile_file, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)

    def generate_adapted_prompt(
        self,
        user_id: str,
        agent_name: str,
        base_prompt: str
    ) -> Tuple[str, List[PromptAdaptation]]:
        """
        Generate adapted prompt based on user preferences

        Args:
            user_id: User identifier
            agent_name: Agent name
            base_prompt: Original agent prompt

        Returns:
            Tuple of (adapted_prompt, list_of_adaptations)
        """
        profile = self.get_user_profile(user_id)

        if not profile:
            # No profile, return base prompt
            return base_prompt, []

        adapted_prompt = base_prompt
        adaptations = []

        # Apply detail level adaptation
        if profile.detail_level == "minimal":
            adaptation = self._create_adaptation(user_id, agent_name, "detail_level", "standard", "minimal")
            adapted_prompt = self._apply_detail_adaptation(adapted_prompt, "minimal")
            adaptations.append(adaptation)
        elif profile.detail_level == "comprehensive":
            adaptation = self._create_adaptation(user_id, agent_name, "detail_level", "standard", "comprehensive")
            adapted_prompt = self._apply_detail_adaptation(adapted_prompt, "comprehensive")
            adaptations.append(adaptation)

        # Apply tone adaptation
        if profile.tone != "professional":
            adaptation = self._create_adaptation(user_id, agent_name, "tone", "professional", profile.tone)
            adapted_prompt = self._apply_tone_adaptation(adapted_prompt, profile.tone)
            adaptations.append(adaptation)

        # Apply format adaptation
        if profile.format_preference == "bullets":
            adaptation = self._create_adaptation(user_id, agent_name, "format", "mixed", "bullets")
            adapted_prompt = self._apply_format_adaptation(adapted_prompt, "bullets")
            adaptations.append(adaptation)
        elif profile.format_preference == "paragraphs":
            adaptation = self._create_adaptation(user_id, agent_name, "format", "mixed", "paragraphs")
            adapted_prompt = self._apply_format_adaptation(adapted_prompt, "paragraphs")
            adaptations.append(adaptation)

        # Save adaptations
        for adaptation in adaptations:
            self._save_adaptation(adaptation)

        return adapted_prompt, adaptations

    def _create_adaptation(
        self,
        user_id: str,
        agent_name: str,
        adaptation_type: str,
        original_value: str,
        adapted_value: str
    ) -> PromptAdaptation:
        """Create adaptation record"""
        adaptation_id = f"adapt_{user_id}_{agent_name}_{adaptation_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return PromptAdaptation(
            adaptation_id=adaptation_id,
            user_id=user_id,
            agent_name=agent_name,
            adaptation_type=adaptation_type,
            original_value=original_value,
            adapted_value=adapted_value,
            created_at=datetime.now().isoformat()
        )

    def _apply_detail_adaptation(self, prompt: str, detail_level: str) -> str:
        """Apply detail level adaptation to prompt"""
        if detail_level == "minimal":
            # Add instruction for conciseness
            adaptation = "\n\n**USER PREFERENCE: This user prefers minimal detail. Keep responses concise, bullet-pointed, and to-the-point. Avoid lengthy explanations unless specifically requested.**\n"
        elif detail_level == "comprehensive":
            # Add instruction for detail
            adaptation = "\n\n**USER PREFERENCE: This user prefers comprehensive detail. Provide thorough explanations, consider edge cases, and include relevant background context.**\n"
        else:
            return prompt

        return prompt + adaptation

    def _apply_tone_adaptation(self, prompt: str, tone: str) -> str:
        """Apply tone adaptation to prompt"""
        if tone == "friendly":
            adaptation = "\n\n**USER PREFERENCE: This user prefers a friendly, conversational tone. Be warm and approachable while maintaining professionalism.**\n"
        elif tone == "direct":
            adaptation = "\n\n**USER PREFERENCE: This user prefers direct communication. Get straight to the point, minimize preamble, and prioritize actionable information.**\n"
        else:
            return prompt

        return prompt + adaptation

    def _apply_format_adaptation(self, prompt: str, format_pref: str) -> str:
        """Apply format preference adaptation to prompt"""
        if format_pref == "bullets":
            adaptation = "\n\n**USER PREFERENCE: This user prefers bullet-point format. Use lists, short items, and clear structure over narrative paragraphs.**\n"
        elif format_pref == "paragraphs":
            adaptation = "\n\n**USER PREFERENCE: This user prefers narrative paragraph format. Use flowing prose and cohesive explanations over bullet points.**\n"
        else:
            return prompt

        return prompt + adaptation

    def _save_adaptation(self, adaptation: PromptAdaptation):
        """Save adaptation record"""
        adaptation_file = self.adaptations_dir / f"{adaptation.adaptation_id}.json"
        with open(adaptation_file, 'w') as f:
            json.dump(adaptation.to_dict(), f, indent=2)

    def analyze_adaptation_effectiveness(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze effectiveness of adaptations for user

        Args:
            user_id: User identifier
            days: Analysis window (days)

        Returns:
            Effectiveness analysis dict
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return {"error": "No profile found"}

        # Get feedback since adaptations started
        cutoff = datetime.now() - timedelta(days=days)
        recent_feedback = []

        for feedback_file in self.feedback_dir.glob(f"fb_{user_id}_*.json"):
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
                feedback = UserFeedback.from_dict(feedback_data)

                if datetime.fromisoformat(feedback.timestamp) > cutoff:
                    recent_feedback.append(feedback)

        if not recent_feedback:
            return {"error": "No recent feedback"}

        # Calculate metrics
        ratings = [f.rating for f in recent_feedback if f.rating is not None]
        corrections = [f for f in recent_feedback if f.feedback_type == "correction"]

        avg_rating = statistics.mean(ratings) if ratings else 0.0
        correction_rate = len(corrections) / len(recent_feedback)

        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_interactions": len(recent_feedback),
            "average_rating": avg_rating,
            "correction_rate": correction_rate,
            "profile": profile.to_dict(),
            "effectiveness_score": self._calculate_effectiveness_score(avg_rating, correction_rate)
        }

    def _calculate_effectiveness_score(self, avg_rating: float, correction_rate: float) -> float:
        """
        Calculate effectiveness score (0-100)

        Args:
            avg_rating: Average user rating (1-5)
            correction_rate: Fraction of interactions with corrections

        Returns:
            Effectiveness score (0-100)
        """
        # Normalize rating to 0-1 (5 = 1.0, 1 = 0.0)
        rating_score = (avg_rating - 1) / 4

        # Invert correction rate (fewer corrections = better)
        correction_score = 1 - correction_rate

        # Weighted combination (70% rating, 30% corrections)
        effectiveness = (rating_score * 0.7) + (correction_score * 0.3)

        return effectiveness * 100


def main():
    """Example usage and testing"""
    system = MetaLearningSystem()

    print("=== Meta-Learning System ===\n")

    user_id = "nathan@example.com"
    agent_name = "cloud_architect"

    # Simulate user feedback
    print("Recording user feedback...\n")

    # User prefers concise responses
    system.record_feedback(
        user_id=user_id,
        agent_name=agent_name,
        interaction_id="int_001",
        feedback_type="correction",
        content="Too verbose. Please keep responses shorter and more to-the-point.",
        rating=3.0
    )

    # User prefers bullet points
    system.record_feedback(
        user_id=user_id,
        agent_name=agent_name,
        interaction_id="int_002",
        feedback_type="correction",
        content="Can you use bullet points instead of long paragraphs?",
        rating=3.5
    )

    # User prefers direct tone
    system.record_feedback(
        user_id=user_id,
        agent_name=agent_name,
        interaction_id="int_003",
        feedback_type="correction",
        content="Just tell me what I need to do, skip the preamble.",
        rating=4.0
    )

    print("✓ Recorded 3 feedback items\n")

    # Get user profile
    print("User Preference Profile:")
    profile = system.get_user_profile(user_id)
    if profile:
        print(f"  Detail Level: {profile.detail_level}")
        print(f"  Tone: {profile.tone}")
        print(f"  Format: {profile.format_preference}")
        print(f"  Avg Rating: {profile.avg_rating:.1f}/5.0")
        print(f"  Interactions: {profile.interaction_count}")
        print()

    # Generate adapted prompt
    base_prompt = """# Cloud Architect Agent

You are an expert cloud architect helping design and optimize cloud infrastructure.

## Your Role
Provide detailed architectural guidance for cloud solutions...

## Response Style
Provide comprehensive explanations with examples..."""

    print("Generating adapted prompt...\n")
    adapted_prompt, adaptations = system.generate_adapted_prompt(user_id, agent_name, base_prompt)

    print(f"Applied {len(adaptations)} adaptations:")
    for adaptation in adaptations:
        print(f"  - {adaptation.adaptation_type}: {adaptation.original_value} → {adaptation.adapted_value}")
    print()

    print("Adapted Prompt Preview (last 300 chars):")
    print(adapted_prompt[-300:])
    print()

    # Analyze effectiveness
    print("Analyzing adaptation effectiveness...")
    analysis = system.analyze_adaptation_effectiveness(user_id, days=30)

    if "error" not in analysis:
        print(f"  Effectiveness Score: {analysis['effectiveness_score']:.1f}/100")
        print(f"  Avg Rating: {analysis['average_rating']:.1f}/5.0")
        print(f"  Correction Rate: {analysis['correction_rate']:.1%}")


if __name__ == "__main__":
    main()
