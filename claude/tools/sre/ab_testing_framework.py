"""
A/B Testing Framework - Automated Prompt Experimentation

Enables systematic testing of prompt variations with:
- Automatic 50/50 random assignment
- Automatic metric collection
- Statistical significance testing
- Automatic winner selection

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 4, Task 4.4
Research: claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md Section 5
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import math


class ExperimentStatus(Enum):
    """Experiment lifecycle status"""
    DRAFT = "draft"              # Being designed
    ACTIVE = "active"            # Running
    PAUSED = "paused"            # Temporarily stopped
    COMPLETED = "completed"      # Finished, results analyzed
    WINNER_PROMOTED = "promoted" # Winner deployed to production


@dataclass
class TreatmentArm:
    """One treatment arm in an experiment"""
    name: str  # e.g., "control", "treatment_extended_examples"
    prompt_file: Path  # Path to prompt file
    description: str
    interactions: int = 0
    successes: int = 0
    total_quality_score: float = 0.0
    total_tokens: int = 0
    total_latency_ms: float = 0.0


@dataclass
class ExperimentMetrics:
    """Collected metrics for an experiment"""
    completion_rate: float  # % of tasks completed successfully
    average_quality_score: float  # 0-100
    average_tokens: float
    average_latency_ms: float
    sample_size: int


@dataclass
class StatisticalResult:
    """Statistical significance test result"""
    p_value: float
    is_significant: bool  # p < 0.05
    effect_size: float  # Percentage improvement
    confidence_interval: Tuple[float, float]  # 95% CI for effect size


@dataclass
class Experiment:
    """Complete A/B test experiment"""
    experiment_id: str
    name: str
    hypothesis: str
    agent_name: str
    control: TreatmentArm
    treatment: TreatmentArm
    start_date: datetime
    end_date: Optional[datetime]
    status: ExperimentStatus
    minimum_sample_size: int = 100  # Min interactions per arm
    success_criteria: str = ">15% improvement with p<0.05"
    winner: Optional[str] = None  # "control" or "treatment"


class StatisticalAnalyzer:
    """Statistical significance testing for A/B experiments"""

    @staticmethod
    def two_proportion_z_test(control_successes: int, control_total: int,
                              treatment_successes: int, treatment_total: int) -> StatisticalResult:
        """
        Two-proportion Z-test for completion rate comparison.

        Args:
            control_successes: Number of successes in control
            control_total: Total interactions in control
            treatment_successes: Number of successes in treatment
            treatment_total: Total interactions in treatment

        Returns:
            StatisticalResult with p-value and significance
        """
        if control_total == 0 or treatment_total == 0:
            return StatisticalResult(
                p_value=1.0,
                is_significant=False,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0)
            )

        # Calculate proportions
        p_control = control_successes / control_total
        p_treatment = treatment_successes / treatment_total

        # Pooled proportion
        p_pooled = (control_successes + treatment_successes) / (control_total + treatment_total)

        # Standard error
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))

        # Z-score
        if se == 0:
            z_score = 0.0
        else:
            z_score = (p_treatment - p_control) / se

        # P-value (two-tailed)
        # Approximate using normal distribution
        p_value = 2 * (1 - StatisticalAnalyzer._normal_cdf(abs(z_score)))

        # Effect size (percentage improvement)
        effect_size = ((p_treatment - p_control) / p_control * 100) if p_control > 0 else 0.0

        # 95% confidence interval
        se_diff = math.sqrt(p_treatment * (1 - p_treatment) / treatment_total +
                           p_control * (1 - p_control) / control_total)
        margin = 1.96 * se_diff
        ci_lower = (p_treatment - p_control - margin) / p_control * 100 if p_control > 0 else 0.0
        ci_upper = (p_treatment - p_control + margin) / p_control * 100 if p_control > 0 else 0.0

        return StatisticalResult(
            p_value=p_value,
            is_significant=p_value < 0.05,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper)
        )

    @staticmethod
    def t_test(control_scores: List[float], treatment_scores: List[float]) -> StatisticalResult:
        """
        Welch's t-test for quality score comparison.

        Args:
            control_scores: List of quality scores for control
            treatment_scores: List of quality scores for treatment

        Returns:
            StatisticalResult with p-value and significance
        """
        if len(control_scores) < 2 or len(treatment_scores) < 2:
            return StatisticalResult(
                p_value=1.0,
                is_significant=False,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0)
            )

        # Calculate means
        mean_control = sum(control_scores) / len(control_scores)
        mean_treatment = sum(treatment_scores) / len(treatment_scores)

        # Calculate variances
        var_control = sum((x - mean_control)**2 for x in control_scores) / (len(control_scores) - 1)
        var_treatment = sum((x - mean_treatment)**2 for x in treatment_scores) / (len(treatment_scores) - 1)

        # Welch's t-test (unequal variances)
        se = math.sqrt(var_control / len(control_scores) + var_treatment / len(treatment_scores))

        if se == 0:
            t_stat = 0.0
        else:
            t_stat = (mean_treatment - mean_control) / se

        # Degrees of freedom (Welch-Satterthwaite)
        df = ((var_control / len(control_scores) + var_treatment / len(treatment_scores))**2 /
              ((var_control / len(control_scores))**2 / (len(control_scores) - 1) +
               (var_treatment / len(treatment_scores))**2 / (len(treatment_scores) - 1)))

        # P-value (approximate using normal distribution for large samples)
        p_value = 2 * (1 - StatisticalAnalyzer._normal_cdf(abs(t_stat)))

        # Effect size
        effect_size = ((mean_treatment - mean_control) / mean_control * 100) if mean_control > 0 else 0.0

        # 95% confidence interval
        margin = 1.96 * se
        ci_lower = (mean_treatment - mean_control - margin) / mean_control * 100 if mean_control > 0 else 0.0
        ci_upper = (mean_treatment - mean_control + margin) / mean_control * 100 if mean_control > 0 else 0.0

        return StatisticalResult(
            p_value=p_value,
            is_significant=p_value < 0.05,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper)
        )

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Cumulative distribution function for standard normal distribution"""
        # Approximate using error function
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


