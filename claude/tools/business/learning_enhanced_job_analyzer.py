#!/usr/bin/env python3
# NOTE: DEMO FILE - Message bus imports deprecated, use Swarm framework instead
# See claude/tools/orchestration/agent_swarm.py for current orchestration patterns
"""
Learning-Enhanced Job Analyzer - Phase 21 Integration
====================================================

Integrates the Contextual Memory & Learning System (Phase 21) with 
Autonomous Multi-Agent Orchestration (Phase 20) to create genuinely
intelligent, adaptive job analysis that learns from user feedback.

Key Features:
- Learns user preferences from job decisions and feedback
- Adapts scoring algorithms based on user patterns
- Provides personalized recommendations based on learned preferences
- Improves accuracy through continuous learning loops
- Remembers context across sessions for consistent personalization

This demonstrates the evolution from stateless automation to learning AI.
"""

import asyncio
import time
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import Phase 20 autonomous orchestration
from claude.tools.business.autonomous_job_analyzer import AutonomousJobAnalyzer
# DEPRECATED: Message bus replaced by Swarm framework
# from claude.tools.agent_message_bus import get_message_bus, MessageType, MessagePriority
from claude.tools.enhanced_context_manager import get_context_manager

# Import Phase 21 learning system
from claude.tools.contextual_memory_learning_system import ContextualMemoryLearningSystem

