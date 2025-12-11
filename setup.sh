#!/bin/bash
# Maia Setup Script - Run this after cloning to get started
# This script sets up your environment for Maia development/usage

set -e

echo "========================================"
echo "  Maia Setup"
echo "========================================"
echo ""

# Get the directory where this script is located (= MAIA_ROOT)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MAIA_ROOT="$SCRIPT_DIR"

echo "MAIA_ROOT: $MAIA_ROOT"
echo ""

# Step 1: Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "   WARNING: Python 3.11+ recommended (found $PYTHON_VERSION)"
    echo "   Some features may not work correctly."
else
    echo "   OK: Python $PYTHON_VERSION"
fi
echo ""

# Step 2: Install Python dependencies
echo "2. Installing Python dependencies..."
if [ -f "$MAIA_ROOT/requirements.txt" ]; then
    pip3 install -r "$MAIA_ROOT/requirements.txt" --quiet
    echo "   OK: Dependencies installed"
else
    echo "   SKIP: requirements.txt not found"
fi
echo ""

# Step 3: Create necessary directories
echo "3. Creating directories..."
mkdir -p "$MAIA_ROOT/claude/data/logs"
mkdir -p "$MAIA_ROOT/claude/data/databases/intelligence"
mkdir -p "$MAIA_ROOT/claude/data/databases/system"
mkdir -p "$MAIA_ROOT/claude/data/databases/user"
mkdir -p "$MAIA_ROOT/claude/data/project_status/active"
mkdir -p "$MAIA_ROOT/claude/data/project_status/archive"
echo "   OK: Directories created"
echo ""

# Step 4: Set up shell environment
echo "4. Setting up shell environment..."
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "export MAIA_ROOT=" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Maia environment" >> "$SHELL_RC"
        echo "export MAIA_ROOT=\"$MAIA_ROOT\"" >> "$SHELL_RC"
        echo "   OK: Added MAIA_ROOT to $SHELL_RC"
    else
        echo "   SKIP: MAIA_ROOT already in $SHELL_RC"
    fi
else
    echo "   NOTE: Add to your shell profile:"
    echo "         export MAIA_ROOT=\"$MAIA_ROOT\""
fi
echo ""

# Step 5: Verify core imports
echo "5. Verifying installation..."
if python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(f'   Paths module: {MAIA_ROOT}')" 2>/dev/null; then
    echo "   OK: Core paths module working"
else
    echo "   WARNING: Core paths module failed to import"
    echo "            Check PYTHONPATH or run from MAIA_ROOT"
fi
echo ""

# Step 6: Check optional dependencies
echo "6. Checking optional features..."

# Ollama for local LLMs
if command -v ollama &> /dev/null; then
    echo "   OK: Ollama installed"
    if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
        echo "   OK: nomic-embed-text embedding model available"
    else
        echo "   NOTE: Run 'ollama pull nomic-embed-text' for RAG features"
    fi
else
    echo "   NOTE: Install Ollama for local LLM features (brew install ollama)"
fi

# Docker for ServiceDesk dashboard
if command -v docker &> /dev/null; then
    echo "   OK: Docker installed"
else
    echo "   NOTE: Install Docker for ServiceDesk dashboard features"
fi
echo ""

# Summary
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Quick Start:"
echo "  1. Source your shell: source $SHELL_RC"
echo "  2. Run Maia tests:    pytest tests/ -v --tb=short"
echo "  3. Use with Claude Code"
echo ""
echo "Documentation:"
echo "  - System overview:    CLAUDE.md"
echo "  - Capabilities:       claude/context/core/capability_index.md"
echo "  - Recent changes:     SYSTEM_STATE.md"
echo ""
