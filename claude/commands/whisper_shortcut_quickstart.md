# Whisper Dictation - Quick Start
## Press Option+Escape → Speak → Paste

---

## ONE-TIME SETUP (2 minutes)

### Grant Accessibility Permission:
1. Open **System Settings** (Apple logo → System Settings)
2. Click **"Privacy & Security"** (left sidebar)
3. Click **"Accessibility"** (scroll down on right)
4. Find **"skhd"** in list → Toggle **ON**
5. Run: `skhd --restart-service`

**That's it!** ✅

---

## USAGE (every time)

1. **Press**: Option+Escape (⌥ esc)
2. **Speak**: "This is a test message"
3. **Wait**: 2 seconds silence
4. **Paste**: Cmd+V

**Text appears!**

---

## TROUBLESHOOTING

### Nothing happens?
```bash
# Run diagnostic:
bash claude/commands/test_whisper_shortcut.sh

# Check skhd running:
launchctl list | grep skhd

# Check Whisper server running:
curl http://127.0.0.1:8090/health
```

### Microphone permission needed?
1. System Settings → Privacy & Security → Microphone
2. Find **"Terminal"** → Toggle ON

---

## FILES

- **Full docs**: `claude/commands/whisper_keyboard_shortcut_final.md`
- **Config**: `~/.skhdrc`
- **Test**: `claude/commands/test_whisper_shortcut.sh`

---

## COMMANDS

```bash
# Restart skhd
skhd --restart-service

# Check status
launchctl list | grep skhd

# View logs
tail -f /tmp/skhd_$USER.out.log

# Test manually
/usr/bin/python3 claude/tools/whisper_dictation_server.py
```

**Ready!** 🎤
