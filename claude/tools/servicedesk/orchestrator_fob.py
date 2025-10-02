#!/usr/bin/env python3
"""
ServiceDesk Orchestrator FOB - Coordinates multiple FOB analyses
================================================================

Orchestrator that coordinates and combines results from multiple specialized FOBs:
- Core Analytics (documentation, FCR, handoffs)
- Temporal Analytics (time patterns, capacity planning)
- Future FOBs (client intelligence, automation opportunities, etc.)

Provides unified reporting and cross-domain insights.

Author: Maia Data Analyst Agent
Version: 2.0.0
Created: 2025-01-24
"""

import json
from datetime import datetime
from pathlib import Path
try:
    from .base_fob import ServiceDeskBase
    from .core_analytics_fob import CoreAnalytics
    from .temporal_analytics_fob import TemporalAnalytics
    from .client_intelligence_fob import ClientIntelligenceFOB
    from .automation_intelligence_fob import AutomationIntelligenceFOB
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase
    from claude.tools.servicedesk.core_analytics_fob import CoreAnalytics
    from temporal_analytics_fob import TemporalAnalytics
    from client_intelligence_fob import ClientIntelligenceFOB
    from automation_intelligence_fob import AutomationIntelligenceFOB

class ServiceDeskOrchestrator(ServiceDeskBase):
    """
    ServiceDesk Analysis Orchestrator.
    
    Coordinates multiple specialized FOBs and provides:
    - Unified analysis execution
    - Cross-domain insights and correlations
    - Comprehensive executive reporting
    - Integrated dashboard data preparation
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """
        Initialize ServiceDesk Orchestrator.
        
        Args:
            database_path: Path to SQLite database
            csv_path: Path to CSV file
            config: Configuration dictionary
        """
        super().__init__(database_path, csv_path, config)
        
        # Initialize specialized FOBs
        self.core_analytics = CoreAnalytics(database_path, csv_path, config)
        self.temporal_analytics = TemporalAnalytics(database_path, csv_path, config)
        self.client_intelligence = ClientIntelligenceFOB(database_path, csv_path, config)
        self.automation_intelligence = AutomationIntelligenceFOB(database_path, csv_path, config)
        
        # Registry of available FOBs
        self.fob_registry = {
            'core': self.core_analytics,
            'temporal': self.temporal_analytics,
            'client': self.client_intelligence,
            'automation': self.automation_intelligence
        }
        
        # Cross-domain insights storage
        self.cross_domain_insights = {}
    
    def run_comprehensive_analysis(self, include_modules=None, include_individual_patterns=False):
        """
        Run coordinated analysis across multiple FOBs.
        
        Args:
            include_modules: List of modules to include ['core', 'temporal'] or None for all
            include_individual_patterns: Include individual documentation patterns
            
        Returns:
            Comprehensive results from all FOBs
        """
        print("🚀 Starting ServiceDesk Orchestrated Analysis")
        print("=" * 60)
        
        # Determine which modules to run
        if include_modules is None:
            modules_to_run = list(self.fob_registry.keys())
        else:
            modules_to_run = [m for m in include_modules if m in self.fob_registry]
        
        print(f"📋 Running modules: {', '.join(modules_to_run)}")
        
        # Load data once for all FOBs
        self.load_data()
        
        # Run each FOB analysis
        fob_results = {}
        
        if 'core' in modules_to_run:
            print("\n🔧 Running Core Analytics...")
            fob_results['core'] = self.core_analytics.run_analysis(include_individual_patterns)
        
        if 'temporal' in modules_to_run:
            print("\n⏰ Running Temporal Analytics...")
            fob_results['temporal'] = self.temporal_analytics.run_analysis()
        
        if 'client' in modules_to_run:
            print("\n👥 Running Client Intelligence...")
            fob_results['client'] = self.client_intelligence.run_analysis()
        
        if 'automation' in modules_to_run:
            print("\n🤖 Running Automation Intelligence...")
            fob_results['automation'] = self.automation_intelligence.run_analysis()
        
        # Perform cross-domain analysis
        self.analyze_cross_domain_insights(fob_results)
        
        # Generate unified summary
        self.generate_unified_summary(fob_results)
        
        # Store all results
        self.analysis_results = {
            'fob_results': fob_results,
            'cross_domain_insights': self.cross_domain_insights,
            'unified_summary': self.analysis_results.get('unified_summary', {})
        }
        
        print("\n✅ Orchestrated Analysis Complete!")
        return self.analysis_results
    
    def analyze_cross_domain_insights(self, fob_results):
        """
        Analyze correlations and insights across different FOB domains.
        
        Args:
            fob_results: Results from all FOB analyses
        """
        print("\n🔗 Analyzing Cross-Domain Insights...")
        
        core_results = fob_results.get('core', {})
        temporal_results = fob_results.get('temporal', {})
        
        insights = {}
        
        # Documentation Quality vs Temporal Patterns
        if core_results and temporal_results:
            insights['documentation_temporal_correlation'] = self._analyze_documentation_time_correlation(
                core_results, temporal_results
            )
        
        # Performance vs Capacity Correlation
        if core_results and temporal_results:
            insights['performance_capacity_correlation'] = self._analyze_performance_capacity_correlation(
                core_results, temporal_results
            )
        
        # Team Efficiency vs Time Patterns
        if core_results and temporal_results:
            insights['team_temporal_efficiency'] = self._analyze_team_temporal_patterns(
                core_results, temporal_results
            )
        
        # Workload Distribution vs Quality Patterns
        if core_results and temporal_results:
            insights['workload_quality_patterns'] = self._analyze_workload_quality_correlation(
                core_results, temporal_results
            )
        
        self.cross_domain_insights = insights
        return insights
    
    def _analyze_documentation_time_correlation(self, core_results, temporal_results):
        """Analyze correlation between documentation quality and time patterns."""
        
        # Get documentation quality metrics
        doc_rate = core_results.get('documentation', {}).get('documentation_rate', 0)
        team_doc_variance = core_results.get('team_documentation', {}).get('team_variance', {}).get('coefficient_of_variation', 0)
        
        # Get temporal efficiency metrics
        peak_degradation = temporal_results.get('response_time_patterns', {}).get('degradation_analysis', {}).get('degradation_factor', 1.0)
        capacity_utilization = temporal_results.get('capacity_utilization', {}).get('utilization_summary', {}).get('avg_utilization_rate', 0)
        
        # Correlation analysis
        correlation_score = self._calculate_correlation_score([
            (doc_rate, 50, 'higher_better'),  # Documentation rate vs 50% baseline
            (team_doc_variance, 50, 'lower_better'),  # Documentation variance vs 50% baseline
            (peak_degradation, 1.5, 'lower_better'),  # Peak degradation vs 1.5x baseline
            (capacity_utilization, 85, 'optimal_range')  # Capacity utilization vs 85% optimal
        ])
        
        return {
            'correlation_strength': correlation_score,
            'key_finding': self._interpret_doc_time_correlation(doc_rate, peak_degradation, capacity_utilization),
            'documentation_efficiency_impact': {
                'low_doc_rate': doc_rate < 40,
                'high_peak_degradation': peak_degradation > 1.5,
                'utilization_stress': capacity_utilization > 95,
                'compound_impact': (doc_rate < 40) and (peak_degradation > 1.5)
            },
            'recommendations': self._generate_doc_time_recommendations(doc_rate, peak_degradation, capacity_utilization)
        }
    
    def _analyze_performance_capacity_correlation(self, core_results, temporal_results):
        """Analyze correlation between performance metrics and capacity utilization."""
        
        # Performance metrics
        fcr_rate = core_results.get('fcr', {}).get('fcr_rate', 0)
        handoff_rate = core_results.get('ownership', {}).get('handoff_rate', 0)
        
        # Capacity metrics
        utilization_rate = temporal_results.get('capacity_utilization', {}).get('utilization_summary', {}).get('avg_utilization_rate', 0)
        overutilized_days = temporal_results.get('capacity_utilization', {}).get('utilization_summary', {}).get('overutilized_days', 0)
        
        # Performance degradation analysis
        performance_score = (fcr_rate / 70) * 100  # Against 70% target
        capacity_stress_score = min(100, utilization_rate)  # Utilization as stress indicator
        
        return {
            'performance_capacity_score': round((performance_score + (100 - capacity_stress_score)) / 2, 1),
            'capacity_impact_on_performance': {
                'fcr_degradation_risk': utilization_rate > 90 and fcr_rate < 60,
                'handoff_increase_risk': utilization_rate > 95 and handoff_rate > 20,
                'quality_stress_indicator': (utilization_rate > 90) and (handoff_rate > 15 or fcr_rate < 65)
            },
            'optimization_opportunities': self._identify_capacity_performance_optimizations(
                fcr_rate, handoff_rate, utilization_rate, overutilized_days
            )
        }
    
    def _analyze_team_temporal_patterns(self, core_results, temporal_results):
        """Analyze team performance patterns across time."""
        
        # Team documentation quality distribution
        team_doc_results = core_results.get('team_documentation', {})
        quality_distribution = team_doc_results.get('quality_distribution', {})
        high_risk_performers = len(team_doc_results.get('productivity_risk_staff', []))
        
        # Temporal efficiency patterns
        weekend_efficiency = temporal_results.get('daily_patterns', {}).get('weekday_vs_weekend', {})
        peak_hour_analysis = temporal_results.get('hourly_patterns', {}).get('peak_analysis', {})
        
        return {
            'team_time_efficiency': {
                'high_performers_count': quality_distribution.get('Excellent', {}).get('user_full_name', 0),
                'critical_performers_count': quality_distribution.get('Critical', {}).get('user_full_name', 0),
                'high_risk_performers': high_risk_performers,
                'weekend_efficiency_delta': weekend_efficiency.get('volume_difference', 0)
            },
            'temporal_team_insights': {
                'peak_hour_stress': peak_hour_analysis.get('peak_volume', 0) > 100,
                'weekend_performance_gap': abs(weekend_efficiency.get('volume_difference', 0)) > 25,
                'capacity_team_mismatch': high_risk_performers > 3 and peak_hour_analysis.get('peak_volume', 0) > 80
            },
            'team_optimization_recommendations': self._generate_team_temporal_recommendations(
                high_risk_performers, weekend_efficiency, peak_hour_analysis
            )
        }
    
    def _analyze_workload_quality_correlation(self, core_results, temporal_results):
        """Analyze correlation between workload patterns and quality metrics."""
        
        # Quality metrics
        doc_rate = core_results.get('documentation', {}).get('documentation_rate', 0)
        fcr_rate = core_results.get('fcr', {}).get('fcr_rate', 0)
        
        # Workload patterns
        volume_volatility = temporal_results.get('weekly_patterns', {}).get('volume_patterns', {}).get('volume_volatility_cv', 0)
        utilization_variance = temporal_results.get('capacity_utilization', {}).get('utilization_summary', {}).get('utilization_variance', 0)
        
        return {
            'workload_stability_impact': {
                'high_volatility': volume_volatility > 30,
                'high_utilization_variance': utilization_variance > 25,
                'quality_correlation': (volume_volatility > 30 and doc_rate < 50) or (utilization_variance > 25 and fcr_rate < 60)
            },
            'workload_quality_score': self._calculate_workload_quality_score(doc_rate, fcr_rate, volume_volatility, utilization_variance),
            'stabilization_recommendations': self._generate_workload_stabilization_recommendations(
                volume_volatility, utilization_variance, doc_rate, fcr_rate
            )
        }
    
    def generate_unified_summary(self, fob_results):
        """Generate comprehensive summary combining all FOB results."""
        print("\n📊 Generating Unified Summary...")
        
        core_results = fob_results.get('core', {})
        temporal_results = fob_results.get('temporal', {})
        
        # Extract key metrics from each domain
        core_metrics = self._extract_core_metrics(core_results)
        temporal_metrics = self._extract_temporal_metrics(temporal_results)
        
        # Calculate unified performance score
        unified_score = self._calculate_unified_performance_score(core_metrics, temporal_metrics)
        
        # Generate strategic insights
        strategic_insights = self._generate_strategic_insights(core_metrics, temporal_metrics)
        
        # Comprehensive recommendations
        unified_recommendations = self._generate_unified_recommendations(core_metrics, temporal_metrics)
        
        unified_summary = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'modules_analyzed': list(fob_results.keys()),
                'data_period': f"{self.get_date_range()[0]} to {self.get_date_range()[1]}",
                'total_tickets': len(self.df) if self.df is not None else 0
            },
            'unified_performance_score': unified_score,
            'domain_metrics': {
                'core_analytics': core_metrics,
                'temporal_analytics': temporal_metrics
            },
            'strategic_insights': strategic_insights,
            'cross_domain_correlations': self.cross_domain_insights,
            'unified_recommendations': unified_recommendations,
            'executive_priorities': self._identify_executive_priorities(core_metrics, temporal_metrics, unified_score)
        }
        
        self.analysis_results['unified_summary'] = unified_summary
        return unified_summary
    
    # Helper methods for cross-domain analysis
    
    def _calculate_correlation_score(self, metric_comparisons):
        """Calculate correlation score based on multiple metric comparisons."""
        total_score = 0
        for metric_value, baseline, comparison_type in metric_comparisons:
            if comparison_type == 'higher_better':
                score = min(100, (metric_value / baseline) * 100)
            elif comparison_type == 'lower_better':
                score = max(0, 100 - ((metric_value - baseline) / baseline * 100))
            else:  # optimal_range
                distance_from_optimal = abs(metric_value - baseline) / baseline
                score = max(0, 100 - (distance_from_optimal * 100))
            total_score += score
        
        return round(total_score / len(metric_comparisons), 1)
    
    def _interpret_doc_time_correlation(self, doc_rate, peak_degradation, capacity_utilization):
        """Interpret documentation and time pattern correlation."""
        if doc_rate < 30 and peak_degradation > 1.8:
            return "Critical: Poor documentation amplifies peak-hour performance degradation"
        elif doc_rate < 50 and capacity_utilization > 90:
            return "High Risk: Low documentation quality under capacity stress"
        elif doc_rate > 70 and peak_degradation < 1.3:
            return "Positive: Good documentation maintains performance during peak hours"
        else:
            return "Moderate: Mixed documentation and temporal performance patterns"
    
    def _generate_doc_time_recommendations(self, doc_rate, peak_degradation, capacity_utilization):
        """Generate recommendations based on documentation-time correlation."""
        recommendations = []
        
        if doc_rate < 40 and peak_degradation > 1.5:
            recommendations.append({
                'priority': 'Critical',
                'action': 'Emergency documentation improvement program',
                'rationale': 'Poor documentation severely impacts peak-hour performance'
            })
        
        if capacity_utilization > 90 and doc_rate < 60:
            recommendations.append({
                'priority': 'High',
                'action': 'Implement mandatory documentation during high-utilization periods',
                'rationale': 'Prevent knowledge loss during capacity stress'
            })
        
        return recommendations
    
    def _identify_capacity_performance_optimizations(self, fcr_rate, handoff_rate, utilization_rate, overutilized_days):
        """Identify capacity and performance optimization opportunities."""
        optimizations = []
        
        if utilization_rate > 95 and fcr_rate < 60:
            optimizations.append({
                'type': 'Capacity Relief',
                'opportunity': 'Reduce utilization to improve FCR',
                'expected_impact': 'FCR improvement of 10-15%'
            })
        
        if overutilized_days > 10 and handoff_rate > 20:
            optimizations.append({
                'type': 'Process Optimization',
                'opportunity': 'Implement peak-hour process streamlining',
                'expected_impact': 'Reduce handoffs by 5-10%'
            })
        
        return optimizations
    
    def _generate_team_temporal_recommendations(self, high_risk_performers, weekend_efficiency, peak_hour_analysis):
        """Generate team and temporal optimization recommendations."""
        recommendations = []
        
        if high_risk_performers > 3:
            recommendations.append({
                'area': 'Team Development',
                'recommendation': 'Prioritize training for high-risk performers',
                'timeline': 'Within 2 weeks'
            })
        
        weekend_gap = abs(weekend_efficiency.get('volume_difference', 0))
        if weekend_gap > 25:
            recommendations.append({
                'area': 'Weekend Operations',
                'recommendation': 'Standardize weekend processes and training',
                'timeline': 'Within 1 month'
            })
        
        return recommendations
    
    def _calculate_workload_quality_score(self, doc_rate, fcr_rate, volume_volatility, utilization_variance):
        """Calculate workload stability and quality score."""
        quality_score = (doc_rate + fcr_rate) / 2
        stability_penalty = (volume_volatility + utilization_variance) / 2
        
        final_score = max(0, quality_score - (stability_penalty * 0.5))
        return round(final_score, 1)
    
    def _generate_workload_stabilization_recommendations(self, volume_volatility, utilization_variance, doc_rate, fcr_rate):
        """Generate workload stabilization recommendations."""
        recommendations = []
        
        if volume_volatility > 30:
            recommendations.append('Implement workload smoothing strategies')
        
        if utilization_variance > 25:
            recommendations.append('Develop flexible staffing models')
        
        if volume_volatility > 30 and doc_rate < 50:
            recommendations.append('Mandatory documentation during volatile periods')
        
        return recommendations
    
    def _extract_core_metrics(self, core_results):
        """Extract key metrics from core analytics results."""
        if not core_results:
            return {}
        
        return {
            'documentation_rate': core_results.get('documentation', {}).get('documentation_rate', 0),
            'fcr_rate': core_results.get('fcr', {}).get('fcr_rate', 0),
            'handoff_rate': core_results.get('ownership', {}).get('handoff_rate', 0),
            'team_doc_variance': core_results.get('team_documentation', {}).get('team_variance', {}).get('coefficient_of_variation', 0),
            'high_risk_performers': len(core_results.get('team_documentation', {}).get('productivity_risk_staff', []))
        }
    
    def _extract_temporal_metrics(self, temporal_results):
        """Extract key metrics from temporal analytics results."""
        if not temporal_results:
            return {}
        
        return {
            'capacity_utilization': temporal_results.get('capacity_utilization', {}).get('utilization_summary', {}).get('avg_utilization_rate', 0),
            'peak_degradation': temporal_results.get('response_time_patterns', {}).get('degradation_analysis', {}).get('degradation_factor', 1.0),
            'volume_volatility': temporal_results.get('weekly_patterns', {}).get('volume_patterns', {}).get('volume_volatility_cv', 0),
            'weekend_efficiency_gap': temporal_results.get('daily_patterns', {}).get('weekday_vs_weekend', {}).get('volume_difference', 0)
        }
    
    def _calculate_unified_performance_score(self, core_metrics, temporal_metrics):
        """Calculate overall performance score across all domains."""
        scores = []
        
        # Core performance scores (0-100)
        if core_metrics:
            doc_score = min(100, core_metrics.get('documentation_rate', 0) / 70 * 100)  # Against 70% target
            fcr_score = min(100, core_metrics.get('fcr_rate', 0) / 70 * 100)  # Against 70% target
            handoff_score = max(0, 100 - (core_metrics.get('handoff_rate', 0) / 15 * 100))  # Against 15% threshold
            scores.extend([doc_score, fcr_score, handoff_score])
        
        # Temporal performance scores (0-100)
        if temporal_metrics:
            capacity_score = 100 - abs(temporal_metrics.get('capacity_utilization', 85) - 85) / 85 * 100  # Against 85% optimal
            stability_score = max(0, 100 - temporal_metrics.get('volume_volatility', 0))  # Lower volatility is better
            efficiency_score = max(0, 100 - (temporal_metrics.get('peak_degradation', 1.0) - 1.0) * 100)  # Lower degradation is better
            scores.extend([capacity_score, stability_score, efficiency_score])
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'overall_score': round(overall_score, 1),
            'performance_grade': self._grade_performance(overall_score),
            'component_scores': {
                'core_analytics': round(sum(scores[:3]) / 3, 1) if len(scores) >= 3 else 0,
                'temporal_analytics': round(sum(scores[3:]) / 3, 1) if len(scores) >= 6 else 0
            }
        }
    
    def _grade_performance(self, score):
        """Grade performance based on unified score."""
        if score >= 90: return 'A+ (Excellent)'
        elif score >= 80: return 'A (Very Good)'
        elif score >= 70: return 'B (Good)'
        elif score >= 60: return 'C (Satisfactory)'
        elif score >= 50: return 'D (Needs Improvement)'
        else: return 'F (Critical Issues)'
    
    def _generate_strategic_insights(self, core_metrics, temporal_metrics):
        """Generate strategic insights from combined analysis."""
        insights = []
        
        # Documentation-Performance Insight
        doc_rate = core_metrics.get('documentation_rate', 0)
        fcr_rate = core_metrics.get('fcr_rate', 0)
        if doc_rate < 50 and fcr_rate < 60:
            insights.append({
                'category': 'Knowledge Management Crisis',
                'insight': 'Poor documentation directly correlates with low FCR performance',
                'business_impact': 'High - affects customer satisfaction and operational costs'
            })
        
        # Capacity-Quality Insight
        utilization = temporal_metrics.get('capacity_utilization', 0)
        handoff_rate = core_metrics.get('handoff_rate', 0)
        if utilization > 90 and handoff_rate > 20:
            insights.append({
                'category': 'Capacity-Quality Trade-off',
                'insight': 'High utilization is degrading service quality through increased handoffs',
                'business_impact': 'Medium - risk of service quality decline and team burnout'
            })
        
        # Stability-Efficiency Insight
        volatility = temporal_metrics.get('volume_volatility', 0)
        if volatility > 35:
            insights.append({
                'category': 'Operational Instability',
                'insight': 'High volume volatility creates inefficiencies across all metrics',
                'business_impact': 'Medium - unpredictable resource needs and inconsistent service levels'
            })
        
        return insights
    
    def _generate_unified_recommendations(self, core_metrics, temporal_metrics):
        """Generate unified recommendations across all domains."""
        recommendations = []
        
        # Priority 1: Critical Issues
        doc_rate = core_metrics.get('documentation_rate', 0)
        if doc_rate < 40:
            recommendations.append({
                'priority': 1,
                'category': 'Documentation Crisis',
                'action': 'Implement emergency documentation improvement program',
                'timeline': '1 week',
                'expected_impact': 'Prevent knowledge loss and improve handoff quality',
                'success_metric': 'Documentation rate >60% within 4 weeks'
            })
        
        # Priority 2: Capacity Management
        utilization = temporal_metrics.get('capacity_utilization', 0)
        if utilization > 95:
            recommendations.append({
                'priority': 2,
                'category': 'Capacity Management',
                'action': 'Scale team or optimize processes to reduce utilization',
                'timeline': '2 weeks',
                'expected_impact': 'Prevent burnout and maintain service quality',
                'success_metric': 'Utilization 80-90% within 6 weeks'
            })
        
        # Priority 3: Process Optimization
        fcr_rate = core_metrics.get('fcr_rate', 0)
        if fcr_rate < 60:
            recommendations.append({
                'priority': 3,
                'category': 'Process Optimization',
                'action': 'Implement FCR improvement program with training focus',
                'timeline': '4 weeks',
                'expected_impact': 'Reduce repeat contacts and improve efficiency',
                'success_metric': 'FCR rate >70% within 8 weeks'
            })
        
        return recommendations
    
    def _identify_executive_priorities(self, core_metrics, temporal_metrics, unified_score):
        """Identify top executive priorities based on analysis."""
        priorities = []
        
        # Determine priority based on business impact and urgency
        score = unified_score.get('overall_score', 0)
        
        if score < 50:
            priorities.append({
                'level': 'CRITICAL',
                'priority': 'Operational Excellence Recovery',
                'description': 'Multiple critical issues requiring immediate intervention',
                'board_impact': 'High - service quality and team sustainability at risk'
            })
        
        high_risk_performers = core_metrics.get('high_risk_performers', 0)
        if high_risk_performers > 3:
            priorities.append({
                'level': 'HIGH',
                'priority': 'Team Performance Management',
                'description': 'Significant number of high-volume, low-quality performers',
                'board_impact': 'Medium - knowledge management and succession planning risk'
            })
        
        utilization = temporal_metrics.get('capacity_utilization', 0)
        if utilization > 90:
            priorities.append({
                'level': 'MEDIUM',
                'priority': 'Capacity Planning',
                'description': 'Team operating at unsustainable utilization levels',
                'board_impact': 'Medium - scalability and growth planning implications'
            })
        
        return priorities
    
    def print_unified_report(self):
        """Print comprehensive unified report."""
        if 'unified_summary' not in self.analysis_results:
            print("❌ Unified summary not available. Run analysis first.")
            return
        
        summary = self.analysis_results['unified_summary']
        
        print("\n" + "="*80)
        print("📊 SERVICEDESK UNIFIED ANALYTICS REPORT")
        print("="*80)
        
        # Analysis metadata
        metadata = summary['analysis_metadata']
        print(f"\n🗓️  Analysis Date: {metadata['analysis_date']}")
        print(f"📊 Data Period: {metadata['data_period']}")
        print(f"🎫 Total Tickets: {metadata['total_tickets']:,}")
        print(f"📋 Modules Analyzed: {', '.join(metadata['modules_analyzed'])}")
        
        # Unified performance score
        perf_score = summary['unified_performance_score']
        print(f"\n🏆 UNIFIED PERFORMANCE ASSESSMENT")
        print(f"Overall Score: {perf_score['overall_score']:.1f}/100")
        print(f"Performance Grade: {perf_score['performance_grade']}")
        print(f"Core Analytics Score: {perf_score['component_scores']['core_analytics']:.1f}/100")
        print(f"Temporal Analytics Score: {perf_score['component_scores']['temporal_analytics']:.1f}/100")
        
        # Strategic insights
        if summary['strategic_insights']:
            print(f"\n💡 STRATEGIC INSIGHTS:")
            for insight in summary['strategic_insights']:
                print(f"• {insight['category']}: {insight['insight']}")
        
        # Executive priorities
        if summary['executive_priorities']:
            print(f"\n🎯 EXECUTIVE PRIORITIES:")
            for priority in summary['executive_priorities']:
                print(f"• {priority['level']}: {priority['priority']}")
                print(f"  {priority['description']}")
        
        # Unified recommendations
        if summary['unified_recommendations']:
            print(f"\n📋 UNIFIED RECOMMENDATIONS:")
            for rec in summary['unified_recommendations']:
                print(f"• Priority {rec['priority']}: {rec['action']} ({rec['timeline']})")
    
    def run_analysis(self):
        """Override base class abstract method - delegates to comprehensive orchestrated analysis."""
        return self.run_comprehensive_analysis(include_modules=None, include_individual_patterns=False)


def main():
    """Main CLI interface for ServiceDesk Orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Orchestrator - Unified Analytics Platform')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--modules', '-m', nargs='+', choices=['core', 'temporal', 'client', 'automation'], 
                       help='Specific modules to run (default: all)')
    parser.add_argument('--individual-patterns', action='store_true', 
                       help='Include individual documentation patterns')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run orchestrated analysis
        with ServiceDeskOrchestrator(database_path=args.database) as orchestrator:
            results = orchestrator.run_comprehensive_analysis(
                include_modules=args.modules,
                include_individual_patterns=args.individual_patterns
            )
            
            # Export results
            if args.output:
                orchestrator.export_results(args.output)
            
            # Print report unless quiet mode
            if not args.quiet:
                orchestrator.print_unified_report()
        
        return 0
        
    except Exception as e:
        print(f"❌ Orchestrated analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())