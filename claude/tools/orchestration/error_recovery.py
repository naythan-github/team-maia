"""
Error Recovery System for Agent Chain Orchestrator

Provides retry logic, rollback mechanisms, and recovery strategies for
production-resilient workflow orchestration.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 111, Workflow #8

Architecture:
    Error Detection → Recovery Strategy → Retry/Rollback → State Persistence

Key Features:
- Configurable retry policies (exponential backoff, linear, fixed)
- Rollback mechanisms for reverting partial state
- Recovery strategies (fail-fast, continue-on-error, retry-then-fail)
- Checkpoint system for workflow resume
- Comprehensive error classification and handling
"""

import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Classification of error severity"""
    TRANSIENT = "transient"      # Temporary errors (network, rate limit) - retry
    VALIDATION = "validation"     # Input/output validation errors - fail
    DEPENDENCY = "dependency"     # Missing dependencies - skip
    FATAL = "fatal"              # Unrecoverable errors - abort


class RecoveryStrategy(Enum):
    """Strategy for handling failures"""
    FAIL_FAST = "fail_fast"                    # Stop immediately on first error
    CONTINUE_ON_ERROR = "continue_on_error"    # Skip failed tasks, continue chain
    RETRY_THEN_FAIL = "retry_then_fail"        # Retry N times, then fail
    RETRY_THEN_SKIP = "retry_then_skip"        # Retry N times, then skip and continue


class RetryPolicy(Enum):
    """Retry backoff strategy"""
    NONE = "none"                       # No retries
    FIXED = "fixed"                     # Fixed delay between retries
    LINEAR = "linear"                   # Linearly increasing delay
    EXPONENTIAL = "exponential"         # Exponentially increasing delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    max_attempts: int = 3
    initial_delay_ms: int = 1000        # 1 second
    max_delay_ms: int = 30000           # 30 seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True                 # Add randomness to prevent thundering herd


@dataclass
class RecoveryConfig:
    """Configuration for error recovery"""
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY_THEN_FAIL
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    enable_rollback: bool = True
    checkpoint_enabled: bool = True
    checkpoint_dir: Optional[Path] = None


@dataclass
class ErrorContext:
    """Context information about an error"""
    subtask_id: int
    subtask_name: str
    error_message: str
    error_type: str
    severity: ErrorSeverity
    attempt_number: int
    timestamp: datetime
    stacktrace: Optional[str] = None


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""
    subtask_id: int
    attempt_number: int
    strategy_used: str
    success: bool
    timestamp: datetime
    delay_ms: float = 0.0
    error_message: Optional[str] = None


@dataclass
class Checkpoint:
    """State checkpoint for workflow resume"""
    chain_id: str
    workflow_name: str
    checkpoint_time: datetime
    completed_subtasks: List[int]
    context: Dict[str, Any]
    next_subtask_id: int
    recovery_attempts: List[RecoveryAttempt] = field(default_factory=list)


class ErrorClassifier:
    """Classifies errors by severity to determine recovery strategy"""

    def classify(self, error: Exception, error_message: str) -> ErrorSeverity:
        """
        Classify error severity based on error type and message.

        Returns:
            ErrorSeverity indicating how to handle the error
        """
        error_type = type(error).__name__
        message_lower = error_message.lower()

        # Transient errors (retry)
        transient_indicators = [
            "timeout", "connection", "network", "rate limit",
            "503", "502", "504", "temporarily unavailable"
        ]
        if any(indicator in message_lower for indicator in transient_indicators):
            return ErrorSeverity.TRANSIENT

        # Dependency errors (skip) - check before validation
        if "KeyError" in error_type or "dependencies not met" in message_lower:
            return ErrorSeverity.DEPENDENCY

        # Validation errors (fail immediately)
        validation_indicators = [
            "validation failed", "invalid", "schema", "required key",
            "malformed"
        ]
        if any(indicator in message_lower for indicator in validation_indicators):
            return ErrorSeverity.VALIDATION

        # Fatal errors (abort)
        fatal_indicators = [
            "out of memory", "disk full", "permission denied",
            "access denied", "authentication failed"
        ]
        if any(indicator in message_lower for indicator in fatal_indicators):
            return ErrorSeverity.FATAL

        # Default to transient (safer to retry than fail)
        return ErrorSeverity.TRANSIENT


class RetryManager:
    """Manages retry logic with configurable backoff strategies"""

    def __init__(self, config: RetryConfig):
        self.config = config

    def calculate_delay(self, attempt_number: int) -> float:
        """
        Calculate delay in milliseconds for the given attempt number.

        Args:
            attempt_number: Current attempt (1-based)

        Returns:
            Delay in milliseconds
        """
        if self.config.policy == RetryPolicy.NONE:
            return 0.0

        elif self.config.policy == RetryPolicy.FIXED:
            delay = self.config.initial_delay_ms

        elif self.config.policy == RetryPolicy.LINEAR:
            delay = self.config.initial_delay_ms * attempt_number

        elif self.config.policy == RetryPolicy.EXPONENTIAL:
            delay = self.config.initial_delay_ms * (
                self.config.backoff_multiplier ** (attempt_number - 1)
            )
        else:
            delay = self.config.initial_delay_ms

        # Cap at max delay
        delay = min(delay, self.config.max_delay_ms)

        # Add jitter (±25% randomness)
        if self.config.jitter:
            import random
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def should_retry(self, attempt_number: int, severity: ErrorSeverity) -> bool:
        """
        Determine if we should retry based on attempt count and error severity.

        Args:
            attempt_number: Current attempt number (1-based)
            severity: Error severity classification

        Returns:
            True if should retry, False otherwise
        """
        # Never retry validation or fatal errors
        if severity in [ErrorSeverity.VALIDATION, ErrorSeverity.FATAL]:
            return False

        # Check max attempts
        if attempt_number >= self.config.max_attempts:
            return False

        return True


class CheckpointManager:
    """Manages workflow state checkpoints for resume capability"""

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: Checkpoint) -> Path:
        """
        Save checkpoint to disk.

        Args:
            checkpoint: Checkpoint to save

        Returns:
            Path to saved checkpoint file
        """
        filename = f"{checkpoint.chain_id}_checkpoint.json"
        filepath = self.checkpoint_dir / filename

        # Convert to JSON-serializable format
        checkpoint_data = {
            "chain_id": checkpoint.chain_id,
            "workflow_name": checkpoint.workflow_name,
            "checkpoint_time": checkpoint.checkpoint_time.isoformat(),
            "completed_subtasks": checkpoint.completed_subtasks,
            "context": checkpoint.context,
            "next_subtask_id": checkpoint.next_subtask_id,
            "recovery_attempts": [
                {
                    "subtask_id": ra.subtask_id,
                    "attempt_number": ra.attempt_number,
                    "strategy_used": ra.strategy_used,
                    "success": ra.success,
                    "timestamp": ra.timestamp.isoformat(),
                    "delay_ms": ra.delay_ms,
                    "error_message": ra.error_message
                }
                for ra in checkpoint.recovery_attempts
            ]
        }

        filepath.write_text(json.dumps(checkpoint_data, indent=2))
        return filepath

    def load_checkpoint(self, chain_id: str) -> Optional[Checkpoint]:
        """
        Load checkpoint from disk.

        Args:
            chain_id: Chain execution ID

        Returns:
            Checkpoint if exists, None otherwise
        """
        filename = f"{chain_id}_checkpoint.json"
        filepath = self.checkpoint_dir / filename

        if not filepath.exists():
            return None

        checkpoint_data = json.loads(filepath.read_text())

        # Convert back to Checkpoint object
        return Checkpoint(
            chain_id=checkpoint_data["chain_id"],
            workflow_name=checkpoint_data["workflow_name"],
            checkpoint_time=datetime.fromisoformat(checkpoint_data["checkpoint_time"]),
            completed_subtasks=checkpoint_data["completed_subtasks"],
            context=checkpoint_data["context"],
            next_subtask_id=checkpoint_data["next_subtask_id"],
            recovery_attempts=[
                RecoveryAttempt(
                    subtask_id=ra["subtask_id"],
                    attempt_number=ra["attempt_number"],
                    strategy_used=ra["strategy_used"],
                    success=ra["success"],
                    timestamp=datetime.fromisoformat(ra["timestamp"]),
                    delay_ms=ra["delay_ms"],
                    error_message=ra.get("error_message")
                )
                for ra in checkpoint_data.get("recovery_attempts", [])
            ]
        )

    def delete_checkpoint(self, chain_id: str):
        """Delete checkpoint file"""
        filename = f"{chain_id}_checkpoint.json"
        filepath = self.checkpoint_dir / filename
        if filepath.exists():
            filepath.unlink()


class ErrorRecoverySystem:
    """
    Main error recovery system coordinating retry, rollback, and checkpoint logic.

    Usage:
        config = RecoveryConfig(
            strategy=RecoveryStrategy.RETRY_THEN_FAIL,
            retry_config=RetryConfig(max_attempts=3)
        )
        recovery = ErrorRecoverySystem(config)

        # Wrap subtask execution with recovery
        result = recovery.execute_with_recovery(
            subtask_id=1,
            subtask_name="Process Data",
            execution_func=lambda: orchestrator.execute_subtask(...)
        )
    """

    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.classifier = ErrorClassifier()
        self.retry_manager = RetryManager(config.retry_config)

        if config.checkpoint_enabled:
            checkpoint_dir = config.checkpoint_dir or (
                Path(__file__).parent.parent.parent / "context" / "session" / "checkpoints"
            )
            self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        else:
            self.checkpoint_manager = None

        self.recovery_attempts: List[RecoveryAttempt] = []

    def execute_with_recovery(
        self,
        subtask_id: int,
        subtask_name: str,
        execution_func: Callable,
        rollback_func: Optional[Callable] = None
    ) -> tuple[bool, Any, Optional[ErrorContext]]:
        """
        Execute function with error recovery logic.

        Args:
            subtask_id: ID of subtask being executed
            subtask_name: Name of subtask
            execution_func: Function to execute (returns result)
            rollback_func: Optional rollback function to call on failure

        Returns:
            Tuple of (success, result, error_context)
        """
        attempt = 0
        last_error = None

        while True:
            attempt += 1

            try:
                # Execute the function
                result = execution_func()

                # Success - record attempt
                self.recovery_attempts.append(RecoveryAttempt(
                    subtask_id=subtask_id,
                    attempt_number=attempt,
                    strategy_used=self.config.strategy.value,
                    success=True,
                    timestamp=datetime.now()
                ))

                return (True, result, None)

            except Exception as e:
                error_message = str(e)
                severity = self.classifier.classify(e, error_message)

                error_context = ErrorContext(
                    subtask_id=subtask_id,
                    subtask_name=subtask_name,
                    error_message=error_message,
                    error_type=type(e).__name__,
                    severity=severity,
                    attempt_number=attempt,
                    timestamp=datetime.now()
                )

                last_error = error_context

                # Determine if we should retry
                should_retry = self.retry_manager.should_retry(attempt, severity)

                if not should_retry:
                    # Record failed attempt
                    self.recovery_attempts.append(RecoveryAttempt(
                        subtask_id=subtask_id,
                        attempt_number=attempt,
                        strategy_used=self.config.strategy.value,
                        success=False,
                        timestamp=datetime.now(),
                        error_message=error_message
                    ))

                    # Call rollback if enabled
                    if self.config.enable_rollback and rollback_func:
                        try:
                            rollback_func()
                        except Exception as rollback_error:
                            # Log rollback failure but don't fail the recovery
                            pass

                    # Apply recovery strategy
                    if self.config.strategy == RecoveryStrategy.FAIL_FAST:
                        return (False, None, error_context)

                    elif self.config.strategy == RecoveryStrategy.CONTINUE_ON_ERROR:
                        return (False, None, error_context)  # Caller will continue

                    elif self.config.strategy == RecoveryStrategy.RETRY_THEN_FAIL:
                        return (False, None, error_context)

                    elif self.config.strategy == RecoveryStrategy.RETRY_THEN_SKIP:
                        return (False, None, error_context)  # Caller will skip

                else:
                    # Retry - calculate delay and wait
                    delay_ms = self.retry_manager.calculate_delay(attempt)

                    self.recovery_attempts.append(RecoveryAttempt(
                        subtask_id=subtask_id,
                        attempt_number=attempt,
                        strategy_used=f"retry_{attempt}",
                        success=False,
                        timestamp=datetime.now(),
                        delay_ms=delay_ms,
                        error_message=error_message
                    ))

                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)  # Convert to seconds

                    # Continue to next iteration (retry)
                    continue

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get statistics about recovery attempts"""
        if not self.recovery_attempts:
            return {
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "success_rate": 0.0
            }

        successful = sum(1 for ra in self.recovery_attempts if ra.success)

        return {
            "total_attempts": len(self.recovery_attempts),
            "successful_attempts": successful,
            "failed_attempts": len(self.recovery_attempts) - successful,
            "success_rate": successful / len(self.recovery_attempts),
            "average_attempts_per_subtask": len(self.recovery_attempts) / len(
                set(ra.subtask_id for ra in self.recovery_attempts)
            )
        }
