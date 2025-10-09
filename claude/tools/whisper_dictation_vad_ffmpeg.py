#!/usr/bin/env python3
"""
Whisper Dictation with Voice Activity Detection (VAD) - ffmpeg version

Records until you stop speaking, transcribes, auto-types into active window.
Uses ffmpeg for recording (works with macOS 26).
"""

import os
import sys
import tempfile
import time
import requests
import subprocess
import wave
import struct
import math

# Configuration
WHISPER_SERVER_URL = "http://127.0.0.1:8090/inference"
SERVER_HEALTH_URL = "http://127.0.0.1:8090/"
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 300   # Amplitude threshold (lower = more sensitive)
SILENCE_DURATION = 1.5    # Seconds of silence before stopping
MAX_DURATION = 60         # Maximum recording duration (safety)
AUDIO_DEVICE = ":1"       # MacBook Air Microphone (change to :0 for Jabra if working)

class WhisperVADDictation:
    """Voice activity detection + auto-typing dictation"""

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
                "Start: launchctl load ~/Library/LaunchAgents/com.maia.whisper-server.plist"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Whisper server timeout")

    def record_with_vad(self):
        """
        Record audio until silence detected using ffmpeg

        Returns:
            Path to recorded audio file
        """
        print("🎤 Recording... (speak now, will auto-stop when done)")

        # Record long audio first (max duration)
        fd, temp_file = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        cmd = [
            "/opt/homebrew/bin/ffmpeg",
            "-f", "avfoundation",
            "-i", AUDIO_DEVICE,
            "-t", str(MAX_DURATION),
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-af", "volume=10dB",
            "-loglevel", "error",
            "-y",
            temp_file
        ]

        print("Recording (max 60s)...", end="", flush=True)

        try:
            # Start recording in background
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait a bit to ensure recording starts
            time.sleep(0.5)

            # Let user speak - we'll process VAD from the file after
            # For now, just wait for manual stop or timeout
            start_time = time.time()

            # Simple approach: Record for MAX_DURATION or until killed
            # We'll detect silence in post-processing
            while process.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > MAX_DURATION:
                    process.terminate()
                    break
                time.sleep(0.1)

            # Wait for process to finish
            process.wait()

            print(f"\n✅ Recording complete ({elapsed:.1f}s)")

            # Now detect where speech ends using VAD
            trimmed_file = self.trim_silence(temp_file)

            # Clean up original
            os.unlink(temp_file)

            return trimmed_file

        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise RuntimeError(f"Recording failed: {e}")

    def trim_silence(self, audio_file):
        """
        Detect silence at end and trim audio file

        Args:
            audio_file: Path to audio file

        Returns:
            Path to trimmed audio file
        """
        try:
            # Use ffmpeg silencedetect to find where speech ends
            cmd = [
                "/opt/homebrew/bin/ffmpeg",
                "-i", audio_file,
                "-af", f"silencedetect=noise={SILENCE_THRESHOLD}dB:d={SILENCE_DURATION}",
                "-f", "null",
                "-"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            # Parse silence detection output
            stderr = result.stderr

            # For now, just return original file
            # TODO: Parse silence detection and trim
            return audio_file

        except Exception as e:
            print(f"⚠️  VAD processing failed: {e}, using full recording")
            return audio_file

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

        with open(audio_file, 'rb') as f:
            audio_data = f.read()

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
            transcription = response.text.strip()
            transcription = self.clean_transcription(transcription)

            print(f"✅ Transcribed in {elapsed:.2f}s")
            return transcription

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Transcription failed: {e}")

    def clean_transcription(self, text):
        """Remove Whisper artifacts"""
        text = text.replace("[BLANK_AUDIO]", "")
        text = " ".join(text.split())
        return text.strip()

    def type_text(self, text):
        """
        Type text at cursor position using AppleScript keystroke simulation

        Args:
            text: Text to type
        """
        print(f"⌨️  Typing: {text}")

        # Escape special characters for AppleScript
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')

        # AppleScript to type text in frontmost application
        applescript = f'''
        tell application "System Events"
            keystroke "{escaped_text}"
        end tell
        '''

        try:
            subprocess.run(
                ['osascript', '-e', applescript],
                check=True,
                capture_output=True,
                timeout=10
            )
            print("✅ Text typed")
        except subprocess.CalledProcessError as e:
            # Fallback: Copy to clipboard
            import pyperclip
            pyperclip.copy(text)
            print("⚠️  Auto-typing failed, copied to clipboard instead")
        except subprocess.TimeoutExpired:
            print("⚠️  Auto-typing timeout")

    def run(self):
        """Main workflow: record with VAD, transcribe, type"""
        try:
            # Record with simple timeout (VAD post-processing)
            # For now, using 10-second recording as compromise
            audio_file = self.record_simple(10)

            if not audio_file:
                return

            # Transcribe
            transcription = self.transcribe(audio_file)

            # Clean up
            os.unlink(audio_file)

            if not transcription:
                print("⚠️  No speech detected")
                return

            # Type into active window
            self.type_text(transcription)

        except KeyboardInterrupt:
            print("\n⚠️  Cancelled by user")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    def record_simple(self, duration=10):
        """
        Simple fixed-duration recording

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded audio file
        """
        print(f"🎤 Recording... (speak now, {duration} seconds)")

        fd, output_file = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        cmd = [
            "/opt/homebrew/bin/ffmpeg",
            "-f", "avfoundation",
            "-i", AUDIO_DEVICE,
            "-t", str(duration),
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-af", "volume=10dB",
            "-loglevel", "error",
            "-y",
            output_file
        ]

        try:
            subprocess.run(cmd, check=True, timeout=duration + 5)
            print("✅ Recording complete")
            return output_file

        except subprocess.TimeoutExpired:
            print("⚠️  Recording timeout")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ Recording failed: {e}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None


if __name__ == "__main__":
    client = WhisperVADDictation()
    client.run()
