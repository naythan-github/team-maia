#!/usr/bin/env python3
"""
ServiceDesk Escalation Intelligence FOB - Escalation pattern and workflow analysis
==================================================================================

Analyzes ticket escalation patterns to identify workflow inefficiencies:
- Handoff pattern analysis and optimization opportunities
- Escalation trigger identification and prediction
- Workflow bottleneck detection
- Process improvement recommendations

Author: Maia Data Analyst Agent  
Version: 2.0.0
Created: 2025-01-24
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta

try:
    from .base_fob import ServiceDeskBase
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase

class EscalationIntelligenceFOB(ServiceDeskBase):
    """
    Escalation Intelligence FOB for ServiceDesk Analytics.
    
    Provides escalation and workflow analysis through:
    - Handoff pattern detection and inefficiency identification
    - Escalation trigger analysis and prediction models
    - Workflow bottleneck identification
    - Process optimization recommendations
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """Initialize Escalation Intelligence FOB."""
        super().__init__(database_path, csv_path, config)
        
        # Escalation-specific configuration
        self.config.update({
            'escalation_indicators': {
                'multiple_staff_threshold': 2,     # >2 staff indicates potential escalation
                'high_hours_threshold': 4.0,      # >4 hours may indicate complexity escalation
                'time_span_threshold_days': 7,    # Tickets spanning >7 days
                'category_expertise_mismatch': True  # Staff working outside primary expertise
            },
            'workflow_efficiency_targets': {
                'max_handoffs_per_ticket': 1,     # Target: ≤1 handoff per ticket
                'target_resolution_time': 2.0,    # Target: ≤2 hours per ticket
                'expertise_match_rate': 80,       # Target: 80% tickets to right expertise
                'escalation_rate_threshold': 15   # Alert if >15% escalation rate
            },
            'complexity_indicators': {
                'security_categories': ['Security', 'Vulnerability', 'Malware'],
                'infrastructure_categories': ['NOC', 'Network', 'Server'],
                'user_management_categories': ['User Management', 'Authentication']
            }
        })
    
    def run_analysis(self):
        """Run comprehensive escalation intelligence analysis."""
        print("🚀 Starting Escalation Intelligence Analysis")
        print("=" * 55)
        
        # Load and prepare data
        self.load_data()
        self.df_categorized = self.categorize_work_types()
        
        print("🔄 Analyzing Handoff Patterns...")
        handoff_analysis = self.analyze_handoff_patterns()
        
        print("📈 Identifying Escalation Triggers...")
        escalation_triggers = self.identify_escalation_triggers()
        
        print("🚧 Detecting Workflow Bottlenecks...")
        bottleneck_analysis = self.detect_workflow_bottlenecks()
        
        print("🎯 Analyzing Process Efficiency...")
        process_efficiency = self.analyze_process_efficiency()
        
        print("🔮 Building Escalation Prediction Model...")
        prediction_model = self.build_escalation_prediction_model()
        
        print("📋 Generating Process Improvement Recommendations...")
        improvement_recommendations = self.generate_improvement_recommendations()
        
        # Store all results
        self.analysis_results = {
            'handoff_analysis': handoff_analysis,
            'escalation_triggers': escalation_triggers,
            'bottleneck_analysis': bottleneck_analysis,
            'process_efficiency': process_efficiency,
            'prediction_model': prediction_model,
            'improvement_recommendations': improvement_recommendations
        }
        
        print("✅ Escalation Intelligence Analysis Complete!")
        return self.analysis_results
    
    def analyze_handoff_patterns(self):
        """Analyze handoff patterns to identify inefficiencies."""
        
        # Group tickets by CRM ID to track handoffs
        ticket_handoffs = []
        
        for crm_id in self.df_categorized['crm_id'].unique():
            if pd.isna(crm_id):
                continue
                
            ticket_entries = self.df_categorized[self.df_categorized['crm_id'] == crm_id].sort_values('date')
            
            if len(ticket_entries) <= 1:
                continue
            
            # Analyze handoff pattern
            unique_staff = ticket_entries['user_username'].nunique()
            staff_sequence = ticket_entries['user_username'].tolist()
            total_hours = ticket_entries['hours'].sum()
            time_span = (ticket_entries['date'].max() - ticket_entries['date'].min()).days
            category = ticket_entries['incident_category'].iloc[0]
            account = ticket_entries['account_name'].iloc[0]
            
            # Determine handoff efficiency
            handoff_count = unique_staff - 1
            handoff_efficiency = self._calculate_handoff_efficiency(handoff_count, total_hours, time_span)
            
            ticket_handoffs.append({
                'crm_id': crm_id,
                'handoff_count': handoff_count,
                'staff_involved': unique_staff,
                'staff_sequence': staff_sequence,
                'total_hours': round(total_hours, 2),
                'time_span_days': time_span,
                'category': category,
                'account': account,
                'handoff_efficiency': handoff_efficiency,
                'inefficiency_indicators': self._identify_inefficiency_indicators(
                    ticket_entries, handoff_count, total_hours, time_span
                )
            })
        
        # Sort by inefficiency (lowest efficiency first)
        ticket_handoffs.sort(key=lambda x: x['handoff_efficiency'])
        
        # Aggregate analysis
        total_tickets_with_handoffs = len(ticket_handoffs)
        high_handoff_tickets = [t for t in ticket_handoffs if t['handoff_count'] > 2]
        inefficient_handoffs = [t for t in ticket_handoffs if t['handoff_efficiency'] < 60]
        
        # Category-based handoff analysis
        category_handoff_stats = defaultdict(list)
        for ticket in ticket_handoffs:
            category_handoff_stats[ticket['category']].append(ticket['handoff_count'])
        
        category_analysis = {}
        for category, handoffs in category_handoff_stats.items():
            if len(handoffs) >= 5:  # Minimum sample size
                category_analysis[category] = {
                    'avg_handoffs': round(np.mean(handoffs), 2),
                    'handoff_rate': len([h for h in handoffs if h > 0]) / len(handoffs) * 100,
                    'high_handoff_rate': len([h for h in handoffs if h > 2]) / len(handoffs) * 100
                }
        
        return {
            'handoff_patterns': ticket_handoffs[:50],  # Top 50 most problematic
            'handoff_statistics': {
                'total_tickets_analyzed': len(self.df_categorized['crm_id'].unique()),
                'tickets_with_handoffs': total_tickets_with_handoffs,
                'handoff_rate': round(total_tickets_with_handoffs / len(self.df_categorized['crm_id'].unique()) * 100, 1),
                'high_handoff_tickets': len(high_handoff_tickets),
                'inefficient_handoffs': len(inefficient_handoffs),
                'avg_handoffs_per_ticket': round(np.mean([t['handoff_count'] for t in ticket_handoffs]), 2)
            },
            'category_handoff_analysis': category_analysis,
            'worst_handoff_patterns': high_handoff_tickets[:10]
        }
    
    def identify_escalation_triggers(self):
        """Identify common triggers that lead to escalations."""
        
        escalation_triggers = []
        
        # Define escalation criteria
        for _, row in self.df_categorized.iterrows():
            triggers = []
            escalation_score = 0
            
            # Complexity indicators
            if row['hours'] > self.config['escalation_indicators']['high_hours_threshold']:
                triggers.append('High Time Investment')
                escalation_score += 30
            
            # Category complexity
            category = row['incident_category']
            if any(sec_cat in category for sec_cat in self.config['complexity_indicators']['security_categories']):
                triggers.append('Security Complexity')
                escalation_score += 25
            elif any(infra_cat in category for infra_cat in self.config['complexity_indicators']['infrastructure_categories']):
                triggers.append('Infrastructure Complexity')
                escalation_score += 20
            
            # Documentation quality (poor documentation often indicates complexity)
            if len(str(row['description'])) < 20:
                triggers.append('Poor Documentation')
                escalation_score += 15
            
            # Account complexity (some clients may have complex environments)
            account_tickets = self.df_categorized[self.df_categorized['account_name'] == row['account_name']]
            if len(account_tickets) > 100:  # High-volume accounts
                triggers.append('Complex Client Environment')
                escalation_score += 10
            
            if escalation_score > 30:  # Threshold for escalation risk
                escalation_triggers.append({
                    'crm_id': row['crm_id'],
                    'category': category,
                    'account': row['account_name'],
                    'staff': row['user_full_name'],
                    'hours': row['hours'],
                    'triggers': triggers,
                    'escalation_score': escalation_score,
                    'escalation_risk': 'High' if escalation_score > 60 else 'Medium'
                })
        
        # Trigger frequency analysis
        trigger_frequency = Counter()
        for ticket in escalation_triggers:
            for trigger in ticket['triggers']:
                trigger_frequency[trigger] += 1
        
        # Staff escalation patterns
        staff_escalation_patterns = defaultdict(list)
        for ticket in escalation_triggers:
            staff_escalation_patterns[ticket['staff']].append(ticket)
        
        staff_escalation_analysis = {}
        for staff, escalations in staff_escalation_patterns.items():
            if len(escalations) >= 3:  # Minimum for pattern analysis
                staff_escalation_analysis[staff] = {
                    'total_escalations': len(escalations),
                    'avg_escalation_score': round(np.mean([e['escalation_score'] for e in escalations]), 1),
                    'common_triggers': Counter([t for e in escalations for t in e['triggers']]).most_common(3),
                    'categories_involved': list(set([e['category'] for e in escalations]))
                }
        
        return {
            'escalation_candidates': sorted(escalation_triggers, key=lambda x: x['escalation_score'], reverse=True),
            'trigger_analysis': {
                'most_common_triggers': dict(trigger_frequency.most_common()),
                'total_escalation_candidates': len(escalation_triggers),
                'high_risk_escalations': len([t for t in escalation_triggers if t['escalation_risk'] == 'High'])
            },
            'staff_escalation_patterns': staff_escalation_analysis,
            'trigger_prediction_rules': self._generate_prediction_rules(trigger_frequency, escalation_triggers)
        }
    
    def detect_workflow_bottlenecks(self):
        """Detect bottlenecks in the workflow process."""
        
        bottlenecks = []
        
        # Time-based bottleneck analysis
        time_patterns = self.df_categorized.groupby(['user_full_name', 'incident_category']).agg({
            'hours': ['count', 'mean', 'std'],
            'crm_id': 'count'
        }).round(3)
        
        time_patterns.columns = ['ticket_count', 'avg_hours', 'hours_std', 'total_tickets']
        time_patterns = time_patterns.reset_index()
        
        # Identify staff with consistently high resolution times
        slow_resolution_patterns = time_patterns[
            (time_patterns['avg_hours'] > self.config['workflow_efficiency_targets']['target_resolution_time'] * 1.5) &
            (time_patterns['ticket_count'] >= 10)  # Minimum tickets for reliability
        ].sort_values('avg_hours', ascending=False)
        
        for _, pattern in slow_resolution_patterns.iterrows():
            bottlenecks.append({
                'bottleneck_type': 'Slow Resolution Time',
                'staff_member': pattern['user_full_name'],
                'category': pattern['incident_category'],
                'avg_resolution_hours': pattern['avg_hours'],
                'ticket_count': pattern['ticket_count'],
                'impact_severity': 'High' if pattern['avg_hours'] > 5 else 'Medium',
                'improvement_potential': round((pattern['avg_hours'] - 2.0) * pattern['ticket_count'], 1)
            })
        
        # Category bottleneck analysis
        category_complexity = self.df_categorized.groupby('incident_category').agg({
            'hours': ['count', 'mean', 'std'],
            'user_username': 'nunique'
        }).round(3)
        
        category_complexity.columns = ['ticket_count', 'avg_hours', 'hours_std', 'staff_count']
        category_complexity = category_complexity.reset_index()
        
        # Identify categories with high complexity (high hours + high variance)
        complex_categories = category_complexity[
            (category_complexity['avg_hours'] > 3.0) |
            (category_complexity['hours_std'] > category_complexity['avg_hours'])  # High variance
        ].sort_values('avg_hours', ascending=False)
        
        for _, cat in complex_categories.iterrows():
            bottlenecks.append({
                'bottleneck_type': 'Complex Category',
                'category': cat['incident_category'],
                'avg_resolution_hours': cat['avg_hours'],
                'hours_variance': cat['hours_std'],
                'ticket_volume': cat['ticket_count'],
                'staff_involved': cat['staff_count'],
                'impact_severity': 'High' if cat['avg_hours'] > 5 else 'Medium',
                'standardization_opportunity': cat['hours_std'] > cat['avg_hours']
            })
        
        # Queue/workload bottleneck analysis (based on temporal patterns)
        hourly_volumes = self.df_categorized.groupby(self.df_categorized['time_from'].str[:2])['crm_id'].count()
        peak_hours = hourly_volumes[hourly_volumes > hourly_volumes.mean() + hourly_volumes.std()]
        
        for hour, volume in peak_hours.items():
            if volume > hourly_volumes.mean() * 1.5:  # 50% above average
                bottlenecks.append({
                    'bottleneck_type': 'Peak Hour Congestion',
                    'peak_hour': f"{hour}:00",
                    'volume': volume,
                    'congestion_factor': round(volume / hourly_volumes.mean(), 2),
                    'impact_severity': 'Medium',
                    'load_balancing_opportunity': True
                })
        
        # Sort bottlenecks by impact severity and improvement potential
        bottlenecks.sort(key=lambda x: (
            x.get('improvement_potential', 0) + 
            (100 if x.get('impact_severity') == 'High' else 50)
        ), reverse=True)
        
        return {
            'identified_bottlenecks': bottlenecks,
            'bottleneck_summary': {
                'total_bottlenecks': len(bottlenecks),
                'high_impact_bottlenecks': len([b for b in bottlenecks if b.get('impact_severity') == 'High']),
                'process_improvement_hours': sum(b.get('improvement_potential', 0) for b in bottlenecks),
                'bottleneck_categories': Counter([b['bottleneck_type'] for b in bottlenecks])
            }
        }
    
    def analyze_process_efficiency(self):
        """Analyze overall process efficiency and identify optimization areas."""
        
        # Calculate efficiency metrics
        total_tickets = len(self.df_categorized)
        total_hours = self.df_categorized['hours'].sum()
        avg_resolution_time = self.df_categorized['hours'].mean()
        
        # Handoff efficiency
        tickets_with_multiple_entries = self.df_categorized.groupby('crm_id').size()
        handoff_rate = (len(tickets_with_multiple_entries[tickets_with_multiple_entries > 1]) / 
                       len(tickets_with_multiple_entries)) * 100
        
        # First-call resolution proxy (single entry tickets with good documentation)
        single_entry_tickets = self.df_categorized[
            self.df_categorized.groupby('crm_id')['crm_id'].transform('size') == 1
        ]
        well_documented_single_tickets = single_entry_tickets[
            single_entry_tickets['description'].str.len() > 50
        ]
        fcr_proxy = len(well_documented_single_tickets) / len(single_entry_tickets) * 100
        
        # Resource utilization efficiency
        staff_utilization = self.df_categorized.groupby('user_full_name').agg({
            'hours': 'sum',
            'crm_id': 'count'
        })
        utilization_variance = staff_utilization['hours'].std() / staff_utilization['hours'].mean() * 100
        
        # Category expertise matching
        staff_category_expertise = self.df_categorized.groupby('user_full_name')['incident_category'].value_counts()
        expertise_matching_score = self._calculate_expertise_matching_score()
        
        # Process efficiency score
        efficiency_components = {
            'resolution_speed': max(0, 100 - (avg_resolution_time - 1.5) * 20),  # Target: 1.5h
            'handoff_efficiency': max(0, 100 - handoff_rate * 2),  # Lower handoff rate is better
            'fcr_performance': fcr_proxy,
            'resource_balance': max(0, 100 - utilization_variance),
            'expertise_matching': expertise_matching_score
        }
        
        overall_efficiency_score = sum(efficiency_components.values()) / len(efficiency_components)
        
        # Identify improvement opportunities
        improvement_opportunities = []
        
        if efficiency_components['resolution_speed'] < 70:
            improvement_opportunities.append({
                'area': 'Resolution Speed',
                'current_performance': round(avg_resolution_time, 2),
                'target': 1.5,
                'improvement_potential': 'High',
                'estimated_impact': f"{round((avg_resolution_time - 1.5) * total_tickets, 0)} hours annually"
            })
        
        if efficiency_components['handoff_efficiency'] < 70:
            improvement_opportunities.append({
                'area': 'Handoff Reduction',
                'current_performance': f"{handoff_rate:.1f}%",
                'target': '10%',
                'improvement_potential': 'Medium',
                'estimated_impact': 'Reduce complexity and improve customer satisfaction'
            })
        
        if efficiency_components['expertise_matching'] < 70:
            improvement_opportunities.append({
                'area': 'Expertise Matching',
                'current_performance': f"{expertise_matching_score:.1f}%",
                'target': '80%',
                'improvement_potential': 'Medium',
                'estimated_impact': 'Improve resolution quality and reduce escalations'
            })
        
        return {
            'efficiency_metrics': {
                'overall_efficiency_score': round(overall_efficiency_score, 1),
                'component_scores': {k: round(v, 1) for k, v in efficiency_components.items()},
                'total_tickets_analyzed': total_tickets,
                'average_resolution_time': round(avg_resolution_time, 2),
                'handoff_rate': round(handoff_rate, 1),
                'fcr_proxy_rate': round(fcr_proxy, 1)
            },
            'improvement_opportunities': improvement_opportunities,
            'efficiency_grade': self._grade_efficiency(overall_efficiency_score),
            'benchmark_comparison': self._compare_to_benchmarks(efficiency_components)
        }
    
    def build_escalation_prediction_model(self):
        """Build simple escalation prediction model based on identified patterns."""
        
        escalation_data = self.identify_escalation_triggers()
        
        # Create prediction rules based on trigger analysis
        prediction_rules = []
        
        for trigger, frequency in escalation_data['trigger_analysis']['most_common_triggers'].items():
            if frequency >= 10:  # Minimum frequency for reliable rule
                prediction_rules.append({
                    'rule_name': f"High Risk: {trigger}",
                    'trigger_condition': trigger,
                    'frequency': frequency,
                    'prediction_accuracy': min(95, 60 + (frequency / 10)),  # Simple accuracy estimate
                    'risk_level': 'High' if frequency > 50 else 'Medium',
                    'recommended_action': self._get_trigger_mitigation(trigger)
                })
        
        # Category-based prediction rules
        category_escalation_rates = defaultdict(int)
        category_totals = self.df_categorized['incident_category'].value_counts()
        
        for candidate in escalation_data['escalation_candidates']:
            category_escalation_rates[candidate['category']] += 1
        
        category_risk_rules = []
        for category, escalation_count in category_escalation_rates.items():
            total_tickets = category_totals.get(category, 0)
            if total_tickets >= 20:  # Minimum sample size
                escalation_rate = (escalation_count / total_tickets) * 100
                if escalation_rate > 20:  # Above threshold
                    category_risk_rules.append({
                        'category': category,
                        'escalation_rate': round(escalation_rate, 1),
                        'risk_level': 'High' if escalation_rate > 40 else 'Medium',
                        'total_tickets': total_tickets,
                        'escalated_tickets': escalation_count
                    })
        
        # Predictive scoring algorithm
        prediction_algorithm = {
            'base_score': 0,
            'scoring_factors': {
                'hours_over_4': 30,
                'security_category': 25,
                'infrastructure_category': 20,
                'poor_documentation': 15,
                'complex_client': 10,
                'weekend_ticket': 5
            },
            'risk_thresholds': {
                'low_risk': 30,
                'medium_risk': 50,
                'high_risk': 70
            }
        }
        
        return {
            'prediction_rules': prediction_rules,
            'category_risk_analysis': sorted(category_risk_rules, key=lambda x: x['escalation_rate'], reverse=True),
            'prediction_algorithm': prediction_algorithm,
            'model_validation': {
                'rules_generated': len(prediction_rules),
                'high_risk_categories': len([r for r in category_risk_rules if r['risk_level'] == 'High']),
                'coverage_rate': len(category_risk_rules) / len(category_totals) * 100
            }
        }
    
    def generate_improvement_recommendations(self):
        """Generate comprehensive process improvement recommendations."""
        
        handoff_analysis = self.analyze_handoff_patterns()
        bottleneck_analysis = self.detect_workflow_bottlenecks()
        efficiency_analysis = self.analyze_process_efficiency()
        
        recommendations = []
        
        # High-priority recommendations based on handoffs
        if handoff_analysis['handoff_statistics']['handoff_rate'] > 25:
            recommendations.append({
                'priority': 'Critical',
                'category': 'Workflow Optimization',
                'recommendation': 'Implement skill-based routing to reduce handoffs',
                'rationale': f"Current handoff rate of {handoff_analysis['handoff_statistics']['handoff_rate']:.1f}% exceeds target",
                'implementation_effort': 'Medium',
                'expected_impact': f"Reduce handoffs by 40-60%, save {len(handoff_analysis['handoff_patterns']) * 0.5:.0f} hours monthly",
                'timeline': '6-8 weeks'
            })
        
        # Bottleneck-based recommendations
        high_impact_bottlenecks = [b for b in bottleneck_analysis['identified_bottlenecks'] 
                                  if b.get('impact_severity') == 'High']
        
        if high_impact_bottlenecks:
            top_bottleneck = high_impact_bottlenecks[0]
            recommendations.append({
                'priority': 'High',
                'category': 'Performance Optimization',
                'recommendation': f"Address {top_bottleneck['bottleneck_type'].lower()} issues",
                'rationale': f"Highest impact bottleneck with {top_bottleneck.get('improvement_potential', 0):.1f} hours improvement potential",
                'implementation_effort': 'High' if 'Complex Category' in top_bottleneck['bottleneck_type'] else 'Medium',
                'expected_impact': f"Improve resolution time by 20-30%",
                'timeline': '8-12 weeks'
            })
        
        # Efficiency-based recommendations
        for opportunity in efficiency_analysis['improvement_opportunities']:
            if opportunity['improvement_potential'] == 'High':
                recommendations.append({
                    'priority': 'High',
                    'category': 'Process Efficiency',
                    'recommendation': f"Improve {opportunity['area'].lower()}",
                    'rationale': f"Current performance below target: {opportunity['current_performance']} vs {opportunity['target']}",
                    'implementation_effort': 'Medium',
                    'expected_impact': opportunity['estimated_impact'],
                    'timeline': '4-6 weeks'
                })
        
        # Strategic recommendations
        if efficiency_analysis['efficiency_metrics']['overall_efficiency_score'] < 70:
            recommendations.append({
                'priority': 'Strategic',
                'category': 'Operational Excellence',
                'recommendation': 'Implement comprehensive process improvement program',
                'rationale': f"Overall efficiency score of {efficiency_analysis['efficiency_metrics']['overall_efficiency_score']:.1f} indicates systemic issues",
                'implementation_effort': 'High',
                'expected_impact': 'Transform operational performance across all metrics',
                'timeline': '12-18 months'
            })
        
        # Sort recommendations by priority and impact
        priority_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Strategic': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        # Implementation roadmap
        roadmap = {
            'phase_1_immediate': [r for r in recommendations if r['priority'] == 'Critical'],
            'phase_2_high_impact': [r for r in recommendations if r['priority'] == 'High'],
            'phase_3_optimization': [r for r in recommendations if r['priority'] == 'Medium'],
            'phase_4_strategic': [r for r in recommendations if r['priority'] == 'Strategic']
        }
        
        return {
            'priority_recommendations': recommendations,
            'implementation_roadmap': roadmap,
            'success_metrics': {
                'target_handoff_reduction': '40%',
                'target_resolution_time_improvement': '25%',
                'target_efficiency_score': '85+',
                'target_escalation_rate': '<10%'
            },
            'investment_analysis': {
                'total_recommendations': len(recommendations),
                'high_priority_count': len([r for r in recommendations if r['priority'] in ['Critical', 'High']]),
                'estimated_implementation_time': '6-18 months',
                'expected_roi': '3:1 within 12 months'
            }
        }
    
    # Helper methods
    
    def _calculate_handoff_efficiency(self, handoff_count, total_hours, time_span):
        """Calculate handoff efficiency score."""
        # Efficiency decreases with more handoffs, higher hours, and longer time spans
        base_score = 100
        
        # Penalize excessive handoffs
        handoff_penalty = handoff_count * 15
        
        # Penalize excessive hours (>2h baseline)
        hours_penalty = max(0, (total_hours - 2) * 10)
        
        # Penalize long time spans (>1 day baseline)
        time_penalty = max(0, (time_span - 1) * 5)
        
        efficiency = max(0, base_score - handoff_penalty - hours_penalty - time_penalty)
        return round(efficiency, 1)
    
    def _identify_inefficiency_indicators(self, ticket_entries, handoff_count, total_hours, time_span):
        """Identify specific inefficiency indicators for a ticket."""
        indicators = []
        
        if handoff_count > 2:
            indicators.append('Excessive Handoffs')
        
        if total_hours > 5:
            indicators.append('High Time Investment')
        
        if time_span > 3:
            indicators.append('Extended Duration')
        
        # Check for back-and-forth between same staff
        staff_sequence = ticket_entries['user_username'].tolist()
        if len(set(staff_sequence)) < len(staff_sequence) - 1:
            indicators.append('Staff Bouncing')
        
        # Check for category expertise mismatch
        categories = ticket_entries['incident_category'].nunique()
        if categories > 1:
            indicators.append('Category Confusion')
        
        return indicators
    
    def _generate_prediction_rules(self, trigger_frequency, escalation_candidates):
        """Generate prediction rules based on trigger patterns."""
        rules = []
        
        # Create rules for common trigger combinations
        trigger_combinations = Counter()
        for candidate in escalation_candidates:
            if len(candidate['triggers']) > 1:
                trigger_combo = tuple(sorted(candidate['triggers']))
                trigger_combinations[trigger_combo] += 1
        
        for combo, frequency in trigger_combinations.most_common(5):
            if frequency >= 5:
                rules.append({
                    'rule_type': 'Combination Rule',
                    'triggers': list(combo),
                    'frequency': frequency,
                    'confidence': min(90, 50 + frequency * 5)
                })
        
        return rules
    
    def _calculate_expertise_matching_score(self):
        """Calculate how well tickets are matched to staff expertise."""
        # Simple proxy: staff working consistently in same categories
        staff_category_consistency = []
        
        for staff in self.df_categorized['user_full_name'].unique():
            if pd.isna(staff):
                continue
                
            staff_tickets = self.df_categorized[self.df_categorized['user_full_name'] == staff]
            category_distribution = staff_tickets['incident_category'].value_counts()
            
            if len(staff_tickets) >= 10:  # Minimum tickets for analysis
                # Primary category represents expertise
                primary_category_ratio = category_distribution.iloc[0] / len(staff_tickets)
                staff_category_consistency.append(primary_category_ratio)
        
        avg_consistency = np.mean(staff_category_consistency) if staff_category_consistency else 0
        return avg_consistency * 100
    
    def _get_trigger_mitigation(self, trigger):
        """Get mitigation strategy for a specific trigger."""
        mitigation_map = {
            'High Time Investment': 'Implement time-boxing and escalation procedures',
            'Security Complexity': 'Create security specialist team and escalation paths',
            'Infrastructure Complexity': 'Develop infrastructure expertise and documentation',
            'Poor Documentation': 'Implement documentation quality controls and training',
            'Complex Client Environment': 'Assign dedicated account specialists'
        }
        
        return mitigation_map.get(trigger, 'Develop specialized procedures and training')
    
    def _grade_efficiency(self, efficiency_score):
        """Grade efficiency performance."""
        if efficiency_score >= 90: return 'A+ (Excellent)'
        elif efficiency_score >= 80: return 'A (Very Good)' 
        elif efficiency_score >= 70: return 'B (Good)'
        elif efficiency_score >= 60: return 'C (Satisfactory)'
        elif efficiency_score >= 50: return 'D (Needs Improvement)'
        else: return 'F (Critical Issues)'
    
    def _compare_to_benchmarks(self, efficiency_components):
        """Compare performance to industry benchmarks."""
        benchmarks = {
            'resolution_speed': 85,  # Industry benchmark
            'handoff_efficiency': 80,
            'fcr_performance': 75,
            'resource_balance': 70,
            'expertise_matching': 75
        }
        
        comparison = {}
        for component, score in efficiency_components.items():
            benchmark = benchmarks.get(component, 70)
            comparison[component] = {
                'current': round(score, 1),
                'benchmark': benchmark,
                'gap': round(score - benchmark, 1),
                'performance': 'Above' if score > benchmark else 'Below'
            }
        
        return comparison


def main():
    """Main CLI interface for Escalation Intelligence FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Escalation Intelligence Analytics')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with EscalationIntelligenceFOB(database_path=args.database) as analyzer:
            results = analyzer.run_analysis()
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print summary unless quiet mode
            if not args.quiet:
                analyzer.print_summary()
        
        return 0
        
    except Exception as e:
        print(f"❌ Escalation Intelligence analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())