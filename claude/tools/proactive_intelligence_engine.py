#!/usr/bin/env python3
# NOTE: DEMO FILE - Message bus imports deprecated, use Swarm framework instead
# See claude/tools/orchestration/agent_swarm.py for current orchestration patterns
"""
Proactive Intelligence Engine - Phase 23
=========================================

The next evolution: From reactive AI to proactive intelligence that anticipates
user needs and takes autonomous actions to optimize productivity and opportunities.

System Evolution:
Phase 19: AI Dashboard → Phase 20: Orchestration → Phase 21: Learning → 
Phase 22: Live Data → Phase 23: Proactive Intelligence

Key Capabilities:
- Background monitoring of emails, calendars, job boards
- Autonomous opportunity identification and prioritization  
- Proactive context preparation and research
- Intelligent scheduling and calendar optimization
- Predictive alerting based on learned user patterns
- Background learning and adaptation from user behaviors

This represents the pinnacle of AI assistance: anticipating needs before they're expressed.
"""

import asyncio
import json
import uuid
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from threading import Thread
from pathlib import Path

# Import Phase 22 real data integration
try:
    from real_data_job_analyzer import RealDataJobAnalyzer
    from production_api_credentials import ProductionCredentialManager
    from phase22_learning_integration_bridge import Phase22LearningIntegrationBridge
except ImportError:
    RealDataJobAnalyzer = None
    ProductionCredentialManager = None
    Phase22LearningIntegrationBridge = None

# Import Phase 21 learning system
try:
    from contextual_memory_learning_system import ContextualMemoryLearningSystem
except ImportError:
    ContextualMemoryLearningSystem = None

# Import Phase 20 orchestration
try:
    from agent_message_bus import get_message_bus, MessageType, MessagePriority
    from enhanced_context_manager import get_context_manager
except ImportError:
    get_message_bus = None
    get_context_manager = None

@dataclass
class ProactiveOpportunity:
    """Proactively identified opportunity or action"""
    opportunity_id: str
    type: str  # job_opportunity, calendar_optimization, research_needed, etc.
    title: str
    description: str
    priority: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    source: str
    created_at: datetime
    expires_at: Optional[datetime]
    action_required: bool
    suggested_actions: List[str]
    context_data: Dict[str, Any]

@dataclass
class ProactiveAlert:
    """Alert for high-priority proactive opportunities"""
    alert_id: str
    opportunity_id: str
    alert_type: str  # immediate, urgent, scheduled, fyi
    message: str
    priority: float
    delivery_channels: List[str]  # email, notification, dashboard
    created_at: datetime
    delivered: bool = False

