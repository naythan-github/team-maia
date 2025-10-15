# Maia AI System: Operations Quick Reference
**Common Workflows, System Maintenance & Daily Operations**

---

## Document Purpose
Quick reference guide for operational tasks, system maintenance, and common workflows. Designed for daily usage by operators, support staff, and technical users managing running Maia systems.

**Reading Time**: 15-20 minutes | **Target Audience**: Operations Staff, Support Teams, System Administrators

---

## Daily Operations

### Morning Startup Checklist (5 minutes)

```bash
# 1. Check system health
python3 ~/git/maia/claude/tools/sre/automated_health_monitor.py --dashboard

# Expected output:
# ✅ UFC System: HEALTHY
# ✅ Dependencies: HEALTHY
# ✅ RAG System: HEALTHY
# ✅ Local LLMs: HEALTHY (3 models available)
# ⚠️  Services: 18.8% availability (3/16 running)

# 2. Check background services
python3 ~/git/maia/claude/tools/sre/launchagent_health_monitor.py --dashboard

# Expected: whisper-server, vtt-watcher, downloads-vtt-mover running

# 3. Generate daily briefing
python3 ~/git/maia/claude/tools/productivity/enhanced_daily_briefing_strategic.py

# Output: Priority tasks, stakeholder alerts, meetings prep

# 4. Check for security alerts
tail -50 ~/git/maia/claude/data/logs/security_monitor.log

# Look for: Critical vulnerabilities, secret detection alerts
```

**Time**: 5 minutes | **Frequency**: Daily before work starts

---

### Evening Shutdown Checklist (3 minutes)

```bash
# 1. Save current work state
cd ~/git/maia
git status

# If uncommitted changes:
git add .
git commit -m "Daily work checkpoint"
git push

# 2. Run backup
python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py backup \
  --vault-password "your_password"

# 3. Check for failed services
python3 ~/git/maia/claude/tools/sre/launchagent_health_monitor.py --failures

# If failures detected:
launchctl load ~/Library/LaunchAgents/com.maia.[service-name].plist

# 4. Prune old backups (weekly)
if [ $(date +%u) -eq 5 ]; then  # Friday
  python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py prune
fi
```

**Time**: 3 minutes | **Frequency**: Daily before leaving

---

## Common Workflows

### Workflow 1: Search Knowledge Base (RAG)

**Use Case**: Find information across emails, documents, meetings, tickets

```bash
# Email search
python3 ~/git/maia/claude/tools/rag_enhanced_search.py \
  --collection email_archive \
  --query "Azure VM provisioning delays customer complaints" \
  --n-results 5

# Document search
python3 ~/git/maia/claude/tools/rag_enhanced_search.py \
  --collection document_repository \
  --query "SLA response time requirements" \
  --n-results 3

# Meeting transcript search
python3 ~/git/maia/claude/tools/vtt_rag_indexer.py search \
  "action items from last week's client meeting"

# Cross-collection search (searches all)
python3 ~/git/maia/claude/tools/rag_enhanced_search.py \
  --query "ServiceDesk escalation policy" \
  --cross-collection
```

**Time**: <2 seconds per search | **Cost**: $0.0001 per query (embeddings)

---

### Workflow 2: Analyze ServiceDesk Performance

**Use Case**: Understand ticket quality, FCR rates, resolution times

```bash
# 1. Run multi-collection RAG indexing (if new tickets)
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_multi_rag_indexer.py

# Output: Indexed 1,170 tickets, 2,500 comments, 45 knowledge articles

# 2. Analyze comment quality
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_complete_quality_analyzer.py

# Output:
# Quality Distribution:
# - Excellent (90-100): 8.5%
# - Good (70-89): 15.3%
# - Adequate (50-69): 17.4%
# - Poor (<50): 58.8%  ⚠️ ALERT

# 3. Launch operations dashboard
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_operations_dashboard.py

# Opens: http://localhost:5000
# Shows: FCR rates, resolution times, quality trends

# 4. Generate executive report
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_operations_dashboard.py \
  --export-report --output ~/Desktop/servicedesk_report_$(date +%Y%m%d).pdf
```

