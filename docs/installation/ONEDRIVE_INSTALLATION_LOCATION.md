# Official Windows Installation Package Location

**Status:** 📍 Files Moved to OneDrive Shared Storage
**Date:** 2026-01-11

---

## Default Installation Location

All Windows installation scripts and documentation are now stored in:

**OneDrive Path:**
```
/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/remote-shared/maia-windows-installation/
```

**Network Access (from Windows RDP/VMs):**
```powershell
# If Z: drive mapped:
Z:\maia-windows-installation\

# Or via OneDrive:
%OneDrive%\Documents\remote-shared\maia-windows-installation\

# Or full path:
\\onedrive\Documents\remote-shared\maia-windows-installation\
```

---

## Why OneDrive?

1. **Shared Access** - Accessible from all RDP sessions and VMs
2. **Auto-Sync** - Always has latest version
3. **No Git Clone Required** - Can run directly from network share
4. **Team Access** - Other team members can access same files

---

## Files Available

### Installation Scripts:
- **Install-MaiaEnvironment-v3.1-FIXED.ps1** ✅ (Recommended - all fixes applied)
- Install-MaiaEnvironment-v3.ps1 (v3.0 - has known issues)
- Install-MaiaEnvironment.ps1 (v2.x - deprecated)

### Documentation:
- **README.md** - Quick start guide
- **INSTALLATION_ISSUES_REPORT.md** - Bug analysis and fixes
- **INSTALLATION_FIX_SUMMARY.md** - Before/after comparison
- WINDOWS_PRO_SETUP.md - Manual installation guide
- INSTALLATION_GUIDE.md - General guide
- setup_windows_maia.md - Command reference

---

## Quick Start

```powershell
# On Windows (PowerShell as Administrator):
cd Z:\maia-windows-installation
.\Install-MaiaEnvironment-v3.1-FIXED.ps1
```

For detailed instructions, see the [README.md](../../Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/remote-shared/maia-windows-installation/README.md) in the OneDrive location.

---

## Local Copies in Repository

The following files remain in the git repository for reference:

- [docs/installation/WINDOWS_PRO_SETUP.md](WINDOWS_PRO_SETUP.md) - Manual guide (may be outdated)
- [docs/installation/INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - General guide (may be outdated)
- [claude/tools/sre/Install-MaiaEnvironment-v3.ps1](../../claude/tools/sre/Install-MaiaEnvironment-v3.ps1) - Original v3.0 script
- [claude/tools/sre/Install-MaiaEnvironment-v3.1-FIXED.ps1](../../claude/tools/sre/Install-MaiaEnvironment-v3.1-FIXED.ps1) - Fixed script (source)

**Note:** The OneDrive location is considered the authoritative source. Repository copies may be outdated.

---

## For Developers

When updating installation scripts:

1. Edit source files in repository:
   - `claude/tools/sre/Install-MaiaEnvironment-v3.1-FIXED.ps1`
   - `docs/installation/INSTALLATION_ISSUES_REPORT.md`

2. Copy updated files to OneDrive:
   ```bash
   cp claude/tools/sre/Install-MaiaEnvironment-v3.1-FIXED.ps1 \
      "/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/remote-shared/maia-windows-installation/"
   ```

3. Update version numbers and dates in README.md

---

**Maintained By:** SRE Team
**Last Sync:** 2026-01-11
