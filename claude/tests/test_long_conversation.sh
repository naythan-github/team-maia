#!/bin/bash
# Phase 127: Long-Conversation Performance Test Suite
# Tests hook performance over 100-message conversation to prevent regressions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAIA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SCRIPT="$MAIA_ROOT/claude/hooks/user-prompt-submit"
MESSAGE_COUNT="${1:-100}"  # Default 100 messages
RESULTS_FILE="/tmp/hook_performance_test_$(date +%s).log"

# Performance SLOs (from Phase 127 requirements)
MAX_TOTAL_LATENCY_MS=5000      # 5 seconds for 100 messages
MAX_OUTPUT_LINES=500            # 500 lines total output
MAX_AVG_LATENCY_MS=50          # 50ms average per message

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 127: Long-Conversation Performance Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Configuration:"
echo "  Messages to test: $MESSAGE_COUNT"
echo "  Hook script: $HOOK_SCRIPT"
echo "  Results log: $RESULTS_FILE"
echo ""

# Verify hook exists
if [[ ! -f "$HOOK_SCRIPT" ]]; then
    echo -e "${RED}❌ FAIL: Hook script not found: $HOOK_SCRIPT${NC}"
    exit 1
fi

echo -e "${YELLOW}⚙️  Running $MESSAGE_COUNT message simulation...${NC}"
echo ""

# Initialize counters
total_latency_ms=0
output_line_count=0
message_num=0
start_time=$(date +%s%N)

# Simulate messages
for i in $(seq 1 $MESSAGE_COUNT); do
    message_num=$i

    # Vary message types for realistic testing
    case $((i % 10)) in
        0) test_message="What is the system status?" ;;
        1) test_message="Analyze this code pattern" ;;
        2) test_message="Create a new function" ;;
        3) test_message="Review the implementation" ;;
        4) test_message="Fix the bug in module X" ;;
        5) test_message="Explain this concept" ;;
        6) test_message="Optimize performance" ;;
        7) test_message="Add tests for feature Y" ;;
        8) test_message="Document the API" ;;
        9) test_message="Refactor legacy code" ;;
    esac

    # Measure single message latency
    msg_start=$(date +%s%N)

    # Execute hook with test message
    hook_output=$(CLAUDE_USER_MESSAGE="$test_message" bash "$HOOK_SCRIPT" 2>&1)
    hook_exit_code=$?

    msg_end=$(date +%s%N)
    msg_latency_ns=$((msg_end - msg_start))
    msg_latency_ms=$((msg_latency_ns / 1000000))

    # Count output lines
    msg_output_lines=$(echo "$hook_output" | wc -l | tr -d ' ')

    # Accumulate totals
    total_latency_ms=$((total_latency_ms + msg_latency_ms))
    output_line_count=$((output_line_count + msg_output_lines))

    # Log to results file
    echo "$i,$msg_latency_ms,$msg_output_lines,$hook_exit_code" >> "$RESULTS_FILE"

    # Progress indicator (every 10 messages)
    if [[ $((i % 10)) -eq 0 ]]; then
        avg_so_far=$((total_latency_ms / i))
        echo -e "  ${BLUE}Progress: $i/$MESSAGE_COUNT messages${NC} (avg: ${avg_so_far}ms, output: $output_line_count lines)"
    fi
done

end_time=$(date +%s%N)
total_test_duration_ms=$(( (end_time - start_time) / 1000000 ))

# Calculate statistics
avg_latency_ms=$((total_latency_ms / MESSAGE_COUNT))
avg_output_lines=$((output_line_count / MESSAGE_COUNT))

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Test Results${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Performance Metrics:"
echo "  Messages tested: $MESSAGE_COUNT"
echo "  Total test duration: ${total_test_duration_ms}ms"
echo "  Total hook latency: ${total_latency_ms}ms"
echo "  Average latency: ${avg_latency_ms}ms per message"
echo "  Total output: $output_line_count lines"
echo "  Average output: $avg_output_lines lines per message"
echo ""

# Evaluate against SLOs
echo "SLO Compliance:"
echo ""

pass_count=0
fail_count=0

# Test 1: Total latency
if [[ $total_latency_ms -le $MAX_TOTAL_LATENCY_MS ]]; then
    echo -e "  ${GREEN}✅ PASS${NC}: Total latency ${total_latency_ms}ms ≤ ${MAX_TOTAL_LATENCY_MS}ms"
    ((pass_count++))
else
    echo -e "  ${RED}❌ FAIL${NC}: Total latency ${total_latency_ms}ms > ${MAX_TOTAL_LATENCY_MS}ms"
    ((fail_count++))
fi

# Test 2: Output pollution
if [[ $output_line_count -le $MAX_OUTPUT_LINES ]]; then
    echo -e "  ${GREEN}✅ PASS${NC}: Output $output_line_count lines ≤ $MAX_OUTPUT_LINES lines"
    ((pass_count++))
else
    echo -e "  ${RED}❌ FAIL${NC}: Output $output_line_count lines > $MAX_OUTPUT_LINES lines"
    ((fail_count++))
fi

# Test 3: Average latency
if [[ $avg_latency_ms -le $MAX_AVG_LATENCY_MS ]]; then
    echo -e "  ${GREEN}✅ PASS${NC}: Average latency ${avg_latency_ms}ms ≤ ${MAX_AVG_LATENCY_MS}ms"
    ((pass_count++))
else
    echo -e "  ${RED}❌ FAIL${NC}: Average latency ${avg_latency_ms}ms > ${MAX_AVG_LATENCY_MS}ms"
    ((fail_count++))
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Final result
if [[ $fail_count -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC} ($pass_count/$((pass_count + fail_count)))"
    echo ""
    echo "Hook performance meets Phase 127 SLO requirements."
    echo "Results saved to: $RESULTS_FILE"
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED${NC} ($fail_count failures, $pass_count passed)"
    echo ""
    echo "Hook performance DOES NOT meet Phase 127 SLO requirements."
    echo "Review results at: $RESULTS_FILE"
    echo ""
    echo "Recommendations:"
    if [[ $total_latency_ms -gt $MAX_TOTAL_LATENCY_MS ]]; then
        echo "  - Investigate slow Python subprocess calls"
        echo "  - Consider caching or async execution"
    fi
    if [[ $output_line_count -gt $MAX_OUTPUT_LINES ]]; then
        echo "  - Reduce verbose output in hooks"
        echo "  - Apply silent mode pattern"
    fi
    exit 1
fi