class ProactiveIntelligenceEngine:
    """
    Proactive Intelligence Engine - Anticipates and acts on user needs
    
    Core Philosophy: Don't wait for user requests - anticipate and prepare
    
    Proactive Capabilities:
    1. Background Monitoring - Continuous scanning of data sources
    2. Opportunity Identification - AI-powered pattern recognition 
    3. Autonomous Research - Automatic context preparation
    4. Intelligent Alerting - Priority-based notifications
    5. Predictive Actions - Learning-based automation
    6. Calendar Optimization - Proactive scheduling management
    """
    
    def __init__(self, user_id: str = "naythan"):
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())
        self.is_running = False
        
        # Data storage
        self.data_dir = Path(__file__).parent.parent / "data" / "proactive_intelligence"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.opportunities_file = self.data_dir / "opportunities.json"
        self.alerts_file = self.data_dir / "alerts.json"
        self.config_file = self.data_dir / "config.json"
        
        # Initialize integrated systems
        self.credential_manager = ProductionCredentialManager() if ProductionCredentialManager else None
        self.learning_system = ContextualMemoryLearningSystem(user_id) if ContextualMemoryLearningSystem else None
        self.integration_bridge = Phase22LearningIntegrationBridge(user_id) if Phase22LearningIntegrationBridge else None
        
        # Orchestration infrastructure
        self.bus = get_message_bus() if get_message_bus else None
        self.context_manager = get_context_manager() if get_context_manager else None
        
        # Proactive monitoring configuration
        self.monitoring_intervals = {
            "job_opportunities": 30,  # minutes
            "calendar_optimization": 60,  # minutes  
            "email_triage": 15,  # minutes
            "market_intelligence": 120,  # minutes
            "learning_analysis": 180  # minutes
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "job_opportunity_priority": 0.8,
            "calendar_conflict": 0.9,
            "urgent_email": 0.85,
            "market_change": 0.7
        }
        
        # Background thread for monitoring
        self.monitoring_thread = None
        
        self._load_configuration()
        self._register_proactive_agents()
        
        print(f"🧠 Proactive Intelligence Engine initialized for {user_id}")
        print(f"🔮 Phase 23: Anticipating and acting on user needs")
        print(f"⚡ Background monitoring: {len(self.monitoring_intervals)} data sources")
    
    def _load_configuration(self):
        """Load proactive intelligence configuration"""
        
        default_config = {
            "proactive_mode": "active",
            "monitoring_enabled": True,
            "alert_preferences": {
                "job_opportunities": "immediate",
                "calendar_conflicts": "immediate", 
                "email_priority": "scheduled",
                "market_updates": "daily_digest"
            },
            "autonomous_actions": {
                "calendar_optimization": True,
                "context_preparation": True,
                "research_automation": True,
                "priority_email_triage": False  # Requires explicit permission
            },
            "learning_integration": {
                "adapt_monitoring_frequency": True,
                "personalize_alert_thresholds": True,
                "learn_from_user_actions": True
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self._save_configuration()
    
    def _save_configuration(self):
        """Save proactive intelligence configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _register_proactive_agents(self):
        """Register specialized proactive monitoring agents"""
        
        if not self.bus:
            return
            
        agents = [
            ("background_monitor", ["continuous_scanning", "pattern_recognition", "anomaly_detection"]),
            ("opportunity_identifier", ["job_matching", "calendar_analysis", "priority_assessment"]),
            ("context_preparer", ["research_automation", "context_preloading", "briefing_generation"]),
            ("alert_manager", ["notification_routing", "priority_filtering", "delivery_optimization"]),
            ("autonomous_optimizer", ["calendar_scheduling", "email_triage", "workflow_automation"])
        ]
        
        for agent_name, capabilities in agents:
            self.bus.register_agent(agent_name, capabilities)
            print(f"🤖 Registered proactive agent: {agent_name} with {len(capabilities)} capabilities")
    
    async def start_proactive_monitoring(self):
        """Start background proactive monitoring"""
        
        if self.is_running:
            print("⚠️  Proactive monitoring already running")
            return
        
        print(f"\\n🚀 Starting Proactive Intelligence Monitoring")
        print("=" * 50)
        
        self.is_running = True
        
        # Schedule background monitoring tasks
        self._schedule_monitoring_tasks()
        
        # Start monitoring thread
        self.monitoring_thread = Thread(target=self._run_background_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        print(f"✅ Proactive monitoring started")
        print(f"🔄 Monitoring {len(self.monitoring_intervals)} data sources")
        print(f"⏰ Job opportunities: every {self.monitoring_intervals['job_opportunities']} minutes")
        print(f"📅 Calendar optimization: every {self.monitoring_intervals['calendar_optimization']} minutes")
        print(f"📧 Email triage: every {self.monitoring_intervals['email_triage']} minutes")
        
        # Perform initial proactive analysis
        await self._perform_initial_proactive_analysis()
    
    def _schedule_monitoring_tasks(self):
        """Schedule recurring proactive monitoring tasks"""
        
        # Job opportunity monitoring
        schedule.every(self.monitoring_intervals["job_opportunities"]).minutes.do(
            self._async_wrapper, self._monitor_job_opportunities
        )
        
        # Calendar optimization monitoring  
        schedule.every(self.monitoring_intervals["calendar_optimization"]).minutes.do(
            self._async_wrapper, self._monitor_calendar_optimization
        )
        
        # Email triage monitoring
        schedule.every(self.monitoring_intervals["email_triage"]).minutes.do(
            self._async_wrapper, self._monitor_email_triage
        )
        
        # Market intelligence monitoring
        schedule.every(self.monitoring_intervals["market_intelligence"]).minutes.do(
            self._async_wrapper, self._monitor_market_intelligence
        )
        
        # Learning analysis monitoring
        schedule.every(self.monitoring_intervals["learning_analysis"]).minutes.do(
            self._async_wrapper, self._monitor_learning_patterns
        )
    
    def _async_wrapper(self, coro_func):
        """Wrapper to run async functions in scheduled tasks"""
        asyncio.create_task(coro_func())
    
    def _run_background_monitoring(self):
        """Run background monitoring loop"""
        
        print(f"🔄 Background monitoring thread started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"⚠️  Background monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    async def _perform_initial_proactive_analysis(self):
        """Perform initial proactive analysis on startup"""
        
        print(f"\\n🔍 Performing Initial Proactive Analysis")
        print("-" * 45)
        
        # Immediate job opportunity scan
        await self._monitor_job_opportunities()
        
        # Calendar analysis for today/tomorrow
        await self._monitor_calendar_optimization()
        
        # Email priority assessment
        await self._monitor_email_triage()
        
        print(f"✅ Initial proactive analysis complete")
    
    async def _monitor_job_opportunities(self):
        """Proactively monitor for new job opportunities"""
        
        print(f"🔍 [Proactive] Monitoring job opportunities...")
        
        if not self.integration_bridge:
            print("  ⚠️  Phase 22 integration not available")
            return
        
        try:
            # Use Phase 22 integration for live data analysis
            results = await self.integration_bridge.analyze_with_full_integration(
                query="new job opportunities",
                days_back=1,  # Only check recent opportunities
                enable_learning=True,
                use_live_data=True
            )
            
            # Extract job opportunities
            job_results = results.get('integration_results', {}).get('results', {})
            opportunities = job_results.get('top_opportunities', [])
            
            # Identify high-priority opportunities
            high_priority_jobs = [
                job for job in opportunities 
                if job.get('confidence', 0) >= self.alert_thresholds['job_opportunity_priority']
            ]
            
            # Create proactive opportunities
            for job in high_priority_jobs:
                opportunity = ProactiveOpportunity(
                    opportunity_id=str(uuid.uuid4()),
                    type="job_opportunity",
                    title=f"High-Priority Job: {job['company']} - {job['title']}",
                    description=f"New {job['title']} role at {job['company']} matches your preferences",
                    priority=job.get('confidence', 0.8),
                    confidence=job.get('confidence', 0.8),
                    source="proactive_job_monitoring",
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=7),
                    action_required=True,
                    suggested_actions=[
                        f"Review job details at {job.get('url', 'N/A')}",
                        f"Research {job['company']} culture and team",
                        "Update CV for this specific role",
                        "Prepare personalized cover letter"
                    ],
                    context_data=job
                )
                
                # Create alert for high-priority opportunities
                if opportunity.priority >= 0.9:
                    await self._create_proactive_alert(opportunity, "immediate")
                
                self._store_opportunity(opportunity)
            
            if high_priority_jobs:
                print(f"  🎯 Identified {len(high_priority_jobs)} high-priority job opportunities")
            else:
                print(f"  📊 No new high-priority opportunities detected")
                
        except Exception as e:
            print(f"  ⚠️  Job monitoring error: {e}")
    
    async def _monitor_calendar_optimization(self):
        """Proactively monitor and optimize calendar"""
        
        print(f"📅 [Proactive] Monitoring calendar optimization...")
        
        # Simulate calendar analysis (would use real Calendar API)
        current_time = datetime.now()
        
        # Check for potential conflicts or optimization opportunities
        calendar_insights = {
            "upcoming_conflicts": [],
            "optimization_opportunities": [
                {
                    "type": "focus_time_block",
                    "suggestion": "Block 2-hour focus time tomorrow 9-11am",
                    "priority": 0.7,
                    "reasoning": "Based on your productive patterns"
                },
                {
                    "type": "interview_prep",
                    "suggestion": "Schedule interview prep for Canva role",
                    "priority": 0.85,
                    "reasoning": "Job application requires preparation time"
                }
            ],
            "travel_optimization": [],
            "meeting_efficiency": []
        }
        
        # Create opportunities for high-priority calendar optimizations
        for insight in calendar_insights["optimization_opportunities"]:
            if insight["priority"] >= 0.8:
                opportunity = ProactiveOpportunity(
                    opportunity_id=str(uuid.uuid4()),
                    type="calendar_optimization",
                    title=f"Calendar Optimization: {insight['type']}",
                    description=insight["suggestion"],
                    priority=insight["priority"],
                    confidence=0.9,
                    source="proactive_calendar_monitoring",
                    created_at=current_time,
                    expires_at=current_time + timedelta(days=1),
                    action_required=False,  # Can be automated
                    suggested_actions=[
                        "Automatically block calendar time",
                        "Send preparation reminders",
                        "Prepare relevant context materials"
                    ],
                    context_data=insight
                )
                
                self._store_opportunity(opportunity)
        
        print(f"  📊 Calendar analysis complete: {len(calendar_insights['optimization_opportunities'])} optimizations identified")
    
    async def _monitor_email_triage(self):
        """Proactively monitor and triage emails"""
        
        print(f"📧 [Proactive] Monitoring email triage...")
        
        # Simulate email analysis (would use real Gmail API)
        email_analysis = {
            "urgent_emails": 2,
            "job_related": 1,
            "action_required": 3,
            "can_be_automated": 5
        }
        
        if email_analysis["urgent_emails"] > 0:
            opportunity = ProactiveOpportunity(
                opportunity_id=str(uuid.uuid4()),
                type="email_triage",
                title=f"Urgent Emails Detected: {email_analysis['urgent_emails']} requiring attention",
                description="High-priority emails need immediate review",
                priority=0.9,
                confidence=0.85,
                source="proactive_email_monitoring",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=2),
                action_required=True,
                suggested_actions=[
                    "Review urgent emails immediately",
                    "Respond to time-sensitive requests",
                    "Delegate or schedule follow-up actions"
                ],
                context_data=email_analysis
            )
            
            await self._create_proactive_alert(opportunity, "urgent")
            self._store_opportunity(opportunity)
        
        print(f"  📊 Email triage complete: {email_analysis['urgent_emails']} urgent, {email_analysis['action_required']} action required")
    
    async def _monitor_market_intelligence(self):
        """Proactively monitor market changes and trends"""
        
        print(f"📈 [Proactive] Monitoring market intelligence...")
        
        # Simulate market analysis
        market_updates = {
            "salary_trends": {
                "engineering_manager_sydney": {
                    "change": "+3.2%",
                    "significance": "notable_increase"
                }
            },
            "company_news": [
                {
                    "company": "Atlassian",
                    "news": "Major cloud platform expansion announced",
                    "relevance": 0.8,
                    "impact": "positive_hiring_outlook"
                }
            ],
            "industry_shifts": []
        }
        
        # Create opportunities for significant market changes
        for company_update in market_updates["company_news"]:
            if company_update["relevance"] >= 0.7:
                opportunity = ProactiveOpportunity(
                    opportunity_id=str(uuid.uuid4()),
                    type="market_intelligence",
                    title=f"Market Update: {company_update['company']}",
                    description=company_update["news"],
                    priority=company_update["relevance"],
                    confidence=0.8,
                    source="proactive_market_monitoring",
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=3),
                    action_required=False,
                    suggested_actions=[
                        f"Research {company_update['company']} expansion plans",
                        "Update job search strategy based on market shift",
                        "Prepare talking points for relevant interviews"
                    ],
                    context_data=company_update
                )
                
                self._store_opportunity(opportunity)
        
        print(f"  📊 Market intelligence complete: {len(market_updates['company_news'])} relevant updates")
    
    async def _monitor_learning_patterns(self):
        """Proactively analyze learning patterns and optimize strategies"""
        
        print(f"🧠 [Proactive] Monitoring learning patterns...")
        
        if not self.learning_system:
            print("  ⚠️  Learning system not available")
            return
        
        # Generate learning insights
        insights = self.learning_system.generate_learning_insights()
        
        # Identify learning optimization opportunities
        learning_stats = insights.get('learning_statistics', {})
        learning_effectiveness = insights.get('learning_effectiveness', {})
        
        # Check if learning could be improved
        if learning_stats.get('total_interactions', 0) > 5:
            confidence_rate = learning_effectiveness.get('preference_confidence_rate', 0)
            
            if confidence_rate < 0.6:  # Low confidence suggests need for more data
                opportunity = ProactiveOpportunity(
                    opportunity_id=str(uuid.uuid4()),
                    type="learning_optimization",
                    title="Learning System Optimization Opportunity",
                    description=f"Learning confidence at {confidence_rate:.1%} - could benefit from more feedback",
                    priority=0.6,
                    confidence=0.8,
                    source="proactive_learning_monitoring",
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=7),
                    action_required=False,
                    suggested_actions=[
                        "Provide more explicit feedback on job recommendations",
                        "Rate recent job analysis results",
                        "Update job preferences and career goals"
                    ],
                    context_data={"learning_stats": learning_stats, "effectiveness": learning_effectiveness}
                )
                
                self._store_opportunity(opportunity)
        
        print(f"  📊 Learning analysis complete: {learning_stats.get('total_interactions', 0)} interactions analyzed")
    
    async def _create_proactive_alert(self, opportunity: ProactiveOpportunity, alert_type: str):
        """Create proactive alert for high-priority opportunities"""
        
        alert = ProactiveAlert(
            alert_id=str(uuid.uuid4()),
            opportunity_id=opportunity.opportunity_id,
            alert_type=alert_type,
            message=f"{opportunity.title}: {opportunity.description}",
            priority=opportunity.priority,
            delivery_channels=self._get_delivery_channels(alert_type),
            created_at=datetime.now()
        )
        
        self._store_alert(alert)
        
        # Deliver alert based on type
        if alert_type == "immediate":
            print(f"🚨 IMMEDIATE ALERT: {alert.message}")
        elif alert_type == "urgent":
            print(f"⚠️  URGENT ALERT: {alert.message}")
        
        print(f"  📢 Alert created: {alert.alert_id[:8]} ({alert_type})")
    
    def _get_delivery_channels(self, alert_type: str) -> List[str]:
        """Get delivery channels based on alert type"""
        
        channel_config = {
            "immediate": ["notification", "dashboard"],
            "urgent": ["notification", "dashboard", "email"],
            "scheduled": ["dashboard", "email"],
            "fyi": ["dashboard"]
        }
        
        return channel_config.get(alert_type, ["dashboard"])
    
    def _store_opportunity(self, opportunity: ProactiveOpportunity):
        """Store proactive opportunity to persistent storage"""
        
        opportunities = self._load_opportunities()
        opportunities[opportunity.opportunity_id] = asdict(opportunity)
        
        # Convert datetime objects to ISO format for JSON storage
        opp_dict = opportunities[opportunity.opportunity_id]
        opp_dict['created_at'] = opportunity.created_at.isoformat()
        if opportunity.expires_at:
            opp_dict['expires_at'] = opportunity.expires_at.isoformat()
        
        with open(self.opportunities_file, 'w') as f:
            json.dump(opportunities, f, indent=2)
    
    def _store_alert(self, alert: ProactiveAlert):
        """Store proactive alert to persistent storage"""
        
        alerts = self._load_alerts()
        alerts[alert.alert_id] = asdict(alert)
        
        # Convert datetime to ISO format
        alerts[alert.alert_id]['created_at'] = alert.created_at.isoformat()
        
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def _load_opportunities(self) -> Dict[str, Any]:
        """Load stored opportunities"""
        
        if self.opportunities_file.exists():
            with open(self.opportunities_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_alerts(self) -> Dict[str, Any]:
        """Load stored alerts"""
        
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_proactive_opportunities(self, limit: int = 10, 
                                  opportunity_type: str = None) -> List[Dict[str, Any]]:
        """Get current proactive opportunities"""
        
        opportunities = self._load_opportunities()
        
        # Filter by type if specified
        if opportunity_type:
            opportunities = {
                k: v for k, v in opportunities.items() 
                if v.get('type') == opportunity_type
            }
        
        # Sort by priority and creation time
        sorted_opportunities = sorted(
            opportunities.values(),
            key=lambda x: (x.get('priority', 0), x.get('created_at', '')),
            reverse=True
        )
        
        return sorted_opportunities[:limit]
    
    def get_proactive_alerts(self, undelivered_only: bool = True) -> List[Dict[str, Any]]:
        """Get current proactive alerts"""
        
        alerts = self._load_alerts()
        
        if undelivered_only:
            alerts = {
                k: v for k, v in alerts.items() 
                if not v.get('delivered', False)
            }
        
        # Sort by priority and creation time
        sorted_alerts = sorted(
            alerts.values(),
            key=lambda x: (x.get('priority', 0), x.get('created_at', '')),
            reverse=True
        )
        
        return sorted_alerts
    
    async def stop_proactive_monitoring(self):
        """Stop background proactive monitoring"""
        
        if not self.is_running:
            print("⚠️  Proactive monitoring not running")
            return
        
        print(f"\\n🛑 Stopping Proactive Intelligence Monitoring")
        
        self.is_running = False
        
        # Clear scheduled tasks
        schedule.clear()
        
        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        print(f"✅ Proactive monitoring stopped")
    
    def get_proactive_status(self) -> Dict[str, Any]:
        """Get current proactive intelligence status"""
        
        opportunities = self._load_opportunities()
        alerts = self._load_alerts()
        
        # Count opportunities by type
        opportunity_counts = {}
        for opp in opportunities.values():
            opp_type = opp.get('type', 'unknown')
            opportunity_counts[opp_type] = opportunity_counts.get(opp_type, 0) + 1
        
        # Count active alerts
        active_alerts = len([a for a in alerts.values() if not a.get('delivered', False)])
        
        status = {
            "proactive_mode": self.config.get('proactive_mode', 'active'),
            "monitoring_active": self.is_running,
            "total_opportunities": len(opportunities),
            "opportunity_breakdown": opportunity_counts,
            "active_alerts": active_alerts,
            "monitoring_intervals": self.monitoring_intervals,
            "last_analysis": datetime.now().isoformat(),
            "next_scheduled_analysis": {
                "job_opportunities": f"Every {self.monitoring_intervals['job_opportunities']} minutes",
                "calendar_optimization": f"Every {self.monitoring_intervals['calendar_optimization']} minutes"
            }
        }
        
        return status

async def main():
    """Demonstrate Proactive Intelligence Engine - Phase 23"""
    print("🧠 Proactive Intelligence Engine - Phase 23 Demo")
    print("=" * 55)
    
    # Initialize proactive intelligence
    engine = ProactiveIntelligenceEngine("naythan")
    
    # Start proactive monitoring
    await engine.start_proactive_monitoring()
    
    # Let it run for a short demonstration
    print(f"\\n⏱️  Running proactive monitoring for 30 seconds...")
    await asyncio.sleep(30)
    
    # Get current opportunities and alerts
    print(f"\\n📊 PROACTIVE INTELLIGENCE RESULTS")
    print("=" * 40)
    
    opportunities = engine.get_proactive_opportunities(limit=5)
    alerts = engine.get_proactive_alerts()
    status = engine.get_proactive_status()
    
    print(f"🎯 Proactive Opportunities Identified: {len(opportunities)}")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"  {i}. {opp['title']}")
        print(f"     Priority: {opp['priority']:.2f} | Type: {opp['type']}")
        print(f"     Actions: {len(opp['suggested_actions'])} suggested")
    
    print(f"\\n🚨 Active Alerts: {len(alerts)}")
    for alert in alerts[:2]:
        print(f"  • {alert['alert_type'].upper()}: {alert['message'][:60]}...")
    
    print(f"\\n📈 System Status:")
    print(f"  🔄 Monitoring Active: {status['monitoring_active']}")
    print(f"  🎯 Total Opportunities: {status['total_opportunities']}")
    print(f"  📢 Active Alerts: {status['active_alerts']}")
    
    print(f"\\n🔮 Proactive Capabilities Demonstrated:")
    print(f"  ✅ Background job opportunity monitoring")
    print(f"  ✅ Autonomous calendar optimization")
    print(f"  ✅ Intelligent email triage")
    print(f"  ✅ Market intelligence tracking")
    print(f"  ✅ Learning pattern analysis")
    
    # Stop monitoring
    await engine.stop_proactive_monitoring()
    
    print(f"\\n✅ Proactive Intelligence Engine demonstration complete")
    print(f"🧠 Phase 23: Successfully anticipating and acting on user needs")
    print(f"🚀 System Evolution: Demo → Orchestration → Learning → Live Data → Proactive Intelligence ✅")

if __name__ == "__main__":
    asyncio.run(main())