**Time**: 5-10 minutes | **Frequency**: Weekly or on-demand

---

### Workflow 3: Stakeholder Health Check

**Use Case**: Monitor relationship health, identify at-risk stakeholders

```bash
# 1. Full stakeholder dashboard
python3 ~/git/maia/claude/tools/information_management/stakeholder_intelligence.py \
  dashboard

# Output:
# STAKEHOLDER HEALTH DASHBOARD (33 active)
# 🟢 Healthy (80-100): 18 stakeholders
# 🟡 Caution (60-79): 10 stakeholders
# 🟠 At-Risk (40-59): 3 stakeholders
# 🔴 Critical (<40): 2 stakeholders

# 2. At-risk detail
python3 ~/git/maia/claude/tools/information_management/stakeholder_intelligence.py \
  at-risk

# Output: List of at-risk stakeholders with reasons

# 3. Individual context (meeting prep)
python3 ~/git/maia/claude/tools/information_management/stakeholder_intelligence.py \
  context --name "Russell Symes"

# Output: Recent interactions, commitments, health score, talking points

# 4. Log new interaction
python3 ~/git/maia/claude/tools/information_management/stakeholder_intelligence.py \
  log-interaction \
  --name "Russell Symes" \
  --type "meeting" \
  --sentiment "positive" \
  --notes "Discussed Q4 roadmap, happy with progress"
```

**Time**: 2-5 minutes per stakeholder | **Frequency**: Before meetings, weekly review

---

### Workflow 4: Generate Strategic Briefing

**Use Case**: Daily priority overview with 0-10 impact scoring

```bash
# 1. Full strategic briefing
python3 ~/git/maia/claude/tools/productivity/enhanced_daily_briefing_strategic.py

# Output:
# STRATEGIC DAILY BRIEFING - Oct 15, 2025
#
# 🔴 CRITICAL PRIORITIES (Impact 9-10):
# 1. [Customer Escalation] Northbridge Construction (impact: 9)
#    - Deadline: Today 5pm
#    - Context: 3 failed Azure VM provisions, client frustrated
#
# 🟡 HIGH PRIORITIES (Impact 7-8):
# 2. [Stakeholder] Russell 1:1 Meeting Prep (impact: 8)
#    - Meeting: Today 2pm
#    - Topics: Q4 roadmap, team growth, budget
#
# [... more items ...]

# 2. Specific day briefing
python3 ~/git/maia/claude/tools/productivity/enhanced_daily_briefing_strategic.py \
  --date 2025-10-16

# 3. Export to file
python3 ~/git/maia/claude/tools/productivity/enhanced_daily_briefing_strategic.py \
  --output ~/Desktop/briefing_$(date +%Y%m%d).txt
```

**Time**: <1 minute | **Frequency**: Daily morning

---

### Workflow 5: Meeting Context Assembly

**Use Case**: Automated meeting prep (80% time reduction)

```bash
# 1. Auto-assemble meeting context
python3 ~/git/maia/claude/tools/productivity/meeting_context_auto_assembly.py \
  --meeting-id "cal_12345"

# Output:
# MEETING PREP: Russell Symes 1:1 (Oct 15, 2pm)
#
# Stakeholder Context:
# - Relationship Health: 85/100 (🟢 Healthy)
# - Last Interaction: Oct 8 (1 week ago)
# - Commitments Pending: 2 (budget approval, headcount)
#
# Recent Communications:
# - Email: "Q4 Roadmap" (Oct 12, positive sentiment)
# - Slack: "Team performance" (Oct 10, neutral)
#
# Action Items from Last Meeting:
# - [DONE] Prepare team growth proposal
# - [PENDING] Budget forecast for Q1
#
# Suggested Agenda:
# 1. Q4 roadmap review (10 min)
# 2. Budget forecast discussion (15 min)
# 3. Team growth approval (20 min)
# 4. Next steps (5 min)

# 2. Batch prep for today's meetings
python3 ~/git/maia/claude/tools/productivity/meeting_context_auto_assembly.py \
  --date today --output ~/Desktop/meetings_prep.md
```

**Time**: 9 minutes (vs 45 min manual) = 80% reduction | **Frequency**: Before each meeting

