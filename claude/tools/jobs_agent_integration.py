#!/usr/bin/env python3
"""
LinkedIn MCP + Jobs Agent Integration
====================================

Enhances job search targeting and application strategies using LinkedIn
network intelligence. Integrates LinkedIn connection data with job
opportunities to provide insider insights and warm introduction paths.

Features:
- Connection-based job targeting
- Insider referral pathway identification  
- Company intelligence from network
- Warm introduction recommendations
- Network-based job prioritization
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class NetworkJobInsight:
    """Insight linking LinkedIn network to job opportunity"""
    job_id: str
    company_name: str
    network_connections: List[Dict[str, Any]]
    referral_strength: float
    insider_intelligence: Dict[str, Any]
    recommended_approach: str
    warm_intro_path: Optional[str] = None

@dataclass
class CompanyNetworkIntelligence:
    """Intelligence about company from LinkedIn network"""
    company_name: str
    total_connections: int
    senior_connections: int
    recent_connections: int
    departments_represented: List[str]
    average_tenure: Optional[float]
    growth_indicators: List[str]
    culture_insights: List[str]
    insider_tips: List[str]

class LinkedInJobsIntegration:
    """Integration system between LinkedIn MCP and Jobs Agent"""
    
    def __init__(self, linkedin_data_path: str = None):
        self.setup_logging()
        self.linkedin_data = self._load_linkedin_data(linkedin_data_path)
        self.company_networks = self._build_company_networks()
        
    def setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger('LinkedInJobsIntegration')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
    def _load_linkedin_data(self, data_path: str = None) -> List[Dict[str, Any]]:
        """Load LinkedIn connection data"""
        if data_path is None:
            data_path = Path("~/Downloads/linkedin_data/enriched_connections.json").expanduser()
        else:
            data_path = Path(data_path)
            
        if not data_path.exists():
            self.logger.warning(f"LinkedIn data not found at {data_path}")
            return []
            
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('connections', [])
        except Exception as e:
            self.logger.error(f"Error loading LinkedIn data: {e}")
            return []
            
    def _build_company_networks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build company-based network mapping"""
        company_networks = {}
        
        for connection in self.linkedin_data:
            company = connection.get('company', '').strip()
            if company:
                # Normalize company name
                company_normalized = self._normalize_company_name(company)
                
                if company_normalized not in company_networks:
                    company_networks[company_normalized] = []
                    
                company_networks[company_normalized].append(connection)
                
        self.logger.info(f"Built network mapping for {len(company_networks)} companies")
        return company_networks
        
    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for matching"""
        # Remove common suffixes and normalize
        normalized = company_name.lower().strip()
        
        # Remove common corporate suffixes
        suffixes = [' pty ltd', ' ltd', ' inc', ' corporation', ' corp', ' llc', 
                   ' limited', ' gmbh', ' ag', ' sa', ' plc', ' bv']
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                
        return normalized
        
    def find_network_connections_for_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Find all network connections at a specific company"""
        company_normalized = self._normalize_company_name(company_name)
        
        # Direct matches
        direct_matches = self.company_networks.get(company_normalized, [])
        
        # Fuzzy matches (partial company name matches)
        fuzzy_matches = []
        for network_company, connections in self.company_networks.items():
            if (company_normalized in network_company or 
                network_company in company_normalized):
                if network_company != company_normalized:  # Avoid duplicates
                    fuzzy_matches.extend(connections)
                    
        all_matches = direct_matches + fuzzy_matches
        
        # Remove duplicates based on connection ID
        seen_ids = set()
        unique_matches = []
        for connection in all_matches:
            conn_id = connection.get('first_name', '') + connection.get('last_name', '') + connection.get('email', '')
            if conn_id not in seen_ids:
                seen_ids.add(conn_id)
                unique_matches.append(connection)
                
        return unique_matches
        
    def analyze_company_network_intelligence(self, company_name: str) -> CompanyNetworkIntelligence:
        """Analyze network intelligence for a specific company"""
        connections = self.find_network_connections_for_company(company_name)
        
        if not connections:
            return CompanyNetworkIntelligence(
                company_name=company_name,
                total_connections=0,
                senior_connections=0,
                recent_connections=0,
                departments_represented=[],
                average_tenure=None,
                growth_indicators=[],
                culture_insights=[],
                insider_tips=[]
            )
            
        # Analyze connections
        total_connections = len(connections)
        senior_connections = len([c for c in connections 
                                if c.get('seniority_level') in ['C-Suite', 'VP/SVP', 'Director']])
        
        # Recent connections (within last year)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(days=365)
        recent_connections = 0
        
        for conn in connections:
            try:
                connected_date = datetime.strptime(conn.get('connected_on', ''), "%d %b %Y")
                if connected_date >= recent_cutoff:
                    recent_connections += 1
            except:
                pass
                
        # Departments represented
        departments = set()
        for conn in connections:
            func_area = conn.get('functional_area')
            if func_area:
                departments.add(func_area)
                
        # Growth indicators
        growth_indicators = []
        if recent_connections > total_connections * 0.3:
            growth_indicators.append("High recent hiring activity")
        if senior_connections > total_connections * 0.4:
            growth_indicators.append("Strong senior leadership presence in network")
        if len(departments) > 5:
            growth_indicators.append("Diverse functional areas represented")
            
        # Culture insights (based on functional areas and seniority)
        culture_insights = []
        engineering_heavy = len([c for c in connections if c.get('functional_area') == 'Engineering']) > total_connections * 0.4
        if engineering_heavy:
            culture_insights.append("Engineering-driven culture")
            
        strategy_heavy = len([c for c in connections if c.get('functional_area') == 'Strategy']) > total_connections * 0.2
        if strategy_heavy:
            culture_insights.append("Strategy and planning focused")
            
        # Insider tips based on connection analysis
        insider_tips = []
        if senior_connections > 0:
            insider_tips.append(f"You have {senior_connections} senior-level connections who could provide referrals")
        if recent_connections > 0:
            insider_tips.append(f"{recent_connections} connections joined recently - they may know about current opportunities")
            
        return CompanyNetworkIntelligence(
            company_name=company_name,
            total_connections=total_connections,
            senior_connections=senior_connections,
            recent_connections=recent_connections,
            departments_represented=list(departments),
            average_tenure=None,  # Would need additional data
            growth_indicators=growth_indicators,
            culture_insights=culture_insights,
            insider_tips=insider_tips
        )
        
    def calculate_referral_strength(self, connections: List[Dict[str, Any]]) -> float:
        """Calculate referral strength for a set of connections (0-1)"""
        if not connections:
            return 0.0
            
        total_strength = 0.0
        
        for connection in connections:
            connection_strength = 0.5  # Base strength
            
            # Seniority bonus
            seniority_bonus = {
                'C-Suite': 0.4,
                'VP/SVP': 0.3,
                'Director': 0.25,
                'Manager': 0.15,
                'Senior IC': 0.1
            }
            seniority = connection.get('seniority_level', '')
            connection_strength += seniority_bonus.get(seniority, 0.0)
            
            # Email availability bonus
            if connection.get('email'):
                connection_strength += 0.15
                
            # Recent connection bonus
            try:
                connected_date = datetime.strptime(connection.get('connected_on', ''), "%d %b %Y")
                days_ago = (datetime.now() - connected_date).days
                if days_ago < 180:  # Within 6 months
                    connection_strength += 0.1
                elif days_ago < 365:  # Within 1 year
                    connection_strength += 0.05
            except:
                pass
                
            total_strength += min(connection_strength, 1.0)
            
        # Return average strength, capped at 1.0
        return min(total_strength / len(connections), 1.0)
        
    def generate_warm_intro_path(self, connections: List[Dict[str, Any]]) -> Optional[str]:
        """Generate recommended warm introduction path"""
        if not connections:
            return None
            
        # Find the best connection for introduction
        best_connection = max(connections, key=lambda c: (
            {'C-Suite': 5, 'VP/SVP': 4, 'Director': 3, 'Manager': 2, 'Senior IC': 1}.get(c.get('seniority_level', ''), 0) +
            (2 if c.get('email') else 0) +
            (1 if c.get('functional_area') in ['Strategy', 'Operations', 'HR'] else 0)
        ))
        
        name = f"{best_connection.get('first_name', '')} {best_connection.get('last_name', '')}".strip()
        position = best_connection.get('position', 'Unknown Position')
        seniority = best_connection.get('seniority_level', '')
        
        if seniority in ['C-Suite', 'VP/SVP', 'Director']:
            return f"Direct outreach to {name} ({position}) - senior level contact with decision-making influence"
        elif best_connection.get('functional_area') == 'HR':
            return f"Contact {name} ({position}) - HR connection can provide hiring process insights"
        elif best_connection.get('email'):
            return f"Email outreach to {name} ({position}) - has contact information available"
        else:
            return f"LinkedIn message to {name} ({position}) - warm connection for company insights"
            
    def enhance_job_with_network_intelligence(self, job_data: Dict[str, Any]) -> NetworkJobInsight:
        """Enhance job data with LinkedIn network intelligence"""
        
        company_name = job_data.get('company', '')
        job_id = job_data.get('job_id', 'unknown')
        
        # Find network connections at this company
        connections = self.find_network_connections_for_company(company_name)
        
        # Calculate referral strength
        referral_strength = self.calculate_referral_strength(connections)
        
        # Generate company intelligence
        company_intel = self.analyze_company_network_intelligence(company_name)
        
        # Generate warm intro path
        warm_intro_path = self.generate_warm_intro_path(connections)
        
        # Generate recommended approach
        approach = self._generate_recommended_approach(referral_strength, connections, company_intel)
        
        return NetworkJobInsight(
            job_id=job_id,
            company_name=company_name,
            network_connections=connections[:5],  # Top 5 connections
            referral_strength=referral_strength,
            insider_intelligence=asdict(company_intel),
            recommended_approach=approach,
            warm_intro_path=warm_intro_path
        )
        
    def _generate_recommended_approach(self, 
                                     referral_strength: float,
                                     connections: List[Dict[str, Any]],
                                     company_intel: CompanyNetworkIntelligence) -> str:
        """Generate recommended application approach"""
        
        if referral_strength >= 0.8:
            return "🎯 INSIDER TRACK: Leverage strong network connections for warm referral before applying"
        elif referral_strength >= 0.6:
            return "🤝 NETWORK APPROACH: Reach out to connections for company insights, then apply with context"
        elif referral_strength >= 0.4:
            return "📧 INFORMED APPLICATION: Gather network intelligence, mention connections in cover letter"
        elif len(connections) > 0:
            return "💡 CONNECTION MENTION: Reference your LinkedIn connections during application process"
        else:
            return "📝 STANDARD APPLICATION: No direct network connections - focus on standard application excellence"
            
    def prioritize_jobs_by_network_strength(self, jobs: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Prioritize job opportunities by network connection strength"""
        
        job_network_scores = []
        
        for job in jobs:
            company_name = job.get('company', '')
            connections = self.find_network_connections_for_company(company_name)
            referral_strength = self.calculate_referral_strength(connections)
            
            # Combine with existing job score if available
            base_score = job.get('score', 0.5)
            
            # Network boost (max 20% boost to base score)
            network_boost = referral_strength * 0.2
            combined_score = base_score + network_boost
            
            job_network_scores.append((job, combined_score))
            
        # Sort by combined score
        job_network_scores.sort(key=lambda x: x[1], reverse=True)
        
        return job_network_scores
        
    def generate_network_job_report(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive network-enhanced job analysis report"""
        
        if not jobs:
            return {"error": "No jobs provided for analysis"}
            
        # Analyze each job with network intelligence
        enhanced_jobs = []
        total_network_connections = 0
        jobs_with_networks = 0
        
        for job in jobs:
            network_insight = self.enhance_job_with_network_intelligence(job)
            enhanced_jobs.append(network_insight)
            
            if network_insight.network_connections:
                jobs_with_networks += 1
                total_network_connections += len(network_insight.network_connections)
                
        # Calculate statistics
        avg_connections_per_job = total_network_connections / len(jobs) if jobs else 0
        network_coverage = (jobs_with_networks / len(jobs)) * 100 if jobs else 0
        
        # Find top network opportunities
        top_network_jobs = sorted(enhanced_jobs, key=lambda x: x.referral_strength, reverse=True)[:10]
        
        return {
            "total_jobs_analyzed": len(jobs),
            "jobs_with_network_connections": jobs_with_networks,
            "network_coverage_percentage": network_coverage,
            "average_connections_per_job": avg_connections_per_job,
            "top_network_opportunities": [asdict(job) for job in top_network_jobs],
            "recommendations": {
                "immediate_network_outreach": len([j for j in enhanced_jobs if j.referral_strength >= 0.7]),
                "informed_applications": len([j for j in enhanced_jobs if 0.4 <= j.referral_strength < 0.7]),
                "standard_applications": len([j for j in enhanced_jobs if j.referral_strength < 0.4])
            }
        }

# Integration functions for Jobs Agent
def enhance_jobs_with_linkedin_intelligence(jobs_data: List[Dict[str, Any]], 
                                          linkedin_data_path: str = None) -> Dict[str, Any]:
    """Main function to enhance job data with LinkedIn intelligence"""
    
    integrator = LinkedInJobsIntegration(linkedin_data_path)
    report = integrator.generate_network_job_report(jobs_data)
    
    return report

def get_company_network_intelligence(company_name: str, 
                                   linkedin_data_path: str = None) -> CompanyNetworkIntelligence:
    """Get network intelligence for a specific company"""
    
    integrator = LinkedInJobsIntegration(linkedin_data_path)
    return integrator.analyze_company_network_intelligence(company_name)

# Testing and demonstration
def main():
    """Demo the LinkedIn Jobs Agent integration"""
    print("🔗 LinkedIn + Jobs Agent Integration")
    print("=" * 50)
    
    # Demo job data
    demo_jobs = [
        {
            "job_id": "job_001",
            "company": "Microsoft",
            "title": "Senior Business Relationship Manager",
            "score": 0.85
        },
        {
            "job_id": "job_002", 
            "company": "Commonwealth Bank",
            "title": "Technology Business Partner",
            "score": 0.75
        },
        {
            "job_id": "job_003",
            "company": "Unknown Startup",
            "title": "Strategic Operations Manager", 
            "score": 0.70
        }
    ]
    
    # Test integration (will work with mock data until LinkedIn export available)
    integrator = LinkedInJobsIntegration()
    
    if not integrator.linkedin_data:
        print("⏳ LinkedIn data not available - using demo mode")
        print("\nDemo capabilities:")
        print("✅ Company network analysis")
        print("✅ Referral strength calculation")
        print("✅ Warm introduction path generation")
        print("✅ Job prioritization by network strength")
        print("✅ Network-enhanced application strategies")
        
    else:
        print("🚀 Running network-enhanced job analysis...")
        report = integrator.generate_network_job_report(demo_jobs)
        
        print(f"📊 Analysis Results:")
        print(f"   • Network Coverage: {report['network_coverage_percentage']:.1f}%")
        print(f"   • Jobs with Connections: {report['jobs_with_network_connections']}")
        print(f"   • Immediate Network Outreach: {report['recommendations']['immediate_network_outreach']}")
        
    print("\n✅ LinkedIn-Jobs integration ready for data import!")

if __name__ == "__main__":
    main()