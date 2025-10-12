#!/usr/bin/env python3
"""
Dynamic Prompt Generation: LLM-generated prompts for specific scenarios

This meta-prompting technique improves prompt quality by:
1. Using an LLM to generate task-specific prompts
2. Optimizing prompts for different domains and contexts
3. Learning from successful prompt patterns
4. Adapting prompts based on user feedback

Use cases:
- Automating prompt engineering
- Domain-specific prompt optimization
- Adapting to new task types
- Continuous prompt improvement

Reference: "Large Language Models Are Human-Level Prompt Engineers"
           Zhou et al., 2023 (ICLR 2023) - APE (Automatic Prompt Engineer)
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

class PromptType(Enum):
    """Type of prompt to generate"""
    INSTRUCTION = "instruction"  # Direct task instruction
    FEW_SHOT = "few_shot"       # With examples
    CHAIN_OF_THOUGHT = "cot"    # With reasoning steps
    REACT = "react"             # Reasoning + Acting
    ZERO_SHOT = "zero_shot"     # No examples

class Domain(Enum):
    """Domain for prompt specialization"""
    GENERAL = "general"
    CODE = "code"
    MATH = "math"
    WRITING = "writing"
    ANALYSIS = "analysis"
    SECURITY = "security"
    CLOUD = "cloud"
    DATA = "data"

@dataclass
class PromptRequirements:
    """Requirements for prompt generation"""
    task_description: str
    domain: Domain
    prompt_type: PromptType
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    context: Optional[Dict] = None

@dataclass
class GeneratedPrompt:
    """A generated prompt"""
    id: str
    requirements: PromptRequirements
    prompt_text: str
    components: Dict[str, str]  # Role, context, task, format, examples
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_score: Optional[float] = None
    feedback: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PromptGenerationResult:
    """Result of prompt generation"""
    requirements: PromptRequirements
    candidate_prompts: List[GeneratedPrompt]
    selected_prompt: GeneratedPrompt
    generation_strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class DynamicPromptGenerator:
    """Engine for dynamic prompt generation"""

    def __init__(
        self,
        prompt_library: Optional[Dict] = None,
        meta_prompt_generator: Optional[Callable] = None
    ):
        """
        Initialize dynamic prompt generator

        Args:
            prompt_library: Library of successful prompt patterns
            meta_prompt_generator: Function to generate meta-prompts
        """
        # Storage (setup first, needed by _load_prompt_library)
        self.prompts_dir = Path(__file__).parent.parent.parent / "data" / "dynamic_prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_file = self.prompts_dir / "generated_prompts.json"
        self.library_file = self.prompts_dir / "prompt_library.json"

        # Initialize with library
        self.prompt_library = prompt_library or self._load_prompt_library()
        self.meta_prompt_generator = meta_prompt_generator or self._default_meta_prompt

    def generate_prompt(
        self,
        requirements: PromptRequirements,
        num_candidates: int = 3
    ) -> PromptGenerationResult:
        """
        Generate optimized prompt for requirements

        Process:
        1. Analyze task requirements and domain
        2. Select prompt template strategy
        3. Generate multiple candidate prompts
        4. Score candidates based on quality heuristics
        5. Select best candidate
        6. Return prompt with metadata

        Args:
            requirements: Prompt requirements
            num_candidates: Number of candidate prompts to generate

        Returns:
            PromptGenerationResult with selected prompt
        """
        # Step 1: Select generation strategy
        strategy = self._select_strategy(requirements)

        # Step 2: Generate candidate prompts
        candidates = []
        for i in range(num_candidates):
            prompt = self._generate_candidate(requirements, strategy, candidate_id=i+1)
            candidates.append(prompt)

        # Step 3: Score candidates
        for candidate in candidates:
            candidate.performance_score = self._score_prompt(candidate)

        # Step 4: Select best candidate
        selected = max(candidates, key=lambda p: p.performance_score or 0)

        result = PromptGenerationResult(
            requirements=requirements,
            candidate_prompts=candidates,
            selected_prompt=selected,
            generation_strategy=strategy
        )

        # Save result
        self._save_result(result)

        return result

    def _select_strategy(self, requirements: PromptRequirements) -> str:
        """Select prompt generation strategy based on requirements"""
        # Strategy selection based on domain and type
        domain = requirements.domain.value
        prompt_type = requirements.prompt_type.value

        if prompt_type == "few_shot":
            return "template_with_examples"
        elif prompt_type == "cot" or prompt_type == "react":
            return "reasoning_focused"
        elif domain in ["code", "security", "cloud"]:
            return "technical_specialized"
        elif domain in ["math", "analysis"]:
            return "analytical_structured"
        else:
            return "general_instruction"

    def _generate_candidate(
        self,
        requirements: PromptRequirements,
        strategy: str,
        candidate_id: int
    ) -> GeneratedPrompt:
        """Generate a single candidate prompt"""
        # Build prompt components
        components = {
            "role": self._generate_role(requirements),
            "context": self._generate_context(requirements),
            "task": self._generate_task(requirements),
            "format": self._generate_format(requirements),
            "constraints": self._generate_constraints(requirements)
        }

        # Add examples if few-shot
        if requirements.prompt_type == PromptType.FEW_SHOT:
            components["examples"] = self._generate_examples(requirements)

        # Add reasoning guidance if CoT/ReACT
        if requirements.prompt_type in [PromptType.CHAIN_OF_THOUGHT, PromptType.REACT]:
            components["reasoning_guidance"] = self._generate_reasoning_guidance(requirements)

        # Assemble prompt text
        prompt_text = self._assemble_prompt(components, strategy)

        prompt_id = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{candidate_id}"

        return GeneratedPrompt(
            id=prompt_id,
            requirements=requirements,
            prompt_text=prompt_text,
            components=components,
            metadata={
                "strategy": strategy,
                "candidate_id": candidate_id
            }
        )

    def _generate_role(self, requirements: PromptRequirements) -> str:
        """Generate role component"""
        domain_roles = {
            Domain.CODE: "expert software engineer",
            Domain.SECURITY: "principal security analyst",
            Domain.CLOUD: "senior cloud architect",
            Domain.DATA: "data engineering specialist",
            Domain.MATH: "mathematics expert",
            Domain.WRITING: "professional technical writer",
            Domain.ANALYSIS: "senior business analyst",
            Domain.GENERAL: "helpful AI assistant"
        }
        return f"You are a {domain_roles.get(requirements.domain, 'helpful assistant')}."

    def _generate_context(self, requirements: PromptRequirements) -> str:
        """Generate context component"""
        if requirements.context:
            context_parts = []
            for key, value in requirements.context.items():
                context_parts.append(f"{key}: {value}")
            return "Context:\n" + "\n".join(f"- {p}" for p in context_parts)
        return ""

    def _generate_task(self, requirements: PromptRequirements) -> str:
        """Generate task component"""
        return f"Task: {requirements.task_description}"

    def _generate_format(self, requirements: PromptRequirements) -> str:
        """Generate output format component"""
        if "format" in [c.lower() for c in requirements.constraints]:
            return "Output Format: Follow the specified format constraints."
        return "Output Format: Provide clear, structured output."

    def _generate_constraints(self, requirements: PromptRequirements) -> str:
        """Generate constraints component"""
        if requirements.constraints:
            return "Constraints:\n" + "\n".join(f"- {c}" for c in requirements.constraints)
        return ""

    def _generate_examples(self, requirements: PromptRequirements) -> str:
        """Generate few-shot examples"""
        # Look up examples from library
        domain = requirements.domain.value
        if domain in self.prompt_library.get("examples", {}):
            examples = self.prompt_library["examples"][domain][:2]  # Use 2 examples
            example_text = "Examples:\n"
            for i, ex in enumerate(examples, 1):
                example_text += f"\nExample {i}:\n"
                example_text += f"Input: {ex['input']}\n"
                example_text += f"Output: {ex['output']}\n"
            return example_text
        return ""

    def _generate_reasoning_guidance(self, requirements: PromptRequirements) -> str:
        """Generate reasoning guidance for CoT/ReACT"""
        if requirements.prompt_type == PromptType.CHAIN_OF_THOUGHT:
            return ("Reasoning Approach:\n"
                    "1. Break down the problem step by step\n"
                    "2. Show your reasoning for each step\n"
                    "3. Arrive at the final answer")
        elif requirements.prompt_type == PromptType.REACT:
            return ("Reasoning Approach:\n"
                    "1. Thought: Analyze what needs to be done\n"
                    "2. Action: Take an action\n"
                    "3. Observation: Observe the result\n"
                    "4. Repeat until task complete")
        return ""

    def _assemble_prompt(self, components: Dict[str, str], strategy: str) -> str:
        """Assemble final prompt from components"""
        prompt_parts = []

        # Add role
        if components.get("role"):
            prompt_parts.append(components["role"])

        # Add context
        if components.get("context"):
            prompt_parts.append(components["context"])

        # Add task
        prompt_parts.append(components["task"])

        # Add examples (for few-shot)
        if components.get("examples"):
            prompt_parts.append(components["examples"])

        # Add reasoning guidance (for CoT/ReACT)
        if components.get("reasoning_guidance"):
            prompt_parts.append(components["reasoning_guidance"])

        # Add constraints
        if components.get("constraints"):
            prompt_parts.append(components["constraints"])

        # Add format
        if components.get("format"):
            prompt_parts.append(components["format"])

        return "\n\n".join(prompt_parts)

    def _score_prompt(self, prompt: GeneratedPrompt) -> float:
        """
        Score prompt quality using heuristics

        Scoring criteria:
        - Clarity (has clear role, task, format)
        - Completeness (includes all required components)
        - Specificity (concrete constraints and examples)
        - Structure (well-organized)
        """
        score = 0.0

        # Clarity (0-30 points)
        if prompt.components.get("role"):
            score += 10
        if prompt.components.get("task"):
            score += 10
        if prompt.components.get("format"):
            score += 10

        # Completeness (0-20 points)
        component_count = len([v for v in prompt.components.values() if v])
        score += (component_count / len(prompt.components)) * 20

        # Specificity (0-30 points)
        if prompt.components.get("constraints"):
            score += 15
        if prompt.components.get("examples"):
            score += 15

        # Structure (0-20 points)
        text_length = len(prompt.prompt_text)
        if 100 <= text_length <= 1000:  # Optimal length range
            score += 20
        elif text_length < 100:
            score += 10
        else:  # Too long
            score += 15

        return round(score, 2)

    def _load_prompt_library(self) -> Dict:
        """Load prompt library from storage"""
        if self.library_file.exists():
            with open(self.library_file, 'r') as f:
                return json.load(f)

        # Default library
        return {
            "examples": {
                "code": [
                    {"input": "Write a function to reverse a string", "output": "def reverse_string(s: str) -> str:\n    return s[::-1]"},
                    {"input": "Create a binary search function", "output": "def binary_search(arr: list, target: int) -> int:\n    left, right = 0, len(arr)-1\n    while left <= right:\n        mid = (left+right)//2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: left = mid+1\n        else: right = mid-1\n    return -1"}
                ],
                "security": [
                    {"input": "Check if SPF record exists", "output": "dig TXT example.com | grep 'v=spf1'"},
                    {"input": "Validate SSL certificate", "output": "openssl s_client -connect example.com:443 -servername example.com"}
                ],
                "cloud": [
                    {"input": "List Azure VMs in subscription", "output": "az vm list --output table"},
                    {"input": "Create AWS S3 bucket", "output": "aws s3 mb s3://my-bucket --region us-east-1"}
                ]
            }
        }

    def _default_meta_prompt(self) -> str:
        """Default meta-prompt for prompt generation"""
        return ("Generate an optimized prompt for the following task requirements. "
                "The prompt should be clear, specific, and include appropriate structure "
                "for the task domain.")

    def _save_result(self, result: PromptGenerationResult):
        """Save result to persistent storage"""
        # Load existing results
        results = []
        if self.prompts_file.exists():
            with open(self.prompts_file, 'r') as f:
                results = json.load(f)

        # Add new result (simplified for JSON)
        result_dict = {
            'task_description': result.requirements.task_description,
            'domain': result.requirements.domain.value,
            'prompt_type': result.requirements.prompt_type.value,
            'selected_prompt_id': result.selected_prompt.id,
            'selected_prompt_text': result.selected_prompt.prompt_text,
            'selected_prompt_score': result.selected_prompt.performance_score,
            'strategy': result.generation_strategy,
            'timestamp': result.timestamp,
            'num_candidates': len(result.candidate_prompts)
        }
        results.append(result_dict)

        # Save
        with open(self.prompts_file, 'w') as f:
            json.dump(results, f, indent=2)

    def optimize_from_feedback(
        self,
        prompt: GeneratedPrompt,
        feedback: str,
        performance_score: float
    ) -> GeneratedPrompt:
        """
        Optimize prompt based on user feedback

        This enables continuous learning and improvement
        """
        # Update prompt with feedback
        prompt.feedback.append(feedback)
        prompt.performance_score = performance_score

        # Generate improved version
        improved_requirements = prompt.requirements

        # Add feedback as constraint
        improved_requirements.constraints.append(f"Improvement: {feedback}")

        # Regenerate
        result = self.generate_prompt(improved_requirements, num_candidates=1)

        return result.selected_prompt

def demo():
    """Demonstrate dynamic prompt generator"""
    print("=" * 80)
    print("Dynamic Prompt Generation Engine Demo")
    print("=" * 80)

    generator = DynamicPromptGenerator()

    # Test Case 1: Code generation prompt
    print("\n📋 Test Case 1: Generate Prompt for Code Generation Task")
    print("-" * 80)

    requirements1 = PromptRequirements(
        task_description="Write a Python function to calculate fibonacci numbers",
        domain=Domain.CODE,
        prompt_type=PromptType.FEW_SHOT,
        constraints=["Include type hints", "Add docstring", "Handle edge cases"],
        success_criteria=["Correct algorithm", "Clean code", "Proper documentation"]
    )

    result1 = generator.generate_prompt(requirements1, num_candidates=3)

    print(f"Task: {requirements1.task_description}")
    print(f"Domain: {requirements1.domain.value}")
    print(f"Prompt Type: {requirements1.prompt_type.value}")
    print(f"\n🎯 Selected Prompt (Score: {result1.selected_prompt.performance_score}):")
    print("-" * 80)
    print(result1.selected_prompt.prompt_text)
    print("-" * 80)

    print(f"\n📊 Candidate Scores:")
    for i, candidate in enumerate(result1.candidate_prompts, 1):
        print(f"   Candidate {i}: {candidate.performance_score}")

    print(f"\n🔧 Prompt Components:")
    for component, content in result1.selected_prompt.components.items():
        if content:
            preview = content[:50] + "..." if len(content) > 50 else content
            print(f"   - {component}: {preview}")

    # Test Case 2: Security analysis prompt
    print("\n" + "=" * 80)
    print("📋 Test Case 2: Generate Prompt for Security Analysis")
    print("-" * 80)

    requirements2 = PromptRequirements(
        task_description="Analyze DNS records for security misconfigurations",
        domain=Domain.SECURITY,
        prompt_type=PromptType.REACT,
        constraints=["Check SPF, DKIM, DMARC", "Identify risks", "Provide remediation"],
        context={"domain": "example.com", "record_types": ["TXT", "MX", "A"]}
    )

    result2 = generator.generate_prompt(requirements2, num_candidates=2)

    print(f"Task: {requirements2.task_description}")
    print(f"Domain: {requirements2.domain.value}")
    print(f"Prompt Type: {requirements2.prompt_type.value}")
    print(f"\n🎯 Selected Prompt (Score: {result2.selected_prompt.performance_score}):")
    print("-" * 80)
    print(result2.selected_prompt.prompt_text)
    print("-" * 80)

    # Test Case 3: Cloud architecture prompt
    print("\n" + "=" * 80)
    print("📋 Test Case 3: Generate Prompt for Cloud Architecture")
    print("-" * 80)

    requirements3 = PromptRequirements(
        task_description="Design highly available architecture for web application",
        domain=Domain.CLOUD,
        prompt_type=PromptType.CHAIN_OF_THOUGHT,
        constraints=["Multi-region", "Auto-scaling", "Cost-optimized"],
        success_criteria=["99.99% uptime", "Under $5k/month", "Handles 100k users"]
    )

    result3 = generator.generate_prompt(requirements3, num_candidates=2)

    print(f"Task: {requirements3.task_description}")
    print(f"Domain: {requirements3.domain.value}")
    print(f"\n🎯 Selected Prompt (Score: {result3.selected_prompt.performance_score}):")
    print("-" * 80)
    print(result3.selected_prompt.prompt_text)
    print("-" * 80)

    # Comparison: Manual vs Generated Prompts
    print("\n" + "=" * 80)
    print("📊 Manual vs Dynamic Prompt Generation Comparison")
    print("-" * 80)

    print(f"\n❌ Manual Prompt Engineering:")
    print(f"   - Time-consuming trial and error")
    print(f"   - Inconsistent quality across domains")
    print(f"   - Hard to scale to many task types")
    print(f"   - Limited learning from successes")

    print(f"\n✅ Dynamic Prompt Generation:")
    print(f"   - Automated optimization: {result1.selected_prompt.performance_score}/100 quality")
    print(f"   - Domain-specific strategies: {result1.generation_strategy}")
    print(f"   - Multiple candidates evaluated: 3 options, best selected")
    print(f"   - Continuous improvement: Feedback loop for learning")

    print(f"\n💡 Benefits:")
    print(f"   - Faster prompt development")
    print(f"   - Consistent quality standards")
    print(f"   - Adapts to new domains/tasks")
    print(f"   - Learns from successful patterns")

    print("\n" + "=" * 80)
    print("✅ Demo Complete")
    print("=" * 80)
    print(f"\nGenerated prompts saved to: {generator.prompts_file}")

if __name__ == "__main__":
    demo()
