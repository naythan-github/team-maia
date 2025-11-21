# Mail.app Setup for Automated Email Sending

## Issue Encountered
When attempting to send email via Mail.app AppleScript, receiving error:
```
Connection is invalid. (-609)
```

## Root Cause
Exchange account in Mail.app is not fully connected/synced. This prevents AppleScript from sending emails even though Mail.app can read messages.

## Solutions

### Option 1: Fix Mail.app Exchange Connection (Recommended)
1. Open Mail.app
2. Go to Mail → Settings → Accounts
3. Select "Exchange" account
4. Verify "Connection Doctor" shows active connection
5. If offline, click "Take All Accounts Online"
6. Test sending a manual email from Mail.app first

### Option 2: Alternative Delivery Methods

#### A. Use iCloud Account for Sending
If you have an iCloud account configured in Mail.app:
```python
mail_bridge.send_email(
    to="naythan.dawe@orro.group",
    subject="Daily Briefing",
    body=html_content,
    html=True,
    account="iCloud"  # Instead of "Exchange"
)
```

#### B. Manual Forward Workflow (Current Fallback)
System automatically saves HTML file when sending fails:
```bash
# Briefing saved to:
~/git/maia/claude/data/daily_briefing_email.html

# Open and manually forward:
open ~/git/maia/claude/data/daily_briefing_email.html
```

#### C. Use Zapier MCP (Existing Tool)
Zapier MCP is already configured for email sending:
```python
# In automated_daily_briefing.py
from zapier_mcp import send_email

send_email(
    to="naythan.dawe@orro.group",
    subject=f"Daily Briefing - {briefing['date']}",
    html_body=html_content
)
```

#### D. Gmail SMTP (If Available)
If Gmail account configured:
```python
import smtplib
from email.mime.text import MIMEText

# Requires app-specific password
```

## Current Configuration

**Delivery Email**: `naythan.dawe@orro.group` (updated from icloud)
**Sending Method**: Mail.app Exchange (with graceful fallback)
**Fallback**: HTML file saved to `~/git/maia/claude/data/daily_briefing_email.html`

## Testing Email Sending

### Test 1: Verify Mail.app Connection
```bash
osascript -e 'tell application "Mail" to return name of accounts'
```

### Test 2: Check Account Status
```bash
osascript -e 'tell application "Mail"
    repeat with acct in accounts
        return (name of acct) & ": " & (enabled of acct)
    end repeat
end tell'
```

### Test 3: Simple Send Test
```bash
cd ~/git/maia && python3 -c "
from claude.tools.macos_mail_bridge import MacOSMailBridge
bridge = MacOSMailBridge()
bridge.send_email(
    to='naythan.dawe@orro.group',
    subject='Test',
    body='<p>Test email</p>',
    html=True,
    account='Exchange'
)
"
```

## Recommended Next Steps

1. **Fix Exchange Connection** (if you want automated sending via Mail.app)
   - Open Mail.app → Settings → Accounts → Exchange
   - Verify connection active
   - Send manual test email

2. **OR Use Zapier MCP** (already working for morning briefings)
   - Update `automated_daily_briefing.py` to use Zapier
   - No Mail.app configuration needed

3. **OR Accept Manual Forward** (simplest, works now)
   - Cron job generates HTML at 7:30 AM
   - You manually forward once per day
   - 30 seconds of manual work

## Current System Behavior

✅ **What Works**:
- Complete briefing generation (5-8 seconds)
- HTML email formatting
- All intelligence gathering (Calendar, Email, Contacts, Meetings, Actions)
- File saving (JSON + HTML)
- Graceful error handling

⚠️ **What Needs Setup**:
- Mail.app Exchange connection for automated sending
- OR alternative delivery method configuration

The system is **production ready** - it just needs one of the delivery methods properly configured.
