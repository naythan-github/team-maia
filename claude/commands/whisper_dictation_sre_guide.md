# Whisper Dictation System - SRE Operations Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ User presses Cmd+Shift+Space                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ skhd (LaunchAgent: com.koekeishiya.skhd)               │
│ - Listens for global keyboard shortcuts                │
│ - Triggers whisper_dictation_server.py                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ whisper_dictation_server.py                             │
│ - Records 5s audio via ffmpeg (device :0)              │
│ - Sends to whisper-server via HTTP POST                │
│ - Receives transcription                                │
│ - Copies to clipboard (pyperclip)                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ whisper-server (LaunchAgent: com.maia.whisper-server)  │
│ - Runs on port 8090 (127.0.0.1 only)                   │
│ - Model: ggml-base.en.bin (~141MB, ~500MB RAM)         │
│ - GPU: Apple M4 Metal acceleration                      │
│ - Inference: <500ms P95 (warm model)                    │
│ - KeepAlive: true (auto-restart on crash)              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Health Monitor (LaunchAgent: com.maia.whisper-health)  │
│ - Checks server every 30s                               │
│ - Restarts after 3 consecutive failures                │
│ - Logs to whisper-health-monitor.log                   │
└─────────────────────────────────────────────────────────┘
```

## System Status

**Check status:**
```bash
bash ~/git/maia/claude/commands/whisper_dictation_status.sh
```

## LaunchAgents Configuration

### 1. Whisper Server
**Location:** `~/Library/LaunchAgents/com.maia.whisper-server.plist`
**Purpose:** Persistent whisper.cpp server with hot model
**Configuration:**
- Binary: `/opt/homebrew/bin/whisper-server`
- Model: `~/models/whisper/ggml-base.en.bin`
- Port: `8090` (localhost only)
- Threads: `4` (optimal for M4)
- RunAtLoad: `true` (starts on login)
- KeepAlive: `true` (auto-restart on crash)
- ThrottleInterval: `10` (prevent crash loops)

**Logs:**
- stdout: `~/git/maia/claude/data/logs/whisper-server.log`
- stderr: `~/git/maia/claude/data/logs/whisper-server-error.log`

**Management:**
```bash
# Start
launchctl load ~/Library/LaunchAgents/com.maia.whisper-server.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.maia.whisper-server.plist

# Restart
launchctl kickstart -k gui/$(id -u)/com.maia.whisper-server

# Check status
launchctl list | grep whisper-server

# View logs
tail -f ~/git/maia/claude/data/logs/whisper-server.log
```

### 2. Health Monitor
**Location:** `~/Library/LaunchAgents/com.maia.whisper-health.plist`
**Purpose:** Proactive health monitoring and auto-recovery
**Configuration:**
- Script: `~/git/maia/claude/tools/whisper_health_monitor.sh`
- Check interval: `30 seconds`
- Failure threshold: `3 consecutive failures`
- Action: Restart whisper-server via `launchctl kickstart`

**Logs:**
- stdout: `~/git/maia/claude/data/logs/whisper-health-stdout.log`
- stderr: `~/git/maia/claude/data/logs/whisper-health-stderr.log`
- Monitor log: `~/git/maia/claude/data/logs/whisper-health-monitor.log`

**Management:**
```bash
# Start
launchctl load ~/Library/LaunchAgents/com.maia.whisper-health.plist

# Stop
launchctl unload ~/Library/LaunchAgents/com.maia.whisper-health.plist

# View health log
tail -f ~/git/maia/claude/data/logs/whisper-health-monitor.log
```

### 3. skhd (Keyboard Shortcuts)
**Location:** `~/.config/skhd/skhdrc`
**Purpose:** Global keyboard shortcut daemon
**Configuration:**
- Hotkey: `Cmd+Shift+Space`
- Command: `/opt/homebrew/bin/python3 /Users/YOUR_USERNAME/git/maia/claude/tools/whisper_dictation_server.py`

**Management:**
```bash
# Start
skhd --start-service

# Stop
skhd --stop-service

# Restart
skhd --restart-service

# Reload config
skhd --reload

# Check status
launchctl list | grep skhd
```

## Reliability Features

### Auto-Restart on Crash
- **KeepAlive: true** - macOS automatically restarts whisper-server if it crashes
- **ThrottleInterval: 10** - Prevents crash loops (10s delay between restarts)

### Health Monitoring
- **Proactive checks** - Every 30s, health monitor checks server response
- **Failure threshold** - 3 consecutive failures trigger restart
- **Automatic recovery** - No manual intervention needed

### Boot Persistence
- **RunAtLoad: true** - All services start automatically on login
- **No manual startup** - System ready immediately after boot

### Audio Device Resilience
- **ffmpeg device handling** - Robust audio device enumeration
- **Device fallback** - Uses default audio input (device :0)
- **Graceful failures** - Clear error messages if mic unavailable

## Performance Metrics

### Target SLIs (Service Level Indicators)
- **Availability:** 99%+ uptime
- **Latency P50:** <800ms end-to-end (speak → clipboard)
- **Latency P95:** <1.5s end-to-end
- **Inference P95:** <500ms (server processing only)
- **Recovery time:** <30s (worst case, 3 failures × 10s)

### Resource Usage
- **RAM:** ~500MB (whisper-server resident)
- **CPU:** <5% idle, <100% during transcription (4 threads)
- **Disk:** 141MB (model file)
- **Network:** Localhost only (no external traffic)

## Troubleshooting

### Server Not Responding
```bash
# Check if running
launchctl list | grep whisper-server

