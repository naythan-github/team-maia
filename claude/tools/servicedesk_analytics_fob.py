#!/usr/bin/env python3
"""
ServiceDesk Analytics FOB - Automated Operational Intelligence
================================================================

Comprehensive analytics tool for ticketing system performance assessment.
Transforms manual analysis into automated operational intelligence with
executive reporting and standardized metrics.

Author: Maia Data Analyst Agent
Version: 1.0.0
Created: 2025-01-XX
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

# Add the maia root to Python path for imports
MAIA_ROOT = os.environ.get('MAIA_ROOT', str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()))
sys.path.append(MAIA_ROOT)

class ServiceDeskAnalytics:
    """
    Comprehensive ServiceDesk operational analytics engine.
    
    Provides automated analysis of ticketing systems including:
    - First Call Resolution (FCR) analysis
    - Documentation quality assessment  
    - Ownership change and handoff patterns
    - Work type distribution and performance
    - Executive reporting and benchmarking
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """
        Initialize ServiceDesk Analytics engine.
        
        Args:
            database_path: Path to SQLite database (preferred)
            csv_path: Path to CSV file (will convert to SQLite)
            config: Configuration dictionary for analysis parameters
        """
        self.database_path = database_path
        self.csv_path = csv_path
        self.config = config or self._default_config()
        self.df = None
        self.analysis_results = {}
        
    def _default_config(self):
        """Default configuration for analysis parameters."""
        return {
            'category_filter': 'Support/Helpdesk',
            'fcr_target': 70.0,
            'documentation_target': 90.0,
            'handoff_threshold': 15.0,
            'excessive_updates_threshold': 5,
            'detailed_description_min_chars': 50,
            'industry_benchmarks': {
                'fcr_rate': 75.0,
                'documentation_rate': 85.0,
                'handoff_rate': 12.0,
                'excessive_updates': 5.0
            }
        }
    
    def load_data(self):
        """Load data from database or CSV file."""
        if self.database_path and os.path.exists(self.database_path):
            self._load_from_database()
        elif self.csv_path and os.path.exists(self.csv_path):
            self._load_from_csv()
        else:
            raise ValueError("No valid data source provided")
        
        print(f"✅ Loaded {len(self.df):,} tickets for analysis")
        
    def _load_from_database(self):
        """Load data from SQLite database."""
        conn = sqlite3.connect(self.database_path)
        query = f"""
        SELECT user_username, user_full_name, title, description, hours, date, 
               time_from, time_to, type, category, account_name, crm_id
        FROM tickets 
        WHERE category = '{self.config['category_filter']}'
        ORDER BY crm_id, date, time_from
        """
        self.df = pd.read_sql_query(query, conn)
        conn.close()
        
    def _load_from_csv(self):
        """Load data from CSV and optionally convert to SQLite."""
        self.df = pd.read_csv(self.csv_path)
        # Clean column names
        self.df.columns = self.df.columns.str.replace('﻿', '').str.replace('TS-', '').str.replace(' ', '_').str.lower()
        
        # Filter for Support/Helpdesk if column exists
        if 'category' in self.df.columns:
            self.df = self.df[self.df['category'] == self.config['category_filter']]
    
    def analyze_documentation_quality(self):
        """Analyze documentation completeness and quality."""
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
        work_types = self._categorize_work_types()
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
        
        # Get database connection for direct SQL queries
        conn = sqlite3.connect(self.database_path)
        
        # Team documentation statistics
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
        HAVING total_tickets >= 50
        ORDER BY pct_with_description DESC
        """
        
        team_docs = pd.read_sql_query(team_query, conn, params=[self.config['category_filter']])
        
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
        
        conn.close()
        
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
        
        conn = sqlite3.connect(self.database_path)
        
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
            users_to_analyze = [row[0] for row in conn.execute(volume_query, [self.config['category_filter']])]
        
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
            
            user_stats = conn.execute(user_query, [user, self.config['category_filter']]).fetchone()
            
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
            
            variance_stats = conn.execute(time_variance_query, 
                                        [user, user, user, user, user, self.config['category_filter']]).fetchone()
            
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
            
            work_types = conn.execute(type_query, [user, self.config['category_filter']]).fetchall()
            
            # Get user's full name
            name_query = "SELECT DISTINCT user_full_name FROM tickets WHERE user_username = ? LIMIT 1"
            full_name = conn.execute(name_query, [user]).fetchone()[0]
            
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
        
        conn.close()
        
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
        work_types = self._categorize_work_types()
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
        
        work_types = self._categorize_work_types()
        
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
    
    def _categorize_work_types(self):
        """Enhanced categorization by work type based on comprehensive title analysis."""
        work_df = self.df.copy()
        incident_categories = []
        
        for title in work_df['title'].fillna(''):
            title_lower = title.lower()
            
            # NOC-specific incidents
            if 'noc:' in title_lower:
                if 'site down' in title_lower:
                    incident_categories.append('NOC: Site Down')
                elif 'wan link down' in title_lower or 'link down' in title_lower:
                    incident_categories.append('NOC: Link Down')
                else:
                    incident_categories.append('NOC: Other')
            
            # Security & Monitoring (major category from analysis)
            elif any(word in title_lower for word in ['alert', 'fired:', 'vulnerability', 'defender', 'trojan', 'security', 'monitor', 'detected']):
                if 'motion detected' in title_lower:
                    incident_categories.append('Security: Motion Detection')
                elif any(word in title_lower for word in ['azure monitor', 'resourcehealth']):
                    incident_categories.append('Security: Azure Monitor')
                elif any(word in title_lower for word in ['vulnerability', 'defender']):
                    incident_categories.append('Security: Vulnerability Management')
                elif 'trojan' in title_lower:
                    incident_categories.append('Security: Malware Detection')
                else:
                    incident_categories.append('Security: Alerts & Monitoring')
            
            # Network & Infrastructure
            elif any(word in title_lower for word in ['vpn', 'network', 'connectivity', 'internet', 'wan', 'link', 'connection']):
                if 'vpn' in title_lower:
                    incident_categories.append('Network: VPN Issues')
                elif any(word in title_lower for word in ['internet', 'connectivity']):
                    incident_categories.append('Network: Connectivity Issues')
                else:
                    incident_categories.append('Network: Infrastructure')
            
            # User Management & Access
            elif any(word in title_lower for word in ['new user', 'starter', 'onboard', 'offboard', 'remove licenses', 'setup', 'assign role']):
                if any(word in title_lower for word in ['remove', 'offboard']):
                    incident_categories.append('User Management: Offboarding')
                elif any(word in title_lower for word in ['new user', 'starter', 'onboard']):
                    incident_categories.append('User Management: Onboarding')
                else:
                    incident_categories.append('User Management: Access Control')
            
            # Storage & Hardware Issues
            elif any(word in title_lower for word in ['storage', 'disk', 'drive', 'freezing', 'hardware', 'max out', 'health']):
                if any(word in title_lower for word in ['storage', 'disk', 'drive']):
                    incident_categories.append('Hardware: Storage Issues')
                elif 'freezing' in title_lower:
                    incident_categories.append('Hardware: System Performance')
                else:
                    incident_categories.append('Hardware: General')
            
            # Software Updates & Patching
            elif any(word in title_lower for word in ['patch', 'update', 'failure notification', 'kb50', 'windows', 'chrome', 'edge', 'version']):
                if 'failure notification' in title_lower and 'patch' in title_lower:
                    incident_categories.append('Software: Patch Management')
                elif any(word in title_lower for word in ['chrome', 'edge', 'browser']):
                    incident_categories.append('Software: Browser Updates')
                elif any(word in title_lower for word in ['windows', 'kb50']):
                    incident_categories.append('Software: Windows Updates')
                else:
                    incident_categories.append('Software: Updates & Patches')
            
            # Software Installation & Licensing
            elif any(word in title_lower for word in ['installation', 'install', 'acrobat', 'premiere', 'licensing', 'foxit', 'datto', 'mcaffe']):
                if any(word in title_lower for word in ['acrobat', 'premiere', 'foxit']):
                    incident_categories.append('Software: Document/Media Apps')
                elif any(word in title_lower for word in ['datto', 'mcaffe']):
                    incident_categories.append('Software: Security/Backup Tools')
                else:
                    incident_categories.append('Software: Installation & Licensing')
            
            # Project & Scheduled Work
            elif any(word in title_lower for word in ['scheduled on-site', 'task -', 'project', 'tenancy split']):
                if 'scheduled on-site' in title_lower:
                    incident_categories.append('Project: Scheduled On-Site')
                elif 'task -' in title_lower:
                    incident_categories.append('Project: Engineering Tasks')
                else:
                    incident_categories.append('Project: General')
            
            # Communication & Collaboration
            elif any(word in title_lower for word in ['teams', 'sharepoint', 'switchboard', '3cx', 'assistance with']):
                if any(word in title_lower for word in ['teams', 'sharepoint']):
                    incident_categories.append('Communication: Microsoft 365')
                elif any(word in title_lower for word in ['3cx', 'switchboard']):
                    incident_categories.append('Communication: Phone Systems')
                else:
                    incident_categories.append('Communication: General')
            
            # Login & Authentication (enhanced)
            elif any(word in title_lower for word in ['password', 'reset', 'unlock', 'login', 'cannot log in', 'unable to login']):
                if any(word in title_lower for word in ['login', 'log in']):
                    incident_categories.append('Authentication: Login Issues')
                else:
                    incident_categories.append('Password/Account')
            
            # Email (existing category)
            elif any(word in title_lower for word in ['email', 'outlook', 'mail']):
                incident_categories.append('Email Issues')
            
            # Phone/VoIP (existing category)
            elif any(word in title_lower for word in ['phone', 'voip', 'call']):
                incident_categories.append('Phone/VoIP')
            
            # Printer/Scanning (existing category)
            elif any(word in title_lower for word in ['printer', 'print', 'scanning']):
                incident_categories.append('Printer/Scanning')
            
            # Backup/Restore (existing category)
            elif any(word in title_lower for word in ['backup', 'restore']):
                incident_categories.append('Backup/Restore')
            
            # Server/Application (existing category)
            elif any(word in title_lower for word in ['server', 'service', 'application']):
                incident_categories.append('Server/Application')
            
            # Catch remaining tickets
            else:
                incident_categories.append('Other/Miscellaneous')
        
        work_df['incident_category'] = incident_categories
        return work_df
    
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
            'data_period': f"{self.df['date'].min()} to {self.df['date'].max()}",
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
    
    def run_full_analysis(self, include_individual_patterns=False):
        """Run complete analysis pipeline."""
        print("🚀 Starting Comprehensive ServiceDesk Analysis")
        print("=" * 60)
        
        self.load_data()
        
        # Run all analysis modules
        self.analyze_documentation_quality()
        self.analyze_team_documentation_quality()
        if include_individual_patterns:
            self.analyze_individual_documentation_patterns()
        self.analyze_first_call_resolution()
        self.analyze_ownership_patterns()
        self.analyze_work_distribution()
        
        # Generate executive summary
        summary = self.generate_executive_summary()
        
        print("\n✅ Analysis Complete!")
        return self.analysis_results
    
    def export_results(self, output_path=None):
        """Export analysis results to JSON file."""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"servicedesk_analysis_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        print(f"📄 Results exported to: {output_path}")
        return output_path
    
    def print_executive_report(self):
        """Print formatted executive report to console."""
        if 'executive_summary' not in self.analysis_results:
            print("❌ Executive summary not available. Run analysis first.")
            return
        
        summary = self.analysis_results['executive_summary']
        
        print("\n" + "="*80)
        print("📊 SERVICEDESK OPERATIONAL INTELLIGENCE REPORT")
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
    """Main CLI interface for ServiceDesk Analytics FOB."""
    parser = argparse.ArgumentParser(description='ServiceDesk Analytics FOB - Automated Operational Intelligence')
    parser.add_argument('--database', '-d', help='Path to SQLite database')
    parser.add_argument('--csv', '-c', help='Path to CSV file')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--config', help='Path to configuration JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    parser.add_argument('--individual-patterns', action='store_true', help='Include individual documentation patterns analysis')
    parser.add_argument('--team-docs-only', action='store_true', help='Run team documentation analysis only')
    parser.add_argument('--analyze-user', help='Analyze specific user documentation patterns (username)')
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Initialize analytics engine
    analyzer = ServiceDeskAnalytics(
        database_path=args.database,
        csv_path=args.csv,
        config=config
    )
    
    try:
        # Load data first
        analyzer.load_data()
        
        # Run specific analysis based on arguments
        if args.team_docs_only:
            analyzer.analyze_team_documentation_quality()
            results = analyzer.analysis_results
        elif args.analyze_user:
            analyzer.analyze_individual_documentation_patterns(args.analyze_user)
            results = analyzer.analysis_results
        else:
            # Run full analysis
            results = analyzer.run_full_analysis(include_individual_patterns=args.individual_patterns)
        
        # Export results
        if args.output:
            analyzer.export_results(args.output)
        
        # Print report unless quiet mode
        if not args.quiet:
            if args.team_docs_only or args.analyze_user:
                # Print specific analysis results
                if 'team_documentation' in results:
                    print("\n📊 TEAM DOCUMENTATION QUALITY REPORT")
                    print("=" * 50)
                    team_results = results['team_documentation']
                    print(f"Total Staff Analyzed: {team_results['team_variance']['total_staff']}")
                    print(f"Average Documentation Rate: {team_results['team_variance']['avg_documentation_rate']:.1f}%")
                    print(f"Documentation Variance (CV): {team_results['team_variance']['coefficient_of_variation']:.1f}%")
                    
                    print(f"\n🏆 TOP PERFORMERS:")
                    for performer in team_results['top_performers']:
                        print(f"• {performer['user_full_name']}: {performer['pct_with_description']:.1f}% documentation")
                    
                    print(f"\n🚨 BOTTOM PERFORMERS:")
                    for performer in team_results['bottom_performers']:
                        print(f"• {performer['user_full_name']}: {performer['pct_with_description']:.1f}% documentation")
                
                if 'individual_patterns' in results:
                    print("\n🔍 INDIVIDUAL DOCUMENTATION PATTERNS")
                    print("=" * 50)
                    for username, data in results['individual_patterns'].items():
                        print(f"\n{data['full_name']} ({username}):")
                        print(f"  Documentation Rate: {data['documentation_patterns']['documentation_rate']:.1f}%")
                        print(f"  Total Tickets: {data['basic_stats']['total_tickets']:,}")
                        print(f"  Hours CV: {data['basic_stats']['coefficient_of_variation']:.1f}%")
            else:
                analyzer.print_executive_report()
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())