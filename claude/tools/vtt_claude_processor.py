#!/usr/bin/env python3
"""
VTT Claude Processor - High-Quality Intelligence Extraction
Processes VTT transcripts using Claude Sonnet with chunked processing for large files

Features:
- Automatic chunking for large transcripts (>20K tokens)
- Superior action/decision/follow-up extraction
- Owner attribution with implied action detection
- Priority and urgency inference from context
- Relationship mapping between actions

Author: Maia Personal Assistant
Phase: 91 - Claude Sonnet VTT Intelligence
Date: 2025-10-06
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTTClaudeProcessor:
    """Process VTT files using Claude Sonnet for high-quality intelligence extraction"""

    def __init__(self):
        """Initialize processor"""
        self.data_dir = MAIA_ROOT / "claude" / "data"
        self.summaries_dir = self.data_dir / "transcript_summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def extract_clean_transcript(self, vtt_file: Path) -> str:
        """Extract clean transcript from VTT format"""
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        transcript_lines = []

        # Extract speaker dialogue
        for line in content.split('\n'):
            # Match: <v Speaker Name>Text</v>
            match = re.search(r'<v ([^>]+)>([^<]+)</v>', line)
            if match:
                speaker = match.group(1).split('|')[0].strip()
                text = match.group(2).strip()

                # Skip very short filler words
                if text and len(text) > 2:
                    transcript_lines.append(f"{speaker}: {text}")

        return '\n'.join(transcript_lines)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)"""
        return len(text) // 4

    def chunk_transcript(self, transcript: str, max_tokens: int = 15000) -> List[str]:
        """
        Split transcript into chunks at speaker boundaries

        Args:
            transcript: Clean transcript with speaker lines
            max_tokens: Maximum tokens per chunk

        Returns:
            List of transcript chunks
        """
        lines = transcript.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.estimate_tokens(line)

            if current_tokens + line_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_tokens = 0

            current_chunk.append(line)
            current_tokens += line_tokens

        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def process_vtt_file(self, vtt_file: Path) -> Dict:
        """
        Process VTT file with Claude Sonnet

        Args:
            vtt_file: Path to VTT file

        Returns:
            Processing results with summary path and intelligence
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {vtt_file.name}")
        logger.info(f"{'='*70}\n")

        # Extract clean transcript
        logger.info("Extracting transcript...")
        transcript = self.extract_clean_transcript(vtt_file)
        total_tokens = self.estimate_tokens(transcript)

        logger.info(f"Transcript: {len(transcript.split())} words (~{total_tokens} tokens)")

        # Determine processing strategy
        if total_tokens <= 20000:
            logger.info("Strategy: Single-pass processing")
            return self._process_single_pass(vtt_file, transcript)
        else:
            logger.info(f"Strategy: Chunked processing ({total_tokens} tokens)")
            return self._process_chunked(vtt_file, transcript)

    def _process_single_pass(self, vtt_file: Path, transcript: str) -> Dict:
        """
        Process small/medium VTT in single pass

        NOTE: This method requires Claude interaction - will be called by VTT watcher
        which has access to Claude context. This tool structures the prompts.
        """
        results = {
            "strategy": "single_pass",
            "vtt_file": str(vtt_file),
            "processing_chunks": 1,
            "prompt": self._generate_analysis_prompt(transcript, is_final=True)
        }

        return results

    def _process_chunked(self, vtt_file: Path, transcript: str) -> Dict:
        """
        Process large VTT in chunks

        NOTE: Returns prompts for Claude to process, doesn't call Claude directly
        """
        chunks = self.chunk_transcript(transcript, max_tokens=15000)

        logger.info(f"Split into {len(chunks)} chunks")

        results = {
            "strategy": "chunked",
            "vtt_file": str(vtt_file),
            "processing_chunks": len(chunks),
            "chunk_prompts": [],
            "consolidation_prompt": None
        }

        # Generate prompts for each chunk
        for i, chunk in enumerate(chunks):
            chunk_prompt = self._generate_chunk_prompt(chunk, i + 1, len(chunks))
            results["chunk_prompts"].append({
                "chunk_number": i + 1,
                "prompt": chunk_prompt
            })

        return results

    def _generate_analysis_prompt(self, transcript: str, is_final: bool = True) -> str:
        """Generate comprehensive analysis prompt for Claude"""

        prompt = f"""Analyze this meeting transcript and extract comprehensive intelligence.

