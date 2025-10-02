#!/usr/bin/env python3
"""
Production Credential Setup Script
=================================

This script guides you through setting up all production credentials
for the Maia AI Assistant system.
"""

import json
import os
from pathlib import Path

def main():
    print("🔐 Maia Production Credential Setup")
    print("=" * 40)
    
    # Create credentials directory
    cred_dir = Path("claude/data/credentials")
    cred_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n📧 GMAIL OAUTH SETUP")
    print("-" * 20)
    print("""
# Gmail OAuth Setup Instructions
# ==============================

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing project
3. Enable Gmail API: 
   - Go to APIs & Services > Library
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Desktop application"
   - Name: "Maia Gmail Integration"
5. Download the JSON file and save as: claude/data/credentials/gmail_oauth.json
6. Add the following scopes:
   - https://www.googleapis.com/auth/gmail.readonly
   - https://www.googleapis.com/auth/gmail.send
   - https://www.googleapis.com/auth/gmail.modify

# Test OAuth flow:
python3 claude/scripts/test_gmail_oauth.py
""")
    
    print("\n💼 LINKEDIN API SETUP")
    print("-" * 20)
    print("""
# LinkedIn API Setup Instructions
# ===============================

1. Go to LinkedIn Developer Portal: https://www.linkedin.com/developers/
2. Create a new app:
   - App name: "Maia Career Intelligence"
   - LinkedIn Page: Your personal LinkedIn profile
   - App use: Career and professional networking
3. Request API access:
   - Basic Profile API
   - Career and Education API (if available)
   - Company API (for company research)
4. Add OAuth 2.0 redirect URL: http://localhost:8080/linkedin/callback
5. Copy Client ID and Client Secret to: claude/data/credentials/linkedin_api.json

# Configuration format:
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "redirect_uri": "http://localhost:8080/linkedin/callback"
}

# Test API access:
python3 claude/scripts/test_linkedin_api.py
""")
    
    print("\n📅 GOOGLE CALENDAR API SETUP")
    print("-" * 25)
    print("""
# Google Calendar API Setup Instructions
# =====================================

1. Use the same Google Cloud Console project from Gmail setup
2. Enable Google Calendar API:
   - Go to APIs & Services > Library
   - Search for "Google Calendar API" and enable it
3. Use the same OAuth 2.0 credentials from Gmail (can share credentials)
4. Add Calendar API scopes:
   - https://www.googleapis.com/auth/calendar
   - https://www.googleapis.com/auth/calendar.events

# The gmail_oauth.json file will work for Calendar API as well
# Test Calendar access:
python3 claude/scripts/test_calendar_api.py
""")
    
    print("\n📱 TWILIO SMS SETUP")
    print("-" * 20)
    print("""
# Twilio SMS Setup Instructions
# =============================

1. Sign up for Twilio: https://www.twilio.com/
2. Get a phone number:
   - Go to Phone Numbers > Manage > Buy a number
   - Choose a number that supports SMS
3. Find your credentials:
   - Go to Console Dashboard
   - Copy Account SID and Auth Token
4. Save credentials to: claude/data/credentials/twilio_sms.json

# Configuration format:
{
  "account_sid": "your_account_sid",
  "auth_token": "your_auth_token",
  "from_phone": "+1234567890",
  "to_phone": "+your_phone_number"
}

# Test SMS delivery:
python3 claude/scripts/test_twilio_sms.py
""")
    
    print("\n✅ CREDENTIAL SETUP COMPLETE")
    print("=" * 30)
    print("After setting up all credentials, run:")
    print("python3 claude/tools/production_deployment_manager.py --verify-credentials")

if __name__ == "__main__":
    main()