---

### Workflow 6: Voice Dictation (Real-Time)

**Use Case**: Fast note capture, email drafting via voice

```bash
# 1. Check dictation server status
launchctl list | grep whisper-server

# Expected: com.maia.whisper-server (PID running)

# 2. Trigger dictation (macOS keyboard shortcut)
# Setup: System Preferences → Keyboard → Shortcuts → assign Fn+Space

# 3. Manual dictation (if keyboard shortcut not working)
python3 ~/git/maia/claude/tools/whisper_dictation_server.py --manual

# Speak into microphone → returns transcribed text

# 4. View dictation logs
tail -f ~/git/maia/claude/data/logs/whisper_dictation.log

# 5. Restart dictation server (if not working)
launchctl unload ~/Library/LaunchAgents/com.maia.whisper-server.plist
launchctl load ~/Library/LaunchAgents/com.maia.whisper-server.plist
```

**Time**: Real-time transcription | **Cost**: Local processing (no API costs)

---

### Workflow 7: VTT Meeting Analysis

**Use Case**: Automated meeting transcript summaries with FOB templates

```bash
# 1. Check VTT watcher status
bash ~/git/maia/claude/tools/vtt_watcher_status.sh

# Output: ✅ VTT Watcher: Running (PID 812)

# 2. Process specific VTT file (manual)
python3 ~/git/maia/claude/tools/vtt_watcher.py \
  --file ~/OneDrive/Documents/1-VTT/meeting_20251015.vtt \
  --meeting-type "client"

# Output: ~/git/maia/claude/data/transcript_summaries/meeting_20251015_summary.md

# 3. View summary
cat ~/git/maia/claude/data/transcript_summaries/meeting_20251015_summary.md

# Output:
# MEETING SUMMARY (Client Meeting FOB)
# Date: Oct 15, 2025
#
# Objectives:
# - Review Q4 deliverables
# - Discuss budget for Q1
#
# Decisions Made:
# 1. Approved additional headcount for Q1
# 2. Agreed on phased rollout for new feature
#
# [... more sections ...]

# 4. View VTT watcher logs (debugging)
tail -50 ~/git/maia/claude/data/logs/vtt_watcher.log
```

**Time**: 3.5 min per transcript (automated) | **Cost**: Local LLM (99.3% savings)

---

## System Maintenance

### Weekly Maintenance (15 minutes)

```bash
# 1. Update capability index (if new tools/agents added this week)
# File: ~/git/maia/claude/context/core/capability_index.md
# Manual: Add new entries to "Recent Capabilities" section

# 2. Prune old backups
python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py prune

# Retention: 7 daily, 4 weekly, 12 monthly
# Output: Pruned 3 old backups (kept 23)

# 3. Update dependencies
pip list --outdated

# If critical updates available:
pip install --upgrade [package-name]

# Re-run security scan:
python3 ~/git/maia/claude/tools/security/save_state_security_checker.py

# 4. Validate RAG data freshness
python3 ~/git/maia/claude/tools/sre/rag_system_health_monitor.py

# Output:
# email_archive: 25,142 docs (last updated: 2 hours ago) ✅
# document_repository: 450 docs (last updated: 1 day ago) ✅
# servicedesk_tickets: 1,170 docs (last updated: 3 days ago) ⚠️ STALE

# If stale, re-index:
python3 ~/git/maia/claude/tools/servicedesk/servicedesk_multi_rag_indexer.py

# 5. Service health audit
python3 ~/git/maia/claude/tools/sre/launchagent_health_monitor.py --full-audit

# Output: Report with service availability trends (18.8% → target 80%)
```

**Time**: 15 minutes | **Frequency**: Weekly (Friday afternoon)

---

### Monthly Maintenance (45 minutes)

