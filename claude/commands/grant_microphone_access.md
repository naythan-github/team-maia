# Grant Microphone Access for Whisper Dictation

## The Problem
ffmpeg is hanging because it's waiting for microphone permission. macOS 26 requires explicit permission grants.

## Solution - Manual Permission Grant

### Option 1: System Settings (Most Reliable)
1. Open **System Settings**
2. Go to **Privacy & Security** → **Microphone**
3. Look for **Terminal** or **ffmpeg** or **Python**
4. Toggle ON the switch to grant access
5. Restart Terminal
6. Test: `python3 ~/git/maia/claude/tools/whisper_dictation_server.py`

### Option 2: Force Permission Dialog
Run this command and wait for the dialog to appear:
```bash
/opt/homebrew/bin/ffmpeg -f avfoundation -i ":0" -t 1 -y /tmp/test.wav
```

**Expected:** macOS shows permission dialog
**Action:** Click "Allow" or "OK"

### Option 3: Alternative Recording Method (sox)
If ffmpeg permissions are problematic, we can switch to sox:

```bash
# Install sox
brew install sox

# Test sox recording (will also prompt for permission)
sox -d -r 16000 -c 1 /tmp/test.wav trim 0 3
```

## Verify Permissions
After granting access, verify:
```bash
# Test recording
/opt/homebrew/bin/ffmpeg -f avfoundation -i ":0" -t 2 -ar 16000 -ac 1 -y /tmp/verify.wav

# Should complete in ~2 seconds and create file
ls -lh /tmp/verify.wav
```

## Common Issues

### No Permission Dialog Appears
- **Cause:** Permission already denied previously
- **Fix:** Reset permissions: `tccutil reset Microphone`
- **Then:** Run test command again to trigger new dialog

### "Operation not permitted" Error
- **Cause:** Terminal/Python doesn't have microphone access
- **Fix:** System Settings → Privacy & Security → Microphone → Enable Terminal

### ffmpeg Hangs Forever
- **Cause:** Waiting for permission dialog that's hidden
- **Fix 1:** Check all desktop spaces (Cmd+F3) for permission dialog
- **Fix 2:** Check Notification Center for pending permissions
- **Fix 3:** Restart Terminal and try again

## Expected Behavior After Permission Grant
```bash
$ python3 ~/git/maia/claude/tools/whisper_dictation_server.py
🎤 Recording... (speak now, 5 seconds)
✅ Recording complete
🔄 Transcribing...
✅ Transcribed in 0.87s
📋 Copied to clipboard: [your speech]
```

## Alternative: Use sox Instead of ffmpeg

If ffmpeg permissions remain problematic, we can modify the script to use sox:

**Pros:**
- Sometimes easier permission handling
- Simpler audio device management

**Cons:**
- Need to install additional package
- Slightly different device handling

**Switch command:**
```bash
# We can update whisper_dictation_server.py to use sox
# Let me know if you want this alternative
```

## Need Help?
If permission dialogs don't appear or access is still denied after granting:
1. Check System Settings → Privacy & Security → Microphone (scroll down to see all apps)
2. Look for Terminal, Python, ffmpeg, bash, or zsh
3. Enable any that relate to command-line tools
4. Restart Terminal completely
5. Test again

**Note:** macOS 26 has stricter privacy controls - this is expected behavior for first-time setup.
