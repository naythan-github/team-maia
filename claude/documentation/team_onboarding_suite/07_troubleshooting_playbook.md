# Maia AI System: Troubleshooting Playbook
**Common Issues, Error Recovery Procedures & Debug Workflows**

---

## Document Purpose
Systematic troubleshooting procedures for common Maia issues with step-by-step diagnosis and resolution. Designed for operations staff, support teams, and developers debugging system problems.

**Reading Time**: 25-30 minutes | **Target Audience**: Operations, Support, Developers

---

## Quick Reference: Common Issues

| Issue | Symptoms | Quick Fix | Details |
|-------|----------|-----------|---------|
| Local LLM not responding | Timeout, connection refused | `ollama serve` | Section 1.1 |
| RAG search empty | No results despite data exists | Re-index collection | Section 1.2 |
| Service not running | LaunchAgent failed/idle | `launchctl load` plist | Section 1.3 |
| Pre-commit hook blocks | Commit fails with security errors | Fix violations, re-commit | Section 1.4 |
| Out of disk space | Backup/indexing fails | Prune old backups/logs | Section 1.5 |
| M365 auth failure | 401 Unauthorized | Regenerate API token | Section 2.1 |
| Confluence rate limit | 429 Too Many Requests | Wait for rate limit reset | Section 2.2 |
| Context loading slow | >500ms load time | Enable caching | Section 3.1 |
| Agent handoff failure | Workflow stops mid-execution | Fix handoff format | Section 3.2 |
| Database locked | SQLite "database is locked" | Check concurrent access | Section 3.3 |

---

## Section 1: Core System Issues

### 1.1 Local LLM Not Responding

**Symptoms**:
- `ollama run` command hangs or times out
- "Could not connect to ollama" error
- Python scripts using local LLMs fail with connection error

**Diagnosis**:
```bash
# Step 1: Check if Ollama is running
ps aux | grep ollama

# Expected: ollama process with PID
# If no process: Ollama not running

# Step 2: Check available models
ollama list

# If error "could not connect": Ollama server not running
# If empty list: No models installed

# Step 3: Check Ollama port
lsof -i :11434

# Expected: ollama listening on port 11434
# If nothing: Ollama server not started
```

**Resolution**:

**Fix 1: Start Ollama Server**
```bash
# Terminal 1: Start Ollama
ollama serve

# Expected output:
# 2025/10/15 14:30:00 Listening on 127.0.0.1:11434
# 2025/10/15 14:30:00 Server started successfully

# Terminal 2: Verify models
ollama list

# Expected:
# NAME              SIZE
# codellama:13b     7.3GB
# starcoder2:15b    9.1GB
# llama3:3b         1.9GB

# Terminal 2: Test inference
ollama run llama3:3b "Hello test"

# Should return response within 2-3 seconds
```

**Fix 2: Install Missing Models** (if `ollama list` is empty)
```bash
# Install required models
ollama pull codellama:13b    # 10-15 min, requires 16GB+ RAM
ollama pull starcoder2:15b   # 12-18 min
ollama pull llama3:3b        # 2-3 min

# Verify installation
ollama list

# Should show all 3 models with sizes
```

**Fix 3: Restart Ollama** (if running but not responding)
```bash
# Kill existing process
pkill ollama

# Wait 2 seconds
sleep 2

# Restart
ollama serve

# Test
ollama run llama3:3b "test"
```

**Prevention**:
```bash
# Create LaunchAgent for Ollama auto-start (optional)
cat > ~/Library/LaunchAgents/com.ollama.server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.ollama.server.plist
```

**Time to Fix**: 1-2 minutes (restart) or 30-45 minutes (install models)

---

### 1.2 RAG Search Returns Empty Results

**Symptoms**:
- Semantic search returns 0 results
- "No documents found" despite knowing data exists
- Query logs show collection name but no matches

**Diagnosis**:
```bash
# Step 1: Check collection status
python3 << 'EOF'
import chromadb
from pathlib import Path

client = chromadb.PersistentClient(
    path=str(Path.home() / "git/maia/claude/data/rag_collections")
)

collections = client.list_collections()
print(f"Total collections: {len(collections)}\n")

for collection in collections:
    count = collection.count()
    print(f"{collection.name}: {count} documents")

    if count == 0:
        print(f"  ⚠️ EMPTY COLLECTION - Needs indexing\n")
    else:
        print(f"  ✅ Operational\n")
EOF

# Example output:
# Total collections: 9
#
# email_archive: 0 documents
#   ⚠️ EMPTY COLLECTION - Needs indexing
#
# servicedesk_tickets: 1,170 documents
#   ✅ Operational
```

