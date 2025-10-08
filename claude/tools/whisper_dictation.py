#!/usr/bin/env python3
"""
Whisper Dictation Tool - Local speech-to-text using whisper.cpp

Provides low-latency, privacy-preserving dictation using locally-hosted
Whisper small model (466MB, 95% accuracy, 1.5-2.5s latency on M4).

Usage:
    python3 claude/tools/whisper_dictation.py
    # Records audio until silence detected, transcribes, copies to clipboard

SRE Metrics:
    - Target Latency: <2.5s P95
    - Target Accuracy: >95% WER
    - Availability: 100% (no network dependency)
"""

import os
import sys
import subprocess
import tempfile
import time
import pyperclip
from pathlib import Path

# Configuration
WHISPER_BIN = "/opt/homebrew/Cellar/whisper-cpp/1.8.0/bin/whisper-cli"
MODEL_PATH = os.path.expanduser("~/.maia/whisper-models/ggml-small.bin")
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000  # Whisper expects 16kHz

class WhisperDictation:
    """Local Whisper-based dictation system"""

    def __init__(self):
        self.validate_setup()

    def validate_setup(self):
        """Ensure whisper-cli and model exist"""
        if not os.path.exists(WHISPER_BIN):
            raise FileNotFoundError(
                f"whisper-cli not found at {WHISPER_BIN}\n"
                f"Install: brew install whisper-cpp"
            )

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Whisper small model not found at {MODEL_PATH}\n"
                f"Download: curl -L -o {MODEL_PATH} "
                f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
            )

    def record_audio(self, duration_seconds=30, output_file=None):
        """
        Record audio from default microphone using sox

        Args:
            duration_seconds: Maximum recording duration (stops on silence)
            output_file: Path to save audio (temp file if None)

        Returns:
            Path to recorded audio file
        """
        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix=f".{AUDIO_FORMAT}")
            os.close(fd)

        print("🎤 Recording... (speak now, auto-stops on silence)")

        # Use sox for recording with silence detection
        # Stops when 2 seconds of silence detected at <2% audio level
        cmd = [
            "sox", "-d",  # Default audio device
            "-r", str(SAMPLE_RATE),  # 16kHz sample rate
            "-c", "1",  # Mono
            "-b", "16",  # 16-bit depth
            output_file,
            "silence", "1", "0.1", "2%",  # Start after 0.1s of audio >2%
            "1", "2.0", "2%",  # Stop after 2s of silence <2%
            "trim", "0", str(duration_seconds)  # Max duration
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ Recording complete")
            return output_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Recording failed: {e.stderr.decode()}")
        except FileNotFoundError:
            raise RuntimeError(
                "sox not found. Install with: brew install sox"
            )

    def transcribe(self, audio_file):
        """
        Transcribe audio file using whisper-cli

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        print("🔄 Transcribing...")
        start_time = time.time()

        cmd = [
            WHISPER_BIN,
            "-m", MODEL_PATH,
            "-f", audio_file,
            "-l", "en",  # English language
            "-np",  # No prints (just results)
            "-nt",  # No timestamps
            "--no-gpu"  # CPU only for now (Metal support coming)
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            elapsed = time.time() - start_time

            # Extract transcription (whisper-cli outputs to stdout)
            transcription = result.stdout.strip()

            # Remove common whisper artifacts
            transcription = self.clean_transcription(transcription)

            print(f"✅ Transcribed in {elapsed:.2f}s")

            return transcription

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Transcription failed: {e.stderr}"
            )

    def clean_transcription(self, text):
        """Remove common Whisper transcription artifacts"""
        # Remove [BLANK_AUDIO] markers
        text = text.replace("[BLANK_AUDIO]", "")

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def dictate(self):
        """
        Complete dictation workflow:
        1. Record audio
        2. Transcribe
        3. Copy to clipboard
        4. Cleanup temp files

        Returns:
            Transcribed text
        """
        audio_file = None

        try:
            # Record audio
            audio_file = self.record_audio()

            # Transcribe
            transcription = self.transcribe(audio_file)

            if not transcription:
                print("⚠️  No speech detected")
                return ""

            # Copy to clipboard
            pyperclip.copy(transcription)
            print(f"📋 Copied to clipboard: {transcription[:100]}...")

            return transcription

        finally:
            # Cleanup temp audio file
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)


def main():
    """CLI entry point"""
    try:
        dictation = WhisperDictation()
        text = dictation.dictate()

        if text:
            print(f"\n📝 Transcription:\n{text}\n")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
