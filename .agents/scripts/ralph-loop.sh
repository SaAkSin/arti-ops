#!/bin/bash
# ralph-loop.sh <agent_name> <ticket_file_name>
AGENT=$1
TICKET=$2

if [ -z "$AGENT" ] || [ -z "$TICKET" ]; then
    echo "Usage: ./ralph-loop.sh <agent_name> <ticket_file.md>"
    exit 1
fi

FAIL_FILE=".agents/tmp/failed_count_${AGENT}.txt"
read count < "$FAIL_FILE" 2>/dev/null || count=0

echo "▶ Running Ralph Loop for [$AGENT] on Ticket [$TICKET]"
echo "▶ Current failure count: $count"

TICKET_SRC=".agents/board/4-testing/$TICKET"

if [ ! -f "$TICKET_SRC" ]; then
    echo "Error: Ticket file $TICKET_SRC not found in 4-testing."
    exit 1
fi

echo "▶ Executing pytest tests/ ..."
pytest tests/
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Tests passed! Moving to 5-pending_approval."
    mv "$TICKET_SRC" ".agents/board/5-pending_approval/$TICKET"
    rm -f "$FAIL_FILE"
    exit 0
else
    count=$((count + 1))
    echo $count > "$FAIL_FILE"
    echo "❌ Tests failed."
    
    if [ $count -ge 3 ]; then
        echo "🚨 CIRCUIT BREAKER: 3 consecutive failures. Moving to 7-failed."
        mv "$TICKET_SRC" ".agents/board/7-failed/$TICKET"
        rm -f "$FAIL_FILE"
        exit 1
    else
        echo "⚠️ Moving back to 2-in_progress for retry."
        mv "$TICKET_SRC" ".agents/board/2-in_progress/$TICKET"
        exit 1
    fi
fi