**Resolution**:

**Fix 1: Re-Index Empty Collection**
```bash
# Identify which collection is empty (from diagnosis)
# Example: email_archive = 0 documents

# Re-index specific collection
python3 ~/git/maia/claude/tools/email_rag_ollama.py --index

# Output:
# Indexing email_archive...
# - Fetching emails from M365...
# - Fetched: 25,142 emails
# - Generating embeddings... (5-10 min)
# - Indexing complete
#
# Collection: email_archive
# Documents: 25,142 ✅

# Verify indexing
python3 << 'EOF'
import chromadb

client = chromadb.PersistentClient(path="~/git/maia/claude/data/rag_collections")
collection = client.get_collection("email_archive")
print(f"Documents: {collection.count()}")
EOF

# Expected: Documents: 25,142 ✅
```

**Fix 2: Re-Index All Collections** (if multiple empty)
```bash
# Email archive
python3 ~/git/maia/claude/tools/email_rag_ollama.py --index

# Document repository
python3 ~/git/maia/claude/tools/document_rag_system.py --index \
  --source ~/Documents

# Meeting transcripts
python3 ~/git/maia/claude/tools/vtt_rag_indexer.py index \
  --source ~/git/maia/claude/data/transcript_summaries

# ServiceDesk data
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_multi_rag_indexer.py

# System state history
python3 ~/git/maia/claude/tools/sre/system_state_rag_indexer.py
```

**Fix 3: Check Embeddings API Key** (if indexing fails)
```bash
# Verify OpenAI API key (for embeddings)
python3 << 'EOF'
import os
from claude.tools.production_api_credentials import OPENAI_API_KEY

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY not set")
else:
    print(f"✅ API key present: {OPENAI_API_KEY[:10]}...")

# Test embedding
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

try:
    response = client.embeddings.create(
        input="test",
        model="text-embedding-ada-002"
    )
    print("✅ Embeddings API working")
except Exception as e:
    print(f"❌ Embeddings API error: {e}")
EOF
```

**Time to Fix**: 5-30 minutes (depending on collection size)

---

### 1.3 Background Service Not Running

**Symptoms**:
- VTT files not being processed
- Daily briefing not generated
- Email RAG not updating
- `launchctl list` shows PID "-" or exit code

**Diagnosis**:
```bash
# Step 1: Check all Maia services
launchctl list | grep maia

# Output format:
# PID    Status    Label
# 812    0         com.maia.vtt-watcher      ← Running (PID 812)
# -      0         com.maia.daily-briefing   ← Idle (scheduled)
# -      1         com.maia.email-indexer    ← Failed (exit code 1)

# Step 2: Check specific service logs
tail -50 ~/git/maia/claude/data/logs/[service-name].log

# Look for error messages:
# - "ModuleNotFoundError" → Python package missing
# - "FileNotFoundError" → Path incorrect in plist
# - "PermissionError" → File access denied
# - "Connection refused" → Dependency service down
```

**Resolution**:

**Fix 1: Reload Failed Service**
```bash
# Unload service
launchctl unload ~/Library/LaunchAgents/com.maia.[service-name].plist

# Fix underlying issue (based on log errors)
# Example: If "ModuleNotFoundError: No module named 'chromadb'"
pip install chromadb

# Reload service
launchctl load ~/Library/LaunchAgents/com.maia.[service-name].plist

# Verify service started
launchctl list | grep [service-name]

# Expected: PID number (not "-")
```

**Fix 2: Verify Plist Paths**
```bash
# Check plist file
cat ~/Library/LaunchAgents/com.maia.[service-name].plist

# Verify paths exist:
# - ProgramArguments[0]: Python path
# - ProgramArguments[1]: Script path

# Test command manually
/usr/local/bin/python3 ~/git/maia/claude/tools/[tool-name].py

# If manual test works but service doesn't:
# → Environment variables not set in plist
# → Add environment variables to plist:

<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin</string>
</dict>
```

**Fix 3: Permissions Issue**
```bash
# Check file permissions
ls -la ~/git/maia/claude/tools/[tool-name].py

# Should be readable (r-- for user)
# If not:
chmod +x ~/git/maia/claude/tools/[tool-name].py

# Check directory permissions
ls -la ~/git/maia/claude/data/logs/

# Should be writable (drwx for user)
# If not:
chmod 755 ~/git/maia/claude/data/logs/
```