class ABTestingFramework:
    """
    Main A/B testing framework for automated prompt experimentation.

    Usage:
        framework = ABTestingFramework()

        # Create experiment
        experiment = framework.create_experiment(
            name="Extended Few-Shot Examples",
            hypothesis="3 examples improve quality by 15%+ vs 2 examples",
            agent_name="dns_specialist",
            control_prompt=Path("agents/dns_specialist_v2.md"),
            treatment_prompt=Path("agents/dns_specialist_v2_extended.md")
        )

        # Assign user to treatment arm
        arm = framework.assign_treatment(experiment.experiment_id, user_id="user123")

        # Record interaction result
        framework.record_interaction(
            experiment_id=experiment.experiment_id,
            user_id="user123",
            success=True,
            quality_score=85.0,
            tokens_used=500,
            latency_ms=2000
        )

        # Analyze results
        result = framework.analyze_experiment(experiment.experiment_id)
        if result.is_significant and result.effect_size > 15:
            framework.promote_winner(experiment.experiment_id)
    """

    def __init__(self, experiments_dir: Path = None):
        if experiments_dir is None:
            experiments_dir = Path(__file__).parent.parent.parent / "context" / "session" / "experiments"
        self.experiments_dir = experiments_dir
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

        self.analyzer = StatisticalAnalyzer()

    def create_experiment(self, name: str, hypothesis: str, agent_name: str,
                         control_prompt: Path, treatment_prompt: Path,
                         treatment_description: str = "") -> Experiment:
        """
        Create a new A/B test experiment.

        Args:
            name: Experiment name
            hypothesis: What you're testing
            agent_name: Which agent is being tested
            control_prompt: Path to control prompt file
            treatment_prompt: Path to treatment prompt file
            treatment_description: Description of what changed

        Returns:
            Experiment object
        """
        experiment_id = self._generate_experiment_id(name)

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            hypothesis=hypothesis,
            agent_name=agent_name,
            control=TreatmentArm(
                name="control",
                prompt_file=control_prompt,
                description="Current production prompt"
            ),
            treatment=TreatmentArm(
                name="treatment",
                prompt_file=treatment_prompt,
                description=treatment_description or f"Testing: {name}"
            ),
            start_date=datetime.now(),
            end_date=None,
            status=ExperimentStatus.ACTIVE
        )

        self._save_experiment(experiment)
        return experiment

    def assign_treatment(self, experiment_id: str, user_id: str) -> str:
        """
        Assign user to treatment arm (50/50 split).

        Uses deterministic hashing to ensure same user always gets same arm.

        Args:
            experiment_id: Experiment ID
            user_id: User identifier

        Returns:
            "control" or "treatment"
        """
        # Hash user_id + experiment_id for consistent assignment
        hash_input = f"{user_id}_{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest(), 16)

        # 50/50 split
        return "control" if hash_value % 2 == 0 else "treatment"

    def record_interaction(self, experiment_id: str, user_id: str,
                          success: bool, quality_score: float,
                          tokens_used: int, latency_ms: float):
        """
        Record an interaction result for the experiment.

        Args:
            experiment_id: Experiment ID
            user_id: User identifier
            success: Whether task completed successfully
            quality_score: Quality score (0-100)
            tokens_used: Token count
            latency_ms: Response latency in milliseconds
        """
        experiment = self._load_experiment(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.ACTIVE:
            return

        # Determine which arm
        arm_name = self.assign_treatment(experiment_id, user_id)
        arm = experiment.control if arm_name == "control" else experiment.treatment

        # Update metrics
        arm.interactions += 1
        if success:
            arm.successes += 1
        arm.total_quality_score += quality_score
        arm.total_tokens += tokens_used
        arm.total_latency_ms += latency_ms

        # Save updated experiment
        self._save_experiment(experiment)

    def analyze_experiment(self, experiment_id: str) -> Optional[StatisticalResult]:
        """
        Analyze experiment results for statistical significance.

        Args:
            experiment_id: Experiment ID

        Returns:
            StatisticalResult or None if not enough data
        """
        experiment = self._load_experiment(experiment_id)
        if not experiment:
            return None

        control = experiment.control
        treatment = experiment.treatment

        # Check minimum sample size
        if control.interactions < experiment.minimum_sample_size or \
           treatment.interactions < experiment.minimum_sample_size:
            return None

        # Perform two-proportion z-test on completion rate
        result = self.analyzer.two_proportion_z_test(
            control.successes, control.interactions,
            treatment.successes, treatment.interactions
        )

        return result

    def get_experiment_metrics(self, experiment_id: str) -> Tuple[Optional[ExperimentMetrics], Optional[ExperimentMetrics]]:
        """
        Get current metrics for both arms.

        Args:
            experiment_id: Experiment ID

        Returns:
            (control_metrics, treatment_metrics) or (None, None)
        """
        experiment = self._load_experiment(experiment_id)
        if not experiment:
            return None, None

        def calc_metrics(arm: TreatmentArm) -> ExperimentMetrics:
            if arm.interactions == 0:
                return ExperimentMetrics(0, 0, 0, 0, 0)

            return ExperimentMetrics(
                completion_rate=arm.successes / arm.interactions * 100,
                average_quality_score=arm.total_quality_score / arm.interactions,
                average_tokens=arm.total_tokens / arm.interactions,
                average_latency_ms=arm.total_latency_ms / arm.interactions,
                sample_size=arm.interactions
            )

        return calc_metrics(experiment.control), calc_metrics(experiment.treatment)

    def promote_winner(self, experiment_id: str) -> bool:
        """
        Promote winning treatment to production.

        Args:
            experiment_id: Experiment ID

        Returns:
            True if winner promoted, False otherwise
        """
        experiment = self._load_experiment(experiment_id)
        if not experiment:
            return False

        result = self.analyze_experiment(experiment_id)
        if not result or not result.is_significant:
            return False

        # Check if improvement meets success criteria (>15%)
        if result.effect_size > 15:
            experiment.winner = "treatment"
            experiment.status = ExperimentStatus.WINNER_PROMOTED
            experiment.end_date = datetime.now()

            # TODO: Actual file copying to promote treatment to production
            # For now, just mark as promoted
            self._save_experiment(experiment)
            return True

        return False

    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(name.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"exp_{timestamp}_{name_hash}"

    def _save_experiment(self, experiment: Experiment):
        """Save experiment to disk"""
        experiment_file = self.experiments_dir / f"{experiment.experiment_id}.json"

        experiment_data = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "hypothesis": experiment.hypothesis,
            "agent_name": experiment.agent_name,
            "control": asdict(experiment.control),
            "treatment": asdict(experiment.treatment),
            "start_date": experiment.start_date.isoformat(),
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "status": experiment.status.value,
            "minimum_sample_size": experiment.minimum_sample_size,
            "success_criteria": experiment.success_criteria,
            "winner": experiment.winner
        }

        # Convert Path objects to strings
        experiment_data["control"]["prompt_file"] = str(experiment_data["control"]["prompt_file"])
        experiment_data["treatment"]["prompt_file"] = str(experiment_data["treatment"]["prompt_file"])

        experiment_file.write_text(json.dumps(experiment_data, indent=2))

    def _load_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Load experiment from disk"""
        experiment_file = self.experiments_dir / f"{experiment_id}.json"

        if not experiment_file.exists():
            return None

        data = json.loads(experiment_file.read_text())

        # Reconstruct Treatment Arms
        control = TreatmentArm(
            name=data["control"]["name"],
            prompt_file=Path(data["control"]["prompt_file"]),
            description=data["control"]["description"],
            interactions=data["control"]["interactions"],
            successes=data["control"]["successes"],
            total_quality_score=data["control"]["total_quality_score"],
            total_tokens=data["control"]["total_tokens"],
            total_latency_ms=data["control"]["total_latency_ms"]
        )

        treatment = TreatmentArm(
            name=data["treatment"]["name"],
            prompt_file=Path(data["treatment"]["prompt_file"]),
            description=data["treatment"]["description"],
            interactions=data["treatment"]["interactions"],
            successes=data["treatment"]["successes"],
            total_quality_score=data["treatment"]["total_quality_score"],
            total_tokens=data["treatment"]["total_tokens"],
            total_latency_ms=data["treatment"]["total_latency_ms"]
        )

        return Experiment(
            experiment_id=data["experiment_id"],
            name=data["name"],
            hypothesis=data["hypothesis"],
            agent_name=data["agent_name"],
            control=control,
            treatment=treatment,
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]) if data["end_date"] else None,
            status=ExperimentStatus(data["status"]),
            minimum_sample_size=data["minimum_sample_size"],
            success_criteria=data["success_criteria"],
            winner=data.get("winner")
        )

    def list_active_experiments(self) -> List[Experiment]:
        """Get all active experiments"""
        experiments = []

        for experiment_file in self.experiments_dir.glob("exp_*.json"):
            experiment = self._load_experiment(experiment_file.stem)
            if experiment and experiment.status == ExperimentStatus.ACTIVE:
                experiments.append(experiment)

        return experiments


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="A/B Testing Framework")
    parser.add_argument("--list", action="store_true", help="List active experiments")

    args = parser.parse_args()

    framework = ABTestingFramework()

    if args.list:
        experiments = framework.list_active_experiments()
        print(f"\n{'='*60}")
        print(f"Active Experiments: {len(experiments)}")
        print(f"{'='*60}")

        for exp in experiments:
            print(f"\n{exp.name} ({exp.experiment_id})")
            print(f"  Agent: {exp.agent_name}")
            print(f"  Hypothesis: {exp.hypothesis}")
            print(f"  Started: {exp.start_date.strftime('%Y-%m-%d')}")

            control_metrics, treatment_metrics = framework.get_experiment_metrics(exp.experiment_id)
            if control_metrics and treatment_metrics:
                print(f"\n  Control:")
                print(f"    Sample size: {control_metrics.sample_size}")
                print(f"    Completion rate: {control_metrics.completion_rate:.1f}%")
                print(f"\n  Treatment:")
                print(f"    Sample size: {treatment_metrics.sample_size}")
                print(f"    Completion rate: {treatment_metrics.completion_rate:.1f}%")

                result = framework.analyze_experiment(exp.experiment_id)
                if result:
                    print(f"\n  Statistical Analysis:")
                    print(f"    Effect size: {result.effect_size:+.1f}%")
                    print(f"    P-value: {result.p_value:.4f}")
                    print(f"    Significant: {'✅ Yes' if result.is_significant else '❌ No'}")


if __name__ == "__main__":
    main()
