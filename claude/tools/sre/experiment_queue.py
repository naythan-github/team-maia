#!/usr/bin/env python3
"""
Experiment Queue System
Priority-based scheduling for multiple A/B experiments

Purpose:
- Manage multiple concurrent experiments (max 3 active)
- Priority-based scheduling (high/medium/low)
- Queue management (add, start, pause, complete)
- Experiment history tracking
- Integration with ABTestingFramework

Author: Maia (Phase 4: Optimization & Automation)
Created: 2025-10-12
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict

class Priority(str, Enum):
    """Priority levels for experiments"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class QueueStatus(str, Enum):
    """Status of queued experiments"""
    QUEUED = "queued"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class QueuedExperiment:
    """Experiment in the queue"""
    experiment_id: str
    agent_name: str
    priority: Priority
    status: QueueStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedExperiment':
        """Create from dictionary"""
        return cls(**data)

class ExperimentQueue:
    """
    Manages priority-based scheduling for multiple experiments

    Features:
    - Maximum 3 concurrent active experiments
    - Priority-based auto-promotion (high > medium > low)
    - Pause/resume capability
    - Complete experiment history
    """

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize experiment queue

        Args:
            max_concurrent: Maximum number of concurrent active experiments (default: 3)
        """
        self.max_concurrent = max_concurrent
        self.maia_root = Path(__file__).resolve().parents[3]
        self.queue_dir = self.maia_root / "claude" / "context" / "session" / "experiment_queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        self.queue_file = self.queue_dir / "queue.json"
        self.history_file = self.queue_dir / "history.json"

        self.queue: List[QueuedExperiment] = self._load_queue()
        self.history: List[QueuedExperiment] = self._load_history()

    def _load_queue(self) -> List[QueuedExperiment]:
        """Load queue from disk"""
        if not self.queue_file.exists():
            return []

        with open(self.queue_file, 'r') as f:
            data = json.load(f)
            return [QueuedExperiment.from_dict(item) for item in data]

    def _save_queue(self):
        """Save queue to disk"""
        with open(self.queue_file, 'w') as f:
            json.dump([item.to_dict() for item in self.queue], f, indent=2)

    def _load_history(self) -> List[QueuedExperiment]:
        """Load history from disk"""
        if not self.history_file.exists():
            return []

        with open(self.history_file, 'r') as f:
            data = json.load(f)
            return [QueuedExperiment.from_dict(item) for item in data]

    def _save_history(self):
        """Save history to disk"""
        with open(self.history_file, 'w') as f:
            json.dump([item.to_dict() for item in self.history], f, indent=2)

    def add_experiment(self, experiment_id: str, agent_name: str,
                      priority: Priority = Priority.MEDIUM, notes: str = "") -> QueuedExperiment:
        """
        Add experiment to queue

        Args:
            experiment_id: Unique experiment identifier
            agent_name: Agent being tested
            priority: Priority level (high/medium/low)
            notes: Optional notes about experiment

        Returns:
            QueuedExperiment: Created queue entry
        """
        # Check if already in queue
        if any(item.experiment_id == experiment_id for item in self.queue):
            raise ValueError(f"Experiment {experiment_id} already in queue")

        queued_exp = QueuedExperiment(
            experiment_id=experiment_id,
            agent_name=agent_name,
            priority=priority,
            status=QueueStatus.QUEUED,
            created_at=datetime.now().isoformat(),
            notes=notes
        )

        self.queue.append(queued_exp)
        self._save_queue()

        # Auto-start if capacity available
        self._try_auto_start()

        return queued_exp

    def _try_auto_start(self):
        """Automatically start queued experiments if capacity available"""
        active_count = len([item for item in self.queue if item.status == QueueStatus.ACTIVE])

        if active_count >= self.max_concurrent:
            return  # At capacity

        # Find highest priority queued experiment
        priority_order = [Priority.HIGH, Priority.MEDIUM, Priority.LOW]

        for priority in priority_order:
            queued_items = [
                item for item in self.queue
                if item.status == QueueStatus.QUEUED and item.priority == priority
            ]

            if queued_items:
                # Start oldest queued experiment at this priority
                oldest = min(queued_items, key=lambda x: x.created_at)
                self.start_experiment(oldest.experiment_id)

                # Check if we can start more
                active_count += 1
                if active_count >= self.max_concurrent:
                    break

    def start_experiment(self, experiment_id: str) -> QueuedExperiment:
        """
        Start a queued experiment

        Args:
            experiment_id: Experiment to start

        Returns:
            QueuedExperiment: Updated queue entry
        """
        item = self._find_experiment(experiment_id)

        if item.status not in [QueueStatus.QUEUED, QueueStatus.PAUSED]:
            raise ValueError(f"Cannot start experiment in {item.status} status")

        active_count = len([i for i in self.queue if i.status == QueueStatus.ACTIVE])
        if active_count >= self.max_concurrent:
            raise ValueError(f"Already at max concurrent experiments ({self.max_concurrent})")

        item.status = QueueStatus.ACTIVE
        item.started_at = datetime.now().isoformat()

        self._save_queue()
        return item

    def pause_experiment(self, experiment_id: str, reason: str = "") -> QueuedExperiment:
        """
        Pause an active experiment

        Args:
            experiment_id: Experiment to pause
            reason: Optional reason for pausing

        Returns:
            QueuedExperiment: Updated queue entry
        """
        item = self._find_experiment(experiment_id)

        if item.status != QueueStatus.ACTIVE:
            raise ValueError(f"Cannot pause experiment in {item.status} status")

        item.status = QueueStatus.PAUSED
        if reason:
            item.notes += f"\nPaused: {reason}"

        self._save_queue()

        # Try to auto-start next queued experiment
        self._try_auto_start()

        return item

    def complete_experiment(self, experiment_id: str, outcome: str = "") -> QueuedExperiment:
        """
        Mark experiment as completed

        Args:
            experiment_id: Experiment to complete
            outcome: Optional outcome summary

        Returns:
            QueuedExperiment: Completed queue entry
        """
        item = self._find_experiment(experiment_id)

        if item.status != QueueStatus.ACTIVE:
            raise ValueError(f"Cannot complete experiment in {item.status} status")

        item.status = QueueStatus.COMPLETED
        item.completed_at = datetime.now().isoformat()
        if outcome:
            item.notes += f"\nOutcome: {outcome}"

        # Move to history
        self.queue.remove(item)
        self.history.append(item)

        self._save_queue()
        self._save_history()

        # Try to auto-start next queued experiment
        self._try_auto_start()

        return item

    def cancel_experiment(self, experiment_id: str, reason: str = "") -> QueuedExperiment:
        """
        Cancel a queued or active experiment

        Args:
            experiment_id: Experiment to cancel
            reason: Optional reason for cancellation

        Returns:
            QueuedExperiment: Cancelled queue entry
        """
        item = self._find_experiment(experiment_id)

        if item.status in [QueueStatus.COMPLETED, QueueStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel experiment in {item.status} status")

        was_active = item.status == QueueStatus.ACTIVE

        item.status = QueueStatus.CANCELLED
        item.completed_at = datetime.now().isoformat()
        if reason:
            item.notes += f"\nCancelled: {reason}"

        # Move to history
        self.queue.remove(item)
        self.history.append(item)

        self._save_queue()
        self._save_history()

        # If was active, try to auto-start next queued experiment
        if was_active:
            self._try_auto_start()

        return item

    def change_priority(self, experiment_id: str, new_priority: Priority) -> QueuedExperiment:
        """
        Change priority of queued experiment

        Args:
            experiment_id: Experiment to update
            new_priority: New priority level

        Returns:
            QueuedExperiment: Updated queue entry
        """
        item = self._find_experiment(experiment_id)

        if item.status != QueueStatus.QUEUED:
            raise ValueError(f"Cannot change priority of {item.status} experiment")

        item.priority = new_priority
        self._save_queue()

        return item

    def _find_experiment(self, experiment_id: str) -> QueuedExperiment:
        """Find experiment in queue by ID"""
        for item in self.queue:
            if item.experiment_id == experiment_id:
                return item

        raise ValueError(f"Experiment {experiment_id} not found in queue")

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status

        Returns:
            Dictionary with queue statistics and contents
        """
        active = [item for item in self.queue if item.status == QueueStatus.ACTIVE]
        queued = [item for item in self.queue if item.status == QueueStatus.QUEUED]
        paused = [item for item in self.queue if item.status == QueueStatus.PAUSED]

        # Sort queued by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        queued_sorted = sorted(queued, key=lambda x: (priority_order[x.priority], x.created_at))

        return {
            "capacity": {
                "max_concurrent": self.max_concurrent,
                "active_count": len(active),
                "available_slots": self.max_concurrent - len(active)
            },
            "queue_counts": {
                "active": len(active),
                "queued": len(queued),
                "paused": len(paused),
                "total": len(self.queue)
            },
            "active_experiments": [item.to_dict() for item in active],
            "queued_experiments": [item.to_dict() for item in queued_sorted],
            "paused_experiments": [item.to_dict() for item in paused],
            "history_count": len(self.history)
        }

    def get_history(self, limit: Optional[int] = None,
                   status: Optional[QueueStatus] = None) -> List[QueuedExperiment]:
        """
        Get experiment history

        Args:
            limit: Maximum number of entries to return (most recent first)
            status: Filter by status (completed/cancelled)

        Returns:
            List of historical experiments
        """
        history = self.history

        if status:
            history = [item for item in history if item.status == status]

        # Sort by completion time (most recent first)
        history_sorted = sorted(history, key=lambda x: x.completed_at or "", reverse=True)

        if limit:
            return history_sorted[:limit]

        return history_sorted