**Time to Fix**: 2-10 minutes (depending on root cause)

---

### 1.4 Pre-Commit Hook Blocks Commit

**Symptoms**:
- `git commit` fails with "SECURITY CHECKS FAILED"
- Error messages about hardcoded secrets, vulnerabilities, or compliance issues
- Commit blocked, changes not committed

**Diagnosis**:
```bash
# Step 1: Run security checks manually
python3 ~/git/maia/claude/tools/security/save_state_security_checker.py

# Output shows violations:
# ❌ SECURITY CHECKS FAILED
# Critical Issues: 2
#
# Violations:
#   1. hardcoded_secret: claude/tools/new_tool.py:15
#      - Pattern: api_key = "sk-abc123..."
#      - Recommendation: Move to encrypted vault
#
#   2. vulnerability: requests 2.25.0 (CVE-2023-1234)
#      - Severity: CRITICAL
#      - Recommendation: Upgrade to requests 2.31.0+

# Step 2: Review each violation
# Open files and check line numbers from output
```

**Resolution**:

**Fix 1: Remove Hardcoded Secrets**
```bash
# Bad (hardcoded):
api_key = "sk-abc123..."

# Good (encrypted vault):
from claude.tools.production_api_credentials import OPENAI_API_KEY
api_key = OPENAI_API_KEY

# Or environment variable:
api_key = os.getenv('OPENAI_API_KEY')

# Save changes
git add claude/tools/new_tool.py
```

**Fix 2: Update Vulnerable Dependencies**
```bash
# Check which package has vulnerability
pip show requests

# Output: Version: 2.25.0 (vulnerable)

# Update package
pip install --upgrade requests

# Verify update
pip show requests

# Output: Version: 2.31.0 (fixed)

# Update requirements.txt
pip freeze > requirements.txt

# Commit requirements.txt
git add requirements.txt
```

**Fix 3: Fix Code Security Issues**
```bash
# Run Bandit scan to see specific issues
bandit -r claude/tools/[your-tool].py

# Example output:
# Issue: [B602:subprocess_popen_with_shell_equals_true]
# Severity: High
# Confidence: High
#
# Location: claude/tools/your_tool.py:42
# Code: subprocess.Popen('rm -rf {}'.format(user_input), shell=True)
#
# Recommendation: Use shell=False and list arguments

# Fix:
# Bad:
subprocess.Popen(f'rm -rf {user_input}', shell=True)

# Good:
subprocess.Popen(['rm', '-rf', user_input], shell=False)
```

**Fix 4: Bypass Hook (Emergency Only)**
```bash
# ⚠️ NOT RECOMMENDED: Only use in emergency
# Bypasses security checks (dangerous)

git commit --no-verify -m "Emergency fix"

# Better approach: Fix violations properly
```

**Time to Fix**: 5-20 minutes (depending on violation type)

---

### 1.5 Out of Disk Space

**Symptoms**:
- "No space left on device" error
- Backup fails
- RAG indexing fails
- Database writes fail

**Diagnosis**:
```bash
# Step 1: Check disk usage
df -h

# Output:
# Filesystem      Size   Used  Avail Capacity  Mounted on
# /dev/disk1s1   500GB  498GB  2GB   99%       /

# Step 2: Find large directories
du -sh ~/git/maia/claude/data/*

# Output:
# 148MB   ~/git/maia/claude/data/databases
# 1.2GB   ~/git/maia/claude/data/rag_collections  ← Large
# 850MB   ~/git/maia/claude/data/logs  ← Large
# 45MB    ~/git/maia/claude/data/transcript_summaries

# Step 3: Check OneDrive backups
du -sh ~/Library/CloudStorage/OneDrive-*/MaiaBackups/*

# Output:
# 421MB   MaiaBackups/full_20251015_030000
# 421MB   MaiaBackups/full_20251014_030000
# [... 23 more backups ...]
# Total: 9.7GB  ← Can be pruned
```

**Resolution**:

**Fix 1: Prune Old Backups**
```bash
# Prune old backups (retention: 7 daily, 4 weekly, 12 monthly)
python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py prune

# Output:
# Analyzing backups...
# - Total: 45 backups (18.9GB)
# - To keep: 23 backups (9.7GB)
# - To delete: 22 backups (9.2GB)
#
# Pruning old backups...
# Deleted: 22 backups
# Freed: 9.2GB

# Verify
df -h
# Avail: 11.2GB (was 2GB)
```

