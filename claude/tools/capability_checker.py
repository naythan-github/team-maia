#!/usr/bin/env python3
"""
Capability Checker - Phase 0 Automated Capability Discovery

Systematically searches existing Maia capabilities to prevent duplicate work.
Implements Phase 0 of the Systematic Thinking Protocol.

Author: Maia System
Created: 2025-10-03 (Phase 85 automation completion)
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.system_state_rag_ollama import SystemStateRAGOllama


@dataclass
class CapabilityMatch:
    """Represents a capability match result"""
    source: str  # 'system_state', 'agents', 'tools', 'rag'
    type: str    # 'exact', 'partial', 'none'
    confidence: float  # 0.0-1.0
    location: str  # File path or phase number
    description: str
    details: str


class CapabilityChecker:
    """Automated Phase 0 capability discovery system"""

    def __init__(self):
        self.maia_root = MAIA_ROOT
        self.system_state_path = self.maia_root / "SYSTEM_STATE.md"
        self.agents_path = self.maia_root / "claude" / "context" / "core" / "agents.md"
        self.available_path = self.maia_root / "claude" / "context" / "tools" / "available.md"

        # Initialize RAG for historical search
        try:
            self.rag = SystemStateRAGOllama()
        except Exception as e:
            print(f"⚠️  RAG not available: {e}")
            self.rag = None

    def check_capability(self, task_description: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute Phase 0 capability check across all sources

        Args:
            task_description: Natural language description of the task
            keywords: Optional list of specific keywords to search

        Returns:
            Dictionary with matches from all sources and recommendation
        """
        if not keywords:
            keywords = self._extract_keywords(task_description)

        results = {
            'task': task_description,
            'keywords': keywords,
            'matches': {
                'system_state': self._search_system_state(keywords),
                'agents': self._search_agents(keywords),
                'tools': self._search_available(keywords),
                'rag': self._search_rag(task_description) if self.rag else []
            },
            'recommendation': None
        }

        # Analyze results and provide recommendation
        results['recommendation'] = self._analyze_matches(results['matches'])

        return results

    def _extract_keywords(self, task_description: str) -> List[str]:
        """Extract search keywords from task description"""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'development', 'system', 'tool', 'agent', 'implementation'}

        # Extract multi-word phrases first (more specific)
        phrases = re.findall(r'\b([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)\b', task_description.lower())
        phrase_keywords = [p for p in phrases if len(p) > 8][:2]  # Top 2 phrases

        # Extract single words
        words = re.findall(r'\b[a-z]+\b', task_description.lower())
        word_keywords = [w for w in words if w not in common_words and len(w) > 3][:5]

        # Combine: phrases first (higher priority), then words
        return phrase_keywords + word_keywords[:3]

    def _search_system_state(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search SYSTEM_STATE.md for matching capabilities"""
        matches = []

        if not self.system_state_path.exists():
            return matches

        with open(self.system_state_path, 'r') as f:
            content = f.read()

        # Search for each keyword in recent phases
        for keyword in keywords:
            pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            if pattern.search(content):
                # Find phase context
                phase_pattern = r'###\s+\*\*(.+?)\*\*[^\n]*?PHASE\s+(\d+[A-Z]?\.?\d*)[^\n]*?\n(.*?)(?=###\s+\*\*|$)'
                for match in re.finditer(phase_pattern, content, re.DOTALL | re.IGNORECASE):
                    phase_title = match.group(1)
                    phase_num = match.group(2)
                    phase_content = match.group(3)

                    if pattern.search(phase_content):
                        # Calculate confidence based on keyword density
                        keyword_count = len(pattern.findall(phase_content))
                        confidence = min(0.3 + (keyword_count * 0.1), 0.9)

                        matches.append(CapabilityMatch(
                            source='system_state',
                            type='partial' if confidence < 0.7 else 'exact',
                            confidence=confidence,
                            location=f"Phase {phase_num}",
                            description=phase_title[:100],
                            details=phase_content[:300]
                        ))

        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:3]

    def _search_agents(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search agents.md for matching agent capabilities"""
        matches = []

        if not self.agents_path.exists():
            return matches

        with open(self.agents_path, 'r') as f:
            content = f.read()

        # Search for agent sections
        for keyword in keywords:
            pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            if pattern.search(content):
                # Find agent context
                agent_pattern = r'###\s+(.+?Agent.*?)\n(.*?)(?=###|$)'
                for match in re.finditer(agent_pattern, content, re.DOTALL):
                    agent_name = match.group(1)
                    agent_content = match.group(2)

                    if pattern.search(agent_content):
                        keyword_count = len(pattern.findall(agent_content))
                        confidence = min(0.4 + (keyword_count * 0.15), 0.95)

                        matches.append(CapabilityMatch(
                            source='agents',
                            type='partial' if confidence < 0.7 else 'exact',
                            confidence=confidence,
                            location=str(self.agents_path),
                            description=agent_name[:100],
                            details=agent_content[:300]
                        ))

        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:3]

    def _search_available(self, keywords: List[str]) -> List[CapabilityMatch]:
        """Search available.md for matching tool capabilities"""
        matches = []

        if not self.available_path.exists():
            return matches

        with open(self.available_path, 'r') as f:
            content = f.read()

        for keyword in keywords:
            pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            if pattern.search(content):
                # Find tool context
                tool_pattern = r'###\s+(.+?)\n(.*?)(?=###|$)'
                for match in re.finditer(tool_pattern, content, re.DOTALL):
                    tool_name = match.group(1)
                    tool_content = match.group(2)

                    if pattern.search(tool_content):
                        keyword_count = len(pattern.findall(tool_content))
                        confidence = min(0.35 + (keyword_count * 0.12), 0.9)

                        matches.append(CapabilityMatch(
                            source='tools',
                            type='partial' if confidence < 0.7 else 'exact',
                            confidence=confidence,
                            location=str(self.available_path),
                            description=tool_name[:100],
                            details=tool_content[:300]
                        ))

        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:3]

    def _search_rag(self, query: str) -> List[CapabilityMatch]:
        """Search archived phases via RAG semantic search"""
        matches = []

        if not self.rag:
            return matches

        try:
            results = self.rag.semantic_search(query, n_results=3)

            for r in results:
                if r['relevance'] > 0.2:  # 20% relevance threshold
                    matches.append(CapabilityMatch(
                        source='rag',
                        type='exact' if r['relevance'] > 0.5 else 'partial',
                        confidence=r['relevance'],
                        location=f"Phase {r['phase']} (archived)",
                        description=r['title'][:100],
                        details=r['preview'][:300]
                    ))
        except Exception as e:
            print(f"⚠️  RAG search error: {e}")

        return matches

    def _analyze_matches(self, matches_dict: Dict[str, List[CapabilityMatch]]) -> Dict[str, Any]:
        """Analyze all matches and provide recommendation"""
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

        # Find highest confidence match
        best_match = max(all_matches, key=lambda x: x.confidence)

        if best_match.type == 'exact' and best_match.confidence > 0.7:
            return {
                'decision': 'use_existing',
                'confidence': best_match.confidence,
                'reasoning': f'Exact capability found in {best_match.source}: {best_match.description}',
                'best_match': best_match,
                'action': f'Use existing capability at {best_match.location}'
            }
        elif best_match.confidence > 0.5:
            return {
                'decision': 'enhance_existing',
                'confidence': best_match.confidence,
                'reasoning': f'Partial match found in {best_match.source}: {best_match.description}',
                'best_match': best_match,
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

        output.append("🔍 **Phase 0: Capability Check Results**\n")
        output.append(f"**Task**: {results['task']}")
        output.append(f"**Keywords**: {', '.join(results['keywords'])}\n")

        # Show matches by source
        for source, matches in results['matches'].items():
            if matches:
                output.append(f"\n**{source.upper()}**: {len(matches)} match(es)")
                for i, match in enumerate(matches[:2], 1):  # Show top 2
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

    parser = argparse.ArgumentParser(description='Phase 0 Capability Checker')
    parser.add_argument('task', nargs='*', help='Task description to check')
    parser.add_argument('--keywords', '-k', nargs='+', help='Specific keywords to search')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    task_description = ' '.join(args.task) if args.task else input("Enter task description: ")

    checker = CapabilityChecker()
    results = checker.check_capability(task_description, args.keywords)

    if args.json:
        # Convert CapabilityMatch objects to dicts for JSON serialization
        json_results = results.copy()
        for source in json_results['matches']:
            json_results['matches'][source] = [
                {
                    'source': m.source,
                    'type': m.type,
                    'confidence': m.confidence,
                    'location': m.location,
                    'description': m.description,
                    'details': m.details
                } for m in json_results['matches'][source]
            ]
        print(json.dumps(json_results, indent=2))
    else:
        print(checker.format_results(results, args.verbose))


if __name__ == "__main__":
    main()
