# Whisper Dictation Keyboard Shortcut Setup

## Quick Action Setup (5 minutes)

### Step 1: Open Automator
1. Open **Spotlight** (Cmd+Space)
2. Type "Automator"
3. Press Enter

### Step 2: Create Quick Action
1. Click **"New Document"**
2. Select **"Quick Action"**
3. Click **"Choose"**

### Step 3: Configure Workflow
1. In the search box (top left), type: **"Run Shell Script"**
2. Drag **"Run Shell Script"** action to the right panel
3. Configure settings at top of action:
   - **Workflow receives**: "no input"
   - **in**: "any application"

### Step 4: Add Script
Paste this exact script into the text box:

```bash
cd /Users/naythandawe/git/maia
/opt/homebrew/bin/python3 claude/tools/whisper_dictation_server.py
```

### Step 5: Save Quick Action
1. Press **Cmd+S** (or File → Save)
2. Name it: **"Whisper Dictation"**
3. Click **"Save"**
4. Close Automator

### Step 6: Assign Keyboard Shortcut
1. Open **System Settings**
2. Go to **Keyboard**
3. Click **"Keyboard Shortcuts..."** button
4. Select **"Services"** in left sidebar
5. Scroll down to **"General"** section
6. Find **"Whisper Dictation"**
7. Click on it to select
8. Click **"Add Shortcut"** button on right
9. Press: **Ctrl+Shift+D**
10. Close System Settings

### Step 7: Grant Microphone Permission
1. Try the shortcut: Press **Ctrl+Shift+D**
2. If prompted for microphone access, click **"OK"**
3. If needed, go to: System Settings → Privacy & Security → Microphone
4. Enable for **"Automator"** or **"Shortcuts"**

---

## Testing Your Shortcut

1. **Open any text field** (Notes, TextEdit, Terminal, Claude Code, etc.)
2. **Press**: `Ctrl+Shift+D`
3. **Wait for**: "🎤 Recording..." message (may appear in notification)
4. **Speak**: Say your text clearly
5. **Auto-stops**: After 2 seconds of silence
6. **Paste**: Press `Cmd+V` to paste transcribed text

---

## Expected Behavior

### First Use (Cold Start):
- Delay: ~1-2 seconds while server warms up
- Then transcription starts

### Subsequent Uses (Warm):
- Immediate recording start
- <1 second transcription after speaking
- Text in clipboard ready to paste

---

## Troubleshooting

### "Nothing happens when I press Ctrl+Shift+D"
- Check: System Settings → Keyboard → Keyboard Shortcuts → Services
- Verify "Whisper Dictation" has shortcut assigned
- Try different shortcut (e.g., Ctrl+Shift+V)

### "Permission denied" or microphone error
- System Settings → Privacy & Security → Microphone
- Enable for "Automator" or "Shortcuts"
- Try shortcut again

### "Server not running" error
- Check server: `curl http://127.0.0.1:8090/health`
- If not running: `bash claude/commands/start_whisper_server.sh`
- Server should auto-start after this (LaunchAgent loaded)

### Slow transcription (>5 seconds)
- First use always slower (model loading)
- If consistently slow:
  - Check server logs: `tail -f ~/.maia/logs/whisper-server.log`
  - Restart server: `bash claude/commands/stop_whisper_server.sh && bash claude/commands/start_whisper_server.sh`

### Recording doesn't stop
- Background noise may prevent silence detection
- Move to quieter location
- Speak, then stay completely silent for 2 seconds

---

## Alternative: Keyboard Maestro (If you have it)

If you use Keyboard Maestro instead:

1. Create new macro
2. Trigger: Hot Key → **Ctrl+Shift+D**
3. Action: Execute Shell Script
4. Script:
   ```bash
   cd /Users/naythandawe/git/maia && /opt/homebrew/bin/python3 claude/tools/whisper_dictation_server.py
   ```
5. Enable macro

---

## Usage Tips

### Best Results:
- Quiet environment (minimal background noise)
- Clear speech at normal pace
- 1-2 feet from microphone
- Pause clearly for punctuation

### Punctuation:
- Say "period" for .
- Say "comma" for ,
- Say "question mark" for ?
- Natural pauses help with sentence breaks

### When It Works Best:
- Dictating code comments
- Writing documentation
- Composing emails
- Taking notes
- Any prose/text input

### When Not To Use:
- Noisy environments (open office, coffee shop)
- Commands/short phrases (though it works)
- Very technical terms (may need correction)
- Real-time transcription needs (this is batch)

---

## Server Status

Check server status anytime:
```bash
# Health check
curl http://127.0.0.1:8090/health

# View logs
tail -f ~/.maia/logs/whisper-server.log

# Check if running
launchctl list | grep whisper

# Manual restart
bash claude/commands/stop_whisper_server.sh
bash claude/commands/start_whisper_server.sh
```

---

## Next Steps After Setup

Once working:
1. Test in different apps (Notes, Browser, IDE)
2. Find your optimal speaking pace
3. Learn punctuation commands
4. Use daily for 1 week to build habit
5. Adjust shortcut if conflicts with other apps

**Setup Complete**: Press `Ctrl+Shift+D` to dictate! 🎤
