# Setup Windows Maia - Full Featured

**Complete WSL2 + Claude Code setup for full Maia functionality on Windows**

## Prerequisites

### System Requirements
- Windows 10 version 2004+ or Windows 11
- At least 8GB RAM (16GB recommended)
- 20GB free disk space for WSL2 and development environment
- Administrator privileges for initial setup

### Software Requirements
- WSL2 enabled
- Ubuntu 20.04+ or Ubuntu 22.04 LTS (recommended)
- Claude Code for Windows
- Git for Windows (optional, for Windows-side Git operations)

---

## Phase 1: WSL2 Environment Setup

### 1.1 Enable WSL2
```powershell
# Run in PowerShell as Administrator
wsl --install

# Or manually if needed:
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart Windows, then set WSL2 as default
wsl --set-default-version 2
```

### 1.2 Install Ubuntu Distribution
```powershell
# Install Ubuntu 22.04 LTS (recommended)
wsl --install -d Ubuntu-22.04

# Verify installation
wsl --list --verbose
```

### 1.3 Initial Ubuntu Configuration
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential development tools
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    jq \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

---

## Phase 2: Python Environment Setup

### 2.1 Install Python 3.11+
```bash
# Add deadsnakes PPA for latest Python versions
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and tools
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    python3.11-distutils

# Set Python 3.11 as default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify installation
python3 --version  # Should show Python 3.11.x
```

### 2.2 Install Node.js (for MCP servers)
```bash
# Install Node.js 18+ LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version  # Should show v18.x or higher
npm --version
```

---

## Phase 3: Maia System Installation

### 3.1 Clone Maia Repository
```bash
# Create development directory
mkdir -p ~/development
cd ~/development

# Clone Maia repository
git clone https://github.com/YOUR_USERNAME/maia.git
cd maia

# Verify UFC structure
ls claude/context/core/
```

### 3.2 Install Python Dependencies
```bash
# Create and activate virtual environment
python3 -m venv maia-env
source maia-env/bin/activate

# Install core dependencies
pip install --upgrade pip
pip install \
    requests \
    beautifulsoup4 \
    pandas \
    numpy \
    python-dateutil \
    pyyaml \
    python-dotenv \
    cryptography \
    keyring \
    sqlite3 \
    asyncio \
    aiohttp \
    fastapi \
    uvicorn \
    Pillow \
    reportlab \
    openpyxl \
    python-docx \
    markdown \
    jinja2 \
    click \
    rich \
    typer \
    pydantic \
    SQLAlchemy \
    alembic

# Install security and optimization tools
pip install \
    bandit \
    safety \
    pip-audit \
    flake8 \
    black \
    mypy \
    isort
```

### 3.3 Install Additional Tools
```bash
# Install ripgrep for enhanced search
curl -LO https://github.com/BurntSushi/ripgrep/releases/download/14.0.3/ripgrep_14.0.3_amd64.deb
sudo dpkg -i ripgrep_14.0.3_amd64.deb
rm ripgrep_14.0.3_amd64.deb

# Install fd for file finding
curl -LO https://github.com/sharkdp/fd/releases/download/v8.7.1/fd_8.7.1_amd64.deb
sudo dpkg -i fd_8.7.1_amd64.deb
rm fd_8.7.1_amd64.deb

# Install bat for enhanced cat
curl -LO https://github.com/sharkdp/bat/releases/download/v0.24.0/bat_0.24.0_amd64.deb
sudo dpkg -i bat_0.24.0_amd64.deb
rm bat_0.24.0_amd64.deb
```

---

## Phase 4: Claude Code Integration

### 4.1 Install Claude Code for Windows
1. Download Claude Code from official Anthropic website
2. Install Claude Code on Windows (not in WSL2)
3. Configure Claude Code to use WSL2 as default terminal

### 4.2 Configure WSL2 Integration
```bash
# In WSL2 Ubuntu terminal
# Add WSL integration to profile
echo 'export DISPLAY=:0' >> ~/.bashrc
echo 'export MAIA_ENV=wsl2' >> ~/.bashrc
echo 'export MAIA_ROOT=~/development/maia' >> ~/.bashrc
echo 'cd ~/development/maia' >> ~/.bashrc
source ~/.bashrc
```

### 4.3 Test Claude Code Integration
1. Open Claude Code on Windows
2. Open terminal in Claude Code (should default to WSL2)
3. Verify you're in Ubuntu environment:
```bash
uname -a  # Should show Linux kernel
which python3  # Should show /usr/bin/python3
ls ~/development/maia/claude/context/core/
```

---

## Phase 5: Maia System Initialization

### 5.1 Run System Bootstrap
```bash
# Activate Maia environment
source ~/development/maia/maia-env/bin/activate
cd ~/development/maia

# Run system bootstrap
python3 claude/tools/bootstrap/system_bootstrap.py
```

### 5.2 Initialize Databases
```bash
# Initialize all Maia databases
python3 claude/tools/bootstrap/initialize_databases.py

# Verify database creation
ls -la ~/Library/CloudStorage/iCloudDrive-Documents/maia/data/  # Or local fallback
```

