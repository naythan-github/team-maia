#!/usr/bin/env python3
"""
LinkedIn Data Enrichment Pipeline
=================================

Advanced preprocessing and enrichment system for LinkedIn exports.
Prepares data for maximum intelligence extraction and analysis.

Features:
- Data cleaning and normalization
- Company intelligence enrichment  
- Industry classification
- Connection scoring and ranking
- Geographic analysis
- Career progression modeling
"""

import re
import csv
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

@dataclass
class EnrichedConnection:
    """Enhanced connection data with intelligence"""
    # Original LinkedIn data
    first_name: str
    last_name: str
    email: str
    company: str
    position: str
    connected_on: str
    
    # Enriched data
    company_domain: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    seniority_level: Optional[str] = None
    functional_area: Optional[str] = None
    geographic_region: Optional[str] = None
    connection_strength: Optional[float] = None
    business_value_score: Optional[float] = None
    last_interaction: Optional[str] = None
    
    # Intelligence flags
    is_decision_maker: bool = False
    is_recruiter: bool = False
    is_potential_client: bool = False
    is_industry_expert: bool = False
    is_alumni: bool = False

class LinkedInDataEnrichmentPipeline:
    """Main enrichment pipeline for LinkedIn data"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("~/Downloads/linkedin_data").expanduser()
        self.setup_logging()
        self.load_enrichment_databases()
        
        # Processing statistics
        self.stats = {
            "total_connections": 0,
            "enriched_connections": 0,
            "company_matches": 0,
            "industry_classifications": 0,
            "seniority_classifications": 0,
            "geographic_mappings": 0,
            "processing_time": 0
        }
        
    def setup_logging(self):
        """Configure logging for enrichment pipeline"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('LinkedInEnrichment')
        
    def load_enrichment_databases(self):
        """Load databases for data enrichment"""
        
        # Company domain mapping (for email domain inference)
        self.company_domains = {
            # Technology Companies
            "Microsoft": ["microsoft.com", "outlook.com"],
            "Google": ["google.com", "gmail.com"],
            "Amazon": ["amazon.com", "aws.amazon.com"],
            "Apple": ["apple.com", "icloud.com"],
            "Meta": ["meta.com", "facebook.com", "instagram.com"],
            "Netflix": ["netflix.com"],
            "Salesforce": ["salesforce.com"],
            "Oracle": ["oracle.com"],
            "SAP": ["sap.com"],
            "IBM": ["ibm.com"],
            
            # Australian Companies
            "Commonwealth Bank": ["cba.com.au", "commbank.com.au"],
            "Westpac": ["westpac.com.au"],
            "ANZ": ["anz.com"],
            "NAB": ["nab.com.au"],
            "Telstra": ["telstra.com", "telstra.com.au"],
            "BHP": ["bhp.com"],
            "Rio Tinto": ["riotinto.com"],
            "Woolworths": ["woolworths.com.au"],
            "Coles": ["coles.com.au"],
            "Qantas": ["qantas.com", "qantas.com.au"],
            
            # Consulting
            "McKinsey": ["mckinsey.com"],
            "BCG": ["bcg.com"],
            "Bain": ["bain.com"],
            "Deloitte": ["deloitte.com", "deloitte.com.au"],
            "PwC": ["pwc.com", "pwc.com.au"],
            "EY": ["ey.com"],
            "KPMG": ["kpmg.com", "kpmg.com.au"],
            "Accenture": ["accenture.com"],
        }
        
        # Industry classification patterns
        self.industry_patterns = {
            "Technology": [
                "software", "tech", "IT", "cloud", "AI", "machine learning",
                "data science", "cybersecurity", "fintech", "saas", "platform"
            ],
            "Financial Services": [
                "bank", "finance", "investment", "trading", "insurance", 
                "wealth", "asset management", "capital markets", "fintech"
            ],
            "Consulting": [
                "consulting", "advisory", "strategy", "transformation",
                "management consulting", "business consulting"
            ],
            "Healthcare": [
                "health", "medical", "pharmaceutical", "biotech", "hospital",
                "healthcare", "life sciences", "therapeutics"
            ],
            "Energy & Mining": [
                "mining", "oil", "gas", "energy", "renewable", "utilities",
                "resources", "petroleum", "coal", "solar", "wind"
            ],
            "Manufacturing": [
                "manufacturing", "automotive", "industrial", "production",
                "supply chain", "logistics", "operations"
            ],
            "Education": [
                "university", "education", "school", "research", "academic",
                "training", "learning", "teaching"
            ],
            "Government": [
                "government", "public sector", "federal", "state", "council",
                "department", "agency", "ministry"
            ]
        }
        
        # Seniority level classification
        self.seniority_patterns = {
            "C-Suite": [
                "CEO", "CTO", "CFO", "COO", "CMO", "CHRO", "Chief",
                "President", "Chairman", "Founder", "Co-founder"
            ],
            "VP/SVP": [
                "Vice President", "VP", "SVP", "Senior Vice President",
                "Executive Vice President", "EVP"
            ],
            "Director": [
                "Director", "Managing Director", "Executive Director",
                "Senior Director", "Associate Director"
            ],
            "Manager": [
                "Manager", "Senior Manager", "Team Lead", "Team Leader",
                "Head of", "Lead", "Principal", "Senior Principal"
            ],
            "Senior IC": [
                "Senior", "Staff", "Principal", "Architect", "Specialist",
                "Expert", "Consultant", "Senior Consultant"
            ],
            "Mid-Level": [
                "Analyst", "Associate", "Coordinator", "Officer",
                "Administrator", "Advisor"
            ],
            "Entry-Level": [
                "Junior", "Assistant", "Trainee", "Graduate", "Intern",
                "Entry", "New Grad"
            ]
        }
        
        # Functional area classification
        self.functional_areas = {
            "Engineering": [
                "engineer", "developer", "architect", "technical", "software",
                "systems", "platform", "infrastructure", "devops", "sre"
            ],
            "Product": [
                "product manager", "product owner", "product", "pm",
                "product marketing", "product strategy"
            ],
            "Sales": [
                "sales", "account manager", "business development", "bd",
                "sales manager", "account executive", "sales director"
            ],
            "Marketing": [
                "marketing", "brand", "communications", "pr", "content",
                "digital marketing", "growth", "demand generation"
            ],
            "Operations": [
                "operations", "ops", "supply chain", "logistics", "procurement",
                "process", "quality", "operational excellence"
            ],
            "Finance": [
                "finance", "accounting", "controller", "treasury", "fp&a",
                "financial analyst", "cfo", "financial planning"
            ],
            "HR": [
                "human resources", "hr", "people", "talent", "recruiting",
                "recruitment", "people ops", "chro", "organizational"
            ],
            "Legal": [
                "legal", "counsel", "lawyer", "attorney", "compliance",
                "regulatory", "general counsel", "legal affairs"
            ],
            "Data": [
                "data scientist", "data analyst", "data engineer", "analytics",
                "business intelligence", "bi", "data", "machine learning"
            ],
            "Strategy": [
                "strategy", "strategic", "business strategy", "corporate strategy",
                "planning", "transformation", "change management"
            ]
        }
        
        # Geographic region mapping
        self.geographic_regions = {
            "Australia": [
                "australia", "sydney", "melbourne", "brisbane", "perth", 
                "adelaide", "darwin", "canberra", "au", ".com.au"
            ],
            "United States": [
                "united states", "usa", "us", "san francisco", "new york", 
                "chicago", "boston", "seattle", "los angeles", "austin"
            ],
            "United Kingdom": [
                "united kingdom", "uk", "london", "manchester", "edinburgh",
                "birmingham", "bristol", ".co.uk"
            ],
            "Asia Pacific": [
                "singapore", "hong kong", "tokyo", "shanghai", "mumbai",
                "bangalore", "seoul", "taipei", "bangkok", "manila"
            ],
            "Europe": [
                "germany", "france", "netherlands", "switzerland", "sweden",
                "denmark", "norway", "finland", "berlin", "paris", "amsterdam"
            ]
        }
        
    def extract_company_domain(self, company: str, email: str = None) -> Optional[str]:
        """Extract or infer company domain"""
        if email and "@" in email:
            domain = email.split("@")[1].lower()
            # Check if it's a corporate domain (not gmail, outlook, etc.)
            generic_domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com"]
            if domain not in generic_domains:
                return domain
                
        # Check our company domain database
        company_clean = company.lower().strip()
        for comp_name, domains in self.company_domains.items():
            if comp_name.lower() in company_clean or company_clean in comp_name.lower():
                return domains[0]  # Return primary domain
                
        return None
        
    def classify_industry(self, company: str, position: str) -> Optional[str]:
        """Classify industry based on company and position"""
        text = f"{company} {position}".lower()
        
        for industry, patterns in self.industry_patterns.items():
            if any(pattern.lower() in text for pattern in patterns):
                return industry
                
        return None
        
    def classify_seniority(self, position: str) -> Optional[str]:
        """Classify seniority level based on position title"""
        position_clean = position.lower().strip()
        
        for level, patterns in self.seniority_patterns.items():
            if any(pattern.lower() in position_clean for pattern in patterns):
                return level
                
        return None
        
    def classify_functional_area(self, position: str) -> Optional[str]:
        """Classify functional area based on position"""
        position_clean = position.lower().strip()
        
        for area, patterns in self.functional_areas.items():
            if any(pattern.lower() in position_clean for pattern in patterns):
                return area
                
        return None
        
    def classify_geographic_region(self, company: str, position: str = "") -> Optional[str]:
        """Classify geographic region"""
        text = f"{company} {position}".lower()
        
        for region, patterns in self.geographic_regions.items():
            if any(pattern.lower() in text for pattern in patterns):
                return region
                
        return None
        
    def calculate_connection_strength(self, connection_data: Dict) -> float:
        """Calculate connection strength score (0-1)"""
        score = 0.5  # Base score
        
        # Factors that increase connection strength
        if connection_data.get("email"):
            score += 0.2  # Has email contact
            
        if connection_data.get("company"):
            score += 0.1  # Has company info
            
        if connection_data.get("position"):
            score += 0.1  # Has position info
            
        # Connected recently
        if connection_data.get("connected_on"):
            try:
                connected_date = datetime.strptime(connection_data["connected_on"], "%d %b %Y")
                days_ago = (datetime.now() - connected_date).days
                if days_ago < 30:
                    score += 0.2
                elif days_ago < 365:
                    score += 0.1
            except:
                pass
                
        return min(score, 1.0)
        
    def calculate_business_value_score(self, connection: EnrichedConnection) -> float:
        """Calculate business value score for targeting (0-1)"""
        score = 0.0
        
        # Seniority bonus
        seniority_bonus = {
            "C-Suite": 0.4,
            "VP/SVP": 0.3,
            "Director": 0.25,
            "Manager": 0.15,
            "Senior IC": 0.1,
            "Mid-Level": 0.05,
            "Entry-Level": 0.0
        }
        score += seniority_bonus.get(connection.seniority_level, 0.0)
        
        # Industry relevance (for your BRM background)
        high_value_industries = ["Technology", "Financial Services", "Consulting"]
        if connection.company_industry in high_value_industries:
            score += 0.3
        elif connection.company_industry:
            score += 0.1
            
        # Functional area relevance
        high_value_functions = ["Strategy", "Operations", "Product", "Engineering"]
        if connection.functional_area in high_value_functions:
            score += 0.2
        elif connection.functional_area:
            score += 0.1
            
        # Decision maker indicators
        if connection.is_decision_maker:
            score += 0.1
            
        return min(score, 1.0)
        
    def identify_special_flags(self, connection: EnrichedConnection) -> EnrichedConnection:
        """Identify special flags for connections"""
        position = connection.position.lower()
        company = connection.company.lower()
        
        # Decision maker patterns
        decision_patterns = ["ceo", "cto", "cfo", "president", "founder", "owner", "partner", "director"]
        connection.is_decision_maker = any(pattern in position for pattern in decision_patterns)
        
        # Recruiter patterns
        recruiter_patterns = ["recruit", "talent", "hr", "human resources", "hiring"]
        connection.is_recruiter = any(pattern in position or pattern in company for pattern in recruiter_patterns)
        
        # Potential client patterns (for consulting/BRM services)
        client_patterns = ["transformation", "strategy", "consulting", "advisory", "change management"]
        connection.is_potential_client = any(pattern in position for pattern in client_patterns)
        
        # Industry expert patterns
        expert_patterns = ["expert", "specialist", "consultant", "advisor", "thought leader", "principal"]
        connection.is_industry_expert = any(pattern in position for pattern in expert_patterns)
        
        # Alumni detection (would need education data)
        # connection.is_alumni = ... (implement when education data available)
        
        return connection
        
    def enrich_connection(self, raw_connection: Dict) -> EnrichedConnection:
        """Enrich a single connection with intelligence"""
        
        # Create enriched connection object
        connection = EnrichedConnection(
            first_name=raw_connection.get("First Name", ""),
            last_name=raw_connection.get("Last Name", ""),
            email=raw_connection.get("Email Address", ""),
            company=raw_connection.get("Company", ""),
            position=raw_connection.get("Position", ""),
            connected_on=raw_connection.get("Connected On", "")
        )
        
        # Apply enrichments
        connection.company_domain = self.extract_company_domain(connection.company, connection.email)
        connection.company_industry = self.classify_industry(connection.company, connection.position)
        connection.seniority_level = self.classify_seniority(connection.position)
        connection.functional_area = self.classify_functional_area(connection.position)
        connection.geographic_region = self.classify_geographic_region(connection.company, connection.position)
        connection.connection_strength = self.calculate_connection_strength(raw_connection)
        
        # Identify special flags
        connection = self.identify_special_flags(connection)
        
        # Calculate business value score (after all other enrichments)
        connection.business_value_score = self.calculate_business_value_score(connection)
        
        # Update statistics
        if connection.company_domain:
            self.stats["company_matches"] += 1
        if connection.company_industry:
            self.stats["industry_classifications"] += 1
        if connection.seniority_level:
            self.stats["seniority_classifications"] += 1
        if connection.geographic_region:
            self.stats["geographic_mappings"] += 1
            
        return connection
        
    def process_connections_file(self, file_path: Path) -> List[EnrichedConnection]:
        """Process LinkedIn connections CSV file"""
        self.logger.info(f"Processing connections file: {file_path}")
        start_time = time.time()
        
        enriched_connections = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    self.stats["total_connections"] += 1
                    
                    try:
                        enriched_connection = self.enrich_connection(row)
                        enriched_connections.append(enriched_connection)
                        self.stats["enriched_connections"] += 1
                        
                        if self.stats["enriched_connections"] % 100 == 0:
                            self.logger.info(f"Processed {self.stats['enriched_connections']} connections...")
                            
                    except Exception as e:
                        self.logger.warning(f"Error enriching connection: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error reading connections file: {e}")
            return []
            
        self.stats["processing_time"] = time.time() - start_time
        self.logger.info(f"Enrichment complete: {len(enriched_connections)} connections in {self.stats['processing_time']:.1f}s")
        
        return enriched_connections
        
    def generate_intelligence_report(self, connections: List[EnrichedConnection]) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        
        if not connections:
            return {"error": "No connections data available"}
            
        # Basic statistics
        total_connections = len(connections)
        connections_with_email = sum(1 for c in connections if c.email)
        
        # Industry breakdown
        industries = {}
        for conn in connections:
            if conn.company_industry:
                industries[conn.company_industry] = industries.get(conn.company_industry, 0) + 1
                
        # Seniority breakdown
        seniority = {}
        for conn in connections:
            if conn.seniority_level:
                seniority[conn.seniority_level] = seniority.get(conn.seniority_level, 0) + 1
                
        # Geographic breakdown
        regions = {}
        for conn in connections:
            if conn.geographic_region:
                regions[conn.geographic_region] = regions.get(conn.geographic_region, 0) + 1
                
        # Top companies
        companies = {}
        for conn in connections:
            if conn.company:
                companies[conn.company] = companies.get(conn.company, 0) + 1
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # High-value connections (business value score > 0.7)
        high_value_connections = [c for c in connections if c.business_value_score and c.business_value_score > 0.7]
        
        # Decision makers
        decision_makers = [c for c in connections if c.is_decision_maker]
        
        return {
            "summary": {
                "total_connections": total_connections,
                "email_coverage": f"{(connections_with_email/total_connections)*100:.1f}%" if total_connections else "0%",
                "enrichment_success": f"{(self.stats['enriched_connections']/self.stats['total_connections'])*100:.1f}%",
                "processing_time": f"{self.stats['processing_time']:.1f}s"
            },
            "industry_breakdown": dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)),
            "seniority_breakdown": dict(sorted(seniority.items(), key=lambda x: x[1], reverse=True)),
            "geographic_breakdown": dict(sorted(regions.items(), key=lambda x: x[1], reverse=True)),
            "top_companies": top_companies,
            "high_value_connections": len(high_value_connections),
            "decision_makers": len(decision_makers),
            "statistics": self.stats
        }
        
    def export_enriched_data(self, connections: List[EnrichedConnection], output_path: Path = None) -> str:
        """Export enriched data to JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"enriched_connections_{timestamp}.json"
            
        # Convert to serializable format
        enriched_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_connections": len(connections),
                "enrichment_pipeline_version": "1.0"
            },
            "intelligence_report": self.generate_intelligence_report(connections),
            "connections": [asdict(conn) for conn in connections]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Enriched data exported to: {output_path}")
        return str(output_path)

# Main pipeline runner
def main():
    """Run the LinkedIn data enrichment pipeline"""
    print("🔍 LinkedIn Data Enrichment Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = LinkedInDataEnrichmentPipeline()
    
    # Check for LinkedIn data
    connections_file = pipeline.data_dir / "Connections.csv"
    
    if not connections_file.exists():
        print("⏳ LinkedIn data not found. Expected location:")
        print(f"   {connections_file}")
        print("\n📥 To prepare for data import:")
        print("   1. Extract LinkedIn export to ~/Downloads/linkedin_data/")
        print("   2. Ensure Connections.csv exists")
        print("   3. Run this script again")
        return
        
    # Process connections
    print("🚀 Processing LinkedIn connections...")
    enriched_connections = pipeline.process_connections_file(connections_file)
    
    if not enriched_connections:
        print("❌ No connections could be processed")
        return
        
    # Generate intelligence report
    print("📊 Generating intelligence report...")
    report = pipeline.generate_intelligence_report(enriched_connections)
    
    # Display summary
    print("\n" + "=" * 50)
    print("📈 LINKEDIN NETWORK INTELLIGENCE SUMMARY")
    print("=" * 50)
    
    summary = report.get("summary", {})
    print(f"Total Connections: {summary.get('total_connections', 0)}")
    print(f"Email Coverage: {summary.get('email_coverage', 'N/A')}")
    print(f"Enrichment Success: {summary.get('enrichment_success', 'N/A')}")
    print(f"High-Value Connections: {report.get('high_value_connections', 0)}")
    print(f"Decision Makers: {report.get('decision_makers', 0)}")
    
    print(f"\n🏢 Top Industries:")
    industries = report.get("industry_breakdown", {})
    for industry, count in list(industries.items())[:5]:
        print(f"   • {industry}: {count} connections")
        
    print(f"\n👔 Seniority Levels:")
    seniority = report.get("seniority_breakdown", {})
    for level, count in list(seniority.items())[:5]:
        print(f"   • {level}: {count} connections")
        
    # Export enriched data
    print("\n💾 Exporting enriched data...")
    export_path = pipeline.export_enriched_data(enriched_connections)
    print(f"✅ Enriched data saved to: {export_path}")
    
    print("\n🎯 Ready for MCP server integration!")

if __name__ == "__main__":
    main()