**Fix 2: Clear Old Logs** (keep last 30 days)
```bash
# Find old logs
find ~/git/maia/claude/data/logs/ -name "*.log" -mtime +30

# Delete old logs
find ~/git/maia/claude/data/logs/ -name "*.log" -mtime +30 -delete

# Check space recovered
du -sh ~/git/maia/claude/data/logs/

# Before: 850MB → After: 120MB (730MB recovered)
```

**Fix 3: Rebuild RAG Collections** (optimize storage)
```bash
# RAG collections can accumulate overhead
# Rebuild to optimize

# Backup collection names
python3 << 'EOF'
import chromadb
client = chromadb.PersistentClient(path="~/git/maia/claude/data/rag_collections")
collections = [c.name for c in client.list_collections()]
print("Collections:", collections)
EOF

# Delete old collections
rm -rf ~/git/maia/claude/data/rag_collections/

# Re-index (optimized storage)
python3 ~/git/maia/claude/tools/email_rag_ollama.py --index
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_multi_rag_indexer.py
# [... re-index other collections ...]

# Check size after rebuild
du -sh ~/git/maia/claude/data/rag_collections/

# Before: 1.2GB → After: 850MB (350MB recovered through optimization)
```

**Fix 4: Clean Large Databases** (if huge)
```bash
# Check largest database
ls -lh ~/git/maia/claude/data/databases/*.db

# servicedesk_tickets.db: 348MB

# Vacuum to reclaim space
sqlite3 ~/git/maia/claude/data/databases/servicedesk_tickets.db "VACUUM;"

# Can recover 10-30% space depending on fragmentation
```

**Time to Fix**: 10-45 minutes (depending on cleanup scope)

---

## Section 2: Integration Issues

### 2.1 M365 Authentication Failure

**Symptoms**:
- 401 Unauthorized when calling M365 APIs
- "Invalid authentication token" error
- Email/calendar/Teams operations fail

**Diagnosis**:
```bash
# Step 1: Test M365 connection
python3 ~/git/maia/claude/tools/productivity/microsoft_graph_integration.py --test

# Output:
# ❌ Authentication: Failed
# Error: The provided credentials are invalid or expired

# Step 2: Check token expiration
python3 << 'EOF'
import jwt
from datetime import datetime
from claude.tools.production_api_credentials import M365_CLIENT_SECRET

try:
    # Decode token (if it's a JWT)
    decoded = jwt.decode(M365_CLIENT_SECRET, options={"verify_signature": False})
    exp = datetime.fromtimestamp(decoded['exp'])

    if exp < datetime.now():
        print(f"❌ Token expired: {exp}")
    else:
        print(f"✅ Token valid until: {exp}")
except:
    print("⚠️ Not a JWT token (client secret doesn't expire)")
EOF
```

**Resolution**:

**Fix 1: Regenerate Client Secret**
```bash
# Azure Portal → App registrations → Maia M365 Integration
# → Certificates & secrets → Client secrets

# Delete old secret
# Create new secret:
#   - Description: "Maia Integration (renewed Oct 2025)"
#   - Expires: 24 months
#   - Copy secret value (only shown once)

# Update credentials file
# File: claude/tools/production_api_credentials.py

M365_CLIENT_SECRET = "new_secret_value"

# Test connection
python3 ~/git/maia/claude/tools/productivity/microsoft_graph_integration.py --test

# Expected: ✅ Authentication: Success
```

**Fix 2: Verify API Permissions** (if newly regenerated token still fails)
```bash
# Azure Portal → App registrations → Maia M365 Integration → API permissions

# Ensure these permissions granted:
# - Mail.Read (Application)
# - Calendars.Read (Application)
# - Chat.Read (Application)
# - ChannelMessage.Read.All (Application)

# Click "Grant admin consent for [Org]" (requires admin)

# Wait 5-10 minutes for propagation
# Test again
```

**Time to Fix**: 5-15 minutes

---

### 2.2 Confluence Rate Limiting

**Symptoms**:
- 429 Too Many Requests error
- "Rate limit exceeded" in logs
- Confluence operations slow/fail

