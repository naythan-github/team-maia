#!/usr/bin/env python3
"""
ServiceDesk Base FOB - Shared utilities and database connections
================================================================

Base class providing common functionality for all ServiceDesk FOB modules.
Handles data loading, database connections, configuration, and shared utilities.

Author: Maia Data Analyst Agent
Version: 2.0.0
Created: 2025-01-24
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC, abstractmethod

class ServiceDeskBase(ABC):
    """
    Base class for all ServiceDesk analytics FOBs.
    
    Provides shared functionality including:
    - Database connections and data loading
    - Configuration management
    - Common data transformations
    - Export utilities
    - Logging and error handling
    """
    
    def __init__(self, database_path=None, csv_path=None, config=None):
        """
        Initialize ServiceDesk Base FOB.
        
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
        self._connection = None
        
    def _default_config(self):
        """Default configuration for analysis parameters."""
        return {
            'category_filter': 'Support/Helpdesk',
            'fcr_target': 70.0,
            'documentation_target': 90.0,
            'handoff_threshold': 15.0,
            'excessive_updates_threshold': 5,
            'detailed_description_min_chars': 50,
            'min_tickets_for_analysis': 50,
            'industry_benchmarks': {
                'fcr_rate': 75.0,
                'documentation_rate': 85.0,
                'handoff_rate': 12.0,
                'excessive_updates': 5.0,
                'sla_compliance': 95.0,
                'csat_score': 4.0
            },
            'temporal_analysis': {
                'peak_threshold': 1.5,  # Peak if >1.5x average volume
                'off_hours': ['17', '18', '19', '20', '21', '22', '23', '00', '01', '02', '03', '04', '05', '06'],
                'weekend_days': [0, 6],  # Sunday=0, Saturday=6
                'holiday_impact_days': 3  # Days before/after holidays
            }
        }
    
    def get_connection(self):
        """Get database connection (singleton pattern)."""
        if self._connection is None:
            if not self.database_path or not os.path.exists(self.database_path):
                raise ValueError(f"Database path not found: {self.database_path}")
            self._connection = sqlite3.connect(self.database_path)
        return self._connection
    
    def close_connection(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def load_data(self, category_filter=None, force_reload=False):
        """
        Load data from database or CSV file.
        
        Args:
            category_filter: Override default category filter
            force_reload: Force reload even if data already exists
        """
        if self.df is not None and not force_reload:
            return
            
        category_filter = category_filter or self.config['category_filter']
        
        if self.database_path and os.path.exists(self.database_path):
            self._load_from_database(category_filter)
        elif self.csv_path and os.path.exists(self.csv_path):
            self._load_from_csv(category_filter)
        else:
            raise ValueError("No valid data source provided")
        
        print(f"✅ Loaded {len(self.df):,} tickets for analysis")
        
    def _load_from_database(self, category_filter):
        """Load data from SQLite database."""
        conn = self.get_connection()
        query = """
        SELECT user_username, user_full_name, title, description, hours, date, 
               time_from, time_to, type, category, account_name, crm_id,
               costcentre_desc, ticket_department, account_bill_state
        FROM tickets 
        WHERE category = ? AND hours IS NOT NULL AND hours > 0
        ORDER BY crm_id, date, time_from
        """
        self.df = pd.read_sql_query(query, conn, params=[category_filter])
        
        # Data type conversions and cleaning
        self._clean_dataframe()
        
    def _load_from_csv(self, category_filter):
        """Load data from CSV and optionally convert to SQLite."""
        self.df = pd.read_csv(self.csv_path)
        # Clean column names
        self.df.columns = self.df.columns.str.replace('﻿', '').str.replace('TS-', '').str.replace(' ', '_').str.lower()
        
        # Filter for Support/Helpdesk if column exists
        if 'category' in self.df.columns and category_filter:
            self.df = self.df[self.df['category'] == category_filter]
            
        self._clean_dataframe()
    
    def _clean_dataframe(self):
        """Clean and standardize dataframe."""
        if self.df is None:
            return
            
        # Convert date column to datetime
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'], dayfirst=True, errors='coerce')
            
        # Standardize time columns
        if 'time_from' in self.df.columns:
            self.df['time_from'] = self.df['time_from'].astype(str)
            
        # Clean text fields
        text_columns = ['title', 'description', 'user_full_name', 'account_name']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).replace('nan', '')
                
        # Ensure hours is numeric
        if 'hours' in self.df.columns:
            self.df['hours'] = pd.to_numeric(self.df['hours'], errors='coerce')
            # Filter out zero or negative hours
            self.df = self.df[self.df['hours'] > 0]
    
    def execute_query(self, query, params=None):
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results as list of tuples
        """
        conn = self.get_connection()
        cursor = conn.execute(query, params or [])
        return cursor.fetchall()
    
    def execute_query_df(self, query, params=None):
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results as pandas DataFrame
        """
        conn = self.get_connection()
        return pd.read_sql_query(query, conn, params=params)
    
    def get_date_range(self):
        """Get the date range of loaded data."""
        if self.df is None or 'date' not in self.df.columns:
            return None, None
        return self.df['date'].min(), self.df['date'].max()
    
    def get_staff_list(self, min_tickets=None):
        """
        Get list of staff members with ticket counts.
        
        Args:
            min_tickets: Minimum tickets to include staff member
            
        Returns:
            DataFrame with staff information
        """
        if self.df is None:
            return pd.DataFrame()
            
        min_tickets = min_tickets or self.config.get('min_tickets_for_analysis', 50)
        
        staff_df = self.df.groupby(['user_username', 'user_full_name']).agg({
            'crm_id': 'count',
            'hours': ['sum', 'mean'],
            'date': ['min', 'max']
        }).round(3)
        
        staff_df.columns = ['ticket_count', 'total_hours', 'avg_hours', 'first_ticket', 'last_ticket']
        staff_df = staff_df.reset_index()
        
        # Filter by minimum ticket count
        staff_df = staff_df[staff_df['ticket_count'] >= min_tickets]
        
        return staff_df.sort_values('total_hours', ascending=False)
    
    def categorize_work_types(self, df=None):
        """
        Enhanced categorization by work type based on comprehensive title analysis.
        
        Args:
            df: DataFrame to categorize (uses self.df if None)
            
        Returns:
            DataFrame with incident_category column added
        """
        work_df = (df if df is not None else self.df).copy()
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
            
            # Security & Monitoring
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
            
            # Authentication & Login
            elif any(word in title_lower for word in ['password', 'reset', 'unlock', 'login', 'cannot log in', 'unable to login']):
                if any(word in title_lower for word in ['login', 'log in']):
                    incident_categories.append('Authentication: Login Issues')
                else:
                    incident_categories.append('Authentication: Password/Account')
            
            # Email Issues
            elif any(word in title_lower for word in ['email', 'outlook', 'mail']):
                incident_categories.append('Email Issues')
            
            # Communication & Collaboration
            elif any(word in title_lower for word in ['teams', 'sharepoint', 'switchboard', '3cx']):
                if any(word in title_lower for word in ['teams', 'sharepoint']):
                    incident_categories.append('Communication: Microsoft 365')
                elif any(word in title_lower for word in ['3cx', 'switchboard']):
                    incident_categories.append('Communication: Phone Systems')
                else:
                    incident_categories.append('Communication: General')
            
            # Hardware & Storage
            elif any(word in title_lower for word in ['storage', 'disk', 'drive', 'freezing', 'hardware', 'printer', 'print']):
                if any(word in title_lower for word in ['storage', 'disk', 'drive']):
                    incident_categories.append('Hardware: Storage Issues')
                elif any(word in title_lower for word in ['printer', 'print']):
                    incident_categories.append('Hardware: Printer/Scanning')
                elif 'freezing' in title_lower:
                    incident_categories.append('Hardware: System Performance')
                else:
                    incident_categories.append('Hardware: General')
            
            # Software & Applications
            elif any(word in title_lower for word in ['software', 'application', 'install', 'update', 'patch', 'version']):
                if any(word in title_lower for word in ['patch', 'update', 'version']):
                    incident_categories.append('Software: Updates & Patches')
                elif any(word in title_lower for word in ['install', 'installation']):
                    incident_categories.append('Software: Installation & Licensing')
                else:
                    incident_categories.append('Software: Application Issues')
            
            # Backup & Restore
            elif any(word in title_lower for word in ['backup', 'restore']):
                incident_categories.append('Backup/Restore')
            
            # Server/Infrastructure
            elif any(word in title_lower for word in ['server', 'service']):
                incident_categories.append('Server/Application')
            
            # Project Work
            elif any(word in title_lower for word in ['task -', 'project', 'scheduled on-site']):
                incident_categories.append('Project Work')
            
            # Catch remaining tickets
            else:
                incident_categories.append('Other/Miscellaneous')
        
        work_df['incident_category'] = incident_categories
        return work_df
    
    def export_results(self, output_path=None):
        """
        Export analysis results to JSON file.
        
        Args:
            output_path: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fob_name = self.__class__.__name__.lower().replace('analytics', '').replace('fob', '')
            output_path = f"servicedesk_{fob_name}_analysis_{timestamp}.json"
        
        # Prepare results for export
        export_data = {
            'analysis_metadata': {
                'fob_type': self.__class__.__name__,
                'analysis_date': datetime.now().isoformat(),
                'data_period': f"{self.get_date_range()[0]} to {self.get_date_range()[1]}" if self.df is not None else None,
                'total_tickets': len(self.df) if self.df is not None else 0,
                'config': self.config
            },
            'analysis_results': self.analysis_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📄 Results exported to: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print basic summary information."""
        if self.df is None:
            print("❌ No data loaded")
            return
            
        date_min, date_max = self.get_date_range()
        print(f"\n📊 DATA SUMMARY")
        print(f"=" * 40)
        print(f"Total Tickets: {len(self.df):,}")
        print(f"Date Range: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}")
        print(f"Unique Staff: {self.df['user_username'].nunique()}")
        print(f"Total Hours: {self.df['hours'].sum():.1f}")
        print(f"Average Hours/Ticket: {self.df['hours'].mean():.2f}")
        
        # Top categories
        if hasattr(self, 'df_categorized'):
            top_categories = self.df_categorized['incident_category'].value_counts().head(5)
            print(f"\nTop 5 Issue Categories:")
            for category, count in top_categories.items():
                pct = (count / len(self.df_categorized)) * 100
                print(f"• {category}: {count:,} ({pct:.1f}%)")
    
    @abstractmethod
    def run_analysis(self):
        """
        Abstract method that each FOB must implement.
        Should contain the main analysis logic for that specific domain.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close_connection()