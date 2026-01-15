# Whisper Dictation - Final Setup Guide
## Keyboard Shortcut: Ctrl+Option+Space

### Step-by-Step Setup (2 minutes)

---

## Step 1: Open Shortcuts App
1. Press **Cmd+Space** (Spotlight)
2. Type: **Shortcuts**
3. Press **Enter**

---

## Step 2: Create New Shortcut
1. Click the **"+"** button (top right corner)
2. You'll see a blank shortcut editor

---

## Step 3: Add Shell Script Action
1. In the search box (right side), type: **"Run Shell Script"**
2. Click on **"Run Shell Script"** to add it
3. You'll see a gray box with "Shell Script" field

---

## Step 4: Paste the Script
Click in the script box and paste this **exact text**:

```bash
cd /Users/YOUR_USERNAME/git/maia
/opt/homebrew/bin/python3 claude/tools/whisper_dictation_server.py
```

---

## Step 5: Name Your Shortcut
1. Click on **"Shortcut Name"** (top of screen)
2. Change it to: **Whisper Dictation**
3. Press Enter

---

## Step 6: Add Keyboard Shortcut
1. Click the **ⓘ (info icon)** in the top right corner
2. Toggle ON: **"Use as Quick Action"**
3. Click **"Add Keyboard Shortcut"**
4. Press these keys together: **Ctrl+Option+Space**
   - **Left pinky** on Ctrl
   - **Left thumb** on Option
   - **Right thumb** on Space
5. You should see: **⌃⌥Space** displayed
6. Click **"Done"**

---

## Step 7: Grant Microphone Permission
1. Close Shortcuts app
2. Open any app (Notes, TextEdit, etc.)
3. Press **Ctrl+Option+Space**
4. If prompted: **"Shortcuts wants to access the microphone"** → Click **"OK"**
5. If not prompted, go to:
   - System Settings → Privacy & Security → Microphone
   - Scroll to find **"Shortcuts"**
   - Toggle it **ON**

---

## Step 8: Test It!
1. Open **Notes** (or any text app)
2. Click in a blank note
3. Press: **Ctrl+Option+Space**
4. You should see terminal output flash (or notification)
5. When you see **"🎤 Recording..."**:
   - Speak clearly: "This is a test of the whisper dictation system"
   - Wait 2 seconds in silence
6. Should say: **"✅ Transcribed in X.XXs"**
7. Press **Cmd+V** to paste
8. Text should appear!

---

## Expected Behavior

### What You'll See:
```
🎤 Recording... (speak now, auto-stops on silence)
✅ Recording complete
🔄 Transcribing...
✅ Transcribed in 0.87s
📋 Copied to clipboard: This is a test of the whisper dictation system...

📝 Transcription:
This is a test of the whisper dictation system.
```

### Timing:
- **First use**: ~2-3 seconds total
- **Subsequent uses**: <1 second transcription
- **Recording**: Ends automatically after 2 seconds of silence

---

## Troubleshooting

### "Nothing happens when I press Ctrl+Option+Space"
**Check 1**: Shortcut enabled?
- Open Shortcuts app → Find "Whisper Dictation"
- Click ⓘ icon → Verify keyboard shortcut shows **⌃⌥Space**

**Check 2**: Another app using that shortcut?
- Try in different app (Terminal, Notes, TextEdit)
- If works in some apps but not others = app-specific conflict

**Fix**: Try alternate shortcut:
- Shortcuts app → Your shortcut → ⓘ icon
- Change to: **Ctrl+Shift+/** or **Option+Shift+Space**

---

### "Server not running" error appears
```bash
# Start the server
bash claude/commands/start_whisper_server.sh

# Verify it's running
curl http://127.0.0.1:8090/health
# Should return: {"status":"ok"}
```

**Server should auto-start** on login (LaunchAgent is loaded), but if you just set this up, it needs one manual start.

---

### "Recording failed" or microphone error
**Fix**: Grant microphone permission
1. System Settings → Privacy & Security → Microphone
2. Find **"Shortcuts"** in the list
3. Toggle **ON**
4. Restart Shortcuts app
5. Try again

---

### Recording doesn't stop automatically
**Cause**: Background noise preventing silence detection

**Fix**:
- Move to quieter location
- Speak clearly, then stay completely silent for 2 seconds
- Close window/door to reduce ambient noise

---

### Transcription is slow (>3 seconds)
**First use is always slower** (model warm-up)

**If consistently slow**:
```bash
# Restart server
bash claude/commands/stop_whisper_server.sh
bash claude/commands/start_whisper_server.sh

# Check logs
tail -f ~/.maia/logs/whisper-server.log
```

---

## Usage Tips

### Best Practices:
✅ **Quiet environment** (home office, quiet room)
✅ **Clear speech** at normal conversational pace
✅ **1-2 feet from built-in mic** (or use external mic)
✅ **Natural pauses** for sentence breaks
✅ **Stay silent 2 seconds** to end recording

### Works Great For:
- Code comments
- Documentation
- Email drafts
- Meeting notes
- Long-form writing

### Less Ideal For:
- Very noisy environments (open office)
- Real-time streaming needs
- Very technical jargon (may need correction)

---

## Keyboard Shortcut Reference

**Your shortcut**: **Ctrl+Option+Space** (⌃⌥Space)

**How to press**:
```
Left hand:
  Pinky = Ctrl
  Thumb = Option
Right hand:
  Thumb = Space

Press all three together
```

**Easy to remember**: "Control + Option + Say it"

---

## Server Management

### Check if running:
```bash
curl http://127.0.0.1:8090/health
# Should return: {"status":"ok"}
```

### Manual control:
```bash
# Start
bash claude/commands/start_whisper_server.sh

# Stop
bash claude/commands/stop_whisper_server.sh

# View logs
tail -f ~/.maia/logs/whisper-server.log
```

### Auto-start status:
```bash
launchctl list | grep whisper
# Should show: 37943   0   com.maia.whisper-server
```

✅ **Auto-starts on login** (LaunchAgent loaded)

---

## What's Next?

### After successful test:
1. ✅ Use it daily for a week to build muscle memory
2. ✅ Test in different apps (VS Code, Browser, Terminal)
3. ✅ Find your optimal speaking pace
4. ✅ Experiment with technical terms

### Future enhancements (optional):
- Add custom vocabulary for technical terms
- Create separate "command mode" for Maia voice commands
- Adjust silence detection threshold

---

## Summary

**Shortcut**: Ctrl+Option+Space
**Server**: http://127.0.0.1:8090
**Auto-start**: ✅ Enabled
**Privacy**: ✅ 100% local (no cloud)
**Latency**: <1s steady-state

**Ready to dictate!** 🎤
