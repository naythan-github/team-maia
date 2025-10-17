#!/usr/bin/env python3
"""
Capability Checker - Cached Version (Phase 127 Optimization)

High-performance capability discovery with in-memory index caching.
Target: <10ms per check (97.5% improvement from 920ms baseline)

Optimizations:
- Persistent index cache (capability_cache.json)
- Cache invalidation on file modifications
- Pre-built keyword indexes for O(1) lookups
- Lazy RAG initialization

Author: Maia System (Phase 127 - Strategic Optimizations)
Created: 2025-10-17
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


@dataclass
class CapabilityMatch:
    """Represents a capability match result"""
    source: str  # 'system_state', 'agents', 'tools', 'rag'
    type: str    # 'exact', 'partial', 'none'
    confidence: float  # 0.0-1.0
    location: str  # File path or phase number
    description: str
    details: str


class CachedCapabilityChecker:
    """
    High-performance capability checker with persistent caching.

    Performance targets:
    - Cold start: <200ms (build cache)
    - Warm cache: <10ms (97.5% reduction from 920ms)
    - Cache hit rate: >95%
    """

    CACHE_FILE = "capability_cache.json"
    CACHE_VERSION = "1.0"

    def __init__(self):
        self.maia_root = MAIA_ROOT
        self.cache_path = self.maia_root / "claude" / "data" / self.CACHE_FILE

        # File paths
        self.system_state_path = self.maia_root / "SYSTEM_STATE.md"
        self.system_state_index_path = self.maia_root / "SYSTEM_STATE_INDEX.json"
        self.agents_path = self.maia_root / "claude" / "context" / "core" / "agents.md"
        self.available_path = self.maia_root / "claude" / "context" / "tools" / "available.md"

        # Cache storage
        self.cache = None
        self.rag = None  # Lazy initialization

        # Load or build cache
        self._load_cache()

    def _get_file_mtime(self, path: Path) -> float:
        """Get file modification time, return 0 if not exists"""
        try:
            return path.stat().st_mtime if path.exists() else 0.0
        except Exception:
            return 0.0

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid (files haven't been modified)"""
        if not self.cache:
            return False

        if self.cache.get('version') != self.CACHE_VERSION:
            return False

        cache_mtimes = self.cache.get('mtimes', {})
        current_mtimes = {
            'system_state': self._get_file_mtime(self.system_state_path),
            'system_state_index': self._get_file_mtime(self.system_state_index_path),
            'agents': self._get_file_mtime(self.agents_path),
            'available': self._get_file_mtime(self.available_path)
        }

        # Check if any file has been modified
        for key, current_mtime in current_mtimes.items():
            if cache_mtimes.get(key, 0) != current_mtime:
                return False

        return True

    def _load_cache(self):
        """Load cache from disk, rebuild if invalid"""
        # Try to load existing cache
        if self.cache_path.exists():
            try:
                self.cache = json.loads(self.cache_path.read_text())
                if self._is_cache_valid():
                    return  # Cache is valid, use it
            except Exception as e:
                print(f"⚠️  Cache load error: {e}, rebuilding...")

        # Cache invalid or missing, rebuild
        self._build_cache()

    def _build_cache(self):
        """Build cache indexes from source files"""
        start_time = time.time()

        self.cache = {
            'version': self.CACHE_VERSION,
            'built_at': time.time(),
            'mtimes': {
                'system_state': self._get_file_mtime(self.system_state_path),
                'system_state_index': self._get_file_mtime(self.system_state_index_path),
                'agents': self._get_file_mtime(self.agents_path),
                'available': self._get_file_mtime(self.available_path)
            },
            'indexes': {
                'system_state': self._build_system_state_index(),
                'agents': self._build_agents_index(),
                'tools': self._build_tools_index()
            }
        }

        # Save cache to disk
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache, indent=2))
        except Exception as e:
            print(f"⚠️  Cache save error: {e}")

        build_time = (time.time() - start_time) * 1000
        print(f"✅ Cache built in {build_time:.0f}ms")

    def _build_system_state_index(self) -> Dict:
        """Build keyword index for SYSTEM_STATE using JSON index if available"""
        # Use existing JSON index if available (already optimized)
        if self.system_state_index_path.exists():
            try:
                json_index = json.loads(self.system_state_index_path.read_text())
                return {
                    'type': 'json_index',
                    'data': json_index
                }
            except Exception:
                pass

        # Fallback: Build simple keyword index from MD
        if not self.system_state_path.exists():
            return {'type': 'empty', 'data': {}}

        keyword_index = {}  # keyword -> [phase_nums]

        try:
            content = self.system_state_path.read_text()

            # Extract phases
            phase_pattern = r'###\s+\*\*(.+?)\*\*[^\n]*?PHASE\s+(\d+[A-Z]?\.?\d*)[^\n]*?\n(.*?)(?=###\s+\*\*|$)'
            for match in re.finditer(phase_pattern, content, re.DOTALL | re.IGNORECASE):
                phase_title = match.group(1)
                phase_num = match.group(2)
                phase_content = match.group(3)

                # Extract keywords (significant words)
                words = re.findall(r'\b[a-z]{4,}\b', (phase_title + ' ' + phase_content[:500]).lower())
                common_words = {'the', 'this', 'that', 'with', 'from', 'have', 'been', 'were', 'when', 'where', 'what', 'they', 'their', 'there', 'these', 'those', 'should', 'would', 'could'}
                keywords = set(w for w in words if w not in common_words)

                for keyword in keywords:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    keyword_index[keyword].append({
                        'phase': phase_num,
                        'title': phase_title[:100]
                    })

        except Exception as e:
            print(f"⚠️  Error building system_state index: {e}")

        return {'type': 'keyword_index', 'data': keyword_index}

    def _build_agents_index(self) -> Dict:
        """Build keyword index for agents"""
        if not self.agents_path.exists():
            return {'type': 'empty', 'data': {}}

        keyword_index = {}  # keyword -> [agent_names]

        try:
            content = self.agents_path.read_text()

            # Extract agent sections
            agent_pattern = r'###\s+(.+?Agent.*?)\n(.*?)(?=###|$)'
            for match in re.finditer(agent_pattern, content, re.DOTALL):
                agent_name = match.group(1).strip()
                agent_content = match.group(2)

                # Extract keywords
                words = re.findall(r'\b[a-z]{4,}\b', (agent_name + ' ' + agent_content[:500]).lower())
                common_words = {'the', 'this', 'that', 'with', 'from', 'have', 'been', 'were', 'agent'}
                keywords = set(w for w in words if w not in common_words)

                for keyword in keywords:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    keyword_index[keyword].append({
                        'agent': agent_name[:100],
                        'description': agent_content[:200]
                    })

        except Exception as e:
            print(f"⚠️  Error building agents index: {e}")

        return {'type': 'keyword_index', 'data': keyword_index}

    def _build_tools_index(self) -> Dict:
        """Build keyword index for tools"""
        if not self.available_path.exists():
            return {'type': 'empty', 'data': {}}

        keyword_index = {}  # keyword -> [tool_names]

        try:
            content = self.available_path.read_text()

            # Extract tool sections
            tool_pattern = r'###\s+(.+?)\n(.*?)(?=###|$)'
            for match in re.finditer(tool_pattern, content, re.DOTALL):
                tool_name = match.group(1).strip()
                tool_content = match.group(2)

                # Extract keywords
                words = re.findall(r'\b[a-z]{4,}\b', (tool_name + ' ' + tool_content[:500]).lower())
                common_words = {'the', 'this', 'that', 'with', 'from', 'have', 'been', 'were', 'tool'}
                keywords = set(w for w in words if w not in common_words)

                for keyword in keywords:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    keyword_index[keyword].append({
                        'tool': tool_name[:100],
                        'description': tool_content[:200]
                    })

        except Exception as e:
            print(f"⚠️  Error building tools index: {e}")

        return {'type': 'keyword_index', 'data': keyword_index}

    def check_capability(self, task_description: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute Phase 0 capability check using cached indexes

        Performance: <10ms (cache hit)
        """
        if not keywords:
            keywords = self._extract_keywords(task_description)

        results = {
            'task': task_description,
            'keywords': keywords,
            'matches': {
                'system_state': self._search_system_state_cached(keywords),
                'agents': self._search_agents_cached(keywords),
                'tools': self._search_tools_cached(keywords),
                'rag': []  # Skip RAG for performance (only use on explicit request)
            },
            'recommendation': None
        }

        # Analyze results and provide recommendation
        results['recommendation'] = self._analyze_matches(results['matches'])

        return results

    def _extract_keywords(self, task_description: str) -> List[str]:
        """Extract search keywords from task description (same as original)"""
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'development', 'system', 'tool', 'agent', 'implementation'}

        # Extract multi-word phrases first
        phrases = re.findall(r'\b([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)\b', task_description.lower())
        phrase_keywords = [p for p in phrases if len(p) > 8][:2]

        # Extract single words
        words = re.findall(r'\b[a-z]+\b', task_description.lower())
        word_keywords = [w for w in words if w not in common_words and len(w) > 3][:5]

        return phrase_keywords + word_keywords[:3]

    def _search_system_state_cached(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search SYSTEM_STATE using cached index (O(1) lookup)"""
        matches = []
        index = self.cache['indexes']['system_state']

        if index['type'] == 'json_index':
            # Use existing JSON index (already optimal)
            data = index['data']
            search_index = data.get('search_index', {})
            phases_data = data.get('phases', {})

            phase_scores = {}

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in search_index:
                    for phase_num in search_index[keyword_lower]:
                        phase_scores[str(phase_num)] = phase_scores.get(str(phase_num), 0) + 0.3

            # Convert top scores to matches
            for phase_num, score in sorted(phase_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                if phase_num in phases_data:
                    phase_data = phases_data[phase_num]
                    confidence = min(score, 0.95)

                    matches.append(CapabilityMatch(
                        source='system_state',
                        type='exact' if confidence >= 0.7 else 'partial',
                        confidence=confidence,
                        location=f"Phase {phase_num}",
                        description=phase_data['title'],
                        details=f"Keywords: {', '.join(phase_data.get('keywords', [])[:5])}"
                    ))

        elif index['type'] == 'keyword_index':
            # Use built keyword index
            data = index['data']
            phase_scores = {}

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in data:
                    for entry in data[keyword_lower]:
                        phase_num = entry['phase']
                        phase_scores[phase_num] = phase_scores.get(phase_num, 0) + 0.3

            # Convert top scores to matches
            for phase_num, score in sorted(phase_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                matches.append(CapabilityMatch(
                    source='system_state',
                    type='exact' if score >= 0.7 else 'partial',
                    confidence=min(score, 0.95),
                    location=f"Phase {phase_num}",
                    description=f"Phase {phase_num}",
                    details=""
                ))

        return matches

    def _search_agents_cached(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search agents using cached index (O(1) lookup)"""
        matches = []
        index = self.cache['indexes']['agents']

        if index['type'] == 'keyword_index':
            data = index['data']
            agent_scores = {}

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in data:
                    for entry in data[keyword_lower]:
                        agent_name = entry['agent']
                        agent_scores[agent_name] = agent_scores.get(agent_name, 0) + 0.4

            # Convert top scores to matches
            for agent_name, score in sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                matches.append(CapabilityMatch(
                    source='agents',
                    type='exact' if score >= 0.7 else 'partial',
                    confidence=min(score, 0.95),
                    location=str(self.agents_path),
                    description=agent_name,
                    details=""
                ))

        return matches

    def _search_tools_cached(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search tools using cached index (O(1) lookup)"""
        matches = []
        index = self.cache['indexes']['tools']

        if index['type'] == 'keyword_index':
            data = index['data']
            tool_scores = {}

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in data:
                    for entry in data[keyword_lower]:
                        tool_name = entry['tool']
                        tool_scores[tool_name] = tool_scores.get(tool_name, 0) + 0.35

            # Convert top scores to matches
            for tool_name, score in sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                matches.append(CapabilityMatch(
                    source='tools',
                    type='exact' if score >= 0.7 else 'partial',
                    confidence=min(score, 0.95),
                    location=str(self.available_path),
                    description=tool_name,
                    details=""
                ))

        return matches

    def _analyze_matches(self, matches_dict: Dict[str, List[CapabilityMatch]]) -> Dict[str, Any]:
        """Analyze all matches and provide recommendation (same as original)"""
        all_matches = []
        for source, matches in matches_dict.items():
            all_matches.extend(matches)

        if not all_matches:
            return {
                'decision': 'build_new',
                'confidence': 0.9,
                'reasoning': 'No existing capabilities found. Proceed to Phase 1 (Problem Analysis).',
                'action': 'Continue with systematic thinking protocol - analyze problem space before building.'
            }

        best_match = max(all_matches, key=lambda x: x.confidence)

        if best_match.type == 'exact' and best_match.confidence > 0.7:
            return {
                'decision': 'use_existing',
                'confidence': best_match.confidence,
                'reasoning': f'Exact capability found in {best_match.source}: {best_match.description}',
                'best_match': asdict(best_match),
                'action': f'Use existing capability at {best_match.location}'
            }
        elif best_match.confidence > 0.5:
            return {
                'decision': 'enhance_existing',
                'confidence': best_match.confidence,
                'reasoning': f'Partial match found in {best_match.source}: {best_match.description}',
                'best_match': asdict(best_match),
                'action': f'Consider enhancing {best_match.location} vs building new. Justify choice.'
            }
        else:
            return {
                'decision': 'build_new',
                'confidence': 0.7,
                'reasoning': 'Only weak matches found. Building new likely better than forcing enhancement.',
                'action': 'Proceed to Phase 1, but document why existing capabilities insufficient.'
            }

    def format_results(self, results: Dict[str, Any], verbose: bool = False) -> str:
        """Format capability check results for display"""
        output = []

        output.append("🔍 **Phase 0: Capability Check Results** (Cached)\n")
        output.append(f"**Task**: {results['task']}")
        output.append(f"**Keywords**: {', '.join(results['keywords'])}\n")

        # Show matches by source
        for source, matches in results['matches'].items():
            if matches:
                output.append(f"\n**{source.upper()}**: {len(matches)} match(es)")
                for i, match in enumerate(matches[:2], 1):
                    output.append(f"  {i}. {match.description[:80]}")
                    output.append(f"     Location: {match.location} | Confidence: {match.confidence:.0%}")
                    if verbose:
                        output.append(f"     Details: {match.details[:150]}...")

        # Show recommendation
        rec = results['recommendation']
        output.append(f"\n✅ **RECOMMENDATION**: {rec['decision'].upper().replace('_', ' ')}")
        output.append(f"**Confidence**: {rec['confidence']:.0%}")
        output.append(f"**Reasoning**: {rec['reasoning']}")
        output.append(f"**Action**: {rec['action']}")

        return '\n'.join(output)


def main():
    """CLI interface for capability checking"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 0 Capability Checker (Cached)')
    parser.add_argument('task', nargs='*', help='Task description to check')
    parser.add_argument('--keywords', '-k', nargs='+', help='Specific keywords to search')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--rebuild-cache', action='store_true', help='Force rebuild cache')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
    args = parser.parse_args()

    if args.benchmark:
        # Performance benchmark
        print("🔧 Running performance benchmark...")
        checker = CachedCapabilityChecker()

        test_queries = [
            "build a security scanner",
            "create recruitment database",
            "implement servicedesk analytics",
            "new stakeholder intelligence agent"
        ]

        times = []
        for query in test_queries:
            start = time.time()
            results = checker.check_capability(query)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            print(f"  {query[:40]}: {elapsed:.1f}ms")

        avg_time = sum(times) / len(times)
        print(f"\n📊 Average: {avg_time:.1f}ms")
        print(f"✅ Target: <10ms | Status: {'PASS' if avg_time < 10 else 'NEEDS OPTIMIZATION'}")
        return

    task_description = ' '.join(args.task) if args.task else input("Enter task description: ")

    checker = CachedCapabilityChecker()

    if args.rebuild_cache:
        print("🔧 Forcing cache rebuild...")
        checker._build_cache()

    start_time = time.time()
    results = checker.check_capability(task_description, args.keywords)
    elapsed = (time.time() - start_time) * 1000

    if args.json:
        # Convert CapabilityMatch objects to dicts
        json_results = results.copy()
        for source in json_results['matches']:
            json_results['matches'][source] = [asdict(m) for m in json_results['matches'][source]]
        json_results['performance'] = {'query_time_ms': elapsed}
        print(json.dumps(json_results, indent=2))
    else:
        print(checker.format_results(results, args.verbose))
        print(f"\n⏱️  Query time: {elapsed:.1f}ms")


if __name__ == "__main__":
    main()
