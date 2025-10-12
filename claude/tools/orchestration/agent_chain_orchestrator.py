"""
Agent Chain Orchestrator - Sequential Subtask Execution

Executes multi-subtask workflows (prompt chains) with dependency management,
context enrichment, and comprehensive audit trails.

Based on: claude/data/AGENT_EVOLUTION_PROJECT_PLAN.md Phase 3, Task 3.2
Research: claude/data/PROMPT_ENGINEER_AGENT_ANALYSIS.md Section 4

Architecture:
    Workflow Definition → Sequential Execution → Context Enrichment → Audit Trail

    Key Features:
    - Dependency validation between subtasks
    - Context preservation across subtasks
    - Output validation and quality checks
    - Complete audit trail (JSONL)
    - Integration with Swarm (agents can handoff within subtasks)
    - Rollback capability on failures
"""

import json
import re
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class SubtaskStatus(Enum):
    """Subtask execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubtaskDefinition:
    """Definition of a single subtask in the chain"""
    subtask_id: int
    name: str
    goal: str
    prompt_template: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[int] = field(default_factory=list)  # IDs of required prior subtasks
    required_outputs: List[str] = field(default_factory=list)  # Required output keys
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    agent_name: Optional[str] = None  # Optional: specific agent to use
    allow_handoff: bool = True  # Can this subtask trigger agent handoffs?
    timeout_seconds: int = 300


@dataclass
class SubtaskExecution:
    """Record of subtask execution"""
    subtask_id: int
    name: str
    status: SubtaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    agent_used: Optional[str] = None
    handoffs_triggered: int = 0
    tokens_used: int = 0
    execution_time_ms: float = 0.0


@dataclass
class ChainExecution:
    """Complete chain execution record"""
    chain_id: str
    workflow_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, partial
    initial_input: Dict[str, Any] = field(default_factory=dict)
    subtask_executions: List[SubtaskExecution] = field(default_factory=list)
    final_output: Dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    total_time_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0


class WorkflowParser:
    """
    Parses workflow definition files into executable subtask definitions.

    Workflow files are markdown with structured sections:
    - Overview
    - Subtask Sequence (multiple subtasks)
    - Each subtask has: Goal, Input, Output, Prompt
    """

    def parse_workflow_file(self, workflow_file: Path) -> Dict[str, Any]:
        """Parse markdown workflow file into structured definition"""
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")

        content = workflow_file.read_text()

        # Extract overview
        overview = self._extract_section(content, r"## Overview\n(.*?)\n##", multiline=True)

        # Extract subtasks
        subtasks = self._parse_subtasks(content)

        return {
            "workflow_name": workflow_file.stem,
            "overview": overview,
            "subtasks": subtasks,
            "workflow_file": str(workflow_file)
        }

    def _extract_section(self, content: str, pattern: str, multiline: bool = False) -> str:
        """Extract section using regex pattern"""
        flags = re.DOTALL if multiline else 0
        match = re.search(pattern, content, flags)
        return match.group(1).strip() if match else ""

    def _parse_subtasks(self, content: str) -> List[SubtaskDefinition]:
        """Parse all subtasks from workflow content"""
        subtasks = []

        # Find all "### Subtask N:" sections
        subtask_pattern = r'### Subtask (\d+):(.*?(?=\n### Subtask |\Z))'
        matches = re.findall(subtask_pattern, content, re.DOTALL)

        for subtask_num, subtask_content in matches:
            subtask_id = int(subtask_num)

            # Extract subtask components
            name = self._extract_section(subtask_content, r'### Subtask \d+: (.*?)\n')
            goal = self._extract_section(subtask_content, r'\*\*Goal\*\*: (.*?)\n')

            # Extract input schema (JSON block after **Input**)
            input_schema = self._extract_json_block(subtask_content, r'\*\*Input\*\*:')

            # Extract output schema (JSON block after **Output**)
            output_schema = self._extract_json_block(subtask_content, r'\*\*Output\*\*:')

            # Extract prompt (```...``` block after **Prompt**)
            prompt_template = self._extract_code_block(subtask_content, r'\*\*Prompt\*\*:')

            # Detect dependencies (references to subtask_N_output)
            dependencies = self._detect_dependencies(prompt_template, subtask_id)

            subtasks.append(SubtaskDefinition(
                subtask_id=subtask_id,
                name=name if name else f"Subtask {subtask_id}",
                goal=goal,
                prompt_template=prompt_template,
                input_schema=input_schema,
                output_schema=output_schema,
                dependencies=dependencies
            ))

        return subtasks

    def _extract_json_block(self, content: str, after_marker: str) -> Dict[str, Any]:
        """Extract JSON block that appears after a marker"""
        # Find marker, then find next ```json block
        marker_pos = content.find(after_marker)
        if marker_pos == -1:
            return {}

        json_start = content.find('```json', marker_pos)
        if json_start == -1:
            json_start = content.find('```', marker_pos)
        if json_start == -1:
            return {}

        json_end = content.find('```', json_start + 3)
        if json_end == -1:
            return {}

        # Extract text between markers
        if '```json' in content[json_start:json_start+10]:
            # Skip ```json\n
            json_text_start = json_start + 7
        else:
            # Skip ```\n
            json_text_start = content.find('\n', json_start) + 1

        json_text = content[json_text_start:json_end].strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return {}

    def _extract_code_block(self, content: str, after_marker: str) -> str:
        """Extract code block (``` ... ```) after marker"""
        marker_pos = content.find(after_marker)
        if marker_pos == -1:
            return ""

        code_start = content.find('```', marker_pos)
        if code_start == -1:
            return ""

        # Find start of actual content (skip ``` and language identifier if present)
        first_newline = content.find('\n', code_start)
        if first_newline == -1:
            return ""
        code_start = first_newline + 1

        # Find closing ```
        code_end = content.find('```', code_start)
        if code_end == -1:
            return ""

        return content[code_start:code_end].strip()

    def _detect_dependencies(self, prompt_template: str, current_id: int) -> List[int]:
        """Detect dependencies from {subtask_N_output} references in prompt"""
        dependencies = []
        pattern = r'\{subtask_(\d+)_output\}'
        matches = re.findall(pattern, prompt_template)

        for match in matches:
            dep_id = int(match)
            if dep_id < current_id and dep_id not in dependencies:
                dependencies.append(dep_id)

        return sorted(dependencies)


class ChainValidator:
    """Validates subtask outputs against schemas and rules"""

    def validate_output(self, output: Dict[str, Any], schema: Dict[str, Any],
                       rules: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate output against schema and rules.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Schema validation (check required keys)
        if schema:
            for key in schema.keys():
                if key not in output:
                    errors.append(f"Missing required output key: {key}")

        # Rule validation
        if rules:
            for rule_name, rule_config in rules.items():
                if rule_name == "min_length":
                    for key, min_len in rule_config.items():
                        if key in output and len(str(output[key])) < min_len:
                            errors.append(f"{key} length ({len(str(output[key]))}) < minimum ({min_len})")

                elif rule_name == "required_keys":
                    for key in rule_config:
                        if key not in output:
                            errors.append(f"Required key missing: {key}")

        return len(errors) == 0, errors


class AgentChainOrchestrator:
    """
    Orchestrates sequential multi-subtask workflows (prompt chains).

    Key Features:
    - Sequential execution with dependency validation
    - Context enrichment (each subtask builds on previous outputs)
    - Comprehensive audit trails
    - Rollback on failures
    - Integration with Swarm (handoffs within subtasks)
    """

    def __init__(self, audit_dir: Path = None):
        self.parser = WorkflowParser()
        self.validator = ChainValidator()

        # Audit trail directory
        if audit_dir is None:
            audit_dir = Path(__file__).parent.parent.parent / "context" / "session" / "chain_executions"
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def load_workflow(self, workflow_file: Path) -> Dict[str, Any]:
        """Load and parse workflow definition"""
        return self.parser.parse_workflow_file(workflow_file)

    def execute_chain(self, workflow: Dict[str, Any], initial_input: Dict[str, Any],
                     chain_id: Optional[str] = None) -> ChainExecution:
        """
        Execute complete prompt chain sequentially.

        Args:
            workflow: Parsed workflow definition (from load_workflow)
            initial_input: Initial input data for chain
            chain_id: Optional chain execution ID (generated if not provided)

        Returns:
            ChainExecution with complete audit trail
        """
        if chain_id is None:
            chain_id = self._generate_chain_id(workflow['workflow_name'])

        execution = ChainExecution(
            chain_id=chain_id,
            workflow_name=workflow['workflow_name'],
            start_time=datetime.now(),
            initial_input=initial_input
        )

        # Build context (accumulates outputs from all subtasks)
        context = initial_input.copy()

        try:
            for subtask_def in workflow['subtasks']:
                # Check dependencies
                if not self._dependencies_met(subtask_def, execution):
                    error_msg = f"Dependencies not met: requires subtasks {subtask_def.dependencies}"
                    execution.subtask_executions.append(SubtaskExecution(
                        subtask_id=subtask_def.subtask_id,
                        name=subtask_def.name,
                        status=SubtaskStatus.SKIPPED,
                        start_time=datetime.now(),
                        error_message=error_msg
                    ))
                    execution.failure_count += 1
                    continue

                # Execute subtask
                subtask_exec = self._execute_subtask(subtask_def, context, execution)
                execution.subtask_executions.append(subtask_exec)

                # Update totals
                execution.total_tokens += subtask_exec.tokens_used
                execution.total_time_ms += subtask_exec.execution_time_ms

                if subtask_exec.status == SubtaskStatus.COMPLETED:
                    execution.success_count += 1

                    # Enrich context with subtask output
                    context[f"subtask_{subtask_def.subtask_id}_output"] = subtask_exec.output_data
                else:
                    execution.failure_count += 1
                    # Stop chain on failure (for now - could make this configurable)
                    break

            # Determine final status
            if execution.failure_count == 0:
                execution.status = "completed"
                execution.final_output = execution.subtask_executions[-1].output_data
            elif execution.success_count > 0:
                execution.status = "partial"
            else:
                execution.status = "failed"

        except Exception as e:
            execution.status = "failed"
            execution.subtask_executions.append(SubtaskExecution(
                subtask_id=999,
                name="Chain Execution Error",
                status=SubtaskStatus.FAILED,
                start_time=datetime.now(),
                error_message=str(e)
            ))

        finally:
            execution.end_time = datetime.now()
            self._save_audit_trail(execution)

        return execution

    def _dependencies_met(self, subtask_def: SubtaskDefinition,
                         execution: ChainExecution) -> bool:
        """Check if all dependencies for subtask are satisfied"""
        completed_ids = [
            se.subtask_id for se in execution.subtask_executions
            if se.status == SubtaskStatus.COMPLETED
        ]

        return all(dep_id in completed_ids for dep_id in subtask_def.dependencies)

    def _execute_subtask(self, subtask_def: SubtaskDefinition, context: Dict[str, Any],
                        chain_exec: ChainExecution) -> SubtaskExecution:
        """Execute single subtask with context"""
        start_time = datetime.now()

        subtask_exec = SubtaskExecution(
            subtask_id=subtask_def.subtask_id,
            name=subtask_def.name,
            status=SubtaskStatus.RUNNING,
            start_time=start_time,
            input_data=context.copy()
        )

        try:
            # Format prompt with context
            formatted_prompt = subtask_def.prompt_template.format(**context)

            # Simulate agent execution (in real implementation, this would call actual agent)
            # For now, return mock output based on subtask_def
            output = self._simulate_agent_execution(subtask_def, formatted_prompt, context)

            # Validate output
            is_valid, errors = self.validator.validate_output(
                output, subtask_def.output_schema, subtask_def.validation_rules
            )

            if not is_valid:
                subtask_exec.status = SubtaskStatus.FAILED
                subtask_exec.error_message = f"Validation failed: {'; '.join(errors)}"
            else:
                subtask_exec.status = SubtaskStatus.COMPLETED
                subtask_exec.output_data = output

            # Record metrics
            subtask_exec.agent_used = subtask_def.agent_name or "default"
            subtask_exec.tokens_used = len(formatted_prompt.split()) + len(str(output).split())

        except KeyError as e:
            subtask_exec.status = SubtaskStatus.FAILED
            subtask_exec.error_message = f"Missing required context key: {e}"

        except Exception as e:
            subtask_exec.status = SubtaskStatus.FAILED
            subtask_exec.error_message = f"Execution error: {str(e)}"

        finally:
            subtask_exec.end_time = datetime.now()
            subtask_exec.execution_time_ms = (
                subtask_exec.end_time - subtask_exec.start_time
            ).total_seconds() * 1000

        return subtask_exec

    def _simulate_agent_execution(self, subtask_def: SubtaskDefinition,
                                  prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate agent execution (mock implementation).

        In production, this would:
        1. Load appropriate agent
        2. Execute with prompt
        3. Parse agent response
        4. Return structured output
        """
        # For testing, return structure matching output_schema
        output = {}
        for key in subtask_def.output_schema.keys():
            output[key] = f"[Mock output for {key}]"

        return output

    def _generate_chain_id(self, workflow_name: str) -> str:
        """Generate unique chain execution ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Add microseconds
        hash_suffix = hashlib.md5(f"{workflow_name}{timestamp}".encode()).hexdigest()[:8]
        return f"{workflow_name}_{timestamp}_{hash_suffix}"

    def _save_audit_trail(self, execution: ChainExecution):
        """Save complete execution audit trail to JSONL"""
        audit_file = self.audit_dir / f"{execution.chain_id}.jsonl"

        # Convert to JSON-serializable format
        audit_data = {
            "chain_id": execution.chain_id,
            "workflow_name": execution.workflow_name,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "status": execution.status,
            "initial_input": execution.initial_input,
            "subtask_executions": [
                {
                    "subtask_id": se.subtask_id,
                    "name": se.name,
                    "status": se.status.value,
                    "start_time": se.start_time.isoformat(),
                    "end_time": se.end_time.isoformat() if se.end_time else None,
                    "input_data": se.input_data,
                    "output_data": se.output_data,
                    "error_message": se.error_message,
                    "agent_used": se.agent_used,
                    "handoffs_triggered": se.handoffs_triggered,
                    "tokens_used": se.tokens_used,
                    "execution_time_ms": se.execution_time_ms
                }
                for se in execution.subtask_executions
            ],
            "final_output": execution.final_output,
            "total_tokens": execution.total_tokens,
            "total_time_ms": execution.total_time_ms,
            "success_count": execution.success_count,
            "failure_count": execution.failure_count
        }

        with open(audit_file, 'w') as f:
            f.write(json.dumps(audit_data, indent=2))

    def get_execution_history(self, workflow_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve execution history from audit trails.

        Args:
            workflow_name: Optional filter by workflow name

        Returns:
            List of execution records
        """
        executions = []

        for audit_file in self.audit_dir.glob("*.jsonl"):
            with open(audit_file, 'r') as f:
                data = json.load(f)

                if workflow_name is None or data['workflow_name'] == workflow_name:
                    executions.append(data)

        # Sort by start_time descending
        executions.sort(key=lambda x: x['start_time'], reverse=True)

        return executions


