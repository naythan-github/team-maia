#!/usr/bin/env python3
"""
ServiceDesk Automation Intelligence FOB - Identifies automation opportunities
============================================================================

Analyzes ticket patterns to identify automation opportunities including:
- Repetitive task identification based on titles and descriptions
- Volume-based automation candidates
- Process standardization opportunities
- ROI calculations for automation initiatives

Author: Maia Data Analyst Agent  
Version: 2.0.0
Created: 2025-01-24
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import re
from datetime import datetime, timedelta

try:
    from .base_fob import ServiceDeskBase
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase

class AutomationIntelligenceFOB(ServiceDeskBase):
    """
    Automation Intelligence FOB for ServiceDesk Analytics.
    
    Identifies automation opportunities through:
    - Pattern recognition in ticket titles and descriptions
    - Volume-based repetitive task analysis
    - Time investment vs automation ROI calculations
    - Process standardization recommendations
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """Initialize Automation Intelligence FOB."""
        super().__init__(database_path, csv_path, config)
        
        # Automation-specific configuration
        self.config.update({
            'min_occurrences_for_automation': 20,  # Minimum repetitions to consider automation
            'automation_roi_threshold': 2.0,  # Minimum 2:1 ROI for automation recommendation
            'high_volume_threshold': 50,  # High volume automation candidates
            'automation_development_hours': {  # Estimated development time
                'simple': 8,    # Simple scripts (8 hours)
                'medium': 40,   # Workflow automation (40 hours) 
                'complex': 120  # Complex integrations (120 hours)
            },
            'automation_patterns': {
                # High automation potential patterns
                'password_reset': ['password', 'reset', 'unlock', 'account locked'],
                'user_provisioning': ['new user', 'user setup', 'onboard', 'create account'],
                'license_management': ['license', 'assign', 'remove license', 'software access'],
                'routine_maintenance': ['update', 'patch', 'restart', 'backup'],
                'monitoring_alerts': ['alert', 'monitor', 'threshold', 'fired:'],
                'access_requests': ['access', 'permission', 'folder access', 'drive access'],
                'software_installation': ['install', 'software', 'application', 'program'],
                'hardware_provisioning': ['hardware', 'laptop', 'monitor', 'equipment']
            }
        })
    
    def run_analysis(self):
        """Run comprehensive automation intelligence analysis."""
        print("🚀 Starting Automation Intelligence Analysis")
        print("=" * 55)
        
        # Load and prepare data
        self.load_data()
        self.df_categorized = self.categorize_work_types()
        
        print("🔍 Identifying Repetitive Task Patterns...")
        repetitive_patterns = self.identify_repetitive_patterns()
        
        print("📊 Analyzing Volume-Based Automation Candidates...")
        volume_candidates = self.analyze_volume_based_candidates()
        
        print("💰 Calculating Automation ROI Opportunities...")
        roi_analysis = self.calculate_automation_roi()
        
        print("🔄 Identifying Process Standardization Opportunities...")
        standardization_opportunities = self.identify_standardization_opportunities()
        
        print("🎯 Analyzing High-Impact Automation Targets...")
        high_impact_targets = self.identify_high_impact_targets()
        
        print("📋 Generating Automation Roadmap...")
        automation_roadmap = self.generate_automation_roadmap()
        
        # Store all results
        self.analysis_results = {
            'repetitive_patterns': repetitive_patterns,
            'volume_candidates': volume_candidates,
            'roi_analysis': roi_analysis,
            'standardization_opportunities': standardization_opportunities,
            'high_impact_targets': high_impact_targets,
            'automation_roadmap': automation_roadmap
        }
        
        print("✅ Automation Intelligence Analysis Complete!")
        return self.analysis_results
    
    def identify_repetitive_patterns(self):
        """Identify repetitive patterns in ticket titles and descriptions."""
        
        # Normalize titles for pattern matching
        normalized_titles = self.df_categorized['title'].str.lower().str.strip()
        
        # Pattern analysis methods
        patterns = {}
        
        # 1. Exact title matches
        exact_matches = normalized_titles.value_counts()
        high_frequency_titles = exact_matches[exact_matches >= self.config['min_occurrences_for_automation']]
        
        patterns['exact_title_matches'] = [
            {
                'pattern': title,
                'occurrences': count,
                'total_hours': self.df_categorized[self.df_categorized['title'].str.lower().str.strip() == title]['hours'].sum(),
                'avg_hours_per_occurrence': self.df_categorized[self.df_categorized['title'].str.lower().str.strip() == title]['hours'].mean(),
                'automation_potential': 'High' if count >= self.config['high_volume_threshold'] else 'Medium'
            }
            for title, count in high_frequency_titles.head(20).items()
        ]
        
        # 2. Keyword-based pattern matching
        keyword_patterns = {}
        for category, keywords in self.config['automation_patterns'].items():
            matching_tickets = self.df_categorized[
                self.df_categorized['title'].str.lower().str.contains('|'.join(keywords), na=False)
            ]
            
            if len(matching_tickets) >= self.config['min_occurrences_for_automation']:
                keyword_patterns[category] = {
                    'keywords': keywords,
                    'matching_tickets': len(matching_tickets),
                    'total_hours': matching_tickets['hours'].sum(),
                    'avg_hours_per_ticket': matching_tickets['hours'].mean(),
                    'most_common_variations': matching_tickets['title'].value_counts().head(5).to_dict()
                }
        
        patterns['keyword_based_patterns'] = keyword_patterns
        
        # 3. Fuzzy pattern matching (similar titles)
        similar_groups = self._identify_similar_title_groups()
        patterns['similar_title_groups'] = similar_groups
        
        # 4. Description pattern analysis
        description_patterns = self._analyze_description_patterns()
        patterns['description_patterns'] = description_patterns
        
        return patterns
    
    def analyze_volume_based_candidates(self):
        """Analyze high-volume tasks for automation potential."""
        
        # Group by incident category for volume analysis
        category_volumes = self.df_categorized.groupby('incident_category').agg({
            'crm_id': 'count',
            'hours': ['sum', 'mean', 'median'],
            'user_username': 'nunique'
        }).round(3)
        
        category_volumes.columns = ['ticket_count', 'total_hours', 'avg_hours', 'median_hours', 'staff_involved']
        category_volumes = category_volumes.reset_index()
        
        # Calculate automation potential scores
        volume_candidates = []
        
        for _, row in category_volumes.iterrows():
            if row['ticket_count'] < self.config['min_occurrences_for_automation']:
                continue
                
            # Automation potential scoring
            volume_score = min(100, row['ticket_count'] / 100 * 100)  # Higher volume = higher score
            consistency_score = max(0, 100 - (row['avg_hours'] - row['median_hours']) / row['median_hours'] * 100)  # Lower variance = higher score
            standardization_score = max(0, 100 - row['staff_involved'] / row['ticket_count'] * 100)  # Fewer staff per ticket = more standardized
            
            automation_potential_score = (volume_score * 0.4 + consistency_score * 0.3 + standardization_score * 0.3)
            
            # Development complexity estimation
            complexity = self._estimate_automation_complexity(row['incident_category'])
            
            volume_candidates.append({
                'category': row['incident_category'],
                'ticket_count': row['ticket_count'],
                'total_hours': row['total_hours'],
                'avg_hours_per_ticket': row['avg_hours'],
                'staff_involved': row['staff_involved'],
                'automation_potential_score': round(automation_potential_score, 1),
                'estimated_complexity': complexity,
                'development_hours_estimate': self.config['automation_development_hours'][complexity]
            })
        
        # Sort by automation potential
        volume_candidates.sort(key=lambda x: x['automation_potential_score'], reverse=True)
        
        return {
            'high_potential_categories': volume_candidates[:10],
            'volume_analysis_summary': {
                'categories_analyzed': len(volume_candidates),
                'high_potential_count': len([c for c in volume_candidates if c['automation_potential_score'] > 70]),
                'total_automatable_hours': sum(c['total_hours'] for c in volume_candidates if c['automation_potential_score'] > 60)
            }
        }
    
    def calculate_automation_roi(self):
        """Calculate ROI for potential automation initiatives."""
        
        roi_calculations = []
        
        # Get volume candidates for ROI calculation
        volume_analysis = self.analyze_volume_based_candidates()
        
        for candidate in volume_analysis['high_potential_categories']:
            # Calculate annual hours (extrapolate from data period)
            data_period_days = (self.get_date_range()[1] - self.get_date_range()[0]).days
            annual_hours = candidate['total_hours'] * (365 / data_period_days)
            
            # Development investment
            development_hours = candidate['development_hours_estimate']
            development_cost = development_hours * 100  # Assume $100/hour development cost
            
            # Annual savings (assume 70% of tasks can be automated)
            automation_efficiency = 0.7
            automated_hours = annual_hours * automation_efficiency
            hourly_operational_cost = 50  # Assume $50/hour operational cost
            annual_savings = automated_hours * hourly_operational_cost
            
            # ROI calculation
            roi_ratio = annual_savings / development_cost if development_cost > 0 else 0
            payback_months = (development_cost / (annual_savings / 12)) if annual_savings > 0 else float('inf')
            
            # 3-year NPV calculation (simplified)
            three_year_savings = annual_savings * 3
            net_present_value = three_year_savings - development_cost
            
            roi_calculations.append({
                'category': candidate['category'],
                'annual_hours': round(annual_hours, 1),
                'development_cost': development_cost,
                'annual_savings': round(annual_savings, 0),
                'roi_ratio': round(roi_ratio, 2),
                'payback_months': round(payback_months, 1) if payback_months != float('inf') else 'N/A',
                'three_year_npv': round(net_present_value, 0),
                'automation_recommendation': 'High Priority' if roi_ratio > 3 else 'Medium Priority' if roi_ratio > 1.5 else 'Low Priority'
            })
        
        # Sort by ROI ratio
        roi_calculations.sort(key=lambda x: x['roi_ratio'], reverse=True)
        
        # Summary statistics
        high_roi_projects = [p for p in roi_calculations if p['roi_ratio'] > self.config['automation_roi_threshold']]
        total_investment = sum(p['development_cost'] for p in high_roi_projects)
        total_annual_savings = sum(p['annual_savings'] for p in high_roi_projects)
        
        return {
            'roi_ranked_projects': roi_calculations,
            'high_roi_projects': high_roi_projects,
            'portfolio_analysis': {
                'total_high_roi_projects': len(high_roi_projects),
                'total_investment_required': total_investment,
                'total_annual_savings_potential': total_annual_savings,
                'portfolio_roi': round(total_annual_savings / total_investment, 2) if total_investment > 0 else 0
            }
        }
    
    def identify_standardization_opportunities(self):
        """Identify process standardization opportunities to enable automation."""
        
        standardization_opportunities = []
        
        # 1. Staff variance analysis - high variance indicates standardization opportunity
        staff_variance_by_category = self.df_categorized.groupby('incident_category').agg({
            'user_username': 'nunique',
            'crm_id': 'count',
            'hours': ['mean', 'std']
        })
        
        staff_variance_by_category.columns = ['unique_staff', 'ticket_count', 'avg_hours', 'hours_std']
        staff_variance_by_category['staff_per_ticket_ratio'] = staff_variance_by_category['unique_staff'] / staff_variance_by_category['ticket_count']
        staff_variance_by_category['hours_cv'] = staff_variance_by_category['hours_std'] / staff_variance_by_category['avg_hours'] * 100
        
        # Identify high variance categories
        high_variance_categories = staff_variance_by_category[
            (staff_variance_by_category['staff_per_ticket_ratio'] > 0.3) &  # Many different staff involved
            (staff_variance_by_category['hours_cv'] > 50) &  # High time variance
            (staff_variance_by_category['ticket_count'] >= 20)  # Sufficient volume
        ].sort_values('staff_per_ticket_ratio', ascending=False)
        
        for category in high_variance_categories.index:
            row = high_variance_categories.loc[category]
            standardization_opportunities.append({
                'category': category,
                'standardization_type': 'Process Documentation & Training',
                'current_staff_involved': int(row['unique_staff']),
                'staff_per_ticket_ratio': round(row['staff_per_ticket_ratio'], 3),
                'hours_coefficient_variation': round(row['hours_cv'], 1),
                'standardization_priority': 'High' if row['staff_per_ticket_ratio'] > 0.5 else 'Medium',
                'potential_automation_enabler': True
            })
        
        # 2. Description quality standardization
        poor_documentation_categories = self.df_categorized.groupby('incident_category').agg({
            'description': lambda x: (x.str.len() < 20).sum() / len(x) * 100,
            'crm_id': 'count'
        })
        poor_documentation_categories.columns = ['poor_documentation_rate', 'ticket_count']
        
        categories_needing_doc_standards = poor_documentation_categories[
            (poor_documentation_categories['poor_documentation_rate'] > 60) &
            (poor_documentation_categories['ticket_count'] >= 15)
        ].sort_values('poor_documentation_rate', ascending=False)
        
        for category in categories_needing_doc_standards.index:
            row = categories_needing_doc_standards.loc[category]
            standardization_opportunities.append({
                'category': category,
                'standardization_type': 'Documentation Templates',
                'poor_documentation_rate': round(row['poor_documentation_rate'], 1),
                'ticket_count': int(row['ticket_count']),
                'standardization_priority': 'High' if row['poor_documentation_rate'] > 80 else 'Medium',
                'potential_automation_enabler': True
            })
        
        return {
            'standardization_opportunities': standardization_opportunities,
            'summary': {
                'total_opportunities': len(standardization_opportunities),
                'high_priority_opportunities': len([o for o in standardization_opportunities if o['standardization_priority'] == 'High']),
                'process_standardization_needed': len([o for o in standardization_opportunities if o['standardization_type'] == 'Process Documentation & Training']),
                'documentation_standardization_needed': len([o for o in standardization_opportunities if o['standardization_type'] == 'Documentation Templates'])
            }
        }
    
    def identify_high_impact_targets(self):
        """Identify highest impact automation targets combining volume, ROI, and business impact."""
        
        # Get data from previous analyses
        roi_analysis = self.calculate_automation_roi()
        volume_analysis = self.analyze_volume_based_candidates()
        
        high_impact_targets = []
        
        # Combine ROI and volume data
        for roi_project in roi_analysis['roi_ranked_projects']:
            # Find matching volume data
            volume_data = next(
                (v for v in volume_analysis['high_potential_categories'] if v['category'] == roi_project['category']), 
                None
            )
            
            if volume_data:
                # Calculate composite impact score
                roi_score = min(100, roi_project['roi_ratio'] * 20)  # Scale ROI to 100
                volume_score = volume_data['automation_potential_score']
                
                # Business impact factors
                business_impact_score = self._calculate_business_impact_score(roi_project['category'])
                
                # Composite score
                composite_score = (roi_score * 0.4 + volume_score * 0.3 + business_impact_score * 0.3)
                
                high_impact_targets.append({
                    'category': roi_project['category'],
                    'composite_impact_score': round(composite_score, 1),
                    'roi_ratio': roi_project['roi_ratio'],
                    'annual_savings': roi_project['annual_savings'],
                    'automation_potential_score': volume_data['automation_potential_score'],
                    'development_complexity': volume_data['estimated_complexity'],
                    'development_cost': roi_project['development_cost'],
                    'payback_months': roi_project['payback_months'],
                    'business_impact_factors': self._get_business_impact_factors(roi_project['category']),
                    'implementation_priority': self._determine_implementation_priority(composite_score, roi_project['roi_ratio'])
                })
        
        # Sort by composite impact score
        high_impact_targets.sort(key=lambda x: x['composite_impact_score'], reverse=True)
        
        return {
            'ranked_targets': high_impact_targets,
            'tier_1_targets': [t for t in high_impact_targets if t['implementation_priority'] == 'Tier 1 - Immediate'],
            'tier_2_targets': [t for t in high_impact_targets if t['implementation_priority'] == 'Tier 2 - Near-term'],
            'tier_3_targets': [t for t in high_impact_targets if t['implementation_priority'] == 'Tier 3 - Future']
        }
    
    def generate_automation_roadmap(self):
        """Generate comprehensive automation implementation roadmap."""
        
        high_impact_analysis = self.identify_high_impact_targets()
        standardization_analysis = self.identify_standardization_opportunities()
        
        # Phase 1: Foundation & Quick Wins (0-6 months)
        phase1_projects = []
        quick_wins = [t for t in high_impact_analysis['tier_1_targets'] if t['development_complexity'] == 'simple']
        standardization_priorities = [o for o in standardization_analysis['standardization_opportunities'] if o['standardization_priority'] == 'High']
        
        phase1_projects.extend(quick_wins[:3])  # Top 3 simple automation projects
        
        # Phase 2: Medium Complexity Automation (6-12 months)
        phase2_projects = [t for t in high_impact_analysis['tier_1_targets'] + high_impact_analysis['tier_2_targets'] 
                          if t['development_complexity'] == 'medium'][:4]
        
        # Phase 3: Complex Automation & Integration (12-24 months)
        phase3_projects = [t for t in high_impact_analysis['ranked_targets'] 
                          if t['development_complexity'] == 'complex'][:3]
        
        # Calculate roadmap metrics
        total_investment = sum(p['development_cost'] for p in phase1_projects + phase2_projects + phase3_projects)
        total_annual_savings = sum(p['annual_savings'] for p in phase1_projects + phase2_projects + phase3_projects)
        
        return {
            'implementation_phases': {
                'phase_1_foundation': {
                    'timeline': '0-6 months',
                    'focus': 'Quick wins and process standardization',
                    'projects': phase1_projects,
                    'standardization_requirements': standardization_priorities,
                    'estimated_investment': sum(p['development_cost'] for p in phase1_projects),
                    'expected_annual_savings': sum(p['annual_savings'] for p in phase1_projects)
                },
                'phase_2_expansion': {
                    'timeline': '6-12 months',
                    'focus': 'Medium complexity workflow automation',
                    'projects': phase2_projects,
                    'estimated_investment': sum(p['development_cost'] for p in phase2_projects),
                    'expected_annual_savings': sum(p['annual_savings'] for p in phase2_projects)
                },
                'phase_3_advanced': {
                    'timeline': '12-24 months',
                    'focus': 'Complex integrations and AI-enabled automation',
                    'projects': phase3_projects,
                    'estimated_investment': sum(p['development_cost'] for p in phase3_projects),
                    'expected_annual_savings': sum(p['annual_savings'] for p in phase3_projects)
                }
            },
            'roadmap_metrics': {
                'total_projects': len(phase1_projects + phase2_projects + phase3_projects),
                'total_investment': total_investment,
                'total_annual_savings_potential': total_annual_savings,
                'overall_roi': round(total_annual_savings / total_investment, 2) if total_investment > 0 else 0,
                'estimated_completion': '24 months'
            },
            'success_metrics': {
                'target_automation_rate': '60% of repetitive tasks',
                'target_time_savings': f"{int(total_annual_savings / 50)} hours annually",  # Assuming $50/hour
                'target_roi': '3:1 within 18 months'
            }
        }
    
    # Helper methods
    
    def _identify_similar_title_groups(self):
        """Identify groups of similar ticket titles for pattern analysis."""
        # Simplified similarity matching based on common words
        title_groups = defaultdict(list)
        processed_titles = set()
        
        for title in self.df_categorized['title'].dropna():
            if title in processed_titles:
                continue
                
            # Find similar titles (contains same key words)
            title_words = set(title.lower().split())
            similar_titles = []
            
            for other_title in self.df_categorized['title'].dropna():
                if other_title == title or other_title in processed_titles:
                    continue
                    
                other_words = set(other_title.lower().split())
                common_words = title_words.intersection(other_words)
                
                # If they share significant words, consider them similar
                if len(common_words) >= 2 and len(common_words) / max(len(title_words), len(other_words)) > 0.5:
                    similar_titles.append(other_title)
            
            if len(similar_titles) >= 5:  # Group must have at least 5 similar titles
                group_key = ' '.join(sorted(list(title_words)[:3]))  # Use first 3 words as key
                title_groups[group_key] = [title] + similar_titles
                processed_titles.update([title] + similar_titles)
        
        # Convert to list format with statistics
        similar_groups = []
        for group_key, titles in title_groups.items():
            matching_tickets = self.df_categorized[self.df_categorized['title'].isin(titles)]
            similar_groups.append({
                'pattern_key': group_key,
                'similar_titles': titles[:10],  # Show top 10
                'total_occurrences': len(matching_tickets),
                'total_hours': matching_tickets['hours'].sum(),
                'avg_hours_per_occurrence': matching_tickets['hours'].mean()
            })
        
        return sorted(similar_groups, key=lambda x: x['total_occurrences'], reverse=True)[:10]
    
    def _analyze_description_patterns(self):
        """Analyze description patterns for automation opportunities."""
        # Look for common phrases and patterns in descriptions
        common_phrases = Counter()
        
        for description in self.df_categorized['description'].dropna():
            if len(description) > 10:  # Skip very short descriptions
                # Extract potential pattern phrases (3-5 words)
                words = description.lower().split()
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10:  # Skip very short phrases
                        common_phrases[phrase] += 1
        
        # Find high-frequency patterns
        frequent_patterns = {phrase: count for phrase, count in common_phrases.items() 
                           if count >= self.config['min_occurrences_for_automation']}
        
        return {
            'frequent_description_patterns': dict(Counter(frequent_patterns).most_common(20)),
            'total_patterns_identified': len(frequent_patterns)
        }
    
    def _estimate_automation_complexity(self, category):
        """Estimate automation complexity based on category type."""
        category_lower = category.lower()
        
        # Simple automation candidates
        simple_indicators = ['password', 'reset', 'unlock', 'license assign', 'user setup']
        if any(indicator in category_lower for indicator in simple_indicators):
            return 'simple'
        
        # Complex automation candidates  
        complex_indicators = ['security', 'malware', 'vulnerability', 'site down', 'integration']
        if any(indicator in category_lower for indicator in complex_indicators):
            return 'complex'
        
        # Default to medium complexity
        return 'medium'
    
    def _calculate_business_impact_score(self, category):
        """Calculate business impact score for automation category."""
        category_lower = category.lower()
        
        # High business impact categories
        if any(indicator in category_lower for indicator in ['security', 'site down', 'critical']):
            return 90
        elif any(indicator in category_lower for indicator in ['user management', 'access', 'authentication']):
            return 75
        elif any(indicator in category_lower for indicator in ['email', 'communication', 'network']):
            return 60
        else:
            return 45
    
    def _get_business_impact_factors(self, category):
        """Get business impact factors for a category."""
        category_lower = category.lower()
        
        factors = []
        if 'security' in category_lower:
            factors.append('Security compliance and risk reduction')
        if 'user' in category_lower:
            factors.append('Employee productivity and satisfaction')
        if 'network' in category_lower or 'site' in category_lower:
            factors.append('Business continuity and uptime')
        if 'email' in category_lower or 'communication' in category_lower:
            factors.append('Communication reliability')
        
        return factors if factors else ['Operational efficiency']
    
    def _determine_implementation_priority(self, composite_score, roi_ratio):
        """Determine implementation priority tier."""
        if composite_score > 80 and roi_ratio > 3:
            return 'Tier 1 - Immediate'
        elif composite_score > 60 and roi_ratio > 2:
            return 'Tier 2 - Near-term'
        else:
            return 'Tier 3 - Future'


def main():
    """Main CLI interface for Automation Intelligence FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Automation Intelligence Analytics')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with AutomationIntelligenceFOB(database_path=args.database) as analyzer:
            results = analyzer.run_analysis()
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print summary unless quiet mode
            if not args.quiet:
                analyzer.print_summary()
        
        return 0
        
    except Exception as e:
        print(f"❌ Automation Intelligence analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())