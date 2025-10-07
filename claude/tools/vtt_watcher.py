#!/usr/bin/env python3
"""
VTT File Watcher - Automated Meeting Transcript Summarization
Monitors directory for new VTT files and triggers automatic summarization
Enhanced with Local LLM Intelligence (CodeLlama 13B for cost savings)
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging
import requests

# Configure logging
LOG_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "vtt_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VTT_WATCH_DIR = Path.home() / "Documents" / "VTT"
SUMMARY_OUTPUT_DIR = Path.home() / "git" / "maia" / "claude" / "data" / "transcript_summaries"
PROCESSED_TRACKER = Path.home() / "git" / "maia" / "claude" / "data" / "vtt_processed.json"

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "codellama:13b"  # 99.3% cost savings vs cloud LLMs

# FOB Templates
FOB_TEMPLATES_FILE = Path.home() / "git" / "maia" / "claude" / "data" / "meeting_fob_templates.json"

# Ensure directories exist
SUMMARY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class FOBTemplateManager:
    """Framework of Brilliance template manager for meeting-type specific summaries"""

    def __init__(self, templates_file: Path = FOB_TEMPLATES_FILE):
        self.templates_file = templates_file
        self.templates = self._load_templates()

    def _load_templates(self) -> dict:
        """Load FOB templates from JSON"""
        try:
            with open(self.templates_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load FOB templates: {e}")
            return {}

    def get_template(self, meeting_type: str) -> dict:
        """Get template for meeting type"""
        # Map meeting types to template keys
        type_mapping = {
            "standup": "standup",
            "client": "client",
            "technical": "technical",
            "planning": "planning",
            "review": "review",
            "one-on-one": "one_on_one",
            "other": "standup"  # Default fallback
        }

        template_key = type_mapping.get(meeting_type.lower(), "standup")
        return self.templates.get(template_key, self.templates.get("standup", {}))

    def format_section_prompt(self, template: dict, section_id: str, transcript: str) -> str:
        """Format LLM prompt for a specific section"""
        sections = template.get("sections", [])

        for section in sections:
            if section.get("id") == section_id:
                prompt = f"""Analyze this meeting transcript and extract information for:

**Section**: {section.get('title')}
**Instructions**: {section.get('prompt')}

Transcript:
{transcript}

Output:"""
                return prompt

        return ""

    def get_executive_summary_prompt(self, template: dict, transcript: str) -> str:
        """Get executive summary prompt for template"""
        summary_instructions = template.get("executive_summary_prompt", "Summarize the meeting in 3-4 concise bullets")

        prompt = f"""Summarize this meeting transcript.

**Instructions**: {summary_instructions}

Transcript:
{transcript}

Summary:"""
        return prompt


class LocalLLMProcessor:
    """Local LLM integration for intelligent transcript analysis"""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.api_url = OLLAMA_API_URL

    def generate(self, prompt: str, system: str = None, temperature: float = 0.3) -> str:
        """Generate completion from local LLM"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 2000
                }
            }

            if system:
                payload["system"] = system

            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return ""

    def extract_action_items(self, transcript: str) -> list:
        """Extract action items with speaker attribution"""
        prompt = f"""Analyze this meeting transcript and extract ALL action items.

For each action item, identify:
- The specific task or deliverable
- Who is responsible (if mentioned)
- Any deadlines or timeframes (if mentioned)

Format each action item as:
- [PERSON]: Task description (deadline if mentioned)

If no person is mentioned, use [TEAM].

Transcript:
{transcript}

Action Items:"""

        response = self.generate(prompt, temperature=0.1)

        # Parse response into structured format
        action_items = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*')):
                # Remove bullet point
                item = line.lstrip('-*').strip()
                if item:
                    action_items.append(item)

        return action_items

    def identify_speakers(self, transcript: str) -> dict:
        """Identify speakers and their contribution counts"""
        speakers = {}

        # Pattern for "Name:" or "Name -" format
        speaker_pattern = r'^([A-Z][a-zA-Z\s]+)(?::|-)(.+)$'

        for line in transcript.split('\n'):
            match = re.match(speaker_pattern, line.strip())
            if match:
                speaker = match.group(1).strip()
                if speaker not in speakers:
                    speakers[speaker] = 0
                speakers[speaker] += 1

        return speakers

    def identify_key_topics(self, transcript: str) -> list:
        """Identify main topics discussed"""
        prompt = f"""Analyze this meeting transcript and identify the 3-5 main topics or themes discussed.

For each topic, provide:
- A clear topic name (2-5 words)
- A brief description (one sentence)

Format as:
1. Topic Name - Description

Transcript:
{transcript}

Key Topics:"""

        response = self.generate(prompt, temperature=0.2)

        topics = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Clean up numbering
                topic = re.sub(r'^\d+[\.\)]\s*', '', line)
                topic = topic.lstrip('-*').strip()
                if topic:
                    topics.append(topic)

        return topics[:5]  # Limit to 5 topics

    def classify_meeting_type(self, transcript: str) -> str:
        """Classify the type of meeting"""
        prompt = f"""Classify this meeting into ONE of these categories:
- Standup: Daily team sync, quick updates, blockers
- Planning: Sprint planning, roadmap discussion, strategic planning
- Review: Sprint review, demo, retrospective
- Technical: Architecture discussion, technical design, problem-solving
- Client: Client meeting, stakeholder update, external communication
- One-on-One: Individual meeting, performance review, career discussion
- Other: Doesn't fit other categories

Just respond with the single category name.

Transcript excerpt:
{transcript[:1000]}

Meeting Type:"""

        response = self.generate(prompt, temperature=0.1)

        # Extract just the category name
        meeting_type = response.strip().split('\n')[0].strip().title()

        # Validate against known types
        valid_types = ["Standup", "Planning", "Review", "Technical", "Client", "One-On-One", "Other"]
        for vtype in valid_types:
            if vtype.lower() in meeting_type.lower():
                return vtype

        return "Other"

    def generate_summary(self, transcript: str) -> str:
        """Generate intelligent meeting summary"""
        prompt = f"""Summarize this meeting transcript in 3-4 concise bullet points.

Focus on:
- Key decisions made
- Important discussions
- Main outcomes or conclusions

Be specific and actionable. Use bullet points.

Transcript:
{transcript}

Summary:"""

        response = self.generate(prompt, temperature=0.3)
        return response.strip()

