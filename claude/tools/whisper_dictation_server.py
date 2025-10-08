#!/usr/bin/env python3
"""
Whisper Dictation Server Client - Fast speech-to-text via persistent server

Uses whisper-server with keep-alive model loading for <1s inference latency.

Architecture:
    - whisper-server: Background daemon with loaded model (500MB RAM resident)
    - This script: Client that records audio and sends to server
    - First request: ~5s (model load + inference)
    - Subsequent: <1s (inference only, model warm)

Usage:
    python3 claude/tools/whisper_dictation_server.py
    # Records audio, sends to server, copies to clipboard

SRE Metrics:
    - First-use latency: ~5s (cold start)
    - Steady-state latency: <1s P95 (warm model)
    - Availability: 99.9% (local service)
"""

import os
import sys
import subprocess
import tempfile
import time
import requests
import pyperclip
from pathlib import Path

# Configuration
WHISPER_SERVER_URL = "http://127.0.0.1:8090/inference"
SERVER_HEALTH_URL = "http://127.0.0.1:8090/health"
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000

class WhisperDictationClient:
    """Client for whisper-server based dictation"""

    def __init__(self):
        self.validate_server()

    def validate_server(self):
        """Check if whisper-server is running"""
        try:
            response = requests.get(SERVER_HEALTH_URL, timeout=2)
            if response.status_code != 200:
                raise RuntimeError("Whisper server unhealthy")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "❌ Whisper server not running.\n\n"
                "Start server:\n"
                "  launchctl load ~/Library/LaunchAgents/com.maia.whisper-server.plist\n\n"
                "Or start manually:\n"
                "  bash claude/commands/start_whisper_server.sh\n\n"
                "Check status:\n"
                "  curl http://127.0.0.1:8080/health"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Whisper server timeout (may be loading model)")

    def record_audio(self, duration_seconds=30, output_file=None):
        """
        Record audio from default microphone using sox

        Args:
            duration_seconds: Maximum recording duration
            output_file: Path to save audio (temp file if None)

        Returns:
            Path to recorded audio file
        """
        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix=f".{AUDIO_FORMAT}")
            os.close(fd)

        print("🎤 Recording... (speak now, auto-stops on silence)")

        # sox with silence detection
        cmd = [
            "sox", "-d",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-b", "16",
            output_file,
            "silence", "1", "0.1", "2%",
            "1", "2.0", "2%",
            "trim", "0", str(duration_seconds)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ Recording complete")
            return output_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Recording failed: {e.stderr.decode()}")

    def transcribe(self, audio_file):
        """
        Transcribe audio via whisper-server

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        print("🔄 Transcribing...")
        start_time = time.time()

        # Read audio file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()

        # Send to server
        files = {'file': ('audio.wav', audio_data, 'audio/wav')}
        data = {
            'temperature': '0.0',
            'temperature_inc': '0.2',
            'response_format': 'text'
        }

        try:
            response = requests.post(
                WHISPER_SERVER_URL,
                files=files,
                data=data,
                timeout=30
            )

            response.raise_for_status()

            elapsed = time.time() - start_time

            # Extract transcription
            transcription = response.text.strip()
            transcription = self.clean_transcription(transcription)

            print(f"✅ Transcribed in {elapsed:.2f}s")

            return transcription

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Transcription failed: {e}")

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
        2. Send to whisper-server
        3. Copy to clipboard
        4. Cleanup

        Returns:
            Transcribed text
        """
        audio_file = None

        try:
            # Record
            audio_file = self.record_audio()

            # Transcribe via server
            transcription = self.transcribe(audio_file)

            if not transcription:
                print("⚠️  No speech detected")
                return ""

            # Copy to clipboard
            pyperclip.copy(transcription)
            print(f"📋 Copied to clipboard: {transcription[:100]}...")

            return transcription

        finally:
            # Cleanup
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)


def main():
    """CLI entry point"""
    try:
        client = WhisperDictationClient()
        text = client.dictate()

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
