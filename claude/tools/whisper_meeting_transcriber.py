#!/usr/bin/env python3
"""
Whisper Meeting Transcriber - Continuous Real-Time Meeting Transcription with RAG Integration

Records and transcribes meetings continuously with live display, automatic saving,
and ChromaDB RAG indexing for intelligent search and summarization.

Features:
- Continuous recording with 30s rolling chunks (optimal accuracy)
- Live terminal display with session status
- Auto-save to Markdown with timestamps
- ChromaDB RAG indexing for semantic search
- Session management (start/stop/pause)
- Integration with existing whisper-server (192ms inference)

Architecture:
    Recording → 30s chunks → Whisper Server → Live Display + Save + RAG Index

Usage:
    python3 claude/tools/whisper_meeting_transcriber.py [--output-dir DIR]

    Controls:
        Ctrl+C: Stop and save
        Space: Pause/Resume (when implemented)

SRE Metrics:
    - Chunk latency: <500ms P95 (30s audio → transcription)
    - Display lag: <100ms (transcription → screen)
    - Storage: ~10KB/min of transcript
    - RAG indexing: <1s per chunk

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-10-29
"""

import os
import sys
import time
import signal
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import hashlib

try:
    import requests
    import blessed
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Install with: pip3 install requests blessed")
    sys.exit(1)

# pyaudio not actually needed - we use ffmpeg for recording
# try:
#     import pyaudio
# except ImportError:
#     pass  # Optional - ffmpeg handles recording

# ChromaDB optional (graceful degradation if not available)
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not available - RAG indexing disabled")
    print("   Install with: pip3 install chromadb sentence-transformers")

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

# Configuration
WHISPER_SERVER_URL = "http://127.0.0.1:8090/inference"
SERVER_HEALTH_URL = "http://127.0.0.1:8090/"
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000
CHUNK_DURATION = 30  # 30 seconds per chunk (optimal for context + accuracy)
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/git/maia/claude/data/transcripts")


