#!/usr/bin/env python3
"""
Robust Job Monitoring System - Replacement for the broken automated_job_monitor.py
Built with proper error handling, database management, and recovery mechanisms
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Add tools path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'core'))
sys.path.append(str(Path(__file__).parent.parent))

from claude.core.path_manager import get_path_manager
from claude.tools.database_connection_manager import DatabaseConnectionManager

# Import these dynamically to avoid corrupted dependencies
def get_gmail_fetcher():
    """Dynamically import gmail fetcher"""
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from gmail_job_fetcher import GmailJobFetcher
        return GmailJobFetcher
    except Exception as e:
        logger.warning(f"Gmail fetcher unavailable: {e}")
        return None

def get_email_extractors():
    """Dynamically import email extractors"""
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from email_job_extractor import extract_job_details_from_email, extract_urls_from_email
        return extract_job_details_from_email, extract_urls_from_email
    except Exception as e:
        logger.warning(f"Email extractors unavailable: {e}")
        return None, None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(get_path_manager().get_path('app_support') / 'logs' / 'job_monitor_robust.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RobustJobMonitor:
    """
    Robust job monitoring system with proper error handling and recovery
    """

    def __init__(self):
        """Initialize the job monitor with robust configurations"""
        self.db_manager = get_database_manager()
        self.config_file = str(get_path_manager().get_path('app_support') / 'config' / 'job_monitor_config.json')
        self.last_run_file = str(get_path_manager().get_path('app_support') / 'config' / 'last_job_run.json')

        # Load configuration
        self.config = self._load_config()

        # Initialize enhanced scorer with error handling
        self.enhanced_scorer = self._initialize_enhanced_scorer()

        logger.info("RobustJobMonitor initialized successfully")

    def _load_config(self) -> Dict:
        """Load configuration with defaults"""
        default_config = {
            'gmail_credentials': str(get_path_manager().get_path('git_root') / 'claude' / 'data' / 'google_credentials' / 'client_secrets.json'),
            'gmail_token': str(get_path_manager().get_path('git_root') / 'claude' / 'data' / 'google_credentials' / 'tokens' / 'google_services_token.pickle'),
            'min_score_threshold': 7.5,
            'email_lookback_hours': 36,
            'max_jobs_per_run': 100
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
                    logger.info("Configuration loaded from file")
            else:
                logger.info("Using default configuration")

            return default_config

        except Exception as e:
            logger.error(f"Error loading config, using defaults: {e}")
            return default_config

    def _initialize_enhanced_scorer(self):
        """Initialize enhanced scorer with error handling"""
        try:
            from enhanced_profile_scorer import EnhancedProfileScorer
            scorer = EnhancedProfileScorer()
            logger.info("Enhanced scorer initialized successfully")
            return scorer
        except Exception as e:
            logger.error(f"Failed to initialize enhanced scorer: {e}")
            logger.info("Will use basic scoring as fallback")
            return None

    def get_last_run_time(self) -> datetime:
        """Get the timestamp of the last successful run"""
        try:
            if os.path.exists(self.last_run_file):
                with open(self.last_run_file, 'r') as f:
                    data = json.load(f)
                    last_run_str = data.get('last_run', '')
                    if last_run_str:
                        return datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))

            # Default to 36 hours ago if no last run found
            return datetime.now() - timedelta(hours=self.config['email_lookback_hours'])

        except Exception as e:
            logger.error(f"Error reading last run time: {e}")
            return datetime.now() - timedelta(hours=self.config['email_lookback_hours'])

    def update_last_run_time(self):
        """Update the last run timestamp"""
        try:
            os.makedirs(os.path.dirname(self.last_run_file), exist_ok=True)

            data = {
                'last_run': datetime.now().isoformat(),
                'updated_by': 'RobustJobMonitor'
            }

            with open(self.last_run_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Last run time updated successfully")

        except Exception as e:
            logger.error(f"Error updating last run time: {e}")

    def fetch_new_jobs(self) -> List[Dict]:
        """Fetch new jobs from Gmail with robust error handling"""
        logger.info("📧 Fetching new job emails...")

        try:
            # Check credentials
            if not os.path.exists(self.config['gmail_credentials']):
                error_msg = f"Gmail credentials not found: {self.config['gmail_credentials']}"
                logger.error(error_msg)
                self.db_manager.log_system_health('gmail_fetcher', 'error', error_msg)
                return []

            # Initialize Gmail fetcher
            fetcher = GmailJobFetcher(
                self.config['gmail_credentials'],
                self.config['gmail_token']
            )
            fetcher.authenticate()

            # Get date range
            last_run = self.get_last_run_time()
            now = datetime.now()

            start_str = last_run.strftime('%Y/%m/%d')
            end_str = (now + timedelta(days=1)).strftime('%Y/%m/%d')

            logger.info(f"Fetching emails from {start_str} to {end_str}")

            # Fetch emails
            emails = fetcher.fetch_jobs_from_date_range(start_str, end_str, batch_size=50)
            logger.info(f"Fetched {len(emails)} emails")

            # Extract jobs from emails
            all_jobs = []
            for email in emails:
                try:
                    # Try URL extraction first
                    urls = extract_urls_from_email(email['body'])
                    for url_data in urls:
                        job = {
                            'title': url_data.get('job_title', ''),
                            'company': url_data.get('company', ''),
                            'location': url_data.get('location', ''),
                            'salary': url_data.get('salary', ''),
                            'description': url_data.get('description', email.get('snippet', '')),
                            'url': url_data.get('url', ''),
                            'source': 'email_url_extract',
                            'email_id': email.get('id', '')
                        }
                        all_jobs.append(job)

                    # Also try direct email job extraction
                    email_jobs = extract_job_details_from_email(email['body'])
                    for job in email_jobs:
                        job.update({
                            'source': 'email_text_extract',
                            'email_id': email.get('id', '')
                        })
                        all_jobs.append(job)

                except Exception as email_error:
                    logger.error(f"Error processing email {email.get('id', 'unknown')}: {email_error}")
                    continue

            logger.info(f"Extracted {len(all_jobs)} total jobs from emails")
            self.db_manager.log_system_health('job_extraction', 'healthy', f"Extracted {len(all_jobs)} jobs")

            return all_jobs[:self.config['max_jobs_per_run']]  # Limit for safety

        except Exception as e:
            error_msg = f"Critical error in job fetching: {e}"
            logger.error(error_msg)
            self.db_manager.log_system_health('job_fetcher', 'critical', error_msg, {'error': str(e)})
            return []

    def score_job_safe(self, job: Dict) -> Tuple[float, Dict]:
        """Score a job with robust error handling and fallbacks"""
        try:
            if self.enhanced_scorer:
                score, breakdown = self.enhanced_scorer.score_job_enhanced(job)

                # Validate that breakdown has required keys
                if not isinstance(breakdown, dict) or 'base_score' not in breakdown:
                    logger.warning(f"Invalid breakdown from enhanced scorer, using fallback")
                    return self._score_job_basic_fallback(job)

                return score, breakdown
            else:
                return self._score_job_basic_fallback(job)

        except Exception as e:
            logger.error(f"Error in job scoring: {e}")
            logger.error(f"Job data: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            return self._score_job_basic_fallback(job)

    def _score_job_basic_fallback(self, job: Dict) -> Tuple[float, Dict]:
        """Basic scoring fallback when enhanced scoring fails"""
        title = (job.get('title') or '').lower()
        company = (job.get('company') or '').lower()
        location = (job.get('location') or '').lower()

        # Basic scoring logic
        base_score = 5.0

        # Title matching bonuses
        title_bonus = 0.0
        if any(keyword in title for keyword in ['senior', 'lead', 'principal', 'manager']):
            title_bonus += 1.0
        if any(keyword in title for keyword in ['brm', 'business relationship', 'client partner']):
            title_bonus += 2.0

        # Company bonuses
        company_bonus = 0.0
        preferred_companies = ['pwc', 'deloitte', 'kpmg', 'microsoft', 'aws', 'google']
        if any(comp in company for comp in preferred_companies):
            company_bonus += 1.0

        # Location bonus
        location_bonus = 0.0
        if 'perth' in location or 'wa' in location:
            location_bonus += 0.5

        total_score = base_score + title_bonus + company_bonus + location_bonus

        breakdown = {
            'base_score': base_score,
            'title_bonus': title_bonus,
            'company_bonus': company_bonus,
            'location_bonus': location_bonus,
            'total_score': total_score,
            'algorithm': 'basic_fallback',
            'usp_matches': [],
            'final_score': total_score
        }

        return total_score, breakdown

    def run(self, fetch_new: bool = True, send_email: bool = False) -> Dict:
        """Main execution method with comprehensive error handling"""
        logger.info("🚀 Starting robust job monitoring run")

        # Start execution log
        log_id = self.db_manager.start_execution_log('manual_run' if not send_email else 'automated_run')

        results = {
            'success': False,
            'jobs_fetched': 0,
            'jobs_stored': 0,
            'jobs_duplicates': 0,
            'high_scoring_jobs': 0,
            'errors': []
        }

        try:
            # Step 1: Fetch new jobs
            if fetch_new:
                new_jobs = self.fetch_new_jobs()
                results['jobs_fetched'] = len(new_jobs)

                if new_jobs:
                    # Step 2: Store jobs in database
                    stored, duplicates = self.db_manager.store_jobs(new_jobs)
                    results['jobs_stored'] = stored
                    results['jobs_duplicates'] = duplicates

                    logger.info(f"✅ Stored {stored} new jobs, {duplicates} duplicates")

                    # Step 3: Score jobs
                    jobs_scored = 0
                    for job in new_jobs:
                        try:
                            score, breakdown = self.score_job_safe(job)

                            # Store scoring data
                            if self.db_manager.score_and_store_job(job, {
                                'base_score': breakdown.get('base_score', 5.0),
                                'location_bonus': breakdown.get('location_bonus', 0.0),
                                'experience_match': breakdown.get('experience_alignment', 0.0),
                                'skill_match': breakdown.get('title_bonus', 0.0),
                                'company_preference': breakdown.get('company_bonus', 0.0),
                                'total_score': score,
                                'algorithm': breakdown.get('algorithm', 'enhanced_v1'),
                                'breakdown': breakdown
                            }):
                                jobs_scored += 1

                        except Exception as job_error:
                            logger.error(f"Error scoring job: {job_error}")
                            results['errors'].append(f"Scoring error: {job_error}")

                    logger.info(f"✅ Scored {jobs_scored} jobs")

            # Step 4: Get high-scoring jobs
            high_jobs = self.db_manager.get_high_scored_jobs(
                min_score=self.config['min_score_threshold'],
                since_hours=self.config['email_lookback_hours']
            )
            results['high_scoring_jobs'] = len(high_jobs)

            logger.info(f"🎯 Found {len(high_jobs)} high-scoring jobs (>= {self.config['min_score_threshold']})")

            # Display top jobs
            for i, job in enumerate(high_jobs[:5], 1):
                logger.info(f"{i}. [{job.get('total_score', 0):.1f}] {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")

            # Step 5: Update last run time
            self.update_last_run_time()

            # Mark as successful
            results['success'] = True

            # Update execution log
            self.db_manager.update_execution_log(
                log_id,
                jobs_processed=results['jobs_fetched'],
                jobs_stored=results['jobs_stored'],
                jobs_duplicates=results['jobs_duplicates'],
                errors_count=len(results['errors']),
                status='completed'
            )

            logger.info("✅ Job monitoring run completed successfully")

            return results

        except Exception as e:
            error_msg = f"Critical error in job monitoring run: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

            # Update execution log with error
            self.db_manager.update_execution_log(
                log_id,
                status='failed',
                error_message=str(e),
                errors_count=len(results['errors'])
            )

            # Log system health
            self.db_manager.log_system_health('job_monitor', 'critical', error_msg, {'error': str(e)})

            return results


def main():
    """Main entry point for command line usage"""
    logger.info("🚀 Robust Job Monitor Starting")

    try:
        monitor = RobustJobMonitor()
        results = monitor.run(fetch_new=True, send_email=False)

        if results['success']:
            print(f"✅ Success: {results['jobs_stored']} jobs stored, {results['high_scoring_jobs']} high-scoring")
        else:
            print(f"❌ Failed with {len(results['errors'])} errors")
            for error in results['errors']:
                print(f"   - {error}")

        # Print database stats
        db_stats = monitor.db_manager.get_database_stats()
        print(f"📊 Database: {db_stats.get('total_jobs', 0)} total jobs, {db_stats.get('high_score_jobs', 0)} high-scoring")

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"💥 Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
