# Team Repository Sharing Guide

**Purpose**: Step-by-step guide for creating a clean, shareable version of Maia
**Audience**: Repository owner preparing Maia for team distribution
**Version**: 1.0 (2025-10-21)

---

## Quick Start (Automated)

### Run the Cleanup Script

```bash
cd ~/git/maia

# Make script executable
chmod +x claude/tools/sre/prepare_team_repo.sh

# Run cleanup (creates clean copy in /tmp/maia-team-share)
./claude/tools/sre/prepare_team_repo.sh

# Review the clean copy
cd /tmp/maia-team-share
```

**That's it!** The script automatically:
- ✅ Clones your repository to a clean location
- ✅ Removes all personal data (databases, credentials, logs)
- ✅ Replaces personal references with placeholders
- ✅ Creates team setup documentation
- ✅ Commits cleanup changes

---

## What Gets Removed

### 1. Personal Data
- ❌ All databases (`claude/data/*.db`)
- ❌ Database temp files (`.db-shm`, `.db-wal`)
- ❌ Your personal email, calendar, meeting data
- ❌ Private conversations or notes

### 2. Credentials & Secrets
- ❌ `claude/tools/production_api_credentials.py`
- ❌ `credentials.vault.enc`
- ❌ `.env` files
- ❌ Any `.pem`, `.key` files
- ❌ API tokens, passwords

### 3. Personal Configurations
- ❌ `.claude/settings.local.json` (your VSCode permissions)
- ❌ `.claude/hooks.local.json`
- ❌ Personal IDE settings (`.vscode/`, `.idea/`)

### 4. Logs & Temporary Files
- ❌ All log files (`claude/logs/**/*.log`)
- ❌ Python cache (`__pycache__/`, `*.pyc`)
- ❌ macOS files (`.DS_Store`)
- ❌ Swap files (`*.swp`)

### 5. Personal References
- ❌ Your name (`naythandawe` → `YOUR_USERNAME`)
- ❌ Organization name (`ORROPTYLTD` → `YOUR_ORG`)
- ❌ Full paths (`/Users/naythandawe/` → `/Users/YOUR_USERNAME/`)

---

## What Gets Added

### 1. Team Setup Documentation
- ✅ `TEAM_SETUP_README.md` - Quick start guide for team
- ✅ `.env.example` - Template for environment variables
- ✅ `production_api_credentials.py` - Placeholder with examples

### 2. Updated .gitignore
- ✅ Prevents accidental commits of:
  - Credentials
  - Personal databases
  - Personal configurations
  - Logs

---

## Step-by-Step Process

### Step 1: Prepare Your Repository

**Option A: Use Latest Committed Code** (Recommended)
```bash
# Ensure latest changes are committed
cd ~/git/maia
git status

# Commit any pending changes
git add -A
git commit -m "Latest updates before team sharing"
```

**Option B: Include Uncommitted Changes**
- The script clones from your working directory
- Uncommitted changes will be included
- Review carefully before sharing

---

### Step 2: Run Cleanup Script

```bash
cd ~/git/maia
chmod +x claude/tools/sre/prepare_team_repo.sh

# Basic usage (default settings)
./claude/tools/sre/prepare_team_repo.sh

# Advanced usage (custom paths/names)
./claude/tools/sre/prepare_team_repo.sh \
    /Users/naythandawe/git/maia \
    /tmp/maia-team-share \
    naythandawe \
    ORROPTYLTD
```

**Parameters**:
- `$1` - Source repository path (default: `/Users/naythandawe/git/maia`)
- `$2` - Clean repository path (default: `/tmp/maia-team-share`)
- `$3` - Your username to replace (default: `naythandawe`)
- `$4` - Your organization to replace (default: `ORROPTYLTD`)

---

### Step 3: Review Clean Repository

```bash
cd /tmp/maia-team-share

# Check for any remaining personal data
grep -r "naythandawe" . 2>/dev/null | grep -v ".git"
grep -r "ORROPTYLTD" . 2>/dev/null | grep -v ".git"

# Verify sensitive files removed
ls -la claude/tools/production_api_credentials.py  # Should show placeholder
ls -la credentials.vault.enc  # Should not exist

# Check placeholders are in place
cat .env.example
cat TEAM_SETUP_README.md
```

**Look for**:
- ✅ No real credentials
- ✅ No personal database files
- ✅ Placeholders with "YOUR_USERNAME" / "YOUR_ORG"
- ✅ Team documentation present

---

### Step 4: Test the Clean Repository

**Quick Test** (verify it works):
```bash
cd /tmp/maia-team-share

# Check Python imports
python3 -c "import sys; sys.path.insert(0, '.'); print('Import test passed')"

# Verify key tools exist
ls -lh claude/tools/sre/setup_wsl_prerequisites.ps1
ls -lh claude/tools/sre/TEAM_ONBOARDING_WSL.md
ls -lh claude/tools/sre/disaster_recovery_system.py

# Check documentation
cat TEAM_SETUP_README.md
```

---

### Step 5: Share with Team

**Option A: Create Git Repository** (Recommended for active development)