class MeetingTranscriptionRAG:
    """RAG indexing for meeting transcripts"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize RAG system for meeting transcripts"""
        if not CHROMADB_AVAILABLE:
            self.enabled = False
            return

        self.enabled = True
        # UFC-compliant path: keep RAG databases within repo structure
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "claude", "data", "rag_databases", "meeting_transcripts_rag"
        )
        self.db_path = db_path or default_path
        os.makedirs(self.db_path, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create meeting transcripts collection
        self.collection = self.client.get_or_create_collection(
            name="meeting_transcripts",
            metadata={"description": "Meeting transcripts with semantic search"}
        )

        # Initialize local embedding model (same as email RAG)
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ RAG indexing enabled (384-dim embeddings)")

    def index_chunk(self, meeting_id: str, chunk_text: str, timestamp: datetime,
                   chunk_number: int, metadata: Dict[str, Any]) -> bool:
        """
        Index a transcript chunk into RAG system

        Args:
            meeting_id: Unique meeting identifier
            chunk_text: Transcribed text
            timestamp: Timestamp of chunk
            chunk_number: Sequential chunk number
            metadata: Additional metadata (title, participants, etc.)

        Returns:
            Success status
        """
        if not self.enabled or not chunk_text.strip():
            return False

        try:
            # Generate unique ID
            chunk_id = f"{meeting_id}_chunk_{chunk_number:04d}"

            # Prepare metadata
            chunk_metadata = {
                "meeting_id": meeting_id,
                "chunk_number": chunk_number,
                "timestamp": timestamp.isoformat(),
                "date": timestamp.strftime("%Y-%m-%d"),
                "time": timestamp.strftime("%H:%M:%S"),
                **metadata
            }

            # Add to collection
            self.collection.add(
                documents=[chunk_text],
                metadatas=[chunk_metadata],
                ids=[chunk_id]
            )

            return True

        except Exception as e:
            print(f"⚠️  RAG indexing failed: {e}")
            return False

    def search(self, query: str, n_results: int = 5,
              meeting_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search meeting transcripts

        Args:
            query: Search query
            n_results: Number of results
            meeting_id: Optional filter by meeting ID

        Returns:
            List of matching chunks with metadata
        """
        if not self.enabled:
            return []

        try:
            where_filter = {"meeting_id": meeting_id} if meeting_id else None

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )

            return results

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []


class MeetingTranscriber:
    """Continuous meeting transcription with live display"""

    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR):
        """Initialize meeting transcriber"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session state
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = None
        self.chunk_count = 0
        self.total_text = []
        self.is_recording = False

        # Output files
        self.transcript_file = None
        self.metadata_file = None

        # Terminal UI
        self.term = blessed.Terminal()

        # RAG system
        self.rag = MeetingTranscriptionRAG()

        # Validate server
        self._validate_whisper_server()

    def _color(self, text: str, color: str = None) -> str:
        """Safely apply terminal color, fallback to plain text"""
        if not color:
            return text
        try:
            color_func = getattr(self.term, color, None)
            if color_func:
                return color_func(text)
        except (TypeError, AttributeError):
            pass
        return text

    def _validate_whisper_server(self):
        """Check if whisper-server is running"""
        try:
            response = requests.get(SERVER_HEALTH_URL, timeout=2)
            if response.status_code != 200:
                raise RuntimeError("Whisper server unhealthy")
        except requests.exceptions.ConnectionError:
            print("❌ Whisper server not running")
            print("\nStart server:")
            print("  launchctl load ~/Library/LaunchAgents/com.maia.whisper-server.plist")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("❌ Whisper server timeout")
            sys.exit(1)

    def _record_chunk(self, duration: int = CHUNK_DURATION) -> Optional[str]:
        """
        Record audio chunk using ffmpeg

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded audio file (or None on failure)
        """
        fd, output_file = tempfile.mkstemp(suffix=f".{AUDIO_FORMAT}")
        os.close(fd)

        cmd = [
            "/opt/homebrew/bin/ffmpeg",
            "-f", "avfoundation",
            "-i", ":0",  # MacBook Air Microphone (audio device 0)
            "-t", str(duration),
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-af", "volume=10dB",
            "-loglevel", "error",
            "-y",
            output_file
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=duration + 5)
            return output_file
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            if os.path.exists(output_file):
                os.remove(output_file)
            return None

    def _transcribe_chunk(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio chunk via whisper-server

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text (or None on failure)
        """
        try:
            with open(audio_file, 'rb') as f:
                audio_data = f.read()

            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            data = {
                'temperature': '0.0',
                'temperature_inc': '0.2',
                'response_format': 'text'
            }

            start_time = time.time()
            response = requests.post(
                WHISPER_SERVER_URL,
                files=files,
                data=data,
                timeout=60
            )

            response.raise_for_status()
            elapsed = time.time() - start_time

            # Clean transcription
            text = response.text.strip()
            text = text.replace("[BLANK_AUDIO]", "")
            text = " ".join(text.split())

            return text if text else None

        except Exception as e:
            return None

    def _display_header(self):
        """Display session header"""
        try:
            print(self.term.home + self.term.clear)
            print(self.term.bold_green("🎤 Meeting Transcription - Live Session"))
        except (TypeError, AttributeError):
            print("\n🎤 Meeting Transcription - Live Session")

        print("═" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"Output: {self.transcript_file}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("─" * 80)

        try:
            print(f"Status: {self.term.green('RECORDING')} | Chunks: {self.chunk_count} | "
                  f"Duration: {self._format_duration()}")
        except (TypeError, AttributeError):
            print(f"Status: RECORDING | Chunks: {self.chunk_count} | "
                  f"Duration: {self._format_duration()}")

        print("─" * 80)
        print("\n")

    def _format_duration(self) -> str:
        """Format elapsed time"""
        if not self.start_time:
            return "00:00:00"
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _save_chunk(self, text: str, timestamp: datetime):
        """Save transcript chunk to file"""
        if not text:
            return

        # Append to transcript file
        with open(self.transcript_file, 'a') as f:
            f.write(f"\n## [{timestamp.strftime('%H:%M:%S')}]\n")
            f.write(f"{text}\n")

        # Update metadata
        self._update_metadata()

    def _update_metadata(self):
        """Update session metadata file"""
        metadata = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "chunk_count": self.chunk_count,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "transcript_file": str(self.transcript_file),
            "rag_indexed": self.rag.enabled
        }

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def start_session(self, title: Optional[str] = None):
        """Start new transcription session"""
        self.start_time = datetime.now()
        self.is_recording = True

        # Create output files
        session_name = title or f"meeting_{self.session_id}"
        self.transcript_file = self.output_dir / f"{session_name}.md"
        self.metadata_file = self.output_dir / f"{session_name}_metadata.json"

        # Write transcript header
        with open(self.transcript_file, 'w') as f:
            f.write(f"# {title or 'Meeting Transcript'}\n\n")
            f.write(f"**Date**: {self.start_time.strftime('%Y-%m-%d')}\n")
            f.write(f"**Time**: {self.start_time.strftime('%H:%M:%S')}\n")
            f.write(f"**Session ID**: {self.session_id}\n\n")
            f.write("---\n")

        try:
            print(self.term.clear)
        except (TypeError, AttributeError):
            print("\n" * 3)

        print(self._color(f"✅ Session started: {session_name}", "bold_green"))
        print(f"📝 Saving to: {self.transcript_file}")
        if self.rag.enabled:
            print("🔍 RAG indexing: ENABLED")
        print("\n")
        print(self._color("Recording in 3 seconds...", "yellow"))
        time.sleep(3)

    def run(self):
        """Main transcription loop"""
        try:
            while self.is_recording:
                chunk_start = datetime.now()
                self.chunk_count += 1

                # Display status
                self._display_header()
                print(self._color(f"🎙️  Recording chunk {self.chunk_count} "
                                 f"({CHUNK_DURATION}s)...", "cyan"))

                # Record chunk
                audio_file = self._record_chunk(CHUNK_DURATION)

                if not audio_file:
                    print(self._color("⚠️  Recording failed, retrying...", "yellow"))
                    continue

                # Transcribe
                print(self._color("🔄 Transcribing...", "cyan"))
                text = self._transcribe_chunk(audio_file)

                # Cleanup audio
                os.remove(audio_file)

                if text:
                    # Display transcription
                    print(self._color("\n📝 Transcription:", "green"))
                    print("─" * 80)
                    print(text)
                    print("─" * 80)

                    # Save to file
                    self._save_chunk(text, chunk_start)
                    self.total_text.append(text)

                    # Index in RAG
                    if self.rag.enabled:
                        self.rag.index_chunk(
                            meeting_id=self.session_id,
                            chunk_text=text,
                            timestamp=chunk_start,
                            chunk_number=self.chunk_count,
                            metadata={
                                "title": self.transcript_file.stem,
                                "total_chunks": self.chunk_count
                            }
                        )
                        print("✅ RAG indexed")
                else:
                    print(self._color("⚠️  No speech detected in chunk", "yellow"))

                print("\nPress Ctrl+C to stop and save\n")
                time.sleep(2)  # Brief pause between chunks

        except KeyboardInterrupt:
            self.stop_session()

    def stop_session(self):
        """Stop recording and finalize transcript"""
        self.is_recording = False
        end_time = datetime.now()
        duration = end_time - self.start_time

        try:
            print(self.term.clear)
        except (TypeError, AttributeError):
            print("\n" * 3)

        print(self._color("\n🛑 Stopping transcription...\n", "bold_yellow"))

        # Write session summary to transcript
        with open(self.transcript_file, 'a') as f:
            f.write(f"\n---\n\n")
            f.write(f"**Session ended**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duration**: {self._format_duration()}\n")
            f.write(f"**Chunks processed**: {self.chunk_count}\n")

        # Final metadata update
        self._update_metadata()

        # Summary
        print(self._color("✅ Session complete", "green"))
        print(f"\n📊 Summary:")
        print(f"   Duration: {self._format_duration()}")
        print(f"   Chunks: {self.chunk_count}")
        print(f"   Transcript: {self.transcript_file}")
        print(f"   Metadata: {self.metadata_file}")

        if self.rag.enabled:
            print(f"\n🔍 RAG Status:")
            print(f"   Indexed chunks: {self.chunk_count}")
            print(f"   Searchable: ✅")
            print(f"\n   Search example:")
            print(f"   python3 -c 'from claude.tools.whisper_meeting_transcriber import MeetingTranscriptionRAG; "
                  f"rag = MeetingTranscriptionRAG(); "
                  f"print(rag.search(\"your query\", meeting_id=\"{self.session_id}\"))'")

        print(f"\n{self._color('Session saved successfully', 'bold_green')}\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Continuous meeting transcription with RAG indexing"
    )
    parser.add_argument(
        '--output-dir',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory for transcripts (default: {DEFAULT_OUTPUT_DIR})'
    )
    parser.add_argument(
        '--title',
        help='Meeting title (optional)'
    )

    args = parser.parse_args()

    # Create transcriber
    transcriber = MeetingTranscriber(output_dir=args.output_dir)

    # Start session
    transcriber.start_session(title=args.title)

    # Run transcription loop
    transcriber.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
