#!/usr/bin/env python3
# NOTE: DEMO FILE - Message bus imports deprecated, use Swarm framework instead
# See claude/tools/orchestration/agent_swarm.py for current orchestration patterns
"""
Professional Performance Analytics - Work performance tracking and optimization
================================================================================

Analyzes work patterns, productivity metrics, and provides insights for
performance optimization and professional development.

Author: Maia System
Version: 2.0.0
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
import asyncio
from collections import defaultdict

# Import existing Maia infrastructure with proper error handling
try:
    from claude.tools.intelligent_work_context_predictor import get_work_context_predictor, WorkScenario
except ImportError:
    # Graceful fallback for missing intelligent_work_context_predictor
    def get_work_context_predictor():
        return None
    
    class WorkScenario:
        pass

try:
    from claude.tools.contextual_memory_learning_system import get_memory_system, MemoryType
except ImportError:
    # Graceful fallback for missing contextual_memory_learning_system
    def get_memory_system():
        return None
    
    class MemoryType:
        pass

# DEPRECATED: Message bus replaced by Swarm framework
# Graceful fallback for missing agent_message_bus
def get_message_bus():
    return None

class MessageType:
    pass

class MessagePriority:
    pass

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    focus_score: float
    productivity_score: float 
    context_switches: int
    deep_work_duration: float
    task_completion_rate: float
    stress_indicators: Dict[str, float]
    work_quality_score: float

@dataclass  
class ProductivityInsight:
    """Productivity insight data structure"""
    insight_type: str
    title: str
    description: str
    confidence: float
    recommended_actions: List[str]
    impact_score: float

class ProfessionalPerformanceAnalytics:
    """
    Professional Performance Analytics System
    Tracks and analyzes work performance patterns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the performance analytics system"""
        self.config = config or {}
        self.metrics_history = []
        self.insights_cache = {}
        
    def track_performance_metric(self, metrics: PerformanceMetrics) -> None:
        """Track a performance metric data point"""
        self.metrics_history.append(metrics)
        
        # Keep only last 30 days of data
        cutoff_date = datetime.now() - timedelta(days=30)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp >= cutoff_date]
    
    def analyze_productivity_trends(self, days_back: int = 7) -> List[ProductivityInsight]:
        """Analyze productivity trends over specified time period"""
        if not self.metrics_history:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_date]
        
        if len(recent_metrics) < 2:
            return []
        
        insights = []
        
        # Analyze productivity trend
        productivity_scores = [m.productivity_score for m in recent_metrics]
        if len(productivity_scores) > 1:
            trend = self._calculate_trend(productivity_scores)
            if abs(trend) > 0.1:  # Significant trend
                insight = ProductivityInsight(
                    insight_type="productivity_trend",
                    title=f"Productivity {'increasing' if trend > 0 else 'decreasing'}",
                    description=f"Your productivity has been {'improving' if trend > 0 else 'declining'} over the last {days_back} days",
                    confidence=min(abs(trend) * 2, 1.0),
                    recommended_actions=self._get_productivity_recommendations(trend),
                    impact_score=abs(trend)
                )
                insights.append(insight)
        
        # Analyze focus patterns
        focus_scores = [m.focus_score for m in recent_metrics]
        avg_focus = statistics.mean(focus_scores) if focus_scores else 0
        if avg_focus < 0.6:  # Low focus threshold
            insight = ProductivityInsight(
                insight_type="focus_issue",
                title="Focus challenges detected",
                description=f"Your average focus score is {avg_focus:.1%}, indicating potential concentration issues",
                confidence=0.8,
                recommended_actions=[
                    "Consider time-blocking techniques",
                    "Reduce interruptions during deep work",
                    "Take regular breaks using Pomodoro technique"
                ],
                impact_score=0.7
            )
            insights.append(insight)
        
        return insights
    
    def generate_performance_report(self, days_back: int = 7) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No performance data available"}
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_date]
        
        if not recent_metrics:
            return {"error": f"No data available for last {days_back} days"}
        
        # Calculate averages
        avg_productivity = statistics.mean([m.productivity_score for m in recent_metrics])
        avg_focus = statistics.mean([m.focus_score for m in recent_metrics])
        avg_completion_rate = statistics.mean([m.task_completion_rate for m in recent_metrics])
        total_deep_work = sum([m.deep_work_duration for m in recent_metrics])
        
        # Get insights
        insights = self.analyze_productivity_trends(days_back)
        
        return {
            "report_period": f"{days_back} days",
            "metrics_summary": {
                "average_productivity": avg_productivity,
                "average_focus": avg_focus,
                "average_completion_rate": avg_completion_rate,
                "total_deep_work_hours": total_deep_work,
                "data_points": len(recent_metrics)
            },
            "insights": [asdict(insight) for insight in insights],
            "recommendations": self._generate_recommendations(recent_metrics),
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope for a series of values"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _get_productivity_recommendations(self, trend: float) -> List[str]:
        """Get recommendations based on productivity trend"""
        if trend > 0:
            return [
                "Keep up the great work!",
                "Consider documenting what's working well",
                "Share successful strategies with team members"
            ]
        else:
            return [
                "Review recent changes to your workflow",
                "Consider reducing context switching",
                "Focus on high-impact tasks first",
                "Evaluate your work environment for distractions"
            ]
    
    def _generate_recommendations(self, recent_metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate general recommendations based on metrics"""
        recommendations = []
        
        if recent_metrics:
            avg_context_switches = statistics.mean([m.context_switches for m in recent_metrics])
            if avg_context_switches > 20:  # High context switching
                recommendations.append("Reduce task switching by time-blocking similar activities")
            
            avg_deep_work = statistics.mean([m.deep_work_duration for m in recent_metrics])
            if avg_deep_work < 2.0:  # Less than 2 hours deep work per day
                recommendations.append("Schedule longer blocks for deep work activities")
        
        return recommendations

# Factory function
def create_analytics_system(config: Optional[Dict[str, Any]] = None) -> ProfessionalPerformanceAnalytics:
    """Create a performance analytics system instance"""
    return ProfessionalPerformanceAnalytics(config)

if __name__ == "__main__":
    # Test the analytics system
    analytics = create_analytics_system()
    
    # Sample metrics
    sample_metrics = PerformanceMetrics(
        timestamp=datetime.now(),
        focus_score=0.75,
        productivity_score=0.8,
        context_switches=15,
        deep_work_duration=3.5,
        task_completion_rate=0.85,
        stress_indicators={"interruptions": 0.3, "workload": 0.6},
        work_quality_score=0.9
    )
    
    analytics.track_performance_metric(sample_metrics)
    report = analytics.generate_performance_report(1)
    print(f"Performance report generated: {report.get('metrics_summary', {})}")