#!/usr/bin/env python3
"""
LinkedIn MCP Testing Framework

Comprehensive testing system for LinkedIn data processing pipeline
including mock data generation, integration testing, and validation.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import random
import string
from dataclasses import dataclass
from unittest.mock import Mock

# Import our LinkedIn MCP components
from data_enrichment_pipeline import LinkedInDataEnrichmentPipeline
from connection_scoring_system import ConnectionScoringSystem
from jobs_agent_integration import LinkedInJobsIntegration
from data_backup_system import LinkedInBackupSystem


@dataclass
class TestDataConfig:
    """Configuration for test data generation"""
    num_connections: int = 100
    num_companies: int = 50
    num_industries: List[str] = None
    num_seniority_levels: List[str] = None
    include_incomplete_profiles: bool = True
    geographic_diversity: bool = True


class MockLinkedInDataGenerator:
    """Generate realistic mock LinkedIn data for testing"""
    
    def __init__(self, config: TestDataConfig = None):
        self.config = config or TestDataConfig()
        
        # Sample data pools
        self.first_names = [
            "James", "Sarah", "Michael", "Emma", "David", "Lisa", "John", "Anna",
            "Robert", "Maria", "William", "Jennifer", "Richard", "Jessica", "Joseph", "Ashley",
            "Thomas", "Amanda", "Christopher", "Melissa", "Daniel", "Deborah", "Matthew", "Rachel"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"
        ]
        
        self.industries = self.config.num_industries or [
            "Technology", "Healthcare", "Finance", "Education", "Manufacturing",
            "Retail", "Energy", "Construction", "Consulting", "Media & Communications",
            "Government", "Mining", "Aviation", "Automotive", "Real Estate"
        ]
        
        self.seniority_levels = self.config.num_seniority_levels or [
            "Entry Level", "Associate", "Senior", "Lead", "Principal", "Manager",
            "Senior Manager", "Director", "Senior Director", "VP", "SVP", "C-Level"
        ]
        
        self.companies = [
            # Australian companies
            "BHP", "Commonwealth Bank", "Westpac", "ANZ", "NAB", "Telstra", "Woolworths",
            "Wesfarmers", "Rio Tinto", "Fortescue Metals", "Origin Energy", "Santos",
            "Qantas", "REA Group", "Atlassian", "Canva", "Xero", "Afterpay",
            
            # International companies
            "Microsoft", "Google", "Amazon", "Apple", "Meta", "Netflix", "Tesla",
            "JPMorgan Chase", "Goldman Sachs", "McKinsey & Company", "Deloitte",
            "PwC", "KPMG", "EY", "Accenture", "IBM", "Oracle", "Salesforce"
        ]
        
        self.job_functions = [
            "Software Engineering", "Product Management", "Business Development",
            "Sales", "Marketing", "Human Resources", "Finance", "Operations",
            "Strategy", "Consulting", "Data Science", "Engineering", "Design",
            "Legal", "Compliance", "Risk Management", "Project Management"
        ]
        
        self.locations = [
            "Sydney, NSW", "Melbourne, VIC", "Brisbane, QLD", "Perth, WA",
            "Adelaide, SA", "Canberra, ACT", "Darwin, NT", "Hobart, TAS",
            # International
            "New York, NY", "San Francisco, CA", "London, UK", "Singapore",
            "Tokyo, Japan", "Toronto, Canada", "Dubai, UAE"
        ]
    
    def generate_connection(self) -> Dict[str, Any]:
        """Generate a single realistic LinkedIn connection"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        full_name = f"{first_name} {last_name}"
        
        company = random.choice(self.companies)
        industry = random.choice(self.industries)
        function = random.choice(self.job_functions)
        seniority = random.choice(self.seniority_levels)
        location = random.choice(self.locations)
        
        # Generate position title based on seniority and function
        if seniority in ["C-Level"]:
            titles = [f"Chief {function} Officer", f"CEO", f"CTO", f"CFO"]
        elif seniority in ["VP", "SVP"]:
            titles = [f"Vice President of {function}", f"VP {function}"]
        elif seniority == "Director":
            titles = [f"Director of {function}", f"{function} Director"]
        elif seniority == "Manager":
            titles = [f"{function} Manager", f"Senior {function} Manager"]
        else:
            titles = [f"{seniority} {function}", f"{function} {seniority}"]
        
        position = random.choice(titles)
        
        # Connection strength simulation
        connection_strength = random.choices(
            ["1st", "2nd", "3rd"],
            weights=[30, 50, 20]  # Most are 2nd connections
        )[0]
        
        # Mutual connections (for 2nd/3rd degree)
        mutual_connections = 0
        if connection_strength == "2nd":
            mutual_connections = random.randint(1, 15)
        elif connection_strength == "3rd":
            mutual_connections = random.randint(1, 5)
        
        connection = {
            "name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "position": position,
            "company": company,
            "industry": industry,
            "location": location,
            "connection_strength": connection_strength,
            "mutual_connections": mutual_connections,
            "profile_url": f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{random.randint(1000, 9999)}",
            "connected_date": self._random_date(days_back=random.randint(30, 1095)),  # 1 month to 3 years
            "last_interaction": self._random_date(days_back=random.randint(0, 365)) if random.random() > 0.3 else None
        }
        
        # Sometimes add incomplete profiles to test robustness
        if self.config.include_incomplete_profiles and random.random() < 0.1:
            fields_to_remove = random.sample(
                ["company", "industry", "location", "position"], 
                random.randint(1, 2)
            )
            for field in fields_to_remove:
                connection[field] = None
        
        return connection
    
    def _random_date(self, days_back: int) -> str:
        """Generate random date string"""
        random_date = datetime.now() - timedelta(days=random.randint(0, days_back))
        return random_date.strftime("%Y-%m-%d")
    
    def generate_profile(self) -> Dict[str, Any]:
        """Generate realistic LinkedIn profile data"""
        return {
            "name": "Naythan Dawe",
            "headline": "Senior Business Relationship Manager | Technology Strategy | Cloud Architecture",
            "location": "Perth, WA, Australia",
            "industry": "Information Technology & Services",
            "summary": "Experienced technology leader with 15+ years in business relationship management...",
            "experience": [
                {
                    "title": "Senior Client Partner",
                    "company": "Zetta",
                    "duration": "March 2025 - July 2025",
                    "description": "Portfolio management of ~15 enterprise clients..."
                },
                {
                    "title": "Senior Business Relationship Manager",
                    "company": "Previous Company",
                    "duration": "2020 - 2025",
                    "description": "Led technology portfolio governance..."
                }
            ],
            "education": [
                {
                    "institution": "University Example",
                    "degree": "Bachelor of Information Technology",
                    "field": "Computer Science",
                    "years": "2005 - 2009"
                }
            ],
            "skills": [
                "Business Relationship Management", "Portfolio Governance", "Azure",
                "Cloud Architecture", "Stakeholder Management", "Strategic Planning"
            ],
            "total_connections": self.config.num_connections
        }
    
    def generate_full_dataset(self) -> Dict[str, Any]:
        """Generate complete LinkedIn dataset for testing"""
        connections = [self.generate_connection() for _ in range(self.config.num_connections)]
        
        return {
            "profile": self.generate_profile(),
            "connections": connections,
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_connections": len(connections),
                "data_version": "1.0",
                "test_dataset": True
            }
        }