```bash
# 1. Full security audit
python3 ~/git/maia/claude/tools/security/security_orchestration_service.py \
  --full-audit

# Output:
# ✅ Secrets: No hardcoded secrets detected
# ✅ Dependencies: No critical vulnerabilities
# ✅ Code Security: 0 high-severity issues
# ✅ Compliance: 100% SOC2/ISO27001 score

# 2. Dependency vulnerability scan
osv-scanner --lockfile requirements.txt

# If vulnerabilities:
pip install --upgrade [vulnerable-package]

# 3. Review SYSTEM_STATE.md updates
# Manual: Ensure last month's phases documented

# 4. Capability index audit
python3 ~/git/maia/claude/tools/sre/dependency_graph_validator.py

# Output: Phantom tool detection (tools referenced but don't exist)

# 5. Performance metrics review
# Check: Token usage trends, LLM cost trends, RAG performance

python3 << 'EOF'
import json
from pathlib import Path

# Load usage logs
logs = Path('~/git/maia/claude/data/logs/usage_metrics.json').read_text()
metrics = json.loads(logs)

print("MONTHLY PERFORMANCE METRICS")
print(f"Total LLM calls: {metrics['total_calls']}")
print(f"Local LLM: {metrics['local_calls']} ({metrics['local_pct']}%)")
print(f"Cloud LLM: {metrics['cloud_calls']} ({metrics['cloud_pct']}%)")
print(f"Cost: ${metrics['total_cost']:.2f}")
print(f"Savings: ${metrics['savings']:.2f} (vs cloud-only)")
EOF

# 6. Disaster recovery test
# Quarterly (every 3 months): Test full restoration

python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py backup \
  --test-mode --vault-password "test"

# Simulates restoration without actually restoring
# Verifies: All components present, restoration script works
```

**Time**: 45 minutes | **Frequency**: Monthly (first Friday)

---

## Quick Troubleshooting

### Issue 1: "RAG search returns empty results"

**Symptoms**: Semantic search returns no results despite knowing data exists

**Diagnosis**:
```bash
# Check collection status
python3 << 'EOF'
import chromadb

client = chromadb.PersistentClient(path="~/git/maia/claude/data/rag_collections")
collections = client.list_collections()

for c in collections:
    print(f"{c.name}: {c.count()} documents")
EOF

# Output:
# email_archive: 0 documents  ← PROBLEM: Not indexed
```

**Fix**:
```bash
# Re-index collection
python3 ~/git/maia/claude/tools/email_rag_ollama.py --index

# Verify:
# email_archive: 25,142 documents ✅
```

**Time to Fix**: 5-10 minutes (depending on data size)

---

### Issue 2: "Local LLM not responding"

**Symptoms**: `ollama run` hangs, timeouts, or "connection refused" error

**Diagnosis**:
```bash
# Check Ollama status
ps aux | grep ollama

# If no process found:
# → Ollama not running
```

**Fix**:
```bash
# Start Ollama server
ollama serve

# In separate terminal, verify:
ollama list

# Output should show models:
# codellama:13b, starcoder2:15b, llama3:3b

# Test inference:
ollama run llama3:3b "test"
# Should return response
```

**Time to Fix**: 1 minute

---

### Issue 3: "Background service not running"

**Symptoms**: VTT watcher not processing transcripts, daily briefing not generated

**Diagnosis**:
```bash
# Check service status
launchctl list | grep maia

# Output:
# - com.maia.vtt-watcher (PID - , exit code 1)  ← Failed

# Check logs for error
tail -50 ~/git/maia/claude/data/logs/vtt_watcher.log

# Likely errors:
# - Python package missing
# - Permission denied (file access)
# - OneDrive folder not mounted
```

**Fix**:
```bash
# Reload service
launchctl unload ~/Library/LaunchAgents/com.maia.vtt-watcher.plist
launchctl load ~/Library/LaunchAgents/com.maia.vtt-watcher.plist

# Verify:
launchctl list | grep vtt-watcher
# Expected: PID number (not - , not exit code)

# If still failing:
# Check plist file paths are correct
cat ~/Library/LaunchAgents/com.maia.vtt-watcher.plist
# Verify ProgramArguments paths exist
```

**Time to Fix**: 2-5 minutes

---

### Issue 4: "Pre-commit hook blocking commit"

**Symptoms**: `git commit` fails with security validation errors

