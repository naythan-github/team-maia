#!/usr/bin/env python3
"""
Whisper Dictation - Python sounddevice version (works with USB audio devices)

Uses sounddevice library which handles macOS USB audio permissions better than ffmpeg.
"""

import os
import sys
import tempfile
import time
import requests
import pyperclip
import sounddevice as sd
import soundfile as sf
import numpy as np

# Configuration
WHISPER_SERVER_URL = "http://127.0.0.1:8090/inference"
SERVER_HEALTH_URL = "http://127.0.0.1:8090/"
SAMPLE_RATE = 16000
DURATION = 5  # seconds

class WhisperDictationClient:
    """Client for whisper-server using sounddevice for recording"""

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
                "Check status:\n"
                "  bash ~/git/maia/claude/commands/whisper_dictation_status.sh"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Whisper server timeout (may be loading model)")

    def record_audio(self, duration=DURATION):
        """
        Record audio using sounddevice (default input device)

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded audio file
        """
        print(f"🎤 Recording... (speak now, {duration} seconds)")

        try:
            # Record audio using default input device
            recording = sd.rec(
                int(duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait until recording is finished

            print("✅ Recording complete")

            # Save to temp file
            fd, output_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

            sf.write(output_file, recording, SAMPLE_RATE)

            return output_file

        except Exception as e:
            raise RuntimeError(f"Recording failed: {e}")

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

        return text.strip()

    def run(self):
        """Main workflow: record, transcribe, copy to clipboard"""
        try:
            # Record audio
            audio_file = self.record_audio()

            # Transcribe
            transcription = self.transcribe(audio_file)

            # Clean up
            os.unlink(audio_file)

            if not transcription:
                print("⚠️  No speech detected")
                return

            # Copy to clipboard
            pyperclip.copy(transcription)
            print(f"📋 Copied to clipboard: {transcription}")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    client = WhisperDictationClient()
    client.run()
