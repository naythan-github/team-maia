#!/usr/bin/env python3
"""
Test cost savings on typical Engineering Manager workflows using multi-LLM routing.
"""

import os
from claude.tools.core.production_llm_router import ProductionLLMRouter, LLMProvider

def test_engineering_manager_workflows():
    """Test cost optimization for typical Engineering Manager tasks."""
    print("🚀 Engineering Manager Workflow Cost Analysis")
    print("=" * 70)
    
    # Set API key for router
    os.environ['GOOGLE_AI_API_KEY'] = 'AIzaSyBVUdH9TPXpp8mL7rQNsqLauXpN5SMHeWc'
    
    router = ProductionLLMRouter()
    
    # Typical Engineering Manager tasks with realistic token estimates
    engineering_tasks = [
        ("Review team performance dashboard logs", 4000, "Daily routine"),
        ("Parse incident reports and extract metrics", 3500, "Weekly analysis"),
        ("Generate status report from project data", 5000, "Weekly reporting"),
        ("Research best practices for cloud migration", 8000, "Strategic planning"),
        ("Analyze team utilization bash scripts output", 2500, "Resource management"),
        ("Read configuration files for environment setup", 2000, "Technical review"),
        ("Extract cost data from Azure billing exports", 3000, "Budget management"),
        ("Research competitive landscape for cloud services", 10000, "Market intelligence"),
        ("Plan strategic architecture roadmap", 15000, "Strategic planning"),
        ("Review security vulnerability assessment results", 8000, "Risk management"),
        ("Generate Python scripts for automation tasks", 6000, "Process improvement"),
        ("Analyze stakeholder feedback from surveys", 7000, "Team development"),
    ]
    
    print(f"\n📊 Task Analysis:")
    print(f"{'Task':<50} {'Current Cost':<12} {'Optimal Cost':<12} {'Savings':<10} {'Model'}")
    print("-" * 95)
    
    current_total = 0
    optimized_total = 0
    
    for task, tokens, category in engineering_tasks:
        # Current cost (all Sonnet)
        current_cost = tokens * router.llm_configs[LLMProvider.CLAUDE_SONNET].cost_per_1k_tokens / 1000
        
        # Optimized cost
        routing = router.route_task(task, tokens)
        optimized_cost = routing.estimated_cost
        
        # Calculate savings
        savings_pct = ((current_cost - optimized_cost) / current_cost * 100) if current_cost > 0 else 0
        
        current_total += current_cost
        optimized_total += optimized_cost
        
        print(f"{task[:49]:<50} ${current_cost:<11.4f} ${optimized_cost:<11.4f} {savings_pct:<9.1f}% {routing.provider.value}")
    
    overall_savings = ((current_total - optimized_total) / current_total * 100) if current_total > 0 else 0
    
    print("-" * 95)
    print(f"{'TOTALS':<50} ${current_total:<11.4f} ${optimized_total:<11.4f} {overall_savings:<9.1f}%")
    
    print(f"\n💰 Engineering Manager Cost Analysis:")
    print(f"Current approach (all Claude Sonnet): ${current_total:.4f} per session")
    print(f"Optimized multi-LLM routing: ${optimized_total:.4f} per session") 
    print(f"Savings per session: ${current_total - optimized_total:.4f} ({overall_savings:.1f}%)")
    
    # Extrapolate to realistic usage patterns
    sessions_per_week = 15  # 3 sessions per day, 5 days
    weeks_per_year = 50     # Account for holidays
    
    weekly_savings = (current_total - optimized_total) * sessions_per_week
    annual_savings = weekly_savings * weeks_per_year
    
    print(f"\n📈 Projected Annual Impact:")
    print(f"Sessions per week: {sessions_per_week}")
    print(f"Working weeks per year: {weeks_per_year}")
    print(f"Weekly savings: ${weekly_savings:.2f}")
    print(f"Annual savings: ${annual_savings:.2f}")
    
    print(f"\n🎯 Optimization Strategy:")
    print(f"• File operations & data parsing: Gemini Flash (100x cheaper)")
    print(f"• Research & analysis: Gemini Pro (2.4x cheaper)")  
    print(f"• Strategic planning: Claude Sonnet (maintain reasoning quality)")
    print(f"• Critical decisions: Claude Opus (when needed)")
    
    return {
        "current_cost": current_total,
        "optimized_cost": optimized_total,
        "savings_percentage": overall_savings,
        "annual_savings": annual_savings
    }

if __name__ == "__main__":
    results = test_engineering_manager_workflows()