#!/usr/bin/env python3
"""
Parallel Agent Executor - Agentic AI Enhancement Phase 3

Implements parallel execution pattern:
  CURRENT: Agent A -> Agent B -> Agent C (sequential)
  AGENTIC: [Agent A, Agent B, Agent C] -> Merge (parallel)

Key Features:
- Identify independent subtasks automatically
- Execute in parallel where no dependencies
- Merge results intelligently
- Handle failures gracefully

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 3)
"""

import asyncio
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskResult:
    """Result from a parallel task execution"""
    task_id: str
    success: bool
    result: Any = None
    error: str = None
    duration: float = 0.0
    source: str = None


class ParallelExecutor:
    """
    Parallel Task Executor with Smart Dependency Detection.

    Executes independent tasks concurrently and merges results.
    """

    # Patterns indicating parallel-able sources
    PARALLEL_SOURCES = [
        r'\b(linkedin|seek|indeed|glassdoor)\b',
        r'\b(aws|azure|gcp|google cloud)\b',
        r'\b(github|gitlab|bitbucket)\b',
        r'\b(slack|teams|discord)\b',
    ]

    # Patterns indicating sequential dependencies
    SEQUENTIAL_PATTERNS = [
        r'\bthen\b',
        r'\bafter\b',
        r'\bbefore\b',
        r'\bfirst\b.*\bnext\b',
        r'\bstep \d+\b.*\bstep \d+\b',
    ]

    # File operation patterns (indicate dependencies)
    FILE_OPS = ['read', 'write', 'create', 'delete', 'update', 'modify']

    def __init__(self, max_workers: int = 5, task_timeout: float = 30.0):
        """
        Initialize Parallel Executor.

        Args:
            max_workers: Maximum concurrent workers
            task_timeout: Timeout per task in seconds
        """
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self._executor = None

    def identify_parallel_tasks(self, query: str) -> List[str]:
        """
        Identify independent subtasks from a query.

        Args:
            query: User query

        Returns:
            List of independent task descriptions
        """
        query_lower = query.lower()

        # Check for sequential indicators
        for pattern in self.SEQUENTIAL_PATTERNS:
            if re.search(pattern, query_lower):
                return [query]  # Keep as single sequential task

        # Look for parallel sources
        found_sources = []
        for pattern in self.PARALLEL_SOURCES:
            matches = re.findall(pattern, query_lower)
            found_sources.extend(matches)

        if len(found_sources) > 1:
            # Split into parallel tasks per source
            tasks = []
            for source in set(found_sources):
                task = f"Search/query {source}: {query}"
                tasks.append(task)
            return tasks

        # Check for comma/and separated items
        if ' and ' in query_lower or ',' in query:
            parts = re.split(r',\s*|\s+and\s+', query)
            if len(parts) > 1 and all(len(p.strip()) > 3 for p in parts):
                return [p.strip() for p in parts if p.strip()]

        return [query]

    def detect_dependencies(self, tasks: List[str]) -> Dict[str, Any]:
        """
        Detect dependencies between tasks.

        Args:
            tasks: List of task descriptions

        Returns:
            Dict with dependency information
        """
        # Check for shared resources
        resources = []
        for task in tasks:
            # Extract file paths
            paths = re.findall(r'[/\w]+\.\w+', task)
            resources.extend(paths)

            # Extract variable/resource names
            for op in self.FILE_OPS:
                if op in task.lower():
                    # Likely has file dependencies
                    return {'has_dependencies': True, 'reason': f'Contains {op} operation'}

        # Check for duplicate resources
        if len(resources) != len(set(resources)):
            return {'has_dependencies': True, 'reason': 'Shared resources detected'}

        return {'has_dependencies': False, 'resources': list(set(resources))}

    def execute_tasks(self, tasks: List[Callable]) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of callable tasks

        Returns:
            List of result dicts
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for i, task in enumerate(tasks):
                future = executor.submit(self._execute_single, task, f"task_{i}")
                futures[future] = i

            for future in futures:
                try:
                    result = future.result(timeout=self.task_timeout)
                    results.append(result)
                except FuturesTimeoutError:
                    results.append({
                        'success': False,
                        'error': 'Task timeout',
                        'task_id': f"task_{futures[future]}"
                    })
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'task_id': f"task_{futures[future]}"
                    })

        return results

    def _execute_single(self, task: Callable, task_id: str) -> Dict[str, Any]:
        """Execute a single task with timing"""
        start = time.time()
        try:
            result = task()
            duration = time.time() - start
            return {
                'success': True,
                'result': result,
                'task_id': task_id,
                'duration': duration
            }
        except Exception as e:
            duration = time.time() - start
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id,
                'duration': duration
            }

    def execute_async_tasks(self, tasks: List[Callable]) -> List[Dict[str, Any]]:
        """
        Execute async tasks.

        Args:
            tasks: List of async callables

        Returns:
            List of result dicts
        """
        async def run_all():
            results = []
            for i, task in enumerate(tasks):
                try:
                    start = time.time()
                    result = await task()
                    duration = time.time() - start
                    results.append({
                        'success': True,
                        'result': result,
                        'task_id': f"async_{i}",
                        'duration': duration
                    })
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'task_id': f"async_{i}"
                    })
            return results

        return asyncio.run(run_all())

    def execute_agent_calls(
        self,
        agents: List[str],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple agent calls in parallel.

        Args:
            agents: List of agent names
            query: Query to send to each

        Returns:
            List of agent responses
        """
        tasks = [
            lambda a=agent: self._call_agent(a, query)
            for agent in agents
        ]
        return self.execute_tasks(tasks)

    def _call_agent(self, agent: str, query: str) -> Dict[str, Any]:
        """Call a single agent (stub for integration)"""
        # This would integrate with actual agent system
        return {
            'agent': agent,
            'query': query,
            'result': f"Response from {agent}"
        }

    def merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from parallel execution.

        Args:
            results: List of task results

        Returns:
            Merged result dict
        """
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]

        combined_results = []
        sources = []

        for r in successful:
            if 'result' in r:
                combined_results.append(r['result'])
            if 'source' in r:
                sources.append(r['source'])

        return {
            'combined': combined_results,
            'sources': sources,
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'failures': [{'task': f.get('task_id'), 'error': f.get('error')} for f in failed]
        }

    def prioritize_results(
        self,
        results: List[Dict[str, Any]],
        key: str = 'quality'
    ) -> List[Dict[str, Any]]:
        """
        Prioritize results by quality or other metric.

        Args:
            results: List of results
            key: Key to sort by

        Returns:
            Sorted results (best first)
        """
        successful = [r for r in results if r.get('success', False)]
        return sorted(
            successful,
            key=lambda x: x.get(key, 0),
            reverse=True
        )


def main():
    """CLI for parallel executor"""
    import argparse

    parser = argparse.ArgumentParser(description="Parallel Executor")
    parser.add_argument('--query', '-q', help='Query to analyze for parallelization')
    parser.add_argument('--workers', '-w', type=int, default=5, help='Max workers')

    args = parser.parse_args()

    executor = ParallelExecutor(max_workers=args.workers)

    if args.query:
        tasks = executor.identify_parallel_tasks(args.query)
        deps = executor.detect_dependencies(tasks)

        print(f"\nQuery: {args.query}")
        print(f"Parallel tasks identified: {len(tasks)}")
        for t in tasks:
            print(f"  - {t}")
        print(f"Has dependencies: {deps['has_dependencies']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
