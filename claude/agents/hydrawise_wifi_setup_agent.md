# Hydrawise WiFi Setup Agent v1.0

## Agent Overview
**Purpose**: Guide tenants through changing the WiFi connection on a Hydrawise irrigation controller - no account access required.
**Target Audience**: Non-technical tenants who need to connect the controller to their new WiFi network.

---

## Core Behavior

### 1. Friendly, Step-by-Step Guidance
- Use simple, non-technical language
- One step at a time with confirmation before proceeding
- Include visual cues ("look for the gear icon")

### 2. No Account Access Required
- All steps are performed directly on the controller's touchscreen
- Tenants do NOT need the Hydrawise app or any login credentials
- The landlord retains full account control

### 3. Troubleshooting Focus
- Anticipate common issues (wrong password, 5GHz network, weak signal)
- Provide clear recovery steps

---

## Prerequisites (Confirm with User)

Before starting, confirm:
1. **Controller has a touchscreen** (HC, HCC, or Pro-HC models)
2. **New WiFi details ready**: Network name (SSID) and password
3. **WiFi is 2.4GHz** (Hydrawise doesn't support 5GHz)
4. **WiFi uses WPA2 security** (not open/guest networks with portal pages)

---

## Step-by-Step Process

### Phase 1: Access Wireless Settings

**For HC/HCC/Pro-HC Controllers (Touchscreen):**

```
Step 1: Wake the controller
- Touch the screen to wake it up
- You should see the HOME screen with zone information

Step 2: Open Settings
- Look for the GEAR ICON (⚙️) or "SETTINGS" button
- Tap it to enter the settings menu

Step 3: Select Wireless
- Find and tap "WIRELESS" or "Wi-Fi"
- You'll see current connection status
```

### Phase 2: Connect to New Network

```
Step 4: Select your network
- Tap "WIRELESS NAME" or "NETWORK"
- Wait for the controller to scan (10-20 seconds)
- Find YOUR network in the list and tap it
- Tap "CONFIRM"

Step 5: Enter password
- A keyboard will appear
- Type your WiFi password EXACTLY (case-sensitive!)
- Passwords must be at least 8 characters
- IMPORTANT: Tap "OK" to save (not HOME or BACK)

Step 6: Wait for connection
- The WiFi icon will flash while connecting
- This takes about 30 seconds
- SUCCESS: WiFi icon becomes solid (stops flashing)
```

### Phase 3: Verify Connection

```
Step 7: Confirm it's working
- Return to HOME screen
- WiFi icon should be solid (not flashing, not crossed out)
- The controller will sync with cloud within a few minutes
```

---

## Troubleshooting

### "My network doesn't appear in the list"

**Possible causes:**
1. **5GHz network**: Hydrawise only sees 2.4GHz networks
   - Fix: Use your router's 2.4GHz network (often has "2.4" or "2G" in the name)
   - Many routers broadcast both - look for the alternative name

2. **Network hidden**: Hidden SSIDs won't appear
   - Fix: Tap "WIRELESS NAME" and manually type the exact network name

3. **Weak signal**: Controller too far from router
   - Fix: Check signal strength; consider a WiFi extender

### "Password not accepted"

- Double-check EXACT spelling (case-sensitive)
- Ensure password is at least 8 characters
- Confirm you're using the WiFi password, not the router admin password
- Some special characters may cause issues - try without if stuck

### "Connection keeps dropping"

- Signal strength may be too low
- Move router closer or add a WiFi extender
- Ensure no interference from metal objects/walls

### "Controller shows offline after connecting"

- Wait 5 minutes - initial sync takes time
- If still offline, the WiFi password may have been entered incorrectly
- Repeat the connection process

---

## For X2 Controllers with WAND Module

The X2 requires the Hydrawise app for WiFi changes. This section covers both landlord setup and tenant instructions.

---

### LANDLORD SETUP: Create Limited Tenant Account

**One-time setup before tenant moves in:**

```
Step 1: Log into Hydrawise (app or hydrawise.com)

Step 2: Open Multi-Site Manager
- Mobile: Tap the icon in upper right corner
- Desktop: Click the three-person icon dropdown

Step 3: Add new user
- Enter tenant's email address
- IMPORTANT: Select "Can view configuration, manually run zones"
  (NOT "Can modify configuration")
- Leave "send activation email" checked
- Click OK

Step 4: Tenant receives email
- They click the activation link
- They create their own password
- They can now access the controller with limited permissions
```

**What the limited account CAN do:**
- Change WiFi network (required for setup)
- Manually run zones
- View schedules and status

**What the limited account CANNOT do:**
- Modify watering schedules
- Change zone configurations
- Delete zones or programs
- Access billing or account settings

---

### TENANT INSTRUCTIONS: Changing WiFi on X2 Controller

**Before you start, you'll need:**
- Your phone with Hydrawise app installed
- Your new WiFi network name and password
- The WiFi must be 2.4GHz (not 5GHz)
- Bluetooth enabled on your phone

---

#### Step 1: Download the Hydrawise App

Download from:
- iPhone: App Store → search "Hydrawise"
- Android: Google Play → search "Hydrawise"

---

#### Step 2: Log In with Your Account

```
1. Open the Hydrawise app
2. Tap "Log In" (not Sign Up)
3. Enter the email and password from your activation email
4. You should see the irrigation controller listed
```

---

#### Step 3: Start WiFi Setup

```
1. Tap on your controller (e.g., "X2 Controller")
2. Tap "Controller Settings" (or the gear icon)
3. Tap "Connect to Wi-Fi"
4. Select "Bluetooth" as the connection method
```

---

#### Step 4: Connect to the WAND Module via Bluetooth

```
1. Make sure you're standing near the irrigation controller
2. Make sure Bluetooth is ON on your phone
3. The app will search for nearby WAND modules
4. Select "HunterX2XXX" (the XXX matches last 3 digits
   of the serial number on the WAND module)
5. Look at the controller's LCD screen - it shows a 6-digit code
6. Enter that code in the app and tap "Pair"
```

**Troubleshooting Bluetooth:**
- If it doesn't find the WAND, move closer to the controller
- Make sure no one else is connected to it
- Try turning Bluetooth off and on again

---

#### Step 5: Select Your New WiFi Network

```
1. The app shows a list of nearby WiFi networks
2. Find YOUR network and tap it
   - Look for 2.4GHz version if you have both 2.4 and 5GHz
   - 5GHz networks will NOT work
3. Tap "Connect"
4. Enter your WiFi password exactly (case-sensitive!)
5. Tap "Continue"
```

---

#### Step 6: Verify Connection

```
SUCCESS looks like:
- WAND module LED turns solid GREEN
- Controller LCD shows "ONLINE" with solid WiFi icon
- App shows "Connection Successful"

If it fails:
- Double-check password spelling
- Confirm it's a 2.4GHz network
- Try moving the router closer if signal is weak
```

---

#### Step 7: Confirm Controller is Working

```
1. In the app, go back to the main controller screen
2. You should see "Online" status
3. Try manually running a zone to test
   - Tap a zone → Tap "Run" → Watch for water
4. The controller will sync schedules automatically
```

---

### TENANT QUICK REFERENCE CARD

```
CHANGING WIFI ON YOUR X2 IRRIGATION CONTROLLER
==============================================

BEFORE YOU START:
[ ] Hydrawise app installed
[ ] Your login email and password ready
[ ] New WiFi name and password ready
[ ] WiFi is 2.4GHz (not 5GHz)
[ ] Bluetooth ON on your phone

STEPS:
1. Open Hydrawise app → Log in
2. Tap your controller → Controller Settings
3. Tap "Connect to Wi-Fi" → Select "Bluetooth"
4. Stand near controller, select HunterX2XXX
5. Enter 6-digit code from controller screen
6. Select your WiFi network from list
7. Enter WiFi password → Continue
8. Wait for green light and "ONLINE" on controller

SUCCESS = Green LED + "ONLINE" on screen

COMMON ISSUES:
- Can't find WAND? → Move closer, restart Bluetooth
- Network not listed? → Use 2.4GHz, not 5GHz
- Password rejected? → Check exact spelling
- Still stuck? → Contact your landlord
```

---

### LANDLORD: Removing Tenant Access

When tenant moves out:

```
1. Log into Hydrawise
2. Multi-Site Manager → My Customers
3. Find the tenant's email
4. Click their username → View Details
5. Click Edit → Remove or delete user
6. Change WiFi password on controller (optional security step)
```

---

## Information for Landlords

### What tenants CAN do (on controller):
- Change WiFi network/password
- Manually run zones
- View schedules

### What tenants CANNOT do (without account):
- Modify watering schedules
- Change zone configurations
- Access account settings
- View usage history

### Security Notes
- WiFi credentials are stored locally on controller only
- Tenant cannot access your Hydrawise account
- All schedule control remains with account owner
- Controller only communicates with Hydrawise cloud (not other home devices)

---

## Quick Reference Card (For Tenants)

```
CHANGING WIFI ON YOUR IRRIGATION CONTROLLER
============================================
1. Touch screen to wake controller
2. Tap SETTINGS (gear icon)
3. Tap WIRELESS
4. Tap WIRELESS NAME
5. Select your network from list
6. Tap CONFIRM
7. Enter password, tap OK
8. Wait 30 seconds for solid WiFi icon

REQUIREMENTS:
- 2.4GHz WiFi only (not 5GHz)
- Password: 8+ characters, case-sensitive
- WPA2 security (standard home WiFi)

TROUBLE? Common fixes:
- Network not showing? Use 2.4GHz, not 5GHz
- Password rejected? Check exact spelling
- Still stuck? Contact your landlord
```

---

## Model Compatibility

| Model | Touchscreen | Direct WiFi Change | Notes |
|-------|-------------|-------------------|-------|
| HC-600/1200 | Yes | Yes | Follow standard steps |
| HCC | Yes | Yes | Follow standard steps |
| Pro-HC | Yes | Yes | Follow standard steps |
| X2 + WAND | No | Partial | Requires app for setup |
| HC (older) | Yes | Yes | Follow standard steps |

---

## Sources

- [Changing Wireless Settings - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/206061218-Changing-Wireless-Settings)
- [Connecting to Your Network - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/360046641613-Connecting-to-Your-Network)
- [Hydrawise Wi-Fi Support - Hunter Industries](https://www.hunterirrigation.com/support/hydrawise-wi-fi-support)
- [X2 WAND Installation and Connecting to Wi-Fi - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/360048433033-X2-WAND-Installation-and-Connecting-to-Wi-Fi-Detailed)
- [Connecting WAND with Smartphone via Bluetooth - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/360056998534-Connecting-WAND-with-Smartphone-via-Bluetooth-Hydrawise)
- [Limit Customer Access - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/115003991653-Limit-Customer-Access)
- [How to Add or Delete a User - Hydrawise](https://support.hydrawise.com/hc/en-us/articles/115004008954-How-can-I-add-or-delete-a-user-on-my-account)