**TRANSCRIPT:**
{transcript}

**EXTRACTION REQUIREMENTS:**

1. **ACTION ITEMS** (with superior attribution and context):
   - Extract ALL action items (explicit and implied)
   - Owner attribution (handle "we should" → identify responsible party)
   - Deadline parsing (infer urgency from context: "urgent" = this week, "soon" = next week)
   - Priority inference (P0 = blocking others, P1 = important, P2 = nice-to-have)
   - Dependencies (what blocks this action, what this blocks)

   Format as table:
   | Owner | Action | Deadline | Priority | Dependencies | Context |

2. **DECISIONS MADE**:
   - Firm decisions (explicitly stated)
   - Tentative approaches (discussed but not final)
   - Deferred decisions (tabled for later)
   - Decision owners and rationale

   Format as table:
   | Decision | Type | Owner | Rationale | Impact |

3. **FOLLOW-UPS & OPEN QUESTIONS**:
   - Unresolved questions
   - Items needing more information
   - Scheduled follow-up meetings

4. **KEY DISCUSSION TOPICS**:
   - Main themes (3-5 topics)
   - Strategic vs operational focus
   - Budget/financial implications

5. **PARTICIPANTS & ROLES**:
   - Who spoke most (leadership indicators)
   - Subject matter experts identified
   - External stakeholders mentioned

6. **EXECUTIVE SUMMARY** (3-4 sentences):
   - Meeting purpose
   - Key outcomes
   - Next steps
   - Critical issues raised

**OUTPUT FORMAT:**
Provide structured markdown with all sections above.
"""

        return prompt

    def _generate_chunk_prompt(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Generate prompt for processing a chunk"""

        prompt = f"""Analyze this meeting transcript chunk ({chunk_num} of {total_chunks}) and extract intelligence.

**TRANSCRIPT CHUNK {chunk_num}/{total_chunks}:**
{chunk}

**EXTRACTION REQUIREMENTS:**

Extract from this chunk:
1. **Action Items**: Owner, action, deadline hints, priority
2. **Decisions**: What was decided, by whom
3. **Key Topics**: Main discussion themes
4. **Open Questions**: Unresolved items
5. **Participants**: Who spoke, their roles/focus

Format as structured data (JSON preferred for consolidation).

Focus on extracting facts - don't infer context from other chunks you haven't seen.
"""

        return prompt

    def save_processing_task(self, results: Dict) -> Path:
        """Save processing task for Claude to execute"""
        task_file = self.data_dir / "vtt_processing_tasks" / f"{Path(results['vtt_file']).stem}_task.json"
        task_file.parent.mkdir(parents=True, exist_ok=True)

        with open(task_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved processing task: {task_file.name}")
        return task_file


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="VTT Claude Processor")
    parser.add_argument("vtt_file", help="VTT file to process")
    parser.add_argument("--output", help="Output directory for summary")

    args = parser.parse_args()

    vtt_file = Path(args.vtt_file)
    if not vtt_file.exists():
        print(f"Error: File not found: {vtt_file}")
        sys.exit(1)

    processor = VTTClaudeProcessor()
    results = processor.process_vtt_file(vtt_file)

    # Save task for Claude to process
    task_file = processor.save_processing_task(results)

    print(f"\n✅ Processing task created: {task_file}")
    print(f"   Strategy: {results['strategy']}")
    print(f"   Chunks: {results['processing_chunks']}")
    print(f"\nNext: Have Claude process this task file to generate intelligence")


if __name__ == "__main__":
    main()