**Diagnosis**:
```bash
# Step 1: Check rate limit headers (from logs or manual test)
curl -I -H "Authorization: Bearer $CONFLUENCE_API_TOKEN" \
     https://your-org.atlassian.net/wiki/rest/api/content

# Response headers:
# HTTP/1.1 429 Too Many Requests
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1696512000  ← Reset timestamp

# Step 2: Calculate wait time
python3 << 'EOF'
import time
from datetime import datetime

reset_timestamp = 1696512000
now = time.time()
wait_seconds = reset_timestamp - now

print(f"Wait time: {wait_seconds:.0f} seconds ({wait_seconds/60:.1f} minutes)")
EOF
```

**Resolution**:

**Fix 1: Wait for Rate Limit Reset**
```bash
# Calculate exact reset time
python3 << 'EOF'
from datetime import datetime
reset_timestamp = 1696512000
reset_time = datetime.fromtimestamp(reset_timestamp)
print(f"Rate limit resets at: {reset_time}")
EOF

# Wait until reset time
# Then retry operation
```

**Fix 2: Implement Client-Side Rate Limiting**
```python
# Update reliable_confluence_client.py
# Add rate limiter (if not already present)

from claude.tools.productivity.reliable_confluence_client import ReliableConfluenceClient

client = ReliableConfluenceClient()

# Rate limiter: 90 requests/min (90% of Atlassian 100/min limit)
client.rate_limiter = RateLimiter(max_requests=90, window_seconds=60)

# All API calls now automatically rate limited
```

**Fix 3: Batch Operations** (reduce API calls)
```python
# Bad: Individual page fetches (100 API calls)
for page_id in page_ids:
    page = client.get_page(page_id)

# Good: Batch fetch (1 API call)
pages = client.get_pages_batch(page_ids)
```

**Time to Fix**: Immediate (wait) or 15 min (implement rate limiting)

---

## Section 3: Performance Issues

### 3.1 Context Loading Slow (>500ms)

**Symptoms**:
- Context loading takes >500ms
- Smart context loader performance degraded
- Noticeable delays in responses

**Diagnosis**:
```bash
# Step 1: Measure current load time
time python3 ~/git/maia/claude/tools/sre/smart_context_loader.py \
  "test query" --stats

# Output:
# real    0m0.850s  ← 850ms (slow)
# Strategy: moderate_complexity
# Token count: 15K

# Step 2: Check if caching enabled
python3 << 'EOF'
from claude.tools.sre.smart_context_loader import SmartContextLoader

loader = SmartContextLoader()
print(f"Cache enabled: {hasattr(loader, 'phase_cache')}")
print(f"Cache size: {len(loader.phase_cache)}")
EOF

# If cache size = 0: No caching (slow)
```

**Resolution**:

**Fix 1: Enable Phase Caching**
```python
# File: claude/tools/sre/smart_context_loader.py

# Add caching decorator
from functools import lru_cache

class SmartContextLoader:
    def __init__(self):
        self.system_state_path = Path("SYSTEM_STATE.md")
        self.phase_cache = {}  # In-memory cache

    @lru_cache(maxsize=50)  # Cache last 50 phases
    def _load_phase(self, phase_number: int) -> str:
        """Load single phase with caching"""
        # ... existing load logic ...
        return phase_content

# Result: 850ms → 120ms (86% faster)
```

**Fix 2: Optimize SYSTEM_STATE.md Parsing**
```python
# Use lazy loading (load phases on-demand, not all at once)

def load_for_intent(self, user_query: str):
    # Step 1: Intent classification (lightweight)
    intent = self._classify_intent(user_query)

    # Step 2: Select relevant phase numbers only
    relevant_phases = self._select_phases(intent)  # Returns [120, 119, 115]

    # Step 3: Load ONLY selected phases (not all 120)
    phase_content = [self._load_phase(p) for p in relevant_phases]

    # Result: 15 phases loaded vs 120 phases = 87% faster
```

**Time to Optimize**: 15-30 minutes implementation

---

### 3.2 Agent Handoff Failure

**Symptoms**:
- Multi-agent workflow stops mid-execution
- "KeyError: 'handoff_context'" in logs
- Agent coordination incomplete

