#!/usr/bin/env python3
"""
Whisper Dictation with Voice Activity Detection (VAD)

Records until you stop speaking, transcribes, auto-types into active window.
No clipboard, no manual paste, no 5-second limit.
"""

import os
import sys
import tempfile
import time
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
import subprocess
from pathlib import Path

# Configuration
WHISPER_SERVER_URL = "http://127.0.0.1:8090/inference"
SERVER_HEALTH_URL = "http://127.0.0.1:8090/"
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
SILENCE_DURATION = 1.5    # Seconds of silence before stopping
MAX_DURATION = 60         # Maximum recording duration (safety)
CHUNK_DURATION = 0.5      # Process audio in 0.5s chunks

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

    def calculate_rms(self, audio_chunk):
        """Calculate RMS (root mean square) amplitude"""
        return np.sqrt(np.mean(np.square(audio_chunk)))

    def record_with_vad(self):
        """
        Record audio until silence detected

        Returns:
            Path to recorded audio file
        """
        print("🎤 Recording... (speak now, will auto-stop when done)")

        chunks = []
        silent_chunks = 0
        chunk_size = int(CHUNK_DURATION * SAMPLE_RATE)
        silence_threshold_chunks = int(SILENCE_DURATION / CHUNK_DURATION)

        try:
            # Start recording stream
            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                blocksize=chunk_size
            )
            stream.start()

            start_time = time.time()
            has_speech = False

            while True:
                # Read audio chunk
                audio_chunk, overflowed = stream.read(chunk_size)

                if overflowed:
                    print("⚠️  Audio buffer overflow (speaking too fast)")

                # Calculate volume
                rms = self.calculate_rms(audio_chunk)

                # Store chunk
                chunks.append(audio_chunk)

                # Check for speech
                if rms > SILENCE_THRESHOLD:
                    has_speech = True
                    silent_chunks = 0
                    print("🔊", end="", flush=True)
                else:
                    if has_speech:  # Only count silence after we've detected speech
                        silent_chunks += 1
                        print(".", end="", flush=True)

                # Stop conditions
                elapsed = time.time() - start_time

                if has_speech and silent_chunks >= silence_threshold_chunks:
                    print(f"\n✅ Recording complete ({elapsed:.1f}s)")
                    break

                if elapsed > MAX_DURATION:
                    print(f"\n⚠️  Max duration reached ({MAX_DURATION}s)")
                    break

            stream.stop()
            stream.close()

            if not has_speech:
                print("⚠️  No speech detected")
                return None

            # Combine chunks
            recording = np.concatenate(chunks, axis=0)

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
            # Fallback: Copy to clipboard (user can paste manually)
            import pyperclip
            pyperclip.copy(text)
            print("⚠️  Auto-typing failed, copied to clipboard instead")
            print(f"   Error: {e.stderr.decode()}")
        except subprocess.TimeoutExpired:
            print("⚠️  Auto-typing timeout")

    def run(self):
        """Main workflow: record with VAD, transcribe, type"""
        try:
            # Record until silence
            audio_file = self.record_with_vad()

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

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    client = WhisperVADDictation()
    client.run()
