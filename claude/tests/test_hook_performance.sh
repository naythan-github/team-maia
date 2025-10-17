#!/bin/bash
# Phase 127: Pre-Commit Hook Performance Gate
# Fast performance check for git pre-commit hook integration
# Validates hook meets minimum performance requirements

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
MAIA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SCRIPT="$MAIA_ROOT/claude/hooks/user-prompt-submit"

# Performance Budget (per-prompt limits)
MAX_LATENCY_MS=150        # 150ms maximum per prompt (allows for test variance)
MAX_OUTPUT_LINES=10       # 10 lines maximum output per prompt

echo -e "${YELLOW}🧪 Testing hook performance...${NC}"

# Test 1: Single message latency
START=$(date +%s%N)
OUTPUT=$(CLAUDE_USER_MESSAGE="test performance check" bash "$HOOK_SCRIPT" 2>&1)
END=$(date +%s%N)
LATENCY_NS=$((END - START))
LATENCY_MS=$((LATENCY_NS / 1000000))

# Test 2: Output pollution
LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')

# Evaluate
FAIL=0

if [ $LATENCY_MS -gt $MAX_LATENCY_MS ]; then
    echo -e "${RED}❌ FAIL: Hook latency ${LATENCY_MS}ms exceeds ${MAX_LATENCY_MS}ms budget${NC}"
    FAIL=1
else
    echo -e "${GREEN}✅ PASS: Hook latency ${LATENCY_MS}ms within ${MAX_LATENCY_MS}ms budget${NC}"
fi

if [ $LINE_COUNT -gt $MAX_OUTPUT_LINES ]; then
    echo -e "${RED}❌ FAIL: Hook output ${LINE_COUNT} lines exceeds ${MAX_OUTPUT_LINES} line budget${NC}"
    FAIL=1
else
    echo -e "${GREEN}✅ PASS: Hook output ${LINE_COUNT} lines within ${MAX_OUTPUT_LINES} line budget${NC}"
fi

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ Hook performance meets Phase 127 requirements${NC}"
    exit 0
else
    echo -e "${RED}❌ Hook performance violates Phase 127 requirements${NC}"
    echo ""
    echo "To investigate:"
    echo "  bash claude/tests/test_long_conversation.sh"
    exit 1
fi
