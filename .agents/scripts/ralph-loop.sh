#!/bin/bash
# Ralph Loop Defense Mechanism
TICKET_ID=$1
AGENT_NAME=$2
FAIL_LOG=".agents/tmp/${AGENT_NAME}_fail_count.txt"

if [ ! -f "$FAIL_LOG" ]; then
    echo 0 > "$FAIL_LOG"
fi

FAIL_COUNT=$(cat "$FAIL_LOG")

echo "Running tests for $AGENT_NAME..."
if .venv/bin/pytest tests/; then
    echo "Tests passed. Resetting fail count."
    echo 0 > "$FAIL_LOG"
    exit 0
else
    FAIL_COUNT=$((FAIL_COUNT+1))
    echo $FAIL_COUNT > "$FAIL_LOG"
    echo "Tests failed. Fail count: $FAIL_COUNT"
    
    if [ "$FAIL_COUNT" -ge 3 ]; then
        echo "Failed 3 times. Moving ticket to 7-failed..."
        # 티켓이 4-testing 에 있다고 가정하고 이동
        mv ".agents/board/4-testing/$TICKET_ID" ".agents/board/7-failed/" 2>/dev/null || true
        echo 0 > "$FAIL_LOG"
    fi
    exit 1
fi