# View error logs
cat ~/git/maia/claude/data/logs/whisper-server-error.log

# Restart
launchctl kickstart -k gui/$(id -u)/com.maia.whisper-server

# Test endpoint
curl http://127.0.0.1:8090/
```

### Keyboard Shortcut Not Working
```bash
# Check skhd status
launchctl list | grep skhd

# Reload skhd config
skhd --reload

# Test manually
python3 ~/git/maia/claude/tools/whisper_dictation_server.py

# Check Accessibility permissions
# System Settings → Privacy & Security → Accessibility → skhd
```

### Audio Recording Issues
```bash
# List audio devices
/opt/homebrew/bin/ffmpeg -f avfoundation -list_devices true -i ""

# Test recording (5 seconds)
/opt/homebrew/bin/ffmpeg -f avfoundation -i ":0" -t 5 -y /tmp/test.wav

# Check microphone permissions
# System Settings → Privacy & Security → Microphone → Terminal/Python
```

### Health Monitor Not Running
```bash
# Check status
launchctl list | grep whisper-health

# Load if missing
launchctl load ~/Library/LaunchAgents/com.maia.whisper-health.plist

# View logs
tail -f ~/git/maia/claude/data/logs/whisper-health-monitor.log
```

## Maintenance

### Daily Checks (Automated)
- Health monitor runs every 30s
- No manual checks needed

### Weekly Checks (Optional)
```bash
# Review logs for errors
grep -i error ~/git/maia/claude/data/logs/whisper-server-error.log

# Check health monitor activity
tail -50 ~/git/maia/claude/data/logs/whisper-health-monitor.log
```

### Monthly Checks
```bash
# Verify all services running
bash ~/git/maia/claude/commands/whisper_dictation_status.sh

# Check disk space
du -sh ~/models/whisper/

# Review uptime
launchctl list | grep whisper
```

### Updates
```bash
# Update whisper.cpp (if desired)
brew upgrade whisper-cpp

# Download new model (if desired)
cd ~/models/whisper/
curl -L -o ggml-small.en.bin "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin?download=true"

# Update model path in plist if changed
# Edit: ~/Library/LaunchAgents/com.maia.whisper-server.plist
```

## Security

### Network Exposure
- **Localhost only:** Server binds to 127.0.0.1 (not accessible from network)
- **No external traffic:** 100% local processing
- **No cloud uploads:** All transcription happens on-device

### Privacy
- **No logging of audio:** Audio files deleted after transcription
- **No transcription storage:** Text only in clipboard (user controlled)
- **No telemetry:** No data sent to external services

### Permissions Required
- **Microphone access:** Required for audio recording (Terminal/Python)
- **Accessibility access:** Required for skhd keyboard shortcuts

## Expected Reliability: 98%+

### Failure Modes (Mitigated)
1. **Model corruption** → Health monitor detects, restarts service
2. **Audio device issues** → ffmpeg handles gracefully, clear error messages
3. **Port conflicts** → LaunchAgent logs error, won't start
4. **Memory leaks** → KeepAlive + ThrottleInterval limits damage
5. **macOS updates** → Services persist across reboots

### Known Limitations
- **First transcription:** ~2-3s (model warmup)
- **Subsequent:** <1s (hot model)
- **Recording fixed:** 5 seconds (can be adjusted in script)
- **English only:** Using base.en model (multilingual available)

## Quick Reference

### One-Line Commands
```bash
# Status check
bash ~/git/maia/claude/commands/whisper_dictation_status.sh

# Restart everything
launchctl kickstart -k gui/$(id -u)/com.maia.whisper-server && skhd --reload

# Test dictation (manual trigger)
python3 ~/git/maia/claude/tools/whisper_dictation_server.py

# View live logs
tail -f ~/git/maia/claude/data/logs/whisper-server.log

# Stop all services
launchctl unload ~/Library/LaunchAgents/com.maia.whisper-server.plist
launchctl unload ~/Library/LaunchAgents/com.maia.whisper-health.plist
skhd --stop-service
```

## Files Reference

### Configuration Files
- `~/Library/LaunchAgents/com.maia.whisper-server.plist` - Whisper server LaunchAgent
- `~/Library/LaunchAgents/com.maia.whisper-health.plist` - Health monitor LaunchAgent
- `~/.config/skhd/skhdrc` - skhd keyboard shortcuts

### Scripts
- `~/git/maia/claude/tools/whisper_dictation_server.py` - Main dictation client
- `~/git/maia/claude/tools/whisper_health_monitor.sh` - Health monitoring script
- `~/git/maia/claude/commands/whisper_dictation_status.sh` - Status check script

### Logs
- `~/git/maia/claude/data/logs/whisper-server.log` - Server stdout
- `~/git/maia/claude/data/logs/whisper-server-error.log` - Server stderr
- `~/git/maia/claude/data/logs/whisper-health-monitor.log` - Health checks

### Models
- `~/models/whisper/ggml-base.en.bin` - Whisper base English model (141MB)

## Support

For issues or improvements, check:
1. Status script: `whisper_dictation_status.sh`
2. Server logs: `~/git/maia/claude/data/logs/`
3. macOS 26 Specialist Agent for system-level troubleshooting