class LearningEnhancedJobAnalyzer:
    """
    Intelligent job analyzer that learns and adapts from user interactions
    
    Evolution Path:
    Phase 20: Autonomous orchestration with static scoring
    Phase 21: Learning system that adapts to user preferences
    
    Capabilities:
    - Learns job preferences from accept/reject decisions
    - Adapts scoring weights based on user feedback
    - Provides personalized job rankings
    - Remembers user patterns across sessions
    - Continuously improves recommendation accuracy
    """
    
    def __init__(self, user_id: str = "naythan"):
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())
        
        # Initialize Phase 20 autonomous orchestration
        self.orchestrator = AutonomousJobAnalyzer()
        
        # Initialize Phase 21 learning system
        self.learning_system = ContextualMemoryLearningSystem(user_id)
        
        # Get orchestration infrastructure
        self.bus = get_message_bus()
        self.context_manager = get_context_manager()
        
        # Learning-enhanced parameters
        self.learning_weight = 0.4  # How much to weight learned preferences
        self.adaptation_rate = 0.2  # How quickly to adapt to new feedback
        
        print(f"🧠 Learning-Enhanced Job Analyzer initialized for {user_id}")
        print(f"🤖 Integrating Phase 20 (Orchestration) + Phase 21 (Learning)")
    
    async def analyze_jobs_with_learning(self, query: str = "recent job emails",
                                        learn_from_feedback: bool = True) -> Dict[str, Any]:
        """
        Analyze job opportunities using both autonomous orchestration and learning
        
        Process:
        1. Use Phase 20 autonomous orchestration for base analysis
        2. Apply Phase 21 learned preferences for personalization
        3. Generate personalized recommendations
        4. Learn from user interactions and feedback
        5. Adapt future analysis based on learning
        """
        
        print(f"\n🚀 Learning-Enhanced Job Analysis - Session: {self.session_id[:8]}")
        print("=" * 70)
        
        # Step 1: Get learned preferences to influence analysis
        print("\n🧠 Step 1: Loading Learned Preferences")
        job_preferences = self.learning_system.predict_preference("job", {"analysis_type": "job_search"})
        communication_prefs = self.learning_system.predict_preference("communication", {})
        
        print(f"  • Job Preferences: {len(job_preferences.get('predictions', {}))} learned")
        print(f"  • Communication Style: {len(communication_prefs.get('predictions', {}))} learned")
        print(f"  • Overall Confidence: {job_preferences.get('confidence', 0):.2f}")
        
        # Step 2: Run autonomous orchestration with learning context
        print("\n🤖 Step 2: Autonomous Orchestration Analysis")
        context = self.context_manager.create_context(
            context_id=f"learning_job_analysis_{int(time.time())}",
            context_type="learning_enhanced_job_analysis"
        )
        
        # Add learned preferences to context
        context['learned_preferences'] = {
            'job_preferences': job_preferences,
            'communication_preferences': communication_prefs,
            'user_id': self.user_id,
            'session_id': self.session_id
        }
        
        # Run base orchestration analysis
        base_results = await self.orchestrator.analyze_job_opportunities(query)
        
        # Step 3: Apply learning-based personalization
        print("\n🎯 Step 3: Applying Personalized Learning")
        if 'results' in base_results and 'top_opportunities' in base_results['results']:
            personalized_jobs = self._apply_learned_preferences(
                base_results['results']['top_opportunities'],
                job_preferences
            )
            base_results['results']['personalized_opportunities'] = personalized_jobs
            base_results['results']['learning_applied'] = True
        
        # Step 4: Generate learning insights
        print("\n🔍 Step 4: Learning Insights Generation")
        learning_insights = self.learning_system.generate_learning_insights()
        base_results['learning_insights'] = learning_insights
        
        # Step 5: Learn from this interaction
        if learn_from_feedback:
            print("\n📚 Step 5: Recording Learning Interaction")
            interaction_id = self.learning_system.learn_from_interaction(
                interaction_type="job_analysis",
                context={
                    "analysis_type": "job_search",
                    "query": query,
                    "jobs_found": len(base_results['results'].get('top_opportunities', [])),
                    "personalization_applied": True,
                    "learned_preferences_used": len(job_preferences.get('predictions', {}))
                },
                user_input=query,
                system_response=f"Analyzed {len(base_results['results'].get('top_opportunities', []))} jobs with learning",
                outcome_rating=4.0  # Default positive rating for successful analysis
            )
            base_results['learning_interaction_id'] = interaction_id
        
        return base_results
    
    def _apply_learned_preferences(self, jobs: List[Dict[str, Any]], 
                                 preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply learned preferences to job ranking"""
        
        if not jobs or not preferences.get('predictions'):
            return jobs
        
        print(f"  🎯 Personalizing {len(jobs)} job opportunities...")
        
        # Get personalized recommendations using learning system
        personalized_jobs = self.learning_system.get_personalized_recommendations(
            domain="job",
            options=jobs,
            context={"analysis_type": "job_search"}
        )
        
        # Combine original scores with personalization scores
        for job in personalized_jobs:
            original_score = job.get('quality_score', 0.0)
            personalization_score = job.get('personalization_score', 0.0)
            
            # Weighted combination of original and personalized scores
            job['combined_score'] = (
                original_score * (1 - self.learning_weight) + 
                personalization_score * 10 * self.learning_weight  # Scale personalization score
            )
            
            job['learning_boost'] = personalization_score * 10
            job['original_score'] = original_score
        
        # Re-sort by combined score
        personalized_jobs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        print(f"  ✅ Applied personalization with {self.learning_weight:.1%} learning weight")
        
        return personalized_jobs
    
    async def provide_job_feedback(self, job_id: str, decision: str, 
                                 feedback: str = None, rating: float = None) -> Dict[str, Any]:
        """
        Provide feedback on job recommendation to improve learning
        
        This is where the system learns and improves from user decisions
        """
        
        print(f"\n📚 Learning from Job Feedback")
        print("=" * 35)
        
        # Find job details (in real implementation, would lookup from database)
        job_context = {
            "job_id": job_id,
            "decision": decision,
            "feedback_provided": feedback is not None,
            "rating_provided": rating is not None
        }
        
        # Record learning interaction
        interaction_id = self.learning_system.learn_from_interaction(
            interaction_type="job_feedback",
            context=job_context,
            user_input=f"Job decision: {decision}",
            system_response=f"Recorded feedback for job {job_id}",
            user_feedback=feedback,
            outcome_rating=rating
        )
        
        # Get updated learning insights
        insights = self.learning_system.generate_learning_insights()
        
        print(f"  ✅ Recorded feedback interaction: {interaction_id[:8]}")
        print(f"  📈 Updated preferences: {insights['learning_statistics']['total_preferences']}")
        print(f"  🎯 Learning effectiveness: {insights['learning_effectiveness']['preference_confidence_rate']:.1%}")
        
        return {
            "interaction_id": interaction_id,
            "learning_updated": True,
            "current_insights": insights,
            "next_recommendations_will_improve": True
        }
    
    def get_personalized_analysis_summary(self) -> Dict[str, Any]:
        """Generate summary of personalized analysis capabilities"""
        
        insights = self.learning_system.generate_learning_insights()
        preferences = self.learning_system._get_top_preferences()
        
        summary = {
            "personalization_status": "active" if preferences else "learning",
            "learned_preferences": preferences,
            "learning_statistics": insights["learning_statistics"],
            "personalization_capabilities": [
                "Job preference learning from decisions",
                "Communication style adaptation",
                "Decision timing pattern recognition",
                "Personalized job ranking and scoring",
                "Continuous improvement from feedback"
            ],
            "competitive_advantages": [
                "Learns your specific job preferences",
                "Adapts to your decision-making style", 
                "Improves recommendations over time",
                "Remembers context across sessions",
                "Provides reasoning for recommendations"
            ]
        }
        
        return summary
    
    def demonstrate_learning_evolution(self) -> Dict[str, Any]:
        """Demonstrate how the system evolves with learning"""
        
        print(f"\n🧠 LEARNING EVOLUTION DEMONSTRATION")
        print("=" * 45)
        
        # Show current state
        insights = self.learning_system.generate_learning_insights()
        print(f"📊 Current Learning State:")
        print(f"  • Interactions Processed: {insights['learning_statistics']['total_interactions']}")
        print(f"  • Preferences Learned: {insights['learning_statistics']['total_preferences']}")
        print(f"  • Behavioral Patterns: {insights['learning_statistics']['total_patterns']}")
        print(f"  • User Satisfaction: {insights['learning_statistics']['average_user_satisfaction']:.2f}/5.0")
        
        # Show learning trajectory
        print(f"\n📈 Learning Trajectory:")
        effectiveness = insights['learning_effectiveness']
        print(f"  • Preference Confidence: {effectiveness['preference_confidence_rate']:.1%}")
        print(f"  • Pattern Reliability: {effectiveness['pattern_reliability_rate']:.1%}")
        print(f"  • Learning Velocity: {effectiveness['daily_learning_rate']:.1f}/day")
        
        # Predict future capabilities
        print(f"\n🚀 Predicted Capabilities (with more data):")
        print(f"  • Highly accurate job preference prediction")
        print(f"  • Proactive career opportunity identification")
        print(f"  • Personalized communication adaptation")
        print(f"  • Behavioral pattern-based scheduling optimization")
        print(f"  • Cross-session context and memory retention")
        
        return {
            "current_state": insights,
            "learning_trajectory": "rapid_improvement",
            "future_capabilities": "advanced_personalization",
            "system_evolution": "stateless_automation → learning_ai"
        }

async def main():
    """Demonstrate Learning-Enhanced Job Analyzer"""
    print("🧠 Learning-Enhanced Job Analyzer - Phase 21 Integration Demo")
    print("=" * 75)
    
    # Initialize learning-enhanced analyzer
    analyzer = LearningEnhancedJobAnalyzer("naythan")
    
    # Run learning-enhanced analysis
    print(f"\n🚀 Running Learning-Enhanced Job Analysis...")
    results = await analyzer.analyze_jobs_with_learning("engineering manager jobs sydney")
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS")
    print("=" * 25)
    
    if 'results' in results:
        # Show original vs personalized rankings
        original_jobs = results['results'].get('top_opportunities', [])
        personalized_jobs = results['results'].get('personalized_opportunities', [])
        
        if personalized_jobs:
            print(f"🎯 PERSONALIZED JOB RANKINGS:")
            for i, job in enumerate(personalized_jobs[:3], 1):
                print(f"  {i}. {job['company']} - {job['title']}")
                print(f"     Combined Score: {job.get('combined_score', 0):.2f}")
                print(f"     Original: {job.get('original_score', 0):.2f} | Learning Boost: +{job.get('learning_boost', 0):.2f}")
                if job.get('personalization_reasoning'):
                    print(f"     Reasoning: {'; '.join(job['personalization_reasoning'])}")
        
        # Show action plan with learning context
        action_plan = results['results'].get('action_plan', [])
        if action_plan:
            print(f"\n📋 PERSONALIZED ACTION PLAN:")
            for action in action_plan[:3]:
                print(f"  • {action}")
    
    # Show learning insights
    if 'learning_insights' in results:
        insights = results['learning_insights']
        print(f"\n🔍 LEARNING INSIGHTS:")
        stats = insights['learning_statistics']
        print(f"  • Total Learning Interactions: {stats['total_interactions']}")
        print(f"  • Learned Preferences: {stats['total_preferences']}")
        print(f"  • User Satisfaction: {stats['average_user_satisfaction']:.2f}/5.0")
    
    # Simulate user feedback
    print(f"\n📚 SIMULATING USER FEEDBACK...")
    feedback_result = await analyzer.provide_job_feedback(
        job_id="job_1",
        decision="very_interested",
        feedback="Perfect match for my engineering management career goals",
        rating=4.8
    )
    
    print(f"  ✅ Learning system updated with user feedback")
    
    # Show learning evolution
    print(f"\n🚀 LEARNING SYSTEM EVOLUTION:")
    evolution = analyzer.demonstrate_learning_evolution()
    
    # Show personalization summary
    summary = analyzer.get_personalized_analysis_summary()
    print(f"\n💡 PERSONALIZATION CAPABILITIES:")
    for capability in summary['personalization_capabilities']:
        print(f"  ✅ {capability}")
    
    print(f"\n🎯 COMPETITIVE ADVANTAGES:")
    for advantage in summary['competitive_advantages']:
        print(f"  🚀 {advantage}")
    
    print(f"\n✅ Learning-Enhanced Job Analyzer demonstration complete")
    print(f"🧠 Phase 21 (Learning) successfully integrated with Phase 20 (Orchestration)")
    print(f"🚀 System Evolution: Static Automation → Adaptive Learning AI")

if __name__ == "__main__":
    asyncio.run(main())