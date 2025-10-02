# Whisper Speech-to-Text Command

## Overview
Local speech-to-text transcription using whisper-cpp with M4 GPU acceleration for privacy-preserving voice processing.

## Core Capabilities
- **Local Processing**: No cloud dependencies, complete privacy
- **M4 GPU Acceleration**: Optimized for Apple Silicon performance
- **Multiple Formats**: JSON, TXT, SRT, VTT output support
- **Multi-language**: Support for 99 languages with auto-detection
- **Real-time Processing**: Fast transcription with sub-3 second processing

## Usage

### Transcribe Audio File
```bash
# Basic transcription
python3 claude/tools/local_whisper_transcriber.py --file audio.wav

# With specific language and format
python3 claude/tools/local_whisper_transcriber.py --file recording.mp3 --language en --format srt

# Translate to English
python3 claude/tools/local_whisper_transcriber.py --file french_audio.wav --translate --format txt

# Save output to file
python3 claude/tools/local_whisper_transcriber.py --file meeting.m4a --format json --output transcription.json
```

### Quick Commands
```bash
# Use different model sizes for speed/accuracy trade-off
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model tiny    # Fastest
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model small   # Balanced
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model medium  # Default
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model large   # Most accurate
```

### Supported Audio Formats
- **WAV**: Uncompressed audio (best quality)
- **MP3**: Compressed audio
- **FLAC**: Lossless compression
- **OGG**: Open source format
- **M4A**: AAC compressed audio

### Output Formats

#### JSON (Structured)
```json
{
  "text": "Transcribed text here",
  "confidence": 0.85,
  "duration_seconds": 11.0,
  "processing_time_ms": 2000,
  "model_used": "whisper-cpp-medium",
  "timestamp": "2025-09-21T20:15:00",
  "segments": [...],
  "metadata": {...}
}
```

#### SRT (Subtitles)
```
1
00:00:00,000 --> 00:00:05,000
First segment of transcribed text

2
00:00:05,000 --> 00:00:10,000
Second segment of transcribed text
```

#### TXT (Plain Text)
```
Transcribed text without timestamps or formatting
```

#### VTT (WebVTT)
```
WEBVTT

00:00:00.000 --> 00:00:05.000
First segment of transcribed text

00:00:05.000 --> 00:00:10.000
Second segment of transcribed text
```

## Performance Characteristics

### M4 GPU Acceleration
- **Hardware**: Apple M4 Neural Engine + GPU
- **Memory**: Unified memory architecture (up to 17GB available)
- **Speed**: ~2-3 seconds for 11 seconds of audio (medium model)
- **Efficiency**: Local processing, no network latency

### Model Performance Comparison
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny  | 39MB | Fastest | Good | Quick notes, real-time |
| base  | 74MB | Fast | Better | General purpose |
| small | 244MB | Medium | Good | Balanced performance |
| medium| 769MB | Slower | Better | Default recommendation |
| large | 1550MB | Slowest | Best | Maximum accuracy |

## Integration with Maia Ecosystem

### Agent Integration
```python
# Use in agents for voice-enabled workflows
from claude.tools.local_whisper_transcriber import LocalWhisperTranscriber

transcriber = LocalWhisperTranscriber(model_size="medium")
result = transcriber.transcribe_audio("meeting_recording.wav")
meeting_text = result.text
```

### Command Chaining
```bash
# Chain with other Maia tools
python3 claude/tools/local_whisper_transcriber.py --file interview.wav --format txt --output interview.txt
python3 claude/tools/enhanced_maia_research.py --source interview.txt --topic "key insights"
```

## Privacy & Security

### Local Processing Benefits
- **Zero Cloud Dependencies**: All processing happens locally
- **Complete Privacy**: Audio never leaves your device
- **No API Keys**: No external service authentication required
- **Offline Capable**: Works without internet connection

### Data Handling
- **Temporary Files**: Automatically cleaned up after processing
- **No Persistence**: Audio data not stored unless explicitly requested
- **Memory Efficient**: Optimized for M4 unified memory architecture

## Advanced Configuration

### Language Detection
```bash
# Auto-detect language
python3 claude/tools/local_whisper_transcriber.py --file multilingual.wav --language auto

# Specific languages
--language en    # English
--language es    # Spanish
--language fr    # French
--language de    # German
--language ja    # Japanese
--language zh    # Chinese
# ... 99 total languages supported
```

### Quality Optimization
```bash
# High accuracy (slower)
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model large

# Fast processing (lower accuracy)  
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model tiny

# Balanced approach (recommended)
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model medium
```

## Troubleshooting

### Common Issues

#### Model Not Found
```bash
# Check model location
ls -la ~/whisper-models/
# Download models if needed (models auto-download on first use)
```

#### Audio Format Issues
```bash
# Convert audio format using ffmpeg
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav
# Then transcribe
python3 claude/tools/local_whisper_transcriber.py --file output.wav
```

#### Performance Optimization
```bash
# Use smaller model for faster processing
python3 claude/tools/local_whisper_transcriber.py --file audio.wav --model small

# Check GPU acceleration is working (should see "using Metal backend" in output)
```

## Future Enhancements

### Planned Features
- **Streaming Transcription**: Real-time processing of live audio
- **Speaker Diarization**: Identify different speakers in conversations
- **Voice Commands**: Direct integration with Maia voice control
- **Batch Processing**: Transcribe multiple files simultaneously
- **Custom Models**: Support for domain-specific whisper models

### Integration Opportunities
- **Meeting Intelligence**: Automatic meeting transcription and analysis
- **Voice Notes**: Convert voice memos to structured text
- **Interview Processing**: Transcribe and analyze interview recordings
- **Content Creation**: Voice-to-blog post workflows

## Related Tools
- **Ollama Integration**: Use with local LLMs for voice-powered AI interactions
- **Meeting Intelligence**: Enhanced meeting processing with action items
- **Research Tools**: Voice-enabled research note-taking
- **Personal Assistant**: Voice commands for Maia ecosystem