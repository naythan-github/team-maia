# Maia Team Setup

Welcome to Maia! This repository has been prepared for team sharing with personal data removed.

## Quick Start

### For Windows Laptops (WSL)

1. **Run prerequisite setup**:
   ```powershell
   # In PowerShell (Admin):
   cd claude/tools/sre
   .\setup_wsl_prerequisites.ps1
   ```

2. **Follow onboarding guide**:
   - Read: `claude/tools/sre/TEAM_ONBOARDING_WSL.md`

3. **Install dependencies**:
   ```bash
   cd ~/maia
   pip3 install -r requirements.txt
   ```

4. **Configure credentials**:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials
   - OR create `claude/tools/production_api_credentials.py` with your credentials

### For macOS

1. **Clone this repository**:
   ```bash
   git clone [repo-url] ~/git/maia
   cd ~/git/maia
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure credentials**:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials

## What's Missing (Intentionally)

- ❌ **Databases** - Personal data removed. You'll create fresh databases or restore from backup.
- ❌ **Credentials** - Use `.env.example` as template
- ❌ **Personal configurations** - Customize `.claude/settings.local.json` for your environment
- ❌ **Logs** - Fresh start

## Documentation

- **System Overview**: `CLAUDE.md`
- **Recent Changes**: `SYSTEM_STATE.md`
- **WSL Onboarding**: `claude/tools/sre/TEAM_ONBOARDING_WSL.md`
- **WSL Technical Guide**: `claude/tools/sre/WSL_RESTORE_GUIDE.md`
- **Capabilities**: `claude/context/core/capability_index.md`

## Getting Help

1. Check the documentation above
2. Review troubleshooting in `TEAM_ONBOARDING_WSL.md`
3. Ask your team lead

Welcome to the team! 🎉
