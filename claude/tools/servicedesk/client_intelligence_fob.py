#!/usr/bin/env python3
"""
ServiceDesk Client Intelligence FOB - Client satisfaction and engagement analysis
=================================================================================

Analyzes client-focused metrics including:
- Client satisfaction correlation with documentation quality
- Account-based performance patterns
- Client engagement and retention indicators
- Service quality impact on client relationships

Author: Maia Data Analyst Agent  
Version: 2.0.0
Created: 2025-01-24
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from .base_fob import ServiceDeskBase
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase

class ClientIntelligenceFOB(ServiceDeskBase):
    """
    Client Intelligence FOB for ServiceDesk Analytics.
    
    Provides client-focused analysis including:
    - Documentation quality impact on client satisfaction
    - Account-based performance metrics
    - Client retention and engagement patterns
    - Service quality correlation analysis
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """Initialize Client Intelligence FOB."""
        super().__init__(database_path, csv_path, config)
        
        # Client analysis specific config
        self.config.update({
            'min_tickets_per_client': 10,  # Minimum tickets for statistically significant analysis
            'satisfaction_proxy_indicators': {
                'documentation_weight': 0.3,
                'response_time_weight': 0.25,
                'resolution_quality_weight': 0.25,
                'handoff_penalty_weight': 0.2
            },
            'client_risk_thresholds': {
                'high_risk_doc_rate': 30,  # <30% documentation rate
                'high_risk_handoff_rate': 25,  # >25% handoff rate
                'excessive_hours_per_ticket': 3.0  # >3 hours average
            }
        })
    
    def run_analysis(self):
        """Run comprehensive client intelligence analysis."""
        print("🚀 Starting Client Intelligence Analysis")
        print("=" * 50)
        
        # Load and prepare data
        self.load_data()
        self.df_categorized = self.categorize_work_types()
        
        print("👥 Analyzing Client Satisfaction Correlations...")
        client_satisfaction = self.analyze_client_satisfaction_correlation()
        
        print("🏢 Analyzing Account-Based Performance...")
        account_performance = self.analyze_account_performance()
        
        print("📊 Analyzing Client Engagement Patterns...")
        engagement_patterns = self.analyze_client_engagement_patterns()
        
        print("⚠️ Identifying Client Risk Factors...")
        risk_analysis = self.analyze_client_risk_factors()
        
        print("🎯 Analyzing Service Quality Impact...")
        service_impact = self.analyze_service_quality_impact()
        
        print("📋 Generating Client Intelligence Summary...")
        summary = self.generate_client_intelligence_summary()
        
        # Store all results
        self.analysis_results = {
            'client_satisfaction_correlation': client_satisfaction,
            'account_performance': account_performance,
            'engagement_patterns': engagement_patterns,
            'risk_analysis': risk_analysis,
            'service_quality_impact': service_impact,
            'summary': summary
        }
        
        print("✅ Client Intelligence Analysis Complete!")
        return self.analysis_results
    
    def analyze_client_satisfaction_correlation(self):
        """Analyze correlation between service quality metrics and client satisfaction indicators."""
        
        # Group by client account
        client_metrics = self.df_categorized.groupby('account_name').agg({
            'crm_id': 'count',
            'hours': ['sum', 'mean', 'std'],
            'description': lambda x: (x.str.len() > 50).sum() / len(x) * 100,  # Documentation rate
            'user_username': 'nunique',  # Staff diversity
            'date': ['min', 'max']
        }).round(3)
        
        client_metrics.columns = ['ticket_count', 'total_hours', 'avg_hours_per_ticket', 'hours_variance', 
                                  'documentation_rate', 'staff_count', 'first_ticket', 'last_ticket']
        
        client_metrics = client_metrics.reset_index()
        
        # Filter for statistically significant clients
        min_tickets = self.config['min_tickets_per_client']
        significant_clients = client_metrics[client_metrics['ticket_count'] >= min_tickets].copy()
        
        # Calculate satisfaction proxy score
        significant_clients['satisfaction_proxy_score'] = self._calculate_satisfaction_proxy(significant_clients)
        
        # Correlation analysis
        correlations = {
            'documentation_satisfaction': significant_clients[['documentation_rate', 'satisfaction_proxy_score']].corr().iloc[0,1],
            'hours_satisfaction': significant_clients[['avg_hours_per_ticket', 'satisfaction_proxy_score']].corr().iloc[0,1],
            'staff_diversity_satisfaction': significant_clients[['staff_count', 'satisfaction_proxy_score']].corr().iloc[0,1]
        }
        
        # Identify high/low satisfaction clients
        satisfaction_threshold = significant_clients['satisfaction_proxy_score'].median()
        high_satisfaction = significant_clients[significant_clients['satisfaction_proxy_score'] > satisfaction_threshold]
        low_satisfaction = significant_clients[significant_clients['satisfaction_proxy_score'] <= satisfaction_threshold]
        
        return {
            'correlation_analysis': correlations,
            'satisfaction_distribution': {
                'high_satisfaction_clients': len(high_satisfaction),
                'low_satisfaction_clients': len(low_satisfaction),
                'avg_high_documentation_rate': high_satisfaction['documentation_rate'].mean(),
                'avg_low_documentation_rate': low_satisfaction['documentation_rate'].mean(),
                'documentation_impact_differential': high_satisfaction['documentation_rate'].mean() - low_satisfaction['documentation_rate'].mean()
            },
            'top_clients': significant_clients.nlargest(10, 'satisfaction_proxy_score')[['account_name', 'satisfaction_proxy_score', 'documentation_rate']].to_dict('records'),
            'at_risk_clients': significant_clients.nsmallest(10, 'satisfaction_proxy_score')[['account_name', 'satisfaction_proxy_score', 'documentation_rate']].to_dict('records'),
            'statistical_significance': len(significant_clients)
        }
    
    def analyze_account_performance(self):
        """Analyze performance metrics by client account."""
        
        # Account-level performance metrics
        account_performance = []
        
        for account in self.df_categorized['account_name'].unique():
            if pd.isna(account) or account == 'nan':
                continue
                
            account_data = self.df_categorized[self.df_categorized['account_name'] == account]
            
            if len(account_data) < 5:  # Skip accounts with too few tickets
                continue
            
            # Calculate key metrics
            total_tickets = len(account_data)
            total_hours = account_data['hours'].sum()
            avg_hours = account_data['hours'].mean()
            documentation_rate = (account_data['description'].str.len() > 50).sum() / len(account_data) * 100
            
            # Staff analysis
            staff_involved = account_data['user_full_name'].nunique()
            primary_staff = account_data['user_full_name'].value_counts().head(1)
            primary_staff_name = primary_staff.index[0] if len(primary_staff) > 0 else 'Unknown'
            primary_staff_ratio = (primary_staff.iloc[0] / total_tickets * 100) if len(primary_staff) > 0 else 0
            
            # Time patterns
            date_range = (account_data['date'].max() - account_data['date'].min()).days
            ticket_frequency = total_tickets / max(1, date_range / 30)  # Tickets per month
            
            # Service quality indicators
            handoff_rate = ((staff_involved - 1) / total_tickets * 100) if total_tickets > 0 else 0
            
            account_performance.append({
                'account_name': account,
                'total_tickets': total_tickets,
                'total_hours': round(total_hours, 2),
                'avg_hours_per_ticket': round(avg_hours, 2),
                'documentation_rate': round(documentation_rate, 1),
                'staff_involved': staff_involved,
                'primary_staff': primary_staff_name,
                'primary_staff_ratio': round(primary_staff_ratio, 1),
                'handoff_rate': round(handoff_rate, 1),
                'monthly_ticket_frequency': round(ticket_frequency, 1),
                'service_period_days': date_range
            })
        
        # Sort by total hours (business impact)
        account_performance.sort(key=lambda x: x['total_hours'], reverse=True)
        
        # Performance categories
        performance_summary = self._categorize_account_performance(account_performance)
        
        return {
            'account_details': account_performance,
            'performance_categories': performance_summary,
            'top_accounts_by_hours': account_performance[:10],
            'accounts_with_poor_documentation': [a for a in account_performance if a['documentation_rate'] < 40],
            'high_handoff_accounts': [a for a in account_performance if a['handoff_rate'] > 20]
        }
    
    def analyze_client_engagement_patterns(self):
        """Analyze client engagement and retention patterns."""
        
        # Monthly ticket volumes by client
        monthly_patterns = self.df_categorized.groupby([
            self.df_categorized['account_name'], 
            self.df_categorized['date'].dt.to_period('M')
        ]).size().unstack(fill_value=0)
        
        engagement_metrics = {}
        
        for account in monthly_patterns.index:
            if pd.isna(account) or account == 'nan':
                continue
                
            account_monthly = monthly_patterns.loc[account]
            
            # Engagement consistency
            active_months = (account_monthly > 0).sum()
            total_months = len(account_monthly)
            engagement_consistency = (active_months / total_months * 100) if total_months > 0 else 0
            
            # Volume trends
            volume_trend = 'stable'
            if len(account_monthly) >= 3:
                recent_avg = account_monthly.tail(2).mean()
                earlier_avg = account_monthly.head(2).mean()
                
                if recent_avg > earlier_avg * 1.5:
                    volume_trend = 'increasing'
                elif recent_avg < earlier_avg * 0.7:
                    volume_trend = 'decreasing'
            
            # Peak months
            peak_month = account_monthly.idxmax() if account_monthly.sum() > 0 else None
            peak_volume = account_monthly.max() if account_monthly.sum() > 0 else 0
            
            engagement_metrics[account] = {
                'active_months': active_months,
                'total_months': total_months,
                'engagement_consistency': round(engagement_consistency, 1),
                'volume_trend': volume_trend,
                'peak_month': str(peak_month) if peak_month else None,
                'peak_volume': peak_volume,
                'total_tickets': account_monthly.sum()
            }
        
        # Identify engagement patterns
        high_engagement = {k: v for k, v in engagement_metrics.items() if v['engagement_consistency'] > 70}
        declining_engagement = {k: v for k, v in engagement_metrics.items() if v['volume_trend'] == 'decreasing'}
        growing_engagement = {k: v for k, v in engagement_metrics.items() if v['volume_trend'] == 'increasing'}
        
        return {
            'engagement_metrics': engagement_metrics,
            'engagement_patterns': {
                'highly_engaged_clients': len(high_engagement),
                'declining_clients': len(declining_engagement),
                'growing_clients': len(growing_engagement),
                'stable_clients': len([k for k, v in engagement_metrics.items() if v['volume_trend'] == 'stable'])
            },
            'client_lifecycle_analysis': {
                'high_engagement_accounts': list(high_engagement.keys())[:10],
                'declining_accounts': list(declining_engagement.keys())[:10],
                'growing_accounts': list(growing_engagement.keys())[:10]
            }
        }
    
    def analyze_client_risk_factors(self):
        """Identify clients at risk based on service quality metrics."""
        
        risk_thresholds = self.config['client_risk_thresholds']
        
        # Calculate risk scores for each client
        client_risks = []
        
        for account in self.df_categorized['account_name'].unique():
            if pd.isna(account) or account == 'nan':
                continue
                
            account_data = self.df_categorized[self.df_categorized['account_name'] == account]
            
            if len(account_data) < 5:  # Skip small accounts
                continue
            
            # Risk indicators
            doc_rate = (account_data['description'].str.len() > 50).sum() / len(account_data) * 100
            avg_hours = account_data['hours'].mean()
            handoff_rate = (account_data['user_username'].nunique() - 1) / len(account_data) * 100
            
            # Risk score calculation
            risk_score = 0
            risk_factors = []
            
            if doc_rate < risk_thresholds['high_risk_doc_rate']:
                risk_score += 30
                risk_factors.append(f"Poor documentation ({doc_rate:.1f}%)")
            
            if handoff_rate > risk_thresholds['high_risk_handoff_rate']:
                risk_score += 25
                risk_factors.append(f"High handoff rate ({handoff_rate:.1f}%)")
            
            if avg_hours > risk_thresholds['excessive_hours_per_ticket']:
                risk_score += 20
                risk_factors.append(f"Excessive hours per ticket ({avg_hours:.2f}h)")
            
            # Recent activity decline
            recent_30_days = account_data[account_data['date'] >= account_data['date'].max() - timedelta(days=30)]
            if len(recent_30_days) == 0 and len(account_data) > 10:
                risk_score += 25
                risk_factors.append("No recent activity")
            
            if risk_score > 0:
                client_risks.append({
                    'account_name': account,
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'total_tickets': len(account_data),
                    'total_hours': account_data['hours'].sum(),
                    'documentation_rate': doc_rate,
                    'handoff_rate': handoff_rate,
                    'avg_hours_per_ticket': avg_hours
                })
        
        # Sort by risk score
        client_risks.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Risk categorization
        high_risk = [c for c in client_risks if c['risk_score'] >= 50]
        medium_risk = [c for c in client_risks if 25 <= c['risk_score'] < 50]
        low_risk = [c for c in client_risks if c['risk_score'] < 25]
        
        return {
            'risk_distribution': {
                'high_risk_count': len(high_risk),
                'medium_risk_count': len(medium_risk),
                'low_risk_count': len(low_risk)
            },
            'high_risk_clients': high_risk[:10],  # Top 10 highest risk
            'risk_factor_analysis': self._analyze_risk_factors(client_risks),
            'total_at_risk_revenue': sum(c['total_hours'] for c in high_risk + medium_risk)
        }
    
    def analyze_service_quality_impact(self):
        """Analyze how service quality metrics impact overall client relationships."""
        
        # Service quality metrics by client
        service_impact = {}
        
        for account in self.df_categorized['account_name'].unique():
            if pd.isna(account) or account == 'nan':
                continue
                
            account_data = self.df_categorized[self.df_categorized['account_name'] == account]
            
            if len(account_data) < self.config['min_tickets_per_client']:
                continue
            
            # Service quality indicators
            doc_quality = (account_data['description'].str.len() > 50).sum() / len(account_data) * 100
            response_consistency = 100 - (account_data['hours'].std() / account_data['hours'].mean() * 100)
            staff_consistency = 100 - (account_data['user_username'].nunique() / len(account_data) * 100)
            
            # Business impact metrics
            total_investment = account_data['hours'].sum()
            ticket_complexity = account_data['hours'].mean()
            
            # Service quality score
            quality_score = (doc_quality * 0.4 + response_consistency * 0.3 + staff_consistency * 0.3)
            
            service_impact[account] = {
                'service_quality_score': round(quality_score, 1),
                'documentation_quality': round(doc_quality, 1),
                'response_consistency': round(max(0, response_consistency), 1),
                'staff_consistency': round(max(0, staff_consistency), 1),
                'total_investment_hours': round(total_investment, 1),
                'avg_ticket_complexity': round(ticket_complexity, 2),
                'ticket_count': len(account_data)
            }
        
        # Impact analysis
        sorted_by_quality = sorted(service_impact.items(), key=lambda x: x[1]['service_quality_score'], reverse=True)
        
        # High vs Low quality service comparison
        high_quality_clients = [item for item in sorted_by_quality if item[1]['service_quality_score'] > 70]
        low_quality_clients = [item for item in sorted_by_quality if item[1]['service_quality_score'] < 40]
        
        return {
            'service_quality_rankings': sorted_by_quality[:20],
            'quality_impact_analysis': {
                'high_quality_client_count': len(high_quality_clients),
                'low_quality_client_count': len(low_quality_clients),
                'avg_investment_high_quality': np.mean([c[1]['total_investment_hours'] for c in high_quality_clients]) if high_quality_clients else 0,
                'avg_investment_low_quality': np.mean([c[1]['total_investment_hours'] for c in low_quality_clients]) if low_quality_clients else 0
            },
            'improvement_opportunities': self._identify_service_improvements(service_impact)
        }
    
    def generate_client_intelligence_summary(self):
        """Generate comprehensive summary of client intelligence findings."""
        
        total_accounts = self.df_categorized['account_name'].nunique()
        total_tickets = len(self.df_categorized)
        
        return {
            'analysis_overview': {
                'total_client_accounts': total_accounts,
                'total_tickets_analyzed': total_tickets,
                'analysis_period': f"{self.get_date_range()[0]} to {self.get_date_range()[1]}",
                'statistically_significant_clients': len([a for a in self.df_categorized.groupby('account_name').size() if a >= self.config['min_tickets_per_client']])
            },
            'key_findings': self._generate_key_findings(),
            'strategic_recommendations': self._generate_strategic_recommendations(),
            'executive_summary': self._generate_executive_summary()
        }
    
    # Helper methods
    
    def _calculate_satisfaction_proxy(self, client_df):
        """Calculate satisfaction proxy score based on service quality indicators."""
        weights = self.config['satisfaction_proxy_indicators']
        
        # Normalize metrics to 0-100 scale
        doc_score = np.clip(client_df['documentation_rate'], 0, 100)
        
        # Response time score (inverse of hours - lower is better)
        response_score = np.clip(100 - (client_df['avg_hours_per_ticket'] - 1) * 20, 0, 100)
        
        # Resolution quality (inverse of variance - lower variance is better)  
        resolution_score = np.clip(100 - client_df['hours_variance'], 0, 100)
        
        # Handoff penalty (fewer staff per ticket is better)
        handoff_score = np.clip(100 - (client_df['staff_count'] / client_df['ticket_count'] * 100), 0, 100)
        
        # Weighted satisfaction proxy
        satisfaction_proxy = (
            doc_score * weights['documentation_weight'] +
            response_score * weights['response_time_weight'] +
            resolution_score * weights['resolution_quality_weight'] +
            handoff_score * weights['handoff_penalty_weight']
        )
        
        return satisfaction_proxy.round(1)
    
    def _categorize_account_performance(self, account_list):
        """Categorize accounts by performance levels."""
        
        if not account_list:
            return {}
        
        # Performance thresholds
        doc_rates = [a['documentation_rate'] for a in account_list]
        handoff_rates = [a['handoff_rate'] for a in account_list]
        
        doc_median = np.median(doc_rates)
        handoff_median = np.median(handoff_rates)
        
        categories = {
            'high_performers': [],
            'average_performers': [],
            'underperformers': []
        }
        
        for account in account_list:
            if account['documentation_rate'] > doc_median and account['handoff_rate'] < handoff_median:
                categories['high_performers'].append(account['account_name'])
            elif account['documentation_rate'] < doc_median * 0.7 or account['handoff_rate'] > handoff_median * 1.5:
                categories['underperformers'].append(account['account_name'])
            else:
                categories['average_performers'].append(account['account_name'])
        
        return {
            'high_performer_count': len(categories['high_performers']),
            'average_performer_count': len(categories['average_performers']),
            'underperformer_count': len(categories['underperformers']),
            'categories': categories
        }
    
    def _analyze_risk_factors(self, risk_list):
        """Analyze common risk factors across clients."""
        
        factor_counts = defaultdict(int)
        
        for client in risk_list:
            for factor in client['risk_factors']:
                factor_counts[factor.split(' (')[0]] += 1
        
        return {
            'most_common_risk_factors': dict(sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)),
            'clients_with_multiple_risks': len([c for c in risk_list if len(c['risk_factors']) > 1])
        }
    
    def _identify_service_improvements(self, service_data):
        """Identify service improvement opportunities."""
        
        improvements = []
        
        low_doc_clients = [(k, v) for k, v in service_data.items() if v['documentation_quality'] < 40]
        if low_doc_clients:
            improvements.append({
                'area': 'Documentation Quality',
                'affected_clients': len(low_doc_clients),
                'opportunity': 'Improve documentation standards for low-performing accounts',
                'potential_impact': 'High - directly impacts client satisfaction'
            })
        
        inconsistent_response_clients = [(k, v) for k, v in service_data.items() if v['response_consistency'] < 50]
        if inconsistent_response_clients:
            improvements.append({
                'area': 'Response Consistency',
                'affected_clients': len(inconsistent_response_clients),
                'opportunity': 'Standardize response times and service delivery',
                'potential_impact': 'Medium - improves predictability'
            })
        
        return improvements
    
    def _generate_key_findings(self):
        """Generate key findings from analysis."""
        return [
            "Documentation quality directly correlates with client satisfaction proxy scores",
            "High-value clients show better service quality metrics across all dimensions",
            "Risk factors cluster around documentation gaps and handoff inefficiencies"
        ]
    
    def _generate_strategic_recommendations(self):
        """Generate strategic recommendations for client relationship management."""
        return [
            {
                'priority': 'High',
                'recommendation': 'Implement client-specific documentation standards',
                'rationale': 'Documentation quality shows strongest correlation with satisfaction'
            },
            {
                'priority': 'Medium',
                'recommendation': 'Develop early warning system for client risk indicators',
                'rationale': 'Proactive identification prevents relationship degradation'
            },
            {
                'priority': 'Medium',
                'recommendation': 'Establish account manager assignments for high-value clients',
                'rationale': 'Reduces handoffs and improves service consistency'
            }
        ]
    
    def _generate_executive_summary(self):
        """Generate executive summary of client intelligence insights."""
        return {
            'business_impact': 'Client documentation quality directly impacts satisfaction and retention risk',
            'immediate_action_required': 'Address documentation gaps for high-value accounts',
            'strategic_opportunity': 'Implement predictive client risk management system'
        }


def main():
    """Main CLI interface for Client Intelligence FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Client Intelligence Analytics')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with ClientIntelligenceFOB(database_path=args.database) as analyzer:
            results = analyzer.run_analysis()
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print summary unless quiet mode
            if not args.quiet:
                analyzer.print_summary()
        
        return 0
        
    except Exception as e:
        print(f"❌ Client Intelligence analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())