**Diagnosis**:
```bash
# Step 1: Check agent workflow logs
tail -50 ~/git/maia/claude/data/logs/agent_orchestration.log

# Look for handoff errors:
# ERROR: Missing handoff_context in agent response
# ERROR: Agent 'target_agent_name' not found in registry

# Step 2: Verify handoff format
python3 << 'EOF'
# Load agent response from log
agent_response = {
    'result': {...},
    'handoff_to': 'target_agent'
    # Missing: 'handoff_context'
}

# Check required keys
required_keys = ['result', 'handoff_to', 'handoff_reason', 'handoff_context']
missing = [k for k in required_keys if k not in agent_response]

if missing:
    print(f"❌ Missing keys: {missing}")
else:
    print("✅ Handoff format correct")
EOF
```

**Resolution**:

**Fix: Correct Handoff Format**
```python
# Bad handoff (missing context):
def agent_process(context):
    result = do_work(context)

    return {
        'result': result,
        'handoff_to': 'security_specialist'
        # Missing: handoff_reason, handoff_context
    }

# Good handoff (complete):
def agent_process(context):
    result = do_work(context)

    if needs_handoff:
        return {
            'result': result,
            'handoff_to': 'security_specialist',
            'handoff_reason': 'Vulnerability found, requires security expert validation',
            'handoff_context': {
                'vulnerability_details': result['vulnerabilities'],
                'recommended_actions': ['review', 'remediate'],
                'priority': 'high'
            }
        }
    else:
        return {
            'result': result,
            'status': 'complete'
        }
```

**Time to Fix**: 5-10 minutes (code correction)

---

### 3.3 Database Locked (SQLite Concurrency)

**Symptoms**:
- "database is locked" error
- Write operations fail
- SQLite timeout errors

**Diagnosis**:
```bash
# Step 1: Check for concurrent access
lsof ~/git/maia/claude/data/databases/servicedesk_tickets.db

# Output:
# COMMAND   PID       USER     FD   TYPE
# python3   12345     user     3r   REG   servicedesk_tickets.db
# python3   12346     user     4w   REG   servicedesk_tickets.db
#                                  ↑ Write lock

# Multiple processes accessing same database

# Step 2: Check long-running transactions
sqlite3 ~/git/maia/claude/data/databases/servicedesk_tickets.db "PRAGMA busy_timeout;"

# Output: 5000 (5 second timeout)
```

**Resolution**:

**Fix 1: Increase Busy Timeout**
```python
# File: Tool accessing database

import sqlite3

conn = sqlite3.connect('servicedesk_tickets.db')

# Increase timeout (default 5 sec → 30 sec)
conn.execute("PRAGMA busy_timeout = 30000")

# Result: Waits up to 30 sec for lock release (vs failing at 5 sec)
```

**Fix 2: Use WAL Mode** (Write-Ahead Logging)
```bash
# Enable WAL mode (allows concurrent readers during writes)
sqlite3 ~/git/maia/claude/data/databases/servicedesk_tickets.db \
  "PRAGMA journal_mode=WAL;"

# Output: wal

# Verify
sqlite3 ~/git/maia/claude/data/databases/servicedesk_tickets.db \
  "PRAGMA journal_mode;"

# Output: wal (enabled)

# Result: Multiple readers + 1 writer concurrency (vs exclusive locks)
```

**Fix 3: Implement Connection Pooling**
```python
# Use singleton pattern for database connections

class DatabaseConnection:
    _instance = None
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._conn = sqlite3.connect('servicedesk_tickets.db')
            cls._conn.execute("PRAGMA busy_timeout = 30000")
            cls._conn.execute("PRAGMA journal_mode=WAL")
        return cls._conn

# Usage: All tools use same connection (reduces lock contention)
conn = DatabaseConnection.get_connection()
```

**Time to Fix**: 2-5 minutes

---

## Section 4: Emergency Procedures

### 4.1 Complete System Failure

**Symptoms**:
- Multiple tools/agents failing
- Widespread errors across system
- Cannot complete basic operations

**Emergency Recovery**:

**Step 1: System Health Check**
```bash
python3 ~/git/maia/claude/tools/sre/automated_health_monitor.py --dashboard

# Output shows multiple failures:
# ❌ UFC System: CRITICAL (missing files)
# ❌ Dependencies: CRITICAL (packages missing)
# ❌ RAG System: CRITICAL (collections unavailable)
# ❌ Local LLMs: CRITICAL (Ollama down)
# ❌ Services: CRITICAL (0/16 running)
```

**Step 2: Disaster Recovery Restoration**
```bash
# If recent backup exists:
cd ~/Library/CloudStorage/OneDrive-YOUR_ORG/MaiaBackups/
ls -lt | head -5

# Find most recent backup
# full_20251015_030000/

cd full_20251015_030000/
./restore_maia.sh

# Follow restoration prompts
# Time: 28 minutes for complete restoration
```

