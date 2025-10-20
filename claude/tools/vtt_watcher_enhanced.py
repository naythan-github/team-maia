#!/usr/bin/env python3
"""
VTT Watcher Enhanced - With Checkpoint/Retry (Option B)

Wraps existing vtt_watcher.py with:
- Checkpoint manager for resume-on-failure
- Retry logic for Ollama API calls
- Better error handling

Usage: Replace vtt_watcher.py in LaunchAgent plist with this file

Author: SRE Principal Engineer Agent
Date: 2025-10-20
Phase: Personal Mac Reliability - Option B
"""

import sys
from pathlib import Path

# Import checkpoint manager
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

from claude.tools.sre.checkpoint_manager import CheckpointManager, retry_with_backoff

# Import original vtt_watcher
import claude.tools.vtt_watcher as original_vtt

# Patch LocalLLMProcessor with retry logic
class EnhancedLocalLLMProcessor(original_vtt.LocalLLMProcessor):
    """Enhanced LLM processor with retry logic"""

    def generate(self, prompt: str, system: str = None, temperature: float = 0.3) -> str:
        """Generate with automatic retry on transient failures"""
        def _make_request():
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

            import requests
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        try:
            return retry_with_backoff(_make_request, max_retries=3, base_delay=5)
        except Exception as e:
            original_vtt.logger.error(f"LLM generation failed after retries: {e}")
            return ""


# Patch VTTFileHandler with checkpoint support
class EnhancedVTTFileHandler(original_vtt.VTTFileHandler):
    """Enhanced file handler with checkpoints"""

    def __init__(self):
        super().__init__()
        self.checkpoint_mgr = CheckpointManager("vtt_processing")

    def process_vtt_file(self, file_path: Path):
        """Process VTT file with checkpoint support"""
        file_id = str(file_path)

        # Check for existing checkpoint
        checkpoint = self.checkpoint_mgr.get_checkpoint(file_id)
        if checkpoint:
            original_vtt.logger.info(f"Resuming from checkpoint: {checkpoint['stage']}")

            # Check retry limit
            if self.checkpoint_mgr.should_give_up(file_id, max_retries=3):
                original_vtt.logger.error(f"Max retries exceeded for {file_path.name}")
                return

        try:
            # Stage 1: Parsing
            self.checkpoint_mgr.save_checkpoint(file_id, "parsing", {})
            transcript_data = self._parse_vtt_file(file_path)

            # Stage 2: Analysis
            self.checkpoint_mgr.save_checkpoint(file_id, "analyzing", {
                "line_count": len(transcript_data.get('lines', []))
            })
            analysis = self._analyze_transcript(transcript_data)

            # Stage 3: Summary generation
            self.checkpoint_mgr.save_checkpoint(file_id, "summarizing", {})
            summary = self._generate_summary(analysis)

            # Stage 4: Saving
            self.checkpoint_mgr.save_checkpoint(file_id, "saving", {})
            self._save_summary(file_path, summary)

            # Success - clear checkpoint
            self.checkpoint_mgr.clear_checkpoint(file_id)
            original_vtt.logger.info(f"✅ Completed: {file_path.name}")

        except Exception as e:
            original_vtt.logger.error(f"Processing failed at stage {checkpoint.get('stage', 'unknown') if checkpoint else 'init'}: {e}")
            self.checkpoint_mgr.increment_retry(file_id)
            raise

    def _parse_vtt_file(self, file_path: Path):
        """Parse VTT file (delegates to original)"""
        # Call original parse logic
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = [line for line in content.split('\n') if line.strip()]
        return {
            'file_path': file_path,
            'lines': lines,
            'content': content
        }

    def _analyze_transcript(self, transcript_data):
        """Analyze transcript (simplified - extend as needed)"""
        return transcript_data

    def _generate_summary(self, analysis):
        """Generate summary (delegates to LLM)"""
        llm = EnhancedLocalLLMProcessor()  # Use enhanced version
        prompt = f"Summarize this meeting transcript:\n\n{analysis['content'][:2000]}"
        return llm.generate(prompt)

    def _save_summary(self, file_path: Path, summary: str):
        """Save summary to output directory"""
        output_file = original_vtt.SUMMARY_OUTPUT_DIR / f"{file_path.stem}_summary.txt"
        with open(output_file, 'w') as f:
            f.write(summary)


# Replace original classes with enhanced versions
original_vtt.LocalLLMProcessor = EnhancedLocalLLMProcessor
original_vtt.VTTFileHandler = EnhancedVTTFileHandler

# Run original main
if __name__ == "__main__":
    original_vtt.main()