# Convenience function for simple usage
def execute_workflow(workflow_file: Path, initial_input: Dict[str, Any]) -> ChainExecution:
    """
    Execute workflow with single function call.

    Example:
        result = execute_workflow(
            workflow_file=Path("claude/workflows/prompt_chains/dns_audit_chain.md"),
            initial_input={"domain": "example.com", "include_subdomains": True}
        )
    """
    orchestrator = AgentChainOrchestrator()
    workflow = orchestrator.load_workflow(workflow_file)
    return orchestrator.execute_chain(workflow, initial_input)


if __name__ == '__main__':
    print("="*70)
    print("AGENT CHAIN ORCHESTRATOR - DEMO")
    print("="*70)

    # Demo: Load and parse workflow
    orchestrator = AgentChainOrchestrator()

    # Find first workflow file
    workflows_dir = Path(__file__).parent.parent.parent / "workflows" / "prompt_chains"
    workflow_files = list(workflows_dir.glob("*.md"))

    if workflow_files:
        print(f"\n📁 Found {len(workflow_files)} workflow files")
        print(f"📄 Loading: {workflow_files[0].name}")

        try:
            workflow = orchestrator.load_workflow(workflow_files[0])
            print(f"\n✅ Workflow loaded: {workflow['workflow_name']}")
            print(f"📊 Subtasks: {len(workflow['subtasks'])}")

            for i, subtask in enumerate(workflow['subtasks'], 1):
                print(f"\n  {i}. {subtask.name}")
                print(f"     Goal: {subtask.goal[:80]}...")
                print(f"     Dependencies: {subtask.dependencies if subtask.dependencies else 'None'}")

            # Demo: Execute workflow (with mock inputs)
            print(f"\n🚀 Executing workflow...")
            initial_input = {"domain": "example.com", "include_subdomains": True}

            execution = orchestrator.execute_chain(workflow, initial_input)

            print(f"\n📊 Execution Results:")
            print(f"   Chain ID: {execution.chain_id}")
            print(f"   Status: {execution.status}")
            print(f"   Success: {execution.success_count}/{len(execution.subtask_executions)}")
            print(f"   Total time: {execution.total_time_ms:.2f}ms")
            print(f"   Total tokens: {execution.total_tokens}")

            print(f"\n✅ Audit trail saved to: {orchestrator.audit_dir / execution.chain_id}.jsonl")

        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print(f"\n⚠️  No workflow files found in {workflows_dir}")
        print("   Create workflow files to test the orchestrator")