**Step 3: Verify Restoration**
```bash
# Re-run health check
python3 ~/git/maia/claude/tools/sre/automated_health_monitor.py --dashboard

# Expected: All systems ✅ HEALTHY
```

**Prevention**:
- Daily automated backups (already configured)
- Test restoration quarterly
- Document critical procedures
- Keep backup credentials secure

---

## Section 5: Debug Workflows

### 5.1 Systematic Debugging Process

**General Debug Workflow**:

**Step 1: Reproduce Issue**
```bash
# Document exact steps to reproduce
# Example:
1. Run command: python3 tool.py --arg value
2. Expected: Success output
3. Actual: Error XYZ
```

**Step 2: Check Logs**
```bash
# Find relevant log file
ls ~/git/maia/claude/data/logs/

# View recent entries
tail -100 ~/git/maia/claude/data/logs/[relevant-log].log

# Search for errors
grep -i "error\|exception\|fail" ~/git/maia/claude/data/logs/[relevant-log].log
```

**Step 3: Enable Debug Logging**
```python
# Add to tool file
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Throughout code:
logger.debug(f"Variable value: {var}")
logger.debug(f"Function entered with: {args}")
```

**Step 4: Isolate Component**
```python
# Test individual functions
if __name__ == '__main__':
    # Test function directly
    result = problematic_function(test_input)
    print(f"Result: {result}")
```

**Step 5: Check Dependencies**
```bash
# Verify all dependencies present
pip check

# If issues:
pip install --upgrade [package-name]
```

**Step 6: Document Solution**
```bash
# After fixing:
# 1. Document issue in this playbook (if common)
# 2. Update tool documentation
# 3. Add test case to prevent regression
```

---

## Section 6: Monitoring & Prevention

### 6.1 Proactive Monitoring Setup

**Daily Health Check**:
```bash
# Add to crontab or LaunchAgent
# Check system health every morning

0 8 * * * /usr/local/bin/python3 \
  ~/git/maia/claude/tools/sre/automated_health_monitor.py \
  --email-report
```

**Alert on Critical Issues**:
```bash
# Configure alerts for:
# - Critical vulnerabilities detected
# - RAG collections >7 days stale
# - Background services failed >3 times
# - Disk space <10GB remaining
# - Backup failures

# Email/Slack notifications
```

**Weekly Maintenance**:
```bash
# Automated weekly tasks
# Friday 5pm

0 17 * * 5 /usr/local/bin/python3 \
  ~/git/maia/claude/tools/sre/weekly_maintenance.py
```

---

## Appendix: Quick Command Reference

**System Health**:
```bash
python3 ~/git/maia/claude/tools/sre/automated_health_monitor.py --dashboard
```

**Service Status**:
```bash
launchctl list | grep maia
```

**RAG Collections**:
```bash
python3 -c "import chromadb; c=chromadb.PersistentClient(path='~/git/maia/claude/data/rag_collections'); print([f'{x.name}: {x.count()}' for x in c.list_collections()])"
```

**Local LLM Status**:
```bash
ollama list
```

**Disk Space**:
```bash
df -h | grep disk1s1
```

**Recent Logs**:
```bash
tail -50 ~/git/maia/claude/data/logs/*.log
```

---

## Document Suite Complete

This Troubleshooting Playbook completes the 8-document team onboarding suite:

1. **Executive Overview** - Business case + strategic value
2. **Technical Architecture Guide** - Deep technical design
3. **Developer Onboarding Package** - Getting started + workflows
4. **Operations Quick Reference** - Daily operations + maintenance
5. **Use Case Compendium** - Real-world scenarios + success stories
6. **Integration Guide** - M365, Confluence, ServiceDesk integration
7. **Troubleshooting Playbook** (this document) - Debug procedures
8. **Metrics & ROI Dashboard** - Financial performance + impact

**Recommended Usage**:
- **Bookmark**: Keep this playbook accessible for quick reference
- **Update**: Add new issues as discovered
- **Share**: Distribute to operations/support teams
- **Test**: Practice emergency procedures quarterly

---

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**Status**: ✅ Publishing-Ready
**Audience**: Operations, Support, Developers
**Reading Time**: 25-30 minutes
**Coverage**: 15 common issues + emergency procedures + systematic debug workflows
