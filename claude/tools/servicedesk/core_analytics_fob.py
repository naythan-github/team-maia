#!/usr/bin/env python3
"""
ServiceDesk Core Analytics FOB - Foundational operational metrics
================================================================

Core operational analytics including:
- Documentation quality assessment (team and individual)
- First Call Resolution (FCR) analysis
- Ownership change and handoff patterns  
- Work type distribution and performance
- Executive reporting and benchmarking

Author: Maia Data Analyst Agent
Version: 2.0.0
Created: 2025-01-24
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
try:
    from .base_fob import ServiceDeskBase
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase

class CoreAnalytics(ServiceDeskBase):
    """
    Core ServiceDesk operational analytics engine.
    
    Provides foundational analysis of ticketing systems including:
    - Documentation quality assessment (team and individual patterns)
    - First Call Resolution (FCR) rates and performance metrics
    - Ownership change and handoff analysis
    - Work type distribution and categorization
    - Executive summary and benchmarking
    """
    
    def run_analysis(self, include_individual_patterns=False):
        """
        Run complete core analysis pipeline.
        
        Args:
            include_individual_patterns: Include individual documentation pattern analysis
            
        Returns:
            Dictionary containing all analysis results
        """
        print("🚀 Starting Core ServiceDesk Analytics")
        print("=" * 50)
        
        self.load_data()
        
        # Run core analysis modules
        self.analyze_documentation_quality()
        self.analyze_team_documentation_quality()
        if include_individual_patterns:
            self.analyze_individual_documentation_patterns()
        self.analyze_first_call_resolution()
        self.analyze_ownership_patterns()
        self.analyze_work_distribution()
        
        # Generate executive summary
        self.generate_executive_summary()
        
        print("\n✅ Core Analysis Complete!")
        return self.analysis_results
    
    def analyze_documentation_quality(self):
        """Analyze overall documentation completeness and quality."""
        print("\n📝 Analyzing Documentation Quality...")
        
        # Basic documentation metrics
        has_description = self.df['description'].notna() & (self.df['description'].str.strip() != '')
        description_length = self.df['description'].fillna('').str.len()
        
        total_tickets = len(self.df)
        with_description = has_description.sum()
        blank_descriptions = total_tickets - with_description
        detailed_descriptions = (description_length > self.config['detailed_description_min_chars']).sum()
        
        # Calculate percentages
        desc_percentage = (with_description / total_tickets) * 100
        blank_percentage = (blank_descriptions / total_tickets) * 100
        detailed_percentage = (detailed_descriptions / total_tickets) * 100
        
        # Work type breakdown
        work_types = self.categorize_work_types()
        doc_by_type = {}
        
        for work_type in work_types['incident_category'].unique():
            type_df = work_types[work_types['incident_category'] == work_type]
            type_has_desc = type_df['description'].notna() & (type_df['description'].str.strip() != '')
            type_desc_rate = (type_has_desc.sum() / len(type_df)) * 100 if len(type_df) > 0 else 0
            doc_by_type[work_type] = {
                'total_tickets': len(type_df),
                'documentation_rate': type_desc_rate
            }
        
        self.analysis_results['documentation'] = {
            'total_tickets': total_tickets,
            'with_description': with_description,
            'blank_descriptions': blank_descriptions,
            'detailed_descriptions': detailed_descriptions,
            'documentation_rate': desc_percentage,
            'blank_rate': blank_percentage,
            'detailed_rate': detailed_percentage,
            'by_work_type': doc_by_type,
            'target_achievement': desc_percentage / self.config['documentation_target'] * 100,
            'benchmark_comparison': desc_percentage - self.config['industry_benchmarks']['documentation_rate']
        }
        
        return self.analysis_results['documentation']
    
    def analyze_team_documentation_quality(self):
        """Comprehensive team documentation quality analysis."""
        print("\n📊 Analyzing Team Documentation Quality...")
        
        # Team documentation statistics query
        team_query = """
        SELECT 
            user_full_name,
            user_username,
            COUNT(*) as total_tickets,
            COUNT(CASE WHEN description IS NULL OR TRIM(description) = '' THEN 1 END) as blank_descriptions,
            COUNT(CASE WHEN description IS NOT NULL AND TRIM(description) != '' THEN 1 END) as has_description,
            COUNT(CASE WHEN LENGTH(TRIM(description)) > 50 THEN 1 END) as detailed_descriptions,
            ROUND((COUNT(CASE WHEN description IS NOT NULL AND TRIM(description) != '' THEN 1 END) * 100.0 / COUNT(*)), 1) as pct_with_description,
            ROUND((COUNT(CASE WHEN LENGTH(TRIM(description)) > 50 THEN 1 END) * 100.0 / COUNT(*)), 1) as pct_detailed,
            SUM(hours) as total_hours,
            ROUND(AVG(hours), 3) as avg_hours
        FROM tickets 
        WHERE category = ?
        GROUP BY user_full_name, user_username
        HAVING total_tickets >= ?
        ORDER BY pct_with_description DESC
        """
        
        min_tickets = self.config.get('min_tickets_for_analysis', 50)
        team_docs = self.execute_query_df(team_query, [self.config['category_filter'], min_tickets])
        
        # Documentation quality categories
        def categorize_quality(pct):
            if pct >= 70: return 'Excellent'
            elif pct >= 50: return 'Good'  
            elif pct >= 30: return 'Poor'
            elif pct >= 10: return 'Very Poor'
            else: return 'Critical'
        
        team_docs['quality_rating'] = team_docs['pct_with_description'].apply(categorize_quality)
        
        # Quality distribution
        quality_dist = team_docs.groupby('quality_rating').agg({
            'user_full_name': 'count',
            'pct_with_description': 'mean',
            'total_hours': 'sum'
        }).round(1)
        
        # Top and bottom performers
        top_documenters = team_docs.nlargest(5, 'pct_with_description')[
            ['user_full_name', 'total_tickets', 'pct_with_description', 'pct_detailed', 'total_hours']
        ].to_dict('records')
        
        bottom_documenters = team_docs.nsmallest(5, 'pct_with_description')[
            ['user_full_name', 'total_tickets', 'pct_with_description', 'pct_detailed', 'total_hours']
        ].to_dict('records')
        
        # High-volume poor documenters (productivity vs quality)
        productivity_risk = team_docs[
            (team_docs['total_hours'] > 150) & (team_docs['pct_with_description'] < 30)
        ][['user_full_name', 'total_hours', 'pct_with_description']].to_dict('records')
        
        # Team variance analysis
        team_variance = {
            'total_staff': len(team_docs),
            'avg_documentation_rate': team_docs['pct_with_description'].mean(),
            'std_documentation_rate': team_docs['pct_with_description'].std(),
            'coefficient_of_variation': (team_docs['pct_with_description'].std() / team_docs['pct_with_description'].mean()) * 100,
            'range': team_docs['pct_with_description'].max() - team_docs['pct_with_description'].min()
        }
        
        self.analysis_results['team_documentation'] = {
            'team_statistics': team_docs.to_dict('records'),
            'quality_distribution': quality_dist.to_dict(),
            'top_performers': top_documenters,
            'bottom_performers': bottom_documenters,
            'productivity_risk_staff': productivity_risk,
            'team_variance': team_variance,
            'analysis_date': datetime.now().isoformat()
        }
        
        return self.analysis_results['team_documentation']
    
    def analyze_individual_documentation_patterns(self, username=None):
        """Detailed individual documentation pattern analysis."""
        print(f"\n🔍 Analyzing Individual Documentation Patterns...")
        
        if username:
            users_to_analyze = [username]
        else:
            # Get top 10 users by ticket volume
            volume_query = """
            SELECT user_username 
            FROM tickets 
            WHERE category = ?
            GROUP BY user_username 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
            """
            users_to_analyze = [row[0] for row in self.execute_query(volume_query, [self.config['category_filter']])]
        
        individual_patterns = {}
        
        for user in users_to_analyze:
            # Individual user analysis
            user_query = """
            SELECT 
                COUNT(*) as total_tickets,
                SUM(hours) as total_hours,
                AVG(hours) as avg_hours,
                MIN(hours) as min_hours,
                MAX(hours) as max_hours,
                COUNT(CASE WHEN description IS NULL OR TRIM(description) = '' THEN 1 END) as blank_descriptions,
                COUNT(CASE WHEN TRIM(description) LIKE 'Email Sent to %' THEN 1 END) as email_templates,
                COUNT(CASE WHEN LENGTH(TRIM(description)) < 30 AND description IS NOT NULL AND TRIM(description) != '' THEN 1 END) as brief_descriptions,
                COUNT(CASE WHEN LENGTH(TRIM(description)) BETWEEN 30 AND 100 THEN 1 END) as medium_descriptions,
                COUNT(CASE WHEN LENGTH(TRIM(description)) > 100 THEN 1 END) as detailed_descriptions
            FROM tickets 
            WHERE user_username = ? AND category = ?
            """
            
            user_stats = self.execute_query(user_query, [user, self.config['category_filter']])[0]
            
            # Time variance for user
            time_variance_query = """
            SELECT 
                ROUND(AVG((hours - (SELECT AVG(hours) FROM tickets WHERE user_username = ? AND hours > 0)) * 
                          (hours - (SELECT AVG(hours) FROM tickets WHERE user_username = ? AND hours > 0))), 3) as variance,
                ROUND(SQRT(AVG((hours - (SELECT AVG(hours) FROM tickets WHERE user_username = ? AND hours > 0)) * 
                              (hours - (SELECT AVG(hours) FROM tickets WHERE user_username = ? AND hours > 0)))), 3) as std_dev
            FROM tickets 
            WHERE user_username = ? AND hours > 0 AND category = ?
            """
            
            variance_stats = self.execute_query(time_variance_query, 
                                              [user, user, user, user, user, self.config['category_filter']])[0]
            
            # Work type distribution
            type_query = """
            SELECT 
                type,
                COUNT(*) as count,
                ROUND(AVG(hours), 3) as avg_hours,
                COUNT(CASE WHEN description IS NOT NULL AND TRIM(description) != '' THEN 1 END) as documented_count
            FROM tickets 
            WHERE user_username = ? AND category = ?
            GROUP BY type
            ORDER BY count DESC
            """
            
            work_types = self.execute_query(type_query, [user, self.config['category_filter']])
            
            # Get user's full name
            name_query = "SELECT DISTINCT user_full_name FROM tickets WHERE user_username = ? LIMIT 1"
            full_name_result = self.execute_query(name_query, [user])
            full_name = full_name_result[0][0] if full_name_result else user
            
            individual_patterns[user] = {
                'full_name': full_name,
                'basic_stats': {
                    'total_tickets': user_stats[0],
                    'total_hours': user_stats[1],
                    'avg_hours': round(user_stats[2], 3),
                    'min_hours': user_stats[3],
                    'max_hours': user_stats[4],
                    'hours_variance': variance_stats[0],
                    'hours_std_dev': variance_stats[1],
                    'coefficient_of_variation': round((variance_stats[1] / user_stats[2]) * 100, 1) if user_stats[2] > 0 else 0
                },
                'documentation_patterns': {
                    'blank_descriptions': user_stats[5],
                    'email_templates': user_stats[6],
                    'brief_descriptions': user_stats[7],
                    'medium_descriptions': user_stats[8],
                    'detailed_descriptions': user_stats[9],
                    'documentation_rate': round((user_stats[0] - user_stats[5]) / user_stats[0] * 100, 1) if user_stats[0] > 0 else 0
                },
                'work_type_distribution': [
                    {
                        'type': wt[0],
                        'count': wt[1], 
                        'avg_hours': wt[2],
                        'documented_count': wt[3],
                        'documentation_rate': round(wt[3] / wt[1] * 100, 1) if wt[1] > 0 else 0
                    } for wt in work_types
                ]
            }
        
        self.analysis_results['individual_patterns'] = individual_patterns
        return individual_patterns
    
    def analyze_first_call_resolution(self):
        """Analyze First Call Resolution rates and patterns."""
        print("\n🎯 Analyzing First Call Resolution...")
        
        # Group by incident (CRM ID) to analyze resolution patterns
        incident_stats = self.df.groupby('crm_id').agg({
            'user_username': ['count', 'nunique'],
            'hours': 'sum'
        })
        
        incident_stats.columns = ['total_entries', 'unique_users', 'total_hours']
        incident_stats = incident_stats.reset_index()
        
        # Calculate FCR metrics
        incident_stats['is_fcr'] = incident_stats['total_entries'] == 1
        incident_stats['has_handoffs'] = incident_stats['unique_users'] > 1
        
        total_incidents = len(incident_stats)
        fcr_incidents = incident_stats['is_fcr'].sum()
        handoff_incidents = incident_stats['has_handoffs'].sum()
        
        fcr_percentage = (fcr_incidents / total_incidents) * 100
        handoff_percentage = (handoff_incidents / total_incidents) * 100
        
        # FCR by work type
        work_types = self.categorize_work_types()
        fcr_by_type = {}
        
        for work_type in work_types['incident_category'].unique():
            type_incidents = work_types[work_types['incident_category'] == work_type]['crm_id'].unique()
            type_stats = incident_stats[incident_stats['crm_id'].isin(type_incidents)]
            
            if len(type_stats) > 0:
                type_fcr_rate = (type_stats['is_fcr'].sum() / len(type_stats)) * 100
                fcr_by_type[work_type] = {
                    'total_incidents': len(type_stats),
                    'fcr_incidents': type_stats['is_fcr'].sum(),
                    'fcr_rate': type_fcr_rate
                }
        
        self.analysis_results['fcr'] = {
            'total_incidents': total_incidents,
            'fcr_incidents': fcr_incidents,
            'fcr_rate': fcr_percentage,
            'handoff_incidents': handoff_incidents,
            'handoff_rate': handoff_percentage,
            'multiple_updates': total_incidents - fcr_incidents,
            'multiple_updates_rate': 100 - fcr_percentage,
            'by_work_type': fcr_by_type,
            'target_achievement': fcr_percentage / self.config['fcr_target'] * 100,
            'benchmark_comparison': fcr_percentage - self.config['industry_benchmarks']['fcr_rate']
        }
        
        return self.analysis_results['fcr']
    
    def analyze_ownership_patterns(self):
        """Analyze ownership changes and handoff patterns."""
        print("\n🔄 Analyzing Ownership Patterns...")
        
        # Calculate ownership changes per incident
        ownership_data = []
        handoff_patterns = defaultdict(int)
        
        for crm_id, group in self.df.groupby('crm_id'):
            users = group['user_username'].tolist()
            changes = 0
            
            # Count ownership changes
            for i in range(1, len(users)):
                if users[i] != users[i-1]:
                    changes += 1
                    handoff_patterns[f'{users[i-1]} → {users[i]}'] += 1
            
            ownership_data.append({
                'crm_id': crm_id,
                'total_entries': len(users),
                'ownership_changes': changes,
                'unique_users': len(set(users))
            })
        
        ownership_df = pd.DataFrame(ownership_data)
        
        # Calculate statistics
        no_changes = (ownership_df['ownership_changes'] == 0).sum()
        one_change = (ownership_df['ownership_changes'] == 1).sum()
        multi_changes = (ownership_df['ownership_changes'] >= 2).sum()
        excessive_updates = (ownership_df['total_entries'] >= self.config['excessive_updates_threshold']).sum()
        
        total_incidents = len(ownership_df)
        
        # Top handoff patterns
        top_handoffs = dict(sorted(handoff_patterns.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # User handoff analysis
        handoff_recipients = defaultdict(int)
        handoff_originators = defaultdict(int)
        
        for pattern, count in handoff_patterns.items():
            if ' → ' in pattern:
                originator, recipient = pattern.split(' → ')
                handoff_originators[originator] += count
                handoff_recipients[recipient] += count
        
        self.analysis_results['ownership'] = {
            'total_incidents': total_incidents,
            'no_changes': no_changes,
            'one_change': one_change,
            'multi_changes': multi_changes,
            'excessive_updates': excessive_updates,
            'no_changes_rate': (no_changes / total_incidents) * 100,
            'handoff_rate': ((one_change + multi_changes) / total_incidents) * 100,
            'excessive_updates_rate': (excessive_updates / total_incidents) * 100,
            'top_handoff_patterns': top_handoffs,
            'top_recipients': dict(sorted(handoff_recipients.items(), key=lambda x: x[1], reverse=True)[:10]),
            'top_originators': dict(sorted(handoff_originators.items(), key=lambda x: x[1], reverse=True)[:10]),
            'benchmark_comparison': ((one_change + multi_changes) / total_incidents) * 100 - self.config['industry_benchmarks']['handoff_rate']
        }
        
        return self.analysis_results['ownership']
    
    def analyze_work_distribution(self):
        """Analyze work type distribution and performance."""
        print("\n📊 Analyzing Work Distribution...")
        
        work_types = self.categorize_work_types()
        
        # Calculate distribution
        distribution = work_types['incident_category'].value_counts()
        total_tickets = len(work_types)
        
        # Performance by work type
        type_performance = {}
        for work_type, count in distribution.items():
            type_df = work_types[work_types['incident_category'] == work_type]
            avg_hours = type_df['hours'].mean()
            
            type_performance[work_type] = {
                'count': count,
                'percentage': (count / total_tickets) * 100,
                'avg_hours': avg_hours
            }
        
        # Calculate NOC vs Non-NOC split
        noc_categories = ['NOC: Site Down', 'NOC: Link Down', 'NOC: Other']
        noc_count = sum(distribution.get(cat, 0) for cat in noc_categories)
        noc_percentage = (noc_count / total_tickets) * 100
        
        # Categorization quality
        other_count = distribution.get('Other/Miscellaneous', 0)
        properly_categorized = total_tickets - other_count
        categorization_rate = (properly_categorized / total_tickets) * 100
        
        self.analysis_results['work_distribution'] = {
            'total_tickets': total_tickets,
            'distribution': type_performance,
            'noc_total': noc_count,
            'noc_percentage': noc_percentage,
            'other_miscellaneous': other_count,
            'categorization_rate': categorization_rate,
            'avg_resolution_time': work_types['hours'].mean()
        }
        
        return self.analysis_results['work_distribution']
    
    def generate_executive_summary(self):
        """Generate executive summary report."""
        print("\n📋 Generating Executive Summary...")
        
        if not self.analysis_results:
            print("❌ No analysis results available. Run analysis methods first.")
            return None
        
        doc_results = self.analysis_results.get('documentation', {})
        team_doc_results = self.analysis_results.get('team_documentation', {})
        fcr_results = self.analysis_results.get('fcr', {})
        ownership_results = self.analysis_results.get('ownership', {})
        work_results = self.analysis_results.get('work_distribution', {})
        
        # Team documentation insights
        team_doc_insights = {}
        if team_doc_results:
            team_variance = team_doc_results.get('team_variance', {})
            quality_dist = team_doc_results.get('quality_distribution', {})
            team_doc_insights = {
                'total_staff_analyzed': team_variance.get('total_staff', 0),
                'avg_team_documentation_rate': round(team_variance.get('avg_documentation_rate', 0), 1),
                'documentation_cv': round(team_variance.get('coefficient_of_variation', 0), 1),
                'quality_categories': {k: v.get('user_full_name', 0) for k, v in quality_dist.items()},
                'high_risk_performers': len(team_doc_results.get('productivity_risk_staff', []))
            }
        
        # Generate summary
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'data_period': f"{self.get_date_range()[0]} to {self.get_date_range()[1]}",
            'total_tickets': len(self.df),
            'total_incidents': fcr_results.get('total_incidents', 0),
            'key_metrics': {
                'documentation_rate': doc_results.get('documentation_rate', 0),
                'team_documentation_variance': team_doc_insights.get('documentation_cv', 0),
                'fcr_rate': fcr_results.get('fcr_rate', 0),
                'handoff_rate': ownership_results.get('handoff_rate', 0),
                'excessive_updates_rate': ownership_results.get('excessive_updates_rate', 0),
                'categorization_rate': work_results.get('categorization_rate', 0)
            },
            'team_documentation_insights': team_doc_insights,
            'performance_assessment': self._assess_performance(),
            'critical_issues': self._identify_critical_issues(),
            'recommendations': self._generate_recommendations()
        }
        
        self.analysis_results['executive_summary'] = summary
        return summary
    
    def _assess_performance(self):
        """Assess overall performance against targets and benchmarks."""
        doc_rate = self.analysis_results.get('documentation', {}).get('documentation_rate', 0)
        fcr_rate = self.analysis_results.get('fcr', {}).get('fcr_rate', 0)
        handoff_rate = self.analysis_results.get('ownership', {}).get('handoff_rate', 0)
        
        # Performance scoring (0-100)
        doc_score = min(100, (doc_rate / self.config['documentation_target']) * 100)
        fcr_score = min(100, (fcr_rate / self.config['fcr_target']) * 100)
        handoff_score = max(0, 100 - (handoff_rate / self.config['handoff_threshold']) * 100)
        
        overall_score = (doc_score + fcr_score + handoff_score) / 3
        
        if overall_score >= 80:
            assessment = "Excellent"
        elif overall_score >= 60:
            assessment = "Good"
        elif overall_score >= 40:
            assessment = "Needs Improvement"
        else:
            assessment = "Critical"
        
        return {
            'overall_score': overall_score,
            'assessment': assessment,
            'component_scores': {
                'documentation': doc_score,
                'fcr': fcr_score,
                'process_stability': handoff_score
            }
        }
    
    def _identify_critical_issues(self):
        """Identify critical issues requiring immediate attention."""
        issues = []
        
        doc_rate = self.analysis_results.get('documentation', {}).get('documentation_rate', 0)
        fcr_rate = self.analysis_results.get('fcr', {}).get('fcr_rate', 0)
        handoff_rate = self.analysis_results.get('ownership', {}).get('handoff_rate', 0)
        excessive_rate = self.analysis_results.get('ownership', {}).get('excessive_updates_rate', 0)
        
        if doc_rate < 60:
            issues.append({
                'type': 'Documentation Crisis',
                'severity': 'Critical',
                'description': f'Only {doc_rate:.1f}% of tickets have documentation',
                'impact': 'Knowledge loss, poor handoffs, compliance risk'
            })
        
        if fcr_rate < 50:
            issues.append({
                'type': 'Low First Call Resolution',
                'severity': 'High',
                'description': f'FCR rate of {fcr_rate:.1f}% is below industry standard',
                'impact': 'Increased costs, poor customer experience'
            })
        
        if handoff_rate > 25:
            issues.append({
                'type': 'Excessive Handoffs',
                'severity': 'High',
                'description': f'{handoff_rate:.1f}% of incidents involve handoffs',
                'impact': 'Process inefficiency, potential ping-ponging'
            })
        
        if excessive_rate > 15:
            issues.append({
                'type': 'Process Churn',
                'severity': 'Medium',
                'description': f'{excessive_rate:.1f}% of incidents have 5+ updates',
                'impact': 'Resource waste, complexity indicators'
            })
        
        return issues
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        doc_rate = self.analysis_results.get('documentation', {}).get('documentation_rate', 0)
        fcr_rate = self.analysis_results.get('fcr', {}).get('fcr_rate', 0)
        
        if doc_rate < 70:
            recommendations.append({
                'priority': 'High',
                'category': 'Documentation',
                'action': 'Implement mandatory description requirements',
                'timeline': 'Week 1',
                'expected_impact': 'Improve knowledge retention and handoff quality'
            })
        
        if fcr_rate < 60:
            recommendations.append({
                'priority': 'High',
                'category': 'Process Improvement',
                'action': 'FCR improvement program with training focus',
                'timeline': 'Month 1',
                'expected_impact': 'Reduce repeat contacts and improve efficiency'
            })
        
        recommendations.append({
            'priority': 'Medium',
            'category': 'Monitoring',
            'action': 'Implement weekly operational metrics dashboard',
            'timeline': 'Month 2',
            'expected_impact': 'Proactive issue identification and trend monitoring'
        })
        
        return recommendations
    
    def print_executive_report(self):
        """Print formatted executive report to console."""
        if 'executive_summary' not in self.analysis_results:
            print("❌ Executive summary not available. Run analysis first.")
            return
        
        summary = self.analysis_results['executive_summary']
        
        print("\n" + "="*80)
        print("📊 SERVICEDESK CORE ANALYTICS REPORT")
        print("="*80)
        
        print(f"\n🗓️  Analysis Period: {summary['data_period']}")
        print(f"📊 Total Tickets: {summary['total_tickets']:,}")
        print(f"🎫 Total Incidents: {summary['total_incidents']:,}")
        
        print(f"\n🎯 KEY PERFORMANCE METRICS:")
        metrics = summary['key_metrics']
        print(f"• Documentation Rate: {metrics['documentation_rate']:.1f}%")
        print(f"• First Call Resolution: {metrics['fcr_rate']:.1f}%")
        print(f"• Handoff Rate: {metrics['handoff_rate']:.1f}%")
        print(f"• Excessive Updates: {metrics['excessive_updates_rate']:.1f}%")
        print(f"• Categorization Quality: {metrics['categorization_rate']:.1f}%")
        
        # Team documentation insights
        if summary.get('team_documentation_insights'):
            team_insights = summary['team_documentation_insights']
            print(f"\n👥 TEAM DOCUMENTATION INSIGHTS:")
            print(f"• Staff Analyzed: {team_insights['total_staff_analyzed']}")
            print(f"• Average Documentation Rate: {team_insights['avg_team_documentation_rate']:.1f}%")
            print(f"• Documentation Variance (CV): {team_insights['documentation_cv']:.1f}%")
            print(f"• High-Risk Performers: {team_insights['high_risk_performers']}")
        
        assessment = summary['performance_assessment']
        print(f"\n🏆 OVERALL ASSESSMENT: {assessment['assessment']}")
        print(f"📈 Performance Score: {assessment['overall_score']:.1f}/100")
        
        if summary['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(summary['critical_issues'])} identified):")
            for issue in summary['critical_issues']:
                print(f"• {issue['type']}: {issue['description']}")
        
        if summary['recommendations']:
            print(f"\n🎯 RECOMMENDATIONS ({len(summary['recommendations'])} actions):")
            for rec in summary['recommendations']:
                print(f"• {rec['priority']} Priority: {rec['action']} ({rec['timeline']})")


def main():
    """Main CLI interface for Core Analytics FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Core Analytics FOB')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--individual-patterns', action='store_true', help='Include individual documentation patterns')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with CoreAnalytics(database_path=args.database) as analyzer:
            results = analyzer.run_analysis(include_individual_patterns=args.individual_patterns)
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print report unless quiet mode
            if not args.quiet:
                analyzer.print_executive_report()
        
        return 0
        
    except Exception as e:
        print(f"❌ Core analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())