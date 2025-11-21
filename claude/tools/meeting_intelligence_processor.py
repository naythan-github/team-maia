#!/usr/bin/env python3
"""
Meeting Intelligence Processor - Content Intelligence Layer for Meeting Transcripts

Provides three core capabilities:
1. Auto-Summarization (5-7 bullet points using Gemma2:9b)
2. Action Item Extraction (JSON structured output using Hermes-2-Pro)
3. Keyword/Topic Extraction (using Qwen2.5:7b-instruct)

Integrates with whisper_meeting_transcriber.py for automatic post-meeting analysis.

Usage:
    # Standalone processing
    python3 claude/tools/meeting_intelligence_processor.py /path/to/transcript.md

    # Python API
    from claude.tools.meeting_intelligence_processor import MeetingIntelligenceProcessor
    processor = MeetingIntelligenceProcessor()
    results = processor.process_transcript("/path/to/transcript.md")

Performance:
    - Summarization: 20-28s (Gemma2:9b)
    - Action Items: 16-24s (Hermes-2-Pro-Mistral-7B)
    - Keywords: 16-24s (Qwen2.5:7b-instruct)
    - Total: 52-76s for all three tasks

Author: Maia System
Created: 2025-11-21
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import requests
except ImportError:
    print("❌ Missing requests library")
    print("   Install with: pip3 install requests")
    sys.exit(1)

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

# Model Selection (based on LLM research)
MODEL_SUMMARIZATION = "gemma2:9b"          # Best quality for summaries
MODEL_ACTION_ITEMS = "knoopx/hermes-2-pro-mistral:7b-q8_0"  # Best for JSON extraction
MODEL_KEYWORDS = "qwen2.5:7b-instruct"     # Best for structured data

# Fallback models (if recommended not available)
FALLBACK_MODEL = "mistral:7b"


class OllamaClient:
    """Simple Ollama API client"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"

    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def model_exists(self, model_name: str) -> bool:
        """Check if a model is downloaded"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                # Check for exact match or prefix match (handles tags like :7b-q8_0)
                for model in models:
                    model_full_name = model.get("name", "")
                    if model_full_name == model_name or model_full_name.startswith(model_name):
                        return True
            return False
        except requests.exceptions.RequestException:
            return False

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        format_json: bool = False,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate text using Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        if system:
            payload["system"] = system

        if format_json:
            payload["format"] = "json"

        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=120  # 2 minutes max
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


class MeetingIntelligenceProcessor:
    """Process meeting transcripts with LLM-powered intelligence"""

    def __init__(
        self,
        ollama_url: str = OLLAMA_BASE_URL,
        summarization_model: Optional[str] = None,
        action_model: Optional[str] = None,
        keyword_model: Optional[str] = None
    ):
        """Initialize processor with model selection"""
        self.ollama = OllamaClient(ollama_url)

        # Check Ollama availability
        if not self.ollama.is_available():
            raise RuntimeError(
                "❌ Ollama is not running. Start with: ollama serve"
            )

        # Model selection with fallbacks
        self.model_summary = self._select_model(
            summarization_model or MODEL_SUMMARIZATION,
            [MODEL_SUMMARIZATION, FALLBACK_MODEL]
        )
        self.model_actions = self._select_model(
            action_model or MODEL_ACTION_ITEMS,
            [MODEL_ACTION_ITEMS, FALLBACK_MODEL]
        )
        self.model_keywords = self._select_model(
            keyword_model or MODEL_KEYWORDS,
            [MODEL_KEYWORDS, FALLBACK_MODEL]
        )

        print(f"✅ Using models:")
        print(f"   Summarization: {self.model_summary}")
        print(f"   Action Items:  {self.model_actions}")
        print(f"   Keywords:      {self.model_keywords}")

    def _select_model(self, preferred: str, fallbacks: List[str]) -> str:
        """Select first available model from list"""
        for model in [preferred] + fallbacks:
            if self.ollama.model_exists(model):
                return model

        # If no models available, return preferred (will fail with clear error)
        return preferred

    def load_transcript(self, file_path: str) -> Dict[str, Any]:
        """Load transcript from Markdown file"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {file_path}")

        with open(path, 'r') as f:
            content = f.read()

        # Extract metadata from header
        metadata = {}
        lines = content.split('\n')

        # Parse Markdown header
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            if line.startswith('**Date**:'):
                metadata['date'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Time**:'):
                metadata['time'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Session ID**:'):
                metadata['session_id'] = line.split(':', 1)[1].strip()
            elif line.startswith('# '):
                metadata['title'] = line[2:].strip()

        # Extract main content (remove header and footer)
        content_start = content.find('---\n')
        if content_start != -1:
            content = content[content_start + 4:]

        # Remove footer if exists (second ---)
        content_end = content.rfind('\n---\n')
        if content_end != -1:
            content = content[:content_end]

        # Clean timestamps from content for LLM processing
        clean_content = re.sub(r'## \[\d{2}:\d{2}:\d{2}\]\n', '', content)

        return {
            "file_path": str(path),
            "metadata": metadata,
            "raw_content": content,
            "clean_content": clean_content.strip(),
            "word_count": len(clean_content.split())
        }

    def summarize(self, transcript_text: str) -> Dict[str, Any]:
        """Generate 5-7 bullet point summary"""
        print("\n🔄 Generating summary...")

        prompt = f"""You are a professional meeting note-taker. Summarize the following meeting transcript into 5-7 concise bullet points. Focus on key decisions, main discussion topics, and important announcements.

Format your response as:
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

Keep each bullet point to 1-2 sentences maximum. Be specific and actionable.

Transcript:
{transcript_text}"""

        start_time = datetime.now()
        response = self.ollama.generate(
            model=self.model_summary,
            prompt=prompt,
            temperature=0.4  # Balance consistency and creativity
        )
        latency = (datetime.now() - start_time).total_seconds()

        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "latency_seconds": latency
            }

        summary_text = response.get("response", "").strip()

        # Extract bullet points
        bullets = []
        for line in summary_text.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                bullets.append(line[1:].strip())
            elif line and not line.startswith('#'):
                # Sometimes models don't use bullet formatting
                bullets.append(line)

        return {
            "success": True,
            "summary_text": summary_text,
            "bullet_points": bullets,
            "bullet_count": len(bullets),
            "model": self.model_summary,
            "latency_seconds": round(latency, 1)
        }

    def extract_action_items(self, transcript_text: str) -> Dict[str, Any]:
        """Extract action items as structured JSON"""
        print("\n🔄 Extracting action items...")

        prompt = f"""Extract all action items, tasks, and follow-ups from this meeting transcript.

Return ONLY valid JSON in this exact format (no additional text):

{{
  "action_items": [
    {{
      "task": "description of the specific task or action",
      "assignee": "person responsible (or null if not mentioned)",
      "deadline": "due date (or null if not mentioned)",
      "priority": "high/medium/low (or null if not clear)",
      "context": "brief context from the meeting"
    }}
  ]
}}

Look for phrases like:
- "need to", "should", "must", "have to"
- "follow up", "action item", "next steps"
- "will do", "going to", "responsible for"
- Deadlines, dates, timeframes

If there are no action items, return: {{"action_items": []}}

Transcript:
{transcript_text}"""

        start_time = datetime.now()
        response = self.ollama.generate(
            model=self.model_actions,
            prompt=prompt,
            temperature=0.1,  # Max consistency for structured output
            format_json=True
        )
        latency = (datetime.now() - start_time).total_seconds()

        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "latency_seconds": latency
            }

        # Parse JSON response
        try:
            action_data = json.loads(response.get("response", "{}"))
            action_items = action_data.get("action_items", [])

            return {
                "success": True,
                "action_items": action_items,
                "count": len(action_items),
                "model": self.model_actions,
                "latency_seconds": round(latency, 1)
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing failed: {e}",
                "raw_response": response.get("response", ""),
                "latency_seconds": latency
            }

    def extract_keywords(self, transcript_text: str, top_n: int = 10) -> Dict[str, Any]:
        """Extract top keywords and topics"""
        print("\n🔄 Extracting keywords...")

        prompt = f"""Identify the top {top_n} key topics and themes discussed in this meeting transcript.

Return as a simple numbered list:
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]

Each topic should be 2-5 words maximum. Focus on specific subjects, products, technologies, or decisions discussed.

Transcript:
{transcript_text}"""

        start_time = datetime.now()
        response = self.ollama.generate(
            model=self.model_keywords,
            prompt=prompt,
            temperature=0.5  # Allow some variation
        )
        latency = (datetime.now() - start_time).total_seconds()

        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "latency_seconds": latency
            }

        keywords_text = response.get("response", "").strip()

        # Extract keywords from numbered list
        keywords = []
        for line in keywords_text.split('\n'):
            line = line.strip()
            # Match patterns like "1. keyword" or "1) keyword" or "- keyword"
            match = re.match(r'^[\d\-\•\*]+[\.\)]\s*(.+)$', line)
            if match:
                keywords.append(match.group(1).strip())
            elif line and not line.startswith('#'):
                keywords.append(line)

        return {
            "success": True,
            "keywords": keywords[:top_n],
            "keywords_text": keywords_text,
            "count": len(keywords[:top_n]),
            "model": self.model_keywords,
            "latency_seconds": round(latency, 1)
        }

    def process_transcript(
        self,
        file_path: str,
        include_summary: bool = True,
        include_actions: bool = True,
        include_keywords: bool = True
    ) -> Dict[str, Any]:
        """Process transcript with all intelligence capabilities"""
        print(f"\n{'='*80}")
        print(f"📋 Processing: {file_path}")
        print(f"{'='*80}")

        # Load transcript
        try:
            transcript = self.load_transcript(file_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load transcript: {e}"
            }

        print(f"\n📊 Transcript Info:")
        print(f"   Title: {transcript['metadata'].get('title', 'Unknown')}")
        print(f"   Date:  {transcript['metadata'].get('date', 'Unknown')}")
        print(f"   Words: {transcript['word_count']}")

        results = {
            "success": True,
            "file_path": file_path,
            "metadata": transcript["metadata"],
            "word_count": transcript["word_count"],
            "timestamp": datetime.now().isoformat()
        }

        total_start = datetime.now()

        # Run analyses
        if include_summary:
            results["summary"] = self.summarize(transcript["clean_content"])

        if include_actions:
            results["action_items"] = self.extract_action_items(transcript["clean_content"])

        if include_keywords:
            results["keywords"] = self.extract_keywords(transcript["clean_content"])

        total_latency = (datetime.now() - total_start).total_seconds()
        results["total_latency_seconds"] = round(total_latency, 1)

        print(f"\n{'='*80}")
        print(f"✅ Processing complete in {total_latency:.1f}s")
        print(f"{'='*80}")

        return results

    def save_intelligence(self, results: Dict[str, Any], output_path: Optional[str] = None):
        """Save intelligence results to JSON file"""
        if not output_path:
            # Generate output path from input file
            input_path = Path(results["file_path"])
            output_path = input_path.parent / f"{input_path.stem}_intelligence.json"

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Intelligence saved: {output_path}")
        return output_path

    def display_results(self, results: Dict[str, Any]):
        """Display results in terminal"""
        print(f"\n{'='*80}")
        print(f"📊 MEETING INTELLIGENCE REPORT")
        print(f"{'='*80}")

        # Metadata
        metadata = results.get("metadata", {})
        print(f"\n📋 Meeting: {metadata.get('title', 'Unknown')}")
        print(f"📅 Date: {metadata.get('date', 'Unknown')}")
        print(f"📝 Words: {results.get('word_count', 0)}")

        # Summary
        if "summary" in results and results["summary"].get("success"):
            summary = results["summary"]
            print(f"\n{'─'*80}")
            print(f"📝 SUMMARY ({summary['bullet_count']} points, {summary['latency_seconds']}s)")
            print(f"{'─'*80}")
            for i, bullet in enumerate(summary.get("bullet_points", []), 1):
                print(f"{i}. {bullet}")

        # Action Items
        if "action_items" in results and results["action_items"].get("success"):
            actions = results["action_items"]
            print(f"\n{'─'*80}")
            print(f"✅ ACTION ITEMS ({actions['count']} items, {actions['latency_seconds']}s)")
            print(f"{'─'*80}")
            for i, item in enumerate(actions.get("action_items", []), 1):
                print(f"\n{i}. {item['task']}")
                if item.get('assignee'):
                    print(f"   👤 Assignee: {item['assignee']}")
                if item.get('deadline'):
                    print(f"   📅 Deadline: {item['deadline']}")
                if item.get('priority'):
                    print(f"   ⚡ Priority: {item['priority']}")

        # Keywords
        if "keywords" in results and results["keywords"].get("success"):
            keywords = results["keywords"]
            print(f"\n{'─'*80}")
            print(f"🏷️  KEYWORDS ({keywords['count']} topics, {keywords['latency_seconds']}s)")
            print(f"{'─'*80}")
            for i, keyword in enumerate(keywords.get("keywords", []), 1):
                print(f"{i}. {keyword}")

        # Performance
        print(f"\n{'─'*80}")
        print(f"⏱️  PERFORMANCE")
        print(f"{'─'*80}")
        print(f"Total processing time: {results.get('total_latency_seconds', 0)}s")

        print(f"\n{'='*80}\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process meeting transcripts with LLM intelligence"
    )
    parser.add_argument(
        'transcript',
        help='Path to transcript Markdown file'
    )
    parser.add_argument(
        '--output',
        help='Output path for intelligence JSON (default: auto-generated)'
    )
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='Skip summary generation'
    )
    parser.add_argument(
        '--no-actions',
        action='store_true',
        help='Skip action item extraction'
    )
    parser.add_argument(
        '--no-keywords',
        action='store_true',
        help='Skip keyword extraction'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (no display)'
    )

    args = parser.parse_args()

    try:
        # Initialize processor
        processor = MeetingIntelligenceProcessor()

        # Process transcript
        results = processor.process_transcript(
            args.transcript,
            include_summary=not args.no_summary,
            include_actions=not args.no_actions,
            include_keywords=not args.no_keywords
        )

        # Save results
        output_path = processor.save_intelligence(results, args.output)

        # Display results
        if not args.quiet:
            processor.display_results(results)

        print(f"✅ Complete! Intelligence saved to: {output_path}")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