def main():
    """Example usage and testing"""
    queue = ExperimentQueue(max_concurrent=3)

    print("=== Experiment Queue System ===\n")

    # Add experiments with different priorities
    print("Adding experiments...")
    exp1 = queue.add_experiment("exp_001", "cloud_architect", Priority.HIGH, "Critical latency test")
    exp2 = queue.add_experiment("exp_002", "jobs_agent", Priority.MEDIUM, "Resume parsing test")
    exp3 = queue.add_experiment("exp_003", "linkedin_advisor", Priority.LOW, "Engagement optimization")
    exp4 = queue.add_experiment("exp_004", "financial_advisor", Priority.HIGH, "Risk assessment test")

    print(f"Added 4 experiments\n")

    # Check queue status
    status = queue.get_queue_status()
    print(f"Queue Status:")
    print(f"  Active: {status['queue_counts']['active']}/{status['capacity']['max_concurrent']}")
    print(f"  Queued: {status['queue_counts']['queued']}")
    print(f"  Available Slots: {status['capacity']['available_slots']}\n")

    print("Active Experiments:")
    for exp in status['active_experiments']:
        print(f"  - {exp['experiment_id']} ({exp['agent_name']}) - Priority: {exp['priority']}")

    print("\nQueued Experiments (priority order):")
    for exp in status['queued_experiments']:
        print(f"  - {exp['experiment_id']} ({exp['agent_name']}) - Priority: {exp['priority']}")

    # Complete an experiment
    print("\n\nCompleting exp_001...")
    queue.complete_experiment("exp_001", "Treatment 15% better, promoted")

    status = queue.get_queue_status()
    print(f"\nQueue Status After Completion:")
    print(f"  Active: {status['queue_counts']['active']}/{status['capacity']['max_concurrent']}")
    print(f"  Queued: {status['queue_counts']['queued']}")
    print(f"  History: {status['history_count']}")

    print("\nActive Experiments:")
    for exp in status['active_experiments']:
        print(f"  - {exp['experiment_id']} ({exp['agent_name']}) - Priority: {exp['priority']}")

    # Pause an experiment
    print("\n\nPausing exp_002...")
    queue.pause_experiment("exp_002", "Waiting for more data")

    status = queue.get_queue_status()
    print(f"\nQueue Status After Pause:")
    print(f"  Active: {status['queue_counts']['active']}/{status['capacity']['max_concurrent']}")
    print(f"  Queued: {status['queue_counts']['queued']}")
    print(f"  Paused: {status['queue_counts']['paused']}")

    # Show history
    print("\n\nExperiment History:")
    history = queue.get_history(limit=5)
    for exp in history:
        print(f"  - {exp.experiment_id} ({exp.agent_name}) - Status: {exp.status}")
        print(f"    Created: {exp.created_at}")
        print(f"    Completed: {exp.completed_at}")
        if exp.notes:
            print(f"    Notes: {exp.notes}")
        print()


if __name__ == "__main__":
    main()
