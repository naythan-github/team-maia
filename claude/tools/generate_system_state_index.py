#!/usr/bin/env python3
"""
Generate SYSTEM_STATE_INDEX.json from SYSTEM_STATE.md

Extracts structured data optimized for fast Phase 0 capability checking:
- Phase metadata (number, title, keywords)
- Capabilities and tools created
- Agents used and integrations
- Keyword search index for instant lookups

Usage:
    python3 claude/tools/generate_system_state_index.py
    python3 claude/tools/generate_system_state_index.py --output custom_path.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict


class SystemStateIndexGenerator:
    """Generate searchable JSON index from SYSTEM_STATE.md"""

    def __init__(self, system_state_path: Optional[Path] = None):
        if system_state_path is None:
            maia_root = Path(__file__).resolve().parent.parent.parent
            self.system_state_path = maia_root / "SYSTEM_STATE.md"
            self.index_path = maia_root / "SYSTEM_STATE_INDEX.json"
        else:
            self.system_state_path = Path(system_state_path)
            self.index_path = self.system_state_path.parent / "SYSTEM_STATE_INDEX.json"

    def extract_phase_number(self, header: str) -> Optional[int]:
        """Extract phase number from header"""
        match = re.search(r'PHASE\s+(\d+)', header, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from phase content"""
        keywords = set()

        # Extract from bold text
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', content)
        for match in bold_matches:
            # Clean and add if meaningful
            clean = match.strip(':').lower()
            if len(clean) > 3 and clean not in ['new', 'previous', 'current', 'session']:
                keywords.add(clean)

        # Extract file extensions as technology markers
        tech_patterns = [
            r'\b(python|javascript|typescript|react|vue|angular)\b',
            r'\.(py|js|ts|jsx|tsx|html|css|json|yaml|yml|md)',
            r'\b(pandas|numpy|flask|django|fastapi|ollama|chromadb|sqlite)\b',
            r'\b(azure|aws|gcp|confluence|trello|power bi|excel)\b',
            r'\b(rag|llm|ai|ml|nlp|embedding|vector)\b',
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.update(m.lower() for m in matches)

        # Extract quoted file/tool names
        file_matches = re.findall(r'`([^`]+\.(py|sh|js|html|json|md))`', content)
        for match, ext in file_matches:
            # Get base name without extension
            base = Path(match).stem
            keywords.add(base.replace('_', ' '))

        return sorted(list(keywords))[:20]  # Limit to top 20

    def extract_files(self, content: str) -> Dict[str, List[str]]:
        """Extract created and modified files"""
        files = {'created': [], 'modified': []}

        # Look for "Files Created" section
        created_section = re.search(r'\*\*Files Created\*\*:?\s*\n(.*?)(?:\n\n|\*\*)', content, re.DOTALL | re.IGNORECASE)
        if created_section:
            file_lines = created_section.group(1).strip().split('\n')
            for line in file_lines:
                # Extract file paths from markdown or plain text
                matches = re.findall(r'[`"]?([a-zA-Z0-9_/.\-]+\.(py|sh|js|html|json|md|plist|yaml|yml|txt|xlsx))[`"]?', line)
                for match, ext in matches:
                    if match not in files['created']:
                        files['created'].append(match)

        # Look for "Files Modified" section
        modified_section = re.search(r'\*\*Files Modified\*\*:?\s*\n(.*?)(?:\n\n|\*\*)', content, re.DOTALL | re.IGNORECASE)
        if modified_section:
            file_lines = modified_section.group(1).strip().split('\n')
            for line in file_lines:
                matches = re.findall(r'[`"]?([a-zA-Z0-9_/.\-]+\.(py|sh|js|html|json|md|yaml|yml|txt))[`"]?', line)
                for match, ext in matches:
                    if match not in files['modified']:
                        files['modified'].append(match)

        return files

    def extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities/achievements from content"""
        capabilities = []

        # Look for numbered achievement lists
        achievement_pattern = r'^\d+\.\s+\*\*([^*]+)\*\*:?\s*([^\n]+)'
        matches = re.findall(achievement_pattern, content, re.MULTILINE)
        for title, description in matches[:10]:  # Limit to 10
            capabilities.append(f"{title.strip()}: {description.strip()[:100]}")

        # Look for bullet points under Achievement/Built sections
        bullet_pattern = r'^[-*]\s+(.+?)$'
        in_achievement = False
        for line in content.split('\n'):
            if re.search(r'\*\*Achievement\*\*|\*\*Built\*\*|\*\*Delivered\*\*', line, re.IGNORECASE):
                in_achievement = True
                continue
            if in_achievement and re.match(r'^#+\s', line):  # Next section
                break
            if in_achievement:
                match = re.match(bullet_pattern, line)
                if match and len(capabilities) < 10:
                    capabilities.append(match.group(1).strip()[:150])

        return capabilities[:10]  # Limit to top 10

    def extract_agents(self, content: str) -> List[str]:
        """Extract agent names mentioned"""
        agents = set()

        # Common agent patterns
        agent_patterns = [
            r'([A-Z][a-zA-Z\s]+Agent)',
            r'Agent Collaboration.*?:\s*\n(.*?)(?:\n\n|\*\*)',
        ]

        for pattern in agent_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # Clean up agent names
                agent_names = re.findall(r'([A-Z][a-zA-Z\s]+Agent)', match)
                agents.update(agent_names)

        return sorted(list(agents))

    def extract_metrics(self, content: str) -> Dict[str, str]:
        """Extract quantifiable metrics"""
        metrics = {}

        # Look for key metrics patterns
        metric_patterns = [
            (r'(\d+(?:,\d+)?)\s*lines', 'lines'),
            (r'(\d+(?:\.\d+)?[KM]?)\s*tokens', 'tokens'),
            (r'(\d+)\s*phases?', 'phases'),
            (r'(\d+)\s*files?', 'files'),
            (r'(\d+(?:\.\d+)?%)\s*(?:savings?|reduction|efficiency)', 'efficiency'),
            (r'\$(\d+(?:,\d+)*(?:\.\d+)?[KM]?)', 'financial'),
        ]

        for pattern, key in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches and key not in metrics:
                metrics[key] = matches[0] if len(matches) == 1 else matches[:3]

        return metrics

    def parse_phases(self) -> Dict[int, Dict]:
        """Parse all phases from SYSTEM_STATE.md"""
        content = self.system_state_path.read_text()
        lines = content.splitlines()

        phase_pattern = re.compile(r'^###\s+\*\*✅\s*(.+?)\s*\*\*\s+⭐\s+\*\*.*PHASE\s+(\d+)', re.IGNORECASE)

        phases = {}
        current_phase_num = None
        current_phase_title = None
        current_phase_content = []

        for line in lines:
            match = phase_pattern.search(line)

            if match:
                # Save previous phase
                if current_phase_num is not None:
                    phase_text = '\n'.join(current_phase_content)
                    phases[current_phase_num] = self.parse_phase_content(
                        current_phase_num,
                        current_phase_title,
                        phase_text
                    )

                # Start new phase
                current_phase_title = match.group(1).strip()
                current_phase_num = int(match.group(2))
                current_phase_content = [line]

            elif line.strip() == '---' and current_phase_num is not None:
                # End of phase
                phase_text = '\n'.join(current_phase_content)
                phases[current_phase_num] = self.parse_phase_content(
                    current_phase_num,
                    current_phase_title,
                    phase_text
                )
                current_phase_num = None
                current_phase_title = None
                current_phase_content = []

            elif current_phase_num is not None:
                current_phase_content.append(line)

        # Don't forget last phase if no closing ---
        if current_phase_num is not None:
            phase_text = '\n'.join(current_phase_content)
            phases[current_phase_num] = self.parse_phase_content(
                current_phase_num,
                current_phase_title,
                phase_text
            )

        return phases

    def parse_phase_content(self, phase_num: int, title: str, content: str) -> Dict:
        """Extract structured data from phase content"""
        return {
            'title': title,
            'keywords': self.extract_keywords(content),
            'capabilities': self.extract_capabilities(content),
            'files': self.extract_files(content),
            'agents': self.extract_agents(content),
            'metrics': self.extract_metrics(content),
            'content_length': len(content)
        }

    def build_search_index(self, phases: Dict[int, Dict]) -> Dict[str, List[int]]:
        """Build keyword → phase number search index"""
        index = defaultdict(list)

        for phase_num, data in phases.items():
            # Index by keywords
            for keyword in data['keywords']:
                if phase_num not in index[keyword]:
                    index[keyword].append(phase_num)

            # Index by title words
            title_words = data['title'].lower().split()
            for word in title_words:
                if len(word) > 3 and phase_num not in index[word]:
                    index[word].append(phase_num)

            # Index by file names
            for file_path in data['files']['created'] + data['files']['modified']:
                file_name = Path(file_path).stem.lower()
                if phase_num not in index[file_name]:
                    index[file_name].append(phase_num)

        # Sort phase lists for each keyword
        return {k: sorted(v, reverse=True) for k, v in index.items()}

    def generate_index(self) -> Dict:
        """Generate complete index structure"""
        print("📊 Parsing SYSTEM_STATE.md...")
        phases = self.parse_phases()

        print(f"✅ Found {len(phases)} phases")

        print("🔍 Building search index...")
        search_index = self.build_search_index(phases)

        print(f"✅ Indexed {len(search_index)} keywords")

        # Convert phase numbers to strings for JSON (JavaScript compatibility)
        phases_str_keys = {str(k): v for k, v in phases.items()}

        index_data = {
            'metadata': {
                'generated_from': str(self.system_state_path),
                'total_phases': len(phases),
                'phase_numbers': sorted(phases.keys()),
                'total_keywords': len(search_index)
            },
            'phases': phases_str_keys,
            'search_index': dict(search_index)
        }

        return index_data

    def write_index(self, index_data: Dict):
        """Write index to JSON file"""
        self.index_path.write_text(json.dumps(index_data, indent=2))
        print(f"\n💾 Index written to: {self.index_path}")
        print(f"   File size: {self.index_path.stat().st_size:,} bytes")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SYSTEM_STATE_INDEX.json from SYSTEM_STATE.md"
    )
    parser.add_argument(
        '--input',
        help='Path to SYSTEM_STATE.md (default: auto-detect)'
    )
    parser.add_argument(
        '--output',
        help='Path for output JSON (default: same directory as input)'
    )

    args = parser.parse_args()

    generator = SystemStateIndexGenerator(
        system_state_path=Path(args.input) if args.input else None
    )

    if args.output:
        generator.index_path = Path(args.output)

    # Generate index
    index_data = generator.generate_index()

    # Write to file
    generator.write_index(index_data)

    # Show sample
    print("\n📋 Sample index entry (Phase 89):")
    if '89' in index_data['phases']:
        sample = index_data['phases']['89']
        print(f"   Title: {sample['title']}")
        print(f"   Keywords: {', '.join(sample['keywords'][:5])}...")
        print(f"   Files created: {len(sample['files']['created'])}")
        print(f"   Capabilities: {len(sample['capabilities'])}")


if __name__ == '__main__':
    main()