class LinkedInMCPTestSuite:
    """Comprehensive test suite for LinkedIn MCP components"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp())
        self.test_data = None
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": []
        }
    
    def setup_test_data(self, config: TestDataConfig = None) -> None:
        """Generate and save test data"""
        print("🔄 Generating test data...")
        
        generator = MockLinkedInDataGenerator(config)
        self.test_data = generator.generate_full_dataset()
        
        # Save test data to file
        test_data_path = self.temp_dir / "linkedin_test_data.json"
        with open(test_data_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        print(f"✅ Generated {len(self.test_data['connections'])} test connections")
        print(f"📁 Test data saved to: {test_data_path}")
    
    def test_data_enrichment_pipeline(self) -> bool:
        """Test the data enrichment pipeline"""
        print("\n🧪 Testing Data Enrichment Pipeline...")
        
        try:
            enricher = LinkedInDataEnrichmentPipeline()
            
            # Test individual connection enrichment
            sample_connection = self.test_data["connections"][0]
            enriched_connection = enricher.enrich_connection(sample_connection)
            
            # Verify enrichment worked and returned EnrichedConnection object
            if not hasattr(enriched_connection, 'company_industry'):
                raise ValueError("Enriched connection missing company_industry field")
            
            if not hasattr(enriched_connection, 'business_value_score'):
                raise ValueError("Enriched connection missing business_value_score field")
            
            # Test batch enrichment by enriching multiple connections
            batch_enriched = []
            for conn in self.test_data["connections"][:5]:  # Test fewer for speed
                enriched = enricher.enrich_connection(conn)
                batch_enriched.append(enriched)
            
            if len(batch_enriched) != 5:
                raise ValueError(f"Expected 5 enriched connections, got {len(batch_enriched)}")
            
            self._record_test_result("data_enrichment_pipeline", True)
            print("✅ Data enrichment pipeline tests passed")
            return True
            
        except Exception as e:
            self._record_test_result("data_enrichment_pipeline", False, str(e))
            print(f"❌ Data enrichment pipeline tests failed: {e}")
            return False
    
    def test_connection_scoring_system(self) -> bool:
        """Test the connection scoring system"""
        print("\n🧪 Testing Connection Scoring System...")
        
        try:
            scorer = ConnectionScoringSystem()
            
            # Test individual scoring models
            sample_connection = self.test_data["connections"][0]
            
            # Test different scoring models
            scoring_models = ["job_search", "business_development", "networking"]
            for model in scoring_models:
                score_result = scorer.calculate_composite_score(sample_connection, model)
                
                # Score result is a ConnectionScore object, check overall_score
                if not hasattr(score_result, 'overall_score') or not (0 <= score_result.overall_score <= 1):
                    raise ValueError(f"Invalid score result for model {model}")
            
            # Test batch scoring with score_all_connections
            batch_scores = scorer.score_all_connections(
                self.test_data["connections"][:5],  # Test fewer for speed
                "job_search"
            )
            
            if len(batch_scores) != 5:
                raise ValueError(f"Expected 5 scores, got {len(batch_scores)}")
            
            # Test top connections method
            top_connections = scorer.get_top_connections(
                self.test_data["connections"][:10],
                "job_search",
                top_n=5
            )
            
            if len(top_connections) > 5:
                raise ValueError(f"get_top_connections returned too many results: {len(top_connections)}")
            
            self._record_test_result("connection_scoring_system", True)
            print("✅ Connection scoring system tests passed")
            return True
            
        except Exception as e:
            self._record_test_result("connection_scoring_system", False, str(e))
            print(f"❌ Connection scoring system tests failed: {e}")
            return False
    
    def test_jobs_agent_integration(self) -> bool:
        """Test LinkedIn-Jobs Agent integration"""
        print("\n🧪 Testing LinkedIn-Jobs Agent Integration...")
        
        try:
            # Create mock job opportunities
            mock_jobs = [
                {
                    "title": "Senior Business Relationship Manager",
                    "company": "Tech Corp",
                    "location": "Perth, WA",
                    "initial_score": 8.5
                },
                {
                    "title": "Product Manager",
                    "company": "Innovation Ltd",
                    "location": "Sydney, NSW", 
                    "initial_score": 7.2
                }
            ]
            
            integration = LinkedInJobsIntegration()
            
            # Test network-based enhancement
            enhanced_jobs = []
            for job in mock_jobs:
                enhanced_job = integration.enhance_job_with_network_intelligence(job)
                enhanced_jobs.append(enhanced_job)
            
            # Verify enhancements were added (NetworkJobInsight objects)
            for enhanced_job in enhanced_jobs:
                if not hasattr(enhanced_job, 'network_connections'):
                    raise ValueError("Enhanced job missing network_connections attribute")
                
                if not hasattr(enhanced_job, 'warm_intro_path'):
                    raise ValueError("Enhanced job missing warm_intro_path attribute")
                
                if not hasattr(enhanced_job, 'insider_intelligence'):
                    raise ValueError("Enhanced job missing insider_intelligence attribute")
            
            self._record_test_result("jobs_agent_integration", True)
            print("✅ LinkedIn-Jobs Agent integration tests passed")
            return True
            
        except Exception as e:
            self._record_test_result("jobs_agent_integration", False, str(e))
            print(f"❌ LinkedIn-Jobs Agent integration tests failed: {e}")
            return False
    
    def test_backup_system(self) -> bool:
        """Test the backup and versioning system"""
        print("\n🧪 Testing Backup System...")
        
        try:
            # Create backup system with test directory
            backup_dir = self.temp_dir / "backups_test"
            backup_system = LinkedInBackupSystem(str(backup_dir))
            
            # Test backup creation
            version_id = backup_system.create_backup(self.test_data, "test")
            
            if not version_id:
                raise ValueError("Backup creation failed - no version ID returned")
            
            # Test backup listing
            backups = backup_system.list_backups()
            if len(backups) != 1 or backups[0]["version_id"] != version_id:
                raise ValueError("Backup listing failed")
            
            # Test backup restoration
            restored_data = backup_system.restore_backup(version_id)
            
            # Verify data integrity
            if restored_data != self.test_data:
                raise ValueError("Restored data does not match original")
            
            # Test integrity verification
            integrity_results = backup_system.verify_backup_integrity()
            if integrity_results["successful"] != 1:
                raise ValueError("Backup integrity verification failed")
            
            self._record_test_result("backup_system", True)
            print("✅ Backup system tests passed")
            return True
            
        except Exception as e:
            self._record_test_result("backup_system", False, str(e))
            print(f"❌ Backup system tests failed: {e}")
            return False
    
    def test_end_to_end_pipeline(self) -> bool:
        """Test complete end-to-end processing pipeline"""
        print("\n🧪 Testing End-to-End Pipeline...")
        
        try:
            # Initialize all components
            enricher = LinkedInDataEnrichmentPipeline()
            scorer = ConnectionScoringSystem()
            integration = LinkedInJobsIntegration()
            
            # Step 1: Enrich connections
            enriched_connections = []
            for conn in self.test_data["connections"][:10]:  # Smaller batch for testing
                enriched = enricher.enrich_connection(conn)
                enriched_connections.append(enriched)
            
            # Step 2: Score connections for different models  
            connection_scores = scorer.score_all_connections(self.test_data["connections"][:10], "job_search")
            
            # Step 3: Find high-value connections (score >= 0.7)
            high_value_connections = [
                score for score in connection_scores
                if score.overall_score >= 0.7
            ]
            
            # Step 4: Test with mock job and network enhancement
            mock_job = {
                "title": "Senior Business Relationship Manager",
                "company": "BHP",
                "location": "Perth, WA",
                "initial_score": 8.0
            }
            
            enhanced_job = integration.enhance_job_with_network_intelligence(mock_job)
            
            # Verify pipeline completeness
            if not enriched_connections:
                raise ValueError("Pipeline failed: No enriched connections")
            
            if not connection_scores:
                raise ValueError("Pipeline failed: No connection scores")
            
            if not hasattr(enhanced_job, 'network_connections'):
                raise ValueError("Pipeline failed: Job not enhanced with network data")
            
            self._record_test_result("end_to_end_pipeline", True)
            print(f"✅ End-to-End pipeline tests passed")
            print(f"   📊 Processed {len(enriched_connections)} connections")
            print(f"   ⭐ Found {len(high_value_connections)} high-value connections")
            print(f"   🎯 Job enhanced with {len(enhanced_job.network_connections)} network connections")
            return True
            
        except Exception as e:
            self._record_test_result("end_to_end_pipeline", False, str(e))
            print(f"❌ End-to-End pipeline tests failed: {e}")
            return False
    
    def _record_test_result(self, test_name: str, passed: bool, error: str = None) -> None:
        """Record test result for reporting"""
        self.results["tests_run"] += 1
        
        if passed:
            self.results["tests_passed"] += 1
        else:
            self.results["tests_failed"] += 1
            self.results["failures"].append({
                "test": test_name,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🚀 Starting LinkedIn MCP Test Suite...")
        print(f"📁 Test directory: {self.temp_dir}")
        
        # Setup test data
        self.setup_test_data()
        
        # Run all tests
        tests = [
            self.test_data_enrichment_pipeline,
            self.test_connection_scoring_system,
            self.test_jobs_agent_integration,
            self.test_backup_system,
            self.test_end_to_end_pipeline
        ]
        
        for test in tests:
            test()
        
        # Generate final report
        return self.generate_test_report()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        success_rate = (self.results["tests_passed"] / self.results["tests_run"]) * 100
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "tests_run": self.results["tests_run"],
                "tests_passed": self.results["tests_passed"],
                "tests_failed": self.results["tests_failed"],
                "success_rate": round(success_rate, 1)
            },
            "test_data": {
                "connections_generated": len(self.test_data["connections"]) if self.test_data else 0,
                "data_completeness": "100%"
            },
            "failures": self.results["failures"],
            "recommendations": self._generate_test_recommendations()
        }
        
        # Save report
        report_path = self.temp_dir / "test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 TEST SUITE COMPLETE")
        print(f"✅ Passed: {report['summary']['tests_passed']}/{report['summary']['tests_run']}")
        print(f"📈 Success Rate: {report['summary']['success_rate']}%")
        print(f"📄 Report saved: {report_path}")
        
        if self.results["failures"]:
            print(f"❌ Failures: {len(self.results['failures'])}")
            for failure in self.results["failures"]:
                print(f"   - {failure['test']}: {failure['error']}")
        
        return report
    
    def _generate_test_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.results["tests_failed"] == 0:
            recommendations.append("All tests passed - LinkedIn MCP ready for production")
            recommendations.append("Consider setting up automated testing pipeline")
        else:
            recommendations.append("Address failing tests before production deployment")
            recommendations.append("Review error logs and fix underlying issues")
        
        recommendations.append("Run integration tests with real LinkedIn export data when available")
        recommendations.append("Set up monitoring and alerting for production system")
        
        return recommendations


def run_linkedin_mcp_tests(test_config: TestDataConfig = None) -> Dict[str, Any]:
    """
    Convenience function to run LinkedIn MCP tests
    
    Args:
        test_config: Configuration for test data generation
        
    Returns:
        Test results report
    """
    # Create test suite
    test_suite = LinkedInMCPTestSuite()
    
    # Use provided config or create default
    if test_config is None:
        test_config = TestDataConfig(
            num_connections=50,  # Smaller dataset for faster testing
            num_companies=20,
            include_incomplete_profiles=True
        )
    
    # Run tests
    results = test_suite.run_all_tests()
    
    return results


if __name__ == "__main__":
    # Run tests with default configuration
    print("🧪 LinkedIn MCP Testing Framework")
    print("=" * 50)
    
    test_results = run_linkedin_mcp_tests()
    
    # Print summary
    if test_results["summary"]["success_rate"] == 100:
        print("\n🎉 ALL TESTS PASSED! LinkedIn MCP system is ready for deployment.")
    else:
        print(f"\n⚠️  Some tests failed. Success rate: {test_results['summary']['success_rate']}%")
        print("Review the failures above and fix issues before deploying.")