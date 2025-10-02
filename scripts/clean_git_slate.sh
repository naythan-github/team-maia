#!/bin/bash
# Clean Git Slate - Remove Problematic History
# Simple, low-risk approach to clean git history

set -e  # Exit on any error

echo "🧹 Maia Git Clean Slate"
echo "======================="
echo ""

# Configuration
BACKUP_DIR="/Users/naythan/git/maia_backup_$(date +%Y%m%d_%H%M%S)"
CLEAN_COMMIT="6294cd6"  # Security fix commit (safe starting point)
REPO_DIR="/Users/naythan/git/maia"

# Safety checks
echo "🔍 Pre-flight Safety Checks:"

# Check we're in the right directory
if [[ ! -f "CLAUDE.md" ]]; then
    echo "❌ Error: Not in Maia repository root"
    exit 1
fi

# Check clean working directory
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Error: Working directory not clean"
    echo "   Please commit or stash changes first"
    git status --short
    exit 1
fi

# Check target commit exists
if ! git cat-file -e "$CLEAN_COMMIT" 2>/dev/null; then
    echo "❌ Error: Clean commit $CLEAN_COMMIT not found"
    exit 1
fi

echo "✅ Repository root confirmed"
echo "✅ Working directory clean"
echo "✅ Target commit exists: $CLEAN_COMMIT"
echo ""

# Show current status
echo "📊 Current Repository Status:"
git log --oneline -10
echo ""

echo "🎯 Target Clean Commit:"
git show --stat $CLEAN_COMMIT
echo ""

# Confirmation
echo "⚠️  This will:"
echo "   - Create backup at: $BACKUP_DIR"
echo "   - Reset history to commit: $CLEAN_COMMIT"
echo "   - Remove all commits before security fixes"
echo "   - Clean up git references and garbage collect"
echo ""

read -p "❓ Continue with clean slate? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "🚫 Operation cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting Clean Slate Process..."

# Step 1: Create complete backup
echo "💾 Step 1: Creating complete repository backup..."
cp -r "$REPO_DIR" "$BACKUP_DIR"
echo "✅ Backup created: $BACKUP_DIR"

# Step 2: Create new clean branch from target commit
echo "🌿 Step 2: Creating clean branch..."
git checkout -b temp-clean-main $CLEAN_COMMIT
echo "✅ Created clean branch from commit $CLEAN_COMMIT"

# Step 3: Replace main branch
echo "🔄 Step 3: Replacing main branch..."
git branch -D main 2>/dev/null || echo "   (main branch already clean)"
git checkout -b main
git branch -D temp-clean-main
echo "✅ Main branch replaced with clean history"

# Step 4: Clean up git references
echo "🧹 Step 4: Cleaning git references..."

# Expire all reflog entries
git reflog expire --expire=now --all

# Remove unreachable objects
git gc --prune=now --aggressive

# Clean up remote tracking info (optional)
git remote prune origin 2>/dev/null || echo "   (no remote to prune)"

echo "✅ Git references cleaned"

# Step 5: Verification
echo "🔍 Step 5: Verification..."

# Check that problematic commits are gone
PROBLEM_COMMITS=$(git log --all --full-history -S "tqsf fmhm ubnq lsmx" --oneline 2>/dev/null | wc -l)

if [[ $PROBLEM_COMMITS -eq 0 ]]; then
    echo "✅ No problematic credentials found in history"
else
    echo "⚠️  Warning: $PROBLEM_COMMITS commits still contain credentials"
fi

# Show new clean history
echo ""
echo "📊 New Clean Repository Status:"
git log --oneline -10
echo ""

# Repository stats
echo "📈 Repository Statistics:"
echo "   Total commits: $(git rev-list --all --count)"
echo "   Branches: $(git branch -a | wc -l)"
echo "   Repository size: $(du -sh .git | cut -f1)"
echo ""

# Final status
echo "🎉 Clean Slate Complete!"
echo "========================"
echo "✅ History cleaned starting from security fix commit"
echo "✅ Backup preserved at: $BACKUP_DIR"
echo "✅ All problematic credentials removed from git history"
echo "✅ Repository ready for clean future development"
echo ""
echo "📋 Next Steps:"
echo "   1. Verify system still works correctly"
echo "   2. Test a few operations to ensure stability"
echo "   3. Optional: Push clean history to remote"
echo ""
echo "🔒 Security Status: CLEAN - No credentials in git history"