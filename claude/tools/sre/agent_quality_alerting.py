#!/usr/bin/env python3
"""
Agent Quality Alerting System - Real-time Quality Regression Detection

Monitors agent quality scores in real-time and triggers alerts when:
- Quality drops below threshold (< 75/100)
- Sudden regression detected (>10 point drop)
- Pattern of declining quality (3+ consecutive drops)
- Critical failure (< 60/100)

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 4, Task 4.3
Integration: Uses AutomatedQualityScorer for scoring
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import statistics


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of quality alerts"""
    THRESHOLD_BREACH = "threshold_breach"  # Score < threshold
    SUDDEN_REGRESSION = "sudden_regression"  # Large drop
    DECLINING_TREND = "declining_trend"  # Pattern of drops
    CRITICAL_FAILURE = "critical_failure"  # Score < 60
    RECOVERY = "recovery"  # Quality improved


@dataclass
class QualityAlert:
    """Quality alert"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    agent_name: str
    current_score: float
    previous_score: Optional[float]
    threshold: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class AlertRule:
    """Configurable alert rule"""
    rule_id: str
    name: str
    condition: str  # "score_below", "drop_greater_than", "consecutive_drops"
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 60  # Min time between same alerts


class AgentQualityAlertingSystem:
    """
    Real-time alerting system for agent quality monitoring.

    Features:
    - Multiple alert rules (threshold, regression, trend)
    - Configurable severity levels
    - Alert cooldown to prevent spam
    - Alert history and analytics
    - Integration with quality scorer
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize alerting system.

        Args:
            config_file: Path to alert configuration (optional)
        """
        # Storage
        self.alerts_dir = Path(__file__).parent.parent.parent / "data" / "quality_alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.alerts_dir / "alerts.json"
        self.alert_history_file = self.alerts_dir / "alert_history.json"
        self.config_file = config_file or (self.alerts_dir / "alert_config.json")

        # Load configuration
        self.rules = self._load_alert_rules()
        self.alert_history: List[QualityAlert] = self._load_alert_history()
        self.agent_scores_history: Dict[str, List[float]] = {}

    def check_quality(
        self,
        agent_name: str,
        quality_score: float,
        response_id: str
    ) -> List[QualityAlert]:
        """
        Check quality score and trigger alerts if needed.

        Args:
            agent_name: Name of agent
            quality_score: Quality score (0-100)
            response_id: Unique response identifier

        Returns:
            List of triggered alerts (empty if no alerts)
        """
        alerts = []

        # Get previous score for comparison
        previous_score = self._get_previous_score(agent_name)

        # Update score history
        self._update_score_history(agent_name, quality_score)

        # Check each alert rule
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check cooldown (prevent alert spam)
            if not self._is_cooldown_expired(agent_name, rule.rule_id):
                continue

            # Evaluate rule
            alert = self._evaluate_rule(
                rule=rule,
                agent_name=agent_name,
                current_score=quality_score,
                previous_score=previous_score,
                response_id=response_id
            )

            if alert:
                alerts.append(alert)
                self._save_alert(alert)

        return alerts

    def _evaluate_rule(
        self,
        rule: AlertRule,
        agent_name: str,
        current_score: float,
        previous_score: Optional[float],
        response_id: str
    ) -> Optional[QualityAlert]:
        """Evaluate a single alert rule"""

        alert_id = f"{agent_name}_{rule.rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Rule 1: Score below threshold
        if rule.condition == "score_below" and current_score < rule.threshold:
            return QualityAlert(
                alert_id=alert_id,
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=rule.severity,
                agent_name=agent_name,
                current_score=current_score,
                previous_score=previous_score,
                threshold=rule.threshold,
                message=f"Agent '{agent_name}' quality below threshold: {current_score:.1f} < {rule.threshold}",
                details={
                    "rule_name": rule.name,
                    "response_id": response_id,
                    "delta": rule.threshold - current_score
                },
                timestamp=datetime.now()
            )

        # Rule 2: Sudden drop (regression)
        if rule.condition == "drop_greater_than" and previous_score is not None:
            drop = previous_score - current_score
            if drop > rule.threshold:
                return QualityAlert(
                    alert_id=alert_id,
                    alert_type=AlertType.SUDDEN_REGRESSION,
                    severity=rule.severity,
                    agent_name=agent_name,
                    current_score=current_score,
                    previous_score=previous_score,
                    threshold=rule.threshold,
                    message=f"Agent '{agent_name}' quality dropped suddenly: -{drop:.1f} points",
                    details={
                        "rule_name": rule.name,
                        "response_id": response_id,
                        "drop_amount": drop,
                        "previous_score": previous_score
                    },
                    timestamp=datetime.now()
                )

        # Rule 3: Consecutive drops (declining trend)
        if rule.condition == "consecutive_drops":
            recent_scores = self._get_recent_scores(agent_name, n=int(rule.threshold))
            if len(recent_scores) >= rule.threshold and self._is_declining_trend(recent_scores):
                return QualityAlert(
                    alert_id=alert_id,
                    alert_type=AlertType.DECLINING_TREND,
                    severity=rule.severity,
                    agent_name=agent_name,
                    current_score=current_score,
                    previous_score=previous_score,
                    threshold=rule.threshold,
                    message=f"Agent '{agent_name}' quality declining: {int(rule.threshold)} consecutive drops",
                    details={
                        "rule_name": rule.name,
                        "response_id": response_id,
                        "recent_scores": recent_scores,
                        "trend": "declining"
                    },
                    timestamp=datetime.now()
                )

        # Rule 4: Critical failure
        if rule.condition == "critical_failure" and current_score < rule.threshold:
            return QualityAlert(
                alert_id=alert_id,
                alert_type=AlertType.CRITICAL_FAILURE,
                severity=AlertSeverity.CRITICAL,
                agent_name=agent_name,
                current_score=current_score,
                previous_score=previous_score,
                threshold=rule.threshold,
                message=f"🚨 CRITICAL: Agent '{agent_name}' quality critically low: {current_score:.1f}",
                details={
                    "rule_name": rule.name,
                    "response_id": response_id,
                    "immediate_action_required": True
                },
                timestamp=datetime.now()
            )

        return None

    def _is_declining_trend(self, scores: List[float]) -> bool:
        """Check if scores show declining trend"""
        if len(scores) < 2:
            return False

        # Each score should be lower than previous
        for i in range(1, len(scores)):
            if scores[i] >= scores[i - 1]:
                return False

        return True

    def _get_previous_score(self, agent_name: str) -> Optional[float]:
        """Get most recent score for agent"""
        if agent_name in self.agent_scores_history:
            scores = self.agent_scores_history[agent_name]
            if len(scores) > 0:
                return scores[-1]
        return None

    def _get_recent_scores(self, agent_name: str, n: int) -> List[float]:
        """Get last N scores for agent"""
        if agent_name in self.agent_scores_history:
            return self.agent_scores_history[agent_name][-n:]
        return []

    def _update_score_history(self, agent_name: str, score: float):
        """Update score history for agent"""
        if agent_name not in self.agent_scores_history:
            self.agent_scores_history[agent_name] = []

        self.agent_scores_history[agent_name].append(score)

        # Keep last 100 scores only
        if len(self.agent_scores_history[agent_name]) > 100:
            self.agent_scores_history[agent_name] = self.agent_scores_history[agent_name][-100:]

    def _is_cooldown_expired(self, agent_name: str, rule_id: str) -> bool:
        """Check if cooldown period has expired"""
        # Find most recent alert for this agent + rule
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.agent_name == agent_name
            and alert.alert_id.find(rule_id) != -1
        ]

        if not recent_alerts:
            return True

        # Check most recent alert timestamp
        most_recent = max(recent_alerts, key=lambda a: a.timestamp)
        rule = next((r for r in self.rules if r.rule_id == rule_id), None)

        if not rule:
            return True

        cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
        return datetime.now() - most_recent.timestamp > cooldown_delta

    def _save_alert(self, alert: QualityAlert):
        """Save alert to history"""
        self.alert_history.append(alert)

        # Save to file
        alerts_data = []
        if self.alert_history_file.exists():
            with open(self.alert_history_file, 'r') as f:
                alerts_data = json.load(f)

        alerts_data.append({
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type.value,
            'severity': alert.severity.value,
            'agent_name': alert.agent_name,
            'current_score': alert.current_score,
            'previous_score': alert.previous_score,
            'threshold': alert.threshold,
            'message': alert.message,
            'details': alert.details,
            'timestamp': alert.timestamp.isoformat(),
            'acknowledged': alert.acknowledged,
            'resolved': alert.resolved
        })

        with open(self.alert_history_file, 'w') as f:
            json.dump(alerts_data, f, indent=2)

    def _load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from config"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return [
                    AlertRule(
                        rule_id=r['rule_id'],
                        name=r['name'],
                        condition=r['condition'],
                        threshold=r['threshold'],
                        severity=AlertSeverity(r['severity']),
                        enabled=r.get('enabled', True),
                        cooldown_minutes=r.get('cooldown_minutes', 60)
                    )
                    for r in config.get('rules', [])
                ]

        # Default rules
        return [
            AlertRule(
                rule_id="quality_below_75",
                name="Quality Below Threshold (75)",
                condition="score_below",
                threshold=75.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=60
            ),
            AlertRule(
                rule_id="sudden_drop_10",
                name="Sudden Quality Drop (>10 points)",
                condition="drop_greater_than",
                threshold=10.0,
                severity=AlertSeverity.ERROR,
                cooldown_minutes=30
            ),
            AlertRule(
                rule_id="declining_3",
                name="Declining Trend (3 consecutive drops)",
                condition="consecutive_drops",
                threshold=3.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=120
            ),
            AlertRule(
                rule_id="critical_below_60",
                name="Critical Quality Failure (<60)",
                condition="critical_failure",
                threshold=60.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=15
            )
        ]

    def _load_alert_history(self) -> List[QualityAlert]:
        """Load alert history from file"""
        if not self.alert_history_file.exists():
            return []

        with open(self.alert_history_file, 'r') as f:
            data = json.load(f)
            return [
                QualityAlert(
                    alert_id=a['alert_id'],
                    alert_type=AlertType(a['alert_type']),
                    severity=AlertSeverity(a['severity']),
                    agent_name=a['agent_name'],
                    current_score=a['current_score'],
                    previous_score=a.get('previous_score'),
                    threshold=a['threshold'],
                    message=a['message'],
                    details=a['details'],
                    timestamp=datetime.fromisoformat(a['timestamp']),
                    acknowledged=a.get('acknowledged', False),
                    resolved=a.get('resolved', False)
                )
                for a in data[-100:]  # Keep last 100 alerts in memory
            ]

    def get_active_alerts(self) -> List[QualityAlert]:
        """Get all unresolved alerts"""
        return [a for a in self.alert_history if not a.resolved]

    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break

    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.resolved = True
                break

    def get_agent_health_summary(self) -> Dict[str, Any]:
        """Get summary of agent health status"""
        active_alerts = self.get_active_alerts()

        return {
            'total_agents_monitored': len(self.agent_scores_history),
            'active_alerts': len(active_alerts),
            'alerts_by_severity': {
                'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                'error': len([a for a in active_alerts if a.severity == AlertSeverity.ERROR]),
                'warning': len([a for a in active_alerts if a.severity == AlertSeverity.WARNING])
            },
            'agents_with_alerts': list(set([a.agent_name for a in active_alerts])),
            'agent_average_scores': {
                agent: statistics.mean(scores[-10:]) if len(scores) >= 10 else statistics.mean(scores)
                for agent, scores in self.agent_scores_history.items()
            }
        }


def demo():
    """Demonstrate quality alerting system"""
    print("=" * 80)
    print("Agent Quality Alerting System Demo")
    print("=" * 80)

    alerting = AgentQualityAlertingSystem()

    # Simulate agent quality scores
    test_scenarios = [
        ("dns_specialist", 88, "resp_001"),  # Good quality
        ("dns_specialist", 72, "resp_002"),  # Below threshold (alert!)
        ("sre_agent", 85, "resp_003"),  # Good
        ("sre_agent", 70, "resp_004"),  # Sudden drop (alert!)
        ("azure_agent", 80, "resp_005"),  # Good
        ("azure_agent", 75, "resp_006"),  # Declining
        ("azure_agent", 70, "resp_007"),  # Declining
        ("azure_agent", 65, "resp_008"),  # Declining trend (alert!)
        ("service_desk", 55, "resp_009"),  # Critical (alert!)
    ]

    print("\n📊 Simulating Agent Quality Checks:")
    print("-" * 80)

    for agent_name, score, response_id in test_scenarios:
        print(f"\n🔍 Checking: {agent_name} | Score: {score}/100 | Response: {response_id}")

        alerts = alerting.check_quality(agent_name, score, response_id)

        if alerts:
            for alert in alerts:
                print(f"   🚨 ALERT: [{alert.severity.value.upper()}] {alert.message}")
                print(f"      Type: {alert.alert_type.value}")
                print(f"      Details: {alert.details}")
        else:
            print(f"   ✅ Quality acceptable (no alerts)")

    # Show active alerts summary
    print("\n" + "=" * 80)
    print("📋 Active Alerts Summary")
    print("=" * 80)

    active_alerts = alerting.get_active_alerts()
    print(f"\nTotal active alerts: {len(active_alerts)}")

    for alert in active_alerts:
        print(f"\n⚠️  Alert ID: {alert.alert_id}")
        print(f"   Agent: {alert.agent_name}")
        print(f"   Severity: {alert.severity.value.upper()}")
        print(f"   Message: {alert.message}")
        print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Show health summary
    print("\n" + "=" * 80)
    print("🏥 Agent Health Summary")
    print("=" * 80)

    health = alerting.get_agent_health_summary()
    print(f"\nAgents Monitored: {health['total_agents_monitored']}")
    print(f"Active Alerts: {health['active_alerts']}")
    print(f"\nAlerts by Severity:")
    print(f"   - Critical: {health['alerts_by_severity']['critical']}")
    print(f"   - Error: {health['alerts_by_severity']['error']}")
    print(f"   - Warning: {health['alerts_by_severity']['warning']}")
    print(f"\nAgents with Alerts: {', '.join(health['agents_with_alerts'])}")
    print(f"\nAverage Scores:")
    for agent, avg_score in health['agent_average_scores'].items():
        status = "✅" if avg_score >= 75 else "⚠️" if avg_score >= 60 else "🚨"
        print(f"   {status} {agent}: {avg_score:.1f}/100")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print(f"\nAlerts saved to: {alerting.alert_history_file}")


if __name__ == "__main__":
    demo()
