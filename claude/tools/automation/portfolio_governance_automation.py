#!/usr/bin/env python3
"""
Portfolio Governance Automation Suite
Component 6/6 of KAI Phase 3: MSP + DevOps Transformation Leadership

A comprehensive system for MSP portfolio governance, demand management, and capacity planning
optimized for Orro Group's Engineering Manager - Cloud role managing 400+ enterprise clients.

Key Features:
- MSP demand intake and prioritization with DevOps transformation focus
- Capacity planning for technical teams across multiple client engagements  
- Portfolio health monitoring and risk assessment
- Resource allocation optimization for MSP operations
- Client SLA compliance tracking and automation ROI measurement
- Integration with stakeholder relationship intelligence

Author: Maia (My AI Agent)
Created: 2025-01-12 (KAI Phase 3 MSP Optimization)
Context: Engineering Manager - Cloud role at Orro Group
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemandPriority(Enum):
    """MSP demand prioritization levels"""
    P1_CRITICAL = "p1_critical"        # SLA breaches, major incidents
    P2_HIGH = "p2_high"                # Client escalations, security issues
    P3_MEDIUM = "p3_medium"            # Planned transformations, optimizations
    P4_LOW = "p4_low"                  # Nice-to-have improvements

class DemandCategory(Enum):
    """MSP service demand categories"""
    INCIDENT_RESPONSE = "incident_response"
    TRANSFORMATION = "transformation" 
    OPTIMIZATION = "optimization"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    AUTOMATION = "automation"
    CAPACITY_EXPANSION = "capacity_expansion"
    CLIENT_ONBOARDING = "client_onboarding"

class ProjectStatus(Enum):
    """Portfolio project statuses"""
    INTAKE = "intake"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ResourceType(Enum):
    """MSP resource categories"""
    SENIOR_ENGINEER = "senior_engineer"
    DEVOPS_SPECIALIST = "devops_specialist"
    AUTOMATION_ENGINEER = "automation_engineer"
    SECURITY_SPECIALIST = "security_specialist"
    SOLUTION_ARCHITECT = "solution_architect"
    PROJECT_MANAGER = "project_manager"

@dataclass
class DemandRequest:
    """MSP demand request structure"""
    request_id: str
    client_id: str
    client_name: str
    title: str
    description: str
    category: DemandCategory
    priority: DemandPriority
    requested_date: datetime
    required_date: datetime
    estimated_effort_days: float
    required_skills: List[ResourceType]
    business_value: str
    risk_if_not_delivered: str
    submitter: str
    status: ProjectStatus = ProjectStatus.INTAKE
    approved_date: Optional[datetime] = None
    assigned_resources: List[str] = None
    
    def __post_init__(self):
        if self.assigned_resources is None:
            self.assigned_resources = []

@dataclass
class ResourceCapacity:
    """MSP team resource capacity"""
    resource_id: str
    name: str
    resource_type: ResourceType
    total_capacity_days: float
    allocated_days: float
    available_days: float
    current_projects: List[str]
    skills: List[str]
    utilization_rate: float
    
    def __post_init__(self):
        self.available_days = self.total_capacity_days - self.allocated_days
        self.utilization_rate = self.allocated_days / self.total_capacity_days if self.total_capacity_days > 0 else 0

@dataclass
class PortfolioMetrics:
    """MSP portfolio governance metrics"""
    total_active_projects: int
    total_demand_requests: int
    average_project_duration: float
    team_utilization_rate: float
    sla_compliance_rate: float
    automation_roi: float
    client_satisfaction_avg: float
    critical_projects_on_track: int
    resource_constraints: List[str]
    capacity_forecast_30_days: Dict[str, float]

class PortfolioGovernanceEngine:
    """Main MSP portfolio governance automation engine"""
    
    def __init__(self, db_path: str = str(Path(__file__).resolve().parents[4 if "claude/tools" in str(__file__) else 0] / "claude" / "data" / "portfolio_governance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with MSP portfolio schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS demand_requests (
                    request_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    requested_date TEXT NOT NULL,
                    required_date TEXT NOT NULL,
                    estimated_effort_days REAL NOT NULL,
                    required_skills TEXT NOT NULL,
                    business_value TEXT,
                    risk_if_not_delivered TEXT,
                    submitter TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approved_date TEXT,
                    assigned_resources TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_capacity (
                    resource_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    total_capacity_days REAL NOT NULL,
                    allocated_days REAL NOT NULL,
                    current_projects TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS governance_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_date TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    context TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    impact_assessment TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def submit_demand_request(self, request: DemandRequest) -> str:
        """Submit new MSP demand request for governance review"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO demand_requests 
                    (request_id, client_id, client_name, title, description, category, priority,
                     requested_date, required_date, estimated_effort_days, required_skills,
                     business_value, risk_if_not_delivered, submitter, status, assigned_resources)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.request_id, request.client_id, request.client_name, request.title,
                    request.description, request.category.value, request.priority.value,
                    request.requested_date.isoformat(), request.required_date.isoformat(),
                    request.estimated_effort_days, json.dumps([skill.value for skill in request.required_skills]),
                    request.business_value, request.risk_if_not_delivered, request.submitter,
                    request.status.value, json.dumps(request.assigned_resources)
                ))
                conn.commit()
            
            # Auto-prioritize based on MSP criteria
            await self._auto_prioritize_request(request.request_id)
            
            logger.info(f"Demand request {request.request_id} submitted successfully")
            return request.request_id
            
        except Exception as e:
            logger.error(f"Error submitting demand request: {e}")
            raise
    
    async def _auto_prioritize_request(self, request_id: str) -> None:
        """Auto-prioritize demand request based on MSP governance rules"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT category, priority, client_name, required_date, business_value
                    FROM demand_requests WHERE request_id = ?
                ''', (request_id,))
                
                result = cursor.fetchone()
                if not result:
                    return
                
                category, current_priority, client_name, required_date, business_value = result
                
                # MSP auto-prioritization logic
                new_priority = current_priority
                
                # Critical incidents always P1
                if category == DemandCategory.INCIDENT_RESPONSE.value:
                    new_priority = DemandPriority.P1_CRITICAL.value
                
                # Security issues are high priority
                elif category == DemandCategory.SECURITY.value:
                    new_priority = DemandPriority.P2_HIGH.value
                
                # Urgent timeline (< 7 days)
                required = datetime.fromisoformat(required_date)
                if required < datetime.now() + timedelta(days=7):
                    if new_priority == DemandPriority.P4_LOW.value:
                        new_priority = DemandPriority.P3_MEDIUM.value
                    elif new_priority == DemandPriority.P3_MEDIUM.value:
                        new_priority = DemandPriority.P2_HIGH.value
                
                # Update if priority changed
                if new_priority != current_priority:
                    conn.execute('''
                        UPDATE demand_requests 
                        SET priority = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE request_id = ?
                    ''', (new_priority, request_id))
                    conn.commit()
                    
                    logger.info(f"Auto-prioritized {request_id} from {current_priority} to {new_priority}")
        
        except Exception as e:
            logger.error(f"Error auto-prioritizing request {request_id}: {e}")
    
    async def get_portfolio_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive MSP portfolio governance dashboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Active projects by status
                cursor = conn.execute('''
                    SELECT status, COUNT(*) as count
                    FROM demand_requests 
                    WHERE status != 'cancelled'
                    GROUP BY status
                ''')
                status_counts = dict(cursor.fetchall())
                
                # Priority distribution
                cursor = conn.execute('''
                    SELECT priority, COUNT(*) as count
                    FROM demand_requests 
                    WHERE status IN ('intake', 'approved', 'in_progress')
                    GROUP BY priority
                ''')
                priority_counts = dict(cursor.fetchall())
                
                # Category analysis
                cursor = conn.execute('''
                    SELECT category, COUNT(*) as count, AVG(estimated_effort_days) as avg_effort
                    FROM demand_requests 
                    WHERE status != 'cancelled'
                    GROUP BY category
                ''')
                category_analysis = {row[0]: {"count": row[1], "avg_effort": row[2]} 
                                   for row in cursor.fetchall()}
                
                # Resource utilization
                cursor = conn.execute('''
                    SELECT resource_type, AVG(allocated_days/total_capacity_days) as avg_utilization
                    FROM resource_capacity 
                    GROUP BY resource_type
                ''')
                resource_utilization = dict(cursor.fetchall())
                
                # Overdue projects
                cursor = conn.execute('''
                    SELECT COUNT(*) 
                    FROM demand_requests 
                    WHERE required_date < date('now') 
                    AND status IN ('intake', 'approved', 'in_progress')
                ''')
                overdue_count = cursor.fetchone()[0]
                
                # Capacity forecast
                capacity_forecast = await self._generate_capacity_forecast()
                
                dashboard = {
                    "snapshot_time": datetime.now().isoformat(),
                    "portfolio_health": {
                        "total_active_projects": sum(status_counts.values()),
                        "projects_by_status": status_counts,
                        "overdue_projects": overdue_count,
                        "priority_distribution": priority_counts
                    },
                    "demand_analysis": {
                        "category_breakdown": category_analysis,
                        "total_estimated_effort": sum(data["count"] * data["avg_effort"] 
                                                    for data in category_analysis.values())
                    },
                    "resource_health": {
                        "utilization_by_type": resource_utilization,
                        "capacity_forecast_30_days": capacity_forecast,
                        "constraint_analysis": await self._identify_resource_constraints()
                    },
                    "governance_metrics": await self._calculate_governance_metrics()
                }
                
                return dashboard
                
        except Exception as e:
            logger.error(f"Error generating portfolio dashboard: {e}")
            raise
    
    async def _generate_capacity_forecast(self) -> Dict[str, float]:
        """Generate 30-day MSP team capacity forecast"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT resource_type, 
                           SUM(total_capacity_days - allocated_days) as available_capacity
                    FROM resource_capacity 
                    GROUP BY resource_type
                ''')
                
                capacity_by_type = dict(cursor.fetchall())
                
                # Factor in upcoming project completions (simplified)
                cursor = conn.execute('''
                    SELECT category, SUM(estimated_effort_days) as total_effort
                    FROM demand_requests 
                    WHERE status = 'in_progress'
                    GROUP BY category
                ''')
                
                in_progress_effort = dict(cursor.fetchall())
                
                # Simple forecast: assume 25% of in-progress work completes in 30 days
                forecast = {}
                for resource_type, available in capacity_by_type.items():
                    forecast[resource_type] = available + (sum(in_progress_effort.values()) * 0.25 / len(capacity_by_type))
                
                return forecast
                
        except Exception as e:
            logger.error(f"Error generating capacity forecast: {e}")
            return {}
    
    async def _identify_resource_constraints(self) -> List[str]:
        """Identify MSP resource capacity constraints"""
        constraints = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT resource_type, 
                           AVG(allocated_days/total_capacity_days) as utilization,
                           COUNT(*) as resource_count
                    FROM resource_capacity 
                    GROUP BY resource_type
                    HAVING utilization > 0.85
                ''')
                
                for resource_type, utilization, count in cursor.fetchall():
                    constraints.append(f"{resource_type}: {utilization:.1%} utilization ({count} resources)")
                
                # Check for skill gaps
                cursor = conn.execute('''
                    SELECT required_skills, COUNT(*) as demand_count
                    FROM demand_requests 
                    WHERE status IN ('intake', 'approved')
                    GROUP BY required_skills
                ''')
                
                for skills_json, demand_count in cursor.fetchall():
                    skills = json.loads(skills_json)
                    for skill in skills:
                        cursor = conn.execute('''
                            SELECT COUNT(*) 
                            FROM resource_capacity 
                            WHERE resource_type = ? AND allocated_days/total_capacity_days < 0.8
                        ''', (skill,))
                        
                        available_resources = cursor.fetchone()[0]
                        if demand_count > available_resources:
                            constraints.append(f"Skill gap: {demand_count} requests need {skill}, only {available_resources} available")
                
        except Exception as e:
            logger.error(f"Error identifying constraints: {e}")
        
        return constraints
    
    async def _calculate_governance_metrics(self) -> Dict[str, float]:
        """Calculate MSP portfolio governance KPIs"""
        metrics = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # On-time delivery rate
                cursor = conn.execute('''
                    SELECT 
                        COUNT(CASE WHEN required_date >= date('now') THEN 1 END) * 100.0 / COUNT(*) as on_time_rate
                    FROM demand_requests 
                    WHERE status = 'delivered'
                ''')
                result = cursor.fetchone()
                metrics["on_time_delivery_rate"] = result[0] if result[0] is not None else 0.0
                
                # Average project cycle time
                cursor = conn.execute('''
                    SELECT AVG(julianday(updated_at) - julianday(requested_date)) as avg_cycle_time
                    FROM demand_requests 
                    WHERE status = 'delivered'
                ''')
                result = cursor.fetchone()
                metrics["avg_cycle_time_days"] = result[0] if result[0] is not None else 0.0
                
                # Portfolio value delivery (simplified)
                cursor = conn.execute('''
                    SELECT COUNT(*) 
                    FROM demand_requests 
                    WHERE category = 'automation' AND status = 'delivered'
                ''')
                automation_delivered = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT COUNT(*) 
                    FROM demand_requests 
                    WHERE status = 'delivered'
                ''')
                total_delivered = cursor.fetchone()[0]
                
                metrics["automation_delivery_rate"] = (automation_delivered / total_delivered * 100) if total_delivered > 0 else 0.0
                
                # Resource optimization
                cursor = conn.execute('''
                    SELECT AVG(allocated_days/total_capacity_days) as avg_utilization
                    FROM resource_capacity
                ''')
                result = cursor.fetchone()
                metrics["team_utilization_rate"] = result[0] if result[0] is not None else 0.0
                
        except Exception as e:
            logger.error(f"Error calculating governance metrics: {e}")
        
        return metrics
    
    async def optimize_resource_allocation(self, scenario: str = "current") -> Dict[str, Any]:
        """MSP resource allocation optimization engine"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current resource state
                cursor = conn.execute('''
                    SELECT resource_id, resource_type, total_capacity_days, allocated_days, skills
                    FROM resource_capacity
                ''')
                resources = cursor.fetchall()
                
                # Get pending high-priority demands
                cursor = conn.execute('''
                    SELECT request_id, priority, required_skills, estimated_effort_days, required_date
                    FROM demand_requests 
                    WHERE status IN ('intake', 'approved')
                    ORDER BY 
                        CASE priority 
                            WHEN 'p1_critical' THEN 1
                            WHEN 'p2_high' THEN 2
                            WHEN 'p3_medium' THEN 3
                            WHEN 'p4_low' THEN 4
                        END,
                        required_date
                ''')
                demands = cursor.fetchall()
                
                # Optimization algorithm (simplified)
                recommendations = []
                resource_availability = {r[0]: r[2] - r[3] for r in resources}  # resource_id: available_days
                
                for demand_id, priority, skills_json, effort, required_date in demands:
                    required_skills = json.loads(skills_json)
                    
                    # Find best resource match
                    best_match = None
                    best_score = 0
                    
                    for resource_id, resource_type, total_cap, allocated, res_skills_json in resources:
                        if resource_availability[resource_id] >= effort:
                            res_skills = json.loads(res_skills_json)
                            
                            # Score based on skill match and availability
                            skill_match_score = len(set(required_skills) & set(res_skills)) / len(required_skills)
                            availability_score = resource_availability[resource_id] / total_cap
                            total_score = skill_match_score * 0.7 + availability_score * 0.3
                            
                            if total_score > best_score:
                                best_score = total_score
                                best_match = {
                                    "resource_id": resource_id,
                                    "resource_type": resource_type,
                                    "match_score": total_score,
                                    "skill_match": skill_match_score
                                }
                    
                    if best_match:
                        recommendations.append({
                            "demand_id": demand_id,
                            "priority": priority,
                            "recommended_resource": best_match,
                            "effort_days": effort,
                            "required_date": required_date
                        })
                        
                        # Update availability for next iteration
                        resource_availability[best_match["resource_id"]] -= effort
                
                return {
                    "scenario": scenario,
                    "optimization_timestamp": datetime.now().isoformat(),
                    "recommendations": recommendations,
                    "resource_utilization_after": {
                        r[0]: (r[3] + sum(rec["effort_days"] for rec in recommendations 
                                         if rec["recommended_resource"]["resource_id"] == r[0])) / r[2]
                        for r in resources
                    },
                    "unallocated_demands": len(demands) - len(recommendations)
                }
                
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            raise
    
    async def generate_governance_report(self, period_days: int = 30) -> str:
        """Generate comprehensive MSP portfolio governance report"""
        try:
            dashboard = await self.get_portfolio_dashboard()
            optimization = await self.optimize_resource_allocation()
            
            report_lines = []
            report_lines.append("# MSP Portfolio Governance Report")
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"Period: Last {period_days} days")
            report_lines.append("")
            
            # Executive Summary
            report_lines.append("## Executive Summary")
            portfolio_health = dashboard["portfolio_health"]
            report_lines.append(f"- **Total Active Projects**: {portfolio_health['total_active_projects']}")
            report_lines.append(f"- **Overdue Projects**: {portfolio_health['overdue_projects']}")
            
            governance_metrics = dashboard["governance_metrics"]
            report_lines.append(f"- **On-Time Delivery**: {governance_metrics.get('on_time_delivery_rate', 0):.1f}%")
            report_lines.append(f"- **Team Utilization**: {governance_metrics.get('team_utilization_rate', 0):.1f}%")
            report_lines.append(f"- **Automation Delivery**: {governance_metrics.get('automation_delivery_rate', 0):.1f}%")
            report_lines.append("")
            
            # Resource Analysis
            report_lines.append("## Resource Health Analysis")
            resource_health = dashboard["resource_health"]
            report_lines.append("### Utilization by Resource Type:")
            for resource_type, utilization in resource_health["utilization_by_type"].items():
                status = "🔴 Overloaded" if utilization > 0.85 else "🟡 High" if utilization > 0.75 else "🟢 Healthy"
                report_lines.append(f"- **{resource_type}**: {utilization:.1%} {status}")
            report_lines.append("")
            
            # Constraints
            if resource_health["constraint_analysis"]:
                report_lines.append("### ⚠️ Resource Constraints:")
                for constraint in resource_health["constraint_analysis"]:
                    report_lines.append(f"- {constraint}")
                report_lines.append("")
            
            # Demand Analysis
            report_lines.append("## Demand Pipeline Analysis")
            demand_analysis = dashboard["demand_analysis"]
            report_lines.append("### Requests by Category:")
            for category, data in demand_analysis["category_breakdown"].items():
                report_lines.append(f"- **{category}**: {data['count']} requests, avg {data['avg_effort']:.1f} days")
            report_lines.append("")
            
            # Optimization Recommendations
            report_lines.append("## Resource Optimization Recommendations")
            if optimization["recommendations"]:
                report_lines.append("### Priority Allocation Suggestions:")
                for rec in optimization["recommendations"][:10]:  # Top 10
                    resource = rec["recommended_resource"]
                    report_lines.append(f"- **{rec['demand_id']}** ({rec['priority']}) → {resource['resource_type']} (Match: {resource['match_score']:.1%})")
                
                if optimization["unallocated_demands"] > 0:
                    report_lines.append(f"\n⚠️ **{optimization['unallocated_demands']} demands** require additional capacity or external resources")
            report_lines.append("")
            
            # Governance Actions
            report_lines.append("## Recommended Governance Actions")
            actions = []
            
            # High utilization action
            high_util_types = [rt for rt, util in resource_health["utilization_by_type"].items() if util > 0.85]
            if high_util_types:
                actions.append(f"1. **Capacity Planning**: Consider hiring/contracting for {', '.join(high_util_types)}")
            
            # Overdue projects action
            if portfolio_health["overdue_projects"] > 0:
                actions.append(f"2. **Project Recovery**: Review {portfolio_health['overdue_projects']} overdue projects for scope/timeline adjustment")
            
            # Automation opportunity
            automation_rate = governance_metrics.get('automation_delivery_rate', 0)
            if automation_rate < 30:
                actions.append(f"3. **Automation Focus**: Current automation delivery at {automation_rate:.1f}% - target 35%+ for MSP efficiency")
            
            if not actions:
                actions.append("1. **Portfolio Health**: No critical governance actions required - maintain current trajectory")
            
            for action in actions:
                report_lines.append(action)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating governance report: {e}")
            raise

# CLI Interface for Portfolio Governance
async def main():
    """CLI interface for MSP portfolio governance operations"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python portfolio_governance_automation.py <command>")
        print("Commands: dashboard, report, optimize, add-demand, add-resource")
        return
    
    engine = PortfolioGovernanceEngine()
    command = sys.argv[1].lower()
    
    try:
        if command == "dashboard":
            dashboard = await engine.get_portfolio_dashboard()
            print(json.dumps(dashboard, indent=2, default=str))
        
        elif command == "report":
            report = await engine.generate_governance_report()
            print(report)
        
        elif command == "optimize":
            optimization = await engine.optimize_resource_allocation()
            print(json.dumps(optimization, indent=2, default=str))
        
        elif command == "add-demand":
            # Example demand request
            request = DemandRequest(
                request_id=f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                client_id="CLIENT001",
                client_name="Example Client",
                title="DevOps Transformation Initiative",
                description="Migrate legacy infrastructure to Azure with full automation",
                category=DemandCategory.TRANSFORMATION,
                priority=DemandPriority.P3_MEDIUM,
                requested_date=datetime.now(),
                required_date=datetime.now() + timedelta(days=60),
                estimated_effort_days=30.0,
                required_skills=[ResourceType.DEVOPS_SPECIALIST, ResourceType.SOLUTION_ARCHITECT],
                business_value="Reduce operational overhead by 40%, improve SLA compliance",
                risk_if_not_delivered="Client retention risk, competitive disadvantage",
                submitter="Engineering Manager"
            )
            
            request_id = await engine.submit_demand_request(request)
            print(f"Demand request submitted: {request_id}")
        
        elif command == "add-resource":
            # Example resource addition (would typically come from HR systems)
            with sqlite3.connect(engine.db_path) as conn:
                resource_id = f"RES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                conn.execute('''
                    INSERT INTO resource_capacity 
                    (resource_id, name, resource_type, total_capacity_days, allocated_days, current_projects, skills)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    resource_id,
                    "New DevOps Engineer", 
                    ResourceType.DEVOPS_SPECIALIST.value,
                    20.0,  # 20 days per month
                    0.0,
                    json.dumps([]),
                    json.dumps(["azure", "kubernetes", "terraform", "automation"])
                ))
                conn.commit()
                print(f"Resource added: {resource_id}")
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        logger.error(f"Error executing command {command}: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())