#!/usr/bin/env python3
"""
Unit Tests for Parallel Agent Executor

Phase 3 Agentic AI Enhancement: Parallel Execution Pattern
Tests concurrent agent execution and result merging.
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestParallelExecutor(unittest.TestCase):
    """Test ParallelExecutor class"""

    def setUp(self):
        """Create executor instance"""
        from parallel_executor import ParallelExecutor
        self.executor = ParallelExecutor(max_workers=3)

    def test_initialization(self):
        """Test executor initializes correctly"""
        self.assertIsNotNone(self.executor)
        self.assertEqual(self.executor.max_workers, 3)

    def test_identify_parallel_tasks(self):
        """Test identifying independent subtasks"""
        query = "Research pricing on LinkedIn, Seek, and Indeed"

        tasks = self.executor.identify_parallel_tasks(query)

        self.assertGreater(len(tasks), 1)
        # Should identify multiple data sources
        self.assertTrue(any('linkedin' in t.lower() or 'seek' in t.lower() for t in tasks))

    def test_identify_sequential_tasks(self):
        """Test identifying dependent tasks that can't parallelize"""
        query = "Create a file, then read it, then delete it"

        tasks = self.executor.identify_parallel_tasks(query)

        # Sequential tasks should not be split
        self.assertEqual(len(tasks), 1)

    def test_execute_single_task(self):
        """Test executing single task"""
        def simple_task():
            return "result"

        result = self.executor.execute_tasks([simple_task])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['result'], "result")
        self.assertTrue(result[0]['success'])

    def test_execute_parallel_tasks(self):
        """Test executing multiple tasks in parallel"""
        results = []

        def task1():
            time.sleep(0.1)
            return "task1"

        def task2():
            time.sleep(0.1)
            return "task2"

        def task3():
            time.sleep(0.1)
            return "task3"

        start = time.time()
        results = self.executor.execute_tasks([task1, task2, task3])
        elapsed = time.time() - start

        # Should complete faster than sequential (0.3s)
        self.assertLess(elapsed, 0.25)
        self.assertEqual(len(results), 3)

    def test_handle_task_failure(self):
        """Test handling failed tasks gracefully"""
        def failing_task():
            raise ValueError("Task failed")

        def passing_task():
            return "success"

        results = self.executor.execute_tasks([failing_task, passing_task])

        self.assertEqual(len(results), 2)
        # One failed, one passed
        failed = [r for r in results if not r['success']]
        passed = [r for r in results if r['success']]
        self.assertEqual(len(failed), 1)
        self.assertEqual(len(passed), 1)

    def test_merge_results(self):
        """Test merging parallel results"""
        results = [
            {'success': True, 'result': 'Data from source A', 'source': 'A'},
            {'success': True, 'result': 'Data from source B', 'source': 'B'},
            {'success': False, 'error': 'Failed', 'source': 'C'}
        ]

        merged = self.executor.merge_results(results)

        self.assertIn('combined', merged)
        self.assertIn('sources', merged)
        self.assertEqual(len(merged['sources']), 2)  # Only successful

    def test_timeout_handling(self):
        """Test task timeout handling"""
        from parallel_executor import ParallelExecutor as PE

        def slow_task():
            time.sleep(5)
            return "slow"

        executor = PE(max_workers=2, task_timeout=0.5)
        results = executor.execute_tasks([slow_task])

        # Should timeout or fail
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['success'])

    def test_dependency_detection(self):
        """Test detecting task dependencies"""
        tasks = [
            "read file.txt",
            "write file.txt",
            "delete file.txt"
        ]

        deps = self.executor.detect_dependencies(tasks)

        # Should detect that tasks depend on same file
        self.assertTrue(deps['has_dependencies'])

    def test_no_dependency_detection(self):
        """Test detecting independent tasks"""
        tasks = [
            "search LinkedIn",
            "search Seek",
            "search Indeed"
        ]

        deps = self.executor.detect_dependencies(tasks)

        self.assertFalse(deps['has_dependencies'])

    def test_parallel_agent_calls(self):
        """Test parallelizing agent calls"""
        mock_agents = {
            'agent1': Mock(return_value={'result': 'A'}),
            'agent2': Mock(return_value={'result': 'B'})
        }

        with patch.object(self.executor, '_call_agent', side_effect=lambda a, q: mock_agents[a]()):
            results = self.executor.execute_agent_calls(
                agents=['agent1', 'agent2'],
                query="test query"
            )

        self.assertEqual(len(results), 2)

    def test_result_prioritization(self):
        """Test prioritizing results from parallel execution"""
        results = [
            {'success': True, 'result': 'Good result', 'quality': 0.9},
            {'success': True, 'result': 'Better result', 'quality': 0.95},
            {'success': True, 'result': 'OK result', 'quality': 0.7}
        ]

        prioritized = self.executor.prioritize_results(results)

        # Highest quality should be first
        self.assertEqual(prioritized[0]['quality'], 0.95)


class TestAsyncExecution(unittest.TestCase):
    """Test async execution capabilities"""

    def test_async_task_execution(self):
        """Test async task execution"""
        from parallel_executor import ParallelExecutor

        executor = ParallelExecutor()

        async def async_task():
            await asyncio.sleep(0.1)
            return "async result"

        results = executor.execute_async_tasks([async_task])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['result'], "async result")


if __name__ == "__main__":
    print("Parallel Executor Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