class VTTFileHandler(FileSystemEventHandler):
    """Handle VTT file events"""

    def __init__(self):
        self.processed_files = self._load_processed_files()
        self.llm = LocalLLMProcessor()
        self.fob = FOBTemplateManager()

    def _load_processed_files(self):
        """Load list of already processed files"""
        if PROCESSED_TRACKER.exists():
            try:
                with open(PROCESSED_TRACKER, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load processed files tracker: {e}")
                return set()
        return set()

    def _save_processed_file(self, file_path: str):
        """Mark file as processed"""
        self.processed_files.add(file_path)
        try:
            with open(PROCESSED_TRACKER, 'w') as f:
                json.dump(list(self.processed_files), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed file tracker: {e}")

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already processed
        if str(file_path) in self.processed_files:
            logger.info(f"Skipping already processed file: {file_path.name}")
            return

        # Wait a moment for file to be fully written (especially on OneDrive)
        time.sleep(2)

        logger.info(f"New VTT file detected: {file_path.name}")
        self.process_vtt_file(file_path)

    def on_modified(self, event):
        """Handle file modifications (OneDrive sync may trigger this)"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process VTT files
        if file_path.suffix.lower() != '.vtt':
            return

        # Skip if already processed
        if str(file_path) in self.processed_files:
            return

        # Wait a moment for file to be fully synced
        time.sleep(2)

        logger.info(f"VTT file modified/synced: {file_path.name}")
        self.process_vtt_file(file_path)

    def process_vtt_file(self, file_path: Path):
        """Process VTT file and generate summary"""
        try:
            logger.info(f"Processing: {file_path.name}")

            # Read VTT content
            with open(file_path, 'r', encoding='utf-8') as f:
                vtt_content = f.read()

            # Extract transcript text (strip timestamps and metadata)
            transcript = self._extract_transcript_text(vtt_content)

            # Generate summary using local LLM for cost savings
            summary = self._generate_summary(transcript, file_path.name)

            # Save summary
            summary_file = SUMMARY_OUTPUT_DIR / f"{file_path.stem}_summary.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)

            logger.info(f"✅ Summary saved: {summary_file.name}")

            # Mark as processed
            self._save_processed_file(str(file_path))

            # 🚀 NEW: Trigger VTT Intelligence Pipeline
            self._trigger_intelligence_pipeline(summary_file)

            # Send notification (optional)
            self._send_notification(file_path.name, summary_file)

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)

    def _extract_transcript_text(self, vtt_content: str) -> str:
        """Extract clean transcript text from VTT format"""
        lines = vtt_content.split('\n')
        transcript_lines = []

        skip_next = False
        for line in lines:
            line = line.strip()

            # Skip VTT header
            if line.startswith('WEBVTT'):
                continue

            # Skip timestamp lines (format: 00:00:00.000 --> 00:00:00.000)
            if '-->' in line:
                skip_next = False
                continue

            # Skip cue identifiers (numbers or blank lines)
            if line.isdigit() or line == '':
                continue

            # Skip metadata
            if line.startswith('NOTE') or line.startswith('STYLE'):
                skip_next = True
                continue

            if skip_next:
                continue

            # This is actual transcript text
            transcript_lines.append(line)

        return '\n'.join(transcript_lines)

    def _generate_summary(self, transcript: str, filename: str) -> str:
        """Generate intelligent meeting summary using local LLM with FOB templates"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        word_count = len(transcript.split())

        logger.info("Analyzing with local LLM (CodeLlama 13B) + FOB Templates...")

        # Meeting type classification
        meeting_type = self.llm.classify_meeting_type(transcript)
        logger.info(f"Meeting type: {meeting_type}")

        # Get FOB template for this meeting type
        fob_template = self.fob.get_template(meeting_type)
        template_name = fob_template.get("name", meeting_type)
        logger.info(f"Using FOB template: {template_name}")

        # Speaker identification
        speakers = self.llm.identify_speakers(transcript)
        logger.info(f"Speakers identified: {len(speakers)}")

        # Executive summary using FOB-specific prompt
        exec_summary_prompt = self.fob.get_executive_summary_prompt(fob_template, transcript)
        exec_summary = self.llm.generate(exec_summary_prompt, temperature=0.3)
        logger.info("Executive summary generated")

        # Build FOB-structured markdown summary
        summary = f"""# 📋 {template_name} Summary

**File**: {filename}
**Processed**: {timestamp}
**Meeting Type**: {meeting_type}
**Duration**: {word_count} words (~{word_count // 150} min speaking time)

---

## 🎯 Executive Summary

{exec_summary}

---

## 👥 Participants

"""

        if speakers:
            for speaker, count in sorted(speakers.items(), key=lambda x: x[1], reverse=True):
                summary += f"- **{speaker}**: {count} contributions\n"
        else:
            summary += "*No speaker attribution detected in transcript*\n"

        summary += "\n---\n"

        # Process FOB template sections
        sections = fob_template.get("sections", [])
        for section in sections:
            section_id = section.get("id")
            section_title = section.get("title")

            logger.info(f"Processing FOB section: {section_id}")

            # Generate content for this section
            section_prompt = self.fob.format_section_prompt(fob_template, section_id, transcript)
            if section_prompt:
                section_content = self.llm.generate(section_prompt, temperature=0.2)

                summary += f"\n## {section_title}\n\n"

                if section_content and section_content.strip():
                    summary += f"{section_content}\n"
                else:
                    summary += "*No information identified for this section*\n"

                summary += "\n---\n"

        # Add full transcript at the end
        summary += f"""
## 📝 Full Transcript

{transcript}

---

*Generated by Maia VTT Watcher with FOB Templates + Local LLM Intelligence (CodeLlama 13B)*
*Framework: {template_name} | Cost Savings: 99.3% vs cloud LLMs | Carbon Neutral: 100% local*
*Location: {SUMMARY_OUTPUT_DIR}*
"""
        return summary

    def _trigger_intelligence_pipeline(self, summary_file: Path):
        """Trigger VTT intelligence pipeline for action extraction and integration"""
        try:
            logger.info(f"🚀 Triggering intelligence pipeline for {summary_file.name}")

            # Import and run pipeline
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from claude.tools.vtt_intelligence_pipeline import VTTIntelligencePipeline

            # Initialize pipeline with defaults
            pipeline = VTTIntelligencePipeline(
                owner="Naythan",
                trello_board="68de069e996bf03442ae5eea"  # Your "My Trello board"
            )

            # Process with full intelligence extraction
            results = pipeline.process_summary_complete(
                summary_file,
                push_to_trello=True,  # Auto-create Trello cards
                index_to_rag=True     # Index to meeting RAG
            )

            logger.info(f"✅ Intelligence pipeline complete: {results.get('status', 'success')}")

        except Exception as e:
            logger.error(f"Intelligence pipeline failed: {e}", exc_info=True)
            # Don't block VTT processing if intelligence fails

    def _send_notification(self, filename: str, summary_file: Path):
        """Send macOS notification"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "Summary saved: {summary_file.name}" with title "VTT Processed" subtitle "{filename}"'
            ], check=False, capture_output=True)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")


def main():
    """Main entry point"""
    logger.info(f"Starting VTT Watcher")
    logger.info(f"Monitoring: {VTT_WATCH_DIR}")
    logger.info(f"Output: {SUMMARY_OUTPUT_DIR}")

    # Check directory exists
    if not VTT_WATCH_DIR.exists():
        logger.error(f"Watch directory does not exist: {VTT_WATCH_DIR}")
        sys.exit(1)

    # Create event handler and observer
    event_handler = VTTFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(VTT_WATCH_DIR), recursive=False)

    # Process any existing unprocessed VTT files
    logger.info("Scanning for existing VTT files...")
    for vtt_file in VTT_WATCH_DIR.glob("*.vtt"):
        if str(vtt_file) not in event_handler.processed_files:
            logger.info(f"Found unprocessed file: {vtt_file.name}")
            event_handler.process_vtt_file(vtt_file)

    # Start watching
    observer.start()
    logger.info("✅ VTT Watcher is running (Press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping VTT Watcher...")
        observer.stop()

    observer.join()
    logger.info("VTT Watcher stopped")


if __name__ == "__main__":
    main()
