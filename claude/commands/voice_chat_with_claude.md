# Voice Chat with Claude

## Quick Start

### Start Voice Chat Session
```bash
# Launch interactive voice session
./voice_chat

# Or run directly
python3 claude/tools/voice_to_claude.py --interactive
```

### How It Works
1. **Speak** → Records your voice using microphone
2. **Transcribe** → Local Whisper converts speech to text (private, no cloud)
3. **Format** → Prepares text for Claude conversation
4. **Copy** → Text goes to clipboard, ready to paste into Claude Code

### Usage Flow
1. Run `./voice_chat`
2. Press Enter when ready to speak
3. Speak your question/request
4. Wait for transcription
5. Copy the formatted text and paste into Claude Code
6. Get Claude's response
7. Repeat for ongoing conversation

## Voice Commands in Session

### Recording
- **Press Enter** → Start voice recording
- **Speak naturally** → Recording auto-stops after silence
- **Ctrl+C during recording** → Stop recording manually

### Session Commands
- **Type 'stats'** → Show session statistics
- **Type 'file <path>'** → Transcribe an audio file instead
- **Type 'quit'** → Exit voice session

### Example Session
```
💬 Ready for voice input (or type command): [Press Enter]
🎙️  Recording voice input (max 30s)...
💬 Speak now! Recording will auto-stop after silence...

✅ Recording completed
🧠 Transcribing with local Whisper...

============================================================
🎯 TRANSCRIPTION RESULT
============================================================
📝 Text: What's the current weather in Perth?
🎯 Confidence: 89.0%
⏱️  Duration: 3.2s
🚀 Processing: 1850ms

📋 Formatted for Claude:
'What's the current weather in Perth?'
✅ Copied to clipboard - paste into Claude Code
```

## Advanced Usage

### Different Model Sizes
```bash
# Fastest transcription (lower accuracy)
python3 claude/tools/voice_to_claude.py --model tiny --interactive

# Most accurate (slower processing)  
python3 claude/tools/voice_to_claude.py --model large --interactive

# Balanced (recommended)
python3 claude/tools/voice_to_claude.py --model medium --interactive
```

### One-off Voice Input
```bash
# Record 10 seconds of audio and transcribe
python3 claude/tools/voice_to_claude.py --record 10

# Transcribe existing audio file
python3 claude/tools/voice_to_claude.py --file meeting_recording.wav
```

### With Auto-formatting
```bash
# Automatically format for Claude Code
python3 claude/tools/voice_to_claude.py --interactive --auto-send
```

## Tips for Best Results

### Audio Quality
- **Speak clearly** and at normal pace
- **Reduce background noise** when possible
- **Position microphone** 6-12 inches from mouth
- **Pause briefly** between thoughts for better transcription

### Voice Input Best Practices
- **Use natural speech** - no need to speak robotically
- **Speak complete thoughts** - Whisper works better with full sentences
- **Avoid filler words** - "um", "uh" may affect transcription quality
- **End with clear silence** - helps auto-stop detection

### Transcription Accuracy
- **English**: Highest accuracy (primary training language)
- **Other languages**: 99 languages supported with auto-detection
- **Technical terms**: May need spelling out or clarification
- **Names/URLs**: Consider typing these manually

## Privacy & Performance

### Complete Privacy
- **Local processing only** - No cloud services used
- **No internet required** - Works completely offline
- **Automatic cleanup** - Temporary audio files deleted
- **No data persistence** - Audio not stored permanently

### M4 Optimization
- **GPU acceleration** - Uses Apple M4 Neural Engine
- **Fast processing** - ~2-3 seconds for typical voice input
- **Memory efficient** - Optimized for unified memory
- **Battery friendly** - Efficient local processing

## Integration with Claude Code

### Current Workflow
1. Voice → Transcription → Clipboard → Paste into Claude Code
2. Get Claude's response
3. Continue conversation

### Future Enhancements (Planned)
- **Direct integration** with Claude Code interface
- **Voice responses** from Claude (text-to-speech)
- **Continuous conversation** without copy/paste
- **Context awareness** across voice sessions

## Troubleshooting

### Microphone Issues
```bash
# Test microphone with simple recording
sox -d test_recording.wav trim 0 5
# Play back to verify
play test_recording.wav
```

### No Audio Detected
- Check microphone permissions in System Preferences
- Speak louder or closer to microphone
- Reduce background noise
- Try manual stop with Ctrl+C

### Poor Transcription Quality
- Use larger model: `--model large`
- Speak more clearly and slowly
- Reduce background noise
- Check audio quality with test recording

### SoX Installation Issues
```bash
# Reinstall SoX if needed
brew uninstall sox
brew install sox
```

## Related Tools
- **Local Whisper Transcriber**: Core transcription engine
- **Meeting Intelligence**: Voice-enabled meeting processing
- **Research Tools**: Voice note-taking for research
- **Personal Assistant**: Voice commands for Maia ecosystem