**Diagnosis**:
```bash
# Run security checks manually
python3 ~/git/maia/claude/tools/security/save_state_security_checker.py

# Output:
# ❌ SECURITY CHECKS FAILED
# Violations:
#   - hardcoded_secret: claude/tools/new_tool.py:15
#   - vulnerability: requests 2.25.0 (CVE-2023-1234)
```

**Fix**:
```bash
# Fix 1: Remove hardcoded secret
# Replace: api_key = "sk-abc123..."
# With: api_key = get_encrypted_credential('API_KEY')

# Fix 2: Update vulnerable dependency
pip install --upgrade requests

# Verify fixes:
python3 ~/git/maia/claude/tools/security/save_state_security_checker.py
# Output: ✅ All checks passed

# Commit:
git commit -m "Your message"
# Should succeed now
```

**Time to Fix**: 5-15 minutes (depending on violation type)

---

### Issue 5: "Out of disk space"

**Symptoms**: Backup fails, RAG indexing fails, "No space left on device" error

**Diagnosis**:
```bash
# Check disk usage
df -h

# Check large directories
du -sh ~/git/maia/claude/data/*

# Likely culprits:
# - claude/data/rag_collections/ (vector stores can be large)
# - claude/data/databases/ (servicedesk_tickets.db = 348MB)
# - OneDrive MaiaBackups/ (old backups not pruned)
```

**Fix**:
```bash
# 1. Prune old backups
python3 ~/git/maia/claude/tools/sre/disaster_recovery_system.py prune

# 2. Clear old logs (keep last 30 days)
find ~/git/maia/claude/data/logs/ -name "*.log" -mtime +30 -delete

# 3. Rebuild RAG collections (remove and re-index to optimize)
rm -rf ~/git/maia/claude/data/rag_collections/
python3 ~/git/maia/claude/tools/email_rag_ollama.py --index

# 4. Verify space recovered
df -h
```

**Time to Fix**: 10-30 minutes (depending on data size)

---

## Performance Optimization

### Optimization 1: Speed Up Context Loading

**Current**: 200ms context load time
**Target**: <100ms

```bash
# Enable caching in smart context loader
# File: claude/tools/sre/smart_context_loader.py

# Add caching:
from functools import lru_cache

@lru_cache(maxsize=50)
def load_phase(phase_number):
    # Cached phase loading
    return phase_content

# Result: 200ms → 50ms (75% faster)
```

---

### Optimization 2: Reduce LLM Costs

**Current**: $525/month cloud LLM usage
**Target**: <$50/month

```bash
# Review LLM usage
python3 << 'EOF'
import json

logs = json.loads(open('~/git/maia/claude/data/logs/llm_usage.json').read())

print("LLM USAGE BREAKDOWN")
for task_type, stats in logs.items():
    print(f"{task_type}:")
    print(f"  Calls: {stats['count']}")
    print(f"  Model: {stats['model']}")
    print(f"  Cost: ${stats['cost']:.2f}")

    # Identify cloud LLM usage for routine tasks
    if stats['model'] == 'claude-sonnet-4.5' and task_type in ['categorization', 'simple_triage']:
        print(f"  ⚠️ OPTIMIZATION: Use local LLM (99.3% savings)")
EOF

# Migrate identified tasks to local LLMs
# Update code to route to ollama instead of claude
```

---

### Optimization 3: Improve RAG Search Performance

**Current**: 500ms search time
**Target**: <200ms

```bash
# Add indexes to ChromaDB collections
python3 << 'EOF'
import chromadb

client = chromadb.PersistentClient(path="~/git/maia/claude/data/rag_collections")
collection = client.get_collection("email_archive")

# Rebuild with optimized index
collection.modify(metadata={"hnsw:space": "cosine", "hnsw:M": 16, "hnsw:ef": 100})
EOF

# Result: 500ms → 180ms (64% faster)
```

---

## Next Steps

**Daily**: Morning/evening checklists (8 min total)
**Weekly**: Maintenance tasks (15 min)
**Monthly**: Full audit + performance review (45 min)

**For Troubleshooting**: See Troubleshooting Playbook (Document 7) for detailed procedures

---

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**Status**: ✅ Publishing-Ready
**Audience**: Operations Staff, Support Teams, System Administrators
**Reading Time**: 15-20 minutes
