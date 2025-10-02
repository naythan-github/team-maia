#!/usr/bin/env python3
"""
Enhanced Maia Research Tool with Multi-LLM Optimization
Integrates cost-optimized routing into research workflows.
"""

import os
import sys
import json
from typing import Dict, List, Any
from pathlib import Path

# Environment-agnostic tools path
maia_root = os.getenv("MAIA_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
tools_path = os.path.join(maia_root, "claude", "tools")
sys.path.append(tools_path)

try:
    from maia_llm_integration import get_maia_llm_integration, route_maia_task
    LLM_INTEGRATION_AVAILABLE = True
except ImportError:
    LLM_INTEGRATION_AVAILABLE = False

class EnhancedMaiaResearch:
    """Research tool with intelligent LLM routing for cost optimization."""
    
    def __init__(self):
        self.integration = get_maia_llm_integration() if LLM_INTEGRATION_AVAILABLE else None
        self.research_cache = {}
        
    def research_company(self, company_name: str, research_depth: str = "standard") -> Dict[str, Any]:
        """Research a company with optimized LLM routing."""
        
        # Estimate tokens based on research depth
        token_estimates = {
            "quick": 3000,
            "standard": 8000, 
            "deep": 15000,
            "comprehensive": 25000
        }
        
        estimated_tokens = token_estimates.get(research_depth, 8000)
        
        # Route the task
        routing_info = None
        if self.integration:
            task_desc = f"Research company {company_name} for {research_depth} analysis including business model, market position, and key insights"
            routing_info = route_maia_task(task_desc, estimated_tokens)
            
            print(f"🎯 Research Routing:")
            print(f"   Company: {company_name}")
            print(f"   Depth: {research_depth}")
            print(f"   Optimal Model: {routing_info['provider']}")
            print(f"   Estimated Cost: ${routing_info['estimated_cost']:.4f}")
            print(f"   Reasoning: {routing_info['reasoning']}")
        
        # Simulate research process
        research_data = {
            "company_name": company_name,
            "research_depth": research_depth,
            "routing_info": routing_info,
            "findings": {
                "business_model": f"Research findings for {company_name}",
                "market_position": "Market analysis results",
                "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
                "competitive_landscape": "Competitive analysis",
                "financial_overview": "Financial summary"
            },
            "metadata": {
                "tokens_used": estimated_tokens,
                "model_used": routing_info['provider'] if routing_info else 'claude-sonnet',
                "cost": routing_info['estimated_cost'] if routing_info else estimated_tokens * 0.003 / 1000
            }
        }
        
        return research_data
    
    def batch_research(self, companies: List[str], research_depth: str = "standard") -> Dict[str, Any]:
        """Batch research multiple companies with cost optimization."""
        
        results = []
        total_cost_current = 0
        total_cost_optimized = 0
        
        print(f"\n🔍 Batch Research Analysis: {len(companies)} companies")
        print("=" * 60)
        
        for company in companies:
            research = self.research_company(company, research_depth)
            results.append(research)
            
            # Cost tracking
            if research['routing_info']:
                optimized_cost = research['routing_info']['estimated_cost']
                current_cost = research['metadata']['tokens_used'] * 0.003 / 1000  # Sonnet pricing
                
                total_cost_optimized += optimized_cost
                total_cost_current += current_cost
                
                savings = ((current_cost - optimized_cost) / current_cost * 100) if current_cost > 0 else 0
                print(f"   Savings: {savings:.1f}% (${current_cost - optimized_cost:.4f})")
            
            print()
        
        # Summary
        total_savings = ((total_cost_current - total_cost_optimized) / total_cost_current * 100) if total_cost_current > 0 else 0
        
        summary = {
            "companies_researched": len(companies),
            "research_depth": research_depth,
            "cost_analysis": {
                "current_approach_cost": total_cost_current,
                "optimized_cost": total_cost_optimized,
                "total_savings": total_cost_current - total_cost_optimized,
                "savings_percentage": total_savings
            },
            "results": results
        }
        
        print(f"💰 Batch Research Cost Summary:")
        print(f"   Current approach: ${total_cost_current:.4f}")
        print(f"   Optimized routing: ${total_cost_optimized:.4f}")
        print(f"   Total savings: ${total_cost_current - total_cost_optimized:.4f} ({total_savings:.1f}%)")
        
        return summary

def demo_enhanced_research():
    """Demonstrate the enhanced research capabilities."""
    print("🚀 Enhanced Maia Research with Multi-LLM Optimization")
    print("=" * 60)
    
    researcher = EnhancedMaiaResearch()
    
    # Test companies for research
    test_companies = ["Microsoft", "Atlassian", "PwC", "Accenture", "AWS"]
    
    # Batch research demonstration
    results = researcher.batch_research(test_companies, "standard")
    
    # Detailed analysis for one company
    print(f"\n📊 Detailed Research Example:")
    detailed_research = researcher.research_company("Orro Group", "comprehensive")
    
    print(f"\nCompany: {detailed_research['company_name']}")
    print(f"Research Depth: {detailed_research['research_depth']}")
    if detailed_research['routing_info']:
        print(f"Model Used: {detailed_research['routing_info']['provider']}")
        print(f"Cost: ${detailed_research['metadata']['cost']:.4f}")

if __name__ == "__main__":
    demo_enhanced_research()