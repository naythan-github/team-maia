#!/bin/bash
# Maia pre-commit hook
# Installed by scripts/setup-team-member.sh

set -e

echo "🔍 Running pre-commit checks..."

# Get repo root
MAIA_ROOT="$(git rev-parse --show-toplevel)"

# ───────────────────────────────────────────────────────────────
# Check 1: Personal data in staged files
# ───────────────────────────────────────────────────────────────
echo "  Checking for personal data..."
if git diff --cached --name-only | xargs grep -l \
   "naythandawe\|/Users/naythan\|/home/naythan" 2>/dev/null | \
   grep -v "CODEOWNERS\|CONTRIBUTING"; then
    echo "❌ BLOCKED: Personal data detected in staged files"
    echo "   Remove personal identifiers before committing"
    exit 1
fi

# ───────────────────────────────────────────────────────────────
# Check 2: Hardcoded paths in Python files
# ───────────────────────────────────────────────────────────────
echo "  Checking for hardcoded paths..."
staged_py=$(git diff --cached --name-only | grep "\.py$" || true)
if [ -n "$staged_py" ]; then
    if echo "$staged_py" | xargs grep -l '"/Users/\|"/home/' 2>/dev/null | \
       grep -v "test_\|\.example"; then
        echo "❌ BLOCKED: Hardcoded user paths detected"
        echo "   Use environment variables or PathManager instead"
        exit 1
    fi
fi

# ───────────────────────────────────────────────────────────────
# Check 3: Potential secrets
# ───────────────────────────────────────────────────────────────
echo "  Checking for secrets..."
if git diff --cached | grep -E 'sk-ant-api|sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}' > /dev/null 2>&1; then
    echo "❌ BLOCKED: Potential API key detected"
    echo "   Never commit secrets - use environment variables"
    exit 1
fi

# ───────────────────────────────────────────────────────────────
# Check 4: TDD gate (if exists)
# ───────────────────────────────────────────────────────────────
if [ -f "$MAIA_ROOT/claude/hooks/pre_commit_tdd_gate.py" ]; then
    echo "  Running TDD gate..."
    python3 "$MAIA_ROOT/claude/hooks/pre_commit_tdd_gate.py" || exit 1
fi

echo "✅ Pre-commit passed"
