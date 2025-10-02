#!/usr/bin/env python3

"""
Workflow Optimizer - Phase 3 Token Optimization
Eliminates redundant AI calls in multi-step workflows while preserving intelligence
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
from datetime import datetime
import sqlite3

class WorkflowOptimizer:
    """
    Optimizes multi-step workflows by:
    1. Detecting redundant analysis steps
    2. Reusing intermediate results
    3. Batching similar operations
    4. Creating intelligent processing pipelines
    """

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or "get_path_manager().get_path('backup') / 'cache/workflow_cache'")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "workflow_cache.db"
        self._init_database()

        # Workflow patterns that can be optimized
        self.optimization_patterns = [
            'batch_processing',
            'pipeline_deduplication',
            'result_reuse',
            'intelligent_routing'
        ]

    def _init_database(self):
        """Initialize workflow optimization database"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS workflow_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_hash TEXT UNIQUE NOT NULL,
                workflow_type TEXT NOT NULL,
                input_signature TEXT NOT NULL,
                output_result TEXT,
                processing_time REAL,
                tokens_used INTEGER,
                tokens_saved INTEGER DEFAULT 0,
                step_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reuse_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS workflow_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_signature TEXT NOT NULL,
                optimization_strategy TEXT NOT NULL,
                average_savings INTEGER,
                success_rate REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS batch_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                batch_signature TEXT NOT NULL,
                batch_size INTEGER,
                potential_savings INTEGER,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.close()

    def analyze_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a workflow for optimization opportunities
        """
        workflow_signature = self._generate_workflow_signature(workflow_steps)

        optimization_opportunities = {
            'batch_processing': [],
            'redundant_steps': [],
            'cacheable_results': [],
            'pipeline_shortcuts': [],
            'estimated_savings': 0
        }

        # Detect batch processing opportunities
        batch_ops = self._detect_batch_opportunities(workflow_steps)
        optimization_opportunities['batch_processing'] = batch_ops

        # Detect redundant steps
        redundant = self._detect_redundant_steps(workflow_steps)
        optimization_opportunities['redundant_steps'] = redundant

        # Detect cacheable intermediate results
        cacheable = self._detect_cacheable_steps(workflow_steps)
        optimization_opportunities['cacheable_results'] = cacheable

        # Calculate potential savings
        total_savings = sum([
            len(batch_ops) * 2000,  # Batch processing savings
            len(redundant) * 1500,  # Redundant step elimination
            len(cacheable) * 1000,  # Caching savings
        ])
        optimization_opportunities['estimated_savings'] = total_savings

        return optimization_opportunities

    def _generate_workflow_signature(self, workflow_steps: List[Dict[str, Any]]) -> str:
        """Generate unique signature for workflow pattern"""
        # Extract essential workflow structure
        signature_data = []
        for step in workflow_steps:
            step_sig = {
                'type': step.get('type', 'unknown'),
                'operation': step.get('operation', 'unknown'),
                'complexity': step.get('complexity', 'medium')
            }
            signature_data.append(step_sig)

        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]

    def _detect_batch_opportunities(self, workflow_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect opportunities for batching similar operations"""
        batch_opportunities = []
        operation_groups = {}

        # Group similar operations
        for i, step in enumerate(workflow_steps):
            operation = step.get('operation', 'unknown')
            if operation not in operation_groups:
                operation_groups[operation] = []
            operation_groups[operation].append((i, step))

        # Identify batchable groups
        for operation, steps in operation_groups.items():
            if len(steps) >= 2 and operation in ['code_review', 'data_analysis', 'pattern_detection']:
                batch_opportunities.append({
                    'operation': operation,
                    'step_count': len(steps),
                    'step_indices': [s[0] for s in steps],
                    'potential_savings': len(steps) * 800,  # Batching efficiency
                    'batch_strategy': 'parallel_processing'
                })

        return batch_opportunities

    def _detect_redundant_steps(self, workflow_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect redundant analysis steps"""
        redundant_steps = []
        seen_analyses = {}

        for i, step in enumerate(workflow_steps):
            # Create content signature for step
            content_sig = self._get_step_content_signature(step)
            analysis_type = step.get('type', 'unknown')

            signature_key = f"{analysis_type}:{content_sig}"

            if signature_key in seen_analyses:
                redundant_steps.append({
                    'step_index': i,
                    'duplicate_of': seen_analyses[signature_key],
                    'analysis_type': analysis_type,
                    'potential_savings': step.get('estimated_tokens', 1500)
                })
            else:
                seen_analyses[signature_key] = i

        return redundant_steps

    def _detect_cacheable_steps(self, workflow_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect steps with cacheable intermediate results"""
        cacheable_steps = []

        for i, step in enumerate(workflow_steps):
            # Steps that produce reusable intermediate results
            if step.get('type') in ['data_processing', 'code_analysis', 'security_scan']:
                complexity = step.get('complexity', 'medium')
                if complexity in ['low', 'medium']:  # Don't cache complex, context-dependent results
                    cacheable_steps.append({
                        'step_index': i,
                        'cache_key': self._get_step_content_signature(step),
                        'estimated_reuse_value': 1200,
                        'cache_duration': '7d' if complexity == 'low' else '3d'
                    })

        return cacheable_steps

    def _get_step_content_signature(self, step: Dict[str, Any]) -> str:
        """Generate content signature for a workflow step"""
        content = step.get('input_data', '') + step.get('parameters', '')
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def optimize_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply optimizations to a workflow
        """
        optimized_workflow = {
            'original_steps': len(workflow_steps),
            'optimized_steps': [],
            'eliminated_steps': [],
            'batch_operations': [],
            'cached_results': [],
            'total_savings': 0
        }

        # Analyze for opportunities
        opportunities = self.analyze_workflow(workflow_steps)

        # Apply optimizations
        remaining_steps = workflow_steps.copy()

        # 1. Eliminate redundant steps
        for redundant in opportunities['redundant_steps']:
            step_idx = redundant['step_index']
            if step_idx < len(remaining_steps):
                eliminated_step = remaining_steps.pop(step_idx)
                optimized_workflow['eliminated_steps'].append({
                    'original_index': step_idx,
                    'step': eliminated_step,
                    'reason': 'redundant_analysis',
                    'savings': redundant['potential_savings']
                })
                optimized_workflow['total_savings'] += redundant['potential_savings']

        # 2. Create batch operations
        for batch_op in opportunities['batch_processing']:
            batch_steps = []
            for step_idx in sorted(batch_op['step_indices'], reverse=True):
                if step_idx < len(remaining_steps):
                    batch_steps.append(remaining_steps.pop(step_idx))

            if batch_steps:
                optimized_workflow['batch_operations'].append({
                    'operation': batch_op['operation'],
                    'batched_steps': batch_steps,
                    'savings': batch_op['potential_savings']
                })
                optimized_workflow['total_savings'] += batch_op['potential_savings']

        # 3. Mark cacheable steps
        for cacheable in opportunities['cacheable_results']:
            if cacheable['step_index'] < len(workflow_steps):
                optimized_workflow['cached_results'].append({
                    'step': workflow_steps[cacheable['step_index']],
                    'cache_key': cacheable['cache_key'],
                    'potential_reuse_value': cacheable['estimated_reuse_value']
                })

        optimized_workflow['optimized_steps'] = remaining_steps
        optimized_workflow['optimization_ratio'] = optimized_workflow['total_savings'] / max(len(workflow_steps) * 2000, 1)

        return optimized_workflow

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get workflow optimization statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT
                workflow_type,
                COUNT(*) as workflow_count,
                SUM(tokens_saved) as total_tokens_saved,
                AVG(tokens_saved) as avg_tokens_saved,
                SUM(reuse_count) as total_reuses
            FROM workflow_cache
            GROUP BY workflow_type
        """)

        stats = {}
        total_savings = 0

        for row in cursor.fetchall():
            workflow_type = row['workflow_type']
            stats[workflow_type] = dict(row)
            total_savings += row['total_tokens_saved']

        stats['overall'] = {
            'total_tokens_saved': total_savings,
            'unique_workflows': len(stats)
        }

        conn.close()
        return stats


