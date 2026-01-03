#!/usr/bin/env python3
"""
LinkedIn Connection Scoring & Quality Assessment System
=====================================================

Advanced scoring system for LinkedIn connections with multiple
scoring models for different use cases (job search, business development,
networking, recruiting, etc.)

Features:
- Multi-dimensional scoring algorithms
- Industry-specific relevance scoring  
- Career progression modeling
- Network influence analysis
- Quality assessment and recommendations
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

@dataclass
class ScoringWeights:
    """Configurable weights for different scoring models"""
    seniority_weight: float = 0.3
    industry_relevance_weight: float = 0.25
    company_size_weight: float = 0.2
    functional_relevance_weight: float = 0.15
    network_freshness_weight: float = 0.1

@dataclass
class ConnectionScore:
    """Comprehensive scoring result for a connection"""
    connection_id: str
    overall_score: float
    dimension_scores: Dict[str, float]
    ranking_percentile: Optional[float] = None
    score_explanation: Optional[str] = None
    recommended_actions: List[str] = None

class ConnectionScoringSystem:
    """Main scoring system for LinkedIn connections"""
    
    def __init__(self):
        self.scoring_models = self._initialize_scoring_models()
        self.industry_hierarchies = self._load_industry_hierarchies()
        self.company_intelligence = self._load_company_intelligence()
        
    def _initialize_scoring_models(self) -> Dict[str, ScoringWeights]:
        """Initialize different scoring models for various use cases"""
        return {
            "job_search": ScoringWeights(
                seniority_weight=0.4,      # Hiring managers matter most
                industry_relevance_weight=0.3,  # Industry fit important
                company_size_weight=0.15,   # Company size relevance
                functional_relevance_weight=0.1,  # Function less critical
                network_freshness_weight=0.05    # Less critical for job search
            ),
            
            "business_development": ScoringWeights(
                seniority_weight=0.35,     # Decision makers critical
                industry_relevance_weight=0.2,   # Broader industry acceptance
                company_size_weight=0.25,  # Larger companies = bigger deals
                functional_relevance_weight=0.15,  # Function matters for fit
                network_freshness_weight=0.05    # Relationship age less critical
            ),
            
            "networking": ScoringWeights(
                seniority_weight=0.2,      # Mixed seniority acceptable
                industry_relevance_weight=0.25,  # Industry connections valuable
                company_size_weight=0.15,  # Size less important
                functional_relevance_weight=0.2,   # Function important for expertise
                network_freshness_weight=0.2     # Recent connections more active
            ),
            
            "recruiting": ScoringWeights(
                seniority_weight=0.15,     # Mixed levels needed
                industry_relevance_weight=0.3,   # Industry expertise crucial
                company_size_weight=0.1,   # Size less relevant
                functional_relevance_weight=0.35,  # Function most critical
                network_freshness_weight=0.1     # Freshness matters for availability
            ),
            
            "thought_leadership": ScoringWeights(
                seniority_weight=0.25,     # Senior people have more influence
                industry_relevance_weight=0.3,   # Industry thought leadership
                company_size_weight=0.2,   # Larger companies = more visibility
                functional_relevance_weight=0.15,  # Function relevance
                network_freshness_weight=0.1     # Freshness less critical
            ),
            
            "brm_technology": ScoringWeights(
                seniority_weight=0.35,     # Senior stakeholders crucial for BRM
                industry_relevance_weight=0.25,  # Technology industry focus
                company_size_weight=0.2,   # Enterprise clients preferred
                functional_relevance_weight=0.15,  # Technology function relevance
                network_freshness_weight=0.05    # Relationship age less critical
            )
        }
        
    def _load_industry_hierarchies(self) -> Dict[str, Dict[str, float]]:
        """Load industry relevance hierarchies"""
        return {
            # For someone with BRM/Technology background
            "brm_technology": {
                "Technology": 1.0,
                "Financial Services": 0.9,  # High BRM relevance
                "Consulting": 0.85,         # High BRM relevance  
                "Healthcare": 0.7,          # Moderate relevance
                "Manufacturing": 0.65,      # Moderate relevance
                "Energy & Mining": 0.6,     # Moderate relevance (Australia focus)
                "Government": 0.6,          # Moderate relevance
                "Education": 0.4,           # Lower commercial relevance
                "Unknown": 0.3              # Default for unclassified
            },
            
            # For general technology roles
            "technology_general": {
                "Technology": 1.0,
                "Financial Services": 0.8,  # FinTech relevance
                "Consulting": 0.7,          # Tech consulting
                "Healthcare": 0.8,          # HealthTech relevance
                "Manufacturing": 0.7,       # Industry 4.0 relevance
                "Energy & Mining": 0.6,     # Digital transformation
                "Government": 0.7,          # GovTech relevance
                "Education": 0.6,           # EdTech relevance
                "Unknown": 0.3
            }
        }
        
    def _load_company_intelligence(self) -> Dict[str, Dict[str, Any]]:
        """Load company size and intelligence database"""
        return {
            # Technology Companies
            "Microsoft": {"size": "Enterprise", "employees": 200000, "influence": 0.95},
            "Google": {"size": "Enterprise", "employees": 150000, "influence": 0.95},
            "Amazon": {"size": "Enterprise", "employees": 1500000, "influence": 0.95},
            "Apple": {"size": "Enterprise", "employees": 150000, "influence": 0.95},
            "Meta": {"size": "Enterprise", "employees": 80000, "influence": 0.9},
            "Netflix": {"size": "Large", "employees": 15000, "influence": 0.85},
            "Salesforce": {"size": "Large", "employees": 80000, "influence": 0.85},
            "Oracle": {"size": "Enterprise", "employees": 140000, "influence": 0.8},
            
            # Australian Enterprise
            "Commonwealth Bank": {"size": "Enterprise", "employees": 50000, "influence": 0.9},
            "Westpac": {"size": "Enterprise", "employees": 40000, "influence": 0.85},
            "ANZ": {"size": "Enterprise", "employees": 40000, "influence": 0.85},
            "Telstra": {"size": "Enterprise", "employees": 30000, "influence": 0.8},
            "BHP": {"size": "Enterprise", "employees": 80000, "influence": 0.85},
            "Rio Tinto": {"size": "Enterprise", "employees": 50000, "influence": 0.8},
            
            # Consulting
            "McKinsey": {"size": "Large", "employees": 35000, "influence": 0.95},
            "BCG": {"size": "Large", "employees": 25000, "influence": 0.9},
            "Bain": {"size": "Large", "employees": 15000, "influence": 0.9},
            "Deloitte": {"size": "Enterprise", "employees": 400000, "influence": 0.85},
            "PwC": {"size": "Enterprise", "employees": 300000, "influence": 0.85},
            "EY": {"size": "Enterprise", "employees": 400000, "influence": 0.8},
            "KPMG": {"size": "Enterprise", "employees": 270000, "influence": 0.8},
            "Accenture": {"size": "Enterprise", "employees": 700000, "influence": 0.85},
        }
        
    def calculate_seniority_score(self, seniority_level: str) -> float:
        """Calculate seniority score (0-1)"""
        seniority_values = {
            "C-Suite": 1.0,
            "VP/SVP": 0.85,
            "Director": 0.7,
            "Manager": 0.55,
            "Senior IC": 0.4,
            "Mid-Level": 0.25,
            "Entry-Level": 0.1,
            None: 0.3  # Default for unknown
        }
        return seniority_values.get(seniority_level, 0.3)
        
    def calculate_industry_relevance_score(self, 
                                         industry: str, 
                                         model: str = "brm_technology") -> float:
        """Calculate industry relevance score"""
        industry_hierarchy = self.industry_hierarchies.get(model, self.industry_hierarchies["brm_technology"])
        return industry_hierarchy.get(industry, 0.3)
        
    def calculate_company_size_score(self, company: str) -> float:
        """Calculate company size/influence score"""
        company_info = self.company_intelligence.get(company, {})
        
        if "influence" in company_info:
            return company_info["influence"]
            
        # Estimate based on company size if we have it
        size = company_info.get("size", "Unknown")
        size_scores = {
            "Enterprise": 0.8,
            "Large": 0.6,
            "Medium": 0.4,
            "Small": 0.3,
            "Startup": 0.3,
            "Unknown": 0.3
        }
        return size_scores.get(size, 0.3)
        
    def calculate_functional_relevance_score(self, 
                                           functional_area: str,
                                           target_function: str = "strategy") -> float:
        """Calculate functional area relevance score"""
        
        # Function relevance matrices for different targets
        relevance_matrices = {
            "strategy": {
                "Strategy": 1.0,
                "Operations": 0.8,
                "Product": 0.7,
                "Engineering": 0.6,
                "Sales": 0.6,
                "Marketing": 0.5,
                "Finance": 0.5,
                "Data": 0.6,
                "HR": 0.3,
                "Legal": 0.3
            },
            "technology": {
                "Engineering": 1.0,
                "Product": 0.9,
                "Data": 0.85,
                "Operations": 0.7,
                "Strategy": 0.6,
                "Marketing": 0.4,
                "Sales": 0.4,
                "Finance": 0.3,
                "HR": 0.2,
                "Legal": 0.2
            },
            "business": {
                "Strategy": 0.9,
                "Sales": 0.9,
                "Marketing": 0.8,
                "Operations": 0.8,
                "Product": 0.7,
                "Finance": 0.7,
                "Engineering": 0.5,
                "Data": 0.5,
                "HR": 0.4,
                "Legal": 0.4
            }
        }
        
        matrix = relevance_matrices.get(target_function, relevance_matrices["strategy"])
        return matrix.get(functional_area, 0.3)
        
    def calculate_network_freshness_score(self, connected_date: str) -> float:
        """Calculate network freshness score based on connection date"""
        try:
            connected = datetime.strptime(connected_date, "%d %b %Y")
            days_ago = (datetime.now() - connected).days
            
            # Fresher connections score higher
            if days_ago <= 30:
                return 1.0      # Very recent
            elif days_ago <= 90:
                return 0.9      # Recent
            elif days_ago <= 180:
                return 0.8      # Moderately recent
            elif days_ago <= 365:
                return 0.6      # Within a year
            elif days_ago <= 730:
                return 0.4      # Within two years
            else:
                return 0.2      # Older connections
                
        except (ValueError, TypeError):
            return 0.5  # Default for unparseable dates
            
    def calculate_composite_score(self, 
                                connection: Dict[str, Any],
                                model_name: str = "brm_technology",
                                target_function: str = "strategy") -> ConnectionScore:
        """Calculate composite score for a connection"""
        
        # Get scoring weights for the model
        weights = self.scoring_models.get(model_name, self.scoring_models["brm_technology"])
        
        # Calculate individual dimension scores
        seniority_score = self.calculate_seniority_score(connection.get("seniority_level"))
        industry_score = self.calculate_industry_relevance_score(connection.get("company_industry"), model_name)
        company_score = self.calculate_company_size_score(connection.get("company", ""))
        functional_score = self.calculate_functional_relevance_score(
            connection.get("functional_area"), target_function
        )
        freshness_score = self.calculate_network_freshness_score(connection.get("connected_on", ""))
        
        # Store dimension scores
        dimension_scores = {
            "seniority": seniority_score,
            "industry_relevance": industry_score, 
            "company_size": company_score,
            "functional_relevance": functional_score,
            "network_freshness": freshness_score
        }
        
        # Calculate weighted composite score
        composite_score = (
            seniority_score * weights.seniority_weight +
            industry_score * weights.industry_relevance_weight +
            company_score * weights.company_size_weight +
            functional_score * weights.functional_relevance_weight +
            freshness_score * weights.network_freshness_weight
        )
        
        # Generate explanation
        explanation = self._generate_score_explanation(dimension_scores, weights, composite_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(connection, dimension_scores)
        
        return ConnectionScore(
            connection_id=connection.get("connection_id", "unknown"),
            overall_score=composite_score,
            dimension_scores=dimension_scores,
            score_explanation=explanation,
            recommended_actions=recommendations
        )
        
    def _generate_score_explanation(self, 
                                  dimension_scores: Dict[str, float],
                                  weights: ScoringWeights,
                                  composite_score: float) -> str:
        """Generate human-readable explanation of the score"""
        
        # Identify strongest and weakest dimensions
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_dims[0]
        weakest = sorted_dims[-1]
        
        explanation_parts = [
            f"Overall Score: {composite_score:.2f} ({self._score_to_rating(composite_score)})"
        ]
        
        explanation_parts.append(f"Strongest Dimension: {strongest[0].replace('_', ' ').title()} ({strongest[1]:.2f})")
        explanation_parts.append(f"Weakest Dimension: {weakest[0].replace('_', ' ').title()} ({weakest[1]:.2f})")
        
        # Add context about scoring model
        if weights.seniority_weight > 0.3:
            explanation_parts.append("Model emphasizes seniority/decision-making power")
        if weights.industry_relevance_weight > 0.25:
            explanation_parts.append("Model values industry alignment")
        if weights.functional_relevance_weight > 0.2:
            explanation_parts.append("Model prioritizes functional expertise match")
            
        return " • ".join(explanation_parts)
        
    def _generate_recommendations(self, 
                                connection: Dict[str, Any],
                                dimension_scores: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations based on scoring"""
        
        recommendations = []
        
        # High overall value recommendations
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)
        
        if overall_score >= 0.8:
            recommendations.append("🎯 HIGH PRIORITY: Schedule immediate outreach")
            recommendations.append("📞 Personalized approach recommended")
            
        elif overall_score >= 0.6:
            recommendations.append("✅ MEDIUM PRIORITY: Include in next outreach batch")
            recommendations.append("📧 Professional email outreach appropriate")
            
        else:
            recommendations.append("⏳ LOWER PRIORITY: Monitor for role/company changes")
            
        # Specific dimension-based recommendations
        if dimension_scores.get("seniority", 0) >= 0.8:
            recommendations.append("👔 Senior decision maker - emphasize strategic value")
            
        if dimension_scores.get("industry_relevance", 0) >= 0.8:
            recommendations.append("🏭 High industry alignment - leverage sector expertise")
            
        if dimension_scores.get("company_size", 0) >= 0.8:
            recommendations.append("🏢 Influential company - potential for significant opportunities")
            
        if dimension_scores.get("network_freshness", 0) >= 0.8:
            recommendations.append("🆕 Recent connection - high likelihood of response")
        elif dimension_scores.get("network_freshness", 0) <= 0.3:
            recommendations.append("⏰ Old connection - consider re-engagement strategy")
            
        # Functional recommendations
        functional_area = connection.get("functional_area")
        if functional_area in ["Strategy", "Operations", "Product"]:
            recommendations.append(f"💼 {functional_area} background - align BRM expertise")
            
        return recommendations
        
    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to rating"""
        if score >= 0.9:
            return "Exceptional"
        elif score >= 0.8:
            return "High Value"
        elif score >= 0.7:
            return "Good Potential"
        elif score >= 0.6:
            return "Moderate Value"
        elif score >= 0.5:
            return "Below Average"
        else:
            return "Low Priority"
            
    def score_all_connections(self, 
                            connections: List[Dict[str, Any]],
                            model_name: str = "brm_technology") -> List[ConnectionScore]:
        """Score all connections and add ranking percentiles"""
        
        # Score all connections
        scored_connections = []
        for connection in connections:
            score = self.calculate_composite_score(connection, model_name)
            scored_connections.append(score)
            
        # Sort by score and add percentiles
        scored_connections.sort(key=lambda x: x.overall_score, reverse=True)
        
        total_connections = len(scored_connections)
        for i, connection_score in enumerate(scored_connections):
            percentile = ((total_connections - i - 1) / total_connections) * 100
            connection_score.ranking_percentile = percentile
            
        return scored_connections
        
    def get_top_connections(self, 
                          connections: List[Dict[str, Any]],
                          model_name: str = "brm_technology",
                          top_n: int = 50,
                          min_score: float = 0.6) -> List[ConnectionScore]:
        """Get top-ranked connections above minimum score threshold"""
        
        scored_connections = self.score_all_connections(connections, model_name)
        
        # Filter by minimum score and return top N
        filtered = [c for c in scored_connections if c.overall_score >= min_score]
        return filtered[:top_n]
        
    def generate_scoring_report(self, 
                              connections: List[Dict[str, Any]],
                              model_name: str = "brm_technology") -> Dict[str, Any]:
        """Generate comprehensive scoring analysis report"""
        
        scored_connections = self.score_all_connections(connections, model_name)
        
        if not scored_connections:
            return {"error": "No connections to score"}
            
        # Calculate statistics
        scores = [c.overall_score for c in scored_connections]
        avg_score = sum(scores) / len(scores)
        
        # Score distribution
        distribution = {
            "exceptional": len([s for s in scores if s >= 0.9]),
            "high_value": len([s for s in scores if 0.8 <= s < 0.9]),
            "good_potential": len([s for s in scores if 0.7 <= s < 0.8]),
            "moderate_value": len([s for s in scores if 0.6 <= s < 0.7]),
            "below_average": len([s for s in scores if 0.5 <= s < 0.6]),
            "low_priority": len([s for s in scores if s < 0.5])
        }
        
        # Top connections
        top_20 = scored_connections[:20]
        
        # Dimension analysis
        dimension_averages = {}
        for dim in ["seniority", "industry_relevance", "company_size", "functional_relevance", "network_freshness"]:
            dim_scores = [c.dimension_scores.get(dim, 0) for c in scored_connections]
            dimension_averages[dim] = sum(dim_scores) / len(dim_scores) if dim_scores else 0
            
        return {
            "model_used": model_name,
            "total_connections_scored": len(scored_connections),
            "average_score": avg_score,
            "score_distribution": distribution,
            "dimension_averages": dimension_averages,
            "top_connections": [asdict(c) for c in top_20],
            "recommendations": {
                "immediate_outreach": len([c for c in scored_connections if c.overall_score >= 0.8]),
                "medium_priority_outreach": len([c for c in scored_connections if 0.6 <= c.overall_score < 0.8]),
                "monitor_for_changes": len([c for c in scored_connections if c.overall_score < 0.6])
            }
        }

# Testing and demonstration functions
def main():
    """Demo the connection scoring system"""
    print("🎯 LinkedIn Connection Scoring System")
    print("=" * 50)
    
    # Initialize scoring system
    scorer = ConnectionScoringSystem()
    
    # Demo connections data
    demo_connections = [
        {
            "connection_id": "conn_001",
            "first_name": "Sarah", 
            "last_name": "Johnson",
            "company": "Microsoft",
            "position": "Senior Director of Business Strategy",
            "company_industry": "Technology", 
            "seniority_level": "Director",
            "functional_area": "Strategy",
            "connected_on": "15 Jan 2024"
        },
        {
            "connection_id": "conn_002", 
            "first_name": "Mike",
            "last_name": "Chen",
            "company": "Commonwealth Bank",
            "position": "Head of Digital Transformation", 
            "company_industry": "Financial Services",
            "seniority_level": "Manager",
            "functional_area": "Strategy",
            "connected_on": "03 Sep 2023"
        },
        {
            "connection_id": "conn_003",
            "first_name": "Emma",
            "last_name": "Wilson", 
            "company": "Startup ABC",
            "position": "Junior Software Engineer",
            "company_industry": "Technology",
            "seniority_level": "Entry-Level", 
            "functional_area": "Engineering",
            "connected_on": "22 Nov 2021"
        }
    ]
    
    print("📊 Testing Different Scoring Models:")
    print("-" * 30)
    
    for model_name in ["job_search", "business_development", "networking"]:
        print(f"\n🎯 Model: {model_name.replace('_', ' ').title()}")
        
        top_connections = scorer.get_top_connections(demo_connections, model_name, top_n=3)
        
        for i, scored_conn in enumerate(top_connections, 1):
            print(f"{i}. Score: {scored_conn.overall_score:.3f} ({scorer._score_to_rating(scored_conn.overall_score)})")
            print(f"   ID: {scored_conn.connection_id}")
            print(f"   Top Dimension: {max(scored_conn.dimension_scores.items(), key=lambda x: x[1])[0]}")
            
    # Generate comprehensive report
    print(f"\n📈 Comprehensive Scoring Report (BRM Model):")
    report = scorer.generate_scoring_report(demo_connections, "brm_technology")
    
    print(f"Average Score: {report['average_score']:.3f}")
    print(f"High Value Connections: {report['recommendations']['immediate_outreach']}")
    print(f"Medium Priority: {report['recommendations']['medium_priority_outreach']}")
    
    print("\n✅ Connection scoring system ready for LinkedIn data import!")

if __name__ == "__main__":
    main()