```bash
cd /tmp/maia-team-share

# Remove old git remote
git remote remove origin

# Add new team repository
git remote add origin https://github.com/your-org/maia-team.git
# OR
git remote add origin git@github.com:your-org/maia-team.git

# Push to team repo
git push -u origin main

# Share repository URL with team
echo "Team members can clone from: https://github.com/your-org/maia-team.git"
```

---

**Option B: Create Archive** (For one-time distribution)

```bash
cd /tmp

# Create compressed archive
tar -czf maia-team-$(date +%Y%m%d).tar.gz maia-team-share/

# Check size
ls -lh maia-team-*.tar.gz

# Share via OneDrive
cp maia-team-*.tar.gz "/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/Team Resources/"
```

---

**Option C: Share via OneDrive Folder**

```bash
# Copy clean repository to OneDrive
cp -r /tmp/maia-team-share "/Users/YOUR_USERNAME/OneDrive - YOUR_ORG/Maia Team Repository/"

# Share OneDrive link with team
```

---

## Team Member Instructions

Once you share the repository, team members should:

### Windows Laptop (WSL) Users

1. **Clone or extract repository**:
   ```bash
   git clone [team-repo-url] ~/maia
   # OR
   tar -xzf maia-team-20251021.tar.gz
   ```

2. **Run prerequisite setup**:
   ```powershell
   cd maia/claude/tools/sre
   .\setup_wsl_prerequisites.ps1
   ```

3. **Follow onboarding guide**:
   - Read: `TEAM_SETUP_README.md`
   - Then: `claude/tools/sre/TEAM_ONBOARDING_WSL.md`

4. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### macOS Users

1. **Clone repository**:
   ```bash
   git clone [team-repo-url] ~/git/maia
   cd ~/git/maia
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

---

## Advanced: Manual Cleanup

If you prefer manual control, here's what to clean:

### 1. Clone Repository
```bash
git clone ~/git/maia /tmp/maia-team-share
cd /tmp/maia-team-share
```

### 2. Remove Databases
```bash
find claude/data -name "*.db*" -type f -delete
```

### 3. Remove Credentials
```bash
rm -f claude/tools/production_api_credentials.py
rm -f credentials.vault.enc
rm -f .env
find . -name ".env" -type f -delete
```

### 4. Remove Personal Configs
```bash
rm -f .claude/settings.local.json
```

### 5. Remove Logs
```bash
find claude/logs -type f -delete
```

### 6. Replace References
```bash
# Replace your name
find . -type f \( -name "*.py" -o -name "*.md" \) \
    -exec sed -i '' 's/naythandawe/YOUR_USERNAME/g' {} \;

# Replace org
find . -type f \( -name "*.py" -o -name "*.md" \) \
    -exec sed -i '' 's/ORROPTYLTD/YOUR_ORG/g' {} \;

# Replace paths
find . -type f \( -name "*.py" -o -name "*.md" \) \
    -exec sed -i '' 's|/Users/naythandawe|/Users/YOUR_USERNAME|g' {} \;
```

---

## Verification Checklist

Before sharing, verify:

- [ ] No real credentials in repository
- [ ] No personal databases (`.db` files)
- [ ] No personal configurations (`.claude/settings.local.json`)
- [ ] No logs with personal data
- [ ] Personal references replaced with placeholders
- [ ] Team documentation created (`TEAM_SETUP_README.md`)
- [ ] `.env.example` template present
- [ ] `.gitignore` updated to prevent future commits of sensitive data
- [ ] Repository tested (Python imports work, key files exist)

---

## Troubleshooting

### Issue: "sed: invalid command code" on Linux

**Cause**: macOS vs Linux sed syntax difference

**Solution**: Remove `-i ''` from sed commands:
```bash
# macOS
sed -i '' 's/old/new/g' file

# Linux
sed -i 's/old/new/g' file
```

The prepare_team_repo.sh script handles this automatically.

---

### Issue: "Repository too large" when sharing

**Cause**: Git history may contain large files

**Solution**: Clean git history (DESTRUCTIVE - use with caution):
```bash
cd /tmp/maia-team-share

# Remove large files from history
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch claude/data/*.db' \
    --prune-empty --tag-name-filter cat -- --all

# Force garbage collection
git gc --aggressive --prune=now
```

---

### Issue: Team members can't find documentation

**Cause**: Documentation not obvious

**Solution**: `TEAM_SETUP_README.md` is created automatically at root and points to all documentation.

---

## Summary

**Automated Process** (Recommended):
1. Run `./claude/tools/sre/prepare_team_repo.sh`
2. Review `/tmp/maia-team-share`
3. Push to team git repository OR create archive
4. Share with team

**Manual Process** (For custom control):
1. Clone repository
2. Remove personal data (databases, credentials, logs, configs)
3. Replace personal references
4. Create team documentation
5. Test and share

**What Team Gets**:
- ✅ Full Maia codebase
- ✅ All tools and agents
- ✅ Setup automation (WSL prerequisite script)
- ✅ Complete documentation
- ✅ Credential templates

**What Team Doesn't Get** (intentionally):
- ❌ Your personal databases
- ❌ Your credentials/API keys
- ❌ Your personal configurations
- ❌ Your logs

---

**Ready to share Maia with your team! 🎉**

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Script**: `claude/tools/sre/prepare_team_repo.sh`