def main():
    """Demo workflow optimization"""
    optimizer = WorkflowOptimizer()

    print("🔄 Testing Workflow Optimizer")
    print("=" * 50)

    # Example workflow with optimization opportunities
    sample_workflow = [
        {
            'type': 'code_review',
            'operation': 'syntax_check',
            'input_data': 'def hello(): print("hello")',
            'complexity': 'low',
            'estimated_tokens': 2000
        },
        {
            'type': 'code_review',
            'operation': 'style_check',
            'input_data': 'def hello(): print("hello")',  # Same content
            'complexity': 'low',
            'estimated_tokens': 1800
        },
        {
            'type': 'data_analysis',
            'operation': 'stats_calculation',
            'input_data': '{"values": [1,2,3,4,5]}',
            'complexity': 'medium',
            'estimated_tokens': 2200
        },
        {
            'type': 'code_review',
            'operation': 'security_check',
            'input_data': 'def process_data(x): return x * 2',
            'complexity': 'low',
            'estimated_tokens': 1900
        }
    ]

    # Analyze workflow
    opportunities = optimizer.analyze_workflow(sample_workflow)
    print(f"Detected optimization opportunities:")
    print(f"  - Batch processing: {len(opportunities['batch_processing'])} opportunities")
    print(f"  - Redundant steps: {len(opportunities['redundant_steps'])} steps")
    print(f"  - Cacheable results: {len(opportunities['cacheable_results'])} results")
    print(f"  - Estimated savings: {opportunities['estimated_savings']:,} tokens")

    # Optimize workflow
    optimized = optimizer.optimize_workflow(sample_workflow)
    print(f"\nOptimization results:")
    print(f"  - Original steps: {optimized['original_steps']}")
    print(f"  - Optimized steps: {len(optimized['optimized_steps'])}")
    print(f"  - Eliminated steps: {len(optimized['eliminated_steps'])}")
    print(f"  - Total savings: {optimized['total_savings']:,} tokens")
    print(f"  - Optimization ratio: {optimized['optimization_ratio']:.2%}")

if __name__ == "__main__":
    main()
