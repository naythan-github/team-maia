#!/usr/bin/env python3
"""
ServiceDesk Training Intelligence FOB - Skill gap and training need analysis
===========================================================================

Analyzes team performance patterns to identify skill gaps and training needs:
- Individual performance assessment and improvement areas
- Team-wide skill distribution analysis
- Training ROI calculations based on performance improvements
- Competency mapping and development pathways

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

class TrainingIntelligenceFOB(ServiceDeskBase):
    """
    Training Intelligence FOB for ServiceDesk Analytics.
    
    Provides skill gap analysis and training recommendations through:
    - Individual performance profiling and improvement areas
    - Team competency mapping and skill distribution
    - Training ROI analysis based on productivity improvements
    - Development pathway recommendations
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """Initialize Training Intelligence FOB."""
        super().__init__(database_path, csv_path, config)
        
        # Training-specific configuration
        self.config.update({
            'performance_benchmarks': {
                'excellent_doc_rate': 80,      # >80% documentation rate
                'good_doc_rate': 60,           # 60-80% documentation rate
                'poor_doc_rate': 40,           # <40% documentation rate
                'efficient_hours_per_ticket': 1.5,  # <1.5 hours per ticket
                'slow_hours_per_ticket': 3.0,      # >3 hours per ticket
                'high_variety_categories': 8,       # Works across 8+ categories
                'low_variety_categories': 3         # Works in <3 categories
            },
            'training_cost_estimates': {
                'documentation_training': 800,      # 1-day workshop
                'technical_skills': 2400,          # 3-day technical course
                'process_efficiency': 1600,        # 2-day efficiency training
                'specialized_domain': 4000,        # 5-day specialized training
                'leadership_development': 3200     # 4-day leadership program
            },
            'improvement_targets': {
                'documentation_rate_improvement': 30,    # Target 30% improvement
                'efficiency_improvement': 20,            # Target 20% time reduction
                'quality_score_improvement': 25          # Target 25% quality improvement
            },
            'min_tickets_for_assessment': 20  # Minimum tickets for reliable assessment
        })
    
    def run_analysis(self):
        """Run comprehensive training intelligence analysis."""
        print("🚀 Starting Training Intelligence Analysis")
        print("=" * 50)
        
        # Load and prepare data
        self.load_data()
        self.df_categorized = self.categorize_work_types()
        
        print("👤 Analyzing Individual Performance Profiles...")
        individual_profiles = self.analyze_individual_performance_profiles()
        
        print("🎯 Identifying Skill Gaps and Training Needs...")
        skill_gap_analysis = self.identify_skill_gaps()
        
        print("📊 Analyzing Team Competency Distribution...")
        competency_analysis = self.analyze_team_competencies()
        
        print("💰 Calculating Training ROI Opportunities...")
        training_roi = self.calculate_training_roi()
        
        print("🛤️ Creating Development Pathways...")
        development_pathways = self.create_development_pathways()
        
        print("📋 Generating Training Roadmap...")
        training_roadmap = self.generate_training_roadmap()
        
        # Store all results
        self.analysis_results = {
            'individual_profiles': individual_profiles,
            'skill_gap_analysis': skill_gap_analysis,
            'competency_analysis': competency_analysis,
            'training_roi': training_roi,
            'development_pathways': development_pathways,
            'training_roadmap': training_roadmap
        }
        
        print("✅ Training Intelligence Analysis Complete!")
        return self.analysis_results
    
    def analyze_individual_performance_profiles(self):
        """Analyze individual performance profiles to identify strengths and improvement areas."""
        
        staff_profiles = []
        min_tickets = self.config['min_tickets_for_assessment']
        
        # Get staff with sufficient ticket volume for analysis
        staff_list = self.get_staff_list(min_tickets)
        
        for _, staff_row in staff_list.iterrows():
            username = staff_row['user_username']
            full_name = staff_row['user_full_name']
            
            # Get individual's tickets
            staff_tickets = self.df_categorized[
                self.df_categorized['user_username'] == username
            ]
            
            if len(staff_tickets) < min_tickets:
                continue
            
            # Performance metrics calculation
            profile = self._calculate_individual_metrics(staff_tickets, username, full_name)
            
            # Identify strengths and improvement areas
            profile['strengths'] = self._identify_strengths(profile)
            profile['improvement_areas'] = self._identify_improvement_areas(profile)
            profile['training_recommendations'] = self._recommend_training(profile)
            profile['performance_tier'] = self._classify_performance_tier(profile)
            
            staff_profiles.append(profile)
        
        # Sort by overall performance score
        staff_profiles.sort(key=lambda x: x['overall_performance_score'], reverse=True)
        
        # Performance distribution
        tier_distribution = Counter([p['performance_tier'] for p in staff_profiles])
        
        return {
            'individual_profiles': staff_profiles,
            'team_summary': {
                'total_staff_analyzed': len(staff_profiles),
                'performance_distribution': dict(tier_distribution),
                'high_performers': [p for p in staff_profiles if p['performance_tier'] == 'High Performer'],
                'development_needed': [p for p in staff_profiles if p['performance_tier'] in ['Needs Development', 'Critical']]
            }
        }
    
    def identify_skill_gaps(self):
        """Identify team-wide skill gaps and training priorities."""
        
        individual_analysis = self.analyze_individual_performance_profiles()
        
        # Aggregate skill gaps across team
        skill_gaps = defaultdict(list)
        training_needs = defaultdict(int)
        
        for profile in individual_analysis['individual_profiles']:
            for area in profile['improvement_areas']:
                skill_gaps[area['skill_area']].append({
                    'staff_name': profile['full_name'],
                    'severity': area['severity'],
                    'impact': area['business_impact']
                })
                training_needs[area['skill_area']] += 1
        
        # Priority ranking based on frequency and impact
        priority_rankings = []
        
        for skill_area, staff_list in skill_gaps.items():
            total_staff_affected = len(staff_list)
            high_severity_count = len([s for s in staff_list if s['severity'] == 'High'])
            avg_business_impact = np.mean([s['impact'] for s in staff_list])
            
            priority_score = (total_staff_affected * 0.4 + 
                            high_severity_count * 0.4 + 
                            avg_business_impact * 0.2)
            
            priority_rankings.append({
                'skill_area': skill_area,
                'staff_affected': total_staff_affected,
                'high_severity_cases': high_severity_count,
                'avg_business_impact': round(avg_business_impact, 1),
                'priority_score': round(priority_score, 2),
                'affected_staff_details': staff_list
            })
        
        # Sort by priority score
        priority_rankings.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'skill_gap_priorities': priority_rankings,
            'team_wide_needs': {
                'most_critical_gap': priority_rankings[0]['skill_area'] if priority_rankings else None,
                'total_skill_areas_identified': len(priority_rankings),
                'staff_needing_development': len(individual_analysis['team_summary']['development_needed'])
            }
        }
    
    def analyze_team_competencies(self):
        """Analyze team competency distribution and coverage gaps."""
        
        # Category expertise analysis
        category_expertise = defaultdict(list)
        
        for _, row in self.df_categorized.iterrows():
            if pd.notna(row['user_full_name']) and pd.notna(row['incident_category']):
                category_expertise[row['incident_category']].append({
                    'staff_name': row['user_full_name'],
                    'hours': row['hours'],
                    'documented': len(str(row['description'])) > 50
                })
        
        # Calculate expertise levels per category
        competency_matrix = {}
        
        for category, tickets in category_expertise.items():
            if len(tickets) < 5:  # Skip low-volume categories
                continue
                
            staff_performance = defaultdict(lambda: {'tickets': 0, 'hours': 0, 'documentation_rate': 0})
            
            for ticket in tickets:
                staff_name = ticket['staff_name']
                staff_performance[staff_name]['tickets'] += 1
                staff_performance[staff_name]['hours'] += ticket['hours']
                if ticket['documented']:
                    staff_performance[staff_name]['documentation_rate'] += 1
            
            # Calculate expertise scores
            category_experts = []
            for staff_name, performance in staff_performance.items():
                if performance['tickets'] >= 5:  # Minimum tickets for expertise assessment
                    doc_rate = (performance['documentation_rate'] / performance['tickets']) * 100
                    avg_efficiency = performance['hours'] / performance['tickets']
                    
                    # Expertise score (documentation quality + efficiency)
                    expertise_score = (doc_rate * 0.6) + (max(0, 100 - avg_efficiency * 20) * 0.4)
                    
                    category_experts.append({
                        'staff_name': staff_name,
                        'tickets_handled': performance['tickets'],
                        'avg_hours_per_ticket': round(avg_efficiency, 2),
                        'documentation_rate': round(doc_rate, 1),
                        'expertise_score': round(expertise_score, 1),
                        'expertise_level': self._classify_expertise_level(expertise_score)
                    })
            
            # Sort by expertise score
            category_experts.sort(key=lambda x: x['expertise_score'], reverse=True)
            
            competency_matrix[category] = {
                'experts': [e for e in category_experts if e['expertise_level'] == 'Expert'],
                'competent': [e for e in category_experts if e['expertise_level'] == 'Competent'],
                'developing': [e for e in category_experts if e['expertise_level'] == 'Developing'],
                'coverage_risk': len(category_experts) < 2,  # Risk if <2 competent staff
                'total_staff_involved': len(category_experts)
            }
        
        # Identify coverage gaps
        coverage_gaps = []
        for category, competencies in competency_matrix.items():
            expert_count = len(competencies['experts'])
            competent_count = len(competencies['competent'])
            
            if expert_count == 0:
                coverage_gaps.append({
                    'category': category,
                    'gap_type': 'No Expert Coverage',
                    'risk_level': 'High',
                    'mitigation': 'Develop expert-level staff through specialized training'
                })
            elif expert_count == 1 and competent_count == 0:
                coverage_gaps.append({
                    'category': category,
                    'gap_type': 'Single Point of Failure',
                    'risk_level': 'Medium',
                    'mitigation': 'Cross-train additional staff to competent level'
                })
        
        return {
            'competency_matrix': competency_matrix,
            'coverage_analysis': {
                'categories_analyzed': len(competency_matrix),
                'high_risk_categories': len([g for g in coverage_gaps if g['risk_level'] == 'High']),
                'coverage_gaps': coverage_gaps
            },
            'expertise_distribution': self._analyze_expertise_distribution(competency_matrix)
        }
    
    def calculate_training_roi(self):
        """Calculate ROI for different training interventions."""
        
        individual_analysis = self.analyze_individual_performance_profiles()
        roi_calculations = []
        
        # Training intervention scenarios
        training_scenarios = {
            'documentation_improvement': {
                'target_staff': [p for p in individual_analysis['individual_profiles'] 
                               if any(area['skill_area'] == 'Documentation Quality' 
                                     for area in p['improvement_areas'])],
                'cost_per_person': self.config['training_cost_estimates']['documentation_training'],
                'expected_improvement': self.config['improvement_targets']['documentation_rate_improvement']
            },
            'efficiency_training': {
                'target_staff': [p for p in individual_analysis['individual_profiles'] 
                               if any(area['skill_area'] == 'Time Efficiency' 
                                     for area in p['improvement_areas'])],
                'cost_per_person': self.config['training_cost_estimates']['process_efficiency'],
                'expected_improvement': self.config['improvement_targets']['efficiency_improvement']
            },
            'technical_skills': {
                'target_staff': [p for p in individual_analysis['individual_profiles'] 
                               if any(area['skill_area'] == 'Technical Competency' 
                                     for area in p['improvement_areas'])],
                'cost_per_person': self.config['training_cost_estimates']['technical_skills'],
                'expected_improvement': self.config['improvement_targets']['quality_score_improvement']
            }
        }
        
        for scenario_name, scenario in training_scenarios.items():
            if not scenario['target_staff']:
                continue
                
            # Calculate investment and returns
            staff_count = len(scenario['target_staff'])
            total_investment = staff_count * scenario['cost_per_person']
            
            # Calculate current performance impact
            current_annual_hours = sum(p['annual_ticket_hours'] for p in scenario['target_staff'])
            hourly_cost = 50  # Assumed cost per hour
            
            # Expected improvements
            if scenario_name == 'efficiency_training':
                # Time savings
                time_reduction = scenario['expected_improvement'] / 100
                annual_hours_saved = current_annual_hours * time_reduction
                annual_savings = annual_hours_saved * hourly_cost
            else:
                # Quality improvements (assumed to reduce rework by 15%)
                rework_reduction = 0.15
                annual_savings = current_annual_hours * rework_reduction * hourly_cost
            
            # ROI calculation
            roi_ratio = annual_savings / total_investment if total_investment > 0 else 0
            payback_months = (total_investment / (annual_savings / 12)) if annual_savings > 0 else float('inf')
            
            roi_calculations.append({
                'training_type': scenario_name,
                'staff_count': staff_count,
                'total_investment': total_investment,
                'annual_savings': round(annual_savings, 0),
                'roi_ratio': round(roi_ratio, 2),
                'payback_months': round(payback_months, 1) if payback_months != float('inf') else 'N/A',
                'net_benefit_year_1': round(annual_savings - total_investment, 0),
                'recommendation': 'High Priority' if roi_ratio > 2 else 'Medium Priority' if roi_ratio > 1 else 'Low Priority'
            })
        
        # Sort by ROI ratio
        roi_calculations.sort(key=lambda x: x['roi_ratio'], reverse=True)
        
        # Portfolio analysis
        high_roi_training = [t for t in roi_calculations if t['roi_ratio'] > 1.5]
        total_portfolio_investment = sum(t['total_investment'] for t in high_roi_training)
        total_portfolio_savings = sum(t['annual_savings'] for t in high_roi_training)
        
        return {
            'training_roi_analysis': roi_calculations,
            'high_roi_programs': high_roi_training,
            'portfolio_summary': {
                'total_high_roi_programs': len(high_roi_training),
                'portfolio_investment': total_portfolio_investment,
                'portfolio_annual_savings': total_portfolio_savings,
                'portfolio_roi': round(total_portfolio_savings / total_portfolio_investment, 2) if total_portfolio_investment > 0 else 0
            }
        }
    
    def create_development_pathways(self):
        """Create personalized development pathways for team members."""
        
        individual_analysis = self.analyze_individual_performance_profiles()
        competency_analysis = self.analyze_team_competencies()
        
        development_pathways = []
        
        for profile in individual_analysis['individual_profiles']:
            if profile['performance_tier'] in ['High Performer']:
                # Focus on leadership and mentoring
                pathway = {
                    'staff_name': profile['full_name'],
                    'current_tier': profile['performance_tier'],
                    'pathway_type': 'Leadership Development',
                    'development_stages': [
                        {
                            'stage': 'Mentor Role',
                            'timeline': '3 months',
                            'activities': ['Pair with developing staff', 'Knowledge transfer sessions'],
                            'success_metrics': ['Mentee improvement scores', 'Knowledge documentation']
                        },
                        {
                            'stage': 'Subject Matter Expert',
                            'timeline': '6 months', 
                            'activities': ['Lead training sessions', 'Process improvement initiatives'],
                            'success_metrics': ['Training effectiveness', 'Process improvements implemented']
                        }
                    ]
                }
            elif profile['performance_tier'] in ['Needs Development', 'Critical']:
                # Focus on foundational skills
                pathway = {
                    'staff_name': profile['full_name'],
                    'current_tier': profile['performance_tier'],
                    'pathway_type': 'Skills Development',
                    'development_stages': []
                }
                
                # Priority order for skill development
                for area in sorted(profile['improvement_areas'], key=lambda x: x['priority_score'], reverse=True)[:3]:
                    stage = {
                        'stage': f"{area['skill_area']} Improvement",
                        'timeline': '6-8 weeks',
                        'activities': self._get_development_activities(area['skill_area']),
                        'success_metrics': [f"{area['skill_area']} score improvement", 'Performance milestone achievement']
                    }
                    pathway['development_stages'].append(stage)
            else:
                # Competent performers - focus on specialization
                pathway = {
                    'staff_name': profile['full_name'],
                    'current_tier': profile['performance_tier'],
                    'pathway_type': 'Specialization',
                    'development_stages': [
                        {
                            'stage': 'Domain Expertise',
                            'timeline': '4 months',
                            'activities': ['Focus on 2-3 specialized categories', 'Advanced technical training'],
                            'success_metrics': ['Expertise score in chosen domains', 'Resolution efficiency']
                        }
                    ]
                }
            
            development_pathways.append(pathway)
        
        return {
            'individual_pathways': development_pathways,
            'pathway_distribution': {
                'leadership_track': len([p for p in development_pathways if p['pathway_type'] == 'Leadership Development']),
                'skills_development': len([p for p in development_pathways if p['pathway_type'] == 'Skills Development']),
                'specialization_track': len([p for p in development_pathways if p['pathway_type'] == 'Specialization'])
            }
        }
    
    def generate_training_roadmap(self):
        """Generate comprehensive training implementation roadmap."""
        
        skill_gaps = self.identify_skill_gaps()
        training_roi = self.calculate_training_roi()
        development_pathways = self.create_development_pathways()
        
        # Phase 1: Critical Skills (0-3 months)
        phase1_priorities = []
        critical_gaps = [gap for gap in skill_gaps['skill_gap_priorities'][:3] 
                        if gap['priority_score'] > 5]
        
        for gap in critical_gaps:
            matching_training = next(
                (t for t in training_roi['training_roi_analysis'] 
                 if gap['skill_area'].lower() in t['training_type']), 
                None
            )
            
            if matching_training:
                phase1_priorities.append({
                    'skill_area': gap['skill_area'],
                    'staff_affected': gap['staff_affected'],
                    'training_investment': matching_training['total_investment'],
                    'expected_roi': matching_training['roi_ratio']
                })
        
        # Phase 2: Development Programs (3-9 months)
        skills_development_count = development_pathways['pathway_distribution']['skills_development']
        phase2_programs = [
            {
                'program': 'Foundational Skills Development',
                'participants': skills_development_count,
                'duration': '6 months',
                'focus': 'Core competency building for underperforming staff'
            }
        ]
        
        # Phase 3: Advanced Development (9-18 months)
        leadership_count = development_pathways['pathway_distribution']['leadership_track']
        specialization_count = development_pathways['pathway_distribution']['specialization_track']
        
        phase3_programs = []
        if leadership_count > 0:
            phase3_programs.append({
                'program': 'Leadership Development',
                'participants': leadership_count,
                'duration': '9 months',
                'focus': 'Mentoring and team leadership skills'
            })
        
        if specialization_count > 0:
            phase3_programs.append({
                'program': 'Technical Specialization',
                'participants': specialization_count,
                'duration': '6 months', 
                'focus': 'Deep domain expertise development'
            })
        
        # Calculate total roadmap investment and returns
        total_investment = training_roi['portfolio_summary']['portfolio_investment']
        total_annual_savings = training_roi['portfolio_summary']['portfolio_annual_savings']
        
        return {
            'implementation_phases': {
                'phase_1_critical': {
                    'timeline': '0-3 months',
                    'focus': 'Address critical skill gaps',
                    'priorities': phase1_priorities,
                    'success_criteria': 'Eliminate high-priority skill gaps'
                },
                'phase_2_development': {
                    'timeline': '3-9 months',
                    'focus': 'Foundational skills improvement',
                    'programs': phase2_programs,
                    'success_criteria': 'Move developing staff to competent level'
                },
                'phase_3_advanced': {
                    'timeline': '9-18 months',
                    'focus': 'Leadership and specialization',
                    'programs': phase3_programs,
                    'success_criteria': 'Establish expertise coverage and leadership bench'
                }
            },
            'roadmap_metrics': {
                'total_investment': total_investment,
                'annual_savings_potential': total_annual_savings,
                'overall_roi': training_roi['portfolio_summary']['portfolio_roi'],
                'staff_development_coverage': len(development_pathways['individual_pathways']),
                'estimated_completion': '18 months'
            },
            'success_indicators': {
                'performance_improvement': 'Move 80% of developing staff to competent level',
                'coverage_improvement': 'Eliminate single points of failure in critical categories',
                'roi_achievement': 'Achieve minimum 2:1 ROI within 12 months'
            }
        }
    
    # Helper methods
    
    def _calculate_individual_metrics(self, staff_tickets, username, full_name):
        """Calculate comprehensive performance metrics for an individual."""
        
        # Basic metrics
        total_tickets = len(staff_tickets)
        total_hours = staff_tickets['hours'].sum()
        avg_hours = staff_tickets['hours'].mean()
        
        # Documentation quality
        documented_tickets = (staff_tickets['description'].str.len() > 50).sum()
        documentation_rate = (documented_tickets / total_tickets) * 100
        
        # Category diversity
        categories_worked = staff_tickets['incident_category'].nunique()
        category_distribution = staff_tickets['incident_category'].value_counts()
        primary_category = category_distribution.index[0] if len(category_distribution) > 0 else 'Unknown'
        
        # Time efficiency variance
        hours_std = staff_tickets['hours'].std()
        efficiency_consistency = 100 - min(100, (hours_std / avg_hours) * 100) if avg_hours > 0 else 0
        
        # Performance scoring
        doc_score = min(100, documentation_rate / 70 * 100)  # Against 70% benchmark
        efficiency_score = max(0, 100 - (avg_hours - 1.5) * 30) if avg_hours > 1.5 else 100  # Against 1.5h benchmark
        consistency_score = efficiency_consistency
        
        overall_performance_score = (doc_score * 0.4 + efficiency_score * 0.4 + consistency_score * 0.2)
        
        # Extrapolate to annual figures
        data_period_days = (self.get_date_range()[1] - self.get_date_range()[0]).days
        annual_tickets = total_tickets * (365 / data_period_days)
        annual_hours = total_hours * (365 / data_period_days)
        
        return {
            'username': username,
            'full_name': full_name,
            'total_tickets': total_tickets,
            'total_hours': round(total_hours, 1),
            'avg_hours_per_ticket': round(avg_hours, 2),
            'documentation_rate': round(documentation_rate, 1),
            'categories_worked': categories_worked,
            'primary_category': primary_category,
            'efficiency_consistency': round(efficiency_consistency, 1),
            'overall_performance_score': round(overall_performance_score, 1),
            'annual_tickets': round(annual_tickets, 0),
            'annual_ticket_hours': round(annual_hours, 0),
            'performance_metrics': {
                'documentation_score': round(doc_score, 1),
                'efficiency_score': round(efficiency_score, 1),
                'consistency_score': round(consistency_score, 1)
            }
        }
    
    def _identify_strengths(self, profile):
        """Identify individual strengths based on performance profile."""
        strengths = []
        
        if profile['performance_metrics']['documentation_score'] > 80:
            strengths.append('Excellent Documentation Quality')
        
        if profile['performance_metrics']['efficiency_score'] > 80:
            strengths.append('High Time Efficiency')
        
        if profile['performance_metrics']['consistency_score'] > 75:
            strengths.append('Consistent Performance')
        
        if profile['categories_worked'] >= self.config['performance_benchmarks']['high_variety_categories']:
            strengths.append('Broad Technical Knowledge')
        
        return strengths if strengths else ['Reliable Team Member']
    
    def _identify_improvement_areas(self, profile):
        """Identify areas for improvement and their business impact."""
        improvement_areas = []
        
        # Documentation quality issues
        if profile['documentation_rate'] < self.config['performance_benchmarks']['poor_doc_rate']:
            improvement_areas.append({
                'skill_area': 'Documentation Quality',
                'current_score': profile['documentation_rate'],
                'severity': 'High' if profile['documentation_rate'] < 20 else 'Medium',
                'business_impact': 85,
                'priority_score': 9
            })
        
        # Time efficiency issues
        if profile['avg_hours_per_ticket'] > self.config['performance_benchmarks']['slow_hours_per_ticket']:
            improvement_areas.append({
                'skill_area': 'Time Efficiency',
                'current_score': profile['performance_metrics']['efficiency_score'],
                'severity': 'High' if profile['avg_hours_per_ticket'] > 4 else 'Medium',
                'business_impact': 75,
                'priority_score': 8
            })
        
        # Consistency issues
        if profile['efficiency_consistency'] < 60:
            improvement_areas.append({
                'skill_area': 'Work Consistency',
                'current_score': profile['efficiency_consistency'],
                'severity': 'Medium',
                'business_impact': 60,
                'priority_score': 6
            })
        
        # Technical breadth
        if profile['categories_worked'] < self.config['performance_benchmarks']['low_variety_categories']:
            improvement_areas.append({
                'skill_area': 'Technical Competency',
                'current_score': profile['categories_worked'],
                'severity': 'Medium',
                'business_impact': 65,
                'priority_score': 5
            })
        
        return improvement_areas
    
    def _recommend_training(self, profile):
        """Recommend specific training based on improvement areas."""
        recommendations = []
        
        for area in profile['improvement_areas']:
            if area['skill_area'] == 'Documentation Quality':
                recommendations.append({
                    'training_type': 'Documentation Workshop',
                    'duration': '1 day',
                    'cost': self.config['training_cost_estimates']['documentation_training'],
                    'expected_improvement': '30% documentation rate improvement'
                })
            elif area['skill_area'] == 'Time Efficiency':
                recommendations.append({
                    'training_type': 'Process Efficiency Training',
                    'duration': '2 days',
                    'cost': self.config['training_cost_estimates']['process_efficiency'],
                    'expected_improvement': '20% time reduction'
                })
            elif area['skill_area'] == 'Technical Competency':
                recommendations.append({
                    'training_type': 'Technical Skills Development',
                    'duration': '3 days',
                    'cost': self.config['training_cost_estimates']['technical_skills'],
                    'expected_improvement': 'Competency in 2-3 additional categories'
                })
        
        return recommendations
    
    def _classify_performance_tier(self, profile):
        """Classify performance tier based on overall score."""
        score = profile['overall_performance_score']
        
        if score >= 85:
            return 'High Performer'
        elif score >= 70:
            return 'Competent'
        elif score >= 50:
            return 'Needs Development'
        else:
            return 'Critical'
    
    def _classify_expertise_level(self, expertise_score):
        """Classify expertise level based on score."""
        if expertise_score >= 80:
            return 'Expert'
        elif expertise_score >= 60:
            return 'Competent'
        else:
            return 'Developing'
    
    def _analyze_expertise_distribution(self, competency_matrix):
        """Analyze distribution of expertise across categories."""
        total_experts = sum(len(cat['experts']) for cat in competency_matrix.values())
        total_competent = sum(len(cat['competent']) for cat in competency_matrix.values())
        total_developing = sum(len(cat['developing']) for cat in competency_matrix.values())
        
        return {
            'expert_count': total_experts,
            'competent_count': total_competent,
            'developing_count': total_developing,
            'categories_with_experts': len([cat for cat in competency_matrix.values() if len(cat['experts']) > 0]),
            'categories_at_risk': len([cat for cat in competency_matrix.values() if cat['coverage_risk']])
        }
    
    def _get_development_activities(self, skill_area):
        """Get specific development activities for a skill area."""
        activities_map = {
            'Documentation Quality': [
                'Documentation standards training',
                'Peer review of ticket updates',
                'Template creation workshop'
            ],
            'Time Efficiency': [
                'Process optimization training',
                'Time management workshop',
                'Tool efficiency training'
            ],
            'Technical Competency': [
                'Hands-on technical training',
                'Shadow senior staff',
                'Certification programs'
            ],
            'Work Consistency': [
                'Standardized procedure training',
                'Quality checklist implementation',
                'Regular coaching sessions'
            ]
        }
        
        return activities_map.get(skill_area, ['General skills development', 'Mentoring sessions'])


def main():
    """Main CLI interface for Training Intelligence FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Training Intelligence Analytics')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with TrainingIntelligenceFOB(database_path=args.database) as analyzer:
            results = analyzer.run_analysis()
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print summary unless quiet mode
            if not args.quiet:
                analyzer.print_summary()
        
        return 0
        
    except Exception as e:
        print(f"❌ Training Intelligence analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())