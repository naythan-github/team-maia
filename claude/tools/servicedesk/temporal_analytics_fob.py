#!/usr/bin/env python3
"""
ServiceDesk Temporal Analytics FOB - Time-based pattern analysis
================================================================

Specialized analytics for time-based patterns and capacity planning:
- Peak hours and days analysis
- Seasonal trend detection
- Capacity utilization patterns
- Workload forecasting
- Response time by time-of-day
- Weekend vs weekday efficiency

Author: Maia Data Analyst Agent
Version: 2.0.0
Created: 2025-01-24
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
try:
    from .base_fob import ServiceDeskBase
except ImportError:
    # Handle direct execution
    from claude.tools.servicedesk.base_fob import ServiceDeskBase

class TemporalAnalytics(ServiceDeskBase):
    """
    Temporal pattern analysis for ServiceDesk operations.
    
    Analyzes time-based patterns including:
    - Peak hours and capacity planning
    - Seasonal trends and forecasting
    - Weekend vs weekday efficiency patterns
    - Response time degradation analysis
    - Workload distribution optimization
    """
    
    def run_analysis(self):
        """
        Run complete temporal analysis pipeline.
        
        Returns:
            Dictionary containing all temporal analysis results
        """
        print("🚀 Starting Temporal Analytics")
        print("=" * 40)
        
        self.load_data()
        
        # Run temporal analysis modules
        self.analyze_hourly_patterns()
        self.analyze_daily_patterns() 
        self.analyze_weekly_patterns()
        self.analyze_monthly_trends()
        self.analyze_capacity_utilization()
        self.analyze_response_time_patterns()
        self.generate_temporal_summary()
        
        print("\n✅ Temporal Analysis Complete!")
        return self.analysis_results
    
    def analyze_hourly_patterns(self):
        """Analyze hourly ticket volume and performance patterns."""
        print("\n🕐 Analyzing Hourly Patterns...")
        
        # Extract hour from time_from column
        self.df['hour'] = self.df['time_from'].str[:2].str.replace(':', '')
        
        # Hourly statistics
        hourly_stats = self.df.groupby('hour').agg({
            'crm_id': 'count',
            'hours': ['mean', 'sum'],
            'user_username': 'nunique',
            'description': lambda x: (x.notna() & (x.str.strip() != '')).sum()
        }).round(3)
        
        hourly_stats.columns = ['ticket_count', 'avg_resolution_time', 'total_hours_logged', 'active_agents', 'documented_tickets']
        hourly_stats = hourly_stats.reset_index()
        
        # Calculate additional metrics
        hourly_stats['documentation_rate'] = (hourly_stats['documented_tickets'] / hourly_stats['ticket_count'] * 100).round(1)
        hourly_stats['tickets_per_agent'] = (hourly_stats['ticket_count'] / hourly_stats['active_agents']).round(2)
        
        # Identify peak hours
        avg_volume = hourly_stats['ticket_count'].mean()
        peak_threshold = avg_volume * self.config['temporal_analysis']['peak_threshold']
        hourly_stats['is_peak'] = hourly_stats['ticket_count'] > peak_threshold
        
        # Off-hours analysis
        off_hours = self.config['temporal_analysis']['off_hours']
        hourly_stats['is_off_hours'] = hourly_stats['hour'].isin(off_hours)
        
        # Peak hour insights
        peak_hours = hourly_stats[hourly_stats['is_peak']].sort_values('ticket_count', ascending=False)
        off_hours_data = hourly_stats[hourly_stats['is_off_hours']]
        
        self.analysis_results['hourly_patterns'] = {
            'hourly_statistics': hourly_stats.to_dict('records'),
            'peak_analysis': {
                'peak_threshold': peak_threshold,
                'peak_hours': peak_hours['hour'].tolist(),
                'highest_volume_hour': peak_hours.iloc[0]['hour'] if not peak_hours.empty else None,
                'peak_volume': int(peak_hours.iloc[0]['ticket_count']) if not peak_hours.empty else 0,
                'peak_efficiency': peak_hours['avg_resolution_time'].mean() if not peak_hours.empty else 0
            },
            'off_hours_analysis': {
                'total_off_hours_tickets': int(off_hours_data['ticket_count'].sum()),
                'off_hours_percentage': round((off_hours_data['ticket_count'].sum() / hourly_stats['ticket_count'].sum()) * 100, 1),
                'avg_off_hours_resolution': round(off_hours_data['avg_resolution_time'].mean(), 2),
                'off_hours_documentation_rate': round(off_hours_data['documentation_rate'].mean(), 1)
            },
            'capacity_insights': {
                'max_concurrent_load': int(hourly_stats['ticket_count'].max()),
                'avg_hourly_load': round(hourly_stats['ticket_count'].mean(), 1),
                'load_variance_cv': round((hourly_stats['ticket_count'].std() / hourly_stats['ticket_count'].mean()) * 100, 1),
                'optimal_staffing_hours': hourly_stats.nlargest(8, 'ticket_count')['hour'].tolist()
            }
        }
        
        return self.analysis_results['hourly_patterns']
    
    def analyze_daily_patterns(self):
        """Analyze daily patterns and weekend vs weekday efficiency."""
        print("\n📅 Analyzing Daily Patterns...")
        
        # Add day of week (0=Monday, 6=Sunday)
        self.df['day_of_week'] = self.df['date'].dt.dayofweek
        self.df['day_name'] = self.df['date'].dt.day_name()
        
        # Daily statistics
        daily_stats = self.df.groupby(['day_of_week', 'day_name']).agg({
            'crm_id': 'count',
            'hours': ['mean', 'sum'],
            'user_username': 'nunique',
            'description': lambda x: (x.notna() & (x.str.strip() != '')).sum()
        }).round(3)
        
        daily_stats.columns = ['ticket_count', 'avg_resolution_time', 'total_hours_logged', 'active_agents', 'documented_tickets']
        daily_stats = daily_stats.reset_index()
        
        # Calculate metrics
        daily_stats['documentation_rate'] = (daily_stats['documented_tickets'] / daily_stats['ticket_count'] * 100).round(1)
        daily_stats['efficiency_score'] = (daily_stats['ticket_count'] / daily_stats['avg_resolution_time']).round(2)
        
        # Weekend vs weekday analysis
        weekend_days = self.config['temporal_analysis']['weekend_days']
        daily_stats['is_weekend'] = daily_stats['day_of_week'].isin(weekend_days)
        
        weekday_stats = daily_stats[~daily_stats['is_weekend']]
        weekend_stats = daily_stats[daily_stats['is_weekend']]
        
        # Day-specific insights
        busiest_day = daily_stats.loc[daily_stats['ticket_count'].idxmax()]
        most_efficient_day = daily_stats.loc[daily_stats['efficiency_score'].idxmax()]
        
        self.analysis_results['daily_patterns'] = {
            'daily_statistics': daily_stats.to_dict('records'),
            'weekday_vs_weekend': {
                'weekday_avg_volume': round(weekday_stats['ticket_count'].mean(), 1),
                'weekend_avg_volume': round(weekend_stats['ticket_count'].mean(), 1),
                'weekday_efficiency': round(weekday_stats['efficiency_score'].mean(), 2),
                'weekend_efficiency': round(weekend_stats['efficiency_score'].mean(), 2),
                'weekday_doc_rate': round(weekday_stats['documentation_rate'].mean(), 1),
                'weekend_doc_rate': round(weekend_stats['documentation_rate'].mean(), 1),
                'volume_difference': round(((weekday_stats['ticket_count'].mean() - weekend_stats['ticket_count'].mean()) / weekend_stats['ticket_count'].mean()) * 100, 1)
            },
            'key_insights': {
                'busiest_day': {
                    'day': busiest_day['day_name'],
                    'volume': int(busiest_day['ticket_count']),
                    'efficiency': round(busiest_day['efficiency_score'], 2)
                },
                'most_efficient_day': {
                    'day': most_efficient_day['day_name'],
                    'efficiency': round(most_efficient_day['efficiency_score'], 2),
                    'volume': int(most_efficient_day['ticket_count'])
                },
                'least_busy_day': {
                    'day': daily_stats.loc[daily_stats['ticket_count'].idxmin()]['day_name'],
                    'volume': int(daily_stats['ticket_count'].min())
                }
            }
        }
        
        return self.analysis_results['daily_patterns']
    
    def analyze_weekly_patterns(self):
        """Analyze weekly patterns and identify recurring cycles."""
        print("\n📊 Analyzing Weekly Patterns...")
        
        # Add week number and year-week
        self.df['week'] = self.df['date'].dt.isocalendar().week
        self.df['year_week'] = self.df['date'].dt.strftime('%Y-W%U')
        
        # Weekly statistics
        weekly_stats = self.df.groupby('year_week').agg({
            'crm_id': 'count',
            'hours': ['mean', 'sum'],
            'user_username': 'nunique',
            'description': lambda x: (x.notna() & (x.str.strip() != '')).sum(),
            'date': ['min', 'max']
        }).round(3)
        
        weekly_stats.columns = ['ticket_count', 'avg_resolution_time', 'total_hours_logged', 'active_agents', 'documented_tickets', 'week_start', 'week_end']
        weekly_stats = weekly_stats.reset_index()
        
        # Calculate weekly metrics
        weekly_stats['documentation_rate'] = (weekly_stats['documented_tickets'] / weekly_stats['ticket_count'] * 100).round(1)
        weekly_stats['workload_intensity'] = (weekly_stats['total_hours_logged'] / weekly_stats['active_agents']).round(2)
        
        # Identify patterns
        avg_weekly_volume = weekly_stats['ticket_count'].mean()
        high_volume_weeks = weekly_stats[weekly_stats['ticket_count'] > avg_weekly_volume * 1.2]
        low_volume_weeks = weekly_stats[weekly_stats['ticket_count'] < avg_weekly_volume * 0.8]
        
        # Weekly trend analysis
        weekly_stats_sorted = weekly_stats.sort_values('week_start')
        if len(weekly_stats_sorted) > 4:
            recent_trend = weekly_stats_sorted.tail(4)['ticket_count'].pct_change().mean()
        else:
            recent_trend = 0
        
        self.analysis_results['weekly_patterns'] = {
            'weekly_statistics': weekly_stats.to_dict('records'),
            'volume_patterns': {
                'avg_weekly_volume': round(avg_weekly_volume, 1),
                'volume_volatility_cv': round((weekly_stats['ticket_count'].std() / avg_weekly_volume) * 100, 1),
                'high_volume_weeks': len(high_volume_weeks),
                'low_volume_weeks': len(low_volume_weeks),
                'peak_week': {
                    'week': weekly_stats.loc[weekly_stats['ticket_count'].idxmax()]['year_week'],
                    'volume': int(weekly_stats['ticket_count'].max()),
                    'start_date': str(weekly_stats.loc[weekly_stats['ticket_count'].idxmax()]['week_start'])
                }
            },
            'trend_analysis': {
                'recent_4_week_trend': round(recent_trend * 100, 1),  # Percentage change
                'trend_direction': 'increasing' if recent_trend > 0.05 else 'decreasing' if recent_trend < -0.05 else 'stable',
                'seasonal_indicator': 'cyclical' if weekly_stats['ticket_count'].std() > avg_weekly_volume * 0.3 else 'stable'
            },
            'workload_analysis': {
                'avg_workload_intensity': round(weekly_stats['workload_intensity'].mean(), 2),
                'peak_workload_week': weekly_stats.loc[weekly_stats['workload_intensity'].idxmax()]['year_week'],
                'workload_variance': round(weekly_stats['workload_intensity'].std(), 2)
            }
        }
        
        return self.analysis_results['weekly_patterns']
    
    def analyze_monthly_trends(self):
        """Analyze monthly trends and seasonal patterns."""
        print("\n📈 Analyzing Monthly Trends...")
        
        # Add month and year-month
        self.df['month'] = self.df['date'].dt.month
        self.df['month_name'] = self.df['date'].dt.month_name()
        self.df['year_month'] = self.df['date'].dt.strftime('%Y-%m')
        
        # Monthly statistics
        monthly_stats = self.df.groupby(['year_month', 'month', 'month_name']).agg({
            'crm_id': 'count',
            'hours': ['mean', 'sum'],
            'user_username': 'nunique',
            'description': lambda x: (x.notna() & (x.str.strip() != '')).sum()
        }).round(3)
        
        monthly_stats.columns = ['ticket_count', 'avg_resolution_time', 'total_hours_logged', 'active_agents', 'documented_tickets']
        monthly_stats = monthly_stats.reset_index()
        
        # Calculate monthly metrics
        monthly_stats['documentation_rate'] = (monthly_stats['documented_tickets'] / monthly_stats['ticket_count'] * 100).round(1)
        monthly_stats['productivity_index'] = (monthly_stats['ticket_count'] / monthly_stats['total_hours_logged']).round(3)
        
        # Seasonal analysis (by calendar month)
        seasonal_stats = self.df.groupby(['month', 'month_name']).agg({
            'crm_id': 'count',
            'hours': 'mean'
        }).round(2)
        seasonal_stats.columns = ['avg_monthly_tickets', 'avg_resolution_time']
        seasonal_stats = seasonal_stats.reset_index()
        
        # Identify seasonal patterns
        peak_season = seasonal_stats.loc[seasonal_stats['avg_monthly_tickets'].idxmax()]
        quiet_season = seasonal_stats.loc[seasonal_stats['avg_monthly_tickets'].idxmin()]
        
        # Month-over-month growth
        monthly_stats_sorted = monthly_stats.sort_values('year_month')
        if len(monthly_stats_sorted) > 1:
            monthly_stats_sorted['mom_growth'] = monthly_stats_sorted['ticket_count'].pct_change() * 100
            avg_growth = monthly_stats_sorted['mom_growth'].mean()
        else:
            avg_growth = 0
        
        self.analysis_results['monthly_trends'] = {
            'monthly_statistics': monthly_stats.to_dict('records'),
            'seasonal_patterns': {
                'seasonal_stats': seasonal_stats.to_dict('records'),
                'peak_season': {
                    'month': peak_season['month_name'],
                    'avg_tickets': int(peak_season['avg_monthly_tickets']),
                    'seasonality_factor': round(peak_season['avg_monthly_tickets'] / seasonal_stats['avg_monthly_tickets'].mean(), 2)
                },
                'quiet_season': {
                    'month': quiet_season['month_name'],
                    'avg_tickets': int(quiet_season['avg_monthly_tickets']),
                    'seasonality_factor': round(quiet_season['avg_monthly_tickets'] / seasonal_stats['avg_monthly_tickets'].mean(), 2)
                }
            },
            'growth_trends': {
                'avg_monthly_growth': round(avg_growth, 1),
                'growth_volatility': round(monthly_stats_sorted['mom_growth'].std() if len(monthly_stats_sorted) > 1 else 0, 1),
                'trend_classification': self._classify_growth_trend(avg_growth)
            },
            'forecasting_indicators': {
                'recent_3_month_avg': round(monthly_stats_sorted.tail(3)['ticket_count'].mean(), 1) if len(monthly_stats_sorted) >= 3 else None,
                'baseline_monthly_volume': round(seasonal_stats['avg_monthly_tickets'].mean(), 1),
                'seasonal_variance_cv': round((seasonal_stats['avg_monthly_tickets'].std() / seasonal_stats['avg_monthly_tickets'].mean()) * 100, 1)
            }
        }
        
        return self.analysis_results['monthly_trends']
    
    def analyze_capacity_utilization(self):
        """Analyze capacity utilization and staffing optimization."""
        print("\n⚖️ Analyzing Capacity Utilization...")
        
        # Daily capacity analysis
        daily_capacity = self.df.groupby('date').agg({
            'crm_id': 'count',
            'user_username': 'nunique',
            'hours': 'sum'
        }).round(2)
        daily_capacity.columns = ['daily_tickets', 'agents_active', 'total_hours_worked']
        
        # Calculate utilization metrics
        daily_capacity['tickets_per_agent'] = (daily_capacity['daily_tickets'] / daily_capacity['agents_active']).round(2)
        daily_capacity['hours_per_agent'] = (daily_capacity['total_hours_worked'] / daily_capacity['agents_active']).round(2)
        
        # Assuming 8-hour workday for utilization calculation
        standard_workday_hours = 8
        daily_capacity['utilization_rate'] = (daily_capacity['hours_per_agent'] / standard_workday_hours * 100).round(1)
        
        # Capacity insights
        avg_utilization = daily_capacity['utilization_rate'].mean()
        overutilized_days = (daily_capacity['utilization_rate'] > 100).sum()
        underutilized_days = (daily_capacity['utilization_rate'] < 60).sum()
        
        # Peak capacity analysis
        peak_day = daily_capacity.loc[daily_capacity['daily_tickets'].idxmax()]
        optimal_staffing_day = daily_capacity.loc[(daily_capacity['utilization_rate'] >= 80) & (daily_capacity['utilization_rate'] <= 100)].head(1)
        
        self.analysis_results['capacity_utilization'] = {
            'daily_capacity_stats': daily_capacity.reset_index().to_dict('records'),
            'utilization_summary': {
                'avg_utilization_rate': round(avg_utilization, 1),
                'optimal_utilization_days': len(daily_capacity[(daily_capacity['utilization_rate'] >= 80) & (daily_capacity['utilization_rate'] <= 100)]),
                'overutilized_days': overutilized_days,
                'underutilized_days': underutilized_days,
                'utilization_variance': round(daily_capacity['utilization_rate'].std(), 1)
            },
            'staffing_insights': {
                'avg_agents_per_day': round(daily_capacity['agents_active'].mean(), 1),
                'peak_staffing_need': int(daily_capacity['agents_active'].max()),
                'avg_tickets_per_agent': round(daily_capacity['tickets_per_agent'].mean(), 2),
                'peak_workload_per_agent': round(daily_capacity['tickets_per_agent'].max(), 2),
                'optimal_agent_count': self._calculate_optimal_staffing(daily_capacity)
            },
            'capacity_recommendations': self._generate_capacity_recommendations(daily_capacity, avg_utilization)
        }
        
        return self.analysis_results['capacity_utilization']
    
    def analyze_response_time_patterns(self):
        """Analyze response time patterns by time periods."""
        print("\n⏱️ Analyzing Response Time Patterns...")
        
        # Response time by hour
        hourly_response = self.df.groupby('hour')['hours'].agg(['mean', 'median', 'std']).round(3)
        hourly_response.columns = ['avg_response_time', 'median_response_time', 'response_time_std']
        hourly_response = hourly_response.reset_index()
        
        # Response time by day of week
        daily_response = self.df.groupby(['day_of_week', 'day_name'])['hours'].agg(['mean', 'median', 'std']).round(3)
        daily_response.columns = ['avg_response_time', 'median_response_time', 'response_time_std']
        daily_response = daily_response.reset_index()
        
        # Identify response time degradation patterns
        peak_hours = self.analysis_results.get('hourly_patterns', {}).get('peak_analysis', {}).get('peak_hours', [])
        if peak_hours:
            peak_response_times = hourly_response[hourly_response['hour'].isin(peak_hours)]
            off_peak_response_times = hourly_response[~hourly_response['hour'].isin(peak_hours)]
            
            degradation_analysis = {
                'peak_avg_response': round(peak_response_times['avg_response_time'].mean(), 3),
                'off_peak_avg_response': round(off_peak_response_times['avg_response_time'].mean(), 3),
                'degradation_factor': round(peak_response_times['avg_response_time'].mean() / off_peak_response_times['avg_response_time'].mean(), 2),
                'quality_impact': 'significant' if peak_response_times['avg_response_time'].mean() / off_peak_response_times['avg_response_time'].mean() > 1.5 else 'moderate'
            }
        else:
            degradation_analysis = {}
        
        # Complex ticket identification
        complex_threshold = self.df['hours'].quantile(0.9)  # Top 10% longest tickets
        complex_tickets = self.df[self.df['hours'] >= complex_threshold]
        
        if not complex_tickets.empty:
            complex_pattern = complex_tickets.groupby('hour').size()
            complex_analysis = {
                'complex_ticket_threshold': round(complex_threshold, 2),
                'complex_tickets_count': len(complex_tickets),
                'complex_tickets_pct': round((len(complex_tickets) / len(self.df)) * 100, 1),
                'peak_complex_hour': complex_pattern.idxmax() if not complex_pattern.empty else None,
                'avg_complex_resolution_time': round(complex_tickets['hours'].mean(), 2)
            }
        else:
            complex_analysis = {}
        
        self.analysis_results['response_time_patterns'] = {
            'hourly_response_times': hourly_response.to_dict('records'),
            'daily_response_times': daily_response.to_dict('records'),
            'degradation_analysis': degradation_analysis,
            'complex_ticket_analysis': complex_analysis,
            'response_time_insights': {
                'fastest_avg_hour': hourly_response.loc[hourly_response['avg_response_time'].idxmin()]['hour'],
                'slowest_avg_hour': hourly_response.loc[hourly_response['avg_response_time'].idxmax()]['hour'],
                'most_consistent_hour': hourly_response.loc[hourly_response['response_time_std'].idxmin()]['hour'],
                'most_variable_hour': hourly_response.loc[hourly_response['response_time_std'].idxmax()]['hour']
            }
        }
        
        return self.analysis_results['response_time_patterns']
    
    def generate_temporal_summary(self):
        """Generate comprehensive temporal analysis summary."""
        print("\n📋 Generating Temporal Summary...")
        
        # Extract key insights from all analyses
        hourly_results = self.analysis_results.get('hourly_patterns', {})
        daily_results = self.analysis_results.get('daily_patterns', {})
        weekly_results = self.analysis_results.get('weekly_patterns', {})
        monthly_results = self.analysis_results.get('monthly_trends', {})
        capacity_results = self.analysis_results.get('capacity_utilization', {})
        response_results = self.analysis_results.get('response_time_patterns', {})
        
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'data_period': f"{self.get_date_range()[0]} to {self.get_date_range()[1]}",
            'total_tickets_analyzed': len(self.df),
            'key_temporal_insights': {
                'peak_performance_window': {
                    'best_hour': response_results.get('response_time_insights', {}).get('fastest_avg_hour'),
                    'best_day': daily_results.get('key_insights', {}).get('most_efficient_day', {}).get('day'),
                    'optimal_capacity_utilization': round(capacity_results.get('utilization_summary', {}).get('avg_utilization_rate', 0), 1)
                },
                'volume_patterns': {
                    'peak_hour': hourly_results.get('peak_analysis', {}).get('highest_volume_hour'),
                    'busiest_day': daily_results.get('key_insights', {}).get('busiest_day', {}).get('day'),
                    'peak_season': monthly_results.get('seasonal_patterns', {}).get('peak_season', {}).get('month'),
                    'volume_volatility': weekly_results.get('volume_patterns', {}).get('volume_volatility_cv', 0)
                },
                'efficiency_indicators': {
                    'weekend_efficiency_impact': self._calculate_weekend_impact(daily_results),
                    'peak_hour_degradation': response_results.get('degradation_analysis', {}).get('degradation_factor', 1.0),
                    'capacity_optimization_opportunity': capacity_results.get('utilization_summary', {}).get('overutilized_days', 0)
                }
            },
            'forecasting_insights': {
                'growth_trend': monthly_results.get('growth_trends', {}).get('trend_classification', 'stable'),
                'seasonal_predictability': monthly_results.get('forecasting_indicators', {}).get('seasonal_variance_cv', 0),
                'capacity_planning_recommendations': capacity_results.get('capacity_recommendations', [])
            },
            'operational_recommendations': self._generate_temporal_recommendations()
        }
        
        self.analysis_results['temporal_summary'] = summary
        return summary
    
    # Helper methods
    
    def _classify_growth_trend(self, avg_growth):
        """Classify growth trend based on average monthly growth."""
        if avg_growth > 5:
            return 'high_growth'
        elif avg_growth > 2:
            return 'moderate_growth'
        elif avg_growth > -2:
            return 'stable'
        elif avg_growth > -5:
            return 'moderate_decline'
        else:
            return 'significant_decline'
    
    def _calculate_optimal_staffing(self, daily_capacity):
        """Calculate optimal staffing levels."""
        # Find days with 80-100% utilization as optimal
        optimal_days = daily_capacity[(daily_capacity['utilization_rate'] >= 80) & (daily_capacity['utilization_rate'] <= 100)]
        if not optimal_days.empty:
            return round(optimal_days['agents_active'].mean(), 0)
        else:
            # Fallback to average adjusted for target utilization
            avg_agents = daily_capacity['agents_active'].mean()
            avg_utilization = daily_capacity['utilization_rate'].mean()
            target_utilization = 85  # Target 85% utilization
            return round(avg_agents * (avg_utilization / target_utilization), 0)
    
    def _generate_capacity_recommendations(self, daily_capacity, avg_utilization):
        """Generate capacity planning recommendations."""
        recommendations = []
        
        if avg_utilization > 100:
            recommendations.append("Consider increasing staffing levels - team is consistently over-utilized")
        elif avg_utilization < 60:
            recommendations.append("Opportunity for efficiency improvements - utilization is below optimal range")
        
        overutilized_days = (daily_capacity['utilization_rate'] > 100).sum()
        if overutilized_days > len(daily_capacity) * 0.2:
            recommendations.append("Implement flex staffing for peak demand periods")
        
        variance = daily_capacity['utilization_rate'].std()
        if variance > 25:
            recommendations.append("High utilization variance suggests need for better workload distribution")
        
        return recommendations
    
    def _calculate_weekend_impact(self, daily_results):
        """Calculate weekend efficiency impact."""
        weekday_vs_weekend = daily_results.get('weekday_vs_weekend', {})
        weekday_eff = weekday_vs_weekend.get('weekday_efficiency', 0)
        weekend_eff = weekday_vs_weekend.get('weekend_efficiency', 0)
        
        if weekend_eff > 0:
            return round(((weekday_eff - weekend_eff) / weekend_eff) * 100, 1)
        return 0
    
    def _generate_temporal_recommendations(self):
        """Generate temporal optimization recommendations."""
        recommendations = []
        
        hourly_results = self.analysis_results.get('hourly_patterns', {})
        daily_results = self.analysis_results.get('daily_patterns', {})
        capacity_results = self.analysis_results.get('capacity_utilization', {})
        
        # Peak hour recommendations
        peak_hours = hourly_results.get('peak_analysis', {}).get('peak_hours', [])
        if peak_hours:
            recommendations.append({
                'category': 'Shift Scheduling',
                'recommendation': f"Increase staffing during peak hours: {', '.join(peak_hours)}",
                'impact': 'Reduce response times and improve SLA compliance'
            })
        
        # Weekend efficiency
        weekend_vs_weekday = daily_results.get('weekday_vs_weekend', {})
        weekend_eff = weekend_vs_weekday.get('weekend_efficiency', 0)
        weekday_eff = weekend_vs_weekday.get('weekday_efficiency', 0)
        
        if weekend_eff < weekday_eff * 0.8:
            recommendations.append({
                'category': 'Weekend Operations',
                'recommendation': 'Implement weekend efficiency improvement program',
                'impact': 'Standardize service quality across all days'
            })
        
        # Capacity utilization
        avg_utilization = capacity_results.get('utilization_summary', {}).get('avg_utilization_rate', 0)
        if avg_utilization > 95:
            recommendations.append({
                'category': 'Capacity Planning',
                'recommendation': 'Scale up team size to prevent burnout',
                'impact': 'Maintain service quality and team sustainability'
            })
        elif avg_utilization < 65:
            recommendations.append({
                'category': 'Efficiency Optimization',
                'recommendation': 'Optimize processes or redistribute workload',
                'impact': 'Improve cost efficiency and productivity'
            })
        
        return recommendations
    
    def print_temporal_report(self):
        """Print formatted temporal analysis report."""
        if 'temporal_summary' not in self.analysis_results:
            print("❌ Temporal summary not available. Run analysis first.")
            return
        
        summary = self.analysis_results['temporal_summary']
        
        print("\n" + "="*60)
        print("📊 SERVICEDESK TEMPORAL ANALYTICS REPORT")
        print("="*60)
        
        print(f"\n🗓️  Analysis Period: {summary['data_period']}")
        print(f"📊 Total Tickets: {summary['total_tickets_analyzed']:,}")
        
        print(f"\n🕐 PEAK PERFORMANCE INSIGHTS:")
        peak_insights = summary['key_temporal_insights']['peak_performance_window']
        print(f"• Best Hour: {peak_insights['best_hour']}:00")
        print(f"• Most Efficient Day: {peak_insights['best_day']}")
        print(f"• Average Utilization: {peak_insights['optimal_capacity_utilization']}%")
        
        print(f"\n📈 VOLUME PATTERNS:")
        volume_patterns = summary['key_temporal_insights']['volume_patterns']
        print(f"• Peak Hour: {volume_patterns['peak_hour']}:00")
        print(f"• Busiest Day: {volume_patterns['busiest_day']}")
        print(f"• Peak Season: {volume_patterns['peak_season']}")
        print(f"• Volume Volatility: {volume_patterns['volume_volatility']}%")
        
        print(f"\n⚖️ EFFICIENCY INDICATORS:")
        efficiency = summary['key_temporal_insights']['efficiency_indicators']
        print(f"• Weekend Impact: {efficiency['weekend_efficiency_impact']}%")
        print(f"• Peak Hour Degradation: {efficiency['peak_hour_degradation']}x")
        print(f"• Over-utilized Days: {efficiency['capacity_optimization_opportunity']}")
        
        if summary['operational_recommendations']:
            print(f"\n🎯 OPERATIONAL RECOMMENDATIONS:")
            for rec in summary['operational_recommendations']:
                print(f"• {rec['category']}: {rec['recommendation']}")


def main():
    """Main CLI interface for Temporal Analytics FOB."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ServiceDesk Temporal Analytics FOB')
    parser.add_argument('--database', '-d', required=True, help='Path to SQLite database')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    try:
        # Initialize and run analysis
        with TemporalAnalytics(database_path=args.database) as analyzer:
            results = analyzer.run_analysis()
            
            # Export results
            if args.output:
                analyzer.export_results(args.output)
            
            # Print report unless quiet mode
            if not args.quiet:
                analyzer.print_temporal_report()
        
        return 0
        
    except Exception as e:
        print(f"❌ Temporal analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())