### 5.3 Configure File System Paths
```bash
# Create configuration directory
mkdir -p ~/.config/maia

# Create paths configuration
cat > ~/.config/maia/paths.yaml << EOF
# Maia Paths Configuration for WSL2
data_root: "~/.local/share/maia/data"
cache_root: "~/.cache/maia"
config_root: "~/.config/maia"
logs_root: "~/.local/share/maia/logs"

# Cross-platform accessibility
windows_mount: "/mnt/c/Users/\$USER/Documents/maia"
backup_locations:
  - "~/.local/share/maia/backup"
  - "/mnt/c/Users/\$USER/Documents/maia/backup"
EOF
```

---

## Phase 6: System Health Verification

### 6.1 Run Health Checks
```bash
# Run comprehensive health check
python3 claude/tools/bootstrap/system_health_monitor.py

# Expected output:
# ✅ Data paths accessible
# ✅ Database connectivity verified
# ✅ Python tools importable
# ✅ Tool instantiation successful
# ✅ Bootstrap system ready
# ✅ Performance metrics acceptable
```

### 6.2 Test Core Functionality
```bash
# Test UFC context loading
python3 -c "
from claude.context.core.identity import *
print('✅ UFC context system operational')
"

# Test agent system
python3 claude/tools/test_agent_simulation.py

# Test security infrastructure
python3 claude/tools/security/local_security_scanner.py
```

---

## Phase 7: Cross-Platform File Access

### 7.1 Windows to WSL2 Access
```bash
# WSL2 file system accessible from Windows Explorer at:
# \\wsl$\Ubuntu-22.04\home\[username]\development\maia

# Or via Windows path in WSL2:
# /mnt/c/Users/[WindowsUsername]/
```

### 7.2 Configure Git Integration
```bash
# Configure Git in WSL2
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase false

# Set Windows-compatible line endings for cross-platform work
git config --global core.autocrlf input
git config --global core.safecrlf true
```

---

## Phase 8: Production Features Setup

### 8.1 MCP Servers Configuration
```bash
# Install MCP server dependencies
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-sqlite

# Configure MCP servers
python3 claude/tools/mcp/setup_credentials.py
```

### 8.2 Security Hardening
```bash
# Run security initialization
python3 claude/tools/security/security_toolkit_installer.py

# Configure encrypted environment management
python3 claude/tools/security/mcp_env_manager.py
```

### 8.3 Optimization System Activation
```bash
# Initialize token optimization suite
python3 claude/tools/optimization/phase3_optimizer.py --initialize

# Test optimization capabilities
python3 claude/tools/optimization/intelligent_context_cache.py --test
```

---

## Phase 9: Verification & Testing

### 9.1 Complete System Test
```bash
# Run integration test suite
python3 claude/tools/optimization/integration_test.py

# Expected results:
# - Core Infrastructure: 100%
# - Agent System: 100%
# - Context Management: 100%
# - Performance: 100%
# - Database Integrity: 67%+ (normal for fresh install)
# - Tool Functionality: 75%+
# - Data Flow: 75%+
# - Security Posture: 67%+
```

### 9.2 Test Claude Code Integration
1. Open Claude Code
2. Open Maia project in WSL2
3. Verify context loading works:
   - Should see "✅ Context loaded. Ready to assist as Maia." message
   - All 8 context files should load successfully
   - Full functionality should be available

---

## Common Issues & Solutions

### WSL2 Issues
```bash
# WSL2 not starting
wsl --shutdown
wsl --unregister Ubuntu-22.04
wsl --install -d Ubuntu-22.04

# Memory issues
# Add to Windows %USERPROFILE%\.wslconfig:
[wsl2]
memory=8GB
processors=4
swap=2GB
```

### Python Issues
```bash
# Permission errors
sudo chown -R $USER:$USER ~/.local/
sudo chown -R $USER:$USER ~/.cache/

# Module import errors
export PYTHONPATH="/home/$USER/development/maia:$PYTHONPATH"
echo 'export PYTHONPATH="/home/$USER/development/maia:$PYTHONPATH"' >> ~/.bashrc
```

### File Permission Issues
```bash
# Set proper permissions for scripts
find ~/development/maia/claude/tools -name "*.py" -exec chmod +x {} \;
find ~/development/maia/claude/hooks -name "*.sh" -exec chmod +x {} \;
```

---

## Success Indicators

✅ **WSL2 Environment**: Ubuntu 22.04+ running smoothly
✅ **Python 3.11+**: Virtual environment activated
✅ **Claude Code**: Integrated with WSL2 terminal
✅ **Maia Context**: All 8 UFC context files loading
✅ **Database System**: Initialized and accessible
✅ **Security Tools**: Scanning and validation active
✅ **Optimization Suite**: 54% cost reduction operational
✅ **Agent Ecosystem**: All 6+ agents functional
✅ **Cross-Platform**: File access working both directions

---

**Result**: Full-featured Maia system operational on Windows with zero compromises - complete UFC context system, all agents, optimization infrastructure, security framework, and cross-platform integration.

**Development Experience**: Native Unix environment within Windows with seamless file system integration and Claude Code compatibility.
